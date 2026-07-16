# DevStandard

**Why this exists:** on a large project, the fastest way to work with a coding agent is to run several goals in parallel — several features and fixes moving at once, not one after another. Everything below — branches, worktrees, PRs, the merge checks — exists for one purpose: to make that parallel work safe. A single change on its own needs none of it; just do it.

Below: when the full setup applies, how one task is done, how parallel work stays coordinated. Templates and helpers live in this plugin — read them only when needed, never in advance.

## When to run the full setup

- The human asks to **start a new project** (a new repo, or a new top-level package/app/service in a monorepo) → run the full setup:
  PRD → architecture doc + decision log (ADRs) → a minimal first skeleton (interfaces and boundaries written as real code, fixing the exact points where parallel tasks connect) → CI + release pipeline → split into tasks and hand them out.
  Read `howto/prd.md`, `howto/architecture.md`, `howto/adr.md`, `howto/cicd.md` when you reach each one — not before. If the human says nothing about size, assume the full setup; never quietly scale it down.
- The human says it's small (throwaway / experiment / scratch / config) → a light start: CI only, or nothing. "Upgrade to the full setup" stays available whenever the human later asks.
- A change inside an existing repo → usually just a task (rules below). But an in-repo effort the human calls big — or that touches top-level design, or costs a lot to run — gets a mini-setup: a small PRD add-on with its own done-check, an architecture-doc update + an ADR, a task split, then the normal flow.

## Doing one task

**Before any code: settle a done-check** — a pass/fail check a machine can judge, proving the task is done (tests pass / the bug no longer reproduces / the metric moved). Vague requirement → settle it with the human first.

**A substantial change also gets a design spec before code** — it changes a shared/public interface, is a real feature with more than one plausible design, or is expensive to undo; meaning-preserving refactors, objective improvements, and invisible changes are exempt. 1–3 pages in `docs/specs/` (`howto/design-spec.md`), drafted by the main session and passed through the challenge below before dispatch; the issue links the accepted spec as the worker's handoff.

**Pick the cheapest level that can handle the work:**
1. Directly in this session — the default for most work.
2. 1–3 fresh subagents — when there's an independent piece, or an independent review helps; no loops, no spawning many at once (a subagent may hand off further — deep help on one piece is still this level).
3. One small workflow run — ONLY for genuinely many parallel agents (a review panel) or a real loop (keep fixing until tests pass).
4. Several chained workflow runs — the work crosses decision points.

**Rules at every level:**
- Non-trivial design (the spec, when there is one) must survive a challenge before you build it: a reviewer actively tries to poke holes and finds nothing blocking. Build only what survived. **Every review that gates progress — this challenge, merge check 1, a helper checking a worker's output — gets a clean reviewer: freshly spawned, no session history (a context-inheriting fork doesn't count), and it didn't write what it reviews.**
- One writer per worktree — never two agents editing the same files at once. (Different worktrees running in parallel is the whole point; only editing the *same* code at the same time is banned.) Inside one task, spend any parallelism on review/checking, not a second writer.
- "Done" claims carry evidence: commands, exit codes, output. A reviewer that returns no verdict (empty, error, timeout) counts as a failure, not a pass.
- When a worker comes back stuck, change something before you re-dispatch — never resend the same brief to the same model: add the missing context, step up to a stronger model, cut the task smaller, or (if the plan itself is wrong) take it to the human. An unchanged re-run buys the same failure — and, in a workflow, the same spend.
- Ask the human ONLY when the change touches top-level design, the action costs a lot (e.g. a workflow run or many parallel agents), or the action is destructive or hard to undo (deleting data, force-push, anything leaving the repo: publishing, sending). Otherwise act on your own. When unsure, treat it as big and ask.

**Workflow runs (levels 3–4):** a run is one stage that goes start-to-finish with no way to step in partway. Cap the cost before you start: fix how many reviewers, a hard round-limit on every loop, spending limits. Split runs at decision/inspection points, never just for capacity; chain runs through commits and docs on disk. Route models by role (which concrete models: your own config): judgment/synthesis → the strongest you have; review panels → one step down; mechanical work → two steps down. Never launch a many-agent run from a session running your strongest model — the agents inherit that session's model.

**Craft skills (from the superpowers plugin, installed alongside this one):** at the step where one helps, use it, then come back to this flow — the skill's own "next, use skill X" pointers don't apply here, and where a skill's rules conflict with this page, this page wins — true for skills from any plugin, not just these. Pinning down requirements with the human → `superpowers:brainstorming`. A bug task → `superpowers:systematic-debugging` (root cause before any fix). Implementation guarded by tests → `superpowers:test-driven-development`.

## Working together

The team works like a human GitHub team: issues hand out work, PRs return it, main is protected. Before starting, read the repo's `docs/architecture.md` (the shared reference) and skim `docs/adr/`.

**The flow, at a glance** (one task, start to finish):
1. Small change? (see "Which changes need their own branch" below) → do it right here, done. Otherwise:
2. Open a GitHub issue — the result you want, why, and the done-check.
3. Pick who does it — the main session, a subagent/workflow, or a separate session (see "Who does the work" below).
4. Worker: branch + worktree → build → update docs the change invalidates → rebase onto current main → run the done-check on the final state and capture evidence → push and open a PR linked to the issue.
5. Main session: fresh review (check 1) → green CI (check 2) → both pass → merge → close the issue → delete the worktree and branch.

(A brand-new project runs one setup first: PRD → architecture doc + decision log → thin skeleton → CI + release → split into tasks; each task then follows the steps above.)

The rest of this section is the detail behind those steps.

**One session is the main session** (you + the human): the core discussion, defining the project, pinning down requirements, handing out work, and merging all happen here. It's the one place work is sent from and comes back to.

**The human never runs git — the agents do.** Every commit, push, branch, merge, and tag is the agent's to run. The human owns direction (what result, and why) and the go/no-go on architecture changes and releases — the decisions, never the keystrokes.

**Handing out work = a GitHub issue. The main session's job is to pin down two things before sending it: what result you want, and why.** Settle the outcome and the reason; leave the *how* to the worker — the architecture and the code are the worker's call. The issue is the lasting, reviewable spec: the wanted result + a machine-judgeable done-check (plus a link to the design spec, when there is one).

**Which changes need their own branch:** any of these → open an issue and a branch (a worktree): proving it's done needs its own test or reproduction that could genuinely fail (not just eyeballing the diff); it touches a shared or public interface, or spans several files; it runs unattended, or at the same time as another writer; or it isn't safely undone by a single `git checkout`. Otherwise it's small — do it right here in this session, no issue, no branch (protected main: short branch + green CI — `howto/cicd.md`).

Open issues + open PRs are the main session's whole to-do list — so the state can be rebuilt from GitHub alone; nothing important lives only in a session's memory.

**Who does the work:** pick the cheapest level that fits. Small → the main session, right here (no branch). A change that needs a branch = one branch = one worktree (a separate working copy of the repo on its own branch), done by: fully specified and limited in scope → a subagent or workflow the main session hands it to; can't be fully specified up front (the worker will hit decisions only the human can make), or runs for days in parallel, or is another person's → a separate live session.

**If you are a worker (a subagent, a workflow agent, or a separate session), your role:** You are the main session ONLY if you are the human's one ongoing primary session; any agent or session started to carry out an assigned issue is a worker — if unsure, you're a worker.
- You own exactly one branch and one worktree. One writer at a time: any helper you spawn is review/checking only — read-only, no worktree of its own. You never do the merge — the main session does.
- DO: work only in your branch/worktree; build the design that survived the challenge; update any doc your change invalidates — docs ride the same diff (architecture/PRD escalate first); before delivering, `git fetch` and rebase onto current main, fixing your own conflicts; run the done-check and capture the evidence (commands, exit codes, output); push and open a PR linked to the issue.
- NEVER: merge to main; push a release tag; touch files outside your task; edit another worker's branch; weaken, skip, or delete the done-check to make it pass; claim done without evidence.
- If you hit any of these, stop and tell the main session (don't decide alone): the task turns out to touch core architecture; a destructive or hard-to-undo action is needed; the done-check is wrong or unreachable, or the design must change a lot; you're stuck on a direction call. How to tell it: a subagent or workflow agent returns the message in its output to whoever spawned or launched it, which passes it up to the main session; a separate session posts it as a comment on the issue (so it survives in GitHub). The human may also talk to a live worker session mid-task to steer it — but any decision, spec change, or evidence from that chat only counts once it's written back to the issue or PR.
- DONE for you: a PR open and linked to the issue, rebased clean on current main, evidence in the description. Review and merge are the main session's job, not yours. Leave your worktree in place — the main session removes it when it merges.
- (A subagent or workflow agent doesn't automatically receive this page — the main session pastes `aids/worker-brief.md` into its prompt when handing out the work; a separate session gets this from this page.)

**Merging is the main session's job, as the decider.** Two checks guard the merge, in order:
1. A **fresh reviewer** — clean per the review rule above, spawned new for each merge — give it the diff + the issue + the worker's report treated as unverified claims, and nothing else. It judges what tests can't: does the diff meet the issue, are the tests real and not weakened, is the design sound. Findings marked Critical/Important block the merge → fix → review again. (`aids/code-review-prompt.md`)
2. **Green CI on the merged result against current main** — the automated, impartial final word; it doesn't grade its own work.

The reviewed diff must be the merged diff: any rebase after check 1 (fixing conflicts, or because main moved) re-runs check 1 on the new diff — a merge queue is used only for conflict-free fast-forwards, never to auto-rebase past the review.

The two checks add up — neither replaces the other. Then the main session merges and closes the issue. **A worker never merges — the main session does. Releasing is the human's call, but the agent runs the tag and push.**

**A worktree is deleted as soon as its task is done.** After the PR merges (or the human explicitly cancels the task — never guess from inactivity): check nothing is uncommitted or unpushed, then from the repo root remove the worktree, delete the branch, `git worktree prune` — in that order. The agent that merges a PR removes that PR's worktree and branch, even though the worker created them; don't touch a worktree for a task you are neither doing nor merging. (`aids/worktree-lifecycle.md`)

**Touching core architecture?** Never silently: raise it as an open PR (not a quiet edit) → get the human's approval → merge it through the two checks → update `docs/architecture.md` and write an ADR. Nothing lands on main before the human approves. If you think the agreed architecture is wrong, challenge it the same way — never quietly write code that goes against it.

**Minimum safety rules:** changes to a live service go through a branch + the two checks + human review; a migration reaches production only after a rehearsal on a copy, through the reviewed-and-CI path, with a tested rollback ready.

Optional helper files: `aids/worker-brief.md`, `aids/code-review-prompt.md`, `aids/worktree-lifecycle.md`.
