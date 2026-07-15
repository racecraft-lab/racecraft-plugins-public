---
type: "speckit-legacy-memory-record"
title: "XPLAT-009 Plugin Source and Payload Bash Eradication"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-4f71dc67b44d2762"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-009 Plugin Source and Payload Bash Eradication

[Source: specs/xplat-009-plugin-source-and-payload-bash-eradication]

XPLAT-009 removed the remaining plugin-source Bash substrate on top of the
XPLAT-008 installed Claude/Codex cutover. It ported active plugin-source script
behavior to Python runner/helper/gate operations, deleted the remaining live
`.sh` files under `speckit-pro/`, replaced active Bash-oriented guidance in
skills and agents, rebuilt generated Claude and Codex payloads from source, and
added a Python-backed zero-Bash guard that proves source, generated payloads,
and a bounded installed-cache artifact are Bash-free with a reviewable
historical allowlist.

Repository-wide Bash confinement outside the plugin package (top-level
`tests/**`, top-level `scripts/**`, hooks outside the plugin, `.specify/**`,
and CI dispatch glue policy) was completed by XPLAT-010.

### Requirements Preserved

- The live `speckit-pro/` plugin source contains zero live `.sh` files and no
  Python wrapper around a live shell script.
- Active skill, agent, command, helper, gate, and release guidance surfaces
  contain no unallowlisted instruction to rely on Bash, `.sh`, `jq`, shell
  interpolation, Git Bash, WSL, PowerShell-specific command language, or
  Unix-only assumptions.
- Rebuilt Claude and Codex payloads report zero `.sh` files and zero
  unallowlisted active Bash or `jq` guidance hits.
- Bounded installed-cache proof reports zero `.sh` files, zero Bash fallback
  guidance hits, and zero `jq` requirement hits; mutable real user cache state
  is supplemental only and cannot satisfy release readiness.
- Guard coverage fails seeded regression cases for reintroduced `.sh` files,
  active Bash guidance, active `jq` requirements, and active Unix-only
  assumptions in in-scope surfaces.
- Historical/archive allowlist entries record path, reason, scope, and
  release-readiness exclusion; no allowlist entry is usable as
  release-readiness proof.

### Success Criteria

XPLAT-009 is successful as a merged implementation because PR #297 shipped the
plugin-source Bash removal, payload rebuilds, zero-Bash guard, installed-cache
proof, historical allowlist, and regression guard coverage, released in
speckit-pro 2.18.0, with PR #299 following up on Windows interpreter and home
directory resolution. SC-001 through SC-007 evidence is preserved under
`docs/ai/specs/.process/XPLAT-009-*` result files.

### Cleanup Note

Archived into project memory on 2026-07-08 after PR #297 merged at
`7bc6be1a9faaa3113f8db903188ddb49a445e7ce`. The active
`specs/xplat-009-plugin-source-and-payload-bash-eradication/` folder was
removed from `specs/**` in post-merge cleanup after preserving contract schemas
under `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/contracts/`;
zero-Bash guard, payload-completeness, installed-cache proof, and
release-readiness evidence was already preserved under
`docs/ai/specs/.process/`. Recovery commands and provenance are recorded in
`.specify/memory/archive-reports/2026-07-08-xplat-009-post-merge-hygiene.md`.
