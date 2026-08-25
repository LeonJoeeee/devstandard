# 0038 — DevStandard is a method with per-harness adapters; Codex is the second

Status: Accepted (2026-08-25). Amends 0018 (its `AGENTS.md` rejection is clarified to cover the
operational-memory channel only; 0038 uses `AGENTS.md` for Codex *delivery* — reconciled, with a
measured check that Claude Code does not read a co-present `AGENTS.md`). Extends 0008 (the execution
ladder is read harness-neutrally), 0019 (the forced first read gains a second delivery form), and 0036
(Codex as the *main session*, the other direction from Codex as a dispatched executor). Follows 0028's
mapping-table-not-copy shape; applies 0036's model-cap ruling to the tier vocabulary. Every other
Claude-side decision stands unchanged — this adds a second harness's realization beside them.

*This ADR decides what DevStandard ships and what it is, not only how this repo operates — a reader in
any harness's seeded project should take it as method.*

## Context

DevStandard shipped only to Claude Code. The human asked (#148) to run the method on Codex as the main
session. The whole method is harness-neutral prose a model reads on demand; only two things were
Claude-specific — the forced first read (ADR 0019's `SessionStart` hook) and five kinds of Claude-bound
vocabulary across nine files (model tiers, `superpowers:` skills, `CLAUDE.md`, the Agent/Workflow
tools, `EnterWorktree`).

Both were settled by building against `codex-cli 0.144.6`, not by reading docs — this repo had three
times shipped "verified" mechanics never run:

- A Codex **plugin cannot force a first action**: a plugin-registered `SessionStart` hook does not fire
  (measured in `codex exec` and an initialized interactive TUI); there is no plugin-root variable, no
  text-injecting manifest field, and `codex plugin add` writes no `AGENTS.md`. Superpowers confirms the
  ceiling — its Codex manifest has no hook and ships as skills, the ~0%-self-trigger path ADR 0001
  rejected for a methodology.
- Codex **reads the consuming repo's `AGENTS.md` at session start and obeys it** — demonstrated
  end-to-end: an `AGENTS.md` pointer at the installed real `core.md` caused it to be read first (a
  sentinel echoed, on a prompt naming no file), and `core.md`'s top routing sentence then caused
  `reference/harness-codex.md` to be read too. For a local-checkout install, the path resolves via
  `codex plugin list --json` to the checkout dir and is version-agnostic, so the pointer cannot go
  silently stale.

## Decision

**DevStandard is a method with per-harness adapters.** The shared `core.md` + `reference/` tree is the
method, written once. An *adapter* is the thin, per-harness layer that (a) packages the tree — a
manifest per marketplace (`.claude-plugin/plugin.json`, now `.codex-plugin/plugin.json`) — and (b)
delivers the forced first read and (c) maps the Claude-bound names. Claude Code is the reference
adapter (hook delivery, native `CLAUDE.md`); Codex is the second: `AGENTS.md`-pointer delivery written
by a per-repo setup step, and a single mapping file `reference/harness-codex.md` reached by one routing
sentence at the top of `core.md`.

The vocabulary is mapped, never neutralized in place (0028): one Codex-only mapping file rules on each
of the five kinds, so `core.md` pays one sentence and the Claude reader is untouched. The one path a
held mapping cannot reach — `reference/worker-brief.md`, pasted verbatim into a worker that never reads
`core.md` — is covered two ways: the dispatching session, primed by having read `harness-codex.md`,
translates the brief at paste time, and the brief carries a pointer back to the mapping file for a
worker that is itself a full session.

## Consequences

- **The delivery asymmetry is real and is stated, not hidden.** On Claude Code the hook makes the
  method automatic per install. On Codex it is **opt-in per repo**: a repo that never runs the setup
  step simply does not have DevStandard — the method is *absent* there, not degraded — and the pointer
  depends on the checkout staying current (`git pull`). This is the honest cost of Codex having no
  plugin-level session-start channel.
- **One repository, three manifests.** CI gate 6 now holds all three in lockstep;
  `CLAUDE.md`'s command block and its release-delegation prose (which said "both manifests") are updated
  in the same change, or the next release bumps two of three and the gate fails.
- **Model tiers do not transfer, the discipline does** (0036): `harness-codex.md` says "set the model
  explicitly, at or below your cap; `opus` is Claude's name, not a Codex tier."
- **Published-marketplace distribution is out of scope.** Install is from this repo's checkout, where
  the path is stable; a remote install resolves to a versioned cache and reintroduces the stale-path
  question — a later decision with its own build check.
- Design recorded in `docs/specs/2026-08-25-devstandard-codex-adapter.md` (accepted after a two-round
  challenge). The adapter model is additive and independently revertible; the Claude delivery path is
  unchanged throughout.
