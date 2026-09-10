# 0051 — A guard that cannot be complete guards the ordinary case

Status: Accepted (2026-09-10). Amends 0046 (role hooks).

## Context

The role hook is what stands between a role and an operation it must never perform. Between
2026-09-05 and 2026-09-10 it grew to meet each new spelling a review round found: a closed lexical
shell grammar with separators, redirections, wrappers and reserved words; a ten-family refusal table
for the syntax that grammar could not model; a second text scan for the orchestrator when the
grammar gave up; a per-tool-call read of `.github/devstandard-guards.json` from the **remote**
default branch through four GitHub API calls; a bounded retry layer for the transport failures that
read produced on a flapping network; and a head-bound authorization record for every irreversible
orchestrator command.

That machinery cost seven review rounds and three releases over 2026-09-09/10. It refused a worker's
`cd <worktree> && git push --force-with-lease`, a `for` loop over `echo`, a `$(printf …)` inside a
`--jq` argument and a multi-line `python3 -c` — ordinary research and delivery commands, none of
them dangerous. It turned a dropped network connection into a refusal a worker was told to retry.
And it never claimed to be complete: ADR 0046's own limitation sentence says this implementation
"does not claim an arbitrary-shell capability boundary," and the shipped page said in as many words
that an interpreter script or an obfuscated spelling passes it. Each round added weight to a fence
whose gate was documented as open.

The human ruled on 2026-09-10: 实在控制不住那就算了，出问题就出问题吧 — a guard that cannot be
complete should guard only the ordinary case, with a rule simple enough to hold in one's head, and
the residual should be accepted rather than chased.

## Decision

**The hook does one thing.** It reads the command's raw text — quotes, here-doc bodies and
substitution bodies included, with no parsing and no grammar — and refuses when that text carries
one of its role's words. A word matches where it begins at a non-identifier position and is not
continued by a hyphen; a rule of several words matches only where those words stand together.
**Unparseable syntax is never a reason to refuse, for any role.**

- **worker:** `merge`, `tag`, `release`, `--force`, `branch -D`, `branch --delete`, `push --delete`,
  `worktree remove`; a recursive `rm` whose targets are not under `/tmp/`; and `push` only where the
  same command also names the default branch. Everything else is admitted, its own task-branch push
  and any composition around it included.
- **reviewer:** read-only — `push`, `merge`, `tag`, `release`, `delete`, `rm`, and a `gh` command's
  `-X`, `--method`, `-f`, `-F`, `--input`. The reviewer agent definition keeps its tool surface.
- **orchestrator:** `gh pr merge` and `git merge`, refused with the reason naming the sole admitted
  entry `<plugin>/scripts/guard merge`; a `push` naming the default branch; and `tag`/`release`
  unless default-branch policy relays a standing release delegation.

**The policy is local.** `.github/devstandard-guards.json` is read once per hook process from the
local `origin/main` ref with `git show`, never over the network inside a tool call and never from
the working tree. A missing ref, a missing file, a directory outside any repository or unparseable
JSON all mean the built-in defaults. **Nothing in the hook refuses because a read failed**, so the
transport-failure vocabulary, the retry layer and the distinct "policy read that could not happen"
reason all go with it.

**One record survives.** `guard merge` still requires the human's head-bound
`devstandard-authorization-v1` comment for an architecture-level merge, and is now its only reader.
Deleting a merged branch or worktree is routine teardown and is admitted with no record. `guard
protection --apply` is not gated by the hook at all; it stays the human's or the main session's by
role instruction and by who holds admin credentials.

**The residual is named and accepted.** Obfuscation, an interpreter script, a forged local ref and
an operation read from runtime data are outside this hook and no rule will be added for them. What
carries the guarantee is the rest of the guard: `guard merge`'s reviewed-head verification, rebase
proof and GitHub reads; branch protection; and the per-role OS sandbox. **A review finding of that
class is a Note, not a defect** — and that clause is the operative half of this decision, because
without it the next round rebuilds the table.

The alternative rejected is the one the last six days took: extend recognition to each newly found
spelling. It converges on a complete shell parser, which the hook is not, cannot become in a
PreToolUse handler, and would still lose to `bash -c "$(curl …)"`.

## Consequences

Refusals are cheaper and more legible: a refusal names a word the caller actually wrote, and every
ordinary command a role runs is admitted. Three behaviours narrow — a worker no longer gets a
recognized-operation exception for `--force-if-includes` alone, a target's `command_patterns` are
now per-role words rather than per-kind regexes, and a repository whose default branch is not `main`
runs on built-in defaults. Three widen: a reviewer's non-`gh` read commands are no longer checked
against an allowlist, an orchestrator's destructive commands outside its three rules are admitted,
and `guard protection --apply` is admitted for every role. Both directions ship in one minor version.

`.github/test-hard-edges.py` keeps a sweep so a regression in the word list still shows, over each
role's words in the bare, quoted, here-doc, substitution and `cd … &&` positions and both tool-input
formats, plus a fixture that decides identically with every network call failing. The adversarial
grammar sweep is deleted rather than weakened, and its sixteen CI shards become two: the suite that
took minutes now runs in seconds. No probe asserts a refusal for an obfuscated construction, because
such a probe would encode a boundary this hook does not claim.

**This ADR decides what the method ships**, not only how this repository operates: every seeded
project's role hook behaves this way.
