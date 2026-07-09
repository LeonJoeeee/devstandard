# 0007 — No router, no skill: the hook injects a one-page core

Status: Accepted (2026-06-11). Supersedes 0001. Amended by 0015 (2026-07-09).

## Context

ADR 0001 shaped the plugin as manifest + hook + a lean ROUTER skill dispatching to ~12 reference files. Subsequent rulings shrank the content drastically: execution teaching was dropped entirely (the Workflow tool is the harness, ADR 0006; later hardened in ADR 0008 to "rules, not method"), and the per-phase methodology files collapsed into a handful of rules. With so little content left, a dispatcher has nothing to dispatch — the router became indirection for its own sake.

## Decision

Drop the router and the skill component entirely. The SessionStart hook injects **one file, `core.md` (~one page: trigger rule + execution discipline + collaboration standards + howto pointers)** directly as additionalContext. Everything else is plain on-demand files: `howto/` (PRD / architecture / ADR / CI-CD templates, read only at repo creation) and `aids/` (optional helpers, read when useful).

What survives from 0001 unchanged: the plugin shell (manifest + hook) as the trigger mechanism; the two on-demand loading seams; the absolute `@path` ban; the every-session token budget — now applied to core.md (target ≤ 800 tokens, ceiling ~1,000).

## Consequences

One less concept, one less hop, and the filename list under `howto/`/`aids/` is the only index needed. The cost: core.md must be ruthlessly edited — it is the single always-loaded artifact, so every line must earn permanent residency.

**Amendment (2026-07-09, see 0015):** The every-session budget is relaxed — hard ceiling ~3,000 tokens, kept as lean as the content earns (currently ~1,700) — so core.md can state the full collaboration model (roles, contract, worker boundaries) inline, because a subagent worker gets no injection and must be briefed from what the cockpit can quote. The hook-injected-one-page mechanism is unchanged; only the size ceiling moves — every line still earns its place.
