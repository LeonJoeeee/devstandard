# 0005 — Parallel model: one session/branch/worktree per task; merging belongs to main; CI/CD in the standard

Status: Accepted (2026-06-10)

## Context

Normal development is many Claude Code sessions in parallel. Parallel work needs collision-free isolation, a shared reference, and a guarded main branch — main is the foundation everyone syncs from; break it once and every worktree inherits the breakage.

## Decision

1. **One session = one branch = one worktree = one task**; all sessions treat `docs/architecture.md` as the shared baseline.
2. **Task sessions only deliver (push their branch); merging is main's act**: CI must be green; an architecture-touching merge additionally passes the human + updates the architecture doc + writes an ADR. Architecture changes are never kept private in a worktree.
3. After a core change merges: other in-flight sessions pause, sync the new baseline, then continue (default; tune with practice).
4. **CI is in the standard**: tests must be green before merging to main (the rule) + repo creation generates a minimal GitHub Actions workflow (the robot — guards against "forgot to run tests" and "ran them and lied").
5. **CD is in the standard too** (the human: hold a high standard — if it ships, it ships): repo creation must answer "what is this project's release form?" (service → deploy; tool/library → publish a package; plugin → marketplace/repo) and generate the release pipeline. Default trigger: **a version tag** — tagging releases; the human still decides when. Fully automatic release-on-merge is a per-project opt-in.
6. Inside a task, no further worktrees (implementation is sequential, verification is parallel) — no nesting with the outer layer.

## Consequences

Parallel work gets complete traffic rules; the price is two robot configs per project and a synchronization point ("core changes wait for the human") — which is exactly the one altitude where the human belongs.
