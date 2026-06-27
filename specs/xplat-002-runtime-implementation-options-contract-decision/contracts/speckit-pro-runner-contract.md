# Contract: `speckit-pro-runner`

This contract is the XPLAT-002 handoff shape for XPLAT-004. It defines the
command interface that the selected runtime must implement after XPLAT-002
chooses the runtime. It does not implement the runner.

## Entrypoint

- Canonical command: `speckit-pro-runner`
- Default payload-relative path: `scripts/speckit-pro-runner`
- Resolution root: installed plugin payload/cache root
- Future path convention: XPLAT-004 may deliberately create a `bin/` convention,
  but this contract does not assume one.

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

## Stdout Response

The runner emits one versioned JSON response on stdout.

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
    "selected_runtime_name": "selected-at-xplat-002-implementation",
    "selected_runtime_version": "selected-at-xplat-002-implementation",
    "platform": "darwin",
    "architecture": "arm64",
    "plugin_root": {
      "kind": "plugin_relative",
      "value": "."
    },
    "source_vs_installed_context": "source",
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
- No `.sh` or `jq` fallback.
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

Prerequisite records include:

- `id`
- `required`
- `available`
- `version`
- `path`
- `remediation`
- `severity`

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

## Fixture Parity Expectations

XPLAT-004 must be able to build fixture parity tests for:

1. Successful helper invocation.
2. Invalid JSON.
3. Missing required request field.
4. Path with spaces.
5. Windows separators.
6. Missing prerequisite.
7. Subprocess nonzero.
8. Stderr-only failure.
9. Runtime-info or preflight.
10. At least one read-only legacy-helper versus runner comparison.
