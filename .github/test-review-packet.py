#!/usr/bin/env python3
"""Review assembly/publication integration: real git and dispatcher, fake GitHub/executor I/O."""
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import os
from pathlib import Path
import re
import runpy
import subprocess
import sys
import threading
import time
import unittest

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('dispatch_tests', Path(__file__).with_name('test-dispatch.py'))
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
SOURCE = fixtures.SOURCE


# Exact reviewer return from PR #222, comment 5551758727 (record envelope excluded).
ROUND_ONE_VERDICT = """Reviewer: Codex, gpt-6-astra at high, read-only — reviewed db4e19917200c4262279ae2752460ec68b74573b

### Goal verdict

No — the assembler substantially implements the issue, but acceptance handling has a reproducible defect and the live publication done-check remains incomplete.

- In [scripts/review-packet:214](/home/leon/projects/prod/devstandard/.claude/worktrees/203-rebuild-3-review-packet-assembly-verdict-publica/scripts/review-packet:214), `outcome()` requires `Yes` or `No` immediately after the Goal heading’s newline. Adding an ordinary Markdown blank line to an otherwise accepted verdict changes the reproduced result from `valid: true` / `accepted` to `valid: false`, `goal: null` / `evidence-fix-decision`. Publication still consumes the round, and `merge-as-is` then refuses the verdict. This breaks the required convergence path for normally formatted reviewer output. Parse the section with blank-line tolerance and cover that format in validation.
- The report explicitly leaves live whole-verdict publication unfinished. At review time, [PR #222’s round-1 comment](https://github.com/LeonJoeeee/devstandard/pull/222#issuecomment-5551758727) records a dispatched attempt, not a returned verdict. Reservation demonstrates progress but does not yet satisfy the publication done-check.

I ran all three supplied diff commands and checked the claimed validation against the implementation and tests. [CI logs](https://github.com/LeonJoeeee/devstandard/actions/runs/33965392956/job/101304491839) confirm 21 dispatcher and 16 assembler tests passed. Read-only verification confirmed all three commit pins resolve, 12 packet slots validate, the predicate contains 51 payload lines, and `git diff --check` passes.

### Floor

1. Evidence-backed completion claim: Pass — the reported implementation and test results have supporting evidence; the report candidly excludes live publication from its completion claim. Packet integrity checks passed. The remaining fulfillment gaps are identified above.
2. Authorization and scope: Pass — no unauthorized irreversible action or out-of-scope work was found. All four changed documentation paths already existed; their edits support the shipped helper, and CLAUDE.md adds a test command. No competing authority or handoff document was added. The manifest bump follows repository policy; no merge or release is evidenced.

Ready to merge: No — the Goal verdict is No.

### Notes

None.

Post this verdict whole on the PR before acting on it."""


# Exact reviewer return from PR #235, comment 5558730594 (record envelope excluded).
EMPHASIZED_ROUND_ONE_VERDICT = """Reviewer: Codex, gpt-6-astra at high, read-only — reviewed 2838572a5aa0e788ba7a5640173c8543c134217a

### Goal verdict

No — the implementation substantially fulfills the rewrite, but the issue’s explicit completion requirements remain outstanding:

- Human drop approval is still **PENDING** in the ledger and PR description.
- Architecture-level human sign-off remains pending.
- Whole check-1 publication remains the caller’s responsibility.

The diff supports the normative opening, shared workflow/interlock, two role references, centralized skill bindings, dispatch updates, and independent inline-or-read delivery.

I ran all three required diff commands. Static calculations reproduce the claimed budget figures exactly: core **6,977 bytes / ~1,347 tokens**, with complete contexts of **7,372** and **9,861 bytes**, below the **10,000-byte** cap. The ledger preserves every non-heading source line from the original core and worker brief and assigns dispositions. `git diff --check` passed. Test implementations and workflow changes support the described verification coverage; I could not independently rerun the suites or confirm hosted results.

### Floor

1. Evidence-backed completion claim: **Pass** — the packet pins resolve, required diff commands succeed, and concrete source, measurement, and verification evidence supports the implementation claim. The report explicitly discloses its unfinished approval requirements rather than claiming they passed.
2. Authorization and scope: **Pass** — the issue authorizes the ledger and both role references; other changed documentation edits existing tracked paths. The ledger is explicitly audit evidence, and the role pages divide responsibilities without creating competing authorities. Supporting hook, dispatch, gate, documentation, and version changes fit the task. No unauthorized irreversible action or unrelated work is evidenced; the working tree is clean.

Ready to merge: **No** — the required human decisions remain unrecorded.

### Notes

The reviewer guard refused test execution and GitHub/browser reads. Hosted CI, native-session measurements, extraction chronology, and any subsequent approvals were therefore assessed from the supplied record, not independently authenticated.

Post this verdict whole on the PR before acting on it."""


# Exact reviewer return from PR #247, comment 5560342269 (record envelope excluded).
# The first Claude-native verdict: its Floor and Ready emphasis wraps label and result together.
LABEL_EMPHASIZED_ROUND_ONE_VERDICT = """Reviewer: Claude subagent, opus, read-only — reviewed 0bd3b0acf4457c0960cc676b78227914ab6a51fe

### Goal verdict

**Yes** — the PR turns the hard-edge adversarial sweep into sixteen deterministic parallel matrix jobs behind a fan-in that preserves the required `test` context, and its claimed commands and outputs are consistent with what the diff supports.

Checked against the diff, claim by claim:

- **N parallel matrix jobs over a deterministic slice.** `.github/workflows/ci.yml` adds `sweep` with `matrix.shard: [0…15]`, `fail-fast: false`, and `HARD_EDGE_SHARD: ${{ matrix.shard }}/${{ strategy.job-total }}`. In `.github/test-hard-edges.py`, both sweep tests take `shard = parse_shard(os.environ.get('HARD_EDGE_SHARD'))` and skip on `index % total != index_selected`, where `index` comes from a `seen` counter incremented for *every* probe before the skip. Because `DANGEROUS_OPERATIONS` (dict, insertion-ordered), `SHELL_FAMILIES` (list), `GLOBAL_OPTIONS`, the role tuple and the tool tuple are all deterministic sequences, the residue classes are an exact partition of the same index space in every shard: no probe is dropped and none is run twice.
- **The rest of the suite stays where it is.** The former `test` job is renamed `suite` with its steps intact, plus `HARD_EDGE_SHARD: rest` on the hard-edge step. `load_tests` sends exactly the two `SWEEP_TESTS` methods to the shards and everything else to `rest`, so `sweep_ids | rest_ids == all_ids` and `sweep_ids & rest_ids == set()` — asserted directly by the new `ShardSelectionTest.test_rest_and_sweep_modes_partition_test_methods`.
- **Fan-in requiring every shard green.** The new job id is literally `test` with no `name:` override, so the branch-protection context `test` survives; `if: ${{ always() }}` plus `needs: [suite, sweep]` and `test "$SUITE_RESULT" = success` / `test "$SWEEP_RESULT" = success` means any non-`success` aggregate (failure, cancelled, skipped, empty matrix) turns it red. `merged-result` still `needs: test`, and the advertised-merge-parent binding that used to live only in `test` is now present in **both** `suite` (inherited step) and `sweep` (new "Bind sweep checkout to the advertised PR merge result" step), so `merged-result / <base> / <head>` still means what it meant.
- **Probe count summed across shards equals the unsharded count.** The claimed table sums to 46,164 token + 50,112 shell = 96,276, matching the claimed unsharded `46164` / `50112`. The split is not merely plausible, it is the *exact* split modulo arithmetic predicts: 46,164 mod 16 = 4, so precisely four shards (0–3) report 2,886 and twelve report 2,885, which is what the table shows; 50,112 / 16 = 3,132 with no remainder, and every shard reports 3,132. The quoted local run `HARD_EDGE_SHARD=0/16` → `2886` / `3132` matches the hosted shard-0 row exactly, which is also independent evidence that `${{ strategy.job-total }}` resolved to `16` rather than to an empty string (an empty denominator would have made `parse_shard` raise and failed all sixteen shards).
- **A deliberately failing probe turns the required check red.** The negative run at head `41832d6a…` (eight shards) reports shard 0 failing one probe, required `test` failing, `merged-result` skipped. Its counters are self-consistent to the single probe: at eight shards a clean run gives 5,771 to shards 0–3 and 5,770 to shards 4–7, and the table shows shard 0 at 5,770 — one short — because `probes += 1` sits *inside* the `with self.subTest(...)` block that the failing assertion aborts, exactly as the PR explains ("counters increment after the assertion"). Sum 96,275 + the one failure = 96,276.
- **Unsharded default unchanged.** `parse_shard(None)` returns `None`, `load_tests` returns `standard_tests` unmodified, and `selected_probe(i, None)` is unconditionally `True` — asserted by `test_unset_preserves_full_suite_and_all_probes`. The quoted local `Ran 89 tests … OK` with the full counters is what that predicts.
- **No test weakened.** Nothing was deleted (129 insertions, 1 deletion — the deletion is the `test:` → `suite:` job-key line). The per-command `h.classify(...) == kind` assertion and the "every configured policy pattern needs a witness" loop sit *above* the sharded innermost loop, so they run in full in all sixteen shards rather than being sliced.
- **Bounds honoured, including the naming requirement.** Only the three files named in the bounds changed, and the PR states which job carries the required context: "the `test` job carries the required `test` context (strict, GitHub Actions app 15368)".

What I could not verify: the GitHub run metadata itself. My tools are read-only and offline, and the contract forbids re-running the suite in any case — CI owns pass/fail. The 150-second wall-time and all-green claims therefore rest on the two linked runs; I judged their internal arithmetic, which corroborates them to the individual probe in both the positive and the negative case.

### Floor

1. **Evidence-backed completion claim: Pass** — the claim is not an evidence-free "done". It supplies a linked head-matched CI run with per-shard job URLs and counters, a separately linked negative run demonstrating the red required check, quoted local exit-0 output for both the unsharded and the `0/16` invocations, and baseline/final `git status --porcelain -uall` snapshots (both empty). Every number I could recompute from the diff's own logic reproduced exactly, including the uneven 4/12 remainder split and the off-by-one in the failing shard.

2. **Authorization and scope: Pass** — no irreversible or unauthorized action: nothing merged, tagged, released or force-pushed; branch protection is untouched by the diff and the required context is preserved rather than renamed; durable writes are disclosed (task branch, issue comments, PR #247 and its evidence comments) and scratch directories are named. Scope: the name-status diff is exactly `M .github/test-hard-edges.py`, `M .github/workflows/ci.yml`, `M CLAUDE.md` — the three paths the bounds name, no branches or files beyond them. Applying the in-repo-writes predicate: `.github/test-hard-edges.py` is code and `.github/workflows/ci.yml` is genuine runtime configuration, so neither is governed; `CLAUDE.md` is governed documentation but is an `M` on a path already tracked in the pinned convention base `b55c30d1…` (confirmed by the pinned `git show b55c30d1…:CLAUDE.md`), which is ordinary work, and it is not a handoff or session-state artifact — it independently satisfies arm 1's repo-root `CLAUDE.md` trigger, since the change adds a command to the command fence. No document was added, so no competing authority is created at any scope, and nothing is admitted on an accepted spec while the packet says `NONE`.

Packet integrity, as directed: every slot is filled; reviewer identity, both bases and the head are supplied; all three diff commands are pinned against `b55c30d1af01630f2f3ed7fd25cadef65270dfa6` → `0bd3b0acf4457c0960cc676b78227914ab6a51fe` with exit code 0; the predicate unit carries both delimiters and its declared **51 payload lines** match the lines actually between them; accepted-spec blob is `NONE` with no document admitted on a spec; the CI-fallback section is `NONE` and is skipped.

**Ready to merge: Yes** — decided only by the Goal verdict and these two Floor checks.

### Notes

1. **`strategy.job-total` is a latent silent-coverage hazard for a future edit.** Today the matrix has one dimension, so `job-total` is 16 and the denominator is right. If anyone later adds a second dimension (an OS or Python-version axis), `job-total` becomes 32 while `matrix.shard` still ranges 0–15, so probes with `index % 32 >= 16` would never run and every shard would still be green. Nothing in the suite guards that coupling. A one-line comment at the `env:` block, or an assertion that the denominator equals the shard-list length, would close it.

2. **`HARD_EDGE_SHARD=rest` combined with an explicit test name raises `TypeError`, not a clean error.** `unittest` skips the module-level `load_tests` hook when test names are passed on the command line, so `HARD_EDGE_SHARD=rest python3 .github/test-hard-edges.py ShellCompositionTest` reaches `selected_probe(index, 'rest')` and evaluates `index % shard[1]` against the character `'e'`. Unreachable from CI and from both documented commands; only an interactive footgun.

3. **The `SWEEP_TESTS` name list is guarded — worth recording as a strength.** A renamed sweep method would otherwise leave the shards loading zero tests and passing vacuously; `ShardSelectionTest.test_rest_and_sweep_modes_partition_test_methods` asserts `len(sweep_ids) == 2` and runs in the `rest`/`suite` job, so that failure mode surfaces red instead of silent.

4. **No manifest bump.** `CLAUDE.md`'s Version bumps paragraph at the convention base says to fold the lockstep bump into the change PR; this PR deliberately does not, and says so. The issue's bounds name only three files and nothing here ships to installers (`.github/` is not packaged), so it is the merging session's call, not a goal or scope defect — flagged only so the call is made deliberately.

5. **`search twice` appears satisfied; I found no site owing reconciliation.** `reference/ci-pipelines.md`'s "enable branch protection on `main` requiring the `test` check" stays true because the context name is preserved, and `reference/hard-edges.md`'s description of the two adversarial sweeps describes what the test file carries, not where or in how many jobs it runs — the union of shards keeps every sentence there accurate.

6. **Minor cost:** the fan-in `test` job provisions a full `ubuntu-latest` runner to evaluate two string comparisons. That is the price of keeping the protected context name, which the bounds explicitly permit; noting it only as an observation.

7. **The CLAUDE.md one-liner hardcodes `/16`.** Any `TOTAL` is valid, so it will not error if the matrix width changes, but it would quietly stop mirroring the CI configuration. Cheap to leave as is.

Post this verdict whole on the PR before acting on it.

"""


# The canonical judging contract: all four decision lines carry their grounds after a spaced em
# dash. On PR #284 (2026-09-07) round 1 closed with a bare `Ready to merge: Yes`; publication
# recorded it accepted while the merge guard refused it, so no round the packet would admit was
# left (#287). Both verdict parsers read these fixtures.
CANONICAL_VERDICT = """Reviewer: Probe, read-only — reviewed {head}
### Goal verdict
Yes — the PR accomplishes the issue's goal within its bounds and done-check.
### Floor
1. Evidence-backed completion claim: Pass — the claimed commands and outputs match the diff.
2. Authorization and scope: Pass — no unauthorized irreversible action and nothing outside the task.
Ready to merge: Yes — decided only by the Goal verdict and these two Floor checks.
### Notes
None.
Post this verdict whole on the PR before acting on it.
"""

# Each decision line as it is written through its result, beside the name a refusal must report.
DECISION_LINES = (('Yes', 'Goal verdict'),
                  ('1. Evidence-backed completion claim: Pass', '1. Evidence-backed completion claim'),
                  ('2. Authorization and scope: Pass', '2. Authorization and scope'),
                  ('Ready to merge: Yes', 'Ready to merge'))


def canonical_verdict(head='a' * 40, bare=None):
    """The accepted verdict; `bare` strips one decision line's grounds, as PR #284's did (#287)."""
    verdict = CANONICAL_VERDICT.format(head=head)
    if bare is None:
        return verdict
    return re.sub('^' + re.escape(bare) + r' — [^\n]*$', bare, verdict, flags=re.M)


def decision(label, value, emphasis, wrap):
    """One decision line, emphasized around the result (#237), the label, or the whole line (#251)."""
    number, _, rest = label.partition('. ') if label[0].isdigit() else ('', '', label)
    number = number and number + '. '
    if wrap == 'result':
        return f'{number}{rest} {emphasis}{value}{emphasis}'
    if wrap == 'label':
        return f'{number}{emphasis}{rest} {value}{emphasis}'
    return f'{emphasis}{number}{rest} {value}{emphasis}'


class OutcomeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(SOURCE/'scripts'))
        try:
            cls.review = runpy.run_path(str(SOURCE/'scripts/review-packet'))
        finally:
            sys.path.pop(0)

    def setUp(self):
        self.record = dict(kind='attempt', status='returned', round=1,
            head='db4e19917200c4262279ae2752460ec68b74573b',
            identity='Codex, gpt-6-astra at high, read-only')

    def test_exact_round_one_return_is_a_goal_gap_and_consumes_one_round(self):
        self.record['outcome'] = self.review['outcome'](ROUND_ONE_VERDICT, self.record)
        self.assertEqual(self.record['outcome'],
            dict(valid=True, goal='No', floor1='Pass', floor2='Pass'))
        status = self.review['state']([self.record], self.record['head'])
        self.assertEqual(status['rounds'], 1)
        self.assertEqual(status['next'], 'goal-fix-decision')

    def test_exact_emphasized_round_one_return_is_a_goal_gap(self):
        record = self.record | {'head': '2838572a5aa0e788ba7a5640173c8543c134217a'}
        result = self.review['outcome'](EMPHASIZED_ROUND_ONE_VERDICT, record)
        self.assertEqual(result, dict(valid=True, goal='No', floor1='Pass', floor2='Pass'))
        status = self.review['state']([record | {'outcome': result}], record['head'])
        self.assertEqual(status['rounds'], 1)
        self.assertEqual(status['next'], 'goal-fix-decision')

    def test_exact_label_emphasized_round_one_return_is_accepted(self):
        record = self.record | {'head': '0bd3b0acf4457c0960cc676b78227914ab6a51fe',
                                'identity': 'Claude subagent, opus, read-only'}
        result = self.review['outcome'](LABEL_EMPHASIZED_ROUND_ONE_VERDICT, record)
        self.assertEqual(result, dict(valid=True, goal='Yes', floor1='Pass', floor2='Pass'))
        status = self.review['state']([record | {'outcome': result}], record['head'])
        self.assertEqual(status['rounds'], 1)
        self.assertEqual(status['next'], 'accepted')

    def test_emphasized_results_preserve_goal_and_floor_decisions(self):
        for emphasis in ('*', '**', '_', '__'):
            for wrap in ('result', 'label', 'line'):
                for goal, floor1, floor2, ready, next_step in (
                        ('Yes', 'Pass', 'Pass', 'Yes', 'accepted'),
                        ('No', 'Pass', 'Pass', 'No', 'goal-fix-decision'),
                        ('Yes', 'Fail', 'Pass', 'No', 'evidence-fix-decision'),
                        ('Yes', 'Pass', 'Fail', 'No', 'human-escalation')):
                    with self.subTest(emphasis=emphasis, wrap=wrap, goal=goal, floor1=floor1, floor2=floor2):
                        verdict = ROUND_ONE_VERDICT.replace('\nNo —', f'\n{emphasis}{goal}{emphasis} —')
                        for label, written, value in (
                                ('1. Evidence-backed completion claim:', 'Pass', floor1),
                                ('2. Authorization and scope:', 'Pass', floor2),
                                ('Ready to merge:', 'No', ready)):
                            verdict = verdict.replace(f'{label} {written}',
                                                      decision(label, value, emphasis, wrap))
                        result = self.review['outcome'](verdict, self.record)
                        self.assertEqual(result, dict(valid=True, goal=goal, floor1=floor1, floor2=floor2))
                        self.assertEqual(self.review['state']([self.record | {'outcome': result}],
                                                            self.record['head'])['next'], next_step)

    def test_goal_accepts_blank_lines_and_ordinary_markdown(self):
        for section in ('### Goal verdict\nNo', '### Goal verdict\n\n\nNo',
                        '### Goal verdict  \n \t\nNo', '### **Goal verdict**\n\n**No**',
                        '  ### __Goal verdict__ ###\n\n_No_', '### *Goal verdict*\n\n*No*'):
            for goal in ('Yes', 'No'):
                with self.subTest(section=section, goal=goal):
                    verdict = ROUND_ONE_VERDICT.replace('### Goal verdict\n\nNo', section.replace('No', goal))
                    verdict = verdict.replace('Ready to merge: No', 'Ready to merge: ' + goal)
                    result = self.review['outcome'](verdict, self.record)
                    self.assertEqual(result, dict(valid=True, goal=goal, floor1='Pass', floor2='Pass'))
                    status = self.review['state']([self.record | {'outcome': result}], self.record['head'])
                    self.assertEqual(status['next'], 'accepted' if goal == 'Yes' else 'goal-fix-decision')

    def canonical_record(self):
        return self.record | {'head': 'a' * 40, 'identity': 'Probe, read-only'}

    def test_canonical_grounded_decision_lines_are_valid_and_accepted(self):
        record = self.canonical_record()
        result = self.review['outcome'](canonical_verdict(), record)
        self.assertEqual(result, dict(valid=True, goal='Yes', floor1='Pass', floor2='Pass'))
        self.assertEqual(self.review['state']([record | {'outcome': result}], record['head'])['next'],
                         'accepted')

    def test_a_decision_line_without_its_grounds_is_malformed_never_accepted(self):
        """PR #284 published a bare `Ready to merge: Yes` the merge guard then refused (#287)."""
        record = self.canonical_record()
        for bare, named in DECISION_LINES:
            with self.subTest(line=bare):
                result = self.review['outcome'](canonical_verdict(bare=bare), record)
                self.assertFalse(result['valid'])
                self.assertIn('grounds', result['reason'])
                self.assertIn(named, result['reason'])
                # A malformed verdict is an evidence gap the orchestrator can rule on, never
                # the accepted state that refuses every further round.
                self.assertEqual(self.review['state']([record | {'outcome': result}],
                                                      record['head'])['next'], 'evidence-fix-decision')

    def test_a_groundless_floor_two_failure_still_stops_the_lane(self):
        """Grounds decide validity, never which result is reported: a Fail must not hide (#260)."""
        record = self.canonical_record()
        groundless = canonical_verdict(bare='2. Authorization and scope: Pass')
        result = self.review['outcome'](
            groundless.replace('2. Authorization and scope: Pass', '2. Authorization and scope: Fail'),
            record)
        self.assertEqual(result['floor2'], 'Fail')
        self.assertFalse(result['valid'])
        self.assertEqual(self.review['state']([record | {'outcome': result}],
                                              record['head'])['next'], 'human-escalation')

    def test_goal_cannot_borrow_an_answer_from_a_later_section_or_prose(self):
        for section in ('### Goal verdict\n\n### Other\nNo',
                        '### Goal verdict\n\nUndecided.\nNo',
                        '### Goal verdict\n\nNobody'):
            with self.subTest(section=section):
                verdict = ROUND_ONE_VERDICT.replace('### Goal verdict\n\nNo', section)
                result = self.review['outcome'](verdict, self.record)
                self.assertFalse(result['valid'])
                self.assertIsNone(result['goal'])


class ContractTest(unittest.TestCase):
    def fence(self):
        source = (SOURCE/'reference/code-review-prompt.md').read_text()
        matches = re.findall(r'\n```\n(.*?)\n```\n', source, re.S)
        self.assertEqual(len(matches), 1, 'the judging contract must stay a single bare fence')
        return matches[0]

    def test_contract_states_the_ci_configuration_rule_once(self):
        fence = self.fence()
        self.assertEqual(fence.count('{CI_CONFIGURATION_PATHS}'), 1)
        # Wrapping is presentation; match the sentence as outcome() matches the verdict's close line.
        self.assertEqual(' '.join(fence.split()).count('is not evidence for the goal'), 1)


class ReviewTest(unittest.TestCase):
    def setUp(self):
        self.d = fixtures.DispatchTest()
        self.d.setUp()
        self.addCleanup(self.d.doCleanups)
        self.root, self.project, self.env = self.d.root, self.d.project, self.d.env
        self.script = SOURCE/'scripts/review-packet'
        remote=self.root/'remote.git'
        self.d.git('init','--bare',str(remote))
        self.d.git('remote','add','origin',str(remote))
        self.d.git('push','origin','main')
        self.base=self.d.git('rev-parse','HEAD')
        self.branch,self.wt=self.d.hand_made_lane()
        self.d.call('--adopt','--base','origin/main','--branch',self.branch,'--worktree',str(self.wt))
        (self.wt/'result.txt').write_text('Result\n\n')
        self.d.git('-C',str(self.wt),'add','.')
        self.d.git('-C',str(self.wt),'commit','-m','result')
        self.head=self.d.git('rev-parse',self.branch)
        self.d.git('push','origin',self.branch)
        self.d.git('update-ref','refs/pull/13/head',self.head)
        self.d.git('push','origin','refs/pull/13/head')
        self.prfile=self.root/'pr.json'
        self.prfile.write_text(json.dumps(dict(number=13,url='https://github.com/o/r/pull/13',state='OPEN',
            headRefName=self.branch,headRefOid=self.head,baseRefName='main',baseRefOid=self.base,
            body='Complete claim. Evidence: command exited 0.\n\nBaseline and final status: empty.')))
        self.prcomments=self.root/'pr-comments.json';self.prcomments.write_text('[]')
        self.checks=self.root/'checks.json';self.checks.write_text(json.dumps([dict(name='test',bucket='pass',state='SUCCESS')]))
        self.env.update(PR_COMMENTS=str(self.prcomments),CHECKS=str(self.checks))
        gh=(self.d.bin/'gh').read_text()
        gh=gh.replace("elif a[:1]==['api']:", """elif a[:2]==['pr','checks']:
 rows=json.loads(Path(os.environ['CHECKS']).read_text());print(json.dumps(rows))
 sys.exit(0 if all(r['bucket']=='pass' for r in rows) else 8)
elif a[0]=='api' and (a[1].endswith('/protection/required_status_checks') or '/issues/13/comments' in a[1] or '/issues/comments/' in a[1]):
 import tempfile
 def write_comments(rows):
  path=Path(os.environ['PR_COMMENTS'])
  with tempfile.NamedTemporaryFile(mode='w',dir=path.parent,delete=False) as temporary:
   json.dump(rows,temporary)
  Path(temporary.name).replace(path)
 endpoint=a[1]; rows=json.loads(Path(os.environ['PR_COMMENTS']).read_text())
 if endpoint.endswith('/protection/required_status_checks'): print(json.dumps({'contexts':['test']}))
 elif '/issues/13/comments' in endpoint:
  if '--input' in a:
   payload=json.loads(Path(a[a.index('--input')+1]).read_text())
   row=dict(id=len(rows)+100,body=payload['body'],html_url='https://github.com/o/r/pull/13#issuecomment-'+str(len(rows)+100))
   rows.append(row);write_comments(rows);print(json.dumps(row))
  else: print(json.dumps(rows))
 elif '/issues/comments/' in endpoint:
  cid=int(endpoint.rsplit('/',1)[1]); row=next(r for r in rows if r['id']==cid)
  if '--input' in a:
   row['body']=json.loads(Path(a[a.index('--input')+1]).read_text())['body'];write_comments(rows)
  print(json.dumps(row))
 else: raise SystemExit('unexpected API: '+endpoint)
elif a[:1]==['api']:""")
        (self.d.bin/'gh').write_text(gh)
        self.out=self.root/'assembly'
        self.verdict=self.root/'verdict.txt'
        self.write_verdict()
        # The executor boundary emits a complete verdict; process launch, sandbox selection,
        # supervision, and publication all remain production code.
        self.env['VERDICT']=str(self.verdict)
        self.d.tool('codex', '''import os,sys
from pathlib import Path
a=sys.argv[1:]
assert a[a.index('-s')+1]=='read-only'
Path(a[a.index('-o')+1]).write_bytes(Path(os.environ['VERDICT']).read_bytes())
''')

    def write_verdict(self, goal='Yes', floor1='Pass', floor2='Pass', notes='None.'):
        source=(SOURCE/'reference/external-agent.md').read_text()
        model,effort=re.search(r'The standing setting on these projects is `-m (\S+) -c model_reasoning_effort=(\S+)`',source).groups()
        self.verdict.write_text(f'Reviewer: Codex, {model} at {effort}, read-only — reviewed {self.head}\n'
            f'### Goal verdict\n{goal} — Checked the claim against the diff.\n### Floor\n'
            f'1. Evidence-backed completion claim: {floor1} — Evidence checked.\n'
            f'2. Authorization and scope: {floor2} — Scope checked.\n'
            f'Ready to merge: {"Yes" if (goal,floor1,floor2)==("Yes","Pass","Pass") else "No"} — Goal and Floor.\n'
            f'### Notes\n{notes}\nPost this verdict whole on the PR before acting on it.\n')

    def call(self, action, *args, ok=True):
        result=subprocess.run([sys.executable,str(self.script),action,'13','--issue','12',
            '--project',str(self.project),*args],env=self.env,text=True,capture_output=True)
        if ok:
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode,0,result.stdout)
        return result.stderr

    def assemble(self, *args, ok=True):
        return self.call('assemble','--architecture-level','no','--output',str(self.out),*args,ok=ok)

    def start(self):
        return self.call('start','--architecture-level','no','--output',str(self.out),'--implementation','codex')

    def head_touching(self, *paths):
        """Advance the PR head over the named paths, keeping every pin the assembler reads current."""
        for path in paths:
            target=self.wt/path
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text('touched by the diff under review\n')
        self.d.git('-C',str(self.wt),'add','.')
        self.d.git('-C',str(self.wt),'commit','-m','touch '+' '.join(paths))
        self.head=self.d.git('-C',str(self.wt),'rev-parse','HEAD')
        self.d.git('push','origin',self.branch)
        self.d.git('update-ref','refs/pull/13/head',self.head)
        self.d.git('push','origin','refs/pull/13/head')
        pr=json.loads(self.prfile.read_text());pr['headRefOid']=self.head
        self.prfile.write_text(json.dumps(pr))

    def published(self):
        deadline=time.monotonic()+12
        while time.monotonic()<deadline:
            comments=json.loads(self.prcomments.read_text())
            if any(r['body'].startswith('## Merge check 1 — round ') for r in comments):
                return comments
            time.sleep(.05)
        self.fail('verdict not published: '+self.prcomments.read_text())

    def test_comment_writes_never_expose_partial_json_to_concurrent_reads(self):
        bodies = ('created ' + 'a' * 4096, 'updated ' + 'b' * 4096)
        payload = self.root / 'comment-payload.json'
        stop = threading.Event()
        reading = threading.Event()

        def read_comments():
            reads = 0
            while not stop.is_set():
                rows = json.loads(self.prcomments.read_text())
                for index, row in enumerate(rows):
                    self.assertEqual(row['id'], 100 + index)
                    self.assertIn(row['body'], bodies)
                reads += 1
                reading.set()
            return reads

        with ThreadPoolExecutor(max_workers=1) as pool:
            reader = pool.submit(read_comments)
            try:
                self.assertTrue(reading.wait(timeout=5), 'reader did not start')
                for iteration in range(300):
                    if reader.done():
                        reader.result()  # Surface a partial read immediately.
                    update = iteration % 2
                    payload.write_text(json.dumps({'body': bodies[update]}))
                    endpoint = (f'repos/o/r/issues/comments/{100 + iteration // 2}'
                                if update else 'repos/o/r/issues/13/comments')
                    result = subprocess.run([str(self.d.bin / 'gh'), 'api', endpoint,
                        '-X', 'PATCH' if update else 'POST', '--input', str(payload)],
                        env=self.env, text=True, capture_output=True, timeout=10)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertEqual(json.loads(result.stdout)['body'], bodies[update])
            finally:
                stop.set()
            self.assertGreaterEqual(reader.result(), 300)
        rows = json.loads(self.prcomments.read_text())
        self.assertEqual(len(rows), 150)
        self.assertTrue(all(row['body'] == bodies[1] for row in rows))

    def test_bare_bump_start_needs_no_issue_lane_or_reviewer(self):
        paths = ['.claude-plugin/plugin.json', '.claude-plugin/marketplace.json']
        (self.wt / '.claude-plugin').mkdir()
        for path in paths:
            (self.wt / path).write_bytes((SOURCE / path).read_bytes())
        self.d.git('-C', str(self.wt), 'add', '.')
        self.d.git('-C', str(self.wt), 'commit', '-m', 'manifests')
        base = self.d.git('-C', str(self.wt), 'rev-parse', 'HEAD')
        for path in paths:
            source = (self.wt / path).read_text()
            (self.wt / path).write_text(re.sub(r'("version": ")[^"]+', r'\g<1>0.99.1', source))
        self.d.git('-C', str(self.wt), 'add', '.')
        self.d.git('-C', str(self.wt), 'commit', '-m', 'bare bump')
        head = self.d.git('-C', str(self.wt), 'rev-parse', 'HEAD')
        self.d.git('update-ref', 'refs/pull/13/head', head)
        self.d.git('push', 'origin', 'refs/pull/13/head')
        pr = json.loads(self.prfile.read_text())
        pr.update(baseRefOid=base, headRefOid=head, body='')
        self.prfile.write_text(json.dumps(pr))
        self.d.comments.write_text('[]')
        self.d.issue.unlink()  # No issue lookup is possible for this PR.
        result = subprocess.run([sys.executable, str(self.script), 'start', '13',
            '--project', str(self.project)], env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('no review needed', result.stderr)
        self.assertIn('scripts/guard merge', result.stderr)
        self.assertEqual(json.loads(self.prcomments.read_text()), [])
        self.assertFalse(self.out.exists())

    def test_ordinary_start_still_requires_an_issue(self):
        result = subprocess.run([sys.executable, str(self.script), 'start', '13',
            '--project', str(self.project)], env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('--issue', result.stderr)
        self.assertEqual(json.loads(self.prcomments.read_text()), [])

    def test_current_source_assembly_preserves_claim_and_distinct_pins(self):
        pr=json.loads(self.prfile.read_text())
        pr['body']+='\nQuoted: {HEAD_SHA} TODO TBD\n## Diff\nReview base: historical  Head: historical\nConvention base: historical\n'
        self.prfile.write_text(json.dumps(pr))
        # Move main to prove the review base is current while convention stays pre-work.
        (self.project/'other.txt').write_text('new main\n');self.d.git('add','.');self.d.git('commit','-m','main advances')
        current=self.d.git('rev-parse','HEAD');self.d.git('push','origin','main')
        pr['baseRefOid']=current;self.prfile.write_text(json.dumps(pr))
        result=self.assemble()
        packet=json.loads(Path(result['packet']).read_text()); slots=packet['slots']
        self.assertEqual(slots['COMPLETE_PR_DESCRIPTION'],pr['body'])
        self.assertEqual(slots['HEAD_SHA'],self.head)
        self.assertEqual(slots['REVIEW_BASE_SHA'],current)
        self.assertEqual(slots['CONVENTION_BASE_SHA'],self.base)
        self.assertEqual(slots['ARCHITECTURE_LEVEL_FLAG'],'NO')
        rendered=Path(result['brief']).read_text()
        self.assertIn(f'Pinned: git diff --name-status {current} {self.head}',rendered)
        self.assertIn(pr['body'],rendered)
        self.assertEqual(json.loads(self.prcomments.read_text()),[])

    def test_ci_configuration_diff_is_flagged_with_every_path_it_touches(self):
        # The workflows plus the gate files they invoke; an ordinary path never joins them.
        self.head_touching('.github/workflows/ci.yml','.github/check-core-budget.py',
                           '.github/devstandard-guards.json','docs/note.md')
        result=self.assemble()
        slots=json.loads(Path(result['packet']).read_text())['slots']
        self.assertEqual(slots['CI_CONFIGURATION_PATHS'],
            '.github/check-core-budget.py .github/devstandard-guards.json .github/workflows/ci.yml')
        self.assertIn('CI configuration touched: .github/check-core-budget.py '
                      '.github/devstandard-guards.json .github/workflows/ci.yml\n',
                      Path(result['brief']).read_text())

    def test_diff_touching_no_ci_configuration_reads_none(self):
        result=self.assemble()
        slots=json.loads(Path(result['packet']).read_text())['slots']
        self.assertEqual(slots['CI_CONFIGURATION_PATHS'],'NONE')
        self.assertIn('CI configuration touched: NONE\n',Path(result['brief']).read_text())

    def test_published_formatted_verdict_is_consumed_by_merge_guard(self):
        # The merged publisher accepts Markdown presentation around the Goal answer.
        # Exercise its real envelope and whole return, rather than a hand-built record.
        self.verdict.write_text(self.verdict.read_text().replace(
            '### Goal verdict\nYes', '### **Goal verdict**\n\n**Yes**'))
        self.start()
        rows = self.published()
        guard = runpy.run_path(str(SOURCE/'scripts/hard_edges.py'))
        accepted = guard['merge_acceptance'](rows, self.head)
        self.assertEqual(accepted['record']['base'], self.base)
        self.assertEqual(accepted['record']['architecture'], 'NO')
        self.assertIn(self.verdict.read_text(), rows[-1]['body'])
        with self.assertRaises(guard['Refusal']):
            guard['merge_acceptance'](rows, 'a'*40)

    def test_red_pending_empty_and_missing_required_checks_refuse_before_output(self):
        for rows in ([dict(name='test',bucket='fail',state='FAILURE')],
                     [dict(name='test',bucket='pending',state='IN_PROGRESS')],[],
                     [dict(name='other',bucket='pass',state='SUCCESS')]):
            with self.subTest(rows=rows):
                self.checks.write_text(json.dumps(rows))
                self.assertIn('check',self.assemble(ok=False).lower())
                self.assertFalse(self.out.exists())
                self.assertEqual(json.loads(self.prcomments.read_text()),[])

    def test_predicate_base_slots_are_filled_without_rescanning_quoted_evidence(self):
        result=self.assemble()
        brief=Path(result['brief']).read_text()
        self.assertNotRegex(brief,r'\{[A-Z_]+\}')
        self.assertIn('Pin the pre-work base as `'+self.base+'`',brief)

    def test_current_contract_change_and_predicate_count_are_validated_before_writes(self):
        import shutil
        install=self.root/'plugin'
        shutil.copytree(SOURCE/'scripts',install/'scripts')
        shutil.copytree(SOURCE/'reference',install/'reference')
        self.script=install/'scripts/review-packet'
        contract=install/'reference/code-review-prompt.md'
        contract.write_text(contract.read_text().replace('## Judging contract','## Judging contract\nCurrent source sentinel.'))
        result=self.assemble()
        self.assertIn('Current source sentinel.',Path(result['brief']).read_text())
        shutil.rmtree(self.out)
        contract.write_text(contract.read_text().replace('Current source sentinel.','{NEW_REQUIRED_SLOT}'))
        self.assertIn('slots',self.assemble(ok=False))
        self.assertFalse(self.out.exists())
        shutil.copy(SOURCE/'reference/code-review-prompt.md',contract)
        predicate=install/'reference/in-repo-writes.md'
        predicate.write_text(re.sub(r'(END IN-REPO-WRITES PREDICATE \()\d+',r'\g<1>999',predicate.read_text()))
        self.assertIn('count',self.assemble(ok=False))
        self.assertFalse(self.out.exists())

    def test_issue_fenced_commands_and_nested_bounds_are_carried_whole(self):
        issue=json.loads(self.d.issue.read_text())
        issue['body']='## Goal\nProduce evidence.\n## Bounds\nOne task.\n### Detail\nKeep this detail.\n## Done-check\nRun:\n```sh\n# Goal\necho TODO\n```\nExit zero.'
        self.d.issue.write_text(json.dumps(issue))
        result=self.assemble()
        slots=json.loads(Path(result['packet']).read_text())['slots']
        self.assertEqual(slots['ISSUE_BOUNDS'],'One task.\n### Detail\nKeep this detail.')
        self.assertEqual(slots['ISSUE_DONE_CHECK'],'Run:\n```sh\n# Goal\necho TODO\n```\nExit zero.')

    def test_missing_claim_and_unfilled_issue_refuse(self):
        pr=json.loads(self.prfile.read_text());pr['body']='';self.prfile.write_text(json.dumps(pr))
        self.assertIn('description',self.assemble(ok=False))
        pr['body']='Evidence.';self.prfile.write_text(json.dumps(pr))
        issue=json.loads(self.d.issue.read_text());issue['body']=issue['body'].replace('Produce evidence.','{GOAL}')
        self.d.issue.write_text(json.dumps(issue))
        self.assertIn('placeholder',self.assemble(ok=False))
        self.assertFalse(self.out.exists())

    def test_start_dispatches_and_publishes_whole_verdict_once(self):
        result=self.start();comments=self.published()
        verdicts=[r for r in comments if r['body'].startswith('## Merge check 1 — round ')]
        self.assertEqual(len(verdicts),1)
        self.assertTrue(verdicts[0]['body'].endswith(self.verdict.read_text()))
        self.assertTrue(verdicts[0]['body'].startswith('## Merge check 1 — round 1\n'))
        status=self.call('status');self.assertEqual(status['rounds'],1)
        self.assertEqual(status['next'],'accepted')
        self.call('publish','--attempt',str(result['attempt']))
        self.assertEqual(self.prcomments.read_text(),json.dumps(comments))

    def test_floor_failure_counts_and_cap_blocks_eighth_dispatch(self):
        self.write_verdict(goal='No',floor1='Fail')
        for round_number in range(1,8):
            if round_number>1:
                self.call('rule','--decision','continue','--reason','Obtain the missing evidence.')
            result=self.start()
            # Explicit publication is recoverable and does not require inline waiting by start.
            deadline=time.monotonic()+12
            while time.monotonic()<deadline:
                status=self.call('status')
                if status['rounds']==round_number:break
                time.sleep(.05)
            self.assertEqual(status['rounds'],round_number)
            self.assertEqual(status['next'],'orchestrator-ruling' if round_number==7 else 'evidence-fix-decision')
        before=self.d.comments.read_text()
        self.assertIn('7',self.call('start','--architecture-level','no','--output',str(self.out),ok=False))
        self.assertIn('7',self.call('rule','--decision','continue','--reason','Again',ok=False))
        self.assertEqual(self.d.comments.read_text(),before)
        self.assertIn('Floor',self.call('rule','--decision','merge-as-is','--reason','Goal met',ok=False))
        ruling=self.call('rule','--decision','rewrite','--reason','Make the done-check attainable.')
        self.assertEqual(ruling['decision'],'rewrite')
        self.assertIn('human',self.call('rule','--decision','abandon','--reason','Stop',ok=False))

    def test_existing_numbered_verdicts_cannot_reset_round_cap_on_adoption(self):
        self.prcomments.write_text(json.dumps([dict(id=100+n,
            body=f'## Merge check 1 — round {n}\n\n'+self.verdict.read_text()) for n in range(1,8)]))
        status=self.call('status')
        self.assertEqual(status['rounds'],7)
        self.assertIn('7',self.call('start','--architecture-level','no','--output',str(self.out),ok=False))
        self.assertEqual(len(json.loads(self.prcomments.read_text())),7)

    def test_floor_two_stops_lane_without_fix_round(self):
        self.write_verdict(goal='No',floor2='Fail');self.start();self.published()
        self.assertEqual(self.call('status')['next'],'human-escalation')
        self.assertIn('Floor',self.call('rule','--decision','continue','--reason','Fix scope',ok=False))

    def test_notes_and_goal_no_require_different_orchestrator_actions(self):
        self.write_verdict(goal='No',notes='Optional style improvement.')
        self.start();self.published()
        self.assertIn('ruling',self.call('start','--architecture-level','no','--output',str(self.out),ok=False))
        result=self.call('rule','--decision','merge-as-is','--reason','Goal is met within bounds; file the note.')
        self.assertEqual(result['decision'],'merge-as-is')
        self.assertEqual(self.call('status')['next'],'merge-as-is')

    def test_accepted_blob_rebase_result_and_prior_verdict_reach_reviewer(self):
        blob=self.d.git('rev-parse',self.head+':result.txt')
        issue=json.loads(self.d.issue.read_text());issue['body']+='\nAccepted spec blob: '+blob
        self.d.issue.write_text(json.dumps(issue))
        proof=self.root/'proof.json';proof.write_text(json.dumps({'result':'failed','reason':'Changed path differs'}))
        result=self.assemble('--accepted-spec',blob,'--rebase-result',str(proof))
        brief=Path(result['brief']).read_text()
        self.assertEqual(json.loads(Path(result['packet']).read_text())['accepted_spec_contents'],'Result\n\n')
        self.assertIn('Changed path differs',brief)
        self.assertIn('Result\n\n',brief)
        self.write_verdict(goal='No',notes='Quoted TODO {HEAD_SHA} and ## Diff are historical.')
        self.start();self.published()
        self.call('rule','--decision','continue','--reason','Repair the goal gap.')
        result=self.assemble()
        self.assertIn(self.verdict.read_text(),Path(result['brief']).read_text())

    def test_failed_executor_without_verdict_releases_attempt_without_consuming_round(self):
        self.d.tool('codex', 'raise SystemExit(9)\n')
        result=self.start()
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            status=self.call('status')
            if not status['active']:break
            time.sleep(.05)
        self.assertEqual(status['rounds'],0)
        self.assertEqual(status['active'],[])
        self.assertIn('failed',self.prcomments.read_text())
        self.assertIn('9',self.prcomments.read_text())

    def test_malformed_return_still_consumes_round_and_is_published_whole(self):
        self.verdict.write_text('Done, trust me.\n');self.start();self.published()
        status=self.call('status')
        self.assertEqual(status['rounds'],1)
        self.assertEqual(status['next'],'evidence-fix-decision')
        self.assertIn('Floor',self.call('rule','--decision','merge-as-is','--reason','Trust the worker',ok=False))

    def test_publication_is_idempotent_after_transient_executor_scratch_is_removed(self):
        import shutil
        result=self.start();self.published()
        shutil.rmtree(Path(result['run']['brief']).parent)
        self.call('publish','--attempt',str(result['attempt']))
        self.assertEqual(self.call('status')['rounds'],1)

    def test_stale_head_verdict_is_published_but_cannot_accept_current_head(self):
        result=self.call('start','--architecture-level','no','--output',str(self.out),'--implementation','claude')
        pr=json.loads(self.prfile.read_text());pr['headRefOid']='f'*40;self.prfile.write_text(json.dumps(pr))
        # Native return is supplied whole by the caller; it must retain the pinned reviewer identity.
        self.verdict.write_text(re.sub(r'^Reviewer: .*? — reviewed',
            'Reviewer: Claude subagent, opus, read-only — reviewed',self.verdict.read_text()))
        self.call('publish','--attempt',str(result['attempt']),'--verdict',str(self.verdict))
        self.assertTrue(self.published()[-1]['body'].endswith(self.verdict.read_text()))
        self.assertEqual(self.call('status')['next'],'full-review')


if __name__ == '__main__':
    unittest.main()
