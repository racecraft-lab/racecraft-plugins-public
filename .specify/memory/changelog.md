# Project Memory: Merged Features Log

Append-only log of merged feature specifications archived into project memory.
Each entry records provenance and the git recovery commands for the raw spec
artifacts. The source `specs/<NNN>/` directory is removed only when the archive
cleanup gate records `safeToApplyCleanup=true`.

---

## Artifact relocation — tiering, .process/, collapse

[Source: specs/007-artifact-relocation]

- **Feature**: Artifact relocation — tiering, `.process/`, collapse
- **Roadmap ID**: PRSG-001 (PR-size governance roadmap) → spec `007-artifact-relocation`
- **Branch**: `007-artifact-relocation`
- **Spec path**: `specs/007-artifact-relocation/`
- **PR URL**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/111
- **Merge commit**: `ed043d5409d387f518cac5b8dc4595ed1d8f20c6`
- **Tree reference**: N/A (merge commit recorded above)
- **CI run URL**: N/A (not supplied)
- **Argos build/review URL**: N/A (no visual artifacts)
- **Metadata gates**: N/A (not supplied)
- **Artifact manifest**: N/A
- **Task completion**: 20 / 20 tasks complete
- **Archived**: 2026-06-05
- **Status**: Completed

### Summary of added behavior

Tiered every speckit-pro-authored spec artifact into CONTRACT (review-visible) vs
EXHAUST (scaffolding); redirected the three speckit-pro-authored EXHAUST artifacts
(design-concept doc, workflow file, UAT runbook) into `.process/` directories
(`docs/ai/specs/.process/` and `specs/<NNN>/.process/`) with no deletion; added a
repository-root `linguist-generated` collapse rule for `.process/` (plus an
idempotent consumer-side ensure-step that writes the same rule into consuming
projects); aligned the reviewability gate to exclude `.process/` lines from
diff-mode reviewable-LOC accounting; and added a Layer-1 lint guarding that every
collapse rule is scoped to `.process/`. Codex skill counterparts were mirrored
identically. Collapse is generated-only (no `-diff`); relocated artifacts stay
diffable. New-specs-only — no existing spec directory was migrated.

### Recovery Commands (raw spec artifacts)

```text
git show ed043d5409d387f518cac5b8dc4595ed1d8f20c6:specs/007-artifact-relocation/spec.md
git show ed043d5409d387f518cac5b8dc4595ed1d8f20c6:specs/007-artifact-relocation/plan.md
git show ed043d5409d387f518cac5b8dc4595ed1d8f20c6:specs/007-artifact-relocation/tasks.md
git show ed043d5409d387f518cac5b8dc4595ed1d8f20c6:specs/007-artifact-relocation/research.md
git show ed043d5409d387f518cac5b8dc4595ed1d8f20c6:specs/007-artifact-relocation/.process/uat-runbook.md
git show ed043d5409d387f518cac5b8dc4595ed1d8f20c6:specs/007-artifact-relocation/checklists/backward-compatibility.md
git show ed043d5409d387f518cac5b8dc4595ed1d8f20c6:specs/007-artifact-relocation/checklists/data-integrity.md
git show ed043d5409d387f518cac5b8dc4595ed1d8f20c6:specs/007-artifact-relocation/checklists/error-handling.md
git show ed043d5409d387f518cac5b8dc4595ed1d8f20c6:specs/007-artifact-relocation/checklists/requirements.md
```

To recover the entire directory at the merge commit:

```text
git checkout ed043d5409d387f518cac5b8dc4595ed1d8f20c6 -- specs/007-artifact-relocation
```

---

## Atomicity-test router (read-only classifier)

[Source: specs/prsg-007-atomicity-router]

- **Feature**: Atomicity-test router (read-only classifier)
- **Roadmap ID**: PRSG-007 (PR-size governance roadmap)
- **Branch**: `prsg-007-atomicity-router`
- **Spec path**: `specs/prsg-007-atomicity-router/`
- **PR URL**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/133
- **Merge commit**: `c918f229aa8205b2b9d19ae1fbdd7af18a42c4d6`
- **Tree reference**: N/A (merge commit recorded above)
- **CI run URL**: https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27214328113
- **Argos build/review URL**: N/A (no visual artifacts)
- **Metadata gates**: validate-plugins=pass; test(speckit-pro)=pass; validate-pr-title=pass; detect=pass; CodeQL=pass
- **Artifact manifest**: specs/prsg-007-atomicity-router/SPEC-MOC.md
- **Task completion**: 30 / 30 tasks complete
- **Archived**: 2026-06-09
- **Status**: Completed
- **Cleanup decision**: `safeToApplyCleanup=false`; active spec folder retained because Layer 4 dogfood/schema tests read this spec directly.

### Summary of added behavior

Added `atomicity-route.sh`, a read-only bash+jq classifier that emits route JSON
after Tasks/G5. The router distinguishes `split-PR`, `one-navigable-PR`,
reserved `branch-by-abstraction`, `single-atomic-PR`, and `out-of-scope`;
detects hard-atomic/releasability signatures; documents the route handoff in
autopilot workflow guidance; and adds Layer 4 fixtures plus Codex parity updates.

### Recovery Commands (raw spec artifacts)

```text
git show c918f229aa8205b2b9d19ae1fbdd7af18a42c4d6:specs/prsg-007-atomicity-router/spec.md
git show c918f229aa8205b2b9d19ae1fbdd7af18a42c4d6:specs/prsg-007-atomicity-router/plan.md
git show c918f229aa8205b2b9d19ae1fbdd7af18a42c4d6:specs/prsg-007-atomicity-router/tasks.md
git show c918f229aa8205b2b9d19ae1fbdd7af18a42c4d6:specs/prsg-007-atomicity-router/contracts/routing-decision.schema.json
git show c918f229aa8205b2b9d19ae1fbdd7af18a42c4d6:specs/prsg-007-atomicity-router/.process/uat-runbook.md
```

To recover the entire directory at the merge commit:

```text
git checkout c918f229aa8205b2b9d19ae1fbdd7af18a42c4d6 -- specs/prsg-007-atomicity-router
```

---

## Retro-migration: version marker + state-keyed backfill/relocate

[Source: specs/prsg-011-retro-migration]

- **Feature**: Retro-migration: version marker + state-keyed backfill/relocate
- **Roadmap ID**: PRSG-011 (PR-size governance roadmap)
- **Branch**: `prsg-011-retro-migration`
- **Spec path**: `specs/prsg-011-retro-migration/`
- **PR URL**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/132
- **Merge commit**: `6916ec43d2d4e3972d7e12425a05158f0b48ae3b`
- **Tree reference**: N/A (merge commit recorded above)
- **CI run URL**: https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27210286401
- **Argos build/review URL**: N/A (no visual artifacts)
- **Metadata gates**: validate-plugins=pass; test(speckit-pro)=pass; detect=pass; CodeQL=pass; validate-pr-title=fail on merged title
- **Artifact manifest**: specs/prsg-011-retro-migration/SPEC-MOC.md
- **Task completion**: 34 / 34 tasks complete
- **Archived**: 2026-06-09
- **Status**: Completed
- **Cleanup decision**: `safeToApplyCleanup=false`; source folder retained during this hygiene pass so cleanup can be handled together with the PRSG-007 test dependency.

### Summary of added behavior

Added deterministic migration tooling for existing SpecKit projects:
`migrate-structure.sh` for repo-level marker/backfill, `relocate-process-artifacts.sh`
for explicit Tier-2 PROCESS relocation, generator updates for legacy backfill,
and scaffold/autopilot/upgrade guidance that suggests but never auto-runs
relocation. The implementation mirrors the archive extension's dry-run/apply,
clean-tree, backup, and recovery-command safety pattern.

### Recovery Commands (raw spec artifacts)

```text
git show 6916ec43d2d4e3972d7e12425a05158f0b48ae3b:specs/prsg-011-retro-migration/spec.md
git show 6916ec43d2d4e3972d7e12425a05158f0b48ae3b:specs/prsg-011-retro-migration/plan.md
git show 6916ec43d2d4e3972d7e12425a05158f0b48ae3b:specs/prsg-011-retro-migration/tasks.md
git show 6916ec43d2d4e3972d7e12425a05158f0b48ae3b:specs/prsg-011-retro-migration/contracts/migrate-structure-cli.md
git show 6916ec43d2d4e3972d7e12425a05158f0b48ae3b:specs/prsg-011-retro-migration/contracts/relocate-process-artifacts-cli.md
git show 6916ec43d2d4e3972d7e12425a05158f0b48ae3b:specs/prsg-011-retro-migration/.process/uat-runbook.md
```

To recover the entire directory at the merge commit:

```text
git checkout 6916ec43d2d4e3972d7e12425a05158f0b48ae3b -- specs/prsg-011-retro-migration
```

---

## PRSG Archive Cleanup Application

[Source: .specify/memory/archive-reports/2026-06-09-prsg-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-09
- **Cleanup branch**: `codex/archive-apply-cleanup`
- **Cleanup command**: `git rm -r specs/prsg-007-atomicity-router specs/prsg-011-retro-migration`
- **Fixture-decoupling prerequisite**: PR #136 merged at `128e1927d0fa0ca6e7c0b1545d7b6547cdb4db9f`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/prsg-007-atomicity-router`, `specs/prsg-011-retro-migration`
- **Recovery**: use the PRSG-007 and PRSG-011 `git show` / `git checkout` commands recorded above.

The removed source folders were already archived in project memory. PR #136
vendored the PRSG-007 dogfood/schema fixture under
`tests/speckit-pro/layer4-scripts/fixtures/atomicity-route/dogfood-prsg-007/`,
so Layer 4 no longer depends on the live archived spec directory.

---

## Layer-planner: tasks.md to ordered increments

[Source: specs/prsg-008-layer-planner]

- **Feature**: Layer-planner: `tasks.md` to ordered increments
- **Roadmap ID**: PRSG-008 (PR-size governance roadmap)
- **Branch**: `prsg-008-layer-planner`
- **Spec path**: `specs/prsg-008-layer-planner/`
- **PR URL**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/138
- **Merge commit**: `deccd8a2a9916e11edfad43df8ceef95a756dc04`
- **Tree reference**: `c022c26fd113bfd366da53ef6c9b1fc6392f920e`
- **CI run URL**: https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27286755895
- **Argos build/review URL**: N/A (no visual artifacts)
- **Metadata gates**: Release=pass; CodeQL=pass; PR Checks=pass; test(speckit-pro)=pass; validate-plugins=pass; validate-pr-title=pass; detect=pass
- **Artifact manifest**: specs/prsg-008-layer-planner/SPEC-MOC.md
- **Task completion**: 45 / 45 tasks complete
- **Archived**: 2026-06-10
- **Status**: Completed
- **Cleanup decision**: `safeToApplyCleanup=true`; source folder removed after Layer 4 planner tests were decoupled from the live spec schema.

### Summary of added behavior

Added `plan-layers.sh`, a read-only Bash+`jq` planner that turns a feature
directory's `tasks.md` into a deterministic JSON layer plan for downstream
split-PR emission. The planner emits semantic increments, embedded tasks,
dependency order, source paths, file/test references, warnings, structured
errors, and counts-only advisory size metadata. Autopilot now runs the planner
only for PRSG-007 `split-PR` routes and stops before implementation on planner
errors.

### Recovery Commands (raw spec artifacts)

```text
git show deccd8a2a9916e11edfad43df8ceef95a756dc04:specs/prsg-008-layer-planner/spec.md
git show deccd8a2a9916e11edfad43df8ceef95a756dc04:specs/prsg-008-layer-planner/plan.md
git show deccd8a2a9916e11edfad43df8ceef95a756dc04:specs/prsg-008-layer-planner/tasks.md
git show deccd8a2a9916e11edfad43df8ceef95a756dc04:specs/prsg-008-layer-planner/contracts/plan-layers.output.md
git show deccd8a2a9916e11edfad43df8ceef95a756dc04:specs/prsg-008-layer-planner/contracts/plan-layers.schema.json
git show deccd8a2a9916e11edfad43df8ceef95a756dc04:specs/prsg-008-layer-planner/.process/uat-runbook.md
git show deccd8a2a9916e11edfad43df8ceef95a756dc04:specs/prsg-008-layer-planner/retrospective.md
```

To recover the entire directory at the merge commit:

```text
git checkout deccd8a2a9916e11edfad43df8ceef95a756dc04 -- specs/prsg-008-layer-planner
```

---

## PRSG-008 Archive Cleanup Application

[Source: .specify/memory/archive-reports/2026-06-10-prsg-008-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-10
- **Cleanup branch**: `codex/archive-prsg-008-hygiene`
- **Cleanup command**: `git rm -r specs/prsg-008-layer-planner`
- **Fixture-decoupling prerequisite**: `test-plan-layers.sh` now reads the vendored schema fixture at `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/contracts/plan-layers.schema.json`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/prsg-008-layer-planner`
- **Recovery**: use the PRSG-008 `git show` / `git checkout` commands recorded above.

The removed source folder was already archived in project memory. Layer 4
planner coverage remains active through fixture task files and the vendored
schema contract fixture under `tests/speckit-pro/layer4-scripts/fixtures/plan-layers/`.

---

## Multi-PR emission (post-implementation rewrite)

[Source: specs/prsg-009-multi-pr-emission]

- **Feature**: Multi-PR emission (post-implementation rewrite)
- **Roadmap ID**: PRSG-009 (PR-size governance roadmap)
- **Branch**: `prsg-009-multi-pr-emission`
- **Spec path**: `specs/prsg-009-multi-pr-emission/`
- **PR URL**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/145
- **Merge commit**: `a3361d50e3dfc5463fb2d5dbb2737a3525637a32`
- **Tree reference**: `c65ad8ae716d3f8cae94ac28026159eebd12a101`
- **PR Checks run URL**: https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27351131255
- **Release run URL**: https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27352284669
- **CodeQL run URLs**: https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27351042365; https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27351042214; https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/27352282130
- **Argos build/review URL**: N/A (no visual artifacts)
- **Metadata gates**: Release=pass; CodeQL=pass; PR Checks=pass; test(speckit-pro)=pass; validate-plugins=pass; validate-pr-title=pass; detect=pass
- **Artifact manifest**: specs/prsg-009-multi-pr-emission/SPEC-MOC.md
- **Task completion**: 47 / 47 tasks complete
- **Archived**: 2026-06-11
- **Status**: Completed
- **Cleanup decision**: `safeToApplyCleanup=true`; source folder removed after PRSG-009 contracts were preserved under the autopilot skill payload.

### Summary of added behavior

Added deterministic multi-PR emission for SpecKit post-implementation flows:
`multi-pr-emission.sh` consumes PRSG-008 layer plans and emits ordered Style B
slice PRs; `generate-pr-body.sh` supports bounded slice packets; `generate-spec-index.sh`
renders PRS schemaVersion 2 navigation rows; `restack.sh` provides dry-run-first
restack recovery; and Claude/Codex post-implementation references describe the
same scoped verification, resume, PRS, and restack contract.

### Recovery Commands (raw spec artifacts)

```text
git show a3361d50e3dfc5463fb2d5dbb2737a3525637a32:specs/prsg-009-multi-pr-emission/spec.md
git show a3361d50e3dfc5463fb2d5dbb2737a3525637a32:specs/prsg-009-multi-pr-emission/plan.md
git show a3361d50e3dfc5463fb2d5dbb2737a3525637a32:specs/prsg-009-multi-pr-emission/tasks.md
git show a3361d50e3dfc5463fb2d5dbb2737a3525637a32:specs/prsg-009-multi-pr-emission/contracts/multi-pr-emission-state.schema.json
git show a3361d50e3dfc5463fb2d5dbb2737a3525637a32:specs/prsg-009-multi-pr-emission/contracts/prs-v2.schema.json
git show a3361d50e3dfc5463fb2d5dbb2737a3525637a32:specs/prsg-009-multi-pr-emission/contracts/restack-output.schema.json
git show a3361d50e3dfc5463fb2d5dbb2737a3525637a32:specs/prsg-009-multi-pr-emission/contracts/slice-packet.schema.json
git show a3361d50e3dfc5463fb2d5dbb2737a3525637a32:specs/prsg-009-multi-pr-emission/.process/uat-runbook.md
git show a3361d50e3dfc5463fb2d5dbb2737a3525637a32:specs/prsg-009-multi-pr-emission/retrospective.md
git show a3361d50e3dfc5463fb2d5dbb2737a3525637a32:specs/prsg-009-multi-pr-emission/verify-tasks-report.md
```

To recover the entire directory at the merge commit:

```text
git checkout a3361d50e3dfc5463fb2d5dbb2737a3525637a32 -- specs/prsg-009-multi-pr-emission
```

---

## PRSG-009 Archive Cleanup Application

[Source: .specify/memory/archive-reports/2026-06-11-prsg-009-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-11
- **Cleanup branch**: `codex/prsg-009-archive-hygiene`
- **Cleanup command**: `git rm -r specs/prsg-009-multi-pr-emission`
- **Fixture-decoupling prerequisite**: PRSG-009 contract schemas now live at `speckit-pro/skills/speckit-autopilot/contracts/`, and `multi-pr-emission.sh` reports payload-included contract paths.
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/prsg-009-multi-pr-emission`
- **Recovery**: use the PRSG-009 `git show` / `git checkout` commands recorded above.

The removed source folder was already archived in project memory. Layer 4
multi-PR emission coverage remains active through payload-included contract
schemas and test fixtures under `tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/`.
