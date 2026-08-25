# Running DevStandard on Codex

DevStandard's method is harness-neutral prose; only its *delivery* and a handful of *names* are written
for Claude Code. This file is the Codex adapter — read it first (the top of `core.md` sent you here),
then read `core.md` and the rest of the method as written, translating the names below as you go. It is
read by a Codex main session, and by a Codex-dispatching session translating a worker brief.

The method itself does not change. Every rule in `core.md` and `reference/` holds on Codex; a rule that
turns out genuinely not to apply here is a finding to file, not a rule to skip.

## Delivery: how `core.md` gets read first

On Claude Code a `SessionStart` hook forces `core.md` to be read before anything else (ADR 0019). Codex
has no plugin hook that fires at session start — measured, it does not — but Codex reads the repo's own
`AGENTS.md` at session start and obeys it. So on Codex the forced-first-read lives in the consuming
repo's `AGENTS.md`, pointing at this plugin's installed `core.md`.

**Setup, once per repo that uses DevStandard on Codex** (re-run only if you move the checkout):

```sh
# 1. Resolve where the plugin is installed. For a local-checkout install this is the checkout dir
#    itself and is stable across version bumps, so the pointer never goes stale — `git pull` updates it.
CORE=$(codex plugin list --json | python3 -c \
  'import json,sys; print(next(p["source"]["path"] for p in json.load(sys.stdin)["installed"] if p["name"]=="devstandard"))')/core.md

# 2. Refuse loudly rather than write a dead pointer.
test -f "$CORE" || { echo "devstandard core.md not found at $CORE — is the plugin installed?"; exit 1; }

# 3. Write (or refresh) the pointer at the top of the repo's AGENTS.md.
printf 'Before your first response in this repo, read this file IN FULL — it is the development method you operate under, and you must follow it:\n\n    %s\n\nDo not answer until you have read it.\n\n' "$CORE" | cat - AGENTS.md 2>/dev/null | sponge AGENTS.md 2>/dev/null || \
printf 'Before your first response in this repo, read this file IN FULL — it is the development method you operate under, and you must follow it:\n\n    %s\n\nDo not answer until you have read it.\n' "$CORE" > AGENTS.md
```

A repo that never runs this simply does not get DevStandard on Codex — the method is *absent* there,
not degraded. That is the one real difference from Claude Code, where install is enough: on Codex,
delivery is opt-in per repo.

## The names, mapped

When the method names a Claude-specific thing, read it as the Codex equivalent:

| The method says | On Codex it means |
|---|---|
| model tiers `opus` / `sonnet` / `haiku`, and "never above `opus`" | Set the model **explicitly** on every agent you spawn, at or below the cap your own budget sets. `opus` is Claude's name for that cap, not a Codex tier — the transferable rule is "set it, always" (ADR 0036), not the specific id. |
| `superpowers:<skill>` (e.g. `superpowers:brainstorming`, `:systematic-debugging`, `:test-driven-development`, `:writing-plans`) | The same craft step, loaded the Codex way — if that skill layer is present, use it at that step; if it is absent, do the step's substance (brainstorm the requirements, find the root cause before fixing, write the plan) without the named skill. Never block on a skill that isn't there. |
| `CLAUDE.md` as the repo's operational memory | `AGENTS.md` — same role, Codex's name. **This substitution matters most where the method tells you to *write* it** (`reference/repo-claude-md.md`, and the CI setup in `reference/ci-pipelines.md`): create/append the repo's `AGENTS.md`, not a `CLAUDE.md` Codex never auto-reads. A repo already carrying a `CLAUDE.md` keeps it; add to `AGENTS.md`. |
| the Agent tool / "workflow run" / the Workflow tool (the execution ladder) | Codex's own primitives — `spawn_agent` for a subagent, `update_plan` for the plan/todo list, and Codex's parallel/loop execution for a "workflow run". The ladder's *shape* (do it here → a few fresh subagents → a bounded parallel/loop run) is unchanged; only the tool names differ. |
| `EnterWorktree` | Plain `git worktree add` — the lifecycle in `reference/worktree-lifecycle.md` is git, not a Claude tool; only that one convenience name is Claude's. |

## Dispatching a worker: translate the brief

`reference/worker-brief.md` is **pasted verbatim** into a spawned worker's prompt, so that worker never
reads `core.md` or this file and never sees the mappings above. When you dispatch a worker from a Codex
session (or dispatch a Codex executor from any session), **translate the brief's Claude-specific names
before you paste it** — you hold the mapping, having read this file to get here. The brief also carries
a one-line pointer back here, so a worker that is itself a full session gets a second chance to open
this file directly; but the paste path is yours to translate.

## What is unchanged

Everything else. The branch + PR + two checks, one writer per worktree, evidence-backed done claims,
issue-first, the design-spec-then-challenge flow, the doc duty, the English-record rule — all
harness-neutral, all in force. Codex as an *executor dispatched by a Claude session* is a separate,
already-shipped decision (ADR 0036); this file is about Codex as the main session running the method.
