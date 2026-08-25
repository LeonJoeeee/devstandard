# 0018 — A repo-root CLAUDE.md joins the doc set: operational memory for clean-context workers

Status: Accepted (2026-07-16). Amended (2026-07-25). Amended by 0030. Amended (2026-08-13). Amended (2026-08-25). Amended by 0037 (2026-08-25). Amended by 0038 (2026-08-25).

## Context

The optimization sweep's one genuine blind spot (`_source/devstandard-optimization-sweep.md`, proposal 2): the method is structurally amnesiac. Clean context is the design — fresh workers, fresh reviewers — so written memory is the only memory. Yet the doc set held design (`docs/architecture.md`), decisions (`docs/adr/`), and tasks (GitHub issues), and had **no home for operational facts**: which command runs the tests, which port is taken, which untracked files a new worktree must copy (`aids/worktree-lifecycle.md` referenced a "declared allowlist" that nothing ever created). Every fresh worker re-derived them by trial and error, or failed review on something one line would have prevented — the same lesson re-bought forever. A repo-root `CLAUDE.md` is the field's most-converged practice, and Claude Code reads it **natively** at session start — the same mechanism as the personal `~/.claude/CLAUDE.md`, scoped to the repo. AGENTS.md was rejected earlier for double-injection risk; CLAUDE.md carries none — it is Claude Code's own channel, separate from this plugin's hook.

## Decision

- **Every full setup generates a repo-root `CLAUDE.md`** in the same step as CI, when the project's commands have just been settled (section + template in `howto/cicd.md`). One page hard max; three kinds of content, nothing else: commands (install / test / run), environment gotchas, and the untracked-files list a new worktree copies. The template's last line is its fence: architecture, decisions, and task state live in their own homes and are never duplicated here.
- **Merge-time write-back** (`aids/worktree-lifecycle.md`, Death): before tearing down a merged task's worktree, ask — did this task expose a command, gotcha, or rule that would have prevented a review finding or a worker dead-end? If yes, one line into `CLAUDE.md` through the small-change lane. A design decision goes through the architecture process instead — never a quiet note.
- An existing repo adopts by a normal small change whenever wanted; the human's light-start declaration is respected as everywhere else.

Rejected: keeping lessons in session memory (evaporates by design); a new log file (the sweep found no load-bearing precedent, and a log is append-heavy where this file must stay one curated page); AGENTS.md (double-injection — already rejected and the reason still holds).

## Consequences

Operational facts reach every session, worktree, and separate session automatically (it is a tracked file — a worktree checkout carries it, and Claude Code loads it without being asked). Lessons stop evaporating: the file grows one line at a time, each line bought by a real incident. Costs: about a page of context per session in that repo, capped by the fence and the one-page rule; one extra question at every teardown. The plugin's own repo carries the first instance.

**Amendment (2026-07-25):** generation is conditional, not unconditional — a project generates the file only when it has commands, gotchas, a copy-list, or a non-English record to declare (howto/cicd.md); otherwise the first real line creates it through the write-back lane. The plugin's own repo no longer carries an instance: everything it held is now CI-enforced or convention (issue #66).

**Amendment (2026-08-06, see 0030):** this repo carries a root `CLAUDE.md` again. The
2026-07-25 amendment recorded that everything it held had become CI-enforced or convention, and
that was true then. It now holds a **Commands** section — this repo's four CI gates, which
were reconstructable only from `ci.yml` — plus two declarations that exist nowhere else: the
reworded-rule sweep, withdrawn from the shipped method as repo-only practice (0030), and the
human's standing delegation of per-release approval (issue #37), which lost both of its earlier
homes. **The conditional this ADR states is satisfied; 0030 widens this ADR's content fence for
this repo alone** — Commands meets the enumeration, and repo-ops practice is an additional kind
admitted here only. The fence `howto/cicd.md` ships to target projects is unchanged.

**Amendment (2026-08-13, caused by 0031):** four live pointers above now read `reference/`, one
per site rather than a count. **Decision bullet 1's** "(section + template in `howto/cicd.md`)" is
`reference/repo-claude-md.md` — 0031 split `cicd.md` into four files, so "now reads `reference/`"
does not name an address on its own. **Decision bullet 2's** "(`aids/worktree-lifecycle.md`,
Death)" is `reference/worktree-lifecycle.md`, "## Death", step 2 — and while there: that bullet's
*"through the small-change lane"* was retired by 0022, which made ceremony universal; the write-back
now rides a short-branch PR like any other change, as that file states. **The 2026-07-25
amendment's** "(howto/cicd.md)" and **the 2026-08-06 amendment's** "the fence `howto/cicd.md` ships
to target projects" are both `reference/repo-claude-md.md`, which carries the conditional-generation
rule and the three-kinds fence. Every rule named is unchanged — only the addresses, and the retired
lane.

**Amendment (2026-08-25, issue #132):** the "One page hard max" in Decision bullet 1 gains the two
things it never had — a measurable proxy and an owner. **The cap is unchanged;** what was missing is
that it could not fire. One page had no number a worker could check, and growth was one-directional:
this ADR's own write-back mechanism only ever appends, and nothing said who removes a line, when, or
by what test. Every long-lived project reaches the cap and then quietly exceeds it, because exceeding
it is nobody's job to notice.

**~30 lines** is the proxy — roughly twice the template `reference/repo-claude-md.md` ships, which is
what a filled-in instance of that template runs to. It is a rendering of "one page", not a new
allowance. **The trim is enforced at write time by whoever is writing:** a write-back that would cross
the cap also drops the line it most clearly supersedes, or otherwise the stalest gotcha — never a
separate cleanup pass, because a pass with no trigger and no owner is how the cap stopped binding in
the first place. Gotchas are the eviction default because they are what the write-back mechanism
grows fastest; Commands and the copy-list are what a cold worker cannot function without.

Recorded here rather than left in the reference file's prose alone, because a future session wanting
to move the number needs the reasoning, not just the number. `reference/repo-claude-md.md` carries the
operative wording.

**Amendment (2026-08-25, see 0037):** the "Gotchas" kind admits one more instance — **a cache or
deploy root the repo uses outside its own tree** (`~/.cache/foo`, `/srv/app`). It is an environment
gotcha of exactly the kind already fenced — a fact about the machine a clean-context worker needs so
it does not invent its own location for a download or a deploy (0037, `reference/out-of-repo-writes.md`)
— the same shape as "port 3000 is taken", recorded here rather than as a new kind, following the
2026-08-06 amendment's precedent of placing new content inside an existing kind. The three-kinds
fence and the one-page rule are unchanged.

**Amendment (2026-08-25, see 0038):** this ADR's Rejected line drops `AGENTS.md (double-injection —
already rejected and the reason still holds)`. That rejection was of `AGENTS.md` as *this method's
operational-memory channel* on Claude Code — and it stands: `CLAUDE.md` remains that channel. 0038
introduces a repo-root `AGENTS.md` for a *different* purpose — the Codex-side forced-read *delivery*
pointer (a Codex plugin has no session-start hook; measured) — so a repo using DevStandard on both
harnesses now carries both files. The double-injection concern does not transfer: **measured, Claude
Code does not read `AGENTS.md` at all when a `CLAUDE.md` is present** (a sentinel in each; only the
`CLAUDE.md` one loaded), and even were a future Claude Code to read it, that `AGENTS.md` holds no
operational memory of its own — it only redirects to the same `core.md` the hook already force-reads.
So the worst case is a redundant read of already-loaded content, never the *second, conflicting*
injection this ADR's double-injection concerned. The two channels stay separate, exactly as this ADR
intended — `CLAUDE.md` is Claude's memory, `AGENTS.md` is Codex's delivery redirect.
