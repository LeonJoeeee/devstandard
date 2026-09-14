# 0059 — Self-contained role pages replace the shared core

Status: Accepted (2026-09-14)

## Context

DevStandard delivered `core.md` to every role and added a role-specific page beside it. The apparent
sharing mostly made each role read instructions addressed to another: orchestrators received worker
write, handback and red-check procedures, while workers received commissioning, integration and
release authority. The shared and role pages also restated one another and drifted; four conflicting
workflow or authority statements were live at once.

The cost is recurring rather than local. Every session pays for mis-addressed text, and a stale copy
can send a role to the human or authorize work at the wrong point. One large rewrite would avoid a
temporary file but could leave the merged method internally inconsistent while both role pages and
their delivery carriers changed together.

## Decision

Each role has one self-contained operative page rather than a shared workflow core plus a role
supplement. Focused reference pages still load only when their resident trigger fires.

The change lands in two self-consistent steps:

1. `reference/orchestrator.md` absorbs all orchestrator workflow and authority. `core.md` temporarily
   retains worker-addressed triggers and the rules genuinely shared by both roles.
2. `reference/worker.md` absorbs that remainder and `core.md` is deleted.

Step 1 changes page ownership only: normal orchestrator startup still receives the temporary core
beside the orchestrator page. Step 2 changes the delivery and recovery carriers together with the
worker-page move and core deletion. Claude compaction cannot distinguish a root session from a
native child, so until then its compatibility carrier keeps the temporary worker core and the
core's neutral role-source pointer lets a root orchestrator recover its page.

## Consequences

Orchestrator authority has one operative source after step 1 even though the temporary worker core
is still delivered beside it. Workers remain complete during the interval between the two steps;
step 2 removes the remaining mis-addressed delivery while changing its carriers atomically.

Role-local duplication may increase where both roles genuinely need the same rule; that is cheaper
than giving either role the other's authority. Delivery gates must measure the complete artifact a
role actually receives, and a role page that no longer fits its carrier stops the change rather than
silently losing information.
