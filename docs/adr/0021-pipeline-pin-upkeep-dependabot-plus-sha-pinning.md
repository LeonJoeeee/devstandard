# 0021 — Pipeline pin upkeep: Dependabot for the pipeline's own actions + SHA-pinning third-party actions

Status: Accepted (2026-07-24)

## Context

A GitHub Actions pipeline's own parts — the `uses:` pins — rot on the vendor's clock, not the project's: actions reach end-of-life and hard-fail on GitHub's cutoff dates (`howto/cicd.md`; evidence `_source/ci-maintenance-industry-alignment.md` §5-B/§5-C). Two industry practices address this, and they are coupled:

- **Dependabot for the pipeline's own action pins** (report §5-B) — first-party, documented practice (GitHub Docs, "Keeping your actions up to date with Dependabot"); Dependabot/Renovate account for 562k of 588k version-bump edits observed in the wild (arXiv 2602.14572). A bot keeps the `uses:` pins current.
- **SHA-pinning third-party actions** (report §5-C) — a non-`actions/*` action pinned to a tag can have that tag rewritten under you; the March 2025 tj-actions/changed-files compromise exposed ~23k repos, and SHA-pinned repos were immune. First-party `actions/*` at a version tag is fine.

The coupling is why they are one decision, not two. An immutable SHA never updates itself, so mandating SHA pins quietly requires the update bot (B); and refusing the bot quietly pushes practice back to rewritable tag pins — the less-secure state C warns against. Deciding either alone lands in an incoherent spot.

An earlier ruling barred bot-driven dependency PRs, but that ruling targeted the PROJECT's own dependencies (report §5, deliberate non-adoptions). This decision does not overturn it — it is explicitly narrowed: bots stay out of the project's dependencies and come in only for the pipeline's own parts.

## Decision

- `howto/cicd.md` gains a `.github/dependabot.yml` template — github-actions ecosystem, directory `/`, weekly — generated in the same setup step as CI, release, and the repo CLAUDE.md. Its PRs ride the normal two checks like any other change. The surrounding text fixes the scope: the pipeline's own actions only; the project's own dependencies stay out (that ruling stands, now narrowed to say so explicitly).
- `howto/cicd.md` gains the third-party SHA-pin line under the CI template's permissions sentence: non-`actions/*` actions pin to a full commit SHA, first-party `actions/*` at a version tag is fine, and the line names the Dependabot file as what keeps those SHAs current — closing the B↔C coupling in the reader's view.
- Self-application: devstandard follows its own method — `.github/dependabot.yml` lives in this repo. An audit of both workflows found only `actions/checkout@v4` (first-party `actions/*`) in each, so no SHA-pinning is needed here today; the config keeps that pin current and covers any third-party action a later change might add.

Rejected: SHA-pinning without the bot (the SHA would silently rot); the bot for project dependencies (out of scope — the prior ruling stands); framing either half as a mandated method line rather than the setup-step default (kept as tooling the setup generates, an opt-in shape).

## Consequences

The pipeline's `uses:` pins stay current automatically, and any third-party action a project later adds is SHA-pinned with a bot maintaining it — the tj-actions failure mode is closed by construction. Cost: one more generated file per project and a stream of small bot PRs, each riding the two checks — bounded by scope (github-actions ecosystem only) and cadence (weekly). The scope line and this ADR record that project dependencies remain deliberately outside the method, so the narrowing cannot be misread as a general dependency-automation policy. No contradiction with the dependency-automation scope ruling as narrowed.
