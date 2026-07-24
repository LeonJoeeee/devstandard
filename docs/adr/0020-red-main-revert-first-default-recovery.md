# 0020 — Red main: revert-first is the default recovery

Status: Accepted (2026-07-24)

## Context

The two ordered merge gates (0011) — a fresh reviewer, then green CI on the merged result against current main — stop most red mains before they land: nothing merges onto a base that isn't green after the merge. Three vectors still slip past them and turn main red anyway: a flaky or time-dependent test that was green at check 2 and red on the next run; upstream or environment drift that only bites main; and the pipeline aging on GitHub's clock, where deprecated actions and EOL'd runtimes hard-fail on fixed cutoff dates (`howto/cicd.md`, "When CI goes red with no change of yours"). So a red main is a real residual state the method has to answer for, not a hole the gates already close.

Industry treats a red mainline as the single highest-priority item and defaults to reverting the offending commit unless a forward fix is trivially fast — Fowler's ~10-minute rule, DORA, trunkbaseddevelopment.com; near-universal (evidence: `_source/ci-maintenance-industry-alignment.md` §5-A).

An earlier ruling kept broken-main *recovery procedure* out of the method's scope (the report §6 refuted a full "red-main response norm" for core.md). This decision does not reopen that ruling. It narrows it to a single ordering rule — which way to go first — and leaves full recovery-procedure design out of scope exactly as before.

## Decision

core.md gains one bold-led paragraph, mirrored in core.zh-CN.md: if main goes red, restoring green outranks all new work and nothing new is dispatched onto a red main; the default recovery is to revert the offending commit, fixing forward only when the fix is obvious and takes minutes; when no commit is at fault (the pipeline itself aged), there is nothing to revert — fix the pipeline, with a pointer to `howto/cicd.md`.

Revert-first is the default because it is unusually agent-suited: zero-judgment (undo the named commit), seconds-fast, and safe (it returns main to a state that was already green), versus an agent improvising a forward fix on the base every worktree branches from. The no-dispatch-onto-red rule makes the ordering explicit — a red main is a stop-the-line condition, not something to work around.

Rejected: a fuller recovery procedure (still out of scope — the ruling is narrowed, not overturned); placing the rule only in `howto/cicd.md` (it is a dispatch/ordering rule, so it belongs in core.md beside the merge-ownership rules, with the pipeline-aging case delegated to cicd.md).

## Consequences

An agent meeting a red main now has one unambiguous first move instead of improvising, and knows not to pile new work onto a broken base. The core.md paragraph triggers the Chinese mirror and the token-ceiling check — both done and verified, with ample headroom. Cost: about two lines of every-session budget and one more rule for the reader, bounded by keeping the paragraph to the ordering call and delegating the pipeline-aging case to cicd.md. No contradiction with cicd.md's "When CI goes red with no change of yours": that section owns the no-commit-at-fault branch, which this rule explicitly routes to it.
