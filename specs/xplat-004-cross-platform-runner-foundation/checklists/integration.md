# Integration Checklist: Cross-Platform Runner Foundation

**Purpose**: Validate integration requirements for the XPLAT-004 runner foundation before tasks and implementation.
**Created**: 2026-06-30
**Feature**: [spec.md](../spec.md)

**Note**: This checklist is generated from the workflow's `$speckit-checklist integration` prompt. It tests requirement quality, not implementation behavior.

## Module Invocation

- [x] CHK001 Is the source package path and supported module-style invocation defined unambiguously for XPLAT-004? [Clarity, Spec §Clarifications Session 1, Plan §Summary]
- [x] CHK002 Are helper-specific CLI arguments excluded so JSON stdin remains the invocation contract? [Consistency, Spec §Clarifications Session 1]
- [x] CHK003 Is the runner test invocation required to use argv form with `shell=False` rather than a new shell launcher? [Completeness, Spec §Clarifications Session 1, Plan §Slice 1]
- [x] CHK004 Does the spec or plan state that XPLAT-005/XPLAT-006 helper ports must extend the same package, module entrypoint, and dispatch contract instead of reopening package or invocation decisions? [Resolved: Spec FR-017, Plan §Summary/Downstream Handoff Rules]

## JSON Envelope Compatibility

- [x] CHK005 Is the request envelope shape versioned and aligned to the XPLAT-002 stdin model for schema version, helper ID, operation, mode, and inputs? [Consistency, Spec §Clarifications Session 1, Contract §runner-envelope]
- [x] CHK006 Are invalid JSON, invalid envelope, unsupported schema version, and missing-field fixture categories distinct? [Completeness, Spec §Clarifications Session 2]
- [x] CHK007 Does the spec or plan require the XPLAT-002 wire-status and exit-code vocabulary to remain the implementation contract, avoiding status aliases such as `success`, `prerequisite_missing`, or `internal_error`? [Resolved: Spec FR-002, Plan §Technical Context/Slice 1]
- [x] CHK008 Are stdout and stderr separation requirements specified as one JSON stdout response plus line-delimited JSON stderr diagnostics? [Clarity, Spec §Clarifications Session 2, Plan §Technical Context]

## Plugin Root And Metadata

- [x] CHK009 Are source-checkout runner package, manifest, and checksum file locations defined under `speckit-pro/speckit_pro_runner/`? [Completeness, Spec §Clarifications Session 3]
- [x] CHK010 Does the spec or plan define concrete plugin-root detection anchors and the discovery origin for source checkout and future installed payload roots? [Resolved: Spec FR-015, Plan §Project Structure/Slice 1]
- [x] CHK011 Are metadata path values required to stay plugin-root-relative so they remain payload-relative after XPLAT-007 generated payload propagation? [Resolved: Spec FR-016, Plan §Slice 2]
- [x] CHK012 Is `source_vs_installed_context` required so XPLAT-004 source-checkout proof cannot be mistaken for installed-cache proof? [Clarity, Spec §Clarifications Session 3]

## Scope Boundaries

- [x] CHK013 Are real production helper ports explicitly deferred to XPLAT-005 and XPLAT-006? [Completeness, Spec §FR-011, Plan §Deferred Work]
- [x] CHK014 Is generated payload propagation and active Claude/Codex cutover explicitly deferred to XPLAT-007? [Completeness, Spec §FR-012/FR-013, Plan §Deferred Work]
- [x] CHK015 Are public native-platform support claims excluded from XPLAT-004? [Consistency, Spec §FR-013]
- [x] CHK016 Is the accepted two-slice plan recorded without requiring child specs or extra branches? [Traceability, Spec §FR-014, Plan §Implementation Strategy]

## Downstream Helper-Port Readiness

- [x] CHK017 Are the shared primitives named for later helper ports: envelope parsing, diagnostics, typed paths, subprocess records, prerequisite discovery, and preflight? [Completeness, Plan §Structure Decision]
- [x] CHK018 Are contract fixtures required before real helper ports so downstream implementers have failing examples? [Completeness, Spec §User Story 2, Plan §Slice 2]
- [x] CHK019 Are XPLAT-005/XPLAT-006 allowed to consume runner primitives without relying on production helper behavior being ported in XPLAT-004? [Clarity, Spec §Assumptions]
- [x] CHK020 Does the plan define a stable downstream handoff rule for future helper IDs, operations, modes, and adapter records while keeping those records out of XPLAT-004 implementation scope? [Resolved: Spec FR-018, Plan §Downstream Handoff Rules]

## Integration Checklist Result

- Items: 20
- Initial gaps: 5
- Remediated gaps: 5
- Current gaps: 0

## Re-run Verification

- Re-ran the same integration checklist focus after remediation.
- Result: 20/20 items satisfied; no current gap markers remain.
