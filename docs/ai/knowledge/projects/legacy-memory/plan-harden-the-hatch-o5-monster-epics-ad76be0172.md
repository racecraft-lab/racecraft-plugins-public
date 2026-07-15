---
type: "speckit-legacy-memory-record"
title: "Harden the hatch + O5 monster-epics"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-ad76be0172f08e5e"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Harden the hatch + O5 monster-epics

[Source: specs/prsg-010-harden-the-hatch]
**Branch**: `prsg-010-harden-the-hatch` · **Status**: Completed · **Archived**: 2026-06-11

### Dependencies & Versions

- Bash + `jq`, `git`, and GitHub CLI (`gh`) at PR-emission boundaries; no package
  manager or compiled build step.
- Reuses PRSG-007 routing, PRSG-008 layer planning, PRSG-009 multi-PR emission,
  and SPEC-006a/b PR body/UAT evidence surfaces.
- Preserves Claude and Codex skill mirrors for autopilot, scaffold, and status
  guidance.

### Architecture / Approach

- `final-reviewability-backstop.sh`: wraps the final diff gate, blocks before PR
  body generation or PR creation when the gate blocks without an honored typed
  exception, and writes durable gate state plus a re-slicing packet.
- `atomicity-route.sh`: extends the routing decision with high-confidence
  contextual probes while preserving conservative fallback and closed enum
  signal/hint vocabularies.
- `o5-topology.sh`: validates O5 parent manifests, flat sibling child paths,
  dependency order, cycle rules, and computed read-only status rollup.
- Scaffold/status skill updates describe O5 as a fallback after ordinary O4
  split planning cannot produce reviewable slices.
- Template and roadmap guidance remove live generated exception boilerplate
  while still documenting accepted exception classes and provenance rules.

### Test Strategy

- `bash tests/speckit-pro/unit/test-final-reviewability-backstop.sh`
  passed `31/31`.
- `bash tests/speckit-pro/unit/test-atomicity-route.sh` passed
  `109/109`.
- `bash tests/speckit-pro/unit/test-o5-topology.sh` passed `25/25`.
- `bash tests/speckit-pro/unit/test-generate-spec-index.sh` passed
  `87/87`.
- `bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run --fixture 03-reviewability-backstop-parent-child-routing`
  passed `3/3`.
- Post-cleanup `bash tests/speckit-pro/run-all.sh` verification is recorded in
  `.specify/memory/archive-reports/2026-06-11-prsg-010-post-merge-hygiene.md`.

### Cleanup Notes

`specs/prsg-010-harden-the-hatch` was removed from active `specs/**` cleanup on
2026-06-11 after PRs #149-#155 merged and the PRSG-010 contract schemas were
preserved under `speckit-pro/skills/speckit-autopilot/contracts/`.

---
