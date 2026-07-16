# Implementation Plan: G56R-001 Candidate Route Baseline

**Branch**: `g56r-001-candidate-route-baseline` | **Date**: 2026-07-15 | **Spec**: `specs/g56r-001-candidate-route-baseline/spec.md`

**Input**: Feature specification from `specs/g56r-001-candidate-route-baseline/spec.md`

## 2026-07-16 Evidence-Parity Amendment

The original one-report plan remains historical. The active implementation
surface is now one canonical human report plus one schema-v2 planning manifest,
governed by the shared CAR/G56R parity contract and schema. The manifest is not
runtime configuration or an installer input. It adds no runtime, payload,
cache, generated-artifact, agent, or version behavior.

## Summary

G56R-001 is a planning-evidence research spike that prepares one canonical
official-source candidate-route baseline for G56R-002. The implementation
authors `docs/ai/research/codex-agent-route-candidates.md` and its sole
schema-v2 planning companion with a dated official OpenAI source ledger,
twelve role contract records, provisional route records, fixture backlog
records, telemetry questions, invalidation rules, and a strict go/no-go
handoff.

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

**Storage**: Repository Markdown plus one governed JSON planning manifest. No
runtime storage, runtime manifest, database, cache, payload, or generated
artifact is introduced.

**Testing**: Focused document checks, stable-ID/count review, traceability
review, link/scope review, `git diff --check`, Layer 1 validation, then the
default Python-authoritative repository suite after implementation.

**Target Platform**: Repository documentation. Platform-independent and not
installed into plugin runtime surfaces.

**Project Type**: Documentation-only research spike.

**Performance Goals**: Deterministic reviewability rather than runtime
performance: the current schema-v2 manifest has exact counts of 21 source
records, 5 effort-surface records, 17 project-input records, 12 role contracts,
23 candidate route records, 12 fixture backlog records, 24 traceability
records, 5 decisions, no unsupported admitted seed candidates, and zero
production runtime files.

**Constraints**: Official OpenAI documentation is the only authority for
platform facts. Project inputs must be labeled `project_input`. The report must
create no runtime behavior, model probes, live evaluation, fixture payloads,
agent definitions, installer changes, generated payloads, cache proofs,
version changes, platform-specific or runtime schema files, helper scripts, or
fallback policy. The shared planning schema and manifest are allowed.

**Scale/Scope**: One canonical implementation report, one governed planning
manifest, and a bounded planning package. The current manifest covers 21
official-source ledger records, 5 effort-surface records, 17 project-input
records, 12 role contract records, 23 source-bound blocked or comparator route
records, 12 fixture backlog records, 24 traceability records, and 5 decisions.

**Reviewability Budget**: Primary surface: docs/process. Secondary surfaces:
repository test guard allowlist only when the new research path must be
explicitly admitted by the changed-surface guard. Projected reviewable
production LOC: 0. Projected production files: 0. Projected implementation
files: 1. Post-review remediation expanded process/checklist files but kept
runtime production files at 0. Actual branch-diff reviewability is 25
docs/process/test-guard files: warning-only above the 15-file warning threshold
and not above the 25-file block threshold.

## Declared File Operations

- NEW docs/ai/research/codex-agent-route-candidates.md
- NEW docs/ai/research/codex-agent-route-candidate-manifest.json
- NEW specs/g56r-001-candidate-route-baseline/ planning package, including
  spec, plan, research, data model, contract, quickstart, checklists, tasks,
  verification report, retrospective, and SPEC-MOC
- NEW docs/ai/specs/.process/G56R-001-design-concept.md
- NEW docs/ai/specs/.process/G56R-001-workflow.md
- MODIFY docs/ai/specs/.process/autopilot-state.json
- MODIFY docs/prd-codex-gpt-5-6-agent-routing.md,
  docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md, and
  docs/ai/specs/codex-gpt-5-6-agent-routing-roadmap-MOC.md to connect the
  G56R-001 package to the roadmap and downstream G56R-002 handoff
- MODIFY tests/speckit-pro/unit/test-speckit-pro-runner.py for the
  changed-surface guard allowlist that admits the new Codex research report
  path while keeping production runtime files at zero

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Plan Evidence |
|---|---|---|
| I. Plugin Structure Compliance | Pass | No plugin manifest, skill, agent, hook, generated payload, or repository-only test layout change is planned. |
| II. Cross-Platform Runtime and Script Safety | Pass | No active script, Bash, `jq`, package install, runtime helper, or platform-specific implementation is planned. |
| III. Semantic Versioning | Pass | No plugin or marketplace version files are in scope. |
| IV. Test Coverage Before Merge | Pass | The implementation phase will run focused document checks, Layer 1 validation, and the default repository suite before completion. |
| V. Conventional Commits | Pass | Phase commits use repository-approved conventional commit subjects. |
| VI. KISS, Simplicity, and YAGNI | Pass | One canonical human report and one shared-schema planning manifest keep the evidence reviewable without introducing a runtime policy artifact. |

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
├── codex-agent-route-candidates.md
└── codex-agent-route-candidate-manifest.json
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
├── codex-skills/
└── agents/

tests/speckit-pro/layer6-efficiency/
dist/codex/speckit-pro/
dist/claude/speckit-pro/
```

**Structure Decision**: Use the existing feature planning directory and
produce exactly one human report plus one governed planning manifest under
`docs/ai/research/`. All plugin, payload, cache, fixture, installer, and version
surfaces remain read-only.

## Phase 0: Research

Resolve planning decisions in `research.md` before authoring tasks:

- official-source snapshot and invalidation policy
- report-plus-governed-manifest evidence architecture
- stable record IDs and relationships
- active route-policy project-input inventory with stable IDs
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
   source family, retrieval method, requested URLs, canonical URLs, retrieval
   timestamp, documented facts, claim bindings, and invalidation triggers.
2. Inventory current Codex TOML roles, Claude parity-role files, and current
   fixture inputs as `project_input`.
3. Compute instruction and full-file hashes for all twelve role records where
   a source file exists.
4. Build provisional candidate route records only from official-source support,
   exact source-fact bindings, candidate rationale, and role-contract fit.
5. Reject or block every seed or candidate that depends on undocumented,
   deprecated, withdrawn, runtime-only, or qualification-only facts.
6. Complete the three-current/nine-missing fixture backlog without creating or
   executing fixture payloads.
7. Finish with stable traceability IDs, stable go/no-go decision IDs, count
   checks, scope checks, repository validation, and the strict G56R-002
   go/no-go decision.

## Verification Strategy

Minimum implementation verification:

- marker search across the feature directory and canonical report
- exact count checks for source, role, and fixture records
- stable-ID traceability review for all platform claims and candidate records
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
