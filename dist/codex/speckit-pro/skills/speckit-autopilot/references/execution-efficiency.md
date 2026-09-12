# Bounded Execution and Verification

Read at kickoff/resume and before Tasks, implementation dispatch, corrective
work, or final verification. This shared contract governs both native hosts;
it does not replace their dispatch, authorization, or mandatory gate rules.

## Durable run budget

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

- `start`: open or recover the same workflow's ledger before the first phase.
  Pass `inputs.spec_file` as the resolved repo-relative feature spec path when
  available; the workflow can live elsewhere. If omitted, only an existing
  adjacent spec can supply requirement IDs, otherwise failures use `unresolved`.
  The registry freezes at start; later paths or contents never reset counters.
  Agent replacement, compaction, stage changes, a reclaimed state mirror, and
  resume never reset it. Preserve another workflow's ledger when reclaiming
  the one-run `autopilot-state.json` mirror.
- `reserve`: before each native dispatch or command, supply `dispatch_id` and
  `kind=implementation|corrective|verification|infrastructure`. A corrective
  dispatch supplies `failure_invariant`: a stable approved requirement or
  invariant ID. Unknown mappings share `unresolved`; changed wording, task IDs,
  agents, and commits are not new families.
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
- `checkpoint`: persist the 45-minute completed-work marker without resetting
  the slice, run, or repair budget. `pause`/`resume` excludes only human-UAT or
  external-approval waits with independent parent `native_observation` carrying
  `native_event_id`, `run_id`, `kind=human_uat|external_approval`, and
  `action=wait_started|wait_ended`. Resume additionally requires
  `wait_start_event_id` matching the active start and a new, unconsumed
  `native_event_id`; replayed events cannot exclude time twice. A worker's
  assertion is insufficient.

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
are the shared ceilings. Reserve before repairs in G3 provenance, G4/G6
remediation, review, formal checks, or hardening. Pass the parent's
`reservation_id` to nested work on the same failure; a nested loop has no
independent allowance. A rejected candidate or failed repair does not create
a new family. Pure read-only diagnosis may continue inside the time budget.

Check `status` before advancing and while waiting. `checkpoint_due` calls for
a completed-work checkpoint at 45 minutes; the slice ceiling is 90 minutes
and the full automated-run budget is 120 minutes. Include startup, tools,
model waits, repairs, tests, artifacts, and automated review in elapsed time.
Only separately evidenced human-UAT/external-approval waits are excluded.
If `disposition=checkpoint_required`, stop new work and record remaining work,
owned in-flight dispatches, unknown effects, consumed reservations, elapsed
time, and the required operator decision. Never call this completion or a
successful runtime measurement. Keep existing run status `in_progress` or
`awaiting_review` as applicable and mirror the execution-control disposition;
do not invent a top-level status. Independent approved work can continue only
when the helper permits it within the remaining budget.

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
  than inventing fresh batch IDs. Dry-run previews do not persist it.
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
The journal always reports `native_qualification=pending` and
`authorization_granted=false`: JSON validation and synthetic fixture success
cannot authenticate native events or authorize continuation on their own.

## Required proof once per unchanged snapshot

Use focused tests per behavior and one independent review per completed
capability group. Review requirement-linked defects at every severity,
security/authorization boundaries, and demonstrated regression risk; style
suggestions are separate and do not trigger repair. Final integration review
is Post Code Review; Post Self-Review reconciles that review and required
evidence, not a second independent review of unchanged code.

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
