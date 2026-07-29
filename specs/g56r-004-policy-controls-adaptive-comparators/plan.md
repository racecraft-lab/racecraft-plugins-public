# Implementation Plan: G56R-004 Policy Controls and Adaptive Comparators

**Branch**: `g56r-004-policy-controls-adaptive-comparators` | **Date**: 2026-07-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/g56r-004-policy-controls-adaptive-comparators/spec.md`

## Summary

G56R-004 freezes Codex-local policy controls and adaptive comparison contracts
before G56R-011 observes final static-core outcomes. The plan is one
repository-only harness/adapter slice: author additive Codex schemas and
deterministic fixtures, add small Python 3.11 stdlib-only validators/replay
helpers, bind frozen G56R-003/CAR-003 artifacts by stable ID plus digest, and
register Layer 4 tests that prove mirror completeness, adaptive behavior,
comparison semantics, reserved-partition refusal, and non-scored smoke sealing.

The architecture follows the design answers verbatim where they constrain the
shape:

> "Freeze unpinned, adaptive, and justified-high-effort; treat automatically
> spawned child work as a modifier."

> "Create Codex-local standalone contracts with Codex IDs, preserve the
> handoff's shapes and semantics."

> "Re-derive the handoff surface in both directions and reject missing, extra,
> or digest-mismatched members."

> "Keep the same gate-first order, eight dimensions, direction rules,
> confidence method, 10% relative margins, and inconclusive/no-verdict handling."

> "Create a content-addressed reserved partition entry owned by G56R-004 and
> fail any replay or smoke row that consumes one of its objectives."

> "Require deterministic replay fixtures and one bounded, non-scored smoke per
> control on the supported ChatGPT-sign-in path."

## Technical Context

**Language/Version**: Python 3.11+.

**Primary Dependencies**: Python standard library only: `json`, `hashlib`,
`pathlib`, `dataclasses`, `typing`, `unittest`, and existing repository test
helpers. No Bash, `jq`, package installation, or network dependency.

**Storage**: Committed JSON Schema documents, committed deterministic JSON
fixtures, feature-local Markdown artifacts, and git-ignored governed smoke
summaries or refusal records under
`tests/speckit-pro/layer6-efficiency/results-codex/`. Raw model, prompt,
response, local path, and operator captures stay off-repository and are never
written under `results-codex/`.

**Testing**: Layer 4 unit tests own behavior coverage. Layer 1 confirms
structural/plugin invariants after suite-manifest edits. The full default suite
is the pre-PR gate. Docs reference generation/checking is required if tracked
test-tree `.md`, `.py`, or `.sh` changes trigger the root `AGENTS.md` rule.

**Target Platform**: Repository-only test and evaluation harness on the local
worktree and CI-compatible Python environments. Live smoke execution is
operator-only and not part of this plan phase.

**Project Type**: Repository-only harness/adapter plus schema/fixture contract
surface.

**Performance Goals**: Deterministic replay fixtures produce byte-identical
governed results across repeated runs. Live smoke plans, when authorized later,
enforce five non-reserved objective attempts, one repetition, zero confirmation
entries, the CAR-004 raw-token arithmetic identity, distinct cache read/write
ceilings, unobserved-rather-than-zero cache diagnostics, 1,800 seconds elapsed
wall clock over the parent-plus-children unit, and child dispatches that consume
no objective attempts.

**Constraints**: Frozen G56R-003/CAR-003 contracts, fixtures, traces, score
bundles, partitions, and evidence records are read-only. G56R-012 reconciliation
debt is out of scope. The only sanctioned mirror divergence is the Codex
`control_kind` value `justified_high_effort` replacing CAR-004
`orchestration_changing`.

**Scale/Scope**: One P1 vertical slice, 42 functional requirements, 18
acceptance scenarios, 19 success criteria, exactly three controls, 19 category-7
decision semantics, and 2 category-8 guards.

**Reviewability Budget**: Primary surface: harness/adapter. Roadmap/scaffold
budget: 235 reviewable LOC, approximately 3 logical helper files, approximately
10 total files, one slice, status `ok`. Concrete declared implementation plan:
12 file operations, 3 logical Python helper files, 3 existing Layer 4 test
owners, and no install-facing plugin runtime files. Exact runner result is
recorded under Reviewability Budget after the estimator run.

## Declared File Operations

- NEW tests/speckit-pro/layer6-efficiency/contracts-codex-specification/policy-control-registry.schema.json
- NEW tests/speckit-pro/layer6-efficiency/contracts-codex-specification/control-comparison.schema.json
- NEW tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/policy-control-registry.json
- NEW tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/control-comparison.json
- NEW tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/partition-registry-entries.json
- NEW tests/speckit-pro/layer6-efficiency/fixtures-codex-controls/replay-cases.json
- NEW tests/speckit-pro/layer6-efficiency/lib/codex_policy_controls.py
- NEW tests/speckit-pro/layer6-efficiency/lib/codex_control_comparison.py
- NEW tests/speckit-pro/layer6-efficiency/lib/codex_control_smoke.py
- MODIFIED tests/speckit-pro/unit/test-policy-control-contracts.py
- MODIFIED tests/speckit-pro/unit/test-control-comparison-dominance.py
- MODIFIED tests/speckit-pro/unit/test-twin-handoff-completeness.py

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Pre-Design Result | Post-Design Result | Evidence |
|-----------|-------------------|--------------------|----------|
| I. Plugin Structure Compliance | PASS | PASS | No plugin install surface changes. Repository-only tests remain under `tests/speckit-pro/`. |
| II. Cross-Platform Runtime & Script Safety | PASS | PASS | Planned helpers are Python 3.11 stdlib-only with structured JSON/path handling. No new Bash, `jq`, shell parsing, or package dependency. |
| III. Semantic Versioning | PASS | PASS | No plugin manifest/version change is planned. |
| IV. Test Coverage Before Merge | PASS | PASS | Layer 4 tests own contract, dominance, replay, guard, and twin-completeness behavior; `suite-manifest.json` remains the registration authority. |
| V. Conventional Commits | PASS | PASS | The autopilot parent creates a scoped phase-checkpoint commit; the future PR title must pass the live release-readiness gate. |
| VI. KISS, Simplicity & YAGNI | PASS | PASS | Three focused Codex-local helper modules; no speculative shared abstraction and no import of Claude identifiers as Codex authority. |

No constitution violation or complexity exception is claimed.

## Project Structure

### Documentation (this feature)

```text
specs/g56r-004-policy-controls-adaptive-comparators/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── policy-control-registry.md
    ├── control-comparison.md
    └── smoke-replay.md
```

### Source Code (repository root)

```text
tests/speckit-pro/
├── layer6-efficiency/
│   ├── contracts-codex-specification/
│   │   ├── policy-control-registry.schema.json
│   │   └── control-comparison.schema.json
│   ├── fixtures-codex-controls/
│   │   ├── policy-control-registry.json
│   │   ├── control-comparison.json
│   │   ├── partition-registry-entries.json
│   │   └── replay-cases.json
│   ├── lib/
│   │   ├── codex_policy_controls.py
│   │   ├── codex_control_comparison.py
│   │   └── codex_control_smoke.py
│   └── results-codex/
├── unit/
│   ├── test-policy-control-contracts.py
│   ├── test-control-comparison-dominance.py
│   └── test-twin-handoff-completeness.py
```

**Structure Decision**: Use the existing Layer 6 evaluation harness layout and
existing Layer 4 durable test owners. New Codex artifacts sit beside, not inside,
the frozen G56R-003/CAR-003 contract set, and the existing
`results-codex/.gitignore` keeps raw per-run smoke output out of git.

## Phase 0: Research

Research is consolidated in [research.md](./research.md). All technical-context
unknowns are resolved: route binding, Codex-local contract form, reuse boundary,
adaptive semantics, comparison semantics, reserved partition handling,
operator-only smoke proof, suite ownership, and reviewability route.

## Phase 1: Design And Contracts

Design outputs are:

- [data-model.md](./data-model.md)
- [contracts/policy-control-registry.md](./contracts/policy-control-registry.md)
- [contracts/control-comparison.md](./contracts/control-comparison.md)
- [contracts/smoke-replay.md](./contracts/smoke-replay.md)
- [quickstart.md](./quickstart.md)

The generated contract notes are human-readable planning contracts. The
implementation-owned machine contracts are the two planned JSON Schema files
under `contracts-codex-specification/`.

## Implementation Boundaries

Frozen read-only bindings:

- G56R-003 successor freeze ID:
  `sha256:734672cea5a83e5b8f296ee604f7cb8d93e0a5296a3f864b873fe78bfe518f1e`
- G56R-003 phase-executor route evidence digest:
  `sha256:f01ff64ca3d17b40db8ca802dd6501e62d91c4c161d01a94879c156f90eb09e4`
- Frozen schema families already present under
  `tests/speckit-pro/layer6-efficiency/contracts-codex-specification/`,
  `contracts-claude/`, and `contracts/`

Implementation must recompute committed-byte digests from those frozen artifacts
and fail closed on mismatch. It must not edit those frozen files to restore
agreement.

## Test Ownership

| Test owner | Planned responsibility | Suite layer |
|------------|------------------------|-------------|
| `tests/speckit-pro/unit/test-policy-control-contracts.py` | Codex registry schema/fixture validation, content-address preimage, exact three controls, adaptive replay including unknown closed-domain refusal, no-wrap floor/ceiling streak accounting, retry/cancellation breach pairings, budget-trigger response distinction, reserved partition guard, raw-token ceiling arithmetic, distinct cache read/write ceilings, unobserved-rather-than-zero cache diagnostics, elapsed wall-clock scope, child-dispatch attempt exclusion, all three unordered cache-isolation pairs, and smoke plan/seal refusal cases | Layer 4 |
| `tests/speckit-pro/unit/test-control-comparison-dominance.py` | Eligibility floors, eight dimensions, direction rules, 10% margin behavior, zero denominator, confidence/multiplicity, verdict-to-claim mapping, and comparison-owned category 1-6 mirror members including exact null preservation | Layer 4 |
| `tests/speckit-pro/unit/test-twin-handoff-completeness.py` | Registry-subset mirror RED at T006, then final composed bidirectional CAR-004/G56R-004 category 1-6 derivation after registry, comparison, and partition artifacts exist; category 7/8 executable checks and single sanctioned divergence enforcement | Layer 4 |
| `tests/speckit-pro/suite-manifest.json` | Existing unchanged authority already registering all three durable test owners; implementation verifies the entries remain present | Layers 1/4 |

Mirror evidence is dependency-ordered rather than prematurely attested:
T006-T007 prove the registry-owned category 1-6 subset, T020-T021 add the
comparison-owned subset including null-valued margins, T024-T025 add the
partition-owned subset, and T032-T033 compose all three into the final
bidirectional completeness proof required by FR-006 and FR-007.

## Reviewability Budget

Concrete plan-phase estimator input is the `Declared File Operations` block in
this file.

| Field | Value |
|-------|-------|
| Initial roadmap budget | `estimated_loc: 235`, `suggested_slices: 1`, `status: ok` |
| Primary surface | `harness/adapter` |
| Declared file operations | 12 |
| Logical helper files | 3 |
| Existing test owners | 3 |
| Exact estimator command | `estimate-reviewable-loc` runner helper against this `plan.md` |
| Exact estimator result | `{"tool":"estimate-reviewable-loc","status":"pass","projected":0,"declared_files":{"production":0,"new":9,"modified":3,"total_entries":12},"greenfield":false,"thresholds":{"warn":400,"block":800,"greenfield_multiplier":1.5,"base_warn":400,"base_block":800}}` |
| Split decision | Keep one vertical slice. The exact estimator passed; no vertical re-slice is required before `tasks.md`. The runner counts 0 production files because all declared implementation paths are repository-only test-tree Python/JSON/manifest files, while the logical implementation surface remains the three planned Codex helper modules. |

## PR Review Packet Source

Future PR packet content is sourced from:

- What changed: `Declared File Operations`
- Why: Summary and Design Authority Quotes
- Non-goals: `research.md` decisions and `spec.md` non-goals
- Review order: schemas/fixtures, helper modules, tests, suite manifest,
  quickstart evidence
- Scope budget: Reviewability Budget
- Traceability: `tasks.md` after G5 plus Test Ownership above
- Verification: Quickstart commands and final suite output
- Known gaps: operator-only live smoke status and any FR-041 reconciliation item
- Rollback/non-applicability: repository-only artifacts; no runtime, installer,
  manifest, scheduler, default, or release integration behavior changed

## Unresolved For Consensus

None at plan time. CAR-004 publishes zero reconciliation candidates. FR-041 is a
conditional stop: if implementation proves a named `mirror_required` member is
genuinely unrepresentable on Codex, implementation must stop, keep the CAR-004
obligation unweakened, and raise the paired CAR/G56R roadmap reconciliation item
before continuing.

Operator authorization for live smokes is not a consensus blocker for planning
or deterministic replay; it remains an implementation/UAT authorization gate.

## Complexity Tracking

No constitution violation is justified.
