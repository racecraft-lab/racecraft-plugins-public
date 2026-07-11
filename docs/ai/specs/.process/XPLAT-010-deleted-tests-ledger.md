# XPLAT-010 — Deleted Orphan Test Disposition Ledger

**Slice:** PR 1 (orphan-test deletion + disposition ledger). **Requirement:** FR-016.
**Historical scope:** `tests/speckit-pro/unit/*.sh` during the PR 1 deletion-only slice.
**Current state:** Layer 4 is now manifest-backed Python (`tests/speckit-pro/suite-manifest.json`
drives `tests/speckit-pro/run-layer-scripts.py`), so this ledger is historical evidence only.

This ledger records, per file, the disposition of every Layer-4 Bash test script that was a
candidate for deletion under FR-016. Deleted scripts are orphans: their subject-under-test — a
speckit-pro plugin Bash helper — was removed by the XPLAT-009 shipped-Bash purge, so the test
exercises nothing and is absent from the active suite list. Git history preserves their content.

## Verification method (per candidate, before deletion)

A file was deleted only when **both** conditions held:

1. **Absent from the active suite at the time** — not referenced anywhere in the then-authoritative
   `tests/speckit-pro/run-all.sh` Layer-4 roster. In the current repo that historical roster has
   been superseded by `tests/speckit-pro/suite-manifest.json`, and Layer 4 dispatch is now Python-only
   through `tests/speckit-pro/run-layer-scripts.py`.
2. **Subject-under-test removed** — the script targets a helper under `speckit-pro/**` that no
   longer exists. Confirmed live: `git ls-files 'speckit-pro/**/*.sh'` returns **0** files (the
   entire shipped-Bash tree was deleted by XPLAT-009). Each script's own `SCRIPT=`/`source` line
   was read to record the exact removed subject (below).

Cross-checks: no candidate references a still-existing subject (`scripts/refresh-local-plugin.sh`,
`scripts/sync-marketplace-versions.sh`, `.specify/**`, or `.claude/hooks/**`); no candidate is
wired into any CI workflow (only historical mentions in `docs/**` roadmaps and
`.github/copilot-instructions.md`, which are non-executing documentation).

## Deleted — orphan-target-deleted (31 files)

Kind for every row below: `orphan-target-deleted`. Paths are under `tests/speckit-pro/unit/`.
The "removed subject" path is under `speckit-pro/` and no longer exists.

| # | deleted test | removed subject-under-test (XPLAT-009) |
|---|---|---|
| 1 | `test-aggregate-crl.sh` | `speckit-pro/skills/speckit-autopilot/scripts/aggregate-crl.sh` |
| 2 | `test-atomicity-route.sh` | `speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh` |
| 3 | `test-check-prerequisites.sh` | `speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh` |
| 4 | `test-confidence-gate.sh` | `speckit-pro/skills/speckit-autopilot/scripts/confidence-gate.sh` |
| 5 | `test-detect-commands.sh` | `speckit-pro/skills/speckit-autopilot/scripts/detect-commands.sh` |
| 6 | `test-detect-presets.sh` | `speckit-pro/skills/speckit-autopilot/scripts/detect-presets.sh` |
| 7 | `test-detect-stack-manager.sh` | `speckit-pro/skills/speckit-autopilot/scripts/detect-stack-manager.sh` |
| 8 | `test-ensure-reviewability-preset.sh` | `speckit-pro/skills/speckit-coach/scripts/ensure-reviewability-preset.sh` |
| 9 | `test-estimate-reviewable-loc.sh` | `speckit-pro/skills/speckit-autopilot/scripts/estimate-reviewable-loc.sh` |
| 10 | `test-final-reviewability-backstop.sh` | `speckit-pro/skills/speckit-autopilot/scripts/final-reviewability-backstop.sh` |
| 11 | `test-generate-pr-body.sh` | `speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh` |
| 12 | `test-generate-spec-index.sh` | `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh` |
| 13 | `test-generate-uat-skeleton.sh` | `speckit-pro/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh` |
| 14 | `test-install-codex-agents.sh` | `speckit-pro/skills/install/scripts/install-codex-agents.sh` |
| 15 | `test-install-curated-set.sh` | `speckit-pro/scripts/install-curated-set.sh` |
| 16 | `test-migrate-structure.sh` | `speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh` |
| 17 | `test-moc-id-normalize.sh` | `speckit-pro/skills/speckit-autopilot/scripts/lib/moc-id-normalize.sh` |
| 18 | `test-multi-pr-emission.sh` | `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh` |
| 19 | `test-o5-topology.sh` | `speckit-pro/skills/speckit-autopilot/scripts/o5-topology.sh` |
| 20 | `test-parse-consensus-categories.sh` | `speckit-pro/skills/speckit-autopilot/scripts/parse-consensus-categories.sh` |
| 21 | `test-plan-layers.sh` | `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh` |
| 22 | `test-project-fixup.sh` | `speckit-pro/skills/speckit-coach/scripts/project-fixup.sh` |
| 23 | `test-relocate-process-artifacts.sh` | `speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh` |
| 24 | `test-resolve-confidence-mode.sh` | `speckit-pro/skills/speckit-autopilot/scripts/resolve-confidence-mode.sh` |
| 25 | `test-restack.sh` | `speckit-pro/skills/speckit-autopilot/scripts/restack.sh` |
| 26 | `test-reviewability-gate.sh` | `speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh` |
| 27 | `test-validate-agent-install.sh` | `speckit-pro/skills/speckit-autopilot/scripts/validate-agent-install.sh` |
| 28 | `test-validate-gate.sh` | `speckit-pro/skills/speckit-autopilot/scripts/validate-gate.sh` |
| 29 | `test-validate-pr-packet.sh` | `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh` |
| 30 | `test-validate-pr-workflow-contract.sh` | `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-workflow-contract.sh` |
| 31 | `test-validate-uat-runbook.sh` | `speckit-pro/skills/speckit-autopilot/scripts/validate-uat-runbook.sh` |

**Redundant-wrapper disposition (kind `redundant-wrapper`) — see retained note below.** The two
seven-line wrapper shims FR-016 groups with the orphans were retained in PR 1 because they still
sat in the historical `run-all.sh` Layer-4 roster. They were deleted once the manifest-backed
Python dispatch landed; no active Layer-4 `.sh` wrappers remain in the current repo.

## Retained candidates (disposition documented, not deleted)

### Redundant wrappers — historical PR 1 retention, later deleted after manifest cutover (2 files)

| retained test | kind | why not deleted now |
|---|---|---|
| `test-speckit-pro-runner.sh` | `redundant-wrapper` | Historical PR 1 note: this 7-line shim still sat in the old `run-all.sh` Layer-4 roster, so deleting it before the manifest cutover would have broken the active gate. The current repo dispatches `test-speckit-pro-runner.py` directly from `suite-manifest.json`, and the shim is gone. |
| `test-speckit-pro-read-only-helpers.sh` | `redundant-wrapper` | Same historical PR 1 reasoning as above. The current repo dispatches `test-speckit-pro-read-only-helpers.py` directly from `suite-manifest.json`, and the shim is gone. |

### PR-13 restore carve-out (1 file)

| retained test | kind | why not deleted now |
|---|---|---|
| `test-estimate-spec-size.sh` | `active-port-later` | Historical PR 1 note: the Bash subject was temporarily absent, but XPLAT-010 later restored the `estimate-spec-size` operation in Python (FR-025). The current repo runs `test-estimate-spec-size.py`; the `.sh` test is gone. |

### Active-port-later (12 files, not candidates)

Referenced in the historical Layer-4 roster and ported in their own layer PRs, so never deletion
candidates: `test-check-toolchain.sh`, `test-eval-runner-skill-selection.sh`, `test-efficiency-codex-runner.sh`,
`test-parity-extractors.sh`, `test-parity-judge.sh`, `test-moc-lint-exit-codes.sh`,
`test-post-implementation-reference.sh`, `test-privacy-scan.sh`, `test-refresh-local-plugin.sh`,
`test-reviewability-marker-guidance.sh`, `test-sync-marketplace-versions.sh`, `test-transcript-helpers.sh`.
Those subjects are now part of the current Python-only Layer-4 roster.

## Count reconciliation (authoritative total: 31 true orphans + 2 wrappers = 33)

At PR 1, `tests/speckit-pro/unit/` held 46 `.sh` files. Its disposition
was **31 deleted** and **15 retained** (12 active-port-later, 1 PR-13 carve-out,
and 2 redundant wrappers).

The superseded FR-016 headline "34" = "32 orphans + 2 wrappers". The two
adjustments are explicitly sanctioned by tasks.md T005 and this PR's
deletion-only / run-all.sh-untouched constraints:

- **−1**: `test-estimate-spec-size.sh` is inside the "32 orphans" census (absent from run-all.sh, subject
  currently gone) but is the ratified PR-13 restore carve-out → not deleted. Real orphan count is 31.
- **−2**: the 2 redundant wrappers were in the historical `run-all.sh` active list; deleting them
  required the PR-2 manifest cutover (above) → deferred in PR 1, then deleted once
  `suite-manifest.json` became authoritative.

Across PR 1 and PR 2, the authoritative FR-016 deletion set is **33 files**:
31 true orphans plus 2 redundant wrappers. `test-estimate-spec-size.sh` is not
an FR-016 orphan/wrapper deletion target; PR 13 restores its subject and ports
its active test to Python.

## Suite evidence

- **Before (historical PR 1):** default-suite gate `status: ok`; layer-1 direct `24/24 passed`;
  historical Layer-4 direct evidence remained green because the 31 deleted scripts were never in
  the active roster.
- **Current repo state:** Layer 4 is Python-authoritative and manifest-backed; the active ported
  shell-subject roster is 18 Python tests/modules, no active Layer-4 `.sh` wrappers remain, and
  stale `run-all.sh` dispatch references in this ledger have been superseded by
  `suite-manifest.json` plus `run-layer-scripts.py`.
