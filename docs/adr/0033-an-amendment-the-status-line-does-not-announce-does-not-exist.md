# 0033 — An amendment the status line does not announce does not exist

Status: Accepted (2026-08-13). Amends 0013 (its amendment mechanism gains a correspondence rule;
the mechanism itself, and the supersede-never-edit rule under it, are unchanged).

## Context

0013 gave an amended ADR **one** block form — `**Amendment (YYYY-MM-DD, see NNNN):**` — and **one**
new status, `Amended by NNNN`. The citation-free status `Amended (date)` arrived in the same commit
but in `howto/adr.md`, not in the ADR; the citation-free *block* form was written down **nowhere**,
in either. So the correspondence was never stated because half the pairing was never stated at all.

**Two sites drifted, and both were found by a person rather than by a check.** The worst is
`0019`: it has carried an amendment since 2026-07-24 that **no status entry announced**, in a
pre-convention blockquoted format. That amendment records the one thing a reader most needs — the
hook's emitted wording dropped its MANDATORY-FIRST-ACTION exclusivity claim for a composable form.
A session re-deriving the delivery rule reads `0019`'s Decision, sees no amendment marker, and
concludes the exclusivity claim still stands.

`reference/adr.md` already makes the consequence explicit: *"`ls docs/adr/` is the index; filenames
carry the summary."* The status line is the second half of that index. An amendment it does not
announce is one a future session does not find.

**One of the three sites the audit reported was not a defect at all, and that is part of the
argument.** `0008` was reported as missing `Amended by 0024`; its status line carries
`Amended by 0017 (2026-07-16), 0024 (2026-07-25)` — a comma-continuation the audit's eye skipped.
A mechanical check written for this ADR was itself wrong on the first run, reporting nine failures
because it did not handle the dateless `Amended by NNNN` form, which much of the log uses. **Three
hand audits and one checker all misread the same field**, which is the strongest available evidence
that this is not a rule people can hold by looking.

## Decision

**The two forms correspond, and every amendment block must appear in the status line.** A block
reading `(date, see NNNN)` pairs with `Amended by NNNN`. **Every other citation pairs with
`Amended (date)`** — a commit, an issue, a PR, and also `caused by NNNN`, which names the change
that *forced* an edit rather than an ADR that decided something about this one. The earlier draft
of this sentence said "a block citing no ADR", which is a contradiction in terms for `caused by`
and would have put the shipped rule and the gate in direct disagreement — check 1 caught it.

**This ships**, in `reference/adr.md`: the rule bullet is **53 words** (excluding the list marker),
and the page gains **72** in all, because two neighbouring bullets had to move with it. The Supersede
bullet showed only the `see NNNN` block shape, so the rule's second half governed a form the page
never displayed — and this repo has twelve merged blocks written in it. The Statuses bullet defined
that form as "cites only a commit — no ADR", which is false of `caused by NNNN` and would have sent
a reader to the wrong status. Both figures measured at this commit, by `wc -w` on the file. It earns them on cost rather than
frequency (0032's rule 1): a target project writes few ADRs and amends fewer, but the failure is
that a decision's correction becomes invisible, and the reader who misses it acts on the
superseded rule. That is the same failure class as a rewritten body, which this method already
treats as one of its two irreversible ones.

**This repository additionally enforces it as a CI gate.** The rule ships; the gate does not — a
target project checks it however it checks anything else, and `.github/workflows/ci.yml` is not
shipped. The gate is tested against the past, not against a
synthetic break: run at `7590a6c` it names both real defects; run at head it is silent.

**Fixed here, and every fix is a status line — no ADR body is edited.** `0019` gains its status
entry; its pre-convention blockquoted header stays exactly as written. `0000`'s middle entry becomes
`Amended by 0013 (2026-08-04)`, matching a block that cites `0013 as amended`. `0008` was not a
defect and is not touched.

**The gate therefore checks announcement, not header style.** It parses the legacy shape rather than
rejecting it, because rejecting it would demand editing an already-merged block — and
`reference/code-review-prompt.md` ships *"a rewritten ADR body is Critical"* with no carve-out. The
sanctioned form is a rule for blocks written from now on; the gate deliberately does not police it,
since the only enforcement available would breach a stronger rule.

Rejected: **(a) repo-ops only, like 0032's audit rules** — tempting for symmetry, but the evidence
here is not about maintaining *our* doc set. It is about a reader of *any* ADR log finding a
correction, and the rule is 53 words against a failure that silently teaches the wrong rule. The strongest
support for shipping it was already in the tree and this ADR nearly missed it:
`reference/code-review-prompt.md` has been telling every check-1 reviewer, in every seeded project,
to verify "an appended dated amendment block **plus its status line**" — pointing at a page that
never stated the rule. That is 0032's rule 2 exactly: a resident trigger with no authority behind it.
0032's rules are about proportioning our own prose; this one is about whether a record works.
**(b) A gate with no shipped rule** — the gate would hold this repo and every seeded project would
keep drifting, with nothing telling them why the two forms exist. **(c) Normalising `0019`'s
pre-convention header in place** — the first draft of this change did exactly that, and check 1
refused it: the objection is not that appending is tidier, it is that `reference/code-review-prompt.md`
ships an absolute rule and an in-place edit gives it an unwritten exception. Teaching the gate the
old shape costs four lines and breaches nothing.

## Consequences

The log's index is now checkable, and the check runs on every push rather than when someone thinks
to look. **The test that matters is that it fails on the past:** run against `7590a6c`, the commit
before this change, it names `0000`'s 2026-08-04 block and `0019`'s unannounced one — the two real
defects, found by hand over two sessions. A gate that is green on the incident that motivated it is
worse than none, and the first draft of this one was exactly that.

**The cost is one more gate on a repo that has deliberately retired one before** (0028 removed the
en/zh mirror gate as a presence check wearing a correctness check's name). This one is not that: it
compares two representations of the same fact and fails only when they disagree, which is exactly
what a gate can do and an eye demonstrably cannot.

What to watch: **a new amendment form nobody teaches the gate about.** `caused by NNNN` was invented
during PR #114, the same day as this gate; the gate pairs it with `Amended (date)`, which is right,
but the next such invention will either fail the gate loudly (good) or slip through a regex that was
never widened (the real risk). The rule in `reference/adr.md` is the authority; the gate is its
servant, and a disagreement between them is a bug in the gate.

**Three gaps in the gate, all latent today, recorded rather than coded around** — closing any of them
means re-reviewing the checker, and none has a live instance in the 34 ADRs:

- The rule draws its line **semantically** (an ADR that merely *caused* the change) while the gate
  keys on the literal marker `see`. Someone who writes `see 0031` meaning "caused by" is asked for
  the wrong status form. The marker word is what decides; the rule should say so if this ever bites.
- **The dateless `Amended by NNNN` form re-opens set membership** — the very hole that made the first
  draft green at base. Two blocks citing the same ADR are both satisfied by one dateless entry. This
  is inherent to that form being legal and in wide use, not fixable in the checker.
- A sanctioned header **at the start of a line inside a fenced code block**, written with a real date
  rather than `YYYY-MM-DD`, is read as a real amendment. This repo writes ADRs *about* ADR
  conventions, so this is the one most likely to fire.
