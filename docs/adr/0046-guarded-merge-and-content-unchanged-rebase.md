# 0046 — Guard the reviewed head and prove a content-unchanged rebase

Status: Accepted architecture (2026-09-05); implementation defaults pending human sign-off on #204. Amends 0011 and 0035 (rebase exception).

## Context

The approved collaboration architecture assigns mechanical enforcement to the merge transition.
Blanket full review after every base advance produces repeated reviews of disjoint, unchanged work.
The human's option-A ruling on issue #179 selects two hard layers: a conflict-free replay with
byte-identical PR-changed paths, then green CI on the merged result. Issue #204 implements those
interfaces; its human sign-off is still required before merge.

## Decision

The orchestrator enters through `scripts/guard merge`: current default base, latest whole verdict
for the exact head, protection, and CI bound to both base and head. Prior acceptance may be reused
only with its recorded old base/head and both rebase layers. Conflicts and changed path bytes or
modes refuse to full review. The API merge pins the verified head; strict protection supplies the
server's current-base check. Architecture-level merges also require recorded human authorization.

The guard consumes #203's attempt/ruling comment format. Seven returned reviews trigger the
orchestrator-first ruling; there is no eighth round, and a ruling cannot waive the Floor.

Role hooks reject recognized worker merge/release/external operations and require authorization
for recognized orchestrator irreversibles. Match lists and an expiring command/head-bound comment
are proposed configurable defaults, not a settled human ruling. Their authority is default-branch
policy, not worker files. The exact interfaces and limitations live in `reference/hard-edges.md`.

The alternative actually rejected by the approved option-A ruling is blanket re-review for every
rebase. This implementation does not claim an arbitrary-shell capability boundary: hook trust,
unsupported tool paths and shared credentials remain visible limitations. The main session runs
live executor probes; the worker's constructed tests cannot establish native enforcement.

## Consequences

Unchanged work can retain acceptance without ignoring integration changes. Tests can reproduce
both proof and refusal without moving the caller's branch. Missing evidence refuses conservatively.
Installing the plugin does not provision a target repository's CI or protection; the human/main
session owns that provisioning and this repository's final sign-off. The shipped protection script
is inspectable and runnable, and the worker's live negative probe uses an unprotected throwaway
branch without changing main's settings.
