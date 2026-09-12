# DevStandard

[![CI](https://github.com/LeonJoeeee/devstandard/actions/workflows/ci.yml/badge.svg)](https://github.com/LeonJoeeee/devstandard/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/LeonJoeeee/devstandard)](https://github.com/LeonJoeeee/devstandard/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**The GitHub flow, extended to agent teams.**

DevStandard is a development-method plugin for [Claude Code](https://code.claude.com/docs) and [Codex](https://developers.openai.com/codex) — delivered by session hooks (see [Install](#install)). It adds the three things an agent harness doesn't do by itself:

1. **Discipline** — rules an agent won't impose on itself: settle what "done" means before starting, get designs torn apart before writing code, prove completion with evidence, know when to stop and ask you;
2. **Project memory** — a PRD, an architecture doc, a decision log, design specs for substantial changes, and a repo CLAUDE.md only when it has commands, gotchas, a worktree copy-list, or record-language declaration to hold, so parallel sessions (and human teammates) stay aligned on *what*, *how*, and *why*;
3. **Reliable delivery of both** — SessionStart delivers the shared core and orchestrator reference; Codex also receives a small host adapter. Dispatched workers receive their own complete role context.

The bet behind it: directing agents is the same collaboration problem humans already solved with the GitHub flow — so agents follow the **same** branches / PRs / CI / review process your team already uses, instead of some new agent-coordination scheme ([why](docs/adr/0009-github-flow-extended-to-agent-teams.md)).

## Requirements

- **Claude Code or Codex**, with plugin and SessionStart-hook support. Both host native workers. Codex uses `codex-native` worker receipts and the independent read-only Codex CLI for gating reviews ([adapter](reference/harness-codex.md)). This restores host support under [ADR 0056](docs/adr/0056-restore-codex-host-support-with-shared-role-sources.md).
- **[superpowers](https://github.com/obra/superpowers)** — the craft layer. Install it on each executing host: DevStandard's role pages point to its requirements, debugging, TDD and planning skills ([ADR 0016](docs/adr/0016-superpowers-becomes-a-dependency.md)).
- **git**, and a **GitHub repo** for the full flow — the generated CI and release pipelines target GitHub Actions. The discipline itself works with any git hosting.
- **Python 3.9+ and an authenticated [`gh`](https://cli.github.com/) CLI** for the shipped commands — the dispatcher, review packets and guarded merge use GitHub through `gh`. Codex process lanes support macOS and Linux using Python's detached-session support; Windows is not qualified ([dispatch guide](reference/external-agent.md)).
- **Codex's [Linux sandbox prerequisites](https://learn.chatgpt.com/docs/sandboxing#prerequisites)** on Linux: install the distribution's `bubblewrap` package and, where required, its scoped AppArmor profile before running Codex lanes.

## Install

**Claude Code.** Inside a session, run:

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

**Codex.** From a shell, register this repository's marketplace and install the plugin:

```sh
codex plugin marketplace add LeonJoeeee/devstandard
codex plugin add devstandard@devstandard
codex plugin list --marketplace devstandard --json
```

These command forms are checked against `codex-cli 0.153.4`. To try a local checkout, use its
absolute path instead of `LeonJoeeee/devstandard` in the marketplace command. In interactive Codex,
review and trust the plugin hooks through `/hooks`, then start a new session. Installation alone
does not grant hook trust. The [adapter](reference/harness-codex.md) explains the delivered context
and how to recover when hooks are unavailable.

For an update, run `codex plugin marketplace upgrade devstandard`, then
`codex plugin add devstandard@devstandard` and start a new session. For a local-path marketplace,
update that checkout before running `plugin add`. If hooks are disabled or waiting for trust,
invoke `$devstandard` explicitly to read the shared method. That loads instructions; it does not
activate the tool guard. No method block is installed into global or project `AGENTS.md`.

## What you get

- **Set the result and why** — the orchestrator turns them into issues with bounds and machine-checkable done-checks. Document and review weight belongs to each task; a demo earns no automatic setup ceremony.
- **Keep one responsive orchestrator** — Claude Code or Codex discusses, dispatches, accepts and merges. It only makes one-or-two-line edits and researches directly; other concrete work goes to a worker.
- **Run workers in parallel lanes** — one task, branch and worktree each, using the host's native subagents by default. Codex native children inherit host permissions and target their assigned worktree; a fresh conversation is not a separate sandbox. CLI workers remain explicit cross-host choices. Workers implement, rebase, prove the final state and deliver a green PR.
- **Accept against the goal** — a clean reviewer judges a green PR under the Goal/Floor/Notes contract. Both review and CI guard integration; architecture-level changes and major releases also need human sign-off.
- **Load the relevant context** — the shared core and orchestrator reference arrive at session start; workers receive their own role and execution craft. Other references load at their triggers.

## How you use it

**Day to day** — nothing visible changes. Ask for a bug fix or a small feature in an existing repo and the agent just does it, under standing discipline: it settles what "done" looks like first, and closes with evidence instead of "should work now".

**Starting something new** — say what you want to build and why. The orchestrator clarifies the outcome and chooses task bounds with you. A durable project definition, shared architecture, substantial design, or pipeline task triggers its corresponding document or template; a demo does not inherit a full lifecycle merely because it is new.

**Working a big project in parallel** — discuss direction with one orchestrator on either host. It creates issues, cuts independent scopes and dispatches N lanes through the [fixed dispatcher](reference/external-agent.md). Workers return evidence-bearing PRs, drive CI green, and leave their worktrees for the orchestrator. A clean reviewer judges acceptance, the guarded merge verifies integration, and the orchestrator closes the issue, cleans up and performs any delegated release. You own direction, irreversible authorization, and architecture/major-release sign-off.

Execution scales through isolated lanes: the orchestrator handles one-or-two-line edits and
research; workers handle other concrete work within the issue's bounds.

## What's actually installed

The orchestrator's static context is [`core.md`](core.md), the shared workflow contract, and
[`reference/orchestrator.md`](reference/orchestrator.md), its event loop and operations. SessionStart
delivers each artifact inline when its complete context fits the measured hook cap; an artifact over
the cap gets an instruction to read it in full before acting, and CI fails any *shipped* artifact
that would need that fallback. Startup, clear and compaction repeat delivery. Codex also receives
[`reference/harness-codex.md`](reference/harness-codex.md); its separate resume trigger tells an
older session to read any missing shared sources in full. Trusted hooks are required for automatic
delivery. Runtime evidence and its limits are recorded in [the architecture](docs/architecture.md).
The worker receives [`reference/worker.md`](reference/worker.md) and one task packet through the
[fixed dispatcher](reference/external-agent.md). Its role is complete without core or the
orchestrator page. The reviewer judges under the sole
[judging contract](reference/code-review-prompt.md), which the review-packet script fills from
current sources, dispatches, and publishes whole on the PR.
Superpowers bindings live once per role, with Claude worker frontmatter checked against its source.
Codex native workers receive the complete role and task in a prepared receipt that the caller passes
to the actual native spawn tool, then records and observes through its returned handle. The plugin
does not load Codex custom agent definitions. Explicit process paths are `codex` for Codex CLI and
`claude-cli` for Claude CLI workers; `claude` retains the native Claude Agent meaning. Claude CLI
uses host/tool permissions and the assigned worktree, while Codex CLI provides its role sandbox.
Other templates and procedures in [`reference/`](reference/) load at their triggers. The supported
configuration and guard limitations are in [the architecture](docs/architecture.md) and
[the guard guide](reference/hard-edges.md).

**A guard runs before your tools, and it denies with a reason.** `hooks/pre-tool-use` sees every tool
call, reads the command itself — not a here-document body or a quoted string it carries — and
refuses when that text carries one of a short list of words for that role, as a whole word: a
worker's `merge`, `tag`, `release`, `--force`, branch/worktree deletion, recursive
`rm` outside `/tmp/`, or a push naming the default branch; a reviewer's whole write vocabulary; an
orchestrator's `gh pr merge` and `git merge`, which route to `scripts/guard merge` instead. Ordinary
work is admitted, shell syntax is never a reason to refuse, and no network failure can produce one.
**There is nothing to configure** — no settings file, no allowlist, no per-project word list — so
adopting it is installing the plugin. Every refusal is a
reminder rather than a wall: it names the word you wrote, what your role does instead, the page to
read, and how to re-spell a benign command that merely mentions a word. This guards the ordinary
case and says so: an interpreter script or an obfuscated spelling is outside it, and `guard merge`,
branch protection and the available host sandbox supply separate enforcement layers. The rule and its limits are in
[the guard guide](reference/hard-edges.md).

## FAQ

**Will it slow down small edits?**
Weight follows the task. A small edit needs no invented PRD, architecture document or ADR;
the ordinary branch/PR gates still apply, with the [two-checks paragraph](core.md) naming the
narrow exceptions. The agents run the commands.

**What exactly enters my context?**
CI enforces the core byte/token budget and each hook output against the measured cap. The shared
core and orchestrator artifacts, plus Codex's adapter, are delivered separately; worker and reviewer
context travel through dispatch. Codex respects existing `AGENTS.md` and explicitly reads the
project's `CLAUDE.md`, which remains the method's operational-memory source.
The [rule ledger](docs/specs/2026-09-06-core-md-rule-ledger.md) records the measurement and carrier choices.

**Does it depend on other plugins?**
One: [superpowers](https://github.com/obra/superpowers). The host supplies mechanics and superpowers supplies craft — at the step where a craft skill helps, the flow names it and the agent invokes it; the skill serves inside that one step, and on any conflict DevStandard's flow wins ([ADR 0016](docs/adr/0016-superpowers-becomes-a-dependency.md)). Two `reference/` files remain adapted from superpowers (MIT, attribution kept).

**Is it for teams or solo?**
The supported configuration is one Claude Code or Codex orchestrator per project and N isolated workers.
GitHub holds the durable collaboration record; the [architecture](docs/architecture.md) defines
the supported executor boundaries.

**Can I adopt it on an existing project?**
Yes. Changes are tasks from day one. Add each method document only when its own trigger fires; the paths in the templates are defaults that yield to an established convention, declared by the architecture doc, and a repo-root `CLAUDE.md` exists only when it has an admitted line to hold (`reference/in-repo-writes.md`).

## Layout

```
core.md          the shared workflow, role interlock and resident triggers
hooks/           SessionStart delivery and the per-role word-list PreToolUse guard
scripts/         the shipped machinery — fixed dispatcher, review packets, guarded merge
agents/          Claude-native worker and reviewer definitions
skills/          explicit method entry and hookless instruction recovery
.codex-plugin/   Codex plugin manifest; .agents/plugins/ holds its marketplace
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

DevStandard was built with its own rules. Its `docs/` holds a real PRD, architecture doc, and an ADR log recording why every major call went the way it did — including the ones that got overturned (0001 → 0007, 0002 → 0016, 0003 → 0008, 0004 → 0014, 0005 → 0015, and the rebuild's own supersessions: 0038/0039 → 0045 → 0056, 0006/0008 → 0047, 0014 → 0048). That log is the best demo of what the method produces.

## License

MIT.
