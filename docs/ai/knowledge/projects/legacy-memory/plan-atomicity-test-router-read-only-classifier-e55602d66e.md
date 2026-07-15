---
type: "speckit-legacy-memory-record"
title: "Atomicity-test router (read-only classifier)"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-e55602d66e724585"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Atomicity-test router (read-only classifier)

[Source: specs/prsg-007-atomicity-router]
**Branch**: `prsg-007-atomicity-router` · **Status**: Completed · **Archived**: 2026-06-09

### Dependencies & Versions

- Bash + `jq` only; no package manager or compiled build step.
- Reads local `tasks.md`, `plan.md`, and `spec.md`; no network, GitHub, or
  reviewability-gate dependency.

### Architecture / Approach

- One production script:
  `speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh`.
- Small duplicated surface/path matchers rather than a shared abstraction with
  `reviewability-gate.sh`.
- Autopilot documentation records the post-Tasks/G5 route handoff; Codex skill
  prose mirrors the Claude skill prose.

### Test Strategy

- `bash tests/speckit-pro/run-all.sh --layer 4` covers router fixtures and
  dogfood behavior.
- `bash tests/speckit-pro/run-all.sh --layer 1` covers structural and Codex
  parity checks.
- PR #133 CI recorded validate-plugins, test(speckit-pro), detect,
  validate-pr-title, and CodeQL as successful.

### Cleanup Notes

`specs/prsg-007-atomicity-router` was removed from active `specs/**` cleanup on
2026-06-09 after PR #136 moved the dogfood/schema tests to committed fixtures
independent of the active spec tree.

---
