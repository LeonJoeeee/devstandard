# CI Maintenance: Industry Practice vs. DevStandard — Alignment Report

> Non-normative research artifact backing issue #34. Produced 2026-07-24 by a 17-agent research workflow: 5 source-grounded lenses (keeping-green, pipeline rot, test health, pipeline security, config integrity) → gap map vs current text → adversarial refutation → synthesis. Backs the CI-maintenance industry-alignment fix batch; not itself a normative method document.

## 1. TL;DR

Industry practice contradicts the "two robots, generated once" framing on one narrow but real point, and vindicates it on most others. A GitHub Actions pipeline ages on the vendor's clock, not the project's — runtimes reach end-of-life and deprecated actions hard-fail on fixed cutoff dates, after months of warnings inside still-green runs — so a pipeline with zero project changes will one day flip red, and our docs currently give an agent no way to interpret that. Beyond that framing fix, the verified gaps are small and cheap: a one-line least-privilege `permissions:` block missing from the CI template, a gate-change clause missing from the reviewer prompt (green CI cannot vouch for a change to CI itself), and a flake rule missing from the worker brief (the docs currently trap an agent between retry-to-green and the never-skip ban). Everything else industry does — scheduled builds, build-cop rotation, coverage gates, required-check babysitting — is either already covered by our structure, refuted for our target shape, or collides with a settled scope ruling and is surfaced below for the human's re-decision (revert-first, Dependabot for the pipeline's own action pins, SHA-pinning third-party actions). The confirmed fix batch touches three files and never touches core.md, so no Chinese-mirror work is needed.

## 2. The industry picture

**Keeping green** — A red mainline is the single highest-priority item: fix or revert before anything else, don't build on a broken base; default recovery is revert-to-last-known-good unless the fix is trivially fast. Strongest sources: Fowler ("Fix Broken Builds Immediately", ~10-minute rule), DORA, trunkbaseddevelopment.com. Near-universal.

**Pipeline rot** — CI decays on the vendor's clock: GitHub retires runner images, EOLs the Node runtimes actions run on, and hard-fails deprecated actions on cutoff dates — deprecations appear as warnings in green runs, then flip red all at once. Keeping the pipeline's own action versions current is a near-universal automated background task (Dependabot in 69.2% and Renovate in 21.0% of workflow histories — arXiv 2602.14572, 2026; GitHub Changelogs 2024–2026).

**Test health** — Flakiness accumulates continuously and is the largest ongoing CI duty: Google measured ~16% of tests flaky and ~84% of retried failures as flakes; the norm is quarantine-and-file-a-bug, never retry-to-green (Google Testing Blog "Flaky Tests at Google"). Coverage-percentage gates are genuinely contested (Fowler/Marick reject them as Goodhart-able).

**Pipeline security** — The recommended hardening is overwhelmingly set-once: top-level `permissions: contents: read` with per-job escalation (GitHub security-hardening guide; OpenSSF Scorecard rates the write-default High risk). The one practice with ongoing upkeep is SHA-pinning third-party actions, made real by the March 2025 tj-actions/changed-files compromise (~23,000 repos exposed; SHA-pinned repos immune).

**Config integrity** — Pipeline-as-code with review on every change is near-universal, plus extra scrutiny on diffs that touch the gate itself, because the gate can't vouch for a change to itself (commonly via CODEOWNERS on `.github/workflows/`). The required-check name-drift gotcha is well documented (GitHub docs), though its common failure branch is loud, not silent.

## 3. Already aligned

| Practice (industry norm) | Where our text covers it |
|---|---|
| Pipeline-as-code: CI config in-repo, changes ride reviewed PRs | howto/cicd.md:63; core.md:59 branch test routes workflow edits through the two checks |
| Don't merge onto a stale/red base | howto/cicd.md:33 ("Require branches to be up to date… two individually green branches can merge into a red main") |
| A single always-known owner of build health | core.md:73 ("Merging is the main session's job, as the decider") — structural ownership; only the rotation mechanism doesn't transfer |
| No silent test weakening/deletion to get green | core.md:68 / worker-brief:18 ("NEVER: … weaken, skip, or delete the done-check to make it pass") |
| Test quality via review, not a coverage-percentage gate | code-review-prompt.md:7 (reviewer owns "do the tests test real behavior… not weakened to pass") |
| Per-job least-privilege escalation where a job writes | howto/cicd.md:50–51 (release template models `permissions: contents: write`) |
| Green tests gate the release path too | howto/cicd.md:56 ("green tests gate the release too") |
| CI extended when a new top-level package/app/service stands up | core.md:9–10 (new top-level thing → full setup incl. CI + release pipeline) |
| Close the admin-bypass hole | howto/cicd.md:34 ("Do not allow bypassing…" — solo sessions run on owner admin credentials) |
| Commands captured in sync with CI at setup | howto/cicd.md:69 + Death-step write-back (worktree-lifecycle:19) |

## 4. Confirmed gaps — the fix batch

Four gaps survived adversarial verification. All wordings below are the verified lean versions.

### 4.1 "Generated once" is false: CI ages on GitHub's clock — `howto/cicd.md`
- **Industry norm:** GitHub EOLs action runtimes and hard-fails deprecated actions on fixed cutoff dates, preceded by warning annotations inside green runs (GitHub Changelogs 2024-09-25, 2026-05-14, 2025-09-19). Platform behavior, not a choice. (Note: runner-image retirement does NOT bite template-followers — our template uses `ubuntu-latest`, which tracks forward; the live vectors are runtime EOL and deprecated-action hard-fail.)
- **Ours now:** cicd.md:3 — "Two robots, generated once:" — no maintenance clause anywhere in the repo (grep-verified).
- **Fix:** change line 3 to "Two robots, generated once — then they age with GitHub, not with the project:" and add ONE note after the templates: *"A green run means the code passed today, not that the pipeline is current. GitHub ends-of-life the runtimes its actions run on, on its own cutoff dates — so a pipeline with zero project changes can go from green to red, usually after months of deprecation-warning annotations inside still-green runs. If a gate goes red mid-task with no relevant change of yours, suspect a vendor deprecation before your own code; when a task already touches a workflow file, bump any `uses:` the run flags as deprecated in the same diff."*
- **Why it matters:** the green-CI gate is the method's safety mechanism; an agent meeting an unexplained red gate with no doc saying this is expected will burn a session misdiagnosing its own code or — worse — distrust the gate.
- **Human call inside this gap:** the final `uses:`-bump clause brushes the settled dependency-automation ruling. It is manual and opportunistic (only when a task already touches the workflow file), not bot-driven — verified as outside the ruling, but confirm the boundary or cut that clause and keep only the interpret-the-red-gate guidance. This clause is also the sole fallback if the Dependabot question (§5, item B) stays "no bot."

### 4.2 CI template ships without a least-privilege permissions block — `howto/cicd.md`
- **Industry norm:** top-level `permissions: contents: read`, escalate per job (GitHub security-hardening guide; OpenSSF Scorecard Token-Permissions, High risk). Write-once, zero upkeep.
- **Ours now:** cicd.md:12–29 — CI template has no `permissions:` block, so the token inherits the repo default (frequently read-write on solo/personal repos — exactly our target shape). The release template (lines 50–51) already models the fix; the asymmetry is the tell.
- **Fix:** add at top level, right after `name: CI`:
  ```yaml
  permissions:
    contents: read
  ```
  plus one sentence under the template: *"The CI token only needs to read the code; a job that must write (like the release template) escalates its own permissions per-job."*
- **Why it matters:** an agent copying the template verbatim ships a workflow whose token can push code; any later third-party action turns that into the tj-actions-style write-token exposure. Green CI (check 2) gates test-pass, not token scope.

### 4.3 Check-1 reviewer has no gate-change clause — `aids/code-review-prompt.md`
- **Industry norm:** changes touching CI/workflow files get extra review scrutiny because the gate can't vouch for a change to itself; new third-party actions are vetted before adoption (GitHub security-hardening guide; CVE-2025-30066/tj-actions; big-org CODEOWNERS — mechanism doesn't transfer, insight does).
- **Ours now:** the "What to check" list (lines 24–38) has only generic "security"; "tests not weakened" is framed as test-code quality, not workflow-YAML edits; nothing covers a newly added action. Check 2 is structurally blind here — it grades using the very gate being changed.
- **Fix:** add ONE item to "What to check" (after Architecture, ~line 30): *"Gate changes: if the diff touches `.github/workflows/` or CI/branch-protection config, green CI cannot vouch for it — this review is the only check. Flag any step that weakens or disables the gate, and any newly added third-party action that isn't version-pinned to a trusted source (it runs untrusted code with repo + secrets access)."*
- **Why it matters:** today a diff that quietly comments out the test step, or adds a malicious action, passes both merge checks; the solo setup has no second human to catch it.

### 4.4 No flake rule: agents are trapped between retry-to-green and the never-skip ban — `aids/worker-brief.md`
- **Industry norm:** a fails-then-passes-without-code-change result is a flake — quarantine off the blocking path AND file a tracked fix; never retry-to-green, never silently delete (Google Testing Blog: ~16% of tests flaky, ~84% of retried failures were flakes).
- **Ours now:** no flake concept anywhere (grep-verified). worker-brief:17's "re-run and re-capture" pushes an agent to re-run a done-check a flake can flip green; worker-brief:18's never-skip ban then forbids the honest exit. The stop-trigger (line 25) can't fire until the agent already has the concept it's missing.
- **Fix:** ONE rule in the Boundaries section (no core.md pointer): *"A done-check that fails then passes with no code change is flaky, not a real result — don't re-run it until it goes green (that hides the flake), and don't 'fix' code that isn't broken. Quarantine it as its own visible change (skip/mark the test, open an issue to fix or delete it deliberately) and say so — a tracked, reviewed quarantine is not the banned silent weakening; the ban is on hiding it."*
- **Why it matters:** without it an agent acts wrongly either way — masks the flake by looping, or wastes a session "fixing" code that isn't broken.

### Batch summary
| File | Edits |
|---|---|
| howto/cicd.md | 4.1 (line-3 reframe + one note after templates) and 4.2 (permissions block + one sentence) |
| aids/code-review-prompt.md | 4.3 (one "What to check" item) |
| aids/worker-brief.md | 4.4 (one Boundaries rule) |

**zh-mirror note:** no confirmed gap touches core.md, so no core.zh-CN.md mirror work and no token-budget check for this batch. (If §5 item A is adopted, that changes — see below.)

## 5. Conscious divergences and settled-ruling collisions

### Deliberate non-adoptions (no action needed)
- **Build-cop / build-sheriff rotation** — scale mismatch; the main session already structurally owns main's health (core.md:73). Rotation needs a team.
- **Coverage-percentage gates (70–85%)** — contested even in industry (Fowler/Marick: Goodhart); our review-based test-quality defense is arguably sharper.
- **CODEOWNERS on `.github/workflows/`** — the mechanism needs a second human; the insight lands via gap 4.3.
- **Flake-detection / auto-quarantine tooling** — big-org infrastructure; we adopt only the mental model (gap 4.4).
- **Two-stage fast/slow pipeline split, ten-minute build budget** — our templates are "gates, not build systems" (cicd.md:8); speed engineering is per-project tooling, not method.
- **Scheduled/nightly builds** — refuted for our shape (see §6); its dominant industry purpose (expensive suites too slow per-commit) doesn't apply to a minimal gate.
- **Bot-driven PRs for the project's dependencies** — settled ruling, and nothing in this research forces reopening it for project deps.

### conflicts_settled — industry says X, our ruling says Y, human's call
**A. Revert-first as the default way back to green** (evidence: strong — Fowler, DORA, trunkbaseddevelopment.com; near-universal). Industry says: revert the offending commit as the default recovery; fix forward only when trivially fast. Our ruling says: broken-main recovery procedure is out of scope. Context for the re-decision: the ruling was made without this being on the table as a one-line ordering rule, and revert-first is unusually agent-suited — the low-judgment, seconds-fast, safe move, versus an agent improvising a forward fix on the base everyone branches from. Red main survives our gates via flaky/time-dependent tests, upstream drift, and main-only environment differences. If adopted: the clause *"restore green by reverting the offending commit unless the fix is obvious and takes minutes"* has no existing home (core.md has no red-main line — the proposed carrier was refuted, §6), so it would need its own ~2-line home in core.md → triggers the zh-mirror and the token-ceiling check.

**B. Dependabot for the pipeline's OWN action pins** (evidence: first-party — GitHub Docs "Keeping your actions up to date with Dependabot"; Dependabot/Renovate account for 562k of 588k version-bump edits, arXiv 2602.14572; near-universal). Industry says: a bot keeps `uses:` pins current. Our ruling says: no bot-driven dependency PRs — but that ruling targeted the PROJECT's dependencies; this is the pipeline's own. Two-part decision: (a) confirm whether the ruling extends to pipeline pins; (b) if the bot stays out, gap 4.1's opportunistic bump clause is the ENTIRE remaining guard against silent pin rot — so verify that clause lands. If the bot comes in: a ~5-line `.github/dependabot.yml` (github-actions ecosystem, weekly) generated in the same setup step, its PRs riding the normal two-check flow — framed as tooling opt-in, never a mandated method line.

**C. SHA-pinning third-party actions** (evidence: strong and specific — tj-actions Mar 2025, ~23k repos, SHA-pinned repos immune; GitHub hardening guide; OpenSSF Scorecard; GitHub org-level SHA-pin enforcement Aug 2025). Industry says: pin non-`actions/*` actions to a full commit SHA — a tag can be rewritten under you; first-party at a version tag is fine. The coupling the human must see: an immutable SHA never updates itself, so mandating SHA pins quietly requires the update automation of item B — and a blanket no-bots stance quietly pushes toward the less-secure tag pin. **Decide B and C together.** Candidate line for cicd.md under the CI template: *"Third-party (non-`actions/*`) actions: pin to a full commit SHA, not a tag — a tag can be rewritten under you (tj-actions, 2025). First-party `actions/*` at a version tag is fine."* The review-side half already lands conflict-free via gap 4.3.

## 6. Refuted

| Proposed gap | Why it died |
|---|---|
| Red-main response norm in core.md ("stop dispatching until green") | Structure already blocks the material half — check 2 ("green CI on the merged result against current main") means nothing merges onto a red main; the residual is self-announcing, since a worker branching off red main fails its confirm-tests-pass Birth step loudly. Also reopens the settled broken-main ruling. |
| Scheduled/cron CI run to catch idle-repo rot | For our shape (nobody watches CI between sessions) a red cron is seen at the next session — the same moment the next task's push-run surfaces the identical rot; and GitHub disables cron after 60 days idle, exactly when it's most needed. Prevents no concrete failure. |
| Required-check name-drift warning | Check 2 is an ACTIVE confirmation by the deciding agent, not reliance on GitHub's auto-block, so a vacuous required-check list can't make red look green; the common failure branch (un-synced rename blocks every PR) is loud and self-correcting, and job renames are rare in a single-`test`-job template. |
