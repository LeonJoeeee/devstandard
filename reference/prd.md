# How to write the PRD

Read this at project start, before any code. The PRD answers **what we are building, why, and what counts as done** — never *how* (structure belongs in the architecture doc). One page. Write it WITH the human: their answers set direction.

The interview itself is the `superpowers:brainstorming` skill's craft — use it, then return here; the output lands in this PRD, not in superpowers' own spec files.

Why it exists: it is much easier to change your mind on paper than in code. The PRD's job is to catch "building the wrong thing" before anything is built.

## Sections (all four, keep each short)

1. **One sentence** — what this is, for whom.
2. **Why build it** — the problem or itch; what's wrong with not building it.
3. **Features as user value** — what the user can do, not how it works. Include **"What we are NOT doing"** — the explicit non-goals; this list prevents more wasted work than anything else.
4. **Definition of done (release criteria)** — concrete, checkable statements. These are the project-level ancestors of every task's done-check: tasks derive their bars from this list.
5. **Constraints** — hard limits worth writing down (compatibility, performance, budget, deadlines). Skip if none.

## Rules

- What/why only. The moment you write a component name or a data flow, move it to the architecture doc.
- Every release criterion must be mechanically checkable — "feels good" is not a criterion.
- Keep it maintained: when direction changes (through the human), update the PRD in the same change.

## Setup mechanics (the whole setup phase, not just the PRD)

- The agent creates the repo first, after asking the human two things: the name, and public or private.
- Setup commits (this PRD, the architecture doc, the skeleton) land directly on main — branch protection arrives together with CI as the LAST setup step, so nothing blocks the bootstrap.
- The architecture doc settled with the human IS the skeleton's design, and that settling is its challenge — setup work needs no separate design spec.

## Template

```markdown
# <Project> — PRD

## One sentence
<what this is, for whom>

## Why build it
<the problem; why now>

## Features (as user value)
- <user can ...>
- <user can ...>

### What we are NOT doing
- <non-goal>

## Definition of done
1. <checkable statement>
2. <checkable statement>

## Constraints
- <hard limit>   (omit section if none)
```

Lands in the target repo as `docs/PRD.md`.
