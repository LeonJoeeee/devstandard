# DevStandard

**English** | [中文](README.zh-CN.md)

[![CI](https://github.com/LeonJoeeee/devstandard/actions/workflows/ci.yml/badge.svg)](https://github.com/LeonJoeeee/devstandard/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/LeonJoeeee/devstandard)](https://github.com/LeonJoeeee/devstandard/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**The GitHub flow, extended to agent teams.**

DevStandard is a plugin for [Claude Code](https://code.claude.com/docs), Anthropic's coding agent. It adds the three things Claude Code doesn't do by itself:

1. **Discipline** — rules an agent won't impose on itself: settle what "done" means before starting, get designs torn apart before writing code, prove completion with evidence, know when to stop and ask you;
2. **Project memory** — a PRD, an architecture doc, a decision log, design specs for substantial changes, and a repo CLAUDE.md (commands & gotchas) in every project, so parallel sessions (and human teammates) stay aligned on *what*, *how*, and *why*;
3. **Reliable delivery of both** — a hook puts one page of rules into every session automatically. Methodology skills that rely on auto-triggering fire ~0% of the time; a hook fires 100%.

The bet behind it: directing agents is the same collaboration problem humans already solved with the GitHub flow — so agents follow the **same** branches / PRs / CI / review process your team already uses, instead of some new agent-coordination scheme ([why](docs/adr/0009-github-flow-extended-to-agent-teams.md)).

## Requirements

- **[Claude Code](https://code.claude.com/docs)** — a recent version (plugin system + SessionStart hooks). The execution ladder's workflow rungs use Claude Code's Workflow tool (available since mid-2026 releases); everything else works without it.
- **[superpowers](https://github.com/obra/superpowers)** — the craft layer. DevStandard is the method layer wrapped around Claude Code (the mechanics) and superpowers (per-step craft: debugging, TDD, requirements interviews); its flow points at superpowers skills by name, so install both ([ADR 0016](docs/adr/0016-superpowers-becomes-a-dependency.md)).
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

## What you get

- **Say "start a new project" and the full lifecycle applies** — PRD → architecture doc + decision log → a thin skeleton that pins the interfaces → CI + a tag-triggered release pipeline + a repo-root CLAUDE.md (commands and gotchas every later session loads automatically) → tasks dispatched as issues. Full by default; say "throwaway" and it stays light — the scope is yours to declare, never the agent's to guess.
- **A change in an existing repo is usually just a task** — no PRD, no architecture doc, no ADR; the discipline still applies (and the change still merges through a branch + PR + review + CI, like everything else). A big in-repo initiative you flag gets a scoped mini-lifecycle.
- **Every task runs disciplined** — a machine-checkable done-check before any code; designs must survive a challenge from an independent fresh reviewer first; one writer at a time (parallelism goes to review); "done" requires commands, exit codes, and output.
- **Parallel work without collisions** — a main session (you + Claude) dispatches each task as an issue; one task = one branch = one worktree, worked by a subagent, a workflow, or a separate session; work returns as a PR. **Merging belongs to `main`**, behind two checks — a fresh review (no prior history), then green CI; an architecture change needs your approval before it lands, plus a decision-log entry.
- **It's lean** — one page (~3,000 tokens) per session carries the whole method; templates and helpers load only when actually read. No background processes, no external services; one companion plugin — superpowers — supplies the per-step craft.

## How you use it

**Day to day** — nothing visible changes. Ask for a bug fix or a small feature in an existing repo and the agent just does it, under standing discipline: it settles what "done" looks like first, and closes with evidence instead of "should work now".

**Starting something new** — say *"create a new repo for X"*. The agent interviews you into a one-page PRD (what / why / what counts as done — you approve it), writes the architecture doc that every later session will treat as the shared map, starts the decision log, scaffolds the skeleton, and generates CI + release workflows plus a repo-root CLAUDE.md (commands and gotchas every later session loads automatically). Then the work is split into tasks.

**Working a big project in parallel** — you and a main session hold the thinking; it files each task as a GitHub issue and dispatches it to the cheapest executor that fits (a subagent, a workflow, or a separate session for the big ones), each owning its branch and worktree. Work comes back as a PR, guarded by two checks — a fresh review (no prior history), then green CI against current main — and the main session merges. When a task needs to change the architecture itself, it comes back to you first: your approval, then the merge, doc updated, decision recorded. Other people — with their own agents — join through the exact same flow.

Execution scales to the task: a one-liner runs solo; heavier work recruits a few subagents or small, spend-capped multi-agent workflow runs — always the cheapest level that holds the job.

## What's actually installed

The entire always-on footprint is **one page**: [`core.md`](core.md) — read it, it's short. A SessionStart hook makes reading it the agent's mandatory first action every session (and again after a context compaction); that's the whole trigger mechanism. Templates ([`howto/`](howto/): PRD, architecture doc, design specs, ADRs, CI/CD) are read when their artifact is due — mostly at repo creation, the design spec at task time; helpers ([`aids/`](aids/): a worker brief, a code-review prompt, a worktree checklist) only when useful. Craft (debugging, TDD, requirements interviews) is not duplicated here — the flow points at the matching [superpowers](https://github.com/obra/superpowers) skill by name ([ADR 0016](docs/adr/0016-superpowers-becomes-a-dependency.md)). There is deliberately no router, no skill chain, no bundled orchestration scripts — Claude Code already knows how to orchestrate; DevStandard only supplies the rules ([ADR 0006](docs/adr/0006-workflow-is-the-harness-thin-shell.md), [0007](docs/adr/0007-no-router-hook-injects-one-page-core.md), [0008](docs/adr/0008-execution-ladder-rationed-workflows.md)).

## FAQ

**Will it slow down small edits?**
No. The full lifecycle triggers only when you start a new project (an explicit signal — the scope is yours to declare, never guessed; [ADR 0014](docs/adr/0014-lifecycle-scope-follows-human-declared-signal.md)). Everything else is a task.

**What exactly enters my context?**
[`core.md`](core.md), once per session, ~3,000 tokens. Nothing else unless the agent explicitly reads it.

**Does it depend on other plugins?**
One: [superpowers](https://github.com/obra/superpowers). DevStandard is the method layer wrapped around Claude Code (mechanics) and superpowers (craft) — at the step where a craft skill helps, the flow names it and the agent invokes it; the skill serves inside that one step, and on any conflict DevStandard's flow wins ([ADR 0016](docs/adr/0016-superpowers-becomes-a-dependency.md)). Two `aids/` files remain adapted from superpowers (MIT, attribution kept).

**Is it for teams or solo?**
Both — that's the point. Solo: you + parallel agent sessions. Team: several humans, each with their own agents, one shared flow.

**Can I adopt it on an existing project?**
Yes. Changes are tasks from day one; add the doc set (`docs/PRD.md`, `docs/architecture.md`, `docs/adr/`, a repo-root `CLAUDE.md`) when you're ready — templates in `howto/`.

## Layout

```
core.md          the always-on page: trigger rule + execution discipline + standards
hooks/           SessionStart hook (forces a first-action read of core.md)
howto/           PRD / architecture / design-spec / ADR / CI-CD templates
aids/            optional helpers — worker brief, reviewer prompt, worktree checklist
docs/            DevStandard's own PRD, architecture doc, and decision log
_source/         the research this design stands on
```

DevStandard was built with its own rules. Its `docs/` holds a real PRD, architecture doc, and an ADR log recording why every major call went the way it did — including the ones that got overturned (0001 → 0007, 0002 → 0016, 0003 → 0008, 0004 → 0014, 0005 → 0015). That log is the best demo of what the method produces.

## License

MIT.
