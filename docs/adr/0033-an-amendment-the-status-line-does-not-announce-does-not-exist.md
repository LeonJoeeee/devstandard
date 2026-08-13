# 0033 — An amendment the status line does not announce does not exist

Status: Accepted (2026-08-14). Amends 0013 (its amendment mechanism gains a correspondence rule;
the mechanism itself, and the supersede-never-edit rule under it, are unchanged).

## Context

0013 gave an amended ADR two status forms — `Amended by NNNN` and `Amended (date)` — and two block
forms — `**Amendment (date, see NNNN):**` and `**Amendment (date):**`. It never said which pairs
with which, or that a block must appear in the status line at all.

**Three sites drifted, and each was found by a person rather than by a check.** The worst is
`0019`: it has carried an amendment since 2026-07-24 that **no status entry announced**, in a
pre-convention blockquoted format. That amendment records the one thing a reader most needs — the
hook's emitted wording dropped its MANDATORY-FIRST-ACTION exclusivity claim for a composable form.
A session re-deriving the delivery rule reads `0019`'s Decision, sees no amendment marker, and
concludes the exclusivity claim still stands.

`reference/adr.md` already makes the consequence explicit: *"`ls docs/adr/` is the index; filenames
carry the summary."* The status line is the second half of that index. An amendment it does not
announce is one a future session does not find.

**Two of the three sites the audit reported did not survive re-checking, and that is part of the
argument.** `0008` was reported as missing `Amended by 0024`; its status line carries
`Amended by 0017 (2026-07-16), 0024 (2026-07-25)` — a comma-continuation the audit's eye skipped.
A mechanical check written for this ADR was itself wrong on the first run, reporting nine failures
because it did not handle the dateless `Amended by NNNN` form that twelve status lines use. **Three
hand audits and one checker all misread the same field**, which is the strongest available evidence
that this is not a rule people can hold by looking.

## Decision

**The two forms correspond, and every amendment block must appear in the status line.** A block
reading `(date, see NNNN)` pairs with `Amended by NNNN`; a block citing no ADR — a factual
correction, or the `caused by NNNN` form a change uses when it decided nothing *about* this ADR —
pairs with `Amended (date)`.

**This ships**, in `reference/adr.md`, at roughly 25 words. It earns them on cost rather than
frequency (0032's rule 1): a target project writes few ADRs and amends fewer, but the failure is
that a decision's correction becomes invisible, and the reader who misses it acts on the
superseded rule. That is the same failure class as a rewritten body, which this method already
treats as one of its two irreversible ones.

**This repository additionally enforces it as a CI gate.** The rule ships; the gate does not — a
target project checks it however it checks anything else, and `.github/workflows/ci.yml` is not
shipped. The gate is negative-tested: removing `0019`'s new status entry makes it fail, and the
failure names the file and the missing entry.

**Fixed here:** `0019` gains its status entry, and its blockquoted pre-convention block header is
normalised to the sanctioned form with a parenthetical saying so — its wording is otherwise
untouched. `0000`'s middle entry becomes `Amended by 0013 (2026-08-04)`, matching a block that
cites `0013 as amended`. `0008` was not a defect and is not touched.

Rejected: **(a) repo-ops only, like 0032's audit rules** — tempting for symmetry, but the evidence
here is not about maintaining *our* doc set. It is about a reader of *any* ADR log finding a
correction, and the rule is 25 words against a failure that silently teaches the wrong rule.
0032's rules are about proportioning our own prose; this one is about whether a record works.
**(b) A gate with no shipped rule** — the gate would hold this repo and every seeded project would
keep drifting, with nothing telling them why the two forms exist. **(c) Normalising `0019`'s block
by appending a new block that explains the old format** — strictly more faithful to immutability,
and rejected as ceremony: the header's punctuation carries no reasoning a future session
re-derives, and the parenthetical records the change in place.

## Consequences

The log's index is now checkable, and the check runs on every push rather than when someone thinks
to look. The four amendment sites this session added — 0025, 0026, 0013, and 0000's re-aimed entry
— all pass it.

**The cost is one more gate on a repo that has deliberately retired one before** (0028 removed the
en/zh mirror gate as a presence check wearing a correctness check's name). This one is not that: it
compares two representations of the same fact and fails only when they disagree, which is exactly
what a gate can do and an eye demonstrably cannot.

What to watch: **a new amendment form nobody teaches the gate about.** `caused by NNNN` was invented
during PR #114 and predates this gate by a day; the gate treats it as citation-free, which is right,
but the next such invention will either fail the gate loudly (good) or slip through a regex that was
never widened (the real risk). The rule in `reference/adr.md` is the authority; the gate is its
servant, and a disagreement between them is a bug in the gate.
