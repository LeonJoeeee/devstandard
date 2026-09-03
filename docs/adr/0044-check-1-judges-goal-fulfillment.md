# 0044 — Check 1 judges goal fulfillment; peripheral observations are notes

Status: Accepted (2026-09-02). Amends 0011 (check 1's judging semantics) and 0035 (the
quoted-fix exception's vocabulary and qualifying verdict).

## Context

PRD pain point 4 attributes goal drift to two causes: repeated revision and a review instrument
that rewards peripheral findings. Check 1's prompt made goal fit one of ten co-equal categories,
then made a severity-ranked issue list the verdict's spine. That structure paid reviewers to perfect
details even when the PR had already accomplished its issue's goal.

The human's goal-centric constitution instead makes the issue's goal the object of review and the
diff evidence. The only hard floor the human approved comes directly from PRD success criteria 2
and 3: completion claims need evidence, and unauthorized irreversible or out-of-scope work fails.

## Decision

`reference/code-review-prompt.md` is the single operative contract for check 1. Its verdict has a
Goal verdict, the two-check Floor, and non-blocking Notes; merge readiness is decided only by the
first two. The severity ladder and the ten-category checklist no longer structure the verdict.

`core.md` and `reference/worker-brief.md` carry only the trigger and pointer. The prompt's existing
review-base, convention-base, accepted-spec, and in-repo-writes packet checks remain because a broken
packet prevents a complete judgment.

## Consequences

Review now optimizes for fulfillment of the issue rather than the production of findings. Style,
peripheral edge cases, and improvements remain visible without gaining power to block or create a
review round. ADRs 0011 and 0035 retain their ordered gates and reviewed-diff mechanics, with their
live instructions amended to the new contract's vocabulary.
