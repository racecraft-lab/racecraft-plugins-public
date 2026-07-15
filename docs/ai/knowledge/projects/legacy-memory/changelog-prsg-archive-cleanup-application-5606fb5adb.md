---
type: "speckit-legacy-memory-record"
title: "PRSG Archive Cleanup Application"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-5606fb5adb212595"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# PRSG Archive Cleanup Application

[Source: .specify/memory/archive-reports/2026-06-09-prsg-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-09
- **Cleanup branch**: `codex/archive-apply-cleanup`
- **Cleanup command**: `git rm -r specs/prsg-007-atomicity-router specs/prsg-011-retro-migration`
- **Fixture-decoupling prerequisite**: PR #136 merged at `128e1927d0fa0ca6e7c0b1545d7b6547cdb4db9f`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/prsg-007-atomicity-router`, `specs/prsg-011-retro-migration`
- **Recovery**: use the PRSG-007 and PRSG-011 `git show` / `git checkout` commands recorded above.

The removed source folders were already archived in project memory. PR #136
vendored the PRSG-007 dogfood/schema fixture under
`tests/speckit-pro/unit/fixtures/atomicity-route/dogfood-atomicity-router/`,
so Layer 4 no longer depends on the live archived spec directory.

---
