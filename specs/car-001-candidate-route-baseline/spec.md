# Feature Specification: CAR-001 Candidate Route Baseline and Role Contracts

**Feature Branch**: `car-001-candidate-route-baseline`

**Created**: 2026-07-14

**Status**: Draft

**Input**: User description: "CAR-001 Candidate Route Baseline and Role Contracts — a dated, cited research record plus a versioned machine-readable candidate-route manifest covering all twelve named agents, produced as a read-only research spike so CAR-002 can freeze the candidate set against probed capabilities. Design decisions recorded in docs/ai/specs/.process/CAR-001-design-concept.md; acceptance criteria AC-1.1 through AC-1.7 in docs/prd-claude-agent-routing.md."

## User Scenarios & Testing *(mandatory)*

<!--
  This is a single-story research spike. The one story below is the whole MVP:
  a dated, cited baseline handoff that unblocks the CAR-002..CAR-011 chain.
-->

### User Story 1 - Consume a dated, cited candidate-route baseline (Priority: P1)

As a CAR-series implementer, I open one research record and one machine-readable manifest and find, for all twelve named agents, what each agent's role contract is, what its immutable production route is today (or that it has none), which candidate routes are role-eligible, and which platform behaviors are documented facts versus inferences versus proposed policies — so I can start capability probing (CAR-002) and scored evaluation (CAR-003) without re-deriving role contracts or re-litigating undocumented platform behavior.

**Why this priority**: It is the only story, and it is the foundational baseline that unblocks every later spec in the CAR series. Nothing downstream can proceed without a dated, cited candidate set and role-contract catalog to build on. P1.

**Independent Test**: Open the research record and the JSON manifest and confirm that each of the twelve agents has a complete entry (role contract; immutable production route or its recorded absence; candidate tuples carrying both the shipped alias and the expected resolved model ID; required capabilities; `agent_contract_id`; instruction hash; rationale; known incompatibilities; required qualification artifacts; invalidation triggers); that every recorded platform fact carries a source URL, an access date, and a short verbatim quote and is labeled fact / inference / proposed policy / assumption; and that the go/no-go handoff lists capability questions with stable IDs — all without any dependency on CAR-002 results and without any shipped-default change.

**Acceptance Scenarios**:

1. **Given** the research record, **When** a reader inventories the target agents, **Then** all twelve named agents appear — the eleven current Claude agents plus the net-new `autopilot-fast-helper` — each with a role-specific contract, and every active source, skill, validation, evaluation, generated-payload, and installed-cache surface that encodes or consumes their route policy is listed. *(AC-1.1)*
2. **Given** any recorded platform fact (model IDs, aliases, subagent configuration fields, effort levels, model-resolution precedence, plugin-agent field support, fast mode, authentication modes, non-interactive telemetry), **When** a reviewer checks its evidence, **Then** the row cites current official Anthropic documentation with a source URL, an access date, and a short verbatim quote, and any conflicting claim is rejected or explicitly marked unresolved. *(AC-1.2)*
3. **Given** each of the twelve agents in the manifest, **When** a consumer reads its entry, **Then** it records the immutable production route (or its explicit absence for the net-new helper), a role-specific contract, every candidate model/effort tuple with both the shipped alias and the expected resolved model ID, required model/modality/subagent-field/tool/skill/client capabilities, `agent_contract_id`, prompt/instruction hash, candidate rationale, known incompatibilities, required qualification artifacts, and invalidation triggers, and it distinguishes project-level candidate eligibility from environment-time availability. *(AC-1.3, AC-1.6)*
4. **Given** any statement in the record, **When** a reviewer classifies it, **Then** it is visibly labeled as exactly one of platform fact, reasonable inference, proposed SpecKit Pro policy, or unverified assumption; no head-to-head benchmark or native fallback feature is claimed where none is documented; and the undocumented behavior when frontmatter names an unavailable model appears as a mandatory probe question, not an assumption. *(AC-1.4)*
5. **Given** the immutable production comparator, **When** a reader checks its identity, **Then** it is pinned to the latest published speckit-pro release tag at research time (2.19.1) plus its commit SHA, and each current agent's frontmatter route tuple is recorded together with the agent file's content hashes for drift detection. *(Design Q3)*
6. **Given** the instruction identity for any agent, **When** it is computed, **Then** it is the sha256 over the frontmatter-stripped agent body with the full-file sha256 recorded alongside, so a pure frontmatter route change does not invalidate instruction identity. *(Design Q4)*
7. **Given** the `autopilot-fast-helper` entry, **When** it is compared to the Codex helper source at `speckit-pro/codex-agents/autopilot-fast-helper.toml`, **Then** its role prose, bounded jobs, hard rules, and output formats are carried over as a contract-equivalent translation accompanied by an explicit platform-field mapping table, and any Claude-only field with no Codex equivalent (for example `maxTurns`) carries a value labeled "proposed SpecKit Pro policy". *(Design Q7, AC-1.6)*
8. **Given** the fixture backlog, **When** a reader inspects each agent's entry, **Then** it contains requirements-level content only — the role contract to exercise, representative task types, required evidence, and a pass/fail signal sketch — and contains no full fixture specifications. *(Design Q8)*
9. **Given** the current Layer 6 Claude evaluation path, **When** the record labels it, **Then** it is described as bare prompt emulation (a frontmatter-stripped agent body piped to `claude -p --model`) and all historical Layer 6 results are labeled `non_release_evidence` pending CAR-003 replay through the shared materializer. *(AC-1.7)*
10. **Given** the spike completes in a single autopilot run, **When** a mandatory fact remains unverified, **Then** it is recorded as an explicit no-go item or a stable-ID capability question in the go/no-go handoff rather than extending the timebox, and the handoff neither depends on CAR-002 results nor claims any candidate is executable before probing. *(Design Q9, AC-1.5)*
11. **Given** the spike's outputs, **When** the repository is inspected after the run, **Then** no agent frontmatter, prompt, generated payload, or shipped default has changed and nothing has landed under speckit-pro/'s allowlisted payload directories. *(Constraints, Non-goals)*

### Edge Cases

- **Alias not bound to a dated model ID in official docs.** If current official Anthropic documentation does not bind a Claude Code alias (opus, sonnet, haiku, fable) to a dated resolved model ID at research time, the binding becomes a mandatory CAR-002 probe question (a stable-ID capability question), not a recorded fact.
- **`fable` resolution or availability undocumented.** `fable` still enters executor-class candidate sets and is recorded with an invalidation trigger and a capability question; it is excluded only by recorded probe or contract evidence, never by product-announcement status.
- **Undocumented unavailable-model behavior.** The behavior when agent frontmatter names an unavailable model (hard error versus silent substitution) is recorded as a mandatory probe question, never assumed.
- **Documentation page changes after the access date.** The verbatim quote plus access date preserve what the official page said at research time; alias re-pointing is captured as a recorded invalidation trigger for *detection* rather than by re-research, while its undocumented execution-time *manifestation* (silent re-pointing versus hard error) is recorded as a mandatory capability question (FR-008) rather than assumed.
- **Mandatory fact unverifiable within the timebox.** Any mandatory fact still unverified when the single autopilot run ends becomes a no-go item or capability question in the handoff, not a timebox extension.
- **Later frontmatter drift from the comparator.** Recorded agent-file content hashes make any later drift of an agent's frontmatter route from the pinned comparator detectable.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The deliverable MUST comprise two artifacts — a human-readable Markdown research record at `docs/ai/research/claude-agent-route-candidates.md` and a separate machine-readable JSON manifest at `docs/ai/research/claude-agent-route-candidate-manifest.json`.
- **FR-002**: The research record MUST be dated and MUST inventory all twelve named target agents: the eleven current Claude agents (`analyze-executor`, `checklist-executor`, `clarify-executor`, `codebase-analyst`, `consensus-synthesizer`, `domain-researcher`, `gate-validator`, `implement-executor`, `phase-executor`, `spec-context-analyst`, `uat-runbook-author`) plus the net-new `autopilot-fast-helper`.
- **FR-003**: The record MUST inventory every active source, skill, validation, evaluation, generated-payload, and installed-cache surface that encodes or consumes agent route policy.
- **FR-004**: For every recorded platform fact — covering model IDs, aliases, subagent configuration fields, effort levels, model-resolution precedence, plugin-agent field support, fast mode, authentication modes, and non-interactive telemetry — the record MUST cite current official Anthropic documentation with a source URL, an access date, and a short verbatim quote.
- **FR-005**: The record MUST reject conflicting documentation claims or mark them explicitly unresolved; it MUST NOT present a resolved fact where official sources conflict. "Explicitly unresolved" MUST have a visible, recorded manifestation: an unresolved conflict MUST be recorded as a capability question (`CAP-Qn`, FR-021) with the conflicting claims quoted verbatim (FR-004) and neither side labeled a platform fact, so the conflict occupies a home consistent with the four statement classes (FR-006, SC-003, which admit no separate "unresolved" class) rather than a silent or unclassifiable state.
- **FR-006**: The record MUST visibly separate four statement classes — platform fact, reasonable inference, proposed SpecKit Pro policy, and unverified assumption — using official Anthropic documentation as the only source for platform facts.
- **FR-007**: The record MUST NOT claim any head-to-head benchmark result or native fallback feature that is not documented.
- **FR-008**: The record MUST record the undocumented behavior that occurs when agent frontmatter names an unavailable model as a mandatory capability (probe) question, never as an assumed behavior. Likewise, the undocumented execution-time manifestation of alias re-pointing — whether a shipped alias that has re-pointed to a new resolved model ID is silently used at run time, hard-errors, or is otherwise handled — MUST be recorded as a mandatory capability (probe) question, distinct from and additional to alias re-pointing's role as a recorded invalidation trigger (FR-014); it MUST NOT be assumed.
- **FR-009**: The manifest MUST pin the immutable production comparator to the latest published speckit-pro release tag at research time (2.19.1) plus its commit SHA.
- **FR-010**: For each of the eleven current agents, the manifest MUST record the current frontmatter route tuple (model and effort) together with content hashes of the agent file for drift detection; the net-new helper's production route MUST be recorded as explicitly absent.
- **FR-011**: The manifest MUST define instruction identity for each agent as the sha256 over the frontmatter-stripped agent body and MUST record the full-file sha256 alongside, so that a pure frontmatter route change does not change the instruction identity. Every hash the manifest records — the FR-010 content hashes, this instruction sha256, and the full-file sha256 — MUST be computed over the agent file's bytes as published at the pinned comparator tag (`speckit-pro-v2.19.1`, commit `e343aa2e4ebcb2d48c501f285d7072cfd55722da`), not the working-tree copy, so each recorded hash provably represents the immutable comparator and is reproducible from the tag by any consumer. The sole exception is `autopilot-fast-helper`, which has no Claude agent file at the tag: its full-file sha256 is computed over the pinned Codex source toml bytes, and its instruction sha256 over the contract-equivalent translated Claude body recorded in the manifest's `platform_field_mapping` (reproducible by re-hashing that string), recorded via `hash_source: codex-toml-translation`.
- **FR-012**: Candidates MUST be identified by the four documented aliases (opus, sonnet, haiku, fable), each with its expected resolved model ID recorded alongside; legacy dated model snapshots MUST NOT be enumerated as separate candidates.
- **FR-013**: `fable` MUST enter executor-class candidate sets and MUST be excluded only by recorded probe or contract evidence, never by product-announcement status.
- **FR-014**: For each of the twelve agents, the manifest MUST record the immutable production route or its recorded absence; every candidate model/effort tuple with both the shipped alias and the expected resolved model ID; required model, modality, subagent-field, tool, skill, and client capabilities; `agent_contract_id`; prompt/instruction hash; candidate rationale; known incompatibilities; required qualification artifacts; and invalidation triggers. The recorded invalidation triggers MUST be candidate-specific and actionable, not boilerplate: for every distinct candidate alias in the entry the triggers MUST include that alias re-pointing to a new resolved model ID, and the triggers MUST include the agent's recorded comparator source drifting from its content hash — for the eleven current agents the agent `.md` frontmatter route/body, and for `autopilot-fast-helper` (which has no Claude `.md`) the Codex source toml plus the contract-equivalent translated body. A single generic trigger that names no specific alias or drift condition does not satisfy this requirement.
- **FR-015**: The manifest MUST distinguish project-level candidate eligibility from environment-time availability.
- **FR-016**: A model or effort MUST be excluded from a candidate set only for recorded incompatibility, recorded contract failure, or predeclared dominance evidence.
- **FR-017**: The `autopilot-fast-helper` contract MUST be derived from `speckit-pro/codex-agents/autopilot-fast-helper.toml` as a contract-equivalent translation — carrying the role prose, bounded jobs, hard rules, and output formats — accompanied by an explicit platform-field mapping table. The mapping table MUST be source-complete: every field present in the source toml (for example `model`, `sandbox_mode`, and the `developer_instructions` contract content) MUST appear as a mapping row, either mapped to its Claude equivalent or explicitly marked as having no Claude equivalent (with the proposed-policy label per FR-018); no source field may be silently omitted.
- **FR-018**: Claude-only helper fields with no Codex equivalent (for example `maxTurns`) MUST carry proposed values labeled "proposed SpecKit Pro policy", deferred to CAR-010 for finalization.
- **FR-019**: The record MUST include a fixture backlog with a requirements-level entry per agent — role contract to exercise, representative task types, required evidence (tool surface, mutation boundary, output format), and a pass/fail signal sketch — and MUST NOT contain full fixture specifications.
- **FR-020**: The record MUST label the current Layer 6 Claude evaluation path (a frontmatter-stripped agent body piped to `claude -p --model`) as bare prompt emulation and MUST label all historical Layer 6 results as `non_release_evidence`. The label MUST be recorded as lifted only by a CAR-003 replay through the shared materializer with exact treatment — the required tool surface, mutation contract, dispatch context, and telemetry proof (AC-1.7) — with CAR-001 itself claiming no such replay and recording that bare prompt emulation is smoke-only evidence that cannot support release.
- **FR-021**: The record MUST assign stable IDs (`CAP-Q1`…`CAP-Qn`) to capability questions in a dedicated section and MUST present the go/no-go handoff to CAR-002 as the record's final section.
- **FR-022**: The go/no-go handoff MUST enumerate the provisional candidate-route manifest, the role-contract catalog, the fixture backlog, the telemetry requirements (as defined in FR-026), the unresolved capability questions, and the go/no-go decision, and MUST NOT depend on CAR-002 results or claim any candidate is executable before capability probing.
- **FR-023**: When a mandatory fact remains unverified at the end of the single autopilot run, it MUST be recorded as a no-go item or a capability question rather than extending the timebox.
- **FR-024**: The work MUST NOT change any agent frontmatter, prompt, generated payload, or shipped default, and no artifact MUST land under speckit-pro/'s allowlisted payload directories.
- **FR-025**: Any hash or content-identity computation MUST use the Python 3.11+ standard library only and MUST introduce no new Bash.
- **FR-026**: The record MUST state the telemetry requirements CAR-002's evaluation must later satisfy — the non-interactive (`claude -p --output-format json`) telemetry fields each role's qualification needs, derived from the recorded non-interactive-telemetry platform facts (FR-004) and labeled by necessity (mandatory, derived-from-configuration, or platform-unavailable, e.g. effective reasoning effort as a field not documented on the `-p` result surface — sourced out-of-band via OpenTelemetry or derived from configuration). CAR-001 states these requirements only; it MUST NOT build CAR-002's telemetry capability profile. This content is what the go/no-go handoff enumerates as "telemetry requirements" (FR-022).
- **FR-027**: For candidate identification, CAR-001 records model/effort candidate tuples only (FR-012, FR-014); AC-1.3's "prompt/context candidates when justified" are deferred to CAR-003's prompt/context-interaction stage, because none are justified before capability probing and measured-overhead evidence exist. The record MUST note this deferral explicitly so the AC-1.3 clause has a recorded disposition rather than a silent omission.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process — a Markdown research record plus a JSON research manifest, both under `docs/ai/research/`.
- **Secondary surfaces, if any**: N/A. The spike is read-only with respect to the plugin; it adds no production code and touches nothing under speckit-pro/'s allowlisted payload directories.
- **Projected reviewable LOC**: Two research-spike documents (record + manifest), sized by timebox rather than code LOC. Slice estimator advisory: `{estimated_loc: 0, suggested_slices: 1, status: ok}` (spike flag). Expected order of magnitude is roughly 1,000–1,600 lines of prose and structured data across the two artifacts; zero production-code LOC.
- **Projected production files**: 0 production-code files.
- **Projected total files**: 2 new deliverable files (the research record and the JSON manifest). Any transient hashing helper used during the run is not a committed deliverable.
- **Budget result**: within budget.
- **Split decision**: Remains one spec. The estimator returned `suggested_slices: 1` with the spike flag; the deliverable is a single coherent baseline-and-handoff whose go/no-go section would be fractured by a split. Downstream work is already sliced as CAR-002 through CAR-011.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, and rollback
  or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Research Record**: the dated, cited human-readable Markdown deliverable; holds the agent inventory and route-policy surface inventory, the primary-source fact table with statement-class labels, the fixture backlog, the capability-question list, and the go/no-go handoff.
- **Candidate Route Manifest**: the versioned machine-readable JSON deliverable that CAR-002, CAR-003, and CAR-006 bind to programmatically; keyed by the twelve named agents.
- **Agent Route Entry**: the per-agent record within the manifest — immutable production route (or recorded absence), role contract, candidate tuples, required capabilities, `agent_contract_id`, instruction/prompt hash, rationale, known incompatibilities, required qualification artifacts, and invalidation triggers.
- **Candidate Route Tuple**: an (alias, expected resolved model ID, effort) combination eligible for an agent's role, with project-level eligibility recorded separately from environment-time availability.
- **Primary-Source Fact Row**: a documented platform fact carrying a source URL, an access date, and a short verbatim quote from official Anthropic documentation.
- **Capability Question**: a stable-ID (`CAP-Qn`) unresolved question handed to CAR-002 for probe design.
- **Immutable Production Comparator**: the pinned baseline — release tag 2.19.1 plus commit SHA, plus the eleven current agents' frontmatter route tuples and agent-file content hashes.
- **Fixture Backlog Entry**: a requirements-level per-agent sketch — role contract to exercise, representative tasks, required evidence, and a pass/fail signal.
- **autopilot-fast-helper Contract**: the net-new twelfth agent contract, a contract-equivalent translation of the Codex helper toml with an explicit platform-field mapping table and no current Claude production route.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All twelve named agents have a complete manifest entry — 100% coverage with zero agents missing any required field (immutable production route or recorded absence, at least one candidate tuple, required capabilities, `agent_contract_id`, instruction hash, rationale, known incompatibilities, required qualification artifacts, and invalidation triggers).
- **SC-002**: 100% of recorded platform facts carry a source URL, an access date, and a short verbatim quote; zero platform facts rest on paraphrase or uncited assertion.
- **SC-003**: Every statement in the research record is classifiable into exactly one of the four labels (fact, inference, proposed policy, assumption); a reviewer can determine each statement's class without ambiguity.
- **SC-004**: A CAR-002 implementer can freeze the project-eligible candidate set and design the capability probes using only the record and manifest, without re-deriving any role contract or re-reading agent source — verified by the go/no-go handoff being self-contained and listing no dependency on CAR-002 results. Executability itself follows successful probing and CAR-003 qualification, never from these artifacts alone.
- **SC-005**: The spike completes in a single autopilot run, and every mandatory fact left unverified appears as a stable-ID capability question or a no-go item in the handoff — zero silent gaps.
- **SC-006**: Zero shipped bytes change — no file under speckit-pro/'s allowlisted payload directories is added, modified, or removed by the spike — and the repository default suite (`python3 tests/speckit-pro/run-all.py`) still passes with zero failures.
- **SC-007**: A pure frontmatter route change to any agent leaves that agent's recorded instruction identity (the frontmatter-stripped-body sha256) unchanged, demonstrable by recomputation.
- **SC-008**: The produced manifest is well-formed JSON and validates against `contracts/agent-route-candidate-manifest.schema.json` with zero schema violations — parseable by a standard JSON parser and conformant to every required field, enum, pattern, and conditional constraint the contract declares.

## Assumptions

- The latest published speckit-pro release tag at research time is 2.19.1 (the 2.19.0 named at scaffold time on 2026-07-13 was superseded by the 2.19.1 patch release published later that day; `speckit-pro/agents/*.md` and `speckit-pro/codex-agents/` are byte-identical between the two tags, so route tuples and content hashes are unchanged); the autopilot run records the exact tag and the commit SHA it pins as the comparator.
- Official Anthropic documentation is reachable during the run to source and quote platform facts; where a needed binding (for example an alias-to-resolved-ID mapping) is not documented, it is recorded as a capability question rather than a fact.
- The eleven current Claude agents are those under `speckit-pro/agents/*.md` at the pinned comparator; the twelfth agent, `autopilot-fast-helper`, has no current Claude production route and derives from `speckit-pro/codex-agents/autopilot-fast-helper.toml`.
- Hash computation uses the Python 3.11+ standard library only (no new Bash and no third-party dependency).
- The JSON manifest produced here is provisional research output under `docs/ai/research/`, not the plugin-owned route-policy manifest, which is CAR-006's artifact.
- The executor-class set for which `fable` is candidate-eligible comprises the agents whose role is task execution; the record names those agents explicitly.
- Downstream specs CAR-002 through CAR-011 consume these artifacts; this spec depends on none of their results.
