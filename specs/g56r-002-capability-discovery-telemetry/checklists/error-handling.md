# Error Handling Checklist: G56R-002 Discovery and Treatment

**Purpose**: Validate fail-closed dispositions, bounded recovery, and deterministic error evidence for discovery, probing, treatment, rerouting, and replay.
**Created**: 2026-07-16
**Feature**: [spec.md](../spec.md)

## Source and Discovery Failures

- [x] CHK001 Are inaccessible, redirected, withdrawn, changed, and conflicting official sources assigned explicit refresh states? [Completeness, Data Model §OfficialSourceRefresh]
- [x] CHK002 Does an adverse source state invalidate only bound current claims/routes and never get repaired by runtime evidence? [Fail closed, Spec §FR-001; Research §Source-Ledger Refresh Rules]
- [x] CHK003 Does a missing or stale current-ledger binding exclude the affected tuple rather than silently carrying the G56R-001 provisional claim forward? [Recovery, Spec §FR-003; Plan §Architecture and Ownership]
- [x] CHK004 Are empty, partial, duplicated, paginated, malformed, or field-omitting app-server results covered as incomplete/unknown evidence? [Edge cases, Spec §Edge Cases; Research §App-server method]
- [x] CHK005 Are partial or irreproducible CLI/picker enumerations unknown rather than complete negative evidence? [Failure semantics, Spec §Clarifications Session 1]
- [x] CHK006 Do mismatched client identities, invalid matrix versions, hash failures, and ambiguous normalization keys fail the aggregate? [Aggregate failure, Spec §Clarifications Session 1; Data Model §SurfaceMatrix]
- [x] CHK007 Do ordinary unavailable surfaces, hidden status, missing fields, and disagreements remain tuple-local exclusions even when all tuples are excluded? [Failure isolation, Spec §Clarifications Session 1]

## Canary Bounds and Terminal Taxonomy

- [x] CHK008 Is the canary unavailable unless documented discovery is unavailable for a source-admitted tuple? [Precondition, Spec §FR-004]
- [x] CHK009 Are the 30-second wall timeout and 64 KiB combined-output limit exact, with process-tree termination on either bound? [Bounded execution, Spec §Clarifications Session 3]
- [x] CHK010 Is one attempt per snapshot/model/effort enforced, with no in-snapshot retry? [Retry safety, Spec §Clarifications Session 3; Data Model §CanaryResult]
- [x] CHK011 Does a proven transient condition require a successor snapshot rather than a discretionary retry? [Recovery, Research §Canary and Raw-Evidence Decisions]
- [x] CHK012 Is the complete terminal taxonomy defined for timeout, output cap, launch, transport, authentication, rate limit, malformed response, explicit rejection, service reroute, and ambiguous error? [Completeness, Spec §Clarifications Session 3]
- [x] CHK013 Does every non-success canary terminal class yield unknown and tuple exclusion without claiming support or non-support? [Fail closed, Data Model §CanaryResult]
- [x] CHK014 Does success require exit zero plus the predeclared sentinel and still prove only pinned-environment availability? [Scope, Spec §Clarifications Session 3]

## Treatment and Misdelivery Failures

- [x] CHK015 Does absent or incomplete effective model/effort evidence yield unknown treatment instead of assuming the requested route? [Treatment failure, Spec §FR-005]
- [x] CHK016 Does failed configured-route consumption, missing hashes/IDs, or incomplete reroute monitoring reject the configured-proof path? [Evidence failure, Data Model §ConfiguredRouteProof]
- [x] CHK017 Are missing, explicit null, unavailable, not-applicable, and undocumented values kept distinct so none silently passes a mandatory field? [Null safety, Data Model §ObservationValue]
- [x] CHK018 Are expected versus loaded agent, skills, MCP, tools, sandbox, approvals, mutation class, and instruction/configuration mismatches recorded as treatment failures? [Misdelivery, Spec §FR-006; Data Model §TreatmentTrace]
- [x] CHK019 Are failed, abandoned, cancelled, validation-failed, compacted, and terminal work retained rather than dropped from resource/lifecycle evidence? [Completeness, Spec §FR-006]
- [x] CHK020 Does a required telemetry profile omission become `undocumented` and prevent treatment proof? [Fail closed, Spec §Clarifications Session 2]

## Reroute and Resolver Errors

- [x] CHK021 Does resolver fallback remain a pre-assignment record with its own attempted routes, index, and reason? [Boundary, Data Model §RouteResolution]
- [x] CHK022 Does service rerouting remain a post-assignment event that cannot rewrite resolver evidence? [Boundary, Spec §Clarifications Session 2]
- [x] CHK023 Does every service-rerouted run become non-scorable for the requested route? [Safety, Spec §FR-007]
- [x] CHK024 May runtime UAT continue only for an identifiable destination already prequalified for the same named agent? [Controlled recovery, Spec §FR-007]
- [x] CHK025 Do unapproved, unknown, unidentifiable, different-agent, ambiguous, or conflicting reroutes hard-fail treatment? [Hard failure, Spec §FR-007]
- [x] CHK026 Does a missing reroute event remain unknown unless the pinned-surface profile guarantees complete terminal capture? [No-event semantics, Spec §FR-007]
- [x] CHK027 Are reroute events joined by pinned surface plus `threadId` and `turnId`, with ambiguous association rejected? [Association, Spec §Clarifications Session 2]

## Evidence, Replay, and Recovery Guidance

- [x] CHK028 Do raw-store path/permission failures prevent collection rather than redirect raw evidence into the repository? [Safety boundary, Plan §Evidence and Data Boundaries]
- [x] CHK029 Does sanitization reject non-allowlisted fields and preserve only deterministic pseudonymous joins? [Privacy failure, Spec §Clarifications Session 3]
- [x] CHK030 Are raw digest, fixture digest, schema/sanitizer version, and expected disposition required before replay? [Precondition, Data Model §Fixture Provenance and Replay]
- [x] CHK031 Does replay fail on hash drift before parsing, undeclared fields, network/raw-store access, disposition drift, or unequal second-pass output? [Determinism, Spec §FR-008]
- [x] CHK032 Are all remediation paths bounded to a corrected input, successor snapshot/freeze, or restored documented discovery rather than retrying outcome-bearing work? [Recovery policy, Research §§Source-Ledger Refresh Rules, Canary Decisions]
- [x] CHK033 Are errors prohibited from leaking into scoring, qualification, preference, fallback order, installation, defaults, agent configuration, or payload behavior? [Scope containment, Plan §Technical Context]

## Result

- 33 items checked.
- 0 unresolved gaps.
- Every recoverable path produces a new bounded input or successor record; none silently assumes success or retries within the same evidence snapshot.
