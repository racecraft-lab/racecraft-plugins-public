Priority: major

## Summary

The Layer 3 headless runner re-implements the Layer 2 Codex isolation arguments, and the copies have drifted. required_tools is enforced only for Codex cases, so 54 Claude cases carry unenforced metadata. The executor-mode scorer crashes on malformed input it promises to reject, blends duplicate seeds, and its design doc names a floor source the scorer never reads.

## Evidence

- **functional-evals-2-005** (major): Layer 3 already imports the Layer 2 Codex runner, yet it re-implements the permission args, MCP inventory and skill isolation args. The copies drifted: CODEX_DISABLED_FEATURES lacks unbounded_connection_retries, which Layer 2 disables, and Layer 3 reaches into the private _canonical_skill_files.
  - `tests/speckit-pro/layer3-functional/run-headless-evals.py:34-37`, `tests/speckit-pro/layer3-functional/run-headless-evals.py:349-410`, `tests/speckit-pro/layer2-trigger/run_codex_evals.py:62-65`, `tests/speckit-pro/layer2-trigger/run_codex_evals.py:559-635`, `tests/speckit-pro/layer3-functional/run-headless-evals.py:342`
- **functional-evals-2-006** (minor): required_tools is enforced only for Codex cases. The Claude branch of require_provider_evidence returns before the check, so the 54 Claude cases that require Skill and Read carry unenforced metadata. launch_policy read_only and restricted_read_only are likewise never read; only hold is.
  - `tests/speckit-pro/layer3-functional/headless_cases.json:42`, `tests/speckit-pro/layer3-functional/run-headless-evals.py:1038`, `tests/speckit-pro/layer3-functional/run-headless-evals.py:1067-1073`
- **functional-evals-2-009** (minor): main() is about 200 lines (cyclomatic complexity 40) and mixes argument validation, staging, launch, event parsing, evidence writing and manifest status in one function.
  - `tests/speckit-pro/layer3-functional/run-headless-evals.py:1121-1326`
- **functional-evals-1-004** (minor): The design doc says the floor comes from .specify/quality-gates.json and lists the scorer flags without --mutation-floor. The scorer reads no such file; the floor is an optional CLI flag defaulting to None, so the "no task below the floor" rule is skipped unless passed. The doc also names only "beats" and "inconclusive" while the scorer can return "loses".
  - `docs/ai/specs/executor-mode-paired-eval-design.md:112`, `docs/ai/specs/executor-mode-paired-eval-design.md:18`, `tests/speckit-pro/layer3-functional/executor-modes/score-executor-modes.py:236-238`
- **functional-evals-2-008** (minor): The scorer says exit 1 is for malformed input, but a result file holding a non-object JSON value raises an uncaught TypeError traceback. Duplicate (case, mode, seed) documents are accepted and blended into the median, and the catalog repeats value is never read, so a short or duplicated run set scores silently.
  - `tests/speckit-pro/layer3-functional/executor-modes/score-executor-modes.py:91-121`, `tests/speckit-pro/layer3-functional/executor-modes/score-executor-modes.py:124-140`, `tests/speckit-pro/layer3-functional/executor-modes/catalog.json:8`, `docs/ai/specs/executor-mode-paired-eval-design.md:52-54`

## Proposed fix

- functional-evals-2-005: Move the shared Codex isolation helpers and feature list into one module under tests/speckit-pro/lib and import it from both layers.
- functional-evals-2-006: Enforce required_tools against the Claude tool trace, or drop the field and the unused launch_policy values from Claude cases.
- functional-evals-2-009: Split into a per-case runner returning a manifest and a thin main that loops cases.
- functional-evals-1-004: Document --mutation-floor and the loses verdict, and state that the caller supplies the floor from quality-gates.json.
- functional-evals-2-008: Reject non-object documents and duplicate seeds as InputError, and check each (case, mode) has catalog repeats distinct seeds or report the shortfall.

## Acceptance

- [ ] One shared module under tests/speckit-pro/lib provides the Codex isolation arguments to both layers.
- [ ] required_tools is enforced for Claude cases, or the field is dropped from them.
- [ ] Regression tests that fail before the fix: a non-object result document and a duplicate (case, mode, seed) are rejected as input errors.
- [ ] The design doc documents --mutation-floor and the 'loses' verdict.

## Related

- None.

Found by the 2026-09 coherence audit.
