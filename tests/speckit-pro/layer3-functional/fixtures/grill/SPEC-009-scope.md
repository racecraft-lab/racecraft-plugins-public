<!-- fixture-kind: deterministic-synthetic-testdata; this is authored setup input, not a real roadmap scope or live evidence. -->

# SPEC-009 Search & Database Scope

This synthetic scope is the immutable setup input for the `grill-me` setup-mode
evaluation. It is materialized in the registered child worktree before the
foreground interview.

## Goal

Provide searchable project records with deterministic indexing and query
behavior for the first release of Search & Database.

## In scope

- Define the searchable record fields and supported query operators.
- Specify indexing and re-indexing behavior for created, updated, and deleted
  records.
- Define result ordering, pagination, and behavior when no records match.
- Record the operational and data-integrity constraints that the implementation
  must satisfy.

## Out of scope

- Replacing the application's primary database.
- Adding an administrative search UI or a new authentication system.
- Choosing a vendor or implementation library before the design decisions are
  resolved.

## Known questions for the interview

- Which fields and operators are required for the first release?
- What consistency delay, if any, is acceptable after a record changes?
- Which result ordering and pagination rules should users observe?
