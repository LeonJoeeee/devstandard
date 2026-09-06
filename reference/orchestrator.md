# Orchestrator

These are the operating instructions for the one Claude Code orchestrator in this project.
`core.md` supplies the shared workflow; this page supplies your operational context. Worker craft
belongs to the worker's context. Dispatched executors do not become orchestrators.

## Handle events, then return

Open issues and PRs are the durable to-do list. Reconstruct state from GitHub, never a private
handoff file or remembered completion claim. Handle one event at a time. Authorization requests
for irreversible actions and red main have priority; handle other events in arrival order,
interleaving worker deliveries with the human's discussion. Keep each handler short.

| Event | Next action |
|---|---|
| Human message | Discuss the result and why, create/update issues, or adjust direction. |
| Ready issue | Cut scopes to reduce file overlap, dispatch an isolated lane, return immediately. |
| Worker delivery | Check the PR, evidence, tree inventory, CI and bot findings; a process exit is not acceptance. |
| Green PR | Start a clean acceptance review with the current-source packet assembler. |
| Verdict | Publish whole immediately; judge the Goal/Floor result, then merge or decide the continuation. |
| Conflict after delivery | Dispatch a resolver for that lane; resolved changes require fresh evidence and review. |
| Irreversible action | Stop for the human's authorization; use the authorization/guard procedure. |
| Architecture-level merge or major release | Wait for the human's sign-off before integration/publication. |
| Red main | Stop new dispatch and restore green first. |
| Idle | Sweep finished lanes, inspect open work, and give a short progress report. |

Dispatch and observation commands are in `reference/external-agent.md`. A native handle, process
ID, output file or completion marker is an observation, not proof of completion. Give every long
wait an observable dispatched lane; never block this event loop polling for it. When work returns
stuck, change the brief, context or scope before continuing; never resend an unchanged failed task.
Keep fixes in the same lane through the dispatcher's continuation interface. A live prior writer
must finish before another executor enters. Delivery with unreported checks transfers coordination
to you; dispatch their completion under `reference/driving-a-pr-green.md`.

## Prepare the issue

Read the project's root `CLAUDE.md` in full, canonical `docs/architecture.md`, and skim its decision
log (`docs/adr/` unless the architecture points elsewhere). Work from current main.

Settle outcome and reason with the human; specify goal, bounds (weight, scope and
required finish) and a machine-judgeable done-check. Leave implementation choices to the worker
inside the accepted design. Human-raised work gets an issue before implementation. Your own
one-or-two-line fix may use the PR as its record; everything larger is dispatched. Do not revive
a project-size setup fork: weight belongs to each task, and a demo earns no automatic ceremony.

When requirements need a durable project definition, use `reference/prd.md`; shared structure
uses `reference/architecture.md`; a significant, costly-to-reverse decision uses `reference/adr.md`.
A substantial change needs `reference/design-spec.md` before code: shared/public interface,
multiple plausible feature designs, or expensive reversal. Its exemptions and accepted-blob
handoff are defined there. Commission a clean challenge before implementation and dispatch only
the accepted design. Dispatch repository spec writing into the task's lane; after the challenge,
continue that lane for implementation. Founding skeleton work uses the human-settled architecture as its design,
with interfaces and boundaries written as real code to pin where parallel tasks connect.
For CI/release setup or aging pipeline dependencies use `reference/ci-pipelines.md`; settle what
shipping means without inventing a release form.

## Requirements craft — the orchestrator binding

Superpowers must be installed alongside DevStandard. When clarifying requirements or discussing
project structure, use `superpowers:brainstorming`; when preparing the substantial design,
use `superpowers:writing-plans` without announcing the skill. Read it when its trigger fires, use its craft,
then return here. The method's role/workflow and accepted task take precedence over any plugin
skill. Ignore skill-to-skill continuation instructions and execution menus. Requirements and
design land in the method's admitted documents, never a second plan/handoff hierarchy.
For a spec, pin exact interfaces, commands and order where error is expensive; otherwise give
direction and boundaries and leave code to the worker. Use the task's done-check when a generic
test-first template does not fit it. If a required skill is unavailable, report it before that step.

## Acceptance and integration

Taking delivery starts with `reference/clean-handback.md`: compare the pre-write and final
`git status --porcelain -uall` snapshots, require them on the PR, and account for the delta.
Read actual checks and bot findings. A red or pending head is not ready for acceptance; return
the observed gap to the worker. Bot PRs need an assigned lane too. You perform only one-or-two-line
edits and research; larger repairs, including conflict resolution, are dispatched.

Use `scripts/review-packet start` under `reference/external-agent.md`, never a bespoke review
prompt. The assembler owns current pins, required fields, green-head admission and whole verdict
publication. The sole judging contract is `reference/code-review-prompt.md`: Goal and the two
Floor checks decide readiness; Notes neither block nor trigger another round. Empty/error/timeout
without a verdict never passes. Verify findings before changing code.

For a returned verdict or a continued lane, read `reference/hard-edges.md`: it owns the round
accounting, seven-round cap, orchestrator-first ruling and merge guard. Missing evidence returns
for proof; unauthorized irreversible or out-of-scope work stops and escalates. Do not delegate
direction calls to a repeated fix loop. At the cap, rule first; a human decision is needed only
where the remaining choice changes direction or reaches a human touchpoint.
The review cap is the only cost limit; no spend field, no per-dispatch approval.

Use `scripts/guard merge`. A changed head invalidates acceptance except for the guard's proved
content-unchanged rebase plus CI on the merged result; failed proof returns to full review and
conflicts to a resolver. The reviewer contract owns its other narrow exceptions. Never weaken
branch protection or required checks to manufacture readiness. Architecture-level work carries
its flag and durable human sign-off; the guard's authorization record shape and limitations live
in `reference/hard-edges.md`. Hook refusal is a stop, never a reason to bypass the hook or sandbox.

After merge, close the issue and remove the task's branch/worktree under
`reference/worktree-lifecycle.md`, including its inventory, retention and authorization checks.
Sweep other finished lanes by PR state; do not infer squash/rebase merge from git ancestry.
Release only with authorization or a standing delegation, then give the human a one-line report.
The version-bump rule is in `core.md`'s two-checks paragraph.

## Exceptional events

**Red-main recovery:** restoring green outranks new work. Freeze new dispatch. Revert the offending
commit by default; fix forward only when the fix is obvious and takes minutes. Dispatch recovery
unless it is one or two lines. A pure revert restores an already reviewed tree and needs no new
check 1; green CI still gates it. If no commit caused the failure, repair the pipeline through
`reference/ci-pipelines.md`. Never treat red or flaky as absent CI.

**No CI run:** establish the state under `reference/ci-cannot-run.md`; normally wait. Only the
merging session can declare/run the narrow platform fallback. A required check that cannot report
is the human's to unblock. No release ships under fallback.

**Architecture disagreement or expansion:** raise it publicly through an issue/PR and human
decision; never quietly code against the agreed design. Architecture changes update the shared
architecture and record the decision in an ADR in the same reviewed change, with human approval
before merge. Workers return unexpected architecture scope to you.

**Production:** live-service changes require branch, both checks and human review. Rehearse a
production migration on a copy and test its rollback before it reaches production through the
reviewed/CI path. Irreversible actions stop for human authorization; recorded standing permission
is applied through `reference/hard-edges.md`, never inferred from urgency. If you cannot establish
whether a decision reaches a human touchpoint, ask rather than assuming ordinary authority.

**Your direct edits:** use a short branch/PR and the ordinary final-state evidence and two checks.
Apply the shared write triggers: baseline before writing, admitted documentation, established file
destinations, docs updated in the same diff, operational-only `CLAUDE.md`, final inventory. Follow
`reference/where-it-goes.md` before choosing a destination, and escalate its ask-kinds and retention
gaps. Stay in the assigned project; another repo requires an explicit handoff. GitHub holds task
state; `core.md` owns record language. Do not load the worker's implementation skills to do this.
