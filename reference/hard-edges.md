# Guarded operations

The installed plugin's `scripts/guard` is the orchestrator's merge entry point. Workers never
merge, release, or apply protection. Python 3.9+, git 2.38+, and authenticated `gh` are required;
the test suite also uses Python 3.11+'s TOML parser. The match and authorization defaults below
are proposed under #204 and need the human's ruling before that architecture-level PR merges.

## Merge and rebase proof

Fetch current objects, then run the read-only check; add `--execute` only as the orchestrator:

```sh
<plugin>/scripts/guard merge --repo OWNER/REPO --pr NUMBER --project CHECKOUT
```

It requires an open PR into the repository's current default branch, that base as an ancestor of
the PR head, the configured protection, and the latest whole Goal Yes / both Floor Pass verdict
for that exact head. Only `record_logins` may publish the operative records (default: repository
owner). This is a publishing-identity check, not proof that a shared account's operator is human.
The API merge uses a head-SHA precondition and GitHub's strict protection; a changed base or PR
during verification refuses. Keep one orchestrator per PR. Protection and current-source review
remain necessary because credentials and workflow files are not made immutable by this script.

The PR description must carry `architecture-level: true|false`, or its #203 review record must
carry `architecture: YES|NO`. Either true flag requires a head-bound human authorization with
kind `architecture` and command text `merge OWNER/REPO#NUMBER`. Classification still requires
judgment; a false declaration is a Floor failure, not something the matcher can discover.

After main moves, add `--old-base FULL_SHA --old-head FULL_SHA`. The latest accepted #203 record
must name both old pins. The guard replays the old commits in a disposable clone with rerere and
hooks disabled, refuses conflicts and merge commits, compares every path changed in either PR
diff (including deletions, mode and symlink identity), and requires the replay tree to equal the
new head tree. Submodules refuse for full review. The caller's refs, index and worktree do not move.
The mechanical half can also be inspected independently:

```sh
<plugin>/scripts/guard compare --project CHECKOUT --old-base OLD_BASE --old-head OLD_HEAD --base NEW_BASE --head NEW_HEAD
```

The second layer requires the configured checks and `merged-result / BASE_SHA / HEAD_SHA` on the
PR head. The shipped CI checks out GitHub's PR merge ref, verifies both parents against the event,
runs the tests, then reports that identity only after success. A target project must carry the
same binding around its own test job; installing the plugin does not install a target's CI.
A missing, red or pending identity refuses. Any failed rebase layer returns to full review,
with a resolver for conflicts. This CLI conservatively requires full review for an amended head
or quoted-Note edit; it does not mechanically implement the older quoted-fix exception.

## Review rounds and dispatch

#203's `devstandard-review-v1` PR comments are the durable attempt/ruling records. The guard reads
them; it does not publish a second round ledger. Returned verdicts, including Floor failures,
consume rounds. At **7**, the orchestrator rules first; no eighth review or goal-fix continuation
is admitted. `merge-as-is` can settle Goal No but never waive either Floor. An active attempt,
missing/duplicate rounds, or a ruling for a different reviewed head refuses. A continuation needs
an explicit `continue` ruling; Floor check 2 stops and escalates. Architecture sign-off still
applies to a merge-as-is ruling. `scripts/guard round --repo OWNER/REPO --pr NUMBER` checks admission.

`scripts/dispatch` gates delivered worker continuations on that history. #203 owns review-attempt
reservation and review dispatch; use its assembler for a review, not a direct low-level dispatch
that omits round accounting. New worker lanes also require green default-branch CI before any
lane creation/publication. Recovery in an existing lane remains possible while main is red.

## Role hooks and configurable authorization

Claude workers expose Read/Glob/Grep/Bash/Edit/Write/Skill; reviewers expose only Read/Glob/Grep.
The worker definition pins a worker PreToolUse hook. The global hook recognizes native worker
and reviewer agent types. Codex dispatch pins the role in an inline hook configuration, keeps
workers workspace-write and reviewers read-only, and grants worker network access for git/gh.
`guard codex-config --role worker|reviewer` prints the exact TOML override for inspecting or
trusting that hook. The dispatcher neither changes persisted hook trust nor bypasses it.

**Live executor refusal is not yet verified by #204's worker.** The main session must run and
publish the PR's live probes before check 1. Codex non-managed hooks need review/trust through
`/hooks` for the exact definition; skipped/untrusted hooks are not passing probes. Managed-hook
policy can also exclude session hooks. See the [Codex hook contract](https://developers.openai.com/codex/hooks)
and [Claude hook contract](https://code.claude.com/docs/en/hooks).

These are guards for recognized operations, **not a credential or arbitrary-program boundary**.
Shell scripts, aliases, encoded commands, interactive stdin, alternative HTTP clients, shared git
metadata and unsupported/hosted tool paths can escape this spelling matcher. Native tool cuts and
OS sandboxes still apply, but do not establish zero unauthorized irreversible actions. Do not
advertise the matcher as that boundary. The main session owns the live-probe findings and the
human owns any stronger enforcement design.

Policy comes only from `.github/devstandard-guards.json` at the target's remote default-branch
SHA. An unmerged worker edit cannot authorize itself. Absent policy means built-in matchers,
required `test`, owner record publisher, no human authorizers and no standing release grant.
Malformed/unreadable policy or authorization fails closed. The proposed settings are:

- `command_patterns`: per-kind regex lists over normalized simple argv segments. Defaults cover
  merge CLI, tag/release/package publication, forced/default-branch pushes, recursive/forced
  deletion and common external delete/API-write commands. Git/gh global options and ordinary
  wrappers/chains are recognized; quoted prose arguments are not executed commands. A provided
  kind replaces that kind's defaults for orchestrator policy; omitted kinds retain defaults.
  Worker role cuts retain the built-in denied spellings. `--force-with-lease` on a task branch
  remains ordinary worker work; this does not authorize a shared-branch rewrite.
- `authorization_issue` and `human_logins`: an allowlisted human posts the following JSON as the
  **whole comment**, prefixed by `<!-- devstandard-authorization-v1 -->` and a newline. The latest
  matching record decides; `revoked: true`, expiry, a wrong head, command digest or actor refuses.
- `standing_release`: null by default. A human may set `{ "repo": "OWNER/REPO", "source":
  "https://github.com/OWNER/REPO/issues/NUMBER#issuecomment-ID" }` to relay an existing standing
  delegation. It covers recognized release commands only, not major-version tags, architecture
  approval or an irreversible command appended to a release. Major tags use `major-release`
  one-shot authorization. Revocation removes the setting on the default branch.

```json
{"repo":"OWNER/REPO","head":"FULL_HEAD_SHA","kind":"irreversible","command_sha256":"SHA256_OF_EXACT_COMMAND_TEXT","expires":"2026-09-06T00:00:00+00:00","revoked":false}
```

The hook permits a recognized orchestrator operation only after this lookup, or permits the exact
installed `guard merge` entry point to perform its own verification. It never turns an authorization
record into worker merge/release permission. Expiry is mandatory; a record is reusable for its exact
head/command until expiration or revocation, not an atomic single-use capability. Humans should use
a distinct publishing identity where agents share the repository owner's account.

## Branch protection

Read-only expected-state check, usable on any branch:

```sh
<plugin>/scripts/guard protection --repo OWNER/REPO --branch main
```

Human/main session only: append `--apply` to run the documented `gh api --method PUT` payload in
`scripts/guard`, then read it back. Defaults require `test` (repeat `--check` to name a target's
checks), strict up-to-date status checks, admin enforcement, no force pushes and no deletions.
The payload sets no review-count or actor restriction; inspect existing extra protection before
using this provisioning command because PUT replaces those fields. Workers never run it.
Classic status protection alone does not prohibit a credential holder from pushing a pre-green
commit directly: PR-only behavior also depends on the role/merge route. It is not a server-side
verification of a Goal/Floor comment. Never weaken protection to manufacture a negative probe.

#204's live negative fixture is `probe/204-unprotected`, created and deleted with `gh` by the worker
under the main session's recorded ruling. Its check refused with HTTP 404 while main's check passed.
Unit probes cover both API shapes. Evidence, commands and exit codes belong on the PR; live executor
probes and whole check 1 belong to the main session under the continuation ruling.
