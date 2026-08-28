# Where each kind of file goes: a routing table, admissible documents, and the tree you hand back

Status: draft

*Items 1–10 were accepted 2026-08-28 after twenty-one challenge rounds, every round by a fresh read-only Codex run at
the standing setting; the last found nothing blocking; **items 11–17 are the human's scope correction and are in challenge now — they carry none of that acceptance.** Issue #168 carries the evidence survey and the
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

**Keyed by role and lifetime. The rows are evaluated in order and the first that fits decides** —
there is no second precedence rule to reconcile with the numbering, because **the order *is* the
precedence**: identity first, then release, shown, kept, reusable, service state, and only then the
mechanisms that produced the file. How a file was produced never outranks what it is for.

1. **Tracked repository material that is not a document** — source; configuration the product ships
   *and* the repo's own (CI, build, lint, `.gitignore`, editor or devcontainer files); lockfiles; a
   fixture committed as an input; an asset it serves. → the repo, where its own structure puts it.
2. **Maintained documentation** — prose the repo keeps, not merely output a human can read. →
   `reference/in-repo-writes.md`.
3. **Untracked local configuration or secrets the task needs** — `.env.local`, a key, seeded data the
   repo expects. → **never committed**; the worktree copy-list's business
   (`worktree-lifecycle.md` Birth 4), at the location the repo declares or the tool documents; where
   neither names one, a stop-and-tell (a worker) or an ask (the main session). Anything the task *generates* here that must survive the worktree: **a credential stays in this row** — the tool's own secure store, or a declared persistent location — and only *other* generated local config moves to row 6's ladder. Neither ever goes to row 5, which shares. The retention check before teardown (item 16c) covers both.
4. **A release deliverable** — a wheel, an installer, a container image, a release archive. → the
   repo's release and publishing convention (`reference/ci-pipelines.md`). Never committed as a
   by-product, and never merely attached to an issue. It stays this row even when someone also looks
   at it.
5. **Something you show someone** — a screenshot, a coverage summary, a benchmark number. → made in
   scratch and shared **only through a channel that is both safe and available**: the issue or PR when
   the artifact carries nothing sensitive and the channel can carry it; redacted first where it can
   be; otherwise a channel the human approved, or an ask. Where a light start has neither issue nor
   PR, the conversation or an explicit handback is the channel.
6. **Generated data, an artifact or a log you must keep** — not a release (row 4), not reusable
   tooling material (row 7), not a service's persistent state (row 8). → item 12's ladder. **A
   destination outside the repo is named in the PR, or at explicit handback where no PR exists**
   (`out-of-repo-writes.md`, "Say where you wrote").
7. **Reusable, non-secret, tool-managed material that outlives the task** — fetched *or* generated:
   model weights, a shared venv, a cloned tool, a `ccache` or Gradle cache. →
   `out-of-repo-writes.md` kind 1 and the tool's own cache. A one-off fetch is row 10; a fetched
   credential is row 3.
8. **Mutable state a service owns and that is meant to persist with it** → `out-of-repo-writes.md`
   kind 2, declared before anything lands there. A disposable local or test service's state is not
   this row — it is row 9 if the tool owns the location, row 10 if it dies with the task.
9. **Tool-managed working output inside the worktree** — `node_modules/`, `.venv/`, `.pytest_cache/`,
   a build directory the tool requires. → the ignored location that tool owns, where the base tree
   already shows it or the tool genuinely requires it; never an agent-chosen one.
10. **Dies with the task** — agent-chosen intermediates, a report read once, a dispatched process's
    output file. → the scratch your session provides, or one `mktemp -d`; a process-invoked agent
    confined to its own disposable worktree may use a gitignored directory in it
    (`out-of-repo-writes.md` kind 3, and only that case).

Reading the order downward is what resolves every case challenge raised: a release archive someone
also views is row 4, not row 5; a coverage report a tool wrote is row 5, not row 9; a log a tool wrote
that must survive is row 6, not row 9; a `.pytest_cache/` is row 9, not row 10; a runtime-generated
fixture is row 10 unless committed as an input, when it is row 1; a disposable test service's SQLite
file is row 9 or 10, never row 8.

**12. The kind with no rule today — generated data, artifacts and logs you must keep.** In order,
first match wins:

**The ladder is the four-arm clause below, in that order** — it is not restated in different words
here, which is how the two drifted apart in the first place. Under each arm, the qualification that
arm needs:

- **(a) base-owned code or configuration that writes there** — *tracked* at `{CONVENTION_BASE_SHA}`.
  **Not** the current working tree, **not** an ignore entry this task added, **not** a
  non-location-bearing pattern like `*.log`, and **not** artifacts an earlier agent left, however
  many: two files under an invented `logs/` establish nothing, because **count is not intent**. A
  directory of same-purpose files qualifies only where the base tree shows its purpose, naming and
  creation condition independently of the artifacts themselves;
- **(b) the tool's documented default, when it is a real location** — `~/.cache/huggingface` is; a
  relative path resolving against the current directory selects nothing;
- **(c) the repo's own documentation as it stood before this work** — including a retained-output root
  carried as an admitted `CLAUDE.md` gotcha (item 16g), never a new placement section;
- **(d) a human decision recorded before the write.** Once the ask fires there must already be a venue
  to record it in: **the issue, or a comment on an already-open PR** — the eventual PR *description*
  is written after the work and is not prior authority — or, in a light start with neither, the
  conversation, disclosed at handback;
- and where none of the four holds: **stop and tell the main session** (a worker) or **ask the human**
  (the main session), which is how arm (d) comes to exist rather than a fifth arm.

**The row-6 authority ladder — exactly one counted, delimited block, and no other statement of it
anywhere.** The preliminary bullets and the loose quotation that used to sit around it are gone: three
versions is how the earlier drafts drifted. The block below is what `reference/where-it-goes.md`
carries, what the reviewer fence receives verbatim, and what CI asserts byte-equal between the two;
its end marker declares its payload line count, so a truncated or reworded paste is detectable by a
reviewer holding no copy of the source.

```
<!-- BEGIN ROW-6 AUTHORITY LADDER -->
A destination for retained generated output takes the FIRST of these that applies, and in every case
it must outlive the task — a gitignored path inside a disposable worktree is never one:
(a) base-owned code or configuration, tracked at the pinned convention base, that writes there — not
    the current tree, not an ignore entry this task added, not a pattern like *.log, and not artifacts
    an earlier agent left, however many; count is not intent;
(b) the tool's documented default, when it is a real location and BOTH the tool and that default
    predate this work or are documented upstream — a relative path resolving against the current
    directory selects nothing, and a tool this diff introduces cannot supply its own default;
(c) the repo's own documentation as it stood before this work, including a retained-output root
    carried as an admitted CLAUDE.md gotcha;
(d) a human decision recorded before the write, in a venue that already exists: the issue, or a
    comment on an already-open PR; where a light start has neither, the conversation, disclosed at
    handback. A doer's own comment or edit is escalation, not approval — including when the doer is
    the main session on its own short branch.
No arm applies: stop and tell the main session (a worker) or ask the human (the main session). Do not
write first and record after.
<!-- END ROW-6 AUTHORITY LADDER (16 payload lines) -->
```

Arms (b) and (c) both say *before this work* for the same reason: otherwise the diff that invents
`outputs/` licenses itself, either by adding a line to `README.md` or by shipping a script whose own
default points there. The four arms are the whole of it — the floor `core.md` states is a summary of
them, not a fifth arm.
Two boundaries the wording must carry, both found in challenge: the last arm is *a human's decision
that a session records*, never a session's own conclusion written down — **a doer's unilateral text is
escalation, not approval, and that holds when the doer is the main session on its own short branch**;
and where a light start has neither issue nor PR, the decision is taken in the conversation and
disclosed at handback, the only lane where nothing durable exists. **This clause governs row 6 only** —
rows 4, 7 and 8 keep the rules they already have, and the resident answer states the common floor
without collapsing them into one ladder.

Never an invented directory — in the repo root or under `$HOME`. **The destination must outlive the
task**: a gitignored path inside a disposable worktree is not a home for something you must keep,
because teardown destroys it silently — commit it (row 1), publish it (rows 6–7), or use a declared
persistent root. Two boundaries: **mutable state a service keeps running is row 8**, declared before
anything lands there; and a **durable artifact that belongs to the product is row 1 or row 4**, not
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
  placement question** (the exact prose is fixed below, and measured), because leaving it inside the cross-repo paragraph is exactly the burial item
  13 diagnoses, and every keyword assertion would still pass. Replaced: the sentence beginning *"The
  same holds for the filesystem between repos:"* through
  *"(`reference/out-of-repo-writes.md`)."* (83 words), by the resident answer: the question; product →
  the repo; **maintained** documentation → what `in-repo-writes.md` admits, while prose that is temporary or
  merely shown is routed by lifetime like anything else; local config and tool-owned output → where the
  repo or the tool already puts them, ignored; dies with the task or shown to someone → scratch, and
  published to the issue or PR; kept output, a release, a download, or a service's state → only where
  the base tree, the tool's default, or the repo's docs already name it, and nothing named is a
  stop-and-tell (a worker) or an ask (the main session); **never invent a place, in the repo root or
  under `$HOME`**; **and any write outside the repo is named in the PR** — the obligation the replaced
  sentence carried, which has no other resident home; the pointer;
**The resident paragraph, verbatim** — drafted and measured before implementation, because the page is
close enough to its ceiling that requirements alone would have left an implementer guessing (the
figure belongs in ADR 0042 and the live gate output in the PR, not here):

> **Every file you create has a place; name what it is, then put it there** — tracked material in the
> repo where its structure puts it, maintained documentation only where `reference/in-repo-writes.md`
> admits it, anything that dies with the task in your session's scratch, anything shown to someone
> made there and shared only through a safe, available channel. **Kept output, a release, a download,
> a service's state: only where something that predates this change already names the place, or a
> human decided before you wrote** — nothing named is a stop-and-tell or an ask. Local config, tool
> output and the rest: the table routes them. **Never invent a place, in the repo root or under
> `$HOME`**; name any durable write outside the repo in the PR, or at handback where there is none
> (`reference/where-it-goes.md`).

**The floor is anchored, not loose.** *Predates this change* and *a human decided before you wrote*
are the two arms that matter at the always-on level: without them a same-diff script or `README` line
licenses its own invented directory before a reader ever opens the table. Local config and tool output
are routed by the table rather than restated here — the page has no room for both, and those two rows
misroute nothing dangerous. *Durable* is load-bearing in the last clause: `out-of-repo-writes.md` asks for scratch disclosure
only when its contents matter, so an unqualified duty would make every ordinary `mktemp -d` a PR
entry. *Maintained* is load-bearing too — temporary or shown prose is routed by lifetime, not through
document admission. The paragraph states the **floor** the four durable kinds share — *only where something already names the place* —
and leaves each kind's own rule to the table, rather than applying row 6's ladder to releases,
downloads and service state, which would weaken all three.

- **removed as redundant** — exactly the clause *"add only a document `reference/in-repo-writes.md`
  admits; "* from the doc/tree duty, which the resident answer now states; and the same sentence's
  enumeration of `CLAUDE.md`'s fence becomes *"write back to `CLAUDE.md` only what its fence admits
  (`reference/repo-claude-md.md`)"* — the trigger stays resident, the enumeration lives where the rule
  does. Nothing else is removed, and every rule the old sentence carried — the PR-disclosure duty
  included — has a resident home in the new one;
- **trimmed, in the same paragraph this change splits** — the cross-repo half keeps its rule word for
  word and loses one clause of pure rationale (*"an outsider session lacks that repo's context and
  conventions"*), which is what makes room for an anchored floor. Nothing operative leaves the page;
- **added** — `core.md`'s ask-axis gains *"a durable location is needed and nothing names one"*; its
  list is exclusive, so without this the main session's own ask is forbidden. **The new case and
  `worker-brief.md`'s matching stop trigger point at the table, not at `out-of-repo-writes.md`** — an
  unnamed *in-repo* destination would otherwise land on the wrong rule.

**Measured, not asserted, and not restated here:** the gate is run on the head and its output is
quoted in the PR's evidence block. No total is written on this page — that is the snapshot-shaped
claim `CLAUDE.md` forbids, and the first draft of this item got the number wrong, which is the reason
for the rule. The **headroom argument** — that `core.md` is at its working ceiling, so the next
addition to it trims before it adds — is stated once, in **ADR 0042**, where the carve-out allows it.

**`$HOME` is not forbidden; an *invented* place under it is** — a tool's documented cache and a path
the human or the repo declared stay legitimate. Cost is measured on the head by the page's own gate,
quoted in the PR and re-run after any wording change.

**14. `reference/worker-brief.md`** — workers receive the brief, not `core.md`, so the rule cannot
reach them by `core.md` alone. Its placement bullet currently reads *"add only documentation admitted by
`reference/in-repo-writes.md`; otherwise use the repo, your session's scratch … or a location a tool's
convention or the repo's `CLAUDE.md` names"* — which routes everything non-document to "the repo" and
carries no pointer to the table: it gains the same resident answer in brief form and the pointer, and its stop list gains
**durable generated output with nowhere named for it** alongside the download/environment/deploy case
already there. Its **Done** rule — *name any write you made outside the repo* — is replaced by the
narrowed duty: **durable** external destinations, plus scratch only where its contents matter
(`out-of-repo-writes.md`), or a worker keeps listing every `mktemp -d` while the resident rule says
otherwise. Verification asserts the old sentence is gone, not merely that the new one is present.

**15. The reviewer fence gains a generated-output trigger and a placement-authority field.** The
authority a destination rests on is not in the diff, so the fence gains **`{PLACEMENT_AUTHORITY}`**:
for every destination this change selects, **the table row it took and that row's own authority** —
row 6 cites one of the four arms above and where it is; row 4 cites the repo's publishing convention;
row 7 the tool's cache; row 8 the declaration that preceded the write. Requiring a row-6 arm for all
of them would reject valid release, reusable-tooling, credential and service-state destinations, or justify
them under the wrong rule. The **routing block — the table's rows — is supplied
mechanically alongside the ladder, and gets the same treatment**: its own begin/end markers, a declared
payload line count, byte-equality asserted by CI, and **unfilled, markerless or mismatched is
Critical**. Because the row order *is* the precedence, a truncated or reordered copy silently changes
the decision, which is why it cannot be pasted loosely. or a source-less reviewer cannot check the claimed row at all and
"row 7, tool cache" passes on assertion. Each citation is an **address**: a path in the base tree, the
tool's documentation, the pre-work doc and its line, or the issue/PR comment and its author.
`reference/worker-brief.md`'s delivery duties gain filling this field, so the reviewer receives it
rather than reconstructing it. **Absent, unfilled, uncitable, or inconsistent with the diff is
Critical**; `NONE` is
valid only when the change selects no destination. Without it a reviewer either rejects a legitimate
approval it cannot see or accepts an unverifiable claim in the report.

 Any **instruction in the diff that selects a
destination** — application source, logging or test configuration, a Docker Compose or service file, a
script, a Makefile, a CI step, **and documentation, since item 12 treats the repo's docs as authority**:
a diff that adds an invented path only to `README.md`, `CLAUDE.md` or the architecture doc would
otherwise escape this trigger and license the write after merge.
A path **supplied complete by the caller** is not the change's choice and is out of scope — but only
complete: code that takes a parent such as `$HOME` and appends its own `logs/`, or supplies a default
or fallback of its own, **is** choosing a destination and is in scope. The fence gains: for a
destination this change selects, apply the placement table's branch — established in
`{CONVENTION_BASE_SHA}`, a real tool default, or authority that existed before this work, or a human decision in
one of arm (d)'s venues — the issue, or a comment on an already-open PR — never the doer's own text. **A mention added by this same diff licenses nothing**, and a caller-supplied
path is not the change's choice. An invented destination is an **Important** finding.

**16b. `reference/out-of-repo-writes.md`** — it presents three *exhaustive* kinds, but item 12 can
send durable generated output outside the repo, which fits none of them, and its disclosure rule
covers only kinds 1–2. Its opening says the three kinds are the ones **it** governs and points
durable generated output at the table; its disclosure rule extends to **any external destination
chosen under row 6**, named in the PR — or at handback where none exists — like the rest. Nothing else on the page moves.

**16c. `reference/clean-handback.md`, and ADR 0041's matching sentence** — the hole this addition
would otherwise open: the page treats
ignored paths as outside `-uall` and outside its promise, while item 12 relies on *rejecting* a
must-keep artifact placed in an ignored path inside a disposable worktree. `git status -uall` is clean
right up to the `git worktree remove` that destroys it. So a **retention check before teardown**:
anything you were told to keep must already live where it survives the worktree — committed,
published, or at a declared persistent root — and the worktree lifecycle's Death step carries the
trigger and the pointer, not only the table. The page's *ignored paths are outside this promise*
exclusion is **narrowed to discovery** — it means the check does not go looking for unknown ignored
paths or read their contents; **a known must-keep artifact stays in scope wherever it sits.** ADR 0041
carries the same sentence and is **edited directly rather than amended**: it is new in this PR and has
never been on `main`, so there is no immutable body to preserve — the append-only check covers ADRs
that exist on `origin/main`, and 0041 is asserted for content instead.

**17. ADR 0042 — the placement decision needs its own ADR.** A design spec does not stand in for one
when the architecture changes, and neither planned amendment records this: 0007's qualifies router
terminology, 0037's records the trigger's relocation. **0042** records the decision itself — every
file has a place, chosen by role and lifetime; a fourth destination class (durable generated output)
with an authority ladder; and the resident answer in `core.md` as a deliberate departure from
pointer-only triggers, on the evidence that the pointer-only form did not land. It amends **0007**, **0012** (its
durable-state-committed-to-the-branch ruling, narrowed by item 16d), **0018** (its gotcha kinds gain
the retained-output root as an instance, item 16g), **0037** and **0041**, each by a
dated block with a matching status entry on both sides. Number claimed 2026-08-28 against the merged log (highest `0040`),
every remote branch (highest `0041`, this branch's own), the one open PR (#171, this work) and the
open issues; the claim is re-verified at write time with its evidence in the PR.

**16d. The "commit what must survive" sentences.** `reference/clean-handback.md`'s *progress that must
survive is committed*, `reference/worktree-lifecycle.md`'s matching line, and **ADR 0012**'s ruling all
predate row 6 and would now have a checkpoint, a retained log or a large generated dataset **committed**
rather than routed. Each is narrowed to **repository and branch progress** — the work the branch
exists to carry — and points generated artifacts at the table. ADR 0012 is amended through **0042**.

**16e. `reference/ci-pipelines.md`** — *anything worth keeping ships through the release pipeline*
collides with two rows at once: retained non-release output (row 6) and published task evidence
(row 5). It gains the distinction: **release deliverables** ship through the pipeline (row 4);
**evidence** is shared through row 5's safe, available channel; **retained non-release output**
follows row 6's ladder.

**16g. `reference/repo-claude-md.md` and ADR 0018** — item 12's arm (c) relies on a retained-output
root living in an admitted `CLAUDE.md` gotcha, but the guide and ADR 0018 admit only a cache or deploy
root as that kind of fact. A retained-output root is the same kind of fact — a location on the machine
a clean-context worker must not re-invent — and is named as another instance of it, not a new content
kind: the fence is not widened. ADR 0018 is reconciled through **0042**.

**16f. `docs/architecture.md`'s ask-axes sentence** — the shared baseline still says the human is
asked on three axes, so a reader could proceed where item 13 now requires asking. It gains the
unnamed-durable-location axis, and joins the subject-based sweep.

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
never widened); a gate on untracked files (impossible); **the discovery and contents of ignored paths
nobody has named** — a *known* must-keep artifact stays governed wherever it sits (item 16c); what the
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
  paragraph whose first sentence is the placement question**, not folded back into the cross-repo one,
  and **byte-identical to the verbatim text in Decision 13**; **the row-6 authority clause byte-equal between the
  table's row 6 and the reviewer fence** (the two sites that carry it; `core.md` states the floor and
  is asserted for that instead); `docs/architecture.md`'s widened ask-axes sentence; the fence's
  `{PLACEMENT_AUTHORITY}` field with its `NONE` case and Critical wording; the narrowed
  "commit what must survive" sentences and `ci-pipelines.md`'s three-way distinction;
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
  in **0007, 0012, 0017, 0018, 0037 and 0041** — 0041's included, since ADR 0042 amends it and the index
  would otherwise hide that block — with ADR 0042's own `Amends` list naming the same set; **ADR 0042 present and indexed**; ADR 0041 asserted for its
  narrowed ignored-path sentence (edited directly — it is new in this PR and never on `main`); all five
  amended-on-main ADRs verified append-only by the Status-block-stripped
  byte-prefix check against `origin/main`;
- **negative boundaries for the addition**, each a case the table must route the stated way and not
  another: `.env.local` (row 3, never row 1), `.pytest_cache/` (row 9, never row 10), a coverage report
  (row 5, never row 2), a release archive (row 4, never row 1 or 5), a kept log with nothing naming a
  location (item 12's stop-and-ask, never an invented `logs/`), and a must-keep artifact offered a
  gitignored worktree path (rejected — the destination must outlive the task); a **generated signing
  key that must survive** (row 3's durable-credential branch, never row 5); a tool-written coverage
  report (row 5, never row 9); a tool-written log that must survive (row 6, never row 9); a release
  archive (row 4, never row 5); **two files under an invented `logs/`** (establishes nothing); a downloaded model
  (row 7, never row 3); a shared venv and a `ccache` (row 7, never row 6); a service's SQLite file (row 8, never row 6, and row 9 or 10 when disposable); and a must-keep artifact still sitting in a worktree at teardown (the retention check fires).

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
the placement table included; **`out-of-repo-writes.md`'s item-16b edits — its qualified opening and
widened disclosure — revert with them**, or a dangling pointer and a rule naming a deleted row survive. ADR
0041 **and ADR 0042** are superseded rather than rewritten — a reverted placement decision must not
sit at `Accepted` for a future reader to act on — and 0007/0012/0017/0018/0037 gain further dated
blocks pointing there; the CI assertion reverts with the pages. No data, schema, or install state is involved.
