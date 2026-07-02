# DevBook

**English** | [中文](README.zh-CN.md)

**The GitHub flow, extended to agent teams.**

A Claude Code plugin that makes AI agents first-class teammates on medium-to-large projects: they follow the same rules humans do — branches, PRs, CI, reviews, recorded decisions — plus the few disciplines only agents need.

## Why

One person could never build a large project alone. That's why software teams exist — and the coordination system humanity converged on for them is the GitHub flow: branches, PRs, CI, reviews, an append-only record of *why*.

Working with AI agents brings the exact same problem back: one human directing several agents — or several humans, each with their own agents — is a collaboration problem of the same shape. DevBook's bet is simple: **don't invent a new coordination system for agents; reuse the one that already won.** Building your own agent-coordination layer is more work and worse than just using GitHub — and GitHub is the only substrate your human teammates can actually *see*: an agent's work becomes a branch and a PR that anyone can review. It also composes with the open internet: strangers can join your project bringing their own agent teams, through the flow they already know.

Small change? One agent handles it serially — no ceremony. Large project? Humans and agents work in parallel through the full flow. The complete argument: [`docs/adr/0009`](docs/adr/0009-github-flow-extended-to-agent-teams.md).

## What it does

One page (`core.md`, ~700 tokens) is injected into every session by a SessionStart hook. It carries three things:

1. **A trigger rule** — ask to create a new repo and the full lifecycle applies (PRD → architecture doc + ADR log → thin skeleton pinning interfaces → CI + release pipeline → tasks fan out to parallel sessions). A change inside an existing repo is just a task — no ceremony.
2. **Execution discipline** — settle a machine-judgeable done-check before code; designs get refuted by clean-context reviewers before implementation; one writer at a time, parallelism goes to verification; done claims carry evidence (commands, exit codes, output); a cost ladder decides how much machinery a task deserves (in-session → a few subagents → small spend-capped workflow runs → chained runs).
3. **Collaboration standards** — one task = one branch = one worktree = one session; sessions deliver branches, merging belongs to main behind green CI; architecture changes are never silent: public merge + maintainer approval + an ADR.

Templates (`howto/`: PRD, architecture doc, ADRs, CI/CD) and helpers (`aids/`: code-review prompt, testing anti-patterns, debugging techniques) load only when read — nothing else costs context.

## Install

From GitHub:

```
/plugin marketplace add LeonJoeeee/devbook
/plugin install devbook@devbook
```

Or try it on a single session without installing anything (zero footprint elsewhere):

```bash
git clone https://github.com/LeonJoeeee/devbook.git
claude --plugin-dir ./devbook
```

Developing the plugin itself: `core.md` edits take effect live; `hooks/` edits need `/reload-plugins`.

## Layout

```
core.md          the injected page: trigger rule + execution discipline + standards
hooks/           SessionStart hook (injects core.md only)
howto/           PRD / architecture / ADR / CI-CD templates — read at repo creation
aids/            optional helpers — reviewer prompt, testing anti-patterns, debugging
docs/            DevBook's own PRD, architecture, and ADR log
_source/         the research this design stands on (workflow deep-dives, porting studies)
```

`docs/` is not an afterthought: DevBook was built with its own rules, and its ADR log records why every major call went the way it did — including the ones that were overturned.

## License

MIT. `aids/` files are adapted from [superpowers](https://github.com/obra/superpowers) (MIT, Jesse Vincent).
