# Feature Specification: Runtime Inventory and Constraints

**Feature Branch**: `codex/xplat-001-runtime-inventory-constraints`

**Created**: 2026-06-25

**Status**: Complete

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
- A public docs claim mentions an installed prerequisite such as `jq`: the docs row remains a public-docs claim and may link to a separate active-runtime finding only when static invocation-trace evidence proves that runtime dependency.
- A text match appears only in tests, fixtures, or archive reports: the report must classify it separately and avoid treating it as an active runtime blocker.
- A helper is repository-only today but may become installed-runtime later: the report must record current classification, rationale, and follow-up owner rather than inventing implementation work.
- A helper has both read-only and write/apply behavior: the report must classify each traced installed invocation by invoked mode, not by the helper's maximum capability, and create separate rows when both modes are traced or materially relevant.
- An invocation trace is ambiguous or incomplete: the report must mark the finding as unproven active runtime and document the evidence gap.
- Runtime or security candidates are named in source material: the report may list them as evaluation targets, but must not score, rank, or select them.

## Clarifications

### Session 1: Inventory Boundaries

- Inventory rows use two axes: `classification` records where the reference lives or what kind of source it is, while `active_runtime_status` records whether it is proven active runtime, unproven active runtime, or not active runtime.
- Active runtime status requires static caller-to-callee evidence from an installed skill, agent, hook, generated payload, or other installed plugin surface to the referenced helper, dependency, or Unix-runtime assumption. A text match alone is not enough, and no runtime probe is required in XPLAT-001.
- Repository-only tooling is classified by invocation evidence, not path alone. Root scripts, release helpers, CI-only helpers, and maintainer tools stay repository-only unless an installed plugin surface invokes them.
- The whole-repo scan boundary is all tracked text files, including hidden tracked paths, `dist/**`, public docs, tests, fixtures, and archive reports. Exclusions are limited to `.git/`, binary assets, untracked files, vendor caches, and other non-text inputs with explicit rationale.
- Public documentation rows are `public-docs-claim` rows unless they link to a separate active-runtime finding with static invocation-trace evidence.

### Session 2: Owner Buckets and Handoff

- Owner bucket follows the traced active invocation mode, not the helper's maximum capability. If one helper has multiple active installed-runtime traces with different modes, record separate rows keyed by caller and mode.
- Use `xplat-005-read-only-helper` only for traced read-only or advisory invocations that do not mutate repository, user-local, or external state. Use `xplat-006-mutation-helper` for traced write, apply, live mutation, install, PR-emission, or mutation-capable dry-run/apply behavior whose parity must preserve apply semantics.
- Public docs rows use `public-docs-claim`, with XPLAT-007 ownership only for installed-workflow or cutover claims that must change when plugin runtime support changes.
- Generated `dist/**` payload rows use `generated-payload-reference`; active generated payload rows map to XPLAT-007 and link back to source rows when possible, but generated payloads are not authoritative edit targets in XPLAT-001.
- Repository-only Bash tooling uses `repository-only-exclusion` when no installed-runtime invocation trace exists. Add rationale and any later allowlist/guard note, but do not assign XPLAT-005, XPLAT-006, or XPLAT-007 ownership without active invocation evidence.
- `follow-up-exception` is allowed only for active or probably active rows that cannot honestly map to XPLAT-005, XPLAT-006, XPLAT-007, or an exclusion bucket. Each exception must include the reason, evidence gap, expiry or removal condition, and named follow-up decision.

### Session 3: Rubric Scope

- Runtime and supply-chain rubrics are non-scoring templates in XPLAT-001. Each rubric must include pass/fail must-have gates, explicit numeric criteria weights with a stated total, and candidate/control/artifact evidence targets.
- The supply-chain rubric must separate first-release gate questions from deferred hardening evidence so XPLAT-003 can choose required controls without XPLAT-001 implying that every evaluated control is immediately mandatory.
- XPLAT-001 must not include candidate scores, sample scoring, ranking, winner selection, required runtime choice, required security model, or required control set. Scoring and selection belong to XPLAT-002 and XPLAT-003.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The inventory report MUST cover whole-repo references to Bash, `.sh`, `jq`, shell quoting, Unix-path assumptions, `chmod`, and line-ending assumptions across tracked text files, including hidden tracked paths, `dist/**`, public docs, tests, fixtures, and archive reports.
- **FR-002**: The inventory report MUST classify every finding using both `classification` and `active_runtime_status`. Classification values MUST cover generated payload reference, public documentation claim, repository-only maintainer tooling, tests/fixtures, historical/archive reference, source reference, or explicit exclusion; active runtime status MUST distinguish proven active runtime, unproven active runtime, and not active runtime.
- **FR-003**: The inventory report MUST require static invocation-trace evidence before marking any finding as a proven active installed-runtime dependency.
- **FR-004**: Each inventory finding MUST include source evidence, runtime relevance, owner bucket, follow-up spec, active runtime status, and classification rationale.
- **FR-005**: The inventory report MUST include summary counts by classification, active runtime status, owner bucket, and follow-up spec.
- **FR-006**: Active installed-runtime findings MUST map to one of the follow-up owner buckets for XPLAT-005, XPLAT-006, XPLAT-007, repository-only exclusion, public-docs claim, generated-payload reference, historical/archive reference, or documented exception. For mixed-mode helpers, the owner bucket MUST follow the traced invocation mode at the inventory-row level.
- **FR-007**: The report MUST separate active installed-runtime dependencies from generated payload, public docs, repository-only tooling, tests, fixtures, and historical/archive references.
- **FR-008**: The runtime evaluation rubric MUST define pass/fail must-have gates, explicit numeric criteria weights with a stated total, and candidate evidence targets for XPLAT-002.
- **FR-009**: The supply-chain evaluation rubric MUST define pass/fail must-have gates, explicit numeric criteria weights with a stated total, artifact/control evidence targets for XPLAT-003, and a release-boundary distinction between first-release gate questions and deferred hardening evidence.
- **FR-010**: XPLAT-001 artifacts MUST NOT score candidates, rank candidates, select a replacement runtime, or select supply-chain/security controls.
- **FR-011**: XPLAT-001 artifacts MUST NOT port helpers to a replacement runtime, change active Claude or Codex invocation paths, or claim native Windows support in public docs. If review remediation corrects an existing shipped helper, generated payload edits MUST be limited to synchronized copies of that same helper.
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
- **Split decision**: Remains one spec because XPLAT-001 is a single inventory/rubric spike with no replacement-runtime implementation and no active invocation path changes. The setup warning is driven by two review surfaces, not by implementation size; post-PR generated payload edits are limited to synchronized copies of an existing helper remediation.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Inventory Finding**: A source-traceable Bash or Unix-runtime assumption with path, evidence excerpt, classification, active runtime status, runtime relevance, owner bucket, follow-up spec, and rationale.
- **Active Runtime Status**: The proof state for a finding: proven active runtime, unproven active runtime, or not active runtime.
- **Invocation Trace**: Static caller-to-callee evidence that connects a finding from an installed skill, agent, hook, generated payload, or other installed plugin runtime surface to the referenced helper, dependency, or Unix-runtime assumption.
- **Owner Bucket**: The provisional handoff category that tells later XPLAT specs who owns the finding or why it is excluded from runtime implementation.
- **Mixed-Mode Helper**: A helper with both read-only/advisory and write/apply behavior; each traced installed invocation is inventoried separately when the modes imply different XPLAT owners.
- **Runtime Evaluation Rubric**: Weighted criteria and must-have gates used by XPLAT-002 to evaluate runtime candidates.
- **Supply-Chain Evaluation Rubric**: Weighted criteria and must-have gates used by XPLAT-003 to evaluate consumer-trust and provenance options.
- **Candidate Evaluation Target**: A named runtime or supply-chain option that may be evaluated later but is not scored or selected in XPLAT-001.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of whole-repo scan matches for the scoped Bash and Unix-runtime assumptions are represented in the report as individual rows or aggregate/match-summary rows, or explicitly excluded with rationale. Aggregate/match-summary rows MUST preserve scan-command traceability, match count, path set or path pattern, matched token or pattern family, classification, active runtime status, owner bucket, follow-up spec, and rationale without combining matches that need different ownership, proof state, invocation mode, or exception treatment.
- **SC-002**: 100% of findings marked active installed-runtime dependency include invocation-trace evidence.
- **SC-003**: 100% of inventory findings include source evidence, runtime relevance, owner bucket, follow-up spec, active runtime status, and classification rationale.
- **SC-004**: The report includes summary counts for every classification, active runtime status, and owner bucket used in the inventory.
- **SC-005**: The runtime rubric includes pass/fail must-have gates and numeric weighted criteria with a stated total covering native platform behavior, installed-cache invocation, dependency footprint, packaging, offline behavior, diagnostics, maintainability, and compatibility adapters.
- **SC-006**: The supply-chain rubric includes pass/fail must-have gates and numeric weighted criteria with a stated total covering dependency policy, lockfiles, generated payload integrity, vulnerability scanning, provenance, checksums/signatures, SBOMs, and consumer-local verification, with each criterion or control evidence target clearly separated as a first-release gate question or deferred hardening evidence for XPLAT-003 decision-making.
- **SC-007**: No XPLAT-001 artifact scores, ranks, or selects a runtime candidate or supply-chain/security model.
- **SC-008**: No XPLAT-001 change ports helper behavior to a replacement runtime, changes active installed Claude/Codex invocation paths, or claims native Windows support. Any generated payload edit is limited to source-to-dist synchronization for an existing helper remediation.

## Assumptions

- The existing XPLAT-001 worktree, branch, and feature directory are already created and are the only execution target for this phase.
- XPLAT-001 consumes the existing cross-platform runtime PRD, technical roadmap, workflow, design concept, and SPEC-MOC as source truth.
- The durable inventory/rubric report will live under `docs/ai/research/`; planning may choose the final filename while preserving that location.
- Static verification is sufficient for this phase because runtime decision work, smoke probes, native Windows UAT, and installed-runtime cutover belong to later XPLAT specs.
- Repository-only maintainer scripts and GitHub Actions are outside active installed-runtime scope unless an installed plugin surface invokes them.
- Public documentation can be inventoried as evidence or claims, but XPLAT-001 must not add public native Windows support claims.
- Generated payload references are inventoried as generated artifacts and linked back to source when possible; they are not the authoritative source for edits unless the plan explicitly proves otherwise.
