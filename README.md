# DevBook

A development method packaged as a Claude Code plugin: repo-creation lifecycle (PRD / architecture / ADR + thin skeleton + CI/CD), parallel-session collaboration standards, and execution discipline. One page (`core.md`) is injected per session by a SessionStart hook; templates (`howto/`) and helpers (`aids/`) load only when read.

The method itself is documented in this repo's own `docs/` (PRD, architecture, ADRs) — DevBook is built with its own rules.

## Install

**Try it / develop it (zero pollution of other sessions):**

```bash
claude --plugin-dir ~/projects/devbook
```

The plugin (and its hook) is active only in sessions started with the flag. Edits to `core.md` take effect live; edits to `hooks/` need `/reload-plugins`.

**Permanent (user level, all sessions):** add this directory as a local marketplace and install, or place it under `~/.claude/skills/` as a skills-dir plugin. Do this only once the content is stable — the hook injects `core.md` (~700 tokens) into every session.

## Layout

```
core.md          the injected page: trigger rule + execution discipline + standards
hooks/           SessionStart hook (injects core.md only)
howto/           PRD / architecture / ADR / CI-CD templates — read at repo creation
aids/            optional helpers — reviewer prompt, testing anti-patterns, debugging
docs/            DevBook's own PRD, architecture, ADR log
_source/         research & migration source material (not part of the plugin)
```

## License

MIT. `aids/` files are adapted from [superpowers](https://github.com/obra/superpowers) (MIT, Jesse Vincent).
