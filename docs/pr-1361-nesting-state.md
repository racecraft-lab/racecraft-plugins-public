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
since it was read. Input refusals answer `input_error` with `nesting_state_invalid` and
`data.writes_state=false`. Publication failures answer `internal_failure` with
`nesting_state_write_failed`; `data.writes_state` is true when publication or
cleanup may already have changed disk. Inspect the current state before retrying.

The apply request requires a nonempty `request_id` slug without a raw UUID.
The producer and the state privacy validator share the UUID pattern.
State reads are bounded to 1 MiB even if the file grows while being read. The `status-evidence`
rule requires every runner response field, including that ID, exact success
codes, empty diagnostics and a closed data shape. It replays the existing
nesting policy to reject contradictory mode, reason, host, depth and
prerequisite combinations. A missing schema fails closed for present nesting
evidence. A state without `nesting_mode` still passes, since records written
before the preflight omit it.

## Security evidence validation

Finding F1361-4313b190 concerns false verified state evidence. The schema
enforces completeness and types; the nesting policy owner checks semantic
consistency. Both host labels use that same validation seam. Regression tests
cover the minimal versioned envelope, every omitted response/data field,
forged codes and IDs, extra fields, invalid scalar/container types,
contradictory reasons and host-specific prerequisites. Actual persisted runner
outputs cover allowed, refused, absent and invalid probes, with depths zero,
three and absent. Configured depth remains observational, never a mode gate.

## Review fixes

- **R1361-6482de17:** `autopilot_state.update` owns the existing-object
  read/modify/write for nesting, formal checkpoint mirroring and draft-PR
  bookkeeping. It uses the existing shared snapshot-checked atomic writer.
  The extraction is behavior preserving; migration of the two older callers
  adds stale-write and unsafe-target refusal as a separate fix. A structural
  regression check fails if any of the three callers bypasses that owner.
- **R1361-ba5501be, R1361-67bded64:** the earlier filename guard and docstring
  fix are retained. Removing the filename guard reproduces the failing
  `package.json` refusal test before restoration.
- **R1361-de21c359, R1361-bbe7bcff, R1361-487e2115:** UUID-shaped request IDs
  fail before writing; publication failures report their actual category and
  possible write effect; snapshots have a bounded read.
- **R1361-28470c6c:** both rendered host skills permit one repair-and-retry,
  then return with the storage diagnostic before executing phases.
- **R1361-8f40809a:** the symlink test first requires a successful apply to a
  regular state file, so unsupported apply mode cannot satisfy the test.
- **R1361-f2b33bfb:** the Codex prompt's g0-setup clause now has a verb.

## Known limits

Accepted at cross-host review. These do not reach the changed code on real
runs, or fail closed when they do.

- **State file next to the workflow.** The runner checks the file name, not
  that the file sits beside the workflow, because the apply request carries no
  workflow path. Only the orchestrator supplies `state_file`, from the path it
  created in Step 1.
- **R1361-ca3045c0: mode-keyed dispatch.** `resolve-nesting-mode` is the only
  helper registered in both read-only and mutation tables; the explicit mode
  route leaves other helper dispatch unchanged.
- **R1361-873d242a: strict envelope version/status.** The schema also pins
  `schema_version=1.0` and `status=ok`. The producer emits those exact values;
  incompatible or failed responses are refused rather than treated as mode
  evidence.
- **R1361-bca8eb13: live canary.** The receipt reader of
  `nesting_mode.data.mode` lives in the external canary harness. The next
  Claude Code canary must confirm the receipt has no `mode.not_observed`.
  Local schema/producer tests cannot establish that external observation.
- **Local evidence is not authentication.** Complete, internally consistent
  JSON is not cryptographic proof of a runner invocation or nested spawn. A
  writer able to fabricate every field can reproduce a valid response; this
  gate rejects incomplete and contradictory evidence. Probe observation still
  comes from the orchestrator.
- **Literal backslashes and hard links.** On POSIX, backslashes name literal
  in-repository entries. A hard-linked state file is replaced atomically,
  leaving its other alias unchanged. Neither permits an outside write.

### Accepted at the cross-host re-review of d3d46ee3

These are Low or Info notes. Each fails closed or does not reach a wrong
result on real runs.

- **Formal mirror runs `state_path` twice.** `mirror_checkpoint` calls
  `state_path` and discards the result, and `formal/helper.py` already ran it.
  It is kept: it carries the beside-the-workflow check that
  `autopilot_state.update` does not make. The cost is one extra parse of a
  file capped at 1 MiB.
- **Read bound travels in the snapshot dict.** `byte_limit` is an optional
  key of the untyped snapshot. Only `autopilot_state.snapshot` sets it; every
  other caller omits it and keeps the unbounded read it had before.
- **Producer refuses only UUID request IDs.** The state privacy guard also
  rejects home paths. A `request_id` holding a home path would be written,
  then fail `status-evidence` closed. The skill asks for a run-specific slug.
- **Owner check is structural.** The AST test checks that each of the three
  callers calls `autopilot_state.update`. It does not prove that no other
  write of `autopilot-state.json` exists; review grep found none.
- **One repair-and-retry is prose only.** No test pins the retry count. A
  state file the runner cannot write also breaks every later state step.
- **Apply refuses an absolute `state_file`.** The skill asks for the
  repository-relative path, and the one allowed retry can correct it.
- **Commit shape.** f7481912 moves the formal and plan-stage callers onto the
  owner and adds their new refusals in one commit. History is not rewritten.
