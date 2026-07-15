---
type: "speckit-legacy-memory-record"
title: "DOC-006 Safe interactive selector and validation aids"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-7016090898dff837"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# DOC-006 Safe interactive selector and validation aids

[Source: .specify/memory/archive-reports/2026-06-17-doc-006-post-merge-hygiene.md]
**Branch**: `codex/doc-006-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-17

### Summary

DOC-006 converted the choose-your-path route into a static-first interactive aid
surface. It keeps complete fallback content in semantic HTML while adding
platform and install-scope selection, copyable Claude Code and Codex command
guidance, repository-only manifest consistency checks, a generated payload flow
diagram, first-run checkpoints, and lightweight handoffs for mismatch or caution
states.

### User Stories And Requirements

- New and returning users can select the platform and supported install scope
  that matches their environment.
- Selected path guidance keeps Claude Code and Codex commands separated and
  labels commands as copyable guidance, not browser-executed local actions.
- Maintainers and evaluators can inspect source and generated payload manifest
  consistency for repository files only.
- The generated payload diagram and first-run checklist remain usable without
  browser scripting.
- Focused validation detects command-surface leakage, missing selector fields,
  checker mismatch/unavailable states, unsafe local-diagnostic UI, handoff
  drift, and missing first-run checkpoints.

### Edge Cases

- Unsupported or ambiguous selector states show explicit text and keep the
  complete supported static path guidance reachable.
- Missing metadata renders unavailable states instead of stale generated facts.
- Intentional packaging differences are informational rows, not false
  mismatches.
- Browser behavior does not read user files, accept pasted JSON, write config,
  install plugins, run shell commands, or invoke plugin workflows.

### Success Criteria

- Every supported selector path includes platform, scope, prerequisites,
  commands, success signals, and next docs links.
- Repository checker rows show compared values and consistency rules.
- Static fallback content covers selector guidance, checker facts, payload
  diagram nodes, and first-run checkpoints.
- Keyboard and source review confirm native controls, visible selected state,
  and readable command/checker content.

### Cleanup Note

The DOC-006 workflow and PR-packet evidence folder was removed from active
`specs/**` cleanup after PR #203 merged. Recovery commands and provenance are
recorded in the DOC-006 archive report.
