---
type: "speckit-legacy-memory-record"
title: "Non-stopping reviewability markers"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-dea0c5ce9989e702"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Non-stopping reviewability markers

[Source: specs/prsg-013-reviewability-markers]
**Branch**: `prsg-013-reviewability-markers` · **Status**: Completed · **Archived**: 2026-06-12

### Summary

PRSG-013 fixes the reviewability sizing product bug: autopilot no longer stops
implementation for size alone. Parseable size warnings and size-only blocks are
recorded as durable PR marker evidence, implementation proceeds in marker
order, and final PR emission can consume the marker plan to create bounded
Foundation or user-story scoped PRs.

### User Stories

- **US1 - Continue through reviewability sizing.** Post-task and final
  reviewability size findings become marker-planning input, while malformed
  evidence and correctness failures still stop.
- **US2 - Emit scoped PRs from durable markers.** Marker planning derives
  stable Foundation and user-story boundaries from `tasks.md`, folds small
  Polish work, and records structured warnings for unsafe subdivisions.
- **US3 - Verify marker planning and emission behavior.** Deterministic
  fixtures and functional eval coverage validate non-stopping behavior,
  marker persistence, implementation ordering, hazard collapse, and Claude/Codex
  guidance parity.

### Functional Requirements

- `plan-layers.sh` records marker-aware plans with source fingerprints,
  marker order, folded Polish tasks, safe subdivision, and stale-plan rejection.
- `final-reviewability-backstop.sh` returns `marker_split` for a valid current
  marker plan when the full diff is size-blocked.
- `multi-pr-emission.sh` validates marker packets before PR side effects and
  supports both scoped marker packets and hazard-collapsed full-spec packets.
- Autopilot guidance requires future runs to checkpoint and record evidence in
  marker order instead of treating size-only reviewability findings as manual
  re-slicing stops.

### Cleanup Note

The active spec folder was removed from `specs/**` cleanup on 2026-06-12 after
PR #157 merged and PRSG-013 contracts/fixtures were preserved under the
autopilot skill payload and test fixtures.
Recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-12-prsg-005-013-post-merge-hygiene.md`.

---
