# Contract: Count-Parity Baseline + Dual-Run Diff (FR-011 / FR-013)

Frozen by Clarifications Session 1 (S1-Q3, S1-Q4). The baseline file is the
single count of record for each ported script; the suite manifest points at it
rather than carrying an inline expected-count integer.

## 1. Baseline file

- **Path:** `tests/speckit-pro/parity/xplat-010/<script>-baseline.txt`
  (one file per `(script, invocation-mode)` pair — e.g. a script with an
  optional scan-root argument that changes its assertion count gets one baseline
  per mode).
- **Frozen format:**
  - One line per executed `_pass`/`_fail` call, in execution order:
    `NNN <canonical-name>` (zero-padded ordinal + verbatim runtime name).
    Grouped checks legitimately repeat the same name on consecutive lines (up to
    11 observed in this repo).
  - A trailing `TOTAL: <N>` line where `N = PASS_COUNT + FAIL_COUNT`.

Example:

    001 validate frontmatter present
    002 validate frontmatter present
    003 description field non-empty
    TOTAL: 3

## 2. Capture rules (5 normalization rules)

1. One line per outcome; names may repeat.
2. Capture environment is pinned and recorded: **non-root, matching CI** (a
   root-vs-non-root capture of `test-moc-lint-exit-codes.sh` diverges 31 vs 36
   assertions).
3. One baseline file per `(script, invocation-mode)` pair for dual-mode scripts.
4. Regeneration triggers include the enumerated data files the script reads at
   runtime (e.g. `scripts/curated-set.json` drives `validate-curated-set.sh`
   check names), not just script source.
5. Names are captured **verbatim** from runtime `VERBOSE=true` PASS/FAIL output,
   parsing only lines matching `^\s*(.+?)\s\.\.\.\s(PASS|FAIL)$` and discarding
   all other subprocess stdout (interleaving is possible mid-line). Never grep
   `assert_`-prefixed source text for inventories — capture is always dynamic
   execution.

Capture tooling SHOULD fail loudly on any PASS/FAIL line with an empty or stale
name rather than falling back to a positional `check-NNN` placeholder (the full
census of 14 Layer-4 scripts + 7 Layer-1 validators found zero un-named sites,
so a positional-fallback feature is not warranted).

## 3. Runtime count granularity (FR-010)

- Granularity is **per individual assertion execution** — every former
  `assert_*` / `_pass` / `_fail` call — not per former `set_test`. This covers
  both loop-generated repetitions and non-loop multi-assertion groupings.
- The Python port computes `{total}`/`{passed}` via a **shared
  `unittest.TestResult` subclass overriding `addSubTest`** (net-new shared
  utility under `tests/speckit-pro/lib/`). Bare `result.testsRun` MUST NOT stand
  in for `{total}` on any module with looping or grouped former assertions, since
  stdlib `subTest` execution never increments `testsRun`.
- `{total}` MUST equal `(test methods not in a subTest loop/group) + (subTest
  units actually executed)`. Each former assertion execution maps to exactly one
  counted Python unit and counts 1 toward `{total}`.
- 1:1 name reconciliation uses `unittest`'s `subTest` `msg=` parameter to
  reproduce each bash check name (shipped precedent: the XPLAT-005 port
  `test-speckit-pro-read-only-helpers.py`).
- **Exempt (retrospective, only these five):**
  `test-speckit-pro-read-only-helpers.py`, `test-speckit-pro-mutation-helpers.py`,
  `test-autopilot-phase-coverage.py`, `test-speckit-pro-runner.py`,
  `test-speckit-pro-gates.py` — born pure-Python under XPLAT-005/006/007, governed
  by the archived XPLAT-007 FR-003 (pass/fail-meaning preservation, not numeric
  count parity). New ports and every other module MUST NOT copy the bare
  `result.testsRun` pattern.

## 4. Dual-run diff block (in every port PR body — 6 required items)

1. The exact bash capture command (`VERBOSE=true <script>`) and the port-run
   command.
2. The committed baseline path.
3. A unified diff of the ordered canonical check-name inventory, **or** the
   literal line `no differences — 1:1 preserved`.
4. The explicit count equality: `bash: N == python: N`.
5. An intentional-change statement — `none` for a clean port; any rename or drop
   flags the PR as a regression.
6. The count-ledger delta line appended to the running ledger.

## 5. Cumulative evidence (FR-013)

- **Running ledger:** `docs/ai/specs/.process/XPLAT-010-count-ledger.md` — one
  delta line per port PR.
- **Final artifact:** `docs/ai/specs/.process/XPLAT-010-suite-parity-result.json`
  — cumulative name-and-count preservation across the whole PR stack.
