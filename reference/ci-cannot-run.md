# When CI cannot run at all (the check-2 fallback)

core.md makes green CI on the merged result check 2 because it is automated, impartial, and doesn't grade its own work. A local run gives up all three — same machine, same environment, run by an interested party — so what follows is a declared, evidenced, temporary degradation, never a second lane.

**The trigger is the platform, not your patience and not your repo.** It fires only when the platform produces no run for any push: the Actions minutes quota is exhausted (private repos only), or the CI platform (GitHub) is down (check the status page). Both are outside this repo, and both can be proved. Prove it, and tell the human: removing the cause is theirs.

**Never triggers.** CI is slow; CI is queued behind other jobs (a queued run is a run — GitHub reports `queued` before `in_progress`); CI is flaky; you would rather not wait; the session is nearly over. And **a red CI is the opposite of a trigger** — a run that starts and fails is CI working (a job that never starts for billing reasons is not a red run — that is the quota case above). Red on a branch means fix the branch; red on main is core.md's revert-first path; red because the pipeline aged is `reference/ci-pipelines.md`'s "When CI goes red with no change of yours" (fix the pipeline). Reaching for the local suite in any of those is the self-grading bypass this rule exists to prevent.

**Repo-side silence is a bug, not a trigger.** No run appeared because the workflow file is invalid YAML, the workflow is disabled in the Actions tab, or the `on:` filters no longer match this branch — fix that in a PR and CI is back in minutes. "Would pushing again produce a run?" does *not* settle these: pushing again to a broken workflow also produces nothing. Ask instead: *is the cause outside this repo?* If it isn't, this section does not apply.

**Actions switched off at the org level is neither.** It is outside this repo, so no PR of yours can fix it — and it is not a platform event, so it is not a trigger either. Lifting it is the human's or the org admin's; say so, and the merge waits.

**A repo with no CI is not in fallback.** It has no check 2 to degrade, and nothing here would ever end. Either the human declared a light start (core.md: "CI only, or nothing") and that declaration governs, or the change deserves a gate — then add the CI template from `reference/ci-pipelines.md`, which is one PR, and merge under the real check 2.

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

**If the fallback fires more than occasionally, the pipeline is the bug, not the gate** — see the minutes paragraph in `reference/ci-pipelines.md`.
