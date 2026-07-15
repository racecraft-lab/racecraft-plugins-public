---
type: "speckit-legacy-memory-record"
title: "Vertical-slice sizing heuristics in PRD/grill-me"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-817e1394931b08ee"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Vertical-slice sizing heuristics in PRD/grill-me

[Source: specs/prsg-005-slice-sizing-heuristics]
**Branch**: `prsg-005-slice-sizing-heuristics` · **Status**: Completed · **Archived**: 2026-06-12

### Summary

PRSG-005 makes right-sized specs more likely at the earliest scoping moment. It
adds shared SPIDR, INVEST, and vertical-slicing guidance, a deterministic
advisory estimator, and mirrored Claude/Codex updates for `speckit-prd` and
`grill-me` so roadmap entries and grilled specs are born as thin vertical
slices.

### User Stories

- **US1 - Catalog-level decomposition in speckit-prd.** The PRD skill decomposes
  raw ideas into thin vertical roadmap entries, populates the existing
  `Projected reviewable LOC` field from the estimator, and keeps over-ceiling
  findings advisory.
- **US2 - Per-spec validation and split in grill-me.** The grill-me skill runs
  the same estimator for a single spec, recommends vertical splits for oversized
  or horizontal scope, and records the selected split in the design concept.

### Functional Requirements

- Shared SPIDR, INVEST, and vertical-slicing guidance lives in one reference
  document, with only short inline summaries in the skill entrypoints.
- The estimator is deterministic, bash plus `jq`, and emits only `ok` or `warn`.
- `warn`, missing estimator output, malformed size signals, and spike slices
  remain advisory and never block the interview or downstream workflow.
- Claude and Codex skill mirrors preserve behavior equivalence without
  duplicating the estimator or the reference guidance.

### Cleanup Note

The active spec folder was removed from `specs/**` cleanup on 2026-06-12 after
PR #120 merged and archive provenance/recovery commands were recorded.
Recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-12-prsg-005-013-post-merge-hygiene.md`.

---
