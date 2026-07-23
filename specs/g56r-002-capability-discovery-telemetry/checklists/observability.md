# Observability Checklist: G56R-002 Telemetry and Treatment

**Purpose**: Validate that every observable has a source, classification, completeness boundary, supported claim, and explicit missing-value behavior.
**Created**: 2026-07-16
**Feature**: [spec.md](../spec.md)

## Telemetry Profile Coverage

- [x] CHK001 Is every discovery, assignment, route-resolution, service-reroute, resource, parent-child, and terminal field included in a closed telemetry inventory? [Completeness, Spec §Clarifications Session 2; Data Model §TelemetryProfileEntry]
- [x] CHK002 Is every profile entry keyed by `client_identity_id`, surface, and field path? [Identity, Spec §Clarifications Session 2]
- [x] CHK003 Does every entry record classification, official source or null, condition, completeness rule, permitted claims, and prohibited claims? [Traceability, Treatment Record Schema §telemetryProfileEntry]
- [x] CHK004 Are classifications prohibited from inheriting across app-server, CLI, and picker surfaces? [Isolation, Spec §Clarifications Session 2]
- [x] CHK005 Does an omitted field become `undocumented` and support no treatment or platform claim? [Fail closed, Spec §FR-005]
- [x] CHK006 Are `stable_native` and `experimental_native` limited to fields with current field-level official documentation? [Authority, Research §Telemetry Classification Semantics]
- [x] CHK007 Is controlled configuration limited to requested/assigned intent, with conditional absence unknown unless completeness is guaranteed? [Claim boundary, Spec §Clarifications Session 2]
- [x] CHK008 Do unavailable and not-applicable fields remain typed null under explicit predicates? [Null semantics, Spec §Clarifications Session 2]
- [x] CHK009 Are CLI and picker fields classified undocumented unless a new current canonical field-level source is recorded? [Authority, Research §Current Official Evidence Bindings]

## Surface and Snapshot Observability

- [x] CHK010 Does every observation expose pinned client/build identity, surface, versioned method, method-input digest, start/end timestamp, completeness state, and evidence digest/reference? [Completeness, Data Model §SurfaceObservation]
- [x] CHK011 Does app-server evidence distinguish initialization, model catalog, hidden inclusion, provider-capability reads, pagination, and completeness? [Method observability, Research §App-server method]
- [x] CHK012 Do CLI/picker observations retain raw labels, recorded visibility rules, and partial/unknown collection state? [Surface evidence, Research §CLI and picker methods]
- [x] CHK013 Are normalization map ID, raw values, proposed canonical key, disagreement class, and tuple disposition observable without a winning surface? [Disagreement visibility, Data Model §Disagreement]
- [x] CHK014 Does the snapshot bind repository revision/tree, task/fixture/objective identity, client, surface matrix, source-refresh set, and collection window? [Environment binding, Data Model §RuntimeCapabilitySnapshot]
- [x] CHK015 Are snapshot and freeze successor IDs plus publication/invalidation triggers observable? [Lifecycle, Data Model §§RuntimeCapabilitySnapshot, CandidateFreeze]

## Route and Treatment Observability

- [x] CHK016 Are preferred route, attempted routes, resolver-selected assigned route, supported effective route, fallback index/reason, snapshot, and resolution time recorded separately? [Resolution, Spec §FR-006; Data Model §RouteResolution]
- [x] CHK017 Are assigned/requested model and effort separate from profile-supported effective evidence? [Treatment distinction, Spec §FR-006]
- [x] CHK018 Does approved configured-route proof expose the exact consumed agent/model/effort, IDs, hashes, client, overrides, launch, and reroute-monitoring status? [Proof observability, Data Model §ConfiguredRouteProof]
- [x] CHK019 Are service-reroute events retained separately with documented `threadId`, `turnId`, `fromModel`, `toModel`, and `reason` fields? [Event evidence, Spec §Evidence Basis]
- [x] CHK020 Is the event association key pinned surface plus thread/turn, with ambiguity observable as a hard-fail reason? [Correlation, Spec §Clarifications Session 2]
- [x] CHK021 Is missing reroute observation unknown unless complete through-terminal capture is documented by the profile? [Absence semantics, Spec §FR-007]
- [x] CHK022 Is every service-rerouted run marked non-scorable for the requested route and classified for UAT continuation or hard failure? [Disposition, Spec §FR-007]

## Resource and Lifecycle Evidence

- [x] CHK023 Does the trace require named agent, instruction/config hashes, sandbox, approvals, mutation class, expected/loaded skills, MCP, tools, parent configuration, client, overrides, delivery canary, and treatment failures? [Treatment context, Spec §FR-006]
- [x] CHK024 Are context and parent-child graph represented without fabricating absent parent attribution? [Attribution, Spec §FR-005, FR-006]
- [x] CHK025 Are the complete raw token vector, request/turn count, and wall time retained when their profile entries permit observation? [Resource evidence, Spec §FR-006; Data Model §TreatmentTrace]
- [x] CHK026 Are retries, compaction, validation, cancellation, failed/abandoned work, terminal state, outcome, and acceptance retained through terminal policy? [Lifecycle, Spec §FR-006]
- [x] CHK027 Are returned effort, effective model, speed, token categories, parent attribution, and all other absent fields prohibited from synthesis? [Negative observability, Spec §FR-005]
- [x] CHK028 Does every field use a typed observation state and evidence reference rather than overloaded null/unknown strings? [Data quality, Data Model §ObservationValue]

## Probe and Replay Evidence

- [x] CHK029 Does each canary record its snapshot/model/effort key, attempt index, timeout, output cap, exit code, sentinel, terminal class, availability disposition, and evidence digest? [Probe observability, Data Model §CanaryResult]
- [x] CHK030 Are raw and sanitized evidence digests, schema/sanitizer versions, expected disposition, deletion record, and fixture digest observable? [Provenance, Spec §Clarifications Session 3]
- [x] CHK031 Does replay verify hashes before parsing and expose identical normalized output, disposition, and digest across two offline passes? [Determinism, Data Model §Fixture Provenance and Replay]
- [x] CHK032 Are source-refresh, snapshot, profile, freeze, route, trace, and fixture invalidation causes traceable to the exact affected claim/tuple/run? [Diagnosis, Spec §SC-001, SC-002; Plan §Evidence and Data Boundaries]

## Result

- 32 items checked.
- 0 unresolved gaps.
- No field is classified native without an explicit current official-source requirement; runtime-only CLI/picker observations remain evidence with prohibited platform claims.
