# Implementation Plan: CAR-002 Capability Probing, Telemetry Profile, and Exact-Treatment Contract

**Branch**: `car-002-capability-probing-telemetry` | **Date**: 2026-07-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/car-002-capability-probing-telemetry/spec.md`

**Note**: This plan was produced by `/speckit-plan`. Design artifacts: [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md).

## Summary

Freeze the executable candidate set for the pinned Claude Code client by publishing one JSON Schema contract (four record `$defs`), a stdlib validator, an operator-only probe tool with a fail-closed writer, a committed runtime-capability snapshot answering CAP-Q1..CAP-Q6, a versioned telemetry capability profile, and binding route-resolution / exact-treatment replay trace contracts that CAR-003..CAR-011 consume. All live probing is operator-only; every repository/CI test is deterministic with zero live model calls. The work is delivered as three Clarify-ratified vertical work packages (WP1 schema foundation + probe + snapshot; WP2 telemetry profile + trace contracts + CAR-003 handoff; WP3 synthetic-replay validation + 37-route join).

The technical approach reuses the CAR-001 manifest pattern verbatim: one review-visible JSON Schema (draft 2020-12) under `docs/ai/research/`, a hand-rolled standard-library validator mirroring `validate_manifest` in `tests/speckit-pro/unit/test-agent-route-research-parity.py` (no third-party `jsonschema`), and the route-to-tuple join derived — never persisted — from the committed CAR-001 manifest (`model_selector`/`effort_selector`) against the snapshot's per-tuple evidence.

## Technical Context

**Language/Version**: Python 3.11+ standard library only (no third-party packages, no `jsonschema`, no `jq`).

**Primary Dependencies**: None beyond the standard library (`json`, `hashlib`, `subprocess`, `pathlib`, `re`, `unittest`). The operator probe tool shells out to the pinned `claude` CLI via `subprocess` with an argument array and `shell=False`; that single boundary is the only live path and is never exercised by any test.

**Storage**: Committed JSON evidence files under `docs/ai/research/` (schema contract, runtime-capability snapshot, telemetry capability profile) plus committed synthetic fixtures under `tests/speckit-pro/unit/fixtures/claude-telemetry-records/`. No database.

**Testing**: `python3 tests/speckit-pro/run-all.py` (Layers 1, 4, 5 — the Python-authoritative default suite). New Layer 4 unit test `tests/speckit-pro/unit/test-efficiency-claude-telemetry.py` registered in `tests/speckit-pro/suite-manifest.json`.

**Target Platform**: Repository tooling — runs on any machine with Python 3.11+, offline, with no `claude` CLI required for the default suite. The operator probe tool additionally requires a working pinned `claude` CLI and valid authentication, but only when an operator runs it.

**Project Type**: Repository-only validation tooling + committed research evidence (single project; no application, no web/mobile split).

**Performance Goals**: Not applicable — determinism and correctness, not throughput. The one operator-time performance constraint is the probe budget: the probe matrix is bounded at roughly 20 live `claude` invocations worst case (FR-003).

**Constraints**: Zero live model calls in any repository/CI test (FR-001/FR-002/SC-002); fail-closed writer aborts on any schema-invalid observation (FR-023/SC-004); all committed raw evidence sanitized to `<home>` before write, with a SHA-256 over the exact sanitized UTF-8 bytes committed verbatim as a string (FR-012/FR-013); platform facts sourced only from `code.claude.com/docs/**` or `platform.claude.com/docs/**`, probes narrow availability but never establish a platform fact (FR-026/FR-027, `docs/ai/specs/agent-routing-parity-contract.md`).

**Scale/Scope**: 4 record contracts in one schema file; 6 unique (model, effort) tuples deduped from 37 CAR-001 candidate routes; 4 synthetic record-class fixtures; ~13 total files across three work packages.

**Reviewability Budget**: Primary surface — harness/adapter (operator probe tool + stdlib validator). Projected reviewable LOC ~860 across the feature (split required). Production files ~10; total files ~13. Budget result: split into 3 ratified vertical work packages; WP1 sizing carries a G5 escalation note (see "Reviewability Budget & Work-Package Split" below).

## Declared File Operations

The plan-phase reviewability estimator (`estimate-reviewable-loc`) parses this block
to project the slice's production-LOC footprint before `tasks.md` exists. Each entry
is one file on its own line starting with a `- ` list marker. Per-work-package
assignment is in the "Reviewability Budget & Work-Package Split" section below;
this block is the deduplicated whole-feature union.

- NEW docs/ai/research/claude-trace-contract.schema.json
- NEW docs/ai/research/claude-runtime-capability-snapshot.json
- NEW docs/ai/research/claude-telemetry-capability-profile.json
- NEW tests/speckit-pro/layer6-efficiency/lib/claude_trace_schema.py
- NEW tests/speckit-pro/layer6-efficiency/lib/claude_capabilities.py
- NEW tests/speckit-pro/unit/test-efficiency-claude-telemetry.py
- NEW tests/speckit-pro/unit/fixtures/claude-telemetry-records/route-resolution.json
- NEW tests/speckit-pro/unit/fixtures/claude-telemetry-records/success.json
- NEW tests/speckit-pro/unit/fixtures/claude-telemetry-records/null.json
- NEW tests/speckit-pro/unit/fixtures/claude-telemetry-records/unavailable.json
- NEW tests/speckit-pro/unit/fixtures/claude-telemetry-records/misdelivery.json
- MODIFIED tests/speckit-pro/suite-manifest.json
- MODIFIED tests/speckit-pro/unit/test-speckit-pro-runner.py

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design — see "Post-Design Constitution Re-Check".*

Constitution v1.2.0 (`.specify/memory/constitution.md`). Per-principle evaluation:

- **I. Plugin Structure Compliance** — PASS. No new plugin and no plugin manifest, command, agent, skill, or hook is added. All new tooling is repository-only validation under top-level `tests/speckit-pro/`, outside any install-facing plugin directory, exactly as the principle requires. Quality gate `run-all.py --layer 1` remains green (no structural surface touched).
- **II. Cross-Platform Runtime & Script Safety** — PASS. Both new modules (`claude_capabilities.py`, `claude_trace_schema.py`) are Python 3.11+ standard library only: structured `json` parsing, `pathlib` paths, `subprocess` with an argument array and `shell=False`, explicit return-code handling, and deterministic UTF-8 I/O. No repository Bash, `jq`, or PowerShell is added; the fixed vendored `.specify/**` allowlist is untouched. The single `claude` subprocess boundary is operator-only and never runs in a test.
- **III. Semantic Versioning** — PASS (not applicable to plugin versions). No `.claude-plugin/plugin.json` version changes. The schema's instance-level `schema_version` const `1.0.0` is a contract identity (FR-015), not a plugin semver, and starts its own version line independent of the CAR-001 manifest's `2.0.0`.
- **IV. Test Coverage Before Merge** — PASS (planned). Both new Python modules receive Layer 4 unit coverage in `tests/speckit-pro/unit/test-efficiency-claude-telemetry.py`, registered in `suite-manifest.json` (FR-028). The deterministic suite `python3 tests/speckit-pro/run-all.py` must pass with zero failures before any WP is complete; the fail-closed writer's pure logic is unit-tested without live calls.
- **V. Conventional Commits** — PASS (planned). Each work-package PR title will be a valid conventional commit; the natural scope is `speckit-pro` (the changed test tree is `tests/speckit-pro/`) or unscoped for the research-evidence files, with plain-English descriptions per the repository release-readiness gate.
- **VI. KISS, Simplicity & YAGNI** — PASS. The design reuses the CAR-001 schema + stdlib-validator pattern rather than inventing new conventions; the route-to-tuple map is derived from the committed manifest, never persisted (FR-004/SC-005); one canonical snapshot replaces in place (git history preserves priors); no speculative abstractions. CAR-002 is documented in the technical roadmap (`docs/ai/specs/claude-agent-routing-technical-roadmap.md`); no new plugin directory is created, so the "master plan entry before directory creation" clause does not apply.

**Gate result**: PASS — no violations. Complexity Tracking table is empty. The WP1 reviewability-sizing item below is a reviewability-budget escalation (G5), not a constitution violation.

## Project Structure

### Documentation (this feature)

```text
specs/car-002-capability-probing-telemetry/
├── plan.md              # This file (/speckit-plan output)
├── research.md          # Phase 0 output — resolves all Plan-owed decisions
├── data-model.md        # Phase 1 output — four record contracts, tuple, IDs
├── quickstart.md        # Phase 1 output — operator runbook + CAR-003 consumption
├── contracts/
│   └── claude-trace-contract.schema.json   # Phase 1 design draft of the shipped schema
├── spec.md              # Final post-Clarify specification
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
docs/ai/research/
├── agent-route-candidate-manifest.schema.json      # CAR-001 (existing) — join source of truth
├── claude-agent-route-candidate-manifest.json      # CAR-001 (existing) — 37 candidate routes
├── claude-trace-contract.schema.json               # NEW (WP1) — one schema, four $defs
├── claude-runtime-capability-snapshot.json         # NEW (WP1) — committed operator evidence
└── claude-telemetry-capability-profile.json        # NEW (WP2) — versioned telemetry profile

tests/speckit-pro/
├── suite-manifest.json                             # MODIFIED (WP1) — register Layer 4 test
├── layer6-efficiency/lib/
│   ├── claude_capabilities.py                      # NEW (WP1) — operator probe tool + fail-closed writer
│   └── claude_trace_schema.py                      # NEW (WP1) — stdlib record validators
└── unit/
    ├── test-efficiency-claude-telemetry.py         # NEW (WP1); MODIFIED (WP2, WP3)
    ├── test-speckit-pro-runner.py                  # MODIFIED (WP1, WP2) — docs-surface allowlist
    └── fixtures/claude-telemetry-records/
        ├── route-resolution.json                   # NEW (WP2) — standalone route_resolution fixture
        ├── success.json                            # NEW (WP3) — exact-treatment replay, scorable
        ├── null.json                               # NEW (WP3) — nulls preserved, not dropped
        ├── unavailable.json                        # NEW (WP3) — cross-refs snapshot unavailable obs
        └── misdelivery.json                        # NEW (WP3) — observed != resolved, non-scorable
```

**Structure Decision**: Single-project repository tooling. Importable probe/validator modules use snake_case names (`claude_capabilities.py`, `claude_trace_schema.py`) because they are imported by the unit test — deliberately distinct from the existing kebab-case *scripts* in the same `lib/` directory (`quality-scorer.py`, `token-counter.py`), which are invoked as executables and never imported. Committed evidence and the schema contract live under `docs/ai/research/` beside the CAR-001 manifest (Q2); synthetic test fixtures live under the purpose-named `tests/speckit-pro/unit/fixtures/claude-telemetry-records/` directory per the unit-layout contract (no spec-ID-named fixture paths).

## Reviewability Budget & Work-Package Split

**Primary surface**: harness/adapter (the operator-only probe tool `claude_capabilities.py` plus the `claude_trace_schema.py` stdlib validator).
**Secondary surfaces**: schema (one JSON Schema, four `$defs`); seed/config (synthetic record-class fixtures); docs/process (the committed snapshot and telemetry profile under `docs/ai/research/`).
**Budget result**: split required — the ratified 3-slice vertical split (spec "Split decision", design concept Q8). This plan resolves the file-to-slice assignment (design concept Open Question 5).

### Per-work-package file assignment

| File | Op | WP | Requirement |
|------|----|----|-------------|
| docs/ai/research/claude-trace-contract.schema.json | NEW | WP1 | FR-015/FR-017 |
| tests/speckit-pro/layer6-efficiency/lib/claude_trace_schema.py | NEW | WP1 | FR-016/FR-028 |
| tests/speckit-pro/layer6-efficiency/lib/claude_capabilities.py | NEW | WP1 | FR-001/FR-003/FR-023 |
| docs/ai/research/claude-runtime-capability-snapshot.json | NEW | WP1 | FR-011/US1 |
| tests/speckit-pro/unit/test-efficiency-claude-telemetry.py | NEW | WP1 | FR-028/const IV |
| tests/speckit-pro/suite-manifest.json | MODIFIED | WP1 | FR-028 |
| tests/speckit-pro/unit/test-speckit-pro-runner.py | MODIFIED | WP1 | docs-surface guard (schema + snapshot) |
| docs/ai/research/claude-telemetry-capability-profile.json | NEW | WP2 | FR-018/FR-019/FR-020 |
| tests/speckit-pro/unit/fixtures/claude-telemetry-records/route-resolution.json | NEW | WP2 | FR-021 / US3 acceptance scenario 1 |
| tests/speckit-pro/unit/test-efficiency-claude-telemetry.py | MODIFIED | WP2 | telemetry-profile + route_resolution coverage (SC-006) |
| tests/speckit-pro/unit/test-speckit-pro-runner.py | MODIFIED | WP2 | docs-surface guard (telemetry profile) |
| tests/speckit-pro/unit/fixtures/claude-telemetry-records/success.json | NEW | WP3 | FR-025/SC-003 |
| tests/speckit-pro/unit/fixtures/claude-telemetry-records/null.json | NEW | WP3 | FR-025/SC-003 |
| tests/speckit-pro/unit/fixtures/claude-telemetry-records/unavailable.json | NEW | WP3 | FR-025/SC-003 |
| tests/speckit-pro/unit/fixtures/claude-telemetry-records/misdelivery.json | NEW | WP3 | FR-025/SC-003 |
| tests/speckit-pro/unit/test-efficiency-claude-telemetry.py | MODIFIED | WP3 | FR-024/SC-005 (four-class + 37-route join) |

Dependency order: **WP1 → WP2 → WP3**. WP2 consumes the schema WP1 published (authors no new `$defs`). WP3's deterministic test extends the Layer 4 coverage WP1 registered and joins against the snapshot WP1 committed.

### WP1 sizing — mechanical estimator vs. real reviewable LOC (G5 escalation)

The mechanical plan estimator (`estimate-reviewable-loc`) classifies a file as
"production" only when its path starts with `src/`, `app/`, `lib/`, or `scripts/`,
or ends in `.ts/.tsx/.js/.jsx/.mjs/.cjs/.sql`. **Every** CAR-002 file is either
test-tree Python (`tests/speckit-pro/**.py`) or research JSON (`docs/ai/research/**.json`),
so none match — the estimator projects `production: 0`, `projected: 0`, `status: pass`
for the whole feature (recorded output in [research.md](./research.md), Decision R10).

That mechanical result is blind to the real reviewer burden. Hand-estimating WP1's
**authored** surface (excluding the operator-generated snapshot data): `claude_trace_schema.py`
~240-300 LOC + `claude_capabilities.py` ~240-320 LOC + the schema JSON ~240-320 lines +
the WP1 portion of the unit test ~140-200 LOC ≈ **550-820 reviewable LOC**. This
breaches the 400 warn ceiling and may approach the 800 block ceiling under the
PR-time diff-mode reviewability gate, which counts real added lines.

**Escalation (do NOT silently re-slice — the 3-WP boundary is Clarify-ratified):**
This conflict is recorded for **G5**. The spec's own rationale couples WP1's contents
(FR-015/FR-016/FR-028 each mandate exactly one schema file, one validator, one suite
registration, and the fail-closed writer at FR-023 cannot be built or tested without
the schema it validates against), so the WP boundary is sound. Two dispositions for
G5 to choose between, without moving the ratified WP seam:
1. Emit WP1 as a single PR with a documented, ratified over-ceiling reviewability
   exception (recommended — the coupling is atomic and the schema/snapshot JSON are
   low per-line reviewer cost data).
2. Have the PRSG split-PR router emit WP1 as ordered file-level review units within
   the one WP (schema + validator, then probe tool + writer + snapshot), preserving
   the WP1 boundary.
The PR-time diff-mode gate is the true arbiter and will re-measure with real numbers.

### PR review packet source

Each WP PR body draws from spec "PR Review Packet Requirements": what changed, why,
non-goals (corpus execution, scoring, statistics, fallback ordering — deferred to
CAR-003+), review order (WP1→WP2→WP3), scope budget (this section), traceability
(the per-WP table maps files to FR/SC IDs), verification (`python3 tests/speckit-pro/run-all.py`),
known gaps (any CAP-Q recorded open in the snapshot), and rollback (revert the additive
PR; no feature flag — all changes are net-new artifacts).

## Post-Design Constitution Re-Check

Re-evaluated after Phase 1 (data-model, contracts, quickstart): no new violations.
The design adds no plugin surface, no third-party dependency, no repository Bash, and
no persisted route-to-tuple duplication. All six principles remain PASS. The single
reviewability escalation (WP1 sizing) is carried to G5 as documented above and is not
a constitution violation.

## Complexity Tracking

> No constitution violations to justify — table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none)    | (none)     | (none)                              |
