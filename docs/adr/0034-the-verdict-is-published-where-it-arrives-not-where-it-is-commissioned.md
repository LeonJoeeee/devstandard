# 0034 — A rule stated where work is commissioned is not obeyed where the work arrives

Status: Accepted (2026-08-17). Amends 0011 and 0026 (the publication half of check 1 gains a
delivery-side statement; both gates, their order, and every verdict semantic are unchanged).

## Context

`core.md` has said, since 0011, that check 1's verdict lands as a comment on the PR before the merge,
**because the review history must be reconstructable from GitHub alone.** The rule is resident on the
force-read page, it is unambiguous, and this repository broke it on **five consecutive merges in one
day** — PRs #114, #116, #117, #119 and #121, twelve review rounds between them, zero comments and
zero reviews on GitHub for any of them.

`gh api repos/.../issues/{114,116,117}/comments` returned `0` for each. PRs #107 and #108, merged
earlier, each carry one. **So this is a regression, not a gap that was never filled**, and the thing
that changed in between is where check 1 runs.

**The reviewer told the merging session, in writing, and the session did not act.** PR #114's round-2
verdict opens: *"Round 1's comment thread is not on the PR (GitHub shows zero comments and zero
reviews on #114), so I worked from the fix commit's own message instead."* A clean-context reviewer
reported the record missing and then routed around it; the next round paid for that by reconstructing
round 1 from commit messages.

**The cause is structural, and it is the finding worth keeping.** `core.md:28` requires check 1 to run
as a *clean, freshly spawned* reviewer. A subagent returns its verdict **to the session that spawned
it, and to nobody else**. When check 1 ran inline, the verdict was already somewhere a human could
see; once it moved into a subagent, publishing became a separate act that nothing prompts.

> **The rule is stated at the point where the review is *commissioned* — inside a paragraph about
> spawning reviewers — and the act it demands happens at the point where the review *arrives*.**

The cost stopped being hypothetical during the same day: the session running those reviews **was
compacted between #114 and #116**. Twelve rounds of adversarial review — including a Critical that
found a CI gate green on the very defects it was built for — existed nowhere but a context that had
already lost part of itself once.

## Decision

**The delivery-side statement goes in `reference/code-review-prompt.md`, above the prompt body.** That
file is what the merging session has open at the moment it commissions the review, and the paragraph
sits outside the block that gets pasted into the reviewer — so it costs the reviewer's prompt nothing
and `core.md` nothing. It says: post the verdict the moment it comes back, whole, before the fix round
and before the merge; a reviewer you spawned returns to you and to nobody else.

**`core.md` is not touched.** Its statement is the rule and the trigger, and it is correct as written;
what was missing was never a rule, it was an *address for the action*. Adding words to a page every
project reads every session, to fix a step that has a natural home in a file already open at that
moment, would be the failure ADR 0032's rule 2 exists to prevent.

**Publishing after the merge is a legitimate repair, and is required rather than optional.** The
twelve verdicts were recovered verbatim from the session transcript and posted to all five PRs, each
under a dated header saying it was posted after the merge and why. The alternative — leaving the
record empty because the moment passed — protects nothing and loses everything the rule exists for. A
repair is not the rule, so the header is what keeps it from reading as one.

**Rejected: a CI gate asserting the PR carries a check-1 comment.** The obvious objection is 0028's —
it retired the en/zh mirror gate as *"a presence check wearing a correctness check's name"*. That
objection does **not** apply here: this rule's content *is* co-presence, so a presence check would
wear its own name honestly. **The real reason is timing.** CI runs on push; the verdict arrives after
the last push and is posted by hand. A required check that can only turn green on an `issue_comment`
event would sit red through every ordinary review round, and a gate that is red in the normal case
teaches sessions to route around it — the precise behaviour PR #114's round-2 reviewer demonstrated
against a rule with no gate at all. **A pre-merge command, run by the merging session, is the right
instrument** and lives in this repository's `CLAUDE.md`, not in the shipped method.

Rejected: **stating it in `core.md` as well.** The page already carries the trigger; a second
statement is the 4× multiplier 0032 exists to price. Rejected: **leaving it to discipline** — five
consecutive merges are the evidence against.

## Consequences

`reference/code-review-prompt.md` pays 71 words on a path read once per merge, by the session that is
about to act on them. Nothing else in the shipped surface moves.

**What to watch: the same shape, elsewhere.** The defect class is *a rule stated at commission time
whose action falls due at delivery time*, and the trigger for it is any step this method moved into a
subagent. The design challenge on issue #91 is the other instance already visible — six lenses
proposed pointing a reader at a file none of them opened, and the fix landed only because a refuter's
brief sent it to the target rather than the pointer. **When a step moves into a subagent, ask where
its output has to land, not just what it has to say.**

The recovered verdicts are on the five PRs. That closes the record and not the defect; the defect is
closed by the paragraph above, and the next merge is the first test of it.
