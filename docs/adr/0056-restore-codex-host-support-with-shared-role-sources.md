# 0056 — Restore Codex host support with shared role sources and process lanes

Status: Proposed (2026-09-11; implementation decision pending human PR sign-off). Supersedes 0045.
Amends 0006, 0007, 0008, 0011, 0015, 0016,
0018, 0019, 0024, 0036, 0038, 0039, 0040, 0047 and 0049 (their live host, delivery or routing clauses).

**Scope: this ADR decides what the method ships.** Both Claude Code and Codex can host the
orchestrator; their shared workflow and the worker/reviewer contracts remain the same.

## Context

ADR 0045 removed unused Codex host packaging during the collaboration rebuild. The human now
wants to use DevStandard from Codex as well as Claude Code ([issue #342](https://github.com/LeonJoeeee/devstandard/issues/342))
and explicitly asked for whole-project reading, a plan and actual hook tests. Host installation is
therefore a required entry point rather than unused structure. The implementation plan
reuses the shipped role sources and dispatcher and ends with a tested PR, without merge or release.

The existing native dispatch output names Claude's Agent tool and role definitions. Translating it
into a new Codex-native implementation would add another delivery and enforcement path. The existing
Codex CLI process path already carries the same issue, lane, role and fresh read-only review contract.

## Decision

Restore `.codex-plugin/plugin.json` and a repository marketplace under `.agents/plugins/`.
The shared SessionStart script delivers `core.md` and `reference/orchestrator.md` on either host,
plus the bounded `reference/harness-codex.md` adapter on Codex. Each artifact keeps its own inline
budget. The shared matcher remains `startup|clear|compact`; the adapter also runs on resume and
instructs a full read of any missing shared sources in an older session.

An explicit `devstandard` skill provides instruction recovery when hooks are unavailable or waiting
for trust. It reads the same sources and preserves an assigned worker/reviewer role. It is not the
self-triggered method delivery rejected by 0007, and it does not activate a tool guard. Hook trust
remains the host's mechanism; installation alone does not prove hooks run.

Claude hosts retain their native-subagent default and the human's choice of Codex. **Codex hosts
explicitly pass `--implementation codex` for governed lanes**, including `review-packet start`.
The adapter owns that binding; no Codex agent-definition translator is added. Ordinary research can
use host-native subagents, and ADR 0055 continues to leave a worker's internal delegation to it.

Dispatch supplies `DEVSTANDARD_ROLE` only to its child processes, overriding inherited values.
Installed startup hooks suppress orchestrator context in those workers/reviewers, and inherited tool
hooks use their assigned role. This marker routes context, not authorization. Per-role sandboxes,
the hook's word lists, review publication, CI and the merge guard keep their existing boundaries.
Detached Python sessions replace the external `setsid`/`nohup` prerequisite on macOS and Linux;
supervision and publication ignore SIGHUP. Windows is not qualified.

`CLAUDE.md` remains the operational-memory source, explicitly read by Codex. Existing `AGENTS.md`
instructions are respected without copying facts or adding managed method blocks. Superpowers is
installed on each executing host and resolved at the existing role triggers.

The three release manifests stay in version lockstep. **The guard's version exemptions still cover
only the two Claude manifests.** A Codex manifest change takes ordinary check 1 and a fresh review
after rebase; release synchronization does not widen the bare-bump waiver or the rebase proof.

Excluded by the implementation plan: restoring the old repository-adoption marker, copying the method
into global instructions, or adding a native Codex executor translation layer. Each would add a
second mechanism where shared sources and the existing process path satisfy the requested entry.

## Consequences

Codex can enter the same method as a main session without becoming a permanent worker. This costs
one bounded adapter and installation entry, plus qualification of the shared hooks on another host.
CLI command help, constructed tests and real runtime probes establish different facts; the release
evidence must distinguish them. Historical 0038/0039 measurements do not qualify a newer CLI.
Architecture labels remain explicit about unverified live behavior until that evidence exists.

Rollback removes the new host carriers and restores the previous shared-hook branch and supervisor
through a reviewed revert. It never edits a user's global instructions. The original ADR bodies and
historical specs remain intact; dated amendments reconcile their actionable routing statements.
