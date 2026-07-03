# Design Concept: XPLAT-005 Read-Only Helper Port

**Spec ID:** XPLAT-005
**Spec Name:** Read-Only Helper Port
**Branch:** `codex/xplat-005-read-only-helper-port`
**Created:** 2026-07-01
**Source Roadmap:** `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`

## Setup Context

XPLAT-005 starts after XPLAT-004 shipped and archived the Python 3.11+
standard-library runner foundation. The roadmap marks XPLAT-005 ready and
assigns it the read-only/advisory helper migration: prerequisites, detection,
counting, validation, reviewability, topology, routing, layer-planning, and
spec-index generation helpers that do not mutate user state.

The setup reviewability gate returned `status=warn`, `pass=true`,
`reviewable_loc=250`, `production_files=4`, `total_files=10`, and warned that
two primary surfaces (`docs/process` and `harness/adapter`) exceed the
one-surface warning threshold. The accepted setup direction is one XPLAT-005
workflow with two internal implementation slices.

## Goals

- Port read-only and advisory helpers onto the XPLAT runner while preserving
  current JSON stdout schemas, stderr diagnostics, and exit-code behavior.
- Establish a small helper registry plus per-helper module pattern that
  XPLAT-006 can reuse for mutation helpers.
- Use deterministic golden fixtures and source-checkout comparisons against the
  current Bash helpers before accepting Python output.
- Promote Python standard-library tests to the release gate for each helper
  only after fixture and Bash-reference parity pass.
- Include a local macOS source-checkout smoke for the accepted read-only helper
  path without making installed-cache or public platform support claims.
- Keep XPLAT-005 reviewable through two planned slices inside one workflow.

## Non-Goals

- Do not update active Claude Code or Codex skill, hook, generated payload, or
  install invocation paths.
- Do not port mutation helpers that write PR packets, emit split-PR state,
  install agents, relocate artifacts, generate PR bodies, or mutate repository
  or user-local state.
- Do not run full native Windows/macOS/Linux installed-plugin UAT; that remains
  XPLAT-007.
- Do not remove Bash helpers globally. Retain Bash helpers as temporary
  reference implementations until XPLAT-007 cutover.
- Do not make public native-platform support claims.

## Accepted Slice Strategy

| Slice | Focus | Acceptance Boundary |
|---|---|---|
| Slice 1 | Foundational prereq/status helpers and shared helper dispatch | Port prerequisite, detection, marker, validation, and confidence helpers first; prove fixture and Bash-reference parity before promotion |
| Slice 2 | Planning/index/topology validators and late read-only PR-packet validation | Port spec-index, topology, atomicity/layer planning, workflow-contract validation, and `validate-pr-packet` only as a read-only validator |

Split into separate child specs only if the Specify/Plan/Tasks phases prove the
two-slice workflow cannot stay within the roadmap reviewability budget.

## Grill Me Q&A Log

### Q1. How should XPLAT-005 be scoped for reviewability?

**Accepted answer:** One workflow, two slices.

Use one XPLAT-005 workflow with explicit internal slices so autopilot can keep
one branch while preserving review order and reviewability. Do not create child
specs during scaffold.

### Q2. Which helper group should XPLAT-005 port first?

**Accepted answer:** Prereq/status first.

Start with prerequisite, detection, marker, validation, and confidence helpers.
These unblock later doctor/preflight work and give XPLAT-006 stable patterns.

### Q3. What parity bar should the helper ports use?

**Accepted answer:** Golden fixtures plus Bash comparison.

Use deterministic fixtures and source-checkout comparisons against current Bash
helpers before accepting Python output. The comparison is a migration proof, not
an installed-runtime dependency claim.

### Q4. Should XPLAT-005 change active Claude/Codex skill or hook invocations?

**Accepted answer:** No active cutover.

XPLAT-005 ports helpers and tests only. Active skill, hook, generated payload,
install, and public documentation cutover remains XPLAT-007.

### Q5. How should XPLAT-005 handle `validate-pr-packet`?

**Accepted answer:** Include validation late.

Port only the read-only validator after foundational helpers. PR body
generation, PR emission, split state, and restack mutation remain XPLAT-006.

### Q6. When should Python helper tests become the release gate?

**Accepted answer:** After parity accepted.

Keep Bash helpers as reference implementations while porting. Promote Python
tests for each helper once fixture parity and Bash-reference comparison pass.

### Q7. What platform proof belongs in XPLAT-005?

**Accepted answer:** Add local macOS smoke.

Cover Windows-style paths and no-Bash behavior through deterministic fixtures,
and add local macOS source-checkout smoke evidence. Installed-cache launch
proof and full native matrix UAT remain XPLAT-007.

### Q8. What shared runner API shape should XPLAT-005 establish?

**Accepted answer:** Registry plus modules.

Add a small helper registry/dispatch pattern and per-helper modules. Avoid a
generic framework, but give XPLAT-006 a stable extension point.

## Open Questions For Clarify

- Exact Slice 1 helper list: confirm whether `validate-gate`,
  `resolve-confidence-mode`, and `confidence-gate` should ship together or be
  ordered after `check-prerequisites` and detection helpers.
- Exact Slice 2 helper list: confirm whether `validate-pr-workflow-contract`
  belongs with topology/index helpers or with late PR-packet validation.
- Parity fixture shape: decide which helpers require direct Bash comparison,
  which can use golden fixtures only, and how to isolate environment-sensitive
  outputs.
- Gate promotion wording: decide how the workflow records "Python gate
  authoritative for helper X" while Bash remains a temporary reference for
  unported helpers.
- Local macOS smoke scope: define the smallest source-checkout command that
  proves the runner path without claiming installed-cache support.

## Downstream Handoff

- XPLAT-006 should consume the helper registry and per-helper module pattern
  for mutation, install, and PR-emission helpers.
- XPLAT-007 remains responsible for active Claude/Codex cutover, generated
  payload propagation, installed-cache launch proof, native Windows/macOS/Linux
  UAT, update/autoheal proof, and public release claims.
