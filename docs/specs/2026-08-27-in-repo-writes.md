# Where each kind of file goes: a routing table, admissible documents, and the tree you hand back

Status: items 1-10 accepted; items 11-17 rewritten 2026-08-29, rounds 15-17 applied, in challenge

*Items 1–10 were accepted 2026-08-28 after twenty-one challenge rounds, every round by a fresh read-only Codex run at
the standing setting; the last found nothing blocking; **items 11–17 are the human's scope correction, rewritten 2026-08-29 when the enumerating design was abandoned (item 11) and challenged afresh in that form; rounds 15, 16 and 17 each returned seven findings, all applied; round 17's are not yet re-challenged.** Issue #168 carries the evidence survey and the
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

**11. `reference/where-it-goes.md`** (new) — where a file goes by what it is. The family's entry
point and the only full statement of the rule. Not a *router* in ADR 0007's sense (that ADR refuses
an always-on dispatcher for requests and skills); this is a list you consult with a file already in
hand — **ADR 0007 gains a dated amendment** saying which kind it refuses, and `README.md`,
`docs/architecture.md` and `docs/PRD.md`, which repeat "no router" as a live claim, say so too. **No
rename of `out-of-repo-writes.md`**: making it the list loses on ADR 0031's granularity rule, and its
three kinds stay where they are.

**It does not enumerate, and it is not meant to.** The human's ruling, 2026-08-29: *"you cannot expect
a document of a few thousand tokens to cover everything; an uncommon case gets one sentence and the
agent decides — for instance, default to the project directory and do not pollute the home
directory."* The earlier draft of this addition tried to decide every case in advance: it grew a
pinned base SHA every doer had to record before any write, a four-arm authority ladder, and the same
"something this diff added authorises nothing" clause restated at six sites, found one site per
challenge round. Fourteen rounds produced a monotonically longer page and a blocking count that never
fell (8, 10, 9, 9, 14, 6, 11, 5, 8, 11, 6, 5, 6, 8; 6,457 to 7,506 words after the round-10 clean
rewrite). The apparatus was defending against an agent that invents a convention to authorise its own
write — which a false base SHA defeats just as easily — while the observed failure is an agent with
**no rule at all** writing into `$HOME`. It is dropped. What replaces it is a closing default, which
is what makes the list safe to leave incomplete.

The list, verbatim (the order decides, so a reordered or truncated copy is wrong):

<!-- BEGIN PLACEMENT LIST -->
Name what the file IS, then put it there. The first line that fits decides — what a file is for
outranks how it was produced.

 1. Material the repository MAINTAINS — source; configuration the product ships and the repo's own
    (CI, build, lint, .gitignore, editor and devcontainer files); lockfiles; a fixture committed as an
    input; an asset it serves. -> the repo, where its own structure puts it. Deciding to commit an
    output does not make it this line: a generated results.json is line 6 however you store it.
 2. Maintained documentation — prose the repo keeps, not merely output a human can read.
    -> only where `reference/in-repo-writes.md` admits it.
 3. Local configuration or a secret the task needs — .env.local, a key, seeded data.
    -> never committed; the worktree copy-list, or the location the repo or the tool already names.
    A credential the task generates stays here: a secure store or a declared path, never published.
 4. A release deliverable — a wheel, installer, image, archive. -> the repo's release and publishing
    convention. Never committed as a by-product, never merely attached to an issue.
 5. One-time evidence you show someone — a screenshot, a coverage summary, a benchmark number.
    -> made in scratch and shown through the issue or PR; redact first, and never put something
    sensitive on a channel that should not carry it.
 6. Something that must be KEPT — data, an artifact, a log, generated by the task or acquired for it.
    -> where something that already existed names: code or configuration that writes there, the tool's
    documented default, the repo's own docs, or a place the human chose. Something you added in this
    same change names nothing. Nothing names a place -> the default below.
 7. Reusable tool-managed material outliving the task — model weights, a shared venv, a cloned tool,
    a ccache. -> the tool's own cache (`out-of-repo-writes.md` kind 1). A one-off fetch is line 10.
 8. State a service owns. -> `out-of-repo-writes.md` kind 2, at a root the repo's docs declare.
 9. Tool-managed working output inside the worktree — node_modules/, .venv/, .pytest_cache/, a build
    directory the tool requires. -> the ignored location that tool owns, never an agent-chosen one.
10. Dies with the task — intermediates, a report read once, a dispatched process's output file.
    -> the scratch your session provides, or one `mktemp -d`.

THE DEFAULT — for anything not listed, and for every line above where nothing names a place: put it
INSIDE THE PROJECT, in a gitignored directory when it is not material the repo maintains, and
**never invent a place under `$HOME` or on the Desktop.** Judge it yourself; you do not need a rule
for every kind of file. Only a durable write that must live OUTSIDE the repo, with nothing naming a
place for it, is a stop-and-tell (a worker) or an ask (the main session).

WHAT THE DEFAULT DOES NOT SURVIVE: a worktree is deleted when its task ends, and a gitignored path
inside one is invisible to `git status --porcelain -uall`. So a KEPT file placed there by this default
is **named in the PR, or at handback where there is no PR**, and teardown does not proceed until it
has been moved out or explicitly discarded. Every durable write outside the repo is named the same
way — whether or not something named the place.
<!-- END PLACEMENT LIST -->

**12. `core.md` carries the answer, not only a pointer** — the human's direction, 2026-08-28: *part of
it in `core.md`, the detail in the file it points at.* The paragraph replaces the cross-repo half's
filesystem sentence, from *"The same holds for the filesystem between repos:"* through
*"(`reference/out-of-repo-writes.md`)."* It carries the common groups **and the default**, so a reader
`core.md` answers never has to open the list to avoid the failure this issue was opened for:

<!-- BEGIN CORE PLACEMENT PARAGRAPH -->
**Every file you create has a place; name what it is, then put it there** — material the repo
maintains, where its structure puts it; maintained documentation only where
`reference/in-repo-writes.md` admits it; a task-local intermediate in your session's scratch; evidence
made there and shown, redacted, through the issue or PR. Anything that must be KEPT goes where
something that already existed names — code or configuration, a tool's default, the repo's docs, the
human's choice; what this change added names nothing. **Nothing names a place: put it inside the
project, gitignored when the repo does not maintain it — never invent one under `$HOME` or on the
Desktop.** Judge it yourself. A kept file inside a worktree is named in the PR or at
handback **and moved out or discarded before teardown**. Name any durable write outside
the repo too; one that must live there with nowhere
named is a stop-and-tell or an ask (`reference/where-it-goes.md`).
<!-- END CORE PLACEMENT PARAGRAPH -->

**A fifth edit pays for the paragraph.** `core.md` does not pass its gate with the
semantically complete paragraph added and nothing removed, so the cross-repo half's *"The issue is the
handoff; that repo's own session picks it up."* is cut — it restates the preceding clause (*filing an
issue there … never fixing it yourself*) and states no rule of its own, which is audit rule 3 applied
to `core.md` for the first time. The gate's own run on the head is the evidence, quoted in the PR;
ADR 0042 carries the headroom argument once. **Not** cut, and deliberately: the parenthesis naming what a cross-repo issue must contain — rule 1 outranks rule 3,
and that is real operational content whose removal belongs to #172's sweep, not smuggled in here.

Three further `core.md` edits make room and keep it consistent: the doc/tree duty loses *"add only a
document `reference/in-repo-writes.md` admits; "* (the trigger now lives in the paragraph above); the
`CLAUDE.md` enumeration becomes *"write back to `CLAUDE.md` only what its fence admits
(`reference/repo-claude-md.md`)"*; and the cross-repo half loses one clause of pure rationale (*"an
outsider session lacks that repo's context and conventions"*). The ask-axis is **not** widened — the
default resolves the common unnamed case, and the existing out-of-repo axis already covers the one
case that still asks.

**13. `reference/worker-brief.md`** — workers receive the brief, not `core.md`. Its *Before you
write* bullet currently routes with *"otherwise use the repo, your session's scratch, … or a location
a tool's convention or the repo's `CLAUDE.md` names"* — **that clause is replaced, not merely
supplemented**: read literally it lets a worker commit generated output the list keeps gitignored.
It becomes the trigger plus the pointer, carrying the default so a worker who never opens the page
still lands inside the project rather than in `$HOME`; its stop list gains *"a durable location
outside the repo is needed and nothing names one."* Not the list itself: rule 2 of our own audit.
Verification asserts the old clause is **gone**, not merely that the new one is present.

**14. `reference/code-review-prompt.md`** — one line inside the fence, no new field and no copied
block. A clean reviewer cannot open our pages, so the instruction must be **self-contained** — the
rule and the severity both travel inside the fence, and a pointer alone would leave the reviewer with
examples and no rule:

> *Placement — every file this diff creates should sit where something that already existed puts it:
> the repo's own structure, a tool's documented default, the repo's docs, or the human's choice.
> Where nothing named a place, it belongs inside the project, gitignored when the repo does not
> maintain it. **Important:** a destination the agent invented under `$HOME` or on the Desktop (a
> tool's own cache such as `~/.cache/<tool>`, or a path the repo or the human named, is fine); a
> destination whose only authority is something this same diff added; a kept file left in a worktree
> without being named in the PR; a durable write outside the repo that the PR does not name.*

**15. What this change would otherwise contradict** — each reconciled in the same diff:
`reference/out-of-repo-writes.md` (its three kinds are the ones *it* governs; durable generated output
points at the list, and its disclosure rule extends to any external destination chosen under line 6);
`reference/worktree-lifecycle.md`'s Death step and `reference/clean-handback.md` (a **retention check before teardown**: something that must be kept, sitting in a
worktree about to be removed, is named in the PR or at handback **and** either moved out or
explicitly discarded — naming alone does not license the removal, which is the whole point of the
list's does-not-survive clause); `reference/ci-pipelines.md`'s *commit what must survive*, narrowed to the artifacts it
means; `reference/repo-claude-md.md`'s write-back sentence; `reference/external-agent.md`'s
`-o <outfile>` example, which is exactly a line-10 file; **`README.md`'s two inventories and
`docs/architecture.md`'s reference tree**, both of which enumerate this family page by page and would
otherwise omit its entry point — the not-a-router qualification is a *second*, separate edit at those
sites, not a substitute for the listing. **Cleared, with reason:** ADR 0037's three kinds keep their
bodies — the list points at them, it does not restate them; `docs/PRD.md` carries the not-a-router
qualification only, having no page inventory.

**16. ADR 0042** — the placement decision needs its own ADR; a design spec does not stand in for one.
It records the list, the default, and **why the enumerating design was abandoned** — the round data
above is the evidence, and it is history, so it stays true. It amends **0007** (which router is
refused), **0012** (durable state committed to the branch, now narrowed), **0037**, whose amendment must correct **both** of its live claims, not merely
route: its *"The operative rule lives in `reference/out-of-repo-writes.md`"* now names
`where-it-goes.md` as the entry point, and its **Rejected: a method-chosen default path** is
distinguished rather than left standing — what 0037 refused was a method-chosen default *outside* the
repo, and still refuses; the default this change adds is *inside the project*, which is the one place
the method already owns and **0041** (the ignored-path sentence), each by a dated block with a
matching status entry on both sides. Number claimed 2026-08-29 against the merged log (highest
`0040`), every remote branch (`0041`, this branch's own), the one open PR (#171, this work) and the
open issues.

**17. This repo's `CLAUDE.md` gains a third audit rule** — the human generalised the ruling on
2026-08-29: *"I think everything else should be like this too — do not over-enumerate. (Beyond where
files go, the same holds for the other questions.)"* It belongs beside the two rules in *Auditing our
own pages* — whose opening *"Two rules, and when they disagree the first one wins"* becomes **"Three
rules"** with the same precedence sentence, since a third rule under a heading that counts two is
exactly the stale statement our own *search twice* rule exists to catch — because it governs how we write every page, and it is repo-ops rather than shipped method:
target projects read the result, not the authoring rule, and putting it in `core.md` would charge every
reader for a rule that binds only us.

> **3. Give the common cases, then a closing default — never chase an exhaustive enumeration of an
> open-ended set.** (A genuinely closed set — a status vocabulary, an absolute NEVER list — is a
> contract, not an enumeration, and rule 3 does not touch it.) A page of a few
> thousand tokens cannot cover every case, and trying is how it grows without converging. Route what
> comes up often, then close with one sentence that decides everything else and let the agent judge.
> The signal that you are enumerating: each review round finds one more site missing the clause you
> added last round. That is not a page approaching completeness — it is a page with no floor. The
> placement design ran fourteen such rounds (ADR 0042).

Rule 1 still outranks it: a default that is cheap to state but wrong in a target project is worse than
the case it replaced. **Existing pages are not swept by this change** — that is issue #172, opened with
this PR, because a sweep of every page is its own reviewable diff and would bury this one.

## Out of scope

ADR 0037's three out-of-repo kinds themselves — they stay in `out-of-repo-writes.md`, unmoved and unrewritten; what each document *contains*; `CLAUDE.md`'s fence (tightened toward,
never widened); a gate on untracked files (impossible); **the discovery and contents of ignored paths
nobody has named** — a *known* must-keep artifact stays governed wherever it sits (item 15's retention check); what the
CI-fallback certifies (#169); the manifests; the human's other repos (#168 surveyed them — fixing a
neighbour is what "Stay in your own repo" forbids).

## Verification

**On the head, each a command whose exit code decides it:**

- every existing CI gate green, quoted with its own output;
- **the new path-shape assertion passes, fires on every negative control, stays green on the positive
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
- **every Decision site asserted inside its own section slice, trigger wording and pointer, enumerated
  rather than sampled.** For the addition, `core.md` has **exactly five** edits and all five are
  asserted — no more and no fewer, since "the named clause gone and nothing else" would otherwise
  reject the third: (a) the placement paragraph replacing the cross-repo filesystem sentence,
  byte-identical to item 12's text and standing as its own paragraph; (b) the doc/tree duty with
  `"add only a document reference/in-repo-writes.md admits; "` gone; (c) the `CLAUDE.md` enumeration
  replaced by the fence pointer; (d) the cross-repo rationale clause gone; (e) **the handoff
  restatement gone** — the trim that pays for (a). Then:
  `where-it-goes.md`'s list, byte-identical to item 11's text, **its closing default and its
  does-not-survive clause present**; `worker-brief.md`'s trigger, pointer and extended stop; the
  reviewer fence's placement line **with its three Important cases inside the fence**; **this repo's
  `CLAUDE.md` carrying audit rule 3** with its closed-set carve-out, **its heading updated to "Three
  rules" and rule 1's precedence sentence intact** (item 17); **`worker-brief.md`'s replaced routing
  clause asserted absent, not merely superseded**; the new page listed in
  `README.md`'s two inventories and `docs/architecture.md`'s reference tree, and the no-router
  qualification present at those two sites and in `docs/PRD.md` — listing and qualification asserted
  separately, since one can land without the other; and item 15's sites each by their own predicate, never as a
  collective: `out-of-repo-writes.md`'s opening naming the list as entry point and its widened
  disclosure; `worktree-lifecycle.md`'s Death step and `clean-handback.md` both carrying **named
  *and* moved-or-discarded**; `ci-pipelines.md`'s *commit what must survive* narrowed to the artifacts
  it means; `repo-claude-md.md`'s write-back sentence; `external-agent.md`'s `-o <outfile>` example
  marked a line-10 file. For items 1–10, unchanged and already verified: the two predicate pages,
  the five tightened `CLAUDE.md` sites, the reviewer fence's `M` case, scratch paths, base placeholders
  and `{ACCEPTED_SPEC_BLOB_SHA}`, `design-spec.md`'s blob-SHA step, the canonical-path consumers, the
  tree entries, README's two inventories and `docs/PRD.md`;
- **`core.md` stays within its gate**, quoted from the gate's own run;
- ADR 0041 and ADR 0042 present and indexed; every intended dated block and its matching status entry
  asserted by name and by amending ADR — 0012, 0017 and 0018 carry 0041's (items 1–10); 0007, 0012,
  0037 and 0041 carry 0042's. Each ADR's `Amends` list is asserted equal to the set of blocks that
  actually cite it. **Every amended ADR keeps its body**, 0041 included: the Status-block-stripped
  byte-prefix check runs against `origin/main` for the ADRs that exist there, and against the
  pre-addition commit on this branch for 0041, which `origin/main` does not contain;
- **each amendment asserted by its required correction, not by its existence** — presence and a
  matching status entry are both satisfied by an empty block. 0037's must name `where-it-goes.md` as
  the entry point in place of *"the operative rule lives in `reference/out-of-repo-writes.md`"* **and**
  distinguish its *Rejected: a method-chosen default path* as refusing an out-of-repo default only;
  0007's must say which router is refused; 0012's must carry the narrowed durable-state wording;
  0041's the ignored-path sentence. **ADR 0042's own body** is asserted for the three things it
  decides: the list, the closing default, and the abandonment of the enumerating design with its
  round data;
- **negative boundaries — challenge cases, not done-check items.** No executable can judge whether a
  signing key routes to line 3 rather than line 5; the machine gate here is the byte-identical block
  assertion above, and these cases are what the challenger and check 1 read the block against: a coverage report (line 5, never line 2); a release archive (line 4, never line 1 or 5); a
  generated signing key that must survive (line 3's durable branch, never line 5); a tool-written log
  that must survive (line 6, never line 9); a downloaded corpus that must be kept (line 6, never 7 or
  10); `.pytest_cache/` (line 9, never line 10); a kept log with nothing naming a location (**the
  default — a gitignored directory inside the project, never an invented one under `$HOME`**); an
  output whose only authority is a Compose file the same diff added (**names nothing — the default
  applies**); and a must-keep artifact still sitting in a worktree at teardown (the retention check
  fires).

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
directory appears under `$HOME` or on the Desktop after this ships; a must-keep artifact is lost to a
worktree teardown; a diff licenses its own output path by adding a mention; **the default sends
something into the project that plainly belonged outside it**, or a reader stops to ask where the
default should have answered. Each is an issue against this spec.

**Rollback** — prose: a revert PR restores the previous wording and deletes **all three** new pages,
`where-it-goes.md` included; **`out-of-repo-writes.md`'s item-15 edits — its qualified opening and
widened disclosure — revert with them**, or a dangling pointer and a rule naming a deleted row survive. ADR
0041 **and ADR 0042** are superseded rather than rewritten — a reverted placement decision must not
sit at `Accepted` for a future reader to act on — and 0007/0012/0017/0018/0037 gain further dated
blocks pointing there; **this repo's `CLAUDE.md` loses the third audit rule with them**; the CI assertion reverts with the pages. No data, schema, or install state is involved.
