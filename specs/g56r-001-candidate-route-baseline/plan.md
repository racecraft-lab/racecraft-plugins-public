# Implementation Plan: Candidate Route Baseline and Role Contracts

**Branch**: `g56r-001-candidate-route-baseline` | **Date**: 2026-07-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/g56r-001-candidate-route-baseline/spec.md`

## Summary

Complete one evidence-first working-day research spike that publishes a cited
Markdown narrative and a separate agent-centric JSON manifest for exactly twelve
named agents. Implementation will gather current OpenAI platform facts only from
official OpenAI sources, gather project facts only from classified repository or
sanitized environment evidence, bind readable IDs to deterministic hashes, and
run one feature-local Python checker before emitting an objective G56R-002 go or
no-go handoff. The slice changes no production, plugin, installer, payload,
cache, installed-state, route, default, or version file.

## Technical Context

**Language/Version**: Markdown, standard JSON, and Python 3.11+

**Primary Dependencies**: Python standard library only (`json`, `hashlib`,
`unicodedata`, `pathlib`, `re`, and `datetime` as needed); no package install

**Storage**: Three checked-in files: one Markdown narrative, one UTF-8 JSON
manifest, and one feature-local read-only checker

**Testing**: `python3 specs/g56r-001-candidate-route-baseline/check-artifacts.py`;
`python3 tests/speckit-pro/run-all.py --layer 4`; final deterministic
`python3 tests/speckit-pro/run-all.py`

**Target Platform**: Repository review on any Python 3.11+ host; recorded Codex
claims remain separately scoped to `cli`, `desktop_app`, `app_server`, and
`non_interactive`

**Project Type**: Research documentation plus a delivery-specific validation
script; no runtime component

**Performance Goals**: Deterministic repeatability rather than throughput; two
successive checker runs over unchanged files return the same result and hashes

**Constraints**: One scheduled maintainer workday; zero production LOC; official
OpenAI sources only for platform facts; repository evidence only for project
facts; sanitized local observations; no runtime probing, scoring,
qualification, final route ordering, production mutation, defect repair, Bash,
`jq`, subprocess shell execution, dependency, reusable schema package, or
validator framework

**Scale/Scope**: Exactly 12 agents, 10 present production routes, 2 explicitly
absent routes, 4 independent Codex surfaces, 3 current fixtures, 9 missing
fixtures, all evidence-supported project-level candidates, and one terminal
handoff decision

**Reviewability Budget**: Primary surface `docs/process`; 0 projected
reviewable production LOC; 0 production files; 3 total delivery files; one
primary surface; within the `speckit-pro-reviewability` v1.0.0 warn threshold of
400 LOC and block threshold of 800 LOC

## Declared File Operations

- NEW docs/ai/research/codex-agent-route-candidates.md
- NEW docs/ai/research/codex-agent-route-candidate-manifest.json
- NEW specs/g56r-001-candidate-route-baseline/check-artifacts.py

These are the complete implementation operations. The checker is intentionally
feature-local and disposable; it is not registered as a reusable repository
framework. All other source, cache, installed-state, agent, fixture, and policy
paths are read-only evidence inputs.

## Constitution Check

*GATE: Passed before Phase 0 research. Re-checked after Phase 1 design below.*

### Pre-design gate

| Principle | Result | Plan evidence |
|---|---|---|
| I. Plugin Structure Compliance | PASS | No plugin file changes. The only executable check remains outside the shipped plugin under the feature spec directory. Layer 1 remains available as part of the default suite. |
| II. Cross-Platform Runtime & Script Safety | PASS | The checker uses Python 3.11+ standard-library structured JSON and path APIs, deterministic UTF-8, and no Bash, `jq`, package, or shell subprocess. |
| III. Semantic Versioning | PASS | No plugin manifest or version changes are planned. |
| IV. Test Coverage Before Merge | PASS | The delivery-specific checker is the focused acceptance test for both artifacts; direct execution is followed by Layer 4 and the default Python-authoritative suite. No reusable helper or production component is introduced. |
| V. Conventional Commits | PASS | The parent workflow owns the phase and final Conventional Commit checkpoints. |
| VI. KISS, Simplicity & YAGNI | PASS | Three delivery files, one flat agent-centric manifest, and one direct checker; no framework, package, router, installer, or abstraction layer. |

Additional scope gates also pass: the plan preserves split evidence authority,
independent surface records, tracked/cache/installed separation, eligibility
versus availability, and the no-probe/no-score/no-mutation boundary.

## Design Decisions

The ratified Design Concept decisions are implemented as follows:

| Accepted decision | Plan application |
|---|---|
| "Markdown + JSON" | Human-readable cited narrative and separate versioned manifest. |
| "All eligible routes" | Include every evidence-supported project candidate; absence on this machine is not exclusion evidence. |
| "Separate surface records" | `cli`, `desktop_app`, `app_server`, and `non_interactive` never inherit evidence from one another. |
| "Record separately" | Tracked source, cache, and installed observations use distinct records; tracked source remains authoritative for production project facts. |
| "Semantic parity" | The two absent Codex roles derive contracts from Claude semantics without copying Claude transport/configuration mechanics. |
| "Readable IDs + hashes" | Stable readable IDs bind to canonical instruction and contract SHA-256 hashes. |
| "Only evidence-justified variants" | Every variant has a bounded overhead hypothesis and an unchanged-treatment control. |
| "Focused artifact checks" | One feature-local Python script validates structure, identity, hashes, provenance, sanitization, and agreement. |
| "Hypotheses, no final order" | Candidate signals remain unqualified hypotheses; lexical display order carries no routing meaning. |
| "Classify and hand off" | Documentation/inventory questions finish here; executable capability and scoring questions go to G56R-002/G56R-003. |
| "Objective completeness gate" | The same declared checks reproduce the terminal decision. |
| "Stop at one day" | The recorded stop time ends work; incomplete conditions produce `no_go`, not scope extension. |
| "Exclude the candidate" | A cited hard-contract incompatibility makes the candidate ineligible. |
| "Record and leave unresolved" | Equal-authority or applicability conflicts remain explicit and terminally classified. |
| "Per-agent fixture contracts" | All 12 records include status, task, input, output, and hard-contract assertions. |
| "Agent-centric records" | Each agent keeps its contract, route/absence, candidates, provenance, fixture, and unknowns together. |
| "Sanitized facts and hashes" | Local records exclude absolute/home paths, identities, credentials, secrets, and unrelated settings. |
| "URL + date + applicability" | Official claims carry exact locator, retrieval date, surface, documented scope, applicability, conflict status, and invalidation trigger. |
| "Record only, do not fix" | Inventory defects become evidence-backed findings with owners; no baseline input is repaired. |
| "Keep eligibility separate" | `project_eligibility` never derives from `installation_availability`, which remains `unresolved_g56r_002`. |

Q5 is controlling where earlier answers conflict: official OpenAI documentation
is exclusive for external platform facts, while tracked repository evidence is
authoritative only for SpecKit Pro project facts.

## One-Working-Day Execution Sequence

The implementation records `started_at` and the scheduled workday `deadline_at`
before step 1 and `stopped_at` at the terminal boundary. All three use RFC 3339
timestamps with explicit UTC offsets and satisfy
`started_at <= stopped_at <= deadline_at`. Steps are sequential because later
records depend on frozen evidence and contract identities. Parallel source
reading is allowed only when source sets are disjoint and reconciliation uses
the predeclared rules.

1. **Freeze the record contract**: record repository revision, research date,
   workday boundary, claim labels, evidence classes, four surfaces,
   sanitization rules, canonicalization, conflict outcomes, and checker
   invariants before drawing conclusions.
2. **Collect official platform evidence**: use the selected runtime research
   capability to inspect current official OpenAI documentation for the FR-016
   topics. Record URL, exact locator, retrieval date, surface, version/client
   scope, applicability, conflicts, and invalidation trigger. Do not infer
   executable availability.
3. **Inventory project evidence**: at one recorded revision, inspect active
   route-policy sources and consumers plus ten Codex definitions, the two
   Claude semantic sources, fixture inventory, cache, and sanitized installed
   observations. Keep each evidence class separate and record defects only.
4. **Build identities and role contracts**: derive twelve complete FR-006
   semantic contracts, canonical instruction bodies, hashes, and immutable
   present/absent production-route records.
5. **Enumerate candidates and fixture contracts**: include every
   evidence-supported eligible model/effort/treatment tuple, record exclusions
   only from cited contract evidence, retain unchanged controls, and describe
   the exact three-current/nine-missing fixture backlog.
6. **Write both artifacts**: author the evidence matrix, role catalog,
   telemetry needs, classified unknowns, and candidate hypotheses in Markdown;
   encode the matching agent-centric projection in JSON.
7. **Run focused validation**: execute the feature-local checker twice, inspect
   its deterministic result, run Layer 4, and run the default deterministic
   suite. Validation is offline, read-only, and performs no probing or
   qualification.
8. **Stop and hand off**: no later than the predeclared `deadline_at`, emit `go`
   only if every FR-024 condition passes with no blocking conflict or
   unclassified unknown. Otherwise emit the exact `no_go` payload without
   extending work or reducing deliverables.

## Evidence and Validation Design

The narrative carries one evidence matrix keyed by claim/evidence ID, source,
exact locator, retrieval date or observation date, surface, documented scope,
applicability, classification, conflict status, and invalidation trigger.
Project records additionally cite repository-relative path, revision, and
evidence role. Cache and installed observations use logical locators only.

The checker reads fixed paths and fails closed on:

- invalid JSON, manifest type/version/date, or non-deterministic UTF-8 content;
- any deviation from exactly 12 unique agents, 10 present routes, and the two
  named absent routes;
- incomplete semantic contracts, routes, candidates, evidence, independent
  surfaces, fixture contracts, telemetry requirements, or classified unknowns;
- malformed/duplicate/reused IDs, malformed hashes, or canonicalization/hash
  mismatches;
- route-to-contract binding drift, an evidenced hard-incompatible candidate
  remaining eligible, missing unchanged controls, unsupported exclusion
  reasons, conflated project eligibility and installed availability, or
  qualification/final-order claims;
- unsafe local fields or path/credential/secret patterns;
- disagreement between normalized Markdown and JSON projections; or
- a freshness or invalidation rule violation; or
- a terminal decision or recorded workday boundary that cannot be reproduced
  from the completion checks.

The checker does not fetch, probe, score, qualify, mutate, or provide reusable
schema APIs. Its human-readable success output lists the validated artifact
paths, counts, manifest version, and reproduced handoff state.

## Requirement and Acceptance Traceability

| Requirement group | Planned evidence | Verification |
|---|---|---|
| AC-1.1 / FR-002–FR-005 | Narrative inventory; 12 agent records; active producer/consumer surfaces; separated source observations | Exact-set, route-count, evidence-class, and inventory-completeness checks |
| AC-1.2 / FR-016–FR-020 | Official-source platform fact matrix with four independent surface records | Provenance, applicability, conflict, no-cross-surface-inheritance checks |
| AC-1.3 / FR-006–FR-015, FR-022 | Contracts, candidates, production routes/absences, fixture contracts | Required-field, ID, hash, candidate-control, exclusion, and 3/9 checks |
| AC-1.4 / FR-018–FR-019 | Visible claim classifications and terminal conflict states | Allowed-enum and unresolved-conflict checks |
| AC-1.5 / FR-023–FR-025 | Telemetry requirements, classified unknowns, timestamps, completion checks, handoff | Owner, timebox, objective gate, and reproducibility checks |
| AC-1.6 / FR-001, FR-008–FR-013 | Versioned agent-centric JSON and matching narrative | JSON, version, projection-agreement, eligibility/availability checks |
| AC-1.7 / FR-022, FR-027 | Exact fixture backlog and `non_release_evidence` labels | Fixture-set, label, and prohibited-claim checks |
| FR-021, FR-026 | Sanitized observations and focused standard-library checker | Forbidden-field/path scan and direct checker execution |

## PR Review Packet Source

The eventual PR description is generated from the narrative's summary and
handoff, the manifest's completion state, the checker output, and this plan's
declared operations. It must state:

- **What/why**: a research baseline for G56R-002, not a route change.
- **Non-goals**: probing, scoring, qualification, ordering, mutation, fixes,
  frameworks, and platform claims without official evidence.
- **Review order**: narrative, manifest, checker, then recorded command output.
- **Scope budget**: one docs/process surface, 0 production LOC/files, 3 files.
- **Traceability**: the table above plus checker evidence for AC-1.1–AC-1.7.
- **Known gaps**: each item names G56R-002, G56R-003, or another exact owner.
- **Rollback/flags**: revert the three files; no runtime feature flag applies.

## Project Structure

### Documentation and planning (this feature)

```text
specs/g56r-001-candidate-route-baseline/
├── SPEC-MOC.md
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── check-artifacts.py                 # Phase 7 delivery-specific checker
└── contracts/
    └── agent-route-candidate-manifest.md
```

### Delivery and read-only evidence surfaces

```text
docs/ai/research/
├── codex-agent-route-candidates.md
└── codex-agent-route-candidate-manifest.json

speckit-pro/
├── codex-agents/                      # read-only current Codex definitions
└── agents/                            # read-only Claude parity sources

tests/speckit-pro/layer6-efficiency/   # read-only fixture inventory
```

**Structure Decision**: The primary review surface is `docs/process`. The two
published research files live with existing research records, while the
one-off checker lives with its feature contract so it can be archived with the
spec instead of becoming permanent infrastructure. All runtime, plugin, test
harness, installer, generated-payload, and environment surfaces remain
read-only.

## Post-design Constitution Re-check

| Principle | Result after data model and contracts | Evidence |
|---|---|---|
| I. Plugin Structure Compliance | PASS | Design adds no shipped plugin content; all three delivery operations remain outside `speckit-pro/`. |
| II. Cross-Platform Runtime & Script Safety | PASS | The contract requires structured JSON, deterministic UTF-8, `pathlib`, Python 3.11+, and no shell/dependencies. |
| III. Semantic Versioning | PASS | Manifest version is the research-data contract version, not a plugin version; no release metadata changes. |
| IV. Test Coverage Before Merge | PASS | `quickstart.md` defines direct focused validation, repeatability, Layer 4, and default-suite commands. |
| V. Conventional Commits | PASS | No design artifact introduces a commit-policy exception. |
| VI. KISS, Simplicity & YAGNI | PASS | The data model is explicit and agent-centric; one fixed-path checker replaces any schema package or generic validation layer. |

No constitution violation or split exception remains. The design stays at 0
production LOC/files and 3 total delivery files, below all reviewability
thresholds.

## Complexity Tracking

No constitution violations require justification.
