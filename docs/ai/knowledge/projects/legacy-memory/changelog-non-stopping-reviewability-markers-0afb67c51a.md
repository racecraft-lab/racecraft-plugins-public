---
type: "speckit-legacy-memory-record"
title: "Non-stopping reviewability markers"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-0afb67c51abfe3e1"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Non-stopping reviewability markers

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
