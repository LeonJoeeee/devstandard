# 0032 — How *we* audit our own pages: a rule's weight must match how often a target project hits it

Status: Accepted (2026-08-13). Amends 0025 and 0026 (each chose to state one rule at several
sites at once; that choice is retained where it was argued and priced where it was not).

**This ADR decides how this repository is maintained, not what the method says.** Nothing here is
added to `core.md` or `reference/`, and no seeded project receives the rule. It is recorded as an
ADR because it changed the shipped pages and a future session will otherwise re-derive it. The
practice itself lives in this repository's root `CLAUDE.md` (0030's ruling on where repo-only
practice belongs).

## Context

The human, on 2026-08-13: *"你开发的是一个通用性的开发标准,它应该适用于开发所有程序,而不仅仅是用来开发
DevStandard。你现在把很多属于 DevStandard 自身的特定规矩和个例问题,写到了一个普适性、应用性的原则之上。"*

Two earlier passes had aimed at the same defect and missed it. 0030 withdrew the two-pass sweep
rule, which was derived entirely from maintaining this repo; issue #91's clean-context audit swept
`core.md` only, found one mis-scope, and declared the page clean. **`reference/` — **3.2×**
`core.md` by words — had never been audited at all.**

A clean-context audit of all eleven files was run and it corrected the framing twice, which is why
its verdict is trusted here:

- **The two files the issue accused were both cleared of the charge.** `ci-cannot-run.md` was
  written for target projects on private repos (issue #71 says so in its closing comment), not from
  our own pain; `driving-a-pr-green.md`'s trigger fires on 100% of tasks, since every PR has checks.
- **The worst offender was not on the list.** `reference/adr.md` spent 314 words — 43% of the file —
  on how to claim a free ADR number, an incident-shaped procedure with four places to look and two
  `git`/`gh` incantations. It passed the mechanical identifier scan only because it says *"this
  method's own log"* instead of an issue number. A normal project writes 5–15 ADRs ever and needs a
  *collision* on top of that; this repo has 32 in two months because its product is decisions. The
  cost when it does collide: two files numbered 0014, caught by `ls`, fixed with `git mv`. **Two
  hundred and fifty words away, the supersede-never-edit rule — the failure this repo calls
  irreversible — got 66.**

**The question that finds this class, and the reason the earlier audits could not:** they asked
*"is this rule true for a project that is not DevStandard?"* — and these rules are true, which is
why they passed. The question that works is

> **Is this rule's weight proportional to how often a normal project hits it, and to what it costs
> when they get it wrong — or to how memorably *we* hit it?**

## Decision

**Two rules for maintaining our own pages.** Both go in `CLAUDE.md`; neither ships.

**1. Weight is earned by frequency × cost-of-getting-it-wrong in a *target* project** — never by how
vivid the incident was here. `reference/worktree-lifecycle.md` is the calibration standard: it is
long exactly where the failure cannot be undone (84 words on the `git log @{u}..` no-upstream trap
before `git branch -D`), and it clears at its current length for that reason.

**2. A rule is stated in full in exactly one place; every other site carries the trigger and a
pointer.** The trigger must stay resident wherever the reader has to *recognise* the situation — a
reader who does not know a rule exists never opens the file that holds it.

The second rule is what the audit found underneath everything else. One incident was buying four
documents: the CI-fallback family ran to 2,005 words across five files, PR-green to 1,456 — **3,461
words for two recoverable, rare failures**, against 223 words for the two this repo itself calls
irreversible. 0025 and 0026 each chose the four-way statement with locally sound reasoning ("a
worker never reads `core.md`", "the reviewer becomes the only impartial party"). **Individually
correct; collectively a 4× multiplier on every rule born from an incident, with nothing in the
review discipline pricing the product.** 0030 found the same 4× shape in the sweep rule and withdrew
all three copies — but it withdrew *that rule*, not the pattern that produced it.

**What was changed, applying both:**

| Read path | Change |
|---|---|
| every merge (`code-review-prompt.md`, pasted) | the CI-fallback audit was unconditional two lines below a placeholder reading `NONE`. The checklist moved to `ci-cannot-run.md`, to be pasted *with* the evidence when the fallback fires. |
| every task (`worker-brief.md`, pasted) | the near-verbatim red-check copy replaced by trigger + pointer; the 646-word DO/NEVER block restructured from two semicolon-chained run-ons into lists — **no words cut, and the single most valuable change in this diff.** |
| 100% of tasks (`driving-a-pr-green.md`) | same. |
| 5–15 times ever (`adr.md`) | number-claiming cut 314 → 106 words; the incantations to `CLAUDE.md`. |
| rare, usually correctly declined (`ci-cannot-run.md`) | **grew.** The branch that is almost always right — *wait* — was never stated anywhere in the file, while *"you would rather not wait"* sat in the non-trigger list, reading as pressure against it. It is now the opening section. The five non-trigger paragraphs — 364 words — are now a 222-word table, because they all resolved on one test that is now stated once above it. |

**A new file, `reference/red-check.md`,** holds the three-states rule that `driving-a-pr-green.md`
and `worker-brief.md` had been carrying near-verbatim.

**Deviation from the audit's own prescription, recorded because it matters:** the audit said to cut
the rule from `driving-a-pr-green.md` and keep it in the brief, on the ground that the brief is
pasted into a prompt and so a pointer is weakest there. That is right about the brief and does not
price the other end — it would leave `driving-a-pr-green.md` pointing at a 2,209-word file to answer
a 218-word question, the amplification 0031 exists to prevent. A file sized to the pointer serves
both: **338 words instead of 810 or 2,209.** 0031's principle decides between two sites the way it
decides between one file and four.

**Not changed, and the ruling matters as much:** `core.md`'s exception blocks all clear at their
current size. They are triggers and gates, not procedures — an agent that does not know the CI
fallback exists never opens the file, and one that does not know a revert may skip check 1 never
looks for permission. The bloat was downstream, in the files, not on the page. `worktree-lifecycle.md`,
`prd.md`, `architecture.md` and `repo-claude-md.md` clear completely.

Rejected: **(a) ship rule 2 in `core.md`** — its whole evidence base is our own doc set, which is
exactly the reasoning 0030 used to withdraw the sweep rule; shipping it would repeat the defect this
ADR exists to close, and `core.md` already obeys it. **(b) Delete `ci-cannot-run.md` down to a
paragraph** — the issue's opening theory. The audit disproved its premise: the rule was written for
target projects on private repos, and its length now sits in the one file nobody reads unless the
platform is actually down. **(c) Cut the run-ons in `worker-brief.md` for length** — the defect there
is structure, not size; a cold worker's operating instructions are the last place to trade clarity
for words.

## Consequences

**The frequent paths got cheaper and the rare one got more expensive, which is the whole point.**
Measured against `daa1d03`: `reference/` is net **−152** words — but the three pages read at every
merge, at every task, and on 100% of PRs are **−463** between them, and `adr.md` a further **−208**,
against **+181** on the fallback file and **+338** for the new shared one. A total that moved a
little conceals a distribution that moved a lot.

**The next incident is priced at 1× instead of 4×.** That is the durable saving, and it will not
show up in any measurement of today's tree.

What to watch, and it is the honest risk: **rule 2 can be used to justify a pointer where the reader
needed the words.** The failure shape is a reader who does not recognise the situation, so never
follows the pointer — the exact reason `core.md`'s exception blocks were cleared here rather than
sunk. When the two rules disagree, rule 1 wins: a rule whose *cost of getting it wrong* is high stays
resident wherever it fires, however many times that repeats it.

Also worth watching: the audit priced something nobody had counted — **~326 words across the shipped
surface exist to manage one dependency's conflicting instructions** (`superpowers:writing-plans`
corrections, in five files). The audit ruled it the real cost of 0016 rather than a defect, and it is
recorded here so the next person to weigh that dependency has the number rather than an impression.
