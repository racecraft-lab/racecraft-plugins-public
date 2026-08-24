# Feature Specification: Capability-aware Resolver, Materializer, Installer, and Strict Override

**Feature Branch**: `g56r-006-resolver-materializer-installer-strict-override`

**Created**: 2026-08-24

**Status**: Draft

**Input**: User description: "Create G56R-006: Capability-aware Resolver, Materializer, Installer, and Strict Override."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Route-aware batch installation plan (Priority: P1)

As a SpecKit Pro maintainer, I need a route-aware dry-run or apply request to resolve and byte-prove every required Codex agent from one fresh capability snapshot and one trusted policy manifest, so I can review the complete installation decision before any user agent file changes.

**Why this priority**: This is the minimum viable framework slice. Without a complete required-agent plan, downstream route qualification cohorts cannot safely supply final policies.

**Independent Test**: Can be fully tested with deterministic route policies and a fake Codex agents home by running dry-run and apply requests that produce a complete required roster, byte proofs, and no bundled-source mutations.

**Acceptance Scenarios**:

1. **Given** a trusted manifest containing policies for the full current roster and an injected capability snapshot where every required route is available, **When** route-aware dry-run runs, **Then** the response includes one snapshot identity, ordered resolution records for all 12 required agents, materialization proofs for each destination file, no planned writes to bundled source files, and the optional helper state.
2. **Given** the same manifest and snapshot, **When** route-aware apply runs against a fake home with missing or stale required agents, **Then** all required destination TOMLs are installed only after every required agent resolves and materializes successfully, and post-apply verification reports the complete required roster.
3. **Given** no trusted route-policy manifest input, **When** the existing install request runs, **Then** static compatibility mode preserves the current route-agnostic installation behavior and does not attempt capability discovery, route resolution, optional-helper omission, or strict override validation.

---

### User Story 2 - Strict global override validation (Priority: P1)

As a maintainer testing a global model override, I need the override to validate the complete required set before mutation and to handle the optional helper according to the approved Q8 rule, so a single incompatible tuple cannot silently fall back or partially install.

**Why this priority**: The override changes the selected route for many agents at once. It must fail closed for required agents and preserve helper optionality without weakening the required roster.

**Independent Test**: Can be fully tested with deterministic manifests that include compatible and incompatible required-agent tuples plus compatible and incompatible helper tuples.

**Acceptance Scenarios**:

1. **Given** a strict global override whose model is compatible with every required agent while preserving each required effort and non-route contract, **When** route-aware dry-run runs, **Then** every required resolution record uses the override route, no required fallback route is selected, and mutation remains blocked until the full batch proof succeeds.
2. **Given** a strict global override where one required agent has no compatible tuple, **When** route-aware dry-run or apply runs, **Then** every required agent is still evaluated for diagnostics, the response marks the required miss, no destination write or helper removal occurs, and no required agent falls back to another route.
3. **Given** a strict global override with a compatible helper tuple, **When** the helper is qualified under the same batch snapshot, **Then** the helper is included in the destination plan with a resolved helper policy.
4. **Given** a strict global override with no compatible helper tuple but a validated no-helper continuation, **When** all required agents resolve, **Then** the required install may proceed without installing a different helper route.

---

### User Story 3 - Optional helper omitted or removed safely (Priority: P2)

As a maintainer preserving user-owned agent files, I need an unavailable optional helper to be omitted or removed only when plugin ownership is proven, so required installation can succeed without deleting user-modified files.

**Why this priority**: The optional helper must not fail the required roster, but removal is destructive enough to require proof.

**Independent Test**: Can be fully tested with fake-home states containing no helper, a plugin-managed helper, a known rendered-byte helper, and a same-named user-modified helper.

**Acceptance Scenarios**:

1. **Given** all required agents resolve and the optional helper has no qualified route, **When** no helper file exists in the fake-home destination, **Then** the route-aware response records validated no-helper continuation and the required roster installs successfully.
2. **Given** all required agents resolve, the optional helper has no qualified route, and an existing helper file has trusted install provenance or a known rendered-byte match, **When** apply runs, **Then** helper removal is planned with managed-file proof, participates in the same rollback-backed batch, and is reflected in the top-level routing evidence.
3. **Given** all required agents resolve, the optional helper has no qualified route, and an existing same-named helper lacks managed-file proof, **When** dry-run or apply runs, **Then** the file is preserved, the required roster may still succeed, and the response includes manual-remediation evidence explaining why automatic removal was refused.

---

### User Story 4 - Complete failure evidence with preservation (Priority: P2)

As a maintainer diagnosing route or filesystem failures, I need complete structured evidence and preservation of the previous known-good installation, so retries are reproducible and failures do not leave partial agent state.

**Why this priority**: A route-aware installer is only safe if every failure mode is inspectable and rollback or zero-write behavior is provable.

**Independent Test**: Can be fully tested with deterministic injected route misses, discovery/probe failures, unsafe destination entries, write failures, verification failures, rollback success, and rollback failure cases in fake homes.

**Acceptance Scenarios**:

1. **Given** at least one required agent has no safe route, **When** route-aware dry-run or apply runs, **Then** the resolver completes the bounded read-only pass for every required agent, returns all attempted routes and rejection reasons, and performs zero writes or removals.
2. **Given** all required agents resolve but a destination write or managed-helper removal fails during apply, **When** rollback succeeds, **Then** prior bytes and file modes are restored, the response records staged, applied, rolled-back, and cleanup actions, and the final state matches the previous known-good state.
3. **Given** rollback cannot fully restore the previous known-good state, **When** apply returns, **Then** the response reports the failed rollback actions, marks that state may have changed, and includes bounded manual-remediation instructions without claiming verification success.

### Edge Cases

- Trusted manifest is missing, malformed, wrong-versioned, incomplete, or contains policies outside the current 12-required-plus-one-optional roster.
- Bundled Codex agent source inventory is missing one of the 13 TOMLs, includes unexpected TOMLs, contains legacy Markdown agents, or classifies the optional helper incorrectly.
- Runtime discovery is unavailable and the bounded official-ledger availability probe is unavailable, fails, or returns an insufficient result.
- A candidate route changes any non-route treatment field: instructions, tools, skills, MCP bindings, sandbox, mutation policy, or output contract.
- A strict override is requested while one required agent lacks the override model, effort, or capability support.
- A helper override is incompatible but the no-helper continuation is not validated.
- Destination path, parent directory, or target file is unsafe, non-regular, symlinked, or changes between planning, write, verification, and rollback.
- A previous helper file is same-named but user-modified or lacks recognized managed-file proof.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Route-aware mode MUST activate only when the request supplies a trusted, versioned, schema-valid route-policy manifest path.
- **FR-002**: Requests without a route-policy manifest MUST preserve the existing static install behavior and MUST NOT perform capability discovery, route-policy evaluation, optional-helper omission, or strict override validation.
- **FR-003**: The bundled Codex source inventory MUST remain strict at exactly 13 TOML files before route-aware or static destination planning proceeds.
- **FR-004**: Route-aware destination planning MUST treat exactly 12 agents as required: `analyze-executor`, `artifact-author`, `checklist-executor`, `clarify-executor`, `codebase-analyst`, `domain-researcher`, `implement-executor`, `phase-executor`, `spec-context-analyst`, `sweep-analyst`, `sweep-classifier`, and `uat-runbook-author`.
- **FR-005**: Route-aware destination planning MUST treat `autopilot-fast-helper` as the only optional helper.
- **FR-006**: Helper optionality MUST apply only to destination planning and MUST NOT allow the bundled helper TOML to be absent from source inventory validation.
- **FR-007**: Route-aware mode MUST capture exactly one fresh runtime capability snapshot at invocation start and bind every per-agent resolution in the batch to that snapshot.
- **FR-008**: Runtime capability observation MUST enter through one runner-owned adapter boundary that can be deterministically injected for tests.
- **FR-009**: When native discovery is unavailable, route-aware resolution MUST use only the bounded availability probe path allowed for the candidate by trusted evidence in the manifest.
- **FR-010**: Each required-agent route resolution MUST evaluate the preferred route followed by ordered fallbacks and record every attempted route and rejection reason.
- **FR-011**: A required-agent route MUST resolve only when model, explicit model reasoning effort, required capabilities, runtime availability, and exact materialized treatment are all valid for that agent policy.
- **FR-012**: Route-aware mode MUST never infer a model or effort from bundled TOML defaults, parent configuration, generic substitution, adjacent agent routes, or omitted policy fields.
- **FR-013**: The materialization proof MUST bind the original source TOML bytes while rendering the selected explicit model and effort into destination bytes.
- **FR-014**: The materialization proof MUST prove all non-route fields unchanged, including instructions, tools, skills, MCP bindings, sandbox, mutation policy, and output contract.
- **FR-015**: The response MUST include a top-level routing block containing the batch snapshot, per-agent route resolution IDs, resolved agent policy IDs, attempted routes, rejection reasons, optional-helper decision, strict-override status, and recovery or mutation evidence.
- **FR-016**: Low-level mutation records MUST remain mechanical file-operation evidence and MUST NOT be the only place where routing policy evidence is reported.
- **FR-017**: Route-aware apply MUST resolve, materialize, and verify the complete required batch before any destination write or optional-helper removal occurs.
- **FR-018**: If any required agent has no safe route, route-aware apply MUST perform zero writes and zero removals while still returning complete required-agent diagnostics.
- **FR-019**: A strict global model override MUST apply to every required agent, preserve each required effort and non-route contract, validate every required tuple before mutation, and reject the batch if any required tuple is incompatible or unresolved.
- **FR-020**: Required-agent strict override failure MUST NOT fall back silently to another route.
- **FR-021**: A strict global model override MUST apply to the optional helper only when a compatible helper tuple exists.
- **FR-022**: If the helper override is incompatible and a validated no-helper continuation exists, route-aware planning MUST prefer the no-helper path instead of selecting another helper route.
- **FR-023**: An unavailable optional helper MUST NOT fail the required roster when all required agents resolve and the no-helper path is validated.
- **FR-024**: Route-aware apply MUST remove an existing helper file only when trusted install provenance or a known rendered-byte match proves plugin ownership.
- **FR-025**: If helper ownership cannot be proven, route-aware apply MUST preserve the helper file and return manual-remediation evidence.
- **FR-026**: All destination writes and managed-helper removals in route-aware apply MUST run as one rollback-backed batch that restores prior bytes and modes on failure where restoration is possible.
- **FR-027**: Filesystem, verification, or rollback failures MUST return structured recovery evidence identifying staged, applied, rolled-back, cleanup, failed, and manual-remediation actions.
- **FR-028**: G56R-006 acceptance MUST use deterministic injected discovery/probe fixtures and fake-home state proofs only.
- **FR-029**: G56R-006 MUST record that downstream G56R-007 through G56R-011 roster reconciliation remains unresolved before final composition.

### Reviewability Notes *(if applicable)*

- This feature is a framework slice. It exercises the current complete roster and policy contracts without qualifying any production route.
- Route-aware installation is explicitly activated by manifest input; default route-aware activation remains later integration work.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: seed/config and tests
- **Projected reviewable LOC**: 385
- **Projected production files**: Approximately 4
- **Projected total files**: Approximately 10
- **Budget result**: within budget
- **Split decision**: Keep one vertical resolver/materializer/installer policy slice because the approved estimator returned one suggested slice and status `ok`; downstream route qualification remains separate.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Route Policy Manifest**: Trusted versioned input that declares the closed roster, each agent policy, preferred route, ordered fallbacks, strict override state, helper state, provenance, and validation identity.
- **Runtime Capability Snapshot**: One fresh batch observation containing the runtime capability facts used for every route decision in the installation request.
- **Route Resolution Record**: Ordered per-agent evidence that identifies attempted routes, rejection reasons, selected route if any, snapshot binding, and terminal outcome.
- **Resolved Agent Policy Record**: Per-agent identity for the exact destination content and selected effective route after resolution and materialization.
- **Materialization Proof**: Byte-level proof binding original source TOML bytes to rendered destination TOML bytes while proving non-route policy fields unchanged.
- **Optional Helper Decision**: Batch-level decision that records helper install, no-helper continuation, managed removal, preservation, or manual remediation.
- **Recovery Record**: Filesystem preservation evidence for pre-state, final state, staged actions, applied actions, rolled-back actions, cleanup actions, rollback outcome, writes-state flag, and manual remediation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In deterministic dry-run fixtures where all required routes are available, 100% of required agents have route resolution records, resolved policy records, and materialization proofs before any planned write is reported.
- **SC-002**: In deterministic apply fixtures where all required routes are available, destination verification reports all 12 required agents present with expected bytes and no bundled-source file changed.
- **SC-003**: In no-manifest fixtures, 100% of static compatibility responses preserve the existing static install destination roster and omit route-aware evidence fields that require a manifest.
- **SC-004**: In strict override fixtures with any incompatible required tuple, 100% of runs return complete diagnostics for all required agents and perform zero writes or removals.
- **SC-005**: In optional-helper-unavailable fixtures, 100% of runs either omit the helper, remove it with managed-file proof, or preserve it with manual-remediation evidence without failing a fully resolved required roster.
- **SC-006**: In required-route-miss fixtures, 100% of runs report every required-agent attempt and preserve the previous known-good installation through zero-write behavior.
- **SC-007**: In filesystem-failure fixtures after mutation begins, 100% of successful rollback cases restore prior bytes and modes and report rollback evidence.
- **SC-008**: In rollback-failure fixtures, 100% of responses identify the unrestored actions, mark the state as changed or uncertain, and avoid reporting verification success.
- **SC-009**: All G56R-006 acceptance evidence is produced by deterministic fixtures and fake-home tests, with zero live model calls and zero real-user-home mutations.

## Assumptions

- The Design Concept decisions Q1 through Q14 are binding for this specification.
- The current bundled source inventory is the 13 TOML files under the Codex agent source directory; `autopilot-fast-helper` is the sole optional destination helper.
- The current static install path remains supported until a later integration specification changes the default activation model.
- G56R-005 contracts provide the fallback, strict override, helper, terminal outcome, and recovery vocabulary that this framework slice adapts into installation evidence.
- G56R-003 canonical materialization remains the source-binding authority and is extended rather than replaced.
- Final preferred routes, fallback order qualification, final aggregates, route-policy cohort expansion, live route UAT, real-home mutation, Claude installation, payload release integration, per-agent overrides, and arbitrary effort maps are out of scope.

## Open Questions

- Downstream G56R-007 through G56R-011 still need roster reconciliation before final composition because the current installer has 12 required agents plus one optional helper while older downstream cohort planning referenced an 11-agent final cohort.
