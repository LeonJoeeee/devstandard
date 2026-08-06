# Working on DevStandard itself

This file is **repo ops for this repository only**. It does not ship: nothing in `core.md`,
`howto/` or `aids/` points at it, and no seeded project receives it. Everything here is a
practice we follow *while building DevStandard*, not a rule DevStandard states.

**The line that decides what belongs here:** a method DevStandard *ships* goes in the shipped
pages; a practice useful only for maintaining *this* project goes here. When the two get
confused, repo-ops material ends up on a page every project pays to read every session — which
is what happened to the rule below (ADR 0030).

## Rewording a rule: search twice

Our product is prose, so nothing mechanical catches a stale statement. Rename a function and
the compiler finds every caller; reword a rule and **nothing responds**. Six recorded instances
(issue #79), plus several more during the 0028/0029 work.

When you change the wording of a rule that exists in more than one place, **search twice**:

1. **Every other statement of the clause** — the aids, the howtos, `docs/architecture.md`, and
   the ADR that recorded it.
2. **Every site that cites or paraphrases it**, found by *its pointer to the rule* — the file
   it names, the rule's subject — and **never by the words you just added.** This is the half
   that matters and the half that keeps being skipped: searching for the word you added finds
   every site that already has it, and by construction cannot find the sites that should now
   carry it.

Reconcile each in the same diff, or say in the PR description why it needs none — a site simply
absent from the sweep is a silent omission, not a clearing.

Two sites take a specific form:

- **An ADR** is reconciled by appending a dated `**Amendment (YYYY-MM-DD, see NNNN):**` block,
  never by a rewritten body (`howto/adr.md`). And the distinction that decides whether it needs
  one at all: an ADR body saying *what was true when the decision was made* is history and is
  never reconciled; one saying *what a future action will cost* is a live instruction and is.
- **A historical record** — a merged PR description, a released tag's notes — is not a site.

## The release delegation

`core.md:87` says releasing is the human's call. **For this repo that call was delegated
standing on 2026-07-24** (issue #37): since v0.9.3 the agent releases right after each merge —
bump both manifests in lockstep, tag, push — without asking per release. The goal was that every
merged improvement reaches the human's other sessions as fast as possible.

Withdrawing it is the human's to do. **Target projects are unaffected:** there, release go/no-go
stays on the human's ask-axes and `howto/cicd.md`'s tag-triggered default governs.

## ADRs in this repo

`docs/adr/` ships inside the plugin package (the human's ruling on issue #93: we are the only
installer today, and the log is more useful one directory away than absent). Consequence:
**an ADR that decides how we operate, rather than what the method says, must say so in its own
title and text** — otherwise a reader in a seeded project takes it for an instruction. ADR 0028
is the model; 0029 needed three review rounds to learn it.
