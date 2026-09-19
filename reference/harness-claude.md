# DevStandard in Claude Code

This page maps the Claude harness for a dispatched worker; `reference/worker.md`, delivered with
it, carries the contract.

## The built-in subagent

The Claude harness loads an agent definition's body as the subagent's system prompt, and
`agents/worker.md`'s body is `reference/worker.md` followed by this page, byte for byte. Both
reach every Claude worker without a read, and both survive compaction.

A native child inherits its caller's directory and must target the packet's worktree for every
command. It inherits the host's permissions and adds no sandbox of its own. Its own subagents go
through the Agent tool, which takes `model` per call and no effort, so an undefined effort inherits
this session's.

### Recovering the binding

A native Claude child recovers only from the host's record of its own conversation, never from a
model-written compaction summary, from the caller's current directory, or from another lane's
receipt: emit a nonce through any tool call, then `grep -rl <that nonce> ~/.claude/projects`
matches exactly one recorded child conversation, whose first line is the packet as delivered. More
than one match is a blocker to report, never to guess past.

## The Claude CLI worker

`scripts/dispatch --implementation claude-cli` runs that same definition as a top-level process
started in the assigned worktree, under host and tool permissions with noninteractive
`acceptEdits`, and adds no OS sandbox of its own.

Where the host records nothing — a dispatched CLI worker runs with session persistence off — the
lane lookup below governs instead, and a child with neither carrier returns the lost binding to the
orchestrator.

A CLI process begins in its lane. When that directory is a linked worktree on a matching
`task/<issue>-...` branch, identify the repository from `origin`, read the latest matching
`devstandard-dispatch-v1` process-run receipt, then read its absolute brief in full. Resume only
when branch and worktree match exactly and every required field is present. A missing, equally-new,
or unreadable receipt/brief is a blocker; never reconstruct a task from a partial summary.
