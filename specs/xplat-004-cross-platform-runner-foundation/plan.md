# Implementation Plan: Cross-Platform Runner Foundation

**Branch**: `codex/xplat-004-cross-platform-runner-foundation` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/xplat-004-cross-platform-runner-foundation/spec.md`

## Summary

Build the minimal Python 3.11+ standard-library runner foundation under `speckit-pro/speckit_pro_runner/`, invoked as `<python> -m speckit_pro_runner` from the package context. The implementation preserves the XPLAT-002 JSON stdin/stdout contract, status/exit-code vocabulary, and XPLAT-003 Python runtime decision while limiting behavior to runtime-info, preflight, contract smoke fixtures, and source-checkout metadata.

The accepted delivery strategy is two planned PR slices inside this one XPLAT-004 workflow:

1. Runner/preflight core.
2. Contract fixture parity plus checksum/manifest metadata.

No real helper ports, generated payload cutover, active skill/hook switch, install behavior change, or public native-platform support claim is in scope. XPLAT-005 and XPLAT-006 must extend this package, module entrypoint, and dispatch contract rather than reopening the package or invocation decision.

## Technical Context

**Language/Version**: Python 3.11+.

**Primary Dependencies**: Python standard library only; official Spec Kit `specify` prerequisite discovered by preflight; no package install, virtual environment restore, `jq`, Node, Bash helper, Go, Rust, Zig, native binary, PowerShell, or WSL dependency for runner execution.

**Storage**: Checked-in source and metadata files only. Runner source-checkout metadata lives under `speckit-pro/speckit_pro_runner/`.

**Testing**: Python stdlib runner tests through a Layer 4 entrypoint, plus existing shell gates for repository structure and generated index checks.

**Target Platform**: Source-checkout execution on maintainer machines with Python 3.11+. Windows/Linux/macOS installed-cache proof and native UAT remain deferred.

**Project Type**: Plugin runner package and test harness.

**Performance Goals**: Valid local preflight returns a structured response in under 5 seconds.

**Constraints**: JSON request on stdin; one JSON response on stdout; line-delimited JSON diagnostics on stderr using the same strict Diagnostic shape as stdout diagnostics; `shell=False` subprocess execution; explicit fixture subprocess timeouts at or below 5 seconds; stdout/stderr capture capped at 16 KiB per stream with byte counts and truncation flags; typed paths; XPLAT-002 status values `ok`, `expected_failure`, `input_error`, `missing_prerequisite`, `subprocess_failure`, and `internal_failure` with the 0-5 exit-code map; bounded structured remediation on failure diagnostics; source-checkout `plugin_relative` metadata; no copying into `dist/**`.

**Scale/Scope**: One small runner package, one Python contract test entrypoint, one compact fixture matrix, source metadata files, and planning/contract artifacts.

**Reviewability Budget**: Primary surface is `harness/adapter`; setup also flagged `docs/process` because this phase creates planning artifacts. Projected reviewable LOC is approximately 420, production/source metadata files stay at or below 6, and total implementation files should stay within 8-12. Budget result is a warning accepted through the two-slice plan.

## Declared File Operations

- NEW speckit-pro/speckit_pro_runner/__init__.py
- NEW speckit-pro/speckit_pro_runner/__main__.py
- NEW speckit-pro/speckit_pro_runner/envelope.py
- NEW speckit-pro/speckit_pro_runner/runtime.py
- NEW speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json
- NEW speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256
- NEW tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.sh
- NEW tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py
- NEW tests/speckit-pro/layer4-scripts/fixtures/speckit-pro-runner/contract-fixtures.json
- NEW specs/xplat-004-cross-platform-runner-foundation/contracts/platform-runbook-fixtures.md
- MODIFIED tests/speckit-pro/run-all.sh

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Plugin Structure Compliance**: Pass. Runner source and metadata stay inside `speckit-pro/` and do not alter plugin manifests, skills, hooks, or generated payloads.
- **II. Script Safety**: Pass with constraint. No runner shell launcher is introduced. The Layer 4 shell wrapper exists only to connect the Python stdlib test entrypoint to the existing shell test orchestrator and must use `#!/usr/bin/env bash` plus `set -euo pipefail`.
- **III. Semantic Versioning**: Pass. No plugin version bump or release metadata change is planned in XPLAT-004.
- **IV. Test Coverage Before Merge**: Pass with planned coverage. Slice 1 adds preflight/runtime-info tests; Slice 2 adds contract fixture, metadata, and manifest validation coverage. Existing deterministic gates remain in place.
- **V. Conventional Commits**: Pass. PR slices can use scoped Conventional Commit titles, for example `feat(speckit-pro): add runner preflight foundation`.
- **VI. KISS, Simplicity & YAGNI**: Pass with warning. The package is intentionally small, stdlib-only, and limited to foundation primitives. Real helper ports and active cutover are deferred.

**Re-check after Phase 1 design**: Pass. `research.md`, `data-model.md`, `quickstart.md`, and `contracts/` keep the same package boundary, source-checkout metadata boundary, and two-slice scope. No new runtime dependency or public support surface was introduced.

## Project Structure

### Documentation (this feature)

```text
specs/xplat-004-cross-platform-runner-foundation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── runner-envelope.schema.json
│   ├── runner-manifest.schema.json
│   └── platform-runbook-fixtures.md
├── checklists/
│   └── requirements.md
├── SPEC-MOC.md
└── spec.md
```

### Source Code (repository root)

```text
speckit-pro/
└── speckit_pro_runner/
    ├── __init__.py
    ├── __main__.py
    ├── envelope.py
    ├── runtime.py
    ├── speckit-pro-runner.manifest.json
    └── speckit-pro-runner.sha256

tests/
└── speckit-pro/
    ├── run-all.sh
    └── layer4-scripts/
        ├── test-speckit-pro-runner.sh
        ├── test-speckit-pro-runner.py
        └── fixtures/
            └── speckit-pro-runner/
                └── contract-fixtures.json
```

**Structure Decision**: Use a small package at `speckit-pro/speckit_pro_runner/`. `__main__.py` owns module invocation, `envelope.py` owns JSON request/response and diagnostics, and `runtime.py` owns preflight/runtime-info, typed path rendering, subprocess result capture for fixtures, prerequisite discovery, plugin-root detection, and source metadata checks. Plugin-root detection starts from the runner package file location and walks ancestors to the nearest directory containing `.claude-plugin/plugin.json` or `.codex-plugin/plugin.json`; it must fail closed if neither anchor is found.

## Implementation Strategy

### Slice 1: Runner/preflight core

**Goal**: Establish `<python> -m speckit_pro_runner` for source-checkout runtime-info and preflight using Python 3.11+ stdlib only.

**Primary files**: `__init__.py`, `__main__.py`, `envelope.py`, `runtime.py`, `test-speckit-pro-runner.py`, `test-speckit-pro-runner.sh`, and `tests/speckit-pro/run-all.sh`.

**Behavior**:

- Accept XPLAT-002 request envelopes on stdin with `schema_version: "1.0"`, `helper_id: "runner"`, `operation: "preflight"` or `"runtime-info"`, and `mode: "read_only"` for this foundation slice, while keeping `helper_id`, `operation`, and `mode` as the stable dispatch fields later helper ports extend.
- Return one JSON response on stdout using XPLAT-002 status values: `ok`, `expected_failure`, `input_error`, `missing_prerequisite`, `subprocess_failure`, and `internal_failure`.
- Emit line-delimited JSON diagnostics on stderr.
- Discover Python 3.11+ and `specify` prerequisites, failing closed when unavailable with `python_too_old`, `python_launcher_unavailable` discovery/runbook evidence, or `specify_missing` as applicable.
- Report `runner_name: "speckit_pro_runner"`, `runner_contract_id: "speckit-pro-runner"`, `selected_runtime_name: "python-stdlib-runner"`, `source_vs_installed_context: "source_checkout"`, the detected plugin root, and plugin-relative metadata pointers.

**Verification**:

- Python stdlib runner tests for valid runtime-info/preflight and missing-prerequisite behavior.
- `bash tests/speckit-pro/run-all.sh --layer 4`.
- `git diff --check`.

### Slice 2: Contract fixture parity plus metadata

**Goal**: Add the XPLAT-002 fixture runway and XPLAT-003/XPLAT-004 source metadata without switching installed workflows.

**Primary files**: `contract-fixtures.json`, `speckit-pro-runner.manifest.json`, `speckit-pro-runner.sha256`, `contracts/platform-runbook-fixtures.md`, and expanded runner tests.

**Behavior**:

- Cover invalid JSON, invalid envelope, unsupported schema version, missing fields, typed path values, paths with spaces, Windows separators, traversal boundary handling, missing prerequisites, subprocess nonzero, subprocess timeout, stderr-only failure, runtime-info, and preflight. Non-`ok` fixtures must assert expected diagnostic codes and remediation objects, not only status and exit code. Subprocess fixtures must use explicit timeouts no greater than 5 seconds and assert stdout/stderr output-capture records with a 16 KiB per-stream limit, byte counts, and truncation flags.
- Keep subprocess execution shell-disabled and fixture-only.
- Store manifest and checksum files under `speckit-pro/speckit_pro_runner/`, using `plugin_relative` values rooted at the detected plugin root, such as `speckit_pro_runner/...`, not absolute source-checkout paths or repo-root-relative values.
- Set metadata `verification_status` to `verified`, `mismatch`, `missing_metadata`, `incomplete_metadata`, or `not_checked` based on actual checks. Preflight must fail closed with `missing_prerequisite` exit code `3` and metadata diagnostics when required metadata is missing, incomplete, mismatched/stale, or not checked.
- Add deterministic Windows/Linux runbook fixtures that record source-checkout context, launcher command family, expected status/exit/diagnostic outcomes, metadata verification expectation, and explicit non-claim language. These fixtures must not be described as installed-cache launch proof, native matrix UAT, release-readiness, or public platform support.

**Verification**:

- Python stdlib contract fixture tests.
- `python3 -m json.tool speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`.
- `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"`.
- Relevant Layer 1 checks when structural files change.
- Full deterministic suite before PR when feasible: `bash tests/speckit-pro/run-all.sh`.

## Downstream Handoff Rules

XPLAT-005 and XPLAT-006 consume this foundation by adding helper IDs,
operations, modes, fixture cases, and compatibility-adapter records to the same
runner package and module entrypoint. They must not introduce a new package
path, shell launcher, helper-specific CLI argument model, or alternate
stdin/stdout envelope.

XPLAT-004 defines the extension rule only. Row-level XPLAT-001 mappings,
owner buckets, real helper IDs, real helper operations, and compatibility
adapter records stay downstream unless a bounded contract fixture needs a
synthetic example. Generated payload copying and installed-cache launch proof
remain XPLAT-007 responsibilities.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Reviewability warning around `docs/process` plus `harness/adapter`, with projected reviewable LOC around 420 | XPLAT-004 must produce planning artifacts and a runner foundation with contract fixtures and metadata in one workflow | Child specs or extra branches were rejected during scaffolding; the accepted approach is one workflow with two planned reviewable PR slices |

## Deferred Work

- XPLAT-005 owns real read-only helper ports.
- XPLAT-006 owns mutation helper ports.
- XPLAT-007 owns generated payload propagation, active Claude/Codex cutover, installed-cache launch proof, native Windows/macOS/Linux UAT, consumer checksum guidance, release-readiness evidence, and public support-claim audit.
- Release automation, signatures, SBOMs, provenance attestations, reproducible builds, and formal audit evidence remain outside XPLAT-004.
