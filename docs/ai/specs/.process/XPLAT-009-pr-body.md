# feat(xplat): eradicate plugin Bash runtime surface

<!-- speckit-pro-review-packet-source: docs/ai/specs/.process/XPLAT-009-pr-packet.json -->

## Summary

Removes plugin-owned Bash source from SpecKit Pro, updates active Claude/Codex guidance to Python runner/helper/gate operation IDs, rebuilds generated payloads from source, and records zero-Bash source/payload/cache proof for release readiness.

## What Changed

- Deleted plugin-owned `.sh` files under `speckit-pro/`.
- Tightened Python runner/helper/gate ownership for read-only helpers, mutation helpers, zero-Bash guard, payload completeness, installed-cache proof, and release readiness.
- Rebuilt `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/` from cleaned source.
- Updated structural and Layer 4 tests so the suite no longer depends on deleted plugin Bash scripts.
- Added XPLAT-009 source inventory, payload proof, installed-cache proof, zero-Bash guard evidence, release-readiness evidence, UAT runbook, and retrospective.

## Review Order

1. Source/guidance cleanup under `speckit-pro/skills/**`, `speckit-pro/codex-skills/**`, agents, and README files.
2. Python runner/helper/gate changes under `speckit-pro/speckit_pro_runner/**`.
3. Generated payload mirrors under `dist/claude/speckit-pro/**` and `dist/codex/speckit-pro/**`.
4. Tests, fixtures, and process evidence under `tests/speckit-pro/**`, `docs/ai/specs/.process/XPLAT-009-*`, and `specs/xplat-009-plugin-source-and-payload-bash-eradication/**`.

## Verification

- `PYTHONPATH=speckit-pro python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-read-only-helpers.py` -> 33/33 passed
- `PYTHONPATH=speckit-pro python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py` -> 17/17 passed
- `PYTHONPATH=speckit-pro python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py` -> 48/48 passed
- `PYTHONPATH=speckit-pro python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-runner.py` -> 10/10 passed
- `bash tests/speckit-pro/layer4-scripts/test-privacy-scan.sh` -> 10/10 passed
- `bash tests/speckit-pro/run-all.sh` -> 2021/2021 passed
- `git diff --check origin/main...HEAD` -> passed

## UAT Runbook

Runbook: `specs/xplat-009-plugin-source-and-payload-bash-eradication/.process/uat-runbook.md`

Core checks:

- `find speckit-pro -type f -name '*.sh'` returns no files.
- `find dist/claude/speckit-pro dist/codex/speckit-pro -type f -name '*.sh'` returns no files.
- `bash tests/speckit-pro/run-all.sh` reports `2021/2021 passed`.

## Evidence

- `docs/ai/specs/.process/XPLAT-009-source-inventory.md`
- `docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json`
- `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json`
- `docs/ai/specs/.process/XPLAT-009-zero-bash-guard-result.json`
- `docs/ai/specs/.process/XPLAT-009-release-readiness-result.json`
- `specs/xplat-009-plugin-source-and-payload-bash-eradication/.process/final-reviewability/gate-state.json`

## Known Gaps

- XPLAT-008 native Windows/macOS/Linux operator UAT remains outside this spec.
- RepoPrompt review-agent launch failed with `Transport closed`; parent-session review completed and deterministic gates passed.

## Rollback

Revert this branch as a unit. Do not partially restore deleted plugin Bash scripts without matching guidance, payload, test, and release-readiness state.
