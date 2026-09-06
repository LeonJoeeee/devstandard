# CI, the release pipeline, and keeping them current

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

Artifacts: upload one only when a later step or a person actually consumes it, and always set `retention-days:` — the default keeps every copy for 90 days, and on a private repo the 500 MB storage quota fills in days of routine pushes, after which uploads start failing. CI output is not an archive: actual release deliverables ship through the release pipeline; a report worth retaining goes where `reference/where-it-goes.md` sends it rather than being published merely to keep it, and any build can be reproduced from its commit.

Minutes are the other finite quota, and the one that stops everything: on a private repo an exhausted monthly balance runs *no* workflow at all — CI, release and Dependabot alike — so the merge gate goes absent rather than red (a public repo's standard runners are free, so this cannot happen there). Treat exhaustion as a pipeline-spend bug before an allowance problem; the usual causes are cheap to fix — a job triggering on every push to every branch when `pull_request` alone would do, a matrix kept wide out of habit, no dependency cache so every run re-downloads the world, no `paths:` filter so a docs typo rebuilds everything, no `concurrency:` group canceling superseded branch runs, and the default 6-hour `timeout-minutes` letting a hung job burn an afternoon. Fix the spend, and tell the human the balance is out — topping it up, or making the repo public, is theirs. The check-2 fallback (`reference/ci-cannot-run.md`) is what you do meanwhile, never the answer.

The minimal template above includes none of these controls; add the language setup action's `cache:` input, job-level `timeout-minutes:`, `on: pull_request: paths:`, `strategy: matrix:`, and a top-level `concurrency:` group.

A self-hosted runner is the other way out, and it is not a degradation: GitHub still triggers the run, `ci.yml` still defines it, the verdict still lands on the PR, and branch protection still enforces it — only the compute moves to a machine you own (a one-line `runs-on:` change), so no minutes are charged. Standing one up is the human's call, like topping up and going public; how to, and why ephemeral is the default, is `reference/self-hosted-runner.md`. It costs what it costs: the machine has to be up when a PR lands — an offline runner leaves the run queued indefinitely, which is not an outage and not a trigger — its environment drifts under you rather than being rebuilt each run, and it must never be used on a public repo, where a fork's pull request runs its own code on your hardware once approved — one click, under the default policy. When the constraint is minutes rather than a platform that is down, reach for this before the check-2 fallback (`reference/ci-cannot-run.md`).

After the first push, enable branch protection on `main` requiring the `test` check — that turns the rule into a hard gate. Three settings make the gate real:

- **"Require branches to be up to date before merging"** — green on a stale base is not green on main. The guarded merge binds CI to the current base and head; a content-unchanged rebase uses the two-layer proof in `reference/hard-edges.md`, otherwise it needs fresh check 1. Do not use a queue that rebases past that verification.
- **"Do not allow bypassing the above settings"** — without it, admins are exempt, and in a solo setup every agent session runs on the owner's admin credentials.
- Know your plan: on free-plan **private** repos branch protection doesn't apply — the gate is convention-only there.

Protection changes only who enforces the ceremony, not the ceremony itself. Under DevStandard every change — however small — rides a branch + PR + fresh review + green CI (core.md); protection doesn't create a lighter lane for small changes. Required status protection makes GitHub enforce the CI portion; the guarded merge route checks the review record. A pre-green direct push is not prohibited by status protection alone. Where protection doesn't apply (free-plan private repos), the same gate is convention-only there — it binds all the same; the only difference is whether the platform blocks a violation or a reviewer catches it after.

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

The same setup step also generates the repo-root `CLAUDE.md`, when the project has anything to put in it — `reference/repo-claude-md.md` (that file stays the operational memory on every harness). The same founding commit also seeds the in-repo worktree root into `.gitignore` (`/.claude/worktrees/`) — the line every later worktree creation checks for (`reference/worktree-lifecycle.md`, Birth).

## When CI goes red with no change of yours

A green run means the code passed today, not that the pipeline is current. GitHub ends-of-life the runtimes its actions run on, on its own cutoff dates — so a pipeline with zero project changes can go from green to red, usually after months of deprecation-warning annotations inside still-green runs. If a gate goes red mid-task with no relevant change of yours, suspect a vendor deprecation before your own code; when a task already touches a workflow file, bump any `uses:` the run flags as deprecated in the same diff.

Provisioning/check commands and the exact protection payload live in `reference/hard-edges.md`. Classic status protection enforces required checks, not the existence of a Goal/Floor verdict or a PR-only write path for pre-green commits; keep the role guards and reviewed-head merge route.
