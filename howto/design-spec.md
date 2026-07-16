# How to write a design spec

Read this when a task is substantial enough to need one (rule below). The design spec is the middle layer between `docs/architecture.md` (the system view) and the code: **one document that settles how a substantial change will be built, before it is built** — and it doubles as the handoff a context-free worker executes.

## When one is required (and when not)

Required when any of these holds — the gate is the significance of the **change**, never the size of the project:

- it changes a shared or public interface (API, schema, on-disk format, a cross-module contract);
- it is a real feature whose design could reasonably go more than one way;
- getting it wrong is expensive to undo.

Explicitly exempt — write nothing: refactors that don't change meaning, objective improvements (speed, fewer warnings), changes invisible to users, and anything the task's issue already fully specifies. The exemption list is what keeps this lean — when in doubt on a borderline case, a half-page spec beats a wrong build, but never write one for the exempt categories.

## What it contains (1–3 pages, never more)

1. **Problem & context** — what this changes and why now; link the issue.
2. **Options considered** — 2–3 real options with the tradeoffs that matter; one line each on what was rejected and why. This section is the document's reason to exist: the chosen design without the rejected alternatives is just code in prose.
3. **Decision** — the chosen design, concretely: the files and interfaces it touches.
4. **Out of scope** — what this deliberately does not do.
5. **Verification** — the end-to-end check that proves it works; the task's done-check derives from this.

Draft it with `superpowers:writing-plans` — a spec is a written plan a context-free worker will execute, and that skill's rules (exact file paths, complete code in every step, no placeholders, map the files and their responsibilities before writing steps, then a self-review pass) are what keep a zero-context worker from getting stuck. Then return to this flow: don't announce the skill; the spec lands here in `docs/specs/`, not in superpowers' own plan folder; ignore its "REQUIRED SUB-SKILL" plan header and the execution-options menu at the end — DevStandard runs execution its own way. Where its mandatory test-first task template doesn't fit the task's done-check (a metric or refactor task isn't proven by a unit test), follow the done-check, not the template. On any conflict, this page wins.

## Mechanics

- **File**: `docs/specs/YYYY-MM-DD-<kebab-title>.md` in the target repo. The date prefix keeps parallel branches from colliding over sequence numbers (the problem ADR numbering solves with merge-time renaming — specs avoid it entirely).
- **Status header**, first line under the title: `Status: draft | accepted | committed | abandoned`. Accepted = survived the pre-code challenge; committed = implemented and merged; abandoned = decided against. **Specs are never deleted** — an abandoned spec is a road not taken, worth remembering; the corpus is a second decision log alongside `docs/adr/`.
- **Review = the existing pre-code challenge**: a clean reviewer (freshly spawned, no history, didn't write it) tries to poke holes in the spec before implementation. Nothing new is added on top.
- **Flow**: by default the spec is drafted on the task's branch and merges with the implementation PR — the worker sets `Status: committed` in that PR before check 1, since the status describes the state at merge (no post-merge edit of a protected main). A spec whose decision must be settled before building starts goes in its own small PR first and stays `accepted`; the implementation PR later flips it to `committed` as part of its reviewed diff.
- **Relation to ADRs**: an architecture-touching change still gets its ADR — the ADR records *the decision and its why* (one page, forever); the spec records *the design* (options, interfaces, verification). Link them; neither replaces the other.

## Template

```markdown
# <change, in one line>

Status: draft

## Problem & context
<what this changes and why now; link the issue>

## Options considered
1. <option> — <the tradeoff that matters>
2. <option> — <why rejected, one line>

## Decision
<the chosen design; the files and interfaces it touches>

## Out of scope
- <what this deliberately does not do>

## Verification
<the end-to-end check that proves it works>
```

Lands in the target repo under `docs/specs/`.
