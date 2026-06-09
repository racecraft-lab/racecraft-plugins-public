# Implementation Plan: Retro-migration - Version Marker and State-Keyed Backfill/Relocate

**Branch**: `prsg-011-retro-migration` | **Date**: 2026-06-08 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/prsg-011-retro-migration/spec.md`

## Summary

Add an operator-safe migration path for existing SpecKit project structure. The
implementation keeps two ordered internal increments: first the repo-level
`structureVersion` marker plus Tier-0 navigation backfill, then explicit Tier-2
PROCESS relocation and scaffold/autopilot suggestion behavior. Dry-runs are
read-only, apply modes require a clean tree and forced backup, and generated
navigation continues to flow through `generate-spec-index.sh`.

## Technical Context

**Language/Version**: Bash 3.2-compatible shell scripts; Markdown skill docs; JSON via `jq`.

**Primary Dependencies**: `git`, `jq`, existing `moc-id-normalize.sh`, existing
`moc-frontmatter.sh`, existing `generate-spec-index.sh`.

**Storage**: Repository files only: `.specify/structure-version.json`,
`SPEC-MOC.md` frontmatter, generated MOC zones, `.specify/feature.json`, and
forced backup directories outside the repo.

**Testing**: Shell-based Layer 1/4 default suite, Layer 3 functional skill evals,
and Layer 8 Codex parity for mirrored skill prose changes.

**Target Platform**: Local SpecKit plugin/project worktrees on macOS/Linux shells
that can run bash, git, and jq.

**Project Type**: CLI/documentation plugin migration tooling.

**Performance Goals**: Stable, deterministic output for fixture comparison;
repository scans remain simple sorted file-tree scans; dry-run leaves the
workspace byte-for-byte unchanged.

**Constraints**: Dry-run modes are read-only and allowed on dirty trees. Apply
modes fail on dirty trees before backup or mutation. Every apply path with a
pending mutation creates a forced, non-skippable backup before mutation and
prints the backup path; already-current apply reruns report no-op without
creating a backup. Post-backup partial failures must report the created backup
path and restore hint. Tier-0 does not move or stamp historical spec files.
Tier-2 moves only approved PROCESS artifacts and keeps CONTRACT artifacts in
place. `.specify/feature.json` is the only in-flight source and every tier skips
valid in-flight specs. Tier-0 emits one generated navigation row per eligible
historical source file or archive-memory entry and does not special-case
multi-ID/gappy legacy inputs beyond shared candidate eligibility and
`moc_id_match`. PRSG-011 may ensure or report the repo-root `.gitattributes`
`.process` rule, but reviewability logic keeps the existing hardcoded `.process`
predicate and does not parse `.gitattributes`.

**Scale/Scope**: Existing SpecKit repositories with multiple completed,
archived, in-flight, or thawed legacy specs. Non-SpecKit and date-named legacy
namespaces stay outside v1 migration scope.

**Reviewability Budget**: Primary surface = schema/migration; secondary surfaces
= docs/process and harness/adapter; projected reviewable LOC approximately 440;
projected production files 6-8; projected total files 15-22; budget result =
warning accepted by Grill Me Q11.

## Declared File Operations

- NEW speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh
- NEW speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh
- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh
- MODIFIED speckit-pro/skills/speckit-upgrade/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-upgrade/SKILL.md
- MODIFIED speckit-pro/skills/speckit-scaffold-spec/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md
- MODIFIED speckit-pro/skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/phase-execution.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md
- NEW tests/speckit-pro/layer4-scripts/test-migrate-structure.sh
- NEW tests/speckit-pro/layer4-scripts/test-relocate-process-artifacts.sh
- MODIFIED tests/speckit-pro/layer3-functional/evals/speckit-scaffold-spec-evals.json
- MODIFIED tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json
- MODIFIED tests/speckit-pro/layer3-functional/codex-evals/speckit-scaffold-spec-evals.json
- MODIFIED tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Plan result | Evidence |
|-----------|-------------|----------|
| I. Plugin Structure Compliance | PASS | New scripts stay under the existing `speckit-pro` skill script tree; skill behavior changes stay in existing skill and Codex mirror files. |
| II. Script Safety | PASS | New scripts will start with `#!/usr/bin/env bash`, use `set -euo pipefail`, quote paths, and use `jq` for JSON rather than text parsing JSON. |
| III. Semantic Versioning | PASS | No manual plugin version edit is planned; release versioning remains release-please scope. |
| IV. Test Coverage Before Merge | PASS | Layer 4 script tests cover dry-run, apply blocking, idempotency, move allow-list, dual anchors, evidence normalization, in-flight skip, and ID normalization. Layer 3 and Layer 8 cover skill/Codex mirror behavior. |
| V. Conventional Commits | PASS | No implementation commit is produced by this phase; future commits must use a scoped conventional commit. |
| VI. KISS, Simplicity & YAGNI | PASS | The design reuses the existing ID normalizer, frontmatter reader, and generated-zone writer. No duplicate INDEX renderer or speculative ID wrapper is introduced. |

**Re-check after Phase 1 design**: PASS. Contracts and data model preserve the
same helper reuse, dry-run/apply split, and two-increment implementation order.

**Reviewability split decision**: Keep PRSG-011 as one spec because the repo
marker, Tier-0 backfill, Tier-2 relocation, and operator suggestions are one
migration feature. Implementation tasks must preserve two internal vertical
increments and stop for a split if the accepted warning becomes unworkable.

**PR review packet source**: PR body must cover what changed, why, non-goals,
review order, scope budget, traceability, verification evidence, known gaps, and
rollback or feature-flag notes. Traceability must map major requirements to
changed files and verification evidence.

## Project Structure

### Documentation (this feature)

```text
specs/prsg-011-retro-migration/
├── SPEC-MOC.md
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── migrate-structure-cli.md
│   ├── migration-report-json.md
│   └── relocate-process-artifacts-cli.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
speckit-pro/
├── skills/
│   ├── speckit-autopilot/
│   │   ├── SKILL.md
│   │   ├── references/phase-execution.md
│   │   └── scripts/
│   │       ├── generate-spec-index.sh
│   │       ├── migrate-structure.sh
│   │       ├── relocate-process-artifacts.sh
│   │       └── lib/
│   │           ├── moc-frontmatter.sh
│   │           └── moc-id-normalize.sh
│   ├── speckit-scaffold-spec/SKILL.md
│   └── speckit-upgrade/SKILL.md
├── codex-skills/
│   ├── speckit-autopilot/
│   │   ├── SKILL.md
│   │   └── references/phase-execution-codex.md
│   ├── speckit-scaffold-spec/SKILL.md
│   └── speckit-upgrade/SKILL.md
tests/speckit-pro/
├── layer4-scripts/
│   ├── test-migrate-structure.sh
│   └── test-relocate-process-artifacts.sh
└── layer3-functional/
├── evals/
└── codex-evals/
```

**Structure Decision**: Use existing plugin script, skill, Codex mirror, and
test locations. Do not introduce a separate migration package, generated-zone
renderer, or ID grammar helper unless implementation proves an existing helper
cannot satisfy a contract fixture.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Reviewability warning accepted | PRSG-011 touches schema/migration, docs/process, and harness/adapter surfaces in one migration feature. | Splitting before planning would decouple the repo marker/Tier-0 state key from the Tier-2 relocation and operator suggestion behavior that depends on it. |

## Phase 0 Research Results

Research is captured in [research.md](./research.md). All implementation
tradeoffs are resolved for planning: generated navigation stays centralized in
`generate-spec-index.sh`, ID matching reuses `moc-id-normalize.sh`, JSON output
uses deterministic compact `jq`, and apply modes create forced backups after the
clean-tree check and before mutation.

## Phase 1 Design Results

- Data model: [data-model.md](./data-model.md)
- Shared report contract: [contracts/migration-report-json.md](./contracts/migration-report-json.md)
- Repository migration CLI: [contracts/migrate-structure-cli.md](./contracts/migrate-structure-cli.md)
- Tier-2 relocation CLI: [contracts/relocate-process-artifacts-cli.md](./contracts/relocate-process-artifacts-cli.md)
- Operator quickstart: [quickstart.md](./quickstart.md)

## Implementation Increments

### Increment 1: Tier-1/Tier-0 Repository Migration

1. Add `migrate-structure.sh` with exact mode parsing, repo root resolution,
   active-feature tri-state validation, dirty-tree apply block, no-op detection
   before backup, forced backup for pending mutations, marker write,
   post-backup recovery reporting, and delegation to `generate-spec-index.sh`.
2. Extend `generate-spec-index.sh` so roadmap-MOC INDEX rendering includes
   eligible ID-normalizable completed or archived historical specs only when
   repo `.specify/structure-version.json` carries integer
   `structureVersion >= 1`, emitting one generated row per eligible historical
   source file or archive-memory entry without special-casing multi-ID/gappy
   legacy entries, while reporting non-SpecKit alpha namespaces and date-first
   legacy namespaces as `skipped_out_of_scope`.
3. Add Layer 4 fixtures for dry-run no-mutation, dirty apply block, marker
   absent/malformed behavior, idempotency, frozen/in-flight skip, archive-memory
   target selection, one-row-per-file multi-ID/gappy legacy inputs, ID
   normalization false-join protection, live-project roadmap de-boilerplate as a
   Tier-1 report/apply item, `.gitattributes`/reviewability-gate separation, and
   out-of-scope non-SpecKit/date-first namespace skip reporting with no Tier-0 row.

### Increment 2: Tier-2 Relocation and Operator Suggestions

1. Add `relocate-process-artifacts.sh` with spec target resolution, active-feature
   skip/block behavior, out-of-scope candidate no-op reporting, allow-list
   classification, CONTRACT protection, dual PROCESS anchors, evidence
   normalization into
   `<spec-dir>/.process/evidence/verification-evidence.md`, review-packet
   canonicalization into `<spec-dir>/.process/pr-review-packet.md`, collision
   detection for competing legacy/canonical sources, no-op detection before
   backup, forced backup for pending mutations, git moves, `SPEC-MOC.md` stamp,
   post-backup recovery reporting, and index regeneration.
2. Update `speckit-upgrade` and its Codex mirror to preserve the existing
   backup/restore language and print the exact safe repository migration
   sequence from FR-028: dry-run first
   (`speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh --dry-run --repo-root .`),
   then clean-tree apply
   (`speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh --apply --repo-root .`)
   after the operator reviews pending/skipped/no-op output.
3. Update scaffold and autopilot skills plus Codex mirrors to statically detect
   thawed legacy specs with relocatable PROCESS artifacts and print the exact
   Tier-2 dry-run and clean-tree apply follow-up from FR-026. They must not
   execute either relocation command or suggest relocation for out-of-scope
   non-SpecKit/date-first namespaces.
4. Keep every `skills/` operator-facing wording edit behavior-equivalent in the
   matching `codex-skills/` mirror in the same implementation increment. Runtime
   syntax may differ, but safe-command sequence, skip/no-op wording, and no-auto-run
   guarantees must match.
5. Add Layer 4 relocation fixtures, Layer 3 skill behavior fixtures, and Layer 8
   parity checks for mirrored skill prose, including deterministic PRSG-001
   deferred scaffold artifact fixtures, no move candidates, no suggestions for
   out-of-scope namespaces, and the exact safe-command sequences from
   FR-026/FR-028.

## Gate G3

- Architecture approved: PASS
- Constitution gates pass: PASS
- Dependencies identified: PASS
- No unresolved technical unknowns in research.md: PASS
