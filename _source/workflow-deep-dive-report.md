# Claude Code Workflows: Can One Run Carry a Feature-Sized Task?

Research synthesis for DevBook, 2026-06-10. Sources: official docs (code.claude.com/docs/en/workflows), binary internals of v2.1.170 (`/home/leon/.local/share/claude/versions/2.1.170`, extracts at `/tmp/wf1.txt`–`/tmp/wf4.txt`, `/tmp/claude-strings.txt`), ~150 real run scripts on this machine, live transcript evidence, and community reports (~13 days post-launch; artifacts in `/home/leon/projects/devbook/.firecrawl/`).

---

## 1. What a Workflow actually is

A workflow is a **deterministic JavaScript program executed by the Claude Code runtime in a Node `vm` sandbox — not by a model**. The script's surface is exactly: `agent, parallel, pipeline, workflow, log, phase, budget, console, setTimeout, clearTimeout, args`. No filesystem, no `Date.now()`/`Math.random()` (they throw, to keep resume deterministic), no way to read user input.

**The orchestrator-context hypothesis is CONFIRMED, at three independent levels:**

1. **Implementation.** The binary creates the script context via `vm.createContext(...)` with `agent/parallel/pipeline` injected as host functions (`/tmp/wf1.txt`, `i24()`). There is no model loop in the run path. `agent()` results return as plain JS values into script variables, untruncated (only UI previews truncate at 400 chars).
2. **Docs, verbatim.** "The workflow runtime executes the script in an isolated environment, separate from your conversation. Intermediate results stay in script variables instead of landing in Claude's context." (workflows.md, "How a workflow runs"; mirror `/tmp/workflows-docs.md` L199.)
3. **Live measurement.** For run `wf_1a96a903` (4 agents, 155k subagent tokens, 6.1 min), the main session's transcript received exactly two items: a ~1.2 KB launch result and one 8,987-char completion notification (`/home/leon/.claude/projects/-home-leon-projects-devbook/ab22a4ff-….jsonl`, lines 517, 576). Zero progress events; the main model did unrelated work mid-run. The inline result is hard-capped at **8,000 chars** (overflow goes to a task output file).

So: every `agent()` spawns a fresh, clean-context subagent (running in `acceptEdits` mode, inheriting the session allowlist); results flow into JS variables; **a run's cost to the main session context is O(10 KB) flat, regardless of run size**. The classic "context fills up over a long task" limit does **not** apply to a single run. It relocates to each individual subagent's window — which changes how you slice work, not how much work one run can hold (§3).

---

## 2. The documented feature surface

**Official docs cover** (https://code.claude.com/docs/en/workflows):

- **Invocation**: `/deep-research <question>` (bundled), `/workflows` (manage runs), saved workflows as slash commands, the `ultracode` keyword, natural-language opt-in ("use a workflow"), `/effort ultracode` (per-session), and `-p`/Agent SDK non-interactive mode (where `ultracode` is silently ignored).
- **Saving & sharing**: `.claude/workflows/` (project) > `~/.claude/workflows/` (user) > bundled; project shadows user shadows built-in. Run scripts persist under `~/.claude/projects/<session>/workflows/scripts/`.
- **Args**: structured input via the `args` global; `undefined` if omitted.
- **Limits table**: min(16, cores−2) concurrent agents; 1,000 agents/run; 4,096 items/call; ~180 s stall watchdog; **no mid-run user input** ("For sign-off between stages, run each stage as its own workflow").
- **Resume**: same-session only ("If you exit Claude Code while a workflow is running, the next session starts the workflow fresh").
- **Permissions**: subagents always run `acceptEdits` and inherit the session tool allowlist regardless of session mode; docs advise pre-populating the allowlist before long runs.
- **Cost**: per-agent token view in `/workflows`; advice to test on a small slice; agents use the session model unless routed.

**Exists only in the binary/spec, not in docs** (all verified in v2.1.170 strings):

- The actual script API semantics: `agent({schema})` validation, `pipeline()` per-stage signature `(prevResult, originalItem, index)`, `parallel()` null-on-rejection, sync-throw-kills-run.
- Per-agent `opts.stallMs` (default `nKf=180000`, ≤5 retries, 45 s throttle backoff); `isolation:'worktree'` (real) and `isolation:'remote'` (stubbed: "not available in this build").
- A second bundled workflow, **`code-review`**, registered `{hidden:!0}` (strings lines 359761–359978) — used by `/code-review` at high+ effort.
- Resume mechanics: journal at `<sessionDir>/subagents/workflows/<runId>/journal.jsonl`; cache key = rolling sha256 chain over prompt + `{schema,model,isolation,agentType}` + previous key; strictly longest-unchanged-prefix (one miss disables all later lookups); null results never journaled; `Workflow({scriptPath, resumeFromRunId})` reuses the runId.
- Budget mechanics: only active if the user typed `+Nk`; shared across the whole turn; `agent()` throws `WorkflowBudgetExceededError`, parallel/pipeline slots degrade to `null`, "In-flight agents will complete; their results are preserved".
- Misc hard caps: 30 s sync-JS timeout, 512 KB script size, 1-level `workflow()` nesting (child shares counter/budget/abort), 1000-entry log cap, plugin workflow loader (`${plugin}:${name}`).

---

## 3. What bounds ONE run — ranked for a feature-sized task

**The orchestrator itself has no context ceiling.** What actually binds, in the order you'll hit it:

**#1 — Human decision gates (architectural; the only structural splitter).** There is no input primitive in the VM, no `humanInput()` (requested in GH #64348, doesn't exist). Docs: run each stage as its own workflow for sign-off. Community scripts confirm this is what people design around: `crowi/parallel-feature-train.js` gates out specs with `openDecisions` and returns early with the plan; `WorkTrackPro/worktrackaccounting-roadmap.js` deliberately stops before security-sensitive modules "for human sign-off". **Splits are forced by decisions, never by capacity.**

**#2 — Per-agent context.** The classic limit relocates: each writer/reviewer must fit its slice plus required repo reading in one subagent window. The script can hold unlimited slices; each slice must be agent-sized. One Reddit report of a deep-review agent that "hallucinated 80% of the response" is the failure mode when a slice is too big.

**#3 — Subscription/rate limits (the #1 *observed* killer in the wild).** From the launch thread (reddit.com/r/ClaudeAI/comments/1tq9ofy): a 7.2M-token, 22-agent run consumed 100% of a session + 20% of a weekly limit in under 10 minutes — "And it didn't even finish"; a 3h22m run was at phase 5/10 at ~45% of a Max-5x session; HN reports of ultracode eating "10% of my weekly allowance in 30 minutes" (item 48467030). On plan limits, agents die to `null` after retries (GH #64664). No workflow ceiling was hit in any report — the wall is the *plan*, not the feature.

**#4 — Process lifetime + failure blast radius, with unreliable recovery.** No wall-clock cap exists in the binary (verified: no run-level timeout constant). But the run dies with the Claude Code process, and a **sync throw in any thunk kills the whole run** (verified empirically: probe `wf_9aeb618e`, error + stack verbatim in run metadata). Recovery is journaled and cheap *in theory* — completed agents replay from cache at ~zero tokens — but two open bugs undermine it in practice: **#65796** (auto-compaction changes the session ID → journal unreachable → resume *silently restarts from phase 1*; workaround: copy `journal.jsonl` into the new session dir) and **#63102** (LLM dispatchers can't reproduce args byte-exactly → 0% cache hit). Also: editing any early prompt invalidates everything after it (prefix-chain cache). Net: multi-hour runs are fine; multi-day or laptop-lid-risk runs should be split or made re-entrant via on-disk state.

**#5 — Budget ceiling.** Only if a `+Nk` target was set; then a hard turn-shared stop with null-slot degradation. Community uses it proactively (32 of 600 wild scripts check `budget.remaining()`); no reports of surprise hard-stops.

**#6 — Numeric caps: unreachable for a feature.** 1,000 agents/run, 4,096 items/call, 16 concurrent, 512 KB script. Real feature-sized runs observed on this machine: **5–25 agents, 10–82 min, 0.3–2.06M output tokens, all completed** (snapshot metadata under `~/.claude/projects/*/workflows/wf_*.json`; biggest: `post-ingest-converge-loop`, 24 agents / 68 min / 2.06M tokens). Bundled deep-research designs for ~100 agents. Nothing approaches the caps.

---

## 4. VERDICT: can a big task run natively in one workflow?

**Yes — one run natively carries a feature- or module-sized task, provided the design is settled before launch.** This is proven, not theoretical: on this machine, an entire subsystem rebuild (`mineru-extract-L1-core`: 5 sequential agents, S2 building on S1's edits in the same tree, 47 min, 753k tokens), a gateway implement-review-selftest (`gateway-implement-and-selftest`, 13 min), and two fix-until-clean loops (82 min / 1.73M tokens; 68 min / 2.06M tokens) each completed in **one run**. The orchestrator held ~2M tokens of agent work with zero context accumulation anywhere.

**What forces a split — exactly three things, none of them capacity:**

1. **A pending human decision.** No input primitive exists. If the run would need direction mid-way, that's a run boundary by construction.
2. **Plan usage-limit walls.** If estimated spend exceeds your session/weekly window, the run dies mid-flight on rate limits (the most common community failure). Split at module boundaries or use `budget.remaining()` reserve checks to stop gracefully.
3. **Multi-day duration.** No wall-clock cap, but the run is tied to the CC process and native resume is fragile across compaction/session changes (#65796, #63102). Even Anthropic's flagship Bun port was a *pipeline of chained workflows across 11 days* (per-file port workflow, fix-loop workflow, nightly cleanup workflows), not one run.

**Decision rule for DevBook:**

> **One workflow run = one decision-free segment of work whose estimated token spend fits comfortably inside your current usage window.** Split at human gates and at agent-context-sized slices; **never pre-split for orchestrator capacity.** A whole approved design's implement → review → fix-until-clean loop over all its slices is one run. Anything needing sign-off, or spanning days, is N runs chained by on-disk state.

Corollaries: lock the spec *before* the run and paste it into every agent (every successful big run does this); keep the workflow return value small (only ≤8 KB lands inline anyway — return a verdict + file paths, let agents write artifacts to disk); the re-entry into a follow-up run is cheap because the design is on disk, not in anyone's context.

---

## 5. Patterns worth adopting

From the bundled workflows (deep-research: binary strings 359984–360265, full text at `/home/leon/.claude/projects/-home-leon-projects-devbook/ab22a4ff-…/tool-results/b97du3wfn.txt`; code-review: 359761–359978), local production runs, and the wild corpus (600 GitHub hits for `path:.claude/workflows "export const meta"`):

1. **Locked SPEC constant pasted into every agent** — the run executes a settled design; it never decides direction (`gateway-implement-and-selftest` l.16–31).
2. **Sole-writer rule** — exactly one implementer mutates the tree at a time ("you are the SOLE implementer — no parallel edits", l.69); parallelism is spent on readers/reviewers/testers. Sequential writers safely chain in the shared working tree (verified: default `agent()` cwd = session dir, nothing resets between calls), passing forward plain-text summaries (`${s1}`). Worktrees (`isolation:'worktree'`) only for *parallel* mutators.
3. **Loop-until-clean with structured audits** — `while (round < MAX_ROUNDS)`: fixer → test-runner-who-fixes-nothing → adversarial auditor; the auditor's schema'd `remaining_issues` (file:line + evidence + fix) becomes the next round's work-list; `break` on `audit.clean && test.failed === 0`; hard round cap (`search-fix-loop` l.100–128). 54 of 600 wild scripts use a `MAX_ROUNDS` loop — this is the community-native shape of "keep going until done."
4. **Schemas everywhere** — `additionalProperties:false`, enums, integer counts, so loop control is mechanical, not parsed prose (both bundled workflows; all serious local runs).
5. **Salvage fallbacks, never crash** — guard-clause early returns with informative partials at every stage boundary; null synthesizer → "salvage the verified claims raw rather than throwing" (deep-research l.259–269); `.filter(Boolean)` after every parallel barrier. Remember the verified gotcha: any sync throw kills the run.
6. **No silent caps** — track `dupes`/`budgetDropped`/`verifySlots` in plain JS counters and report them in the final stats block (both bundled scripts).
7. **Re-entrancy via on-disk state, not native resume** — start with a manifest-probe agent that lists what already exists so re-runs skip finished shards (`vblanco20-1/stb_image_jai` `10-port-sections`); accept `args` like `"D1"` or `shard/nshards` to restart from a point (`WorkTrackPro`, `Microck/phase-e`). This is the community's answer to the broken resume story.
8. **Budget-reserve gating** — check `budget.remaining() < reserve` *before* each module and stop with a reason instead of dying mid-module (`WorkTrackPro`).
9. **Gate-and-return-early** — when a planning stage surfaces open decisions, return the plan as the run's result and let the human relaunch (`crowi/parallel-feature-train`).
10. **Compose via nested `workflow()`** (one level deep, shared budget) for module sequences inside one run; 24 wild scripts do this.
11. **Resume-aware prompt ordering** — the cache is a prefix chain, so put volatile/likely-to-edit prompts *late* in the script.
12. **Externalize contended resources** — 16 agents each running `cargo check` caused contention; the fix was a single external daemon writing a log the agents read (`phase-e-proper-port`).

---

## 6. What remains unknown

- **Cross-session `--resume` cache hits**: path arithmetic and persisted journals make it very likely that `claude --resume` + `resumeFromRunId` replays the cache, but it was not two-session-probed from inside this research. A 10-minute experiment would settle it (and whether the #65796 journal-copy workaround is reliable).
- **`isolation:'remote'`** is stubbed ("not available in this build") — unknown when/whether cloud-isolated agents land, which would change the process-lifetime bound entirely.
- **Budget target surface**: only the `+Nk` user-typed form is confirmed; whether a script or settings key can set a ceiling is unknown.
- **True multi-hour ceiling**: longest verified completed run is 82 min / 1.73M tokens locally and ~3h22m (unfinished at posting) in the community. Nobody has published a verified 8-hour single run; whether throttle-retry behavior holds up over that horizon is untested.
- **Quality at high fan-out**: the Bun port's output drew serious soundness criticism (github.com/oven-sh/bun/issues/30719 — "13,255 lines containing 'unsafe'"); how much review density a feature-sized run needs to stay trustworthy is a build-time question, not a research one.
- **The feature is 13 days old.** Every constant cited here (1000 agents, 180 s watchdog, 8 KB inline cap, prefix-chain cache) is from binary v2.1.170 and could change in any release; re-verify the load-bearing ones before DevBook hard-codes around them.

The single experiment that would close the biggest remaining gap for DevBook: run one deliberately long (3–4 h) decision-free implement loop with a `+Nk` budget and a mid-run process kill, then measure resume fidelity same-session vs `--resume` vs fresh session. Everything else above is evidence-backed today.