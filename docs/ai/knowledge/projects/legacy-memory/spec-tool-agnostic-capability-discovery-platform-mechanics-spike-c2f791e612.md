---
type: "speckit-legacy-memory-record"
title: "Tool-Agnostic Capability Discovery: platform mechanics spike"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-c2f791e6128359f7"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Tool-Agnostic Capability Discovery: platform mechanics spike

[Source: specs/tacd-001-platform-mechanics-spike]
**Branch**: `tacd-001-platform-mechanics-spike` · **Status**: Completed · **Archived**: 2026-06-18

### Summary

TACD-001 completed the platform-mechanics spike for replacing named optional MCP
preferences in SpecKit Pro with installed-capability discovery. The canonical
report audits active Claude and Codex runtime guidance, prerequisite messaging,
dependency metadata, generated payloads, and eval/test expectations; records a
Claude/Codex capability mechanics matrix; recommends a shared
capability-discovery reference with runtime-specific pointers and approved
equivalents; and defines the TACD-004 category allowlist that separates active
guidance from historical/provenance text.

### User Stories

- **US1 - Audit named-tool references.** Maintainers can see which named-tool
  references are active runtime guidance, prerequisite/user-facing messaging,
  runtime/dependency metadata, deterministic/eval expectations, generated
  source-derived duplicates, historical/provenance, fixture-only, or ambiguous.
- **US2 - Recommend directive home.** TACD-002 implementers have a specific
  directive-home decision: shared capability-discovery reference plus
  runtime-specific pointers or approved equivalents, with TACD-004 proving
  pointer coverage, target resolution, and behavior-observable evals.
- **US3 - Define enforcement categories.** TACD-004 authors can enforce
  vendor-neutral active guidance without over-banning archive records,
  generated duplicates, fixtures, or exact metadata IDs that are still required
  by a runtime schema.

### Functional Requirements

- Produce `docs/ai/research/tool-agnostic-capability-discovery-spike.md` as the
  report and decision record.
- Audit Claude and Codex active guidance, skills/references, prerequisite
  checks, plugin limitation docs, dependency metadata, generated payloads, and
  tests/evals for named optional-tool references.
- Record sanitized source/probe evidence for Claude Code and Codex across
  installed tools, MCP/app connectors, skills/plugins, and repo-local helpers.
- Recommend the directive home and downstream TACD-002/TACD-003/TACD-004
  handoffs without changing runtime behavior in TACD-001.
- Preserve historical/provenance references and avoid committing raw runtime
  inventories, local paths, connector lists, transcripts, or identifiers.

### Success Criteria

- The spike report covers both Claude Code and Codex and all four capability
  classes.
- The directive-home recommendation names the proof bar for shared-reference
  adoption.
- TACD-004 receives a category allowlist with blocked, allowed, and review
  classes.
- The TACD-001 diff remains report/process-only and leaves active runtime
  behavior changes to TACD-002/TACD-003/TACD-004.

### Cleanup Note

The active spec folder was removed from `specs/**` cleanup after PRs #211-#214
merged the spike stack and PR #216 adopted the spike decisions into the PRD and
roadmap. Recovery commands and provenance are recorded in
`.specify/memory/archive-reports/2026-06-18-tacd-001-post-merge-hygiene.md`.

---
