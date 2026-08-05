# 0028 — This plugin retires its own translations; the mirror rule stands for target projects

Status: Accepted (2026-08-05). Amends 0023 (this repo's own practice only — the rule 0023
states for target projects is unchanged) and 0027 (two claims about the en/zh gate).

## Context

0023 settled that the durable record is English and that a human-facing translation is "a
marked mirror naming its canonical file, changed in the same diff as the canonical". This
plugin then applied that to itself: `core.md` had `core.zh-CN.md`, `README.md` had
`README.zh-CN.md`, and v0.12.1 made the pairing a CI gate after two commits had broken it.

Two years of that arrangement were never audited. Measured now:

- **`hooks/session-start` names only `core.md`.** A grep of the live tree for anything that
  opens the mirror returns two hits: a link in `README.zh-CN.md` for a human, and the CI gate
  itself. **No agent has ever read the translation** — its entire audience is one person.
- **The gate cannot check what the rule requires.** It asserts that `core.zh-CN.md` appears
  in any diff touching `core.md` — co-modification, never agreement. Prose has no mechanical
  equivalence test, so the gate was always a presence check wearing a correctness check's
  name.
- **The drift it permitted is documented, not theoretical.** Three separate check-1 rounds on
  PR #85 found real divergence under a green gate: once the Chinese was *stronger* than the
  English it mirrored (`明确判定` where the English said only "clear"), once `core.md` was
  thinner than both aids on the same clause, once one venue clause read four different ways
  across four files.
- **It doubled the edit cost of the page the method works hardest to keep small.** Every rule
  change to a 5,000-token ceiling page was written twice, by hand, in two languages.

## Decision

`core.zh-CN.md` and `README.zh-CN.md` are deleted, the CI mirror gate and the `fetch-depth: 0`
checkout it required are removed, and `README.md`'s language switcher goes with them. The
repository is English throughout.

**0023's rule is not repealed — it is scoped.** A target project whose record is in another
language still declares it in its repo-root `CLAUDE.md`, and a translation it keeps for humans
is still a marked mirror naming its canonical file and riding the same diff. What that rule
never contemplated is the case here: a translation of *the method's own pages*, whose readers
are agents that read only the canonical, and whose sole human reader is the person who can
read the canonical too. The cost lands entirely on the side that gets no benefit.

**The distinction that makes this consistent rather than convenient:** 0023's mirror serves a
project whose *record* is another language, where the canonical is the translation's source
and both have readers. Here the canonical had every reader and the mirror had a courtesy copy.
A rule about serving a non-English record does not oblige an English-record repo to maintain a
second language nobody's work depends on.

Rejected: (a) keep the mirror and strengthen the gate to check content — there is no
mechanical equivalence test for prose, so this is unimplementable, and the three drifts above
all passed the gate that exists; (b) keep the mirror, drop the gate, accept drift — the worst
option, since a stale translation of the method's own page is a second source of truth that
looks authoritative and disagrees; (c) keep `README.zh-CN.md` and retire only `core.zh-CN.md`
— defensible, since the README costs almost nothing and is a public front page, and it was
put to the human as a separate decision; the human chose to retire both, and a repo that is
English throughout needs no rule about which files are exempt; (d) generate the translation
mechanically at release — it would still be unread by agents, and a machine translation of a
page whose every word has been fought over across dozens of review rounds is worse than none.

## Consequences

`core.md` is untouched, so the token budget is unchanged at 4,560 of 5,000 — but every future
rule change now costs one edit instead of two, which is the real saving on a page with 440
tokens of headroom left. CI drops from five gates to four; the remaining four (hook validity
and size, token budget, no `@path`, version lockstep) are all content checks that can actually
fail for the reason they claim. The installed package loses 32K.

What is lost, and it is not nothing: the human's reading copy of the single most important
page in the method. That was weighed and accepted by the person it costs.

What to watch: whether any target project's translation duty gets read as retired too — 0023's
rule is unchanged and this ADR is the only place the distinction is written down, so a reader
who finds the deleted files without finding this ADR could conclude the method dropped
translations altogether. `core.md:71` still carries the rule for target projects, which is the
line that actually governs.
