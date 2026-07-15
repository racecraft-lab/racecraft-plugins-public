---
type: "speckit-legacy-memory-record"
title: "TACD-002 Capability Discovery Directive and Agent Updates"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-a7596a85f931125e"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# TACD-002 Capability Discovery Directive and Agent Updates

[Source: specs/tacd-002-capability-discovery-directive-and-agent-updates]
**Branch**: `tacd-002-capability-discovery-directive-and-agent-updates` · **Status**: Completed · **Archived**: 2026-06-18

### Summary

TACD-002 implemented the tool-agnostic capability-discovery directive selected
by TACD-001. The shipped behavior adds the shared directive at
`speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`,
updates scoped Claude and Codex agents to choose research/context help by
capability need, keeps fallback evidence transparent with confidence levels,
preserves exact tool IDs only as metadata or generated runtime evidence, and
refreshes generated Claude/Codex payloads from source.

TACD-002 also hardened marker PR emission after the real post-implementation
flow exposed branch namespace, title-normalization, and changed-file scope
blockers. The emitter now separates emitted branch prefixes from source feature
directories, derives reviewer-safe PR titles from story boundaries, and admits
declared tests, generated payload counterparts, and standard SpecKit process
evidence while still blocking unrelated undeclared files.

### User Stories

- **US1 - Agents choose by capability need.** Operators get guidance that names
  capability categories instead of preferred optional MCP tool sets.
- **US2 - Agents work without optional capabilities.** Agents continue with
  local, native platform, or repo-local fallback evidence and lower-confidence
  disclosure when optional capabilities are missing or unusable.
- **US3 - Runtime guidance stays semantically aligned.** Claude and Codex
  guidance share one semantic directive or an approved installed-runtime
  equivalent.
- **US4 - Generated payloads match source guidance.** Generated Claude and Codex
  payloads are refreshed from source and trace back to source guidance changes.
- **US5 - Marker emission survives branch namespace conflicts.** Ordered marker
  slice PRs can be emitted from a source feature directory even when the emitted
  branch prefix must avoid an existing parent branch ref.

### Functional Requirements

- Active behavior guidance selects capabilities by task need and evidence fit.
- Guidance covers codebase context, spec context, library documentation, web or
  domain research, source extraction, installed skills/plugins, and repo-local
  helpers.
- Claude agents point to the shared directive; Codex TOML agents include the
  approved compact-equivalent marker where direct Markdown pointer resolution is
  not stable.
- Discovery-informed answers report capability path, evidence, and confidence.
- Generated payloads are refreshed from source through
  `bash scripts/build-plugin-payloads.sh`.
- Marker emission supports `--source-feature-dir` separately from emitted
  branch prefix, normalizes public titles, and validates expected generated and
  process evidence.

### Success Criteria

- Scoped source and generated behavior surfaces no longer contain preferred
  named optional-tool wording.
- Source and generated Claude/Codex runtime guidance remain semantically
  aligned.
- Preserved exact IDs are classified as metadata, historical/provenance, or
  generated rewrite evidence rather than active preferred behavior.
- Focused marker-emission regressions and the deterministic SpecKit suite pass.

### Cleanup Note

The active spec folder was removed from `specs/**` cleanup after PRs #221-#226
merged the TACD-002 stack. Recovery commands and provenance are recorded in
`.specify/memory/archive-reports/2026-06-18-tacd-002-post-merge-hygiene.md`.

---
