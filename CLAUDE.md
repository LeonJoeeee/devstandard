# Working on DevStandard itself

This file is **repo ops for this repository only**. It is not part of the method: nothing in
`core.md` or `reference/` points at it, and no seeded project receives it. Like `docs/adr/`
(below) it is copied into the plugin package, where nothing reads it — Claude Code loads a
*project's* `CLAUDE.md`, never a plugin's. Everything here is a practice we follow *while
building DevStandard*, not a rule DevStandard states.

**Never write the page total.** An ADR or a PR description may state what a change *cost* — ADR
0027's *"core.md pays 180 tokens"* for the sweep rule — because that is history and stays true
forever. It may not state what the page *measures afterwards* (`total 4,560 of 5,000`): that is a
snapshot, it is stale by the next change that moves anything, and the CI-enforced ceiling is the
only current figure a reader needs. Every such total written this month was wrong within a week —
and the ones already in `docs/adr/` stay exactly as written; an immutable body is not a defect to
clean up.

Two carve-outs. **A gate's own output quoted as evidence** — `core.md ~N tokens (ceiling 5000)`
in a PR's evidence block — is the run's words, dated by the run, and is what a reviewer verifies
gate 2 against; quote it there and restate it nowhere else (including here, which is why this
example is a placeholder). And **an argument that turns on headroom** may state the distance to
the ceiling, because a delta cannot express it — but it states it once, in the ADR that makes the
argument.

**The line that decides what belongs here:** a method DevStandard *ships* goes in the shipped
pages; a practice useful only for maintaining *this* project goes here. When the two get
confused, repo-ops material ends up on a page every project pays to read every session — which
is what happened to the rule below (ADR 0030).

## Auditing our own pages (ADR 0032)

Our pages are the product, so their length is a cost every reader pays. Two rules, and when they
disagree the first one wins.

**1. Weight is earned by frequency × cost-of-getting-it-wrong *in a target project*** — never by
how vivid the incident was here. The question that finds the defect is not "is this rule true for
someone else?" (it usually is, which is why two audits passed it) but **"is its weight proportional
to how often a normal project hits it — or to how memorably we hit it?"** `reference/adr.md` failed
it hardest: 314 words on claiming a free ADR number, a collision we hit because our product is
decisions, sitting beside 66 words for the irreversible one. `reference/worktree-lifecycle.md` is
the standard — long exactly where the failure cannot be undone.

**2. A rule is stated in full in exactly one place; every other site carries the trigger and a
pointer.** One incident used to buy four documents — the CI-fallback family ran to 2,005 words
across five files. Prefer a small file sized to what the pointer asks for over pointing at a large
file that happens to contain the answer (ADR 0031); `reference/red-check.md` exists for exactly that
reason.

**The trigger always stays resident.** A reader who does not recognise the situation never follows
the pointer, so rule 2 never applies to the sentence that makes someone *look* — which is why
`core.md`'s exception blocks were cleared rather than sunk. Sinking a trigger is not compression;
it is deletion with extra steps.

## Commands

Any change here is done-checked by the CI gates (`.github/workflows/ci.yml`), all runnable from the
repo root — **plus one pre-merge command that is deliberately not in CI.** A gate could be built
(`on: pull_request` already has the number and a token); 0034 rejects it because `.github/` is not
shipped, so target projects would inherit nothing from it. Quote the count nowhere: it keeps
changing, and a stated count is the snapshot-shaped claim the rule above forbids.

```sh
# 1. hook: valid JSON, < 4000 bytes, names core.md with the forced-read wording
./hooks/session-start | python3 -c 'import json,sys; r=sys.stdin.buffer.read(); d=json.loads(r); c=d["hookSpecificOutput"]["additionalContext"]; assert len(r)<4000 and d["hookSpecificOutput"]["hookEventName"]=="SessionStart" and all(x in c for x in ("DevStandard","core.md","IN FULL","before acting")); print("hook OK",len(r),"bytes")'

# 2. core.md token budget (the repo's own words x 1.35 proxy) — must be <= 5000
python3 -c 'w=len(open("core.md").read().split()); t=int(w*1.35); assert t<=5000; print(t,"tokens")'

# 3. no @path references (they force-load at session start)
! grep -rn "@[a-zA-Z0-9_-]*/" core.md reference/ --include='*.md' | grep -v actions/ | grep -v anthropic | grep .

# 4. every ADR amendment block is announced by its status line, in the matching form
python3 .github/check-adr-index.py

# 5. NOT a CI gate — run this yourself before merging: the PR carries its check-1 verdict(s).
#    Counting all comments passes on a CI-FALLBACK block or a bot note, so match the verdict itself.
PR=<number> test "$(gh api "repos/LeonJoeeee/devstandard/issues/$PR/comments" \
  --jq '[.[] | select(.body | test("[Mm]erge check 1"))] | length')" -ge 1
#    Matches the heading reference/code-review-prompt.md now prescribes. All twelve of this repo's
#    first verdicts predate that convention; six happen to match, the rest open with headings of
#    their own.

# 6. manifests in lockstep (and equal to the tag, on release)
python3 -c 'import json; p=json.load(open(".claude-plugin/plugin.json"))["version"]; m=json.load(open(".claude-plugin/marketplace.json"))["plugins"][0]["version"]; assert p==m; print("lockstep",p)'
```

**The verdict is posted when it arrives, not when you remember.** Check 1 runs as a subagent here,
so its verdict comes back into the merging session and nowhere else. Five consecutive merges went
out without one (issue #118), and **the last two went out after the diagnosis was already written**
— so knowing the rule is not the safeguard. Command 5 above is the pre-merge check. The safeguard
meant to fire at the moment itself is in the reviewer's own prompt, which now makes the *verdict*
close with a line telling the caller to publish — **and it only reaches you if you paste the fence
whole.** A bespoke brief that keeps the output format and drops the rest drops the safeguard too.
Whether it works is a claim the next merges get to test, not one to make here.

## Rewording a rule: search twice

Our product is prose, so nothing mechanical catches a stale statement. Rename a function and
the compiler finds every caller; reword a rule and **nothing responds**. Six recorded instances
(issue #79), plus several more during the 0028/0029 work.

When you change the wording of a rule that exists in more than one place, **search twice**:

1. **Every other statement of the clause** — the `reference/` files, `docs/architecture.md`, and
   the ADR that recorded it.
2. **Every site that cites or paraphrases it**, found by *its pointer to the rule* — the file
   it names, the rule's subject — and **never by the words you just added.** This is the half
   that matters and the half that keeps being skipped: searching for the word you added finds
   every site that already has it, and by construction cannot find the sites that should now
   carry it.

Reconcile each in the same diff, or say in the PR description why it needs none — a site simply
absent from the sweep is a silent omission, not a clearing.

**Cite the rule, not the line.** A `core.md:NN` pointer is stale the moment anything above it moves.
One trim of `core.md` staled **every live citation below its first cut** — four sites, three of them
in immutable ADR bodies correctable only by appending, and the cut that broke the oldest of them was
nowhere near the rule it named. Name the rule or its paragraph instead; that survives an edit, and it
is what a reader searches for anyway.

The one place a line number belongs is **an amendment recording the move** — there the number *is*
the correction, and a reader holding the old one needs the mapping. Give the rule's name beside it, so
the block still works after the next trim moves it again.

**Record the ruling, not the tally.** Do not close a sweep with "N sites" — three consecutive
review rounds on one PR were each closed by such a count, and each later pass found the count
short. A count is also the total-shaped claim the rule above forbids: it is a snapshot, and the
next commit that quotes an old path moves it. State which sites are reconciled and which are
cleared and why; if a measurement is worth giving, give it with the commit it was taken at.

Two sites take a specific form:

- **An ADR** is reconciled by appending a dated `**Amendment (YYYY-MM-DD, see NNNN):**` block,
  never by a rewritten body (`reference/adr.md`). And the distinction that decides whether it needs
  one at all — sharpened after PR #108 answered it one way for this file and the other way for
  `docs/adr/` without noticing: **would a reader *act* on the sentence, or only read it?** A
  statement they would follow — where a rule lives now, what a future action will cost — is a live
  instruction and is reconciled. A statement they would only read — what was true when the decision
  was made, what a change cost at the time — is history and never is. **Ask what the sentence is
  *for*, not what tense it is in:** a Consequences sentence listing which files a change touched
  (*"core.md, `reference/ci-pipelines.md` … are updated to carry the rule"*) is history even in the
  present tense — it records what happened; a sentence whose job is to **route** (*"X carries the
  operative wording"*, *"Operational checklist: X"*, *"the fence X ships is unchanged"*) is live
  even inside a Consequences section. **The cue is structure, not the verb:** a *standalone*
  sentence whose only job is to say where a rule lives is live; the same verb inside a list of what
  this change touched is not — "carries" appears on both sides of the line.
- **A historical record** — a merged PR description, a released tag's notes — is not a site.

## The release delegation

`core.md`'s two-checks paragraph says releasing is the human's call. **For this repo that call was
delegated standing on 2026-07-24** (issue #37): since v0.9.3 the agent releases right after each merge —
bump both manifests in lockstep, tag, push — without asking per release. The goal was that every
merged improvement reaches the human's other sessions as fast as possible.

Withdrawing it is the human's to do. **Target projects are unaffected:** there, release go/no-go
stays on the human's ask-axes and `reference/ci-pipelines.md`'s tag-triggered default governs.

**Version bumps:** fold into the change PR when the semver call is unambiguous; split it out when
that call deserves a reviewer's attention (issue #99, recorded in ADR 0029).

## ADRs in this repo

`docs/adr/` ships inside the plugin package (the human's ruling on issue #93: we are the only
installer today, and the log is more useful one directory away than absent). Consequence:
**an ADR that decides how we operate, rather than what the method says, must say so in its own
title and text** — otherwise a reader in a seeded project takes it for an instruction. ADR 0028
is the model; 0029 needed three review rounds to learn it.

**Two amendment blocks of the same date share one status entry**, and that is correct rather than a
gap: the status line is a set of dates, and one `Amended (YYYY-MM-DD)` announces every block carrying
it. Verified when the first such pair appeared (0007, 2026-08-17) — removing that single entry makes
`.github/check-adr-index.py` fail on **both** blocks, so nothing hides under it. Not to be confused
with the dateless `Amended by NNNN` gap ADR 0033 records, which is a different form and a real one.

**Claiming a number here is a real collision risk, and it is not in normal projects.** We write
ADRs at a rate a target project never will — our product *is* decisions — and several branches
are usually open at once. `reference/adr.md` states the rule (claim at write time; next above the
highest claimed anywhere, never the lowest free); these are the four places to look, kept here
because the file is read by projects that will never need the incantations:

```sh
# 1. the merged log — not `ls`, which shows your own working tree
git ls-tree --name-only origin/main docs/adr/
# 2. every remote branch. --no-renames, or an ADR moved in shows as a rename and hides from -A
git fetch --all && git log --all --diff-filter=AR --no-renames --name-only --pretty=format: -- 'docs/adr/*' | sort -u | grep .
# 3. every open PR
gh pr list --state open   # then: gh pr diff <n> --name-only | grep docs/adr/
```

The fourth place has no command: **an open issue that reserved a number for work not yet
written.** It has happened here — a number whose only claim lived in an issue, with nothing in
any tree, branch or PR to find. Record which number you took and what you checked it against in
the PR description, so check 1 can verify it like any other claim.
