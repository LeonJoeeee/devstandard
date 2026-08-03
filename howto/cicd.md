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

Artifacts: upload one only when a later step or a person actually consumes it, and always set `retention-days:` — the default keeps every copy for 90 days, and on a private repo the 500 MB storage quota fills in days of routine pushes, after which uploads start failing. CI output is not an archive: anything worth keeping ships through the release pipeline, and any build can be reproduced from its commit.

Minutes are the other finite quota, and the one that stops everything: on a private repo an exhausted monthly balance runs *no* workflow at all — CI, release and Dependabot alike — so the merge gate goes absent rather than red (a public repo's standard runners are free, so this cannot happen there). Treat exhaustion as a pipeline-spend bug before an allowance problem; the usual causes are cheap to fix — a job triggering on every push to every branch when `pull_request` alone would do, a matrix kept wide out of habit, no dependency cache so every run re-downloads the world, no `paths:` filter so a docs typo rebuilds everything, and the default 6-hour `timeout-minutes` letting a hung job burn an afternoon. Fix the spend, and tell the human the balance is out — topping it up, or making the repo public, is theirs. The fallback below is what you do meanwhile, never the answer.

A self-hosted runner is the other way out, and it is not a degradation: GitHub still triggers the run, `ci.yml` still defines it, the verdict still lands on the PR, and branch protection still enforces it — only the compute moves to a machine you own (a one-line `runs-on:` change), so no minutes are charged. Standing one up is the human's call, like topping up and going public. It costs what it costs: the machine has to be up when a PR lands — an offline runner leaves the run queued indefinitely, which is not an outage and not a trigger — its environment drifts under you rather than being rebuilt each run, and it must never be used on a public repo, where any fork's pull request would run its own code on your hardware. When the constraint is minutes rather than a platform that is down, reach for this before the fallback below.

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

## Driving a PR to green

core.md: opening a PR is not done — its opener owns it until every check on it reports green and every review-bot finding is fixed or answered on the PR. Here is what that costs in practice.

**What counts, and what green means.** Every check the PR reports, and every finding a review bot posts on it — static analysis, security scanners, style bots. A check that has not reported is not green: queued is not green, in-progress is not green, and a PR whose checks have not started is not a finished PR. A finding with no fix and no reply is unhandled — the reply on the PR is what lets GitHub alone show it was considered.

**Bot findings run on the check-1 discipline** — verify first, fix what is right without commentary, refute what is wrong with the evidence (`aids/worker-brief.md`). One difference, and only one: the answer goes on the PR, because no re-review settles a bot. A reasoned dismissal on the PR is a legitimate resolution; silence is not, and neither is obeying a finding you know to be wrong.

**A red check is not an opinion.** It cannot be answered or waited out — and there are three states, not two. Your diff caused it → fix the diff. Your change deliberately made the check's assumption stale, the case right after a structural change where the check asserts something the new structure changed on purpose → fix the check in the same PR, naming the staled assumption and why your change staled it, in both the implementer's report and the PR description; that repair is a gate change, and since a diff touching CI cannot be vouched for by CI, check 1 is the only check it gets (`aids/code-review-prompt.md`). Neither → it is not your diff to fix and not yours to work around: `main` is red (core.md's revert-first path — restoring green outranks this PR; rebase once it is green) or the pipeline aged out from under you (the section above — fix the pipeline, in its own PR). Say what you observed on the PR and let the owning rule run. Loosening an assertion because it is inconvenient is the banned weakening of a done-check applied to CI, in every one of the three states.

**Not a route into the fallback below — and the fallback is not a breach of this.** That fallback triggers on *no run at all*, from two named platform causes; a check that ran and failed is CI working, so red authorises nothing here. In the other direction: while a declared fallback is in force there are no checks to drive green, and a required check parked at "Expected — waiting for status to be reported" is that state, not a never-green check to escalate. The fallback's own order governs that merge; this section resumes at the return.

**Taking delivery.** A dispatched worker terminates when it returns; it cannot watch a run that finishes minutes later, and the method never pretends otherwise. The duty transfers at delivery: the main session's first act on a returned PR is to look at its checks, not to spawn check 1 — a reviewer's time is wasted on a diff that is about to change. Two ways to finish it. The main session drives the PR green itself on the worker's branch: its worker has terminated, so one-writer-per-worktree holds, and the merging session already owns that branch's teardown. Or it re-dispatches, handing over the new CI output and bot findings — which is the "change something before you re-dispatch" the ladder requires (core.md), and which makes that branch and worktree the new worker's outright, not "another worker's branch". Where a worker spawned a worker, the handback rides up the chain like a stop message: passing it on is each intermediate's job, and a summary that quietly drops an unreported check is how the duty ends up held by nobody. A PR whose worker terminated mid-run is not a rotting PR; it is the main session's — as is a PR a bot opened (a Dependabot pin bump), which has no session behind it at all. A PR the main session opened itself never transfers: it holds it to green.

**Handing back is not finishing.** A check you watched fail is not "unreported" — it is unfinished work, and naming it in a handback does not finish it. What may be handed back is a run that has not reported yet, when the doer genuinely has to return before it does: the PR link, and the unreported checks named. Wait for the run if you can; the handback is the exception, not the exit.

**When a check can never go green.** Someone else's required check that is broken, a job needing a secret this repo does not have, a bot demanding something the human already ruled out. Name it rather than absorb it: post on the PR what you observed and what you tried, hand it to the main session, and the main session takes it to the human. The PR then sits in a stated, visible blocked state — waiting is legitimate only once it is written on the PR. What ends it is a change landed through the ordinary ceremony: a visible, tracked quarantine of a flaky test (`aids/worker-brief.md`), a pipeline fix in its own PR, or the human deliberately editing the required-check list. Never a waiver improvised in chat to get this one PR through — a human's "looks fine" is not a green check, and the one place a human waiver has a defined meaning is the never-*reporting* required check under the fallback below. And never an agent disabling, deleting or making a check permissive: that does more damage than the merge it was buying. A check that fails then passes with no code change has not gone green either — it has shown you a flake: one re-run identifies it, a second is hope, not a plan, and from there the flaky-check rule governs (a tracked, reviewed quarantine).

## When CI cannot run at all (the check-2 fallback)

core.md makes green CI on the merged result check 2 because it is automated, impartial, and doesn't grade its own work. A local run gives up all three — same machine, same environment, run by an interested party — so what follows is a declared, evidenced, temporary degradation, never a second lane.

**The trigger is the platform, not your patience and not your repo.** It fires only when the platform produces no run for any push: the Actions minutes quota is exhausted (private repos only), or the CI platform (GitHub) is down (check the status page). Both are outside this repo, and both can be proved. Prove it, and tell the human: removing the cause is theirs.

**Never triggers.** CI is slow; CI is queued behind other jobs (a queued run is a run — GitHub reports `queued` before `in_progress`); CI is flaky; you would rather not wait; the session is nearly over. And **a red CI is the opposite of a trigger** — a run that starts and fails is CI working (a job that never starts for billing reasons is not a red run — that is the quota case above). Red on a branch means fix the branch; red on main is core.md's revert-first path; red because the pipeline aged is the section above (fix the pipeline). Reaching for the local suite in any of those is the self-grading bypass this rule exists to prevent.

**Repo-side silence is a bug, not a trigger.** No run appeared because the workflow file is invalid YAML, the workflow is disabled in the Actions tab, or the `on:` filters no longer match this branch — fix that in a PR and CI is back in minutes. "Would pushing again produce a run?" does *not* settle these: pushing again to a broken workflow also produces nothing. Ask instead: *is the cause outside this repo?* If it isn't, this section does not apply.

**Actions switched off at the org level is neither.** It is outside this repo, so no PR of yours can fix it — and it is not a platform event, so it is not a trigger either. Lifting it is the human's or the org admin's; say so, and the merge waits.

**A repo with no CI is not in fallback.** It has no check 2 to degrade, and nothing here would ever end. Either the human declared a light start (core.md: "CI only, or nothing") and that declaration governs, or the change deserves a gate — then add the CI template above, which is one PR, and merge under the real check 2.

**If you cannot tell, CI can run.** No `gh` auth, no network, an Actions tab you can't read: that is your visibility failing, not the platform. Establish the state or wait — an unproven outage is not an outage.

**Who runs it, and on what tree.** The merging main session — never the worker, never a helper — and never the branch as pushed: `git fetch`, build the merge result locally against current `origin/main`, then run every job CI would have run, unfiltered and to completion (not just the tests the change touches). That keeps two of CI's three properties: the merged state against current main, and a run nobody can quietly skip. Impartiality is the one genuinely lost, which is why the run is published and audited instead of self-certified — including when the merging session wrote the diff itself, the ordinary case for a main-session short-branch fix. A worker's own done-check evidence is never check 2, whatever it ran.

**A partial run is never check 2.** If a job can't run locally — it needs secrets, a live service, another OS, a GPU — you have no fallback for that job. Wait for the platform, make the job runnable (a seeded fixture, a container, a documented local mode, in its own PR), or take it to the human. Never merge on the subset that happened to be runnable and call it evidence.

**Unblocking a protected main is the human's call, not yours.** With the required check never reporting, the PR sits at "Expected — waiting for status to be reported" and the merge button is dead — for admins too, because "Do not allow bypassing" is on. Do NOT drop the required check, untick the bypass setting, edit the ruleset, or push to main directly. Name the PR to the human and ask; the human either removes the cause (top up minutes, make the repo public) or waives the check, and protection is restored in the same session the merge lands. An agent that switches the gate off to get past it has done more damage than the unverified merge. Where protection doesn't apply (free-plan private repos) nothing blocks the button — the same evidence and the same audit are owed all the same.

**The order flips: evidence first, then check 1.** Normally check 1 precedes check 2. Under the fallback, run the suite and post the evidence *before* check 1, and hand that comment to the reviewer with the diff — an impartial clean reader auditing the run is the closest available substitute for an impartial runner. If check 1 sends the diff back, or the rebase moves, redo the run: the last evidence on the PR must come from the tree that actually merged.

**What goes on the PR**, as a comment before the merge, so GitHub alone reconstructs why this change merged without a CI run. Keep the `CI-FALLBACK` marker literal — the return sweep searches for it:

    CI-FALLBACK (check 2 degraded)
    Reason: minutes quota exhausted | provider outage
            + proof (billing/usage page or `gh api` output; status-page incident id)
    Merged state: base <SHA> = current origin/main tip; head <SHA> = this PR's head
    Run at: <UTC timestamp>
    Runner: main session — <OS, toolchain versions>
    $ git status --porcelain   -> (empty)
    $ <command>          -> exit <code>
    <output tail>
    (one block per CI job; every job covered, none skipped or filtered)

**No releases under the fallback.** The release pipeline is a workflow too: pushing `vX.Y.Z` while runs are impossible publishes nothing and leaves a tag that looks shipped. Hold the release until the return, then tag.

**Main is unverified, not red.** Dispatch continues — the stop-the-line rule answers a failing run, and there is no run. What ends the uncertainty is the sweep, not a pause.

**The return path.** The fallback ends the moment a push can produce a run again — no grace period, no standing "fallback mode"; the next merge is back on check 2. Re-verification is free: `main`'s first CI run after the return covers every commit merged under the fallback at once. Green closes them — nothing is re-reviewed. Red makes them the prime suspects: search closed PRs for `CI-FALLBACK` to get the list, and the red-main rule applies as written (revert first; fix forward only when the fix is obvious and takes minutes). Don't let that first run wait for the next task — when minutes reset or the outage clears, trigger a run on `main` yourself, and confirm protection is back on.

**If the fallback fires more than occasionally, the pipeline is the bug, not the gate** — see the minutes paragraph under the CI template above.

## Repo CLAUDE.md (generated in the same setup step)

CI settles the project's commands — capture them while they're fresh: generate a repo-root `CLAUDE.md` — when there is something to put in it (below) — one page hard max. Claude Code reads it natively at every session start in the repo, so it is the one place operational facts reach every clean-context worker automatically. Three kinds of content — plus one conditional fourth, and nothing else:

- **Commands** — install, test, run (the same ones CI just encoded);
- **Environment gotchas** — ports in use, services that must be up, local-vs-CI differences;
- **Untracked files a new worktree must copy** — the allowlist `aids/worktree-lifecycle.md` copies from (`.env`, keys, local config).

One conditional fourth item — the fence's only exception: a `## Record language` line, when the repo's durable record is not English (core.md's rule). It sits here because a clean-context worker must see it natively; the reasoning behind the choice goes in that repo's ADR log, not here. Its absence means English.

Generate it only when the project actually has some of that to say. A file that merely transcribes what CI already encodes, or that would stand empty under every heading with no record language to declare, is noise every later session pays to read — skip it, and let the first real command, gotcha, copy-list line or record-language declaration create it through the same write-back lane.

It grows one line at a time: whoever merges a task that exposed a command, gotcha, or rule writes it back (the worktree checklist's Death step) through a short-branch PR like any other change. Architecture, decisions, and task state never go here — the template's last line is the fence; the record-language line is its one exception.

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
