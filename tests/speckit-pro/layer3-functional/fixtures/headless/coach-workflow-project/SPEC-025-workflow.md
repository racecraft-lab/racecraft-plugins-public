# SpecKit Workflow: SPEC-025 — Project Activity Export

## Specification Context

| Field | Value |
|---|---|
| Spec ID | SPEC-025 |
| Name | Project Activity Export |
| Branch | `codex/spec-025-activity-export` |
| Dependencies | None |
| Priority | P2 |

## Feature Scope

A project member can export the project's activity entries as UTF-8 CSV. Each
row contains event_id, occurred_at, and summary. Exports include only the chosen
project's entries and preserve chronological order. An empty project produces
a header-only file. Scheduled exports and external storage are outside scope.

## Workflow Overview

| Phase | Command | Status |
|---|---|---|
| Specify | `/speckit-specify` | Pending |
| Clarify | `/speckit-clarify` | Pending |
| Plan | `/speckit-plan` | Pending |
| Checklist | `/speckit-checklist` | Pending |
| Tasks | `/speckit-tasks` | Pending |
| Analyze | `/speckit-analyze` | Pending |
| Confidence Gate | G6.5 | Pending |
| Implement | `/speckit-implement` | Pending |
| Post | Post-Implementation | Pending |

## Phase Inputs

### Specify Prompt

Specify the project activity export described above, including access to the
selected project, CSV columns, chronological ordering, and empty results.

### Clarify Prompt

Resolve ambiguous timestamp formatting and CSV quoting requirements.

### Plan Prompt

Plan the export endpoint, activity-record query, and CSV serialization for the
existing TypeScript service.

### Checklist Prompt

Review the export requirements for omitted cases and conflicting behavior.

### Tasks Prompt

Generate dependency-ordered tasks from the completed specification and plan.

### Analyze Prompt

Check consistency and traceability across the specification, plan, and tasks.

### Implement Prompt

Implement the approved tasks with their defined verification steps.

### Post Prompt

Review the implementation and prepare the required acceptance and review
artifacts after implementation is complete.
