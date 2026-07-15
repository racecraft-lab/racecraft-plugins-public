---
type: "speckit-legacy-memory-record"
title: "Atomicity-test router (read-only classifier)"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-629526af34a09379"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Atomicity-test router (read-only classifier)

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
