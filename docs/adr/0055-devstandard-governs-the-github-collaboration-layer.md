# 0055 — DevStandard governs the GitHub-collaboration layer, and nothing below a role

Status: Accepted (2026-09-11). Amends 0051 (the definitions its 2026-09-11 block names).

**Scope: this ADR decides what the method ships.** It states the layer the method governs and
removes what v0.45.0 shipped below it, so a seeded project inherits both the scope and the removal.

## Context

v0.45.0 (#334) made the worker's helper review real: a third shipped agent definition,
`agents/helper.md`, a rule on `reference/worker.md` that every worker commissions one read-only
review of `git diff <named base>..HEAD` before handing back, spawn forms for both executors, and a
CI assertion pinning the worker body to the definition it commissions. The rule worked — the review
ran, cost one `opus` read per lane, and nothing in it was wrong.

The human's ruling on seeing it, 2026-09-11: the method governs one layer only, the collaboration
with GitHub. *"他有能力自己去发任何的 general purpose subagent……他愿意发啥发啥……我们这个只管一层，
也就是只管和 GitHub 协作的那一层。至于他再往下派，往往是不和 GitHub 协作的，只是帮他完成一件事的那种."*

What a role spawns beneath itself opens no issue, no PR and no review; it is invisible to the
collaboration record and to everyone but the role that spawned it. The addition was therefore three
rules — a named sub-agent, a required step, a test pinning both — spent on a layer the method does
not govern. ADR 0053's four questions did not refuse it, because the scope they would have been
weighed against had never been written down. That is the gap this ADR closes: not a bad answer to
the questions, a missing fixed point for them.

## Decision

**DevStandard governs the GitHub-collaboration layer — issue, lane, PR, review, merge — and nothing
below a role.** A role's own subagents are its own business: the method neither names nor requires
any of them, and a role spawns whatever helps it finish its task. What the method requires of a lane
is unchanged and is the whole of what it asks: **one accountable author hands back one PR**, whatever
that author delegated inside the lane.

Removed under that statement: `agents/helper.md`; `reference/worker.md`'s commission rule with its
Claude and Codex spawn forms, the one-writer-with-helpers sentence and *"Give reviewer helpers no
craft bindings"*; the helper's role map, hook map and worker-body assertion in
`.github/check-agents.py`; `core.md`'s *"worker helpers follow `reference/worker.md`"*;
`reference/external-agent.md`'s helper pointer, its gating-review row item, its definitions mention
and its Codex-internal-helper claim; `README.md`'s file-map line; and `reference/hard-edges.md`'s two
helper mentions, which fall back onto the general sentence already beside them — a subagent is bound
by the hook its own definition declares, or by the spawning session's where it declares none.

`reference/worker.md` carries the operative wording (ADR 0032 rule 2): one sentence of scope and one
of guidance, in place of the rule. This ADR states the scope for the log.

**What this does not touch: the gating reviews above a role.** Merge check 1 and the pre-code design
challenge are commissioned by the orchestrator, published on the PR, and gate a merge — they are the
governed layer, and their clean-reviewer properties (fresh, read-only, did not write what it judges)
stand unchanged.

**Rejected: keeping `agents/helper.md` as an optional definition** — "there if a worker wants it". A
shipped, named definition is the method reaching below the role whether or not a page requires it,
and it keeps its entry in the routing table, the CI gate and the hook map. **Rejected: replacing the
rule with softer guidance** — *"consider a helper review before handback"*. Guidance to spawn
something is still a rule about a layer the method does not govern, and it is the shape ADR 0053
tells an issue to price before adding.

## Consequences

The method loses its one guaranteed second read of a lane's diff before handback. Check 1 is
unchanged and remains the gate that decides whether a head is ready, so the loss falls on how much
work reaches it, not on what is accepted. If it turns out to matter, the evidence will be check-1
findings a pre-handback read would have caught — a main-line measurement, not a principle — and the
answer then is the worker's own judgment about what to spawn, which this decision leaves free.

Workers lose nothing they could do: a worker may still spawn a read-only reviewer of its diff, and
now decides for itself whether one is worth the cost in a given lane.

The scope statement is the test for the next addition: **if a proposed rule lands below a role, it
does not belong in the method.** It is stated on `reference/worker.md` and in `docs/architecture.md`
§1, and this ADR is where a future session finds why.

#334's live proof stays as history on that issue and nothing there is reopened; the shipped agent
definitions are `agents/worker.md` and `agents/reviewer.md`.
