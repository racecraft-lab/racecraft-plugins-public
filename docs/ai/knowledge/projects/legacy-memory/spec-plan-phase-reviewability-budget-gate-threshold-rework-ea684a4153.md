---
type: "speckit-legacy-memory-record"
title: "Plan-phase reviewability budget + gate threshold rework"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-ea684a4153d32bc3"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Plan-phase reviewability budget + gate threshold rework

[Source: specs/prsg-006-reviewability-budget]
**Branch**: `prsg-006-reviewability-budget` · **Status**: Completed · **Archived**: 2026-06-13

### Summary

Added preventive reviewability sizing: plan-phase LOC estimation, production-only
diff metrics, greenfield allowance, surface count downgraded to warning, and
typed reviewability exceptions. The shipped behavior lives in
`estimate-reviewable-loc.sh`, `reviewability-gate.sh`, templates, guidance, and
Layer 4 fixtures.

### Cleanup Note

The active spec folder was removed after PR #119 merge provenance and recovery
commands were recorded.

---
