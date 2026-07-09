# 0012 — A worktree dies with its task

Status: Accepted (2026-07-02)

## Context

core.md mandated one task = one branch = one worktree = one session, but specified only the worktree's birth, never its death. The field's evidence says end-of-life is where methods bleed. superpowers has the most mature teardown *when it fires* — provenance-checked, merge-verified, correctly ordered — but it fires only when the agent voluntarily invokes a skill, its PR path explicitly says "Do NOT clean up worktree" with no post-merge reap ever, and abandoned sessions have no reclamation (46 worktree-labeled issues). Spec Kit has no teardown of anything: its branch numbering *scans old branches to avoid collisions*, structurally assuming branches are never deleted. Unmanaged worktrees also silently erode the one-task invariant — a stale worktree is an open invitation for a second writer — and `git worktree list` stops being an honest map of in-flight work.

## Decision

**A worktree dies with its task.**

- **Trigger:** the branch merged, or the human explicitly abandoned the work — never an assumption.
- **Inventory first:** check for uncommitted and unpushed work; anything found is surfaced to the human before deletion. Teardown never eats work silently.
- **Order, from the repo root:** remove worktree → delete branch (safe delete locally; remote too if the platform didn't) → `git worktree prune`.
- **Provenance:** never reap a worktree you didn't create.
- **Orphan sweep:** sessions sometimes die before their own teardown — that is the normal leak path, so whoever merges at main also sweeps (`git worktree list` + `git branch --merged main`) and reaps anything whose task is finished. Teardown gets two chances, not one.
- **Birth hygiene rides along:** explicit base ref (`origin/main`, never implicit HEAD), gitignored worktree directory, green test baseline verified before work starts, durable state committed to the branch — never git-ignored scratch.

Operational checklist: `aids/worktree-lifecycle.md`.

## Consequences

Worktree and branch accumulation is bounded — leaks are caught at the next merge instead of growing monotonically. A task's done state now includes its workspace being gone, keeping the worktree list an honest map of in-flight work. Cost: a few commands per task and one sweep per merge.
