# Data Model: PRSG-009 multi-PR emission

## Layer Plan

Authoritative PRSG-008 output consumed by emission.

Fields:
- `source_path`: path to the layer-plan JSON or captured output.
- `source_sha`: hash of the layer-plan input when available.
- `layers[]`: ordered slice definitions.
- `generated_at`: timestamp from the planner or capture step.

Rules:
- Emission must preserve layer order.
- Missing, unreadable, empty, or unparsable input blocks emission.
- PRSG-009 does not add or override layer membership.

## Slice Record

One durable state entry for one emitted or pending slice.

Fields:
- `slice_id`: stable slug from the PRSG-008 increment identifier.
- `review_order`: one-based order from the layer plan.
- `expected_branch`: `<feature-branch>/<NN>-<slice-id>`.
- `expected_base_branch`: integration base for the first slice, previous slice
  branch for later slices.
- `head_sha`: current slice branch commit after branch creation or verification.
- `declared_files[]`: planned file operations from the layer plan.
- `declared_scoped_tests[]`: scoped commands selected from project commands.
- `scoped_verification`: verification command records and evidence path.
- `pr`: PR number, URL, refs, state, head SHA, and merge SHA when available.
- `status`: `pending`, `branch_created`, `verified`, `pr_opened`, `merged`,
  `closed`, or `failed`.
- `last_error`: bounded failure details for the last failed operation.

Rules:
- A slice cannot advance past `verified` unless scoped verification succeeds.
- A failed slice must stop before PR creation.
- Existing PRs are reconciled by expected head and base before new creation.

## Multi-PR Emission State

Top-level `multi_pr_emission` object in
`docs/ai/specs/.process/autopilot-state.json`.

Fields:
- `schema_version`: state schema version.
- `status`: overall state such as `pending`, `emitting`, `blocked`, or
  `complete`.
- `source_layer_plan`: layer-plan path and identity.
- `base_branch`: integration base branch.
- `base_sha`: integration base SHA before emission.
- `next_slice_id`: next pending slice to attempt.
- `reconciled_at`: timestamp for the last branch/PR reconciliation.
- `slices[]`: ordered slice records.
- `failed_slice`: optional failed scoped-verification record.

Rules:
- State is written after branch/base/head metadata, after verification evidence,
  and after PR reconciliation.
- `next_slice_id` advances only after PRS rows, MOC regeneration, and workflow
  evidence are persisted.
- Full logs are stored by path, not inline.

## Slice Packet

Bounded JSON input passed to `generate-pr-body.sh --slice-packet`.

Fields:
- `slice_id`
- `review_order`
- `total_slices`
- `base_branch`
- `head_branch`
- `declared_files[]`
- `declared_tests[]`
- `scoped_verification.commands[]`
- `full_verification_evidence`
- `traceability[]`
- `restack_note`
- `prs_row`

Rules:
- The packet is optional; existing positional PR body invocation remains valid.
- Packet values should be copied from durable state/evidence, not recomputed.

## PRS Manifest v2

Reviewer-facing manifest at `specs/<branch>/.process/prs.json`.

Fields:
- `schemaVersion`: `2`
- `records[]`: bounded PR rows.
- Row fields: `review_order`, `slice_id`, `layer`, `branch`, `base_branch`,
  `pr_number`, `pr_url`, `declared_files`, `verification_evidence`, `status`,
  `head_sha`, and optional `merged_sha`.

Rules:
- Schema v1 rendering remains supported.
- Open rows display `head_sha`.
- Merged rows prefer `merged_sha` when present.
- Open PR head commits must not be written into `merged_sha`.

## Scoped Verification Command

One command evidence entry for a slice.

Fields:
- `command`
- `gate_type`
- `reason`
- `required`
- `evidence_path`
- `exit_status`
- `started_at`
- `finished_at`
- `stdout_tail`
- `stderr_tail`

Rules:
- Required command failure blocks PR creation for that slice.
- Full stdout/stderr logs live under `.process/emission/<slice_id>/`.

## Restack Operation

Dry-run or applied operation for remaining open slice branches after a lower
stack PR is squash-merged.

Fields:
- `slice_id`
- `branch`
- `old_base`
- `new_base`
- `action`
- `applied`
- `result`

Rules:
- Dry-run is default.
- Mutation requires `--apply`.
- Declared file-operation scope must not change during restack.
