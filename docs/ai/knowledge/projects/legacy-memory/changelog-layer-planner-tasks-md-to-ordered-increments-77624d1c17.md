---
type: "speckit-legacy-memory-record"
title: "Layer-planner: tasks.md to ordered increments"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-77624d1c175e9f24"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Layer-planner: tasks.md to ordered increments

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
