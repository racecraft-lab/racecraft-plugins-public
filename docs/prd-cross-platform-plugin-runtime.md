# PRD: Cross-Platform Plugin Runtime for SpecKit Pro

**Status**: Draft
**Created**: 2026-06-24
**Last updated**: 2026-06-25
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
native Windows, macOS, and Linux, and that users can adopt with reasonable
supply-chain confidence.

## Goals

- A public user can install SpecKit Pro on Claude Code or Codex and run the
  documented plugin workflows on native Windows, macOS, and Linux.
- Installed plugin workflows no longer require Bash, Git Bash, WSL, PowerShell,
  or `jq` as the implementation substrate.
- Claude and Codex plugin behavior stays semantically equivalent during and
  after the migration.
- The runtime choice is evidence-backed before implementation starts.
- Consumers can evaluate the plugin's runtime artifacts, dependencies, and
  release provenance before adopting it.
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
- Claiming cryptographic release guarantees until the supply-chain approach is
  selected and implemented.

## Features

### 1. Runtime Inventory and Constraints *(-> XPLAT-001)*

Inventory every active Bash, `jq`, `.sh`, shell-quoting, and Unix-path assumption
that can affect installed Claude or Codex plugin behavior. Classify each
reference and turn the inventory into concrete evaluation requirements for the
runtime decision.

**Acceptance Criteria**

- AC-1.1: The inventory covers Claude skills, Codex skills, Claude agents, Codex
  agents, hooks, install helpers, generated payloads, and public plugin docs.
- AC-1.2: Historical/archive/test-only Bash references are classified separately
  from active runtime references so enforcement can avoid false positives.
- AC-1.3: Each active runtime dependency has an owner category: read-only helper,
  mutation/helper, cutover guidance, repository-only exclusion, or follow-up
  exception.
- AC-1.4: The inventory produces an evaluation rubric for runtime candidates,
  including native Windows/macOS/Linux support, invocation from installed plugin
  caches, dependency footprint, packaging, offline behavior, diagnostics, and
  maintainability.

### 2. Runtime Implementation Options and Contract Decision *(-> XPLAT-002)*

Research and evaluate implementation options before building the runner. The
decision must compare plausible strategies such as JavaScript/TypeScript,
Python, and small per-platform binaries, then select one canonical runtime
contract for later specs.

**Acceptance Criteria**

- AC-2.1: Candidate strategies are compared against the XPLAT-001 rubric,
  including native platform behavior, Claude/Codex invocation reliability,
  packaging/distribution model, dependency management, update path, performance,
  diagnostics, and maintainer ergonomics.
- AC-2.2: Where runtime mechanics are uncertain, smoke probes or documented
  platform evidence verify that Claude Code and Codex can invoke the candidate
  from installed plugin caches without extra user setup.
- AC-2.3: The decision record selects one runtime strategy, explains rejected
  options, and names any compatibility adapters that are allowed temporarily.
- AC-2.4: The selected contract defines stable command names, argument parsing,
  JSON input/output envelopes, stderr/error behavior, path normalization,
  subprocess execution rules, prerequisite reporting, and version reporting.

### 3. Supply-Chain Security and Consumer Trust Model *(-> XPLAT-003)*

Research and choose the supply-chain approach for the new runtime so consumers
can understand what they are installing and how releases are produced.

**Acceptance Criteria**

- AC-3.1: The selected approach defines dependency policy, lockfile/reproducible
  build expectations, generated payload integrity, vulnerability scanning, and
  release verification requirements appropriate to the chosen runtime.
- AC-3.2: The approach evaluates SBOMs, provenance/attestations, artifact
  checksums or signatures, dependency update cadence, and how much of that scope
  is required for the first public release.
- AC-3.3: The trust model documents what consumers can verify locally after
  installing the plugin and what maintainers verify in CI before release.
- AC-3.4: The roadmap records which security controls must land in the runner
  foundation, which belong to release automation, and which are deferred with a
  clear rationale.

### 4. Cross-Platform Runner Foundation *(-> XPLAT-004)*

Build the shared runner, support library, and parity harness that later specs use
to port behavior without changing plugin semantics.

**Acceptance Criteria**

- AC-4.1: The new runner can execute a named helper from Claude and Codex plugin
  skills using the same documented command shape.
- AC-4.2: The runner performs shell-free filesystem, path, JSON, and subprocess
  operations using the selected runtime's structured APIs.
- AC-4.3: The runner includes a preflight command that reports platform, runtime,
  executable availability, plugin root, missing prerequisites, and runtime
  version in a JSON envelope.
- AC-4.4: A parity harness can compare old Bash helper output with new runner
  output for fixtures while Bash still exists.
- AC-4.5: Foundation implementation includes the XPLAT-003 first-release
  security controls that apply to runtime source, dependencies, and generated
  runtime artifacts.

### 5. Read-Only Helper Port *(-> XPLAT-005)*

Port the read-only and advisory helpers first: prerequisite checks, command and
preset detection, gates, counters, reviewability estimation, layer planning,
atomicity routing, topology checks, and spec-index generation.

**Acceptance Criteria**

- AC-5.1: Every read-only helper used by autopilot, scaffold/status, agents, or
  docs-generation has a cross-platform implementation.
- AC-5.2: Fixture parity proves equivalent JSON output and exit semantics against
  current Bash behavior before cutover.
- AC-5.3: The new helpers do not shell out for path traversal, JSON construction,
  text parsing, or glob expansion.
- AC-5.4: The existing Claude and Codex guidance can still use the Bash path until
  XPLAT-007 performs the final cutover.

### 6. Mutation, Install, and PR-Emission Helper Port *(-> XPLAT-006)*

Port the helpers that write files, emit PR packets, install Codex agents, manage
curated sets, migrate/relocate process artifacts, restack, or create split-PR
state. These are higher-risk because they mutate repository or user-local state.

**Acceptance Criteria**

- AC-6.1: Every mutation-capable plugin helper has a cross-platform equivalent
  with explicit dry-run and apply behavior where the Bash helper has it.
- AC-6.2: File writes are atomic where the current Bash helper promises atomicity
  or safe-write behavior.
- AC-6.3: PR packet, workflow-contract, multi-PR, restack, install, and relocation
  outputs preserve their current JSON schemas and human-readable diagnostics.
- AC-6.4: The parity harness covers success, invalid-input, missing-prerequisite,
  dirty-worktree, and partial-failure cases before any active skill points at the
  new helper.

### 7. Claude/Codex Cutover and Native Windows Release Gate *(-> XPLAT-007)*

Switch active Claude and Codex plugin surfaces from Bash helpers to the
cross-platform runner, remove Bash/`jq` from plugin-runtime prerequisites, rebuild
payloads, and add release gates that block reintroducing active Bash runtime
dependencies.

**Acceptance Criteria**

- AC-7.1: Active Claude and Codex skills, agents, hooks, install guidance, and
  generated payloads invoke the cross-platform runner, not Bash scripts.
- AC-7.2: Public plugin docs state the new runtime prerequisites and no longer
  describe Bash, Git Bash, WSL, PowerShell, or `jq` as required for installed
  plugin workflows.
- AC-7.3: Deterministic checks fail if an active installed-runtime surface
  reintroduces `bash`, `.sh`, `jq`, shell interpolation, or Unix-only path
  assumptions outside explicitly allowlisted historical/test references.
- AC-7.4: Manual UAT evidence covers native Windows, macOS, and Linux for both
  Claude and Codex plugin flows.
- AC-7.5: Public release is blocked until the native Windows UAT path passes
  without WSL, Git Bash, or PowerShell-specific workarounds.
- AC-7.6: Public release notes and docs accurately describe the implemented
  supply-chain security model without overstating guarantees.

## Success Metrics

- Zero active Claude/Codex plugin runtime invocations require Bash or `jq`.
- All ported helpers pass fixture parity before cutover and native platform tests
  after cutover.
- A native Windows developer can complete install, `$install`/agent setup,
  scaffold/status, and an autopilot dry-run path without a Unix shell.
- The release-readiness checklist has a hard gate for native Windows plugin UAT.
- Public runtime artifacts have documented dependency, provenance, and local
  verification expectations.

## Open Questions

- Which implementation runtime is the best public-release contract: bundled
  JavaScript/TypeScript, Python, or small per-platform binaries?
- Can Claude Code and Codex both reliably invoke the selected runtime from
  installed plugin caches without extra user setup?
- Which supply-chain controls are required for the first public release, and
  which can safely remain follow-up hardening?
- Which repository-only scripts should remain Bash after plugin-runtime cutover,
  and how should they be classified so enforcement stays precise?

## SPEC Catalog Crosswalk

| Feature | Acceptance Criteria | SPEC | Depends On | Priority |
|---|---|---|---|---|
| Runtime inventory and constraints | AC-1.* | XPLAT-001 | None | P1 |
| Runtime options and contract decision | AC-2.* | XPLAT-002 | XPLAT-001 | P1 |
| Supply-chain security and consumer trust | AC-3.* | XPLAT-003 | XPLAT-002 | P1 |
| Runner foundation | AC-4.* | XPLAT-004 | XPLAT-002, XPLAT-003 | P1 |
| Read-only helper port | AC-5.* | XPLAT-005 | XPLAT-004 | P1 |
| Mutation/install/PR-emission helper port | AC-6.* | XPLAT-006 | XPLAT-004, XPLAT-005 | P1 |
| Claude/Codex cutover and release gate | AC-7.* | XPLAT-007 | XPLAT-005, XPLAT-006 | P1 |
