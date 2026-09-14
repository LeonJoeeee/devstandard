# Orchestrator

Operating instructions for this project's Claude Code or Codex orchestrator. The shared workflow
section below is part of this page. Worker craft belongs to the worker; dispatch never promotes it
to orchestrator.

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
| Irreversible action | Stop and ask the human; the guarded commands are in this page's Guarded operations section. |
| Architecture-level merge or major release | Wait for the human's sign-off before integration/publication. |
| Red main | Stop new dispatch and restore green first. |
| Idle | Sweep finished lanes, inspect open work, and give a short progress report. |

This page's Dispatching to an executor section owns dispatch and observation; handles and output do not establish
completion, and long waits never block the loop. Route stuck, ambiguous or unreliable returns by
that page. Continue fixes in the same lane; a live executor blocks continuation. **Perform a
worker-refused act with your admitted commands**, then resume via `--continue --resume HANDLE`; use
a fresh executor only when no context-bearing handle remains. Round accounting stays. Delivery with
unreported checks transfers coordination to you under this page's Driving a PR to green section.

## Prepare the issue

Read root `CLAUDE.md` in full, respect existing `AGENTS.md`, read `docs/architecture.md`, and skim the decision
log (`docs/adr/` unless the architecture points elsewhere). Work from current main.

An issue may open early as a memo so compaction cannot lose it. Settle outcome and reason, ask the
human to confirm the conclusion, and only then complete the issue for dispatch. **The issue is the
worker's whole brief:** a dispatched worker sees it and nothing from the conversation, so anything
settled but omitted does not reach the worker and will be guessed or lost; the dispatcher-side
counterpart is this page's Dispatching to an executor section, “What it returns”. Completing the issue before
confirmation instead carries the memo rather than the conclusion: the worker builds the stale
request, and a review round catching it is the cheap outcome. After the first dispatch, put later
conclusions in issue comments; do not rewrite the body or try to keep it in sync. Every worker
launch fetches the ordered issue record again.

Use the sections the shared workflow specifies; `Bounds` carries weight and scope. Before its goal, answer
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

This page's The tree you hand back section requires both `-uall` snapshots on the PR, with their delta accounted
for. Read actual checks and bot findings. Return a red or pending head to the worker; bot PRs and
larger repairs, including conflicts, need lanes.

Use `scripts/review-packet start` under this page's Dispatching to an executor section, never a bespoke review
prompt; that page owns assembly, admission and publication. `reference/code-review-prompt.md` alone
defines judging: Goal and the two Floor checks decide readiness. No returned verdict means no pass.

For a verdict or continued lane, this page's Guarded operations section owns rounds, the cap, the orchestrator's
first ruling and the merge guard. Floor 1 returns for evidence; Floor 2 stops and escalates. Do not
delegate a direction call to a fix loop. The review cap is the only cost limit; there is no spend
field or per-dispatch approval.

Invoke `<plugin>/scripts/guard merge --repo OWNER/REPO --pr NUMBER --project CHECKOUT`, with the
absolute plugin root and that path as the first command word — no wrapper, composition or
redirection. Add `--execute` only after verification. This page's Guarded operations section owns changed-head
proof. Never weaken checks or treat a hook refusal as authority to bypass the hook or sandbox.

After merge, close the issue and run `scripts/dispatch --cleanup ISSUE --pr NUMBER`; workers cannot
tear down lanes. This page's Worktree lifecycle section governs inventory and refusals; sweep by PR state,
never ancestry. Release under the shared workflow's human-authorization or standing-delegation
rule, then report once. Only the human grants or withdraws delegation; the shared workflow also
owns version bumps.

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

**Your direct edits:** use a short branch/PR, final evidence and both checks. Apply the shared
workflow's resident triggers, including placement and retention; do not load worker skills.

## The shared workflow

**DevStandard is your operating instruction. Follow this workflow and your assigned role before acting.**

DevStandard exists to return the human's scarce time. Orchestrator and worker, lanes, worktrees,
packets and gates are means to keep it for direction and judgment, never waiting on machinery. The
human settles what the result should be and why, takes one look before a merge, and authorizes
irreversible acts; everything between is the orchestrator's unattended work. Every issue meeting
`reference/orchestrator.md`'s ready-at-dispatch definition dispatches at once in its own lane; no lane waits for another. Cut scope to reduce file overlap,
never concurrency; only a genuinely broken default branch delays dispatch. What waits for a
returning human is finished work, not a queue: completed PRs, one at a time for yes or no; then new
problems; then new issues. When the human leaves, every such issue dispatches at once.

## Workflow

Human need or an observed problem → conclude discussion → human confirms the handover → **complete
the issue → isolated lane → PR with
final-state evidence → green CI → clean acceptance review → merge → cleanup → authorized release.**
The issue uses nonempty Markdown sections `## Goal`, `## Bounds` (weight and required finish),
and `## Done-check` (machine-judgeable); no unresolved template slots, TBD or TODO.
Clarify a vague goal before dispatch. Every ordinary change gets an issue before work and uses
a branch and PR. Founding bootstrap mechanics: `reference/prd.md`.

**Two checks guard merge:** check 1 judges goal fulfillment and the Floor under
`reference/code-review-prompt.md`; check 2 is green CI on the merged result against current main.
The reviewer receives a green PR and returns a whole verdict for publication on that PR. Neither
check substitutes for the other. The reviewed diff must be the merged diff: a changed head returns
to review unless `reference/orchestrator.md`'s Guarded operations section proves its permitted rebase path; use the guarded merge.
The version bump rides the change PR, with the semver call in its description; a reviewer's
disagreement is a Note, never a separate PR. An unavoidable bare bump PR changing only the
declared version fields needs no issue or check-1 reviewer—CI's lockstep gate is its review, and
guarded merge still applies. Narrow review exceptions live with the reviewer contract.

## The roles interlock

**Human:** owns direction and acceptance criteria, confirms the handover, authorizes irreversible actions, and signs off
before architecture-level merges and major releases. Agents run git and publish the record.
Release needs the human's authorization or the project's standing delegation.

**Orchestrator:** one Claude Code or Codex main session per project; discuss, create issues, dispatch,
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

**Executor choice:** Dispatched work goes to the host's own subagent unless the human's
instruction, for one dispatch or standing until their next, selects Codex instead; gating review
needs a fresh read-only reviewer. Codex uses native workers and independent CLI gating review under
`reference/harness-codex.md`. Read `reference/orchestrator.md`'s Dispatching to an executor section for routing, reviewer
independence, explicit models, fixed dispatch and review packets. Reviewer is a read-only purpose,
with no craft skills; its contract stays in `reference/code-review-prompt.md`. A resolver is a
worker assigned conflicts, never a merger.

## Triggers: read the named page when the situation occurs

| Situation | Act / source |
|---|---|
| Requirements, a substantial design, or a bug/implementation step | Use only your role's skill binding in `reference/orchestrator.md` or `reference/worker.md`; return to this workflow afterward. |
| Before a write | Read the repo's `CLAUDE.md`, architecture and decision log; snapshot the baseline (this page's The tree you hand back section). Admit documentation through `reference/in-repo-writes.md`; place files through `reference/where-it-goes.md`. |
| No established destination for secrets/confidential data, long-lived application state, or a release deliverable; or no durable home for a must-keep artifact | Stop and escalate before writing (`reference/where-it-goes.md`). Never commit or publish secrets. Never invent a destination outside the project or work in another repo without a handoff. |
| New operational knowledge or docs invalidated by the change | Docs ride the same diff; `CLAUDE.md` accepts only commands, environment gotchas, copy-list entries and record language (`reference/repo-claude-md.md`). Task state goes on the issue/PR. |
| Create a worktree or remove a merged/cancelled lane | `reference/orchestrator.md`'s Worktree lifecycle section; before the first in-repo worktree, run `git check-ignore -q .claude/worktrees/probe` and land a missing ignore rule first. Inventory before teardown; disclose durable writes outside the repo and must-keep worktree artifacts. |
| PR opened or delivered | Its owner drives every check green and answers every bot finding (this page's Driving a PR to green section). Unreported is not green; a red seen by the worker is unfinished work. |
| Red or flaky check | `reference/red-check.md`: fix your breakage, repair a deliberately staled assumption visibly, or escalate another owner's failure. Never retry a flake into “green.” |
| Main goes red | Freeze new dispatch; restore green first (`reference/orchestrator.md`, red-main recovery). |
| CI produces no run at all | Escalate; only the merging session may establish the narrow platform fallback in `reference/ci-cannot-run.md`. Slow, queued, flaky and red runs do not qualify. |
| Review return, changed head, conflict, or irreversible operation | `reference/orchestrator.md`'s Guarded operations section and the orchestrator's event loop. Evidence-free completion returns for proof; unauthorized/out-of-scope work stops the lane. |
| Core architecture, live service, or production migration | Escalate to the orchestrator before proceeding; its role reference owns sign-off and production safeguards. |

**Record language:** English for code, comments, docs and GitHub records unless root `CLAUDE.md`
declares otherwise; conversation follows the human, product-facing text its audience. For an
existing non-English record or a human translation, read `reference/repo-claude-md.md`.

Load references only at their triggers; paths here resolve from the delivered plugin root. Report
a problem found in another repo as an issue there; an explicit handoff is required before fixing it.

# Dispatching to an executor

Use the fixed dispatcher for a host-native worker or an explicitly selected CLI executor. The role
source carries the worker contract; its dynamic packet carries the freshly fetched issue body and
ordered non-record comments verbatim, plus lane identity and any explicit inputs/output detail.
Give an implementer write access to its own lane and let it run its loop; reviews and challenges
are read-only. The shared contracts and the role operations are both in
`reference/orchestrator.md` and `reference/worker.md`.

Before a repo's first in-repo worktree, perform the pre-creation ignore check in
this page's Worktree lifecycle section. Verify external review findings before acting on them.

## Native or CLI execution

**Dispatched work goes to the host's own subagent.** The human's instruction selects the executor
instead — for one dispatch, or standing until their next instruction. Explicit CLI execution makes
the other host available: Claude can launch Codex CLI and Codex can launch Claude CLI workers.
Codex CLI also supplies an OS-enforced sandbox; a different vendor supplies independent judgment. The standing choice lives with the
orchestrator that received it, not in any project file.

**Native bindings:** Claude uses `--implementation claude`; Codex uses
`--implementation codex-native` for workers (`reference/harness-codex.md`). Both prepare a spawn
receipt for the caller's actual host tool. Codex native spawn inherits host permissions and cannot
set a per-child read-only sandbox, so its gating review uses `--implementation codex`, the fresh
read-only CLI process. Native reviewer dispatch refuses before writes. Research outside a governed
lane and a worker's internal delegation remain the host's own subagent work.

Gating review or challenge always takes a fresh, independent read-only executor — a separate
process for Codex, a freshly spawned subagent otherwise; put required harness-only evidence in its
packet, never give it session history. For implementation, a hard requirement for Claude's capabilities selects Claude: native on its host, or the explicit `claude-cli` worker path from
Codex. Report an unavailable qualified implementation. A subagent also fits quick
read-only exploration whose answer belongs in the orchestrator context, or a piece smaller than its
brief. Any departure from the human's current choice is explained at handback; gating work has no
such departure.

No executor receives missing task context magically. For a worker, the whole issue is the brief and
the dispatcher fetches it again at every launch and continuation; anything settled elsewhere is
still absent. Standalone live-session lanes and workflow panels are outside the supported
configuration. When Codex is unavailable, use the fallback below only if it preserves the role and
gate properties.

## Route it explicitly — model and effort follow the work

Set the model on every dispatch, and set the reasoning/effort level too where the tool has one.
Use this default ladder by kind of work, with two knobs: **model tier and reasoning effort**
(human ruling, 2026-09-09; ADR 0050). No tier is off-limits: the highest tiers are defaults for
the work that needs them.

| Kind of work | Codex | Claude |
|---|---|---|
| Final ruling on a dilemma, an irreversible judgment, an architecture-level acceptance | `gpt-6-astra` at `xhigh` | `fable` |
| Gating review (check 1, a design challenge) | `gpt-6-astra` at `high` | `opus` |
| Implementation, tests, bug fixing, conflict resolution | `gpt-5.6-sol` at `high` | `opus` |
| Wide scans, first-pass triage, evidence gathering | `gpt-5.6-terra` at `medium` or `low` | `sonnet` |
| Fixed-field extraction, list making, format conversion | `gpt-5.6-luna` at `low` | `haiku` |
| Counting, sorting, hashing and other deterministic operations | a script, not a model | a script, not a model |

The asymmetry is deliberate: the human's cost rationale is that Claude `fable` costs twice `opus`
per token and reviews are frequent, so ordinary Claude check 1 stays at `opus` and `fable` is
reserved for the top row. Codex `gpt-6-astra` is the everyday top and carries ordinary reviews
and design challenges. A gating review never runs below the tier that produced the work it
judges; an architecture-level review runs one tier above, using the top row's model/effort pair.

**Recursion depth never lowers the tier.** Route a subagent's subagent doing hard work by that
work, regardless of depth. When work returns stuck, ambiguous or unreliable, change one thing
in this order and never re-run unchanged:

1. Add the missing context.
2. Raise effort.
3. Raise the model one tier.
4. Cut the task smaller.
5. Take it to the human.

A question whose answer is irreversible or a genuine dilemma escalates straight to the top row.
When a knob is already at its highest setting, proceed to the next available change.
Before downgrading, ask whether a script can do it. Downgrade only for **high-volume,
low-difficulty** work, both knobs together, and only when its output can be checked mechanically
or spot-checked one tier up. The gating-review floor still applies.

A project's root `CLAUDE.md` or the issue naming a model overrides the table; the caller carries
that choice through `--model` and/or `--effort` on `dispatch` or `review-packet start`. The human's own
session model stays outside the method. Claude-native agents use tier aliases, never version
IDs. Every spawn names its model explicitly where the tool offers a model field; a tool with
no model control is the sole exception. The shipped worker and reviewer definitions carry
`model: opus` and `effort: high`; an ad hoc Claude spawn inherits the session's effort when its
tool offers no effort control. An unset model or effort is otherwise an invisible config-file
choice, so name both where supported.

The role TOML printed by `guard codex-config` carries `agents.default_subagent_model` and
`agents.default_subagent_reasoning_effort` matching the gating-review row. Dispatch passes each
assignment as its own `-c` override alongside the fixed role hook. An explicit spawn setting still
takes precedence over these subagent defaults; defaults never remove the explicit-spawn duty.

The dispatcher selects the implementation row for `--purpose worker` and the gating-review row
for `--purpose reviewer` (also `review-packet start`). Codex-native uses the Codex column; Claude
uses the table’s tier alias and its matching shipped role’s effort default. Each explicitly supplied
`--model` or `--effort` wins independently; omitted fields keep that purpose’s defaults. Other kinds
of work still require the caller to classify and pass the table’s settings explicitly.

**The standing setting on these projects is `-m gpt-6-astra -c model_reasoning_effort=high`** — the
human's ruling, effective 2026-09-05 (superseding the 2026-08-26 setting under ADR 0040), stated here
and nowhere else. This dated record describes the gating-review row; purpose selects the row, so
workers use the implementation row. The CI gate checks this single dated record; when changing the
gating row, reconcile the record and its date. Explicit departures are recorded at handback.

## Sandbox by role

A review or a design challenge runs read-only — it has no reason to write, and an OS-enforced
sandbox makes that structural instead of a promise in the prompt. Codex CLI gets write access
scoped to its worktree. Claude CLI uses host/tool permissions with explicit `acceptEdits` and
noninteractive prompts; it does not supply Codex's per-role OS sandbox and cannot serve as a gating
reviewer. A native worker inherits the host's permissions; its dedicated
worktree and role bind where it works, not a per-child sandbox grant. A fresh native conversation
does not change that boundary. A "bypass all sandboxing" mode is never used. If a legitimately-needed action is blocked
by the sandbox, that is a stop-and-tell, exactly like any other blocked action — not a reason to
re-invoke with a looser flag.

## What it returns, and how that reaches the main session

A process-invoked agent returns through the dispatcher's output file. Keep the brief and output in
session scratch, never in the worktree; read the output and post durable evidence to the issue or
PR. Retain CLI lifecycle scratch until lane cleanup as specified below. Claude stdout is captured as JSON Lines by the supervisor. Codex's `-o` file
is written by its CLI outside the sandboxed agent — the measured reason the dispatcher's
scratch is writable even though the agent itself cannot write there (`reference/out-of-repo-writes.md`).
For every rule in `reference/worker.md` that says *return the message in your output to whoever
launched you*, **that file is your output** — the same channel, in a different form. The caller reads that output and publishes durable evidence; do not assume another channel is watched.

Two consequences worth stating, because both have bitten:

- **It cannot ask.** Everything it needs must be in the issue or explicit brief. A `{PLACEHOLDER}`
  left unfilled does not get queried, it gets guessed at or worked around.
- **Anything it could not do comes back as prose, if at all.** Read the returned file before
  treating the task as done, and verify the done-check yourself rather than accepting its report.

## The record says which agent produced the work

Git's author field carries whoever's credentials are configured locally — the human's, for any local
agent. So nothing in the record distinguishes a diff another vendor's agent wrote unless it is put
there: a trailer on the commit, and a line in a review verdict naming its reviewer.

This matters most for a gating review. If a different vendor's independent judgment is the reason to
use one, a record that cannot say which vendor produced a verdict cannot support that reason later.

**This is a discipline expectation with no gate behind it, and it is the kind that fails.** Where
this method has made a rule stick, it did so by putting the instruction where the act falls due
rather than where the work is commissioned (`reference/code-review-prompt.md`). The equivalent here
is to write the attribution into the dispatch brief — so the agent emits it — rather than to
remember afterwards.

## When it is not there

Where the human's choice is Codex, check before dispatching; if the tool is missing,
unauthenticated, or errors out, fall back to your harness's own executor **where it can keep the
gate's properties** — fresh, process-isolated, read-only for a review — and say so where the work
is handed back. That fallback is the caller re-dispatching explicitly under the other
implementation: the dispatcher never substitutes one for the other. Where no available executor
can keep those properties, the gate is **blocked, not lowered**: stop and tell the human. **Its absence
never lowers a bar.** Skipping a review, or accepting a weaker one, because an executor was unavailable is the availability-keyed
exception this method rejects everywhere else.

## Fixed dispatcher

Run the installed plugin's `scripts/dispatch` from the target checkout (Python 3.9+, `git`,
authenticated `gh`; Codex process dispatch supports macOS and Linux). It resolves this page's purpose
routing at runtime. `--implementation claude|codex-native|codex|claude-cli` overrides a default of
`claude`; pass the host
binding or human's standing choice explicitly on each launch. A Codex host uses `codex-native` for
workers and `codex` for gating review. `--implementation codex` where Codex is
not installed refuses plainly rather than falling back, and a Codex startup failure is captured,
never silently retried under another implementation.
The dispatch does not carry superpowers: the role pages' `superpowers:<skill>` pointers resolve
only where that plugin is installed on the executing host, the Codex host included.

```sh
git fetch origin
<plugin>/scripts/dispatch 123 --purpose worker --base origin/main
<plugin>/scripts/dispatch 123 --purpose worker --continue --brief <continuation-file>
<plugin>/scripts/dispatch 123 --purpose worker --continue --pr 124 --brief <continuation-file>
<plugin>/scripts/dispatch 123 --adopt --base origin/main --branch <existing-branch> --worktree <existing-worktree> --pr 124
<plugin>/scripts/dispatch 123 --purpose reviewer --packet <complete-review-packet>
<plugin>/scripts/dispatch 123 --cleanup --pr 124
# Codex host's native worker:
<plugin>/scripts/dispatch 123 --purpose worker --base origin/main --implementation codex-native
```

The issue must contain nonempty Markdown heading sections `Goal`, `Bounds`, and `Done-check`.
Missing fields and unresolved template slots are refused before any lane is created or adopted.
Default-branch CI is an orchestrator event, not a reason to serialize ready lanes: only genuinely
red main delays new dispatch under `reference/orchestrator.md`'s recovery rule; unreported or
pending checks do not. Recovery inside an existing lane stays available while main is red.
Creating or adopting a lane also requires a named `--base`; fetch it first. New branch/worktree
defaults are deterministic and recorded: `task/ISSUE-TITLE` and
`PROJECT/.claude/worktrees/ISSUE-TITLE`, with a sanitized title. Override with
`--branch` and `--worktree`; in-project worktrees must already be ignored. `--project` selects the
target checkout when the command is invoked elsewhere. Its `CLAUDE.md` copy-list and baseline
procedure remain the worker's receipt duties.

For a hand-made lane, `--adopt --base REF --branch B --worktree W [--pr N]` records its identity
without launching an executor or creating a branch/worktree. The explicit branch and linked
worktree must already exist in the target repository; mismatches are refused.
The optional PR must name that branch. Adoption refuses an existing active lane record; subsequent
reviews and continuations use that record as usual. Invoke adoption separately from dispatch.

GitHub issue comments hold the lane identity and each run's implementation, purpose, model, PID or
native-spawn status, and scratch paths. A Codex CLI run uses a Python supervisor started
in a new OS session, with stdin closed and SIGHUP ignored; no external `setsid` or `nohup` is needed.
The child receives its assigned `DEVSTANDARD_ROLE`, so an installed plugin cannot inject the
orchestrator set into that run. JSON stdout gives `output` (final response), `log` (combined process output), and
`completion` (atomic exit-code file). A missing marker means running or lost, never done; read the
response and verify the PR/evidence. Keep the run directory, brief identity, `supervisor.lock` and
completion marker until successful lane cleanup. Output/logs may be archived after durable
publication; remove run scratch best-effort only after cleanup. Early deletion makes a prior run
unknown. The script never deletes arbitrary scratch paths recovered from issue comments.

**Inside a tool with a bounded process lifetime**, use `dispatch ... --implementation codex|claude-cli
--wait`. Keep the same originating tool execution alive with its normal yield/poll mechanism until
it returns. Default detached execution survives SIGHUP, but cannot survive teardown of an enclosing
PID namespace. A subsequent shell waiting on the receipt does not repair that loss. `--wait` returns
one receipt JSON object after atomic completion, including the observed `executor_exit`; a nonzero
executor exit retains output and logs and is not task acceptance. Invalid native, adoption, cleanup
or reconciliation combinations refuse before mutation. Direct dispatch waiting forwards SIGINT/TERM
only to its still-owned supervisor group and observes termination for a bounded interval; an
unobserved exit remains unknown. SIGKILL, namespace teardown and machine loss need not leave a marker.

The pre-acquired advisory `supervisor_lock` stays with the supervisor, never the CLI child. PIDs are
diagnostic only. Valid atomic completion establishes an observed exit; without it, a held lock blocks
reuse as running, and a free or missing lock blocks as lost or unknown. An orphaned CLI may still be
writing after its supervisor disappears, so an unlocked lock never authorizes continuation.

**Lost-run recovery is an ownership attestation**, not an inference from a PID, empty output, lock
absence or URL. Inspect the originating host/process environment, identify this exact run, and
establish that no owned supervisor or executor remains, including any necessary termination and
subsequent absence check. If that inspection is unavailable, remain blocked. Publish the evidence,
then use this standalone action:

```sh
<plugin>/scripts/dispatch 123 --reconcile-lost /exact/recorded/scratch/brief.txt --reason 'Originating-host inspection and result' --evidence https://github.com/owner/repo/issues/123#issuecomment-ID
```

The action resolves exactly one CLI run in the current issue lane and updates only its original
comment to `reconciled-lost`, preserving identity/artifacts and adding reason, evidence and the
caller's ownership claim, not automated verification of the originating-host inspection. It refuses
active locks, valid completion, native or ambiguous targets and conflicting retries. Identical retries are idempotent. Existing locks remain held through revalidation
and publication; missing scratch is not recreated. With no lock, the single-orchestrator ownership
contract and fresh issue read apply; GitHub comment updates are not distributed compare-and-swap.
No exit, output or successful work is inferred. A reconciled run permits fresh continuation only
through all remaining lane/PR/round gates; `--native-finished` cannot clear any CLI run.

The worker prompt expands `reference/worker.md` and appends the issue URL, its freshly fetched body
and every non-dispatch-record comment verbatim in order, plus lane metadata; `--brief` adds required
inputs/output detail. Reviewers reuse the recorded lane, receive the structured `--packet` produced
by `scripts/review-packet assemble`, and run read-only. The dispatcher
validates its template against the current fenced contract, fills reviewer identity from the selected
executor, and renders each slot once. It never scans quoted evidence for template syntax or Diff
headings. Old hand-assembled text packets must be assembled again; they do not identify control slots
unambiguously. **Review packets**, below, owns assembly, green-head admission, and publication.
Continuation requires a `--brief` containing the blocking goal gaps. Before a PR exists,
`--continue --brief FILE` reuses the recorded branch/worktree. Once a PR is recorded or found on
GitHub for that branch, the dispatcher resolves its single open PR when `--pr` is omitted; an
explicit `--pr` must be open and name the lane's branch. A closed recorded PR does not pin its
number, so a replacement from the same branch can continue, while no open PR after delivery still
refuses. A continuation into a delivered lane is gated on the selected PR's review history and
needs the orchestrator's recorded ruling, under the round-accounting contract in
this page's Guarded operations section.
Both forms retain the lane; CLI implementations start a fresh process, while a native continuation
resumes its recorded handle with `--resume` and prepares a fresh executor without one. A live prior
executor blocks another dispatch into the lane.

**Codex-native is a prepared worker spawn.** `--implementation codex-native` writes
`native-spawn.json`, a semantic receipt with format `devstandard-codex-native-v1`, the full worker
role plus task in `message` after a canonical-read preamble, `fresh_conversation: true`, the assigned
`worktree` and native-tool obligations. The absolute `brief` and `brief_sha256` also appear in the
run record; `reference/harness-codex.md`, Native workers, owns the required read and verification.
Its `model` and `reasoning_effort` use the same purpose routing and explicit overrides as Codex CLI dispatch.
It reports `awaiting-agent-tool`, without inventing a handle, PID or completion marker.
Pass the complete message to the actual native tool, using its fresh-conversation setting
(`fork_context=false` in v1 or `fork_turns="none"` in v2), passing the receipt's `model` and
`reasoning_effort` explicitly. A tool without those controls, or rejecting them, is unsupported;
report it rather than substituting inherited settings. Supply the other fields the tool requires.
Record the returned native handle on the issue and use the host's native wait/status tools to
observe it. The script cannot invoke or observe a host tool itself. A child inherits developer
instructions, cwd and permissions even with no forked conversation; the worker must use the named
worktree explicitly. Codex does not load the Claude agent definitions, and this receipt is not
Claude Agent JSON. Reviewer purpose refuses for `codex-native`; `--resume HANDLE` does not. A
finished native child accepts a follow-up and answers with its context intact (probed live on
Codex CLI 0.153.4, issue #352), so a continuation carrying a handle sets `fresh_conversation: false`,
records `resume` in the receipt, and obliges the caller to deliver the message to that existing
child — v1 `send_input`, v2 `followup_task` — instead of spawning one. The resumed child keeps the
model and effort it was spawned with, because neither follow-up tool carries those fields; report a
mismatch rather than respawning silently. The handle lives in the spawning session's agent tree,
so a lost or closed handle is a fresh executor, never an invented one.

**Claude CLI is an explicit worker process.** `--implementation claude-cli` lets Codex dispatch a
Claude worker through the installed, normally authenticated CLI. It loads this plugin for that
process, passes the complete role/task and assigned worktree, and uses explicit `acceptEdits` with
noninteractive permission prompts, without a permission bypass. Model and effort follow the purpose
routing and explicit overrides above. Its tool permissions are not a per-child OS sandbox; the worker
must keep writes in its lane. Reviewer purpose and native resume are unsupported. It uses a fresh
process with no session persistence. Logs and completion follow the Codex CLI observation contract;
the output preserves the emitted Claude event stream as JSON Lines. Read every `result` record and its
`permission_denials`, including results preceding background-agent completion. A denied required
action is blocked and must be surfaced even if the process exits successfully.

**Claude is a prepared spawn, not a shell-launched agent.** With `--implementation claude`, JSON
stdout names an `instruction` file containing the Agent-tool arguments for `devstandard:worker`
or `devstandard:reviewer`. The caller invokes that tool in Claude Code and records its returned
native handle on the issue; the command cannot invoke a tool in another session or observe that
handle. It reports `awaiting-agent-tool`, never a running PID. A Claude worker continuation can
also pass `--resume HANDLE` — the continuation for a handback whose cause is an act the worker's
role refuses (`reference/orchestrator.md`); omit it for a fresh executor. Reviewers always start fresh. Agent
definitions supply Claude's static role; the receipt explicitly supplies the requested model and
effort. If the native tool has no effort control, the shipped role supplies its default; a differing
per-spawn effort request is unsupported and must be reported, not silently claimed as applied.
For a Claude reviewer, the dispatcher verifies locally resolvable review-base, head, and convention-base
pins from the structured slots, then captures
`git diff --name-status`, `git diff --stat`, the full diff, and convention-base blobs for every changed
path (both sides of renames, all extensions). External diff drivers, text conversion, and color are
disabled. Command records preserve exit codes and exact output as arrays of bounded text chunks;
concatenate each array without a separator to recover the original output. An absent convention-base
path retains its failed `git show` result; other command failures refuse dispatch before publication.
The Agent-tool prompt points to `brief.txt` for an IN FULL read: the contract, packet, and evidence are
readable artifacts, without a giant escaped prompt line for the caller to copy. Emitting that
instruction does not exercise the native path.

For either native implementation, `--native-finished` attests that **all outstanding Claude and
Codex-native handles in the recorded lane have finished**. It bypasses their liveness checks for
that operation only; it does not persist completion, clear another lane or bypass a live or unknown
CLI run. Supply it on each subsequent operation needing that attestation, never as a standalone
command. A prepared receipt or a caller's guess is not evidence that a handle finished.

## Review packets

The installed plugin's `scripts/review-packet` uses Python, `git`, and authenticated `gh`. Run it from
the target checkout; `--project` selects another checkout root. Its issue must already have a lane
record matching the PR. The convention base is that lane's pre-work base SHA; the review base and
head are the PR's current GitHub base/head SHAs, fetched and checked locally. The predicate's own
review/convention-base slots receive those pins too, preserving its complete counted payload. Beside
those slots the packet carries the complete issue body as quoted evidence, whole and untruncated;
`reference/code-review-prompt.md` states its standing for the verdict. All observed checks
must pass and classic branch-protection required contexts must be reported. Missing, failing,
pending, cancelled, or skipped checks refuse assembly. GitHub state is re-read to reject changes
during assembly. Configure required checks on the repository; this command never changes protection.

```sh
<plugin>/scripts/review-packet assemble 124 --issue 123 --architecture-level no --output <session-scratch>
<plugin>/scripts/review-packet start 124 --issue 123 --architecture-level no --output <session-scratch>
# Codex host:
<plugin>/scripts/review-packet start 124 --issue 123 --architecture-level no --output <session-scratch> --implementation codex --wait
<plugin>/scripts/review-packet status 124 --issue 123
<plugin>/scripts/review-packet publish 124 --issue 123 --attempt <comment-id>
<plugin>/scripts/review-packet fail 124 --issue 123 --attempt <comment-id> --reason '<why no reviewer launched>'
<plugin>/scripts/review-packet rule 124 --issue 123 --decision continue --reason '<blocking goal gap or missing evidence>'
```

`assemble` writes `packet.json` and the readable `packet.txt` without starting a round. `start`
reassembles from current sources, reserves a review attempt on the PR, invokes the fixed dispatcher,
and returns immediately by default. The returned `attempt` is the PR comment ID. For Codex tool
sessions, `start --implementation codex --wait` keeps the originating invocation alive through
executor completion and synchronous publication, returning the `publication` outcome. The PR attempt
is recorded as dispatched before waiting; this mode starts no detached publisher. Other actions and
native review reject `--wait` before mutation. Default Codex execution's detached return handler
publishes the whole output when its completion marker arrives; a failed process with no verdict is
recorded as a failed attempt rather than a returned verdict — the distinction round accounting turns
on (this page's Guarded operations section). A nonzero executor exit cannot yield acceptance.
Publication replaces the reservation with `## Merge check 1 — round N`, the exact-head metadata,
and the unedited verdict. Repeating `publish` is idempotent. A changed head does not suppress the old
head's verdict or reset the count; that verdict cannot accept the new head.

For Claude — the command-line default — `start` returns the dispatcher's Agent instruction; invoke it and
return the whole result using `publish --attempt ID --verdict FILE`. A start is a dispatch into the
lane and refuses on the same liveness condition as any other (above), so use `--native-finished` on
a subsequent start only under the fixed dispatcher's all-handles-finished attestation.

`--accepted-spec SHA` requires a reachable blob whose SHA was published on the issue, and includes
its contents in the packet; absent that argument the slot is `NONE`. The caller supplies the explicit
`--architecture-level yes|no` classification. `--rebase-result FILE` consumes the guard comparison JSON as
review evidence; it neither computes the comparison nor waives green-head admission or full review.
This ordinary assembler sets CI fallback to `NONE`; a declared fallback remains the merging
session's separate procedure under `reference/ci-cannot-run.md`.

GitHub PR comments are the durable round record; pre-existing numbered check-1 verdicts count too,
so adopting the assembler cannot reset a PR’s cap. An unnumbered legacy heading requires history
reconciliation before dispatch. A returned verdict closes its attempt, and the next
start requires an explicit `rule --decision continue --reason ...`. Notes alone never justify a
round. This page's Guarded operations section states the round-accounting contract these commands enforce — what
consumes a round, the cap, the orchestrator's first ruling, and how each Floor result routes;
`rule --decision` takes `continue`, `merge-as-is`, `rewrite`, `abandon` or `change-route`, and a
ruling is recorded rather than merged. Once the cap is reached every further start refuses.
Directional outcomes, an architecture merge ruling, or `--human-touchpoint`
require `--human-authorization` with the durable GitHub sign-off URL. The caller is responsible for
classifying the touchpoint and verifying the human's authority.

A restarted caller uses `status` and the issue's dispatcher records. If a return handler stopped,
`publish --attempt ID` resumes publication from recorded executor output. If the originating
`start` stopped before recording any run and no reviewer launched, `fail --attempt ID --reason ...`
changes that reservation to the existing failed state so another `start` can retry without consuming
a round. It refuses any attempt carrying a recorded run; those stay on the publication path. For a
lost recorded execution, first use the exact issue-run reconciliation above, then use `publish
--attempt ID`. Publication re-reads that current issue record and releases the matching attempt as failed with
the reconciliation evidence, even if all scratch is missing. Partial output cannot become a verdict;
no executor exit or verdict round is invented. Unreconciled loss stays blocked. A terminated review
caller may leave a running or unknown executor: inspect it and use these same publication/reconciliation paths;
never signal an old receipt's diagnostic PID. A post-exit publication failure retains the real
completion/output for an idempotent `publish` retry without another executor. A verdict too large for one GitHub comment is refused whole with its output retained for
escalation, never truncated. Remove caller assembly scratch after durable publication; retain dispatcher
lifecycle scratch until lane cleanup. Keep the branch and worktree for the merging session.

Cleanup runs from outside the lane. It requires the merged PR's branch and exact head, refuses
tracked, untracked, or ignored leftovers, prints the base-relative commit inventory, then removes
the worktree, deletes the local branch, and prunes. A squash/rebase merge can require `-D`: inspect
the printed inventory and supply `--force-delete` only with the caller's explicit authorization
under this page's Worktree lifecycle section. `--discard` is the caller's explicit discard instruction,
for example for a disposable smoke lane; it does not imply permission to force-delete commits.
Remote branch removal remains the merging caller's duty. Never clean a lane on process exit alone.

## Verified mechanics

The invocations themselves are `scripts/dispatch`'s, above — that script is their operative
statement, and nothing here restates the shape it builds. What follows is verified by use against
`codex-cli` specifically. **Another tool's flags are unverified until someone has run them the same
way.**

Four gotchas, each found by running it and none of them in the tool's help text:

- **Run it in the foreground of the detached supervisor** (the fixed dispatcher above does this). Backgrounded directly, it waits on stdin, echoes the prompt, and exits 0
  having done nothing. `< /dev/null` alone does not fix it.
- **A linked worktree needs both `--add-dir <repo>/.git` and
  `--add-dir <repo>/.git/worktrees/<name>` to commit.** Its `.git` file points into the parent repo,
  and the grant through `.git` is **not recursive**, so the common gitdir grant does not make the
  per-worktree gitdir writable. Without both, the work can complete while every staging or commit
  operation fails. A plain clone has no separate per-worktree gitdir and keeps its single
  `--add-dir <clone>/.git` grant.
- **`-C` and `-s` do not exist on the `review` subcommand**, and that subcommand cannot take a custom
  prompt alongside a base branch. Use plain `exec` and paste this method's own reviewer prompt.
- **Watch the output's shape, not just its content.** Literal `\n` sequences instead of newlines in a
  commit message, and quote characters that do not match the surrounding file, have each appeared on
  some runs and not others. Intermittent is worse than systematic: a merged commit message can never
  be corrected.

## Guarded executor and merge edges

`scripts/dispatch` pins each Codex role's PreToolUse configuration in the invocation itself — and a
hook named in argv is not by itself a live refusal, so enforcement is claimed only from an observed
one. This page's Guarded operations section owns hook trust and what a probe does and does not establish, the role
hook's word-list rule and the residual it deliberately leaves outside, the exact merge/rebase
commands, and the round-accounting contract the review commands above enforce.

# Guarded operations

The installed plugin's `scripts/guard` is the orchestrator's merge entry point. Workers never
merge, release, or apply protection. Python 3.9+, git 2.38+, and authenticated `gh` are required;
the test suite also uses Python 3.11+'s TOML parser. **There is nothing to configure.** The guard
has no settings file: the role hook's words are in its source, `guard merge` reads GitHub itself,
and every check name a command needs comes from that command line.

## Merge and rebase proof

Fetch current objects, then run the read-only check; add `--execute` only as the orchestrator:

```sh
<plugin>/scripts/guard merge --repo OWNER/REPO --pr NUMBER --project CHECKOUT
```

It requires an open PR into the repository's current default branch, that base as an ancestor of
the PR head, conforming protection on that branch or GitHub's exact plan-limit response proving
protection unavailable, and the latest whole Goal Yes / both Floor Pass verdict for that exact
head. **Operative records whose comment row GitHub reports as `OWNER`, `MEMBER`, or
`COLLABORATOR` are admitted.**
`NONE`, `CONTRIBUTOR`, and a missing association are rejected. The association is read from the
existing comments response rather than from configuration or another permissions lookup. This is
a repository-association check, not proof that the publisher's operator is human.
The API merge uses a head-SHA precondition and, where the repository plan supports it, GitHub's
strict protection; a changed base or PR during verification refuses. Keep one orchestrator per PR.
Protection where available and current-source review remain necessary because credentials and
workflow files are not made immutable by this script.
**The merge is a squash**, with the PR title plus `(#PR)` as the commit subject and the verified
head commit's `Claude-Session`, `Codex-Session`, and `Co-authored-by` trailers as its short body.

**GitHub's merge queue stays off.** The reviewed commit has to be the merged commit, and the queue
lands one the server built instead: a commit no reviewer saw, merged without `guard merge` running,
so the verdict binding, the protection check and the head-pinned merge above are all skipped. That
the queue runs the required checks on its own commit does not cover this: what a queue displaces is
check 1 and the guard, not check 2. `guard protection` reports an enabled `merge_queue` rule as
non-conforming.

The PR description must carry `architecture-level: true|false`, or its #203 review record must
carry `architecture: YES|NO`.

After main moves, add `--old-base FULL_SHA --old-head FULL_SHA`. The latest accepted #203 record
must name both old pins. The guard replays the old commits in a disposable clone with rerere and
hooks disabled, refuses conflicts and merge commits, compares every path changed in either PR
diff (including deletions, mode and symlink identity), and requires the replay tree to equal the
new head tree. The bump rides the change PR, so the synchronized manifest version lines are the one
exemption: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` and
`.codex-plugin/plugin.json` must differ only in their `version` value, with equal old and new
versions across all three. Both comparisons read that as no difference, and a replay conflict
confined to those version lines resolves to the new base's value instead of refusing.
Where that exemption is what admits the replay comparison, the guard further requires the new head
to declare a bump against the reviewed head, and its value — read as a dotted numeric release — to
sort above both the reviewed head's and the replay's, so a lane cannot rebase past a merged bump
and then set the manifests back to an older version. The admitted pair rides the proof as
`version_bump`. Any other byte or mode difference on any path still refuses. Submodules refuse for
full review. The caller's refs, index and worktree do not move.
A bare-bump review waiver requires exactly those synchronized version-line changes; a stale or
mismatched manifest, another field, or any mode change takes ordinary review.
The mechanical half can also be inspected independently:

```sh
<plugin>/scripts/guard compare --project CHECKOUT --old-base OLD_BASE --old-head OLD_HEAD --base NEW_BASE --head NEW_HEAD
```

The second layer requires the merged-result check — `merged-result / BASE_SHA / HEAD_SHA`, one
fixed name pinned to both SHAs — on the PR head, and every other check the head reports to be green.
That all-observed-green rule is the whole CI requirement: no list of names is configured anywhere,
so a project cannot be judged against a job it does not have, and silence is never green — a head
reporting no check at all refuses. The CI checks out
GitHub's PR merge ref, verifies both parents against the event, runs the tests, then reports that
identity only after success. `reference/ci-pipelines.md`'s template ships that job; a target project
must carry it around its own test job, because installing the plugin does not install a target's CI.
A missing, red or pending identity refuses. Any failed rebase layer returns to full review,
with a resolver for conflicts. This CLI conservatively requires full review for an amended head
or quoted-Note edit; it does not mechanically implement the older quoted-fix exception.

## Review rounds and dispatch

#203's `devstandard-review-v1` PR comments are the durable attempt/ruling records. The guard reads
them; it does not publish a second round ledger. Returned verdicts consume rounds, including a Floor
failure or a malformed response; an attempt whose process returned no verdict at all does not. At
**7**, the orchestrator rules first; no eighth review or goal-fix continuation is admitted. Floor
check 1 returns the lane for real evidence; Floor check 2 stops it and escalates to the human, and
no `continue` or `merge-as-is` ruling can waive that. `merge-as-is` can settle Goal No but never
waive either Floor, and only while the reviewed head is still green. A continuation needs an
explicit `continue` ruling. An active attempt, missing/duplicate rounds, or a ruling for a different
reviewed head refuses.
`scripts/guard round --repo OWNER/REPO --pr NUMBER` checks admission.

A reservation whose originating `start` stopped before recording any run can be changed to the
existing failed state with `review-packet fail --attempt ID --reason ...`; use it only after that
invocation has stopped and no reviewer launched. It refuses every attempt carrying a recorded run,
so a possible verdict stays on the publication or exact-run recovery path. A failed reservation is
not active and consumes no round; it waives neither the next verdict nor either Floor check.

An accepted head may continue for recovery when it is behind main, with or without a conflict,
or the guard has refused that head. `review-packet rule --decision continue --reason ...` verifies
the base advance against fetched base/head objects. For a guard refusal, add
`--guard-refusal 'observed refusal'`: this is the orchestrator's attestation about the current accepted head,
not an automatic guard run. The ruling records the recovery reason and exact head (and the base
SHA for a base advance); both `start` and worker continuation consume that head-bound record.
An up-to-date accepted head without recovery evidence still refuses: Notes do not authorize a
round. Recovery waives neither the cap, Floor 2, active-attempt checks nor green CI before review.

This history is what `scripts/dispatch` and #203's assembler read — the assembler to reserve and
publish a review round, the dispatcher to admit a delivered lane's continuation. Never reach for a
low-level dispatch that omits round accounting. Both commands and their own refusals are in
this page's Dispatching to an executor section.

## The role hook: one rule per role

`hooks/pre-tool-use --role worker|reviewer|orchestrator` decides one tool call, and it does one
thing: it reads the **command's own text** — here-document bodies and quoted-string contents
removed, substitution bodies still read — and refuses when that text carries one of the role's
words. There is no parsing and no grammar, so **unparseable syntax is never a reason to refuse**,
for any role: an unbalanced quote or an unterminated here-document removes what it can and decides
on the words that remain.

**Text a command carries is not a command.** A file body written with `cat > file <<'EOF'`, a
commit message, an issue body, a search pattern: those words are written or matched, never run,
and the scan does not read them. File content goes through the host's editing tool
(`Write`/`Edit`, `apply_patch`), which the hook never reads at all, so a lifecycle word in the
content of a file is no obstacle to writing it.

**A word matches where it begins at a non-identifier position and ends at one that continues
neither an identifier nor a hyphenated word.** That is the whole boundary rule: `--force` never
reads `--force-with-lease`, `merge` never reads `merged` or `--merged`, `tag` never `--tags`, `rm`
never `rmdir`, and `git merge-base` is not `git merge`. A `gh` write flag is the one exception,
because an option and the value written onto it are a single word to the shell: `-X` still reads
`-XPOST`. A rule of several words matches only where those words stand next to each other, so an
option wedged between them (`git branch -v -D x`) escapes it.

| Role | Refuses a command whose text carries |
|---|---|
| worker | `merge`, `tag`, `release`, `--force`, `branch -D`, `branch --delete`, `push --delete`, `worktree remove`; an `rm` whose first option carries `r` or `R` (or spells `--recursive`) unless every absolute path after it is a real path under `/tmp/` with no `..`; and `push` **only** where the same command also names the default branch |
| reviewer | `push`, `merge`, `tag`, `release`, `delete`, `rm`; and, in a command carrying `gh`, `-X`, `--method`, `-f`, `-F` or `--input` |
| orchestrator | `gh pr merge` and `git merge`, refused with the reason naming the sole admitted merge entry — `<plugin>/scripts/guard merge`, which keeps its own reviewed-head verification, rebase proof and GitHub reads |

The default branch is `main` or `master`, by name. A repository that calls its default branch
something else is outside the worker's push rule, and nothing the hook could read would tell it
otherwise. **Everything else is admitted**: a worker's push to its own task branch, its
`--force-with-lease`, a multi-line
`python3 -c`, a `$(…)` in an argument, a `for` loop, and any composition around them; a reviewer's
`gh pr view`/`gh api` reads and any other read command; and the orchestrator's routine teardown —
deleting a merged branch or worktree — **with no authorization record of any kind**.

**The hook judges commands by word list, and never tool names.** Every tool call that is not a
shell command is admitted for every role, a role's own `Agent` spawn of a subagent included. No
tool allowlist remains anywhere, and that is this page's rule of shape: **a hard limit
— a hook, a guard, a tool denial — is reserved for the very serious or the fully forbidden, and is
always a blacklist of the few acts, never an allowlist of what is permitted** (ADR 0051). A
definition therefore names only what it forbids: `agents/reviewer.md` denies the built-in writers
and is read-only by contract, `agents/worker.md` denies nothing, and Codex CLI enforces its role
sandbox. Native Codex and Claude CLI workers retain host/tool permissions and target their assigned
worktree; neither path supplies a per-child read-only sandbox. A subagent is bound by the hook its own definition declares, or by the spawning
session's where it declares none.

**A refusal is a reminder, not a wall.** A worker that reaches for `merge` has usually forgotten
which lane it is in rather than defected, and the harness hands this text straight back to the
model — so one template per role fills in the word the caller actually wrote, what the role does
instead, the one page to read, and, because the scan is textual and a `grep`, a commit message or
an issue body can spell a word innocently, how to re-spell when the operation was not the intent.
The worker's, in full:

> worker role refuses a command carrying 'merge'. Instead, a worker pushes its own task branch and
> hands the PR back to the orchestrator, which owns acceptance, merge and teardown. Read
> `reference/worker.md`'s Never section. If that operation was not the intent — the word sits in a
> commit message, an issue body or a search pattern — re-spell the command so the word is absent:
> put the text in a file and pass the file (`--body-file`, `-F`, a script), or search with a
> pattern that does not spell it. That detour is legitimate.

The reviewer's sends the caller to `reference/code-review-prompt.md`'s Output format section and
the orchestrator's to `reference/orchestrator.md`'s Acceptance and integration section, naming
`guard merge` as what it does instead. **Re-spelling is a legitimate detour, not an evasion**: the
rule is about the operation a command performs, and a command that merely spells a word performs
nothing. Passing a refused *operation* under another spelling is the evasion, and no role may do
it (`reference/worker.md`).

**Two operations the hook deliberately does not decide.** **Releasing** is not on the
orchestrator's list: its role page says releasing needs the human's authorization or the project's
standing delegation, and the orchestrator follows that page rather than a machine-readable record
of it. And an **orchestrator's push naming the default branch** is admitted with no carve-out and
no condition: founding means those first commits to land there, and once founding has applied
protection GitHub rejects the push server-side, which is the layer that check belongs to
(ADR 0052).

**What is outside this boundary stays outside.** Obfuscation — a word quoted as its own argument
(`git "merge" main`) included — an interpreter script, its script given as a quoted argument or a
here-document (`sh -c "…"`, `bash <<EOF`) included, a forged
local ref, an operation read from runtime data, a subagent spawned deliberately to run what the
spawner's own role refuses, and an MCP tool that acts outside the repository — every role reaches
every server the session has attached, and the hook reads commands, not tool calls — are not
modelled, and no rule here will be added for them: this guards the ordinary case and accepts the
residual (ADR 0051; the limitation ADR 0046 already stated). The remedy for the last is to not
attach such a server to a session that runs workers. What remains is the rest of the guard —
`guard merge`'s reviewed-head verification, branch protection, and the OS sandbox where the
implementation supplies one (this page's Dispatching to an executor section).
**A review finding of that class is a Note**, not a defect.

The worker definition pins a worker hook. The global hook resolves a pinned worker/reviewer role first,
then recognized worker/reviewer agent types, then a dispatched `DEVSTANDARD_ROLE`. An otherwise
unclassified child event with a nonempty `agent_id` and absent or `default` agent type uses the
worker rule; Codex-native children inherit no process role marker. Named Claude research children
retain the parent role, preserving a role’s own-subagents boundary. Codex research children still
take the worker fallback; that residual is accepted. Explicit reviewer bindings take precedence.
Both CLI dispatchers set `DEVSTANDARD_ROLE` only in the child process, overriding any
inherited value: installed startup hooks suppress the orchestrator context, and inherited tool
hooks use the assigned role. This delivery marker is not an authorization mechanism.
Codex CLI dispatch also pins the role in an inline hook configuration at the per-role sandbox
posture this page's Dispatching to an executor section sets, and grants worker network access for git/gh.
`guard codex-config --role worker|reviewer` prints the exact TOML override for inspecting that
hook. Because that hook is the fixed one from the dispatcher's own installation — whose presence
the dispatcher checks before creating a lane — the invocation passes Codex's
`--dangerously-bypass-hook-trust`, intended for automation that already vets hook sources. **The
bypass is invocation-wide, not limited to the fixed role hook.** Before dispatch the caller vets
every effective enabled hook source, including installed plugin hooks. It does not change persisted
trust, and Claude dispatch never receives it.

**The main session owns live executor verification before check 1.** Its Claude probe refused; the
[completed Codex probe on head f5d3c99](https://github.com/LeonJoeeee/devstandard/pull/223#issuecomment-5551952108)
also refused worker merge before execution through the dispatcher's own command, under the pinned
role hook above. That records the tested head; it does not establish enforcement for every command.
Skipped/untrusted hooks are not passing probes. Managed-hook policy can also exclude session hooks.
See the [Codex hook contract](https://developers.openai.com/codex/hooks)
and [Claude hook contract](https://code.claude.com/docs/en/hooks).

`.github/test-hard-edges.py` carries the table above as `REFUSED` and `ADMITTED`, swept across both
tool-input formats and all three roles in five positions: the bare, substitution and `cd … && …`
positions, where every witness must refuse, and the quoted and here-doc positions, where the same
witness must be admitted. A fixture decides identically in a bare directory that is no repository at
all and inside one while every network call fails. The sweep also
asserts every refusal names its role's page and carries the re-spelling sentence. No probe
asserts a refusal for an obfuscated construction — that would encode a boundary this hook does not
claim.

## Founding a repository

Setup starts in an empty directory and needs no bootstrap of any kind: **there is no file to seed
and nothing to fill in.** The founding commits go straight to the default branch, which is what the
orchestrator's word list admits with no carve-out, and the last founding step — applying branch
protection — is what closes that door, server-side, for everyone including the account that opened
it. Founding is the orchestrator's work (`reference/prd.md` has the order).

That the push is admitted is not a claim that it is safe: `--force` and `--delete` are not on the
orchestrator's word list anywhere, and GitHub's branch protection is the layer that rejects a push
to a protected branch. `gh pr merge`, `git merge` and every other role's words keep their refusal
throughout.

## Branch protection

Read-only expected-state check, usable on any branch:

```sh
<plugin>/scripts/guard protection --repo OWNER/REPO --branch main
```

On a free-plan **private** repo, branch protection does not apply, so only the server-side block is
unavailable and convention carries that layer. The same review, CI, reviewed-head, and head-SHA
checks remain required by the method and the guard.
GitHub reports that state as `Upgrade to GitHub Pro or make this repository public`; that exact
plan-limit message — from either the classic-protection or branch-rules read — is the only failed
read the guard admits. The read-only command reports `protection` and `merge_queue` as unavailable
on this repository's plan. `guard merge` carries that result under `branch_protection` in both its
verification and execution records, and `review-packet` handles the same response through its
existing unprotected-repository path. A different failure, including another HTTP 403, refuses:
it does not establish that protection is absent. To make the server-side gate available, make the
repository public or use a paid GitHub plan; otherwise restore permission to read protection.

Human/main session only: append `--apply` to run the documented `gh api --method PUT` payload in
`scripts/guard`, then read it back. **The required contexts come from `--check`, repeated once per
name, and from nowhere else** — `--apply` with no name refuses rather than PUT an empty context
list, which would strip every required check off the branch. Without `--apply` the check is
read-only and needs no name at all: it verifies protection's shape.
The payload also sets strict up-to-date status checks, admin enforcement, no force pushes and no
deletions.
The check also refuses an enabled merge queue (above); because classic protection carries no queue
field, it reads the branch's active rules for a `merge_queue` rule, and an unreadable rules response
refuses rather than passes unless it is the exact plan-limit response above. A merge queue is itself
a ruleset feature, so that response establishes that no queue can exist. `--apply` does not turn a
queue off — that is the human's to do.
The payload sets no review-count or actor restriction; inspect existing extra protection before
using this provisioning command because PUT replaces those fields. Workers never run it.
Classic status protection alone does not prohibit a credential holder from pushing a pre-green
commit directly: PR-only behavior also depends on the role/merge route. It is not a server-side
verification of a Goal/Floor comment. Never weaken protection to manufacture a negative probe.

#204's live negative fixture is `probe/204-unprotected`, created and deleted with `gh` by the worker
under the main session's recorded ruling. Its check refused with HTTP 404 while main's check passed.
That 404 shape is unchanged; unit probes also cover the exact plan limit and other-403 refusal.
Evidence, commands and exit codes belong on the PR; live executor probes and whole check 1 belong
to the main session under the continuation ruling.

# Worktree lifecycle (birth and death)

One task = one branch = one worktree (your role page). This checklist covers both ends of that worktree's life. Adapted where noted from superpowers (MIT, Jesse Vincent) — with the holes its issue tracker exposed closed.

## Birth

0. **Already isolated?** If the harness dropped you into a worktree (`EnterWorktree` or similar), creating another nests a phantom one the harness can't see or clean. Check: `git rev-parse --git-dir` vs `git rev-parse --git-common-dir` — different → you are already in a linked worktree: skip creation and go straight to steps 4–6; detached HEAD there → cut a branch before any PR. Equal → create one below (a plain submodule also shows equal dirs, and creating a worktree there is fine).
1. **Prefer the harness's native worktree tool** (e.g. `EnterWorktree`) if one exists; fall back to `git worktree add`. Never fight the harness.
2. **Base ref is explicit, never implicit HEAD:**
   `git fetch origin && git worktree add <path> -b <branch> origin/main`.
   Branch name states the task (e.g. `task/<short-slug>`); consistent names make orphan-sweeping tractable.
   If `git worktree add` says the branch or path is in use, run `git worktree list`. A dead session's stale *worktree* registration clears with `git worktree prune` — but that does not delete the branch it created, so the retry then fails with `a branch named '<branch>' already exists`. Drop `-b` to resume that branch (`git worktree add <path> <branch>`), or `git branch -D <branch>` first to start it over. A real collision — the branch is checked out elsewhere, or the worktree is locked — is resolved or unlocked first. Never invent a second branch name to evade any of these.
3. The worktree directory must be gitignored (`git check-ignore -q <dir>`) or live outside the repo — and this is checked **before creating** a repo's first in-repo worktree: if `git check-ignore -q .claude/worktrees/probe` fails, land the `/.claude/worktrees/` line through a short-branch PR first, then create.
4. **Copy in the untracked-but-needed files.** A fresh worktree carries only git-tracked files — `.env`, secrets, local config, and seeded data do NOT follow. Copy them from the main checkout per the allowlist in the repo's `CLAUDE.md`, if the repo has one (its "new worktree" section — see `reference/repo-claude-md.md`; e.g. `.env`, `.env.local`; no file, or no such section, means nothing to copy); point at shared dependency caches instead of reinstalling from scratch where you can; and parameterize anything that would collide across parallel worktrees (ports, DB/schema names, docker-compose project names) off the branch name. Without this, the check below fails before you write a line — and that failure looks identical to a red main.
5. **Baseline before anything the task produces:** after the copy-in and before install or tests, take the snapshot this page's The tree you hand back section requires — that page owns the command, where it is published, how its entries are accounted for against the copy-list, and the final comparison.
6. **Confirm the tests pass before writing anything**: install deps, run the suite. A passing start is what lets you blame later failures on your own change. Tests already failing → report and ask, don't build on it.

## Death — trigger: the PR merged, or the human explicitly said discard

1. **Confirm the trigger.** Merged: `gh pr view <n> --json state,mergedAt` — that is the authoritative check, and the only one that answers for a squash- or rebase-merged PR. `git branch --merged main` lists only branches whose tip is a literal ancestor of `main`, so it silently reports a squash- or rebase-merged branch (often the platform's default button) as *unmerged*; never read its silence as "not merged yet". Abandoned: an explicit instruction — never an assumption.
2. **Write back the lesson.** Did this task expose a command, environment gotcha, worktree copy-list entry, or record-language declaration that would have prevented a review finding or worker dead-end? If yes: one line into the repo's `CLAUDE.md` — creating the file if this is its first line — through a short-branch PR like any other change (`reference/repo-claude-md.md`). A design decision goes through the architecture process instead — never a quiet note.
3. **Inventory before deleting:** apply this page's The tree you hand back section — its final delta, and its retention check for anything whose only durable copy is in this worktree — then run `git status --porcelain -uall` (anything remaining?) and `git log @{u}.. --oneline` (unpushed?). Anything found → surface it to the human first; teardown never eats work silently. On the discard path a branch may never have been pushed — `git log @{u}..` then errors (no upstream) and reads as nothing-to-check right before an irreversible `-D`. The trap is not unique to discard: it recurs after merge whenever the platform auto-deleted the remote branch. Inventory base-relative on both paths instead: `git log main..<branch> --oneline`. After a squash- or rebase-merge this lists the branch's own commits even though they merged — same ancestry mechanic as step 1 — so a list matching the merged PR is expected, not a warning. Show it (with branch name and worktree path) to the human and get explicit go-ahead before `git branch -D`.
4. From the **main repo root** (not inside the worktree): `git worktree remove <path>`. Worktree before branch — branch deletion fails while its worktree exists, and removal from inside the worktree fails.
5. `git branch -d <branch>` — safe delete, but do not read it as the gate. It measures against the branch's *upstream* when one still exists, so a squash-merged branch usually deletes with only a `merged to refs/remotes/origin/<branch>, but not yet merged to HEAD` warning; once the upstream is gone it flips to refusing outright, since the tip is not a literal ancestor of `main`. Neither outcome tells you anything about unmerged work — step 3's inventory is the gate, and its go-ahead is what authorizes `-D` when the refusal does fire. Delete the remote branch if the platform didn't: `git push origin --delete <branch>`.
6. `git worktree prune` — self-heals stale registrations.

**Who removes it:** the agent that merges a PR removes that PR's worktree and branch, even though the worker created them. Don't remove a worktree for a task you are neither doing nor merging; a workspace the harness's own tooling or a human created is theirs to clean.

**Sweep for leftovers:** a session sometimes ends before it cleans up — that's the normal way worktrees leak. Whoever merges at main also runs `git worktree list` and removes anything whose task is finished, checking each one's PR state (step 1) rather than `git branch --merged main` — under squash- or rebase-merge that command finds nothing, which is exactly how a leaked worktree survives every sweep. So cleanup gets two chances, not one.

**Mid-task session end:** progress — work in the branch — that must outlive the session is committed to the branch, never left in git-ignored scratch, which is deleted along with the worktree.

# The tree you hand back

Read this before the first task-generated write and again before delivery. The rule covers every doer:
a dispatched worker and a main session working its own short branch.

## Baseline before work

After every declared copy-in, but before install, tests, or anything else the task produces, record:

```sh
git status --porcelain -uall
```

Keep the snapshot in session scratch. Where there is an issue, publish it there immediately so it
survives the session; otherwise publish it in the eventual PR or handback. If the first act creates the
repository, record an empty-tree baseline and publish it on the setup issue once the repository exists.
Work with neither issue nor remote has no durable venue, so the doer keeps and compares the
snapshot itself.

Account for every baseline entry against the repo's worktree copy-list. **Taking over without a
baseline:** treat every current non-copy-list path as unaccounted-for and name it rather than silently
inheriting it.

## Final delta and cleanup

After the final edit, rebase, and done-check run — and before every check-1 or re-review dispatch — run the
same `-uall` command and compare it with the baseline. Publish both snapshots. Every path new since the
baseline and visible to the command is committed when it is material the repo maintains, and otherwise
removed; naming a leftover does not license it. Install and test artifacts are deliberately
post-baseline: if they are not ignored, commit them only when they are material the repo maintains;
otherwise ignore or remove them.

For known disposable untracked worktree paths, preview `git clean -nd -- <path>` and use
`git clean -fd -- <path>` only when every previewed entry is yours and disposable; for task scratch,
use `rm -rf` only with literal absolute targets under `/tmp/`, which is what the worker hook
admits (this page, The role hook).

Delete only paths you created and know are disposable. Anything you did not create or cannot account
for is named, never deleted, and blocks a clean handback until its owner decides whether it is removed,
committed, or deliberately retained. Non-ignored copy-list inputs are removed at teardown only after
confirming the main checkout still holds them. The comparison is about which paths are present, not
their contents. Ignored paths are outside the snapshot's visibility, and an ignored path nobody has
named is outside this promise; a known must-keep artifact is not. **Any kept file whose only durable
copy is in the worktree, however it got there, is named — in the PR, or at handback where there is no
PR — and moved out or discarded before teardown.** Nowhere durable to move it to is the placement
rule's ask, not a reason to leave it (`reference/where-it-goes.md`).

Progress — work in the branch — that must survive a session is committed. A handoff or session-state
document is not a cleanup substitute: whether one can exist at all is governed by
`reference/in-repo-writes.md`, and the ordinary answer is to put that message on the issue or PR.

# Driving a PR to green

Your role page: opening a PR is not done — its opener owns it until every check on it reports green and every review-bot finding is fixed or answered on the PR. Here is what that costs in practice.

**What counts, and what green means.** Every check the PR reports, and every finding a review bot posts on it — static analysis, security scanners, style bots. A check that has not reported is not green: queued is not green, in-progress is not green, and a PR whose checks have not started is not a finished PR. A finding with no fix and no reply is unhandled — the reply on the PR is what lets GitHub alone show it was considered.

**A required reviewer or CODEOWNERS approval is not check 1 and does not satisfy it; it blocks merge like an unreported check.** Name it on the PR; an unresponsive approver routes through "When a check can never go green" — escalate to the human who owns that relationship, never wait silently.

**Bot findings run on the check-1 discipline** — verify first, fix what is right without commentary, refute what is wrong with the evidence (`reference/worker.md`). One difference, and only one: the answer goes on the PR, because no re-review settles a bot. A reasoned dismissal on the PR is a legitimate resolution; silence is not, and neither is obeying a finding you know to be wrong.

**A red check is not an opinion — it is the gate, and there are three states, not two:** your diff caused it, your change deliberately staled the check's assumption, or neither. Which one decides everything that follows, including who owns the fix — `reference/red-check.md`.

**A declared check-2 fallback is not a breach of this rule.** While one is in force there are no checks to drive green, and a required check parked at "Expected — waiting for status to be reported" is that state, not a never-green check to escalate. The fallback's own order governs that merge (`reference/ci-cannot-run.md`); this section resumes at the return.

**Taking delivery transfers this duty; it does not end it.** An unreported check returned with a PR
becomes the orchestrator's to drive, and a PR a bot opened is its to own from the moment it appears.
What the orchestrator does with a delivered PR — the tree inventory, the checks and bot findings,
then dispatching a named gap into the same lane rather than repairing it by hand — is its acceptance
procedure (`reference/orchestrator.md`). A PR the orchestrator opened itself never transferred.

**A rebase that re-decides the diff is not driving green — it is a redesign.** The longer a PR sits on any wait above, the further `main` drifts; past some point "fixing conflicts" means re-deciding the change against code no reviewer has seen. That is the "design must change a lot" stop-trigger (`reference/worker.md`) for whoever holds the PR — a worker, or the main session on a PR that never transferred — and it is escalated, never pushed through as a rewritten diff nobody reviewed.

**Handing back is not finishing.** A check you watched fail is not "unreported" — it is unfinished work, and naming it in a handback does not finish it. What may be handed back is a run that has not reported yet, when the doer genuinely has to return before it does: the PR link, and the unreported checks named. Wait for the run if you can; the handback is the exception, not the exit. Where a worker spawned a worker, that handback rides up the chain like a stop message, and passing it on is each intermediate's job — a summary that quietly drops it leaves the check owned by nobody.

**When a check can never go green.** Someone else's required check that is broken, a job needing a secret this repo does not have, a bot demanding something the human already ruled out. Name it rather than absorb it: post on the PR what you observed and what you tried, hand it to the main session, and the main session takes it to the human. The PR then sits in a stated, visible blocked state — waiting is legitimate only once it is written on the PR. What ends it is a change landed through the ordinary ceremony: a visible, tracked quarantine of a flaky test (`reference/worker.md`), a pipeline fix in its own PR, or the human deliberately editing the required-check list. Never a waiver improvised in chat to get this one PR through — a human's "looks fine" is not a green check, and the one place a human waiver has a defined meaning is the never-*reporting* required check under the check-2 fallback (`reference/ci-cannot-run.md`). And never an agent disabling, deleting or making a check permissive: that does more damage than the merge it was buying. (A check that fails then passes with no code change has not gone green either — that is a flake, not a resolution: `reference/red-check.md`.)
