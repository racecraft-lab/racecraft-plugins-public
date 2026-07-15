---
type: "speckit-legacy-memory-record"
title: "TACD-002 Capability Discovery Directive and Agent Updates"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-f6c0021ffc6502e4"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# TACD-002 Capability Discovery Directive and Agent Updates

[Source: .specify/memory/archive-reports/2026-06-18-tacd-002-post-merge-hygiene.md]
**Branch**: `codex/tacd-002-post-merge-hygiene` · **Status**: Completed · **Archived**: 2026-06-18

### Scope

TACD-002 completed the active agent-behavior tier for the tool-agnostic
capability discovery roadmap. It owns the shared capability-discovery directive,
Claude and Codex runtime guidance updates, source-derived generated payloads,
and marker-emission hardening required to finish the sliced PR stack.

### Architecture / Approach

- Keep one shared source directive at
  `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`.
- Point Claude agent bodies to the directive and use approved compact
  equivalents in installed Codex TOML agents where direct pointers are not
  stable.
- Preserve exact named IDs only in schema metadata, historical/provenance text,
  or generated runtime evidence.
- Regenerate Claude and Codex payload roots from source through
  `bash scripts/build-plugin-payloads.sh`; do not treat `dist/**` as durable
  source.
- Separate marker-emission source feature directory from emitted branch prefix
  so existing parent branch refs no longer block ordered slice PR creation.
- Leave TACD-003 prerequisite/user-facing messaging and TACD-004 deterministic
  enforcement as separate roadmap specs.

### Test Strategy

- Confirm PRs #221-#226 merged to `main`.
- Validate JSON state after replacing active TACD-002 autopilot state.
- Regenerate and check SpecKit generated indexes after active spec removal.
- Verify active `specs/**` contains only expected active specs after cleanup.
- Run `git diff --check` and the deterministic SpecKit test suite.

### Cleanup Notes

`specs/tacd-002-capability-discovery-directive-and-agent-updates` was removed
from active `specs/**` cleanup after the shared directive, runtime guidance,
generated payloads, marker-emission hardening, and tests landed through PRs
#221-#226. Recovery commands and provenance are recorded in the TACD-002
archive report.
