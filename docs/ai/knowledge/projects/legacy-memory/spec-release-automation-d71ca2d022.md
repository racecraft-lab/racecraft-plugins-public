---
type: "speckit-legacy-memory-record"
title: "Release Automation"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-d71ca2d022893fd8"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Release Automation

[Source: specs/003-release-automation]
**Branch**: `003-release-automation` · **Status**: Completed · **Archived**: 2026-06-13

### Summary

Added release automation for `speckit-pro`: GitHub release workflow wiring,
release-please v4 integration, marketplace version sync after release creation,
and release safety documentation. The shipped contract lives in
`.github/workflows/release.yml`, release-please config, and the marketplace sync
script.

### Cleanup Note

The active spec folder was removed after PR #3 merge provenance and recovery
commands were recorded.

---
