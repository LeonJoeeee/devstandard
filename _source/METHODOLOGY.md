# Development Playbook (the MODEL layer / METHODOLOGY)

> **In one sentence**: the human is involved only at the highest level — the direction, and (for a complex task) the up-front brainstorm that breaks it into medium-sized pieces — and nowhere else. After that, for each medium piece the agent walks a single reference chain (`external world -> top-level design -> mid-level design -> low-level code`), checking each layer against the layer above it, and turns the requirement into code that meets a clear bar on its own. At the end of every iteration the agent judges its own work against a fixed "definition of done"; if the bar is not met it runs another iteration, stopping only when the bar is met or no further step is available.
>
> This file answers "what is the model, and why is each rule the way it is." It is the **single source of truth**.
> The step-by-step "how do I actually run this" lives in SKILL.md, which is a thin checklist that only points back here and never restates the criteria found here.

---

## Top rule: this method handles the INVARIANTS that sit above every requirement SHAPE

When a human hands a development task to an agent, **the requirement varies enormously**. Building a framework, adding a feature to an existing system, fixing a bug, doing a refactor, raising a numeric metric — these are all just **different SHAPES of a requirement**, not different methods.

**This method is not specialized for any one requirement shape.** What it handles is **the invariants that every shape shares, the things that do not depend on the specific requirement**:

- **The reference chain** — development is laid out as a single chain, `external world -> top-level design -> mid-level design -> low-level code`, and each layer is checked against the layer above it as its reference.
- **Three iterating layers plus adversarial review** — L3 picks the direction, L2 writes the mid-level design, L1 writes the code and tests; each layer is self-checked by "holding it up against its reference and looking for things that do not match."
- **A single human-decision altitude** — the human is involved only at the direction level; the approval point may fire at two moments, but both sit at that one altitude (a high-cost action inside L3, and the L3 -> L2 handoff; see §4). When the task is complex, that same altitude also covers the up-front brainstorm-split (see §0.5). Everything else is autonomous.
- **A definition of done** — before each task starts, a single, fixed "what counts as done" is settled, so the agent can judge for itself and stop on its own.

When a new requirement arrives, the approach is always the same: first see what shape it is, then run this same skeleton over it. **"What counts as done" is determined by the shape (you look it up in an open dispatch table, see §5), but the skeleton does not change by a single line.** When the requirement is too large to fit one run, the skeleton is preceded by a separate front-phase brainstorm-split into medium pieces (§0.5) and then run, unchanged, on each piece — the front phase sits before the skeleton, it does not add a step to it.

> **Why this is written at the very top**: almost every rule in this method holds true even though "the requirement varies." That is exactly what makes them invariants, and that is why they are fixed. Only a small number of actions are **specific to one particular shape** (the shape "improve a metric") — for example, "measure each candidate approach and keep the wins." Those are all gathered into a clearly marked appendix (§7) and must never leak into the main body. The reason this distinction is stated explicitly is to prevent anyone from later taking one class of requirement (most often "improve a metric") and generalizing the whole method from that one shape. **The main body recognizes only the invariants that sit above every shape.**

---

## Terminology (defined once here, used consistently throughout)

| Term | Definition |
|---|---|
| **L3 / L2 / L1** | Three abstraction layers. **L3 = the research layer** (pick the approach / set the top-level design). **L2 = the mid-level layer** (write the mid-level design, the SDD / pseudocode). **L1 = the implementation layer** (write the concrete code plus tests). |
| **Reference chain** | The chain `external world -> top-level design -> mid-level design -> low-level code`, in which each layer is checked against the layer above it as its reference (§1). This is the first principle of the method. |
| **Adversarial review** | One deliberate "find the flaws" check of a layer against its reference: locate every place in that layer that does not match the reference. The self-check at all three layers is the same action; only the reference differs. A **substantive issue** is one that, left unfixed, would make the layer diverge from its reference — a wrong or missing decision, a logic gap, an unhandled path — as opposed to wording or formatting; only substantive issues block a pass, minor findings do not. |
| **Definition of done (done-check)** | A statement of "is this requirement done yet" that the agent can **decide true-or-false mechanically, on its own**. It is not necessarily a number — it can be a set of tests, a behavioral contract, the state of a reproduction case, or a metric reading. It is the half of the contract that the human fixes when handing over the task. |
| **Requirement shape (shape)** | Which class a requirement belongs to (build a framework / add a feature / fix a bug / refactor / improve a metric / ...). The shape determines "which definition of done you self-judge against," but it does not change the skeleton. |
| **SDD** | Software Design Document = the product of the mid-level layer. One per pipeline; it is the single source of truth for that pipeline. The format is in §2. |
| **One iteration / the outer loop** | One complete pass that advances the same requirement: L3 decides the next step -> human approval point -> L2 -> L1 -> self-judge against the definition of done -> feed the result back up to L3 (§3). |
| **Human approval point** | Where the human steps in. It can fire at two moments — before a high-cost action inside L3, and at the L3 -> L2 handoff for a change that touches the top-level design — and only ever gates the **downward** direction; reporting results upward never goes through it (§4). For a complex task, the up-front brainstorm-split sits at this same single human-decision altitude, before the first iteration (§0.5). |
| **Brainstorm-split** | The front phase for an above-medium (complex / larger-than-one-service) task: a **human-plus-agent** brainstorm that decomposes the complex task into MEDIUM-sized pieces, each fitting one run / one context, then orders them by dependency. It is the method's first phase for a complex task, not a thing outside the method (§0.5). It is human-in-the-loop, not autonomous AI. |
| **Scaffold** | A device placed on each error-prone jump between abstraction levels, specifically to force the agent to think the logic through (research / pseudocode / tests). |
| **Slice** | A piece that L2 cuts a task into along its dependencies (S1 / S2 / ...). This is splitting **inside** a single medium task, done autonomously by the AI; it is a different thing from the **brainstorm-split** that decomposes a complex task into medium pieces (human-plus-agent, the front phase of §0.5). Do not conflate the two. |

---

## 0. Value proposition (why this beats just prompting an agent directly)

The way most people use an agent to develop is to do **only two layers, L3 and L1**: think of an approach, then write the code directly. There is no intermediate layer, the code is written in one shot, and "done" is judged by gut feeling. The result is that the high-level logic is too thick and too dense, and shallow logic errors slip through repeatedly.

**This method does exactly two things more than that:**

1. **It inserts a mid-level design layer (L2) between "the approach" and "the code."** Jumping straight from approach to code is one wide leap from the abstract approach to concrete code; when you cannot clear that span, logic gets dropped. L2 **breaks that one large leap into two smaller, crossable leaps** (approach -> mid-level pseudocode -> code), forcing the model to first work the logic through completely. In essence, this hardens "think it through before you write it" into a fixed step in the process.
2. **It wraps a goal-driven outer loop around L3/L2/L1.** It replaces "write it all in one shot and call it done by gut feeling" with "**at the end of each iteration, self-judge against the definition of done; if it is not met, run another iteration; stop only when it is verifiably done.**" This layer is what drives the work that remains after "you just think and hand over the requirement" — automatically completing the work and bringing it to a close on its own.

Those two — inserting L2, and wrapping the outer loop — are the entire difference between this method and the ordinary L3+L1 way of using an agent; everything else exists to make exactly those two additions run reliably. They are not, however, the method's first principles: the first principles are the reference chain (§1) and adversarial review against a reference, which both the ordinary way and this method would do well to obey. The two additions are simply where this method goes beyond ordinary practice.

---

## 0.5 Scope (how big a job this method handles)

The **scope of this method = a MEDIUM-sized task and above**. The method no longer refuses a complex or large task; it handles it by beginning with a brainstorm-split that brings it down to medium pieces. Three sizes, three responses:

- **LOW — skip the method, just do it directly.** A LOW-complexity task — a single simple file or function (for example, a basic random-number generator), a change you can confirm correct just by reading it, or a pure question / consultation whose output is an answer rather than code — does not need this machinery.
- **MEDIUM — run the method directly, one Executor pass.** A MEDIUM task spans multiple coupled modules or a pipeline — something you cannot fully grasp from just one or two files — and reaches at most roughly one service or module. That is the size a single run can handle, and it is the sweet spot: settle the done-check (Step 0) and run the outer loop (L3/L2/L1) over it in one Executor run.
- **ABOVE MEDIUM — begin with the brainstorm-split, then run the method per piece.** An above-medium task is complex or larger than a single service — for example, a whole multi-service project. A large project is a complex pipeline strung together from many MEDIUM-sized tasks (each one a full pass through L3/L2/L1). For such a task the **first phase of the method is a brainstorm-split**: a human-plus-agent brainstorm that decomposes the complex task into MEDIUM-sized pieces (each fitting one run / one context) and orders them by dependency. Then the method runs, unchanged, on each medium piece in dependency order.

So the overall shape for an above-medium task is:

```
brainstorm-split  ->  [ for each medium piece, in dependency order:  Step 0 (done-check)  +  outer loop (L3/L2/L1) ]
```

The brainstorm-split is the method's first phase for a complex task, not something "out of scope." But it is deliberately a **human-in-the-loop brainstorm** — the agent and the human do it together — rather than something the AI does autonomously. The three reasons below explain **why the split must be human-in-the-loop**, and they are also exactly why the split is what brings a too-large task down to context-fitting medium pieces:

- AI today **hits its ceiling at L3 (picking the approach / setting the direction)**; going further up — chartering a complex effort and decomposing it — is something it does noticeably less well, so a human must be in the loop on the split rather than letting the AI do it alone.
- **An LLM cannot be accountable for the outcome; the human is who is ultimately responsible.** For a large engineering effort, authority and accountability must match, so the decomposition of the whole must keep the human in the loop.
- The design of a complete complex task **does not fit in a single context** (even a million tokens is not enough). This is precisely why the front phase exists: the brainstorm-split is how a too-large task is broken down into context-fitting MEDIUM pieces, each of which a single run can then hold and handle.

**"The top level belongs to the human" is consistent at both scales**: inside a medium piece, the human stands at L3 (the direction, the human approval point of §4); for a complex task, the human is in the loop on the brainstorm-split that decomposes it into medium pieces. Same reason in both cases: accountability plus the AI's capability ceiling. This is why the front-phase brainstorm sits at the same single human-decision altitude as the direction — it is the highest-level decision, made together with the human, not handed off to the AI.

> **To stress it once more**: the **slicing** L2 does in §2 is splitting **inside** a single medium piece (AI, autonomous); the **brainstorm-split** this section describes is decomposing a complex task into medium pieces (human-plus-agent, the front phase). Both are part of the method now; do not conflate the two.

### Roles: Orchestrator and Executor

In a multi-window way of working, the front phase and the per-piece work correspond to two roles:

- **Orchestrator (the lead)** — runs the **brainstorm-split together with the human** as the method's front phase: holds the whole complex task, brainstorms with the human to decompose it into individual MEDIUM pieces and to order them by dependency, then hands each piece down in that order. Both the decomposition and the ordering are part of the human-plus-agent brainstorm, not an autonomous orchestrator decision.
- **Executor** — receives one MEDIUM piece and **runs the per-piece method (Step 0 + the outer loop L3/L2/L1) inside its own window**, turning that one piece into code that meets the bar.

For a MEDIUM-sized task that already fits one run, there is no front phase to run: it goes straight to an Executor. For an above-medium task, the brainstorm-split is the method's first phase, after which each medium piece is run by an Executor. The rest of this document describes how **one Executor runs inside one medium piece**.

---

## 1. First principle: the reference chain

```
external source ──check──▶ top-level design ──check──▶ mid-level design (SDD) ──check──▶ low-level code
```

- Each layer is checked against **the layer above it** as its reference; the reference for the topmost layer is the **external world**.
- The three "checks" are **the same action** (in every case "hold the thing up against its reference and find what does not match," i.e. adversarial review); only the reference differs.
- **The single definition of "this layer passes"**: a layer passes if and only if it is aligned with its reference — that is, **adversarial review can no longer find any substantive issue (no findings)**.
- **Feeding back upward**: when checking a layer, if the problem that surfaces actually lives in **the reference itself** (the layer above is wrong, not the layer being checked) -> **go back up one layer** and redo that upper layer.

---

## 2. The three abstraction layers / the three nested iterations

| Layer | What it does | Reference | Condition to pass this layer | How it is judged |
|---|---|---|---|---|
| **L3 research** | Pick the approach / set the direction (top-level design) | External world | The approach holds up against the external reference: shown best by desk comparison, or, when that cannot settle it, by actual measurement | Adversarial review (and, where review cannot settle it, actual measurement) |
| **L2 mid-level** | Turn the approach into a mid-level SDD (pseudocode) | Top-level design | "Nothing is left for L1 to decide, only to translate" + several (at least two) concurrent, independent, context-clean reviewers, each using a different lens, surface no substantive issue | Adversarial review |
| **L1 implementation** | Turn the SDD into concrete code | Mid-level design (SDD) | Tests written from the SDD all pass + it actually runs without errors | Tests actually run |

### L1 implementation (mid-level -> low-level)

- Its responsibility is **very narrow**: it only asks "did I faithfully translate the SDD into code, and does the code have bugs?" It does not touch any high-level decision at all.
- **This layer passes by actually running tests, not by adversarial review.** The agent designs its own tests against the SDD given by L2/L3; all tests green plus the thing actually runs without errors = this layer is done.
  - **Why this layer must actually run and cannot rely on review alone**: the code must at minimum be able to run without erroring, and "does it run" is something review (just looking) cannot tell you — only actually running it once can prove it. At the same time, because the tests are designed to capture the intent of the SDD, tests going green thereby also confirms that "the code is faithful to the SDD."
  - **What "actually runs" means for different kinds of modules**: anything with a runnable entry point (a service / CLI / pipeline) must actually be started and smoke-tested once; a pure library / pure-function module has no standalone entry point, so the equivalent of "actually runs" is "the test suite imports successfully and executes fully green." Do not let this criterion dangle on modules that have no entry point.
- The LLM is already strong at this layer — **but with a precondition**: only when L2 leaves no gap is L1 truly just "translation." The moment L2 leaves a gap, a design decision leaks down into L1, and L1 is forced to make a decision it should not be making, pulling it out of the kind of work it is genuinely reliable at.

### L2 mid-level (top-level design -> mid-level SDD)

- It is **the bridge that carries L3 down to L1**, so by nature it **faces two ways**: facing up, it must faithfully deliver the approach (it is checked by the top-level design); facing down, it must be concrete enough for L1 to write straight from it (it is itself the reference for L1).
- **The sharp passing criterion**: **write until "there is nothing left for L1 to *decide*, only to *translate*."** Every place where L1 would still have to make a judgment call is a place where L2 still has a gap — and that gap is exactly a "high-level -> low-level" leap that was not broken down cleanly.
- L2 is also responsible for **slicing**: once the top-level design is settled, L2 cuts the task into pieces along its dependencies (S1 / S2 / ...) and writes an SDD for each piece. A small task reduces to a single slice.
- The mid-level design is a "non-runnable design document"; it cannot be tested by running it, so the only way it passes this layer is through **adversarial review by context-clean subagents working from several different lenses**.
  - **Why it must be clean subagents**: whoever writes this layer is anchored by their own thinking and cannot see the gaps they left; only a subagent that did not take part in writing it, and whose context is clean, can pick at it objectively.
  - **The review gate is a single pass with several (at least two) concurrent, independent, context-clean reviewers, each using a different lens.** They run at the same time and do not share state. **If they surface no substantive issue, the layer passes.** If they do surface a substantive issue, fix it and re-review — this is ordinary use of review feedback, not a fixed number of mandatory re-review rounds. Use more reviewers, or more lenses, when this layer carries more risk or complexity.

### L3 research (external world -> top-level design)

- Pick the approach. The reference = the external world, which is **not in hand**; you have to actively reach out and fetch it:
  - **Desk research (purely consulting the literature / state of the art / comparable systems, without running your own experiments)**: pull them in and compare (cheap; take this route first by default).
  - **Actual measurement**: when a paper comparison cannot decide it, build a thin spike and measure it on your own data (expensive).
- **Actual measurement upgrades "passing this layer" from "a review judgment" to "a hard, objective measurement"** — this is L3's decisive tool when the stakes are high and review alone cannot settle the question, and it is also why "actual measurement" lives at L3.

### The SDD format (what L2's product looks like)

A standard SDD = an HLD view (WHAT) + the §6 pseudocode LLD (HOW). One `*_SDD.md` per pipeline; it is the single source of truth for that pipeline. Nine sections in total (kept minimal and information-dense):

| Section | Content | Form |
|---|---|---|
| 1. Overview | Purpose / scope + the invariants being locked down | Short sentences + bullets |
| 2. Context | Boundaries (who calls it / what it depends on) + the high-level flow | Table + one diagram |
| 3. Composition and dependencies | Module list + dependency edges | Table |
| 4. Data | Key structures + fields | Compact definitions |
| 5. Interfaces | Each cross-segment contract, fn(in) -> out | Table |
| **6. Processing logic / algorithms** | **Segment-by-segment pseudocode (the LLD) — the core; L1 translates from this** | **Pseudocode** |
| 7. Concurrency and resources | Semaphores / locks / GPU | Short sentences |
| 8. State dynamics | State machine (must be TOTAL + restart-safe) | Pseudocode / table |
| 9. Design rationale | Why the key trade-offs were decided this way (including the reasoning behind L3's choice of approach) | Bullets |

**Cut the prose**: do not write narrative paragraphs aimed at someone unfamiliar with the system. Information is carried by telegraphic intent lines plus pseudocode; the assumed reader is a developer who knows the system. A plain-language explanatory document for an external audience is a **separate** document and is not mixed into the SDD.

---

## 3. The outer loop: at the end of each iteration, self-judge against the definition of done; if it is not met, run another iteration

- **The contract = `{requirement, done-check}`.**
  - The requirement can be any shape (build a framework / add a feature / fix a bug / refactor / improve a metric are all just shapes).
  - The done-check is the standard for "what counts as done" for this requirement, expressed so the agent can decide it true-or-false mechanically on its own. It is the precondition for autonomy — with it, the agent can judge "done or not" for itself and need not come back to ask the human every iteration.
  - **The done-check is not necessarily a number.** Which one it is and what it looks like is determined by the requirement shape (look it up in the dispatch table of §5). A metric reading is just the special case where the requirement happens to be "raise a numeric metric."

- **One outer iteration** (for an above-medium task this loop runs per medium piece, after the §0.5 brainstorm-split):

```
   Step 0 (once per piece, before that piece's loop): a mechanically self-judgeable done-check must exist;
   if it is missing, settle it with the human first (§8), then enter the loop
      │
      ▼
   L3 decides "what to push toward the requirement next"   ◄── the human steps in around here
      │  (human-plus-machine: direction + research/measurement + adversarial review)
      │  [human approval point can fire INSIDE L3, before a high-cost action — see §4]
      ▼
   [human approval point at the L3 -> L2 handoff: only top-level-design changes pass — see §4]
      ▼
   L2 produces the SDD (autonomous) ──▶ L1 produces code + tests (autonomous)
      ▼
   self-judge against the done-check, "done or not" (+ evidence)  →  result fed back up to L3 (no approval point upward)
      ▼
   L3 reads the result: is the done-check met? not yet → set the next step, run another iteration
```

- **The number of iterations is determined by the shape; the skeleton does not change.** Some shapes meet the bar in one or two iterations (or even a single pass): a bug fix is usually basically one pass ("write a red case -> fix it green -> fold it into the regression suite"); building a framework usually wraps up in a few iterations ("build it + tests green"). Other shapes need many iterations to close in: improving a metric often adjusts one knob per iteration and inches upward. The skeleton (self-judge at the end of each iteration + run another iteration if not met) is exactly the same for both; only the number of iterations it triggers differs. **Do not mistake "many iterations of grinding" for a required part of the skeleton — it is just the rhythm of certain shapes.**

- **"What L3 actually does in one iteration, and where the next step comes from" also varies by shape (a shape-specific operation on top of the skeleton, listed here to keep you from running the wrong rhythm)**:
  - **Build a framework / add a feature**: L3's research is done **once up front** at the start; after that, each iteration is just "build the next slice from the already-settled design," with no need to re-research every iteration.
  - **Improve a metric**: L3's research **must be redone every iteration** — each iteration first researches "the next candidate technique worth trying," then "change one knob -> measure -> keep it or roll it back." **This is the rhythm most easily lost when improving a metric: you cannot research once at the start and then tune in your head forever; every iteration you have to find the next candidate again.**
  - **Fix a bug**: one iteration is "locate it -> write a failing case that reproduces it (red) -> fix until green," usually a single pass.
  - These differences only change "what happens inside one iteration"; they do not change the skeleton (the contract + self-judge at the end of each iteration + feed back up).
- **The self-judgment at the end of each iteration**: judge true-or-false against the done-check yourself, and **attach evidence**. The form of the evidence varies with the requirement shape — it might be test output, the red/green state of a reproduction case, the findings list from an adversarial review, or a metric reading.
  - This step is the same action for every shape: "judge true-or-false against the done-check." For the "improve a metric" shape it collapses to "read a number," but for "build a framework" or "fix a bug" it is "all tests green / the reproduction case turns green." **This is why the search-pipeline crash example (§6) is consistent with the outer-loop narrative: it never produced a number reading in the first place; the evidence it produced was "adversarial review caught a bug / the regression test turned green after the fix."**

- **The termination criterion is the same for all shapes, but the weight of the two parts shifts with the shape**:
  - **First part: the done-check is met.** This is the primary termination condition for every shape. For "one-shot" shapes (build a framework / add a feature / fix a bug / refactor), built is built and green is green, and termination is almost always driven by this part.
  - **Second part: L3 judges that "within the approved direction, there is no remaining action that can mechanically and self-judgeably advance the done-check."** This part mainly serves shapes whose goal is to converge gradually and where there is in principle always a next thing to try — the typical case being "improve a metric" (there is almost always some other approach left to try, so this part is what makes it deliberately stop).
  - **For the "improve a metric" shape, "when there is no next step" becomes a cost-versus-benefit judgment** (is the cost of investing further still worth the expected benefit). That is laid out in §7; the main body does not spell it out here.

- L3 is not something you pick once at the start and then never touch again. It is **the action of "deciding the next step" in every iteration**; L2/L1 are the execution links that **autonomously deliver** each decision.

> **The done-check is a precondition that runs through the whole task, not a step done once at the start.** Before the first line of L1 code is written for this task, there must already be a mechanically self-judgeable done-check; and that done-check must stay **continuously in effect** — every iteration ends by self-judging against it. Without it, the outer loop cannot terminate on its own (the agent never knows when to stop). How to write the done-check in a "machine can decide true-or-false automatically" form is in §8.

---

## 4. The human approval point (where the human steps in)

- **It is not one fixed spot.** The approval point is a gate that can fire at two distinct moments, depending on which axis is hit:
  - **Inside L3, before a high-cost action (the cost axis).** When a step within L3 is about to spend a large cost — for example an expensive measurement spike — the spend goes through the approval point **first, before the compute is spent**, even if the direction has barely moved. There is no L3 -> L2 handoff yet at this moment; the gate fires inside L3.
  - **At the L3 -> L2 handoff, for a change that touches the top-level design (the design axis).** A change of approach / a refactor / anything that touches the top-level design itself goes through the approval point as it crosses from L3 into L2.
- Both gatings only ever apply to the **downward** direction; reporting results upward never goes through an approval point.
- **The trigger has two axes; hitting either one passes through the approval point**:
  - **Axis one: does it touch the top-level design?** A small change within the direction -> autonomous, no approval point. A big change / refactor / change of approach (touching the top-level design itself) -> goes through the human approval point (this is the L3 -> L2 handoff gating above).
  - **Axis two: does it spend a large cost (money / time / compute)?** High-cost actions such as "build a spike and measure" or "do a refactor," even if you feel the direction has barely moved, go through the approval point by default — because they consume meaningful resources, and asking the human before spending money / time is the floor. For a high-cost action inside L3, this is the inside-L3 gating above (approve the spend before it happens).
  - Both axes are invariants independent of requirement shape: a task of any shape can touch "the top-level design" or "spend a large cost."
- The human approves the **direction**, not the details of the SDD — which is exactly the altitude where "taste should rule and adversarial review cannot substitute." For a complex task, the brainstorm-split (§0.5) is the human-in-the-loop decision at this same altitude, sitting before the first iteration.
- **Guarding against self-deception**:
  - "Does this count as touching the top-level design" is **decided by a clean subagent**, not by an agent that is eager to charge ahead judging itself.
  - **When unsure, treat it as a big change and go through the approval point.** Why default to the strict side: asking the human once is cheap; going the wrong way on a major direction is expensive.
- This rule also automatically solves the "a flood of candidate changes drowns the human" problem: small changes are autonomous, only structural big changes go through the approval point, so **the frequency of human involvement scales automatically with the importance of the change**.
- **Explicit delegation can waive it**: if the human explicitly says "I'm going to sleep / delivery is a week out, the tests and the permissions are yours," then this run downgrades / waives the approval point and goes fully autonomous; **by default the approval point still applies**.
- **Dynamic opening and closing (driven by the top-level-design axis; the cost axis still fires independently per the two-axis rule above)**: a small change within the direction -> the agent is autonomous; needing to change the approach / refactor / touch the top-level design -> go through the human approval point; once that structural change has landed, further small changes on top of it that are still within the direction -> back to the agent being autonomous. In other words, this opening and closing tracks "does the change touch the top-level design," and has nothing to do with "does this requirement have an improvement curve or a bottleneck" — the latter is just the narrative of the one shape "improve a metric" (its cost/benefit view is in §7), and you should not use it as the skeleton for the approval point. (This describes only the top-level-design axis; the cost axis still independently sends high-cost actions through the approval point.)

---

## 5. The done-check dispatch table (requirement shape -> what counts as done)

"What counts as done" is **not assumed to be one fixed measuring stick**; it is derived from the requirement shape. Below is an **open, extensible** dispatch table — at the end of each iteration, first see which shape the requirement is, then self-judge against the done-check on the corresponding row.

**This table only illustrates a few common shapes; it is open. When you hit a shape not listed (for example a migration or a dependency upgrade), add a row using the three questions below.** More rows are not pre-filled here, to avoid drifting into ever-finer detail.

**The three questions for adding a row for a new shape** (run through them every time you add a row, so that rows added by different people come out consistent):

1. **Can the done-check be decided true-or-false by a machine on its own?** If not, first rework it into a form the machine can self-judge (see §8); otherwise the outer loop cannot terminate on its own.
2. **Is it "one-shot" or "gradual convergence"?** A one-shot shape (such as build a framework / fix a bug / refactor) terminates on the first part (the done-check is met); a gradual-convergence shape (such as improve a metric) also needs the second termination part (no remaining action can advance it) and the slimmed general loop of §7.
3. **Before optimizing, is the done-check itself truthful?** A done-check that is a number can be a problem if that number does not faithfully track the real goal — see the single caveat in §7.

> **Where "performance / latency optimization" belongs**: its done-check is a number (latency / throughput / memory), so by the questions above it is just another "raise a numeric metric" shape. It uses **the same slimmed general flow as any other metric** (see §7) — not a separate, one-shot path.

| Requirement shape | Done-check (what counts as done) |
|---|---|
| **Build a framework / add a feature** | The tests it designed itself are all green + it actually runs. (Built + tests green.) |
| **Fix a bug** | **First write a failing case that reproduces the bug (red)** -> fix until it turns green + fold this case into the regression suite + adversarial review confirms there is no sibling gap of the same kind. |
| **Refactor** | The existing tests are still all green (behavior unchanged) + the target property is achieved (for example "this piece of logic is consolidated into a single entry point," whatever the refactor itself was meant to achieve). Note: the "pre-change test snapshot" here is a **behavioral baseline**, the implicit reference of a refactor; it is not the same thing as the numeric target of improving a metric. |
| **Improve a metric** | Measure + keep the wins + terminate when the candidate approaches are exhausted, or sooner, when the cost of investing further outweighs the expected benefit. This shape follows the slimmed general loop in §7 — and so does performance / latency optimization, since it is also a numeric metric being improved (see the three questions above). |

> **A neutral reminder that applies to every shape**: the done-check itself should also be passed through adversarial review once, to confirm that "meeting this done-check = genuinely meeting the requirement," so that the done-check does not itself have a hole. This matters for every shape; for the "improve a metric" shape in particular, see the single caveat in §7.

---

## 6. Why it works

- On every "abstraction jump that is easy to fall off," there is a **scaffold + an adversarial review**:
  - requirement -> approach, paired with **research**;
  - approach -> mid-level, paired with **pseudocode**;
  - mid-level -> low-level, paired with **tests**.
  - This forces the agent to think the logic through at every level, instead of jumping all the way to the bottom in one step and dropping logic everywhere.
- The LLM is already strong at the "mid-level -> low-level" segment -> so **the weight is placed on L3 + L2**, and L1 reduces to a small, local, constrained task.
- The non-runnable layers (L2/L3, which can only be reviewed and cannot be tested by running) are written by someone who gets anchored by their own thinking -> so **context-clean subagents** must do the adversarial review for it to be objective.
- "Hardening L2 into existence" + "wrapping a goal-driven iteration around it" are the entire difference between this method and "the ordinary L3+L1 way of using an agent" (§0).

### The search-pipeline crash example: a correctness bug caught by adversarial review that the tests did not catch

This is the single strongest piece of evidence for the method — it confirms that "the real value of L2's adversarial review = catching correctness, with nothing to do with any metric."

A search pipeline was already "built, tests all green." But while running the method over it and doing adversarial review on its abstraction layers, **a real crash that the tests had not captured at all was found**:

> When the entire corpus in the library is tokenized to empty, `BM25Okapi` executes `avg_idf = idf_sum / 0` and throws `ZeroDivisionError`; and that call site is outside the `try` block -> it crashes the whole tool outright.

A guard was added on the spot + a regression test added + the decision fed back into the SDD; the next adversarial review surfaced no substantive issue, and that iteration ended on its own.

**This is exactly the value that "adversarially reviewing the abstraction layers (L2's check)" adds over "just running the tests (L1)"**: tests only cover the inputs that were thought of, and cannot cover a corner like "the whole library tokenizes to empty"; whereas checking the mid-level logic against the top-level design can force out, at the level of "could this path crash," exactly that. Note: this example has **no metric and no number reading at all** — it is purely correctness. That is why L2's adversarial review is an invariant, part of the main body, and not something specific to one shape.

---

## 7. Metric-improvement appendix (the clearly marked "shape-specific" notes)

> **Scope: only when the done-check is a numeric metric being improved, needing gradual convergence (the typical case being improve a metric; performance / latency optimization belongs here too — see the three questions in §5).** Improving a metric is not a separate method. It is just the same general outer loop the rest of this document describes, applied to a shape whose evidence is a number.

The general loop, applied to a numeric metric:

- **L3 enumerates the candidate approaches.** There may be few or many — do not assume any fixed small count. Each iteration, L3 researches the next candidate worth trying (this is the rhythm most easily lost: keep finding the next candidate, do not research once and then tune in your head forever).
- **Triage each candidate by cost.** Cheap or obvious ones -> try them autonomously. High-cost ones (a new, large, expensive approach) -> take them to the human approval point (§4), where the human decides whether the expected benefit is worth the cost.
- **Measure each candidate** (did the number improve or not) and **keep the wins**, roll back the rest.
- **Stop when the candidate approaches are exhausted**, or sooner, when the cost of investing further outweighs the expected benefit.

That is the whole flow. There is no mandatory numeric-baseline ceremony, no fixed convergence counter, no "stop after N rounds without improvement" rule.

> **The one caveat for metric work (keep exactly this, in plain words)**: before you optimize a metric, first make sure the metric objectively and truthfully reflects the real goal you actually want — so that the number going up genuinely means the thing got better, and you never end up in a situation where the metric rises while real performance drops.

---

## 8. Startup preparation & landing conventions

### Startup preparation (a precondition that runs through the whole task, not a one-time t=0 step)

- **Before the first line of L1 code is written for this task, the done-check must be written in a form a machine can decide true-or-false automatically, and it must be relied on for self-judgment throughout the task.**
  - What it looks like concretely lands according to the requirement shape (look it up in the dispatch table of §5): build a framework = a set of tests that decide "does it work correctly"; fix a bug = a reproducing failing case; refactor = existing tests + the target property; improve a metric = a measurement of the number (and, before optimizing, a check that the number truthfully reflects the real goal — see §7).
  - **If the requirement handed down does not come with a mechanically self-judgeable done-check, work it out with the human first, then start.** Why this is a hard precondition: without it, the outer loop cannot terminate on its own — the agent never knows "when it counts as done."

### Landing conventions (general rules independent of requirement shape)

- **One `*_SDD.md` per pipeline (the single source of truth)**; a separate plain-language explanatory document for an external audience, and **the two are not mixed**.
- **Startup preparation writes only the first version of the done-check; it does not adversarially grind it during startup.** Adversarial review happens inside the iterations, bound together with code + tests/measurement.
- **Changing a production service** (touching a running daemon / data) must go through a branch + a test gate + human review before merging to the main branch; **never run a migration on production data** — a migration is tested only on a temporary copy. This is a safety floor, independent of requirement shape.
