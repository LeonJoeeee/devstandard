# 0054 — A task's bounds bound what a worker writes, not what it traces

Status: Accepted (2026-09-10)

**Scope: this ADR decides what the method ships.** `reference/worker.md` carries the operative
wordings and `docs/PRD.md`'s Workflow 3 states the same reading, so a project seeded with
DevStandard inherits this rule for its own dispatched work. It is not a repository-maintenance
practice.

## Context

DevStandard binds three superpowers skills to the worker role. One of them,
`superpowers:systematic-debugging`, tells a worker where a fix belongs: **"Fix at source, not at
symptom"** (its data-flow tracing step) and **"Fix the root cause, not the symptom"** (its
implementation phase). The worker page's Never list said: **"Touch files outside the task or edit
another worker's branch."**

Those two collide whenever tracing lands the cause in a file the issue's Bounds does not name, and
no sentence decided the collision. What did decide it was the worker page's skill-sovereignty rule
— *apply this role and the accepted task over conflicting plugin skill rules* — which resolves the
conflict toward the role page and therefore toward a patch at the symptom, inside the bounds.

Check 1 cannot catch that outcome. A symptom patch inside the bounds satisfies the Goal verdict
(the issue's goal, achieved within its bounds) and passes Floor 2, whose failure mode is
*out-of-scope* work; a patch that stays in scope is invisible to it by construction. So the method
had a path to a plausible-but-wrong change on main that every gate would wave through — the
goal-drift pain point the PRD names.

No lane had hit it. This records the human's ruling before an incident rather than after one, on
2026-09-10: a worker should chase the root cause whether or not it lies inside the task, because
the point is to solve the problem, not to assume the dispatched instruction is right; when the
instruction is wrong the worker says so and asks whether the task should be recalibrated.

## Decision

**A task's bounds bound what a worker writes. They never bound what it reads or traces.**
Investigation follows the cause wherever it goes.

**A root cause outside the bounds is returned, not resolved.** It goes on the issue with its
evidence and with the question whether the task should change, and the lane waits for the
orchestrator's recalibration. This joins the worker's existing stop triggers; escalating is never
held against the worker.

**Both shortcuts are the failure the page already names.** Patching the symptom inside the bounds,
and silently fixing the cause outside them, are each the "guessing and shipping plausible-but-wrong
work instead of saying so" that the worker page's escalation paragraph forbids — the second is also
the out-of-scope work Floor 2 fails.

**The bounds are not presumed correct.** They were drawn before anyone traced the problem. A worker
that has traced it knows something the dispatcher did not, and returning that is the worker's job,
not a challenge to the orchestrator's authority.

Rejected:

- **A "one exception" clause on the skill-sovereignty sentence.** It would make that sentence a
  third site for one rule and invite a fourth; the collision is decided where the bounds are stated
  instead. Sovereignty is unchanged: the role page still wins, and it now says what winning means
  here.
- **A new row in the orchestrator's event table.** The orchestrator's escalation ladder already
  receives a worker stop with evidence and already decides recalibration; a row per newly-named
  trigger is the exhaustive enumeration the page-audit rules warn against.
- **A hook, guard or test change.** Nothing mechanical can tell a symptom patch from a fix, so
  enforcement would be theatre.

## Consequences

`reference/worker.md` carries the operative wording in four places: its Never list now forbids
*changing* files outside the task's bounds rather than *touching* them; "Execute the accepted
design" says the boundaries bound what you write, never what you read or trace; "Stop and return to
the orchestrator" lists a root cause outside the bounds among its triggers and states what returning
one looks like. `docs/PRD.md`'s Workflow 3 says to change only what is in the task's scope and to
trace wherever the cause leads.

What gets better: the one path to a gate-passing wrong change that the review floors cannot see is
closed by the worker's own rule, and an orchestrator gets told when its bounds were drawn wrong —
which is information it can get no other way.

What it costs: a lane that finds an out-of-bounds cause stops and waits, so the work takes a
recalibration round instead of a commit. That is the intended trade.

What to watch: a worker with a weak trace has an incentive to call anything inconvenient an
out-of-bounds root cause. The evidence requirement is the check — a return without a traced cause is
an escalation the orchestrator should send back, not a recalibration.
