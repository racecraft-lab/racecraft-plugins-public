# Tasks: CAR-001 Candidate Route Baseline and Role Contracts

**Input**: Design documents from `specs/car-001-candidate-route-baseline/`

**Prerequisites**: plan.md (required), spec.md (27 FRs, 8 SCs), research.md (D1-D9), data-model.md (manifest field set), contracts/agent-route-candidate-manifest.schema.json, quickstart.md (V1-V8)

**Tests**: This is a read-only documentation research spike — there is no product code to test. "Tests" here are the deterministic validation checks in quickstart.md (JSON validity, schema conformance, hash reproducibility, privacy scan, zero-shipped-byte guard, default suite). They appear in Phase 4, not as TDD red-green tasks.

**Reviewability**: Spike within budget — 0 production-code LOC, 2 deliverable files, 1 primary surface (`docs/ai/research/`), all below warn thresholds. Estimator advisory `{estimated_loc: 0, suggested_slices: 1, status: ok}` (spike flag). No split exception required. T009 records this before authoring begins.

**Organization**: One user story (research spike). Per the design intent, tasks are organized by **deliverable** and by the dependency chain **inventory → fact research → contracts/manifest → fixture backlog/telemetry → handoff**, not by code layer.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (reads/writes different files, no dependency on an incomplete task)
- **[US1]**: The single user story (Consume a dated, cited candidate-route baseline)
- Every task carries a repo-relative file path and an observable "Done when" check. No absolute filesystem paths appear in any deliverable (privacy scan, T028).

## Path Conventions (this spike)

- **Deliverables (committed)**: `docs/ai/research/claude-agent-route-candidates.md` (the record) and `docs/ai/research/claude-agent-route-candidate-manifest.json` (the manifest).
- **SDD process artifacts**: `specs/car-001-candidate-route-baseline/` (spec, plan, research, data-model, contracts, quickstart).
- **Read-only inventory sources (never modified)**: `speckit-pro/agents/*.md`, `speckit-pro/codex-agents/autopilot-fast-helper.toml`, `tests/speckit-pro/layer6-efficiency/fixtures/`, plus the skills/validators/dist/installed-cache surfaces swept for AC-1.1.
- **Comparator identity**: all agent bytes read for hashing come from the pinned tag `speckit-pro-v2.19.1` (commit `e343aa2e4ebcb2d48c501f285d7072cfd55722da`) via `git show <tag>:<path>`, never the working tree.

## Non-Goal Guardrails (bound every task)

Per the design concept's Non-goals, no task in this spec may: edit agent frontmatter, prompt, generated payload, or any shipped default; build full fixtures; order or select fallbacks; or claim any candidate is executable before probing. Those cross the CAR-002 / CAR-003 / CAR-006 / CAR-010 boundaries. Any authoring that drifts toward them must stop and be re-scoped; T030 is the explicit enforcement check.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the two deliverable files, the pinned comparator identity, and the stdlib hashing method before any inventory or authoring.

- [ ] T001 Create the dated research record `docs/ai/research/claude-agent-route-candidates.md` with a dated H1 and empty section skeleton (agent + route-policy surface inventory; primary-source fact table; capability questions; fixture backlog; telemetry requirements; Layer 6 labeling; go/no-go handoff), placed under the existing `docs/ai/research/` research-spike convention. [FR-001, FR-002 (dated)]
  - Done when: the file exists with a dated top-level heading and the named section headers present (empty bodies allowed).
- [ ] T002 Pin and record the immutable production comparator in a scratch note for later manifest use: tag `speckit-pro-v2.19.1`, commit `e343aa2e4ebcb2d48c501f285d7072cfd55722da`; verify the tag resolves and that `git diff speckit-pro-v2.19.0 speckit-pro-v2.19.1 -- speckit-pro/agents speckit-pro/codex-agents` is empty (2.19.0→2.19.1 reconciliation). [FR-009]
  - Done when: the tag/SHA resolve via `git rev-parse speckit-pro-v2.19.1` and the scoped `git diff` prints nothing (byte-identical agents/codex-agents).
- [ ] T003 Establish the Python 3.11+ standard-library hashing approach (transient helper, never committed under `speckit-pro/` or `tests/`): read tag bytes via `git show <tag>:<path>`, strip the leading `---`…`---` YAML frontmatter block, `hashlib.sha256` over the remaining body (instruction identity) and over the full file. [FR-025, FR-011 (method)]
  - Done when: a throwaway stdlib snippet computes both hashes for one agent (e.g. `phase-executor`) from the pinned tag with no new Bash and no third-party import.

---

## Phase 2: Foundational (Inventory & Baseline — Blocking Prerequisites)

**Purpose**: Produce the raw inventory the fact table, manifest, and handoff all consume. The four inventory sweeps read four distinct source surfaces and are mutually parallel-safe. Hash computation and the reviewability checkpoint gate the manifest.

**⚠️ CRITICAL**: No fact-table or manifest authoring (Phase 3) begins until this phase is complete.

- [ ] T004 [P] Inventory the eleven current Claude agents at the pinned tag — for each of `analyze-executor`, `checklist-executor`, `clarify-executor`, `codebase-analyst`, `consensus-synthesizer`, `domain-researcher`, `gate-validator`, `implement-executor`, `phase-executor`, `spec-context-analyst`, `uat-runbook-author`, record the frontmatter route tuple (`model`, `effort`) and note the role-prose source, reading `git show speckit-pro-v2.19.1:speckit-pro/agents/<name>.md`. (Each agent is an independent read — parallel-safe.) [FR-002, FR-010]
  - Done when: all eleven route tuples are captured in the record's inventory section with their `model`/`effort` values.
- [ ] T005 [P] Inventory the Codex helper source `speckit-pro/codex-agents/autopilot-fast-helper.toml` at the pinned tag — enumerate every field present (`model`, `sandbox_mode`, and the `developer_instructions` contract content: role prose, the four bounded jobs, hard rules, output formats) so the later mapping table can be source-complete. [FR-002, FR-017 (source-completeness)]
  - Done when: every field in the toml is listed in the inventory section as a candidate mapping row.
- [ ] T006 [P] Run the AC-1.1 route-policy surface sweep — enumerate every active source, skill, validation, evaluation, generated-payload, and installed-cache surface under `speckit-pro/**`, `dist/**`, and the installed-cache mirrors that encodes or consumes agent route policy. Read-only. [FR-003, AC-1.1]
  - Done when: the record's surface-inventory subsection lists each route-policy-bearing surface with its repo-relative path.
- [ ] T007 [P] Inventory the Layer 6 Claude fixture gap — record the two current fixtures (`consensus-synthesizer`, `gate-validator` under `tests/speckit-pro/layer6-efficiency/fixtures/`) and the ten agents with no current Claude fixture. [supports FR-019, FR-020]
  - Done when: the record shows the 2-current / 10-missing split across the twelve agents.
- [ ] T008 Compute agent-file hashes from the pinned-tag bytes for all twelve entries (Python stdlib only): for the eleven Claude agents, `instruction_sha256` (frontmatter-stripped body) + `full_file_sha256`, `hash_source: claude-agent-md`; for `autopilot-fast-helper`, `instruction_sha256` over the contract-equivalent translated body + `full_file_sha256` of the source toml, `hash_source: codex-toml-translation`. All inputs from `git show speckit-pro-v2.19.1:<path>`, not the working tree. [FR-010, FR-011, FR-025, SC-007]
  - Done when: twelve `{instruction_sha256, full_file_sha256, hash_source}` triples exist (64-hex each) and re-running the snippet reproduces them from the tag.
- [ ] T009 Record the reviewability-budget checkpoint and split decision before authoring: 0 production LOC, 2 deliverable files, 1 primary surface — within budget; remains one spec (`suggested_slices: 1`, spike flag). [Reviewability Budget; FR-024 scope]
  - Done when: `specs/car-001-candidate-route-baseline/tasks.md` (this file) and the record note the budget result "within budget / one spec, no exception required".

**Checkpoint**: Inventory complete, hashes reproducible, comparator pinned — deliverable authoring can begin.

---

## Phase 3: User Story 1 - Consume a dated, cited candidate-route baseline (Priority: P1) 🎯 MVP

**Goal**: One research record + one machine-readable manifest that let a CAR-002 implementer freeze the executable candidate set — role contracts, immutable routes (or recorded absence), candidate tuples with alias+resolved-ID, statement-class labels, fixture backlog, telemetry requirements, and a self-contained go/no-go handoff — with zero shipped-default change.

**Independent Test**: Open the record and the JSON manifest and confirm each of the twelve agents has a complete entry; every recorded platform fact carries a source URL, an access date, and a short verbatim quote and is class-labeled; and the go/no-go handoff lists capability questions with stable IDs — all with no dependency on CAR-002 results and no shipped-default change.

### Group A — Primary-source fact table (fact research; gates candidate tuples in Group B and the handoff in Group D)

These author the same fact-table section of `docs/ai/research/claude-agent-route-candidates.md` and are sequential (shared file; each row gates downstream tuple bindings). Not [P].

- [ ] T010 [US1] Author the fact rows for model IDs and the four aliases (`opus`, `sonnet`, `haiku`, `fable`) in `docs/ai/research/claude-agent-route-candidates.md` — each with source URL + access date + short verbatim quote from current official Anthropic documentation; record each alias's expected resolved model ID as a fact, or, where the docs do not bind the alias at research time, record a `CAP-Qn` binding question instead of a fact. Keep `fable` in scope (no product-announcement exclusion). [FR-004, FR-012, FR-013, Edge Cases]
  - Done when: four alias rows exist, each either citing a resolved ID (URL+date+quote) or naming a `CAP-Qn`; no legacy dated snapshot is enumerated as a separate candidate.
- [ ] T011 [US1] Author the fact rows for subagent configuration fields, effort levels, and model-resolution precedence in the record — each URL + access date + verbatim quote, each visibly class-labeled. [FR-004, FR-006]
  - Done when: each of these three fact classes has at least one cited, class-labeled row.
- [ ] T012 [US1] Author the fact rows for plugin-agent field support, fast mode, authentication modes, and non-interactive (`claude -p --output-format json`) telemetry in the record — each URL + access date + verbatim quote. (These non-interactive-telemetry facts feed T022.) [FR-004]
  - Done when: each of these four fact classes has at least one cited row, and the telemetry rows are marked as the source for the T022 requirements.
- [ ] T013 [US1] Apply the four-class statement labeling (platform fact / reasonable inference / proposed SpecKit Pro policy / unverified assumption) across the whole record, and enforce conflict + no-overclaim handling: reject any conflicting documentation claim or record it as an unresolved `CAP-Qn` with both claims quoted and neither side labeled a platform fact; assert no undocumented head-to-head benchmark or native fallback feature is claimed. [FR-005, FR-006, FR-007, SC-002, SC-003]
  - Done when: every statement in the record carries exactly one class label, and any conflict appears as a `CAP-Qn` (not a silent/unclassified state).
- [ ] T014 [US1] Record the two undocumented-behavior probe questions as `CAP-Qn` in the record (never as assumptions): (a) behavior when agent frontmatter names an unavailable model (hard error vs silent substitution); (b) execution-time manifestation of alias re-pointing (silent use vs hard error), distinct from and additional to alias re-pointing's role as an invalidation trigger (FR-014). [FR-008]
  - Done when: both behaviors exist as distinct `CAP-Qn` entries, and neither is stated as a fact or assumption anywhere.

### Group B — Manifest assembly & role contracts (gates the handoff; single JSON file — sequential, not [P])

All tasks write `docs/ai/research/claude-agent-route-candidate-manifest.json`; because they mutate one file they run in sequence.

- [ ] T015 [US1] Author the manifest top-level object in `docs/ai/research/claude-agent-route-candidate-manifest.json`: `schema_version: "1.0.0"`, `manifest_kind: "agent_route_candidate_manifest"`, `generated_at` (research date), `provisional: true`, `immutable_production_comparator` (tag + SHA + pin_rationale + reconciliation_note from T002), `alias_universe: ["opus","sonnet","haiku","fable"]`, and empty `capability_questions` / `agents` to be filled. [FR-001, FR-009, FR-015 (top-level)]
  - Done when: the file is valid JSON and the top-level required keys are present with the pinned comparator identity.
- [ ] T016 [US1] Author the eleven current agents' `agent_route_entry` objects (from T004/T008): `role_contract` (summary, mutation_boundary, output_format, repo-relative source_ref), `immutable_production_route` (route tuple), `production_route_recorded_absence: false`, `agent_file_hashes`, `required_capabilities` (model/modality/subagent_fields/tools/skills/client), `agent_contract_id`, `candidate_rationale`, `known_incompatibilities`, `required_qualification_artifacts`, `fixture_backlog_ref`. [FR-014, AC-1.6, SC-001]
  - Done when: eleven entries exist with every required field non-empty and `immutable_production_route` matching the recorded tuple.
- [ ] T017 [US1] Author `candidate_routes` for every agent entry: each tuple = `alias` + `expected_resolved_model_id` (or `null` → set `environment_time_availability.binding_question_ref`) + `effort`; `project_level_eligibility` (`eligible`, `basis`, `evidence_class`) recorded now and kept separate from `environment_time_availability` (`status: probe_required`, `probe_question_ref`); `fable` present in executor-class sets; exclusions only for recorded incompatibility/contract-failure/dominance. Also record in the record the explicit deferral of AC-1.3 prompt/context candidates to CAR-003 (model/effort tuples only here). [FR-012, FR-013, FR-015, FR-016, FR-027, AC-1.3]
  - Done when: every entry has ≥1 tuple with the eligibility/availability split; every `null` resolved-ID tuple carries a `binding_question_ref`; and the record contains the AC-1.3 prompt/context deferral note.
- [ ] T018 [US1] Author candidate-specific, actionable `invalidation_triggers` per entry (no boilerplate): for every distinct alias in that entry's `candidate_routes`, a trigger for that alias re-pointing to a new resolved model ID, plus the agent's comparator-drift trigger (frontmatter route drifts from the recorded comparator hash). [FR-014, data-model §7 rule 10]
  - Done when: each entry's triggers name every one of its aliases plus the drift condition; no entry relies on a single generic trigger.
- [ ] T019 [US1] Author the twelfth entry `autopilot-fast-helper` (from T005): contract-equivalent translation of the toml (role prose, four bounded jobs, hard rules, output formats); `immutable_production_route: null`; `production_route_recorded_absence: true`; a **source-complete** `platform_field_mapping` array — every toml field (`model`, `sandbox_mode`, `developer_instructions` content) as a `{codex_field, claude_equivalent, evidence_class, note}` row, either mapped or explicitly no-equivalent; Claude-only fields (e.g. `maxTurns`) carry proposed values with `evidence_class: proposed_policy` labeled "proposed SpecKit Pro policy" deferred to CAR-010. [FR-017, FR-018, SC-001]
  - Done when: the entry validates with `platform_field_mapping` present, no source toml field omitted, and every no-equivalent/Claude-only field labeled proposed_policy.
- [ ] T020 [US1] Author the manifest `capability_questions` array (machine stubs: `id` `^CAP-Q\d+$`, `question`, `blocks`) so every `probe_question_ref` / `binding_question_ref` used in T017 resolves to an existing entry. [FR-021 (machine side)]
  - Done when: every `CAP-Qn` referenced by any tuple exists in `capability_questions`, and vice-versa (no dangling refs).

### Group C — Fixture backlog, telemetry requirements & Layer 6 labeling (record; gates the handoff)

- [ ] T021 [US1] Author the requirements-level fixture backlog in the record — one entry per twelve agents: the role contract to exercise, representative task types, required evidence (tool surface, mutation boundary, output format), and a pass/fail signal sketch. NO full fixture specifications. Each entry's anchor matches the manifest `fixture_backlog_ref`. [FR-019, SC-004]
  - Done when: twelve backlog entries exist, each requirements-level only, each resolvable from its manifest `fixture_backlog_ref`.
- [ ] T022 [US1] Author the telemetry-requirements section in the record — the non-interactive (`claude -p --output-format json`) telemetry fields each role's qualification must later satisfy, derived from the T012 non-interactive-telemetry facts and labeled by necessity (mandatory / derived-from-configuration / platform-unavailable, e.g. effective reasoning effort as a never-returned/derived field). State requirements only; do not build CAR-002's telemetry capability profile. [FR-026]
  - Done when: the section lists per-role telemetry fields each carrying a necessity label, and explicitly states CAR-001 builds no CAR-002 profile.
- [ ] T023 [US1] Label the current Layer 6 Claude evaluation path in the record as **bare prompt emulation** (a frontmatter-stripped agent body piped to `claude -p --model`) and mark all historical Layer 6 results `non_release_evidence`; state the label is lifted only by a CAR-003 replay through the shared materializer with exact treatment (required tool surface, mutation contract, dispatch context, telemetry proof), with CAR-001 itself claiming no such replay and recording that bare prompt emulation is smoke-only evidence that cannot support release. [FR-020, AC-1.7]
  - Done when: the record carries the "bare prompt emulation" description, the `non_release_evidence` label on historical results, and the CAR-003 lift condition.

### Group D — Capability questions & go/no-go handoff (record's final section; depends on Groups A-C)

- [ ] T024 [US1] Author the record's dedicated capability-question section — full prose for `CAP-Q1…CAP-Qn`, consolidating every probe question raised in T010/T013/T014, with stable IDs matching the manifest `capability_questions` stubs (T020). [FR-021]
  - Done when: every `CAP-Qn` in the manifest has matching full prose in the record's capability-question section, and IDs are contiguous and stable.
- [ ] T025 [US1] Author the go/no-go handoff as the **final section** of the record: enumerate the provisional candidate-route manifest, the role-contract catalog, the fixture backlog, the telemetry requirements (FR-026), the unresolved capability questions, and the go/no-go decision; record any mandatory fact left unverified within the single-run timebox as a no-go item or `CAP-Qn`; assert the handoff depends on no CAR-002 result and claims no candidate executable before probing. [FR-021, FR-022, FR-023, SC-004, SC-005]
  - Done when: the handoff is the record's last section, enumerates all six required elements, and contains an explicit "no dependency on CAR-002 results / no executable claim" statement.

**Checkpoint**: Both deliverables authored; US1 is independently reviewable — proceed to verification.

---

## Phase 4: Polish, Verification & Non-Goal Guardrails

**Purpose**: Prove the success criteria and the non-goal boundaries. These validation checks map to quickstart.md V1-V8.

- [ ] T026 [P] Validate the manifest is well-formed JSON and conforms to `specs/car-001-candidate-route-baseline/contracts/agent-route-candidate-manifest.schema.json` with zero violations (twelve-agent coverage, alias closure, absence integrity, eligibility/availability split, unbound-alias conditional, helper `platform_field_mapping`). Runs quickstart V2/V3/V4. [SC-008, SC-001]
  - Done when: `python3 -m json.tool` succeeds and schema validation reports zero violations against `docs/ai/research/claude-agent-route-candidate-manifest.json`.
- [ ] T027 [P] Verify instruction-identity stability by recomputation (quickstart V5): recompute the frontmatter-stripped-body sha256 for a current agent from the pinned tag and confirm it equals the manifest `instruction_sha256`; then confirm a pure frontmatter route change (model/effort only) leaves it unchanged. Python stdlib only. [SC-007, FR-011]
  - Done when: recomputed hash matches the manifest and the simulated route-only edit yields the identical instruction hash.
- [ ] T028 [P] Run the privacy scan (quickstart V6) for absolute filesystem paths (user/home directory roots) across both deliverables `docs/ai/research/claude-agent-route-candidates.md` and `docs/ai/research/claude-agent-route-candidate-manifest.json`. [privacy constraint]
  - Done when: the scan reports zero absolute-path hits in either deliverable.
- [ ] T029 Verify zero shipped-byte change and green suite (quickstart V1/V7): `git status --porcelain speckit-pro dist tests` is empty AND `python3 tests/speckit-pro/run-all.py` passes with zero failures. [SC-006, FR-024]
  - Done when: the git status is empty for those paths and the default suite exits clean.
- [ ] T030 Non-goal guardrail audit: confirm the run changed no agent frontmatter/prompt/generated payload/shipped default, ordered/selected no fallbacks, built no full fixtures, and claimed no candidate executable before probing — flag any authored content that would cross the CAR-002/CAR-003/CAR-006/CAR-010 boundary. [FR-024, Non-goals]
  - Done when: the audit finds nothing under `speckit-pro/`'s allowlisted payload dirs changed and no boundary-crossing content in the deliverables.
- [ ] T031 Manual review pass (quickstart V8) plus cross-reference integrity: every fact row carries URL + access date + verbatim quote (SC-002); every statement is class-labeled (SC-003); the go/no-go handoff is self-contained with no CAR-002 dependency (SC-004); and every `agent_contract_id`, `fixture_backlog_ref`, and `CAP-Qn` referenced in the manifest resolves to a section in the record (data-model §7 rule 9). [SC-002, SC-003, SC-004]
  - Done when: the reviewer confirms all four citation/labeling/self-containment checks pass and no manifest cross-reference dangles.
- [ ] T032 Generate or update the PR review packet for the spike: what changed, why, non-goals, review order, scope budget, traceability (each FR/SC → deliverable section + verification evidence), verification evidence, known gaps, and rollback/feature-flag notes; name follow-up specs (CAR-002/003/006/010) for deferred work. [PR Review Packet Requirements]
  - Done when: the PR packet contains all nine required elements and the traceability table maps every major requirement to a changed file and a verification check.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup. The four inventory sweeps (T004-T007) are mutually parallel; T008 (hashes) depends on T004's file set; T009 (reviewability checkpoint) precedes authoring. **Blocks all of Phase 3.**
- **User Story 1 (Phase 3)**: Depends on Foundational. Internal order is the deliverable dependency chain:
  - Group A (fact table) → gates Group B tuple bindings (resolved IDs / `CAP-Qn`) and Group D.
  - Group B (manifest) depends on T004/T005/T008 (routes, helper fields, hashes) and Group A (`CAP-Qn` refs); tasks within B are sequential (one JSON file).
  - Group C (fixture backlog / telemetry / Layer 6) depends on T007 (fixture gap) and T012 (telemetry facts).
  - Group D (capability questions + handoff) depends on Groups A, B, and C.
- **Polish (Phase 4)**: Depends on all of Phase 3. T026/T027/T028 are parallel; T029/T030/T031/T032 follow.

### Within Group B (manifest)

- T015 (top-level) → T016 (eleven entries) → T017 (candidate tuples) → T018 (invalidation triggers) → T019 (twelfth entry) → T020 (capability-question stubs). Sequential because all write one JSON file.

### Parallel Opportunities

- **Foundational inventory**: T004, T005, T006, T007 run in parallel — four distinct read-only source surfaces (agents / codex toml / route-policy surfaces / Layer 6 fixtures). Within T004, each of the eleven agent reads is itself independent and may be fanned out.
- **Polish verification**: T026, T027, T028 run in parallel — schema validation, hash recomputation, and privacy scan touch independent checks.
- **Not parallel by design**: the fact-table tasks (T010-T014) and every manifest task (T015-T020) are sequential — they share one file and gate later tuple bindings and the handoff.

---

## Parallel Example: Foundational Inventory

```text
# Launch the four inventory sweeps together (distinct read-only surfaces):
Task T004: Inventory the eleven Claude agents' route tuples from git show speckit-pro-v2.19.1:speckit-pro/agents/<name>.md
Task T005: Inventory every field in speckit-pro/codex-agents/autopilot-fast-helper.toml
Task T006: Sweep the AC-1.1 route-policy surfaces under speckit-pro/**, dist/**, installed-cache mirrors
Task T007: Inventory the Layer 6 fixture gap in tests/speckit-pro/layer6-efficiency/fixtures/ (2 current / 10 missing)
```

---

## Implementation Strategy

### MVP (this spike = User Story 1)

There is exactly one user story; it is the whole MVP. Complete Phase 1 → Phase 2 → Phase 3 (Groups A→B→C→D) → Phase 4. The deliverable is a single coherent baseline-and-handoff; do not split.

1. Setup: create the dated record, pin the comparator, prove the stdlib hashing method.
2. Foundational: run the four inventory sweeps, compute the twelve hash triples from the pinned tag, record the reviewability checkpoint.
3. User Story 1: author the fact table, then the manifest (top-level → eleven entries → tuples → triggers → twelfth entry → capability stubs), then the fixture backlog / telemetry / Layer 6 labeling, then the capability-question section and the go/no-go handoff.
4. **STOP and VALIDATE**: run Phase 4 (schema conformance, hash reproducibility, privacy scan, zero-shipped-byte guard, default suite, non-goal audit, manual review, PR packet).

### Notes

- [P] tasks = different files / independent checks, no dependency on an incomplete task.
- Every recorded platform fact needs URL + access date + short verbatim quote; anything the docs do not bind becomes a `CAP-Qn`, never an assumption.
- All hashes are computed over the agent bytes at the pinned tag `speckit-pro-v2.19.1` (commit `e343aa2e4ebcb2d48c501f285d7072cfd55722da`), reproducible via `git show <tag>:<path>` — not the working tree.
- Zero shipped bytes change: nothing lands under `speckit-pro/`'s allowlisted payload directories, `dist/`, or `tests/`. Deliverables live only under `docs/ai/research/`; spec artifacts under `specs/car-001-candidate-route-baseline/`.
- Avoid: full fixture specs (CAR-003), fallback ordering (CAR-003), plugin-owned route-policy manifest (CAR-006), finalizing helper `maxTurns` (CAR-010), and any "executable" claim before probing (CAR-002).
