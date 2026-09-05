# Code reviewer prompt

Use the installed plugin's `scripts/review-packet start` to commission an ordinary review from the
current sources. It fills the fenced contract below, admits only a reported green PR head, calls
`scripts/dispatch`, and publishes the whole returned verdict with its round number. The commands,
recovery path, and orchestrator rulings are in `reference/external-agent.md`'s **Review packets**
section. `assemble` produces the same packet without dispatching or publishing. The structured
packet keeps contract slots separate from quoted issue, PR, and prior-verdict evidence; a literal
placeholder name in that evidence is not an unfilled contract slot.

The assembler fills reviewer/head identity; the issue's goal, bounds, and done-check; the explicit
architecture-level flag; separate review and convention bases; the complete PR description; the
accepted-spec blob SHA (`SHA` or `NONE`); and the entire delimited in-repo-write predicate, including
its counted end marker. The fence remains the sole judging contract.

> Adapted from superpowers (`requesting-code-review/code-reviewer.md`, MIT, Jesse Vincent).

**Post the verdict on the PR the moment it comes back** — whole, before the fix round and before the merge. A reviewer you spawned returns to *you* and to nobody else; unpublished, the review dies with your session. **You are reading this at dispatch, which is not when the act falls due** — so the prompt below makes the reviewer close with the instruction, and it reaches you inside the verdict. **Title the comment `## Merge check 1 — round N`** so the record is greppable and a pre-merge check can find it. Publishing after the merge is a repair: say so in a header giving both times — when you posted it and when the PR merged.

**Before commissioning check 1 or any re-review**, compare the worktree against its pre-write baseline
under `reference/clean-handback.md` and put both `git status --porcelain -uall` snapshots in the PR.
This also covers a main session reviewing its own short-branch PR, which never passes through Taking
delivery.

**Context rules:** hand the reviewer the issue's goal statement, bounds, and done-check; the complete PR description as the fulfillment claim and its evidence; the diff at explicit base/head SHAs; and whether the change is flagged architecture-level — never your session history. The reviewer treats the PR description as unverified claims and checks it against the diff. The reviewer does **not** re-run the test suite — CI owns pass/fail. **Under a declared check-2 fallback only,** fill the CI-fallback placeholder with the PR's `CI-FALLBACK` comment *and* the audit checklist that goes with it — the reviewer is a clean context and cannot open this plugin's files, so anything it must check has to be pasted (`reference/ci-cannot-run.md`). Every other review leaves that placeholder `NONE`. The fence is the sole judging contract: goal fulfillment and the two Floor checks decide readiness; every peripheral observation is a Note and cannot block or cause a re-review.

```
You are a Senior Code Reviewer. Judge whether this PR, as a whole,
accomplished what its issue set out to accomplish. The diff is evidence,
not the object of the verdict.

## Issue contract
Goal statement: {ISSUE_GOAL_STATEMENT}
Bounds: {ISSUE_BOUNDS}
Done-check: {ISSUE_DONE_CHECK}
Architecture-level flag: {ARCHITECTURE_LEVEL_FLAG}

## PR fulfillment claim and evidence
{COMPLETE_PR_DESCRIPTION}

## Diff
Review base: {REVIEW_BASE_SHA}  Head: {HEAD_SHA}
Convention base: {CONVENTION_BASE_SHA}
Run: git diff --name-status {REVIEW_BASE_SHA} {HEAD_SHA}
Then: git diff --stat {REVIEW_BASE_SHA} {HEAD_SHA}  and  git diff {REVIEW_BASE_SHA} {HEAD_SHA}

## Accepted-spec authority
Accepted spec blob: {ACCEPTED_SPEC_BLOB_SHA}
If this is a SHA, confirm it matches the SHA published on the issue, retrieve it with
`git cat-file blob {ACCEPTED_SPEC_BLOB_SHA}`, and read that blob itself as authority. Do not compare
it with the spec in the diff: an implementation PR legitimately flips that copy from accepted to
committed. If it is `NONE`, no document may be admitted on “the accepted spec.” A mismatch with the
issue, an unfilled value, an unreachable blob, or a document admitted on a spec while this says
`NONE` makes the packet incomplete, so Floor check 1 fails.

## CI fallback evidence (if any)
{CI_FALLBACK_COMMENT_OR_NONE}

## Packet and scope integrity
Every placeholder must be filled, every supplied SHA must resolve, and all three diff commands must
run against the supplied review base and head. If not, the claim cannot be checked and Floor check 1
fails. If the CI fallback section says `NONE`, skip it. Otherwise audit the supplied evidence against
its supplied checklist item by item; missing evidence or a missing checklist also fails Floor check 1.

For every documentation path reported as added, copied, moved, renamed, or modified (`A`, `C`, `R`,
or `M`) by the name-status diff, apply this exact admission predicate (a modification is ordinary
only where the predicate says so, never for inherited handoff/session state):

{IN_REPO_WRITES_PREDICATE}

The copied unit must contain both delimiter markers, and its end marker's
declared payload line count must match the lines between them. An unfilled placeholder, a missing
marker, or a mismatched count makes the packet incomplete and fails Floor check 1. For provenance,
the issue contract and accepted-spec slots above carry authority; the report slot is the complete PR
description. Use
`git show {CONVENTION_BASE_SHA}:<path>` to verify what the pinned convention
base actually kept: licensing comes only from that base. Check competing
authorities against what the merge will contain—`{REVIEW_BASE_SHA}`, the head,
and every other candidate—not merely against the older convention base. A
document passing no arm, or competing at the same scope, is work outside the task and fails Floor
check 2.

## Judging contract
Decide in this order:

1. Goal verdict. Did this PR, as a whole, accomplish the issue's goal within its bounds and
done-check? Answer Yes or No first, then give the grounds. Check the evidence: do the commands and
outputs claimed in the PR description match what the diff can support? A defect belongs in these
grounds only when it means the PR did not accomplish the issue's goal.
2. Floor. Apply exactly two checks: (a) the completion claim is backed by evidence—an evidence-free
“done” does not pass; (b) there was no unauthorized irreversible action and no work outside the
task's scope, including files or branches beyond the task—either one fails the PR. Packet integrity
failures are Floor failures as directed above, not another category.
3. Notes. Record everything else observed, including style, peripheral edge cases, and possible
improvements. Notes never affect the verdict. Notes never trigger a re-review; the orchestrator
fixes them in passing or files issues.

Ready to merge is decided by the Goal verdict and Floor only.

## Output format
Open with one line, verbatim in shape: "Reviewer: {REVIEWER_IDENTITY} — reviewed
{HEAD_SHA}" — the agent, the model and effort exactly as invoked, the mode, and
the head you reviewed (e.g. "Codex, <model> at <effort>, read-only — reviewed
<sha>" or "Claude subagent, opus — reviewed <sha>"); the record names the
reviewer and the diff it judged. After that identity line, output exactly these three sections:
### Goal verdict
[Yes | No] — grounds, including whether the PR's claimed commands and outputs were checked against
the diff.
### Floor
1. Evidence-backed completion claim: [Pass | Fail] — grounds.
2. Authorization and scope: [Pass | Fail] — grounds covering both unauthorized irreversible actions
and work outside the task's scope.
Ready to merge: [Yes | No] — decided only by the Goal verdict and these two Floor checks.
### Notes
[Everything else observed, or “None.”] Notes never affect the verdict. Notes never trigger a
re-review; the orchestrator fixes them in passing or files issues.

## Rules
DO: judge the PR as a whole; verify the fulfillment claim against the diff; give a clear verdict.
CLOSE WITH this line, verbatim: "Post this verdict whole on the PR before
acting on it." You are your caller's only reader.
DON'T: let a Note change readiness; review code you did not read; be vague; dodge the verdict.
```

## Two narrow exceptions to "re-run check 1 on the new diff"

`core.md`'s rule is unconditional by default: any change after check 1 re-runs it. Two evidenced,
narrow cases don't — read by *you*, the merging session, not by the reviewer, and not by a worker
deciding whether its own amend needs one: `core.md`'s unconditional statement of the rule is what a
worker acts on, and stays exactly that for a worker. These two cases are the merging session's own
call, made after the fact.

**1. A note's verbatim-quoted fix, on a verdict that was ready to merge.** The verdict must be
**complete** — it states the Goal verdict and both Floor results with their grounds, not a run that
stopped partway — and it must say Goal verdict: Yes with both Floor checks passing. A Note's own
quoted text, applied byte-identical with the diff containing nothing but that Note's quoted text,
closes without a further round. **This does not apply to a Goal-verdict ground or a Floor failure,
ever, regardless of how exact the reviewer's replacement text was** — those still fix, then
re-review. A blocking ground can arrive with quoted replacement text too; applying it without a
fresh review is precisely the bypass this design exists to prevent, and it is why "ready to merge"
is the gate, not "the fix was quoted."

**"Quoted", not "prescribed":** the reviewer must have typed the replacement text out, in its own
fenced block — never a blockquote, never embedded in running prose, and never as one of two candidates
the implementer picks between (both are judgement). *"Fix the wording to be clearer"* or *"and
mirror it in Chinese"* with no Chinese text written does not qualify — verify the observation and
write the Note's fix yourself, the ordinary path. Any adaptation of the quoted text, however small,
voids the exception, as does anything else in the diff — no other file, no other line, including a
co-modification the fix happens to force (a lockfile the quoted file also regenerates counts as
"something else"). Comparison: byte-identical against the verdict's raw comment body as stored on
the PR — the comment titled `## Merge check 1 — round N` for the round being relied on
(`gh api …/comments --jq '.[].body'`, never a rendered view), after stripping the common
leading-whitespace prefix shared by every **non-blank** (empty or whitespace-only counts as blank)
line of the fenced block — nothing else stripped, collapsed, or normalized, so a
Markdown-significant blank line or a trailing two-space hard break stays load-bearing. **The fix
lands as a new commit, never an amend** — an amend orphans `<verdict-SHA>`, the one endpoint a
later reader needs. Evidence to publish: both SHAs (`<verdict-SHA>..<post-fix-SHA>`) and the diff,
so a later reader checks the match directly.

**2. Tree-unchanged fix.** A ground against something outside the merged tree — most commonly the
PR description — is closed by editing that artifact alone, whether it appeared under Goal verdict
or Floor: the reviewed-diff rule was never engaged, because the merged tree never moved.
**Evidence: publish both SHAs, and in a genuine case they are the same commit** — nothing in the
repo was touched, so
`<verdict-SHA>` and `<post-fix-SHA>` are identical. If they differ, something in the tree moved and
this exception does not apply, whatever the tree diff between them shows. An amended commit message
is not covered even though no file changed: it rewrites the durable record, so it is a change to the
record and re-runs check 1. Neither is a rebase, an amend, a commit reorder, or a force-push that
happens to leave the tree identical — SHA equality is
what rules them out; an empty tree diff between two different SHAs does not.

**Neither is available because a reviewer is unavailable, slow, or costly to re-dispatch** —
availability is never the trigger for either, on purpose: keying an exception to it is the
incentive this design has to avoid. A Note's fix merely described (not quoted), a fix needing
one word of judgement, a second line riding along, or any doubt about which case applies — none of
these qualify; re-run check 1, whatever the size of the change.
