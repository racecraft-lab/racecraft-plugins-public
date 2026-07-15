---
type: "speckit-legacy-memory-record"
title: "Retro-migration: version marker + state-keyed backfill/relocate"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-dd3263ba979876da"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Retro-migration: version marker + state-keyed backfill/relocate

[Source: specs/prsg-011-retro-migration]
**Branch**: `prsg-011-retro-migration` · **Status**: Completed · **Archived**: 2026-06-09

### Dependencies & Versions

- Bash + `jq` only; no package manager or compiled build step.
- Reuses `generate-spec-index.sh` and the MOC ID/frontmatter helper libraries.
- Mirrors archive-extension safety: dry-run/apply separation, clean-tree guards,
  backups, and recovery commands.

### Architecture / Approach

- `migrate-structure.sh`: repo-level structure marker, Tier-1 edits, and Tier-0
  navigation backfill.
- `relocate-process-artifacts.sh`: explicit Tier-2 relocation for thawed legacy
  specs only.
- `speckit-upgrade`, `speckit-scaffold-spec`, and `speckit-autopilot` document
  the new behavior; scaffold/autopilot suggest the codemod but never auto-run it.

### Test Strategy

- Layer 4 covers migration dry-run/apply, idempotency, dirty-tree failure,
  backup behavior, relocation allow-list, collisions, and ID normalization.
- Layer 3/8 fixtures cover Claude/Codex guidance parity for Tier-2 suggestions.
- PR #132 CI recorded validate-plugins, test(speckit-pro), detect, CodeQL, and
  code scanning as successful; `validate-pr-title` failed on the already-merged
  title and is recorded as a metadata gate exception.

### Cleanup Notes

The source spec folder was removed from active `specs/**` cleanup on 2026-06-09
after PR #136 decoupled Layer 4 dogfood/schema tests from the live PRSG-007
directory and the cleanup gate recorded `safeToApplyCleanup=true`.

---
