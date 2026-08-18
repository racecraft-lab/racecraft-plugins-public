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
`tests/speckit-pro/unit/fixtures/atomicity-route/dogfood-atomicity-router/`,
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
- **Fixture-decoupling prerequisite**: `test-plan-layers.sh` now reads the vendored schema fixture at `tests/speckit-pro/unit/fixtures/plan-layers/contracts/plan-layers.schema.json`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/prsg-008-layer-planner`
- **Recovery**: use the PRSG-008 `git show` / `git checkout` commands recorded above.

The removed source folder was already archived in project memory. Layer 4
planner coverage remains active through fixture task files and the vendored
schema contract fixture under `tests/speckit-pro/unit/fixtures/plan-layers/`.

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
schemas and test fixtures under `tests/speckit-pro/unit/fixtures/multi-pr-emission/`.

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
under `tests/speckit-pro/unit/fixtures/`.

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
  `tests/speckit-pro/unit/fixtures/pr-packet-feature/`.
- PRSG-012 marker-emission regression now reads committed marker-plan fixtures
  under `tests/speckit-pro/unit/fixtures/marker-plan/`.
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

## TACD-002 Capability Discovery Directive and Agent Updates

[Source: .specify/memory/archive-reports/2026-06-18-tacd-002-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-18
- **Cleanup branch**: `codex/tacd-002-post-merge-hygiene`
- **Cleanup command**: `git rm -r specs/tacd-002-capability-discovery-directive-and-agent-updates`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/tacd-002-capability-discovery-directive-and-agent-updates`

### Provenance

| PR | Title | Merge commit | Tree reference |
|----|-------|--------------|----------------|
| #221 | `feat(TACD-002): Add capability discovery foundation` | `b63dfc95525eb64f9f221d7f2513c9ab9c36b314` | `46e1c2b3f1a7d83b06815c7b34f1dc7531df53cf` |
| #222 | `feat(TACD-002): Update agent capability selection` | `da9a7c5cd6ba567f1530e396cfc69527948bf7a7` | `8c2005f42f187542de7a20c10707759b436d0777` |
| #223 | `feat(TACD-002): Document fallback evidence behavior` | `2060789358cdf4cd946d423238ee2be1f7f90675` | `a93e16d3ae648c5c13a8cc305a7c783d7119321d` |
| #224 | `feat(TACD-002): Align Claude and Codex guidance` | `4203e1011a1d67220e0e82115108759446fa04cf` | `55cb7f67ac1c8aa0e4e127bc65e6f382a8c61194` |
| #225 | `feat(TACD-002): Refresh generated capability payloads` | `12ff3667a36906552bb47ee11b7b53239d42f391` | `0e35350187cd7196412a8ab14287a492e1cd1984` |
| #226 | `feat(TACD-002): Emit ordered slice PRs` | `130abd2b6329e774207c84ab798cfb5b6dab7131` | `0ec46aa6307a8cc8f4f63d729b2a729123c2a62e` |

### Summary

TACD-002 completed the active runtime guidance tier for tool-agnostic
capability discovery. The canonical shipped artifacts include the shared
capability directive, scoped Claude and Codex agent guidance, generated Claude
and Codex payload copies, marker-emission hardening, and focused regression
tests. TACD-003 is now unblocked for prerequisite and user-facing documentation
messaging.

### Canonical Artifacts

- `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`
- `speckit-pro/agents/*.md`
- `speckit-pro/codex-agents/*.toml`
- `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh`
- `tests/speckit-pro/unit/test-multi-pr-emission.sh`
- `tests/speckit-pro/unit/test-reviewability-marker-guidance.sh`
- `dist/claude/speckit-pro/`
- `dist/codex/speckit-pro/`

### Recovery Commands

```text
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/spec.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/plan.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/tasks.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/SPEC-MOC.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/research.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/data-model.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:specs/tacd-002-capability-discovery-directive-and-agent-updates/quickstart.md
git show 130abd2b6329e774207c84ab798cfb5b6dab7131:speckit-pro/skills/speckit-autopilot/references/capability-discovery.md
git checkout 130abd2b6329e774207c84ab798cfb5b6dab7131 -- specs/tacd-002-capability-discovery-directive-and-agent-updates
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-06-18-tacd-002-post-merge-hygiene.md`.

## DOC-008 and DOC-009 Interactive Documentation Trust and Release Workflow

[Source: .specify/memory/archive-reports/2026-06-18-doc-008-009-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-18
- **Cleanup branch**: `codex/doc-specs-post-merge-hygiene`
- **Cleanup command**: `git rm -r specs/doc-008-troubleshooting-security-trust-update-rollback specs/doc-009-maintainer-contributor-release-workflow`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**:
  - `specs/doc-008-troubleshooting-security-trust-update-rollback`
  - `specs/doc-009-maintainer-contributor-release-workflow`

### Provenance

| Spec | PR | Title | Merge commit | Tree reference |
|------|----|-------|--------------|----------------|
| DOC-008 | #220 | `docs(DOC-008): Add troubleshooting, Security, Trust, Update, and Rollback` | `a27fc5dcb2b295fd7ea2d3250d2df58692a7408b` | `0ec6e8b0dd3fecdc39233208bf0623d6d63c2954` |
| DOC-009 | #219 | `docs(DOC-009): document maintainer contributor release workflow` | `2686caa2a12dbaf460c33f37f054f40765fb2b35` | `4175b9ee51fd256943945ffb157f22c97faa7496` |

### Summary

DOC-008 shipped source-backed troubleshooting, security/trust, and
update/rollback documentation for Claude Code and Codex install, cache,
permission, version, CLI, custom-agent, managed-policy, stale-payload, and
rollback cases. DOC-009 shipped the release workflow guide for contributors and
maintainers, covering source/generated boundaries, release-readiness commands,
payload rebuilds, marketplace sync, version ownership, PR Checks behavior,
release automation, Conventional Commit titles, public-readable PR bodies, and
the DOC-010 handoff.

The cleanup also hardened `generate-spec-index.sh` and its generated Claude and
Codex payload copies for the zero-active-spec state exposed after removing the
last DOC active spec folders, so roadmap-MOC generated indexes clear
deterministically when only `specs/.gitkeep` remains.

### Canonical Artifacts

- `docs-site/src/content/docs/troubleshooting.md`
- `docs-site/src/content/docs/security-and-trust.md`
- `docs-site/src/content/docs/update-and-rollback.md`
- `docs-site/src/content/docs/install/claude-code.md`
- `docs-site/src/content/docs/install/codex.md`
- `docs-site/src/content/docs/reference.md`
- `docs-site/src/content/docs/contribute-and-release.md`

### Recovery Commands

```text
git show a27fc5dcb2b295fd7ea2d3250d2df58692a7408b:specs/doc-008-troubleshooting-security-trust-update-rollback/spec.md
git show a27fc5dcb2b295fd7ea2d3250d2df58692a7408b:specs/doc-008-troubleshooting-security-trust-update-rollback/plan.md
git show a27fc5dcb2b295fd7ea2d3250d2df58692a7408b:specs/doc-008-troubleshooting-security-trust-update-rollback/tasks.md
git show a27fc5dcb2b295fd7ea2d3250d2df58692a7408b:specs/doc-008-troubleshooting-security-trust-update-rollback/SPEC-MOC.md
git checkout a27fc5dcb2b295fd7ea2d3250d2df58692a7408b -- specs/doc-008-troubleshooting-security-trust-update-rollback

git show 2686caa2a12dbaf460c33f37f054f40765fb2b35:specs/doc-009-maintainer-contributor-release-workflow/spec.md
git show 2686caa2a12dbaf460c33f37f054f40765fb2b35:specs/doc-009-maintainer-contributor-release-workflow/plan.md
git show 2686caa2a12dbaf460c33f37f054f40765fb2b35:specs/doc-009-maintainer-contributor-release-workflow/tasks.md
git show 2686caa2a12dbaf460c33f37f054f40765fb2b35:specs/doc-009-maintainer-contributor-release-workflow/SPEC-MOC.md
git checkout 2686caa2a12dbaf460c33f37f054f40765fb2b35 -- specs/doc-009-maintainer-contributor-release-workflow
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-06-18-doc-008-009-post-merge-hygiene.md`.

## TACD-003 Prerequisite and Documentation Messaging

[Source: .specify/memory/archive-reports/2026-06-19-tacd-003-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-19
- **Cleanup branch**: `codex/tacd-003-archive-cleanup`
- **Cleanup command**: `git rm -r specs/tacd-003-prerequisite-and-documentation-messaging`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/tacd-003-prerequisite-and-documentation-messaging`

### Provenance

| PR | Title | Merge commit | Tree reference |
|----|-------|--------------|----------------|
| #230 | `feat(speckit-pro): TACD-003 prerequisite advisory, active guidance, focused verification, and review packet evidence` | `bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9` | `6aea1266ff75fef87b94fb5aac3bf6a5aa5d58e6` |

### Summary

TACD-003 completed the prerequisite and user-facing documentation messaging
tier for tool-agnostic capability discovery. The canonical shipped artifacts
include the generic `capability_coverage` advisory, active Claude and Codex
prerequisite guidance, plugin limitation guidance, coach/autopilot wording,
source-derived generated payloads, and focused regression tests. TACD-004 is now
unblocked for deterministic static enforcement and eval coverage.

### Canonical Artifacts

- `speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh`
- `speckit-pro/skills/speckit-autopilot/references/prerequisites.md`
- `speckit-pro/codex-skills/speckit-autopilot/references/prerequisites-codex.md`
- `speckit-pro/skills/speckit-autopilot/references/plugin-limitations.md`
- `speckit-pro/skills/speckit-coach/references/autopilot-guide.md`
- `tests/speckit-pro/unit/test-check-prerequisites.sh`
- `dist/claude/speckit-pro/`
- `dist/codex/speckit-pro/`

### Recovery Commands

```text
git show bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9:specs/tacd-003-prerequisite-and-documentation-messaging/spec.md
git show bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9:specs/tacd-003-prerequisite-and-documentation-messaging/plan.md
git show bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9:specs/tacd-003-prerequisite-and-documentation-messaging/tasks.md
git show bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9:specs/tacd-003-prerequisite-and-documentation-messaging/SPEC-MOC.md
git show bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9:specs/tacd-003-prerequisite-and-documentation-messaging/research.md
git show bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9:specs/tacd-003-prerequisite-and-documentation-messaging/quickstart.md
git show bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9:speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh
git checkout bcc8eedd2dd732b6f02e18ff68fd4de0e58396e9 -- specs/tacd-003-prerequisite-and-documentation-messaging
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-06-19-tacd-003-post-merge-hygiene.md`.

## DOC-010 Search, Accessibility, Deep Links, Docs Validation

[Source: .specify/memory/archive-reports/2026-06-19-doc-010-post-merge-hygiene.md]

- **Cleanup applied**: 2026-06-19
- **Cleanup branch**: `codex/archive-doc-tacd-completed-work`
- **Cleanup command**: `git rm -r specs/doc-010-search-accessibility-deep-links-docs-validation`
- **safeToApplyCleanup**: `true`
- **Removed from active specs**: `specs/doc-010-search-accessibility-deep-links-docs-validation`

### Provenance

| PR | Title | Merge commit | Tree reference |
|----|-------|--------------|----------------|
| #232 | `docs(DOC-010): Add docs-site validation foundation` | `699c54bda562d6c900a306d4838b97d9f6ddbcf8` | `4babe109cd87cc5a906f006b8355dfb06cfb9da3` |
| #233 | `docs(DOC-010): Update Find And Share Support Guidance` | `6f88b0b8a7f38869e5e7fc78c507a580dd92b998` | `148133bb9448d13e4e2d7a5a8ceb18766c0133e4` |
| #234 | `docs(DOC-010): Update Use Interactive Aids Accessibly` | `b3c0eb5e5b281df94f5e03861a65674ec291e0a1` | `418bc613e0a90a5b14edffe7ac066337ca8835f1` |
| #235 | `docs(DOC-010): Update Run One Matching Docs Validation Path` | `abd7f2343b6a723cfe7bca806ce17dba96657141` | `2e662e61ca0f760fa7baad55d34cc896f28f1221` |
| #236 | `docs(DOC-010): Update Review Minimal Browser Evidence` | `3fb8b55fc13b3896f7a9507eb07fa40b077f8781` | `bd1b9df9e41e99bbb201a9712868b9d8ec714029` |

### Summary

DOC-010 completed the interactive documentation quality hardening roadmap. The
canonical shipped artifacts include support anchor and source-update validation,
accessible install/lifecycle aids and fallbacks, the combined
`pnpm --dir docs-site validate` path, the conditional PR Checks
`validate-docs` gate, compact Playwright smoke coverage, and 7-day
`docs-site-smoke-evidence` artifact behavior. DOC-001 through DOC-010 are now
complete and archived.

### Canonical Artifacts

- `docs-site/package.json`
- `docs-site/playwright.config.mjs`
- `docs-site/scripts/validate-docs-quality.mjs`
- `docs-site/scripts/validate-doc006-safe-aids.mjs`
- `docs-site/tests/docs-smoke.spec.mjs`
- `docs-site/src/content/docs/glossary.md`
- `docs-site/src/content/docs/choose-your-path.mdx`
- `docs-site/src/components/LifecycleFlow.astro`
- `.github/workflows/pr-checks.yml`

### Recovery Commands

```text
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:specs/doc-010-search-accessibility-deep-links-docs-validation/spec.md
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:specs/doc-010-search-accessibility-deep-links-docs-validation/plan.md
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:specs/doc-010-search-accessibility-deep-links-docs-validation/tasks.md
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:specs/doc-010-search-accessibility-deep-links-docs-validation/SPEC-MOC.md
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:specs/doc-010-search-accessibility-deep-links-docs-validation/research.md
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:specs/doc-010-search-accessibility-deep-links-docs-validation/data-model.md
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:specs/doc-010-search-accessibility-deep-links-docs-validation/quickstart.md
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:specs/doc-010-search-accessibility-deep-links-docs-validation/contracts/browser-smoke-contract.md
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:docs/ai/specs/.process/DOC-010-workflow.md
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:docs-site/scripts/validate-docs-quality.mjs
git show 3fb8b55fc13b3896f7a9507eb07fa40b077f8781:docs-site/tests/docs-smoke.spec.mjs
git checkout 3fb8b55fc13b3896f7a9507eb07fa40b077f8781 -- specs/doc-010-search-accessibility-deep-links-docs-validation
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-06-19-doc-010-post-merge-hygiene.md`.

## TACD-004 Verification Coverage

### Provenance

| PR | Title | Merged at | Merge commit |
|----|-------|-----------|--------------|
| #240 | `fix(speckit-pro): restore empty Claude skill payloads and add vendor-neutral checks` | 2026-06-20T21:36:55Z | `b95d721f107dd1a17cee88671dc48da791e8e54c` |

### Summary

TACD-004 locked the vendor-neutral optional-tool contract with a Layer 5
named-tool guard (and full removal of the named MCP assertions), Layer 1
pointer-coverage and target-resolution guards against `dist/**`, and rewritten
Claude/Codex functional evals with behavior-observable scenarios. It also fixed
the `strip_codex_guard` payload-build defect and added a body-completeness
guard, restoring all 8 truncated Claude skill bodies.

### Canonical Artifacts

- `scripts/build-plugin-payloads.sh`
- `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.sh`
- `tests/speckit-pro/layer1-structural/validate-capability-pointer.sh`
- `tests/speckit-pro/layer1-structural/validate-capability-resolution.sh`
- `tests/speckit-pro/layer1-structural/validate-payload-completeness.sh`
- `tests/speckit-pro/layer3-functional/evals/` and `codex-evals/` (autopilot + coach)
- `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/`

### Recovery Commands

```text
git show b95d721f107dd1a17cee88671dc48da791e8e54c:specs/tacd-004-verification-coverage/spec.md
git show b95d721f107dd1a17cee88671dc48da791e8e54c:specs/tacd-004-verification-coverage/plan.md
git show b95d721f107dd1a17cee88671dc48da791e8e54c:specs/tacd-004-verification-coverage/tasks.md
git checkout b95d721f107dd1a17cee88671dc48da791e8e54c -- specs/tacd-004-verification-coverage
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-06-22-tacd-004-post-merge-hygiene.md`.

## DOC-011 GitHub Pages Build-And-Deploy Pipeline

### Provenance

| PR | Title | Merged at | Merge commit | Tree reference |
|----|-------|-----------|--------------|----------------|
| #243 | `docs(DOC-011): add GitHub Pages deploy pipeline` | 2026-06-23T23:02:27Z | `538fb63323cb8b8562a246167eea9a46abcbc499` | `15a66732284ce5ff06b5821c8e3d44a63d20d0d3` |

### Summary

DOC-011 shipped the staging GitHub Pages deploy workflow for `docs-site/`, the
staging `noindex,nofollow` and `robots.txt` guard, docs-quality validation for
that guard, the CI/CD verification runbook, CLAUDE deploy guidance, PR workflow
lint coverage, release docs-reference runtime alignment, and shared
roadmap-MOC index generator hardening with synced generated payload copies and
focused tests.

The first post-merge `Deploy Docs` run failed because repository Pages was not
yet enabled/configured for GitHub Actions. That is the documented manual
operator prerequisite, not a committed-source cleanup blocker.

### Canonical Artifacts

- `.github/workflows/deploy-docs.yml`
- `.github/workflows/pr-checks.yml`
- `.github/workflows/release.yml`
- `docs-site/astro.config.mjs`
- `docs-site/public/robots.txt`
- `docs-site/scripts/validate-docs-quality.mjs`
- `docs/ai/specs/cicd-release-pipeline-verification.md`
- `CLAUDE.md`
- `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh`
- `dist/claude/speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh`
- `dist/codex/speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh`
- `tests/speckit-pro/layer1-structural/validate-pr-checks-sentinel.sh`
- `tests/speckit-pro/unit/test-generate-spec-index.sh`

### Recovery Commands

```text
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/spec.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/plan.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/tasks.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/SPEC-MOC.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/research.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/data-model.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/quickstart.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:specs/doc-011-github-pages-build-and-deploy-pipeline/contracts/deploy-docs-workflow.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:docs/ai/specs/.process/DOC-011-workflow.md
git show 538fb63323cb8b8562a246167eea9a46abcbc499:docs/ai/specs/.process/DOC-011-design-concept.md
git checkout 538fb63323cb8b8562a246167eea9a46abcbc499 -- specs/doc-011-github-pages-build-and-deploy-pipeline
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-06-23-doc-011-post-merge-hygiene.md`.

---

## Brand identity and marketplace landing page

[Source: specs/doc-013-brand-identity-marketplace-landing]

- **Feature**: Brand identity and marketplace landing page
- **Roadmap ID**: DOC-013
- **Branch**: `doc-013-brand-identity-marketplace-landing`
- **Spec path**: `specs/doc-013-brand-identity-marketplace-landing/`
- **PR URL**: https://github.com/racecraft-lab/racecraft-plugins-public/pull/246
- **Merge commit**: `6a0516ffef30e63b0f00347aa37463bdc1396d30`
- **Tree reference**: N/A (merge commit recorded above)
- **CI run URL**: N/A (PR Checks green at merge: `validate-plugins`, `validate-pr-title`, `validate-docs`)
- **Argos build/review URL**: N/A (no visual-regression service; WCAG AA contrast evidence is the enumerated foreground/background ratio table in the PR packet)
- **Metadata gates**: `validate-pr-title=pass`, `validate-plugins=pass`, `validate-docs=pass`
- **Artifact manifest**: N/A (binary brand assets — 5 woff2, 10 favicon/manifest files, 3 logo SVGs — committed verbatim under `docs-site/public/` and `docs-site/src/assets/`)
- **Task completion**: 15 / 16 tasks checked (T016 "assemble the PR review packet" was completed via the merged PR #246 body but left unchecked in tasks.md)
- **Archived**: 2026-06-24
- **Status**: Completed

### Summary

DOC-013 applied the Racecraft visual identity to the `docs-site/` Astro 6.4.6 +
Starlight 0.40.0 site and converted the stock-Starlight home route into a real
marketplace landing page. A single `brand.css` maps the Racecraft palette onto
Starlight's `--sl-color-*` tokens for light and dark mode (blue accent for
links/active-nav, AA-safe `#2a6a99` link text, red `#dc143c` reserved as
punctuation — never as failing normal-size text, soft dark-gray `#1a1a1a`
reading surface with true black `#0a0a0a` scoped to the hero block only),
declares five self-hosted woff2 `@font-face`s with `font-display: swap`
(Space Grotesk 400/700, Geist 400/600, Fira Code regular), and points Starlight's
font tokens at those faces. `astro.config.mjs` wires `customCss`, the light/dark
wordmark `logo` (`replacesTitle`), the `favicon`, and two above-the-fold font
preloads (Space Grotesk 700 + Geist 400, each with `crossorigin="anonymous"`).
`index.mdx` became a Starlight-native `template: splash` + `hero` + `<CardGrid>`
landing with the logomark hero image, a benefit-led headline, ~3 anti-hype
value-prop cards, one primary CTA to `/racecraft-plugins-public/first-run/`, and
a subordinate secondary CTA to the GitHub repo. WCAG AA contrast is met in both
modes (enumerated ratio table recorded in the PR packet); reduced-motion is
respected. Brand assets were ported verbatim from the sibling `landing-page/website`
project. Per-component restyle (DOC-016), performance/Lighthouse budget (DOC-017),
verbal-voice/tone system (DOC-019), and domain/base-path cutover (DOC-012) were
explicitly deferred.

Post-merge review (Copilot) caught three issues fixed on-branch before merge: the
PWA manifest icon `src` values were base-path-prefixed (GitHub Pages project page),
the font preloads use explicit `crossorigin="anonymous"` (not a boolean), and a
stale heading-font-stack comment was corrected.

### Canonical Artifacts

- `docs-site/src/styles/brand.css` (NEW — token map + 5 `@font-face` + font tokens + scoped red/hero-block + focus ring + reduced-motion)
- `docs-site/astro.config.mjs` (MODIFIED — `customCss`, `logo`, `favicon`, font-preload/favicon/theme `head` tags)
- `docs-site/src/content/docs/index.mdx` (MODIFIED — `template: splash` + hero + CardGrid landing)
- `docs-site/src/assets/{logo.svg, logo-light.svg, mark.svg}` (NEW — wordmark + logomark)
- `docs-site/public/{favicon.svg, favicon.ico, favicon-16x16.png, favicon-32x32.png, favicon-32x32-light.png, favicon-48x48.png, apple-touch-icon.png, android-chrome-192x192.png, android-chrome-512x512.png, site.webmanifest}` (NEW — ported)
- `docs-site/public/fonts/{space-grotesk-400, space-grotesk-700, geist-400, geist-600, fira-code-regular}.woff2` (NEW — ported)

### Recovery Commands

```text
git show 6a0516ffef30e63b0f00347aa37463bdc1396d30:specs/doc-013-brand-identity-marketplace-landing/spec.md
git show 6a0516ffef30e63b0f00347aa37463bdc1396d30:specs/doc-013-brand-identity-marketplace-landing/plan.md
git show 6a0516ffef30e63b0f00347aa37463bdc1396d30:specs/doc-013-brand-identity-marketplace-landing/tasks.md
git show 6a0516ffef30e63b0f00347aa37463bdc1396d30:specs/doc-013-brand-identity-marketplace-landing/research.md
git show 6a0516ffef30e63b0f00347aa37463bdc1396d30:specs/doc-013-brand-identity-marketplace-landing/data-model.md
git show 6a0516ffef30e63b0f00347aa37463bdc1396d30:specs/doc-013-brand-identity-marketplace-landing/quickstart.md
git show 6a0516ffef30e63b0f00347aa37463bdc1396d30:specs/doc-013-brand-identity-marketplace-landing/brand-guide.md
git show 6a0516ffef30e63b0f00347aa37463bdc1396d30:specs/doc-013-brand-identity-marketplace-landing/SPEC-MOC.md
git show 6a0516ffef30e63b0f00347aa37463bdc1396d30:docs/ai/specs/.process/DOC-013-workflow.md
git show 6a0516ffef30e63b0f00347aa37463bdc1396d30:docs/ai/specs/.process/DOC-013-design-concept.md
git checkout 6a0516ffef30e63b0f00347aa37463bdc1396d30 -- specs/doc-013-brand-identity-marketplace-landing
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-06-24-doc-013-post-merge-hygiene.md`.

---

## XPLAT-003 Supply-Chain Security and Consumer Trust Model

### Provenance

| PR | Title | Merged at | Merge commit | Tree reference |
|----|-------|-----------|--------------|----------------|
| #267 | `feat(XPLAT-003): Add supply-chain security and consumer trust model` | 2026-06-29T00:26:40Z | `1ab96b38da7e400b3c8e78b21d92e7b05302cfdd` | N/A |

### Summary

XPLAT-003 shipped the first-release security/control model for the cross-platform
runtime lane after the runtime decision was amended from native-binary options
to a Python 3.11+ standard-library runner aligned with official Spec Kit /
`specify` prerequisites. It is a planning and evidence contract, not an
implementation slice.

The merged artifacts reject Go, Rust, Zig, native binaries, Bash, Git Bash, WSL,
PowerShell helper scripts, `jq`, Node, `pip install`, virtualenv restore, and
package restore as required installed-plugin runtime substrates. They assign
runner source/preflight/checksum/manifest controls to XPLAT-004, helper behavior
ports to XPLAT-005/XPLAT-006, and Claude/Codex installed-cache cutover,
latest-tag verification, complete bundled-agent install evidence, native UAT,
update/autoheal proof, consumer-local verification, and public claim readiness
to XPLAT-007.

### Canonical Artifacts

- `specs/xplat-003-supply-chain-security-and-consumer-trust-model/spec.md`
- `specs/xplat-003-supply-chain-security-and-consumer-trust-model/plan.md`
- `specs/xplat-003-supply-chain-security-and-consumer-trust-model/tasks.md`
- `specs/xplat-003-supply-chain-security-and-consumer-trust-model/research.md`
- `specs/xplat-003-supply-chain-security-and-consumer-trust-model/data-model.md`
- `specs/xplat-003-supply-chain-security-and-consumer-trust-model/quickstart.md`
- `specs/xplat-003-supply-chain-security-and-consumer-trust-model/platform-user-journeys.md`
- `specs/xplat-003-supply-chain-security-and-consumer-trust-model/contracts/supply-chain-control-contract.md`
- `specs/xplat-003-supply-chain-security-and-consumer-trust-model/.process/uat-runbook.md`
- `docs/ai/specs/.process/XPLAT-003-workflow.md`
- `docs/ai/specs/.process/XPLAT-003-design-concept.md`
- `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`
- `docs/ai/specs/cross-platform-plugin-runtime-roadmap-MOC.md`

### Recovery Commands

```text
git show 1ab96b38da7e400b3c8e78b21d92e7b05302cfdd:specs/xplat-003-supply-chain-security-and-consumer-trust-model/spec.md
git show 1ab96b38da7e400b3c8e78b21d92e7b05302cfdd:specs/xplat-003-supply-chain-security-and-consumer-trust-model/plan.md
git show 1ab96b38da7e400b3c8e78b21d92e7b05302cfdd:specs/xplat-003-supply-chain-security-and-consumer-trust-model/tasks.md
git show 1ab96b38da7e400b3c8e78b21d92e7b05302cfdd:specs/xplat-003-supply-chain-security-and-consumer-trust-model/research.md
git show 1ab96b38da7e400b3c8e78b21d92e7b05302cfdd:specs/xplat-003-supply-chain-security-and-consumer-trust-model/data-model.md
git show 1ab96b38da7e400b3c8e78b21d92e7b05302cfdd:specs/xplat-003-supply-chain-security-and-consumer-trust-model/quickstart.md
git show 1ab96b38da7e400b3c8e78b21d92e7b05302cfdd:specs/xplat-003-supply-chain-security-and-consumer-trust-model/platform-user-journeys.md
git show 1ab96b38da7e400b3c8e78b21d92e7b05302cfdd:specs/xplat-003-supply-chain-security-and-consumer-trust-model/contracts/supply-chain-control-contract.md
git show 1ab96b38da7e400b3c8e78b21d92e7b05302cfdd:specs/xplat-003-supply-chain-security-and-consumer-trust-model/.process/uat-runbook.md
git show 1ab96b38da7e400b3c8e78b21d92e7b05302cfdd:specs/xplat-003-supply-chain-security-and-consumer-trust-model/SPEC-MOC.md
git show 1ab96b38da7e400b3c8e78b21d92e7b05302cfdd:docs/ai/specs/.process/XPLAT-003-workflow.md
git show 1ab96b38da7e400b3c8e78b21d92e7b05302cfdd:docs/ai/specs/.process/XPLAT-003-design-concept.md
git checkout 1ab96b38da7e400b3c8e78b21d92e7b05302cfdd -- specs/xplat-003-supply-chain-security-and-consumer-trust-model
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-06-29-xplat-003-post-merge-hygiene.md`.

---

## Completed Active Specs Sweep - XPLAT-001, XPLAT-002, DOC-014

### Provenance

| Spec | PR | Title | Merged at | Merge commit |
|------|----|-------|-----------|--------------|
| XPLAT-001 | #263 | `feat(speckit-pro): Add runtime Inventory and Constraints` | 2026-06-26T22:47:42Z | `a7f9ca97548ebe4b50cf84a19828d745471756a0` |
| XPLAT-002 | #266 | `feat(XPLAT-002): Add runtime implementation options and contract decision` | 2026-06-27T15:23:45Z | `fff4d6b5e7f4bf5ca85b2e55225417152b70b45f` |
| DOC-014 | #264 | `docs(DOC-014): make the docs site discoverable by search engines and AI agents` | 2026-06-26T21:54:32Z | `6c24f56885f09755dd85e0a451deb923e5ef437a` |

### Summary

This sweep archived the remaining completed active spec folders on current
`origin/main` after PR #269 merged. XPLAT-001 delivered the runtime inventory
report and rubrics. XPLAT-002 delivered the amended Python stdlib runtime
decision and runner contract. DOC-014 delivered the docs-site discoverability
foundation across crawler access, agent-readable outputs, metadata, schema, OG
cards, sitemap freshness, validation, and success-metric documentation.

### Canonical Artifacts

- `docs/ai/research/cross-platform-runtime-inventory.md`
- `docs/ai/specs/.process/XPLAT-001-workflow.md`
- `docs/ai/specs/.process/XPLAT-002-workflow.md`
- `docs/ai/specs/.process/DOC-014-workflow.md`
- `docs/ai/specs/doc-014-ai-discoverability-success-metric.md`
- `docs-site/src/pages/robots.txt.ts`
- `docs-site/src/pages/[...slug].md.ts`
- `docs-site/src/pages/og/[...slug].ts`
- `docs-site/src/routeData.ts`
- `docs-site/src/lib/schema.ts`
- `docs-site/tests/seo-*.spec.mjs`

### Recovery

Detailed per-spec recovery commands are stored in
`.specify/memory/archive-reports/2026-06-29-completed-active-specs-post-merge-hygiene.md`.

---

## XPLAT-004 Cross-Platform Runner Foundation

### Provenance

| Spec | PR | Title | Merged at | Merge commit |
|------|----|-------|-----------|--------------|
| XPLAT-004 | #274 | `feat(XPLAT-004): Add cross-platform runner foundation` | 2026-07-01T22:13:40Z | `cef3ed260dabf73833d3de82f82cacdb2c7758fa` |

### Summary

XPLAT-004 shipped the source-checkout Python 3.11+ standard-library runner
foundation for SpecKit Pro. The implementation added the `speckit_pro_runner`
package, module-style runner invocation, JSON envelope validation,
runtime-info/preflight operations, deterministic diagnostics, typed path and
subprocess fixture primitives, source manifest/checksum metadata, and focused
Layer 4 runner tests.

The feature deliberately did not switch active Claude Code or Codex skills,
hooks, generated payloads, install behavior, or public documentation claims to
the runner. XPLAT-005 owns read-only helper parity, XPLAT-006 owns mutation and
install helper ports, and XPLAT-007 owns active cutover plus native
Windows/macOS/Linux installed-plugin UAT.

### Canonical Artifacts

- `speckit-pro/speckit_pro_runner/__init__.py`
- `speckit-pro/speckit_pro_runner/__main__.py`
- `speckit-pro/speckit_pro_runner/envelope.py`
- `speckit-pro/speckit_pro_runner/runtime.py`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `tests/speckit-pro/unit/test-speckit-pro-runner.py`
- `tests/speckit-pro/unit/test-speckit-pro-runner.sh`
- `tests/speckit-pro/unit/fixtures/speckit-pro-runner/contract-fixtures.json`
- `tests/speckit-pro/unit/fixtures/speckit-pro-runner/runner-foundation-changed-files.txt`
- `tests/speckit-pro/unit/fixtures/speckit-pro-runner/platform-runbook-fixtures.md`
- `docs/ai/specs/.process/XPLAT-004-workflow.md`
- `docs/ai/specs/.process/XPLAT-004-design-concept.md`

### Recovery Commands

```text
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/spec.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/plan.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/tasks.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/research.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/data-model.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/quickstart.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:specs/xplat-004-cross-platform-runner-foundation/contracts/platform-runbook-fixtures.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:docs/ai/specs/.process/XPLAT-004-workflow.md
git show cef3ed260dabf73833d3de82f82cacdb2c7758fa:docs/ai/specs/.process/XPLAT-004-design-concept.md
git checkout cef3ed260dabf73833d3de82f82cacdb2c7758fa -- specs/xplat-004-cross-platform-runner-foundation
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-07-01-xplat-004-post-merge-hygiene.md`.

---

## XPLAT-005 Read-Only Helper Port

### Provenance

| Spec | PR | Title | Merged at | Merge commit |
|------|----|-------|-----------|--------------|
| XPLAT-005 | #276 | `feat(XPLAT-005): Add read-only helper port` | 2026-07-03T03:16:56Z | `c4642f50ae99172170798a49f0c8fd990891c0f9` |

### Summary

XPLAT-005 shipped read-only/advisory helper ports on top of the XPLAT-004
Python standard-library runner. The implementation added the helper registry,
read-only helper module, envelope/runtime integration, Python-authoritative
promotion records, request fixtures, source-checkout Bash-reference
comparisons, synthetic path and malformed-input coverage, runner metadata
refresh, and Layer 4 helper test entrypoint.

The feature deliberately did not switch active Claude Code or Codex skills,
hooks, generated payloads, install behavior, mutation helper behavior, or public
documentation claims to the runner. XPLAT-006 owns mutation, install, restack,
state-writing, and PR-emission helper ports. XPLAT-007 owns active cutover,
generated payload proof, installed-cache proof, native Windows/macOS/Linux UAT,
update/autoheal proof, and public release claims.

### Canonical Artifacts

- `speckit-pro/speckit_pro_runner/helpers/__init__.py`
- `speckit-pro/speckit_pro_runner/helpers/registry.py`
- `speckit-pro/speckit_pro_runner/helpers/read_only.py`
- `speckit-pro/speckit_pro_runner/envelope.py`
- `speckit-pro/speckit_pro_runner/runtime.py`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py`
- `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.sh`
- `tests/speckit-pro/unit/fixtures/read-only-helpers/`
- `tests/speckit-pro/unit/fixtures/read-only-helpers/read-only-helper-feature/`
- `docs/ai/specs/.process/XPLAT-005-workflow.md`
- `docs/ai/specs/.process/XPLAT-005-design-concept.md`

### Recovery Commands

```text
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/spec.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/plan.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/tasks.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/research.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/data-model.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/quickstart.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/contracts/read-only-helper-request.schema.json
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/contracts/helper-promotion-record.schema.json
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/.process/uat-runbook.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:specs/xplat-005-read-only-helper-port/SPEC-MOC.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:docs/ai/specs/.process/XPLAT-005-workflow.md
git show c4642f50ae99172170798a49f0c8fd990891c0f9:docs/ai/specs/.process/XPLAT-005-design-concept.md
git checkout c4642f50ae99172170798a49f0c8fd990891c0f9 -- specs/xplat-005-read-only-helper-port
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-07-03-xplat-005-post-merge-hygiene.md`.

---

## XPLAT-006 Mutation, Install, and PR-Emission Helper Port

### Provenance

| Spec | PR | Title | Merged at | Merge commit |
|------|----|-------|-----------|--------------|
| XPLAT-006 | #281 | `feat(XPLAT-006): Add mutation, install, and PR-emission helper port` | 2026-07-04T03:59:03Z | `85e79cd4b5ccc0116a2c5cdd0f04ce274294075f` |

### Summary

XPLAT-006 shipped mutation-capable Python runner helper infrastructure,
install/doctor fake-home proof, generated PR-body output, dry-run command-plan
evidence, deferred-live-mutation diagnostics, autopilot phase-coverage
hardening, and deterministic Layer 4 fixtures. The implementation added the
mutation, install, PR-emission, and promotion helper modules, install inventory,
phase-coverage validator, source/generated payload mirrors, contract fixtures,
runner metadata refresh, and focused Python test coverage.

The feature deliberately did not switch active Claude Code or Codex invocation
paths, generated-payload selection/cutover behavior, native installed-cache UAT,
public platform support claims, or repo-local release gates. XPLAT-007 owns
active Python tooling and release-gate migration. XPLAT-008 owns Claude/Codex
cutover, installed-plugin UAT, update/autoheal proof, and public release
readiness.

### Canonical Artifacts

- `speckit-pro/speckit_pro_runner/helpers/mutation.py`
- `speckit-pro/speckit_pro_runner/helpers/install.py`
- `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`
- `speckit-pro/speckit_pro_runner/helpers/promotion.py`
- `speckit-pro/speckit_pro_runner/helpers/registry.py`
- `speckit-pro/speckit_pro_runner/install_inventory.json`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`
- `speckit-pro/codex-skills/speckit-autopilot/`
- `dist/codex/speckit-pro/skills/speckit-autopilot/`
- `dist/claude/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`
- `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`
- `tests/speckit-pro/unit/test-autopilot-phase-coverage.py`
- `tests/speckit-pro/unit/fixtures/mutation-helpers/`
- `tests/speckit-pro/unit/fixtures/mutation-helpers/contracts/`
- `docs/ai/specs/.process/XPLAT-006-workflow.md`
- `docs/ai/specs/.process/XPLAT-006-design-concept.md`

### Recovery Commands

```text
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/spec.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/plan.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/tasks.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/research.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/data-model.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/quickstart.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/contracts/mutation-helper-request.schema.json
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/contracts/mutation-helper-result.schema.json
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/contracts/doctor-preflight-result.schema.json
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/contracts/helper-promotion-record.schema.json
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/contracts/autopilot-phase-coverage-report.schema.json
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/.process/uat-runbook.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:specs/xplat-006-mutation-install-pr-emission-helper-port/SPEC-MOC.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:docs/ai/specs/.process/XPLAT-006-workflow.md
git show 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f:docs/ai/specs/.process/XPLAT-006-design-concept.md
git checkout 85e79cd4b5ccc0116a2c5cdd0f04ce274294075f -- specs/xplat-006-mutation-install-pr-emission-helper-port
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-07-04-xplat-006-post-merge-hygiene.md`.

---

## XPLAT-007 Python Tooling and Release-Gate Migration

### Provenance

| Spec | PR | Title | Merged at | Merge commit |
|------|----|-------|-----------|--------------|
| XPLAT-007 | #284 | `feat(XPLAT-007): Add gate dispatch foundation` | 2026-07-05T17:16:16Z | `6c0af6cf6cd53e1569bcb03c9a56d939360a4b24` |
| XPLAT-007 | #285 | `feat(XPLAT-007): Update Python repo-local gate runner` | 2026-07-05T18:08:14Z | `cb1697290b8f7cb289d0740e59c899285dc95c33` |
| XPLAT-007 | #286 | `feat(XPLAT-007): Update payload install release gates` | 2026-07-05T18:34:53Z | `a0d2dd015f0a33e85634256061926e5274fdb69a` |
| XPLAT-007 | #287 | `feat(speckit-pro): Update Review Active No-Shell Guardrails` | 2026-07-05T18:57:01Z | `0ff2d8d731698cde02b334cdc3b2a377216b5d45` |

### Summary

XPLAT-007 shipped Python-authoritative repo-local suite, payload,
install-verification, release-readiness, and active-path guard gates through
the existing `speckit_pro_runner` JSON envelope. The implementation added the
gate package, runner dispatch, CI dispatch updates, maintainer command updates,
promotion records, request fixtures, case fixtures, active no-shell guard
coverage, runner metadata refreshes, and focused Layer 4 gate tests.

The feature deliberately did not switch installed Claude Code or Codex runtime
surfaces, publish generated release payloads, run native installed-plugin UAT,
or make public platform/update/autoheal claims. XPLAT-008 owns those final
release gates.

### Canonical Artifacts

- `speckit-pro/speckit_pro_runner/gates/`
- `speckit-pro/speckit_pro_runner/runtime.py`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `.github/workflows/pr-checks.yml`
- `.github/workflows/release.yml`
- `CLAUDE.md`
- `docs-site/src/content/docs/contribute-and-release.md`
- `docs-site/src/content/docs/reference/tests.md`
- `tests/speckit-pro/run-all.sh`
- `tests/speckit-pro/layer1-structural/validate-pr-checks-sentinel.sh`
- `tests/speckit-pro/layer1-structural/validate-release-workflow.sh`
- `tests/speckit-pro/unit/test-speckit-pro-gates.py`
- `tests/speckit-pro/unit/fixtures/runner-gates/`
- `docs/ai/specs/.process/XPLAT-007-workflow.md`
- `docs/ai/specs/.process/XPLAT-007-design-concept.md`

### Recovery Commands

```text
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/spec.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/plan.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/tasks.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/research.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/data-model.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/quickstart.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/contracts/migrated-gate-request.schema.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/contracts/migrated-gate-result.schema.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/contracts/promotion-record.schema.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/contracts/payload-evidence.schema.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/contracts/install-verification-result.schema.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/contracts/release-readiness-result.schema.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:specs/xplat-007-python-tooling-and-release-gate-migration/contracts/active-path-guard-result.schema.json
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:docs/ai/specs/.process/XPLAT-007-workflow.md
git show 0ff2d8d731698cde02b334cdc3b2a377216b5d45:docs/ai/specs/.process/XPLAT-007-design-concept.md
git checkout 0ff2d8d731698cde02b334cdc3b2a377216b5d45 -- specs/xplat-007-python-tooling-and-release-gate-migration
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-07-05-xplat-007-post-merge-hygiene.md`.

---

## XPLAT-008 Claude/Codex Cutover and Universal Install Release Gate

### Provenance

| Spec | PR | Title | Merged at | Merge commit |
|------|----|-------|-----------|--------------|
| XPLAT-008 | #289 | `feat(speckit-pro): Update Active Installed-Runtime Surface Cutover` | 2026-07-07T00:54:54Z | `59c18b2dcf79284182f6f5932e61716db0d58090` |
| XPLAT-008 | #290 | `feat(speckit-pro): Update Payload, Release, and Public Docs Gates` | 2026-07-07T01:14:33Z | `1793128875dd0a31e9fafd606eaa55e92123d63e` |
| XPLAT-008 | #291 | `feat(speckit-pro): Update Native UAT, Update, and Safe Repair` | 2026-07-07T01:25:47Z | `66defab977c166bff8726724cdb728b95eec0165` |
| XPLAT-008 | #292 | `fix(release): unblock XPLAT-008 readiness gate` | 2026-07-07T02:00:33Z | `9507fd452a3e344c1912b449f3bb4f2c38437b38` |

### Summary

XPLAT-008 shipped active Claude/Codex installed-runtime cutover to the Python
runner, generated Claude and Codex payload rebuilds, payload completeness and
release-readiness gates, public docs and README claim alignment, UAT matrix
validation, install-health repair controls, partial Codex/macOS installed-cache
UAT evidence, and a deterministic release block for incomplete native operator
UAT.

The implementation is archived, but public native Windows/macOS/Linux support
claims remain blocked until all six operator UAT rows pass in
`docs/ai/specs/.process/XPLAT-008-uat-matrix.md`.

### Canonical Artifacts

- `speckit-pro/speckit_pro_runner/gates/release.py`
- `speckit-pro/speckit_pro_runner/gates/payloads.py`
- `speckit-pro/speckit_pro_runner/gates/active_path_guard.py`
- `speckit-pro/speckit_pro_runner/helpers/install.py`
- `dist/claude/speckit-pro/`
- `dist/codex/speckit-pro/`
- `docs-site/src/content/docs/install/claude-code.md`
- `docs-site/src/content/docs/install/codex.md`
- `docs-site/src/content/docs/security-and-trust.md`
- `docs-site/src/content/docs/troubleshooting.md`
- `docs-site/src/content/docs/update-and-rollback.md`
- `docs/ai/specs/.process/XPLAT-008-workflow.md`
- `docs/ai/specs/.process/XPLAT-008-design-concept.md`
- `docs/ai/specs/.process/XPLAT-008-release-readiness.md`
- `docs/ai/specs/.process/XPLAT-008-uat-matrix.md`
- `docs/ai/specs/.process/XPLAT-008-uat-codex-macos.md`
- `tests/speckit-pro/unit/fixtures/installed-plugin-release/`

### Recovery Commands

```text
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/spec.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/plan.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/tasks.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/research.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/data-model.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:specs/xplat-008-claude-codex-cutover-universal-install-release-gate/quickstart.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:docs/ai/specs/.process/XPLAT-008-workflow.md
git show 9507fd452a3e344c1912b449f3bb4f2c38437b38:docs/ai/specs/.process/XPLAT-008-design-concept.md
git checkout 9507fd452a3e344c1912b449f3bb4f2c38437b38 -- specs/xplat-008-claude-codex-cutover-universal-install-release-gate
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-07-07-xplat-008-post-merge-hygiene.md`.

---

## XPLAT-009 Plugin Source and Payload Bash Eradication

### Provenance

| Spec | PR | Title | Merged at | Merge commit |
|------|----|-------|-----------|--------------|
| XPLAT-009 | #295 | `docs(xplat): plan Bash eradication backstop` | 2026-07-07T14:40:51Z | `bb744db61fe569514c5b856bc4b20cbf478fd8d0` |
| XPLAT-009 | #297 | `feat(xplat): eradicate plugin Bash runtime surface` | 2026-07-08T20:05:01Z | `7bc6be1a9faaa3113f8db903188ddb49a445e7ce` |
| XPLAT-009 | #299 | `fix(runner): resolve python interpreter and home directory on windows` | 2026-07-08T22:44:29Z | `fa7cd5671a40350e8a3feb9a13ebc3900591eef1` |

### Summary

XPLAT-009 removed the remaining plugin-source Bash substrate while preserving
the XPLAT-008 installed-runtime contract of direct Python 3.11+
`speckit_pro_runner` invocation. The merged implementation ported active
plugin-source script behavior to Python runner/helper/gate operations, deleted
the remaining live `.sh` files under `speckit-pro/`, replaced active Bash
instructions in skills and agent guidance, rebuilt generated Claude and Codex
payloads from source, and proved source, generated payloads, and a bounded
installed-cache artifact pass one Python-backed zero-Bash guard with a
reviewable historical allowlist. It shipped in speckit-pro 2.18.0; PR #299
followed up with a Windows interpreter/home-directory resolution fix. Repo-wide
Bash confinement outside the plugin package was completed by XPLAT-010.

### Canonical Artifacts

- `speckit-pro/speckit_pro_runner/gates/active_path_guard.py`
- `speckit-pro/speckit_pro_runner/gates/registry.py`
- `speckit-pro/speckit_pro_runner/gates/release.py`
- `speckit-pro/speckit_pro_runner/helpers/read_only.py`
- `speckit-pro/speckit_pro_runner/helpers/registry.py`
- `dist/claude/speckit-pro/`
- `dist/codex/speckit-pro/`
- `scripts/refresh-release-artifacts.py`
- `docs/ai/specs/.process/XPLAT-009-workflow.md`
- `docs/ai/specs/.process/XPLAT-009-design-concept.md`
- `docs/ai/specs/.process/XPLAT-009-source-inventory.md`
- `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json`
- `docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json`
- `docs/ai/specs/.process/XPLAT-009-zero-bash-guard-result.json`
- `docs/ai/specs/.process/XPLAT-009-release-readiness-result.json`
- `docs/ai/specs/.process/XPLAT-009-retrospective.md`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/`
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/contracts/`

### Recovery Commands

```text
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/spec.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/plan.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/tasks.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/research.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/data-model.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/quickstart.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/SPEC-MOC.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/contracts/historical-allowlist-entry.schema.json
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/contracts/installed-cache-proof.schema.json
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/contracts/zero-bash-guard-request.schema.json
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/contracts/zero-bash-guard-result.schema.json
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/.process/uat-runbook.md
git show 7bc6be1a9faaa3113f8db903188ddb49a445e7ce:specs/xplat-009-plugin-source-and-payload-bash-eradication/.process/final-reviewability/gate-state.json
git checkout 7bc6be1a9faaa3113f8db903188ddb49a445e7ce -- specs/xplat-009-plugin-source-and-payload-bash-eradication
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-07-08-xplat-009-post-merge-hygiene.md`.

---

## XPLAT-010 Repository Bash Confinement and CI Dispatch Guard

### Provenance

XPLAT-010 merged as the complete no-gap PR stack #311 through #328 on
2026-07-11. The final merge commit and complete recovery source is
`ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29`; all 18 review branches were
deleted. Exact PR titles, merged-at timestamps, merge commits, and head branches
are recorded in
`.specify/memory/archive-reports/2026-07-11-xplat-010-post-merge-hygiene.md`.

## 2026-07-30 - ART-001 Post-Merge Archive Cleanup

### ART-001

- PRs: https://github.com/racecraft-lab/racecraft-plugins-public/pull/407 and
  the follow-up fix
  https://github.com/racecraft-lab/racecraft-plugins-public/pull/409
- Titles: `feat(speckit-pro): add the artifact gallery brand kit, routing
  catalog, and validation` and `fix(speckit-pro): scan artifact script bodies
  for external references and prohibited constructs`
- Merged at: `2026-07-30T13:12:39Z` and `2026-07-30T14:43:55Z`
- Source: `specs/art-001-brand-kit-gallery-foundation`
- Canonical artifacts: the six-file gallery under
  `speckit-pro/artifact-gallery/` and its two `dist/` materializations, the
  payload-completeness gate fix, the regenerated installed-cache proofs, and
  `tests/speckit-pro/unit/test-artifact-gallery.py`.
- Governance note: this spec does change the shipped plugin payload — the
  gallery directory is new shipped content — so the generated artifact contract
  was part of its merge, not of this cleanup.

ART-001 is the foundation the four template-port specs consume: the Racecraft
brand kit, the gallery manifest schema, and the single-file-SPA contract. Its
highest-value output was verification rather than code — seven defects surfaced
after the implementation was written, the most serious being a fail-silent gap
in the payload builder that would have shipped every payload without the gallery
directory at all.

### Manual acceptance discharged before merge

T026 and T027 ran on 2026-07-29 over `file://`: 12 of 12 scenarios passed, none
unrun. The feature retrospective contradicts itself here — its narrative section
records the run, its task-execution section still lists both tasks open — and
the workflow record and the merge both proceeded on the former. Noted, not
silently reconciled.

### Harness relocation

`.process/acceptance-harness.html` was forward-looking rather than exhaust: it
is the evidence behind the 12-of-12 result and the reference implementation the
roadmap directs a later spec to reuse. It moved to
`docs/ai/specs/.process/ART-001-acceptance-harness.html` before removal, and the
two references pointing into the spec folder were repointed.

### Known gap carried forward

ART-001 ships no gallery artifacts of its own, so roughly half its validation
surface runs against synthetic fixtures. Re-running the twelve manual scenarios
against a real shipped artifact belongs to ART-002.

Detailed recovery and verification evidence:

- `.specify/memory/archive-reports/2026-07-30-art-001-post-merge-hygiene.md`

---

## 2026-07-30 - CAR-005 Post-Merge Archive Cleanup

### CAR-005

- PRs: https://github.com/racecraft-lab/racecraft-plugins-public/pull/411 and
  https://github.com/racecraft-lab/racecraft-plugins-public/pull/412
- Titles: `feat(car-005): add a reference simulator that pins what happens when
  an agent's model is unavailable` and `feat(car-005): extend the route-fallback
  simulator with structural rejection and recovery cases`
- Merged at: `2026-07-30T20:53:03Z` and `2026-07-30T21:19:49Z`
- Merge commits: `3ba89fa4bee8b1cc6402b47a473181d3f96eed12` and
  `e31475fa7cb36aed83b76bc63d423bcb10557b97`
- Source: `specs/car-005-availability-fallback-recovery`
- Canonical artifacts: three closed Claude route contracts, one eighteen-case
  replay corpus, one standard-library simulator module, and one durable Layer 4
  test owner under `tests/speckit-pro/`.
- Governance note: repository-only validation assets; no production routing,
  installer, manifest, scheduler, default, release behavior, plugin payload, or
  version changed.

CAR-005 pins bounded resolution and recovery semantics synthetically, ahead of
any real route policy. `no_safe_route` is report-only — it names the unresolved
agent, the attempted routes, each rejection reason, and rollback remediation,
and mutates no shipped agent file. The two slices delivered as a stacked chain
and slice 2 held the append-only seam: no schema file and no suite-manifest
entry changed, and corpus additions landed only at the tail of `cases[]`.

### Known gap carried forward

The simulator declares `POLICY_SCHEMA_PATH` and `SNAPSHOT_SCHEMA_PATH` but reads
neither, so it validates the report it emits and not the policy or snapshot it
accepts. All eighteen committed policies and snapshots satisfy both contracts,
so closing the gap changes no pinned report; the correction is a follow-up
change against `main`, and CAR-006 inherits the gap until then.

### No relocation required

Every machine-enforced artifact was authored directly under
`tests/speckit-pro/`, and a tree-wide search for the bare directory name found
no live reader before removal. Unlike CAR-004 and G56R-004 the feature carried
no unrun operator procedure, so nothing had to move out of the folder first.

Detailed recovery and verification evidence:

- `.specify/memory/archive-reports/2026-07-30-car-005-post-merge-hygiene.md`

---

## 2026-07-29 - G56R-004 Post-Merge Archive Cleanup

### G56R-004

- PR: https://github.com/racecraft-lab/racecraft-plugins-public/pull/403
- Title: `feat(g56r-004): add policy controls and adaptive comparators`
- Merged at: `2026-07-29T19:36:55Z`
- Merge commit: `77e7dfff017597c6c93118a30eeb2b1c08d734de`
- Source: `specs/g56r-004-policy-controls-adaptive-comparators`
- Canonical artifacts: two closed Codex specification schemas, four governed
  control fixtures, three standard-library helpers, and three durable Layer 4
  test owners under `tests/speckit-pro/`.
- Governance note: repository-only validation assets; no production routing,
  installer, manifest, scheduler, default, release behavior, plugin payload, or
  version changed.

G56R-004 freezes the Codex-local control and comparison evidence that G56R-005
and G56R-011 consume later. The implementation preserves the CAR-004 mirror
shape while deriving actual twin evidence from source artifacts and retaining
the one sanctioned platform naming divergence.

### Known gap carried forward

The operator-authorized ChatGPT sign-in smokes remain unrun, so SC-014 through
SC-016 are partial for live observation. Deterministic smoke planning, refusal,
sealing, bounds, exact-treatment, cache-isolation, and privacy evidence remain
green; no live result is inferred.

### Runbook relocation

The feature quickstart contained the forward-looking operator procedure rather
than pure planning exhaust. It was moved to
`docs/ai/specs/.process/G56R-004-live-smoke-runbook.md` before the active folder
was removed. No schema or fixture relocation was needed because all live
machine-enforced artifacts already live under `tests/speckit-pro/`.

Detailed recovery and verification evidence:

- `.specify/memory/archive-reports/2026-07-29-g56r-004-post-merge-hygiene.md`

---

## 2026-07-28 - CAR-004 Post-Merge Archive Cleanup

### CAR-004

- PR: https://github.com/racecraft-lab/racecraft-plugins-public/pull/401
- Title: `feat(car-004): add the three routing policy controls and their
  comparison rules`
- Merged at: `2026-07-29T00:58:26Z`
- Merge commit: `8b224ce8d1fbaba89606772a4d51401ac754a70b`
- Source: `specs/car-004-policy-controls-comparators`
- Canonical artifacts: two content-addressed schemas under
  `tests/speckit-pro/layer6-efficiency/contracts-claude/`, four frozen instances
  under `tests/speckit-pro/layer6-efficiency/fixtures-controls/`, the
  `claude_policy_controls.py` and `claude_control_comparison.py` Layer 6 modules
  sharing one fail-closed schema engine, the operator-only
  `run-control-smoke.py` driver, and three deterministic Layer 4 unit suites.
- Governance note: zero production files. The change is validation assets only,
  touching nothing under `speckit-pro/` and altering no shipped default or
  generated payload.

CAR-004 preserves the freeze ordering the feature exists to protect: the
comparison rule is frozen before any result exists to measure it against. No
CAR-004 artifact states or implies which side wins, and the reserved partition is
guarded so CAR-011's comparison cannot reuse workload selection already saw.

### Known gap carried forward

Task T062 — the three bounded, developer-local, subscription-authenticated live
smokes — was never run, so SC-009, SC-026, SC-027, SC-029, SC-030, and SC-031
ship unevidenced. This was named in the PR body before merge, not discovered
afterwards.

### Runbook relocation

The feature's `.process/` directory held one forward-looking artifact rather than
pure exhaust. `CAR-004-live-smoke-runbook.md` is the only operator instruction
set that closes the six criteria above, and the preserved `CAR-004-workflow.md`
pointed at it, so it was moved to `docs/ai/specs/.process/` and its three
archived-path references were repointed at git provenance. The PR packet under
`.process/pr-packets/` is exhaust and was removed with the folder.

No contract relocation was needed. Unlike CAR-003, CAR-004 authored both JSON
Schema documents directly into the test tree, and a tree-wide search for the bare
directory name found zero readers outside `specs/**` before removal.

Detailed recovery and verification evidence:

- `.specify/memory/archive-reports/2026-07-28-car-004-post-merge-hygiene.md`

---

## 2026-07-27 - CAR-003 and G56R-003 Post-Merge Archive Cleanup

### CAR-003

- PR: https://github.com/racecraft-lab/racecraft-plugins-public/pull/385
- Title: `feat(car-003): add the evaluation platform that turns capability
  evidence into qualification evidence`
- Merged at: `2026-07-26T23:49:26Z`
- Merge commit: `9fab2083cd74fcaca28cb6589cf8705e0e8ddd3c`
- Source: `specs/car-003-evaluation-runner-scoring`
- Canonical artifacts: `speckit-pro/speckit_pro_runner/materializer.py` as the
  sole shipped production surface, the six
  `docs/ai/research/claude-car-003-*.json` evidence files, six Layer 6
  `claude_*` qualification modules with their fixtures, and eight deterministic
  unit suites.
- Governance note: the final gate recorded a size-only block with a typed size
  exception preserved at `docs/ai/specs/.process/CAR-003-size-exception.md`.

### G56R-003

- PR: https://github.com/racecraft-lab/racecraft-plugins-public/pull/386
- Title: `feat(g56r-003): add evaluation runner scoring`
- Merged at: `2026-07-27T03:11:13Z`
- Merge commit: `dcceef86daed97fe42e81a43c90e82556457dc48`
- Source: `specs/g56r-003-evaluation-runner-scoring`
- Canonical artifacts:
  `speckit-pro/speckit_pro_runner/agent_materialization.py`,
  `docs/ai/research/codex-g56r-003-effort-ladder.json`, nine closed schemas
  under `tests/speckit-pro/layer6-efficiency/contracts/`, eight
  `qualification_*` and `codex_*` Layer 6 modules, twelve per-role fixtures
  with a single shared corpus manifest, and six deterministic unit suites.

Both lanes preserve the no-qualification boundary: only non-eligible
calibration partitions are accepted, and outputs are limited to
calibration-complete, inconclusive, or invalid. Neither selects preferred
routes, orders fallbacks, nor changes installed defaults.

### Contract relocation

Both spec folders held contract schemas that live code still read, so the
archive moved them into the test tree before removing the folders:

- CAR-003's nine to `tests/speckit-pro/layer6-efficiency/contracts-claude/`,
  repointing one Layer 6 library and five unit tests.
- G56R-003's nine specification-side copies to
  `tests/speckit-pro/layer6-efficiency/contracts-codex-specification/`,
  repointing two unit tests.

Each schema was moved rather than copied, so every artifact still has exactly
one home. `tests/speckit-pro/layer6-efficiency/contracts/` was left untouched.
CAR-012 and G56R-012 Key Files were repointed to the new paths.

Detailed recovery and verification evidence:

- `.specify/memory/archive-reports/2026-07-27-car-003-post-merge-hygiene.md`
- `.specify/memory/archive-reports/2026-07-27-g56r-003-post-merge-hygiene.md`

---

## 2026-07-24 - CAR-002 and G56R-002 Post-Merge Archive Cleanup

### CAR-002

- PR: https://github.com/racecraft-lab/racecraft-plugins-public/pull/369
- Title: `feat(car-002): capture Claude runtime capability probe evidence and trace contracts`
- Merged at: `2026-07-23T02:11:51Z`
- Merge commit: `4eea291ab71f47f03ab14da6af19e94381c2af2f`
- Source: `specs/car-002-capability-probing-telemetry`
- Canonical artifacts: `docs/ai/research/claude-runtime-capability-snapshot.json`,
  `docs/ai/research/claude-telemetry-capability-profile.json`,
  `docs/ai/research/claude-trace-contract.schema.json`, and the corresponding
  Layer 6 adapter plus deterministic unit fixtures.

### G56R-002

- PRs: https://github.com/racecraft-lab/racecraft-plugins-public/pull/366,
  https://github.com/racecraft-lab/racecraft-plugins-public/pull/367, and
  https://github.com/racecraft-lab/racecraft-plugins-public/pull/368
- Merge commits: `8d11815eceefe25683f966241de722592f86d58e`,
  `470faccb6eea814ad23d49602178a52490d1ccc7`, and
  `06d54487fd3b507333f96e571223805c1956998b`
- Source: `specs/g56r-002-capability-discovery-telemetry`
- Canonical artifacts: `docs/ai/research/codex-g56r-002-capability-evidence.md`,
  `docs/ai/research/codex-g56r-002-executable-candidate-freeze.json`, focused
  Layer 6 capability/treatment modules and contracts, and deterministic replay
  and completed-marker fixtures.

Detailed recovery and verification evidence:

- `.specify/memory/archive-reports/2026-07-24-car-002-post-merge-hygiene.md`
- `.specify/memory/archive-reports/2026-07-24-g56r-002-post-merge-hygiene.md`


---

## 2026-07-16 - HRNS-001 and G56R-001 Post-Merge Archive Sweep

### Provenance

| Spec | PR | Title | Merged at | Merge commit |
|---|---|---|---|---|
| HRNS-001 | [#357](https://github.com/racecraft-lab/racecraft-plugins-public/pull/357) | `fix(speckit-pro): Enable PR packet emission` | `2026-07-16T12:33:28Z` | `dcef3e90896e52b32bdb668ec55dd29ea7ba282a` |
| G56R-001 | [#360](https://github.com/racecraft-lab/racecraft-plugins-public/pull/360) | `docs(speckit-pro): align G56R official-source route evidence` | `2026-07-16T15:52:57Z` | `191642962e55df21000a5303f36e9010a14898d2` |

### Summary

- Archived HRNS-001 after its taxonomy and packet-emission implementation
  merged with green CI and resolved review threads.
- Archived G56R-001 after its official-source schema-v2 evidence package merged
  on top of shared CAR/G56R foundation PR #362.
- Removed both completed active spec directories while preserving all authored
  workflow/design evidence under `docs/ai/specs/.process/`.
- Marked HRNS-002, HRNS-003, and G56R-002 ready without advancing specs that
  still have unmet dependencies.

### Canonical Artifacts

- `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`
- `speckit-pro/speckit_pro_runner/helpers/pr_emission.py`
- `docs/ai/research/codex-agent-route-candidates.md`
- `docs/ai/research/codex-agent-route-candidate-manifest.json`
- `docs/ai/research/agent-route-candidate-manifest.schema.json`
- `docs/ai/specs/agent-routing-parity-contract.md`
- `docs/ai/specs/.process/HRNS-001-*`
- `docs/ai/specs/.process/G56R-001-*`

### Recovery

```text
git checkout dcef3e90896e52b32bdb668ec55dd29ea7ba282a -- specs/hrns-001-harness-surface-inventory-gap-taxonomy
git checkout 191642962e55df21000a5303f36e9010a14898d2 -- specs/g56r-001-candidate-route-baseline
```

Detailed artifact-level recovery commands and cleanup verification are stored
in `.specify/memory/archive-reports/2026-07-16-hrns-001-post-merge-hygiene.md`
and `.specify/memory/archive-reports/2026-07-16-g56r-001-post-merge-hygiene.md`.

---

## CAR-001 Candidate Route Baseline and Role Contracts

### Provenance

| Spec | PR | Title | Merged at | Merge commit |
|------|----|-------|-----------|--------------|
| CAR-001 | #350 | `docs(speckit-pro): add the Claude agent route-candidate research baseline` | 2026-07-15T13:42:16Z | `725be949b856724a073622900bd168d29b2f4603` |

### Summary

CAR-001 shipped the Claude agent route-candidate baseline and role-contract
handoff for the CAR-001..CAR-011 sequence. The merged research record and JSON
manifest cover all twelve named agents, pin the immutable comparator to
`speckit-pro-v2.19.1`, distinguish project-level route eligibility from
environment-time availability, record capability questions for CAR-002, label
bare prompt emulation as non-release evidence, and keep all executable-route
claims deferred until probing and qualification.

### Canonical Artifacts

- `docs/ai/research/claude-agent-route-candidates.md`
- `docs/ai/research/claude-agent-route-candidate-manifest.json`
- `docs/ai/specs/.process/CAR-001-workflow.md`
- `docs/ai/specs/.process/CAR-001-design-concept.md`
- `docs/ai/specs/claude-agent-routing-technical-roadmap.md`
- `docs/ai/specs/claude-agent-routing-roadmap-MOC.md`

### Recovery Commands

```text
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/spec.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/plan.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/tasks.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/research.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/data-model.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/quickstart.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/contracts/agent-route-candidate-manifest.schema.json
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/checklists/requirements.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/checklists/traceability.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/checklists/research-rigor.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/checklists/data-integrity.md
git show 725be949b856724a073622900bd168d29b2f4603:specs/car-001-candidate-route-baseline/SPEC-MOC.md
git show 725be949b856724a073622900bd168d29b2f4603:docs/ai/specs/.process/CAR-001-workflow.md
git show 725be949b856724a073622900bd168d29b2f4603:docs/ai/specs/.process/CAR-001-design-concept.md
git checkout 725be949b856724a073622900bd168d29b2f4603 -- specs/car-001-candidate-route-baseline
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-07-15-car-001-post-merge-hygiene.md`.

### Summary

XPLAT-010 replaced active repository Bash orchestration, validators, helpers,
hooks, replay/parity/evaluation runners, and release tooling with Python 3.11+
standard-library entrypoints. It made the suite manifest authoritative, added
the repository Bash-confinement gate and fixed release-excluded vendored
`.specify/**` allowlist, restored `estimate-spec-size`, added Linux container
and advisory Windows preflight, and shipped deterministic consumer release-note
validation and Highlights composition.

The final neutral-PATH deterministic suite passed `2512/2512`. T108 completed
with hosted relevant-path, docs-only, failure-propagation, manual-main, and four
PR-trigger canaries. T117 completed when non-strict `main` branch protection
required exactly the three PR checks plus both Linux container sentinels.
Public native-platform claims remain blocked by the XPLAT-008 operator UAT
matrix, not by XPLAT-010.

### Canonical Artifacts

- `tests/speckit-pro/suite-manifest.json`
- `tests/speckit-pro/run-all.py`
- `tests/speckit-pro/run-layer-scripts.py`
- `tests/speckit-pro/unit/`
- `tests/speckit-pro/parity/bash-to-python/`
- `speckit-pro/speckit_pro_runner/gates/active_path_guard.py`
- `speckit-pro/speckit_pro_runner/gates/release.py`
- `scripts/release_note_policy.py`
- `scripts/compose-release-notes.py`
- `.github/workflows/pr-checks.yml`
- `.github/workflows/container-preflight.yml`
- `.github/workflows/release.yml`
- `docs/ai/specs/.process/XPLAT-010-*`

### Recovery Commands

```text
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/spec.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/plan.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/tasks.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/research.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/data-model.md
git show ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29:specs/xplat-010-repository-bash-confinement/quickstart.md
git checkout ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29 -- specs/xplat-010-repository-bash-confinement
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-07-11-xplat-010-post-merge-hygiene.md`.

## 2026-08-09 — ART-006 Autopilot Staging archived

Merged in PR #422 at `5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff`, then archived
from `chore/archive-art-006-post-merge`.

Shipped the `plan` / `implement` / `full` stage vocabulary on both distributions,
the registered runner operation `resolve-autopilot-stage` that both reach by
operation identifier, a stage-bounded phase scan, a registered stage-mirror check
in the phase-coverage guard, durable stage state in the workflow file with the
session state file as its mirror, and a cross-distribution argument-parity
assertion sited in the unit test rather than the existence-only structural
validator.

Recorded CI anomaly: the merge carries one failed non-required check,
`Analyze (actions)`, stranded by the 2026-08-06 GitHub Actions major outage
(incident `qcvjkzcs7j74`). All required checks passed and `mergeStateStatus` was
`CLEAN`. Default-setup CodeQL runs cannot be retried through the API.

Known gaps carried forward as ready roadmap specs: ART-014 (phase-guard
enforcement repair — the shipped workflow-identity check is inert two ways over)
and ART-015 (spec-size re-estimation trigger — the estimator is sound but is only
ever fed scoping-time signals).

### Recovery Commands

```text
git show 5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff:specs/art-006-autopilot-staging/spec.md
git show 5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff:specs/art-006-autopilot-staging/plan.md
git show 5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff:specs/art-006-autopilot-staging/tasks.md
git show 5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff:specs/art-006-autopilot-staging/research.md
git show 5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff:specs/art-006-autopilot-staging/data-model.md
git show 5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff:specs/art-006-autopilot-staging/quickstart.md
git checkout 5e184e332b8c8f8442cdbda37c3bdc45cb6d62ff -- specs/art-006-autopilot-staging
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-08-09-art-006-post-merge-hygiene.md`.

## 2026-08-12 — ART-002 Draft-PR Template Set archived

Merged across three pull requests and archived from
`chore/archive-art-post-merge`:

- PR #425 at `a9e8d30764fd1dc28ea07734d4dbe7c0952e1294` — slice 1,
  `implementation-plan` and `spec-explainer`
- PR #427 at `4ecb1b4b441cbb85015586612190a7bc340f0c9c` — slice 2,
  `code-approaches` and `module-map`
- PR #430 at `425364b7be34d5b88605012d0492c0e97bdbefaf` — the recorded
  acceptance result

Shipped four Racecraft-branded, self-contained single-file gallery templates
with declared fill regions and export affordances, four catalog entries flipped
to `shipped`, and two Layer 4 tests covering fill regions and the gallery
manifest. Every pinned export string holds character for character; all four
templates make zero non-theme `setItem` calls; the `module-map` drawing keeps an
accessible name with no `role="img"`, so all seventeen internal labels stay
reachable.

CI was clean on all three: 21 pass and 1 skip on #425 and #427, 26 pass and 4
skip on #430, zero failures.

The acceptance runbook was preserved by relocation rather than deleted, at
`docs/ai/specs/.process/ART-002-uat-runbook.md`. Every executed step passed;
fifteen of sixty-one steps are recorded as *not executed* across four kinds of
check, each with its substitute, and no step is a pass on partial evidence.

Both slices ran over the declared 530-LOC reviewability budget at 1494 and 2027
measured, both size-only blocks with no correctness finding.

ART-002's completion discharges ART-007's last dependency.

### Recovery Commands

```text
git show 425364b7be34d5b88605012d0492c0e97bdbefaf:specs/art-002-draft-pr-template-set/spec.md
git show 425364b7be34d5b88605012d0492c0e97bdbefaf:specs/art-002-draft-pr-template-set/plan.md
git show 425364b7be34d5b88605012d0492c0e97bdbefaf:specs/art-002-draft-pr-template-set/tasks.md
git show 425364b7be34d5b88605012d0492c0e97bdbefaf:specs/art-002-draft-pr-template-set/research.md
git show 425364b7be34d5b88605012d0492c0e97bdbefaf:specs/art-002-draft-pr-template-set/data-model.md
git show 425364b7be34d5b88605012d0492c0e97bdbefaf:specs/art-002-draft-pr-template-set/quickstart.md
git checkout 425364b7be34d5b88605012d0492c0e97bdbefaf -- specs/art-002-draft-pr-template-set
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-08-12-art-002-post-merge-hygiene.md`.

## 2026-08-12 — ART-012 Implementation-Notes Capture archived

Merged in PR #426 at `1916d8c917eea4892035daafe4c02d2558e203f3`, then archived
from `chore/archive-art-post-merge` in the same commit as ART-002.

Shipped a durable per-task implementation-notes record appended on the turn each
task completes, a combined deviations/edge-cases/surprises field in all three
authored Task Result templates, an explicit "None" entry so silence stays
distinguishable from an unreported task, the same contract documented on both
the Claude and Codex distributions, a Layer 4 test asserting the two platform
documents agree, and a correction to a stale batched-delivery claim in the Agent
Teams reference. Six production files, 269 added production lines. CI clean: 21
pass, 1 skip, zero failures.

An operator amendment reversed a Clarify consensus that had narrowed the
per-task append guarantee, restoring the literal guarantee and adding FR-006 and
a sixth production file. An adversarial audit run after implementation found
five real defects, four introduced by the run, two of which would have shipped
green — including the record this feature produced violating the contract this
feature ships.

Known gaps carried forward, none yet a roadmap spec: the Layer 6 Codex
qualification corpus has no regeneration tooling; a spec-artifact consistency
check would have caught three of the run's four cascade failures; and the record
contract has no answer for a late-arriving fuller summary.

### Recovery Commands

```text
git show 1916d8c917eea4892035daafe4c02d2558e203f3:specs/art-012-implementation-notes-capture/spec.md
git show 1916d8c917eea4892035daafe4c02d2558e203f3:specs/art-012-implementation-notes-capture/plan.md
git show 1916d8c917eea4892035daafe4c02d2558e203f3:specs/art-012-implementation-notes-capture/tasks.md
git show 1916d8c917eea4892035daafe4c02d2558e203f3:specs/art-012-implementation-notes-capture/contracts/implementation-notes-record.md
git show 1916d8c917eea4892035daafe4c02d2558e203f3:specs/art-012-implementation-notes-capture/contracts/task-result-reporting-field.md
git checkout 1916d8c917eea4892035daafe4c02d2558e203f3 -- specs/art-012-implementation-notes-capture
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-08-12-art-012-post-merge-hygiene.md`.

---

## 2026-08-13 — ART-014 Phase-Guard Enforcement Repair archived

Merged in PR #433 at `12d8c2d48469df9293227cb2c28cf05a4847fc61`, then archived
from `art-014-post-merge-hygiene`.

Shipped the repair that makes the autopilot phase guard's workflow-identity
check enforce the authority its documentation already promised. The comparison
of the supplied `--workflow` against `autopilot-state.json.workflow_file` now
runs unconditionally, rather than behind a `pr-marker-plan.v2` schema and an
`--expected-head-commit` that a normal autopilot run supplies neither of, and its
findings report under a new `workflow_authority_errors` key registered in the
`status-evidence` tuple the autopilot always selects. Before the repair, a run
resuming against the wrong specification exited 0 and reported pass. Also closed
a third short-circuit found during Clarify: repository-root resolution walked the
state path as supplied, so a state file genuinely inside the repository resolved
no root when named relatively from a subdirectory, making the check depend on
path spelling rather than on file location. Five production files, 488 added
production lines, 24 functional requirements, 27 of 27 tasks. The suite moved
from 7378 to 7396. CI clean on the final head: 20 pass, 1 skip, zero failures.

Advisory status became a recorded decision rather than an accident. A
`PROBLEM_KEY_INTENT` map classifies all 21 emitted problem keys under a closed
three-value vocabulary, enforced by a test that derives the key set from a real
report and fails in both directions — an unclassified emitted key, and a verdict
recorded for a key the guard never emits.

The load-bearing evidence is a canary, not a pass rate. A skipped comparison and
a satisfied comparison both report no error and both exit zero, so 54 green
corpus files proved nothing on their own; only the deliberately mismatched canary
flipping from exit 0 to exit 1 established that the repair took. Applying that
same principle downstream found four further defects that neither the suite nor
CI could see, three of them in this feature's own paperwork, all fixed before
merge: the corpus evidence overclaimed what a present-and-empty key proves, both
protocol references undercounted their own branch table after a review fix added
a third skip, a malformed roadmap row silently dropped ART-017's blocking
dependency, and quickstart scenario 4 promised an observable its own commands
cannot emit.

Three follow-ups were opened from this run and are recorded on the HTML artifacts
roadmap: ART-016 for Claude-side live pull-request commit authority, ART-017 to
arm the three accidentally-advisory keys, and ART-018 to repair three governance
matchers that report clean on input they should catch. ART-017 is unblocked by
this merge.

### Recovery Commands

```text
git show 12d8c2d48469df9293227cb2c28cf05a4847fc61:specs/art-014-phase-guard-enforcement-repair/spec.md
git show 12d8c2d48469df9293227cb2c28cf05a4847fc61:specs/art-014-phase-guard-enforcement-repair/plan.md
git show 12d8c2d48469df9293227cb2c28cf05a4847fc61:specs/art-014-phase-guard-enforcement-repair/tasks.md
git show 12d8c2d48469df9293227cb2c28cf05a4847fc61:specs/art-014-phase-guard-enforcement-repair/research.md
git show 12d8c2d48469df9293227cb2c28cf05a4847fc61:specs/art-014-phase-guard-enforcement-repair/quickstart.md
git checkout 12d8c2d48469df9293227cb2c28cf05a4847fc61 -- specs/art-014-phase-guard-enforcement-repair
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-08-13-art-014-post-merge-hygiene.md`.

## 2026-08-13 — ART-011 Scaffold Integration archived

Merged in PR #434 at `6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b` on
2026-08-13T21:06:20Z by `fgabelmannjr`. CI on the final head `34cbd591`: 19 pass,
1 skipped, 0 failures. The active folder is removed; 13 tracked files.

`speckit-scaffold-spec` now opens with a read-only blind-spot pass, reusing the
shipped `codebase-analyst`, and closes by handing the operator the exact command
that starts the planning stage. Both platform variants ship the change. grill-me
is untouched.

The feature shipped inverted from its design. It was specified to *chain*
in-session into the autopilot plan stage so one invocation would end at a reviewed
draft PR. `speckit-autopilot/SKILL.md` carries `disable-model-invocation: true`,
which blocks the `Skill` tool outright and exists precisely to stop a seven-phase
auto-committing run from being model-triggerable. Scaffold was demoted to printing
the command, and the post-planning apparatus the chain implied was deleted. Nine
requirements were amended and five superseded; `contracts/chain-handoff.md` shipped
with a banner stating that no section is unchanged.

Two lessons are recorded rather than smoothed. A green `gh pr checks` is not
evidence unless the **check count** is right: mid-review this PR reported clean
while only 4 of 20 checks had run, because a conflicted PR cannot build
`refs/pull/N/merge` and GitHub skips every `pull_request` workflow. And the
feature took a skill from 497 lines — three under the documented ceiling — to 984.

Two gaps leave with this archive rather than closing. Layer 2 trigger evaluation
never ran while this feature rewrote the `description` from 975 to 1013
characters, which is the string skill selection matches on; Layer 2 is
`live_only` and does not execute in CI, and its runners are operator-only because
they move the installed skill directory aside. ART-019 owns the size gap and its
slice D supersedes FR-022.

### Canonical Artifacts

- `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` and
  `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md`
- `tests/speckit-pro/layer2-trigger/evals/speckit-scaffold-spec-trigger.json` and
  its `codex-evals/` mirror
- Generated payload copies under `dist/claude`, `dist/codex`, and the
  installed-cache proofs

Historical evidence stays under `docs/ai/specs/.process/`:
`ART-011-design-concept.md` and `ART-011-workflow.md`. No retrospective was
produced; the workflow file records that step as pending and the state file was
wrong to claim otherwise.

### Recovery Commands

```text
git show 6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b:specs/art-011-scaffold-integration/spec.md
git show 6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b:specs/art-011-scaffold-integration/plan.md
git show 6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b:specs/art-011-scaffold-integration/tasks.md
git show 6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b:specs/art-011-scaffold-integration/research.md
git show 6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b:specs/art-011-scaffold-integration/contracts/chain-handoff.md
git show 6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b:specs/art-011-scaffold-integration/contracts/blind-spot-pass.md
git checkout 6437ecd2f12d1ee0e3aaeb54895b9a48a0e3670b -- specs/art-011-scaffold-integration
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-08-13-art-011-post-merge-hygiene.md`.

## 2026-08-14 — ART-003 Final-PR Template Set archived

ART-003 shipped as three stacked slices, one template per pull request, all
merged and archived on 2026-08-14 UTC.

| PR | Template | Merged at | Merge commit |
|---|---|---|---|
| [#435](https://github.com/racecraft-lab/racecraft-plugins-public/pull/435) | `pr-writeup` | `2026-08-14T13:25:49Z` | `ad6cab53395fd410aa7acca05fd29531f0c9cd89` |
| [#436](https://github.com/racecraft-lab/racecraft-plugins-public/pull/436) | `annotated-diff` | `2026-08-14T14:14:24Z` | `6a1518c395fc3fcce4de315a70691eee33f4de94` |
| [#439](https://github.com/racecraft-lab/racecraft-plugins-public/pull/439) | `flowchart` | `2026-08-14T14:54:54Z` | `780a6724915ce481199073de84fa007ca16deb8b` |

CI on each: 19 pass, 1 skipped, 0 failures. Merged by `fgabelmannjr`, base
`main` for all three; slices 2 and 3 were auto-retargeted when their stacked
parents squash-merged. The gallery now carries seven shipped templates of
twenty-one catalogued, and `flowchart` is the first declared read-only.

Every slice landed under its own reviewability declaration — 735 against 758,
724 against 750, 408 against 460 — the first ART spec where none overran. The
budget was re-declared at scaffold on ART-002's realized measurement rather than
the roadmap's original 285 estimate.

Manual acceptance ran in full against the shipped bytes for the first time in
this roadmap: **176 checks, all passing**, on `file://`. The blocker every pull
request had recorded was the browser automation tool's own URL validation, not
Chrome's. The pass found and fixed two defects — a diff row that copied as two
lines because `display: grid` blockifies its cells, and a flowchart link that
left focus behind — and missed a third that code review caught.

### Cleanup

Three active spec folders removed. The acceptance runbook was relocated to
`docs/ai/specs/.process/ART-003-uat-runbook.md` rather than deleted: nothing
cites it, but it is the only committed statement of what acceptance means for
`pr-writeup.html`, and its Step 1 carries the console finding. Design concept
and all three workflow files stay under `docs/ai/specs/.process/`. No
retrospective was produced.

Three gaps leave with the archive: no acceptance record was merged, the three
workflow files still record runbook generation as pending, and slices 2 and 3
merged with every task box unchecked.

### Canonical Artifacts

- `speckit-pro/artifact-gallery/templates/pr-writeup.html`,
  `annotated-diff.html` and `flowchart.html`
- `speckit-pro/artifact-gallery/manifest.json` (three rows flipped to `shipped`)
- `tests/speckit-pro/unit/test-artifact-fill-regions.py` and
  `test-artifact-gallery.py`
- Generated payload copies under `dist/claude`, `dist/codex`, and the
  installed-cache proofs

### Recovery Commands

```text
git checkout ad6cab53395fd410aa7acca05fd29531f0c9cd89 -- specs/art-003-final-pr-template-set
git checkout 6a1518c395fc3fcce4de315a70691eee33f4de94 -- specs/art-003-final-pr-template-set-slice-2
git checkout 780a6724915ce481199073de84fa007ca16deb8b -- specs/art-003-final-pr-template-set-slice-3
```

The detailed archive and verification record is stored in
`.specify/memory/archive-reports/2026-08-14-art-003-post-merge-hygiene.md`.

## 2026-08-14 — ART-003 gap triage, and ART-020 opened

A triage of the five gaps the ART-003 archive carried forward. Three resolve to no
action, one was discharged immediately, and the sweep found the archive had
misdiagnosed one of its own findings. Full record in
`.specify/memory/archive-reports/2026-08-14-art-003-gap-triage-amendment.md`; the
archive report itself is left unedited.

### Discharged

The ART-003 acceptance evidence and the harness that produced it are now in the
repository under `docs/ai/specs/.process/`: `ART-003-uat-results.md`, plus
`ART-003-uat-harness/` carrying `cdp.py`, three drivers, and three results files
totalling 176 rows with every `ok` true. They had been sitting in a session
scratchpad under `/private/tmp`, which clears. All three drivers were re-run from
their new location against `main` at `bb3f425e` before commit, so the evidence
describes the merged bytes: 58/58, 65/65, 53/53.

Preserving it required removing its launcher. The harness as run started Chrome
from a hard-coded macOS path, which no shared repository should carry, and which
the repository's own Bash-confinement guard independently refused: a `subprocess`
executable it cannot statically resolve reports as `<dynamic executable>` and
blocks release readiness. Satisfying the guard with a literal would have
reintroduced the portability defect, so `cdp.py` now connects to a browser the
operator starts, over `CDP_ENDPOINT`. It carries no `subprocess` call, no platform
assumption, and no absolute path. Per-stage isolation is preserved by giving each
`Chrome()` its own browser context.

### Corrected

The unchecked task boxes on slices 2 and 3 were recorded as ledger hygiene. Measured
at the merge commits they are a gate finding. `count_tasks` anchors on
`^\s*-\s+\[[ xX]\]\s+T[0-9]` (`read_only.py:4143`), so slice 3's decorated
`**T001**` form counted zero of 36; G7 consumes that at `:935` and gates on
`remaining == 0 and total > 0`, producing a reason that names the wrong problem.
Separately, neither slice records a G7 result while both declare the gate. Slice 2's
tasks were readable, so G7 would have failed loudly had it run. Both halves are now
ART-018's, which gains a fourth matcher row and a verification requirement that the
check is proven to *run*.

### Withdrawn

The offline console line is not an open question. The roadmap carries a dated
2026-07-28 Key Decision rejecting embedded woff2 at ~300KB per artifact. ART-003
rediscovered a settled decision and correctly rewrote its runbook step to match.

### Opened

**ART-020 — Keyboard-Reachable Scroll Containers In The Shipped Gallery.** Five
`overflow-x: auto` containers carry no `tabindex`, so a keyboard-only Safari reader
cannot reach their clipped content: `code-approaches.html:700`,
`implementation-plan.html:721` and `:942`, `module-map.html:587` and `:769`.
ART-003's own two templates already ship the fix. The gap was recorded during
ART-003 slice 2 and no entry owned it.

### Still owed

ART-002's fifteen unexecuted acceptance steps, across four shipped templates. The
preserved harness covers two of the four kinds; reduced motion needs a CDP method
`cdp.py` does not implement, and focus-indicator perceptibility is a human
judgement. No driver exists for those templates. Belongs in ART-009's scoping.

---

## 2026-08-18 — ART-007 Draft-PR Emission archived

ART-007 shipped as a single unstacked pull request, merged and archived on
2026-08-18 UTC.

| PR | Title | Merged at | Merge commit |
|---|---|---|---|
| [#445](https://github.com/racecraft-lab/racecraft-plugins-public/pull/445) | `feat(speckit-autopilot): Open a draft pull request when the plan stage ends` | `2026-08-18T21:06:52Z` | `1d58e5cbb47ce8c79b92e1cd793d6fdb2b29d8c9` |

CI: 19 pass, 1 skipped, 0 failures. Merged by `fgabelmannjr`, base `main`,
99 files, +14625 −576. Copilot reviewed and reported no blocking issues with
zero inline comments. The repository suite moved from 7399 to 7525.

### What shipped

The autopilot plan stage can now end at an open draft pull request whose body
indexes the generated artifact pages, instead of ending privately. Four parts: a
third packet mode `draft` with a conditional schema branch and mode-aware
producer; a `Draft PR` workflow-file row with its own grammar and reader; stage
resolution corroboration over a closed six-status vocabulary computed from one
read-only `gh` observation; and an `artifact-author` agent on both platforms.

### What the run taught

Four design defects were caught by executing the contract rather than reading it.
The draft relaxation was first written as an added `allOf` branch, which cannot
relax anything because `allOf` is conjunctive, and had to be inverted into an
`else` arm.

The highest-value find was an unnamed authority. The draft contract cited a
"release-readiness title check" without naming the operation. The obvious
candidate, `validate-pr-workflow-contract`, would have made draft emission
structurally impossible on `prsg-`, `spec-`, `doc-` and `xplat-` specs, because
`spec_scope_from_changed_path` upper-cases those slugs while the contract demands
a lowercase scope. ART-007's own `art-` slug matches none of them, so the wrong
choice would have shipped green and broken four other namespaces.

### Opened

Two spec-index defects, both routed to **HRNS-015** as scope bullets 7 and 8
rather than fixed here. `generate-spec-index` walks the filesystem rather than
the git index, so git-ignored artifacts become committed backlinks; and no gate
runs the check against the real repository tree, because the Layer 1 test uses a
fixture root. ART-007's own `SPEC-MOC.md` sat with three empty generated zones
through a full green run and was caught only by hand.

### Still owed

T052 never ran: quickstart scenarios 5 through 7 need an installed plugin
carrying this feature, which exists only after a release cuts from this merge.
The emission path has therefore never run end to end. Everything at the decision
layer is confirmed from its own input, but no draft pull request has been opened
by this code.
