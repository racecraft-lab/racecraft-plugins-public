# Data Model: PRSG-011 Retro-migration

## RepositoryStructureMarker

Represents the repo-level migration high-water mark.

- **Path**: `.specify/structure-version.json`
- **Fields**:
  - `structureVersion`: bare integer. Version `1` means the first structure
    migration has completed.
- **Validation**:
  - Missing marker: repo has not completed v1 migration.
  - Malformed, unreadable, non-integer, or value below `1`: Tier-0 legacy-row
    discovery remains disabled, and apply modes block before mutation.

## SpecMocMarker

Represents per-spec migration state on `SPEC-MOC.md`.

- **Path**: `<spec-dir>/SPEC-MOC.md`
- **Fields**:
  - `spec_id`: namespace-aware spec ID used for joins.
  - `structureVersion`: bare integer. Version `1` means the thawed spec has
    accepted the current structure contract.
- **Validation**:
  - Tier-0 never stamps this marker for completed historical specs.
  - Tier-2 requires a regular `SPEC-MOC.md` and stamps only after relocation
    succeeds.

## ActiveFeatureState

Tri-state interpretation of `.specify/feature.json`.

- **States**:
  - `absent`: no active frozen target is declared.
  - `valid`: `feature_directory` is a non-empty string, resolves inside the
    repo, and can be matched by normalized path or `moc_id_match`.
  - `invalid`: present but malformed, unreadable, missing the key, non-string,
    empty, outside the repo, or non-normalizable.
- **Rules**:
  - `valid` freezes the matching spec in every tier.
  - `invalid` is reported by dry-run and blocks every mutating mode before
    backup or mutation.

## MigrationTier

Ordered migration unit.

- **Tier-1**: Repo-level marker creation and repository edits required for the
  structure contract.
- **Tier-0**: Generated roadmap-MOC navigation backfill for eligible historical
  specs, performed through `generate-spec-index.sh`.
- **Tier-2**: Explicit per-spec PROCESS artifact relocation for a thawed legacy
  spec.

## SpecCandidate

Spec directory or archive-memory target considered by Tier-0 or Tier-2.

- **Fields**:
  - `id`: original ID or directory basename.
  - `eligibility`: `eligible` or `out_of_scope`.
  - `out_of_scope_reason`: `null`, `non_speckit_namespace`, or
    `date_named_legacy_namespace`.
  - `normalized_id`: output of `moc_normalize`.
  - `path`: repo-relative target when on disk.
  - `state`: `version_gated`, `legacy_on_disk`, `archive_memory_only`,
    `frozen_in_flight`, `out_of_scope`, or `already_current`.
  - `link_target`: selected Tier-0 navigation target.
- **Rules**:
  - Candidate eligibility is evaluated before Tier-0 row rendering, Tier-2 move
    discovery, and scaffold/autopilot suggestion emission.
  - Current SpecKit candidates are eligible when the first dash-delimited segment
    is `prsg` or `spec`.
  - Legacy numeric/spec candidates remain eligible when they can join to the
    roadmap-MOC spine under `moc_id_match` and are not date-first namespaces.
  - Candidates whose first dash-delimited segment is all-alpha and not `prsg` or
    `spec` are `out_of_scope` with reason `non_speckit_namespace`.
  - Candidates whose basename or archive ID starts with `YYYY`, `YYYY-MM`, or
    `YYYY-MM-DD` followed by end-of-string or `-` are `out_of_scope` with reason
    `date_named_legacy_namespace`.
  - Out-of-scope candidates do not receive Tier-0 rows, Tier-2 move candidates,
    or scaffold/autopilot suggestions.
  - Version-gated specs link to `../../../specs/<dir>/SPEC-MOC.md`.
  - Legacy on-disk specs without a gated MOC link to
    `../../../specs/<dir>/spec.md`.
  - Archive-memory-only specs link to
    `../../../.specify/memory/spec.md#<section-slug>`.

## ArtifactClassification

Classifies files under a thawed spec and matching docs-side process files.

- **Classes**:
  - `process`: allowed to move under Tier-2.
  - `contract`: must remain in place.
  - `already_normalized`: already under a `.process/` anchor.
  - `out_of_scope`: ignored and reported only when relevant.
  - `collision`: move cannot proceed because target already exists.
- **PROCESS allow-list**:
  - `retrospective.md`
  - `*-report.md`
  - `uat-*`
  - `pr-review-packet.md`
  - `peer-review-*`
  - `cleanup-report.md`
  - `analysis.md`
  - `evidence/`
  - `verification-evidence.md`
  - `design-concept.md`
  - `*-design-concept.md`
  - `workflow.md`
  - `*-workflow.md`
- **Canonicalization rules**:
  - `peer-review-*` is a legacy review-packet input alias only. The canonical
    relocated review-packet target is `<spec-dir>/.process/pr-review-packet.md`.
  - Legacy evidence sources canonicalize under the spec `.process` anchor, not
    the visible spec root.
- **CONTRACT protections**:
  - `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`,
    `quickstart.md`, `contracts/**`, `checklists/**`, and `SPEC-MOC.md`.

## MoveOperation

One proposed or applied Tier-2 file move.

- **Fields**:
  - `source`: repo-relative source path.
  - `target`: repo-relative target path.
  - `classification`: artifact classification.
  - `action`: `move`, `protect`, `skip`, `normalize`, or `collision`.
  - `reason`: stable machine-readable reason.
- **Rules**:
  - Spec-root PROCESS files target `<spec-dir>/.process/`.
  - Matching docs-side `docs/ai/specs/<SPEC-ID>-design-concept.md` and
    `<SPEC-ID>-workflow.md` target `docs/ai/specs/.process/`.
  - CONTRACT protection wins over filename allow-list matches.
  - Root `verification-evidence.md` and root
    `evidence/verification-evidence.md` both target
    `<spec-dir>/.process/evidence/verification-evidence.md`.
  - Root `evidence/` targets `<spec-dir>/.process/evidence/` and preserves
    contained evidence files unless a target path would be overwritten.
  - Root `pr-review-packet.md` and exactly one legacy root `peer-review-*`
    target `<spec-dir>/.process/pr-review-packet.md`; legacy basenames are not
    preserved.
  - Multiple source candidates for the same canonical evidence or
    review-packet target are `collision`.
  - Existing canonical `.process/**` targets with no root source are
    `already_normalized`.

## BackupPlan

Restore point required before mutation.

- **Fields**:
  - `path`: absolute backup directory outside the repo.
  - `created`: boolean.
  - `restore_hint`: stable operator instruction.
- **Rules**:
  - Dry-run reports the planned path without creating it.
  - Apply creates the backup after clean-tree validation and before the first
    pending mutation.
  - Already-current apply reruns report no-op without creating a backup.
  - Post-backup failures report the created backup path and restore hint.
  - Tests may override backup root and timestamp for deterministic fixtures.

## MigrationReport

One deterministic JSON object emitted by a migration script.

- **Fields**:
  - `schema_version`
  - `script`
  - `mode`
  - `repo_root`
  - `spec_dir`
  - `active_feature`
  - `dirty_tree`
  - `backup`
  - `status`
  - `items`
  - `recovery`
- **Rules**:
  - Arrays are sorted in stable path/action order.
  - Reports distinguish pending, applied, absent active feature, invalid active
    feature, frozen/in-flight, skipped out-of-scope with stable reason,
    protected CONTRACT, dirty-tree apply-blocked, backup, recovery, no-op
    current-state, and post-backup partial-failure results.
  - Post-backup marker-write, move, stamp, and generator failures keep
    `backup.created` true and require `recovery.available` with a restore hint
    that names the backup path.

## OperatorSuggestion

Static scaffold/autopilot suggestion for Tier-2 relocation.

- **Fields**:
  - `spec_dir`
  - `reason`
  - `dry_run_command`
  - `apply_command`
  - `auto_executed`: always `false`.
- **Rules**:
  - Suggested only for thawed legacy specs with relocatable PROCESS artifacts.
  - `dry_run_command` is
    `speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh --dry-run --spec specs/<spec-dir> --repo-root .`.
  - `apply_command` is
    `speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh --apply --spec specs/<spec-dir> --repo-root .`.
  - Not suggested for valid in-flight specs, already-current specs, or specs
    without relocatable PROCESS artifacts.
  - Not suggested for out-of-scope candidates with `non_speckit_namespace` or
    `date_named_legacy_namespace` reasons.

## UpgradeMigrationGuidance

Static `speckit-upgrade` operator guidance for repository-level migration.

- **Fields**:
  - `dry_run_command`
  - `apply_command`
  - `precondition`
  - `auto_executes_tier2`: always `false`.
- **Rules**:
  - `dry_run_command` is
    `speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh --dry-run --repo-root .`.
  - `apply_command` is
    `speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh --apply --repo-root .`.
  - `precondition` tells the operator to review pending/skipped/no-op dry-run
    output and ensure a clean worktree before apply.
  - Guidance preserves the existing `speckit-upgrade` backup/restore language
    and does not run Tier-2 relocation automatically.
