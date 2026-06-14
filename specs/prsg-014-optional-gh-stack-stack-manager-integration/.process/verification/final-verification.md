# PRSG-014 Final Verification Evidence

Recorded after implementation commit `03da8f3c8587d911e6adbbb8361966c80b8cc717`
and evidence commit `c69e1cd`.

| Command | Result |
|---------|--------|
| `bash tests/speckit-pro/layer4-scripts/test-detect-stack-manager.sh` | Passed `18/18` |
| `bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh` | Passed `159/159` |
| `bash tests/speckit-pro/layer4-scripts/test-restack.sh` | Passed `33/33` |
| `bash tests/speckit-pro/run-all.sh --layer 1` | Passed `979/979` |
| `bash tests/speckit-pro/run-all.sh --layer 4` | Passed `1768/1768` |
| `bash tests/speckit-pro/layer7-integration/run-all-fixtures.sh` | Passed all replay fixture classes |
| `bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run` | Passed `12/12` |
| `bash tests/speckit-pro/run-all.sh` | Passed `2937/2937` |

The final default suite was rerun after the detector missing-support
classification fix.
