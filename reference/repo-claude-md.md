# The repo-root `CLAUDE.md`

CI settles the project's commands — capture them while they're fresh: generate a repo-root `CLAUDE.md` — when there is something to put in it (below) — one page hard max. Claude Code reads it natively at every session start in the repo, so it is the one place operational facts reach every clean-context worker automatically. Three kinds of content — plus one conditional fourth, and nothing else:

- **Commands** — install, test, run (the same ones CI just encoded);
- **Environment gotchas** — ports in use, services that must be up, local-vs-CI differences;
- **Untracked files a new worktree must copy** — the allowlist `reference/worktree-lifecycle.md` copies from (`.env`, keys, local config).

One conditional fourth item — the fence's only exception: a `## Record language` line, when the repo's durable record is not English (core.md's rule). It sits here because a clean-context worker must see it natively; the reasoning behind the choice goes in that repo's ADR log, not here. Its absence means English.

Generate it only when the project actually has some of that to say. A file that merely transcribes what CI already encodes, or that would stand empty under every heading with no record language to declare, is noise every later session pays to read — skip it, and let the first real command, gotcha, copy-list line or record-language declaration create it through the same write-back lane.

It grows one line at a time: whoever merges a task that exposed a command, gotcha, or rule writes it back (the worktree checklist's Death step) through a short-branch PR like any other change. The writer enforces the 30-line cap (roughly twice the filled-in template below) at write time: a write-back that would cross it also drops the line it most clearly supersedes, or otherwise the stalest gotcha — never a separate cleanup pass. Architecture, decisions, and task state never go here — the template's last line is the fence; the record-language line is its one exception.

```markdown
# <Project> — repo notes for agents

## Commands
- install: <command>
- test: <command>
- run: <command>

## Gotchas
- <port / service / local-vs-CI difference worth one line>

## New worktree: copy these untracked files
- <path>   (or: none — everything load-bearing is tracked)

Architecture: see docs/architecture.md — never duplicated here. Decisions: docs/adr/. Tasks: GitHub issues.
```
