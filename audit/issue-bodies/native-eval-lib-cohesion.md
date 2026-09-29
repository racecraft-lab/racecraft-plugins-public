Priority: major

## Summary

The strict duplicate-key JSON loader is re-implemented about 20 times across 16 native eval modules with different rules, so the README's strict-JSON contract holds only in some paths. runner_result and verification are near copies. Several modules and symbols have no production caller.

## Evidence

- **native-eval-harness-002** (major): The strict duplicate-key JSON loader is re-implemented in about 20 places across 16 lib modules with different error types and different rules. Adapters (482, 3385, 3991) and the store (165) do not reject NaN or Infinity constants, while catalog, judge, execution, capture and pairing do, so the README's strict-JSON contract holds only in some paths.
  - `tests/speckit-pro/lib/native_eval_adapters.py:3375`, `tests/speckit-pro/lib/native_eval_store.py:165`, `tests/speckit-pro/lib/native_eval_runner_result.py:105`, `tests/speckit-pro/lib/native_eval_verification.py:111`, `tests/speckit-pro/lib/native_eval_execution.py:284`, `tests/speckit-pro/lib/native_eval_upstream.py:562`
- **native-eval-harness-003** (minor): runner_result and verification are near copies: _path, _loads, _output_text, attach_receipt and the *_checks selectors differ only in the exception class and metadata key. _strict_equal is defined four times (execution:2228, grading:181, runner_result:124, verification:130).
  - `tests/speckit-pro/lib/native_eval_runner_result.py:39`, `tests/speckit-pro/lib/native_eval_verification.py:50`, `tests/speckit-pro/lib/native_eval_runner_result.py:322`, `tests/speckit-pro/lib/native_eval_verification.py:290`, `tests/speckit-pro/lib/native_eval_grading.py:181`
- **native-eval-harness-005** (major): native_eval_skill_reads.py (296 lines) has no production importer; only its own unit test uses it. Codex activation is now derived from injection evidence in native_eval_codex_rollouts.py, so the read-based qualifier is orphaned code that still ships a schema (codex-skill-read-qualification/v1).
  - `tests/speckit-pro/lib/native_eval_skill_reads.py:187`, `tests/speckit-pro/unit/test-native-eval-skill-reads.py:15`
- **native-eval-harness-006** (minor): pointer_artifacts has no caller anywhere (only its __all__ entry), and _GIT_OBSERVATION_V1 is never read. observe_git_topology and decode_sealed_plan_repair_message are called only from unit tests.
  - `tests/speckit-pro/lib/native_eval_verification.py:79`, `tests/speckit-pro/lib/native_eval_execution.py:93`, `tests/speckit-pro/lib/native_eval_git_observation.py:149`, `tests/speckit-pro/lib/native_eval_dispatch_context.py:271`
- **native-eval-harness-010** (minor): The 4,500-line adapters module mixes Claude and Codex staging, isolation proofs, receipts and two embedded Python programs held as raw string literals (git and upstream scaffolds). String-embedded code escapes lint, mypy and direct tests, and it calls private setup helpers (_workspace_directory, _write_receipt).
  - `tests/speckit-pro/lib/native_eval_adapters.py:72-160`, `tests/speckit-pro/lib/native_eval_adapters.py:1340`
- **native-eval-harness-012** (minor): The public CLI embeds the NativeJudge callback (process supervision, cleanup and result validation) instead of native_eval_judge.py, imports the private _validate_limits from the pool module, and exposes --claude-model, --codex-model and --judge-model with hard-coded defaults that the README never mentions.
  - `tests/speckit-pro/run-native-evals.py:35-96`, `tests/speckit-pro/run-native-evals.py:20`, `tests/speckit-pro/run-native-evals.py:116-118`

## Proposed fix

- native-eval-harness-002: Add one strict_json helper (duplicate keys, constants, recursion) in a shared lib module with a caller-supplied error class, and replace every local copy.
- native-eval-harness-003: Extract the shared receipt attach, output parsing and strict equality into one helper module and parameterize the metadata key and error class.
- native-eval-harness-005: Delete the module and its test, or wire it into grading and document why both activation sources exist.
- native-eval-harness-006: Remove the unused symbols; keep the test-only ones only if a production caller is planned.
- native-eval-harness-010: Ship the scaffolds as real files under lib/ and split adapters into per-host modules.
- native-eval-harness-012: Move NativeJudge into native_eval_judge.py, make the limits validator public, and document or remove the model flags.

## Acceptance

- [ ] One strict_json helper with a caller-supplied error class replaces every local copy.
- [ ] A regression test that fails before the fix: NaN and Infinity are rejected by the adapters and store paths.
- [ ] Orphaned modules and symbols are removed or wired in; adapters embed no Python programs as strings.
- [ ] Native eval unit tests pass.

## Related

- None.

Found by the 2026-09 coherence audit.
