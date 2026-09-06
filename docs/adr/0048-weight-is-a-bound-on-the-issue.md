# 0048 — Weight is a bound on each issue; the declared setup fork is removed

Status: Accepted (2026-09-07). Supersedes 0014.

*This ADR changes what DevStandard ships — one project setup instead of three declared paths — so a
reader in a seeded project should take it as method.*

## Context

0004 keyed the full lifecycle to one event, repo creation. 0014 replaced that with three
human-declared paths — full by default, a light start when the human calls the work throwaway or
experimental, a mini-lifecycle for a big in-repo initiative — while keeping 0004's principle that the
trigger is an explicit human signal and never an agent's guess at size.

Two things moved under it. 0022 made ceremony universal, withdrawing the anti-ceremony floor this
ADR had been cited for — 0015's trivial in-repo change done in-session — before this rebuild began.
So the fork was already carrying less than it was written to carry. And the rebuilt pages no
longer contain the fork at all: nothing in `core.md` or `reference/prd.md` selects among three setup
shapes, `reference/prd.md` is read at project start unconditionally, and the issue instead carries
**bounds** — weight and required finish — which the dispatcher refuses to launch a lane without.

The fork's remaining job is therefore already being done, but per task instead of once per project,
and by a field the human fills when the issue is written.

## Decision

The three declared setup paths are removed. There is one project setup — the founding documents at
project start — and **weight is a bound on each issue**, settled with the human as the issue is
written.

**0014's and 0004's shared principle is what survives, and it is restated here: the agent never
guesses scope.** It moves from a once-per-project declaration to a per-task field, where the human is
deciding anyway and knows more than they did at project start. Silence still authorizes no
downgrade: bounds are a required issue field, and an unfilled one is a refusal rather than a
default.

0014's monorepo gap closes by the same mechanism — a new top-level package is an issue with its own
bounds, and the founding documents get written when the project has none. Its
big-in-repo-initiative path folds into ordinary practice: work that touches top-level design
escalates and takes an ADR, which is the rule everywhere else already.

Rejected: **keeping the light path** — it asks for the ceremony decision at the moment least is known
about the work, and the relief it offered is available per task from someone better informed.
Rejected: **keeping the mini-lifecycle as a named path** — a big in-repo initiative is a sequence of
issues under the architecture-escalation rule, and naming it separately adds a classification with
no distinct behavior behind it.

## Consequences

One classification fewer for the orchestrator, and the anti-ceremony pressure now lands where the
work is, on the issue, instead of on a word said once at project start.

The cost is the one 0014 argued for: a genuinely throwaway repository no longer gets a project-level
exemption from the founding documents. That relief is withdrawn deliberately, under the approved
architecture, and it is the thing to watch. If such projects start carrying an architecture doc they
let drift — the failure 0014 named — the answer is a rule about what a repository with no
coordination need writes at setup, not a return to a scope word declared once.
