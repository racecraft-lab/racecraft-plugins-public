# Feature Specification: UAT Runner Fixture

## User Scenarios & Testing

### User Story 1 - Generate a runbook (Priority: P1)

The operator receives a source-derived acceptance runbook.

### Edge Cases

- The workflow has no existing runbook.

## Requirements

### Functional Requirements

- **FR-001**: The runner MUST generate the runbook before PR-body generation.

## Rollback

Revert the helper promotion commit.
