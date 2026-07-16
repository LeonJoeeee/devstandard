# Documentation Layering Between Architecture and Code: What Professional Teams Actually Do — and What DevStandard Should Steal

> Research artifact behind ADR 0017. Produced 2026-07-16 by an 82-agent research workflow (5 search angles, 64 raw claims, top 20 adversarially verified: 20/20 survived); 12 cited sources. Evidence gaps are flagged inline.

## 1. TL;DR

Professional teams almost universally maintain a **middle-layer design artifact** between the architecture doc and the code — called a design doc (Google [1]), RFD (Oxide [2]), RFC (Rust, Uber [3][4]), or design document/blueprint (GitLab [7]). Its defining properties are consistent across all these shops: it is written **before** coding starts [1], it documents **options considered with tradeoffs and an explicit decision**, not just the chosen design [2], and it is **gated by the significance of the change, not the size of the project** — Rust's RFC process makes the artifact mandatory only for "substantial" changes and explicitly exempts refactors, objective improvements, and invisible changes [3]. Sizing is elastic within the artifact itself: Google sanctions both 10–20-page docs for large projects and 1–3-page "mini design docs" for smaller changes [1].

**Tiering at scale** in the formal models (C4, arc42) is not "big project → more docs." It is **hierarchical zoom on demand**: arc42 whiteboxes only the selected building blocks that need another level of detail [6], and C4's answer to "600 components" is to split one diagram into many smaller diagrams scoped by bounded context / business area — each at the *same* level of abstraction [5]. Both models explicitly stop short of the code level; C4 calls code-level documentation optional and discourages maintaining it, since tooling generates it on demand [5].

The **load-bearing logs** are decision logs: ADRs are append-only (accepted ADRs are never edited, only superseded with a link back) [8], and Oxide's RFDs carry lifecycle states (`published`, `committed`, `abandoned`) so the design corpus itself becomes a permanent record [2]. The known failure mode is logging every decision: "if every decision is architectural, no decision is architectural" — significance is measured by **cost of change** [9].

**In the agent era (2025–2026)**, the middle layer is being revived as the *agent handoff artifact*: Anthropic's official guidance is interview → write a self-contained SPEC.md (files, interfaces, out-of-scope, end-to-end verification step) → execute in a fresh session [12]. But volume actively hurts: a Spec Kit practitioner reported that cutting generated spec text by ~3× *improved* LLM stability [10]. Agent-facing docs complement rather than replace human docs (AGENTS.md model) [11].

**For DevStandard**: add a trigger-gated, 1–3-page design/spec doc (significance-gated, never size-gated); add a "split-on-zoom" rule for the architecture doc instead of a second doc tier; keep the ADR log but arm it with the cost-of-change test; skip any new log, skip code-level documentation, skip multi-artifact spec generation. Details in §6.

---

## 2. The Middle Layer: Design Docs, Tech Specs, RFCs, RFDs

### What it is and when it's written

The canonical description is Google's: design docs are "relatively informal documents that the primary author or authors of a software system or application create **before they embark on the coding project**" [1]. This timing is the artifact's defining feature — it precedes implementation and shapes it, rather than describing it after the fact. GitLab frames the same artifact's purpose as capturing "a technical vision and a set of principles that will guide feature implementation... It acts as guardrails to keep team aligned" — alignment guardrails, explicitly *not* an implementation spec [7].

### What it contains

Oxide's RFD 1 is the most precise about mandatory content: a strong RFD must "document the viable options (or a subset of options if we can easily rule some out) and the benefits and drawbacks of each option," back reasoning "with data and references wherever possible; making it easy for our future selves (and those who join in the future) to understand the decisions we made and why," and state an explicit final determination [2]. The distinguishing content of a good middle-layer doc is therefore **the rejected alternatives and the why**, not the design itself.

### How heavy

Google's sizing guidance: "The sweet spot for a larger project seems to be around 10-20ish pages... It should also be noted that it is absolutely possible to write a 1-3 page 'mini design doc'" [1]. Critically, this tiering lives **inside the single artifact type** — same document kind, elastic length — not as a separate ceremony tier.

### When it's required at all

Rust's RFC #0002 (adopted 2014, still the live governing process) draws the sharpest line. An RFC is mandatory only for "substantial" changes: semantic/syntactic language changes that aren't bugfixes, feature removals, compiler–library interface changes, stdlib additions [3]. And it carves out an explicit no-ceremony floor: "rephrasing, reorganizing, refactoring, or otherwise 'changing shape does not change meaning'," objective-metric improvements (speedups, warning removal), and changes invisible to end users require **no RFC at all** [3]. The gate is the *nature of the change*, never the size of the team or project.

### Who reviews, and how the process scales

Oxide requires RFDs to be public and collaborative — discussed in a pull request before merging — both to invite broad input on significant decisions and to counteract authors' "natural hesitancy to publish something unpolished" [2]. RFDs also move through six defined lifecycle states (prediscussion → ideation → discussion → published → committed / abandoned), giving the doc a path from rough idea to permanent implemented record [2]. At Uber, the process started as literally "an email to every engineer" and, as headcount grew to thousands, evolved into per-domain mailing lists (backend, mobile, web) with engineer-built templates — i.e., the review audience scaled **organically by domain**, not via a size-based ceremony ladder [4].

---

## 3. Doc Tiering at Scale: C4, arc42, and When One Doc Becomes Many

### C4: split by scope, not by adding levels

Simon Brown's explicit guidance for real-world systems ("600 components rather than 6") is **not** to force one giant diagram, nor to invent new abstraction levels: "don't be afraid to split that single complex diagram into a larger number of simpler diagrams, each with a specific focus around a business area, functional area, functional grouping, bounded context, use case, user interaction, feature set, etc." — each telling "a different part of the same overall story, at the same level of abstraction" [5]. The split trigger is **legibility of a single view**, and the split axis is **domain scope**, not size class.

Equally important is where C4 says to *stop*: the fourth (Code) level "is very much an optional level of detail and is often available on-demand from tooling such as IDEs... No, particularly for long-lived documentation because most IDEs can generate this level of detail on demand" [5]. The model's own author says don't maintain docs at the code level.

### arc42: hierarchical zoom, only where needed

arc42's official tips instruct: "Explain the structure of your source code as a hierarchy of white- and blackboxes, starting from the context view" [6]. The levels are concrete and, crucially, **selective**: "Level 1 is the white box description of the overall system together with black box descriptions of all contained building blocks. Level 2 zooms into *some* building blocks of level 1... Level 3 zooms into *selected* building blocks of level 2, and so on" [6]. Decomposition proceeds one level at a time, only for the blocks that warrant it — never uniformly across the whole system.

### Diataxis

No claims about Diataxis survived verification in this research run — **evidence is thin here and what follows is background framing only**: Diataxis organizes *user-facing* documentation by reader need (tutorial / how-to / reference / explanation) and is largely orthogonal to the architecture-to-code layering question. It matters for DevStandard only insofar as it warns against mixing "explanation" (why the system is shaped this way — the architecture doc's job) with "reference" (what exactly the interface is — the spec/code's job) in one document.

### The consolidated split rule

Across both formal models, the split trigger is the same: **split when one view at one level of abstraction can no longer tell its story legibly, and split along domain/subsystem seams — never on a project-size threshold.** The overview doc survives the split as the Level-1 whitebox / system landscape; child docs are added only for the specific subsystems that need a zoom.

---

## 4. The Log Family: What's Load-Bearing

### ADR / decision logs — load-bearing, with a strict append-only discipline

The core rule (Fowler's bliki, concept originated by Michael Nygard 2011): "Once an ADR is accepted, it should never be reopened or changed — instead it should be superseded" [8]. The new ADR links back to the old one, so the sequence of files forms a permanent, append-only log of decisions and how long each governed the work [8]. This is what makes an ADR log load-bearing: it preserves *why* and *for how long*, which no mutable document can.

The failure mode is equally well documented. Pureur and Bittner (InfoQ, 2023): an ADR log becomes dead weight once it records every team decision — "if every decision is architectural, no decision is architectural," because bloat obscures genuine architectural concerns [9]. Their admission test (adopted from Grady Booch): a decision qualifies only if its **cost of change is high** — it touches fundamental data structures/algorithms or has effects scattered across the codebase rather than localized to one component [9].

### RFD corpus as a second log — load-bearing at Oxide

Oxide's RFDs double as a decision log because of their lifecycle states: a `committed` RFD is a permanent record of established direction; an `abandoned` RFD is a permanent record of a road not taken [2]. The design-doc corpus and the decision log are the *same repository* — no separate journal needed.

### Dev journals, changelogs, incident logs — evidence thin

No claims about engineering dev journals/work logs, changelogs, or incident logs survived verification in this run. I cannot support, from verified evidence, that any of these is load-bearing for the middle-layer problem DevStandard is trying to solve. The honest reading of the evidence: the two logs professional teams demonstrably treat as load-bearing for *design* are (a) the append-only ADR log [8][9] and (b) the never-deleted design-doc/RFD corpus with lifecycle states [2].

---

## 5. The Lean Floor and the Smells of Dead Weight

**The demonstrated lean floor** for a serious team, assembled from the evidence:

- A significance gate for the middle layer, with an explicit no-ceremony list — refactors, objective improvements, invisible changes need nothing [3].
- A 1–3-page mini design doc as the sanctioned lightweight form of the middle layer [1], written before coding [1], containing options + tradeoffs + explicit decision [2].
- One architecture overview, hierarchically extended only where a block needs a zoom [6], split along domain seams only when a single view stops working [5].
- An append-only ADR log admitting only high-cost-of-change decisions [8][9].

**Smells that a doc layer has become dead weight:**

1. **The log records everything.** "If every decision is architectural, no decision is architectural" [9].
2. **Docs at the code level.** C4's own author says don't maintain them — tooling generates that detail on demand [5]. In 2026 the "tooling" includes coding agents reading the source directly.
3. **Uniform decomposition.** Documenting every subsystem to the same depth, rather than arc42's selective zoom of only the blocks that need it [6].
4. **Volume as proxy for rigor.** The strongest agent-era data point: the original poster of the widely-discussed Spec Kit critique thread reported that cutting spec/documentation input to the LLM by roughly 3× *improved* model stability and reduced randomness in task execution [10] — a single practitioner data point, but a direct one, and it points the same direction as the human-side evidence: text that doesn't carry a decision is a cost.
5. **Editing history instead of appending to it.** Reopening accepted ADRs destroys the log's value [8]; Oxide's answer to a dead idea is the `abandoned` state, not deletion [2].

---

## 6. RECOMMENDATION FOR DEVSTANDARD

Current state: one-page injected core + per-project PRD + single architecture doc (1–3 pages) + ADR log; SDD deliberately optional to avoid Spec Kit ceremony. The gap is real — every serious shop surveyed has a middle-layer artifact [1][2][3][4][7] — but the evidence also says it can be added without reintroducing size tiers, because **no surveyed process gates the middle layer on project size; all gate on change significance** [1][3].

### (a) Add the middle layer: a trigger-gated Design Spec, 1–3 pages, one artifact type

- **One artifact, elastic length.** A single "design spec" doc type, guided to 1–3 pages — exactly Google's sanctioned mini-design-doc form [1]. No small/medium/large variants; length flexes inside the one type [1]. This is consistent with the rejected-size-tier decision, because the gate is never size.
- **Gate it Rust-style, with the no-ceremony floor written down.** Required only for "substantial" changes; explicitly exempt refactors that don't change meaning, objective-metric improvements, and user-invisible changes [3]. Ship the exemption list — the floor is what keeps it lean.
- **Written before coding** [1], and its required content is: options considered with tradeoffs, reasoning with references, explicit final decision [2]; plus the agent-era additions from Anthropic's official guidance — name the specific files and interfaces, state what's out of scope, end with an end-to-end verification step [12].
- **Make it the agent handoff artifact.** This is the 2026-specific payoff: the workflow Anthropic documents is interview → SPEC.md → execute in a fresh session with clean context [12]. DevStandard's design spec should *be* that SPEC.md — one artifact serving human review and agent execution. This also resolves the SDD-optional tension: the design spec is SDD's useful residue with a crisp trigger, instead of Spec Kit's always-on multi-artifact generation.
- **Review as a lightweight PR discussion** on the doc itself, Oxide-style [2] — no new meeting, no committee.

### (b) Add a when-to-split rule, not a doc tier

Do **not** add a second architecture-doc class. Add one rule to the existing architecture doc's guidance:

> The architecture doc stays the single 1–3-page overview (the Level-1 whitebox [6] / C4 system view [5]). When one section of it can no longer explain a subsystem legibly at the overview's level of abstraction, extract *that subsystem only* into a child doc scoped to it — split along domain/bounded-context seams [5], zoom one level at a time, only for blocks that need it [6]. Never split on a size threshold; never document all subsystems to equal depth [6]; never document down to code level — agents and IDEs read the source on demand [5].

This keeps the doc model formally flat until the moment a specific seam forces a zoom, which matches both C4 and arc42 exactly and adds zero ceremony for small projects.

### (c) The log: keep one, arm it, add none

- **Keep the ADR log; add the admission test.** One sentence in the guidance: a decision earns an ADR only if its cost of change is high — fundamental structures, or effects scattered across the codebase [9]. And enforce append-only: accepted ADRs are superseded, never edited [8].
- **No new log.** The evidence supports exactly two load-bearing design logs, and DevStandard can get the second one for free: **keep design specs in-repo permanently, never deleted, with a one-word status header (`draft` / `accepted` / `committed` / `abandoned`)** — a two-state-lighter version of Oxide's lifecycle [2]. The spec corpus then *is* the second log. Evidence for dev journals, changelogs, and incident logs being load-bearing here is thin (nothing survived verification); skip them.

### What to SKIP, explicitly

| Skip | Why |
|---|---|
| Size-based ceremony tiers | No surveyed process uses them; all gate on change significance [1][3]; already rejected by DevStandard — the evidence vindicates that call. |
| Mandatory design spec for all work | Rust's exemption floor is the model [3]; keep SDD-optional, just give it a trigger. |
| Code-level documentation (C4 L4, class diagrams) | C4's author discourages maintaining it; generated on demand [5] — doubly true when agents read source directly. |
| Spec Kit–style multi-artifact generation | Practitioner evidence: ~3× less generated spec text *improved* agent stability [10]. |
| A separate agent-doc hierarchy | AGENTS.md-style content complements human docs [11]; DevStandard's injected one-page core already plays this role — one design spec should serve both audiences [12]. |
| Full arc42/C4 template adoption | Steal only the zoom rule [6] and the split-by-seam rule [5]; the full skeletons are sized for systems DevStandard doesn't target. |
| Dev journal / new log types | No verified evidence of load-bearing value; the status-tagged spec corpus [2] + ADR log [8] cover it. |

**Net change: one new artifact type (trigger-gated, 1–3 pages, doubles as agent spec), one new sentence-long split rule, one new sentence-long ADR admission test, one status header on specs. Nothing else.**

---

## Sources

1. **Design Docs at Google** — Malte Ubl (Google), July 6, 2020. Canonical, frequently cited reference. https://www.industrialempathy.com/posts/design-docs-at-google
2. **RFD 1 — Requests for Discussion** — Oxide Computer Company, originally 2020, living/continuously updated document. https://rfd.shared.oxide.computer/rfd/0001
3. **RFC #0002: The Rust RFC Process** — Rust core team, adopted 2014-03-11; still the live governing process document. https://rust-lang.github.io/rfcs/0002-rfc-process.html
4. **Scaling Engineering Teams via RFCs: Writing Things Down** — Gergely Orosz (ex-Uber), 2021. https://blog.pragmaticengineer.com/scaling-engineering-teams-via-writing-things-down-rfcs
5. **The C4 model for visualising software architecture** — Simon Brown, ongoing since 2006–2011; site actively maintained, accessed 2026. https://c4model.com
6. **arc42 Tip 5-2: Organize the building block view hierarchically** — arc42 (Gernot Starke & Peter Hruschka, created 2005); docs continuously maintained, accessed 2026. https://docs.arc42.org/tips/5-2
7. **GitLab Handbook — Architecture Design Documents** — GitLab, last modified 2026-02-02, accessed 2026. https://handbook.gitlab.com/handbook/engineering/architecture/design-documents
8. **Architecture Decision Record (bliki)** — martinfowler.com, page updated 2022; concept originated 2011 by Michael Nygard. https://martinfowler.com/bliki/ArchitectureDecisionRecord.html
9. **Has Your Architectural Decision Record Lost Its Purpose?** — Pierre Pureur & Kurt Bittner, InfoQ, 2023-10-25. https://www.infoq.com/articles/architectural-decision-record-purpose
10. **"SpecKit creates the illusion of work" — GitHub Spec Kit Discussion #1784** — NaikSoftware et al., opened 2025-09-08; cited data point posted 2025-09-12. Single-practitioner report. https://github.com/github/spec-kit/discussions/1784
11. **AGENTS.md — a simple, open format for guiding coding agents** — living standard, stewarded by the Agentic AI Foundation (Linux Foundation) as of 2026. https://agents.md
12. **Best practices for Claude Code** — Anthropic official docs, live document, current as of July 2026. https://code.claude.com/docs/en/best-practices

*Evidence gaps noted inline: Diataxis (§3) and dev journals/changelogs/incident logs (§4) had no claims survive verification in this research run; statements there are flagged as background framing or absence-of-evidence rather than verified findings.*