---
type: "speckit-legacy-memory-record"
title: "DOC-005 First successful workflow tutorial and lifecycle explainer"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-50e39cd2f1f7f3fc"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# DOC-005 First successful workflow tutorial and lifecycle explainer

[Source: .specify/memory/archive-reports/2026-06-16-doc-005-post-merge-hygiene.md]
**Branch**: `codex/doc-005-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-16

### Summary

DOC-005 converted the `/first-run` and `/spec-kit-lifecycle` route shells into
source-backed onboarding content. It defines first success as a visible
artifact trail rather than a merged PR, separates Claude Code
`/speckit-pro:<skill>` commands from Codex `$speckit-*` commands, records a
validated Codex `specify init --here --integration codex
--integration-options="--skills" --script sh` snippet, and explains the idea,
PRD, roadmap, scaffold, autopilot, validation, and G1-G7 gate lifecycle.

### User Stories And Requirements

- New Claude Code and Codex users can start from the correct platform install
  route before running a first workflow.
- Users can check Spec Kit CLI, constitution, roadmap, branch, GitHub CLI, and
  JSON tooling prerequisites before scaffolding or running autopilot.
- Users can identify the expected artifacts for PRD, roadmap entry, scaffolded
  workflow/spec, autopilot phase output, and validation evidence.
- The lifecycle explainer exposes phase outputs and gate meanings as visible
  semantic content with a static fallback path.
- Command examples remain platform-specific and avoid browser-executed local
  plugin runs.

### Edge Cases

- Missing roadmap entries route users back to PRD or roadmap creation before
  scaffold.
- Missing scaffold output requires inspecting scaffold evidence and the
  roadmap target before continuing.
- Partial autopilot output uses `autopilot-state.json`, phase artifacts,
  checklists, tasks, and PR-packet evidence to continue from the recorded
  phase.
- Failed validation checkpoints are recorded in review evidence and handed off
  to troubleshooting rather than expanding the first-run route into a full
  diagnostic matrix.

### Success Criteria

- The first-run page identifies success as artifacts plus validation evidence,
  not merged PR completion.
- Claude Code and Codex command surfaces are visually separated.
- The lifecycle page covers idea, PRD, roadmap, scaffold, specify, clarify,
  plan, checklist, tasks, analyze, implement, and G1-G7 gates.
- The lifecycle visualizer works as static HTML with visible text and no client
  JavaScript or shell execution.

### Cleanup Note

The residual DOC-005 PR-packet evidence folder was removed from active
`specs/**` cleanup after PRs #198-#201 merged. Recovery commands and
provenance are recorded in the DOC-005 archive report.

---
