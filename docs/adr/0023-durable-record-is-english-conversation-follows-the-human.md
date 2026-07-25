# 0023 — The durable record is English; the conversation follows the human

Status: Accepted (2026-07-25)

## Context

The rule "reply to the user in Chinese; all artifacts in English" lived only in the human's global `~/.claude/CLAUDE.md`, which they cleared as duplicative of DevStandard (issue #64) — verified empty (0 bytes). The method must carry it or it is gone. A model mirrors the language of its prompt, so a session held in Chinese produces Chinese commits, issues and ADRs with nobody deciding to; commit messages and the issue/PR history are immutable, so the drift is unrecoverable. Under the method's own issue-first rule (core.md line 57) the agent — not the human — writes the issue that becomes the worker's handoff spec and the fresh reviewer's requirements input, so "the human's words" is not a carve-out.

## Decision

Everything an agent writes that lands in the repo or on GitHub — code, comments, docs, commits, issues, PRs, ADRs, specs, including text it writes up from what the human said — is English, whatever language the session is held in, because English is the one language every future agent, reader and tool shares. What a product shows its own users (interface text, user docs) follows that product's audience. Everywhere else the agent speaks the human's language. A repo overrides the record language only by declaring it in its repo-root `CLAUDE.md` — never per file, never per agent — and a record already written in another language counts as decided: the agent writes the declaration and follows the existing record rather than starting a second language. A human-facing translation is a marked mirror naming its canonical file, changed in the same diff as the canonical.

Rejected: (a) leaving the rule in personal config — verified empty, and the method cannot depend on a file it does not ship; (b) scoping the rule by intent ("the agent's own words") rather than by venue — the issue-first flow makes the agent the author of the human's task statement, so intent gives two readings with no tiebreak; (c) stopping to ask the human on encountering an undeclared non-English record — core.md line 33 restricts asking to three axes, the existing record already answers the question, and every change passes a PR the human sees.

This does NOT amend ADR 0008. Its "names no concrete models — the concrete mapping and quota policy are personal config" bullet is about models and stands (see 0024 for the part that does change): models are per-human market and quota ephemera; the language of the shared record is a property every agent, reader and tool must read.

## Consequences

core.md grows ~213 tokens of permanent every-session budget. `howto/cicd.md`'s "three kinds of content, nothing else" fence gains its first conditional exception, named as such in the fence itself so the page does not contradict itself. The plugin's own core.md / core.zh-CN.md pair is the reference implementation of the mirror clause; README.zh-CN.md is brought into compliance in the same change. The override deliberately requires a written declaration in the one file Claude Code loads natively in the repo at every session start (0018), never an agent's inference from files it happened to open. What to watch: a repo whose record language is switched later still cannot fix its commit, issue and PR history — the rule's whole point.
