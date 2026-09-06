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
from unittest.mock import patch

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
    'RoleTokenTest.test_all_operation_tokens_refuse_regardless_of_position',
    'ShellCompositionTest.test_adversarial_sweep_every_configured_operation_across_every_family',
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
            unittest.defaultTestLoader.loadTestsFromTestCase(RoleTokenTest),
            unittest.defaultTestLoader.loadTestsFromTestCase(ShellCompositionTest),
            unittest.defaultTestLoader.loadTestsFromTestCase(ProtectionTest),
        ])
        all_ids = {test.id() for test in iter_tests(tests)}
        with patch.dict(os.environ, HARD_EDGE_SHARD='0/8'):
            sweep_ids = {test.id() for test in load_tests(None, tests, None)}
        with patch.dict(os.environ, HARD_EDGE_SHARD='rest'):
            rest_ids = {test.id() for test in load_tests(None, tests, None)}
        self.assertEqual(len(sweep_ids), 2)
        self.assertEqual(sweep_ids & rest_ids, set())
        self.assertEqual(sweep_ids | rest_ids, all_ids)


def module():
    path = ROOT / 'scripts/hard_edges.py'
    assert path.exists(), 'hard-edge implementation is missing'
    spec = importlib.util.spec_from_file_location('hard_edges', path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@contextmanager
def remote_policy_project(policy):
    """Disposable project and gh boundary for executable-hook tests; no live credentials."""
    import base64
    with tempfile.TemporaryDirectory(prefix='policy-hook-') as tmp:
        project = Path(tmp)
        # An unmerged local policy must not replace the remote extension.
        (project / '.github').mkdir()
        (project / '.github/devstandard-guards.json').write_text('{}')
        responses = {
            'repos/o/r': {'default_branch': 'trunk'},
            'repos/o/r/branches/trunk': {'commit': {'sha': 'b'*40}},
            'repos/o/r/git/trees/' + 'b'*40 + '?recursive=1': {
                'tree': [{'path': '.github/devstandard-guards.json', 'sha': 'c'*40}],
                'truncated': False},
            'repos/o/r/git/blobs/' + 'c'*40: {'content': base64.b64encode(
                json.dumps(policy).encode()).decode()},
        }
        (project / 'responses.json').write_text(json.dumps(responses))
        gh = project / 'gh'
        gh.write_text('#!' + sys.executable + '\n'
            'import json, sys\nfrom pathlib import Path\n'
            'if sys.argv[1:3] == ["repo", "view"]: print("o/r")\n'
            'elif sys.argv[1] == "api": print(json.dumps(json.loads('
            'Path(__file__).with_name("responses.json").read_text())[sys.argv[2]]))\n'
            'else: sys.exit(1)\n')
        gh.chmod(0o755)
        env = dict(os.environ, PATH=tmp + os.pathsep + os.environ['PATH'])
        yield project, env


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

# Rows whose metacharacter sits in the argument position recognition consumes — a push
# refspec, a delete target — carry quoting itself into both sweeps: masking a quoted
# literal must not stop the value being read as the operation it names.
DANGEROUS_OPERATIONS = {
    'merge': ['gh pr merge 0 --squash', 'scripts/guard merge --pr 0'],
    'release': ['git tag v0.1.2', 'git push origin --tags', 'git push origin --follow-tags',
                'git push origin refs/tags/probe', 'git push origin v0.1.2',
                "git push origin 'refs/tags/*:refs/tags/*'",
                'gh release create v0.1.2', 'gh release upload v0.1.2 artifact',
                'gh release edit v0.1.2',
                'npm publish', 'pnpm publish', 'yarn publish', 'twine upload artifact'],
    'irreversible': ['rm -rf /probe', "rm -rf '/probe/*'", 'git push --force origin main',
                     "git push origin 'refs/heads/*:refs/heads/*'",
                     'git push -f origin main', 'git push origin --delete main',
                     'git push origin :refs/heads/main', 'git push origin main',
                     'gh repo delete o/r', 'gh api -X DELETE repos/o/r',
                     'gh api -X PUT repos/o/r', 'gh api -X PATCH repos/o/r',
                     'gh api -X POST repos/o/r', 'gh api repos/o/r -f name=value',
                     'scripts/guard protection --apply', 'terraform destroy',
                     'kubectl delete pod probe', 'aws s3api delete-bucket --bucket probe'],
}


# Tool help/manual synonyms; independent of the production regex table.
# Each row also joins both adversarial sweeps below.
DEFAULT_BRANCH_REFS = (
    'trunk', 'refs/heads/trunk', 'heads/trunk',
    ':trunk', ':refs/heads/trunk', ':heads/trunk',
    'HEAD:trunk', 'HEAD:refs/heads/trunk', 'HEAD:heads/trunk',
)
OPERATION_SYNONYMS = [
    ('rm', 'irreversible', ['rm ' + flag + ' /probe' for flag in
        ('-r', '-R', '--recursive', '-f', '--force', '-rf', '-fr', '-Rf', '-fR',
         '-rfv', '-vrf', '-vRf', '-ifR', '-RIv', '-vrrf')]),
    ('git push force/delete', 'irreversible', ['git push origin ' + suffix for suffix in
        ('--force task/probe', '-f task/probe', '-vf task/probe', '-fv task/probe',
         '--force-with-lease main', '--force-with-lease=refs/heads/main main',
         '--force-with-lease=refs/heads/main:abc main',
         '--force-if-includes main', '--mirror', '--delete task/probe',
         '-d task/probe', '-vd task/probe', '-dv task/probe',
         '+HEAD:refs/heads/task/probe', ':refs/heads/task/probe',
         '--all', '--branches', '--prune', ':', 'main', 'HEAD:main', 'HEAD:refs/heads/main')]),
    ('git push default destinations', 'irreversible', [
        'git push origin ' + flag + ref
        for flag in ('', '--force-with-lease ', '--force-if-includes ')
        for ref in DEFAULT_BRANCH_REFS]),
    ('git branch', 'irreversible', ['git branch ' + flags + ' task/probe' for flags in
        ('-D', '-vD', '-Dv', '--delete --force', '--force --delete', '-d -f',
         '-df', '-fd', '-vdf', '-dfv', '--delete -f', '-d --force')]),
    ('git tag delete', 'irreversible', ['git tag ' + flag + ' probe' for flag in
        ('-d', '--delete', '-nd', '-dn')]),
    ('git update-ref', 'irreversible', ['git update-ref ' + flag + ' refs/heads/task/probe'
        for flag in ('-d', '-zd', '-dz')]),
    ('terraform destroy', 'irreversible', ['terraform destroy', 'terraform apply -destroy']),
    ('gh release delete', 'irreversible', ['gh release delete probe',
        'gh release delete probe --cleanup-tag', 'gh release delete probe -y']),
    ('gh repo delete', 'irreversible', ['gh repo delete o/r', 'gh repo delete o/r --yes']),
    ('gh api write', 'irreversible', ['gh api repos/o/r ' + flags for flags in
        ('-X DELETE', '-XDELETE', '--method DELETE', '--method=DELETE',
         '-iXDELETE', '-iX DELETE', '-X PUT', '--method=PUT', '-X PATCH',
         '--method=PATCH', '-X POST', '--method=POST', '-f name=value', '-fname=value',
         '-F name=value', '-Fname=value', '-ifname=value', '-iFname=value',
         '--raw-field name=value', '--raw-field=name=value', '--field name=value',
         '--field=name=value', '--input probe.json', '--input=probe.json')]),
]
for _, kind, commands in OPERATION_SYNONYMS:
    DANGEROUS_OPERATIONS[kind].extend(commands)


GLOBAL_OPTIONS = {
    'git': ('--no-pager', '-c user.name=Probe', '-cuser.name=Probe', '-C /probe',
            '-C/probe', '--git-dir /probe', '--git-dir=/probe', '--work-tree /probe',
            '--work-tree=/probe', '-p', '--paginate', '-P', '--no-optional-locks',
            '--no-pager -cuser.name=Probe -C /probe', '-pP'),
    'gh': ('-R owner/repo', '-Rowner/repo', '--repo owner/repo', '--repo=owner/repo',
           '--hostname github.com', '--hostname=github.com', '--help', '--version',
           '-Rowner/repo --help', '-hv', '-Rowner/repo -hv'),
}


def orchestrator_hook(command, tool='Bash', field='command', *, settings=None, rows=None, role='orchestrator'):
    """Exercise the real handler/authorization; double only remote policy and head reads."""
    h = module()
    if settings is None:
        settings = json.loads((ROOT / '.github/devstandard-guards.json').read_text())
        # The committed standing release delegation (#227) deliberately admits the orchestrator's
        # routine release commands, so refusal probes run without it; the delegation itself is
        # exercised by the tests that construct a standing_release setting explicitly.
        settings['standing_release'] = None
    event = {'tool_name': tool, 'tool_input': {field: command}, 'cwd': str(ROOT)}
    out = io.StringIO()
    with patch.dict(sys.modules, {'hard_edges': h}), \
         patch.object(h, 'settings_for', return_value=('LeonJoeeee/devstandard', settings)), \
         patch.object(h, 'run', return_value='a'*40), \
         patch.object(h, 'api', return_value=rows or []) as api, \
         patch.object(sys, 'argv', ['pre-tool-use', '--role', role]), \
         patch.object(sys, 'stdin', io.StringIO(json.dumps(event))), patch.object(sys, 'stdout', out):
        runpy.run_path(str(ROOT / 'hooks/pre-tool-use'), run_name='__main__')
    return json.loads(out.getvalue()), api.call_count


class RoleTokenTest(unittest.TestCase):
    def test_documented_synonyms_reach_real_hook_and_authorization(self):
        import hashlib
        settings = {'authorization_issue': 204, 'human_logins': ['human'],
                    '_default_branch': 'trunk'}
        for family, kind, commands in OPERATION_SYNONYMS:
            for command in commands:
                record = {'repo': 'LeonJoeeee/devstandard', 'head': 'a'*40, 'kind': kind,
                          'command_sha256': hashlib.sha256(command.encode()).hexdigest(),
                          'expires': '2099-01-01T00:00:00+00:00'}
                rows = [{'user': {'login': 'human'}, 'body':
                         '<!-- devstandard-authorization-v1 -->\n' + json.dumps(record)}]
                for role in ('worker', 'reviewer', 'orchestrator'):
                    for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
                        with self.subTest(family=family, command=command, role=role, tool=tool):
                            result, queries = orchestrator_hook(command, tool, field,
                                settings=settings, role=role)
                            output = result.get('hookSpecificOutput', {})
                            self.assertEqual(output.get('permissionDecision'), 'deny')
                            self.assertIn(kind, output['permissionDecisionReason'])
                            self.assertEqual(queries, int(role == 'orchestrator'))
                            result, _ = orchestrator_hook(command, tool, field,
                                settings=settings, rows=rows, role=role)
                            if role == 'orchestrator':
                                self.assertEqual(result, {})
                            else:
                                self.assertEqual(result['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_rm_short_clusters_expand_at_any_position(self):
        from itertools import product
        h = module()
        for length in range(1, 5):
            for flags in product('rRfv', repeat=length):
                if not set(flags) & set('rRf'):
                    continue
                command = 'rm -' + ''.join(flags) + ' /probe'
                with self.subTest(command=command):
                    self.assertEqual(h.classify(command, {}), 'irreversible')

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
                        result, _ = orchestrator_hook(command, tool, field, role=role)
                        self.assertEqual(result.get('hookSpecificOutput', {}).get('permissionDecision'), 'deny')

    def test_all_operation_tokens_refuse_regardless_of_position(self):
        h = module()
        settings = json.loads((ROOT / '.github/devstandard-guards.json').read_text())
        settings.update(_default_branch='trunk', standing_release=None)
        probes = 0
        seen = 0
        shard = parse_shard(os.environ.get('HARD_EDGE_SHARD'))
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
                            index = seen
                            seen += 1
                            if not selected_probe(index, shard):
                                continue
                            with self.subTest(command=candidate, role=role, tool=tool):
                                self.assertIsNotNone(h.tool_decision(role, tool, {field: candidate}, settings))
                                result, _ = orchestrator_hook(candidate, tool, field, role=role,
                                                              settings=settings)
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
        for command in ('git push origin HEAD:refs/heads/task/12',
                        'git --no-pager push origin task/12',
                        'gh issue comment 12 --body "gh pr merge 12"',
                        'git status; cat tag', 'cat git; cat tag',
                        'gh pr > merge view 0', 'git status -- tagged'):
            for role in ('worker', 'orchestrator'):
                with self.subTest(command=command, role=role):
                    self.assertIsNone(h.tool_decision(role, 'Bash', {'command': command}, {}))
        self.assertIn('scripts/guard merge', h.tool_decision('orchestrator', 'Bash',
                                                           {'command': 'git diff -- gh merge pr'}, {}))


class RoleRoutineWorkTest(unittest.TestCase):
    """Real hook decisions with the committed policy; command text is never executed."""
    def decisions(self, role, commands, allowed, settings=None):
        for command in commands:
            for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
                with self.subTest(role=role, command=command, tool=tool):
                    result, _ = orchestrator_hook(command, tool, field, role=role, settings=settings)
                    if allowed:
                        self.assertEqual(result, {})
                    else:
                        self.assertEqual(result.get('hookSpecificOutput', {}).get('permissionDecision'), 'deny')

    def test_worker_lease_pushes_to_explicit_task_destinations(self):
        commands = [
            'git push --force-with-lease origin task/x',
            'git push origin --force-with-lease task/x',
            'git push --force-with-lease=refs/heads/task/x origin HEAD:task/x',
            'git push --force-with-lease=refs/heads/task/x:abc origin HEAD:refs/heads/task/x',
            'git push --force-with-lease --force-if-includes origin task/x',
            'git push --force-if-includes origin task/x',
            'git push --force-with-lease origin HEAD:heads/task/x',
            'git push --force-if-includes origin heads/task/x',
        ]
        self.decisions('worker', commands, True)
        self.decisions('reviewer', commands, False)
        self.decisions('orchestrator', commands, False)

    def test_default_branch_destination_spellings_never_gain_worker_exception(self):
        for default in ('main', 'trunk', 'heads/trunk'):
            commands = ['git push origin ' + flag + ref.replace('trunk', default)
                        for flag in ('', '--force-with-lease ', '--force-if-includes ')
                        for ref in DEFAULT_BRANCH_REFS]
            self.decisions('worker', commands, False, {'_default_branch': default})

    def test_worker_push_exception_cannot_hide_other_operations(self):
        commands = [
            'git push --force-with-lease origin main',
            'git push --force-with-lease origin task/x HEAD:refs/heads/main',
            'git push --force origin task/x', 'git push -f origin task/x',
            'git push origin +HEAD:task/x',
            'git push --force-with-lease --force origin task/x',
            'git push --force-with-lease -vf origin task/x',
            'git push --force-with-lease origin +HEAD:task/x',
            'git push --force-with-lease --mirror origin task/x',
            'git push --force-with-lease --all origin',
            'git push --force-with-lease --delete origin task/x',
            'git push --force-with-lease origin :task/x',
            'git push --force-with-lease origin refs/tags/probe',
            'git push --force-with-lease origin', 'git push --force-with-lease',
            'git push --force-with-lease origin HEAD',
            'git push --force-with-lease origin task/x; rm -rf /srv/data',
            'git push --force-with-lease origin task/x > /srv/data',
        ]
        self.decisions('worker', commands, False)
        self.decisions('worker', ['git push --force-with-lease origin HEAD:trunk'], False,
                       {'_default_branch': 'trunk'})
        self.decisions('worker', ['git push --force-with-lease origin task/x'], False,
                       {'command_patterns': {'irreversible': [r'\bgit push\b']}})

    def test_worker_temp_cleanup_is_admitted_after_policy_recognition(self):
        commands = ['rm -rf /tmp/devstandard-x.abc',
                    '/bin/rm -Rf -- /tmp/devstandard-x.abc',
                    'rm --recursive --force /tmp/devstandard-x.abc /tmp/devstandard-y.abc']
        self.decisions('worker', commands, True)
        self.decisions('reviewer', commands, False)
        self.decisions('orchestrator', commands, False)
        h = module()
        policy = json.loads((ROOT / '.github/devstandard-guards.json').read_text())
        self.assertEqual(h.classify(commands[0], policy), 'irreversible')

    def test_worker_cleanup_rejects_outside_mixed_and_unresolved_targets(self):
        self.decisions('worker', [
            'rm -rf /srv/data', 'rm -r /srv/data',
            'rm -rf /tmp/devstandard-x.abc /srv/data',
            'rm -rf /tmp', 'rm -rf /tmp/', 'rm -rf /',
            'rm -rf /tmp/../srv/data', 'rm -rf /tmp-other/data',
            'rm -rf relative', 'rm -rf', 'rm -rf "$TMPDIR/devstandard-x.abc"',
            'rm -rf /tmp/devstandard-x.abc; rm -rf /srv/data',
            'rm -rf /tmp/devstandard-x.abc > /srv/data',
            'rm --unknown /tmp/devstandard-x.abc -rf',
            'cat rm -rf /tmp/devstandard-x.abc',
        ], False)
        with tempfile.TemporaryDirectory(prefix='routine-work-') as tmp:
            link = Path(tmp) / 'outside'
            link.symlink_to('/srv')
            self.decisions('worker', [f'rm -rf {link}/data'], False)
            with patch('tempfile.gettempdir', return_value=tmp):
                self.decisions('worker', [f'rm -rf {tmp}/scratch'], True)
                self.decisions('worker', [f'rm -rf {tmp}'], False)
        with patch('tempfile.gettempdir', return_value='/var/tmp/devstandard-custom'):
            self.decisions('worker', ['rm -rf /var/tmp/devstandard-custom/scratch'], True)
            self.decisions('worker', ['rm -rf /var/tmp/devstandard-custom'], False)

    def test_reviewer_github_reads(self):
        self.decisions('reviewer', [
            'gh pr view 1 --json body', 'gh issue view 236 --comments',
            'gh run view 1', 'gh pr checks 1',
            'gh api repos/o/r/issues/1/comments',
            'gh api --method GET repos/o/r/issues/1/comments --paginate',
            'gh api repos/o/r/issues/1/comments -XGET',
            'gh api repos/o/r/issues/1/comments --method=GET',
            'gh api repos/o/r/issues/1/comments -X GET --jq .body',
        ], True)

    def test_reviewer_github_writes_and_composition_stay_refused(self):
        self.decisions('reviewer', [
            'gh pr comment 1 --body x', 'gh issue edit 1 --title x',
            'gh pr merge 1', 'gh run cancel 1',
            'gh api repos/o/r/issues/1/comments -X POST',
            'gh api repos/o/r/issues/1/comments --method=HEAD',
            'gh api repos/o/r/issues/1/comments -XGET -XPOST',
            'gh api repos/o/r/issues/1/comments -f k=v',
            'gh api repos/o/r/issues/1/comments -Fk=v',
            'gh api repos/o/r/issues/1/comments --input data.json',
            'gh api repos/o/r/issues/1/comments -X GET --field k=v',
            'gh api repos/o/r/issues/1/comments --output /tmp/result',
            'gh api graphql',
            'gh pr view 1 --web',
            'gh pr view 1; gh pr comment 1 --body x',
            'gh pr view 1 > /tmp/result',
        ], False)

    def test_reviewer_find_admits_searches_and_refuses_its_action_language(self):
        """find joins the read surface as a search; its side-effecting primaries do not."""
        self.decisions('reviewer', [
            'find reference -type f', "find reference -name '*.md'",
            "find reference -name '*.md' -print", 'find reference -maxdepth 1 -ls',
        ], True)
        self.decisions('reviewer', [
            'find reference -delete', "find reference -name '*.md' -delete",
            "find reference -exec cat '{}' +", "find reference -execdir cat '{}' +",
            "find reference -ok cat '{}' +", "find reference -okdir cat '{}' +",
            'find reference -fprint /tmp/out', 'find reference -fprint0 /tmp/out',
            "find reference -fprintf /tmp/out '%p'", 'find reference -fls /tmp/out',
        ], False)


class QuotedShellTest(unittest.TestCase):
    """Quote handling through both real hook input formats; no command text executes."""
    def check(self, commands, reason=None, roles=('worker', 'reviewer', 'orchestrator')):
        for command in commands:
            for role in roles:
                for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
                    with self.subTest(command=command, role=role, tool=tool):
                        result, _ = orchestrator_hook(command, tool, field, role=role)
                        if reason is None:
                            self.assertEqual(result, {})
                        else:
                            output = result.get('hookSpecificOutput', {})
                            self.assertEqual(output.get('permissionDecision'), 'deny')
                            self.assertIn(reason, output['permissionDecisionReason'])

    def test_quoted_search_patterns_are_literal_arguments(self):
        self.check([
            "rg --files -g '*.md' reference", 'rg --files -g "*prd*" reference',
            "find reference -name '*.md'", 'find reference -name "*.md"',
            "rg -n '^##|^###' file", 'rg -n "^##|^###" file',
            "rg -n '[ab]?{2}~(x)' file", 'rg -n "[ab]?{2}~(x)" file',
            "rg --files -g '*'.md reference", 'rg --files -g "*"prd"*" reference',
            "rg -n 'a;b&c<d>e' file", 'rg -n "a;b&c<d>e" file',
            'rg -n "a\\\"|b" file',
            "gh pr view 1 --jq '.body | length'",
        ])

    def test_single_quoted_comment_body_keeps_reviewer_write_refusal(self):
        commands = ["gh issue comment 1 --body 'text with `code`, | and *'"]
        self.check(commands, roles=('worker', 'orchestrator'))
        self.check(commands, 'reviewer tool surface refuses non-read command', roles=('reviewer',))

    def test_single_quoted_substitution_text_is_literal(self):
        self.check([
            "git status '$suffix'", "git status '$(npm publish)'",
            "rg -n '${suffix}' file", "rg -n '`npm publish`' file",
        ])

    def test_unquoted_expansion_and_active_double_quoted_substitution_refuse(self):
        self.check([
            'rg --files -g *.md', "rg --files -g '*.md'* reference",
            'rg --files -g {a,b}.md', 'rg --files -g [ab].md',
            'rg --files -g ?.md', 'cat ~/file', '{ rg --files; }',
            'rg -n $(pwd) file', 'rg -n "$(pwd)" file',
            'rg -n $pattern file', 'rg -n "${pattern}" file',
            'rg -n `pwd` file', 'rg -n "`pwd`" file',
            'rg -n "\\`pwd\\`" file', 'rg -n "\\$pattern" file',
            "rg -n 'literal'`pwd` file", 'rg -n \\"$(pwd) file',
            'rg -n "literal"\\\'$(pwd) file', 'rg -n "literal"$pattern file',
            'rg --files\ncat file', "rg -n 'line\nbreak' file",
            'rg -n "line\nbreak" file', "rg -n '*.md file", 'rg -n "*.md file',
        ], 'shell syntax is unsupported')

    def test_quoted_arguments_do_not_hide_modelled_composition(self):
        benign = ["rg -n '^##|^###' file | cat", 'rg -n foo file | cat']
        self.check(benign, roles=('worker', 'orchestrator'))
        self.check(benign, 'reviewer tool surface refuses non-read command', roles=('reviewer',))
        self.check(["rg -n '^##|^###' file | npm publish",
                    "rg -n 'literal' file; npm publish"], 'release')
        self.check(["rg -n '^##|^###' file > /tmp/result",
                    "rg -n 'literal' file; cat file"],
                   'reviewer tool surface refuses non-read command', roles=('reviewer',))

    def test_quoted_wildcard_push_refspec_is_irreversible(self):
        # Quoting is how a caller stops the local shell globbing a refspec, so the
        # pattern reaches git itself and pushes every matching branch, default included.
        self.check([
            "git push origin 'refs/heads/*:refs/heads/*'",
            'git push origin "refs/heads/*:refs/heads/*"',
            "git push origin 'refs/heads/*'",
            "git push origin '*:*'",
            "git push origin '*'",
            "git push origin 'HEAD:refs/heads/*'",
            "git push origin 'refs/heads/task/*:refs/heads/task/*'",
            "git push origin 'heads/*'",
            "git push --force-with-lease origin 'refs/heads/*:refs/heads/*'",
        ], 'irreversible')

    def test_quoted_wildcard_outside_the_branch_namespace_keeps_its_own_kind(self):
        # The tag namespace is the release predicate's, and stays there.
        self.check(["git push origin 'refs/tags/*:refs/tags/*'",
                    "git push origin 'refs/tags/*'"], 'release')


class RemotePolicyHookTest(unittest.TestCase):
    """Real handler AND settings loader; only external gh/git responses are doubled."""
    def setUp(self):
        import base64
        self.h = module()
        self.policy = {'command_patterns': {'irreversible': [r'\brm -R\b', r'\bacmectl destroy\b']}}
        self.tree = {'tree': [{'path': '.github/devstandard-guards.json', 'sha': 'c'*40}],
                     'truncated': False}
        self.error = None
        def api(endpoint, *args):
            if self.error:
                raise self.error
            if endpoint == 'repos/o/r': return {'default_branch': 'trunk'}
            if endpoint == 'repos/o/r/branches/trunk': return {'commit': {'sha': 'b'*40}}
            if endpoint == 'repos/o/r/git/trees/' + 'b'*40 + '?recursive=1': return self.tree
            if endpoint == 'repos/o/r/git/blobs/' + 'c'*40:
                return {'content': base64.b64encode(json.dumps(self.policy).encode()).decode()}
            self.fail(endpoint)
        def run(*args, **kwargs):
            if args == ('gh', 'repo', 'view', '--json', 'nameWithOwner', '--jq', '.nameWithOwner'):
                return 'o/r'
            if args == ('git', '-C', str(ROOT), 'rev-parse', 'HEAD'): return 'a'*40
            self.fail(args)
        self.api = self.enterContext(patch.object(self.h, 'api', side_effect=api))
        self.enterContext(patch.object(self.h, 'run', side_effect=run))
        self.enterContext(patch.dict(sys.modules, {'hard_edges': self.h}))

    def hook(self, role, command, tool='Bash', field='command'):
        out = io.StringIO()
        event = {'tool_name': tool, 'tool_input': {field: command}, 'cwd': str(ROOT)}
        with patch.object(sys, 'argv', ['pre-tool-use', '--role', role]), \
             patch.object(sys, 'stdin', io.StringIO(json.dumps(event))), patch.object(sys, 'stdout', out):
            runpy.run_path(str(ROOT / 'hooks/pre-tool-use'), run_name='__main__')
        return json.loads(out.getvalue())

    def test_remote_extensions_through_executable_worker_hook_in_both_formats(self):
        with remote_policy_project(self.policy) as (project, env):
            for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
                for command in ('rm -R /probe', 'acmectl destroy db'):
                    with self.subTest(tool=tool, command=command):
                        event = {'tool_name': tool, 'tool_input': {field: command}, 'cwd': str(project)}
                        result = subprocess.run([str(ROOT / 'hooks/pre-tool-use'), '--role', 'worker'],
                            input=json.dumps(event), env=env, text=True, capture_output=True)
                        self.assertEqual(result.returncode, 0, result.stderr)
                        output = json.loads(result.stdout).get('hookSpecificOutput', {})
                        self.assertEqual(output.get('permissionDecision'), 'deny')
                        self.assertEqual(output['permissionDecisionReason'],
                                         'worker role refuses recognized irreversible operation')

    def test_remote_extensions_reach_all_roles_and_cache_once_per_process(self):
        for role in ('worker', 'reviewer', 'orchestrator'):
            for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
                for command in ('rm -R /probe', 'acmectl destroy db'):
                    with self.subTest(role=role, tool=tool, command=command):
                        output = self.hook(role, command, tool, field).get('hookSpecificOutput', {})
                        self.assertEqual(output.get('permissionDecision'), 'deny')
                        self.assertIn('irreversible', output['permissionDecisionReason'])
        self.assertEqual(self.api.call_count, 4, 'one remote policy snapshot shared by all tool calls')

    def test_remote_default_branch_is_guarded_without_a_local_policy_override(self):
        self.policy['_default_branch'] = 'fake-local-choice'
        for role in ('worker', 'reviewer', 'orchestrator'):
            for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
                for ref in DEFAULT_BRANCH_REFS:
                    with self.subTest(role=role, tool=tool, ref=ref):
                        output = self.hook(role, 'git push origin ' + ref, tool, field).get('hookSpecificOutput', {})
                        self.assertEqual(output.get('permissionDecision'), 'deny')
                        self.assertIn('irreversible', output['permissionDecisionReason'])

    def test_routine_worker_commands_use_remote_patterns_and_default_branch(self):
        self.policy = json.loads((ROOT / '.github/devstandard-guards.json').read_text())
        for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
            for command, allowed in (
                    ('rm -rf /tmp/devstandard-x.abc', True),
                    ('rm -rf /srv/data', False),
                    ('git push --force-with-lease origin task/x', True),
                    ('git push --force-with-lease origin HEAD:trunk', False),
                    ('git push --force-with-lease origin HEAD:heads/trunk', False)):
                with self.subTest(tool=tool, command=command):
                    result = self.hook('worker', command, tool, field)
                    if allowed:
                        self.assertEqual(result, {})
                    else:
                        self.assertEqual(result['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_unreadable_policy_refuses_all_roles_even_for_read_commands(self):
        self.error = self.h.Refusal('policy unavailable')
        for role in ('worker', 'reviewer', 'orchestrator'):
            for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
                with self.subTest(role=role, tool=tool):
                    output = self.hook(role, 'git status', tool, field).get('hookSpecificOutput', {})
                    self.assertEqual(output.get('permissionDecision'), 'deny')
                    self.assertIn('policy unavailable', output['permissionDecisionReason'])

    def test_proven_absent_policy_keeps_builtins_and_default_branch(self):
        self.tree['tree'] = []
        for command in ('rm -R /probe', 'git push origin HEAD:trunk'):
            self.assertEqual(self.hook('worker', command).get('hookSpecificOutput', {}).get('permissionDecision'), 'deny')
        self.assertEqual(self.hook('worker', 'git status'), {})
        self.assertEqual(self.api.call_count, 3)

    def test_malformed_match_extensions_refuse_before_non_shell_tools(self):
        for patterns in ([], {'irreversible': 'rm'}, {'irreversible': ['[']}, {'unknown': []}):
            self.policy = {'command_patterns': patterns}
            # Malformed policy must not be cached as a successful snapshot.
            with self.subTest(patterns=patterns):
                output = self.hook('worker', 'ignored', 'Read', 'file_path').get('hookSpecificOutput', {})
                self.assertEqual(output.get('permissionDecision'), 'deny')

    def test_malformed_and_truncated_policy_refuse(self):
        self.policy = []
        self.assertEqual(self.hook('worker', 'git status').get('hookSpecificOutput', {}).get('permissionDecision'), 'deny')
        self.tree = {'tree': [], 'truncated': True}
        self.assertEqual(self.hook('reviewer', 'git status').get('hookSpecificOutput', {}).get('permissionDecision'), 'deny')


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
                        result, _ = orchestrator_hook(command, tool, field, role=role)
                        self.assertEqual(result['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_adversarial_sweep_every_configured_operation_across_every_family(self):
        import re
        h = module()
        settings = json.loads((ROOT / '.github/devstandard-guards.json').read_text())
        settings.update(_default_branch='trunk', standing_release=None)
        for kind, patterns in settings['command_patterns'].items():
            # An added policy pattern needs a witness; no configured matcher can silently miss the sweep.
            for pattern in patterns:
                self.assertTrue(any(re.search(pattern, c) for c in DANGEROUS_OPERATIONS[kind]), pattern)
        probes = 0
        seen = 0
        shard = parse_shard(os.environ.get('HARD_EDGE_SHARD'))
        for kind, commands in DANGEROUS_OPERATIONS.items():
            for command in commands:
                self.assertEqual(h.classify(command, settings), kind)
                for family, decision, variant in SHELL_FAMILIES:
                    candidate = variant(command)
                    for role in ('worker', 'reviewer', 'orchestrator'):
                        for tool, field in (('Bash', 'command'), ('exec_command', 'cmd')):
                            index = seen
                            seen += 1
                            if not selected_probe(index, shard):
                                continue
                            with self.subTest(operation=command, family=family, role=role, tool=tool):
                                self.assertIsNotNone(h.tool_decision(role, tool, {field: candidate}, settings))
                                result, _ = orchestrator_hook(candidate, tool, field, role=role,
                                                              settings=settings)
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
                        result, _ = orchestrator_hook(command, tool, field, role='worker')
                        out = result['hookSpecificOutput']
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
            'git status "${suffix}"',
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

    def test_substitution_refuses_every_role_including_double_quotes(self):
        self.assert_unsupported_shell_refuses([
            'git status `npm publish`', 'git status $(npm publish)',
            'git status "$(npm publish)"',
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
        self.assertEqual(h.classify('git push --force-with-lease origin task/12', {}), 'irreversible')
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

    def test_exact_label_emphasized_verdict_from_pr_247_is_admitted(self):
        h = module()
        row = {'id': 1, 'user': {'login': 'o'},
               'body': '## Merge check 1 — round 1\n' + verdicts.LABEL_EMPHASIZED_ROUND_ONE_VERDICT}
        self.assertEqual(h.acceptance([row], '0bd3b0acf4457c0960cc676b78227914ab6a51fe')['id'], 1)

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
        with remote_policy_project({}) as (project, env):
            result = subprocess.run(shlex.split(command), input=json.dumps({'tool_name':'Bash',
                'tool_input':{'command':'gh pr merge 0 --squash'}, 'cwd':str(project)}),
                env=env, text=True, capture_output=True)
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
        if endpoint.endswith('/branches/main'): return {'commit': {'sha': self.base}}
        if '/comments' in endpoint: return []
        if endpoint.endswith('/protection'):
            return {'required_status_checks': {'strict': True, 'contexts': ['test']},
                    'enforce_admins': {'enabled': True}, 'allow_force_pushes': {'enabled': False},
                    'allow_deletions': {'enabled': False}}
        if 'check-runs' in endpoint: return {'check_runs': self.checks}
        if '/status?' in endpoint: return {'statuses': []}
        self.fail(endpoint)

    def guard(self):
        out = io.StringIO()
        with patch.dict(sys.modules, {'hard_edges': self.h}), \
             patch.object(self.h, 'api', side_effect=self.api), \
             patch.object(self.h, 'settings_for', return_value=('o/r', {})), \
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
        for checks in ([], self.checks[:1], [dict(c, conclusion='failure') for c in self.checks],
                       [dict(c, status='in_progress', conclusion=None) for c in self.checks]):
            with self.subTest(checks=checks):
                self.checks = checks
                stderr = io.StringIO()
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as error:
                    self.guard()
                self.assertEqual(error.exception.code, 2)
                self.assertIn('CI not green', stderr.getvalue())

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
                     patch.object(h, 'settings_for', return_value=('o/r', settings)), \
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
             patch.object(h,'version_only',return_value=False), \
             patch.object(h,'settings_for',return_value=('o/r',{})), patch.object(h,'protection_check'), \
             patch.object(h,'commit_checks',return_value={}), patch.object(h,'authorized',return_value=False):
            with self.assertRaisesRegex(h.Refusal,'human sign-off'):
                h.merge_check(Path('.'),'o/r',12)


if __name__ == '__main__':
    unittest.main(verbosity=2)
