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
The complete emitted context is also checked against `INLINE_CAP_BYTES` read from the hook, and
every delivered artifact must arrive inline: a crossing **fails** the gate instead of reporting
the delivery mode (#258, 2026-09-07), so an edit cannot enter the costlier startup path silently.
The measured overflow branch's before-acting IN FULL instruction stays what a larger artifact
receives at runtime — the hook's fallback, never a permitted CI state.
CI and the release validation invoke `.github/check-core-budget.py`; `CLAUDE.md` carries the
same command. The worker reference is expanded directly in dispatch prompts (outside the hook
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

Disposition: D2 removes workflow staging; D3 drops run-spending limits and its proposed issue-bounds replacement under the recorded human overruling. The cost rule lands in reference/orchestrator.md, Acceptance and integration; fixed review-cap mechanics remain in reference/hard-edges.md. Trimmed 2026-09-07 (#254): the cost rule stays on reference/orchestrator.md, but that page no longer carries the round number or a second statement of the first ruling in the same paragraph — reference/hard-edges.md states the seven-round cap and the orchestrator-first ruling and reference/external-agent.md enforces them; the page keeps the cap trigger and its pointer.

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

Disposition: core.md workflow; reference/orchestrator.md issue preparation. Trimmed 2026-09-07 (#254): reference/orchestrator.md no longer restates that human-raised work gets an issue before implementation; core.md's workflow paragraph states it and is resident for the orchestrator, and the page keeps settling the outcome and reason and writing the issue's fields.

> 1. **Issue first** — dispatched work, and any task the human raises, gets a GitHub issue (the result you want, why, and the done-check) opened *before* the work; clarifying with the human may come first, skipping the issue may not. A small fix the main session notices itself may skip the issue — the PR is its record — but never the ceremony below.

### C025 — `core.md`

Disposition: core.md interlock; reference/external-agent.md executor routing; D2 removes separate-session/workflow choices.

> 2. Pick who does it — the main session, a subagent/workflow, or a separate session (see "Who does the work" below).

### C026 — `core.md`

Disposition: reference/worker.md delivery; reference/orchestrator.md direct-edit duty. Trimmed 2026-09-07 (#254): the direct-edit paragraph stays the act site #206's group-1 sweep cleared, so it still names every write trigger (baseline, admitted documentation, established destinations, docs in the same diff, operational-only CLAUDE.md, final inventory) and still sends destinations and their ask-kinds to reference/where-it-goes.md; only the wording is compressed, and the enumeration now says whose triggers they are — core.md's before-a-write rows, which the orchestrator always has resident.

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

Disposition: reference/code-review-prompt.md unchanged contract; reference/external-agent.md assembler and publication; core.md two checks. Trimmed 2026-09-07 (#254): reference/orchestrator.md no longer restates what the assembler owns (current pins, required fields, whole-verdict publication), the Notes rule, or the definitions behind the two Floor consequences — reference/external-agent.md's Review packets states assembly, green-head admission, publication and the Floor 1 / Floor 2 lane consequences, and reference/code-review-prompt.md states that readiness comes from the Goal verdict and the two Floor checks alone. The page keeps both pointers, the readiness sentence, the no-verdict-never-passes bar and the two Floor triggers.

> 1. A **fresh reviewer** — clean per the review rule above, spawned new for each merge — give it the diff + the issue + the worker's report treated as unverified claims, and nothing else. Where Codex is installed it is a Codex run, read-only (`reference/external-agent.md`); its verdict names which agent gave it. Apply the goal-centered judging contract in `reference/code-review-prompt.md`; that file alone defines what blocks and what becomes a note. The verdict lands as a comment on the PR before the merge — the review history must be reconstructable from GitHub alone.

### C047 — `core.md`

Disposition: core.md two checks; reference/hard-edges.md merge proof.

> 2. **Green CI on the merged result against current main** — the automated, impartial final word; it doesn't grade its own work.

### C048 — `core.md`

Disposition: reference/hard-edges.md; reference/code-review-prompt.md unchanged narrow exceptions; core.md changed-head trigger. Trimmed 2026-09-07 (#254): reference/orchestrator.md no longer restates the proof's layers or where a failed proof routes; reference/hard-edges.md states both (content-unchanged replay plus merged-result CI, with failed layers returning to full review and conflicts to a resolver). The page keeps the changed-head trigger with its pointer, and its event table keeps the resolver dispatch.

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

Disposition: reference/worktree-lifecycle.md; core.md birth/death triggers; reference/external-agent.md fixed dispatcher. Trimmed 2026-09-07 (#254): reference/orchestrator.md's sweep keeps the trigger — by PR state, never git ancestry — and no longer restates why ancestry misses a squash- or rebase-merge; reference/worktree-lifecycle.md states that mechanic in its Death step 1 and leftover sweep.

> **Before a repo's first in-repo worktree is created — on any path, dispatch included:** `git check-ignore -q .claude/worktrees/probe`; if it fails, land the `/.claude/worktrees/` ignore line through a short-branch PR first (`reference/worktree-lifecycle.md`, Birth). **A worktree is deleted as soon as its task is done.** After the PR merges (or the human explicitly cancels the task — never guess from inactivity): check nothing is uncommitted or unpushed, then from the repo root remove the worktree, delete the branch, `git worktree prune` — in that order. The agent that merges a PR removes that PR's worktree and branch, even though the worker created them; don't touch a worktree for a task you are neither doing nor merging. While there, also sweep for other finished tasks' leftovers (`git worktree list`, then each one's PR state — `git branch --merged` misses a squash-merge) — a session sometimes ends before its own teardown, so cleanup gets two chances, not one. (`reference/worktree-lifecycle.md`)

### C053 — `core.md`

Disposition: reference/orchestrator.md architecture decision; core.md human sign-off. Trimmed 2026-09-07 (#254): the paragraph keeps the act and the human's approval before merge, and no longer spells out recording the decision in an ADR — reference/adr.md states what an ADR is and how it is written, and reference/architecture.md the shared document.

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

Disposition: reference/worker.md Never. Its landing paragraph's hook clause was narrowed on 2026-09-06 (#246) after six measured halts: a refusal of an action the task needs is the stop; a refusal aimed at a means is rephrased or reached another way, and rephrasing is not bypassing. reference/worker.md states it; reference/orchestrator.md keeps the resident ban and points there.

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

Disposition: reference/external-agent.md executor routing and mechanics; D2 removes ladder/workflow/separate-session claims. Trimmed 2026-09-07 (#254): reference/orchestrator.md's event loop keeps both triggers — an observation is not completion, and a live prior executor blocks the lane — while reference/external-agent.md states what the dispatcher records and refuses (native handles, PIDs, outfiles, completion markers, a still-running executor).

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

Disposition: reference/driving-a-pr-green.md; D2 replaces direct orchestrator implementation beyond one-or-two-line edits with dispatch; reference/worker.md is the renamed source. Trimmed 2026-09-07 (#254): taking delivery on reference/orchestrator.md keeps the trigger — both `-uall` snapshots on the PR, the delta accounted for — and no longer restates the baseline-versus-final comparison; reference/clean-handback.md states it. The same paragraph no longer repeats the one-or-two-line limit either: core.md's orchestrator contract states it and reference/orchestrator.md's Prepare the issue already carries it, so acceptance keeps only what is new there — larger repairs, conflict resolution included, are dispatched.

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
- 2026-09-07 (#254), `reference/orchestrator.md` inline headroom: restatements of clauses another
  page owns were replaced by their trigger plus a pointer, and the owner is named in the disposition
  of each source entry above — C020, C024, C026, C046, C048, C052, C053, R004 and R013. No rule left
  the method: every trimmed clause is stated in full on the page named there, and the two entries
  that record only compressed wording (C026, C053) say so. The act sites #206's group-1 sweep
  cleared stay act sites; the resident triggers, the #252 hook-refusal sentence and the
  requirements-craft binding are untouched. This is a headroom trim, not #206's group 5, which still
  audits both role references against the whole corpus. No page total is recorded here — the gate's
  before and after output belongs to the PR.
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

## Reference-corpus disposition (#206)

Status: all five groups delivered. The three drop proposals await the
human's decision and are **not applied**. Issue: #206. Group 1 recorded its source base here as
`96e1877`; from group 3 on, each group's own section records the base it was written against.
**The Group order section below is the only list of what is delivered and what remains** — group 3
appended a second one and the two immediately drifted (round 1 on PR #261, note 4), so group 2
removed it and folded its status into the original.

This section continues the same ledger rather than opening a second one. #205 dispositioned the
source clauses of `core.md` and the old worker brief; this section dispositions every **file** now
under `reference/`, against `docs/PRD.md` (the existence criterion in §7) and the approved
architecture (chapter 6, output 6). It is implementation evidence, not a shipped rules page.

### How each disposition was decided

**Keep** — the page traces to a PRD §1 problem or a §2 reuse decision, and it is the one place its
rule is stated. **Merge** — its surviving content belongs inside another page, and the page then
goes. **Move to a role** — the content is one role's operating instruction and belongs in that
role's context set (architecture ch. 2), leaving a trigger and pointer behind. **Drop** — nothing in
PRD §1 or §2 reaches it. A drop or a merge that deletes shipped words is a **proposal** here; the
human decides (PRD §7's existence criterion, architecture ch. 6 output 6), and nothing is deleted
before that.

**Where the one-site line falls.** Two kinds of site state a rule, and only one of them is a
duplicate:

- An **act site** is where the rule fires: `core.md`'s trigger table, and the two role references
  that are delivered whole to an agent that has read nothing else. It carries the situation, the
  operative act, and the pointer — never the rule's exceptional cases. `core.md`'s worktree trigger
  carrying the `git check-ignore` command is the deliberate example: a reader who does not run it
  never learns the check exists (`CLAUDE.md`, "the trigger always stays resident").
- A **reference** is what the pointer leads to. **Two references stating the same complete rule is
  the defect this audit removes**, because a reader following either pointer gets the whole rule
  twice and the two drift apart with nothing to catch it.

### Disposition table — every current file under `reference/`

| File | Disposition | Role | Act site | Tier | PRD trace |
|---|---|---|---|---|---|
| `adr.md` | Keep | Orchestrator | `orchestrator.md`, Prepare the issue (a significant, costly-to-reverse decision) | Soft | §1.5, §1.6 |
| `architecture.md` | Keep | Orchestrator | `orchestrator.md`, Prepare the issue (shared structure) | Soft | §1.1, §1.5 |
| `ci-cannot-run.md` | Keep | Orchestrator (merging session only) | `core.md`, "CI produces no run at all"; `orchestrator.md`, Exceptional events | Structural (published evidence block audited by check 1); Soft (the declaration) | §1.2, §2.1 |
| `ci-pipelines.md` | Keep; absorbs `self-hosted-runner.md`'s decision in group 2 | Orchestrator | `orchestrator.md`, Prepare the issue (CI/release setup, aging pipeline) | Structural (required check, branch protection); Soft | §1.2, §2.1, §2.2 |
| `clean-handback.md` | **Keep — now the single site for the baseline, the final delta, and worktree retention** | Worker; Orchestrator at delivery | `worker.md` before-first-write 3 and delivery; `orchestrator.md`, Acceptance and integration | Structural | §1.2, §1.5 |
| `code-review-prompt.md` | Keep (the reviewer context set, architecture ch. 2) | Reviewer | Packet assembly; `orchestrator.md`, Acceptance and integration | Structural (assembler fills every slot and refuses a partial packet); Soft (the judgment) | §1.2, §1.4 |
| `design-spec.md` | Keep | Orchestrator admits and challenges; worker writes the artifact | `orchestrator.md`, Prepare the issue | Soft | §1.4, §1.5 |
| `driving-a-pr-green.md` | Keep, **minus "Taking delivery" → move into `reference/orchestrator.md`** (group 2) | Worker; Orchestrator after delivery | `core.md`, "PR opened or delivered"; `worker.md`, Deliver evidence | Soft | §1.2, §2.1 |
| `external-agent.md` | Keep (group 4 audits its verified-mechanics block) | Orchestrator; worker for helper routing | `orchestrator.md` event loop; `worker.md` helper routing | Hard (dispatcher refusals); Structural | §1.1, §1.5, §2.2 |
| `hard-edges.md` | Keep | Orchestrator | `orchestrator.md`, Acceptance and integration; `core.md`, "Review return, changed head, conflict, or irreversible operation" | Hard | §1.2, §1.3, §2.1, §2.2 |
| `in-repo-writes.md` | Keep, unchanged — its predicate is copied verbatim into every review packet under a counted marker | Worker; Orchestrator for its own edits | `worker.md` before-first-write 4; the review packet | Structural (packet-copied predicate; Floor check 2) | §1.5, §1.6 |
| `orchestrator.md` | Keep (the orchestrator context set); audited last, in group 5 | Orchestrator | The SessionStart hook, delivered inline | Structural | §1.1, §1.5, §2.3 |
| `out-of-repo-writes.md` | **Keep — the three expensive kinds' own requirements only; the authority clause is no longer restated here** | Worker; Orchestrator for its own edits | `where-it-goes.md` continuation; `worker.md` before-first-write 4 | Soft; the ask is Structural | §1.3, §1.5 |
| `prd.md` | Keep | Orchestrator | `orchestrator.md`, Prepare the issue; `core.md`, "Founding bootstrap mechanics" | Soft | §1.4, §1.5 |
| `red-check.md` | Keep | Worker; Orchestrator for red main | `core.md`, "Red or flaky check"; `worker.md`, Review findings and red checks | Soft | §1.2 |
| `repo-claude-md.md` | Keep, unchanged | Worker and Orchestrator write back; every fresh session reads | `core.md`, "New operational knowledge"; `worktree-lifecycle.md` Death 2 | Structural (Claude Code loads it natively; Codex is instructed to read it); Soft (the fence) | §1.5 |
| `self-hosted-runner.md` | **Merge into `ci-pipelines.md`** — the decision is kept, the build recipe is drop proposal **P2**; not applied | Orchestrator relays; the human owns the machine | `ci-pipelines.md`, the minutes paragraph | Soft | §1.2 for the decision; the recipe traces to nothing |
| `where-it-goes.md` | **Keep — the placement entry point; sole site of the authority clause and the durability ask** | Worker; Orchestrator for its own edits | `core.md`, "Before a write" and the ask-kind trigger; `worker.md` before-first-write 4 | Soft (the judgment); Structural (the ask stops the lane) | §1.3, §1.5 |
| `worker-brief.md` | **Drop proposal P1** — a one-release compatibility pointer from #235; stays as its one-line pointer until the human closes the window | Worker | None; it is a path-compatibility shim only | — | none |
| `worker.md` | Keep (the worker context set); audited last, in group 5 | Worker | The dispatch prompt and the `devstandard:worker` definition | Structural | §1.2, §1.5, §2.3 |
| `worktree-lifecycle.md` | **Keep — birth and death mechanics; the baseline and the retention check are now pointers** | Worker at birth; Orchestrator at death | `core.md` worktree trigger; `worker.md` before-first-write 2; `orchestrator.md` after merge | Hard (the pre-creation ignore check); Structural | §1.1, §2.2 |

Every file now under `reference/` appears above. `core.md` is #205's, not a `reference/` page.

### Group order

One PR per group, never one PR for all pages (issue #206's bounds). This list carries each group's
state; nothing else in this ledger restates it.

1. **Writes and the tree** — *delivered* (PR #253): `where-it-goes.md`, `out-of-repo-writes.md`,
   `in-repo-writes.md`, `clean-handback.md`, `worktree-lifecycle.md`, `repo-claude-md.md`.
2. **The PR gate** — *delivered*: `driving-a-pr-green.md`, `red-check.md`, `ci-pipelines.md`,
   `ci-cannot-run.md`, `self-hosted-runner.md`. Carried the "Taking delivery" move into the
   orchestrator role. P2 was still unapproved when the group ran, so the `self-hosted-runner.md`
   merge is **not** applied and the proposal stays open below.
3. **Founding documents** — *delivered* (PR #261): `prd.md`, `architecture.md`, `adr.md`,
   `design-spec.md`. Ran ahead of group 2, whose move-to-role targeted a page #254 was trimming.
4. **Dispatch and the gates** — *delivered*: `external-agent.md`, `hard-edges.md`,
   `code-review-prompt.md`'s non-fence prose. #204 and #246 had both closed when it ran, so the live
   sentences they own on those pages were settled. Group 2's inherited finding is verified rather
   than collapsed: `hard-edges.md` is the single site for what classic status protection leaves open.
   **P1 and P3 remain unapplied** and still need the human; the fenced judging contract is untouched.
5. **The two role references** — *delivered*: `orchestrator.md`, `worker.md`. Ran last, because
   groups 1–4 change what they point at, and `orchestrator.md` is delivered inline against a
   measured budget, so its own trims are judged against that gate's output rather than a stated
   total. **P1, P2 and P3 all remain unapplied**; with no group left to carry them, each is now its
   own PR whenever the human rules. Rebuild 6's page audit is complete.

### Group 1 — the single-siting register

Each rule, its one site, and the sites that now carry a trigger and a pointer instead.

| Rule | Single site | Trigger + pointer sites | Change in this PR |
|---|---|---|---|
| Pre-write baseline snapshot: when to take it, the command, where to publish it, the no-issue/no-remote and taking-over cases | `clean-handback.md`, Baseline before work | `core.md` Before a write; `worker.md` 3; `worktree-lifecycle.md` Birth 5; `code-review-prompt.md`; `orchestrator.md` | `worktree-lifecycle.md` Birth 5 stated it in full; it now names the moment and points |
| Final delta, what is committed, what is removed, what may not be deleted | `clean-handback.md`, Final delta and cleanup | `worker.md` delivery; `orchestrator.md`; `worktree-lifecycle.md` Death 3 | unchanged |
| A kept file whose only durable copy is in the worktree is named and resolved before teardown | `clean-handback.md`, Final delta and cleanup | `core.md` worktree trigger; `worker.md` delivery; `worktree-lifecycle.md` Death 3; `where-it-goes.md` | the sentence stood **verbatim** in both `clean-handback.md` and `worktree-lifecycle.md`, and again in other words in `where-it-goes.md`; the single site now also names the venue (the PR, or handback where there is none), which none of the three did |
| Nowhere durable to keep a must-keep artifact → stop and ask | `where-it-goes.md`, Say where it went | `core.md` ask trigger; `worker.md` 4; `orchestrator.md`; `clean-handback.md` | unchanged rule; `clean-handback.md` now points at it so the retention check has somewhere to send a reader with nowhere to move the file |
| The authority clause: only something that already existed and puts **this project's** files there; a document relays authority and never originates one | `where-it-goes.md`, the placement rule | `out-of-repo-writes.md` (three places); `repo-claude-md.md`'s cache/deploy-root line | `out-of-repo-writes.md` restated it three times — in its opening, in the cache arm, and in the deploy-root arm; all three now point |
| Say where you wrote: every durable write outside the repo is named, with which branch of the rule applied and why | `out-of-repo-writes.md`, Say where you wrote | `core.md`; `worker.md` delivery; `where-it-goes.md` | `where-it-goes.md` stated it too; it now points |
| The three expensive kinds and their ask | `where-it-goes.md` | `core.md`; `worker.md` 4 | unchanged. Their kind-specific *requirements* — the cache order, the declared root and its retention, scratch — stay in `out-of-repo-writes.md`; that is the same rule's detail, not a second statement of it |
| The documentation admission predicate | `in-repo-writes.md`, inside its counted markers | `core.md`; `worker.md` 4; every review packet | unchanged. The predicate is machine-copied under a declared payload-line count; editing it is a packet change, not a prose change, and is out of this group's scope |
| What may go in a repo-root `CLAUDE.md`, and its 30-line cap | `repo-claude-md.md` | `core.md`; `worker.md`; `worktree-lifecycle.md` Death 2; `ci-pipelines.md` | unchanged. Its cache/deploy-root paragraph is the fence's own condition — may this line go in this file — not a second statement of the authority clause |
| Worktree birth and death, and the pre-creation ignore check | `worktree-lifecycle.md` | `core.md` worktree trigger (carries the command, deliberately); `worker.md` 2; `orchestrator.md`; `external-agent.md`; `ci-pipelines.md` | unchanged |
| The worktree copy-list | `repo-claude-md.md` holds the content kind; `worktree-lifecycle.md` Birth 4 holds the copy procedure | `worker.md` 2; `clean-handback.md` accounts against it | unchanged; complementary halves, not a duplicate |

### Group 1 — pointer sweep

Reconciled in this diff: `worktree-lifecycle.md` Birth 5 and Death 3; `where-it-goes.md`'s
disclosure paragraph; `out-of-repo-writes.md`'s opening, cache arm and deploy-root arm;
`clean-handback.md`'s retention sentence, which gains the venue the pointers now rely on.

Cleared without a change, each found by its pointer to one of these pages rather than by the words
added:

- `core.md`'s four write triggers still resolve. "Inventory before teardown; disclose durable writes
  outside the repo and must-keep worktree artifacts" now reaches the retention rule one hop further
  on, through `worktree-lifecycle.md` Death 3, which names the check at the act site.
- `worker.md` 3, 4 and its delivery paragraph, and `orchestrator.md`'s acceptance, worktree and
  direct-edit paragraphs, are act sites: they carry the operative act and the pointer, never the
  exceptional cases, so they are not second statements. `orchestrator.md`'s "inventory, retention and
  authorization checks" still names three things `worktree-lifecycle.md` Death 3 still has.
- `code-review-prompt.md`'s pre-dispatch snapshot line, `driving-a-pr-green.md`'s Taking-delivery
  pointer, `ci-pipelines.md`'s retained-report and worktree-ignore lines, `external-agent.md`'s
  pre-creation-ignore, scratch and force-delete pointers, `prd.md`, `architecture.md`, `adr.md`,
  `design-spec.md` and `README.md`'s location lines: all are pointers whose targets are unmoved.
- `CLAUDE.md`'s "`reference/worktree-lifecycle.md` is the standard — long exactly where the failure
  cannot be undone" is unstaled: this diff removed a duplicated sentence and a restated procedure,
  and left the Death section's irreversible-teardown reasoning whole.
- `docs/adr/` is not reconciled here. Its live routing statements are Rebuild 7's, as #205's sweep
  already disclosed; this is the same disclosed deferral, not a claim that they were cleared.

### Drop proposals — the human's decision, not applied

Nothing below is removed by this PR. Each names what fails the existence criterion and what would
survive.

- **P1 — `reference/worker-brief.md`, the whole page.** #235 left it as a one-line pointer to
  `reference/worker.md` for one release, so an older installed plugin's path still resolves. It
  traces to no PRD §1 problem and no §2 reuse; it is a path shim with a window, and the human owns
  when the window closes. Until then it stays exactly as it is, and CI keeps asserting its
  one-line shape. Removal is a shipped-page removal: minor bump, group 4.
- **P2 — the build recipe in `reference/self-hosted-runner.md`.** What survives and merges into
  `reference/ci-pipelines.md`: ephemeral rather than persistent, and the measured reason (a job's
  marker file survived into the next job on a persistent runner, and the probe that should have
  caught it reported success because a `run:` block's exit status is its last command's) — that one
  is a §1.2 trace, because a persistent runner makes "green" a weaker claim than check 2's;
  never on a public repo; the secrets the machine must not hold; and the queued-past-five-minutes
  signal that the loop is down. What is proposed for dropping: the Dockerfile, the entrypoint, the
  build and start commands, and the deregistration incantation. Those trace to nothing in §1 or §2
  — they are vendor documentation that ages on GitHub's clock, for a machine the human decides to
  stand up and owns. Removal is a shipped-page removal: minor bump, group 2.
- **P3 — the raw `codex exec` invocation block under "Verified mechanics" in
  `reference/external-agent.md`.** `scripts/dispatch` is now the operative statement of those
  invocations, and the page's own opening says to use it, so the block is a second statement that
  can drift from the script with nothing to catch it. The four gotchas beside it are findings, not
  commands, and would stay. Lower confidence than P1 and P2: a reader debugging a dispatch may want
  the shape the script builds. Group 4, and it needs #204's and #246's work to settle first.

**Re-examined and kept, against a live repo-ops finding.** `CLAUDE.md`'s page-audit rule names
`reference/adr.md`'s ADR-number ceremony as its worst weight failure — a collision this repo hits
because its product is decisions. The audit re-examined it and keeps the rule: this method makes
several open lanes the normal state of a target project too, so two branches claiming one number is
frequency-proportionate there now in a way it was not when that finding was made. The incantations
for finding a free number stay in `CLAUDE.md`, where that rule already put them; the shipped page
keeps only the rule.

### Group 3 — the founding documents

Source base: the lane's named base was `d86c819`; delivered rebased onto `bdc2c6d`, after #254
landed mid-lane.

Pages: `reference/prd.md`, `reference/architecture.md`, `reference/adr.md`,
`reference/design-spec.md`. Group 3 ran ahead of group 2 because group 2's one move-to-role targets
`reference/orchestrator.md`, which #254 was trimming — it could not land against a moving target.
#254 has since landed, so group 2 is unblocked and is next. Group order is otherwise unchanged.

All four keep their dispositions from the table above. The disposition table's `Keep` rows for
`repo-claude-md.md` and `in-repo-writes.md` put them in group 1, so they are not revisited here.

**Clause attributes.** Round 3 on PR #253 noted that group 1 recorded role, act site, tier and PRD
trace per *file* and asked the remaining groups for them per *retained clause*. Group 3's clauses:

| Rule | Role | Act site | Tier | PRD trace |
|---|---|---|---|---|
| The ADR admission test | Orchestrator | `orchestrator.md`, Prepare the issue | Soft (Structural in this repo only, through the unshipped `.github/check-adr-index.py`) | §1.5, §1.6 — the anti-accretion half is why the test exists at all |
| What makes the pre-code challenger clean, and how it is dispatched | Orchestrator commissions; worker for helper routing | `orchestrator.md`, Prepare the issue; `worker.md` helper routing | Hard (OS read-only sandbox); Structural (the dispatcher places the context) | §1.2 — a self-certified design is an unverified claim; §1.4 — a challenger carrying history drifts to the periphery |
| Founding setup owes no separate design spec | Orchestrator | `core.md`, "Founding bootstrap mechanics"; `orchestrator.md`, Prepare the issue | Soft | §1.4, §1.5 |
| Pin detail in proportion to the cost of getting it wrong | Orchestrator writes and briefs; worker builds inside it | `orchestrator.md`, Requirements craft | Soft | §1.4, §1.5 |
| Where each founding document lands, and what a convention may override | Worker; Orchestrator for its own edits | `worker.md` before-first-write 4; the review packet | Structural (packet-copied predicate) | §1.5, §1.6 |
| The PRD's and architecture doc's update-in-the-same-change duties | Worker; Orchestrator for its own edits | `core.md`, docs-invalidated trigger; `worker.md` | Structural at the trigger; Soft in judging what a change invalidates | §1.1, §1.4, §1.5 |
| ADR numbering, supersede-never-edit, and the amendment/status forms | Orchestrator, and any doer writing an ADR | `orchestrator.md`, Prepare the issue | Soft | §1.5, §1.6 |
| The spec status vocabulary and the accepted-blob handoff | Orchestrator accepts and publishes; worker writes and flips | `orchestrator.md`, Prepare the issue; the packet's accepted-spec slot | Structural (the assembler refuses a document admitted on `NONE`); Soft for the status call | §1.4, §1.5 |

**The register.** Each rule, its one site, and the sites that carry a trigger and a pointer instead.
Rows name the rule by its subject rather than restating it, so the ledger does not become a
second site for the rule it is auditing (round 3 on PR #253).

| Rule | Single site | Trigger + pointer sites | Change in this PR |
|---|---|---|---|
| The ADR admission test — which decisions earn an ADR | `reference/adr.md`, When to write one | `orchestrator.md`, Prepare the issue; `in-repo-writes.md` arm 1's ADR trigger; ADR 0017's 2026-08-13 amendment | the page stated the test **twice** — once as the two axes, once again as "Admission test when unsure" in different words. Merged into one statement that keeps every discriminator both carried, and the name "admission test" now labels the whole rule rather than only the second copy, so `in-repo-writes.md`'s pointer no longer lands on the narrower half |
| What makes the pre-code challenger clean, and how it is dispatched | `reference/external-agent.md`, When a subagent, when Codex | `core.md`, Executor choice; `worker.md` helper routing; `design-spec.md`, Mechanics | `design-spec.md` restated the properties **and** carried a raw `codex exec` routing incantation — the same shape drop proposal P3 names on `external-agent.md`. It now keeps the challenge trigger and the one property specific to this gate (the challenger did not write the spec) and points for the rest |
| Founding setup owes no separate design spec | `reference/prd.md`, Setup mechanics | `core.md`, "Founding bootstrap mechanics"; `orchestrator.md`, Prepare the issue; `design-spec.md`'s exemption paragraph | `design-spec.md` had **no** route to this rule while its own exemption paragraph closed the loophole the rule needs ("a spec and its challenge run regardless"), so the page read alone demanded a spec for the founding skeleton that `prd.md` and `orchestrator.md` both say is not owed. It now carries the trigger and points; the rule itself stays where `core.md` routes it |
| Pin detail in proportion to the cost of getting it wrong | `reference/design-spec.md` | `orchestrator.md`, Requirements craft | the paragraph closed with "That is how the no-placeholders rigor above applies here", whose antecedent — the `superpowers:writing-plans` paragraph quoted at R012 — was replaced by Rebuild 5 (`fa10051`). The back-reference has pointed at nothing since. Repaired to state the proportionality directly; both failure modes it names are unchanged |
| Where each founding document lands, and what an adopted repository's convention may override | the four pages' closing location lines, each for its own kind | `in-repo-writes.md` arm 1 (the canonical paths) and arm 2 (the convention) | unchanged — complementary halves. The predicate decides *admission*; each page's footer states *where its own kind lands*. `architecture.md`'s footer additionally holds the declaration rule for off-canonical mappings, which the other three point at |
| The PRD's and architecture doc's update-in-the-same-change duties | `reference/prd.md` and `reference/architecture.md`, each for its own document | `core.md`, "docs invalidated by the change"; `worker.md`; `orchestrator.md`, Architecture disagreement | unchanged. Each states what *triggers* its own document's update — a direction change through the human; a merge that changes structure — which the general same-diff rule does not say |
| ADR numbering, supersede-never-edit, and the amendment/status forms | `reference/adr.md`, Mechanics | `CLAUDE.md` (the four places to look); `.github/check-adr-index.py`; ADRs 0013, 0033 | unchanged. The number ceremony was re-examined in group 1 against ADR 0032's weight finding and **kept**; this group did not reopen it |
| The spec status vocabulary and the accepted-blob handoff | `reference/design-spec.md`, Mechanics | `orchestrator.md`, Prepare the issue; `in-repo-writes.md` arm 3 (the blob as authority); `code-review-prompt.md` (the packet slot) | unchanged. Three different jobs — the doer's procedure, the admission condition, the reviewer's check — not three statements of one rule |

**Weight (CLAUDE.md rule 1).** Re-checked page by page against frequency × cost in a *target*
project. `design-spec.md`'s longest item is the accepted-blob flow, where getting it wrong sends a
worker to build an unaccepted design; `adr.md`'s is the number ceremony, settled in group 1;
`prd.md` and `architecture.md` carry no block out of proportion. No weight change is proposed.

### Group 3 — pointer sweep

Reconciled in this diff: `reference/adr.md`'s admission-test block; `reference/design-spec.md`'s
exemption paragraph, proportional-rigor paragraph and challenge bullet.

Cleared without a change, each found by *its pointer to these pages* — the file it names or the
rule's subject — rather than by the words this diff added:

- `core.md` needs none. It names `reference/prd.md` for founding bootstrap mechanics (that rule is
  unmoved and now has a second consumer), and routes design and decision work through the role
  bindings rather than naming these pages; its Executor-choice paragraph is the act site for the
  reviewer-freshness rule and is unchanged.
- `reference/orchestrator.md` is an act site, and this lane did not edit it. Re-verified after #254
  trimmed that page mid-lane: its Prepare-the-issue paragraph still routes exemptions to
  `design-spec.md` and still states the founding-skeleton act; its Requirements-craft pin-detail
  sentence and its Architecture-disagreement same-change duty both survive. The contradiction this
  diff removes was on the `design-spec.md` side, so none of them needed a change.
- `reference/in-repo-writes.md` arm 1's ADR trigger reads "the ADR admission test fired". It now
  reaches a single statement instead of the second of two; the predicate itself is untouched, so
  the counted payload block is unchanged.
- `reference/out-of-repo-writes.md`'s "the same shape `reference/adr.md`'s attribution rule … name
  for their own duties" cites `adr.md`'s write-at-decision-time discipline, which this diff does not
  touch.
- `reference/external-agent.md` gains a consumer, not an edit: `design-spec.md` now points at it for
  the challenger's properties and routing. Its own "Gating review **or challenge**" sentence already
  covered the pre-code challenge, which is why the pointer needs nothing added there.
- `CLAUDE.md` cites `reference/adr.md` for the number ceremony, for the amendment-block form, and in
  ADR 0032's weight finding. None of those names the admission test, and none is staled.
- `.github/check-adr-index.py` enforces the amendment/status forms, untouched by this diff; its two
  docstring citations of `reference/adr.md` still resolve.
- `docs/adr/0017` — its Decision item 3 is the ADR that established the admission test (history), and
  its 2026-08-13 amendment routes it to `reference/adr.md` (live). Both still hold: the rule keeps
  every clause it had and its address is unchanged, so **no amendment is owed**.
- `docs/adr/0040`'s "Cost on the pages" bullet lists `reference/design-spec.md` among the act sites
  that "carry the Codex trigger and pointer". That is a list of what *that change touched* — history
  under `CLAUDE.md`'s structure cue, not a standalone routing sentence — so it is not reconciled.
  Its live 2026-09-05 amendment puts the fresh read-only reviewer and the dated setting on
  `reference/external-agent.md`, which this diff moves *toward*, not away from.
- `docs/PRD.md`, `docs/architecture.md` and `README.md` cite none of the four rules. README's
  "design-spec templates" is a contents listing.
- `docs/specs/` is history, including this ledger's own R010–R012 and R022 quotations of the
  superseded wording. They are the record of what Rebuild 5 replaced — and R012's quoted paragraph
  is the evidence for the dangling back-reference repaired above.
- `docs/adr/` is otherwise not reconciled here, for the reason #205's sweep already disclosed and
  group 1 repeated: its live routing statements belong to Rebuild 7. Same disclosed deferral.

### Group 3 — drop proposals

**None.** All four pages trace to PRD §1 problems, every clause this group touched survives at one
site, and nothing shipped is removed — so this group needs no human drop decision of its own. P1,
P2 and P3 from the table above are still open and still unapplied; they belong to groups 4, 2 and 4
respectively.

### Group 2 — the PR gate

Source base: `416c335` (`origin/main`), after group 3 landed as v0.39.9.

Pages: `reference/driving-a-pr-green.md`, `reference/red-check.md`, `reference/ci-pipelines.md`,
`reference/ci-cannot-run.md`, `reference/self-hosted-runner.md`. All five keep the disposition the
table above gave them. `reference/code-review-prompt.md` is **not** in this group — the disposition
table puts it in group 4 with the other gate pages, so neither its fenced judging contract nor its
surrounding prose is touched here.

**The move-to-role, clause by clause.** The audit found one move: `driving-a-pr-green.md`'s "Taking
delivery" paragraph duplicated `reference/orchestrator.md`'s acceptance procedure, and the role
reference is the act site. Checked clause by clause, the role reference already carried every
operative half, so **the move added nothing to `orchestrator.md`**:

| "Taking delivery" clause | Where it already was |
|---|---|
| compare the returned tree with the published baseline; both snapshots on the PR | `orchestrator.md`, Acceptance and integration, first sentence (which points at `clean-handback.md`) |
| inspect CI and bot findings before check 1 | `orchestrator.md`, Acceptance ("Read actual checks and bot findings… a red or pending head is not ready"), and the event table's Worker-delivery → Green-PR order |
| delivery transfers coordination, not permission to do an implementation-sized repair | `orchestrator.md`, Acceptance ("Larger repairs, including conflict resolution, are dispatched") and the event loop ("Delivery with unreported checks transfers coordination to you") |
| dispatch the named gap into the same lane | `orchestrator.md`, event loop ("Keep fixes in the same lane through the dispatcher's continuation interface") |
| the prior writer must have finished | `orchestrator.md`, event loop ("a live prior executor blocks it") |
| only a one-or-two-line repair fits the direct-edit allowance | `orchestrator.md`, Prepare the issue; `core.md`, the orchestrator role |
| a bot PR needs an owner and, for larger work, a lane | `orchestrator.md`, Acceptance ("Bot PRs need an assigned lane too") |
| returned unreported checks stay visible until green | `orchestrator.md`, event loop (dispatch their completion under `driving-a-pr-green.md`) |
| **intermediates carry an unreported check up with the handback** | **nowhere else** — it is a doer's duty, not an orchestrator act (ADR 0026's third accepted hole), so it stays on `driving-a-pr-green.md`, folded into "Handing back is not finishing" |

`orchestrator.md` is delivered inline against a measured cap, so the move was budgeted before it was
made: `python3 .github/check-core-budget.py` reported `reference/orchestrator.md: inline, context
9403 bytes (cap 10000)` at the base and the identical figure at the head, because the page is not
edited. The lane's ceiling for this move was 9,800 bytes; it never approached it, and no
trigger-plus-pointer compromise was needed.

**Clause attributes** for what this group retained, per clause (the per-clause form round 3 on
PR #253 asked for):

| Rule | Role | Act site | Tier | PRD trace |
|---|---|---|---|---|
| The PR's opener owns it until every check reports green and every bot finding is fixed or answered | Worker; Orchestrator on a PR it opened itself | `core.md`, "PR opened or delivered"; `worker.md`, Deliver evidence | Structural (the assembler refuses a red or unreported head at acceptance); Soft (the driving) | §1.2, §2.1 |
| Delivery transfers the duty; the acceptance procedure is the orchestrator's | Orchestrator | `orchestrator.md`, Acceptance and integration; its event loop | Structural (green-head admission) | §1.2, §1.4 |
| An intermediate passes an unreported-check handback up the chain | Worker acting as an intermediate | `worker.md`, Stop and return / Deliver evidence | Soft (ADR 0026 records it as an accepted hole with no receipt) | §1.1, §1.2 |
| A red check is the gate, in three states | Worker; Orchestrator for red main | `core.md`, "Red or flaky check"; `worker.md`, Review findings and red checks | Soft | §1.2 |
| A flake is not a green check; quarantine it visibly | Worker | `core.md`, "Red or flaky check"; `worker.md`, Flaky done-check | Soft | §1.2 |
| A check that can never go green is named, escalated and never waived in chat or switched off | Worker, then Orchestrator, then the human | `core.md`, "PR opened or delivered"; `worker.md` NEVER (branch protection and the required-check list) | Hard for the NEVER (the worker has no protection capability); Soft for the escalation | §1.2, §1.3 |
| CI and release pipelines: what to generate, and that they age on GitHub's clock | Orchestrator | `orchestrator.md`, Prepare the issue (CI/release setup, aging pipeline) | Structural (required check, branch protection); Soft | §1.2, §2.1, §2.2 |
| What branch protection buys, and what it leaves to the role guards and the merge route | Orchestrator; the human applies it | `orchestrator.md`, Acceptance (never weaken protection); `hard-edges.md` for the payload | Hard (the applied protection); Structural (the guard) | §1.2, §2.2 |
| A self-hosted runner: the human's call, never on a public repo | Orchestrator relays; the human owns the machine | `ci-pipelines.md`, the minutes paragraph | Soft; the public-repo prohibition is absolute | §1.2 |
| The check-2 fallback: trigger, non-triggers, who runs it, the evidence block and the return sweep | Orchestrator (merging session only) | `core.md`, "CI produces no run at all"; `orchestrator.md`, Exceptional events | Structural (published evidence block audited by check 1); Soft (the declaration) | §1.2, §2.1 |

**The register.** Each rule, its one site, and the sites that carry a trigger and a pointer instead.
Rows name the rule by its subject rather than restating it, so the ledger does not become a second
site for the rule it is auditing.

| Rule | Single site | Trigger + pointer sites | Change in this PR |
|---|---|---|---|
| Taking delivery — the acceptance procedure on a returned PR | `reference/orchestrator.md`, Acceptance and integration (an act site, delivered inline) | `core.md`, "PR opened or delivered"; `driving-a-pr-green.md`'s delivery paragraph | `driving-a-pr-green.md` stated the whole procedure a second time. It now states only what delivery does to the *duty* — it transfers, it does not end — and points. The one clause the role reference did not carry, the intermediate's relay, moved into "Handing back is not finishing" on the same page |
| A flake is a check that fails then passes with no code change | `reference/red-check.md`, closing paragraph | `core.md`, "Red or flaky check"; `worker.md`, Flaky done-check (which owns the quarantine); `red-check.md`'s own opening line; `driving-a-pr-green.md`'s never-green paragraph | `red-check.md` stated the identifying condition **twice on one page** — once as the "check flakiness first" ordering, once as the closing rule. The opening now gives the ordering and sends the reader down the page; the rule is stated once |
| On a free-plan private repo protection does not apply, and the gate binds anyway | `reference/ci-pipelines.md`, the branch-protection settings list | `ci-cannot-run.md`'s protected-main paragraph | stated **twice on one page**, in the settings list and again in the paragraph below it. Merged into the bullet, which is where a reader checking their plan looks |
| What classic status protection leaves open — no verdict verification, no PR-only write path | `reference/hard-edges.md`, Branch protection | `ci-pipelines.md`, the protection paragraph | `ci-pipelines.md` stated it **twice on one page** (once under the settings list, once in its closing note) while `hard-edges.md` states it beside the provisioning command that needs it. Both copies are now one pointer; `hard-edges.md` is group 4's page and keeps the statement |
| The self-hosted runner decision: gates unchanged, ephemeral by default, what it costs | `reference/self-hosted-runner.md` | `ci-pipelines.md`, the minutes paragraph; `ci-cannot-run.md`'s runner-offline row | `ci-pipelines.md` re-stated the unchanged-gates list and the fork-PR mechanism near-verbatim, and carried one claim that had gone false — "its environment drifts under you rather than being rebuilt each run" is the *persistent* model, which the same sentence's pointer calls not the default. It now keeps the triggers — minutes, the human's call, that the operating model is a choice and that persistent makes green a weaker claim, and the two costs that decide whether to reach for it at all — plus the pointer. The measurement behind the ephemeral default, the fork mechanism and the runner's own checks stay on the one page |
| The public-repo prohibition | `reference/ci-pipelines.md` (`self-hosted-runner.md` defers to it in its own words: "already says never") | `self-hosted-runner.md`, "A public repo", which keeps the fork/one-click mechanism | unchanged as a rule; `ci-pipelines.md` keeps the prohibition and drops the mechanism, so the two pages no longer both explain it |

**Considered and kept as complementary, not duplicated.** Each of these is a pair a matcher flags
and the one-site line does not reach:

- `driving-a-pr-green.md`'s closing "(a check that fails then passes … is a flake, not a
  resolution)" keeps the identifying condition because it is the trigger that stops a flake being
  misrouted into "can never go green". Dropping "with no code change" would leave a trigger that
  cannot fire (`CLAUDE.md`, "the trigger always stays resident").
- `ci-cannot-run.md`'s free-plan sentence states a different act — under the fallback nothing blocks
  the merge button, so the evidence and the audit are owed anyway — not the setup-time consequence.
- `ci-cannot-run.md`'s runner-offline row routes; `self-hosted-runner.md` diagnoses. The row's
  parenthetical is the routing a reader needs without opening the runner page.
- `driving-a-pr-green.md`'s never-green paragraph and `ci-cannot-run.md`'s protected-main paragraph
  both forbid switching a gate off, in two different states: a check that will never *go* green, and
  a required check that will never *report* under a declared fallback. The second names the four
  specific settings and the human's waiver route; the first has no waiver at all. ADR 0026 assigns
  the first to this page and ADR 0025 the second to that one.

**Weight (`CLAUDE.md` rule 1).** Re-checked page by page against frequency × cost in a *target*
project. `ci-cannot-run.md` is the longest page in the group and is deliberately so: ADR 0032 grew
it on purpose, because the branch that is almost always right — wait — was missing. Its length is
the fallback's cost, and it is audited **keep, unchanged**. `self-hosted-runner.md` is the one
weight failure in the group, and it is P2's subject rather than this PR's, because trimming it
deletes shipped words.

### Group 2 — pointer sweep

Reconciled in this diff: `driving-a-pr-green.md`'s delivery paragraph and its handback paragraph;
`red-check.md`'s opening flakiness line; `ci-pipelines.md`'s self-hosted-runner paragraph, its
protection settings list, its protection paragraph and its closing note.

Cleared without a change, each found by *its pointer to these pages* — the file it names or the
rule's subject — rather than by the words this diff added:

- `core.md` needs none. "PR opened or delivered" still routes to `driving-a-pr-green.md` for the
  ownership rule the page still states; "Red or flaky check" still routes to `red-check.md`, whose
  three states and flake rule keep every clause; "CI produces no run at all" still routes to
  `ci-cannot-run.md`, untouched.
- `reference/orchestrator.md` is the surviving site and this lane did not edit it — which is the
  claim the clause table above verifies rather than asserts. Its event loop still points at
  `driving-a-pr-green.md` for a delivery with unreported checks, and that page still answers the
  question the pointer asks.
- `reference/worker.md` is an act site and is group 5's. Its "neither → escalate through
  `reference/driving-a-pr-green.md`" still lands on the never-green paragraph, unmoved; its flaky
  done-check paragraph still owns the quarantine that `red-check.md` points at.
- `reference/self-hosted-runner.md` gains no edit and loses no pointer: its "A public repo" section
  says `reference/ci-pipelines.md` "already says never", and that page still says never. Its
  runner-offline paragraph still points at `ci-cannot-run.md`'s row, which is unchanged.
- `reference/hard-edges.md` gains a consumer, not an edit: `ci-pipelines.md` now routes the limits of
  status protection to it instead of restating them. Its own statement of those limits sits beside
  the provisioning command; group 4 owns that page and inherits the check.
- `reference/red-check.md`'s pointers out — to `orchestrator.md`, `ci-pipelines.md`,
  `driving-a-pr-green.md`, `code-review-prompt.md` and `worker.md` — all still resolve; nothing this
  diff touched moved a target.
- `.github/workflows/ci.yml`'s static assertion `grep -q "seeds the in-repo worktree root"
  reference/ci-pipelines.md` is one of the five worktree-ignore trigger sites; the paragraph it
  matches is not in this diff, and the assertion was re-run green.
- `CLAUDE.md` cites `reference/ci-pipelines.md` twice: for its tag-triggered release default, which
  this diff does not touch, and inside the search-twice section's own quoted example of a
  history-shaped Consequences sentence. Neither is staled. Its `reference/red-check.md` citation is
  about why that file exists, which is unchanged.
- `docs/adr/0029`'s 2026-08-13 amendment redirects *"its tag-triggered default still governs"* and
  the release-shape citation to `reference/ci-pipelines.md`. Both name the release template and its
  tag trigger, which this diff leaves untouched.
- `docs/adr/0031`'s word-count table is history (a measurement taken at that commit). Its two live
  statements about these pages — that `ci-pipelines.md` now hands off explicitly to
  `repo-claude-md.md`, and the two-hop route that makes such a hand-off legitimate — both still hold:
  that paragraph is not in this diff, and this diff adds hand-offs rather than removing any.
- `README.md`'s layout block lists the pages by kind. No page is added or removed, so it is unstaled.
- `docs/architecture.md`'s "Driving CI green" row assigns tiers to that edge and names no page; its
  `reference/worker-brief.md` citation in the evidence column is #235's staling, not this diff's.
- `docs/adr/0026` — its Decision bullets state the ownership, three-states, handback, transfer and
  never-green rules; those are the decision itself, and every one of them survives at a site this
  diff names. Its Consequences sentence "`howto/cicd.md` carries the operational half — … taking
  delivery and re-dispatch …" is a list of what that change touched, which `CLAUDE.md`'s structure
  cue calls history even in the present tense — and its own 2026-08-13 amendment already declares
  the `aids/`/`howto/` paths history. Its live amendment routes the *three-states* rule to
  `reference/red-check.md`, which this diff leaves as that rule's single site. **No amendment is
  owed**; the same test group 3 applied to 0017 and 0040.
- `docs/adr/0025`'s live amendments route the fallback's audit checklist and its identity proof to
  `reference/ci-cannot-run.md`, a page this diff does not touch, and say `reference/ci-pipelines.md`
  was not narrowed *by that change* — history about that change, not a bar on later ones. The
  fallback's trigger, non-triggers and evidence template are all unchanged here.
- `docs/adr/0032`'s finding that `driving-a-pr-green.md`'s trigger fires on 100% of tasks is why this
  diff removes words from it rather than adding them; its table row for `ci-cannot-run.md` ("grew")
  is the reason that page is kept unchanged.
- `docs/specs/` is history, including `2026-08-27-in-repo-writes.md`'s two citations of
  `driving-a-pr-green.md`'s "Taking delivery" — that spec records what was true when it was written.
- `docs/adr/` is otherwise not reconciled here, the same disclosed deferral groups 1 and 3 recorded:
  its live routing statements belong to Rebuild 7.

### Group 2 — drop proposals

Nothing is removed by this PR, and **P2 is not applied**: the human's approval is not recorded on
#206, and merging `reference/self-hosted-runner.md` into `reference/ci-pipelines.md` deletes shipped
words. P2 stands exactly as the table above states it — the decision, the measured persistent-runner
finding, the public-repo ban, the secrets the machine must not hold and the queued-past-five-minutes
signal survive and merge; the Dockerfile, the entrypoint, the build and start commands and the
deregistration incantation are what is proposed for dropping. Removal is a shipped-page removal:
**minor bump, and it would need its own PR** now that group 2 has run without it.

Two things this group did without a drop decision, and why neither needs one: reducing a second
statement to a pointer removes no rule (the rule survives at its single site), and removing the
"environment drifts under you" clause repairs a claim that had gone false rather than dropping a
rule — the page's own pointer names ephemeral as the default, which rebuilds the environment every
run.

P1 (`worker-brief.md`) and P3 (the raw `codex exec` block in `external-agent.md`) are untouched and
belong to group 4.

### Group 4 — dispatch and the gates

Source base: `e8c1656` (`origin/main`), after group 2 landed.

Pages: `reference/external-agent.md`, `reference/hard-edges.md`, and the **non-fence prose** of
`reference/code-review-prompt.md`. All three keep the disposition the table above gave them. The
fenced judging contract is untouched: `scripts/review_packet.py` requires exactly one bare fence on
that page and renders it as the reviewer's contract, so editing it is a packet change, not a prose
change — the same boundary group 1 drew around `in-repo-writes.md`'s counted predicate.

`reference/self-hosted-runner.md` is **not** revisited here. The Group order above puts it in
group 2, which audited it and left it unedited; its only open item is P2, restated below.
`reference/in-repo-writes.md` and `reference/repo-claude-md.md` are group 1's for the same reason.

The group's two blockers had cleared: **#204 and #246 are both closed**, so the live sentences they
own on `hard-edges.md` and `worker.md` were settled before this lane wrote anything.

**Where this group's one-site line fell.** Two references were each stating the other's rule, and
the act site had already drawn the boundary — so the audit followed `reference/orchestrator.md`
rather than inventing a split. Its Acceptance paragraph says `external-agent.md` "owns packet
assembly, green-head admission and publication" and that `hard-edges.md` "owns round accounting,
the cap, the orchestrator's first ruling and the merge guard"; `core.md` adds that
`external-agent.md` "owns routing, explicit models, fixed dispatch and review packets." Both moves
below are that boundary applied, in the two directions it points.

**Clause attributes** for what this group retained, per clause:

| Rule | Role | Act site | Tier | PRD trace |
|---|---|---|---|---|
| Executor routing — Codex where installed; a subagent for harness-only capability, quick read-only exploration, or a piece smaller than its brief | Orchestrator; worker for helper routing | `core.md`, Executor choice; `orchestrator.md` event loop; `worker.md` helper routing | Soft | §1.1, §1.5 |
| Route it explicitly — model and effort set on every dispatch, the Claude tier-alias ceiling, the standing setting stated once and dated | Orchestrator | `scripts/dispatch`, which reads the sentence at runtime; the two agent definitions | Structural (the dispatcher and a CI gate both read that one sentence) | §1.5, §1.6 |
| The per-role sandbox posture — read-only for a review or challenge, worktree-scoped write for an implementer, never a bypass mode, a blocked legitimate action is a stop | Orchestrator dispatches; worker obeys | `core.md`, Executor choice; `worker.md`, the hook/sandbox-refusal paragraph | Hard (the OS sandbox); Soft (the stop) | §1.2, §1.3, §2.2 |
| What a process executor returns, and that its outfile is the only channel back | Orchestrator; worker as intermediate | `orchestrator.md` event loop; `worker.md`, Stop and return | Structural (the dispatcher places brief and outfile in session scratch) | §1.1, §1.2 |
| The record says which agent produced the work | Orchestrator | the dispatch brief, so the agent emits it | Soft — the page states outright that it has no gate behind it | §1.2 |
| When the executor is not there — fall back only where the gate's properties survive; otherwise the gate blocks | Orchestrator | `core.md`, Executor choice; this repo's `CLAUDE.md` | Soft | §1.2 |
| Fixed dispatcher — required issue fields, a named base, deterministic lane identity, adoption, and its refusals including green default-branch CI on a new lane | Orchestrator | `orchestrator.md`, Ready issue and Red main; `core.md`, "Main goes red" | Hard (the script refuses before any lane exists) | §1.1, §1.2, §2.1 |
| Review packets — assembly, green-head admission, publication, and recovery after a lost return | Orchestrator | `orchestrator.md`, Acceptance and integration | Structural (a partial packet, or a red or unreported head, refuses) | §1.2, §1.4 |
| Round accounting — what consumes a round, the cap, the orchestrator's first ruling, and how each Floor result routes | Orchestrator | `orchestrator.md`, Acceptance; `core.md`, "Review return, changed head, conflict, or irreversible operation" | Hard (both the guard and the assembler refuse past the cap); Soft (the ruling itself) | §1.2, §1.4 |
| The merge and rebase proof — reviewed-head acceptance, the content-unchanged replay and its version-bump exemption, merged-result CI | Orchestrator | `core.md`, the two-checks paragraph; `orchestrator.md`, Acceptance | Hard | §1.2, §1.3, §2.1 |
| Role hooks and configurable authorization — the policy loader, the record shape, and what a probe does not establish | Orchestrator; the human authorizes | `worker.md` NEVER and its hook-refusal paragraph; `orchestrator.md`, Production/irreversibles | Hard (the hook); Structural (policy read from the default branch, never a worker file) | §1.3, §2.2 |
| The documented operation indicators and the shell composition contract | Orchestrator; worker and reviewer at the refusal | the hook itself; `worker.md`, "reissue it as separate simple commands the grammar admits" | Hard | §1.3 |
| Branch protection — the read-only check, the provisioning payload, and what classic status protection leaves open | Orchestrator relays; the human applies it | `orchestrator.md`, Acceptance (never weaken protection); `ci-pipelines.md`, the protection paragraph | Hard (the applied protection); Structural (the guard) | §1.2, §2.2 |
| The fenced judging contract — Goal, the two Floor checks, Notes, and the output shape | Reviewer | the packet the assembler renders | Structural (the dispatcher validates its template against this fence and fills every slot) | §1.2, §1.4 |
| Publish the verdict whole when it arrives, titled `## Merge check 1 — round N` | Orchestrator | the reviewer's own closing line, inside the fence — the act site, not the commissioning site | Soft (the discipline); Structural for the ordinary path, which `publish` performs | §1.2, §1.4 |
| Context rules — the packet is the reviewer's whole context, never session history; no test re-run; the CI-fallback slot | Orchestrator | the assembler | Structural (slot fill); Soft | §1.2, §1.4 |
| The two narrow exceptions to re-running check 1 on a changed head | Orchestrator, merging session only | `core.md`, "Narrow review exceptions live with the reviewer contract"; `orchestrator.md`, Acceptance | Soft | §1.2, §1.4 |

**The register.** Each rule, its one site, and the sites that carry a trigger and a pointer instead.
Rows name the rule by its subject rather than restating it, so the ledger does not become a second
site for the rule it is auditing.

| Rule | Single site | Trigger + pointer sites | Change in this PR |
|---|---|---|---|
| Round accounting — what consumes a round, the cap, the orchestrator's first ruling, and how each Floor result routes | `reference/hard-edges.md`, Review rounds and dispatch | `core.md`, the review-return trigger; `orchestrator.md`, Acceptance; `external-agent.md`'s Review packets (the `rule` command, its values and its refusals); `code-review-prompt.md`'s opening | `external-agent.md` stated the whole contract a second time — the cap, the first ruling, the Floor routing and the merge-as-is conditions. It now documents the commands and points. Two clauses that only the second copy carried moved **into** the single site rather than being lost: `merge-as-is` needs the reviewed head still green, and a malformed response consumes a round while an attempt that returned no verdict does not |
| Dispatcher refusals — a new lane needs green default-branch CI, and a delivered lane's continuation rides that PR's review history | `reference/external-agent.md`, Fixed dispatcher | `core.md`, "Main goes red"; `orchestrator.md`, the Red-main row and red-main recovery; `hard-edges.md`'s Review-rounds paragraph | stated in full on both pages. `hard-edges.md` now names which commands read the round history and points; the exception only *it* carried — recovery inside an existing lane stays available while main is red — moved into the single site |
| The per-role sandbox posture | `reference/external-agent.md`, Sandbox by role | `core.md`, Executor choice; `worker.md` helper routing; `hard-edges.md`'s role-hook paragraph | `hard-edges.md` restated "workers workspace-write, reviewers read-only" beside the tool cuts. It now points; the Claude tool allowlist and the worker network grant, which are its own, stay |
| An argv hook configuration is not proven enforcement | `reference/hard-edges.md`, Role hooks, beside the probe record that is its evidence | `external-agent.md`, Guarded executor and merge edges | `external-agent.md` stated it in the sentence immediately **after** its own pointer to that page. It now carries the trigger — the dispatcher pins the role hook in argv — and points |
| The Claude tier-alias routing ceiling does not reach another vendor's model names | `reference/external-agent.md`, the tier-alias paragraph | ADR 0024's 2026-09-05 amendment | stated **twice on one page**: once as the rule, once again closing the paragraph that explains what the explicitness prevents. That paragraph now ends on the failure it explains |
| A live executor in the lane blocks another dispatch | `reference/external-agent.md`, Fixed dispatcher | `orchestrator.md` event loop; the review-start paragraph on the same page | stated **twice on one page**, once generally and once for review starts. The review-start paragraph now names the situation and refers back — which is what makes `--native-finished` legible there |
| Reviewers always start fresh | `reference/external-agent.md`, the Claude-spawn paragraph, where `--resume` makes it operative | `core.md`, Executor choice; the page's own "When a subagent, when Codex" | stated **twice on one page** as CLI behaviour. The bare restatement in Review packets is gone; the copy that decides something — `--resume` never applies to a reviewer — stays |
| The fence is the sole judging contract | `reference/code-review-prompt.md`, Context rules | `orchestrator.md`, Acceptance; `worker.md`, Review findings; the fence itself | stated **twice on one page**, eleven lines apart. The bare restatement closing the assembler paragraph is gone; the copy that says what it *means* — Goal and the two Floor checks decide readiness, a Note cannot — stays |
| What the reviewer's packet carries | `reference/code-review-prompt.md`, the assembler paragraph | the fence's own slots; `external-agent.md`'s Review packets | the page listed the slots **twice in prose**, once as the assembler's inventory and once inside Context rules. Context rules now states the rule it exists for — that packet is the whole context, never session history — instead of re-listing it |
| What classic status protection leaves open | `reference/hard-edges.md`, Branch protection | `ci-pipelines.md`, the protection paragraph | unchanged. This is group 2's inherited finding, **verified rather than collapsed**: the statement is single-sited here and `ci-pipelines.md`'s pointer resolves to it |

**Considered and kept as complementary, not duplicated.** Each is a pair a matcher flags and the
one-site line does not reach:

- `external-agent.md`'s page abstract ("reviews and challenges are read-only") beside Sandbox by
  role. The abstract is a four-sentence orientation carrying none of the rule — not the
  OS-enforcement claim, not the bypass ban, not the blocked-action stop. Sinking it would open the
  dispatch page without saying what it dispatches into (`CLAUDE.md`, "the trigger always stays
  resident").
- `## Merge check 1 — round N` appears three times across two pages doing three different jobs: the
  discipline of publishing the moment a verdict arrives, the assembler's publication behaviour, and
  the comment that exception 1's byte-comparison is taken **against**. `CLAUDE.md`'s pre-merge
  command greps for the same heading.
- `hard-edges.md`'s "this CLI conservatively requires full review for an amended head or quoted-Note
  edit" beside `code-review-prompt.md`'s exceptions paragraph. The first is the CLI's own boundary,
  named by its inputs; the second is now the consequence for *these two exceptions* plus a pointer,
  where it previously restated the boundary.
- `orchestrator.md`'s Floor 1 / Floor 2 lines and its "a live prior executor blocks it" are act
  sites carrying the operative act and a pointer, never the exceptional cases — group 1's rule, not
  second statements.

**Weight (`CLAUDE.md` rule 1).** Re-checked page by page against frequency × cost in a *target*
project. `hard-edges.md` is the longest page in the corpus and is audited **keep**: its subject is
PRD §1.3, where the cost of getting it wrong is the one kind this method treats as unacceptable, and
its two long tables are closed contracts with literal test witnesses in `.github/test-hard-edges.py`
— a contract, which rule 3's own carve-out excludes from the enumeration ban, not an open-ended set.
It is `worktree-lifecycle.md`'s shape: long exactly where the failure cannot be undone.
`external-agent.md`'s weight sits in the dispatcher and review-packet contracts, which a target
project touches on every task. The one block whose weight is not earned is the raw `codex exec`
invocation — that is **P3's** subject rather than this PR's, because removing it deletes shipped
words. `code-review-prompt.md`'s exceptions section is rule 3 done right: two named cases and a
closing default ("any doubt about which case applies — re-run check 1"). No weight change is
proposed.

### Group 4 — pointer sweep

Reconciled in this diff: `code-review-prompt.md`'s opening routing sentence. It sent a reader to
`external-agent.md`'s Review packets section for "the commands, recovery path, **and orchestrator
rulings**" — and the ruling contract is exactly what this diff single-sites on `hard-edges.md`, so
that pointer would have landed one hop short. It now routes the commands and recovery to one page
and the round-accounting contract to the other. Found by *the pointer*, not by the words added.

Cleared without a change, each found by *its pointer to these pages* — the file it names or the
rule's subject — rather than by the words this diff added:

- `core.md` needs none. "`reference/external-agent.md` owns routing, explicit models, fixed dispatch
  and review packets" still holds on all four counts, and fixed dispatch gained a refusal rather
  than losing one. Its Executor-choice paragraph is the act site for reviewer freshness and the
  read-only posture, both unmoved; its review-return trigger and its changed-head sentence still land
  on `hard-edges.md`, which keeps every clause they name.
- `reference/orchestrator.md` is the act site this group's split follows, and this lane did not edit
  it. Both of its routing sentences are now *more* accurate: `external-agent.md` still owns packet
  assembly, green-head admission and publication, and `hard-edges.md` now owns round accounting, the
  cap and the first ruling without a second copy competing. Its own Floor 1 / Floor 2 lines and its
  event-loop liveness clause are act-site statements and need nothing.
- `reference/worker.md` is group 5's and is an act site. Its "reissue it as separate simple commands
  the grammar admits (`reference/hard-edges.md`)" still lands on the Shell composition contract,
  untouched; its lease-refusal pointer still lands on the role exceptions, untouched; its helper
  routing still lands on `external-agent.md`'s standing setting, untouched.
- `reference/ci-pipelines.md`'s three citations of `hard-edges.md` — the rebase proof, what status
  protection leaves open, and the provisioning payload — all still resolve. The middle one is group
  2's handover and was verified explicitly, not assumed.
- `reference/design-spec.md`'s "`reference/external-agent.md` owns what clean requires and how to
  dispatch it" lands on "When a subagent, when Codex", which this diff does not touch —
  group 3 having just pointed that page here makes it the citation most at risk, so it was checked
  first.
- `reference/out-of-repo-writes.md`'s "as `reference/external-agent.md` prescribes" lands on the
  outfile/session-scratch rule in "What it returns", untouched.
- `.github/workflows/ci.yml` asserts two things about `external-agent.md`: that exactly one dated
  standing-setting sentence exists across every live page and that it is on this one, and that the
  page still carries "pre-creation ignore check". Both survive, and both were replayed at the head.
  `scripts/dispatch` and `.github/test-review-packet.py` parse that same sentence at runtime.
- `scripts/review_packet.py` and `.github/test-dispatch.py` extract `code-review-prompt.md`'s single
  bare fence. The fence is byte-unchanged, which is why the assembly and dispatch suites pass
  unmodified.
- `agents/reviewer.md` and `agents/worker.md` point at their role sources by path;
  `.github/check-agents.py` re-verified both.
- `CLAUDE.md` cites `reference/external-agent.md` for "When it is not there", a section this diff
  does not touch, and greps for the `## Merge check 1` heading, which is unchanged.
- `README.md`'s four citations — the dispatch guide, the fixed dispatcher, the judging contract and
  the guard guide — are contents listings by kind. No page is added or removed.
- `docs/architecture.md`'s round-accounting and cap rows assign tiers to workflow edges and name no
  page. Its "Hard-edge implementation evidence (#204)" paragraph says `scripts/dispatch` "refuses
  new work on red default CI" — a record of what #204 built, history under `CLAUDE.md`'s structure
  cue — while its one routing sentence, "`reference/hard-edges.md` owns their operation and policy
  defaults", still holds. Not reconciled, and not silently skipped either.
- `docs/adr/0024`'s live 2026-09-05 amendment keeps the Claude tier cap and puts the standing setting
  on `external-agent.md`. The sentence this diff removed was the paragraph's *second* statement of
  that ceiling; the rule's own sentence is untouched, so the amendment still resolves. **No amendment
  is owed.**
- `docs/adr/0046`'s Decision states the seven-round cap, the orchestrator-first ruling and that a
  ruling cannot waive the Floor — that is the decision itself, and every clause survives at the site
  its own live sentence names ("the exact interfaces and limitations live in
  `reference/hard-edges.md`"), which this diff moves *toward*. `0011` and `0035`'s 2026-09-05
  amendments route the rebase proof to the same page, untouched here. **No amendment is owed.**
- `docs/adr/0034`'s publication rule cites `external-agent.md`'s "What it returns" and the reviewer
  prompt's closing line; both are unchanged. `0036`, `0038`, `0039`, `0040` and `0045` cite "When a
  subagent, when Codex" and the standing-setting line — the two blocks on that page this diff
  deliberately did not enter.
- `docs/specs/` is history, including this ledger's own source-clause dispositions, whose column for
  C-entry "Review packets states … the Floor 1 / Floor 2 lane consequences" records what was true at
  Rebuild 5. This section is the record of the move.
- `docs/adr/` is otherwise not reconciled here — the same disclosed deferral groups 1, 2 and 3 each
  recorded: its live routing statements belong to Rebuild 7.

### Group 4 — drop proposals

**Nothing is removed by this PR, and no drop is applied.** Reducing a second statement to a pointer
removes no rule — the rule survives at its single site — so nothing here needed a drop decision.
Three proposals stay open for the human, two of them this group's own:

- **P1 — `reference/worker-brief.md`, the whole page.** Unchanged and **not applied**. It is #235's
  one-release path shim, still exactly its one-line pointer, and CI still asserts that shape. The
  human owns when the compatibility window closes; the table above already records that it traces
  to no PRD §1 problem and no §2 reuse. Removal is a shipped-page removal: **minor bump, its own PR.**
- **P3 — the raw `codex exec` invocation block under "Verified mechanics" in
  `reference/external-agent.md`.** **Not applied**, and the audit single-sited *around* it: the
  block, its "another tool's flags are unverified" preamble and all four gotchas are byte-unchanged.
  The proposal stands as group 1 stated it — `scripts/dispatch` is now the operative statement of
  those invocations and the page's own opening says to use it, so the block can drift from the
  script with nothing to catch it, while the four gotchas beside it are findings rather than commands
  and would stay. Group 4's weight check agrees it is the one block on that page whose weight is not
  earned, which strengthens the case without deciding it. The lower-confidence reading group 1
  recorded also still stands: someone debugging a dispatch may want the shape the script builds.
  Removal is a shipped-page removal: **minor bump, its own PR.**
- **P2 — the build recipe in `reference/self-hosted-runner.md`.** Restated here because the group 4
  dispatch brief named it, though the Group order above assigns it to group 2, which ran without it.
  **Not applied, and nothing on that page is touched by this PR.** It stands exactly as groups 1 and
  2 stated it: what survives and merges into `reference/ci-pipelines.md` is the ephemeral-versus-
  persistent decision with its measured reason (a job's marker file survived into the next job on a
  persistent runner, and the probe that should have caught it reported success because a `run:`
  block's exit status is its last command's), never on a public repo, the secrets the machine must
  not hold, and the queued-past-five-minutes signal; what is proposed for dropping is the Dockerfile,
  the entrypoint, the build and start commands, and the deregistration incantation. Removal is a
  shipped-page removal: **minor bump, its own PR.**

### Group 5 — the two role references

Source base: `ccd2770` (`origin/main`), after group 4 landed. Pages: `reference/orchestrator.md`
and `reference/worker.md`. Both keep the disposition the table above gave them.

**Two constraints shape this group and no other.** `reference/orchestrator.md` is delivered inline
by `hooks/session-start` against a measured cap, and since #264 `.github/check-core-budget.py`
**fails** rather than reports when an artifact's complete context crosses it — so every edit of that
page was made against that gate's output, and the page must still arrive inline afterwards.
`reference/worker.md` rides the dispatch brief (`scripts/dispatch` expands it) and must stay
complete without `core.md`, as `core.md` promises. That second constraint decides one thing outright:
where `core.md` is the single site of a rule the worker still has to perform, `worker.md` cannot
point at it, and its compact statement of the operative act is the act site rather than a duplicate.

**Where this group's one-site line fell.** Both pages are **act sites** by the definition above —
each is delivered whole to an agent that has read nothing else — so the pair of them carrying the
same operative act is not the defect this audit removes, and group 1's register already settled
that. What the sweep looked for instead was the two shapes an act site can still get wrong: a rule
whose *full* statement sits here rather than at the reference that owns its subject, and a statement
that has **drifted** from the site it duplicates. Four of each kind were found; three of the four
drifts were introduced by Rebuild 5 itself, when the old worker brief was split into two pages.

**Clause attributes** for what this group retained, per clause. `orchestrator.md`'s tier is
Structural throughout its delivery — the SessionStart hook puts the whole page at the act site — so
the tier column below records what each *rule* binds by, not how the page arrives.

| Rule | Role | Act site | Tier | PRD trace |
|---|---|---|---|---|
| The event loop — reconstruct state from GitHub, one event at a time, priority order, short handlers | Orchestrator | `orchestrator.md`, Handle events; the hook that delivers it every session, clear and compaction | Structural (delivery puts it at the act site) | §1.1, §1.5, §2.1 |
| Every long wait is an observable dispatched lane; a handle, PID, outfile or marker is an observation, not completion | Orchestrator | `orchestrator.md`, Handle events; `external-agent.md`, What it returns | Soft | §1.1, §1.2 |
| Never resend an unchanged failed task; fixes stay in the lane through the continuation interface | Orchestrator | `orchestrator.md`, Handle events | Hard (the dispatcher refuses a continuation while a prior executor is live); Soft (changing the brief) | §1.1, §1.4 |
| Issue preparation — outcome and reason settled with the human; goal, bounds and a machine-judgeable done-check; implementation left to the worker | Orchestrator | `orchestrator.md`, Prepare the issue; `core.md`'s workflow line | Hard (the dispatcher refuses a missing field); Soft (the judgment) | §1.1, §1.5 |
| Which durable document a situation needs — PRD, architecture, ADR, design spec, CI/release | Orchestrator | `orchestrator.md`, Prepare the issue | Soft | §1.4, §1.5, §1.6 |
| Founding setup owes no separate spec; its mechanics are the PRD page's | Orchestrator | `orchestrator.md`, Prepare the issue; `design-spec.md`'s exemption list; `core.md`'s founding pointer | Soft | §1.6 |
| The requirements-skill binding — which skill at which trigger, and no second plan/handoff hierarchy | Orchestrator | `orchestrator.md`, Requirements craft (`core.md` names it the owner) | Soft — the orchestrator is a live session with no frontmatter for a gate to check, unlike the worker's | §2.3, §1.5, §1.6 |
| Skill containment — read at the trigger and return, ignore skill-to-skill chaining, the method's role and accepted task win, report a missing skill | Orchestrator; Worker | `orchestrator.md` and `worker.md`, each in its own binding section; `core.md`'s skill row | Soft | §2.3 |
| Acceptance — both snapshots with the delta accounted for, real checks and bot findings, a red or pending head returns, larger repairs dispatched | Orchestrator | `orchestrator.md`, Acceptance; `clean-handback.md`; `driving-a-pr-green.md`'s taking-delivery paragraph | Structural (the assembler refuses a non-green head); Soft | §1.2 |
| The review cap is the only cost limit — no spend field, no per-dispatch approval | Orchestrator | `orchestrator.md`, Acceptance | Soft (D3's landing, and the human's overruling of the proposed replacement) | §1.1, §1.4 |
| Merge through the guard; never weaken protection or the required-check list to manufacture readiness | Orchestrator | `orchestrator.md`, Acceptance; `hard-edges.md` | Hard | §1.2, §1.3, §2.2 |
| After merge — close, tear the lane down, sweep other lanes by PR state rather than git ancestry, release only on authorization or a standing delegation | Orchestrator | `orchestrator.md`, Acceptance; `worktree-lifecycle.md`, Death and Sweep | Hard (the release guard); Structural | §1.3, §2.2 |
| Red-main recovery — freeze new dispatch, revert by default, and a pure revert needs no new check 1 | Orchestrator | `orchestrator.md`, Exceptional events (`core.md`, `red-check.md` and `ci-cannot-run.md` all point here) | Hard (the dispatcher's red-main refusal); Soft (revert versus fix forward) | §1.2, §2.1 |
| No CI run — establish the state, normally wait, merging session only, no release under fallback | Orchestrator, merging session only | `orchestrator.md`, Exceptional events; `ci-cannot-run.md` | Soft | §1.2, §2.1 |
| Architecture disagreement or expansion — raised publicly, decided by the human, landed with its ADR in the same reviewed change | Orchestrator; the human decides | `orchestrator.md`, Exceptional events; `core.md`'s escalation trigger | Soft | §1.5, §1.6 |
| Production and irreversibles — branch plus both checks plus human review; a migration rehearsed and its rollback tested; standing permission applied through the guard, never inferred from urgency | Orchestrator; the human authorizes | `orchestrator.md`, Exceptional events; `hard-edges.md` | Hard (the guard); Soft (classifying what the hook cannot) | §1.3 |
| The orchestrator's own direct edits take the ordinary ceremony — short branch/PR, both checks, final-state evidence | Orchestrator | `orchestrator.md`, Exceptional events; `core.md`'s before-a-write triggers | Structural | §1.2, §1.5 |
| Receipt — the four packet fields, a missing or vague one stops the task, and the accepted design is vetted at receipt | Worker | `worker.md`, Receive the task, expanded into the dispatch prompt | Hard (the dispatcher refuses an unresolved field); Soft (judging vagueness) | §1.2, §1.5 |
| Task scratch and where a durable result goes | Worker | `worker.md`, Receive the task; `out-of-repo-writes.md`, kind 3 | Soft | §1.5 |
| Lane validation against the recorded worktree and a named base; a mismatch stops rather than adapts | Worker | `worker.md` before-first-write 2; `worktree-lifecycle.md`, Birth | Hard (the worktree and sandbox); Soft (the stop) | §1.1, §2.2 |
| The baseline snapshot, taken and published before anything the task produces | Worker | `worker.md` before-first-write 3; `clean-handback.md`, Baseline | Structural | §1.2 |
| Placement — admitted documentation, an established destination, and the three kinds that stop the lane | Worker | `worker.md` before-first-write 4; `in-repo-writes.md`; `where-it-goes.md` | Structural (the packet-copied predicate); Soft (the judgment) | §1.3, §1.5 |
| One writer at a time; a helper only reviews, fresh and read-only, and never wrote what it reviews | Worker | `worker.md`, Execute; `external-agent.md` | Hard (tool cuts and the sandbox); Soft | §1.2, §1.5 |
| Docs ride the same diff; a PRD or architecture expansion escalates before implementation | Worker | `worker.md`, Execute; `core.md`'s docs trigger | Soft | §1.5, §1.6 |
| Record language and commit attribution | Worker | `worker.md`, Execute — `core.md` owns the full rule, and this page cannot point at a page it must be complete without | Soft | §1.5 |
| The execution-skill binding — the two skills, inside the counted markers | Worker | `worker.md`'s marker block; `agents/worker.md`'s frontmatter | Structural (`.github/check-agents.py` reads the markers and requires the frontmatter to match) | §2.3 |
| The worker NEVER list | Worker | `worker.md`, Never; `core.md`'s worker paragraph | Hard (capability cuts, branch protection); Soft | §1.2, §1.3 |
| A hook or sandbox refusal — a refused action stays refused however it is spelled, while a refused *means* is reissued as simple commands the grammar admits | Worker | `worker.md`, Never; `hard-edges.md`, Shell composition contract | Hard | §1.3 |
| The stop list and the escalation channel, including a process executor's outfile | Worker | `worker.md`, Stop and return; `orchestrator.md`'s event loop | Structural (the outfile is the only channel); Soft (recognising the trigger) | §1.2, §1.3 |
| `--force-with-lease` on an own unmerged branch is ordinary work; bare force is not, and a guard refusal is returned rather than argued | Worker | `worker.md`, Stop and return; `hard-edges.md` | Hard (the guard) | §1.3 |
| Check-1 grounds are claims to verify; a bot finding gets the same discipline but its answer belongs on the PR | Worker | `worker.md`, Review findings; `code-review-prompt.md`; `driving-a-pr-green.md` | Soft | §1.2, §1.4 |
| Delivery — rebase, the done-check on the final state, evidence, then drive every check green | Worker | `worker.md`, Deliver evidence; `driving-a-pr-green.md` | Structural (CI reruns the mechanical assertions); Soft (non-mechanical evidence) | §1.2 |
| The final delta, disclosure of every durable write outside the repo, and leaving the lane in place | Worker | `worker.md`, Deliver evidence; `clean-handback.md`, Final delta | Structural | §1.2, §1.5 |

**The register.** Each rule, its one site, and the sites that carry a trigger and a pointer instead.
Rows name the rule by its subject rather than restating it, so the ledger does not become a second
site for the rule it is auditing.

| Rule | Single site | Trigger + pointer sites | Change in this PR |
|---|---|---|---|
| Founding work's design is the architecture the human settled, and that settling is its challenge | `reference/prd.md`, Setup mechanics | `core.md`, "Founding bootstrap mechanics"; `design-spec.md`'s exemption list; `orchestrator.md`, Prepare the issue | stated in full at **both** `prd.md` and `orchestrator.md`, neither pointing at the other, while `core.md` had already named `prd.md` the site. `orchestrator.md` now carries the act — commission no spec for founding setup — and points |
| What the first skeleton pins: interfaces and boundaries written as real code | `reference/prd.md`, Setup mechanics | `orchestrator.md`'s founding pointer | the clause lived **only** on `orchestrator.md`, orphaned from the rest of the founding bootstrap by Rebuild 5. A reader following `core.md`'s founding pointer never reached it. It moved into the single site rather than being lost |
| The superpowers dependency assumption | co-resident on `orchestrator.md` and `worker.md`, in one reconciled wording | `README.md` declares the requirement (ADR 0016's Consequences); PRD §2.3 records the reuse | the two pages had **drifted**: "must be installed" against "is installed" — a requirement on one page, an assertion on the other. Both now state ADR 0016's own word, *assumes*. Sinking it is not available: neither role reads the other's page, and without it "report a missing skill" reads as an expected state rather than a failure |
| Where a worker's task scratch goes | `reference/worker.md`, Receive the task, for the worker (`out-of-repo-writes.md` kind 3 owns the general rule and defers this case here) | `out-of-repo-writes.md`, kind 3 | the two sites **contradicted** each other: `worker.md` said `mktemp -d` unconditionally for every worker, while `out-of-repo-writes.md` gives Claude Code `$CLAUDE_JOB_DIR/tmp` and reserves `mktemp -d` for a harness that names none. The old worker brief scoped it to Codex; Rebuild 5 dropped the scope when it merged that paragraph. `worker.md` now carries the same branch, and names why a process executor always takes the second one |
| The return channel — a process executor's outfile **is** its output | `reference/worker.md`, Stop and return | `external-agent.md`, What it returns | `external-agent.md` quotes this rule in italics *as worker.md's own words*, and the quotation had staled: it read "whoever **spawned** you" against a page that now says "launched". One word, reconciled — a citation that does not resolve is what the sweep exists to find |
| Bot findings — verify, then fix without commentary or refute with evidence | `reference/worker.md`, Review findings | `driving-a-pr-green.md`; `code-review-prompt.md` | unchanged, and **verified rather than assumed**: group 2 pointed `driving-a-pr-green.md` at this page, so this is the citation most at risk in the corpus. It resolves, and the one difference that page names — the answer goes on the PR — is the same clause `worker.md` carries as its act |
| Red-main recovery | `reference/orchestrator.md`, Exceptional events | `core.md`, "Main goes red"; `red-check.md` state 3; `ci-cannot-run.md`'s red row | unchanged. Three pages point here and all three resolve. `ci-cannot-run.md`'s return path repeats "revert first; fix forward only when the fix is obvious and takes minutes" inside a parenthesis that says *applies as written* — a quotation of the rule it points at, not a second statement of it |
| The acceptance procedure for a delivered PR | `reference/orchestrator.md`, Acceptance and integration | `driving-a-pr-green.md`'s taking-delivery paragraph; `clean-handback.md` | unchanged; verified. That paragraph names the tree inventory, the checks and bot findings, and dispatching a named gap — three things this page still has |

**Considered and kept as complementary, not duplicated.** Each is a pair a matcher flags and the
one-site line does not reach:

- **The two skill-binding sections themselves.** They share five clauses, one of them verbatim
  ("Ignore skill-to-skill continuation instructions and execution menus"), and they stay. Neither
  role reads the other's page, and the rule fires *inside* a skill — at the moment its text says
  "next, use skill X". That is the sentence that makes someone look, so sinking it is deletion with
  extra steps (`CLAUDE.md`, "the trigger always stays resident"). What was reconciled is the drift,
  not the residency. The role-specific halves differ correctly: the worker's list sits inside
  counted markers a CI gate reads, the orchestrator's has no carrier to check it against.
- `orchestrator.md`'s "Bot PRs need an assigned lane too" beside `driving-a-pr-green.md`'s "a PR a
  bot opened is its to own from the moment it appears". The second states when ownership begins; the
  first states the act that follows. Removing either leaves a reader knowing only half.
- Both pages' *"read the root `CLAUDE.md`, the architecture and the decision log"* openings, and
  `core.md`'s before-a-write trigger. Three act sites of one trigger, which group 1's register
  already cleared; each is the situation and the act, and none carries the exceptional cases.
- `worker.md`'s record-language and English-record sentence beside `core.md`'s Record language
  paragraph. `core.md` owns the rule — `orchestrator.md` says so outright — and carries the
  exceptional cases (a declaration must be earned, a translation names its canonical file).
  `worker.md` cannot point at a page it is required to be complete without.
- `worker.md`'s three-state red-check line beside `red-check.md`. The act site names the three
  states and their acts; the reference owns what each state costs, the CI-diff-cannot-vouch-for-CI
  consequence, and the sub-routing of state 3. The trigger — *there are three states, not two* — is
  resident at both on purpose.

**Weight (`CLAUDE.md` rule 1).** `reference/orchestrator.md` carries the most-paid weight in the
corpus: it is delivered whole at every session start, clear and compaction, so its length is a cost
the orchestrator pays more often than any other page's. Audited **keep**, section by section. Its
four ordinary sections are hit on every task. Its Exceptional-events section is the low-frequency
half, and it earns its place by cost rather than frequency — red main freezes all dispatch, and
production and irreversibles are PRD §1.3, the one failure kind this method treats as unacceptable —
while staying three to six lines per case rather than a page. The event table is a closed
vocabulary with a closing `Idle` row, and the irreversibles paragraph closes on a default ("if you
cannot establish whether a decision reaches a human touchpoint, ask"), so rule 3 is satisfied in the
shape rule 3 asks for rather than by enumeration. `reference/worker.md` is audited **keep** on the
same reading: every section is hit on every task, its NEVER list is a closed contract that rule 3's
own carve-out excludes, and its stop list closes on a default ("simply being unable to establish the
right approach"). This group **removes 38 bytes of delivered context** from `orchestrator.md` — the
founding clause reduced to a pointer — and adds nothing to it. No weight change is proposed.

### Group 5 — pointer sweep

Both pages were swept **in both directions**, because groups 1–4 changed what they point at and
because four pages now point back at them.

**Reconciled in this diff**, each found by *the pointer* rather than by the words added:
`orchestrator.md`'s founding sentence, which stated `prd.md`'s rule instead of pointing at it;
`prd.md`'s Setup mechanics, which absorbs the orphaned skeleton clause; both binding sections'
dependency sentence; `worker.md`'s scratch sentence; and `external-agent.md`'s staled quotation of
`worker.md`'s return-channel rule.

**Cleared without a change**, each found by *its pointer to these pages* — the file it names or the
rule's subject:

- **`core.md` needs none, and this diff does not touch it.** Its four citations were each verified
  against the current pages rather than assumed. "It owns the event loop, operational context and
  requirements-skill bindings" holds on all three counts. "The worker reference is complete without
  this page and owns execution-skill bindings and handback" holds — and the completeness half was
  re-checked against the one clause that tests it, record language, which `worker.md` still states
  as its own act. The skill-binding trigger row routes to a section each page still has, and the
  "Main goes red" row still lands on red-main recovery, untouched.
- `reference/prd.md` and `reference/architecture.md` both say "use the requirements binding in
  `reference/orchestrator.md` for the design dialogue" — that binding is `superpowers:brainstorming`,
  still named there. `reference/design-spec.md`'s "centralized design craft binding" lands on
  `superpowers:writing-plans`, likewise unmoved. Group 3 pointed all three here, so they were
  checked first; the dependency sentence this diff reworded sits in the same paragraph.
- `reference/design-spec.md`'s founding-setup exemption already carried a pointer to `reference/prd.md`
  rather than a second statement, which is why it needed nothing when `orchestrator.md` did.
- `reference/driving-a-pr-green.md` cites `worker.md` three times (bot findings, the
  design-must-change stop-trigger, the flaky-test quarantine) and `orchestrator.md` once (the
  acceptance procedure). All four resolve to sections this diff does not touch.
- `reference/red-check.md`'s two citations — red-main recovery on `orchestrator.md`, the flaky-check
  rule on `worker.md` — both resolve. `reference/ci-cannot-run.md`'s red row resolves to the same
  recovery paragraph.
- `reference/repo-claude-md.md`'s "`reference/worker.md` instructs the read" lands on
  before-first-write 1, which still requires the explicit **IN FULL** read on every harness.
- `reference/out-of-repo-writes.md`'s "a process-invoked worker follows the scratch binding in
  `reference/worker.md`" is the one citation this diff's scratch fix had to keep true, and it is now
  *more* true: the two pages state the same two branches instead of contradicting on one of them.
  No pointer cycle was introduced — that page points here, and this page states the act without
  pointing back.
- `reference/external-agent.md`'s other two mentions are structural: its abstract naming both role
  sources, and "the worker prompt expands `reference/worker.md`", which matches `scripts/dispatch`.
- `scripts/dispatch` reads `reference/worker.md` whole into the brief and `hooks/session-start`
  delivers `reference/orchestrator.md`; `.github/check-agents.py` parses the WORKER SKILLS markers
  and requires `agents/worker.md`'s frontmatter to match them; `.github/check-core-budget.py`
  requires both pages to exist and be named in `core.md`, and the orchestrator page to arrive
  inline; `.github/workflows/ci.yml` greps `reference/worker.md` for "this brief is what makes you a
  worker" (case-insensitively) and for `reference/worktree-lifecycle.md`. Every one was replayed at
  the head, and the marker block is byte-unchanged.
- `README.md`'s two citations are contents listings by kind; its "Superpowers bindings live once per
  role, with Claude worker frontmatter checked against its source" is still exactly what
  `check-agents.py` enforces. Its declaration of the superpowers requirement is the site ADR 0016's
  Consequences names, and this diff moves the role pages *toward* it, not away.
- `docs/architecture.md` names both pages as Rebuild 5's implementation sources (ch. 3), which is
  unchanged. Its Workflow 3 evidence cell citing `reference/worker-brief.md` for final-state
  evidence is an evidence-state record of what was verified at the time — history under `CLAUDE.md`'s
  structure cue — and the same paragraph already records the compatibility-pointer status. Its
  worker-context-set paragraph (ch. 2) lists the packet fields `worker.md` still receives.
  Not reconciled, and not silently skipped either.
- `docs/adr/0016` is the decision behind the dependency sentence. Its Decision says DevStandard
  **assumes** superpowers is installed and that every pointer says "then return to this flow"; this
  diff moves both role pages onto that exact word and leaves the return clause on both. Its
  Consequences sentence "the README declares the requirement" is history under the act-versus-read
  test, and the README still does. **No amendment is owed.**
- `docs/adr/` is otherwise **not** reconciled here — the same disclosed deferral groups 1, 2, 3 and 4
  each recorded: its live routing statements belong to Rebuild 7.
- `docs/specs/` is history, including this ledger's own W-entries. W002's source clause is the record
  that the scratch rule was scoped to Codex before Rebuild 5 widened it; that entry stays exactly as
  written, and this section is the record of the correction.

### Group 5 — drop proposals

**Nothing is removed by this PR, and no drop is applied.** Reducing a second statement to a pointer
removes no rule — the rule survives at its single site, and the one clause that moved landed on
`reference/prd.md` before it left `reference/orchestrator.md` — so this group needed no drop
decision of its own. All three proposals stay open for the human, and **group 5 is the last group**:
each is now its own PR whenever the human rules, rather than riding a later group.

- **P1 — `reference/worker-brief.md`, the whole page.** **Not applied**, and deliberately untouched
  by this PR even though it is this group's own neighbour: it is the compatibility pointer to
  `reference/worker.md`, so a group auditing that page is the group most likely to sweep it away by
  accident. It stands as #235 left it — exactly one line naming `worker.md`, a shape
  `.github/check-core-budget.py` still asserts twice. It traces to no PRD §1 problem and no §2 reuse;
  it is a path shim with a window, and the human owns when that window closes. The audit
  single-sited **around** it: nothing in this diff points at it, and nothing in it points anywhere
  but `worker.md`. Removal is a shipped-page removal: **minor bump, its own PR.**
- **P2 — the build recipe in `reference/self-hosted-runner.md`.** **Not applied, and this PR does
  not touch that page.** It stands exactly as groups 1, 2 and 4 stated it: what survives and merges
  into `reference/ci-pipelines.md` is the ephemeral-versus-persistent decision with its measured
  reason (a job's marker file survived into the next job on a persistent runner, and the probe that
  should have caught it reported success because a `run:` block's exit status is its last
  command's), never on a public repo, the secrets the machine must not hold, and the
  queued-past-five-minutes signal; what is proposed for dropping is the Dockerfile, the entrypoint,
  the build and start commands, and the deregistration incantation. Removal is a shipped-page
  removal: **minor bump, its own PR.**
- **P3 — the raw `codex exec` invocation block under "Verified mechanics" in
  `reference/external-agent.md`.** **Not applied.** This PR edits one word elsewhere on that page —
  the staled quotation above — and leaves the block, its "another tool's flags are unverified"
  preamble and all four gotchas byte-unchanged. It stands as groups 1 and 4 stated it:
  `scripts/dispatch` is now the operative statement of those invocations and the page's own opening
  says to use it, so the block can drift from the script with nothing to catch it, while the four
  gotchas beside it are findings rather than commands and would stay; against that, someone
  debugging a dispatch may want the shape the script builds. Removal is a shipped-page removal:
  **minor bump, its own PR.**
