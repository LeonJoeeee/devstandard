# 0030 — A practice useful only for maintaining this plugin lives in its repo `CLAUDE.md`, not in the shipped pages

Status: Accepted (2026-08-06). Amends 0027 (its rule is withdrawn from the shipped method and
kept as repo practice), 0022 (the second doc-duty pass it added), and 0018 (this repo carries a
root `CLAUDE.md` again).

## Context

The human drew a line this method had never stated: **the rules we use *to build* DevStandard
and the rules DevStandard *ships* are two different things, and an observation from the first
does not become a rule in the second.** Nothing in the review discipline asked that question —
every check-1 prompt asked whether the text was correct, complete and internally consistent,
never whether the rule belonged. Fitness-for-audience had no slot.

ADR 0027's two-pass sweep is the clearest instance. It was derived entirely from maintaining
*this* repo — six recorded cases (issue #79), all of them prose in a methodology project — and
then written into `core.md`, the page every session of every project is forced to read. Its
cost, measured across the three shipped pages:

| Page | Cost | Read by |
|---|---|---|
| `core.md` | **162 tokens** | every session, every project, forced |
| `aids/worker-brief.md` | 282 tokens | every dispatched worker |
| `aids/code-review-prompt.md` | 238 tokens | every check-1 reviewer |

**The defect it prevents is invisible only where the product is prose.** Rename a function and
the compiler names every caller; change an interface and the tests go red. Reword a rule and
nothing responds — which is a fact about this repo, not about software projects. A target
project building an application hits it rarely; we hit it six times in one PR.

Two symptoms had already been filed separately and are closed by this: the shipped checklist
enumerated *this plugin's own directory layout* — "the aids, the howtos" — to readers who have
neither (#87), and the whole question of whether the rule belonged (#90).

## Decision

**The sweep rule is withdrawn from the shipped method**, in all three places, together with the
five pointers that referenced it from `core.md`'s flow step and worker DO list, and from
`aids/worker-brief.md`'s DO list and Done line. `core.md` returns to **4,380 tokens**, its
v0.15.0 figure minus the rule.

**It is kept, operative, in a repo-root `CLAUDE.md`** — which does not ship, which no shipped
page points at, and which only a session opened on *this* repository reads. The rule is real and
it earns its keep here: it caught three separate defects during the 0028/0029 work alone.

**And the general form, which is the part worth having:** *a practice useful only for
maintaining this project lives in the repo `CLAUDE.md`; the shipped pages carry only what a
target project needs.* This is the first artifact of the repo-ops/method distinction, and it
gives the distinction somewhere to live instead of being re-derived per change.

**The release delegation moves in with it.** Issue #37's standing delegation of per-release
approval had lost both doc homes it was given — the repo `CLAUDE.md` deleted in v0.12.1 and the
CHANGELOG header deleted in 0029 — leaving it reachable only by grepping the ADR log (#100, and
the reviewer of PR #101 confirmed the index does not lead to it). It belongs in exactly the file
this ADR re-creates.

**0018 is satisfied, not overridden.** 0018 as amended prescribes a repo-root `CLAUDE.md` when a
project has something operational to declare, and recorded that this repo then had nothing
unique. That was true in v0.12.1 and is no longer: it now has two declarations that exist
nowhere else.

Rejected: (a) **split the rule** — keep the "why" in `core.md` (~20 tokens) and move the
procedure to `howto/` — the author's recommendation, and the human's first instruction. Rejected
by the human on reading the full text: *"这里面的东西对于我们做别的东西都没有用"* — the whole
clause, not merely its procedure, is about maintaining this project. Keeping a 20-token stub on
the forced-read page would leave a rule with no operative content for its stated audience.
(b) **Delete it outright, keeping only ADR 0027 as history** — knowledge preserved, practice
lost: no agent reads an ADR at the moment it reworders a rule, so the three failure modes would
return. (c) **Keep it in `howto/`** — still ships, still names our directories, still asks a
target project to carry a page it does not need.

## Consequences

`core.md` regains **180 tokens** (4,560 → 4,380), and the two aids lose 520 more that every
worker and every reviewer was carrying. The shipped surface now states nothing about `aids/` or
`howto/` as places a *target project* should search, which closes #87 as a side effect rather
than as its own change.

**What is lost, and it is not nothing:** the reviewer no longer has a check item for this, so
the failure mode's backstop is gone from the one party that caught most instances. In this repo
that is covered — check-1 reviewers are dispatched from here and this `CLAUDE.md` is in their
session's repo. It is not covered for a target project, which is the point: the rule was never
theirs.

**Deleted with it, and flagged rather than smuggled:** the reviewer check item carried a clause
that *"a rewritten ADR body is Critical"* — a check on `howto/adr.md`'s supersede-never-edit
rule, which is shipped method and survives this change. Removing it removes a real check on a
surviving rule. It is a separable question and is left for check 1 to rule on rather than
decided here.

What to watch: whether the repo `CLAUDE.md` accumulates. It has two entries and a stated
admission test; a third that fails that test is the signal that this file is becoming the
dumping ground the shipped pages just stopped being.
