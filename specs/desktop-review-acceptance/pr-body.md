# Issue #571 desktop artifact-review acceptance fixture

> **DO NOT MERGE — disposable evidence fixture.** This draft PR exists only to
> exercise the shipped artifact-review delivery and resume contract.

## Scope

This fixture carries a small seeded planning record and four filled draft-stage
gallery pages: implementation plan, spec explainer, code approaches, and module
map. `architecture-viewer` is recorded as a planned-template gap because the
active manifest has no shipped template for it.

The planning files are **seeded test preconditions**, not evidence that the
full SpecKit phases ran. Generation, rendered preview, human approval, and UAT
are separate gates.

## Verification boundary

- Generation is validated from actual page/template/input bytes and by the real
  `resolve-autopilot-stage` operation.
- Preview dispositions begin pending and will be updated only from parent-owned
  rendered observations.
- Human approval and manual UAT remain pending.
