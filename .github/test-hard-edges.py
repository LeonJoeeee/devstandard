#!/usr/bin/env python3
"""Hard-edge probes: real git replay, with doubled external GitHub responses."""
import importlib.util
import json
import os
from pathlib import Path
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


class ToolGuardTest(unittest.TestCase):
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
