# 0058 — Human-to-orchestrator handover mirrors orchestrator-to-worker handover

Status: Accepted (2026-09-13). Amends 0057 (defines ready and the authority it transfers).

**Scope: this ADR decides what the method ships.** `reference/orchestrator.md` carries the
operative ready-at-dispatch definition and issue-writing rule; this record carries their structural
reason.

## Context

ADR 0057 made human time the end and required every ready issue to run, but it never defined ready.
Issue creation therefore acted as dispatch permission: an early memo could become work before its
discussion concluded, while an orchestrator could still return ordinary decisions to the human
after work had supposedly been handed over.

The method already has the right shape one level down. The orchestrator gives a worker a complete
brief, the worker has authority inside its bounds without mid-lane interference, and the worker
returns a PR with evidence. The human described the missing upper edge on 2026-09-13: once they and
the orchestrator have aligned and the human confirms the conclusion, authority belongs to the
orchestrator until the PR returns it. The first draft of issue #381 demonstrates both failures: it
was only a memo, and it proposed the per-issue approval stamp the human then rejected.

## Decision

The human-to-orchestrator handover has the same structure as the orchestrator-to-worker handover: a
brief carries everything settled, the receiver has full authority within the settled bounds, and
work returns with evidence. Ready names the conditions at the dispatch moment, in the order
recorded by ADR 0057's amendment; it is not a property an issue acquires or a separate approval
form. `reference/orchestrator.md` owns the full definition, the `hold` exception, queued Bounds, and
the three grounds that can interrupt the authority interval.

The alternatives were rejected at the human's direction. A `ready` label would add a permission
step to every issue and mistake the handover for a stamp. Treating a missing label as not ready
would strand work on a sleeping human, so the only label names the exception: `hold`. Treating issue
creation as readiness would dispatch memos before their conclusions exist.

## Consequences

**The issue is the worker's whole brief.** Conversation does not cross the next handover: the
worker sees the issue body and its comments, and nothing else. Therefore every conclusion must be
written there before the launch that needs it; later conclusions go in comments, and continuation
fetches them without rewriting the body. If a conclusion is absent, the worker guesses or
faithfully builds a stale request; a review round catching the mismatch is the cheap outcome.

**The issue is completed after the human confirms the conclusion, never before.** Issues may open
early as small durable memos, and the discussion that follows supplies most of their contract.
Completing one first freezes the memo at exactly the point when it is least authoritative, so the
worker receives the beginning of the discussion instead of its result. The order is conclude,
confirm, complete, dispatch.

After confirmation the orchestrator owns the work through the PR. Returning a settled direction,
a decision within its standing, or a blockage it can route around makes the human schedule the
work again and breaks the symmetry. Only the interrupt grounds in the operative definition cross
that boundary.

A held memo costs one label and one line stating what lifts it. Queueing remains ordinary scope in
`Bounds`, so no dependency label or second state mechanism is added.
