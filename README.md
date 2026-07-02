# DevStandard

**English** | [中文](README.zh-CN.md)

[![CI](https://github.com/LeonJoeeee/devstandard/actions/workflows/ci.yml/badge.svg)](https://github.com/LeonJoeeee/devstandard/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/LeonJoeeee/devstandard)](https://github.com/LeonJoeeee/devstandard/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**The GitHub flow, extended to agent teams.**

DevStandard is a plugin for [Claude Code](https://code.claude.com/docs), Anthropic's coding agent. It adds the three things Claude Code doesn't do by itself:

1. **Discipline** — rules an agent won't impose on itself: settle what "done" means before starting, get designs torn apart before writing code, prove completion with evidence, know when to stop and ask you;
2. **Project memory** — a PRD, an architecture doc, and a decision log in every project, so parallel sessions (and human teammates) stay aligned on *what*, *how*, and *why*;
3. **Reliable delivery of both** — a hook puts one page of rules into every session automatically. Methodology skills that rely on auto-triggering fire ~0% of the time; a hook fires 100%.

The bet behind it: directing agents is the same collaboration problem humans already solved with the GitHub flow — so agents follow the **same** branches / PRs / CI / review process your team already uses, instead of some new agent-coordination scheme ([why](docs/adr/0009-github-flow-extended-to-agent-teams.md)).

## Requirements

- **[Claude Code](https://code.claude.com/docs)** — a recent version (plugin system + SessionStart hooks). The execution ladder's workflow rungs use Claude Code's Workflow tool (available since mid-2026 releases); everything else works without it.
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

- **Say "create a repo" and the full lifecycle applies** — PRD → architecture doc + decision log → a thin skeleton that pins the interfaces → CI + a tag-triggered release pipeline → tasks fan out to parallel sessions. Same treatment for every project, no size guessing.
- **A change in an existing repo is just a task** — no documents, no ceremony; the discipline still applies.
- **Every task runs disciplined** — a machine-checkable done-check before any code; designs refuted by independent clean-context reviewers first; one writer at a time (parallelism goes to verification); "done" requires commands, exit codes, and output.
- **Parallel work without collisions** — one session = one branch = one worktree = one task; sessions deliver branches/PRs; **merging belongs to `main`**, behind green CI; architecture changes additionally need maintainer approval plus a decision-log entry.
- **It's cheap** — one page (~700 tokens) per session; templates and helpers load only when actually read. No background processes, no external services, no other plugins required.

## How you use it

**Day to day** — nothing visible changes. Ask for a bug fix or a small feature in an existing repo and the agent just does it, under standing discipline: it settles what "done" looks like first, and closes with evidence instead of "should work now".

**Starting something new** — say *"create a new repo for X"*. The agent interviews you into a one-page PRD (what / why / what counts as done — you approve it), writes the architecture doc that every later session will treat as the shared map, starts the decision log, scaffolds the skeleton, and generates CI + release workflows. Then the work is split into tasks.

**Working a big project in parallel** — open one Claude Code session per task; each owns its branch and worktree and reads the architecture doc before starting. Sessions push branches; **you** merge them when CI is green. When a task needs to change the architecture itself, it comes back to you: public merge, your approval, doc updated, decision recorded. Other people — with their own agents — join through the exact same flow.

Execution scales to the task: a one-liner runs solo; heavier work recruits a few subagents or small, spend-capped multi-agent workflow runs — always the cheapest rung that holds the job.

## What's actually installed

The entire always-on footprint is **one page**: [`core.md`](core.md) — read it, it's short. A SessionStart hook injects it; that's the whole trigger mechanism. Templates ([`howto/`](howto/): PRD, architecture doc, ADRs, CI/CD) are read only during repo creation; helpers ([`aids/`](aids/): a code-review prompt, testing anti-patterns, debugging techniques) only when useful. There is deliberately no router, no skill chain, no bundled orchestration scripts — Claude Code already knows how to orchestrate; DevStandard only supplies the rules ([ADR 0006](docs/adr/0006-workflow-is-the-harness-thin-shell.md), [0007](docs/adr/0007-no-router-hook-injects-one-page-core.md), [0008](docs/adr/0008-execution-ladder-rationed-workflows.md)).

## FAQ

**Will it slow down small edits?**
No. The full lifecycle triggers only when you ask to create a new repo (an explicit signal — no complexity guessing, [ADR 0004](docs/adr/0004-trigger-repo-creation-uniform-lifecycle.md)). Everything else is a task.

**What exactly enters my context?**
[`core.md`](core.md), once per session, ~700 tokens. Nothing else unless the agent explicitly reads it.

**Does it depend on other plugins?**
No. Self-contained. Parts of `aids/` are adapted from [superpowers](https://github.com/obra/superpowers) (MIT, attribution kept) — superpowers itself is not required.

**Is it for teams or solo?**
Both — that's the point. Solo: you + parallel agent sessions. Team: several humans, each with their own agents, one shared flow.

**Can I adopt it on an existing project?**
Yes. Changes are tasks from day one; add the doc set (`docs/PRD.md`, `docs/architecture.md`, `docs/adr/`) when you're ready — templates in `howto/`.

## Layout

```
core.md          the injected page: trigger rule + execution discipline + standards
hooks/           SessionStart hook (injects core.md only)
howto/           PRD / architecture / ADR / CI-CD templates — read at repo creation
aids/            optional helpers — reviewer prompt, testing anti-patterns, debugging
docs/            DevStandard's own PRD, architecture doc, and decision log
_source/         the research this design stands on
```

DevStandard was built with its own rules. Its `docs/` holds a real PRD, architecture doc, and ten ADRs recording why every major call went the way it did — including the ones that got overturned (0001 → 0007, 0003 → 0008). That log is the best demo of what the method produces.

## License

MIT.
