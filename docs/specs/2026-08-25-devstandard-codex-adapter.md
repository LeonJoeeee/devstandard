# DevStandard on Codex: one tree, checkout-resolved AGENTS.md delivery, a Codex mapping file

Status: committed

*Survived a two-round pre-code challenge. Round 1 found two blocking gaps (mapping reach; failure
detection); round 2 found one (the routing-sentence detour was unverified). All resolved below — the
round-2 item by a live run, not a paper fix. Non-blocking items 3–4 folded in as the reviewer advised.
Implemented on `feat/148-codex-adapter`; this PR carries the spec at `committed` per the flow in
`reference/design-spec.md`. The merge itself is gated on the human's approval (core architecture).*

## Problem & context

DevStandard ships only to Claude Code. The human wants it on Codex as the *main session* too (#148) —
Codex running the method, not merely dispatched as an executor (ADR 0036, already shipped).

The whole method is markdown a model reads on demand. Only two things are Claude-specific:

1. **Delivery.** ADR 0019 forces `core.md` read-first via a `SessionStart` hook, because ADR 0001
   measured a methodology skill self-triggering from its description at ~0% on real dev tasks.
2. **Vocabulary.** Five kinds across nine files (#148 "Question 2"): tiers `opus`/`sonnet`/`haiku` (6),
   `superpowers:<skill>` (8), `CLAUDE.md` as operational memory (9), "workflow run"/Agent/Workflow
   tools (4), `EnterWorktree` (2).

**Everything below rests on measurement against `codex-cli 0.144.6`, not inference** — this repo has
three times shipped "verified" mechanics that were never run (#148):

- A Codex **plugin cannot force a first action** — a plugin `SessionStart` hook does not fire
  (`codex exec` and interactive TUI both); no plugin-root variable, no text-injecting manifest field,
  `codex plugin add` writes no `AGENTS.md`. Superpowers confirms it (Codex manifest has no `hooks`; it
  ships as skills — the ~0% path ADR 0001 rejected).
- Codex **reads the consuming repo's `AGENTS.md` at session start, unprompted, and obeys it.**
- **The full delivery chain is demonstrated end-to-end** (this spec's verification, already run):
  `AGENTS.md` → `<source.path>/core.md` (the real 94-line page) read first → its top routing sentence
  → Codex self-identifies as non-Claude and reads `reference/harness-codex.md`. Both a `core.md`
  sentinel and a `harness-codex.md` sentinel were echoed on a prompt naming no file; a no-`AGENTS.md`
  control produced neither.
- **The path is stable.** Installed from a **local git checkout**, `codex plugin list --json` reports
  `source.path` = the checkout dir, **version-agnostic**: a 0.1.0→0.2.0 bump left it unchanged and
  updated `core.md` in place. So `<source.path>/core.md` reads the live checkout — it cannot go
  silently stale, and `git pull` *is* the update. A manifest with only
  `name`/`version`/`description`/`author`/`license` (no content field, no `hooks`) installs cleanly.

So delivery is a per-repo `AGENTS.md` pointer written by a setup step, resolving `source.path`. One
repo, one tree, a thin `.codex-plugin/plugin.json` (superpowers precedent; a second repo is the
`core.md` copy ADR 0028 retired).

## Options considered

- **Delivery:** plugin hook (*dead, measured*) / skills (*~0%, ADR 0001*) / **`AGENTS.md` pointer
  written by a setup step** — chosen, the only measured forced-first-action channel.
- **Pointer path:** a `core.md` copy per repo (*second copy*) / a version-pinned cache path (*goes
  stale*) / **`source.path` from `codex plugin list --json`, which for a local checkout is stable and
  version-agnostic** — chosen and measured. No symlink, no per-repo re-run; `git pull` updates.
  *(A future published-marketplace install resolves `source.path` to a versioned cache instead —
  out of scope, flagged in the ADR; a single `~/.codex/devstandard/core.md` symlink refreshed once per
  update restores an O(1) stable path if that is ever shipped.)*
- **Vocabulary:** neutralize `core.md` (*ceiling + vaguer-for-all*) / **a Codex mapping file plus the
  minimum in-place pointers a held mapping cannot reach** — chosen (superpowers' `codex-tools.md`
  shape; ADR 0028's mapping-table-not-copy).

## Decision

Files, and each one's interface:

1. **`.codex-plugin/plugin.json`** (new) — `name`/`version`/`description`/`author`/`license`, no
   `hooks`, no content field (install measured to succeed). Registers the checkout so `source.path`
   resolves; delivers nothing itself.
2. **`reference/harness-codex.md`** (new; read by a Codex session, and by a Codex-dispatching Claude
   session translating a brief) — (a) **setup step**: resolve `source.path` via
   `codex plugin list --json`, verify `<path>/core.md` exists (refuse loudly if not), write/refresh the
   consuming repo's `AGENTS.md` pointer; (b) **per-kind ruling** for all five (the done-check's "ruling
   per item"): tiers → set the model explicitly, `opus` is Claude's cap-name not a Codex tier (ADR
   0036); `superpowers:<skill>` → the Codex skill-load equivalent, or skip where absent; `CLAUDE.md` →
   `AGENTS.md`; Agent/Workflow → `spawn_agent`/`update_plan` and Codex's execution primitives;
   `EnterWorktree` → plain `git worktree`; (c) the **`worker-brief.md` paste-translation rule** below.
3. **`core.md`** — one routing sentence, **at the very top, before any vocab-bearing line** (its own
   `opus`/`superpowers:`/"workflow run" appear early, so a later placement would let a Codex reader hit
   them un-primed): a non-Claude harness reads `reference/harness-codex.md` first, then this page. This
   is the only shipped-page change; the token gate has ample room (~4,658/5,000; a sentence is ~69, measured).
4. **`reference/worker-brief.md`** — one pointer line (top): a non-Claude harness reads
   `harness-codex.md` first; if this was handed to you as a paste, its harness-bound names were already
   translated by your dispatcher. Two independent layers cover the paste path (worker never reads
   `core.md`): the dispatcher, primed by having read `harness-codex.md`, translates at paste time; and
   this pointer gives even a raw subagent a direct second chance.
5. **`reference/repo-claude-md.md`** and **`reference/ci-pipelines.md`** — one pointer line each. These
   are the files about *generating* a repo's `CLAUDE.md`; a Codex reader who misses the
   `CLAUDE.md`→`AGENTS.md` substitution here writes a file Codex never auto-reads, silently disabling
   that project's operational-memory channel for its life — low frequency, high cost (ADR 0032). The
   other five vocab-carrying files rely on the mapping primed by step 3's early routing sentence.
6. **`AGENTS.md`** (repo root, new) — DevStandard's own repo adopting the mechanism it ships: the
   pointer resolved to this checkout's `core.md`, so a Codex session working on DevStandard reads the
   method first. Dogfooding and the setup step's worked example.
7. **Gate 6** — extended to three manifests in lockstep, in `ci.yml`, the `CLAUDE.md` command block,
   **and `CLAUDE.md`'s "release delegation" prose** (which currently says "bump *both* manifests" —
   left unswept, the next agent-run release bumps two of three and gate 6 fails; this is the
   search-twice omission `CLAUDE.md` itself warns of).
8. **ADR 0038** (number free: highest across merged log, all remote branches, open PRs, and open issues
   is 0037) — **DevStandard is a method with per-harness adapters**; Claude Code is the reference
   adapter, Codex the second; shared `core.md`/`reference/` is the method, a thin manifest + mapping
   file + delivery mechanism is each adapter. States plainly: Codex delivery is **opt-in per repo**
   (absent, not degraded, where the setup step never ran) and depends on the checkout staying current
   (`git pull`), where Claude's hook is automatic per install; and records the two-layer paste
   mechanism as the reason the vocab mapping reaches a pasted worker.
9. **`docs/architecture.md`** §2/§4 and **`README.md`** — the adapter model, the third manifest, the
   AGENTS.md path.

## Out of scope

- **No skill-layer port** (DevStandard has no `skills/` dir), **no behavioral rewrite** (only names
  gain a mapping; a rule that genuinely doesn't apply on Codex is a follow-up finding), **no
  published-marketplace distribution** (install is from this checkout; a remote install reintroduces
  the versioned-cache stale-path question — the ADR flags it), **no claim Codex reviews/executes
  better** (that is ADR 0036).

## Verification

Steps 1–4 were **run during this spec's challenge and passed**; steps 5–6 run in the build's CI.

1. `codex plugin marketplace add <checkout> && codex plugin add devstandard@<mkt>` — installs with the
   no-content-field manifest. **Passed.**
2. Setup step resolves `source.path`, verifies `<path>/core.md`, writes the scratch repo's `AGENTS.md`.
   **Passed** (hand-edited nothing).
3. Codex session, prompt naming no file → **reads the real `core.md` first**, proven by a `core.md`
   sentinel echoed (never a self-report); no-`AGENTS.md` control echoes nothing. **Passed.**
4. **The detour (round-2 blocking item):** a second sentinel in `harness-codex.md` is echoed in the
   same run, proving the top routing sentence is followed and the mapping is primed. **Passed** — the
   session was observed reading `harness-codex.md` unprompted.
5. Missing-path is loud: point `AGENTS.md` at a nonexistent `core.md`; the session reports it cannot
   find the method rather than proceeding silently. (Build-time check.)
6. Repo gates: extended gate 6 with three manifests in lockstep; `core.md` token gate with the added
   sentence; `check-adr-index.py` with ADR 0038.

## Failure detection & rollback

Changes an on-disk delivery contract (a consuming repo's `AGENTS.md`) and `core.md`.

- **Detection.** The local-install read path names the live checkout (no version in it), so ADR 0019's
  silent-stale failure does not arise: a wrong path is a *missing* path — refused by the setup step,
  loud at read time (step 5). Method staleness reduces to a stale checkout, visible to
  `git status`/`git pull`. The sentinels are this spec's gate, not a live production monitor.
- **Two failures found and fixed in check-1 round 1, both verified.** (i) The setup step must never
  destroy an existing `AGENTS.md` — the first draft depended on `sponge` (not installed here) and
  silently truncated on its absence; the shipped snippet is install-free, prepends preserving prior
  content, and is idempotent via a marker (tested across create / preserve / re-run). (ii) 0018 rejected
  `AGENTS.md` for double-injection; measured, **Claude Code does not read a co-present `AGENTS.md`**
  (a sentinel in each file; only `CLAUDE.md`'s loaded), so the two channels stay separate — recorded as
  a dated amendment on 0018.
- **Rollback.** Every part is additive and reverts alone without touching the unchanged Claude delivery
  path: the `.codex-plugin` manifest, `harness-codex.md`, the `core.md` sentence, the three pointer
  lines. A consuming repo opts out by deleting its `AGENTS.md` line. No migration, no data, no
  irreversible step.
