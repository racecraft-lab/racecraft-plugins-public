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

- Malformed JSON returns `status: "input_error"`, process exit code `2`, and diagnostic code `invalid_json`.
- Structurally invalid envelopes, including wrong field types, wrong `helper_id`, wrong `operation`, wrong `mode`, or disallowed extra fields, return `status: "input_error"`, process exit code `2`, and diagnostic code `invalid_envelope`.
- Missing required fields returns `status: "input_error"`, process exit code `2`, and diagnostic code `missing_required_field`.
- Unsupported schema versions return `status: "input_error"`, process exit code `2`, and diagnostic code `unsupported_schema_version`.
- Unsupported operations return a deterministic non-`ok` response and do not execute helper behavior.

## Runner Response Envelope

Represents the single JSON response written to stdout.

**Fields**:

- `schema_version`: string. Mirrors the supported contract version.
- `request_id`: optional string copied from the request when provided.
- `status`: string enum. Allowed wire values are `"ok"`, `"expected_failure"`, `"input_error"`, `"missing_prerequisite"`, `"subprocess_failure"`, and `"internal_failure"`.
- `exit_code`: integer process exit code selected by the runner contract.
- `legacy_exit_code`: integer or null for compatibility with prior shell-backed behavior.
- `diagnostics`: array of Diagnostic records.
- `data`: object containing operation-specific response data.

**Validation rules**:

- Exactly one response object is written to stdout.
- Diagnostics that need streaming visibility are also emitted as line-delimited JSON on stderr using the same Diagnostic shape.
- `ok` responses must not hide failed prerequisite checks.

**Exit-code map**:

| Code | Status | Contract meaning |
|---:|---|---|
| 0 | `ok` | Successful runner or helper completion |
| 1 | `expected_failure` | Expected helper or domain failure |
| 2 | `input_error` | Invalid usage, malformed JSON, or schema error |
| 3 | `missing_prerequisite` | Required runtime, executable, or input prerequisite unavailable |
| 4 | `subprocess_failure` | Subprocess nonzero, timeout, or stderr-only failure category |
| 5 | `internal_failure` | Unexpected runner exception or unclassified internal failure |

## Diagnostic

Represents a deterministic warning or error.

**Fields**:

- `severity`: `"info"`, `"warning"`, or `"error"`.
- `source`: `"runner"` for XPLAT-004 runner diagnostics.
- `code`: stable machine-readable diagnostic code.
- `message`: short human-readable summary.
- `remediation`: required object with a short `summary`, one to three bounded `actions`, and optional `deferred_to` owner/spec when the fix is outside the runner response boundary.
- `details`: optional object with bounded structured context.

**Validation rules**:

- Contract fixture diagnostics must use stable codes for invalid JSON, invalid envelope, unsupported schema version, missing fields, missing prerequisites, subprocess nonzero, subprocess timeout, stderr-only failure, and metadata readiness failures.
- Stderr diagnostics are line-delimited JSON objects, not plain text logs.
- Diagnostics in stdout and stderr include remediation; informational diagnostics use a no-action remediation summary rather than changing the JSON shape.
- Diagnostic `details` must stay bounded and must not embed unbounded subprocess stdout/stderr. Large captured streams are represented through Output Capture records with byte counts, limits, and truncation flags.

**Diagnostic code inventory**:

| Code | Status | Exit code | Meaning |
|---|---|---:|---|
| `invalid_json` | `input_error` | 2 | Stdin is not a valid JSON document |
| `invalid_envelope` | `input_error` | 2 | Request envelope is the wrong type, contains wrong field values, or contains disallowed extra fields |
| `unsupported_schema_version` | `input_error` | 2 | `schema_version` is present but not supported by XPLAT-004 |
| `missing_required_field` | `input_error` | 2 | One or more required envelope fields are absent |
| `python_too_old` | `missing_prerequisite` | 3 | The launched Python interpreter is below 3.11 |
| `python_launcher_unavailable` | `missing_prerequisite` | 3 | Discovery/runbook evidence could not launch any Python 3.11+ executable; no runner stdout response is promised |
| `specify_missing` | `missing_prerequisite` | 3 | Official SpecKit `specify` is missing or undiscoverable |
| `plugin_root_missing` | `missing_prerequisite` | 3 | No `.claude-plugin/plugin.json` or `.codex-plugin/plugin.json` anchor was found by walking ancestors from the runner package |
| `runner_metadata_missing` | `missing_prerequisite` | 3 | Required runner manifest or checksum metadata is absent |
| `runner_metadata_incomplete` | `missing_prerequisite` | 3 | Required metadata exists but lacks required source file coverage or required fields |
| `runner_metadata_mismatch` | `missing_prerequisite` | 3 | Required metadata exists but is stale or does not match current source checksums |
| `runner_metadata_not_checked` | `missing_prerequisite` | 3 | Preflight skipped a required metadata check and therefore cannot claim readiness |
| `subprocess_nonzero` | `subprocess_failure` | 4 | Fixture subprocess exited nonzero |
| `subprocess_timeout` | `subprocess_failure` | 4 | Fixture subprocess exceeded its configured timeout |
| `subprocess_stderr_only_failure` | `subprocess_failure` | 4 | Fixture marks stderr output as failure through `stderr_is_failure: true` |

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
- Missing plugin-root anchors fail closed with `plugin_root_missing`.
- Metadata status is `verified` only when current source metadata was actually checked.
- Preflight returns `missing_prerequisite` with exit code `3` when required metadata is missing, incomplete, mismatched/stale, or not checked.
- Runtime-info may report `not_checked` for metadata only when it is not claiming preflight readiness.

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

- Required missing or too-old prerequisites make preflight return `missing_prerequisite` with exit code `3`.
- Python below 3.11 uses diagnostic code `python_too_old`.
- Missing or undiscoverable `specify` uses diagnostic code `specify_missing`.
- Host-level failure to launch any Python 3.11+ executable is outside the runner response guarantee and is covered by discovery/runbook evidence with diagnostic code `python_launcher_unavailable` plus remediation.

## Output Capture

Represents one bounded captured stream from a fixture subprocess.

**Fields**:

- `text`: captured text after applying the XPLAT-004 stream limit.
- `byte_count`: integer count of bytes observed before truncation.
- `limit_bytes`: integer capture limit. XPLAT-004 fixture records use `16384`.
- `truncated`: boolean indicating whether raw output exceeded `limit_bytes`.

**Validation rules**:

- XPLAT-004 fixture subprocesses cap stdout and stderr independently at 16 KiB per stream.
- Truncated output remains a deterministic fixture outcome, not an internal failure.
- Failure diagnostics may reference byte counts and truncation flags but must not duplicate unbounded stream text in diagnostic `details`.

## Subprocess Result

Represents fixture-only process execution capture.

**Fields**:

- `argv`: array of string arguments.
- `exit_code`: integer or null when timeout prevents normal exit.
- `stdout`: Output Capture record for bounded standard output.
- `stderr`: Output Capture record for bounded standard error.
- `timed_out`: boolean.
- `timeout_seconds`: explicit timeout applied to this fixture subprocess; XPLAT-004 fixture values must be greater than `0` and no greater than `5`.
- `duration_ms`: integer duration.
- `stderr_is_failure`: boolean fixture flag.

**Validation rules**:

- Execution uses `shell=False`.
- Nonzero, timeout, and stderr-only failure remain distinct fixture cases.
- Subprocess failures return `status: "subprocess_failure"` with process exit code `4`.
- Subprocess failure diagnostics use `subprocess_nonzero`, `subprocess_timeout`, or `subprocess_stderr_only_failure`.
- Every fixture subprocess sets `timeout_seconds` explicitly, and contract tests assert timeout and output-bound fields in failure records.

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
- Paths use `plugin_relative` values rooted at the detected plugin root. In source checkout that root is `speckit-pro/`, but stored values omit the root prefix, for example `speckit_pro_runner/__main__.py`.

## Contract Fixture

Represents one bounded fixture case for runner contract tests.

**Fields**:

- `case_id`: stable fixture identifier.
- `category`: fixture category such as envelope, typed path, subprocess, diagnostics, runtime-info, or preflight.
- `request`: request object or raw invalid input marker.
- `expected_status`: expected response status.
- `expected_exit_code`: expected process exit code.
- `expected_diagnostic_codes`: expected diagnostic code list.
- `expected_remediation`: required expected remediation object for non-`ok` fixture cases.
- `expected_output_bounds`: optional object for subprocess fixtures, asserting timeout and stdout/stderr capture limits.
- `notes`: optional reviewer-facing explanation.

**Validation rules**:

- Fixtures do not call real production helpers.
- Fixture coverage includes valid envelope, invalid JSON, invalid envelope, unsupported schema version, missing fields, typed path behavior, subprocess nonzero, subprocess timeout, stderr-only failure, missing prerequisites, runtime-info, and preflight.
- Every non-`ok` fixture asserts expected diagnostic codes and remediation object presence.
- Subprocess fixtures assert `timeout_seconds`, `limit_bytes`, `byte_count`, and `truncated` expectations for each captured stream.

## Platform Runbook Fixture

Represents deterministic Windows/Linux proof guidance for XPLAT-004 without claiming installed-cache or public platform readiness.

**Fields**:

- `fixture_id`: stable fixture identifier.
- `platform_family`: `"windows"` or `"linux"` for XPLAT-004 deterministic runbook fixtures.
- `evidence_context`: `"source_checkout"` for XPLAT-004 unless a later spec performs installed-cache UAT.
- `launcher_command_family`: expected launcher family, for example Windows `py -3.11`/`python`/`python3` discovery or Linux `python3`/`python` discovery.
- `request_kind`: `"runtime-info"` or `"preflight"`.
- `expected_status`: expected runner status or `missing_prerequisite` for host-level discovery proof.
- `expected_exit_code`: expected process exit code when the runner starts, or null when host-level Python launch fails before a runner response exists.
- `expected_diagnostic_codes`: expected diagnostic codes, including `python_launcher_unavailable` when no Python 3.11+ launcher can start the runner.
- `metadata_verification_status`: expected metadata state, such as `verified`, `mismatch`, `missing_metadata`, `incomplete_metadata`, or `not_checked`.
- `non_claim_statement`: required text stating that XPLAT-004 fixture evidence is not installed-cache proof, native matrix UAT, release-readiness, or public platform support.

**Validation rules**:

- Windows/Linux runbook fixtures must label source-checkout context explicitly.
- Fixture rows must not say or imply public native-platform readiness.
- Installed-cache launch proof, public claim audit, and full native Windows/macOS/Linux UAT remain XPLAT-007 unless that spec records actual native evidence.
