# Feature Specification: Candidate Route Baseline and Role Contracts

**Feature Branch**: `g56r-001-candidate-route-baseline`

**Created**: 2026-07-14

**Status**: Draft

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
  safety, grounding, mutation, tool, skill, MCP, sandbox, or output contract.
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

## Requirements *(mandatory)*

### Scope Boundaries

This feature is one research-only spike. It does not perform runtime capability
probes, execute or score candidates, qualify routes, choose final fallback
ordering, or mutate agents, installers, prompts, payloads, caches,
installed-state, defaults, or versions. Defects discovered during inventory are
recorded and handed off; they are not fixed in this feature.

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
  that encodes or consumes the twelve agents' route policy.
- **FR-005**: Tracked source, cached source, and sanitized installed-state
  evidence MUST remain separate, and any mismatch MUST be recorded without
  allowing local state to redefine the tracked production contract.
- **FR-006**: Every agent MUST have a semantic role contract covering role and
  authorization boundaries, safety, grounding, mutation, tools, skills, MCP
  use, sandbox expectations, output contract, supported-client assumptions,
  and representative tasks.
- **FR-007**: The two parity contracts MUST be derived from the semantics of
  the corresponding Claude definitions and MUST NOT copy Claude-specific
  configuration mechanics as if they were Codex requirements.
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
  triggers.
- **FR-011**: The catalog MUST include every evidence-supported project-level
  model-and-effort candidate eligible for a named role, including the immutable
  production baseline, without claiming that a candidate is executable or
  qualified.
- **FR-012**: A candidate MAY be excluded only for recorded incompatibility,
  hard-contract failure, or applicable predeclared dominance evidence; every
  exclusion MUST cite its evidence and affected contract, and local
  unavailability alone MUST NOT be an exclusion.
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
  SpecKit Pro project facts.
- **FR-017**: Every platform fact MUST record an exact official source locator,
  retrieval date, target Codex surface, and client or feature applicability;
  every project fact MUST record a repository-relative source locator.
- **FR-018**: Platform facts, project facts, reasonable inferences, proposed
  SpecKit Pro policy, and unverified assumptions MUST be visibly classified;
  the research MUST NOT claim undocumented native fallback, benchmark, model,
  effort, telemetry, or effective-route behavior.
- **FR-019**: Conflicting or applicability-ambiguous sources MUST be recorded
  as conflicts and left unresolved when authority cannot be established; the
  newest source or a local observation MUST NOT silently win.
- **FR-020**: CLI, desktop/app, app-server, and non-interactive records MUST be
  separate and MUST state when evidence is unavailable for a surface.
- **FR-021**: Installed-state evidence MUST retain only relevant sanitized
  facts and hashes and MUST exclude home paths, credentials, secrets, and
  unrelated local configuration.
- **FR-022**: The handoff MUST identify the three current and nine missing Codex
  role fixtures, provide a fixture contract for every agent with a
  representative task, expected behavior, and hard-contract assertions, and
  label historical prompt-emulation results as `non_release_evidence`.
- **FR-023**: The handoff MUST state telemetry requirements, classify every
  unresolved question by whether documentation, G56R-002 capability discovery,
  or later scored qualification can answer it, and identify the owning
  downstream spec without treating the unknown as a final policy decision.
- **FR-024**: The G56R-002 handoff MUST use an objective completeness gate that
  checks artifact presence, twelve-agent coverage, contract and candidate
  completeness, provenance, cross-artifact agreement, fixture contracts,
  telemetry requirements, classified unknowns, and sanitization.
- **FR-025**: The spike MUST stop after one working day. It MUST emit a go
  packet only when FR-024 passes; otherwise it MUST emit a no-go packet listing
  each unmet condition, available evidence, impact, and required follow-up
  without extending the spike or reducing accepted deliverables.
- **FR-026**: Artifact validation MUST use focused Python 3.11+ standard-library
  structured checks only, MUST parse JSON structurally, and MUST NOT add Bash,
  `jq`, package dependencies, or a reusable validator framework.
- **FR-027**: The spike MUST NOT perform runtime probing, live scoring,
  qualification, final fallback ordering, production mutation, or defect fixes,
  and MUST NOT remove a project candidate solely because this installation
  lacks it.

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
- **Projected total delivery files**: approximately 3
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
- **SC-010**: The delivery preserves 0 production LOC, 0 production files, and
  approximately 3 delivery files, and its PR review packet maps every major
  requirement and outcome to a file and verification result without invoking a
  transition exception.

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
