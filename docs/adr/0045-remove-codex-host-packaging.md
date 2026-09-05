# 0045 — Remove Codex host packaging; Codex is a dispatched executor

Status: Accepted (2026-09-05). Supersedes 0038 and 0039. Amends 0006, 0007, 0008, 0011,
0015, 0016, 0018, 0019, 0024, 0036, and 0040 (their live Codex host, delivery, and routing statements).

## Context

The human's ruling on issue #179, implemented by issue #200, selects one Claude Code
orchestrator with dispatched executors. Codex is used only as a CLI executor invoked by Claude
Code; the DevStandard Codex plugin was already uninstalled on both machines. Keeping its unused
packaging and forced per-worker read of `core.md` contradicts PRD §1.6's no-unused-structure
criterion and §5's separation of role context and delivery.

Architecture chapters 1, 3, 6, and 7 previously left the Codex host carriers unchanged without a
compatibility promise. Issue #200 rejects that alternative: the path is removed from scope.

## Decision

DevStandard ships as a Claude Code plugin only. Remove `.codex-plugin/`, the Codex delivery
branch of `hooks/session-start`, `reference/harness-codex.md`, and the Codex install/update and
hookless fallback instructions. The Claude hook retains its forced read, payload, stdin handling,
and matcher; unsupported environments retain a visible warning and receive no method instruction.
The former equal-valued compatibility aliases are unsupported, while Claude's environment with an
unrelated inherited `PLUGIN_DATA` keeps its existing behavior.

Codex remains a worker or reviewer process, with role constraints supplied by dispatch rather than
plugin startup. `reference/worker-brief.md` carries the necessary explicit operational-memory read,
craft-skill trigger, and scratch guidance. ADR 0040's executor preference and explicit standing
setting remain on `reference/external-agent.md`; Codex host orchestration is removed from scope.

## Consequences

The two Claude manifests stay in lockstep. CI retains the Claude hook and method budgets, verifies
unsupported-environment warnings and absent Codex host artifacts, and reconciles the old
manifest-description, fallback, and dual-footprint assertions. These are deliberately staled gate
assumptions under `reference/red-check.md`; the PR declares each for merge check 1.

Architecture chapters 1, 3, 6, 7, and the traceability table now describe removal. Dated amendments
reconcile live ADR instructions while preserving their original bodies and measured history.
Historical specs remain design records. This change does not implement the later role split,
inline-delivery choice, agent definitions, or dispatcher. Human architecture sign-off remains a
pre-merge duty of the main session.
