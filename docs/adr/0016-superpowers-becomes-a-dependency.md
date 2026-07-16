# 0016 — superpowers becomes a dependency: point at its skills, don't copy them

Status: Accepted (2026-07-16). Supersedes 0002.

## Context

0002 made superpowers a quarry: port the best pieces with attribution, never install it in the final environment — set when the plan was to eventually replace it. A month of lived reality says otherwise. The human runs Claude Code + superpowers + DevStandard together in every session and has declared that arrangement permanent ("the three are siblings — they always appear together"). superpowers is actively maintained upstream (installed: v5.1.0), while our two copied technique files (`aids/testing-anti-patterns.md`, `aids/debugging-techniques.md`) froze at their port date and silently drift. And the layering has clarified: Claude Code provides the mechanics (sessions, tools, agents), superpowers provides the per-step craft (how one agent does one job well), DevStandard provides the method (how a team of agents runs a project) — a layer wrapped around the other two.

## Decision

**Declare the dependency.** DevStandard assumes Claude Code and superpowers are installed alongside it, and its documents point at superpowers skills by name. A pointer is plain text naming the skill to use at a step; the agent invokes the skill itself — DevStandard executes nothing on its behalf.

- Four pointers (names verified against installed v5.1.0): pinning down requirements with the human → `superpowers:brainstorming`; a bug task → `superpowers:systematic-debugging`; implementation guarded by tests → `superpowers:test-driven-development`; an issue/spec written for a context-free worker → `superpowers:writing-plans`.
- The two copied technique aids are deleted — the live skills replace them. `aids/code-review-prompt.md` and `aids/worktree-lifecycle.md` stay: they are DevStandard's own protocol (adapted with attribution), not duplicated craft.
- Two guards carry over from 0002's reasoning:
  1. **Sovereignty and chain-cutting.** A skill serves inside one step of this flow, and every pointer says "then return to this flow" — superpowers skills chain to each other ("next, use skill X") and would otherwise pull the agent into superpowers' own pipeline. On any conflict, DevStandard's page wins; the 12-entry conflict register in `_source/superpowers-porting-plan.md` still maps where the conflicts live.
  2. **A never-point list.** Skills whose territory DevStandard owns are not pointed at: worktree setup/teardown and branch finishing (superpowers keeps worktrees after PRs; our merger deletes them), the code-review pair (merge check 1 has its own protocol), and its dispatch/router skills (announce boilerplate, a universal tests-green gate, ask-anytime).

Rejected: conditional "if superpowers is installed…" pointers with the copies kept as fallback — that preserves a standalone mode nobody uses, at the price of permanent duplication and drift.

## Consequences

Leaner (two copies deleted; upstream improvements now flow in live) and honest about the real environment. Costs: DevStandard no longer works standalone — the README declares the requirement, and the plugin system cannot enforce it; an upstream rename or content change can dangle a pointer or sharpen a conflict — daily dogfooding catches it, and the conflict register is the guard. 0002's porting plan keeps earning its place as the map of what to point at and what to keep away from.
