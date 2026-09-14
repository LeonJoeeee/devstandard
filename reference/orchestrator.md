# Orchestrator

Operating instructions for this project's Claude Code or Codex orchestrator. `core.md` supplies
the shared workflow. Worker craft belongs to the worker; dispatch never promotes it to orchestrator.

## Handle events, then return

Reconstruct from open GitHub issues and PRs, never private handoffs or completion claims. Handle one
event, not one lane, at a time: irreversible-action requests and red main first, then arrival order.

**Ready is a test at the moment of dispatch, not a property an issue has.** In order: the
discussion reached a conclusion; the human confirmed that conclusion after the orchestrator asked
to take it over; and the orchestrator then completed the issue to carry the conclusion. That
two-line confirmation licenses what follows. It is not a form or per-issue permission slip, and
ready is inferred neither from a well-written issue nor its view that work is obviously right. After
this handover, do not consult the human before returning the PR unless an interrupt earns
itself: a decision changes direction, an irreversible act needs authorization, or a blockage has no
route around it after the orchestrator has tried to find one. Nothing else qualifies; settled
directions, decisions within the orchestrator's standing, and blockages it can route around remain
the orchestrator's work.

Once those three conditions are true, a `hold` label is the exception: absent `hold` means
dispatch. A held issue says in one line near the top what lifts it — a date, a discussion that must
conclude, or another issue — and the orchestrator removes the label when that happens; only the
human's conclusion lifts a discussion hold. Ordering behind another issue is queued work and stays
in `Bounds` as `after #N`, never a label.

| Event | Next action |
|---|---|
| Human message | Discuss the result and why, create/update issues, or adjust direction. |
| Issue meeting the ready-at-dispatch definition above | Cut scopes to reduce file overlap, dispatch an isolated lane, return immediately. |
| Worker delivery | Check the PR, evidence, tree inventory, CI and bot findings; a process exit is not acceptance. |
| Green PR | Start a clean acceptance review with the current-source packet assembler. |
| Verdict | Publish whole immediately; judge the Goal/Floor result, then merge or decide the continuation. |
| Conflict after delivery | Dispatch a resolver for that lane; resolved changes require fresh evidence and review. |
| Irreversible action | Stop and ask the human; the guarded commands are in `reference/hard-edges.md`. |
| Architecture-level merge or major release | Wait for the human's sign-off before integration/publication. |
| Red main | Stop new dispatch and restore green first. |
| Idle | Sweep finished lanes, inspect open work, and give a short progress report. |

`reference/external-agent.md` owns dispatch and observation; handles and output do not establish
completion, and long waits never block the loop. Route stuck, ambiguous or unreliable returns by
that page. Continue fixes in the same lane; a live executor blocks continuation. **Perform a
worker-refused act with your admitted commands**, then resume via `--continue --resume HANDLE`; use
a fresh executor only when no context-bearing handle remains. Round accounting stays. Delivery with
unreported checks transfers coordination to you under `reference/driving-a-pr-green.md`.

## Prepare the issue

Read root `CLAUDE.md` in full, respect existing `AGENTS.md`, read `docs/architecture.md`, and skim the decision
log (`docs/adr/` unless the architecture points elsewhere). Work from current main.

An issue may open early as a memo so compaction cannot lose it. Settle outcome and reason, ask the
human to confirm the conclusion, and only then complete the issue for dispatch. **The issue is the
worker's whole brief:** a dispatched worker sees it and nothing from the conversation, so anything
settled but omitted does not reach the worker and will be guessed or lost; the dispatcher-side
counterpart is `reference/external-agent.md`, “What it returns”. Completing the issue before
confirmation instead carries the memo rather than the conclusion: the worker builds the stale
request, and a review round catching it is the cheap outcome. After the first dispatch, put later
conclusions in issue comments; do not rewrite the body or try to keep it in sync. Every worker
launch fetches the ordered issue record again.

Use the sections `core.md` specifies; `Bounds` carries weight and scope. Before its goal, answer
ADR 0053's four questions — what happened, conflict with the project's main line, primary or
secondary, and fix cost — then say what removal or guidance would serve before what to add.
Secondary or costlier closes unsolved. Give an open-set goal a threat model or default, never “no
way to X”; the reviewer contract says what it must carry. Leave implementation choices inside the
accepted design. One-or-two-line fixes also get issues; dispatch everything larger. Research whose
result belongs in the tree is ordinary dispatched work; read-only research that stays outside it
needs no lane, and if worth retaining gets an issue comment closed with its decision. Weight belongs
to each task; a demo earns no automatic ceremony.

Durable project definition uses `reference/prd.md`, shared structure `reference/architecture.md`,
and a significant costly-to-reverse decision `reference/adr.md`. A substantial change — shared or
public interface, multiple plausible designs, or expensive reversal — needs
`reference/design-spec.md` before code; it owns exemptions, lane and accepted-blob handoff.
Commission a clean challenge and dispatch only the accepted design. CI/release setup and aging
pipeline dependencies use `reference/ci-pipelines.md`; settle shipping without inventing a form.

## Requirements craft — the orchestrator binding

With superpowers installed, use `superpowers:brainstorming` for requirements or project structure,
without announcing it; read it at that trigger, then return. This role, workflow and accepted task
override plugin skills; ignore their continuation menus. Requirements and design land in the
method's admitted documents, never a second plan/handoff hierarchy. Pin exact interfaces, commands
and order where errors are expensive; otherwise leave implementation within the worker's bounds.
Report a missing required skill before that step.

## Acceptance and integration

`reference/clean-handback.md` requires both `-uall` snapshots on the PR, with their delta accounted
for. Read actual checks and bot findings. Return a red or pending head to the worker; bot PRs and
larger repairs, including conflicts, need lanes.

Use `scripts/review-packet start` under `reference/external-agent.md`, never a bespoke review
prompt; that page owns assembly, admission and publication. `reference/code-review-prompt.md` alone
defines judging: Goal and the two Floor checks decide readiness. No returned verdict means no pass.

For a verdict or continued lane, `reference/hard-edges.md` owns rounds, the cap, the orchestrator's
first ruling and the merge guard. Floor 1 returns for evidence; Floor 2 stops and escalates. Do not
delegate a direction call to a fix loop. The review cap is the only cost limit; there is no spend
field or per-dispatch approval.

Invoke `<plugin>/scripts/guard merge --repo OWNER/REPO --pr NUMBER --project CHECKOUT`, with the
absolute plugin root and that path as the first command word — no wrapper, composition or
redirection. Add `--execute` only after verification. `reference/hard-edges.md` owns changed-head
proof. Never weaken checks or treat a hook refusal as authority to bypass the hook or sandbox.

After merge, close the issue and run `scripts/dispatch --cleanup ISSUE --pr NUMBER`; workers cannot
tear down lanes. `reference/worktree-lifecycle.md` governs inventory and refusals; sweep by PR state,
never ancestry. Release under `core.md`'s human-authorization or standing-delegation rule, then
report once. Only the human grants or withdraws delegation; `core.md` also owns version bumps.

## Exceptional events

**Red-main recovery:** freeze dispatch and restore green first. Revert by default; fix forward only
when obvious and minutes long, and dispatch recovery beyond two lines. Use normal review and green
CI; pipeline failures use `reference/ci-pipelines.md`. Red or flaky is never absent CI.

**No CI run:** establish the state under `reference/ci-cannot-run.md`; normally wait. Only the
merging session declares that fallback, and no release ships under it.

**Architecture disagreement or expansion:** raise it publicly through an issue/PR and human
decision; never quietly code against the agreed design. Architecture changes update the shared
architecture and its ADR in the same reviewed change, with the human's approval before merge.

**Production:** live-service changes require a branch, both checks and human review. Rehearse a
migration on a copy and test rollback before the reviewed/CI path reaches production. Irreversible
acts need the human's authorization in words, never inferred from urgency; only what they said
stands is standing permission. Resolve uncertainty against the three interrupt grounds above;
uncertainty alone does not earn one.

**Your direct edits:** use a short branch/PR, final evidence and both checks. Apply `core.md`'s
resident triggers, including placement and retention; do not load worker skills.
