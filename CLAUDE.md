# DevStandard — repo notes for agents

## Commands

Docs-only plugin — no build, no test suite; CI runs exactly four checks, reproducible locally from the repo root:

- Hook emits a valid, bounded forced-read instruction: `./hooks/session-start | python3 -c "import json,sys; raw=sys.stdin.buffer.read(); assert len(raw)<4000, len(raw); d=json.loads(raw)['hookSpecificOutput']; assert d['hookEventName']=='SessionStart' and 'core.md' in d['additionalContext'] and 'FIRST ACTION' in d['additionalContext']; print('ok', len(raw), 'bytes')"`
- core.md token budget (hard ceiling 5000): `python3 -c "print(int(len(open('core.md').read().split())*1.35))"`
- No `@path` references in core.md / howto/ / aids/ (they force-load context).
- `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` versions in lockstep.

## Gotchas

- Check the core.md token count BEFORE pushing any core.md edit — the ceiling is hard, CI fails at 5001; lean rule unchanged (the ceiling is headroom, not a target).
- Every core.md edit must be mirrored in core.zh-CN.md (Chinese mirror for humans; English is canonical — it is the page the hook forces every session to read).
- Worktrees live as siblings of the repo: `../devstandard-wt-<slug>` (no gitignored worktree dir inside).
- Release = bump both versions in lockstep, merge, then push tag `vX.Y.Z` — release.yml is idempotent. Standing policy since v0.9.3: every merged change releases immediately (per-release approval delegated to the agent, issue #37).

## New worktree: copy these untracked files

- none — everything load-bearing is tracked.

Architecture: see docs/architecture.md — never duplicated here. Decisions: docs/adr/. Tasks: GitHub issues.
