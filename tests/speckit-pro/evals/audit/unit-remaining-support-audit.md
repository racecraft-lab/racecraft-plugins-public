# Remaining Layer 4 Support Audit

## Verdict

This bounded slice deeply reviews exactly 200 frozen loaded families in six runner, helper, and support-utility executables. It does not complete Layer 4. The frozen Layer 4 baseline contains 1,615 loaded families; five earlier audits cover 761 without file overlap, this slice covers 200, and 654 remain.

All 200 dispositions are **keep**. No family is retained merely because it exists: the JSON ledger records the frozen function body hash, requirement, failure boundary, observed assertion expressions, invoked contract paths, simulation limit, runtime result, and replacement field for every loaded family. No replacement is proposed because review found no replacement-level weak or successful no-op oracle.

## Exact scope and counts

| Frozen executable | Loaded families | Static assertions in loaded bodies | Focused result |
|---|---:|---:|---|
| `tests/speckit-pro/lib/test_lib.py` | 7 | 28 | 7/7 passed |
| `tests/speckit-pro/unit/test-unit-layout.py` | 11 | 18 | 11/11 passed |
| `tests/speckit-pro/unit/test-speckit-pro-gates.py` | 53 | 643 | 48/53 passed |
| `tests/speckit-pro/unit/test-speckit-pro-runner.py` | 12 | 65 | 11/12 passed |
| `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` | 114 | 673 | 114/114 passed |
| `tests/speckit-pro/unit/test-workflow-guard-hook.py` | 3 | 30 | 3/3 methods passed; 34/34 house units |
| **Total** | **200** | **1,457** | **194 passed, 6 failed, 0 skipped methods** |

Separate inventory measures must not be conflated: these six files contain 1,568 total static assertion sites, 77 static subtest call sites in loaded bodies, seven support-only test-shaped functions, one skip-decorated loaded family, and zero preview/dry-run-named loaded families. `test_lib.py` intentionally runs nested failing stimulus while its seven loaded harness tests pass (`tests/speckit-pro/lib/test_lib.py:21`).

The exact source files in the trigger, workflow-eval, release-tooling, quality-formal, and execution-contract audit ledgers were excluded before selection. All six selected source hashes still match the frozen inventory, and the overlap is zero.

## Actionable findings

### 1. Current runner trust metadata is stale

Six families correctly fail closed. The current SHA-256 values for `speckit_pro_runner/gates/active_path_guard.py` and `speckit_pro_runner/gates/suite.py` differ from their generated runner-manifest records. The runner test detects the mismatch directly (`tests/speckit-pro/unit/test-speckit-pro-runner.py:292`); five payload/readiness families then fail on that same stale installed-payload boundary (`tests/speckit-pro/unit/test-speckit-pro-gates.py:430`, `tests/speckit-pro/unit/test-speckit-pro-gates.py:1966`, `tests/speckit-pro/unit/test-speckit-pro-gates.py:2009`, `tests/speckit-pro/unit/test-speckit-pro-gates.py:2080`, and `tests/speckit-pro/unit/test-speckit-pro-gates.py:2136`).

Action: after concurrent runner-source work settles, regenerate release artifacts and rerun those two focused executables. Do not weaken, remove, or reinterpret the failures as passes.

### 2. Deterministic fixtures are not live qualification

These families use source/schema inspection, temporary workspaces, local subprocesses, patched command results, and installed-release fixtures. They do not prove a live provider, Docker daemon, or remote Git operation. Every family record explicitly sets all three proof flags to false. Local Git-shaped metadata cases in the helper suite remain simulations (`tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2795`), and installed-release cases remain fixture-bound (`tests/speckit-pro/unit/test-speckit-pro-gates.py:1544`).

### 3. One platform-conditional family ran on this host

The descriptor-safe symlink replacement test is skip-decorated for unsupported platforms (`tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3110`). It ran here, and the file reported 114/114 with zero skips. That is current-host evidence only.

### 4. Clone shapes do not justify removing a requirement

A fresh Ripwire unit-tree clone scan found 90 groups touching the selected unit files: three Type-2 groups and 87 Type-3 groups. All Type-2 groups are local harness helpers (`run_runner`, `assert_response`, and `command_stdin_fixture`), not loaded case-family bodies. The Type-3 rows are predominantly shared fixture scaffolding and adjacent positive/negative boundary cases with different injected inputs or postconditions. A separate `test_lib.py` scan found one Type-3 pair: all-pass versus skipped-suite accounting. Those enforce opposite result boundaries and both remain.

## Negative controls

Six temporary, non-mutating fault injections were detected 6/6:

1. A counted runner that omits the empty-suite summary.
2. A spec-ID regex that can never match.
3. A corrupted default-suite command-ID mapper.
4. Release-review detection forced false.
5. Repository-root discovery forced to return `None`.
6. The unpushed-work hook forced to allow without a decision.

These controls establish representative sensitivity; they are not substituted for the per-family body and assertion review in the JSON ledger.

## Completion-gate boundary

The repository-wide Ripwire completion checks are not green in this concurrent worktree. `--quality-delta` exited 2 with 22 gating findings across 32 changed paths; `--test-gate` exited 4 with 142 requested tests and 85 untested symbols. Those totals include concurrent implementation and audit lanes and cannot be attributed to these two report-only additions. This slice ran only the six focused executables listed above and the six temporary negative controls; it does not reinterpret the whole-worktree gates as passed.

## Remaining boundary

This report stops at the approved 200-family cap. Exactly 654 frozen Layer 4 loaded families remain outside the five earlier audit file lists and this slice. Native-eval files that changed after the frozen inventory were deliberately not selected, and no source, test, manifest, provider, Docker, or remote-Git operation was changed or launched.
