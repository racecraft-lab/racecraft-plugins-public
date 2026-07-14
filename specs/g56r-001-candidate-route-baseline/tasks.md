# Tasks: Candidate Route Baseline and Role Contracts

**Input**: Design documents from `specs/g56r-001-candidate-route-baseline/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/agent-route-candidate-manifest.md`, `quickstart.md`, and
`docs/ai/specs/.process/G56R-001-design-concept.md`

**Delivery boundary**: Exactly three research delivery files:

- `docs/ai/research/codex-agent-route-candidates.md`
- `docs/ai/research/codex-agent-route-candidate-manifest.json`
- `specs/g56r-001-candidate-route-baseline/check-artifacts.py`

The checked-in checker also requires exactly two validation-path changes:

- `tests/speckit-pro/unit/test-g56r-001-artifacts.py`
- `tests/speckit-pro/suite-manifest.json`

No production, plugin, agent, installer, payload, cache, installed-state,
default-route, version, generated-release, or unrelated file is modified. The
checker is delivery-specific, offline, read-only, Python 3.11+ standard-library
code; its focused Layer 4 coverage and suite entry do not create a reusable
validation framework.

**Organization**: All tasks implement the sole P1 maintainer story. The phases
form one ordered working-day sequence. No task is marked `[P]` because each
increment either shares a delivery file or depends on the preceding frozen
evidence and identity results.

## Phase 1: Start the Clock and Build the Checker Test-First

**Goal**: Record the workday boundary before implementation, then establish the
artifact invariants through focused Layer 4 RED/GREEN cycles before authoring
conclusions.

**Independent Test**: The focused unit file passes after three verified RED/GREEN
increments, and the checker exits non-zero with a precise missing-artifact
failure without network, probe, scoring, qualification, or mutation behavior.

- [ ] T001 [US1] Create the research-boundary header in `docs/ai/research/codex-agent-route-candidates.md` and record RFC 3339 `started_at` plus the scheduled `deadline_at` before any checker or evidence work begins (AC-1.5)
- [ ] T002 [US1] Write focused missing-artifact, fixed-path, offline, and read-only assertions in `tests/speckit-pro/unit/test-g56r-001-artifacts.py`, run that file directly, and record verified RED assertion failures before the checker exists (AC-1.5, AC-1.6)
- [ ] T003 [US1] Declare `tests/speckit-pro/unit/test-g56r-001-artifacts.py` in Layer 4 of `tests/speckit-pro/suite-manifest.json` without changing any other layer or test entry (AC-1.5)
- [ ] T004 [US1] Implement the fixed artifact paths, manifest envelope, exact 12/10/2 and 3/9 sets, four surfaces, one-day timestamp rules, sanitization prohibitions, and precise missing-artifact behavior in `specs/g56r-001-candidate-route-baseline/check-artifacts.py`, then rerun T002 to verified GREEN (AC-1.1, AC-1.4, AC-1.5, AC-1.6, AC-1.7)
- [ ] T005 [US1] Add canonicalization, readable-ID, hash-format, manifest-content-hash omission, route-to-contract binding, candidate tuple/control, and eligibility-versus-availability assertions to `tests/speckit-pro/unit/test-g56r-001-artifacts.py`, then run it and record verified RED assertion failures (AC-1.3, AC-1.6)
- [ ] T006 [US1] Implement the T005 canonicalization, identity, self-reference-free manifest hash, binding, candidate, and availability checks in `specs/g56r-001-candidate-route-baseline/check-artifacts.py`, then rerun the focused unit file to verified GREEN (AC-1.3, AC-1.6)
- [ ] T007 [US1] Add assertions for route-policy inventory links, provenance, freshness, independent surfaces, source observations, parity mappings, fixture contracts, telemetry, classified unknowns, cross-artifact agreement, and reproducible handoff to `tests/speckit-pro/unit/test-g56r-001-artifacts.py`, then record verified RED assertion failures (AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7)
- [ ] T008 [US1] Implement the T007 fixed-shape and agreement checks in `specs/g56r-001-candidate-route-baseline/check-artifacts.py`, rerun the focused unit file to verified GREEN, then run the checker and confirm its only remaining failure is the not-yet-complete narrative and manifest (AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7)

**Checkpoint**: The workday is measured, the checker has focused Layer 4
coverage, and artifact invariants are executable before conclusions are written.

---

## Phase 2: Collect and Reconcile Evidence

**Goal**: Freeze evidence authority, then inventory platform and project facts
without crossing surfaces or allowing environment observations to redefine
tracked source.

**Independent Test**: A maintainer can trace every claim and route-policy
integration point to a classified, dated source at the pinned revision or to a
sanitized logical environment observation.

- [ ] T009 [US1] Complete the frozen research header in `docs/ai/research/codex-agent-route-candidates.md` with `research_date`, pinned repository revision, official-versus-project authority, tracked/cache/installed separation, four-surface isolation, claim labels, freshness/invalidation, sanitization, conflict rules, and non-goals before collecting conclusions (AC-1.1, AC-1.2, AC-1.4, AC-1.5)
- [ ] T010 [US1] Research current official OpenAI sources for model identifiers, custom-agent fields, reasoning controls, capability discovery, telemetry, reroute events, and non-interactive output, then record URL, exact locator, retrieval date, documented scope, applicability, conflict state, invalidation trigger, and independent `cli`, `desktop_app`, `app_server`, and `non_interactive` records in `docs/ai/research/codex-agent-route-candidates.md` (AC-1.2, AC-1.4)
- [ ] T011 [US1] Inventory each active route-policy source, installer, skill, validation, evaluation, generated-payload, cache, and installed consumer exactly once with stable entry ID, repository-relative or logical locator, producer/consumer role, affected agents and fields, authority/evidence class, canonical-or-derived relationship, reciprocal links, revision/version, observation date, mismatch state, and defect owner in `docs/ai/research/codex-agent-route-candidates.md` (AC-1.1)
- [ ] T012 [US1] Record separate tracked-source, cached-source, and sanitized installed-state observations for all twelve agents using only permitted fields and logical local locators, and record each mismatch as an owned defect without fixing it or changing the tracked contract in `docs/ai/research/codex-agent-route-candidates.md` (AC-1.1, AC-1.4)
- [ ] T013 [US1] Reconcile evidence using the frozen authority rules, reclassify unavailable or stale facts, assign every unresolved conflict `blocking_no_go` or owned `nonblocking_deferred`, and ensure no inference or local observation is presented as a platform fact in `docs/ai/research/codex-agent-route-candidates.md` (AC-1.2, AC-1.4, AC-1.5)

**Checkpoint**: Evidence classes, surfaces, freshness, conflicts, and inventory
relationships are complete before role or candidate conclusions.

---

## Phase 3: Build Contracts, Candidates, Fixtures, and Unknowns

**Goal**: Produce the complete twelve-role baseline and downstream research
handoff without probing, scoring, qualification, or route ordering.

**Independent Test**: The narrative contains twelve complete semantic role
contracts, ten immutable current routes, two explicit absences, every
evidence-supported candidate, exact fixture coverage, and owned unknowns.

- [ ] T014 [US1] Derive complete FR-006 semantic contracts and immutable tracked production routes for the ten current Codex agents from `speckit-pro/codex-agents/`, recording permitted/prohibited behavior and stop/escalation conditions for every hard boundary in `docs/ai/research/codex-agent-route-candidates.md` (AC-1.1, AC-1.3, AC-1.6)
- [ ] T015 [US1] Derive `consensus-synthesizer` and `gate-validator` semantic contracts from the corresponding `speckit-pro/agents/` instruction bodies, record all twelve field-level parity mappings and justified Codex adaptations, and record explicit absent Codex production routes in `docs/ai/research/codex-agent-route-candidates.md` (AC-1.1, AC-1.3, AC-1.6)
- [ ] T016 [US1] Calculate and record one stable contract ID plus repeatable instruction and contract hashes for each of the twelve contracts, and bind each present route to its enclosing contract without encoding preference rank in `docs/ai/research/codex-agent-route-candidates.md` (AC-1.3, AC-1.6)
- [ ] T017 [US1] Enumerate every evidence-supported project-level model/effort/treatment candidate, retain each immutable production baseline and each justified unchanged control, cite all inclusion or hard-contract exclusion evidence, keep installation availability `unresolved_g56r_002`, and label all preference signals as unqualified hypotheses in `docs/ai/research/codex-agent-route-candidates.md` (AC-1.2, AC-1.3, AC-1.4, AC-1.6)
- [ ] T018 [US1] Define actionable fixture contracts for all twelve agents, classifying exactly `codebase-analyst`, `domain-researcher`, and `spec-context-analyst` as current and the other nine as missing, with repository-relative paths or null, representative inputs, expected outputs, hard-contract assertions, and historical prompt emulation labeled `non_release_evidence` in `docs/ai/research/codex-agent-route-candidates.md` (AC-1.3, AC-1.7)
- [ ] T019 [US1] Record per-agent telemetry requirements and classify every remaining question as closed G56R-001 documentation/inventory work, G56R-002 executable-capability work, or G56R-003 replay/scoring/qualification work with impact, exact owner, and required follow-up in `docs/ai/research/codex-agent-route-candidates.md` (AC-1.4, AC-1.5, AC-1.7)

**Checkpoint**: The human-readable baseline is complete and contains no runtime
availability, qualification, preferred-route, fallback-order, or defect-fix
claim.

---

## Phase 4: Assemble the Agent-Centric Manifest

**Goal**: Encode the cited narrative as a separate, self-contained JSON
projection without adding normalized top-level routing tables.

**Independent Test**: JSON parsing yields exactly twelve unique records with
the required route states, identities, bindings, evidence, fixtures, and owned
unknowns.

- [ ] T020 [US1] Create the UTF-8 agent-centric envelope and twelve lexically presented agent records in `docs/ai/research/codex-agent-route-candidate-manifest.json`, encoding each complete contract, canonical IDs/hashes, and immutable present route or cited absence with explicit nulls (AC-1.1, AC-1.3, AC-1.6)
- [ ] T021 [US1] Encode every candidate, capability requirement, rationale, incompatibility, qualification requirement, provenance record, invalidation trigger, source observation, independent surface record, fixture contract, telemetry requirement, and classified unknown in `docs/ai/research/codex-agent-route-candidate-manifest.json`, using explicit empty arrays and permitted nulls where required (AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7)
- [ ] T022 [US1] Finalize the normalized twelve-agent projection and evidence-backed candidate rationale in `docs/ai/research/codex-agent-route-candidates.md` so it agrees field-for-field with `docs/ai/research/codex-agent-route-candidate-manifest.json` while remaining a cited human review record rather than generated policy (AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.6, AC-1.7)

**Checkpoint**: Both artifacts are complete enough for objective pre-handoff
validation.

---

## Phase 5: Validate and Emit the Terminal Handoff

**Goal**: Reproduce the objective decision, stop within the declared workday,
and leave a review-ready three-file research delivery with its two required
validation-path changes.

**Independent Test**: Two focused checker runs return the same result; a
maintainer reviewing narrative, manifest, and checker reaches the same terminal
decision without undocumented context.

- [ ] T023 [US1] Run `python3 specs/g56r-001-candidate-route-baseline/check-artifacts.py`, correct only in-scope completeness or agreement defects in the three declared delivery files, and preserve evidence for every remaining failed gate without probing, scoring, qualifying, mutating, or fixing source defects (AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7)
- [ ] T024 [US1] Run `python3 tests/speckit-pro/unit/test-g56r-001-artifacts.py`, `python3 tests/speckit-pro/run-all.py --layer 4`, `python3 tests/speckit-pro/run-all.py --integration`, and `python3 tests/speckit-pro/run-all.py`, preserving exact results for the handoff and confirming that the only suite-manifest change is the focused Layer 4 declaration while all production surfaces remain unchanged (AC-1.5)
- [ ] T025 [US1] Classify all remaining unknowns and publish the reproducible `go` or precise `no_go` packet, final `stopped_at`, completion checks, self-reference-free manifest content hash, G56R-002 capability-snapshot requirement, admission binding or unmet conditions, validation evidence, AC-1.1–AC-1.7 traceability, review order, 0-production-LOC scope, known-gap owners, and rollback/no-feature-flag notes in `docs/ai/research/codex-agent-route-candidates.md` and `docs/ai/research/codex-agent-route-candidate-manifest.json` (AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-1.6, AC-1.7)
- [ ] T026 [US1] Run `python3 specs/g56r-001-candidate-route-baseline/check-artifacts.py` twice and `git diff --check`, confirm identical checker summaries and exactly three research delivery paths plus two validation paths, and ensure any terminal failure remains an owned `no_go` rather than extending the workday or reducing scope (AC-1.5, AC-1.6)

**Checkpoint**: G56R-001 ends with a deterministic three-file research handoff
and zero production files or LOC.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1** starts immediately and blocks artifact conclusions.
- **Phase 2** depends on the Phase 1 checker contract and frozen evidence rules.
- **Phase 3** depends on reconciled Phase 2 evidence.
- **Phase 4** depends on the complete Phase 3 narrative records and identities.
- **Phase 5** depends on both Phase 4 artifacts and ends at the one-day boundary.

### User Story Dependency

- **US1 (P1)** is the sole story. Tasks T001–T026 execute in numeric order and
  together form its independently reviewable increment.

### Parallel Opportunities

- None. The three-delivery-file ceiling plus two constitution-required
  validation paths means evidence collection, contract derivation, projection,
  and validation either share an output or depend on a frozen prior result.
  Adding `[P]` would create same-file conflicts or nondeterministic
  reconciliation.

## Implementation Strategy

### MVP Scope

The MVP is the complete US1 sequence. There is no smaller acceptable delivery:
the checker, narrative, and manifest must all exist, and the terminal result may
be `no_go` when an objective condition remains unmet at the deadline.

### Review Order

1. Review `docs/ai/research/codex-agent-route-candidates.md` for evidence and
   classifications.
2. Review `docs/ai/research/codex-agent-route-candidate-manifest.json` for the
   exact agent-centric projection.
3. Review and run
   `specs/g56r-001-candidate-route-baseline/check-artifacts.py` for objective
   agreement and handoff reproduction.
4. Review `tests/speckit-pro/unit/test-g56r-001-artifacts.py` and the single
   Layer 4 declaration in `tests/speckit-pro/suite-manifest.json` for focused
   checker coverage.

## Notes

- Every task maps to `[US1]` and at least one of AC-1.1 through AC-1.7.
- All candidate availability, fixture execution, scoring, qualification, and
  route ordering remain downstream work.
- Source defects are recorded with owners and are never repaired in this
  sequence.
- The optional `after_tasks` git hook is reported but not executed because the
  parent autopilot owns the phase checkpoint commit.
