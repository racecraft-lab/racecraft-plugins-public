---
type: "speckit-legacy-memory-record"
title: "Multi-PR emission (post-implementation rewrite)"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-aabe1aebb53b4c59"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Multi-PR emission (post-implementation rewrite)

[Source: specs/prsg-009-multi-pr-emission]
**Branch**: `prsg-009-multi-pr-emission` · **Status**: Completed · **Archived**: 2026-06-11

### Summary

Adds PRSG-009's post-implementation split-PR emission path. The implementation
consumes PRSG-008 layer-plan output, emits ordered Style B slice PRs with
explicit `gh pr create --base --head --body-file` arguments, records schema v2
PRS rows, writes durable resume state, isolates failed slice verification, and
provides dry-run-first restack recovery.

### User Stories

- **US1 - Emit ordered slice PRs.** A verified implementation can produce one
  branch and one PR per PRSG-008 layer in dependency order.
- **US2 - Persist PR table and resume evidence.** After each successful slice,
  `.process/prs.json`, the Spec MOC PRS table, workflow evidence, and
  `autopilot-state.json` contain enough data to resume without duplicate PRs.
- **US3 - Define stack topology, scoped CI, and restack.** Slice PR bodies carry
  scoped verification and full-regression evidence, while `restack.sh` plans or
  applies ordered retarget/rebase recovery after lower-stack squash merges.

### Functional Requirements

- The emitter consumes the PRSG-008 layer-plan envelope as the sole slice source
  and adds no new routing or slicing heuristics.
- Slice branches use deterministic `<feature-branch>/<NN>-<slice-id>` names and
  explicit base/head PR creation.
- Scoped verification must pass before a slice PR opens; failed later slices do
  not rewind or relabel earlier opened PRs.
- State persistence uses same-directory temp files and validated JSON candidates
  for `autopilot-state.json`, PRS v2 manifests, and slice packet outputs.
- PRS schema v2 renders bounded reviewer-navigation rows with order, slice, PR,
  status, branch, base, SHA, scope, and verification fields.
- `gh-stack` remains optional; `restack.sh` is the deterministic fallback and is
  dry-run by default.

### Success Criteria

- Layer 4 fixtures validate three-slice emission, single-slice emission, scoped
  verification failure blocking, no-scoped-test evidence, resume reconciliation,
  post-PR persistence failure handling, closed-PR blocking, and restack exit
  semantics.
- PR #145 CI passed PR Checks, CodeQL, Release, `test(speckit-pro)`,
  `validate-plugins`, `validate-pr-title`, and `detect`.
- Post-cleanup `bash tests/speckit-pro/run-all.sh` passed `2300/2300`.

### Cleanup Note

The active spec folder was removed from `specs/**` cleanup on 2026-06-11 after
PR #145 merged and the PRSG-009 contract schemas were preserved under
`speckit-pro/skills/speckit-autopilot/contracts/`.
Recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-11-prsg-009-post-merge-hygiene.md`.

---
