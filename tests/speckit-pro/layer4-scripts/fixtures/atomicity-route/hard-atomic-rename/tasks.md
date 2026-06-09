# Tasks: Rename the public client export

This change renames an exported public symbol, so it must land as one atomic PR
even though the rest of the work is a PROVEN additive multi-seam change (two
independent, purely additive surfaces) that US1 would otherwise route to split-PR.
The hard-atomic override must beat that split signal. The rename is a concrete
action with named operands, not a vocabulary mention.

- [ ] T001 Rename the exported symbol `createApiClient` to `makeApiClient`
  across the public package entrypoint in `src/sdk/index.ts`.
- [ ] T002 [P] Add a new client options store: `CREATE TABLE client_options` in
  the migration `db/migrations/0001_client_options.sql` (additive schema seam).
- [ ] T003 [P] Add a new usage example panel in
  `src/components/SdkExample.tsx` referencing the renamed export (additive UI seam).
