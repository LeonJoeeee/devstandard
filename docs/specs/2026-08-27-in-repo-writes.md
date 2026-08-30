# Where each file goes: the placement rule, admissible documents, and the tree you hand back

Status: items 1-10 accepted; items 11-17 rewritten 2026-08-29 with no taxonomy, in challenge

*Items 1–10 were accepted 2026-08-28 after twenty-one challenge rounds, every round by a fresh read-only Codex run at
the standing setting; the last found nothing blocking; **items 11–17 are the human's scope correction. Three taxonomies were built and defeated over rounds 15–21 (7, 7, 7, 7, 9, 9, 10 blocking, never falling); on the human's word they were dropped entirely for a rule that closes with a default and names only the three kinds where the default is expensive. This form carries none of items 1–10's acceptance.** Issue #168 carries the evidence survey and the
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

**11. `reference/where-it-goes.md`** (new) — the family's entry point. **It is not a decision
procedure and does not classify.** It states the rule once, then spends its length on worked examples
and on the reasoning a reader needs to apply the rule to a case it does not name. Not a *router* in
ADR 0007's sense (that ADR refuses an always-on dispatcher for requests and skills) — **ADR 0007
gains a dated amendment** saying which kind it refuses, and `README.md`'s two inventories,
`docs/architecture.md`'s reference tree and `docs/PRD.md` carry the page and the qualification. **No
rename of `out-of-repo-writes.md`**: it loses on ADR 0031's granularity rule, and its three kinds stay
where they are.

**Why there is no taxonomy.** Three were built and each was defeated by the challenge in a way the
next one reproduced: an ordered list (the catch-all preceded the specific rows, so model weights took
the catch-all); two questions with no precedence (the output question overlapped every other kind, so
a service's data could reach the project-local default and die with a worktree); roles that bind (a
release archive containing a private key matches both *release: publish* and *secret: never publish*,
and *a file has one role* is not enforceable). The common cause is a page trying to be a complete
decision procedure over an open-ended set — the shape #173 records as unclosable by review, and the
shape the human ruled out on 2026-08-29. What ships instead decides the common case, closes with a
default, and **names only the three kinds where taking the default is expensive**.

The rule, verbatim — the page carries this and then its examples:

<!-- BEGIN PLACEMENT RULE -->
**Put every file where something that ALREADY EXISTED puts it** — code or configuration that writes
there, a tool's documented default, **the repo's own docs as they stood before this change**, or a
place the human chose. What this same change added names nothing: a config file, workflow or Compose
file this diff introduces cannot authorise its own destination. **A document relays authority, never
originates it** — a design spec, an issue or a note counts when it repeats a destination the human
chose or one that already existed; a destination it invents counts for nothing, including in a spec
written for this very task. **Neither does a handoff or session-state document** — inherited,
tracked, or admitted at a human's request: such an artifact never names a destination, whatever its
own standing. (`reference/in-repo-writes.md` governs whether it may exist at all; this governs
whether it may point anywhere, and the answer is no.)

**Nothing names a place? Put it inside the project** — in a gitignored directory when it is not
material the repo maintains — and **never invent a place outside it**: not under `$HOME`, not on the
Desktop, not an absolute path like `/opt/x`. Judge it yourself; you do not need a rule for every kind
of file, and a file that dies with the task belongs in your session's scratch or one `mktemp -d`.

**Three never take that default**, because a wrong answer costs more than a stray file. Where nothing
already names a place for one of these, ASK — a worker stops and tells the main session, the main
session asks the human:
- **a secret or confidential data** — a key, a token, a credential, including one your task
  generates; and data that must not spread: a production export, personal data, a licensed corpus.
  Never committed, never published, **whatever else is true of the file it sits in** — and note that
  the project-local default is not containment: `.gitignore` is not `.dockerignore`, and an ignored
  path is still copied by an image build or an archive;
- **application state, persistent or operational** — a service's, and equally a desktop app's or a
  CLI's autosave, history or local database; and the runtime files a program must be able to create
  to run at all: a socket, a PID file, a lock file, a spool. A project-local gitignored path dies with
  the worktree, a package replacement or a read-only install loses the first kind, and a read-only
  installation cannot create the second at all;
- **a release deliverable** — never committed as a by-product, never merely attached to an issue.

**Say where it went.** This is about artifacts, not about your work: a file you committed is safe in
the branch. **A kept file whose only durable copy is inside the worktree** — an untracked or ignored
artifact — is named in the PR, or at handback where there is no PR, and moved out or discarded before
teardown: a worktree is deleted when its task ends
and a gitignored path in one is invisible to `git status --porcelain -uall`. **"Inside the project"
means the repository you are working in — a disposable worktree is not a durable place.** If it must
outlive the task and the only place you have is a worktree — **or any other destination that does not
promise to keep it, an evictable tool cache included** — you have nowhere to move it to: stop and tell
the main session (a worker), or ask the human (the main session), before teardown rather than after.
A downloaded corpus that must be kept is the standing example: the tool's cache is the right place for
a re-fetchable copy, and the wrong place for the only one. Every durable write
outside the repo is named the same way, whether or not something named the place.
<!-- END PLACEMENT RULE -->

The page **points at `reference/out-of-repo-writes.md` for the details of the three expensive kinds**
— its declared-root requirement for service state, its cache arm, its retention and disclosure rules —
because the rule above says *that* they must not take the default, not *what* each one then needs. A
reader arriving from `core.md` must reach those details from here.

The page's examples carry the cases the challenge found, as illustrations rather than rules: a
generated `results.json` is not repo material because you decided to commit it; a coverage report
shown once lives in scratch and the same report that must be retained does not; model weights go to the tool's
documented cache whenever one exists, however many tasks they serve — the existing-authority rule is
unconditional; only where no cache is documented does the question arise, and then weights fetched for
one task are scratch while weights that must be kept take the durability rule and its ask;
generated prose a human can read is still governed by `reference/in-repo-writes.md`.

**12. `core.md` carries the answer, not only a pointer** — the human's direction, 2026-08-28: *part of
it in `core.md`, the detail in the file it points at.* It replaces the cross-repo half's filesystem
sentence, from *"The same holds for the filesystem between repos:"* through
*"(`reference/out-of-repo-writes.md`)."*

**It is a trigger and a pointer, not a statement of the rule** — audit rule 2, and the page's token
gate leaves no other option. What stays resident is what makes a reader recognise the situation and
what stops the failure this issue was opened for: put it where something already existed, never invent
a place outside the project, and the three kinds that ask instead. Everything else — why a same-change
document authorises nothing, that the secret rule binds whatever else the file is, that a kept
worktree file is moved out or discarded before teardown, that an evictable cache is no home for an
only copy — lives on the page, reached by the pointer.

<!-- BEGIN CORE PLACEMENT PARAGRAPH -->
**Every file you create has a place: put it where something that already existed puts it** — code or
config that writes there, a tool's documented default, the repo's docs, the human's choice; **what
this change added names nothing, and neither does a handoff or session-state document.** Nothing names
a place: put it inside the project, gitignored unless the repo maintains it, and **never invent one
outside it — not `$HOME`, not the Desktop.** Judge it yourself. **Three never take that default — a
secret or confidential data, application state, a release: where nothing names a place for one, ask**,
as you do when something must outlive the task and nowhere durable will keep it. Name any durable
write outside the repo, and any kept file still in a worktree, in the PR
(`reference/where-it-goes.md`).
<!-- END CORE PLACEMENT PARAGRAPH -->

**Another edit is a reconciliation the *search twice* rule demands anyway, and it pays for part of the
paragraph:** `core.md`'s ask-axis ends *"a durable write onto the human's filesystem outside the repo
with no place named for it — `reference/out-of-repo-writes.md`"*, which now both duplicates the
paragraph's own ask and routes to the wrong page. It becomes *"a durable write outside the repo with
nowhere named (`reference/where-it-goes.md`)"*.

The remaining `core.md` edits pay for the rest and keep it consistent. The page sits at its gate, so this
addition trims before it adds: the cross-repo half's *"The issue is the handoff; that repo's own
session picks it up."* is cut — it restates the preceding clause (*filing an issue there … never
fixing it yourself*) and states no rule of its own, which is **audit rule 3 applied to `core.md` for
the first time**. Then: the doc/tree duty's `CLAUDE.md` clause **keeps its four kinds and gains
the pointer** — *"write back only a command, environment gotcha, worktree copy-list entry, or
record-language declaration to `CLAUDE.md` (`reference/repo-claude-md.md`)"*. An earlier draft
replaced those four kinds with the pointer alone to save tokens; that sinks a **resident trigger**,
which audit rule 2 forbids and rule 3 exempts — four named kinds are a closed contract, not an
enumeration — and a main session that never opens the page would stop recording the first command or
gotcha it finds. **What pays for the paragraph instead** is the cross-repo half's *"(what you saw,
where, how to reproduce, why it matters)"*: filing an issue in another repo is rare and a thin one
costs a follow-up question, while a missed `CLAUDE.md` write-back is the cold-worker failure this repo
has already had — audit rule 1 decides it that way round. And the cross-repo half
**the ask-axis clause becomes *"or a write the placement rule below sends to an
ask"*** — shorter than what it replaces, and necessary: `core.md`'s ask-rule is exclusive (*"Ask the
human ONLY when…"*), so without it a main session facing an unnamed retained report is forbidden both
to use the default and to ask, which is the trap ADR 0037 hit and solved the same way. And the
cross-repo half loses one clause of pure rationale (*"an outsider session lacks that repo's context and
conventions"*). The doc/tree duty's document-admission clause **stays as items 1–10 shipped it** —
admission is not placement, and this paragraph does not restate it. The gate is run on the head and
quoted in the PR; ADR 0042 carries the headroom argument once.

**13. `reference/worker-brief.md`** — a subagent or workflow worker receives the brief and not
`core.md` (a separate live session reads both, so the two resident forms must not drift). Its *Before you write*
bullet routes with *"otherwise use the repo, your session's scratch, … or a location a tool's
convention or the repo's `CLAUDE.md` names"*, and its stop list carries *"a download, environment, or
deploy root needs a home and nothing names one …"*. **Both are replaced, not supplemented**: the first
lets a worker commit generated output; the second stops for three named cases and leaves every other
unnamed location to invention. They become the rule's trigger with the pointer, the default, and the
three ask-kinds. **Its Done paragraph's *"Name any write you made outside the repo"* is narrowed to
*durable* writes** — as written it also covers scratch and `mktemp`, which dilutes the signal the
disclosure exists to carry. Verification asserts all three old forms are **gone**.

**14. `reference/code-review-prompt.md`** — one self-contained instruction inside the fence, no new
field. A clean reviewer cannot open our pages, so the rule and the severities both travel inside it.
Its existing external-write paragraph — *"if the task plainly needed one and the report names none,
ask where it went (Minor — a question, not a blocking gate)"* — is **narrowed, not left standing
beside the new rule**: it stays Minor exactly where the reviewer cannot see the write.

> *Placement — every file this diff creates, **every destination it adds or changes in existing code
> or configuration**, and **every write the report says the work made**, should sit where something
> that already existed puts it:
> the repo's own structure, code or configuration that writes there, a tool's documented default, the
> repo's docs as they stood before this change, or the human's choice — **a handoff or session-state
> document names nothing even when tracked, and any document only relays a destination the human chose
> or one that already existed; a destination a document invents counts for nothing**. Where nothing named a place, it belongs inside the project, gitignored when the repo
> does not maintain it, and a disposable worktree is not a durable place. **Critical** where secret or confidential data is committed or
> published — **including inside an archive, image or bundle that is also a legitimate release going
> to its named destination; the container being authorised does not authorise its contents**. That is
> the existing security calibration, not a placement question. **Otherwise any violation of the rule
> above is Important** — including generated output committed into the repo, since deciding to commit
> something does not make it material the repo maintains. The cases below are applications of that
> rule, not the whole of it: (i) any destination
> the agent invented outside the project — under `$HOME`, on the Desktop, or an absolute path such as
> `/opt/x` — where a tool's own cache such as `~/.cache/<tool>`, or a path the repo or the human
> named, is fine and is not this, **except as the only copy of something that must be kept: a cache
> can be evicted, so that is a finding**; (ii) a destination outside the project whose only authority is
> something this same diff added; (iii) a secret or confidential file, application state persistent or
> operational, or a release deliverable **placed by the project-local default** — including into a gitignored worktree
> path — rather than by something that named it or by asking; a release committed as a by-product or
> merely attached to an issue; (iv) **an untracked or ignored kept file still sitting in a worktree —
> disclosed or not**, since naming it does not save it from teardown, while anything committed is safe
> in the branch and is not this; and a durable write outside the repo, visible in the
> diff or the report, that the PR does not name. Where you merely suspect an undisclosed write
> and cannot see one, that stays a question (Minor).*

**15. What this change would otherwise contradict** — each reconciled in the same diff, each by its
own predicate: **`reference/clean-handback.md`'s *"Progress that must survive a session is
committed"*** and **`reference/worktree-lifecycle.md`'s *"any progress that must outlive the session
is committed to the branch"*** — narrowed to *progress* (work in the branch), so neither orders
generated output committed against this rule; **`clean-handback.md`'s *"commit, ignore, or remove"***
for install and test artifacts — committing available only where the file is material the repo
maintains; **`ci-pipelines.md`'s *"anything worth keeping ships through the release pipeline"*** —
narrowed to actual release deliverables, so a retained coverage or security report is not published
as a release asset; both pages' **retention check before teardown** (named **and** moved out or
discarded, for a file placed by this default); **`reference/out-of-repo-writes.md`'s deliverable sentence** — the page calls every
*deliverable* session-local and disposable, which now sends a release archive to scratch to be
deleted; it is qualified to *task-local* deliverables, release deliverables excluded. **Its claim that a repo document names an external destination** is
qualified the same way — pre-existing, and never a handoff or session-state document — since as
written a worker could write such a document and then cite it; **ADR 0037's equivalent live claims
take the same correction in its amendment**. **Its opening and its stop-and-ask arm** —
the page is qualified as applying **only once `where-it-goes.md` has established that the destination
must be outside the project**, because its *"you are about to choose a location on the human's machine
that nothing has chosen — stop and tell"* would otherwise fire for a routine unnamed file the default
now places inside the project; it also names `where-it-goes.md` as the entry point and extends its
disclosure to every durable external write;
`reference/external-agent.md`'s `-o <outfile>` example, which is a dies-with-the-task file;
**the instruction to name task scratch in the PR when its contents matter, at BOTH
sites that carry it** — `reference/harness-codex.md` and `reference/out-of-repo-writes.md`'s kind 3.
Disclosure is now durable writes only and scratch is disposable, so each becomes: post any durable
result, then remove the scratch directory. Two sites, two assertions — reconciling one and not the
other is how the contradiction ships. **Cleared,
with reason:** `reference/repo-claude-md.md` — items 1–10 already reconciled its write-back sentence
and this change does not touch admission; ADR 0037's three kind *descriptions* — the rule points at
them and does not restate them, while the ADR itself is reconciled by item 16.

**16. ADR 0042** — the placement decision needs its own ADR. It records the rule, the default, the
three ask-kinds, and **why three taxonomies were abandoned**, with the round data as evidence; it
carries the headroom argument, the one place this repo allows the distance to the ceiling to be
stated. It amends **0007** (which router is refused), **0012** (durable state committed to the
branch, now narrowed), **0037** and **0041**. **0037's amendment corrects every live statement this change
touches, not only its routing** — its two routing claims (*"The operative rule lives in
`reference/out-of-repo-writes.md`"*, *"`reference/out-of-repo-writes.md` (new) carries the full
rule"*); its ***"The undeclared case is an ask"*** and the widened ask-axis and worker stop trigger
that follow from it, all narrowed to a write **already established as belonging outside the project**,
with the ordinary in-project default recorded as what now answers the rest; **its unqualified disclosure paragraph**, narrowed to durable
external writes to match the shipped pages; **both of its claims that a repo document names an
external destination**, qualified to a document that pre-existed this change and is not a handoff or
session-state artifact; **its frequency defence — *"rare by construction (only a durable write with no
tool default and no declared root)"*** — which no longer bounds the ask, since a secret, a runtime file
or a socket with nothing naming a place now asks whether or not the write is durable — left standing, the immutable ADR keeps teaching the self-authorisation path
the rule forbids; and its ***Rejected: a method-chosen default path***,
distinguished — what 0037 refused was a method-chosen default *outside*
the repo, and still refuses; this default is *inside the project*. Number claimed 2026-08-29 against the merged log
(highest `0040`), every remote branch (`0041`), the open PR (#171) and the open issues.

**17. This repo's `CLAUDE.md` gains a third audit rule, recorded in ADR 0043** — the human
generalised the ruling on 2026-08-29: *"I think everything else should be like this too — do not
over-enumerate."* It belongs beside the two rules in *Auditing our own pages*, because it governs how
we write every page and is repo-ops rather than shipped method. **ADR 0032 decided "Two rules for
maintaining our own pages"**, so the count is a decision: **ADR 0043** (repo-ops, and **said so in its title *and* in its
body**, per this repo's `docs/adr/` rule — the log ships inside the plugin, so a seeded-project reader
must not take it for method) records rule 3 and amends 0032 with a dated block; 0032 keeps its body. Only the section's
**opening sentence** changes — *"Two rules, and when they disagree the first one wins"* becomes
*"Three rules, …"*; the heading `## Auditing our own pages (ADR 0032)` stays. Number claimed
2026-08-29 against the same four sources; `0042` is claimed by item 16 of this spec.

> **3. Give the common cases, then a closing default — never chase an exhaustive enumeration of an
> open-ended set.** (A genuinely closed set — a status vocabulary, an absolute NEVER list — is a
> contract, not an enumeration, and rule 3 does not touch it.) Name explicitly the few cases where
> taking the default is expensive, and let the default carry the rest. The signal that you are
> enumerating: **round after round finds a new case the page does not decide, and the answer each
> time is another rule.** **The count alone proves nothing** — a round whose findings are consequences
> of the last round's fixes, or gaps in its verification, is the review working, however many there
> are. Two things it never licenses dismissing: **a site whose statement has staled** (rule 2 and
> *search twice*) and **a safety regression**. See #173 for the review-side counterpart.

Rule 1 still outranks it: a default that is cheap to state but wrong in a target project is worse
than the enumeration it replaced. **Existing pages are not swept by this change** — that is #172.

## Out of scope

ADR 0037's three out-of-repo kinds themselves — they stay in `out-of-repo-writes.md`, unmoved, and
unrewritten **except for the qualifications item 15 names**, each of which is a live arm that
would otherwise accept a destination this same change declares: kind 1's stop-and-ask arm (narrowed to
a write already established as belonging outside the project) **and its `CLAUDE.md` cache-root arm**;
kind 2's ***"document it before writing"* arm** — both qualified to a declaration that **pre-existed
this change**, or the human's choice; **and its *"never a path a design spec merely mentioned"*
sentence**, which as written also refuses a spec accepted before the work even though workers are
handed accepted specs. It is narrowed so that **a spec relays authority, never originates it**: a
destination the human chose, or one that already existed before this change, still counts when a spec
repeats it; **a destination the spec itself invents counts for nothing, including a spec written for
this very task** — otherwise a main session could name `/opt/x` in its own spec and dispatch a durable
write there without ever asking; and kind 3's deliverable sentence, which calls every deliverable
session-local and disposable and must exclude release deliverables. Any of them left alone contradicts
the rule or reopens self-authorisation; what each document *contains*; `CLAUDE.md`'s fence (tightened toward,
never widened); a gate on untracked files (impossible); **the discovery and contents of ignored paths
nobody has named** — a *known* must-keep artifact stays governed wherever it sits (item 15's retention check); what the
CI-fallback certifies (#169); the manifests; the human's other repos (#168 surveyed them — fixing a
neighbour is what "Stay in your own repo" forbids).

## Verification

**On the head, each a command whose exit code decides it:**

- every existing CI gate green, quoted with its own output, `core.md`'s token gate included;
- **the path-shape assertion passes, fires on every negative control, stays green on the positive
  control, and leaves the tree as it found it.** Negatives: root `NOTES.md`; `docs/HANDOFF.md`;
  `docs/adr/HANDOFF.md`; root `HANDOFF.MD` (suffix case); `ReadMe.MD` beside `README.md` (case-folded
  duplicate); `DOCS/adr/0041-x.md` (directory case); a case-only rename of `README.md` to `README.MD`,
  restored byte-for-byte; two otherwise-valid split-on-zoom children differing only by case
  (`docs/architecture/api.md` and `.../API.md`) — the uniqueness control, since `ReadMe.MD` fails the
  exact root allowlist even where case-folded uniqueness was never implemented; a truncated predicate
  block; a root `ARCHITECTURE.md` while `docs/architecture.md` exists. Positive: a valid
  `docs/architecture/<subsystem>.md`, which must stay green — a checker rejecting every split-on-zoom
  child would otherwise pass every negative. Each control is created, `git add`ed, the checker run,
  then unstaged **and deleted**, with `git status --porcelain -uall` matching the pre-control snapshot;
- **each `core.md` edit is asserted individually by its own effect** — that is the machine claim, and
  it is all a command can make. Whether the diff contains *those effects and nothing else* is check 1's
  judgement on `git diff <base> HEAD -- core.md`, named here so the reviewer knows to make it; no count
  is asserted, because a count is not what an exit code can establish and a stale one only misleads.
  **The base is named on the final branch, after the last rebase — never a SHA fixed
  in advance.** It is the parent of this addition's first implementation commit, identified once the
  branch is in its merged shape and restated in the PR description then. Any SHA written earlier is
  rewritten by the rebase this flow requires and would be unreachable when check 1 runs; and it is not
  GitHub's PR diff base either, which spans items 1–10 as well. The same commit is what ADR 0041's
  append-only check compares against — 0041 exists there, which is why the items-1–10 *spec*
  acceptance commit cannot serve: it predates 0041 and differs in `core.md` by unrelated hunks. **The "exactly these edits, nothing else" claim is check 1's to judge, not a
  command's.** An earlier draft of this section invented an expected-patch oracle — a patch committed
  before implementation, published by digest, addressed first by commit SHA and then by blob SHA to
  survive the rebase, its own files then needing removal so they would not violate this very change's
  placement rule. Three consecutive rounds found a new hole in that apparatus and the answer each time
  was another mechanism: **the same pathology this change exists to name, appearing inside its own
  done-check.** It is dropped. What replaces it is the division of labour this repo already has — CI
  owns path shape, check 1 owns semantics: the PR description names the pinned base and lists the
  edits below, and **check 1 verifies against `git diff <base> HEAD -- <path>` that exactly those
  edits are present and nothing else is.** A reviewer reading a diff is what that judgement actually
  needs; a command claiming to make it was over-claiming. This governs `core.md`'s edits, named below,
  **`out-of-repo-writes.md`** (whose three kind definitions this change promises to leave unmoved and
  unrewritten apart from the named qualifications), and **this repo's `CLAUDE.md`** (whose rules 1 and
  2 must survive while only the opening sentence changes). **The base is named after the final rebase, not before it.** A fixed SHA
  taken earlier is rewritten by the rebase this flow requires and would be unreachable when check 1
  runs; so the base is identified on the final branch — the last commit before this addition's first
  implementation commit — and its SHA is restated in
  the PR description at that point, after the last force-push. It is also what ADR 0041's append-only
  check compares against, ADR 0041
  existing there. The effects, named rather than counted — a tally is the
  snapshot-shaped claim this repo's own rule forbids, and two rounds of stale ones proved it: (a) the placement
  paragraph replacing the cross-repo filesystem sentence, byte-identical to item 12's block and
  standing as its own paragraph; (b) the doc/tree duty's `CLAUDE.md` clause gaining the
  `repo-claude-md.md` pointer **with its four kinds still present** — asserted both ways, since
  dropping them sinks a resident trigger; (b2) the cross-repo issue-contents parenthesis gone; (c) the cross-repo rationale clause gone; (d) the handoff restatement gone; (e) the ask-axis's out-of-repo clause
  shortened and re-pointed at `where-it-goes.md`. (d) and (e) pay for (a). **The doc/tree
  duty's document-admission clause is asserted PRESENT** — unchanged from items 1–10, so a diff that
  removes it fails;
- **`where-it-goes.md` carries item 11's block byte-identical**, with its default, its three
  ask-kinds and its say-where-it-went paragraph each asserted by their own text; the page's worked
  examples asserted **individually, each by its own text** — the committed `results.json`, the coverage
  report shown once versus retained, model weights for many tasks versus one, and generated prose still
  governed by `in-repo-writes.md` — since an empty section would otherwise pass while removing the
  reasoning that makes an open-ended default usable; **its pointer to
  `reference/out-of-repo-writes.md` for the three expensive kinds' details asserted present; and its
  *why there is no taxonomy* reasoning asserted — the statement that the page does not classify, the
  three shapes that failed, and their common cause** — since that is what makes an open-ended default
  usable by a reader facing a case it does not name;
- **`worker-brief.md`'s two old forms asserted ABSENT** — *"otherwise use the repo, your session's
  scratch"* and *"a download, environment, or deploy root needs a home and nothing names one"* — **and its Done paragraph's *"Name any write you made outside the repo"* asserted
  absent in that unqualified form and present narrowed to durable writes** — three old forms, three
  assertions. **The same bullet's in-repo document-admission trigger is asserted PRESENT** — items
  1–10 put it there, this change rewrites the placement half of the same sentence, and deleting it
  would otherwise pass every stated check and let a brief-only worker invent documents; and the new trigger, pointer, default and three ask-kinds present;
- **the reviewer fence's placement instruction present with all four Important cases (i)–(iv)
  asserted separately as applications rather than an inventory, with **the *any violation of the rule
  above is Important* sentence asserted** — without it a committed non-material `results.json` matches
  no case; the Critical clause asserted whole, its *including inside an archive, image or
  bundle that is also a legitimate release* binding included — the only protection for the
  release-containing-a-key case**; and the old unqualified Minor clause asserted absent;
- **item 15's sites, each by its own predicate, never as a collective**: `clean-handback.md`'s
  *"Progress that must survive a session is committed"* and `worktree-lifecycle.md`'s *"any progress
  that must outlive the session is committed to the branch"* each **absent** in their old form and
  present narrowed to *progress*; `clean-handback.md`'s *"commit, ignore, or remove"* qualified;
  `ci-pipelines.md`'s *"anything worth keeping ships through the release pipeline"* narrowed, its
  unqualified form absent; both pages' retention check carrying **named *and* moved-out-or-discarded,
  for a file placed by this default**; `out-of-repo-writes.md`'s **deliverable sentence asserted absent in its
  all-deliverables form and present qualified to task-local deliverables; its `CLAUDE.md` cache-root
  arm, kind 2's *document it before writing* arm, its general repo-document-authority claim, and its
  *never a path a design spec merely mentioned* sentence each asserted absent in their unqualified
  form and present qualified to a document that pre-existed this change and is not a handoff or
  session-state artifact; and a human-chosen destination asserted still accepted at each of them; **the
  design-spec sentence asserted in its relays-not-originates form; **the scratch-disclosure
  instruction asserted reconciled at BOTH `harness-codex.md` and kind 3**; and the reviewer fence's
  cache clause asserted with its only-copy exception** — a spec repeating a human's or a
  pre-existing destination counts, a spec inventing one does not, this task's own spec included**,
  since over-tightening would reject a service root the human named this week, its opening naming the
  entry point, its widened disclosure, **and its stop-and-ask arm asserted in the qualified form with the old unconditional
  *"a location on the human's machine that nothing has chosen"* absent** — otherwise a routine unnamed
  file still triggers the stop the default exists to remove; `external-agent.md`'s `-o <outfile>` example marked dies-with-the-task;
- **this repo's `CLAUDE.md`**: audit rule 3 present with its closed-set carve-out and its
  not-a-stale-site carve-out; its opening sentence reading *"Three rules, and when they disagree the
  first one wins"*; its `## Auditing our own pages (ADR 0032)` heading **unchanged**;
- the new page listed in `README.md`'s two inventories and `docs/architecture.md`'s reference tree,
  and the no-router qualification present at those two sites and in `docs/PRD.md` — listing and
  qualification asserted separately, since one can land without the other;
- **ADRs**: 0041 and 0042 and 0043 present and indexed; every intended dated block and its matching
  status entry asserted by name and by amending ADR — 0012, 0017 and 0018 carry 0041's (items 1–10);
  0007, 0012, 0037 and 0041 carry 0042's; **0032 carries 0043's**. Each ADR's `Amends` list asserted
  equal to the set of blocks that actually cite it, **0043's asserted equal to `{0032}`**. **Every
  amended ADR keeps its body**, 0041 included: the Status-block-stripped byte-prefix check runs
  against `origin/main` for the ADRs that exist there, and against the pre-addition commit on this
  branch for 0041, which `origin/main` does not contain;
- **each amendment asserted by its required correction, not by its existence** — presence and a
  matching status entry are both satisfied by an empty block. 0037's must name `where-it-goes.md` as
  the entry point in place of **both** its live routing claims; **narrow all three of its
  ask-statements — *"The undeclared case is an ask"*, the widened ask-axis, and the worker stop
  trigger — to a write already established as belonging outside the project, and record the ordinary
  in-project default as what answers the rest**; **qualify both of its claims that a repo document names an external
  destination to a pre-existing, non-handoff document; narrow its unqualified disclosure paragraph to durable
  external writes**; and distinguish its *Rejected: a method-chosen default path* as refusing an
  out-of-repo default only; 0007's must say which router is
  refused; 0012's must carry the narrowed durable-state wording; 0041's must qualify its *ignored paths remain outside the promise*
  sentence — a **known** must-keep artifact in an ignored path is named and moved out or discarded
  before teardown, even though the handback snapshot cannot see it, or 0041 still reads as licensing
  its disappearance;
  **0032's appended block must itself carry the correction — that there are now three
  rules and that 0043 records the third — asserted by that text, not by 0043's presence; and ADR
  0043's own body asserted for rule 3, its two carve-outs, its subordination to rule 1, **and an
  explicit repo-maintenance-only statement — asserted in the title AND in the body, since the log
  ships inside the plugin and a seeded-project reader must not take it for method.** **ADR 0042's body** asserted for the rule, the
  default, the three ask-kinds, the abandonment of the three taxonomies with its round data, and the
  headroom argument;
- **the ADR number claims are checked, not just asserted**: `0042` and `0043` absent from the merged
  log, and from every remote branch and open PR **other than this branch and this PR**, at check time
  (the three commanded sources in this repo's `CLAUDE.md`; a correct implementation necessarily puts
  both ADRs on this branch, so including it would make the check unsatisfiable), and the PR description carrying the claim evidence for both —
  the fourth source — an open issue reserving a number — is queried too
  (`gh issue list --state open --search "0042 OR 0043"`), **excluding #168, which is this work's own
  issue and legitimately reserves both**; a hit anywhere else is a collision;
- **issue #172 and issue #173 exist and are referenced** by the text that promises them.

**Challenge cases, not done-check items.** No executable can judge whether a generated signing key is
a secret rather than evidence; the machine gate is the byte-identical block assertion above, and these
are what the challenger and check 1 read the block against: a coverage report shown once (scratch) and
the same report that must be retained (not scratch); a generated signing key with nothing naming a
place (**ask — never the default; the case that shows an ask-kind outranks it**); a service's
persistent data with no declared root (**ask — never a gitignored path in a worktree**); a release
archive containing a private key (**both a release and a secret — the secret rule binds regardless,
which is why it is written as *whatever else is true of the file it sits in***); model weights serving
more than this task, and the same weights fetched for one task; a downloaded corpus that must be kept;
generated prose a human can read (still `in-repo-writes.md`); a fixture the repo commits as a test
input (repo material, not a secret); an ordinary output path — not state, not a secret, not a release — named by a
Compose file **this same diff adds** (**names nothing, so the default applies, and that is not a review
finding**), against the same file naming a `./data` database volume (**application state: the ask-kind
binds, the default does not apply**); `node_modules/` (the
tool's ignored location, never committed).

**Process, not head state:** check 1's verdict is posted whole — the comment opens with the prescribed
`## Merge check 1 — round N` heading **and contains the reviewer's raw output verbatim**, asserted by an
exit-code comparison of the heading-stripped comment body against the reviewer's own outfile **before
that outfile is removed** (the heading is prepended by the poster, so whole-comment byte equality is
the wrong test, and a prose claim of "verbatim" would pass a truncated verdict). The reviewer line
names the current head SHA.

## Failure detection & rollback

**Detection** — the path-shape assertion goes red or its allowlist is edited with no reason; a merged
PR adds a document passing no arm and check 1 did not raise it; a handoff document appears, or an
inherited one keeps being updated; a worker hands back a tree with unaccounted-for paths or without
its snapshots; **the hygiene rule deletes something it should have surfaced**; a dispatched run's
brief or outfile is found inside a worktree. **For the addition:** a directory the agent invented
appears outside the project after this ships; a must-keep artifact is lost to a worktree teardown; a
diff licenses a destination outside the project by adding a mention of it; **a secret or confidential file is committed or published at all,
whatever named the destination — or takes the project-local default instead of an existing authority
or an ask**, which is how one sits in an ignored path until an image build copies it out; application state — persistent or operational — or a release deliverable is
placed by the project-local default instead of by something that named it or by asking — the three the rule says never take it; or, the opposite
failure, **a reader stops to ask where the default should plainly have answered**. Each is an issue
against this spec.

**Rollback** — prose: a revert PR restores the previous wording and deletes `where-it-goes.md`, with
`out-of-repo-writes.md`'s item-15 edits reverting alongside it or a dangling pointer survives.
**Scoped to the addition:** items 1–10 stand — they were accepted separately, are already merged into
this branch's history, and `in-repo-writes.md` and `clean-handback.md` stay, as does ADR 0041. **Audit
rule 3 and ADR 0043 also stand** unless the human separately rescinds them: the human directed the
authoring rule independently of this design, and a durable log left declaring a rule the operative
page removed is the exact defect 0043 exists to prevent. ADR 0042 is superseded rather than rewritten
— a reverted placement decision must not sit at `Accepted` for a future reader to act on — and
0007/0012/0037/0041 gain further dated blocks pointing there. The CI assertion is untouched: it is
items 1–10's. No data, schema, or install state is involved.
