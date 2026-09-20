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
import functools
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
ARTIFACTS = ('reference/orchestrator.md', 'reference/harness-codex.md')
# Artifact selector -> page, as hooks/hooks.json spells it. A page above one output arrives in
# several ordered parts (ADR 0059), so wholeness here is checked part by part, not by one `in`.
SELECTORS = {'orchestrator': 'reference/orchestrator.md', 'codex': 'reference/harness-codex.md'}
# Read from the hook, never restated: the cap and the Codex limit hooks.json sets from it are
# stated together in `hooks/session-start`, beside this constant's definition.
INLINE_CAP_BYTES = int(re.search(
    r'^INLINE_CAP_BYTES=(\d+)$', (ROOT / 'hooks/session-start').read_text(), re.M)[1])
# The control's lever. Our own cap is now well under Codex's 2500-token default, so a part at it
# no longer reaches that default and the control would pass vacuously. The control therefore runs
# the same shipped hook with a raised cap of its own: what it measures is the HOST's default, not
# ours, and it must stay above whatever number a token-dense 2500 tokens occupies in bytes.
CONTROL_CAP_BYTES = 14000
CAP_HEAD = 'DEVSTANDARD_CAP_HEAD_389'
CAP_TAIL = 'DEVSTANDARD_CAP_TAIL_389'
# One marked line per ~47 bytes, the line density of the role pages this stands in for. The hook
# escapes its context in pure bash, and that cost rises with the line count, so a filler of much
# shorter lines would measure a page no project ships.
CAP_LINE = 'DEVSTANDARD_CAP_LINE_%05d ' + 'x' * 20 + '\n'
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
        # probe to exercise a refusal (`reference/orchestrator.md`, The role hook).
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


def hook_config(role, root=ROOT, keep_context_limit=True):
    """Run the shipped handlers, retaining their shipped lifecycle matchers/limits.

    Inline hooks do not get plugin environment variables, so supply the documented
    aliases explicitly. Native plugin environment/discovery is tested separately.
    `root` points the shipped commands at a fixture plugin root instead of this repository,
    and `keep_context_limit=False` strips `additionalContextLimit` from every handler — the
    one control case's lever, never a mode any shipped delivery runs in.
    """
    config = json.loads((ROOT / 'hooks/hooks.json').read_text())['hooks']
    for groups in config.values():
        for group in groups:
            for handler in group['hooks']:
                if not keep_context_limit:
                    handler.pop('additionalContextLimit', None)
                command = handler['command']
                command = command.replace('${CLAUDE_PLUGIN_ROOT}', str(root))
                command = command.replace('${PLUGIN_ROOT}', str(root))
                # Only the two audited entrypoints may receive invocation-wide trust.
                args = shlex.split(command)
                require(args[0] in (str(root / 'hooks/session-start'),
                                    str(root / 'hooks/pre-tool-use')),
                        'unvetted hook command: ' + command)
                require(all(part in SELECTORS or part.isdigit() for part in args[1:]),
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


def fixture_settings(port, *, enabled=True):
    """The `codex exec` settings every shell-hook case shares: local provider, no network."""
    return {
        'model_provider': 'devstandard-fixture',
        'model_providers.devstandard-fixture': {
            'name': 'Local deterministic DevStandard fixture',
            'base_url': 'http://127.0.0.1:' + str(port) + '/v1',
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


def run_case(binary, fixture, name, *, role=None, trusted=False, enabled=True, logs=None,
             native=None, prompt=None, carries=None):
    """`prompt` replaces the fixture's probe instruction with a dispatched worker's real one,
    and `carries` is the (source paths, resolved text) that prompt is supposed to deliver — the
    Codex CLI path where the PROMPT, not the hook, is what brings a worker its role pages."""
    forbidden = {'worker': 'tag', 'reviewer': 'push'}.get(role, 'git merge')
    with ResponsesFixture(forbidden) as server:
        settings = fixture_settings(server.server.server_port, enabled=enabled)
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
        command.append(
            prompt or 'Run the two harmless local printf probes supplied by the fixture, then finish.')
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
        # The hooks that actually ran belong to the installed plugin in `--native-plugin` mode,
        # and a part's header carries its plugin root — which also sets the header's length and
        # so the line boundary each part is cut at. Emit from the same root the host used, or
        # the parts compared against the request are a different split of the same page.
        source = native['root'] if native else ROOT
        for selector, artifact in SELECTORS.items():
            # Full source, including its middle, must survive hook delivery and spill handling —
            # every declared part of it, since one output may not hold the whole page.
            page = (source / artifact).read_bytes()
            contexts = delivered_contexts(str(source), selector)
            require(''.join(part_bodies(contexts)).encode() == page,
                    name + ': the hook itself does not rebuild ' + artifact)
            present = header_present(actual, contexts)
            expected = active and role is None
            require(bool(present) == expected,
                    name + ': incomplete full context delivery for ' + artifact)
            if not expected:
                head_probe, tail_probe = leak_probes(str(source), artifact)
                require(head_probe not in actual and tail_probe not in actual,
                        name + ': partial or spilled role context leaked from ' + artifact)
                continue
            # Decoded text, so JSON escaping cannot hide a missing tail — and reassembled by
            # part number out of the host's own request, because text presence of each part is
            # not the property this owes; the reconstructed page is.
            assembled, _ = reconstruct_from_request(actual, contexts, artifact)
            require(assembled.encode() == page,
                    name + ': ' + artifact + ' did not arrive byte-identical; the parts taken '
                    'from the host request reassemble to ' + str(len(assembled.encode()))
                    + ' bytes, the file is ' + str(len(page)))
            delivered.append(artifact)
        if carries:
            # #396's other half on this host: a dispatched Codex CLI worker's role page is
            # carried by the prompt, not by the hook, so what it owes is the page's exact bytes
            # in the host's own request — once, undivided, with the host role page suppressed
            # above rather than merely absent.
            carried_sources, carried_text = carries
            found = actual.count(carried_text)
            require(found == 1, name + ': the dispatched ' + ' + '.join(carried_sources)
                    + ' reached the model ' + str(found)
                    + ' times, want exactly one byte-identical copy')
            if logs:
                (logs / (name + '.role-delivery.json')).write_text(json.dumps(
                    {'artifact': list(carried_sources),
                     'page_bytes': [len((source / path).read_bytes()) for path in carried_sources],
                     'resolved_page_bytes': len(carried_text.encode()),
                     'carrier': 'scripts/dispatch brief as the codex exec prompt argument',
                     'arrived_byte_identical_in_request': True,
                     'host_role_page_delivered': delivered}, indent=2) + '\n')
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


def emitted_context(root, artifact, index=1, total=None):
    """The complete additionalContext the fixture root's own hook emits, and what it cost.

    Generous timeout on purpose: this is fixture preparation, and the hook's bash escaping of a
    page at the cap costs whole seconds on the system bash of some hosts (macOS ships 3.2). The
    elapsed time is returned rather than asserted on, so the case reports that cost per host
    instead of failing a delivery test over it.
    """
    env = {key: value for key, value in os.environ.items()
           if key not in ('PLUGIN_DATA', 'CLAUDE_PLUGIN_DATA', 'DEVSTANDARD_ROLE')}
    env.update(PLUGIN_DATA='devstandard-cap-fixture', CLAUDE_PLUGIN_DATA='devstandard-cap-fixture')
    started = time.monotonic()
    result = subprocess.run([str(root / 'hooks/session-start'), artifact,
                             str(index), str(total if total is not None else index)],
                            input='{"source":"startup"}', capture_output=True, text=True,
                            cwd=str(root), env=env, timeout=120, check=True)
    elapsed = time.monotonic() - started
    payload = json.loads(result.stdout)
    return payload.get('hookSpecificOutput', {}).get('additionalContext', ''), elapsed


def declared_handlers(selector):
    """The shipped SessionStart calls for one artifact: (part, declared parts) per handler."""
    groups = json.loads((ROOT / 'hooks/hooks.json').read_text())['hooks']['SessionStart']
    calls = []
    for group in groups:
        for handler in group['hooks']:
            args = shlex.split(handler['command'].replace('${CLAUDE_PLUGIN_ROOT}', '/plugin')
                               .replace('${PLUGIN_ROOT}', '/plugin'))
            if len(args) == 4 and args[1] == selector:
                calls.append((int(args[2]), int(args[3])))
    require(calls, 'no declared SessionStart handler for ' + selector)
    return sorted(calls)


@functools.lru_cache(maxsize=None)
def delivered_contexts(root, selector):
    """Each delivered part's complete emitted context, in part order, from this root's own hook.

    Concatenating their bodies is the page: that is the property a multi-part artifact is
    delivered under, and every caller here reassembles rather than searching for each part.
    """
    parts = []
    for index, total in declared_handlers(selector):
        context, _ = emitted_context(Path(root), selector, index, total)
        if context:
            require('requires an IN FULL read' not in context and 'part 0' not in context,
                    selector + ': the fixture hook degraded instead of delivering part '
                    + str(index))
            parts.append(context)
    return tuple(parts)


def part_bodies(contexts):
    """Each emitted context's page text, with its delivery header removed."""
    bodies = []
    for number, context in enumerate(contexts, start=1):
        head, blank, body = context.partition('\n\n')
        require(blank, 'part ' + str(number) + ': emitted context carries no delivery header')
        bodies.append(body)
    return bodies


def reconstruct_from_request(host_text, contexts, artifact):
    """Reassemble the page out of the text the HOST sent, in part order, and say where it landed.

    Each part is located by its own delivery header, which must appear exactly once, and the
    body is then taken FROM THE HOST TEXT rather than from the hook's output — so a part the
    host truncated, elided the middle of, escaped differently, dropped or duplicated cannot
    reconstruct the page. What the caller compares against the file is the delivery as the
    model received it, not a restatement of the file.

    The order is the parts' own numbering, which is what the delivery header tells the reader
    to reassemble by; the order they APPEAR in is the host's, returned and never asserted on.
    `.github/test-claude-runtime.py` carries the same helper for the Claude host; the two are
    one idea and change together.
    """
    assembled = ''
    arrival = []
    for number, context in enumerate(contexts, start=1):
        head, blank, body = context.partition('\n\n')
        require(blank, artifact + ' part ' + str(number) + ': context carries no delivery header')
        anchor = head + blank
        seen = host_text.count(anchor)
        require(seen == 1, artifact + ' part ' + str(number) + ' of ' + str(len(contexts))
                + ': its delivery header appears ' + str(seen)
                + ' times in the host request, want exactly one')
        start = host_text.index(anchor) + len(anchor)
        assembled += host_text[start:start + len(body)]
        arrival.append(host_text.index(anchor))
    return assembled, [number for number, _ in
                       sorted(enumerate(arrival, start=1), key=lambda row: row[1])]


def header_present(host_text, contexts):
    """How many of these parts' delivery headers the host request carries."""
    return sum(context.partition('\n\n')[0] in host_text for context in contexts)


@functools.lru_cache(maxsize=None)
def leak_probes(root, artifact):
    """Two 200-byte probes cut from the part of this page no OTHER role page also carries.

    Both role pages state the shared workflow contract in byte-identical paragraphs (ADR 0059),
    and until #413's fold of the worker page's exceptional events their last 200 bytes were the
    same block: a dispatched worker legitimately carrying its own page would trip a tail probe
    taken from the orchestrator's, and a spilled orchestrator tail would be indistinguishable
    from it. The shared suffix is measured below rather than assumed, so cutting the probes from
    this page's unique portion keeps the leak check meaning what it says whatever the two pages
    currently share.
    """
    unique = (Path(root) / artifact).read_text()
    for other in ('reference/orchestrator.md', 'reference/worker.md'):
        if other == artifact:
            continue
        text = (Path(root) / other).read_text()
        shared = 0
        while (shared < min(len(unique), len(text))
               and unique[-1 - shared] == text[-1 - shared]):
            shared += 1
        unique = unique[:len(unique) - shared]
    require(len(unique) >= 400, artifact + ': no unique portion left to probe a leak with')
    return unique[:200], unique[-200:]


def dispatched_worker_prompt(worktree):
    """The prompt `scripts/dispatch --implementation codex` hands `codex exec`.

    The dispatcher reads `reference/worker.md` unchanged — the page carries no template slot
    since #402 — then appends the marked worker-facing section of `reference/harness-codex.md`,
    because Codex has no carrier that survives a lost packet and the hook delivers that page to
    no dispatched child (ADR 0061). It writes the result as the lane's brief and passes it as the
    prompt argument; `.github/test-dispatch.py` asserts the argv carries it. This rebuilds the
    same shape so the real CLI can be asked what this test owes: do those exact bytes reach the
    model?
    """
    page = (ROOT / 'reference/worker.md').read_text()
    adapter = (ROOT / 'reference/harness-codex.md').read_text()
    mechanics = adapter.split('<!-- BEGIN CODEX WORKER MECHANICS -->\n', 1)[1] \
                       .split('<!-- END CODEX WORKER MECHANICS -->\n', 1)[0].strip('\n')
    require(mechanics, 'reference/harness-codex.md carries no worker-facing section')
    carried = page + '\n' + mechanics + '\n'
    packet = ('\n\n# Task packet\nIssue: https://github.com/o/r/issues/396\n'
              'Branch: task/396-runtime-fixture\nWorktree: ' + str(worktree) + '\n'
              'Named base: origin/main\nRole references resolve from: ' + str(ROOT) + '\n\n'
              'Run the two harmless local printf probes supplied by the fixture, then finish.\n')
    return carried, carried + packet


def pad_adapter_to_cap(root, cap):
    """Pad the fixture's adapter page until one hook output is exactly `cap` bytes.

    Same technique as `.github/test-session-start.py`'s at-cap case, so the two at-cap tests stay
    one idea: measure the delivery overhead once, then fill the remainder. The filler is numbered
    ASCII lines between a head and a tail marker, so the case reports which parts of the page
    reached the model instead of only that something was missing. The adapter is the artifact that
    still ships inside one output, which is what this boundary is about; the orchestrator page's
    multi-part delivery is measured in the same run, below.
    """
    line = len(CAP_LINE % 0)
    page = root / 'reference/harness-codex.md'
    page.write_text('X')
    overhead, _ = emitted_context(root, 'codex')
    fill = cap - (len(overhead.encode()) - 1)
    require(fill > len(CAP_HEAD) + len(CAP_TAIL) + line,
            'fixture delivery overhead leaves no room to pad the adapter to the cap')
    body = CAP_HEAD + '\n' + ''.join(CAP_LINE % number for number in range(fill // line + 2))
    content = body[:fill - len(CAP_TAIL)] + CAP_TAIL
    require(len(content.encode()) == fill, 'padded fixture page is not the intended size')
    page.write_text(content)
    context, seconds = emitted_context(root, 'codex')
    require(len(context.encode()) == cap,
            'padded fixture context is ' + str(len(context.encode())) + ' bytes, want the cap')
    require(content in context, 'the hook itself did not deliver the padded page whole')
    return content, context, round(seconds, 2)


def run_cap_case(binary, name, *, honour_limit, logs=None):
    """#389: left unset, Codex truncates a hook's additional context at 2500 tokens, and it drops
    the context's MIDDLE rather than its tail — a role page keeps the opening that identifies it
    and an ending that looks like an ending, and loses the rules in between, which is why nothing
    reported it for as long as our own cap happened to sit under theirs.

    `hooks/hooks.json` therefore sets `additionalContextLimit` from `INLINE_CAP_BYTES`: our cap is
    bytes and theirs is tokens, and a token is never shorter than one byte, so a limit numerically
    equal to the byte cap cannot cut a page the byte cap already admits. `.github/test-codex-plugin.py`
    enforces that conversion offline; this case is the real host's answer to it — a page padded to
    exactly the cap, delivered by the shipped handler, arriving byte-identical from the pinned CLI.

    The control, the same shipped handler with the key stripped, is what keeps the honoured case
    from being vacuous: it is the truncation this issue was opened for, in the same fixture. It runs
    at `CONTROL_CAP_BYTES` rather than the shipped cap, because the shipped cap now sits below the
    host default and a part at it would not reach the truncation at all. If the control ever stops
    truncating at that size, the host's default has moved — re-measure it and restate it beside
    `INLINE_CAP_BYTES` in `hooks/session-start`. It is not a case to delete quietly.
    """
    with tempfile.TemporaryDirectory(prefix='devstandard-cap-') as scratch:
        scratch = Path(scratch).resolve()
        project = scratch / 'project'
        project.mkdir()
        inventory(project)
        subprocess.run(['git', 'init', '--quiet', str(project)], check=True, capture_output=True)
        root = scratch / 'plugin'
        (root / 'hooks').mkdir(parents=True)
        (root / 'reference').mkdir()
        for path in ('hooks/session-start', 'hooks/pre-tool-use', 'hooks/hooks.json', *ARTIFACTS):
            shutil.copy2(ROOT / path, root / path)
        cap = INLINE_CAP_BYTES
        if not honour_limit:
            # Raise only the control fixture's own cap, so its single part sits above the host
            # default this case exists to measure. Never a mode any shipped delivery runs in.
            cap = CONTROL_CAP_BYTES
            hook = root / 'hooks/session-start'
            hook.write_text(re.sub(r'^INLINE_CAP_BYTES=\d+$', 'INLINE_CAP_BYTES=' + str(cap),
                                   hook.read_text(), count=1, flags=re.M))
            require(str(cap) in hook.read_text(), 'control fixture cap was not applied')
        page, context, hook_seconds = pad_adapter_to_cap(root, cap)
        config = hook_config(None, root, keep_context_limit=honour_limit)
        limits = sorted({handler.get('additionalContextLimit')
                         for group in config['SessionStart'] for handler in group['hooks']}, key=str)
        with ResponsesFixture('git merge') as server:
            settings = fixture_settings(server.server.server_port)
            for event, groups in config.items():
                settings['hooks.' + event] = groups
            command = [binary, 'exec', '--ignore-user-config', '--ephemeral', '--json',
                       '-s', 'read-only', '-C', str(project), '-m', 'devstandard-fixture']
            for key, value in settings.items():
                command += ['-c', key + '=' + toml(value)]
            command += ['--dangerously-bypass-hook-trust',
                        'Run the two harmless local printf probes supplied by the fixture, then finish.']
            env = dict(os.environ)
            for key in ('DEVSTANDARD_ROLE', 'PLUGIN_DATA', 'CLAUDE_PLUGIN_DATA',
                        'PLUGIN_ROOT', 'CLAUDE_PLUGIN_ROOT', 'OPENAI_API_KEY'):
                env.pop(key, None)
            started = time.monotonic()
            result = subprocess.run(command, env=env, stdin=subprocess.DEVNULL,
                                    capture_output=True, text=True, timeout=45)
        if logs:
            (logs / (name + '.events.jsonl')).write_text(result.stdout)
            (logs / (name + '.stderr.log')).write_text(result.stderr)
        require(result.returncode == 0, name + ': Codex failed: ' + result.stderr[-2000:])
        require(not server.errors, name + ': ' + repr(server.errors))
        require(len(server.requests) == 3, name + ': expected two tool calls and final request, got '
                + str(len(server.requests)) + '; ' + result.stderr[-1000:])
        # Compare decoded text, as `trusted-main` does, so JSON escaping cannot hide a missing part.
        actual = '\n'.join(text_fragments(server.requests[0].get('input', [])))
        marked = re.findall(r'DEVSTANDARD_CAP_LINE_\d{5}', page)
        arrived = set(re.findall(r'DEVSTANDARD_CAP_LINE_\d{5}', actual)) & set(marked)
        # The other half of #396's delivery proof, measured in the same run: the shipped
        # orchestrator page is larger than one output, so it arrives only if every declared
        # part does. The parts are this fixture root's own hook output, so what is compared
        # against the request is the delivery's own bytes.
        role_contexts = delivered_contexts(str(root), 'orchestrator')
        role_bodies = part_bodies(role_contexts)
        role_page = (root / 'reference/orchestrator.md').read_bytes()
        require(''.join(role_bodies).encode() == role_page,
                name + ': the fixture hook does not rebuild the orchestrator page')
        role_arrival = []
        role_assembled = None
        if header_present(actual, role_contexts) == len(role_contexts):
            role_assembled, role_arrival = reconstruct_from_request(
                actual, role_contexts, 'reference/orchestrator.md')
        measured = {'inline_cap_bytes': cap,
                    'shipped_cap_bytes': INLINE_CAP_BYTES,
                    'role_page_bytes': len(role_page),
                    'role_page_parts': len(role_contexts),
                    'role_page_part_bytes': [len(body.encode()) for body in role_bodies],
                    'role_page_headers_in_request': header_present(actual, role_contexts),
                    'role_page_reassembled_bytes':
                        None if role_assembled is None else len(role_assembled.encode()),
                    # The host's own arrival order, recorded and never asserted on. Codex CLI
                    # 0.153.4 has so far been observed only in part order; Claude Code 2.1.270
                    # runs the declared handlers concurrently and appends each context as its
                    # process finishes, giving a different order between runs (#396). Neither
                    # host promises one, so the part numbers carry the order.
                    'role_page_prompt_arrival_order': role_arrival,
                    'role_page_whole_in_request':
                        role_assembled is not None and role_assembled.encode() == role_page,
                    'additional_context_limit': limits,
                    'emitted_context_bytes': len(context.encode()),
                    'page_bytes': len(page.encode()),
                    'page_byte_identical_in_request': context in actual,
                    'marked_lines': len(marked), 'marked_lines_delivered': len(arrived),
                    'page_head_present': page[:200] in actual,
                    'page_tail_present': page[-200:] in actual,
                    # Reported, never asserted on: what this host's bash costs to escape and emit
                    # a page at the cap. Slow system bash is a host property, not a delivery fault.
                    'hook_emit_seconds': hook_seconds,
                    'seconds': round(time.monotonic() - started, 2)}
        diagnostic = json.dumps(measured)
        if honour_limit:
            require(measured['page_byte_identical_in_request'],
                    name + ': a page at the inline cap did not arrive whole from the Codex host; '
                    + diagnostic)
            require(measured['role_page_parts'] > 1,
                    name + ': the orchestrator page no longer exceeds one output, so this run '
                    'proves nothing about multi-part delivery; ' + diagnostic)
            require(measured['role_page_whole_in_request'],
                    name + ': the multi-part orchestrator page did not arrive whole from the '
                    'Codex host; ' + diagnostic)
        else:
            require(not measured['page_byte_identical_in_request'],
                    name + ': the host delivered a page above its default limit whole, so that '
                    'default has moved: re-measure it and restate it beside INLINE_CAP_BYTES in '
                    'hooks/session-start; ' + diagnostic)
            require(measured['page_head_present'] and measured['page_tail_present'],
                    name + ': the measured truncation is a middle elision keeping the head and the '
                    'tail, and this delivery is neither whole nor that; ' + diagnostic)
        summary = {'case': name, 'status': 'pass', **measured}
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
                                         'untrusted-after', 'worker', 'worker-brief', 'reviewer',
                                         'mcp-refused-without-the-setting', 'mcp-reviewer',
                                         'mcp-worker', 'mcp-worker-code-mode',
                                         'cap-at-the-inline-cap',
                                         'cap-truncated-without-the-setting'])
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
        # The standing dispatched path on this host: `--implementation codex` passes the brief,
        # which opens with the resolved worker page and the Codex harness's worker section under
        # it, as the prompt. The hook delivers no page to a dispatched child (DEVSTANDARD_ROLE),
        # so the prompt is the only carrier of either and must be exact.
        if args.case is None or args.case == 'worker-brief':
            carried, prompt = dispatched_worker_prompt(fixture)
            results.append(run_case(binary, fixture, 'worker-brief', trusted=True, role='worker',
                                    prompt=prompt,
                                    carries=(('reference/worker.md',
                                              'reference/harness-codex.md'), carried),
                                    logs=args.log_dir, native=native))
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
    # #389: the byte cap our own gates enforce, answered by the host that also limits delivery.
    cap_cases = [('cap-at-the-inline-cap', True), ('cap-truncated-without-the-setting', False)]
    results += [run_cap_case(binary, name, honour_limit=honour, logs=args.log_dir)
                for name, honour in cap_cases if args.case is None or args.case == name]
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
