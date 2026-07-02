# DevStandard

How development works in every project here: when the full lifecycle applies, how work is executed, how parallel work coordinates. Templates and aids live in this plugin — read them only when needed, never preemptively.

## Trigger

- The human asks to **create a new repo** → run the full lifecycle, identical for every project, no size exceptions:
  PRD → architecture doc + ADR log → thin skeleton (interfaces/boundaries land as code, pinning where parallel work plugs in) → CI + release pipeline → split into tasks, fan out parallel sessions.
  Read `howto/prd.md`, `howto/architecture.md`, `howto/adr.md`, `howto/cicd.md` when you reach each artifact — not before.
- Any change inside an existing repo → it is just a task (rules below). No project-level ceremony.

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
- Ask the human ONLY when the change touches top-level design or the action spends large cost; otherwise autonomous. When unsure, treat it as big and ask.

**Workflow runs (rungs 3–4):** a run is one coherent stage flown blind — nothing can intervene mid-run. Cap spend before launch: fixed panel sizes, MAX_ROUNDS on every loop, budget guards. Split runs at decision/inspection points, never for capacity; chain runs through commits and docs on disk. Route models by role: judgment/synthesis → strongest available; review panels → one tier down; mechanical work → two tiers down. Never launch a wide run from a top-tier session — agents inherit the session model.

## Collaboration standards

- One task = one branch = one worktree = one session. Before starting: read the repo's `docs/architecture.md` (the shared baseline) and scan `docs/adr/`.
- Deliver by pushing your branch (open a PR where the project uses them). **Merging is main's act**: CI must be green. Never merge or push to main from a task session.
- Touching the core architecture? Never silently: surface it → public merge → maintainer approval → update `docs/architecture.md` + write an ADR. A baseline you believe is wrong is challenged the same way — never quietly built against.
- Safety floor: changes to a live service go through branch + test gate + human review; never run a migration on production data — only on a copy.
- Optional aids in this plugin: `aids/code-review-prompt.md`, `aids/testing-anti-patterns.md`, `aids/debugging-techniques.md`.
