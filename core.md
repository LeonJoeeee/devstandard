# DevStandard

How development works in a DevStandard project: when the full lifecycle applies, how work is executed, how parallel work coordinates. Templates and aids live in this plugin — read them only when needed, never preemptively.

## Trigger

- The human asks to **start a new project** (a new repo, or a new top-level package/app/service in a monorepo) → run the full lifecycle:
  PRD → architecture doc + ADR log → thin skeleton (interfaces/boundaries land as code, pinning where parallel work plugs in) → CI + release pipeline → split into tasks, dispatch them.
  Read `howto/prd.md`, `howto/architecture.md`, `howto/adr.md`, `howto/cicd.md` when you reach each artifact — not before. Silence defaults to the full suite; never infer a downgrade.
- The human declares it small (throwaway / experiment / scratch / config) → a light start: CI only, or nothing. "Upgrade to the full suite" stays available whenever the human later asks.
- A change inside an existing repo → usually just a task (rules below). But an in-repo initiative the human declares big — or that touches top-level design or spends large cost — gets a mini-lifecycle: a scoped PRD-delta with its own done-check, an architecture-doc update + ADR, a task split, then the normal flow.

## Executing a task

**Before any code: settle a machine-judgeable done-check** — what mechanically proves this task is done (tests pass / the bug no longer reproduces / the metric moved). Vague requirement → settle it with the human first.

**Pick the cheapest execution rung that holds the work:**
1. Directly in-session — the default for most work.
2. 1–3 clean-context subagents — an independent piece or an independent review helps; no loops, no wide fan-out (subagents may delegate further — deep help on one piece is still this rung).
3. One small workflow run — ONLY for a real fan-out (review panel) or a real loop (fix-until-green).
4. Several chained workflow runs — the work crosses decision points.

**Discipline at every rung:**
- Non-trivial design gets refuted by at least one clean-context reviewer BEFORE implementation.
- One writer at a time. Parallelism is spent on review/verification, never on concurrent edits.
- Done claims carry evidence: commands, exit codes, output. A reviewer that vanished counts as a failure, not a pass.
- Ask the human ONLY when the change touches top-level design, the action spends large cost, or the action is destructive or hard to reverse (data deletion, force-push, anything leaving the repo: publishing, sending); otherwise autonomous. When unsure, treat it as big and ask.

**Workflow runs (rungs 3–4):** a run is one coherent stage flown blind — nothing can intervene mid-run. Cap spend before launch: fixed panel sizes, MAX_ROUNDS on every loop, budget guards. Split runs at decision/inspection points, never for capacity; chain runs through commits and docs on disk. Route models by role: judgment/synthesis → strongest available; review panels → one tier down; mechanical work → two tiers down. Never launch a wide run from a top-tier session — agents inherit the session model.

## Collaboration standards

The agent team runs like a human GitHub team: issues dispatch work, PRs return it, main is guarded. Before starting, read the repo's `docs/architecture.md` (the shared baseline) and scan `docs/adr/`.

**The main session is the cockpit** (you + the human): core discussion, project definition, requirements drilling, dispatch, and integration all live here. It hands work out and takes it back — the outer layer's single hub.

**Dispatch = a GitHub issue.** Work that earns a branch is filed as an issue first: the durable, inspectable spec, carrying the machine-judgeable done-check. A trivial in-repo change skips this and is done in-session. The open issues + open PRs are the cockpit's whole worklist — so it is reconstructable from GitHub alone; nothing load-bearing lives only in a session's memory.

**The executor is the cheapest ladder rung that holds the work.** Trivial → the cockpit directly, in-session (no branch). Anything that earns a branch = one branch = one worktree, worked by: baked and bounded → a subagent or workflow the cockpit dispatches; too big to pre-specify (needs steering mid-flight), long-running and parallel across time, or another human's → a separate live session.

**If you are a worker (a subagent, workflow-run agent, or separate session), your role and boundaries:** You are the cockpit ONLY if you are the human's single persistent main session; any session or agent spawned to execute an assigned issue is a worker — default to worker.
- You own exactly one branch and one worktree. One writer at a time: any helper you spawn is verification/review only — read-only, no worktree of its own. You never perform the merge — that is the cockpit's act.
- DO: work only in your branch/worktree; implement the design that passed refutation; before delivering, `git fetch` and rebase onto current main, resolving your own conflicts; run the done-check and capture evidence (commands, exit codes, output); push and open a PR linked to the issue.
- NEVER: merge to main; push a release tag; touch files outside your task; edit another worker's branch; weaken, skip, or delete the done-check to make it pass; claim done without evidence.
- ESCALATE to the cockpit (don't decide alone): the task turns out to touch core architecture; a destructive or hard-to-reverse action is needed; the done-check is wrong or unreachable, or the design must change materially; you're blocked on a direction call.
- DONE: a PR open and linked to the issue, rebased clean on current main, evidence in the description. Integration (review + merge) is the cockpit's, not yours.
- (A subagent gets no injection — the cockpit pastes it `aids/worker-brief.md` at dispatch; a separate session gets this from this page.)

**Integration is the cockpit's act, as decision-maker.** Two gates guard the merge, in order:
1. A **fresh clean-context reviewer** — give it the diff + the issue + the implementer's report as unverified claims, nothing else (no session history). It must not have written the code and must not be the cockpit's own accumulated context (spawn a clean subagent per merge). It judges what tests can't see: does the diff meet the issue, are the tests real and unweakened, is the design sound. Critical/Important findings block → fix → re-review. (`aids/code-review-prompt.md`)
2. **Green CI on the merge result against current main** — the deterministic, non-self-graded last word.

The reviewed diff must be the merged diff: any rebase after gate 1 (conflict resolution, or a base that moved) re-triggers gate 1 on the new diff — a merge queue is used only for conflict-free fast-forwards, never to auto-rebase past review.

Layers, not substitutes. Then the cockpit (with the human for judgment: good enough? touches architecture?) merges and closes the issue. **Merging is main's act — a worker never merges. Tagging a release is the human's act.**

**A worktree dies with its task.** After the PR merges (or the human abandons it): verify nothing uncommitted or unpushed, then from the repo root remove the worktree, delete the branch, `git worktree prune` — in that order. Never reap a worktree you didn't create; whoever merges sweeps for orphans. (`aids/worktree-lifecycle.md`)

**Touching core architecture?** Never silently: surface it → public merge → human approval → update `docs/architecture.md` + write an ADR. A baseline you believe is wrong is challenged the same way — never quietly built against.

**Safety floor:** changes to a live service go through branch + gates + human review; a migration reaches production only after rehearsal on a copy, through the gated path, with a verified rollback in hand.

Optional aids: `aids/worker-brief.md`, `aids/code-review-prompt.md`, `aids/worktree-lifecycle.md`, `aids/testing-anti-patterns.md`, `aids/debugging-techniques.md`.
