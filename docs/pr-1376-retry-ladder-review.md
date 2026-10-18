# PR #1376 retry-ladder review notes

## Fixes

- R1376-85350741: a lost-session retry dispatch can settle as interrupted
  without a native result after the runner's `reconcile` marked it unknown.
  Ordinary unknown completion still requires independent native evidence.
- F1376-0b909cf8: loading a ledger replays failure freshness at each rung's
  reservation time, across current and archived epochs, using the same rule
  as live reservation. Future failures cannot justify earlier reservations.

## Known limits

- F1376-77586417 (Low): the caller already holds completion-reporting access
  and can assert an interruption on a reserved or running dispatch, or beside
  a matching native failure for an unknown dispatch. The runner cannot prove
  that the host actually stopped. This remains a reachable trust limit;
  it permits at most two dispatches per rung, six per check. The missing-result
  recovery additionally requires a recorded reconciliation; a caller's
  `interrupted=true` flag on its own cannot discard an unknown dispatch.
  The caller issues `reconcile` itself, though, and `reconcile` also accepts a
  dispatch the caller already completed as `unknown`. So `complete unknown`,
  then `reconcile`, then an interrupted `complete` settles without native
  evidence. That reaches the same state as interrupting the running dispatch
  directly, so it adds nothing beyond this limit, and the six-per-check bound
  holds. The pin test covers only the path without `reconcile`.
- Same-timestamp replay (Low): `_fails_again` keeps check evidence recorded
  at or before a rung's `reserved_at`. If a rung were reserved and a passing
  verification were then recorded at exactly the same clock reading, a reload
  would treat that later pass as earlier evidence and reject a ledger the live
  path wrote. (In the other order the live reservation sees the pass too and
  refuses, so live and reload agree.) Not reachable
  in practice: the two requests run in separate, lock-serialized invocations
  with fsync writes between them, so they cannot read the same `time.time()`
  float. A clock coarse enough to repeat a reading (Windows on Python below
  3.13) is the only plausible trigger.
