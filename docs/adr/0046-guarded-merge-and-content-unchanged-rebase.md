# 0046 — Guard the reviewed head and prove a content-unchanged rebase

Status: Accepted (2026-09-05). Amends 0011 and 0035 (rebase exception). Amended (2026-09-07).

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

**Amendment (2026-09-07, issues #242 and #256):** the Decision's "changed path bytes or modes refuse
to full review" has one exemption, added after the human's ruling that the version bump rides the
change PR. The two Claude manifest version lines read as no difference when both move in lockstep to
the same value. Where that exemption is what admits the comparison, the guard additionally requires
the new head to declare a bump against the reviewed head, and that value — read as a dotted numeric
release — to sort above both the reviewed head's and the replay's, so a lane cannot rebase past a
merged bump and then set the manifests back. Every other path still refuses.
`reference/hard-edges.md` carries the operative wording; the admitted pair rides the proof as
`version_bump`.

**Amendment (2026-09-07, issue #274):** the Decision's "Conflicts and changed path bytes or modes
refuse to full review" carries that exemption on its conflict clause too. The replay is what feeds
the comparison, so when the reviewed head and the new base bump from one base to different versions
git cannot auto-merge the two version lines; refusing there sent a rebase that moved only those
lines back to a full review round (PR #271). A replay conflict confined to the two manifest version
lines is now resolved to the new base's value and the replay continues, leaving every check above
to run unchanged — including the ordering check, which still measures the new head against the
version the new base merged. A conflict on any other path, or on any other line of either manifest,
still refuses to full review. `reference/hard-edges.md` carries the operative wording.

**Amendment (2026-09-07, issue #279):** the status line above read *"Accepted architecture
(2026-09-05); implementation defaults pending human sign-off on #204"* — a value outside the three
`reference/adr.md` admits, carrying a precondition that has since been met. It now reads `Accepted
(2026-09-05)`, and this block records what the retired half of it said. **The sign-off was given.**
The human approved the architecture-level change on 2026-09-06 and delegated the three proposed
defaults to the main session, which decided them as recorded on PR #223
(https://github.com/LeonJoeeee/devstandard/pull/223#issuecomment-5557327712); #204's implementation
merged as `0c82b76`. So the Decision's *"Match lists and an expiring command/head-bound comment are
proposed configurable defaults, not a settled human ruling"* is settled: the documented synonym match
set extended additively by default-branch policy, the whole `devstandard-authorization-v1` comment
form bound to repository, head, kind, command digest and expiry with `standing_release` filled from
the 2026-07-24 delegation, and the repository-scoped Codex role-hook trust bypass all ship in
`.github/devstandard-guards.json`. Their authority is still default-branch policy, never worker
files. Nothing in the architecture this ADR decided changes, and its stated limitations stand: hook
trust, unsupported tool paths and shared credentials remain visible limits, and no complete
capability-boundary claim is made. `reference/hard-edges.md` carries the operative wording.

**Amendment (2026-09-07, issue #293):** the Decision's *"Role hooks … require
authorization for recognized orchestrator irreversibles"* has one exception, and it is the only one.
A repository being founded has no policy file on its default branch, so it has no
`authorization_issue`, so no record can exist — and the push that would land that file is itself a
recognized irreversible. Read literally the sentence made a project seeded from these pages
permanently unable to become guarded: it could never take its first step. The guard therefore admits
an **orchestrator's** plain `git push` whose every destination is the default branch, and only while
that branch provably carries neither a policy file nor protection. Both conditions are the argument:
with no policy there is nothing to bypass, and with no protection there is nothing to replace; the
push that lands the policy file closes the door behind itself. Absence must be proven — an explicit
404, including a default branch with no commits — and any other read failure still refuses.
`--force`, `--delete`, `--mirror`, `--tags`, a wildcard refspec, another destination, another
command, and every other role keep their refusal. Applying protection is deliberately *not* in the
exception: by then the policy file exists, so the ordinary record is available and is what a new
project's human authorizes first. The Consequences' *"the human/main session owns that
provisioning"* is unchanged. `reference/hard-edges.md` carries the operative wording, under
*Founding a repository*.

**Amendment (2026-09-07, issue #293):** the Decision's *"CI bound to both base and
head"* names a check whose spelling is now a target's to choose. The guard reads the required
contexts from `required_checks` and the integration check's name from `merged_result_check`,
defaulting to `merged-result / {base} / {head}`; a name that drops either pin refuses, so renaming
can never unbind the check from the exact merge result. `reference/ci-pipelines.md`'s CI template
ships the job that reports it, which it did not before — the guard required a check no seeded
project produced.
