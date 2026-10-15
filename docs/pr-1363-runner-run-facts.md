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
- **Hook snapshot errors fail open.** An unreadable ledger or a mirror without
  `run_id` makes the hook return no decision. This matches the hook's
  documented fail-open policy.
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
