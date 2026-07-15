---
type: "speckit-legacy-memory-record"
title: "Non-stopping reviewability markers"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-b4a3c9a330ce5fad"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Non-stopping reviewability markers

[Source: specs/prsg-013-reviewability-markers]
**Branch**: `prsg-013-reviewability-markers` · **Status**: Completed · **Archived**: 2026-06-12

### Dependencies & Versions

- Bash plus `jq`, `git`, and GitHub CLI at PR-emission boundaries.
- Builds on PRSG-008 layer planning, PRSG-009 multi-PR emission, and PRSG-010
  final reviewability backstop ordering.
- Preserves Claude and Codex autopilot guidance parity.

### Architecture / Approach

- `plan-layers.sh` adds marker-aware planning and persisted source
  fingerprints.
- `final-reviewability-backstop.sh` consumes valid marker plans and returns a
  `marker_split` proceed outcome for full-diff size blocks.
- `multi-pr-emission.sh` validates marker packets, emits scoped marker packets,
  and supports hazard-collapsed full-spec output.
- Workflow/state evidence records marker order, checkpoint expectations,
  warnings, final backstop evidence, and PR-emission mapping.

### Test Strategy

- PR #157 passed PR Checks, CodeQL, `test(speckit-pro)`,
  `validate-plugins`, `validate-pr-title` after title repair, and `detect`.
- Autopilot evidence records the default deterministic suite passing
  `2587/2587` before merge.
- Post-cleanup verification is recorded in
  `.specify/memory/archive-reports/2026-06-12-prsg-005-013-post-merge-hygiene.md`.

### Cleanup Notes

`specs/prsg-013-reviewability-markers` was removed from active `specs/**`
cleanup on 2026-06-12 after PR #157 merged and PRSG-013 contracts/fixtures were
preserved under the autopilot payload and Layer 4 fixtures.

---
