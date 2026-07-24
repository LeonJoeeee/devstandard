# How to set up CI + the release pipeline

Read this at project start, after the skeleton exists. Two robots, generated once — then they age with GitHub, not with the project:

- **CI** — runs the tests on every push/PR. The rule it enforces: *nothing merges to main unless tests are green.* With parallel sessions sharing main as their foundation, this gate cannot rely on anyone remembering to run tests.
- **Release (CD)** — every project must ANSWER the release question: *what does "shipping" mean here?* A service → deploy; a tool/library → publish a package; a plugin → publish to its marketplace/repo. Default trigger: **a version tag** — pushing `vX.Y.Z` releases automatically; the human decides when to tag. Fully-automatic release-on-merge is a per-project opt-in, not the default.

Adapt the templates to the project's language/toolchain (swap the test command and the release steps). Keep each file minimal — these are gates, not build systems.

## CI template (`.github/workflows/ci.yml`)

```yaml
name: CI
permissions:
  contents: read
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

The CI token only needs to read the code; a job that must write (like the release template) escalates its own permissions per-job.

Third-party (non-`actions/*`) actions: pin to a full commit SHA, not a tag — a tag can be rewritten under you (the 2025 tj-actions compromise; SHA-pinned repos were immune). First-party `actions/*` at a version tag is fine. A SHA never updates itself — that is exactly what the Dependabot file below keeps current.

After the first push, enable branch protection on `main` requiring the `test` check — that turns the rule into a hard gate. Three settings make the gate real:

- **"Require branches to be up to date before merging"** — green on a stale base is not green on main; two individually green branches can merge into a red main. A merge queue fits only if it lands the exact reviewed commits (conflict-free fast-forwards) — GitHub's built-in queue never does: every merge method it offers builds a new merge result the check-1 reviewer never saw. Skip the queue: keep this setting instead, and re-run check 1 after any rebase (core.md).
- **"Do not allow bypassing the above settings"** — without it, admins are exempt, and in a solo setup every agent session runs on the owner's admin credentials.
- Know your plan: on free-plan **private** repos branch protection doesn't apply — the gate is convention-only there.

Protection changes only who enforces the ceremony, not the ceremony itself. Under DevStandard every change — however small — rides a branch + PR + fresh review + green CI (core.md); protection doesn't create a lighter lane for small changes. A protected main just makes GitHub *enforce* that gate (no direct push to main, required checks) instead of leaving it to the agents' discipline. Where protection doesn't apply (free-plan private repos), the same gate is convention-only there — it binds all the same; the only difference is whether the platform blocks a violation or a reviewer catches it after.

## Pipeline pin upkeep (`.github/dependabot.yml`, generated in the same setup step)

The pipeline's own parts — the `uses:` pins in these workflows — rot on GitHub's clock, not the project's: actions age out of support and a SHA pin never updates itself. Generate this file in the same setup step; a bot then opens PRs bumping those pins as new versions land, and each rides the normal two checks like any other change. This keeps the pipeline's own actions current only — the project's own dependencies stay out of the method's scope (that ruling stands, now narrowed to say so explicitly).

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

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

## When CI goes red with no change of yours

A green run means the code passed today, not that the pipeline is current. GitHub ends-of-life the runtimes its actions run on, on its own cutoff dates — so a pipeline with zero project changes can go from green to red, usually after months of deprecation-warning annotations inside still-green runs. If a gate goes red mid-task with no relevant change of yours, suspect a vendor deprecation before your own code; when a task already touches a workflow file, bump any `uses:` the run flags as deprecated in the same diff.

## Repo CLAUDE.md (generated in the same setup step)

CI settles the project's commands — capture them while they're fresh: generate a repo-root `CLAUDE.md`, one page hard max. Claude Code reads it natively at every session start in the repo, so it is the one place operational facts reach every clean-context worker automatically. Three kinds of content, nothing else:

- **Commands** — install, test, run (the same ones CI just encoded);
- **Environment gotchas** — ports in use, services that must be up, local-vs-CI differences;
- **Untracked files a new worktree must copy** — the allowlist `aids/worktree-lifecycle.md` copies from (`.env`, keys, local config).

It grows one line at a time: whoever merges a task that exposed a command, gotcha, or rule writes it back (the worktree checklist's Death step) through a short-branch PR like any other change. Architecture, decisions, and task state never go here — the template's last line is the fence.

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
