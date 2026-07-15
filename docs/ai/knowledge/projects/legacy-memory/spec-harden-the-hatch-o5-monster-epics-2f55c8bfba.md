---
type: "speckit-legacy-memory-record"
title: "Harden the hatch + O5 monster-epics"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-2f55c8bfba9406a3"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Harden the hatch + O5 monster-epics

[Source: specs/prsg-010-harden-the-hatch]
**Branch**: `prsg-010-harden-the-hatch` · **Status**: Completed · **Archived**: 2026-06-11

### Summary

PRSG-010 closes the remaining reviewability hatch after the small-PR path exists.
It adds a final pre-PR backstop with re-slicing guidance, preserves typed
exceptions only when provenance is operator-owned and review-visible, adds an O5
monster-epic parent/child model using flat sibling specs, and promotes contextual
router signals only from deterministic high-confidence evidence.

### User Stories

- **US1 - Stop unreviewable PRs before creation.** Final gate blocks stop before
  PR body generation, `gh pr create`, or multi-PR emission, and write a
  re-slicing packet with PRSG-007/008/009 recovery steps.
- **US2 - Model genuine monster epics without nested specs.** O5 parent
  manifests coordinate flat sibling child specs, dependency order, shared links,
  and read-only status rollup without introducing nested `specs/<parent>/<child>`
  scanning.
- **US3 - Route from strong contextual evidence only.** Flag-system,
  release-cadence, and consumer-locality probes affect routing only when the
  evidence is deterministic and high confidence; weak evidence remains advisory.

### Functional Requirements

- Autopilot runs the final reviewability diff gate after implementation
  verification and before PR body generation, PR creation, or multi-PR emission.
- Blocking final gate results without honored exceptions stop the run and record
  `final_reviewability_gate` state plus a machine-readable re-slicing packet.
- Typed exceptions remain valid only as exact branch-added Markdown pragmas in
  committed, review-visible, non-generated CONTRACT artifacts.
- Generated roadmap, workflow, template, and PR-description content cannot emit
  live copy-pasteable exception override lines.
- O5 parent manifests are review-visible CONTRACT data, children remain flat
  siblings under `specs/`, topology validates before rollup, and status emits one
  row per declared child.
- Atomicity routing promotes only high-confidence contextual evidence into
  closed `signals[]`; weak, stale, fixture-only, code-fence-only, or conflicting
  evidence remains route-neutral in closed `hints[]`.

### Success Criteria

- Final gate block scenarios without a valid typed exception create no pull
  request and record a re-slicing packet.
- Valid typed exception scenarios expose class and provenance in run state and
  review evidence.
- Generated education surfaces contain zero standalone valid exception pragma
  lines.
- O5 rollup output is stable and reserves O5 for cases ordinary O4 routing and
  layer planning cannot slice thin enough.
- Contextual probe fixtures prove weak evidence does not change decisive routes,
  while high-confidence evidence uses documented signal vocabulary.

### Cleanup Note

The active spec folder was removed from `specs/**` cleanup on 2026-06-11 after
PRs #149-#155 merged and the PRSG-010 production contracts were preserved under
`speckit-pro/skills/speckit-autopilot/contracts/`.
Recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-11-prsg-010-post-merge-hygiene.md`.

---
