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
    'RoleRuleTest.test_every_refused_word_refuses_as_a_command_and_is_admitted_as_text',
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
        self.env = {k: v for k, v in os.environ.items() if k != 'DEVSTANDARD_ROLE'}
        self.env.update(GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1')
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
        for path in ('.claude-plugin/plugin.json', '.claude-plugin/marketplace.json', '.codex-plugin/plugin.json'):
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
                                          '.claude-plugin/plugin.json', '.codex-plugin/plugin.json', 'changed'])
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
                                          '.claude-plugin/plugin.json', '.codex-plugin/plugin.json', 'changed'])

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
        """Collected lockstep versions is still a regression when it lowers the version."""
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
                                          '.claude-plugin/plugin.json', '.codex-plugin/plugin.json', 'changed'])
        self.assertEqual(self.git('status', '--porcelain', '-uall'), '')

    def test_any_other_line_beside_the_version_lines_refuses(self):
        h = module()
        oldbase, oldhead, newbase = self.bump_lane()
        replay = self.git('rev-parse', 'HEAD')
        plugin = self.repo / '.claude-plugin/plugin.json'
        for change in ('manifest field', 'other path', 'one manifest', 'mode', 'deleted manifest',
                       'not in lockstep', 'stale Codex', 'Codex mismatch'):
            with self.subTest(change=change):
                self.git('reset', '--hard', replay)
                self.manifest('0.99.2')
                if change == 'manifest field':
                    plugin.write_text(plugin.read_text().replace('"name": "devstandard"', '"name": "other"'))
                elif change == 'other path':
                    (self.repo / 'changed').write_text('unreviewed\n')
                elif change == 'one manifest':
                    self.git('checkout', replay, '--', '.claude-plugin/marketplace.json')
                elif change == 'stale Codex':
                    self.git('checkout', replay, '--', '.codex-plugin/plugin.json')
                elif change == 'Codex mismatch':
                    codex = self.repo / '.codex-plugin/plugin.json'
                    codex.write_text(codex.read_text().replace('0.99.2', '0.99.4'))
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
        """The replay has synchronized versions, so only the exemption's own check refuses."""
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
            if endpoint == 'repos/o/r': return {'default_branch':'main', 'owner':{'login':'o'}}
            if endpoint.endswith('/pulls/12'): return pr
            if endpoint.endswith('/branches/main'): return {'commit':{'sha':self.newbase}}
            if '/comments' in endpoint: return [comment]
            if 'check-runs' in endpoint:
                return {'check_runs':[{'id':i,'name':name,'status':'completed','conclusion':'success'}
                                     for i,name in enumerate(['test', integration])]}
            if '/status?' in endpoint: return {'statuses':[]}
            self.fail(endpoint)
        with patch.object(h,'api',side_effect=api), patch.object(h,'project_repo',return_value='o/r'), patch.object(h,'protection_check'):
            result = h.merge_check(self.repo,'o/r',12,self.base,self.old)
            self.assertEqual(result['comparison']['comparison'],'pass')
            integration = 'merged-result / stale base / '+self.new
            with self.assertRaisesRegex(h.Refusal,'required CI checks unmet'):
                h.merge_check(self.repo,'o/r',12,self.base,self.old)
            with self.assertRaisesRegex(h.Refusal,'exact accepted head'):
                h.merge_check(self.repo,'o/r',12)


# ---------------------------------------------------------------------------
# The role hook's one rule (#323): the command's own text, a short word list per role.
# Every command below is decision input only; none of them run.
# ---------------------------------------------------------------------------

LANE = '/home/dev/project/.claude/worktrees/323-probe'

# The positions a word can occupy in a command, and whether that position is the command
# itself. A substitution body runs, and a composition around it runs, so those carry the
# refusal; a here-doc body and a quoted string are data the shell never runs, so since #351
# the scan removes them and the same witness is admitted there for every role.
POSITIONS = [
    ('bare', lambda command: command, True),
    ('substitution', lambda command: 'echo $(' + command + ')', True),
    ('cd composition', lambda command: 'cd ' + LANE + ' && ' + command, True),
    ('quoted', lambda command: "echo '" + command + "'", False),
    ('heredoc', lambda command: 'cat <<EOF\n' + command + '\nEOF', False),
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
        'git fetch --tags',
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
        'rmdir empty',
    ],
    'orchestrator': [
        '/plugin/scripts/guard merge --repo o/r --pr 1 --project .',
        'git push origin main',
        'git push -u origin HEAD:main',
        'git tag -a v0.43.0 -m x',
        'gh release create v0.43.0 --generate-notes',
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

# Writing a word rather than running it: the file content, records and searches every role
# writes daily. Each of these cost a lane or a round before #351, and each is admitted for
# every role — the words sit in a here-doc body, a quoted string, or a longer word.
TEXT_IS_NOT_A_COMMAND = [
    "cat > t.py <<'EOF'\nrelease = threading.Event()\nEOF",
    'git commit -m "merge the release notes"',
    'gh issue create --title x --body "$(cat <<\'EOF\'\nrun gh pr merge here\nEOF\n)"',
    'git branch --merged',
    'grep -n merged-result ci.yml',
    'git commit -m \'release: tag the merge\' && git status',
    'cat <<EOF > /tmp/plan.md\nrm -rf the old worktree, then merge\nEOF',
]

# The one page each role's refusal sends the caller to (#323).
REFUSAL_PAGE = {'worker': 'reference/worker.md',
                'reviewer': 'reference/code-review-prompt.md',
                'orchestrator': 'reference/orchestrator.md'}



_SHARED = []


def shared_module():
    """One import of the real implementation for the probes that only read it."""
    if not _SHARED:
        _SHARED.append(module())
    return _SHARED[0]


def role_hook(command, tool='Bash', field='command', *, role='orchestrator', cwd=None,
              process_role=None):
    """Run the real hook handler. There is nothing to configure and nothing to supply.

    `api` and `run` are doubled to raise on every call, so a GitHub read or a
    subprocess on the decision path fails the probe instead of answering it.
    """
    h = shared_module()
    event = {'tool_name': tool, 'tool_input': {field: command}, 'cwd': cwd or str(ROOT)}
    hook_env = {k: v for k, v in os.environ.items() if k != 'DEVSTANDARD_ROLE'}
    if process_role is not None:
        hook_env['DEVSTANDARD_ROLE'] = process_role
    out = io.StringIO()
    with patch.dict(os.environ, hook_env, clear=True), \
         patch.dict(sys.modules, {'hard_edges': h}), \
         patch.object(h, 'run', side_effect=AssertionError('the hook ran a subprocess')), \
         patch.object(h, 'api', side_effect=AssertionError('the hook read GitHub')), \
         patch.object(sys, 'argv', ['pre-tool-use', '--role', role]), \
         patch.object(sys, 'stdin', io.StringIO(json.dumps(event))), patch.object(sys, 'stdout', out):
        runpy.run_path(str(ROOT / 'hooks/pre-tool-use'), run_name='__main__')
    return json.loads(out.getvalue())


class RoleRuleTest(unittest.TestCase):
    """The whole hook contract: the command's own text, one word list per role, nothing else."""

    def deny(self, result, command):
        output = result.get('hookSpecificOutput', {})
        self.assertEqual(output.get('permissionDecision'), 'deny', command)
        return output['permissionDecisionReason']

    def test_every_refused_word_refuses_as_a_command_and_is_admitted_as_text(self):
        shard = parse_shard(os.environ.get('HARD_EDGE_SHARD'))
        refusals = admissions = seen = 0
        for role, rows in REFUSED.items():
            for word, witness in rows:
                for position, wrap, refused in POSITIONS:
                    candidate = wrap(witness)
                    for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
                        index = seen
                        seen += 1
                        if not selected_probe(index, shard):
                            continue
                        with self.subTest(role=role, word=word, position=position, tool=tool):
                            result = role_hook(candidate, tool, field, role=role)
                            if not refused:
                                self.assertEqual(result, {}, candidate)
                                admissions += 1
                                continue
                            reason = self.deny(result, candidate)
                            self.assertIn(role, reason)
                            # Every refusal is a reminder: the role's page and the way out.
                            self.assertIn(REFUSAL_PAGE[role], reason)
                            self.assertIn('re-spell', reason)
                            refusals += 1
        print(f'Role word-list sweep: {refusals} role/word/position/tool refusals, '
              f'{admissions} admitted where the word is only text')

    def test_ordinary_work_is_admitted_for_every_role(self):
        for role, commands in ADMITTED.items():
            for command in commands + TEXT_IS_NOT_A_COMMAND:
                for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
                    with self.subTest(role=role, command=command, tool=tool):
                        self.assertEqual(role_hook(command, tool, field, role=role), {})

    def test_unparseable_syntax_is_never_a_reason_to_refuse(self):
        """Every role: broken quoting decides on its words alone (#323)."""
        for command in ('git status "unterminated', "git status 'unterminated",
                        'git status \\', 'git status ${', 'git status $(', 'git status `',
                        'git status ;; --porcelain', 'git status |& cat',
                        # #351: an unterminated here-document removes what it can and is
                        # never itself the reason — its body is data either way.
                        'cat <<EOF', "cat <<'EOF'\nrm -rf /srv/x",
                        'cat <<-EOF\n\tgit merge main'):
            for role in ('worker', 'reviewer', 'orchestrator'):
                with self.subTest(command=command, role=role):
                    self.assertEqual(role_hook(command, role=role), {})

    def test_obfuscation_and_interpreters_are_outside_the_hook(self):
        """The accepted residual, stated as behaviour rather than left implied.

        #351 widens it by what the stripped positions imply: an interpreter given its script
        as a quoted argument or a here-document, and a word quoted as its own argument to the
        command that runs it. They are the same class as the `python3 -c` and base64 rows
        below — the command runs text the scan no longer reads, and writing it that way is a
        deliberate act, not the forgotten lane this hook exists to remind someone of. They
        are recorded here as behaviour rather than answered with a new rule.
        """
        for command in ('python3 -c \'import subprocess; subprocess.run(["git","pu"+"sh","origin","ma"+"in"])\'',
                        'bash /tmp/land-it.sh',
                        'echo Z2l0IHB1c2ggb3JpZ2luIG1haW4= | base64 -d | sh',
                        'sh -c "git merge main"',
                        'bash <<EOF\ngit merge main\nEOF',
                        'git "merge" main'):
            for role in ('worker', 'reviewer', 'orchestrator'):
                with self.subTest(command=command, role=role):
                    self.assertEqual(role_hook(command, role=role), {})
        # An option quoted the same way escapes the same way. The reviewer still refuses this
        # one on its own bare `push`, which is the shape of what survives: a word left
        # unquoted anywhere in the command is still read.
        self.assertEqual(role_hook('git push "--force" origin task/x', role='worker'), {})
        self.assertNotEqual(role_hook('git push "--force" origin task/x', role='reviewer'), {})

    def test_the_scan_reads_the_command_and_not_the_data_it_carries(self):
        """#351: a here-document body and a quoted string are removed before the word list.

        Removal is one-directional — the quote characters and the line structure stay, so
        nothing the scan removes can join two fragments into a word nobody wrote, and a
        word that survives was written outside the data.
        """
        h = module()
        for text, expected in (
                # The opener line keeps its own text; the body and its terminator go.
                ("cat > t.py <<'EOF'\nrelease = threading.Event()\nEOF",
                 'cat > t.py <<'),
                ('cat <<-EOF > out\n\trelease\n\tEOF\ndone',
                 'cat << > out\ndone'),
                ('git commit -m "merge it"', 'git commit -m ""'),
                ("echo 'merge' \"tag\"", "echo '' \"\""),
                # A substitution body is command text and is still read.
                ('echo $(git merge main)', 'echo $(git merge main)'),
                # What cannot be paired is read as written: an unbalanced quote and an
                # unterminated here-document remove what they can and no more.
                ('git status "unterminated', 'git status "unterminated'),
                ('cat <<EOF\nmerge', 'cat <<'),
                # A second here-document opened on the same line keeps its body: the pass
                # misses rather than over-removes, which is the direction that cannot
                # invent an admission the word list would refuse.
                ('cat <<EOF <<EOF2\nb1\nEOF\nmerge\nEOF2',
                 'cat << <<EOF2\nmerge\nEOF2'),
                # A here-string is not a here-document, and neither is a left shift.
                ("grep -f - <<<'merge' file\nmerge", "grep -f - <<<'' file\nmerge"),
                ('echo $((1 << 2)) && git merge main', 'echo $((1 << 2)) && git merge main')):
            with self.subTest(text=text):
                self.assertEqual(h.command_only(text), expected)
        # Removing text can only admit: a word split across a quote boundary is not made whole.
        self.assertEqual(h.command_only('me"x"rge'), 'me""rge')
        self.assertIsNone(h.tool_decision('worker', 'Bash', {'command': 'me"x"rge'}))
        # A word the data does not hide is still read, however broken the quoting around it.
        self.assertIsNotNone(h.tool_decision('worker', 'Bash',
                                             {'command': "echo 'git merge main"}))

    def test_the_refusal_reason_names_the_word_and_the_merge_entry(self):
        h = module()
        self.assertIn("'merge'", h.tool_decision('worker', 'Bash', {'command': 'git merge x'}))
        self.assertIn('scripts/guard merge', h.tool_decision(
            'orchestrator', 'Bash', {'command': 'gh pr merge 1'}))
        self.assertIn('scripts/guard merge', h.tool_decision(
            'orchestrator', 'Bash', {'command': 'git merge origin/main'}))
        self.assertIn('main', h.tool_decision(
            'worker', 'Bash', {'command': 'git push origin main'}))

    def test_every_refusal_is_a_reminder_not_a_wall(self):
        """Four parts: the word refused, what the role does instead, the page, the way out (#323)."""
        h = module()
        cases = {
            'worker': [('git merge origin/main', "'merge'"),
                       ('git push origin main', "'push'"),
                       ('rm -rf /srv/data', "'rm -r'"),
                       ('rm --recursive /srv/data', "'rm --recursive'"),
                       ('git worktree remove /srv/lane', "'worktree remove'")],
            'reviewer': [('git push origin task/x', "'push'"),
                         ('gh api repos/o/r/issues/1/comments -f body=x', "'-f'")],
            'orchestrator': [('gh pr merge 1 --squash', "'gh pr merge'"),
                             ('git merge origin/main', "'git merge'")],
        }
        instead = {'worker': 'pushes its own task branch',
                   'reviewer': 'returns a verdict and writes nothing',
                   'orchestrator': 'scripts/guard merge'}
        for role, rows in cases.items():
            for command, word in rows:
                with self.subTest(role=role, command=command):
                    reason = h.tool_decision(role, 'Bash', {'command': command})
                    self.assertIsNotNone(reason, command)
                    self.assertIn(role, reason)
                    self.assertIn(word, reason)
                    self.assertIn(instead[role], reason)
                    self.assertIn(REFUSAL_PAGE[role], reason)
                    self.assertIn('re-spell', reason)
                    self.assertIn('--body-file', reason)

    def test_a_word_is_never_read_through_a_hyphen_or_into_a_longer_word(self):
        """`--force-with-lease` is not `--force`, `git merge-base` is not `merge`, and
        since #351 `merged`, `--merged`, `--tags` and `rmdir` are not their listed words."""
        h = module()
        for command in ('git push --force-with-lease origin task/x',
                        'git push --force-if-includes origin task/x',
                        'git merge-base --is-ancestor HEAD origin/x',
                        'git merge-tree HEAD origin/x',
                        'git branch --merged',
                        'git log --merges --oneline',
                        'grep -n merged-result .github/workflows/ci.yml',
                        'git fetch --tags'):
            with self.subTest(command=command):
                self.assertIsNone(h.tool_decision('worker', 'Bash', {'command': command}))
        for command in ('rmdir empty', 'git branch --merged', 'ls /tmp/release-notes.md'):
            with self.subTest(command=command, role='reviewer'):
                self.assertIsNone(h.tool_decision('reviewer', 'Bash', {'command': command}))
        self.assertFalse(h.carries('git push --tags origin', 'tag'))
        self.assertFalse(h.carries('git branch --merged', 'merge'))
        self.assertFalse(h.carries('rmdir empty', 'rm'))
        self.assertFalse(h.carries('git push --force-with-lease origin x', '--force'))
        # An option and the value written onto it are one word to the shell, so the `gh`
        # write-flag rule keeps the older boundary rather than the whole-word one.
        self.assertFalse(h.carries('gh api repos/o/r -XPOST', '-X'))
        self.assertTrue(h.carries_flag('gh api repos/o/r -XPOST', '-X'))
        self.assertTrue(h.carries_flag('gh api repos/o/r --method=POST', '--method'))
        self.assertIsNotNone(h.tool_decision('reviewer', 'Bash',
                                             {'command': 'gh api repos/o/r -XPOST'}))

    def test_a_phrase_matches_only_where_its_words_stand_together(self):
        h = module()
        self.assertTrue(h.carries('git branch -D task/x', 'branch -D'))
        # Any whitespace stands between them, a newline included.
        self.assertTrue(h.carries('git branch\n-D x', 'branch -D'))
        self.assertFalse(h.carries('git branch -v -D task/x', 'branch -D'))
        self.assertFalse(h.carries('gh pr view 1 && git log --grep merge', 'gh pr merge'))

    def test_the_worker_push_rule_needs_the_default_branch_by_name(self):
        h = module()
        for command, refused in (('git push origin task/x', False),
                                 ('git push origin main', True),
                                 ('git push origin master', True),
                                 ('git push origin HEAD:main', True),
                                 ('git push origin refs/heads/main', True),
                                 ('git push origin main:main', True),
                                 # #351: a branch whose name merely begins with the default
                                 # branch's is its own branch, and pushing it is the lane's
                                 # ordinary work — the whole-word rule stopped reading it.
                                 ('git push origin task/mainline', False),
                                 ('git push origin task/main-line', False),
                                 ('git rebase origin/main', False)):
            with self.subTest(command=command):
                self.assertEqual(h.tool_decision('worker', 'Bash', {'command': command})
                                 is not None, refused)

    def test_the_default_branch_is_main_or_master_by_name(self):
        """#326: two names in the source, no declaration to read anywhere."""
        h = module()
        self.assertEqual(h.DEFAULT_BRANCHES, ('main', 'master'))
        # A target whose default branch is called something else is not covered by this rule,
        # and nothing the hook can read would tell it otherwise.
        self.assertIsNone(h.tool_decision('worker', 'Bash', {'command': 'git push origin trunk'}))

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
                                  ('rm -rf /var/tmp/x', False),
                                  # #351: this rule reads targets rather than words, so it is
                                  # the one place where removing a quoted string could turn an
                                  # admitted cleanup into a refusal. A quoted /tmp/ path still
                                  # names /tmp/, and a path named only inside data is not a
                                  # target of the command that runs.
                                  ("rm -rf '/tmp/x'", True),
                                  ('rm -rf "/tmp/x" "/tmp/y"', True),
                                  ('cat <<EOF > /tmp/note\nrm -rf /srv/x\nEOF\nrm -rf /tmp/x', True),
                                  ('rm -rf "/tmp/x" /srv/y', False),
                                  ('rm -rf "/srv/x"', False)):
            with self.subTest(command=command):
                self.assertEqual(h.tool_decision('worker', 'Bash', {'command': command})
                                 is None, admitted)

    def test_release_is_not_the_hooks_business(self):
        """#326: `core.md` says releasing is the human's call; no word list decides it."""
        h = module()
        for command in ('git tag -a v1 -m x', 'gh release create v1', 'git push origin --tags'):
            with self.subTest(command=command):
                self.assertIsNone(h.tool_decision('orchestrator', 'Bash', {'command': command}))
        # The lane roles keep their refusal on the two commands that make a release:
        # releasing is never a worker's or a reviewer's operation whoever authorized it.
        for command in ('git tag -a v1 -m x', 'gh release create v1'):
            for role in ('worker', 'reviewer'):
                with self.subTest(command=command, role=role):
                    self.assertIsNotNone(h.tool_decision(role, 'Bash', {'command': command}))
        # #351 narrows one spelling: `--tags` is not the word `tag`, so a worker's
        # `git push origin --tags` is now admitted by the word list. The reviewer's own
        # `push` still refuses it, GitHub's protection still governs what may land, and
        # `core.md` plus `reference/worker.md` still say a worker never pushes a release
        # tag. Recorded as behaviour under this hook's accepted residual, not answered
        # with a new word.
        self.assertIsNone(h.tool_decision('worker', 'Bash',
                                          {'command': 'git push origin --tags'}))
        self.assertIsNotNone(h.tool_decision('reviewer', 'Bash',
                                             {'command': 'git push origin --tags'}))

    def test_the_orchestrators_founding_push_is_admitted_with_no_carve_out(self):
        """#326: GitHub's branch protection refuses this once founding has set it."""
        h = module()
        for command in ('git push origin main', 'git push -u origin HEAD:main',
                        'git push origin HEAD:refs/heads/master'):
            with self.subTest(command=command):
                self.assertIsNone(h.tool_decision('orchestrator', 'Bash', {'command': command}))
        # The merge entry point is still the orchestrator's one refusal.
        self.assertIsNotNone(h.tool_decision('orchestrator', 'Bash',
                                             {'command': 'gh pr merge 1 --squash'}))

    def test_the_hook_judges_commands_and_never_tool_names(self):
        """#334: the per-role tool allowlists are gone; a tool name is never a refusal.

        Spawning a sub-agent is useful work — a role may delegate a piece of its own task
        below itself (#339) — and the allowlist that refused it was the
        enumerate-what-is-allowed shape ADR 0051 rejected for commands. What a role may
        reach is set outside the hook and only as a denial: the reviewer's `disallowedTools`,
        and the per-role Codex sandbox.
        """
        h = module()
        for tool in ('Agent', 'Task', 'spawn_agent', 'SendMessage', 'Read', 'Glob', 'Grep',
                     'Write', 'Edit', 'apply_patch', 'Skill', 'update_plan', 'view_image',
                     'mcp__github__create_issue', 'mcp__github__merge_pull_request',
                     'mcp__anything__release_delete_publish_send'):
            for role in ('worker', 'reviewer', 'orchestrator'):
                with self.subTest(tool=tool, role=role):
                    self.assertIsNone(h.tool_decision(role, tool, {}))
        # The three the done-check names, spelled out.
        self.assertIsNone(h.tool_decision('worker', 'Agent', {}))
        self.assertIsNone(h.tool_decision('worker', 'spawn_agent', {}))
        self.assertIsNone(h.tool_decision('orchestrator', 'SendMessage', {}))
        # A shell tool is still judged, by its command's own text and nothing else.
        self.assertIsNotNone(h.tool_decision('worker', 'Bash', {'command': 'git merge origin/main'}))
        self.assertIsNotNone(h.tool_decision('reviewer', 'exec_command',
                                             {'cmd': 'rm -rf /srv/data'}))
        for name in ('READ_TOOLS', 'WORKER_TOOLS', 'REVIEWER_TOOLS', 'tool_refusal'):
            with self.subTest(name=name):
                self.assertFalse(hasattr(h, name), f'{name} should be gone with the allowlist')

    def test_a_native_worker_or_reviewer_subagent_type_selects_its_own_role(self):
        h = module()
        for agent_type in ('worker', 'devstandard:worker', 'reviewer', 'devstandard:reviewer'):
            with self.subTest(agent_type=agent_type):
                out = io.StringIO()
                event = {'tool_name': 'Bash', 'tool_input': {'command': 'git merge origin/main'},
                         'cwd': str(ROOT), 'agent_type': agent_type}
                with patch.dict(sys.modules, {'hard_edges': h}), \
                     patch.object(sys, 'argv', ['pre-tool-use', '--role', 'orchestrator']), \
                     patch.object(sys, 'stdin', io.StringIO(json.dumps(event))), \
                     patch.object(sys, 'stdout', out):
                    runpy.run_path(str(ROOT / 'hooks/pre-tool-use'), run_name='__main__')
                reason = json.loads(out.getvalue())['hookSpecificOutput']['permissionDecisionReason']
                self.assertIn(agent_type.split(':')[-1], reason)

    def test_a_cli_role_marker_overrides_a_nominal_orchestrator_role(self):
        for process_role in ('worker', 'reviewer'):
            with self.subTest(process_role=process_role):
                command = 'git tag -l'
                reason = self.deny(role_hook(command, role='orchestrator',
                                             process_role=process_role), command)
                self.assertIn(process_role, reason)

    def test_generic_claude_children_keep_the_parent_role_but_codex_children_default_to_worker(self):
        # Removing the agent_type constraint would incorrectly bind Claude research children.
        for agent_type, denied in [('general-purpose', False), ('Explore', False),
                                   ('default', True), (None, True)]:
            with self.subTest(agent_type=agent_type):
                event = dict(tool_name='Bash', tool_input={'command': 'git tag -l'},
                             agent_id='native-child')
                if agent_type is not None:
                    event['agent_type'] = agent_type
                result = subprocess.run([sys.executable, str(ROOT / 'hooks/pre-tool-use'),
                                         '--role', 'orchestrator'], input=json.dumps(event),
                                        text=True, capture_output=True,
                                        env={k:v for k,v in os.environ.items() if k != 'DEVSTANDARD_ROLE'})
                self.assertEqual(result.returncode, 0, result.stderr)
                output = json.loads(result.stdout)
                self.assertEqual(bool(output), denied)
                if denied:
                    self.assertIn('worker', output['hookSpecificOutput']['permissionDecisionReason'])


class ZeroConfigurationTest(unittest.TestCase):
    """The hook decides with nothing to read: no policy, no repository, no network (#326)."""

    def setUp(self):
        self.h = module()
        tmp = self.enterContext(tempfile.TemporaryDirectory(prefix='zero-configuration-'))
        self.tmp = Path(tmp)
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith('GIT_') and
                    k not in ('DEVSTANDARD_ROLE', 'GH_REPO', 'GH_TOKEN', 'GITHUB_TOKEN')}
        self.env.update(GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1', LC_ALL='C',
                        GH_CONFIG_DIR=str(self.tmp / 'gh-config'),
                        PATH=str(self.tmp) + os.pathsep + os.environ['PATH'])
        # Every network call fails, in the vocabulary `gh` prints when it reaches no server.
        failing = self.tmp / 'gh'
        failing.write_text('#!' + sys.executable + '\nimport sys\n'
                           'sys.stderr.write("Post \\"https://api.github.com/graphql\\": EOF\\n")\n'
                           'sys.exit(1)\n')
        failing.chmod(0o755)

    def git(self, at, *args):
        result = subprocess.run(['git', '-C', str(at)] + list(args), env=self.env,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def repository(self):
        """A real clone with a real `origin/main` ref, so `cwd` is inside a repository."""
        upstream, project = self.tmp / 'upstream', self.tmp / 'project'
        upstream.mkdir()
        self.git(self.tmp, 'init', '-b', 'main', str(upstream))
        for key, value in (('user.email', 'p@example.invalid'), ('user.name', 'Probe')):
            self.git(upstream, 'config', key, value)
        (upstream / 'README.md').write_text('probe\n')
        self.git(upstream, 'add', 'README.md')
        self.git(upstream, 'commit', '-m', 'found')
        self.git(self.tmp, 'clone', '--quiet', str(upstream), str(project))
        return project

    def hook(self, cwd, command, role='worker', tool='Bash', field='command'):
        event = {'tool_name': tool, 'tool_input': {field: command}, 'cwd': str(cwd)}
        result = subprocess.run([str(ROOT / 'hooks/pre-tool-use'), '--role', role],
                                cwd=str(ROOT), env=self.env, input=json.dumps(event),
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    # The same decisions in three environments: a bare directory that is no repository at
    # all, a real repository, and both with every network call failing.
    DECISIONS = (
        ('worker', 'git status --porcelain', True),
        ('worker', 'git push --force-with-lease origin task/x', True),
        ('worker', 'git push origin task/x', True),
        ('worker', 'git push origin main', False),
        ('worker', 'git merge origin/main', False),
        ('worker', 'git tag -a v1 -m x', False),
        # The decision the whole issue is about, through the real hook process (#351).
        ('worker', "cat > /tmp/x.py <<'EOF'\nrelease = threading.Event()\nEOF", True),
        ('worker', 'git commit -m "merge the release notes"', True),
        ('reviewer', 'gh pr view 1 --json body', True),
        ('reviewer', 'gh api repos/o/r -X POST', False),
        ('orchestrator', 'gh issue view 1 --json title', True),
        ('orchestrator', 'git push origin main', True),
        ('orchestrator', 'git tag -a v1 -m x', True),
        ('orchestrator', 'gh release create v1', True),
        ('orchestrator', 'gh pr merge 1 --squash', False),
        ('orchestrator', 'git merge origin/main', False),
    )

    def decide(self, cwd):
        for role, command, admitted in self.DECISIONS:
            with self.subTest(cwd=str(cwd), role=role, command=command):
                result = self.hook(cwd, command, role)
                if admitted:
                    self.assertEqual(result, {})
                else:
                    output = result['hookSpecificOutput']
                    self.assertEqual(output['permissionDecision'], 'deny')
                    # A read that cannot happen can never be the reason, because there is none.
                    self.assertNotIn('EOF', output['permissionDecisionReason'])

    def test_the_hook_decides_in_a_bare_directory_with_no_repository_at_all(self):
        bare = self.tmp / 'bare'
        bare.mkdir()
        inside = subprocess.run(['git', '-C', str(bare), 'rev-parse', '--is-inside-work-tree'],
                                env=self.env, text=True, capture_output=True)
        self.assertNotEqual(inside.returncode, 0, 'the probe directory must be no repository')
        self.decide(bare)

    def test_the_hook_decides_inside_a_repository_with_the_network_failing(self):
        self.decide(self.repository())

    def test_a_cwd_that_does_not_exist_still_decides(self):
        self.decide(self.tmp / 'no-such-directory')

    def test_nothing_on_the_decision_path_reads_a_policy_a_file_or_the_network(self):
        """The done-check's grep, as an assertion (#326)."""
        source = (ROOT / 'scripts/hard_edges.py').read_text()
        hook = (ROOT / 'hooks/pre-tool-use').read_text()
        for name in ('settings_for', 'POLICY_PATH', 'devstandard-guards', 'policy_words',
                     'standing_delegation', 'standing_release', 'command_patterns',
                     'required_checks', 'record_logins', 'human_logins', 'authorization_issue',
                     'merged_result_check', 'codex_role_hook_trust_bypass', 'authorized',
                     'PolicyUnreadable', 'reading_policy', 'TRANSPORT_FAILURES', 'classify',
                     'shell_segments', 'unsupported_shell', 'worker_routine_command',
                     'unparsed_orchestrator_reason'):
            with self.subTest(name=name):
                self.assertNotIn(name, source, f'{name} should be gone with the policy (#326)')
                self.assertNotIn(name, hook, f'{name} should be gone with the policy (#326)')
        # The whole decision, from the role's words to the answer, reads only its arguments.
        for name in ('def command_only', 'def carries', 'def carries_flag',
                     'def command_refusal', 'def tool_decision'):
            body = source[source.index(name):]
            body = body[:body.index('\ndef ', 1)]
            with self.subTest(name=name):
                self.assertNotIn('api(', body)
                self.assertNotIn('run(', body)
                self.assertNotIn('open(', body)



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
        reason = json.loads(result.stdout)['hookSpecificOutput']['permissionDecisionReason']
        self.assertTrue(reason.startswith("worker role refuses a command carrying 'merge'"), reason)
        self.assertIn(REFUSAL_PAGE['worker'], reason)

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
    """#314, #326: every observed check green and at least one reported. No names anywhere."""

    def setUp(self):
        self.h = module()
        self.head = 'a' * 40

    def gate(self, observed):
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
            return self.h.default_ci('o/r')

    def refusal(self, observed):
        with self.assertRaises(self.h.Refusal) as error:
            self.gate(observed)
        message = str(error.exception)
        self.assertIn('default-branch CI refused dispatch', message)
        return message

    def test_a_head_whose_every_check_is_green_admits_a_lane(self):
        observed = {'tests': 'success', 'cycle-pr': 'success', 'notebook-english': 'skipped'}
        self.assertEqual(self.gate(observed),
                         {'branch': 'main', 'head': self.head, 'checks': observed})

    def test_a_head_whose_ci_job_is_not_called_test_admits_a_lane(self):
        """No project renames its CI job to satisfy this gate, because no name is required."""
        self.assertEqual(self.gate({'tests': 'success'})['checks'], {'tests': 'success'})

    def test_a_red_head_refuses_and_names_the_check_that_failed(self):
        message = self.refusal({'tests': 'success', 'cycle-pr': 'failure'})
        self.assertIn('CI not green', message)
        self.assertIn("'cycle-pr': 'failure'", message)

    def test_a_pending_head_refuses(self):
        self.assertIn('CI not green', self.refusal({'tests': 'success', 'cycle-pr': None}))

    def test_a_head_carrying_no_check_at_all_refuses(self):
        """Silence is not green: an unchecked default branch never admits a lane."""
        self.assertIn('no CI checks reported', self.refusal({}))



class VersionBumpTest(unittest.TestCase):
    git = RebaseTest.git
    commit = RebaseTest.commit

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='version-bump-test-')
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.env = {k: v for k, v in os.environ.items() if k != 'DEVSTANDARD_ROLE'}
        self.env.update(GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1')
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Probe')
        self.git('config', 'user.email', 'probe@example.invalid')
        self.paths = ['.claude-plugin/plugin.json', '.claude-plugin/marketplace.json', '.codex-plugin/plugin.json']
        for path in self.paths:
            (self.repo / path).parent.mkdir(exist_ok=True)
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
        if endpoint == 'repos/o/r': return {'default_branch': 'main', 'owner': {'login': 'o'}}
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
        for change in ('extra path', 'one manifest', 'other field', 'mode', 'newline', 'mismatch', 'nested version', 'stale Codex', 'Codex mismatch'):
            with self.subTest(change=change):
                self.git('reset', '--hard', self.head)
                plugin = self.repo / self.paths[0]
                if change == 'extra path': (self.repo / 'extra').write_text('not a bump\n')
                elif change == 'one manifest':
                    self.git('checkout', self.base, '--', self.paths[0])
                elif change == 'stale Codex':
                    self.git('checkout', self.base, '--', '.codex-plugin/plugin.json')
                elif change == 'Codex mismatch':
                    codex = self.repo / '.codex-plugin/plugin.json'
                    codex.write_text(codex.read_text().replace('0.99.1', '0.99.2'))
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
    """`guard merge` with nothing configured: its own GitHub reads decide (#326)."""

    BASE, HEAD = 'b' * 40, 'a' * 40
    TRAILERS = ('Claude-Session: https://claude.ai/code/session_fixture\n'
                'Co-Authored-By: Test Author <test@example.com>')
    MESSAGE = ('fix: intermediate worker commit\n\nImplementation details.\n\n'
               + TRAILERS.replace('\nCo-', '\n\nCo-'))

    def setUp(self):
        self.h = module()
        self.owner = 'octocat'
        self.integration = f'merged-result / {self.BASE} / {self.HEAD}'
        self.pr = {'state': 'open', 'title': 'fix: restore squash history (#232)',
                   'head': {'sha': self.HEAD, 'repo': {'full_name': 'o/r'}},
                   'base': {'sha': self.BASE, 'ref': 'main', 'repo': {'full_name': 'o/r'}},
                   'body': 'architecture-level: false'}
        self.comments = [{'id': 1, 'body': self.verdict(), 'user': {'login': self.owner}}]
        self.observed = {'test': 'success', self.integration: 'success'}
        self.writes = []
        self.protection = []

    def check_runs(self):
        rows = []
        for index, (name, state) in enumerate(self.observed.items()):
            completed = state is not None
            rows.append({'id': index, 'name': name,
                         'status': 'completed' if completed else 'in_progress',
                         'conclusion': state})
        return {'check_runs': rows}

    def api(self, endpoint, *args):
        if endpoint == 'repos/o/r':
            return {'default_branch': 'main', 'owner': {'login': self.owner}}
        if endpoint.endswith('/pulls/12/merge'):
            self.writes.append((endpoint, args))
            return {'merged': True}
        if endpoint.endswith('/pulls/12'): return self.pr
        if endpoint == 'repos/o/r/branches/main': return {'commit': {'sha': self.BASE}}
        if '/comments' in endpoint: return list(self.comments)
        if '/check-runs?' in endpoint: return self.check_runs()
        if '/status?' in endpoint: return {'statuses': []}
        self.fail(endpoint)

    def run_git(self, *args):
        if args[3:] == ('merge-base', '--is-ancestor', self.BASE, self.pr['head']['sha']):
            return ''
        if args[3:] == ('log', '-1', '--format=%B', self.pr['head']['sha']):
            return self.MESSAGE
        self.fail(args)

    def guard(self, *extra):
        """Run the installed CLI; only GitHub, the protection read and local git are doubled."""
        out, err = io.StringIO(), io.StringIO()
        argv = ['guard', 'merge', '--repo', 'o/r', '--pr', '12', '--project', str(ROOT)]
        code = 0
        with patch.dict(sys.modules, {'hard_edges': self.h}), \
             patch.object(self.h, 'api', side_effect=self.api), \
             patch.object(self.h, 'run', side_effect=self.run_git), \
             patch.object(self.h, 'version_only', return_value=False), \
             patch.object(self.h, 'project_repo', return_value='o/r'), \
             patch.object(self.h, 'protection_check',
                          side_effect=lambda *a: self.protection.append(a)), \
             patch.object(sys, 'argv', argv + list(extra)), \
             patch.object(sys, 'stdout', out), redirect_stderr(err):
            try:
                runpy.run_path(str(ROOT / 'scripts/guard'), run_name='__main__')
            except SystemExit as exit:
                code = exit.code
        return code, out.getvalue(), err.getvalue()

    def refused(self, *extra):
        code, _, err = self.guard(*extra)
        self.assertEqual(code, 2, err)
        self.assertEqual(self.writes, [], 'a refused merge must write nothing')
        return err

    # ---- the four cases the done-check names ---------------------------------

    def test_a_head_without_a_whole_verdict_on_the_pr_refuses(self):
        for name, comments in (('no comment at all', []),
                               ('a note that is not a verdict',
                                [{'id': 1, 'body': 'looks good to me', 'user': {'login': 'octocat'}}]),
                               ('a verdict published by another account',
                                [{'id': 1, 'body': self.verdict(), 'user': {'login': 'someone-else'}}])):
            with self.subTest(comments=name):
                self.comments = comments
                self.assertIn('no whole Merge check 1 verdict', self.refused())

    def test_a_red_or_pending_observed_check_refuses(self):
        for name, state in (('red', 'failure'), ('pending', None), ('cancelled', 'cancelled')):
            with self.subTest(check=name):
                self.observed = {'test': 'success', self.integration: 'success', 'lint': state}
                self.assertIn('CI not green', self.refused())
        # The integration check is required by name, so its absence is not merely silence.
        self.observed = {'test': 'success'}
        self.assertIn('required CI checks unmet', self.refused())
        self.observed = {}
        self.assertIn('no CI checks reported', self.refused())

    def test_an_architecture_level_pr_without_an_owner_comment_refuses(self):
        self.pr['body'] = 'architecture-level: true'
        # The verdict is published under the owner's account; it is not the sign-off.
        self.assertIn('sign-off comment on this PR', self.refused())
        self.comments = self.comments + [
            {'id': 2, 'body': 'Approved.', 'user': {'login': 'someone-else'}}]
        self.assertIn('sign-off comment on this PR', self.refused())
        # A dispatcher or review record under the owner's account is not the sign-off either.
        self.comments = self.comments[:1] + [
            {'id': 3, 'body': '<!-- devstandard-dispatch-v1 -->\n```json\n{}\n```\n',
             'user': {'login': self.owner}}]
        self.assertIn('sign-off comment on this PR', self.refused())
        # The human's own comment on the PR is.
        self.comments = self.comments[:1] + [
            {'id': 4, 'body': 'Architecture-level: approved.', 'user': {'login': self.owner}}]
        code, out, err = self.guard('--execute')
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)['merge'], 'pass')
        self.assertEqual(len(self.writes), 1)

    def test_a_verified_head_merges_with_squash(self):
        code, out, err = self.guard()
        self.assertEqual(code, 0, err)
        result = json.loads(out)
        self.assertEqual(result['merge'], 'pass')
        self.assertEqual(result['head'], self.HEAD)
        self.assertEqual(result['checks'], self.observed)
        self.assertEqual(self.writes, [], 'a read-only check must not merge')
        # Protection is still verified, with no list of contexts to configure.
        self.assertEqual(self.protection, [('o/r', 'main')])
        code, out, err = self.guard('--execute')
        self.assertEqual(code, 0, err)
        self.assertEqual(self.writes, [('repos/o/r/pulls/12/merge', (
            '--method', 'PUT', '-f', 'sha=' + self.HEAD,
            '-f', 'merge_method=squash',
            '-f', 'commit_title=fix: restore squash history (#232) (#12)',
            '-f', 'commit_message=' + self.TRAILERS))])

    # ---- the reads the guard keeps -------------------------------------------

    def test_a_moved_base_refuses(self):
        self.pr['base']['sha'] = 'c' * 40
        self.assertIn('base', self.refused())

    def test_the_integration_check_is_pinned_to_this_exact_base_and_head(self):
        self.assertEqual(self.h.merged_result(self.BASE, self.HEAD), self.integration)
        self.observed = {'test': 'success', f'merged-result / {"c"*40} / {self.HEAD}': 'success'}
        self.assertIn('required CI checks unmet', self.refused())



class ProtectionCliTest(unittest.TestCase):
    """#326: `guard protection` takes its check names from the command line and nowhere else."""

    def guard(self, *argv):
        h = module()
        seen, out, err = [], io.StringIO(), io.StringIO()
        code = 0
        with patch.object(h, 'project_repo', side_effect=AssertionError('read a policy')), \
             patch.object(h, 'protection_check',
                          side_effect=lambda repo, branch, names=(): seen.append(list(names))), \
             patch.dict(sys.modules, {'hard_edges': h}), \
             patch.object(sys, 'argv', ['guard'] + list(argv)), \
             patch.object(sys, 'stdout', out), redirect_stderr(err):
            try:
                runpy.run_path(str(ROOT / 'scripts/guard'), run_name='__main__')
            except SystemExit as exit:
                code = exit.code
        return code, seen, err.getvalue()

    def test_named_checks_come_from_argv_with_no_project_read(self):
        code, seen, err = self.guard('protection', '--repo', 'o/r', '--check', 'ci')
        self.assertEqual((code, seen), (0, [['ci']]), err)
        code, seen, err = self.guard('protection', '--repo', 'o/r',
                                     '--check', 'build', '--check', 'lint')
        self.assertEqual((code, seen), (0, [['build', 'lint']]), err)

    def test_the_read_only_check_needs_no_names_at_all(self):
        """Protection's shape — strict, admins, no force push, no queue — needs no context."""
        code, seen, err = self.guard('protection', '--repo', 'o/r')
        self.assertEqual((code, seen), (0, [[]]), err)

    def test_apply_refuses_with_no_name_rather_than_stripping_every_required_check(self):
        code, seen, err = self.guard('protection', '--repo', 'o/r', '--apply')
        self.assertEqual(code, 2)
        self.assertEqual(seen, [], 'nothing may be read back from a refused apply')
        self.assertIn('--check', err)

    def test_apply_puts_the_names_from_argv(self):
        payloads = []
        h = module()
        result = subprocess.CompletedProcess([], 0, '', '')
        with patch.object(h, 'project_repo', side_effect=AssertionError('read a policy')), \
             patch.object(h, 'protection_check', side_effect=lambda repo, branch, names=(): {}), \
             patch('subprocess.run',
                   side_effect=lambda *a, **kw: payloads.append((a[0], kw.get('input'))) or result), \
             patch.dict(sys.modules, {'hard_edges': h}), \
             patch.object(sys, 'argv', ['guard', 'protection', '--repo', 'o/r', '--apply',
                                        '--check', 'test']), \
             patch('sys.stdout', new_callable=io.StringIO):
            runpy.run_path(str(ROOT / 'scripts/guard'), run_name='__main__')
        self.assertEqual(len(payloads), 1)
        command, body = payloads[0]
        self.assertEqual(command[:4], ['gh', 'api', '--method', 'PUT'])
        self.assertEqual(json.loads(body)['required_status_checks'],
                         {'strict': True, 'contexts': ['test']})


class ShippedTemplateTest(unittest.TestCase):
    """The shipped CI template produces the integration check the guard requires."""

    def block(self, path, opener, contains):
        """The one fenced template on a page that carries `contains`; a page may ship several."""
        text = (ROOT / path).read_text()
        blocks = [b for b in re.findall(r'^```' + opener + r'\n(.*?)^```$', text, re.M | re.S)
                  if contains in b]
        self.assertEqual(len(blocks), 1, f'{path}: want one {opener} block carrying {contains!r}')
        return blocks[0]

    def test_the_shipped_ci_template_reports_the_merged_result_identity(self):
        template = self.block('reference/ci-pipelines.md', 'yaml', 'merged-result')
        name = module().MERGED_RESULT.replace(
            '{base}', '${{ github.event.pull_request.base.sha }}').replace(
            '{head}', '${{ github.event.pull_request.head.sha }}')
        self.assertIn(name, template)
        for line in ('fetch-depth: 2', "git rev-parse HEAD^1", "git rev-parse HEAD^2",
                     'needs: test'):
            self.assertIn(line, template, line)

    def test_founding_seeds_no_configuration_file(self):
        """#326: the setup sequence has nothing to fill in and no template to copy."""
        self.assertFalse((ROOT / 'reference/devstandard-guards.json.template').exists())
        self.assertFalse((ROOT / '.github/devstandard-guards.json').exists())
        for page in ('reference/prd.md', 'reference/hard-edges.md', 'reference/ci-pipelines.md',
                     'README.md'):
            with self.subTest(page=page):
                self.assertNotIn('devstandard-guards', (ROOT / page).read_text())



if __name__ == '__main__':
    unittest.main(verbosity=2)
