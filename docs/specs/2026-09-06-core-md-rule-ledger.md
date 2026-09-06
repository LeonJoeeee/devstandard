# Core rule ledger

Status: implementation prepared; human drops approved 2026-09-06; architecture sign-off pending.

Issue: #205. Source base: `3f7e9009511d0237a46eefc4ad9d30c90a727da9` (`origin/main`).
This is an audit artifact, not an operative method page. Source clauses were extracted and dispositioned before the rewrite and are preserved verbatim below,
one numbered paragraph/list item per entry, including conjunctive duties and exceptions. The landing
column dispositions the entire entry; mixed entries explicitly name both surviving duties and drops.
Headings without rules are recorded as structural entries. PRD §1.1–§1.6 and §2 supply the reason:
coordination/isolated lanes (1,2), evidence/gates (2,4), irreversibles (3), conventions (5), bounded
context (6), and reuse of GitHub, worktrees and craft (2). The approved architecture is the design.

## Drop list — separate human decision before merge

- **D1 — automatic full/light/mini setup fork.** Replace project-size ceremony with issue bounds and task-triggered documents (approved architecture chapter 6, PRD §1.6). Keep founding mechanics, safety checks and templates where their task needs them. This does not authorize unreviewed ordinary changes.
- **D2 — execution ladder and unsupported executor topologies.** Remove direct execution as the default and main-session repository spec writing, the old multi-condition worker test, 1–3 fan-out limit, workflow runs/chains/panels, recursive implementation helpers, and separate live-session worker delivery. Use one Claude orchestrator, N isolated workers, Claude-native or Codex-process executors; the orchestrator only edits one or two lines or researches (PRD §1.1, architecture chapters 1–3). Clean reviews, explicit routing and same-lane continuation survive.
- **D3 — ordinary dispatch cost as another human approval event.** Drop approved; the human also overruled the proposed replacement of cost limits in issue bounds on 2026-09-06 (approval record below). Cost is inherent to the work and larger tasks legitimately cost more. The operative rule lands in `reference/orchestrator.md`, Acceptance and integration, beside the review cap; routine fan-out and continuation are orchestrator decisions. Human direction remains authoritative; irreversibles, architecture-level merge and major release retain explicit authorization/sign-off (PRD §4 Workflow 2).
- **D4 — review before green CI.** Deliver a green PR before acceptance; require both gates on the merged result. Existing review-packet admission already enforces that order (PRD §1.2; architecture chapter 4).
- **D5 — blanket reviewer/issue ceremony for bare version bumps.** Apply the human's #226 ruling: bump rides the change PR; an unavoidable PR changing only the two manifest version lines needs neither issue nor check 1, while CI and guarded merge remain. That exception landed in #234 and is included through the rebase.

**Human drop approval: APPROVED — D1–D5, 2026-09-06.** The main session recorded the human's
decision, including the D3 overruling, at
https://github.com/LeonJoeeee/devstandard/pull/235#issuecomment-5559320446.
Architecture-level sign-off remains separately pending the human's line after check 1 round 2.

## Hook-cap measurement

**Measured 2026-09-06, Claude Code 2.1.263 (Linux).** A temporary SessionStart command emitted
valid JSON containing an ASCII payload with a unique marker only at its tail. Independent fresh
Claude print sessions (`--model opus --effort low --tools "" --strict-mcp-config`, no user/project
settings, no session persistence, a one-dollar ceiling per probe) were asked for that marker.
The **10,000-byte additionalContext** payload was returned intact. At **10,001 bytes**, Claude
persisted the context to a `tool-results/hook-…-additionalContext.txt` file and returned its path
instead of the marker; 12,000 bytes also persisted. The source marker did not appear in the user
prompt. Tools were unavailable, so an instructed read could not masquerade as inline reception.
The boundary is measured for ASCII; the implementation conservatively bounds UTF-8 bytes for
all text rather than inferring a Unicode character allowance. JSON escaping and systemMessage
are not counted as additionalContext. The earlier binary sanitizer search was not used as cap
evidence: it describes a different path.

**Draft qualification:** two real hook outputs, one per static artifact, were supplied as two
SessionStart commands in the same fresh no-tool session. Each had a unique marker appended after
the complete artifact. The response was exactly `CORE_END_d91e36` followed by `ROLE_END_ee625a`;
process exit 0. The source hashes were:

- core: `252177dbec0f85ac7b716ad310453150025a0293cd96acf37dc4f575cea289d5`
- orchestrator: `cb8f84e409c33494459535a6615ff465ecc0f441a927488c35c7ca851f5ee1d4`

Both artifact tails reached the model inline despite their combined size exceeding one output's
cap. That selects separate hook outputs, not an aggregate carrier followed by an unnecessary
read. Startup/clear/compact hook registration is checked locally; the live qualification exercised
startup, not a forced live compaction. The measurement is version/date-specific, not a promise
about every future harness release. Source hashes bind the measured drafts without publishing
stale page totals. Final exact payload sizes belong only in the PR's quoted gate output.

**Budget derivation:** reserve one tenth of the measured cap for wrapper/path overhead: core's
byte ceiling is 9,000. Scale the measured core draft's word-proxy density to that byte ceiling,
then round upward to the next hundred: `ceil((floor(words × 1.35) / UTF8_bytes × 9000) / 100) × 100`
gives a **1,800 proxy-token ceiling**. The byte gate independently controls delivery; the proxy
is the repository's historical readability approximation, not a tokenizer or harness limit.
The complete emitted context is also checked against `INLINE_CAP_BYTES` read from the hook.
CI and the release validation invoke `.github/check-core-budget.py`; `CLAUDE.md` carries the
same command. Larger artifacts receive the measured overflow branch's before-acting IN FULL
instruction. The worker reference is expanded directly in dispatch prompts (outside the hook
channel); the native worker definition consumes that full brief or reads the role if given only
a task packet. Reviewer contract delivery and location are unchanged.

**Reproducible local boundary test:** `.github/test-session-start.py` invokes the real hook from
a temporary installation, constructs a payload that fills the complete context exactly to the
measured boundary, adds one byte, and checks inline versus forced read. It also covers UTF-8,
escaping, missing role files, unsupported environments, inherited environment and lifecycle
source metadata. These tests failed against the original forced-read hook before implementation.
This test is a regression check on our carrier, not a substitute for the native measurement.


## Source ledger

### C001 — `core.md`

Disposition: core.md workflow; founding exception: reference/prd.md (D1 removes its automatic setup trigger).

> **Why this exists:** on a large project, several features and fixes move at once rather than one after another. Worktrees, dispatch, and issues exist to make that parallel work safe; the branch + PR + two merge checks ride *every* change regardless, from the first task onward — even a lone fix reaches main only through a reviewed PR, so no diff ever lands unseen. (The one exception — a project's own founding setup — is named below.)

### C002 — `core.md`

Disposition: core.md trigger table.

> Templates and helpers live in this plugin — read them only when needed, never in advance.

### C003 — `core.md`

Disposition: D1; retain founding mechanics and document templates in reference/prd.md, reference/architecture.md, reference/adr.md and reference/ci-pipelines.md under task-scoped triggers.

> - The human asks to **start a new project** (a new repo, or a new top-level package/app/service in a monorepo) → run the full setup:
>   PRD → architecture doc + decision log (ADRs) → a minimal first skeleton (interfaces and boundaries written as real code, fixing the exact points where parallel tasks connect) → CI + release pipeline → split into tasks and hand them out.
>   Read `reference/prd.md`, `reference/architecture.md`, `reference/adr.md`, `reference/ci-pipelines.md` when you reach each one — not before. If the human says nothing about size, assume the full setup; never quietly scale it down. Setup itself is the one exception to the ceremony below: the founding PRD/architecture/skeleton commits land directly on main (branch protection arrives with CI, setup's last step), and the architecture doc settled with the human is the skeleton's design spec — nothing further is owed before code there.

### C004 — `core.md`

Disposition: D1; task weight and zero demo ceremony: reference/orchestrator.md.

> - The human says it's small (throwaway / experiment / scratch / config) → a light start: CI only, or nothing. "Upgrade to the full setup" stays available whenever the human later asks.

### C005 — `core.md`

Disposition: D1; task-scoped design triggers: reference/orchestrator.md and reference/design-spec.md.

> - A change inside an existing repo → usually just a task (rules below). But an in-repo effort the human calls big — or that touches top-level design, or costs a lot to run — gets a mini-setup: a small PRD add-on with its own done-check, an architecture-doc update + an ADR, a task split, then the normal flow.

### C006 — `core.md`

Disposition: core.md workflow; reference/orchestrator.md issue preparation; reference/worker.md receipt.

> **Before any code: settle a done-check** — a pass/fail check a machine can judge, proving the task is done (tests pass / the bug no longer reproduces / the metric moved). Vague requirement → settle it with the human first.

### C007 — `core.md`

Disposition: reference/design-spec.md; reference/orchestrator.md design trigger; D2 dispatches repository drafting while the orchestrator retains the challenge.

> **A substantial change also gets a design spec before code** — it changes a shared/public interface, is a real feature with more than one plausible design, or is expensive to undo; meaning-preserving refactors, objective improvements, and invisible changes are exempt. 1–3 pages in `docs/specs/` unless the architecture doc points elsewhere (`reference/design-spec.md`), drafted by the main session and passed through the challenge below before dispatch; the issue links the accepted spec as the worker's handoff.

### C008 — `core.md`

Disposition: D2 (heading only; routing survives in reference/external-agent.md).

> **Pick the cheapest level that can handle the work:**

### C009 — `core.md`

Disposition: D2; core.md orchestrator contract.

> 1. Directly in this session — the default for most work.

### C010 — `core.md`

Disposition: D2 removes numeric fan-out and recursive worker execution; clean reviews and executor selection land in reference/external-agent.md; one writer in reference/worker.md.

> 2. 1–3 fresh subagents — when there's an independent piece, or an independent review helps; no loops, no spawning many at once (a subagent may hand off further — deep help on one piece is still this level). A fresh executor may be an agent invoked as a process — such as `codex exec` invoked by Claude Code — and where Codex is installed it is the one to use, a subagent only where the work especially suits one; same rung, same rules, plus what a process needs that your harness would have handled (`reference/external-agent.md`: when a subagent, when Codex).

### C011 — `core.md`

Disposition: D2.

> 3. One small workflow run — ONLY for genuinely many parallel agents (a review panel) or a real loop (keep fixing until tests pass).

### C012 — `core.md`

Disposition: D2.

> 4. Several chained workflow runs — the work crosses decision points.

### C013 — `core.md`

Disposition: core.md role interlock (heading only).

> **Rules at every level:**

### C014 — `core.md`

Disposition: reference/design-spec.md challenge; reference/code-review-prompt.md review contract; reference/external-agent.md clean executor.

> - Non-trivial design (the spec, when there is one) must survive a challenge before you build it: a reviewer actively tries to poke holes and finds nothing blocking. Build only what survived. **Every review that gates progress — this challenge, merge check 1, a helper checking a worker's output — gets a clean reviewer: freshly spawned, no session history (a context-inheriting fork doesn't count), and it didn't write what it reviews.**

### C015 — `core.md`

Disposition: core.md interlock; reference/worker.md boundaries.

> - One writer per worktree — never two agents editing the same files at once. (Different worktrees running in parallel is the whole point; only editing the *same* code at the same time is banned.) Inside one task, spend any parallelism on review/checking, not a second writer.

### C016 — `core.md`

Disposition: core.md evidence contract; reference/external-agent.md failed review attempts.

> - "Done" claims carry evidence: commands, exit codes, output. A reviewer that returns no verdict (empty, error, timeout) counts as a failure, not a pass.

### C017 — `core.md`

Disposition: reference/external-agent.md explicit routing; agents/worker.md and agents/reviewer.md fix opus; D2 removes workflow routing.

> - Route every agent you spawn by role, and never above `opus` — whatever this session runs. `opus` is both the cap and the default, every review that gates progress included; drop to `sonnet` or `haiku` only for genuinely mechanical work (file sweeps, test runs, checklist edits). Tier aliases, never version ids. Set the model on every spawn that takes one; an agent you don't route inherits the session's model, which may sit above the cap — a spawn with no model knob at all is the cap's one exception.

### C018 — `core.md`

Disposition: reference/orchestrator.md continuation; reference/external-agent.md explicit setting and round procedure.

> - When a worker comes back stuck, change something before you re-dispatch — never resend the same brief to the same model: add the missing context, step up a tier (`opus` at most), cut the task smaller, or (if the plan itself is wrong) take it to the human. An unchanged re-run buys the same failure — and, in a workflow, the same spend.

### C019 — `core.md`

Disposition: core.md human touchpoints; reference/hard-edges.md authorization; reference/worker.md own-branch lease exception; D3 removes ordinary fan-out as an approval event.

> - Ask the human ONLY when the change touches top-level design, the action costs a lot (e.g. a workflow run or many parallel agents), or the action is destructive or hard to undo (deleting data, force-pushing a branch others depend on — main, a shared branch, one a review is in flight against — anything leaving the repo: publishing, sending, or a write the placement rule below sends to an ask). `--force-with-lease` on your own unmerged branch, with no review in flight, is ordinary work — amending after check 1 passed still re-runs check 1. Otherwise act on your own. When unsure, treat it as big and ask.

### C020 — `core.md`

Disposition: D2 removes workflow staging; D3 drops run-spending limits and its proposed issue-bounds replacement under the recorded human overruling. The cost rule lands in reference/orchestrator.md, Acceptance and integration; fixed review-cap mechanics remain in reference/hard-edges.md.

> **Workflow runs (levels 3–4):** a run is one stage that goes start-to-finish with no way to step in partway. Cap the cost before you start: fix how many reviewers, a hard round-limit on every loop, spending limits. Split runs at decision/inspection points, never just for capacity; chain runs through commits and docs on disk. Route every agent in the run (the routing rule above) — a wide fan-out left unrouted is the fastest way to burn a quota.

### C021 — `core.md`

Disposition: reference/orchestrator.md requirements binding; reference/worker.md execution binding; core.md role-specific skill pointer.

> **Craft skills (from the superpowers plugin, installed alongside this one):** at the step where one helps, use it, then come back to this flow — the skill's own "next, use skill X" pointers don't apply here, and where a skill's rules conflict with this page, this page wins — true for skills from any plugin, not just these. Pinning down requirements with the human → `superpowers:brainstorming`. A bug task → `superpowers:systematic-debugging` (root cause before any fix). Implementation guarded by tests → `superpowers:test-driven-development`.

### C022 — `core.md`

Disposition: reference/orchestrator.md receipt; reference/worker.md receipt.

> Before starting, read the repo's canonical `docs/architecture.md` (the shared reference) and skim `docs/adr/` unless that architecture doc points elsewhere, when the project has them.

### C023 — `core.md`

Disposition: core.md workflow (heading only).

> **The flow, at a glance** (one task, start to finish):

### C024 — `core.md`

Disposition: core.md workflow; reference/orchestrator.md issue preparation.

> 1. **Issue first** — dispatched work, and any task the human raises, gets a GitHub issue (the result you want, why, and the done-check) opened *before* the work; clarifying with the human may come first, skipping the issue may not. A small fix the main session notices itself may skip the issue — the PR is its record — but never the ceremony below.

### C025 — `core.md`

Disposition: core.md interlock; reference/external-agent.md executor routing; D2 removes separate-session/workflow choices.

> 2. Pick who does it — the main session, a subagent/workflow, or a separate session (see "Who does the work" below).

### C026 — `core.md`

Disposition: reference/worker.md delivery; reference/orchestrator.md direct-edit duty.

> 3. The doer works on a branch (a dispatched worker also gets its own worktree): build → update the docs the change invalidates (they ride the same diff) → `git fetch` and rebase onto current main, fixing its own conflicts → run the done-check on the final state and capture evidence → push, open a PR (linked to the issue, when there is one), and drive it green.

### C027 — `core.md`

Disposition: core.md two checks; D4 replaces review-before-green ordering.

> 4. Main session: fresh review (check 1) → green CI (check 2) → both pass → merge → close the issue (if any) → remove the branch (and its worktree, when the work had one).

### C028 — `core.md`

Disposition: core.md orchestrator contract.

> **One session is the main session** (you + the human): the core discussion, defining the project, pinning down requirements, handing out work, and merging all happen here. It's the one place work is sent from and comes back to.

### C029 — `core.md`

Disposition: core.md human contract.

> **The human never runs git — the agents do.** Every commit, push, branch, merge, and tag is the agent's to run. The human owns direction (what result, and why) and the go/no-go on architecture changes and releases — the decisions, never the keystrokes.

### C030 — `core.md`

Disposition: reference/orchestrator.md issue preparation; accepted design remains binding in reference/worker.md.

> **Handing out work = a GitHub issue. The main session's job is to pin down two things before sending it: what result you want, and why.** Settle the outcome and the reason; leave the *how* to the worker — the architecture and the code are the worker's call. The issue is the lasting, reviewable spec: the wanted result + a machine-judgeable done-check (plus a link to the design spec, when there is one). (Timing, and the small-fix exception: step 1 above, "Issue first".)

### C031 — `core.md`

Disposition: D2 replaces the old issue/worker test with the one-or-two-line boundary; issue exception remains in core.md.

> **Which changes earn an issue and a worker:** under universal ceremony every change already rides a branch + PR, so this test decides only the *weight* — does the change need its own issue and a dispatched worker, or is it a main-session short-branch job? Any of these → open an issue and hand it to a worker on its own branch + worktree: proving it's done needs its own test or reproduction that could genuinely fail (not just eyeballing the diff); it touches a shared or public interface, or spans several files; it runs unattended, or at the same time as another writer; or it isn't safely undone by a single `git checkout`. None of these → it's small: the main session does it itself on a short branch — no issue needed unless the human raised it, but the same branch → PR → review → CI as everything else, never a direct commit to main (`reference/ci-pipelines.md`).

### C032 — `core.md`

Disposition: reference/orchestrator.md event loop.

> Open issues + open PRs are the main session's whole to-do list — so the state can be rebuilt from GitHub alone; nothing important lives only in a session's memory.

### C033 — `core.md`

Disposition: core.md write trigger; reference/worker.md scope boundary.

> **Stay in your own repo, and off the human's filesystem.** A session works the repo(s) it was opened for. Discovering a problem in another repo — even the same human's — means filing an issue there, never fixing it yourself: cross-repo edits from a passing session are how repos get polluted. Only an explicit handoff from the human makes another repo yours to change.

### C034 — `core.md`

Disposition: reference/where-it-goes.md complete placement rule; resident ask-kind and durability trigger in core.md and independently delivered reference/worker.md.

> <!-- BEGIN CORE PLACEMENT PARAGRAPH -->
> **Every file you write while working has a place: put it where something that already existed puts
> it** — code or
> config that writes there, a tool's documented default, the repo's docs relaying one of those or the
> human's choice; **what this change added names nothing, and neither does a handoff or session-state
> document.** Nothing names a place: put it inside the project, gitignored unless the repo maintains it,
> and **never one outside it — not `$HOME`, not the Desktop**; what dies with the task goes to session
> scratch. Judge it yourself. **Three never take that default — a secret or confidential data, never
> committed or published whatever else the file also is; application state for a program that outlives
> your task; a release: where nothing names a place for one, ask**, as you do when something must
> outlive the task and nowhere durable will keep it. Name any durable write outside the repo, and any
> kept file left in a worktree, in the PR or at handback (`reference/where-it-goes.md`).
> <!-- END CORE PLACEMENT PARAGRAPH -->

### C035 — `core.md`

Disposition: core.md interlock; reference/external-agent.md routing; D2 removes old ladder and separate live-session lane.

> **Who does the work:** pick the cheapest level that fits. Small → the main session itself, on a short branch (same PR + review + CI, just no separate worktree). A change dispatched to a worker = one branch = one worktree (a separate working copy of the repo on its own branch), done by: fully specified and limited in scope → a subagent or workflow the main session hands it to; can't be fully specified up front (the worker will hit decisions only the human can make), or runs for days in parallel, or is another person's → a separate live session. Dispatched work goes to Codex where it is installed — the rung-2 executor; a separate live session stays the lane above — a harness-native subagent only where the work especially suits one; `reference/external-agent.md` says which is which and carries the standing model and effort.

### C036 — `core.md`

Disposition: reference/clean-handback.md, reference/in-repo-writes.md and reference/repo-claude-md.md; core.md write trigger; reference/worker.md receipt and delivery.

> **The doer's doc/tree duty is universal:** before the first task-generated write, snapshot the tree; add only a document `reference/in-repo-writes.md` admits; update invalidated docs in the same diff; write back only a command, environment gotcha, worktree copy-list entry, or record-language declaration to `CLAUDE.md` (`reference/repo-claude-md.md`); put notes for the next session on the issue or PR; and hand back nothing unintended (`reference/clean-handback.md`). A design decision still escalates through architecture. The reviewer's Docs check is the backstop, not the first line.

### C037 — `core.md`

Disposition: reference/driving-a-pr-green.md and reference/red-check.md; core.md PR ownership trigger.

> **Opening a PR isn't done:** its opener owns it until every check reports green and every review-bot finding is fixed or answered on the PR. A bot finding is an opinion; a red check is the gate, and there are three states, not two: your diff caused it, your diff deliberately staled the check's assumption, or neither — never loosen a check because it's inconvenient (`reference/red-check.md`). A check that only passes after repeated re-runs with no code change is a flake, not green — quarantine it visibly, never retry it quietly. A doer returning before a check reports hands back the PR link and that check, never one it watched go red; the main session inherits at delivery and takes what can never go green to the human. (`reference/driving-a-pr-green.md`)

### C038 — `core.md`

Disposition: core.md record rule; worker delivery carries its own language duty.

> **The record is English; the conversation is the human's language.** Everything you write that lands in the repo or on GitHub — code, comments, docs, commits, issues, PRs, ADRs, specs — is English, whatever language you and the human are speaking, including when you write up what the human said. What the product shows its own users — interface text, user docs — follows that product's audience instead. Everywhere else, speak the human's language. A repo whose record is another language says so in its repo-root `CLAUDE.md`, and that holds for the whole record — never per file, never per agent; a record whose docs and commit history are already in another language has decided, so write that line and follow it, never start a second one. A translation kept for humans is a mirror, not a second source: it names its canonical file at the top and rides the same diff.

### C039 — `core.md`

Disposition: reference/worker.md identity; core.md interlock; scripts/dispatch and agents/worker.md carriers; D2 removes unsupported session/workflow topology.

> **A dispatched worker (a subagent, a workflow agent, or a separate session sent to carry out an assigned issue) is told so by its brief — `reference/worker-brief.md`, pasted into its prompt or linked from its issue; every dispatched worker receives, or opens, that brief before acting.** The brief is the only thing that ever announces the role; a session the human opened and is steering is simply this conversation's main session. What a worker owns and owes:

### C040 — `core.md`

Disposition: core.md interlock; reference/worker.md boundaries.

> - You own exactly one branch and one worktree. One writer at a time: any helper you spawn is review/checking only — read-only, no worktree of its own. You never do the merge — the main session does.

### C041 — `core.md`

Disposition: reference/worker.md NEVER boundaries; core.md interlock.

> - NEVER: merge to main; push a release tag; touch files outside your task; edit another worker's branch; weaken, skip, or delete the done-check to make it pass; claim done without evidence.

### C042 — `core.md`

Disposition: reference/worker.md escalation; core.md worker stop trigger; D2 removes separate-session return channel.

> - If you hit any of these, stop and tell the main session (don't decide alone): the task turns out to touch core architecture; a destructive or hard-to-undo action is needed; the done-check is wrong or unreachable, or the design must change a lot; you're stuck on a direction call. How to tell it: a subagent or workflow agent returns the message in its output to whoever spawned or launched it, which passes it up to the main session; a separate session posts it as a comment on the issue (so it survives in GitHub). The human may also talk to a live worker session mid-task to steer it — but any decision, spec change, or evidence from that chat only counts once it's written back to the issue or PR.

### C043 — `core.md`

Disposition: reference/worker.md delivery; core.md evidence contract.

> - **Everything this page says about the doer is yours in full** — step 3 of the flow above, the doc duty, the evidence rule, PR ownership. You are DONE when your PR is open and linked to the issue, rebased clean on current main, **with your done-check evidence in the PR description**, and its checks reported green or handed back unreported, never red. Review and merge are the main session's job. **Leave your worktree in place — the agent that merges removes it.**

### C044 — `core.md`

Disposition: reference/worker.md static delivery; D2 removes separate-session startup assumption.

> - (A subagent or workflow agent doesn't automatically receive this page — the brief is its whole briefing; a separate session reads this page at startup and still opens the brief for the operational checklist this page does not repeat.)

### C045 — `core.md`

Disposition: core.md two checks; D5 adds settled bare-bump exception.

> **Merging is the main session's job, as the decider.** Both checks guard *every* merge, however small the diff — no size lets a change reach main unreviewed. In order:

### C046 — `core.md`

Disposition: reference/code-review-prompt.md unchanged contract; reference/external-agent.md assembler and publication; core.md two checks.

> 1. A **fresh reviewer** — clean per the review rule above, spawned new for each merge — give it the diff + the issue + the worker's report treated as unverified claims, and nothing else. Where Codex is installed it is a Codex run, read-only (`reference/external-agent.md`); its verdict names which agent gave it. Apply the goal-centered judging contract in `reference/code-review-prompt.md`; that file alone defines what blocks and what becomes a note. The verdict lands as a comment on the PR before the merge — the review history must be reconstructable from GitHub alone.

### C047 — `core.md`

Disposition: core.md two checks; reference/hard-edges.md merge proof.

> 2. **Green CI on the merged result against current main** — the automated, impartial final word; it doesn't grade its own work.

### C048 — `core.md`

Disposition: reference/hard-edges.md; reference/code-review-prompt.md unchanged narrow exceptions; core.md changed-head trigger.

> The reviewed diff must be the merged diff. A changed head re-runs check 1 unless the orchestrator proves a content-unchanged, conflict-free rebase plus green merged-result CI through `reference/hard-edges.md`. Use its guarded merge entry point; never auto-rebase past review. The quoted-Note and artifact-only exceptions remain in `reference/code-review-prompt.md`.

### C049 — `core.md`

Disposition: core.md two checks and human touchpoints; reference/orchestrator.md release.

> The two checks add up — neither replaces the other. Then the main session merges and closes the issue. **A worker never merges — the main session does. Releasing is the human's call, but the agent runs the tag and push.**

### C050 — `core.md`

Disposition: reference/ci-cannot-run.md; core.md unavailable-CI trigger.

> **If CI cannot run at all** — no push produces a run, and only because minutes are exhausted or the provider is down — check 2 degrades: the merging session, never the worker, runs every CI job on the merged result, posts the evidence, the merged SHAs and proof it cannot run on the PR, and hands that comment to check 1 to audit before merging. Not triggers: slow, queued, flaky or red CI, or anything this repo or its org could fix; unsure means it can run. A never-reporting required check blocks the merge — the human unblocks it, never you. No release ships under it. It ends at the first push that runs (`reference/ci-cannot-run.md`).

### C051 — `core.md`

Disposition: reference/orchestrator.md red-main recovery; core.md red-main trigger.

> **If main goes red** — a merge that slipped through, a flaky test, or the platform aging under you — restoring green outranks all new work, and nothing new is dispatched onto a red main. Default recovery: revert the offending commit; fix forward only when the fix is obvious and takes minutes. The revert itself is the one change that merges without a fresh review — the tree it restores was already reviewed when it first merged; green CI still gates it. If no commit is at fault (the pipeline itself aged — `reference/ci-pipelines.md`), there is nothing to revert: fix the pipeline.

### C052 — `core.md`

Disposition: reference/worktree-lifecycle.md; core.md birth/death triggers; reference/external-agent.md fixed dispatcher.

> **Before a repo's first in-repo worktree is created — on any path, dispatch included:** `git check-ignore -q .claude/worktrees/probe`; if it fails, land the `/.claude/worktrees/` ignore line through a short-branch PR first (`reference/worktree-lifecycle.md`, Birth). **A worktree is deleted as soon as its task is done.** After the PR merges (or the human explicitly cancels the task — never guess from inactivity): check nothing is uncommitted or unpushed, then from the repo root remove the worktree, delete the branch, `git worktree prune` — in that order. The agent that merges a PR removes that PR's worktree and branch, even though the worker created them; don't touch a worktree for a task you are neither doing nor merging. While there, also sweep for other finished tasks' leftovers (`git worktree list`, then each one's PR state — `git branch --merged` misses a squash-merge) — a session sometimes ends before its own teardown, so cleanup gets two chances, not one. (`reference/worktree-lifecycle.md`)

### C053 — `core.md`

Disposition: reference/orchestrator.md architecture decision; core.md human sign-off.

> **Touching core architecture?** Never silently: raise it as an open PR (not a quiet edit) → get the human's approval → merge it through the two checks → update `docs/architecture.md` and write an ADR. Nothing lands on main before the human approves. If you think the agreed architecture is wrong, challenge it the same way — never quietly write code that goes against it.

### C054 — `core.md`

Disposition: reference/orchestrator.md live-service and migration safeguards; core.md production-change trigger.

> **Minimum safety rules:** changes to a live service go through a branch + the two checks + human review; a migration reaches production only after a rehearsal on a copy, through the reviewed-and-CI path, with a tested rollback ready.

### W001 — `reference/worker-brief.md`

Disposition: reference/worker.md receipt and delivery; D2 removes workflow/separate-session topology.

> **Two ways to arrive here, and they fill the fields below differently.** The main session **pastes** this file, filled in, when it hands a task to a **subagent or a workflow agent** — neither receives `core.md` when it starts, so they must be briefed here (paste it to a separate session too, if you are not sure its startup read of `core.md` fired). A **separate live session** may instead open this file itself: nobody fills it in for you, and **your fields are in your issue**.

### W002 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> **Codex executors:** the dispatch brief supplies the role; no DevStandard plugin hook delivers
> `core.md`. Read the named craft skill's `SKILL.md` when its trigger fires, then return to this
> brief. Use one dedicated `mktemp -d` directory for task scratch; publish durable results on the
> issue or PR and remove scratch best-effort at completion. `CLAUDE.md` stays the repo's
> operational-memory file on every harness; the before-write rule below requires its explicit read.

### W003 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> **This brief is what makes you a worker**: it was pasted into your prompt, or your assigning issue linked it. You work one task; you own exactly one branch and one worktree; you never do the merge — that's the main session's job (the session that dispatched this work).

### W004 — `reference/worker-brief.md`

Disposition: reference/worker.md task packet.

> - Issue: {ISSUE_LINK_OR_SPEC}

### W005 — `reference/worker-brief.md`

Disposition: reference/worker.md task packet.

> - Done-check (a machine-judgeable pass/fail check, from the issue): {DONE_CHECK}

### W006 — `reference/worker-brief.md`

Disposition: reference/worker.md named-base receipt.

> - Branch: {BRANCH}   Worktree: {WORKTREE_PATH}   Base: current `main`

### W007 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> **Pasted to you, and a {field} is still a placeholder — or filled but too vague to act on cold** (e.g. "fix the race condition" with no repro, error text, failing-test name, or target file)? **Don't start; ask the main session to make it specific.** You have none of its context, and it is the one that can answer.

### W008 — `reference/worker-brief.md`

Disposition: reference/worker.md placement validation; reference/worktree-lifecycle.md birth; D2 removes self-created separate-session lane.

> **A separate live session? The placeholders are not a stop.** Your issue holds the first two. If your dispatcher created and recorded a worktree for you, use it — validate the placement below and escalate on a mismatch; if the assignment is yours end-to-end, create the branch and worktree yourself off current `main` — and before creating the repo's first in-repo worktree, check `git check-ignore -q .claude/worktrees/probe`: if it fails, land the `/.claude/worktrees/` ignore line through a short-branch PR first (`reference/worktree-lifecycle.md`). What survives the paste is the *test*: **if the issue gives you no result to reach and no machine-judgeable done-check, ask on the issue before building.**

### W009 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - If the repo has a root `CLAUDE.md`, **read it in full first** — on a harness that doesn't auto-load it (Codex), it is the only place the project's commands, gotchas, and copy-list reach you; write back only a command, environment gotcha, worktree copy-list entry, or record-language declaration (`reference/repo-claude-md.md`).

### W010 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - **Validate your placement when the worktree was made for you**: `git rev-parse --git-dir` differs from `--git-common-dir` (you are in a linked worktree), the resolved toplevel equals the worktree recorded on your issue, your cwd is at that root (a subdirectory or wrong-directory start is a mismatch), and the checked-out branch matches the recorded one — any mismatch: escalate and stop, don't adapt.

### W011 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - Confirm your worktree is on a **named base** — `origin/main`, not just wherever HEAD points.

### W012 — `reference/worker-brief.md`

Disposition: reference/worktree-lifecycle.md birth, triggered by reference/worker.md receipt.

> - Copy in any untracked-but-needed files: `.env`, keys, local config (`reference/worktree-lifecycle.md`).

### W013 — `reference/worker-brief.md`

Disposition: reference/clean-handback.md, triggered by reference/worker.md receipt.

> - **Before the first task-generated write**, record `git status --porcelain -uall` in session scratch and publish it immediately to the issue; the final comparison and cleanup are in `reference/clean-handback.md`.

### W014 — `reference/worker-brief.md`

Disposition: reference/where-it-goes.md and reference/in-repo-writes.md; resident worker placement and ask-kind triggers.

> - **Place every write deliberately** — add only documentation admitted by `reference/in-repo-writes.md`; put every other file where something that already existed puts it (`reference/where-it-goes.md`). Nothing names a place: use the project-local default, gitignored unless the repo maintains the file; what dies with the task goes to session scratch. Never invent a place outside the project. Three never take that default: secret or confidential data, **never committed or published, whatever else is true of the file it sits in**; application state, persistent or operational, **for a program that outlives your task**; and a release deliverable. If nothing names a place for one of those, stop and tell the main session.

### W015 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - Install deps, then **confirm the tests pass before you change anything.** A passing start is what lets you blame later failures on your own change.

### W016 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - Read the canonical `docs/architecture.md` and skim `docs/adr/` unless that architecture doc points elsewhere, when the project has them. The shared baseline may have moved since the issue was written — build against what is on `main` now, not the spec's snapshot or your memory.

### W017 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - **Vet the issue and its design spec at receipt.** A spec that survived its challenge can still hide a gap a fresh reader catches. If the done-check looks wrong or unreachable, or the design won't start cleanly, raise it now (stop list below) — not after a full build.

### W018 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - **Work only in your branch and worktree.**

### W019 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - **Build the design that already survived a reviewer's challenge.** If the issue links a design spec, that spec is the design.

### W020 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - **One writer at a time.** Any helper you spawn is review/checking only: read-only, no worktree of its own, and clean — freshly spawned, no session history, never a context-inheriting fork. Route it: where Codex is installed, a read-only `codex exec` at the standing setting (`reference/external-agent.md`); otherwise set its model, `opus`.

### W021 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - **Update any doc your change invalidates** — docs ride the same diff. A change that turns out to touch architecture or the PRD escalates first (below).

### W022 — `reference/worker-brief.md`

Disposition: reference/worker.md record duty; core.md complete record rule.

> - **Write the record in English** — code, comments, docs, commit messages, the PR — unless the repo-root `CLAUDE.md` declares another record language. Text the product shows its own users (UI strings, user docs) follows the product's audience instead.

### W023 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - **Read your own diff end-to-end before opening the PR.** Hunt for what the done-check cannot catch: a leftover debug print, dead code, a half-finished edge case, a dropped requirement. Fixing it now costs minutes — letting merge check 1 catch it costs a whole review–fix–re-review round.

### W024 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - **Before delivering, `git fetch` and rebase onto current `main`,** fixing your own conflicts.

### W025 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - **Then run the done-check on your FINAL state** — after your last edit *and* the rebase — and capture that run's evidence: commands, exit codes, output. An earlier green run, from before a later change, does not count; re-run and re-capture.

### W026 — `reference/worker-brief.md`

Disposition: reference/worker.md delivery; reference/driving-a-pr-green.md ownership.

> - **Push, open a PR linked to the issue, and stay with it until its checks report green.** Opening the PR is not done, and a check that has not reported yet is not a green one. Fix what your diff broke; fix or answer every review-bot finding on the PR itself. Return before a check reports only when you actually have to — then hand back the PR link and name which checks are still unreported.

### W027 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - **Merge to `main`, or push a release tag.**

### W028 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - **Touch files outside your task, or edit another worker's branch.**

### W029 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - **Weaken, skip, or delete the done-check to make it pass** — or claim done without evidence.

### W030 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - **Merge because CI is unavailable, or offer your own local test run as a substitute for it.** Your done-check evidence is a claim for the reviewer to verify, never merge check 2. Working around an absent CI is not yours to do at all.

### W031 — `reference/worker-brief.md`

Disposition: reference/driving-a-pr-green.md; reference/worker.md handback boundary.

> - **Hand back a check you watched go red,** or a bot finding you never answered on the PR. What may be handed back: a run that has not reported yet, or a red you escalated on the PR as not yours to fix (below) — never a check your own diff left broken.

### W032 — `reference/worker-brief.md`

Disposition: reference/red-check.md; reference/worker.md NEVER boundary.

> - **Loosen, skip or delete a CI check to turn a red run green; re-run a failing check until it passes; read a red run as CI being unable to run.** (Two exceptions: a tracked, visible quarantine of a flake, below; and repairing an assumption your change deliberately staled — `reference/red-check.md` has the procedure.)

### W033 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - **Touch branch protection or the required-check list.**

### W034 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> Nothing lifts these — not a deadline, and not the human telling you to mid-task. A live instruction that collides with this list goes to the issue as an escalation; it never becomes permitted by being recorded ("How to tell it", below).

### W035 — `reference/worker-brief.md`

Disposition: reference/worker.md CI absence escalation.

> **No CI run appears at all:** if your own diff broke the workflow (invalid YAML, an `on:` filter that no longer matches), that's yours to fix like any other breakage you caused. Otherwise don't diagnose it and don't work around it — say what you observed in the PR and hand it to the main session, which owns the call about what CI's absence means.

### W036 — `reference/worker-brief.md`

Disposition: reference/worker.md flaky done-check.

> **Flaky done-check:** A done-check that fails then passes with no code change is flaky, not a real result — don't re-run it until it goes green (that hides the flake), and don't "fix" code that isn't broken. Quarantine it as its own visible change (skip/mark the test, open an issue to fix or delete it deliberately) and say so — a tracked, reviewed quarantine is not the banned silent weakening; the ban is on hiding it.

### W037 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> **Craft skills (from the superpowers plugin):** a bug task → `superpowers:systematic-debugging` (root cause before any fix); implementation guarded by tests → `superpowers:test-driven-development`. Use the skill for that step, then return to this brief — the skill's own "next, use skill X" pointers don't apply, and where it conflicts with this brief, this brief wins.

### W038 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - the task turns out to touch core architecture (the shared reference in `docs/architecture.md`);

### W039 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - a destructive or hard-to-undo action is needed (deleting data, force-pushing a branch others depend on — `main`, a shared branch, one a review is in flight against — anything leaving the repo: publishing, sending);

### W040 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - `reference/where-it-goes.md` sends a write to an ask: the project-local default never applies when nothing already names a place for secret or confidential data (never committed or published, whatever else is true of the file it sits in), application state for a program that outlives your task, or a release deliverable — stop and tell the main session;

### W041 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - deps won't install, or the runtime won't come up, for a reason unrelated to your change — report what you observed; don't route around it;

### W042 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - the done-check is wrong or unreachable, or the design must change a lot;

### W043 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - you're stuck on a direction call;

### W044 — `reference/worker-brief.md`

Disposition: reference/driving-a-pr-green.md, triggered by reference/worker.md escalation.

> - a check on your PR can never go green: a required check that is theirs and broken, a job needing a secret this repo does not have, or a bot demanding something the human already ruled out — post on the PR what you observed and what you tried, then hand it back; never sit re-running it, and never switch it off. A check that fails then passes with no code change has not gone green either — that is a flake, and the flaky-done-check rule above governs it;

### W045 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> - you're simply in over your head — reading file after file without getting closer, or you genuinely can't tell whether your approach is right.

### W046 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> **Not on that list:** `git push --force-with-lease` on your OWN unmerged branch, with no review in flight against it. That is ordinary work needing nobody's permission — it is how you amend after a check-1 finding. Two limits, both narrow: the lease is what makes it safe, so a bare `--force` is back on the list above; and it never buys you slipping a change past a review that already passed, because the reviewed diff must be the merged diff — amending after check 1 passed still re-runs check 1.

### W047 — `reference/worker-brief.md`

Disposition: reference/worker.md.

> Escalating a task you can't do is never held against you — the real failure is guessing and shipping plausible-but-wrong work instead of saying so.

### W048 — `reference/worker-brief.md`

Disposition: reference/worker.md return channel; D2 removes separate-session routing.

> **How to tell it:** if you're a subagent or a workflow agent, return the message in your output to whoever spawned or launched you (it passes up to the main session) — if you were invoked as a process, the file your final message is written to *is* that output, and it is the only channel you have. If you're a separate session, post it as a comment on the issue (so it survives in GitHub). The human may also talk to you mid-task to steer you — but any decision, spec change, or evidence from that chat only counts once it's written back to the issue or PR. An instruction that collides with the NEVER list does not become permitted by being written down — the NEVER list is absolute, and writing it to the issue is how you escalate it, not how you clear it.

### W049 — `reference/worker-brief.md`

Disposition: reference/worker.md verdict handling; reference/code-review-prompt.md remains sole readiness contract.

> When check 1 does not return Ready to merge under `reference/code-review-prompt.md`, verify each stated ground against the codebase before implementing it. The reviewer saw only the diff, the issue, and your report — not the wider codebase, platform or version constraints, or your reasoning — so a ground can be wrong for this project: it breaks working code, the current code exists for a compatibility reason, or it asks for a feature nothing uses (grep for the caller first). Verified correct → fix it, no commentary. Verified wrong → don't implement it; send the main session your technical reasoning with the evidence (the code, the constraint, the grep), and re-review settles it. Apply that prompt's Notes rule as written; this page adds no second handling contract. Fix the grounds that prevented readiness, then re-run the done-check before handing back.

### W050 — `reference/worker-brief.md`

Disposition: reference/worker.md verify/fix/refute; reference/driving-a-pr-green.md publication.

> **A review-bot finding gets the same verify-then-fix-or-refute discipline** — verify it against the codebase first, then fix what is right without commentary, or refute what is wrong with the evidence (the paragraph above; a bot is a confident false-positive generator, so verifying first matters more here, not less). One difference, and only one: a bot's answer goes on the PR itself, not into your handback, while a check-1 ground you contest still goes to the main session, as that paragraph says. A bot finding with no fix and no reply on the PR is unhandled, whatever you concluded privately.

### W051 — `reference/worker-brief.md`

Disposition: reference/red-check.md, triggered by reference/worker.md.

> **A red check is not a finding — it is the gate.** It cannot be answered, contested or waited out, and there are three states, not two: your diff caused it, your change deliberately staled the check's assumption, or neither — in which case it is not yours to work around. **Read `reference/red-check.md` before you touch a red check**; which of the three you are in decides everything, including whether the fix is yours at all.

### W052 — `reference/worker-brief.md`

Disposition: reference/worker.md CI absence/fallback boundary; reference/ci-cannot-run.md owns fallback.

> **While a CI fallback is in force** (the main session has declared that the platform can produce no run — `reference/ci-cannot-run.md`), there are no checks for you to drive green and nothing here for you to fix: hand the PR back with your done-check evidence as usual and say so. Running the fallback is the merging session's act, never yours.

### W053 — `reference/worker-brief.md`

Disposition: reference/worker.md delivery; reference/clean-handback.md final inventory; reference/driving-a-pr-green.md ownership.

> A PR is open, linked to the issue, rebased clean on current `main`, with evidence in the description, no doc left stale by your change, and every check on it reported green with every bot finding fixed or answered on the PR. After the last repository-touching command, its description also carries the baseline and final `git status --porcelain -uall` snapshots; every new visible path material the repo maintains is committed, and every other new visible path is removed (`reference/clean-handback.md`). If a run genuinely has not reported by the time you have to return, wait for it if you can; if you cannot, hand back the PR link and name the unreported checks in your final output, and the main session picks the duty up at delivery — if another worker spawned you rather than the main session, that handback rides up the same chain as a stop message (above), and passing it on is that agent's job too. **A check you watched fail is not unreported — it is unfinished work, and handing it back does not finish it.** If you finished but still hold a doubt about correctness or scope that isn't a stop-trigger, write it plainly in the PR description so merge check 1 sees exactly what you weren't sure of — don't bury it. **Name any durable write you made outside the repo** — a cache path, a deploy root — in the PR description too: the path, and why there. No check can see it in the diff, so the disclosure is the only record. Review and merge are the main session's job, not yours. **Leave your worktree and branch in place — the main session removes them when it merges.** If a later merge means the branch has to be rebased again and that creates conflicts after you've already finished, the main session opens a fresh issue for it — not you.

## Reference material affected by the move and pointer sweep

### R001 — `reference/external-agent.md`

Disposition: reference/external-agent.md executor routing and mechanics; D2 removes ladder/workflow/separate-session claims.

> # Dispatching to an external agent

### R002 — `reference/external-agent.md`

Disposition: reference/external-agent.md executor routing and mechanics; D2 removes ladder/workflow/separate-session claims.

> An agent invoked as a process rather than through your harness — such as a `codex exec`
> launched by Claude Code — is an admissible executor wherever this method would
> hand work to a fresh subagent: implementing a task, reviewing a diff, challenging a design. It is a
> choice of *executor* at rung 2, not a new rung on the ladder — it does not reach into a workflow
> run's agents and does not replace a separate live session — and **not a dependency**: a project
> without one loses nothing, because every rung keeps the executor it already had.

### R003 — `reference/external-agent.md`

Disposition: reference/external-agent.md executor routing and mechanics; D2 removes ladder/workflow/separate-session claims.

> On these projects **Codex is the standing external executor** (ADR 0045 for the topology, ADR 0040
> for the preference below); the
> neutrality above stands for any other tool. **The brief is where the worker constraints live —
> nothing on the target machine pre-arms them**: what makes the dispatched process a worker is the
> filled brief you paste, nothing else. And dispatching to an external agent is dispatching to an
> *agent* (#155/#156): brief it like a subagent — the outcome, the why, the boundaries, inputs and
> outputs, the done-check — grant the access the work needs (its own worktree, write access for
> implementation), and let it run its own loop. **Read-only is for gating reviews and challenges,
> never the default for real work**; a keystroke-scripted brief is the dispatcher overstepping into
> the worker's *how* (the issue-writing rule — outcome and why, never the how — extended to external
> dispatch). Before dispatching into a repo whose first in-repo worktree this would be, run the
> pre-creation ignore check (`core.md`'s worktree rule). And **an external reviewer's findings are
> verified before acting on them, never auto-applied** — the same stance this method takes toward
> every review bot.

### R004 — `reference/external-agent.md`

Disposition: reference/external-agent.md executor routing and mechanics; D2 removes ladder/workflow/separate-session claims.

> **Almost nothing here is new rule.** A worker never merges, one writer per worktree, done claims
> carry evidence, every gating review gets a clean reviewer, the reviewed diff is the merged diff —
> all of that is already blind to who executes, and stays exactly as written. What follows is only
> what the harness would otherwise have handled for you.

### R005 — `reference/external-agent.md`

Disposition: reference/external-agent.md executor routing and mechanics; D2 removes ladder/workflow/separate-session claims.

> ## When a subagent, when Codex

### R006 — `reference/external-agent.md`

Disposition: reference/external-agent.md executor routing and mechanics; D2 removes ladder/workflow/separate-session claims.

> Pick the venue first, as `core.md` says — in this session, rung 2, a workflow run, or a separate live
> session; this section decides only the **rung-2 executor** — a separate live session stays the lane
> for work that cannot be fully specified up front, and a workflow run keeps its own agents, its
> review panel included (that panel is workflow-native, and this rule does not reach into a run). Both
> candidates sit at rung 2 under the same rules. **Where Codex is installed, use it for dispatched work
> — a harness-native subagent only where the work especially suits one** (the human's ruling, ADR
> 0040). The lists below are that rule, not a menu. Two tie-breaks: **gating work always takes the
> fresh process** — a review or challenge is never "quick exploration", and one that needs a
> harness-only source gets that source's output folded into the report it receives (one of the three
> artifacts `core.md`'s reviewer rule allows — never a fourth) rather than a subagent; and for
> **implementation**, a hard capability need (this harness's own rung-2 mechanisms) wins — a subagent,
> because the other executor cannot do it.

### R007 — `reference/external-agent.md`

Disposition: reference/external-agent.md executor routing and mechanics; D2 removes ladder/workflow/separate-session claims.

> **Codex — the default:**
> - **Dispatched implementation** — a fully specified task that needs a real agentic loop: its own
>   worktree, write access, its own PR driven to green. It runs the worker side of the ceremony through
>   a PR whose checks are green or handed back unreported — never red — and leaves this session's
>   context untouched.
> - **A gating review or a design challenge** — what the gate needs is a fresh, process-isolated,
>   read-only run: no history, and the sandbox enforced by the OS rather than promised in a prompt.
>   A second vendor's judgment comes on top for the Claude Code orchestrator. The record names which
>   agent gave the verdict.

### R008 — `reference/external-agent.md`

Disposition: reference/external-agent.md executor routing and mechanics; D2 removes ladder/workflow/separate-session claims.

> **A harness-native subagent — only when** (a rung-2 subagent is always fresh — `core.md`'s ladder —
> so either executor starts cold and everything it needs goes in the brief; neither can ask):
> - **Quick read-only exploration** whose answer belongs in this context — the dispatch overhead (a full
>   brief, a separate process, an output file to read back) outweighs the work.
> - Work that needs **this harness's own rung-2 mechanisms** — `EnterWorktree`, MCP servers configured
>   here. (A need for the Workflow tool is not a rung-2 exception: it selects rung 3, another venue.)
> - A piece **small enough that the brief would be longer than the diff**.

### R009 — `reference/external-agent.md`

Disposition: reference/external-agent.md executor routing and mechanics; D2 removes ladder/workflow/separate-session claims.

> A subagent for an implementation task outside that list is a departure — say why in the handback
> (gating work has no such departure: the tie-break above is absolute). Where Codex is
> not installed, the preference above does not apply: another installed process agent stays admissible
> under the opening rule, and otherwise the harness's own executor does all of it ("When it is not
> there", below).

### R010 — `reference/prd.md`

Disposition: reference/orchestrator.md requirements binding; reference/prd.md founding mechanics survive; D1 removes automatic setup.

> The interview itself is the `superpowers:brainstorming` skill's craft — use it, then return here; the output lands in this PRD, not in superpowers' own spec files.

### R011 — `reference/architecture.md`

Disposition: reference/orchestrator.md requirements binding; reference/architecture.md template and structural duties survive.

> Settle the structure WITH the human, using the same interview discipline as the PRD: `superpowers:brainstorming`. Use it for the design dialogue, then return here — the design lands in this doc and its ADRs, not in superpowers' own spec files.

### R012 — `reference/design-spec.md`

Disposition: reference/orchestrator.md centralized design craft binding; reference/design-spec.md design admission and mechanics survive.

> Draft it with `superpowers:writing-plans` — a spec is a written plan a context-free worker will execute, and that skill's rules (exact file paths, complete code in every step, no placeholders, map the files and their responsibilities before writing steps, then a self-review pass) are what keep a zero-context worker from getting stuck. Then return to this flow: don't announce the skill; the spec lands in the repository's default or established spec location, not in superpowers' own plan folder; ignore its "REQUIRED SUB-SKILL" plan header and the execution-options menu at the end — DevStandard runs execution its own way. Where its mandatory test-first task template doesn't fit the task's done-check (a metric or refactor task isn't proven by a unit test), follow the done-check, not the template. On any conflict, this page wins.

### R013 — `reference/driving-a-pr-green.md`

Disposition: reference/driving-a-pr-green.md; D2 replaces direct orchestrator implementation beyond one-or-two-line edits with dispatch; reference/worker.md is the renamed source.

> **Taking delivery.** A dispatched worker terminates when it returns; it cannot watch a run that finishes minutes later, and the method never pretends otherwise. The duty transfers at delivery: the main session first compares the returned tree with its published baseline, ensures both `-uall` snapshots are on the PR, and resolves every new or unaccounted-for path under `reference/clean-handback.md`; then it looks at checks and bot findings, not yet spawning check 1 — a reviewer's time is wasted on a diff or tree that is about to change. Two ways to finish it. The main session drives the PR green itself on the worker's branch: its worker has terminated, so one-writer-per-worktree holds, and the merging session already owns that branch's teardown. Or it re-dispatches, handing over the new CI output and bot findings — which is the "change something before you re-dispatch" the ladder requires (core.md), and which makes that branch and worktree the new worker's outright, not "another worker's branch". Where a worker spawned a worker, the handback rides up the chain like a stop message: passing it on is each intermediate's job, and a summary that quietly drops an unreported check is how the duty ends up held by nobody. A PR whose worker terminated mid-run is not a rotting PR; it is the main session's — as is a PR a bot opened (a Dependabot pin bump), which has no session behind it at all. A PR the main session opened itself never transfers: it holds it to green.

### R014 — `reference/ci-cannot-run.md`

Disposition: reference/ci-cannot-run.md fallback procedure survives; D1 removes light-start routing; D4 replaces obsolete order assertion.

> | Not a trigger | Where it goes instead |
> |---|---|
> | slow, queued, or flaky CI; the session nearly over | wait — a queued run *is* a run (`queued` precedes `in_progress`) |
> | self-hosted runner offline — platform up, run queued | tell the human to check or restart the runner (`reference/self-hosted-runner.md` — for an ephemeral fleet an empty runner list is the idle state; a job `queued` past five minutes with the list still empty is the loop being down) |
> | red CI — a run that started and failed is CI working | branch → fix the branch; main → core.md's revert-first path; the pipeline aged → `reference/ci-pipelines.md` |
> | no run because of this repo: invalid workflow YAML, the workflow disabled in the Actions tab, `on:` filters no longer matching | fix it in a PR — CI is back in minutes |
> | Actions switched off at the org level — outside this repo, but not a platform event | the human's or an org admin's to lift; the merge waits |
> | the repo has no CI at all — no check 2 to degrade | the human's light start governs (core.md), or add the template from `reference/ci-pipelines.md` |
> | you cannot tell: no `gh` auth, no network, an unreadable Actions tab | establish the state, or wait — an unproven outage is not an outage |

### R015 — `reference/ci-cannot-run.md`

Disposition: reference/ci-cannot-run.md fallback procedure survives; D1 removes light-start routing; D4 replaces obsolete order assertion.

> **The order flips: evidence first, then check 1.** Normally check 1 precedes check 2. Under the fallback, run the suite and post the evidence *before* check 1, and hand that comment to the reviewer with the diff — an impartial clean reader auditing the run is the closest available substitute for an impartial runner. If check 1 sends the diff back, or the rebase moves, redo the run: the last evidence on the PR must come from the tree that actually merged.

### R016 — `reference/in-repo-writes.md`

Disposition: reference/in-repo-writes.md; D1 replaces setup/mini-setup vocabulary with per-task founding or architectural-redefinition trigger, retaining admission and no-remote evidence duties.

> 1. **A method kind whose own trigger fired.** The kinds and triggers are:
>    - `docs/PRD.md` and `docs/architecture.md`: setup or mini-setup;
>    - `docs/architecture/<subsystem>.md`: the overview can no longer explain that subsystem legibly;
>    - `docs/adr/NNNN-*.md`: the ADR admission test fired;
>    - `docs/specs/YYYY-MM-DD-*.md`: the change is substantial;
>    - the repo-root `CLAUDE.md`: there is a command, environment gotcha, worktree copy-list entry, or
>      record-language declaration to put in it.

### R017 — `reference/in-repo-writes.md`

Disposition: reference/in-repo-writes.md; D1 replaces setup/mini-setup vocabulary with per-task founding or architectural-redefinition trigger, retaining admission and no-remote evidence duties.

> 3. **It was requested in writing by an authority.** Authority is the human, the main session, or the
>    pre-work record: the issue as the dispatcher wrote it; the accepted spec at the version accepted,
>    whose reachable blob SHA was published to the issue before dispatch; or a pre-existing document.
>    A handoff or session-state artifact is never authority. A doer editing or commenting on its own
>    issue, or adding authorization to the spec it is implementing, is escalation until the main session
>    approves it there. In a light start with neither issue nor remote, the human's instruction in that
>    session may authorize a document only when disclosed with the handback.

### R018 — `reference/clean-handback.md`

Disposition: reference/clean-handback.md; no-issue/no-remote record retention remains, D1 removes light-start naming.

> Keep the snapshot in session scratch. Where there is an issue, publish it there immediately so it
> survives the session; otherwise publish it in the eventual PR or handback. If the first act creates the
> repository, record an empty-tree baseline and publish it on the setup issue once the repository exists.
> A light start with neither issue nor remote has no durable venue, so the doer keeps and compares the
> snapshot itself.

### R019 — `reference/out-of-repo-writes.md`

Disposition: reference/out-of-repo-writes.md disclosure and scratch; reference/worker.md owns executor scratch binding; D1 removes light-start naming.

> **3. Scratch, drops, and task-local deliverables** — session-local, gone when the session is; release
> deliverables are not this kind. Write to the
> scratch the session gives you — the location your harness provides: on Claude Code,
> `$CLAUDE_JOB_DIR/tmp` or the scratchpad it names; on a harness that names none (a standalone Codex
> session), one dedicated `mktemp -d` directory per task. Post any durable result to the issue, PR, or
> other destination the placement rule chose, then remove the scratch directory best-effort at task
> completion (an abnormal exit leaves it to the OS's tmp cleanup). A
> process-invoked agent (`reference/external-agent.md`) has none of that — under a write-scoped
> sandbox a Claude dispatcher's `$CLAUDE_JOB_DIR` is present as a variable but denied as a path (a
> Codex dispatcher passes none), and only the worktree and `/tmp` are writable — so its scratch is a gitignored
> subdirectory of its own worktree, which dies with the worktree (`reference/worktree-lifecycle.md`).
> An `-o` result captured by the dispatching CLI is a dies-with-the-task file: the CLI, outside the
> agent's sandbox, writes it into the dispatcher's session scratch as `reference/external-agent.md`
> prescribes.
> The human's Desktop and `$HOME` are never a drop target unless the human names one: showing them a
> result is what the PR, the issue, and the conversation are for.

### R020 — `reference/out-of-repo-writes.md`

Disposition: reference/out-of-repo-writes.md disclosure and scratch; reference/worker.md owns executor scratch binding; D1 removes light-start naming.

> Every durable write outside the repo is named in the PR description or, where a light start has no
> PR, at handback — the path, which branch of the rule applied, and why. **A committed write is
> reviewable; an ad hoc one is not.** If the write is in the diff — a script,
> a Makefile, a CI step that fetches to a path — merge check 1 sees it and can flag an invented
> location like any other line. A write done by a command typed in the session (which is what every
> row of the incident that prompted this rule was) leaves no trace in any diff; check 1 sees the diff
> and the report and nothing else, so nothing catches an undisclosed one.
> This is a discipline the acting agent keeps, not a gate — the same shape `reference/adr.md`'s
> attribution rule and ADR 0036 name for their own duties. The disclosure gives a human, or a later
> audit, the one place to look; the reviewer asks for it when a task plainly needed a location (a
> model, a dataset, a service) and the report names none.

### R021 — `reference/ci-pipelines.md`

Disposition: reference/ci-pipelines.md; core.md two-checks exceptions (D5) replace blanket-ceremony paraphrase.

> Protection changes only who enforces the ceremony, not the ceremony itself. Under DevStandard every change — however small — rides a branch + PR + fresh review + green CI (core.md); protection doesn't create a lighter lane for small changes. Required status protection makes GitHub enforce the CI portion; the guarded merge route checks the review record. A pre-green direct push is not prohibited by status protection alone. Where protection doesn't apply (free-plan private repos), the same gate is convention-only there — it binds all the same; the only difference is whether the platform blocks a violation or a reviewer catches it after.

### R022 — `reference/design-spec.md` ownership and handoff

Disposition: reference/design-spec.md retains the challenge, reachable accepted blob, issue
publication and status handoff. D2 replaces the main session's repository drafting with a worker
in its recorded lane; the orchestrator retains the design discussion, challenge and authorization
of implementation. Same-lane pre-PR continuation already exists in scripts/dispatch.

> - **Review = the existing pre-code challenge, run by the main session before dispatch**: a clean reviewer (freshly spawned, no history, didn't write it — a read-only `codex exec` where Codex is installed, `reference/external-agent.md`) tries to poke holes in the spec before any implementation starts. Nothing new is added on top.
> - **Flow**: the main session drafts the spec and runs the pre-code challenge BEFORE handing the task out — the header flips to `Status: accepted` when nothing blocking remains. Before dispatch, ensure that accepted blob is reachable in the repository, publish its blob SHA on the issue, and link the accepted spec as the worker's handoff. The spec file travels in the worker's implementation PR, which sets `Status: committed` before check 1 — the status describes the state at merge (no post-merge edit of a protected main). A spec whose decision must be settled long before building starts can instead merge alone in its own small PR at `accepted`; the implementation PR later flips it to `committed` as part of its reviewed diff.

## Search-twice reconciliation

- `core.md`, `reference/worker-brief.md`, `reference/orchestrator.md`, `reference/worker.md`: source
  clauses above dispositioned; the old worker path is a one-line pointer for one release.
- `scripts/dispatch`, `agents/worker.md`, `.github/check-agents.py`: canonical worker source
  repointed; frontmatter is a checked binding carrier. `agents/reviewer.md` and the fenced
  `reference/code-review-prompt.md` contract are unchanged because their source path and role
  remain correct. Reviewer operational publication already belongs to the caller.
- `reference/external-agent.md`: retired ladder citations replaced by supported routing; fixed
  dispatch, process lifetime, packet assembly and guard procedures remain operative there.
- `reference/prd.md`, `reference/architecture.md`, `reference/design-spec.md`: craft bindings
  point to the orchestrator; templates, founding mechanics, spec admission and challenge survive.
- `reference/driving-a-pr-green.md`: larger post-delivery repairs return to a lane; direct edits
  use the settled one-or-two-line limit. `reference/red-check.md` and `reference/ci-cannot-run.md`
  point to red-main recovery's new home; fallback admission remains unchanged, obsolete gate
  ordering and light-start references are reconciled.
- `reference/in-repo-writes.md`, `reference/clean-handback.md`, `reference/out-of-repo-writes.md`:
  per-task founding/redefinition replaces setup-size vocabulary. Admission safeguards and
  no-remote evidence duties survive. Process scratch points to the worker binding.
- `reference/repo-claude-md.md` repoints the explicit-read consumer; the operational content
  fence and language rule survive. `reference/worktree-lifecycle.md` and
  `reference/where-it-goes.md` need no wording change: their core pointers still lead to resident
  triggers and their own complete rules. `reference/self-hosted-runner.md` does not cite a moved
  clause; its procedure is unaffected.
- `reference/ci-pipelines.md`: the blanket-review paraphrase points to the shared two-checks
  rule and its #226 exception. CI provisioning and release mechanics remain unchanged.
- `README.md`, both plugin manifests: delivery, task-weight and executor descriptions reconciled.
  The lockstep minor bump rides this PR; the task adds role artifacts and delivery behavior.
- `CLAUDE.md`: local gate commands updated; #226's release-version wording landed in #234 and
  is retained through the rebase. Core's two-checks paragraph matches it. Historical page totals and rule
  costs remain history, not current measurement claims.
- `.github/workflows/ci.yml` and `.github/workflows/release.yml`: old forced-read-only/<4000-byte
  checks are intentionally staled by inline delivery. Replacement tests retain environment and
  lifecycle coverage and add boundary/overflow behavior. The old token ceiling is replaced by
  the derived budget. Worker-path assertions now follow the new role; worker birth routes to
  the lifecycle procedure because workers validate dispatcher-created lanes. No required check
  or branch-protection setting is removed. This is the visible staled-assumption repair under
  `reference/red-check.md`, not a weakening in response to a failing CI run.
- `docs/architecture.md`: adds only implementation-source/evidence pointers to the approved
  design. The dated requirement text is distinguished from its measured implementation by that
  pointer; unrelated mechanism evidence is not reclassified.
- `docs/adr/`: skimmed and searched, left untouched as explicitly required by this packet.
  Live routing in 0007/0008/0014/0015/0016/0019/0022/0024/0036/0040 and the other delivery/acceptance
  amendments remains Rebuild 7's reconciliation. This is a disclosed deferral, not a claim that
  those old live instructions were cleared. Historical specs and `_source/` are research/history,
  not operative role sources; they are left intact.

## Approval and completion evidence

The 2026-09-06 fix-round sweep checks the clause and its bounds, dispatch, acceptance and role
pointers:

- `core.md` already limits issue fields to goal, bounds (weight and required finish), and done-check;
  `reference/worker.md` only consumes the supplied bounds. Neither adds a spending field.
- `reference/orchestrator.md` removes the spending field and owns the cost rule beside the round
  cap; `reference/external-agent.md` removes the quota-budget analogy from model selection.
  D2, D3 and C020 above and the PR description record the same disposition.
- `docs/PRD.md`, `docs/architecture.md`, `reference/hard-edges.md`, the reviewer contract, agent
  definitions and dispatch/review/guard scripts retain goal bounds, human touchpoints and round
  accounting without another spending limit. Their pointers need no change.
- `reference/prd.md`'s product constraints, `reference/ci-pipelines.md` and
  `reference/ci-cannot-run.md`'s provider quotas, and the hook/context-size gates govern different
  constraints; they do not add a dispatch-cost approval or field. README and role/skill pointers
  impose no spending limit. Historical source quotes in this ledger and `_source/` stay verbatim.
- ADR 0006's budget loops, 0008's rationing, 0014's large-cost trigger, 0024's quota/rationing
  language and 0036's quota analogy are specifically included in the existing Rebuild 7 deferral.
  They are not silently cleared as history. ADR 0040's cost rationale expressly does not ration
  by price; historical measurement and change-cost statements elsewhere need no correction.

Human drop approval is recorded above and on the PR. Every source entry has a disposition;
architecture sign-off remains pending after round 2. Round 1's whole verdict is posted at
https://github.com/LeonJoeeee/devstandard/pull/235#issuecomment-5558730594.
Final test commands, exit codes, output and baseline/final snapshots belong on the PR; the main
session rules and commissions round 2 on the delivered head.
