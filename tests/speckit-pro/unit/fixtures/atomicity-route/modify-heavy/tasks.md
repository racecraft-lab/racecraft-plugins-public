# Tasks: Tidy up the orders schema

This change modifies existing behavior rather than adding new capability. No
hard-atomic signature, no proven additive seams — it edits what is already there.

- [ ] T001 UPDATE every existing `orders` row to backfill the new status value in
  `db/migrations/0042_backfill_status.sql`.
- [ ] T002 DROP the deprecated `legacy_total` column from the orders table.
- [ ] T003 DELETE the stale rows flagged by the cleanup job.
- [ ] T004 Relax the `orders_total_positive` CHECK constraint on the table.
