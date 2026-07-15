---
type: "speckit-legacy-memory-record"
title: "PRSG-005 and PRSG-013 Archive Cleanup Application"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-acecd5998ebfced4"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# PRSG-005 and PRSG-013 Archive Cleanup Application

[Source: .specify/memory/archive-reports/2026-06-12-prsg-005-013-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-12
- **Cleanup branch**: `codex/spec-hygiene-prsg-013-005`
- **Cleanup command**: `git rm -r specs/prsg-005-slice-sizing-heuristics specs/prsg-013-reviewability-markers`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/prsg-005-slice-sizing-heuristics`, `specs/prsg-013-reviewability-markers`
- **Recovery**: use the `git show` / `git checkout` commands recorded above.

The removed source folders were already merged and archived in project memory.
PRSG-005 behavior remains covered through shipped skill guidance and estimator
tests; PRSG-013 behavior remains covered through payload-included schemas and
Layer 4 marker fixtures.

---
