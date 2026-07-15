# Feature Specification: Harness Surface Inventory and Gap Taxonomy

**Feature Branch**: `hrns-001-harness-surface-inventory-gap-taxonomy`

**Created**: 2026-07-15

**Status**: Draft

**Input**: User description: "Create a source-grounded harness surface inventory and gap taxonomy for SpecKit Pro, using the verified merged baseline as authority, without blocking on CAR or G56R."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Trace Harness Gaps to Ownership (Priority: P1)

As a SpecKit Pro maintainer planning downstream HRNS work, I can use one
source-grounded taxonomy to trace every relevant harness surface and retained
gap to its state, evidence, owner workflow, dependency posture, safety closure,
and downstream spec ownership so that I do not duplicate work or make an
ungrounded dependency decision.

**Why this priority**: This is the baseline needed by HRNS-002, HRNS-003,
HRNS-005, and HRNS-009. Without it, later specs risk rediscovering the same
surfaces, misclassifying evidence, or absorbing CAR/G56R-owned work.

**Independent Test**: A reviewer can inspect only the canonical taxonomy
artifact and determine which harness surfaces exist, which gaps remain, what
evidence supports each gap, whether CAR/G56R owns any work, and what downstream
HRNS spec should handle each retained gap.

**Acceptance Scenarios**:

1. **Given** the merged repository baseline, **When** a maintainer reviews the
   taxonomy, **Then** every required harness surface category is represented
   and every retained gap is tied to at least one surface.
2. **Given** a downstream HRNS author needs to plan a spec, **When** they find a
   retained gap, **Then** the row identifies lifecycle state, evidence class,
   owner workflow, dependency posture, self-improvement closure, and downstream
   ownership.
3. **Given** a gap overlaps CAR or G56R, **When** the maintainer reviews the
   row, **Then** HRNS-001 marks the external owner and reference evidence
   without blocking on or absorbing that work.
4. **Given** an external candidate is considered, **When** the candidate matrix
   is reviewed, **Then** each recommendation is backed by dated primary
   evidence or an explicit `unknown` value.
5. **Given** HRNS-001 is ready for review, **When** the PR packet is prepared,
   **Then** AC-1.1 through AC-1.10 have an explicit crosswalk and the smallest
   applicable documentation checks are recorded.

---

### Edge Cases

- CAR or G56R evidence exists only on an unmerged branch; the taxonomy treats it
  as planned reference evidence, not current authoritative state.
- A harness gap appears under multiple surfaces; the taxonomy keeps one
  canonical row and multiple surface tags rather than duplicate rows.
- External primary evidence is missing, stale, or unclear; the affected field is
  recorded as `unknown` and cannot support dependency adoption.
- A workflow can influence future harness behavior but lacks proof of bounded
  human control; the closure is `unknown/non-promotable`.
- Generated distributions, installed caches, raw transcripts, fixtures, or
  derived indexes disagree with source files; repository source evidence wins.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The taxonomy MUST inventory current SpecKit Pro skills, agents,
  commands, helpers, runner surfaces, generated payloads, docs, workflow files,
  PR packets, tests, evals, and release gates from the verified merged baseline.
- **FR-002**: The taxonomy MUST tag every retained gap to at least one harness
  surface category: skill, agent, command, helper, runner, generated payload,
  docs, workflow file, PR packet, test/eval, or release gate.
- **FR-003**: The taxonomy MUST give every retained gap one stable `HRNS-GAP`
  identity and one canonical row. [NEEDS CLARIFICATION] Finalize HRNS-GAP ID
  format and canonical row fields.
- **FR-004**: The taxonomy MUST classify retained gaps by type, including
  context, tool contract, permission, sandbox, memory/state, orchestration,
  verification, observability, HITL, security, garbage collection, or an
  explicitly justified extension.
- **FR-005**: The taxonomy MUST classify retained gaps by lifecycle state:
  implemented, planned, deferred, duplicate, obsolete, or unknown.
- **FR-006**: The taxonomy MUST record owner workflow, cross-roadmap ownership,
  downstream HRNS ownership, and CAR/G56R references without treating unmerged
  work as authoritative current state.
- **FR-007**: The taxonomy MUST record dependency posture for every retained
  gap: repo-local convention, runner/helper change, generated-doc/test evidence,
  future explicit dependency decision, deferred, or unknown.
- **FR-008**: The artifact MUST include an external-candidate matrix covering
  relevant schema, orchestration, eval, trace/observability, guardrail,
  workflow-runtime, coding-agent harness, and knowledge-format references.
  [NEEDS CLARIFICATION] Finalize candidate set, primary-source types,
  as-of/version fields, and recommendation vocabulary.
- **FR-009**: The taxonomy MUST record self-improvement loop closure for any
  workflow that can generate or influence future harness behavior: human-in-the-
  loop, human-on-the-loop, fully automated, disallowed, or
  unknown/non-promotable.
- **FR-010**: The inventory MUST classify authoritative source evidence and
  explicitly exclude generated distributions, caches, fixtures, raw transcripts,
  unreviewed chat, and derived indexes as factual authority.
- **FR-011**: The taxonomy MUST include knowledge initialization, incremental
  ingest and synthesis, query and compounding capture, structural conformance,
  health/drift, code-intelligence interoperability, external exchange,
  provenance, conflict handling, and cross-distribution parity as distinct gap
  and ownership areas.
- **FR-012**: The artifact MUST record the normative OKF revision, maturity,
  reference-tooling evidence, compatibility gaps, extension posture, and
  blocking/advisory/deferred disposition.
- **FR-013**: The artifact MUST include an AC-1.1 through AC-1.10 crosswalk,
  surface coverage proof, evidence-class coverage proof, link review, and
  intentional-deferment notes. [NEEDS CLARIFICATION] Finalize completion proof,
  documentation checks, and PR packet evidence.

### Reviewability Notes *(if applicable)*

- HRNS-001 is a docs/process planning spec. It MUST NOT introduce runtime code,
  machine-readable registries, generated payload edits, installed-cache edits,
  vendored edits, or new validator code.
- Typed reviewability exceptions are not expected. If later phases discover a
  budget issue, the workflow must record it in reviewability evidence rather
  than expanding the implementation surface.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: N/A
- **Projected reviewable LOC**: 335
- **Projected production files**: 4
- **Projected total files**: 8
- **Budget result**: within budget
- **Split decision**: Keep one docs/process spec. The scaffold estimator used
  one user story, four files, and ten functional requirements and returned one
  suggested slice with status `ok`; O5 is not indicated.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include what the taxonomy changes, why it exists,
  non-goals, review order, scope budget, AC-1.1 through AC-1.10 traceability,
  verification evidence, known gaps, and intentional deferrals.
- Traceability MUST map each major requirement and acceptance criterion to the
  taxonomy artifact section and verification evidence.
- Deferred work MUST name the owning follow-up HRNS, CAR, G56R, or roadmap
  entry.
- The PR packet MUST state that HRNS-001 does not authorize dependency adoption,
  runtime changes, or generated-artifact changes.

### Key Entities *(include if feature involves data)*

- **Harness Surface**: A source, command, helper, runner, workflow, document,
  generated payload, test/eval, PR packet, or release gate that can affect
  long-running SpecKit Pro agent behavior.
- **Retained Gap**: A reviewed observation that remains relevant after
  duplicate, obsolete, and out-of-scope items are removed.
- **External Candidate**: A third-party standard, framework, library, tool, or
  exemplar used as reference evidence for future harness decisions.
- **Evidence Class**: A category describing whether a source is authoritative,
  generated, fixture-like, unreviewed, derived, or excluded as factual authority.
- **Closure Classification**: The human-control or automation boundary for a
  workflow that can influence future harness behavior.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reviewer can trace 100% of AC-1.1 through AC-1.10 to a named
  taxonomy section or row.
- **SC-002**: Every retained gap row has a stable ID, at least one surface tag,
  lifecycle state, evidence reference, owner workflow, dependency posture, and
  downstream ownership value.
- **SC-003**: Every external candidate row has an as-of date and either dated
  primary evidence for each required field or an explicit `unknown`.
- **SC-004**: The artifact contains zero duplicated gap ownership rows; gaps
  that apply to multiple surfaces use one canonical row with multiple tags.
- **SC-005**: The PR packet records the canonical artifact, review scope,
  verification commands, AC crosswalk, and all intentional deferrals.

## Assumptions

- The verified merged `origin/main` baseline is the current factual authority
  for HRNS-001.
- CAR and G56R do not block HRNS-001; unmerged work is reference evidence only.
- The canonical deliverable is
  `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md`.
- Later HRNS specs may update the taxonomy through normal review while
  preserving stable gap IDs and history.
- Existing repository checks and link/crosswalk proof are sufficient for
  HRNS-001; new validator code is out of scope.
