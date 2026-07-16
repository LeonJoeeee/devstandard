# DevStandard v0.9.0 — Post-Release-Day Audit Report

> Research artifact behind v0.9.1 (issue #30). Produced 2026-07-16 by a 20-agent workflow: 7 audit lenses → triage (14 raw findings, 2 dropped) → adversarial verification (11 checked: 6 confirmed, 5 refuted) → synthesis. Overall verdict: the structure held through the nine-release day; six doc fixes, shipped in v0.9.1.

Scope: full doc set at main @ v0.9.0 after nine releases (v0.5.0 → v0.9.0) in one day. Seven lenses; 11 candidate findings adversarially verified against the actual files; 6 confirmed, 5 refuted, 2 dropped at triage.

---

## 1. TL;DR

**DevStandard came through its nine-release day in remarkably good shape.** The feared failure mode — files updated at different moments contradicting each other — did happen, but far less than the pace would predict: the ADR chain, version lockstep, CI checks, merge authority, model routing, and both language mirrors all cross-check clean. What survived verification is six findings, all of them small doc edits: **one Critical** (the injected core.md contradicts itself on whether the done-check runs before or after the rebase), **five Important** (an unowned pre-code-challenge gate in the design-spec default flow, plus four stale-claim/record-hygiene items), and **zero blocking Minors**. Nothing structural is broken; no fix requires a design change except one small ownership decision. Total repair effort is roughly one short fix-batch PR.

## 2. Per-lens health

| Lens | One-line verdict |
|---|---|
| **consistency** | Coherent after nine releases — ceilings, routing, merge authority, supersede chains all cross-check; the one drift that survived verification is the CHANGELOG tag-authority header. |
| **mirror** | High fidelity — core and README mirrors track line-for-line after ~10 paired edits; the single candidate divergence (纯指标优化) was refuted as a defensible rendering. |
| **walkthrough-setup** | Full setup and mini-setup walk cleanly end-to-end; both claimed tail problems (protection deadlock, light-start carve-out) were refuted by the docs' own fallback lanes and scoping. |
| **walkthrough-task** | Two real seams from the rapid spec/brief changes: the done-check/rebase ordering contradiction (Critical) and the design-spec ownership gap (Important); the bug-fix and small-change scenarios walk clean. |
| **history** | Strong — ADR chain 0000–0018 is clean and bidirectional, counts match sources, every version maps to a tag; one false credit ("submodule guard") slipped into the 0.9.0 entry. |
| **outward** | Accurate on every big bet (superpowers dependency, autonomous merges, token figure, overturn list); one real gap — 0017/0018 additions never propagated to either README. |
| **voice** | Plain-language and mirror discipline hold; one dogfooding self-contradiction — the "currently" hedge banned today survives in the project's own architecture doc and PRD. |

## 3. Confirmed findings and fix-batch plan

### Critical

**C1. core.md's at-a-glance flow orders the done-check before the rebase — opposite of its own DO list and the worker brief.**
- **Files:** `core.md` line 46 vs `core.md` line 67 and `aids/worker-brief.md` line 17.
- **What:** Line 46 sequences "run the done-check and capture evidence → rebase onto current main → push"; lines 67 and the brief mandate the reverse and explicitly rule that pre-rebase evidence "doesn't count." Two live rules inside the same injected file contradict; a worker following the summary ships evidence that doesn't describe the state check 1 and CI evaluate.
- **Fix:** Reorder line 46 to place the rebase before the done-check: "4. Worker: branch + worktree → build → update docs the change invalidates → rebase onto current main → run the done-check on the final state and capture evidence → push and open a PR linked to the issue."

### Important

**I1. Design-spec authorship and pre-code-challenge ownership contradict across three files.**
- **Files:** `howto/design-spec.md` line 32 vs `core.md` line 19 and `aids/worker-brief.md` lines 16–17.
- **What:** core.md and the brief encode a pre-existing, already-challenged spec at handoff (the worker drafts nothing); design-spec.md's default flow drafts the spec on the worker's branch. In that default path the pre-code challenge gate (core.md line 28) has no assigned owner and can be skipped entirely.
- **Fix (lowest-churn option):** Make design-spec.md line 32's default match the other two files — the main session drafts the spec and runs the pre-code challenge before handoff (spec reaches Status: accepted); the worker only carries the file into its branch and flips it to committed in the implementation PR. Drop "the spec is drafted on the task's branch" as the default. (Alternative: keep on-branch drafting as the default, but then add the draft + on-branch clean-reviewer-challenge step to worker-brief.md and soften the "already survived" language in core.md/brief. Either way, name the drafter and the challenge's owner in all three files.)

**I2. CHANGELOG standing header says the human applies release tags.**
- **File:** `CHANGELOG.md` line 3 vs `core.md` lines 55/79 (and CHANGELOG's own line 100).
- **What:** The live header — not dated history — states "Each release tag is applied by the human after merge," contradicting the settled human-decides/agent-runs split and the file's own 0.5.0 entry.
- **Fix:** Replace with "Each release tag is pushed by the agent once the human calls the release."

**I3. CHANGELOG 0.9.0 credits a "submodule guard" the released files removed before the tag.**
- **File:** `CHANGELOG.md` line 11 vs shipped `aids/worktree-lifecycle.md` line 7.
- **What:** Commit 5a37880 (dropping the empirically-refuted submodule rationale) is a verified ancestor of tag v0.9.0; the entry was false at the moment the tag was cut. Correctable per repo precedent (e6baf10 fixed the 0.7.0 counts as a check-1 Important).
- **Fix:** Drop "submodule guard" from the parenthetical, leaving "(git-dir vs git-common-dir)."

**I4. READMEs never picked up today's two doc-set additions (design specs, repo-root CLAUDE.md).**
- **Files:** `README.md` lines 14, 45, 55, 63, 80, 87 and `README.zh-CN.md` at the mirrored lines.
- **What:** The howto/ enumeration lists 4 of 5 templates (design-spec.md missing, per ADR 0017); the setup-output flows and the adoption checklist omit the repo-root CLAUDE.md that ADR 0018 made the sixth artifact. One root cause: 0017/0018 never propagated outward.
- **Fix:** In both READMEs: (1) add design-spec to both howto/ enumerations (phrase as a fifth template without forcing the "read at repo creation" timing — it's read at task time); (2) add the repo-root CLAUDE.md to both setup-output flows and the adoption checklist; (3) optionally widen line 14's project-memory promise to acknowledge operational memory. English canonical, mirror each edit faithfully.

**I5. Dogfooding violation: the project's own docs carry the "currently ~3,000" hedge banned today.**
- **Files:** `docs/architecture.md` line 40 and `docs/PRD.md` line 42 vs `howto/architecture.md` line 19.
- **What:** The v0.9.0 rule bans time-relative hedges in architecture docs ("currently" named explicitly); the project's own governed docs use it, and the figure will silently stale as core.md grows toward the 5,000 ceiling (already 3,083).
- **Fix:** Replace both with the stable fact — "kept as lean as the content earns, well under the ~5,000 ceiling" / "kept lean, well under the ~5,000 ceiling" — and let the live count live only in CLAUDE.md beside the CI formula.

### Fix-batch plan (lean — one PR, three commits)

- **Batch A — injected page & method files (gates acceptance test):** C1 (core.md line 46 reorder) + I1 (design-spec ownership, lowest-churn option unless the human prefers on-branch drafting). Mirror both core.md edits into core.zh-CN.md line-for-line.
- **Batch B — record hygiene:** I2 + I3 (two one-line CHANGELOG edits).
- **Batch C — outward docs:** I4 (both READMEs) + I5 (docs/architecture.md, docs/PRD.md).

All three batches are pure doc edits with no code surface; they can ride one short-lived branch through the normal two-check merge.

## 4. Refuted and dropped findings

| Finding | Disposition | Why |
|---|---|---|
| Setup tail deadlock: protection enabled before release.yml/CLAUDE.md land | Refuted | ci.yml + release.yml + CLAUDE.md ship in the same setup step (cicd.md:65, prd.md:26 "LAST setup step"); section order ≠ execution order; cicd.md:37's branch lane means no lockout even on a literal reading. |
| Check-1 "operational facts" Docs line vs merger CLAUDE.md write-back | Refuted | Alter/expose split is carried by the texts' verbs: diff ALTERS a documented fact → worker's same-diff duty (core.md:67); task EXPOSED a lesson → merger's teardown write-back. The conflicting scenario never arises. |
| worker-brief parity claim stale after 0.9.0 additions | Refuted | Two-tier design, not drift: the brief always carried more than core.md's compressed section; line 3's own safety valve says paste the brief when unsure; the one load-bearing gap is covered by superpowers:receiving-code-review auto-triggering. |
| Light start routes through cicd.md's unconditional protection | Refuted | cicd.md is self-scoped to full setup (line 3, post-skeleton); core.md:3 already exempts single-change work; and line 37's self-merge lane means no stuck state regardless. |
| zh mirror narrows "objective improvements" to 纯指标优化 | Refuted | The canonical's own gloss is metric-shaped ("speed, fewer warnings"); the spec gate is positive-trigger-driven, so the exemption wording can't cause a wrong spec. Defensible translation, not drift. |
| core.md setup enumerations omit repo-root CLAUDE.md | Dropped at triage | Summary-arrow enumeration; the agent necessarily reads cicd.md at the CI step where the requirement lives. Real 0018 gap is the README finding (I4). |
| "full setup" vs "full lifecycle" vs "full suite" naming drift | Dropped at triage | Pure register polish; misdirects no action. |

## 5. Final judgment: ready for the first real acceptance-test project?

**Yes — after Batch A, which is a same-day fix.** The method's structure held up under the hardest stress test it will plausibly face (nine releases in one day): the walkthroughs complete, the history is intact, the mirrors are faithful, and every claimed deadlock or lockout was refuted by lanes the docs already provide.

**What gates the acceptance test:** only the two Batch-A items, because both live on the path every task will walk on day one:
1. **C1** — the done-check/rebase ordering sits in the injected core.md's at-a-glance flow, the single most-read passage; left as-is, the very first worker may ship non-counting evidence.
2. **I1** — the first substantial task will hit the design-spec default flow immediately, and right now nobody owns drafting or the pre-code challenge in that path. This needs a one-line human call (pre-handoff drafting recommended as lowest-churn) before the method meets a real project.

**What does not gate:** I2–I5 are record and outward hygiene — they mislead readers, not acting agents — and can merge in the same PR or trail it without risk. No structural change, no new ADR beyond possibly a one-line amendment to 0017 recording the ownership clarification, and no re-audit is needed before launch.