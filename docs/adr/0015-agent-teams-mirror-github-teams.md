# 0015 — Agent teams mirror a human GitHub team: issues dispatch, PRs return, the ladder picks the executor

Status: Accepted (2026-07-09). Supersedes 0005.

## Context

0005 fixed the parallel model as "one session = one branch = one worktree = one task." Three things push a refinement.

1. **"= one session" is the weakest link.** What is load-bearing is one-branch-one-worktree (isolation + clean integration); *who* executes inside is an execution-ladder choice, not a fixed identity. The rigid identity also contradicts 0009's own doctrine — sessions are mortal, and work must survive into another session.
2. **In practice the human does the core thinking with one persistent "main" session** (project definition, requirements drilling), and most tasks, once drilled, are baked enough to hand to a subagent or a workflow rather than a whole separate session — the cheapest rung that holds the work.
3. **Dispatch and hand-back had no durable substrate:** a worker's assignment lived in an ephemeral first prompt, and "who merges" was defined three incompatible ways across the docs.

## Decision

Model the agent team on a human GitHub team, on GitHub-native, durable artifacts:

1. **The main session is the cockpit** (human + Claude): core discussion, project definition, requirements drilling, dispatch, and integration decisions live here. It is the outer layer's single hub — it fans work out and fans it back in.
2. **Dispatch = a GitHub issue.** Work that earns a branch is filed as an issue: the durable, inspectable task spec carrying the done-check (replacing the ephemeral first prompt). A trivial in-repo change skips this — done in-session (the anti-ceremony floor, 0014).
3. **Executor = the cheapest ladder rung that holds the work** (the execution ladder, 0008). One task = one branch = one worktree; the executor inside is chosen, not fixed: trivial → the cockpit directly; baked/bounded → a subagent or workflow; too big to pre-specify (needs mid-flight steering) / long-running and parallel across time / another human's → a separate live session. "= one session" is retired as an invariant and becomes the top rung.
4. **Return = a PR** linked to the issue; the worker never writes main. While the author is live it rebases its own branch onto current main and resolves its own conflicts (it has the context); it never performs the merge. When the author is ephemeral (a subagent/workflow that ended at PR-open) and a later merge forces a conflicting re-rebase, the cockpit files it as a new bounded issue and dispatches a fresh worker — the rebase duty falls to whoever is live, never to a dead author.
5. **Integration is the cockpit's act as decision-maker.** For each PR it spawns a **fresh clean-context reviewer** (sees only the diff + the issue) — never grading its own work, never anchored by the cockpit's accumulated context — then green CI against current main (the two gates, 0011); then, with the human for judgment (good enough? touches architecture → human + ADR), it merges and closes the issue.
6. **Roles and boundaries are written down** so any executor knows them: you own your branch, you deliver a PR, you never merge or tag, your done-check is in the issue. A separate session learns this from injected `core.md`; a subagent, which gets no injection, learns it from `aids/worker-brief.md` pasted in at dispatch.

Surviving 0005 unchanged: CI/CD in the standard (green-before-merge; tag-triggered release; the human decides when to ship); architecture-touching merges pass the human + an ADR; a worktree dies with its task (0012).

## Consequences

The team runs on issues → branches → PRs → merges — the flow humans already converged on (0009), now literally reused. Everything durable is a GitHub artifact, so the cockpit is reconstructable for free (worklist = open issues + PRs) — no special rule needed. Executor cost scales with task difficulty instead of paying for a full session every time. Cost: the collaboration model is now large enough that it must be stated in full for workers, so core.md's every-session budget is relaxed (recorded as an amendment on 0007: hard ceiling ~3,000, kept lean) to carry roles, contract, and boundaries inline. The issue→PR flow binds work that earns a branch; trivial changes stay in-session.
