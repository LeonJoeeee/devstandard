# 0002 — superpowers is a quarry, not a dependency

Status: Accepted (direction set 2026-06-09, recorded 2026-06-10)

## Context

superpowers (an official plugin; 222k stars; actively maintained; installed copy = latest v5.1.0) overlaps DevBook on worktree/merge/review content. But all 14 of its skills contain **zero references to the Workflow tool** (grep-verified) — their parallelism is the older Agent-tool style — and they carry opinions that clash with this method (a universal "tests green" gate, announcement boilerplate, an in-house pipeline chain, ask-the-human-anytime).

## Decision

**Reference it, specialize it, eventually replace it**: port the best parts verbatim (MIT license; keep attribution), specialize everything for our Workflow-driven model, and **do not install superpowers in the final environment**. The earlier "delegate to superpowers + fallback" plan is withdrawn.

The porting plan lives at `_source/superpowers-porting-plan.md`: zero skills portable whole, 11 to specialize, 3 to skip; near-verbatim portable files (the three debugging technique files, the code-reviewer prompt, the git finish mechanics, the testing anti-patterns); a 12-entry conflict register, every entry resolved as "DevBook policy wins."

## Consequences

No external dependency and one consistent voice; the price is that ported material is ours to maintain — upstream updates no longer flow in.
