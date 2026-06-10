# Development Playbook — a Claude Code skill

A disciplined, **general-purpose development method** for an AI coding agent. Instead of jumping
straight from an idea to code (which drops shallow logic errors on anything non-trivial), the
agent walks a single **reference chain** — `external world → top-level design → mid-level design
→ low-level code` — checking each layer against the layer above it, with the human stepping in
only at the direction level.

It applies to **any shape** of task at **medium complexity and above** (build a framework, add a
feature, fix a substantial bug, refactor, improve a metric). A medium task runs the method
directly; a complex (larger-than-one-service) task starts with a human-in-the-loop
**brainstorm-split** into medium pieces, then runs the method on each. The shape only decides
"what counts as done"; the skeleton never changes.

## Files

- **`SKILL.md`** — the execution layer: a thin checklist (the trigger + run order). This is what
  Claude Code loads; its `name` is `development-playbook`.
- **`METHODOLOGY.md`** — the model and the *why*: the single source of truth. `SKILL.md` points
  back into it and never restates its criteria.

## Install

As a **user-level skill** (available in every project on this machine):

```bash
git clone https://github.com/LeonJoeeee/development-playbook.git ~/.claude/skills/development-playbook
```

Or as a **project-level skill** (versioned with one repo): clone/copy it into that repo's
`.claude/skills/development-playbook/`.

## Scope

**MEDIUM and above.** A medium task — spans multiple coupled modules or a pipeline, up to ~one
service/module — runs the method directly. A complex (larger-than-one-service) task is also in
scope: it starts with a human-in-the-loop **brainstorm-split** into medium pieces, then runs the
method on each in dependency order. Not for trivial one-file/one-line changes, and not for pure
questions (the output is an answer, not code). See `METHODOLOGY.md` §0.5.
