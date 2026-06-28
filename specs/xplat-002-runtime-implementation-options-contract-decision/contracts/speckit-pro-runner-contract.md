# Contract: `speckit-pro-runner`

This contract is the XPLAT-002 handoff shape for XPLAT-004. It defines the
command interface that the selected runtime must implement after XPLAT-002
chooses the runtime. It does not implement the runner.

## Selected Runtime

- Runtime family: Python standard-library runner aligned with the official
  Spec Kit / `specify` prerequisite boundary.
- Implementation runtime: Python 3.11+ using the standard library.
- Selection source:
  `specs/xplat-002-runtime-implementation-options-contract-decision/runtime-decision.md`
- Packaging constraint: the installed plugin payload carries Python runner
  source and any thin launch metadata needed by Claude Code and Codex. Users
  must not run `npm install`, `pip install`, virtualenv restoration, `uv`,
  `brew`, Go/Rust/Zig toolchain setup, or network package restoration after the
  plugin cache is populated.
- Prerequisite boundary: SpecKit-Pro may require a healthy official Spec Kit
  installation, including Python 3.11+ and a working `specify` command.
- Supply-chain boundary: XPLAT-003 chooses source integrity, generated-payload,
  prerequisite-diagnostic, consumer-local verification, and public-claim
  controls before XPLAT-004 ships the runner.

## Entrypoint

- Canonical command: `speckit-pro-runner`
- Default payload-relative runner source path: `scripts/speckit_pro_runner.py`
- Resolution root: installed plugin payload/cache root
- Future launcher convention: XPLAT-004 may add a thin payload-local launcher
  path such as `scripts/speckit-pro-runner` if Claude Code or Codex needs a
  stable command target. Launcher logic must be dispatch-only and must not
  implement helper behavior in Bash or PowerShell.

## Invocation

The runner reads one versioned JSON request from stdin. CLI arguments are
reserved for command metadata only, such as `--help` and `--version`.
Helper-specific arguments are encoded in the JSON request, not argv.

```json
{
  "schema_version": "1.0",
  "request_id": "uuid-or-stable-id",
  "helper_id": "spec-index",
  "operation": "check",
  "mode": "read_only",
  "inputs": {}
}
```

## Input Validation and Error Responses

The runner validates the stdin envelope before helper dispatch. Validation
failures include malformed JSON, a non-object envelope, unsupported
`schema_version`, missing required fields, and invalid field types.

When the runner process can safely emit a response, input-validation failures
still write one JSON response to stdout and one or more line-delimited JSON
diagnostics to stderr. For malformed JSON, `request_id` and `helper_id` are
`null` because they cannot be read from the envelope. For schema-valid JSON
that is missing another required field, any already-available `request_id` and
`helper_id` values are echoed; unavailable identifiers are `null`.

Input-validation responses use:

- `status`: `input_error`
- process `exit_code`: `2`
- `legacy_exit_code`: `null`
- stderr diagnostic `severity`: `error`
- stderr diagnostic `source`: `runner`
- stderr diagnostic `code`: `invalid_json`, `invalid_envelope`,
  `unsupported_schema_version`, or `missing_required_field`

## Helper Dispatch

The request fields `helper_id`, `operation`, and `mode` identify a
runner-owned helper implementation resolved from the installed plugin
payload/cache root. The contract does not dispatch through repository authoring
checkout paths such as `speckit-pro/skills/...` or `dist/...` source paths.

XPLAT-004 may choose the concrete internal registry shape, but each dispatchable
helper must trace to XPLAT-001 row IDs when it replaces or adapts an active
runtime surface. Temporary compatibility adapters may map legacy surfaces to
runner helper IDs, operations, and modes; adapters still invoke the runner
through the installed payload entrypoint.

## Stdout Response

The runner emits one versioned JSON response on stdout.

Allowed `status` values are:

- `ok`
- `expected_failure`
- `input_error`
- `missing_prerequisite`
- `subprocess_failure`
- `internal_failure`

```json
{
  "schema_version": "1.0",
  "request_id": "uuid-or-stable-id",
  "helper_id": "spec-index",
  "status": "ok",
  "exit_code": 0,
  "legacy_exit_code": null,
  "data": {},
  "diagnostics": [],
  "runtime": {
    "runner_name": "speckit-pro-runner",
    "runner_version": "0.0.0-decision",
    "contract_version": "1.0",
    "selected_runtime_name": "python-stdlib-runner",
    "selected_runtime_version": "3.11+",
    "platform": "darwin",
    "architecture": "arm64",
    "plugin_root": {
      "kind": "plugin_relative",
      "value": "."
    },
    "source_vs_installed_context": "installed_plugin_cache",
    "capabilities": [],
    "prerequisites": []
  }
}
```

## Stderr Diagnostics

Stderr emits deterministic line-delimited JSON diagnostic events. Diagnostics
must not be mixed into stdout JSON.

```json
{"severity":"error","code":"missing_prerequisite","message":"Required executable not found","source":"runner","details":{"id":"git"}}
```

Diagnostic event fields:

| Field | Required | Notes |
|---|---|---|
| `severity` | Yes | `debug`, `info`, `warn`, or `error` |
| `code` | Yes | Stable machine-readable code |
| `message` | Yes | Human-readable diagnostic |
| `source` | Yes | Runner, helper, prerequisite, or subprocess source |
| `details` | Yes | Structured object; may be empty |

Required diagnostic codes for XPLAT-004 parity fixtures:

| Code | Required scenario |
|---|---|
| `invalid_json` | Stdin cannot be parsed as JSON |
| `invalid_envelope` | Parsed JSON is not a valid request object or has invalid field types |
| `unsupported_schema_version` | `schema_version` is present but unsupported |
| `missing_required_field` | A required request field is absent or empty |
| `missing_prerequisite` | Required selected runtime, `specify`, executable, or input prerequisite is unavailable |
| `subprocess_nonzero` | A subprocess exits nonzero and is not mapped to expected helper/domain failure |
| `subprocess_timeout` | A subprocess times out |
| `subprocess_stderr_only_failure` | A helper-defined stderr-only subprocess failure category is observed |
| `internal_failure` | Unexpected runner exception or unclassified internal failure |

## Exit-Code Map

| Code | Category | Contract Meaning |
|---:|---|---|
| 0 | `ok` | Successful runner/helper completion |
| 1 | `expected_failure` | Expected helper or domain failure |
| 2 | `input_error` | Invalid usage, malformed JSON, or schema error |
| 3 | `missing_prerequisite` | Required runtime, executable, or input prerequisite unavailable |
| 4 | `subprocess_failure` | Subprocess nonzero, timeout, or stderr-only failure category |
| 5 | `internal_failure` | Unexpected runner exception or unclassified internal failure |

`legacy_exit_code` preserves a documented helper-specific exit code only when
fixture parity requires it.

If the entrypoint process starts and detects that Python 3.11+, `specify`, or a
required executable is unavailable, it must emit `status:
missing_prerequisite`, a `missing_prerequisite` stderr diagnostic, and process
exit code `3`. A host-level failure to launch the entrypoint at all is outside
the runner response guarantee and must be recorded by XPLAT-004 as launcher
evidence, not as a successful runner invocation.

## Path Values

Path values are typed objects.

```json
{
  "kind": "repo_relative",
  "value": "specs/example/spec.md",
  "display": "specs/example/spec.md"
}
```

Allowed `kind` values:

- `repo_relative`
- `plugin_relative`
- `cache_relative`
- `absolute`
- `temp`

Reader-facing output should prefer repo/plugin-relative display paths when
available. Contract behavior must preserve paths with spaces and Windows,
macOS, and Linux separators.

## Subprocess Rules

Subprocess execution, when allowed by a helper operation, uses structured argv
arrays with shell disabled.

Required subprocess result fields:

- `argv`
- `cwd`
- `env`
- `stdout`
- `stderr`
- `exit_code`
- `timed_out`
- `missing_prerequisite`

Rules:

- No shell interpolation.
- No globbing through a shell.
- No redirection as a command contract primitive.
- No `.sh`, PowerShell-script, or `jq` fallback.
- cwd and env use explicit allowlists.
- Missing executables produce exit code `3`.
- Nonzero or timed-out subprocesses produce exit code `4` unless the helper
  explicitly maps the result to expected helper/domain failure.

## Runtime Info / Preflight Operation

The runner exposes a `runtime-info` or `preflight` operation returning:

- runner name and version
- contract version
- selected runtime name and version
- platform and architecture
- plugin root
- source-vs-installed context
- executable availability
- capabilities
- prerequisite records
- discovered Python executable path and version
- discovered `specify` executable path and version

The `plugin_root` and `source-vs-installed context` fields must make it clear
whether the runner is executing from an installed Claude cache, an installed
Codex cache, or a supplemental source/generator context. Installed-cache
reliability must be judged from installed-cache contexts, not from source-only
probes.

Prerequisite records include:

- `id`
- `required`
- `available`
- `version`
- `path`
- `remediation`
- `severity`

Required prerequisite records for the selected Python model:

- `python`: required, minimum version `3.11`, with the exact executable path
  used by the runner.
- `specify`: required, with the executable path and version/result returned by
  the official CLI.
- workflow-specific tools such as `git` or `gh`: required only when the helper
  operation needs them.

## Compatibility Adapter Records

Compatibility adapters are temporary migration records, not runtime candidates.

Required fields:

- `adapter_id`
- `legacy_surface`
- `xplat001_source_row`
- `runner_helper_id`
- `runner_operation`
- `runner_mode`
- `owner_bucket`
- `owner_spec`
- `removal_spec`
- `removal_condition`
- `evidence`

`adapter_id` uses an owner-first format such as:

```text
xplat-005-compat-<legacy-helper-or-surface-slug>
```

Adapter dispatch must use the installed runner entrypoint and must not require
the repository authoring checkout. `xplat001_source_row` preserves row-level
traceability to the inventory input that made the adapter necessary.

## XPLAT-004 Implementation Inputs

The XPLAT-004 handoff bundle derived from XPLAT-001 must include:

- XPLAT-001 row IDs and owner buckets.
- Active invocation modes.
- Runner helper IDs, operations, and modes.
- Adapter records where legacy compatibility is required.
- Fixture parity expectations tied to the relevant rows.
- Explicit exclusions for generated-payload cutover, public docs, repository-only
  helpers, and other non-XPLAT-004 work.

The bundle's integration target is the installed plugin payload/cache root for
Claude and Codex, not a source checkout.

## Fixture Parity Expectations

XPLAT-004 must be able to build fixture parity tests from these assertions:

| Fixture | Stdout response assertion | Stderr assertion | Process exit |
|---|---|---|---:|
| Successful helper invocation | One JSON response with `status: ok`, `exit_code: 0`, request identifiers echoed, and helper data in `data` | No `error` severity diagnostic required for success | 0 |
| Invalid JSON | One JSON response with `status: input_error`, `exit_code: 2`, `request_id: null`, `helper_id: null`, and `legacy_exit_code: null` | At least one JSON line with `severity: error`, `source: runner`, and `code: invalid_json` | 2 |
| Missing required request field | One JSON response with `status: input_error`, `exit_code: 2`, available identifiers echoed or `null`, and `legacy_exit_code: null` | At least one JSON line with `code: missing_required_field` and `details.field` naming the missing field | 2 |
| Path with spaces | The path value remains a single typed `Path Value`; no shell splitting or quote-stripping is observable | No diagnostic caused only by spaces in a path | Scenario-specific |
| Windows separators | The path value preserves Windows separators or records a normalized display path without assuming POSIX-only separators | No diagnostic caused only by Windows separators | Scenario-specific |
| Missing prerequisite | One JSON response with `status: missing_prerequisite`, `exit_code: 3`, and a prerequisite record when applicable | At least one JSON line with `code: missing_prerequisite` | 3 |
| Subprocess nonzero | One JSON response with `status: subprocess_failure`, `exit_code: 4`, captured subprocess stdout/stderr, and subprocess `exit_code` | At least one JSON line with `code: subprocess_nonzero` and the child exit code in `details` | 4 |
| Subprocess timeout | One JSON response with `status: subprocess_failure`, `exit_code: 4`, and `timed_out: true` in the subprocess result | At least one JSON line with `code: subprocess_timeout` | 4 |
| Stderr-only failure | One JSON response with `status: subprocess_failure`, `exit_code: 4`, and captured stderr unless the helper explicitly maps it to `expected_failure` | At least one JSON line with `code: subprocess_stderr_only_failure` | 4 unless mapped to 1 |
| Runtime-info or preflight | One JSON response with `status: ok`, `exit_code: 0`, and all required runtime-info fields | No `error` severity diagnostic required for success | 0 |
| Read-only legacy-helper comparison | Runner response preserves documented helper parity and sets `legacy_exit_code` only when the compared helper requires it | Diagnostics remain line-delimited JSON and do not corrupt stdout | Shared map code for the scenario |
