# 0008 — Execution ladder: pick the cheapest rung; workflows are rationed

Status: Accepted (2026-06-11). Supersedes 0003. Amended by 0017 (2026-07-16).

## Context

ADR 0003 made a Workflow mandatory for every task. Reality intervened on two fronts. **Quota:** on the human's 20x plan, a top-tier-resident workflow can burn a 5-hour usage window in ~20 minutes; community reports match (a 22-agent run consuming a full session limit in 10 minutes). **Evidence:** the deep-dive (`_source/workflow-deep-dive-report.md`) showed runs cannot be intervened in mid-flight, agent spend — not orchestration — is the entire cost, and a workflow with no real fan-out or loop is pure overhead over direct subagent calls. The flagship Bun Zig→Rust port (750k lines / 11 days / 99.8% tests passing, yet unsound code — oven-sh/bun#30719) confirmed both that chained small runs are how large work actually ships and that the done-check defines the only quality you get.

## Decision

Replace "Workflow mandatory" with the **execution ladder** — pick the cheapest rung that holds the work:

1. **In-session directly** — the default;
2. **1–3 clean-context subagents** (Agent tool) — an independent piece or review helps; no loops, no wide fan-out;
3. **One small workflow run** — only for a real fan-out (review panel) or a real loop (fix-until-green);
4. **Several chained runs** — the work crosses decision points.

Companion rules:
- **Run sizing:** a run = one coherent stage you can fly blind through (no mid-run intervention exists). Split at human-decision and inspection points, never for capacity. Lower bound: no fan-out/loop → no run.
- **Rationing:** every run is spend-capped before launch (fixed panel sizes, MAX_ROUNDS, budget guards); runs are reserved for verification-dense work (design refutation, fix-until-green, pre-merge audit).
- **Model routing by role, in relative tiers:** judgment/synthesis → strongest available; review panels → one tier down; mechanical work → two tiers down. DevBook names no concrete models — the concrete mapping and quota policy are personal config (`~/.claude/CLAUDE.md`), not method.

What survives from 0003 unchanged: SDD remains optional; the discipline backbone (design refuted before code; verification-heavy token spend; evidence-based closing) applies at **every** rung, not only inside workflows.

## Consequences

Execution cost now scales with the work instead of being fixed at "fan-out always"; the discipline is preserved where it was always load-bearing (verification), and the method no longer embeds model-market ephemera. The cost: rung selection is a judgment call — core.md states the rule in one line so the call is cheap and consistent.

**Amendment (2026-07-16, see 0017):** "SDD remains optional" is refined, not reversed — a substantial change (shared/public interface, a real feature whose design could go more than one way, expensive to undo) now writes a 1–3-page design spec before code; ordinary tasks still write nothing.
