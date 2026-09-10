# Guarded operations

The installed plugin's `scripts/guard` is the orchestrator's merge entry point. Workers never
merge, release, or apply protection. Python 3.9+, git 2.38+, and authenticated `gh` are required;
the test suite also uses Python 3.11+'s TOML parser. The role hook's rule, the
policy fields and the hook-trust default below ship in `.github/devstandard-guards.json`.

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
The `merge_method` setting in `.github/devstandard-guards.json` defaults to `squash`; `merge` and
`rebase` are also accepted by GitHub. The API payload uses the PR title plus `(#PR)` as the commit
subject and the verified head commit's `Claude-Session`, `Codex-Session`, and `Co-authored-by`
trailers as its short body. GitHub's rebase method retains the individual commit messages.

**GitHub's merge queue stays off.** The reviewed commit has to be the merged commit, and the queue
lands one the server built instead: a commit no reviewer saw, merged without `guard merge` running,
so the verdict binding, the protection check and the head-pinned merge above are all skipped. That
the queue runs the required checks on its own commit does not cover this: what a queue displaces is
check 1 and the guard, not check 2. `guard protection` reports an enabled `merge_queue` rule as
non-conforming.

The PR description must carry `architecture-level: true|false`, or its #203 review record must
carry `architecture: YES|NO`. Either true flag requires a head-bound human authorization with
kind `architecture` and command text `merge OWNER/REPO#NUMBER`. Classification still requires
judgment; a false declaration is a Floor failure, not something the matcher can discover.

After main moves, add `--old-base FULL_SHA --old-head FULL_SHA`. The latest accepted #203 record
must name both old pins. The guard replays the old commits in a disposable clone with rerere and
hooks disabled, refuses conflicts and merge commits, compares every path changed in either PR
diff (including deletions, mode and symlink identity), and requires the replay tree to equal the
new head tree. The bump rides the change PR, so the two manifest version lines are the one
exemption: when `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` differ only in
their `version` value and both move to the same value, both comparisons read that as no difference,
and a replay conflict confined to those two lines resolves to the new base's value instead of
refusing.
Where that exemption is what admits the replay comparison, the guard further requires the new head
to declare a bump against the reviewed head, and its value — read as a dotted numeric release — to
sort above both the reviewed head's and the replay's, so a lane cannot rebase past a merged bump
and then set the manifests back to an older version. The admitted pair rides the proof as
`version_bump`. Any other byte or mode difference on any path still refuses. Submodules refuse for
full review. The caller's refs, index and worktree do not move.
The mechanical half can also be inspected independently:

```sh
<plugin>/scripts/guard compare --project CHECKOUT --old-base OLD_BASE --old-head OLD_HEAD --base NEW_BASE --head NEW_HEAD
```

The second layer requires the configured checks and the merged-result check — `merged-result /
BASE_SHA / HEAD_SHA` unless `merged_result_check` renames it — on the PR head. The CI checks out
GitHub's PR merge ref, verifies both parents against the event, runs the tests, then reports that
identity only after success. `reference/ci-pipelines.md`'s template ships that job; a target project
must carry it around its own test job, because installing the plugin does not install a target's CI.
A missing, red or pending identity refuses. Any failed rebase layer returns to full review,
with a resolver for conflicts. This CLI conservatively requires full review for an amended head
or quoted-Note edit; it does not mechanically implement the older quoted-fix exception.

## Review rounds and dispatch

#203's `devstandard-review-v1` PR comments are the durable attempt/ruling records. The guard reads
them; it does not publish a second round ledger. Returned verdicts consume rounds, including a Floor
failure or a malformed response; an attempt whose process returned no verdict at all does not. At
**7**, the orchestrator rules first; no eighth review or goal-fix continuation is admitted. Floor
check 1 returns the lane for real evidence; Floor check 2 stops it and escalates to the human, and
no `continue` or `merge-as-is` ruling can waive that. `merge-as-is` can settle Goal No but never
waive either Floor, and only while the reviewed head is still green. A continuation needs an
explicit `continue` ruling. An active attempt, missing/duplicate rounds, or a ruling for a different
reviewed head refuses. Architecture sign-off still applies to a merge-as-is ruling.
`scripts/guard round --repo OWNER/REPO --pr NUMBER` checks admission.

An accepted head may continue for recovery when it is behind main, with or without a conflict,
or the guard has refused that head. `review-packet rule --decision continue --reason ...` verifies
the base advance against fetched base/head objects. For a guard refusal, add
`--guard-refusal 'observed refusal'`: this is the orchestrator's attestation about the current accepted head,
not an automatic guard run. The ruling records the recovery reason and exact head (and the base
SHA for a base advance); both `start` and worker continuation consume that head-bound record.
An up-to-date accepted head without recovery evidence still refuses: Notes do not authorize a
round. Recovery waives neither the cap, Floor 2, active-attempt checks nor green CI before review.

This history is what `scripts/dispatch` and #203's assembler read — the assembler to reserve and
publish a review round, the dispatcher to admit a delivered lane's continuation. Never reach for a
low-level dispatch that omits round accounting. Both commands, and their own refusals including the
green-default-branch condition on a new lane, are in `reference/external-agent.md`.

## The role hook: one rule per role

`hooks/pre-tool-use --role worker|reviewer|orchestrator` decides one tool call, and it does one
thing: it reads the command's **raw text** — quotes, here-doc bodies and substitution bodies
included — and refuses when that text carries one of the role's words. There is no parsing and no
grammar, so **unparseable syntax is never a reason to refuse**, for any role.

**A word matches where it begins at a non-identifier position and is not continued by a hyphen.**
That is the whole boundary rule: `--force` never reads `--force-with-lease`, `-X` reads `-XPOST`,
`tag` reads `--tags`, and `git merge-base` is not `git merge`. A rule of several words matches only
where those words stand next to each other, so an option wedged between them (`git branch -v -D x`)
escapes it.

| Role | Refuses a command whose raw text carries |
|---|---|
| worker | `merge`, `tag`, `release`, `--force`, `branch -D`, `branch --delete`, `push --delete`, `worktree remove`; an `rm` whose first option carries `r` or `R` (or spells `--recursive`) unless every absolute path after it is a real path under `/tmp/` with no `..`; and `push` **only** where the same command also names the default branch |
| reviewer | `push`, `merge`, `tag`, `release`, `delete`, `rm`; and, in a command carrying `gh`, `-X`, `--method`, `-f`, `-F` or `--input` |
| orchestrator | `gh pr merge` and `git merge`, refused with the reason naming the sole admitted merge entry — `<plugin>/scripts/guard merge`, which keeps its own reviewed-head verification, rebase proof and GitHub reads; `push` naming the default branch; and `tag` or `release` unless the policy relays a standing release delegation |

The default branch is `main`, `master`, or whatever `default_branch` declares. **Everything else is
admitted**: a worker's push to its own task branch, its `--force-with-lease`, a multi-line
`python3 -c`, a `$(…)` in an argument, a `for` loop, and any composition around them; a reviewer's
`gh pr view`/`gh api` reads and any other read command; and the orchestrator's routine teardown —
deleting a merged branch or worktree — **with no authorization record of any kind**. Non-shell
tools are decided by the role's tool surface alone: Claude workers expose
Read/Glob/Grep/Bash/Edit/Write/Skill, reviewers only Read/Glob/Grep, and an orchestrator MCP tool
whose name reads as merge/release/delete/publish/send refuses to the guarded CLI.

**A refusal is a reminder, not a wall.** A worker that reaches for `merge` has usually forgotten
which lane it is in rather than defected, and the harness hands this text straight back to the
model — so one template per role fills in the word the caller actually wrote, what the role does
instead, the one page to read, and, because the scan is textual and a `grep`, a commit message or
an issue body can spell a word innocently, how to re-spell when the operation was not the intent.
The worker's, in full:

> worker role refuses a command carrying 'merge'. Instead, a worker pushes its own task branch and
> hands the PR back to the orchestrator, which owns acceptance, merge and teardown. Read
> `reference/worker.md`'s Never section. If that operation was not the intent — the word sits in a
> commit message, an issue body or a search pattern — re-spell the command so the word is absent:
> put the text in a file and pass the file (`--body-file`, `-F`, a script), or search with a
> pattern that does not spell it. That detour is legitimate.

The reviewer's sends the caller to `reference/code-review-prompt.md`'s Output format section and
the orchestrator's to `reference/orchestrator.md`'s Acceptance and integration section, naming
`guard merge` and the standing delegation as what it does instead. **Re-spelling is a legitimate detour, not an evasion**: the
rule is about the operation a command performs, and a command that merely spells a word performs
nothing. Passing a refused *operation* under another spelling is the evasion, and no role may do
it (`reference/worker.md`). A tool-surface refusal carries the same instead-and-page and no
re-spelling advice, because no word was written.

**What is outside this boundary stays outside.** Obfuscation, an interpreter script, a forged local
ref and an operation read from runtime data are not modelled, and no rule here will be added for
them: this guards the ordinary case and accepts the residual (ADR 0051; the limitation ADR 0046
already stated). What remains is the rest of the guard — `guard merge`'s reviewed-head
verification, branch protection, and the per-role OS sandbox. **A review finding of that class is a
Note**, not a defect.

The worker definition pins a worker hook; the global hook recognizes native worker and reviewer
agent types. Codex dispatch pins the role in an inline hook configuration at the per-role sandbox
posture `reference/external-agent.md` sets, and grants worker network access for git/gh.
`guard codex-config --role worker|reviewer` prints the exact TOML override for inspecting that
hook; the dispatcher's invocation policy is the `codex_role_hook_trust_bypass` setting below.

**The main session owns live executor verification before check 1.** Its Claude probe refused; the
[completed Codex probe on head f5d3c99](https://github.com/LeonJoeeee/devstandard/pull/223#issuecomment-5551952108)
also refused worker merge before execution through the dispatcher's own command, using the trust
setting below. That records the tested head; it does not establish enforcement for every command.
Skipped/untrusted hooks are not passing probes. Managed-hook policy can also exclude session hooks.
See the [Codex hook contract](https://developers.openai.com/codex/hooks)
and [Claude hook contract](https://code.claude.com/docs/en/hooks).

`.github/test-hard-edges.py` carries the table above as `REFUSED` and `ADMITTED`, swept across the
bare, quoted, here-doc, substitution and `cd … && …` positions, both tool-input formats and all
three roles, with a fixture that decides identically while every network call fails. The sweep also
asserts every refusal names its role's page and carries the re-spelling sentence. No probe
asserts a refusal for an obfuscated construction — that would encode a boundary this hook does not
claim.

## The policy file

`.github/devstandard-guards.json` **on the default branch** is the only policy. The hook reads it
once per process from the **local `origin/main` ref** with `git show` — never over the network
inside a tool call, and never from the working tree, so an unmerged edit grants nothing and no
fetch happens. A missing ref, a missing file, a directory outside any repository, or JSON that will
not parse all mean the built-in defaults above, for every role. **Nothing in the hook refuses
because a read failed**, so no network fault can arrive as a refusal (#303, #323). A repository
whose default branch is not `main` therefore runs on the built-in defaults.

- `required_checks`: the protection contexts this target requires, default `["test"]`. `guard merge`
  and `guard protection` both read it; `protection --check` overrides it. A value that is not
  a non-empty list of names refuses **at merge and protection time**, never at a tool call. The
  dispatcher's new-lane gate reads the same field and takes no default, so a target naming none is
  judged green-only (`reference/external-agent.md`).
- `merged_result_check`: the name of the per-merge integration check, default
  `merged-result / {base} / {head}`. A target that renames its job says so here and must keep both
  `{base}` and `{head}` in the name — a name unbound to either pin refuses, because an unpinned
  check proves nothing about *this* merge result.
- `default_branch`: the branch name the `push` rules add to `main` and `master`.
- `command_patterns`: `{"worker": [...], "reviewer": [...], "orchestrator": [...]}` — extra words
  for one role, matched exactly like the built-ins. **Additive only**: an unknown key, a wrong
  shape or an empty list adds nothing and can remove nothing.
- `standing_release`: null by default. A human may set `{ "repo": "OWNER/REPO", "source":
  "https://github.com/OWNER/REPO/issues/NUMBER#issuecomment-ID" }` to relay an existing standing
  delegation; the source must be a comment URL under that same `repo`. It admits the orchestrator's
  `tag` and `release` commands and nothing else. Revocation removes the setting on the default branch.
- `authorization_issue` and `human_logins`: **the one record left.** `guard merge` requires it for
  an architecture-level merge and is its only reader — the hook performs no lookup of any kind, and
  a release needs the delegation above rather than a record. An allowlisted human posts the JSON
  below as the **whole comment**, prefixed by `<!-- devstandard-authorization-v1 -->` and a newline.
  The latest matching record decides; `revoked: true`, expiry, a wrong head, command digest or
  actor refuses. Take the digest from the exact command text
  (`printf '%s' 'merge OWNER/REPO#NUMBER' | sha256sum`); expiry is mandatory, and a record is
  reusable for its exact head/command until expiry or revocation. Humans should use a distinct
  publishing identity where agents share the repository owner's account.
- `record_logins`: who may publish the operative review records, default the repository owner.
- `merge_method`: `squash` by default; `merge` and `rebase` are also accepted by GitHub.
- `codex_role_hook_trust_bypass`: true by default. Only when attaching the fixed
  `hooks/pre-tool-use` role hook from its own installation does the dispatcher pass
  `--dangerously-bypass-hook-trust`, intended by Codex for automation that already vets hook
  sources. It checks that source exists before creating a lane. The flag applies to enabled hooks
  for that invocation, so the caller must vet the installation and any other enabled hook sources;
  it does not change persisted trust. Setting false omits the flag and requires trust established
  outside non-interactive `exec`, which cannot prompt to trust this inline hook. A string value
  such as `"false"` refuses. Claude dispatch never receives the flag.

```json
{"repo":"OWNER/REPO","head":"FULL_HEAD_SHA","kind":"architecture","command_sha256":"SHA256_OF_EXACT_COMMAND_TEXT","expires":"2026-09-06T00:00:00+00:00","revoked":false}
```

## Founding a repository

Setup starts in an empty directory, and a repository being founded has no policy file — so it has
no `authorization_issue`, so no record can exist, and the push that would land that file is itself
a push to the default branch. So the one admission: **an orchestrator's push naming the default
branch is admitted while `origin/main` carries no `.github/devstandard-guards.json`.** With no
policy there is nothing to bypass, and the push that lands the file closes the door behind itself.
Nothing else widens — `gh pr merge`, a release, and every other role keep their refusal. The
admission is a plain one and is not a claim that the push is safe: `--force` and `--delete` are not
on the orchestrator's word list anywhere, and GitHub's branch protection is what rejects a push to a
protected branch, which is the layer that check belongs to. Founding is the orchestrator's work
(`reference/prd.md`).

Copy the shipped [policy template file](devstandard-guards.json.template) to the target's
`.github/devstandard-guards.json`. Replace every `OWNER-LOGIN` with the human's GitHub login and
`ISSUE-NUMBER` with the unquoted integer number of the authorization issue the setup step opens.
The filled file must parse as JSON; keep `{base}` and `{head}` literal in `merged_result_check`.

That is the whole minimum: `command_patterns` extends the built-ins where a project has commands of
its own, and `standing_release` stays absent until a human delegates one. Applying protection comes
after this file lands, because `required_checks` is what names its contexts — and since #323 the
hook does not gate `guard protection --apply` at all. It stays the human/main session's command by
role instruction and by who holds admin credentials, not by a refusal.

## Branch protection

Read-only expected-state check, usable on any branch:

```sh
<plugin>/scripts/guard protection --repo OWNER/REPO --branch main
```

Human/main session only: append `--apply` to run the documented `gh api --method PUT` payload in
`scripts/guard`, then read it back. The required contexts come from the target's own
`required_checks` (read through `--project`, defaulting to the working directory); repeat `--check`
to name them explicitly instead, which is also what a repository with no policy file yet must do.
The payload also sets strict up-to-date status checks, admin enforcement, no force pushes and no
deletions.
The check also refuses an enabled merge queue (above); because classic protection carries no queue
field, it reads the branch's active rules for a `merge_queue` rule, and an unreadable rules response
refuses rather than passes. `--apply` does not turn a queue off — that is the human's to do.
The payload sets no review-count or actor restriction; inspect existing extra protection before
using this provisioning command because PUT replaces those fields. Workers never run it.
Classic status protection alone does not prohibit a credential holder from pushing a pre-green
commit directly: PR-only behavior also depends on the role/merge route. It is not a server-side
verification of a Goal/Floor comment. Never weaken protection to manufacture a negative probe.

#204's live negative fixture is `probe/204-unprotected`, created and deleted with `gh` by the worker
under the main session's recorded ruling. Its check refused with HTTP 404 while main's check passed.
Unit probes cover both API shapes. Evidence, commands and exit codes belong on the PR; live executor
probes and whole check 1 belong to the main session under the continuation ruling.
