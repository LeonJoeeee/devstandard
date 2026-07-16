# 0018 — A repo-root CLAUDE.md joins the doc set: operational memory for clean-context workers

Status: Accepted (2026-07-16)

## Context

The optimization sweep's one genuine blind spot (`_source/devstandard-optimization-sweep.md`, proposal 2): the method is structurally amnesiac. Clean context is the design — fresh workers, fresh reviewers — so written memory is the only memory. Yet the doc set held design (`docs/architecture.md`), decisions (`docs/adr/`), and tasks (GitHub issues), and had **no home for operational facts**: which command runs the tests, which port is taken, which untracked files a new worktree must copy (`aids/worktree-lifecycle.md` referenced a "declared allowlist" that nothing ever created). Every fresh worker re-derived them by trial and error, or failed review on something one line would have prevented — the same lesson re-bought forever. A repo-root `CLAUDE.md` is the field's most-converged practice, and Claude Code reads it **natively** at session start — the same mechanism as the personal `~/.claude/CLAUDE.md`, scoped to the repo. AGENTS.md was rejected earlier for double-injection risk; CLAUDE.md carries none — it is Claude Code's own channel, separate from this plugin's hook.

## Decision

- **Every full setup generates a repo-root `CLAUDE.md`** in the same step as CI, when the project's commands have just been settled (section + template in `howto/cicd.md`). One page hard max; three kinds of content, nothing else: commands (install / test / run), environment gotchas, and the untracked-files list a new worktree copies. The template's last line is its fence: architecture, decisions, and task state live in their own homes and are never duplicated here.
- **Merge-time write-back** (`aids/worktree-lifecycle.md`, Death): before tearing down a merged task's worktree, ask — did this task expose a command, gotcha, or rule that would have prevented a review finding or a worker dead-end? If yes, one line into `CLAUDE.md` through the small-change lane. A design decision goes through the architecture process instead — never a quiet note.
- An existing repo adopts by a normal small change whenever wanted; the human's light-start declaration is respected as everywhere else.

Rejected: keeping lessons in session memory (evaporates by design); a new log file (the sweep found no load-bearing precedent, and a log is append-heavy where this file must stay one curated page); AGENTS.md (double-injection — already rejected and the reason still holds).

## Consequences

Operational facts reach every session, worktree, and separate session automatically (it is a tracked file — a worktree checkout carries it, and Claude Code loads it without being asked). Lessons stop evaporating: the file grows one line at a time, each line bought by a real incident. Costs: about a page of context per session in that repo, capped by the fence and the one-page rule; one extra question at every teardown. The plugin's own repo carries the first instance.
