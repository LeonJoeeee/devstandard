# Dispatching to an external agent

An agent from another vendor — invoked as a process rather than through your harness — is an
admissible executor anywhere this method would hand work to a fresh subagent or a separate session:
implementing a task, reviewing a diff, challenging a design. It is a choice of *executor*, not a new
rung on the ladder, and **not a dependency**: a project without one loses nothing, because every
rung keeps the executor it already had.

**Almost nothing here is new rule.** A worker never merges, one writer per worktree, done claims
carry evidence, every gating review gets a clean reviewer, the reviewed diff is the merged diff —
all of that is already blind to who executes, and stays exactly as written. What follows is only
what the harness would otherwise have handled for you.

## Route it explicitly — the level is the human's, the explicitness is not

Set the model on every dispatch, and set the reasoning/effort level too where the tool has one.
**Which level is the human's call**, like their own session model and their quota budget; that this
method does not choose for them is deliberate. What it does require is that the choice be *made*,
visibly, at the dispatch.

The failure this prevents is not a wrong level. It is that a tool with a config file supplies both
to any invocation that omits them, so an unset flag is not "no choice" — it is a choice made
somewhere no reviewer will look. The cap this method puts on agents it spawns through its own
harness does not carry over: another vendor's model names are not this one's tiers, and hard-coding
them here would rot on their release schedule, not yours.

## Sandbox by role

A review or a design challenge runs read-only — it has no reason to write, and an OS-enforced
sandbox makes that structural instead of a promise in the prompt. An implementing run gets write
access scoped to its own worktree, which is how one-writer-per-worktree already works for any
executor. A "bypass all sandboxing" mode is never used. If a legitimately-needed action is blocked
by the sandbox, that is a stop-and-tell, exactly like any other blocked action — not a reason to
re-invoke with a looser flag.

## What it returns, and how that reaches the main session

A process-invoked agent has no channel back except what you give it: capture its final message to a
file and read that. For every rule in `reference/worker-brief.md` that says *return the message in
your output to whoever spawned you*, **that file is your output** — the same channel, in a different
form. A separate live session's channel (a comment on the issue) does not apply; nothing is watching
for one.

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
harness's own executor and say so where the work is handed back. **Its absence never lowers a bar.**
Skipping a review, or accepting a weaker one, because an executor was unavailable is the
availability-keyed exception this method rejects everywhere else.

## Verified mechanics

Verified by use against `codex-cli` specifically. **Another tool's flags are unverified until
someone has run them the same way** — treat the shape below as an example of what to establish, not
as a spec that generalises.

```sh
codex exec -s read-only -m <model> -c model_reasoning_effort=<level> \
  -C <worktree> -o <outfile> "$(cat brief.txt)" < /dev/null      # a review

codex exec -s workspace-write -m <model> -c model_reasoning_effort=<level> \
  -C <worktree> --add-dir <repo>/.git -o <outfile> "$(cat brief.txt)" < /dev/null
```

Four gotchas, each found by running it and none of them in the tool's help text:

- **Run it in the foreground.** Backgrounded, it waits on stdin, echoes the prompt, and exits 0
  having done nothing. `< /dev/null` alone does not fix it.
- **`--add-dir <repo>/.git` is required to commit inside a linked worktree.** A worktree's `.git` is
  a file pointing into the parent repo, which the working-directory flag never covered — so the work
  completes and the commit fails.
- **`-C` and `-s` do not exist on the `review` subcommand**, and that subcommand cannot take a custom
  prompt alongside a base branch. Use plain `exec` and paste this method's own reviewer prompt.
- **Watch the output's shape, not just its content.** Literal `\n` sequences instead of newlines in a
  commit message, and quote characters that do not match the surrounding file, have each appeared on
  some runs and not others. Intermittent is worse than systematic: a merged commit message can never
  be corrected.
