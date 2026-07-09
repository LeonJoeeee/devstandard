# 0009 — Position DevBook as the GitHub flow extended to agent teams; the outer layer stays

Status: Accepted (2026-07-01). Amended by 0015 (2026-07-09).

## Context

Two things converged. First, DevBook is going public — it needs a reason a stranger should care, not "one developer's habits." Second, a real challenge to its design: Claude Code now allows subagents to spawn their own subagents (recursive delegation), so a main agent can act as a deep orchestrator. Does that make DevBook's outer layer — one task = one branch/worktree/session, merging owned by main, CI gate, architecture changes reviewed — obsolete?

## Decision

**Positioning.** One person could never build a large project alone; that is why software teams exist, and the coordination system humanity converged on for them is the GitHub flow — branches, PRs, CI, reviews, an append-only record of why. Working with AI agents recreates *the same collaboration problem in the same shape*: one human directing several agents, or several humans each bringing their own agents. DevBook's bet: **do not invent a new coordination system for agents — reuse the one that already won.** Not GitHub for GitHub's sake: for medium-to-large projects this is simply the highest-efficiency arrangement available, it is the only substrate humans can *see* (agents' work becomes branches and PRs a teammate can review), and it composes with the open internet — strangers can join a project bringing their own agent teams, through the exact flow they already know.

**The recursion question.** Recursive delegation raises single-session *capacity* — and capacity was never the binding constraint (the same verdict as the single-workflow-run analysis, `_source/workflow-deep-dive-report.md`). The outer layer exists for four things recursion cannot touch:

1. **Durable memory** — an orchestrator is mortal (context fills, sessions crash, quota windows close, laptops sleep); a recursive agent tree lives in memory and evaporates with its root. Branches, commits, and docs live on disk and survive into tomorrow, another machine, another person or agent.
2. **Gates** — inside an agent tree every change lands as one blob in one working tree with no CI/review checkpoint; the outer layer forces integration through reviewable units.
3. **Human visibility** — teammates cannot see an agent tree; they can see PRs. Git is the only shared language between humans and agents; drop it and humans are excluded from the collaboration.
4. **Quota windows** — multi-day work must chain through on-disk state regardless of agent topology.

So recursion changes the **inner** layer only: a task session can digest a larger task before the outer flow takes over (the execution ladder's rung 2 gets richer — noted in core.md). The outer layer is untouched, and under the multi-human-multi-agent positioning it matters *more*, because it is the half of the system humans participate in. DevBook stands on git, not on any agent topology — which is also why Claude Code updates do not shake it.

## Consequences

The README leads with this argument; the repo (including `docs/` and `_source/` — the evidence that DevBook built itself with its own rules) goes public under MIT. The cost: as a public standard the wording must stay plain and the personal specifics (models, quotas) must stay out — already the case (personal policy lives in the owner's own config, ADR 0008).

**Amendment (2026-07-09, see 0015):** The outer layer stands, but "one task = one branch/worktree/session" (Context, above) is refined — one-branch/one-worktree is the invariant; "= one session" is retired to the execution ladder's top rung (the executor is chosen per task: a subagent, a workflow, or a separate session). The GitHub-flow bet and the four durable-memory / gates / visibility / quota arguments are unchanged.
