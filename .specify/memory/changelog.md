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
