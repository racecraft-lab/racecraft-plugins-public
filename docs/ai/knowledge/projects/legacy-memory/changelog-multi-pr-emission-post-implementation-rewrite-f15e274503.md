---
type: "speckit-legacy-memory-record"
title: "Multi-PR emission (post-implementation rewrite)"
description: "Atomic legacy memory record migrated from changelog."
resource: ".specify/memory/changelog.md"
tags: ["legacy-memory","changelog"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-f15e274503961a82"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/changelog.md|87f298677b2de7d51fbc33b22047848d70ba6be8bbce1822fd597e23cafc49c3"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Multi-PR emission (post-implementation rewrite)

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
