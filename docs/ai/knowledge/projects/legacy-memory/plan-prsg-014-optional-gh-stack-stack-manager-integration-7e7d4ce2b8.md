---
type: "speckit-legacy-memory-record"
title: "PRSG-014 Optional gh-stack stack manager integration"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-7e7d4ce2b8068036"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# PRSG-014 Optional gh-stack stack manager integration

[Source: .specify/memory/archive-reports/2026-06-14-prsg-014-post-merge-hygiene.md]
**Branch**: `codex/post-merge-archive-hygiene` · **Status**: Completed · **Archived**: 2026-06-14

### Scope

PRSG-014 added optional stack-manager support for autopilot create/sync/restack
flows while preserving explicit `gh pr create/edit --base --head` as the
deterministic fallback path.

### Architecture / Approach

- Add one shared `detect-stack-manager.sh` script used by both emission and
  restack flows.
- Persist stack-manager decisions through `stack-manager-decision.schema.json`
  and evidence paths under feature/workflow `.process` directories.
- Select `gh-stack` only after command availability, version/support, read-only
  proof, and topology compatibility checks pass.
- Fall back to explicit `gh` before mutation for missing, unsupported,
  ambiguous, unsafe, or topology-incompatible environments.
- Block with recoverable state after partial or unknown `gh-stack` mutation
  instead of switching managers and risking duplicate or divergent PR topology.
- Keep Codex and Claude guidance in parity while sharing scripts and contracts.

### Test Strategy

- Focused Layer 4 tests: `test-detect-stack-manager` 18/18,
  `test-multi-pr-emission` 159/159, `test-restack` 33/33.
- Broader recorded verification: Layer 1 979/979, Layer 4 1768/1768, Layer 7
  fixtures, Layer 8 parity 12/12, and default suite 2937/2937 before PR #181.
- Post-cleanup validation regenerates Spec-MOC indexes and reruns the default
  deterministic suite.

### Cleanup Notes

`specs/prsg-014-optional-gh-stack-stack-manager-integration` was removed from
active `specs/**` cleanup after PR #181 merged. Recovery commands and provenance
are recorded in the PRSG-014 archive report.

---
