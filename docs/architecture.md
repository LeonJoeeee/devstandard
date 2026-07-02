# DevStandard — Architecture

> This document is the **shared baseline** for all parallel work: read it before starting any task. Changing anything written here = touching the core: it must go through a public merge + human approval + an ADR (see `adr/0000`). The *why* lives in `adr/`; this file only states *what is*.

## 1. What DevStandard is

DevStandard holds exactly the three things Claude Code does not do natively:

1. **Discipline** — the rules a machine won't impose on itself: settle a done-check before starting, get the design refuted before code, close on evidence, when to ask the human, how money is spent;
2. **Project memory** — the PRD / architecture / ADR document set in each target repo: the only thing that keeps parallel sessions aligned and preserves the *why*;
3. **Reliable triggering** — a SessionStart hook, so the above is present in every session without being asked.

It deliberately does NOT teach orchestration (the Workflow tool is the harness and already knows how — ADR 0006), does not bundle workflow scripts, does not name models (model/quota policy is personal config in `~/.claude/CLAUDE.md`, not method), and does not depend on superpowers (a quarry only — ADR 0002).

## 2. Plugin shape (ADR 0007)

```
devstandard/
├── .claude-plugin/plugin.json   # minimal manifest (name/version/description)
├── hooks/
│   ├── hooks.json               # SessionStart (matcher: startup|clear|compact)
│   └── session-start            # cats ONLY core.md as additionalContext
├── core.md                      # ONE PAGE, injected into every session:
│                                #   trigger rule + execution discipline
│                                #   + collaboration standards + howto pointers
├── howto/                       # read ONLY at repo creation:
│   ├── prd.md                   #   how to write the PRD + template
│   ├── architecture.md          #   how to write the architecture doc + template
│   ├── adr.md                   #   ADR trigger / numbering / supersede + template
│   └── cicd.md                  #   CI + release pipeline rules + templates
└── aids/                        # optional, read when useful (ported from
    ├── code-review-prompt.md    #   superpowers, MIT, attribution kept):
    ├── testing-anti-patterns.md
    └── debugging-techniques.md
```

There is no router and no skill: the content is small enough that the hook injects `core.md` directly. **Budget: core.md stays at ~one page (target ≤ 800 tokens, hard ceiling ~1,000)** — it is paid for in every session. Everything else loads only when explicitly Read. **Cross-file references use plain relative paths, never `@path`** (which force-loads at session start and destroys the on-demand split).

## 3. Lifecycle (repo-creation projects)

```
Human asks to create a repo
  → write the PRD (what / why / what counts as done)        [howto/prd.md]
  → write the architecture doc + start the ADR log          [howto/architecture.md, adr.md]
  → scaffold a thin skeleton: interfaces and boundaries
    land as code, pinning where parallel work plugs in
  → generate CI + the release pipeline                      [howto/cicd.md]
  → split into tasks, fan out parallel sessions
  → iterate; changing core architecture = public merge +
    human approval + update the architecture doc + an ADR
```

The same full lifecycle applies to every repo-creation project — no size tiers (ADR 0004). In-repo changes skip all of it: each is a single task executed under the rules below.

## 4. Execution model: two layers

**Outer (project → tasks).** One Claude Code session = one branch = one worktree = one task. Task sessions only DELIVER (push their branch); **merging is main's act**: CI must be green; architecture-touching merges additionally pass the human and produce an ADR (ADR 0005). All sessions treat this architecture document as the shared reference; a wrong baseline is challenged through the same public-merge path, never silently built against.

**Inner (inside one task) — the execution ladder (ADR 0008).** Pick the cheapest rung that holds the work:

```
① in-session directly          — the default for most work
② 1–3 clean-context subagents — an independent piece or review helps;
                                 no loops, no wide fan-out
③ one small workflow run       — ONLY for a real fan-out (review panel)
                                 or a real loop (fix-until-green)
④ several chained runs         — the work crosses decision points
```

Discipline at every rung: machine-judgeable done-check before starting; design refuted by clean-context review before code; one writer at a time (parallelism is spent on verification, never on concurrent edits); done claims carry evidence (commands, exit codes, output) and an absent reviewer counts as red; the human is asked only on the two axes (touches top-level design, or spends large cost).

Workflow runs (rungs ③④): **a run = one coherent stage you can fly blind through** — nothing can intervene mid-run, so spend is capped before launch (fixed panel sizes, MAX_ROUNDS, budget guards) and runs split at decision/inspection points, never for capacity. Models route by ROLE in relative tiers: judgment/synthesis → strongest available; review panels → one tier down; mechanical work → two tiers down (no concrete model names in DevStandard — that is personal config). Runs chain through on-disk state (commits + docs), not native resume.

Implementation is sequential within a task and verification is parallel → inner agents need no worktrees of their own (no nesting with the outer layer).

## 5. What lands in a target project

Every repo-creation project gets: `docs/PRD.md`, `docs/architecture.md`, `docs/adr/NNNN-*.md`, CI + release pipeline config, and a thin skeleton. Templates live in the plugin's `howto/` files; the project holds only instances.

## 6. Sources

- `_source/METHODOLOGY.md` — the predecessor method; its surviving essence is condensed into core.md's discipline rules;
- `_source/superpowers-porting-plan.md` — per-skill verdicts + the 12-entry conflict register (DevStandard policy always wins);
- `_source/workflow-feature-research.md` and `_source/workflow-deep-dive-report.md` — the Workflow evidence base (execution model, single-run bounds, authoring rules) behind ADR 0006/0008.
