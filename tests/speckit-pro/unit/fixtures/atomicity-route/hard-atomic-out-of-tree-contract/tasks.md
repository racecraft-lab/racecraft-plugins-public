# Tasks: Break the public v2 orders contract

This change makes a breaking change to a versioned, out-of-tree API contract that
external consumers depend on, so it must land atomically. The break targets a
concrete versioned path with a real version number.

- [ ] T001 [P] Remove the deprecated `total` field from the public response in
  `src/app/api/v2/orders/route.ts`, a breaking change to the external contract.
- [ ] T002 [P] Add a new pricing breakdown module in `src/orders/pricing.ts`
  (a fresh additive surface).
- [ ] T003 [P] Add a new order detail panel in `src/components/OrderDetail.tsx`.
