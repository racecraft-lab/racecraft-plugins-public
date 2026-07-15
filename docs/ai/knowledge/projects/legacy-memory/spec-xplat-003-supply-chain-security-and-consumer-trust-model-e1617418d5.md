---
type: "speckit-legacy-memory-record"
title: "XPLAT-003 Supply-Chain Security and Consumer Trust Model"
description: "Atomic legacy memory record migrated from spec."
resource: ".specify/memory/spec.md"
tags: ["legacy-memory","spec"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-e1617418d56bf289"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/spec.md|6cf150d1147d326b209ae521a49b153b8679c9a4fe9eba55d406391f0aac564d"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-003 Supply-Chain Security and Consumer Trust Model

[Source: specs/xplat-003-supply-chain-security-and-consumer-trust-model]

### Summary

XPLAT-003 recorded the first-release supply-chain security and consumer-trust
model for the cross-platform runtime lane. It amended the active runtime
direction to a Python 3.11+ standard-library runner aligned with official Spec
Kit / `specify` prerequisites and rejected Go, Rust, Zig, native binaries, Bash,
Git Bash, WSL, PowerShell helper scripts, `jq`, Node, `pip install`, virtualenv
restore, and package restore as required installed-plugin runtime substrates.

The spec is decision/control only. It does not implement the runner, port helper
behavior, rebuild payloads, edit release automation, or make public native
platform claims. XPLAT-004 owns runner source/preflight/integrity controls;
XPLAT-007 owns Claude/Codex cutover, installed plugin UAT, update/autoheal proof,
latest tagged release verification, and public claim readiness.

### User Stories

- **US1 - Maintainer reviews trust baseline**: A maintainer can see which
  first-release controls block public runtime cutover and which hardening items
  stay deferred.
- **US2 - Implementer maps controls to owner specs**: An implementer can tell
  which controls belong in XPLAT-004, XPLAT-007, release automation, or public
  documentation.
- **US3 - Consumer understands local verification and limits**: A consumer can
  understand what an installed plugin can verify locally and which guarantees
  the project intentionally does not claim.

### Functional Requirements (highlights)

- Use Python 3.11+ stdlib as the only planned installed-plugin runtime
  substrate, through the official Spec Kit / `specify` prerequisite boundary.
- Require runner identity/preflight output, plugin-root detection, prerequisite
  checks, artifact-integrity pointers, and SHA-256 manifest/checksum evidence.
- Require source-to-dist drift checks, generated payload completeness evidence,
  install-completeness checks for Claude Code and Codex, and latest tagged
  release verification before public claims.
- Require doctor/autoheal behavior for scaffold/status/autopilot so stale or
  incomplete installs are detected and only safe gaps are auto-repaired.
- Require complete native Windows/macOS/Linux UAT evidence with readable
  runbooks before universal install/full-use claims.
- Treat signatures, SBOMs, provenance attestations, reproducible builds, formal
  audit, and cryptographic trust-chain verification as deferred hardening unless
  later promotion evidence exists.

### Success Criteria

XPLAT-003 is successful when XPLAT-004 can build the Python stdlib runner and
first-release controls without reopening the runtime/package decision, XPLAT-007
knows which installation and public-claim evidence is required, and consumers
receive accurate local verification guidance without overclaimed guarantees.

### Cleanup Note

Archived into project memory on 2026-06-29 (PR #267,
`1ab96b38da7e400b3c8e78b21d92e7b05302cfdd`). The active
`specs/xplat-003-supply-chain-security-and-consumer-trust-model/` folder was
removed from `specs/**` in the post-merge cleanup. Recovery commands and
provenance are recorded in
`.specify/memory/archive-reports/2026-06-29-xplat-003-post-merge-hygiene.md`.
