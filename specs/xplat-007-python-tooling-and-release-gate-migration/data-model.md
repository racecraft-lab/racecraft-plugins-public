# Data Model: Python Tooling and Release-Gate Migration

## Migrated Gate

Represents one active repo-local gate or helper group being moved from Bash to
the Python runner.

Fields:

- `gate_id`: stable kebab-case identifier.
- `gate_group`: one of `suite`, `layer`, `eval`, `payload`, `install`,
  `release`, `guard`, `helper`.
- `active_role`: one of `active_test_gate`, `active_eval_gate`,
  `active_payload_gate`, `active_install_verification`,
  `active_release_readiness`, `active_repo_helper`, `ci_dispatch_glue`.
- `prior_command_path`: repo-relative Bash script, workflow step, or command
  family being replaced.
- `python_operation`: runner operation name.
- `authoritative_request`: request fixture path or documented stdin envelope.
- `promotion_status`: `planned`, `bash_compared`, `python_authoritative`,
  `retired`, `deferred`, or `out_of_scope`.
- `xplat_008_boundary`: boolean marking surfaces that must not be cut over in
  XPLAT-007.

Relationships:

- Has one or more `Command Operation` records.
- Has zero or more `Parity Comparison` records while migrating.
- Has one `Promotion Record` before `python_authoritative`.

Validation rules:

- `python_authoritative` requires a promotion record and zero blocking
  active-path guard findings for the prior command path.
- `xplat_008_boundary=true` cannot have `promotion_status=python_authoritative`
  in XPLAT-007.

## Command Operation

Defines the runner request and response behavior for one migrated operation.

Fields:

- `operation`: stable runner operation name.
- `helper_id`: runner helper/gate id.
- `mode`: `read_only`, `dry_run`, or `apply`.
- `inputs`: JSON object accepted by the operation.
- `stdout_contract`: always one JSON runner response.
- `stderr_contract`: line-delimited runner diagnostics.
- `exit_contract`: status-mapped exit code.
- `artifact_outputs`: list of repo-relative fixture or evidence paths.
- `failure_classes`: stable diagnostic or expected-failure categories.

Relationships:

- Belongs to one `Migrated Gate`.
- Produces one `Release-Readiness Result`, `Payload Evidence`,
  `Install Verification Result`, or `Active-Path Guard Result` where applicable.

Validation rules:

- `apply` mode is allowed only for source-checkout test evidence, temporary
  fixtures, or explicitly scoped verification metadata.
- Operations must use argv-list subprocesses only when subprocesses are
  unavoidable.

## Parity Comparison

Records comparison between a Python operation and the prior Bash behavior while
Bash remains a temporary reference.

Fields:

- `comparison_id`: stable identifier.
- `gate_id`: associated migrated gate.
- `bash_reference`: repo-relative Bash path or workflow command being compared.
- `request_fixture`: Python runner request fixture.
- `comparison_mode`: `exact`, `json_semantic`, `semantic_markdown`,
  `artifact_hash`, or `command_plan`.
- `normalized_fields`: explicit allowlist of volatile fields.
- `legacy_exit_code`: integer or null.
- `runner_exit_code`: integer.
- `stdout_result`: `match`, `mismatch`, or `not_applicable`.
- `stderr_result`: `match`, `mismatch`, or `not_applicable`.
- `artifact_result`: `match`, `mismatch`, or `not_applicable`.

Validation rules:

- Exit code and stderr compare exactly unless the promotion record names a
  field-level normalization.
- Counts, booleans, statuses, diagnostic codes, and guard blocking decisions
  cannot be normalized away.

## Promotion Record

Review evidence proving the Python operation can replace the active gate.

Fields:

- `gate_id`
- `prior_bash_gate`
- `python_operation`
- `request_fixture`
- `fixture_ids`
- `bash_reference_ids`
- `failure_classes`
- `comparison_mode`
- `normalized_fields`
- `exit_code_result`
- `stream_result`
- `artifact_result`
- `active_path_guard_result`
- `bash_reference_retirement`: `removed_from_active_gate`,
  `inactive_parity_evidence`, `archive_provenance`, or `not_applicable`.
- `rollback`
- `promoted_at`

State transitions:

```text
planned -> bash_compared -> python_authoritative -> retired
planned -> deferred
planned -> out_of_scope
```

Validation rules:

- `python_authoritative` requires `exit_code_result=match`,
  `stream_result=match`, and `active_path_guard_result=pass`.
- `inactive_parity_evidence` requires the active-path guard to classify the
  retained Bash reference as nonblocking.

## Active-Path Guard Finding

Represents one shell-specific pattern found by the guard.

Fields:

- `path`: repo-relative path.
- `line`: one-based line number or null for file-level findings.
- `category`: `bash`, `script_file`, `jq`, `git_bash`, `wsl`,
  `powershell_helper`, `shell_parsing`, `shell_interpolation`,
  `shell_true`, `os_system`, or `command_string_subprocess`.
- `pattern`: matched token or detection code.
- `reason`: reviewer-facing explanation.
- `active_role`: invocation role.
- `classification`: `blocking_active_gate`, `ci_dispatch_glue`,
  `temporary_parity_evidence`, `archive_provenance`,
  `consumer_spec_kit_helper`, `generated_payload_mirror`,
  `xplat_008_cutover_surface`, or `docs_out_of_scope`.
- `remediation`: required change for blocking findings.

Validation rules:

- `blocking_active_gate` findings make the guard result
  `status=expected_failure` and exit `1`.
- CI dispatch glue is nonblocking only when it directly invokes Python gates and
  contains no plugin validation, packaging, install, release, loop, `jq`, or
  parsing logic.

## Payload Evidence

Represents XPLAT-007 test payload output and fingerprints.

Fields:

- `evidence_id`
- `payload_surface`: `claude_test` or `codex_test`.
- `mode`: `read_only`, `dry_run`, or `apply`.
- `input_root`
- `output_root`
- `files`: list of `{path, sha256, byte_count}` records.
- `file_tree_hash`
- `release_payload_cutover`: must be `false`.
- `status`: `ok`, `expected_failure`, or `input_error`.

Validation rules:

- `release_payload_cutover` must remain `false`.
- Output roots must be fixture or temporary roots, not generated release payload
  selection paths.

## Release-Readiness Result

Aggregates release-blocking checks after migration.

Fields:

- `status`: `pass`, `fail`, or `input_error`.
- `checks`: array of check records with `check_id`, `status`, `evidence`, and
  `blocking`.
- `blocking_count`
- `promotion_record_count`
- `test_payload_evidence_ids`
- `install_verification_ids`
- `active_path_guard_summary`
- `xplat_008_handoff_items`

Validation rules:

- `status=pass` requires zero blocking checks, zero active-path guard blockers,
  and a promotion record for each promoted active gate.
- Release-readiness cannot claim native installed UAT or generated release
  payload cutover in XPLAT-007.

## Install Verification Result

Fixture-bound proof for local refresh and install verification.

Fields:

- `verification_id`
- `status`: `complete`, `safe_repair`, `blocked`, or `input_error`.
- `install_root`
- `fake_home`: boolean.
- `stubbed_cli`: boolean.
- `bundled_agent_count`
- `expected_files`
- `missing_files`
- `checksum_mismatches`
- `command_plans`
- `safe_repairs`
- `unsafe_manual_remediations`
- `native_uat_claimed`: must be `false`.

Validation rules:

- Real `HOME` writes are refused.
- `native_uat_claimed` must remain `false`.
- Safe repair can be planned or applied only in fixture/fake-home roots.

## XPLAT-008 Handoff Item

Explicit deferred work for the final cutover spec.

Fields:

- `item_id`
- `category`: `active_invocation_cutover`, `generated_release_payload`,
  `public_docs`, `release_notes`, `installed_cache_uat`, `native_platform_uat`,
  `update`, `autoheal`, or `public_release_readiness`.
- `deferred_reason`
- `source_evidence`
- `required_before_public_claim`: boolean.
- `owner_spec`: must be `XPLAT-008`.

Validation rules:

- Every accidental XPLAT-008 surface found during implementation becomes either
  a reverted change or a handoff item.
- Release-readiness output includes all handoff items relevant to final public
  release blocking.
