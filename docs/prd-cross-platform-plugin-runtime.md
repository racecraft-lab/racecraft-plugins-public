# PRD: Cross-Platform Plugin Runtime for SpecKit Pro

**Status**: Draft
**Created**: 2026-06-24
**Last updated**: 2026-06-24
**Owner**: Racecraft Lab
**Spec ID prefix**: `XPLAT-###`
**Technical roadmap**: [docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md](ai/specs/cross-platform-plugin-runtime-technical-roadmap.md)

---

## Problem Statement

SpecKit Pro is not ready for broad public release while its installed Claude Code
and Codex plugin workflows require Bash. A developer who installs the plugin on
native Windows today can install the plugin metadata, but core workflows break
when they reach Bash-backed helper execution. The current runtime surfaces invoke
`bash`, depend on `jq`, and include helpers that assume Unix paths or macOS/Linux
Bash availability.

This PRD defines the product requirement to replace Bash as a plugin runtime
dependency with one cross-platform implementation path that behaves the same on
native Windows, macOS, and Linux.

## Goals

- A public user can install SpecKit Pro on Claude Code or Codex and run the
  documented plugin workflows on native Windows, macOS, and Linux.
- Installed plugin workflows no longer require Bash, Git Bash, WSL, PowerShell,
  or `jq` as the implementation substrate.
- Claude and Codex plugin behavior stays semantically equivalent during and
  after the migration.
- The migration is reviewable: each implementation spec is small enough to test,
  compare, and roll back independently.

## Non-Goals

- Replacing repository maintainer shell scripts that are not shipped or invoked
  by the installed Claude/Codex plugin runtime.
- Replacing GitHub Actions or CI shell usage.
- Replacing GitHub Spec Kit's own generated `.specify/scripts/bash/` helpers in
  consumer repositories.
- Changing the user-facing SpecKit workflow model, PR-size governance behavior,
  or capability-discovery contract except where Bash removal requires invocation
  wording changes.

## Features

### 1. Runtime Inventory and Decision *(-> XPLAT-001)*

Inventory every active Bash, `jq`, `.sh`, shell-quoting, and Unix-path assumption
that can affect installed Claude or Codex plugin behavior. Choose one canonical
cross-platform runtime strategy and define the invocation, JSON I/O, error, path,
and subprocess contracts.

**Acceptance Criteria**

- AC-1.1: The inventory covers Claude skills, Codex skills, Claude agents, Codex
  agents, hooks, install helpers, generated payloads, and public plugin docs.
- AC-1.2: The selected runtime strategy explicitly supports native Windows,
  macOS, and Linux without requiring Bash, Git Bash, WSL, PowerShell, or `jq`.
- AC-1.3: The runtime contract defines stable command names, argument parsing,
  JSON output envelopes, stderr/error behavior, path normalization, and subprocess
  execution rules.
- AC-1.4: Historical/archive/test-only Bash references are classified separately
  from active runtime references so enforcement can avoid false positives.

### 2. Cross-Platform Runner Foundation *(-> XPLAT-002)*

Build the shared runner, support library, and parity harness that later specs use
to port behavior without changing plugin semantics.

**Acceptance Criteria**

- AC-2.1: The new runner can execute a named helper from Claude and Codex plugin
  skills using the same documented command shape.
- AC-2.2: The runner performs shell-free filesystem, path, JSON, and subprocess
  operations using the selected runtime's structured APIs.
- AC-2.3: The runner includes a preflight command that reports platform, runtime,
  executable availability, and missing prerequisites in a JSON envelope.
- AC-2.4: A parity harness can compare old Bash helper output with new runner
  output for fixtures while Bash still exists.

### 3. Read-Only Helper Port *(-> XPLAT-003)*

Port the read-only and advisory helpers first: prerequisite checks, command and
preset detection, gates, counters, reviewability estimation, layer planning,
atomicity routing, topology checks, and spec-index generation.

**Acceptance Criteria**

- AC-3.1: Every read-only helper used by autopilot, scaffold/status, agents, or
  docs-generation has a cross-platform implementation.
- AC-3.2: Fixture parity proves equivalent JSON output and exit semantics against
  current Bash behavior before cutover.
- AC-3.3: The new helpers do not shell out for path traversal, JSON construction,
  text parsing, or glob expansion.
- AC-3.4: The existing Claude and Codex guidance can still use the Bash path until
  XPLAT-005 performs the final cutover.

### 4. Mutation, Install, and PR-Emission Helper Port *(-> XPLAT-004)*

Port the helpers that write files, emit PR packets, install Codex agents, manage
curated sets, migrate/relocate process artifacts, restack, or create split-PR
state. These are higher-risk because they mutate repository or user-local state.

**Acceptance Criteria**

- AC-4.1: Every mutation-capable plugin helper has a cross-platform equivalent
  with explicit dry-run and apply behavior where the Bash helper has it.
- AC-4.2: File writes are atomic where the current Bash helper promises atomicity
  or safe-write behavior.
- AC-4.3: PR packet, workflow-contract, multi-PR, restack, install, and relocation
  outputs preserve their current JSON schemas and human-readable diagnostics.
- AC-4.4: The parity harness covers success, invalid-input, missing-prerequisite,
  and partial-failure cases before any active skill points at the new helper.

### 5. Claude/Codex Cutover and Native Windows Release Gate *(-> XPLAT-005)*

Switch active Claude and Codex plugin surfaces from Bash helpers to the
cross-platform runner, remove Bash/`jq` from plugin-runtime prerequisites, rebuild
payloads, and add release gates that block reintroducing active Bash runtime
dependencies.

**Acceptance Criteria**

- AC-5.1: Active Claude and Codex skills, agents, hooks, install guidance, and
  generated payloads invoke the cross-platform runner, not Bash scripts.
- AC-5.2: Public plugin docs state the new runtime prerequisites and no longer
  describe Bash, Git Bash, WSL, PowerShell, or `jq` as required for installed
  plugin workflows.
- AC-5.3: Deterministic checks fail if an active installed-runtime surface
  reintroduces `bash`, `.sh`, `jq`, shell interpolation, or Unix-only path
  assumptions outside explicitly allowlisted historical/test references.
- AC-5.4: Manual UAT evidence covers native Windows, macOS, and Linux for both
  Claude and Codex plugin flows.
- AC-5.5: Public release is blocked until the native Windows UAT path passes
  without WSL, Git Bash, or PowerShell-specific workarounds.

## Success Metrics

- Zero active Claude/Codex plugin runtime invocations require Bash or `jq`.
- All ported helpers pass fixture parity before cutover and native platform tests
  after cutover.
- A native Windows developer can complete install, `$install`/agent setup,
  scaffold/status, and an autopilot dry-run path without a Unix shell.
- The release-readiness checklist has a hard gate for native Windows plugin UAT.

## Open Questions

- Which implementation runtime is the best public-release contract: bundled
  JavaScript/TypeScript, Python, or small per-platform binaries?
- Can Claude Code and Codex both reliably invoke the selected runtime from
  installed plugin caches without extra user setup?
- Which repository-only scripts should remain Bash after plugin-runtime cutover,
  and how should they be classified so enforcement stays precise?

## SPEC Catalog Crosswalk

| Feature | Acceptance Criteria | SPEC | Depends On | Priority |
|---|---|---|---|---|
| Runtime inventory and decision | AC-1.* | XPLAT-001 | None | P1 |
| Runner foundation | AC-2.* | XPLAT-002 | XPLAT-001 | P1 |
| Read-only helper port | AC-3.* | XPLAT-003 | XPLAT-002 | P1 |
| Mutation/install/PR-emission helper port | AC-4.* | XPLAT-004 | XPLAT-002, XPLAT-003 | P1 |
| Claude/Codex cutover and release gate | AC-5.* | XPLAT-005 | XPLAT-003, XPLAT-004 | P1 |
