# Archival Report - G56R-002 Capability Discovery and Exact Treatment

## Mode

- **archiveMode**: merged-spec cleanup sweep
- **dryRun**: false
- **applyCleanupRequested**: true
- **dryRunProvenanceOnly**: false
- **safeToApplyCleanup**: true
- **excludedCurrentSpec**: none

## Provenance

| PR | Title | Merged at | Merge commit |
|---|---|---|---|
| [#366](https://github.com/racecraft-lab/racecraft-plugins-public/pull/366) | `feat(g56r-002): Freeze capability authority and evidence` | `2026-07-23T18:26:36Z` | `8d11815eceefe25683f966241de722592f86d58e` |
| [#367](https://github.com/racecraft-lab/racecraft-plugins-public/pull/367) | `feat(g56r-002): Add exact-treatment contracts` | `2026-07-23T20:59:56Z` | `470faccb6eea814ad23d49602178a52490d1ccc7` |
| [#368](https://github.com/racecraft-lab/racecraft-plugins-public/pull/368) | `feat(g56r-002): Add deterministic treatment replay` | `2026-07-23T22:47:21Z` | `06d54487fd3b507333f96e571223805c1956998b` |

- **Source spec path**: `specs/g56r-002-capability-discovery-telemetry/`
- **Head branches**: `g56r-002-slices/01-us1`,
  `g56r-002-slices/02-us2`, `g56r-002-slices/03-us3`
- **Base branch**: `main`
- **Workflow preserved**: `docs/ai/specs/.process/G56R-002-workflow.md`
- **Design concept preserved**: `docs/ai/specs/.process/G56R-002-design-concept.md`
- **CI / metadata gates**: required checks passed on all three PRs, including
  structural and full SpecKit tests, metadata gates, CodeQL, artifact
  consistency, and Linux container preflight.
- **Screenshot retention**: N/A
- **Expiration risk**: committed source, fixtures, schemas, and process
  evidence have no external artifact-retention dependency.

## Feature Summary

G56R-002 shipped the official-source-bound executable-candidate freeze,
telemetry and exact-treatment contracts, sanitized capability capture,
append-only evidence handling, and deterministic eight-case replay. It does not
qualify routes or select defaults. G56R-003 now has the frozen capability and
treatment foundation required for outcome-bearing evaluation.

## Canonical Shipped Artifacts

- `docs/ai/research/codex-g56r-002-capability-evidence.md`
- `docs/ai/research/codex-g56r-002-executable-candidate-freeze.json`
- `tests/speckit-pro/layer6-efficiency/lib/codex_capability_*.py`
- `tests/speckit-pro/layer6-efficiency/lib/treatment_trace_*.py`
- `tests/speckit-pro/layer6-efficiency/contracts/`
- `tests/speckit-pro/unit/fixtures/capability-treatment-replay/`
- `tests/speckit-pro/unit/fixtures/final-reviewability-backstop/`
- `tests/speckit-pro/unit/test-codex-capability-contract.py`
- `tests/speckit-pro/unit/test-reviewability-marker-guidance.py`
- `docs/ai/specs/.process/G56R-002-workflow.md`
- `docs/ai/specs/.process/G56R-002-design-concept.md`

The three live test-owned schemas and three immutable marker checkpoint samples
were moved from the completed spec package into durable test contract and
fixture paths. Historical completed-marker records retain their original paths
as provenance and are verified with `git show` against their recorded commits.

## Recovery Commands

The final merge commit contains the complete raw spec package. The directory
checkout restores every raw artifact, including all checkpoint, correction,
verification, reviewability, checklist, contract, and planning files.

```text
git show 06d54487fd3b507333f96e571223805c1956998b:specs/g56r-002-capability-discovery-telemetry/spec.md
git show 06d54487fd3b507333f96e571223805c1956998b:specs/g56r-002-capability-discovery-telemetry/plan.md
git show 06d54487fd3b507333f96e571223805c1956998b:specs/g56r-002-capability-discovery-telemetry/tasks.md
git show 06d54487fd3b507333f96e571223805c1956998b:specs/g56r-002-capability-discovery-telemetry/research.md
git show 06d54487fd3b507333f96e571223805c1956998b:specs/g56r-002-capability-discovery-telemetry/data-model.md
git show 06d54487fd3b507333f96e571223805c1956998b:specs/g56r-002-capability-discovery-telemetry/quickstart.md
git show 06d54487fd3b507333f96e571223805c1956998b:specs/g56r-002-capability-discovery-telemetry/SPEC-MOC.md
git show 06d54487fd3b507333f96e571223805c1956998b:specs/g56r-002-capability-discovery-telemetry/contracts/capability-freeze.schema.json
git show 06d54487fd3b507333f96e571223805c1956998b:specs/g56r-002-capability-discovery-telemetry/contracts/marker-checkpoint.schema.json
git show 06d54487fd3b507333f96e571223805c1956998b:specs/g56r-002-capability-discovery-telemetry/contracts/treatment-record.schema.json
git checkout 06d54487fd3b507333f96e571223805c1956998b -- specs/g56r-002-capability-discovery-telemetry
```

To enumerate or recover an individual process artifact:

```text
git ls-tree -r --name-only 06d54487fd3b507333f96e571223805c1956998b -- specs/g56r-002-capability-discovery-telemetry
git show 06d54487fd3b507333f96e571223805c1956998b:specs/g56r-002-capability-discovery-telemetry/.process/checkpoints/us1.json
git show 06d54487fd3b507333f96e571223805c1956998b:specs/g56r-002-capability-discovery-telemetry/.process/checkpoints/us2.json
git show 06d54487fd3b507333f96e571223805c1956998b:specs/g56r-002-capability-discovery-telemetry/.process/checkpoints/us3.json
```

## Changed Files and Impact

| Artifact | Change |
|---|---|
| `.specify/memory/{spec,plan,changelog}.md` | Append shipped behavior, architecture, provenance, and cleanup state |
| Codex routing roadmap and MOC | Mark G56R-002 archived and G56R-003 ready |
| Layer 6 contracts and final-reviewability fixtures | Own the schemas and samples still needed by live tests |
| Capability and marker tests | Read canonical live contracts and historical provenance correctly |
| `docs/ai/specs/.process/autopilot-state.json` | Record completed archive sweep |
| `specs/g56r-002-capability-discovery-telemetry/` | Remove completed active spec residue |

## Cleanup Decision

- **cleanupApplied**: true
- **cleanupCommand**: `git rm -r specs/g56r-002-capability-discovery-telemetry`
- **cleanupBranch**: `codex/archive-merged-specs-20260724`
- **blockedBy**: none after live test dependencies were migrated
- **Downstream state**: G56R-003 is ready; route qualification, policy
  selection, resolver behavior, installation, and release remain downstream.

## Verification Commands

- `python3 -m json.tool docs/ai/specs/.process/autopilot-state.json`
- runner operation `generate-spec-index-write` in apply mode
- runner helper `generate-spec-index-check`
- `python3 tests/speckit-pro/unit/test-codex-capability-contract.py`
- `python3 tests/speckit-pro/unit/test-reviewability-marker-guidance.py`
- `python3 tests/speckit-pro/run-all.py --layer 1`
- `git diff --check`
- final active-spec inventory and stale live-reference audits

## Verification Results

- PASS: `autopilot-state.json` parses as valid JSON.
- PASS: SpecKit index write and check report all in-scope maps current.
- PASS: G56R-002 capability/treatment tests passed `98/98`.
- PASS: completed-marker provenance tests passed `77/77`.
- PASS: Layer 1 structural validation passed `1428/1428`.
- PASS: full deterministic suite passed `3246/3246`.
- PASS: docs reference pages are current.
- PASS: `git diff --check` found no whitespace errors.
- PASS: active spec inventory contains only `specs/.gitkeep`; remaining old
  `specs/g56r-002-*` strings exist only as immutable historical provenance in
  the completed-marker evidence fixture and are read through recorded commits.

## Constitution Compliance

PASS by scope. The cleanup preserves the Python-owned contract and validation
surface, changes no plugin version or payload, retains immutable provenance, and
keeps the active `specs/**` directory reserved for work that is not merged.
