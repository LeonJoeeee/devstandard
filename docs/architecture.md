# DevStandard — Architecture

> This document is the **shared baseline** for all parallel work: read it before starting any task. Changing anything written here = touching the core: it must go through a public merge + human approval + an ADR (see `adr/0000`). The *why* lives in `adr/`; this file only states *what is*.

## 1. What DevStandard is

DevStandard holds exactly the three things Claude Code does not do natively:

1. **Discipline** — the rules a machine won't impose on itself: settle a done-check before starting, make the design survive a challenge before code, close on evidence, when to ask the human, how money is spent;
2. **Project memory** — the PRD / architecture / ADR document set in each target repo: the only thing that keeps parallel sessions aligned and preserves the *why*;
3. **Reliable triggering** — a SessionStart hook, so the above is present in every session without being asked.

It deliberately does NOT teach orchestration (the Workflow tool is the harness and already knows how — ADR 0006), does not bundle workflow scripts, does not name models (model/quota policy is personal config in `~/.claude/CLAUDE.md`, not method), and does not write craft content of its own: it is the method layer wrapped around its two siblings — Claude Code (the mechanics) and superpowers (the per-step craft, assumed installed; the flow points at its skills by name, and on any conflict this method wins — ADR 0016).

## 2. Plugin shape (ADR 0007)

```
devstandard/
├── .claude-plugin/plugin.json   # minimal manifest (name/version/description)
├── hooks/
│   ├── hooks.json               # SessionStart (matcher: startup|clear|compact)
│   └── session-start            # emits the forced-read instruction (not core.md's text)
├── core.md                      # one page (ceiling ~5,000 tok), read at session start:
│                                #   trigger rule + execution discipline
│                                #   + collaboration standards + howto pointers
├── howto/                       # read when their artifact is due (mostly repo creation):
│   ├── prd.md                   #   how to write the PRD + template
│   ├── architecture.md          #   architecture doc + split-on-zoom rule + template
│   ├── design-spec.md           #   when a change earns a design spec + template (0017)
│   ├── adr.md                   #   ADR trigger / admission test / supersede + template
│   └── cicd.md                  #   CI + release pipeline rules + templates
└── aids/                        # optional, read when useful:
    ├── worker-brief.md          #   role/boundaries brief the main session pastes to a subagent
    ├── worktree-lifecycle.md    #   worktree birth + death checklist
    └── code-review-prompt.md    #   the check-1 reviewer prompt (fresh, no history)
                                 #   (review/worktree files adapted from superpowers, MIT;
                                 #    craft is pointed at superpowers skills, never copied — ADR 0016)
```

There is no router and no skill: the SessionStart hook instructs the model to Read `core.md` in full as its mandatory first action — delivery by forced read, not inline injection (the harness inline-caps hook output near ~10KB, so injecting the whole page truncated it; ADR 0019 amending 0007). **Budget: hard ceiling ~5,000 tokens, kept as lean as the content earns (ADR 0007 as amended — 0015, then 2026-07-16; the live count and its measuring command live in the repo CLAUDE.md)** — it is paid for in every session (the model still reads the whole page each time). Everything else loads only when explicitly Read. **Cross-file references use plain relative paths, never `@path`** (which force-loads at session start and destroys the on-demand split).

## 3. Lifecycle (repo-creation projects)

```
Human asks to start a new project
  → write the PRD (what / why / what counts as done)        [howto/prd.md]
  → write the architecture doc + start the ADR log          [howto/architecture.md, adr.md]
  → scaffold a thin skeleton: interfaces and boundaries
    land as code, pinning where parallel work plugs in
  → generate CI + the release pipeline                      [howto/cicd.md]
  → split into tasks, dispatch them (issue → PR, ADR 0015)
  → iterate; changing core architecture = public merge +
    human approval + update the architecture doc + an ADR
```

The full lifecycle runs when the human starts a new project (ADR 0014); silence defaults to full. A project the human declares small gets a light start (CI only, or nothing); an in-repo change is usually just a task, but an initiative the human declares big gets a mini-lifecycle. Repo creation is the common special case; a new package/app/service in a monorepo fires the same lifecycle in its subtree.

## 4. Execution model: two layers

**Outer (project → tasks) — an agent team mirroring a human GitHub team (ADR 0015; ceremony made universal by 0022).** A persistent **main session** (human + Claude) runs the show: it holds the core thinking, files dispatched and human-raised work as **GitHub issues**, and integrates the results. **Every change rides a branch + PR through the two checks (0022)** — issues gate on dispatch or a human request, not on size, and a main-session self-noticed small fix skips the issue but never the branch/PR. One task = one branch = one worktree; who executes inside is the cheapest level that fits — the main session directly (on a short branch), a subagent/workflow it hands the task to, or a separate live session when the task can't be fully specified up front, runs for days in parallel, or is another person's. A worker delivers a **PR** (rebased on current main) and never merges. **Integration is the main session's act:** a fresh reviewer (no prior history), then green CI against current main, then merge + close the issue (if any); an architecture-touching change gets the human's approval *before* that merge and produces an ADR. All sessions treat this architecture document as the shared reference; a baseline you believe is wrong is challenged through the same open-PR path, never quietly built against.

**Inner (inside one task) — the execution ladder (ADR 0008).** Pick the cheapest rung that holds the work:

```
① in-session directly          — the default for most work
② 1–3 fresh subagents (no history) — an independent piece or review helps;
                                 no loops, not many at once
③ one small workflow run       — ONLY for genuinely many parallel agents
                                 (a review panel) or a loop (fix until tests pass)
④ several chained runs         — the work crosses decision points
```

Discipline at every level: a machine-judgeable done-check before starting; a substantial change writes a 1–3-page design spec first (`docs/specs/`, 0017); the design must survive a challenge before code, and every gating review uses a clean reviewer — freshly spawned, no history, never a context-inheriting fork (0017); one writer per worktree (parallelism goes to review, never to two writers on the same files); done claims carry evidence (commands, exit codes, output) and a reviewer that returns no verdict counts as a failure; the human is asked only on the three axes (touches top-level design, costs a lot, or is destructive / hard to undo).

Workflow runs (levels ③④): **a run = one coherent stage that goes start-to-finish with no way to step in partway** — so cost is capped before launch (fixed reviewer counts, round limits, spending limits) and runs split at decision/inspection points, never just for capacity. Models route by ROLE, by relative strength: judgment/synthesis → the strongest available; review panels → one step down; mechanical work → two steps down (no concrete model names in DevStandard — that is personal config). Runs chain through on-disk state (commits + docs), not native resume.

Implementation is sequential within a task and verification is parallel → inner agents need no worktrees of their own (no nesting with the outer layer).

## 5. What lands in a target project

Every repo-creation project gets: `docs/PRD.md`, `docs/architecture.md`, `docs/adr/NNNN-*.md`, CI + release pipeline config, a repo-root `CLAUDE.md` (operational memory: commands, gotchas, the worktree copy-list — grown one line at a time by merge-time write-back, 0018), and a thin skeleton. As the project grows: a substantial change adds a date-named, status-headed spec under `docs/specs/` (never deleted — a second decision log), and a subsystem the overview can no longer explain gets its own `docs/architecture/<subsystem>.md` (split on zoom; both 0017). Templates live in the plugin's `howto/` files; the project holds only instances.

## 6. Sources

- The predecessor method (the retired `development-playbook` skill) — its surviving essence is condensed into core.md's discipline rules;
- `_source/superpowers-porting-plan.md` — per-skill verdicts + the 12-entry conflict register (DevStandard policy always wins);
- `_source/superpowers-coupling-map.md` — the full 14-skill coupling survey behind the 0016 amendment (pointer placement, never-point reasons, hazards register);
- `_source/devstandard-optimization-sweep.md` — the six-angle optimization sweep behind the v0.7.0 fixes (merge authority, protected-main lanes, setup mechanics);
- `_source/superpowers-absorption-quarry.md` — the 10-skill quarry behind v0.9.0 (receiving discipline, lifecycle holes; the never-pointed set is quarried out);
- `_source/full-audit-v090.md` — the seven-lens whole-plugin audit behind v0.9.1 (verdict: structure held; six doc fixes);
- `_source/doc-layering-research.md` — the doc-layering evidence (Google design docs, Rust RFC, Oxide RFD, C4, arc42, agent-era practice) behind ADR 0017;
- `_source/workflow-feature-research.md` and `_source/workflow-deep-dive-report.md` — the Workflow evidence base (execution model, single-run bounds, authoring rules) behind ADR 0006/0008.
