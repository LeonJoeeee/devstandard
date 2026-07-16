# Quarrying the 10 never-pointed superpowers skills — final report

> Research artifact behind v0.9.0 (issue #28). Produced 2026-07-16 by a 23-agent workflow: 10 per-skill quarriers (each diffing the installed skill against DevStandard's current files) → triage merge (18 raw gems, 7 dropped) → adversarial refutation (11 checked: 1 refuted, 10 confirmed) → synthesis. Verdict: after this batch the never-pointed set is quarried out.

## 1. TL;DR

The 10 never-pointed skills still held **real but narrow** unabsorbed value. Of 18 candidate gems, 7 died at triage, 11 reached adversarial verification, 1 was refuted, and **10 survive**. The pattern is decisive: DevStandard has thoroughly absorbed the *dispatching* and *reviewing* sides of its method (6 of 10 skills are near-totally absorbed already), but the **receiving side of work — how a worker takes a handoff, self-checks, contests a wrong finding, and admits defeat — was almost bare**. 5 of the 10 surviving gems land on one file, `aids/worker-brief.md`. Two more fix concrete latent defects in `aids/worktree-lifecycle.md` (including one live bug: the discard-path inventory `git log @{u}..` errors out on never-pushed branches right before an irreversible `-D`). Only **one** gem earns `core.md` residency (~90 tokens + zh mirror); everything else lands on on-demand files at zero session-budget cost. After this batch, the never-pointed set is quarried out — nothing further worth taking.

## 2. Coverage per skill

| Skill | Already absorbed (where) | Newly proposed (surviving) | Anything left? |
|---|---|---|---|
| dispatching-parallel-agents | Context isolation (core.md L10, worker-brief L3); branch-prompt checklist realized as worker-brief itself; lazy-fix ban (core.md L30/67 + pointed systematic-debugging); fan-in verification (core.md L30/73/76) | Contributes the vague-task guard to the receipt-time gem (F) | No — fan-out guard refuted (already covered by L22-23 + L29), spot-check triage-dropped |
| executing-plans | Follow-steps/evidence (core.md L17/30, worker-brief L17-18); never-on-main (worktree-lifecycle Birth 2); stop-conditions (worker-brief L22-28); stale-plan escalation (L25/28) | Contributes receipt-time critical spec read to gem F | No |
| finishing-a-development-branch | Near-total: cleanup ordering, prune, provenance, inventory, merged-result CI, force-push ban — all in worktree-lifecycle.md + core.md | Gem H: base-relative discard inventory | No |
| receiving-code-review | Reviewer-side verify-first (code-review-prompt L7); fix→re-review loop (core.md L73, ADR 0011); design-disagreement path (core.md L82) | **Gem B: verify-then-refute for merge-check findings — the biggest single gem in the set** | No — receiving side now covered |
| requesting-code-review | Near-total: code-review-prompt.md is the attributed fork; all 8 payload elements carried over, plus DevStandard's own Docs-ride-the-diff addition | Nothing (2 triage drops) | No |
| subagent-driven-development | Report-as-unverified-claims (L7/73); model routing (core.md L33); over/under-build check; fresh reviewer; escalation triggers | Gems C (over-your-head + doubt disclosure), D (self-review diff), I (stuck-return = change something) | No — two-stage review and status enum are settled non-ports |
| using-git-worktrees | Near-total: attributed fork; Birth 1-5, plus DevStandard's own improvements (explicit base ref, collision parameterization) | Gem G: already-in-a-worktree detection (Birth step 0) — the one hole the fork dropped | No |
| using-superpowers | SKIP verdict holds; WHAT-not-HOW, priority rung, SUBAGENT-STOP all structurally present | Contributes current-baseline read to gem F | No |
| verification-before-completion | Most fully absorbed skill: Iron Law IS core.md L30/66/73 + code-review-prompt L7/32 + baseline discipline | Gem E: evidence from FINAL state | No |
| writing-skills | Structure-absorbed: budgets, altitude, states-what-is, loophole-closing, one-example, escape hatches | Gems J (proportional pinning → design-spec), K (no time-relative → architecture) | No — construction apparatus is settled skip |

## 3. Surviving absorption plan (10 gems, 4 batched issues, disjoint file sets)

### Issue 1 — worker-brief receiving discipline (files: `aids/worker-brief.md` + companion one-liner in `aids/code-review-prompt.md`)
Five gems share worker-brief.md, so they must ship as one issue (one writer per file). In document order:

**(F1) Vague-task guard — replace the line-13 placeholder guard with:**
> **If any {field} above is still a placeholder — or filled but too vague to act on cold (e.g. 'fix the race condition' with no repro, error text, failing-test name, or target file) — don't start; ask the main session to make it specific.** You get none of its session context; a vague task only makes you guess.

**(F2) Current-baseline + receipt-time vetting — append to "Before you write:" (line 16):**
> read the current docs/architecture.md and skim docs/adr/ — the shared baseline may have moved since the issue was written, so build against what's on main now, not the spec's snapshot or your memory; and vet the issue and its design spec at receipt — a spec that survived the challenge can still hide a gap a fresh reader catches, so if the done-check looks wrong or unreachable or the design won't start cleanly, raise it now (stop-list below), not after a full build.

**(E) Final-state evidence — rewrite the existing evidence clause in the DO line (line 17) as:**
> run the done-check on your FINAL state — after your last edit and the rebase — and capture that run's evidence (commands, exit codes, output); an earlier green run, from before a later change, does not count — re-run and re-capture.

**(D) Self-review the diff — insert in the DO list (line 17), just before "push and open a PR linked to the issue":**
> read your own diff end-to-end before you open the PR — hunt for what the done-check can't catch: a leftover debug print, dead code, a half-finished edge case, a requirement you dropped. Fixing it now costs minutes; letting merge check 1 catch it costs a whole review-fix-re-review round.

**(C1) Over-your-head trigger — add a bullet to "When to stop and tell the main session" (lines 22-26):**
> you're simply in over your head — reading file after file without getting closer, or you genuinely can't tell whether your approach is right.
Then one line closing the list:
> Escalating a task you can't do is never held against you — the real failure is guessing and shipping plausible-but-wrong work instead of saying so.

**(B1) Verify-then-refute — new section after "When to stop and tell the main session":**
> ## Handling merge-check findings
> When check 1 returns Critical/Important findings, verify each against the codebase before you implement it. The reviewer saw only the diff, the issue, and your report — not the wider codebase, platform/version constraints, or your reasoning — so a finding can be wrong for this project: it breaks working code, the current code exists for a compat reason, or it asks for a feature nothing uses (grep for the caller first). Verified correct → fix it, no commentary. Verified wrong → don't implement it; send the main session your technical reasoning with the evidence (the code, the constraint, the grep), so re-review resolves it. Fix blocking findings first, then re-run the done-check before handing back.

**(C2) Doubt disclosure — add to "Done" (line 31):**
> If you finished but still hold a doubt about correctness or scope that isn't a stop-trigger, write it plainly in the PR description so merge check 1 sees exactly what you weren't sure of — don't bury it.

**(B2) Companion edit — `aids/code-review-prompt.md` line 7, after "A rationale in the implementer's report never downgrades a finding's severity.":**
> That bars dodging a valid finding with narrative — not disagreeing with a wrong one: a finding the implementer has verified as incorrect (breaks working code, or misses a constraint the reviewer couldn't see) is contested with counter-evidence to the main session and settled by re-review, never by a note in the report.

Leave core.md line 68's four-trigger summary untouched — the aid is allowed to expand on the injected core.

### Issue 2 — worktree lifecycle holes (file: `aids/worktree-lifecycle.md`)

**(G) Insert as Birth step 0 (before current step 1):**
> 0. First, are you already isolated? If the harness dropped you into a worktree (EnterWorktree or similar), creating another nests a phantom one the harness can't see or clean. Check: `[ "$(git rev-parse --git-dir)" != "$(git rev-parse --git-common-dir)" ] && ! git rev-parse --show-superproject-working-tree 2>/dev/null | grep -q .` — true → you are already in a linked worktree (the second clause excludes a git submodule, where the dirs also differ): skip creation and go straight to setup (step 4). If that worktree is in detached HEAD, cut a branch before the PR. Only when the two dirs are equal do you create one below.

**(H) Append to Death step 3 (line 19) — fixes a live defect (`git log @{u}..` errors on never-pushed branches):**
> On the discard path, a branch may never have been pushed — `git log @{u}..` then errors (no upstream) and reads as nothing-to-check right before an irreversible `-D`. Inventory base-relative instead: `git log main..<branch> --oneline`; show that commit list (with branch name and worktree path) to the human and get explicit go-ahead before `git branch -D`.

### Issue 3 — howto refinements (files: `howto/design-spec.md` + `howto/architecture.md`, disjoint)

**(J) Insert after design-spec.md line 23 (the writing-plans borrowing paragraph):**
> **Pin detail in proportion to the cost of getting it wrong.** Spell out exact interfaces, commands, and step order where a mistake is expensive or the sequence is fragile — a migration, a shared contract, a destructive step; where several implementations would all be fine, give the direction and the boundary and leave the code to the worker (core.md: the code is the worker's call). That is how the no-placeholders rigor above applies here — to the fragile parts, not uniformly: over-specifying a low-risk part burns the pre-code challenge on minutiae and boxes out the worker; under-specifying a fragile sequence invites a data-losing reorder.

**(K) architecture.md line 19 — replace "The doc states *what is*, not history. History lives in ADRs and git." with:**
> **The doc states the stable present** — not history (which lives in ADRs and git), and not future promises or time-relative hedges ('currently', 'for now', 'temporarily', 'until the Q3 migration'). Such lines read as true but go stale with no signal, misleading the parallel workers building against this doc. A change that's coming is an ADR when it lands, not a promise written here.

### Issue 4 — the one core.md item (files: `core.md` + `core.zh-CN.md`; zh mirror REQUIRED)

**(I) Add to the "Rules at every level" block (core.md lines 27-31):**
> When a worker comes back stuck, change something before you re-dispatch — never resend the same brief to the same model: add the missing context, step up to a stronger model, cut the task smaller, or (if the plan itself is wrong) take it to the human. An unchanged re-run just buys the same failure — and, in a loop or workflow, the same wasted spend.

Cost: ~68 words / ~90 tokens English + the zh-CN mirror line. Against the stated 2,998-of-5,000 ceiling this fits comfortably; it is the only surviving item that pays permanent every-session residency, justified because the stuck-return decision belongs to the main session and no aid file is in that read path.

Issues 1-4 have fully disjoint file sets and can run as parallel branches.

## 4. Rejected on review

| Title (source) | Reason |
|---|---|
| Fan out only genuinely independent work (dispatching-parallel-agents) — **adversary-refuted** | core.md L22-23's "when there's an independent piece" already guards the fan-out decision; the three failure clauses map to L29, L35, and L17; the residual test doesn't earn ~85 words of every-session core.md residency plus zh mirror |
| Systematic-error spot-check across template fan-out | Speculative for DevStandard's shape — tasks are individually-specified issues, not one template fanned across merge-bound branches |
| Early checkpoint review on multi-step builds | Optional-tone advice, not a failure guard; the mandatory pre-code challenge already de-risks the foundation |
| Few-shot worked example in the reviewer prompt | code-review-prompt.md already carries calibration, severity definitions, per-issue shape, and a forced verdict; a worked example would double the aid |
| Sandbox-denial fallback: work in place | Conflicts with settled one-task=one-branch=one-worktree isolation; the real failure is already routed by stop-and-tell |
| Rationalization guard: pre-rebutted self-talk list | Conflict-register #5: self-policing exhortation deliberately replaced by deterministic gates (check 1 verifies tests weren't weakened) |
| Confidence-is-the-trigger verification line | Same #5 reasoning; its concrete tail risk is covered by the mechanical final-state evidence gem (E) |
| One term per concept across the doc set | Failure speculative — issue+spec+architecture read together disambiguates; writing-craft polish, not a failure guard |

## 5. Attribution notes

- **`aids/code-review-prompt.md`** — stays a near-verbatim fork; the existing line "Adapted from superpowers (`requesting-code-review/code-reviewer.md`, MIT, Jesse Vincent)" remains required. The new companion sentence (B2) is DevStandard's own text and changes nothing about the attribution.
- **`aids/worktree-lifecycle.md`** — the line-3 header "Adapted where noted from superpowers (MIT, Jesse Vincent)" remains required and already covers the two new additions: Birth step 0 carries the near-verbatim `git-dir` vs `git-common-dir` + submodule-guard technique from `using-git-worktrees`, and the base-relative inventory principle comes from `finishing-a-development-branch`. No new attribution line needed; the generic header suffices.
- **Everything else** (worker-brief additions, core.md line, both howto edits) — rewritten as DevStandard's own text carrying absorbed *ideas*, not copied prose; no attribution required.