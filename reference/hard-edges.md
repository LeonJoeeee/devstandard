# Guarded operations

The installed plugin's `scripts/guard` is the orchestrator's merge entry point. Workers never
merge, release, or apply protection. Python 3.9+, git 2.38+, and authenticated `gh` are required;
the test suite also uses Python 3.11+'s TOML parser. The match, authorization and hook-trust defaults below
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
`guard codex-config --role worker|reviewer` prints the exact TOML override for inspecting that hook;
the dispatcher's invocation policy is the `codex_role_hook_trust_bypass` setting below.

**The main session owns live executor verification before check 1.** Its Claude probe refused;
the [completed Codex probe on head f5d3c99](https://github.com/LeonJoeeee/devstandard/pull/223#issuecomment-5551952108)
also refused worker merge before execution through the dispatcher's own command, using the trust
setting below. That records the tested head; it does not establish enforcement for every command.
Skipped/untrusted hooks are not passing probes. Managed-hook policy can also exclude session hooks.
See the [Codex hook contract](https://developers.openai.com/codex/hooks)
and [Claude hook contract](https://code.claude.com/docs/en/hooks).

The guard recognizes ordinary operation spellings identically across all three roles. Workers and
reviewers refuse them; the orchestrator requires authorization or the guarded merge entry point.
Every composition the parser cannot fully account for refuses. Encoded or self-modifying forms
(base64 piped to a shell, code strings handed to an interpreter, functions defined and called in one
line whose tokens no longer name the operation) are outside this guard by design. Hook trust, the
OS sandbox and GitHub protection remain separate enforcement boundaries with the limitations above.

Every role loads `.github/devstandard-guards.json` from the target's remote default-branch SHA
through the same `settings_for` loader, before deciding a modelled tool call. Repository metadata
also supplies the actual default branch for push recognition; a policy field cannot override it.
The successful snapshot is cached per project for the life of the Python process. A fresh hook
process reads a fresh snapshot; this is not a cross-process or persistent cache.

The conservative fallback is shared: built-in kinds always apply and configured extensions only
add. Proven policy absence means built-ins, required `test`, owner record publisher, no human
authorizers and no standing release grant. Malformed/unreadable policy or authorization refuses,
including worker/reviewer read calls; there is no empty-policy recovery from a failed read.
An unmerged local edit cannot narrow or authorize anything. The proposed settings are:

- `command_patterns`: per-kind regex lists extending the shared built-in token recognizer. Built-ins cover
  merge CLI, tag/release/package publication, forced/default-branch pushes, recursive/forced
  deletion and common external delete/API-write commands. The shell contract below decides which
  inputs reach those patterns. Configured patterns can add operations, never disable built-ins.
  Each recovered segment is recognized when its tokens contain the executable and operation verbs
  anywhere, regardless of order or intervening options/values. Push/delete/API-write indicators
  are matched the same way. Executable paths use basenames; multiword quoted data stays one token.
  Over-refusal is accepted by the round-4 orchestrator ruling: `git tag -l`, `gh pr merge --help`,
  and even read commands whose separate arguments name an operation reach the same role consequence.
  Short-option clusters expand before matching: each character is an indicator and each suffix
  retains its attached value (`-rfv` supplies `-r`/`-f`/`-v`; `-iXDELETE` supplies `-XDELETE`).
  Long options stay whole. Values are not consumed, so option-looking data can over-refuse.
  Recognition is independent of role: workers/reviewers refuse;
  the orchestrator follows its exact-command authorization or guarded-merge path. Extension regexes
  see the segment's literal argv joined with spaces, with git/gh/guard paths reduced to basenames
  and multiword arguments replaced by `<argument>`; they do not consume option values.
  The round-6 continuation requires guarding `--force-with-lease` too. The role brief still
  permits an own-branch rewrite without a review in flight; this conservative matcher cannot
  establish those conditions and refuses it at the hook. Route that refusal to the caller;
  ordinary permission in the role brief is not a hook bypass.
- `authorization_issue` and `human_logins`: an allowlisted human posts the following JSON as the
  **whole comment**, prefixed by `<!-- devstandard-authorization-v1 -->` and a newline. The latest
  matching record decides; `revoked: true`, expiry, a wrong head, command digest or actor refuses.
- `standing_release`: null by default. A human may set `{ "repo": "OWNER/REPO", "source":
  "https://github.com/OWNER/REPO/issues/NUMBER#issuecomment-ID" }` to relay an existing standing
  delegation. It covers recognized release commands only, not major-version tags, architecture
  approval or an irreversible command appended to a release. Major tags use `major-release`
  one-shot authorization. Revocation removes the setting on the default branch.
- `codex_role_hook_trust_bypass`: true by default, pending the human's ruling. Only when attaching
  the fixed `hooks/pre-tool-use` role hook from its own installation does the dispatcher pass
  `--dangerously-bypass-hook-trust`, intended by Codex for automation that already vets hook
  sources. It checks that source exists before creating a lane. The flag applies to enabled hooks
  for that invocation, so the caller must vet the installation and any other enabled hook sources;
  it does not change persisted trust. Setting false omits the flag and requires trust established
  outside non-interactive `exec`, which cannot prompt to trust this inline hook. A string value
  such as `"false"` refuses. Claude dispatch never receives the flag.

```json
{"repo":"OWNER/REPO","head":"FULL_HEAD_SHA","kind":"irreversible","command_sha256":"SHA256_OF_EXACT_COMMAND_TEXT","expires":"2026-09-06T00:00:00+00:00","revoked":false}
```

The hook permits a recognized orchestrator operation only after this lookup, or permits the exact
installed `guard merge` entry point to perform its own verification. It never turns an authorization
record into worker merge/release permission. Expiry is mandatory; a record is reusable for its exact
head/command until expiration or revocation, not an atomic single-use capability. Humans should use
a distinct publishing identity where agents share the repository owner's account.

## Documented operation indicators

This table defines the built-in match set; `.github/test-hard-edges.py` carries its literal witnesses
in `DANGEROUS_OPERATIONS` and `OPERATION_SYNONYMS`. Indicators are conjunctions within a recovered
segment, independent of argv position. All short forms below also match in clusters, in any order
and with other switches. Dry-run/help/negating flags do not cancel a recognized operation. When kinds
overlap, merge wins, then irreversible, then release; a release delegation cannot authorize deletion.

| Operation (tool documentation) | Indicators and synonyms | Kind |
|---|---|---|
| [`gh pr merge`](https://cli.github.com/manual/gh_pr_merge), installed `guard merge` | Executable plus `pr merge`, or `guard merge`; no option needed | merge |
| [`rm`](https://www.gnu.org/software/coreutils/manual/html_node/rm-invocation.html) | `-r`, `-R`, `--recursive`, `-f`, `--force`; clusters such as `-rf`, `-fr`, `-Rf`, `-fR`, `-rfv`, `-vrf`, `-ifR` | irreversible |
| [`git push`](https://git-scm.com/docs/git-push) | `--force`, `-f`, `--force-with-lease[=ref[:expect]]`, `--force-if-includes`, `--mirror`, `--delete`, `-d`, leading `+refspec`, leading `:refspec`, matching-branches `:`; default-branch destinations as bare names or `[source:]refs/heads/NAME` / `source:NAME`; `--all` / `--branches` includes the default branch and `--prune` deletes refs | irreversible |
| [`git branch`](https://git-scm.com/docs/git-branch) | `-D`, or `-d` / `--delete` together with `-f` / `--force`; includes `-df`, `-fd`, `-vD`, `-vdf` | irreversible |
| [`git tag`](https://git-scm.com/docs/git-tag) | Any `tag` operation is release; `-d` / `--delete` raises it to irreversible | release / irreversible |
| [`git update-ref`](https://git-scm.com/docs/git-update-ref) | `-d` (no documented long deletion alias) | irreversible |
| [`gh release`](https://cli.github.com/manual/gh_release) | `create`, `upload`, `edit`; `delete` raises it to irreversible | release / irreversible |
| [`gh repo delete`](https://cli.github.com/manual/gh_repo_delete) | `repo delete`, with or without `--yes` | irreversible |
| [`gh api`](https://cli.github.com/manual/gh_api) | `DELETE`, `PUT`, `PATCH`, `POST` with `-X METHOD`, `-XMETHOD`, `--method METHOD`, `--method=METHOD`; `-f` / `--raw-field`, `-F` / `--field`, `--input` also imply writes, with joined or separate values | irreversible |
| [`git push` tags](https://git-scm.com/docs/git-push) | `--tags`, `--follow-tags`, `refs/tags/` refspecs or semantic-version tag tokens; `--mirror` already requires irreversible authorization | release |
| [`npm`](https://docs.npmjs.com/cli/v11/commands/npm-publish/), [`pnpm`](https://pnpm.io/cli/publish), [`yarn`](https://classic.yarnpkg.com/en/docs/cli/publish), [`twine`](https://twine.readthedocs.io/en/stable/#twine-upload) | `publish` for the package managers; `upload` for twine | release |
| [`terraform`](https://developer.hashicorp.com/terraform/cli/commands/destroy), [`kubectl`](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_delete/), [`aws`](https://docs.aws.amazon.com/cli/latest/reference/s3api/delete-bucket.html) | `destroy` / `apply -destroy`, `delete`, and `delete` / `delete-*`, respectively | irreversible |
| `guard protection` | `--apply`; provisioning remains human/main-session only | irreversible |

The short-option witnesses include attached values and clusters at both ends. An exhaustive small
alphabet probe covers every length-1–4 cluster of `rRfv` containing a destructive rm indicator.
The two adversarial sweeps insert global options, reorder tokens, and apply each shell family to
these witnesses for all roles and both tool formats. The real hook must deny with no grant; focused
probes prove only the orchestrator can take a valid exact-command authorization path. Remote-policy
handler probes include `rm -R` and an extension-only operation so built-in coverage cannot mask a
missing policy read, plus absent/unreadable policy, a non-`main` default branch and process-cache reuse.

## Shell composition contract

The classifier accepts a closed grammar of literal words, horizontal whitespace, the separators
and redirections below. It consumes the entire input before classification, preserving quote and
adjacency information until operators and their targets have been removed. Any unsupported token,
malformed quote/escape, or unread lexer remainder refuses **before** role exceptions or policy
lookup. This contract concerns shell composition, not the behavior of an arbitrary executable.

| Family | Decision and probe contract |
|---|---|
| Separators `;`, `&&`, `\|\|`, pipe, `&` | Modelled: recover and classify every command segment; a dangerous segment refuses. Other operator combinations (such as `;;` or pipe-and-stderr) refuse. |
| Newline, CR, other control/whitespace characters | Refused, including inside quotes. Only ordinary space and tab are admitted. |
| Grouping `( )`, `{ }`; functions and control flow | Refused. Reserved command words, assignment prefixes, and negation also refuse. |
| Redirections `<`, `>`, `>>`, `2>`, `&>`, `&>>`, `>|`, `n>&m`, `<&`, `<<<`, `<>` | Modelled: remove each operator and its literal target; preserve surrounding argv. Adjacent unquoted descriptor numbers are removed; quoted or spaced numbers remain arguments. Descriptor close/move targets are consumed too. A missing target or unsupported operator refuses. |
| Here-documents `<<`, `<<-` | Refused as a whole, including quoted delimiters and tab-stripped bodies. Their bodies and expansions are not modelled or treated as ordinary argv. Use a separate input file. |
| Wrappers `eval`, `sh -c`, `bash -c`, `env`, `xargs`, `command`, `exec`, `nohup`, `setsid`, `time`, `nice`, `sudo`, `timeout`, `builtin` | Refused at command position, including paths, quoted names and options. Other named shells, `source`, `.`, and alias-definition commands also refuse. Quoted command arguments cannot disappear as prose under a wrapper. |
| Substitution `$()`, backticks, `${}`, `$VAR`, process substitution | Refused by the raw syntax gate, even when quoted or escaped. |
| Brace and glob expansion (`{gh,x}`, `g?`, `g*`, `[g]h`), tilde expansion | Refused by the raw syntax gate, even when quoted or escaped. |
| Quoting and escaping (`g"h"`, `\gh`, `'gh'`) | Modelled: concatenate/decode literal words before matching. Quoted/escaped operators remain argv, never separators or redirections. Multiword prose arguments remain data. The raw syntax refusals above still apply. |
| Comments and hashes | Conservative over-scan: no hash discards a suffix. Plain/quoted hash filenames work; an operation after a comment marker may refuse even when the shell would ignore it. |

Worker and reviewer roles refuse every dangerous or unsupported case above. Reviewers additionally
retain their restricted read-command surface, so modelled shell operators can still refuse there.
The orchestrator retains exact-command/head authorization for **modelled** recognized operations;
a release grant cannot authorize an irreversible segment, and unsupported syntax refuses for that
role too. Use separate simple commands when this grammar refuses; authorization cannot override it.

`.github/test-hard-edges.py` carries the table as `SHELL_FAMILIES`, direct hook probes for both tool
input shapes and all three roles, redirection probes at every argv boundary, and an adversarial sweep of
operation witnesses across every family. `GLOBAL_OPTIONS` also sweeps joined/separate option
values, switches and clusters at every argv boundary, alongside reordered/interleaved tokens and
the round-4 through round-6 negative hook probes. Each configured operation
pattern must have a witness. Both sweeps exercise every role
hook with no grant: every variant must deny, never return `{}`. Focused probes also verify the real
authorization lookup, exact-command binding, standing release and exact installed merge entry point.
Only external policy/head/GitHub reads are doubled; dangerous text is never executed.

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
