# 0004 — Trigger on repo creation; every project gets the same lifecycle

Status: Superseded by 0014 (2026-07-09)

## Context

The initial idea was to scale ceremony by project size ("small projects get fewer docs"). Rejected: **complexity cannot be judged up front** — a simple-looking feature can turn complex midway; and writing the docs is cheap anyway. Size tiers force the agent to guess, and a wrong guess corrupts the process.

## Decision

**The trigger is whether the human asks to create a new repo** — an explicit, known-at-the-start signal involving no complexity guessing:

- Repo creation requested → the full lifecycle: PRD + architecture + ADRs → thin skeleton → parallel-session development → CI/CD. **Identical for every project, no size distinctions.**
- A change inside an existing repo → it is a single task; it goes straight into the harness with no project-level ceremony.

## Consequences

The rule is unambiguous and needs zero classification logic; a one-line change can never be forced into PRD ceremony, because it is not a repo creation. The cost: a project that genuinely grows from a throwaway needs the human to say, at some point, "upgrade this to the full suite."
