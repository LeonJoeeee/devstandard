#!/usr/bin/env python3
"""Hard-edge probes: real git replay, with doubled external GitHub responses."""
from contextlib import contextmanager, redirect_stderr
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import call, patch

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

# The verbatim reviewer returns live once, in the suite that publishes them; the acceptance
# check must read every presentation its publisher reads (#251).
_spec = importlib.util.spec_from_file_location('review_packet_tests',
                                               Path(__file__).with_name('test-review-packet.py'))
verdicts = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verdicts)


SWEEP_TESTS = {
    'RoleRuleTest.test_every_refused_word_refuses_in_every_position',
}


def parse_shard(value):
    """Unset runs everything; rest runs non-sweeps; INDEX/TOTAL runs one sweep slice."""
    if value is None or value == 'rest':
        return value
    match = re.fullmatch(r'([0-9]+)/([0-9]+)', value)
    if match:
        index, total = map(int, match.groups())
        if 0 <= index < total:
            return index, total
    raise ValueError('HARD_EDGE_SHARD must be rest or INDEX/TOTAL with 0 <= INDEX < TOTAL')


def selected_probe(index, shard):
    return shard is None or index % shard[1] == shard[0]


def iter_tests(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from iter_tests(test)
        else:
            yield test


def load_tests(loader, standard_tests, pattern):
    shard = parse_shard(os.environ.get('HARD_EDGE_SHARD'))
    if shard is None:
        return standard_tests
    return unittest.TestSuite(
        test for test in iter_tests(standard_tests)
        if ('.'.join(test.id().split('.')[-2:]) in SWEEP_TESTS) == (shard != 'rest'))


class ShardSelectionTest(unittest.TestCase):
    def test_unset_preserves_full_suite_and_all_probes(self):
        suite = unittest.TestSuite([ProtectionTest('test_protected_and_unprotected_api_shapes')])
        with patch.dict(os.environ):
            os.environ.pop('HARD_EDGE_SHARD', None)
            self.assertIs(load_tests(None, suite, None), suite)
        self.assertTrue(all(selected_probe(i, parse_shard(None)) for i in range(19)))

    def test_shards_partition_uneven_probe_count_without_duplicates(self):
        slices = [[i for i in range(19) if selected_probe(i, parse_shard(f'{n}/3'))]
                  for n in range(3)]
        self.assertEqual(slices, [[0, 3, 6, 9, 12, 15, 18], [1, 4, 7, 10, 13, 16],
                                  [2, 5, 8, 11, 14, 17]])

    def test_invalid_selectors_fail_instead_of_silently_losing_coverage(self):
        for value in ('', '0', 'all', '0/0', '8/8', '-1/8', '0/-8', '0/8/2', 'a/8'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_shard(value)

    def test_rest_and_sweep_modes_partition_test_methods(self):
        tests = unittest.TestSuite([
            unittest.defaultTestLoader.loadTestsFromTestCase(RoleRuleTest),
            unittest.defaultTestLoader.loadTestsFromTestCase(ProtectionTest),
        ])
        all_ids = {test.id() for test in iter_tests(tests)}
        with patch.dict(os.environ, HARD_EDGE_SHARD='0/8'):
            sweep_ids = {test.id() for test in load_tests(None, tests, None)}
        with patch.dict(os.environ, HARD_EDGE_SHARD='rest'):
            rest_ids = {test.id() for test in load_tests(None, tests, None)}
        self.assertEqual(len(sweep_ids), 1)
        self.assertEqual(sweep_ids & rest_ids, set())
        self.assertEqual(sweep_ids | rest_ids, all_ids)


def module():
    path = ROOT / 'scripts/hard_edges.py'
    assert path.exists(), 'hard-edge implementation is missing'
    spec = importlib.util.spec_from_file_location('hard_edges', path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


PROTECTED = {'required_status_checks': {'strict': True, 'contexts': ['test']},
             'enforce_admins': {'enabled': True},
             'allow_force_pushes': {'enabled': False}, 'allow_deletions': {'enabled': False}}


def protection_api(protection, rules):
    """Double the two reads `protection_check` makes: classic protection, then the active rules."""
    def call(endpoint, *args):
        answer = protection if endpoint.endswith('/protection') else rules
        if isinstance(answer, Exception):
            raise answer
        return answer
    return call


class ProtectionTest(unittest.TestCase):
    def test_protected_and_unprotected_api_shapes(self):
        h = module()
        with patch.object(h, 'api', side_effect=protection_api(PROTECTED, [])):
            h.protection_check('o/r', 'main', ['test'])
        with patch.object(h, 'api', side_effect=h.Refusal('gh: Branch not protected (HTTP 404)')):
            with self.assertRaisesRegex(h.Refusal, 'not protected'):
                h.protection_check('o/r', 'probe/unprotected', ['test'])
        for field in ['strict', 'contexts']:
            broken = json.loads(json.dumps(PROTECTED))
            broken['required_status_checks'][field] = False if field == 'strict' else []
            with patch.object(h, 'api', side_effect=protection_api(broken, [])):
                with self.assertRaises(h.Refusal):
                    h.protection_check('o/r', 'main', ['test'])

    def test_enabled_merge_queue_is_non_conforming(self):
        h = module()
        queued = [{'type': 'pull_request'},
                  {'type': 'merge_queue', 'ruleset_id': 7, 'parameters': {'merge_method': 'MERGE'}}]
        with patch.object(h, 'api', side_effect=protection_api(PROTECTED, queued)):
            with self.assertRaisesRegex(h.Refusal, 'merge queue'):
                h.protection_check('o/r', 'main', ['test'])
        with patch.object(h, 'api', side_effect=protection_api(PROTECTED, [{'type': 'pull_request'}])):
            self.assertEqual(h.protection_check('o/r', 'main', ['test'])['merge_queue'], 'off')

    def test_unreadable_rules_refuse_instead_of_passing(self):
        h = module()
        for rules in [h.Refusal('gh: API rate limit exceeded (HTTP 403)'), {'message': 'Not Found'}]:
            with self.subTest(rules=rules), patch.object(h, 'api',
                                                         side_effect=protection_api(PROTECTED, rules)):
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

    def manifest(self, version):
        """Carry the shipped manifests, so the fixture tracks their real shape."""
        for path in ('.claude-plugin/plugin.json', '.claude-plugin/marketplace.json'):
            target = self.repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            source = target.read_text() if target.exists() else (ROOT / path).read_text()
            target.write_text(re.sub(r'("version": ")[^"]+', r'\g<1>' + version, source))

    def bump_lane(self):
        """A reviewed lane whose bump collides with the bump another lane merged meanwhile."""
        self.git('checkout', 'main')
        self.manifest('0.99.0')
        self.commit('manifests')
        oldbase = self.git('rev-parse', 'HEAD')
        self.git('checkout', '-b', 'bump-topic')
        (self.repo / 'changed').write_text('lane work\n')
        self.manifest('0.99.1')
        self.commit('lane work carrying its own bump')
        oldhead = self.git('rev-parse', 'HEAD')
        self.git('checkout', 'main')
        (self.repo / 'other').write_text('merged elsewhere\n')
        self.manifest('0.99.1')
        self.commit('another lane merges with the same bump')
        newbase = self.git('rev-parse', 'HEAD')
        self.git('checkout', 'bump-topic')
        self.git('rebase', 'main')
        return oldbase, oldhead, newbase

    def revert_lane(self, merged='0.99.1'):
        """A reviewed lane that never touched the manifests, rebased past a merged bump."""
        self.git('checkout', 'main')
        self.manifest('0.99.0')
        self.commit('manifests')
        oldbase = self.git('rev-parse', 'HEAD')
        self.git('checkout', '-b', 'revert-topic')
        (self.repo / 'changed').write_text('lane work\n')
        self.commit('lane work leaving the manifests alone')
        oldhead = self.git('rev-parse', 'HEAD')
        self.git('checkout', 'main')
        (self.repo / 'other').write_text('merged elsewhere\n')
        self.manifest(merged)
        self.commit('another lane merges its own bump')
        newbase = self.git('rev-parse', 'HEAD')
        self.git('checkout', 'revert-topic')
        self.git('rebase', 'main')
        return oldbase, oldhead, newbase

    def collide_lane(self, upstream=None):
        """A reviewed lane whose own bump collides with the different bump main merged meanwhile."""
        self.git('checkout', 'main')
        self.manifest('0.99.0')
        self.commit('manifests')
        oldbase = self.git('rev-parse', 'HEAD')
        self.git('checkout', '-b', 'collide-topic')
        (self.repo / 'changed').write_text('lane work\n')
        self.manifest('0.99.1')
        self.commit('lane work carrying its own bump')
        oldhead = self.git('rev-parse', 'HEAD')
        self.git('checkout', 'main')
        (self.repo / 'other').write_text('merged elsewhere\n')
        if upstream:
            (self.repo / 'changed').write_text(upstream)
        self.manifest('0.99.5')
        self.commit('another lane merges a bump of its own')
        newbase = self.git('rev-parse', 'HEAD')
        # Where the human's own rebase lands: the lane's work on main, version still to resolve.
        self.git('checkout', '-b', 'collide-rebased')
        (self.repo / 'changed').write_text('lane work\n')
        return oldbase, oldhead, newbase

    def test_a_version_line_conflict_in_the_replay_still_proves(self):
        """Both sides bumped from one base to different values; nothing else differs."""
        h = module()
        oldbase, oldhead, newbase = self.collide_lane()
        self.manifest('0.99.6')
        self.commit('rebase onto the merged bump, resolved to the next lockstep value')
        proof = h.compare_rebase(self.repo, oldbase, oldhead, newbase, self.git('rev-parse', 'HEAD'))
        self.assertEqual(proof['comparison'], 'pass')
        self.assertEqual(proof['version_bump'], ['0.99.1', '0.99.6'])
        self.assertEqual(proof['paths'], ['.claude-plugin/marketplace.json',
                                          '.claude-plugin/plugin.json', 'changed'])
        self.assertEqual(self.git('status', '--porcelain', '-uall'), '')

    def test_a_lane_whose_bump_is_its_own_commit_replays_through_the_conflict(self):
        """Resolving to the base empties that commit; the replay still lands the lane's work."""
        h = module()
        self.git('checkout', 'main')
        self.manifest('0.99.0')
        self.commit('manifests')
        oldbase = self.git('rev-parse', 'HEAD')
        self.git('checkout', '-b', 'split-topic')
        (self.repo / 'changed').write_text('lane work\n')
        self.commit('lane work')
        self.manifest('0.99.1')
        self.commit('the bump, on a commit of its own')
        oldhead = self.git('rev-parse', 'HEAD')
        self.git('checkout', 'main')
        self.manifest('0.99.5')
        self.commit('another lane merges a bump of its own')
        newbase = self.git('rev-parse', 'HEAD')
        self.git('checkout', '-b', 'split-rebased')
        (self.repo / 'changed').write_text('lane work\n')
        self.manifest('0.99.6')
        self.commit('the lane rebased, resolved to the next lockstep value')
        proof = h.compare_rebase(self.repo, oldbase, oldhead, newbase, self.git('rev-parse', 'HEAD'))
        self.assertEqual(proof['version_bump'], ['0.99.1', '0.99.6'])
        self.assertEqual(proof['paths'], ['.claude-plugin/marketplace.json',
                                          '.claude-plugin/plugin.json', 'changed'])

    def test_a_resolved_version_conflict_below_the_merged_bump_refuses(self):
        """Resolving to the base keeps the replay-side ordering live: 0.99.2 is under main's."""
        h = module()
        oldbase, oldhead, newbase = self.collide_lane()
        self.manifest('0.99.2')
        self.commit('rebase past the merged bump but set a version below it')
        with self.assertRaisesRegex(h.Refusal, 'above the versions they replace'):
            h.compare_rebase(self.repo, oldbase, oldhead, newbase, self.git('rev-parse', 'HEAD'))

    def test_a_version_conflict_beside_another_conflicted_path_refuses(self):
        """One more changed line outside the manifests puts the replay back in full review."""
        h = module()
        oldbase, oldhead, newbase = self.collide_lane(upstream='upstream work\n')
        self.manifest('0.99.6')
        self.commit('rebase onto the merged bump, keeping the reviewed line')
        with self.assertRaisesRegex(h.Refusal, 'conflict-free rebase proof refused'):
            h.compare_rebase(self.repo, oldbase, oldhead, newbase, self.git('rev-parse', 'HEAD'))

    def test_a_conflicted_path_shaped_like_a_manifest_is_still_not_one(self):
        """This body satisfies the version-line reading, so only the path list rejects it."""
        h = module()
        decoy = self.repo / 'decoy.json'
        body = '{\n  "plugins": [\n    {\n      "version": "%s"\n    }\n  ]\n}\n'
        self.git('checkout', 'main')
        self.manifest('0.99.0')
        decoy.write_text(body % '0.99.0')
        self.commit('manifests beside a file shaped like one')
        oldbase = self.git('rev-parse', 'HEAD')
        self.git('checkout', '-b', 'decoy-topic')
        self.manifest('0.99.1')
        decoy.write_text(body % '0.99.1')
        self.commit('lane bump beside its own decoy bump')
        oldhead = self.git('rev-parse', 'HEAD')
        self.git('checkout', 'main')
        self.manifest('0.99.5')
        decoy.write_text(body % '0.99.5')
        self.commit('another lane merges a different bump beside the decoy')
        newbase = self.git('rev-parse', 'HEAD')
        self.git('checkout', '-b', 'decoy-rebased')
        decoy.write_text(body % '0.99.1')
        self.manifest('0.99.6')
        self.commit('the reviewed decoy on main, resolved to the next lockstep value')
        with self.assertRaisesRegex(h.Refusal, 'conflict-free rebase proof refused'):
            h.compare_rebase(self.repo, oldbase, oldhead, newbase, self.git('rev-parse', 'HEAD'))

    def test_a_manifest_conflict_off_the_version_line_refuses(self):
        """A conflict inside a manifest but not confined to its version line is not the exempt one."""
        h = module()
        plugin = self.repo / '.claude-plugin/plugin.json'
        self.git('checkout', 'main')
        self.manifest('0.99.0')
        self.commit('manifests')
        oldbase = self.git('rev-parse', 'HEAD')
        self.git('checkout', '-b', 'describe-topic')
        self.manifest('0.99.1')
        plugin.write_text(plugin.read_text().replace('"description": "', '"description": "lane '))
        self.commit('lane bump beside its own description edit')
        oldhead = self.git('rev-parse', 'HEAD')
        self.git('checkout', 'main')
        self.manifest('0.99.5')
        plugin.write_text(plugin.read_text().replace('"description": "', '"description": "merged '))
        self.commit('another lane merges a different bump and description')
        newbase = self.git('rev-parse', 'HEAD')
        self.git('checkout', '-b', 'describe-rebased')
        plugin.write_text(plugin.read_text().replace('"description": "merged ', '"description": "lane '))
        self.manifest('0.99.6')
        self.commit('the reviewed manifests on main, resolved to the next lockstep value')
        with self.assertRaisesRegex(h.Refusal, 'conflict-free rebase proof refused'):
            h.compare_rebase(self.repo, oldbase, oldhead, newbase, self.git('rev-parse', 'HEAD'))

    def test_rebase_past_a_merged_bump_cannot_set_the_manifests_back(self):
        """Both pins read 0.99.0, so no bump is collected and the exemption has nothing to admit."""
        h = module()
        oldbase, oldhead, newbase = self.revert_lane()
        self.manifest('0.99.0')
        self.commit('set the manifests back to the reviewed version')
        with self.assertRaisesRegex(h.Refusal, 'reviewed head bump'):
            h.compare_rebase(self.repo, oldbase, oldhead, newbase, self.git('rev-parse', 'HEAD'))

    def test_version_lines_moving_down_refuse(self):
        """A collected lockstep pair is still a regression when it lowers the version."""
        h = module()
        oldbase, oldhead, newbase = self.bump_lane()
        self.manifest('0.99.0')
        self.commit('lower the version below the reviewed head and the replay')
        with self.assertRaisesRegex(h.Refusal, 'above the versions they replace'):
            h.compare_rebase(self.repo, oldbase, oldhead, newbase, self.git('rev-parse', 'HEAD'))

    def test_a_bump_above_the_reviewed_head_but_below_the_replay_refuses(self):
        """The lane's own pair rises, so only the replay-side ordering sees the lost merged bump."""
        h = module()
        oldbase, oldhead, newbase = self.revert_lane('0.99.5')
        self.manifest('0.99.1')
        self.commit('bump above the reviewed head but below what main merged')
        with self.assertRaisesRegex(h.Refusal, 'above the versions they replace'):
            h.compare_rebase(self.repo, oldbase, oldhead, newbase, self.git('rev-parse', 'HEAD'))

    def test_manifest_read_failure_refuses_instead_of_raising_value_error(self):
        """review_packet's readers raise ValueError; this guard boundary presents Refusal."""
        h = module()
        # A real read of a path absent at both pins: review_packet raises, the boundary refuses.
        with self.assertRaisesRegex(h.Refusal, 'cannot read pinned version diff'):
            h.refusing(h.manifest_bump, self.repo, self.base, self.old, '.claude-plugin/plugin.json')
        oldbase, oldhead, newbase = self.bump_lane()
        self.manifest('0.99.2')
        self.commit('resolve the version to the next lockstep value')
        with patch.object(h, 'manifest_bump', side_effect=ValueError('unreadable manifest')):
            with self.assertRaisesRegex(h.Refusal, 'unreadable manifest'):
                h.compare_rebase(self.repo, oldbase, oldhead, newbase, self.git('rev-parse', 'HEAD'))

    def test_manifest_version_lines_only_rebase_proves(self):
        h = module()
        oldbase, oldhead, newbase = self.bump_lane()
        self.manifest('0.99.2')
        self.commit('resolve the version to the next lockstep value')
        proof = h.compare_rebase(self.repo, oldbase, oldhead, newbase, self.git('rev-parse', 'HEAD'))
        self.assertEqual(proof['comparison'], 'pass')
        self.assertEqual(proof['version_bump'], ['0.99.1', '0.99.2'])
        self.assertEqual(proof['paths'], ['.claude-plugin/marketplace.json',
                                          '.claude-plugin/plugin.json', 'changed'])
        self.assertEqual(self.git('status', '--porcelain', '-uall'), '')

    def test_any_third_line_beside_the_version_lines_refuses(self):
        h = module()
        oldbase, oldhead, newbase = self.bump_lane()
        replay = self.git('rev-parse', 'HEAD')
        plugin = self.repo / '.claude-plugin/plugin.json'
        for change in ('manifest field', 'other path', 'one manifest', 'mode', 'deleted manifest',
                       'not in lockstep'):
            with self.subTest(change=change):
                self.git('reset', '--hard', replay)
                self.manifest('0.99.2')
                if change == 'manifest field':
                    plugin.write_text(plugin.read_text().replace('"name": "devstandard"', '"name": "other"'))
                elif change == 'other path':
                    (self.repo / 'changed').write_text('unreviewed\n')
                elif change == 'one manifest':
                    self.git('checkout', replay, '--', '.claude-plugin/marketplace.json')
                elif change == 'mode':
                    plugin.chmod(0o755)
                elif change == 'deleted manifest':
                    self.git('rm', '--force', '--quiet', '.claude-plugin/plugin.json')
                else:
                    plugin.write_text(plugin.read_text().replace('0.99.2', '0.99.4'))
                self.commit(change)
                with self.assertRaisesRegex(h.Refusal, 'identical|lockstep|replay'):
                    h.compare_rebase(self.repo, oldbase, oldhead, newbase,
                                     self.git('rev-parse', 'HEAD'))

    def test_reviewed_head_out_of_lockstep_is_not_exempt(self):
        """The replay is a clean lockstep pair, so only the exemption's own check refuses."""
        h = module()
        self.git('checkout', 'main')
        self.manifest('0.99.0')
        self.commit('manifests')
        oldbase = self.git('rev-parse', 'HEAD')
        self.git('checkout', '-b', 'half-bump')
        (self.repo / 'changed').write_text('lane work\n')
        self.manifest('0.99.1')
        self.git('checkout', oldbase, '--', '.claude-plugin/marketplace.json')
        self.commit('lane work bumping one manifest only')
        oldhead = self.git('rev-parse', 'HEAD')
        self.git('checkout', 'main')
        self.manifest('0.99.1')
        self.commit('another lane merges a lockstep bump')
        newbase = self.git('rev-parse', 'HEAD')
        self.git('checkout', 'half-bump')
        self.git('rebase', 'main')
        self.manifest('0.99.2')
        self.commit('resolve the version')
        with self.assertRaisesRegex(h.Refusal, 'lockstep'):
            h.compare_rebase(self.repo, oldbase, oldhead, newbase, self.git('rev-parse', 'HEAD'))

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
        with patch.object(h,'api',side_effect=api), patch.object(h,'settings_for',return_value={}), patch.object(h,'project_repo',return_value='o/r'), patch.object(h,'protection_check'):
            result = h.merge_check(self.repo,'o/r',12,self.base,self.old)
            self.assertEqual(result['comparison']['comparison'],'pass')
            integration = 'merged-result / stale base / '+self.new
            with self.assertRaisesRegex(h.Refusal,'required CI checks unmet'):
                h.merge_check(self.repo,'o/r',12,self.base,self.old)
            with self.assertRaisesRegex(h.Refusal,'exact accepted head'):
                h.merge_check(self.repo,'o/r',12)


# ---------------------------------------------------------------------------
# The role hook's one rule (#323): raw text, a short word list per role.
# Every command below is decision input only; none of them run.
# ---------------------------------------------------------------------------

LANE = '/home/dev/project/.claude/worktrees/323-probe'

# The positions a word can occupy in a command. The hook reads raw text, so the
# quoted, here-doc and substitution bodies are read exactly like the bare one.
POSITIONS = [
    ('bare', lambda command: command),
    ('quoted', lambda command: "echo '" + command + "'"),
    ('heredoc', lambda command: 'cat <<EOF\n' + command + '\nEOF'),
    ('substitution', lambda command: 'echo $(' + command + ')'),
    ('cd composition', lambda command: 'cd ' + LANE + ' && ' + command),
]

# One literal witness per refused word, per role. A regression in the word list
# shows here; the sweep multiplies these by position and tool-input format.
REFUSED = {
    'worker': [
        ('merge', 'git merge origin/main'),
        ('merge', 'gh pr merge 1 --squash'),
        ('tag', 'git tag -a v1 -m x'),
        ('release', 'gh release create v1'),
        ('--force', 'git push --force origin task/x'),
        ('branch -D', 'git branch -D task/x'),
        ('branch --delete', 'git branch --delete task/x'),
        ('push --delete', 'git push --delete origin task/x'),
        ('worktree remove', 'git worktree remove ' + LANE),
        ('rm -r', 'rm -rf /srv/data'),
        ('rm -r', 'rm -fr /srv/data'),
        ('rm -r', 'rm --recursive /srv/data'),
        ('push', 'git push origin main'),
        ('push', 'git push origin HEAD:refs/heads/main'),
    ],
    'reviewer': [
        ('push', 'git push origin task/x'),
        ('merge', 'git merge origin/main'),
        ('tag', 'git tag -a v1 -m x'),
        ('release', 'gh release create v1'),
        ('delete', 'gh repo delete o/r --yes'),
        ('rm', 'rm /tmp/probe'),
        ('-X', 'gh api repos/o/r -X POST'),
        ('-X', 'gh api repos/o/r -XPOST'),
        ('--method', 'gh api repos/o/r --method POST'),
        ('--method', 'gh api repos/o/r --method=POST'),
        ('-f', 'gh api repos/o/r -f name=value'),
        ('-F', 'gh api repos/o/r -F name=value'),
        ('--input', 'gh api repos/o/r --input body.json'),
    ],
    'orchestrator': [
        ('gh pr merge', 'gh pr merge 1 --squash'),
        ('git merge', 'git merge origin/main'),
        ('push', 'git push origin main'),
        ('push', 'git push --force origin refs/heads/main'),
        ('tag', 'git tag -a v1 -m x'),
        ('release', 'gh release create v1'),
    ],
}

# Ordinary work each role must keep. A refusal here is the failure the human's
# 2026-09-10 ruling is about.
ADMITTED = {
    'worker': [
        'git push origin task/x',
        'git push --force-with-lease origin task/x',
        'git push --force-with-lease=refs/heads/task/x origin HEAD:task/x',
        'git push --force-with-lease --force-if-includes origin task/x',
        'cd ' + LANE + ' && git push --force-with-lease origin task/x',
        'rm -rf /tmp/devstandard-x.abc',
        'rm -rf /tmp/a /tmp/b',
        'cd ' + LANE + ' && rm -rf /tmp/devstandard-x.abc',
        'rm /srv/one-file',
        "python3 -c 'import json\nprint(json.dumps({\"ok\": 1}))'",
        'gh issue view 323 --json title --jq "$(printf \'.title\')"',
        'for f in reference/*.md; do echo "$f"; done',
        'git rebase origin/main',
        'git merge-base --is-ancestor HEAD origin/main',
        'git status --porcelain -uall',
        'git commit -F /tmp/message.txt',
        'gh pr create --body-file /tmp/body.md',
        'python3 .github/test-hard-edges.py',
        'git status "unterminated',
        'git log --format=%B -1 | cat',
    ],
    'reviewer': [
        'gh pr view 1 --json body',
        'gh issue view 323 --comments',
        'gh api repos/o/r/issues/1/comments --paginate',
        'gh api repos/o/r/issues/1/comments --jq ".[].body"',
        'gh run view 1 --log-failed',
        'cat reference/hard-edges.md',
        'rg -n "^##" reference/hard-edges.md',
        "find reference -name '*.md'",
        'git diff origin/main...HEAD',
        'git log --oneline -20',
        'cd /srv/checkout && cat reference/worker.md',
        'git status "unterminated',
    ],
    'orchestrator': [
        '/plugin/scripts/guard merge --repo o/r --pr 1 --project .',
        'gh issue view 323 --json title --jq "$(printf \'.title\')"',
        'git push origin --delete task/x',
        'git push origin task/x',
        'git branch -D task/x',
        'git worktree remove ' + LANE,
        'rm -rf ' + LANE,
        'gh pr view 1 --json body',
        'gh api repos/o/r/issues/1/comments -f body=text',
        'for f in reference/*.md; do echo "$f"; done',
        'git status "unterminated',
    ],
}

# The standing release delegation this repository actually carries (#37).
DELEGATION = {'repo': 'LeonJoeeee/devstandard',
              'source': 'https://github.com/LeonJoeeee/devstandard/issues/37#issuecomment-5557328234'}


_SHARED = []


def shared_module():
    """One import of the real implementation for the probes that only read it."""
    if not _SHARED:
        _SHARED.append(module())
    return _SHARED[0]


def role_hook(command, tool='Bash', field='command', *, settings=None, role='orchestrator',
              cwd=None):
    """Run the real hook handler; only the policy snapshot is supplied directly.

    `api` and `run` are doubled to raise on every call, so a GitHub read or a
    subprocess on the decision path fails the probe instead of answering it.
    """
    h = shared_module()
    event = {'tool_name': tool, 'tool_input': {field: command}, 'cwd': cwd or str(ROOT)}
    out = io.StringIO()
    with patch.dict(sys.modules, {'hard_edges': h}), \
         patch.object(h, 'settings_for', return_value=dict(settings or {})), \
         patch.object(h, 'run', side_effect=AssertionError('the hook ran a subprocess')), \
         patch.object(h, 'api', side_effect=AssertionError('the hook read GitHub')), \
         patch.object(sys, 'argv', ['pre-tool-use', '--role', role]), \
         patch.object(sys, 'stdin', io.StringIO(json.dumps(event))), patch.object(sys, 'stdout', out):
        runpy.run_path(str(ROOT / 'hooks/pre-tool-use'), run_name='__main__')
    return json.loads(out.getvalue())


class RoleRuleTest(unittest.TestCase):
    """The whole hook contract: raw text, one word list per role, nothing else."""

    def deny(self, result, command):
        output = result.get('hookSpecificOutput', {})
        self.assertEqual(output.get('permissionDecision'), 'deny', command)
        return output['permissionDecisionReason']

    def test_every_refused_word_refuses_in_every_position(self):
        shard = parse_shard(os.environ.get('HARD_EDGE_SHARD'))
        probes = seen = 0
        for role, rows in REFUSED.items():
            for word, witness in rows:
                for position, wrap in POSITIONS:
                    candidate = wrap(witness)
                    for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
                        index = seen
                        seen += 1
                        if not selected_probe(index, shard):
                            continue
                        with self.subTest(role=role, word=word, position=position, tool=tool):
                            # A guarded repository: the founding admission is its own probe.
                            reason = self.deny(role_hook(candidate, tool, field, role=role,
                                                         settings={'_policy': True}), candidate)
                            self.assertIn(role, reason)
                            probes += 1
        print(f'Role word-list sweep: {probes} role/word/position/tool refusals')

    def test_ordinary_work_is_admitted_for_every_role(self):
        for role, commands in ADMITTED.items():
            settings = {'standing_release': DELEGATION} if role == 'orchestrator' else {}
            for command in commands:
                for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
                    with self.subTest(role=role, command=command, tool=tool):
                        self.assertEqual(role_hook(command, tool, field, role=role,
                                                   settings=settings), {})

    def test_unparseable_syntax_is_never_a_reason_to_refuse(self):
        """Every role: broken quoting decides on its words alone (#323)."""
        for command in ('git status "unterminated', "git status 'unterminated",
                        'git status \\', 'git status ${', 'git status $(', 'git status `',
                        'git status ;; --porcelain', 'git status |& cat'):
            for role in ('worker', 'reviewer', 'orchestrator'):
                with self.subTest(command=command, role=role):
                    self.assertEqual(role_hook(command, role=role), {})

    def test_obfuscation_and_interpreters_are_outside_the_hook(self):
        """The accepted residual, stated as behaviour rather than left implied."""
        for command in ('python3 -c \'import subprocess; subprocess.run(["git","pu"+"sh","origin","ma"+"in"])\'',
                        'bash /tmp/land-it.sh',
                        'echo Z2l0IHB1c2ggb3JpZ2luIG1haW4= | base64 -d | sh'):
            for role in ('worker', 'reviewer', 'orchestrator'):
                with self.subTest(command=command, role=role):
                    self.assertEqual(role_hook(command, role=role), {})

    def test_the_refusal_reason_names_the_word_and_the_merge_entry(self):
        h = module()
        self.assertIn("'merge'", h.tool_decision('worker', 'Bash', {'command': 'git merge x'}, {}))
        self.assertIn('scripts/guard merge', h.tool_decision(
            'orchestrator', 'Bash', {'command': 'gh pr merge 1'}, {}))
        self.assertIn('scripts/guard merge', h.tool_decision(
            'orchestrator', 'Bash', {'command': 'git merge origin/main'}, {}))
        self.assertIn('main', h.tool_decision(
            'orchestrator', 'Bash', {'command': 'git push origin main'}, {'_policy': True}))
        self.assertIn('delegation', h.tool_decision(
            'orchestrator', 'Bash', {'command': 'git tag -a v1 -m x'}, {}))

    def test_a_word_is_never_read_through_a_hyphen(self):
        """`--force-with-lease` is not `--force`, and `git merge-base` is not `merge`."""
        h = module()
        for command in ('git push --force-with-lease origin task/x',
                        'git push --force-if-includes origin task/x',
                        'git merge-base --is-ancestor HEAD origin/x',
                        'git merge-tree HEAD origin/x'):
            with self.subTest(command=command):
                self.assertIsNone(h.tool_decision('worker', 'Bash', {'command': command}, {}))
        self.assertTrue(h.carries('gh api repos/o/r -XPOST', '-X'))
        self.assertTrue(h.carries('git push --tags origin', 'tag'))
        self.assertFalse(h.carries('git push --force-with-lease origin x', '--force'))

    def test_a_phrase_matches_only_where_its_words_stand_together(self):
        h = module()
        self.assertTrue(h.carries('git branch -D task/x', 'branch -D'))
        self.assertTrue(h.carries('cat <<EOF\ngit branch\n-D x\nEOF', 'branch -D'))
        self.assertFalse(h.carries('git branch -v -D task/x', 'branch -D'))
        self.assertFalse(h.carries('gh pr view 1 && git log --grep merge', 'gh pr merge'))

    def test_the_worker_push_rule_needs_the_default_branch_by_name(self):
        h = module()
        for command, refused in (('git push origin task/x', False),
                                 ('git push origin main', True),
                                 ('git push origin master', True),
                                 ('git push origin HEAD:main', True),
                                 ('git push origin refs/heads/main', True),
                                 ('git push origin task/mainline', True),
                                 ('git push origin task/main-line', False),
                                 ('git rebase origin/main', False)):
            with self.subTest(command=command):
                self.assertEqual(h.tool_decision('worker', 'Bash', {'command': command}, {})
                                 is not None, refused)

    def test_a_policy_default_branch_joins_main_and_master(self):
        h = module()
        settings = {'default_branch': 'trunk'}
        self.assertIsNotNone(h.tool_decision('worker', 'Bash',
                             {'command': 'git push origin trunk'}, settings))
        self.assertIsNotNone(h.tool_decision('orchestrator', 'Bash',
                             {'command': 'git push origin HEAD:refs/heads/trunk'},
                             dict(settings, _policy=True)))
        self.assertIsNone(h.tool_decision('worker', 'Bash',
                          {'command': 'git push origin trunk-task'}, settings))

    def test_the_temp_cleanup_boundary(self):
        h = module()
        for command, admitted in (('rm -rf /tmp/x', True),
                                  ('rm -rf /tmp/x /tmp/y', True),
                                  ('cd ' + LANE + ' && rm -rf /tmp/x', True),
                                  ('rm -rf /tmp/x && echo done', True),
                                  ('rm -rf "/tmp/x"', True),
                                  ('rm -rf /tmp', False),
                                  ('rm -rf /tmp/', False),
                                  ('rm -rf /', False),
                                  ('rm -rf /tmp/../srv', False),
                                  ('rm -rf /tmp/x /srv/y', False),
                                  ('rm -rf relative', False),
                                  ('rm -rf', False),
                                  ('rm -rf $TMPDIR/x', False),
                                  ('rm -rf /var/tmp/x', False)):
            with self.subTest(command=command):
                self.assertEqual(h.tool_decision('worker', 'Bash', {'command': command}, {})
                                 is None, admitted)

    def test_the_standing_delegation_gates_orchestrator_tag_and_release(self):
        h = module()
        for command in ('git tag -a v1 -m x', 'gh release create v1', 'git push origin --tags'):
            with self.subTest(command=command):
                self.assertIsNotNone(h.tool_decision('orchestrator', 'Bash', {'command': command}, {}))
                self.assertIsNone(h.tool_decision('orchestrator', 'Bash', {'command': command},
                                                  {'standing_release': DELEGATION}))
                # The delegation is the orchestrator's alone.
                for role in ('worker', 'reviewer'):
                    self.assertIsNotNone(h.tool_decision(role, 'Bash', {'command': command},
                                                         {'standing_release': DELEGATION}))

    def test_a_delegation_without_a_durable_comment_source_is_no_delegation(self):
        h = module()
        for delegation in (None, {}, {'repo': 'o/r'},
                           {'repo': 'o/r', 'source': 'the human said so'},
                           {'repo': 'o/r', 'source': 'https://github.com/other/repo/issues/1#issuecomment-1'},
                           {'repo': 'o/r', 'source': 'https://github.com/o/r/issues/1'}):
            with self.subTest(delegation=delegation):
                self.assertFalse(h.standing_delegation({'standing_release': delegation}))
        self.assertTrue(h.standing_delegation({'standing_release': DELEGATION}))
        self.assertTrue(h.standing_delegation(
            {'standing_release': {'repo': 'o/r',
                                  'source': 'https://github.com/o/r/pull/2#issuecomment-3'}}))

    def test_policy_words_add_to_a_role_and_never_subtract(self):
        h = module()
        settings = {'command_patterns': {'worker': ['acmectl destroy'], 'reviewer': ['acmectl'],
                                         'orchestrator': ['acmectl destroy']}}
        for role in ('worker', 'reviewer', 'orchestrator'):
            with self.subTest(role=role):
                self.assertIsNotNone(h.tool_decision(role, 'Bash',
                                     {'command': 'acmectl destroy db'}, settings))
        # A policy that names an empty list, a wrong role or a wrong shape subtracts nothing.
        for patterns in ({'worker': []}, {'unknown-role': ['git status']}, {'worker': 'merge'},
                         'nonsense', None):
            with self.subTest(patterns=patterns):
                broken = {'command_patterns': patterns}
                self.assertIsNotNone(h.tool_decision('worker', 'Bash',
                                     {'command': 'git merge origin/main'}, broken))
                self.assertIsNone(h.tool_decision('worker', 'Bash',
                                  {'command': 'git status'}, broken))

    def test_tool_surfaces_are_unchanged(self):
        h = module()
        for tool in ('Write', 'Edit', 'apply_patch', 'mcp__github__create_issue'):
            self.assertIsNotNone(h.tool_decision('reviewer', tool, {}, {}))
        for tool in ('Read', 'Glob', 'Grep', 'Bash', 'exec_command', 'view_image'):
            self.assertIsNone(h.tool_decision('reviewer', tool, {}, {}))
        for tool in ('Read', 'Bash', 'Edit', 'Write', 'Skill', 'apply_patch', 'update_plan'):
            self.assertIsNone(h.tool_decision('worker', tool, {}, {}))
        self.assertIsNotNone(h.tool_decision('worker', 'mcp__github__merge_pull_request', {}, {}))
        self.assertIn('scripts/guard merge',
                      h.tool_decision('orchestrator', 'mcp__github__merge_pull_request', {}, {}))
        self.assertIsNone(h.tool_decision('orchestrator', 'Read', {}, {}))

    def test_a_native_worker_or_reviewer_subagent_type_selects_its_own_role(self):
        h = module()
        for agent_type in ('worker', 'devstandard:worker', 'reviewer', 'devstandard:reviewer'):
            with self.subTest(agent_type=agent_type):
                out = io.StringIO()
                event = {'tool_name': 'Bash', 'tool_input': {'command': 'git merge origin/main'},
                         'cwd': str(ROOT), 'agent_type': agent_type}
                with patch.dict(sys.modules, {'hard_edges': h}), \
                     patch.object(h, 'settings_for', return_value={}), \
                     patch.object(sys, 'argv', ['pre-tool-use', '--role', 'orchestrator']), \
                     patch.object(sys, 'stdin', io.StringIO(json.dumps(event))), \
                     patch.object(sys, 'stdout', out):
                    runpy.run_path(str(ROOT / 'hooks/pre-tool-use'), run_name='__main__')
                reason = json.loads(out.getvalue())['hookSpecificOutput']['permissionDecisionReason']
                self.assertIn(agent_type.split(':')[-1], reason)


class LocalPolicyTest(unittest.TestCase):
    """`settings_for` reads `origin/main:.github/devstandard-guards.json` with git, and nothing else."""

    POLICY = {'required_checks': ['build'], 'standing_release': DELEGATION,
              'command_patterns': {'worker': ['acmectl destroy']}}

    def setUp(self):
        self.h = module()
        tmp = self.enterContext(tempfile.TemporaryDirectory(prefix='local-policy-'))
        self.tmp = Path(tmp)
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith('GIT_') and k not in ('GH_REPO', 'GH_TOKEN', 'GITHUB_TOKEN')}
        self.env.update(GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1', LC_ALL='C',
                        GH_CONFIG_DIR=str(self.tmp / 'gh-config'),
                        PATH=str(self.tmp) + os.pathsep + os.environ['PATH'])
        # Every network call fails, in the vocabulary `gh` prints when it reaches no server.
        failing = self.tmp / 'gh'
        failing.write_text('#!' + sys.executable + '\nimport sys\n'
                           'sys.stderr.write("Post \\"https://api.github.com/graphql\\": EOF\\n")\n'
                           'sys.exit(1)\n')
        failing.chmod(0o755)
        self.founded = 0

    def git(self, at, *args):
        result = subprocess.run(['git', '-C', str(at)] + list(args), env=self.env,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def found(self, policy=None):
        """A real upstream with a real clone, so `origin/main` is a real local ref."""
        self.founded += 1
        upstream = self.tmp / f'upstream-{self.founded}'
        project = self.tmp / f'project-{self.founded}'
        upstream.mkdir()
        self.git(self.tmp, 'init', '-b', 'main', str(upstream))
        for key, value in (('user.email', 'p@example.invalid'), ('user.name', 'Probe')):
            self.git(upstream, 'config', key, value)
        if policy is not None:
            (upstream / '.github').mkdir(exist_ok=True)
            (upstream / '.github/devstandard-guards.json').write_text(
                policy if isinstance(policy, str) else json.dumps(policy))
            self.git(upstream, 'add', '.github/devstandard-guards.json')
        else:
            (upstream / 'README.md').write_text('probe\n')
            self.git(upstream, 'add', 'README.md')
        self.git(upstream, 'commit', '-m', 'found')
        self.git(self.tmp, 'clone', '--quiet', str(upstream), str(project))
        return project

    def hook(self, project, command, role='worker', tool='Bash', field='command'):
        event = {'tool_name': tool, 'tool_input': {field: command}, 'cwd': str(project)}
        result = subprocess.run([str(ROOT / 'hooks/pre-tool-use'), '--role', role],
                                cwd=str(ROOT), env=self.env, input=json.dumps(event),
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_the_policy_comes_from_the_default_branch_ref_not_the_working_tree(self):
        project = self.found(self.POLICY)
        # An unmerged local edit grants nothing and adds nothing.
        (project / '.github/devstandard-guards.json').write_text(json.dumps(
            {'command_patterns': {'worker': ['git status']}, 'standing_release': None}))
        settings = self.h.settings_for(str(project))
        self.assertEqual(settings['required_checks'], ['build'])
        self.assertEqual(settings['command_patterns'], {'worker': ['acmectl destroy']})
        self.assertIs(settings['_policy'], True)
        self.assertEqual(self.hook(project, 'git status'), {})
        self.assertEqual(self.hook(project, 'acmectl destroy db')
                         ['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_the_hook_decides_with_the_network_failing_on_every_call(self):
        """Same decisions as the unit probes above, with `gh` guaranteed to fail (#303, #323)."""
        project = self.found(self.POLICY)
        for role, command, admitted in (
                ('worker', 'git status --porcelain', True),
                ('worker', 'git push --force-with-lease origin task/x', True),
                ('worker', 'git push origin main', False),
                ('worker', 'git merge origin/main', False),
                ('reviewer', 'gh pr view 1 --json body', True),
                ('reviewer', 'gh api repos/o/r -X POST', False),
                ('orchestrator', 'gh issue view 1 --json title', True),
                ('orchestrator', 'git tag -a v1 -m x', True),  # the policy's delegation
                ('orchestrator', 'gh pr merge 1 --squash', False),
                ('orchestrator', 'git push origin main', False)):
            with self.subTest(role=role, command=command):
                result = self.hook(project, command, role)
                if admitted:
                    self.assertEqual(result, {})
                else:
                    self.assertEqual(result['hookSpecificOutput']['permissionDecision'], 'deny')
                    self.assertNotIn('EOF', result['hookSpecificOutput']['permissionDecisionReason'])

    def test_a_missing_unreadable_or_malformed_policy_means_the_built_in_defaults(self):
        for name, policy in (('no policy file', None), ('malformed', '{not json'),
                             ('not an object', '[]'),
                             ('junk extras', '{"command_patterns": "nonsense"}')):
            with self.subTest(policy=name):
                project = self.found(policy)
                self.assertEqual(self.hook(project, 'git status'), {})
                self.assertEqual(self.hook(project, 'git merge origin/main')
                                 ['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_a_directory_outside_any_repository_means_the_built_in_defaults(self):
        outside = self.tmp / 'outside'
        outside.mkdir()
        self.assertEqual(self.h.settings_for(str(outside)), {})
        self.assertEqual(self.hook(outside, 'git init -b main', 'orchestrator'), {})
        self.assertEqual(self.hook(outside, 'git merge origin/main')
                         ['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_the_founding_push_is_admitted_only_while_the_branch_carries_no_policy(self):
        """An `authorization_issue` cannot precede the file that names it (ADR 0046, #293)."""
        unguarded = self.found(None)
        self.assertEqual(self.hook(unguarded, 'git push origin main', 'orchestrator'), {})
        self.assertEqual(self.hook(unguarded, 'git push -u origin HEAD:main', 'orchestrator'), {})
        # Nothing else, and no other role.
        for role in ('worker', 'reviewer'):
            self.assertEqual(self.hook(unguarded, 'git push origin main', role)
                             ['hookSpecificOutput']['permissionDecision'], 'deny')
        self.assertEqual(self.hook(unguarded, 'gh pr merge 1', 'orchestrator')
                         ['hookSpecificOutput']['permissionDecision'], 'deny')
        # The push that lands the policy file closes the door behind itself.
        guarded = self.found(self.POLICY)
        self.assertEqual(self.hook(guarded, 'git push origin main', 'orchestrator')
                         ['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_no_github_read_reaches_the_hook_decision_path(self):
        """The done-check's grep, as an assertion: `settings_for` is one local `git show`."""
        source = (ROOT / 'scripts/hard_edges.py').read_text()
        body = source[source.index('def settings_for'):]
        body = body[:body.index('\ndef ', 1)]
        self.assertIn("'show', 'origin/main:' + POLICY_PATH", body)
        self.assertNotIn('api(', body)
        for name in ('PolicyUnreadable', 'reading_policy', 'TRANSPORT_FAILURES', 'classify',
                     'shell_segments', 'unsupported_shell', 'worker_routine_command',
                     'unparsed_orchestrator_reason'):
            self.assertNotIn(name, source, f'{name} should be gone with the grammar (#323)')


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
        # Ordinary Markdown spacing — a blank line after every heading — is still a whole verdict (#230).
        spaced = self.verdict().replace('### Goal verdict\n', '### Goal verdict\n\n').replace(
            '### Floor\n', '### Floor\n\n').replace('### Notes\n', '### Notes\n\n')
        self.assertEqual(h.acceptance([dict(row, body=spaced)], 'a'*40)['id'], 1)
        for body in (self.verdict(head='b'*40), self.verdict(goal='No'),
                     self.verdict(floor='Fail'), 'Ready to merge: Yes'):
            with self.subTest(body=body), self.assertRaises(h.Refusal):
                h.acceptance([dict(row, body=body)], 'a'*40)

    def test_emphasized_results_accept_ready_and_refuse_incomplete_failed_and_stale(self):
        h = module()
        for emphasis in ('*', '**', '_', '__'):
            for wrap in ('result', 'label', 'line'):
                def wrapped(goal='Yes', floor='Pass'):
                    body = self.verdict(goal=goal, floor=floor)
                    for heading in ('Goal verdict', 'Floor', 'Notes'):
                        body = body.replace(f'### {heading}\n', f'### {heading}\n\n')
                    body = re.sub(r'^(Yes|No)(?= —)', f'{emphasis}\\1{emphasis}', body, flags=re.M)
                    ready = 'Yes' if goal == 'Yes' and floor == 'Pass' else 'No'
                    for label, value in (('1. Evidence-backed completion claim:', floor),
                                         ('2. Authorization and scope:', 'Pass'),
                                         ('Ready to merge:', ready)):
                        body = body.replace(f'{label} {value}',
                                            verdicts.decision(label, value, emphasis, wrap))
                    return body
                row = {'id': 1, 'body': wrapped()}
                with self.subTest(emphasis=emphasis, wrap=wrap):
                    self.assertEqual(h.acceptance([row], 'a'*40), row)
                    self.assertEqual(h.acceptance([dict(row, body=wrapped(goal='No'))], 'a'*40,
                                                  allow_goal_no=True)['id'], 1)
                for invalid in (row['body'].replace('a'*40, 'b'*40), wrapped(goal='No'),
                                wrapped(floor='Fail'),
                                row['body'].replace('Authorization and scope:', 'Missing floor:'),
                                row['body'].replace('### Notes\n', ''),
                                row['body'].replace('Post this verdict whole on the PR before acting on it.', '')):
                    with self.subTest(emphasis=emphasis, wrap=wrap, invalid=invalid), self.assertRaises(h.Refusal):
                        h.acceptance([dict(row, body=invalid)], 'a'*40)

    def test_publication_and_acceptance_agree_on_groundless_decision_lines(self):
        """One verdict, one answer: what the guard refuses, publication calls malformed (#287).

        PR #284's bare `Ready to merge: Yes` split them — publication recorded it accepted and
        the guard refused it, so the packet would admit no further round.
        """
        h = module()
        outcome = runpy.run_path(str(ROOT / 'scripts/review-packet'))['outcome']
        record = {'head': 'a' * 40, 'identity': 'Probe, read-only'}
        for bare in (None, *(line for line, _ in verdicts.DECISION_LINES)):
            body = verdicts.canonical_verdict(bare=bare)
            row = {'id': 1, 'user': {'login': 'o'}, 'body': '## Merge check 1 — round 1\n' + body}
            try:
                h.acceptance([row], 'a' * 40)
                refused = None
            except h.Refusal as error:
                refused = str(error)
            with self.subTest(line=bare):
                self.assertEqual(outcome(body, record)['valid'], refused is None, refused)
                self.assertEqual(refused is None, bare is None)

    def test_exact_label_emphasized_verdict_from_pr_247_is_admitted(self):
        h = module()
        row = {'id': 1, 'user': {'login': 'o'},
               'body': '## Merge check 1 — round 1\n' + verdicts.LABEL_EMPHASIZED_ROUND_ONE_VERDICT}
        self.assertEqual(h.acceptance([row], '0bd3b0acf4457c0960cc676b78227914ab6a51fe')['id'], 1)

    def test_publication_and_acceptance_both_refuse_each_malformed_shape(self):
        h = module()
        outcome = runpy.run_path(str(ROOT / 'scripts/review-packet'))['outcome']
        record = {'head': 'a' * 40, 'identity': 'Probe, read-only'}
        for name, body in verdicts.malformed_shapes().items():
            row = {'id': 1, 'body': '## Merge check 1 — round 1\n' + body}
            with self.subTest(shape=name, consumer='publication'):
                self.assertFalse(outcome(body, record)['valid'])
            with self.subTest(shape=name, consumer='acceptance'), self.assertRaises(h.Refusal):
                h.acceptance([row], record['head'])

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

    def test_accepted_recovery_requires_a_ruling_bound_to_that_head(self):
        h = module()
        for recovery in (dict(kind='behind-base', head='a'*40, base='b'*40),
                         dict(kind='guard-refusal', head='a'*40, reason='guard refused: malformed verdict')):
            ruling = self.rule(1, 'continue')
            record = json.loads(ruling['body'].split('```json\n')[1].split('\n```')[0])
            record['recovery'] = recovery
            ruling['body'] = ruling['body'].split('```json\n')[0] + '```json\n' + json.dumps(record) + '\n```\n'
            with self.subTest(recovery=recovery):
                rows = self.rows(goal='Yes')
                self.assertEqual(h.round_check(rows+[ruling], 'a'*40)['next_round'], 2)
                with self.assertRaisesRegex(h.Refusal, 'Notes'):
                    h.round_check(rows+[self.rule(1, 'continue')], 'a'*40)
                stale = dict(ruling)
                record['recovery'] = dict(recovery, head='c'*40)
                stale['body'] = ruling['body'].split('```json\n')[0] + '```json\n' + json.dumps(record) + '\n```\n'
                with self.assertRaisesRegex(h.Refusal, 'Notes'):
                    h.round_check(rows+[stale], 'a'*40)

    def test_emphasized_floor_two_failure_stops_the_lane(self):
        """The stop-lane trigger reads the parsed decision, never raw verdict text (#260)."""
        h = module()
        for emphasis in ('*', '**', '_', '__'):
            for wrap in ('result', 'label', 'line'):
                rows = self.rows()
                rows[0]['body'] = rows[0]['body'].replace('2. Authorization and scope: Pass',
                    verdicts.decision('2. Authorization and scope:', 'Fail', emphasis, wrap))
                with self.subTest(emphasis=emphasis, wrap=wrap), \
                        self.assertRaisesRegex(h.Refusal, 'Floor check 2'):
                    h.round_check(rows+[self.rule(1, 'continue')], 'a'*40)

    def test_a_later_contradicting_floor_two_line_still_stops_the_lane(self):
        """A Fail on any Floor 2 line stops the lane; a passing first line cannot cover it (#260)."""
        h = module()
        rows = self.rows()
        rows[0]['body'] = rows[0]['body'].replace('2. Authorization and scope: Pass — checked.',
            '2. Authorization and scope: Pass — checked.\n2. **Authorization and scope: Fail** — revoked.')
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
    def test_codex_config_sets_gating_subagent_defaults_for_both_roles(self):
        import tomllib
        for role in ('worker', 'reviewer'):
            with self.subTest(role=role):
                result = subprocess.run([str(ROOT / 'scripts/guard'), 'codex-config',
                                         '--role', role], text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                config = tomllib.loads(result.stdout)
                self.assertEqual(config.get('agents'), {
                    'default_subagent_model': 'gpt-6-astra',
                    'default_subagent_reasoning_effort': 'high',
                })

    def test_codex_config_runs_hook_with_fixed_role(self):
        h = module()
        self.assertTrue(hasattr(h, 'codex_hook_config'), 'Codex hook carrier missing')
        import tomllib
        import shlex
        config = tomllib.loads(h.codex_hook_config(ROOT, 'worker'))
        command = config['hooks']['PreToolUse'][0]['hooks'][0]['command']
        with tempfile.TemporaryDirectory(prefix='codex-config-') as project:
            result = subprocess.run(shlex.split(command), input=json.dumps({'tool_name':'Bash',
                'tool_input':{'command':'gh pr merge 0 --squash'}, 'cwd':project}),
                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['hookSpecificOutput']['permissionDecisionReason'],
                         "worker role refuses a command carrying 'merge'")

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


class DefaultBranchCiTest(unittest.TestCase):
    """#314: the dispatch gate judges by the target's own policy, never a name we picked."""

    def setUp(self):
        self.h = module()
        self.head = 'a' * 40

    def gate(self, settings, observed):
        def api(endpoint, *args):
            if endpoint == 'repos/o/r': return {'default_branch': 'main'}
            if endpoint == 'repos/o/r/branches/main': return {'commit': {'sha': self.head}}
            if '/check-runs?' in endpoint:
                return {'check_runs': [{'id': i, 'name': name, 'status': 'completed',
                                        'conclusion': conclusion}
                                       for i, (name, conclusion) in enumerate(observed.items())]}
            if '/status?' in endpoint: return {'statuses': []}
            self.fail(endpoint)
        with patch.object(self.h, 'api', side_effect=api):
            return self.h.default_ci('o/r', settings)

    def refusal(self, settings, observed):
        with self.assertRaises(self.h.Refusal) as error:
            self.gate(settings, observed)
        message = str(error.exception)
        self.assertIn('default-branch CI refused dispatch', message)
        return message

    def test_policy_named_check_admits_a_head_whose_ci_is_not_called_test(self):
        result = self.gate({'required_checks': ['tests'], '_policy': True}, {'tests': 'success'})
        self.assertEqual(result, {'branch': 'main', 'head': self.head, 'checks': {'tests': 'success'}})

    def test_policy_naming_no_checks_admits_a_head_whose_every_check_is_green(self):
        observed = {'tests': 'success', 'cycle-pr': 'success', 'notebook-english': 'skipped'}
        for settings in ({'_policy': False}, {'merge_method': 'squash', '_policy': True}):
            with self.subTest(settings=settings):
                self.assertEqual(self.gate(settings, observed)['checks'], observed)

    def test_policy_naming_no_checks_still_refuses_a_red_head_and_names_the_failure(self):
        message = self.refusal({'_policy': False}, {'tests': 'success', 'cycle-pr': 'failure'})
        self.assertIn('CI not green', message)
        self.assertIn("'cycle-pr': 'failure'", message)

    def test_policy_naming_no_checks_still_refuses_a_head_carrying_no_check_at_all(self):
        self.assertIn('no CI checks reported', self.refusal({'_policy': False}, {}))

    def test_a_required_check_the_head_lacks_refuses_naming_the_set_it_applied(self):
        message = self.refusal({'required_checks': ['test'], '_policy': True}, {'tests': 'success'})
        self.assertIn("required=['test']", message)
        self.assertIn("'tests': 'success'", message)
        # CI is green here; only the policy's own name is absent, so the refusal may not say red.
        self.assertNotIn('not green', message)


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

    def test_the_record_is_the_only_one_left_and_never_a_release_grant(self):
        """#323: a standing delegation is read from policy by the hook, never from a record."""
        h = module()
        settings = {'standing_release': {'repo': 'o/r',
                                         'source': 'https://github.com/o/r/issues/1#issuecomment-1'},
                    'authorization_issue': 1, 'human_logins': ['human']}
        with patch.object(h, 'api', return_value=[]):
            self.assertFalse(h.authorized('o/r', 'a'*40, 'git tag v1.2.3', 'release', settings))
        self.assertTrue(h.standing_delegation(settings))


class VersionBumpTest(unittest.TestCase):
    git = RebaseTest.git
    commit = RebaseTest.commit

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='version-bump-test-')
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1')
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Probe')
        self.git('config', 'user.email', 'probe@example.invalid')
        self.paths = ['.claude-plugin/plugin.json', '.claude-plugin/marketplace.json']
        (self.repo / '.claude-plugin').mkdir()
        for path in self.paths:
            (self.repo / path).write_bytes((ROOT / path).read_bytes())
        self.commit('base')
        self.base = self.git('rev-parse', 'HEAD')
        for path in self.paths:
            source = (self.repo / path).read_text()
            import re
            (self.repo / path).write_text(re.sub(r'("version": ")[^"]+', r'\g<1>0.99.1', source))
        self.commit('bare bump')
        self.head = self.git('rev-parse', 'HEAD')
        self.h = module()
        self.pr = {'state': 'open', 'head': {'sha': self.head},
                   'base': {'sha': self.base, 'ref': 'main', 'repo': {'full_name': 'o/r'}},
                   'body': ''}
        self.checks = [{'id': i, 'name': name, 'status': 'completed', 'conclusion': 'success'}
                       for i, name in enumerate(['test', f'merged-result / {self.base} / {self.head}'])]

    def api(self, endpoint, *args):
        if endpoint == 'repos/o/r': return {'default_branch': 'main'}
        if endpoint.endswith('/pulls/12'): return self.pr
        if endpoint.startswith('repos/o/r/rules/branches/'): return []
        if endpoint.endswith('/branches/main'): return {'commit': {'sha': self.base}}
        if '/comments' in endpoint: return []
        if endpoint.endswith('/protection'): return PROTECTED
        if 'check-runs' in endpoint: return {'check_runs': self.checks}
        if '/status?' in endpoint: return {'statuses': []}
        self.fail(endpoint)

    def guard(self):
        out = io.StringIO()
        with patch.dict(sys.modules, {'hard_edges': self.h}), \
             patch.object(self.h, 'api', side_effect=self.api), \
             patch.object(self.h, 'settings_for', return_value={}), \
             patch.object(self.h, 'project_repo', return_value='o/r'), \
             patch.object(sys, 'argv', ['guard', 'merge', '--repo', 'o/r', '--pr', '12',
                                      '--project', str(self.repo)]), patch.object(sys, 'stdout', out):
            runpy.run_path(str(ROOT / 'scripts/guard'), run_name='__main__')
        return json.loads(out.getvalue())

    def test_bare_bump_cli_passes_green_ci_without_issue_lane_or_verdict(self):
        result = self.guard()
        self.assertEqual(result['merge'], 'pass')
        self.assertIsNone(result['verdict'])
        self.assertEqual(result['head'], self.head)

    def test_bare_bump_still_requires_green_merged_result(self):
        # Each refusal names the state it found: no checks, a required one absent, or a red one.
        for checks, diagnosis in (([], 'no CI checks reported'),
                                  (self.checks[:1], 'required CI checks unmet'),
                                  ([dict(c, conclusion='failure') for c in self.checks], 'CI not green'),
                                  ([dict(c, status='in_progress', conclusion=None) for c in self.checks],
                                   'CI not green')):
            with self.subTest(checks=checks):
                self.checks = checks
                stderr = io.StringIO()
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as error:
                    self.guard()
                self.assertEqual(error.exception.code, 2)
                self.assertIn(diagnosis, stderr.getvalue())

    def test_any_extra_change_requires_review(self):
        for change in ('extra path', 'one manifest', 'other field', 'mode', 'newline', 'mismatch', 'nested version'):
            with self.subTest(change=change):
                self.git('reset', '--hard', self.head)
                plugin = self.repo / self.paths[0]
                if change == 'extra path': (self.repo / 'extra').write_text('not a bump\n')
                elif change == 'one manifest':
                    self.git('checkout', self.base, '--', self.paths[0])
                elif change == 'other field': plugin.write_text(plugin.read_text().replace('devstandard', 'other'))
                elif change == 'mode': plugin.chmod(0o755)
                elif change == 'newline': plugin.write_bytes(plugin.read_bytes().rstrip(b'\n'))
                elif change == 'mismatch': plugin.write_text(plugin.read_text().replace('0.99.1', '0.99.2'))
                else:
                    plugin.write_text(plugin.read_text().replace('"version": "0.99.1"',
                        '"nested": {"version": "0.99.1"}'))
                self.commit(change)
                self.pr['head']['sha'] = self.git('rev-parse', 'HEAD')
                stderr = io.StringIO()
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as error:
                    self.guard()
                self.assertEqual(error.exception.code, 2)
                self.assertIn('no whole Merge check 1 verdict', stderr.getvalue())

    def test_empty_diff_requires_review(self):
        self.pr['head']['sha'] = self.base
        stderr = io.StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit) as error:
            self.guard()
        self.assertEqual(error.exception.code, 2)
        self.assertIn('no whole Merge check 1 verdict', stderr.getvalue())


class MergeTest(AcceptanceTest):
    def test_merge_cli_sends_configured_method_and_history_message(self):
        base, head = 'b'*40, 'a'*40
        pr = {'state': 'open', 'title': 'fix: restore squash history (#232)',
              'head': {'sha': head, 'repo': {'full_name': 'o/r'}},
              'base': {'sha': base, 'ref': 'main', 'repo': {'full_name': 'o/r'}},
              'body': 'architecture-level: false'}
        trailers = ('Claude-Session: https://claude.ai/code/session_fixture\n'
                    'Co-Authored-By: Test Author <test@example.com>')
        message = ('fix: intermediate worker commit\n\nImplementation details.\n\n'
                   + trailers.replace('\nCo-', '\n\nCo-'))
        for settings, method in (({}, 'squash'), ({'merge_method': 'merge'}, 'merge'),
                                 ({'merge_method': 'rebase'}, 'rebase')):
            with self.subTest(settings=settings):
                h = module()
                writes = []
                def api(endpoint, *args):
                    if endpoint.endswith('/pulls/12/merge'):
                        writes.append((endpoint, args))
                        return {'merged': True}
                    if endpoint.endswith('/pulls/12'): return pr
                    if '/comments' in endpoint:
                        return [{'id': 1, 'body': self.verdict(), 'user': {'login': 'o'}}]
                    if endpoint.endswith('/branches/main'): return {'commit': {'sha': base}}
                    if endpoint == 'repos/o/r': return {'default_branch': 'main'}
                    self.fail(endpoint)
                def run(*args):
                    if args == ('git', '-C', str(ROOT), 'merge-base', '--is-ancestor', base, head):
                        return ''
                    if args == ('git', '-C', str(ROOT), 'log', '-1', '--format=%B', head):
                        return message
                    self.fail(args)
                argv = ['guard', 'merge', '--repo', 'o/r', '--pr', '12', '--project', str(ROOT)]
                with patch.dict(sys.modules, {'hard_edges': h}), \
                     patch.object(h, 'api', side_effect=api), patch.object(h, 'run', side_effect=run), \
                     patch.object(h, 'version_only', return_value=False), \
                     patch.object(h, 'settings_for', return_value=settings), \
             patch.object(h, 'project_repo', return_value='o/r'), \
                     patch.object(h, 'protection_check'), patch.object(h, 'commit_checks', return_value={}), \
                     patch('sys.stdout', new_callable=io.StringIO):
                    with patch.object(sys, 'argv', argv):
                        runpy.run_path(str(ROOT / 'scripts/guard'), run_name='__main__')
                    self.assertEqual(writes, [])
                    with patch.object(sys, 'argv', argv + ['--execute']):
                        runpy.run_path(str(ROOT / 'scripts/guard'), run_name='__main__')
                self.assertEqual(writes, [('repos/o/r/pulls/12/merge', (
                    '--method', 'PUT', '-f', 'sha=' + head,
                    '-f', 'merge_method=' + method,
                    '-f', 'commit_title=fix: restore squash history (#232) (#12)',
                    '-f', 'commit_message=' + trailers))])

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
             patch.object(h, 'version_only', return_value=False), \
             patch.object(h, 'settings_for', return_value={}), \
             patch.object(h, 'project_repo', return_value='o/r'), \
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
             patch.object(h,'version_only',return_value=False), \
             patch.object(h,'settings_for',return_value={}), patch.object(h,'project_repo',return_value='o/r'), patch.object(h,'protection_check'), \
             patch.object(h,'commit_checks',return_value={}), patch.object(h,'authorized',return_value=False):
            with self.assertRaisesRegex(h.Refusal,'human sign-off'):
                h.merge_check(Path('.'),'o/r',12)


class SeededProjectBootstrapTest(AcceptanceTest):
    """#293: a project seeded from the shipped pages founds itself and then merges."""

    def guard(self, argv, settings=None, checks=None):
        """Run the installed CLI; only the policy and protection reads are doubled."""
        h = module()
        seen = [] if checks is None else checks
        with patch.object(h, 'settings_for', return_value=settings or {}), \
             patch.object(h, 'project_repo', return_value='o/r'), \
             patch.object(h, 'protection_check',
                          side_effect=lambda repo, branch, names: seen.append(list(names))), \
             patch.dict(sys.modules, {'hard_edges': h}), \
             patch.object(sys, 'argv', ['guard'] + argv), \
             patch('sys.stdout', new_callable=io.StringIO):
            runpy.run_path(str(ROOT / 'scripts/guard'), run_name='__main__')
        return seen

    def test_protection_provisioning_takes_the_required_checks_from_policy(self):
        self.assertEqual(
            self.guard(['protection', '--repo', 'o/r', '--project', str(ROOT)],
                       {'required_checks': ['build', 'lint']}),
            [['build', 'lint']])

    def test_named_checks_override_the_policy_without_reading_it(self):
        h = module()
        seen = []
        with patch.object(h, 'settings_for', side_effect=AssertionError('policy read')), \
             patch.object(h, 'project_repo', side_effect=AssertionError('policy read')), \
             patch.object(h, 'protection_check', side_effect=lambda r, b, names: seen.append(list(names))), \
             patch.dict(sys.modules, {'hard_edges': h}), \
             patch.object(sys, 'argv', ['guard', 'protection', '--repo', 'o/r', '--check', 'ci']), \
             patch('sys.stdout', new_callable=io.StringIO):
            runpy.run_path(str(ROOT / 'scripts/guard'), run_name='__main__')
        self.assertEqual(seen, [['ci']])

    def merge_with(self, settings):
        """Run the real merge_check against a doubled PR, returning the checks it required."""
        h = module()
        base, head = 'b'*40, 'a'*40
        pr = {'state': 'open', 'head': {'sha': head, 'repo': {'full_name': 'o/r'}},
              'base': {'sha': base, 'ref': 'main', 'repo': {'full_name': 'o/r'}},
              'body': 'architecture-level: false'}
        def api(endpoint, *args):
            if endpoint.endswith('/pulls/12'): return pr
            if '/comments' in endpoint: return [{'id': 1, 'body': self.verdict(), 'user': {'login': 'o'}}]
            if endpoint.endswith('/branches/main'): return {'commit': {'sha': base}}
            if endpoint == 'repos/o/r': return {'default_branch': 'main'}
            self.fail(endpoint)
        with patch.object(h, 'api', side_effect=api), patch.object(h, 'run', return_value=''), \
             patch.object(h, 'version_only', return_value=False), \
             patch.object(h, 'settings_for', return_value=settings), \
             patch.object(h, 'project_repo', return_value='o/r'), \
             patch.object(h, 'protection_check') as protection, \
             patch.object(h, 'commit_checks', return_value={'ci': 'success'}) as ci:
            h.merge_check(Path('.'), 'o/r', 12)
        return list(ci.call_args.args[2]), list(protection.call_args.args[2])

    def test_merge_requires_the_merged_result_name_the_policy_states(self):
        base, head = 'b'*40, 'a'*40
        required, protection = self.merge_with(
            {'required_checks': ['ci'], 'merged_result_check': 'integration / {base} / {head}'})
        self.assertEqual(required, ['ci', f'integration / {base} / {head}'])
        self.assertEqual(protection, ['ci'])

    def test_policy_selected_checks_gate_the_real_merge_validation(self):
        """A green `test` cannot replace policy's lint check or its pinned integration job."""
        h = module()
        base, head = 'b'*40, 'a'*40
        identity = f'integration / {base} / {head}'
        settings = {'required_checks': ['build', 'lint'],
                    'merged_result_check': 'integration / {base} / {head}'}
        pr = {'state': 'open', 'head': {'sha': head},
              'base': {'sha': base, 'ref': 'main', 'repo': {'full_name': 'o/r'}},
              'body': 'architecture-level: false'}
        observed = ['build', 'lint', identity]
        def api(endpoint, *args):
            if endpoint == 'repos/o/r': return {'default_branch': 'main'}
            if endpoint.endswith('/pulls/12'): return pr
            if endpoint == 'repos/o/r/branches/main': return {'commit': {'sha': base}}
            if endpoint.endswith('/branches/main/protection'):
                return dict(PROTECTED, required_status_checks={'strict': True,
                                                              'contexts': ['build', 'lint']})
            if '/rules/branches/' in endpoint: return []
            if '/comments' in endpoint:
                return [{'id': 1, 'body': self.verdict(), 'user': {'login': 'o'}}]
            if '/check-runs?' in endpoint:
                return {'check_runs': [{'id': i, 'name': name, 'status': 'completed',
                                        'conclusion': 'success'} for i, name in enumerate(observed)]}
            if '/status?' in endpoint: return {'statuses': []}
            self.fail(endpoint)
        with patch.object(h, 'api', side_effect=api), patch.object(h, 'run', return_value=''), \
             patch.object(h, 'version_only', return_value=False), \
             patch.object(h, 'settings_for', return_value=settings), \
             patch.object(h, 'project_repo', return_value='o/r'):
            result = h.merge_check(Path('.'), 'o/r', 12)
            self.assertEqual(result['merge'], 'pass')
            self.assertEqual(result['checks'], {name: 'success' for name in observed})
            for missing in ('lint', identity):
                observed = [name for name in ('build', 'lint', identity) if name != missing] + ['test']
                with self.subTest(missing=missing), \
                     self.assertRaisesRegex(h.Refusal, 'required CI checks unmet'):
                    h.merge_check(Path('.'), 'o/r', 12)

    def test_the_default_merged_result_name_is_what_the_shipped_template_reports(self):
        base, head = 'b'*40, 'a'*40
        required, _ = self.merge_with({})
        self.assertEqual(required, ['test', f'merged-result / {base} / {head}'])

    def test_a_merged_result_name_unbound_to_either_pin_refuses(self):
        h = module()
        for template in ('merged-result', 'merged-result / {base}', 'merged-result / {head}', 7):
            with self.subTest(template=template), self.assertRaises(h.Refusal):
                h.merged_result_check({'merged_result_check': template}, 'b'*40, 'a'*40)

    def test_a_required_check_list_that_is_not_a_list_of_names_refuses(self):
        h = module()
        for value in ('test', [], [''], ['test', 3], {}):
            with self.subTest(value=value), self.assertRaises(h.Refusal):
                h.required_checks({'required_checks': value})

    # ---- the shipped templates produce what the guard requires ---------------

    def block(self, path, opener, contains):
        """The one fenced template on a page that carries `contains`; a page may ship several."""
        text = (ROOT / path).read_text()
        blocks = [b for b in re.findall(r'^```' + opener + r'\n(.*?)^```$', text, re.M | re.S)
                  if contains in b]
        self.assertEqual(len(blocks), 1, f'{path}: want one {opener} block carrying {contains!r}')
        return blocks[0]

    def test_the_shipped_ci_template_reports_the_default_merged_result_identity(self):
        template = self.block('reference/ci-pipelines.md', 'yaml', 'merged-result')
        name = module().MERGED_RESULT.replace(
            '{base}', '${{ github.event.pull_request.base.sha }}').replace(
            '{head}', '${{ github.event.pull_request.head.sha }}')
        self.assertIn(name, template)
        for line in ('fetch-depth: 2', "git rev-parse HEAD^1", "git rev-parse HEAD^2",
                     'needs: test'):
            self.assertIn(line, template, line)

    def test_the_shipped_policy_template_loads_as_valid_policy(self):
        path = ROOT / 'reference/devstandard-guards.json.template'
        self.assertTrue(path.is_file(), 'seeded setup needs a shipped policy template file')
        raw = path.read_text()
        filled = raw.replace('OWNER-LOGIN', 'octocat').replace('ISSUE-NUMBER', '7')
        h, settings = module(), json.loads(filled)
        self.assertFalse(h.standing_delegation(settings))
        self.assertEqual(h.required_checks(settings), ['test'])
        self.assertEqual(h.merged_result_check(settings, 'b'*40, 'a'*40),
                         'merged-result / ' + 'b'*40 + ' / ' + 'a'*40)
        self.assertEqual(settings['human_logins'], ['octocat'])
        self.assertEqual(settings['record_logins'], ['octocat'])
        self.assertEqual(settings['authorization_issue'], 7)


if __name__ == '__main__':
    unittest.main(verbosity=2)
