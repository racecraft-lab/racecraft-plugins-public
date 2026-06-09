# Tasks: Fix the counter data race

This change fixes a concurrency defect, so a green CI run does not prove it is
releasable. It is not a hard-atomic class on its own — its route is decided by the
other detectors — but releasability must be flagged. The fix is a concrete action
on shared state, not a topic mention.

- [ ] T001 Fix a data race on the shared request counter in
  `src/metrics/counter.ts` by switching the increment to a compare-and-swap (CAS).
- [ ] T002 Resolve the deadlock between the flush and rotate paths in
  `src/metrics/flusher.ts`.
