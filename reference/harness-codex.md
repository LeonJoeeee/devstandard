# DevStandard in Codex

Use the shared `core.md` and `reference/orchestrator.md` for a main Codex session. This
page maps their harness-specific mechanics; it does not create another workflow.
Paths resolve from this plugin root. User instructions and the host's permissions take precedence.

## Context and project memory

The trusted SessionStart hooks deliver the shared core, orchestrator role, and this adapter.
After resuming an older session, read any missing shared artifact in full. If hooks are disabled
or awaiting trust, invoke `$devstandard` to read the same sources explicitly; that fallback
loads instructions but does not install or trust a tool guard.

Codex automatically discovers a project's `AGENTS.md`. Also read its existing `CLAUDE.md`
explicitly when the workflow requests operational memory. Respect both; keep each fact at its
established source. Do not copy the whole method into either project file or change global
instructions merely to enable this plugin. Resolve superpowers skills from the available skill
catalog and read their `SKILL.md` at the role's trigger.

## Dispatch and acceptance

Codex does not load the Claude agent definitions in `agents/`. For governed worker and reviewer
lanes, run the existing `scripts/dispatch` and `scripts/review-packet start` with explicit
`--implementation codex`. This is the Codex host adapter's supported executor path; the shared
native-subagent default continues to apply in Claude Code. Do not invoke a nonexistent Claude
Agent tool or translate its agent-spawn JSON into a Codex subagent call.

The dispatcher supplies the complete role, issue, lane, model, effort and sandbox to `codex exec`.
It marks the child `DEVSTANDARD_ROLE=worker` or `reviewer`; plugin startup then skips the
orchestrator context and the inherited guard uses the assigned role. Keep that marker inside
those dispatched processes; do not set it globally. Workers may use their own built-in
subagents within their task under `reference/worker.md`. A gating review remains a fresh,
read-only process and publishes through the existing review-packet machinery.

Use the host's process tools to observe the returned log, completion marker and output; a PID
is not evidence of completion. Dispatch supports macOS and Linux using a detached Python
supervisor, with no external `setsid` or `nohup` prerequisite. Windows dispatch is not qualified.
Keep the existing guard, sandbox, green-CI and clean-review requirements.

## Hook trust

Codex requires trust for plugin hooks independently of plugin installation. Review and trust
DevStandard's hook definitions through Codex's `/hooks` interface, then start a new session.
Do not change permissions or bypass trust to repair a missing automatic load. If the host does
not expose hook trust, use the skill entry and report that the PreToolUse guard is inactive.

Official contracts: [plugins](https://developers.openai.com/plugins/build/plugins),
[hooks and trust](https://learn.chatgpt.com/docs/hooks).
