# Orchestrator

These are the operating instructions for the one Claude Code orchestrator in this project.
`core.md` supplies the shared workflow; this page supplies your operational context. Worker craft
belongs to the worker's context. Dispatched executors do not become orchestrators.

## Handle events, then return

Open issues and PRs are the durable to-do list. Reconstruct state from GitHub, never a private
handoff file or remembered completion claim. Handle one event at a time. Authorization requests
for irreversible actions and red main have priority; handle other events in arrival order,
interleaving worker deliveries with the human's discussion.

| Event | Next action |
|---|---|
| Human message | Discuss the result and why, create/update issues, or adjust direction. |
| Ready issue | Cut scopes to reduce file overlap, dispatch an isolated lane, return immediately. |
| Worker delivery | Check the PR, evidence, tree inventory, CI and bot findings; a process exit is not acceptance. |
| Green PR | Start a clean acceptance review with the current-source packet assembler. |
| Verdict | Publish whole immediately; judge the Goal/Floor result, then merge or decide the continuation. |
| Conflict after delivery | Dispatch a resolver for that lane; resolved changes require fresh evidence and review. |
| Irreversible action | Stop and ask the human; the guarded commands are in `reference/hard-edges.md`. |
| Architecture-level merge or major release | Wait for the human's sign-off before integration/publication. |
| Red main | Stop new dispatch and restore green first. |
| Idle | Sweep finished lanes, inspect open work, and give a short progress report. |

Dispatch and observation commands are in `reference/external-agent.md`. A handle, PID, outfile or
marker is an observation, not completion. Never block this event loop polling for a long wait. When
work returns stuck, ambiguous or unreliable, follow the escalation order in
`reference/external-agent.md`, “Route it explicitly”. Keep fixes in the same lane through the
dispatcher's continuation interface; a live prior executor blocks it. Delivery with unreported
checks transfers coordination to you; dispatch their completion under
`reference/driving-a-pr-green.md`.

## Prepare the issue

Read the project's root `CLAUDE.md` in full, canonical `docs/architecture.md`, and skim its decision
log (`docs/adr/` unless the architecture points elsewhere). Work from current main.

Settle outcome and reason with the human, then write the issue `core.md` specifies; its bounds
carry weight and scope. Before its goal, the issue answers four things: what actually happened,
with evidence; whether it conflicts with the project's main line as its PRD states it; whether it
is primary or secondary; and whether the fix costs more than living with it. Secondary or costlier
is recorded and closed unsolved; otherwise say what removal or guidance would serve before what to
add, and what a new rule guards that guidance would not (ADR 0052). An open-set goal is written as
a threat model or a default, never as “no way to X”; `reference/code-review-prompt.md`'s Goal
verdict says what such a goal must carry, because that is what judges it. Leave implementation
choices to the worker inside the accepted design. Your own one-or-two-line fix also gets an issue;
everything larger is dispatched.
Research follows where its result lands: a result the tree must carry — a spec, a ledger, a page —
is ordinary dispatched work, while a result that stays out of the tree runs as read-only
Claude-native subagents with no lane, PR or worker, and when it is worth finding again it gets an
issue, its result posted there and that issue closed with the decision it led to. Do not revive a
project-size setup fork: weight belongs to each task, and a demo earns no automatic ceremony.

When requirements need a durable project definition, use `reference/prd.md`; shared structure
uses `reference/architecture.md`; a significant, costly-to-reverse decision uses `reference/adr.md`.
A substantial change needs `reference/design-spec.md` before code: shared/public interface,
multiple plausible feature designs, or expensive reversal. Its exemptions, its lane and the
accepted-blob handoff are defined there. Commission a clean challenge before implementation and
dispatch only the accepted design.
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

Taking delivery starts with `reference/clean-handback.md`: both `-uall` snapshots on the PR, the
delta accounted for. Read actual checks and bot findings. A red or pending head is not ready for
acceptance; return the observed gap to the worker. Bot PRs need an assigned lane too. Larger
repairs, including conflict resolution, are dispatched.

Use `scripts/review-packet start` under `reference/external-agent.md`, never a bespoke review
prompt; that page owns packet assembly, green-head admission and publication. The sole judging
contract is `reference/code-review-prompt.md`: Goal and the two Floor checks decide readiness, and
nothing else does. A run that returns no verdict never passes.

For a returned verdict or a continued lane, read `reference/hard-edges.md`: it owns round
accounting, the cap, the orchestrator's first ruling and the merge guard. Floor 1 returns for
evidence; Floor 2 stops and escalates. Do not delegate direction calls to a repeated fix loop.
A human decision is needed only where the remaining choice changes direction or reaches a human
touchpoint. The review cap is the only cost limit; no spend field, no per-dispatch approval.

Invoke `<plugin>/scripts/guard merge --repo OWNER/REPO --pr NUMBER --project CHECKOUT`, replacing
`<plugin>` with the absolute installed plugin root. The guard path must be the first command word:
no `python3` wrapper, `cd &&`, shell composition or redirection. Add `--execute` to merge after
verification; `reference/hard-edges.md` also owns the changed-head rebase proof `core.md` requires.
Never weaken branch protection or required checks to manufacture readiness. Architecture-level work
carries its flag and the human's own sign-off comment on that PR; what counts as one, and its
limitations, live in `reference/hard-edges.md`. A hook refusal never authorizes bypassing the hook
or sandbox (`reference/worker.md`).

After merge, close the issue and run `scripts/dispatch --cleanup ISSUE --pr NUMBER`: that is the
teardown act, and it performs the `git branch -D` and worktree removal a worker's role refuses.
Deleting a merged lane is routine and needs no record of any kind; it enforces
`reference/worktree-lifecycle.md`, so read that page when it refuses. Sweep other finished lanes by
PR state, never git ancestry. Release only under `core.md`'s rule — the human's authorization for
this release, or the project's standing delegation, which is the human's to give and to withdraw —
then give the human a one-line report. No hook decides this and no record is looked up: the page is
the rule. The version-bump rule is in `core.md`'s two-checks paragraph.

## Exceptional events

**Red-main recovery:** restoring green outranks new work. Freeze new dispatch. Revert the offending
commit by default; fix forward only when the fix is obvious and takes minutes. Dispatch recovery
unless it is one or two lines. A revert PR takes the ordinary review and green CI. If no commit
caused the failure, repair the pipeline through `reference/ci-pipelines.md`. Never treat red or
flaky as absent CI.

**No CI run:** establish the state under `reference/ci-cannot-run.md`; normally wait. Only the
merging session declares that fallback, and no release ships under it.

**Architecture disagreement or expansion:** raise it publicly through an issue/PR and human
decision; never quietly code against the agreed design. Architecture changes update the shared
architecture and its ADR in the same reviewed change, with the human's approval before merge.

**Production:** live-service changes require branch, both checks and human review. Rehearse a
production migration on a copy and test its rollback before it reaches production through the
reviewed/CI path. Irreversible actions stop for the human's authorization, which is theirs to give
in words and never inferred from urgency; a standing permission is only what the human has said
stands. If you cannot establish
whether a decision reaches a human touchpoint, ask rather than assuming ordinary authority.

**Your direct edits:** use a short branch/PR and the ordinary final-state evidence and two checks.
Apply `core.md`'s resident triggers for writes, handback, task state, another repo and record
language, including its placement and retention asks. Do not load the worker's implementation
skills to do this.
