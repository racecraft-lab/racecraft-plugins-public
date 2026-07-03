# Data Model: XPLAT-006 Mutation, Install, and PR-Emission Helper Port

## Mutation Helper Request

Represents a runner request for a mutation-capable helper.

Fields:
- `helper_id`: Stable helper identifier.
- `operation`: Helper-specific operation such as `check`, `install`, `repair`,
  `generate`, `emit`, `restack`, `migrate`, or `relocate`.
- `schema_version`: Runner request contract version, currently `1.0`.
- `mode`: `read_only`, `dry_run`, or `apply`.
- `inputs`: Helper-specific JSON object.
- `request_id`: Optional deterministic id for fixture and PR packet traceability.

Validation rules:
- Reject unsupported helper/mode/operation combinations before helper execution.
- Require explicit `apply` mode before mutation.
- Reject extra top-level request fields.
- Reject path inputs that escape the repository trust boundary.
- Refuse apply mode unless `git status --porcelain` proves the worktree is clean.
- Trust `fake_home: true` only inside the committed fixture fake-home boundary.

## Deferred Live Mutation Boundary

The XPLAT-006 runner does not accept a live mutation approval object yet.
Command-plan helpers remain dry-run only for live GitHub/PR actions until the
active cutover work lands.

Fields:
- `data.mutation.planned_operations`: Command plans captured as argv lists.
- `data.mutation.live_mutation`: Always `false` in XPLAT-006.
- `diagnostics[].code`: `deferred_live_mutation` when apply mode is requested
  for command-plan helpers.

Validation rules:
- `live_mutation_approved: true` cannot turn command-plan apply into success.
- Live PR creation, restack, and GitHub mutation stay outside the runner until
  XPLAT-007/XPLAT-008 cutover gates define the approval contract.

## Mutation Helper Result

Runner output that preserves the top-level envelope and stores mutation details
under `data.mutation`.

Fields:
- Top-level envelope: `schema_version`, `status`, `exit_code`,
  `legacy_exit_code`, `diagnostics`, `data`.
- `data.mutation.mode`
- `data.mutation.mutation_status`
- `data.mutation.planned_operations`
- `data.mutation.applied_operations`
- `data.mutation.skipped_operations`
- `data.mutation.planned_paths`
- `data.mutation.touched_paths`
- `data.mutation.dirty_worktree`
- `data.mutation.failure_operation`
- `data.mutation.rollback_notes`
- `data.mutation.manual_remediation`
- `data.mutation.live_mutation`

Validation rules:
- Dry-run results contain planned operations and no touched paths.
- Apply no-op returns success with no applied operations or touched paths.
- Partial failure identifies the failed operation and remediation.
- Existing stdout JSON schemas, stderr diagnostics, remediation text, and exit
  codes are preserved per helper.

## Planned Operation

Deterministic dry-run operation record.

Fields:
- `operation_id`
- `kind`: `write_file` or `command_plan`.
- `target`: Present for `write_file`.
- `command`: Present for `command_plan` as an argv-list representation.

Validation rules:
- File targets must resolve inside the repository trust boundary.
- Generated JSON and Markdown use UTF-8 LF with one final newline.
- Command operations use argv-list subprocess representation.

## Applied Operation

Apply-mode operation result.

Fields:
- `operation_id`
- `kind`
- `target`: Present for `write_file`.
- `command`: Present for `command_plan`.

Validation rules:
- Apply records every operation attempted.
- Failed operations include a deterministic failure class.
- Multi-operation helpers report partial failure rather than global rollback
  unless the helper already provides a narrower rollback behavior.

## Install Inventory Manifest

Committed source truth for install completeness checks.

Fields:
- `schema_version`
- `generated_at`
- `plugin_version`
- `marketplace_version`
- `claude_agents`
- `codex_agents`
- `runner_files`
- `generated_payload_files`
- `metadata_files`
- `checksums`

Validation rules:
- Inventory is read from the source checkout.
- Doctor/preflight reports malformed inventory and checksum mismatch
  deterministically.
- Generated inventory updates are reviewed before preflight readiness is claimed.

## Safe Repair Record

Doctor/preflight classification and repair plan.

Fields:
- `target_id`
- `target_kind`
- `status`: `complete`, `safe_repair`, `unsafe_manual_remediation`, `blocked`,
  `stale_release`, `downgrade_refusal`, `malformed_inventory`, or
  `source_truth_checksum_mismatch`.
- `planned_repair_operations`
- `deferred_live_mutation`
- `remediation_text`
- `preserved_unrelated_files`

Validation rules:
- Doctor/preflight is read-only by default.
- Repair is a separate apply-mode operation.
- Safe repair is limited to fixture fake-home boundaries in XPLAT-006.

## Parity Fixture

Golden fixture proving helper behavior.

Fields:
- `fixture_id`
- `helper_id`
- `operation`
- `mode`
- `input_path`
- `expected_stdout_path`
- `expected_stderr_path`
- `expected_exit_code`
- `environment`
- `normalization`

Validation rules:
- Covers success, no-op, dry-run, apply, invalid input, missing prerequisite,
  malformed JSON, dirty worktree, path escape, write failure, and partial
  failure where applicable.
- Uses fake state by default.

## Bash Reference Comparison

Source-checkout parity comparison between current Bash helper behavior and the
Python runner helper.

Fields:
- `comparison_id`
- `helper_id`
- `bash_argv`
- `python_argv`
- `fixture_ids`
- `normalized_fields`
- `accepted`
- `notes`

Validation rules:
- Uses explicit argv lists and captured stdout/stderr.
- Does not require network or real user-home/GitHub mutation.

## Helper Promotion Record

Reviewer-facing record that determines whether Python behavior is authoritative.

Fields:
- `helper_id`
- `operation`
- `mode`
- `status`: `golden_only`, `bash_compared`, `python_authoritative`, `deferred`,
  or `out_of_scope`.
- `fixture_ids`
- `bash_comparison_ids`
- `normalized_fields`
- `python_test_command`
- `rollback_guidance`
- `deferred_follow_up`

Validation rules:
- Python tests become authoritative only after accepted fixture parity and
  Bash-reference comparison for Bash-backed helpers.
- Deferred and out-of-scope helpers name the follow-up owner.

## Scope Audit Record

Verification artifact proving forbidden cutover surfaces did not change, while
allowed phase-coverage hardening source/mirror changes are identified
separately.

Fields:
- `diff_base`
- `changed_files`
- `forbidden_surface_matches`
- `status`
- `evidence_commands`

Validation rules:
- Fails if active Claude/Codex invocation behavior, hooks, generated-payload
  selection/cutover, install guidance, public docs claims, repo-local release
  gates, or native UAT artifacts change in XPLAT-006.
- Allows only the autopilot phase-coverage hardening source and generated mirror
  as explicit skill/payload changes.

## Autopilot Phase Coverage Report

Validator output proving workflow and durable state preserve all canonical
autopilot phases and post-implementation items.

Fields:
- `status`
- `workflow_file`
- `state_file`
- `plan_step_count`
- `missing_workflow_sections`
- `missing_workflow_tokens`
- `missing_workflow_post_items`
- `missing_state_prefixes`
- `missing_state_post_items`
- `duplicate_state_steps`
- `state_order_errors`
- `in_progress_errors`

Validation rules:
- Missing Phase 6.5 fails.
- Missing Post items fail.
- Collapsed later phases fail.
- Malformed `autopilot-state.json` returns deterministic `input_error`.
- More than one `in_progress` item fails.
