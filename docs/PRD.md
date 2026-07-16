# DevStandard — PRD

> This document answers *what we are building, why, and what counts as done*. The *how* lives in `architecture.md`; the reasoning behind key decisions lives in `adr/`.

## One sentence

DevStandard is a Claude Code plugin that extends the GitHub flow to agent teams — a complete development method covering **when the rules apply (a new project = the full suite, scope declared by the human), how documents are managed (PRD / architecture / ADR), how code flows (issue → branch/worktree → PR → gated merge), and how each task is executed**. It is the successor to the `development-playbook` skill.

## Why build it

1. **Triggering is unreliable.** A methodology skill almost never auto-triggers from its description (measured repeatedly: ~0% on real dev tasks). A SessionStart hook must inject the method into every session.
2. **The old method only covers single tasks.** development-playbook is "how one medium task lands as running code." It has no project layer — no PRD, no architecture doc, no ADRs, no multi-session parallel coordination, no CI/CD.
3. **The Workflow tool changed the economics of execution.** Orchestration is now native and deterministic; what remains scarce is quota and judgment. The old SDD-document method was designed for single-agent development and is replaced by discipline rules plus a cost ladder (always-on SDD becomes a trigger-gated design spec — ADR 0017; workflows are reserved for verification-dense moments).
4. **superpowers covers the craft, not the project.** Its skills teach one agent to do one job well (debugging, TDD, brainstorming) but have no project layer — no PRD/architecture/ADR set, no issue→PR coordination, no CI gate — and carry opinions that clash with this method where their territory overlaps ours (a universal "tests green" gate, its own pipeline chain). DevStandard is the method layer wrapped around Claude Code (the mechanics) and superpowers (the craft): it points at their strengths at the right step and supplies what neither has (ADR 0016).
5. **Collaboration with agents is a problem humans already solved.** One person could never build a large project; the GitHub flow is humanity's converged answer to team coordination. Human+agent work is a collaboration problem of the same shape — reuse the flow that won instead of inventing an agent-coordination system (ADR 0009).

## User

Anyone building medium-to-large projects with Claude Code: a solo developer directing parallel agent sessions, or a team where several humans each bring their own agents (Leon is user zero). The human appears only at direction decisions; everything else is held by machine verification.

## Features (as user value)

- **Say "start a new project" and the full suite applies**: PRD + architecture + ADR docs → a thin skeleton that pins interfaces → work develops against it → CI/CD generated alongside, plus a repo-root CLAUDE.md capturing commands and gotchas for every later clean-context worker (ADR 0018). Full by default; the human can declare a project small (light start) or an in-repo initiative big (mini-lifecycle) — the scope is declared, never guessed (ADR 0014).
- **A change inside an existing repo is usually just a task**: no project-level ceremony; it goes straight into the task harness.
- **Every task runs under the same discipline**: done-check first, the design must survive a challenge before code, one writer at a time, close on real evidence — and execution picks the cheapest level that holds the work (in-session → a few subagents → small spend-capped workflow runs → chained runs).
- **Parallel work without collisions**: a main session dispatches each task as a GitHub issue; one task = one branch = one worktree, worked by the cheapest executor (subagent / workflow / separate session); work returns as a PR; the architecture doc is the shared baseline; merging is the main session's act, behind two checks — a fresh review (no prior history) then green CI; an architecture-touching change gets the human's approval *before* the merge and produces an ADR (ADR 0015, 0011).
- **Decisions leave a trail**: a substantial change writes a 1–3-page design spec before code (options → decision; it doubles as the worker's handoff and is kept forever in `docs/specs/`); significant decisions (high cost of change) get an ADR; new decisions supersede old ones — history is never rewritten.

## Non-goals

- No craft content of our own where superpowers already has the skill — the flow points at the skill by name, never copies it (superpowers is assumed installed alongside — ADR 0016);
- No router/skill indirection and no one-skill-per-phase chain (one injected page + on-demand files);
- No concrete model names in DevStandard content (model/quota policy is personal config, not method);
- No forced fully-automatic deployment (CD defaults to tag-triggered release; the human decides when to ship);
- No `@path` links between any files (they destroy on-demand loading);
- No project ceremony for small in-repo changes.

## Definition of done (release criteria)

1. In a fresh session the hook fires reliably: core.md appears in context;
2. On-demand loading holds: `howto/` and `aids/` files enter context only when explicitly Read;
3. core.md stays within its budget (hard ceiling ~5,000 tokens, kept lean; ADR 0007 as amended);
4. One real repo-creation project runs end-to-end on DevStandard (this project itself is the first);
5. The plugin installs cleanly: skills-dir local load during development (no pollution of other sessions), user-level install once stable.

## Constraints

- Lean and anti-ceremony: reference files, not a pile of skills; ritual never exceeds what the task needs;
- Plain language: no internal jargon in anything a human reads;
- On conflicts, DevStandard policy always wins (especially over ported superpowers material).
