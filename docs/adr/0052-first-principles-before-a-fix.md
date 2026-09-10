# 0052 — First principles before a fix: what went wrong, whether it is worth solving, and what could be removed instead

Status: Accepted (2026-09-10). Amends 0032 (a fourth rule for auditing this repository's pages).

**Scope: this ADR decides what the method ships** — two shipped pages carry its operative wordings,
so a seeded project inherits the rule. It also adds one repository-maintenance line beside ADR
0032's three page-audit rules in this repository's root `CLAUDE.md`; that line is repo-only, and it
is marked as such where it lives.

## Context

Between 2026-09-05 and 2026-09-10 (the window ADR 0051 records) the role hook accreted a layer per
review round, and every round's answer was another rule. The chain, by PR number:

| PR | What it added | Why |
|---|---|---|
| #240 | routine-command admissions inside the shell grammar | the grammar refused ordinary work |
| #248 | quoted literal patterns | the grammar mis-read quotes |
| #252 | a page rule separating a refused action from a rephrasable means (#246) | refusals halted workers |
| #302 | a seeded policy file, with a founding carve-out | the hook had to learn who the human was |
| #312 | a second, unparsed text scan for the orchestrator (#310) | the grammar gave up on some syntax |
| #317 | the CI gate's required checks read from that policy (#314) | the policy file now existed |
| #320 | a `cd <lane worktree> && …` composition rule (#318) | the worker page leads workers to that spelling |
| #321 | a missing-repository shape and a bounded transport retry (#303) | the remote policy read kept failing |

Each layer solved the previous layer's problem. Not one round — mine or a reviewer's — asked
whether the layer being repaired should exist. #315's stop signal for repeated findings did not
fire, and correctly so: the findings were not of the same shape, since each round found a genuinely
new spelling. The missing question was one level above the shapes.

The human ended it on 2026-09-10: *"每次遇到一个问题，考虑的永远不是'减'…最后去擦一大堆屁股"* and
*"很多工程师做的最蠢的事情，就是去优化一个本就不该存在的东西。"* #325 (issue #323) deleted the
grammar, the remote read and the authorization records in favour of one word list per role (ADR
0051), and issue #326's lane deletes the policy file and everything that existed to read it. Most
of what eight rounds built came out in two changes.

## Decision

**The fixed point an issue is judged against is its own project's main line — the goal and the pain
point that project's PRD states — never DevStandard's.** `reference/prd.md` is where that lives: its
first two sections are what this is and for whom, and why build it. For a research project the main
line is the question the study answers; for a product, what the product must do for whom; for *this*
repository, one human and one orchestrator getting reviewed changes onto main safely through
dispatched workers — one worked example, not the yardstick a seeded project inherits. Held against
someone else's end — ours, in a seeded project — the question answers *"no conflict"* every time,
which is the same as not asking it. Four questions are answered in an issue's Goal before it states
a goal:

1. What actually happened — observed, with the evidence.
2. Whether it conflicts with that main line.
3. Whether the problem is primary, or secondary to one.
4. Whether the fix, and the problems the fix itself creates, cost more than living with the problem.

**A secondary problem, or one whose fix costs more, is left unsolved on purpose, and the issue
closes recording that decision.** That outcome is the half of this decision that does the work:
without it, opening an issue already implies that something will be built.

Where a fix is warranted, the issue says what could be **removed**, or what **guidance at the point
of failure** would do — a refusal that explains itself is the hook's own example — before it says
what to add. An issue that adds a rule names what the rule guards and why guidance alone would not
do.

**The reviewer asks the same question first**, under the Goal verdict and before the boundary
clause: whether the issue answered those things, and so whether the change optimizes something that
should not exist. Where removing a rule, a layer, a file or a step, or leaving the problem unsolved,
would meet the goal as well, that goes in the Goal grounds and the Notes propose the smaller change.

**Where the operative wordings live** (one place each, ADR 0032 rule 2):
`reference/orchestrator.md`'s *Prepare the issue* holds the issue side; `reference/code-review-prompt.md`'s
Goal verdict holds the review side; and one line in this repository's root `CLAUDE.md`, beside ADR
0032's three page-audit rules, points here for the repo-maintenance side.

**Rejected: a fifth decision line, or a new verdict category, for "should this exist?".** Readiness
stays the Goal verdict and the two Floor checks (0044). A category would make the question blocking,
and a reviewer cannot rewrite an issue — the orchestrator closes that loop. **Also rejected: stating
the four questions in `core.md`.** The orchestrator writes issues and receives its own page every
session; `core.md`'s workflow line already names the issue's three sections, and a fourth statement
there is exactly the multiplier 0032 exists to price.

## Consequences

Writing an issue costs a paragraph more up front, and that paragraph is where a fix that should not
be built dies. The reviewer can now return *"this should not exist"* as grounds without failing the
PR: a PR that faithfully implements an issue that should not have been written still answers Yes on
the goal, with the observation on the record and the smaller change in Notes.

`reference/orchestrator.md` had 447 bytes of headroom under its 10,000-byte inline delivery cap at
`a30e4a2`, which is why the four questions are stated there in the shortest form that carries them,
and why the main line is glossed here — and its home named in `reference/prd.md` — rather than
spelled out on the page. The next addition to that page needs a headroom lane first; #316 and #319
are the precedent.

ADR 0051 decided the hook's own shape and is not revisited here. What this decision adds is the
question that would have reached 0051's answer six days earlier.
