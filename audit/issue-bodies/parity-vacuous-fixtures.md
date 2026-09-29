Priority: blocking

## Summary

Layer 7 parity fixtures 02 and 03 compare only tables from the input workflow.md, which the runner copies unchanged into both output directories. Neither declares required_invariants, so a live run passes even when autopilot does nothing. No compared value comes from a shipped skill, registry or runner, so both fixtures are checks that pass on nothing.

## Evidence

- **parity-layer7-001** (blocking): Fixture 02 compares only tables in the workflow.md that run_path copies unchanged into both output dirs, and it declares no required_invariants. Live mode passes when autopilot does nothing, and no compared value is read from a shipped skill, registry, or runner. The audit doc already calls the removed parity policy tasks vacuous reimplementations.
  - `tests/speckit-pro/layer7-parity/02-repository-migration-guidance/workflow.md:35`, `tests/speckit-pro/layer7-parity/02-repository-migration-guidance/expected-equivalence.json:5`, `tests/speckit-pro/layer7-parity/run-parity-fixtures.py:664`, `tests/speckit-pro/layer7-parity/run-parity-fixtures.py:409`
- **seam-003** (blocking): Parity fixture 03 has the same defect as parity-layer7-001 (fixture 02). It compares only table columns of the input workflow.md, which run_path copies unchanged into both output directories, and it declares no required_invariants, so live mode passes when autopilot does nothing. parity-layer7-001's fix names only fixture 02, and parity-layer7-006 missed fixtures 03 and 04 because it counted two tracked fixtures where four exist.
  - `tests/speckit-pro/layer7-parity/03-reviewability-backstop-parent-child-routing/expected-equivalence.json:5-34`, `tests/speckit-pro/layer7-parity/03-reviewability-backstop-parent-child-routing/workflow.md:27`, `tests/speckit-pro/layer7-parity/run-parity-fixtures.py:409`, `tests/speckit-pro/layer7-parity/run-parity-fixtures.py:694-696`

## Proposed fix

- parity-layer7-001: Retire fixture 02 from the legacy runner (the native parity.02-scaffold-relocation-guidance case covers the surface), or compare artifacts a run must produce and derive the values from the skills and registry.
- seam-003: Retire fixture 03 from the legacy runner or compare artifacts the run must produce, and make the runner reject a fixture whose every compare source is the copied workflow.md unless required_invariants is declared.

## Acceptance

- [ ] A regression test in test-parity-runner.py that fails before the fix: a fixture whose every compare source is the copied workflow.md, with no required_invariants, is rejected.
- [ ] Fixtures 02 and 03 are either retired from the legacy runner or compare artifacts that a run must produce.
- [ ] Fixture 01 and 04 still pass the dry-run in the CI suite.

## Related

- None.

Found by the 2026-09 coherence audit.
