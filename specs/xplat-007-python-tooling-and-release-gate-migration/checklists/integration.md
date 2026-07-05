# Integration Checklist: Python Tooling and Release-Gate Migration

**Purpose**: Validate integration-quality requirements for migrating active repo-local gates, evals, payload builders, install verification, helper tooling, and release-readiness checks onto Python runner operations while preserving prior XPLAT contracts and deferring active Claude/Codex cutover to XPLAT-008.
**Created**: 2026-07-04
**Feature**: [spec.md](../spec.md)
**Domain**: integration
**Depth**: Standard release-gate requirements quality review
**Audience**: Reviewer before XPLAT-007 task generation and implementation
**Source artifacts**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`, `docs/ai/specs/.process/XPLAT-007-workflow.md`

**Note**: This checklist is generated from the workflow's `$speckit-checklist integration` prompt. It tests requirement quality, not implementation behavior.

## Active Gate Inventory And Scope Boundaries

- [x] CHK001 Does the spec require a complete active gate inventory before promotion across `tests/speckit-pro/**`, payload/release helpers, reachable plugin helper scripts, and plugin workflows? [Completeness, Spec FR-001, Plan Scale/Scope, Research Decision 1]
- [x] CHK002 Does the plan distinguish active repo-local gates from fixtures, archive/provenance, generated payload mirrors, consumer Spec Kit helpers, and XPLAT-008 cutover surfaces? [Clarity, Spec Edge Cases, Data Model Active-Path Guard Finding, Research Decision 4]
- [x] CHK003 Are generated release payload selection, installed Claude/Codex invocation cutover, public docs, release notes, update, autoheal, and native installed UAT excluded consistently? [Consistency, Spec Edge Cases, Plan Summary, Quickstart XPLAT-008 Exclusions]
- [x] CHK004 Does the workflow focus explicitly include tests, evals, payload builders, install verification, repo helpers, release-readiness gates, and current Layer 1/4/AI-eval/tool-scoping/integration/parity flows? [Coverage, Workflow Integration Checklist Prompt, Spec User Stories 1-3]
- [x] CHK005 Is maintainer-facing documentation scope limited to active repo-local run instructions needed for XPLAT-007 gates, without broad public support or install-doc changes? [Clarity, Spec FR-012, Plan Slice 2 Boundary, Research Decision 5]

## Runner Contract Integration

- [x] CHK006 Are migrated active gates required to use `python -m speckit_pro_runner` operations wherever practical instead of separate command families? [Completeness, Spec FR-004, Plan Command Surface, Research Decision 2]
- [x] CHK007 Does the plan preserve the XPLAT-004 runner envelope: one JSON stdout response, line-delimited stderr diagnostics, and the status-to-exit-code contract? [Consistency, Spec Runner Stream And Exit Contract, Plan Command Surface, XPLAT-004 archive report]
- [x] CHK008 Are standalone Python commands constrained to unit/eval harnesses or justified non-authoritative wrappers that reuse runner implementation? [Clarity, Spec Runner Operation Rule, Plan Command Surface, Research Decision 2]
- [x] CHK009 Are command modes defined for read-only, dry-run, and apply behavior, with apply limited to source-checkout test evidence, temporary fixtures, or scoped verification metadata? [Coverage, Spec Mutable Command Mode Rule, Data Model Command Operation, Plan Slice 2]
- [x] CHK010 Do migrated operations require deterministic stdout, stderr, exit codes, artifact outputs, path handling, and missing-prerequisite diagnostics before release-readiness review? [Measurability, Spec FR-015, Plan Verification Plan, Data Model Command Operation]

## Prior XPLAT Contract Reuse

- [x] CHK011 Does XPLAT-007 explicitly reuse the XPLAT-004 runner package, manifest/checksum metadata, typed-path, subprocess fixture, runtime-info, and preflight primitives rather than reopening the runtime substrate decision? [Consistency, Spec FR-014, Plan Primary Dependencies, XPLAT-004 archive report]
- [x] CHK012 Are XPLAT-005 read-only helper registry and helper-record patterns preserved as source truth for existing helper contracts? [Completeness, Spec FR-014, Plan Structure Decision, XPLAT-005 fixture `read-only-helpers/fixture-manifest.json`]
- [x] CHK013 Are XPLAT-006 mutation, install, PR-emission, promotion, and deferred-live-mutation contracts preserved while XPLAT-007 replaces only active repo-local gates around them? [Consistency, Spec FR-014 to FR-016, Plan Primary Dependencies, XPLAT-006 fixture `mutation-helpers/promotion-records.json`]
- [x] CHK014 Does the plan create a small `gates/` package for release-gate behavior instead of folding gate authority into read-only helper modules or a broad generic framework? [Clarity, Plan Structure Decision, Constitution VI, Research Decision 9]
- [x] CHK015 Are preserved contract schemas and fixture roots named for runner, read-only helper, mutation helper, and XPLAT-007 gate evidence so reviewers can trace reuse? [Traceability, Plan Declared File Operations, Plan Project Structure, Data Model Promotion Record]

## Suite, Eval, Parity, And Promotion Flow

- [x] CHK016 Is Slice 1 required to migrate the default suite, Layer 1, Layer 4, Layer 5/tool-scoping, opt-in AI-eval dispatch, integration, and parity aggregation before later release-helper authority? [Coverage, Spec US1, Plan Slice 1, Workflow Focus]
- [x] CHK017 Does every migrated gate require golden fixtures and source-checkout Bash-reference comparison before it becomes Python-authoritative? [Completeness, Spec FR-005, Plan Promotion Bar, Research Decision 3]
- [x] CHK018 Are promotion records required to capture prior gate path, Python operation, request fixture, failure classes, comparison mode, stream/result evidence, artifact diff/hash, rollback, and Bash-reference retirement? [Measurability, Spec Promotion Record Rule, Data Model Promotion Record, Plan Promotion And Retirement Model]
- [x] CHK019 Does promotion require proof that the active-path guard no longer finds the Bash reference in active gate paths, while allowing inactive historical/parity evidence? [Consistency, Spec Bash Retirement Rule, Data Model Promotion Record, Research Decision 4]
- [x] CHK020 Are Windows-style paths, spaces, traversal rejection, line endings, fake-home roots, stale generated files, and local macOS source-checkout smoke represented in requirements and fixtures? [Coverage, Spec Edge Cases, Plan Verification Plan, Research Decision 7]

## Payload, Install, And Release-Readiness Integration

- [x] CHK021 Are payload builder requirements limited to isolated Claude/Codex test payload evidence with fixture or temporary output roots and `release_payload_cutover=false`? [Clarity, Spec FR-008, Data Model Payload Evidence, Quickstart Section 4]
- [x] CHK022 Do local refresh and install-verification requirements use fixture roots, fake-home paths, stubbed CLIs, bundled-agent inventory, version checks, and no real HOME or installed-cache mutation? [Coverage, Spec Local Refresh And Install Verification Rule, Data Model Install Verification Result, Quickstart Section 5]
- [x] CHK023 Are marketplace/version sync, changed-plugin detection, suite aggregation, PR-title validation, workflow-contract validation, release-PR payload-sync parsing, and post-release drift checks assigned to runner-backed release-readiness operations? [Completeness, Spec Release-Readiness Migration Rule, Plan Command Surface, Data Model Release-Readiness Result]
- [x] CHK024 Does the release-readiness model fail closed when promotion records, active-path guard status, test payload evidence, install verification, or marketplace/version evidence are stale or inconsistent? [Measurability, Spec FR-007, Data Model Release-Readiness Result, Quickstart Section 5]

## Active-Path Guard And XPLAT-008 Boundary

- [x] CHK025 Does the active-path guard fail active repo-local gate/release paths for Bash, `.sh` calls, `jq`, Git Bash, WSL, PowerShell helper dependency, shell parsing, shell interpolation, `shell=True`, `os.system`, and command-string subprocess calls? [Coverage, Spec FR-009, Spec Forbidden Pattern Rule, Data Model Active-Path Guard Finding]
- [x] CHK026 Are CI workflow shell snippets allowed only as direct dispatch glue to Python gates or non-plugin docs tooling, with no plugin validation, packaging, install, release, loop, `jq`, or parsing logic? [Consistency, Spec FR-011, Spec CI Dispatch Allowlist Rule, Research Decision 6]
- [x] CHK027 Does guard output define blocking counts, classified nonblocking counts, finding fields, expected-failure status, exit code `1`, clean `ok` status, and line-delimited diagnostics? [Measurability, Spec Guard Output Contract, Data Model Active-Path Guard Finding, Quickstart Section 3]
- [x] CHK028 Does the PR review packet requirement force changed-file mapping, parity/promotion evidence, guard evidence, rollback notes, known gaps, and explicit XPLAT-008 handoff items? [Completeness, Spec FR-018, Data Model XPLAT-008 Handoff Item, Plan Verification Plan]

## Integration Checklist Result

- Items: 28
- Initial gaps: 0
- Remediated gaps: 0
- Current gaps: 0
- Consensus: skipped because the integration requirements are already covered by the current spec, plan, contracts, workflow prompt, and prior XPLAT source evidence.
