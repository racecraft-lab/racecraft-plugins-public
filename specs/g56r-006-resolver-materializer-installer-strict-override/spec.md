# Feature Specification: Capability-aware Resolver, Materializer, Installer, and Strict Override

**Feature Branch**: `g56r-006-resolver-materializer-installer-strict-override`

**Created**: 2026-08-24

**Status**: Draft

**Input**: User description: "Create G56R-006: Capability-aware Resolver, Materializer, Installer, and Strict Override."

## Clarifications

### Session 2026-08-24 — Roster and Cross-spec Boundary

- Q: Which no-manifest behavior is the compatibility baseline? → A: The current Python installer's route-agnostic 13-file destination copy/verify behavior; the older 10-file prose list is stale documentation, not runtime authority.
- Q: What does route success mean inside this framework slice? → A: Manifest-admitted, compatible, snapshot-bound, and exactly materialized; production route qualification remains in G56R-007 through G56R-010.
- Q: How is the manifest roster shaped? → A: Exactly 12 required-agent policies plus an explicit `autopilot-fast-helper` policy/no-helper state, independent of the strict 13-TOML source inventory check.
- Q: How is the downstream 11-agent mismatch recorded? → A: Name the affected existing and proposed roles as reconciliation inputs, but leave cohort assignment and final counts to downstream specs before G56R-011 composition.
- Q: What route evidence appears in static mode? → A: No policy-dependent top-level routing block; existing mechanical mutation and verification evidence remains unchanged.

### Session 2026-08-24 — Resolution and Override Semantics

- Q: What happens after one required agent has no safe route? → A: Continue the bounded read-only pass in stable canonical roster order until all 12 required agents have complete preferred-then-fallback attempt evidence; the miss is terminal for mutation, not diagnostics.
- Q: How do bounded probes relate to the one-batch snapshot? → A: Every required and helper resolution cites one invocation snapshot ID; a manifest-admitted bounded probe may enrich that same snapshot as child evidence only when native discovery is unavailable, without recapturing or widening route authority.
- Q: What route list applies under a strict global override? → A: Evaluate exactly one override-derived tuple per required agent while preserving that agent's explicit effort and non-route contract; never walk preferred or fallback routes after an override miss, but complete read-only override diagnostics for all 12 required agents.
- Q: What happens when the helper override is incompatible? → A: Choose the no-helper path only when that continuation is validated; otherwise fail the whole route-aware batch before mutation. Never select another helper fallback after an explicit override miss.
- Q: What does zero-write mean after a required-agent miss? → A: Dry-run and apply report zero planned or applied destination writes, zero helper removals, `writes_state=false`, and no restart requirement; only read-only routing diagnostics and no-mutation recovery evidence may be populated.

### Session 2026-08-24 — State, Ownership, and Evidence

- Q: What proves an existing helper is plugin-managed and removable? → A: Either a trusted runner-owned install provenance record binds the destination path, installer, source roster, manifest/policy, materialization, and destination digest identities, or the existing bytes exactly match a known rendered helper digest derived from the current trusted source and manifest. Filename or parsed-TOML similarity is never sufficient.
- Q: What makes a route-policy manifest trusted? → A: The resolved manifest path must yield a closed, supported-version, schema-valid document with manifest and provenance identities, a digest binding the current strict 13-TOML source roster, exactly 12 required policies plus explicit helper/no-helper state, and only manifest-admitted candidates and bounded probes. Inline policy objects and inferred bundled defaults do not activate route-aware mode.
- Q: What static response and restart behavior remain compatible? → A: No-manifest responses preserve the current 13-file installer fields and mechanical evidence, omit `routing`, and set `restart_required=false` for dry-run, no-op apply, pre-mutation failure, or successful rollback; restart is required only after a destination state change or when restoration cannot be proven.
- Q: What proves successful rollback? → A: Capture prior bytes and file modes for every planned write or managed removal; restore or remove as appropriate; prove matching pre/final state identities; report `rollback_outcome=restored` or `not_required`, `writes_state=false`, and `restart_required=false`. Any unrestored action reports changed or uncertain state, restart guidance, and bounded manual remediation without claiming verification success.
- Q: What exact policy evidence does route-aware mode return? → A: A closed top-level `routing` object contains schema/mode, manifest identity and provenance, one runtime snapshot plus child probe evidence, canonical required-agent resolution/materialization records, optional-helper decision, strict-override evidence, and recovery-or-mutation evidence; static mode has no `routing` object and low-level `mutation` remains mechanical.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Route-aware batch installation plan (Priority: P1)

As a SpecKit Pro maintainer, I need a route-aware dry-run or apply request to resolve and byte-prove every required Codex agent from one fresh capability snapshot and one trusted policy manifest, so I can review the complete installation decision before any user agent file changes.

**Why this priority**: This is the minimum viable framework slice. Without a complete required-agent plan, downstream route qualification cohorts cannot safely supply final policies.

**Independent Test**: Can be fully tested with deterministic route policies and a fake Codex agents home by running dry-run and apply requests that produce a complete required roster, byte proofs, and no bundled-source mutations.

**Acceptance Scenarios**:

1. **Given** a trusted manifest containing policies for the full current roster and an injected capability snapshot where every required route is available, **When** route-aware dry-run runs, **Then** the response includes one snapshot identity, ordered resolution records for all 12 required agents, materialization proofs for each destination file, no planned writes to bundled source files, and the optional helper state.
2. **Given** the same manifest and snapshot, **When** route-aware apply runs against a fake home with missing or stale required agents, **Then** all required destination TOMLs are installed only after every required agent resolves and materializes successfully, and post-apply verification reports the complete required roster.
3. **Given** no trusted route-policy manifest input, **When** the existing install request runs, **Then** static compatibility mode preserves the current route-agnostic 13-file destination copy/verify behavior, omits the policy-dependent top-level routing block, and does not attempt capability discovery, route resolution, optional-helper omission, or strict override validation.

---

### User Story 2 - Strict global override validation (Priority: P1)

As a maintainer testing a global model override, I need the override to validate the complete required set before mutation and to handle the optional helper according to the approved Q8 rule, so a single incompatible tuple cannot silently fall back or partially install.

**Why this priority**: The override changes the selected route for many agents at once. It must fail closed for required agents and preserve helper optionality without weakening the required roster.

**Independent Test**: Can be fully tested with deterministic manifests that include compatible and incompatible required-agent tuples plus compatible and incompatible helper tuples.

**Acceptance Scenarios**:

1. **Given** a strict global override whose model is compatible with every required agent while preserving each required effort and non-route contract, **When** route-aware dry-run runs, **Then** every required resolution record uses the override route, no required fallback route is selected, and mutation remains blocked until the full batch proof succeeds.
2. **Given** a strict global override where one required agent has no compatible tuple, **When** route-aware dry-run or apply runs, **Then** exactly one override-derived tuple is evaluated for each required agent, every required agent is still evaluated for diagnostics, the response marks the required miss, no destination write or helper removal is planned or applied, `writes_state=false`, no restart is required, and no required agent falls back to another route.
3. **Given** a strict global override with a compatible helper tuple, **When** the helper route resolves as manifest-admitted compatible under the same batch snapshot, **Then** the helper is included in the destination plan with a resolved helper policy.
4. **Given** a strict global override with no compatible helper tuple, **When** all required agents resolve, **Then** the required install may proceed without installing a different helper route only when the no-helper continuation validates; otherwise the whole batch fails before mutation.

---

### User Story 3 - Optional helper omitted or removed safely (Priority: P2)

As a maintainer preserving user-owned agent files, I need an unavailable optional helper to be omitted or removed only when plugin ownership is proven, so required installation can succeed without deleting user-modified files.

**Why this priority**: The optional helper must not fail the required roster, but removal is destructive enough to require proof.

**Independent Test**: Can be fully tested with fake-home states containing no helper, a plugin-managed helper, a known rendered-byte helper, and a same-named user-modified helper.

**Acceptance Scenarios**:

1. **Given** all required agents resolve and the optional helper has no manifest-admitted compatible route, **When** no helper file exists in the fake-home destination, **Then** the route-aware response records validated no-helper continuation and the required roster installs successfully.
2. **Given** all required agents resolve, the optional helper has no manifest-admitted compatible route, and an existing helper file has a trusted provenance binding or exact known rendered-byte digest match, **When** apply runs, **Then** helper removal is planned with managed-file proof, participates in the same rollback-backed batch, and is reflected in the top-level routing evidence.
3. **Given** all required agents resolve, the optional helper has no manifest-admitted compatible route, and an existing same-named helper lacks managed-file proof, **When** dry-run or apply runs, **Then** the file is preserved, the required roster may still succeed, and the response includes manual-remediation evidence explaining why automatic removal was refused.

---

### User Story 4 - Complete failure evidence with preservation (Priority: P2)

As a maintainer diagnosing route or filesystem failures, I need complete structured evidence and preservation of the previous known-good installation, so retries are reproducible and failures do not leave partial agent state.

**Why this priority**: A route-aware installer is only safe if every failure mode is inspectable and rollback or zero-write behavior is provable.

**Independent Test**: Can be fully tested with deterministic injected route misses, discovery/probe failures, unsafe destination entries, write failures, verification failures, rollback success, and rollback failure cases in fake homes.

**Acceptance Scenarios**:

1. **Given** at least one required agent has no safe route, **When** route-aware dry-run or apply runs, **Then** the resolver completes the bounded read-only pass in stable canonical roster order for every required agent, returns all attempted routes and rejection reasons, reports zero planned or applied writes and removals with `writes_state=false` and no restart requirement, and preserves the previous known-good installation.
2. **Given** all required agents resolve but a destination write or managed-helper removal fails during apply, **When** rollback succeeds, **Then** prior bytes and file modes are restored or newly created files are removed, pre-state and final-state identities match, the response records staged, applied, rolled-back, and cleanup actions with `rollback_outcome=restored`, `writes_state=false`, and `restart_required=false`, and the failed apply does not claim verification success.
3. **Given** rollback cannot fully restore the previous known-good state, **When** apply returns, **Then** the response reports every unrestored action and error, marks `writes_state` as true or uncertain, sets `restart_required=true`, and includes bounded manual-remediation instructions without claiming verification success.

### Edge Cases

- Trusted manifest is missing, unreadable, malformed, wrong-versioned, incomplete, lacks required identity/provenance/source-roster bindings, or contains policies, candidates, or probes outside the current 12-required-plus-one-optional closed roster.
- Bundled Codex agent source inventory is missing one of the 13 TOMLs, includes unexpected TOMLs, contains legacy Markdown agents, or classifies the optional helper incorrectly.
- Runtime discovery is unavailable and the bounded official-ledger availability probe is unavailable, fails, or returns an insufficient result.
- A candidate route changes any non-route treatment field: instructions, tools, skills, MCP bindings, sandbox, mutation policy, or output contract.
- A strict override is requested while one required agent lacks the override model, effort, or capability support.
- A helper override is incompatible but the no-helper continuation is not validated.
- Destination path, parent directory, or target file is unsafe, non-regular, symlinked, or changes between planning, write, verification, and rollback.
- A previous helper file is same-named but user-modified, matches only after parsing or normalization, or lacks recognized managed-file proof.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Route-aware mode MUST activate only when the request supplies a manifest path whose resolved document has a supported version, passes a closed schema, carries manifest and provenance identities, binds the current strict 13-TOML source roster by digest, declares exactly the 12 required-agent policies plus an explicit `autopilot-fast-helper` policy/no-helper state, and admits every candidate and bounded probe used by resolution; inline policy objects and inferred bundled defaults MUST NOT activate route-aware mode.
- **FR-002**: Requests without a route-policy manifest MUST preserve the current route-agnostic 13-file static destination copy/verify behavior and response fields, including mechanical mutation and verification evidence, `agent_files`, selected static model, source, destination, `writes_state`, `mutation`, `verification`, and `restart_required`; they MUST omit the policy-dependent top-level `routing` object and MUST NOT perform capability discovery, route-policy evaluation, optional-helper omission, or strict override validation.
- **FR-003**: The bundled Codex source inventory MUST remain strict at exactly 13 TOML files before route-aware or static destination planning proceeds.
- **FR-004**: Route-aware destination planning MUST treat exactly 12 agents as required: `analyze-executor`, `artifact-author`, `checklist-executor`, `clarify-executor`, `codebase-analyst`, `domain-researcher`, `implement-executor`, `phase-executor`, `spec-context-analyst`, `sweep-analyst`, `sweep-classifier`, and `uat-runbook-author`.
- **FR-005**: Route-aware destination planning MUST treat `autopilot-fast-helper` as the only optional helper.
- **FR-006**: Helper optionality MUST apply only to destination planning and MUST NOT allow the bundled helper TOML to be absent from source inventory validation.
- **FR-007**: Route-aware mode MUST capture exactly one fresh runtime capability snapshot at invocation start, assign it one identity, and bind every required-agent and optional-helper resolution in the batch to that same identity without per-agent recapture.
- **FR-008**: Runtime capability observation MUST enter through one runner-owned adapter boundary that can be deterministically injected for tests.
- **FR-009**: When native discovery is unavailable, route-aware resolution MUST use only the bounded availability probe path allowed for the candidate by trusted evidence in the manifest, MUST record probe results as child evidence of the one batch snapshot, and MUST NOT let probes widen the manifest-admitted candidate set or create another snapshot identity.
- **FR-010**: Normal route-aware resolution MUST evaluate all 12 required agents in the stable canonical roster order from FR-004; for each agent it MUST evaluate the preferred route followed by ordered fallbacks, record every attempted route and rejection reason, and continue the bounded read-only diagnostic pass after any required miss.
- **FR-011**: A required-agent route MUST resolve only when model, explicit model reasoning effort, required capabilities, runtime availability, and exact materialized treatment are all valid for that agent policy.
- **FR-012**: Route-aware mode MUST never infer a model or effort from bundled TOML defaults, parent configuration, generic substitution, adjacent agent routes, or omitted policy fields.
- **FR-013**: The materialization proof MUST bind the original source TOML bytes while rendering the selected explicit model and effort into destination bytes.
- **FR-014**: The materialization proof MUST prove all non-route fields unchanged, including instructions, tools, skills, MCP bindings, sandbox, mutation policy, and output contract.
- **FR-015**: Each route-aware response MUST include a closed top-level `routing` object, absent in static mode, with `schema_version`; `mode=route_aware`; `manifest` containing path, manifest ID, schema version, source-roster ID, and provenance ID; `runtime_capability_snapshot` containing snapshot ID, deterministic observation evidence, and child probe results; `required_agents` in canonical order containing agent name, route-resolution ID, policy ID, resolved-agent-policy ID, materialization ID and proof, snapshot ID, attempted routes, rejection reasons, selected route or null, and terminal outcome; `optional_helper_decision` containing its state, applicable policy/resolution/resolved-policy/materialization IDs and proof or null, snapshot binding, attempts, rejections, selected route or null, terminal outcome, no-helper validation, managed-ownership proof, and manual remediation; `strict_override` containing status and evaluated-tuple evidence; and `recovery_or_mutation` containing planned/applied writes and removals, recovery record, `writes_state`, and `restart_required`.
- **FR-016**: Low-level mutation records MUST remain mechanical file-operation evidence and MUST NOT be the only place where routing policy evidence is reported.
- **FR-017**: Route-aware dry-run or apply MUST resolve, materialize, and verify the complete required batch before reporting any planned destination mutation or performing any destination write or optional-helper removal.
- **FR-018**: If any required agent has no safe route, route-aware dry-run or apply MUST report zero planned or applied destination writes, zero optional-helper removals, `writes_state=false`, and no restart requirement while still returning complete read-only diagnostics for all 12 required agents.
- **FR-019**: A strict global model override MUST evaluate exactly one override-derived tuple for every required agent, preserve each agent's explicit effort and non-route contract, complete read-only override diagnostics for all 12 required agents before returning, validate every required tuple before mutation, and reject the batch if any required tuple is incompatible or unresolved.
- **FR-020**: Required-agent strict override failure MUST NOT evaluate or select a preferred or fallback route after the override-derived tuple misses.
- **FR-021**: A strict global model override MUST apply to the optional helper only when a compatible helper tuple exists.
- **FR-022**: If the helper override is incompatible, route-aware planning MUST select the no-helper path only when that continuation validates and MUST NOT evaluate or select another helper route after the explicit override misses.
- **FR-023**: An unavailable optional helper MUST NOT fail the required roster when all required agents resolve and the no-helper path validates; if the no-helper continuation does not validate, the route-aware batch MUST fail before mutation because the helper decision remains unresolved.
- **FR-024**: Route-aware apply MUST remove an existing helper file only when either a trusted runner-owned install provenance record binds its destination path, installer identity, source-roster identity, manifest and policy identities, materialization identity, and destination digest, or its existing bytes exactly match a known rendered helper digest derived from the current trusted source and manifest.
- **FR-025**: Filename, location, syntactic TOML validity, parsed equivalence, or normalized content MUST NOT prove helper ownership; when the trusted binding or exact known rendered-byte match is absent, route-aware apply MUST preserve the helper file and return manual-remediation evidence.
- **FR-026**: All destination writes and managed-helper removals in route-aware apply MUST run as one rollback-backed batch that captures prior bytes and file modes before mutation and, on failure where restoration is possible, restores those bytes and modes or removes files newly created by the failed batch; a verified no-op or fully restored batch MUST report `writes_state=false` and `restart_required=false`, while a successful batch that changes destination state MUST report `restart_required=true`.
- **FR-027**: Filesystem, verification, or rollback failures MUST return structured recovery evidence identifying staged, applied, rolled-back, cleanup, failed, and manual-remediation actions; any pre-mutation required-route failure MUST instead report `writes_state=false`, no restart requirement, and explicit no-mutation evidence.
- **FR-028**: G56R-006 acceptance MUST use deterministic injected discovery/probe fixtures and fake-home state proofs only.
- **FR-029**: G56R-006 MUST record that downstream G56R-007 through G56R-011 roster reconciliation remains unresolved before final composition and MUST name `artifact-author`, `sweep-analyst`, `sweep-classifier`, and the proposed `consensus-synthesizer` and `gate-validator` as reconciliation inputs without assigning their downstream cohorts here.

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

- **Route Policy Manifest**: Closed, supported-version input loaded only from an explicit path; it carries manifest and provenance identities, binds the current strict 13-TOML source roster by digest, declares exactly 12 required-agent policies separately from the explicit `autopilot-fast-helper` policy/no-helper state, and admits every preferred route, ordered fallback, strict override state, and bounded probe.
- **Runtime Capability Snapshot**: One fresh batch observation with one identity containing the runtime capability facts used for every required and helper route decision; any bounded manifest-admitted probe is child evidence of this same observation rather than a new snapshot.
- **Route Resolution Record**: Stable canonical per-agent evidence that identifies preferred-then-fallback attempts in normal mode or the sole override-derived attempt in strict mode, rejection reasons, selected route if any, batch snapshot binding, and terminal outcome; records remain complete for all 12 required agents after any required miss.
- **Resolved Agent Policy Record**: Per-agent identity for the exact destination content and selected effective route after resolution and materialization.
- **Materialization Proof**: Byte-level proof binding original source TOML bytes to rendered destination TOML bytes while proving non-route policy fields unchanged.
- **Optional Helper Decision**: Batch-level decision that records helper install with its policy, resolution, resolved-policy, materialization, and snapshot identities and proof; validated no-helper continuation; managed removal with its trusted provenance binding or exact known rendered-byte digest proof; preservation; manual remediation; or a pre-mutation failure when neither the explicit helper override nor no-helper continuation validates.
- **Recovery Record**: Filesystem preservation evidence for pre-state and final-state identities, captured prior bytes and modes, staged actions, applied actions, rolled-back actions, cleanup actions and errors, rollback outcome, writes-state flag, restart requirement, and bounded manual remediation.
- **Routing Evidence**: The closed top-level route-aware response object defined by FR-015; it owns policy decisions and identity joins while the sibling low-level `mutation` evidence remains purely mechanical.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In deterministic dry-run fixtures where all required routes are available, 100% of required agents have route resolution records, resolved policy records, and materialization proofs before any planned write is reported.
- **SC-002**: In deterministic apply fixtures where all required routes are available, destination verification reports all 12 required agents present with expected bytes and no bundled-source file changed.
- **SC-003**: In no-manifest fixtures, 100% of static compatibility responses preserve the current route-agnostic 13-file static destination roster and omit the policy-dependent top-level routing block.
- **SC-004**: In strict override fixtures with any incompatible required tuple, 100% of runs evaluate only the override-derived tuple for each required agent, return complete diagnostics for all 12 required agents, report zero planned or applied writes and removals with `writes_state=false`, and require no restart.
- **SC-005**: In optional-helper-unavailable fixtures, 100% of runs either omit the helper, remove it with managed-file proof, or preserve it with manual-remediation evidence without failing a fully resolved required roster.
- **SC-006**: In required-route-miss fixtures, 100% of runs report every required-agent attempt in stable canonical roster order and preserve the previous known-good installation through zero planned or applied mutations, `writes_state=false`, and no restart requirement.
- **SC-007**: In filesystem-failure fixtures after mutation begins, 100% of successful rollback cases restore prior bytes and modes or remove newly created files, prove matching pre-state and final-state identities, report `rollback_outcome=restored`, `writes_state=false`, and `restart_required=false`, and avoid claiming verification success for the failed apply.
- **SC-008**: In rollback-failure fixtures, 100% of responses identify every unrestored action and error, mark `writes_state` as true or uncertain, set `restart_required=true`, include bounded manual remediation, and avoid reporting verification success.
- **SC-009**: All G56R-006 acceptance evidence is produced by deterministic fixtures and fake-home tests, with zero live model calls and zero real-user-home mutations.

## Assumptions

- The Design Concept decisions Q1 through Q14 are binding for this specification.
- The current bundled source inventory is the 13 TOML files under the Codex agent source directory; `autopilot-fast-helper` is the sole optional destination helper.
- The current static install path remains supported until a later integration specification changes the default activation model.
- G56R-006 compatibility proves only that a manifest-admitted route is structurally compatible, snapshot-bound, and exactly materialized; it does not qualify any production route.
- G56R-005 contracts provide the fallback, strict override, helper, terminal outcome, and recovery vocabulary that this framework slice adapts into installation evidence.
- G56R-003 canonical materialization remains the source-binding authority and is extended rather than replaced.
- Final preferred routes, fallback order qualification, final aggregates, route-policy cohort expansion, live route UAT, real-home mutation, Claude installation, payload release integration, per-agent overrides, and arbitrary effort maps are out of scope.

## Open Questions

- Downstream G56R-007 through G56R-011 still need roster reconciliation before final composition because the current installer has 12 required agents plus one optional helper while older downstream cohort planning referenced an 11-agent final cohort. The reconciliation inputs are `artifact-author`, `sweep-analyst`, `sweep-classifier`, and the proposed `consensus-synthesizer` and `gate-validator`; G56R-006 does not assign those roles to cohorts or change final aggregate counts.
