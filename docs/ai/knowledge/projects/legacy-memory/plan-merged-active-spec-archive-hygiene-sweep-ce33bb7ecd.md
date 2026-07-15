---
type: "speckit-legacy-memory-record"
title: "Merged active-spec archive hygiene sweep"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-ce33bb7ecd97deb8"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Merged active-spec archive hygiene sweep

[Source: .specify/memory/archive-reports/2026-06-13-merged-specs-post-merge-hygiene.md]
**Branch**: `codex/archive-merged-specs-hygiene` · **Status**: Completed · **Archived**: 2026-06-13

### Scope

This sweep archived and removed the remaining active `specs/**` folders whose
implementation had already merged:

- SPEC-001 repository foundation, SPEC-002 PR checks, SPEC-003 release
  automation, SPEC-004 integration/verification, and SPEC-006a UAT skeleton.
- PRSG-002 MOC templates, PRSG-003 generated spec index, PRSG-004 roadmap-MOC
  home note, PRSG-006 reviewability budget, and PRSG-012 reviewer-ready PR
  packet contract.

### Architecture / Approach

- Treat merge commits as the archive source of truth, with explicit recovery
  commands in the archive report.
- Preserve historical workflow docs under `docs/ai/specs/` and
  `docs/ai/specs/.process/`; remove only active merged `specs/**` folders.
- Decouple tests from live spec folders before cleanup:
  - MOC lints now use committed fixture-backed dogfood assertions instead of
    reading `specs/prsg-002-moc-templates/SPEC-MOC.md`.
  - PRSG-012 PR body and marker-emission regression tests now read vendored
    fixtures under `tests/speckit-pro/unit/fixtures/`.
  - SPEC-006a already used the vendored full-spec snapshot fixture.
- Regenerate generated roadmap-MOC INDEX content after active spec removal so
  generated links do not point to archived spec folders.

### Test Strategy

- Pre-cleanup fixture verification:
  - `bash tests/speckit-pro/unit/test-generate-pr-body.sh` passed
    `85/85`.
  - `bash tests/speckit-pro/unit/test-multi-pr-emission.sh` passed
    `156/156`.
  - `bash tests/speckit-pro/layer1-structural/validate-moc-stale-index.sh`
    passed `11/11`.
  - `bash tests/speckit-pro/layer1-structural/validate-moc-orphan.sh` passed
    `29/29`.
- Post-cleanup `bash tests/speckit-pro/run-all.sh` passed `2915/2915`
  (Layer 1 structural `549/549`, Codex structural `430/430`, Layer 4 script
  unit `1746/1746`, Layer 5 tool scoping `190/190`).

### Cleanup Notes

`specs/001-repository-foundation`, `specs/002-pr-checks-workflow`,
`specs/003-release-automation`, `specs/004-integration-verification`,
`specs/006a-uat-skeleton`, `specs/prsg-002-moc-templates`,
`specs/prsg-003-spec-index`, `specs/prsg-004-roadmap-moc-home-note`,
`specs/prsg-006-reviewability-budget`, and
`specs/prsg-012-reviewer-ready-pr-packet-contract` were removed from active
`specs/**` cleanup after provenance, recovery commands, and fixture
decoupling were recorded.

---
