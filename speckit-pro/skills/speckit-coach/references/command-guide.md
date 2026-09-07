# Spec Kit Command Guide

Use this reference to explain when an installed official Spec Kit command fits,
what artifact or result it owns, and how to recover when its prerequisites are
missing. This is coaching, not command logic.

## Read the active command first

Before giving version-specific instructions, inspect the command or skill that
is installed for the active host and project. Its definition owns exact inputs,
limits, files, hooks, and execution steps.

If the requested command is not installed or its definition cannot be read:

1. Give only stable conceptual help from this guide.
2. Say that version-specific mechanics could not be verified.
3. Do not invent paths, limits, flags, or outputs, and do not install or upgrade
   anything unless the user separately requests that lifecycle action.

For Autopilot gate questions, read the installed `speckit-autopilot` skill as a
reference only. Do not invoke or execute Autopilot while answering.

## Workflow shape

The normal core progression is:

```text
constitution → specify → clarify (as needed) → plan → checklist (as needed) → tasks → analyze (as needed) → implement
```

Treat Clarify, Checklist, and Analyze as conditional quality passes. A project or
installed Spec Kit version may expose additional commands; inspect their active
definitions rather than treating this sequence as a closed command catalog.

Do not advance around a missing prerequisite or failed gate. Name the artifact
or evidence that must change, route back to its owning command, and re-check the
active definition before continuing.

## Common command responsibilities

This table is a conceptual router, not an exhaustive command inventory.

| Command | Use it for | Primary result or recovery direction |
|---|---|---|
| Constitution | Establish or amend testable project governance. | Update the live constitution; use the [constitution guide](./constitution-guide.md) for amendment decisions. |
| Specify | Capture user outcomes, requirements, acceptance criteria, and scope without inventing implementation design. | Produce or repair the feature specification before planning. |
| Clarify | Resolve material ambiguity in a specification instead of guessing. | Record decisions in the specification; return to Specify when the capability boundary itself changed. |
| Plan | Make the technical design, contracts, and constitution alignment explicit. | Produce or repair the implementation plan and only the supporting artifacts required by the active command. |
| Checklist | Test whether requirements are complete, clear, consistent, measurable, and scenario-complete. | Produce a requirement-quality checklist; use the [checklist domains guide](./checklist-domains-guide.md) to choose evidence-based focus areas. |
| Tasks | Turn accepted design artifacts into dependency-ordered, independently verifiable work. | Produce or repair the task list while preserving its active marker format. |
| Analyze | Check the specification, plan, and tasks for conflicts, gaps, and missing coverage. | Return a read-only report; repair the named source artifact before rerunning. |
| Implement | Execute accepted tasks while respecting their dependencies and project verification rules. | Update implementation and task state; do not treat partial or failed evidence as completion. |
| Issue export or another installed command | Perform only the behavior declared by its active definition. | Confirm external writes before creating or changing remote records; report missing capability rather than substituting another command. |

## Coaching rules

- Keep user outcomes and acceptance criteria in the specification; keep technical
  decisions in the plan.
- Preserve identifiers and traceability markers defined by the active artifacts.
- A Checklist evaluates requirements, not whether implementation works.
- Analyze is read-only. Do not turn an explanation of its findings into an
  unapproved edit.
- Report the artifacts inspected, what changed, checks actually observed, and
  unresolved evidence. Never infer that a command or gate passed.
