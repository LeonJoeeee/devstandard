# 0024 — DevStandard names Claude's model tiers; a spawned agent never runs above `opus`

Status: Accepted (2026-07-25). Amended by 0028. Amended by 0039 (2026-08-26). Amends 0008 (its model-routing bullet only; the ladder, run sizing and rationing stand).

## Context

0008 routed by relative tier and delegated the concrete mapping to personal config (`~/.claude/CLAUDE.md`). That delegation went empty: the human cleared the file as duplicative of DevStandard (verified 0 bytes), so a session read "the strongest you have" with nothing saying which model that is. Meanwhile the main session legitimately runs above `opus` — which is what turns "an unrouted agent inherits the session's model" from a harmless default into the one invisible path that breaches a cap, since nobody typed a model and nobody reviews it. The human's own call (issue #65): "子代理最多只能使用 opus,酌情往下减,主 session 的事情 user 自己控制".

## Decision

DevStandard is a Claude Code plugin and names Claude's tiers outright. Every agent the method spawns is capped at `opus`, whatever the main session runs; `opus` is also the default — every review that gates progress (the pre-code challenge, merge check 1, a helper checking a worker's output) included — and `sonnet`/`haiku` are for genuinely mechanical work (file sweeps, test runs, checklist edits). Tier aliases only, never version ids. The model is set explicitly on every spawn that takes one; the v0.11.5 "a lone judgment agent may inherit" carve-out is retired. A spawn that exposes no model knob at all — a context-inheriting fork, a skill that runs in a subagent — is the cap's one exception, because a spawn with no knob cannot be routed by anyone; it never touches a gate, since every gating review independently requires a clean, non-fork reviewer. The main session's own model, and the human's quota budget, stay the human's.

The cap is one-directional: a session model above `opus` is the expected case, not a violation — which is why the stuck-worker rule now reads "step up a tier (`opus` at most)".

Rejected: (a) keep relative tiers and re-populate personal config — the method cannot depend on a file it does not ship and cannot verify; (b) name version ids (`claude-opus-5`) — silent rot; (c) keep the inheritance carve-out — the one path that breaches the cap invisibly; (d) a three-rung assignment with implementation pinned to `sonnet` — it demotes the method's two quality gates one tier below the policy being imported, and leaves ordinary (non-spec) implementation, which is most work, in no bucket at all.

## Consequences

The page is now Claude-specific and dated, on purpose, in exchange for a rule that binds instead of pointing at an empty file. A new tier ABOVE `opus` costs nothing (the cap is a ceiling and a stronger session model is already today's case); a new tier between or below costs nothing (the named rungs still exist). A rename or retirement of one of the three names, or an account that cannot use `opus`, costs exactly four edits: core.md, core.zh-CN.md, architecture.md §4, and a dated amendment here. Review panels now fan out at `opus`, so panel SIZE, not tier, carries the quota load — which is already the rationing rule's job ("fix how many reviewers"), and why core.md's workflow warning stays scoped to unrouted fan-out. Net core.md cost: +43 tokens over the bullet it replaces.

**Amendment (2026-08-05, see 0028):** the cost estimate above — "a rename or retirement of one
of the three names … costs exactly four edits: core.md, core.zh-CN.md, architecture.md §4, and
a dated amendment here" — is now **three**: `core.zh-CN.md` no longer exists (0028). Amended
rather than left as a historical note, because unlike a Consequences line describing what a
past change did, this one instructs a *future* session on what a future action will cost, and
a session following it would go looking for a file that is not there.

**Amendment (2026-08-26, see 0039):** the cap and tier names this ADR sets bind agents spawned
through Claude's harness. A Codex main session routes within its own harness's models at the
human's standing effort settings; what transfers universally is the discipline — set the model
explicitly on every spawn that takes one (0036).
