# Dispatching to an executor

Use the fixed dispatcher for one Claude-native or Codex-process worker/reviewer. The role source
and dynamic task packet carry the outcome, why, bounds, inputs, output and done-check. Give an
implementer write access to its own lane and let it run its loop; reviews and challenges are
read-only. The shared contracts are in `core.md`; role operations are in
`reference/orchestrator.md` and `reference/worker.md`.

Before a repo's first in-repo worktree, perform the pre-creation ignore check in
`reference/worktree-lifecycle.md`. Verify external review findings before acting on them.

## When a subagent, when Codex

Where Codex is installed, use it for dispatched work. Gating review or challenge always takes
a fresh, independent read-only process; put required harness-only evidence in its packet, never
give it session history. For implementation, a hard requirement for Claude's own capabilities
selects a Claude-native subagent. A subagent also fits quick read-only exploration whose answer
belongs in the orchestrator context, or a piece smaller than its brief. Any other departure from
the implementation default is explained at handback; gating work has no such departure.

Neither executor receives missing task context magically: brief it completely. Keep a worker's
read-only helper outside this dispatcher and follow `reference/worker.md`'s executor-specific helper rule.
Standalone live-session lanes and workflow panels
are outside the supported configuration. When Codex is unavailable, use the fallback below
only if it preserves the role and gate properties.

## Route it explicitly — the level is the human's, the explicitness is not

Set the model on every dispatch, and set the reasoning/effort level too where the tool has one.
**Which level is the human's call**, like their own session model; that this
method does not choose for them is deliberate. What it does require is that the choice be *made*,
visibly, at the dispatch.

Claude-native agents use tier aliases, never version IDs: `opus` is the default and ceiling;
only mechanical work may use `sonnet` or `haiku`. Set the model on every spawn that offers a
model field; a tool with no model control is the sole exception. The shipped worker and reviewer
definitions fix `opus`. This routing ceiling does not extend to another vendor's model names.

The failure this prevents is not a wrong level. It is that a tool with a config file supplies both
to any invocation that omits them, so an unset flag is not "no choice" — it is a choice made
somewhere no reviewer will look.

**The standing setting on these projects is `-m gpt-6-astra -c model_reasoning_effort=high`** — the
human's ruling, effective 2026-09-05 (superseding the 2026-08-26 setting under ADR 0040), stated here and nowhere else. Pass it explicitly on every
Codex dispatch, review and challenge alike; the CI gate reads the record from this sentence, so a
change is this line and its date. A dispatch at another level is the human's to direct, and says
so in the handback.

## Sandbox by role

A review or a design challenge runs read-only — it has no reason to write, and an OS-enforced
sandbox makes that structural instead of a promise in the prompt. An implementing run gets write
access scoped to its own worktree, which is how one-writer-per-worktree already works for any
executor. A "bypass all sandboxing" mode is never used. If a legitimately-needed action is blocked
by the sandbox, that is a stop-and-tell, exactly like any other blocked action — not a reason to
re-invoke with a looser flag.

## What it returns, and how that reaches the main session

A process-invoked agent has no channel back except what you give it. Put both the relative `brief.txt`
the command reads and its `-o` outfile in the dispatcher's session scratch, never in the worktree;
read the outfile, remove both best-effort, and post anything durable to the issue or PR. The outfile
is written by the dispatching CLI outside the sandboxed agent — the measured reason the dispatcher's
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

Check before dispatching; if the tool is missing, unauthenticated, or errors out, fall back to your
harness's own executor **where it can keep the gate's properties** — fresh, process-isolated,
read-only for a review — and say so where the work is handed back. Where no available executor
can keep those properties, the gate is **blocked, not lowered**: stop and tell the human. **Its absence
never lowers a bar.** Skipping a review, or accepting a weaker one, because an executor was unavailable is the availability-keyed
exception this method rejects everywhere else.

## Fixed dispatcher

Run the installed plugin's `scripts/dispatch` from the target checkout (Python 3.9+, `git`,
authenticated `gh`, and Linux `setsid`/`nohup` for Codex). It reads this page's standing setting at
runtime. `--implementation codex|claude` overrides the default: Codex when installed, Claude
otherwise. A Codex startup failure is captured, never silently retried under another implementation.
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
```

The issue must contain nonempty Markdown heading sections `Goal`, `Bounds`, and `Done-check`.
Missing fields and unresolved template slots are refused before any lane is created or adopted.
A new worker lane also requires green default-branch CI: red or unreported refuses lane creation
and publication, while recovery inside an existing lane stays available while main is red.
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
native-spawn status, and scratch paths. Codex runs in the foreground of a `setsid nohup` supervisor,
with stdin closed. JSON stdout gives `output` (final response), `log` (combined process output), and
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
Both forms retain the lane and start a fresh Codex process. A live prior executor blocks
another dispatch into the lane.

**Claude is a prepared spawn, not a shell-launched agent.** With `--implementation claude`, JSON
stdout names an `instruction` file containing the Agent-tool arguments for `devstandard:worker`
or `devstandard:reviewer`. The caller invokes that tool in Claude Code and records its returned
native handle on the issue; the command cannot invoke a tool in another session or observe that
handle. It reports `awaiting-agent-tool`, never a running PID. `--native-finished` attests that
**all outstanding Claude handles in the recorded lane have finished**, including workers and
reviewers. It bypasses every prior Claude run's liveness check for that operation only; it does
not persist completion, clear another lane, or bypass a live Codex process. Supply it alongside
each subsequent lane operation that needs this attestation, never as a standalone command.
A worker continuation can
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

## Review packets

The installed plugin's `scripts/review-packet` uses Python, `git`, and authenticated `gh`. Run it from
the target checkout; `--project` selects another checkout root. Its issue must already have a lane
record matching the PR. The convention base is that lane's pre-work base SHA; the review base and
head are the PR's current GitHub base/head SHAs, fetched and checked locally. The predicate's own
review/convention-base slots receive those pins too, preserving its complete counted payload. All observed checks
must pass and classic branch-protection required contexts must be reported. Missing, failing,
pending, cancelled, or skipped checks refuse assembly. GitHub state is re-read to reject changes
during assembly. Configure required checks on the repository; this command never changes protection.

```sh
<plugin>/scripts/review-packet assemble 124 --issue 123 --architecture-level no --output <session-scratch>
<plugin>/scripts/review-packet start 124 --issue 123 --architecture-level no --output <session-scratch>
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

For Claude, `start --implementation claude` returns the dispatcher's Agent instruction; invoke it and
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
one. `reference/hard-edges.md` owns hook trust and what a probe does and does not establish, the
exact merge/rebase commands, the configurable authorization record, and the round-accounting
contract the review commands above enforce.
