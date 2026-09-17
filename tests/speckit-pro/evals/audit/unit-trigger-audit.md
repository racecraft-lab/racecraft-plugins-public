# Layer 4 unit-trigger substantive audit

## Summary

- Frozen membership: 10 registered `unit/test-trigger-*.py` executables and 159 loaded case families from `deterministic-inventory.json`.
- Review completion: 159 reviewed, 0 unreviewed.
- Dispositions: 157 keep, 0 merge, 2 replace, 0 remove.
- Coverage character: 60 implementation, 69 adapter, 21 parser, and 9 declaration families.
- This was a provider-free source and boundary audit. It did not launch Claude or Codex and did not run a campaign.

The exhaustive family ledger is `unit-trigger-audit.json`. Each entry records the exact symbol, source line, body SHA-256, file SHA-256, requirement, failure mode, exercised boundary, observed assertions/callees/patches/parameters, disposition, and any replacement.

## Frozen scope

The inventory snapshot was captured at `2026-09-15T17:00:57Z` from Git head `e1536a7a2f4b9b54fc88d357d01c4d8ea5fe46e6` with a dirty worktree. Every current source hash in this lane still matched its frozen inventory hash during this audit.

| Executable | Families | Disposition | Coverage | Frozen source SHA-256 prefix |
| --- | ---: | --- | --- | --- |
| `test-trigger-eval-runners.py` | 36 | 34 keep, 2 replace | 25 adapter, 11 parser | `5b1362347ffa` |
| `test-trigger-trial-records.py` | 3 | 3 keep | 3 implementation | `153a87e568a6` |
| `test-trigger-signal-restoration.py` | 3 | 3 keep | 3 adapter | `d9cce222d014` |
| `test-trigger-eval-coverage.py` | 3 | 3 keep | 3 declaration | `1818e30ad0bd` |
| `test-trigger-inventory.py` | 19 | 19 keep | 15 implementation, 4 declaration | `95d1e00dafe8` |
| `test-trigger-comparison.py` | 13 | 13 keep | 3 implementation, 10 parser | `511ecafc2615` |
| `test-trigger-campaign.py` | 16 | 16 keep | 16 implementation | `7822121fb346` |
| `test-trigger-campaign-execution.py` | 36 | 36 keep | 36 adapter | `eda31cbf7398` |
| `test-trigger-carry-forward.py` | 27 | 27 keep | 23 implementation, 4 adapter | `42e1b8a5d084` |
| `test-trigger-controlled-description.py` | 3 | 3 keep | 2 declaration, 1 adapter | `620a3e07312c` |

## Replacement findings

### Replace `Layer2TriggerRunnerTests.test_claude_direct_runner_contracts`

This 656-line family combines launch/preflight, stream parsing and usage, evidence retention, cleanup/timeout, environment, CLI pinning, and policy cases. Ripwire reports structural complexity 55 and cognitive complexity 27. Its final dictionary-of-checks assertion makes a failure hard to localize and lets unrelated setup share one enormous fixture.

Replacement: split those boundaries into focused families while preserving every current subtest vector. Do not retire the aggregate until the focused replacements demonstrably retain all vectors.

### Replace `Layer2TriggerRunnerTests.test_codex_contracts_remain_unchanged`

This 817-line family combines launch/environment, JSONL event ownership, command and file-change evidence, selection classification, and timeout behavior. Ripwire reports structural complexity 119 and cognitive complexity 49. It has the same localization and shared-fixture risks as the Claude aggregate.

Replacement: split those boundaries into focused families while preserving every current subtest vector. Do not infer nested-agent dispatch from generic collaboration events in a replacement parser test.

## Keep and merge decisions

- No family was removed. Source inspection found a concrete implementation, adapter, parser, or declaration boundary for every family.
- No family was merged. Ripwire found one Type-3 near-copy pair at 0.80 similarity: Codex timeout cleanup and completed-leader lingering-descendant cleanup. They intentionally distinguish timeout state from completed-leader state, so merging would erase a failure boundary.
- `test_claude_first_selection_guard_contract` remains keep despite its 266-line body because its vectors form one parser/provenance guard matrix with one observable decision boundary. Its size is a maintainability watch item, not evidence that its contract is redundant.
- `test_main_retains_canonical_trial_before_next_launch_and_stops_invalid` remains keep despite high branching because it checks one cross-phase transactional ordering invariant; decomposing it would lose the sequencing assertion.

## Tautology, parameter, and mock review

- AST review found no identical-operand `assertEqual`/`assertIs`/`assertIsNot`, and no constant `assertTrue`/`assertFalse` assertions.
- No literal empty parameter vector was found.
- The positive standing-v3 quota-shape family intentionally has no assertion call: success means both genuine accepted shapes complete without an exception. Adjacent negative families reject forged, mismatched, revoked, excess-authority, and continuity cases.
- The v4 admission handoff wrapper delegates to five assertion-bearing helpers. Those helpers test durable reservation transitions, byte drift, path replacement, and first-writable-transaction handoff.
- Preflight helpers assert an exception and also prove that output creation, ledger construction, lease acquisition, provider invocation, and filesystem mutation did not occur.
- Provider and native-process mocks are kept where the claim is an adapter boundary: the test asserts preflight, lifecycle, durable ledger, replay, or publication behavior around the mocked transport. They are not counted as proof of provider-native semantics.

## Inherited dirty carry-forward entries

The frozen inventory includes two dirty carry-forward additions relative to HEAD:

- `CarryForwardThreatTests.test_clean_boundary_mode_uses_dedicated_admission_contract` at line 686.
- `CarryForwardThreatTests.test_clean_boundary_schedule_reserves_only_the_remaining_336_codex_trials` at line 963.

Both have useful, non-tautological adapter checks and therefore receive `keep` as a utility disposition. Their separate adoption status is `historical_non_adopted_dirty_carry_forward`: this audit neither authored nor approves the inherited edits.

## Focused mutation evidence

Six representative families passed unmodified and killed bounded in-memory faults:

| Boundary | Injected fault | Result |
| --- | --- | --- |
| Trial identity | Force `case_id` to one constant | Assertion failure |
| Hit comparison | Force regression to false | Assertion failure |
| Inventory planning | Increment launch count | Assertion failure |
| Durable reservation | Make `reserve_case` a no-op | Downstream ledger error |
| Execution preflight | Accept invalid scope | Missing-expected-exception failure |
| Declaration coverage | Add a described skill without an eval file | Assertion failure |

These probes show that important implementation, parser, adapter, and declaration families reach the claimed code rather than passing on fixture shape alone. They are bounded checks, not complete mutation coverage.

## Limits and residual risk

- The two aggregate runner families need focused replacements before removal; replacement status is not implementation-complete.
- The audit establishes local deterministic coverage value, not native-provider correctness or campaign qualification.
- Ripwire clone counts are floors for its capped Type-3 classifier. The exact-file scans reported no other clone rows, but semantic overlap can still exist below the classifier threshold.
- Family requirements originate from the frozen inventory and were checked against actual bodies, callees, assertions, and helpers; the ledger does not claim that a passing unit family alone proves the corresponding end-to-end behavior.
