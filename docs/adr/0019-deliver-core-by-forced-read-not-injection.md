# 0019 — Deliver core.md by hook-forced first-action read, not full-text injection

Status: Accepted (2026-07-24). Amends 0007 (delivery mechanism only; the one-page shape and the token ceiling are unchanged).

## Context

Since 0007 the SessionStart hook delivered the method by **injecting core.md's full text** as `additionalContext`. That silently stopped working. Claude Code inline-caps hook `additionalContext` at **~10,000 bytes** (undocumented, hardcoded, no settings key or env var to change it, and it applies to every hook event): above the cap the harness persists the full text to a `.txt` file and injects only a **~2KB preview plus the file path**. core.md is now 13,988 bytes, so every session since ~v0.4.2 — when the page first crossed the cap — received a fragment: the trigger rule survived in the preview, the task flow, merge checks, worker rules, and safety rules sat behind a file the model was never told to open (issue #35, with the harness-cap research in its comments).

The CI token gate never caught this because it measures a **different axis**. 10KB of hook output is ~2,300 tokens by our `words×1.35` formula — far under the 5,000-token ceiling — so the byte cap binds long before the token ceiling ever could. A green token gate coexisted with a two-thirds-truncated delivery for months.

The reference is proven: the human's research project delivers 20–57KB orchestrator/executor playbooks reliably by having a SessionStart hook instruct a first-action read, in daily use since June 2026.

## Decision

The SessionStart hook stops embedding core.md. It emits a short imperative instruction (well under 1,500 bytes) — *MANDATORY FIRST ACTION, before responding to the user and before any other tool call: Read `<plugin_root>/core.md` IN FULL* — plus a `systemMessage` so the human sees the hook fire. The full page is delivered by the model reading the file, so its size no longer bounds delivery. hooks.json's matcher is unchanged (`startup|clear|compact`, resume still excluded — context is not lost on resume), so the instruction re-fires and the page is re-read exactly when context was compacted or cleared.

Options considered:

- **Trim core.md back under the cap** (target ≤ ~9KB) — rejected by the human: "短了它不够用" — the page needs its length to state the full collaboration model inline for clean-context workers (the reason 0007's ceiling was raised to 5,000 tokens in the first place). Trimming would also partly reverse that decision's intent.
- **Split injection across multiple SessionStart hook registrations** — undocumented whether the cap is per-registration, untested, and fragile across harness updates. Fallback only.
- **Forced first-action read (chosen)** — size-independent, and a pattern already proven in daily use in the human's research project.

A CI byte gate is added alongside the unchanged token gate: total hook output must stay **< 4,000 bytes** (a wide margin under the ~10KB cap), so delivery can never silently regress to a preview again — the regression gate the byte cap itself never gave us.

## Consequences

Delivery is no longer byte-bound: core.md can grow to whatever the method needs without the harness quietly truncating it. The **5,000-token ceiling (0007 as amended) stays** — no longer as a delivery limit but as the context-cost governor, since the model still pays to read the whole page every session. The scheme now **relies on model compliance** rather than a guaranteed inline paste — the persisted-file fallback disappears, because the instruction *is* the delivery. Mitigations: the imperative is unmistakable (a ⭐ FIRST ACTION header, "before any other tool call"), the `systemMessage` makes the hook visible to the human when it fires, and the matcher re-fires the instruction on every compaction/clear so a re-read follows a context loss. The hook now also reads stdin to surface the `source` subtype in the `systemMessage` (pure sed, no new dependency); it never blocks on a terminal and bad or absent stdin degrades to no source. See 0007 for the one-page shape and budget history this amends.
