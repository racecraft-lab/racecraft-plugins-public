# XPLAT-004 Full Verification Evidence

## Commands

| Command | Result |
|---|---|
| `tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.sh` | Pass, 9/9 |
| `bash tests/speckit-pro/run-all.sh --layer 4` | Pass, 2075/2075 |
| `bash tests/speckit-pro/run-all.sh --layer 1` | Pass, 1438/1438 |
| `bash tests/speckit-pro/run-all.sh` | Pass, 3713/3713 |
| `node docs-site/scripts/generate-reference-pages.mjs --check` | Pass, generated reference pages current |
| `node docs-site/scripts/validate-docs-quality.mjs` | Pass |
| `speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh diff origin/main...HEAD` | Pass, `infra` exception honored; total files 43 |
| `bash speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"` | Pass, index current |
| `bash speckit-pro/skills/speckit-autopilot/scripts/validate-gate.sh G7 specs/xplat-004-cross-platform-runner-foundation` | Pass, 47/47 tasks complete |
| `git diff --check origin/main...HEAD` | Pass |
| `python3 -m json.tool speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | Pass |

## Scope Notes

- XPLAT-004 adds a source-checkout Python runner foundation and synthetic contract fixtures only.
- No generated payloads under `dist/**` were changed.
- No active Claude Code or Codex skills, hooks, install behavior, or public support-claim docs were switched to the runner.
- The only docs-site change is the generated tests reference entry for the new runner tests.
- Native installed-cache UAT, generated payload propagation, and public support claims remain XPLAT-007 scope.
