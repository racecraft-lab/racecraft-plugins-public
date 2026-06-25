# Feature Specification: Runtime Inventory and Constraints

**Feature Branch**: `codex/xplat-001-runtime-inventory-constraints`

**Created**: 2026-06-25

**Status**: Draft

**Input**: User description: "Inventory active Bash, jq, shell quoting, Unix-path, chmod, and related Unix runtime assumptions across the repository; classify them by runtime relevance and owner bucket; produce Markdown inventory and weighted runtime/security rubrics without selecting or implementing a replacement runtime."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review Runtime Inventory (Priority: P1)

As a maintainer, I can review one Markdown inventory report under `docs/ai/research/` and understand every whole-repo Bash or Unix-runtime assumption by category and owner bucket.

**Why this priority**: Later runtime work depends on knowing which references are real active installed-runtime dependencies and which are generated payloads, public docs, repository-only tooling, tests, fixtures, or historical/archive references.

**Independent Test**: A reviewer can open the inventory report, compare it against the documented whole-repo scan scope, and verify that every finding has evidence, runtime relevance, owner bucket, and follow-up spec.

**Acceptance Scenarios**:

1. **Given** a whole-repo scan result containing Bash, `.sh`, `jq`, shell-quoting, Unix-path, `chmod`, or line-ending references, **When** the maintainer reviews the report, **Then** every result is represented or explicitly excluded with evidence and rationale.
2. **Given** a finding marked as an active installed-runtime dependency, **When** the reviewer checks the finding, **Then** the report cites invocation-trace evidence from an installed skill, agent, hook, or generated payload.
3. **Given** a finding that appears only in tests, fixtures, docs, generated payload, or archive material, **When** the reviewer checks the finding, **Then** it is not promoted to an active runtime blocker without invocation-trace evidence.

---

### User Story 2 - Use Runtime Evaluation Rubric (Priority: P2)

As a runtime decision-maker, I can use a weighted runtime evaluation rubric without XPLAT-001 choosing the runtime for me.

**Why this priority**: XPLAT-002 needs stable criteria and weights so it can compare runtime candidates without reopening the inventory scope.

**Independent Test**: A reviewer can use the rubric to evaluate named candidate categories while confirming that no candidate is scored, ranked, or selected in XPLAT-001.

**Acceptance Scenarios**:

1. **Given** the inventory report, **When** the runtime decision-maker reviews the runtime rubric, **Then** it includes must-have gates, weighted criteria, and candidate evidence targets for XPLAT-002.
2. **Given** a named runtime candidate, **When** the reviewer checks the XPLAT-001 artifacts, **Then** the candidate appears only as an evaluation target and is not scored or chosen.

---

### User Story 3 - Use Supply-Chain Evaluation Rubric (Priority: P3)

As a security/trust decision-maker, I can use a weighted supply-chain evaluation rubric without XPLAT-001 choosing the security model for me.

**Why this priority**: XPLAT-003 needs stable consumer-trust criteria before runner implementation begins.

**Independent Test**: A reviewer can use the rubric to evaluate security and provenance options while confirming that no security model or control set is selected in XPLAT-001.

**Acceptance Scenarios**:

1. **Given** the inventory report, **When** the security/trust decision-maker reviews the supply-chain rubric, **Then** it includes must-have gates, weighted criteria, and artifact evidence targets for XPLAT-003.
2. **Given** a possible supply-chain control, **When** the reviewer checks the XPLAT-001 artifacts, **Then** the control appears only as an evaluation target and is not selected as the required model.

---

### Edge Cases

- A text match appears in generated payload and source files: the report must classify both locations and identify which source is authoritative for follow-up.
- A text match appears only in public documentation: the report must classify it as a public-docs claim unless an invocation trace proves installed-runtime behavior.
- A text match appears only in tests, fixtures, or archive reports: the report must classify it separately and avoid treating it as an active runtime blocker.
- A helper is repository-only today but may become installed-runtime later: the report must record current classification, rationale, and follow-up owner rather than inventing implementation work.
- An invocation trace is ambiguous or incomplete: the report must mark the finding as unproven active runtime and document the evidence gap.
- Runtime or security candidates are named in source material: the report may list them as evaluation targets, but must not score, rank, or select them.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The inventory report MUST cover whole-repo references to Bash, `.sh`, `jq`, shell quoting, Unix-path assumptions, `chmod`, and line-ending assumptions.
- **FR-002**: The inventory report MUST classify every finding as active installed-runtime dependency, generated payload reference, public documentation claim, repository-only maintainer tooling, tests/fixtures, historical/archive reference, or explicit exclusion.
- **FR-003**: The inventory report MUST require invocation-trace evidence before marking any finding as an active installed-runtime dependency.
- **FR-004**: Each inventory finding MUST include source evidence, runtime relevance, owner bucket, follow-up spec, and classification rationale.
- **FR-005**: The inventory report MUST include summary counts by classification, owner bucket, and follow-up spec.
- **FR-006**: Active installed-runtime findings MUST map to one of the follow-up owner buckets for XPLAT-005, XPLAT-006, XPLAT-007, repository-only exclusion, public-docs claim, generated-payload reference, historical/archive reference, or documented exception.
- **FR-007**: The report MUST separate active installed-runtime dependencies from generated payload, public docs, repository-only tooling, tests, fixtures, and historical/archive references.
- **FR-008**: The runtime evaluation rubric MUST define must-have gates, weighted criteria, and candidate evidence targets for XPLAT-002.
- **FR-009**: The supply-chain evaluation rubric MUST define must-have gates, weighted criteria, and artifact evidence targets for XPLAT-003.
- **FR-010**: XPLAT-001 artifacts MUST NOT score candidates, rank candidates, select a replacement runtime, or select supply-chain/security controls.
- **FR-011**: XPLAT-001 artifacts MUST NOT port helpers, change active Claude or Codex invocations, rebuild generated payloads, or claim native Windows support in public docs.
- **FR-012**: Verification MUST be static and source-traceable, with no native Windows UAT, runtime smoke probes, or platform execution probes required in this spec.
- **FR-013**: The durable report MUST be Markdown under `docs/ai/research/` and use structured tables, owner buckets, and summary counts.
- **FR-014**: The report MUST include enough evidence for reviewers to verify that later XPLAT runtime work is scoped to real active dependencies rather than untraced text matches.

### Reviewability Notes *(if applicable)*

- XPLAT-001 is one inventory/rubric spike. It may touch docs/process and scan/handoff evidence surfaces, but it must not change installed runtime behavior.
- Typed reviewability exceptions are not expected for this phase. If later phases exceed budget, the split decision belongs in planning or implementation review packets.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: harness/adapter evidence only, if needed to document scan or traceability method
- **Projected reviewable LOC**: 250
- **Projected production files**: 4
- **Projected total files**: 10
- **Budget result**: warning accepted
- **Split decision**: Remains one spec because XPLAT-001 is a single inventory/rubric spike with no runtime implementation, no generated payload rebuild, and no active invocation changes. The setup warning is driven by two review surfaces, not by implementation size.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Inventory Finding**: A source-traceable Bash or Unix-runtime assumption with path, evidence excerpt, classification, runtime relevance, owner bucket, follow-up spec, and rationale.
- **Invocation Trace**: Evidence that connects a finding to an active installed skill, agent, hook, generated payload, or other installed plugin runtime surface.
- **Owner Bucket**: The provisional handoff category that tells later XPLAT specs who owns the finding or why it is excluded from runtime implementation.
- **Runtime Evaluation Rubric**: Weighted criteria and must-have gates used by XPLAT-002 to evaluate runtime candidates.
- **Supply-Chain Evaluation Rubric**: Weighted criteria and must-have gates used by XPLAT-003 to evaluate consumer-trust and provenance options.
- **Candidate Evaluation Target**: A named runtime or supply-chain option that may be evaluated later but is not scored or selected in XPLAT-001.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of whole-repo scan matches for the scoped Bash and Unix-runtime assumptions are represented in the report or explicitly excluded with rationale.
- **SC-002**: 100% of findings marked active installed-runtime dependency include invocation-trace evidence.
- **SC-003**: 100% of inventory findings include source evidence, runtime relevance, owner bucket, follow-up spec, and classification rationale.
- **SC-004**: The report includes summary counts for every classification and owner bucket used in the inventory.
- **SC-005**: The runtime rubric includes at least one must-have gate and weighted criteria covering native platform behavior, installed-cache invocation, dependency footprint, packaging, offline behavior, diagnostics, maintainability, and compatibility adapters.
- **SC-006**: The supply-chain rubric includes at least one must-have gate and weighted criteria covering dependency policy, lockfiles, generated payload integrity, vulnerability scanning, provenance, checksums/signatures, SBOMs, and consumer-local verification.
- **SC-007**: No XPLAT-001 artifact scores, ranks, or selects a runtime candidate or supply-chain/security model.
- **SC-008**: No XPLAT-001 change ports helper behavior, changes active installed Claude/Codex invocation paths, rebuilds generated payloads, or claims native Windows support.

## Assumptions

- The existing XPLAT-001 worktree, branch, and feature directory are already created and are the only execution target for this phase.
- XPLAT-001 consumes the existing cross-platform runtime PRD, technical roadmap, workflow, design concept, and SPEC-MOC as source truth.
- The durable inventory/rubric report will live under `docs/ai/research/`; planning may choose the final filename while preserving that location.
- Static verification is sufficient for this phase because runtime decision work, smoke probes, native Windows UAT, and installed-runtime cutover belong to later XPLAT specs.
- Repository-only maintainer scripts and GitHub Actions are outside active installed-runtime scope unless an installed plugin surface invokes them.
- Public documentation can be inventoried as evidence or claims, but XPLAT-001 must not add public native Windows support claims.
