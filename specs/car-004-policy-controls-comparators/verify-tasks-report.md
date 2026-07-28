# Verify Tasks Report: CAR-004 Policy Controls and Adaptive Comparators

**Date**: 2026-07-28
**Scope**: `all` (base `origin/main` to HEAD, plus uncommitted and untracked)
**Tasks assessed**: 63 completed `[X]`; 1 unchecked `[ ]` (T062, out of assessment scope)
**Base ref**: `origin/main` — 9 commits behind HEAD, 33 changed files

> **FRESH SESSION ADVISORY**: This run executed in a separate agent session from the one
> that performed `/speckit.implement`.

---

## Summary Scorecard

| Verdict | Count |
|---|---|
| VERIFIED | 63 |
| PARTIAL | 0 |
| WEAK | 0 |
| NOT_FOUND | 0 |
| SKIPPED | 0 |

**No phantom completions detected.**

---

## Flagged Items

None.

---

## Evidence Base

### Layer 1 — File existence

All 15 declared file operations exist. No path in any completed task is missing.

### Layer 2 — Git diff cross-reference

All 15 declared files appear in the `origin/main...HEAD` change set (33 files total).

### Layer 3 — Content pattern matching

Every symbol named in a GREEN task is defined at a real definition site:

| Task | Symbols | Location |
|---|---|---|
| T012 | `ControlContractError`, `load_contract`, `validate_instance` | `claude_policy_controls.py:84,93,108` |
| T014 | `control_digest`, `validate_registry`, `assert_closed_at_three`, `load_registry` | `:316,377,326,1537` |
| T016 | `verify_car_003_bindings` | `:433` |
| T018 | `validate_unpinned_control` | `:519` |
| T020 | `validate_signal_maps`, `resolve_response` | `:649,718` |
| T022 | `validate_escalation_ladder`, `next_route`, `previous_route` | `:783,870,877` |
| T024 | `advance_clean_streak` | `:914` |
| T026 | `evaluate_bounds`, `classify_service_reroute` | `:977,1056` |
| T028 | `aggregate_objective`, `worst_terminal_state` | `:1405,1170` |
| T030 | `unit_members`, `validate_orchestration_control` | `:1293,1191` |
| T032 | `aggregate_raw_tokens_and_cache` | `:1465` |
| T034 | `ControlComparisonError`, `load_comparison`, `validate_comparison`, `project_resource_vector`, `check_eligibility_floors` | `claude_control_comparison.py:53,387,370,400,433` |
| T036 | `pareto_verdict`, `materiality_filter`, `compare` | `:489,548,603` |
| T038 | `claim_class` | `:645` |
| T044 | `replay` | `claude_policy_controls.py:1874` |
| T047 | `assert_reserved_partition_untouched` | `:1686` |
| T049 | `validate_smoke_record` | `:2083` |
| T051 | `evaluate_demonstration`, `evaluate_cache_isolation` | `:2294,2404` |

### Layer 4 — Dead-code detection

44 public symbols scanned across both new modules. **Zero dead symbols.**

Two symbols carry no external caller and were individually cleared as internally wired:

- `document_bytes_digest` — called at `claude_policy_controls.py:453` and `:544`, exported at `:2569`.
- `validate_control_specializations` — called from `validate_registry` at `:393`, exported at `:2584`.

The remaining 42 are referenced from the unit tests or `run-control-smoke.py`.

### Layer 5 — Semantic assessment

Interpretive, and positive on every task.

- **No stubs.** Zero `TODO`, `FIXME`, `NotImplementedError`, or placeholder bodies across the
  six new Python files. The single bare `pass` (`claude_policy_controls.py:299`) is the
  deliberate bool branch of the JSON-Schema type dispatcher, guarding against
  `isinstance(True, int)` falling through to numeric validation.
- **Test density is real**: 342 test methods and 616 assertions across the three new modules.
- **Mutation-proven binding to committed bytes.** Two seeded mutations were applied to the
  committed registry fixture and reverted:
  - Frozen numeric `smoke_bounds.max_attempts.value` 5 to 6: 21 assertions failed.
  - `frozen_at` timestamp only, no other change: 21 assertions failed, confirming T013's
    claim that the timestamp sits inside the digest preimage so a timestamp-only edit moves
    the address.

  Both restored; the tracked tree is byte-identical to its pre-verification state.
- **Stdlib-only confirmed** (T012, T055): imports resolve to the standard library plus
  sibling repository modules. No `jsonschema`, no third-party package, no new Bash or `jq`
  dependency.
- **Frozen sources read live, not transcribed** (T014, T020, T026, T030, T051):
  `canonical_json`/`record_digest` from `claude_successor_freeze`, `failure_plane_for` from
  `claude_score_bundle`, `build_partition_registry_entry`/`register_partitions` from
  `claude_experiment_policy`.

### Suite execution

| Layer | Result |
|---|---|
| L1 structural | 1428/1428 |
| L4 unit | 3295/3295 |
| L5 | 186 (per workflow record) |
| **Total** | **4909** |

New modules within L4: `test-policy-control-contracts` 518/518,
`test-control-comparison-dominance` 125/125, `test-twin-handoff-completeness` 26/26.

### Re-executed verification tasks

| Task | Re-run result |
|---|---|
| T003 | `.gitignore` carries `results/*` wholesale plus exactly one allow-rule, `!results/consolidated-baseline.json` |
| T006 | Three `{path,label,baseline}` entries at `suite-manifest.json:122-124` |
| T040 | Both entries present, both `owning_spec: "CAR-004"`; reserved is `integrated_confirmation`/eligible, smoke is `calibration`/not eligible |
| T041 | All seven required members present; alpha 0.05, confidence 0.95, cluster-robust sandwich by role, Holm-Bonferroni within the secondary control-arm family |
| T042 | Nine cases; cases 7-8 are the two bound-breach paths, case 9 is the streak surviving an excluded non-scorable objective; multi-child orchestration case present |
| T052/T053 | Driver loaded by `importlib` at `test-policy-control-contracts.py:3084-3097`; 12 methods cover `--plan` and `--seal`; `:3240` asserts the driver is absent from the manifest |
| T059 | All six new files present in the generated docs reference page |
| T060 | `contracts-claude/` exactly 2 `A` and 0 `M`; `lib/` exactly 2 `A` and 0 `M`; `results/` untracked and uncommitted |
| T063 | Packet present; validation `status: passed`, `exit_code: 0`; title `feat(car-004): add the three routing policy controls and their comparison rules` |

---

## Verified Items

| Task | Verdict | Summary |
|---|---|---|
| T001 | VERIFIED | Green baseline; L1 and L4 re-run green this session |
| T002 | VERIFIED | Fixture directory holds four fixtures, no placeholder |
| T003 | VERIFIED | `.gitignore` matches the described wholesale-plus-one-allow shape |
| T004 | VERIFIED | Budget and no-split decision recorded in `plan.md:236-250` |
| T005 | VERIFIED | Three importable modules, all registered and passing |
| T006 | VERIFIED | Three manifest entries at `suite-manifest.json:122-124` |
| T007-T010 | VERIFIED | Both schema documents authored; shape assertions present and passing |
| T011-T016 | VERIFIED | Schema engine, content addressing, CAR-003 binding verifier all wired |
| T017-T032 | VERIFIED | Per-control validators all defined, called from tests, mutation-sensitive |
| T033-T038 | VERIFIED | Comparison validator, Pareto, materiality, claim class all wired |
| T039-T045 | VERIFIED | Four fixtures authored; committed-instance conformance proven by mutation |
| T046-T047 | VERIFIED | Reserved-partition guard defined and exercised |
| T048-T053 | VERIFIED | Smoke record validation and the unregistered operator driver both covered |
| T054-T057 | VERIFIED | Twin-handoff record carries categories 1-8, divergences, empty reconciliation list |
| T058 | VERIFIED | Full gate; L1 1428 + L4 3295 + L5 186 = 4909 |
| T059 | VERIFIED | Docs reference regenerated and committed |
| T060 | VERIFIED | Additive-only discipline re-confirmed from the change set |
| T061 | VERIFIED | Quickstart sections 1-4 walk clean; section 3 table matches observed L4 results |
| T063 | VERIFIED | PR packet generated; title validated against the release-readiness gate |
| T064 | VERIFIED | Reviewability result recorded in `plan.md:157-177` with its fallback chain |

---

## Unassessable Items

None.

---

## Note on T062

T062 is correctly left `[ ]`. It is the three developer-local live smokes, which require an
operator on a subscription authentication path and are explicitly never run in CI. Its
unmarked state is accurate bookkeeping, not an omission, and it is not a phantom.

## Note on T064

T064's plan.md entry honestly records that diff mode is **deferred** on the authoritative
read-only runner rather than claiming a diff-mode pass. That refusal was independently
confirmed in source: `speckit-pro/speckit_pro_runner/helpers/read_only.py:851-852` returns
exit code 2 with the exact string the plan quotes for any mode other than `setup`. The task
deliverable — recording the result — exists and is truthful. Any downstream reviewability
diff-gate step will meet the same documented refusal.

---

## Machine-Parseable Verdicts

| T001 | VERIFIED | Baseline green, re-verified |
| T002 | VERIFIED | Fixture directory populated |
| T003 | VERIFIED | gitignore shape confirmed |
| T004 | VERIFIED | Split decision recorded |
| T005 | VERIFIED | Three modules importable |
| T006 | VERIFIED | Manifest entries present |
| T007 | VERIFIED | Registry shape assertions present |
| T008 | VERIFIED | Registry schema authored |
| T009 | VERIFIED | Comparison shape assertions present |
| T010 | VERIFIED | Comparison schema authored |
| T011 | VERIFIED | Fail-closed engine assertions present |
| T012 | VERIFIED | Engine implemented, stdlib only |
| T013 | VERIFIED | Identity assertions mutation-proven |
| T014 | VERIFIED | Digest and closure implemented |
| T015 | VERIFIED | Binding assertions present |
| T016 | VERIFIED | Binding verifier wired |
| T017 | VERIFIED | Unpinned assertions present |
| T018 | VERIFIED | Unpinned rules implemented |
| T019 | VERIFIED | Signal-map assertions present |
| T020 | VERIFIED | Signal maps read live from frozen enums |
| T021 | VERIFIED | Ladder assertions present |
| T022 | VERIFIED | Ladder navigation implemented |
| T023 | VERIFIED | Streak assertions present |
| T024 | VERIFIED | Streak accounting implemented |
| T025 | VERIFIED | Bound and reroute assertions present |
| T026 | VERIFIED | Bounds and reroute implemented |
| T027 | VERIFIED | Aggregate assertions present |
| T028 | VERIFIED | Aggregation implemented |
| T029 | VERIFIED | Unit topology assertions present |
| T030 | VERIFIED | Unit membership implemented |
| T031 | VERIFIED | Raw-token and cache assertions present |
| T032 | VERIFIED | Token and cache aggregation implemented |
| T033 | VERIFIED | Projection and eligibility assertions present |
| T034 | VERIFIED | Comparison loader implemented, engine reused |
| T035 | VERIFIED | Dominance assertions present |
| T036 | VERIFIED | Pareto and materiality implemented |
| T037 | VERIFIED | Messaging assertions present |
| T038 | VERIFIED | Claim class implemented |
| T039 | VERIFIED | Registry instance frozen with recorded digests |
| T040 | VERIFIED | Both partition entries frozen |
| T041 | VERIFIED | Comparison instance frozen |
| T042 | VERIFIED | Nine replay cases including both breach paths |
| T043 | VERIFIED | Replay assertions present |
| T044 | VERIFIED | Replay implemented |
| T045 | VERIFIED | Committed-instance conformance mutation-proven |
| T046 | VERIFIED | Partition guard assertions present |
| T047 | VERIFIED | Partition guard implemented |
| T048 | VERIFIED | Smoke record assertions present |
| T049 | VERIFIED | Smoke record validation implemented |
| T050 | VERIFIED | Demonstration and isolation assertions present |
| T051 | VERIFIED | Demonstration and isolation implemented |
| T052 | VERIFIED | Driver assertions present, driver imported |
| T053 | VERIFIED | Driver authored, deliberately unregistered |
| T054 | VERIFIED | Completeness assertions present |
| T055 | VERIFIED | Both-directions diff implemented |
| T056 | VERIFIED | Twin-handoff categories 1-6 authored |
| T057 | VERIFIED | Categories 7-8 and closing sections authored |
| T058 | VERIFIED | Full gate 4909 passing |
| T059 | VERIFIED | Docs reference regenerated |
| T060 | VERIFIED | Additive-only confirmed |
| T061 | VERIFIED | Quickstart 1-4 clean |
| T063 | VERIFIED | PR packet validated |
| T064 | VERIFIED | Reviewability recorded with fallback chain |

## Walkthrough Log

No flagged items. No walkthrough was required.
