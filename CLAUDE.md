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

## Commands

Any change here is done-checked by the four CI gates (`.github/workflows/ci.yml`), all runnable
from the repo root:

```sh
# 1. hook: valid JSON, < 4000 bytes, names core.md with the forced-read wording
./hooks/session-start | python3 -c 'import json,sys; r=sys.stdin.buffer.read(); d=json.loads(r); c=d["hookSpecificOutput"]["additionalContext"]; assert len(r)<4000 and d["hookSpecificOutput"]["hookEventName"]=="SessionStart" and all(x in c for x in ("DevStandard","core.md","IN FULL","before acting")); print("hook OK",len(r),"bytes")'

# 2. core.md token budget (the repo's own words x 1.35 proxy) — must be <= 5000
python3 -c 'w=len(open("core.md").read().split()); t=int(w*1.35); assert t<=5000; print(t,"tokens")'

# 3. no @path references (they force-load at session start)
! grep -rn "@[a-zA-Z0-9_-]*/" core.md reference/ --include='*.md' | grep -v actions/ | grep -v anthropic | grep .

# 4. manifests in lockstep (and equal to the tag, on release)
python3 -c 'import json; p=json.load(open(".claude-plugin/plugin.json"))["version"]; m=json.load(open(".claude-plugin/marketplace.json"))["plugins"][0]["version"]; assert p==m; print("lockstep",p)'
```

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

`core.md:87` says releasing is the human's call. **For this repo that call was delegated
standing on 2026-07-24** (issue #37): since v0.9.3 the agent releases right after each merge —
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
