# Dispatching to an executor

Use the fixed dispatcher for a host-native worker or an explicitly selected CLI executor. The role source
and dynamic task packet carry the outcome, why, bounds, inputs, output and done-check. Give an
implementer write access to its own lane and let it run its loop; reviews and challenges are
read-only. The shared contracts are in `core.md`; role operations are in
`reference/orchestrator.md` and `reference/worker.md`.

Before a repo's first in-repo worktree, perform the pre-creation ignore check in
`reference/worktree-lifecycle.md`. Verify external review findings before acting on them.

## Native or CLI execution

**Dispatched work goes to the host's own subagent.** The human's instruction selects the executor
instead — for one dispatch, or standing until their next instruction. Explicit CLI execution makes
the other host available: Claude can launch Codex CLI and Codex can launch Claude CLI workers.
Codex CLI also supplies an OS-enforced sandbox; a different vendor supplies independent judgment. The standing choice lives with the
orchestrator that received it, not in any project file.

**Native bindings:** Claude uses `--implementation claude`; Codex uses
`--implementation codex-native` for workers (`reference/harness-codex.md`). Both prepare a spawn
receipt for the caller's actual host tool. Codex native spawn inherits host permissions and cannot
set a per-child read-only sandbox, so its gating review uses `--implementation codex`, the fresh
read-only CLI process. Native reviewer dispatch refuses before writes. Research outside a governed
lane and a worker's internal delegation remain the host's own subagent work.

Gating review or challenge always takes a fresh, independent read-only executor — a separate
process for Codex, a freshly spawned subagent otherwise; put required harness-only evidence in its
packet, never give it session history. For implementation, a hard requirement for Claude's capabilities selects Claude: native on its host, or the explicit `claude-cli` worker path from
Codex. Report an unavailable qualified implementation. A subagent also fits quick
read-only exploration whose answer belongs in the orchestrator context, or a piece smaller than its
brief. Any departure from the human's current choice is explained at handback; gating work has no
such departure.

No executor receives missing task context magically: brief it completely. Standalone
live-session lanes and workflow panels are outside the supported configuration. When Codex is
unavailable, use the fallback below only if it preserves the role and gate properties.

## Route it explicitly — model and effort follow the work

Set the model on every dispatch, and set the reasoning/effort level too where the tool has one.
Use this default ladder by kind of work, with two knobs: **model tier and reasoning effort**
(human ruling, 2026-09-09; ADR 0050). No tier is off-limits: the highest tiers are defaults for
the work that needs them.

| Kind of work | Codex | Claude |
|---|---|---|
| Final ruling on a dilemma, an irreversible judgment, an architecture-level acceptance | `gpt-6-astra` at `xhigh` | `fable` |
| Gating review (check 1, a design challenge) | `gpt-6-astra` at `high` | `opus` |
| Implementation, tests, bug fixing, conflict resolution | `gpt-5.6-sol` at `high` | `opus` |
| Wide scans, first-pass triage, evidence gathering | `gpt-5.6-terra` at `medium` or `low` | `sonnet` |
| Fixed-field extraction, list making, format conversion | `gpt-5.6-luna` at `low` | `haiku` |
| Counting, sorting, hashing and other deterministic operations | a script, not a model | a script, not a model |

The asymmetry is deliberate: the human's cost rationale is that Claude `fable` costs twice `opus`
per token and reviews are frequent, so ordinary Claude check 1 stays at `opus` and `fable` is
reserved for the top row. Codex `gpt-6-astra` is the everyday top and carries ordinary reviews
and design challenges. A gating review never runs below the tier that produced the work it
judges; an architecture-level review runs one tier above, using the top row's model/effort pair.

**Recursion depth never lowers the tier.** Route a subagent's subagent doing hard work by that
work, regardless of depth. When work returns stuck, ambiguous or unreliable, change one thing
in this order and never re-run unchanged:

1. Add the missing context.
2. Raise effort.
3. Raise the model one tier.
4. Cut the task smaller.
5. Take it to the human.

A question whose answer is irreversible or a genuine dilemma escalates straight to the top row.
When a knob is already at its highest setting, proceed to the next available change.
Before downgrading, ask whether a script can do it. Downgrade only for **high-volume,
low-difficulty** work, both knobs together, and only when its output can be checked mechanically
or spot-checked one tier up. The gating-review floor still applies.

A project's root `CLAUDE.md` or the issue naming a model overrides the table. The human's own
session model stays outside the method. Claude-native agents use tier aliases, never version
IDs. Every spawn names its model explicitly where the tool offers a model field; a tool with
no model control is the sole exception. The shipped worker and reviewer definitions carry
`model: opus` and `effort: high`; an ad hoc Claude spawn inherits the session's effort when its
tool offers no effort control. An unset model or effort is otherwise an invisible config-file
choice, so name both where supported.

The role TOML printed by `guard codex-config` carries `agents.default_subagent_model` and
`agents.default_subagent_reasoning_effort` matching the gating-review row. Dispatch passes each
assignment as its own `-c` override alongside the fixed role hook. An explicit spawn setting still
takes precedence over these subagent defaults; defaults never remove the explicit-spawn duty.

The table supplies routing defaults, not automatic task classification. The standing project
setting below is the model and effort a Codex dispatch carries, not the choice of executor;
project/issue overrides select departures.

**The standing setting on these projects is `-m gpt-6-astra -c model_reasoning_effort=high`** — the
human's ruling, effective 2026-09-05 (superseding the 2026-08-26 setting under ADR 0040), stated here and nowhere else. Pass it explicitly on every
Codex dispatch, review and challenge alike; the CI gate reads the record from this sentence, so a
change is this line and its date. A dispatch at another level is the human's to direct, and says
so in the handback.

## Sandbox by role

A review or a design challenge runs read-only — it has no reason to write, and an OS-enforced
sandbox makes that structural instead of a promise in the prompt. Codex CLI gets write access
scoped to its worktree. Claude CLI uses host/tool permissions with explicit `acceptEdits` and
noninteractive prompts; it does not supply Codex's per-role OS sandbox and cannot serve as a gating
reviewer. A native worker inherits the host's permissions; its dedicated
worktree and role bind where it works, not a per-child sandbox grant. A fresh native conversation
does not change that boundary. A "bypass all sandboxing" mode is never used. If a legitimately-needed action is blocked
by the sandbox, that is a stop-and-tell, exactly like any other blocked action — not a reason to
re-invoke with a looser flag.

## What it returns, and how that reaches the main session

A process-invoked agent returns through the dispatcher's output file. Keep the brief and output in
session scratch, never in the worktree; read the output, remove both best-effort, and post durable
evidence to the issue or PR. Claude stdout is captured as JSON Lines by the supervisor. Codex's `-o` file
is written by its CLI outside the sandboxed agent — the measured reason the dispatcher's
scratch is writable even though the agent itself cannot write there (`reference/out-of-repo-writes.md`).
For every rule in `reference/worker.md` that says *return the message in your output to whoever
launched you*, **that file is your output** — the same channel, in a different form. The caller reads that output and publishes durable evidence; do not assume another channel is watched.

Two consequences worth stating, because both have bitten:

- **It cannot ask.** Everything it needs must be in the brief. A `{PLACEHOLDER}` left unfilled does
  not get queried, it gets guessed at or worked around.
- **Anything it could not do comes back as prose, if at all.** Read the returned file before
  treating the task as done, and verify the done-check yourself rather than accepting its report.

## The record says which agent produced the work

Git's author field carries whoever's credentials are configured locally — the human's, for any local
agent. So nothing in the record distinguishes a diff another vendor's agent wrote unless it is put
there: a trailer on the commit, and a line in a review verdict naming its reviewer.

This matters most for a gating review. If a different vendor's independent judgment is the reason to
use one, a record that cannot say which vendor produced a verdict cannot support that reason later.

**This is a discipline expectation with no gate behind it, and it is the kind that fails.** Where
this method has made a rule stick, it did so by putting the instruction where the act falls due
rather than where the work is commissioned (`reference/code-review-prompt.md`). The equivalent here
is to write the attribution into the dispatch brief — so the agent emits it — rather than to
remember afterwards.

## When it is not there

Where the human's choice is Codex, check before dispatching; if the tool is missing,
unauthenticated, or errors out, fall back to your harness's own executor **where it can keep the
gate's properties** — fresh, process-isolated, read-only for a review — and say so where the work
is handed back. That fallback is the caller re-dispatching explicitly under the other
implementation: the dispatcher never substitutes one for the other. Where no available executor
can keep those properties, the gate is **blocked, not lowered**: stop and tell the human. **Its absence
never lowers a bar.** Skipping a review, or accepting a weaker one, because an executor was unavailable is the availability-keyed
exception this method rejects everywhere else.

## Fixed dispatcher

Run the installed plugin's `scripts/dispatch` from the target checkout (Python 3.9+, `git`,
authenticated `gh`; Codex process dispatch supports macOS and Linux). It reads this page's standing setting at
runtime. `--implementation claude|codex-native|codex|claude-cli` overrides a default of `claude`; pass the host
binding or human's standing choice explicitly on each launch. A Codex host uses `codex-native` for
workers and `codex` for gating review. `--implementation codex` where Codex is
not installed refuses plainly rather than falling back, and a Codex startup failure is captured,
never silently retried under another implementation.
The dispatch does not carry superpowers: the role pages' `superpowers:<skill>` pointers resolve
only where that plugin is installed on the executing host, the Codex host included.

```sh
git fetch origin
<plugin>/scripts/dispatch 123 --purpose worker --base origin/main
<plugin>/scripts/dispatch 123 --purpose worker --continue --brief <continuation-file>
<plugin>/scripts/dispatch 123 --purpose worker --continue --pr 124 --brief <continuation-file>
<plugin>/scripts/dispatch 123 --adopt --base origin/main --branch <existing-branch> --worktree <existing-worktree> --pr 124
<plugin>/scripts/dispatch 123 --purpose reviewer --packet <complete-review-packet>
<plugin>/scripts/dispatch 123 --cleanup --pr 124
# Codex host's native worker:
<plugin>/scripts/dispatch 123 --purpose worker --base origin/main --implementation codex-native
```

The issue must contain nonempty Markdown heading sections `Goal`, `Bounds`, and `Done-check`.
Missing fields and unresolved template slots are refused before any lane is created or adopted.
A new worker lane also requires green default-branch CI: red or unreported refuses lane creation
and publication, while recovery inside an existing lane stays available while main is red. Green
means every check the head reports concluded success, neutral or skipped, and that at least one
reported. That is the whole rule — no list of check names is configured anywhere — so no project
renames its CI job to satisfy this gate, and its refusal names the checks it observed.
Creating or adopting a lane also requires a named `--base`; fetch it first. New branch/worktree
defaults are deterministic and recorded: `task/ISSUE-TITLE` and
`PROJECT/.claude/worktrees/ISSUE-TITLE`, with a sanitized title. Override with
`--branch` and `--worktree`; in-project worktrees must already be ignored. `--project` selects the
target checkout when the command is invoked elsewhere. Its `CLAUDE.md` copy-list and baseline
procedure remain the worker's receipt duties.

For a hand-made lane, `--adopt --base REF --branch B --worktree W [--pr N]` records its identity
without launching an executor or creating a branch/worktree. The explicit branch and linked
worktree must already exist in the target repository; mismatches are refused.
The optional PR must name that branch. Adoption refuses an existing active lane record; subsequent
reviews and continuations use that record as usual. Invoke adoption separately from dispatch.

GitHub issue comments hold the lane identity and each run's implementation, purpose, model, PID or
native-spawn status, and scratch paths. A Codex CLI run uses a Python supervisor started
in a new OS session, with stdin closed and SIGHUP ignored; no external `setsid` or `nohup` is needed.
The child receives its assigned `DEVSTANDARD_ROLE`, so an installed plugin cannot inject the
orchestrator set into that run. JSON stdout gives `output` (final response), `log` (combined process output), and
`completion` (atomic exit-code file). A missing marker means running or lost, never done; read the
response and verify the PR/evidence. After publishing durable evidence, the caller removes each
run's scratch directory. Scratch paths are observations, not durable task state.

The worker prompt expands `reference/worker.md` and appends the issue and lane packet;
`--brief` adds required inputs/output detail. Reviewers reuse the recorded lane, receive the
structured `--packet` produced by `scripts/review-packet assemble`, and run read-only. The dispatcher
validates its template against the current fenced contract, fills reviewer identity from the selected
executor, and renders each slot once. It never scans quoted evidence for template syntax or Diff
headings. Old hand-assembled text packets must be assembled again; they do not identify control slots
unambiguously. **Review packets**, below, owns assembly, green-head admission, and publication.
Continuation requires a `--brief` containing the blocking goal gaps. Before a PR exists,
`--continue --brief FILE` reuses the recorded branch/worktree. Once a PR is recorded or found on
GitHub for that branch, supply the existing open `--pr`; a recorded PR cannot be replaced by
another. A continuation into a delivered lane is gated on that PR's review history and needs the
orchestrator's recorded ruling, under the round-accounting contract in `reference/hard-edges.md`.
Both forms retain the lane; CLI implementations start a fresh process and Codex-native prepares a
fresh child. A live prior executor blocks another dispatch into the lane.

**Codex-native is a prepared worker spawn.** `--implementation codex-native` writes
`native-spawn.json`, a semantic receipt with format `devstandard-codex-native-v1`, the full worker
role plus task in `message` after a canonical-read preamble, `fresh_conversation: true`, the assigned
`worktree` and native-tool obligations. The absolute `brief` and `brief_sha256` also appear in the
run record; `reference/harness-codex.md`, Native workers, owns the required read and verification.
Its `model` and `reasoning_effort` use the same standing setting as Codex CLI dispatch.
It reports `awaiting-agent-tool`, without inventing a handle, PID or completion marker.
Pass the complete message to the actual native tool, using its fresh-conversation setting
(`fork_context=false` in v1 or `fork_turns="none"` in v2), passing the receipt's `model` and
`reasoning_effort` explicitly. A tool without those controls, or rejecting them, is unsupported;
report it rather than substituting inherited settings. Supply the other fields the tool requires.
Record the returned native handle on the issue and use the host's native wait/status tools to
observe it. The script cannot invoke or observe a host tool itself. A child inherits developer
instructions, cwd and permissions even with no forked conversation; the worker must use the named
worktree explicitly. Codex does not load the Claude agent definitions, and this receipt is not
Claude Agent JSON. Reviewer purpose and `--resume` refuse for `codex-native`.

**Claude CLI is an explicit worker process.** `--implementation claude-cli` lets Codex dispatch a
Claude worker through the installed, normally authenticated CLI. It loads this plugin for that
process, passes the complete role/task and assigned worktree, and uses explicit `acceptEdits` with
noninteractive permission prompts, without a permission bypass. Model and effort come from the
shipped Claude worker definition. Its tool permissions are not a per-child OS sandbox; the worker
must keep writes in its lane. Reviewer purpose and native resume are unsupported. It uses a fresh
process with no session persistence. Logs and completion follow the Codex CLI observation contract;
the output preserves the emitted Claude event stream as JSON Lines. Read every `result` record and its
`permission_denials`, including results preceding background-agent completion. A denied required
action is blocked and must be surfaced even if the process exits successfully.

**Claude is a prepared spawn, not a shell-launched agent.** With `--implementation claude`, JSON
stdout names an `instruction` file containing the Agent-tool arguments for `devstandard:worker`
or `devstandard:reviewer`. The caller invokes that tool in Claude Code and records its returned
native handle on the issue; the command cannot invoke a tool in another session or observe that
handle. It reports `awaiting-agent-tool`, never a running PID. A Claude worker continuation can
also pass `--resume HANDLE`; omit it for a fresh executor. Reviewers always start fresh. Agent
definitions supply Claude's static role and model. For a Claude reviewer, the dispatcher verifies
locally resolvable review-base, head, and convention-base pins from the structured slots, then captures
`git diff --name-status`, `git diff --stat`, the full diff, and convention-base blobs for every changed
path (both sides of renames, all extensions). External diff drivers, text conversion, and color are
disabled. Command records preserve exit codes and exact output as arrays of bounded text chunks;
concatenate each array without a separator to recover the original output. An absent convention-base
path retains its failed `git show` result; other command failures refuse dispatch before publication.
The Agent-tool prompt points to `brief.txt` for an IN FULL read: the contract, packet, and evidence are
readable artifacts, without a giant escaped prompt line for the caller to copy. Emitting that
instruction does not exercise the native path.

For either native implementation, `--native-finished` attests that **all outstanding Claude and
Codex-native handles in the recorded lane have finished**. It bypasses their liveness checks for
that operation only; it does not persist completion, clear another lane or bypass either live CLI
process. Supply it on each subsequent operation needing that attestation, never as a standalone
command. A prepared receipt or a caller's guess is not evidence that a handle finished.

## Review packets

The installed plugin's `scripts/review-packet` uses Python, `git`, and authenticated `gh`. Run it from
the target checkout; `--project` selects another checkout root. Its issue must already have a lane
record matching the PR. The convention base is that lane's pre-work base SHA; the review base and
head are the PR's current GitHub base/head SHAs, fetched and checked locally. The predicate's own
review/convention-base slots receive those pins too, preserving its complete counted payload. Beside
those slots the packet carries the complete issue body as quoted evidence, whole and untruncated;
`reference/code-review-prompt.md` states its standing for the verdict. All observed checks
must pass and classic branch-protection required contexts must be reported. Missing, failing,
pending, cancelled, or skipped checks refuse assembly. GitHub state is re-read to reject changes
during assembly. Configure required checks on the repository; this command never changes protection.

```sh
<plugin>/scripts/review-packet assemble 124 --issue 123 --architecture-level no --output <session-scratch>
<plugin>/scripts/review-packet start 124 --issue 123 --architecture-level no --output <session-scratch>
# Codex host:
<plugin>/scripts/review-packet start 124 --issue 123 --architecture-level no --output <session-scratch> --implementation codex
<plugin>/scripts/review-packet status 124 --issue 123
<plugin>/scripts/review-packet publish 124 --issue 123 --attempt <comment-id>
<plugin>/scripts/review-packet rule 124 --issue 123 --decision continue --reason '<blocking goal gap or missing evidence>'
```

`assemble` writes `packet.json` and the readable `packet.txt` without starting a round. `start`
reassembles from current sources, reserves a review attempt on the PR, invokes the fixed dispatcher,
and returns immediately. The returned `attempt` is the PR comment ID. Codex's detached return handler
publishes the whole output when its completion marker arrives; a failed process with no verdict is
recorded as a failed attempt rather than a returned verdict — the distinction round accounting turns
on (`reference/hard-edges.md`). A nonzero executor exit cannot yield acceptance.
Publication replaces the reservation with `## Merge check 1 — round N`, the exact-head metadata,
and the unedited verdict. Repeating `publish` is idempotent. A changed head does not suppress the old
head's verdict or reset the count; that verdict cannot accept the new head.

For Claude — the command-line default — `start` returns the dispatcher's Agent instruction; invoke it and
return the whole result using `publish --attempt ID --verdict FILE`. A start is a dispatch into the
lane and refuses on the same liveness condition as any other (above), so use `--native-finished` on
a subsequent start only under the fixed dispatcher's all-handles-finished attestation.

`--accepted-spec SHA` requires a reachable blob whose SHA was published on the issue, and includes
its contents in the packet; absent that argument the slot is `NONE`. The caller supplies the explicit
`--architecture-level yes|no` classification. `--rebase-result FILE` consumes the guard comparison JSON as
review evidence; it neither computes the comparison nor waives green-head admission or full review.
This ordinary assembler sets CI fallback to `NONE`; a declared fallback remains the merging
session's separate procedure under `reference/ci-cannot-run.md`.

GitHub PR comments are the durable round record; pre-existing numbered check-1 verdicts count too,
so adopting the assembler cannot reset a PR’s cap. An unnumbered legacy heading requires history
reconciliation before dispatch. A returned verdict closes its attempt, and the next
start requires an explicit `rule --decision continue --reason ...`. Notes alone never justify a
round. `reference/hard-edges.md` states the round-accounting contract these commands enforce — what
consumes a round, the cap, the orchestrator's first ruling, and how each Floor result routes;
`rule --decision` takes `continue`, `merge-as-is`, `rewrite`, `abandon` or `change-route`, and a
ruling is recorded rather than merged. Once the cap is reached every further start refuses.
Directional outcomes, an architecture merge ruling, or `--human-touchpoint`
require `--human-authorization` with the durable GitHub sign-off URL. The caller is responsible for
classifying the touchpoint and verifying the human's authority; `reference/hard-edges.md` owns enforcement at merge.

A restarted caller uses `status` and the issue's dispatcher records. If a return handler stopped,
`publish --attempt ID` resumes publication from recorded executor output. A reservation without a
recorded run, a lost supervisor, missing scratch, or a publication error requires the orchestrator to
reconcile the observable issue-side run before another launch; do not infer a verdict or reset the
rounds. A verdict too large for one GitHub comment is refused whole with its output retained for
escalation, never truncated. After durable publication, remove caller and dispatcher scratch
best-effort. Keep the branch and worktree for the merging session.

Cleanup runs from outside the lane. It requires the merged PR's branch and exact head, refuses
tracked, untracked, or ignored leftovers, prints the base-relative commit inventory, then removes
the worktree, deletes the local branch, and prunes. A squash/rebase merge can require `-D`: inspect
the printed inventory and supply `--force-delete` only with the caller's explicit authorization
under `reference/worktree-lifecycle.md`. `--discard` is the caller's explicit discard instruction,
for example for a disposable smoke lane; it does not imply permission to force-delete commits.
Remote branch removal remains the merging caller's duty. Never clean a lane on process exit alone.

## Verified mechanics

The invocations themselves are `scripts/dispatch`'s, above — that script is their operative
statement, and nothing here restates the shape it builds. What follows is verified by use against
`codex-cli` specifically. **Another tool's flags are unverified until someone has run them the same
way.**

Four gotchas, each found by running it and none of them in the tool's help text:

- **Run it in the foreground of the detached supervisor** (the fixed dispatcher above does this). Backgrounded directly, it waits on stdin, echoes the prompt, and exits 0
  having done nothing. `< /dev/null` alone does not fix it.
- **A linked worktree needs both `--add-dir <repo>/.git` and
  `--add-dir <repo>/.git/worktrees/<name>` to commit.** Its `.git` file points into the parent repo,
  and the grant through `.git` is **not recursive**, so the common gitdir grant does not make the
  per-worktree gitdir writable. Without both, the work can complete while every staging or commit
  operation fails. A plain clone has no separate per-worktree gitdir and keeps its single
  `--add-dir <clone>/.git` grant.
- **`-C` and `-s` do not exist on the `review` subcommand**, and that subcommand cannot take a custom
  prompt alongside a base branch. Use plain `exec` and paste this method's own reviewer prompt.
- **Watch the output's shape, not just its content.** Literal `\n` sequences instead of newlines in a
  commit message, and quote characters that do not match the surrounding file, have each appeared on
  some runs and not others. Intermittent is worse than systematic: a merged commit message can never
  be corrected.

## Guarded executor and merge edges

`scripts/dispatch` pins each Codex role's PreToolUse configuration in the invocation itself — and a
hook named in argv is not by itself a live refusal, so enforcement is claimed only from an observed
one. `reference/hard-edges.md` owns hook trust and what a probe does and does not establish, the role
hook's word-list rule and the residual it deliberately leaves outside, the exact merge/rebase
commands, the architecture-level sign-off, and the round-accounting contract the review
commands above enforce.
