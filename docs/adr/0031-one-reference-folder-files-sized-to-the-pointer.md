# 0031 — One `reference/` folder, and a file is as big as the pointer that asks for it

Status: Accepted (2026-08-07). Amends 0007 (the `howto/`/`aids/` split it created).

## Context

0007 gave the plugin two on-demand directories and a stated division: `howto/` is *"read when their
artifact is due"* — how to write a document the project will hold, with a template — and `aids/` is
*"optional, read when useful"* — text you paste into an agent.

**Two of the eight files already violated it**, and the larger violation was the largest file in the
plugin:

- `aids/worktree-lifecycle.md` is a checklist you follow, not a prompt you paste.
- `howto/cicd.md` was 3,849 words, of which **2,344 (59%) were merge discipline** — "Driving a PR to
  green" and "When CI cannot run at all". Neither is a template and neither produces a document. A
  session at merge time opened a file named `cicd.md` to find the review rules.

And for the six that did fit, the division **produced no behaviour**: both directories are read the
same way — `core.md` names a file, the agent reads that file — and both resolve against the plugin
root by the same hook declaration. **It was a classification, not a distinction.**

The sharper defect was underneath it. `howto/cicd.md` was the target of **four separate `core.md`
pointers, each wanting a different section**: the setup reading list wanted the CI and release
templates; the PR-ownership rule wanted "Driving a PR to green"; the CI-fallback rule wanted "When
CI cannot run at all"; the red-main rule wanted "When CI goes red with no change of yours". **Every
one of them cost 5,196 tokens to answer**, because an agent reads a file whole.

## Decision

**One directory, `reference/`.** The `howto/`/`aids/` split is retired: it named a difference that
made none.

**And a file is as big as the smallest thing a pointer asks for.** `howto/cicd.md` is split at the
seams its own section headings already marked — no judgement call was needed, no section straddled a
boundary:

| New file | Words | Answers |
|---|---|---|
| `ci-pipelines.md` | 1,245 | the setup reading list; the short-branch/protected-main lane; the pipeline-ageing path |
| `driving-a-pr-green.md` | 1,042 | "opening a PR isn't done" |
| `ci-cannot-run.md` | 1,226 | the check-2 fallback |
| `repo-claude-md.md` | 350 | the repo-root `CLAUDE.md` a project generates, and the worktree copy-list |

**What each pointer now costs, against 5,196 before:** red-main → 1,680. PR-ownership → 1,406.
CI-fallback → 1,655. The worktree copy-list, reached from `reference/worktree-lifecycle.md`, →
**472**.

**The principle, which is the part worth keeping:** *granularity follows the pointer.* Consolidating
would have gone the wrong way — merging the eleven files into one costs **14,030 tokens for every
read** — a **14.2×** amplification on a reader who wanted the ADR template (986) or the worktree
checklist (978). The reason these files are cheap is not that they are small; it is that **nothing
reads them until `core.md` points at one.** Fewer, larger files spend that property; more, smaller
files bank it.

Rejected: (a) **one file** — the arithmetic above; (b) **three or four files grouped by when they
are read** (setup / per task / merge) — better names than today, but a worker wanting the worktree
checklist would pay 5,138 instead of 978, so it buys tidiness with the exact cost this ADR exists to
reduce; (c) **keep both directories and only split `cicd.md`** — leaves a classification that
produces no behaviour and that two files already contradict.

## Consequences

**Twenty-one pointers were re-aimed**, nine of them at `cicd.md`, and **seven of those nine now name
a file whose name they did not previously contain** — the shape in which a stale pointer hides. The
`@path` CI gate, `docs/architecture.md` §2's tree, `docs/PRD.md`'s on-demand claim, `README.md`'s
layout block and `CLAUDE.md`'s own command all moved with them.

**The split broke eight intra-file cross-references and that is the real hazard it carries.** Phrases
like *"the section above"*, *"the fallback below"* and *"the CI template above"* were true inside one
3,849-word file and false the moment it became four. All eight are now explicit paths. **A future split
of any long page must sweep for relative references before it sweeps for pointers** — the pointers
announce themselves in a grep; the relative references do not.

`core.md` is unchanged at **4,387 tokens** — this ADR moves no rule and rewords none. That is
deliberate: the exception-path sinking (`core.md`'s CI-fallback, red-main, architecture-change and
safety blocks, ~561 tokens of rules most sessions never reach) is the next change and lands *into*
the files this one creates. Doing them together would have meant re-aiming the same pointers twice.

**And the dual of the principle, learned by breaking it in this very change:** granularity follows
the pointer, so **a carved-out file needs a pointer from every path that used to reach it**, not just
from the one that motivated the carve. `repo-claude-md.md` was reached at setup only because the
section heading inside `cicd.md` said *"(generated in the same setup step)"* — an instruction carried
for free by adjacency. Carving the file out deleted the adjacency and the instruction with it, and
check 1 caught that no path remained that told a repo-creation session to generate the file at all.
`ci-pipelines.md` now hands off explicitly.

What to watch: whether `reference/` accumulates files **no pointer reaches** — reachability, not
direct naming by `core.md`, because the paragraph above establishes that two hops are a legitimate
route (`core.md:11` → `ci-pipelines.md` → `repo-claude-md.md`). A file nothing reaches is not
on-demand — it is unreachable, and the rule that put it there has no reader.
