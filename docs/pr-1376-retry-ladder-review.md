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
  recovery additionally requires the runner-recorded reconciliation; a caller's
  `interrupted=true` flag on its own cannot discard an unknown dispatch.
