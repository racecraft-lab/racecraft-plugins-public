# Data Model: Cross-Platform Runner Foundation

## Runner Request Envelope

Represents one structured runner invocation received on stdin.

**Fields**:

- `schema_version`: string. Must be `"1.0"` for XPLAT-004.
- `request_id`: optional string for caller correlation.
- `helper_id`: string. Must be `"runner"` for foundation operations.
- `operation`: string enum. Supported values are `"preflight"` and `"runtime-info"`; contract fixtures may exercise validation failure paths.
- `mode`: string. Must be `"read_only"` for XPLAT-004.
- `inputs`: object. Bounded operation-specific input data.

**Validation rules**:

- Malformed JSON returns `status: "input_error"` and process exit code `2`.
- Missing required fields returns `status: "input_error"` and process exit code `2`.
- Unsupported schema versions return `status: "input_error"` and process exit code `2`.
- Unsupported operations return a deterministic non-success response and do not execute helper behavior.

## Runner Response Envelope

Represents the single JSON response written to stdout.

**Fields**:

- `schema_version`: string. Mirrors the supported contract version.
- `request_id`: optional string copied from the request when provided.
- `status`: string enum such as `"success"`, `"input_error"`, `"prerequisite_missing"`, `"subprocess_failure"`, or `"internal_error"`.
- `exit_code`: integer process exit code selected by the runner contract.
- `legacy_exit_code`: integer or null for compatibility with prior shell-backed behavior.
- `diagnostics`: array of Diagnostic records.
- `data`: object containing operation-specific response data.

**Validation rules**:

- Exactly one response object is written to stdout.
- Diagnostics that need streaming visibility are also emitted as line-delimited JSON on stderr.
- Success responses must not hide failed prerequisite checks.

## Diagnostic

Represents a deterministic warning or error.

**Fields**:

- `severity`: `"info"`, `"warning"`, or `"error"`.
- `source`: `"runner"` for XPLAT-004 runner diagnostics.
- `code`: stable machine-readable diagnostic code.
- `message`: short human-readable summary.
- `details`: optional object with bounded structured context.

**Validation rules**:

- Contract fixture diagnostics must use stable codes for invalid JSON, invalid envelope, unsupported schema version, missing fields, missing prerequisites, subprocess nonzero, subprocess timeout, and stderr-only failure.
- Stderr diagnostics are line-delimited JSON objects, not plain text logs.

## Typed Path

Represents a path without shell-specific parsing assumptions.

**Fields**:

- `kind`: path trust boundary and interpretation, for example `"plugin_relative"` or `"absolute"`.
- `value`: raw path value within the declared boundary.
- `display`: reader-facing display value.

**Validation rules**:

- Typed path fixtures accept only typed path objects.
- Paths with spaces remain one value and must not be split.
- Windows separators do not imply POSIX-only behavior.
- Traversal is rejected only when it escapes the declared trust boundary.

## Preflight Report

Represents runtime and environment readiness before later helper ports depend on the runner.

**Fields**:

- `runner_name`: `"speckit_pro_runner"`.
- `runner_contract_id`: `"speckit-pro-runner"`.
- `selected_runtime_name`: `"python-stdlib-runner"`.
- `contract_version`: durable command contract version.
- `runner_version`: runner implementation version.
- `python_version`: actual Python runtime version.
- `platform`: operating-system/platform string.
- `architecture`: machine architecture string.
- `source_vs_installed_context`: `"source_checkout"` for XPLAT-004.
- `paths`: typed paths for plugin root, runner package, manifest file, and checksum file.
- `prerequisites`: prerequisite records for Python and `specify`.
- `metadata`: manifest/checksum pointer records with verification status.

**Validation rules**:

- Python below 3.11 fails closed.
- Missing `specify` fails closed.
- Metadata status is `verified` only when current source metadata was actually checked.

## Prerequisite Record

Represents one runtime prerequisite check.

**Fields**:

- `name`: prerequisite name, for example `"python"` or `"specify"`.
- `required`: boolean.
- `status`: `"available"`, `"missing"`, `"too_old"`, or `"not_checked"`.
- `version`: optional discovered version.
- `path`: optional Typed Path or executable display path.
- `diagnostic_code`: optional failure code.

**Validation rules**:

- Required missing or too-old prerequisites make preflight non-success.
- Host-level failure to launch Python is outside the runner response guarantee and is covered by discovery/runbook evidence.

## Subprocess Result

Represents fixture-only process execution capture.

**Fields**:

- `argv`: array of string arguments.
- `exit_code`: integer or null when timeout prevents normal exit.
- `stdout`: captured bounded stdout string.
- `stderr`: captured bounded stderr string.
- `timed_out`: boolean.
- `duration_ms`: integer duration.
- `stderr_is_failure`: boolean fixture flag.

**Validation rules**:

- Execution uses `shell=False`.
- Nonzero, timeout, and stderr-only failure remain distinct fixture cases.
- Subprocess failures return `status: "subprocess_failure"` with process exit code `4`.

## Runner Metadata Manifest

Represents source-checkout identity and checksum coverage.

**Fields**:

- `runner_name`: `"speckit_pro_runner"`.
- `runner_contract_id`: `"speckit-pro-runner"`.
- `selected_runtime_name`: `"python-stdlib-runner"`.
- `contract_version`: durable command contract version.
- `plugin_version`: plugin version observed from source metadata.
- `runner_version`: runner implementation version.
- `source_revision`: source revision or `"unknown"` when not available.
- `python_minimum_version`: `"3.11"`.
- `specify_required`: boolean.
- `checksum_algorithm`: `"sha256"`.
- `runner_files`: array of runner-owned source file records.

**Validation rules**:

- Runner implementation source files under `speckit-pro/speckit_pro_runner/**.py` are covered.
- The manifest and checksum files are not included in their own checksum set.
- Paths use source-checkout `plugin_relative` values rooted at `speckit-pro/`.

## Contract Fixture

Represents one bounded fixture case for runner contract tests.

**Fields**:

- `case_id`: stable fixture identifier.
- `category`: fixture category such as envelope, typed path, subprocess, diagnostics, runtime-info, or preflight.
- `request`: request object or raw invalid input marker.
- `expected_status`: expected response status.
- `expected_exit_code`: expected process exit code.
- `expected_diagnostic_codes`: expected diagnostic code list.
- `notes`: optional reviewer-facing explanation.

**Validation rules**:

- Fixtures do not call real production helpers.
- Fixture coverage includes valid envelope, invalid JSON, invalid envelope, unsupported schema version, missing fields, typed path behavior, subprocess nonzero, subprocess timeout, stderr-only failure, missing prerequisites, runtime-info, and preflight.
