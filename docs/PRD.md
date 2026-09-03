# DevStandard Project Definition (PRD)

Approved by the human 2026-09-01 (issue #182); this document is the measuring stick for every
structure in this project — see the existence criterion at the end.

## 1. Problem background

1. **The native harness provides a single agent.** Advancing several pieces of work in parallel
   forces the human into the scheduler-and-coordinator role; their time goes to coordination
   instead of direction.
2. **An unsupervised agent's completion claims are untrustworthy.** Observed in practice:
   completion claims with no evidence, tests weakened until they pass, code reaching the main
   branch unreviewed.
3. **Irreversible operations carry the highest risk.** Ordinary mistakes are acceptable;
   unrecoverable damage is not. A run-first-fix-later strategy is premised on things remaining
   fixable.
4. **Repeated revision erodes the core of the work.** An agent's first pass usually gets the core
   right, with defects concentrated in the periphery; after several review-and-fix rounds the
   periphery approaches perfection while the core is lost. Two causes: the multi-round mechanism
   itself induces goal drift, and the review prompt steers reviewers toward secondary issues.
5. **Agents lack the working conventions human developers assume.** Where files belong, when to
   ask before acting, what must not be touched — every fresh session violates them anew.
6. **The rules layer accretes incident by incident.** Preventive construction piles up until the
   layer is too large to read or maintain.

## 2. Structures reused as-is

1. **The GitHub collaboration flow** (issues / PRs / review / CI): the structure human software
   development has already validated; machines simply reuse it.
2. **git worktrees, OS-level sandboxes, branch protection**: parallel isolation and enforcement,
   natively available, requiring only configuration.
3. **The superpowers skill library**: mature working methods — test-driven development,
   systematic debugging, requirements clarification — bound into the workflow per role: the
   worker role binds the execution skills, the orchestrator role binds the requirements skills.
   Binding sites are centralized, so upgrading or replacing the library touches one place.

## 3. Vision

> **One person directs an agent team through development: the human owns direction, sets the
> acceptance criteria, and signs off on architecture-level changes and major releases; one
> orchestrator converses, dispatches, gates quality against those criteria, and merges; N
> workers process N issues in parallel. Fast, without losing control.**

## 4. The solution: the target workflows

The substance of this product is the three workflows below; every rule, file, and mechanism exists
to make agents run by them.

**Workflow 1: the full lifecycle of one task**

```
Entry: the human raises a need, or the orchestrator finds a problem
  → Discussion pins down: the wanted result, and why        [human participates]
  → 1. Create the issue: goal, bounds (weight and required finish), done-check
  → 2. Dispatch: branch + worktree + role injection
  → 3. Worker: implement → rebase onto current main → run the done-check on the
       final state, keep the evidence
       → open the PR (restating the goal, with evidence of fulfillment)
       → drive the checks green → deliver
  → 4. Orchestrator acceptance: one clean-context reviewer rules on
       "did this PR accomplish what the issue set out to accomplish"
       ├ Goal met     → peripheral issues recorded as notes; no re-review; pass
       ├ Goal not met → return for fixes → re-review (judging the goal only)
       └ Conflicts with main → dispatch a resolver → re-review
       (Ordinary tasks pass on this ruling alone. Architecture-level changes and
        major releases additionally wait for the human's sign-off before merge.)
  → 5. Worker drives CI green before handback → reviewer sees a green PR →
       review pass + CI green → merge → close the issue → remove the worktree
  → 6. Release (repos with a standing delegation) → one-line report to the human
```

**Workflow 2: the orchestrator's main loop**

```
loop {
  The human speaks        → discuss / create issues / adjust direction
  An irreversible action
  is needed               → stop; request the human's authorization;
                            proceed only after approval
  An architecture-level
  change or major release
  is ready to merge       → wait for the human's sign-off
                            (these three are the only events that wait on the human)
  Issues await dispatch   → dispatch, N ways in parallel
                            (cut scopes to minimize file overlap)
  A worker delivers       → acceptance → start the review
  A verdict returns       → met: merge, release, clean up
                            not met: return | conflict: dispatch a resolver
  Main goes red           → freeze new dispatch; revert first
  Idle                    → sweep leftovers; report progress
}
The orchestrator does by hand only: changes on the order of one or two lines,
and research. Everything else is dispatched.
```

**Workflow 3: the worker's one execution**

```
Receive the task (role context + the issue: goal, bounds, done-check)
  → Check the task is specified: goal or done-check missing/vague → do not start;
    return it to the orchestrator
  → Take position: own branch + worktree; record a starting-state snapshot (baseline)
  → Implement, using the execution skills (TDD, systematic debugging); touch only what
    is in the task's scope
       On any of four events → stop, escalate to the orchestrator, wait:
         touching core architecture | an irreversible action needed |
         done-check wrong or unreachable | stuck on a direction call
  → Rebase onto current main; resolve own conflicts
  → Run the done-check on the final state; keep the evidence (commands, exit codes, output)
  → Open the PR: restate the goal — "done, evidence here"
  → Drive CI green: red caused by own diff → fix; red not one's own → escalate
  → Hand back to the orchestrator; leave the worktree in place (removed at merge)
  ← Returned (goal not met) → fix the named gap → repeat rebase → done-check →
    evidence → hand back
```

Workflow 1 is one task crossing both roles; workflow 2 is the orchestrator's side; workflow 3 is
the worker's side — every step of workflow 1 maps to a step in workflow 2 or 3.

**The two roles.** Orchestrator — converse, discuss, relay between human and workers, gate and
merge; stays responsive. Worker — a fixed-role executor; one task maps to one branch and one
worktree; delivers evidence; never merges; stops and escalates on anything major — and an action that is
irreversible (deleting data, force-pushing shared branches, publishing, writes leaving the repo)
always stops for the human's authorization before anyone performs it.

## 5. Implementation

Claude Code and Codex each ship their own harness — sessions, tools, permissions, sandboxes. But
on the native harness alone, agents will not run the workflows of section 4: the native layer has
no notion of roles, no dispatch-and-acceptance protocol, and no concept of multi-agent parallel
collaboration.

This project therefore adds a **supplementary harness** on top of the native one. The available
building blocks:

- **hooks** — inject instructions at fixed points in the session lifecycle (e.g. delivering the
  working method at session start);
- **skills** — mature methods invoked at the matching workflow step;
- **custom subagents** — role definitions that fix a worker's or reviewer's system prompt,
  skills, tools, and model;
- **external agent processes** — another agent invoked as a command-line process (e.g. Claude
  Code invoking `codex exec`), serving as a de facto subagent for worker or reviewer duty; the
  role is injected through the dispatch prompt, the sandbox is OS-enforced, and the process
  lifetime is managed independently;
- **scripts** — mechanical steps (dispatch, review-packet assembly) made fixed;
- and **hybrids** of the above.

Which blocks to choose, and how to combine them, has exactly one criterion: **whether they
reliably realize the workflows of section 4.**

**This supplementary harness is, in essence, context engineering: it decides what each agent
sees, when, and in what form — working method, role identity, task content, available skills.**
A structural consequence follows: **the orchestrator's harness and the worker's harness are two
separate sets, designed and delivered separately.** The orchestrator's set is built around
communication and decisions — requirements-clarification skills, the operational context for
dispatch, acceptance and merging, reporting to the human. The worker's set is built around
execution — implementation skills (test-driven development, systematic debugging), task
boundaries, evidence duties, escalation rules. Each set is complete on its own and they are never
mixed: a worker has no need to see merge and release operations; an orchestrator has no need to
load implementation methods. The two sets share only the workflow contract itself — the parts
where the roles interlock and must know each other (who delivers what, who accepts, who merges).

Five engineering sub-problems have been identified in building this layer: **delivery** (how the
constraints are guaranteed to reach every agent), **lifetime** (dispatched processes must survive
independently of the session), **asymmetry** (the two native environments differ in capability, so
one role needs two bindings), **enforcement** (pure prompt constraints fail silently; some edges
must rest on native enforcement), and **observability** (how the orchestrator learns a worker's
true state rather than its self-report). These five belong to the architecture document; this
document does not expand on them.

## 6. Success criteria

Success is defined as: the problems of section 1 no longer occur. Item by item:

1. **The human no longer schedules**: with several pieces of work in parallel, the human's
   actions reduce to giving direction and inspecting results.
2. **Zero evidence-free completion claims pass acceptance.**
3. **Zero unauthorized irreversible operations occur.**
4. **The core is no longer lost**: after acceptance, a deliverable's core is still the goal its
   issue set; rework of the "periphery perfected, trunk lost" kind no longer appears.
5. **Fresh sessions no longer violate the working conventions** (misplaced files, acting where
   asking was due).
6. **The rules layer stays readable end-to-end**: every rule traces to a problem above or a reuse
   decision in section 2; whatever cannot be traced has in fact been deleted.

Observation metrics (in service of the above; not criteria themselves): N = *(value to be set by
the human)* genuinely parallel lanes without interference; human involvement limited to direction and
criteria-setting, authorization of irreversibles, and sign-off on architecture-level changes and
major releases; zero startup ceremony for a demo project.

## 7. Boundaries

- **Never replaces the native harness; supplies only the difference.**
- **Zero errors is not the goal**: outside irreversible accidents, problems surface in running
  and are fixed once surfaced; acceptance rules on "goal met within the declared bounds," not on
  perfection.
- **No preventive construction**: rules are established by real incidents, structure is built by
  real need; anything constructed in advance for an imagined problem is presumed wrong.

**Existence criterion (operative clause):** every rule, file, and mechanism in this supplementary
harness must trace back to a problem in section 1 or a reuse decision in section 2; whatever
cannot be traced is to be deleted.
