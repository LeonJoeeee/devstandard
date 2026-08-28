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

**11. `reference/where-it-goes.md`** (new) — the placement table, the family's entry point, and the
only statement of the routing rule. Not a *router* in ADR 0007's sense (that ADR rejects an always-on
dispatcher for requests and skills); this is a lookup opened with a file in hand — **ADR 0007 gains a
dated amendment** qualifying its ruling, and `README.md`, `docs/architecture.md` and `docs/PRD.md`,
which repeat "no router" as a live claim, say which kind is refused. **No rename of
`out-of-repo-writes.md`**: making it the table loses on ADR 0031's granularity rule and its three kinds
stay where they are.

The table ships as **one delimited, counted block** — the reviewer receives it verbatim and CI asserts
the two copies byte-equal, because the row order *is* the precedence and a truncated or reordered
paste silently changes the decision:

```
<!-- BEGIN PLACEMENT TABLE -->
Rows are evaluated in order; the FIRST that fits decides. The order is the precedence: what a file is
for outranks how it was produced.
THE PINNED BASE: before your first write — every doer, on every task, whether or not a document is
involved — record the SHA of the base you started from (normally origin/main; local main or HEAD with
no remote; the empty tree for founding setup) and publish it where the baseline goes. It is the base
every "predates this work" test below is measured against, and recording it later, or after a rebase,
would let edits made during the work count as pre-existing.

 1. Material the repository MAINTAINS, that is not a document — source; configuration the product
    ships and the repo's own (CI, build, lint, .gitignore, editor or devcontainer files); lockfiles; a
    fixture committed as an input; an asset it serves. -> the repo, where its own structure puts it.
    This row is about what the file IS, not where you propose to put it: DECIDING TO COMMIT AN OUTPUT
    DOES NOT MAKE IT ROW 1. A generated results.json or log is row 6 however you intend to store it,
    unless the repo already maintains that file as an input or a shipped asset.
 2. Maintained documentation — prose the repo keeps, not merely output a human can read.
    -> reference/in-repo-writes.md.
 3. Local configuration or secrets the task needs — .env.local, a key, seeded data the repo expects.
    -> never committed; the worktree copy-list, at the location the repo declares or the tool
    documents; where neither names one, stop-and-tell (a worker) or ask (the main session). A
    credential this task GENERATES stays in this row. If it must survive: the tool's own secure store,
    or a declared persistent location. If it is deliberately task-local — a test key, a throwaway
    token — a declared protected path for the task, removed before teardown; never published, never
    committed. Other generated local config that must survive takes row 6.
 4. A release deliverable — a wheel, installer, container image, release archive. -> the repo's
    release and publishing convention. Never committed as a by-product, never merely attached to an
    issue. It stays this row even when someone also looks at it. Where the repo has no such convention
    yet, the human's explicit pre-write destination decides; with none, stop and tell the main session
    (a worker) or ask the human (the main session) — first-match must not push you into inventing one.
 5. One-time evidence you show someone, with no retention requirement of its own — a screenshot, a
    coverage summary, a benchmark number. -> made in scratch and shared ONLY through a channel that
    is safe and available: the issue or PR when the artifact carries nothing sensitive and the channel
    can carry it; redacted first where it can be; otherwise a channel the human approved, or an ask.
    Where a light start has neither issue nor PR, the conversation or an explicit handback. Anything
    that must also be RETAINED is row 6, whether or not it is shown.
 6. Generated data, an artifact or a log you must keep — not a release (row 4), not reusable tooling
    material (row 7), not a service's persistent state (row 8). -> the authority ladder below. A
    destination outside the repo is named in the PR, or at explicit handback where no PR exists.
 7. Reusable, non-secret, tool-managed material that outlives the task — fetched or generated: model
    weights, a shared venv, a cloned tool, a ccache or Gradle cache. -> out-of-repo-writes.md kind 1
    and the tool's own cache. A one-off fetch is row 10; a fetched credential is row 3.
 8. Mutable state a service owns and that is meant to persist with it. -> out-of-repo-writes.md
    kind 2, declared before anything lands there. A disposable local or test service's state is row 9
    if the tool owns the location, row 10 if it dies with the task.
 9. Tool-managed working output inside the worktree — node_modules/, .venv/, .pytest_cache/, a build
    directory the tool requires. -> the ignored location that tool owns, where the pinned base already
    shows it or the tool genuinely requires it; never an agent-chosen one.
10. Dies with the task — agent-chosen intermediates, a report read once, a dispatched process's output
    file. -> the scratch your session provides, or one mktemp -d. Task-scoped state that must outlive
    the SESSION but not the task — a checkpoint the next session resumes from — goes in the worktree's
    own declared, gitignored scratch, is named in the handback, and is removed or promoted before
    teardown; a process-invoked agent confined to its own disposable worktree uses that same location
    (out-of-repo-writes.md kind 3).
<!-- END PLACEMENT TABLE (52 payload lines) -->
```

Reading downward resolves every case challenge raised: a release archive someone also views is row 4;
a coverage report a tool wrote is row 5; the same report if it must be retained is row 6; a
`.pytest_cache/` is row 9; a runtime-generated fixture is row 10 unless committed as an input, when it
is row 1; a disposable test service's SQLite is row 9 or 10; a reusable model is row 7 while a one-off
download is row 10.

**12. The row-6 authority ladder** — the kind with no rule today. It ships as the second delimited,
counted block, and **there is no other statement of it anywhere**: three competing versions is how the
earlier drafts drifted, and each qualification lives inside the block rather than trailing after it.

```
<!-- BEGIN ROW-6 AUTHORITY LADDER -->
FIRST, the override, which is not one of the arms: where the human has decided where this output goes
and that decision is recorded before the write — in the issue, in a comment on an already-open PR, or,
for a light start with neither, in the conversation and disclosed at handback — THAT is the
destination. An older base or tool default never outranks a newer human choice. What does not count is
a session's own conclusion written down as if it were the human's; an attributed, contemporaneous
record of what the human decided does count, and still does when the session recording it is the main
session on its own short branch.
Only where no such decision exists, take the FIRST arm below that applies. In every case the
destination must OUTLIVE THE TASK: a gitignored path inside a disposable worktree is never one.
(a) base-owned code or configuration, tracked at the pinned base, that writes there — not the current
    tree, not an ignore entry this task added, not a pattern like *.log, and not artifacts an earlier
    agent left, however many: count is not intent.
(b) the tool's documented default, when it is a real location AND the evidence establishing it — the
    tool's own release or upstream documentation — predates this work. A relative path resolving
    against the current directory selects nothing; a tool this diff introduces, or documentation this
    diff adds, supplies no default.
(c) the repo's own documentation as it stood at the pinned base, including a retained-output root
    carried as an admitted CLAUDE.md gotcha.
No override and no arm applies: stop and tell the main session (a worker) or ask the human (the main
session). Never write first and record after — that is how an invented directory becomes a precedent.
<!-- END ROW-6 AUTHORITY LADDER (20 payload lines) -->
```

Arms (a)–(c) are all measured against the pinned base; (b) and (c) carry the extra restriction that
the evidence establishing them must predate the work too, for one reason: otherwise the diff that invents
`outputs/` licenses itself, by adding a `README` line or by shipping a script whose own default points
there. A destination that must be kept but has no arm is not a licence to improvise — it is the ask.

**13. `core.md` carries the answer, not only a pointer** — the human's direction, 2026-08-28: *part of
it can live in `core.md`, and the rest points at the detail file.* A reader holding a file and asking
where it goes had no resident sentence keyed to that question: the rule rode inside the *stay in your
own repo* paragraph, whose subject is cross-repo edits. That is the likeliest reason a shipped rule did
not land (#168). The replacement is **its own paragraph, opening with the question** — leaving it in
the old paragraph is the burial this item diagnoses, and every keyword assertion would still pass — and
this is its exact text, drafted and measured before implementation:

> **Every file you create has a place; name what it is, then put it there** — material the repo
> maintains, where its structure puts it; maintained documentation only where
> `reference/in-repo-writes.md` admits it; a task-local intermediate in your session's scratch;
> one-time evidence made there and shared only through a safe, available channel. **Anything kept,
> released, reusable, or a service's state: only where something that predates this change already
> names the place, or a human decided before you wrote** — nothing named is a stop-and-tell or an ask.
> Tool-managed output, cross-session task state and the rest: the table routes them. **Never invent a
> place, in the repo root or under `$HOME`**; name any durable write outside the repo in the PR, or at
> handback where there is none (`reference/where-it-goes.md`).
>
> *Its categories are mutually exclusive, which the first draft's were not: "anything that dies with
> the task" swallowed `.venv`, `node_modules/` and a session-spanning checkpoint, and "anything shown"
> swallowed a viewed release and retained evidence — in the always-on text, where a reader acts
> without ever opening the table. It names a task-local intermediate and one-time evidence, and hands
> tool-managed output, cross-session task state, releases and retained evidence to the table by name.*

Everything else about the edit is stated once, here, rather than re-described route by route:

- it **replaces** the sentence from *"The same holds for the filesystem between repos:"* to
  *"(`reference/out-of-repo-writes.md`)."*, and every rule that sentence carried — the PR-disclosure
  duty included — appears above;
- the doc/tree duty loses exactly *"add only a document `reference/in-repo-writes.md` admits; "*, which
  the paragraph now states, and its enumeration of `CLAUDE.md`'s fence becomes *"write back to
  `CLAUDE.md` only what its fence admits (`reference/repo-claude-md.md`)"* — the trigger stays
  resident, the enumeration lives where the rule does;
- the cross-repo half keeps its rule word for word and loses one clause of pure rationale (*"an
  outsider session lacks that repo's context and conventions"*), which is what makes room for an
  anchored floor rather than a loose one;
- `core.md`'s ask-axis, which is exclusive, gains *"a durable location is needed and nothing names
  one"*, and that case — with `worker-brief.md`'s matching stop trigger — points at the table, not at
  `out-of-repo-writes.md`, since an unnamed *in-repo* destination would otherwise land on the wrong
  rule;
- the gate is run on the head and quoted in the PR. **No total is written on this page**; the headroom
  argument belongs once, to ADR 0042, which records the consequence: `core.md` is at its working
  ceiling, and the next addition to it trims before it adds.

**14. `reference/worker-brief.md`** — workers receive the brief, not `core.md`, so the rule reaches
them only if it is here. Its placement bullet — which today routes everything non-document to "the
repo" with no pointer — carries the resident answer in brief form and the pointer; its stop list gains
**durable generated output with nowhere named for it**, pointing at the table; its **Done** rule
(*name any write you made outside the repo*) is replaced by the narrowed duty — **durable** external
destinations, plus scratch only where its contents matter — and verification asserts the old sentence
is gone, not merely that the new one is present. Filling `{PLACEMENT_AUTHORITY}` joins its delivery
duties.

**15. `reference/code-review-prompt.md`** — two changes above the fence, three inside.
**Above:** before commissioning check 1 or any re-review, compare against your baseline and put both
snapshots in the PR (a main session's own short-branch PR never transfers, so "Taking delivery" never
reaches it). **Inside:** the Docs check gains the `{IN_REPO_WRITES_PREDICATE}` block as before; the
**placement table and the authority ladder are supplied as their own counted blocks**, extracted
mechanically, with unfilled, markerless or mismatched-count copies **Critical** — a source-less
reviewer cannot check a claimed row without the rows, and cannot check precedence without their order;
and **`{PLACEMENT_AUTHORITY}`** records, for every destination this change selects, **the row it took
and that row's own authority**, each citation an address (a path at the pinned base, the tool's
documentation and its version, the pre-work doc and its line, or the issue/PR comment and its author).
`NONE` is valid only when the change selects no destination. The trigger covers **any instruction in
the diff that selects a destination** — application source, logging or test configuration, a Docker
Compose or service file, a script, a Makefile, a CI step, and documentation, since the ladder treats
the repo's docs as authority. A path **supplied complete by the caller** is out of scope; code that
takes a parent and appends its own subdirectory, default or fallback is choosing, and is in scope.
Absent, unfilled, uncitable or inconsistent with the diff is **Critical**.

**16. What this change would otherwise contradict** — each reconciled in the same diff:
`reference/out-of-repo-writes.md` (its three kinds are the ones *it* governs; durable generated output
points at the table, and its disclosure rule extends to any external destination chosen under row 6);
`reference/clean-handback.md` and the lifecycle's Death step (a **retention check before teardown**:
anything you were told to keep already lives where it survives the worktree, and the *ignored paths are
outside this promise* exclusion is narrowed to **discovery** — a known must-keep artifact stays in
scope); ADR 0041's matching sentence, **edited directly** since it is new in this PR and never on
`main`; the *progress that must survive is committed* sentences in `clean-handback.md`,
`worktree-lifecycle.md` and **ADR 0012**, narrowed to repository and branch progress;
`reference/ci-pipelines.md`'s *anything worth keeping ships through the release pipeline*, which now
distinguishes releases (row 4), evidence shared through row 5's safe channel, and retained output
(row 6); `reference/repo-claude-md.md` and **ADR 0018**, where a retained-output root is named as
another instance of the existing gotcha kind — the fence is not widened; `docs/architecture.md`'s
ask-axes sentence, which still says the human is asked on three; and the no-router claims in
`README.md`, `docs/architecture.md` and `docs/PRD.md`. `README.md`'s two inventories, its *What you
get*, `docs/PRD.md`'s summary, `docs/architecture.md`'s tree entry and `reference/in-repo-writes.md`'s
footer gain the table. Cleared as history: the abandoned specs and every Consequences line describing
the outside-only subject.

**17. ADR 0042** — the placement decision needs its own ADR; a design spec does not stand in for one
when the architecture changes. It records: every file has a place, chosen by role and lifetime, with
the order as the precedence; a fourth destination class (durable generated output) with an authority
ladder anchored to the pinned base; the resident answer in `core.md` as a deliberate departure from
pointer-only triggers, on the evidence that the pointer-only form did not land; and the consequence
that `core.md` is at its working ceiling. It **amends 0007** (router terminology), **0012**
(durable-state-committed-to-the-branch), **0018** (the gotcha kinds gain an instance), **0037** (the
trigger's relocation) and **0041** (the ignored-path sentence) — each by a dated block with a matching
status entry on both sides. Number claimed 2026-08-28 against the merged log (highest `0040`), every
remote branch (`0041`, this branch's own), the one open PR (#171, this work) and the open issues;
re-verified at write time with the evidence in the PR.

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
  and **byte-identical to the verbatim text in Decision 13**; **both canonical blocks — the placement table and the row-6 authority ladder — byte-equal between the
  page that owns them and the reviewer fence**, each with its declared payload line count matching its
  own content (the count is asserted, not trusted — the first draft of this spec got both counts wrong);
  `core.md` states the floor only and is asserted for that instead; `docs/architecture.md`'s widened ask-axes sentence; the fence's
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
  **by name and by amending ADR**: 0012, 0017 and 0018 carry ADR **0041**'s blocks (items 1–10); 0007,
  0012, 0018, 0037 and 0041 carry ADR **0042**'s — 0012 and 0018 therefore carry one of each, and 0017
  is amended by 0041 only, which is why it is absent from 0042's `Amends` list. Each ADR's `Amends`
  list is asserted equal to the set of blocks that actually cite it; **ADR 0042 present and indexed**; ADR 0041 asserted for its
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
  a **reusable** model that outlives the task (row 7, never row 3) **and a one-off download (row 10,
  never row 7)**; a shared venv and a `ccache` (row 7, never row 6); a service's SQLite file (row 8, never row 6, and row 9 or 10 when disposable); and a must-keep artifact still sitting in a worktree at teardown (the retention check fires).

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
