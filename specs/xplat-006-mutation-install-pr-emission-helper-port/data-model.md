# Data Model: XPLAT-006 Mutation, Install, and PR-Emission Helper Port

## Mutation Helper Request

Represents a runner request for a mutation-capable helper.

Fields:
- `helper_id`: Stable helper identifier.
- `operation`: Helper-specific operation such as `check`, `install`, `repair`,
  `generate`, `emit`, `restack`, `migrate`, or `relocate`.
- `mode`: `dry_run` or `apply`.
- `inputs`: Helper-specific JSON object.
- `boundary_context`: Declared repo, plugin, fake-home, fake-cache, temp, CLI,
  and network/GitHub boundaries.
- `approval_evidence`: Optional live mutation approval evidence.
- `request_id`: Optional deterministic id for fixture and PR packet traceability.

Validation rules:
- Reject unsupported helper/mode/operation combinations before helper execution.
- Require explicit `apply` mode before mutation.
- Require approval evidence for live repo, user-local, plugin-cache, network, or
  GitHub mutation.
- Reject path inputs that escape declared boundaries.

## Live Mutation Approval Evidence

Auditable approval object for exceptional live mutation.

Fields:
- `approval_id`
- `approver`
- `timestamp`
- `channel`
- `dry_run_result_id`
- `dry_run_hash`
- `allowed_boundaries`
- `allowed_operations`
- `expires_at`

Validation rules:
- Boolean flags or mode names alone are not valid approval.
- Approval must reference prior dry-run output and allowed boundaries.
- Expired approval cannot authorize apply.

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
- `data.mutation.manual_remediation_actions`

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
- `kind`: `write`, `delete`, `copy`, `command`, `pr_action`, `repair`,
  `migration`, `relocation`, or `generated_output`.
- `target`
- `boundary`
- `mode`
- `content_sha256`
- `line_ending_policy`
- `expected_result`

Validation rules:
- File targets must resolve inside declared boundaries.
- Generated JSON and Markdown use UTF-8 LF with one final newline.
- Command operations use argv-list subprocess representation.

## Applied Operation

Apply-mode operation result.

Fields:
- `operation_id`
- `kind`
- `target`
- `boundary`
- `mode`
- `result`
- `failure_class`
- `content_sha256`
- `line_ending_policy`
- `rollback_note`
- `manual_remediation`

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
- `required_approval`
- `remediation_text`
- `preserved_unrelated_files`

Validation rules:
- Doctor/preflight is read-only by default.
- Repair is a separate apply-mode operation.
- Safe repair is limited to fake or explicitly approved declared boundaries.

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
