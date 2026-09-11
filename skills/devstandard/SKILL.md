---
name: devstandard
description: Use when the user asks to use DevStandard for a repository, or when working in a project that has adopted its GitHub issue, isolated worker, PR, and acceptance workflow.
---

In Codex, read [the Codex adapter](../../reference/harness-codex.md) in full. In Claude Code,
use the shared roles directly. Resolve method paths from this plugin root, two directories
above this skill.

For a main session, read [core.md](../../core.md) and
[the orchestrator role](../../reference/orchestrator.md) in full unless already delivered by
SessionStart. Follow that shared workflow within the user's requested scope and permissions.

If the dispatch brief assigns worker or reviewer, follow that supplied role instead; do not
load the orchestrator role or promote yourself to it. Read project `AGENTS.md` and existing
`CLAUDE.md` before repository work. The adapter explains Codex dispatch and hook trust.
