# 0003 — Task execution: Workflow mandatory, SDD optional

Status: Accepted (2026-06-09)

## Context

The old method centered task execution on the SDD (a pseudocode design document) — designed for a single interactive agent developing sequentially. The Workflow tool changed the economics: **for the same task, a workflow spends more tokens, delivers better quality, and needs less human labor** (tokens buy quality; quality buys autonomy). A workflow is itself an excellent dynamic design artifact.

## Decision

Every task **must** be driven by a Workflow (a dedicated harness is being designed for this); the SDD is demoted to an **optional** aid — written only when clarifying static structure (modules / interfaces / data flow) first helps author a better workflow.

The non-negotiable backbone survives the demotion: the discipline the SDD used to protect — **design first, adversarially review the design, only then write code** — moves into the harness's structure (an early stage emits the design → clean-context agents refute it → only then implementation begins). Dropping the document must not drop the discipline.

Where tokens burn: before writing (design refutation), after writing (adversarial verification of the implementation + machine self-judgment), before closing (completeness critique). Only independent, opposed verification buys quality; shared-context redundancy does not.

## Consequences

Task execution shifts from "write a document, then follow it" to "author a workflow with verification built into its structure." The harness's concrete skeleton and delivery form are decided separately (currently OPEN; see architecture.md §4).
