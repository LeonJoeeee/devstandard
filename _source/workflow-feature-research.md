# Workflow Feature Research (2026-06-10)

> Produced by a 3-angle research workflow (official docs / community practice / spec-to-rules distillation; the official-docs agent died mid-run on a socket error — its ground was re-covered by the spec agent, which extracted the undocumented surface directly from the Claude Code binary v2.1.170). Informs the two OPEN harness decisions in docs/architecture.md §4.

# DevBook Harness × Workflow Tool — Synthesis Report

## 1. Workflow feature surface

**Documented officially** (https://code.claude.com/docs/en/workflows):
- Save/reuse: `/workflows` → `s` → `.claude/workflows/` (project, repo-shared) or `~/.claude/workflows/` (personal); runs as `/<name>`; project shadows personal; `/deep-research` is the reference implementation.
- `args` as a global; structured JSON passed directly; `undefined` if omitted.
- Resume: cached agent results — but docs say **same-session only** ("exit Claude Code… the next session starts the workflow fresh").
- Limits: 16 concurrent agents (fewer on small CPUs), 1,000 agents/run, **no mid-run user input** ("For sign-off between stages, run each stage as its own workflow"), no script-level fs/shell — agents do all I/O.
- Per-stage model routing; subagents always run `acceptEdits` and inherit your allowlist (pre-populate it or un-allowlisted calls prompt mid-run).
- Trigger keyword renamed `workflow` → `ultracode` in v2.1.160 (https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md).

**In the binary spec (v2.1.170) but NOT in official docs** — extracted from `/home/leon/.local/share/claude/versions/2.1.170`; readable extracts at `/tmp/wf1.txt`–`/tmp/wf4.txt`, full dump `/tmp/claude-strings.txt` (lines ~358620–358731):
- **Plugin workflow loader** (`loadPluginWorkflows`/`loadWorkflowsDir`): plugins ship `.js` workflows registered as `<plugin>:<name>`; project/user dirs override plugins; built-ins lowest (`/tmp/wf1.txt`). Zero mention in the plugins reference (https://code.claude.com/docs/en/plugins-reference).
- Resume via `Workflow({scriptPath, resumeFromRunId})` with longest-unchanged-prefix journal cache (rolling sha256 over prompt + {schema, model, isolation, agentType} + previous key) (`/tmp/wf4.txt`).
- Concurrency formula `min(16, max(2, cores−2))`, excess queues; **4096-item max** per `parallel()`/`pipeline()` (hard error); stall watchdog 180 s, ≤5 retries, 45 s throttle backoff, undocumented `opts.stallMs`.
- `opts.agentType` resolves from the same registry as the Agent tool — **DevBook custom agents are reusable**, composes with `schema`.
- `isolation:'worktree'` costs ~200–500 ms + disk per agent, auto-removed if clean, preserved if dirty; `isolation:'remote'` schema-present but "not available in this build".
- Budget: user "+Nk" directive is a **hard ceiling** shared across the whole turn; further `agent()` calls throw, in-flight agents finish, drops logged in `<failures>`. (No community sighting of "+500k"; it exists in the spec only.)
- Per-agent user **skip → `null`** and **retry** mid-run, pause/kill, `/workflows` live progress UI.
- Nested `workflow('plugin:name', args)` — one level only; child shares concurrency cap, agent counter, budget.
- Explicit opt-in clause: "the user invoked a skill or slash command whose instructions tell you to call Workflow" satisfies the trigger requirement (`/tmp/wf1.txt` L26) — **DevBook's mandatory-Workflow design is legal without per-task keywords**.

Empirically verified (memory: `/home/leon/.claude/projects/-home-leon-projects-devbook/memory/workflow-tool-sync-throw-gotcha.md`): sync throw in a thunk crashes the run; only async rejection → `null`; pipeline streams with `(prevResult, originalItem, index)`; `agent({schema})` returns a validated object; `budget.total` null when no target.

## 2. Verdict: can a plugin ship a named workflow?

**Yes — confirmed in loader code, but undocumented and partly buggy in the field.**
- For: binary loader reads plugin `workflowsPath`/`workflowsPaths`, registers `<plugin>:<name>`, invocable via `Workflow({name, args})` and nested `workflow('plugin:name', args)` (`/tmp/wf1.txt`: `Loaded ${n} workflows from plugin ${name}…`). The bundled `/deep-research` plugin workflow resolves by name in practice (issue #63876).
- Against: plugins-reference lists no workflows component; #63876 (https://github.com/anthropics/claude-code/issues/63876) reports user `.mjs` not resolving by name unless `/workflows`-saved, and `Workflow({scriptPath, args})` **drops args**; bcherny on HN says first-class sharing docs are "coming soon" (https://news.ycombinator.com/item?id=48311705).
- Community fallback idiom: skill-packaged templates Claude instantiates per task (https://github.com/ray-amjad/claude-code-workflow-creator; https://claudefa.st/blog/guide/development/dynamic-workflows).

**Recommendation: hybrid, weighted toward bundled.** Ship the canonical parameterized scripts in the plugin's workflows directory (primary path, code-confirmed); keep a thin authoring-reference section in the skill as fallback so a session can re-author or patch if name-resolution fails on the user's version (#63876 shows the resolution path is young). Verify name+args dispatch at install time (see §5). Do not build the pure reference-doc model — the existence proof for bundled delivery is in the binary.

## 3. Harness authoring rules

**Stage-by-stage** (spec citations in `/tmp/wf1.txt`–`/tmp/wf4.txt`):

| Stage | Primitive | Pattern | Why |
|---|---|---|---|
| 0 done-check | Inline scouting or one `agent({schema})` | Optional single refuter ("machine-judgeable? gameable?") | Spec's hybrid rule: scout inline before orchestrating (`wf1` L29) |
| 1 design/RCA | One `agent({schema})`; knob `args.designAttempts>1` → judge panel | Judge panel is the spec's named escalation for wide solution spaces (`wf3` L50) | Stage 2 supplies the adversarial pressure anyway |
| 2 refutation | `parallel()` — barrier genuinely correct | N skeptics with **diverse lenses** (correctness/security/perf/feasibility), "default refuted=true if uncertain", majority kill | Verdict needs ALL results = spec's barrier test (`wf2` L23–26). **Human gate fires in the main loop AFTER the workflow returns** — no elicitation primitive exists |
| 3 slices | **Plain `for…of` of awaits — NOT `pipeline()`**; per slice: one writer `agent()` → `parallel()` reviewer panel → loop-until-dry fixes | Loop-until-dry = K consecutive clean rounds, not fixed fix count (`wf3` L51); `opts.phase: \`Slice ${i+1}\`` | Pipeline contract is *independent* items and starts all items concurrently — dependent slices would mutate the repo in parallel. No worktree isolation needed: one writer at a time |
| 4 close | `parallel()` of judges + a distinct completeness critic | Schema-required evidence fields (command, exit code, output excerpt); critic findings loop back to stage 3; `log()` any skipped checks (`wf4` L3–4) | Subagents have full tools, so evidence is real, not prose-trusted |

**Spine:** stages as separate chained plugin workflows (`devbook:design-and-refute` → gate → `devbook:implement-slices` → `devbook:close`), main session reads each result and gates between — literally the spec's recommended macro-pattern (`wf1` L36) and the only home for the human gate.

**DO:** `meta` as pure literal, phase titles matching `phase()` calls; `schema` on every programmatic result; `.filter(Boolean)` every parallel/pipeline result **and count expected vs received — fail closed if a judge vanished** (the tool degrades to null; "all green" must treat null as red); real JSON in `args`, never stringified; `opts.phase` inside concurrent stages; guard budget loops with `budget.total && budget.remaining() > X`; keep early prompts stable for resume-prefix caching; pass timestamps via `args` (Date/random throw — also alexop.dev: https://alexop.dev/posts/claude-code-workflows-deterministic-orchestration/); make risky code async-reject, never sync-throw; omit `opts.model` by default; reuse custom agents via `opts.agentType`.

**DON'T:** default to `parallel()` (barrier only for cross-item context / zero-count early-exit); use `pipeline()` for dependent slices (a null stage also short-circuits that item: `if (prev === null) break`); fixed counts for discovery loops (dedup vs `seen`, not `confirmed`); worktree isolation without parallel mutators; nest `workflow()` >1 level; TypeScript, fs/Node APIs, computed `meta`; expect mid-script human answers; >4096 items per call.

**Where the skeleton fights the grain + fix:**
1. Sequential slices vs pipeline → for-loop (above). 2. Stage-2 human gate vs non-interactive runs → chain per-stage workflows; monolith alternative: return `{gate:'human'}` early, relaunch with `resumeFromRunId` (cached prefix ≈ 0 tokens to the gate). 3. "All green" vs drop-to-null tolerance → explicit null-as-red counting. 4. Budget → never require "+Nk"; scale panels `budget.total ? f(remaining) : defaultN` with hard iteration caps.

## 4. Community experience

Sparse — feature is ~2 weeks public (v2.1.154+, blog May 28, 2026). One docs page, one 200-pt HN thread, 3–4 real writeups, one dedicated repo; GitHub search for `.claude/workflows` returns mostly pre-feature noise; several SEO restatements excluded.

**Borrow:** workflow-creator's per-shape `patterns.md` + `implement-and-review.js` (schema'd reviewer `{passed, issues[]}`, hard `MAX_ROUNDS`, "the loop lives in JavaScript… physically cannot forget to re-review") and its pre-execution linter `scripts/validate-workflow.mjs` (https://github.com/ray-amjad/claude-code-workflow-creator). alexop.dev's "default to pipeline(), barrier only when a stage needs all prior results". HN user wrs's point — adversarial convergence only works with supplied ground truth — directly validates DevBook's stage-0 done-check. rally_ai's cost report (one small task ate ~20% of a session limit: https://note.com/rally_ai/n/nc0a366d425dc) argues for keeping the 建库 trigger strict.

**Known bugs to design around:** #63876 (named resolution + scriptPath args drop), #63762 (subagent `tools:` allowlist ignored — Write/Edit always granted), #66621 (runaway-token crash), #64664 (rate-limit context overflow), #63693/#66703 (subagent model config gaps), #65446 (sandbox exec), #64348 (requested-not-existing: `humanInput()`, `exec()`, `createAgent()`).

## 5. Build-time verification checklist

1. Plugin workflow dispatch: does `Workflow({name: 'devbook:<stage>', args})` deliver `args` intact on the current version? (#63876 says scriptPath dispatch drops args; named-plugin path untested publicly.)
2. Does project/user `.claude/workflows/` actually shadow a same-named plugin workflow as the loader code implies?
3. Cross-session resume: docs say fresh-on-restart; binary has `resumeFromRunId` journal cache — does it survive exiting Claude Code?
4. `workflow('devbook:x', args)` nesting from a parent script: real behavior of shared budget/agent counter/abort.
5. Stage-2 gate ergonomics: chained workflows vs `{gate:'human'}` + resume relaunch — measure actual cache-hit cost of the relaunch.
6. Null-as-red accounting under induced skip/stall/budget-drop: confirm `<failures>` metadata is parseable enough to fail closed.
7. `opts.agentType` with DevBook custom agents: schema composition, permission-rule denials, and whether #63762 (tools allowlist ignored) affects reviewer agents that must be read-only.
8. Per-phase `meta.phases[].model` and `opts.model` overrides on the user's plan/version (#63693/#66703 gaps).
9. Real token cost of stage-2/4 panels at default N on a MEDIUM task (rally_ai's 20%-of-session warning).
10. `opts.stallMs` override: exists in code, undocumented — confirm it's honored before relying on it for long evidence-collection agents.
11. Worktree-isolation behavior if ever enabled (background-session edit bug was fixed per changelog — verify on current version).
12. "+Nk" budget directive: confirm syntax and that `budget.total` populates inside plugin-named workflows.