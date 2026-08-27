# The tree you hand back

Read this before the first task-generated write and again before delivery. The rule covers every doer:
a dispatched worker and a main session working its own short branch.

## Baseline before work

After every declared copy-in, but before install, tests, or anything else the task produces, record:

```sh
git status --porcelain -uall
```

Keep the snapshot in session scratch. Where there is an issue, publish it there immediately so it
survives the session; otherwise publish it in the eventual PR or handback. If the first act creates the
repository, record an empty-tree baseline and publish it on the setup issue once the repository exists.
A light start with neither issue nor remote has no durable venue, so the doer keeps and compares the
snapshot itself.

Account for every baseline entry against the repo's worktree copy-list. **Taking over without a
baseline:** treat every current non-copy-list path as unaccounted-for and name it rather than silently
inheriting it.

## Final delta and cleanup

After the final edit, rebase, and done-check run — and before every check-1 or re-review dispatch — run the
same `-uall` command and compare it with the baseline. Publish both snapshots. Every path new since the
baseline and visible to the command is committed or removed; naming a leftover does not license it.
Install and test artifacts are deliberately post-baseline: if they are not ignored, they are yours to
commit, ignore, or remove.

Delete only paths you created and know are disposable. Anything you did not create or cannot account
for is named, never deleted, and blocks a clean handback until its owner decides whether it is removed,
committed, or deliberately retained. Non-ignored copy-list inputs are removed at teardown only after
confirming the main checkout still holds them. The comparison is about which paths are present, not
their contents; ignored paths are outside `-uall` and outside this promise.

Progress that must survive a session is committed. A handoff or session-state document is not a
cleanup substitute: whether one can exist at all is governed by `reference/in-repo-writes.md`, and the
ordinary answer is to put that message on the issue or PR.
