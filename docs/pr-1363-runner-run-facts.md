# Runner run facts and deferred publication checks

Issue #1163: the agent hand-wrote `updated_at` and `elapsed_seconds` into
`autopilot-state.json`, and the Stop hook demanded a push while background
agents were still running.

## Rule

- `autopilot_state.write_state` stamps UTC `updated_at` and projects the
  execution-control mirror (`ledger_path`, `run_id`, `disposition`, `reasons`,
  `elapsed_seconds`, `checkpoint_due`) from the bound ledger. The plan
  terminal, the formal checkpoint mirror and the `execution-control` helper in
  `mode=apply` all write state through it.
- The `execution-control` helper refreshes an existing state file only after
  its ledger change is durable. If that refresh fails (for example a malformed
  state file), the helper still answers with the applied result and its
  `run_id`, plus a `state_mirror_not_refreshed` warning diagnostic. The ledger
  change is never reported as an input error.
- The `unpushed` Stop hook defers while any plan row is `pending` or
  `in_progress`, or any ledger dispatch is `reserved`, `running` or `unknown`.
  The plan terminal and completed-work checkpoints own their pushes.

## Compact applied-result repair

Finding `F1363-d2805a40` exposed full execution-ledger history competing with
the applied action and mirror warning for the compact envelope's 16 KiB budget.
The envelope now projects execution-control's ledger to `run_id` on every
compact path. The full ledger remains durable at `ledger_path`, and detailed
responses retain it. The action's other fields and diagnostics are preserved.

`test-compact-answers.py` exercises validated ledgers with 109, 110 and 300
implementation dispatches through source, Claude and Codex launchers:

- `test_compact_status_retains_applied_result_when_the_state_mirror_fails`:
  apply status with JSON-array and invalid-JSON state, preserving run identity,
  disposition, warning, remediation and the wire-size cap after the durable write.
- `test_compact_reserve_retains_applied_result_when_the_state_mirror_fails`:
  the same states and sizes for reserve, proving the next dispatch is durably
  reserved and its returned ID is retained.
- `test_detailed_applied_results_and_non_apply_mirror_controls`: detailed
  status/reserve retain the complete result; read-only status and dry-run
  status/reserve leave ledger and state bytes unchanged and emit no mirror warning.
- `test_execution_history_projection_keeps_refusals_and_nested_results`:
  history in other ledger fields (epochs and excluded intervals), nested result
  wrappers, continue/defer/checkpoint dispositions, false authorization, action
  fields and detailed-result immutability. `test_other_helpers_keep_their_ledger_evidence`
  limits this projection to execution-control.

The adversarial pass follows the ledger through the helper's durable-write,
mirror-warning and envelope windows. Projection occurs after all three helper
actions (execution-control, execute-verification and task-results) are routed;
only execution-control's tagged result is projected. The shared source and both
regenerated payloads use the same rule. No pathname lookup, link traversal,
rename handling or ledger validation changes in this repair.

## Unknown-dispatch output repair

Finding `F1363-ce3c1911` exposed the same compact applied-result loss through
two historical lists outside the ledger: `unknown_dispatch_ids` and
`blocked_by`. Compact execution-control answers retain bounded batches of
complete IDs alongside exact `unknown_dispatch_count` and `blocked_by_count`
values, including nested results and refusals. Detailed answers retain both
complete lists and the full ledger;
the durable ledger remains available at `ledger_path`. This bounds historical
ID output independently of dispatch count, ID length and JSON escaping, while
keeping the action's dispatch ID, run ID, disposition, reasons and diagnostics.

Review findings `R1363-f813bca5` and `R1363-f2f9d554` exposed the counts-only
projection's loss of actionable recovery IDs. Source, both rendered hosts and
the Codex overlay now use the same bounded-batch protocol: settle returned IDs,
then refresh compact status or retry the blocked action for the next batch.
Counts describe totals and never stand in for dispatch IDs. The ledger
validator enforces the existing nonempty, 240-character dispatch-ID admission
bound on persisted keys before any apply write, so at least one valid ID fits
every nonempty batch, even with maximum JSON escaping. Producer and envelope
field names share the package contract constants (`R1363-53a37229`).

`test_compact_only_root_receives_ids_to_reconcile_on_all_launchers` uses only
compact runner requests to start from a reserved worker, complete it unknown,
read status and attempt overlapping work; both needed ID lists name that worker.
`test_compact_batches_reveal_remaining_exact_ids_after_resolution` settles
maximum-length escaped IDs and retrieves the remaining IDs in successive
compact answers. `test_invalid_persisted_dispatch_ids_fail_before_apply_writes`
rejects blank, whitespace and overlength stored IDs without changing the ledger.
`test_both_hosts_describe_compact_id_batches_and_refresh` checks the batch and
count fields at all three guidance sites in both rendered hosts.

Finding `F1363-596e46be` identified an incorrect reachability claim in this
document and compact-runner-answers.md. Unknown dispatches block unscoped or
overlapping work. Implementation reserves for distinct `tdd_units` continue,
so normal reserve/complete calls can accumulate unknown records. A fixed
overflow count is misleading because serialized ID length also matters.

The new `CompactUnknownDispatchTests` in `test-compact-answers.py` cover:

- `test_unknown_status_apply_keeps_mirror_warning_on_all_launchers`: 700
  validated unknowns, array/invalid-JSON mirror, durable write and warning.
- `test_unknown_scoped_reserve_keeps_durable_dispatch_on_all_launchers`:
  700 independent units, both malformed mirrors, durable next dispatch and ID.
- `test_unknown_status_without_state_keeps_applied_result_on_all_launchers`:
  800 unknowns, durable status write without a state file or warning.
- `test_unknown_guarded_actions_keep_refusal_and_exact_blocker_count`: all
  nine guarded actions, including unscoped reserve, retain refusal and counts
  without adding a dispatch. `test_unknown_overlapping_reserve_counts_only_actual_blockers`
  checks that one overlapping unit yields one blocker, not all unknowns.
- `test_unknown_detailed_apply_and_compact_non_apply_controls`: detailed
  apply retains full evidence; compact read-only/dry-run leave ledger bytes
  unchanged without mirror warnings. Source and both host launchers are covered.
- `test_unknown_compact_size_is_independent_of_id_length`: short, ordinary,
  long Unicode and escaped IDs at the same history count.
- `test_independent_units_can_accumulate_unknowns_through_public_actions`:
  real reserve/complete calls produce unknowns and still admit a distinct unit.
- `test_unknown_history_counts_preserve_nested_refusals_without_mutating_details`
  in `CompactExecutionProjectionTests`: nested refusals keep decision fields,
  count each list independently and leave the original detailed result intact.
  `test_other_helpers_keep_their_ledger_evidence` excludes unrelated helpers.

The focused adversarial pass checked both list producers in `_control_result`
and `_update_ledger`, every guarded action, the write-before-mirror window,
nested projection, and source/Claude/Codex launchers. The repair changes only
response projection: no pathname, symlink, hard-link or rename operation changes.

## Known limits

- **Plan-row deferral is wider than "agents pending".** The canonical plan
  keeps future rows `pending` until the run ends, so the hook rarely fires
  during an active run. A run that ends with a row still open (a harm halt, or
  a parked unit's row left `pending`) also gets no push demand. Not blocking:
  the plan terminal pushes its own commits, stop-policy.md documents the
  deferral, and unpushed commits stay in the local branch. The owner may
  narrow the trigger to the ledger dispatches alone.
- **The ledger check covers only reserved agents.** Background agents that the
  orchestrator never reserves in the ledger are covered by the plan-row proxy
  only.
- **A mismatched mirror stops the plan terminal bookkeeping write.** If
  `execution_control.run_id` or `ledger_path` in state does not match the
  ledger, `record_pull_request` raises after the PR exists, and reruns fail the
  same way. Reachable only when state is hand-edited: every
  `execution-control` apply now refreshes the mirror from the ledger.
- **Hand-written `updated_at` persists until the next apply call.** Nothing
  rejects it. phase-execution.md still describes per-step state edits without
  naming the refresh call; SKILL.md and task-list-canonical.md do name it.
- **The hook imports the runner at module level.** An `ImportError` would exit
  1 with a traceback instead of the documented fail-open exit 0, and would
  also disable `lockfile` mode. Unreachable in the shipped layout: both host
  payloads ship `speckit_pro_runner` beside `scripts/`.
- **Hook snapshot errors fall back to the Git check.** An unreadable ledger or a
  mirror without `run_id` is not evidence of pending work; the hook notes it on
  stderr and still checks commits (see pr-1363-security-fix.md).
- **Duplicated facts.** The state path rule
  (`Path(workflow).with_name("autopilot-state.json")`) appears in
  `autopilot_state.py` twice, `plan_stage_terminal.py` and
  `formal/lifecycle.py`. The unsettled-outcome set in
  `stop_policy.publication_pending` copies one in `execution_control.py`. The
  mirror projection appears twice in `autopilot_state.py`. Behavior is
  consistent today; a later refactor should give each fact one home.
- **The formal state mirror no longer sorts keys.** `write_state` writes
  insertion order where `atomic_record` sorted keys. No reader depends on key
  order; diffs of the state file may reorder once.
- **The clock tests live in test-plan-stage-terminal.py**, not the
  test-autopilot-stage-resolution.py the issue proposed.
- **A hand-repaired state can hide reserved dispatches from the hook.** After a
  `state_mirror_not_refreshed` warning, an agent that rewrites the state by hand
  without the `status mode=apply` refresh leaves no bound mirror. With no
  pending plan row, the hook then asks for a push while ledger agents are still
  reserved or running. Not blocking: it fails closed (an extra push demand),
  the canonical plan keeps rows `pending` during a run, and the warning's
  remediation names the refresh call.
- **The mirror warning catches only `ValueError`, `OSError` and `TypeError`.**
  A `RecursionError` from a deeply nested state file would escape the
  applied-result path. Unreachable in practice: it needs a deliberately crafted
  state file.
- **The envelope names one helper.** `compact_decision_data` projects the
  ledger only for `helper_id == "execution-control"`. A per-helper projection
  hook would be cleaner ownership, but with one helper it would be speculative.
  Move the rule to execution-control if a second helper needs a projection.
