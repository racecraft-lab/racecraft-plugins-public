---
type: "speckit-legacy-memory-record"
title: "Layer-planner: tasks.md to ordered increments"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-5c5e4b861e04b907"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Layer-planner: tasks.md to ordered increments

[Source: specs/prsg-008-layer-planner]
**Branch**: `prsg-008-layer-planner` · **Status**: Completed · **Archived**: 2026-06-10

### Summary

Adds a read-only PRSG-008 planner for the PR-size governance split-PR engine.
`plan-layers.sh` accepts a feature directory, parses its `tasks.md`, and emits a
deterministic versioned JSON layer plan to stdout with no repository writes. The
planner remains independent from PRSG-007 routing and PRSG-009 branch/PR
emission.

### User Stories

- **US1 — Stable layer-plan envelope.** `speckit-autopilot` can pass one feature
  directory and receive stable JSON with `ok`, `invalid_plan`, or `input_error`
  status and concise stderr diagnostics.
- **US2 — Ordered increment parser.** Foundation, user-story, and Polish sections
  are grouped into semantic increments such as `foundation`, `us1`, `us2`, and
  `polish`, using `## Dependencies & Execution Order` plus
  `### Incremental Delivery` as authoritative ordering.
- **US3 — Structured diagnostics.** Malformed task plans fail with schema-backed
  machine-readable errors, while missing file/test references remain warnings.
- **US4 — Autopilot gate.** Autopilot runs the planner after PRSG-007 route
  recording only for `split-PR`, persists successful envelopes, and stops before
  implementation on planner errors.

### Functional Requirements

- The CLI is
  `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh <feature-dir>`.
- Successful plans write stable JSON to stdout and no files.
- Usage/input errors exit `2`; invalid task plans exit `1`; success exits `0`.
- Output uses a single versioned envelope with increments, tasks, warnings,
  errors, summary counts, repo-relative paths, source line numbers, checkbox
  state, `[P]` metadata, dependencies, and counts-only advisory size metadata.
- Invalid-plan diagnostics use stable codes/details for missing headings, empty
  increments, unknown increments, dependency cycles, contradictory ordering,
  duplicate IDs, and malformed task-like lines.
- Path fields are normalized relative to the worktree root with leading `./` and
  redundant `.` segments removed.
- PRSG-008 does not create branches, PR bodies, restack metadata, or multi-PR
  topology; PRSG-009 owns emission.

### Success Criteria

- Layer 4 planner fixtures validate stable success, warnings, invalid-plan,
  input-error, read-only, determinism, schema, and generated 200-task behavior.
- Direct PRSG-008 dogfood planning returned `status=ok`, 6 increments, and 45
  tasks during implementation validation.
- PR #138 CI recorded successful PR Checks, CodeQL, and post-merge main checks.

### Cleanup Note

The active spec folder was removed from `specs/**` cleanup on 2026-06-10 after
the Layer 4 planner harness was decoupled from the live spec schema by vendoring
`tests/speckit-pro/unit/fixtures/plan-layers/contracts/plan-layers.schema.json`.

---
