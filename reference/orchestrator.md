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

Dispatch and observation commands are in `reference/external-agent.md`. A handle, PID, outfile or
marker is an observation, not completion. Give every long wait an observable dispatched lane; never
block this event loop polling for it. When work returns stuck, change the brief, context or scope
before continuing; never resend an unchanged failed task. Keep fixes in the same lane through the
dispatcher's continuation interface; a live prior executor blocks it. Delivery with unreported checks
transfers coordination to you; dispatch their completion under `reference/driving-a-pr-green.md`.

## Prepare the issue

Read the project's root `CLAUDE.md` in full, canonical `docs/architecture.md`, and skim its decision
log (`docs/adr/` unless the architecture points elsewhere). Work from current main.

Settle outcome and reason with the human; the issue carries goal, bounds (weight, scope and
required finish) and a machine-judgeable done-check. Leave implementation choices to the worker
inside the accepted design. Your own one-or-two-line fix also gets an issue; everything larger
is dispatched. Research follows where its result lands: a result the tree must carry — a
spec, a ledger, a page — is ordinary dispatched work, while a result that stays out of the tree
runs as read-only Claude-native subagents with no lane, PR or worker, and when it is worth finding
again it gets an issue, its result posted there and that issue closed with the decision it led to.
Do not revive a project-size setup fork: weight belongs to each task, and a demo earns no automatic
ceremony.

When requirements need a durable project definition, use `reference/prd.md`; shared structure
uses `reference/architecture.md`; a significant, costly-to-reverse decision uses `reference/adr.md`.
A substantial change needs `reference/design-spec.md` before code: shared/public interface,
multiple plausible feature designs, or expensive reversal. Its exemptions and accepted-blob
handoff are defined there. Commission a clean challenge before implementation and dispatch only
the accepted design. Dispatch repository spec writing into the task's lane; after the challenge,
continue that lane for implementation. Founding setup owes no separate spec; its mechanics,
including what the first skeleton pins, are `reference/prd.md`'s.
For CI/release setup or aging pipeline dependencies use `reference/ci-pipelines.md`; settle what
shipping means without inventing a release form.

## Requirements craft — the orchestrator binding

DevStandard assumes superpowers is installed alongside it. When clarifying requirements or discussing
project structure, use `superpowers:brainstorming` without announcing the skill. Read it when its
trigger fires, use its craft, then return here. The method's role/workflow and accepted task take
precedence over any plugin skill. Ignore skill-to-skill continuation instructions and execution
menus. Requirements and design land in the method's admitted documents, never a second plan/handoff
hierarchy. For a spec, pin exact interfaces, commands and order where error is expensive; otherwise
give direction and boundaries and leave code to the worker. If a required skill is unavailable,
report it before that step.

## Acceptance and integration

Taking delivery starts with `reference/clean-handback.md`: both `git status --porcelain -uall`
snapshots go on the PR, with the delta accounted for. Read actual checks and bot findings. A red or
pending head is not ready for acceptance; return the observed gap to the worker. Bot PRs need an
assigned lane too. Larger repairs, including conflict resolution, are dispatched.

Use `scripts/review-packet start` under `reference/external-agent.md`, never a bespoke review
prompt; that page owns packet assembly, green-head admission and publication. The sole judging
contract is `reference/code-review-prompt.md`: Goal and the two Floor checks decide readiness, and
nothing else does. A run that returns no verdict never passes. Verify findings before changing code.

For a returned verdict or a continued lane, read `reference/hard-edges.md`: it owns round
accounting, the cap, the orchestrator's first ruling and the merge guard. Floor 1 returns for
evidence; Floor 2 stops and escalates. Do not delegate direction calls to a repeated fix loop.
A human decision is needed only where the remaining choice changes direction or reaches a human
touchpoint. The review cap is the only cost limit; no spend field, no per-dispatch approval.

Invoke `<plugin>/scripts/guard merge --repo OWNER/REPO --pr NUMBER --project CHECKOUT`, replacing
`<plugin>` with the absolute installed plugin root. The guard path must be the first command word:
no `python3` wrapper, `cd &&`, shell composition or redirection. Add `--execute` to merge after
verification (`reference/hard-edges.md`). A changed head invalidates acceptance except through the
guard's rebase proof in `reference/hard-edges.md`; the reviewer contract owns its other narrow exceptions. Never
weaken branch protection or required checks to manufacture readiness. Architecture-level work carries
its flag and durable human sign-off; the guard's authorization record shape and limitations live
in `reference/hard-edges.md`. A hook refusal never authorizes bypassing the hook or sandbox
(`reference/worker.md`).

After merge, close the issue and run `scripts/dispatch --cleanup ISSUE --pr NUMBER`: that is the teardown
act, and it performs the `git branch -D` and worktree removal your own role refuses. It enforces
`reference/worktree-lifecycle.md`'s inventory, retention and authorization checks; read that page
when it refuses. Sweep other finished lanes by PR state, never git ancestry.
Release only with authorization or a standing delegation, then give the human a one-line report.
The version-bump rule is in `core.md`'s two-checks paragraph.

## Exceptional events

**Red-main recovery:** restoring green outranks new work. Freeze new dispatch. Revert the offending
commit by default; fix forward only when the fix is obvious and takes minutes. Dispatch recovery
unless it is one or two lines. A revert PR takes the ordinary review and green CI. If no commit
caused the failure, repair the pipeline through `reference/ci-pipelines.md`. Never treat red or
flaky as absent CI.

**No CI run:** establish the state under `reference/ci-cannot-run.md`; normally wait. Only the
merging session can declare/run the narrow platform fallback. A required check that cannot report
is the human's to unblock. No release ships under fallback.

**Architecture disagreement or expansion:** raise it publicly through an issue/PR and human
decision; never quietly code against the agreed design. Architecture changes update the shared
architecture and its ADR in the same reviewed change, with the human's approval before merge.
Workers return unexpected architecture scope to you.

**Production:** live-service changes require branch, both checks and human review. Rehearse a
production migration on a copy and test its rollback before it reaches production through the
reviewed/CI path. Irreversible actions stop for human authorization; recorded standing permission
is applied through `reference/hard-edges.md`, never inferred from urgency. If you cannot establish
whether a decision reaches a human touchpoint, ask rather than assuming ordinary authority.

**Your direct edits:** use a short branch/PR and the ordinary final-state evidence and two checks.
Apply `core.md`'s resident write and handback triggers, including its placement and retention asks.
Stay in the assigned project; another repo requires an explicit handoff. GitHub holds task state;
record-language details are in `reference/repo-claude-md.md`.
Do not load the worker's implementation skills to do this.
