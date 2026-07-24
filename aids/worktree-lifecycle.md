# Worktree lifecycle (birth and death)

One task = one branch = one worktree (core.md). This checklist covers both ends of that worktree's life. Adapted where noted from superpowers (MIT, Jesse Vincent) — with the holes its issue tracker exposed closed.

## Birth

0. **Already isolated?** If the harness dropped you into a worktree (`EnterWorktree` or similar), creating another nests a phantom one the harness can't see or clean. Check: `git rev-parse --git-dir` vs `git rev-parse --git-common-dir` — different → you are already in a linked worktree: skip creation and go straight to step 4's setup; detached HEAD there → cut a branch before any PR. Equal → create one below (a plain submodule also shows equal dirs, and creating a worktree there is fine).
1. **Prefer the harness's native worktree tool** (e.g. `EnterWorktree`) if one exists; fall back to `git worktree add`. Never fight the harness.
2. **Base ref is explicit, never implicit HEAD:**
   `git fetch origin && git worktree add <path> -b <branch> origin/main`.
   Branch name states the task (e.g. `task/<short-slug>`); consistent names make orphan-sweeping tractable.
3. The worktree directory must be gitignored (`git check-ignore -q <dir>`) or live outside the repo.
4. **Copy in the untracked-but-needed files.** A fresh worktree carries only git-tracked files — `.env`, secrets, local config, and seeded data do NOT follow. Copy them from the main checkout per the allowlist in the repo's `CLAUDE.md` (its "new worktree" section — see `howto/cicd.md`; e.g. `.env`, `.env.local`); point at shared dependency caches instead of reinstalling from scratch where you can; and parameterize anything that would collide across parallel worktrees (ports, DB/schema names, docker-compose project names) off the branch name. Without this, the check below fails before you write a line — and that failure looks identical to a red main.
5. **Confirm the tests pass before writing anything**: install deps, run the suite. A passing start is what lets you blame later failures on your own change. Tests already failing → report and ask, don't build on it.

## Death — trigger: the PR merged, or the human explicitly said discard

1. **Confirm the trigger.** Merged: `gh pr view <n> --json state,mergedAt` or the branch appears in `git branch --merged main`. Abandoned: an explicit instruction — never an assumption.
2. **Write back the lesson.** Did this task expose a command, gotcha, or rule that would have prevented a review finding or a worker dead-end? If yes: one line into the repo's `CLAUDE.md`, through a short-branch PR like any other change. A design decision goes through the architecture process instead — never a quiet note.
3. **Inventory before deleting:** `git status --porcelain` (uncommitted?) and `git log @{u}.. --oneline` (unpushed?). Anything found → surface it to the human first; teardown never eats work silently. On the discard path a branch may never have been pushed — `git log @{u}..` then errors (no upstream) and reads as nothing-to-check right before an irreversible `-D`. Inventory base-relative instead: `git log main..<branch> --oneline`; show that commit list (with branch name and worktree path) to the human and get explicit go-ahead before `git branch -D`.
4. From the **main repo root** (not inside the worktree): `git worktree remove <path>`. Worktree before branch — branch deletion fails while its worktree exists, and removal from inside the worktree fails.
5. `git branch -d <branch>` (safe delete; `-D` only on explicit discard). Delete the remote branch if the platform didn't: `git push origin --delete <branch>`.
6. `git worktree prune` — self-heals stale registrations.

**Who removes it:** the agent that merges a PR removes that PR's worktree and branch, even though the worker created them. Don't remove a worktree for a task you are neither doing nor merging; a workspace the harness's own tooling or a human created is theirs to clean.

**Sweep for leftovers:** a session sometimes ends before it cleans up — that's the normal way worktrees leak. Whoever merges at main also runs `git worktree list` + `git branch --merged main` and removes anything whose task is finished. So cleanup gets two chances, not one.

**Mid-task session end:** any progress that must outlive the session is committed to the branch — never left in git-ignored scratch, which is deleted along with the worktree.
