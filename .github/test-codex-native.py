#!/usr/bin/env python3
"""Run emitted worker briefs through real Codex native v1/v2 subagents.

Only GitHub I/O is simulated, using the dispatcher regression fixture. Codex,
git, native spawn/wait, and plugin hooks are real. A localhost Responses server
supplies a canonical-brief read and fixed harmless printf calls; no model service
or authentication is used.
Parent permissions/cwd are inherited. Each worker tool explicitly selects its
assigned worktree; this test makes no claim of a separate child sandbox.
"""
import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / '.github' / filename)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


runtime = module('codex_runtime_fixture', 'test-codex-runtime.py')
dispatch_tests = module('dispatch_fixture', 'test-dispatch.py')
require = runtime.require
PARENT = 'DEVSTANDARD_NATIVE_PARENT_551'
TASK = 'DEVSTANDARD_NATIVE_TASK_551'
DEVELOPER = 'DEVSTANDARD_NATIVE_PARENT_DEVELOPER_551'
ALLOW = 'DEVSTANDARD_NATIVE_CHILD_ALLOWED_551'
DENY = 'DEVSTANDARD_NATIVE_CHILD_EXECUTED_551'
DONE = 'DEVSTANDARD_NATIVE_CHILD_DONE_551'
PARENT_ALLOW = 'DEVSTANDARD_NATIVE_PARENT_ALLOWED_551'


def catalog(request):
    result = {}
    supplied = list(request.get('tools', []))
    for item in request.get('input', []):
        if item.get('type') == 'additional_tools':
            supplied.extend(item.get('tools', []))
    for tool in supplied:
        if tool.get('type') == 'namespace':
            for member in tool.get('tools', []):
                result[member['name']] = (member, tool['name'])
        elif tool.get('name'):
            result[tool['name']] = (tool, None)
    return result


def function(request, name, arguments, call_id):
    if name == 'exec_command' and name not in catalog(request) and 'exec' in catalog(request):
        # Some model metadata supplies code mode through additional_tools input
        # records. Exercise its actual nested exec hook, not an invented tool.
        _tool, namespace = catalog(request)['exec']
        return {'type': 'custom_tool_call', 'id': 'fc_' + call_id, 'call_id': call_id,
                'name': 'exec', 'namespace': namespace,
                'input': 'text(await tools.exec_command(' + json.dumps(arguments) + '));'}
    require(name in catalog(request), 'missing native tool: ' + name)
    _tool, namespace = catalog(request)[name]
    result = {'type': 'function_call', 'id': 'fc_' + call_id, 'call_id': call_id,
              'name': name, 'arguments': json.dumps(arguments)}
    if namespace:
        result['namespace'] = namespace
    return result


def tool_results(request):
    return {item['call_id']: item.get('output', '') for item in request.get('input', [])
            if item.get('type') in ('function_call_output', 'custom_tool_call_output')}


def tool_text(output):
    # Direct exec returns plain text; code-mode exec wraps the same result in JSON.
    fragments = []
    for text in runtime.text_fragments(output):
        try:
            decoded = json.loads(text)
        except ValueError:
            fragments.append(text)
        else:
            fragments.extend(runtime.text_fragments(decoded))
    return '\n'.join(fragments)


def final(text, suffix):
    return {'type': 'message', 'id': 'msg_' + suffix, 'role': 'assistant',
            'status': 'completed', 'content': [{'type': 'output_text', 'text': text,
                                              'annotations': []}]}


class NativeFixture:
    def __init__(self, protocol, instruction, canonical):
        self.protocol, self.instruction = protocol, instruction
        self.canonical = canonical
        self.requests, self.errors = [], []
        self.root_stage = self.child_stage = 0
        self.child_done = threading.Event()
        self.lock = threading.Lock()
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_GET(self):
                if self.path.split('?', 1)[0] != '/v1/models':
                    outer.errors.append('unexpected local endpoint: ' + self.path)
                    self.send_error(404)
                    return
                body = b'{"models":[]}'
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                try:
                    require(self.path.rstrip('/') == '/v1/responses', 'unexpected endpoint')
                    require(not self.headers.get('Authorization'), 'unexpected authentication')
                    require(self.headers.get('Content-Encoding', 'identity') == 'identity',
                            'unexpected request compression')
                    request = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                    with outer.lock:
                        index = len(outer.requests)
                        outer.requests.append(request)
                    require(index < 15, 'unexpected extra native continuation')
                    item = outer.response(request)
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/event-stream')
                    self.send_header('Connection', 'close')
                    self.end_headers()
                    response = {'id': 'resp_native_' + str(index), 'object': 'response',
                                'status': 'completed', 'output': [item],
                                'usage': {'input_tokens': 1, 'output_tokens': 1, 'total_tokens': 2}}
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
                    self.send_error(500, 'native fixture refused request')

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @staticmethod
    def child(request):
        # Spawn arguments also contain TASK in parent history; inspect message
        # content only. V2 delivers the child's initial task as agent_message.
        content = '\n'.join(runtime.text_fragments([
            item for item in request.get('input', [])
            if item.get('type') in ('message', 'agent_message')]))
        return TASK in content and PARENT not in content

    def response(self, request):
        if self.child(request):
            self.child_stage += 1
            if self.child_stage == 1:
                # Exercise the real child's file access and complete tool output.
                # A digest-only host-side check would miss unreadable/truncated delivery.
                reader = ('import hashlib, sys; from pathlib import Path; '
                          'data = Path(sys.argv[1]).read_bytes(); '
                          'assert hashlib.sha256(data).hexdigest() == sys.argv[2], "brief digest mismatch"; '
                          'sys.stdout.write(data.decode("utf-8"))')
                return function(request, 'exec_command', {
                    'cmd': shlex.join([sys.executable, '-c', reader, self.instruction['brief'],
                                       self.instruction['brief_sha256']]),
                    'workdir': self.instruction['worktree'], 'login': False,
                    'max_output_tokens': 20000}, 'child_brief')
            if self.child_stage == 2:
                observed = tool_results(request).get('child_brief', '')
                require(self.canonical in tool_text(observed),
                        'native child did not read complete canonical role and packet: ' + str(observed)[:1000])
            if self.child_stage < 4:
                # The guarded word stands outside the quotes, as an ignored `printf` operand:
                # since #351 the hook does not read quoted text, so a word inside the format
                # string would exercise no refusal (`reference/hard-edges.md`, The role hook).
                command = ("printf '" + ALLOW + " %s\\n' \"$PWD\""
                           if self.child_stage == 2 else
                           "printf '" + DENY + "\\n' tag")
                return function(request, 'exec_command', {
                    'cmd': command, 'workdir': self.instruction['worktree'],
                    'login': False, 'max_output_tokens': 200},
                    'child_allow' if self.child_stage == 2 else 'child_deny')
            self.child_done.set()
            return final(DONE, 'child')
        self.root_stage += 1
        if self.root_stage == 1:
            return function(request, 'exec_command', {
                # Also unquoted: this probe's point is that the root is not a worker, which
                # only shows where a worker would have been refused (#351).
                'cmd': "printf '" + PARENT_ALLOW + "\\n' tag", 'login': False,
                'max_output_tokens': 100}, 'parent_allow')
        if self.root_stage == 2:
            args = {'message': self.instruction['message'], 'model': self.instruction['model'],
                    'reasoning_effort': self.instruction['reasoning_effort']}
            if self.protocol == 'v2':
                args.update(task_name='devstandard_worker', fork_turns='none')
            else:
                args['fork_context'] = False
            properties = catalog(request)['spawn_agent'][0]['parameters']['properties']
            require(set(args) <= set(properties), 'native protocol schema differs')
            return function(request, 'spawn_agent', args, 'spawn_worker')
        if self.root_stage == 3:
            raw = tool_results(request).get('spawn_worker', '')
            try:
                handle = json.loads(raw) if isinstance(raw, str) else raw
            except ValueError:
                raise AssertionError('native spawn failed: ' + str(raw)[:1500])
            require(self.child_done.wait(12), 'native child did not finish fixed probes')
            args = {'timeout_ms': 10000}
            if self.protocol == 'v1':
                args['targets'] = [handle['agent_id']]
            else:
                require(handle.get('task_name') == '/root/devstandard_worker',
                        'native v2 returned unexpected handle')
            return function(request, 'wait_agent', args, 'wait_worker')
        return final('DevStandard native fixture complete.', 'root')

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)


OBSERVER = '''import hashlib, json, os, sys
from pathlib import Path
event = json.load(sys.stdin)
row = {key: event.get(key) for key in ('hook_event_name','session_id','agent_id','agent_type','cwd','tool_name','tool_use_id','source')}
row['role_environment'] = os.environ.get('DEVSTANDARD_ROLE')
if event.get('tool_name') == 'Bash': row['command'] = event['tool_input']['command']
with Path(sys.argv[1]).open('a') as target: target.write(json.dumps(row) + '\\n')
print('{}')
'''


def run_case(binary, protocol, logs, native):
    fixture = dispatch_tests.DispatchTest()
    fixture.setUp()
    try:
        runtime.inventory(fixture.project)
        issue = json.loads(fixture.issue.read_text())
        issue['body'] = '## Goal\n' + TASK + '\n## Bounds\nOne harmless fixture.\n## Done-check\nNative probes finish.'
        fixture.issue.write_text(json.dumps(issue))
        source = native['root'] if native else ROOT
        fixture.script = source / 'scripts/dispatch'
        receipt = fixture.start('--implementation', 'codex-native')
        require(receipt['status'] == 'awaiting-agent-tool', 'dispatcher started a process')
        require(not any(key in receipt for key in ('pid', 'completion', 'output')), 'native receipt has process state')
        instruction = json.loads(Path(receipt['instruction']).read_text())
        require(instruction['format'] == 'devstandard-codex-native-v1', 'unexpected native instruction format')
        require(instruction['fresh_conversation'] is True, 'native worker must start clean')
        require(instruction['model'] == receipt['model'] and
                instruction['reasoning_effort'] == receipt['effort'], 'native model routing differs from receipt')
        canonical = Path(receipt['brief']).read_bytes()
        digest = hashlib.sha256(canonical).hexdigest()
        require(instruction.get('brief') == receipt['brief'] and Path(receipt['brief']).is_absolute(),
                'native instruction omits absolute canonical brief source')
        require(instruction.get('brief_sha256') == digest and receipt.get('brief_sha256') == digest,
                'canonical brief digest differs from saved bytes or run receipt')
        canonical = canonical.decode('utf-8')
        require(instruction['message'].endswith(canonical), 'native message omits exact inline brief')
        preamble = instruction['message'][:-len(canonical)]
        require(receipt['brief'] in preamble and digest in preamble,
                'canonical source and digest must precede inline brief')
        worker = (source / 'reference/worker.md').read_text().rstrip('\n')
        for slot, value in {'ISSUE_LINK_OR_SPEC': issue['url'], 'DONE_CHECK': 'Native probes finish.',
                            'BRANCH': receipt['branch'], 'WORKTREE_PATH': receipt['worktree']}.items():
            worker = worker.replace('{' + slot + '}', value)
        require(worker in instruction['message'], 'complete worker role missing from emitted instruction')
        require(instruction['worktree'] == receipt['worktree'], 'assigned lane differs')
        hook_log = fixture.root / 'native-hooks.jsonl'
        observer = fixture.root / 'native-observer.py'
        observer.write_text(OBSERVER)
        with NativeFixture(protocol, instruction, canonical) as server:
            settings = {
                'model_provider': 'devstandard-native-fixture',
                'model_providers.devstandard-native-fixture': {
                    'name': 'Local deterministic native fixture',
                    'base_url': 'http://127.0.0.1:' + str(server.server.server_port) + '/v1',
                    'wire_api': 'responses', 'requires_openai_auth': False,
                    'supports_websockets': False, 'request_max_retries': 0,
                    'stream_max_retries': 0, 'stream_idle_timeout_ms': 20000},
                'features.hooks': True, 'features.plugins': False, 'features.apps': False,
                'features.remote_plugin': False, 'features.enable_request_compression': False,
                'features.shell_snapshot': False, 'features.code_mode': False,
                'features.multi_agent': True, 'features.multi_agent_v2': protocol == 'v2',
                'features.skip_host_skill_discovery': True, 'web_search': 'disabled',
                'check_for_update_on_startup': False, 'approval_policy': 'never',
                'analytics.enabled': False, 'developer_instructions': DEVELOPER,
            }
            hooks = {} if native else runtime.hook_config(None)
            if native:
                settings.update(native['settings'])
            # Observe identity without replacing or modifying any installed hook.
            for event in ('SessionStart', 'SubagentStart', 'UserPromptSubmit', 'PreToolUse', 'SubagentStop'):
                hooks.setdefault(event, []).append({'matcher': '.*', 'hooks': [{
                    'type': 'command', 'command': shlex.join([sys.executable, str(observer), str(hook_log)]),
                    'timeout': 5}]})
            for event, groups in hooks.items():
                settings['hooks.' + event] = groups
            command = [binary, 'exec', '--ignore-user-config', '--ephemeral', '--json',
                       '-s', 'read-only', '-C', str(fixture.project), '-m', 'devstandard-native-fixture']
            for key, value in settings.items():
                command += ['-c', key + '=' + runtime.toml(value)]
            command += ['--dangerously-bypass-hook-trust', PARENT + ': Run the deterministic fixture; use its one native worker and wait for the result.']
            env = dict(fixture.env)
            for key in ('DEVSTANDARD_ROLE', 'PLUGIN_DATA', 'CLAUDE_PLUGIN_DATA', 'PLUGIN_ROOT', 'CLAUDE_PLUGIN_ROOT', 'OPENAI_API_KEY'):
                env.pop(key, None)
            result = subprocess.run(command, env=env, stdin=subprocess.DEVNULL,
                                    capture_output=True, text=True, timeout=60)
        hook_events = [json.loads(line) for line in hook_log.read_text().splitlines()] if hook_log.exists() else []
        children = [request for request in server.requests if server.child(request)]
        parents = [request for request in server.requests if not server.child(request)]
        report = {'protocol': protocol, 'fixture_errors': server.errors,
                  'hook_source': 'installed-plugin' if native else 'inline',
                  'plugin_selector': native['selector'] if native else None,
                  'plugin_root': str(source),
                  'hook_events': hook_events, 'child_requests': len(children),
                  'child_tool_outputs': [tool_results(request) for request in children],
                  'parent_tool_outputs': [tool_results(request) for request in parents],
                  'child_models': [request.get('model') for request in children],
                  'child_efforts': [request.get('reasoning', {}).get('effort') for request in children],
                  'brief_sha256': digest,
                  'instruction_sha256': hashlib.sha256(instruction['message'].encode()).hexdigest()}
        if logs:
            (logs / (protocol + '.events.jsonl')).write_text(result.stdout)
            (logs / (protocol + '.stderr.log')).write_text(result.stderr)
            (logs / (protocol + '.catalog.json')).write_text(json.dumps(report, indent=2) + '\n')
        diagnostic = json.dumps({'fixture_errors': server.errors, 'child_requests': len(children),
                                 'child_tool_outputs': report['child_tool_outputs'],
                                 'stderr_tail': result.stderr[-2500:]})
        require(result.returncode == 0 and not server.errors, 'native run failed: ' + diagnostic)
        require(len(children) == 4, 'expected canonical read, two native child tools and completion: ' + diagnostic)
        require(all(request.get('model') == instruction['model'] for request in children),
                'native child did not use requested model')
        require(all(request.get('reasoning', {}).get('effort') == instruction['reasoning_effort']
                    for request in children), 'native child did not use requested reasoning effort')
        child_context = '\n'.join(runtime.text_fragments(children[0].get('input', [])))
        require(instruction['message'] in child_context, 'full emitted worker message did not reach child')
        require(worker in child_context, 'worker role tail did not reach child')
        require(PARENT not in child_context, 'parent conversation leaked into clean worker')
        require(DEVELOPER in child_context, 'parent developer inheritance changed; requalify native contract')
        for artifact in ('reference/orchestrator.md', 'reference/harness-codex.md'):
            page = (source / artifact).read_text().rstrip('\n')
            require(page not in child_context, 'root SessionStart artifact leaked into worker: ' + artifact)
        child_outputs = tool_results(children[-1])
        require(canonical in tool_text(child_outputs.get('child_brief', '')),
                'complete canonical role/packet missing from native read output: ' + diagnostic)
        require(ALLOW + ' ' + instruction['worktree'] in str(child_outputs.get('child_allow', '')),
                'native allowed command/lane failed: ' + diagnostic)
        require('worker role refuses' in str(child_outputs.get('child_deny', '')),
                'native worker hook did not refuse tag: ' + diagnostic)
        require('Process exited with code' not in str(child_outputs.get('child_deny', '')),
                'refused native command was executed: ' + diagnostic)
        parent_outputs = tool_results(parents[-1])
        require(PARENT_ALLOW in str(parent_outputs.get('parent_allow', '')), 'root was treated as a worker')
        require('wait_worker' in parent_outputs, 'native wait was not completed')
        require(DONE in '\n'.join(runtime.text_fragments(parents[-1])), 'native completion did not reach parent')
        starts = [event for event in hook_events if event['hook_event_name'] == 'SubagentStart']
        require(len(starts) == 1 and starts[0]['agent_id'], 'missing real native child identity')
        require(starts[0]['agent_type'] == 'default', 'unexpected default native role')
        child_events = [event for event in hook_events if event.get('agent_id') == starts[0]['agent_id']]
        require(all(event['role_environment'] is None for event in child_events), 'native role came from process env')
        require(not any(event['hook_event_name'] == 'SessionStart' for event in child_events), 'root startup ran in child')
        require(any(DENY in event.get('command', '') for event in child_events),
                'denial has no child hook witness')
        return {'protocol': protocol, 'status': 'pass', 'full_worker_brief': True, 'canonical_brief_read': True,
                'brief_sha256': digest,
                'native_spawn_wait': True, 'guard': 'worker', 'lane_workdir': 'explicit',
                'model': instruction['model'], 'reasoning_effort': instruction['reasoning_effort'],
                'parent_developer_instructions': 'inherited',
                'hook_source': 'installed-plugin' if native else 'inline'}
    finally:
        fixture.doCleanups()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log-dir', type=Path)
    parser.add_argument('--protocol', choices=('v1', 'v2'))
    parser.add_argument('--native-plugin')
    parser.add_argument('--plugin-root', type=Path)
    args = parser.parse_args()
    require(bool(args.native_plugin) == bool(args.plugin_root), 'native plugin and root must be paired')
    binary = shutil.which('codex')
    require(binary, 'Codex CLI 0.153.4+ is required')
    if args.log_dir:
        args.log_dir.mkdir(parents=True, exist_ok=True)
    native = runtime.native_plugin(binary, args.native_plugin, args.plugin_root) if args.native_plugin else None
    if native:
        for relative in ('scripts/dispatch', 'scripts/hard_edges.py', 'scripts/review_packet.py',
                         'reference/worker.md', 'reference/external-agent.md'):
            cached = native['root'] / relative
            require(cached.is_file() and not cached.is_symlink() and cached.read_bytes() == (ROOT / relative).read_bytes(),
                    'native dispatcher source differs: ' + relative)
    results = [run_case(binary, protocol, args.log_dir, native)
               for protocol in ([args.protocol] if args.protocol else ['v1', 'v2'])]
    print(json.dumps({'status': 'pass', 'results': results,
                      'not_exercised': ['independent native reviewer sandbox', 'persisted resume',
                                        'full-history fork', 'subagent compaction']}))


if __name__ == '__main__':
    try:
        main()
    except (AssertionError, OSError, subprocess.SubprocessError, KeyError, ValueError) as error:
        print(json.dumps({'status': 'fail', 'error': str(error)}))
        raise SystemExit(1)
