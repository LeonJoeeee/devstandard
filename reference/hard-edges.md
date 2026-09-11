# Guarded operations

The installed plugin's `scripts/guard` is the orchestrator's merge entry point. Workers never
merge, release, or apply protection. Python 3.9+, git 2.38+, and authenticated `gh` are required;
the test suite also uses Python 3.11+'s TOML parser. **There is nothing to configure.** The guard
has no settings file: the role hook's words are in its source, `guard merge` reads GitHub itself,
and every check name a command needs comes from that command line.

## Merge and rebase proof

Fetch current objects, then run the read-only check; add `--execute` only as the orchestrator:

```sh
<plugin>/scripts/guard merge --repo OWNER/REPO --pr NUMBER --project CHECKOUT
```

It requires an open PR into the repository's current default branch, that base as an ancestor of
the PR head, conforming protection on that branch, and the latest whole Goal Yes / both Floor Pass
verdict for that exact head. **Only the account that owns the repository may publish the operative
records**, read from the repository's own API record rather than declared anywhere. This is a
publishing-identity check, not proof that a shared account's operator is human.
The API merge uses a head-SHA precondition and GitHub's strict protection; a changed base or PR
during verification refuses. Keep one orchestrator per PR. Protection and current-source review
remain necessary because credentials and workflow files are not made immutable by this script.
**The merge is a squash**, with the PR title plus `(#PR)` as the commit subject and the verified
head commit's `Claude-Session`, `Codex-Session`, and `Co-authored-by` trailers as its short body.

**GitHub's merge queue stays off.** The reviewed commit has to be the merged commit, and the queue
lands one the server built instead: a commit no reviewer saw, merged without `guard merge` running,
so the verdict binding, the protection check and the head-pinned merge above are all skipped. That
the queue runs the required checks on its own commit does not cover this: what a queue displaces is
check 1 and the guard, not check 2. `guard protection` reports an enabled `merge_queue` rule as
non-conforming.

The PR description must carry `architecture-level: true|false`, or its #203 review record must
carry `architecture: YES|NO`. Either true flag requires **one comment of the repository owner's own
on that PR** — any comment that is not one of the records this method publishes there. Signing off
is reading the change and saying so on it; there is no record to format, no issue to find it on and
no allowlist to keep. Classification still requires judgment; a false declaration is a Floor
failure, not something the matcher can discover.

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
The Codex plugin manifest is outside this exemption and the bare-bump review waiver. Its version
is synchronized at release, but changing it takes ordinary check 1 and a fresh review after rebase.
The mechanical half can also be inspected independently:

```sh
<plugin>/scripts/guard compare --project CHECKOUT --old-base OLD_BASE --old-head OLD_HEAD --base NEW_BASE --head NEW_HEAD
```

The second layer requires the merged-result check — `merged-result / BASE_SHA / HEAD_SHA`, one
fixed name pinned to both SHAs — on the PR head, and every other check the head reports to be green.
That all-observed-green rule is the whole CI requirement: no list of names is configured anywhere,
so a project cannot be judged against a job it does not have, and silence is never green — a head
reporting no check at all refuses. The CI checks out
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
| orchestrator | `gh pr merge` and `git merge`, refused with the reason naming the sole admitted merge entry — `<plugin>/scripts/guard merge`, which keeps its own reviewed-head verification, rebase proof and GitHub reads |

The default branch is `main` or `master`, by name. A repository that calls its default branch
something else is outside the worker's push rule, and nothing the hook could read would tell it
otherwise. **Everything else is admitted**: a worker's push to its own task branch, its
`--force-with-lease`, a multi-line
`python3 -c`, a `$(…)` in an argument, a `for` loop, and any composition around them; a reviewer's
`gh pr view`/`gh api` reads and any other read command; and the orchestrator's routine teardown —
deleting a merged branch or worktree — **with no authorization record of any kind**.

**The hook judges commands by word list, and never tool names.** Every tool call that is not a
shell command is admitted for every role, a role's own `Agent` spawn of a subagent included. No
tool allowlist remains anywhere, and that is this page's rule of shape: **a hard limit
— a hook, a guard, a tool denial — is reserved for the very serious or the fully forbidden, and is
always a blacklist of the few acts, never an allowlist of what is permitted** (ADR 0051). A
definition therefore names only what it forbids: `agents/reviewer.md` denies the built-in writers
and is read-only by contract, `agents/worker.md` denies nothing, and Codex CLI enforces its role
sandbox. Native Codex and Claude CLI workers retain host/tool permissions and target their assigned
worktree; neither path supplies a per-child read-only sandbox. A subagent is bound by the hook its own definition declares, or by the spawning
session's where it declares none.

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
`guard merge` as what it does instead. **Re-spelling is a legitimate detour, not an evasion**: the
rule is about the operation a command performs, and a command that merely spells a word performs
nothing. Passing a refused *operation* under another spelling is the evasion, and no role may do
it (`reference/worker.md`).

**Two operations the hook deliberately does not decide.** **Releasing** is not on the
orchestrator's list: `core.md` says releasing needs the human's authorization or the project's
standing delegation, and the orchestrator follows that page rather than a machine-readable record
of it. And an **orchestrator's push naming the default branch** is admitted with no carve-out and
no condition: founding means those first commits to land there, and once founding has applied
protection GitHub rejects the push server-side, which is the layer that check belongs to
(ADR 0052).

**What is outside this boundary stays outside.** Obfuscation, an interpreter script, a forged local
ref, an operation read from runtime data, a subagent spawned deliberately to run what the
spawner's own role refuses, and an MCP tool that acts outside the repository — every role reaches
every server the session has attached, and the hook reads commands, not tool calls — are not
modelled, and no rule here will be added for them: this guards the ordinary case and accepts the
residual (ADR 0051; the limitation ADR 0046 already stated). The remedy for the last is to not
attach such a server to a session that runs workers. What remains is the rest of the guard —
`guard merge`'s reviewed-head verification, branch protection, and the OS sandbox where the
implementation supplies one (`reference/external-agent.md`).
**A review finding of that class is a Note**, not a defect.

The worker definition pins a worker hook. The global hook resolves a pinned worker/reviewer role first,
then recognized worker/reviewer agent types, then a dispatched `DEVSTANDARD_ROLE`. An otherwise
unclassified child event with a nonempty `agent_id` and absent or `default` agent type uses the
worker rule; Codex-native children inherit no process role marker. Named Claude research children
retain the parent role, preserving a role’s own-subagents boundary. Codex research children still
take the worker fallback; that residual is accepted. Explicit reviewer bindings take precedence.
Both CLI dispatchers set `DEVSTANDARD_ROLE` only in the child process, overriding any
inherited value: installed startup hooks suppress the orchestrator context, and inherited tool
hooks use the assigned role. This delivery marker is not an authorization mechanism.
Codex CLI dispatch also pins the role in an inline hook configuration at the per-role sandbox
posture `reference/external-agent.md` sets, and grants worker network access for git/gh.
`guard codex-config --role worker|reviewer` prints the exact TOML override for inspecting that
hook. Because that hook is the fixed one from the dispatcher's own installation — whose presence
the dispatcher checks before creating a lane — the invocation passes Codex's
`--dangerously-bypass-hook-trust`, intended for automation that already vets hook sources. **The
bypass is invocation-wide, not limited to the fixed role hook.** Before dispatch the caller vets
every effective enabled hook source, including installed plugin hooks. It does not change persisted
trust, and Claude dispatch never receives it.

**The main session owns live executor verification before check 1.** Its Claude probe refused; the
[completed Codex probe on head f5d3c99](https://github.com/LeonJoeeee/devstandard/pull/223#issuecomment-5551952108)
also refused worker merge before execution through the dispatcher's own command, under the pinned
role hook above. That records the tested head; it does not establish enforcement for every command.
Skipped/untrusted hooks are not passing probes. Managed-hook policy can also exclude session hooks.
See the [Codex hook contract](https://developers.openai.com/codex/hooks)
and [Claude hook contract](https://code.claude.com/docs/en/hooks).

`.github/test-hard-edges.py` carries the table above as `REFUSED` and `ADMITTED`, swept across the
bare, quoted, here-doc, substitution and `cd … && …` positions, both tool-input formats and all
three roles, with a fixture that decides identically in a bare directory that is no repository at
all and inside one while every network call fails. The sweep also
asserts every refusal names its role's page and carries the re-spelling sentence. No probe
asserts a refusal for an obfuscated construction — that would encode a boundary this hook does not
claim.

## Founding a repository

Setup starts in an empty directory and needs no bootstrap of any kind: **there is no file to seed
and nothing to fill in.** The founding commits go straight to the default branch, which is what the
orchestrator's word list admits with no carve-out, and the last founding step — applying branch
protection — is what closes that door, server-side, for everyone including the account that opened
it. Founding is the orchestrator's work (`reference/prd.md` has the order).

That the push is admitted is not a claim that it is safe: `--force` and `--delete` are not on the
orchestrator's word list anywhere, and GitHub's branch protection is the layer that rejects a push
to a protected branch. `gh pr merge`, `git merge` and every other role's words keep their refusal
throughout.

## Branch protection

Read-only expected-state check, usable on any branch:

```sh
<plugin>/scripts/guard protection --repo OWNER/REPO --branch main
```

Human/main session only: append `--apply` to run the documented `gh api --method PUT` payload in
`scripts/guard`, then read it back. **The required contexts come from `--check`, repeated once per
name, and from nowhere else** — `--apply` with no name refuses rather than PUT an empty context
list, which would strip every required check off the branch. Without `--apply` the check is
read-only and needs no name at all: it verifies protection's shape.
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
