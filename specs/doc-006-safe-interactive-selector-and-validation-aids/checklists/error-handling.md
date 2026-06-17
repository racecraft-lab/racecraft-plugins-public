# Error Handling Checklist: Safe Interactive Selector and Validation Aids

**Purpose**: Validate DOC-006 error-handling requirement quality before task generation
**Created**: 2026-06-16
**Feature**: [spec.md](../spec.md)
**Domain prompt**: `/speckit-checklist error-handling`

Focus areas:

- Unsupported or ambiguous selector states.
- Manifest/version mismatch explanations.
- Safe handoffs to troubleshooting/update/release docs without claiming a local diagnostic was run.
- Preventing browser-side shell execution, config writes, or local file inspection.

## Selector State Errors

- [x] EH001 [Spec US1 AC-1.1, FR-002, FR-003, Edge Cases] Are no-selection and single-scope selector states specified clearly enough to avoid implying unsupported install scopes? [Coverage]
- [x] EH002 [Resolved: Spec Edge Cases, FR-003, Clarifications: Unsupported and ambiguous selector states; Plan Implementation Boundaries; Quickstart Focused Validation] Are requirements defined for unsupported, unavailable, or ambiguous platform/scope selector combinations, including the user-visible state and safe fallback guidance? [Coverage]
- [x] EH003 [Spec FR-005, FR-006, Clarifications: Platform command boundaries] Are cross-platform command-surface errors prevented by requirements that separate Claude Code and Codex command records? [Consistency]

## Manifest And Version Mismatch States

- [x] EH004 [Spec FR-009, FR-010, SC-003] Are manifest/version mismatch requirements specific about compared values, pass or mismatch state, and the expected consistency rule? [Completeness]
- [x] EH005 [Spec FR-010, Clarifications: Checker comparison rules] Are intentional platform packaging differences required to be informational rather than false mismatch errors? [Clarity]
- [x] EH006 [Spec Edge Cases, FR-016, Clarifications: Mismatch and unavailable handoffs] Are unavailable metadata states required to explain unavailable values and route to lightweight handoffs? [Coverage]

## Safe Handoffs

- [x] EH007 [Spec FR-016, Clarifications: Mismatch and unavailable handoffs] Are mismatch, unavailable, and caution handoffs bounded to lightweight orientation rather than full troubleshooting, update, rollback, cache diagnosis, or repair procedures? [Consistency]
- [x] EH008 [Spec Clarifications: Mismatch and unavailable handoffs, Data Model: TroubleshootingHandoff] Are handoff audiences and scopes specified so installer, maintainer, and evaluator paths remain distinct? [Completeness]
- [x] EH009 [Spec FR-011, FR-016] Are handoff requirements clear that the page does not claim to inspect local user configuration, pasted JSON, installed cache files, or user machine state? [Clarity]

## Browser Safety Boundaries

- [x] EH010 [Spec FR-015, Edge Cases] Are browser-side shell command execution, local file reads, config writes, plugin installs, and local workflow invocation explicitly prohibited? [Coverage]
- [x] EH011 [Spec Clarifications: Copy affordance boundary] Are copy affordances specified as optional progressive enhancement with visible raw commands and visible clipboard failure/status text? [Consistency]
- [x] EH012 [Data Model: CommandGuidance, Plan Implementation Boundaries] Are command records described as visible guidance rather than executable browser behavior? [Clarity]

## Validation Coverage

- [x] EH013 [Spec FR-017, SC-006] Does focused validation require command-surface leakage checks and no pasted-JSON/local-diagnostic UI checks? [Coverage]
- [x] EH014 [Spec FR-017, Quickstart Focused Validation] Does focused validation require pass, mismatch, and unavailable checker states? [Coverage]
- [x] EH015 [Quickstart Manual Review Checklist] Are manual review expectations present for visible guidance-only commands and no local command or local file behavior? [Traceability]

## Notes

- Initial error-handling pass found one requirements-quality gap around explicit unsupported, unavailable, or ambiguous selector combinations. The existing spec covers no selection, single-scope paths, cross-platform command leakage, repository checker mismatch/unavailable states, safe handoffs, and browser safety boundaries.
- Remediation added explicit unsupported/ambiguous selector-state requirements, implementation boundaries, and focused validation coverage without expanding into local diagnostics, config repair, or DOC-008 troubleshooting depth.

## Verification Pass

- [x] EH016 [Spec Clarifications: Unsupported and ambiguous selector states] Re-run confirms unsupported, unavailable, and ambiguous platform/scope combinations require a text state and supported static guidance. [Coverage]
- [x] EH017 [Plan Implementation Boundaries, Quickstart Focused Validation] Re-run confirms focused validation must cover unsupported or ambiguous selector-state handling without local diagnostics or repair claims. [Traceability]
