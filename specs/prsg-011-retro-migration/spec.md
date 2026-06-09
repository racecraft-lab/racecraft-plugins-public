# Feature Specification: Retro-migration - Version Marker and State-Keyed Backfill/Relocate

**Feature Branch**: `prsg-011-retro-migration`

**Created**: 2026-06-08

**Status**: Draft

**Input**: User description: "Add a deterministic, operator-safe migration path that upgrades existing SpecKit project structure with a repo-level structure marker, Tier-0 navigation backfill, and an explicit Tier-2 PROCESS artifact relocation codemod for thawed legacy specs."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run repository structure migration safely (Priority: P1)

As a maintainer upgrading an existing SpecKit project, I can run `migrate-structure.sh --dry-run` to see ordered pending structure migrations without changing files, then run `migrate-structure.sh --apply` on a clean tree to establish the repository structure marker and Tier-0 navigation backfill.

**Why this priority**: This is the minimum safe upgrade path. It gives existing projects the new repository structure contract without moving or stamping completed legacy specs.

**Independent Test**: Can be fully tested against a fixture repository with historical specs by comparing workspace state before and after dry-run, then applying on a clean tree and verifying the marker plus navigation output.

**Acceptance Scenarios**:

1. **Given** an existing SpecKit project without `.specify/structure-version.json`, **When** the maintainer runs `migrate-structure.sh --dry-run`, **Then** the output lists pending Tier-1 repository edits and Tier-0 navigation backfill in a stable order and no files are changed.
2. **Given** the same project on a clean tree, **When** the maintainer runs `migrate-structure.sh --apply`, **Then** the migration creates `.specify/structure-version.json` with `structureVersion` set to `1`, performs Tier-1 repository edits, and updates generated navigation for eligible historical specs.
3. **Given** a dirty worktree, **When** the maintainer runs `migrate-structure.sh --apply`, **Then** the command fails before backup creation, file writes, index regeneration, or other mutations.
4. **Given** a project already migrated to `structureVersion` 1, **When** the maintainer runs dry-run or apply again, **Then** the output reports the current no-op state and does not duplicate marker or navigation changes.

---

### User Story 2 - Relocate PROCESS artifacts for a thawed legacy spec (Priority: P2)

As a maintainer thawing a legacy spec, I can run `relocate-process-artifacts.sh --dry-run` to preview the exact PROCESS artifacts that would move, then run `relocate-process-artifacts.sh --apply` on a clean tree to move only allowed PROCESS artifacts into the correct `.process/` anchor, stamp the spec MOC, regenerate links/index, and recover from the forced backup if needed.

**Why this priority**: It completes the migration path for specs that are intentionally brought forward while preserving historical specs by default.

**Independent Test**: Can be fully tested with a fixture legacy spec that contains both PROCESS and CONTRACT artifacts by validating the dry-run move set, apply results, backup path, stamp, and regenerated links.

**Acceptance Scenarios**:

1. **Given** a thawed legacy spec with relocatable PROCESS files, **When** the maintainer runs `relocate-process-artifacts.sh --dry-run`, **Then** the output lists every proposed move, skipped CONTRACT artifact, evidence normalization, generated-link update, and backup location without changing files.
2. **Given** the thawed legacy spec on a clean tree, **When** the maintainer runs `relocate-process-artifacts.sh --apply`, **Then** the command creates a forced backup, moves only allowed PROCESS artifacts into `.process/`, stamps `SPEC-MOC.md` with `structureVersion: 1`, normalizes legacy evidence into `.process/evidence/verification-evidence.md`, and regenerates links/index.
3. **Given** the same spec after successful relocation, **When** the maintainer re-runs dry-run or apply, **Then** the command reports an idempotent no-op state and does not move or stamp anything again.
4. **Given** a target path collision or partial failure, **When** relocation cannot complete safely, **Then** the command stops with a clear error, leaves recovery instructions that name the backup path, and does not continue with later moves.

---

### User Story 3 - Suggest Tier-2 codemod without auto-running it (Priority: P3)

As a scaffold or autopilot operator, I see an explicit suggested next action when a thawed legacy spec has relocatable PROCESS files, while the scaffold/autopilot flow never executes the relocation codemod for me.

**Why this priority**: Operators need discoverability for the migration path, but automatic file moves would be too risky inside scaffold/autopilot flows.

**Independent Test**: Can be fully tested by running scaffold/autopilot fixtures for thawed, frozen, and already-migrated specs and checking the surfaced suggestion text plus absence of codemod side effects.

**Acceptance Scenarios**:

1. **Given** a thawed legacy spec with relocatable PROCESS files, **When** scaffold or autopilot evaluates the spec, **Then** it shows the exact Tier-2 dry-run command and apply follow-up as a suggested next action.
2. **Given** an in-flight spec listed in `.specify/feature.json`, **When** scaffold or autopilot evaluates migration state, **Then** it reports the frozen/in-flight reason and does not suggest or run relocation.
3. **Given** a thawed spec with no relocatable PROCESS artifacts, **When** scaffold or autopilot evaluates migration state, **Then** it reports no Tier-2 action is needed.
4. **Given** any scaffold or autopilot run, **When** the Tier-2 codemod is suggested, **Then** no dry-run or apply command is executed automatically.

### Edge Cases

- Dry-run is executed on a dirty tree and must remain read-only.
- Any mutation path is requested on a dirty tree and must fail before backup, file writes, moves, stamps, or generated-zone updates.
- `.specify/feature.json` names an in-flight spec; that spec is skipped in every tier and reported as frozen/in-flight.
- `.specify/feature.json` exists but cannot identify a valid active spec; dry-run reports the invalid active-feature state, and every mutating mode exits before backup or mutation.
- A historical spec can be ID-normalized for navigation but has no `SPEC-MOC.md`; Tier-0 must not stamp or move it and must report what was backfilled or skipped.
- `.specify/structure-version.json` is absent, unreadable, malformed, or has `structureVersion` below `1`; Tier-0 legacy-row discovery is disabled and `generate-spec-index.sh` preserves pre-marker behavior by indexing only version-marked SPEC-MOCs and skipping legacy or non-version-marked specs.
- A candidate directory, archive-memory section, or docs-side PROCESS file starts with a non-SpecKit alpha namespace such as `foo-001-*`, or with a date-first legacy namespace such as `2026-*`, `2026-06-*`, or `2026-06-08-*`; every tier reports `skipped_out_of_scope` with reason `non_speckit_namespace` or `date_named_legacy_namespace` and emits no navigation row, relocation move, or scaffold/autopilot suggestion.
- A legacy spec contains both `pr-review-packet.md` and `peer-review-*`; relocation must recognize both as review-packet source candidates, keep `.process/pr-review-packet.md` as the canonical target, and report a target-path collision instead of overwriting.
- A legacy spec contains `verification-evidence.md` and/or an existing `evidence/` directory; relocation must normalize evidence under `.process/evidence/` without overwriting unrelated evidence.
- A legacy spec contains both root `verification-evidence.md` and root `evidence/verification-evidence.md`; dry-run reports a target-path collision for `.process/evidence/verification-evidence.md` and apply fails before mutation.
- A spec contains CONTRACT artifacts with names similar to PROCESS artifacts; CONTRACT artifacts must stay in place.
- A spec contains PROCESS-like filenames under `contracts/` or `checklists/`; explicit CONTRACT protections win and those files stay in place.
- A thawed spec has matching legacy scaffold files in `docs/ai/specs/<SPEC-ID>-design-concept.md` or `docs/ai/specs/<SPEC-ID>-workflow.md`; Tier-2 reports and moves only those matching docs-side PROCESS files to `docs/ai/specs/.process/`.
- A migration is re-run after a completed or partially completed migration; output must be deterministic and safe to act on.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The migration tooling MUST expose `migrate-structure.sh (--dry-run|--apply) [--repo-root <path>]` as the repository-level structure migration entry point, and exactly one mode flag MUST be required per invocation.
- **FR-002**: `migrate-structure.sh --dry-run` MUST emit one deterministic JSON report that lists pending Tier-1 repository edits, Tier-0 navigation backfill, skipped frozen specs, planned backup path, and no-op current-state items in stable order.
- **FR-003**: All dry-run modes MUST be read-only and MUST be safe to run on a dirty worktree.
- **FR-004**: All mutation modes MUST fail on any non-empty `git status --porcelain=v1 --untracked-files=all` output before backup creation, file writes, file moves, marker updates, generated-zone updates, or stamps.
- **FR-005**: `migrate-structure.sh --apply` MUST create `.specify/structure-version.json` with `structureVersion` set to `1` when the repository has not already completed the first structure migration.
- **FR-006**: `migrate-structure.sh --apply` MUST treat `structureVersion` 1 as current and MUST be idempotent when re-run after a successful migration: when marker and generated navigation are already current, apply MUST report no-op and MUST NOT create a backup, write files, or regenerate generated zones.
- **FR-007**: Tier-0 navigation backfill MUST include completed or archived historical specs when their spec IDs can be normalized and joined to the roadmap-MOC spine, using the best existing durable target: `../../../specs/<dir>/SPEC-MOC.md` for version-gated specs, `../../../specs/<dir>/spec.md` for on-disk legacy specs without a gated MOC, or `../../../.specify/memory/spec.md#<section-slug>` for archive-memory-only specs.
- **FR-008**: Tier-0 navigation backfill MUST NOT stamp, move, rename, or otherwise mutate completed historical spec files outside generated navigation zones.
- **FR-009**: Every migration tier MUST skip specs listed as in-flight by a valid `.specify/feature.json` and MUST report a frozen/in-flight reason in dry-run output. `.specify/feature.json` parsing MUST be tri-state: missing file means no active frozen target is declared; a valid non-empty `feature_directory` is normalized relative to the repo root and matched by exact normalized path or the shared `moc_id_match`; a present malformed, unreadable, missing-key, non-string, empty, outside-repo, or non-normalizable file MUST be reported by dry-run and MUST block every mutating mode before backup or mutation.
- **FR-010**: The migration tooling MUST expose `relocate-process-artifacts.sh (--dry-run|--apply) --spec <spec-dir> [--repo-root <path>]` as the explicit Tier-2 codemod entry point for thawed legacy specs, and exactly one mode flag MUST be required per invocation.
- **FR-011**: `relocate-process-artifacts.sh --dry-run` MUST emit one deterministic JSON report that includes the exact proposed PROCESS move set, CONTRACT protections, marker stamp, generated-link/index updates, dirty-tree state, apply-blocked reason when dirty, and planned backup path without changing files.
- **FR-012**: Any apply mode with at least one pending mutation, including `migrate-structure.sh --apply` and `relocate-process-artifacts.sh --apply`, MUST create a forced, non-skippable backup outside the repository after all pre-mutation blocks pass and before the first mutation, using a run-specific path such as `/tmp/speckit-migration-backup-<STAMP>/`, and MUST print the backup path in command output.
- **FR-013**: Tier-2 relocation MUST move only root-relative PROCESS artifacts on the approved allow-list: `retrospective.md`, `*-report.md`, `uat-*`, `pr-review-packet.md`, legacy `peer-review-*`, `cleanup-report.md`, `analysis.md`, `evidence/`, `verification-evidence.md`, `design-concept.md`, `*-design-concept.md`, `workflow.md`, and `*-workflow.md`. Already-normalized `.process/**` files MUST be reported as no-op. For review packets, `pr-review-packet.md` is the canonical target name: a root `pr-review-packet.md` file or exactly one legacy root `peer-review-*` file MUST target `<spec-dir>/.process/pr-review-packet.md`; legacy `peer-review-*` basenames are not preserved after relocation. If multiple review-packet source files exist, or if the canonical target already exists while any root review-packet source remains, dry-run MUST report a target-path collision and apply MUST fail before mutation.
- **FR-014**: Tier-2 relocation MUST keep CONTRACT artifacts in place, including `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/**`, `checklists/**`, and `SPEC-MOC.md`; explicit CONTRACT protections MUST take precedence over allow-list filename matches.
- **FR-015**: Tier-2 relocation MUST normalize legacy spec-root evidence to `<spec-dir>/.process/evidence/verification-evidence.md`. Root `verification-evidence.md` and root `evidence/verification-evidence.md` are source candidates for that same canonical target. If exactly one source candidate exists and the target is absent, relocation MUST move it to the canonical target. If multiple source candidates exist, or if the canonical target already exists while any root source candidate remains, dry-run MUST report a target-path collision and apply MUST fail before mutation. If only the canonical target exists, relocation MUST report an already-normalized no-op. Root `evidence/` directories MUST move to `<spec-dir>/.process/evidence/` while preserving unrelated evidence files unless a target path would be overwritten.
- **FR-016**: Tier-2 relocation MUST require an existing regular `SPEC-MOC.md`, stamp only thawed migrated spec MOCs with bare integer `structureVersion: 1`, and fail before mutation when the target MOC is missing or non-regular; it MUST NOT stamp completed historical specs during Tier-0.
- **FR-017**: Tier-2 relocation MUST delegate to `generate-spec-index.sh` or the existing generated-zone writer after a successful apply so affected links and generated indexes are regenerated without a second renderer.
- **FR-018**: Tier-2 relocation MUST be idempotent after successful completion and MUST report no-op state on repeat runs without creating another backup, moving files, stamping `SPEC-MOC.md`, or regenerating links/index when no mutation is pending.
- **FR-019**: Scaffold and autopilot flows MUST suggest the Tier-2 codemod when they detect a thawed legacy spec with relocatable PROCESS artifacts.
- **FR-020**: Scaffold and autopilot flows MUST NOT automatically execute `relocate-process-artifacts.sh --dry-run` or `relocate-process-artifacts.sh --apply`.
- **FR-021**: Operator-facing JSON output MUST distinguish pending, applied, active-feature absent, active-feature invalid, skipped frozen/in-flight, skipped out-of-scope, protected CONTRACT, dirty-tree apply-blocked, backup, recovery, no-op current-state, and post-backup partial-failure results. Post-backup failures MUST distinguish marker-write, move, stamp, and generator failures from pre-mutation blocks; when a backup was created, the report MUST set recovery as available and name the backup path in the restore hint.
- **FR-022**: The implementation MUST preserve the two ordered internal increments: first Tier-1/Tier-0 repository migration, then Tier-2 relocation plus scaffold/autopilot registration.
- **FR-023**: Tier-0 navigation backfill MUST be implemented as durable, repo-marker-gated legacy-row discovery in `generate-spec-index.sh`, not as a one-time direct INDEX write by `migrate-structure.sh`. When `.specify/structure-version.json` has integer `structureVersion >= 1`, roadmap-MOC INDEX rendering MUST include ID-normalizable completed or archived historical specs that are not frozen/in-flight even if those historical specs have no per-spec `structureVersion`; when the repo marker is absent, malformed, unreadable, or below `1`, `generate-spec-index.sh` MUST preserve pre-marker behavior and skip legacy or non-version-marked SPEC-MOCs. This applies only to roadmap-MOC INDEX rows; per-spec SPEC-MOC generated zones remain unchanged.
- **FR-024**: `migrate-structure.sh --apply` MUST drive Tier-0 by creating or updating the repo-level structure marker and invoking or delegating to `generate-spec-index.sh`; it MUST NOT maintain a second INDEX renderer or patch roadmap-MOC INDEX rows directly.
- **FR-025**: Tier-2 relocation MUST use dual PROCESS anchors. PROCESS artifacts found under `--spec <spec-dir>` MUST move to `<spec-dir>/.process/`. Matching scaffold-time PROCESS artifacts in `docs/ai/specs/` whose basename matches the thawed spec ID, specifically `<SPEC-ID>-design-concept.md` and `<SPEC-ID>-workflow.md`, MUST move to `docs/ai/specs/.process/<same-basename>`. Tier-2 MUST NOT move unrelated `docs/ai/specs/` files, technical roadmaps, PRDs, already-current `.process/` files, or any CONTRACT artifact.
- **FR-026**: Scaffold and autopilot suggestion behavior MUST use static detection/reporting only: inspect target spec state and active-feature state directly, print the exact Tier-2 dry-run command `speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh --dry-run --spec specs/<spec-dir> --repo-root .` and clean-tree apply follow-up `speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh --apply --spec specs/<spec-dir> --repo-root .`, and never invoke `relocate-process-artifacts.sh`.
- **FR-027**: Migration candidate eligibility MUST be evaluated before Tier-0 roadmap row rendering, Tier-2 move discovery, and scaffold/autopilot suggestion emission. Eligible SpecKit candidates are current namespace-prefixed candidates whose first dash-delimited segment is `prsg` or `spec`, plus legacy numeric/spec candidates that can join to the roadmap-MOC spine under `moc_id_match` and are not date-first legacy namespaces. A candidate whose first dash-delimited segment is all-alpha and not `prsg` or `spec` MUST be reported with `items[].action` `skipped_out_of_scope` and reason `non_speckit_namespace`. A candidate whose basename or archive ID begins with a date-first prefix matching `YYYY`, `YYYY-MM`, or `YYYY-MM-DD` followed by end-of-string or `-` MUST be reported with reason `date_named_legacy_namespace`. Out-of-scope candidates MUST NOT emit roadmap-MOC INDEX rows, Tier-2 move/protection/collision candidates, or scaffold/autopilot relocation suggestions.
- **FR-028**: `speckit-upgrade` MUST tell operators the exact safe repository migration sequence for existing projects: run `speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh --dry-run --repo-root .` first, review pending/skipped/no-op output, clean the tree if needed, then run `speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh --apply --repo-root .` only when ready to mutate. `speckit-upgrade` MUST preserve its existing backup/restore guidance and MUST NOT auto-run Tier-2 relocation.
- **FR-029**: Every PRSG-011 operator-facing skill wording change for `speckit-upgrade`, `speckit-scaffold-spec`, `speckit-autopilot`, and the autopilot phase-execution reference MUST be mirrored behavior-equivalently between the Claude Code `skills/` surface and the Codex `codex-skills/` surface. Runtime-specific invocation syntax may differ, but the safety contract, exact migration command sequence, static Tier-2 suggestion behavior, skip/no-op wording, and no-auto-run guarantees MUST match.
- **FR-030**: Tier-0 legacy-row discovery MUST emit one generated roadmap-MOC INDEX row per eligible historical source file or archive-memory entry and MUST NOT special-case multi-ID or gappy legacy entries beyond PRSG-011 candidate eligibility and the shared `moc_id_match` join.
- **FR-031**: PRSG-011 migration work MUST preserve the PRSG-001 `.gitattributes` / reviewability-gate boundary: repository migration may report or ensure the repo-root `.gitattributes` `.process` collapse rule as a Tier-1 item, but MUST NOT make `reviewability-gate.sh`, `estimate-reviewable-loc.sh`, or related reviewability logic parse `.gitattributes`; the existing hardcoded `.process` exclusion remains the gate contract and is verified by existing L1/L4 guards.
- **FR-032**: `migrate-structure.sh` MUST treat live-project roadmap de-boilerplating of legacy reviewability exception phrases (`split exception`, `transition exception`, and `ratified exception`) as an idempotent Tier-1 report/apply item when those phrases appear in project roadmaps, while leaving plugin roadmap templates and PRSG-010 hatch-removal scope untouched.

### Reviewability Budget *(mandatory)*

- **Primary surface**: schema/migration
- **Secondary surfaces, if any**: docs/process, harness/adapter
- **Projected reviewable LOC**: approximately 440
- **Projected production files**: 6-8
- **Projected total files**: 15-22 including deterministic fixtures and parity coverage
- **Budget result**: warning accepted
- **Split decision**: Keep one spec because the repo marker, Tier-0 backfill, Tier-2 codemod, and operator suggestions are one migration feature. Tasks must preserve two internal vertical increments and implementation must revisit the split only if the accepted warning budget becomes unworkable.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, and rollback
  or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Repository Structure Marker**: Repo-level structure state with current value `structureVersion` 1 for the first migration; future structure migrations use later values.
- **Spec MOC Marker**: Per-spec frontmatter carrier for `structureVersion: 1`, stamped only when a legacy spec is explicitly thawed and Tier-2 relocation succeeds.
- **Migration Tier**: Ordered migration unit: Tier-1 repository edits, Tier-0 navigation backfill, and Tier-2 per-spec PROCESS relocation.
- **Tier-0 Link Target**: The durable Markdown target selected for a historical navigation row, chosen from version-gated `SPEC-MOC.md`, legacy `spec.md`, or archive memory section without creating or stamping a new MOC.
- **Artifact Classification**: The migration decision that classifies spec files as PROCESS artifacts that may move or CONTRACT artifacts that must remain visible.
- **PROCESS Anchor**: A `.process/` destination that receives moved process artifacts; PRSG-011 uses `<spec-dir>/.process/` for spec-root artifacts and `docs/ai/specs/.process/` for matching scaffold-time design/workflow artifacts.
- **Migration Report**: Deterministic operator-facing JSON output with fields for schema version, script, mode, repo root, spec directory when applicable, dirty-tree state, backup path, status, itemized decisions, and recovery instructions.
- **Forced Backup**: Non-optional restore point created outside the repository before mutation so an operator can recover if relocation or repository migration fails.
- **Frozen/In-Flight Spec**: A spec identified by `.specify/feature.json` that must be excluded from every migration tier until the operator thaws it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In fixture runs, 100% of dry-run executions leave the workspace byte-for-byte unchanged while reporting pending, skipped, and no-op migration decisions.
- **SC-002**: In fixture runs, 100% of mutation attempts on dirty worktrees fail before backup creation or mutation and return a clear operator-facing reason.
- **SC-003**: After Tier-0 apply, and on any later `generate-spec-index.sh` run with repo `structureVersion >= 1`, 100% of eligible ID-normalizable completed or archived historical specs not marked in-flight appear in generated roadmap-MOC navigation without receiving new stamps or file moves; marker-absent or malformed fixtures preserve the pre-marker legacy-skip behavior, and non-SpecKit/date-first candidates report `skipped_out_of_scope` without rows.
- **SC-004**: In Tier-2 relocation fixtures, 100% of PROCESS allow-list artifacts move to their correct anchor (`<spec-dir>/.process/` or `docs/ai/specs/.process/`), 0 CONTRACT or unrelated docs artifacts move, and every migrated spec MOC carries `structureVersion: 1`.
- **SC-005**: For legacy evidence fixtures, 100% of successful Tier-2 applies produce `<spec-dir>/.process/evidence/verification-evidence.md` without losing existing evidence content.
- **SC-006**: Scaffold/autopilot behavior checks show the Tier-2 codemod suggestion for 100% of thawed legacy specs with relocatable PROCESS artifacts and 0 automatic codemod executions.
- **SC-007**: Re-running apply after successful Tier-1/Tier-0 or Tier-2 migration reports a no-op current state in 100% of idempotency fixtures and creates no backup, file write, move, stamp, or generated-zone update when no mutation is pending.
- **SC-008**: Layer 3 skill fixtures and Layer 8 parity checks show that Claude Code and Codex operator-facing wording expose the same repository migration dry-run/apply sequence, Tier-2 suggestion command sequence, skip/no-op reasons, and no-auto-run guarantees.

## Assumptions

- Existing projects may contain completed or archived SpecKit specs that predate PRSG-001 through PRSG-010.
- Absence of `structureVersion` on a historical spec remains the legacy exemption signal until an operator explicitly thaws and migrates that spec.
- `.specify/feature.json` is the authoritative in-flight spec state for migration skipping.
- Migration logic does not infer frozen/in-flight state from the current branch name; `.specify/feature.json` is the only active-feature source for migration skipping.
- The repo-level structure marker is the state key that enables legacy-row discovery for roadmap-MOC INDEX rendering; Tier-0 is not a separate historical snapshot writer.
- Migration scripts source `speckit-pro/skills/speckit-autopilot/scripts/lib/moc-id-normalize.sh` directly for `moc_normalize` and `moc_id_match`; no duplicate ID grammar is introduced unless implementation proves the helper insufficient.
- Non-SpecKit and date-named legacy namespaces remain outside v1 migration scope by the deterministic eligibility rules in FR-027.
- Operator-facing script names and flags are part of the product contract for this migration feature.
- The exact command strings in FR-026 and FR-028 are operator-facing product contracts; tasks and implementation may substitute only the concrete `specs/<spec-dir>` value when a specific target spec is known.
- Migration scripts may support deterministic test-only environment overrides for backup root or timestamp so fixture expectations stay stable.
- The accepted reviewability warning remains valid as long as tasks and implementation preserve the two ordered internal vertical increments.
- The six PRD/roadmap defaults accepted by Design Concept Q1 are implementation guardrails: eager Tier-0 backfill, no Tier-0 stamps, one row per eligible historical file, non-SpecKit/date-first namespaces out of scope, a single integer repo marker, and no `.gitattributes` parser in reviewability logic.
- Deferred PRSG-001 scaffold artifact relocation is validated through deterministic PRSG-011 fixtures; implementation validation does not move real historical docs as test data.
