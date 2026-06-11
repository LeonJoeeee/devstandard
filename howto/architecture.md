# How to write the architecture doc

Read this at repo creation, after the PRD. The architecture doc is the **shared baseline every parallel session works against** — it must stay correct, because people coordinate through it. It answers *how the project is structured*; the *why* behind each decision lives in ADRs. 1–3 pages, no more.

## Sections

1. **Header rule** (verbatim, adapted): "This document is the shared baseline for all parallel work: read it before starting any task. Changing anything written here = touching the core: public merge + human approval + an ADR."
2. **Context** — what this system is and what it talks to (a paragraph; a simple diagram only if it pays for itself).
3. **Structure** — the level-1 picture: the main components/modules, what each owns, and the interfaces/boundaries between them. This is the map parallel tasks navigate by.
4. **Key quality goals** — the 3–5 properties that drive structural choices (e.g. latency, simplicity, portability). These are tie-breakers for future decisions.
5. **Pointer to the ADR log** — one line: "Decisions and their reasons: `docs/adr/`."

## Rules

- **Altitude discipline** — the #1 staleness trap is detail creep. The architecture doc holds what is *slow-changing and cross-cutting*. Per-task design detail does not belong here; volatile reasoning goes to ADRs (append-only); implementation detail stays in code.
- **Update-in-same-change**: any merge that changes the structure updates this doc in the same merge (plus an ADR). A baseline that drifts from reality is worse than none — people build against it.
- The doc states *what is*, not history. History lives in ADRs and git.

## Template

```markdown
# <Project> — Architecture

> Shared baseline for all parallel work. Read before any task.
> Changing anything here = public merge + human approval + an ADR.

## Context
<what this is, what it talks to>

## Structure
<components, ownership, interfaces/boundaries — the level-1 map>

## Key quality goals
1. <property> — <why it matters here>

Decisions and their reasons: `docs/adr/`.
```

Lands in the target repo as `docs/architecture.md`.
