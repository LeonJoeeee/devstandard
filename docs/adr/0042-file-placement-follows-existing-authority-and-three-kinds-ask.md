# 0042 — File placement follows existing authority, and three expensive kinds ask

Status: Accepted (2026-08-31). Amends 0007 (which router it refuses), 0012 (durable progress and
commit-or-remove), 0018 (declared roots relay authority), 0037 (external placement and disclosure),
and 0041 (handback qualification for committed and ignored paths).

## Context

ADR 0037 prevented an agent from inventing a destination outside its repository, but its rule began
only after a write had already been classified as external. It therefore answered every undeclared
destination with an ask and left no ordinary default for generated results, reports, or files used
only by the task. Items 1–10 of issue #168 separately admitted in-repo documents and made worktree
handback deliberate; placement still needed one entry point spanning both sides.

Three attempts tried to classify the open-ended set. An ordered list let a catch-all pre-empt a
specific row; two questions without precedence overlapped; binding roles failed when one file was
both a release and a secret. Challenge rounds 22–62 followed the human's 2026-08-29 direction to
abandon those taxonomies. No new case demanded a new rule after round 27, and round 62 returned zero
blocking findings. The evidence supports a closing default, not another taxonomy.

## Decision

The operative placement wording lives only in `reference/where-it-goes.md`. It closes the ordinary
case with a project-local default and reserves asks for the three cases where a wrong default is
expensive: secret or confidential data, application state for a program that outlives the task, and
a release deliverable. The page also owns retention and disclosure at worktree teardown;
`reference/out-of-repo-writes.md` retains the detailed requirements for those three external kinds.

`core.md` carries only the resident trigger, default, ask-kinds, and pointer. After the required cuts
and insertion, the repository's 1.35× word proxy leaves three tokens of headroom below the 5,000-token
ceiling. That distance is deliberately recorded here rather than repeated on a live page: the tight
fit is the reason the operative reasoning and examples remain on demand.

The entry point is not the always-on request/skill dispatcher rejected by ADR 0007. It applies one
placement rule after the work has a file to write; it does not classify requests to select rules.

## Consequences

Ordinary task output no longer forces an ask or an invented external directory, while the security,
state-loss, and release risks still stop. Same-change documents cannot authorise their own
destinations, a disposable worktree is not durable storage, and generated output does not become
repository material merely because it was committed. Existing placement and handback statements are
reconciled by the dated amendments this ADR announces; the full rule remains single-sited.
