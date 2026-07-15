# Changelog

All notable changes to DevStandard are recorded here. Versions follow the plugin's `plugin.json` / `marketplace.json` (kept in lockstep). Each release tag is applied by the human after merge.

## 0.4.2

A plain-language and disambiguation pass on the injected page and the worker brief — the flow is unchanged; the wording is now jargon-free and harder to misread. Prompted by a fresh-context jargon audit.

- **De-jargoned** core.md / core.zh-CN.md / aids/worker-brief.md: "cockpit" → "the main session"; and gates → "the two checks", rung/ladder → "level", plus fan-out, clean-context, "flown blind", reap/orphan-sweep, "load-bearing", "baked" all replaced with plain words.
- **Fixed wordings that could make an agent act wrongly:** "refuted / passed refutation" (literal sense was the opposite → "survived a challenge"); the architecture path "public merge → human approval" reordered so nothing lands on main before approval; the self-contradictory worktree-removal rule ("never remove one you didn't create" vs. the merger sweeps) resolved — the agent that merges removes that PR's worktree; and a concrete test for which changes need their own branch versus are done in-session.
- **Worktree provisioning:** on birth, copy untracked-but-needed files (`.env`, keys, local config) and parameterize collision-prone resources (ports, DB names) — a fresh worktree carries only git-tracked files (`aids/worktree-lifecycle.md`).
- **Escalation channel stated:** a subagent returns to the main session; a separate session posts an issue comment. Mid-task verbal steering is fine, but decisions count only once written back to the issue/PR.
- Model tiers stay relative (no model names named), per ADR 0008.

## 0.4.1

core.md refinements (the flow is unchanged; the page now says *why* it exists and sharpens who owns what):
- **Lead with the purpose** — the method exists to run several goals in parallel on a large project; that concurrency is the whole point, and a single serial change needs none of the machinery.
- **Sharpen the cockpit's dispatch role** — before sending a task it settles *what result* and *why*, and leaves the *how* (architecture, implementation) to the worker.
- **Clarify the one-writer rule** — it is per-worktree; only concurrent edits to the *same* code are banned, while different worktrees running in parallel is exactly the point.
- **The human never runs git** — all commits, pushes, branches, merges, and tags are the agents' to execute; the human owns the decisions (direction, and go/no-go on architecture and releases), not the keystrokes.

## 0.4.0

The agent-team collaboration redesign — DevStandard's parallel model is now modelled on a human GitHub team, running on durable GitHub-native artifacts (ADRs 0011–0015).

- **Issue → PR dispatch flow.** Work that earns a branch is filed as a GitHub issue carrying its done-check (replacing the ephemeral first prompt); the executor is the cheapest execution-ladder rung that holds the work; the worker returns a PR linked to the issue and never writes main. Trivial in-repo changes stay in-session (ADR 0015).
- **Dual merge gates.** Every merge is guarded by two ordered gates: a fresh clean-context review of the branch diff (a per-merge subagent that never wrote the code and carries no session history — Critical/Important findings block), then green CI on the merge result against current main. Neither substitutes for the other; the reviewed diff is the merged diff (ADR 0011).
- **Worktree lifecycle.** A worktree dies with its task: triggered only by a merge or an explicit human abandon, inventory-checked for uncommitted/unpushed work first, torn down in a fixed order, provenance-guarded, and orphan-swept by whoever merges at main (ADR 0012).
- **Human-declared lifecycle scope.** Ceremony now follows what the human declares instead of repo creation alone — full lifecycle by default (silence defaults to full), a light start when the human declares the work small, a mini-lifecycle for a big in-repo initiative. The trigger phrase becomes "start a new project" (ADR 0014, supersedes 0004).
- **ADR log survives parallel agents.** Dated, append-only amendments are now legal, and final ADR numbers are assigned at merge (branches draft as `DRAFT-`) so parallel branches stop colliding on numbers (ADR 0013).
- core.md's every-session budget is relaxed (hard ceiling ~3,000 tokens, kept lean) to carry the roles, contract, and boundaries inline for workers.

## 0.3.0

Went public; renamed the project to DevStandard (ADR 0010).
