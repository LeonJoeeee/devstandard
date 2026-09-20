# DevStandard in Codex

Use `reference/orchestrator.md` in a main Codex session. This page
maps host mechanics; user instructions and host permissions take precedence. Method paths resolve
from the installed plugin root.

## Context and project memory

Trusted SessionStart hooks deliver the orchestrator role page and this adapter. After resuming
an older session, read any missing artifact in full. If hooks are disabled or awaiting trust,
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
Nothing else wakes this session: the wake is that wait/status call on the recorded handle, or
`--wait` keeping the dispatching tool invocation alive, arranged in the same step as the dispatch.

Before task work, the child reads the receipt's absolute `brief` IN FULL and verifies its
`brief_sha256`. That saved role/task is authoritative over the inline copy. Missing, unreadable,
incomplete or mismatched source means stop and return blocked. Keep that per-run file available
until the child finishes; continuation gets its own file and digest.

A fresh conversation still inherits host developer instructions, cwd and permissions. It does not
create a sandbox or move the child into its lane: the task packet names the worktree, and the worker
validates it and targets every command there. Native children fire SubagentStart, not SessionStart;
the complete role therefore rides the receipt. Inherited PreToolUse hooks recognize an absent/default
child type as worker-family under `reference/orchestrator.md`’s Guarded operations section and its role resolution; explicit bindings win.
No custom Codex agent definition or global configuration is required; this plugin's manifest declares no agents loader.

A native child also inherits the host's **MCP tools**, which reach it through code mode's nested
`tools` object as `mcp__<server>__<tool>` rather than through its own tool list. The host's approval
policy then governs the call exactly as it governs a CLI child's: measured on Codex CLI 0.153.4
under both v1 and v2 (issue #358), a child of a host at `approval_policy = "never"` is refused with
*"MCP tool call requires approval, but approval policy is never"* and nothing reaches the server,
while the same per-server `default_tools_approval_mode = "approve"` admits it. Dispatch only
prepares a receipt here and never launches the child, so on this path that key is the Codex-host
operator's to set in their own configuration.

This adapter is not a native-worker recovery carrier: it is root SessionStart context and is absent
from a native child's SubagentStart context. The child also inherits the caller's working directory,
not the assigned lane as an ambient directory. If compaction loses its initial message, inherited
developer instructions and cwd identify neither its lane nor its receipt, so no self-service native
recovery is qualified. The empty-context probe measured this reachability limit; it did not measure
actual compaction. This is not a recovery procedure: a child that detects the loss returns to the
orchestrator, which re-dispatches with a fresh receipt. Neither other executor is bound by this
limit: a CLI process worker starts in the assigned worktree, and a native Claude child's host keeps
a record of the conversation its packet arrived in. `reference/harness-claude.md` owns both Claude
lookups; Worker mechanics below owns the Codex ones.

For continuation, `--continue --resume HANDLE` delivers the continuation receipt to that same
native child as a follow-up — v1 `send_input`, v2 `followup_task` — and it answers with its context
intact; without a handle, use a fresh native child with the continuation receipt. A resume and a
fresh spawn alike proceed on the recorded handle: no native liveness is observed here, and the
handle you recorded on the issue is the evidence its child finished. Workers may delegate within
their own task under `reference/worker.md`.

## Gating review and process execution

Native Codex spawn cannot apply a per-child read-only sandbox. `codex-native` reviewer dispatch
therefore refuses before writes. Commission gating review through
`scripts/review-packet start ... --implementation codex --wait`, using the existing fresh read-only Codex
CLI process and whole-verdict publication path. Explicit worker process choices are `codex` and `claude-cli`; each requires its installed,
authenticated CLI. `reference/orchestrator.md`'s Dispatching to an executor section owns their invocation and permission boundaries.

**Verified Codex mechanics.** Run Codex CLI in the foreground of its detached supervisor. A linked
worktree needs write grants to both the common `.git` directory and its `.git/worktrees/<name>`
directory; the first grant is not recursive. Codex's `review` subcommand cannot take this contract
and its sandbox controls, so gating review uses plain read-only `exec`. Inspect actual output shape,
including newlines and attribution, before accepting it. These are Codex-specific observations, not
claims about another tool.

Codex CLI dispatch supplies role, task, model, effort and sandbox, and sets child-only
`DEVSTANDARD_ROLE=worker|reviewer`. Installed startup hooks suppress orchestrator context and
inherited guards use that role. **It also admits the host's MCP tools, for both purposes.**
`codex exec` is non-interactive, so its approval policy is `never`, and `never` auto-rejects every
MCP tool call — a child that sees the tools, is refused on the call, and cannot tell that from an
unreachable server. On 0.153.4 the per-server `mcp_servers.<name>.default_tools_approval_mode =
"approve"` is the only admission that keeps an explicit sandbox mode: `exec` ignores every
`approval_policy` value, `--approve-for-me` cannot be combined with `-s`, and the bypass flag would
cost the OS sandbox the gating reviewer is built on. Dispatch asks `codex mcp list --json` which
servers the host has and passes that key per enabled server, so it reads and edits no configuration
file; a server it cannot admit is named in the run record rather than left silently refused. Each
purpose keeps the sandbox mode it had. Every role then reaches every attached server — the residual
`reference/orchestrator.md`'s Guarded operations section accepts, whose remedy is not attaching such a server to a session that
runs workers. What an executor must do when a visible tool is refused anyway is
`reference/worker.md`'s harness-limit rule.

Use `dispatch ... --wait` for CLI workers inside a Codex tool;
keep that same tool execution alive through its yield/poll mechanism until the command returns.
`review-packet start --wait` also retains synchronous whole-verdict publication. A later tool call
cannot rescue a launch whose PID namespace has already ended. Detachment protects against SIGHUP,
not namespace teardown. Default detached execution remains available on ordinary hosts.

The run's advisory lock identifies an active supervisor across PID namespaces; PIDs are diagnostic.
Only the atomic completion marker reports an observed CLI exit. Missing completion with an absent
supervisor is lost or unknown and blocks reuse, which no attestation clears. Preserve lifecycle
scratch until lane cleanup; `reference/orchestrator.md`'s Dispatching to an executor section owns explicit lost-run reconciliation and
publication recovery. `--wait` changes lifetime only: it adds no runtime-directory access,
authentication, hook trust or nested sandbox capability. Python supervision supports macOS/Linux
without external `setsid` or `nohup`; Windows is not qualified. `--implementation claude` still prepares a Claude Agent call in a Claude
host. `--implementation claude-cli` is the separate cross-host worker process: host/tool
permissions plus the assigned worktree, with no per-child read-only sandbox. It rejects reviewer
purpose before mutation; Codex-host gating review stays on read-only Codex CLI.

<!-- BEGIN CODEX WORKER MECHANICS -->
## Worker mechanics

`scripts/dispatch` delivers this section with `reference/worker.md` to every Codex worker. That
page carries the contract, including what a worker does when the packet cannot be recovered; this
section is the Codex harness under it.

A native child inherits the host's permissions and developer instructions and creates no sandbox of
its own; a Codex CLI worker runs inside the OS sandbox dispatch scoped to its lane.
A nested `codex exec` is not a native child inside your sandbox. Its own subagents go through the
host's native subagent tool.

A native Codex child has no qualified lane-specific recovery source once its packet is lost: the
caller's checkout holds the receipts of every lane and nothing in it distinguishes this child's, so
a fresh dispatch is the only route back to a packet here.

A CLI process begins in its lane. When that directory is a linked worktree on a matching
`task/<issue>-...` branch, `origin` identifies the repository, the latest matching
`devstandard-dispatch-v1` process-run receipt names the lane, and its absolute brief holds the
packet in full. The receipt fits this lane only when its branch and worktree match exactly and
every required field is present; a missing, equally-new, or unreadable receipt or brief leaves the
packet unrecovered, and a partial summary found in the checkout is not one.
<!-- END CODEX WORKER MECHANICS -->

## Hook trust

Review and trust plugin hooks through Codex's `/hooks`, then start a new session. Plugin installation
alone does not grant trust. Do not loosen permissions or bypass trust to repair missing automatic
loading. If the host exposes no trust interface, use the explicit skill and report the inactive guard.

After a plugin update, probe before you rely on the session: run a `codex exec` probe in a trusted
project directory and re-trust in `/hooks` only when it shows no context, because an update
sometimes leaves every SessionStart handler untrusted and sometimes does not (measured 2026-09-20:
releases 0.62.0, 1.0.0 and 1.3.0 did, 1.4.0 through 1.7.0 did not). Never refresh the plugin during
a live lane — it unbinds the running PreToolUse hook silently (#348) — and where the cache path
moved, start a new session before trusting any probe.

Official contracts: [plugins](https://developers.openai.com/plugins/build/plugins),
[hooks and trust](https://learn.chatgpt.com/docs/hooks).
