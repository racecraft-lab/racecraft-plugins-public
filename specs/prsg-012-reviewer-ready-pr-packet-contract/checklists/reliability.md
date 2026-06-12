# Reliability Requirements Checklist: Reviewer-ready PR packet contract

**Purpose**: Validate reliability requirements for deterministic packet validation evidence, workflow remediation events, shared validator reuse, evidence layers, and Claude Code/Codex parity.
**Created**: 2026-06-12
**Domain**: reliability
**Prompt**: `/speckit-checklist reliability` focused on deterministic validation JSON paths under `.process`, workflow event content and remediation quality, shared validator reuse across PR creation paths, Layer 4/3/7/8 evidence expectations, and Claude Code/Codex guidance drift.

## Requirement Completeness

- [x] CHK001 Are deterministic per-packet validation JSON paths specified for passed and failed rendered packets? [Completeness, Spec FR-014, Assumptions]
- [x] CHK002 Are malformed, missing, unreadable, directory-valued, invalid-JSON, and schema-invalid packet inputs specified with deterministic input-error evidence behavior? [Completeness, Spec FR-015A, Data Model Packet Validation Result]
- [x] CHK003 Are single-PR and split-PR creation paths both required to validate rendered packets before any `gh pr create` attempt? [Completeness, Spec FR-004/FR-005, Plan Summary]
- [x] CHK004 Are validation failure and input-error classes specified separately with distinct exit codes, blocked PR behavior, and remediation evidence? [Completeness, Spec FR-013/FR-015B, Data Model Packet Validation Result]
- [x] CHK005 Are split-PR partial-failure requirements specified so earlier successful PR evidence is preserved and resume cannot duplicate already opened PRs? [Completeness, Spec FR-015E, Data Model Packet Resume Evidence]
- [x] CHK006 Is the workflow event requirement complete enough to name the durable workflow sink, append/idempotency behavior, and minimum remediation fields operators need after a block? [Resolved, Spec FR-015F, Data Model Workflow Event, Quickstart Scenarios 3/4/7/8]

## Requirement Clarity

- [x] CHK007 Is deterministic stderr specified with a fixture-comparable format and host-specific content exclusions? [Clarity, Spec FR-015C]
- [x] CHK008 Are validation result fields clear enough to distinguish authoritative machine-readable JSON from reader-facing workflow evidence? [Clarity, Spec FR-014/FR-015]
- [x] CHK009 Are resume requirements clear that stale failed validation records are evidence only and current rendered packet content must be revalidated? [Clarity, Spec FR-015D, Data Model Packet Resume Evidence]
- [x] CHK010 Are PR target fields required and bound unambiguously to `gh pr create --base`, `--head`, `--title`, and `--body-file`? [Clarity, Spec FR-004A, Plan Phase 0]

## Requirement Consistency

- [x] CHK011 Are deterministic validation result paths consistent across spec, plan, data model, quickstart, and contract assumptions? [Consistency, Spec FR-014, Plan Technical Context, Quickstart Scenario 1]
- [x] CHK012 Are single-PR and split-PR packet entities consistent about which fields are shared and which fields are split-only? [Consistency, Spec Key Entities, Data Model PR Packet]
- [x] CHK013 Are host PR template coexistence requirements consistent with protected canonical packet sections and source-marker validation? [Consistency, Spec FR-016C/FR-017, Data Model PR Packet]

## Evidence And Verification Requirements

- [x] CHK014 Are Layer 4, Layer 3, Layer 7, and Layer 8 evidence expectations decomposed into exact artifact and command expectations rather than a generic fixture-update statement? [Resolved, Spec PR Review Packet Requirements/SC-009, Plan Reliability Evidence Plan, Quickstart Extended Evidence Commands]
- [x] CHK015 Are seeded valid, invalid, input-error, protected-edit, and split-partial-failure examples required for deterministic validation coverage? [Completeness, Spec SC-002/SC-003/SC-007/SC-008, Plan Declared File Operations]

## Parity And Drift Control

- [x] CHK016 Are Claude Code and Codex autopilot guidance surfaces explicitly named, with a single-copy boundary for the shared schema and validator to prevent drift? [Resolved, Spec FR-019, Plan Declared File Operations, Plan Reliability Evidence Plan]
- [x] CHK017 Are existing UAT runbook guarantees preserved by requiring both How To UAT and literal `## UAT Runbook` content? [Consistency, Spec FR-009, Constraints]
- [x] CHK018 Are no-new-dependency and reusable-script constraints aligned with project constitution simplicity and script-safety principles? [Consistency, Spec Constraints, Constitution Principles II/VI]

## Notes

- Initial reliability pass found three true requirement issues: workflow event sink/remediation specificity, non-fast evidence layer specificity, and Claude Code/Codex parity surface specificity.
- Remediation pass 1 added durable workflow-event requirements, exact Layer 3/4/7/8 evidence expectations, and explicit Claude Code/Codex parity surfaces with a single shared validator/schema boundary.
- Re-run pass 1 found no remaining reliability requirement issues; marker counter returned `{"type":"gaps","total":0,"spec":0,"plan":0,"checklists":0,"details":[]}`.
