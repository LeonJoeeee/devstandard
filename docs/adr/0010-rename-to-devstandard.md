# 0010 — Rename: DevBook → DevStandard

Status: Accepted (2026-07-02). Amended (2026-07-09).

## Context

Going public exposed the name. GitHub search showed the "devbook" namespace crowded, and **every** neighbor interprets "Book" as actual books — a 995★ Korean dev-book list, PDF ebook collections, a developer's handbook, an ebook landing-page template. The name actively steers strangers toward "reading/notes project," missing both the standard and the collaboration halves of what this is. The owner's stated ambition: a universal development standard for medium-to-large projects.

Candidates checked with collision data: bare `discipline` (crowded — a 998★ keyboard, a 336★ Scala library — plus a 403★ conceptual neighbor "Disciplined-AI-Software-Development"); `devdiscipline` (free but clunky, and covers only the rules pillar); `DevCharter` (free and apt — core.md is literally a charter — but less self-evident); `DevStandard` (near-empty namespace, max 13★; the name states the claim).

## Decision

**DevStandard.** The repo is renamed (GitHub redirects old URLs); the plugin and marketplace names become `devstandard`; living documents (README, PRD, architecture, core.md, hook) are updated. Historical records — ADRs 0000–0009 and MIGRATION-BRIEF.md — keep "DevBook" as written: supersede-don't-edit applies to history. Version bumps to 0.3.0 (the install coordinates changed).

Known tradeoff, accepted: "standard" can misread as a code-style guide; the tagline ("The GitHub flow, extended to agent teams") corrects that within the first line.

## Consequences

Install becomes `/plugin marketplace add LeonJoeeee/devstandard` + `/plugin install devstandard@devstandard`. Anyone who installed under the old name must reinstall (zero known users at rename time). The owner's local directory keeps its old path until convenient to move.

**Amendment (2026-07-09, see f847b58):** MIGRATION-BRIEF.md was removed later the same day in the prune f847b58; the ADRs are the remaining preserved DevBook-era record.
