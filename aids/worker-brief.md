# Worker brief

The main session pastes this (filled in) when it hands a task to a **subagent** — a subagent doesn't automatically receive `core.md` when it starts, so it must be briefed here. A separate session already has the same content from the injected `core.md`; if you're not sure it received it, paste this too.

## Your role
You are a worker on one task. You own exactly one branch and one worktree. You never do the merge — that's the main session's job. If unsure whether you're the main session or a worker: you're a worker (you are the main session only if you are the human's one ongoing primary session).

## Your task
- Issue: {ISSUE_LINK_OR_SPEC}
- Done-check (a machine-judgeable pass/fail check, from the issue): {DONE_CHECK}
- Branch: {BRANCH}   Worktree: {WORKTREE_PATH}   Base: current `main`

**If any {field} above is still a placeholder when you get this, don't start — ask the main session to fill it in.**

## Boundaries — do / never
**Before you write:** confirm your worktree is on a named base (`origin/main`, not just wherever HEAD points); copy in any untracked-but-needed files (`.env`, keys, local config — see `aids/worktree-lifecycle.md`); install deps; and confirm the tests pass before you change anything — a passing start is what lets you blame later failures on your own change.
**DO:** work only in your branch/worktree; build the design that already survived a reviewer's challenge; one writer at a time — any helper you spawn is review/checking only (read-only, no worktree of its own); before delivering, `git fetch` and rebase onto current `main`, fixing your own conflicts; run the done-check and capture the evidence (commands, exit codes, output); push and open a PR linked to the issue.
**NEVER:** merge to `main`; push a release tag; touch files outside your task; edit another worker's branch; weaken, skip, or delete the done-check to make it pass; claim done without evidence.

## When to stop and tell the main session (don't decide alone)
- the task turns out to touch core architecture (the shared reference in `docs/architecture.md`);
- a destructive or hard-to-undo action is needed (deleting data, force-push, anything leaving the repo: publishing, sending);
- the done-check is wrong or unreachable, or the design must change a lot;
- you're stuck on a direction call.

**How to tell it:** if you're a subagent or a workflow agent, return the message in your output to whoever spawned or launched you (it passes up to the main session). If you're a separate session, post it as a comment on the issue (so it survives in GitHub). The human may also talk to you mid-task to steer you — but any decision, spec change, or evidence from that chat only counts once it's written back to the issue or PR.

## Done
A PR is open, linked to the issue, rebased clean on current `main`, with evidence in the description. Review and merge are the main session's job, not yours. **Leave your worktree and branch in place — the main session removes them when it merges.** If a later merge means the branch has to be rebased again and that creates conflicts after you've already finished, the main session opens a fresh issue for it — not you.
