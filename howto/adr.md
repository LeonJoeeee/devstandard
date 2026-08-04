# How to write ADRs

Read this at project start (to seed the log) and whenever a significant decision lands. An ADR records **one decision and its why**, dated, one page — so no future session burns cost re-deriving "why was it done this way".

## When to write one (and when not)

Two axes — either one fires:
- the decision **touches top-level design** (structure, interfaces, dependencies, a key quality goal), or
- it is **costly to reverse**.

Skip: trivial single-person choices, temporary workarounds/spikes, anything already covered by an existing ADR or the architecture doc. Litmus test: *would a future session burn real cost re-deriving why this was chosen?* No → no ADR.

Admission test when unsure: a decision earns an ADR only if its **cost of change is high** — it touches fundamental structures, or its effects scatter across the codebase instead of staying local to one component. A log that records everything protects nothing: if every decision is architectural, no decision is architectural.

ADRs are the natural by-product of asking the human: when a change gets the human's approval because it touches top-level design, that approval gets an ADR in the same merge.

## Mechanics

- Files: `docs/adr/NNNN-kebab-title.md` — four digits, sequential, zero-padded, never reused. Seed the log at project start with `0000-record-architecture-decisions.md` (the ADR saying this project uses ADRs, containing the trigger rules above).
- **The number is claimed when the ADR is written — and only after verifying it is free.** Verifying is the writer's duty, and it has three places to look, because a number can already be claimed by work that has not merged:
  - the merged log — `ls docs/adr/` on current `main`;
  - every remote branch — `git fetch --all && git log --all --diff-filter=A --name-only -- 'docs/adr/*' | sort -u`;
  - every open PR — `gh pr list --state open`, then `gh pr diff <n> --name-only` on any that touches `docs/adr/`.

  Take the lowest number free in all three, and **record the check in the PR description** — which number, checked against what — so check 1 can see it rather than take it on trust. Claimed counts as taken before it merges; a gap left by an abandoned branch is fine, since the numbers order the log and don't have to be dense. This replaces the merge-time `DRAFT-kebab-title.md` rename (0013 as amended): verify-then-claim gives the same collision safety at the moment the writer already has the tree open, and unlike the rename it is a step someone actually performs.
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
