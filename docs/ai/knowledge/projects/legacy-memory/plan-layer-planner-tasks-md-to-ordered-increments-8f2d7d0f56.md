---
type: "speckit-legacy-memory-record"
title: "Layer-planner: tasks.md to ordered increments"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-8f2d7d0f566b0755"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Layer-planner: tasks.md to ordered increments

[Source: specs/prsg-008-layer-planner]
**Branch**: `prsg-008-layer-planner` · **Status**: Completed · **Archived**: 2026-06-10

### Dependencies & Versions

- Bash + `jq` only; no package manager, compiled build step, Python runtime, or
  network dependency in the shipped planner.
- Reads a local feature directory's `tasks.md` and emits JSON to stdout.
- Autopilot orchestration persists successful layer-plan envelopes to existing
  workflow/state surfaces when the PRSG-007 route is exactly `split-PR`.

### Architecture / Approach

- One production script:
  `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh`.
- One schema-backed output contract under the archived PRSG-008 spec artifacts,
  with the Layer 4 test harness carrying a vendored schema fixture after cleanup.
- Deterministic Bash parsing of headings, checkbox tasks, dependency order,
  incremental delivery order, file/test references, and warning/error envelopes.
- Autopilot prose in Claude and Codex surfaces runs the planner only after
  post-G5 atomicity routing and before Analyze/implementation when route is
  `split-PR`; all other routes skip layer planning.

### Test Strategy

- `bash tests/speckit-pro/unit/test-plan-layers.sh` covers planner
  contract behavior and passed `66/66`.
- `bash tests/speckit-pro/run-all.sh --layer 4` passed `1029/1029`.
- `bash tests/speckit-pro/run-all.sh --layer 1` passed `887/887`.
- `bash tests/speckit-pro/run-all.sh` passed `2106/2106`.
- PR #138 post-merge main checks passed Release and CodeQL runs for merge commit
  `deccd8a2a9916e11edfad43df8ceef95a756dc04`.

### Cleanup Notes

`specs/prsg-008-layer-planner` was removed from active `specs/**` cleanup on
2026-06-10 after the planner schema was vendored under
`tests/speckit-pro/unit/fixtures/plan-layers/contracts/` and focused
planner tests passed from the fixture-backed schema.

---
