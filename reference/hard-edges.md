# Guarded operations

The installed plugin's `scripts/guard` is the orchestrator's merge entry point. Workers never
merge, release, or apply protection. Python 3.9+, git 2.38+, and authenticated `gh` are required;
the test suite also uses Python 3.11+'s TOML parser. The match, authorization and hook-trust
defaults below were settled under #204 on 2026-09-06 and ship in `.github/devstandard-guards.json`.

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

## Role hooks and configurable authorization

Claude workers expose Read/Glob/Grep/Bash/Edit/Write/Skill; reviewers expose only Read/Glob/Grep.
The worker definition pins a worker PreToolUse hook. The global hook recognizes native worker
and reviewer agent types. Codex dispatch pins the role in an inline hook configuration at the
per-role sandbox posture `reference/external-agent.md` sets, and grants worker network access
for git/gh.
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
reviewers refuse them except for the routine worker commands below; the orchestrator
requires authorization or the guarded merge entry point. Codex reviewers also admit literal
`gh pr view`, `gh issue view`, `gh run view`, `gh pr checks`, and REST `gh api` reads with an
implicit or explicit GET; writes, non-GET methods, fields, input files, and shell composition refuse.
The Shell composition contract below owns syntax admission and its textual boundary. Hook trust,
the OS sandbox and GitHub protection remain separate enforcement boundaries with the limitations above.

Once a target repository resolves, every role loads `.github/devstandard-guards.json` from its remote
default-branch SHA through the same `settings_for` loader, before deciding a modelled tool call. Repository metadata
also supplies the actual default branch for push recognition; a policy field cannot override it.
The successful snapshot is cached per project for the life of the Python process. A fresh hook
process reads a fresh snapshot; this is not a cross-process or persistent cache.

The conservative fallback is shared: built-in kinds always apply and configured extensions only
add. Proven policy absence means built-ins, required `test`, owner record publisher, no human
authorizers and no standing release grant. Malformed/unreadable policy or authorization refuses,
including worker/reviewer read calls; there is no empty-policy recovery from a failed read.
An unmerged local edit cannot narrow or authorize anything. The settings are:

- `required_checks`: the protection contexts this target requires, default `["test"]`. `guard merge`
  and `guard protection` both read it; `protection --check` overrides it. A value that is not
  a non-empty list of names refuses.
- `merged_result_check`: the name of the per-merge integration check, default
  `merged-result / {base} / {head}`. A target that renames its job says so here and must keep both
  `{base}` and `{head}` in the name — a name unbound to either pin refuses, because an unpinned
  check proves nothing about *this* merge result.

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
  Recognition is independent of role: workers/reviewers refuse subject to the exceptions below;
  the orchestrator follows its exact-command authorization or guarded-merge path. Extension regexes
  see the segment's literal argv joined with spaces, with git/gh/guard paths reduced to basenames
  and multiword arguments replaced by `<argument>`; they do not consume option values.
  After recognition, workers may use a simple `git push` with `--force-with-lease[=ref[:expect]]`
  or `--force-if-includes`, an explicit remote and non-default branch destinations, and no other
  irreversible/release indicators; ownership and absence of a review in flight remain the worker
  brief's obligations. Workers may also use a simple `rm` whose every target is an absolute path
  resolving strictly below `/tmp` or the system temp directory selected by `TMPDIR`; temp roots,
  parent traversal, symlink escapes, mixed outside targets, and shell composition refuse. These
  role exceptions preserve recognition and the configured patterns, including the repository's
  recursive-deletion pattern.
- `authorization_issue` and `human_logins`: an allowlisted human posts the following JSON as the
  **whole comment**, prefixed by `<!-- devstandard-authorization-v1 -->` and a newline. The latest
  matching record decides; `revoked: true`, expiry, a wrong head, command digest or actor refuses.
- `standing_release`: null by default. A human may set `{ "repo": "OWNER/REPO", "source":
  "https://github.com/OWNER/REPO/issues/NUMBER#issuecomment-ID" }` to relay an existing standing
  delegation. It covers recognized release commands only, not major-version tags, architecture
  approval or an irreversible command appended to a release. Major tags use `major-release`
  one-shot authorization. Revocation removes the setting on the default branch.
- `codex_role_hook_trust_bypass`: true by default. Only when attaching the fixed
  `hooks/pre-tool-use` role hook from its own installation does the dispatcher pass
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
a distinct publishing identity where agents share the repository owner's account. Take the digest
from the exact command text: `printf '%s' 'COMMAND' | sha256sum`.

## Founding a repository: the policy file, and what happens before it exists

Setup starts in an empty directory. If repository discovery fails and local Git establishes that
the tool event's cwd is outside a repository or has no `origin` remote, there is no repository policy
to read. Ordinary non-shell tools and unrecognized shell commands are admitted, including `Read`,
`git init -b main` and `gh repo create X --public`; existing role/tool restrictions still apply.
Recognized merge, release and irreversible commands instead deny with **`no repository to read
policy from`**, before any HEAD, authorization or founding lookup. This is fail-closed for guarded
operations, not a grant of founding permission. Other Git failures and failures reading a resolved
repository's remote policy still refuse; neither is treated as an absent repository.

Every setting above lives on the default branch, so a new repository has none of them — and an
authorization record cannot come first, because `authorization_issue` is a policy field. Denying
everything would make the founding push unreachable and leave a seeded project permanently
unguarded, so **proven policy absence admits exactly one operation it otherwise refuses: an
orchestrator's plain `git push` whose every destination is the default branch, and only while that
branch is also unprotected.** Both facts are what make it safe — there is no policy to bypass and no
protection to replace — and either policy or protection appearing closes the door, so the push that lands the
policy file is the last one admitted. Absence must be *proven*: a default branch with no commits at
all counts (a branch that does not exist carries no file), an explicit 404 and nothing else; any
other read failure refuses, as it always did. Nothing else widens. `--force`, `--delete`, `--mirror`,
`--tags`, a wildcard refspec, any other destination, `guard protection --apply`, an API write, a
release or a deletion all keep their refusal, and no other role gets this at all — workers and
reviewers still refuse the push. Founding is the orchestrator's work (`reference/prd.md`).

Copy the shipped [policy template file](devstandard-guards.json.template) to the target's
`.github/devstandard-guards.json`. Replace every `OWNER-LOGIN` with the human's GitHub login and
`ISSUE-NUMBER` with the unquoted integer number of the authorization issue the setup step opens.
The filled file must parse as JSON; keep `{base}` and `{head}` literal in `merged_result_check`.

That is the whole minimum: `command_patterns` extends the built-ins where a project has commands of
its own, and `standing_release` stays absent until a human delegates one. Applying protection comes
after this file lands, under an ordinary authorization record — so the first thing a new project's
human authorizes is the gate itself.

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
| [`git push`](https://git-scm.com/docs/git-push) | `--force`, `-f`, `--force-with-lease[=ref[:expect]]`, `--force-if-includes`, `--mirror`, `--delete`, `-d`, leading `+refspec`, leading `:refspec`, matching-branches `:`; default-branch destinations normalize `refs/heads/NAME`, `heads/NAME`, and `NAME`, including source-prefixed and deletion refspecs; `--all` / `--branches` includes the default branch and `--prune` deletes refs; a wildcard branch destination (`refs/heads/*:refs/heads/*`, `*:*`) has that same reach spelled as a refspec, quoted or not | irreversible |
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

The worker/reviewer grammar models literal words, horizontal whitespace, and the separators and
redirections below. It consumes the entire input before classification, preserving quote and
adjacency information until operators and their targets have been removed. The orchestrator
extensions follow the table.

| Family | Decision and probe contract |
|---|---|
| Separators `;`, `&&`, `\|\|`, pipe, `&` | Modelled: recover and classify every command segment; a dangerous segment refuses. Other operator combinations (such as `;;` or pipe-and-stderr) refuse. |
| Newline, CR, other control/whitespace characters | Refused, including inside quotes. Only ordinary space and tab are admitted. |
| Grouping `( )`, `{ }`; functions and control flow | Refused outside quotes. Reserved command words, assignment prefixes, and negation also refuse. |
| Redirections `<`, `>`, `>>`, `2>`, `&>`, `&>>`, `>|`, `n>&m`, `<&`, `<<<`, `<>` | Modelled: remove each operator and its literal target; preserve surrounding argv. Adjacent unquoted descriptor numbers are removed; quoted or spaced numbers remain arguments. Descriptor close/move targets are consumed too. A missing target or unsupported operator refuses. |
| Here-documents `<<`, `<<-` | Refused as a whole, including quoted delimiters and tab-stripped bodies. Their bodies and expansions are not modelled or treated as ordinary argv. Use a separate input file. |
| Wrappers `eval`, `sh -c`, `bash -c`, `env`, `xargs`, `command`, `exec`, `nohup`, `setsid`, `time`, `nice`, `sudo`, `timeout`, `builtin` | Refused at command position, including paths, quoted names and options. Other named shells, `source`, `.`, and alias-definition commands also refuse. Quoted command arguments cannot disappear as prose under a wrapper. |
| Substitution `$()`, backticks, `${}`, `$VAR`, process substitution | Dollar signs and backticks refuse outside single quotes, including double-quoted or escaped forms. Process substitution refuses outside quotes. Single-quoted text is literal. |
| Brace and glob expansion (`{gh,x}`, `g?`, `g*`, `[g]h`), tilde expansion | Refused outside quotes, including escaped forms; single- and double-quoted patterns are literal arguments. |
| Quoting and escaping (`g"h"`, `\gh`, `'gh'`) | Modelled: concatenate/decode literal words before matching. Quoted/escaped operators remain argv, never separators or redirections. Multiword prose arguments remain data. Quote masking stops exactly where the shell still expands: control characters refuse inside quotes too, and dollar signs and backticks keep refusing inside double quotes. A quoted argument is still read as the value it is, so a wildcard refspec or delete target keeps its operation's kind. |
| Comments and hashes | Conservative over-scan: no hash discards a suffix. Plain/quoted hash filenames work; an operation after a comment marker may refuse even when the shell would ignore it. |

Worker and reviewer roles refuse every dangerous or unsupported case above, subject to the exceptions
for routine worker commands. Reviewers retain their restricted read-command surface, so modelled
shell operators can still refuse there; literal `find` joins `rg` and the other read commands as a
search only — `-delete`, `-exec`/`-execdir`, `-ok`/`-okdir`, `-fprint`/`-fprint0`/`-fprintf` and
`-fls` act rather than read, and refuse for that role.

**Orchestrator extensions:** newlines separate commands (and remain data inside quotes); literal
backslash-newline continuations join words. An unquoted `#` at the start of a word begins a comment
through the end of that line, before heredoc, operator, or command recognition; hashes inside words
or quotes stay literal. `$()` and simple backtick substitutions recursively
parse and classify every inner command. `~` or `~/` is a path prefix. Literal `for NAME in WORD…;
do … done`, `if … then … [else …] fi`, and `while … do … done` classify every condition and body;
only an enclosing loop's `$NAME` may expand in argument position. A single-quoted identifier
delimiter, `<<'EOF'`, attaches its body as data; shell wrappers and interpreter commands that
execute that input refuse. Executables must always be literal.

Substitution results and loop variables are **unknown words**, never evaluated. Unknown arguments
are admitted only for this closed inert allowlist, unless a built-in predicate or repository policy
guards the executable: `echo`, `printf`, `cat`, `ls`, `wc`, `head`, `tail`, `cut`, `sort`, `uniq`,
`tr`, `grep`, `sed`, `awk`, `jq`, `diff`, `cmp`, `stat`, `file`, `basename`, `dirname`, `realpath`,
`date`, `test`, `true`, `false`, `mkdir`, `touch`, `cp`, `mv` (within the project); `find` only
without any literal `-exec`, `-execdir`, `-ok`, `-okdir`, or `-delete`; `python3`/`node` only after
a literal script path or their literal `-c`/`-e` selector. Interpreter behavior retains the textual
boundary described below. Existing wrappers remain refused; `ssh`, `parallel`, `watch`, and every
other unlisted executable refuse unknown arguments. `rm` remains guarded. A guarded executable
may accept an unknown word only after a literal read subcommand from this closed set:

- `git`: `log`, `show`, `diff`, `status`, `rev-parse`, `ls-tree`, `ls-files`, `cat-file`,
  `merge-base`, `branch --show-current`, `fetch`, `worktree list`;
- `gh`: `issue view`, `issue list`, `pr view`, `pr list`, `pr checks`, `pr diff`, `run view`,
  `run list`, `release view`, and plain-GET `api` without method, field, or input options.

The unknown must occupy a provable data position: a single quoted word after `--` or a
value-taking option (`--jq`, `--json`, `-m`, `--format`, `--body`, `--title`), or a positional
word whose literal prefix excludes an option. Otherwise it refuses with
`unresolved argument to a guarded executable`, naming that executable. Uncertain policy
executable prefixes conservatively guard every executable. The same refusal reason applies to
unlisted executables and excluded allowlist forms. Built-in predicates and policy patterns see
only literal words.

The orchestrator retains exact-command/head authorization for recognized operations, including
inside substitutions and compounds; a release grant cannot authorize an irreversible segment.
Both grammars are closed: any unsupported syntax, malformed quote/escape, or unread remainder is
**unparsed** and every role refuses it with `shell syntax is unsupported; use separate simple
commands` (workers/reviewers do so before policy lookup). No residual unmodelled syntax is admitted.
Brace/glob expansion, general parameter expansion, arithmetic, process substitution, unquoted
heredocs and wrappers remain outside the orchestrator grammar. Interpreter arguments such as
`python3 script.py` retain their existing textual classification; arbitrary interpreter behavior
remains outside this boundary ([ADR 0046](../docs/adr/0046-guarded-merge-and-content-unchanged-rebase.md)).

`.github/test-hard-edges.py` carries the table as `SHELL_FAMILIES`, direct hook probes for both tool
input shapes and all three roles, redirection probes at every argv boundary, and an adversarial sweep of
operation witnesses across every family. `GLOBAL_OPTIONS` also sweeps joined/separate option
values, switches and clusters at every argv boundary, alongside reordered/interleaved tokens and
the round-4 through round-6 negative hook probes. Each configured operation
pattern must have a witness. Default-destination witnesses include a non-main default branch across
bare, qualified, source-prefixed, and deletion refspecs. Witnesses also carry quoting in the argument
position recognition consumes — a wildcard push refspec, a quoted delete target — so masking a quoted
literal cannot hide the operation its value names. Lease-push refusal witnesses target the
default branch; focused probes cover admitted task-branch pushes and temporary cleanup alongside
their refused variants. Both sweeps exercise every role hook with no grant: executable-operation
and unsupported-syntax variants must deny; comment-only variants follow the role grammar above.
Focused probes also verify the real
authorization lookup, exact-command binding, standing release and exact installed merge entry point.
Only external policy/head/GitHub reads are doubled; dangerous text is never executed.

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
