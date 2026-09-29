Priority: minor

## Summary

Several test modules hand-list their test classes or methods, so a new test never runs and the suite still passes. Large test files mix unrelated contracts, and about thirty tests copy the same loader and runner helpers. The dispatchers keep a retired shell mode, unused environment variables and a misnamed default-suite request.

## Evidence

- **structural-layers-2-011** (minor): build_suite runs a hand-listed TEST_METHOD_ORDER, so a test method added to ValidateToolScoping and not listed never runs, and the suite still passes.
  - `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py:129`, `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py:550`
- **brokers-and-verification-014** (minor): The 3154-line execution-control test file also holds the host and Docker verification suites (VerificationTests, DockerVerificationTests), which duplicate the subject of test-verification-docker.py and test-verification-git.py. Its __main__ block runs a hand-written class list, so a new TestCase class not added there never runs, and nothing asserts the list is complete. The branch of PR 852 keeps growing that list.
  - `tests/speckit-pro/unit/test-execution-control.py:2544`, `tests/speckit-pro/unit/test-execution-control.py:3058`, `tests/speckit-pro/unit/test-execution-control.py:3142-3154`
- **autopilot-and-agents-012** (minor): The module docstring scopes it to the status-evidence rule, but 2,405 lines also hold prose-contract classes for blocked-action deferral, run finalization, failure classes, ambiguous wording, plugin drift and standing-policy preflight. It mixes six feature contracts under one misleading name.
  - `tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:2`, `tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:616`, `tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:981`
- **pr-emission-and-stack-2-006** (minor): test-finalize-run.py also holds DeferredSectionInPrBodyTests, which exercises pr_emission.normalize_packet_input and packet validation. That is PR-body emission, not run finalization, so a body regression is hidden in this file.
  - `tests/speckit-pro/unit/test-finalize-run.py:439`, `tests/speckit-pro/unit/test-finalize-run.py:1`
- **runner-core-008** (minor): The runner-subprocess helper run_runner is redefined in at least nine unit test modules, and command_stdin_fixture and assert_response in two or three each, though tests/speckit-pro/lib/test_lib.py exists. move_after_copy_open is defined twice in one test file. Copies already differ in signature and return shape.
  - `tests/speckit-pro/unit/test-speckit-pro-gates.py:85`, `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:395`, `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:419`, `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3974`, `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5810`, `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:271`, `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:304`, `tests/speckit-pro/unit/test-speckit-pro-runner.py:38`
- **release-tooling-016** (minor): About thirty unit tests each define the same importlib file loader, and no shared helper exists in tests/speckit-pro/lib. changed_files_for_base is duplicated between check-go-module.py and classify-docs-validation.py.
  - `tests/speckit-pro/unit/test-release-pr-reconciliation.py:25`, `tests/speckit-pro/unit/test-typesafe-jev-release-build.py:33`, `tests/speckit-pro/unit/test-pr-checks-helpers.py:32`, `scripts/check-go-module.py:50`, `scripts/classify-docs-validation.py:129`
- **structural-layers-2-007** (minor): run-all.py exports TESTS_DIR, PLUGIN_ROOT and PROJECT_ROOT to children, but nothing under tests, scripts or the plugin reads them. Its docstring (lines 4 and 17) and run-layer-scripts.py:69 cite the retired run-all.sh. The two dispatchers also build different child environments.
  - `tests/speckit-pro/run-all.py:141`, `tests/speckit-pro/run-all.py:4`, `tests/speckit-pro/run-layer-scripts.py:69`, `tests/speckit-pro/run-layer-scripts.py:80`
- **release-tooling-015** (minor): The 'shell' toolchain mode runs the same checks as 'tests' under a different label, in a repository with no Bash dependency. The mode set is listed in check-toolchain.py and three times in suite.py; run-all.py still selects shell as a fallback.
  - `tests/speckit-pro/check-toolchain.py:20`, `tests/speckit-pro/check-toolchain.py:221`, `speckit-pro/speckit_pro_runner/gates/suite.py:30`
- **release-tooling-017** (minor): run-default-suite.json lists six layer keys, including integration and parity, which the manifest marks non-default, and it restates the manifest roster by hand. The name says default; the request is the CI suite.
  - `tests/speckit-pro/unit/fixtures/runner-gates/requests/run-default-suite.json:9`, `tests/speckit-pro/suite-manifest.json:1`
- **native-eval-harness-001** (minor, adjusted from major in review): README says layers 2, 3, 6 and 7 are live native selectors of run-native-evals.py, but the manifest ids 2 and 3 still dispatch the legacy run-trigger-evals and run-functional-evals runners, and 6 and 7 dispatch deterministic fixture runners. run-all.py never mentions run-native-evals.py, so one layer id has two unrelated entry points.
  - `tests/speckit-pro/evals/README.md:217-225`, `tests/speckit-pro/suite-manifest.json:223-248`, `tests/speckit-pro/suite-manifest.json:195-218`

## Proposed fix

- structural-layers-2-011: Discover test_* methods and keep an explicit order only for the one test that mutates module state, or assert the list equals the discovered set.
- brokers-and-verification-014: Move the verification classes to their own module and replace the manual list with a check that every TestCase in the module is in the suite.
- autopilot-and-agents-012: Split the source-contract classes into per-feature test files.
- pr-emission-and-stack-2-006: Move DeferredSectionInPrBodyTests into a PR-emission test module and keep this file to finalize-run.
- runner-core-008: Add one shared runner-invocation helper to tests/speckit-pro/lib/ and import it.
- release-tooling-016: Add one load_script helper to tests/speckit-pro/lib and one shared changed-files function in scripts/.
- structural-layers-2-007: Drop the unused variables, remove run-all.sh references, and share one child-environment helper.
- release-tooling-015: Drop the shell mode, or derive the mode set from one constant.
- release-tooling-017: Rename it to the CI suite and derive the roster from the manifest, or drop the explicit list.
- native-eval-harness-001: State in the README that native evaluation is a separate CLI whose selectors reuse the layer numbers, or register the native runner in the manifest layers and retire the legacy runners once migration ends.

## Acceptance

- [ ] A regression test that fails before the fix: a TestCase or test method not in the hand list is detected (or discovery replaces the lists).
- [ ] Verification, bookkeeping and PR-body tests move to modules named for their concern.
- [ ] Shared run_runner and load_script helpers live in tests/speckit-pro/lib.
- [ ] The shell toolchain mode and run-all.sh references are gone; the suite request name says CI; the README explains the native CLI's layer selectors.
- [ ] Both suites pass.

## Related

- Overlaps files changed by the open stop-policy stack: #837, #838, #843, #844, #845, #846, #847, #848, #849, #850, #851, #852. Land after that stack merges.
- Overlaps files changed by open PR #685.
- Overlaps files changed by the in-progress fix for #832.
- Depends on #856

Found by the 2026-09 coherence audit.
