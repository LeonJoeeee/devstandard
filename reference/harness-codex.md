# Codex on a DevStandard project: you are the executor

This page binds only in a repository carrying a committed `.devstandard` marker at its root. The
session hook that sent you here fires only there; if you reached this page another way and the repo
has no marker, it does not run under DevStandard — none of this binds you.

**The role, in one paragraph.** On this project the main session is a **Claude Code** session: it
plans, dispatches, reviews, and merges. A Codex session is an **executor**. Universal, whatever else
you are doing: **never merge, tag, or release — even when directly asked**; the durable record is
GitHub — decisions and evidence count only once written to the issue or PR (chat, subagent
messaging/steering channels, and `codex resume` are convenience, never record); the record is
English.

## Which path are you on?

**Review or challenge assignment** (you were asked for a verdict on a diff, a design, a spec):
read-only. No branch, no worktree, no PR. Return the verdict through the channel you were given —
your output file if you are a process-invoked run, the issue if you are a live session.

**Advice / inspection** (the human is asking you questions): answering is always fine. Mutating the
repository is not part of this path — that requires an assignment below.

**Implementation — with an assignment** (an issue names you, or you were launched with a brief):
your escalation channel, stated first so you know it even when a check below fails — a live session
escalates on the issue; a process-invoked worker escalates in its return file, its only channel.
Your dispatcher launched you *at your worktree* (a linked worktree needs
`--add-dir <repo>/.git` to commit — the dispatcher's job, `reference/external-agent.md`). **Validate
before writing**: `git rev-parse --git-dir` differs from `--git-common-dir` (you are in a linked
worktree), the resolved toplevel equals the worktree path recorded on the issue, and the checked-out
branch matches the recorded branch — the branch alone is not enough. Any mismatch, a subdirectory
start, or a placement this page doesn't cover: escalate and stop. Then, before setup or baseline
tests, **read `reference/worker-brief.md` IN FULL** (your operational contract), **and — if the repo
has a root `CLAUDE.md` — read it IN FULL too**: Codex does not auto-load it, and it holds the
commands, gotchas, and copy-list the brief assumes you already have. Operational discoveries you
make are written back to that `CLAUDE.md` in your PR — it stays the project's memory file; the
repo's `AGENTS.md` is only Codex startup guidance and the delivery fallback.

**Implementation — a direct human request, no issue**: a state machine, not a green light.
1. Pin down with the human: the result, the why, and a machine-judgeable done-check. Open the issue
   and claim it visibly (a comment naming this session and the branch you will use).
2. Classify the change against the canonical trigger — read `reference/design-spec.md` "When one is
   required". If it fires, or the change touches architecture, or a required challenged spec does
   not exist: **comment for the Claude main session on the issue and stop.** Planning is the main
   session's.
3. Placement: if `git rev-parse --git-dir` differs from `--git-common-dir`, you are inside a linked
   worktree that belongs to some task — an unassigned request here escalates and stops (never nest a
   worktree, never squat another task's branch). From the primary checkout root, create your
   worktree under `<repo-root>/.claude/worktrees/<branch>` (ignored via the committed adopter entry;
   inside your writable scope, so no relaunch) and record branch + worktree path on the issue. Every
   subsequent command targets the worktree path; the checkout you opened in is never modified.
4. Work it as that issue's worker: the with-an-assignment path above, `worker-brief.md` and
   `CLAUDE.md` reads included.

**Name mappings** for the method's Claude-specific words: `CLAUDE.md` = the operational-memory file
(you read and write it as above; never move its content into `AGENTS.md`). `EnterWorktree` = plain
`git worktree add`. Craft skills (`superpowers:<name>`) = your catalog's real names, or do the
step's substance. A gating helper you need = a **separate `codex exec -s read-only`** — an in-tree
`spawn_agent` child inherits your writable sandbox and filesystem (`fork_turns:"none"` cleans the
conversation, not the permissions) — or leave the gating review to the main session. This page is
about **Codex CLI**; other Codex surfaces differ.

---

## Adopting a repo (run by the Claude main session, or the human)

Adoption is a **committed change**: run the plugin's adopter at the target repo's root, review the
diff, merge it like any change — git is the provenance and the undo.

```sh
"$PLUGIN_ROOT"/scripts/codex-adopt adopt              # marker + worktree gitignore entry
"$PLUGIN_ROOT"/scripts/codex-adopt adopt --fallback   # + managed AGENTS.md block (hookless envs)
"$PLUGIN_ROOT"/scripts/codex-adopt unadopt            # remove what adopt recorded it created
```

It manages three tracked artifacts — the `.devstandard` marker (also its ownership manifest), the
`.gitignore` line `/.claude/worktrees/`, and (only on `--fallback`) a delimited, **prepended**
`AGENTS.md` block for environments where the hook is unavailable. It is idempotent, migrates the
legacy single-marker block, preserves pre-existing entries it did not create, and **refuses with
zero mutation** on anything it does not recognize. Machine setup besides adoption: install the
DevStandard plugin in Codex and confirm the one-time hook trust in the Codex TUI ("Hooks need
review → Trust all and continue"); verify delivery afterwards by opening a Codex session in an
adopted repo — the role banner names this page.
