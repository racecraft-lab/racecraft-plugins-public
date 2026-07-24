# Archival Report - CAR-002 Capability Probing and Telemetry

## Mode

- **archiveMode**: merged-spec cleanup sweep
- **dryRun**: false
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true
- **excludedCurrentSpec**: none

## Provenance

- **Source spec path**: `specs/car-002-capability-probing-telemetry/`
- **PR URL**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/369
- **PR title**: `feat(car-002): capture Claude runtime capability probe evidence and trace contracts`
- **Merged at**: `2026-07-23T02:11:51Z`
- **Merge commit**: `4eea291ab71f47f03ab14da6af19e94381c2af2f`
- **Head branch**: `car-002-capability-probing-telemetry`
- **Base branch**: `main`
- **Workflow preserved**: `docs/ai/specs/.process/CAR-002-workflow.md`
- **Design concept preserved**: `docs/ai/specs/.process/CAR-002-design-concept.md`
- **CI / metadata gates**: required PR checks passed, including
  `validate-pr-title`, `validate-release-note`, `validate-workflows`,
  `validate-docs`, `artifact-consistency`, `test (speckit-pro)`,
  `validate-plugins`, CodeQL, and Linux container preflight.
- **Screenshot retention**: N/A
- **Expiration risk**: committed source and process evidence has no artifact
  retention dependency.

## Feature Summary

CAR-002 shipped a bounded, sanitized Claude runtime capability snapshot, a
field-classified telemetry profile, a readable exact-treatment trace schema,
and deterministic offline validators for success, null, unavailable, and
misdelivery records. It preserved the no-qualification boundary: capability
observations and exact-treatment evidence do not select preferred routes or
change shipped agent policies.

## Canonical Shipped Artifacts

- `docs/ai/research/claude-runtime-capability-snapshot.json`
- `docs/ai/research/claude-telemetry-capability-profile.json`
- `docs/ai/research/claude-trace-contract.schema.json`
- `tests/speckit-pro/layer6-efficiency/lib/claude_capabilities.py`
- `tests/speckit-pro/layer6-efficiency/lib/claude_trace_schema.py`
- `tests/speckit-pro/unit/fixtures/claude-telemetry-records/`
- `tests/speckit-pro/unit/test-efficiency-claude-telemetry.py`
- `docs/ai/specs/.process/CAR-002-workflow.md`
- `docs/ai/specs/.process/CAR-002-design-concept.md`

## Recovery Commands

```text
git show 4eea291ab71f47f03ab14da6af19e94381c2af2f:specs/car-002-capability-probing-telemetry/spec.md
git show 4eea291ab71f47f03ab14da6af19e94381c2af2f:specs/car-002-capability-probing-telemetry/plan.md
git show 4eea291ab71f47f03ab14da6af19e94381c2af2f:specs/car-002-capability-probing-telemetry/tasks.md
git show 4eea291ab71f47f03ab14da6af19e94381c2af2f:specs/car-002-capability-probing-telemetry/research.md
git show 4eea291ab71f47f03ab14da6af19e94381c2af2f:specs/car-002-capability-probing-telemetry/data-model.md
git show 4eea291ab71f47f03ab14da6af19e94381c2af2f:specs/car-002-capability-probing-telemetry/quickstart.md
git show 4eea291ab71f47f03ab14da6af19e94381c2af2f:specs/car-002-capability-probing-telemetry/retrospective.md
git show 4eea291ab71f47f03ab14da6af19e94381c2af2f:specs/car-002-capability-probing-telemetry/SPEC-MOC.md
git show 4eea291ab71f47f03ab14da6af19e94381c2af2f:specs/car-002-capability-probing-telemetry/contracts/claude-trace-contract.schema.json
git show 4eea291ab71f47f03ab14da6af19e94381c2af2f:specs/car-002-capability-probing-telemetry/checklists/requirements.md
git show 4eea291ab71f47f03ab14da6af19e94381c2af2f:specs/car-002-capability-probing-telemetry/checklists/traceability.md
git show 4eea291ab71f47f03ab14da6af19e94381c2af2f:specs/car-002-capability-probing-telemetry/checklists/data-integrity.md
git show 4eea291ab71f47f03ab14da6af19e94381c2af2f:specs/car-002-capability-probing-telemetry/checklists/error-handling.md
git checkout 4eea291ab71f47f03ab14da6af19e94381c2af2f -- specs/car-002-capability-probing-telemetry
```

## Changed Files and Impact

| Artifact | Change |
|---|---|
| `.specify/memory/{spec,plan,changelog}.md` | Append shipped behavior, architecture, provenance, and cleanup state |
| Claude routing roadmap and MOC | Mark CAR-002 archived and CAR-003 ready |
| `docs/ai/specs/.process/autopilot-state.json` | Record completed archive sweep |
| `specs/car-002-capability-probing-telemetry/` | Remove completed active spec residue |

## Cleanup Decision

- **cleanupApplied**: true
- **cleanupCommand**: `git rm -r specs/car-002-capability-probing-telemetry`
- **cleanupBranch**: `codex/archive-merged-specs-20260724`
- **blockedBy**: none
- **Downstream state**: CAR-003 is ready; CAR-004 and later dependencies remain
  governed by their existing sequence.

## Verification Commands

- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
- runner operation `generate-spec-index-write` in apply mode
- runner helper `generate-spec-index-check`
- `python3 tests/speckit-pro/unit/test-efficiency-claude-telemetry.py`
- `python3 tests/speckit-pro/run-all.py --layer 1`
- `git diff --check`
- final active-spec inventory audit

## Verification Results

- PASS: `autopilot-state.json` parses as valid JSON.
- PASS: SpecKit index write and check report all in-scope maps current.
- PASS: CAR-002 telemetry tests passed `378/378`.
- PASS: Layer 1 structural validation passed `1428/1428`.
- PASS: full deterministic suite passed `3246/3246`.
- PASS: docs reference pages are current.
- PASS: `git diff --check` found no whitespace errors.
- PASS: active spec inventory contains only `specs/.gitkeep`.

## Constitution Compliance

PASS by scope. Cleanup preserves durable evidence, changes no plugin version or
runtime payload, keeps repository tooling on Python, and retains all merged
source through immutable git provenance.
