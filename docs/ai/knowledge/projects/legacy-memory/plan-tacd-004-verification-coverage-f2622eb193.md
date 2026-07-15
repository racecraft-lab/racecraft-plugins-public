---
type: "speckit-legacy-memory-record"
title: "TACD-004 Verification Coverage"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-f2622eb193f7584b"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# TACD-004 Verification Coverage

### Scope

Add deterministic verification (Layer 5 named-tool guard + Layer 1
pointer-coverage/target-resolution) and rewritten functional evals that lock the
vendor-neutral optional-tool contract, and fix the `strip_codex_guard` payload
defect with a body-completeness guard. Extend Layers 1/4/5 in place; no new test
layer, no agent-behavior or docs-wording changes.

### Architecture / Approach

- Named-tool guard lives in Layer 5; pointer-coverage and target-resolution in
  Layer 1; behavior expectations in the four eval files.
- The pointer rule is a literal path match to `capability-discovery.md` plus a
  small enumerated approved-equivalent allowlist (empty by design).
- The payload-completeness guard anchors on a structural invariant (last
  non-guard source heading present) rather than an absolute line count.
- `strip_codex_guard` strips from `## Codex Skill-Selection Guard` to the next
  heading or EOF; `dist/` is rebuilt from source.

### Test Strategy

- Confirm PR #240 merged to `main`.
- Validate JSON state after replacing the active autopilot state.
- Regenerate and check SpecKit generated indexes after active spec removal.
- Verify active `specs/**` contains only `specs/.gitkeep` after cleanup.
- Run `git diff --check` and `bash tests/speckit-pro/run-all.sh`.

### Cleanup Notes

`specs/tacd-004-verification-coverage` was removed from active `specs/**`
cleanup after the verification guards, the `strip_codex_guard` fix, rebuilt
payloads, and rewritten evals landed through PR #240. Recovery commands and
provenance are recorded in the TACD-004 archive report.
