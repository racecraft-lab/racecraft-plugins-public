---
type: "speckit-legacy-memory-record"
title: "Reviewer-ready PR packet contract"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-f43d4f36cc0f2be4"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Reviewer-ready PR packet contract

[Source: specs/prsg-012-reviewer-ready-pr-packet-contract]
**Branch**: `prsg-012-reviewer-ready-pr-packet-contract` · **Status**: Completed · **Archived**: 2026-06-13

### Summary

PRSG-012 makes autopilot-generated PR packets reviewer-ready before creation. It
adds generated conventional titles with future-spec scope support, structured
neutral PR descriptions, pre-create PR packet validation, split-PR validation
ordering, safe editable prose fields, and regression tests that prevent raw
evidence dumps or patronizing labels from entering PR descriptions.

### Cleanup Note

The active spec folder was removed after PR stack #164-#168 merged. The PRSG-012
feature and marker-plan test dependencies are preserved under
`tests/speckit-pro/unit/fixtures/`; recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-13-merged-specs-post-merge-hygiene.md`.

---
