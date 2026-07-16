# DevStandard × superpowers 5.1.0 — Final Coupling Map

> Research artifact behind the 2026-07-16 amendment to ADR 0016. Produced by a 16-agent workflow (one assessor per skill + the non-skill layer, adversarial refutation reserved for new pointer proposals, synthesis); every load-bearing claim verified against the installed superpowers 5.1.0 files.

Synthesis note: every assessment arrived with `verdict: null` — no adversarial rejections were recorded. I therefore verified each proposal's load-bearing factual claims directly against the installed skills (`/home/leon/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/`) and DevStandard's current files. All checked out: writing-plans' REQUIRED SUB-SKILL header (SKILL.md L52), Execution Handoff menu (L134–151), test-first template (L39, L73), save path (L18); brainstorming's every-project hard gate (L13), writing-plans terminal state (L66), decompose-before-detail (L73–74); executing-plans' self-redirect to subagent-driven-development (L14); using-git-worktrees' consent question (L43) and announce line (L14); finishing-a-development-branch's local-merge option (L73); porting-plan §2 L45 earmarking brainstorming for both prd-how AND architecture-how; core.md at 2,160 words (~2,990 tokens). All surviving proposals stand on verified fact.

---

## 1. Coupling table (all 14 skills + non-skill layer)

| Feature | Decision | Flow step | Pointer location |
|---|---|---|---|
| brainstorming | **point** | pinning down requirements with the human; PRD + architecture-doc authoring | core.md L33 (canonical) + step-local redirect lines in howto/prd.md and **howto/architecture.md (new)** |
| systematic-debugging | **point** (keep as-is) | bug-shaped task, before any fix | core.md L33 + aids/worker-brief.md L20 (intentional mirror) |
| test-driven-development | **point** (keep as-is) | implementation guarded by tests | core.md L33 + aids/worker-brief.md L20 (intentional mirror) |
| writing-plans | **point** (relocate) | authoring the design-spec for a substantial change, before handing to a context-free worker | **howto/design-spec.md ONLY** — delete the clause from core.md L33 |
| dispatching-parallel-agents | never-point | — | — |
| executing-plans | never-point | — | — |
| finishing-a-development-branch | never-point | — | — |
| receiving-code-review | never-point | — | — |
| requesting-code-review | never-point | — | — |
| subagent-driven-development | never-point | — | — |
| using-git-worktrees | never-point | — | — |
| using-superpowers | never-point | — | — |
| verification-before-completion | never-point | — | — |
| writing-skills | **ignore** | no DevStandard flow step ever authors a SKILL.md | — (its craft serves DevStandard's own build process, unshipped) |
| non-skill layer (SessionStart hook; scripts/assets/.opencode/config/repo docs) | never-point (hook) / ignore (rest) | hook fires automatically — nothing to point at | — (no fence spend; see §4) |

Net changes: 1 new pointer site (architecture.md), 1 pointer relocation (writing-plans core.md → design-spec.md), 2 dedup trims (prd.md), 0 new core.md tokens, ~50 core.md tokens freed.

---

## 2. Final pointer wordings and locations

### 2.1 core.md — craft-skills paragraph (L33), final form
One edit: **delete the writing-plans clause.** Final paragraph:

> **Craft skills (from the superpowers plugin, installed alongside this one):** at the step where one helps, use it, then come back to this flow — the skill's own "next, use skill X" pointers don't apply here, and where a skill's rules conflict with this page, this page wins. Pinning down requirements with the human → `superpowers:brainstorming`. A bug task → `superpowers:systematic-debugging` (root cause before any fix). Implementation guarded by tests → `superpowers:test-driven-development`.

Why the deletion is right (this is the one place I go beyond "keep as-is"): the current clause anchors writing-plans to "writing an issue," while core.md L54 deliberately keeps issues low-on-how ("leave the *how* to the worker — over-specifying the method wastes its judgment"). writing-plans is complete-code-per-step — the opposite altitude. Its real step is the design-spec artifact, whose howto already points at it, making the core.md clause both miscalibrated and a double-pointer. Budget: frees ~50 tokens → core.md drops to roughly 2,940/3,000. Nothing else in this map needs core.md text, so the ceiling is safe with headroom restored.

Mirror the same deletion in **core.zh-CN.md**.

### 2.2 aids/worker-brief.md — L20, unchanged
> **Craft skills (from the superpowers plugin):** a bug task → `superpowers:systematic-debugging` (root cause before any fix); implementation guarded by tests → `superpowers:test-driven-development`. Use the skill for that step, then return to this brief — the skill's own "next, use skill X" pointers don't apply, and where it conflicts with this brief, this brief wins.

Both entries are intentional mirrors of core.md (subagent workers never see core.md). Correctly does NOT carry brainstorming or writing-plans — workers neither elicit requirements nor author specs.

### 2.3 howto/prd.md — trim + compress (dedup, see §6)
Line 3 final: "…One page. Write it WITH the human: their answers set direction." (delete "ask one question at a time, prefer concrete options over open-ended questions, and propose 2–3 alternatives with a recommendation when a real choice exists" — that is the skill's craft; the pointer carries the how.)

Line 5 final:
> The interview itself is the `superpowers:brainstorming` skill's craft — use it, then return here; the output lands in this PRD, not in superpowers' own spec files.

### 2.4 howto/architecture.md — NEW pointer (own paragraph after the intro, mirroring prd.md's placement)
> Settle the structure WITH the human, using the same interview discipline as the PRD: `superpowers:brainstorming`. Use it for the design dialogue, then return here — the design lands in this doc and its ADRs, not in superpowers' own spec files.

Grounding: porting-plan §2 L45 earmarks brainstorming's question discipline for both prd-how and architecture-how; architecture.md carries none of it today despite its template demanding a level-1 decomposition and quality-goal tradeoffs. I deliberately dropped the assessor's inline craft summary ("one question at a time, 2–3 approaches, decompose first") from the wording — restating skill craft inline is exactly what §6 deletes from prd.md; be consistent. Cost: zero core.md tokens (on-demand file).

### 2.5 howto/design-spec.md (in-flight) — sole home of the writing-plans pointer
> When a change is substantial enough to need this spec — a written plan a context-free worker will execute — draft it with `superpowers:writing-plans`: its rules (exact file paths, complete code in every step, no placeholders, map the files and their responsibilities before writing steps, then a self-review pass) are what keep a zero-context worker from getting stuck. Then return to this flow: don't announce the skill; the spec lands here in `docs/specs/`, not in superpowers' own plan folder; ignore its "REQUIRED SUB-SKILL" plan header and the execution-options menu at the end — DevStandard runs execution its own way. Where its mandatory test-first task template doesn't fit the task's done-check (a metric or refactor task isn't proven by a unit test), follow the done-check, not the template. On any conflict, this page wins.

This is the one pointer with a per-hazard fence (the test-first-template sentence), deliberately: it is the only hazard currently held by nothing but the generic sovereignty rule, and the file is on-demand so the sentence is free. The paragraph is longer than the core.md pointers because, unlike them, it cannot lean on core.md's umbrella preamble at the moment of use (a spec author may open this howto directly).

### 2.6 Not pointed anywhere, on purpose
- brainstorming at the design-spec step: design-spec already points at writing-plans; brainstorming's every-change ceremony is the wrong default for in-repo changes and would fight the task model.
- Any core.md sentence naming the SessionStart-injected using-superpowers block: unaffordable and unnecessary — the sovereignty rule generalizes, and the injected block's own SUBAGENT-STOP guard and instruction-priority ladder (user instructions > skills) concede precedence to DevStandard.

---

## 3. Never-point list (one-line reasons)

1. **dispatching-parallel-agents** — parallel dispatch is DevStandard's defining layer; the skill's multiple-writers-in-one-shared-workspace model directly violates "one writer per worktree."
2. **executing-plans** — self-deprecates on Claude Code (its own Note redirects to subagent-driven-development); its body duplicates DevStandard's worker protocol; it chains into three never-point skills.
3. **finishing-a-development-branch** — branch finishing belongs to DevStandard's merger; its 4-option menu (local merge, keep-worktree-on-PR) instructs a worker to do exactly what DevStandard forbids; the salvageable git ordering is already in aids/worktree-lifecycle.md with attribution.
4. **receiving-code-review** — merge check 1's fix-then-re-review-on-the-new-diff loop plus worker-brief's escalation already covers finding triage structurally; the residue is thin craft wrapped in human-chat ceremony (Circle K, no-gratitude rules).
5. **requesting-code-review** — the code-review pair is owned territory; aids/code-review-prompt.md is the retained, hardened fork; the skill's shell (cadence, Task dispatch, tests-green line) conflicts on every axis.
6. **subagent-driven-development** — the archetypal dispatch/router skill; "never dispatch implementers in parallel" and "don't pause for your human partner between tasks" contradict DevStandard's reason to exist and its human gates.
7. **using-git-worktrees** — worktree lifecycle is owned; its consent question vs. mandatory isolation and keep-on-PR vs. merger-deletes conflict directly; DevStandard's worktree-lifecycle.md is strictly richer (named base ref, copy-untracked, parallel-port parametrization).
8. **using-superpowers** — DevStandard IS the router; probabilistic "1% chance → MUST invoke" dispatch plus announce ceremony would re-route past DevStandard's deterministic step pointers.
9. **verification-before-completion** — its entire craft is DevStandard's evidence spine, enforced by structure (done-check, unverified-claims review, CI) rather than self-discipline; pointing would re-import fear-register framing and the universal tests-green bar.
10. **SessionStart hook (non-skill)** — fires automatically, so there is nothing to point at; mechanically safe (both hooks' additionalContext concatenate); its ceremony content is a soft collision held by the existing sovereignty rule.

(**writing-skills** is *ignore*, not never-point: not owned-and-fenced territory, simply a step DevStandard's flow never reaches. Its baseline-testing/loophole-closing craft applies to DevStandard's own document authoring — build-time only, never shipped.)

---

## 4. Hazards register (what upstream change breaks which pointer)

| Pointer | Upstream change to watch | Effect | Guard |
|---|---|---|---|
| all four | skill renamed/removed/split | dangling pointer | accepted cost per ADR 0016 — daily dogfooding catches; fix the name in core.md/worker-brief/howto |
| brainstorming | hard gate (SKILL.md L13) hardened further, or new terminal-state chains beyond writing-plans (L66) | more pull into design-ceremony and superpowers' pipeline | sovereignty + umbrella chain-cut; do NOT add per-hazard fences |
| brainstorming | spec save path changes (docs/superpowers/specs/) | none | prd.md/architecture.md redirect lines already override |
| systematic-debugging | currently has NO announce line and NO universal tests-green gate — upstream could add either; Phase 4's TDD link or the related-skills link to verification-before-completion (never-point) could become a hard REQUIRED | ceremony/chain leakage into bug tasks | umbrella chain-cut + sovereignty; re-check the "(root cause before any fix)" gloss still matches the Iron Law on upstream major versions |
| test-driven-development | currently chain-free and announce-free — upstream could add a next-skill chain; "ask your human partner" exceptions could grow | worker chats the human instead of returning BLOCKED | worker-brief sovereignty routes it to the stop-and-tell protocol |
| test-driven-development | testing-anti-patterns.md restructured | none | intra-skill reference, resolved inside the skill |
| writing-plans | REQUIRED SUB-SKILL header / Execution Handoff wording changes (L52, L134–151) | stronger pull into subagent-driven-development / executing-plans | design-spec.md's explicit ignore-the-header sentence |
| writing-plans | test-first 5-step template made more coercive | wrong proof shape for metric/refactor tasks | the done-check-shape sentence in design-spec.md — the one per-hazard fence in the map |
| non-skill hook | injected using-superpowers block's content grows (more ceremony, new hard gates before EnterPlanMode) | standing pressure beside core.md every session | sovereignty rule; re-audit at each superpowers major version |
| non-skill hook | session-start JSON-escaping/printf workaround (bash 5.3 heredoc hang) diverges from DevStandard's borrowed copy in hooks/session-start | hook breakage on bash updates | periodic sync glance, attribution comment marks the borrow |
| whole map | a future superpowers version ships commands/ or agents/ (5.1.0 has neither) | new surface no fence covers | run a fresh fencing review before upgrading the declared dependency |

---

## 5. Implementation checklist (DevStandard's own issue → PR flow)

1. **Open one GitHub issue**: "Superpowers coupling map: relocate writing-plans pointer, add architecture-doc brainstorming pointer, dedup PRD craft restatement." Done-check (machine-judgeable, all must hold): `grep -c 'writing-plans' core.md` = 0 AND `grep -c 'writing-plans' core.zh-CN.md` = 0; `grep -c 'writing-plans' howto/design-spec.md` ≥ 1; `grep -c 'one question at a time' howto/prd.md` = 0; `grep -c 'superpowers:brainstorming' howto/architecture.md` = 1; core.md token count < 3000 (measure, don't estimate).
2. **Sequencing dependency**: this issue depends on the in-flight design-spec change (howto/design-spec.md + docs/specs/) being merged first — deleting the core.md clause before design-spec.md exists on main would orphan the writing-plans pointer. Also verify the in-flight change gives core.md (or the mini-setup line) a reference to howto/design-spec.md; that reference is the discovery path after the move. If it doesn't, add it in this PR (it fits the freed ~50 tokens).
3. **Branch + worktree** per the flow; edits:
   - `core.md` L33 — delete the writing-plans clause (§2.1); mirror in `core.zh-CN.md`.
   - `howto/design-spec.md` — ensure it carries the full §2.5 wording (including the done-check-shape sentence and the ignore-the-header sentence).
   - `howto/architecture.md` — add the §2.4 paragraph after the intro.
   - `howto/prd.md` — trim L3, compress L5 (§2.3).
   - `aids/worker-brief.md` — no change.
   - `CHANGELOG.md` — entry.
4. Run the done-check, capture evidence, rebase onto main, PR linked to the issue.
5. Two merge checks (fresh clean reviewer per the blanket rule, then green CI); merger merges, closes, deletes worktree + branch.

---

## 6. Dedup plan

### (a) Delete + pointer (duplicated skill craft)
| Passage | Action | Why |
|---|---|---|
| howto/prd.md L3: "ask one question at a time, prefer concrete options over open-ended questions, and propose 2–3 alternatives with a recommendation…" | **DELETE**; L5's pointer carries the how | Restates brainstorming's question discipline inline while the next line defers to the skill; ADR 0016 explicitly rejected keeping copies as fallback, so the gist earns nothing |
| core.md L33 writing-plans clause | **DELETE**; pointer lives in design-spec.md | Wrong altitude (contradicts L54's low-on-how issue rule) + double-pointing with the in-flight howto |
| aids/testing-anti-patterns.md, aids/debugging-techniques.md | already deleted by ADR 0016 | confirm no resurrection; nothing further |

### (a) Keep — DevStandard's own protocol, not craft (with reasons)
- **aids/code-review-prompt.md** (whole file) — retained fork with DevStandard-only hardening (unverified-claims contract, CI-owns-pass/fail split, ADR 0011 verdict semantics); its source skill is never-pointed, so there is no pointer to replace it with. Attribution line already present.
- **aids/worktree-lifecycle.md** Birth/Death — own protocol, strictly richer than upstream (named base ref, copy-untracked files, parametrized ports; merger-deletes death protocol upstream lacks entirely); source skill never-pointed.
- **core.md L28/L71/L72** (evidence-carrying claims, unverified-claims review, CI as final word) — the method's spine; verification-before-completion is never-pointed precisely because structure replaced self-discipline.
- **core.md L21/L26/L27** (dispatch ladder, fresh-reviewer challenge, one-writer-per-worktree) — convergent with dispatching/subagent-driven skills but stricter and owned; those skills are never-pointed.
- **worker-brief.md L16** (named base, copy-untracked, passing-start baseline) — own worker protocol plus craft upstream lacks.
- **core.md L17 done-check / L56 branch rules / L78 teardown ordering** — own protocol throughout.

### (b) One-pointer-one-place audit
- **systematic-debugging**: core.md + worker-brief — **INTENTIONAL mirror** (subagent workers never receive core.md). Keep both.
- **test-driven-development**: core.md + worker-brief — **INTENTIONAL mirror**. Keep both.
- **brainstorming**: canonical pointer = core.md L33. The prd.md and architecture.md lines are step-local artifact redirects, not independent pointers — core.md cannot carry per-artifact output paths (the same skill lands in different artifacts at different steps), so the redirect must live in each howto. After the §2.3 trim they carry no craft restatement and only the compressed chain-cut ("then return here"). Not double-pointing; not a worker mirror (workers never brainstorm).
- **writing-plans**: current state (core.md + in-flight design-spec.md) **IS the one true double-pointing in the map** — resolved by the relocation; after the move it lives in exactly one place.
- **worker-brief** correctly omits brainstorming and writing-plans — workers neither elicit requirements nor author specs; adding them would be mirrors of pointers whose steps a worker never reaches.

---

Files referenced: /home/leon/projects/prod/devstandard/core.md, /home/leon/projects/prod/devstandard/core.zh-CN.md, /home/leon/projects/prod/devstandard/aids/worker-brief.md, /home/leon/projects/prod/devstandard/howto/prd.md, /home/leon/projects/prod/devstandard/howto/architecture.md, /home/leon/projects/prod/devstandard/howto/design-spec.md (in-flight), /home/leon/projects/prod/devstandard/docs/adr/0016-superpowers-becomes-a-dependency.md, /home/leon/projects/prod/devstandard/_source/superpowers-porting-plan.md (§2–3), /home/leon/.claude/plugins/cache/claude-plugins-official/superpowers/5.1.0/skills/.