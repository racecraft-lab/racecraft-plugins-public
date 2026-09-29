# SPEC-850 Workflow

## Gate Status

| Gate | Status | Note |
| ---- | ------ | ---- |
| G3 (after Plan) | passed | |
| G4 (after Checklist) | failed | 3 `[Gap]` markers remain after the repair loop |
| G5 (after Tasks) | pending | depends on G4 |

## Checklist Results

- spec.md: `[Gap]` FR-004 has no acceptance scenario.
- spec.md: `[Gap]` FR-007 names no measurable threshold.
- plan.md: `[Gap]` the rollback path has no owner.

## Ready Units

- T021 Add the export header parser (independent of G4)
- T022 Add the export footer parser (independent of G4)
- T023 Generate tasks from the checklist (depends on G4)
