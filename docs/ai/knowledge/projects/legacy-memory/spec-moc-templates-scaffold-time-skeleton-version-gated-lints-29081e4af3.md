---
type: "speckit-legacy-memory-record"
title: "MOC templates + scaffold-time skeleton + version-gated lints"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-29081e4af380d92c"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# MOC templates + scaffold-time skeleton + version-gated lints

[Source: specs/prsg-002-moc-templates]
**Branch**: `prsg-002-moc-templates` · **Status**: Completed · **Archived**: 2026-06-13

### Summary

Added the MOC navigation contract: roadmap/spec MOC templates, scaffold-time
`SPEC-MOC.md` creation, version-gated orphan/stale-index lints, namespace-aware
ID normalization, and grandfathering for legacy specs without markers.

### Cleanup Note

The active spec folder was removed after PR #116 merge provenance and recovery
commands were recorded. MOC lint dogfood assertions now use committed fixtures
rather than the live PRSG-002 spec folder.

---
