# Reliability Checklist: Cross-Platform Runner Foundation

**Purpose**: Validate reliability requirements for the XPLAT-004 runner foundation before tasks and implementation.
**Created**: 2026-06-30
**Feature**: [spec.md](../spec.md)

**Note**: This checklist is generated from the workflow's `$speckit-checklist reliability` prompt. It tests requirement quality, not implementation behavior.

## Runtime-Info And Preflight Determinism

- [x] CHK001 Does runtime-info/preflight report platform, architecture, Python version, plugin root, prerequisite status, runner identity, and metadata pointers? [Completeness, Spec §FR-003, Data Model §Preflight Report]
- [x] CHK002 Is `source_vs_installed_context: "source_checkout"` required so local proof cannot be mistaken for installed-cache readiness? [Clarity, Spec §Clarifications Session 3, Plan §Target Platform]
- [x] CHK003 Does preflight fail closed when Python 3.11+, `specify`, plugin-root anchors, or required metadata are unavailable? [Reliability, Spec §FR-004/FR-005/FR-010/FR-015]
- [x] CHK004 Are host-level Python launcher failures separated from runner stdout guarantees and recorded as runbook/discovery evidence? [Clarity, Spec §Clarifications Session 2, Data Model §Prerequisite Record]

## Metadata Freshness And Checksum Verification

- [x] CHK005 Are source-checkout manifest and checksum files located with the runner package under `speckit-pro/speckit_pro_runner/`? [Completeness, Spec §Clarifications Session 3]
- [x] CHK006 Are checksum coverage and manifest identities specified for runner-owned source files while excluding manifest/checksum self-coverage? [Reliability, Spec §Clarifications Session 3, Data Model §Runner Metadata Manifest]
- [x] CHK007 Does preflight use explicit metadata verification states and refuse `ok` readiness unless metadata is present, complete, checked, and current? [Reliability, Spec §Clarifications Session 3, Data Model §Preflight Report]
- [x] CHK008 Are metadata stale, incomplete, missing, and skipped-check cases mapped to deterministic diagnostic codes and structured remediation? [Completeness, Data Model §Diagnostic Code Inventory]

## Contract Fixture Repeatability

- [x] CHK009 Do contract fixtures cover path values with spaces, Windows separators, traversal boundaries, and typed-path object validation? [Scenario Coverage, Spec §Clarifications Session 2, Data Model §Typed Path]
- [x] CHK010 Do subprocess fixtures keep nonzero, timeout, and stderr-only failure categories distinct while asserting expected status, exit code, diagnostic code, and remediation? [Scenario Coverage, Spec §FR-008/FR-020]
- [x] CHK011 Do prerequisite fixtures use test-controlled discovery for Python and `specify` outcomes instead of depending on ambient machine state? [Repeatability, Spec §Clarifications Session 2]
- [x] CHK012 Are concrete timeout bounds and stdout/stderr output bounds specified for fixture subprocess records so repeatability does not depend on host speed or unbounded captured output? [Resolved: Spec §FR-021, Plan §Constraints/Slice 2, Data Model §Output Capture/Subprocess Result]

## Output Bounds And Failure Records

- [x] CHK013 Does the response model preserve exactly one JSON stdout response plus line-delimited JSON stderr diagnostics? [Reliability, Plan §Technical Context, Data Model §Runner Response Envelope]
- [x] CHK014 Is the strict Diagnostic shape required for stdout diagnostics and stderr records, including remediation on failures? [Completeness, Spec §FR-019, Data Model §Diagnostic]
- [x] CHK015 Do deterministic failure records include enough bounded fields to prove truncation, timeout, elapsed duration, and captured-output status without leaking unbounded stdout/stderr into responses? [Resolved: Spec §FR-021, Data Model §Output Capture/Subprocess Result, Contract §runner-envelope]
- [x] CHK016 Are non-`ok` fixtures required to assert diagnostic code and remediation object presence, not only status and exit code? [Repeatability, Spec §FR-020, Data Model §Contract Fixture]

## Platform Runbook Proof Boundaries

- [x] CHK017 Is full native Windows/macOS/Linux installed-cache UAT explicitly deferred to XPLAT-007? [Boundary, Spec §Assumptions, Plan §Deferred Work]
- [x] CHK018 Does XPLAT-004 avoid switching active skills, hooks, generated payloads, install behavior, or public docs to the runner? [Boundary, Spec §FR-012/FR-013]
- [x] CHK019 Are Windows/Linux runbook fixtures required to record exact context, launcher command family, expected diagnostic/status, and explicit non-claim language so they cannot be read as installed-cache or public platform readiness? [Resolved: Spec §FR-022/SC-007, Plan §Slice 2, Data Model §Platform Runbook Fixture, Contract §platform-runbook-fixtures]
- [x] CHK020 Does the PR review packet require known gaps and deferred follow-up boundaries so reliability evidence is not silently promoted to release readiness? [Traceability, Spec §PR Review Packet Requirements]

## Reliability Checklist Result

- Items: 20
- Initial gaps: 3
- Remediated gaps: 3
- Current gaps: 0

## Re-run Verification

- Re-ran the same reliability checklist focus after remediation.
- Result: 20/20 items satisfied; no current gap markers remain.
