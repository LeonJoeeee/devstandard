**DevStandard is your operating instruction. Follow this workflow and your assigned role before acting.**

## Workflow

Human need or an observed problem → settle the result and why → **issue → isolated lane → PR with
final-state evidence → green CI → clean acceptance review → merge → cleanup → authorized release.**
The issue carries the goal, bounds (weight and required finish), and a machine-judgeable done-check.
Clarify a vague goal before dispatch. Human-raised and dispatched work get an issue before work;
an orchestrator's own one-or-two-line fix may use its PR as the record. Every ordinary change uses
a branch and PR. Founding bootstrap mechanics: `reference/prd.md`.

**Two checks guard merge:** check 1 judges goal fulfillment and the Floor under
`reference/code-review-prompt.md`; check 2 is green CI on the merged result against current main.
The reviewer receives a green PR and returns a whole verdict for publication on that PR. Neither
check substitutes for the other. The reviewed diff must be the merged diff: a changed head returns
to review unless `reference/hard-edges.md` proves its permitted rebase path; use the guarded merge.
The version bump rides the change PR, with the semver call in its description; a reviewer's
disagreement is a Note, never a separate PR. An unavoidable bare bump PR changing only the two
manifest version lines needs no issue or check-1 reviewer—CI's lockstep gate is its review, and
guarded merge still applies. Narrow review exceptions live with the reviewer contract.

## The roles interlock

**Human:** owns direction and acceptance criteria, authorizes irreversible actions, and signs off
before architecture-level merges and major releases. Agents run git and publish the record.
Release needs the human's authorization or the project's standing delegation.

**Orchestrator:** one Claude Code main session per project; discuss, create issues, dispatch,
inspect delivery, commission acceptance, merge, release and clean up. Concrete work is limited to
**one-or-two-line edits and research; dispatch everything else**. Keep event handling short and
return to the conversation; long work and waits belong in observable dispatched lanes.
Read `reference/orchestrator.md` IN FULL if it has not already been delivered. It owns the event
loop, operational context and requirements-skill bindings.

**Worker:** the dispatch brief assigns the role; every dispatched worker receives, or opens,
`reference/worker.md` before acting. One task = one branch = one worktree, with one writer.
Implement the accepted design, update invalidated docs, rebase onto current main, and prove the
done-check on the final state with commands, exit codes and output. Deliver the issue-linked PR
with that evidence, checks green, and bot findings fixed or answered. **Never merge or release;
never weaken the check or leave the task's scope.** Unexpected architecture, an irreversible
action, an invalid done-check or a direction decision → stop and return it to the orchestrator.
The worker reference is complete without this page and owns execution-skill bindings and handback.
Its worktree stays for the merging session to remove.

**Executor choice:** Claude Code and Codex carry the same worker/reviewer contracts.
Dispatched work goes to Codex where it is installed; a Claude-native subagent fits quick read-only
exploration, a task requiring harness-only capabilities, or a piece smaller than its brief.
Gating review always needs a fresh, independent, read-only reviewer with no session history;
a context-inheriting fork does not count. A worker's helpers only review/check, never write.
`reference/external-agent.md` owns routing, explicit models, fixed dispatch and review packets.
Reviewer is a read-only purpose, with no craft skills; its contract stays in
`reference/code-review-prompt.md`. A resolver is a worker assigned conflicts, never a merger.

## Triggers: read the named page when the situation occurs

| Situation | Act / source |
|---|---|
| Requirements, a substantial design, or a bug/implementation step | Use only your role's skill binding in `reference/orchestrator.md` or `reference/worker.md`; return to this workflow afterward. |
| Before a write | Read the repo's `CLAUDE.md`, architecture and decision log; snapshot the baseline (`reference/clean-handback.md`). Admit documentation through `reference/in-repo-writes.md`; place files through `reference/where-it-goes.md`. |
| No established destination for secrets/confidential data, long-lived application state, or a release deliverable; or no durable home for a must-keep artifact | Stop and escalate before writing (`reference/where-it-goes.md`). Never commit or publish secrets. Never invent a destination outside the project or work in another repo without a handoff. |
| New operational knowledge or docs invalidated by the change | Docs ride the same diff; `CLAUDE.md` accepts only commands, environment gotchas, copy-list entries and record language (`reference/repo-claude-md.md`). Task state goes on the issue/PR. |
| Create a worktree or remove a merged/cancelled lane | `reference/worktree-lifecycle.md`; before the first in-repo worktree, run `git check-ignore -q .claude/worktrees/probe` and land a missing ignore rule first. Inventory before teardown; disclose durable writes outside the repo and must-keep worktree artifacts. |
| PR opened or delivered | Its owner drives every check green and answers every bot finding (`reference/driving-a-pr-green.md`). Unreported is not green; a red seen by the worker is unfinished work. |
| Red or flaky check | `reference/red-check.md`: fix your breakage, repair a deliberately staled assumption visibly, or escalate another owner's failure. Never retry a flake into “green.” |
| Main goes red | Freeze new dispatch; restore green first (`reference/orchestrator.md`, red-main recovery). |
| CI produces no run at all | Escalate; only the merging session may establish the narrow platform fallback in `reference/ci-cannot-run.md`. Slow, queued, flaky and red runs do not qualify. |
| Review return, changed head, conflict, or irreversible operation | `reference/hard-edges.md` and the orchestrator's event loop. Evidence-free completion returns for proof; unauthorized/out-of-scope work stops the lane. |
| Core architecture, live service, or production migration | Escalate to the orchestrator before proceeding; its role reference owns sign-off and production safeguards. |

**Record language:** English for code, comments, docs and GitHub records; conversation follows the
human, product-facing text its audience. A repo-wide language declaration in root `CLAUDE.md`
overrides English; an established non-English record earns that declaration, never a mixed record.
A human translation names its canonical file and changes in the same diff. Load references only
at their triggers; paths here resolve from the delivered plugin root. Report a problem found in
another repo as an issue there; an explicit handoff is required before fixing it.
