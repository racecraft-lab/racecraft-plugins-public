# Runner run facts and deferred publication checks

Issue #1163: the agent hand-wrote `updated_at` and `elapsed_seconds` into
`autopilot-state.json`, and the Stop hook demanded a push while background
agents were still running.

## Rule

- `autopilot_state.update(..., workflow=...)` stamps UTC `updated_at` and
  projects the execution-control mirror (`ledger_path`, `run_id`,
  `disposition`, `reasons`, `elapsed_seconds`, `checkpoint_due`) from the bound
  ledger (`refresh_run_facts`). The plan terminal, the formal checkpoint mirror
  and the `execution-control` helper in `mode=apply` all write state through
  it. Nesting persistence calls `update` without `workflow`, so it keeps
  main's timestamp behavior.
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
  `autopilot_state.py`, `plan_stage_terminal.py` and
  `formal/lifecycle.py`. The unsettled-outcome set in
  `stop_policy.publication_pending` copies one in `execution_control.py`.
  Behavior is consistent today; a later refactor should give each fact one
  home.
- **The formal state mirror no longer sorts keys.** `autopilot_state.update` writes
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

## Checkpoint compact-history follow-up

R1363-eecf75d1: compact checkpoint answers now project `completed_dispatch_ids`
with the existing wire-bounded batch policy and exact `completed_dispatch_count`.
Detailed checkpoint answers and the validated ledger retain every completed ID.
The public reserve/complete regression builds nine completed dispatches, including
eight maximal astral IDs. Before the fix, checkpoint applied its timestamp then
overflowed in all six source/Claude/Codex and absent/invalid mirror cases.
The repaired answer preserves the run identity, disposition and mirror warning.

R1363-06386042 and R1363-f5903a96: shared guidance and the Codex overlay describe
phase-local read-only detailed status when a batch stays stuck, and explicitly
allow independent units when the runner permits their reserve. A stuck unknown
still blocks its overlapping or unscoped work; recovery never clears it merely
to advance the compact batch.

Additional review notes retained for subsequent reviews:

- R1363-30bbb25d: the prior constant extraction and behavior change share one
  commit. Changing that historical ordering requires prohibited history
  rewriting; no runtime defect is involved. This follow-up adds one field to
  the existing contract. The later commit 05a2bba0 shares its field name
  between producer and projection, but it also rewords recovery guidance,
  reorders the Codex overlay prompt and extends a contract assertion, so it
  is not purely behavior-preserving. Splitting it would rewrite pushed history.
- R1363-e361b2df: the package-root field contract avoids an envelope import of
  execution-control; there is no import cycle on the shipped path.
- R1363-14a84558: `blocked_by` uses insertion order. The earlier subset assertion
  is valid for its sorted-insertion fixture, but is not a general ordering
  guarantee; no production result depends on that fixture ordering.
- R1363-2ccbb033: the prior batch-advance test uses an independent native result
  with `complete`; it proves batch advancement, not reconcile-unit verification.
- R1363-67e6e598: extra blank lines in the existing test are cosmetic.
- R1363-67a1ec3c: the recovery instruction now consistently says retry the blocked
  action, matching the existing runner behavior.

- The Codex overlay uses the same recovery protocol but is not pinned by the
  shared Markdown wording assertions. This is not a reachable defect in the
  reviewed overlay; generated-artifact consistency checks its shipped copy.

## Review follow-up at 05a2bba0

- Detailed `status` answers are uncapped and serialize the full `ledger` before
  `unknown_dispatch_ids`, so host output truncation could drop the IDs a
  phase-local inspection was meant to expose. The recovery guidance now has the
  phase-local request parse the answer and return only `data.unknown_dispatch_ids`;
  the contract test pins that wording on both hosts. The runner output is unchanged.
- The checkpoint regression asserts the history cap through
  `COMPACT_EXECUTION_HISTORY_LIMIT_BYTES` instead of a literal.
- Info, accepted: the recovery paragraph is copied into `SKILL.md`,
  `execution-efficiency.md` and `phase-execution.md` (existing pattern; the
  contract test pins all three). Compact checkpoint always returns the same
  insertion-order prefix; no guidance consumes `completed_dispatch_ids`.

## Review follow-up at 614530c7

- Low, fixed: the recovery guidance said to parse the detailed answer but not
  where. A delegate that reads the answer as tool output first can still lose
  the IDs to host truncation. The guidance now has it parse the runner's stdout
  with `python3` before printing, and the contract test pins that wording on
  both hosts. The runner output is unchanged.
- Info, accepted: the guidance's reason (the ledger precedes the list) relies on
  `emit_response` sorting keys; no test pins that order, but the instruction
  stays correct if the order changes.
- Info, accepted: detailed `status` returns the full `unknown_dispatch_ids` list
  uncapped and omits the field when no dispatch is unknown. The list is far
  smaller than the ledger (about 9 KB for 700 IDs), and the guidance only
  delegates this read when IDs remain outside a compact batch.

## Review follow-up at 080e8319

- Low, fixed: this document still named `autopilot_state.write_state` as the
  run-facts owner after the merge removed it; it now names
  `autopilot_state.update(..., workflow=...)`.
- Low, fixed: `mirror_execution_result` projected the mirror fields from the
  applied result, then `refresh_run_facts` overwrote every one of them from
  the bound ledger. It now binds only `ledger_path` and `run_id` and lets
  `refresh_run_facts` own the projection. The written state is unchanged.
- Info, accepted: `refresh_run_facts` names its local `snapshot`, shadowing the
  module function `snapshot()`; the module docstring does not list the
  execution mirror; `plan_stage_terminal.record_pull_request` states
  `stage="plan", status="completed"` in both its idempotency check and its
  update; `test-compact-answers.py` borrows `setUp`/`call` from fixture classes
  and passes `mode` through `**inputs`; the duplicate `mypy.ini` entry removal
  rides in a `refactor(tests)` commit.
- Info, accepted: detailed `status` omits `unknown_dispatch_ids` when no
  dispatch is unknown, so a phase-local delegate that indexes it directly gets
  a `KeyError` (fails loudly; only delegated when a compact count exceeds its
  batch, so the key is present).
