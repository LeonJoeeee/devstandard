# 0013 — The ADR log survives parallel agents: dated amendments + merge-time numbering

Status: Accepted (2026-07-09)

## Context

Two holes in the ADR house rules (0000, `howto/adr.md`) surface once real parallel agents write ADRs.

1. **"Supersede, never edit; the only permitted change is a status flip"** cannot express the two states a live log actually reaches: a *partial* supersession (the core call stands, one detail was overtaken) and a *post-hoc factual note* (a referenced file was later deleted). Forced to choose, an author either leaves an accepted ADR misleading — the exact "a future session burns cost re-deriving why" failure ADRs exist to prevent — or wholly supersedes it, falsely signalling the core decision died. The project's own tree already broke the rule (0006 and 0010 carry appended notes); that is diagnostic, not sloppy — the rule lacked the expressiveness, so the author routed around it.
2. **Sequential numbering** ("four digits, never reused") collides silently under parallelism: two branches each allocate the same next `NNNN`; different kebab titles let git merge both with no conflict, and "never reused" breaks with nothing to alert anyone.

## Decision

1. **Dated amendments are legal.** An accepted ADR may carry an appended, clearly-marked block — `**Amendment (YYYY-MM-DD, see NNNN):** …` — that never rewrites the original text. It records a partial supersession or a factual correction while the body stays immutable. Full supersession (a new ADR + status flip) remains the tool when the *whole* decision is replaced. A third status, `Amended by NNNN`, may sit alongside `Accepted` and `Superseded by NNNN`.
2. **Final ADR numbers are assigned at merge — main's act.** In-flight branches draft as `docs/adr/DRAFT-kebab-title.md`; whoever integrates at main renames to the next free `NNNN`. Numbering is allocated by the single integration point, never by parallel branches — consistent with "merging is main's act."

## Consequences

The append-only property the rule actually protects is preserved (originals are never rewritten); agents get a legal path to correct the record; parallel ADR-writing stops colliding. This ADR's first use is its own introduction — 0000 receives an amendment note pointing here, and the pre-existing notes on 0006/0010 are reformatted into the sanctioned block. Bootstrap note: this ADR and its siblings (0011–0015) were authored in one change and numbered directly, not via the `DRAFT-` path they introduce — the merge-time-numbering rule binds subsequent parallel work, not the change that establishes it. Cost: one more status value and one naming convention in `howto/adr.md`.
