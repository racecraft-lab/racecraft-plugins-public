# Security Checklist: Python Tooling and Release-Gate Migration

**Purpose**: Validate security-quality requirements for Python-only active gates, safe subprocess usage, bounded writes, no-shell guardrails, fixture-bound install verification, and XPLAT-008 cutover boundaries.
**Created**: 2026-07-04
**Feature**: [spec.md](../spec.md)
**Domain**: security
**Depth**: Standard release-gate security requirements quality review
**Audience**: Reviewer before XPLAT-007 task generation and implementation
**Source artifacts**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`, `docs/ai/specs/.process/XPLAT-007-workflow.md`

**Note**: This checklist is generated from the workflow's `$speckit-checklist security` prompt. It tests requirement quality, not implementation behavior.

## No-Shell Command Safety

- [x] CHK001 Does the spec explicitly prohibit Bash, `.sh` active entrypoints, `jq`, Git Bash, WSL, PowerShell helper dependencies, shell interpolation, and shell-only parsing in promoted active paths? [Security, Completeness, Spec Forbidden Pattern Rule, Spec FR-009]
- [x] CHK002 Does the plan explicitly include `shell=True`, `os.system`, and command-string subprocess calls in the active-path guard's blocking categories? [Security, Coverage, Plan Constraints, Plan Slice 3]
- [x] CHK003 Are promoted operations required to use Python runner entrypoints rather than thin Bash wrappers or shell command strings? [Security, Consistency, Spec Runner Operation Rule, Spec Bash Retirement Rule, Plan Command Surface]
- [x] CHK004 Are subprocesses constrained to argv-list execution only when unavoidable, with shell parsing replaced by Python standard-library behavior? [Security, Clarity, Data Model Command Operation, Spec Forbidden Pattern Rule]
- [x] CHK005 Are missing prerequisites required to produce deterministic diagnostics instead of falling back to Bash, shell snippets, or platform-specific helper scripts? [Security, Reliability, Spec Assumptions, Spec FR-015, Plan Performance Goals]

## Bounded Path And Write Safety

- [x] CHK006 Are payload operations limited to fixture or temporary output roots and required to keep `release_payload_cutover=false`? [Security, Completeness, Spec Test Payload Evidence Rule, Data Model Payload Evidence]
- [x] CHK007 Are local refresh and install-verification operations limited to fixture roots, fake-home paths, stubbed CLIs, and command plans instead of real `HOME` or installed-cache mutation? [Security, Safety, Spec Local Refresh And Install Verification Rule, Data Model Install Verification Result]
- [x] CHK008 Does the plan define `read_only`, `dry_run`, and narrowly scoped `apply` modes, with `apply` limited to source-checkout test evidence, temporary fixtures, or scoped verification metadata? [Security, Clarity, Spec Mutable Command Mode Rule, Plan Slice 2]
- [x] CHK009 Are Windows-style paths, backslashes, spaces, traversal rejection, fake-home roots, and line-ending normalization required in source-checkout fixtures? [Security, Coverage, Spec Edge Cases, Spec Platform Proof Rule, Plan Verification Plan]
- [x] CHK010 Do command-operation requirements include deterministic artifact output paths and file fingerprints where migrated gates produce files? [Security, Measurability, Data Model Command Operation, Data Model Payload Evidence, Plan Promotion And Retirement Model]

## Active-Path Guard Scope

- [x] CHK011 Does the guard block only active repo-local build, test, eval, payload, install-verification, repository-helper, and release-readiness paths? [Security, Clarity, Spec Guard Scope Rule, Research Decision 4]
- [x] CHK012 Does the guard classify archive/provenance text, consumer Spec Kit helpers, temporary parity evidence, generated payload mirrors, docs out of scope, and XPLAT-008 cutover surfaces as nonblocking unless reachable from an active gate? [Security, Consistency, Spec Nonblocking Classification Rule, Data Model Active-Path Guard Finding]
- [x] CHK013 Does the guard output require path, line, category, pattern, reason, active role, classification, remediation, blocking counts, and classified nonblocking counts? [Security, Measurability, Spec Guard Output Contract, Data Model Active-Path Guard Finding]
- [x] CHK014 Does promotion require the active-path guard to prove retired Bash references are no longer active while preserving inactive historical or parity evidence when needed? [Security, Consistency, Spec Promotion Record Rule, Spec Bash Retirement Rule, Data Model Promotion Record]
- [x] CHK015 Are CI workflow shell snippets allowed only as direct dispatch glue to Python gates or non-plugin docs tooling, with no plugin validation, packaging, install, release, loop, `jq`, or parsing logic? [Security, Coverage, Spec CI Dispatch Allowlist Rule, Research Decision 6]

## Release And Install Boundary Safety

- [x] CHK016 Do release-readiness requirements fail closed when promotion records, guard status, test payload evidence, install verification, or marketplace/version evidence are stale or inconsistent? [Security, Reliability, Spec FR-007, Data Model Release-Readiness Result]
- [x] CHK017 Are marketplace/version sync, changed-plugin detection, suite aggregation, PR-title validation, workflow-contract validation, release-PR payload-sync parsing, and post-release drift checks assigned to runner-backed operations? [Security, Completeness, Spec Release-Readiness Migration Rule, Plan Command Surface]
- [x] CHK018 Does install verification explicitly avoid installed-cache native UAT while checking expected files, bundled-agent inventory, checksums, safe repairs, and unsafe manual remediations in fixture/fake-home roots? [Security, Clarity, Spec FR-016, Data Model Install Verification Result]
- [x] CHK019 Are generated release payload selection, publishing, and cutover excluded from XPLAT-007 even when test payload evidence is rebuilt? [Security, Scope, Spec FR-008, Spec SC-005, Research Decision 5]
- [x] CHK020 Are release helper operations required to preserve one JSON stdout response, line-delimited diagnostics, status-mapped exits, and deterministic missing-prerequisite handling for reviewability? [Security, Measurability, Spec Runner Stream And Exit Contract, Plan Command Surface]

## Public Claim And Cutover Controls

- [x] CHK021 Does the spec defer active Claude/Codex invocation cutover, generated release payloads, public docs, release notes, native installed-plugin UAT, update, autoheal, and public release-readiness claims to XPLAT-008? [Security, Scope, Spec Edge Cases, Spec XPLAT-008 Handoff Item]
- [x] CHK022 Does the maintainer documentation boundary limit documentation edits to active repo-local run instructions required for XPLAT-007 gates? [Security, Consistency, Spec Maintainer Documentation Boundary Rule, Spec FR-012]
- [x] CHK023 Does platform proof stay limited to source-checkout fixtures and local macOS smoke without native installed-plugin or public platform claims? [Security, Clarity, Spec Platform Proof Rule, Spec SC-006]
- [x] CHK024 Does the release-readiness model require XPLAT-008 handoff items for accidental cutover or public-claim surfaces found during implementation? [Security, Coverage, Data Model XPLAT-008 Handoff Item, Spec PR Review Packet Requirements]
- [x] CHK025 Does the PR review packet require no-shell guard evidence, parity or promotion evidence, known gaps, rollback notes, and explicit XPLAT-008 handoff items? [Security, Reviewability, Spec FR-018, Plan Verification Plan]

## Security Checklist Result

- Items: 25
- Initial gaps: 0
- Remediated gaps: 0
- Current gaps: 0
- Consensus: skipped because security requirements are already covered by the current spec, plan, contracts, workflow prompt, and prior XPLAT source evidence.
