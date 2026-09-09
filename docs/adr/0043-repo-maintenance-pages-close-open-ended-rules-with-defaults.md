# 0043 — Repo-maintenance only: pages close open-ended rules with defaults

Status: Accepted (2026-08-31). Amends 0032 (adds the third rule for maintaining this repository's
own pages). Amended (2026-09-10).

**This ADR decides how the DevStandard repository is maintained, not what the shipped method says.**
The log ships inside the plugin package, so this scope is explicit: a seeded-project reader must not
treat the decision as project guidance.

## Context

Issue #168 produced three taxonomies for an open-ended set. Each review round found another case,
and each repair added another rule until the human directed the design toward common cases plus a
default. The same pattern appears in earlier multi-round changes. The repository's two existing page
audit rules in ADR 0032 price a statement and keep it single-sited, but do not tell an author when an
enumeration itself is the defect.

## Decision

Add a third repository-maintenance audit rule. Its trigger is repeated review finding a new case the
page does not decide and answering with another rule; at that point the author tests whether a common
default can close the open-ended subject. The operative wording, including its closed-contract,
stale-site, and safety-regression boundaries, lives beside rules 1 and 2 in this repository's root
`CLAUDE.md`. It is not restated here, so the immutable ADR cannot become a second live copy.

This rule governs new authoring. Existing pages are not swept as part of this decision; issue #172
owns that separate review. Issue #173 records the review-side counterpart and its evidence.

## Consequences

Authors get a stop signal before an open-ended inventory grows by another case, while rule 1 still
protects target-project correctness and rule 2 still requires stale sites to be reconciled. Safety
findings cannot be dismissed as enumeration churn. The maintenance rule remains single-sited in
`CLAUDE.md`, where repo-only practice belongs under ADR 0030.

**Amendment (2026-09-10, issue #313):** the Decision's *"Issue #173 records the review-side
counterpart and its evidence"* is corrected as a pointer. #173 stays the evidence record, but its
third consequence — the reviewer is told the list is deliberately incomplete, and an uncovered case
is a finding only where the default routes it somewhere harmful — is no longer recorded only there:
`reference/code-review-prompt.md` now states it operatively under the Goal verdict, beside the stop
signal a reviewer reports when a round's findings repeat the previous round's shape, and
`reference/orchestrator.md` states how to write an open-set goal so the reviewer can judge it. This
ADR's own scope is unchanged — it still decides only how this repository's pages are authored, and
rule 3's operative wording still lives in `CLAUDE.md`.
