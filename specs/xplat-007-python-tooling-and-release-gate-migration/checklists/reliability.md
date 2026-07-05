# Reliability Checklist: Python Tooling and Release-Gate Migration

**Purpose**: Validate reliability requirements for deterministic Python gate promotion, Bash-reference retirement, command output contracts, fixture evidence, artifact paths, and source-checkout platform stability before XPLAT-007 task generation.
**Created**: 2026-07-04
**Feature**: [spec.md](../spec.md)
**Domain**: reliability
**Depth**: Standard release-gate reliability requirements quality review
**Audience**: Reviewer before XPLAT-007 task generation and implementation
**Source artifacts**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`, `docs/ai/specs/.process/XPLAT-007-workflow.md`

**Note**: This checklist is generated from the workflow's `$speckit-checklist reliability` prompt. It tests requirement quality, not implementation behavior.

## Deterministic Gate Execution

- [x] CHK001 Does the spec require migrated active gates to preserve current pass/fail meaning before Python authority changes? [Measurability, Spec US1, Spec FR-003, Spec SC-002]
- [x] CHK002 Does the plan require active repo-local gates to use `python -m speckit_pro_runner` operations wherever practical, with standalone Python limited and justified? [Clarity, Spec FR-004, Plan Command Surface, Research Decision 2]
- [x] CHK003 Are stdout, stderr, and exit semantics defined as one JSON response, line-delimited diagnostics, and status-mapped exits `0` through `5`? [Measurability, Spec Runner Stream And Exit Contract, Plan Command Surface, Contract `migrated-gate-result.schema.json`]
- [x] CHK004 Are missing prerequisites required to fail deterministically rather than falling back to Bash or shell-specific behavior? [Reliability, Spec Assumptions, Spec FR-015, Plan Command Surface]
- [x] CHK005 Are promoted commands required to expose stable diagnostic or expected-failure categories suitable for release-readiness review? [Measurability, Data Model Command Operation, Contract `migrated-gate-result.schema.json`, Spec FR-015]

## Golden Fixtures And Bash-Reference Comparison

- [x] CHK006 Does each migrated gate require golden request fixtures before it can become Python-authoritative? [Completeness, Spec FR-005, Plan Slice 1 Promotion Bar, Research Decision 3]
- [x] CHK007 Does source-checkout Bash-reference comparison remain required while the legacy gate exists? [Completeness, Spec US1 Acceptance Scenario 2, Plan Promotion Bar, Research Decision 3]
- [x] CHK008 Are exit codes and stderr compared exactly unless the fixture or promotion record declares a field-level normalization? [Clarity, Data Model Parity Comparison, Plan Promotion Bar]
- [x] CHK009 Are counts, booleans, statuses, diagnostic codes, and guard blocking decisions protected from normalization? [Reliability, Data Model Parity Comparison, Plan Promotion Bar]
- [x] CHK010 Does the plan allow semantic JSON stdout comparison only when old stdout is structured and the comparison mode is declared? [Clarity, Spec Runner Stream And Exit Contract, Data Model Parity Comparison]

## Promotion Records And Bash Retirement

- [x] CHK011 Are promotion records required to name the prior Bash gate, Python operation, request fixture, fixture ids, Bash reference ids, failure classes, and comparison mode? [Completeness, Spec Promotion Record Rule, Data Model Promotion Record, Contract `promotion-record.schema.json`]
- [x] CHK012 Do promotion records capture exit-code, stream, artifact, active-path guard, rollback, and Bash-reference retirement results? [Measurability, Data Model Promotion Record, Contract `promotion-record.schema.json`, Plan Promotion And Retirement Model]
- [x] CHK013 Is Python authority blocked until the active-path guard proves the prior Bash reference is no longer active? [Consistency, Spec Bash Retirement Rule, Data Model Migrated Gate, Plan Promotion And Retirement Model]
- [x] CHK014 Can retired Bash references remain as inactive historical or parity evidence without losing review provenance? [Clarity, Spec Promotion Record Rule, Data Model Promotion Record, Research Decision 3]
- [x] CHK015 Are thin Bash wrappers explicitly rejected as active transition entrypoints after migration? [Consistency, Spec FR-017, Spec Bash Retirement Rule, Research Decision 2]

## Artifact Paths And Test Payload Evidence

- [x] CHK016 Do command-operation requirements include deterministic artifact output paths for fixture or evidence files? [Completeness, Data Model Command Operation, Contract `migrated-gate-result.schema.json`, Spec FR-015]
- [x] CHK017 Are artifact hashes, byte counts, or diff results required where migrated gates produce files? [Measurability, Data Model Parity Comparison, Data Model Payload Evidence, Contracts `payload-evidence.schema.json` and `promotion-record.schema.json`]
- [x] CHK018 Is test payload rebuild evidence limited to Claude/Codex test surfaces with fixture or temporary output roots? [Clarity, Spec Test Payload Evidence Rule, Data Model Payload Evidence, Quickstart Section 4]
- [x] CHK019 Does payload evidence require file fingerprints and `release_payload_cutover=false`? [Measurability, Data Model Payload Evidence, Contract `payload-evidence.schema.json`, Spec SC-005]
- [x] CHK020 Does release-readiness fail closed when payload evidence, promotion records, install verification, active-path guard output, or marketplace/version evidence is stale or inconsistent? [Reliability, Spec FR-007, Data Model Release-Readiness Result, Contract `release-readiness-result.schema.json`]

## Platform And Path Stability

- [x] CHK021 Are Windows-style paths, backslashes, spaces, traversal rejection, fake-home install roots, and line-ending normalization included in source-checkout fixtures? [Coverage, Spec Edge Cases, Spec Platform Proof Rule, Research Decision 7]
- [x] CHK022 Does XPLAT-007 require local macOS source-checkout smoke while avoiding native installed-plugin UAT claims? [Clarity, Spec Platform Proof Rule, Spec SC-006, Quickstart Section 1]
- [x] CHK023 Are missing Python or `specify` prerequisites required to report deterministic prerequisite diagnostics? [Reliability, Spec Assumptions, Spec FR-015, Plan Verification Plan]
- [x] CHK024 Are stale generated files represented as release-readiness or guard failures rather than accepted silently? [Reliability, Spec Edge Cases, Data Model Release-Readiness Result, Plan Verification Plan]
- [x] CHK025 Are real `HOME` and installed plugin cache mutations refused during install verification? [Safety, Spec Local Refresh And Install Verification Rule, Data Model Install Verification Result, Quickstart Section 5]

## CI And Local Environment Differences

- [x] CHK026 Does the spec distinguish CI dispatch glue from plugin validation, packaging, install, release, loop, `jq`, or parsing logic? [Clarity, Spec CI Dispatch Allowlist Rule, Research Decision 6]
- [x] CHK027 Are plugin `pr-checks.yml` and `release.yml` Bash or `jq` validation paths blocking until migrated to runner operations? [Reliability, Spec CI Dispatch Allowlist Rule, Research Decision 6, Plan Constraints]
- [x] CHK028 Does the active-path guard output include blocking counts, classified nonblocking counts, path/category/reason/remediation fields, and deterministic exit behavior? [Measurability, Spec Guard Output Contract, Contract `active-path-guard-result.schema.json`, Quickstart Section 3]
- [x] CHK029 Does final verification require Python Layer 1, Layer 4, and default deterministic suite runs after promotion? [Completeness, Plan Verification Plan, Spec US1, Workflow G7]
- [x] CHK030 Does the PR packet require per-gate promotion state, parity evidence, guard evidence, rollback notes, known gaps, and XPLAT-008 handoff items? [Reviewability, Spec FR-018, Spec PR Review Packet Requirements, Data Model XPLAT-008 Handoff Item]

## Reliability Checklist Result

- Items: 30
- Initial gaps: 0
- Remediated gaps: 0
- Current gaps: 0
- Consensus: skipped because reliability requirements are already covered by the current spec, plan, contracts, workflow prompt, and prior XPLAT source evidence.
