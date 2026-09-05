# Dispatching to an external agent

An agent invoked as a process rather than through your harness — such as a `codex exec`
launched by Claude Code — is an admissible executor wherever this method would
hand work to a fresh subagent: implementing a task, reviewing a diff, challenging a design. It is a
choice of *executor* at rung 2, not a new rung on the ladder — it does not reach into a workflow
run's agents and does not replace a separate live session — and **not a dependency**: a project
without one loses nothing, because every rung keeps the executor it already had.

On these projects **Codex is the standing external executor** (ADR 0045 for the topology, ADR 0040
for the preference below); the
neutrality above stands for any other tool. **The brief is where the worker constraints live —
nothing on the target machine pre-arms them**: what makes the dispatched process a worker is the
filled brief you paste, nothing else. And dispatching to an external agent is dispatching to an
*agent* (#155/#156): brief it like a subagent — the outcome, the why, the boundaries, inputs and
outputs, the done-check — grant the access the work needs (its own worktree, write access for
implementation), and let it run its own loop. **Read-only is for gating reviews and challenges,
never the default for real work**; a keystroke-scripted brief is the dispatcher overstepping into
the worker's *how* (the issue-writing rule — outcome and why, never the how — extended to external
dispatch). Before dispatching into a repo whose first in-repo worktree this would be, run the
pre-creation ignore check (`core.md`'s worktree rule). And **an external reviewer's findings are
verified before acting on them, never auto-applied** — the same stance this method takes toward
every review bot.

**Almost nothing here is new rule.** A worker never merges, one writer per worktree, done claims
carry evidence, every gating review gets a clean reviewer, the reviewed diff is the merged diff —
all of that is already blind to who executes, and stays exactly as written. What follows is only
what the harness would otherwise have handled for you.

## When a subagent, when Codex

Pick the venue first, as `core.md` says — in this session, rung 2, a workflow run, or a separate live
session; this section decides only the **rung-2 executor** — a separate live session stays the lane
for work that cannot be fully specified up front, and a workflow run keeps its own agents, its
review panel included (that panel is workflow-native, and this rule does not reach into a run). Both
candidates sit at rung 2 under the same rules. **Where Codex is installed, use it for dispatched work
— a harness-native subagent only where the work especially suits one** (the human's ruling, ADR
0040). The lists below are that rule, not a menu. Two tie-breaks: **gating work always takes the
fresh process** — a review or challenge is never "quick exploration", and one that needs a
harness-only source gets that source's output folded into the report it receives (one of the three
artifacts `core.md`'s reviewer rule allows — never a fourth) rather than a subagent; and for
**implementation**, a hard capability need (this harness's own rung-2 mechanisms) wins — a subagent,
because the other executor cannot do it.

**Codex — the default:**
- **Dispatched implementation** — a fully specified task that needs a real agentic loop: its own
  worktree, write access, its own PR driven to green. It runs the worker side of the ceremony through
  a PR whose checks are green or handed back unreported — never red — and leaves this session's
  context untouched.
- **A gating review or a design challenge** — what the gate needs is a fresh, process-isolated,
  read-only run: no history, and the sandbox enforced by the OS rather than promised in a prompt.
  A second vendor's judgment comes on top for the Claude Code orchestrator. The record names which
  agent gave the verdict.

**A harness-native subagent — only when** (a rung-2 subagent is always fresh — `core.md`'s ladder —
so either executor starts cold and everything it needs goes in the brief; neither can ask):
- **Quick read-only exploration** whose answer belongs in this context — the dispatch overhead (a full
  brief, a separate process, an output file to read back) outweighs the work.
- Work that needs **this harness's own rung-2 mechanisms** — `EnterWorktree`, MCP servers configured
  here. (A need for the Workflow tool is not a rung-2 exception: it selects rung 3, another venue.)
- A piece **small enough that the brief would be longer than the diff**.

A subagent for an implementation task outside that list is a departure — say why in the handback
(gating work has no such departure: the tie-break above is absolute). Where Codex is
not installed, the preference above does not apply: another installed process agent stays admissible
under the opening rule, and otherwise the harness's own executor does all of it ("When it is not
there", below).

## Route it explicitly — the level is the human's, the explicitness is not

Set the model on every dispatch, and set the reasoning/effort level too where the tool has one.
**Which level is the human's call**, like their own session model and their quota budget; that this
method does not choose for them is deliberate. What it does require is that the choice be *made*,
visibly, at the dispatch.

The failure this prevents is not a wrong level. It is that a tool with a config file supplies both
to any invocation that omits them, so an unset flag is not "no choice" — it is a choice made
somewhere no reviewer will look. The cap this method puts on agents it spawns through its own
harness does not carry over: another vendor's model names are not this one's tiers.

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
For every rule in `reference/worker-brief.md` that says *return the message in your output to whoever
spawned you*, **that file is your output** — the same channel, in a different form. A separate live
session's channel (a comment on the issue) does not apply; nothing is watching for one.

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

The worker prompt expands `reference/worker-brief.md` and appends the issue and lane packet;
`--brief` adds required inputs/output detail. Reviewers reuse the recorded lane, receive the caller's
complete `--packet` unchanged plus the task packet, and run read-only. Packet assembly, current-head
CI admission, and whole-verdict publication belong to the caller. Do not give a partial packet.
Continuation requires a `--brief` containing the blocking goal gaps. Before a PR exists,
`--continue --brief FILE` reuses the recorded branch/worktree. Once a PR is recorded or found on
GitHub for that branch, supply the existing open `--pr`; a recorded PR cannot be replaced by
another. Both forms retain the lane and start a fresh Codex process. A live prior executor blocks
another dispatch into the lane.

**Claude is a prepared spawn, not a shell-launched agent.** With `--implementation claude`, JSON
stdout names an `instruction` file containing the Agent-tool arguments for `devstandard:worker`
or `devstandard:reviewer`. The caller invokes that tool in Claude Code and records its returned
native handle on the issue; the command cannot invoke a tool in another session or observe that
handle. It reports `awaiting-agent-tool`, never a running PID. Once the native task has finished,
the caller supplies `--native-finished` on subsequent lane operations. A worker continuation can
also pass `--resume HANDLE`; omit it for a fresh executor. Reviewers always start fresh. Agent
definitions supply Claude's static role and model; reviewer packets must include evidence readable
with their restricted tools. Emitting these instructions does not exercise the native path.

Cleanup runs from outside the lane. It requires the merged PR's branch and exact head, refuses
tracked, untracked, or ignored leftovers, prints the base-relative commit inventory, then removes
the worktree, deletes the local branch, and prunes. A squash/rebase merge can require `-D`: inspect
the printed inventory and supply `--force-delete` only with the caller's explicit authorization
under `reference/worktree-lifecycle.md`. `--discard` is the caller's explicit discard instruction,
for example for a disposable smoke lane; it does not imply permission to force-delete commits.
Remote branch removal remains the merging caller's duty. Never clean a lane on process exit alone.

## Verified mechanics

Verified by use against `codex-cli` specifically. **Another tool's flags are unverified until
someone has run them the same way** — treat the shape below as an example of what to establish, not
as a spec that generalises.

```sh
cd <dispatcher-session-scratch>
codex exec -s read-only -m <model> -c model_reasoning_effort=<level> \
  -C <worktree> -o review-output.txt "$(cat brief.txt)" < /dev/null      # a review; brief/outfile: dies-with-the-task

codex exec -s workspace-write -m <model> -c model_reasoning_effort=<level> \
  -C <worktree> --add-dir <repo>/.git \
  --add-dir <repo>/.git/worktrees/<name> -o worker-output.txt "$(cat brief.txt)" < /dev/null  # brief/outfile: dies-with-the-task
```

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
