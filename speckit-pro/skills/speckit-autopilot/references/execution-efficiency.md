# Bounded Execution and Verification

Read at kickoff/resume and before Tasks, implementation dispatch, corrective
work, or final verification. This shared contract governs both native hosts;
it does not replace their dispatch, authorization, or mandatory gate rules.

## Durable run ledger

Invoke runner helper `execution-control`, operation `execution-control`, with
`inputs.workflow_file` and `inputs.action`. Use `mode=apply` for ledger changes
(`dry_run` previews); `action=status` is `mode=read_only`.

Every non-start action requires `inputs.expected_run_id` from the last genuine
`result.data.ledger.run_id`. First-ever kickoff may omit it; a known resume
also passes `expected_run_id`, so a missing ledger is a recovery failure, never
a new kickoff. Preserve the `ledger_path` returned by the helper and pass it
when resuming or relocating the workflow; never construct a filename or use a
new workflow path to reset counters. Ledger names are workflow-keyed, not a
shared fixed file for every workflow in a directory.
The default ledger lives in `.process/execution-control/` beside the workflow,
or in `execution-control/` when the workflow already sits in a `.process`
directory. An earlier `.process/.process/execution-control/` ledger stays valid
when passed as `ledger_path`. Verification evidence follows the same rule in
`verification/`; a record already under `.process/.process/verification/`
still validates. Both directories are self-ignoring from the run's `start`: the
runner writes a `.gitignore` holding `*` into each, so a verification log you
write there is never committed or scanned. Untracked ledger, verification evidence, and task-results
journals under `.process/execution-control/`, `.process/verification/`, or
`.process/task-results/` never make the worktree dirty for mutation helpers; any other change still refuses `apply`.
An existing ledger belongs to its recorded canonical workflow path. An explicit
`ledger_path` does not authorize a different workflow to adopt that run; an
existing explicit ledger also requires the parent's `expected_run_id` on start.
Missing stored workflow identity is a recovery failure, not permission to infer
ownership from the caller's current workflow.

- `start`: open or recover the same workflow's ledger before the first phase.
  Pass `inputs.spec_file` as the resolved repo-relative feature spec path when
  available; the workflow can live elsewhere. If omitted, only an existing
  adjacent spec can supply requirement IDs, otherwise failures use `unresolved`.
  An existing spec's registry freezes at start; later paths or contents never
  reset counters.
  Agent replacement, compaction, a reclaimed state mirror, and resume never
  reset it. Only two actions open a fresh allowance: `begin-stage-epoch` when
  the operator explicitly starts the implement stage, and an operator-approved
  `begin-replan-epoch`. Preserve another workflow's ledger when reclaiming
  the one-run `autopilot-state.json` mirror.
- `bind-invariants`: for a greenfield run that started with an empty registry,
  call once after Specify has produced the feature spec, before the next
  corrective reservation. Pass the same `workflow_file`, `expected_run_id`,
  `ledger_path`, and an explicit repo-relative `spec_file`. The helper requires
  at least one FR, NFR, or INV ID and records the spec path and content digest.
  It refuses an already populated or previously bound registry. Later spec
  edits do not silently import new IDs; a second bind is refused. This action
  preserves the run identity, clocks, dispatches, reservations, and consumed
  corrective cycles. Earlier `unresolved` reservations remain `unresolved`;
  do not use a new ID to retry the same failure. Do not bind while an external
  wait or unknown dispatch outcome needs reconciliation.
- `reserve`: before each native dispatch or command, supply `dispatch_id` and
  `kind=implementation|corrective|verification|infrastructure`. A corrective
  dispatch supplies `failure_invariant`: a stable approved requirement or
  invariant ID. Unknown mappings share `unresolved`; changed wording, task IDs,
  agents, and commits are not new families.
  A review fix for the increment under review also supplies
  `review_remediation`: `{"tdd_unit": <the increment's TDD unit>, "paths":
  [<every repo-relative path the fix touches>]}`, plus an explicit `spec_file`
  naming the feature spec, since the workflow file usually lives outside the
  feature directory. The helper reads ownership only from the
  `.process/task-execution.json` beside that spec, and only when its
  fingerprints match the current spec, plan, and tasks. When every path sits
  inside that unit's `owns` and overlaps no other unit that is still open, it
  reserves the fix under the increment's own allowance: two rounds per TDD
  unit, recorded in
  `increment_allowances` and returned as `review_allowance=increment`. That
  allowance never draws on the run-wide `corrective_cycles` budget. Otherwise
  the request takes the ordinary run-wide path unchanged, and the result
  carries `review_allowance=run_wide` and the reason in `increment_ineligible`
  (`ownership_evidence_unavailable`, `ownership_evidence_stale`,
  `increment_not_in_ownership_evidence`, `no_remediation_paths`,
  `path_outside_increment_ownership`, or `path_reopens_another_increment`).
  Missing ownership evidence never grants a free allowance. Another unit is
  closed, so sharing a file with it does not refuse the fix, only when every
  one of its tasks is checked in both the committed HEAD `tasks.md` and the
  worktree `tasks.md`, and the committed task definitions match the sidecar's
  fingerprints. The runner reads that state itself; without git or a matching
  committed file, every other unit counts as open. A third round for the
  same unit returns `disposition=defer` with
  `increment_review_allowance_exhausted`: defer that increment to the
  end-of-run request and continue. Its tasks stay checked and its dependents
  stay runnable; its open findings become a tracked follow-up in the
  implementation notes and the workflow file, never a new `tasks.md` line, so
  a serial plan never stops mid-run on a deferral. Increment
  allowances archive with the rest of the allowance in `corrective_epochs`.
  A planning gate's own remediation (G2 through G7, most often G6 Analyze)
  instead supplies `gate_remediation`: `{"gate": "G6", "paths": [<every
  repo-relative path the fix touches>]}`, plus the same explicit `spec_file`.
  The feature directory is that spec's directory; when the ledger has already
  bound a spec in `invariant_binding`, it must be the same one. When every path
  is a planning document of that feature (`spec.md`, `plan.md`, `research.md`,
  `tasks.md`, `data-model.md`, `quickstart.md`, `.process/task-execution.json`,
  or a `checklists/<name>.md`), the helper reserves the fix under the gate's own
  allowance: two rounds per gate, recorded in `gate_allowances` and returned as
  `remediation_allowance=gate`. It never draws on the run-wide
  `corrective_cycles` budget and needs no operator event. A fix that touches
  code, tests, formal models, `contracts/`, or any other path takes the
  ordinary run-wide path unchanged, and the result carries
  `remediation_allowance=run_wide` and the reason in `gate_ineligible`
  (`feature_binding_mismatch`, `no_remediation_paths`, or
  `path_outside_planning_documents`). The helper judges paths only: a
  threshold or scope change written inside a planning document is the
  orchestrator's call, so omit `gate_remediation` and reserve it run-wide. Missing evidence never grants a free
  allowance. A third round for the same gate returns `disposition=defer` with
  `gate_remediation_allowance_exhausted` and a `deferred` entry whose
  `unit_kind` is `gate`: record the open findings for the end-of-run request
  and continue; it is never a mid-run stop. Planning documents produce no
  runner-parsed failing checks, so a gate allowance has no convergence
  admission; its two rounds are its fixed bound. Gate allowances
  archive in `corrective_epochs` like increment allowances.
- `complete`: record the same `dispatch_id` and actual
  `outcome=completed|failed|unknown|expected_tdd_red`. Expected assertion RED is
  implementation work, not corrective work. Infrastructure failures remain
  distinct from failed required verification; neither authorizes blind retry.
- `reconcile`: permit one read-only inspection of a missing native result for
  its `dispatch_id`. Inspect owned effects and retained output, not just agent
  liveness. This records an unknown outcome and `checkpoint_required`, even
  when `reconciliation_allowed=true` permits that one inspection. It does not
  authorize continuing writes, a new dispatch ID, or a replacement launch.
  Resolve a recovered result only with `action=complete` and independently
  recovered parent `native_observation` containing `native_event_id`, `run_id`,
  `dispatch_id`, `action=dispatch_result`, and matching
  `outcome=completed|failed|expected_tdd_red`. Without that genuine event,
  unknown remains a checkpoint; worker text or a receipt cannot clear it.
- `authorize-corrective-retry`: after a corrective reservation owner's
  dispatch has failed because of an infrastructure error in the host result,
  and the operator has explicitly approved recovery, atomically reserve one retry under that same
  reservation. Pass a new `dispatch_id`, the original `failed_dispatch_id` and
  `reservation_id`, plus a parent `native_observation` with the operator's
  actual `native_event_id`, `run_id`, `action=corrective_retry_approved`,
  `failed_dispatch_id`, `failed_native_event_id` matching the recorded failure,
  `retry_dispatch_id`, `reservation_id`, and `failure_kind=infrastructure`.
  The parent verifies the host error and user message before supplying this
  event; matching fields in the helper are validation, not authentication.
  The helper preserves the failed dispatch and both consumed cycles, and
  permits one retry only when the two-cycle ceiling is reached and no sibling
  dispatch used that reservation. Dispatch only after it returns `continue`.
  A second retry, self-asserted approval, or a failed result without a recorded
  native failure event remains blocked.
- `authorize-corrective-continuation`: after a corrective executor or its
  authorized infrastructure retry completes, a required Analyze consensus
  edit can make the Tasks metadata fingerprint stale. If the two-cycle ceiling
  is reached, checkpoint the work and obtain explicit operator approval for
  exactly one Tasks metadata reconciliation under that same reservation. Pass
  the completed `completed_dispatch_id`, a new `dispatch_id`, and the original
  `reservation_id`, plus the operator's independently observed
  `native_observation`: `native_event_id`, `run_id`,
  `action=corrective_continuation_approved`, `completed_dispatch_id`,
  `continuation_dispatch_id`, `reservation_id`, and
  `purpose=task_metadata_reconciliation`. Verify the actual operator message
  before supplying it; the helper only validates its binding. It requires the
  completed corrective dispatch to be the reservation owner or its recorded
  recovery, rejects unrelated work in that reservation and reused event IDs,
  and reserves one continuation without changing run identity or cycle counts.
  The Tasks producer may update only source-bound metadata, then the parent
  revalidates G5 before G6. A second continuation or a failed/unknown source
  remains blocked; this action is not a general repair-budget reset.
- `authorize-corrective-exception`: when an ordinary corrective `reserve` for a
  reproduced application failure returns `disposition=defer` with
  `corrective_run_budget_exhausted` or `failure_family_budget_exhausted` (a
  repeat of an already reserved family whose work has completed or failed),
  defer that correction and name it in the one end-of-run consolidated
  request. This is an end-of-run tool, never a mid-run question: call it only
  after the operator approves that exact correction in answer to that request.
  Pass a new `dispatch_id` (or the deferred one), the approved
  `failure_invariant`, and the approved correction's `scope_sha256`, plus the
  operator's independently observed `native_observation`: `native_event_id`,
  `run_id`, `action=corrective_exception_approved`, `failure_invariant`,
  `dispatch_id`, `failure_kind=application`, `refusal_reason` (the refusal the
  ordinary reserve returned), `scope_sha256`, and `spec_sha256` matching the
  ledger's `invariant_binding`. The invariant must be an approved ID, never
  `unresolved`, and the run must have bound its spec with `bind-invariants`.
  The helper records one top-level `corrective_exception` per corrective epoch
  and reserves that single dispatch under it. It leaves `corrective_cycles`, reservations,
  earlier results, and ordinary ceilings unchanged, and refuses replay, a
  second exception, a mismatched identity, scope, or spec, and any request an
  ordinary reserve would accept. The exception dispatch has no nested,
  retry, or continuation allowance. When the correction fixes a failure class
  in one test file (see the phase guidance on repeated gate failures), pass
  `failure_class` as well: `test_file` (repo-relative), `failure_signature`
  (the normalized failure message, with test names, durations, and counts
  stripped), and `change_kind`. The operator event carries the same
  `failure_class` object. The helper refuses a production path, an unknown
  change kind, or an event whose class differs from the request.
- `reserve-class-correction`: after a class-scoped exception, reserve a
  follow-up correction inside that exact class without a new operator event.
  Pass a new `dispatch_id` and the same `failure_class`: `test_file`,
  `failure_signature`, and `change_kind` (only `test_timeout` today). All three
  must equal the approved class exactly; the parent normalizes the signature
  the same way both times. `test_file` must be a test path under the runner's
  existing test-file classifier, never a production path. Every earlier
  correction in the class must have completed; a failed or unknown one needs
  the operator. One approval covers at most two follow-ups, recorded in the
  exception's `follow_up_dispatch_ids`. A third follow-up returns
  `disposition=defer` with `failure_class_allowance_exhausted`: defer it to the
  end-of-run request. A different file, signature, or change kind, a reused
  dispatch ID, an exact-diff exception, or an archived epoch is refused
  without mutation.
- `begin-replan-epoch`: when the operator orders a re-plan (a rescope, or a
  `--from-phase` rerun of planning phases the run already completed) after the
  run has spent corrective allowance, open a fresh allowance for the re-plan
  with the operator's approval. This is an end-of-run tool, never a mid-run
  question: offer the re-plan in the one end-of-run consolidated request, or
  take it from an operator-ordered rerun. Pass the explicit repo-relative
  `spec_file` and
  the operator's independently observed `native_observation`:
  `native_event_id`, `run_id`, `action=replan_epoch_approved`, and
  `spec_sha256`, the digest of that spec file as it stands now. Every dispatch
  must be settled and no wait may be open. The helper moves the spent
  counters, reservations, dispatches, invariant registry, and exception into
  `corrective_epochs`, rebinds the registry to the current spec, and resets
  the counters. The run ID, clocks, and consumed events carry over; archived
  dispatch IDs and events can never be reused. A re-plan the operator did not
  order is not grounds for a new epoch.
- `begin-stage-epoch`: when the invocation argv names `--stage implement`,
  call it once after `start`, after Step 0.6c has written the resolved `Stage`
  row. Pass `autopilot_args`, the same invocation argv given to
  `resolve-autopilot-stage`. No operator event is needed: the operator's
  explicit stage request is the approval. The helper reads its own evidence and
  refuses unless the argv names `--stage implement` explicitly (an
  auto-detected stage, `full`, and `plan` never qualify), the workflow file
  records every planning phase complete, and its `Stage` row already reads
  `implement`. Every dispatch must be settled and no wait may be open. It moves
  the planning stage's spent counters, reservations, dispatches, and exception
  into `corrective_epochs` under the runner-derived event ID
  `stage-transition:implement`, keeps the invariant registry and its binding,
  and resets the counters. A stage opens one allowance per run: a resumed
  `--stage implement` invocation returns `stage_epoch_opened=false` and
  changes nothing. When real corrections spend this stage's own allowance,
  defer the blocked work to the end-of-run request; never ask mid-run.
- Metadata-only correction: a task verb reworded so the task routes to
  verification (for example T001 `Confirm` to `Verify`) spends no cycle and
  needs no re-plan or operator question. Apply the `tasks.md` edit first,
  then `reserve` a new corrective dispatch with `metadata_only: true` and the
  explicit `spec_file`. The runner proves the claim itself against the
  committed `HEAD` of that feature directory: `spec.md` and `plan.md` must
  match byte for byte, and `tasks.md` may differ only on task lines whose
  leading verb swaps between two words of `PHASE7_VERIFY_KEYWORDS`, with the
  task ID, `[P]` and story markers, and every other byte unchanged. Checkbox
  state is ignored, as in the task fingerprints. Dependencies and ownership
  live in `.process/task-execution.json`: its `tasks` must match `HEAD`, and
  its `fingerprints` may be the committed ones or the refresh for the
  corrected sources. A feature without that sidecar at `HEAD` and in the
  worktree passes this check. A proven correction returns
  `correction_allowance=metadata_only` with its `task_ids`, and the ledger
  records it in `metadata_corrections`. Each task gets one such correction
  per run, across stage and re-plan epochs. Anything else returns
  `correction_allowance=run_wide` with `metadata_ineligible` and takes the
  ordinary reservation path: `baseline_unavailable` (no git, no committed
  file, or a symlinked or unreadable one), `planning_source_changed`,
  `not_metadata_only` (any other word, path, marker, task, line, phase, or
  sidecar change), `no_task_correction` (nothing differs from `HEAD`),
  `task_already_corrected`, or `feature_binding_mismatch`. After admission,
  refresh the task-execution sidecar fingerprints through
  `validate-task-execution` with `action=fingerprints`, rerun the affected
  gate, commit the edit, and record the dispatch result. When the ordinary
  path defers instead, undo the edit and carry it to the end-of-run request.
- `checkpoint`: persist the 45-minute completed-work marker without resetting
  the repair budget. `pause`/`resume` excludes only human-UAT or
  external-approval waits with independent parent `native_observation` carrying
  `native_event_id`, `run_id`, `kind=human_uat|external_approval`, and
  `action=wait_started|wait_ended`. Resume additionally requires
  `wait_start_event_id` matching the active start and a new, unconsumed
  `native_event_id`; replayed events cannot exclude time twice. A worker's
  assertion is insufficient.
- `relocate-workflow`: after an actual parent-observed workflow move, pass the
  original `ledger_path`, unchanged `expected_run_id`, and new `workflow_file`.
  Supply independent parent `native_observation` with `native_event_id`,
  `run_id`, `action=workflow_relocated`, `previous_workflow_file`, and
  `workflow_file`. Both paths must match the recorded source and actual new
  destination. Never synthesize this event from an edited ledger. Relocation
  changes workflow ownership explicitly without resetting the run, invariant
  registry, elapsed time, dispatches, or consumed repair allowances; replayed
  relocation events cannot authorize another move.

Each `native_event_id` is single-use across workflow moves, wait boundaries,
and recovered dispatch results. Operator retry, continuation, and exception
approvals share that rule. Changing the action or kind does not make a
consumed event new; obtain a distinct genuine parent event for each transition.

After a successful or `expected_failure` ledger response, the native orchestrator
mirrors `result.data` fields `ledger_path`, `disposition`, `reasons`,
`elapsed_seconds`, and `checkpoint_due`, plus `result.data.ledger.run_id`, into
the optional `autopilot-state.json.execution_control` object. These fields are
directly in `data`, not `data.stdout_json`. The helper writes its durable ledger,
not the one-run status file; workers do not own this mirror. Preserve the existing
top-level status and pending plan rows. An input error has diagnostics, not a
new mirror. On resume, read the live helper result before refreshing the mirror;
a stale mirror never initializes, overwrites, or resets a ledger. This record
is for user visibility, not independent proof of authority or completed work.

One corrective cycle per failure family and two corrective cycles per spec
are the shared ceilings. The operator-approved infrastructure recovery above
reuses an existing reservation without changing either count. Reserve before
repairs in G3 provenance, G4/G6 remediation, review, formal checks, or
hardening. Pass the parent's
`reservation_id` to nested work on the same failure; a nested loop has no
independent allowance. A rejected candidate or failed repair does not create
a new family. Pure read-only diagnosis may continue.

**Keep remediating while each round converges.** The ceilings above are the
non-convergence fallback, not a count that stops a converging repair. When an
ordinary corrective `reserve` would refuse a family that already holds a
reservation (`failure_family_budget_exhausted`), the helper first asks whether
that family's previous correction measurably converged, judged only from
evidence the runner recorded itself. Every `execute-verification` run parses
the output it executed, from a closed set of formats (unittest, pytest, bun,
and jest), into `failing_checks` on its verification dispatch: `command_id`,
`command_sha256` (the digest of the argv it ran), `format`, the sorted
`failing` test identifiers, the `passing` identifiers when the format names
them, `checks_run` (the run's own summary count), an `output_sha256` digest,
and `recorded_at`. No
helper action accepts this field, so a caller cannot supply it. Output in no
supported format, output matching two formats, a nonzero exit naming no
failure, or a command that did not finish records `failing: null`.

A family's first correction stores the newest recorded failure as its
`baseline`, and pins `spec_file` (the bound spec when the run has one, else
the resolved spec) with its `spec_sha256`. Later checks reread that pinned
file and ignore a request's `spec_file`. The next correction in that family is
admitted with no operator event, no new reservation, and no change to
`corrective_cycles` when all of these hold: every correction in its
reservation, nested ones included, completed; the pinned spec is unchanged; and
the newest `failing_checks` for the same `command_id`, recorded after the
previous correction completed, ran the same argv and at least as many checks,
and is either a strict subset of that correction's baseline set or disjoint
from it with every baseline failure named as passing.
It must also differ from every failing set the family already had. The
admitted dispatch records `progress_of` (the previous correction) and its own
`baseline`, so the chain of baselines is the family's history. The response
carries `progress` with `admitted=true`, `change` (`shrank` or `moved`),
`previous_dispatch_id`, and `baseline`. An admitted correction has no nested
allowance of its own. Dispatch it through the executor with
the consensus agents' diagnosis, rerun verification, and reserve the next
correction the same way.

Anything else is non-convergence, and the reserve falls through to the
ceilings and the deferral below, with `progress.reason` naming why:
`no_progress` (the same set, a larger one, or a disjoint set without named
passes), `returned_to_earlier_state`, `evidence_unparsed`, `no_new_evidence`
(no verification ran after the previous correction, or that run already
anchors this family), `command_changed` (a narrowed or edited command),
`fewer_checks_ran` (a deleted or skipped check), `no_failing_checks`, `previous_correction_unsettled` (a
failed, unknown, or unfinished correction), `no_baseline`, `spec_changed`, or
`unresolved_family`. The progress path never admits a requirement or scope
change: a changed spec ends the chain. It never covers boundary files, pushes,
or remote changes, which stay hard human stops whatever the progress. The
ledger recomputes every baseline and admission on each call, so a tampered
history is an integrity failure that stops the run.

Check `status` before advancing and while waiting. A run has no wall-clock
limit: elapsed time never stops it. `checkpoint_due` calls for a
completed-work checkpoint (commit and push progress) every 45 minutes, and the
run then continues. `elapsed_seconds` reports time for the record and excludes
only separately evidenced human-UAT/external-approval waits.
If `disposition=defer`, the helper refused that one dispatch: it is the
non-convergence fallback, never the default outcome of a budget. Its
allowance is spent: an exhausted failure family or run budget, a spent
reservation (`corrective_cycle_failed_no_nested_retry` or
`corrective_cycle_already_closed`), `increment_review_allowance_exhausted`, or
`failure_class_allowance_exhausted`. The envelope status is
`expected_failure` and no reservation was made, so do not dispatch it. The
ledger records the refusal once in its `deferred` list and returns the same
entry as `deferred`: `dispatch_id`, `reason`, `unit_kind` (`failure_family`,
`increment`, or `failure_class`), `unit`, and `deferred_at`. A repeated
`reserve` for the same `dispatch_id` returns that entry again. Record the
deferred item with the task or gate it blocks and the exact gate output, then
keep executing every independent task, increment, gate, and Post check. A
deferral is never a stop and never a mid-run question. When a later
corrective dispatch for the same unit completes, the ledger marks the entry
resolved itself: it adds `resolved_by` (that dispatch ID) and `resolved_at`
(its completion time) and keeps the entry for audit. A dispatch resolves an
entry only when the ledger ties it to the entry's unit: the reservation or
`corrective_exception` of that failure family (or failure class), the
increment's own review allowance, or the gate's allowance. It
must be reserved at or after `deferred_at` and have `outcome=completed`. No
request can name a resolution, and a failed or unknown result resolves
nothing. At the end, list every unresolved entry of the current `deferred`
list in the one end-of-run consolidated request; `finalize-run` omits resolved
entries. An entry still unresolved at the end makes `finalize-run` return
`outcome=human_stop`: the run never finalizes ready for review over it, a
gate's included. `authorize-corrective-exception` and `begin-replan-epoch` are
end-of-run tools that act on the operator's answer to that request. A new
allowance archives the list into `corrective_epochs` with the rest of the
spent allowance. The ledger validates every entry on each call: an entry whose
allowance the ledger does not show as spent, a duplicate, or an out-of-order
clock is an integrity failure that stops the run, and so is a resolution the
ledger's own records do not prove. A ledger written before resolutions existed
has no resolution fields and still validates; its entries stay unresolved.

If `disposition=checkpoint_required`, stop new work and record remaining work,
owned in-flight dispatches, unknown effects, consumed reservations, elapsed
time, and the required operator decision. Never call this completion or a
successful runtime measurement. Keep existing run status `in_progress` or
`awaiting_review` as applicable and mirror the execution-control disposition;
do not invent a top-level status. Independent approved work can continue only
when the helper permits it.

## Tasks metadata and native batches

The Tasks prompt produces `<feature>/.process/task-execution.json` with
`schema_version=task-execution.v1`, `fingerprints` (`spec_sha256`,
`plan_sha256`, `tasks_sha256`), and `tasks` keyed by every stable task ID.
Each entry supplies `capability_group`, `depends_on`, `owns`, and `tdd_unit`.
Ownership includes shared fixtures and generated inputs. Task definitions,
specification, and plan bind the metadata; checkbox completion does not.

Use `validate-task-execution` with `tasks_file` and `action=fingerprints` to
obtain the exact fingerprints and IDs for the producer. Default action
validates the authored sidecar. Set `task_execution_required=true` for a new
workflow whose Tasks prompt requests metadata. Validate after Tasks and before
partitioning after any definition change, including Converge/review appends.
The parent reconciles changed definitions through the Tasks producer; do not
modify upstream Converge or ask it to generate the sidecar. Invalid or stale
metadata stops dispatch. Legacy workflows without metadata keep singleton
execution; absence is not a silent optimization downgrade for new workflows.

Invoke `partition-phase7-tasks` with existing `tasks_file`, `wave_size`, and
project routing inputs, plus `task_execution_required` and `completed_tasks`.
The latter is the parent-reconciled set supported by consumed results and
verified effects, matching checked tasks; checkboxes alone are not evidence.
Metadata-aware output gives `batches` and `waves` of batch IDs. Each batch has
`id`, `agent`, `group`, `capability_group`, `tasks`, `tdd_units`, and `owns`.
Use the helper's result, never recreate its dependency/ownership scheduler.

Dispatch up to four adjacent tasks of one phase, routed agent, and capability
group per batch, sequentially inside that worker. Parallelize only the
helper's disjoint, dependency-ready batches within the host ceiling. Native
Agent/spawn_agent remains the dispatcher. Supply shared instructions,
PROJECT_COMMANDS, TDD protocol, completed-work evidence, and reservation once
per batch, followed by exact task descriptions and metadata. A TDD unit is a
closed behavior: keep its test/implementation checkboxes together, preserve
each task's result, and do not claim a test-only checkbox reached GREEN alone.
Each task gets its own `## Task Result: <TASK_ID>` and implementation-notes
entry. Reconcile partial results and resume only unfinished tasks; missing
effects require the read-only reconciliation/checkpoint path, not a replay of
the entire batch. Existing legacy partition output is consumed one task at a
time even if its old `[P]` runs contain several tasks.

### Persist per-task evidence

For metadata-aware execution, invoke runner helper/operation `task-results`:

- `action=start`, `mode=apply`: before dispatch, pass `tasks_file`,
  `journal_file=<feature>/.process/task-results/<run-id>.json`, and the same
  partition routing/concurrency/completed-task inputs. This freezes the original
  partition and `batches[].id`; reuse that journal after checkbox changes rather
  than inventing fresh batch IDs. Retain the returned `partition_sha256` from
  this genuine parent start result outside the worker-owned journal. Pass it
  unchanged as `expected_partition_sha256` on every existing-journal start,
  inspect, or record. Never recover the expected identity from a possibly edited
  journal or a worker claim. Missing independent identity requires recovery of
  the original parent result, not adoption of the journal's current plan.
  Dry-run previews do not persist it.
- `action=record`, `mode=apply`: on each native batch result, supply that
  `batch_id`, all frozen task IDs in order as `results`, and independent parent
  `native_observations`. Each result has `task_id`, `tdd_unit`,
  `status=complete|unfinished`, the full original Task Result `block`, and
  `evidence_event_ids`. Do not store just counters or `passed: true`.
- `action=inspect`, `mode=read_only`: before resume and group completion, read
  the same `tasks_file`/`journal_file` and reconcile retained reports with actual
  effects. Only independently established complete tasks enter `completed_tasks`;
  preserve unfinished results and resume only their uncompleted work.

Each implementation parent-supplied native observation carries `event_id`, `tdd_unit`,
`stage=red|green|refactor`, actual `argv`, integer `exit_code`,
`classification=assertion_failure|test_pass|infrastructure`, contained
`output_path`, `output_sha256`, and `snapshot_sha256`. Complete implementation
units require distinct ordered RED/GREEN/refactor events for the same focused
command: assertion-failure/nonzero RED, test-pass/zero GREEN and refactor.
Shared TDD-unit tasks share status and evidence references; no test-only GREEN.
For research or orchestrator-direct tasks, the frozen route derives
`tdd_not_applicable_reason`; workers cannot supply that reason or change the
route. Their independent native observation instead has `event_id`, `tdd_unit`,
`stage=task_result`, `task_id`, `outcome=completed`, `output_path`, and
`output_sha256`. Retain the full result block and never fabricate RED/GREEN/refactor
for non-TDD work. This event cannot complete an implementation task.
Workers supply their result blocks, never the independent native observations.

Missing, duplicate, reordered, stale, or invalid evidence blocks recording;
never discard earlier reports to make a record pass. An unfinished report is
persisted with `helper_exit_code=1` and `disposition=checkpoint_required`.
On a partial batch's later report, carry every previously complete task's block
and evidence references unchanged; identical native observations may be carried
only for those completed tasks. Resume unfinished work without replaying them.
Changed definitions require explicit parent reconciliation: a successor journal
names `prior_journal_file`, `reconciliation_event_id`, and
`reconciliation_reason`, preserving the old journal unchanged. Its new reports
start empty; prior evidence is linked, not manufactured as new completion.
Retained lineage must remain present and byte-identical to its recorded hashes;
missing, changed, cyclic, or excessive history blocks inspect and record. Do not
delete or rewrite prior journals to make reconciliation pass.
The journal always reports `native_qualification=pending` and
`authorization_granted=false`: JSON validation and synthetic fixture success
cannot authenticate native events or authorize continuation on their own.

## Required proof once per unchanged snapshot

Use focused tests per behavior and one independent review per completed
capability group. Review requirement-linked defects at every severity,
security/authorization boundaries, and demonstrated regression risk; style
suggestions are separate and do not trigger repair. Final integration review
is Post Code Review; no later step reviews unchanged code a second time.

After all producing changes and artifact regeneration, execute the complete
required suite and artifact checks on the final immutable input snapshot.
Use `execute-verification`, operation `execute-verification`, `mode=apply`, with
`workflow_file`, `command_id` selecting an existing PROJECT_COMMANDS slot, and
`expected_run_id` plus `dispatch_id` from an existing execution-control
`kind=verification` reservation; also pass the returned `ledger_path` when
needed for resume/relocation. The wrapper begins its reserved dispatch
atomically; do not pre-call `begin-verification` or invoke the wrapper twice.
After the actual execution result, record its completion in the same ledger;
unknown outcomes retain no-relaunch accounting. Dry-run need not reserve work.
Persist discovered commands once in the workflow's unique `## PROJECT_COMMANDS`
section as a fenced JSON command object. Do not supply arbitrary caller argv
or convert unsupported compound shell commands into a different check.
For an existing result, call `validate-execution-record`, operation `validate-execution-record`,
`mode=read_only`, with `workflow_file`, `record_path`, and `command_id`.
Pass `native_observation` from the actual host execution event: the returned
`observation_material` plus that genuine event's `native_event_id`. Independently
recover the event on resume; never reconstruct it from a receipt or worker text.
G7 and Post may consume the same result only when this validator proves reuse.
`reusable=false` requires execution, not relabeling a worker summary as proof.
The current `copy_only` wrapper is not a qualified native producer; even a
successful copied check is `reusable=false`. Preserve ordinary required checks
until an independently qualified native mode exists, and report this reuse
qualification gap rather than claiming the performance acceptance target.

The default Docker `docker-verification-record/v1` remains non-reusable.
Supply `docker` with explicit `executable`, local Unix
`endpoint`, digest-pinned `base_image`, and `output_contract="streams_only"`.
It retains stdout/stderr, not generated file artifacts. It does not provide a
macOS guest or replace native Claude/Codex qualification.

For Git-dependent checks, additionally supply `git_snapshot` with canonical
absolute `common_directory` and `worktree_directory` paths. These must match
the source repository's actual Git layout; no implicit directory discovery or
host global configuration inheritance is authorized. The
`git-readonly-metadata/v1` profile copies original objects, refs, config, HEAD,
and index bytes into the isolated image, binding their source locations and
modes in the evidence. Source and Git inputs share one size/entry limit;
changes detected at the post-run recapture invalidate `inputs_unchanged`.
Dry-run reports the selected profile without contacting Docker.

This is a limited relocation profile, not a complete Git environment: hooks,
external tools, reflogs, linked-worktree topology, and nested repositories are
not captured. Known unsupported inputs (including alternates, shallow/split
indexes, per-worktree refs, includes, and credential-bearing configuration)
are refused. A caller requiring omitted behavior must use ordinary native
verification. Private contexts and Docker build caches may retain supplied
source and Git history; only owned containers and image tags are cleaned up.

For a new qualification attempt, explicitly add
`qualification_profile="docker-qualified/v2"` inside `docker` and supply
`git_snapshot`. The separate `docker-verification-record/v2` contract requires
a hermetic Git snapshot and binds two identities: `execution_closure_sha256`
for the completed execution, and `revalidation_input_sha256` for inputs that
must still match at each consumer. Never upgrade a v1 record or relabel its
isolation mode; missing historical observations require a new execution.

The v2 evidence must include source/Git snapshot readback before and after
execution, image/platform and command bindings, Docker client/daemon/runtime
identities, the trusted launcher's initial init/toolchain/confinement
observation, fixed environment, retained streams, and ordered execution events.
The hermetic Git profile refuses hooks, configuration includes, unsupported
repository layouts, and omitted host behavior; it does not assert equivalence
to an arbitrary host Git environment. The daemon is a trusted execution
dependency, not a cryptographically attested host or macOS guest.

The v2 profile fixes hostname, DNS settings, and the selected runtime. It also
requires the qualified byte hashes of Docker's injected `/etc/hostname`,
`/etc/hosts`, and `/etc/resolv.conf`, with no workload write access. A Docker
version that renders different bytes is unsupported until separately qualified;
network isolation alone does not make these inputs interchangeable.

The producer still returns `reusable=false`: retain its `observation_material`
directly from the actual orchestrator-issued execution result, with its genuine
`native_event_id`, independently of the saved record and evidence files.
Both G7 and Post pass that same independently retained observation to
`validate-execution-record`; each must revalidate current inputs, retained
evidence, and current Docker dependencies. Missing runtime qualification
requires rerunning, as do changed bindings, malformed evidence, or unavailable
Docker. Unit fixtures and native event provenance alone do not establish
runtime qualification. Do not replace missing observations with caller claims.

Reuse binds exact command, toolchain, environment, all source/test/config
inputs, isolated build outputs, and orchestrator-issued producer evidence.
A content hash or worker `passed: true` is insufficient. Missing input coverage,
changed inputs, failed checks, absent process/native producer attestation, or
unresolved findings require rerunning affected checks; broaden if impact is
unknown. No general cache or daemon is introduced. Review edits invalidate
affected evidence before PR emission. Preserve G0 test counts as diagnostics;
require meaningful behavioral coverage, not count growth or redundant tests.

Keep all required gates and truthful manual-UAT status. Timing targets are
qualification outcomes, never grounds to skip requirements or mark a partial
implementation complete. Keep model and reasoning defaults unchanged.
