Priority: blocking

## Summary

Layer 4 lists its unit scripts by hand in tests/speckit-pro/suite-manifest.json and omits two tracked tests. test-consensus-synthesizer-regressions.py and test-native-eval-fixture-setup.py never run in run-all.py or the CI suite, and the second is the only test of the feature_deletions symlink and reserved-path guards. Nothing checks that the roster is complete.

## Evidence

- **structural-layers-2-001** (blocking): Layer 4 lists its scripts by hand and omits two tracked unit tests. Neither test-consensus-synthesizer-regressions.py nor test-native-eval-fixture-setup.py appears in the manifest, so run-all.py and the CI suite never run them. test-unit-layout.py does not check roster completeness. No in-flight branch adds them.
  - `tests/speckit-pro/suite-manifest.json:176`, `tests/speckit-pro/unit/test-consensus-synthesizer-regressions.py:1`, `tests/speckit-pro/unit/test-native-eval-fixture-setup.py:1`
- **native-eval-harness-004** (blocking, adjusted from major in review): test-native-eval-fixture-setup.py is absent from the Layer 4 manifest, so run-layer-scripts.py never runs it and it is the only test of the feature_deletions symlink and reserved-path guards. Nothing in test-unit-layout.py enforces that every unit test is registered.
  - `tests/speckit-pro/unit/test-native-eval-fixture-setup.py:1`, `tests/speckit-pro/suite-manifest.json:59-88`

## Proposed fix

- structural-layers-2-001: Add both tests to layer 4 in suite-manifest.json, and add a manifest-completeness check (every unit/test-*.py is listed) to test-unit-layout.py.
- native-eval-harness-004: Register the script in suite-manifest.json layer 4 and add a layout test that every unit/test-*.py appears in the manifest.

## Acceptance

- [ ] Both scripts are registered in layer 4 and pass.
- [ ] test-unit-layout.py (or a sibling layout test) fails when any tests/speckit-pro/unit/test-*.py is missing from the manifest. Show it failing before the registration.
- [ ] The CI suite request runs both scripts.

## Related

- Overlaps files changed by the open stop-policy stack: #843, #845, #850, #851, #852. Land after that stack merges.
- Overlaps files changed by open PR #685.
- Overlaps files changed by the in-progress fix for #832.

Found by the 2026-09 coherence audit.
