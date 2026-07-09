# 0011 — Two ordered merge gates: clean-context diff review, then green CI

Status: Accepted (2026-07-02)

## Context

A source-grounded dissection of the two dominant published agent-dev methods found neither composes agent review with a deterministic CI gate. superpowers layers clean-context review over locally-run tests and then self-merges locally — the exact self-graded finish DevStandard forbids; a community PR adding a CI gate (obra/superpowers#1505) was closed unmerged. GitHub Spec Kit (~117k stars) prescribes neither review nor CI after implementation: tests are "OPTIONAL", the lifecycle ends at "report to user". Notably, superpowers' own doctrine argues the composition it never built: "tests passing" is explicitly *not sufficient* for "requirements met", and its task reviewer is told **not** to re-run the suite — review and deterministic checks are layers with different jobs.

Meanwhile DevStandard's own merge rule ("CI must be green") had two verified holes. First, no eyes on the diff at the merge boundary: design refutation happens *before* implementation, CI checks only what tests encode — so a non-architecture PR merged with zero review of the code itself, dropping the one safeguard human GitHub flow is built around. Second, green-on-branch ≠ green-after-merge: a branch tested against a stale base can merge a red main out of two individually green branches, and the failure rate grows with exactly the parallelism the method advertises.

## Decision

Per task, the merge is guarded by **two ordered gates**:

1. **Clean-context review of the branch diff.** The reviewer is a **fresh subagent spawned per merge** — it must not have written the code, and must not be the cockpit's own accumulated context (0015); a saturated reviewer is anchored, not clean. It gets the diff (base/head SHAs), the requirements/issue, and the implementer's report as unverified claims — never any session history. Critical/Important findings block: fix, then re-review. Minor findings are recorded, never block. The reviewer does not re-run the test suite — CI owns pass/fail; the reviewer owns what tests can't see (spec fit, test quality, design, check integrity).
2. **Green CI on the merge result against current main**, as a required check that binds admins ("require branches to be up to date"; a merge queue only for conflict-free fast-forwards).

**The reviewed diff is the merged diff.** Any rebase after gate 1 — conflict resolution, or a base that moved — re-triggers gate 1 on the new diff; a merge queue never auto-rebases past review. Otherwise conflict-resolution code reaches main unreviewed — exactly the two-green-branches case gate 2 was written to catch.

Layers, not substitutes: no agent verdict substitutes for CI; no green CI substitutes for review. Both gates and the merge are the cockpit's act as integration decision-maker (0015); a worker never merges. Rejected: agent review as the *final* gate (superpowers' model) — a probabilistic gate as the last word reintroduces the self-grading failure the field converged on eliminating; the deterministic gate says the last word.

## Consequences

core.md's collaboration standards carry the ordered chain; reviewer-context rules land in `aids/code-review-prompt.md`; `howto/cicd.md` hardens branch protection (up-to-date requirement, no admin bypass, free-plan-private caveat). Review scope shrinks (no suite re-runs), making reviews cheaper and non-overlapping with CI. Cost: one review round-trip per PR — paid from the parallelism budget the method already earmarks for verification.
