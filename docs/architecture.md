# DevStandard — Collaboration-model architecture

> Shared baseline for all parallel work. Read before any task. Changing anything here = touching
> the core: public merge + human approval + an ADR.

This document defines the supplementary harness required by the three target workflows in PRD §4. It
does not repeat those workflows or the working rules held by their role pages. It defines the
roles, context boundaries, delivery paths, enforcement points, and concurrency behavior from which
the rebuild is implemented. Every structure named here is traced to a PRD §1 pain point or a PRD §2
reuse decision in the closing table.

Delivery and enforcement statements use two labels. **Verified** means the behavior was measured or
the artifact was inspected, and names its source. **Unverified** means the architecture requires the
behavior but the rebuild has not demonstrated it. A design requirement is not treated as a fact
about a native harness. Unless a paragraph or evidence cell says **Verified**, mechanisms described
here are **Unverified** target requirements.

## 1. Scope and configuration

The supported configuration is one Claude Code or Codex orchestrator with N dispatched executors. A
dispatched executor has one of two purposes, worker or reviewer. Implementations are Claude-native
subagents, Codex-native workers, Codex CLI processes and Claude CLI workers. A conflict resolver is a
worker assigned a conflict task, not a third role. This is the smallest configuration that removes scheduling from the human while
retaining the GitHub flow and native isolation mechanisms (PRD §1.1, §2.1, §2.2).

DevStandard is a supplementary harness. Each host owns its sessions, hooks, native subagents,
tools, models and permissions; a dispatched Codex CLI process also owns its sandbox. Claude CLI
workers use host/tool permissions and the assigned worktree. DevStandard supplies the
missing collaboration protocol: role context, dispatch, acceptance, and the transitions between
GitHub artifacts. It does not replace either native harness (PRD §1.1, §1.5).

**It governs one layer: the collaboration with GitHub — issue, lane, PR, review, merge — and
nothing below a role.** What a dispatched role spawns beneath itself to finish its own task touches
none of those artifacts, so this design neither names nor requires any such subagent; what it
requires of a lane is that one accountable author hands back one PR (ADR 0055). The gating reviews
above a role — merge check 1 and the pre-code design challenge, both commissioned by the
orchestrator and published on the PR — are inside this layer and unaffected.

ADR 0056 restores Codex host installation on the human's request ([issue #342](https://github.com/LeonJoeeee/devstandard/issues/342)),
superseding ADR 0045's removal. Both hosts use the same core and role sources. Claude Code retains
its native workers; Codex uses its own native workers through prepared `codex-native` receipts.
Codex gating review uses the independent read-only `codex` CLI because native spawning cannot apply
a per-child read-only sandbox. `reference/harness-codex.md` owns this binding. Workers retain their
internal delegation under ADR 0055. Separate live-session lanes, Codex custom agent configuration
and workflow panels are not required (PRD §1.6).

**Verified — repository source:** the plugin has a Codex manifest and marketplace, a shared
SessionStart script with a Codex adapter artifact, and an explicit skill entry. Codex native-worker
receipts carry the complete role and task plus a canonical-file read/digest preamble for the actual
native API. CLI briefs deliver the same role source; their `DEVSTANDARD_ROLE` prevents startup hooks from adding the orchestrator set.
Native host qualification and its remaining boundaries are recorded under **Codex host qualification (2026-09-11, #342)** below.

The durable coordination state is GitHub: issues declare work, branches and worktrees isolate it,
PRs deliver it, review records acceptance, and CI plus branch protection gate integration. Native
task handles, process identifiers, and output files are transient observations, not a second state
machine (PRD §2.1, §2.2).

## 2. Roles and context sets

### Orchestrator

The orchestrator converses with the human, turns a settled result and reason into an issue,
partitions concurrent work, dispatches executors, observes delivery, assembles acceptance reviews,
merges accepted work, and performs cleanup and delegated release. Its context set contains:

- the workflow contract and the three events that wait on the human;
- open-issue, open-PR, CI, branch, and worktree state needed to run the main loop;
- the dispatch, acceptance, merge, cleanup, and reporting triggers with pointers to their operative
  procedures;
- requirements-clarification skill bindings used while discussing direction with the human; and
- the rule that implementation craft and a worker's task-local procedure are not loaded into the
  orchestrator set.

This set keeps the main conversation responsive and stops the human from becoming the scheduler
(PRD §1.1). It delivers assumed working conventions to every new orchestrator session (PRD §1.5)
without mixing in the worker set described below.

### Dispatched executor: purpose × implementation

There is one dispatched-executor construct. Purpose determines its context and authority;
implementation determines how that context is delivered.

| Purpose | Claude-native | Codex-native | Codex CLI | Claude CLI | Result |
|---|---|---|---|---|---|
| Worker | `devstandard:worker` fixes static role, skill bindings and model; dispatch supplies the issue and lane. | Dispatch supplies the full shared role and task, worktree and explicit model/effort for an actual native spawn with fresh conversation. Developer instructions, cwd and permissions remain inherited. | Dispatch supplies the same role/task, explicit settings and a sandbox granting the worktree plus required linked-worktree git metadata. | Explicit worker process with the same role/task and assigned worktree, using host/tool permissions and noninteractive `acceptEdits`, without a sandbox bypass. | A green PR linked to the issue, rebased on current `main`, with final-state evidence. |
| Reviewer | `devstandard:reviewer` fixes the judging role, empty skills, model and denial of built-in writers. The packet supplies the review instance. | Refused before mutation: the native API cannot impose per-child read-only permissions. | Dispatch supplies the judging contract and packet, explicit settings and an OS read-only sandbox. | Refused before mutation: no qualified per-child read-only sandbox. | A verdict naming the reviewer and reviewed head, published whole on the PR. |

The Claude carriers are the whole shipped set of agent definitions, `agents/worker.md` and
`agents/reviewer.md`. A role's own subagents are not a third one: they sit below the governed layer
(§1), so v0.45.0's `devstandard:helper` definition and the pre-handback review it was required for
are removed (ADR 0055).

The routing rule is ADR 0040 as amended by 0056: Claude hosts default to a Claude-native subagent,
and the human's instruction — for one dispatch, or standing until their next — selects Codex
CLI execution instead. Codex hosts bind native workers and CLI gating review as above. Native
receipts require actual spawn/wait tools; a prepared receipt is not a launched worker. The choice
changes delivery, not purpose or obligations. Explicit binding prevents invented working conventions
(PRD §1.5); role-based skill bindings reuse the superpowers library at the step where its craft is needed (PRD §2.3).

### Worker context set

The worker set consists of the static role plus one dynamic task packet.

The static role binds the worker to PRD §4 Workflow 3: one issue, branch, and worktree; write
authority only in that lane; evidence and attribution duties; the NEVER and escalation boundaries;
and the execution-skill triggers, including test-driven development and systematic debugging. The
task packet supplies the issue's goal, reason, bounds, done-check, named base, branch, worktree,
required inputs, and expected output. It carries no merge, release, or orchestration procedure. This
separates execution from integration and makes a worker's claim inspectable rather than trusted
(PRD §1.2, §1.5, §2.3).

### Reviewer context set

Reviewer is the read-only purpose of the dispatched-executor family. Its static set is the judging
contract from issue #183 and PR #188: Goal verdict first, the two-check Floor second, and Notes last.
Only the Goal verdict and Floor decide readiness; Notes neither block nor trigger another review
round. The reviewer has no craft skills because it reads and rules rather than builds (PRD §1.4).

An ordinary review packet contains the issue's goal, bounds, and done-check; the PR description as
the fulfillment claim; explicit review-base and head SHAs; the convention base; the accepted-spec
blob or `NONE`; the architecture-level flag; the CI-configuration paths the diff touches, so a green
run the diff configured cannot vouch for it; the in-repo-write predicate; and CI-fallback evidence
only when the fallback has been declared. Beside those slots it carries the complete issue body as
quoted evidence, the three contract sections still deciding the verdict
(`reference/code-review-prompt.md`). The reviewer sees no orchestrator history and treats
supplied claims as unverified (PRD §1.2, §1.4).

### Resolver

A resolver is a worker whose issue-sized assignment is to rebase a delivered branch that conflicts
with current `main`. It receives the ordinary worker set plus the delivered PR, old and new bases,
the conflicting paths, and the original issue contract. It may change only that lane, reruns the
original done-check on the resolved final state, republishes evidence, and returns the new head for
fresh review. It never receives merge authority (PRD §1.2, §2.2).

## 3. Context delivery

Static role content has one operative source per role: the orchestrator role reference, the worker
role reference, and `reference/code-review-prompt.md` for the reviewer. Agent definitions and
dispatch prompts are delivery carriers, not independently edited copies. `core.md` holds the shared
workflow contract, triggers, and pointers; it does not restate the role pages in full. This
arrangement addresses convention loss without rebuilding another incident-driven rules layer
(PRD §1.5, §1.6).

Rebuild 5's implementation sources are `reference/orchestrator.md` and `reference/worker.md`.
**The one-release compatibility pointer was removed 2026-09-07 (#206, #269)**, so those two are the
only role sources a session resolves. The hook-cap measurement, per-artifact carrier qualification
and source-rule dispositions are recorded in `docs/specs/2026-09-06-core-md-rule-ledger.md`. That
implementation evidence qualifies the dated delivery requirements below; it does not requalify the
unrelated executor/enforcement claims.

Under the human's [delivery ruling](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5550401101),
direct context injection is the default delivery for every static context set. The concrete
mechanism for each artifact—hook inline injection or an instructed read—is chosen at implementation
from the artifact's measured size against the hook's inline cap. **Verified — repository source:**
`hooks/session-start` and `.github/check-core-budget.py` implement the measured per-artifact cap
recorded in the rule ledger above. The two mechanisms have an identical caching profile, so the choice is
about reliability, not caching cost
([measurement and caching record](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5550375489);
PRD §1.5, §5).

The shared reduction applies on both hosts. Codex adds only its bounded adapter artifact and an
explicit skill entry for hookless instruction recovery. The skill is not a self-triggered delivery
guarantee and cannot enable a guard whose hooks are untrusted. Startup, clear and compaction deliver
the shared core and orchestrator set; the adapter also fires on resume and requires full reads of
any shared sources missing from an older session. Codex native workers receive SubagentStart, not
main-session SessionStart, and obtain their complete role through dispatch. CLI workers/reviewers
receive the role in their brief and suppress orchestrator startup delivery (PRD §1.5, §1.6).

| Context and executor | Delivery path | Evidence state |
|---|---|---|
| Orchestrator static set | Claude Code's SessionStart hook delivers the static artifacts under the rule above: inline by default, with an instructed read selected only from the re-measured artifact size. `core.md` supplies the workflow entry point, and the same trigger repeats after context clear or compaction. | **Verified — repository source:** `hooks/hooks.json`, `hooks/session-start`, and the local CI hook gates show one output per delivered artifact — the complete artifact inlined when it fits the measured cap and the IN FULL read only when it does not — on the unchanged matcher, and the core-budget gate failing an artifact that does not fit (#258; ADR 0049). Native startup is qualified below; persistent UI lifecycle behavior remains **Unverified**. |
| Codex orchestrator static set | Trusted plugin hooks deliver the same core and orchestrator artifacts plus `reference/harness-codex.md`. The adapter's resume trigger instructs reads of missing shared sources. The explicit `devstandard` skill reads those sources when hooks are unavailable. | **Verified — native startup:** see **Codex host qualification (#342)** below. Persistent UI lifecycle behavior remains **Unverified**; manual invocation does not demonstrate automatic delivery. |
| Claude-native worker static set | The `devstandard:worker` agent definition supplies role identity and model settings, the worker role under the delivery rule above, and execution-skill bindings. | **Verified — [issue #187](https://github.com/LeonJoeeee/devstandard/issues/187) and [issue #179's enforcement-tier ruling](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5488257766):** the recorded native-subagent probe found that a subagent receives neither the session hook nor the method automatically. The current agent definition is qualified below; a model reading the complete role reference remains **Unverified**. |
| Claude-native worker task | The dispatcher validates the issue and lane, then prepares the Agent receipt with base, inputs and output duty. The caller invokes the actual host tool and records its handle. | **Verified — repository source:** `scripts/dispatch` validates fields and publishes the prepared receipt; `.github/test-dispatch.py` covers refusal and lane records. Native runtime qualification is reported separately. |
| Claude-native reviewer static set | The `devstandard:reviewer` agent definition fixes the read-only purpose, judging contract under the delivery rule above, empty skill set, denial of the built-in writers, and model. | **Verified — [issue #179](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5501782986) and [issue #183](https://github.com/LeonJoeeee/devstandard/issues/183#issuecomment-5496822719) role rulings:** reviewer is a worker-family purpose with a separate set and read-only posture. The current definition and writer denial are qualified below; a model reading the complete judging contract remains **Unverified**. |
| Codex-native worker | `scripts/dispatch --implementation codex-native` prepares the full role/task and explicit model/effort, prefixed by the canonical-file read and SHA-256 requirement owned by `reference/harness-codex.md`. The caller forwards these to the actual native tool with history forking disabled, records the returned handle and waits natively. Assigned worktree use is a role duty; native permissions and cwd are inherited. | **Verified — repository source:** `scripts/dispatch` emits a semantic receipt, refuses native reviewers and permits fresh native continuation only. Native API qualification is recorded under **Codex host qualification (#342)** below. |
| Codex CLI worker or reviewer static set | The fixed dispatcher expands the appropriate role reference into the prompt, without depending on Codex agent definitions. It passes explicit model, effort, working directory and sandbox, and sets the child role marker to suppress orchestrator startup context. | **Verified — historical probe:** [issue #187](https://github.com/LeonJoeeee/devstandard/issues/187) and [issue #179](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5501782986) established dispatch-brief delivery for their tested CLI. Installed-plugin role suppression and hook behavior are qualified under **Codex host qualification (#342)** below. |
| Claude CLI worker | `scripts/dispatch --implementation claude-cli` passes the full role/task on stdin, selects the shipped worker definition's model/effort and sets the assigned cwd plus child role marker. It uses noninteractive `acceptEdits`, preserving normal authentication and settings. | **Verified — repository source:** dispatch emits a real process receipt with JSON Lines output, logs and completion. Required-action permission denials must be reported as blocked; no OS sandbox or reviewer support is claimed. Runtime qualification is recorded separately below. |
| CLI worker lifetime | A Python supervisor starts a new OS session on macOS/Linux and ignores SIGHUP. The selected CLI remains foreground inside it, with output captured in session scratch; Codex has closed stdin, while Claude reads the complete brief from a file. Default review publication uses the same lifetime principle. In tool PID namespaces, explicit `--wait` retains the originating invocation through CLI completion and synchronous review publication. No external `setsid` or `nohup` is required. | **Verified — historical probe:** [issue #187](https://github.com/LeonJoeeee/devstandard/issues/187) and [issue #179](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5501782986) established the detached-session requirement. Replacement supervision and publication are qualified under **Codex host qualification (#342)** below. |
| Review instance, either implementation | The review-packet assembler reads current GitHub state, resolves exact SHAs, takes the current reviewer contract, and fills every ordinary-packet slot before dispatch. It refuses a partial packet or a review before the PR is green. | **Verified — [issue #183](https://github.com/LeonJoeeee/devstandard/issues/183) and [PR #188](https://github.com/LeonJoeeee/devstandard/pull/188):** the judging protocol changed while this architecture work was being dispatched, demonstrating that a copied earlier packet can stale under the dispatcher. **Verified — repository source:** `scripts/review-packet` implements current-source assembly, green-head admission and refusal of incomplete slots; `.github/test-review-packet.py` covers these transitions. |

The dispatcher records implementation, purpose, issue, branch, worktree and either process identity
or prepared native status on the issue. For native execution the caller adds the actual returned
handle; the shell dispatcher cannot invent or observe it. That lane record is the observable marker for the
dispatched wait. While a lane is running, native-handle, supervisor-lock, and captured-output checks
feed short event handlers or a dispatched monitor lane; the orchestrator never waits on them inline.
Completion is never inferred from those signals: it is established only by the durable PR,
evidence, verdict, and CI state. A restarted orchestrator reconstructs work from open issues and
PRs; absence of a PR remains "running or lost," not "done" (PRD §1.1, §1.2, §2.1).

**Unverified:** native-subagent status delivery, detached-process observation after orchestrator
restart, and issue-record creation have not been tested as one recovery path.

## 4. Workflow edges and enforcement tiers

The tiers describe how a rule binds:

- **Hard:** a native mechanism refuses an invalid action. Use it for catastrophic and mechanically
  decidable boundaries.
- **Structural:** the harness puts required context or a fixed transition at the act site. The agent
  can still disobey, but omission is not left to memory.
- **Soft:** the role instructions require judgment. Use it only where the decision cannot be made
  mechanically.

The workflow comes first; tiers are assigned to its edges, not used to invent additional workflow.
The worker-side rows below point to PRD §4 Workflow 3 and assign mechanisms to its boundary; they do
not restate the worker's execution.

### Workflow 1: one task

| Step or edge from PRD §4 | Tier and native mechanism | Evidence state |
|---|---|---|
| Discussion → ① issue | **Structural:** the orchestrator set provides the issue fields and the requirements-skill trigger. **Soft:** the human and orchestrator judge the wanted result, reason, bounds, weight, and done-check. | **Verified — repository source:** the orchestrator role supplies these fields and triggers; native startup delivery is qualified below. The use of a skill here is reuse under PRD §2.3, not a claim that a skill can judge completeness. |
| ① issue → ② dispatch / Workflow 3 receipt | **Hard:** the fixed dispatch script refuses a missing issue, goal, bounds, done-check, named base, branch, or worktree. **Structural:** the injected worker set points to Workflow 3's specification check. **Soft:** the orchestrator cuts scope and selects the executor implementation. | **Verified — repository source:** `scripts/dispatch` validates fields and selects the requested implementation; `.github/test-dispatch.py` covers its refusals. This edge exists to prevent evidence-free work and missing conventions (PRD §1.2, §1.5). |
| ② dispatch → Workflow 3 isolated lane | **Hard:** Codex CLI sandboxes restrict filesystem writes; Codex gating reviewers are read-only. **Structural:** native Codex workers inherit host permissions and must target the assigned worktree. A dedicated worktree separates working trees, while the selected role set and task packet bind the worker to Workflow 3 through the agent definition or dispatch prompt. **Soft:** a worker with required shared-git-metadata access still obeys its named-branch boundary. | **Verified — [issue #187](https://github.com/LeonJoeeee/devstandard/issues/187) and [issue #179's delivery finding](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5488257766):** the tested native subagents lacked SessionStart method delivery. **Verified — repository source:** dispatch sets Codex CLI sandbox arguments and lane identity; Claude definitions declare tool restrictions. Native Codex has no per-child sandbox. Live qualification is scoped below. Reuses PRD §2.2. |
| ③ Workflow 3 execution → green delivered PR | **Hard:** Codex CLI sandbox grants scope its process writes, and review assembly refuses acceptance until the current PR checks report green. **Structural:** the worker set binds Workflow 3's act-site obligations to the lane. **Soft:** implementation choices and the truth of non-mechanical evidence remain worker judgment subject to review. | **Verified — repository source:** worker carriers deliver the role or its read instruction and review-packet enforces green-head admission. **Unverified:** the complete live execution-to-handback path. GitHub, CI, and worktrees are reused under PRD §2.1 and §2.2; acceptance addresses PRD §1.2. |
| Delivered green PR → ④ acceptance | **Hard:** the assembler refuses an ordinary review while the current PR head is red or unreported; Codex CLI review is OS read-only and Claude review denies built-in writers. **Structural:** the assembler supplies a complete, current, clean-context packet and the Goal/Floor/Notes output shape. **Soft:** the reviewer judges goal fulfillment and the Floor evidence. | **Verified — [issue #183](https://github.com/LeonJoeeee/devstandard/issues/183) and [PR #188](https://github.com/LeonJoeeee/devstandard/pull/188):** the goal-centric contract and empty-by-design skill set are recorded, and PR #188's CI is green. **Verified — repository source:** `scripts/review-packet` implements green-head admission and packet assembly; `scripts/dispatch` selects the review sandbox. Live role enforcement is qualified separately below. This edge addresses PRD §1.2 and §1.4. |
| ④ accepted head → ⑤ merge and cleanup | **Hard:** branch protection rejects direct main writes; the merge guard requires a Goal Yes/Floor Pass verdict or the permitted orchestrator merge-as-is ruling after both Floor checks pass. If `main` moves after acceptance, the only path without a fresh verdict is a conflict-free rebase for which the comparison script proves every PR-changed path byte-identical — chapter 5's manifest version-line exemption apart — and CI passes on the merged result; both hard layers pass → merge, while either failure falls back to full review and a resolver where needed. **Structural:** the guard records the acceptance anchor and comparison proof; architecture-level status and the human sign-off slot travel in the issue, PR, and review packet. **Soft:** the orchestrator classifies architecture-level work and reads the human's decision. | **Verified — [issue #179's option-A ruling](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5550436875):** the human fixed the two-layer path. **Verified — repository source:** `scripts/guard`, `scripts/hard_edges.py` and `.github/test-hard-edges.py` implement and constructively probe these checks. Target-repository protection and human sign-off still require actual evidence. The hard mechanisms are reused under PRD §2.1 and §2.2. |
| ⑤ merged result → ⑥ delegated release | **Structural:** the orchestrator set requires the human's authorization or the project's standing delegation before releasing, and the one-line report after. **Soft:** the human decides a new delegation or major-release sign-off. | **Unverified:** delivery of the release rule to a fresh orchestrator. Since ADR 0052 this edge has **no hard tier**: the hook does not recognize `tag` or `release`, and no record is looked up. Releasing is judged against PRD §1.3 by the role's page, and that is the ruling, not a gap to close. |

### Workflow 2: orchestrator events

The event-handler paragraph under [PRD §4 Workflow 2](./PRD.md#4-the-solution-the-target-workflows),
tracked in [issue #194](https://github.com/LeonJoeeee/devstandard/issues/194), is the authority for
the loop's semantics rather than this table. The architectural consequence is that every event
handler must be short, and any long wait is a dispatched lane plus an observable marker, never an
inline wait ([human ruling](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5550436875)).

| Event from PRD §4 | Tier and native mechanism | Evidence state |
|---|---|---|
| The human speaks | **Soft:** the orchestrator discusses or adjusts direction. **Structural:** its role set presents the issue-creation and requirements-skill triggers. | **Verified — repository source:** `reference/orchestrator.md` supplies these triggers; host delivery is qualified below. Addresses PRD §1.1 and reuses §2.3. |
| An irreversible action is needed | **Hard:** role hooks reject their listed command words, and the orchestrator's PreToolUse hook refuses `gh pr merge` and `git merge`, routing merges through `guard merge`; GitHub's branch protection rejects a direct push to a protected default branch. **Soft:** the orchestrator identifies every irreversible action the hook's word list does not reach — which since ADR 0051 is deliberately most of them, teardown of a merged lane included, and since ADR 0052 the founding push and the release as well. | **Verified — repository source:** role hooks implement the word lists; live host enforcement is scoped below. Addresses PRD §1.3. |
| Architecture-level change or major release is ready | **Hard:** `guard merge` requires a comment of the repository owner's own on that PR for an architecture-level merge, read from the repository's API record; since ADR 0052 there is no record format and no allowlist, and a release is governed by `core.md` rather than by any lookup. **Soft:** the orchestrator classifies the change and the human decides. | **Verified — repository source:** `scripts/hard_edges.py` checks the architecture flag and owner comment; `.github/test-hard-edges.py` covers admission and refusal. Addresses the irreversible-control concern in PRD §1.3. |
| Issues await dispatch | **Hard:** the dispatcher refuses a new lane while default-branch CI is red and enforces one branch/worktree per task. **Structural:** it creates and records N lanes. **Soft:** the orchestrator cuts scopes to reduce overlap. | **Verified — repository source:** `scripts/dispatch` checks default CI and publishes lane records; `.github/test-dispatch.py` covers these transitions. GitHub, worktrees, and CI are reused under PRD §2.1 and §2.2 to address PRD §1.1. |
| A worker delivers | **Structural:** the orchestrator observes the PR and external state, validates the fulfillment packet, and starts acceptance only when required checks for the current head are green. A red or unreported PR remains on the worker side of the handback edge. **Soft:** a worker report remains a claim until review establishes it. | **Verified — repository source:** `scripts/review-packet` enforces green-head admission. **Unverified:** autonomous observer behavior as a complete live loop. The durable source is GitHub under PRD §2.1; the distrust boundary addresses PRD §1.2. |
| A verdict returns | **Structural:** Goal Yes/Floor Pass advances the reviewed head toward merge; if its base later moves, it enters the two-layer light-review path. Goal No returns only the stated goal grounds to the orchestrator for its per-PR continuation decision. A Floor check 1 failure—an evidence-free completion claim—returns to the worker for real evidence, and the failed review counts as a round. A Floor check 2 failure—an unauthorized irreversible action or out-of-scope work—stops the lane and escalates to the human at the irreversibles touchpoint, with no fix round. A conflict dispatches a resolver. **Hard:** merge waits on exact-head acceptance or a prior acceptance anchor plus both content-unchanged-rebase layers; any failed layer falls back to full review and a resolver where needed. **Soft:** the verdict, the permitted orchestrator ruling, and whether another goal-fix round is useful are judgments. | **Verified — [issue #183](https://github.com/LeonJoeeee/devstandard/issues/183) and [PR #188](https://github.com/LeonJoeeee/devstandard/pull/188):** Goal/Floor/Notes semantics. **Verified — [issue #179's round ruling](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5525395030) and [option-A ruling](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5550436875):** the human fixed the continuation, cap, and base-move paths. **Verified — repository source:** review-packet round accounting, guard rebase proof and dispatch continuation implement the mechanical transitions. **Unverified:** the complete autonomous verdict-to-resolution loop. Addresses PRD §1.2, §1.3, and §1.4. |
| Main goes red | **Hard:** dispatch refuses new starts until default-branch CI is green. **Structural:** the orchestrator set presents revert-first recovery and the relevant procedure. **Soft:** it decides whether an obvious minutes-long fix-forward is safer than revert. | **Verified — repository source:** `scripts/dispatch` refuses new starts on red or unreported default CI; `.github/test-dispatch.py` probes it. CI is reused under PRD §2.1; preventing concurrent work on a bad base supports PRD §1.1. |
| Idle | **Structural:** the main-loop trigger queries open issues, PRs, checks, and worktree records and reports progress. **Soft:** the orchestrator decides whether a leftover needs cleanup or escalation. | **Verified — repository source:** `reference/orchestrator.md` supplies the idle trigger. **Unverified:** sustained autonomous idle handling. Reuses GitHub state under PRD §2.1 to address PRD §1.1. |

### Workflow 3: worker execution

[PRD §4 Workflow 3](./PRD.md#4-the-solution-the-target-workflows) is the authority for the steps; this table assigns their enforcement mechanisms.

| Step or edge from PRD §4 Workflow 3 | Tier and native mechanism | Evidence state |
|---|---|---|
| Receipt → specification check | **Hard:** the fixed dispatch script refuses an unfilled goal, bounds, done-check, named base, branch, or worktree. **Soft:** the worker judges vagueness and returns an underspecified task rather than starting. | **Verified — repository source:** dispatch validates the contract and the worker role begins with the specification check. Host delivery qualification is separate below. |
| Taking position → baseline snapshot | **Hard:** Codex CLI sandbox grants constrain its process writes. **Structural:** the dedicated worktree separates the lane; native Codex inherits host permissions and must use that worktree explicitly. The role set requires the baseline snapshot, and the dispatcher records the lane on the issue. | **Verified — [issue #179's lifetime finding](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5501782986):** detached Codex execution survives its invoking session. **Unverified:** worktree/sandbox enforcement, baseline delivery, and issue recording as a complete lane path; the lifetime probe does not verify them. |
| Implementation | **Structural:** the agent definition or dispatch prompt binds execution skills, including TDD and systematic debugging. **Hard:** Codex CLI sandbox grants limit its process write scope; native Codex has no separate grant. **Soft:** implementation choices and the named-branch boundary remain judgment where shared git metadata access is required. | **Verified — [issue #179's delivery probe](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5488257766) and [role-matrix ruling](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5501782986):** the tested native subagents lacked SessionStart method delivery, and Codex CLI's role rode its brief. **Verified — repository source:** role pages and Claude definitions bind skills; dispatch selects Codex CLI sandbox arguments. **Unverified:** uncoached skill use and named-branch adherence. |
| The four stop events | **Hard:** the worker role hook refuses command text carrying its short word list, decided from source alone. It does not remove every way to perform an irreversible operation. **Soft:** recognizing core-architecture work, a wrong or unreachable done-check, or a direction call requires worker judgment. **Structural:** the role set fixes the escalation channel (output file / issue comment) and requires the lane to stop and wait. | **Verified — repository source:** the worker role defines the stop triggers and `scripts/hard_edges.py` implements the word list. **Unverified:** uncoached escalation behavior; live hook probes are scoped below. The open enforcement boundary below still applies. |
| Rebase onto current main → own conflicts | **Structural:** the role set assigns rebasing and conflict resolution to the worker. **Hard:** the merge guard rejects a head not based on current main; a moved base after acceptance uses the content-unchanged-rebase path in chapter 5 or full review. | **Verified — [issue #179's option-A ruling](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5550436875):** the two-layer rebase path is settled. **Verified — repository source:** the worker role assigns rebase ownership; guard and comparison machinery implement the current-base and unchanged-content checks. Live recovery as one sequence remains unverified. |
| Final-state done-check → evidence | **Structural:** the role set requires the done-check on the final state with commands, exit codes, and output. **Hard:** CI reruns the mechanical assertions. **Soft:** the truth of non-mechanical evidence is judged by Floor check 1. | **Verified — repository source:** `reference/worker.md` requires final-state evidence and `.github/workflows/ci.yml` carries mechanical assertions. **Verified — [PR #188](https://github.com/LeonJoeeee/devstandard/pull/188):** the Floor evidence contract. **Unverified:** the complete live evidence-to-acceptance path. |
| Opening the PR → fulfillment claim | **Structural:** the PR template restates the goal and carries the evidence. **Hard:** branch protection forbids direct main writes. | **Unverified:** rebuilt template delivery and branch-protection configuration. |
| Driving CI green | **Hard:** the observer and assembler refuse a red or unreported current head at acceptance. **Soft:** the worker classifies own-red versus not-own-red and escalates the latter. | **Verified — repository source:** review assembly enforces green-head admission and the worker role supplies red-check classification and escalation. Uncoached compliance remains unverified. |
| Handback → worktree left in place | **Hard:** the worker role hook refuses its listed merge command words. **Structural:** the lane record and handback message return the PR and evidence to the orchestrator, retaining the worktree for removal at merge. | **Verified — repository source:** the role hook, dispatch lane record and cleanup preconditions exist. **Unverified:** the complete live handback/cleanup transition. |
| Returned for a goal fix | **Structural:** a continuation brief carries the named goal gap into the same branch, worktree, and PR; the lane persists and the executor is disposable. **Hard:** per-PR round accounting enforces the 7-round cap. | **Verified — [issue #179's round ruling](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5525395030):** same-lane continuation and the cap are settled. **Verified — repository source:** `scripts/dispatch` preserves the lane on continuation and `scripts/review-packet` enforces round accounting. The caller supplies evidence that all prior native handles finished. |

**open:** the architecture never claimed zero unauthorized irreversible actions, and since ADR 0051
it does not attempt to. A hook that reads command text is not complete enforcement — obfuscation, an
interpreter script and an operation built from runtime data all pass it — so the role hook guards the
ordinary case and the layers that carry the guarantee are `guard merge`'s reviewed-head verification,
branch protection and, for Codex CLI, the OS sandbox. Native Codex and Claude CLI workers retain
host/tool permissions: their assigned-worktree and named-branch boundaries are structural role obligations.
A CLI worker's shared git metadata access also does not enforce its named-branch boundary.

These assignments answer the five engineering sub-problems from PRD §5. Delivery is role-specific
and has one source per context set; CLI lifetime uses detached supervision or an explicitly retained
originating tool invocation;
asymmetry is explicit in the implementation columns; enforcement is selected per workflow edge; and
observability uses external state while treating self-report as a claim.

## 5. Concurrency and review convergence

N-way dispatch is N issue/branch/worktree lanes under one orchestrator. The orchestrator cuts work
so concurrently writable path sets are disjoint where the goal permits. Worktrees separate lanes;
Codex CLI sandboxes constrain its writes, while other workers obey their assigned-worktree contract.
GitHub provides the queue and durable return path. Work that cannot be cut
without overlapping the same authority is sequenced instead of being declared parallel (PRD §1.1,
§2.1, §2.2).

**open:** the human has not set the observation target for N in PRD §6. The architecture therefore
defines N-way behavior without claiming a supported lane count.

Before handback, the worker owns rebasing and conflict resolution under PRD §4 Workflow 3. After a
green PR is handed back, the orchestrator never repairs a new conflict in its own worktree; it
dispatches a resolver worker into the affected lane. The resolver preserves the issue goal, reruns
final evidence, drives the new head green, and returns it for review. The
[live case recorded on issue #179](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5488090376)
verifies the cost: with two concurrent PRs, merging #177 caused #171 to conflict in
`reference/external-agent.md`; detection consumed review round 5, resolution used an
orchestrator-dispatched worker, and the changed head required round 6. That observation supports
scope cutting and resolver dispatch; it does not prove that every conflict has the same cost.

The review dose is one goal-centric round by default. Notes do not trigger another review round.
Whether to dispatch each next goal-fix round is the orchestrator's per-PR decision, judged only from
the verdict's stated goal gaps. Each returned verdict consumes a review round,
including a verdict that fails Floor check 1. The hard cap is **7 rounds** per PR; 7 is
provisional and is tuned from observed effect
([human ruling](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5525395030)).

The lane persists and the worker is disposable. A goal-fix round sends a continuation brief into
the same branch, worktree, and PR, carrying only the blocking goal gaps, the PR, and the issue. A
Claude-native executor may continue through the same subagent or a fresh one. Codex-native uses a
fresh child; both CLI implementations use a fresh process. Before native continuation or cleanup,
the caller attests completion of all outstanding native handles in that lane with `--native-finished`. This
operation-only attestation never bypasses a live or unknown CLI run.

A Floor check 1 failure for an evidence-free completion claim returns to that lane for real evidence;
the failed review has already consumed a round. A Floor check 2 failure for an unauthorized
irreversible action or out-of-scope work stops the lane and escalates to the human at the
irreversibles touchpoint; it receives no fix round. A conflict after review invalidates the reviewed
head and dispatches a resolver; the resolver's changed head enters full review.

At round 7, or earlier when another round would be pointless, the orchestrator rules first:
merge as-is when the goal is met within bounds and file the remaining Notes as issues; return the
issue for rewriting; abandon it; or change route. The ruling reaches the human only when it is
directional (abandon or change route) or independently touches one of PRD §4 Workflow 2's three
human touchpoints. Otherwise the orchestrator decides and reports the ruling in one line. A
merge-as-is ruling may settle an unresolved Goal No; it cannot waive either Floor check (PRD §1.4).

Before the option-A implementation, the rule re-reviewed every rebased head because its SHA changed. Applied to N ready PRs, each
merge can invalidate the other N−1 reviews even when the changed paths are disjoint. The issue #179
case demonstrates the conflict branch of this cascade at N=2; the general quadratic cost is an
inference, not a measurement.

Under the
[human's option-A ruling](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5550436875),
a reviewed PR whose base moves is neither merged blind nor sent immediately through another full
review. It receives a light review in two ordered, hard layers. The
[industry survey on issue #179](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5525494302)
found no mature system that adds a human or model interaction gate keyed on textual identity; CI on
the merged result is treated as the empirical answer, and the PRD's no-preventive-construction
boundary applies.

1. **Mechanical, hard:** a script proves that the rebase was conflict-free and every path changed by
   the PR is byte-identical before and after it. **One exemption, added 2026-09-07 (#242, #256)**
   because the human's ruling puts the version bump on the change PR: all three release manifest
   version lines read as no difference when their old and new versions each agree, and where that
   exemption is what admits the comparison the new head must declare a bump against the reviewed
   head whose value, read as a dotted numeric release, sorts above both the reviewed head's and the
   replay's — so a lane cannot rebase past a merged bump and set the manifests back. The same
   exemption governs the replay that feeds the comparison: a conflict confined to those version lines
   resolves to the new base's value and the replay continues (#274). Every other byte or mode
   difference, and every conflict reaching any other path or line, still refuses.
   The same synchronized version-only predicate covers the bare-bump review waiver; stale or
   mismatched Codex versions and non-version changes require ordinary review.
2. **Integration, hard:** CI is green on the merged result.

Both layers pass → merge. Any failure falls back to full review and dispatches a resolver where
needed (PRD §1.2, §1.4, §2.1, §2.2).

## 6. Rebuild outputs

The original rebuild opened the following implementation work after architecture approval. The
shipped source and remaining runtime qualification are recorded below; this is not a new task list:

1. Add the Claude-native worker and reviewer agent definitions, including their purpose-specific
   tools, model settings, context pointers, and worker-only skill bindings (PRD §1.5, §2.3).
2. Build the fixed dispatcher for both executor implementations: issue-field validation, worktree
   creation, implementation selection, sandbox arguments, detached Codex supervision, attribution,
   issue-side lane record, same-lane continuation dispatch that supports either a continuing or
   disposable executor, and cleanup (PRD §1.1, §1.4, §1.5, §2.2).
3. Build current-source acceptance assembly and publication: exact SHAs; green-head admission;
   complete ordinary packets from the current reviewer contract; refusal on placeholders;
   whole-verdict return; and per-PR round accounting with the 7-round cap and orchestrator-first
   ruling path (PRD §1.2, §1.4).
4. Split the orchestrator and worker context into two role references, evolving the existing worker
   brief, and reduce `core.md` to the shared workflow contract, triggers, and pointers. Bind
   superpowers once per role. Set `core.md`'s size budget from the hook's inline cap once that cap is
   re-measured against the rebuilt draft. Issue #200 removed Codex host delivery during this rebuild;
   ADR 0056 restores it using these shared artifacts, with workers still receiving their role through
   dispatch (PRD §1.5, §1.6, §2.3).
5. Implement and probe the hard edges: the role hook's per-role word lists, the reviewed-head
   merge guard, the two-layer content-unchanged-rebase path (comparison script and CI on the
   merged result), branch-protection settings, main-red dispatch refusal, PreToolUse
   authorization guards, and recovery behavior (PRD §1.2, §1.3, §2.1, §2.2).
6. Audit every current `reference/` page as keep, merge, move-to-role, or drop. Build a rule ledger
   that gives every retained clause its role, act site, enforcement tier, and PRD trace; a drop needs
   the human's approval. This ledger is implementation evidence, not a new shipped rules page (PRD
   §1.6).
7. Write the superseding and amending ADRs indicated below when their implementation lands. ADR
   bodies remain immutable; only status lines and dated amendment blocks change (PRD §1.5).

ADR 0056 extends these shipped mechanisms with native Codex worker receipts and the host binding
described above; it does not reopen the original rebuild.

## 7. ADR dispositions and traceability

This table finalizes the preliminary inventory on issue #179 against the approved PRD and the later
human rulings. It records what the rebuild must do and names the ADRs as their implementation lands.

**Reconciled 2026-09-07 (#207).** Every row below now names the ADR that carries its disposition,
and the dated amendment blocks are appended on the ADRs the rebuild overtook. ADR bodies were not
rewritten; a row whose disposition needs no ADR says so.

| Disposition | ADRs | Reason |
|---|---|---|
| Already superseded; history only | 0001–0005 | Later ADRs already replaced the initial package, superpowers, execution, lifecycle, and fixed-session forms. No rebuild action, and no ADR needed. |
| Stands as foundation | 0000, 0009, 0012, 0013, 0017, 0018, 0020, 0022, 0023, 0025, 0026, 0031, 0033, 0034, 0037, 0041, 0042 | ADR discipline; GitHub collaboration; worktree lifecycle; task-level design and document admission; operational memory; red-main recovery; universal PR/review/CI; record language; CI fallback; PR ownership; reference sizing; verdict publication; placement; and clean handback remain required by this architecture. Unchanged by the rebuild, so no ADR needed. |
| Superseded by the rebuild | 0006, 0008 → 0047; 0014 → 0048 | The native Workflow tool is no longer the whole harness because fixed dispatch and packet machinery are required, and direct in-session work is no longer the default beyond one- or two-line changes and research (0047); the full/light/mini setup fork is removed and weight is a bound on each issue (0048). The reusable parts of each decision — run sizing, rationing, and "the agent never guesses scope" — are restated by the superseding ADR. |
| Superseded by 0045 (issue #200), then 0045 superseded by 0056 | 0038, 0039, 0045 | Rebuild 0 removed Codex host delivery. ADR 0056 restores the host with shared roles, native workers and independent read-only CLI gating review; the older role-marker and adoption designs remain history. |
| Amended for role delivery | 0007, 0015, 0016, 0019 → 0049; 0015, 0036, 0040 → 0047; 0024 dated block; 0024, 0040 → 0050 | Static context is now one delivered artifact per role, injected by default with the carrier chosen from a measured size and a CI gate that fails an over-cap artifact (0049). The dispatch-first rule and the retirement of the ladder's rung vocabulary ride 0047. ADR 0050 supersedes 0024's cap and 0040's restatement with the model/effort ladder by kind of work on `reference/external-agent.md`, including nested helpers. ADR 0045 reconciled the Codex host removal earlier. |
| Amended for acceptance and concurrency | 0011, 0035 | Already carried: the goal-centric contract by 0044, and the two-layer light review by 0046. Added 2026-09-07 as dated blocks on 0011, 0035 and 0046: the manifest version-line exemption to the byte-identical clause (#242, #256). Resolver dispatch needs no block here — it leaves both gates and the reviewed-diff rule as written; the live statement it overtook is 0015's, which its 0047 block carries. |
| Repository operations; unaffected | 0010, 0021, 0027–0030, 0032, 0043 | Rename history, this repository's pipeline upkeep, wording sweeps, translation and changelog policy, repo-only placement, and page-audit rules do not define the target collaboration model. No ADR needed. |
| Reviewer-contract ADR | 0044 | It records the approved Goal/Floor/Notes contract from PR #188; this architecture does not duplicate or supersede it. No ADR needed. |
| Written by the rebuild | 0045, 0046, 0047, 0048, 0049 | Codex host removal; the guarded merge and content-unchanged rebase; the shipped collaboration machinery with dispatch as the default; weight as a per-issue bound; and per-artifact injected role context. Each rode the PR that implemented its decision, except 0047–0049, which reconcile decisions already landed across Rebuild 0–6. |
| Host restoration after the rebuild | 0056 | Adds Codex packaging and a bounded host adapter around the existing collaboration machinery; preserves the role split, guards, review contract and historical ADR bodies. |

### Structure traceability

| Named structure | PRD source | Why it exists |
|---|---|---|
| Shared supplementary harness on Claude Code and Codex | §1.1, §1.5 | Native sessions do not supply the collaboration protocol or assumed team conventions. |
| Either host as orchestrator with its own native workers | §1.6, §5 | Shared roles and lane receipts reach the actual native tool. Codex gating review stays in an independent read-only CLI because native permissions are inherited. |
| GitHub as durable coordination state | §2.1 | Reuses issues, PRs, review, and CI rather than inventing an agent state machine. |
| Orchestrator context set | §1.1, §1.5 | Removes human scheduling and delivers main-loop conventions to a fresh session. |
| Dispatched-executor purpose × implementation matrix | §1.1, §1.5 | Enables parallel execution while carrying the same role contract through asymmetric native harnesses. |
| Worker context set and worker role reference | §1.2, §1.5, §2.3 | Makes completion evidence-bearing, supplies conventions, and binds execution craft. |
| Reviewer context set and ordinary packet | §1.2, §1.4 | Distrusts completion claims and stops peripheral review drift through a clean, current judging packet. |
| Resolver as a worker purpose | §1.2, §2.2 | Keeps conflict changes isolated and re-verifiable without granting merge authority. |
| SessionStart delivery of the orchestrator set | §1.5 | Ensures a fresh orchestrator receives the conventions it otherwise lacks. |
| Codex adapter and explicit recovery skill | §1.5, §5 | Maps host mechanics without copying the method; provides an explicit read path when hook trust is absent, without claiming that it activates enforcement. |
| Direct-injection default and measured per-artifact carrier choice | §1.5, §5 | Makes static context delivery reliable: the carrier for each artifact follows its measured size against the re-measured hook cap, and since ADR 0049 an artifact that does not fit is a failed gate rather than a silently degraded delivery. |
| Claude worker/reviewer agent definitions | §1.5, §2.3 | Carry fixed role, tool, model, and role-bound skill settings where no session hook reaches. |
| Fixed cross-implementation dispatcher and same-lane continuation | §1.1, §1.4, §1.5, §2.2 | Creates N isolated lanes, keeps fix state in the lane rather than the executor, and closes the Claude/Codex delivery asymmetry. |
| CLI supervisor and explicit tool-lifetime wait | §1.1 | Detached supervision survives SIGHUP; `--wait` retains the originating tool where an enclosing PID namespace would otherwise tear down. Review waiting includes synchronous publication. |
| Current-source ordinary review-packet assembler | §1.2, §1.4 | Delivers a complete, non-stale fulfillment claim to a clean reviewer. |
| Hard / structural / soft enforcement tiers | §1.2, §1.3, §1.5 | Mechanizes evidence and safety boundaries while retaining judgment only where required. |
| Workflow 3 edge tiers | §1.2, §1.3, §1.5, §2.2 | Assign evidence, stop, and isolation mechanisms to every worker-execution step without duplicating the PRD workflow. |
| Worktrees, OS sandboxes, branch protection, and CI-green-before-review order | §1.2, §2.1, §2.2 | Reuses native isolation and integration enforcement while ensuring the reviewer judges a green PR and merge requires both gates. |
| Reviewed-head merge guard | §1.2, §2.1 | Prevents an acceptance verdict for one head from authorizing a different merge unless both hard layers prove the rebased content unchanged — chapter 5's manifest version-line exemption apart — and the merged result green. |
| PreToolUse role hook | §1.3 | Refuses the ordinary spelling of the operations a role must never perform, cheaply enough to hold in one's head, without refusing ordinary work, and with nothing to configure: since ADR 0052 the words are in its source and it reads no file, no ref and no network, and since ADR 0051's 2026-09-11 amendment it judges a command's raw text and never a tool name — no allowlist anywhere, with what a role may reach left to the agent definition's denials and the sandbox that already carried it. |
| GitHub-first lane observability | §1.1, §1.2, §2.1 | Lets the orchestrator reconstruct state without trusting a worker's self-report. |
| Scope cutting and N-way lanes | §1.1, §2.2 | Provide parallel throughput while reducing writable overlap. |
| Per-PR round decision, 7-round cap, and orchestrator-first ruling | §1.1, §1.4 | Bounds revision without making the human schedule ordinary continuation decisions. |
| Same-lane goal repair and the two Floor-failure transitions | §1.2, §1.3, §1.4, §2.2 | Returns an evidence-free claim for proof while stopping unauthorized irreversible or out-of-scope work instead of treating it as a normal fix. |
| Resolver full review and two-layer content-unchanged-rebase light review | §1.2, §1.4, §2.1, §2.2 | Reviews changed conflict resolutions fully while checking byte identity — chapter 5's manifest version-line exemption apart — and merged-result integration for an unchanged PR. |
| Rule ledger and reference-corpus disposition | §1.6 | Prevent silent loss while deleting every clause that lacks a PRD reason. |

Decisions and their reasons: `docs/adr/`.

### Hard-edge implementation evidence (#204)

`scripts/guard` implements the reviewed-head/current-base check and the two-layer rebase path;
`scripts/dispatch` carries role hooks and refuses new work on red default CI. Constructed negative
probes live in `.github/test-hard-edges.py` and `.github/test-dispatch.py`. The live protection
fixture refused while main passed, as recorded on #204. ADR 0046 records the interfaces;
`reference/hard-edges.md` owns their operation. **The match/authorization defaults settled on
2026-09-06 (#204, #223) no longer exist**: the human signed off on the architecture-level change and
delegated three proposed defaults to the main session, which shipped them in a configuration file —
and ADR 0052 deleted that file with every rule that read it on 2026-09-10. Live executor hook
enforcement remains **Unverified**, assigned to the main session by #204's second continuation
ruling. Neither command matching nor classic status protection alone proves zero unauthorized
operations or a complete PR-only capability boundary.

**One rule per role (2026-09-10, #323).** The machinery above — a closed shell grammar, a
ten-family refusal table, a per-tool-call policy read from the remote default branch, an
authorization record for every irreversible orchestrator command, and a retry layer for the network
faults that read caused — cost seven review rounds and three releases over 2026-09-09/10 and still
refused ordinary research commands. On the human's ruling the hook now reads raw command text and
decides on a short word list per role, and no read failure can produce a refusal. Each refusal is
written as a reminder rather than a wall — the
word, what the role does instead, its page, and how to re-spell a benign command — because a
textual scan will sometimes hit one. The residual is accepted rather than chased. ADR 0051 records
the ruling, `reference/hard-edges.md` owns the operative wording, and the rows above are written to
it.

**No configuration file (2026-09-10, #326).** The same day's second ruling finished the first one.
The chain that produced a policy file ran: a hook to stop a subagent writing to GitHub → a file so
the hook knew who the human was and what to require → rules for reading the file → an issue about
where the file lives; each layer solved the previous layer's problem. **The hook stays and
everything that existed only to feed it goes.** The word lists are in the source, the default
branch is `main` or `master` by name, `guard merge` keeps its own GitHub reads and derives the
repository owner from the repository's API record, `guard protection --apply` takes its check names
from the command line, and the dispatch gate judges by the all-observed-green rule alone. The
founding admission below is now the absence of a rule rather than a carve-out, and the
authorization record, the authorization issue and the standing-release entry are retired. ADR 0052
records the ruling and the chain it undoes.

**Founding admission (2026-09-07, #293; retired 2026-09-10, #326).** Proven policy absence once
narrowed what the guard granted and then also admitted one operation, because an authorization
record could not precede the policy file that named its issue. **The admission has no code left.**
Its protection half was dropped on 2026-09-10 (#323) with the remote reads; its policy half went
the same day with the file (#326), because the orchestrator's word list no longer carries `push`
at all. GitHub's own branch protection is what rejects a push to a protected branch, which is the
layer that check belongs to. `reference/hard-edges.md` owns the wording and its limits; ADR 0046's
2026-09-07 and 2026-09-10 blocks record the admission, its narrowing and its retirement.

### Rebuild implementation evidence (2026-09-07, #207)

Rebuild 0 through 6 landed the mechanisms this document specifies. `scripts/dispatch` validates the
issue contract, creates and records the lane, selects the executor implementation, and detaches a
Codex process (#202, #213). `scripts/review-packet` assembles current-source packets, refuses a red
or unreported head, publishes the whole verdict, and accounts rounds against the cap (#203, #222).
`scripts/guard` with `scripts/hard_edges.py` implements the reviewed-head merge and the two-layer
rebase proof (#204, #223). `hooks/session-start` delivers one artifact per role (#205, #235), and
`agents/worker.md` and `agents/reviewer.md` carry the Claude-native roles (#201, #208). Their
constructed tests live in `.github/`. ADRs 0047 and 0049 record the decisions behind the shipped
machinery and the delivery split; 0048 records weight as a per-issue bound.

**Source labels reconciled 2026-09-11 (#342).** The original 2026-09-07 qualification (#279) told
readers to reinterpret absent-mechanism cells using this implementation record. The cells now name
the shipped source directly. Constructed tests qualify the mechanism they reach, not unrelated
behavior. What constructed tests leave **Unverified** includes live enforcement of role hooks and
sandbox by the harness (separately qualified below),
native-subagent status delivery, detached-process observation after an orchestrator restart, and
the complete recovery path exercised as one sequence. A passing constructed probe is not a proof
about the harness.

### Codex host qualification (2026-09-11, #342)

**Verified — native Codex CLI 0.153.4 on macOS and Ubuntu 24.04:** `.github/test-codex-install.py` and
`.github/test-codex-runtime.py` exercised a temporary native plugin installation, its cache and
skill discovery, and actual native hook handlers with the plugin's own environment. A deterministic
local Responses service drove disabled hooks, untrusted hooks before and after an invocation-wide
trust bypass, and invocation-trusted main, worker and reviewer runs. The main request contained the
complete core, orchestrator and adapter artifacts. Assigned workers/reviewers received no
orchestrator startup context, and their actual tool hooks enforced their role. These were installed
plugin hooks, not inline-hook or environment doubles; the trust bypass did not persist trust.

**Verified — installed Codex plugin on macOS:** `.github/test-codex-native.py`, called before
installer cleanup, passed both native spawn protocols against the actual cached dispatcher and
hooks. The full emitted worker brief and explicit model/effort reached a fresh child; it inherited
developer instructions and permissions, used the assigned worktree explicitly, ran an allowed
command, and refused the worker's forbidden command. Its real `agent_id` selected worker rules
without a process role marker. Native wait returned completion. This proves native dispatch and
hook behavior with a deterministic provider, not independent child sandboxing or a remote PR lifecycle.

**Verified — Claude Code 2.1.268 on macOS and the original Linux SSH development server:**
`.github/test-claude-runtime.py` exercised the candidate through session-only plugin loading and a
local deterministic Messages service. Main startup delivered full core/orchestrator context without
the Codex adapter. Direct worker/reviewer sessions, with and without the CLI role marker, and actual
background Agent workers/reviewers received their shipped role definition without orchestrator context. Allowed shell
commands ran and each role's forbidden command was refused; reviewer tool catalogs excluded
`Write` and `Edit`. A worker process's inherited role did not override its named reviewer child.
The `--dispatch-cli` case also exercised the real dispatcher and detached supervisor into Claude:
the full resolved brief arrived through stdin, the assigned cwd and explicit model/effort were
used, and structured output retained permission denials alongside completion. GitHub I/O and provider
responses were fixtures; test-only invocation controls excluded unrelated configuration and tools.
This left the existing installation unchanged. It does not establish a native Claude model reading
the full referenced role/contract, production authentication/model behavior, or a remote PR lifecycle.

**Verified — real macOS/Linux processes with controlled GitHub/model boundaries:** the dispatch and
review-packet integration suites passed Python session detachment, SIGHUP survival, completion and
publication checks. Those fixtures establish process behavior, not a complete remote worker/PR
lifecycle or uncoached model adherence to the method.

Linux CI installs the distribution Bubblewrap package and its scoped AppArmor profile under
[Codex's prerequisites](https://learn.chatgpt.com/docs/sandboxing#prerequisites); the real runtime
probes retain the read-only sandbox and existing command rules. Captured qualification runs are
linked from [PR #343](https://github.com/LeonJoeeee/devstandard/pull/343).

**Unverified:** persistent UI resume, clear and compaction behavior; matcher-fixture coverage does
not qualify those UI transitions. These limits belong to this
restored-host path and do not rewrite the older rebuild's evidence or qualify unrelated recovery
claims above.

**CLI lifetime correction (2026-09-11, #342 continuation).** A real Linux Codex workspace-write tool
could publish a detached launch then lose its supervisor when the tool PID namespace ended.
Python session detachment does not prevent that teardown. Explicit CLI `dispatch --wait` retains
the originating execution until the actual child exit is atomically recorded; `review-packet start
--wait` also publishes the whole verdict synchronously. Default detached behavior remains.

A supervisor inherits a pre-acquired advisory lock in existing run scratch, avoiding a publication
readiness race; its CLI child does not inherit ownership. Later callers use this lock, never a
namespace-local PID, to distinguish active supervision from lost/unknown execution. Valid completion
records a CLI exit, not task acceptance. Missing completion and a free/missing lock block reuse;
explicit exact-run reconciliation requires authoritative originating-host absence evidence. It
changes the original issue run to `reconciled-lost`, without fabricating an exit. Lost reviews release
only after reading that exact reconciliation, as failed attempts with no verdict round. The existing
single-orchestrator contract remains; no global journal or distributed comment lock is added.
`reference/external-agent.md` owns recovery and retention through lane cleanup. These mechanisms do
not change authentication, hook trust, runtime-directory grants or nested sandbox capability.
