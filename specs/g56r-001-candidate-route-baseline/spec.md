# Feature Specification: Candidate Route Baseline and Role Contracts

**Feature Branch**: `g56r-001-candidate-route-baseline`

**Created**: 2026-07-14

**Status**: Complete

**Input**: User description: "Define a one-working-day, research-only candidate route baseline and role contracts for all twelve named agents."

**Source decisions**: `docs/ai/specs/.process/G56R-001-design-concept.md` (23 accepted scoping decisions), `docs/prd-codex-gpt-5-6-agent-routing.md` (AC-1.1 through AC-1.7), and `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md` (G56R-001)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review a Trustworthy Candidate Baseline (Priority: P1)

As a SpecKit Pro maintainer, I can review one dated, cited research narrative
and a separate structured manifest for all twelve named agents so that G56R-002
can freeze an executable candidate set without rediscovering scope or silently
changing production behavior.

**Why this priority**: G56R-002 cannot safely discover capabilities or freeze
an executable set until every named role, immutable route, candidate, evidence
boundary, and downstream requirement has an auditable baseline.

**Independent Test**: A maintainer can review the two research artifacts and
run the focused artifact checks to reproduce the recorded G56R-002 go/no-go
decision without consulting undocumented context or executing a candidate.

**Acceptance Scenarios**:

1. **Given** the ten current Codex agents and the two parity additions, **When**
   the maintainer reviews the narrative and manifest, **Then** exactly twelve
   agent records are present, each with a role contract and either its immutable
   current production route or an explicit recorded absence.
2. **Given** `consensus-synthesizer` and `gate-validator` have no current Codex
   production route, **When** their records are reviewed, **Then** their
   contracts preserve the semantics of the corresponding Claude roles without
   treating Claude-specific configuration syntax as the contract.
3. **Given** a platform claim and a project claim, **When** their evidence is
   inspected, **Then** the platform claim cites current official OpenAI
   documentation and the project claim cites repository evidence, with facts,
   inferences, proposed policy, and unverified assumptions visibly separated.
4. **Given** route-related evidence from tracked source, cached source, and an
   installed environment, **When** the baseline is reviewed, **Then** the three
   evidence classes remain distinct and installed observations are sanitized.
5. **Given** a role-eligible model-and-effort candidate, **When** the candidate
   catalog is reviewed, **Then** it is present unless a recorded hard-contract
   incompatibility or another predeclared evidence-based exclusion applies;
   absence on the current machine alone does not exclude it.
6. **Given** CLI, desktop/app, app-server, and non-interactive evidence, **When**
   a maintainer traces a claim, **Then** its surface and applicability are
   explicit and the claim is not generalized to another surface.
7. **Given** the current three Codex role fixtures and nine missing role
   fixtures, **When** the handoff is reviewed, **Then** all twelve agents have a
   fixture contract and historical prompt-emulation results are marked
   `non_release_evidence`.
8. **Given** the one-working-day boundary, **When** every objective completion
   condition is satisfied, **Then** the research records a go handoff to
   G56R-002 with classified downstream unknowns.
9. **Given** the one-working-day boundary, **When** any objective completion
   condition is not satisfied, **Then** work stops without extension and emits
   a precise no-go packet naming each unmet condition, its evidence, and the
   required follow-up.

### Edge Cases

- Official sources conflict, use different client terminology, or do not state
  whether a claim applies to a target surface.
- Tracked source, cached source, and sanitized installed-state observations
  disagree about a production route or instruction body.
- One of the two parity roles lacks enough project evidence to derive a
  semantic safety, mutation, tool, or output contract.
- A project-level candidate is documented but unavailable on the current
  machine or on only some target surfaces.
- A candidate is otherwise discoverable but cannot preserve one hard role,
  authorization or approval, safety, grounding, mutation, tool, skill, MCP,
  sandbox, or output contract.
- A prompt or context variant has no evidence-backed overhead hypothesis, or
  the unchanged-prompt control is missing.
- Two records use different readable IDs for the same canonical contract or
  route, or reuse an ID for different canonical content.
- Installed-state evidence contains a home path, credential, or unrelated
  configuration field that must not enter public artifacts.
- A source becomes unavailable, changes during the spike, or cannot be
  classified before the timebox expires.
- A G56R-002 capability question remains open at the deadline; it is allowed
  only when clearly classified and does not hide a missing G56R-001 contract,
  candidate, provenance, or agreement requirement.

## Clarifications

### Session 1 — Evidence Authority and Surface Applicability (2026-07-14)

- **Official-source precedence**: Use only first-party OpenAI documentation or
  release notes for platform facts. Prefer the source with the narrowest
  explicit surface, version, and feature applicability. Release notes establish
  historical or version facts only; recency alone does not resolve equal-scope
  conflicts.
- **Repository evidence roles**: Cite tracked files at a recorded repository
  revision. Accepted planning records establish requirements, source and
  manifests establish current definitions, and tests or fixtures establish
  declared validation and inventory. Generated artifacts cannot override their
  canonical inputs; cache and installed state remain environment observations.
- **Surface isolation**: Represent `cli`, `desktop_app`, `app_server`, and
  `non_interactive` independently. Evidence never inherits across surfaces;
  silence is `undocumented`, and `not_applicable` requires explicit evidence.
- **Provenance completeness**: Record source URL, exact locator, retrieval date,
  surface, feature, documented client or version scope, applicability, conflict
  status, and invalidation trigger. Missing source scope is `not_stated`, never
  an inferred current or cross-version claim.
- **Conflict terminal rule**: Classify every unresolved authority conflict as
  `blocking_no_go` when it prevents the objective completeness gate, or as
  `nonblocking_deferred` only when it supports no G56R-001 conclusion and has a
  named owner, impact, and follow-up.
- **Authority-resolution proof**: `resolved_by_authority` MUST name the winning
  evidence ID and the narrower explicit surface/version/feature basis. Evidence
  recorded as `not_stated` for that surface can neither win nor participate as
  a competing authority. An intersection or admission restriction derived from
  multiple sources is `proposed_policy`, not an authority resolution.
- **Freshness and invalidation rule**: Platform and environment evidence used
  by a passing completion check MUST be retrieved or observed during the
  recorded workday; project evidence MUST match the pinned research revision.
  An unavailable or unverifiable source, or a fired invalidation trigger, MUST
  stop the affected claim from remaining classified as a fact. The claim MUST
  be revalidated or classified as an `unverified_assumption` or `conflict` with
  a terminal disposition. A trigger that fires after `go` invalidates the
  affected admission evidence and dependent results until refresh and
  re-admission.

### Session 2 — Agent Contract, Identity, and Manifest Completeness (2026-07-14)

- **Manifest envelope and version**: The JSON root MUST contain
  `"manifest_type": "agent_route_candidate_manifest"`,
  `"manifest_version": 1`, `"research_date": "YYYY-MM-DD"`, and
  `"agents": [...]`. The `agents` array contains one self-contained record per
  named agent; route-centric or normalized top-level tables are prohibited.
  Increment `manifest_version` only when the machine-readable contract changes.
- **Readable IDs**: `agent_contract_id` MUST match
  `agent-contract/<agent-name>/v<N>`. `candidate_route_id` MUST match
  `candidate-route/<agent-name>/<model-slug>/<effort-slug>/<treatment-slug>/v<N>`,
  where exact model and effort values remain separate fields and
  `treatment-slug` is `unchanged` or an evidence-justified variant. IDs MUST NOT
  encode preference or fallback rank. One canonical identity has one ID, and an
  ID MUST NOT be reused after its route-defining tuple or bound hashes change.
- **Canonical hashes**: Hashes use SHA-256 and lowercase
  `sha256:<64-hex>`. Before hashing, normalize strings to Unicode NFC, normalize
  CRLF and CR to LF, preserve all other whitespace, and encode UTF-8 without a
  byte-order mark. `instruction_hash` covers the complete decoded instruction
  body only, excluding TOML, frontmatter, route, and transport syntax; for the
  two parity roles it covers the cited Claude instruction body used as the
  semantic source without implying a Codex production route. `contract_hash`
  covers `agent_name` plus the FR-006 semantic contract fields after recursive
  string normalization and Python
  `json.dumps(..., ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)`
  serialization. IDs, hashes, routes, candidates, provenance, and presentation
  fields are excluded from the contract-hash payload.
  For Claude frontmatter sources, the body begins immediately after the LF
  terminating the closing `---`; every following character, including the
  blank separator LF before the first heading, remains part of the body.
- **Required record fields**: Every agent record contains `agent_name`,
  `agent_contract`, `production_route`, and `candidates`. `agent_contract`
  contains both IDs and hashes plus every FR-006 semantic field.
  `production_route` contains `status`, `candidate_route_id`, `model_id`,
  `reasoning_effort`, `instruction_hash`, `contract_hash`, `absence_reason`,
  `provenance`, and `invalidation_triggers`. Present routes require non-null
  route bindings; only `consensus-synthesizer` and `gate-validator` use
  `status: "absent"`, null route bindings, and a cited absence reason. Every
  candidate contains `candidate_route_id`, `agent_contract_id`, `model_id`,
  `reasoning_effort`, `treatment`, both hashes, `project_eligibility`,
  `installation_availability`, `capability_requirements`, `rationale`,
  `known_incompatibilities`, `qualification_requirements`, `provenance`, and
  `invalidation_triggers`. Capability requirements separately cover model,
  modalities, reasoning effort, custom agents, tools, skills, MCP, sandbox,
  mutation, and clients. Rationale records classification, summary, and evidence
  IDs. Each incompatibility records the affected contract field, description,
  evidence IDs, and eligibility effect; use an explicit empty list when no
  incompatibilities exist. Qualification remains `unqualified` or
  `not_applicable_excluded` and
  names required capability checks, fixture, artifacts, telemetry, and owner.
  Project-fact provenance also records repository revision and evidence role.
  `installation_availability.status` remains `unresolved_g56r_002`; sanitized
  observations cannot change project eligibility.
- **Agreement and completeness**: Focused checks prove both artifacts contain
  exactly the FR-002 set: 12 unique agents, 10 present production routes, and
  absent routes only for `consensus-synthesizer` and `gate-validator`. Normalized
  Markdown and JSON projections agree on IDs, hashes, route or absence,
  model-effort-treatment tuples, eligibility, installed availability,
  capabilities, rationale, incompatibilities, qualification, provenance,
  invalidation triggers, and classified unknowns. Missing fields are errors;
  empty lists and permitted nulls are explicit values. A deterministic
  human-narrative content-hash marker MUST also bind all prose outside the
  normalized projection so stale summary text fails validation. Lexical
  stable-ID order is presentation-only and MUST NOT express preference or
  fallback ordering.

Changing hash inputs, role, authorization or approval, safety, grounding,
mutation, tool, skill, MCP, sandbox, output, route-to-contract binding,
hard-incompatibility, parity-route absence, or eligibility-versus-availability
semantics requires explicit maintainer security review; this clarification does
not change those accepted boundaries.

### Session 3 — Local Evidence, Fixture Backlog, and Go/No-Go (2026-07-14)

- **Evidence separation and sanitization**: Every agent MUST record independent
  `tracked_source`, `cached_source`, and `installed_state` observations with
  only the evidence class, agent name, relevant model and effort fields,
  instruction and contract hashes, observation date, surface, and version when
  known. Tracked source additionally records a repository-relative path,
  revision, and evidence role; cache and installed locators remain logical
  labels. Absolute or home paths, usernames, hostnames, credentials, secrets,
  and unrelated configuration are prohibited. Only tracked source defines the
  production contract; mismatches are record-only defects with a named owner.
- **Fixture inventory and contract**: The three current fixtures are exactly
  `codebase-analyst`, `domain-researcher`, and `spec-context-analyst`. The nine
  missing fixtures are exactly `phase-executor`, `implement-executor`,
  `analyze-executor`, `checklist-executor`, `uat-runbook-author`,
  `clarify-executor`, `consensus-synthesizer`, `gate-validator`, and
  `autopilot-fast-helper`. Every agent's fixture contract contains status, a
  nullable repository-relative fixture path, representative task and input
  type, expected behavior and output shape, and FR-006 hard-contract
  assertions. Historical prompt-emulation remains `non_release_evidence`.
- **Focused artifact checks**: One delivery-specific, offline, read-only Python
  3.11+ standard-library checker MUST parse JSON structurally and fail on an
  invalid envelope or version; incorrect 12/10/2 coverage; missing or duplicate
  IDs; invalid hashes or canonicalization; incomplete contracts, candidates,
  provenance, or surface records; fixture inventory or contract gaps;
  sanitization violations; cross-artifact disagreement; unclassified unknowns;
  or an unreproducible gate result. It MUST NOT become a reusable framework or
  perform probing, scoring, qualification, or mutation.
- **Unknown ownership**: G56R-001 resolves documentation and tracked, cached,
  and sanitized installed-state inventory questions and completes contracts,
  candidates, provenance, fixture contracts, agreement, and sanitization.
  G56R-002 owns executable capability and installation-availability questions
  against a versioned capability snapshot. G56R-003 owns fixture execution,
  exact-treatment replay, scoring, qualification, and evidence-backed preferred
  or fallback ordering. Every deferred unknown records its class, impact, owner
  spec, and required follow-up.
- **One-day terminal gate**: Before evidence collection, record `started_at`
  and the scheduled workday `deadline_at`; record `stopped_at` when the terminal
  packet is emitted. All three are RFC 3339 timestamps with explicit UTC
  offsets and MUST satisfy `started_at <= stopped_at <= deadline_at`. Emit `go`
  only when every FR-024 condition passes before the deadline and no blocking
  conflict or unclassified unknown remains. Otherwise emit `no_go` with the
  three timestamps, `completed_artifacts`, and `unmet_conditions`; each unmet
  condition contains `gate_id`, `requirement_refs`, `condition`,
  `available_evidence_ids`, `impact`, `owner_spec`, and `required_follow_up`.
  The spike MUST NOT extend scope, reduce deliverables, fix discovered defects,
  or mutate production state.

Expanding retained machine-local fields or changing the security-relevant
boundaries named after Session 2 requires explicit maintainer security review.
Human review of these normative field and payload names is required with the
artifact review; it does not create an unresolved Clarify item.

## Requirements *(mandatory)*

### Scope Boundaries

This feature is one research-only spike. It does not perform runtime capability
probes, execute or score candidates, qualify routes, choose final fallback
ordering, or mutate tracked source, agents, installers, prompts, payloads,
caches, installed-state, defaults, versions, or unrelated configuration.
Defects discovered during inventory are recorded and handed off; they are not
fixed in this feature.

### Functional Requirements

- **FR-001**: The research MUST publish one dated, cited Markdown narrative and
  one separate, versioned JSON `agent_route_candidate_manifest`.
- **FR-002**: The two artifacts MUST cover exactly these twelve named agents:
  `phase-executor`, `implement-executor`, `analyze-executor`,
  `checklist-executor`, `uat-runbook-author`, `clarify-executor`,
  `domain-researcher`, `codebase-analyst`, `spec-context-analyst`,
  `consensus-synthesizer`, `gate-validator`, and `autopilot-fast-helper`.
- **FR-003**: Every agent MUST have an immutable production-route record; the
  ten current Codex agents MUST record their source baseline, while
  `consensus-synthesizer` and `gate-validator` MUST record that no current Codex
  production route exists.
- **FR-004**: The inventory MUST identify every active source, installer,
  skill, validation, evaluation, generated-payload, and installed-cache surface
  that encodes or consumes the twelve agents' route policy. Each active point
  MUST appear exactly once at the pinned research revision with a stable entry
  ID, repository-relative or logical locator, integration class, producer,
  consumer, or both role, affected agents and policy fields, authority and
  evidence classes, canonical-input or derived-output relationship, reciprocal
  upstream and downstream entry IDs, revision or version, observation date,
  mismatch status, and nullable defect owner. Derived outputs MUST name their
  canonical input and remain non-authoritative. Missing, duplicate, orphaned,
  unclassified, or unowned mismatching entries fail FR-024.
- **FR-005**: Tracked source, cached source, and sanitized installed-state
  evidence MUST remain separate, and any mismatch MUST be recorded without
  allowing local state to redefine the tracked production contract.
- **FR-006**: Every agent MUST have a semantic role contract covering role and
  authorization boundaries, including approval conditions and authorized
  approvers, safety, grounding, mutation, tools, skills, MCP use, sandbox
  expectations, output contract, supported-client assumptions, and
  representative tasks. Each hard-boundary field MUST state its applicable
  permitted and prohibited behavior and required stop or escalation condition;
  a generic capability label is insufficient.
- **FR-007**: The two parity contracts MUST be derived from the semantics of
  the corresponding Claude definitions and MUST NOT copy Claude-specific
  configuration mechanics as if they were Codex requirements. For every
  FR-006 field, each parity contract MUST record the exact Claude source
  locator and revision, a mapping status of `preserved`, `codex_adapted`, or
  `not_applicable`, a justification for adapted or non-applicable fields, and
  the mapped Codex contract value. Mapping metadata is provenance excluded from
  `contract_hash`; the mapped semantic value remains in the existing hash
  payload. Any missing hard field, unresolved locator, invalid status, missing
  justification, empty value, or normalized-value disagreement forces
  `no_go`.
- **FR-008**: Every agent contract MUST have a readable, stable
  `agent_contract_id`, a canonical instruction hash, and a canonical contract
  hash, with repeatable canonicalization rules recorded in the narrative.
- **FR-009**: The manifest MUST use agent-centric records that keep each named
  agent's contract, production route or absence, candidates, provenance, and
  invalidation rules together.
- **FR-010**: Every candidate route MUST have a readable
  `candidate_route_id` and record its model-and-effort tuple, instruction and
  contract hashes, required model and modality capabilities, custom-agent,
  tool, skill, MCP, sandbox, mutation, and client requirements, rationale,
  known incompatibilities, required qualification artifacts, and invalidation
  triggers. Each candidate's `agent_contract_id` and `contract_hash`, and each
  production route's `contract_hash`, MUST match the enclosing agent contract.
  Changing model, reasoning effort, or treatment MUST NOT replace or relax the
  bound hard contract.
- **FR-011**: The catalog MUST include every evidence-supported project-level
  model-and-effort candidate eligible for a named role, including the immutable
  production baseline, without claiming that a candidate is executable or
  qualified.
- **FR-012**: A candidate MAY be excluded only for recorded incompatibility,
  hard-contract failure, or applicable predeclared dominance evidence; every
  exclusion MUST cite its evidence and affected contract, and local
  unavailability alone MUST NOT be an exclusion. A cited incompatibility with
  any hard role, authorization or approval, safety, grounding, mutation, tool,
  skill, MCP, sandbox, or output boundary MUST mark the candidate `excluded`.
- **FR-013**: Project-level candidate eligibility MUST be distinct from
  installation-time availability, which remains a G56R-002 decision bound to a
  versioned capability snapshot.
- **FR-014**: A prompt or context variant MUST be included only when evidence
  supports a bounded overhead hypothesis, and every such comparison MUST
  retain the unchanged prompt or context as its attribution control.
- **FR-015**: Preferred-route and fallback-candidate signals MUST be labeled as
  hypotheses; the artifacts MUST NOT establish a final preferred route or
  ordered fallback policy.
- **FR-016**: The platform fact table MUST cover model identifiers,
  custom-agent configuration fields, supported reasoning controls, capability
  discovery, telemetry, reroute events, and non-interactive output. Current
  official OpenAI documentation MUST be the exclusive authority for these
  OpenAI platform facts, while repository files MUST be the authority only for
  SpecKit Pro project facts. For competing official sources, authority MUST
  follow the source with the narrowest explicit surface, version, and feature
  applicability; recency alone MUST NOT break a tie, and equally applicable
  conflicts MUST remain unresolved.
- **FR-017**: Every platform fact MUST record an exact official source locator,
  retrieval date, target Codex surface, feature, documented client or version
  scope, applicability status, conflict status, and invalidation trigger.
  Omitted source scope MUST be recorded as `not_stated` and MUST NOT be
  inferred. Every project fact MUST cite a tracked repository-relative path and
  recorded revision, identify that file's evidence role, and remain unresolved
  when no declared canonical source establishes precedence. Evidence used by a
  passing FR-024 check MUST satisfy the freshness rule: official and environment
  evidence is retrieved or observed during the recorded workday, and project
  evidence matches the pinned research revision. If a source is unavailable or
  unverifiable, or an invalidation trigger fires, the affected claim MUST be
  revalidated or reclassified from fact to `unverified_assumption` or
  `conflict`; the affected completion check cannot pass until resolved.
- **FR-018**: Platform facts, project facts, reasonable inferences, proposed
  SpecKit Pro policy, and unverified assumptions MUST be visibly classified;
  the research MUST NOT claim undocumented native fallback, benchmark, model,
  effort, telemetry, or effective-route behavior.
- **FR-019**: Conflicting or applicability-ambiguous sources MUST be recorded
  as conflicts and left unresolved when authority cannot be established; the
  newest source or a local observation MUST NOT silently win. Every unresolved
  authority conflict MUST end as `blocking_no_go` or `nonblocking_deferred`.
  Blocking conflicts fail FR-024; nonblocking conflicts require named
  ownership, impact, and follow-up and MUST NOT support a G56R-001 conclusion.
- **FR-020**: Every platform claim MUST use independent Surface Records for
  `cli`, `desktop_app`, `app_server`, and `non_interactive` as applicable.
  Evidence MUST NOT be inherited across surfaces; silent coverage is
  `undocumented`, and `not_applicable` requires explicit official evidence.
- **FR-021**: Installed-state evidence MUST retain only relevant sanitized
  facts and hashes and MUST exclude absolute or home paths, usernames,
  hostnames, credentials, secrets, and unrelated local configuration.
- **FR-022**: The handoff MUST identify the three current and nine missing Codex
  role fixtures, provide a fixture contract for every agent with a
  representative task, expected behavior, and hard-contract assertions, and
  label historical prompt-emulation results as `non_release_evidence`.
- **FR-023**: The handoff MUST state telemetry requirements, classify every
  unresolved question by whether documentation, G56R-002 capability discovery,
  or later scored qualification can answer it, and identify the owning
  downstream spec without treating the unknown as a final policy decision.
  G56R-002 admission MUST require `go`, the supported manifest type/version,
  passing focused checks, and an immutable binding to the research revision,
  manifest content hash, every production-route identity, every contract ID
  and hash, every candidate ID and bound identity tuple, and the required
  capability-snapshot scope. The manifest content hash MUST be lowercase
  `sha256:<64-hex>` over the complete recursively normalized manifest after
  omitting `handoff.admission_binding.manifest_content_hash`, serialized with
  the FR-008 canonical JSON rules. G56R-002, not G56R-001, creates or selects
  the versioned runtime capability snapshot and binds it during admission.
  `no_go` and unsupported manifest versions are rejected before capability
  work begins.
- **FR-024**: The G56R-002 handoff MUST use an objective completeness gate that
  checks artifact presence, twelve-agent coverage, contract and candidate
  completeness, provenance, cross-artifact agreement, fixture contracts,
  telemetry requirements, classified unknowns, and sanitization. Admission
  MUST preserve the candidate set and every project-eligibility value; G56R-002
  may record installation availability only after binding its own versioned
  capability snapshot and MUST NOT mutate qualification, preference, or
  fallback order.
  Drift in any bound research revision, manifest identity, production route,
  instruction, contract, or candidate identity invalidates admission and its
  dependent results until G56R-002 re-admits a new versioned snapshot.
- **FR-025**: Before evidence collection, the spike MUST record `started_at`
  and its scheduled workday `deadline_at`, then stop and record `stopped_at` no
  later than that deadline. All three timestamps MUST use RFC 3339 with an
  explicit UTC offset and satisfy `started_at <= stopped_at <= deadline_at`.
  It MUST emit a go packet only when FR-024 passes before the deadline;
  otherwise it MUST emit a no-go packet listing each unmet condition, available
  evidence, impact, and required follow-up without extending the spike or
  reducing accepted deliverables.
- **FR-026**: Artifact validation MUST use focused Python 3.11+ standard-library
  structured checks only, MUST parse JSON structurally, and MUST NOT add Bash,
  `jq`, package dependencies, or a reusable validator framework. Because the
  checked-in checker is a repository tool, it MUST have focused Layer 4 unit
  coverage under `tests/speckit-pro/unit/`, with its test entry declared in
  `tests/speckit-pro/suite-manifest.json`. The existing repository guard MUST
  also allow exactly the two contracted `docs/ai/research/` artifacts without
  broadening its public-claim exclusions.
- **FR-027**: The spike MUST NOT perform runtime probing, live scoring,
  qualification, final fallback ordering, or defect fixes; MUST NOT mutate
  tracked source, agents, prompts, installers, caches, installed-state,
  generated payloads, defaults, versions, or unrelated configuration; and MUST
  NOT remove a project candidate solely because this installation lacks it.

### Reviewability Notes

- This is a ratified one-working-day research spike, not a transition
  exception. Incomplete objective criteria produce the no-go packet required by
  FR-025 rather than a larger review surface.
- Documentation, JSON, and focused verification evidence remain part of the
  human review even though they contribute no production LOC.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: N/A; repository runtime, payload, installer,
  and agent surfaces are read-only evidence inputs
- **Projected reviewable production LOC**: 0
- **Projected production files**: 0
- **Projected total delivery files**: approximately 3 research delivery files,
  plus 3 required validation paths after the post-commit guard is exercised
- **Budget result**: within budget as a one-working-day research spike; the
  timebox and objective terminal gate are the sizing controls
- **Split decision**: no split; this remains one G56R-001 spike and stops with a
  precise no-go packet if the accepted scope cannot finish in one working day
- **Transition exception**: none

### PR Review Packet Requirements *(mandatory)*

- The PR description MUST include what changed, why it changed, non-goals,
  review order, the 0-production-LOC scope budget, traceability, verification
  evidence, known gaps, and rollback or feature-flag notes.
- Review order MUST lead with the cited narrative, continue through the
  agent-centric manifest, and finish with focused artifact-check evidence.
- Traceability MUST map every major functional requirement and measurable
  outcome to the delivery artifact and verification evidence that proves it.
- Known gaps and deferred work MUST name G56R-002, G56R-003, or the exact later
  owning spec; no generic future-work bucket is sufficient.
- Rollback notes MUST state that the research artifacts can be reverted without
  production-route changes; feature-flag notes MUST explicitly record that no
  runtime feature flag applies to this research-only delivery.

### Key Entities

- **Research Narrative**: The dated human-readable record of evidence,
  classifications, conflicts, source-versus-environment observations, role
  contracts, fixture gaps, telemetry needs, unknowns, and the final handoff.
- **Agent Contract**: The immutable semantic obligations for one named role,
  including authorization, safety, grounding, mutation, tools, skills, MCP,
  sandbox, output, client assumptions, and representative work.
- **Candidate Route**: One project-level model-and-effort hypothesis bound to an
  agent contract, canonical hashes, capability requirements, provenance,
  incompatibilities, qualification needs, and invalidation triggers.
- **Evidence Claim**: A classified platform fact, project fact, inference,
  proposed policy, assumption, conflict, or sanitized environment observation
  with a source locator and applicability.
- **Surface Record**: Evidence scoped to one of CLI, desktop/app, app-server, or
  non-interactive Codex behavior.
- **Fixture Contract**: The representative task, expected behavior, and hard
  assertions later qualification must implement for one named agent.
- **Handoff Decision**: A reproducible go or no-go result with completion-gate
  evidence, classified unknowns, and named downstream ownership.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: By the end of one working day, exactly one dated Markdown
  narrative and one separate versioned JSON manifest exist, or a no-go packet
  precisely identifies why either required artifact could not be completed.
- **SC-002**: Artifact checks find exactly 12 unique named-agent records: 10
  with immutable Codex production routes and 2 with explicit absent-route
  records for `consensus-synthesizer` and `gate-validator`.
- **SC-003**: All 12 agents have complete role contracts, unique readable
  contract IDs, canonical instruction hashes, and canonical contract hashes;
  repeated canonicalization produces the same hashes.
- **SC-004**: Every included or excluded candidate has all required route,
  evidence, compatibility, qualification, and invalidation fields; zero
  candidates are excluded solely because they are unavailable on this machine.
- **SC-005**: One hundred percent of platform facts cite current official
  OpenAI documentation with locator, retrieval date, surface, and
  applicability, and one hundred percent of project facts cite repository
  locators; unresolved source conflicts remain explicitly labeled.
- **SC-006**: All four target Codex surfaces have separate records, all tracked,
  cached, and installed evidence is separately classified, and publication
  contains zero home paths, credentials, secrets, or unrelated local settings.
- **SC-007**: The fixture inventory reports exactly 3 current and 9 missing
  Codex role fixtures, all 12 fixture contracts are actionable, and every
  historical prompt-emulation result is labeled `non_release_evidence`.
- **SC-008**: Focused structured checks report valid JSON, no missing or
  duplicate agent/contract/route IDs, no hash-format or canonicalization errors,
  and no material disagreement between the narrative and manifest.
- **SC-009**: Given the same artifacts, a maintainer following the published
  completion gate reaches the same go/no-go result as the recorded handoff and
  can identify the owner of every deferred unknown without undocumented
  judgment.
- **SC-010**: The delivery preserves 0 production LOC and 0 production files,
  contains the approximately 3 research delivery files plus only the focused
  Layer 4 test, required suite-manifest declaration, and exact two-file
  research allowance in the existing repository guard, and its PR review
  packet maps every major requirement and outcome to a file and verification
  result without invoking a transition exception.

## Assumptions

- The research date is 2026-07-14, and source retrieval dates are recorded at
  the time each source is inspected.
- The ten tracked Codex agent definitions are the current project baseline at
  spike start; the research revalidates, rather than assumes, their exact route
  and instruction contents.
- The accepted baseline is three current Codex fixture directories and nine
  missing role fixtures; Claude parity fixtures and historical prompt-emulation
  results do not count as current Codex release evidence.
- A classified G56R-002 capability unknown may coexist with a go decision when
  all G56R-001 facts, contracts, candidates, provenance, and handoff fields are
  complete. An unclassified unknown or a missing G56R-001 obligation requires a
  no-go decision.
- "One working day" means one scheduled maintainer workday with recorded start
  and stop timestamps; the spike does not continue into another workday.
- Official OpenAI documentation may not answer installation-specific
  executability questions. Those questions remain explicitly deferred to
  G56R-002 rather than inferred from local availability.
- Focused validation is delivery-specific and disposable; it does not establish
  a new general-purpose schema or validation framework.

### Dependencies

- G56R-001 has no upstream SPEC dependency. Its research inputs are the tracked
  Codex agent definitions, the corresponding Claude definitions for the two
  semantic-parity roles, the current fixture inventory, and current official
  OpenAI documentation for platform facts.
- G56R-002 depends on this spike's candidate manifest, role contracts,
  telemetry requirements, classified capability questions, and objective
  go/no-go packet; this spike does not depend on G56R-002 capability results.
- G56R-003 owns later fixture execution, exact-treatment replay, scoring, and
  qualification. Those downstream activities are not prerequisites for this
  research baseline.
