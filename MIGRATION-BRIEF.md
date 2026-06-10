# DevBook — Migration / Build Brief

> **Self-contained handoff.** A fresh Claude Code session (which will NOT have the prior conversation) should be able to build DevBook from this file alone. Written 2026-06-08.

---

## 0. How to use this brief (read first)

1. Open a fresh Claude Code session **in this directory** (`~/projects/devbook`). Fresh session = clean context + correct cwd; the prior design session was very long.
2. Tell that session: **"Read `MIGRATION-BRIEF.md`, then let's build DevBook."**
3. The agent should: read this brief → confirm the **OPEN DECISIONS (§6)** with the human → then build per **§5**.
4. **Dogfood option:** build DevBook *using* the existing `development-playbook` skill/method (invoke it manually). Good real-world validation of the method while you build its successor.

---

## 1. What we're building

**DevBook = a Claude Code PLUGIN** that packages a full-SDLC development methodology for personal, general-purpose project development in Claude Code (not tied to any orchestrator).

It is the **evolution of the existing `development-playbook` skill**: same core model, now **expanded** to a full lifecycle — **PRD → Architecture → ADR → [per task: worktree → design → SDD → code+tests → review → merge] → iterate** — and **repackaged as a lean plugin** so (a) context splits per phase and (b) triggering is reliable via a hook.

---

## 2. The core methodology (content = source of truth)

The model, in one paragraph: development is a **reference chain** `external world → top-level design → mid-level design → low-level code`. Three abstraction layers, each checked against the layer above by **context-clean adversarial review**: **L3** research/pick-direction (top-level design), **L2** mid-level design = the **SDD** (pseudocode), **L1** code + tests. An **outer loop** drives a requirement to a per-shape **done-check**, iterating until met. The human is involved at **one altitude** — an approval point at the L3→L2 handoff, firing on two axes: *touches top-level design* OR *spends large cost*. Requirements come in **shapes** (build / feature / bug / refactor / improve-a-metric / optimize-perf); a **dispatch table** maps shape → done-check; metric-improvement is a slimmed **appendix**, not the core. Complex (> one service) tasks start with a **brainstorm-split** into medium pieces.

**Full text to migrate is staged here:** `_source/METHODOLOGY.md` (the model, ~7.2k words), `_source/SKILL.md` (current execution checklist), `_source/README.md`. These are the content you split into the plugin's router + reference files.

---

## 3. Packaging decision — DECIDED: Option B (lean plugin)

A **thin plugin shell** = `plugin.json` manifest + **ONE SessionStart hook** + **ONE lean "router" skill** + **many cheap reference files**; persistent artifacts live as **repo docs in the target project**; worktree/merge **delegate to superpowers** (or self-contained — see §6).

Rejected alternatives (don't revisit without reason):
- **Option A (bare skill, no plugin):** can't bundle a hook → triggering stays ~0% (see §4). 
- **Option C (one skill per phase, ~10 chained skills):** over-engineered — ~10 frontmatter blocks + ~10 slash-commands + a brittle chain, for a context win a reference file already gives. Violates the human's complexity-discipline.

**Why a plugin at all (not just a skill):** the plugin shell buys exactly two things a bare skill can't: **(1)** a SessionStart **hook** (the only reliable trigger for a methodology skill — see §4), and **(2)** clean **delegation/reuse** of superpowers' worktree/finish skills. The context-splitting itself is done by **reference files, NOT by many skills**.

---

## 4. Mechanics that MUST be respected (non-obvious; getting these wrong defeats the design)

- **Context split = two progressive-disclosure seams:** (1) a skill's `SKILL.md` body loads only when the skill is invoked; (2) sibling `reference/*.md` files load **only when the agent explicitly Reads them**. So during L3 top-level design, the agent Reads only `methodology-core.md` + `L3-research.md`; the L2 SDD 9-section format, L1 test bar, and metric appendix are **physically absent from context**.
- **NEVER use `@path` syntax** to point between files. `@path` force-loads the file at session start and **destroys the split**. Reference other files **by name / relative path that the agent Reads on demand** (this is the exact lesson from superpowers).
- **Triggering:** methodology/process skills auto-trigger **~0%** from their `description` alone (empirically verified last session with skill-creator's run_loop — 5 description rewrites, 0% on real dev tasks; the model just does the dev work without consulting a "how to develop" skill). **The fix is the SessionStart hook** that injects ONLY the lean router every session. Do **not** sink effort into description optimization for auto-trigger. (Memory: `skill-triggering-methodology-undertriggers`.)
- **Keep the router genuinely lean** — the hook pays its token cost on EVERY session (incl. non-dev ones). Router = trigger tiers + lifecycle phase order + human-gate two-axis rule + safety floor + the three invariants + a **phase → reference-file dispatch table**. Everything heavy goes in reference files.
- **Phases are reference files, not skills.** Reserve "make it a skill" only for nodes that need independent triggering/chaining (likely just the router; maybe a brainstorm-split entry).
- **Caller-perspective writing** for any description/trigger text: say *when to use*, plain language, no internal jargon (memory: `mcp-llm-to-llm-design`).

---

## 5. Target structure + build steps

### Structure
```
devbook/                                  # the plugin (this dir, once built)
├── .claude-plugin/plugin.json            # minimal manifest (see template below)
├── hooks/
│   ├── hooks.json                        # SessionStart → session-start
│   └── session-start                     # bash: inject ONLY the lean router into context
├── skills/
│   └── devbook/
│       ├── SKILL.md                      # the LEAN ROUTER (+ phase→reference dispatch table)
│       └── reference/
│           ├── methodology-core.md       # the reference-chain model, invariants, "why it works"
│           ├── L3-research.md            # L3: pick direction, desk vs measurement
│           ├── L2-sdd.md                 # L2: the SDD 9-section format + "L1 only translates" criterion
│           ├── L1-implementation.md      # L1: tests-from-SDD, "actually runs" bar
│           ├── done-check.md             # the dispatch table (shape → done-check) + outer-loop termination
│           ├── brainstorm-split.md       # complex (>1 service) → split into medium pieces
│           ├── metric-appendix.md        # improve-a-metric shape ONLY (slimmed)
│           ├── prd-how.md                # how to write/maintain docs/PRD.md (+ template)
│           ├── architecture-how.md       # how to write/maintain docs/architecture.md (+ template)
│           ├── adr-how.md                # how to write an ADR + docs/adr/NNNN-*.md template + numbering rule
│           ├── worktree-how.md           # isolate the task (delegate to superpowers OR self-contained — §6)
│           └── merge-finish-how.md       # review → merge/PR/finish (delegate to superpowers OR self-contained)
└── README.md                            # install + scope only (not the method)
```
Persistent artifacts live in the **TARGET project's repo**, NOT in the plugin:
`docs/PRD.md`, `docs/architecture.md`, `docs/adr/NNNN-title.md`. Their *templates/format* live in the paired `*-how.md` reference (so the spec lazy-loads with the procedure; the artifact body only enters context when the agent Reads the specific repo file).

### Build steps
1. `git init` here (unless §6.1 says reuse the development-playbook repo). Add a `.gitignore` for `_source/` if you don't want the scratch staging committed (or delete `_source/` after migrating).
2. Write `.claude-plugin/plugin.json` (adapt the superpowers template in `_source/superpowers-templates/plugin.json` — keep `name`/`version`/`description`/`"skills":"./skills/"`; drop the multi-IDE/marketplace cruft).
3. Write `hooks/hooks.json` + `hooks/session-start` (adapt `_source/superpowers-templates/`). The hook should `cat` ONLY `skills/devbook/SKILL.md` (the router) as additionalContext. Drop superpowers' legacy-skills warning. Keep it a tiny bash script using `${CLAUDE_PLUGIN_ROOT}`.
4. **Split `_source/METHODOLOGY.md` into the `reference/*.md` files** above (this is the bulk of the migration — it's mostly cut-and-place: §0.5→scope into router; §1/§6→methodology-core; §2 L3→L3-research; §2 L2 + SDD-format→L2-sdd; §2 L1→L1-implementation; §3 + §5 dispatch table→done-check; §7→metric-appendix; brainstorm-split→its file).
5. Write the **lean router `SKILL.md`**: trigger tiers (LOW skip / MEDIUM run / COMPLEX brainstorm-split), the lifecycle phase order, the human-gate two-axis rule, the safety floor, the three invariants, and the **phase→reference dispatch table** ("entering L3 → Read methodology-core.md + L3-research.md", etc.). No `@paths`.
6. Write the **5 new how-tos**: `prd-how.md`, `architecture-how.md`, `adr-how.md` (+ ADR template + numbering/supersede rule), `worktree-how.md`, `merge-finish-how.md` — each ends with where its repo artifact lives.
7. **Install (project-scoped first — see §6.2)** and **open a FRESH session** to test: confirm the hook fires (router shows up), confirm the agent follows the dispatch table without pulling later-phase files, then **run one real MEDIUM task** end-to-end as a dogfood. Iterate.
8. When stable: decide user-level install + naming/repo (§6), commit, push.

---

## 6. OPEN DECISIONS — confirm with the human at build start (recommendations given; the human decides)

1. **Source repo & naming.** New `~/projects/devbook` repo (recommended — plugin layout differs from the skill repo) vs reuse/rename the existing `development-playbook` repo (private GitHub: `LeonJoeeee/development-playbook`). If new: development-playbook is retired/redirected once devbook is up.
2. **Install scope + hook.** During dev: **project-scoped or uninstalled** so a half-built hook doesn't fire in every unrelated session. Final: **user-level** (general personal use). The hook injects the router into EVERY session — accepted as the price of reliable triggering; keep the router lean. **Confirm the exact local-install mechanism with claude-code-guide before installing** (don't pollute all sessions with a dev hook).
3. **Worktree / merge: delegate vs self-contained.** Delegate to `superpowers:using-git-worktrees` + `superpowers:finishing-a-development-branch` (less to maintain, but requires superpowers installed) vs self-contained `worktree-how.md` / `merge-finish-how.md` (no dependency). Recommendation: delegate, with a minimal self-contained fallback noted.
4. **Build-time details:** ADR-after-gate prescriptiveness (does the router actively say "write an ADR after every top-level-design gate decision"?); repo-doc paths (`docs/PRD.md`, `docs/architecture.md`, `docs/adr/NNNN-title.md`); ADR numbering + supersede-vs-edit rule.

---

## 7. Source material & reference paths

- **Content to migrate:** `_source/METHODOLOGY.md`, `_source/SKILL.md`, `_source/README.md` (copied here). Live skill: `~/.claude/skills/development-playbook/`. Private GitHub: `https://github.com/LeonJoeeee/development-playbook`.
- **superpowers = PACKAGING exemplar** (copy the manifest + hook *shape*, drop its cruft): `/home/leon/.claude/plugins/cache/claude-plugins-official/superpowers/6fd450765978/`. Templates staged at `_source/superpowers-templates/` (`plugin.json`, `hooks.json`, `session-start`). Reusable skills to delegate to: `superpowers:using-git-worktrees`, `superpowers:finishing-a-development-branch` (also `requesting-code-review` / `receiving-code-review` if wanted).
- **Full packaging research** (Option A/B/C detail + recommendation + all open decisions): `/tmp/claude-1000/-home-leon-projects-dev-research/17505123-2f78-41d6-9e00-1a47bc6dac15/tasks/wrubcxnlf.output` (may be cleared — the essence is in §3–§6 here).
- **skill-creator** (for description/eval IF needed — but triggering relies on the hook, not the description): `/home/leon/.claude/plugins/cache/claude-plugins-official/skill-creator/`.
- **Chinese methodology** (reference reading): `/tmp/开发手册-方法论-中文.md`.
- **CC mechanics questions** → use the `claude-code-guide` agent (plugin/skill/hook/install specifics).

---

## 8. Guardrails (the human's standing preferences — honor these)

- **Anti-over-engineering / complexity-discipline:** keep it lean. Reference files, not many skills. No ceremony for its own sake. Scale ritual to task size (don't force PRD+ADR on a one-line change).
- **No jargon in caller-facing text**; precise, plain, caller-perspective.
- **Don't pre-decide architecture:** surface dimensions, let the human decide; for big changes, paraphrase intent first and confirm before implementing.
- **The human (PI) approves direction; the agent does the build.**
- **Note:** this new project (`~/projects/devbook`) has its **own per-project memory scope** — the research project's memories won't auto-load here. This brief is the handoff.
