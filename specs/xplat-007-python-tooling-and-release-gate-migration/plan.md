# Implementation Plan: Python Tooling and Release-Gate Migration

**Branch**: `codex/xplat-007-python-tooling-and-release-gate-migration` | **Date**: 2026-07-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/xplat-007-python-tooling-and-release-gate-migration/spec.md`

## Summary

Replace active repo-local Bash-backed test, eval, payload, install-verification,
helper, and release-readiness gates with Python 3.11+ standard-library
operations exposed through `python -m speckit_pro_runner`. XPLAT-007 remains one
workflow with three reviewable slices: test/eval gates first, payload/install
and release helpers second, then active-path guardrails and Bash-reference
cleanup. Generated release payload cutover, installed Claude/Codex invocation
cutover, public docs, release notes, update, autoheal, and native installed UAT
remain XPLAT-008.

## Technical Context

**Language/Version**: Python 3.11+ standard library through `speckit-pro/speckit_pro_runner/`

**Primary Dependencies**: Existing runner envelope, diagnostics, typed path, subprocess fixture, helper registry, XPLAT-005 read-only helper records, and XPLAT-006 mutation/install/PR-emission contracts; no new runtime dependency

**Storage**: Checked-in source files, fixtures, JSON schemas, runner metadata, test payload evidence under fixture or temporary output roots; no database

**Testing**: Python standard-library tests and deterministic fixture requests;
Bash-reference comparison is temporary migration proof only

**Target Platform**: Source-checkout macOS smoke plus deterministic
Windows-style path fixtures. Native installed-cache UAT remains XPLAT-008.

**Project Type**: Plugin marketplace repository with runner-backed CLI-like JSON-envelope operations

**Performance Goals**: Deterministic release-gate behavior with bounded stdout,
stderr, and artifact captures. Gates should fail closed with stable diagnostics
instead of falling back to shell behavior.

**Constraints**: Python-only active gates; no Bash, `.sh`, `jq`, Git Bash, WSL,
PowerShell helper scripts, shell interpolation, `shell=True`, `os.system`, or
shell-only parsing in promoted active paths. Remaining CI shell may dispatch
directly to Python gates only and must contain no plugin validation, packaging,
install, release, or runtime logic.

**Scale/Scope**: Active repo-local gates across `tests/speckit-pro/**`,
payload/release helpers, reachable plugin helper scripts, and plugin
release/test workflows. Historical/archive text, consumer `.specify/scripts/bash`
helpers, generated payload mirrors, and XPLAT-008 cutover surfaces are
classified but nonblocking unless reachable from an active gate.

**Reviewability Budget**: Primary surfaces `harness/adapter` and
`docs/process`; setup gate recorded `status=warn`, `pass=true`, two primary
surfaces, no blockers. The warning is accepted for one workflow with three
internal slices. Split before implementation only if tasks prove the planned
slice order cannot stay under the roadmap block thresholds.

## Declared File Operations

- NEW speckit-pro/speckit_pro_runner/gates/__init__.py
- NEW speckit-pro/speckit_pro_runner/gates/registry.py
- NEW speckit-pro/speckit_pro_runner/gates/suite.py
- NEW speckit-pro/speckit_pro_runner/gates/payloads.py
- NEW speckit-pro/speckit_pro_runner/gates/release.py
- NEW speckit-pro/speckit_pro_runner/gates/active_path_guard.py
- MODIFIED speckit-pro/speckit_pro_runner/runtime.py
- MODIFIED speckit-pro/speckit_pro_runner/helpers/registry.py
- MODIFIED speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json
- MODIFIED speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256
- NEW tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py
- NEW tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-default-suite.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/active-path-guard.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/test-payload-evidence.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/install-verification.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/release-readiness.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/promotion-records.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/active-path-guard-cases.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/payload-evidence-cases.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/release-readiness-cases.json
- NEW tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/install-verification-cases.json
- MODIFIED .github/workflows/pr-checks.yml
- MODIFIED .github/workflows/release.yml
- MODIFIED CLAUDE.md
- MODIFIED docs-site/src/content/docs/contribute-and-release.md

Legacy `.sh` entrypoints are expected to leave active gate/release paths after
promotion. The task phase should record concrete deletion or inactive-parity
classification because this template accepts only `NEW` and `MODIFIED` lines.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Plan Evidence |
|---|---|---|
| I. Plugin Structure Compliance | PASS | New runner operations stay under `speckit-pro/` and fixture/test additions stay under `tests/speckit-pro/`. |
| II. Script Safety | PASS | No new Bash scripts are planned. Existing Bash references are temporary comparison or retirement targets, not promoted gates. |
| III. Semantic Versioning | PASS | No manual plugin version edit is planned. Marketplace/version sync is checked by runner operations only. |
| IV. Test Coverage Before Merge | PASS | Each migrated gate requires fixture coverage, Bash-reference comparison while available, and per-gate promotion records before authority changes. |
| V. Conventional Commits | PASS | No commit is produced by this phase; PR title/commit validation remains a release-readiness gate. |
| VI. KISS, Simplicity & YAGNI | PASS | The design uses explicit runner operations and fixture records rather than a generic command framework. |

## Project Structure

### Documentation (this feature)

```text
specs/xplat-007-python-tooling-and-release-gate-migration/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── active-path-guard-result.schema.json
│   ├── install-verification-result.schema.json
│   ├── migrated-gate-request.schema.json
│   ├── migrated-gate-result.schema.json
│   ├── payload-evidence.schema.json
│   ├── promotion-record.schema.json
│   └── release-readiness-result.schema.json
└── tasks.md
```

### Source Code (repository root)

```text
speckit-pro/
└── speckit_pro_runner/
    ├── runtime.py
    ├── helpers/
    │   └── registry.py
    └── gates/
        ├── __init__.py
        ├── registry.py
        ├── suite.py
        ├── payloads.py
        ├── release.py
        └── active_path_guard.py

tests/speckit-pro/
├── layer4-scripts/
│   ├── test-speckit-pro-gates.py
│   └── fixtures/xplat-007-gates/
│       ├── requests/
│       ├── active-path-guard-cases.json
│       ├── payload-evidence-cases.json
│       ├── release-readiness-cases.json
│       ├── install-verification-cases.json
│       └── promotion-records.json
└── existing layer fixtures retained only as parity evidence until promotion

.github/workflows/
├── pr-checks.yml
└── release.yml
```

**Structure Decision**: Use a small `gates/` package for active repo-local gates
instead of folding release-gate behavior into read-only helper modules. Keep
XPLAT-005/XPLAT-006 helper registries as source truth for existing helper
contracts, and expose new gate operations through the same runner envelope,
status, stdout, stderr, and exit-code contract.

## Implementation Slices

### Slice 1: Test/Eval Runner Gates

Port the top-level deterministic runner, Layer 1 structural checks, Layer 4
helper tests, Layer 5 tool-scoping checks, opt-in AI-eval dispatch, integration,
and parity suite aggregation into runner operations. This slice establishes the
Python-authoritative verification base used by later slices.

Promotion bar:

- golden request fixtures for success and expected failures
- source-checkout Bash-reference comparison while the legacy gate exists
- semantic JSON comparison where old stdout is structured
- exact stderr and exit-code comparison unless a declared normalization applies
- promotion record proving the Bash reference is no longer active

### Slice 2: Payload, Install, And Release Helpers

Move test payload evidence, local plugin refresh fixtures, marketplace/version
sync, install verification, release checks, release-PR payload-sync parsing,
post-release drift checks, and release-readiness aggregation into runner
operations. Operations use `read_only`, `dry_run`, and narrowly scoped `apply`
modes. In XPLAT-007, `apply` may write only source-checkout test evidence,
temporary fixtures, or explicitly declared repo-local verification metadata.

Boundary:

- rebuild isolated Claude/Codex test payload evidence only
- do not select, publish, or cut over generated release payloads
- do not mutate real `HOME` or installed plugin caches
- verify install behavior only through fake-home, fixture roots, stubbed CLIs,
  command plans, bundled-agent inventory, and doctor/preflight records

### Slice 3: Active-Path Guardrails And Cleanup

Add the active-path no-shell/no-jq guard, update plugin CI dispatch steps to call
runner operations, remove or reclassify active Bash references after promotion,
and write the XPLAT-008 handoff. The guard scans tracked text and classifies all
findings, but blocks only active repo-local gate/release paths.

Blocking active findings include Bash/shebangs, `.sh` executable calls, `jq`,
Git Bash, WSL, PowerShell helper dependencies, `grep`/`sed`/`awk` parsing
pipelines in active gates, command substitution, `shell=True`, `os.system`, and
command-string subprocess calls.

## Command Surface

Authoritative active gates use `python -m speckit_pro_runner` with a JSON
request envelope on stdin and one JSON response on stdout. Stderr remains
line-delimited runner diagnostics. Exit semantics remain:

| Status | Exit |
|---|---:|
| `ok` | 0 |
| `expected_failure` | 1 |
| `input_error` | 2 |
| `missing_prerequisite` | 3 |
| `subprocess_failure` | 4 |
| `internal_failure` | 5 |

Planned operation groups:

| Group | Operations | Authority |
|---|---|---|
| Suite gates | `run-default-suite`, `run-layer`, `run-ai-evals`, `run-integration-suite`, `run-parity-suite` | Runner-authoritative after promotion |
| Payload/install | `build-test-payload-evidence`, `refresh-local-plugin-fixture`, `verify-install` | Runner-authoritative fixture/dry-run/apply modes only |
| Release readiness | `detect-changed-plugin`, `aggregate-suite-results`, `check-marketplace-version-sync`, `validate-pr-title`, `validate-workflow-contract`, `check-payload-evidence`, `parse-release-pr-payload-sync`, `check-post-release-drift`, `release-readiness` | Runner-authoritative |
| Guardrails | `active-path-guard`, `classify-shell-finding` | Runner-authoritative |

Standalone Python is allowed only for unit/eval harnesses that call the same
runner implementation or for a justified non-authoritative ergonomic wrapper.
No standalone Python command may become the release contract when a runner
operation can provide the same behavior.

## Promotion And Retirement Model

Each migrated gate must produce a promotion record with:

- prior Bash gate or command path
- Python operation and fixture request
- fixture ids and failure classes
- path, line-ending, artifact, and stderr/stdout coverage
- exact or semantic comparison mode
- legacy and runner exit-code result
- artifact hash or diff result where files are produced
- rollback path
- Bash-reference retirement classification

Promotion is complete only when the active-path guard proves no active gate,
workflow, helper, release-readiness command, or maintainer run instruction still
invokes the retired Bash reference. Bash-reference manifests may remain as
inactive historical/parity evidence only.

## Verification Plan

Planning artifacts:

1. Validate JSON schema syntax for `contracts/*.schema.json`.
2. Check `plan.md`, `research.md`, `data-model.md`, and `quickstart.md` for
   unresolved clarification, gap, or critical marker text.
3. Run G3 validation for the feature directory if the existing gate accepts the
   generated plan artifacts.

Implementation phase targets:

1. Run runner source-checkout smoke through `runtime-info` and `preflight`,
   including manifest/checksum metadata validation after runner file changes.
2. Run focused gate fixtures for each migrated operation.
3. Run active-path guard and verify blocking count is zero.
4. Rebuild test payload evidence and verify release cutover remains false.
5. Run local macOS source-checkout smoke.
6. Run Layer 1, Layer 4, and default deterministic suite through Python paths
   after promotion.
7. Confirm no active Claude/Codex invocation, generated release payload,
   public install/runtime docs, release notes, update, autoheal, or native UAT
   surface changed.

## Phase 1 Design Recheck

| Principle | Status | Recheck Evidence |
|---|---|---|
| Plugin Structure Compliance | PASS | Planned package, test, fixture, and contract paths fit the existing plugin repository layout. |
| Script Safety | PASS | The design introduces no new shell scripts and requires active `.sh` retirement after promotion. |
| Semantic Versioning | PASS | Version files are not part of the plan-phase output or planned implementation. |
| Test Coverage Before Merge | PASS | All migrated gates require fixture tests, parity comparison, promotion records, and guard evidence. |
| Conventional Commits | PASS | No commit is produced by this phase. |
| KISS, Simplicity & YAGNI | PASS | Explicit operation modules avoid a speculative framework while preserving the runner envelope. |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Reviewability warning: two primary surfaces, `harness/adapter` and `docs/process` | XPLAT-007 must change active gate mechanics and produce process evidence that proves temporary Bash parity, promotion, guard status, and XPLAT-008 handoff. | Splitting before tasks would separate the runner authority model from the release/guard evidence that reviewers need to evaluate the migration. |
