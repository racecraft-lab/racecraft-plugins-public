# Data Model: Optional gh-stack stack manager integration

## Stack Manager Decision

Represents the pre-mutation selection of either `gh-stack`, explicit `gh`, or blocked recovery.

Fields:

- `schema_version`: constant `stack-manager-decision.v1`
- `phase`: `emission` or `restack`
- `operation`: `detect`, `link`, `sync`, or `restack`
- `selected_manager`: `gh-stack`, `explicit-gh`, or `blocked`
- `reason`: concise operator-facing reason for the selected manager
- `fallback_reason`: reason fallback was selected, or `null`
- `fallback_allowed`: boolean; false after partial or unknown `gh-stack` mutation
- `mutation_boundary`: first planned topology-changing operation, or `none`
- `gh_stack`: availability, version, invocation, support, and repository compatibility evidence
- `read_only_proof`: command evidence and parse status for `gh stack view --json`
- `topology_compatibility`: comparison between PRS/marker topology and observed stack topology
- `command_plan`: ordered argv operations
- `topology`: pre-mutation and post-mutation PR/branch relationships when available
- `recovery`: recoverable block state when selected manager is `blocked`

Validation:

- `selected_manager=gh-stack` requires available/supported/compatible/read-only-proof success and at least one command plan item.
- `selected_manager=explicit-gh` requires `fallback_allowed=true` and a non-empty `fallback_reason`.
- `selected_manager=blocked` requires `fallback_allowed=false` and recoverable evidence.

## gh-stack Evidence

Captures deterministic local and project capability evidence.

Fields:

- `available`: whether `gh stack` can be invoked through GitHub CLI
- `extension_owner`: expected `github`
- `extension_name`: expected `gh-stack`
- `version`: parsed version string such as `0.0.5`
- `version_supported`: boolean from exact capability matrix
- `invocation`: argv used for version/help/read-only checks
- `repo_enabled`: true only when read-only proof confirms repository support
- `support_status`: `supported`, `missing`, `unsupported_version`, `private_preview_unavailable`, `ambiguous`, `read_only_proof_failed`, or `topology_incompatible`

## Read-Only Proof

The pre-mutation proof that `gh-stack` can inspect the current stack safely.

Fields:

- `argv`: `["gh", "stack", "view", "--json"]`
- `exit_status`: command exit status
- `stdout_tail`: bounded output tail
- `stderr_tail`: bounded error tail
- `parsed`: whether stdout parsed as JSON
- `matched_expected_topology`: whether observed order/base topology matches PRS/marker expectations
- `evidence_path`: persisted proof path when saved

## Command Plan

An ordered list of executable argv arrays. This is the only executable representation.

Fields:

- `id`: stable operation id
- `action`: `detect`, `create_pr`, `edit_pr`, `link_stack`, `sync_stack`, `rebase_upstack`, `retarget_base`, or `block`
- `manager`: `gh-stack` or `explicit-gh`
- `argv`: non-empty string array
- `mutates`: boolean
- `mutation_boundary`: boolean
- `slice_id`: related slice or marker id when applicable
- `review_order`: marker/PRS review order when applicable
- `preconditions`: packet, topology, and retry reconciliation checks
- `reason`: why the operation is planned

Validation:

- No command plan item may store joined shell text as executable state.
- Branch names and PR body paths must already be validated before appearing in argv.
- The first `gh-stack` mutating item is the no-fallback boundary.

## Topology Evidence

Represents branch and PR ordering before and after stack-manager operations.

Fields:

- `source`: `prs-v2`, `pr-marker-plan`, `gh-stack-view-json`, or `gh-pr-view`
- `records`: ordered records containing `review_order`, `slice_id`, `branch`, `base_branch`, `pr_number`, `pr_url`, `head_sha`, and `status`
- `marker_order`: ordered marker IDs when marker-aware emission is active
- `matches_expected`: boolean
- `mismatch_reason`: reason when topology is incompatible

Validation:

- PRSG-013 marker order must be monotonically increasing by `review_order`.
- Branch names and base branches must match PRS/marker records before supported-path mutation.

## Command Execution Evidence

Captures actual command execution without unbounded logs.

Fields:

- `command_id`: command plan item id
- `argv`: executed argv array
- `started_at`: timestamp
- `finished_at`: timestamp
- `exit_status`: integer
- `stdout_tail`: bounded to 120 lines and 16 KiB
- `stderr_tail`: bounded to 120 lines and 16 KiB
- `side_effect_class`: `none`, `planned_mutation`, `partial_mutation`, or `partial_mutation_unknown`
- `evidence_path`: persisted command evidence path

## Recoverable Block State

Emitted when `gh-stack` may have partially mutated topology and fallback would risk duplicate PRs or manager mixing.

Fields:

- `status`: `blocked`
- `reason`: operator-facing block reason
- `fallback_allowed`: false
- `selected_manager`: `gh-stack`
- `failed_operation`: command plan item and execution evidence
- `mutation_boundary`: attempted boundary operation
- `pre_mutation_topology`: topology snapshot before mutation
- `observed_post_failure_topology`: topology snapshot when available
- `prior_successful_prs`: PR numbers/URLs already reconciled
- `next_resume_boundary`: slice/marker/branch to inspect before retry
- `retry_policy`: same-manager reconciliation or operator repair instructions
- `evidence_paths`: state, command log, PRS manifest, and workflow evidence paths
