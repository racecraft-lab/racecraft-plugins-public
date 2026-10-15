# Nesting preflight state

Issue #1358: the nesting preflight answer reached `autopilot-state.json` only
as a hand-made copy, so a two-field `{mode, reason}` record dropped
`nesting_mode.data.mode` and the canary receipt fell back to `mode: flat`.

## Rule

`resolve-nesting-mode` in `apply` mode resolves the probe and writes the
complete runner envelope as `nesting_mode` in the run's existing state file,
preserving every other field. `read_only` mode is unchanged.

`state_file` must be a repository-relative path outside `.git` whose file name
is `autopilot-state.json`, and that file must already hold a JSON object. The
write refuses symlinks, paths that leave the worktree, and a file that changed
since it was read. Every refusal answers `input_error` with
`nesting_state_invalid` and leaves the file as it was.

The `status-evidence` rule rejects a `nesting_mode` that lacks
`data.schema_version == "nesting-mode/v1"` or a `data.mode` in the receipt
enum. A state without `nesting_mode` still passes, since records written before
the preflight omit it.

## Known limits

Accepted at cross-host review. These do not reach the changed code on real
runs, or fail closed when they do.

- **Third state read-modify-write.** `persist_nesting_mode`,
  `formal/lifecycle.py` `mirror_checkpoint`, and `plan_stage_terminal.py`
  `record_pull_request` each read and rewrite `autopilot-state.json`
  (AGENTS.md hard invariant 2). Consolidating them changes the other two
  callers' behavior (stale-write refusal, atomic rename), so it is the
  builder's follow-up as its own commit.
- **State file next to the workflow.** The runner checks the file name, not
  that the file sits beside the workflow, because the apply request carries no
  workflow path. Only the orchestrator supplies `state_file`, from the path it
  created in Step 1.
- **UUID request ids.** The persisted envelope keeps `request_id`. A raw UUID
  there fails `state_privacy_errors`. Skill guidance uses slug ids, and the
  failure is closed: the run's own validator stops it.
- **Write races.** A concurrent writer or a failed rename also answers
  `nesting_state_invalid` ("correct state_file and retry"). A retry succeeds,
  so the misleading remediation costs one extra call.
- **No size cap on the state read.** The state file is the run's own record,
  written by the runner and the orchestrator.
- **Retry wording.** Step 1.5 says to repair the state file and retry. A state
  file the runner cannot write would also break every later step, so the
  retry has no separate bound.
- **Live canary.** The receipt reader of `nesting_mode.data.mode` lives in
  the external canary harness. The next Claude Code canary must confirm the
  receipt has no `mode.not_observed`.
