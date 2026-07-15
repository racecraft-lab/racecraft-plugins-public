---
type: "speckit-legacy-memory-record"
title: "XPLAT-003 Supply-Chain Security and Consumer Trust Model"
description: "Atomic legacy memory record migrated from plan."
resource: ".specify/memory/plan.md"
tags: ["legacy-memory","plan"]
timestamp: "2026-07-14T12:00:00Z"
x-speckit-id: "legacy-memory-dbd6092089031d9b"
x-speckit-project: "legacy-memory"
x-speckit-authority: "reviewed"
x-speckit-status: "active"
x-speckit-confidence: "high"
x-speckit-sensitivity: "internal"
x-speckit-sources: [".specify/memory/plan.md|d5658cd2b1231d4ddfdeede36cb1bf9d43650292437b64960ae855cc29857c10"]
x-speckit-producer-skill: "knowledge-migration"
x-speckit-producer-agent: "speckit-pro-runner"
---
# XPLAT-003 Supply-Chain Security and Consumer Trust Model

[Source: specs/xplat-003-supply-chain-security-and-consumer-trust-model]

### Dependencies and Environment

- **Runtime decision**: Python 3.11+ standard-library runner, aligned with
  official Spec Kit / `specify` prerequisites.
- **Rejected installed-plugin runtime substrates**: Go, Rust, Zig, native
  binaries, Bash, Git Bash, WSL, PowerShell helper scripts, `jq`, Node,
  `pip install`, virtualenv restore, and package restore.
- **Storage**: checked-in repository files and generated Claude/Codex plugin
  payloads only; no database or runtime service state.
- **Target platforms**: native Windows, macOS, and Linux through installed
  Claude Code and Codex plugin caches.

### Architecture / Approach

XPLAT-003 is a decision/control spec. It defines what downstream implementation
must prove before the runtime lane can claim universal installed-plugin support.

- XPLAT-004 owns the Python runner source layout, plugin entrypoint, path/JSON
  envelope helpers, subprocess execution without a shell, platform detection,
  prerequisite checks for Python 3.11+ and `specify`, runner identity/preflight
  output, checksum/manifest files, and Python stdlib test/eval runner patterns.
- XPLAT-005 and XPLAT-006 own behavior ports once the runner foundation exists.
- XPLAT-007 owns Claude Code and Codex cutover, generated payload verification,
  latest tagged release checks, complete bundled-agent/install evidence, native
  platform UAT, update and autoheal proof, consumer-local verification docs, and
  public claim readiness.
- Release automation and public documentation may only claim controls that are
  implemented and verified; SBOMs, attestations, reproducible builds, signatures,
  formal audit, and cryptographic trust-chain verification remain deferred
  hardening unless later promoted.

### Testing Strategy

XPLAT-003 itself is docs/process-only. Verification for the cleanup is archive
state, generated roadmap-MOC index regeneration, JSON validation, active spec
inventory review, whitespace validation, and the focused structural SpecKit Pro
test layer. Downstream XPLAT specs must add Python stdlib unit/parity/eval gates
and native installed-cache UAT before public release claims.

### Constitution Check

PASS. XPLAT-003 did not change plugin runtime behavior, manifests, release
automation, generated payloads, or public docs. It created the policy and
control contract that later implementation specs must satisfy.

### Cleanup Notes

`specs/xplat-003-supply-chain-security-and-consumer-trust-model` was removed
from active `specs/**` in the post-merge cleanup after PR #267 merged. Recovery
commands and provenance are recorded in the XPLAT-003 archive report.
