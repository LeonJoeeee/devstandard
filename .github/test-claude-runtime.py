#!/usr/bin/env python3
"""Exercise Claude Code plugin discovery and hooks with a local Anthropic fixture.

No external model calls, permission bypass, global settings edits or production
checkout changes. Requires Python 3.11+ and the Claude CLI. The isolated invocation
keeps HOME unchanged, ignores user/project/local settings, disables external MCP,
and permits only the fixture's harmless Bash printf commands. Stored logs include
the fixture requests and CLI events, never real authentication headers.
"""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import runpy
import shutil
import signal
import subprocess
import tempfile
import threading
import time


ROOT = Path(__file__).resolve().parents[1]
ALLOW = 'DEVSTANDARD_CLAUDE_ALLOWED_342'
DENY = 'DEVSTANDARD_CLAUDE_EXECUTED_342'
DUMMY_KEY = 'devstandard-local-fixture-no-real-credentials'


def require(condition, message):
    if not condition:
        raise AssertionError(message)


class AnthropicFixture:
    def __init__(self, forbidden, native_role=None, diagnostic=None, parent_denial=False):
        self.requests = []
        self.child_requests = []
        self.main_requests = []
        self.errors = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                try:
                    require(self.path.split('?', 1)[0] == '/v1/messages',
                            'unexpected local endpoint: ' + self.path)
                    require(self.headers.get('x-api-key') == DUMMY_KEY,
                            'fixture did not receive its dummy API key')
                    require(not self.headers.get('Authorization'),
                            'fixture unexpectedly received an authorization header')
                    body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                    outer.requests.append(body)
                    if diagnostic:
                        diagnostic.write_text(json.dumps(outer.requests, indent=2))
                    step = len(outer.requests)
                    require(step <= (8 if parent_denial else 7 if native_role else 3),
                            'unexpected extra model continuation')
                    model = body['model']
                    is_child = native_role and ('You are the DevStandard ' + native_role
                                                in json.dumps(body.get('system')))
                    lane = outer.child_requests if is_child else outer.main_requests
                    lane.append(body)
                    logical_step = len(lane) if not native_role or is_child else 3
                    require(not is_child or len(lane) <= 3, 'unexpected child continuation')
                    block = ({'type': 'tool_use', 'id': 'toolu_devstandard_' + str(logical_step),
                              'name': 'Bash', 'input': {'command':
                              "printf '%s\\n' '" + (ALLOW if logical_step == 1 else DENY)
                              + ("'" if logical_step == 1 else " " + forbidden + "'")}}
                             if logical_step in (1, 2)
                             else {'type': 'text', 'text': 'Fixture complete.'})
                    if native_role and not is_child and len(lane) == (2 if parent_denial else 1):
                        block = {'type': 'tool_use', 'id': 'toolu_devstandard_agent',
                                 'name': 'Agent', 'input': {
                                     'subagent_type': 'devstandard:' + native_role,
                                     'description': 'Verify isolated role hooks',
                                     'prompt': 'Exercise the deterministic local fixture.'}}
                    elif parent_denial and not is_child and len(lane) == 1:
                        block = {'type': 'tool_use', 'id': 'toolu_devstandard_parent_denied',
                                 'name': 'Bash', 'input': {
                                     'command': "printf '%s\\n' '" + DENY + " release'"}}
                    uses_tool = block['type'] == 'tool_use'
                    events = [
                        ('message_start', {'type': 'message_start', 'message': {
                            'id': 'msg_devstandard_' + str(step), 'type': 'message',
                            'role': 'assistant', 'model': model, 'content': [],
                            'stop_reason': None, 'stop_sequence': None,
                            'usage': {'input_tokens': 100, 'output_tokens': 1}}}),
                        ('content_block_start', {'type': 'content_block_start', 'index': 0,
                            'content_block': ({**block, 'input': {}} if uses_tool
                                              else {'type': 'text', 'text': ''})}),
                        ('content_block_delta', {'type': 'content_block_delta', 'index': 0,
                            'delta': ({'type': 'input_json_delta',
                                       'partial_json': json.dumps(block['input'])} if uses_tool
                                      else {'type': 'text_delta', 'text': block['text']})}),
                        ('content_block_stop', {'type': 'content_block_stop', 'index': 0}),
                        ('message_delta', {'type': 'message_delta', 'delta': {
                            'stop_reason': 'tool_use' if uses_tool else 'end_turn',
                            'stop_sequence': None}, 'usage': {'output_tokens': 20}}),
                        ('message_stop', {'type': 'message_stop'}),
                    ]
                    payload = ''.join('event: ' + name + '\ndata: ' + json.dumps(data)
                                      + '\n\n' for name, data in events).encode()
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/event-stream')
                    self.send_header('Content-Length', str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except Exception as error:
                    outer.errors.append(str(error))
                    if diagnostic:
                        diagnostic.with_suffix('.errors.json').write_text(json.dumps(outer.errors))
                    self.send_error(500)

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()


def runtime(binary, fixture_dir, log_dir, role):
    case = role
    from_worker = case == 'native-reviewer-from-cli-worker'
    native = role.startswith('native-')
    marker = role.startswith('cli-')
    role = 'reviewer' if from_worker else role.removeprefix('native-').removeprefix('cli-')
    forbidden = {'orchestrator': 'git merge', 'worker': 'release', 'reviewer': 'push'}[role]
    with AnthropicFixture(forbidden, role if native else None,
                          log_dir / (case + '.requests.json')) as fixture:
        env = {key: value for key, value in os.environ.items()
               if key in ('HOME', 'USER', 'LOGNAME', 'PATH', 'LANG', 'LC_ALL', 'TMPDIR')}
        env.update(TMPDIR=str(fixture_dir), ANTHROPIC_API_KEY=DUMMY_KEY,
                   ANTHROPIC_BASE_URL='http://127.0.0.1:' + str(fixture.server.server_port),
                   CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1',
                   CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL='1',
                   CLAUDE_CODE_DISABLE_THINKING='1',
                   CLAUDE_CODE_DISABLE_NONSTREAMING_FALLBACK='1')
        if marker or from_worker:
            env['DEVSTANDARD_ROLE'] = 'worker' if from_worker else role
        command = [binary, '-p', 'Exercise the deterministic local fixture.',
                   '--restricted', '--setting-sources', '',
                   '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
                   '--plugin-dir', str(ROOT), '--tools',
                   'Bash,Read,Write,Edit' + (',Agent' if native else ''),
                   '--allowedTools', 'Bash(printf *)', '--permission-mode', 'dontAsk',
                   '--permission-prompts', 'none', '--no-session-persistence',
                   '--no-chrome', '--disable-slash-commands',
                   '--output-format', 'stream-json', '--verbose', '--include-hook-events',
                   '--debug-file', str(log_dir / (case + '.debug.log')),
                   '--model', 'claude-sonnet-4-6']
        if native:
            command += ['--allowedTools', 'Agent']
            if from_worker:
                command += ['--agent', 'devstandard:worker']
        elif role != 'orchestrator':
            command += ['--agent', 'devstandard:' + role]
        try:
            result = subprocess.run(command, cwd=fixture_dir, env=env,
                                    capture_output=True, text=True, timeout=90)
        except subprocess.TimeoutExpired as error:
            result = subprocess.CompletedProcess(command, 124,
                (error.stdout or b'').decode() if isinstance(error.stdout, bytes)
                else error.stdout or '',
                (error.stderr or b'').decode() if isinstance(error.stderr, bytes)
                else error.stderr or '')
    (log_dir / (case + '.stdout.jsonl')).write_text(result.stdout)
    (log_dir / (case + '.stderr.log')).write_text(result.stderr)
    (log_dir / (case + '.requests.json')).write_text(json.dumps(fixture.requests, indent=2))
    require(not fixture.errors, 'fixture protocol errors: ' + repr(fixture.errors))
    require(result.returncode == 0, role + ' CLI failed: ' + result.stderr[-2000:])
    rows = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
    init = next((row for row in rows if row.get('type') == 'system'
                 and row.get('subtype') == 'init'), {})
    plugins = init.get('plugins', [])
    require([row['name'] for row in plugins] == ['devstandard'],
            'unexpected plugins in isolated invocation: ' + repr(plugins))
    require(not init.get('mcp_servers'), 'unrelated MCP server was loaded')
    require(len(fixture.child_requests if native else fixture.requests) == 3,
            case + ' did not complete both shell requests')
    request_text = json.dumps(fixture.requests[0], ensure_ascii=False)
    require('unknown harness' not in request_text, 'Claude plugin environment not recognized')
    if role == 'orchestrator' or (native and not from_worker):
        for artifact in ('core.md', 'reference/orchestrator.md'):
            require('DevStandard operating context: ' + artifact in request_text,
                    'missing delivered artifact ' + artifact)
        require('DevStandard operating context: reference/harness-codex.md' not in request_text,
                'Codex adapter leaked into Claude')
    else:
        require('DevStandard operating context: reference/orchestrator.md' not in request_text,
                'direct CLI worker/reviewer inherited orchestrator context')
        require('You are the DevStandard ' + ('worker' if from_worker else role) in request_text,
                'direct CLI worker/reviewer did not receive its shipped role')
    tool_results = []
    evidence_request = fixture.child_requests[-1] if native else fixture.requests[-1]
    for message in evidence_request['messages']:
        if isinstance(message.get('content'), list):
            tool_results += [block for block in message['content']
                             if block.get('type') == 'tool_result']
    allow_id = 'toolu_devstandard_1'
    deny_id = 'toolu_devstandard_2'
    allow = [block for block in tool_results if block.get('tool_use_id') == allow_id]
    deny = [block for block in tool_results if block.get('tool_use_id') == deny_id]
    require(len(allow) == len(deny) == 1, 'missing shell result evidence')
    require(not allow[0].get('is_error') and ALLOW in json.dumps(allow[0]),
            'harmless allowed command did not execute')
    require(deny[0].get('is_error') and role in json.dumps(deny[0])
            and 'refus' in json.dumps(deny[0]).lower(),
            'guard did not refuse the forbidden command for ' + role)
    if native:
        require('You are the DevStandard ' + role in json.dumps(fixture.child_requests[0]),
                'native Agent did not receive the shipped role')
        require('DevStandard operating context: reference/orchestrator.md'
                not in json.dumps(fixture.child_requests[0]),
                'native Agent inherited orchestrator context')
    if role == 'reviewer':
        role_request = fixture.child_requests[0] if native else fixture.requests[0]
        writers = {'Write', 'Edit'} & {tool['name'] for tool in role_request['tools']}
        require(not writers, 'reviewer exposes disallowed built-in writers: ' + repr(writers))
    return {'role': case, 'requests': len(fixture.requests),
            'plugin': plugins[0], 'allowed': 'executed', 'forbidden': 'denied by role hook'}


def dispatch_cli(binary, log_dir, native_background=False):
    """Run the real dispatcher/supervisor/Claude chain; only GitHub is simulated.

    Reuse the command-level tests' real Git fixture and controlled gh executable.
    The Claude wrapper adds this fixture's isolation and local endpoint only; it
    preserves every dispatched argument, cwd, brief stdin and JSON Lines output.
    """
    case_type = runpy.run_path(str(ROOT / '.github/test-dispatch.py'))['DispatchTest']
    case = case_type()
    case.setUp()
    record = None
    label = 'dispatch-cli-native' if native_background else 'dispatch-cli'
    try:
        with AnthropicFixture('push' if native_background else 'release',
                              native_role='reviewer' if native_background else None,
                              diagnostic=log_dir / (label + '.requests.json'),
                              parent_denial=native_background) as fixture:
            keep = ('HOME', 'USER', 'LOGNAME', 'PATH', 'LANG', 'LC_ALL', 'TMPDIR',
                    'ISSUE', 'COMMENTS', 'PR', 'GIT_CONFIG_GLOBAL', 'GIT_CONFIG_NOSYSTEM')
            case.env = {key: value for key, value in case.env.items() if key in keep}
            case.env.update(ANTHROPIC_API_KEY=DUMMY_KEY,
                            ANTHROPIC_BASE_URL='http://127.0.0.1:' + str(fixture.server.server_port),
                            CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1',
                            CLAUDE_CODE_DISABLE_OFFICIAL_MARKETPLACE_AUTOINSTALL='1',
                            CLAUDE_CODE_DISABLE_THINKING='1',
                            CLAUDE_CODE_DISABLE_NONSTREAMING_FALLBACK='1')
            metadata = case.root / 'claude-invocation.json'
            isolation = ['--restricted', '--setting-sources', '', '--strict-mcp-config',
                         '--mcp-config', '{"mcpServers":{}}', '--no-chrome',
                         '--disable-slash-commands', '--tools',
                         'Bash,Read,Write,Edit' + (',Agent' if native_background else ''),
                         '--allowedTools', 'Bash(printf *)']
            if native_background:
                isolation += ['--allowedTools', 'Agent']
            case.tool('claude', 'import json,os,sys\nfrom pathlib import Path\n'
                + 'Path(' + repr(str(metadata)) + ').write_text(json.dumps(dict('
                + 'cwd=os.getcwd(),sid=os.getsid(0),pid=os.getpid(),'
                + 'role=os.environ.get("DEVSTANDARD_ROLE"),argv=sys.argv[1:])))\n'
                + 'os.execv(' + repr(binary) + ',[' + repr(binary)
                + ',*sys.argv[1:],*' + repr(isolation) + '])\n')
            record = case.start('--implementation', 'claude-cli')
            completion = Path(record['completion'])
            deadline = time.monotonic() + 45
            while not completion.exists() and time.monotonic() < deadline:
                time.sleep(.05)
            (log_dir / (label + '.record.json')).write_text(json.dumps(record, indent=2))
            for key in ('output', 'log', 'completion', 'brief'):
                path = Path(record[key])
                if path.exists():
                    shutil.copy2(path, log_dir / (label + '.' + path.name))
            require(completion.exists(), 'real Claude dispatcher did not finish within 45s')
            require(completion.read_text().strip() == '0', 'real Claude executor failed')
            (log_dir / (label + '.requests.json')).write_text(json.dumps(fixture.requests, indent=2))
            events = [json.loads(line) for line in Path(record['output']).read_text().splitlines()]
            results = [event for event in events if event.get('type') == 'result']
            require(results and all(not result.get('is_error') for result in results)
                    and results[-1].get('result') == 'Fixture complete.',
                    'invalid captured Claude JSONL result events')
            require(not fixture.errors and len(fixture.requests) == (7 if native_background else 3),
                    'dispatcher fixture did not complete its local request sequence')
            invocation = json.loads(metadata.read_text())
            shutil.copy2(metadata, log_dir / (label + '.invocation.json'))
            require(invocation['cwd'] == record['worktree'], 'Claude did not use assigned worktree')
            require(invocation['sid'] == record['pid'], 'Claude did not retain detached supervisor session')
            require(invocation['role'] == 'worker', 'dispatcher omitted process role marker')
            content = json.dumps(fixture.requests[0], ensure_ascii=False)
            # Compare the unescaped source in serialized request text by first
            # finding the raw input content blocks; JSON escaping is not delivery.
            message_text = '\n'.join(block.get('text', '')
                for message in fixture.requests[0]['messages']
                if isinstance(message.get('content'), list) for block in message['content'])
            brief = Path(record['brief']).read_text().strip()
            require(brief in message_text, 'complete dispatch brief did not reach Claude through stdin')
            expected_role = (ROOT / 'reference/worker.md').read_text().strip()
            bindings = {'ISSUE_LINK_OR_SPEC': 'https://github.com/o/r/issues/12',
                        'DONE_CHECK': 'Output is captured.', 'BRANCH': record['branch'],
                        'WORKTREE_PATH': record['worktree']}
            for key, value in bindings.items():
                expected_role = expected_role.replace('{' + key + '}', value)
            require(expected_role in brief, 'dispatch brief omitted or altered the complete resolved worker role')
            require('Issue: https://github.com/o/r/issues/12' in message_text,
                    'dynamic issue packet did not reach Claude through brief stdin')
            require('DevStandard operating context: reference/orchestrator.md' not in content,
                    'dispatcher worker inherited orchestrator context')
            final_request = fixture.child_requests[-1] if native_background else fixture.requests[-1]
            tool_results = [block for message in final_request['messages']
                       if isinstance(message.get('content'), list) for block in message['content']
                       if block.get('type') == 'tool_result']
            allowed = next(block for block in tool_results if block['tool_use_id'] == 'toolu_devstandard_1')
            denied = next(block for block in tool_results if block['tool_use_id'] == 'toolu_devstandard_2')
            require(not allowed.get('is_error') and ALLOW in json.dumps(allowed),
                    'dispatched Claude did not execute the harmless allowed command')
            expected_role = 'reviewer' if native_background else 'worker'
            require(denied.get('is_error') and expected_role + ' role refuses' in json.dumps(denied),
                    'dispatched Claude did not apply worker hook denial')
            required_id = 'toolu_devstandard_parent_denied' if native_background else 'toolu_devstandard_2'
            require(any(row.get('tool_use_id') == required_id for result in results
                        for row in result.get('permission_denials', [])),
                    'dispatcher discarded Claude permission-denial metadata')
            if native_background:
                require(len(results) >= 2, 'native background completion did not emit multiple result events')
                require(any(row.get('tool_use_id') == required_id for result in results[:-1]
                            for row in result.get('permission_denials', [])),
                        'fixture did not preserve an earlier result permission denial')
                require(not any(row.get('tool_use_id') == required_id
                                for row in results[-1].get('permission_denials', [])),
                        'fixture did not exercise a later result without the earlier denial')
            require(all(row.get('output_config', {}).get('effort') == 'high'
                        for row in fixture.requests), 'dispatched effort did not reach model API')
            return {'role': label, 'requests': len(fixture.requests),
                    'execution': 'real detached Claude CLI', 'result_events': len(results),
                    'github': 'fixture', 'full_brief': 'delivered through stdin',
                    'worktree': 'verified', 'jsonl_permission_denials': 'preserved across all result events'}
    finally:
        if record and not Path(record['completion']).exists():
            try:
                if os.getsid(record['pid']) == record['pid']:
                    os.killpg(record['pid'], signal.SIGTERM)
            except ProcessLookupError:
                pass
        case.doCleanups()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--claude', default=shutil.which('claude'))
    parser.add_argument('--log-dir', type=Path, required=True)
    parser.add_argument('--roles', default='orchestrator,worker,reviewer,native-worker,native-reviewer,cli-worker,cli-reviewer,native-reviewer-from-cli-worker')
    parser.add_argument('--dispatch-cli', action='store_true',
                        help='also exercise the real dispatcher with a controlled GitHub boundary')
    args = parser.parse_args()
    require(args.claude, 'Claude CLI not found; provide --claude')
    for path in (Path('/etc/claude-code/managed-settings.json'),
                 Path('/Library/Application Support/ClaudeCode/managed-settings.json')):
        require(not path.exists(), 'runtime isolation unavailable: managed settings ' + str(path))
    args.log_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='devstandard-claude-runtime-') as temporary:
        results = [runtime(args.claude, Path(temporary), args.log_dir, role)
                   for role in args.roles.split(',')]
        if args.dispatch_cli:
            results.append(dispatch_cli(args.claude, args.log_dir))
            results.append(dispatch_cli(args.claude, args.log_dir, native_background=True))
    version = subprocess.check_output([args.claude, '--version'], text=True).strip()
    print(json.dumps({'status': 'pass', 'claude': version, 'cases': results}, indent=2))


if __name__ == '__main__':
    main()
