# When a subagent, when Codex: the executor rule and the standing setting on the page

Status: committed

*Written on check 1's finding (PR #166, round 1) that this change meets the
borderline case — "when in doubt, a half-page spec beats a wrong build". Challenged by fresh
read-only Codex runs until nothing blocking remained; the round record is on issue #165.*

## Problem & context

Issue #165. The pages said *where* an external agent fits (rung 2, 0036), *which* (Codex, 0039) and
*how* to brief it (#156), and nothing about **when** to pick it over a harness-native subagent; and
they refused to name a model or effort ("would rot on their release schedule"). The human ruled:
write the classification down; use Codex for dispatched work unless the case especially suits a
subagent; the standing strength is `gpt-5.6-sol` at `xhigh`, on the page.

## Options considered

1. **Where the classification lives** — (a) in full on `core.md` (*rejected: the always-on page pays
   for every reader; the ladder already routes to the dispatch page*); (b) **in full on
   `reference/external-agent.md`, trigger + pointer on `core.md`** — chosen (CLAUDE.md's rule 2).
2. **Rule or recommendation** — (a) "recommended" with a symmetric list (*rejected by the human:
   "use Codex as much as we can, unless the case especially suits a subagent"*); (b) **Codex by
   default, a subagent only for an enumerated list; a subagent outside it is a departure said in the
   handback** — chosen.
3. **Where the standing setting lives** — (a) nowhere on the pages, in the dispatcher's memory or a
   config file (*rejected: that is the "choice made where no reviewer looks" 0036 itself warned of*);
   (b) the project's `CLAUDE.md` (*rejected: that file is commands / gotchas / copy-list, and a
   worker on Codex reads it only after dispatch — too late to pick the executor*); (c) **once, dated,
   on the dispatch page, with a CI assertion that it appears there and nowhere else live** — chosen.
   This reverses 0036's refusal to name vendor ids; the rot is bounded to one visible, dated line.
4. **The reason for Codex reviews** — (a) "a second vendor's independent judgment" (*rejected: it
   fails when the main session is itself Codex, a topology 0039 supports*); (b) **a fresh,
   process-isolated, read-only run — clean context, OS-enforced sandbox — with vendor diversity as
   the extra a Claude main session gets** — chosen.

## Decision

- `reference/external-agent.md`: section "When a subagent, when Codex" (the rule in full, Option 2b,
  reason 4b); opening widened to a Codex main session's own fresh `codex exec`; routing section
  states the standing setting once, dated (Option 3c), replacing the "would rot" sentence.
- Venue precedence, stated on the page and mirrored at every trigger: the rule chooses the **rung-2
  executor only** — Codex takes the subagent's slot; a workflow run's agents, its review panel
  included, are workflow-native; a separate live session is not replaced. Overviews name Codex in
  the subagent position, never as a fourth lane. Within rung 2, gating work always takes the fresh
  process (a harness-only source it needs is folded into the report it receives — `core.md`'s three
  reviewer artifacts, never a fourth); for implementation a hard
  capability need wins. When no qualifying process can run — a Codex main session whose
  `codex exec` fails — the gate is blocked, not lowered.
- `core.md`: trigger + pointer at rung 2 (scoped: the rung-2 executor; a separate live session stays
  the lane above), in "Who does the work", and in the fresh-reviewer line.
- `reference/harness-codex.md`: model routing points at the setting's address.
- The act sites where a review or challenge is commissioned carry the resident Codex trigger +
  pointer: `reference/code-review-prompt.md` (route, and a `{REVIEWER_IDENTITY}` opening line inside
  the fence so the record names the reviewer), `reference/worker-brief.md` (a worker's helper),
  `reference/design-spec.md` (the pre-code challenge), `docs/architecture.md` (the discipline
  paragraph, with the `opus` cap scoped to Claude-spawned agents), this repo's `CLAUDE.md` (check 1
  here); the overviews in `README.md` and `docs/PRD.md` name the Codex executor with the pointer.
- ADR 0040 (amends 0011, 0034, 0036, 0038 and 0039 by dated blocks, and 0024 in one routing detail —
  the address of the standing setting — its cap untouched);
  `docs/architecture.md`'s tree entry and outer-loop sentence reconciled.
- `.github/workflows/ci.yml`: the 0039 literal assertion follows the new wording; a new assertion
  that **reads the standing-setting record from the dispatch page's own sentence** (so the page is
  the single source and a change is one edit) and checks: the record appears exactly once there,
  its paragraph is dated, and the model name appears on no other live page (enumerated by path).

## Out of scope

Changing 0024's cap or tier names for Claude-spawned agents; rationing by price (the human's cost
reasoning is recorded as theirs, not turned into a rule); any change to how a worker is briefed.

## Verification

CI green on the head: the invariants step (the 0040 literal and the single-siting script: the full
record exactly once on the dispatch page, dated; the model name absent from every other live page,
enumerated by path) plus the
existing gates; the ADR index gate on 0011/0024/0034/0036/0038/0039/0040. Append-only on each amended ADR, by
this exact check — strip only the `Status:` block (from the `Status:` line to the next blank line)
and require the current remainder to start byte-for-byte with the origin remainder; it exits
non-zero on a rewrite or a failed `git show`:
```sh
for n in 0011 0024 0034 0036 0038 0039; do f=$(ls docs/adr/$n-*.md); python3 - "$f" <<'PY' || exit 1
import re,subprocess,sys
f=sys.argv[1]; strip=lambda s: re.sub(r'(?ms)^Status:.*?\n\n','',s,count=1)
old=strip(subprocess.run(['git','show',f'origin/main:{f}'],capture_output=True,text=True,check=True).stdout)
new=strip(open(f).read()); assert new.startswith(old), f'{f}: REWRITTEN'; print(f, 'append-only')
PY
done
```
Pre-merge, on this PR: a `## Merge check 1` comment whose anchored reviewer line names Codex at the
standing model and effort (read from the dispatch page, not repeated here), read-only, **and the
current full head SHA** exists — the rule applied to its own merge. Fails fast on any lookup error:
```sh
python3 - <<'PY' || exit 1
import json,re,subprocess
run=lambda *a: subprocess.run(a,capture_output=True,text=True,check=True).stdout
head=json.loads(run('gh','pr','view','166','--json','headRefOid'))['headRefOid']; assert re.fullmatch(r'[0-9a-f]{40}',head), head
rec=re.findall(r'The standing setting on these projects is `([^`]+)`', open('reference/external-agent.md').read()); assert len(rec)==1
model=re.search(r'-m\s+([^\s`]+)',rec[0]).group(1); effort=re.search(r'model_reasoning_effort=([^\s`]+)',rec[0]).group(1)
line=re.compile(r'^Reviewer: Codex, '+re.escape(model)+r' at '+re.escape(effort)+r', read-only — reviewed '+head+r'\s*$', re.M)
pages=json.loads(run('gh','api','--paginate','--slurp','repos/LeonJoeeee/devstandard/issues/166/comments'))
bodies=[c['body'] for page in pages for c in page]
hits=[b for b in bodies if b.lstrip().startswith('## Merge check 1') and line.search(b)]; assert hits, 'no check-1 verdict for the current head with the anchored Codex reviewer line'
print('check-1 verdict for', head[:7], 'by Codex at the standing setting: present')
PY
```
Whether later dispatches follow the rule is failure monitoring (below), not this spec's done-check.

## Failure detection & rollback

This changes the shipped method, so: **detection** — (a) the single-siting assertion goes red
(the setting restated, undated, or moved); (b) a dispatched task on a seeded project routed to a
subagent with no departure stated in its handback; (c) a Codex main session that cannot apply the
rule (the reason or the pointer failing under its topology) — any of these is a defect against this
spec, filed as an issue. **Rollback** — the pages are prose: a revert PR of the shipped pages returns
the previous wording (the `.claude/worktrees/` ignore and every rule outside this change are
untouched); ADR 0040 is not rewritten — it is superseded by a new ADR, and 0011/0024/0034/0036/0038/0039 gain a
further dated block pointing there; the CI assertions revert with the pages. No data, schema or
install state is involved; a stale installed plugin only lags, it does not break.
