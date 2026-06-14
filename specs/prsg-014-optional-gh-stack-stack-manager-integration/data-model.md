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
- `evidence_path`: repo-relative path to the persisted decision record when saved

Validation:

- `selected_manager=gh-stack` requires available/supported/compatible/read-only-proof success and at least one command plan item.
- `selected_manager=explicit-gh` requires `fallback_allowed=true`, `gh_stack.supported=false`, a non-empty `gh_stack.reason`, a non-empty `fallback_reason`, and at least one explicit `gh` command plan item.
- `selected_manager=blocked` requires `fallback_allowed=false`, `mutation_boundary.status` of `partial_mutation` or `partial_mutation_unknown`, and recoverable evidence with the failed `gh-stack` operation and resume boundary.

## gh-stack Evidence

Captures deterministic local and project capability evidence.

Fields:

- `available`: whether `gh stack` can be invoked through GitHub CLI
- `supported`: true only when availability, version support, repository enablement, read-only proof, and topology compatibility all pass for the requested operation
- `reason`: concise reason for the `supported` value, suitable for detection output and reviewer evidence
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
- `evidence_path`: repo-relative persisted proof path when saved

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
- Every argv element must be non-empty, bounded, and free of NUL, newline, carriage return, and other control characters before command capture.
- The executable position and command shape must be allowlisted before command capture. Runtime command plans are limited to canonical `gh stack`, explicit `gh pr`, scoped `git`, and repo-local validator argv shapes.
- `gh stack` branch operands must pass git ref validation and must not be option-looking operands unless the selected command shape has a proven operand delimiter; PR numbers are preferred for `gh stack link`.
- Human-readable display commands may be rendered from argv for evidence, but display text is never executable and must not be parsed back into argv.
- Fake CLI fixtures are test-only controls injected through PATH-scoped fake `gh` dispatch or controlled sandbox/fixture executable paths. Persisted decision and execution evidence records the canonical runtime argv shape, not the fake executable path as the selected command.
- The first `gh-stack` mutating item is the no-fallback boundary.

## Stack-Manager Evidence Path

Represents durable evidence locations that can be reopened on resume.

Path families:

- Decision evidence: `specs/<feature>/.process/stack-manager/<phase>/<operation>/<stable-operation-id>/decision.json`
- Read-only proof: `specs/<feature>/.process/stack-manager/<phase>/<operation>/<stable-operation-id>/read-only-proof.json`
- Command execution evidence: `specs/<feature>/.process/stack-manager/<phase>/<operation>/<stable-operation-id>/commands.json`
- Recovery evidence: `specs/<feature>/.process/stack-manager/<phase>/<operation>/<stable-operation-id>/recovery.json`
- Workflow event evidence: `docs/ai/specs/.process/<workflow-id>-workflow.md`

Validation:

- Evidence paths must be repo-relative and must start with either `specs/<feature>/.process/` or `docs/ai/specs/.process/`.
- The stable operation id is derived from phase, operation, slice id or review order when present, and first mutating command id when present.
- Evidence paths must not contain timestamps, random temporary names, absolute host paths, or command display strings.
- Evidence paths must reject parent traversal, shell metacharacter-derived display strings, and control characters before persistence.
- Workflow event ids for blocked operations are derived from the decision evidence path, selected manager, mutation-boundary command id, and next resume boundary so retries can supersede stale blocked events.

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
- `action`: command plan action that ran
- `manager`: command manager, with blocked recovery failures using `gh-stack`
- `argv`: executed argv array
- `mutates`: whether the command can change branch, PR, or stack metadata
- `mutation_boundary`: whether this command is the no-fallback boundary
- `started_at`: timestamp
- `finished_at`: timestamp
- `exit_status`: integer
- `stdout_tail`: bounded to 120 lines and 16 KiB
- `stderr_tail`: bounded to 120 lines and 16 KiB
- `side_effect_class`: `none`, `planned_mutation`, `partial_mutation`, or `partial_mutation_unknown`
- `evidence_path`: repo-relative persisted command evidence path

Classification rules:

- `none`: command is read-only, or a planned mutating command failed before it was attempted and current topology proves no side effects.
- `planned_mutation`: mutating command completed successfully and observed topology matches the expected post-command state.
- `partial_mutation`: mutating command was attempted and failed, and observed post-failure topology proves that at least one branch, PR, base, or stack metadata side effect occurred.
- `partial_mutation_unknown`: mutating command was attempted and then timed out, crashed, returned ambiguous output, or left evidence that cannot prove no side effects occurred. This class sets `fallback_allowed=false` until operator repair or same-manager reconciliation proves a safe resume boundary.
- Same-manager no-change reconciliation can clear a blocked boundary only when current topology, PR identity, base/head refs, head SHA, and packet identity exactly match the pre-mutation expected state and the failed argv is proven to have left no topology changes.

## Recoverable Block State

Emitted when `gh-stack` may have partially mutated topology and fallback would risk duplicate PRs or manager mixing.

Fields:

- `status`: `blocked`
- `reason`: operator-facing block reason
- `fallback_allowed`: false
- `selected_manager`: `gh-stack`
- `failed_operation`: command plan item and execution evidence, including action, argv, exit status, side-effect class, stdout/stderr tails, and evidence path
- `mutation_boundary`: attempted boundary operation with `status=partial_mutation` or `partial_mutation_unknown`
- `pre_mutation_topology`: topology snapshot before mutation
- `observed_post_failure_topology`: topology snapshot when available
- `prior_successful_prs`: PR numbers/URLs already reconciled
- `next_resume_boundary`: slice/marker/branch to inspect before retry
- `retry_policy`: same-manager reconciliation or operator repair instructions
- `blocked_event_id`: deterministic workflow event id for superseding stale blocked events
- `resume_preflight`: ordered checks that must pass before any resumed create/sync/restack command
- `stale_result_policy`: how retry handles existing blocked decision/recovery/workflow evidence
- `evidence_paths`: state, command log, PRS manifest, and workflow evidence paths

Validation:

- A recoverable block MUST NOT allow an explicit-`gh` fallback while `side_effect_class` is `partial_mutation` or `partial_mutation_unknown`.
- Recovery evidence MUST include enough current and expected topology to prevent duplicate PR creation or ambiguous base retargeting on retry.
- Resume preflight MUST reload the prior decision and recovery evidence, revalidate current topology, PR identity, base/head refs, head SHA, and packet identity, then either prove same-manager no-change reconciliation or keep the run blocked.
- Stale blocked workflow events MUST be superseded by `blocked_event_id`; a retry MUST NOT append duplicate blocked events for the same boundary.
