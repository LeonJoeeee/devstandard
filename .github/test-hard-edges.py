#!/usr/bin/env python3
"""Hard-edge probes: real git replay, with doubled external GitHub responses."""
import importlib.util
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]


def module():
    path = ROOT / 'scripts/hard_edges.py'
    assert path.exists(), 'hard-edge implementation is missing'
    spec = importlib.util.spec_from_file_location('hard_edges', path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class ProtectionTest(unittest.TestCase):
    def test_protected_and_unprotected_api_shapes(self):
        h = module()
        protected = {'required_status_checks': {'strict': True, 'contexts': ['test']},
                     'enforce_admins': {'enabled': True},
                     'allow_force_pushes': {'enabled': False}, 'allow_deletions': {'enabled': False}}
        with patch.object(h, 'api', return_value=protected):
            h.protection_check('o/r', 'main', ['test'])
        with patch.object(h, 'api', side_effect=h.Refusal('gh: Branch not protected (HTTP 404)')):
            with self.assertRaisesRegex(h.Refusal, 'not protected'):
                h.protection_check('o/r', 'probe/unprotected', ['test'])
        for field in ['strict', 'contexts']:
            broken = json.loads(json.dumps(protected))
            broken['required_status_checks'][field] = False if field == 'strict' else []
            with patch.object(h, 'api', return_value=broken):
                with self.assertRaises(h.Refusal):
                    h.protection_check('o/r', 'main', ['test'])


class RebaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='hard-edge-test-')
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / 'repo'
        self.repo.mkdir()
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1')
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Probe')
        self.git('config', 'user.email', 'probe@example.invalid')
        (self.repo / 'changed').write_text('base\n')
        self.commit('base')
        self.base = self.git('rev-parse', 'HEAD')
        self.git('checkout', '-b', 'topic')
        (self.repo / 'changed').write_text('reviewed\n')
        self.commit('reviewed')
        self.old = self.git('rev-parse', 'HEAD')
        self.git('checkout', 'main')
        (self.repo / 'unrelated').write_text('new base\n')
        self.commit('main advances')
        self.newbase = self.git('rev-parse', 'HEAD')
        self.git('checkout', 'topic')
        self.git('rebase', 'main')
        self.new = self.git('rev-parse', 'HEAD')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], env=self.env,
                                       stderr=subprocess.DEVNULL, text=True).strip()

    def commit(self, message):
        self.git('add', '.')
        self.git('commit', '-m', message)

    def test_constructed_content_unchanged_rebase_proves(self):
        h = module()
        proof = h.compare_rebase(self.repo, self.base, self.old, self.newbase, self.new)
        self.assertEqual(proof['head'], self.new)
        self.assertEqual(proof['paths'], ['changed'])
        self.assertEqual(self.git('status', '--porcelain', '-uall'), '')

    def test_constructed_changed_rebase_refuses(self):
        h = module()
        (self.repo / 'changed').write_text('unreviewed\n')
        self.commit('sneak edit')
        with self.assertRaisesRegex(h.Refusal, 'identical|replay'):
            h.compare_rebase(self.repo, self.base, self.old, self.newbase, self.git('rev-parse', 'HEAD'))

    def test_conflicting_rebase_refuses_even_if_manually_resolved_to_old_bytes(self):
        h = module()
        self.git('checkout', 'main')
        (self.repo / 'changed').write_text('upstream conflict\n')
        self.commit('conflict')
        conflictbase = self.git('rev-parse', 'HEAD')
        (self.repo / 'changed').write_text('reviewed\n')
        self.commit('manual resolution')
        with self.assertRaisesRegex(h.Refusal, 'conflict'):
            h.compare_rebase(self.repo, self.base, self.old, conflictbase, self.git('rev-parse', 'HEAD'))

    def test_changed_mode_or_extra_path_refuses(self):
        h = module()
        (self.repo / 'changed').chmod(0o755)
        self.commit('mode change')
        with self.assertRaises(h.Refusal):
            h.compare_rebase(self.repo, self.base, self.old, self.newbase, self.git('rev-parse', 'HEAD'))

    def test_prior_acceptance_needs_replay_and_exact_integration_identity(self):
        h = module()
        record = {'kind':'attempt', 'status':'returned', 'round':1, 'head':self.old,
                  'base':self.base, 'architecture':'NO'}
        verdict = AcceptanceTest().verdict(head=self.old).split('\n',1)[1]
        comment = {'id':1, 'user':{'login':'o'}, 'body':'## Merge check 1 — round 1\n\n'
                   '<!-- devstandard-review-v1 -->\n```json\n'+json.dumps(record)+'\n```\n\n'+verdict}
        pr = {'state':'open','head':{'sha':self.new}, 'base':{'sha':self.newbase,'ref':'main',
              'repo':{'full_name':'o/r'}}, 'body':'architecture-level: false'}
        integration = f'merged-result / {self.newbase} / {self.new}'
        def api(endpoint, *args):
            if endpoint == 'repos/o/r': return {'default_branch':'main'}
            if endpoint.endswith('/pulls/12'): return pr
            if endpoint.endswith('/branches/main'): return {'commit':{'sha':self.newbase}}
            if '/comments' in endpoint: return [comment]
            if 'check-runs' in endpoint:
                return {'check_runs':[{'id':i,'name':name,'status':'completed','conclusion':'success'}
                                     for i,name in enumerate(['test', integration])]}
            if '/status?' in endpoint: return {'statuses':[]}
            self.fail(endpoint)
        with patch.object(h,'api',side_effect=api), patch.object(h,'settings_for',return_value=('o/r',{})), patch.object(h,'protection_check'):
            result = h.merge_check(self.repo,'o/r',12,self.base,self.old)
            self.assertEqual(result['comparison']['comparison'],'pass')
            integration = 'merged-result / stale base / '+self.new
            with self.assertRaisesRegex(h.Refusal,'CI not green'):
                h.merge_check(self.repo,'o/r',12,self.base,self.old)
            with self.assertRaisesRegex(h.Refusal,'exact accepted head'):
                h.merge_check(self.repo,'o/r',12)


# Each row is a shell family decision, shared by focused probes and the operation sweep.
# Commands are classification input only; none of these operations are executed.
SHELL_FAMILIES = [
    ('semicolon', 'modelled', lambda c: 'true; ' + c),
    ('and', 'modelled', lambda c: 'true && ' + c),
    ('or', 'modelled', lambda c: 'false || ' + c),
    ('pipe', 'modelled', lambda c: 'true | ' + c),
    ('background', 'modelled', lambda c: 'true & ' + c),
    ('newline', 'refused', lambda c: 'true\n' + c),
    ('CR', 'refused', lambda c: 'true\r' + c),
    ('parentheses', 'refused', lambda c: '(' + c + ')'),
    ('braces', 'refused', lambda c: '{ ' + c + '; }'),
    ('command substitution', 'refused', lambda c: 'echo $(' + c + ')'),
    ('backticks', 'refused', lambda c: 'echo `' + c + '`'),
    ('parameter expansion', 'refused', lambda c: '${prefix}' + c),
    ('variable expansion', 'refused', lambda c: '$prefix ' + c),
    ('brace expansion', 'refused', lambda c: '{' + c.split(' ', 1)[0] + ',x} ' + c.split(' ', 1)[1]),
    ('glob question', 'refused', lambda c: c.split(' ', 1)[0][:-1] + '? ' + c.split(' ', 1)[1]),
    ('glob star', 'refused', lambda c: c.split(' ', 1)[0] + '* ' + c.split(' ', 1)[1]),
    ('glob bracket', 'refused', lambda c: '[' + c[0] + ']' + c[1:]),
    ('tilde expansion', 'refused', lambda c: '~/bin/' + c),
    ('quote concatenation', 'modelled', lambda c: c[0] + '"' + c[1] + '"' + c[2:]),
    ('escape', 'modelled', lambda c: '\\' + c),
    ('single quote', 'modelled', lambda c: "'" + c.split(' ', 1)[0] + "' " + c.split(' ', 1)[1]),
    ('hash in word', 'modelled', lambda c: 'git status -- probe#file; ' + c),
    ('comment', 'modelled', lambda c: c + ' # comment'),
    ('comment scanned conservatively', 'modelled', lambda c: 'true # comment; ' + c),
    ('here-doc', 'refused', lambda c: c.split(' ', 1)[0] + ' <<EOF ' + c.split(' ', 1)[1] + '\n\nEOF'),
    ('tab-stripped here-doc', 'refused', lambda c: c + " <<-'EOF'\n\ttext\n\tEOF"),
    ('process substitution', 'refused', lambda c: 'cat <(' + c + ')'),
    ('assignment', 'refused', lambda c: 'PREFIX=value ' + c),
    ('conditional', 'refused', lambda c: 'if true; then ' + c + '; fi'),
    ('negation', 'refused', lambda c: '! ' + c),
]
REDIRECTIONS = ('< /dev/null', '> /dev/null', '>> /dev/null', '2> /dev/null',
                '&> /dev/null', '&>> /dev/null', '>| /dev/null', '2>&1', '0<&3',
                '3>&-', '3>&1-', '<<< input', '<> /dev/null', '2>/dev/null')
for redirection in REDIRECTIONS:
    SHELL_FAMILIES.append(('redirection ' + redirection, 'modelled',
        lambda c, r=redirection: c.split(' ', 1)[0] + ' ' + r + ' ' + c.split(' ', 1)[1]))
for wrapper in ('eval', 'sh -c', 'bash -c', 'env', 'xargs', 'command', 'exec',
                'nohup', 'setsid', 'time', 'nice', 'sudo', 'timeout 1', 'builtin'):
    SHELL_FAMILIES.append(('wrapper ' + wrapper, 'refused',
        lambda c, w=wrapper: w + ' ' + ("'" + c + "'" if w in ('eval', 'sh -c', 'bash -c') else c)))

DANGEROUS_OPERATIONS = {
    'merge': ['gh pr merge 0 --squash', 'scripts/guard merge --pr 0'],
    'release': ['git tag v0.1.2', 'git push origin --tags', 'git push origin --follow-tags',
                'git push origin refs/tags/probe', 'git push origin v0.1.2',
                'gh release create v0.1.2', 'gh release upload v0.1.2 artifact',
                'gh release edit v0.1.2', 'gh release delete v0.1.2',
                'npm publish', 'pnpm publish', 'yarn publish', 'twine upload artifact'],
    'irreversible': ['rm -rf /probe', 'git push --force origin main',
                     'git push -f origin main', 'git push origin --delete main',
                     'git push origin :refs/heads/main', 'git push origin main',
                     'gh repo delete o/r', 'gh api -X DELETE repos/o/r',
                     'gh api -X PUT repos/o/r', 'gh api -X PATCH repos/o/r',
                     'gh api -X POST repos/o/r', 'gh api repos/o/r -f name=value',
                     'scripts/guard protection --apply', 'terraform destroy',
                     'kubectl delete pod probe', 'aws s3api delete-bucket --bucket probe'],
}


GLOBAL_OPTIONS = {
    'git': ('--no-pager', '-c user.name=Probe', '-cuser.name=Probe', '-C /probe',
            '-C/probe', '--git-dir /probe', '--git-dir=/probe', '--work-tree /probe',
            '--work-tree=/probe', '-p', '--paginate', '-P', '--no-optional-locks',
            '--no-pager -cuser.name=Probe -C /probe', '-pP'),
    'gh': ('-R owner/repo', '-Rowner/repo', '--repo owner/repo', '--repo=owner/repo',
           '--hostname github.com', '--hostname=github.com', '--help', '--version',
           '-Rowner/repo --help', '-hv', '-Rowner/repo -hv'),
}


def orchestrator_hook(command, tool='Bash', field='command', *, settings=None, rows=None):
    """Exercise the real handler/authorization; double only remote policy and head reads."""
    h = module()
    if settings is None:
        settings = json.loads((ROOT / '.github/devstandard-guards.json').read_text())
    event = {'tool_name': tool, 'tool_input': {field: command}, 'cwd': str(ROOT)}
    out = io.StringIO()
    with patch.dict(sys.modules, {'hard_edges': h}), \
         patch.object(h, 'settings_for', return_value=('LeonJoeeee/devstandard', settings)), \
         patch.object(h, 'run', return_value='a'*40), \
         patch.object(h, 'api', return_value=rows or []) as api, \
         patch.object(sys, 'argv', ['pre-tool-use', '--role', 'orchestrator']), \
         patch.object(sys, 'stdin', io.StringIO(json.dumps(event))), patch.object(sys, 'stdout', out):
        runpy.run_path(str(ROOT / 'hooks/pre-tool-use'), run_name='__main__')
    return json.loads(out.getvalue()), api.call_count


class RoleTokenTest(unittest.TestCase):
    def test_round_five_orchestrator_negative_hook_probes(self):
        for command, reason, queries in (
                ('git --no-pager tag v0.1.2', 'authorization', 1),
                ('gh -RLeonJoeeee/devstandard pr merge 0 --squash', 'scripts/guard merge', 0)):
            for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
                with self.subTest(command=command, tool=tool):
                    result, actual_queries = orchestrator_hook(command, tool, field)
                    output = result.get('hookSpecificOutput', {})
                    self.assertEqual(output.get('permissionDecision'), 'deny')
                    self.assertIn(reason, output['permissionDecisionReason'])
                    self.assertEqual(actual_queries, queries)

    def test_round_four_negative_hook_probes(self):
        for command in ('git --no-pager tag v0.1.2', 'git -cuser.name=Probe tag v0.1.2',
                        'gh -RLeonJoeeee/devstandard pr merge 0 --squash'):
            for role in ('worker', 'reviewer'):
                for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
                    with self.subTest(command=command, role=role, tool=tool):
                        result = subprocess.run([str(ROOT / 'hooks/pre-tool-use'), '--role', role],
                            input=json.dumps({'tool_name': tool, 'tool_input': {field: command}}),
                            text=True, capture_output=True)
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertEqual(json.loads(result.stdout).get('hookSpecificOutput', {}).get(
                            'permissionDecision'), 'deny')

    def test_all_operation_tokens_refuse_regardless_of_position(self):
        h = module()
        settings = json.loads((ROOT / '.github/devstandard-guards.json').read_text())
        probes = 0
        for commands in DANGEROUS_OPERATIONS.values():
            for command in commands:
                words = command.split()
                # Includes read-looking prefixes so reviewer denial cannot rely on its read allowlist.
                variants = ['git diff -- ' + ' --probe value '.join(reversed(words)),
                            'cat ' + ' --probe value '.join(words),
                            '/usr/bin/' + command]
                for option in GLOBAL_OPTIONS.get(words[0], ('--probe value',)):
                    for at in range(1, len(words) + 1):
                        variants.append(' '.join(words[:at] + [option] + words[at:]))
                for candidate in variants:
                    for role in ('worker', 'reviewer', 'orchestrator'):
                        for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
                            with self.subTest(command=candidate, role=role, tool=tool):
                                self.assertIsNotNone(h.tool_decision(role, tool, {field: candidate}, settings))
                                if role == 'orchestrator':
                                    result, _ = orchestrator_hook(candidate, tool, field)
                                    self.assertEqual(result.get('hookSpecificOutput', {}).get('permissionDecision'), 'deny')
                                probes += 1
        print(f'Adversarial option/token sweep: {probes} role/tool refusals')

    def test_over_refusal_and_push_indicators(self):
        h = module()
        for command in ('git tag -l', 'gh pr merge --help', 'git diff -- gh pr merge',
                        'git -c alias.x=tag tag -l', 'git --no-pager push origin HEAD:main',
                        'git push origin HEAD:refs/heads/main', 'git push -vf origin task/12',
                        'gh api -XPOST repos/o/r', 'gh api repos/o/r -Fname=value',
                        'git push origin :v0.1.2'):
            for role in ('worker', 'reviewer'):
                with self.subTest(command=command, role=role):
                    self.assertIsNotNone(h.tool_decision(role, 'Bash', {'command': command}, {}))

    def test_literal_data_separate_segments_and_task_push_remain_available(self):
        h = module()
        for command in ('git push --force-with-lease origin task/12',
                        'git --no-pager push --force-with-lease origin task/12',
                        'gh issue comment 12 --body "gh pr merge 12"',
                        'git status; cat tag', 'cat git; cat tag',
                        'gh pr > merge view 0', 'git status -- tagged'):
            for role in ('worker', 'orchestrator'):
                with self.subTest(command=command, role=role):
                    self.assertIsNone(h.tool_decision(role, 'Bash', {'command': command}, {}))
        self.assertIn('scripts/guard merge', h.tool_decision('orchestrator', 'Bash',
                                                           {'command': 'git diff -- gh merge pr'}, {}))


class ShellCompositionTest(unittest.TestCase):
    def test_redirections_preserve_surrounding_argv_and_role_denial(self):
        h = module()
        for operation, kind in [('gh pr merge 0 --squash', 'merge'), ('npm publish', 'release')]:
            words = operation.split()
            for redirection in REDIRECTIONS:
                for at in range(len(words) + 1):
                    command = ' '.join(words[:at] + [redirection] + words[at:])
                    with self.subTest(command=command):
                        self.assertEqual(h.classify(command, {}), kind)
                        self.assertIsNotNone(h.tool_decision('worker', 'Bash', {'command': command}, {}))
                        self.assertIsNotNone(h.tool_decision('reviewer', 'Bash', {'command': command}, {}))

    def test_family_decisions_and_handler_refusals(self):
        h = module()
        for family, decision, variant in SHELL_FAMILIES:
            command = variant('gh pr merge 0 --squash')
            with self.subTest(family=family):
                self.assertEqual(h.classify(command, {}), 'merge' if decision == 'modelled' else 'unparsed')
                for role in ('worker', 'reviewer'):
                    for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
                        result = subprocess.run([str(ROOT / 'hooks/pre-tool-use'), '--role', role],
                            input=json.dumps({'tool_name': tool, 'tool_input': {field: command}}),
                            text=True, capture_output=True)
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertEqual(json.loads(result.stdout)['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_adversarial_sweep_every_configured_operation_across_every_family(self):
        import re
        h = module()
        settings = json.loads((ROOT / '.github/devstandard-guards.json').read_text())
        for kind, patterns in settings['command_patterns'].items():
            # An added policy pattern needs a witness; no configured matcher can silently miss the sweep.
            for pattern in patterns:
                self.assertTrue(any(re.search(pattern, c) for c in DANGEROUS_OPERATIONS[kind]), pattern)
        probes = 0
        for kind, commands in DANGEROUS_OPERATIONS.items():
            for command in commands:
                self.assertEqual(h.classify(command, settings), kind)
                for family, decision, variant in SHELL_FAMILIES:
                    candidate = variant(command)
                    for role in ('worker', 'reviewer', 'orchestrator'):
                        for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
                            with self.subTest(operation=command, family=family, role=role, tool=tool):
                                self.assertIsNotNone(h.tool_decision(role, tool, {field: candidate}, settings))
                                if role == 'orchestrator':
                                    result, _ = orchestrator_hook(candidate, tool, field)
                                    self.assertEqual(result.get('hookSpecificOutput', {}).get('permissionDecision'), 'deny')
                                probes += 1
        print(f'Adversarial shell sweep: {probes} role/tool refusals across {len(SHELL_FAMILIES)} families/variants')

    def test_literal_operator_arguments_are_not_shell_operators(self):
        h = module()
        for command, expected in [("gh '>' pr merge 0", 'merge'), ("gh ';' pr merge 0", 'merge'),
                                  ('gh "2" > /dev/null pr merge 0', 'merge'),
                                  ('gh 2 > /dev/null pr merge 0', 'merge'),
                                  ('gh 2> /dev/null pr merge 0', 'merge'),
                                  ('gh pr > "merge" view 0', None),
                                  ('gh pr > "a b" merge 0', 'merge'),
                                  ('gh 2 >2>file pr merge 0', 'merge'),
                                  ('gh pr</dev/null merge 0', 'merge'),
                                  ('gh pr 2>/dev/null merge 0', 'merge'),
                                  ('gh pr \\> merge 0', 'merge')]:
            with self.subTest(command=command):
                self.assertEqual(h.classify(command, {}), expected)

    def test_unsupported_syntax_does_not_become_an_ordinary_word(self):
        h = module()
        for command in ('gh pr >', 'gh pr > ; merge 0', 'gh pr >>> file merge 0',
                        'gh pr <<EOF merge 0', 'gh pr ;; merge 0', 'gh pr |& merge 0',
                        '/usr/bin/env gh pr merge 0', "e'val' 'gh pr merge 0'",
                        'exec -a harmless gh pr merge 0', 'time -p gh pr merge 0',
                        'function f { gh pr merge 0; }; f', '. script'):
            with self.subTest(command=command):
                self.assertEqual(h.classify(command, {}), 'unparsed')

    def test_safe_redirection_is_available_to_worker_and_orchestrator(self):
        h = module()
        for role in ('worker', 'orchestrator'):
            self.assertIsNone(h.tool_decision(role, 'Bash', {'command': 'git > /dev/null status'}, {}))
        self.assertIn('authorization', h.tool_decision('orchestrator', 'Bash',
                      {'command': 'npm < /dev/null publish'}, {}) or '')


class ToolGuardTest(unittest.TestCase):
    def test_hash_never_hides_worker_merge_or_release(self):
        h = module()
        for prefix in ('git status -- probe#file', 'git status -- "probe#file"',
                       "git status -- 'probe#file'", 'git status # comment'):
            for operation, kind in (('gh pr merge 0 --squash', 'merge'), ('npm publish', 'release')):
                command = prefix + '; ' + operation
                for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
                    with self.subTest(command=command, tool=tool):
                        self.assertEqual(h.classify(command, {}), kind)
                        reason = h.tool_decision('worker', tool, {field: command}, {})
                        self.assertEqual(reason, f'worker role refuses recognized {kind} operation')
                        result = subprocess.run([str(ROOT / 'hooks/pre-tool-use'), '--role', 'worker'],
                            input=json.dumps({'tool_name': tool, 'tool_input': {field: command}}),
                            text=True, capture_output=True)
                        self.assertEqual(result.returncode, 0, result.stderr)
                        out = json.loads(result.stdout)['hookSpecificOutput']
                        self.assertEqual(out['permissionDecision'], 'deny')
                        self.assertEqual(out['permissionDecisionReason'], reason)

    def test_plain_hash_arguments_and_benign_comments_remain_usable(self):
        h = module()
        for command in ('git status -- probe#file', 'git status -- "probe#file"',
                        "git status -- 'probe#file'", 'git status # harmless comment'):
            for role in ('worker', 'reviewer', 'orchestrator'):
                for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
                    with self.subTest(command=command, role=role, tool=tool):
                        self.assertIsNone(h.classify(command, {}))
                        self.assertIsNone(h.tool_decision(role, tool, {field: command}, {}))

    def test_unparseable_text_refuses_before_role_or_merge_exceptions(self):
        self.assert_unsupported_shell_refuses([
            'git status "unterminated', "git status 'unterminated", 'git status \\',
            f'{ROOT}/scripts/guard merge --pr "unterminated',
        ])

    def test_unmodeled_expansions_and_process_substitution_refuse(self):
        self.assert_unsupported_shell_refuses([
            'git status ${suffix}; npm publish', 'git status $suffix',
            'git status "${suffix}"', "git status '$suffix'",
            'git status <(npm publish)', 'git status >(npm publish)',
            f'{ROOT}/scripts/guard merge --pr 0 <(npm publish)',
        ])

    def test_unaccounted_tokenizer_remainder_refuses(self):
        import shlex
        h = module()
        class IncompleteLexer(shlex.shlex):
            def __iter__(self):
                # Fault injection at the parser boundary: valid prefix, unread suffix.
                yield self.get_token()
                yield self.get_token()
        with patch.object(shlex, 'shlex', IncompleteLexer):
            command = 'git status -- probe#file; npm publish'
            self.assertEqual(h.classify(command, {}), 'unparsed')
            for role in ('worker', 'reviewer', 'orchestrator'):
                for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
                    with self.subTest(role=role, tool=tool):
                        self.assertEqual(h.tool_decision(role, tool, {field: command}, {}),
                                         'shell syntax is unsupported; use separate simple commands')

    def assert_unsupported_shell_refuses(self, commands):
        h = module()
        for command in commands:
            for role in ('reviewer', 'worker', 'orchestrator'):
                for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
                    with self.subTest(command=command, role=role, tool=tool):
                        self.assertEqual(h.classify(command, {}), 'unparsed')
                        reason = h.tool_decision(role, tool, {field: command}, {})
                        self.assertEqual(reason, 'shell syntax is unsupported; use separate simple commands')
                        # Handler-only probe: embedded merge/publish text is never executed.
                        # No cwd: syntax must refuse before policy lookup or merge-entry bypass.
                        result = subprocess.run([str(ROOT / 'hooks/pre-tool-use'), '--role', role],
                            input=json.dumps({'tool_name': tool, 'tool_input': {field: command}}),
                            text=True, capture_output=True)
                        self.assertEqual(result.returncode, 0, result.stderr)
                        out = json.loads(result.stdout)['hookSpecificOutput']
                        self.assertEqual(out['permissionDecision'], 'deny')
                        self.assertEqual(out['permissionDecisionReason'], reason)

    def test_newline_merge_and_publish_chains_refuse_every_role(self):
        self.assert_unsupported_shell_refuses([
            'git status\ngh pr merge 0 --squash', 'git status\nnpm publish',
            'git status\r\nnpm publish', 'git status\\\nnpm publish',
            f'{ROOT}/scripts/guard merge --pr 0\nnpm publish',
        ])

    def test_control_and_non_shell_whitespace_refuse_every_role(self):
        self.assert_unsupported_shell_refuses([
            'git status' + separator + 'npm publish'
            for separator in ('\r', '\f', '\v', '\x00', '\x1b', '\x7f', '\x85', '\u00a0', '\u2028', '\u2029')
        ])

    def test_substitution_refuses_every_role_even_inside_quotes(self):
        self.assert_unsupported_shell_refuses([
            'git status `npm publish`', 'git status $(npm publish)',
            'git status "$(npm publish)"', "git status '$(npm publish)'",
            f'{ROOT}/scripts/guard merge --pr $(npm publish)',
        ])

    def test_horizontal_whitespace_and_parsed_separators(self):
        h = module()
        for role in ('reviewer', 'worker', 'orchestrator'):
            for command in ('git status --porcelain', 'git status\t--porcelain'):
                with self.subTest(role=role, command=command):
                    self.assertIsNone(h.tool_decision(role, 'Bash', {'command': command}, {}))
            for separator in (';', '&&', '||', '|', '&', '(', ')', '<(', '>('):
                command = 'git status ' + separator + ' npm publish'
                with self.subTest(role=role, command=command):
                    self.assertIsNotNone(h.tool_decision(role, 'Bash', {'command': command}, {}))

    def test_wrappers_protection_apply_and_compound_release_refuse(self):
        h = module()
        for command in ('git -C /tmp tag v1.2.3', 'gh --repo o/r pr merge 12',
                        '/opt/plugin/scripts/guard protection --repo o/r --apply',
                        'git push origin :refs/heads/main', 'git push origin v1.2.3',
                        'gh api repos/o/r/releases -f tag_name=v1.2.3'):
            with self.subTest(command=command):
                self.assertIsNotNone(h.tool_decision('worker', 'Bash', {'command': command}, {}))
        self.assertEqual(h.classify('git tag v1.2.3; rm -rf /srv/data', {}), 'irreversible')
        self.assertIsNone(h.classify('git push --force-with-lease origin task/12', {}))
        self.assertIsNone(h.classify('gh issue comment 12 --body "gh pr merge 12"', {}))
        self.assertIsNotNone(h.tool_decision('reviewer', 'Bash', {'command': 'sed -i s/a/b/ f'}, {}))

    def test_settings_add_recognized_commands(self):
        h = module()
        settings = {'command_patterns': {'irreversible': [r'\bacmectl destroy\b']}}
        self.assertEqual(h.classify('acmectl destroy db', settings), 'irreversible')
        self.assertEqual(h.classify('gh pr merge 12', settings), 'merge')
        settings = {'command_patterns': {'release': [], 'merge': [], 'irreversible': []}}
        for command, kind in [('git --no-pager tag v0.1.2', 'release'),
                              ('gh -Rowner/repo pr merge 0', 'merge'),
                              ('gh -Rowner/repo api -XDELETE repos/o/r', 'irreversible')]:
            self.assertEqual(h.classify(command, settings), kind)

    def test_worker_cannot_merge_release_or_delete_external_resources(self):
        h = module()
        self.assertTrue(hasattr(h, 'tool_decision'), 'role command guard is missing')
        for command in ('gh pr merge 12 --squash', 'git tag v1.0.0',
                        'git push origin --tags', 'npm publish', 'gh repo delete o/r --yes',
                        'gh api -X DELETE repos/o/r', 'git push origin HEAD:main'):
            with self.subTest(command=command):
                reason = h.tool_decision('worker', 'Bash', {'command': command}, {})
                self.assertIn('worker', reason)
        self.assertIsNone(h.tool_decision('worker', 'Bash', {'command': 'git status --porcelain'}, {}))
        self.assertIn('tool', h.tool_decision('worker', 'mcp__github__merge_pull_request', {}, {}))

    def test_reviewer_has_no_write_or_external_tools(self):
        h = module()
        self.assertTrue(hasattr(h, 'tool_decision'), 'role command guard is missing')
        for tool in ('Write', 'Edit', 'apply_patch', 'mcp__github__create_issue'):
            self.assertIsNotNone(h.tool_decision('reviewer', tool, {}, {}))
        self.assertIsNone(h.tool_decision('reviewer', 'Read', {}, {}))

    def test_orchestrator_requires_authorization_for_recognized_irreversibles(self):
        h = module()
        self.assertTrue(hasattr(h, 'tool_decision'), 'authorization guard is missing')
        for command in ('rm -rf /srv/data', 'git push --force origin main', 'gh release create v1.0.0'):
            self.assertIn('authorization', h.tool_decision('orchestrator', 'Bash', {'command': command}, {}))
        self.assertIsNone(h.tool_decision('orchestrator', 'Bash', {'command': 'git status'}, {}))


class AcceptanceTest(unittest.TestCase):
    def verdict(self, head='a'*40, goal='Yes', floor='Pass'):
        return f"""## Merge check 1 — round 1
Reviewer: Probe, read-only — reviewed {head}
### Goal verdict
{goal} — assessed.
### Floor
1. Evidence-backed completion claim: {floor} — checked.
2. Authorization and scope: Pass — checked.
Ready to merge: {'Yes' if goal == 'Yes' and floor == 'Pass' else 'No'} — decided.
### Notes
None.
Post this verdict whole on the PR before acting on it.
"""

    def test_incomplete_failed_and_stale_verdicts_refuse(self):
        h = module()
        self.assertTrue(hasattr(h, 'acceptance'), 'reviewed-head guard is missing')
        row = {'body': self.verdict(), 'id': 1, 'user': {'login': 'owner'}}
        self.assertEqual(h.acceptance([row], 'a'*40)['id'], 1)
        for body in (self.verdict(head='b'*40), self.verdict(goal='No'),
                     self.verdict(floor='Fail'), 'Ready to merge: Yes'):
            with self.subTest(body=body), self.assertRaises(h.Refusal):
                h.acceptance([dict(row, body=body)], 'a'*40)

    def test_latest_failed_verdict_revokes_old_acceptance(self):
        h = module()
        self.assertTrue(hasattr(h, 'acceptance'), 'reviewed-head guard is missing')
        with self.assertRaises(h.Refusal):
            h.acceptance([{'body': self.verdict(), 'id': 1},
                          {'body': self.verdict(goal='No'), 'id': 2}], 'a'*40)

    def test_inconsistent_readiness_and_duplicate_sections_refuse(self):
        h = module()
        for body in (self.verdict().replace('Ready to merge: Yes', 'Ready to merge: No'),
                     self.verdict()+'\n### Goal verdict\nNo — revoked.'):
            with self.assertRaises(h.Refusal):
                h.acceptance([{'body': body, 'id': 1}], 'a'*40)

    def test_wrapped_floor_grounds_keep_the_whole_verdict(self):
        h = module()
        body = self.verdict().replace('1. Evidence-backed completion claim: Pass — checked.',
            '1. Evidence-backed completion claim: Pass — checked.\n   The evidence matches the final head.\n')
        h.acceptance([{'id':1,'body':body}], 'a'*40)

    def test_goal_presentation_never_hides_duplicate_or_borrowed_answers(self):
        h = module()
        for goal in ('### Goal verdict\n\n### Other\nYes',
                     '### Goal verdict\n\nUndecided.\nYes',
                     '### Goal verdict\n\nYesterday'):
            with self.subTest(goal=goal), self.assertRaises(h.Refusal):
                h.acceptance([{'id':1,'body':self.verdict().replace('### Goal verdict\nYes',goal)}], 'a'*40)
        duplicate = self.verdict() + '\n### **Goal verdict**\n\n**No** — revoked.\n'
        with self.assertRaises(h.Refusal):
            h.acceptance([{'id':1,'body':duplicate}], 'a'*40)


class RoundTest(AcceptanceTest):
    def rows(self, n=1, goal='No', floor='Pass'):
        return [{'id': i, 'body': self.verdict(goal=goal, floor=floor).replace('round 1', f'round {i}'),
                 'user': {'login': 'o'}} for i in range(1, n+1)]

    def rule(self, n, decision, head='a'*40):
        record = {'kind': 'ruling', 'round': n, 'head': head, 'decision': decision, 'reason': 'assessed gap'}
        return {'id': 100, 'user': {'login': 'o'}, 'body': f'## Review ruling — after round {n}\n\n'
                '<!-- devstandard-review-v1 -->\n```json\n'+json.dumps(record)+'\n```\n'}

    def test_cap_and_floor_failures_refuse_dispatch_despite_ruling(self):
        h = module()
        self.assertTrue(hasattr(h, 'round_check'), 'round admission missing')
        with self.assertRaisesRegex(h.Refusal, 'ruling'):
            h.round_check(self.rows(), 'a'*40)
        h.round_check(self.rows()+[self.rule(1, 'continue')], 'a'*40)
        with self.assertRaisesRegex(h.Refusal, 'Notes'):
            h.round_check(self.rows(goal='Yes')+[self.rule(1, 'continue')], 'a'*40)
        with self.assertRaisesRegex(h.Refusal, '7 review rounds'):
            h.round_check(self.rows(7)+[self.rule(7, 'continue')], 'a'*40)
        rows = self.rows()
        rows[0]['body'] = rows[0]['body'].replace('2. Authorization and scope: Pass', '2. Authorization and scope: Fail')
        with self.assertRaisesRegex(h.Refusal, 'Floor check 2'):
            h.round_check(rows+[self.rule(1, 'continue')], 'a'*40)

    def test_merge_ruling_cannot_waive_floor_or_accept_another_head(self):
        h = module()
        self.assertTrue(hasattr(h, 'merge_acceptance'), 'merge ruling integration missing')
        h.merge_acceptance(self.rows()+[self.rule(1, 'merge-as-is')], 'a'*40)
        for rows in (self.rows(floor='Fail')+[self.rule(1, 'merge-as-is')],
                     self.rows()+[self.rule(1, 'merge-as-is', 'b'*40)], self.rows(7, goal='Yes')):
            with self.assertRaises(h.Refusal):
                h.merge_acceptance(rows, 'a'*40)

    def test_rebuild_three_returned_record_and_active_attempt(self):
        h = module()
        self.assertTrue(hasattr(h, 'merge_acceptance'), 'record consumer missing')
        record = {'kind': 'attempt', 'status': 'returned', 'round': 1, 'head': 'a'*40,
                  'architecture': 'NO', 'base': 'b'*40}
        body = '## Merge check 1 — round 1\n\n<!-- devstandard-review-v1 -->\n```json\n'+json.dumps(record)+'\n```\n\n'+self.verdict().split('\n',1)[1]
        rows = [{'id': 1, 'body': body, 'user': {'login': 'o'}}]
        self.assertEqual(h.merge_acceptance(rows, 'a'*40)['id'], 1)
        active = dict(record, status='dispatched', round=2)
        rows.append({'id': 2, 'body': '## Review attempt — round 2\n\n<!-- devstandard-review-v1 -->\n```json\n'+json.dumps(active)+'\n```\n'})
        with self.assertRaisesRegex(h.Refusal, 'active'):
            h.merge_acceptance(rows, 'a'*40)


class ApiTest(unittest.TestCase):
    def test_codex_config_runs_hook_with_fixed_role(self):
        h = module()
        self.assertTrue(hasattr(h, 'codex_hook_config'), 'Codex hook carrier missing')
        import tomllib
        import shlex
        config = tomllib.loads(h.codex_hook_config(ROOT, 'worker'))
        command = config['hooks']['PreToolUse'][0]['hooks'][0]['command']
        result = subprocess.run(shlex.split(command), input=json.dumps({'tool_name':'Bash',
            'tool_input':{'command':'gh pr merge 0 --squash'}, 'cwd':str(ROOT)}), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['hookSpecificOutput']['permissionDecisionReason'],
                         'worker role refuses recognized merge operation')

    def test_paginated_api_keeps_later_revocation(self):
        h = module()
        with patch.object(h, 'run', return_value='[{"id":1}]\n[{"id":2}]'):
            self.assertEqual(h.api('comments', '--paginate'), [{'id':1}, {'id':2}])

    def test_check_runs_newest_failure_refuses(self):
        h = module()
        runs = [{'id':1, 'name':'test', 'status':'completed', 'conclusion':'success', 'app':{'id':15368}},
                {'id':2, 'name':'test', 'status':'completed', 'conclusion':'failure', 'app':{'id':15368}}]
        def api(endpoint, *args):
            return {'check_runs':runs} if 'check-runs' in endpoint else {'statuses':[]}
        with patch.object(h,'api',side_effect=api), self.assertRaises(h.Refusal):
            h.commit_checks('o/r','a'*40)


class AuthorizationTest(unittest.TestCase):
    def test_orchestrator_token_variants_reach_exact_authorization_or_standing_release(self):
        import hashlib
        settings = {'authorization_issue': 204, 'human_logins': ['human']}
        for command in ('git --no-pager tag v0.1.2', 'git -cuser.name=Probe tag v0.1.2',
                        'gh -Rowner/repo release create v0.1.2'):
            record = {'repo': 'LeonJoeeee/devstandard', 'head': 'a'*40, 'kind': 'release',
                      'command_sha256': hashlib.sha256(command.encode()).hexdigest(),
                      'expires': '2099-01-01T00:00:00+00:00'}
            rows = [{'user': {'login': 'human'},
                     'body': '<!-- devstandard-authorization-v1 -->\n' + json.dumps(record)}]
            for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
                with self.subTest(command=command, tool=tool):
                    result, queries = orchestrator_hook(command, tool, field, settings=settings, rows=rows)
                    self.assertEqual(result, {})
                    self.assertEqual(queries, 1)
                    result, _ = orchestrator_hook(command + ' --dry-run', tool, field,
                                                  settings=settings, rows=rows)
                    self.assertEqual(result['hookSpecificOutput']['permissionDecision'], 'deny')
                    delegation = {'standing_release': {'repo': 'LeonJoeeee/devstandard',
                        'source': 'https://github.com/LeonJoeeee/devstandard/issues/204#issuecomment-1'}}
                    result, queries = orchestrator_hook(command, tool, field, settings=delegation)
                    self.assertEqual(result, {})
                    self.assertEqual(queries, 0)
                    for candidate in (command.replace('v0.1.2', 'v1.0.0'), command + '; rm -rf /probe'):
                        result, _ = orchestrator_hook(candidate, tool, field, settings=delegation)
                        self.assertEqual(result['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_only_exact_installed_merge_entry_reaches_merge_verification(self):
        for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
            command = str(ROOT / 'scripts/guard') + ' merge --pr 0'
            result, _ = orchestrator_hook(command, tool, field)
            self.assertEqual(result, {})  # The entry point itself owns reviewed-head verification.
            for candidate in ('gh -RLeonJoeeee/devstandard pr merge 0 --squash',
                              'scripts/guard merge --pr 0', command + '; true',
                              command + ' > /dev/null'):
                with self.subTest(command=candidate, tool=tool):
                    result, queries = orchestrator_hook(candidate, tool, field)
                    output = result['hookSpecificOutput']
                    self.assertEqual(output['permissionDecision'], 'deny')
                    self.assertIn('scripts/guard merge', output['permissionDecisionReason'])
                    self.assertEqual(queries, 0)

    def test_orchestrator_redirection_authorization_remains_bound_to_exact_command(self):
        import hashlib
        import io
        import runpy
        h = module()
        command = 'npm < /dev/null publish'
        settings = {'authorization_issue': 1, 'human_logins': ['human']}
        record = {'repo': 'o/r', 'head': 'a'*40, 'kind': 'release',
                  'command_sha256': hashlib.sha256(command.encode()).hexdigest(),
                  'expires': '2099-01-01T00:00:00+00:00'}
        rows = [{'user': {'login': 'human'},
                 'body': '<!-- devstandard-authorization-v1 -->\n' + json.dumps(record)}]
        # Only GitHub/policy/head reads are doubled; parse, authorization and hook output are real.
        with patch.dict(sys.modules, {'hard_edges': h}), \
             patch.object(h, 'settings_for', return_value=('o/r', settings)), \
             patch.object(h, 'run', return_value='a'*40), patch.object(h, 'api', return_value=rows):
            for role, candidate, allowed in [('orchestrator', command, True),
                    ('orchestrator', command + ' --dry-run', False),
                    ('orchestrator', 'eval ' + repr(command), False),
                    ('worker', command, False), ('reviewer', command, False)]:
                event = {'tool_name': 'Bash', 'tool_input': {'command': candidate}, 'cwd': str(ROOT)}
                out = io.StringIO()
                with self.subTest(role=role, command=candidate), \
                     patch.object(sys, 'argv', ['pre-tool-use', '--role', role]), \
                     patch.object(sys, 'stdin', io.StringIO(json.dumps(event))), patch.object(sys, 'stdout', out):
                    runpy.run_path(str(ROOT / 'hooks/pre-tool-use'), run_name='__main__')
                    result = json.loads(out.getvalue())
                    if allowed:
                        self.assertEqual(result, {})
                    else:
                        self.assertEqual(result['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_latest_revocation_and_cross_repository_delegation_refuse(self):
        h = module()
        import hashlib
        record = {'repo':'o/r', 'head':'a'*40, 'kind':'irreversible',
                  'command_sha256':hashlib.sha256(b'rm -rf /srv/data').hexdigest(),
                  'expires':'2099-01-01T00:00:00+00:00'}
        def row(record):
            return {'user':{'login':'human'}, 'body':'<!-- devstandard-authorization-v1 -->\n'+json.dumps(record)}
        with patch.object(h, 'api', return_value=[row(record), row(dict(record, revoked=True))]):
            self.assertFalse(h.authorized('o/r','a'*40,'rm -rf /srv/data','irreversible',
                                         {'authorization_issue':1,'human_logins':['human']}))
        with patch.object(h, 'api', return_value=[row(record), row(dict(record, expires='invalid'))]):
            self.assertFalse(h.authorized('o/r','a'*40,'rm -rf /srv/data','irreversible',
                                         {'authorization_issue':1,'human_logins':['human']}))
        self.assertFalse(h.authorized('o/r','a'*40,'git tag v1.2.3','release',
            {'standing_release':{'repo':'o/r','source':'https://github.com/other/repo/issues/1#issuecomment-1'}}))

    def test_authorization_binds_actor_repo_head_command_and_expiry(self):
        h = module()
        self.assertTrue(hasattr(h, 'authorized'), 'durable authorization lookup is missing')
        import hashlib
        command = 'gh release create v1.0.0'
        record = {'kind': 'release', 'repo': 'o/r', 'head': 'a'*40,
                  'command_sha256': hashlib.sha256(command.encode()).hexdigest(),
                  'expires': '2099-01-01T00:00:00+00:00'}
        row = {'user': {'login': 'human'}, 'body': '<!-- devstandard-authorization-v1 -->\n'+json.dumps(record)}
        settings = {'human_logins': ['human'], 'authorization_issue': 1}
        with patch.object(h, 'api', return_value=[row]):
            self.assertTrue(h.authorized('o/r', 'a'*40, command, 'release', settings))
            self.assertFalse(h.authorized('o/r', 'b'*40, command, 'release', settings))
            self.assertFalse(h.authorized('o/r', 'a'*40, command+' --draft', 'release', settings))
            self.assertFalse(h.authorized('o/r', 'a'*40, command, 'release', dict(settings, human_logins=[])))
        record['expires'] = '2000-01-01T00:00:00+00:00'
        row['body'] = '<!-- devstandard-authorization-v1 -->\n'+json.dumps(record)
        with patch.object(h, 'api', return_value=[row]):
            self.assertFalse(h.authorized('o/r', 'a'*40, command, 'release', settings))

    def test_standing_delegation_requires_durable_source_and_does_not_cover_major(self):
        h = module()
        self.assertTrue(hasattr(h, 'authorized'), 'durable authorization lookup is missing')
        settings = {'standing_release': {'repo': 'o/r', 'source': 'https://github.com/o/r/issues/1#issuecomment-1'}}
        self.assertTrue(h.authorized('o/r', 'a'*40, 'git tag v1.2.3', 'release', settings))
        self.assertFalse(h.authorized('o/r', 'a'*40, 'git tag v2.0.0', 'major-release', settings))


class MergeTest(AcceptanceTest):
    def test_merge_requires_current_base_acceptance_and_merged_result_ci(self):
        h = module()
        self.assertTrue(hasattr(h, 'merge_check'), 'integrated merge guard is missing')
        base, head = 'b'*40, 'a'*40
        pr = {'state': 'open', 'head': {'sha': head, 'repo': {'full_name': 'o/r'}},
              'base': {'sha': base, 'ref': 'main', 'repo': {'full_name': 'o/r'}}, 'body': 'architecture-level: false'}
        comments = [{'id': 1, 'body': self.verdict(), 'user': {'login': 'o'}}]
        def api(endpoint, *args):
            if endpoint.endswith('/pulls/12'): return pr
            if '/comments' in endpoint: return comments
            if endpoint.endswith('/branches/main'): return {'commit': {'sha': base}}
            if endpoint == 'repos/o/r': return {'default_branch': 'main'}
            self.fail(endpoint)
        with patch.object(h, 'api', side_effect=api), patch.object(h, 'run', return_value=''), \
             patch.object(h, 'settings_for', return_value=('o/r', {})), \
             patch.object(h, 'protection_check'), patch.object(h, 'commit_checks', return_value={'test':'success'}) as ci:
            result = h.merge_check(Path('.'), 'o/r', 12)
            self.assertEqual(result['head'], head)
            self.assertIn('merged-result / '+base+' / '+head, ci.call_args.args[2])
            pr['base']['sha'] = 'c'*40
            with self.assertRaisesRegex(h.Refusal, 'base'):
                h.merge_check(Path('.'), 'o/r', 12)

    def test_architecture_merge_requires_human_signoff(self):
        h = module()
        self.assertTrue(hasattr(h, 'merge_check'), 'integrated merge guard is missing')
        base, head = 'b'*40, 'a'*40
        pr = {'state':'open', 'head':{'sha':head, 'repo':{'full_name':'o/r'}},
              'base':{'sha':base,'ref':'main','repo':{'full_name':'o/r'}}, 'body':'architecture-level: true'}
        def api(endpoint, *args):
            if endpoint.endswith('/pulls/12'): return pr
            if '/comments' in endpoint: return [{'id':1,'body':self.verdict(),'user':{'login':'o'}}]
            if endpoint.endswith('/branches/main'): return {'commit':{'sha':base}}
            if endpoint == 'repos/o/r': return {'default_branch':'main'}
            self.fail(endpoint)
        with patch.object(h,'api',side_effect=api), patch.object(h,'run',return_value=''), \
             patch.object(h,'settings_for',return_value=('o/r',{})), patch.object(h,'protection_check'), \
             patch.object(h,'commit_checks',return_value={}), patch.object(h,'authorized',return_value=False):
            with self.assertRaisesRegex(h.Refusal,'human sign-off'):
                h.merge_check(Path('.'),'o/r',12)


if __name__ == '__main__':
    unittest.main(verbosity=2)
