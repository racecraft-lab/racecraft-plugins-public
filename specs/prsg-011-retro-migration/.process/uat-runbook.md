# UAT Runbook: prsg-011-retro-migration

| Field | Value |
|-------|-------|
| Spec | prsg-011-retro-migration |
| Branch | prsg-011-retro-migration |
| PR | https://github.com/racecraft-lab/racecraft-plugins-public/pull/132 |
| Generated from | 2026-06-09T01:55:37Z |

## Env Setup

Run every command from the repository root on branch `prsg-011-retro-migration`.
This repo has no build, typecheck, lint, or app server step; the acceptance
surface is deterministic shell validation.

| Command | Value |
|---------|-------|
| BUILD | _not available for this project_ |
| TYPECHECK | _not available for this project_ |
| LINT | _not available for this project_ |
| LINT_FIX | _not available for this project_ |
| UNIT_TEST | `bash tests/speckit-pro/run-all.sh --layer 4` |
| INTEGRATION_TEST | `bash tests/speckit-pro/run-all.sh` |
| SINGLE_FILE_INTEGRATION | _not available for this project_ |

## Smoke Checks

1. Confirm the branch and local diff:
   ```bash
   git status --short --branch
   git diff --check origin/main
   ```
2. Expected result: branch is `prsg-011-retro-migration`; whitespace check exits
   zero.

## Per-Story Acceptance Tests

<a id="us-1"></a>
### User Story 1 - Run Repository Structure Migration Safely

1. Run the repository migration fixture:
   ```bash
   bash tests/speckit-pro/layer4-scripts/test-migrate-structure.sh
   ```
2. Expected result: 69 checks pass. The fixture proves dry-run reports work
   without mutation, dirty apply blocks before backup or writes, active-feature
   invalid state blocks mutation, frozen specs are skipped, the repo marker is
   written as `{"structureVersion":1}`, and generator-driven legacy navigation
   backfill is idempotent.

<a id="us-2"></a>
### User Story 2 - Relocate PROCESS Artifacts for a Thawed Legacy Spec

1. Run the Tier-2 relocation fixture:
   ```bash
   bash tests/speckit-pro/layer4-scripts/test-relocate-process-artifacts.sh
   ```
2. Expected result: 104 checks pass. The fixture proves read-only dry-run,
   CONTRACT protection, evidence normalization, review-packet canonicalization,
   docs-side design/workflow relocation, collision blocking, dirty-tree blocking,
   forced backup creation, `SPEC-MOC.md` stamping, generator delegation, and
   idempotent re-run behavior.

<a id="us-3"></a>
### User Story 3 - Suggest Tier-2 Codemod Without Auto-Running It

1. Run the affected functional fixture discovery commands:
   ```bash
   bash tests/speckit-pro/layer3-functional/run-functional-evals.sh speckit-scaffold-spec
   bash tests/speckit-pro/layer3-functional/run-functional-evals.sh speckit-autopilot
   bash tests/speckit-pro/layer3-functional/run-functional-evals-codex.sh speckit-scaffold-spec
   bash tests/speckit-pro/layer3-functional/run-functional-evals-codex.sh speckit-autopilot
   ```
2. Expected result: the commands discover 1, 23, 8, and 29 evals respectively.
   The new fixtures cover one eligible thawed PRSG legacy spec, frozen/in-flight
   suppression, already-current/already-normalized suppression, no-candidate
   suppression, non-SpecKit/date-named namespace suppression, exact dry-run/apply
   command text, and no automatic relocation execution.
3. Run the parity dry-run:
   ```bash
   bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run --fixture 02-prsg-011-migration-guidance
   ```
4. Expected result: 3 variants pass, 0 fail, 0 skip.

## Full Regression

Run the default deterministic suite:

```bash
bash tests/speckit-pro/run-all.sh
```

Expected result: 1958/1958 checks pass.

## FR Coverage Matrix

| Story | Acceptance coverage |
|-------|---------------------|
| [User Story 1](#us-1) | FR-001 through FR-009, FR-021 through FR-024, FR-027 through FR-032 |
| [User Story 2](#us-2) | FR-010 through FR-018, FR-021, FR-022, FR-025, FR-027 |
| [User Story 3](#us-3) | FR-019, FR-020, FR-026, FR-027, FR-029 |

## Negative-Path Tests

- Dirty-tree dry-run is read-only.
- Dirty-tree apply fails before backup, file writes, moves, stamps, or generated
  navigation updates.
- Invalid `.specify/feature.json` blocks every mutating mode before backup.
- Frozen/in-flight specs are skipped in every tier.
- Completed historical specs can be backfilled into navigation without stamping
  or moving their files.
- Missing or invalid repo `structureVersion` preserves pre-marker legacy skip
  behavior.
- Non-SpecKit and date-first namespaces report `skipped_out_of_scope` and never
  emit navigation rows, relocation moves, or scaffold/autopilot suggestions.
- Review-packet and evidence target collisions report a collision and block apply
  before mutation.
- CONTRACT artifacts stay in place even when their names resemble PROCESS files.
- Re-running either migration after completion reports deterministic no-op state.

## Self-Review Findings

1. **Tests executed?** Build/typecheck/lint are N/A for this plugin marketplace
   repo. The required test commands did run and exit zero: Layer 1 887/887,
   Layer 4 881/881, default suite 1958/1958, affected Layer 3 discovery checks,
   Layer 8 dry-run 6 passed, and `git diff --check origin/main` passed on
   2026-06-09T03:24:16Z after the EOF cleanup.
2. **Edge cases?** Covered by the Layer 4 migration and relocation fixtures,
   Layer 3 suggestion fixtures, and Layer 8 parity fixture listed above.
3. **Requirements matched?** All T001-T034 rows are checked in `tasks.md`; the
   task coverage section maps every FR group to completed tasks.
4. **Follow-up?** No `[TODO]`, `[DEFERRED]`, or `[OUT-OF-SCOPE]` markers were
   found in the spec, plan, tasks, or workflow artifacts.

## Sign-off

Advisory only; these checkboxes block nothing.

- [ ] Reviewer ran the smoke checks.
- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

Revert the PR commits. Downstream operator apply commands are explicit and emit a
forced backup path plus restore hint in their JSON reports.
