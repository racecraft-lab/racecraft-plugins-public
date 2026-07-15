---
type: "speckit-legacy-memory-record"
title: "TACD-004 Verification Coverage"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-a504711de649098c"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# TACD-004 Verification Coverage

### Summary

TACD-004 is the final Tool-Agnostic Capability Discovery spec. It locks the
vendor-neutral optional-tool contract with deterministic guards plus functional
eval coverage, and repairs the Claude payload-build `strip_codex_guard` defect
that installed 8 of 10 Claude skills with empty bodies.

### User Stories

- As a maintainer, I want a deterministic check that fails when active runtime
  guidance reintroduces a hardcoded named optional-tool contract.
- As a maintainer, I want structural checks proving every capability-dependent
  agent points to the shared capability-discovery directive and that the pointer
  resolves from the installed `dist/**` layout.
- As a maintainer, I want the four functional eval expectations rewritten to
  assert both the absence of a named set and an affirmative capability-first
  answer.
- As a consumer, I want every installed skill to ship its full body, with a
  deterministic check that fails if the Claude payload truncates a `SKILL.md`.

### Functional Requirements

- Named-tool guard (Layer 5) plus full removal of the named MCP assertions.
- Pointer-coverage and target-resolution guards (Layer 1) against
  `dist/claude/**` and `dist/codex/**`.
- `strip_codex_guard` section-boundary fix, `dist/` rebuild, and a
  body-completeness guard.
- Vendor-neutral eval rewrites with behavior-observable scenarios and
  Claude/Codex parity, validated by committed fixtures with no live-run merge
  gate.

### Success Criteria

- The default deterministic suite passes: `bash tests/speckit-pro/run-all.sh`.
- Each new guard is non-vacuous: a deliberate regression fails it.
- All 8 truncated Claude skill bodies are restored.

### Cleanup Note

The active spec folder was removed from `specs/**` cleanup after PR #240 merged.
Recovery commands and provenance are recorded in
`.specify/memory/archive-reports/2026-06-22-tacd-004-post-merge-hygiene.md`.
