# Data Model: PRSG-009 multi-PR emission

## Layer Plan

Authoritative PRSG-008 output consumed by emission.

Fields:
- `source_path`: path to the layer-plan JSON or captured output.
- `source_sha`: hash of the layer-plan input when available.
- `tool`: must be `plan-layers`.
- `contract_version`: PRSG-008 output contract version.
- `status`: `ok`, `invalid_plan`, or `input_error`.
- `increments[]`: ordered PRSG-008 increment definitions.
- `warnings[]`, `errors[]`, and `summary`: planner diagnostics and counts.
- `generated_at`: timestamp from the planner or capture step.

Consumed increment fields:
- `id`: source for the PRSG-009 `slice_id` slug.
- `order`: source for one-based review order after preserving planner order.
- `depends_on`: stack dependency evidence.
- `files[]`: declared file-operation scope.
- `tests[]`: declared scoped-test candidates.
- `advisory_size`: review-scope context copied into slice evidence.

Rules:
- Emission must preserve layer order.
- Missing, unreadable, empty, or unparsable input blocks emission.
- `status` values other than `ok` block before branch creation.
- `status: ok` with warnings may proceed, but warnings are copied to emission
  evidence and affected slice packets without changing membership.
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
- `known_gaps[]`
- `warnings[]`
- `restack_note`
- `prs_row`

Rules:
- The packet is optional; existing positional PR body invocation remains valid.
- Packet values should be copied from durable state/evidence, not recomputed.
- Packet validation happens before the PR body output file is created or
  overwritten. Invalid packets exit 2 with a deterministic stderr line beginning
  `generate-pr-body.sh: invalid slice packet:`.
- Valid packet rendering adds stable sections named `Slice summary`, `Review
  order`, `Scope`, `Verification`, `Traceability`, `Restack or rollback`,
  `Known gaps`, and `Full regression evidence`.

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
- Schema v2 renders as a link-free Markdown table with columns `Order`, `Slice`,
  `PR`, `Status`, `Branch`, `Base`, `SHA`, `Scope`, and `Verification`.
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
- Process exit codes are fixed: `0` success, `1` conflicts, `2` input error,
  `3` dirty worktree, and `4` `git`/`gh` failure.
- JSON stdout `status` and `exit_code` must match the process outcome.
- Failure diagnostics go to stderr in `restack.sh: <status>: <message>` format
  with no timestamps, colors, or host-specific absolute paths except paths
  supplied by the operator.
- Declared file-operation scope must not change during restack.
