---
type: "speckit-legacy-memory-record"
title: "PRSG-008 Archive Cleanup Application"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-bb8ea35715bf50f7"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# PRSG-008 Archive Cleanup Application

[Source: .specify/memory/archive-reports/2026-06-10-prsg-008-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-10
- **Cleanup branch**: `codex/archive-prsg-008-hygiene`
- **Cleanup command**: `git rm -r specs/prsg-008-layer-planner`
- **Fixture-decoupling prerequisite**: `test-plan-layers.sh` now reads the vendored schema fixture at `tests/speckit-pro/unit/fixtures/plan-layers/contracts/plan-layers.schema.json`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/prsg-008-layer-planner`
- **Recovery**: use the PRSG-008 `git show` / `git checkout` commands recorded above.

The removed source folder was already archived in project memory. Layer 4
planner coverage remains active through fixture task files and the vendored
schema contract fixture under `tests/speckit-pro/unit/fixtures/plan-layers/`.

---
