# 0014 — Lifecycle scope follows a human-declared signal, not repo creation alone

Status: Accepted (2026-07-09). Supersedes 0004.

## Context

0004 keyed the full lifecycle to one event — "the human asks to create a new repo" — to avoid agents guessing project size. Its **principle survives**: the trigger must be an explicit human signal, never a complexity guess. Its **conclusion does not**: 0004 refuted only *agent-guessed* size tiers and never considered a *human-declared* scope signal, which is equally explicit and equally guess-free — so the jump from "no agent guessing" to "identical for every project, no size exceptions" is stronger than the argument supports.

Keyed to a packaging event, the rule fails in three real directions:

- a **throwaway / config / experiment repo** pays a mandatory PRD interview plus a permanent architecture-doc maintenance contract it will let drift (a drifting baseline is worse than none, by the method's own axiom) — for coordination value never realized;
- **monorepo shops** never create a repo, so the entire project layer silently no-ops for a large slice of the "medium-to-large team" audience;
- a **major in-repo initiative** too big for one task (a rearchitecture, a language port — the Bun-port class 0008 itself cites) is denied the planning layer by "a change inside an existing repo is just a task."

And the method's own constraint — "ritual never exceeds what the task needs" — directly contradicts "no size exceptions."

## Decision

Ceremony follows what the human declares, keeping zero agent guessing:

- **Default** (a project-shaped "start a project" / "create a repo") → the full lifecycle, as before. **Silence defaults to full** — no downgrade is ever inferred.
- **Human declares it small** ("throwaway / experiment / scratch / config") → a light start: CI only, or nothing, plus the "upgrade to the full suite" path, now promoted from a footnote to a stated option.
- **In-repo initiative the human declares big** (or that hits the two-axis gate: touches top-level design, or spends large cost) → a mini-lifecycle: a scoped PRD-delta with its own done-definition, an architecture-doc update plan + ADR, a task split, then the normal outer flow.

The trigger phrase becomes **"start a new project"** — repo creation is the common special case; a new top-level package/app/service in a monorepo fires the same lifecycle in its subtree.

## Consequences

Ceremony scales with declared scope while the trigger stays an explicit human signal — the property 0004 correctly protected. Small work stops paying for coordination it never uses; big in-repo work gets the planning layer it needs; monorepos are covered. Cost: three declared paths instead of one — bounded because the human's own words select the path and the agent still never guesses.
