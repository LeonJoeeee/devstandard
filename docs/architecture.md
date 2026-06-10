# DevBook — Architecture

> This document is the **shared baseline** for all parallel work: read it before starting any task. Changing anything written here = touching the core: it must go through a public merge + human approval + an ADR (see `adr/0000`). The *why* lives in `adr/`; this file only states *what is*.

## 1. Content structure: three pillars

1. **Development standards** (worktree / git / CI/CD): the rules and mechanics of how code flows;
2. **Document management** (PRD / architecture / ADR): how project-level docs are written, maintained, and updated;
3. **Task execution** (the Workflow harness): how a single task is carried out; SDD demoted to an optional aid.

## 2. Plugin shape

A lean plugin: **manifest + one SessionStart hook + one lean router skill + many on-demand reference files**.

```
devbook/
├── .claude-plugin/plugin.json        # minimal manifest (name/version/description)
├── hooks/
│   ├── hooks.json                    # SessionStart (matcher: startup|clear|compact)
│   └── session-start                 # cats ONLY the router SKILL.md as additionalContext
├── skills/devbook/
│   ├── SKILL.md                      # lean router: trigger test + phase→file dispatch table
│   └── reference/
│       ├── methodology-core.md       # reference-chain model, invariants, safety floor (migrated)
│       ├── L3-research.md            # direction research (migrated)
│       ├── done-check.md             # shape → definition-of-done dispatch table (migrated)
│       ├── brainstorm-split.md       # splitting oversized work into medium pieces (migrated)
│       ├── metric-appendix.md        # improve-a-metric shape only (migrated)
│       ├── task-workflow-how.md      # how to AUTHOR a task's workflow: skeleton + rules + example (new; absorbs L2/L1 content)
│       ├── prd-how.md                # how to write a PRD + template (new)
│       ├── architecture-how.md       # how to write an architecture doc + template (new)
│       ├── adr-how.md                # ADR trigger / numbering / supersede rules + template (new)
│       ├── worktree-how.md           # worktree mechanics (specialized from superpowers)
│       ├── merge-finish-how.md       # delivery / merge / finish steps (specialized from superpowers)
│       └── cicd-how.md               # CI/CD generation rules + templates (new)
└── docs/                             # DevBook's own PRD/architecture/ADRs (this directory)
```

**Two on-demand loading seams — never break them**: a skill's body enters context only when the skill is invoked; reference files enter context only when explicitly Read. **All cross-file references use plain relative paths, never `@path`** (which force-loads everything at session start).

Router budget: target ≤ 1,500 tokens, ceiling ~2,000. The router only dispatches: the trigger test (repo creation or not), the lifecycle order, the two-axis human gate in one line, the safety floor in one line, and the phase→file dispatch table. All content lives in reference files.

## 3. Lifecycle (repo-creation projects)

```
Human asks to create a repo
  → write the PRD (what / why / what counts as done)
  → write the architecture doc (this file's counterpart) + start the ADR log
  → scaffold a thin skeleton: interfaces and boundaries land as code,
    pinning where parallel work plugs in
  → generate CI/CD (test robot + tag-triggered release pipeline)
  → split into tasks, fan out parallel sessions
  → iterate; changing core architecture = public merge + human approval
    + update this file + write an ADR
```

In-repo changes skip all of the above: each is a single task that goes straight into the harness.

## 4. Execution model: two layers

**Outer (project → tasks).** One Claude Code session = one branch = one worktree = one task. Task sessions only DELIVER (push their branch); **merging is main's act**: CI must be green; architecture-touching merges additionally pass the human and produce an ADR. All sessions treat this architecture document as the shared reference; if the baseline itself turns out wrong, fix it through the same public-merge path — never silently build against a known-wrong baseline.

**Inner (inside one task).** **The Workflow tool itself is the harness** — orchestration, parallel verification, schema-validated handoffs, budget control, and the quality patterns are all native to it. DevBook adds only a **thin shell**: the `task-workflow-how.md` reference file, which the session reads and then **authors a fresh workflow fitted to this task** (ADR 0006). The authored workflow follows this skeleton:

```
0 Set the bar    Define "done" for this task's shape (machine-judgeable)
1 Emit a design  One agent produces the design / root-cause analysis
                 (prompts fit the task shape)
2 Refutation     N independent clean-context agents attack it in parallel
3 Implement      Sequential slices: write → self-verify → independent
                 review → fix (parallel firepower goes to review, not writing)
4 Close          Self-judge against the bar with real evidence (commands,
                 exit codes, output); completeness critic; green before delivery
```

Hard rules the shell imposes on authoring: no code before the refutation passes; dependent slices are written sequentially (a plain loop, not concurrent fan-out); an absent/dead reviewer counts as red, never silently dropped; closing evidence = command + exit code + output, not prose; panel sizes scale with task weight. **The human gate lives between workflow runs, not inside one** (a workflow cannot ask the human mid-run): if refutation hits a two-axis issue, the run ends, the session surfaces it to the human, then continues with a new run.

Implementation is sequential within a task and verification is parallel → inner agents need no worktrees of their own (no nesting with the outer layer). DevBook ships **no bundled workflow scripts** — method, not machinery.

## 5. What lands in a target project

Every repo-creation project gets: `docs/PRD.md`, `docs/architecture.md`, `docs/adr/NNNN-*.md`, CI/CD config, and a thin skeleton. Templates live in the plugin's `*-how.md` reference files; the project holds only instances.

## 6. Sources

- `_source/METHODOLOGY.md`: the old method in full; the migrated reference files come from it;
- `_source/superpowers-porting-plan.md`: per-skill verdicts for all 14 superpowers skills + landing map + a 12-entry conflict register (DevBook policy always wins);
- superpowers is a quarry, not a dependency: MIT-licensed, verbatim porting allowed with attribution; the final environment does not install it.
