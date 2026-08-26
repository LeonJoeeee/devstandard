# DevStandard

[![CI](https://github.com/LeonJoeeee/devstandard/actions/workflows/ci.yml/badge.svg)](https://github.com/LeonJoeeee/devstandard/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/LeonJoeeee/devstandard)](https://github.com/LeonJoeeee/devstandard/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**The GitHub flow, extended to agent teams.**

DevStandard is a development-method plugin for [Claude Code](https://code.claude.com/docs) and [Codex](https://developers.openai.com/codex) — the same method on both, delivered by the same session hook (see [Install](#install)). It adds the three things an agent harness doesn't do by itself:

1. **Discipline** — rules an agent won't impose on itself: settle what "done" means before starting, get designs torn apart before writing code, prove completion with evidence, know when to stop and ask you;
2. **Project memory** — a PRD, an architecture doc, a decision log, design specs for substantial changes, and a repo CLAUDE.md (commands & gotchas) in every project, so parallel sessions (and human teammates) stay aligned on *what*, *how*, and *why*;
3. **Reliable delivery of both** — a hook puts the method into every session automatically (`core.md` on Claude Code; `core.md` plus a bounded mappings page on Codex). Methodology skills that rely on auto-triggering fire ~0% of the time; a hook fires 100%.

The bet behind it: directing agents is the same collaboration problem humans already solved with the GitHub flow — so agents follow the **same** branches / PRs / CI / review process your team already uses, instead of some new agent-coordination scheme ([why](docs/adr/0009-github-flow-extended-to-agent-teams.md)).

## Requirements

- **[Claude Code](https://code.claude.com/docs)** (a recent version: plugin system + SessionStart hooks) **and/or [Codex](https://developers.openai.com/codex)** (a recent codex-cli: plugins + hooks) — the same plugin serves both; either runs the full method alone. The execution ladder's workflow rungs use each harness's own orchestration (Claude Code's Workflow tool; Codex's subagent/loop primitives); everything else works without them.
- **[superpowers](https://github.com/obra/superpowers)** — the craft layer. DevStandard is the method layer wrapped around Claude Code (the mechanics) and superpowers (per-step craft: debugging, TDD, requirements interviews); its flow points at superpowers skills by name, so install both — on each harness you run the method on ([ADR 0016](docs/adr/0016-superpowers-becomes-a-dependency.md)).
- **git**, and a **GitHub repo** for the full flow — the generated CI and release pipelines target GitHub Actions. The discipline itself works with any git hosting.

## Install

Inside a Claude Code session, run:

```
/plugin marketplace add LeonJoeeee/devstandard
/plugin install devstandard@devstandard
```

To check it took: start a new session and ask *"what does DevStandard tell you to do?"* — the agent should recite the trigger rule and the discipline.

Prefer to try before installing? From a shell (affects only that one session):

```bash
git clone https://github.com/LeonJoeeee/devstandard.git
claude --plugin-dir ./devstandard
```

**On Codex.** The same plugin delivers the same method ([ADR 0039](docs/adr/0039-codex-runs-the-method.md)): install it (`codex plugin marketplace add <checkout>` then `codex plugin add devstandard@<marketplace>`) and confirm the one-time hook trust in the Codex TUI ("Hooks need review → Trust all and continue"); then install superpowers on Codex as well — `codex plugin marketplace add https://github.com/obra/superpowers` (it registers as `superpowers-dev`), then `codex plugin add superpowers@superpowers-dev`: the official OpenAI marketplace carries superpowers several versions behind, and its skills then appear in the Codex catalog under the same `superpowers:<name>` names the method uses. That's all — every Codex session then reads `core.md` plus the mappings page, everywhere, exactly as Claude sessions read `core.md`. Collaboration is by dispatch, not identity: a Codex session works as a worker only when a dispatch brief says so. *(Hookless environments only: prepend this fallback block to the repo's effective instruction file — `AGENTS.md`, or `AGENTS.override.md` where one shadows it; prepended, so a long file cannot truncate it: `<!-- devstandard-fallback --> Read IN FULL before acting: the installed DevStandard plugin's core.md and reference/harness-codex.md — locate it via codex plugin list --json, the devstandard entry's source.path.`)* *(Migrating from v0.27: update the plugin first, then remove `.devstandard` and the old managed AGENTS.md block via a small PR; keep the `/.claude/worktrees/` ignore line.)*

**Updating (either harness).** Claude Code: `claude plugin marketplace update devstandard && claude plugin update devstandard@devstandard`, then start a new session. Codex: `git pull` in the checkout, then run `codex plugin add devstandard@devstandard` **again** — the install copies a versioned snapshot into `~/.codex/plugins/cache/<marketplace>/devstandard/<version>/` and the hook runs from that copy, so a pulled checkout is not read live (`source.path` in `codex plugin list --json` still names the checkout; do not read it as the running version). The one-time hook trust carries over the re-add as long as `hooks/hooks.json` is unchanged — it is keyed on that file. Confirm the same way as the install check above; a session that recites nothing is running the old snapshot.

## What you get

- **Say "start a new project" and the full lifecycle applies** — PRD → architecture doc + decision log → a thin skeleton that pins the interfaces → CI + a tag-triggered release pipeline + a repo-root CLAUDE.md (commands and gotchas every later session loads automatically) → tasks dispatched as issues. Full by default; say "throwaway" and it stays light — the scope is yours to declare, never the agent's to guess.
- **A change in an existing repo is usually just a task** — no PRD, no architecture doc, no ADR; the discipline still applies (and the change still merges through a branch + PR + review + CI, like everything else). A big in-repo initiative you flag gets a scoped mini-lifecycle.
- **Every task runs disciplined** — a machine-checkable done-check before any code; designs must survive a challenge from an independent fresh reviewer first; one writer at a time (parallelism goes to review); "done" requires commands, exit codes, and output.
- **Parallel work without collisions** — a main session (you + your agent, whichever harness) dispatches each task as an issue; one task = one branch = one worktree, worked by a subagent (a Codex process where one is installed — [`reference/external-agent.md`](reference/external-agent.md)), a workflow, or a separate session; work returns as a PR. **Merging belongs to `main`**, behind two checks — a fresh review (no prior history), then green CI; an architecture change needs your approval before it lands, plus a decision-log entry.
- **It's lean** — a bounded always-on payload carries the whole method (`core.md`, under 5,000 tokens, on Claude Code; plus a mappings page under 4 KiB on Codex); templates and helpers load only when actually read. No background processes, no external services; one companion plugin — superpowers — supplies the per-step craft.

## How you use it

**Day to day** — nothing visible changes. Ask for a bug fix or a small feature in an existing repo and the agent just does it, under standing discipline: it settles what "done" looks like first, and closes with evidence instead of "should work now".

**Starting something new** — say *"create a new repo for X"*. The agent interviews you into a one-page PRD (what / why / what counts as done — you approve it), writes the architecture doc that every later session will treat as the shared map, starts the decision log, scaffolds the skeleton, and generates CI + release workflows plus a repo-root CLAUDE.md (commands and gotchas every later session loads automatically). Then the work is split into tasks.

**Working a big project in parallel** — you and a main session hold the thinking; it files each task as a GitHub issue and dispatches it to the cheapest executor that fits (a subagent — a Codex process where one is installed, [`reference/external-agent.md`](reference/external-agent.md) — a workflow, or a separate session for the big ones), each owning its branch and worktree. Work comes back as a PR, guarded by two checks — a fresh review (no prior history), then green CI against current main — and the main session merges. When a task needs to change the architecture itself, it comes back to you first: your approval, then the merge, doc updated, decision recorded. Other people — with their own agents — join through the exact same flow.

Execution scales to the task: a one-liner runs solo; heavier work recruits a few subagents or small, spend-capped multi-agent workflow runs — always the cheapest level that holds the job.

## What's actually installed

The always-on footprint is **bounded and enumerated**: [`core.md`](core.md) on Claude Code; `core.md` plus [`reference/harness-codex.md`](reference/harness-codex.md) (the name mappings, under 4 KiB) on Codex. A SessionStart hook makes reading them the agent's mandatory first action every session (and again after a context compaction); that's the whole trigger mechanism. Everything else lives in [`reference/`](reference/) — one file per thing `core.md` points at, read only when it does: the PRD / architecture / ADR / design-spec templates, the CI and release pipelines, the rules for driving a PR green, for a red check, and for a CI outage, a worker brief, a code-review prompt, a worktree checklist, a guide to dispatching a process-invoked agent (another vendor's, or a fresh `codex exec`) and when to, an ephemeral self-hosted runner, where writes go outside the repo. Craft (debugging, TDD, requirements interviews) is not duplicated here — the flow points at the matching [superpowers](https://github.com/obra/superpowers) skill by name ([ADR 0016](docs/adr/0016-superpowers-becomes-a-dependency.md)). There is deliberately no router, no skill chain, no bundled orchestration scripts — Claude Code already knows how to orchestrate; DevStandard only supplies the rules ([ADR 0006](docs/adr/0006-workflow-is-the-harness-thin-shell.md), [0007](docs/adr/0007-no-router-hook-injects-one-page-core.md), [0008](docs/adr/0008-execution-ladder-rationed-workflows.md)).

## FAQ

**Will it slow down small edits?**
No heavy lifecycle (PRD / architecture doc / ADR) triggers for a small edit — that only fires when you start a new project (an explicit signal, the scope yours to declare, never guessed; [ADR 0014](docs/adr/0014-lifecycle-scope-follows-human-declared-signal.md)). It does still ride a branch + PR + review + CI like every change ([ADR 0022](docs/adr/0022-ceremony-is-universal-every-change-through-pr-review-ci.md)) — but the agents run all of that, not you.

**What exactly enters my context?**
[`core.md`](core.md), once per session, under 5,000 tokens — a ceiling CI enforces on every change — plus, on Codex only, the mappings page (under 4 KiB, also CI-enforced). Nothing else unless the agent explicitly reads it.

**Does it depend on other plugins?**
One: [superpowers](https://github.com/obra/superpowers). DevStandard is the method layer wrapped around Claude Code (mechanics) and superpowers (craft) — at the step where a craft skill helps, the flow names it and the agent invokes it; the skill serves inside that one step, and on any conflict DevStandard's flow wins ([ADR 0016](docs/adr/0016-superpowers-becomes-a-dependency.md)). Two `reference/` files remain adapted from superpowers (MIT, attribution kept).

**Is it for teams or solo?**
Both — that's the point. Solo: you + parallel agent sessions. Team: several humans, each with their own agents, one shared flow.

**Can I adopt it on an existing project?**
Yes. Changes are tasks from day one; add the doc set (`docs/PRD.md`, `docs/architecture.md`, `docs/adr/`, a repo-root `CLAUDE.md`) when you are ready — templates in `reference/`.

## Layout

```
core.md          the always-on page: trigger rule + execution discipline + standards
hooks/           SessionStart hook (forces a first-action read of core.md — Claude Code)
.codex-plugin/   the Codex manifest — the same method, delivered by the same hook (ADR 0039)
reference/       one file per thing core.md points at — PRD / architecture / ADR /
                 design-spec templates, CI + release pipelines, PR-green, red-check
                 and CI-fallback rules, worker brief, reviewer prompt, worktree
                 checklist, external-agent dispatch, the Codex name mappings (harness-codex.md),
                 self-hosted runner, out-of-repo writes
docs/            DevStandard's own PRD, architecture doc, and decision log
_source/         the research this design stands on
```

DevStandard was built with its own rules. Its `docs/` holds a real PRD, architecture doc, and an ADR log recording why every major call went the way it did — including the ones that got overturned (0001 → 0007, 0002 → 0016, 0003 → 0008, 0004 → 0014, 0005 → 0015). That log is the best demo of what the method produces.

## License

MIT.
