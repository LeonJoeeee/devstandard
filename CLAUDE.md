# DevStandard — repo notes for agents

## Commands

Docs-only plugin — no build, no test suite; CI runs exactly four checks, reproducible locally from the repo root:

- Hook emits valid JSON: `./hooks/session-start | python3 -c "import json,sys; d=json.load(sys.stdin)['hookSpecificOutput']; assert d['hookEventName']=='SessionStart' and 'DevStandard' in d['additionalContext']; print('ok')"`
- core.md token budget (hard ceiling 5000): `python3 -c "print(int(len(open('core.md').read().split())*1.35))"`
- No `@path` references in core.md / howto/ / aids/ (they force-load context).
- `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` versions in lockstep.

## Gotchas

- Check the core.md token count BEFORE pushing any core.md edit — the ceiling is hard, CI fails at 5001; lean rule unchanged (the ceiling is headroom, not a target).
- Every core.md edit must be mirrored in core.zh-CN.md (Chinese mirror for humans; English is canonical and injected).
- Worktrees live as siblings of the repo: `../devstandard-wt-<slug>` (no gitignored worktree dir inside).
- Release = bump both versions in lockstep, merge, then push tag `vX.Y.Z` — release.yml is idempotent; releasing is the human's call.

## New worktree: copy these untracked files

- none — everything load-bearing is tracked.

Architecture: see docs/architecture.md — never duplicated here. Decisions: docs/adr/. Tasks: GitHub issues.
