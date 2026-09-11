#!/usr/bin/env python3
"""Qualify real Codex hooks against a local Responses fixture, without model usage.

Requires Python 3.11+ and Codex CLI 0.153.4+. No user configuration, trust record,
marketplace, HOME, or CODEX_HOME is changed. Existing rules remain in force.
The only model output is this fixture's two harmless printf calls and final text.
Default mode uses vetted inline hooks. --native-plugin with --plugin-root tests an
already installed plugin's discovery, skill catalog and hooks without inline copies.
Installing/removing that temporary plugin is the caller's responsibility.
Resume/clear/compaction are separate checks.
"""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import threading
import time


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ('core.md', 'reference/orchestrator.md', 'reference/harness-codex.md')
ALLOW = 'DEVSTANDARD_RUNTIME_ALLOWED_342'
DENY = 'DEVSTANDARD_RUNTIME_EXECUTED_342'


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def toml(value):
    """Encode the small JSON-compatible inline TOML config used by this fixture."""
    if isinstance(value, dict):
        return '{' + ','.join(json.dumps(key) + '=' + toml(item)
                              for key, item in value.items()) + '}'
    if isinstance(value, list):
        return '[' + ','.join(toml(item) for item in value) + ']'
    return json.dumps(value)


def inventory(fixture):
    """Refuse external hook layers before granting this invocation's hook trust.

    User config is ignored and plugins are disabled by supported CLI overrides.
    Standalone hook files and managed system config are not overridden that way.
    Conservative refusal is preferable to executing an unrelated user's hook.
    """
    codex_home = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))
    candidates = [codex_home / 'hooks.json', codex_home / 'requirements.toml',
                  Path('/etc/codex/config.toml'),
                  Path('/etc/codex/requirements.toml')]
    for parent in (fixture, *fixture.parents):
        candidates += [parent / '.codex/hooks.json', parent / '.codex/config.toml']
    found = sorted({str(path) for path in candidates if path.exists()})
    require(not found, 'runtime isolation unavailable: external hook/config layers: '
            + ', '.join(found))
    return {'external_hook_layers': [], 'user_config': 'ignored',
            'plugins': 'disabled for this invocation', 'execpolicy_rules': 'preserved'}


def native_plugin(binary, selector, installed_root):
    """Vet the installed execution closure and disable unrelated plugins for one run."""
    require(re.fullmatch(r'devstandard@[A-Za-z0-9_-]+', selector),
            'native fixture requires an installed devstandard@marketplace selector')
    installed_root = installed_root.resolve()
    codex_home = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))).resolve()
    marketplace = selector.split('@', 1)[1]
    expected_parent = codex_home / 'plugins/cache' / marketplace / 'devstandard'
    require(installed_root.parent == expected_parent,
            'native plugin root must be the selected marketplace installation cache')
    closure = ('.codex-plugin/plugin.json', '.claude-plugin/plugin.json',
               'hooks/hooks.json', 'hooks/session-start', 'hooks/pre-tool-use',
               'scripts/hard_edges.py', 'scripts/review_packet.py',
               'skills/devstandard/SKILL.md', *ARTIFACTS)
    for path in closure:
        cached = installed_root / path
        require(cached.is_file() and not cached.is_symlink(), 'missing/linked cached source: ' + path)
        require(cached.read_bytes() == (ROOT / path).read_bytes(), 'cached source differs: ' + path)
    for path in ('hooks/session-start', 'hooks/pre-tool-use'):
        require(os.access(installed_root / path, os.X_OK), 'cached hook is not executable: ' + path)
    for path in ('plugin.json', '.mcp.json', 'mcp.json', '.app.json'):
        require(not (installed_root / path).exists(), 'unexpected native execution source: ' + path)
    hook_config(None)  # Validate the shipped hook command allowlist without installing overrides.
    result = subprocess.run([binary, 'plugin', 'list', '--json'],
                            capture_output=True, text=True, timeout=30, check=True)
    rows = json.loads(result.stdout)['installed']
    selected = [row for row in rows if row['pluginId'] == selector]
    require(len(selected) == 1, 'native plugin is not installed: ' + selector)
    source = selected[0].get('marketplaceSource', {})
    require(source.get('sourceType') == 'local' and Path(source.get('source', '')).is_dir(),
            'native fixture requires an existing local marketplace source')
    settings = {'features.plugins': True, 'features.remote_plugin': False,
                'features.skip_host_skill_discovery': False, 'skills.max_context_tokens': 10000,
                # --ignore-user-config also hides marketplace registrations. Restore
                # only this already installed temporary source, for this invocation.
                'marketplaces': {marketplace: {'source_type': 'local', 'source': source['source']}},
                # CLI dotted override paths retain quote characters in a segment.
                # Encode the table as TOML instead so selectors remain exact keys.
                'plugins': {row['pluginId']: {'enabled': row['pluginId'] == selector}
                            for row in rows}}
    # Listing is read-only; verify the per-plugin disabling overrides before using trust.
    command = [binary]
    for key, value in settings.items():
        command += ['-c', key + '=' + toml(value)]
    command += ['plugin', 'list', '--json']
    listing = subprocess.run(command, capture_output=True, text=True, timeout=30, check=True)
    enabled = [row['pluginId'] for row in json.loads(listing.stdout)['installed'] if row['enabled']]
    require(enabled == [selector], 'runtime isolation unavailable: enabled plugins: ' + repr(enabled))
    return {'selector': selector, 'root': installed_root, 'settings': settings,
            'other_plugins': [row['pluginId'] for row in rows if row['pluginId'] != selector]}


class ResponsesFixture:
    def __init__(self, forbidden):
        self.forbidden = forbidden
        self.requests = []
        self.errors = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_GET(self):
                # Custom providers are queried for model metadata before the first turn.
                # An empty catalog deliberately selects Codex's fallback metadata.
                if self.path.split('?', 1)[0] != '/v1/models':
                    outer.errors.append('unexpected local endpoint: ' + self.path)
                    self.send_error(404)
                    return
                if self.headers.get('Authorization'):
                    outer.errors.append('fixture unexpectedly received authentication')
                    self.send_error(403)
                    return
                body = b'{"models":[]}'
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                try:
                    require(self.path.rstrip('/') == '/v1/responses',
                            'unexpected local endpoint: ' + self.path)
                    require(not self.headers.get('Authorization'),
                            'fixture unexpectedly received authentication')
                    require(self.headers.get('Content-Encoding', 'identity') == 'identity',
                            'request compression must be disabled for the fixture')
                    body = self.rfile.read(int(self.headers['Content-Length']))
                    request = json.loads(body)
                    outer.requests.append(request)
                    require(len(outer.requests) <= 3, 'unexpected extra model continuation')
                    item = outer.response_item(request, len(outer.requests) - 1)
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/event-stream')
                    self.send_header('Connection', 'close')
                    self.end_headers()
                    response = {'id': 'resp_devstandard_' + str(len(outer.requests)),
                                'object': 'response', 'status': 'completed', 'output': [item],
                                'usage': {'input_tokens': 1, 'output_tokens': 1,
                                          'total_tokens': 2}}
                    for event in [
                        {'type': 'response.created', 'response': dict(response, status='in_progress', output=[])},
                        {'type': 'response.output_item.added', 'output_index': 0, 'item': item},
                        {'type': 'response.output_item.done', 'output_index': 0, 'item': item},
                        {'type': 'response.completed', 'response': response},
                    ]:
                        self.wfile.write(('data: ' + json.dumps(event) + '\n\n').encode())
                    self.wfile.flush()
                except Exception as error:
                    outer.errors.append(str(error))
                    self.send_error(500, 'fixture refused request')

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def response_item(self, request, index):
        if index == 2:
            return {'type': 'message', 'id': 'msg_fixture', 'role': 'assistant',
                    'status': 'completed', 'content': [{'type': 'output_text',
                    'text': 'DevStandard runtime fixture complete.', 'annotations': []}]}
        tools = {tool.get('name'): tool for tool in request.get('tools', [])}
        require('exec_command' in tools, 'Codex did not expose the expected unified exec tool')
        command = ('printf ' + shlex.quote(ALLOW + '\n') if index == 0 else
                   'printf ' + shlex.quote(self.forbidden + ' ' + DENY + '\n'))
        return {'type': 'function_call', 'id': 'fc_' + str(index),
                'call_id': 'call_' + str(index), 'name': 'exec_command',
                'arguments': json.dumps({'cmd': command, 'login': False,
                                         'max_output_tokens': 100})}


def hook_config(role):
    """Run the shipped handlers, retaining their shipped lifecycle matchers/limits.

    Inline hooks do not get plugin environment variables, so supply the documented
    aliases explicitly. Native plugin environment/discovery is tested separately.
    """
    config = json.loads((ROOT / 'hooks/hooks.json').read_text())['hooks']
    for groups in config.values():
        for group in groups:
            for handler in group['hooks']:
                command = handler['command']
                command = command.replace('${CLAUDE_PLUGIN_ROOT}', str(ROOT))
                command = command.replace('${PLUGIN_ROOT}', str(ROOT))
                # Only the two audited entrypoints may receive invocation-wide trust.
                args = shlex.split(command)
                require(args[0] in (str(ROOT / 'hooks/session-start'),
                                    str(ROOT / 'hooks/pre-tool-use')),
                        'unvetted hook command: ' + command)
                require(all(part in ('core', 'orchestrator', 'codex') for part in args[1:]),
                        'unvetted hook arguments: ' + command)
                handler['command'] = shlex.join([
                    'env', 'PLUGIN_DATA=devstandard-runtime-fixture',
                    'CLAUDE_PLUGIN_DATA=devstandard-runtime-fixture',
                    'DEVSTANDARD_ROLE=' + (role or ''), *args])
    return config


def tool_results(request):
    return {item['call_id']: item.get('output', '') for item in request.get('input', [])
            if item.get('type') == 'function_call_output'}


def catalog_paths(text):
    """Resolve the CLI catalog's compact skill-root aliases to actual file paths."""
    roots = dict(re.findall(r'`([^`\s]+)`\s*=\s*`(/[^`]+)`', text))
    paths = set()
    for reference in re.findall(r'\(file:\s*([^\n)]+)\)', text):
        reference = reference.strip(' `')
        alias, separator, suffix = reference.partition('/')
        if separator and alias in roots:
            paths.add(str(Path(roots[alias]) / suffix))
        elif reference.startswith('/'):
            paths.add(reference)
    return paths


def run_case(binary, fixture, name, *, role=None, trusted=False, enabled=True, logs=None, native=None):
    forbidden = {'worker': 'tag', 'reviewer': 'push'}.get(role, 'git merge')
    with ResponsesFixture(forbidden) as server:
        settings = {
            'model_provider': 'devstandard-fixture',
            'model_providers.devstandard-fixture': {
                'name': 'Local deterministic DevStandard fixture',
                'base_url': 'http://127.0.0.1:' + str(server.server.server_port) + '/v1',
                'wire_api': 'responses', 'requires_openai_auth': False,
                'supports_websockets': False, 'request_max_retries': 0,
                'stream_max_retries': 0, 'stream_idle_timeout_ms': 5000},
            'features.hooks': enabled, 'features.plugins': False,
            'features.apps': False, 'features.remote_plugin': False,
            'features.enable_request_compression': False,
            'features.shell_snapshot': False, 'features.code_mode': False,
            'features.multi_agent': False, 'features.skip_host_skill_discovery': True,
            'web_search': 'disabled', 'check_for_update_on_startup': False,
            'approval_policy': 'never', 'analytics.enabled': False,
        }
        if native:
            settings.update(native['settings'])
        else:
            for event, groups in hook_config(role).items():
                settings['hooks.' + event] = groups
        command = [binary, 'exec', '--ignore-user-config', '--ephemeral', '--json',
                   '-s', 'read-only', '-C', str(fixture), '-m', 'devstandard-fixture']
        for key, value in settings.items():
            command += ['-c', key + '=' + toml(value)]
        if trusted:
            command.append('--dangerously-bypass-hook-trust')
        command.append('Run the two harmless local printf probes supplied by the fixture, then finish.')
        env = dict(os.environ)
        for key in ('DEVSTANDARD_ROLE', 'PLUGIN_DATA', 'CLAUDE_PLUGIN_DATA',
                    'PLUGIN_ROOT', 'CLAUDE_PLUGIN_ROOT', 'OPENAI_API_KEY'):
            env.pop(key, None)
        if native and role:
            env['DEVSTANDARD_ROLE'] = role
        started = time.monotonic()
        result = subprocess.run(command, env=env, stdin=subprocess.DEVNULL,
                                capture_output=True, text=True, timeout=45)
        if logs:
            (logs / (name + '.events.jsonl')).write_text(result.stdout)
            (logs / (name + '.stderr.log')).write_text(result.stderr)
        require(result.returncode == 0, name + ': Codex failed: ' + result.stderr[-2000:])
        require(not server.errors, name + ': ' + repr(server.errors))
        require(len(server.requests) == 3,
                name + ': expected two tool calls and final request, got ' + str(len(server.requests))
                + '; ' + result.stderr[-1000:])
        active = trusted and enabled
        delivered = []
        actual = '\n'.join(text_fragments(server.requests[0].get('input', [])))
        if native:
            catalog = '\n'.join(text_fragments(server.requests[0]))
            skill_path = str(native['root'] / 'skills/devstandard/SKILL.md')
            paths = catalog_paths(catalog)
            if logs:
                (logs / (name + '.catalog.json')).write_text(json.dumps({
                    'selected_skill_in_input': skill_path in actual,
                    'selected_skill_in_request': skill_path in catalog,
                    'selected_skill_resolved': skill_path in paths,
                    'resolved_plugin_skills': sorted(path for path in paths if '/plugins/cache/' in path),
                    'cache_paths': sorted(set(re.findall(r'/[^\s<>"\x27]*plugins/cache/[^\s<>"\x27]*', catalog))),
                }, indent=2) + '\n')
            require(skill_path in catalog or skill_path in paths,
                    name + ': native DevStandard skill is missing from the model catalog')
            for selector in native['other_plugins']:
                plugin, marketplace = selector.split('@', 1)
                require('/plugins/cache/' + marketplace + '/' + plugin + '/' not in catalog,
                        name + ': unrelated plugin skill/context leaked: ' + selector)
                require(not any('/plugins/cache/' + marketplace + '/' + plugin + '/' in path
                                for path in paths),
                        name + ': unrelated plugin skill resolved: ' + selector)
        for artifact in ARTIFACTS:
            # Full source, including its middle, must survive hook delivery and spill handling.
            page = (ROOT / artifact).read_text().rstrip('\n')
            # Compare decoded text so JSON escaping cannot hide a missing tail.
            contains = page in actual
            expected = active and role is None
            require(contains == expected, name + ': incorrect full context delivery for ' + artifact)
            if not expected:
                require(page[:200] not in actual and page[-200:] not in actual,
                        name + ': partial or spilled role context leaked from ' + artifact)
            if contains:
                delivered.append(artifact)
        outputs = tool_results(server.requests[2])
        require(ALLOW in str(outputs.get('call_0', '')), name + ': admitted shell did not execute')
        events = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
        commands = [event['item'] for event in events if event.get('type') == 'item.completed'
                    and event.get('item', {}).get('type') == 'command_execution']
        require(any(item.get('aggregated_output') == ALLOW + '\n'
                    and item.get('exit_code') == 0 for item in commands),
                name + ': no successful printf execution in Codex events')
        blocked = str(outputs.get('call_1', ''))
        if active:
            require('role refuses' in blocked, name + ': no hook refusal reached model: ' + blocked[:500])
            # Codex quotes the refused command in its feedback; execution events are
            # the independent witness that the printf itself never ran.
            require(not any(DENY in item.get('command', '') for item in commands),
                    name + ': denied printf executed')
            require((role or 'orchestrator') + ' role refuses' in blocked,
                    name + ': wrong guard role: ' + blocked[:500])
        else:
            require(DENY in blocked, name + ': inactive hook branch did not execute harmless probe')
            require(any(item.get('aggregated_output') == forbidden + ' ' + DENY + '\n'
                        and item.get('exit_code') == 0 for item in commands),
                    name + ': inactive hook branch has no successful printf event')
        summary = {'case': name, 'status': 'pass', 'context': delivered,
                   'hook_source': 'installed-plugin' if native else 'inline',
                   'guard': 'denied' if active else 'inactive',
                   'requests': len(server.requests), 'seconds': round(time.monotonic() - started, 2)}
        if logs:
            (logs / (name + '.summary.json')).write_text(json.dumps(summary, indent=2) + '\n')
        return summary


def text_fragments(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from text_fragments(item)
    elif isinstance(value, list):
        for item in value:
            yield from text_fragments(item)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log-dir', type=Path, help='Save concise Codex events and assertion summaries')
    parser.add_argument('--case', choices=['disabled', 'untrusted-before', 'trusted-main',
                                         'untrusted-after', 'worker', 'reviewer'])
    parser.add_argument('--native-plugin', help='Installed devstandard@marketplace selector')
    parser.add_argument('--plugin-root', type=Path, help='Exact installed plugin cache root')
    args = parser.parse_args()
    require(bool(args.native_plugin) == bool(args.plugin_root),
            '--native-plugin and --plugin-root must be supplied together')
    binary = shutil.which('codex')
    require(binary, 'Codex CLI is required; install the CI-pinned version before this test')
    version = subprocess.check_output([binary, '--version'], text=True).strip()
    match = re.fullmatch(r'codex-cli (\d+)\.(\d+)\.(\d+)', version)
    require(match and tuple(map(int, match.groups())) >= (0, 153, 4),
            'runtime fixture requires Codex CLI 0.153.4 or newer: ' + version)
    if args.log_dir:
        args.log_dir.mkdir(parents=True, exist_ok=True)
    cases = [('disabled', {'enabled': False}), ('untrusted-before', {}),
             ('trusted-main', {'trusted': True}), ('untrusted-after', {}),
             ('worker', {'trusted': True, 'role': 'worker'}),
             ('reviewer', {'trusted': True, 'role': 'reviewer'})]
    with tempfile.TemporaryDirectory(prefix='devstandard-runtime-') as scratch:
        fixture = Path(scratch).resolve()
        isolation = inventory(fixture)
        native = native_plugin(binary, args.native_plugin, args.plugin_root) if args.native_plugin else None
        if native:
            isolation['plugins'] = 'only ' + native['selector']
            isolation['other_plugins_disabled'] = len(native['other_plugins'])
            isolation['native_skill_catalog'] = 'verified on the first request of every case'
        subprocess.run(['git', 'init', '--quiet', str(fixture)], check=True, capture_output=True)
        results = [run_case(binary, fixture, name, logs=args.log_dir, native=native, **options)
                   for name, options in cases if args.case is None or args.case == name]
    not_exercised = ['resume', 'clear', 'manual compact', 'automatic compact']
    if not native:
        not_exercised.insert(0, 'native plugin installation/discovery')
    print(json.dumps({'codex': version, 'isolation': isolation, 'results': results,
                      'not_exercised': not_exercised},
                     ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (AssertionError, OSError, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'fail', 'error': str(error)}))
        raise SystemExit(1)
