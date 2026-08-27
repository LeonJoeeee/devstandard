# The method on Codex: name mappings

You were sent here by the session hook alongside `core.md`. The method is the same on every harness;
only a few names in it are Claude Code's. Read them as follows, then apply `core.md` as written.

**`CLAUDE.md`** — the repo's operational-memory file, on every harness. Codex does not auto-load it:
if the repo has one, read it in full before any repo work — it holds the commands, gotchas, and
worktree copy-list — and write back only a command, environment gotcha, worktree copy-list entry, or
record-language declaration in your PR. Add documentation only when `reference/in-repo-writes.md`
admits it; never move `CLAUDE.md`'s content into `AGENTS.md`.

**Session scratch** — `core.md`'s "scratch the session gives you" means the location your harness
provides; Codex names none, so use one dedicated `mktemp -d` directory per task, name it in the PR
when its contents matter, and remove it best-effort when the task completes
(`reference/out-of-repo-writes.md`).

**`EnterWorktree`** — plain `git worktree add`. The lifecycle in `reference/worktree-lifecycle.md` is
git, not a Claude tool.

**Craft skills (`superpowers:<name>`)** — with superpowers installed on Codex (README, the Codex
install), your skill catalog lists them under exactly these names: read the named `SKILL.md`, apply it
for that step, return to the method's flow. If the catalog lacks one, do the step's substance
(interview the requirements, find the root cause before fixing, guard the implementation with tests)
and return.

**The Agent tool / plan list / "workflow run"** — your harness's own primitives: `spawn_agent` for a
subagent, `update_plan` for the plan list, and your parallel/loop execution for a workflow run. The
ladder's shape in `core.md` is unchanged; only the tool names differ.

**Model routing** — set the model explicitly on every spawn that takes one. The `opus` cap names
Claude's tiers and binds agents spawned through Claude's harness; on Codex, route within your own
harness's models at the human's standing setting, written once on `reference/external-agent.md`. The
discipline transfers; the tier names do not (ADR 0036, 0039, 0040).

**A gating helper** (a review or challenge you commission) — a separate `codex exec -s read-only`
process, never an in-tree `spawn_agent` child: children inherit your writable sandbox and filesystem,
and `fork_turns:"none"` cleans the conversation, not the permissions. If that process cannot run,
the gate is blocked, not lowered (`reference/external-agent.md`, "When it is not there").

This page is about **Codex CLI** — the surface measured and supported. One scope note: this page and
`core.md` arrive by the plugin's session hook after a one-time trust confirmation ("Hooks need
review → Trust all and continue" in the Codex TUI); in an environment without hooks, the repo-level
fallback snippet in the README's install section delivers the same two reads.
