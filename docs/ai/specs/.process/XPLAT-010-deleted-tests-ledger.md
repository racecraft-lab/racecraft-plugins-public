# XPLAT-010 — Deleted Orphan Test Disposition Ledger

**Slice:** PR 1 (orphan-test deletion + disposition ledger). **Requirement:** FR-016.
**Scope:** `tests/speckit-pro/layer4-scripts/*.sh`. Deletion-only; no port, no run-all.sh edit.

This ledger records, per file, the disposition of every Layer-4 Bash test script that was a
candidate for deletion under FR-016. Deleted scripts are orphans: their subject-under-test — a
speckit-pro plugin Bash helper — was removed by the XPLAT-009 shipped-Bash purge, so the test
exercises nothing and is absent from the active suite list. Git history preserves their content.

## Verification method (per candidate, before deletion)

A file was deleted only when **both** conditions held:

1. **Absent from the active suite** — not referenced anywhere in `tests/speckit-pro/run-all.sh`
   (whose layer lists reference exactly 17 test files: 3 `.py` + 14 `.sh`). `run-layer-scripts.py`
   and the shipped default-suite gate dispatch that list, so a non-referenced script runs nowhere.
2. **Subject-under-test removed** — the script targets a helper under `speckit-pro/**` that no
   longer exists. Confirmed live: `git ls-files 'speckit-pro/**/*.sh'` returns **0** files (the
   entire shipped-Bash tree was deleted by XPLAT-009). Each script's own `SCRIPT=`/`source` line
   was read to record the exact removed subject (below).

Cross-checks: no candidate references a still-existing subject (`scripts/refresh-local-plugin.sh`,
`scripts/sync-marketplace-versions.sh`, `.specify/**`, or `.claude/hooks/**`); no candidate is
wired into any CI workflow (only historical mentions in `docs/**` roadmaps and
`.github/copilot-instructions.md`, which are non-executing documentation).

## Deleted — orphan-target-deleted (31 files)

Kind for every row below: `orphan-target-deleted`. Paths are under `tests/speckit-pro/layer4-scripts/`.
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
seven-line wrapper shims FR-016 groups with the orphans are **not** deleted in this PR (they sit
in run-all.sh's active list). Deleting them safely requires PR 2's manifest cutover, so they are
retained here and their deletion is deferred.

## Retained candidates (disposition documented, not deleted)

### Redundant wrappers — retained, deletion deferred to PR 2 (2 files)

| retained test | kind | why not deleted now |
|---|---|---|
| `test-speckit-pro-runner.sh` | `redundant-wrapper` | 7-line shim that runs `test-speckit-pro-runner.py`. It **is** entry in `run-all.sh`'s active 17-entry layer-4 list. `run-layer-scripts.py` treats a listed-but-missing file as a hard **FAIL** (not a skip), so deleting the shim without editing run-all.sh turns the layer-4 gate red. Editing run-all.sh is out of scope for this deletion-only slice, and dropping the entry would lose the `.py`'s suite coverage. PR 2 replaces run-all.sh with `suite-manifest.json` (which lists the `.py` directly); the shim is deleted there. |
| `test-speckit-pro-read-only-helpers.sh` | `redundant-wrapper` | Same as above, shimming `test-speckit-pro-read-only-helpers.py`. Retained; deleted in PR 2. |

### PR-13 restore carve-out (1 file)

| retained test | kind | why not deleted now |
|---|---|---|
| `test-estimate-spec-size.sh` | `active-port-later` | Subject `speckit-pro/skills/speckit-coach/scripts/estimate-spec-size.sh` is currently absent, but XPLAT-010 **restores** the `estimate-spec-size` operation in PR 13 (FR-025). Per tasks.md T005 this is explicitly excluded from deletion; its test is ported/refreshed in PR 13 (T123). |

### Active-port-later (12 files, not candidates)

Referenced in `run-all.sh`'s layer-4 list and ported in their own layer PRs, so never deletion
candidates: `test-check-toolchain.sh`, `test-eval-runner-skill-selection.sh`, `test-l6-codex-runner.sh`,
`test-l8-extractors.sh`, `test-l8-judge.sh`, `test-moc-lint-exit-codes.sh`,
`test-post-implementation-reference.sh`, `test-privacy-scan.sh`, `test-refresh-local-plugin.sh`,
`test-reviewability-marker-guidance.sh`, `test-sync-marketplace-versions.sh`, `test-transcript-helpers.sh`.

## Count reconciliation (FR-016 headline 34 → 31 deleted)

`tests/speckit-pro/layer4-scripts/` holds 46 `.sh` files. Disposition: **31 deleted** + **15 retained**
(12 active-port-later + 1 PR-13 carve-out + 2 redundant wrappers).

The FR-016 headline "34" = "32 orphans + 2 wrappers". The two adjustments, both explicitly sanctioned
by tasks.md T005 and this PR's deletion-only / run-all.sh-untouched constraints:

- **−1**: `test-estimate-spec-size.sh` is inside the "32 orphans" census (absent from run-all.sh, subject
  currently gone) but is the ratified PR-13 restore carve-out → not deleted. Real orphan count is 31.
- **−2**: the 2 redundant wrappers are in run-all.sh's active list; deleting them requires the PR-2
  manifest cutover (above) → deferred, not deleted here.

## Suite evidence

- **Before:** default-suite gate `status: ok`; layer-1 direct `24/24 passed`; layer-4 direct `17/17 passed`;
  docs reference drift check `Reference pages are current`.
- **After (this PR):** unchanged — the 31 deleted scripts were never in the suite list, so runner
  headlines are identical; `docs-site` `tests.md` regenerated to drop the 31 script rows (reference
  drift check green).
