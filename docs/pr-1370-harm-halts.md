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

## Aborting publisher repair

`F1370-7a04641b` is the class **halt persistence fails open after a competing
writer aborts**. The halt module validates every record field before acquiring
the ledger lock. A validated publisher opts into retaining that lock on any
exception, including a failed write or an interruption after atomic replacement.
Other ledger clients retain their existing cleanup behavior. A contending stop
therefore has a record or a lock that survives the competing writer's failure.
The reader also treats a dangling lock symlink as unsafe.

Plan-stage reports `halt_record_status: recorded` after publication and
`blocked` when a record, publication lock, or unsafe storage path refuses it.
It retains the real tamper report and stops before any commit or GitHub action.
Both hosts use the same Python policy; generated Claude and Codex payloads carry
it without changes to skill sources, agents, or overlays.

Each test below exercises both host request shapes in
`tests/speckit-pro/unit/test-plan-stage-terminal.py`:

| Review variant | Test |
| --- | --- |
| Malformed competitor (`last_safe_state: 17`) | `test_malformed_competitor_cannot_discard_the_independent_tamper_halt` |
| Valid competing publisher wins first | `test_valid_competitor_keeps_first_evidence_and_resume_refusal` |
| Persistent lock appears after precheck | `test_lock_appearing_after_precheck_keeps_resume_refused` |
| Record symlink appears after precheck | `test_symlink_appearing_after_precheck_keeps_resume_refused` |
| Storage controller removes or renames a lock or symlink | `test_storage_controller_can_remove_lock_or_symlink_after_the_stop` |
| Invalid plan reason or non-text state is unreachable | `test_real_plan_stop_supplies_registered_reason_and_text_state` |
| Valid competitor aborts publication | `test_aborting_valid_competitor_leaves_durable_resume_refusal` |
| File-shaped lock, live/dangling lock links, live record link | `test_linked_or_non_directory_locks_and_live_record_links_refuse_resume` |

`tests/speckit-pro/unit/test-harm-halt.py` additionally checks all input fields
before storage is touched (`test_invalid_trigger_fields_are_rejected_before_storage_is_touched`),
ValueError, OSError, and interruption before/after atomic publication
(`test_aborted_publication_keeps_a_blocker_for_every_failure_window`), and a
dangling lock without touching its target
(`test_dangling_publication_lock_refuses_resume_without_touching_its_target`).
The regressions were run red against the unfixed implementation before repair.
Safe and unreachable variants were red on the new explicit persistence report;
the malformed and aborting competitors were red on missing resume refusal.

Both independent review axes completed without a blocking finding. The
standards review's conditional test-discovery concern was checked against the
actual module loader: plan-stage uses `loadTestsFromModule`, while harm-halt's
explicit `build_suite` includes the new class. The red run named every new
variant, and the final rerun counted 242 plan-stage checks and 41 halt checks.
The sweep writer uses the same `record_halt` owner with constant nonempty
evidence and formatted text state. Generated-artifact consistency and direct
source/payload byte comparisons verify both hosts.

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

- A sequential duplicate trigger also retains its acquired lock when it finds
  an existing record. This conservative refusal preserves first evidence;
  human recovery removes the record and any retained lock together.
  Superseded by #1378 (`docs/pr-1378-harm-halt-clear.md`): a trigger refused
  because a readable halt already stands now releases its lock, so the owner's
  clear token still works.
- The public halt helper repeats the evidence text check before calling the
  publisher, which validates all record fields. Both use the same
  `strict_input.require_text` primitive, so no validation policy differs;
  the extra call is a bounded maintenance repetition.
- Sweep isolation retains its existing `halt_record_status: unavailable`
  vocabulary, while plan-stage reports `recorded` or `blocked`. These are
  reporting fields, not authorization or resume inputs; both paths use the
  same publisher and halt reader. No consumer uses these strings to permit
  dispatch.
- An OSError in plan-stage's own halt publication can still propagate instead
  of preserving the stop report. That reporting behavior predates this repair;
  the newly retained lock now refuses subsequent dispatch. Publisher tests
  cover OSError before and after atomic publication; the plan-stage race test
  also covers OSError in a competing publisher.

- An actor who can delete or rename halt storage can remove a lock or record
  symlink after the stop and permit later dispatch. That actor already controls
  the same path used for the record itself. Both removal and rename are tested;
  defending against an actor with direct storage control is outside this fix.
- Plan-stage cannot supply an invalid harm reason or non-text safe state on
  the real tamper path: its reason is a registered constant and its state is
  formatted from the initial HEAD. The real stop test verifies those values;
  the publisher separately rejects malformed direct callers before locking.
- Failure before lock acquisition cannot provide a durable halt when storage
  itself cannot be created (for example, a permission or disk failure). This
  environmental limit predates the repair. Once the lock is acquired, every
  publication failure leaves it blocking; a concurrent refusal no longer relies
  on another writer succeeding.

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
