---
type: "speckit-legacy-memory-record"
title: "PRSG-010 Archive Cleanup Application"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-2364de89019ae8c8"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# PRSG-010 Archive Cleanup Application

[Source: .specify/memory/archive-reports/2026-06-11-prsg-010-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-11
- **Cleanup branch**: `codex/prsg-010-archive-hygiene`
- **Cleanup command**: `git rm -r specs/prsg-010-harden-the-hatch`
- **Fixture-decoupling prerequisite**: PRSG-010 contract schemas live at `speckit-pro/skills/speckit-autopilot/contracts/`, and Layer 4/Layer 8 tests cover final-backstop, contextual-router, O5, and parity behavior without the live spec folder.
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/prsg-010-harden-the-hatch`
- **Recovery**: use the PRSG-010 `git show` / `git checkout` commands recorded above.

The removed source folder was already archived in project memory. Layer 4
coverage remains active through payload-included contract schemas and fixtures
under `tests/speckit-pro/unit/fixtures/`.

---
