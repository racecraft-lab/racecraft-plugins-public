# Data Model: XPLAT-005 Read-Only Helper Port

## Helper Registry Entry

Represents one helper id that the runner can dispatch.

**Fields**

- `helper_id`: stable helper id, for example `check-prerequisites` or `validate-pr-packet-read-only`
- `slice`: `1` or `2`
- `operation`: runner operation string
- `module_target`: Python module and callable target
- `mode`: `read_only`
- `input_contract`: accepted input shape reference
- `promotion_status`: `python_authoritative`, `bash_reference_only`, or `out_of_scope`
- `bash_reference_path`: source-checkout Bash script path, or `null` for golden-only registry cases
- `writes_state`: boolean, always `false` for XPLAT-005 in-scope entries

**Validation Rules**

- In-scope entries must use `mode=read_only`.
- In-scope entries must not name mutation operations.
- `python_authoritative` entries require fixture parity and Bash-reference comparison unless the helper is a permitted golden-only runner/safety case.

## Helper Invocation Request

The runner input envelope for one helper invocation.

**Fields**

- `schema_version`: `1.0`
- `request_id`: caller-provided correlation id
- `helper_id`: registered helper id
- `operation`: operation name accepted by the registry entry
- `mode`: `read_only`
- `inputs`: helper-specific object

**Validation Rules**

- Requests with unknown helper ids or mutation modes fail before helper execution.
- `inputs` may contain repo-relative paths, feature-directory paths, fixture ids, or helper options.
- Paths must be handled through runner typed-path primitives, not shell parsing.

## Helper Invocation Result

The normalized result captured by tests for Python and Bash-reference runs.

**Fields**

- `helper_id`
- `fixture_id`
- `stdout_json`: parsed JSON object or array when stdout is JSON
- `stderr`: text diagnostics
- `exit_code`: integer process exit code
- `diagnostics`: optional structured diagnostics from the runner envelope
- `normalized_fields`: list of field paths changed before comparison

**Validation Rules**

- JSON stdout is compared semantically.
- Stderr diagnostics and exit codes are compared exactly unless a helper-specific normalization rule allows otherwise.
- Missing or malformed JSON must preserve the current failure class.

## Parity Fixture

A deterministic input/output case for one helper.

**Fields**

- `fixture_id`
- `helper_id`
- `slice`
- `description`
- `input_kind`: `repo_fixture`, `synthetic_path`, `malformed_request`, or `normalization_unit`
- `request`
- `expected_stdout_json`
- `expected_stderr`
- `expected_exit_code`
- `failure_class`: one of `invalid_input`, `missing_input`, `malformed_json`, `missing_file`, `unsupported_path`, `missing_prerequisite`, `validation_failure`, `subprocess_failure`, `preflight_failure`, or `none`
- `expected_stdout_schema`: schema reference required when the helper emits machine-readable failure output
- `expected_remediation`: deterministic remediation text or runner diagnostic remediation actions when diagnostics are emitted
- `normalization_rule_ids`

**Validation Rules**

- Every promoted helper must have at least one accepted fixture and one fixture for each applicable rejected-input failure class unless the helper has no rejected state.
- Helpers that emit machine-readable rejected-input output must define the rejected stdout JSON schema.
- Diagnostics with remediation must assert deterministic remediation text or remediation actions.
- Golden-only fixtures are limited to runner envelope/registry dispatch, typed-path/subprocess safety, malformed request cases, synthetic Windows/no-Bash/path fixtures, and normalization unit tests.

## Bash Reference Comparison

Evidence that a Python helper matches the current source-checkout Bash helper.

**Fields**

- `comparison_id`
- `helper_id`
- `bash_script_path`
- `fixture_id`
- `bash_args`
- `python_request`
- `stdout_comparison`: `semantic_json`
- `stderr_comparison`: `exact` or listed normalization rule
- `exit_code_comparison`: `exact`
- `subprocess_policy`: `argv_only`
- `bounded_input`: boolean indicating the harness avoids unbounded subprocess input
- `result`: `pass` or `fail`

**Validation Rules**

- Bash-reference comparisons run only from a source checkout.
- Bash comparison is required before a Bash-backed helper can be promoted.
- Bash-reference comparison harnesses must not use `shell=True`, shell-command strings, `os.system`, shell interpolation, or unbounded subprocess input.
- Subprocess execution must use explicit argv sequences and capture stdout/stderr.
- Failed comparisons must identify the field, stream, or exit-code difference.

## Failure Class Mapping

Defines exact rejected-input semantics per helper.

**Fields**

- `helper_id`
- `failure_class`
- `expected_status`
- `expected_exit_code`
- `stdout_schema_ref`
- `stderr_required`
- `diagnostic_code`
- `remediation_required`
- `fixture_ids`

**Validation Rules**

- Every applicable rejected-input fixture must map to a failure class.
- Missing-input, invalid-input, malformed-JSON, missing-file, unsupported-path, prerequisite-failure, validation-failure, subprocess-failure, and preflight-failure classes must not collapse into a generic error unless the Bash reference already exposes only one class.
- Exit codes and diagnostic codes must match the Bash reference or documented runner envelope status.

## Trusted Path Input

Represents a filesystem input after trust-boundary resolution.

**Fields**

- `kind`: `repo_relative`, `plugin_relative`, or `absolute_fixture`
- `raw_value`
- `resolved_value`
- `trust_boundary`: repo root or plugin root
- `accepted`
- `rejection_reason`

**Validation Rules**

- Relative components and symlinks must be resolved before reading files.
- Resolved paths must stay inside the declared repo or plugin trust boundary.
- Traversal and symlink escapes must be rejected before helper logic consumes the file.

## Normalization Rule

Documents a deterministic transformation applied before comparison.

**Fields**

- `rule_id`
- `field_path`
- `reason`
- `before_kind`
- `after_value`
- `allowed_for_helpers`

**Allowed Reasons**

- repo/worktree absolute path converted to repo-relative path
- temp path converted to stable placeholder
- executable path or version when not fixture-controlled
- platform, architecture, or runtime identity field
- branch/worktree metadata when live git state is intentionally used

**Validation Rules**

- Counts, booleans, statuses, route/status enums, diagnostic codes, public text, and exit codes must not be normalized unless a helper-specific rule explicitly names the field.

## Promotion Record

The per-helper evidence row required by the spec and PR review packet.

**Fields**

- `helper_id`
- `slice`
- `bash_script_path`
- `runner_operation`
- `runner_module`
- `fixture_ids`
- `bash_comparison_ids`
- `normalized_fields`
- `status`: `python_authoritative`, `bash_reference_only`, or `out_of_scope`
- `authoritative_test_command`
- `deferred_follow_up`

**Validation Rules**

- `python_authoritative` requires fixture ids and either Bash comparison ids or an allowed golden-only reason.
- `out_of_scope` requires a named deferred follow-up, such as XPLAT-006 or XPLAT-007.
- No helper may be left with an ambiguous status.

## Source-Checkout Smoke Evidence

Local macOS evidence for the accepted runner path.

**Fields**

- `request_id`: `xplat-005-smoke`
- `command`
- `expected_status`: `ok`
- `expected_context`: `source_checkout`
- `claims_supported`
- `claims_not_supported`

**Validation Rules**

- The smoke proves only local source-checkout runner launch and runtime-info response.
- It does not prove installed-cache launch, generated payload propagation, active Claude/Codex invocation, helper parity, mutation-helper safety, or full native Windows/macOS/Linux support.

## Scope Audit Record

Evidence that XPLAT-005 did not perform active cutover or mutation-helper work.

**Fields**

- `checked_paths`
- `disallowed_path_matches`
- `disallowed_helper_modes`
- `result`
- `notes`

**Validation Rules**

- Result must be `pass` only when active Claude Code/Codex skills, hooks, generated payloads, installer behavior, marketplace/public docs, PR emission, split state, restack, relocation, install repair, autoheal, and mutation-helper ports are absent from the implementation diff.
