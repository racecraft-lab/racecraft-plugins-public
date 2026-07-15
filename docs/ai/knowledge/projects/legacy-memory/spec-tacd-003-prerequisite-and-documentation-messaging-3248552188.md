---
type: "speckit-legacy-memory-record"
title: "TACD-003 Prerequisite and Documentation Messaging"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-324855218894b43d"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# TACD-003 Prerequisite and Documentation Messaging

[Source: specs/tacd-003-prerequisite-and-documentation-messaging]
**Branch**: `tacd-003-prerequisite-and-documentation-messaging-slice/01-foundation` · **Status**: Completed · **Archived**: 2026-06-19

### Summary

TACD-003 completed the prerequisite and user-facing messaging tier for the
tool-agnostic capability discovery roadmap. It replaces the named optional MCP
inventory in `check-prerequisites.sh` with one successful
`capability_coverage` advisory, updates active Claude and Codex prerequisite
guidance to describe capability coverage and fallback confidence, aligns plugin
limitation and coach/autopilot docs with capability-first wording, and refreshes
source-derived generated payloads.

### User Stories

- **US1 - Non-blocking capability advisory.** Operators see optional
  research/context coverage as a successful advisory instead of a setup failure.
- **US2 - Capability-first user guidance.** Active prerequisite and limitation
  docs explain codebase context, library documentation, web or domain research,
  and source extraction without promoting a fixed optional tool set.
- **US3 - Focused regression coverage.** Maintainers have deterministic checks
  for advisory shape, JSON output, missing optional capability success, true
  blocker preservation, and changed active guidance.

### Functional Requirements

- Replace the fixed optional-tool report with one `capability_coverage` check.
- Keep optional capability absence non-blocking when acceptable fallback
  evidence exists.
- Preserve true prerequisite blockers with actionable failure messaging.
- Update active Claude/Codex prerequisite, plugin limitation, coach, and
  autopilot guidance to use capability-first wording.
- Leave broad static enforcement, Layer 3 eval updates, Layer 5 pointer
  coverage, and broad named-tool detection to TACD-004.
- Regenerate generated payload copies from source rather than hand-editing
  `dist/**`.

### Success Criteria

- Missing optional capability paths remain successful and emit one parseable
  `capability_coverage` advisory.
- Changed active guidance contains capability categories instead of a fixed
  optional-tool recommendation.
- Focused Layer 4 and default deterministic test suites pass.
- PR packet evidence and reviewability state identify TACD-004 as the follow-up
  for final enforcement.

### Cleanup Note

The active spec folder was removed from `specs/**` cleanup after PR #230 merged.
Recovery commands and provenance are recorded in
`.specify/memory/archive-reports/2026-06-19-tacd-003-post-merge-hygiene.md`.

---
