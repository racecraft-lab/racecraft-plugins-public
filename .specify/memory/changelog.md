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

---

## Harden the hatch + O5 monster-epics

[Source: specs/prsg-010-harden-the-hatch]

- **Feature**: Harden the hatch + O5 monster-epics
- **Roadmap ID**: PRSG-010 (PR-size governance roadmap)
- **Branch**: `prsg-010-harden-the-hatch`
- **Spec path**: `specs/prsg-010-harden-the-hatch/`
- **PR URLs**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/149; https://github.com/racecraft-lab/racecraft-plugins-public/pull/150; https://github.com/racecraft-lab/racecraft-plugins-public/pull/151; https://github.com/racecraft-lab/racecraft-plugins-public/pull/152; https://github.com/racecraft-lab/racecraft-plugins-public/pull/153; https://github.com/racecraft-lab/racecraft-plugins-public/pull/154; https://github.com/racecraft-lab/racecraft-plugins-public/pull/155
- **Final merge commit**: `8b59fe55128ee2a835c64003662ce0674cac4edf`
- **Tree reference**: `08f3e8dc7cfa463a8b9e9492812bec7c1e4474a9`
- **Final PR head commit**: `569b0e4cb14f4e3b958d5261a1a8ffe06704bfe6`
- **Artifact manifest**: specs/prsg-010-harden-the-hatch/SPEC-MOC.md
- **Task completion**: 57 / 57 tasks complete
- **Archived**: 2026-06-11
- **Status**: Completed
- **Cleanup decision**: `safeToApplyCleanup=true`; source folder removed after PRSG-010 contracts were preserved under the autopilot skill payload.

### Summary of added behavior

Added the final reviewability backstop and re-slicing packet, high-confidence
contextual router probes, O5 parent/child topology validation and status rollup,
and parity/template cleanup so generated education no longer emits live
copy-pasteable exception override lines.

### PR Stack

| PR | Merge commit | Scope |
|----|--------------|-------|
| #149 | `fcb360280e4f3281d233741574c98b092ae29796` | PRSG-010 scaffold and workflow foundation |
| #150 | `6a9cbe2d73043c8443f550d6423a4f726caebfaa` | Final backstop core |
| #151 | `57c3ab24c5fd84eb880086fad21a74d0b9ec3e7c` | Final hatch guidance and safety check |
| #152 | `965a3ff95ed1fefdb45c93f654bc5d9594b26258` | Contextual router probes |
| #153 | `d29502a0e40109a3c09506f34fea6d4d3fb5dc8a` | O5 topology core |
| #154 | `6d9cd5ec406fddbdbd684bf0df7add987e59f722` | O5 scaffold/status guidance |
| #155 | `8b59fe55128ee2a835c64003662ce0674cac4edf` | Parity, safety checks, and polish |

### Recovery Commands (raw spec artifacts)

```text
git show 8b59fe55128ee2a835c64003662ce0674cac4edf:specs/prsg-010-harden-the-hatch/spec.md
git show 8b59fe55128ee2a835c64003662ce0674cac4edf:specs/prsg-010-harden-the-hatch/plan.md
git show 8b59fe55128ee2a835c64003662ce0674cac4edf:specs/prsg-010-harden-the-hatch/tasks.md
git show 8b59fe55128ee2a835c64003662ce0674cac4edf:specs/prsg-010-harden-the-hatch/research.md
git show 8b59fe55128ee2a835c64003662ce0674cac4edf:specs/prsg-010-harden-the-hatch/data-model.md
git show 8b59fe55128ee2a835c64003662ce0674cac4edf:specs/prsg-010-harden-the-hatch/quickstart.md
git show 8b59fe55128ee2a835c64003662ce0674cac4edf:specs/prsg-010-harden-the-hatch/SPEC-MOC.md
git show 8b59fe55128ee2a835c64003662ce0674cac4edf:specs/prsg-010-harden-the-hatch/contracts/final-reviewability-gate-state.schema.json
git show 8b59fe55128ee2a835c64003662ce0674cac4edf:specs/prsg-010-harden-the-hatch/contracts/o5-parent-manifest.schema.json
git show 8b59fe55128ee2a835c64003662ce0674cac4edf:specs/prsg-010-harden-the-hatch/contracts/reslicing-packet.schema.json
git show 8b59fe55128ee2a835c64003662ce0674cac4edf:specs/prsg-010-harden-the-hatch/contracts/routing-decision.schema.json
```

To recover the entire directory at the final merge commit:

```text
git checkout 8b59fe55128ee2a835c64003662ce0674cac4edf -- specs/prsg-010-harden-the-hatch
```

---

## PRSG-010 Archive Cleanup Application

[Source: .specify/memory/archive-reports/2026-06-11-prsg-010-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-11
- **Cleanup branch**: `codex/prsg-010-archive-hygiene`
- **Cleanup command**: `git rm -r specs/prsg-010-harden-the-hatch`
- **Fixture-decoupling prerequisite**: PRSG-010 contract schemas live at `speckit-pro/skills/speckit-autopilot/contracts/`, and Layer 4/Layer 8 tests cover final-backstop, contextual-router, O5, and parity behavior without the live spec folder.
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/prsg-010-harden-the-hatch`
- **Recovery**: use the PRSG-010 `git show` / `git checkout` commands recorded above.

The removed source folder was already archived in project memory. Layer 4
coverage remains active through payload-included contract schemas and fixtures
under `tests/speckit-pro/layer4-scripts/fixtures/`.

---

## Vertical-slice sizing heuristics in PRD/grill-me

[Source: specs/prsg-005-slice-sizing-heuristics]

- **Feature**: Vertical-slice sizing heuristics in PRD/grill-me
- **Roadmap ID**: PRSG-005 (PR-size governance roadmap)
- **Branch**: `prsg-005-slice-sizing-heuristics`
- **Spec path**: `specs/prsg-005-slice-sizing-heuristics/`
- **PR URL**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/120
- **Merge commit**: `a4e930bc8989b84910b8840abb193f91bb1ae5b9`
- **Tree reference**: `c3dd8a196dde9f1ddb987560f7bd95573500a373`
- **Final PR head commit**: `6bc94585626ce0e6195f93c31acd0cf2fb86f6c5`
- **Artifact manifest**: specs/prsg-005-slice-sizing-heuristics/SPEC-MOC.md
- **Task completion**: 20 / 23 tasks complete; remaining Layer 2, Layer 3, and
  Layer 8 follow-ups were developer-local evidence items, not merge blockers.
- **Archived**: 2026-06-12
- **Status**: Completed
- **Cleanup decision**: `safeToApplyCleanup=true`; source folder removed after
  PR #120 merge provenance and recovery commands were recorded.

### Summary of added behavior

Added advisory vertical-slice sizing at PRD and grill-me scoping time, with one
shared SPIDR/INVEST/vertical-slicing reference, one shared deterministic
estimator, and mirrored Claude/Codex skill behavior.

### Recovery Commands (raw spec artifacts)

```text
git show a4e930bc8989b84910b8840abb193f91bb1ae5b9:specs/prsg-005-slice-sizing-heuristics/spec.md
git show a4e930bc8989b84910b8840abb193f91bb1ae5b9:specs/prsg-005-slice-sizing-heuristics/plan.md
git show a4e930bc8989b84910b8840abb193f91bb1ae5b9:specs/prsg-005-slice-sizing-heuristics/tasks.md
git show a4e930bc8989b84910b8840abb193f91bb1ae5b9:specs/prsg-005-slice-sizing-heuristics/data-model.md
git show a4e930bc8989b84910b8840abb193f91bb1ae5b9:specs/prsg-005-slice-sizing-heuristics/quickstart.md
git show a4e930bc8989b84910b8840abb193f91bb1ae5b9:specs/prsg-005-slice-sizing-heuristics/SPEC-MOC.md
git show a4e930bc8989b84910b8840abb193f91bb1ae5b9:specs/prsg-005-slice-sizing-heuristics/contracts/estimate-spec-size.md
git checkout a4e930bc8989b84910b8840abb193f91bb1ae5b9 -- specs/prsg-005-slice-sizing-heuristics
```

---

## Non-stopping reviewability markers

[Source: specs/prsg-013-reviewability-markers]

- **Feature**: Non-stopping reviewability markers
- **Roadmap ID**: PRSG-013 (PR-size governance roadmap)
- **Branch**: `prsg-013-reviewability-markers`
- **Spec path**: `specs/prsg-013-reviewability-markers/`
- **PR URL**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/157
- **Merge commit**: `6af4e714077c8ebc9fa71466bee2461bc8652930`
- **Tree reference**: `d97e2bce53b322f14cf5808e86697c1bdd27c7a6`
- **Final PR head commit**: `cb719a078b9fa0e928ada6a7680c56f44408c06e`
- **Artifact manifest**: specs/prsg-013-reviewability-markers/SPEC-MOC.md
- **Task completion**: 45 / 45 tasks complete.
- **Archived**: 2026-06-12
- **Status**: Completed
- **Cleanup decision**: `safeToApplyCleanup=true`; source folder removed after
  PR #157 merge provenance and recovery commands were recorded.

### Summary of added behavior

Turned reviewability sizing blocks into PR-marker inputs instead of
implementation stops, persisted marker plans with source fingerprints, added
marker-aware final backstop and multi-PR emission paths, and recorded guidance
for marker-ordered implementation and evidence.

### Recovery Commands (raw spec artifacts)

```text
git show 6af4e714077c8ebc9fa71466bee2461bc8652930:specs/prsg-013-reviewability-markers/spec.md
git show 6af4e714077c8ebc9fa71466bee2461bc8652930:specs/prsg-013-reviewability-markers/plan.md
git show 6af4e714077c8ebc9fa71466bee2461bc8652930:specs/prsg-013-reviewability-markers/tasks.md
git show 6af4e714077c8ebc9fa71466bee2461bc8652930:specs/prsg-013-reviewability-markers/research.md
git show 6af4e714077c8ebc9fa71466bee2461bc8652930:specs/prsg-013-reviewability-markers/data-model.md
git show 6af4e714077c8ebc9fa71466bee2461bc8652930:specs/prsg-013-reviewability-markers/quickstart.md
git show 6af4e714077c8ebc9fa71466bee2461bc8652930:specs/prsg-013-reviewability-markers/SPEC-MOC.md
git show 6af4e714077c8ebc9fa71466bee2461bc8652930:specs/prsg-013-reviewability-markers/contracts/marker-split-result.schema.json
git show 6af4e714077c8ebc9fa71466bee2461bc8652930:specs/prsg-013-reviewability-markers/contracts/pr-marker-plan.schema.json
git checkout 6af4e714077c8ebc9fa71466bee2461bc8652930 -- specs/prsg-013-reviewability-markers
```

---

## PRSG-005 and PRSG-013 Archive Cleanup Application

[Source: .specify/memory/archive-reports/2026-06-12-prsg-005-013-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-12
- **Cleanup branch**: `codex/spec-hygiene-prsg-013-005`
- **Cleanup command**: `git rm -r specs/prsg-005-slice-sizing-heuristics specs/prsg-013-reviewability-markers`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/prsg-005-slice-sizing-heuristics`, `specs/prsg-013-reviewability-markers`
- **Recovery**: use the `git show` / `git checkout` commands recorded above.

The removed source folders were already merged and archived in project memory.
PRSG-005 behavior remains covered through shipped skill guidance and estimator
tests; PRSG-013 behavior remains covered through payload-included schemas and
Layer 4 marker fixtures.

---

## Merged Active-Spec Archive Hygiene Sweep

[Source: .specify/memory/archive-reports/2026-06-13-merged-specs-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-13
- **Cleanup branch**: `codex/archive-merged-specs-hygiene`
- **Cleanup command**: `git rm -r specs/001-repository-foundation specs/002-pr-checks-workflow specs/003-release-automation specs/004-integration-verification specs/006a-uat-skeleton specs/prsg-002-moc-templates specs/prsg-003-spec-index specs/prsg-004-roadmap-moc-home-note specs/prsg-006-reviewability-budget specs/prsg-012-reviewer-ready-pr-packet-contract`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/001-repository-foundation`, `specs/002-pr-checks-workflow`, `specs/003-release-automation`, `specs/004-integration-verification`, `specs/006a-uat-skeleton`, `specs/prsg-002-moc-templates`, `specs/prsg-003-spec-index`, `specs/prsg-004-roadmap-moc-home-note`, `specs/prsg-006-reviewability-budget`, `specs/prsg-012-reviewer-ready-pr-packet-contract`

### Provenance

| Spec | PR | Merge commit | Tree reference | Task completion |
|------|----|--------------|----------------|-----------------|
| `specs/001-repository-foundation` | #1 | `b10d40f0d5c54ccc4a3d29ebe776a1bd74bae4c2` | `0bc6ef47bf24f37f63a8a3effec2b533ca93c2ef` | 30 / 30 |
| `specs/002-pr-checks-workflow` | #2 | `030c47a6ae7f032d96a158883b4b6bfde2f5ef19` | `2143519cda2908838e8e1b3f5689b4233c9eccea` | 16 / 16 |
| `specs/003-release-automation` | #3 | `5a52abebf05941eca0905e2ba61b0b9e66b374c1` | `2468efe7e9d400080acdf38fb4fd1af62b40322e` | 11 / 11 |
| `specs/004-integration-verification` | #5 | `c11d9291a13b984cfca467a3418ac482e566c49b` | `acd61703cfd47e129c43d7895a848cf11e36623b` | 0 / 31 recorded; merged PR is authoritative |
| `specs/006a-uat-skeleton` | #99 | `dcd1208a57780abbb9c9d204b3c096be3a7da188` | `df5f8a07aae0005185f82e557994e592edd3872d` | 28 / 28 |
| `specs/prsg-002-moc-templates` | #116 | `3e4be3e9901c466040809a211af8aa0ec0c6935b` | `c6cc7c63dabce308d1a15552872ca7958564f25d` | 24 / 24 |
| `specs/prsg-003-spec-index` | #121 | `339fbaadc299f3593392937cf563b33e5d44627a` | `6cbdf0e7279c39641d9249524cb209a44d41e2df` | 25 / 25 |
| `specs/prsg-004-roadmap-moc-home-note` | #129 | `60018313eb768b8339cf60737e9b9965cc9465b8` | `1bf3942b2c88fdb959cf6c54001b82c1c402feef` | 23 / 24; remaining PR packet task was not a merge blocker |
| `specs/prsg-006-reviewability-budget` | #119 | `9d4b94867d2ad9e47a3b64b7551fa6d86ce8cf53` | `8f0058ff12832c0c08529cdf97295eba20cd9954` | 35 / 35 |
| `specs/prsg-012-reviewer-ready-pr-packet-contract` | #164-#168 | `896ab42f443e330d095f1c08be681cc8c9bca995` | `4c50790bf3009149c07eeba92771f5b2a501995d` | 56 / 56 |

### PRSG-012 PR Stack

| PR | Merge commit | Scope |
|----|--------------|-------|
| #164 | `b57e2992b8e304b0e649398b86f7b495aada3252` | Add reviewer packet validation contract |
| #165 | `7580f08fc78877f21a71c72ff4a6a2781c9017ce` | Generate packet-owned conventional PR titles |
| #166 | `d6685c44ae706370ec91977831d3d1149c299b65` | Render plain-English reviewer PR body evidence |
| #167 | `302d73a884d7fbe10964839f17460aec91f04dc1` | Block invalid PR packets before creation |
| #168 | `896ab42f443e330d095f1c08be681cc8c9bca995` | Protect editable PR body prose |

### Recovery Commands

```text
git checkout b10d40f0d5c54ccc4a3d29ebe776a1bd74bae4c2 -- specs/001-repository-foundation
git checkout 030c47a6ae7f032d96a158883b4b6bfde2f5ef19 -- specs/002-pr-checks-workflow
git checkout 5a52abebf05941eca0905e2ba61b0b9e66b374c1 -- specs/003-release-automation
git checkout c11d9291a13b984cfca467a3418ac482e566c49b -- specs/004-integration-verification
git checkout dcd1208a57780abbb9c9d204b3c096be3a7da188 -- specs/006a-uat-skeleton
git checkout 3e4be3e9901c466040809a211af8aa0ec0c6935b -- specs/prsg-002-moc-templates
git checkout 339fbaadc299f3593392937cf563b33e5d44627a -- specs/prsg-003-spec-index
git checkout 60018313eb768b8339cf60737e9b9965cc9465b8 -- specs/prsg-004-roadmap-moc-home-note
git checkout 9d4b94867d2ad9e47a3b64b7551fa6d86ce8cf53 -- specs/prsg-006-reviewability-budget
git checkout 896ab42f443e330d095f1c08be681cc8c9bca995 -- specs/prsg-012-reviewer-ready-pr-packet-contract
```

The detailed per-file `git show` recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-13-merged-specs-post-merge-hygiene.md`.

### Fixture Decoupling

- PRSG-012 PR body generation now reads a committed feature fixture under
  `tests/speckit-pro/layer4-scripts/fixtures/prsg-012-feature/`.
- PRSG-012 marker-emission regression now reads committed marker-plan fixtures
  under `tests/speckit-pro/layer4-scripts/fixtures/marker-plan/`.
- MOC orphan/stale-index lints now use committed MOC fixtures for former
  PRSG-002 dogfood assertions.

### Verification

- Pre-cleanup focused tests passed: `test-generate-pr-body.sh` `85/85`,
  `test-multi-pr-emission.sh` `156/156`, MOC stale-index `11/11`, MOC orphan
  `29/29`.
- Post-cleanup `bash tests/speckit-pro/run-all.sh` passed `2915/2915`
  (Layer 1 structural `549/549`, Codex structural `430/430`, Layer 4 script
  unit `1746/1746`, Layer 5 tool scoping `190/190`).

---

## DOC-001 Interactive Documentation Framework and IA Spike

[Source: .specify/memory/archive-reports/2026-06-13-doc-001-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-13
- **Cleanup branch**: `codex/doc-001-post-merge-hygiene`
- **Cleanup command**: `git rm -r specs/doc-001-static-docs-framework-and-ia-spike`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/doc-001-static-docs-framework-and-ia-spike`

### Provenance

| Spec | PR | Merge commit | Tree reference | Task completion |
|------|----|--------------|----------------|-----------------|
| `specs/doc-001-static-docs-framework-and-ia-spike` | #163 | `4ddc1a5ce24de50d07695669fce34709c60147b3` | `a9e02aa9b15818c4a6828553f9dd4362bd1a43ca` | 28 / 28 |

### Summary

DOC-001 selected Astro/Starlight as the default DOC-002 docs-site stack, kept
Docusaurus/MDX as the first fallback for true hard blockers, recorded pnpm and
docs-site command roles as report-only guidance, and produced the 11-route
Diataxis IA skeleton. The durable review artifact is
`docs/ai/research/interactive-documentation-framework-spike.md`.

### Recovery Commands

```text
git show 4ddc1a5ce24de50d07695669fce34709c60147b3:specs/doc-001-static-docs-framework-and-ia-spike/spec.md
git show 4ddc1a5ce24de50d07695669fce34709c60147b3:specs/doc-001-static-docs-framework-and-ia-spike/plan.md
git show 4ddc1a5ce24de50d07695669fce34709c60147b3:specs/doc-001-static-docs-framework-and-ia-spike/tasks.md
git show 4ddc1a5ce24de50d07695669fce34709c60147b3:specs/doc-001-static-docs-framework-and-ia-spike/SPEC-MOC.md
git checkout 4ddc1a5ce24de50d07695669fce34709c60147b3 -- specs/doc-001-static-docs-framework-and-ia-spike
```

The detailed per-file `git show` recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-13-doc-001-post-merge-hygiene.md`.

---

## DOC-002 Unified Landing Page and IA Shell

[Source: .specify/memory/archive-reports/2026-06-14-doc-002-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-14
- **Cleanup branch**: `codex/doc-002-post-merge-hygiene`
- **Cleanup command**: `git rm -r specs/doc-002-unified-landing-page-and-ia-shell`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/doc-002-unified-landing-page-and-ia-shell`

### Provenance

| PR | Title | Merge commit |
|----|-------|--------------|
| #173 | `feat(speckit-pro): Add docs site foundation` | `0bb5e6b5f7589a7872819a2fe3c0ddb583e63565` |
| #174 | `feat(speckit-pro): Add landing page platform choice` | `ce59667582a4bd656eface86a850293b98d50ad5` |
| #175 | `feat(speckit-pro): Add IA route shell navigation` | `e52035516f3434b82d728e32d3834f24400140cd` |
| #176 | `feat(speckit-pro): Add docs validation and review evidence` | `73ad7c97a44b036be9247d8e5910587ce61d9ae6` |
| #177 | `fix(autopilot): require reslice continuation` | `4fc5f81363e5b99e71d298390785d4d4c70d86ae` |

### Summary

DOC-002 added the Astro/Starlight `docs-site/` shell, all 11 IA route shells,
landing page platform choice, source-vs-payload explanation, Pages-ready config,
and docs-site validation scripts. PR #177 is included in the completion record
because it fixed the autopilot continuation bug that had paused final PR packet
generation after reviewability backstop.

### Recovery Commands

```text
git show 4fc5f81363e5b99e71d298390785d4d4c70d86ae:specs/doc-002-unified-landing-page-and-ia-shell/spec.md
git show 4fc5f81363e5b99e71d298390785d4d4c70d86ae:specs/doc-002-unified-landing-page-and-ia-shell/plan.md
git show 4fc5f81363e5b99e71d298390785d4d4c70d86ae:specs/doc-002-unified-landing-page-and-ia-shell/tasks.md
git show 4fc5f81363e5b99e71d298390785d4d4c70d86ae:specs/doc-002-unified-landing-page-and-ia-shell/SPEC-MOC.md
git checkout 4fc5f81363e5b99e71d298390785d4d4c70d86ae -- specs/doc-002-unified-landing-page-and-ia-shell
```

The detailed per-file `git show` recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-14-doc-002-post-merge-hygiene.md`.

---

## PRSG-014 Optional gh-stack Stack Manager Integration

[Source: .specify/memory/archive-reports/2026-06-14-prsg-014-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-14
- **Cleanup branch**: `codex/post-merge-archive-hygiene`
- **Cleanup command**: `git rm -r specs/prsg-014-optional-gh-stack-stack-manager-integration`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/prsg-014-optional-gh-stack-stack-manager-integration`

### Provenance

| PR | Title | Merge commit | Tree reference |
|----|-------|--------------|----------------|
| #181 | `feat(speckit-pro): Add optional gh-stack stack manager integration` | `4b8342f42db3223db6955a1390b30949b8caea8c` | `ca39ded7975c93fc93217144121237b3295abce3` |

### Summary

PRSG-014 added optional `gh-stack` support detection and stack-aware
create/sync/restack evidence while preserving explicit GitHub base/head PR
operations as the fallback. Missing, unsupported, ambiguous, unsafe, or
topology-incompatible `gh stack` environments fall back before mutation.
Partial or unknown `gh-stack` mutations block with recoverable state instead of
switching managers.

### Recovery Commands

```text
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/spec.md
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/plan.md
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/tasks.md
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/SPEC-MOC.md
git show 4b8342f42db3223db6955a1390b30949b8caea8c:specs/prsg-014-optional-gh-stack-stack-manager-integration/contracts/stack-manager-decision.schema.json
git checkout 4b8342f42db3223db6955a1390b30949b8caea8c -- specs/prsg-014-optional-gh-stack-stack-manager-integration
```

The detailed per-file `git show` recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-14-prsg-014-post-merge-hygiene.md`.

---

## DOC-003 and DOC-004 Platform Install Paths

[Source: .specify/memory/archive-reports/2026-06-15-doc-003-004-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-15
- **Cleanup branch**: `codex/doc-003-004-post-merge-hygiene`
- **Cleanup command**: `git rm -r specs/doc-003-claude-code-marketplace-installation-path specs/doc-004-codex-marketplace-installation-path`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**:
  - `specs/doc-003-claude-code-marketplace-installation-path`
  - `specs/doc-004-codex-marketplace-installation-path`

### Provenance

| Spec | PR | Title | Merge commit | Tree reference | Task completion |
|------|----|-------|--------------|----------------|-----------------|
| DOC-003 | #187 | `docs(DOC-003): add Claude Code install route` | `afc197a278001c7b8c2ffeb973c359971676d597` | `ef3e4eb22c286bafa1657e78c5461b774e8da1e6` | 39 / 39 |
| DOC-004 | #186 | `docs(DOC-004): add Codex marketplace installation path` | `bc48441c494d34a7df9876c3bdebabc4db8408a5` | `31c75c95d787ea2661216e29e6ec8b0a8ab19625` | 20 / 20 |

### Summary

DOC-003 and DOC-004 completed the platform-specific install tier of the
interactive documentation roadmap. The canonical shipped docs are:

- `docs-site/src/content/docs/install/claude-code.md`
- `docs-site/src/content/docs/install/codex.md`

### Recovery Commands

```text
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/spec.md
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/plan.md
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/tasks.md
git show afc197a278001c7b8c2ffeb973c359971676d597:specs/doc-003-claude-code-marketplace-installation-path/SPEC-MOC.md
git checkout afc197a278001c7b8c2ffeb973c359971676d597 -- specs/doc-003-claude-code-marketplace-installation-path

git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/spec.md
git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/plan.md
git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/tasks.md
git show bc48441c494d34a7df9876c3bdebabc4db8408a5:specs/doc-004-codex-marketplace-installation-path/SPEC-MOC.md
git checkout bc48441c494d34a7df9876c3bdebabc4db8408a5 -- specs/doc-004-codex-marketplace-installation-path
```

The detailed per-file `git show` recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-15-doc-003-004-post-merge-hygiene.md`.

---

## DOC-005 First Successful Workflow Tutorial and Lifecycle Explainer

[Source: .specify/memory/archive-reports/2026-06-16-doc-005-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-16
- **Cleanup branch**: `codex/doc-005-post-merge-hygiene`
- **Cleanup command**: `git rm -r specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer`

### Provenance

| PR | Title | Merge commit | Tree reference |
|----|-------|--------------|----------------|
| #198 | `docs(DOC-005): Record DOC-005 validation evidence` | `238bd36921787588f52d5f0f24bd3a0d7b485d66` | `6f098af3452d8c935c67622e5acfa34ae86328f0` |
| #199 | `docs(DOC-005): Document the first successful run tutorial` | `d6143d8fdf142f277b525a8fb759ee8b10faa44e` | `e7e392f897853ce206ab6b8aaf470a4481b4e04b` |
| #200 | `docs(DOC-005): Document the SpecKit lifecycle explainer` | `f03e352d5cc143d104c9b8f977266496fa869fd4` | `cec126592fcaf5a71325f73bebc6c839377edcc5` |
| #201 | `docs(DOC-005): Add prerequisite checks and fallback handoffs` | `0f0eff05f80130d4c61cc91c2633f2b73ad88151` | `8bbf7ea908e30407a2d67a5fb25d3ed60a04c336` |

### Summary

DOC-005 completed the first successful workflow tutorial and Spec Kit lifecycle
explainer. The canonical shipped docs are:

- `docs-site/src/content/docs/first-run.md`
- `docs-site/src/content/docs/spec-kit-lifecycle.mdx`
- `docs-site/src/components/LifecycleFlow.astro`

The merged active spec state contained residual PR-packet evidence only; the
normal `spec.md`, `plan.md`, and `tasks.md` active spec contract files were
already absent from `main` before this hygiene branch.

### Recovery Commands

```text
git show 238bd36921787588f52d5f0f24bd3a0d7b485d66:specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer/.process/pr-packets/doc-005/command-validation.md
git show 238bd36921787588f52d5f0f24bd3a0d7b485d66:specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer/.process/pr-packets/doc-005/scope.md
git show d6143d8fdf142f277b525a8fb759ee8b10faa44e:specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer/.process/pr-packets/doc-005/first-run-review.md
git show d6143d8fdf142f277b525a8fb759ee8b10faa44e:specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer/.process/pr-packets/doc-005/first-run-snippet-review.md
git show f03e352d5cc143d104c9b8f977266496fa869fd4:specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer/.process/pr-packets/doc-005/lifecycle-accessibility-review.md
git show f03e352d5cc143d104c9b8f977266496fa869fd4:specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer/.process/pr-packets/doc-005/lifecycle-static-review.md
git show 0f0eff05f80130d4c61cc91c2633f2b73ad88151:specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer/.process/pr-packets/doc-005/bounded-fallback-review.md
git show 0f0eff05f80130d4c61cc91c2633f2b73ad88151:specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer/.process/pr-packets/doc-005/platform-separation-review.md
git checkout 0f0eff05f80130d4c61cc91c2633f2b73ad88151 -- specs/doc-005-first-successful-workflow-tutorial-and-lifecycle-explainer
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-06-16-doc-005-post-merge-hygiene.md`.

---

## DOC-006 Safe Interactive Selector and Validation Aids

[Source: .specify/memory/archive-reports/2026-06-17-doc-006-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-17
- **Cleanup branch**: `codex/doc-006-post-merge-hygiene`
- **Cleanup command**: `git rm -r specs/doc-006-safe-interactive-selector-and-validation-aids`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/doc-006-safe-interactive-selector-and-validation-aids`

### Provenance

| PR | Title | Merge commit | Tree reference |
|----|-------|--------------|----------------|
| #203 | `docs(DOC-006): Add safe interactive selector and validation aids` | `973e9cf76143efe168f4c2b9ab5682581317e28c` | `a2678d1cd8d8ef6591d68a98c0279cfc6fcfacc7` |

### Summary

DOC-006 completed the choose-your-path safe selector, repository-only manifest
checker, generated payload diagram, first-run checklist, and focused validation
harness. The canonical shipped docs and validation files are:

- `docs-site/src/content/docs/choose-your-path.mdx`
- `docs-site/src/components/SafeInstallAids.astro`
- `docs-site/src/data/safe-install-aids.ts`
- `docs-site/scripts/validate-doc006-safe-aids.mjs`

### Recovery Commands

```text
git show 973e9cf76143efe168f4c2b9ab5682581317e28c:specs/doc-006-safe-interactive-selector-and-validation-aids/spec.md
git show 973e9cf76143efe168f4c2b9ab5682581317e28c:specs/doc-006-safe-interactive-selector-and-validation-aids/plan.md
git show 973e9cf76143efe168f4c2b9ab5682581317e28c:specs/doc-006-safe-interactive-selector-and-validation-aids/tasks.md
git show 973e9cf76143efe168f4c2b9ab5682581317e28c:specs/doc-006-safe-interactive-selector-and-validation-aids/SPEC-MOC.md
git show 973e9cf76143efe168f4c2b9ab5682581317e28c:specs/doc-006-safe-interactive-selector-and-validation-aids/contracts/doc006-safe-aids.schema.json
git show 973e9cf76143efe168f4c2b9ab5682581317e28c:specs/doc-006-safe-interactive-selector-and-validation-aids/.process/verify-report.md
git show 973e9cf76143efe168f4c2b9ab5682581317e28c:specs/doc-006-safe-interactive-selector-and-validation-aids/.process/uat-runbook.md
git show 973e9cf76143efe168f4c2b9ab5682581317e28c:specs/doc-006-safe-interactive-selector-and-validation-aids/.process/pr-body.md
git checkout 973e9cf76143efe168f4c2b9ab5682581317e28c -- specs/doc-006-safe-interactive-selector-and-validation-aids
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-06-17-doc-006-post-merge-hygiene.md`.

## DOC-007 Command, Workflow, Manifest, and File-Layout Reference

[Source: .specify/memory/archive-reports/2026-06-17-doc-007-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-17
- **Cleanup branch**: `codex/doc-007-post-merge-hygiene`
- **Cleanup command**: `git rm -r specs/doc-007-command-workflow-manifest-and-file-layout-reference`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/doc-007-command-workflow-manifest-and-file-layout-reference`

### Provenance

| PR | Title | Merge commit | Tree reference |
|----|-------|--------------|----------------|
| #208 | `docs(DOC-007): add generated reference pages` | `2f5ee096e903723e1ab0133c699bda5a22ae2172` | `67d3b8890b09605150b9cf300543d7a7ba517045` |

### Summary

DOC-007 completed the generated reference library for skills, agents,
manifests, hooks, scripts, tests, and source-vs-dist layout. The canonical
shipped docs and validation files are:

- `docs-site/scripts/generate-reference-pages.mjs`
- `docs-site/src/content/docs/reference.md`
- `docs-site/src/content/docs/reference/skills.md`
- `docs-site/src/content/docs/reference/agents.md`
- `docs-site/src/content/docs/reference/manifests.md`
- `docs-site/src/content/docs/reference/hooks.md`
- `docs-site/src/content/docs/reference/scripts.md`
- `docs-site/src/content/docs/reference/tests.md`
- `docs-site/src/content/docs/reference/source-vs-dist.md`

This cleanup also added `speckit-archive-cleanup` as a plugin skill so future
post-merge archive hygiene can be invoked directly.

### Recovery Commands

```text
git show 2f5ee096e903723e1ab0133c699bda5a22ae2172:specs/doc-007-command-workflow-manifest-and-file-layout-reference/spec.md
git show 2f5ee096e903723e1ab0133c699bda5a22ae2172:specs/doc-007-command-workflow-manifest-and-file-layout-reference/plan.md
git show 2f5ee096e903723e1ab0133c699bda5a22ae2172:specs/doc-007-command-workflow-manifest-and-file-layout-reference/tasks.md
git show 2f5ee096e903723e1ab0133c699bda5a22ae2172:specs/doc-007-command-workflow-manifest-and-file-layout-reference/SPEC-MOC.md
git show 2f5ee096e903723e1ab0133c699bda5a22ae2172:specs/doc-007-command-workflow-manifest-and-file-layout-reference/contracts/reference-generator.md
git show 2f5ee096e903723e1ab0133c699bda5a22ae2172:specs/doc-007-command-workflow-manifest-and-file-layout-reference/contracts/reference-inventory.schema.json
git checkout 2f5ee096e903723e1ab0133c699bda5a22ae2172 -- specs/doc-007-command-workflow-manifest-and-file-layout-reference
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-06-17-doc-007-post-merge-hygiene.md`.

## TACD-001 Platform Mechanics Spike

[Source: .specify/memory/archive-reports/2026-06-18-tacd-001-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-18
- **Cleanup branch**: `codex/tacd-001-post-merge-hygiene`
- **Cleanup command**: `git rm -r specs/tacd-001-platform-mechanics-spike`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/tacd-001-platform-mechanics-spike`

### Provenance

| PR | Title | Merge commit | Tree reference |
|----|-------|--------------|----------------|
| #211 | `feat(speckit-pro): Add platform mechanics spike foundation` | `2104432cb8d92c0088b99f02e0922d5ebf433a98` | `ab754c7e7fdd61281c97e8d4ca140a414cec9a85` |
| #212 | `feat(speckit-pro): Document runtime capability mechanics` | `e9d3c08af55658b97452c86c294bae0b340a3bc4` | `7fd0642c4f076ab5a0d0830987c1833e15b6daf1` |
| #213 | `feat(speckit-pro): Classify active and historical references` | `dfa18a20691b86724cc05008c2b3fae93a0d9127` | `60a3970fd64cfbe3c6f1f61421cbe6532ecf56f6` |
| #214 | `feat(speckit-pro): Recommend directive home and handoffs` | `46d01dcf081a8c416c692db497daea5cae11a801` | `61f2a4a2118edc6b8eeca93c285741119a183eac` |
| #216 | `docs(TACD): Adopt platform spike decisions` | `62dc58a46419ed09c1aa506974ef8c7fbab998ee` | `060dd16f5186049ce8455a50c77a88a2e78ed441` |

### Summary

TACD-001 completed the report-only platform mechanics spike for
tool-agnostic capability discovery. The canonical report records active
named-tool reference categories, Claude/Codex capability mechanics, the selected
shared-reference-plus-runtime-pointers directive home, the TACD-004 allowlist,
and downstream handoffs for TACD-002, TACD-003, and TACD-004. PR #216 adopted
those decisions into the PRD and technical roadmap.

### Canonical Artifacts

- `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- `docs/prd-tool-agnostic-capability-discovery.md`
- `docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md`
- `docs/ai/specs/tool-agnostic-capability-discovery-roadmap-MOC.md`

### Recovery Commands

```text
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/spec.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/plan.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/tasks.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/SPEC-MOC.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/research.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/data-model.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:specs/tacd-001-platform-mechanics-spike/quickstart.md
git show 46d01dcf081a8c416c692db497daea5cae11a801:docs/ai/research/tool-agnostic-capability-discovery-spike.md
git show 62dc58a46419ed09c1aa506974ef8c7fbab998ee:docs/prd-tool-agnostic-capability-discovery.md
git show 62dc58a46419ed09c1aa506974ef8c7fbab998ee:docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md
git checkout 46d01dcf081a8c416c692db497daea5cae11a801 -- specs/tacd-001-platform-mechanics-spike
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-06-18-tacd-001-post-merge-hygiene.md`.
