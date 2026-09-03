# DevStandard — Collaboration-model architecture

> Shared baseline for all parallel work. Read before any task. Changing anything here = touching
> the core: public merge + human approval + an ADR.

This document defines the supplementary harness required by the target workflows in PRD §4. It
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

The supported configuration is one Claude Code orchestrator with N dispatched executors. A
dispatched executor has one of two purposes, worker or reviewer, and one of two implementations, a
Claude-native subagent or a Codex process. A conflict resolver is a worker assigned a conflict task,
not a third role. This is the smallest configuration that removes scheduling from the human while
retaining the GitHub flow and native isolation mechanisms (PRD §1.1, §2.1, §2.2).

DevStandard is a supplementary harness. Claude Code still owns sessions, hooks, native subagents,
tools, and permissions. Codex still owns its process, model, and sandbox. DevStandard supplies the
missing collaboration protocol: role context, dispatch, acceptance, and the transitions between
GitHub artifacts. It does not replace either native harness (PRD §1.1, §1.5).

Codex-as-orchestrator is outside this design. Its shipped hook branch and
`reference/harness-codex.md` remain frozen: they are not removed, redesigned, or promised to track
this rebuild. The orchestrator context and mechanisms below are Claude-native only. Codex appears
in this design only as a worker or reviewer process. Separate live sessions, Codex-side subagents,
and workflow-native panels are not worker or reviewer implementations in this configuration. Their
existing references are dispositioned by the rebuild audit rather than extended here. This prevents
unused configurations from adding rules before use requires them (PRD §1.6).

**Verified — repository source:** the frozen Codex hook branch still directs a Codex session to read
`core.md` plus the bounded mappings page, `reference/harness-codex.md`; `hooks/session-start` and the
CI assertion record that source behavior. This is not a new Codex-orchestrator guarantee.
**Unverified — harness behavior:** the frozen path was not re-probed for this rebuild.

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

| Purpose | Claude-native implementation | Codex-process implementation | Result |
|---|---|---|---|
| Worker | A `devstandard:worker` agent definition fixes the static role, tools, skill bindings, and model. The dispatch supplies the issue and lane. | The fixed dispatch script places the same static role and dynamic task in the prompt, sets model and effort explicitly, and grants the worktree plus the linked-worktree git metadata required to commit. | A PR linked to the issue, rebased on current `main`, with final-state evidence and green checks or named unreported checks. |
| Reviewer | A `devstandard:reviewer` agent definition fixes the judging role, read-only tools, empty skill set, and model. The assembled packet supplies the review instance. | The fixed dispatch script places the same judging contract and packet in the prompt, sets model and effort explicitly, and invokes an OS read-only sandbox. | A verdict naming the reviewer and reviewed head, published whole on the PR. |

The routing rule remains ADR 0040's: use Codex where installed; use a Claude-native subagent only
where the work especially suits one. The choice changes delivery, not purpose or obligations. The
explicit binding prevents a fresh executor from inventing working conventions (PRD §1.5); role-based
skill bindings reuse the superpowers library at the step where its craft is needed (PRD §2.3).

### Worker context set

The worker set consists of the static role plus one dynamic task packet.

The static role defines one issue, branch, and worktree; write authority only in that lane; the
build → rebase → final done-check → PR → checks-green delivery sequence; evidence and attribution
duties; the NEVER and escalation boundaries; and the execution-skill triggers, including test-driven
development and systematic debugging. The task packet supplies the issue's goal, reason, bounds,
done-check, named base, branch, worktree, required inputs, and expected output. It carries no merge,
release, or orchestration procedure. This separates execution from integration and makes a worker's
claim inspectable rather than trusted (PRD §1.2, §1.5, §2.3).

### Reviewer context set

Reviewer is the read-only purpose of the dispatched-executor family. Its static set is the judging
contract from issue #183 and PR #188: Goal verdict first, the two-check Floor second, and Notes last.
Only the Goal verdict and Floor decide readiness; Notes neither block nor trigger re-review. The
reviewer has no craft skills because it reads and rules rather than builds (PRD §1.4).

Each review packet contains the issue's goal, bounds, and done-check; the PR description as the
fulfillment claim; explicit review-base and head SHAs; the convention base; the accepted-spec blob
or `NONE`; the architecture-level flag; the in-repo-write predicate; and CI-fallback evidence only
when the fallback has been declared. The reviewer sees no orchestrator history and treats the PR
description as unverified claims (PRD §1.2, §1.4).

### Resolver

A resolver is a worker whose issue-sized assignment is to rebase a delivered branch that conflicts
with current `main`. It receives the ordinary worker set plus the delivered PR, old and new bases,
the conflicting paths, and the original issue contract. It may change only that lane, reruns the
original done-check on the resolved final state, republishes evidence, and returns the new head for
fresh review. It never receives merge authority (PRD §1.2, §2.2).

## 3. Context delivery

Static role content has one operative source per role: the orchestrator role reference, the worker
role reference (evolving `reference/worker-brief.md`), and `reference/code-review-prompt.md` for the
reviewer. Agent definitions and dispatch prompts are delivery carriers, not independently edited
copies. `core.md` holds the shared workflow contract, triggers, and pointers; it does not restate
the role pages in full. This arrangement addresses convention loss without rebuilding another
incident-driven rules layer (PRD §1.5, §1.6).

| Context and executor | Delivery path | Evidence state |
|---|---|---|
| Orchestrator static set | Claude Code's SessionStart hook forces a first-action read of `core.md`; `core.md` directs the orchestrator to its role reference and step-local procedures. The same trigger repeats after context clear or compaction. | **Verified — repository source:** `hooks/hooks.json`, `hooks/session-start`, and the local CI hook gate show the emitted instruction and matcher. **Unverified — harness behavior:** the rebuilt two-stage read has not been exercised in Claude Code. |
| Claude-native worker static set | The `devstandard:worker` agent definition supplies role identity, tool and model settings, the worker-reference read, and execution-skill bindings. | **Verified — [issue #187](https://github.com/LeonJoeeee/devstandard/issues/187) and [issue #179's enforcement-tier ruling](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5488257766):** the recorded native-subagent probe found that a subagent receives neither the session hook nor the method automatically. **Unverified:** delivery through the proposed agent definition and its forced reference read has not been probed. |
| Claude-native worker task | The fixed dispatcher invokes the agent with the issue contract, branch, worktree, base, inputs, and output duty. It rejects an unresolved field before launch. | **Unverified:** the dispatcher and validation do not yet exist. |
| Claude-native reviewer static set | The `devstandard:reviewer` agent definition fixes the read-only purpose, judging contract pointer, empty skill set, tool restriction, and model. | **Verified — [issue #179](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5501782986) and [issue #183](https://github.com/LeonJoeeee/devstandard/issues/183#issuecomment-5496822719) role rulings:** reviewer is a worker-family purpose with a separate set and read-only posture. **Unverified:** Claude agent-definition tool restriction and contract delivery have not been exercised. |
| Codex worker or reviewer static set | The fixed dispatcher expands the appropriate role reference into the prompt because Codex has no role-definition carrier. It passes the explicit model, effort, working directory, and sandbox posture. | **Verified — [issue #187](https://github.com/LeonJoeeee/devstandard/issues/187) and [issue #179's role-matrix probe](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5501782986):** Codex has no custom agent-definition mechanism; the role must ride the dispatch brief. **Unverified:** the fixed expansion, sandbox behavior, and validation script have not been exercised as one path. |
| Codex worker lifetime | The dispatcher starts a supervisor in a detached `setsid` session; Codex remains foreground within that supervisor, with stdin closed and output captured in session scratch. The launch returns control to the orchestrator. | **Verified — [issue #187](https://github.com/LeonJoeeee/devstandard/issues/187) and [issue #179's lifetime finding](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5501782986):** a process coupled to the invoking session dies with that session, while the `setsid`-detached form survives. **Unverified:** the final supervisor command, cleanup, and failure reporting have not been implemented end to end. |
| Review instance, either implementation | The review-packet assembler reads the current issue and PR, resolves exact SHAs, takes the current reviewer contract, fills every slot, and only then dispatches the reviewer. It refuses a partial packet. | **Verified — [issue #183](https://github.com/LeonJoeeee/devstandard/issues/183) and [PR #188](https://github.com/LeonJoeeee/devstandard/pull/188):** the judging protocol changed while this architecture work was being dispatched, demonstrating that a copied earlier packet can stale under the dispatcher. **Unverified:** runtime assembly from the current contract has not been implemented. |

The dispatcher records the executor implementation, purpose, issue, branch, worktree, and native
task handle or process identifier on the issue. While a lane is running, the orchestrator may use
the native handle, OS liveness, and captured output to detect termination. Completion is never
inferred from those signals: it is established only by the durable PR, evidence, verdict, and CI
state. A restarted orchestrator reconstructs work from open issues and PRs; absence of a PR remains
"running or lost," not "done" (PRD §1.1, §1.2, §2.1).

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

### Workflow 1: one task

| Step or edge from PRD §4 | Tier and native mechanism | Evidence state |
|---|---|---|
| Discussion → ① issue | **Structural:** the orchestrator set provides the issue fields and the requirements-skill trigger. **Soft:** the human and orchestrator judge the wanted result, reason, bounds, weight, and done-check. | **Unverified:** the rebuilt orchestrator set has not been delivered. The use of a skill here is reuse under PRD §2.3, not a claim that a skill can judge completeness. |
| ① issue → ② dispatch | **Hard:** the fixed dispatch script refuses a missing issue, goal, bounds, done-check, named base, branch, or worktree. **Soft:** the orchestrator cuts scope and selects the executor implementation. | **Unverified:** field validation and executor selection have not been implemented. This edge exists to prevent evidence-free work and missing conventions (PRD §1.2, §1.5). |
| ② dispatch → isolated lane | **Hard:** the OS sandbox restricts filesystem writes and reviewer invocations are read-only. **Structural:** a dedicated worktree separates working trees, while the selected role set and task packet are injected by the agent definition or dispatch prompt. **Soft:** a worker with required shared-git-metadata access still obeys its named-branch boundary. | **Verified — [issue #187](https://github.com/LeonJoeeee/devstandard/issues/187) and [issue #179's delivery finding](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5488257766):** native subagents do not inherit hook delivery. **Unverified:** the proposed sandbox restrictions, Claude agent-definition restrictions, and complete fixed dispatcher. Reuses PRD §2.2. |
| ③ worker → delivered PR | **Hard:** the sandbox limits the lane and CI later checks executable assertions. **Structural:** the worker set places rebase, final-state evidence, PR, and checks-green duties at execution. **Soft:** implementation choices and the truth of non-mechanical evidence remain worker judgment subject to review. | **Unverified:** the rebuilt worker carrier has not been exercised. GitHub, CI, and worktrees are reused under PRD §2.1 and §2.2; acceptance addresses PRD §1.2. |
| Delivered PR → ④ acceptance | **Hard:** the reviewer is OS read-only. **Structural:** the assembler supplies a complete, current, clean-context packet and the Goal/Floor/Notes output shape. **Soft:** the reviewer judges goal fulfillment and the Floor evidence. | **Verified — [issue #183](https://github.com/LeonJoeeee/devstandard/issues/183) and [PR #188](https://github.com/LeonJoeeee/devstandard/pull/188):** the goal-centric contract and empty-by-design skill set are recorded, and PR #188's CI is green. **Unverified:** read-only enforcement, agent-definition delivery, and packet assembly. This edge addresses PRD §1.2 and §1.4. |
| ④ accepted head → ⑤ merge and cleanup | **Hard:** branch protection rejects direct main writes and requires CI for the PR head. **Structural:** the merge guard compares the published verdict's head with the PR head; architecture-level status and the human sign-off slot travel in the issue, PR, and review packet. **Soft:** the orchestrator classifies architecture-level work and reads the human's decision. | **Unverified:** the merge guard, the rebuild's exact branch-protection configuration, and the sign-off marker have not been exercised. The hard mechanisms are reused under PRD §2.1 and §2.2. |
| ⑤ merged result → ⑥ delegated release | **Hard:** a PreToolUse release guard blocks tag or publish commands unless the repository has a standing delegation or the current release has recorded human authorization. **Structural:** the orchestrator set requires the one-line report after release. **Soft:** the human decides a new delegation or major-release sign-off. | **Unverified:** the blocking hook, covered command set, and authorization lookup have not been implemented. This is the mechanizable boundary around PRD §1.3. |

### Workflow 2: orchestrator events

| Event from PRD §4 | Tier and native mechanism | Evidence state |
|---|---|---|
| The human speaks | **Soft:** the orchestrator discusses or adjusts direction. **Structural:** its role set presents the issue-creation and requirements-skill triggers. | **Unverified:** rebuilt role delivery. Addresses PRD §1.1 and reuses §2.3. |
| An irreversible action is needed | **Hard:** workers and reviewers lack merge, release, and external destructive capabilities; an orchestrator PreToolUse hook blocks recognized irreversible operations until human authorization is recorded. **Soft:** the orchestrator identifies semantically irreversible actions the hook cannot classify. | **Unverified:** capability cuts, match coverage, and authorization proof. Addresses PRD §1.3. |
| Architecture-level change or major release is ready | **Hard:** the merge or release guard requires a durable human sign-off marker. **Soft:** the orchestrator classifies the change and the human decides. | **Unverified:** marker shape and guard integration. Addresses the irreversible-control concern in PRD §1.3. |
| Issues await dispatch | **Hard:** the dispatcher refuses a new lane while default-branch CI is red and enforces one branch/worktree per task. **Structural:** it creates and records N lanes. **Soft:** the orchestrator cuts scopes to reduce overlap. | **Unverified:** dispatch refusal and lane-record behavior. GitHub, worktrees, and CI are reused under PRD §2.1 and §2.2 to address PRD §1.1. |
| A worker delivers | **Structural:** the orchestrator observes the PR and external state, validates that the fulfillment packet is present, and starts acceptance. **Soft:** a worker report remains a claim until the review and checks establish it. | **Unverified:** observer behavior. The durable source is GitHub under PRD §2.1; the distrust boundary addresses PRD §1.2. |
| A verdict returns | **Structural:** Goal Yes/Floor Pass advances the reviewed head; Goal No returns only the stated goal grounds; a conflict dispatches a resolver. **Hard:** merge still waits on branch protection and CI. **Soft:** the verdict itself is judgment. | **Verified — [issue #183](https://github.com/LeonJoeeee/devstandard/issues/183) and [PR #188](https://github.com/LeonJoeeee/devstandard/pull/188):** Goal/Floor/Notes semantics. **Unverified:** transition automation and resolver dispatch. Addresses PRD §1.2 and §1.4. |
| Main goes red | **Hard:** dispatch refuses new starts until default-branch CI is green. **Structural:** the orchestrator set presents revert-first recovery and the relevant procedure. **Soft:** it decides whether an obvious minutes-long fix-forward is safer than revert. | **Unverified:** the dispatch gate. CI is reused under PRD §2.1; preventing concurrent work on a bad base supports PRD §1.1. |
| Idle | **Structural:** the main-loop trigger queries open issues, PRs, checks, and worktree records and reports progress. **Soft:** the orchestrator decides whether a leftover needs cleanup or escalation. | **Unverified:** there is no rebuilt idle trigger. Reuses GitHub state under PRD §2.1 to address PRD §1.1. |

**open:** the PreToolUse command/tool match set, the merge-guard boundary, and the durable form of
human authorization must be settled and probe-tested before the architecture can claim zero
unauthorized irreversible actions. A hook that covers only known command spellings is not complete
enforcement, and a worker's required access to shared git metadata does not by itself enforce the
named-branch boundary.

These assignments answer the five engineering sub-problems from PRD §5. Delivery is role-specific
and has one source per context set; Codex lifetime is detached from the orchestrator session;
asymmetry is confined to the two delivery columns; enforcement is selected per workflow edge; and
observability uses external state while treating self-report as a claim.

## 5. Concurrency and review convergence

N-way dispatch is N issue/branch/worktree lanes under one orchestrator. The orchestrator cuts work
so concurrently writable path sets are disjoint where the goal permits. Worktrees and OS sandboxes
provide lane isolation; GitHub provides the queue and durable return path. Work that cannot be cut
without overlapping the same authority is sequenced instead of being declared parallel (PRD §1.1,
§2.1, §2.2).

**open:** the human has not set the observation target for N in PRD §6. The architecture therefore
defines N-way behavior without claiming a supported lane count.

When `main` moves, each unmerged lane rebases before delivery or merge. A conflict is not repaired in
the orchestrator's worktree. The orchestrator dispatches a resolver worker into the affected lane;
the resolver preserves the issue goal, reruns final evidence, and returns a new head for review.
The [live case recorded on issue #179](https://github.com/LeonJoeeee/devstandard/issues/179#issuecomment-5488090376) verifies the cost: with two concurrent PRs, merging #177 caused
#171 to conflict in `reference/external-agent.md`; detection consumed review round 5, resolution used
an orchestrator-dispatched worker, and the changed head required round 6. That observation supports
scope cutting and resolver dispatch; it does not prove that every conflict has the same cost.

The review dose is one goal-centric round by default. A Goal No verdict permits one fix-and-review
round judging the goal grounds. Notes never buy a round. A conflict after review is different: it
invalidates the reviewed head, so the resolver's new head requires review even though the prior Goal
verdict was Yes. Further goal-failure rounds stop for human direction rather than iteratively
optimizing peripheral findings (PRD §1.4).

The current rule re-reviews every rebased head because its SHA changed. Applied to N ready PRs, each
merge can invalidate the other N−1 reviews even when the changed paths are disjoint. The issue #179
case demonstrates the conflict branch of this cascade at N=2; the general quadratic cost is an
inference, not a measurement.

The proposed narrow exemption is limited to a conflict-free, path-disjoint, byte-identical rebase.
Let `B0..H0` be the reviewed change and `B0..B1` the new main change. It qualifies only if the two
changed-path sets are disjoint, rebase produces `H1` without conflict, every path changed by the PR
has the same mode and blob bytes in `H0` and `H1`, and every other path in `H1` matches `B1`. The PR
records all four SHAs and the machine comparison. A same-file edit, changed generated file, mode
change, ambiguous rename, failed comparison, or different commit message does not qualify. Those
cases dispatch a resolver when needed and re-review. This exemption removes reviews that can inspect
no changed PR bytes while retaining review after any overlapping change (PRD §1.4, §2.2).

**open:** the byte-identical-rebase exemption is a proposal, not a human ruling. Until the human
approves it and an ADR defines its executable comparison, every rebase after review continues to
require check 1. Batched merge windows are not adopted: they delay integration and do not remove the
need to establish each PR against the merged base.

## 6. Rebuild outputs

The implementation work is opened only after this architecture is approved. The implied issue list
is:

1. Add the Claude-native worker and reviewer agent definitions, including their purpose-specific
   tools, model settings, context pointers, and worker-only skill bindings (PRD §1.5, §2.3).
2. Build the fixed dispatcher for both executor implementations: issue-field validation, worktree
   creation, implementation selection, sandbox arguments, detached Codex supervision, attribution,
   issue-side lane record, and cleanup (PRD §1.1, §1.5, §2.2).
3. Build current-source review-packet assembly and publication: exact SHAs, complete dynamic packet,
   refusal on placeholders, current reviewer contract, and whole-verdict return (PRD §1.2, §1.4).
4. Split the orchestrator and worker context into two role references, evolving the existing worker
   brief, and reduce `core.md` to the shared workflow contract, triggers, and pointers. Bind
   superpowers once per role (PRD §1.5, §1.6, §2.3).
5. Implement and probe the hard edges: least-privilege role tools, the reviewed-head merge guard,
   CI and branch-protection settings, main-red dispatch refusal, PreToolUse authorization guards,
   and recovery behavior (PRD §1.2, §1.3, §2.1, §2.2).
6. Audit every current `reference/` page as keep, merge, move-to-role, or drop. Build a rule ledger
   that gives every retained clause its role, act site, enforcement tier, and PRD trace; a drop needs
   the human's approval. This ledger is implementation evidence, not a new shipped rules page (PRD
   §1.6).
7. Write the superseding and amending ADRs indicated below when their implementation lands. ADR
   bodies remain immutable; only status lines and dated amendment blocks change (PRD §1.5).

Do not pre-open these issues from this document. Their boundaries may be adjusted to keep one writer
per worktree, but no issue may silently omit one of the outputs above.

## 7. ADR dispositions and traceability

This table finalizes the preliminary inventory on issue #179 against the approved PRD and the later
human rulings. It records what the rebuild must do; it does not edit or create the superseding ADRs.

| Disposition | ADRs | Reason |
|---|---|---|
| Already superseded; history only | 0001–0005 | Later ADRs already replaced the initial package, superpowers, execution, lifecycle, and fixed-session forms. No rebuild action. |
| Stands as foundation | 0000, 0009, 0012, 0013, 0017, 0018, 0020, 0022, 0023, 0025, 0026, 0031, 0033, 0034, 0037, 0041, 0042 | ADR discipline; GitHub collaboration; worktree lifecycle; task-level design and document admission; operational memory; red-main recovery; universal PR/review/CI; record language; CI fallback; PR ownership; reference sizing; verdict publication; placement; and clean handback remain required by this architecture. |
| Superseded by the rebuild | 0006, 0008, 0014 | The native Workflow tool is no longer the whole harness because fixed dispatch and packet machinery are required; direct in-session work is no longer the default beyond one- or two-line changes and research; the full/light/mini setup fork is removed and weight lives per task. The reusable parts of each decision are restated by the superseding ADR. |
| Amended for role delivery | 0007, 0015, 0016, 0019, 0024, 0036, 0038, 0039, 0040 | The one-page core and forced-read principle remain, but role references, Claude agent definitions, the dispatch-first rule, deeper role-bound superpowers integration, fixed process delivery and lifetime, and the frozen Codex-orchestrator scope change their operative delivery statements. |
| Amended for acceptance and concurrency | 0011, 0035 | The goal-centric contract from issue #183/PR #188 changes check-1 vocabulary and semantics; resolver dispatch changes conflict handling. A third byte-identical-rebase exception is added only if the open proposal receives human approval. |
| Repository operations; unaffected | 0010, 0021, 0027–0030, 0032, 0043 | Rename history, this repository's pipeline upkeep, wording sweeps, translation and changelog policy, repo-only placement, and page-audit rules do not define the target collaboration model. |
| Reviewer-contract ADR | 0044 | It records the approved Goal/Floor/Notes contract from PR #188; this architecture does not duplicate or supersede it. |

### Structure traceability

| Named structure | PRD source | Why it exists |
|---|---|---|
| Supplementary harness above Claude Code and Codex | §1.1, §1.5 | Native sessions do not supply the collaboration protocol or assumed team conventions. |
| Claude Code orchestrator; frozen Codex-orchestrator path | §1.6 | One used configuration is designed; the unused second path receives no preventive construction. |
| GitHub as durable coordination state | §2.1 | Reuses issues, PRs, review, and CI rather than inventing an agent state machine. |
| Orchestrator context set | §1.1, §1.5 | Removes human scheduling and delivers main-loop conventions to a fresh session. |
| Dispatched-executor purpose × implementation matrix | §1.1, §1.5 | Enables parallel execution while carrying the same role contract through asymmetric native harnesses. |
| Worker context set and worker role reference | §1.2, §1.5, §2.3 | Makes completion evidence-bearing, supplies conventions, and binds execution craft. |
| Reviewer context set and Goal/Floor/Notes contract | §1.2, §1.4 | Distrusts completion claims while stopping peripheral review drift. |
| Resolver as a worker purpose | §1.2, §2.2 | Keeps conflict changes isolated and re-verifiable without granting merge authority. |
| SessionStart delivery of the orchestrator set | §1.5 | Ensures a fresh orchestrator receives the conventions it otherwise lacks. |
| Claude worker/reviewer agent definitions | §1.5, §2.3 | Carry fixed role, tool, model, and role-bound skill settings where no session hook reaches. |
| Fixed cross-implementation dispatcher | §1.1, §1.5, §2.2 | Creates N isolated lanes and closes the Claude/Codex delivery asymmetry. |
| Detached Codex supervisor | §1.1 | Keeps parallel work alive without occupying or sharing the orchestrator session lifetime. |
| Current-source review-packet assembler | §1.2, §1.4 | Delivers a complete, non-stale claim and judging contract to a clean reviewer. |
| Hard / structural / soft enforcement tiers | §1.2, §1.3, §1.5 | Mechanizes evidence and safety boundaries while retaining judgment only where required. |
| Worktrees, OS sandboxes, branch protection, and CI | §2.1, §2.2 | Reuses native isolation and integration enforcement. |
| Reviewed-head merge guard | §1.2, §2.1 | Prevents an acceptance verdict for one head from authorizing a different merge. |
| PreToolUse authorization guard | §1.3 | Blocks mechanizable irreversible actions before execution. |
| GitHub-first lane observability | §1.1, §1.2, §2.1 | Lets the orchestrator reconstruct state without trusting a worker's self-report. |
| Scope cutting and N-way lanes | §1.1, §2.2 | Provide parallel throughput while reducing writable overlap. |
| One-round review dose and resolver re-review | §1.4 | Prevent repeated peripheral revision while reviewing a head changed by conflict resolution. |
| Proposed byte-identical-rebase exemption | §1.4, §2.2 | Avoids re-review when the PR's bytes are unchanged and isolation proves no overlap. |
| Rule ledger and reference-corpus disposition | §1.6 | Prevent silent loss while deleting every clause that lacks a PRD reason. |

Decisions and their reasons: `docs/adr/`.
