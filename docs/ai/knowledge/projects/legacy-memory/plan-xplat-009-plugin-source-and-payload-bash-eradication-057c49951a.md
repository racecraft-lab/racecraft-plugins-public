---
type: "speckit-legacy-memory-record"
title: "XPLAT-009 Plugin Source and Payload Bash Eradication"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-057c49951ae97661"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-009 Plugin Source and Payload Bash Eradication

[Source: specs/xplat-009-plugin-source-and-payload-bash-eradication]

XPLAT-009 implemented the plugin-source Bash eradication lane on top of the
XPLAT-004 runner, XPLAT-005/XPLAT-006 helper registries, XPLAT-007 gate
substrate, and XPLAT-008 installed-runtime cutover, using two vertical slices:
active plugin-source Bash removal first, then payload rebuild, installed-cache
proof, and zero-Bash guards.

### Technical Approach

- Port active plugin-source script behavior (autopilot, coach, and install
  skill scripts plus `speckit-pro/scripts/`) to Python runner/helper/gate
  operations and delete the remaining live `.sh` files under `speckit-pro/`.
- Replace active source and generated agent instructions that called Bash
  helpers with Python runner operations or no-shell guidance, keeping
  historical/archive references as prose behind a documented allowlist.
- Rebuild generated Claude and Codex payloads from the updated source surfaces
  and compare them against source-derived inventories.
- Prove source, generated payloads, and a bounded installed-cache artifact pass
  one Python-backed zero-Bash guard, with committed evidence under
  `docs/ai/specs/.process/XPLAT-009-*`.
- Preserve XPLAT-009 contract schemas under
  `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/contracts/` so
  Layer 4 gates no longer depend on active `specs/**` content.

### Testing Strategy

XPLAT-009 verification uses focused Python standard-library Layer 4
runner/helper/gate tests, Layer 1 structural validation, payload-completeness
apply/read-only evidence, installed-cache proof, the active-instruction
no-shell/no-`jq` guard, seeded zero-Bash regression cases, release-readiness
fixture coverage, spec-index checks, JSON validation, diff hygiene, and the
default deterministic suite.

### Cleanup Notes

`specs/xplat-009-plugin-source-and-payload-bash-eradication` was removed from
active `specs/**` in the post-merge cleanup after PR #297 merged and shipped in
speckit-pro 2.18.0. Recovery commands and provenance are recorded in the
XPLAT-009 archive report. Repository-wide Bash confinement and the CI dispatch
guard were completed by XPLAT-010, and public native Windows/macOS/Linux
release claims remain blocked until the preserved XPLAT-008 UAT matrix has six
passing operator rows.
