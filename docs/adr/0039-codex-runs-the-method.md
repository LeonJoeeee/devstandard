# 0039 — Codex runs the method; worker constraints ride the dispatch, not the hook

Status: Superseded by 0045 (2026-09-05). Amended by 0045 (2026-09-05). Originally Accepted (2026-08-26). Amended by 0040 (2026-08-26). Amends 0038 (identity and scoping — the measured delivery mechanics
stand), 0006 (harness-native orchestration), 0007 and 0019 (the hook's Codex branch delivers the
method, not a role), 0008 and 0024 (the tier cap scoped to Claude-spawned agents), 0015 (the cockpit
is harness-neutral), 0016 (the harness assumption widened), and 0018 (the fallback reframed as
install guidance).

*This ADR decides what DevStandard ships on every harness — a reader in any seeded project should
take it as method.*

## Context

0038 (shipped v0.27.0) read the human's "Claude leads, Codex executes" as an identity: every Codex
session permanently a worker, told so by the hook, scoped by a committed `.devstandard` marker with
an adopt ceremony. The human corrected it the day it shipped (#155): **the leadership is the shape
of a collaboration, not a brand on the harness.** Sharpened twice more in the same exchange: worker
constraints are injected by the dispatch prompt; a session the human opens is a main session — and
being one needs **no announcement at all** ("甚至这个事情你都不用跟他说'你是主会话'"). A harness is
trained and built to be the main session; the only identity that ever needs saying is *worker*, and
the dispatch brief's first line already says it. #156 landed alongside: dispatch an external agent
as an *agent* — outcome, boundaries, done-check, write access for implementation — never a
read-only oracle.

The design survived seven adversarial challenge rounds (fresh Codex reviewers at xhigh; ~31 findings
absorbed; one exchange where the author's narrowing of a fix was rebutted and conceded — the log is
on #155).

## Decision

**Both harnesses receive the same method, unconditionally.** The session hook's Codex branch
delivers a forced read of `core.md` **plus** `reference/harness-codex.md` — a bounded page of name
mappings only (operational memory stays `CLAUDE.md` everywhere; session scratch; `EnterWorktree`;
craft skills; Agent/Workflow primitives; the cross-harness model rule; the read-only gating-helper
rule). No marker, no adoption ceremony, no role text: `.devstandard`, `scripts/codex-adopt`, and the
managed `AGENTS.md` block retire.

**Worker identity has exactly one announcement: the dispatch brief.** `core.md` and
`worker-brief.md` carry no self-classification — `core.md` describes the dispatched worker in the
third person and keeps one neutral trigger (every dispatched worker receives, or opens, the brief
before acting); the brief opens by saying what makes its reader a worker. A session the human opens
is that conversation's main session, whatever the harness, and is never told so.

**The tier cap is Claude's harness rule.** `opus`/`sonnet`/`haiku` bind agents spawned through
Claude's harness (0024 as scoped here); a Codex main session sets its models explicitly within its
own harness at the human's standing effort settings — the set-it-always discipline is universal
(0036), the names are not.

**The measured mechanics of 0038 stand unchanged**: plugin-hook discovery on both harnesses,
one-time trust, the `PLUGIN_DATA`-equality discriminator with its two-sided requalification trigger,
the byte-identical Claude branch, the unknown-harness warning.

## Consequences

- **Always-read cost, stated once** (the headroom carve-out): on Codex the payload is `core.md`
  plus the mappings page — at this decision, roughly 5,300 proxy tokens combined against `core.md`'s
  5,000-token gate plus the page's CI-enforced 4,096-byte gate; the two gates are the current
  figures a reader needs thereafter.
- **Worktree bootstrap is harness-neutral**: the full setup seeds `/.claude/worktrees/` into
  `.gitignore`; every creation path (dispatch lanes, Birth, a worker creating its own) carries the
  pre-creation `git check-ignore` trigger.
- **Migration from v0.27.0** (one release-day cohort): update the plugin first, then remove
  `.devstandard` and the managed `AGENTS.md` block by a small reviewed PR, keeping the
  worktree-ignore line; a hookless repo replaces the old block with the README's neutral fallback
  snippet instead (prepended, in the effective instruction file).
- **A measured compliance deviation is on record**: trivial one-shot action prompts can skip the
  hook's initial read (method-relevant prompts, and any session that has read the pages, comply
  fully — including self-arranged fresh review); the evidence and its narrow scope live in PR #157's
  V2/V4 verification comments. The same honest bet ADR 0019 records for the Claude side.
- Design and challenge record: `docs/specs/2026-08-26-codex-gets-the-full-method.md`, issue #155.

**Amendment (2026-08-26, see 0040):** "at the human's standing effort settings" above now has an address — the standing model and effort are written once on `reference/external-agent.md` (`gpt-5.6-sol` at `xhigh`, dated), and `reference/harness-codex.md` points there. And the executor choice this ADR left open is decided: where Codex is installed, dispatched work goes to Codex; a harness-native subagent only where the work especially suits one.

**Amendment (2026-09-05, see 0045):** Superseded by 0045. Codex no longer receives the method through a plugin hook or README fallback, and Codex-as-orchestrator is removed from scope. The Codex footprint and mappings-page budget are retired. Dispatch still supplies worker identity and constraints; operational memory remains `CLAUDE.md`, read explicitly by the worker brief. Existing worktree-ignore and retirement rules remain.
