# Feature Specification: Capability Discovery, Telemetry Profile, and Exact-Treatment Contract

**Feature Branch**: `g56r-002-capability-discovery-telemetry`

**Created**: 2026-07-16

**Status**: Draft

**Input**: User description: "Freeze a source-bound executable Codex model/effort candidate set for a pinned build and define trustworthy, null-preserving telemetry, route-resolution, and exact-treatment contracts before G56R-003 performs outcome-bearing evaluation."

## Evidence Basis

- Current Codex app-server documentation establishes that
  [`model/list`](https://learn.chatgpt.com/docs/app-server#list-models-modellist)
  returns available model entries with supported and default reasoning effort,
  hidden status, and other selector metadata. Hidden entries require
  `includeHidden: true`; discovery remains runtime evidence rather than
  candidate authority.
- The same app-server documentation identifies
  `modelProvider/capabilities/read` as the method for reading provider
  capability bounds. Because the published page does not define a complete
  response contract, any collected fields require pinned-build evidence and
  explicit telemetry classification.
- Current turn-event documentation defines
  [`model/rerouted`](https://learn.chatgpt.com/docs/app-server#turn-events) as
  `{ threadId, turnId, fromModel, toModel, reason }` when the service routes a
  request to another model. Absence of an observed event is not proof that no
  reroute occurred unless the pinned telemetry profile establishes that claim.
- The direct
  [GPT-5.6 prompting guide](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6.md)
  can support only API-surface prompt-treatment claims. It cannot establish
  Codex custom-agent fields, runtime availability, defaults, telemetry, or
  exact treatment.

## Clarifications

### Session 2026-07-16 — Surface Matrix and Candidate Freeze

- **Q: What exact identity proves all three observations came from one pinned
  Codex build?** **A:** Every observation references one `client_identity_id`
  derived from the reported client version plus an immutable vendor build ID.
  When the client exposes no immutable build ID, the SHA-256 of the resolved
  executable or application package is the build ID. A missing or unequal
  identity prevents a shared matrix.
- **Q: What deterministic collection contract applies to each surface?**
  **A:** Each surface uses a predeclared, versioned collection method with fixed
  inputs and configuration. App-server collection uses initialization followed
  by documented `model/list` with `includeHidden: true` and documented provider
  capability discovery. CLI and picker collection performs the complete
  non-mutating selector enumeration available to a clean pinned-client session.
  Each method retains the ordered raw capture or its content hash. An incomplete
  or irreproducible collection is `unknown`; missing values are never inferred.
- **Q: What normalization key and disagreement record are authoritative?**
  **A:** Surfaces join only on `(official-ledger canonical model ID, canonical
  effort token)`. Raw labels are always retained. An alias is usable only
  through a versioned one-to-one mapping supported by field-level official
  documentation or a machine-readable identifier exposed by the same pinned
  build. A disagreement record preserves every surface value and evidence
  reference, the proposed normalized key, disagreement class, and tuple
  disposition without choosing a winning surface.
- **Q: When is picker omission of a hidden model consistent rather than a
  contradiction?** **A:** Hidden status is an explicit visibility state. Picker
  omission is consistent only when app-server reports `hidden: true` and the
  picker collection method proves complete enumeration under its recorded
  visibility rules. Independent current-ledger admission and all other required
  evidence remain necessary; otherwise the affected tuple is `unknown` and
  excluded.
- **Q: What causes snapshot-wide invalidity?** **A:** Only an absent or invalid
  matrix version, an unprovable shared `client_identity_id`, a failed aggregate
  integrity hash, or ambiguous or duplicate normalization keys that prevent
  tuple attribution invalidates the aggregate. Missing fields, unavailable
  surfaces, hidden status, and ordinary disagreements remain tuple-local
  exclusions, even when every tuple is excluded.
- **Q: What makes a candidate freeze immutable?** **A:** A freeze is append-only
  and content-addressed over its schema version, client identity, current-ledger
  digest, surface-matrix digest, and complete tuple-decision digest. Any source,
  build, evidence, normalization, or disposition change creates a successor
  freeze ID; a published freeze is never edited.

### Session 2026-07-16 — Telemetry and Exact Treatment

- **Q: What is the atomic telemetry-profile entry and closed field inventory?**
  **A:** Each entry is keyed by `(client_identity_id, surface, field_path)`.
  The inventory contains every discovery, assignment, route-resolution,
  service-reroute, resource, parent-child, and terminal field required by
  [FR-002] and [FR-006]. Classifications never inherit across surfaces. An
  omitted entry is `undocumented` and cannot support treatment.
- **Q: What claims may each telemetry classification support?** **A:**
  `stable_native` requires a documented field-level contract and supports only
  observed values within its completeness rule. `experimental_native` is
  documented but unstable and supports only pinned-build observations.
  `derived_from_controlled_configuration` requires deterministic, hash-bound
  configuration evidence and supports requested or assigned intent only.
  `conditional` supports only a documented condition-bound claim when its
  predicate is met; absence is unknown without a completeness guarantee.
  `unavailable` has no collectable pinned-surface value, `not_applicable` has an
  explicit false applicability predicate, and both remain null. `undocumented`
  may retain evidence but supports no platform or treatment claim.
- **Q: What makes configured-route proof approved?** **A:** It is
  content-addressed evidence that the launched client consumed the exact
  materialized configuration for the named agent, explicit model and effort,
  candidate and agent-contract IDs, instruction and configuration hashes,
  client identity, controlled overrides, and launch. The telemetry profile must
  approve this proof path and reroute monitoring must be complete. It proves
  requested assignment only, never an undocumented effective model or effort.
- **Q: What qualifies as effective-route evidence and complete reroute
  monitoring?** **A:** An effective model or effort is claimable only through a
  profile entry with field-level official support whose completeness rule is
  satisfied. A documented `model/rerouted` event proves only its observed
  `threadId`, `turnId`, `fromModel`, `toModel`, and `reason`; it proves neither
  effort, named-agent identity, nor absence of another reroute. Monitoring is
  complete only when the pinned-surface contract guarantees coverage and the
  capture spans the associated run through terminal state without gaps.
  Otherwise treatment is `unknown`.
- **Q: How are resolver fallback and service reroute kept distinct?** **A:**
  Records preserve separate immutable fields for the preferred route,
  resolver-selected assigned route, requested model and effort, observed
  service-reroute events, and supported effective destination. Resolver fallback
  occurs before assignment and owns the fallback index and reason. A service
  reroute occurs after assignment, never rewrites resolver evidence, and makes
  the requested route non-scorable. Events join by pinned surface plus
  `threadId` and `turnId`; ambiguous or conflicting joins hard-fail treatment.
- **Q: How are null, missing, unavailable, and unknown represented?** **A:** A
  typed value is stored separately from its observation state and evidence.
  `observed_value`, `explicit_null`, `missing`, `unavailable`,
  `not_applicable`, and `undocumented` remain distinct states and are never
  coerced to zero, false, a configured value, or the string `unknown`.
  `Unknown` is the knowledge or treatment disposition produced by missing or
  incomplete required evidence and causes tuple-local exclusion.

### Session 2026-07-16 — Probe Bounds and Evidence Retention

- **Q: What exact canary execution envelope applies?** **A:** Permit one launch
  per `(runtime_capability_snapshot_id, canonical_model_id, canonical_effort)`
  with a 30-second wall-clock timeout and 64 KiB combined-output cap. Crossing
  either bound requires the approved executor to kill its process tree. The
  repository adapter validates an injected `CanaryExecutor` contract and fails
  closed as `unknown` when no approved platform executor is supplied; default
  tests never launch a process. Approval comes only from a versioned,
  repository-owned allowlist that is empty in this slice; an external result
  cannot self-approve. The closed result envelope binds the executor and result
  digests, contract version, timeout/output-cap acknowledgements,
  process-tree-termination state, and zero retry count. There is no retry within
  a snapshot. An independently proven transient condition requires a successor
  snapshot. Only an exit-zero response matching
  the predeclared sentinel can record pinned-environment availability, and it
  still cannot establish support, effort support, eligibility, quality, or
  preference.
- **Q: What terminal error taxonomy is required?** **A:** Use `timeout`,
  `output_cap_exceeded`, `launch_error`, `transport_error`,
  `authentication_error`, `rate_limited`, `malformed_response`,
  `explicit_rejection`, `service_reroute`, or `ambiguous_error`. Every error
  produces the `unknown` disposition and tuple-local exclusion; none proves
  support or non-support.
- **Q: What is the redaction contract?** **A:** A deny-by-default sanitizer
  removes credentials, headers, cookies, prompt or user content, account
  identifiers, hostnames, absolute paths, and repository remotes. Required
  joins use deterministic fixture-local pseudonyms generated only at explicitly
  declared schema field paths; caller-supplied `fixture-*` values never create a
  trust exception. Only schema-allowlisted fields may enter a committed fixture.
- **Q: How is source-body visibility established without a browser renderer?**
  **A:** Every captured body must declare `normalized_plain_text`; raw HTML and
  angle-bracket markup are rejected. The adapter collapses only whitespace that
  already exists in those plain-text bytes and never infers browser rendering,
  CSS visibility, intrinsic element state, or text-node separators.
- **Q: What exactly does the aggregate source-capture digest identify?**
  **A:** The 22 closed capture rows are sorted by source ID and encoded as
  canonical JSON plus one trailing newline. Normalization and raw revalidation
  both recompute that identity; a stored or caller-supplied digest is never
  accepted on syntax or cross-row agreement alone.
- **Q: Where and how long is raw evidence retained?** **A:** `raw_evidence_root`
  is a required content-addressed location outside the repository. Directories
  are operator-only mode `0700`; files are mode `0600` and have exactly one hard
  link. Captures remain for 30 days after trusted retention registration. An
  immutable publication intent makes its exact record set governing before
  output begins, and a matching receipt proves completion only after the exact
  freeze bytes exist. Claims left before intent remain non-governing, expire
  one day after trusted registration, and cannot be promoted after expiry;
  deletion uses the latest governing or individually capped pending deadline. A
  shared parent-directory advisory lock is acquired before any reserved
  `.capability-evidence-write-*` temporary pathname appears and is held through
  writer commit or recovery.
  The temporary lock then proves no writer remains: a single-link
  pre-publication file is discarded,
  while a linked file additionally requires exact descriptor-bound target,
  inode, and byte proof. Concurrent identical source captures accept the
  verified single-link winner. Unknown-attempt captures use the same append-only
  publication and exact-byte concurrent-winner verification. Source and unknown
  materialization serialize with retention cleanup; any deletion intent or
  completion record permanently tombstones its evidence digest and blocks
  rematerialization. If the original
  open deletion descriptor retains any link after unlink, cleanup never
  republishes the payload or rebinds a substitute inode; the durable intent
  remains fail-closed for manual investigation and cannot produce completion.
  Expired bytes are deleted while their digest and a deletion record remain. Live private-store
  operations fail closed on Windows until equivalent owner-only DACL validation
  exists. Repository tests never require raw-store access.
- **Q: How are deterministic fixtures derived and hashed?** **A:** Sanitize
  first, keep only schema-allowlisted fields, replace unstable values with fixed
  tokens, serialize canonical UTF-8 JSON with sorted keys and no insignificant
  whitespace, and compute SHA-256 over those exact bytes. Store the exact-byte
  digest in a separate committed digest manifest so replay can compare raw
  bytes before parsing without a self-referential hash. Each fixture records
  its schema and sanitizer versions, raw-evidence digest, and expected
  disposition; the manifest records its path and fixture digest.
- **Q: What constitutes synthetic replay acceptance?** **A:** Validate every
  fixture hash before parsing; replay every required success and failure class
  twice without network or raw-store access; and require identical normalized
  outputs, dispositions, and digests. Any mismatch, undeclared field, raw-data
  dependency, or canary-derived support or eligibility claim fails acceptance.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Freeze Executable Candidate Tuples [US1] (Priority: P1)

As a capability steward, I can pin one Codex build, revalidate the current
official-source ledger, compare app-server, CLI, and interactive-picker
observations without collapsing disagreements, and freeze only source-admitted
model/effort tuples with supported availability and consistent surface evidence.

**Why this priority**: G56R-003 cannot evaluate routes until the executable
candidate set is bounded by current documentation and verified for the tested
environment.

**Independent Test**: Supply a current source ledger and sanitized surface
observations containing admitted, hidden, mismatched, and unavailable tuples.
The resulting freeze retains all evidence, admits only eligible tuples, and
records tuple-local exclusion reasons for every other tuple.

**Acceptance Scenarios**:

1. **Given** all 22 current `OPENAI-DOC-*` records and a pinned client identity,
   **When** the steward refreshes the ledger, **Then** every current record has
   a revalidation outcome and any body-identity change invalidates every claim
   bound to that source
   without consuming or rewriting historical `OSL-*` rows.
2. **Given** a source-admitted model and surface observations from the same
   pinned build, **When** app-server, CLI, and picker evidence agree on an
   available model/effort tuple, **Then** the tuple is eligible for the frozen
   executable set with all source and runtime bindings preserved.
3. **Given** a hidden entry without independent current-ledger admission,
   **When** the surface matrix is evaluated, **Then** the observation is
   retained as evidence and the tuple is excluded.
4. **Given** one tuple with contradictory or unknown surface evidence,
   **When** the freeze is produced, **Then** only that tuple is excluded and
   unrelated valid tuples remain eligible.
5. **Given** documented discovery is unavailable for a source-admitted tuple,
   **When** the approved canary path is used, **Then** no more than one bounded,
   non-scored attempt is recorded and it makes no platform-support or
   eligibility claim.

---

### User Story 2 - Prove Telemetry and Exact Treatment [US2] (Priority: P2)

As an evaluation designer, I can classify every desired telemetry field and
determine whether requested or effective treatment is proven, unknown, or
failed without inferring missing values or confusing service reroutes with
plugin-selected fallback.

**Why this priority**: Candidate availability is insufficient for valid
evaluation; every future outcome must be attributable to the intended named
agent, model, effort, configuration, and route.

**Independent Test**: Validate representative route-resolution and treatment
records with complete, partial, null, misdelivered, and rerouted evidence. Each
record receives a deterministic treatment disposition and preserves every
unsupported value as null or unknown.

**Acceptance Scenarios**:

1. **Given** a desired telemetry field, **When** its profile entry is reviewed,
   **Then** it names one allowed classification, its source, completeness rule,
   and permitted claims.
2. **Given** requested configuration plus an approved configured-route proof and
   reroute monitoring, **When** the profile permits that proof, **Then** the
   requested assignment may be accepted without asserting an undocumented
   returned or effective value.
3. **Given** missing effective-treatment or reroute evidence, **When** the tuple
   is evaluated, **Then** treatment is `unknown` and the tuple is excluded
   rather than assumed successful.
4. **Given** a service reroute to a destination prequalified for the same named
   agent, **When** runtime UAT continues, **Then** the run remains non-scorable
   as the requested route and records the service reroute separately from
   resolver fallback.
5. **Given** an unapproved, unidentifiable, unknown, or different-agent reroute,
   **When** treatment is evaluated, **Then** the run hard-fails treatment.

---

### User Story 3 - Replay Sanitized Evidence [US3] (Priority: P3)

As a test author, I can replay sanitized, deterministic capability and treatment
records for success and failure states before any live corpus run, while raw
live responses remain outside Git.

**Why this priority**: Deterministic replay makes the discovery and treatment
rules reviewable and prevents later evaluation from depending on live,
sensitive, or unstable responses.

**Independent Test**: Run the replay suite twice against the committed fixtures.
Both runs produce identical dispositions for success, null, unavailable,
misdelivery, reroute, surface-disagreement, and discovery-unavailable cases and
validate every fixture hash.

**Acceptance Scenarios**:

1. **Given** sanitized fixtures for all required cases, **When** they are
   replayed, **Then** each case produces the predeclared candidate and treatment
   disposition with explicit null behavior.
2. **Given** a raw capability response retained outside Git, **When** its
   sanitized fixture is created, **Then** the runtime snapshot carries the raw
   evidence or a content-addressed reference and the committed fixture carries
   only sanitized content and its hash.
3. **Given** a fixture whose content no longer matches its recorded hash,
   **When** replay begins, **Then** validation fails before the fixture can
   support a claim.

### Edge Cases

- A current source redirects, becomes inaccessible, changes body or locator, or
  conflicts with another current official source after the prior ledger pin.
- An app-server model list is paginated, duplicated, empty, or omits fields that
  were present in another surface observation.
- App-server, CLI, and picker use different labels for what may be the same
  model, and no approved normalization key establishes equivalence.
- A model is hidden from the picker but appears in full discovery, with or
  without independent current-ledger admission.
- A model is source-admitted but an effort value appears on only one runtime
  surface.
- Documented discovery is unavailable and the single allowed canary times out,
  exceeds its output bound, or returns an ambiguous error.
- Requested model or effort is recorded but effective model or effort is absent.
- No `model/rerouted` event is observed on a surface whose profile does not
  guarantee complete reroute reporting.
- A reroute identifies a destination model but not an approved route for the
  same named agent.
- Token categories, parent attribution, speed, retry, or compaction fields are
  absent, partially reported, or not applicable.
- Work fails, is cancelled, times out, or is abandoned after resource use but
  before acceptance.
- A content-addressed raw-evidence reference is missing, inaccessible, or does
  not match its expected digest.
- A proposed role/model binding names a model outside the canonical
  official-ledger candidate set.
- A controlled repository snapshot or task/fixture identity differs between
  discovery, assignment, and replay records.

## Requirements *(mandatory)*

### Functional Requirements

- **[FR-001] Current source authority**: Before candidate freeze, the feature
  MUST revalidate all 22 current `OPENAI-DOC-*` manifest records against the
  current canonical allowlist and record a per-record outcome. Missing,
  conflicting, inaccessible, withdrawn, or body-changed documentation MUST
  invalidate every current claim and route bound to that source. Historical
  `OSL-*` evidence MUST remain historical and MUST NOT be consumed or rewritten
  as the active ledger. The direct GPT-5.6 prompting guide MUST be bound only to
  API-surface prompt treatment and MUST NOT support Codex agent-field,
  availability, default, telemetry, or exact-treatment claims.
- **[FR-002] Versioned surface matrix and controlled identity**: The feature
  MUST create one versioned matrix aggregate containing distinct, surface-keyed
  app-server, CLI, and interactive-picker observations from the same pinned
  Codex build through the clarified `client_identity_id`. It MUST use the
  clarified versioned collection methods, normalization key, hidden visibility
  rule, disagreement record, and aggregate-invalidity boundary, and MUST
  preserve contradictory fields rather than collapse them. Every observation
  MUST bind its client/build and surface identity, method, method inputs,
  timestamp, discovered models, supported efforts, relevant capabilities, and
  raw capability evidence or an explicit content-addressed raw-evidence
  reference. Every run MUST also bind the controlled repository snapshot,
  candidate route, and task, fixture, or objective identity.
- **[FR-003] Source-admitted executable freeze**: The feature MUST use the
  documented app-server model and provider-capability discovery contracts and
  cross-check CLI and picker observations for the same pinned build. Runtime
  evidence MAY narrow availability but MUST NOT admit a model, effort, field, or
  platform behavior. Hidden entries MUST be retained and excluded absent
  independent current-ledger admission. A new role/model binding MAY be
  recorded only for a model already in the canonical official-ledger candidate
  set and MUST bind its source and agent-contract rationale. The frozen set
  MUST contain only source-admitted, availability-supported model/effort tuples
  whose required surfaces agree; mismatch or unknown evidence MUST exclude only
  the affected tuple. The published freeze MUST use the clarified append-only,
  content-addressed identity and successor rule.
- **[FR-004] Bounded fallback and evidence retention**: Only when documented
  discovery is unavailable, the feature MAY perform at most one predeclared,
  non-scored canary per clarified snapshot/model/effort key. The canary MUST
  obey the clarified 30-second timeout, 64 KiB output cap, zero-retry rule,
  process-tree termination, success criterion, and terminal error taxonomy. It
  MUST retain only redacted evidence, MUST NOT become a repeated availability
  campaign, and MUST NOT establish platform support, effort support,
  eligibility, quality, or preference. Unresolved availability MUST exclude
  the tuple. Raw live responses MUST remain outside Git under the clarified
  content-addressed retention and access contract; committed evidence MUST use
  the clarified deny-by-default sanitizer, canonical serialization, and hashes.
- **[FR-005] Telemetry profile and exact-treatment proof**: The feature MUST
  publish a versioned, surface-keyed telemetry profile that classifies every
  desired field as `stable_native`, `experimental_native`,
  `derived_from_controlled_configuration`, `conditional`, `unavailable`,
  `not_applicable`, or `undocumented`, and records the source, completeness
  rule, and permitted claims for that field. Entries MUST use the clarified
  atomic key, closed inventory, classification semantics, and typed
  value/observation-state representation. A native classification MUST have
  field-level official support for the pinned surface. Returned effort,
  effective model, speed, token categories, parent attribution, or any other
  missing value MUST NOT be fabricated. Exact treatment MUST require observed
  effective treatment or an approved configured-route proof meeting the
  clarified consumption-evidence contract and permitted by the profile plus
  complete reroute monitoring. Before publication, the successor freeze MUST
  bind a content-addressed digest of the exact retained observation,
  configured-route, and sanitized source evidence owner set; configured intent alone MUST NOT prove an
  undocumented effective value, and missing proof MUST produce the `unknown`
  disposition without replacing the typed value or observation state.
- **[FR-006] Joined route-resolution and execution-trace contract**: Every
  assigned objective MUST bind `candidate_route_id`, `agent_contract_id`,
  `runtime_capability_snapshot_id`, `route_resolution_id`,
  `experiment_policy_id`, and `execution_trace_id`. Each route-resolution
  record MUST identify preferred and effective routes, attempted routes,
  fallback index and reason, capability snapshot, and timestamp. Each
  treatment trace MUST record the named agent; explicit assigned, requested,
  and supported effective model/effort evidence; instruction hash; sandbox,
  approvals, and mutation class; expected and loaded skills, MCP, and tools;
  parent configuration; pinned client; controlled overrides; delivery canary;
  treatment failures; context; parent-child graph; complete objective-level raw
  token vector; request/turn count; wall time; retries; compaction; validation;
  cancellation; failed or abandoned work; terminal state; outcome and
  acceptance; and explicit null behavior. Resolver-selected fields, requested
  fields, service-reroute events, and supported effective fields MUST remain
  separate and immutable. Values MUST remain null when the profile does not
  permit a claim.
- **[FR-007] Service-reroute treatment**: Service rerouting MUST remain distinct
  from resolver-selected fallback. Every service-rerouted run MUST be recorded
  and MUST be non-scorable as evidence for the requested route. Runtime UAT MAY
  continue only when the destination is identifiable and already prequalified
  for the same named agent; otherwise the run MUST hard-fail treatment.
  Unapproved, unidentifiable, unknown, or different-agent reroutes MUST hard
  fail. A missing reroute observation MUST remain unknown unless the pinned
  telemetry profile establishes complete reporting for that surface. Event
  association MUST use the pinned surface plus `threadId` and `turnId`; an
  ambiguous or conflicting association MUST hard-fail treatment.
- **[FR-008] Deterministic replay and contract boundary**: Before any live
  corpus run, the feature MUST replay sanitized deterministic records covering
  success, explicit null, unavailable field, misdelivery, approved same-agent
  prequalified-destination reroute, unapproved or unidentifiable hard-fail
  reroute, surface disagreement, and unavailable discovery. Replay MUST verify
  fixture hashes and deterministic dispositions through the clarified offline
  double-replay acceptance contract. Vendor-specific collection evidence MUST
  remain identifiable while treatment and trace records retain a vendor-neutral
  contract. G56R-002 MUST NOT create a cross-vendor probing
  abstraction or define corpus execution, scoring, statistical qualification,
  ranking, preference, fallback ordering, resolver policy, installation,
  defaults, agent configuration, payload regeneration, or release claims.

### Reviewability Notes *(if applicable)*

- The capability adapter crossed the 400-LOC boundary during implementation and
  is now safely subdivided behind its stable public facade into focused source,
  observation, matrix, private I/O, retention, freeze, contract, and CLI
  modules. The facade exports exactly the supported public API and no private
  trust primitives. Every capability module remains below 400 source lines, so T001-T015
  no longer relies on a `typed_size_only` / `no_safe_boundary` exception.
- The feature remains one guarded slice with three ordered review markers:
  source/surface freeze, telemetry/treatment contracts, and sanitized replay.
  Treatment and replay remain separate; any new capability feature growth or
  cross-marker coupling must stop and re-run the reviewability gate.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: schema/data contract; sanitized fixtures and tests
- **Projected reviewable LOC**: 297, with a 265-LOC roadmap target retained where practical
- **Projected production files**: approximately 3
- **Projected total files**: approximately 10
- **Budget result**: warning accepted
- **Split decision**: Keep one guarded slice because the authoritative scaffold estimator recommends one slice; re-estimate during planning and split if the extracted change crosses a binding threshold.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, and rollback
  or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Official Source Claim**: One current `OPENAI-DOC-*` record and its canonical
  source, documented facts, claim bindings, refresh outcome, gaps, and
  invalidation triggers. Historical `OSL-*` rows are not current instances.
- **Surface Matrix**: Versioned aggregate for one pinned build that preserves
  separate app-server, CLI, and picker observations and their normalization or
  disagreement status.
- **Runtime Capability Snapshot**: Surface-keyed environment observation with
  models, efforts, relevant capabilities, method, timestamp, and raw evidence
  or a content-addressed external reference; never candidate authority.
- **Executable Candidate Tuple**: A source-admitted named-agent/model/effort
  binding joined to its contract, capability snapshot, availability decision,
  and tuple-local inclusion or exclusion reason.
- **Telemetry Profile**: Versioned surface contract that classifies each field,
  identifies its source and completeness rule, and limits the claims it may
  support.
- **Route Resolution**: Record of preferred, attempted, and effective routes,
  resolver fallback facts, capability snapshot, reason, and timestamp,
  separate from service behavior.
- **Exact-Treatment Trace**: Null-preserving record joining assignment,
  requested and supported effective route evidence, loaded treatment context,
  parent-child structure, resource observations, terminal policy, and outcome.
- **Sanitized Replay Fixture**: Deterministic, hash-bound representation of a
  success or failure case derived without committing raw live responses.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 22 current `OPENAI-DOC-*` records have a recorded refresh
  outcome before freeze, zero historical `OSL-*` rows are treated as current,
  and every invalidation is traceable to only the affected claims or routes.
- **SC-002**: One hundred percent of considered model/effort tuples have a
  source-admission decision, a surface-matrix disposition, and either supported
  availability or an explicit tuple-local exclusion; no contradictory surface
  field is silently collapsed.
- **SC-003**: One hundred percent of frozen tuples have profiled treatment proof
  and reroute evidence sufficient for their permitted claims; every tuple with
  missing proof is excluded as unknown.
- **SC-004**: One hundred percent of desired telemetry fields have an allowed
  classification, source, completeness rule, and permitted-claims statement;
  unsupported fields remain null and zero returned or effective values are
  inferred from configured intent.
- **SC-005**: Every assigned-objective replay record binds all six required IDs
  and preserves every required route, treatment, resource, terminal, and null
  field through validation.
- **SC-006**: All eight required synthetic case classes replay deterministically
  on repeated runs, including both approved-continuation and hard-fail reroute
  cases, with identical dispositions and valid fixture hashes.
- **SC-007**: Zero raw live responses are committed to Git; every committed
  fixture is sanitized and hash-bound, and every retained raw observation is
  represented in its snapshot directly or by an explicit content-addressed
  external reference.
- **SC-008**: G56R-003 receives one frozen executable-candidate handoff and one
  validated telemetry/treatment contract before any outcome-bearing corpus run,
  while G56R-002 produces no score, ranking, preference, or release claim.

## Assumptions

- The G56R-001 v3 machine manifest is the canonical candidate and source-ledger
  input and contains 22 current `OPENAI-DOC-*` records; its historical `OSL-*`
  material remains evidence only.
- G56R-001 candidates are provisional and source-bound, not yet executable or
  preferred. Runtime discovery can narrow them but cannot broaden them.
- App-server, CLI, and picker observations can differ even for one pinned build;
  an equivalence or normalization rule must be explicit before fields can join.
- Missing observations mean unknown unless a field's telemetry profile defines
  a stronger completeness guarantee.
- Raw live evidence is retained outside Git under the path, lifetime, access,
  redaction, and hashing contract to be frozen during clarification and
  planning; repository verification must not depend on access to that raw data.
- Aggregate IDs owned by later roadmap specs remain null until those aggregates
  exist.
- G56R-003 owns corpus design, execution, scoring, qualification, and statistical
  analysis; G56R-002 supplies only the frozen candidate and evidence contracts.
- Planning and implementation remain subject to the repository constitution,
  existing project tooling, and the one-slice reviewability gate.
