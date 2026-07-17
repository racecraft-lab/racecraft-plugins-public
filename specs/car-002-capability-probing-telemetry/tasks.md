---
description: "Task list for CAR-002 Capability Probing, Telemetry Profile, and Exact-Treatment Contract"
---

# Tasks: CAR-002 Capability Probing, Telemetry Profile, and Exact-Treatment Contract

**Input**: Design documents from `specs/car-002-capability-probing-telemetry/`

**Prerequisites**: plan.md (FR→WP table + Declared File Operations), spec.md (US1–US4), research.md (R1–R15), data-model.md (four record `$defs`), contracts/claude-trace-contract.schema.json, quickstart.md (operator runbook Part A + CAR-003 handoff Part C).

**Tests**: TDD is explicitly requested for the WP1 schema foundation ("failing schema tests first"). Test tasks are therefore first-class here. The one exception is the operator live-probe run (T015), which is human-gated and never test-driven and never CI (FR-001).

## Work-Package ↔ User-Story map

Tasks are organized by the three Clarify-ratified vertical work packages (spec.md "Split decision"; plan.md FR→WP table). Every task carries a single explicit `[WP1]`/`[WP2]`/`[WP3]` tag (CHK034) and cites the FR(s)/SC(s) and file(s) it implements (CHK035). No task spans two work packages.

| WP | User stories | FRs (plan.md FR→WP table) | Independent verification |
|----|--------------|---------------------------|--------------------------|
| **WP1** | US1 (P1) | FR-001, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-023, FR-026, FR-027, FR-028 (20) | Operator produces a committed snapshot that validates against the `runtimeCapabilitySnapshot` `$def`; fail-closed writer aborts on an invalid observation. |
| **WP2** | US2 + US3 (P2) | FR-018, FR-019, FR-020, FR-021, FR-022 (5) | Committed telemetry profile + `route-resolution.json` fixture validate against their `$defs` (exactly-one-label, nulls preserved, all FR-021 bindings present). |
| **WP3** | US4 (P3) | FR-002, FR-024, FR-025 (3) | `python3 tests/speckit-pro/run-all.py` validates all four record-class fixtures + snapshot + profile + the 37-route join, offline, zero live model calls. |

**Dependency order: WP1 → WP2 → WP3.** The schema `$defs` (WP1) gate everything downstream; WP2 consumes the published schema (authors no new `$defs`); WP3 extends the Layer 4 coverage WP1 registered and joins against the snapshot WP1 committed.

## Scope guard — Non-goals (design-concept Non-goals; Q1)

No task in this list executes a corpus, scores an outcome, computes statistics, orders a fallback chain, or edits any shipped agent frontmatter — those cross CAR-003/005/006 boundaries and are out of scope. The **only** live `claude` invocation in the entire feature is the human-gated operator task **T015**; no CI or test path makes a live model call (FR-001/FR-002). The throwaway subagent-frontmatter probe agent file (T014) is generated at probe time and **never committed**, so no shipped agent is created or edited (constitution I). Deliverables land only under `docs/ai/research/`, `tests/speckit-pro/layer6-efficiency/lib/`, `tests/speckit-pro/unit/`, and this spec directory — nothing under `speckit-pro/` payload dirs, `dist/`, or installed-cache mirrors.

## Format: `[ID] [P?] [WP] Description [FR/SC markers] — file path`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task).
- **[WP]**: the single work package the task routes to for split-PR emission (CHK034).
- Every task cites its FR/SC markers and its exact file path (CHK035).

---

## Phase 1: Setup & Reviewability Gate

- [x] T001 [WP1] Record the WP1 reviewability disposition **before** implementation: WP1's hand-estimated ~550–820 authored reviewable LOC breaches the 400 warn ceiling, carried to **G5** per plan.md "WP1 sizing — mechanical estimator vs. real reviewable LOC (G5 escalation)". Disposition = single WP1 PR with a documented, ratified over-ceiling exception (recommended) OR PRSG file-level review units within WP1; do **NOT** re-slice the Clarify-ratified 3-WP boundary. **Done-check**: the chosen disposition is written into WP1's PR-packet scope-budget section (T018) and the WP1→WP2→WP3 seam is unchanged. [Reviewability Budget / plan.md G5]

**Checkpoint**: Reviewability disposition recorded — WP1 implementation may begin.

---

## Phase 2: WP1 Foundation — Schema Contract + Validator + Suite Registration (US1, TDD)

**Goal**: Publish the one platform-neutral JSON Schema (four `$defs`) + the stdlib validator + the Layer 4 suite registration that gate everything downstream.

**Independent Test**: `python3 tests/speckit-pro/run-all.py --layer 4` discovers the new test and it validates valid records and rejects malformed ones against all four `$defs`, with zero live model calls.

> **TDD: write the failing schema tests FIRST (T002), confirm they FAIL, then build the schema (T003–T004) and validator (T005) to make them PASS (T006).**

- [x] T002 [WP1] Write the FAILING Layer 4 unit test module `tests/speckit-pro/unit/test-efficiency-claude-telemetry.py` with schema-load + four-`$def`-presence assertions and malformed-record rejection cases (behavior-named methods, unit-layout compliant per research R14); run `python3 tests/speckit-pro/run-all.py --layer 4` and **confirm it FAILS** (schema + validator absent). [FR-028][FR-016][SC-002] — tests/speckit-pro/unit/test-efficiency-claude-telemetry.py
- [x] T003 [WP1] Author the shipped JSON Schema contract at `docs/ai/research/claude-trace-contract.schema.json` (promoting/completing the Phase-1 draft in `contracts/claude-trace-contract.schema.json`): shared primitives (`sha256` `^[0-9a-f]{64}$`, `nullableString` `["string","null"]`, CAR-002 `rawEvidence` = full sanitized `raw_output` string + `raw_output_sha256` + `sanitization` const `"home_paths_normalized_utf8"`) and all four record `$defs` — `runtimeCapabilitySnapshot`, `telemetryProfile`, `routeResolution`, `exactTreatmentReplay`; draft 2020-12, top-level `$id`, `additionalProperties:false` throughout, camelCase `$def` names, snake_case instance fields, instance-level `schema_version` const `"1.0.0"`. [FR-015][FR-017][SC-007] — docs/ai/research/claude-trace-contract.schema.json
- [x] T004 [WP1] In the same schema file, complete the `routeResolution` `$def` FR-021 bindings including the roadmap-added **`dispatch_namespace`** (string) and **`parent_session_configuration`** (`nullableString`, null preserved), plus nullable `fallback_index`/`fallback_reason` (AC-2.3, always null under CAR-002 unset-proof), and pattern-constrain the cross-reference IDs **identically wherever they appear across `$defs`**: `candidate_route_id` → `CAR-001-CR-<NN>-<NN>`, `agent_contract_id` → `car.<name>.v<n>`, `runtime_capability_snapshot_id` → `CAR-002-RCS-<YYYY-MM-DD>-V<n>` (never free-text min-length). [FR-021][FR-015] — docs/ai/research/claude-trace-contract.schema.json
- [x] T005 [WP1] Implement the standard-library-only validator `tests/speckit-pro/layer6-efficiency/lib/claude_trace_schema.py` (no third-party `jsonschema`), mirroring the CAR-001 `validate_manifest` pattern (`require_exact_keys`/`schema_keys`/`require_sha256`/`require_utc_timestamp`): load the schema file once as the single source of truth, drive required-key + `additionalProperties:false` + enum/const/`sha256`/UTC checks, one validator entrypoint per `$def`. [FR-016][FR-028][SC-007] — tests/speckit-pro/layer6-efficiency/lib/claude_trace_schema.py
- [x] T006 [WP1] Extend `test-efficiency-claude-telemetry.py` to exercise `claude_trace_schema.py` against inline valid + invalid samples for each `$def` (schema conformance + fail-closed rejection of a malformed record); run `--layer 4` and **confirm the previously-failing tests now PASS**. [FR-016][FR-023][SC-004] — tests/speckit-pro/unit/test-efficiency-claude-telemetry.py
- [x] T007 [WP1] Register the new Layer 4 test in `tests/speckit-pro/suite-manifest.json` (unit-layer entry with a path under `tests/speckit-pro/unit/`); run `python3 tests/speckit-pro/run-all.py --layer 4` and confirm the test is discovered and green. [FR-028] — tests/speckit-pro/suite-manifest.json
- [x] T008 [WP1] Check/regenerate the committed docs-site test reference page for the newly registered `tests/speckit-pro/` entry (per `tests/speckit-pro/AGENTS.md`); **done-check**: the generated reference has no uncommitted diff. [FR-028 / repo docs contract] — docs-site/src/content/docs/reference/tests.md (generated — regenerate via the docs-site build; never hand-edit, per tests/speckit-pro/AGENTS.md)

**Checkpoint**: Schema + validator + registration are green — the contract that gates WP2/WP3 exists.

---

## Phase 3: WP1 — Probe Tool + Fail-Closed Writer + Operator Run + Snapshot (US1)

**Goal**: Ship the operator-only probe tool with the fail-closed writer, then have an operator run it to produce and commit the canonical runtime-capability snapshot. Operator runbook = quickstart.md Part A.

**Independent Test**: Running the probe tool with a working `claude` CLI writes a schema-valid snapshot at the canonical path; an invalid observation aborts the write (fail-closed) with no file created.

- [x] T009 [WP1] Implement the **pure (non-live)** probe logic in `tests/speckit-pro/layer6-efficiency/lib/claude_capabilities.py`: bounded probe-matrix builder that dedupes the 37 CAR-001 routes to the 6 unique `(model, effort)` tuples (`opus__max`, `sonnet__max`, `fable__max`, `haiku__max`, `haiku__low`, `sonnet__low`), `tuple_id` derivation `<model>__<effort>` (null effort → `none`, research R1), the fixed canary text `Reply with the single word: ok` + its SHA-256 over exact bytes, `<home>` sanitization, per-payload SHA-256 over sanitized UTF-8 bytes, and the fail-closed disposition gating — all separated from the single live boundary. [FR-003][FR-004][FR-005][FR-012][FR-013][FR-023] — tests/speckit-pro/layer6-efficiency/lib/claude_capabilities.py
- [x] T010 [WP1] Enforce the FR-003 budget/timeout/no-retries controls in `claude_capabilities.py`: bound at ~20 live invocations equal to the precomputed matrix cardinality with an **overrun surfaced BEFORE any live call**; an **explicit per-invocation timeout** whose value is recorded in snapshot probe metadata; and **NO automatic retries** — a timed-out or transport-failed invocation follows the "Partial probe matrix" abort disposition. [FR-003] — tests/speckit-pro/layer6-efficiency/lib/claude_capabilities.py
- [ ] T011 [WP1] Implement the **single live `claude` boundary** in `claude_capabilities.py` via `subprocess` (argument array, `shell=False`, explicit timeout, `text=True` UTF-8 capture, explicit return-code handling) as the ONLY path permitted to make a live call; structure it so no importable test entrypoint can reach it. [FR-001][FR-002] — tests/speckit-pro/layer6-efficiency/lib/claude_capabilities.py
- [ ] T012 [WP1] Implement the capability-answer + evidence-capture logic in `claude_capabilities.py`: alias→dated-ID bindings for opus/sonnet/haiku/fable from the canary `modelUsage` (CAP-Q1..Q4); per-tuple effort-acceptance in plain-text `--print` (or a recorded no-org-cap assumption) labeled observation, never certification (research R6); dual-surface unavailable-model observations (`print_model` + `subagent_frontmatter`) each with the FR-010 `unset_proof` drawn from the actual operator environment (`--fallback-model`/`fallbackModel`, `CLAUDE_CODE_SUBAGENT_MODEL`, `availableModels` absent) and a requested-vs-observed `modelUsage` cross-check (`remap_flagged`, research R4); CAP-Q6 recorded as a route-change detection-rule **open** entry (research R11); authentication-mode detection with the `GET /v1/models` corroboration called **only** in api_key mode (else a recorded gap, research R7); and explicit open/gap entries for any bounded-matrix-unanswerable question. [FR-006][FR-007][FR-008][FR-009][FR-010][FR-014][FR-026][FR-027] — tests/speckit-pro/layer6-efficiency/lib/claude_capabilities.py
- [x] T013 [WP1] Add unit coverage in `test-efficiency-claude-telemetry.py` for the probe tool's PURE logic — matrix cardinality = 6 tuples, `tuple_id` derivation, sanitization to `<home>`, hash computation, and the three fail-closed dispositions — exercised with zero live calls; confirm green offline. [FR-002][FR-023][FR-004] — tests/speckit-pro/unit/test-efficiency-claude-telemetry.py
- [ ] T014 [WP1] Implement the FR-009 subagent-frontmatter dispatch mechanism in `claude_capabilities.py` (research R12): generate an **uncommitted** throwaway `.claude/agents/<probe-name>.md` whose YAML frontmatter names the unavailable dated model ID, dispatch via an explicit `@agent-<probe-name>` mention in a fresh non-`--bare` `claude -p` with **no preempting per-invocation `--model`**, and **remove the file on every exit path** (success, abort, timeout) so an aborted run leaves no probe residue. Record the dispatch-equivalence caveat as labeled inference. [FR-009] — tests/speckit-pro/layer6-efficiency/lib/claude_capabilities.py
- [ ] **T015 [WP1] OPERATOR-ONLY, HUMAN-GATED — never CI, never TDD (FR-001).** An operator with the pinned `claude` CLI and valid auth runs the probe tool (quickstart.md Part A). **Probe step 1** = the one-shot raw `--output-format json` stdout **key-spelling confirmation** (confirm camelCase `modelUsage` and sub-fields `inputTokens`/`outputTokens`/`cacheReadInputTokens`/`cacheCreationInputTokens`/`contextWindow`/`costUSD`, plus snake_case `usage.*`/`total_cost_usd`/`num_turns`/`duration_ms`) before the parser is trusted (spec Assumptions "Telemetry field grounding"; research R3) — any unconfirmed field stays labeled `observation`. Then run the bounded matrix (steps 2–3) and the fail-closed write (step 4), producing and committing `docs/ai/research/claude-runtime-capability-snapshot.json`. **Done-check**: the committed snapshot exists, validates against the `runtimeCapabilitySnapshot` `$def`, and records alias→dated-ID bindings, one shared evidence set per tuple, both unavailable surfaces, and a `capability_answers` entry for each of CAP-Q1..Q6 (answered or explicitly open). [FR-001][FR-011][FR-003][SC-001][SC-004] — docs/ai/research/claude-runtime-capability-snapshot.json
- [ ] T016 [WP1] Add the two WP1 `docs/ai/research/**` deliverables (`claude-trace-contract.schema.json` + `claude-runtime-capability-snapshot.json`) to the `allowed_agent_route_research_exact` **exact-path** set in `tests/speckit-pro/unit/test-speckit-pro-runner.py` (narrow docs-surface guard, research R15); confirm the guard passes. [FR-011 / docs-surface guard] — tests/speckit-pro/unit/test-speckit-pro-runner.py
- [ ] T017 [WP1] Extend `test-efficiency-claude-telemetry.py` to validate the **committed snapshot** against the `runtimeCapabilitySnapshot` `$def` plus the FR-011 identity checks (the date embedded in `runtime_capability_snapshot_id` equals the UTC date of `captured_at_utc`; `V<n>` well-formed); run `python3 tests/speckit-pro/run-all.py` and confirm green. [FR-011][SC-002] — tests/speckit-pro/unit/test-efficiency-claude-telemetry.py
- [ ] T018 [WP1] Assemble the **WP1 PR review packet**: what changed, why, non-goals (corpus execution / scoring / statistics / fallback ordering deferred to CAR-003+), review order (WP1→WP2→WP3), scope budget **including the T001 G5 over-ceiling exception**, traceability (WP1 files → FR/SC IDs), verification evidence (`python3 tests/speckit-pro/run-all.py`), known gaps (any CAP-Q recorded open in the snapshot), rollback (revert the additive PR; no feature flag). [Reviewability Budget / PR Review Packet Requirements] — WP1 PR body

**Checkpoint**: US1 complete — the canonical snapshot is committed and continuously validated. **This is the MVP.**

---

## Phase 4: WP2 — Telemetry Profile + Route-Resolution/Exact-Treatment Contracts + CAR-003 Handoff (US2, US3)

**Goal**: Publish the versioned telemetry capability profile and finalize the `route_resolution` / exact-treatment replay trace contracts that CAR-003..CAR-011 consume.

**Independent Test**: The committed profile validates against `telemetryProfile` (exactly-one-label per field, nulls preserved) and the standalone `route-resolution.json` fixture validates against `routeResolution` with every FR-021 binding present.

- [ ] T019 [WP2] Author the versioned telemetry capability profile `docs/ai/research/claude-telemetry-capability-profile.json` (validated against the `telemetryProfile` `$def`): `telemetry_profile_id` = `CAR-002-TP-<YYYY-MM-DD>-V<n>`, recorded `pinned_client_version` (FR-018, in a field, not the ID), cross-ref `runtime_capability_snapshot_id`, and a `field_classifications` array with one entry per telemetry field. [FR-018] — docs/ai/research/claude-telemetry-capability-profile.json
- [ ] T020 [WP2] Populate the field classifications with **exactly one** label each from `{stable_native, derived, derived_from_controlled_configuration, unavailable}`, mandating the FR-019 minimums: `stable_native` for the raw token vector (`usage.input_tokens`/`output_tokens`/`cache_read_input_tokens`, per-TTL `usage.cache_creation.ephemeral_5m_input_tokens`/`ephemeral_1h_input_tokens`, flat `usage.cache_creation_input_tokens`, `num_turns`, `duration_ms`, the `modelUsage` per-model key set + `inputTokens`/`outputTokens`/`cacheReadInputTokens`/`cacheCreationInputTokens`/`contextWindow`, and the effective model per AC-2.4/roadmap verbatim), `derived` for `total_cost_usd` + `modelUsage.<model>.costUSD`, `derived_from_controlled_configuration` for effective reasoning effort; every field not yet confirmed by T015 step 1 labeled `observation`, never `fact` (FR-027; crosswalk from CAR-001 `source_class`). [FR-019][SC-006] — docs/ai/research/claude-telemetry-capability-profile.json
- [ ] T021 [WP2] Preserve null-valued telemetry fields in the profile: each unobserved field is present with `observed_value: null` and still classified (typically `unavailable`), **never dropped**, so "unavailable" is distinguishable from "absent". [FR-020][SC-006] — docs/ai/research/claude-telemetry-capability-profile.json
- [ ] T022 [P] [WP2] Author the standalone `route-resolution.json` fixture under `tests/speckit-pro/unit/fixtures/claude-telemetry-records/` exercising the `routeResolution` `$def` in isolation (US3 acceptance scenario 1): every FR-021 binding present — agent/requested alias/resolved dated ID/effort/`instruction_sha256`/`mutation_contract`/**`dispatch_namespace`**/**`parent_session_configuration`**/client version/`fast_mode_state`/`env_override_proof`, verbatim CAR-001 cross-ref IDs (`candidate_route_id`, `agent_contract_id`, `runtime_capability_snapshot_id`), nullable `fallback_index`/`fallback_reason` null, deterministic literal `route_resolution_id` `CAR-002-RR-FIXTURE-001`. [FR-021] — tests/speckit-pro/unit/fixtures/claude-telemetry-records/route-resolution.json
- [ ] T023 [WP2] Extend `test-efficiency-claude-telemetry.py` to validate the committed **telemetry profile** against `telemetryProfile` (SC-006 exactly-one-label + nulls-preserved) and the **`route-resolution.json` fixture** against `routeResolution` (all FR-021 bindings incl. `dispatch_namespace`/`parent_session_configuration`); run the suite and confirm green. [FR-019][FR-020][FR-021][SC-006] — tests/speckit-pro/unit/test-efficiency-claude-telemetry.py
- [ ] T024 [WP2] Finalize the exact-treatment replay telemetry-linkage rule in the validator: when `outcome.telemetry_ref` is non-null it MUST resolve against the telemetry-profile field set during deterministic validation (raw token categories, nulls preserved, reachable from the record); a dangling reference fails validation. [FR-022] — tests/speckit-pro/unit/test-efficiency-claude-telemetry.py
- [ ] T025 [WP2] Add the WP2 `docs/ai/research/**` deliverable (`claude-telemetry-capability-profile.json`) to the `allowed_agent_route_research_exact` exact-path set in `tests/speckit-pro/unit/test-speckit-pro-runner.py` (docs-surface guard, research R15); confirm the guard passes. [FR-018 / docs-surface guard] — tests/speckit-pro/unit/test-speckit-pro-runner.py
- [ ] T026 [WP2] Confirm the CAR-003 handoff (quickstart.md Part C): a downstream consumer can bind a `route_resolution` / `exactTreatmentReplay` record from the published schema, snapshot, and profile **without re-probing** and without any capability question CAR-002 was responsible for answering. **Done-check**: the handoff path is exercised by the committed `route-resolution.json` fixture validating green (SC-008 traceable to committed bytes). [FR-022][SC-008] — quickstart.md Part C / tests/speckit-pro/unit/fixtures/claude-telemetry-records/route-resolution.json
- [ ] T027 [WP2] Check/regenerate the committed docs-site test reference page if the WP2 test-tree `.py` edits changed it (per `tests/speckit-pro/AGENTS.md`); **done-check**: no uncommitted diff. [repo docs contract] — docs-site/src/content/docs/reference/tests.md (generated — regenerate via the docs-site build; never hand-edit, per tests/speckit-pro/AGENTS.md)
- [ ] T028 [WP2] Assemble the **WP2 PR review packet** (same structure as T018, WP2 files → FR/SC mapping; review order note that WP2 consumes the WP1 schema and authors no new `$defs`). [PR Review Packet Requirements] — WP2 PR body

**Checkpoint**: US2 + US3 complete — the telemetry profile and both trace contracts are published and validated.

---

## Phase 5: WP3 — Four Record-Class Fixtures + Deterministic Validation + 37-Route Join (US4)

**Goal**: Commit the four synthetic exact-treatment fixtures and mature the deterministic validator into the full trust anchor — schema conformance, class invariants, integrity re-checks, and the 37-route→tuple join — all offline.

**Independent Test**: `python3 tests/speckit-pro/run-all.py` on a machine with **no** `claude` CLI and **no** network validates all four fixtures + the route-resolution fixture + the snapshot + the telemetry profile and computes the 37-route join, passing with zero live model calls; a drifted fixture fails closed.

> The four record-class fixtures (T029–T032) are independent files and are **parallel-safe [P]**.

- [ ] T029 [P] [WP3] Author `success.json` — a complete exact-treatment replay record with a full `route_resolution` binding, every field present and non-null, `record_class: "success"`, `scorable: true`, `outcome.status: "completed"`. [FR-025][SC-003] — tests/speckit-pro/unit/fixtures/claude-telemetry-records/success.json
- [ ] T030 [P] [WP3] Author `null.json` — every **nullable** field present but `null` (not dropped, proving "unavailable" ≠ "absent"), required non-nullable fields present, `record_class: "null"`, `scorable: true`, `outcome.status: "completed"`. [FR-025][FR-020][SC-003] — tests/speckit-pro/unit/fixtures/claude-telemetry-records/null.json
- [ ] T031 [P] [WP3] Author `unavailable.json` — `record_class: "unavailable"`, cross-referencing the corresponding unavailable observation in the committed snapshot via `runtime_capability_snapshot_id` (FR-021), `scorable: false`, `outcome.status: "unavailable"`. [FR-025][FR-021][SC-003] — tests/speckit-pro/unit/fixtures/claude-telemetry-records/unavailable.json
- [ ] T032 [P] [WP3] Author `misdelivery.json` — `observed_model_id` ≠ `route_resolution.resolved_dated_model_id` with `fallback_index`/`fallback_reason` **null** (precedence rule: fallback-null difference = misdelivery, not resolver fallback), `record_class: "misdelivery"`, `scorable: false`, `outcome.status: "completed"`. [FR-025][SC-003] — tests/speckit-pro/unit/fixtures/claude-telemetry-records/misdelivery.json
- [ ] T033 [WP3] Extend `test-efficiency-claude-telemetry.py` to validate all four record-class fixtures against the `exactTreatmentReplay` `$def` on every CI run (SC-003 100% record-class coverage; a drifted fixture fails the suite and blocks merge). [FR-024][FR-002][SC-003] — tests/speckit-pro/unit/test-efficiency-claude-telemetry.py
- [ ] T034 [WP3] Add the FR-024 **class-invariant + semantic** checks to the validator beyond structural conformance: the class↔scorable pairing (`unavailable` and `misdelivery` ⇒ non-scorable; `success` and `null` ⇒ scorable) and the per-class semantic rule (misdelivery: observed ≠ resolved qualified ID; null: every nullable field present-but-null; unavailable: a resolvable snapshot cross-reference). [FR-024][FR-025] — tests/speckit-pro/unit/test-efficiency-claude-telemetry.py
- [ ] T035 [WP3] Add the **37-route → tuple join** to the validator: recompute the join every run from the committed CAR-001 manifest `model_selector`/`effort_selector` against the snapshot's `tuple_evidence` (derived, **never persisted** as a `candidate_route_id`→`tuple_id` map), failing closed if any of the 37 routes resolves to **zero** or to **more than one** tuple. [FR-024][FR-004][SC-005] — tests/speckit-pro/unit/test-efficiency-claude-telemetry.py
- [ ] T036 [WP3] Add the FR-024 **integrity re-checks** to the validator: recompute each stored `raw_output_sha256` over the committed sanitized payload bytes and the canary hash over the recorded canary text, failing on any mismatch; **re-scan** every committed payload for an unsanitized home/user/session path (continuously re-checking the write-time FR-012/FR-013 guarantee); and verify **referential integrity** — every committed `candidate_route_id`/`agent_contract_id` resolves to an existing CAR-001 manifest entry and every non-null `runtime_capability_snapshot_id`/`telemetry_ref` resolves to a committed record, not merely a well-formed string. [FR-024][FR-012][FR-013][FR-022] — tests/speckit-pro/unit/test-efficiency-claude-telemetry.py
- [ ] T037 [WP3] Prove offline determinism: run `python3 tests/speckit-pro/run-all.py` on a machine with **no** `claude` CLI and **no** network; confirm the full default suite (Layers 1, 4, 5) validates the four fixtures + route-resolution fixture + snapshot + telemetry profile + 37-route join with **zero live model calls** and passes. [FR-002][SC-002] — verification command
- [ ] T038 [WP3] Check/regenerate the committed docs-site test reference page if the WP3 test-tree `.py` edits changed it (per `tests/speckit-pro/AGENTS.md`); **done-check**: no uncommitted diff. [repo docs contract] — docs-site/src/content/docs/reference/tests.md (generated — regenerate via the docs-site build; never hand-edit, per tests/speckit-pro/AGENTS.md)
- [ ] T039 [WP3] Assemble the **WP3 PR review packet** (same structure as T018, WP3 files → FR/SC mapping; note WP3 extends the Layer 4 coverage WP1 registered and joins against the WP1 snapshot). [PR Review Packet Requirements] — WP3 PR body

**Checkpoint**: US4 complete — the schemas are a deterministically-enforced binding contract. All four work packages independently verifiable.

---

## Phase 6: Polish & Cross-Cutting

- [ ] T040 [WP3] Run the quickstart.md Part B validation as the final gate: `python3 tests/speckit-pro/run-all.py` green across Layers 1/4/5 offline, and confirm the FR→Task traceability table below shows every FR in plan.md's FR→WP table mapped to ≥1 task (G5 cross-reference). [SC-002][FR-002] — verification command

---

## Dependencies & Execution Order

### Phase / Work-Package dependencies

- **Phase 1 (Setup)**: no dependencies — record the G5 disposition first.
- **Phase 2 (WP1 foundation)**: depends on Phase 1. The schema `$defs` (T003–T004) + validator (T005) block all downstream validation.
- **Phase 3 (WP1 probe + snapshot)**: depends on Phase 2 (writer validates against the schema). **T015 (operator run) is human-gated** and precedes snapshot validation (T017).
- **Phase 4 (WP2)**: depends on WP1's published schema (consumes it; authors no new `$defs`) and the committed `runtime_capability_snapshot_id` (cross-ref).
- **Phase 5 (WP3)**: depends on WP2's `$def` usage and joins against the WP1 snapshot + CAR-001 manifest.
- **Phase 6 (Polish)**: depends on all three WPs.

### Within WP1 (TDD)

T002 (failing test) → T003 → T004 (schema) → T005 (validator) → T006 (green) → T007 (register) → T008 (docs ref) → T009 → T010 → T011 → T012 → T013 (pure-logic tests) → T014 (subagent mechanism) → **T015 (operator run, human-gated)** → T016 (guard) → T017 (snapshot validation) → T018 (PR packet).

### Parallel opportunities

- **T029, T030, T031, T032** — the four record-class fixtures are different files with no interdependency → run in parallel `[P]`.
- **T022** (route-resolution fixture) is independent of the telemetry-profile authoring (T019–T021) — both depend only on the WP1 schema → `[P]`.
- WP1's schema is a single file (T003/T004 sequential); the probe-tool tasks (T009–T014) share `claude_capabilities.py` and are sequential.

---

## Implementation Strategy

### MVP (WP1 / US1 only)

1. Phase 1 (reviewability gate) → Phase 2 (schema + validator + registration) → Phase 3 (probe tool + **operator run** + snapshot).
2. **STOP and VALIDATE**: the committed snapshot answers CAP-Q1..Q6 and validates against the schema; the fail-closed writer aborts on an invalid observation. WP1 delivers standalone value even if WP2/WP3 never ship (spec US1 "Why this priority").

### Incremental delivery (one PR per work package)

1. WP1 → committed schema + validator + snapshot (MVP) → ship PR 1.
2. WP2 → telemetry profile + trace contracts + CAR-003 handoff → ship PR 2.
3. WP3 → four fixtures + deterministic validation + 37-route join → ship PR 3.

Each WP is an independently reviewable, independently verifiable additive increment; review order WP1→WP2→WP3.

---

## FR → Task traceability (G5 cross-reference)

Every FR in plan.md's FR→WP table maps to at least one task.

| FR | WP | Task(s) |
|----|----|---------|
| FR-001 | WP1 | T011, T014, T015 |
| FR-002 | WP3 | T011, T013, T033, T037, T040 |
| FR-003 | WP1 | T009, T010, T015 |
| FR-004 | WP1 | T009, T035 |
| FR-005 | WP1 | T009 |
| FR-006 | WP1 | T012 |
| FR-007 | WP1 | T012 |
| FR-008 | WP1 | T012 |
| FR-009 | WP1 | T012, T014 |
| FR-010 | WP1 | T012 |
| FR-011 | WP1 | T015, T016, T017 |
| FR-012 | WP1 | T009, T036 |
| FR-013 | WP1 | T009, T036 |
| FR-014 | WP1 | T012 |
| FR-015 | WP1 | T003, T004 |
| FR-016 | WP1 | T002, T005, T006 |
| FR-017 | WP1 | T003 |
| FR-018 | WP2 | T019 |
| FR-019 | WP2 | T020, T023 |
| FR-020 | WP2 | T021, T023, T030 |
| FR-021 | WP2 | T004, T022, T031 |
| FR-022 | WP2 | T024, T026, T036 |
| FR-023 | WP1 | T006, T009, T013 |
| FR-024 | WP3 | T033, T034, T035, T036 |
| FR-025 | WP3 | T029, T030, T031, T032, T034 |
| FR-026 | WP1 | T012 |
| FR-027 | WP1 | T012, T020 |
| FR-028 | WP1 | T002, T005, T007, T008 |

SC coverage: SC-001 (T015), SC-002 (T013/T017/T037/T040), SC-003 (T029–T033), SC-004 (T006/T015), SC-005 (T035), SC-006 (T020/T021/T023), SC-007 (T003/T005), SC-008 (T026).

---

## Notes

- **CHK034 satisfied**: every task carries a single explicit `[WP1]`/`[WP2]`/`[WP3]` tag matching plan.md's per-WP file assignment, so split-PR emission routes each task to exactly one PR.
- **CHK035 satisfied**: every task cites its FR/SC markers and its exact file path; no task spans two work packages. The two recurring test files (`test-efficiency-claude-telemetry.py`: NEW@WP1/MOD@WP2/MOD@WP3; `test-speckit-pro-runner.py`: MOD@WP1/WP2) are incrementally extended, each task touching only its own WP's slice (CHK030).
- WP tags occupy the template's `[Story]` position because CHK034 is a forward requirement specific to this tasks.md; WP1=US1, WP2=US2+US3, WP3=US4.
- Every done-check is observable: a test passes, JSON validates against a `$def`, a fixture exists, the suite is green offline, or a sanitized-payload hash reproduces from committed bytes.
- **T015 is the only live-`claude` path** and is human-gated (never CI, never TDD, FR-001). No task executes a corpus, scores, computes statistics, orders fallbacks, or edits shipped agent frontmatter (design-concept Non-goals; the throwaway probe agent file in T014 is uncommitted).
