# Where a write goes when it is not in the repo

`reference/where-it-goes.md` is the entry point. This page applies only after that placement rule has
established that a destination must be outside the project, and gives the three expensive kinds their
specific requirements. It exists because nothing said, and so every agent defaulted to `$HOME` — which is how a
home directory fills with `~/data`, `~/services`, `~/tools`, `~/labs`, and a folder dropped on the
Desktop, none of it the human's doing.

For adding documentation *inside* the repository, use `reference/in-repo-writes.md`. For what may
remain in the working tree at handback, use `reference/clean-handback.md`.

**The line is conventional, not visible.** A tool's own documented cache — `~/.cache/huggingface`,
`~/.npm`, `~/.cargo` — is where that tool already puts things, and is fine. `~/data/x` and
`~/.mydata/x` are both an agent *inventing* a place on the human's machine; the leading dot changes
nothing. The complaint is invented clutter, not what `ls` shows. *Invented* means the agent chose the
location itself. A path the human chose, or an authority that already existed and puts this project's
files there, is not invented. A repo document may relay that authority; it cannot originate one, and a
handoff or session-state document relays nothing either way.

## Three kinds of write, one rule each

**1. Downloads, environments, tool clones** — model weights, a venv, a cloned tool, whether they
serve one task or many. In order:

- the tool's own documented cache, if it has one, however many tasks the material serves — and most do (`hf download` uses
  `~/.cache/huggingface` unless told otherwise; overriding that to hand-build `~/data/mage-vl` is
  the exact move that produced this rule). An evictable cache is never the only durable copy of
  material that must be kept;
- else, material that dies with the task goes to scratch; for material that must be kept, use the
  cache root the repo's `CLAUDE.md` relays only when that root already existed or the human chose it
  (`reference/repo-claude-md.md`);
- else, where the entry-point rule has established that the write belongs outside the project,
  **stop and tell the main session** (a worker) or **ask the human** (the main session). Never an
  invented entry under `$HOME`, hidden or not. A design spec relays authority but never originates
  it: a destination the human chose or one that already existed still counts when the spec repeats
  it; a destination the spec invents counts for nothing, including a spec written for this task.

**2. A deploy root or runtime state** — where a service the project runs keeps its files. The
location is the project's call: use a destination that pre-change code, configuration, or a tool
convention already assigned to this project, or one the human chose. It is **documented in that
repo's `CLAUDE.md` or architecture doc before anything lands there**. A same-change document may
relay an existing or human-chosen destination; it never authorises one the change invents, and a
handoff or session-state document relays nothing. The root is not merely a directory that happens to
exist, and it is not an invented entry under `$HOME`. A declared root also says what it retains —
which copies are removed and when — because naming the place fixes where things go, not how many pile
up: a documented `~/services` still grew fourteen release directories and a multi-gigabyte rehearsal
leftover.

**3. Scratch, drops, and task-local deliverables** — session-local, gone when the session is; release
deliverables are not this kind. Write to the
scratch the session gives you — the location your harness provides: on Claude Code,
`$CLAUDE_JOB_DIR/tmp` or the scratchpad it names; on a harness that names none (a standalone Codex
session), one dedicated `mktemp -d` directory per task. Post any durable result to the issue, PR, or
other destination the placement rule chose, then remove the scratch directory best-effort at task
completion (an abnormal exit leaves it to the OS's tmp cleanup). A
process-invoked agent (`reference/external-agent.md`) has none of that — under a write-scoped
sandbox a Claude dispatcher's `$CLAUDE_JOB_DIR` is present as a variable but denied as a path (a
Codex dispatcher passes none), and only the worktree and `/tmp` are writable — so its scratch is a gitignored
subdirectory of its own worktree, which dies with the worktree (`reference/worktree-lifecycle.md`).
An `-o` result captured by the dispatching CLI is a dies-with-the-task file: the CLI, outside the
agent's sandbox, writes it into the dispatcher's session scratch as `reference/external-agent.md`
prescribes.
The human's Desktop and `$HOME` are never a drop target unless the human names one: showing them a
result is what the PR, the issue, and the conversation are for.

## Say where you wrote

Every durable write outside the repo is named in the PR description or, where a light start has no
PR, at handback — the path, which branch of the rule applied, and why. **A committed write is
reviewable; an ad hoc one is not.** If the write is in the diff — a script,
a Makefile, a CI step that fetches to a path — merge check 1 sees it and can flag an invented
location like any other line. A write done by a command typed in the session (which is what every
row of the incident that prompted this rule was) leaves no trace in any diff; check 1 sees the diff
and the report and nothing else, so nothing catches an undisclosed one.
This is a discipline the acting agent keeps, not a gate — the same shape `reference/adr.md`'s
attribution rule and ADR 0036 name for their own duties. The disclosure gives a human, or a later
audit, the one place to look; the reviewer asks for it when a task plainly needed a location (a
model, a dataset, a service) and the report names none.
