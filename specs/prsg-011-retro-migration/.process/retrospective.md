# Retrospective: PRSG-011 Retro-Migration

| Field | Value |
|-------|-------|
| PR | https://github.com/racecraft-lab/racecraft-plugins-public/pull/132 |
| Branch | prsg-011-retro-migration |
| Completed | 2026-06-09T03:33:53Z |
| Mode | Codex autopilot with parent-session fallbacks for unavailable extension commands |

## Outcome

PRSG-011 completed the intended migration path:

- Repository-level migration command for structure marker and legacy navigation backfill.
- Per-spec Tier-2 relocation command for thawed legacy PROCESS artifacts.
- Static suggestion guidance in scaffold and autopilot surfaces without automatic relocation.
- Claude and Codex guidance parity through mirrored skills, dist payloads, functional fixtures, and parity fixture dry-runs.

## What Worked

- The two internal increments kept the review path readable: repository migration first, Tier-2 relocation and guidance second.
- Layer 4 fixtures caught the risky behavior directly: dirty-tree mutation blocks, forced backups, idempotency, collisions, frozen specs, and out-of-scope namespaces.
- The UAT runbook and generated PR body made the final review packet concrete instead of relying on raw workflow notes.

## Friction

- The linked worktree has `.git` as a file, so the PR body could not be written to `.git/speckit-pr-body.md`; it was generated under `/private/tmp` and passed to `gh`.
- `.codex/commands` was absent even though extension command docs exist under `.claude/commands`, so Doctor, Code Review, Cleanup, and Retrospective required explicit parent-session fallback or skip records.
- The registered `uat-runbook-author` agent was not available in this Codex session, so the parent rewrote the generated UAT skeleton in place.

## Residual Risk

- Live parity mode was not run because it invokes external agent prompts and is opt-in. Deterministic parity fixture dry-run and the default test suite passed.
- GitHub CodeQL checks were still pending on the first post-PR poll; no comments or human reviews existed at that poll.

## Recommendation

For a follow-on process hardening pass, make the PR body output path worktree-aware and expose Codex-callable wrappers for installed extension command docs.
