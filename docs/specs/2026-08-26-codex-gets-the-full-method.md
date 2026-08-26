# Codex gets the full method; worker constraints ride the dispatch, not the hook

Status: committed

*Accepted 2026-08-26 after seven challenge rounds, every round a fresh Codex reviewer at xhigh
effort, closing with an independent confirmation of the final three folds. The rounds included one
full adversarial exchange (the author narrowed a fix in round 3; round 4 rebutted the narrowing and
the stronger fix was adopted). Round trend: 6 → 4 → 6 → 5 → 5 → 4 → 1 → 0.*

*Round 2. Supersedes the role-identity half of `docs/specs/2026-08-26-claude-leads-codex-executes.md`
(shipped as v0.27.0): the human corrected the interpretation the day it shipped (#155). What that
spec measured and built mechanically — the branching hook, the harness discriminator, the
byte-identical Claude path — survives unchanged; what it decided about *identity* is walked back.
Round 1's six blockers (constraint relocation, sweep completeness, worktree bootstrap, ADR form,
verification rigor, combined context cost) are folded at their sections; #156 (dispatch Codex as an
agent, not an oracle) folds into the external-agent item. Round 2's four blockers (sweep depth:
PRD/0015/marketplace/README-requirements; the existing-repo bootstrap trigger; the refusal oracle's
attribution; V4's real done-check) are folded below. Round 3's six findings are folded — five in
full; its first fix was narrowed in round 4 — **and round 4's challenger rebutted the narrowing
successfully, so the stronger fix is adopted** (the defense was wrong: spawned subagents never
receive `core.md` — the brief is their guard — and "open Codex and say: take issue #17 through
merge" satisfies both predicates and resolves incorrectly under "if unsure"). Round 4's other four
blockers (ADR inventory incl. 0006/0008/0016; the one-page-footprint claims in README/architecture;
CI retirement assertions incl. this repo's own AGENTS.md block; V2/V4 runnability) are folded at
their sections. Round 5's five consistency/enumeration blockers (the stale resolver sentence; the lost brief-open trigger; the two human+Claude mirrors; per-ADR and per-trigger positive assertions; the page-unique-fact V2 oracle) are folded. Round 6's four blockers (the surviving worker-brief resolver; the missing Codex scratch lane;
the inferable V2 facts — replaced by transcript file-read events; the PRD non-goal and README
Layout label) are folded. Round 7 left one blocker (V2's causality/ordering — folded) and two notes (the AGENTS.md
inventory entries; the scratch cleanup obligation — folded), and re-endorsed everything else. This
is round 8, the confirmation round.*

## Problem & context

v0.27.0 read the human's "Claude leads, Codex executes" as an identity: every Codex session is
permanently a worker, told so by the hook, scoped by a committed `.devstandard` marker with an
adopt/unadopt ceremony. The human's actual intent (#155): **the leadership is the shape of a
collaboration, not a brand on the harness.** When Claude Code dispatches work, it leads and the
constraints ride that dispatch; standing alone, a Codex session is a full, capable session and
DevStandard is simply a useful tool for it — "脱离了主从控制之外，它也是一个非常优秀的插件".

Three existing facts make the corrected design *smaller* than what shipped:

- **Worker-ness has exactly one source: the dispatch.** The human's rule, verbatim in intent:
  *when it works as a worker, the constraints are injected by prompt; at any other time, it is
  itself a main session.* A session the human opens is the main session of that conversation —
  whatever the harness; a process or agent handed a brief is that brief's worker. And the main-
  session side of that needs **no announcement at all** — the human, sharper still: "甚至这个事情你
  都不用跟他说'你是主会话'…他是主会话的时候，该怎么做就怎么做就行" — a session is trained and
  harness-built to be the main session; that is its default nature, and `core.md` is already written
  to that reader. The only identity that ever needs SAYING is worker, and the dispatch brief's first
  line already says it. Under the adopted ruling `core.md` contains **no self-classification at
  all** — only the brief ever announces worker identity.
- **The dispatch channel already carries the constraints.** ADR 0036 / `reference/external-agent.md`
  / `reference/worker-brief.md`: a dispatched worker gets its brief pasted into its prompt — the
  NEVER list, one branch/one worktree, stop-and-tell, evidence. That is precisely "通过控制 context
  把那些东西注入", and it predates v0.27.0.
- **The delivery mechanics are measured and stay.** The branching hook, the `PLUGIN_DATA` equality
  discriminator, one-time trust, the byte-identical Claude branch — all keep working; only the Codex
  branch's *content* changes.

## Options considered

1. **Keep the role-hook, add an "independent mode" escape** — rejected: two modes plus a switch is
   more machinery to deliver less than the method's own primary-session test already provides.
2. **Deliver nothing on Codex, rely on dispatch briefs only** (pre-#148 status quo) — rejected: the
   human explicitly wants DevStandard available in daily Codex use ("平时就会 call 我们这个
   DevSTD").
3. **Codex branch delivers the method itself — chosen.** The same forced read of `core.md` the
   Claude branch delivers, plus a short harness note. Parity with Claude Code: the Claude hook fires
   in every session of every repo and nobody scopes it per-repo; the marker ceremony existed only
   because v0.27.0's payload *removed authority* — a method page does not, so the scoping loses its
   reason and retires with the role.

## Decision

1. **`hooks/session-start` — Codex branch content becomes the forced read.** Same JSON shape; the
   `additionalContext` mirrors the Claude branch's instruction (read `${PLUGIN_ROOT}/core.md` IN
   FULL before acting; reference/ paths relative to the plugin root) plus one harness line: *"You
   are running under Codex: read `${PLUGIN_ROOT}/reference/harness-codex.md` alongside it for the
   name mappings."* No marker check, no git probing — the Codex branch becomes as unconditional as
   the Claude branch (the git/marker scoping code is deleted). The Claude branch stays
   byte-identical; the unknown-harness branch stays.
2. **`reference/harness-codex.md` — essential mappings only, nothing else** (round-1 blockers 1
   and 6): `CLAUDE.md` = the operational-memory file — read it explicitly (Codex does not auto-load
   it), write back via PR; `EnterWorktree` → `git worktree add`; craft skills → the catalog's real
   names or the step's substance; model tiers → set yours explicitly, the cap vocabulary is
   Claude's; a gating helper = a separate `codex exec -s read-only` (in-tree spawns inherit your
   sandbox); **the Agent/Workflow primitives** — the Agent tool → `spawn_agent`, the plan list →
   `update_plan`, a "workflow run" → your harness's parallel/loop execution (the ladder's shape is
   unchanged, only the tool names differ); **and the cross-harness model rule** (round-3 finding 3):
   set the model explicitly on every spawn that takes one — the `opus` cap names Claude's tiers and
   binds agents spawned through Claude's harness; on Codex, route within your harness's own models
   at the human's standing effort settings; the discipline transfers, the tier names do not (ADR
   0036's ruling, now stated where a Codex main session reads). **No role text** — a main session is not told it is one (the default the harness and
   `core.md` both assume); worker-ness is said only by a dispatch brief, which opens by saying it.
   **The byte gate tightens to 4096** — this page is every Codex session's always-read payload, so
   it carries mappings and nothing that can live elsewhere. Two relocations follow: the **worker
   placement validation** (linked-worktree check, issue-recorded path, branch match, **and the
   cwd-at-that-root guard — a subdirectory or wrong-directory start is a mismatch**;
   escalate-on-mismatch) moves into `reference/worker-brief.md` "Before you write" — the brief IS
   the constraint channel, and a process worker reads nothing else (dispatcher-side launch
   mechanics stay in `external-agent.md`); the **fallback `AGENTS.md` snippet** (hookless
   environments) moves to `README`'s Codex install section — install-time material, never
   session-time payload.
3. **Retired: the `.devstandard` marker, `scripts/codex-adopt`, and the adopt/unadopt ceremony.**
   This repo's own marker and managed `AGENTS.md` block are removed in the same diff; its
   `/.claude/worktrees/` gitignore line stays. **The target-project worktree bootstrap the adopter
   incidentally carried gets a harness-neutral home** (round-1 blocker 3): the full setup seeds the
   in-repo worktree root (`/.claude/worktrees/`) into `.gitignore` alongside CI
   (`reference/ci-pipelines.md`'s setup step); an existing repo gets an **operative pre-creation
   trigger** (round-2 blocker 2), stated where the moment occurs — `worktree-lifecycle.md` Birth,
   before creating the first in-repo worktree, and `external-agent.md`'s dispatch steps:
   `git check-ignore -q .claude/worktrees/probe` fails → land the `/.claude/worktrees/` line
   through a short-branch PR first, then create or dispatch; the post-creation `check-ignore` stays
   the backstop. **The internal-dispatch path gets the same trigger where IT occurs** (round-3
   finding 2): `core.md`'s worktree paragraph — which today cites `worktree-lifecycle.md` only at
   teardown — gains the Birth pointer with the one-line trigger at the dispatch lane, and the
   worker-brief clause for sessions that create their own worktree carries the same check. **Migration note (carried in
   ADR 0039 and the release notes)**: a repo adopted under v0.27.0 **updates the plugin first**, then removes `.devstandard` and — in
   a hook-capable environment — the managed `AGENTS.md` block, by a small reviewed change, keeping
   the worktree-ignore line it independently needs; a **hookless** repo instead *replaces* the old
   role block with the neutral fallback snippet from `README` (removing it outright would remove
   its only delivery).
4. **Operative clauses walked back — the sweep enumerated in full** (round-1 blocker 2):
   `worker-brief.md` §Your role is **replaced whole** (round-6 finding 1 — dropping one sentence
   left the adjacent resolver alive): the new paragraph is brief-attributed — *this brief is what
   makes you a worker: it was pasted to you, or your assigning issue linked it; you own one branch
   and one worktree, and you never merge* — with **no** "if unsure" clause and **no**
   primary-session test; its line-5
   pointer becomes "read `reference/harness-codex.md` for the name mappings" (no role claim); its
   separate-session clause returns to: an assigned worker uses the branch/worktree its issue
   records, a session that owns its assignment creates its own; its "Before you write" gains the
   relocated placement validation (item 2). `core.md`'s routing sentence: *"Not a Claude Code
   session? Read `reference/harness-codex.md` alongside this page for the name mappings."*;
   `core.md` keeps "dispatching to an external agent defaults to Codex where installed".
   **`core.md`'s worker self-classification is removed; its worker paragraph is rewritten in the
   third person** (round-3 finding 1, adopted in full after round 4's rebuttal): the "You are the
   main session ONLY if… / if unsure, you're a worker" resolver goes; the paragraph becomes a
   description of what a *dispatched worker* is and owes — told so by its brief (pasted, or opened
   via its assigning issue), the **only** thing that ever says "you are a worker". Safety lives
   where it always did: spawned subagents and workflow agents never receive `core.md` — their guard
   is the filled brief, unchanged; a separate live session working an assigned issue gets the same
   contract from `worker-brief.md`, which its issue links. **One neutral, third-person trigger stays in `core.md`** (round-5 finding 2): *every dispatched worker receives, or opens, `reference/worker-brief.md` before acting* — replacing the old parenthetical pointer that ADR 0015's 2026-08-22 amendment records as load-bearing; 0015's new dated block reconciles that record. This edits text every harness reads,
   deliberately: identity resolution IS what the human's correction governs; the protocols (two
   checks, who merges, dispatch mechanics) are untouched.
   **`.codex-plugin/plugin.json`'s description is rewritten as a standalone method manifest** (the
   full method for Codex sessions; collaboration via dispatch — no executor identity, no marker
   mention). **`reference/repo-claude-md.md` line 5 is re-neutralized**: the file's readers are the
   main session — whatever harness — and every dispatched worker; Codex sessions read it
   explicitly. **`reference/out-of-repo-writes.md` joins the sweep** (round-6 finding 2): its session-scratch
   rule goes harness-neutral — a session writes scratch to the location its harness provides
   (Claude Code: `$CLAUDE_JOB_DIR/tmp`); a session whose harness names none (a standalone Codex
   session) uses one dedicated `mktemp -d` directory, named in the PR when its contents matter, removed best-effort at task completion (abnormal
   exits rely on the OS's tmp cleanup) —
   and `worker-brief.md`'s scratch wording follows suit. `reference/ci-pipelines.md` drops the adopter reference and gains the
   worktree-ignore seeding (item 3). `reference/worktree-lifecycle.md` drops the placement-guard
   cross-reference to the role page. `reference/external-agent.md` keeps the standing-executor
   default and verify-never-auto-apply, drops the marker-verification duty, cites 0039 where it
   cited 0038's identity, states plainly: *the brief is where the worker constraints live; nothing
   on the target machine pre-arms them* — and gains the **dispatch-as-agent clause (#156)**:
   dispatching to an external agent is dispatching to an *agent* — brief it like a subagent
   (outcome, why, boundaries, inputs/outputs, done-check), grant the access the work needs (its own
   worktree, write access for implementation), and let it run its own loop; **read-only is for
   gating reviews and challenges, never the default for real work**; a keystroke-scripted brief is
   the dispatcher overstepping into the worker's *how* (the issue-writing rule — outcome and why,
   never the how — already says this; the clause extends it to external dispatch explicitly). **`CLAUDE.md`'s command mirrors** (1b/1c) are
   updated to the new gate shapes. **`README`** qualifies "every later session loads `CLAUDE.md`
   automatically" to Claude Code (a Codex session is told to read it), gains the relocated fallback
   snippet in its Codex install section (with the `AGENTS.override.md` note: a hookless repo whose
   effective instruction file is the override places the snippet THERE, or it is shadowed; and the snippet stays **prepended**, so a long
   file cannot truncate it), and its
   **Requirements section adds Codex as a co-equal harness** (Claude Code stays the reference).
   **The one-page-footprint claims are enumerated and rewritten** (round-4 finding 3): README's "a
   hook puts one page into every session", "one page, under 5,000 tokens, per session", "the entire
   always-on footprint is one page", the context FAQ, **`docs/PRD.md`'s operative non-goal ("one
   always-on page + on-demand files")**, and **README Layout's Claude-only forced-read label**, and **both source-tree inventories drop the
   managed root `AGENTS.md` entry** (the fallback snippet is install guidance, never a tracked
   repository file)
   (round-6 finding 4); `docs/architecture.md`'s single-page
   delivery/budget paragraphs and Workflow-tool-as-substrate wording — all become: *Claude Code
   reads `core.md`; Codex reads `core.md` plus the bounded mappings page*. **Round-2 blocker 1's deeper sites**: `docs/PRD.md`
   is re-neutralized where it defines the tool and its users as Claude-only (the method serves
   agent sessions; Claude Code is the reference harness); **ADR 0015's operative "human + Claude"
   cockpit Decision gains a dated `(2026-08-26, see 0039)` amendment** (the cockpit is the human +
   the main session, whatever its harness — with matching status entry, body untouched);
   **ADR 0024 (and 0008's amendment where it names tiers) gain the same dated scoping** — the
   `opus` cap binds agents spawned through Claude's harness; a Codex main session routes within its
   own models (round-3 finding 3) — and `docs/PRD.md` / `docs/architecture.md`'s tier clauses are
   neutralized the same way; `.claude-plugin/marketplace.json`'s description names both harnesses. The CI sweep (item 5)
   covers all of these.
5. **CI gates**: the Codex-branch gate's three cases become two (any-dir delivery → forced-read
   sentinel present; no-vars → warning); the harness-page byte gate tightens to 4096; the static
   assertions swap targets AND widen their scan set (round-1 blocker 2): the negative sweep (no
   "never the main session", no `codex-adopt`/`.devstandard` references, no "Codex executor"
   identity wording) covers `core.md`, `reference/`, `README.md`, `docs/architecture.md`,
   **`CLAUDE.md`, `docs/PRD.md`, and both plugin manifests**; the negative identity sweep also covers
   **`hooks/session-start` itself, root `AGENTS.md`, and all three manifests**; **retirement is
   asserted, not assumed** (round-4 finding 4): `.devstandard` and `scripts/codex-adopt` do not
   exist; the role sentinel is absent from `AGENTS.md` (this repo is hook-capable — its v0.27 block
   is removed outright in this diff); `/.claude/worktrees/` remains in this repo's `.gitignore`;
   the fallback snippet names the forced reads; the relocated placement guard and every
   pre-creation trigger are present. The positive assertions are enumerated in full (round-3
   finding 5): the memory-flip and dispatch-default lines; the `.codex-plugin` description says the
   full method; the Codex-branch gate's sentinel is the forced-read instruction; README's
   Requirements names Codex; `docs/PRD.md` carries the neutral definition; **both** marketplace
   descriptions name both harnesses; **every amended ADR's status carries its 0039 entry and its
   dated block exists** (0006/0007/0008/0015/0016/0018/0019/0024/0038 — the index checker
   validates blocks that exist but cannot see an omitted one, so presence is asserted per ADR);
   and **every worktree-ignore site is asserted present** — ci-pipelines' full-setup seeding,
   worktree-lifecycle's Birth trigger, core.md's dispatch-lane trigger, external-agent's dispatch
   steps, and worker-brief's self-creation lane; and **the two harness-specific footprints are asserted
   positively** — Claude: `core.md`; Codex: `core.md` plus the mappings page (round-6 finding 4).
6. **ADR 0039** — *"Codex runs the method; worker constraints ride the dispatch"*. **The
   relationship is an amendment, not a supersession** (round-1 blocker 4; `reference/adr.md`:
   partial change = amend): **0039's own status enumerates every ADR it amends** (round-3 finding 4):
   `Amends 0038 (identity and scoping; the measured delivery mechanics stand), 0006, 0007, 0008,
   0015, 0016, 0018, 0019, and 0024 (each: the Codex-role / Claude-only clause corrected or
   scoped)` — **0016** ("assumes Claude Code installed alongside") is scoped to "a supported
   harness — Claude Code or Codex", superpowers decision intact; **0006** ("the Workflow tool is
   the harness") is generalized to harness-native orchestration; **0008** joins because it receives
   a dated block; 0038's status gains `Amended by 0039 (2026-08-26)` plus the dated block — its
   original body stays untouched. **And the operative amendments on 0007, 0019, and 0018 are
   themselves now false** (each says the Codex branch delivers the worker role / calls Codex a
   worker): each gets a further dated `(2026-08-26, see 0039)` block correcting the clause, with
   matching status entries. The 0036 amendment (dispatch default) survives as written. ADR 0039
   also states, once, the added always-read cost on the Codex side (the headroom carve-out permits
   it in the ADR that makes the argument) and carries the v0.27 migration note.
7. **`docs/architecture.md` + `README`** — the collaboration framing replaces the identity
   framing, **including the two named mirrors** (round-5 finding 3): README's "a main session
   (you + Claude)" bullet and `docs/architecture.md` §4's "persistent main session (human +
   Claude)" become harness-neutral, and Decision 5's negative patterns gain `human + Claude`
   and `you + Claude` as main-session definitions, plus the resolver stems `if unsure whether` and
   `one ongoing primary session` (round-6 finding 1);
   the Codex install section drops adoption and gains "installs like the Claude side: plugin +
   one-time trust, active everywhere".

## Out of scope

The Claude-side delivery (byte-identical throughout); the discriminator and its requalification
trigger; ADR 0036's executor mechanics; every protocol (the two checks, who merges, dispatch and
worktree mechanics) — identity-resolution TEXT is in scope for every harness, protocols are not;
any claim about which harness reviews or executes better.

## Verification

1. **Claude branch byte-identical** to main's hook output (diffed, pinned env) — as every round.
2. **Codex delivery, real path** — split per round-4 finding 5 (measured: `codex exec` refuses a
   non-git directory without `--skip-git-repo-check`): (a) a flag-less run inside an ordinary git
   repo and (b) a non-git directory run with `--skip-git-repo-check`. Both are **causal and
   ordering-decisive** (round-7): clean fixtures with no other instruction source (no `AGENTS.md`);
   a neutral prompt naming neither DevStandard file but requiring one harmless target-file
   operation; the captured `--json` transcript must show both complete plugin pages read **before
   the target operation and before the answer** — a single combined read command counts. The
   no-vars run still warns.
3. **The dispatch still constrains — capability-controlled, gate-compliant** (round-1 blocker 5):
   the control must be a merge the method itself would allow, or refusal proves nothing. Both
   scratch GitHub repos get: a green mergeable PR (a trivial always-pass workflow so check 2 is
   real), a fresh check-1 verdict posted on the PR for the exact head SHA (produced by a separate
   `codex exec -s read-only` reviewer), and the probe carries explicit human authorization.
   *Control* (no brief): "both checks are green and the human authorizes — merge PR #1" →
   **merges** (an undispatched session is a main session and may). *Test — the refusal must name the brief's merge
   prohibition in its output* (round-3 finding 6): identical setup + a **completely
   filled** worker brief (exact issue/branch/worktree fields — no placeholders), the worker
   launched **at its issue-recorded linked-worktree root** with the required `.git` access, and its
   placement validation demonstrably passed (its output confirms it proceeded past "Before you
   write") — only then the same authorized merge probe → **refuses**, PR stays open, asserted on
   GitHub state. Any placeholder-stop or placement-stop is recorded as an invalid run, not a pass —
   the refusal must be attributable to the brief's NEVER list alone.
4. **Standalone Codex runs the method** — exact recipe (round-1 blocker 5; round-3 finding 6:
   the oracle must prove *who* produced the state): the top-level **ordinary git-repo Codex invocation (no `--skip-git-repo-check`) is
   itself captured** (`--json` event transcript), given **one initial task prompt and no procedural
   follow-ups**, and the transcript's command ordering is correlated with the GitHub artifacts —
   issue before branch, verdict and green CI before merge. A seeded scratch repo
   (README + trivial always-pass CI), the task "add file X with content Y" with a machine-judgeable
   done-check; the evidence chain, each link asserted on GitHub state: the **issue** exists (a
   human-raised task requires one); a branch + PR linked to it; a **separate fresh reviewer**
   (`codex exec -s read-only`, invocation and verdict captured, the verdict posted on the PR naming
   base/head SHAs); green CI on that head; **the done-check itself executed after the final
   edit/rebase with its evidence in the PR description** (asserted by reading the PR body); the
   merge only after both checks; and finally **the exact blob asserted on GitHub's merged `main`**
   — the PR's remote state is MERGED and `X` is read from `origin/main` after an explicit fetch
   (never a possibly-stale local ref) — issue-before-work and checks-before-merge ordering preserved
   throughout. Model compliance is the honest limit, stated as such.
5. **Repo gates** — the reshaped gate set passes; the widened negative sweep is clean; **the
   combined Codex always-read payload is measured and stated once in ADR 0039, both pages under the
   same token proxy** (words × 1.35; CI's operative caps stay the core.md token gate and the
   harness page's 4096-byte gate; the ADR carries the justification under ADR 0032).

## Failure detection & rollback

- **Detection**: V2's sentinel probe stays the delivery detector; the role regression this spec
  *removes* is itself the thing to watch inversely — the static assertions now fail if the identity
  language reappears.
- **Rollback**: the Codex branch's content swap is one hunk in the hook; the clause walk-backs are
  enumerated in item 4; the marker/adopter retirement is additive-in-reverse (restoring v0.27.0 =
  reverting this diff). The Claude path is untouched throughout.
