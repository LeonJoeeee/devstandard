# DevStandard in Codex

Use the shared `core.md` and `reference/orchestrator.md` in a main Codex session. This page
maps host mechanics; user instructions and host permissions take precedence. Method paths resolve
from the installed plugin root.

## Context and project memory

Trusted SessionStart hooks deliver the core, orchestrator role and this adapter. After resuming
an older session, read any missing shared artifact in full. If hooks are disabled or awaiting trust,
invoke `$devstandard` to read the same sources; that fallback does not activate a tool guard.

Codex discovers the project's `AGENTS.md` natively. Also read existing `CLAUDE.md` when the workflow
requests operational memory. Respect both and keep each fact at its established source. Do not
copy the method into either file or change global instructions to enable this plugin. Resolve
superpowers through the available skill catalog at the existing role triggers.

## Native workers

Dispatch workers with `scripts/dispatch ... --implementation codex-native`. The dispatcher prepares
an isolated lane and a receipt containing the complete worker role, issue/task packet and worktree;
it cannot invoke the host's native tool. Its `native-spawn.json` is a semantic receipt, not arguments
to copy into a particular API. Pass its full `message`, including the canonical-brief preamble,
through the available native spawn tool, start a fresh conversation (`fork_context=false` in v1;
`fork_turns="none"` in v2), and provide the envelope's explicit `model` and `reasoning_effort` plus
other fields the tool requires. If the tool
cannot accept those controls, report it rather than inheriting a model silently.
Record the actual returned handle on the issue and observe its
completion with the host's native wait/status tools. A prepared receipt is not a running worker.

Before task work, the child reads the receipt's absolute `brief` IN FULL and verifies its
`brief_sha256`. That saved role/task is authoritative over the inline copy. Missing, unreadable,
incomplete or mismatched source means stop and return blocked. Keep that per-run file available
until the child finishes; continuation gets its own file and digest.

A fresh conversation still inherits host developer instructions, cwd and permissions. It does not
create a sandbox or move the child into its lane: the task packet names the worktree, and the worker
validates it and targets every command there. Native children fire SubagentStart, not SessionStart;
the complete role therefore rides the receipt. Inherited PreToolUse hooks recognize the child event
as worker-family unless an explicit role binding takes precedence. No custom Codex agent definition
or global configuration is required; this plugin's manifest declares no agents loader.

For continuation, use a fresh native child with the continuation receipt. `--native-finished`
attests that all outstanding native handles in that lane have finished, for that operation only;
it cannot clear any live or unknown CLI run. `--resume` remains Claude-native only. Workers may delegate
within their own task under `reference/worker.md`.

## Gating review and process execution

Native Codex spawn cannot apply a per-child read-only sandbox. `codex-native` reviewer dispatch
therefore refuses before writes. Commission gating review through
`scripts/review-packet start ... --implementation codex --wait`, using the existing fresh read-only Codex
CLI process and whole-verdict publication path. Explicit worker process choices are `codex` and `claude-cli`; each requires its installed,
authenticated CLI. `reference/external-agent.md` owns their invocation and permission boundaries.

Codex CLI dispatch supplies role, task, model, effort and sandbox, and sets child-only
`DEVSTANDARD_ROLE=worker|reviewer`. Installed startup hooks suppress orchestrator context and
inherited guards use that role. Use `dispatch ... --wait` for CLI workers inside a Codex tool;
keep that same tool execution alive through its yield/poll mechanism until the command returns.
`review-packet start --wait` also retains synchronous whole-verdict publication. A later tool call
cannot rescue a launch whose PID namespace has already ended. Detachment protects against SIGHUP,
not namespace teardown. Default detached execution remains available on ordinary hosts.

The run's advisory lock identifies an active supervisor across PID namespaces; PIDs are diagnostic.
Only the atomic completion marker reports an observed CLI exit. Missing completion with an absent
supervisor is lost or unknown and blocks reuse, including with `--native-finished`. Preserve lifecycle
scratch until lane cleanup; `reference/external-agent.md` owns explicit lost-run reconciliation and
publication recovery. `--wait` changes lifetime only: it adds no runtime-directory access,
authentication, hook trust or nested sandbox capability. Python supervision supports macOS/Linux
without external `setsid` or `nohup`; Windows is not qualified. `--implementation claude` still prepares a Claude Agent call in a Claude
host. `--implementation claude-cli` is the separate cross-host worker process: host/tool
permissions plus the assigned worktree, with no per-child read-only sandbox. It rejects reviewer
purpose before mutation; Codex-host gating review stays on read-only Codex CLI.

## Hook trust

Review and trust plugin hooks through Codex's `/hooks`, then start a new session. Plugin installation
alone does not grant trust. Do not loosen permissions or bypass trust to repair missing automatic
loading. If the host exposes no trust interface, use the explicit skill and report the inactive guard.

Official contracts: [plugins](https://developers.openai.com/plugins/build/plugins),
[hooks and trust](https://learn.chatgpt.com/docs/hooks).
