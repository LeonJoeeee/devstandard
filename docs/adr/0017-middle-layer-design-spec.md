# 0017 — The middle layer: a trigger-gated design spec, split-on-zoom, and an ADR admission test

Status: Accepted (2026-07-16)

## Context

DevStandard's doc set was flat: a PRD + a single 1–3-page architecture doc + ADRs — small-project-shaped, with nothing between the architecture doc and the code, and no rule for what happens to documents when a project grows. The human asked for both gaps to be filled without reintroducing size-based ceremony (a direction already rejected once). A dedicated research run (82 agents; every claim used was adversarially verified — `_source/doc-layering-research.md`) found the field remarkably consistent: every serious shop keeps a middle-layer design artifact (Google design docs, Oxide RFDs, Rust and Uber RFCs, GitLab design docs); **all of them gate it on the significance of the change, none on project size**, with an explicit no-ceremony floor (Rust exempts meaning-preserving refactors, objective improvements, invisible changes); sizing is elastic inside one artifact type (Google's sanctioned 1–3-page mini design doc); doc growth is hierarchical zoom on demand (arc42), split along domain seams when a single view stops working (C4), always stopping above code level; the load-bearing logs are the append-only ADR log guarded by a cost-of-change admission test, plus the never-deleted design-doc corpus with lifecycle states (Oxide). In the agent era the design doc doubles as the handoff a fresh session executes (Anthropic's documented interview → spec → fresh-session practice), while spec *volume* actively hurts (the Spec Kit critique: ~3× less spec text improved model stability).

## Decision

Three additions — one artifact and two sentences — nothing else:

1. **A trigger-gated design spec** (`howto/design-spec.md`; lands as `docs/specs/YYYY-MM-DD-<kebab-title>.md`). Required only when the change touches a shared/public interface, is a real feature whose design could go more than one way, or is expensive to undo; meaning-preserving refactors, objective improvements, and invisible changes are exempt. 1–3 pages, written before code: options + tradeoffs + decision, files/interfaces touched, out of scope, end-to-end verification. Status header (`draft/accepted/committed/abandoned`); never deleted — the corpus is the second decision log. It is the worker's handoff (the issue links to it) and the object of the existing pre-code challenge — no new review step.
2. **Split-on-zoom** (in `howto/architecture.md`): the overview stays the single 1–3-page doc; when one subsystem can no longer be explained legibly there, extract *that subsystem only* into `docs/architecture/<subsystem>.md`, split along domain seams — never on a size threshold, never to code level (agents read source on demand).
3. **ADR admission test** (in `howto/adr.md`): a decision earns an ADR only if its cost of change is high — fundamental structures, or effects scattered across the codebase; "if every decision is architectural, no decision is architectural."

Rider, made blanket in the same change (it was stated only at two spots, and fork-type subagents inherit context — a real loophole): **every review that gates progress uses a clean reviewer** — freshly spawned, no session history, never a context-inheriting fork, and it didn't write what it reviews.

Relation to 0008: "SDD remains optional" is **refined, not reversed** — ordinary tasks still write nothing; the design spec is SDD's useful residue given a crisp trigger (0008 carries a dated amendment). Rejected: size-tiered doc sets (no surveyed process uses them — the evidence vindicates the earlier rejection); Spec Kit-style multi-artifact generation (volume hurts agents); any new log type (the status-headed spec corpus + the ADR log cover it); code-level documentation.

## Consequences

A small project feels nothing — the gates simply don't fire, and the doc set stays three files. A large project gets the middle layer and a growth path without a second doc class or a ceremony ladder. Costs: one more howto to maintain; the discipline of flipping spec statuses at merge; `docs/specs/` grows monotonically by design — that is the point.
