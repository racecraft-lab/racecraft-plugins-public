Priority: major

## Summary

The autopilot phase coverage report schema sets additionalProperties false and names 14 fields, but build_report emits 19 further *_errors keys. A real report therefore fails its own schema. The only test reads two schema keys and never validates a report.

## Evidence

- **autopilot-and-agents-005** (major): The report schema sets additionalProperties false and names 14 fields, but build_report emits 19 further *_errors keys (workflow_authority_errors, autonomy_boundary_errors, state_privacy_errors and others). A real report fails its own schema. The only test reads two schema keys and never validates a report against it.
  - `tests/speckit-pro/unit/fixtures/mutation-helpers/contracts/autopilot-phase-coverage-report.schema.json:5`, `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:5165`, `tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3657`

## Proposed fix

- autopilot-and-agents-005: Add the missing keys (or drop additionalProperties) and validate a real build_report output against the schema in the test.

## Acceptance

- [ ] A regression test that fails before the fix validates a real build_report output against the schema.
- [ ] The schema and build_report agree.

## Related

- Overlaps files changed by the open stop-policy stack: #850, #852. Land after that stack merges.
- Overlaps files changed by open PR #685.

Found by the 2026-09 coherence audit.
