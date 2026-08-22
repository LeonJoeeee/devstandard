# 0034 — A rule stated where work is commissioned is not obeyed where the work arrives

Status: Accepted (2026-08-17). Amends 0022 (the publication half of ceremony gains a delivery-side
statement; the rule itself, both gates, their order, and every verdict semantic are unchanged).

## Context

`core.md` has said since 2026-07-19 — commit `8596e71`, issue #32, seventeen days after 0011 — that
check 1's verdict lands as a comment on the PR before the merge, **because the review history must
be reconstructable from GitHub alone**; 0022's Decision records it as part of universal ceremony.
**0011 decides the two gates and never mentions publication**, which three review rounds of this
change took on trust before round 4 checked the log. The rule is resident on the
force-read page, it is unambiguous, and this repository broke it on **five consecutive merges across
two days** — #114, #116 and #117 on 2026-08-13, #119 and #121 on 2026-08-17 — twelve review rounds
between them, zero comments and zero reviews on GitHub for any of them at the moment each merged.

`gh api repos/.../issues/{114,116,117}/comments` returned `0` for each. PRs #107 and #108, merged
earlier, each carry one. **So this is a regression, not a gap that was never filled**, and the thing
that changed in between is where check 1 runs.

**The reviewer told the merging session, in writing, and the session did not act.** PR #114's round-2
verdict says, verbatim: *"Round 1's comment thread is not on the PR (GitHub shows zero comments and
zero reviews on #114), so I worked from the fix commit's own message, the PR description, and the
trees."* A clean-context reviewer reported the record missing and then worked around it from what the
tree still held — three sources, none of them the review it was owed.

**The cause is structural, and it is the finding worth keeping.** `core.md`'s clean-reviewer rule —
*"every review that gates progress … gets a clean reviewer: freshly spawned, no session history"* —
requires check 1 to run that way. A subagent returns its verdict **to the session that spawned
it, and to nobody else**. When check 1 ran inline, the verdict was already somewhere a human could
see; once it moved into a subagent, publishing became a separate act that nothing prompts.

> **The rule is stated at the point where the review is *commissioned* — inside a paragraph about
> spawning reviewers — and the act it demands happens at the point where the review *arrives*.**

The cost stopped being hypothetical on the first day: the session running those reviews **was
compacted between #114 and #116**. The seven rounds up to #117 — including a Critical that found a CI
gate green on the very defects it was built for — existed nowhere but a context that had already lost
part of itself once. **The 2026-08-17 pair is the sharper evidence, and it points elsewhere:** by
then this issue was filed and the whole diagnosis was in hand, and #119's and #121's verdicts still
went up **40 and 4 seconds after their merges**. Knowledge at dispatch was maximal; the act still
missed the moment.

## Decision

**The instruction has to arrive with the verdict, so it goes inside the prompt.**
`reference/code-review-prompt.md`'s `## Rules` block now tells the reviewer to close with, verbatim,
*"Post this verdict whole on the PR before acting on it."* Twenty-two words in the fence, paid by
every reviewer's prompt, and they buy the one thing nothing else on the path can: **a sentence that
reaches the merging session at the instant the act falls due**, rather than one it read when it
dispatched.

**The dependency, stated because it is real:** this works only if the commissioning session pastes the
fence whole. A bespoke brief that keeps the output format and drops the rest drops the safeguard with
it — and the session writing that brief is the actor this ADR has just called unreliable at exactly
that moment. The evidence from this change runs both ways and the second half is the important one.
**Obeyed when read:** every check-1 round on this PR *after the line existed* closed with it, and each
said its own brief did not contain it — they had read the fence **in the diff under review**. (The
line was added by this PR's own first fix commit; the round before that fix cannot be counted either
way.) **Delivered: not once.** The commissioning session has dispatched check 1 repeatedly over this
change and pasted the fence on none of those dispatches, writing a bespoke brief every time. So the
precondition the mechanism rests on has failed on every opportunity so far, in the change that created
it, at the hands of the actor this ADR calls unreliable at exactly that moment. That is the strongest
thing this ADR can say about itself, and it belongs here rather than in a footnote.

A second statement stays above the prompt body, for the session filling the placeholders — it says
what the duty is, says outright that reading it there is not when the act falls due, and prescribes
the comment heading (`## Merge check 1 — round N`) so the published record is greppable and a
pre-merge check can find it. **That is a deliberate duplication**, not an avoided one: 0032 prices a
rule stated twice, and this rule is worth the price because one statement addresses the reader and
the other reaches them at the moment.

**`core.md` is not touched.** Its statement is the rule and the trigger, and it is correct as written;
what was missing was never a rule, it was an *address for the action*. Adding words to a page every
project reads every session, to fix a step that has a natural home in a file already open at that
moment, would be the failure ADR 0032's rule 2 exists to prevent.

**Publishing after the merge is a legitimate repair, and is required rather than optional** — but only
if it announces itself. The alternative, leaving the record empty because the moment passed, protects
nothing and loses everything the rule exists for. **The header is the whole difference**, and it has to
name both times: when the comment was posted and when the PR merged. A header that says only *"posted
by the merging session, per core.md's requirement"* reads as compliance, and five of the twelve
recovered verdicts went up wearing exactly that before check 1 caught it (Consequences).

**Rejected: a CI gate asserting the PR carries a check-1 comment — and not because one cannot be
built.** 0028's objection (*"a presence check wearing a correctness check's name"*) does **not**
apply: this rule's content *is* co-presence, so such a check would wear its own name honestly. Nor
is timing the obstacle: `on: [pull_request, issue_comment]` with a `checks.create({head_sha})` call
attaches a run to the head that branch protection matches, and being red until the PR does the thing
is what every gate does. **The reason is cost and audience.** The gate would live in
`.github/workflows/`, which is not shipped, so target projects inherit nothing from it; a pre-merge
command in this repository's `CLAUDE.md` buys the same assurance for one line. And presence is all
either instrument can check — a gate and the command alike see that *a* comment exists, never that
it is the verdict for the diff being merged. That is a limit of checking presence, not an argument
for one over the other, and it is worth knowing before anyone trusts either.

Rejected: **stating it in `core.md` as well.** Not because a second statement is forbidden — this
change deliberately makes two — but because neither of `core.md`'s readings helps: it is read at
session start, further from the moment than either statement above. Rejected: **leaving it to
discipline** — five consecutive merges, the last two with the diagnosis already written, are the
evidence against.

## Consequences

`reference/code-review-prompt.md` pays 141 words: **22 of them inside the fence**, on every
reviewer's prompt, and 119 above it on a path read once per merge. The 22 are the expensive
ones and the ones that do the work.

**What to watch, first:** the heading convention this change adds is itself delivered at commission
time — `reference/code-review-prompt.md`'s paragraph prescribes `## Merge check 1 — round N`, and
the in-fence line says nothing about the title. A session that pastes the fence whole still learns
the heading only from above it. The failure mode is a false red on a pre-merge check rather than a
lost record, so it is recorded rather than fixed; but it is this ADR's own defect class, applied to
this ADR's own rule, one page later.

**What to watch, second:** the same shape, elsewhere. The defect class is *a rule stated at
commission time whose action falls due at delivery time*, and the trigger for it is any step this
method moved into a subagent. The design challenge on issue #91 is the other instance already
visible — six lenses proposed pointing a reader at a file none of them opened, and the fix landed
only because a refuter's brief sent it to the target rather than the pointer. **When a step moves
into a subagent, ask where its output has to land, not just what it has to say.**

The recovered verdicts are on the five PRs, and **all twelve now state both times** — when the
comment was posted and when the PR merged — which is what the standard above requires. **None of
them did at first, and it took two review rounds to get there.** Round 1 found that five carried a
header saying only that they were *"posted by the merging session, per core.md's requirement"*,
which reads as compliance with the rule it had just broken. Round 2 then found that the other seven,
untouched since the day they were posted, gave a date and no times at all — so the sentence claiming
the record was uniform was false a second time, about the seven this time; they were corrected after
that round. **A repair is a repair only if it says so, and saying so is harder to get right than it
looks.**

That closes the record and not the defect. Whether the defect is closed is not something this ADR can
assert — the next merge is the first test, and the test is whether the verdict is on the PR before
the fix round rather than after the merge.
