# Tasks: CAR-005 Model Availability, Fallback, and Recovery Simulation

**Input**: Design documents from `specs/car-005-availability-fallback-recovery/`

**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories),
`research.md`, `data-model.md`, `quickstart.md`. No per-feature `contracts/`
directory exists, deliberately — the design contracts *are* the three committed
JSON Schema documents in the test tree, and copying them here would create two
sources of truth for the same bytes (plan.md §Project Structure, FR-017a).

**Note**: This task list was produced against the `speckit-pro-reviewability`
preset tasks template (v1.0.0), which overrides the core template. Every section
the preset declares is present and filled: the Reviewability budget block, the
Foundational reviewability-checkpoint task, the PR-review-packet task, the
quickstart-validation task, and the budget note in Notes.

**Tests**: Test tasks are included and are **mandatory** here, not optional. This
feature's deliverable *is* a test surface — a reference simulator plus a pinned
fixture corpus plus the unit module that replays it. Every implementation task is
paired with the assertion that proves it, in RED→GREEN order.

**Reviewability**: The task list preserves the spec's reviewability budget. The
declared surface is 0 production files, 7 authored files plus 1 generated, and one
primary review surface (harness/adapter), so no automated threshold warns or
blocks — `estimate-reviewable-loc` computes `production_files × 40 = 0`. The split
into two slices is therefore **elected on review burden and independent slice
value, not gate-forced**, and plan-time or PR-time re-estimation cannot overturn
it by returning a smaller number. Task generation stayed inside that election: it
added no third slice and no task outside the seven-file set FR-033a fixes. T004 is
the checkpoint task that records this before any file is written.

**Organization**: Tasks are grouped by user story so each story is independently
implementable, testable, and landable. User Story 1 is slice 1; User Story 2 is
slice 2, stacked on slice 1 as a `gh-stack` chain (FR-033).

## Format: `[ID] [P?] [Story?] [Slice] Description`

- **[P]**: Can run in parallel — different files, no shared state. Two tasks that
  append to the same file are **not** parallel-safe, which is why `[P]` is rare
  here: slice 1 has exactly one simulator module, one corpus file, and one test
  module, so nearly every task after Foundational is serialized on a shared file.
- **[Story]**: `[US1]` or `[US2]`, required for user-story phase tasks only.
  Setup, Foundational, and Polish tasks carry no story label.
- **[Slice]**: `[S1]` or `[S2]`, required on **every** task without exception.
  The orchestrator drives Phase 7 from this partition and then emits two stacked
  pull requests, so an unassigned task would block PR emission. `[S1]` ≡ slice 1
  ≡ the first PR; `[S2]` ≡ slice 2 ≡ the second PR, based on slice 1.
- **Description**: Clear action with the exact repository-relative file path.

## Path Conventions

None of the core template's three project shapes applies. This feature is
repository-only validation, so paths follow the existing Layer 6 efficiency
layout:

- **Schemas**: `tests/speckit-pro/layer6-efficiency/contracts-claude/`
- **Simulator library**: `tests/speckit-pro/layer6-efficiency/lib/`
- **Fixture corpus**: `tests/speckit-pro/layer6-efficiency/fixtures-fallback/`
- **Unit test**: `tests/speckit-pro/unit/`
- **Suite registry**: `tests/speckit-pro/suite-manifest.json`
- **Generated docs page**: `docs-site/src/content/docs/reference/tests.md`

The shared byte-identical `tests/speckit-pro/layer6-efficiency/contracts/`
directory is **never** touched (FR-016, SC-005). No path under `speckit-pro/` is
touched (FR-030, SC-004).

## Verification Commands

This repository has **no typechecker and no linter**, so no task runs one.

| Purpose | Command |
| --- | --- |
| Structural | `python3 tests/speckit-pro/run-all.py --layer 1` |
| Script safety and unit coverage | `python3 tests/speckit-pro/run-all.py --layer 4` |
| Full suite | `python3 tests/speckit-pro/run-all.py` |
| Inner loop on the one new module | `python3 tests/speckit-pro/unit/test-route-fallback-simulation.py` |
| Docs reference regen (required after any tracked `.py` change under the test tree) | `pnpm --dir docs-site reference:generate` then `pnpm --dir docs-site reference:check` |

---

## Phase 1: Setup (Shared Infrastructure) — Slice 1

**Purpose**: Establish an attributable baseline and confirm the read-only import
surfaces this feature depends on, before any file is authored.

- [X] T001 [S1] Record a green baseline by running `python3 tests/speckit-pro/run-all.py` from the repository root and noting the pass count, so any later failure is attributable to this feature rather than to pre-existing state. Acceptance: zero failures; treat "zero failures" as the criterion rather than the absolute count, which rises as other work lands (quickstart.md §Baseline).
- [X] T002 [P] [S1] Install the docs-site dependencies once for this worktree with `pnpm --dir docs-site install --frozen-lockfile`. Acceptance: the command exits clean and `pnpm --dir docs-site reference:check` runs without a missing-dependency error. Required because both slices add a tracked `.py` file under `tests/speckit-pro/`, which regenerates `docs-site/src/content/docs/reference/tests.md` (quickstart.md §Prerequisites).
- [X] T003 [P] [S1] Confirm the five read-only in-tree imports resolve before designing around them: `canonical_json` from `tests/speckit-pro/layer6-efficiency/lib/claude_successor_freeze.py`, and `validate_instance`, `load_contract`, `CONTRACT_ROOT`, `ControlContractError` from `tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py`. Acceptance: all five import successfully in a throwaway interpreter session using the two-path `sys.path` insertion pattern the existing unit modules use; `canonical_json` is verified to emit **no trailing newline** and to use `sort_keys=True`, minimal separators, `ensure_ascii=False`, `allow_nan=False` (FR-014a). Nothing is written; this is a read-only de-risking check.

---

## Phase 2: Foundational (Blocking Prerequisites) — Slice 1

**Purpose**: The three JSON Schema documents and the simulator's canonical
serialization surface. Both user stories express themselves in terms of the
report contract, so nothing in either story can begin until these land.

**CRITICAL**: All three schemas land **complete in slice 1**. Slice 2 modifies no
schema file at all — strictly stronger than append-only additivity, and it
preserves this directory's unbroken invariant that no contract document has ever
been edited after its introducing commit (FR-019, FR-033a, FR-033b).

- [X] T004 [S1] Record the reviewability budget and seam decision in the slice-1 working notes before authoring any file: 0 production files, 7 authored plus 1 generated, one primary surface (harness/adapter), secondary surface seed/config (one manifest entry); split elected on review burden and independent slice value rather than forced by a threshold; the advisory `estimate-spec-size` figure suggesting more slices is recorded and **not** acted on, because only an operator decision moves this split. Acceptance: the seven-file allocation in FR-033a is restated and confirmed unchanged, and the restack rule is recorded — a slice-2 finding that needs a slice-1 change lands on slice 1's branch and the chain restacks, never absorbed into slice 2's diff (FR-033, FR-033a, FR-033b, plan.md §Reviewability Budget).
- [X] T005 [S1] Create `tests/speckit-pro/unit/test-route-fallback-simulation.py` with its module docstring, the `REPO_ROOT` / two-path `sys.path` preamble the sibling unit modules use, the `run_counted` entry point, and a first RED test class asserting the three schema documents load through `load_contract`, declare `$schema` draft 2020-12, carry their `https://racecraft.dev/schemas/car-005/<name>.schema.json` `$id`, and pin `schema_version` with `const`. Acceptance: the module runs and the new test class **FAILS** because no schema exists yet; no test method name and no file stem contains `car-005` (FR-032, verified by the existing layout test).
- [X] T006 [P] [S1] Author `tests/speckit-pro/layer6-efficiency/contracts-claude/route-policy.schema.json`: root requiring `schema_version`, `agent`, `preferred_route`, `fallback_routes`, `budgets`, with one optional `optional_helper`; `$defs/agentIdentity` (`name`, `role_class` inline enum `required_executor`/`bounded_analyst`/`optional_helper`); `$defs/route` with `route_id`, `alias`, `qualified` required and `resolved_model`, `effort`, `adjacent_to`, `substituted_agent` optional; the closed five-member effort ladder `low`/`medium`/`high`/`xhigh`/`max` declared inline; `fallback_routes` as an ordered array with `minItems: 0` and **no** `uniqueItems`; `$defs/declaredBudgets` with `max_probe_attempts` (`minimum: 1`, `maximum: 8`), `max_retries` (`minimum: 0`, `maximum: 8`), `max_candidate_routes` (`minimum: 1`, `maximum: 8`); and `$defs/declaredOptionalHelper` carrying the helper's own `agent`, `preferred_route`, and `fallback_routes`. Acceptance: `resolved_model` and `effort` stay **optional** and `fallback_routes` declares **no** `uniqueItems`, so the FR-023 and FR-020 fixtures produce diagnostics rather than validation errors; the budget maxima are co-located with each field's `type`; record objects close with `additionalProperties: false` (FR-003, FR-003a, FR-007a, FR-016, FR-016a, FR-025b, FR-027).
- [X] T007 [P] [S1] Author `tests/speckit-pro/layer6-efficiency/contracts-claude/environment-snapshot-projection.schema.json` with all **seven** projection members plus `schema_version`: `available_models`, `alias_bindings`, `supported_efforts`, `probe_availability`, `exact_invocation_probe`, `platform_route_changes`, `available_models_allowlist`, each required. Acceptance: the four open-keyed maps (`alias_bindings`, `supported_efforts`, `probe_availability`, `exact_invocation_probe`) use `propertyNames` plus a value schema and **never** `additionalProperties: false`, which would make the document unsatisfiable for any non-empty snapshot; `platform_route_changes` is an array of closed two-field records with `uniqueItems: true`; `available_models_allowlist` is a `uniqueItems` string array with `minItems: 0`; the CAR-002 capture-record shape is **not** reused; every member maps to a named consuming requirement per the consumed-by column in data-model.md §2, and no consumed fact is missing (FR-002, FR-002a, FR-016, FR-016a).
- [X] T008 [P] [S1] Author the root of `tests/speckit-pro/layer6-efficiency/contracts-claude/route-resolution-report.schema.json` as a **single** shape discriminated by `outcome`: require `schema_version`, `agent`, `outcome`, `attempted_routes`, `diagnostics`, `budgets`, `release_claim_eligible`, `optional_helper` in both outcomes; express conditional requiredness as three `allOf` + `if`/`then` branches carrying `required` and `not: {required: [...]}` — `resolved` requires `effective_dispatch_tuple` and forbids `unresolved_agent`, `no_safe_route` requires `unresolved_agent`, and `override` present requires `effective_dispatch_tuple`; add `$defs/attemptedRoute` (with `disposition` inline enum `selected`/`rejected`, and model/effort optional), `$defs/dispatchTuple`, `$defs/reportedBudgets` (declared caps plus three actual integer counters), `$defs/optionalHelper` (`consulted`, `no_helper_path_validated`, `probe_attempts` with `minimum: 0`), and `$defs/override` (`source` as `const` `CLAUDE_CODE_SUBAGENT_MODEL`, `requested_model`, `disposition` inline enum `honored`/`skipped_by_allowlist`, `qualified`, conditional `tuple`, `would_have_been`). Acceptance: `attempted_routes` declares `minItems: 0` so a pre-walk rejection validates; the document is **not** a root-level `oneOf` and is **not** split into two report schemas; `override.tuple` is required on `honored` and forbidden on `skipped_by_allowlist` (FR-013, FR-013a, FR-016, FR-019c, FR-024b, FR-025a, FR-026).
- [X] T009 [S1] Extend `route-resolution-report.schema.json` with the two diagnostic definitions: `$defs/resolutionDiagnostic` whose `properties/code/enum` holds exactly the five roadmap codes, and `$defs/policyViolationDiagnostic` whose `properties/code/enum` holds exactly the five policy-violation codes, unioned where the diagnostics array is declared by `{"oneOf": [{"$ref": "#/$defs/resolutionDiagnostic"}, {"$ref": "#/$defs/policyViolationDiagnostic"}]}`; both share the runner envelope with `code`, `message` (`maxLength: 240`), `severity` (inline enum `info`/`warning`/`error`), `source` (`const` `route-fallback-simulator`), and `remediation` required, and `details` optional; add **eight** `allOf` branches — four in each definition — each making `details` required **and** `route_id` required within it, with the first two resolution branches additionally requiring the payload FR-006 and FR-007 name. Acceptance: `unqualified_override` is the one member of either enum taking no branch, because it is an environment condition scoped to no route; `remediation` is a field of each diagnostic entry and **never** a top-level report field; no `$ref` leaves `#/$defs/`; the diagnostics dialect mirrors the installed **runner**, not the autopilot gate-state contract that requires `details` and omits `remediation` (FR-005, FR-012, FR-012c, FR-016, FR-016a, FR-019, FR-029a).
- [X] T010 [S1] Complete `route-resolution-report.schema.json` with `$defs/remediation` — `summary` required, `actions` required as an array with `minItems: 1`, `maxItems: 3`, and `items` a **closed inline enum of eleven literal strings** including `Roll back to the previous plugin release.` verbatim — and with the named `details` properties: `sub_reason` (inline four-member enum `alias_unresolved`, `alias_repointed`, `model_absent`, `platform_route_changed`), `alias`, `pinned_resolved_model`, `observed_resolved_model`, `declared_effort`, `supported_efforts`, `route_id`, and `exhausted_budget` (array over an inline three-member enum `probe_attempts`/`retries`/`candidate_routes`, `minItems: 1`, `uniqueItems: true`). Acceptance: `details` is the single deliberate `additionalProperties: true` object, so slice 2 needs no schema field; action entries are plain strings with no structured objects and no substitution slots, so case-specific values live only in `details`; the action enum is declared **inline** at `$defs/remediation/properties/actions/items/enum` rather than as a bare-enum `$defs` member, which is the documented deviation from FR-012a's literal placement recorded in plan.md §Complexity Tracking (FR-012a, FR-016a, FR-026a).
- [X] T011 [S1] Run `python3 tests/speckit-pro/run-all.py --layer 4` and confirm the three new documents pass the pre-existing keyword-support test. Acceptance: `test-policy-control-contracts` passes, proving every keyword used — `oneOf`, `allOf`/`if`/`then`/`not`, `minItems`/`maxItems`, `maximum`, `const`, `propertyNames`, `uniqueItems` — is inside the shared engine's supported set; no `ControlContractError` mentioning `$ref` is raised, proving no cross-document reference was introduced; the T005 contract-presence class now **PASSES** (GREEN) (FR-016, FR-032a).
- [X] T012 [S1] Create `tests/speckit-pro/layer6-efficiency/lib/claude_route_fallback.py` with its module docstring, the read-only imports of `canonical_json` and the four validation-engine names, module-level constants for both closed vocabularies and the sub-reason evaluation order, `RouteFallbackError(AssertionError)`, a `_require(condition, message)` fail-closed helper, and `serialize_report(report)` returning `canonical_json(report)`. Acceptance: the module is a pure function surface with no filesystem, network, wall-clock, or randomness input in `resolve`; it is the **single** module for this capability and no second module is created for structural validation; `serialize_report` appends no trailing newline; the file stem contains no spec ID (FR-001, FR-014a, FR-030, FR-032, FR-033d).

**Checkpoint**: All three contracts are complete and validated by the existing
keyword test; the simulator module exists with its serialization surface. Slice 2
will touch no schema file from here on. User Story 1 implementation can begin.

---

## Phase 3: User Story 1 — Resolution-failure semantics (Priority: P1) — Slice 1 🎯 MVP

**Goal**: Deliver the environment-snapshot projection, the route-policy fixture
shape, the ordered preferred-then-fallback resolution walk, the five pinned
resolution reason codes with machine-readable sub-reasons, and byte-identical
deterministic replay against pinned expected reports.

**Independent Test**: Run the reference simulator over the nine resolution-failure
cases in the scenario corpus and assert each produced report is byte-identical to
that case's pinned expected report, and byte-identical across two successive runs.

**Slice-1 completeness rule**: This slice MUST be complete and passing on its own
with nothing stubbed and no deferral marker left for a later slice. Every report
it emits is a fully valid instance of the committed report schema, including
`budgets` with all three actual counters, `release_claim_eligible`, and
`optional_helper` (FR-033b).

### Tests and implementation for User Story 1 (RED→GREEN pairs)

> Write each test first and confirm it FAILS before writing the implementation
> that makes it pass. All test tasks append to the one unit module and all
> simulator tasks append to the one library module, so none of them is `[P]`.

- [X] T013 [US1] [S1] RED: add the replay harness test to `tests/speckit-pro/unit/test-route-fallback-simulation.py` — for each corpus case, resolve twice over identical inputs and assert both serialized reports are byte-identical to each other and to the case's pinned expected report under canonical serialization. Acceptance: the test **FAILS** because neither `load_corpus`, `resolve`, nor the corpus exists yet (FR-014, SC-002).
- [X] T014 [US1] [S1] GREEN: implement `load_corpus(path=...)` and the `resolve(policy, snapshot, overrides, budgets)` walk in `tests/speckit-pro/layer6-efficiency/lib/claude_route_fallback.py` — attempt the preferred route first, then the declared fallbacks in their declared order, select the first compatible route, and record **every** attempted route in attempt order in `attempted_routes` with its `disposition`. Acceptance: array order **is** attempt order with no redundant index field; the walk is a pure function of its four arguments (FR-001, FR-004).
- [X] T015 [US1] [S1] RED→GREEN: implement `preferred_model_unavailable` with its closed four-member sub-reason vocabulary as **staged private helpers called in declaration order** — `alias_unresolved`, `alias_repointed`, `model_absent`, `platform_route_changed` — so the evaluation order is a call-graph property rather than a comment a later edit can reorder. Acceptance: exactly one sub-reason applies to any snapshot; `alias_repointed` carries the pinned-versus-observed model pair, `model_absent` carries the missing resolved model ID, and `platform_route_changed` is reached only when the three prior predicates all miss because it reads a separate snapshot field and can otherwise co-occur; each diagnostic carries `details.route_id` (FR-006, FR-012, FR-029a).
- [X] T016 [US1] [S1] RED→GREEN: implement `effort_unsupported` — a route whose model is available but whose declared effort is absent from that model's `supported_efforts` entry is rejected, with `details` naming both the declared effort and the model's supported efforts. Acceptance: rejection happens at preflight even though the documented runtime silently degrades to the highest supported level at or below the declared one — this divergence is a **recorded deliberate decision**, not an oversight, and MUST NOT be "fixed" toward runtime behaviour (FR-007, FR-007a, SC-013).
- [X] T017 [US1] [S1] RED→GREEN: implement `capability_probe_unavailable` — a route whose model carries `probe_availability: false` is rejected, and probe absence is **never** treated as probe success. Acceptance: the CAR-002 `undetermined` outcome maps onto probe unavailability rather than onto `success` or `absent`, so an observation from which no availability claim derives is handled fail-closed; the mapping is the one declared in data-model.md §2 and leaves no CAR-002 outcome unrepresented (FR-008, FR-002a).
- [X] T018 [US1] [S1] RED→GREEN: implement `treatment_probe_failed` — a route whose `exact_invocation_probe` outcome is `failure` is rejected and MUST NOT be selected. Acceptance: the route appears in `attempted_routes` with `disposition: rejected` and the walk continues to the next declared fallback (FR-009).
- [X] T019 [US1] [S1] RED→GREEN: implement diagnostic emission ordering as a **second staged call graph**, separate from the sub-reason staging — one private helper per rejection family called in the FR-005 declaration order, each appending its own diagnostic when its predicate holds, so a route failing several independent checks emits **one diagnostic per failed check** rather than only the highest-precedence reason; assemble the whole `diagnostics` array in its three stages (pre-walk violations, then per-route entries in attempt order, then `unqualified_override`, then exactly one terminal `no_safe_route` last). Acceptance: the Edge Cases example emits `effort_unsupported` then `treatment_probe_failed` in that order; the accumulate-all shape is used rather than an alphabetical sort, which would scramble a meaningful precedence; the biconditional holds — `outcome` is `no_safe_route` **if and only if** exactly one diagnostic carries code `no_safe_route`, and a `resolved` report carries none (FR-012b).
- [X] T020 [US1] [S1] RED→GREEN: implement the effective dispatch tuple on the resolved path — `agent`, `alias`, `resolved_model`, `effort`, all required — and prove the clean-success path emits **no** resolution diagnostic when the preferred route's exact-invocation probe succeeds. Acceptance: a consumer reads the selected outcome without re-deriving it from the attempt list; `diagnostics` is an empty array on the clean success, which is why the array declares no `minItems` (FR-011, FR-013).
- [X] T021 [US1] [S1] RED→GREEN: implement the three report fields that are required in **every** report and would otherwise be the slice-1 stubs FR-033b forbids — `release_claim_eligible` derived as a closed disqualifier list with `true` as the residual (`false` when an override is in force, when `outcome` is `no_safe_route`, or when any policy-violation diagnostic is present); `optional_helper` in its no-helper-declared state (`consulted: false`, `no_helper_path_validated: true`, `probe_attempts: 0`); and `budgets` carrying the declared caps plus all three actual counters with their FR-026a units — `probe_attempts` once per route's **first** probe-state consultation, `retries` once per subsequent consultation of a failing route, `candidate_routes` once per candidate route entered. Acceptance: a report whose preferred route was rejected for `alias_repointed` or `platform_route_changed` and which then resolved on a declared qualified fallback reads `release_claim_eligible: true`, deliberately — the route-scoped fact is carried by that route's `attempted_routes` entry and its diagnostic sub-reason, not by this report-scoped flag; `probe_attempts <= candidate_routes` holds; **cap enforcement and the exhaustion terminal are slice 2**, but the counters themselves are complete here (FR-024a, FR-025a, FR-026a).

### Corpus authoring for User Story 1

> All corpus tasks append to the same single file, so none is `[P]`. Case order is
> **declaration order, never sorted**, so slice 2's appends never reorder or
> re-pin a slice-1 case (FR-015, FR-033b, FR-033c).

- [X] T022 [US1] [S1] Create `tests/speckit-pro/layer6-efficiency/fixtures-fallback/fallback-scenario-corpus.json` with its envelope — `schema_version`, `fixture_kind` set to `route_fallback_replay`, `description`, `cases` — and the first three cases with fully pinned expected reports: `preferred-absent-fallback-selected`, `fable-alias-model-absent`, `alias-unresolved`. Acceptance: each case carries its own `case_id`, `purpose`, `proves`, `requirements`, `policy`, `snapshot`, `overrides` (explicitly `null`), and `expected_report`; the `fable` case exercises the `model_absent` sub-reason because the roadmap subordinates it to preferred-model-absent; `alias-unresolved` exists as its own case because neither other sub-reason can describe it; agent names are drawn from the synthetic three-role cast, each carrying the `fixture-` prefix (`fixture-required-executor`, `fixture-bounded-analyst`, `fixture-optional-helper`), and **no** shipped agent name appears (FR-010, FR-015, FR-018, SC-006).
- [X] T023 [US1] [S1] Append the two alias/platform cases to the corpus: `alias-repointed` and `platform-route-changed`, each with a fully pinned report. Acceptance: `platform-route-changed` binds its alias **exactly as the route pins it** and lists the pinned resolved model among `available_models`, so the three earlier sub-reason predicates all miss and the case actually pins the sub-reason its name promises — a snapshot that also repoints the alias or omits the model resolves to `alias_repointed` or `model_absent` instead and surfaces as a replay failure whose stated cause looks unrelated to how the snapshot was built (FR-006, data-model.md §3).
- [X] T024 [US1] [S1] Append the three probe-and-effort cases to the corpus: `effort-unsupported`, `capability-probe-unavailable`, `treatment-probe-failed`, each with a fully pinned report. Acceptance: `effort-unsupported` pins both the declared effort and the model's supported efforts in `details`; `capability-probe-unavailable` uses an explicit `probe_availability: false` rather than an absent key; each diagnostic's `severity` is `warning` and its `actions` array is the single code-specific member from the data-model.md §3 mapping (FR-007, FR-008, FR-009, FR-012a, FR-012c).
- [X] T025 [US1] [S1] Append the clean-success case `preferred-probe-success-clean` to the corpus with its fully pinned report. Acceptance: the preferred route is selected, `diagnostics` is an empty array, `effective_dispatch_tuple` is recorded, `unresolved_agent` is absent, and `release_claim_eligible` is `true`; the corpus now holds exactly **nine** cases and each of the three role classes is the subject or declared helper of at least one case across the corpus as a whole (FR-011, FR-013, FR-018).
- [X] T026 [US1] [S1] Add the per-case schema-validation test to the unit module — validate every case's `policy` against the route-policy schema, `snapshot` against the projection schema, and `expected_report` against the resolution-report schema, using the imported `validate_instance` and `load_contract`. Acceptance: all nine cases validate against all three committed contracts; the failure mode for an over-constrained route schema is caught here rather than misdiagnosed later — an omitted model or effort must be **admitted** by the schema and rejected by the simulator (FR-003a, SC-003).

### Slice-1 assertion obligations that are easy to miss

> Each of the following is a distinct slice-1 obligation with its own task, because
> each is provable the moment the slice-1 schema exists and each would otherwise
> leave slice 1 shipping a guarantee unproven inside its own diff.

- [X] T027 [US1] [S1] Add the single-serializer discipline test and audit to the unit module: assert every byte comparison runs over the string `serialize_report` itself returns, and that the test module declares **no** local `canonical_json`. Acceptance: this is a **correctness trap, not a style rule** — the repository carries eight `canonical_json` definitions of which three append a trailing newline, all six existing occurrences under the unit tree re-declare their own copy, and the established comparison shape re-serializes both sides, so a divergent local copy would **cancel** a real mismatch and leave a green test over a simulator whose real output differs; additionally assert the serialized report carries no trailing newline and that every numeric field in every pinned report is an integer, so `repr`-dependent float rendering is unreachable (FR-014a, SC-002).
- [X] T028 [US1] [S1] Add the roadmap parity test to the unit module: read the resolution enum **live** from the committed schema by JSON pointer `$defs/resolutionDiagnostic/properties/code/enum` and assert exact set equality against the five codes the **Claude** routing roadmap pins, failing on both a missing and an extra member; pin the known cross-platform divergence as **test data** — the four byte-identical shared members plus the recorded third-member difference between the Claude and Codex spellings — so a silent change to either roadmap's spelling fails the suite. Acceptance: the test MUST NOT transcribe the enum's members into the test file, because a test that restated the enum would absorb the very drift it exists to catch — the schema and the roadmap are two independently committed witnesses and collapsing them into one defeats the assertion; the divergence is a **permanent intentional platform difference**, so no reconciliation is attempted; the count of Codex-side files changed by this feature is zero (FR-017, FR-017a, FR-017b, FR-017c, SC-012).
- [X] T029 [US1] [S1] Add the policy-violation enum set-equality test to the unit module: read `$defs/policyViolationDiagnostic/properties/code/enum` live by JSON pointer and assert exact set equality against the five members `fallback_loop`, `unqualified_adjacent_model`, `generic_agent_substitution`, `silent_inherit_materialization`, `unqualified_override`, failing in **both** directions. Acceptance: unlike the parity test, this one **does** declare its expected members in the test file, and that is correct rather than a violation of the read-live discipline — the policy-violation vocabulary has no independent committed authority, since the roadmap names its four rejections only in prose and the fifth member is this spec's own addition, so the test-side literal is the second witness and is what makes drift detectable at all (FR-019b, SC-003).
- [X] T030 [US1] [S1] Add the effort-ladder set-equality test to the unit module: read the route schema's effort enum and assert exact set equality against `low`, `medium`, `high`, `xhigh`, `max`, failing in both directions. Acceptance: this is the third closed enum in the same shipped schemas and it previously had none of the drift protection the two reason-code vocabularies receive, so a sixth member or a dropped member would have failed nothing; the second independent committed witness is the frozen successor-capability contract, so a test-side literal plus that contract is the pairing that makes drift detectable; `ultracode` is deliberately **not** a member because it is a session-level orchestration setting rather than a subagent effort level (FR-007a, SC-013).
- [X] T031 [US1] [S1] Add the out-of-vocabulary negative-validation test to the unit module: construct a diagnostic instance whose `code` falls outside **both** closed enums, together with the schema, **inline**, and assert it fails schema validation. Acceptance: the instance and schema are constructed inline and the test requires **no corpus case**, because the property is negative — an unrecognized code fails validation rather than passing through — and is therefore provable with zero cases; this is the requirement that makes declaring the policy-violation enum in slice 1 safe, since without it slice 1 would ship a closed vocabulary whose closure is unproven inside its own diff (FR-019a, SC-003).
- [X] T032 [US1] [S1] Add the out-of-range budget negative-validation test to the unit module: construct a declared-budget object exceeding the schema maximum **inline** and assert it fails validation rather than being clamped at run time. Acceptance: this is a **slice-1** obligation, not a slice-2 one — the negative proof travels with the `maximum` keyword it proves, by the same reasoning the enum-closure proof travels with the enum, and it proves *validation* rejects rather than proving behaviour; it is **not** a corpus case, because every corpus case must validate; the recorded honest cost is that slice 1 declares budget constraints it validates but does not yet enforce behaviourally, which is the lesser evil against making slice 2 reopen a slice-1 schema for a one-keyword change (FR-027, FR-003a).
- [X] T033 [US1] [S1] Add the corpus envelope assertions to the unit module, over the whole `cases[]` array: `case_id` values are unique with the count of distinct values equal to the count of cases; each `case_id` is a non-empty string, so no case is silently keyed by an empty value; every case carries its own `policy`, `snapshot`, `overrides` (explicitly `null` when the case declares none, never absent), and `expected_report`; and no case's payload names another case's `case_id`. Acceptance: these are asserted mechanically because the corpus has **no schema of its own** — exactly three schema documents are permitted and none validates the envelope — and both the append-only seam rule and the read-one-case guarantee depend on these properties; cross-slice stability is deliberately **not** claimed as mechanically enforced, because a case whose inputs and pinned report both moved would still replay consistently, so that half is review-borne (FR-015a, SC-007).
- [X] T034 [US1] [S1] Add the naming and fixture-hygiene assertions to the unit module: assert every agent name in the corpus carries the `fixture-` prefix, that no shipped agent name appears anywhere in the corpus with the roster derived **live** by listing `speckit-pro/agents/*.md` rather than transcribed into the test, that every policy agent's `role_class` is one of the three synthetic classes, and that the code-to-severity and code-to-actions mapping from data-model.md §3 holds over **every** emitted diagnostic — each code carries its one fixed severity and its `source` is the literal `route-fallback-simulator`. Acceptance: the prefix assertion is the **positive** rule and is what the corpus is held to, because the negative one alone goes stale — eleven agent definitions ship today and a twelfth is net-new in CAR-010, so a transcribed blocklist stops covering names added after it was written; severity is a function of `code`, which is a **deliberate divergence** from the installed runner whose severity is caller-determined, justified because this feature's emitter is a hand-authored corpus where leaving severity to the emitter would be unfalsifiable authoring latitude in a byte-compared corpus; no test method name and no authored file stem contains `car-005`, which the existing layout test enforces mechanically (FR-012c, FR-018, FR-032, SC-006, SC-013).
- [X] T035 [US1] [S1] Append **one** entry to the layer 4 `scripts[]` array in `tests/speckit-pro/suite-manifest.json` for the new module, matching the array's existing `{"path", "label", "baseline"}` shape and becoming the new tail after the current 62 entries. Acceptance: exactly one entry is added, which is what keeps the manifest out of slice 2's diff entirely — a second slice-2 entry would have to add a comma to slice 1's last line; `test-route-fallback-simulation` appears in `python3 tests/speckit-pro/run-all.py --layer 4` output and passes, so the module is dispatched through the suite rather than only runnable by hand (FR-032, FR-033a, SC-008).
- [X] T036 [US1] [S1] Regenerate the docs reference page with `pnpm --dir docs-site reference:generate` and verify with `pnpm --dir docs-site reference:check`. Acceptance: `docs-site/src/content/docs/reference/tests.md` is regenerated and committed, and `reference:check` exits clean — a stale page passes locally while failing CI's docs validation; the page is generated content and is not hand-edited.
- [X] T037 [US1] [S1] Run the full suite with `python3 tests/speckit-pro/run-all.py` and walk the slice-1 acceptance table in quickstart.md. Acceptance: zero failures; all nine cases replay byte-identically to their pinned reports and across two successive runs; the roadmap-parity assertion, the set-equality assertions on **all three** closed enums (resolution, policy-violation, effort ladder), both inline-negative assertions, and the corpus-envelope and severity assertions all pass; nothing under `speckit-pro/` changed; `tests/speckit-pro/layer6-efficiency/contracts/` is unchanged; nothing is stubbed and no deferral marker is left for slice 2 (FR-033b, SC-002, SC-003, SC-004, SC-005, SC-008, SC-012).

**Checkpoint**: User Story 1 is fully functional, independently testable, and
independently landable. The snapshot projection, report contract, and reason-code
vocabulary — the three artifacts CAR-006 needs first — can be adopted even if
slice 2 never lands.

---

## Phase 4: User Story 2 — Structural rejection and recovery semantics (Priority: P2) — Slice 2

**Goal**: Pin the defective-policy and degraded-environment cases — policies that
loop, substitute an unqualified adjacent model, substitute a generic agent, or
silently inherit an unpinned route; unqualified environment overrides on both
allowlist branches; an unavailable optional helper; and declared budgets that
exhaust deterministically into a report-only no-safe-route outcome carrying
rollback remediation.

**Independent Test**: Run the reference simulator over the nine
structural-rejection, override, helper, and exhaustion cases and assert each
produced report is byte-identical to that case's pinned expected report.

**Seam rule for every task in this phase**: The additive surface is exactly three
files — the simulator module, the corpus, and the unit test. **No schema file and
no manifest entry may appear in slice 2's diff.** Slice 2 adds new module
constants, new private helpers, and new public entry points, and changes **no**
slice-1 function signature. It appends corpus cases at the tail and appends test
functions; it never rewrites, reorders, renames, or re-pins anything slice 1
committed. If a finding here requires changing slice-1 content, the fix lands on
**slice 1's branch** and the chain restacks (FR-001, FR-033a, FR-033b).

### Structural rejections

- [ ] T038 [US2] [S2] RED→GREEN: add the structural-validation **pre-pass** to the simulator as a new private stage that runs to completion before the first route is attempted and suppresses the walk entirely when it emits any diagnostic. Acceptance: the pass covers **three** codes, not four — `unqualified_adjacent_model`, `generic_agent_substitution`, and `silent_inherit_materialization` are properties of the policy **document**, decidable with no walk state; `fallback_loop` is explicitly **not** in this pass; a pre-walk rejection produces a valid report with `attempted_routes` **empty**, `outcome: no_safe_route`, `unresolved_agent` set to the policy's own agent name, `effective_dispatch_tuple` absent unless an override is in force, all three actual counters at `0`, `optional_helper` in its not-consulted form, and `release_claim_eligible: false`; the array is empty **if and only if** the pre-walk pass rejected the policy (FR-019c, FR-024a).
- [ ] T039 [US2] [S2] RED→GREEN: implement `unqualified_adjacent_model` — a policy naming a fallback adjacent to a qualified route but not itself qualified is rejected and that fallback is never selected. Acceptance: the adjacency relation is read from the route's `adjacent_to` sibling reference; the diagnostic carries `details.route_id` naming the **declared** route, which by construction was never attempted; `severity` is `error` (FR-021, FR-029a).
- [ ] T040 [US2] [S2] RED→GREEN: implement `generic_agent_substitution` — a policy whose fallback replaces a named synthetic agent with a generic agent is rejected. Acceptance: the substitution is read from the route's `substituted_agent` object whose `class` is `generic`; the diagnostic carries `details.route_id`; `severity` is `error` (FR-022, FR-029a).
- [ ] T041 [US2] [S2] RED→GREEN: implement `silent_inherit_materialization` — a policy route omitting an explicit model or effort, such that the value would be materialized by inheritance, is rejected. Acceptance: the fixture is **admitted by the schema and rejected by the simulator**, which is why `resolved_model` and `effort` stay optional in the route definition; the diagnostic carries `details.route_id`; `severity` is `error` (FR-023, FR-003a, FR-029a).
- [ ] T042 [US2] [S2] RED→GREEN: implement `fallback_loop` detection **inside** the walk, at the point a route already attempted is reached, terminating the walk without repeating the revisited route. Acceptance: detection uses the walk state the module already owns, which is why structural validation is not a second module; the diagnostic is emitted **after** the last attempted route's entries in the whole-array ordering, because it is detected on reaching the revisit; it carries `details.route_id` matching an `attempted_routes` entry; `severity` is `error` (FR-020, FR-012b, FR-033d).
- [ ] T043 [US2] [S2] Append the four structural-rejection cases at the **tail** of `cases[]` in the corpus with fully pinned reports: `fallback-loop`, `unqualified-adjacent-model`, `generic-agent-substitution`, `silent-inherit-materialization`. Acceptance: the three pre-walk cases pin `attempted_routes: []`, all three actual counters at `0`, and `release_claim_eligible: false`; `fallback-loop` is the exception in that group and pins the routes attempted before the revisit without repeating the revisited route; at least one of these cases takes the bounded-analyst role class as its subject; no slice-1 case position or pinned byte changes (FR-018, FR-019c, FR-033b, FR-033c).

### Override and helper paths

- [ ] T044 [US2] [S2] RED→GREEN: implement the honored override branch — when the synthetic environment carries a subagent-model override whose target passes the organization allowlist, record the override as the effective dispatch tuple, emit an `unqualified_override` diagnostic when the override is unqualified, set `release_claim_eligible: false`, and record the qualified resolution that would have applied without the override. Acceptance: `outcome` follows the **qualified walk** and an override never promotes a `no_safe_route` outcome to `resolved`; the effective tuple is a **hybrid** — `alias` and `resolved_model` from the override's requested value, `agent` and `effort` retained from the route the qualified walk selected or from the preferred route when it selected none, because the variable sets a model only and no documented subagent-effort environment override exists; `override.would_have_been.effective_dispatch_tuple` is **omitted, never present as `null`**, when no qualified route resolved; `unqualified_override` carries **no** `details.route_id` branch because it is an environment condition scoped to no route; its `severity` is `warning` because dispatch proceeds under it, with the consequence carried by `release_claim_eligible` (FR-024, FR-024a, FR-012c, FR-019c).
- [ ] T045 [US2] [S2] RED→GREEN: implement the allowlist-skip branch — when the override's target resolves to a model the organization allowlist excludes, the override is **skipped** and MUST NOT be recorded as effective. Acceptance: `override.disposition` is `skipped_by_allowlist` and `override.tuple` is **absent**; the report records only that the override did not take effect and **deliberately does not name the model that runs instead**, because the documented fallback target is the *inherited* model, which this projection does not carry and MUST NOT gain — reading the skip as "resolution resumes at the per-invocation parameter" is inference and MUST NOT be encoded; this bounded negative claim is a **recorded decision, not an oversight**, and MUST NOT be "fixed" by adding a model field; `release_claim_eligible` is `false` on this branch too, for a reason independent of the override disqualifier; the allowlist gate is independent of this feature's own fixture-declared qualification, so an override can be unqualified yet permitted or qualified yet excluded; the `inherit` sentinel is modelled as the **no-override state** with `overrides: null`, not as an override (FR-024b, SC-013).
- [ ] T046 [US2] [S2] Append the two override cases at the tail of `cases[]` with fully pinned reports: `unqualified-override` against an allowlist that **permits** its target, so `disposition` is `honored`, `qualified` is `false`, the hybrid `tuple` is present, and the `unqualified_override` diagnostic is emitted; and `override-skipped-by-allowlist` against an allowlist that **excludes** its target, so `disposition` is `skipped_by_allowlist`, `tuple` is absent, and `effective_dispatch_tuple` follows the qualified walk. Acceptance: both carry `release_claim_eligible: false`; one case cannot cover both branches, and without the second the corpus would pin the unconditional override effect the documented runtime does not have (FR-024b, SC-001).
- [ ] T047 [US2] [S2] RED→GREEN: implement the helper-unavailable path over the policy's declared helper routes — when the helper's routes are unavailable the helper is not consulted, the report records continuation on the validated no-helper path, and required-agent resolution does not fail. Acceptance: continuation is recorded as the **structured `optional_helper` field, never as a diagnostic entry**, and neither closed enum gains a member for it, because helper unavailability is an environment condition rather than a policy-authoring defect; `probe_attempts` is an explicit `0` whenever `consulted` is `false`, which makes the non-consultation claim falsifiable rather than a self-asserted boolean; that counter is **disjoint** from `budgets.actual.probe_attempts`, which counts the reported agent's own walk; **no `attempted_routes` entry names a helper route** when `consulted` is `false`, which is the corroborating structural evidence a counter alone cannot supply; the two other reachable states are handled too — consulted-and-available, and no-helper-declared (FR-025, FR-025a, FR-025b).
- [ ] T048 [US2] [S2] Append `helper-unavailable-continues` at the tail of `cases[]` with its fully pinned report. Acceptance: this is the **one** case whose policy declares an `optional_helper`, carrying the root required agent plus the helper declaration whose `role_class` is the helper class; its snapshot marks the helper's route models unavailable; its pinned report carries `optional_helper` with `consulted: false`, `no_helper_path_validated: true`, `probe_attempts: 0`, no attempted-route entry naming a helper route, and a **resolved** outcome for the required agent, which is the second half of the requirement the case must also pin; the optional-helper role class is now the declared helper of at least one case, completing the three-role coverage claim (FR-018, FR-025, FR-025b).

### Budget exhaustion and no-safe-route recovery

- [ ] T049 [US2] [S2] RED→GREEN: implement declared budgets as **hard caps resolution never exceeds**, with the walk truncating at `max_candidate_routes` rather than continuing to the end of a longer fallback list, and the report recording the actual count alongside the declared cap for each of the three dimensions. Acceptance: all three counters are counted **over the reported agent's own walk** and never aggregated across cases or agents; `candidate_routes` equals `len(attempted_routes)` whenever the walk runs; `probe_attempts <= candidate_routes` holds because a route rejected before probing is reached raises the latter without raising the former; `retries` uses the **exclusive** base — re-attempts only, not total attempts — so `max_retries: 1` admits two consultations of one route, which is why that cap alone carries `minimum: 0` while its two siblings carry `minimum: 1`; all three exhaust into `no_safe_route` with **no new terminal code introduced** (FR-026, FR-026a).
- [ ] T050 [US2] [S2] RED→GREEN: implement `details.exhausted_budget` on the terminal `no_safe_route` diagnostic — an array listing every class whose actual count equals its declared cap, ordered by the enum's declaration order. Acceptance: it is present on that diagnostic and on **no other**, so its presence means "spent to the limit **and** the walk failed", which is exactly the conjunction a single counter comparison cannot express — a walk can legitimately reach a cap without failing because of it; it is **required only when at least one class is at cap and omitted, not empty, when none is**, since `minItems: 1` forbids the empty array and two reachable cases have a necessarily empty at-cap set (a pre-walk rejection fixing all counters at `0` against caps whose minimum is `1`, and a no-safe-route report arising from an empty fallback list); an **array** rather than a single naming of the terminating class is deliberate, because against a static snapshot no budget's exhaustion changes the result and none is causally privileged, so recording the at-cap set is deterministic by construction and needs no tie-break rule (FR-026a, SC-009).
- [ ] T051 [US2] [S2] RED→GREEN: implement the report-only no-safe-route outcome — naming the unresolved agent, every attempted route, each rejection reason, and remediation whose `actions` include `Roll back to the previous plugin release.` **verbatim** — and confirm the simulator neither reads a shipped agent file for mutation nor writes one. Acceptance: the obligations attach to the **outcome**, not to the stated precondition, so they apply to any report whose `outcome` is `no_safe_route` however the walk ended — every fallback rejected, an empty fallback list, a cap reached, or a pre-walk rejection; the two arrays are **joinable** rather than merely co-present, because every diagnostic concerning a specific route carries `details.route_id` and positional association is impossible when a variable number of diagnostics is emitted per route; the rollback action appears **only** on the terminal entry, which also carries the summary remediation, so per-route entries are not inflated toward the three-action truncation boundary; exactly one terminal entry exists and it is the final element of the array (FR-029, FR-029a, FR-012a, FR-012b, SC-010).
- [ ] T052 [US2] [S2] Append `budget-exhaustion-of-one` at the tail of `cases[]` with its fully pinned report. Acceptance: it binds the **retry** class specifically, because the roadmap states retry exhaustion as its own proof obligation while the requirement's parent sentence and the acceptance scenario both allow "a probe or retry budget", a disjunction a probe-only case would satisfy while leaving retries unproven; it declares all three budgets at `1` and pins all three actual counts; its preferred route's exact-invocation outcome is `failure`, the one permitted retry re-consults it and returns the same `failure`, and no further retry may be taken; `details.exhausted_budget` lists all three classes in enum declaration order; all three declared values satisfy the schema bounds so the case validates; recorded honestly, no case makes probe-attempt or candidate-route exhaustion the *sole* at-cap class, which is acceptable because one shared cap check governs all three dimensions (FR-028, FR-026a, SC-009).
- [ ] T053 [US2] [S2] Append `no-safe-route-report-only` at the tail of `cases[]` with its fully pinned report, completing the corpus at **eighteen** cases. Acceptance: the report names the unresolved agent, carries every attempted route with `disposition: rejected`, carries one diagnostic per failed check joined to its route by `details.route_id`, carries `release_claim_eligible: false`, and carries the terminal `no_safe_route` entry last with the verbatim rollback action among its two actions and `severity: error`; no slice-1 case position or pinned byte changed anywhere in this phase (FR-029, FR-033b, SC-010).
- [ ] T054 [US2] [S2] Append the scenario-coverage test to the unit module, asserting that every scenario the roadmap mandates is represented by at least one of the eighteen cases with **zero** unrepresented: preferred model absent including the `fable` case, alias unresolved, effort unsupported, probe unavailable, exact-invocation probe success, exact-invocation probe failure, alias re-pointing, platform route change, unqualified override, override skipped by the organization allowlist, fallback loop, unqualified adjacent model, generic-agent substitution, silent inherit materialization, helper unavailable, retry exhaustion, and no safe route. Acceptance: exhaustion is named by its **terminating class** rather than as generic budget exhaustion; the override-skipped family is included even though it is this spec's own addition rather than a roadmap-named one; the corpus holds exactly 18 cases, 9 from slice 1 and 9 appended here (SC-001).
- [ ] T055 [US2] [S2] Verify slice-2 additivity against slice 1's branch with `git diff --stat` and a per-file `git diff` on the corpus. Acceptance: exactly **three** authored files appear in the diff — the simulator module, the corpus, and the unit test — plus the regenerated docs reference page; **no schema file and no `suite-manifest.json` appears**, or the seam is broken; the corpus diff is additions only, all at the tail of `cases[]`, with no slice-1 `case_id`, input, or pinned expected report changed; no slice-1 function signature changed; cross-slice stability of slice-1 cases is confirmed by **this diff review**, not by the replay test, which cannot detect a case whose inputs and pinned report both moved (FR-001, FR-033a, FR-033b, quickstart.md §Slice 2).
- [ ] T056 [US2] [S2] Regenerate the docs reference page with `pnpm --dir docs-site reference:generate` and verify with `pnpm --dir docs-site reference:check`. Acceptance: `docs-site/src/content/docs/reference/tests.md` is regenerated and committed and `reference:check` exits clean; the page is generated content and is not hand-edited.
- [ ] T057 [US2] [S2] Run the full suite with `python3 tests/speckit-pro/run-all.py` and walk the slice-2 acceptance table in quickstart.md. Acceptance: zero failures; all eighteen cases replay byte-identically to their pinned reports and across two successive runs; the budget-of-one case never exceeds its declared caps; the no-safe-route case is report-only with the verbatim rollback action; helper unavailability is the structured field rather than a diagnostic; both override branches behave as contracted; `test-policy-control-contracts` and the layout test still pass (SC-002, SC-008, SC-009, SC-010).

**Checkpoint**: Both user stories are independently functional. CAR-006 and the
cohort specs inherit proven rejection semantics.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Per-slice boundary audits, quickstart validation, and the PR review
packet each slice's pull request carries. There is no code cleanup, performance,
or security-hardening work here — the surface is a test harness with zero
production files and no runtime.

- [ ] T058 [P] [S1] Audit the slice-1 non-goal boundaries and record the evidence: the count of production files changed is zero and nothing under `speckit-pro/` appears in the diff; the count of frozen CAR-002, CAR-003, and CAR-004 schemas or fixtures modified is zero; the count of members added to `tests/speckit-pro/layer6-efficiency/contracts/` is zero; the count of Codex-side files changed is zero; the count of fixture agent names matching the roster listed live from `speckit-pro/agents/` is zero, and the count of fixture agent names missing the `fixture-` prefix is likewise zero; no live model call and no dispatch occurs anywhere in the module; no production resolver was written. Acceptance: all seven counts are zero and each is evidenced by a command whose output is recorded; the roadmap edit is the one declared modification outside the test tree and is expected in this diff (FR-030, FR-031, FR-033a, SC-004, SC-005, SC-006, SC-012).
- [ ] T059 [P] [S1] Walk `specs/car-005-availability-fallback-recovery/quickstart.md` end to end for slice 1, including the manual determinism spot-check that resolves each case twice and compares against the pinned report independently of the test's own assertion. Acceptance: the spot-check reports no mismatches; a `a != b` result indicates non-determinism from a timestamp, randomness, or dict-order dependence, and a `a == b != pinned` result means the pinned report disagrees with the simulator and which one is wrong must be decided before either is edited.
- [ ] T060 [S1] Generate the slice-1 pull-request review packet covering what changed, why, non-goals, review order, scope budget, traceability mapping each major requirement and success criterion to changed files and verification evidence, verification evidence, known gaps, and rollback notes; state the PR's position as the base of the stacked chain. Acceptance: the traceability section maps every requirement this slice satisfies to a changed file and a passing assertion; the recorded deviation on the action-enum placement is carried as a known deviation rather than omitted; the exact final title validates against the live release-readiness gate in `<type>(<lowercase-scope>): <plain English description>` form; the body carries exactly one non-empty release-note fence.
- [ ] T061 [P] [S2] Audit the slice-2 non-goal boundaries with the same seven zero-counts as T058, plus the seam counts: zero schema files changed and zero manifest entries changed in slice 2's diff. Acceptance: all nine counts are zero and each is evidenced by a recorded command output (FR-030, FR-031, FR-033a, FR-033b, SC-004, SC-005, SC-006, SC-012).
- [ ] T062 [P] [S2] Walk `specs/car-005-availability-fallback-recovery/quickstart.md` end to end for slice 2, including the manual determinism spot-check across all eighteen cases and both slice-2-specific diff checks. Acceptance: the spot-check reports no mismatches across eighteen cases; the additivity and slice-1-untouched diffs are both clean.
- [ ] T063 [S2] Generate the slice-2 pull-request review packet with the same nine sections, stating its position in the stacked chain and **naming slice 1 as its base**, and emit the two pull requests as a `gh-stack` chain with slice 2 based on slice 1. Acceptance: both slices pass the pull-request-time diff-mode reviewability gate on their own diff; slice 2's PR names slice 1 as its base; the exact final title validates against the live release-readiness gate; the body carries exactly one non-empty release-note fence; the named follow-up for the cross-platform mirroring obligation is recorded as G56R-005 (SC-011).

---

## Slice Partition

Every one of the 63 tasks carries an explicit `[S1]` or `[S2]` label. No task is
unassigned.

| Slice | Tasks | Count | Pull request |
| --- | --- | --- | --- |
| **Slice 1** (User Story 1) | T001–T037, T058–T060 | **40** | First PR, base of the chain |
| **Slice 2** (User Story 2) | T038–T057, T061–T063 | **23** | Second PR, based on slice 1 |

**File-level allocation the partition enforces** (FR-033a):

| File | Slice 1 | Slice 2 |
| --- | --- | --- |
| `contracts-claude/route-policy.schema.json` | create (T006) | untouched |
| `contracts-claude/environment-snapshot-projection.schema.json` | create (T007) | untouched |
| `contracts-claude/route-resolution-report.schema.json` | create (T008–T010) | **untouched** |
| `lib/claude_route_fallback.py` | create (T012–T021) | extend additively (T038–T042, T044–T045, T047, T049–T051) |
| `fixtures-fallback/fallback-scenario-corpus.json` | create, 9 cases (T022–T025) | append 9 at the tail (T043, T046, T048, T052–T053) |
| `unit/test-route-fallback-simulation.py` | create (T005, T013, T026–T034) | append test functions (T054) |
| `suite-manifest.json` | modify, one layer-4 entry (T035) | **untouched** |
| `docs/ai/specs/claude-agent-routing-technical-roadmap.md` | modify — status line, progress row, Grounded Platform Facts (PF-1…PF-4), and the two dated scope amendments (landed during the planning phases; audited by T058) | **untouched** |
| `docs-site/src/content/docs/reference/tests.md` | regenerate (T036) | regenerate (T056) |

Nine declared entries, matching FR-033a and plan.md §Declared File Operations:
six created, two modified, one regenerated. Corpus totals: **18 cases — 9 in slice
1, 9 in slice 2.** Registered test modules: **exactly one**, in slice 1.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately.
- **Foundational (Phase 2)**: Depends on Setup. **Blocks both user stories** — all
  three contracts and the serialization surface must exist first.
- **User Story 1 (Phase 3)**: Depends on Foundational. Independently landable and
  releasable on completion.
- **User Story 2 (Phase 4)**: Depends on User Story 1 being **complete and
  merged-or-stacked**, not merely on Foundational. This is the one place this
  feature departs from the template's default independence: the slices are a
  stacked chain by requirement, so slice 2's diff is measured against slice 1's
  branch.
- **Polish (Phase 5)**: The slice-1 polish tasks depend on Phase 3; the slice-2
  polish tasks depend on Phase 4.

### Dependency chain within the feature

Schemas (T006–T010) → simulator core (T012, T014) → resolution codes and
sub-reasons (T015–T021) → corpus cases (T022–T025) → replay pinning and the
slice-1 assertion obligations (T013, T026–T034) → manifest registration and docs
(T035–T036) → slice-1 gate (T037) → structural rejections (T038–T043) → override
and helper paths (T044–T048) → budget exhaustion and no-safe-route recovery
(T049–T053) → scenario-coverage and seam verification (T054–T055) → slice-2 gate
(T057).

Note that manifest registration lands in **slice 1** rather than at the end of the
whole feature, because slice 2 must leave the manifest untouched. Within slice 1
it comes after the test module exists and after the slice-1 assertions pass, so
the module is dispatched through the suite for the slice-1 gate.

### Within Each User Story

- Tests are written and confirmed FAILING before the implementation that makes
  them pass.
- Contracts before the simulator; the simulator before the corpus; the corpus
  before replay pinning.
- Both staged call graphs — the sub-reason order and the diagnostic-emission
  order — are structural before any case that depends on them is pinned, because
  a case pinned against an unstaged order fails later with a stated cause that
  looks unrelated to how the snapshot was built.
- Story complete and gated before moving to the next slice.

### Parallel Opportunities

Genuinely parallel work is scarce here and the task list does not pretend
otherwise. Slice 1 has one simulator module, one corpus file, and one test module,
so every task touching any of them is serialized on a shared file — two tasks
appending to the same corpus or the same test module are **not** parallel-safe.

The four real opportunities, covering all 9 `[P]` tasks:

- **T002 and T003** — different surfaces, both read-only or dependency-local.
- **T006, T007, and T008** — three distinct schema files with no shared state.
- **T058 and T059** — independent read-only slice-1 audits.
- **T061 and T062** — independent read-only slice-2 audits.

Everything else is sequential. Total `[P]` tasks: **9**.

---

## Parallel Example: Foundational Schemas

The three contract documents are the only implementation tasks in this feature
that can run concurrently. User Story 1 and User Story 2 have **no** parallel
tasks at all, because each story's work converges on the same three files.

```bash
# Launch the three schema-authoring tasks together:
Task: "Author route-policy.schema.json in tests/speckit-pro/layer6-efficiency/contracts-claude/"
Task: "Author environment-snapshot-projection.schema.json in tests/speckit-pro/layer6-efficiency/contracts-claude/"
Task: "Author the root of route-resolution-report.schema.json in tests/speckit-pro/layer6-efficiency/contracts-claude/"

# Then serialize: T009 and T010 both extend the report schema T008 created.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational — all three contracts land complete.
3. Complete Phase 3: User Story 1.
4. **STOP and VALIDATE**: run the full suite and walk the slice-1 acceptance
   table. Slice 1 must be complete and passing **alone**, with nothing stubbed
   and no deferral marker left for slice 2.
5. Open slice 1's pull request. It is independently releasable and is the artifact
   CAR-006 needs first — the snapshot projection, the report contract, and the
   reason-code vocabulary can all be adopted even if slice 2 never lands.

### Incremental Delivery

1. Setup plus Foundational → all three contracts complete and keyword-verified.
2. Add User Story 1 → nine cases replaying byte-identically → slice 1 PR (MVP).
3. Add User Story 2 → eighteen cases replaying byte-identically → slice 2 PR,
   stacked on slice 1.
4. Each slice adds value without breaking the previous one, and slice 2 adds no
   new authored file.

### Restack Rule

If a slice-2 finding requires changing slice-1 content, that is evidence the
slice-1 contract was wrong. The fix lands on **slice 1's branch** and the chain
restacks. It is never absorbed into slice 2's diff.

### Parallel Team Strategy

Limited by design. Two developers can split the Foundational schemas (T006, T007,
T008). After that the work converges on three shared files and is best carried by
one developer per slice, with slice 2 waiting on slice 1's gate rather than
running concurrently.

---

## Requirement Coverage

Every one of the 60 functional-requirement identifiers in `spec.md` maps to at
least one task.

| Requirement | Tasks |
| --- | --- |
| FR-001 | T012, T014, T038, T055 |
| FR-002 | T007 |
| FR-002a | T007, T017 |
| FR-003 | T006 |
| FR-003a | T006, T026, T041 |
| FR-004 | T014 |
| FR-005 | T009, T019, T028 |
| FR-006 | T015, T023 |
| FR-007 | T016, T024 |
| FR-007a | T006, T016, T030 |
| FR-008 | T017, T024 |
| FR-009 | T018, T024 |
| FR-010 | T022 |
| FR-011 | T020, T025 |
| FR-012 | T009, T015 |
| FR-012a | T010, T024, T051 |
| FR-012b | T019, T042, T051 |
| FR-012c | T009, T024, T034, T044 |
| FR-013 | T008, T020, T025 |
| FR-013a | T008 |
| FR-014 | T013, T027 |
| FR-014a | T003, T012, T027 |
| FR-015 | T022 |
| FR-015a | T033 |
| FR-016 | T006, T007, T008, T009, T011 |
| FR-016a | T006, T007, T009, T010 |
| FR-017 | T028 |
| FR-017a | T028 |
| FR-017b | T028 |
| FR-017c | T028, T058 |
| FR-018 | T022, T025, T034, T043, T048 |
| FR-019 | T009, T029 |
| FR-019a | T031 |
| FR-019b | T029 |
| FR-019c | T038, T043, T044 |
| FR-020 | T042 |
| FR-021 | T039 |
| FR-022 | T040 |
| FR-023 | T041 |
| FR-024 | T044, T046 |
| FR-024a | T021, T038, T044 |
| FR-024b | T045, T046 |
| FR-025 | T047, T048 |
| FR-025a | T021, T047 |
| FR-025b | T006, T047, T048 |
| FR-026 | T049 |
| FR-026a | T010, T021, T049, T050, T052 |
| FR-027 | T006, T032 |
| FR-028 | T052 |
| FR-029 | T051, T053 |
| FR-029a | T009, T039, T040, T041, T042, T051 |
| FR-030 | T012, T058, T061 |
| FR-031 | T058, T061 |
| FR-032 | T005, T012, T034, T035 |
| FR-032a | T011 |
| FR-033 | T004, T063 |
| FR-033a | T004, T035, T055, T058 |
| FR-033b | T004, T037, T043, T053, T055 |
| FR-033c | T022, T043 |
| FR-033d | T012, T042 |

Success criteria coverage: SC-001 (T054), SC-002 (T013, T027, T037, T057),
SC-003 (T026, T029, T031), SC-004 (T058, T061), SC-005 (T058, T061),
SC-006 (T022, T034, T058), SC-007 (T033), SC-008 (T035, T037, T057),
SC-009 (T050, T052), SC-010 (T051, T053), SC-011 (T063),
SC-012 (T028, T037, T058), SC-013 (T016, T030, T034, T045).

---

## Non-Goal Boundaries

No task in this list crosses any of the design concept's non-goal boundaries. The
boundaries and the tasks that audit them:

| Non-goal | Enforcement |
| --- | --- |
| No production resolver | Zero tasks touch `speckit-pro/`; the simulator is an executable specification that CAR-006 re-proves against, not code CAR-006 inherits. Audited by T058, T061. |
| No real-agent-name fixtures | All fixture agents are drawn from the three-role synthetic cast. Asserted by T034, audited by T058. |
| No shared `contracts/` members | All three schemas land in `contracts-claude/`, which is platform-scoped rather than a mirrored twin. Audited by T058, T061. |
| No live dispatch | The simulator is a pure function with no filesystem, network, wall-clock, or randomness input. Enforced by T012, T014; audited by T058, T061. |
| No CAR-002/003/004 schema edits | Those schemas are imported read-only or cited, never modified. Audited by T058, T061. |
| No Codex-side edits | The cross-platform divergence is pinned as test data rather than reconciled. Enforced by T028; audited by T058, T061. |

Three **deliberate divergences** appear in the task list and MUST NOT be "fixed":
the preflight rejection of an unsupported effort where the documented runtime
silently degrades (T016), the allowlist-skip branch's refusal to name the
model that runs instead (T045), and `severity` being a function of `code` where the
installed runner leaves it caller-determined (T034). All three are recorded
decisions carried in the requirements, not oversights.

---

## Notes

- `[P]` tasks are different files with no shared state. Two tasks appending to the
  same corpus file, the same simulator module, or the same test module are not
  parallel-safe, which is why only 9 of 63 tasks carry the marker.
- `[S1]`/`[S2]` is present on every task and is what the orchestrator reads to
  emit the two stacked pull requests. An unassigned task would block PR emission.
- Five tasks carry **no** functional-requirement citation, deliberately: T002
  (worktree dependency install), T036 and T056 (regenerating the generated docs
  reference page), and T059 and T062 (walking the quickstart). They serve declared
  file operations and validation rather than a requirement, so their absence from
  the Requirement Coverage table is correct, not a coverage gap. All 63 tasks are
  still accounted for by slice in the Slice Partition ranges.
- `[US1]`/`[US2]` maps a task to its user story; because the seam is the
  story boundary, the story label and the slice label agree wherever both appear.
- Verify each test FAILS before writing the implementation that makes it pass.
- Commit after each task or logical group.
- Stop at either checkpoint to validate that slice independently.
- No task runs a typechecker or a linter, because this repository has neither.
- Any task that changes a tracked `.py` file under `tests/speckit-pro/` obliges
  the docs reference regeneration in T036 or T056 before the slice is called done.
- Avoid: vague tasks, same-file conflicts marked `[P]`, and cross-slice
  dependencies that would force slice-1 churn.
- Avoid: expanding this task list past the reviewability budget instead of
  splitting the spec. The split is already elected at two slices and only an
  operator decision moves it.
