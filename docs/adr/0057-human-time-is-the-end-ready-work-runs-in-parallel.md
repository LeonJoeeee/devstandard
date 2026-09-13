# 0057 — Human time is the end; ready work runs in parallel

Status: Accepted (2026-09-13)

**Scope: this ADR decides what the method ships.** It makes the project's purpose operative in the
page every session receives and decides what that purpose requires of dispatch.

## Context

From 2026-09-06 through 2026-09-13, this repository ran every lane one at a time. Issue #358, a
defect that could leave Codex review verdicts ungrounded, waited ten hours behind unrelated work
because the orchestrator invented a rule that a new lane waits for the previous one to finish. The
human returned after that unattended interval to find a queue still being worked and had to keep
waiting. Their ruling was that a method which still serializes work after being given enough time
has failed.

The principle was already present in `docs/PRD.md`: §1.1 names forced human scheduling as the
problem, and §3 says N workers process N issues in parallel. But `core.md`, the page every session
receives, described the division of labour without stating its purpose. When the mechanism and its
unstated purpose came apart, the mechanism won. `reference/orchestrator.md` also said to handle one
event at a time without distinguishing serial attention from the number of live lanes.

## Decision

**The end is the human's time; everything else is a means.** Orchestrators and workers, lanes,
worktrees, packets and gates exist so the human spends scarce time on direction and judgment, not
waiting on machinery.

The human has three touchpoints: settle what the result should be and why; look once before a
merge; authorize an irreversible act. Everything between belongs to the orchestrator and runs
unattended.

Every ready issue is dispatched at once in its own lane, and no lane waits for another. The
orchestrator cuts scope to reduce file overlap, never concurrency. Only a genuinely broken default
branch delays dispatch. What waits for a returning human is finished work, not a queue: completed
PRs are presented one at a time for a yes or no, followed by new problems and then new issues; when
the human leaves, all ready work is dispatched at once.

Three behaviors are failures of the method under this decision:

- holding a ready lane because another lane is in flight;
- asking the human to unblock a step that is not direction, acceptance, or an irreversible act; and
- treating “easier for the orchestrator to track” as a reason for any choice.

This decision makes `docs/PRD.md` §1.1 and §3 operative; it implements rather than supersedes them.
The event loop remains single-threaded: one event at a time governs the orchestrator's attention,
not the number of live lanes.

Rejected: leaving the purpose only in the PRD, because the incident showed that a principle absent
from the always-delivered page does not bind. Also rejected: a new gate that attempts to count
parallel work, because dispatchability and useful scope require judgment and the gate would add
machinery in order to defend machinery.

## Consequences

Every session pays a small amount of `core.md` space for the purpose that decides how the rest of
the method is used. The orchestrator can no longer defend serial dispatch as caution or tracking
convenience. Scope cutting still reduces conflicts, but a remaining overlap is handled by the
existing lane, rebase, and resolver workflow instead of making a ready issue wait.

The rule is intentionally not enforced by a new check. Review can recognize serializing ready work
as a failure, while the decision remains about judgment rather than a lane-count metric.
