# Implementation Plan: G56R-005 Model Availability, Fallback, and Recovery Simulation

**Branch**: `g56r-005-model-availability-fallback-recovery` | **Date**: 2026-08-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/g56r-005-model-availability-fallback-recovery/spec.md`

## Summary

Create deterministic, repository-local Codex simulation evidence for model route availability, ordered fallback evaluation, service reroute attribution, strict override rejection, optional-helper degradation, bounded harness execution, and fake-home install recovery. The implementation is a Python 3.11+ stdlib test harness and fixture corpus that proves the G56R-005 contract without wiring production routing, changing shipped payloads, or making live model availability claims.

## Technical Context

**Language/Version**: Python 3.11+ standard library only

**Primary Dependencies**: Existing repo-local helpers under `tests/speckit-pro/lib`, `tests/speckit-pro/layer6-efficiency/lib`, and `speckit-pro/speckit_pro_runner/helpers/install.py`; the authoritative bundled Codex source roster; no new third-party dependencies

**Storage**: Canonical JSON fixtures, JSON Schema contracts, fake-home temporary filesystem state

**Testing**: `python3 tests/speckit-pro/run-all.py`, focused unit tests, Layer 4 deterministic suite, and generated-artifact checks where required

**Target Platform**: Repository-local cross-platform Python test/runtime surface

**Project Type**: Test harness / deterministic simulation library

**Performance Goals**: Bounded sequential replay; no live service calls; fixture replay records byte-stable across three consecutive runs

**Constraints**: No recursive agent execution, no human-in-the-loop escalation, no real home writes, no production resolver or installer wiring, no payload/version/release-artifact mutation

**Scale/Scope**: One vertical simulation slice covering 22 FRs, 9 SCs, 4 user stories, and the required scenario coverage table

**Reviewability Budget**: Primary surface `harness/adapter`; secondary surfaces `seed/config` and `docs/process`; projected 385 reviewable LOC; projected 0 production files; projected 10 total files; budget result within one-slice reviewability ceiling

## Declared File Operations

- NEW tests/speckit-pro/layer6-efficiency/contracts-codex-fallback/route-policy.schema.json
- NEW tests/speckit-pro/layer6-efficiency/contracts-codex-fallback/route-resolution-report.schema.json
- NEW tests/speckit-pro/layer6-efficiency/contracts-codex-fallback/recovery-record.schema.json
- NEW tests/speckit-pro/layer6-efficiency/fixtures-codex-fallback/fallback-recovery-corpus.json
- NEW tests/speckit-pro/layer6-efficiency/lib/codex_route_fallback.py
- NEW tests/speckit-pro/unit/test-codex-route-fallback-recovery.py
- MODIFIED tests/speckit-pro/suite-manifest.json
- MODIFIED specs/g56r-005-model-availability-fallback-recovery/spec.md
- MODIFIED specs/g56r-005-model-availability-fallback-recovery/SPEC-MOC.md
- MODIFIED docs/ai/specs/codex-gpt-5-6-agent-routing-roadmap-MOC.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Plugin Structure Compliance | PASS | Work is repository-only simulation under tests/spec artifacts; production install paths and payloads stay untouched |
| II. Cross-Platform Runtime & Script Safety | PASS | Python 3.11+ stdlib, structured JSON, canonical UTF-8 bytes, no Bash or `jq` dependency |
| III. Semantic Versioning | PASS | No plugin version, manifest, payload, or release artifact changes planned |
| IV. Test Coverage Before Merge | PASS | New focused unit test path is registered in `suite-manifest.json`; full suite remains final verification |
| V. Conventional Commits | PASS | Phase commits and final PR title use lowercase scope and plain-English description |
| VI. KISS, Simplicity & YAGNI | PASS | One Codex-local resolver, one fake-home adapter boundary, one sequential harness state machine; no shared cross-platform resolver extraction |

Reviewability remains within budget. No split exception is required. Deferred production wiring belongs to G56R-006; cross-platform vocabulary reconciliation belongs to CAR-012/G56R-012.

## Project Structure

### Documentation (this feature)

```text
specs/g56r-005-model-availability-fallback-recovery/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── fallback-recovery-contract.md
├── SPEC-MOC.md
└── spec.md
```

### Source Code (repository root)

```text
tests/speckit-pro/
├── layer6-efficiency/
│   ├── contracts-codex-fallback/
│   │   ├── recovery-record.schema.json
│   │   ├── route-policy.schema.json
│   │   └── route-resolution-report.schema.json
│   ├── fixtures-codex-fallback/
│   │   └── fallback-recovery-corpus.json
│   └── lib/
│       └── codex_route_fallback.py
├── suite-manifest.json
└── unit/
    └── test-codex-route-fallback-recovery.py
```

**Structure Decision**: Keep the feature in the existing repository-only test and Layer 6 evidence surface. The production plugin runner remains read-only precedent for required-agent roster and fake-home safety patterns, but G56R-005 does not modify installer runtime behavior. Bind fixtures to an identity derived from the current bundled source roster, classify `autopilot-fast-helper.toml` as conditional optional-helper destination state, and fail closed for fixture re-review on roster drift. The current checkout has 10 core definitions plus the helper; the roadmap's future 11-core-plus-helper target is not hard-coded into this simulation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Phase 0 Research

See [research.md](./research.md).

## Phase 1 Design

See [data-model.md](./data-model.md), [quickstart.md](./quickstart.md), and [contracts/fallback-recovery-contract.md](./contracts/fallback-recovery-contract.md).

## Review Packet Source

The PR packet must state that this is deterministic local simulation only; live model/service availability was not tested. Review in this order: schemas, corpus, resolver/state adapter, focused tests, suite manifest, spec artifacts. Rollback is removal of the new simulation files plus suite-manifest registration and regenerated spec index changes.
