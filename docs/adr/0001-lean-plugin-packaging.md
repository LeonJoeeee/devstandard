# 0001 — Package as a lean plugin: one hook + one router + reference files

Status: Superseded by 0007 (2026-06-11)

## Context

A methodology skill auto-triggers from its description at roughly 0% (measured: five description rewrites, zero hits on real dev tasks). Meanwhile the full method is 7,000+ words; injecting it whole into every session is unacceptable — context must split by phase.

## Decision

Package as a plugin: **manifest + one SessionStart hook (injecting ONLY a lean router) + one router skill + many reference files Read on demand**.

Rejected alternatives: **a bare skill** (cannot bundle a hook, so the triggering problem stays unsolved); **one skill per phase** (~10 frontmatter blocks + a brittle chain for a context split that reference files already deliver — over-engineering).

Companion hard rules: cross-file references **never use `@path`** (it force-loads everything at session start, destroying the split); router budget target ≤ 1,500 tokens, ceiling ~2,000 (it is paid in every session).

## Consequences

Triggering becomes reliable; the price is the router's fixed token cost per session. The router must stay a pure dispatcher — all content sinks into reference files.
