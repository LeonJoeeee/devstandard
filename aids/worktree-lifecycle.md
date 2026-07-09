# Worktree lifecycle (birth and death)

One task = one branch = one worktree (core.md). This checklist covers both ends of that worktree's life. Adapted where noted from superpowers (MIT, Jesse Vincent) — with the holes its issue tracker exposed closed.

## Birth

1. **Prefer the harness's native worktree tool** (e.g. `EnterWorktree`) if one exists; fall back to `git worktree add`. Never fight the harness.
2. **Base ref is explicit, never implicit HEAD:**
   `git fetch origin && git worktree add <path> -b <branch> origin/main`.
   Branch name states the task (e.g. `task/<short-slug>`); consistent names make orphan-sweeping tractable.
3. The worktree directory must be gitignored (`git check-ignore -q <dir>`) or live outside the repo.
4. **Verify a green baseline before writing anything**: install deps, run the suite. A green start is what lets you attribute later failures to your own change. Red baseline → report and ask, don't build on it.

## Death — trigger: the PR merged, or the human explicitly said discard

1. **Confirm the trigger.** Merged: `gh pr view <n> --json state,mergedAt` or the branch appears in `git branch --merged main`. Abandoned: an explicit instruction — never an assumption.
2. **Inventory before deleting:** `git status --porcelain` (uncommitted?) and `git log @{u}.. --oneline` (unpushed?). Anything found → surface it to the human first; teardown never eats work silently.
3. From the **main repo root** (not inside the worktree): `git worktree remove <path>`. Worktree before branch — branch deletion fails while its worktree exists, and removal from inside the worktree fails.
4. `git branch -d <branch>` (safe delete; `-D` only on explicit discard). Delete the remote branch if the platform didn't: `git push origin --delete <branch>`.
5. `git worktree prune` — self-heals stale registrations.

**Provenance rule:** only reap worktrees this flow created for this task. A workspace the harness or a human created is theirs to clean.

**Orphan sweep:** sessions die before step 1 sometimes — that is the normal leak path. Whoever merges at main also runs `git worktree list` + `git branch --merged main` and reaps anything whose task is finished. Teardown has two chances to happen, not one.

**Mid-task session end:** progress state that must survive the session is committed to the branch — never left in git-ignored scratch, which dies with the worktree.
