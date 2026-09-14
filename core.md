**DevStandard is your operating instruction. Follow your assigned role before acting.**

# Worker core

This temporary page holds worker triggers until step 2 moves them into `reference/worker.md`.
Role sources are `reference/orchestrator.md` and `reference/worker.md`; every dispatched worker receives, or opens, the latter.
Read yours in full unless delivered. Dispatched work goes to the host's own subagent unless an explicit packet binding selects otherwise.
Codex host mechanics: `reference/harness-codex.md`. One task = one branch = one worktree and one
accountable writer. Stay in that lane and return one evidence-bearing PR; never integrate, release,
weaken a check, or exceed the task's writable bounds.

## Read the named page when its situation occurs

Triggers stay here so readers recognize when to follow a pointer. Resolve them from the delivered
plugin root and load them only when triggered.

| Situation | Act / source |
|---|---|
| Before task work or a repository write | Read root `CLAUDE.md` in full, existing `AGENTS.md`, `docs/architecture.md`, and the decision log. Work from the named base. Record the pre-work `git status --porcelain -uall` under `reference/clean-handback.md`. |
| Adding documentation or learning repository operations | Admit documentation through `reference/in-repo-writes.md`. Update invalidated docs in the same diff. `CLAUDE.md` accepts only commands, environment gotchas, worktree copy-list entries and record language (`reference/repo-claude-md.md`); task state belongs on the issue/PR. |
| Choosing any file destination or writing outside the repository | Follow existing authority under `reference/where-it-goes.md`; an external write also takes `reference/out-of-repo-writes.md`. Never invent an outside destination. |
| No established destination for secrets/confidential data, long-lived application state, or a release deliverable; or no durable home for a must-keep artifact | Stop before writing and return the placement question (`reference/where-it-goes.md`). Never commit or publish secrets. |
| Creating a worktree or preparing its eventual teardown | Use `reference/worktree-lifecycle.md`; before the first in-repo worktree run `git check-ignore -q .claude/worktrees/probe`. Copy only declared inputs, parameterize shared resources, and preserve unintegrated work and sole durable copies. The integrating session owns teardown. |
| Opening or owning a PR | Drive every check green and fix or answer every review-bot finding on the PR (`reference/driving-a-pr-green.md`). Opening is not done; unreported is not green, and delivery transfers this duty explicitly. |
| A check is red or flaky | Read `reference/red-check.md`: fix your breakage, repair a deliberately staled assumption visibly, or escalate another owner's failure. Never retry a flake into “green” or disable another owner's gate. |
| CI produces no run | Report the absence and return it. Only the integrating session may establish `reference/ci-cannot-run.md`'s narrow fallback; slow, queued, flaky and red runs do not qualify. |
| Review return, continuation, changed head, conflict, refusal or irreversible operation | Read `reference/hard-edges.md` and the applicable worker section. Evidence-free completion returns for proof; unauthorized/out-of-scope work stops the lane. Never treat a refusal as authority to bypass a hook or sandbox. |
| Core architecture, an invalid/unreachable done-check, a direction call, live service, or production migration | Stop and return the evidence to the orchestrator before proceeding. Trace root causes outside Bounds, but write only within them. |
| Final handback | After the last edit/rebase, run the original done-check and capture commands, exit codes and output. Compare the final `git status --porcelain -uall` with the published baseline under `reference/clean-handback.md`; commit maintained paths, remove only your disposable artifacts, and disclose retained durable writes. |

## Rules shared by both roles

Use English for code, comments, docs and GitHub records unless root `CLAUDE.md` declares otherwise;
conversation follows the human and product text its audience. For an existing non-English record or
human translation, read `reference/repo-claude-md.md`.

Never commit or publish secrets. Report another repository's problem there; changing it needs an
explicit handoff.
