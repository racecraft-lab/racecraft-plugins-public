# PRD: Cross-Platform Plugin Runtime for SpecKit Pro

**Status**: Draft
**Created**: 2026-06-24
**Last updated**: 2026-06-28
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
supply-chain confidence. The implementation path selected by the amended
XPLAT-002/XPLAT-003 decision is a Python 3.11+ standard-library runner that
leans on the official Spec Kit / `specify` prerequisite boundary. That decision
also applies to active build, test, eval, and release-readiness gates that
validate or publish shipped plugin behavior.

## Confidence Posture

Python is the highest-confidence runtime path because it is already part of the
official Spec Kit / `specify` prerequisite boundary, so XPLAT does not add a new
user-installed implementation runtime. Planning confidence is high that Python
3.11+ standard-library APIs can support the runner consistently across native
Windows, macOS, and Linux:

- Python as the universal dependency: high confidence, approximately 90%.
- Python stdlib runner behavior after launch: high confidence, approximately
  85-90%.
- Full Claude/Codex installed-plugin user journey today: medium confidence,
  approximately 65-75%, because XPLAT-004 and XPLAT-007 still need installed
  cache launch proof, generated-payload cutover, and platform UAT.

These confidence levels are planning inputs, not public support evidence.
Native Windows/macOS/Linux claims remain blocked until downstream specs prove
interpreter discovery, `specify` discovery, installed-cache execution, payload
freshness, and full workflow UAT for every claimed platform and host product.

## Goals

- A public user can install SpecKit Pro on Claude Code or Codex and run the
  documented plugin workflows on native Windows, macOS, and Linux.
- A first-time user can move from install to first successful scaffold/status
  and autopilot dry-run without manually repairing missing bundled agents,
  hooks, helper scripts, or generated payload files.
- Installed plugin workflows no longer require Bash, Git Bash, WSL, PowerShell,
  or `jq` as the implementation substrate.
- Active plugin build, test, eval, and release-readiness gates that validate or
  publish shipped behavior run through Python standard-library tooling rather
  than Bash-only scripts.
- Claude and Codex plugin behavior stays semantically equivalent during and
  after the migration.
- The runtime choice is evidence-backed before implementation starts.
- Consumers can evaluate the plugin's runner files, dependencies, and
  release provenance before adopting it.
- Scaffold and autopilot can diagnose and repair incomplete installs where that
  is safe, and otherwise return a concrete remediation message.
- The migration is reviewable: each implementation spec is small enough to test,
  compare, and roll back independently.

## Desired Universal User Journey

XPLAT is complete only when the normal user journey works, not merely when Bash
has been removed from individual helper scripts.

1. A user installs the latest tagged SpecKit Pro plugin release for Claude Code,
   Codex, or both.
2. The installed plugin contains every required skill, bundled agent, hook,
   runner source file, optional thin launcher, manifest/checksum entry, and
   generated payload file for that product surface.
3. The user runs the first documented workflow, including scaffold/status and an
   autopilot dry-run, without installing Bash, Git Bash, WSL, PowerShell-specific
   shims, `jq`, Go, Rust, Zig, or any implementation runtime beyond official
   Spec Kit / `specify` prerequisites.
4. If the local install is stale or incomplete, scaffold/status/autopilot run a
   shared doctor/preflight check, auto-repair safe gaps, and report exact manual
   remediation for unsafe gaps.
5. The user can update to the latest tagged release and rerun the same workflows
   with version, payload, and bundled-agent consistency verified across Claude
   Code and Codex.
6. Maintainers have a readable UAT runbook that proves the journey across native
   Windows, macOS, Linux, and any explicitly documented WSL path before public
   release claims are made.
7. Maintainers can run the active release-readiness test/eval suite on each
   platform without Bash, `jq`, Git Bash, WSL, or PowerShell helper scripts.

## Non-Goals

- Rewriting historical/archive prose that mentions prior Bash implementations.
- Replacing GitHub Actions YAML or minimal CI shell wrappers when they only
  dispatch to Python gates and do not contain plugin validation logic.
- Replacing GitHub Spec Kit's own generated `.specify/scripts/bash/` helpers in
  consumer repositories.
- Replacing unrelated repository-only shell scripts that neither build, test,
  evaluate, publish, nor validate shipped plugin behavior.
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
- AC-1.2: Historical/archive Bash references are classified separately from
  active runtime and active verification references so enforcement can avoid
  false positives without exempting release gates.
- AC-1.3: Each active runtime or active release-gate dependency has an owner
  category: read-only helper, mutation/helper, test/eval gate, build/payload
  gate, cutover guidance, unrelated repository-only exclusion, or follow-up
  exception.
- AC-1.4: The inventory produces an evaluation rubric for runtime candidates,
  including native Windows/macOS/Linux support, invocation from installed plugin
  caches, dependency footprint, packaging, offline behavior, diagnostics, and
  maintainability.

### 2. Runtime Implementation Options and Contract Decision *(-> XPLAT-002)*

Research and evaluate implementation options before building the runner. The
completed decision now locks one canonical runtime contract for later specs:
Python 3.11+ standard-library source aligned with the official Spec Kit /
`specify` prerequisite boundary. JavaScript/TypeScript and compiled
per-platform binaries are rejected historical candidates, not fallback paths for
XPLAT.

**Acceptance Criteria**

- AC-2.1: Candidate strategies are compared against the XPLAT-001 rubric,
  including native platform behavior, Claude/Codex invocation reliability,
  packaging/distribution model, dependency management, update path, performance,
  diagnostics, and maintainer ergonomics.
- AC-2.2: Where runtime mechanics are uncertain, smoke probes or documented
  platform evidence verify that Claude Code and Codex can invoke the candidate
  from installed plugin caches without extra user setup.
- AC-2.3: The decision record selects Python standard-library source, explains
  rejected options, and names any compatibility adapters that are allowed
  temporarily. Compiled binaries are not an allowed adapter or fallback.
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
- AC-3.2: The approach evaluates SBOMs, provenance/attestations, runner-file
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
  output for fixtures while Bash still exists as a temporary reference oracle.
- AC-4.5: Foundation implementation includes the XPLAT-003 first-release
  security controls that apply to runtime source, dependencies, and generated
  runner files.
- AC-4.6: The foundation introduces Python standard-library test/eval runner
  patterns so later ports can retire Bash-only Layer 4 tests and AI-eval
  wrappers without changing expected semantics.

### 5. Read-Only Helper Port *(-> XPLAT-005)*

Port the read-only and advisory helpers first: prerequisite checks, command and
preset detection, gates, counters, reviewability estimation, layer planning,
atomicity routing, topology checks, and spec-index generation.

**Acceptance Criteria**

- AC-5.1: Every read-only helper used by autopilot, scaffold/status, agents, or
  docs-generation has a cross-platform implementation.
- AC-5.2: Fixture parity proves equivalent JSON output and exit semantics against
  current Bash behavior before cutover, then the Python fixture tests become the
  active release gate.
- AC-5.3: The new helpers do not shell out for path traversal, JSON construction,
  text parsing, or glob expansion.
- AC-5.4: The existing Claude and Codex guidance can still use the Bash path
  only until XPLAT-007 performs the final cutover; Bash-only tests may remain
  only as temporary parity fixtures before then.

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
- AC-6.5: Install and agent helpers verify the complete expected bundled-agent
  set for Claude Code and Codex from a source manifest or generated inventory,
  rather than from a stale hardcoded list.
- AC-6.6: Scaffold/status/autopilot can call a shared doctor/preflight contract
  that detects stale releases, missing runner files, missing generated
  payload files, and missing bundled agents before workflow execution continues.
- AC-6.7: Mutation-helper test coverage is ported to Python standard-library
  gates before the Bash helper is removed from the release-readiness path.

### 7. Claude/Codex Cutover and Universal Install Release Gate *(-> XPLAT-007)*

Switch active Claude and Codex plugin surfaces from Bash helpers to the
cross-platform runner, remove Bash/`jq` from plugin-runtime prerequisites, rebuild
payloads, and add release gates that block reintroducing active Bash runtime
dependencies or publishing incomplete Claude/Codex installs.

**Acceptance Criteria**

- AC-7.1: Active Claude and Codex skills, agents, hooks, install guidance, and
  generated payloads invoke the cross-platform runner, not Bash scripts.
- AC-7.2: Public plugin docs state the new runtime prerequisites and no longer
  describe Bash, Git Bash, WSL, PowerShell, or `jq` as required for installed
  plugin workflows.
- AC-7.3: Deterministic checks fail if an active installed-runtime surface
  reintroduces `bash`, `.sh`, `jq`, shell interpolation, or Unix-only path
  assumptions outside explicitly allowlisted historical/archive references.
- AC-7.3a: Deterministic checks fail if active plugin build, test, eval, payload,
  or release-readiness gates that validate shipped behavior remain Bash-only or
  require `jq`, Git Bash, WSL, or PowerShell helper scripts.
- AC-7.4: Manual UAT evidence covers native Windows, macOS, and Linux for both
  Claude and Codex plugin journeys: install, bundled-agent verification,
  scaffold/status, autopilot dry-run, update, and safe repair of an incomplete
  install.
- AC-7.5: Public release is blocked until the native Windows UAT path passes
  without WSL, Git Bash, or PowerShell-specific workarounds.
- AC-7.6: Public release notes and docs accurately describe the implemented
  supply-chain security model without overstating guarantees.
- AC-7.7: UAT runbooks are human-readable and complete, with no placeholder PR
  fields, raw HTML anchors, empty expected-result sections, or unfilled
  platform/product rows.

## Success Metrics

- Zero active Claude/Codex plugin runtime invocations require Bash or `jq`.
- All ported helpers pass fixture parity before cutover and native platform tests
  after cutover.
- A native Windows developer can complete install, `$install`/agent setup,
  scaffold/status, and an autopilot dry-run path without a Unix shell.
- Claude Code and Codex installs both contain 100 percent of expected bundled
  agents, hooks, runner files, and generated payload files for the latest
  tagged release.
- Zero active plugin test/eval/release-readiness gates that validate or publish
  shipped behavior require Bash, `jq`, Git Bash, WSL, or PowerShell helper
  scripts.
- Scaffold/status/autopilot detect incomplete installs before doing meaningful
  work and either autoheal them or provide a specific, tested remediation path.
- The release-readiness checklist has a hard gate for native Windows plugin UAT.
- Public runner files have documented dependency, provenance, and local
  verification expectations.

## Open Questions

- Can the amended Python standard-library runner contract prove reliable launch
  from installed Claude and Codex caches on native Windows, macOS, and Linux?
- Can Claude Code and Codex both reliably invoke the selected runtime from
  installed plugin caches without extra user setup?
- Which supply-chain controls are required for the first public release, and
  which can safely remain follow-up hardening?
- Which unrelated repository-only scripts, if any, can remain Bash after
  plugin-runtime cutover, and what guard prevents them from becoming runtime,
  test/eval, payload, or release-readiness dependencies later?

## SPEC Catalog Crosswalk

| Feature | Acceptance Criteria | SPEC | Depends On | Priority |
|---|---|---|---|---|
| Runtime inventory and constraints | AC-1.* | XPLAT-001 | None | P1 |
| Runtime options and contract decision | AC-2.* | XPLAT-002 | XPLAT-001 | P1 |
| Supply-chain security and consumer trust | AC-3.* | XPLAT-003 | XPLAT-002 | P1 |
| Runner foundation | AC-4.* | XPLAT-004 | XPLAT-002, XPLAT-003 | P1 |
| Read-only helper port | AC-5.* | XPLAT-005 | XPLAT-004 | P1 |
| Mutation/install/PR-emission helper port | AC-6.* | XPLAT-006 | XPLAT-004, XPLAT-005 | P1 |
| Claude/Codex cutover and universal install release gate | AC-7.* | XPLAT-007 | XPLAT-005, XPLAT-006 | P1 |
