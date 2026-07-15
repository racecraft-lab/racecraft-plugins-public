---
type: "speckit-legacy-memory-record"
title: "XPLAT-008 Claude/Codex Cutover and Universal Install Release Gate"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-2c28e13c8c4cd906"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-008 Claude/Codex Cutover and Universal Install Release Gate

[Source: specs/xplat-008-claude-codex-cutover-universal-install-release-gate]

XPLAT-008 shipped the installed Claude/Codex cutover and release-readiness
packet on top of the Python runner, helper, and gate substrates from
XPLAT-004 through XPLAT-007. It moved active installed-runtime surfaces to
direct Python runner invocation, rebuilt generated Claude and Codex payloads,
aligned public install/trust/update guidance with implemented controls, added
UAT matrix and release-readiness gates, and implemented bounded install-health
repair behavior.

The feature is archived as an implementation and blocked release-readiness
packet. It does not authorize public native Windows/macOS/Linux support claims
until all six operator UAT rows pass in
`docs/ai/specs/.process/XPLAT-008-uat-matrix.md`.

### Requirements Preserved

- Active Claude/Codex skills, agents, hooks, install guidance, generated
  payloads, and release gates avoid Bash, Git Bash, WSL, PowerShell-specific
  command language, `jq`, shell interpolation, and Unix-only runtime
  assumptions.
- Generated Claude and Codex payloads are source-built and checked for version
  metadata, bundled agents, hooks, runner files, manifest/checksum records, and
  public trust evidence.
- Release readiness fails on active shell-runtime dependencies, incomplete
  payloads, missing bundled agents, stale metadata, unsafe public claims,
  incomplete UAT/update/repair evidence, unsafe repair behavior, path leakage,
  and nondeterministic generated payload output.
- Safe repair is limited to trusted missing or stale installed-cache artifacts
  with expected paths, source identity, release channel or tag, and
  checksum-backed evidence.
- Native platform release claims require passing Claude and Codex UAT rows for
  Windows, macOS, and Linux.

### Success Criteria

XPLAT-008 is successful as a merged implementation because PRs #289 through
#292 shipped active installed-runtime cutover, payload rebuilds, public docs
claim alignment, UAT/release-readiness fixtures, install-health repair
controls, generated payload sync, and focused Layer 4 coverage. The public
release claim remains intentionally blocked until the preserved native UAT
matrix is filled with real passing operator evidence.

### Cleanup Note

Archived into project memory on 2026-07-07 after PR #292 merged at
`9507fd452a3e344c1912b449f3bb4f2c38437b38`. The active
`specs/xplat-008-claude-codex-cutover-universal-install-release-gate/` folder
was removed from `specs/**` in post-merge cleanup after preserving contract
schemas under `tests/speckit-pro/unit/fixtures/installed-plugin-release/contracts/`
and release/UAT evidence under `docs/ai/specs/.process/`. Recovery commands and
provenance are recorded in
`.specify/memory/archive-reports/2026-07-07-xplat-008-post-merge-hygiene.md`.
