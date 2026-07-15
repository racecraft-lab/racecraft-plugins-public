---
type: "speckit-legacy-memory-record"
title: "Vertical-slice sizing heuristics in PRD/grill-me"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-d1866a9b22fd1ef2"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Vertical-slice sizing heuristics in PRD/grill-me

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
