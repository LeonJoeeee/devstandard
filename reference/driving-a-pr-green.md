# Driving a PR to green

core.md: opening a PR is not done — its opener owns it until every check on it reports green and every review-bot finding is fixed or answered on the PR. Here is what that costs in practice.

**What counts, and what green means.** Every check the PR reports, and every finding a review bot posts on it — static analysis, security scanners, style bots. A check that has not reported is not green: queued is not green, in-progress is not green, and a PR whose checks have not started is not a finished PR. A finding with no fix and no reply is unhandled — the reply on the PR is what lets GitHub alone show it was considered.

**A required reviewer or CODEOWNERS approval is not check 1 and does not satisfy it; it blocks merge like an unreported check.** Name it on the PR; an unresponsive approver routes through "When a check can never go green" — escalate to the human who owns that relationship, never wait silently.

**Bot findings run on the check-1 discipline** — verify first, fix what is right without commentary, refute what is wrong with the evidence (`reference/worker.md`). One difference, and only one: the answer goes on the PR, because no re-review settles a bot. A reasoned dismissal on the PR is a legitimate resolution; silence is not, and neither is obeying a finding you know to be wrong.

**A red check is not an opinion — it is the gate, and there are three states, not two:** your diff caused it, your change deliberately staled the check's assumption, or neither. Which one decides everything that follows, including who owns the fix — `reference/red-check.md`.

**A declared check-2 fallback is not a breach of this rule.** While one is in force there are no checks to drive green, and a required check parked at "Expected — waiting for status to be reported" is that state, not a never-green check to escalate. The fallback's own order governs that merge (`reference/ci-cannot-run.md`); this section resumes at the return.

**Taking delivery transfers this duty; it does not end it.** An unreported check returned with a PR
becomes the orchestrator's to drive, and a PR a bot opened is its to own from the moment it appears.
What the orchestrator does with a delivered PR — the tree inventory, the checks and bot findings,
then dispatching a named gap into the same lane rather than repairing it by hand — is its acceptance
procedure (`reference/orchestrator.md`). A PR the orchestrator opened itself never transferred.

**A rebase that re-decides the diff is not driving green — it is a redesign.** The longer a PR sits on any wait above, the further `main` drifts; past some point "fixing conflicts" means re-deciding the change against code no reviewer has seen. That is the "design must change a lot" stop-trigger (`reference/worker.md`) for whoever holds the PR — a worker, or the main session on a PR that never transferred — and it is escalated, never pushed through as a rewritten diff nobody reviewed.

**Handing back is not finishing.** A check you watched fail is not "unreported" — it is unfinished work, and naming it in a handback does not finish it. What may be handed back is a run that has not reported yet, when the doer genuinely has to return before it does: the PR link, and the unreported checks named. Wait for the run if you can; the handback is the exception, not the exit. Where a worker spawned a worker, that handback rides up the chain like a stop message, and passing it on is each intermediate's job — a summary that quietly drops it leaves the check owned by nobody.

**When a check can never go green.** Someone else's required check that is broken, a job needing a secret this repo does not have, a bot demanding something the human already ruled out. Name it rather than absorb it: post on the PR what you observed and what you tried, hand it to the main session, and the main session takes it to the human. The PR then sits in a stated, visible blocked state — waiting is legitimate only once it is written on the PR. What ends it is a change landed through the ordinary ceremony: a visible, tracked quarantine of a flaky test (`reference/worker.md`), a pipeline fix in its own PR, or the human deliberately editing the required-check list. Never a waiver improvised in chat to get this one PR through — a human's "looks fine" is not a green check, and the one place a human waiver has a defined meaning is the never-*reporting* required check under the check-2 fallback (`reference/ci-cannot-run.md`). And never an agent disabling, deleting or making a check permissive: that does more damage than the merge it was buying. (A check that fails then passes with no code change has not gone green either — that is a flake, not a resolution: `reference/red-check.md`.)
