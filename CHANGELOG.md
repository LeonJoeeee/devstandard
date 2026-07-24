# Changelog

All notable changes to DevStandard are recorded here. Versions follow the plugin's `plugin.json` / `marketplace.json` (kept in lockstep). Each release tag is pushed by the agent; since 0.9.3, releases follow every merge (per-release approval delegated by the human, 2026-07-24).

## 0.11.3

- **hooks/session-start: composable forced-read wording** (issue #56) — the SessionStart instruction no longer claims "MANDATORY FIRST ACTION"; it now reads "Read this file IN FULL before acting on the user's request or resuming prior work", plus an explicit composition-blind yield rule ("if a more specific method layer claims the very first action, read that first and this page immediately after"). Standalone semantics unchanged (nothing else claims first → identical behavior); under composition with another forced-read plugin (observed live: executor-kit, two colliding FIRST claims) exactly one FIRST remains. systemMessage gains the ✅ prefix for uniform hook listings.

## 0.11.2

- **howto/cicd.md: artifact hygiene** (PR #54, issue #53) — upload an artifact only when a later step or a person actually consumes it; always set `retention-days:` (default keeps every copy 90 days; a private repo's 500 MB quota fills in days of routine pushes, then uploads start failing); CI output is not an archive — the release pipeline owns keepable outputs, any build is reproducible from its commit. Evidence: a live incident the same day (an unconsumed per-push `dist` artifact accumulated 2.65 GB in six days and blew the account quota).

## 0.11.1

- **CI: `actions/checkout` v4 → v7 in both workflows** (PR #45) — the repo's first Dependabot PR, riding the exact path ADR 0021 prescribed: bot proposes, clean review under the gate-change rule (green CI can't vouch for a change to CI itself), then merge. v7's one breaking change targets `pull_request_target`/`workflow_run` triggers this repo doesn't use.

## 0.11.0

Ceremony is universal — the venue and ceremony axes are decoupled (the human's live-use observation: where work happens and whether it gets the ritual are two different questions; the docs had welded them into one size test).

- **Every change now merges through a branch + PR + fresh clean review + green CI** (PR #50, ADR 0022 amending 0015, issues #41/#46/#47): the small-change early exit is gone from the flow; the branch test now decides *weight* (issue + dispatched worker vs a main-session short branch), never whether ceremony happens; protection status only changes whether GitHub also enforces the gate. One carve-out: a red-main revert merges on a short branch + green CI without a fresh review — the tree it restores was already reviewed.
- **Issues: human-raised tasks get theirs opened FIRST** (clarify-then-create allowed, skipping not); a main-session self-noticed small fix goes straight to a PR — the PR is its record.
- **The doer's doc duty is universal**: whoever makes a change — any venue, any size — updates the docs it invalidates in the same diff; the reviewer's Docs check stays the backstop.
- **Docs aligned**: cicd.md protection paragraph, worktree write-back path, architecture doc §4, README FAQ honesty pass (small edits do ride the full gate — the agents run it, not you), ADR 0015 amendment block.
- Also: the three Minor findings from PR #44's review fixed (PR #49) — hook stdin capture hardened to `[A-Za-z]` so valid JSON is unconditional on stdin content; ADR 0019 accuracy corrections.

## 0.10.0

The delivery mechanism is replaced, and two more industry-alignment decisions land.

- **core.md now reaches sessions by a hook-forced first-action read, not full-text injection** (PR #44, ADR 0019, fixes #35): Claude Code silently caps inline hook output at ~10KB — every session since ~v0.4.2 had received only a 2KB preview of the method. The SessionStart hook now emits an ~836-byte mandatory instruction (read core.md in full before responding, before any other tool call; re-read after compaction — matcher `startup|clear|compact` unchanged) plus a visible systemMessage; the CI and release gates assert hook output stays under 4,000 bytes so the truncation regression can never ship again. Modeled on the maintainer's research-project playbook hooks.
- **Red main: revert-first is the default recovery** (PR #43, ADR 0020, core.md + zh): restoring green outranks all new work and nothing new is dispatched onto a red main; revert the offending commit — fix forward only when the fix is obvious and takes minutes; a red with no commit at fault (the pipeline aged) routes to the pipeline fix.
- **Pipeline pin upkeep** (PR #43, ADR 0021, howto/cicd.md): setup now also generates a 5-line Dependabot config (github-actions ecosystem, weekly) — the pipeline's own `uses:` pins rot on GitHub's clock, and its PRs ride the normal two checks; third-party (non-`actions/*`) actions pin to a full commit SHA (the 2025 tj-actions compromise; SHA-pinned repos were immune). The two rules are one decision: a SHA never updates itself, so the pin needs the bot. Self-applied: this repo now runs Dependabot; its own workflows use only first-party actions.

## 0.9.3

CI maintenance, aligned with industry practice (`_source/ci-maintenance-industry-alignment.md`: 5 source-grounded research lenses, 10 gaps mapped against the current text, 4 confirmed after adversarial refutation — and 10 industry practices verified as already covered by the method's structure). PR #36, issue #34.

- **howto/cicd.md — "generated once" was false**: the two robots age with GitHub, not with the project (runtime end-of-life and deprecated-action hard-fails hit on the vendor's dates, after months of warnings inside green runs). A new "When CI goes red with no change of yours" section teaches the read: suspect a vendor deprecation before your own code; bump flagged `uses:` pins when a task already touches the workflow file.
- **howto/cicd.md — least-privilege CI template**: top-level `permissions: contents: read`; a job that must write escalates per-job (the release template already modeled it). Without it, the template's token inherits the repo default — frequently read-write on solo repos, the tj-actions-style exposure.
- **aids/code-review-prompt.md — gate changes**: if the diff touches CI or branch-protection config, green CI cannot vouch for it — the review is the only check; flag gate-weakening steps and unpinned new third-party actions.
- **aids/worker-brief.md — the flake rule**: a done-check that fails then passes with no code change is a flake — quarantine it visibly (issue filed), never retry-to-green, never "fix" unbroken code; a tracked, reviewed quarantine is not the banned silent weakening.
- **Repo ops**: per-release approval is delegated — every merged change releases immediately (repo CLAUDE.md + this header updated; issue #37). Three settled-ruling collisions from the research stay open for the human: revert-first as the red-main default, Dependabot for the pipeline's own action pins, SHA-pinning third-party actions (report §5).

## 0.9.2

- **Check 1's verdict must land on the PR** (core.md + zh): the fresh reviewer's conclusion is recorded as a PR comment before the merge — the review history must be reconstructable from GitHub alone. Session practice on every PR since #10, now a stated rule; it closes the gap that GitHub machine-enforces only check 2 (CI) while check 1 lived purely in the method's discipline. (The review itself stays a local clean subagent: a single-account repo cannot use GitHub's Approve — self-approval is forbidden there.)

## 0.9.1

Fixes the six confirmed findings of the post-release-day whole-plugin audit (`_source/full-audit-v090.md`: 7 lenses, 11 findings adversarially verified, 6 confirmed / 5 refuted — overall verdict: the structure held through nine releases).

- **core.md (+ zh)**: the at-a-glance worker flow now rebases BEFORE running the done-check — final-state evidence, matching the DO list and the worker brief (it said the opposite: the one Critical).
- **Design-spec ownership unified** (human decision): the main session drafts the spec and runs the pre-code challenge before dispatch — the issue links an `accepted` spec; the worker carries the file in the implementation PR and flips it to `committed`. Previously three files implied two different owners and the default path left the challenge unowned.
- **CHANGELOG hygiene**: the standing header now matches the human-decides/agent-runs split (tag pushed by the agent once the human calls the release); the 0.9.0 entry no longer credits the "submodule guard" that was removed before the tag.
- **READMEs catch up with ADR 0017/0018**: design specs appear in both howto/ enumerations, and the repo-root CLAUDE.md appears in the setup outputs, the adoption answer, and the project-memory line.
- **Our own docs obey our own rule**: the "currently ~3,000" time-relative hedge (banned by v0.9.0's architecture-doc rule) is gone from docs/architecture.md and docs/PRD.md; the live count lives in the repo CLAUDE.md beside its measuring command.

## 0.9.0

The never-pointed superpowers skills are quarried out (`_source/superpowers-absorption-quarry.md`: 10 per-skill assessors, 18 raw gems, 10 survived adversarial verification; nothing further worth taking). The finding: dispatching and reviewing were absorbed long ago — the RECEIVING side of work was almost bare.

- **aids/worker-brief.md — receiving discipline**: the vague-task guard now stops filled-but-vague fields, not just placeholders; workers read the current architecture baseline and vet the issue/spec at receipt; done-check evidence must come from the FINAL state (post-edit, post-rebase — an earlier green run doesn't count); read your own diff end-to-end before the PR; a new "Handling merge-check findings" section (verify each finding against the codebase — fix what's right without commentary, contest what's wrong with evidence, re-review settles it); an over-your-head stop trigger plus "escalating is never held against you"; lingering doubts go in the PR description, never buried.
- **aids/code-review-prompt.md**: the no-rationale-downgrades rule now states what it bars — narrative dodges, not evidence-backed contests.
- **aids/worktree-lifecycle.md**: Birth step 0 — already-isolated detection (git-dir vs git-common-dir) so harness-created worktrees don't get phantom nests; the Death discard-path inventory is fixed — `git log @{u}..` errors on never-pushed branches right before an irreversible `-D` (a live defect); inventory base-relative (`git log main..<branch>`) and show the human the list first.
- **howto/design-spec.md**: pin detail in proportion to the cost of getting it wrong — the no-placeholders rigor applies to fragile sequences, not uniformly.
- **howto/architecture.md**: the doc states the stable present — time-relative hedges ("currently", "for now") banned alongside history.
- **core.md (+ zh)**: when a worker comes back stuck, change something before re-dispatch — context, stronger model, smaller task, or the human; never resend the same brief to the same model.

## 0.8.2

The every-session budget's hard ceiling moves 3,000 → 5,000 (human call 2026-07-16; second dated amendment on ADR 0007). core.md had reached 2,998 after the v0.5–v0.8 rule additions — each new line was fighting word-trims instead of clarity. Unchanged: kept-as-lean-as-the-content-earns; the ceiling is headroom, not a target, and every line still earns permanent residency. CI + release workflows, both READMEs, PRD, architecture doc, and the repo CLAUDE.md figures updated.

## 0.8.1

Doc maintenance moves to the doer (human call 2026-07-16: finishing a feature/fix naturally includes maintaining the docs — review is the backstop, not the mechanism). Previously the update-in-same-change rule lived only in setup-time howtos; the worker's own action list never mentioned docs.

- **core.md (+ zh)**: the worker's flow step and DO list gain "update docs the change invalidates — docs ride the same diff" (architecture/PRD changes still escalate first, unchanged); the small-change rule gains the protected-main pointer (short branch + green CI — howto/cicd.md), closing the follow-up recorded on #16.
- **aids/worker-brief.md**: DO gains the same rule; DONE now includes "no doc left stale by your change".
- **aids/code-review-prompt.md**: "What to check" gains a Docs line — the reviewer verifies docs rode the diff instead of being the only line of defense.
- Division of labor recorded: docs follow the diff (worker); lessons follow the teardown (merger's CLAUDE.md write-back, unchanged — avoids parallel workers colliding on CLAUDE.md and re-review churn).

## 0.8.0

The doc set gains its sixth artifact: a repo-root `CLAUDE.md` — operational memory for clean-context workers (ADR 0018; the optimization sweep's one true blind spot, parked in v0.7.0, decided by the human 2026-07-16).

- **howto/cicd.md** gains a "Repo CLAUDE.md" section: generated in the same setup step as CI, one page hard max — commands, environment gotchas, and the untracked-files list a new worktree copies. Claude Code reads it natively every session, so the facts reach every worker automatically; the template's last line fences it from architecture / decisions / task state.
- **aids/worktree-lifecycle.md**: Birth's "declared allowlist" finally has a home (the repo CLAUDE.md); Death gains the write-back step — one line per exposed command/gotcha/rule via the small-change lane; a design decision goes through the architecture process instead, never a quiet note.
- **DevStandard's own CLAUDE.md** added — the template's first instance (the four CI checks run locally, the zh-mirror rule, the worktree convention).
- docs/architecture.md §5 and docs/PRD.md updated. Not AGENTS.md: that was rejected for double-injection, and the reason still holds — CLAUDE.md is Claude Code's own channel.

## 0.7.0

Implements the surviving findings of a full-method optimization sweep (`_source/devstandard-optimization-sweep.md`: 6 finder angles, 22 raw findings, 12 after triage, 6 adversarially confirmed — 6 others refuted by the docs' own text). Shipped as three parallel issues (#15–#17) with disjoint file sets; every post-review rebase re-triggered check 1, with patch identity verified by range-diff. Human decisions 2026-07-16: routine merges are the main session's autonomous act; on a protected main, small changes ride a short-lived branch + green CI, self-merged; the sweep's repo-CLAUDE.md proposal (and its teardown write-back line) is parked pending the human's decision.

- **core.md (+ zh)**: the human-per-merge parenthetical is deleted — a routine PR with both checks green is merged by the main session on its own authority; the human's role stays where it was already written (the ask-axes, architecture approval before the merge, release go/no-go). The sovereignty clause now covers skills from any plugin, not just superpowers. Brief delivery names workflow agents — they never see core.md either. (#15)
- **howto/cicd.md**: the merge-queue advice no longer installs a standing check-1 bypass — GitHub's built-in queue never lands the exact reviewed commits; skip it, keep require-up-to-date, and re-run check 1 after any rebase. New paragraph: the protected-main small-change lane. (#16)
- **howto/design-spec.md + howto/prd.md**: the spec's status flips to `committed` inside the implementation PR — the status describes the state at merge, so a protected main never needs a post-merge edit. New "Setup mechanics" section: the repo is created after asking the human its name and visibility; setup commits land directly on main with branch protection arriving last (with CI); the architecture doc settled with the human IS the skeleton's design. (#17)

## 0.6.1

Implements the superpowers coupling survey (`_source/superpowers-coupling-map.md`: all 14 skills + the non-skill layer assessed; the four pointed-at skills confirmed, placement refined, duplication removed — 0016 amended).

- **writing-plans relocated**: deleted from core.md's craft paragraph (+ zh) — issue-writing stays low-on-how; its sole home is now `howto/design-spec.md`, with a fully fenced wording (ignore the REQUIRED SUB-SKILL header and execution menu; the test-first template yields to the task's done-check shape; no announce; specs land in `docs/specs/`). core.md drops to ~2,950 tokens — real headroom under the 3,000 ceiling restored.
- **New step-local redirect**: `howto/architecture.md` — settle structure with the human via `superpowers:brainstorming`; the design lands in the doc and its ADRs.
- **Dedup in `howto/prd.md`**: the inline restatement of the interview craft (one question at a time, 2–3 options…) is deleted — the pointer carries the how.
- Intentional non-changes, recorded by the survey: worker-brief's systematic-debugging + TDD mirrors stay (subagent workers never see core.md); the never-point list is confirmed unchanged; a hazards register now maps which upstream change would break which pointer.

## 0.6.0

The middle layer lands — the gap between the architecture doc and the code is filled, and the doc set gets a growth rule; grounded in `_source/doc-layering-research.md` (ADR 0017).

- **Design spec** (`howto/design-spec.md`): a substantial change (shared/public interface, a real feature whose design could go more than one way, expensive to undo) writes a 1–3-page spec before code — options + tradeoffs + decision, files/interfaces, out of scope, verification. Exempt, spelled out: meaning-preserving refactors, objective improvements, invisible changes. Lands as `docs/specs/YYYY-MM-DD-<title>.md` with a status header (draft/accepted/committed/abandoned), never deleted; it doubles as the worker handoff and is what the pre-code challenge reviews. The gate is change significance — never project size.
- **Split-on-zoom** (`howto/architecture.md`): the overview stays the single 1–3-page doc; a subsystem it can no longer explain is extracted alone into `docs/architecture/<subsystem>.md`, along domain seams; never by size, never to code level.
- **ADR admission test** (`howto/adr.md`): high cost of change only — "if every decision is architectural, no decision is architectural."
- **The clean-reviewer rule is now blanket** (core.md, worker brief): every gating review — the design challenge, merge check 1, a worker's helper — uses a freshly spawned reviewer with no session history (a context-inheriting fork doesn't count) that didn't write what it reviews. Previously stated only at two spots.
- ADR 0008 gets a dated amendment ("SDD optional" refined, not reversed); the research report lands in `_source/`.

## 0.5.0

DevStandard becomes the method layer wrapped around its two siblings — Claude Code (the mechanics) and superpowers (the per-step craft) — instead of a self-contained standalone (ADR 0016, superseding 0002's quarry-only stance).

- **superpowers is a declared dependency**, assumed installed alongside. The flow points at its skills by name at the step where the craft helps: pinning down requirements → `superpowers:brainstorming`; a bug task → `superpowers:systematic-debugging`; test-guarded implementation → `superpowers:test-driven-development`; specs for context-free workers → `superpowers:writing-plans` (names verified against installed v5.1.0).
- **Every pointer cuts the chain**: use the skill for that step, then return to this flow — superpowers' own "next, use skill X" pointers don't apply, and on any conflict DevStandard's page wins (rule now stated in core.md, the worker brief, and howto/prd.md).
- **Deleted the two copied technique aids** (`testing-anti-patterns.md`, `debugging-techniques.md`) — the live skills replace them, so upstream improvements flow in instead of drifting. `code-review-prompt.md` and `worktree-lifecycle.md` stay: they are DevStandard's own protocol, and their territory (merge check 1, worktree teardown) is deliberately never pointed at superpowers, whose rules there are the opposite.
- PRD / architecture doc / READMEs updated to the new stance; stale "~1,700 tokens" figures corrected to the measured ~2,900.

## 0.4.3

A fix pass after a fresh-context regression review of v0.4.2, plus a quick-reference pipeline.

- **Added "the flow, at a glance"** to core.md — a numbered, one-task-start-to-finish sequence an agent can follow step by step, sitting above the prose detail.
- **Tightened the "which changes need their own branch" test** — v0.4.2's conditions matched almost every task (every task has a done-check; "more than one file" is common), which accidentally overrode the "small changes are done in-session" default. Now: proving it done needs its own test/reproduction that could genuinely fail; it touches a shared/public interface or spans several files; it runs unattended or alongside another writer; or it isn't undone by a single `git checkout`.
- **Propagated the plain-language + ordering fixes into the living docs** the v0.4.2 pass had missed: `docs/architecture.md` (the shared baseline every agent reads), `docs/PRD.md`, and both READMEs — "cockpit" → "the main session", gates → "checks", ladder/rung → "level", "refuted" → "survives a challenge", and architecture approval now stated *before* the merge. Frozen ADRs stay as-is; ADR 0012's reversed worktree-provenance rule gets a dated amendment.
- **Restored two things dropped while de-jargoning:** the harness-created-workspace exemption in the worktree teardown, and "evidence" in the worker brief's write-back rule.
- **Escalation now covers all three worker types** (a workflow agent was unnamed) and routes a nested subagent's message up through its spawner.

## 0.4.2

A plain-language and disambiguation pass on the injected page and the worker brief — the flow is unchanged; the wording is now jargon-free and harder to misread. Prompted by a fresh-context jargon audit.

- **De-jargoned** core.md / core.zh-CN.md / aids/worker-brief.md: "cockpit" → "the main session"; and gates → "the two checks", rung/ladder → "level", plus fan-out, clean-context, "flown blind", reap/orphan-sweep, "load-bearing", "baked" all replaced with plain words.
- **Fixed wordings that could make an agent act wrongly:** "refuted / passed refutation" (literal sense was the opposite → "survived a challenge"); the architecture path "public merge → human approval" reordered so nothing lands on main before approval; the self-contradictory worktree-removal rule ("never remove one you didn't create" vs. the merger sweeps) resolved — the agent that merges removes that PR's worktree; and a concrete test for which changes need their own branch versus are done in-session.
- **Worktree provisioning:** on birth, copy untracked-but-needed files (`.env`, keys, local config) and parameterize collision-prone resources (ports, DB names) — a fresh worktree carries only git-tracked files (`aids/worktree-lifecycle.md`).
- **Escalation channel stated:** a subagent returns to the main session; a separate session posts an issue comment. Mid-task verbal steering is fine, but decisions count only once written back to the issue/PR.
- Model tiers stay relative (no model names named), per ADR 0008.

## 0.4.1

core.md refinements (the flow is unchanged; the page now says *why* it exists and sharpens who owns what):
- **Lead with the purpose** — the method exists to run several goals in parallel on a large project; that concurrency is the whole point, and a single serial change needs none of the machinery.
- **Sharpen the cockpit's dispatch role** — before sending a task it settles *what result* and *why*, and leaves the *how* (architecture, implementation) to the worker.
- **Clarify the one-writer rule** — it is per-worktree; only concurrent edits to the *same* code are banned, while different worktrees running in parallel is exactly the point.
- **The human never runs git** — all commits, pushes, branches, merges, and tags are the agents' to execute; the human owns the decisions (direction, and go/no-go on architecture and releases), not the keystrokes.

## 0.4.0

The agent-team collaboration redesign — DevStandard's parallel model is now modelled on a human GitHub team, running on durable GitHub-native artifacts (ADRs 0011–0015).

- **Issue → PR dispatch flow.** Work that earns a branch is filed as a GitHub issue carrying its done-check (replacing the ephemeral first prompt); the executor is the cheapest execution-ladder rung that holds the work; the worker returns a PR linked to the issue and never writes main. Trivial in-repo changes stay in-session (ADR 0015).
- **Dual merge gates.** Every merge is guarded by two ordered gates: a fresh clean-context review of the branch diff (a per-merge subagent that never wrote the code and carries no session history — Critical/Important findings block), then green CI on the merge result against current main. Neither substitutes for the other; the reviewed diff is the merged diff (ADR 0011).
- **Worktree lifecycle.** A worktree dies with its task: triggered only by a merge or an explicit human abandon, inventory-checked for uncommitted/unpushed work first, torn down in a fixed order, provenance-guarded, and orphan-swept by whoever merges at main (ADR 0012).
- **Human-declared lifecycle scope.** Ceremony now follows what the human declares instead of repo creation alone — full lifecycle by default (silence defaults to full), a light start when the human declares the work small, a mini-lifecycle for a big in-repo initiative. The trigger phrase becomes "start a new project" (ADR 0014, supersedes 0004).
- **ADR log survives parallel agents.** Dated, append-only amendments are now legal, and final ADR numbers are assigned at merge (branches draft as `DRAFT-`) so parallel branches stop colliding on numbers (ADR 0013).
- core.md's every-session budget is relaxed (hard ceiling ~3,000 tokens, kept lean) to carry the roles, contract, and boundaries inline for workers.

## 0.3.0

Went public; renamed the project to DevStandard (ADR 0010).
