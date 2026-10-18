# PR 1370: harm-halt repair

The main merge retains both `may_end` and `publication_pending`, plus every
pre-existing test from either parent. Generated payloads and references were
regenerated from the merged sources.

The repair closes the two findings on the previous reviewed head:

- `R1370-5cb5aeb8`: runner entry checks the standing halt before gates dispatch,
  including `payload-gate` / `payload-completeness` / `apply` with `apply_dist`.
- `R1370-34b45e54`: sweep isolation failure persists the harm halt before
  returning. Recoverable GitHub observation failures remain recoverable.

The follow-up spec note about printing the record is addressed in the shared
phase reference: read the existing `harm-halt` helper in `read_only` mode and
print its reason, redacted evidence, and last safe state before the stop marker.

## Review repair at the runner seam

- `F1370-b9241f5a`: a standing halt uses an explicit pure-read allowlist,
  rather than treating `read_only` or `dry_run` as evidence of no side effects.
  Sweep capture, launch, acceptance and close are refused before dispatch.
- `F1370-f201596b`: halt publication reuses the execution-control exclusive
  ledger lock and atomic JSON writer. A concurrent second trigger is refused;
  the first reason and evidence remain intact, including same-reason races.
  An interrupted publication lock, unsafe ignore-marker directory, or regular
  file occupying the halt directory also refuses dispatch and resume.
- `F1370-06475426`: agent `clear` requests remain refused. ADR 0004 removes
  operator-event paths; the remaining `execution_control._operator_event`
  validates a caller-supplied event shape, run binding and single use. It does
  not authenticate a human halt-clear signal. Other owner decisions likewise
  carry observations supplied by the orchestrator. None can safely authorize
  halt clearance from attacker-controlled repository content, so no new trust
  channel or reason-as-authorization substitute was added. Human inspection
  outside the agent runner remains necessary.
- `R1370-9009d152`: ordinary process timeout, launch failure and non-zero exit
  return `sweep_process_failed`; TTL expiry returns `sweep_session_expired`.
  Both refuse that sweep attempt without recording tampering. The parent also
  revalidates its private session after a zero-exit worker and before decoding
  its output, so expiry during either host launch remains recoverable. Boundary failure
  and invalid, replayed or cross-session receipts retain the halt.
- `R1370-126d65ed`: payload requests check the same root the payload gate uses,
  including invocation beneath a nested `.specify` fixture.
- `R1370-4403eb13`: sweep state effects propagate into `writes_state`, including
  an isolation-failure halt record.
- `R1370-eddc3522`: an unreadable prior record remains untouched and the sweep
  returns the closed isolation failure with `halt_record_status: unavailable`.

The halt module remains the deep policy module: runner and helper dispatch use
its refusal at the public request seam. The launchers classify operational
failures where they originate; the receipt owner classifies expiry. Both host
payloads render the same guidance and ship the same Python policy. No skill
entrypoint, agent source or Codex-only overlay changed in this repair, so no
trigger-eval draft requires rebinding.

## CI regression repair

The earlier halt guard also runs before read-only helpers. Path-inspection
errors now retain `internal_failure`, while an actual standing halt reports
`expected_failure`; both refuse before dispatch. This preserves the existing
phase-brief symlink boundary contract without weakening it. Informational
Claude attestation is a pure preflight: an unavailable boundary there reports
its closed reason without persisting a halt. Capture and launch boundary
failures still persist one. This prevents the read-only helper fixture from
leaving a halt that contaminates later G0 probes.

## Human recovery

Agent clearance remains refused. After resolving the cause, a human outside the
agent workflow inspects and preserves the redacted record, confirms no halt
publisher is live, then removes `.specify/harm-halt/halt.json` and any abandoned
`.specify/harm-halt/halt.lock` directory. Removing only the record leaves an
abandoned publication lock blocking resume. An unsafe
`.specify/harm-halt/.gitignore` directory must also be repaired into the runner's
regular ignore marker. A regular file occupying `.specify/harm-halt` must be
restored to a directory after inspection. Agents leave this recovery to the human; no repository field or reason string authorizes it.

## Known limits

- A failed Claude worker can leave an attestation file in the separate,
  owner-controlled sweep-hook store when failure precedes the explicit unlink.
  `TemporaryDirectory` removes the runtime directory, not that attestation file.
  The attestation name hashes the random runtime path, so it cannot authorize a
  future invocation with a different runtime path. The surviving file is a
  bounded cleanup limit, not reusable evidence for another invocation.
- The pure-read allowlist is manually audited policy, not a general filesystem
  sandbox for future helper implementations. The six current entries read
  registries or supplied/local text and return derived values; adding an entry
  requires verifying its code path. The static test graph does not prove this
  property for arbitrary future changes.

- The standards re-review noted that `SchemaViolation` has no `reason`, so an
  invalid capture or receipt request can also take the isolation fallback and
  persist a halt. Informational attestation instead reports its readiness gap. Examples are an unknown capture surface or an unsupported receipt
  stage. This is a conservative refusal, with explicit human clearance; it
  neither bypasses the halt nor loses evidence. The supported orchestrator
  sends exact closed request shapes; reviewer prose cannot select these
  trusted request fields. A malformed direct caller can reach this limit.
  The earlier guidance already classified this fallback as the isolation halt.
  Separating invalid caller requests from invalid worker evidence would change
  that existing classification contract, so this repair retains it.
- The passive halt reader treats a directory-shaped ignore marker as unsafe,
  including a symlink to a directory. The existing directory writer can repair
  that link. Supported writers create a regular ignore marker; only manually
  altered local state reaches the difference. The reader fails closed and
  leaves repair to human inspection rather than changing state during a read.
- The architecture advisory flags `gates/payloads.py` importing `runtime.py`.
  This edge exists unchanged on main. No architecture baseline or quality
  acknowledgment was changed to suppress it.
- Linux VM coverage excludes the two real macOS sandbox tests named in the PR
  verification reply. The orchestrator owns those tests and macOS plugin CI.
- `apply_refusal` returns no refusal when the runner cannot resolve the
  repository root. Every dispatch path then rejects the same request for that
  root, so no write follows.
- `apply_refusal` repeats the payload gate's root rule
  (`path_utils.find_repo_root(Path.cwd())` for `payload-gate`) rather than
  asking the gate. The architecture rules keep helpers from importing gates,
  and the rule itself already lives in core `path_utils`. The two roots differ
  only under a nested `.specify` fixture inside the source checkout; in a
  consumer repository the source-checkout resolver returns nothing and the
  payload gate answers `missing_prerequisite`.
- A `dry_run` request with `action` `clear` validates and returns the record
  with `halted: true` and `resume: "refused"`. It clears nothing and claims no
  clear would succeed; the `apply` request is refused.
