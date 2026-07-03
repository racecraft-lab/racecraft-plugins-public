# Requirements Checklist: Mutation, Install, and PR-Emission Helper Port

**Purpose**: Validate that the XPLAT-006 specification is complete, testable, scoped to mutation/install/PR-emission helper porting, and ready for Clarify.
**Created**: 2026-07-03
**Feature**: [spec.md](../spec.md)

**Note**: This checklist validates the Specify output before Clarify, Plan, and Tasks add implementation details.

## Content Quality

- [x] CHK001 Specification focuses on user value, helper safety, parity evidence, install completeness, and reviewability instead of implementation tasks.
- [x] CHK002 Problem statement is grounded in XPLAT-004 runner foundation and XPLAT-005 read-only helper registry completion.
- [x] CHK003 Users include maintainers, SpecKit operators, install maintainers, release reviewers, and downstream XPLAT implementers.
- [x] CHK004 User stories are independently testable and prioritized.
- [x] CHK005 Acceptance scenarios use observable Given/When/Then outcomes.
- [x] CHK006 Edge cases cover dirty worktrees, no-op paths, path escapes, atomic write failures, fake CLI failures, stale manifests, partial failures, and unapproved live mutation.
- [x] CHK007 No unresolved clarification markers remain in the specification.

## Requirements Completeness

- [x] CHK008 Functional requirements define explicit dry-run and apply modes for mutation-capable helpers.
- [x] CHK009 Functional requirements require mutation request/result shapes with planned operations, applied operations, touched paths, diagnostics, exit class, rollback notes, and remediation actions.
- [x] CHK010 Functional requirements preserve stdout JSON schemas, stderr diagnostics, human-readable remediation, and documented exit codes.
- [x] CHK011 Functional requirements require atomic write behavior, path-boundary checks, dirty-worktree guards, partial-failure reporting, and rollback/manual-remediation notes.
- [x] CHK012 Functional requirements require fake repositories, fake homes, fake plugin caches, fake `gh`, and fake `specify` by default.
- [x] CHK013 Functional requirements define manifest-driven install completeness for Claude agents, Codex agents, runner files, generated payload files, versions, and checksum metadata.
- [x] CHK014 Functional requirements require safe-repair versus unsafe-manual-remediation classifications for doctor/preflight.
- [x] CHK015 Functional requirements require golden fixtures plus source-checkout Bash-reference comparisons before helper promotion.
- [x] CHK016 Functional requirements lock promoted helper execution to Python 3.11+ standard library only with no new runtime dependency, `jq`, Bash, PowerShell, Node, Go, Rust, or Zig.

## Scope Boundaries

- [x] CHK017 Specification excludes active Claude Code or Codex invocation cutover.
- [x] CHK018 Specification excludes generated payload cutover, install-guidance cutover, public native-platform support claims, repo-local release-gate migration, and native matrix UAT.
- [x] CHK019 Specification avoids re-porting accepted XPLAT-005 read-only helper modes.
- [x] CHK020 Specification keeps live repository, user-local, plugin-cache, network, and GitHub mutation behind explicit approval after dry-run evidence.
- [x] CHK021 Helper and mode matrix seed names the accepted three slices and the deferred or out-of-scope boundaries.

## Reviewability And Verification

- [x] CHK022 Reviewability budget records a warning-accepted one-workflow, three-slice strategy and a split condition if Plan or Tasks proves the scope too large.
- [x] CHK023 PR review packet requirements include review order, traceability, helper promotion evidence, known gaps, and rollback or manual remediation notes.
- [x] CHK024 Key entities identify mutation requests/results, planned/applied operations, install inventory, safe repair records, parity fixtures, Bash comparisons, promotion records, and scope audits.
- [x] CHK025 Success criteria are measurable and tied to helper promotion records, fixture coverage, doctor/preflight detection, source-checkout tests, scope audit, and PR packet traceability.
- [x] CHK026 Clarify-owned details are named as follow-up topics without leaving unresolved requirement markers in the spec.

## Gate Readiness

- [x] CHK027 G1 scope gate is satisfied: XPLAT-006 is limited to mutation, install, doctor/preflight, PR-emission, restack, migration, relocation, and state-writing helper ports.
- [x] CHK028 The spec is ready for Clarify to finalize helper/mode matrix, mutation envelope fields, doctor inventory source, parity bar details, fake/live boundary, and mixed-mode ownership.
