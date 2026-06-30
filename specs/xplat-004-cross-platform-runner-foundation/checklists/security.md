# Security Checklist: Cross-Platform Runner Foundation

**Purpose**: Validate security and claim-boundary requirements for the XPLAT-004 runner foundation before tasks and implementation.
**Created**: 2026-06-30
**Feature**: [spec.md](../spec.md)

**Note**: This checklist is generated from the workflow's `$speckit-checklist security` prompt. It tests requirement quality, not implementation behavior.

## Dependency Boundary

- [x] CHK001 Is the Python 3.11+ standard-library-only runtime boundary stated as a requirement rather than an implementation preference? [Clarity, Spec §Input, Plan §Technical Context]
- [x] CHK002 Are package install, virtual environment restore, `jq`, Node, Bash helper, Go, Rust, Zig, native binary, PowerShell, and WSL dependencies excluded for runner execution? [Completeness, Plan §Technical Context]
- [x] CHK003 Does the plan preserve the existing shell test orchestrator only as an outer gate while keeping runner execution and runner-specific tests Python stdlib based? [Consistency, Spec §Clarifications Session 1, Plan §Testing/Constitution Check]
- [x] CHK004 Are shell quoting and shell launcher dependencies excluded from runner invocation and subprocess fixture execution? [Security, Spec §Clarifications Session 1, Plan §Technical Context]

## Runner Identity And Preflight Controls

- [x] CHK005 Are runner identity fields separated between Python package name, durable contract ID, and selected runtime name? [Completeness, Spec §Clarifications Session 3, Data Model §Runner Metadata Manifest]
- [x] CHK006 Does preflight report runtime version, platform, architecture, plugin root, prerequisite status, source-checkout context, and typed metadata pointers before downstream helper ports depend on it? [Completeness, Spec §FR-003, Data Model §Preflight Report]
- [x] CHK007 Are Python and `specify` prerequisite failures required to fail closed with deterministic diagnostics instead of continuing with partial readiness? [Security, Spec §FR-004/FR-005, Data Model §Prerequisite Record]
- [x] CHK008 Does plugin-root detection start from the resolved runner package file location and fail closed when plugin manifest anchors are absent? [Security, Spec §FR-015, Plan §Project Structure]

## Checksum And Manifest Metadata

- [x] CHK009 Are the source-checkout manifest and checksum files located with the runner package under `speckit-pro/speckit_pro_runner/`? [Completeness, Spec §Clarifications Session 3, Plan §Declared File Operations]
- [x] CHK010 Is checksum coverage required for runner-owned Python source files while excluding the manifest and checksum files from their own checksum set? [Security, Spec §Clarifications Session 3, Data Model §Runner Metadata Manifest]
- [x] CHK011 Are manifest fields specified for runner identity, contract version, plugin version, runner version, source revision, Python minimum, `specify` requirement, checksum algorithm, and covered files? [Completeness, Spec §Clarifications Session 3, Contract §runner-manifest]
- [x] CHK012 Are metadata path values constrained to `plugin_relative` paths rooted at the detected plugin root rather than absolute checkout paths or repo-root-relative paths? [Security, Spec §FR-016, Contract §runner-manifest]
- [x] CHK013 Does preflight use explicit metadata verification states and refuse `ok` readiness when metadata is missing, incomplete, stale/mismatched, or not checked? [Security, Spec §Clarifications Session 2/3, Data Model §Preflight Report]

## Non-Claim And Deferred Trust Boundaries

- [x] CHK014 Are signatures, SBOMs, provenance attestations, reproducible builds, formal audit evidence, release automation, and public support claims explicitly deferred outside XPLAT-004? [Completeness, Spec §Reviewability Notes, Plan §Deferred Work]
- [x] CHK015 Are generated payload propagation, active Claude/Codex cutover, install behavior changes, installed-cache launch proof, and public claim audit deferred to XPLAT-007? [Consistency, Spec §Clarifications Session 3, Plan §Deferred Work]
- [x] CHK016 Does the spec prevent source-checkout metadata from being described as public release readiness by naming `source_checkout` context and assigning release-readiness evidence to XPLAT-007? [Security, Spec §Clarifications Session 3, Spec §Assumptions, Plan §Deferred Work]
- [x] CHK017 Do success criteria require zero runner cutover or public native-platform support claims in active skills, hooks, generated payloads, public docs, and install behavior? [Measurability, Spec §SC-005]

## Fixture And Review Evidence Boundaries

- [x] CHK018 Are metadata-readiness failures covered by deterministic fixture requirements with diagnostic codes and remediation, not only by reviewer inspection? [Scenario Coverage, Spec §FR-010/FR-020, Data Model §Diagnostic Code Inventory]
- [x] CHK019 Are contract fixtures limited to runner primitives and explicitly prevented from porting real production helper behavior? [Scope, Spec §FR-011, Data Model §Contract Fixture]
- [x] CHK020 Does the review packet requirement force deferred work to name follow-up specs so security and trust work is not silently treated as complete in XPLAT-004? [Traceability, Spec §PR Review Packet Requirements]

## Security Checklist Result

- Items: 20
- Initial gaps: 0
- Remediated gaps: 0
- Current gaps: 0

## Re-run Verification

- Re-ran the same security checklist focus after the initial pass.
- Result: 20/20 items satisfied; no current gap markers remain.
