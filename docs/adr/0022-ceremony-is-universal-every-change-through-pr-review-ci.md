# 0022 — Ceremony is universal: every change merges through PR + fresh review + CI

Status: Accepted (2026-07-24). Amends 0015 (the small-change ceremony exemption only; 0015's issues-dispatch / PRs-return / ladder-picks-executor core stands).

## Context

DevStandard entangled two independent questions under one size test. 0015 modelled the agent team on a human GitHub team — issues dispatch, PRs return, the execution ladder picks the executor — and, in its decision point 2, exempted small work from the whole apparatus: "a trivial in-repo change skips this — done in-session (the anti-ceremony floor, 0014)." 0014's floor ("ritual never exceeds what the task needs") supplied the justification, and 0011's two merge gates were scoped to the PRs that exemption let through — so a small change reached main with no branch, no PR, no fresh review, and on an unprotected repo as a direct commit. `howto/cicd.md` carried the same lane for a protected main: a short branch, green CI, "no issue, no fresh review."

In live use the human observed that the size test was answering two questions at once that are in fact independent axes:

- **venue** — where the work is done (main session inline / a subagent or workflow / a separate session), which size and specifiability rightly decide;
- **ceremony** — whether the change rides a branch + PR + fresh review + CI, which size was *also* deciding, so that review (check 1) existed only for branch-worthy changes.

Welding the two means the one safeguard the human GitHub flow is built around — eyes on the diff at the merge boundary (0011) — is precisely the safeguard a small change skips. The smallest changes, the ones most often made in a hurry, were the ones landing on main unreviewed.

## Decision

The two axes are decoupled. Venue is unchanged. **Ceremony is universal:** every change to the repo rides a branch + PR, gets check 1 (a fresh clean reviewer, verdict as a comment on the PR) and check 2 (green CI on the merged result against current main), and is merged by the main session. There is no size below which a change reaches main unreviewed. Whether main is a protected branch changes only whether GitHub *enforces* this gate or the agents' discipline does — never whether the ceremony happens.

- **Issues (axis 3) stay size-gated, not ceremony-gated.** An issue is the dispatch/tracking artifact: mandatory for work handed to a worker, and for any task the human raises — and (issue #47) a human-raised task's issue is opened *first*, before the work, as the main session's first move; clarifying the request may precede it, skipping it may not. A small fix the main session notices itself may skip the issue — the PR is its record — but never the ceremony.
- **The doer's doc duty is universal (issue #46).** Whoever makes a change — any venue, any size, a main-session small fix included — updates the docs it invalidates in the same diff; the reviewer's Docs check stays the backstop, not the first line.
- **Single carve-out: a red-main revert.** The revert-first recovery (0020) restores a tree that was already reviewed when it first merged; a fresh review would spend the very minutes the revert exists to save. A revert rides a short branch + green CI and merges *without* a fresh review — the only change class with that exemption. Green CI still gates it.

The "which changes need their own branch" test in core.md is repurposed rather than deleted: under universal ceremony every change already gets a branch, so the test now decides only *weight* — whether a change earns its own issue and a dispatched worker, or is a main-session short-branch job.

Rejected: requiring an issue for literally every change as well (the open question issue #41 raised) — a self-noticed one-line fix's PR is already a complete GitHub record, and forcing an issue in front of it buys tracking that nothing reads; the issue stays the dispatch/human-request artifact, not a universal pre-registration.

## Consequences

Every change now carries a review round-trip — a typo fix, a one-line `CLAUDE.md` write-back, a release-prep commit each cost a branch + PR + one clean-reviewer spawn + a CI wait. That cost is paid from the same verification budget the method already earmarks (0011's "one review round-trip per PR"), now with no floor under it. Teardown write-backs (0018) and small fixes become tiny PRs; `howto/cicd.md`'s protected-main lane and `aids/worktree-lifecycle.md`'s "small-change lane" wording are rewritten to the short-branch PR that every change now uses.

What it buys: no unreviewed diff ever reaches main; the GitHub record is complete (every change has a PR carrying a verdict comment, reconstructable from GitHub alone); and the last size-tier disappears from the task flow — the small-change lane was arguably the final remnant of the size-tiering the method otherwise bans.

This amends 0015's decision point 2 and its "trivial changes stay in-session" consequence only; 0015's core — the team mirrors a GitHub team, issues dispatch, PRs return, the ladder picks the executor — is untouched, as are 0011 (its two gates now simply apply to every merge), 0014 (its floor still governs project-lifecycle scope, not per-change ceremony), and 0020 (whose revert is the one carve-out named above). core.md, core.zh-CN.md, `howto/cicd.md`, `aids/worktree-lifecycle.md`, and `docs/architecture.md` §4 are updated to carry the rule; the core.md token ceiling holds with headroom.
