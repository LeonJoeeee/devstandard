# 0035 — A verdict's own quoted fix, or a fix that never touches the tree, does not re-run check 1

Status: Accepted (2026-08-17). Amends 0011 (the reviewed-diff-is-the-merged-diff rule gains two
narrow, evidenced exceptions; the rule itself, both gates, and every verdict semantic are
unchanged).

## Context

`core.md`'s rule is unconditional: any change to the diff after check 1 re-runs check 1, because
the reviewed diff must be the merged diff. Two situations expose a real cost in that rule that the
method has never separated from the risk it exists to prevent.

**Case 1 — the reviewer's own prescribed text.** PR #77's round 3 verdict cleared the PR with one
Minor and an exact replacement sentence quoted in the verdict itself. The worker applied that
sentence verbatim — one line, in an ADR. The round-4 reviewer then died on an API session limit
before producing a verdict, which `core.md` counts as a failure, not a pass. The merging session
merged anyway, disclosed the exception rather than claiming a verdict it did not have, and could
re-run the mechanical half of round 4's brief itself (finding nothing) but not the judgement half
— whether the prescribed sentence reads coherently in its paragraph.

**Case 2 — a finding against something outside the tree.** PR #85's round 3 returned *With fixes*
on one Important: the PR **description** still reported the pre-round-1 state, including three
clearings rounds 1 and 2 had already overturned. The reviewer prescribed exact replacement text and
said explicitly: *"Fix it with `gh pr edit` and merge; the diff needs no fourth review round, and I
would not spend one on it."* Applying it changed the description; `git diff` on the merged tree
before and after was empty. This is not case 1 — nothing in the merged tree changed at all, so
`core.md`'s reviewed-diff rule is not engaged in the first place. What actually blocks in this state
is the Critical/Important-findings-block-the-merge clause, and that clause is satisfied the moment
the finding — against the description — is fixed.

**Four design-challenge rounds on a combined spec covering both cases returned Survives-with-fixes,
Blocked, Blocked, Blocked** — each revision answered a round's findings by adding a mechanism, and
the mechanism generated the next round's findings. Round 4 recommended splitting delivery: state
what survived cleanly, decide the two remaining unsettled points here rather than in a fifth round
on the combined document.

**Decoupled from issue #83 on purpose.** #83 named the general question — what the method does
when check 1 itself cannot run — and was closed on the human's decision to remove the cause (a
subscription tier change eliminated the session-limit deaths that produced every instance). This
ADR's exception is **not conditioned on reviewer availability**: keying it to unavailability would
create the one incentive the whole design has to avoid — an agent that wants to skip a round
reaching for "the reviewer was unavailable" as the trigger. Because it is unconditioned, #83's
closure does not resolve it and this ADR does not depend on #83's cause being real or fixed.

**The abuse path, named because it decided the design.** "The reviewer suggested something like
this" is a short walk from "the reviewer prescribed exactly this." An exception keyed on the
implementer's own claim of verbatimness is self-certified — the same failure shape as issue #75's
instant-return doer. Both cases below are built so a later reader checks the claim from two SHAs,
never from an assertion.

## Decision

Two exceptions to *"the reviewed diff must be the merged diff"*, both narrow, both evidenced, both
independent of reviewer availability. Full text in `reference/code-review-prompt.md`; `core.md`
carries the trigger.

**1. Verbatim-quoted fix.** A blocking (Critical/Important) finding closes without a further round
if the fix is the verdict's own **quoted** text, applied byte-identical, and the diff contains
nothing else. **"Quoted", not "prescribed":** a reviewer writing *"and mirror it in Chinese"* with
no Chinese text written out does not qualify — the fix must be typed out in the verdict, not
gestured at. Any adaptation, however small, voids the exception: the changes that need judgement
are exactly the ones that lose it. Evidence: both SHAs, and the diff showing the applied text
matches the quoted text after removing only the code-fence indentation the verdict's own markdown
added — nothing else is collapsed or normalized, which keeps a Markdown-significant blank line or a
trailing hard-break intact rather than destroyed by a looser comparison.

**2. Tree-unchanged fix.** A finding against something outside the merged tree — most commonly the
PR description — is closed by editing that artifact. `core.md`'s reviewed-diff rule is not engaged
at all, because the diff never changed: `git diff <verdict-SHA>..<merge-SHA>` on the tree is empty,
published as the evidence. **Caveat, found in round 4: an amended commit message is not covered
even though the tree's files are unchanged** — it rewrites text the record-language check reads, so
it is a change to the record and re-runs check 1 like any other.

**Neither exception is available because a reviewer is unavailable, slow, or expensive to
re-dispatch.** Availability is never the trigger for either. A finding described but not quoted, a
fix needing one word of judgement, a second file or line riding along, any doubt about which case
applies — re-runs check 1, whatever the size of the change.

Rejected: **(a) a single combined rule** — four challenge rounds on that shape each produced a new
finding from the previous round's fix; splitting into two independently-conditioned rules is what
stopped the cycle, because the two cases fail on different axes (case 1 on whether text was
adapted; case 2 on whether the tree moved at all) and a shared condition set kept licensing one
case's failure mode through the other's clause. **(b) keying the exception to reviewer
availability** — the incentive problem above; also makes the rule untestable by a later reader,
since "was the reviewer actually unavailable" is not something a diff can prove. **(c) folding case
2 under case 1's conditions** (treating a PR-description fix as a degenerate "quoted fix with an
empty tree diff") — case 1's conditions are about text-matching a quote; case 2 has no quote to
match against and is evidenced by tree identity instead, so forcing it through case 1's shape adds
a vacuous condition 1 is not designed to check.

## Consequences

`core.md` pays ~30 words for the trigger; the two rules in full live in
`reference/code-review-prompt.md`, read by the merging session at exactly the point it is deciding
whether a round is needed.

**What to watch:** whether "quoted" gets read loosely in practice — a reviewer who writes a long
prose description that happens to contain the right words embedded in it is not the same as a
reviewer who wrote out the replacement text as replacement text, and the line between them is a
judgement call the merging session has to make honestly, once, before either exception can apply at
all. If that line proves unworkable in practice, the fix is to tighten the definition of "quoted",
not to widen "adaptation" — loosening the latter is how this design failed four times before it
split.

The concrete cases behind this ADR — PR #77's round 4, PR #85's round 3 — are already merged and
are not reopened by this ADR; it is the rule the next such case gets, not a retroactive audit of
those two.
