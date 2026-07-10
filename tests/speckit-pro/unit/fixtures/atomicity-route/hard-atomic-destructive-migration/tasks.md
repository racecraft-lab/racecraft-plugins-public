# Tasks: Collapse the legacy ledger tables

This change runs a destructive, irreversible schema migration, so it must land as
one atomic PR and is not provably releasable from a green CI run alone. The
destructive verb sits on the same task as its migration deliverable path.

- [ ] T001 [P] In `db/migrations/0091_collapse_ledger.sql` run `DROP TABLE legacy_ledger` and `DELETE FROM ledger_audit`.
- [ ] T002 [P] Add a new consolidated read model in `src/models/Ledger.ts`
  (a fresh additive surface).
- [ ] T003 [P] Add a new ledger summary panel in `src/components/LedgerSummary.tsx`.
