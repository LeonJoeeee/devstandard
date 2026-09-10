# DevStandard

[![CI](https://github.com/LeonJoeeee/devstandard/actions/workflows/ci.yml/badge.svg)](https://github.com/LeonJoeeee/devstandard/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/LeonJoeeee/devstandard)](https://github.com/LeonJoeeee/devstandard/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**The GitHub flow, extended to agent teams.**

DevStandard is a development-method plugin for [Claude Code](https://code.claude.com/docs) — delivered by its session hook (see [Install](#install)). It adds the three things an agent harness doesn't do by itself:

1. **Discipline** — rules an agent won't impose on itself: settle what "done" means before starting, get designs torn apart before writing code, prove completion with evidence, know when to stop and ask you;
2. **Project memory** — a PRD, an architecture doc, a decision log, design specs for substantial changes, and a repo CLAUDE.md only when it has commands, gotchas, a worktree copy-list, or record-language declaration to hold, so parallel sessions (and human teammates) stay aligned on *what*, *how*, and *why*;
3. **Reliable delivery of both** — SessionStart delivers `core.md` on Claude Code and its orchestrator reference; dispatched workers receive their own complete role context.

The bet behind it: directing agents is the same collaboration problem humans already solved with the GitHub flow — so agents follow the **same** branches / PRs / CI / review process your team already uses, instead of some new agent-coordination scheme ([why](docs/adr/0009-github-flow-extended-to-agent-teams.md)).

## Requirements

- **[Claude Code](https://code.claude.com/docs)** (a recent version: plugin system + SessionStart hooks). Codex is an optional CLI executor invoked by Claude Code for dispatched implementation and review; it receives its role through the dispatch brief ([dispatch guide](reference/external-agent.md)). It is a dispatched executor and nothing else — the earlier Codex-as-orchestrator direction, with its own plugin packaging and hook delivery, was withdrawn ([ADR 0045](docs/adr/0045-remove-codex-host-packaging.md)).
- **[superpowers](https://github.com/obra/superpowers)** — the craft layer. DevStandard is the method layer wrapped around Claude Code (the mechanics) and superpowers (per-step craft: debugging, TDD, requirements interviews); its flow points at superpowers skills by name, so install both in Claude Code ([ADR 0016](docs/adr/0016-superpowers-becomes-a-dependency.md)).
- **git**, and a **GitHub repo** for the full flow — the generated CI and release pipelines target GitHub Actions. The discipline itself works with any git hosting.
- **Python 3.9+ and an authenticated [`gh`](https://cli.github.com/) CLI** for the shipped commands — the dispatcher, the review packets and the guarded merge all read and write GitHub through `gh`. Detached Codex lanes additionally need Linux `setsid`/`nohup` ([dispatch guide](reference/external-agent.md)).

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

**Updating.** Run `claude plugin marketplace update devstandard && claude plugin update devstandard@devstandard`, then start a new session. Confirm the same way as the install check above.

## What you get

- **Set the result and why** — the orchestrator turns them into issues with bounds and machine-checkable done-checks. Document and review weight belongs to each task; a demo earns no automatic setup ceremony.
- **Keep one responsive orchestrator** — Claude Code discusses, dispatches, accepts and merges. It only makes one-or-two-line edits and researches directly; other concrete work goes to a worker.
- **Run isolated workers in parallel** — one task, branch and worktree each, using Codex where installed or a Claude-native subagent where its capabilities fit. Workers implement, rebase, prove the final state and deliver a green PR.
- **Accept against the goal** — a clean reviewer judges a green PR under the Goal/Floor/Notes contract. Both review and CI guard integration; architecture-level changes and major releases also need human sign-off.
- **Load the relevant context** — the shared core and orchestrator reference arrive at session start; workers receive their own role and execution craft. Other references load at their triggers.

## How you use it

**Day to day** — nothing visible changes. Ask for a bug fix or a small feature in an existing repo and the agent just does it, under standing discipline: it settles what "done" looks like first, and closes with evidence instead of "should work now".

**Starting something new** — say what you want to build and why. The orchestrator clarifies the outcome and chooses task bounds with you. A durable project definition, shared architecture, substantial design, or pipeline task triggers its corresponding document or template; a demo does not inherit a full lifecycle merely because it is new.

**Working a big project in parallel** — discuss direction with one Claude Code orchestrator. It creates issues, cuts independent scopes and dispatches N lanes through the [fixed dispatcher](reference/external-agent.md). Workers return evidence-bearing PRs, drive CI green, and leave their worktrees for the orchestrator. A clean reviewer judges acceptance, the guarded merge verifies integration, and the orchestrator closes the issue, cleans up and performs any delegated release. You own direction, irreversible authorization, and architecture/major-release sign-off.

Execution scales through isolated lanes: the orchestrator handles one-or-two-line edits and
research; workers handle other concrete work within the issue's bounds.

## What's actually installed

The orchestrator's static context is [`core.md`](core.md), the shared workflow contract, and
[`reference/orchestrator.md`](reference/orchestrator.md), its event loop and operations. SessionStart
delivers each artifact inline when its complete context fits the measured hook cap; an artifact over
the cap gets an instruction to read it in full before acting, and CI fails any *shipped* artifact
that would need that fallback. Startup, clear and compaction repeat delivery.
The worker receives [`reference/worker.md`](reference/worker.md) and one task packet through the
[fixed dispatcher](reference/external-agent.md). Its role is complete without core or the
orchestrator page. The reviewer judges under the sole
[judging contract](reference/code-review-prompt.md), which the review-packet script fills from
current sources, dispatches, and publishes whole on the PR.
Superpowers bindings live once per role, with Claude worker frontmatter checked against its source.
Other templates and procedures in [`reference/`](reference/) load at their triggers. The supported
configuration and guard limitations are in [the architecture](docs/architecture.md) and
[the guard guide](reference/hard-edges.md).

**A guard runs before your tools, and it denies with a reason.** `hooks/pre-tool-use` sees every tool
call, reads the command's raw text, and refuses when that text carries one of a short list of words
for that role — a worker's `merge`, `tag`, `release`, `--force`, branch/worktree deletion, recursive
`rm` outside `/tmp/`, or a push naming the default branch; a reviewer's whole write vocabulary; an
orchestrator's `gh pr merge` and `git merge`, which route to `scripts/guard merge` instead. Ordinary
work is admitted, shell syntax is never a reason to refuse, and no network failure can produce one.
Policy is read from `.github/devstandard-guards.json` on the repo's **default branch**, so an
adopting project lands that file on `main` and an unmerged edit grants nothing. This guards the
ordinary case and says so: an interpreter script or an obfuscated spelling is outside it, and
`guard merge`, branch protection and the sandboxes are what carry the guarantee. The rule and its
limits are in [the guard guide](reference/hard-edges.md).

## FAQ

**Will it slow down small edits?**
Weight follows the task. A small edit needs no invented PRD, architecture document or ADR;
the ordinary branch/PR gates still apply, with the [two-checks paragraph](core.md) naming the
narrow exceptions. The agents run the commands.

**What exactly enters my context?**
CI enforces the core byte/token budget and each hook output against the measured cap. The two
orchestrator artifacts are delivered separately; worker and reviewer context travel through dispatch.
The [rule ledger](docs/specs/2026-09-06-core-md-rule-ledger.md) records the measurement and carrier choices.

**Does it depend on other plugins?**
One: [superpowers](https://github.com/obra/superpowers). DevStandard is the method layer wrapped around Claude Code (mechanics) and superpowers (craft) — at the step where a craft skill helps, the flow names it and the agent invokes it; the skill serves inside that one step, and on any conflict DevStandard's flow wins ([ADR 0016](docs/adr/0016-superpowers-becomes-a-dependency.md)). Two `reference/` files remain adapted from superpowers (MIT, attribution kept).

**Is it for teams or solo?**
The supported configuration is one Claude Code orchestrator per project and N isolated workers.
GitHub holds the durable collaboration record; the [architecture](docs/architecture.md) defines
the supported executor boundaries.

**Can I adopt it on an existing project?**
Yes. Changes are tasks from day one. Add each method document only when its own trigger fires; the paths in the templates are defaults that yield to an established convention, declared by the architecture doc, and a repo-root `CLAUDE.md` exists only when it has an admitted line to hold (`reference/in-repo-writes.md`).

## Layout

```
core.md          the shared workflow, role interlock and resident triggers
hooks/           SessionStart delivery and recognized-operation PreToolUse guards
scripts/         the shipped machinery — fixed dispatcher, review packets, guarded merge
agents/          Claude-native worker and reviewer definitions
reference/       one file per thing core.md points at — PRD / architecture / ADR /
                 design-spec templates, CI + release pipelines, PR-green, red-check
                 and CI-fallback rules, orchestrator and worker role pages, reviewer
                 prompt, guarded-operation rules, worktree checklist,
                 external-agent dispatch, where files go (where-it-goes.md — not a
                 router or classifier), out-of-repo writes, in-repo document
                 admission, repo CLAUDE.md admission, clean handback
docs/            DevStandard's own PRD, architecture doc, and decision log
_source/         the research this design stands on
```

DevStandard was built with its own rules. Its `docs/` holds a real PRD, architecture doc, and an ADR log recording why every major call went the way it did — including the ones that got overturned (0001 → 0007, 0002 → 0016, 0003 → 0008, 0004 → 0014, 0005 → 0015, and the rebuild's own supersessions: 0038/0039 → 0045, 0006/0008 → 0047, 0014 → 0048). That log is the best demo of what the method produces.

## License

MIT.
