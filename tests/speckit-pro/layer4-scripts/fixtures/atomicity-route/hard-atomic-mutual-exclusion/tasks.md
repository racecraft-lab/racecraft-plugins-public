# Tasks: Add single-writer protection to checkout

This change introduces a mutual-exclusion primitive guarding payment writes, so it
must land atomically — a partial rollout would expose an unsafe double-charge
window. The primitive is introduced as a concrete action with a named target.

- [ ] T001 [P] Introduce a distributed lock around the checkout writer in
  `src/payments/checkout.ts` so only one auth holder can commit a charge.
- [ ] T002 [P] Add a new lease store table in `src/payments/lease.ts`
  (a fresh additive surface).
- [ ] T003 [P] Add a new contention dashboard panel in
  `src/components/LockStatus.tsx`.
