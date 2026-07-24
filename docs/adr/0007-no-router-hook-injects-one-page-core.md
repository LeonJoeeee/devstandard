# 0007 — No router, no skill: the hook injects a one-page core

Status: Accepted (2026-06-11). Supersedes 0001. Amended by 0015 (2026-07-09); Amended (2026-07-16); Amended by 0019 (2026-07-24, delivery mechanism).

## Context

ADR 0001 shaped the plugin as manifest + hook + a lean ROUTER skill dispatching to ~12 reference files. Subsequent rulings shrank the content drastically: execution teaching was dropped entirely (the Workflow tool is the harness, ADR 0006; later hardened in ADR 0008 to "rules, not method"), and the per-phase methodology files collapsed into a handful of rules. With so little content left, a dispatcher has nothing to dispatch — the router became indirection for its own sake.

## Decision

Drop the router and the skill component entirely. The SessionStart hook injects **one file, `core.md` (~one page: trigger rule + execution discipline + collaboration standards + howto pointers)** directly as additionalContext. Everything else is plain on-demand files: `howto/` (PRD / architecture / ADR / CI-CD templates, read only at repo creation) and `aids/` (optional helpers, read when useful).

What survives from 0001 unchanged: the plugin shell (manifest + hook) as the trigger mechanism; the two on-demand loading seams; the absolute `@path` ban; the every-session token budget — now applied to core.md (target ≤ 800 tokens, ceiling ~1,000).

## Consequences

One less concept, one less hop, and the filename list under `howto/`/`aids/` is the only index needed. The cost: core.md must be ruthlessly edited — it is the single always-loaded artifact, so every line must earn permanent residency.

**Amendment (2026-07-09, see 0015):** The every-session budget is relaxed — hard ceiling ~3,000 tokens, kept as lean as the content earns (currently ~1,700) — so core.md can state the full collaboration model (roles, contract, worker boundaries) inline, because a subagent worker gets no injection and must be briefed from what the cockpit can quote. The hook-injected-one-page mechanism is unchanged; only the size ceiling moves — every line still earns its place.

**Amendment (2026-07-16):** The ceiling is raised again — hard ceiling 5,000 tokens (was ~3,000 via 0015), by the human's call: core.md reached ~3,000 after the v0.5–v0.8 rules (superpowers pointers, the design spec, the blanket clean-reviewer rule, docs-ride-the-diff) and every further line was fighting word-trims instead of clarity. The kept-as-lean-as-the-content-earns rule is unchanged — the ceiling is headroom, not a target.

**Amendment (2026-07-24, see 0019):** The **delivery mechanism** changes: the hook no longer injects core.md's full text as `additionalContext` (Claude Code inline-caps that at ~10KB and persisted the rest to a file behind a 2KB preview — issue #35). It now emits a short imperative instruction telling the model to **Read core.md in full as its mandatory first action**; the page is delivered by the read, not the paste. Everything else in this ADR is unchanged — no router, no skill, the one-page core, the on-demand `howto/`/`aids/` split, the `@path` ban, and the 5,000-token ceiling all stand (the ceiling is now the context-cost governor rather than a delivery limit).
