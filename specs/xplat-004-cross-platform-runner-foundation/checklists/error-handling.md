# Error-Handling Checklist: Cross-Platform Runner Foundation

**Purpose**: Validate error-handling requirements for the XPLAT-004 runner foundation before tasks and implementation.
**Created**: 2026-06-30
**Feature**: [spec.md](../spec.md)

**Note**: This checklist is generated from the workflow's `$speckit-checklist error-handling` prompt. It tests requirement quality, not implementation behavior.

## Envelope Validation

- [x] CHK001 Are malformed JSON, invalid envelope, unsupported schema version, and missing-field cases defined as distinct validation categories? [Completeness, Spec §Clarifications Session 2]
- [x] CHK002 Does the spec or data model name the stable diagnostic codes for each envelope validation category instead of only saying "corresponding" or "stable" codes? [Resolved: Spec §Clarifications Session 2, Data Model §Diagnostic Code Inventory]
- [x] CHK003 Are envelope validation failures mapped to `status: "input_error"`, process `exit_code: 2`, and `legacy_exit_code: null`? [Consistency, Spec §Clarifications Session 2, Data Model §Runner Request Envelope]
- [x] CHK004 Does the request contract require all dispatch fields needed before execution: `schema_version`, `helper_id`, `operation`, `mode`, and `inputs`? [Completeness, Contract §runner-envelope]

## Prerequisite Fail-Closed Behavior

- [x] CHK005 Are Python-too-old and missing-Python discovery cases given explicit diagnostic codes and status/exit-code/remediation requirements, including the host-level boundary where Python cannot launch the runner? [Resolved: Spec §FR-004, Data Model §Prerequisite Record]
- [x] CHK006 Is missing `specify` defined as a fail-closed `missing_prerequisite` case with a stable diagnostic code and structured remediation guidance? [Resolved: Spec §FR-005, Data Model §Prerequisite Record]
- [x] CHK007 Is missing, stale, incomplete, or unchecked runner metadata mapped to a deterministic preflight status, diagnostic code, verification status, and remediation path? [Resolved: Spec §Clarifications Session 3, Data Model §Preflight Report]
- [x] CHK008 Does the preflight report state that `ok` responses must not hide failed prerequisite checks? [Consistency, Data Model §Runner Response Envelope]

## Subprocess Failure Categories

- [x] CHK009 Are subprocess nonzero, timeout, and stderr-only failure fixtures kept distinct while sharing `status: "subprocess_failure"` and exit code `4`? [Completeness, Spec §Clarifications Session 2, Data Model §Subprocess Result]
- [x] CHK010 Does the spec or data model name the exact diagnostic codes for subprocess nonzero, timeout, and stderr-only failure categories? [Resolved: Spec §FR-008, Data Model §Diagnostic Code Inventory]
- [x] CHK011 Is stderr-only failure requirements wording tied to an explicit fixture flag rather than treating any stderr as automatic failure? [Clarity, Spec §Clarifications Session 2, Data Model §Subprocess Result]
- [x] CHK012 Are captured subprocess fields specified for command outcome, exit status, stdout, stderr, timeout state, and duration? [Completeness, Data Model §Subprocess Result]

## Stream Separation And Exit Mapping

- [x] CHK013 Are stdout and stderr responsibilities separated as one JSON stdout response plus line-delimited JSON stderr diagnostics? [Clarity, Plan §Technical Context, Data Model §Runner Response Envelope]
- [x] CHK014 Is the 0-5 exit-code map tied to the XPLAT-002 wire-status vocabulary rather than new natural-language aliases? [Consistency, Spec §FR-002, Data Model §Runner Response Envelope]
- [x] CHK015 Does the response schema make the diagnostic shape strict enough to preserve deterministic stderr JSON records and bounded remediation details? [Resolved: Contract §runner-envelope, Data Model §Diagnostic]
- [x] CHK016 Are `internal_failure` cases separated from input, prerequisite, and subprocess failures so unexpected runner exceptions do not collapse into user-remediable categories? [Consistency, Data Model §Runner Response Envelope]

## Acceptance Criteria And Fixture Coverage

- [x] CHK017 Do success criteria require deterministic non-success diagnostics for missing runtime and missing `specify` cases in covered fixtures? [Acceptance Criteria, Spec §SC-002]
- [x] CHK018 Do contract fixtures cover the required primitive categories: envelope validation, typed paths, subprocess outcomes, diagnostics, runtime-info, and preflight? [Coverage, Spec §SC-003, Data Model §Contract Fixture]
- [x] CHK019 Are fixture expectations required to include diagnostic codes and remediation fields, not just status and exit code? [Resolved: Spec §FR-020, Data Model §Contract Fixture]
- [x] CHK020 Is the scope boundary clear that XPLAT-004 proves fixture behavior without porting real production helpers or switching installed workflows? [Consistency, Spec §FR-011/FR-012, Plan §Deferred Work]

## Error-Handling Checklist Result

- Items: 20
- Initial gaps: 7
- Remediated gaps: 7
- Current gaps: 0

## Re-run Verification

- Re-ran the same error-handling checklist focus after remediation.
- Result: 20/20 items satisfied; no current gap markers remain.
