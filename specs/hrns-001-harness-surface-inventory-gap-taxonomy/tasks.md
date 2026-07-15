# Tasks: Harness Surface Inventory and Gap Taxonomy

**Input**: Design documents from `specs/hrns-001-harness-surface-inventory-gap-taxonomy/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `docs/ai/specs/.process/HRNS-001-design-concept.md`, `docs/prd-harness-engineering-uplift.md`, `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md`

**Tests**: No new test code is requested. Validation uses the existing documentation/process checks in `quickstart.md`.

**Reviewability**: Stay within the docs/process reviewability budget. HRNS-001 creates one canonical artifact at `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md` and must not add runtime code, validators, generated payload edits, installed-cache edits, vendored edits, or required external dependencies.

**Organization**: One independently testable P1 maintainer story.

## Phase 1: Setup

**Purpose**: Create the canonical artifact skeleton and freeze the source boundary before conclusions are written.

- [ ] T001 Record the merged-baseline cutoff, branch/worktree, as-of date, and source authority rule in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T002 Create the required taxonomy sections for current-state boundary, surface inventory, evidence classes, canonical gap register, external-candidate matrix, self-improvement loop register, AC-1.* crosswalk, coverage proof, and deferred ownership in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T003 Seed the AC-1.1 through AC-1.10 requirement list from `docs/prd-harness-engineering-uplift.md` and `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md` into `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`

---

## Phase 2: Foundational

**Purpose**: Establish row schemas and evidence boundaries that block all user-story content.

**Critical**: No gap classification or external recommendation should be written until this phase is complete.

- [ ] T004 [P] Enumerate authoritative and excluded evidence classes from `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.specify/memory/constitution.md`, `docs/prd-harness-engineering-uplift.md`, and `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md` in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T005 [P] Enumerate plugin distribution surfaces from `speckit-pro/.claude-plugin/plugin.json`, `speckit-pro/.codex-plugin/plugin.json`, `speckit-pro/skills/`, `speckit-pro/codex-skills/`, `speckit-pro/agents/`, and `speckit-pro/codex-agents/` in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T006 [P] Enumerate runner, helper, gate, hook, and generated-payload source surfaces from `speckit-pro/speckit_pro_runner/`, `speckit-pro/hooks/`, `speckit-pro/codex-hooks.json`, and `speckit-pro/scripts/curated-set.json` in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T007 [P] Enumerate tests, evals, PR packet, release gate, docs-site, workflow, and SpecKit extension surfaces from `tests/speckit-pro/`, `.github/pull_request_template.md`, `.github/workflows/`, `docs-site/`, `.specify/extensions.yml`, and `.specify/extensions/` in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T008 Define the canonical `HRNS-GAP-###` row schema, lifecycle values, taxonomy types, dependency posture values, owner fields, closure values, and stable-ID rules in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T009 Define the external-candidate matrix schema, recommendation vocabulary, primary-evidence requirements, and `unknown` handling rules in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T010 Define self-improvement loop closure semantics and fail-closed promotion rules in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`

**Checkpoint**: Schemas and source boundaries are ready; the maintainer story can be implemented.

---

## Phase 3: User Story 1 - Trace Harness Gaps to Ownership (Priority: P1) MVP

**Goal**: A maintainer can inspect one source-grounded taxonomy and trace every relevant harness surface, retained gap, owner workflow, downstream HRNS owner, dependency posture, safety closure, and external-candidate recommendation.

**Independent Test**: Review only `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md` and confirm every AC-1.1 through AC-1.10 requirement has a named section or row, every retained gap has one canonical `HRNS-GAP-###` row, CAR/G56R-owned work is reference-only when unmerged, and no external candidate is authorized as a required dependency.

### Implementation for User Story 1

- [ ] T011 [US1] Populate the current-state boundary and source precedence summary in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T012 [P] [US1] Populate skill, command, agent, and Codex/Claude distribution rows from `speckit-pro/skills/`, `speckit-pro/codex-skills/`, `speckit-pro/agents/`, and `speckit-pro/codex-agents/` in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T013 [P] [US1] Populate runner, helper, gate, hook, generated-payload, and install-inventory rows from `speckit-pro/speckit_pro_runner/`, `speckit-pro/hooks/`, `speckit-pro/codex-hooks.json`, and `speckit-pro/speckit_pro_runner/install_inventory.json` in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T014 [P] [US1] Populate docs, workflow, PR packet, test/eval, release gate, and extension rows from `docs/`, `docs-site/`, `.github/pull_request_template.md`, `.github/workflows/`, `tests/speckit-pro/`, `.specify/extensions.yml`, and `.specify/extensions/` in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T015 [US1] Identify retained gaps from the surface inventory and assign stable `HRNS-GAP-###` canonical rows in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T016 [US1] Classify each canonical gap row by surface tags, taxonomy type, lifecycle state, dependency posture, and authoritative evidence in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T017 [US1] Record owner workflow, cross-roadmap owner, CAR/G56R reference posture, downstream HRNS owner, and intentional deferments for every canonical gap row in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T018 [US1] Add knowledge initialization, incremental ingest and synthesis, query and compounding capture, structural conformance, health/drift, code-intelligence interoperability, external exchange, provenance, conflict handling, and cross-distribution parity rows in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T019 [US1] Add self-improvement loop rows with approval boundary, promotion rule, closure evidence, and unknown/non-promotable handling in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T020 [P] [US1] Research dated primary evidence for Pydantic and JSON Schema rows and record schema-candidate findings in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T021 [P] [US1] Research dated primary evidence for OpenTelemetry, OpenInference, LangSmith, Langfuse, and Phoenix rows and record trace/observability findings in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T022 [P] [US1] Research dated primary evidence for LangGraph, OpenAI Agents SDK, and the pinned OKF v0.1 knowledge-catalog reference and record orchestration/knowledge-format findings in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T023 [P] [US1] Research dated primary evidence for Braintrust, promptfoo, Inspect AI, and DSPy rows and record eval/coding-agent findings in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T024 [US1] Populate the complete external-candidate matrix with category, mapped HRNS surfaces, local-first fit, runtime dependency posture, telemetry/privacy posture, license/supply-chain risk, normative/reference status, observed version or commit, compatibility gaps, recommendation, as-of date, and `unknown` fields in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T025 [US1] Add the OKF-specific row with pinned normative revision, draft maturity, reference-tooling compatibility evidence, known spec/tool mismatches, extension-preservation posture, and blocking/advisory/deferred disposition in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T026 [US1] Add AC-1.1 through AC-1.10 crosswalk, surface coverage proof, evidence-class coverage proof, self-improvement loop coverage, and deferred-gap ownership proof in `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T027 [US1] Review `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md` and remove or reword any text that could authorize dependency adoption, runtime changes, generated-artifact changes, or CAR/G56R work absorption

**Checkpoint**: User Story 1 is complete when the taxonomy independently answers the maintainer tracing question and all fields required by FR-001 through FR-013 are represented.

---

## Phase 4: Polish & Validation

**Purpose**: Prove the artifact is reviewable, linked, current, and ready for PR packet generation.

- [ ] T028 Update `specs/hrns-001-harness-surface-inventory-gap-taxonomy/SPEC-MOC.md` and `docs/ai/specs/harness-engineering-uplift-roadmap-MOC.md` through the existing spec-index helper after taxonomy content is final
- [ ] T029 [P] Run the placeholder sweep from `specs/hrns-001-harness-surface-inventory-gap-taxonomy/quickstart.md` against `specs/hrns-001-harness-surface-inventory-gap-taxonomy/` and `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T030 [P] Run the Markdown link/evidence review from `specs/hrns-001-harness-surface-inventory-gap-taxonomy/quickstart.md` against `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- [ ] T031 Run the generated spec-index check from `specs/hrns-001-harness-surface-inventory-gap-taxonomy/quickstart.md` and apply the existing spec-index helper if it reports stale generated maps
- [ ] T032 Run `git diff --check` for `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`, `specs/hrns-001-harness-surface-inventory-gap-taxonomy/`, and `docs/ai/specs/.process/HRNS-001-workflow.md`
- [ ] T033 Run `python3 tests/speckit-pro/run-all.py --layer 1` if final changed paths warrant structural validation, or record the docs-only skip rationale in `docs/ai/specs/.process/HRNS-001-workflow.md`
- [ ] T034 Update Phase 7 and Post evidence in `docs/ai/specs/.process/HRNS-001-workflow.md` and `docs/ai/specs/.process/autopilot-state.json`
- [ ] T035 Prepare the PR review packet content with what changed, why, non-goals, review order, scope budget, AC-1.1 through AC-1.10 traceability, verification evidence, known gaps, and intentional deferrals in `docs/ai/specs/.process/HRNS-001-workflow.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user-story content.
- **User Story 1 (Phase 3)**: Depends on Foundational.
- **Polish & Validation (Phase 4)**: Depends on User Story 1 content.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational; no dependency on other user stories.

### Within User Story 1

- T011 must happen before canonical gap and matrix conclusions.
- T012, T013, and T014 can run in parallel because they inventory separate source surfaces before the final gap register is consolidated.
- T015 through T019 are sequential because canonical gap identity, ownership, and closure rows share one artifact.
- T020 through T023 can run in parallel because they research independent candidate families, but their results must merge through T024 and T025.
- T026 and T027 must run after all rows are complete.

### Parallel Opportunities

- T004 through T007 can run in parallel after T001 through T003.
- T012 through T014 can run in parallel after T011.
- T020 through T023 can run in parallel after T019.
- T029 and T030 can run in parallel after T028.

---

## Parallel Example: User Story 1

```text
Task: "Populate skill, command, agent, and distribution rows in docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md"
Task: "Populate runner, helper, gate, hook, generated-payload, and install-inventory rows in docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md"
Task: "Populate docs, workflow, PR packet, test/eval, release gate, and extension rows in docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md"
```

```text
Task: "Research Pydantic and JSON Schema candidate evidence in docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md"
Task: "Research OpenTelemetry, OpenInference, LangSmith, Langfuse, and Phoenix candidate evidence in docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md"
Task: "Research LangGraph, OpenAI Agents SDK, and OKF candidate evidence in docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md"
Task: "Research Braintrust, promptfoo, Inspect AI, and DSPy candidate evidence in docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md"
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete all User Story 1 implementation tasks.
3. Stop and validate the taxonomy using the independent test and quickstart checks.
4. Only then update workflow/state and prepare the PR packet.

### Incremental Delivery

1. Build the skeleton and evidence boundaries.
2. Add source-surface rows.
3. Consolidate canonical gaps and owners.
4. Add external-candidate evidence.
5. Add crosswalk and validation proof.

### Notes

- `[P]` tasks touch different evidence areas but still write to the same final artifact; merge them sequentially if one agent is doing the implementation.
- External candidates are evidence-only. HRNS-001 must not install, prototype, or adopt them.
- CAR and G56R rows are allowed as reference/ownership rows, but unmerged CAR/G56R state is not authoritative current evidence.
