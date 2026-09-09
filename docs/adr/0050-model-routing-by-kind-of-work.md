# 0050 — Route model and effort by kind of work, without a tier cap

Status: Accepted (2026-09-09). Amends 0024 (the tier cap and mechanical-only downgrade rule) and 0040 (its restatement of the cap and uniform routing); amends 0008, 0036, 0039 and 0047 (their routing statements).

## Context

The human ruled on issue #309 on **2026-09-09** that no model tier is off-limits. The previous
Claude cap prevented difficult judgments from reaching the strongest tier, and a single Codex
model/effort setting did not distinguish review, implementation, scanning, and mechanical work.
Nested helpers also needed an explicit routing rule instead of silently inheriting cheaper settings.

## Decision

Route by kind of work using two knobs, model tier and reasoning effort. The default table and
operative rules live in `reference/external-agent.md`, “Route it explicitly”: final dilemmas,
irreversible judgments and architecture acceptance take the top row; ordinary gating review,
implementation, scans and extraction each have their own row; deterministic work takes a script.
Claude tier aliases and explicit spawn settings remain required, with effort set wherever the
tool supports it. The human's own session model remains outside the method, and a project's root
`CLAUDE.md` or an issue naming a model overrides the table.

The executor asymmetry is deliberate. The human's cost rationale is that Claude's highest tier
costs twice the next tier per token and reviews are frequent, so ordinary Claude gating reviews
stay on the next tier; Codex's everyday top carries ordinary gating reviews too. This records the
human's rationale, not a price guarantee. Retaining the cap and using one strength for every kind
of work are rejected by that ruling; no other alternatives were recorded.

Stuck, ambiguous or unreliable work changes one thing per attempt: supply missing context, raise
effort, raise the model one tier, reduce task size, then ask the human. Never repeat unchanged;
irreversible questions and genuine dilemmas go straight to the top row. Recursion depth never
lowers the tier. Downgrade both knobs only for high-volume, low-difficulty work whose output is
mechanically checkable or can be spot-checked one tier up, after asking whether a script suffices.
A gating review never runs below its producer's tier; architecture review runs one tier above.

## Consequences

The dated standing-setting paragraph remains the single dispatch-default record, unchanged by
this decision. The table supplies routing defaults rather than an automatic task classifier;
the standing project setting and explicit project/issue overrides still apply. Codex-internal
helpers use the same routing table. Role TOML adds the gating row's subagent model and effort
defaults, with explicit spawn settings taking precedence; dispatch passes each root assignment
as its own CLI override while preserving the role hook. Claude worker/reviewer definitions add
explicit high effort and retain their default tier.

Routing now has more values to maintain. Model or tier changes require reconciling the canonical
table, role settings and their tests, plus dated ADR amendments where live instructions change.
The cap statements in 0024 and 0040 are superseded by dated blocks; their other decisions stand.
