# Release-Readiness Checklist: Python Tooling and Release-Gate Migration

**Purpose**: Validate release-readiness requirements for Python-authoritative release checks, marketplace/version sync, payload evidence, install verification, active-path no-shell guardrails, and the XPLAT-008 handoff boundary before XPLAT-007 task generation.
**Created**: 2026-07-04
**Feature**: [spec.md](../spec.md)
**Domain**: release-readiness
**Depth**: Standard release-gate requirements quality review
**Audience**: Reviewer before XPLAT-007 task generation and implementation
**Source artifacts**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`, `docs/ai/specs/.process/XPLAT-007-workflow.md`

**Note**: This checklist is generated from the workflow's `$speckit-checklist release-readiness` prompt. It tests requirement quality, not implementation behavior.

## Release Gate Authority And Fail-Closed Scope

- [x] CHK001 Are active release checks required to use Python 3.11+ standard-library entrypoints before they become authoritative? [Completeness, Spec FR-002, Spec FR-007, Plan Summary]
- [x] CHK002 Are release-readiness operations assigned to `python -m speckit_pro_runner` wherever practical, with standalone Python excluded from the release contract unless justified? [Clarity, Spec Runner Operation Rule, Plan Command Surface, Research Decision 2]
- [x] CHK003 Does the release-readiness result require zero blocking checks, zero active-path guard blockers, and promotion records for promoted active gates before `status=pass`? [Measurability, Data Model Release-Readiness Result, Contract `release-readiness-result.schema.json`]
- [x] CHK004 Are stale or inconsistent promotion records, guard output, payload evidence, install verification, and marketplace/version evidence defined as release blockers? [Coverage, Spec Release-Readiness Migration Rule, Data Model Release-Readiness Result, Quickstart Section 5]
- [x] CHK005 Are changed-plugin detection, suite dispatch/result aggregation, PR-title validation, workflow-contract validation, release-PR payload-sync parsing, and post-release drift checks included in the release-readiness scope? [Completeness, Spec Release-Readiness Migration Rule, Plan Command Surface, Workflow Release-Readiness Prompt]

## Marketplace And Version Synchronization

- [x] CHK006 Does the spec require marketplace/version sync checks to run without Bash or `jq`? [Completeness, Spec US2, Spec FR-007, Spec CI Workflow Inventory Rule]
- [x] CHK007 Are plugin version edits constrained by the constitution and plan so release-readiness checks validate sync without manually changing versions in XPLAT-007? [Consistency, Constitution III, Plan Constitution Check, Spec Assumptions]
- [x] CHK008 Are marketplace-source validation and version consistency required for local refresh and install-verification fixtures? [Coverage, Spec Local Refresh And Install Verification Rule, Quickstart Section 5]
- [x] CHK009 Do release-readiness checks distinguish release-gate metadata drift from generated release payload selection or publication? [Clarity, Spec FR-008, Research Decision 5, Data Model Payload Evidence]
- [x] CHK010 Are post-release drift checks required to be runner-backed release checks rather than shell or `jq` parsing in workflows? [Consistency, Spec Release-Readiness Migration Rule, Research Decision 6, Plan Constraints]

## Payload Evidence Boundary

- [x] CHK011 Is test payload evidence limited to isolated Claude/Codex test surfaces under fixture or temporary output roots? [Clarity, Spec Test Payload Evidence Rule, Data Model Payload Evidence, Quickstart Section 4]
- [x] CHK012 Does payload evidence require fingerprints, file-tree proof, byte counts, or artifact diff/hash evidence where files are produced? [Measurability, Data Model Payload Evidence, Plan Promotion And Retirement Model, Contract `payload-evidence.schema.json`]
- [x] CHK013 Is `release_payload_cutover=false` required by both the data model and contract schema? [Measurability, Data Model Payload Evidence, Contract `payload-evidence.schema.json`, Spec SC-005]
- [x] CHK014 Are generated release payload selection, publication, active payload selection, public docs, and release-note changes excluded from XPLAT-007 even when test payload evidence is rebuilt? [Consistency, Spec FR-008, Spec Edge Cases, Quickstart XPLAT-008 Exclusions]
- [x] CHK015 Does release-readiness require payload evidence to block if stale or inconsistent without treating test payload rebuilds as public release payload cutover? [Release Boundary, Spec US2 Acceptance Scenario 1, Data Model Release-Readiness Result, Research Decision 5]

## Install Verification And Fake-Home Proof

- [x] CHK016 Are install-verification checks required to use fixture roots, fake-home paths, stubbed CLIs, and command plans instead of real `HOME` or installed plugin caches? [Safety, Spec Local Refresh And Install Verification Rule, Data Model Install Verification Result, Quickstart Section 5]
- [x] CHK017 Does the install-verification result require bundled-agent inventory, expected files, missing files, checksum mismatches, safe repairs, unsafe manual remediations, and `native_uat_claimed=false`? [Completeness, Data Model Install Verification Result, Spec FR-016]
- [x] CHK018 Are safe repairs limited to fixture or fake-home roots, with real installed-cache repair, update, and autoheal deferred? [Clarity, Data Model Install Verification Result, Spec Edge Cases, Quickstart XPLAT-008 Exclusions]
- [x] CHK019 Are source-checkout platform proof requirements limited to local macOS smoke plus Windows-style path fixtures without native installed-plugin UAT claims? [Consistency, Spec Platform Proof Rule, Spec SC-006, Research Decision 7]

## Active-Path No-Shell Release Blockers

- [x] CHK020 Does the active-path guard fail release-readiness when active gate, helper, workflow, payload, install-verification, or release paths still require Bash, `.sh`, `jq`, shell interpolation, or shell-only parsing? [Coverage, Spec FR-009, Spec Forbidden Pattern Rule, Plan Slice 3]
- [x] CHK021 Are `shell=True`, `os.system`, command-string subprocess calls, Git Bash, WSL, and PowerShell helper dependencies included as blocking active-path guard categories? [Security, Coverage, Spec Forbidden Pattern Rule, Data Model Active-Path Guard Finding]
- [x] CHK022 Are CI workflow shell snippets allowlisted only as direct dispatch glue to Python gates or non-plugin docs tooling with no plugin validation, packaging, install, release, loop, `jq`, or parsing logic? [Consistency, Spec CI Dispatch Allowlist Rule, Research Decision 6]
- [x] CHK023 Does the guard classify archive/provenance, consumer Spec Kit helpers, temporary parity evidence, generated payload mirrors, docs out of scope, and XPLAT-008 cutover surfaces as nonblocking unless reachable from an active gate? [Clarity, Spec Nonblocking Classification Rule, Data Model Active-Path Guard Finding]
- [x] CHK024 Is Python authority blocked until the active-path guard proves the prior Bash reference is no longer active, while preserving inactive historical or parity evidence where needed? [Release Blocker, Spec Bash Retirement Rule, Data Model Promotion Record]

## XPLAT-008 Handoff And Public Release Boundary

- [x] CHK025 Does the spec require explicit XPLAT-008 handoff items for active Claude/Codex invocation cutover, generated release payloads, public docs, release notes, installed-cache UAT, native platform UAT, update, autoheal, and public release readiness? [Completeness, Spec XPLAT-008 Handoff Item, Data Model XPLAT-008 Handoff Item]
- [x] CHK026 Does the release-readiness output include XPLAT-008 handoff items relevant to final public release blocking without claiming they are complete in XPLAT-007? [Clarity, Data Model Release-Readiness Result, Contract `release-readiness-result.schema.json`]
- [x] CHK027 Are active maintainer-facing documentation updates limited to repo-local run instructions needed for XPLAT-007 gates, excluding public install/runtime docs and release notes? [Scope, Spec Maintainer Documentation Boundary Rule, Spec FR-012]
- [x] CHK028 Does the PR review packet require per-gate promotion state, parity evidence, no-shell guard evidence, test payload evidence, known gaps, rollback notes, and explicit XPLAT-008 handoff items? [Reviewability, Spec FR-018, Spec PR Review Packet Requirements, Workflow G7]

## Release-Readiness Checklist Result

- Items: 28
- Initial gaps: 0
- Remediated gaps: 0
- Current gaps: 0
- Consensus: skipped because release-readiness requirements are already covered by the current spec, plan, contracts, workflow prompt, quickstart, and project constitution.
