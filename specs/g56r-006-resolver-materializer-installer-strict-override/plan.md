# Implementation Plan: Capability-aware Resolver, Materializer, Installer, and Strict Override

**Branch**: `g56r-006-resolver-materializer-installer-strict-override` | **Date**: 2026-08-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/g56r-006-resolver-materializer-installer-strict-override/spec.md`

## Summary

G56R-006 extends the current Codex `install-codex-agents` runner helper with an explicit route-aware mode that is activated only by a trusted policy manifest. Static no-manifest requests keep the current 13-file copy/verify behavior. Route-aware requests validate a closed 12-required-agent roster plus one optional helper from one fresh capability snapshot, materialize selected model/effort routes from original source TOML bytes, and mutate a fake-home destination only after the complete required batch is proven.

The implementation stays on the existing Python runner surfaces: `agent_materialization.py` for source-bound destination bytes, `helpers/install.py` for request validation, resolution, mutation, rollback, and response evidence, and `helpers/registry.py` for helper metadata. It adds deterministic fake-home fixtures and Codex install documentation, then refreshes generated payload/reference mirrors.

## Technical Context

**Language/Version**: Python 3.11+.

**Primary Dependencies**: Python standard library only: `json`, `tomllib`, `pathlib`, `hashlib`, `dataclasses`, `typing`, `tempfile`, `os`, and existing runner helpers. No package dependency, Bash, `jq`, PowerShell, WSL, or shell wrapper.

**Storage**: Filesystem-only plugin source TOMLs, explicit manifest JSON files, fake-home destination TOMLs, runner response JSON, and generated payload/reference files.

**Testing**: Repository Python-authoritative runner: `python3 tests/speckit-pro/run-all.py`; focused materializer coverage in `tests/speckit-pro/unit/test-agent-materialization.py`; focused installer coverage in `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`; Layer 1 structural validation after payload refresh; docs reference generation/check when tracked tests change.

**Target Platform**: Cross-platform installed SpecKit Pro runner for Codex custom subagents. Acceptance uses deterministic injected fixtures and fake homes only.

**Project Type**: Public plugin marketplace repository with an installed Python runner helper and Codex custom-agent payloads.

**Performance Goals**: The route-aware path handles a fixed 13-file source inventory and 12 required destination records in one batch. It must capture one runtime capability snapshot per invocation and avoid per-agent recapture or unbounded probing.

**Constraints**: Preserve static 13-file install compatibility; validate exactly 13 bundled source TOMLs; route-aware mode requires a trusted manifest path; use structured JSON/TOML parsing; direct argv arrays with `shell=False`; no live model calls; no real-user-home mutation in G56R-006 acceptance; no downstream route qualification or cohort count changes.

**Scale/Scope**: One vertical resolver/materializer/installer framework slice over 12 required Codex agents plus `autopilot-fast-helper` as optional destination helper.

**Reviewability Budget**: Primary surface: harness/adapter. Secondary surfaces: seed/config, tests, and docs. The authored implementation surface is 4 production files plus 4 test/fixture/doc files (8 total); six planning artifacts and 41 generator-owned payload, trust-metadata, proof, evidence, and reference paths are reported separately. Setup estimate remains 385 reviewable LOC, one suggested slice, status `ok`. The plan-phase helper returned `status=pass`, `projected=0`, `declared_files.production=0`, `declared_files.new=7`, `declared_files.modified=48`, and `declared_files.total_entries=55`; its production taxonomy does not classify this repository's `speckit-pro/**/*.py` paths, so the manual authored count is the operative planning evidence. Split decision: keep one vertical slice because 4 production and 8 authored implementation files stay below the blocking thresholds and the Design Concept fixed this as one end-to-end framework slice.

## Declared File Operations

- NEW specs/g56r-006-resolver-materializer-installer-strict-override/plan.md
- NEW specs/g56r-006-resolver-materializer-installer-strict-override/research.md
- NEW specs/g56r-006-resolver-materializer-installer-strict-override/data-model.md
- NEW specs/g56r-006-resolver-materializer-installer-strict-override/quickstart.md
- NEW specs/g56r-006-resolver-materializer-installer-strict-override/contracts/route-policy-manifest.schema.md
- NEW specs/g56r-006-resolver-materializer-installer-strict-override/contracts/install-codex-agents-route-aware.md
- MODIFIED speckit-pro/speckit_pro_runner/agent_materialization.py
- MODIFIED speckit-pro/speckit_pro_runner/helpers/install.py
- MODIFIED speckit-pro/speckit_pro_runner/helpers/registry.py
- MODIFIED speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json
- MODIFIED speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256
- MODIFIED speckit-pro/codex-skills/install/SKILL.md
- MODIFIED tests/speckit-pro/unit/test-agent-materialization.py
- MODIFIED tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py
- NEW tests/speckit-pro/unit/fixtures/mutation-helpers/codex-agent-routing/cases.json
- MODIFIED dist/codex/speckit-pro/speckit_pro_runner/agent_materialization.py
- MODIFIED dist/codex/speckit-pro/speckit_pro_runner/helpers/install.py
- MODIFIED dist/codex/speckit-pro/speckit_pro_runner/helpers/registry.py
- MODIFIED dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json
- MODIFIED dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256
- MODIFIED dist/codex/speckit-pro/skills/install/SKILL.md
- MODIFIED dist/claude/speckit-pro/speckit_pro_runner/agent_materialization.py
- MODIFIED dist/claude/speckit-pro/speckit_pro_runner/helpers/install.py
- MODIFIED dist/claude/speckit-pro/speckit_pro_runner/helpers/registry.py
- MODIFIED dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json
- MODIFIED dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/speckit_pro_runner/agent_materialization.py
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/speckit_pro_runner/helpers/install.py
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/speckit_pro_runner/helpers/registry.py
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/skills/install/SKILL.md
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/speckit_pro_runner/agent_materialization.py
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/speckit_pro_runner/helpers/install.py
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/speckit_pro_runner/helpers/registry.py
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-file-root.json
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-missing-mutable.json
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-missing-source-root.json
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-mutable.json
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-partial-root.json
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-root-mismatch.json
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-same-root.json
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-single-product.json
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-source-mismatch.json
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-stale-hash.json
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof-traversal-root.json
- MODIFIED tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof.json
- MODIFIED docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json
- MODIFIED docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json
- MODIFIED docs/ai/specs/.process/XPLAT-009-zero-bash-guard-result.json
- MODIFIED docs/ai/specs/.process/XPLAT-009-release-readiness-result.json
- MODIFIED docs-site/src/content/docs/install/codex.md
- MODIFIED docs-site/src/content/docs/reference/tests.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Plan impact | Status |
|-----------|-------------|--------|
| I. Plugin Structure Compliance | Runtime changes stay under `speckit-pro/`; repository-only tests stay under `tests/speckit-pro/`; generated payload mirrors are refreshed rather than hand-designed. | PASS |
| II. Cross-Platform Runtime & Script Safety | Active logic uses Python 3.11 stdlib, structured JSON/TOML parsing, pathlib-safe paths, deterministic UTF-8, and direct argv arrays with `shell=False`; no new Bash or `jq`. | PASS |
| III. Semantic Versioning | No manual version or marketplace manifest edit is planned. | PASS |
| IV. Test Coverage Before Merge | Focused Layer 4 fake-home coverage, Layer 1 structural checks after generated payload refresh, and the default suite are required. | PASS |
| V. Conventional Commits | Parent workflow owns commits; any commit must use a conventional-commit title with lowercase scope. | PASS |
| VI. KISS, Simplicity & YAGNI | Extend the existing materializer/installer framework. No parallel resolver, per-agent override map, live UAT, or downstream route qualification is introduced. | PASS |

**Initial Gate Result**: PASS. No constitution violations require an exception. Reviewability sizing remains one vertical slice: the setup estimate is 385 LOC; the authored implementation surface is 4 production and 8 total files; and the remaining declared paths are planning artifacts or generator-owned trust metadata, payload mirrors, proof fixtures, evidence, and docs references.

## Project Structure

### Documentation (this feature)

```text
specs/g56r-006-resolver-materializer-installer-strict-override/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- install-codex-agents-route-aware.md
|   `-- route-policy-manifest.schema.md
`-- tasks.md
```

### Source Code (repository root)

```text
speckit-pro/
|-- codex-agents/                       # UNCHANGED strict 13-source TOML roster
|-- codex-skills/
|   `-- install/SKILL.md                # MODIFIED Codex subagent install contract
`-- speckit_pro_runner/
    |-- agent_materialization.py        # MODIFIED explicit route rendering proof
    `-- helpers/
        |-- install.py                  # MODIFIED route-aware request/plan/apply/rollback
        `-- registry.py                 # MODIFIED helper metadata or promotion evidence

tests/speckit-pro/
`-- unit/
    |-- test-agent-materialization.py
    |-- test-speckit-pro-mutation-helpers.py
    `-- fixtures/
        |-- mutation-helpers/codex-agent-routing/cases.json
        `-- plugin-bash-confinement/installed-cache/{claude,codex}/speckit-pro/...

dist/
|-- claude/speckit-pro/speckit_pro_runner/...   # GENERATED MODIFIED
`-- codex/speckit-pro/...                       # GENERATED MODIFIED

docs-site/src/content/docs/
|-- install/codex.md
`-- reference/tests.md                          # GENERATED MODIFIED
```

**Structure Decision**: Use the existing single plugin runner structure. The route-aware behavior is a mode of `install-codex-agents`, not a new command or parallel installer. The strict source roster in `speckit-pro/codex-agents/*.toml` remains unchanged and is treated as the source inventory authority.

## Design Concept Architecture Decisions

Every architecture-shaping decision below links back to the binding Design Concept:

| Area | Design Concept quote | Plan consequence |
|------|----------------------|------------------|
| Roster | ["12 current required agents; fast helper optional"](../../docs/ai/specs/.process/G56R-006-design-concept.md#decisions) | Model the manifest and response around 12 required destination records and one optional helper decision while keeping 13 bundled TOMLs mandatory. |
| Materializer | ["Extend canonical materializer to render and prove the selected route"](../../docs/ai/specs/.process/G56R-006-design-concept.md#decisions) | Add explicit model/effort route rendering to `agent_materialization.py`; retain original source bytes and prove non-route fields unchanged. |
| Runtime discovery | ["One injectable runner-owned adapter"](../../docs/ai/specs/.process/G56R-006-design-concept.md#decisions) | `helpers/install.py` owns one adapter boundary that tests can inject; no fixture booleans flow directly into production resolution. |
| Evidence output | ["Top-level structured routing response"](../../docs/ai/specs/.process/G56R-006-design-concept.md#decisions) | Route policy evidence lives in `data.routing`; low-level `mutation` stays mechanical file-operation evidence. |
| Activation | ["Explicit policy manifest enables route-aware mode; static mode remains compatible"](../../docs/ai/specs/.process/G56R-006-design-concept.md#decisions) | Requests without `route_policy_manifest` keep the existing no-`routing` 13-file static response. |
| Override | ["Required agents are strict; matching helper override installs, incompatible helper uses no-helper"](../../docs/ai/specs/.process/G56R-006-design-concept.md#decisions) | Strict override evaluates exactly one tuple for each required agent, never falls back, and only installs the helper when compatible. |
| Managed removal | ["Provenance or known-byte proof required"](../../docs/ai/specs/.process/G56R-006-design-concept.md#decisions) | Helper deletion requires trusted provenance or an exact rendered-byte digest match; name or parsed TOML similarity never qualifies. |
| Atomicity | ["Complete plan first, rollback-backed batch apply"](../../docs/ai/specs/.process/G56R-006-design-concept.md#decisions) | All required agents resolve/materialize/verify before planned writes; apply uses one rollback-backed batch. |
| Diagnostics | ["Resolve all required agents, return all attempts, zero writes on any required miss"](../../docs/ai/specs/.process/G56R-006-design-concept.md#decisions) | Required misses produce complete read-only diagnostics for all 12 agents and an empty mutation plan. |
| Snapshot | ["One fresh batch snapshot"](../../docs/ai/specs/.process/G56R-006-design-concept.md#decisions) | Every resolution record and helper decision binds to the same snapshot ID; probes are child evidence only. |
| Acceptance | ["Deterministic fixtures and fake homes only"](../../docs/ai/specs/.process/G56R-006-design-concept.md#decisions) | Tests inject discovery/probe outcomes and fake destinations; no live model calls or real home writes. |
| Downstream drift | ["Flag roster reconciliation; do not expand this framework slice"](../../docs/ai/specs/.process/G56R-006-design-concept.md#decisions) | This plan records downstream mismatch only and does not alter G56R-007 through G56R-011 cohort counts. |

## Phase 0: Research

Research decisions are captured in [research.md](research.md). No clarification markers remain.

## Phase 1: Design & Contracts

Design artifacts:

- [data-model.md](data-model.md)
- [contracts/route-policy-manifest.schema.md](contracts/route-policy-manifest.schema.md)
- [contracts/install-codex-agents-route-aware.md](contracts/install-codex-agents-route-aware.md)
- [quickstart.md](quickstart.md)

## Post-Design Constitution Check

| Principle | Re-check result |
|-----------|-----------------|
| I. Plugin Structure Compliance | PASS: planned source, tests, generated payloads, and docs stay in their established repository locations. |
| II. Cross-Platform Runtime & Script Safety | PASS: route-aware logic remains Python stdlib and structured parsing only; fixture commands use existing runner/test entry points. |
| III. Semantic Versioning | PASS: no manual version edit planned. |
| IV. Test Coverage Before Merge | PASS: each user story maps to fake-home unit coverage plus Layer 1, Layer 4, docs reference checks, and full suite verification. |
| V. Conventional Commits | PASS: parent workflow owns commits. |
| VI. KISS, Simplicity & YAGNI | PASS: one route-aware mode inside the existing installer, one adapter, one snapshot, one rollback batch, no downstream qualification. |

**Gate Result**: PASS. No unresolved clarification markers, no Design Concept drift, and no split requirement. `tests/speckit-pro/layer6-efficiency/fixtures-codex/` remains unchanged because no Codex agent TOML definition changes in this slice; the generated runner trust metadata and installed-cache proof families above cover the changed runner and skill inputs.

## Complexity Tracking

No constitution violations or split exceptions are required.

## Review Packet Source

The PR packet should report:

- What changed: route-aware install mode, manifest validation, single-snapshot resolution, strict override, optional helper decisioning, materialization proof, rollback evidence, deterministic fixtures, and Codex install docs.
- Why: G56R-006 supplies the reusable framework that downstream G56R-007 through G56R-010 can use for qualified policies.
- Non-goals: no production route qualification, live route UAT, real-user-home mutation, Claude agent install path, per-agent override map, arbitrary effort map, or downstream cohort count update.
- Review order: contracts/data model, materializer, installer route planning, rollback/verification, tests/fixtures, generated payload/docs.
- Scope budget: one vertical slice, setup estimate 385 LOC, plan-phase estimator evidence, generated mirrors excluded from authored reviewable LOC.
- Traceability: FR-001 through FR-029 map to the contracts, data model, installer/materializer files, and fake-home test matrix.
- Verification: focused mutation-helper tests, Layer 1, Layer 4, docs reference generation/check, full runner suite.
- Known gaps: downstream G56R-007 through G56R-011 roster reconciliation and live/default route activation remain unresolved by design.
- Rollback/flags: route-aware mode is gated by explicit manifest input; static no-manifest mode remains compatible and can be used as the fallback path.
