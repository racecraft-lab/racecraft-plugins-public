---
type: "speckit-legacy-memory-record"
title: "Optional gh-stack stack manager integration"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-cdd04c57056f29db"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# Optional gh-stack stack manager integration

[Source: specs/prsg-014-optional-gh-stack-stack-manager-integration]
**Branch**: `prsg-014-optional-gh-stack-stack-manager-integration` · **Status**: Completed · **Archived**: 2026-06-14

### Summary

PRSG-014 completed optional stack-manager hardening for autopilot split-PR
emission and restack flows. It added shared deterministic `gh stack` support
detection, a versioned `stack-manager-decision` contract, evidence threading
through `multi-pr-emission.sh` and `restack.sh`, pre-mutation explicit-`gh`
fallback, blocked recovery after partial or unknown `gh-stack` mutation, and
Claude/Codex operator-guidance parity.

The canonical path remains explicit GitHub `--base`/`--head` PR topology.
`gh-stack` is opportunistic and only selected after command availability,
version/support, read-only proof, and topology compatibility checks pass.

### Cleanup Note

The active spec folder was removed after PR #181 merged. Shipped behavior lives
in the shared autopilot scripts/contracts and committed Layer 4, Layer 7, and
Layer 8 fixtures; recovery commands are recorded in
`.specify/memory/archive-reports/2026-06-14-prsg-014-post-merge-hygiene.md`.

---
