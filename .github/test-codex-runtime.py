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
import sys
import tempfile
import threading
import time


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ('core.md', 'reference/orchestrator.md', 'reference/harness-codex.md')
ALLOW = 'DEVSTANDARD_RUNTIME_ALLOWED_342'
DENY = 'DEVSTANDARD_RUNTIME_EXECUTED_342'
MCP_TOKEN = 'DEVSTANDARD_MCP_TOOL_RAN_358'
MCP_SERVER_NAME = 'probe'
MCP_TOOL_NAME = 'devstandard_probe'
MCP_BINDING = 'mcp__' + MCP_SERVER_NAME + '__' + MCP_TOOL_NAME
# The exact setting scripts/dispatch appends per host MCP server. Held here as well so this
# case fails if the dispatcher stops emitting it, not only if the CLI stops honouring it.
MCP_APPROVAL = 'mcp_servers.{name}.default_tools_approval_mode="approve"'
MCP_SERVER = '''import json, sys
from pathlib import Path
LOG = Path(sys.argv[1])
TOOL = {'name': %r, 'description': 'Return one fixed token. No side effects.',
        'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False}}
RESULTS = {'initialize': {'protocolVersion': '2025-06-18', 'capabilities': {'tools': {}},
                          'serverInfo': {'name': 'devstandard-probe', 'version': '1.0.0'}},
           'tools/list': {'tools': [TOOL]},
           'tools/call': {'content': [{'type': 'text', 'text': %r}], 'isError': False},
           'ping': {}}
for line in sys.stdin:
    if not line.strip():
        continue
    message = json.loads(line)
    with LOG.open('a') as record:
        record.write(json.dumps({'method': message.get('method')}) + '\\n')
    if 'id' not in message:
        continue
    result = RESULTS.get(message.get('method'))
    answer = ({'jsonrpc': '2.0', 'id': message['id'], 'result': result} if result is not None else
              {'jsonrpc': '2.0', 'id': message['id'],
               'error': {'code': -32601, 'message': 'unsupported'}})
    sys.stdout.write(json.dumps(answer) + '\\n')
    sys.stdout.flush()
''' % (MCP_TOOL_NAME, MCP_TOKEN)


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
        # The refused probe stays a harmless `printf`, with the guarded word as an unquoted
        # operand. It used to sit inside the quoted format string; since #351 the hook does
        # not read quoted text, so the word has to stand in the command itself for this
        # probe to exercise a refusal (`reference/hard-edges.md`, The role hook).
        command = ('printf ' + shlex.quote(ALLOW + '\n') if index == 0 else
                   'printf ' + shlex.quote(DENY + '\n') + ' ' + self.forbidden)
        return {'type': 'function_call', 'id': 'fc_' + str(index),
                'call_id': 'call_' + str(index), 'name': 'exec_command',
                'arguments': json.dumps({'cmd': command, 'login': False,
                                         'max_output_tokens': 100})}


class McpFixture(ResponsesFixture):
    """Two turns: call the single tool the local stdio MCP server offers, then finish.

    Codex offers that tool in one of two shapes, and this case exercises whichever the host
    actually produces rather than configuring one into existence. Without code mode the server
    arrives as its own `mcp__<server>` namespace. With code mode — the default a dispatched
    child runs under — only `exec` is offered and MCP tools live on the JavaScript `tools`
    object as `mcp__<server>__<tool>`, so a flip in that default cannot quietly leave this case
    exercising no MCP call at all.
    """

    def __init__(self, prefer=None):
        super().__init__('git merge')  # No shell probe runs in this case.
        self.prefer, self.shape = prefer, None

    @staticmethod
    def catalog(request):
        supplied = list(request.get('tools', []))
        for item in request.get('input', []):
            if item.get('type') == 'additional_tools':
                supplied.extend(item.get('tools', []))
        found = {}
        for tool in supplied:
            if tool.get('type') == 'namespace':
                for member in tool.get('tools', []):
                    found[member['name']] = tool['name']
            elif tool.get('name'):
                found[tool['name']] = None
        return found

    def response_item(self, request, index):
        if index:
            return {'type': 'message', 'id': 'msg_mcp', 'role': 'assistant', 'status': 'completed',
                    'content': [{'type': 'output_text', 'text': 'MCP fixture complete.',
                                 'annotations': []}]}
        item, self.shape = mcp_call_item(request, 'fc_mcp', 'call_mcp', self.prefer)
        return item


def mcp_call_item(request, item_id, call_id, prefer=None):
    """Build the one MCP tool call in whichever shape the host actually offers this turn.

    Returns the response item and the label naming that shape. Lifted out of `McpFixture` so the
    native suite can make the same call the same way (#373) instead of growing a second fixture;
    it decides nothing this class did not already decide, and asserts nothing.
    """
    catalog = McpFixture.catalog(request)
    direct = None if prefer == 'code-mode' else next(
        (name for name, space in catalog.items()
         if space and str(space).startswith('mcp__')), None)
    if direct:
        return ({'type': 'function_call', 'id': item_id, 'call_id': call_id,
                 'namespace': catalog[direct], 'name': direct, 'arguments': '{}'},
                'mcp namespace tool')
    require('exec' in catalog, 'Codex offered neither an MCP namespace nor code mode: '
            + repr(sorted(catalog)))
    # Caught and reported as text, so a denied call reaches the model as a result to
    # assert on rather than as an opaque script failure.
    script = ('try { text(JSON.stringify(await tools.' + MCP_BINDING + '({}))); } '
              "catch (error) { text('MCP_CALL_ERROR ' + String(error)); }")
    item = {'type': 'custom_tool_call', 'id': item_id, 'call_id': call_id,
            'name': 'exec', 'input': script}
    if catalog['exec']:
        item['namespace'] = catalog['exec']
    return item, 'code-mode tools.' + MCP_BINDING


def run_mcp_case(binary, name, *, sandbox, admit, prefer=None, logs=None):
    """#358: a dispatched Codex child could see its host's MCP tools and never call one.

    `codex exec` is non-interactive, so its approval policy is `never`, and `never` auto-rejects
    every MCP tool call — indistinguishably from an unreachable server. The `admit=False` case is
    that defect, kept as the control: it is what CI was green on. The rest are the fix — one per
    purpose, proving the admission composes with each sandbox mode rather than trading it away, and
    one pinning the code-mode call shape a dispatched child runs under.
    This is also the guard for the next `@openai/codex` pin bump, which is half its value: the
    behaviour already moved once between 0.149.1 and 0.153.4.
    """
    require(MCP_APPROVAL in (ROOT / 'scripts/dispatch').read_text(),
            'scripts/dispatch no longer emits the qualified MCP approval setting')
    with tempfile.TemporaryDirectory(prefix='devstandard-mcp-') as scratch:
        scratch = Path(scratch).resolve()
        project = scratch / 'project'
        project.mkdir()
        inventory(project)
        subprocess.run(['git', 'init', '--quiet', str(project)], check=True, capture_output=True)
        # A run that configures an MCP server persists a project trust entry, which
        # `--ignore-user-config` does not prevent: that flag governs reading, not writing.
        # This case therefore gets its own CODEX_HOME, so it changes no user state — the
        # promise this file's docstring makes and `test-codex-install.py` checks.
        codex_home = scratch / 'codex-home'
        codex_home.mkdir()
        server = scratch / 'mcp-server.py'
        server.write_text(MCP_SERVER)
        log = scratch / 'mcp-calls.jsonl'
        with McpFixture(prefer) as fixture:
            settings = {
                'model_provider': 'devstandard-fixture',
                'model_providers.devstandard-fixture': {
                    'name': 'Local deterministic DevStandard fixture',
                    'base_url': 'http://127.0.0.1:' + str(fixture.server.server_port) + '/v1',
                    'wire_api': 'responses', 'requires_openai_auth': False,
                    'supports_websockets': False, 'request_max_retries': 0,
                    'stream_max_retries': 0, 'stream_idle_timeout_ms': 5000},
                'features.hooks': False, 'features.plugins': False,
                'features.apps': False, 'features.remote_plugin': False,
                'features.enable_request_compression': False,
                # Code mode decides which shape the MCP tool arrives in, and a dispatched child
                # runs under whichever the host defaults to, so neither shape is assumed: cases
                # leave it alone, and one case pins it on to cover that arm deliberately.
                'features.shell_snapshot': False,
                'features.multi_agent': False, 'features.skip_host_skill_discovery': True,
                'web_search': 'disabled', 'check_for_update_on_startup': False,
                # The policy axis is not the lever: `exec` ignores every value it is given.
                'approval_policy': 'never', 'analytics.enabled': False,
                # Local, deterministic, offline: one tool returning one fixed token.
                'mcp_servers.' + MCP_SERVER_NAME: {
                    'command': sys.executable, 'args': [str(server), str(log)],
                    'startup_timeout_sec': 30, 'tool_timeout_sec': 30},
            }
            if prefer == 'code-mode':
                settings['features.code_mode'] = True
            command = [binary, 'exec', '--ignore-user-config', '--ephemeral', '--json',
                       '-s', sandbox, '-C', str(project), '-m', 'devstandard-fixture']
            for key, value in settings.items():
                command += ['-c', key + '=' + toml(value)]
            if admit:
                command += ['-c', MCP_APPROVAL.format(name=MCP_SERVER_NAME)]
            command.append('Call the one MCP probe tool the fixture offers, then finish.')
            env = dict(os.environ, CODEX_HOME=str(codex_home))
            for key in ('DEVSTANDARD_ROLE', 'PLUGIN_DATA', 'CLAUDE_PLUGIN_DATA',
                        'PLUGIN_ROOT', 'CLAUDE_PLUGIN_ROOT', 'OPENAI_API_KEY'):
                env.pop(key, None)
            started = time.monotonic()
            result = subprocess.run(command, env=env, stdin=subprocess.DEVNULL,
                                    capture_output=True, text=True, timeout=90)
        methods = [json.loads(line)['method'] for line in log.read_text().splitlines()] \
            if log.exists() else []
        # Code mode returns the same call as a custom_tool_call_output, so read both forms.
        answer = str({item['call_id']: item.get('output', '')
                      for item in fixture.requests[-1].get('input', [])
                      if item.get('type') in ('function_call_output', 'custom_tool_call_output')}
                     .get('call_mcp', '<missing>'))
        diagnostic = json.dumps({'server_methods': methods, 'tool_result': answer[-1500:],
                                 'stderr_tail': result.stderr[-2000:]})
        if logs:
            (logs / (name + '.events.jsonl')).write_text(result.stdout)
            (logs / (name + '.mcp.json')).write_text(diagnostic + '\n')
        require(result.returncode == 0, name + ': Codex failed: ' + result.stderr[-2000:])
        require(not fixture.errors, name + ': ' + repr(fixture.errors))
        # The server's own method log and the model's tool result are independent witnesses:
        # neither alone separates "the call was refused" from "the server never answered".
        require('tools/list' in methods, name + ': the MCP server was never listed; ' + diagnostic)
        if admit:
            require('tools/call' in methods, name + ': no call reached the server; ' + diagnostic)
            require(MCP_TOKEN in answer, name + ': the tool result never reached the model; '
                    + diagnostic)
        else:
            require('tools/call' not in methods, name + ': control case called the server; '
                    + diagnostic)
            require('approval policy is never' in answer,
                    name + ': control case was refused for another reason; ' + diagnostic)
        summary = {'case': name, 'status': 'pass', 'sandbox': sandbox,
                   'codex_home': 'scratch', 'user_state': 'unchanged',
                   'mcp_approval': 'per-server approve' if admit else 'none (control)',
                   'call_shape': fixture.shape, 'server_methods': methods,
                   'seconds': round(time.monotonic() - started, 2)}
        if logs:
            (logs / (name + '.summary.json')).write_text(json.dumps(summary, indent=2) + '\n')
        return summary


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
        events = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
        commands = [event['item'] for event in events if event.get('type') == 'item.completed'
                    and event.get('item', {}).get('type') == 'command_execution']
        # An admitted tool can still fail before its process starts (for example,
        # Linux sandbox setup). Keep that cause in CI output even without --log-dir.
        # These are only the fixture's fixed printf results, never full model requests.
        allow_diagnostic = json.dumps({
            'tool_output': str(outputs.get('call_0', '<missing call_0 result>'))[-2500:],
            'command_events': [{key: item.get(key) for key in
                               ('status', 'exit_code', 'command', 'aggregated_output')}
                              for item in commands],
            'stderr_tail': result.stderr[-3000:],
        })
        require(ALLOW in str(outputs.get('call_0', '')),
                name + ': admitted shell did not execute; ' + allow_diagnostic)
        require(any(item.get('aggregated_output') == ALLOW + '\n'
                    and item.get('exit_code') == 0 for item in commands),
                name + ': no successful printf execution in Codex events; ' + allow_diagnostic)
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
            # The guarded word is an ignored operand now, so the format alone is the output.
            require(any(item.get('aggregated_output') == DENY + '\n'
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
                                         'untrusted-after', 'worker', 'reviewer',
                                         'mcp-refused-without-the-setting', 'mcp-reviewer',
                                         'mcp-worker', 'mcp-worker-code-mode'])
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
    # The sandbox mode each purpose gets is unchanged; only the MCP admission differs (#358).
    mcp_cases = [('mcp-refused-without-the-setting', 'read-only', False, None),
                 ('mcp-reviewer', 'read-only', True, None),
                 ('mcp-worker', 'workspace-write', True, None),
                 # Code mode reaches an MCP tool through `exec`'s JavaScript rather than through
                 # the tool's own namespace, and a dispatched child on a default host runs in
                 # that arm, so it gets a case instead of being left to the host's default.
                 ('mcp-worker-code-mode', 'workspace-write', True, 'code-mode')]
    results += [run_mcp_case(binary, name, sandbox=sandbox, admit=admit, prefer=prefer,
                             logs=args.log_dir)
                for name, sandbox, admit, prefer in mcp_cases
                if args.case is None or args.case == name]
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
