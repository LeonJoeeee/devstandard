# How to set up CI + the release pipeline

Read this at project start, after the skeleton exists. Two robots, generated once:

- **CI** — runs the tests on every push/PR. The rule it enforces: *nothing merges to main unless tests are green.* With parallel sessions sharing main as their foundation, this gate cannot rely on anyone remembering to run tests.
- **Release (CD)** — every project must ANSWER the release question: *what does "shipping" mean here?* A service → deploy; a tool/library → publish a package; a plugin → publish to its marketplace/repo. Default trigger: **a version tag** — pushing `vX.Y.Z` releases automatically; the human decides when to tag. Fully-automatic release-on-merge is a per-project opt-in, not the default.

Adapt the templates to the project's language/toolchain (swap the test command and the release steps). Keep each file minimal — these are gates, not build systems.

## CI template (`.github/workflows/ci.yml`)

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # <language setup step here, e.g. actions/setup-node / setup-python>
      - name: Install
        run: <install command>
      - name: Test
        run: <test command>
```

After the first push, enable branch protection on `main` requiring the `test` check — that turns the rule into a hard gate. Three settings make the gate real:

- **"Require branches to be up to date before merging"** — green on a stale base is not green on main; two individually green branches can merge into a red main. A merge queue fits only if it lands the exact reviewed commits (conflict-free fast-forwards) — GitHub's built-in queue never does: every merge method it offers builds a new merge result the check-1 reviewer never saw. Skip the queue: keep this setting instead, and re-run check 1 after any rebase (core.md).
- **"Do not allow bypassing the above settings"** — without it, admins are exempt, and in a solo setup every agent session runs on the owner's admin credentials.
- Know your plan: on free-plan **private** repos branch protection doesn't apply — the gate is convention-only there.

Protection changes the mechanics of small changes, not the ceremony: on a protected main, a change too small for an issue (core.md's branch test) rides a short-lived branch the main session pushes itself, waits for green CI, and merges itself — no issue, no fresh review. Where protection doesn't apply (free-plan private repos), the direct-to-main lane keeps working as before.

## Release template (`.github/workflows/release.yml`)

```yaml
name: Release
on:
  push:
    tags: ['v*']

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      # <language setup + install + build steps>
      - name: Test
        run: <test command>          # green tests gate the release too
      - name: Publish
        run: <publish/deploy step>   # gh release create / npm publish / deploy ...
```

If the project genuinely has no release form yet, generate CI only and record the open release question in the PRD's constraints — don't invent ceremony.

Both files land in the target repo under `.github/workflows/`.

## Repo CLAUDE.md (generated in the same setup step)

CI settles the project's commands — capture them while they're fresh: generate a repo-root `CLAUDE.md`, one page hard max. Claude Code reads it natively at every session start in the repo, so it is the one place operational facts reach every clean-context worker automatically. Three kinds of content, nothing else:

- **Commands** — install, test, run (the same ones CI just encoded);
- **Environment gotchas** — ports in use, services that must be up, local-vs-CI differences;
- **Untracked files a new worktree must copy** — the allowlist `aids/worktree-lifecycle.md` copies from (`.env`, keys, local config).

It grows one line at a time: whoever merges a task that exposed a command, gotcha, or rule writes it back (the worktree checklist's Death step) through the small-change lane. Architecture, decisions, and task state never go here — the template's last line is the fence.

```markdown
# <Project> — repo notes for agents

## Commands
- install: <command>
- test: <command>
- run: <command>

## Gotchas
- <port / service / local-vs-CI difference worth one line>

## New worktree: copy these untracked files
- <path>   (or: none — everything load-bearing is tracked)

Architecture: see docs/architecture.md — never duplicated here. Decisions: docs/adr/. Tasks: GitHub issues.
```
