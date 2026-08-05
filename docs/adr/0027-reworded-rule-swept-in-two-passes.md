# 0027 — A reworded rule is swept for twice: its other statements, and the sites that cite it

Status: Accepted (2026-08-04). Amended by 0028. Amends 0022 (the doc-duty bullet only —
it gains a second, differently-searched pass; 0022's universal-ceremony core, the issue
rule and the revert carve-out stand).

## Context

0022 made the doer's doc duty universal: whoever changes anything updates the docs that
change invalidates, in the same diff. This repo's own history shows the rule is read
narrowly — and correctly, on its wording — as *documents this change made false*, and that
a whole class of staleness sits outside that reading.

The observed pattern: a review finding says file A and file B disagree. The fix reconciles
A and B. A third file C — which quoted, pointed at, or restated the same clause — is left
stating the old version. The next review finds C; fixing C stales D. Six are counted on
issue #79 and five described there, four of them inside a single PR, each found by a
different party.
The fixer is never careless: every one of those fixes was verified in place. "In place" is
the defect — it means the two files in hand, and nothing tells the fixer to look further.

The sixth instance shows why one search is not enough. A wording widened in `core.md` from
"any rebase" to "any rebase or amend" left `howto/cicd.md` telling every seeded project to
re-run check 1 "after any rebase" — text that was not in the diff, was not false, and had
just become incomplete. The implementer and the round-1 reviewer both swept, and both swept
for the *word* they had added. That search finds every site that already says "amend" and,
by construction, cannot find the sites that should now say it. The stale site was reachable
only by searching for what *cites* the rule — a `(core.md)` pointer beside "check 1" — never
for what the rule now says.

The ADR is the member of the set most often missed and the most expensive to leave stale:
it is what a future session re-derives the rule from, so a stale ADR does not merely
disagree with the page — it teaches the next writer the old rule.

## Decision

Rewording a rule is its own doc duty, discharged in the same diff, in two passes that are
searched differently:

1. **Every other statement of the clause** — the translated mirror, the aids, the howtos,
   the architecture doc, and the ADR that recorded it.
2. **Every site that cites or paraphrases the rule**, checked against its new scope — found
   by its *pointer* to the rule (the file it names, the rule's subject), never by the words
   just added. Widening a rule silently narrows every summary of it, and a summary that
   needs the new words is precisely a site that does not yet contain them.

Each site is reconciled **or explicitly cleared** — a clearing is a ruling ("this is a
historical record; it says what was true then"), reported where the change is reported. A
site simply absent from the sweep is a silent omission, not a clearing.

Two kinds of site take a specific form, because "reconcile" otherwise reads as "edit":
an **ADR** is reconciled by appending a dated amendment block, never by a rewritten body —
the append-only record is the property the whole log exists to hold — and a **historical
record** (a CHANGELOG entry, a merged PR description) is not a site at all: it states what
was true at that release, and correcting it would falsify the history rather than the rule.

Where it lands, and why in three places: core.md's doc-duty paragraph, because the duty is
universal and a main session doing its own short-branch fix reads no aid; a step in
`aids/worker-brief.md`'s findings section, because a worker fixing a check-1 finding is the
commonest rewriter and never receives core.md; and a check item in
`aids/code-review-prompt.md`, because the reviewer caught most of the recorded instances —
the backstop stays a backstop, but is now told what to look for.

Rejected: (a) the reviewer prompt alone — cheapest, and it is where the catches actually
happened, but it makes the method rely on catching rather than doing, and each catch costs
a whole fix-and-re-review round; (b) a mechanical gate (CI greps the doc set for a reworded
clause) — there is no machine-checkable definition of "the same rule stated differently",
and the one gate this repo *can* enforce mechanically, the en/zh mirror, is already in place
and caught none of the six; (c) folding it into the existing doc-duty sentence as "and any
doc that quotes it" — it reads as the same search, which is the misreading that produced the
six instances; the two passes have to be visibly two.

## Consequences

Every wording change now costs two searches before it can be pushed, which is the intended
price: most of the recorded instances cost a full review-fix-re-review round instead, and
the one that did not was caught only because its brief said *verify, do not assume*.
core.md pays 180 tokens (total 4,560 of 5,000); `aids/worker-brief.md` and
`aids/code-review-prompt.md` are read on demand, so their share is free at session start.
The rule is self-applying, and this diff applies it to itself: it fixes the sixth instance
(`howto/cicd.md`'s "after any rebase") as its own demonstration case, and reconciles rather
than clears core.md's two other statements of the doc duty — the flow-at-a-glance step and
the worker DO list — with a short pointer each, on the precedent 0026 set when it corrected
the flow-at-a-glance step in place because it is what an agent skims. What to watch:
whether "explicitly clear" decays into a formality, since a clearing with no ruling is the
failure shape it was meant to prevent; and whether pass 2 ever fires in practice, because a
pass nobody's search finds anything in is a pass nobody is really running.

**Amendment (2026-08-05, see 0028):** two claims above are overtaken for **this repo only**.
The pass-1 site list still names "the translated mirror" — correct for any project that keeps
one, and this plugin no longer does (0028), so that member is simply empty here. And Rejected
(b) argued that "the one gate this repo *can* enforce mechanically, the en/zh mirror, is
already in place and caught none of the six" — that gate is retired, which strengthens rather
than weakens the argument it was making: the only mechanical check available was one that
compared file *presence*, never content, and it never could have caught the defect this ADR
exists to close. The two-pass rule itself is unchanged.
