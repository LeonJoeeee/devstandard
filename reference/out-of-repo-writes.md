# Where a write goes when it is not in the repo

`core.md` says stay in your own repo *and off the human's filesystem*. This is the *off the
filesystem* half: where an agent may write when the target is neither the repo's tracked tree nor a
worktree. It exists because nothing said, and so every agent defaulted to `$HOME` — which is how a
home directory fills with `~/data`, `~/services`, `~/tools`, `~/labs`, and a folder dropped on the
Desktop, none of it the human's doing.

**The line is conventional, not visible.** A tool's own documented cache — `~/.cache/huggingface`,
`~/.npm`, `~/.cargo` — is where that tool already puts things, and is fine. `~/data/x` and
`~/.mydata/x` are both an agent *inventing* a place on the human's machine; the leading dot changes
nothing. The complaint is invented clutter, not what `ls` shows. *Invented* means the agent chose the location itself; a path the human handed over, or that the repo's own docs declare, is not invented — the same line "Stay in your own repo" draws for another repository.

## Three kinds of write, one rule each

**1. Downloads, environments, tool clones** — model weights, a venv, a cloned tool: things that
outlive the task. In order:

- the tool's own documented cache, if it has one — and most do (`hf download` uses
  `~/.cache/huggingface` unless told otherwise; overriding that to hand-build `~/data/mage-vl` is
  the exact move that produced this rule);
- else the cache root the repo's `CLAUDE.md` declares (`reference/repo-claude-md.md`);
- else you are about to choose a location on the human's machine that nothing has chosen — **stop
  and tell the main session** (a worker) or **ask the human** (the main session). Never an invented
  entry under `$HOME`, hidden or not; never a path a design spec merely mentioned, because a spec is
  not where a clean-context worker looks.

**2. A deploy root or runtime state** — where a service the project runs keeps its files. The
location is the project's call, but it is **written in that repo's `CLAUDE.md` or architecture doc
before anything lands there**, and it is not an invented entry under `$HOME`. A declared root also
says what it retains — which copies are removed and when — because naming the place fixes where
things go, not how many pile up: a documented `~/services` still grew fourteen release directories
and a multi-gigabyte rehearsal leftover.

**3. Scratch, drops, and deliverables** — session-local, gone when the session is. Write to the
scratch the session gives you — the location your harness provides: on Claude Code,
`$CLAUDE_JOB_DIR/tmp` or the scratchpad it names; on a harness that names none (a standalone Codex
session), one dedicated `mktemp -d` directory per task, named in the PR when its contents matter and
removed best-effort at task completion (an abnormal exit leaves it to the OS's tmp cleanup). A
process-invoked external agent (`reference/external-agent.md`) has none of that — under a
write-scoped sandbox the dispatching session's `$CLAUDE_JOB_DIR` is present as a variable but denied
as a path, and only the worktree and `/tmp` are writable — so its scratch is a gitignored
subdirectory of its own worktree, which dies with the worktree (`reference/worktree-lifecycle.md`).
The human's Desktop and `$HOME` are never a drop target unless the human names one: showing them a
result is what the PR, the issue, and the conversation are for.

## Say where you wrote

Any write under kind 1 or 2 is named in the PR description — the path, which branch of the rule
applied, and why. **A committed write is reviewable; an ad hoc one is not.** If the write is in the diff — a script,
a Makefile, a CI step that fetches to a path — merge check 1 sees it and can flag an invented
location like any other line. A write done by a command typed in the session (which is what every
row of the incident that prompted this rule was) leaves no trace in any diff; check 1 sees the diff
and the report and nothing else, so nothing catches an undisclosed one.
This is a discipline the acting agent keeps, not a gate — the same shape `reference/adr.md`'s
attribution rule and ADR 0036 name for their own duties. The disclosure gives a human, or a later
audit, the one place to look; the reviewer asks for it when a task plainly needed a location (a
model, a dataset, a service) and the report names none.
