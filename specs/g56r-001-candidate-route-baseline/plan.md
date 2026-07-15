# Implementation Plan: G56R-001 Candidate Route Baseline

**Branch**: `g56r-001-candidate-route-baseline` | **Date**: 2026-07-15 | **Spec**: `specs/g56r-001-candidate-route-baseline/spec.md`

**Input**: Feature specification from `specs/g56r-001-candidate-route-baseline/spec.md`

## Summary

G56R-001 is a documentation-only research spike that prepares one canonical
official-source candidate-route baseline for G56R-002. The implementation will
author `docs/ai/research/codex-agent-route-candidates.md` with a dated official
OpenAI source ledger, twelve role contract records, provisional route records,
fixture backlog records, telemetry questions, invalidation rules, and a strict
go/no-go handoff.

The plan keeps platform facts grounded in official OpenAI documentation only.
Repository files define project inputs, current role inventory, and fixture
state, but they never establish model, effort, platform, telemetry, or Codex
client facts.

## Technical Context

**Language/Version**: Markdown planning and research documentation; repository
verification uses Python 3.11+ standard-library tooling only.

**Primary Dependencies**: No new dependencies. Use existing SpecKit Pro
templates, existing repository validation, official OpenAI documentation, and
read-only project inputs.

**Storage**: Repository Markdown files only. No runtime storage, JSON manifest,
database, cache, payload, or generated artifact is introduced.

**Testing**: Focused document checks, stable-ID/count review, traceability
review, link/scope review, `git diff --check`, Layer 1 validation, then the
default Python-authoritative repository suite after implementation.

**Target Platform**: Repository documentation. Platform-independent and not
installed into plugin runtime surfaces.

**Project Type**: Documentation-only research spike.

**Performance Goals**: Deterministic reviewability rather than runtime
performance: exact counts for 9 source records, 12 role contracts, 12 fixture
backlog records, no unsupported admitted seed candidates, and zero production
runtime files.

**Constraints**: Official OpenAI documentation is the only authority for
platform facts. Project inputs must be labeled `project_input`. The report must
create no runtime behavior, model probes, live evaluation, fixture payloads,
agent definitions, installer changes, generated payloads, cache proofs,
version changes, schema files, helper scripts, or fallback policy.

**Scale/Scope**: One canonical implementation report with a bounded planning
package. The report covers 9 official-source ledger records, 12 role contract
records, 12 fixture backlog records, provisional route records, and one
G56R-002 handoff decision.

**Reviewability Budget**: Primary surface: docs/process. Secondary surfaces:
none. Projected reviewable production LOC: 0. Projected production files: 0.
Projected implementation files: 1. Budget result: within budget.

## Declared File Operations

- NEW docs/ai/research/codex-agent-route-candidates.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Plan Evidence |
|---|---|---|
| I. Plugin Structure Compliance | Pass | No plugin manifest, skill, agent, hook, generated payload, or repository-only test layout change is planned. |
| II. Cross-Platform Runtime and Script Safety | Pass | No active script, Bash, `jq`, package install, runtime helper, or platform-specific implementation is planned. |
| III. Semantic Versioning | Pass | No plugin or marketplace version files are in scope. |
| IV. Test Coverage Before Merge | Pass | The implementation phase will run focused document checks, Layer 1 validation, and the default repository suite before completion. |
| V. Conventional Commits | Pass | Phase commits use repository-approved conventional commit subjects. |
| VI. KISS, Simplicity, and YAGNI | Pass | One canonical report keeps the source ledger, contracts, candidates, fixtures, telemetry questions, and decision matrix in one reviewable artifact. |

No constitution violation or split exception is required.

## Project Structure

### Documentation

```text
specs/g56r-001-candidate-route-baseline/
├── SPEC-MOC.md
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── codex-agent-route-candidates.contract.md
└── tasks.md
```

### Implementation Output

```text
docs/ai/research/
└── codex-agent-route-candidates.md
```

### Read-Only Project Inputs

```text
docs/ai/specs/
├── codex-gpt-5-6-agent-routing-technical-roadmap.md
└── codex-gpt-5-6-agent-routing-roadmap-MOC.md

docs/
└── prd-codex-gpt-5-6-agent-routing.md

speckit-pro/
├── codex-agents/
└── agents/

tests/speckit-pro/layer6-efficiency/
```

**Structure Decision**: Use the existing feature planning directory for
planning artifacts and produce exactly one implementation artifact under
`docs/ai/research/`. All plugin, payload, cache, fixture, installer, and
version surfaces remain read-only.

## Phase 0: Research

Resolve planning decisions in `research.md` before authoring tasks:

- official-source snapshot and invalidation policy
- one-report architecture
- stable record IDs and relationships
- candidate admission and rejection classifications
- role-contract field model
- fixture backlog field model
- deterministic verification strategy
- no-runtime and no-payload boundaries

Research output must not admit any platform fact. It defines how the
implementation will retrieve and classify official documentation.

## Phase 1: Design

Produce record definitions in `data-model.md`, a planning-only report contract
in `contracts/codex-agent-route-candidates.contract.md`, and implementation
verification guidance in `quickstart.md`.

Design output must keep source authority explicit:

- `official_documentation` establishes platform facts.
- `project_input` defines repository state and role intent.
- `runtime_verification_needed` is deferred to G56R-002.
- `qualification_needed` is deferred to G56R-003 and later.
- `undocumented` blocks candidate admission.

## Implementation Approach

1. Revalidate official OpenAI documentation at report-authoring time and record
   direct URLs, retrieval date, source family, documented facts, claim bindings,
   and invalidation triggers.
2. Inventory current Codex TOML roles, Claude parity-role files, and current
   fixture inputs as `project_input`.
3. Compute instruction and full-file hashes for all twelve role records where
   a source file exists.
4. Build provisional candidate route records only from official-source support
   plus role-contract fit.
5. Reject or block every seed or candidate that depends on undocumented,
   deprecated, withdrawn, runtime-only, or qualification-only facts.
6. Complete the three-current/nine-missing fixture backlog without creating or
   executing fixture payloads.
7. Finish with traceability, count checks, scope checks, repository validation,
   and the strict G56R-002 go/no-go decision.

## Verification Strategy

Minimum implementation verification:

- marker search across the feature directory and canonical report
- exact count checks for source, role, and fixture records
- traceability review for all platform claims and candidate records
- changed-file scope review proving no runtime, installer, payload, cache,
  fixture payload, generated artifact, or version change
- `git diff --check`
- `python3 tests/speckit-pro/run-all.py --layer 1`
- `python3 tests/speckit-pro/run-all.py`

If official documentation is unreachable or does not support a required
candidate, the report must record the failure as `undocumented`,
`rejected_deprecated_or_withdrawn`, or `blocked_pending_capability` rather than
substituting repository state or runtime observation.

## Complexity Tracking

No complexity violations.
