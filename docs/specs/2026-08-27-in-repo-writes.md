# Where each kind of file goes: a routing table, admissible documents, and the tree you hand back

Status: draft

*Items 1–10 were accepted 2026-08-28 after twenty-one challenge rounds, every round by a fresh read-only Codex run at
the standing setting; the last found nothing blocking; **items 11–15 are the human's scope correction and are in challenge now — they carry none of that acceptance.** Issue #168 carries the evidence survey and the
full record — every finding and its disposition, including three refused with reasoning and one split
out as #169. This page is the design.*

## Problem & context

ADR 0037 settles where a write goes when the target is **not** the repo. Inside it, `core.md`'s *"write
to the repo, to the scratch your session provides, or to a location a tool's convention or the repo's
`CLAUDE.md` names"* leaves *write to the repo* unqualified, so two moves have no rule: **an invented
document** (a `HANDOFF.md` carrying state for the next session; a method kind at an invented path — a
root `ARCHITECTURE.md` beside `docs/architecture.md` is two competing authorities) and **untracked
leftovers** (`worker-brief.md` asks the doer to read its own *diff*; an untracked file is not in the
diff, and is one `git add -A` from the record).

Surveyed on this human's machine (#168): three repos carry an agent-facing handoff document, two a
method kind at an invented path, four untracked leftovers — and this repo carried a shell-redirect
artifact at its root across several `git add -A` commits. ADR 0017 already gates two documents by
trigger; nothing generalises that to the set.

## Options considered

*(Rationale and rejected alternatives in full on #168.)*

1. **Two sibling pages, not one and not `core.md`** — `core.md` has no room, and a *fragment* of a
   predicate is worse than none; renaming `out-of-repo-writes.md` would land the reader about to hand
   back on a page about download caches (ADR 0031). One page for both halves was the first pass,
   overturned by counting act sites: most want one half only. Hence **`reference/in-repo-writes.md`**
   (documents) and **`reference/clean-handback.md`** (the tree you leave).
2. **ADR 0037's *invented* test applied to documentation**, each kind's trigger carried over — not a
   filename allowlist (fights `CONTRIBUTING.md`, translations, generated trees), not kind membership
   alone (ADR 0017 refuses an ADR no decision earned). It closes four laundering routes found in
   challenge: a stale `HANDOFF.md` licensing the next; an *established* handoff convention; a request
   the doer wrote itself; and a handoff cited as authority.
3. **Documentation, generated prose included**; excluded are non-document build output, code, genuine
   product or runtime config, fixtures, lockfiles, `.gitignore`. **Handoff and session-state artifacts
   are governed whatever their syntax** — `session-state.json` is the same message wearing another
   extension.
4. **The message goes to the issue or the PR**, never `CLAUDE.md`, whose fence this change tightens
   toward and never widens — which is also why an off-canonical document location is declared in
   `docs/architecture.md`'s generated pointer footer, not smuggled into `CLAUDE.md` as a "gotcha".
5. **Hygiene: baseline → delta → commit or remove → surface what you did not create → publish both
   snapshots.** Not *"delete the rest"* (a worktree carries copied-in `.env`, config, seeded data —
   ADR 0012). **Refused** (#168 r3): hashing the baseline — the contract is appearance, not content.
   **Split out** (#169): proving a fallback run sat on the merge result.
6. **What it can promise** — `-uall`; ignored paths are outside it; it guarantees exactly the risk,
   everything a later `git add -A` would commit. No CI gate is possible for that half (a clean checkout
   cannot see a leftover): an honest limit, the shape ADR 0019 and 0037 use. The document half needs
   none — an added file is in the diff.
7. **A CI assertion here**, dogfooding, contract stated as **path shape, never semantics**: over
   `git ls-files`, root Markdown is exactly `README.md`, `CLAUDE.md`, `core.md`; `docs/` holds only
   `PRD.md`, `architecture.md`, `architecture/`, `adr/`, `specs/`; `docs/adr/` only `NNNN-*.md`,
   `docs/specs/` only `YYYY-MM-DD-*.md`, `docs/architecture/` only `<subsystem>.md`. Markdown suffixes
   match case-insensitively, but an allowed path must be spelled exactly as canonical and be unique
   after case-folding. It catches a root `NOTES.md` and a `docs/adr/HANDOFF.md`; it does **not** catch a
   root `HANDOFF.txt` — **check 1 owns semantic admission**. Guards this repo only (ADR 0034).
8. **The version bump** rides its own PR after this one (#159/#164/#167 precedent).

## Decision

**1. `reference/in-repo-writes.md`** (new) — which documents may exist. Prose a person or an agent
reads, generated prose included. **This governs *adding* one.** Editing a document already tracked at
that exact path is ordinary work — an existing file licenses that path, never a second document
elsewhere — **except a handoff or session-state document, which must qualify whether or not its path is
tracked**: an inherited one is the defect, and updating it entrenches it. To add one:

- **a method kind whose own trigger fired.** The trigger is always required — arms 2 and 3 admit no ADR
  whose decision failed the admission test (ADR 0017) and no spec no change earned, however firmly an
  issue asks. **Trigger gating is separate from path selection**: where an adopted repo's established
  convention keeps the kind elsewhere (`docs/decisions/`), arm 2 supplies the *location* while arm 1
  supplies the *trigger*. Canonical paths are relative to the scope the lifecycle ran in (a monorepo
  subtree's `<subtree>/docs/PRD.md`). The kinds: `docs/PRD.md` and `docs/architecture.md` (setup or
  mini-setup); `docs/architecture/<subsystem>.md` (split-on-zoom); `docs/adr/NNNN-*.md` (the admission
  test); `docs/specs/YYYY-MM-DD-*.md` (a substantial change); the repo-root `CLAUDE.md` (a command,
  gotcha, copy-list line or record-language declaration, and only when there is one); and, in a
  hookless environment, the delivery block prepended to `AGENTS.md`/`AGENTS.override.md`. Reserved
  outright, admitting no substitute: that delivery block, and `CLAUDE.md`'s content fence. `README.md`
  is deliberately absent — the method triggers none — except as a **founding-scaffolder output**: what
  the scaffolder the accepted setup design names produces is the skeleton, not an invention. A
  scaffolder introduced later licenses nothing;
- **a kind an established convention of the base tree keeps, whose own creation condition has fired.**
  The *base tree* is the named pre-work base — `origin/main`; local `main`/HEAD with no remote; empty
  for founding setup — pinned at task start as `{CONVENTION_BASE_SHA}`. Files sharing purpose, location
  and naming that the base already shows, or one a tool **already in the base tree** maintains, *and*
  the condition that convention writes to (a release happened; the generator ran). Shape alone licenses
  nothing, or two release notes license an invented third. **One incidental file is not a convention.**
  **A convention whose condition is "a session ended" is the pattern this rule names** — being
  established does not launder it; raise it on the issue instead of extending it;
- **it was asked for, in writing, by someone whose word is authority** — the human, the main session,
  or the repo's pre-work record: the issue as the dispatcher wrote it; **the accepted spec at the
  version accepted**, its blob SHA published to the issue before dispatch and passed to check 1 (the
  worker edits that same file in its PR, so an unpinned "accepted spec" is a self-licensing lane); or a
  pre-existing document — **never a handoff or session-state artifact**, or a prior agent could write
  "please add X" into `HANDOFF.md` for the next worker to cite. **A doer editing or commenting on its
  own issue, or adding an authorisation to the spec, is escalation, not authority** — it counts once
  the main session approves it there. In a light start with neither issue nor remote there is no
  durable venue: the authority is the human's instruction in that session, disclosed with the handback,
  and that is the only lane where it suffices.

Never **two competing authorities at the same scope**. A marked translation naming the document it
follows (ADR 0023) and a split-on-zoom child linked from the overview are not competing. Everything
else is invented — and **an invented document is almost always a message wearing a filename**: a
handoff, a summary, a status note; the issue, the PR description, or a comment is where those go.
**"A session ended" or "work changed hands" is never sufficient under any arm**, nor by changing the
file's format. Raising it on the issue means putting the state *in* the issue, not commissioning a file
to hold it. One line each to `out-of-repo-writes.md` and `clean-handback.md`.

**1b. `reference/clean-handback.md`** (new) — the tree you leave. **Baseline before your first
task-generated write** — after any declared copy-in, before install, tests, or anything you produce —
whoever you are, worker or main session on a short branch; where the first act *creates* the repository,
the baseline is the **empty tree**, recorded as such. `git status --porcelain -uall`, kept in scratch
**and published immediately to the issue where there is one** (a session is mortal), otherwise in the
eventual PR or handback. An entry you cannot account for against the copy-list is named, not silently
inherited; **taking over without a baseline**, treat every current non-copy-list path as unaccounted-for
and name it. **Compare again after your last repository-touching command** — the final edit, the rebase,
*and the done-check run* — and **before every check-1 or re-review dispatch**; **publish both
snapshots**. Every path new since the baseline **and visible to that command** is **committed or
removed** — naming a leftover does not license leaving it, and `git worktree remove` refuses a dirty
worktree. Install and test artifacts land after the baseline deliberately: ignored, they never appear;
not ignored, they are yours to commit, ignore or remove. **Delete only what you created and know is
disposable; anything you did not create, or cannot account for, is named, never deleted — and it blocks
a clean handback until its owner says what becomes of it** (removal, commit, or deliberate retention):
the one path with no unilateral outcome, since the alternative is an agent deleting someone else's work
to make its own checklist pass (ADR 0012). Non-ignored copy-list inputs are removed at teardown only
after confirming the main checkout still holds them. The check compares what is *there*, not contents.

**2. `core.md`** — two insertions, neutral trigger plus pointer, no fragment of either predicate:
*write to the repo* gains "— and only what belongs there (`reference/in-repo-writes.md`)"; the doc-duty
sentence gains that a document you add is one that page admits, that a note for the next session belongs
in the issue or the PR, and — **before your first write, not only at handback** — that you snapshot the
tree and hand back one carrying nothing you did not mean (`reference/clean-handback.md`).

**3b. The canonical-path consumers.** `core.md`'s read-the-architecture-doc line and its
skim-the-decision-log line, `worker-brief.md`'s equivalent, `repo-claude-md.md`'s template footer,
`docs/architecture.md` §5 and `docs/PRD.md`'s doc-set sentence all name fixed paths. Each becomes
**canonical unless the architecture doc's pointer says otherwise** — the smallest possible change (in
`core.md`, a parenthetical), so a reader in an adopted repo follows the declaration instead of an
absent directory. The declaration itself lives in exactly one place, as Decision 3a says.

**3. Resident triggers, each carrying the trigger *and* the pointer, naming the half it needs** —
`worker-brief.md` (both), `worktree-lifecycle.md` (**Birth gains the baseline step**; Death's inventory
points at `clean-handback.md`), `driving-a-pr-green.md` ("Taking delivery"), `repo-claude-md.md`,
`out-of-repo-writes.md` (sibling lines), `harness-codex.md` (**the repo-root `CLAUDE.md` is read before
any repo work**, not only before setup — the off-canonical declaration and every canonical-path
consumer depend on it), `docs/architecture.md` (tree entries), `README.md` (**both** live inventories),
`docs/PRD.md`.

**3a. The four document-creation guides** — `prd.md`, `architecture.md`, `adr.md`, `design-spec.md` —
state their canonical paths as **defaults that yield to an established convention**, and
`architecture.md`'s generated footer (*"Decisions and their reasons: `docs/adr/`"*) is **parameterised**
to the location the repo uses, so an adopted repo neither grows a competing tree nor inherits a broken
pointer. That footer, in the shared reference every task reads, is where an off-canonical location is
declared. **`docs/architecture.md` itself and the repo-root `CLAUDE.md` stay canonical** — they are the
entry points a session must find with no pointer to guide it. `design-spec.md`'s Flow also records the
accepted spec's blob SHA to the issue before dispatch. **ADR 0017's amendment covers path selection as
well as trigger gating.**

**4. `reference/external-agent.md`** — its `-o <outfile>` creates exactly this kind of file, its example
runs `-C <worktree>`, and its command block reads a relative `brief.txt`. **Both brief and outfile live
in the dispatcher's session scratch, never the worktree**, read and removed best-effort, anything
durable posted to the issue or PR. The apparent conflict with `out-of-repo-writes.md` kind 3 dissolves
on measurement: **`-o` is written by the CLI on the dispatcher's side, not by the sandboxed agent** —
verified on codex-cli 0.149.1 under both sandboxes with `-C <worktree>` (#168). Both pages say which is
which.

**5. `reference/code-review-prompt.md`**, both sides of the fence. **Above it**: before commissioning
check 1 or any re-review, compare against your baseline and put both snapshots in the PR (a main
session's own short-branch PR never transfers, so "Taking delivery" never reaches it). **Inside**: the
Docs check gains a **`{IN_REPO_WRITES_PREDICATE}` placeholder** filled by mechanically extracting a
delimited block from the canonical page — the copied unit includes both markers, and the end marker
declares the payload line count, which CI asserts, so **unfilled, missing-marker or mismatched-count is
Critical**; subtler alteration is not something a reviewer without the source can catch, and the design
says so rather than pretending. Plus both bases as filled placeholders: `git diff --name-status
{REVIEW_BASE_SHA} {HEAD_SHA}` (additions, copies, moves, renames **and modifications**), and
`{CONVENTION_BASE_SHA}` with `git show {CONVENTION_BASE_SHA}:<path>` for provenance. **A third
placeholder, `{ACCEPTED_SPEC_BLOB_SHA}`**, carries the version the main session accepted, as `SHA` or
`NONE`. Where it is a SHA the reviewer **retrieves that blob with `git cat-file blob` and reads it as
the authority itself** — it does *not* compare it against the copy in the diff, which necessarily
differs: `reference/design-spec.md` has the implementation PR flip `Status: accepted` to `committed`,
so a byte comparison would false-fail every ordinary review. Reading the accepted blob is also what
stops the worker's edited copy standing in as authority, which was the point. The dispatcher ensures
the blob is **reachable in the repository the reviewer reads** before publishing its SHA, and the
reviewer checks the filled SHA against the one published on the issue — **a mismatch is Critical**. `NONE` is
valid only when no document is admitted on "the accepted spec" — a task with no spec is the ordinary
case. **An unfilled placeholder, an unreachable blob, or a document admitted on a spec while `NONE` is
filled, is Critical.** **Licensing looks at the pinned base; competing-authority collision looks at what the merge
will contain** — `{REVIEW_BASE_SHA}`, the head, and the other candidates — or an authority added
upstream after task start and one added here merge unseen. Provenance maps onto the three artifacts: the
requirements slot carries the issue and the accepted spec, the report slot the **complete PR
description**. A document passing no arm, or competing at the same scope, is an **Important** finding.

**6. Five sites tightened to `CLAUDE.md`'s fence** — `core.md`'s doc duty, `repo-claude-md.md`'s
write-back sentence, `worktree-lifecycle.md` Death 2 ("a command, gotcha, or **rule**"), plus
`worker-brief.md` and `harness-codex.md` ("your own operational discoveries"). All five name the fence's
kinds. The fence itself is unchanged.

**7. `reference/ci-cannot-run.md`** — its audit item asks for an *empty* `git status --porcelain`, which
a clean worktree fails whenever the copy-list put a non-ignored file in it. It becomes: **tracked state
clean before the run** (`git diff --quiet`, `git diff --cached --quiet`), **permitted untracked inputs
enumerated — paths already on the pre-run baseline *and* named by the copy-list, never an invented
fixture**, then **`-uall` snapshots before and after compared**; ignored paths are invisible to all of
it, so an ignored input the run depends on is named in the block. (Whether the run sat on the merge
result is #169.)

**8. ADR 0041** (reserved on #168; re-verified against all four sources at write time, evidence in the
PR). Dated amendments: **0012** (pre-handback cleanup versus Death's surface-never-eat backstop),
**0017** (trigger gating *and* path selection now govern every kind), **0018** (its write-back invites a
*rule* into `CLAUDE.md`). ADR 0037 cleared — decision unchanged; its page carries the sibling pointer
and the `-o` distinction.

**9. `.github/workflows/ci.yml`** — option 7's assertion, in the invariants step, contract in a comment.

**10. The unconditional-doc-set sites** — `README.md`'s adopt-an-existing-project answer licenses the
whole set *"when you are ready"*, bypassing the triggers; it gains the trigger framing and the pointer.
That answer, plus README's project-memory bullet, full-lifecycle bullet and Starting-something-new
walkthrough, and `docs/PRD.md`'s full-suite bullet, promise a repo-root `CLAUDE.md` unconditionally
while `repo-claude-md.md` generates it **only when there is something to put in it**: each gains the
condition.

**Cleared with reasoning:** `docs/adr/0000-record-architecture-decisions.md`'s canonical ADR path (this
repository's own, where it is correct); `reference/ci-pipelines.md` (conditional trigger and two-hop pointer already
correct); ADR 0030 and this repository's own root `CLAUDE.md` (0030 rules them outside the method);
`docs/architecture.md` §5 (what a *target* project receives).

**11. `reference/where-it-goes.md`** (new, small) — the placement table, and the family's entry point.
Not a *router* in ADR 0007's sense (that ADR rejects an always-on dispatcher that routes requests or
skills); this is a lookup a reader opens with a file in hand. **ADR 0007 gains a dated amendment**
qualifying its ruling, and `README.md`, `docs/architecture.md` and `docs/PRD.md` — which repeat "no
router" as a live claim — say which kind of router is refused.

**No rename of `out-of-repo-writes.md`**: making it the table loses on ADR 0031's granularity rule —
the table is consulted on nearly every task, the out-of-repo procedure rarely — and keeping the names
removes the rename's whole sweep. Its three kinds stay exactly where they are.

**Keyed by role and lifetime, first match wins**, because nouns overlap:

1. **Tracked product material that is not a document** — source, configuration the product ships, a
   fixture committed as an input, an asset it serves. → the repo, where its own structure puts it.
2. **Maintained documentation** — prose the repo keeps, not merely output a human can read. →
   `reference/in-repo-writes.md`.
3. **Untracked local configuration or secrets the task needs** — `.env.local`, a key, seeded data
   the repo expects. **Not** anything fetched, which is row 9, and not a running service's state,
   which is row 10. → **never committed**; the worktree copy-list's business
   (`worktree-lifecycle.md` Birth 4), at the location the repo declares or the tool documents; where
   neither names one, it is a stop-and-tell (a worker) or an ask (the main session), like any other
   unnamed location.
4. **Tool-managed working output inside the worktree** — `node_modules/`, `.venv/`, `.pytest_cache/`,
   a build directory the tool requires. → the ignored location that tool owns, where the base tree
   already shows it or the tool genuinely requires it; never an agent-chosen one.
5. **Dies with the task** — agent-chosen intermediates, a report read once, a dispatched process's
   output file. → the scratch your session provides, or one `mktemp -d`; a process-invoked agent
   confined to its own disposable worktree may use a gitignored directory in it
   (`out-of-repo-writes.md` kind 3, and only that case).
6. **Something you show someone** — a screenshot, a coverage summary, a benchmark number. → made in
   scratch and **published** to the issue or PR; where a light start has neither, the conversation or
   an explicit handback is the channel (`out-of-repo-writes.md` kind 3 already says the repo and the
   Desktop are not).
7. **A release deliverable** — a wheel, an installer, a container image, a release archive. → the
   repo's release and publishing convention (`reference/ci-pipelines.md`). Never committed as a
   by-product, and never merely attached to an issue.
8. **Generated data, an artifact or a log you must keep** — and not a fetched reusable (row 9) or a
   service's live state (row 10). → item 12.
9. **Fetched and reusable across tasks** — model weights, a venv you share, a cloned tool. →
   `out-of-repo-writes.md` kind 1.
10. **Mutable state a running service owns** → `out-of-repo-writes.md` kind 2, declared before
    anything lands there.

First-match ordering is what resolves the overlaps, and the rows are written so the order is safe:
product documentation is row 2, not row 1, because row 1 excludes documents; a coverage report is
row 6, not row 2, because row 2 is *maintained* documentation; `.env.local` is row 3, never row 1;
`.pytest_cache/` is row 4, not row 5, so it does not fight `clean-handback.md`'s post-baseline
artifacts; a runtime-generated fixture is row 5 unless committed as an input, when it is row 1; a
local service's SQLite file is row 10.

**12. The kind with no rule today — generated data, artifacts and logs you must keep.** In order,
first match wins:

- **a location established in the base tree** — *tracked* evidence at `{CONVENTION_BASE_SHA}`: a
  directory already holding same-purpose files, or a tool configuration the base owns that names it.
  **Not** the current working tree, **not** an ignore entry this task added, **not** a
  non-location-bearing pattern like `*.log`, and **not** one incidental artifact an earlier agent
  left — the self-licensing route items 1–10 closed, in its filesystem form;
- else **a tool's own documented default, when it is a real location** — `~/.cache/huggingface` is;
  a relative path resolving against the current directory selects nothing and does not count;
- else **a path the repo's `CLAUDE.md` already carries** inside an admitted command or gotcha — never
  a new placement section, which would widen the fence this change tightens;
- else **stop and tell the main session** (a worker) or **ask the human** (the main session). The
  answer becomes authority once **the human or the main session** writes it to the issue or the PR —
  **a doer's own comment is escalation, not approval**, the same lane items 1–10 already define. Item
  15's reviewer rule names these same lanes and no others.

Never an invented directory — in the repo root or under `$HOME`. **The destination must outlive the
task**: a gitignored path inside a disposable worktree is not a home for something you must keep,
because teardown destroys it silently — commit it (row 1), publish it (rows 6–7), or use a declared
persistent root. Two boundaries: **mutable state a service keeps running is row 10**, declared before
anything lands there; and a **durable artifact that belongs to the product is row 1 or row 7**, not
this one. "Outlives the task" alone does not make something a deploy root.

**13. `core.md` carries the answer, not only a pointer** — the human's direction, 2026-08-28: *part of
it can live in `core.md`, and the rest points at the detail file.*

A reader holding a file and asking where it goes has no resident sentence keyed to **their** question:
the placement rule rides inside the *stay in your own repo* paragraph, whose subject is cross-repo
edits, and points outward for everything. That is the likeliest reason a shipped rule did not land
(#168). `core.md` therefore gains the **short answer**, one clause per destination group, with the
table keeping the ordering and the edge cases.

**Exactly what changes, so no implementer removes the wrong thing:**

- **replaced, and lifted out of that paragraph** — the answer is its **own paragraph, opening with the
  placement question**, because leaving it inside the cross-repo paragraph is exactly the burial item
  13 diagnoses, and every keyword assertion would still pass. Replaced: the sentence beginning *"The
  same holds for the filesystem between repos:"* through
  *"(`reference/out-of-repo-writes.md`)."* (83 words), by the resident answer: the question; product →
  the repo; **maintained** documentation → what `in-repo-writes.md` admits, while prose that is temporary or
  merely shown is routed by lifetime like anything else; local config and tool-owned output → where the
  repo or the tool already puts them, ignored; dies with the task or shown to someone → scratch, and
  published to the issue or PR; kept output, a release, a download, or a service's state → only where
  the base tree, the tool's default, or the repo's docs already name it, and nothing named is a
  stop-and-tell (a worker) or an ask (the main session); **never invent a place, in the repo root or
  under `$HOME`**; the pointer;
- **removed as redundant** — exactly the clause *"add only a document `reference/in-repo-writes.md`
  admits; "* from the doc/tree duty, which the resident answer now states. Nothing else is removed,
  and every rule the old sentence carried has a resident home in the new one;
- **added** — `core.md`'s ask-axis gains the case this rule creates: a durable location that nothing
  names. Its list is exclusive, so without this the main session's own ask is forbidden.

**`$HOME` is not forbidden; an *invented* place under it is** — a tool's documented cache and a path
the human or the repo declared stay legitimate. Cost is measured on the head by the page's own gate,
quoted in the PR and re-run after any wording change.

**14. `reference/worker-brief.md`** — workers receive the brief, not `core.md`, so the rule cannot
reach them by `core.md` alone. Its placement bullet currently reads *"add only documentation admitted by
`reference/in-repo-writes.md`; otherwise use the repo, your session's scratch … or a location a tool's
convention or the repo's `CLAUDE.md` names"* — which routes everything non-document to "the repo" and
carries no pointer to the table: it gains the same resident answer in brief form and the pointer, and its stop list gains
**durable generated output with nowhere named for it** alongside the download/environment/deploy case
already there.

**15. The reviewer fence gains a generated-output trigger.** Any **code or configuration in the diff
that selects a destination** — application source, logging or test configuration, a Docker Compose or
service file, a script, a Makefile, a CI step — is invisible today unless it writes outside the repo.
A path supplied by the caller is not the change's choice and is out of scope. The fence gains: for a
destination this change selects, apply the placement table's branch — established in
`{CONVENTION_BASE_SHA}`, a real tool default, or authority that existed before this work or was
approved in the issue. **A mention added by this same diff licenses nothing**, and a caller-supplied
path is not the change's choice. An invented destination is an **Important** finding.

**16b. `reference/out-of-repo-writes.md`** — it presents three *exhaustive* kinds, but item 12 can
send durable generated output outside the repo, which fits none of them, and its disclosure rule
covers only kinds 1–2. Its opening says the three kinds are the ones **it** governs and points
durable generated output at the table; its disclosure rule extends to **any external destination
chosen under row 8**, named in the PR like the rest. Nothing else on the page moves.

**16c. `reference/clean-handback.md`** — the hole this addition would otherwise open: the page treats
ignored paths as outside `-uall` and outside its promise, while item 12 relies on *rejecting* a
must-keep artifact placed in an ignored path inside a disposable worktree. `git status -uall` is clean
right up to the `git worktree remove` that destroys it. So a **retention check before teardown**:
anything you were told to keep must already live where it survives the worktree — committed,
published, or at a declared persistent root — and the worktree lifecycle's Death step carries the
trigger and the pointer, not only the table.

**16. The sweep the addition owns.** `out-of-repo-writes.md` keeps its name, so no pointer moves and
ADR 0018's route stays correct. **ADR 0037** gains a dated amendment: its Decision records that
`core.md`'s *"Stay in your own repo"* bullet carries the trigger — now false. **ADR 0007** gains one
qualifying "no router". `README.md`'s two inventories and its no-router line, `docs/architecture.md`'s
tree entry and its no-router line, `docs/PRD.md`'s no-router line, and this spec's own earlier
references gain the table. `docs/PRD.md`'s product summary and feature list, and README's *What you
get*, gain the placement capability itself — role-and-lifetime routing for every file, not only
documents and handback. `reference/in-repo-writes.md`'s footer, which routes only to out-of-repo
writes and clean handback, gains *"for deciding what kind this file is"* → the table. The abandoned specs and historical Consequences lines are **history,
explicitly cleared**.

## Out of scope

ADR 0037's three out-of-repo kinds themselves — they stay in `out-of-repo-writes.md`, unmoved and unrewritten; what each document *contains*; `CLAUDE.md`'s fence (tightened toward,
never widened); a gate on untracked files (impossible); ignored paths and file contents; what the
CI-fallback certifies (#169); the manifests; the human's other repos (#168 surveyed them — fixing a
neighbour is what "Stay in your own repo" forbids).

## Verification

**On the head, each a command whose exit code decides it:**

- every existing CI gate green, quoted with its own output;
- **the new assertion passes, fires on every negative control, stays green on the positive control, and
  leaves the tree as it found it.** Negatives: root `NOTES.md`; `docs/HANDOFF.md`;
  `docs/adr/HANDOFF.md`; root `HANDOFF.MD` (suffix case); `ReadMe.MD` beside `README.md` (case-folded
  duplicate); `DOCS/adr/0041-x.md` (directory case); a case-only rename of `README.md` to `README.MD`,
  restored byte-for-byte; **two otherwise-valid split-on-zoom children differing only by case
  (`docs/architecture/api.md` and `.../API.md`) — the uniqueness control, since `ReadMe.MD` fails the
  exact root allowlist even where case-folded uniqueness was never implemented**; a truncated predicate block; a root `ARCHITECTURE.md` while
  `docs/architecture.md` exists. Positive: a valid `docs/architecture/<subsystem>.md`, which must stay
  green — a checker rejecting every split-on-zoom child would otherwise pass every negative. Each control is
  created, `git add`ed, the checker run, then unstaged **and deleted**, with
  `git status --porcelain -uall` matching the pre-control snapshot;
- **every Decision site asserted inside its own section slice, both trigger wording and pointer** —
  enumerated, not sampled: `core.md`'s **resident placement answer** (each destination group present,
  the never-invent clause, the pointer) and its widened ask-axis; the doc/tree duty with exactly the
  named clause gone and nothing else; **all three** new pages' sections, including the placement
  table's ten rows and item 12's four-step ladder with its outlive-the-task requirement;
  `worker-brief.md`'s placement bullet, pointer and extended stop trigger; the reviewer fence's
  generated-output trigger with its same-diff-licenses-nothing clause; the no-router qualification in
  `README.md`, `docs/architecture.md` and `docs/PRD.md`; **the resident answer standing as its own
  paragraph whose first sentence is the placement question**, not folded back into the cross-repo one;
  `out-of-repo-writes.md`'s qualified opening and widened disclosure; `clean-handback.md`'s and the
  lifecycle Death step's retention check;
  `worker-brief.md`'s bullets and Done; `worktree-lifecycle.md`'s Birth baseline step and Death
  inventory; `driving-a-pr-green.md`'s *Taking delivery*; `repo-claude-md.md`'s write-back sentence;
  `out-of-repo-writes.md`'s sibling lines; `external-agent.md`'s output-channel paragraph;
  **`harness-codex.md`'s "before any repo work" timing** (not merely its tightened write-back); the four
  creation guides' yields-to-convention wording and `architecture.md`'s parameterised footer; **the six
  canonical-path consumers' "unless the architecture doc points elsewhere" wording**;
  `design-spec.md`'s blob-SHA step; the reviewer prompt **above and inside** its fence; the tree entries;
  README's **two** inventories; `docs/PRD.md`;
- the five tightened sites and the five conditional-`CLAUDE.md` sites carry their new wording; the
  reviewer fence names the `M` case, both scratch paths, both base placeholders (**present and
  separately filled; equal values are legitimate, so identity is never asserted**),
  **`{ACCEPTED_SPEC_BLOB_SHA}` present and filled (`SHA`/`NONE`), with the
  read-the-blob-as-authority wording, the reachability duty, and the Critical cases**, and the unfilled/missing-marker/line-count rule; **CI asserts the declared line count matches the block**;
- ADR 0041 present and indexed; the intended dated blocks and matching status entries asserted by name
  in **0007, 0012, 0017, 0018 and 0037**; all five verified append-only by the Status-block-stripped
  byte-prefix check against `origin/main`;
- **negative boundaries for the addition**, each a case the table must route the stated way and not
  another: `.env.local` (row 3, never row 1), `.pytest_cache/` (row 4, never row 5), a coverage report
  (row 6, never row 2), a release archive (row 7, never row 1 or 8), a kept log with nothing naming a
  location (item 12's stop-and-ask, never an invented `logs/`), and a must-keep artifact offered a
  gitignored worktree path (rejected — the destination must outlive the task); a downloaded model
  (row 9, never row 3); a shared venv (row 9, never row 8); a service's SQLite file (row 10, never row
  8); and a must-keep artifact still sitting in a worktree at teardown (the retention check fires).

**Process, not head state:** check 1's verdict is posted whole — the comment opens with the prescribed
`## Merge check 1 — round N` heading **and contains the reviewer's raw output verbatim** (the heading is
prepended by the poster, so whole-comment byte equality is the wrong test), with the reviewer line
naming the current head SHA.

## Failure detection & rollback

**Detection** — the assertion goes red or its allowlist is edited with no reason; a merged PR adds a
document passing no arm and check 1 did not raise it; a handoff document appears, or an inherited one
keeps being updated; a worker hands back a tree with unaccounted-for paths or without its snapshots;
**the hygiene rule deletes something it should have surfaced** (the failure option 5 exists to prevent);
a dispatched run's brief or outfile is found inside a worktree. **For the addition:** an invented
directory appears under `$HOME` or a repo root after this ships; a must-keep artifact is lost to a
worktree teardown; a diff licenses its own output path by adding a mention; the placement table sends
two readers of the same file to different rows. Each is an issue against this spec.

**Rollback** — prose: a revert PR restores the previous wording and deletes **all three** new pages,
the placement table included; `out-of-repo-writes.md` needs nothing undone, since it never moved. ADR
0041 is superseded rather than rewritten, and 0007/0012/0017/0018/0037 gain further dated blocks
pointing there; the CI assertion reverts with the pages. No data, schema, or install state is involved.
