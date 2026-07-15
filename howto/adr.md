# How to write ADRs

Read this at project start (to seed the log) and whenever a significant decision lands. An ADR records **one decision and its why**, dated, one page — so no future session burns cost re-deriving "why was it done this way".

## When to write one (and when not)

Two axes — either one fires:
- the decision **touches top-level design** (structure, interfaces, dependencies, a key quality goal), or
- it is **costly to reverse**.

Skip: trivial single-person choices, temporary workarounds/spikes, anything already covered by an existing ADR or the architecture doc. Litmus test: *would a future session burn real cost re-deriving why this was chosen?* No → no ADR.

ADRs are the natural by-product of asking the human: when a change gets the human's approval because it touches top-level design, that approval gets an ADR in the same merge.

## Mechanics

- Files: `docs/adr/NNNN-kebab-title.md` — four digits, sequential, zero-padded, never reused. Seed the log at project start with `0000-record-architecture-decisions.md` (the ADR saying this project uses ADRs, containing the trigger rules above). **Numbers are assigned at merge (main's act):** in-flight branches draft as `docs/adr/DRAFT-kebab-title.md`; whoever integrates renames to the next free `NNNN`. This stops two parallel branches from silently claiming the same number (0013).
- **Supersede, never edit — but dated amendments are legal.** A changed decision = a NEW ADR stating "Supersedes NNNN"; the old one's status flips to "Superseded by MMMM". Original text is never rewritten. For a *partial* supersession (the core call stands, one detail was overtaken) or a *factual correction*, append a dated block instead — `**Amendment (YYYY-MM-DD, see NNNN):** …` — leaving the body immutable (0013).
- Statuses: `Accepted`, `Superseded by NNNN`, and `Amended by NNNN` (which sits alongside Accepted). A factual correction that cites only a commit — no ADR — carries `Amended (date)` without a number.
- One decision per file — separate files keep parallel sessions conflict-free and let agents read only what's relevant (`ls docs/adr/` is the index; filenames carry the summary).

## Template

```markdown
# NNNN — <decision in one line>

Status: Accepted (<date>)

## Context
<the situation and forces; what made this a real decision>

## Decision
<what was decided, concretely. If real alternatives existed,
one line each on what was rejected and why>

## Consequences
<what gets better, what it costs, what to watch>
```

Lands in the target repo under `docs/adr/`.
