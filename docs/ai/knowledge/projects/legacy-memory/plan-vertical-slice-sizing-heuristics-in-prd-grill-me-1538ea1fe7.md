---
type: "speckit-legacy-memory-record"
title: "Vertical-slice sizing heuristics in PRD/grill-me"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-1538ea1fe71c2e6a"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Vertical-slice sizing heuristics in PRD/grill-me

[Source: specs/prsg-005-slice-sizing-heuristics]
**Branch**: `prsg-005-slice-sizing-heuristics` · **Status**: Completed · **Archived**: 2026-06-12

### Dependencies & Versions

- Bash plus `jq`; no package manager or compiled build step.
- Applies to Claude and Codex `speckit-prd` and `grill-me` skill mirrors.
- Feeds the existing roadmap `Projected reviewable LOC` field without adding a
  new roadmap schema.

### Architecture / Approach

- `estimate-spec-size.sh` provides the shared deterministic advisory estimator.
- `slicing-heuristics.md` is the single source of truth for SPIDR, INVEST, and
  vertical-slicing guidance.
- `speckit-prd` applies the guidance at catalog-authoring time.
- `grill-me` applies the same sizing branch to single-spec scoping and records
  the chosen split for later scaffold/autopilot phases.

### Test Strategy

- PR #120 passed PR Checks, CodeQL, `test(speckit-pro)`,
  `validate-plugins`, `validate-pr-title`, and `detect`.
- Task evidence records `20/23` implementation tasks complete, with Layer 2,
  Layer 3, and Layer 8 developer-local follow-ups intentionally not required as
  merge blockers.
- Post-cleanup verification is recorded in
  `.specify/memory/archive-reports/2026-06-12-prsg-005-013-post-merge-hygiene.md`.

### Cleanup Notes

`specs/prsg-005-slice-sizing-heuristics` was removed from active `specs/**`
cleanup on 2026-06-12 after PR #120 merged and archive recovery commands were
recorded.

---
