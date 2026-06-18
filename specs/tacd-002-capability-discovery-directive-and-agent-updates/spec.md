# Feature Specification: TACD-002 Capability Discovery Directive and Agent Updates

**Feature Branch**: `tacd-002-capability-discovery-directive-and-agent-updates`

**Created**: 2026-06-18

**Status**: Draft

**Input**: User description: "Apply TACD-001's tool-agnostic capability-discovery decision to active SpecKit Pro Claude and Codex runtime guidance. Keep TACD-003 prerequisite and user-facing messaging, and TACD-004 enforcement and evals, out of scope."

## Clarifications

### Session 2026-06-18 - Directive Home And Pointer Resolution

- Q: What is the exact shared directive path? A:
  `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`
  is the durable source directive path for TACD-002.
- Q: Which active surfaces are in scope for directive pointers or equivalents?
  A: Six active Claude Markdown agents
  (`codebase-analyst`, `domain-researcher`, `clarify-executor`,
  `checklist-executor`, `analyze-executor`, `implement-executor`), the six
  matching Codex TOML agents under `speckit-pro/codex-agents/`, and narrow
  active reference pointers in `speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md`
  and `speckit-pro/skills/speckit-autopilot/references/gate-validation.md`.
- Q: Which runtime-specific equivalents are acceptable? A: Claude agents and
  shared skill references should point to the shared directive; Codex skill
  references may use payload-builder-rewritten paths; installed Codex TOML
  agents may embed a compact equivalent with a source-note marker when direct
  Markdown pointer resolution would break after install.
- Q: How is pointer resolution verified before TACD-004 enforcement? A:
  TACD-002 records ad hoc evidence only: directive file exists, payload refresh
  runs, source and generated payload surfaces contain the pointer or equivalent
  marker, and the default suite passes. New deterministic enforcement remains
  deferred to TACD-004.

### Session 2026-06-18 - Metadata And Generated Payloads

- Q: Which exact IDs remain as runtime/dependency metadata? A: Preserve Codex
  dependency values such as `tavily` and `context7` in
  `speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml`, and preserve
  Claude agent frontmatter `tools:` allowlist IDs such as
  `mcp__RepoPrompt__*`, `mcp__tavily-mcp__*`, and `mcp__context7__*`.
  Rewrite body prose and Codex TOML developer instructions that describe named
  optional tools as preferred behavior.
- Q: What evidence proves preserved IDs are metadata rather than active
  preferred-tool behavior? A: The PR packet must include a preserved-ID review
  table with file, field, classification, and behavior-scan result. Metadata
  fields include Codex `agents/openai.yaml` dependency values, Claude
  frontmatter `tools:` allowlists, and generated manifest/path rewrites. Body
  text and Codex TOML developer instructions are behavior surfaces.
- Q: Which existing command refreshes generated payloads from source? A:
  `bash scripts/build-plugin-payloads.sh` refreshes both
  `dist/claude/speckit-pro` and `dist/codex/speckit-pro` from source.
- Q: How is source-derived generated payload evidence proved? A: Record the
  builder invocation, verify both payload roots were generated, review paired
  source and `dist/**` diffs, run `bash tests/speckit-pro/run-all.sh`, and
  ensure a second rebuild produces no unintended additional payload changes.

### Session 2026-06-18 - Fallback Evidence Language

- Q: What exact evidence wording should discovery-informed answers use? A:
  Use the compact evidence note `Capability path: <need> -> <selected capability/source>; Evidence: <citations or local file refs>; Confidence: <high|medium|low> (<brief reason>)`.
- Q: How should agents describe fallback when no installed capability covers a
  need? A: Continue with local, native platform, or repo-local evidence and
  disclose lower confidence using `No installed <capability> was available/usable; used <local/native/repo-local fallback>; confidence is <medium|low> because <reason>.`
- Q: How should guidance avoid full installed-tool inventories in normal
  answers? A: Report only the selected capability path and any material
  fallback gap. Full inventories are allowed only when directly requested,
  needed for troubleshooting, or required as PR evidence such as preserved-ID
  review tables.
- Q: How can formerly named tools still be selected without being privileged?
  A: Treat them as ordinary installed capabilities and name them only when
  actually selected by discovery, or when preserved as metadata, historical
  provenance, or other non-behavior evidence.
- Q: How should guidance avoid replacing named-tool preference with a fixed
  vendor-neutral fallback chain? A: Treat capability categories as a taxonomy,
  not an ordered chain. Guidance must identify the task need first, then choose
  among installed matches by fit and evidence quality; only after no installed
  match is available or usable may it fall back to local, native platform, or
  repo-local evidence with lower-confidence disclosure.
- Q: Should scoped autopilot references replace named preferred-tool rows with
  capability-first pointers? A: Yes. Narrowly update active behavior pointers in
  `consensus-protocol.md` and `gate-validation.md` to point at the shared
  directive or use capability categories; do not rewrite TACD-003 prerequisite
  docs or TACD-004 enforcement.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agents Choose By Capability Need (Priority: P1)

As an operator with one or more optional research or context capabilities installed, I want SpecKit Pro agents to select capabilities by task need instead of preferring a named vendor-specific MCP set.

**Why this priority**: This is the core TACD-002 behavior change and removes active preferred-tool wording from runtime guidance.

**Independent Test**: Review updated active Claude and Codex guidance for a research/context task and confirm the agent instructions select a capability category first, then choose the best installed matching capability.

**Acceptance Scenarios**:

1. **Given** an active agent instruction that previously preferred a named optional research or context tool, **When** TACD-002 guidance is applied, **Then** the instruction describes the needed capability category instead of privileging that named tool.
2. **Given** multiple installed capabilities can satisfy a research/context need, **When** an agent follows the updated guidance, **Then** it chooses the best fit for the task and records the capability path used.

---

### User Story 2 - Agents Work Without Optional Capabilities (Priority: P1)

As an operator without optional research or context capabilities installed, I want agents to keep working by using transparent lower-confidence fallback evidence.

**Why this priority**: Tool-agnostic behavior must not make optional integrations prerequisites for normal agent operation.

**Independent Test**: Inspect the updated guidance for a no-optional-capability environment and confirm it instructs agents to use local files, native platform context, or repo-local helpers with confidence disclosure.

**Acceptance Scenarios**:

1. **Given** no optional research or context capability is available, **When** an agent needs evidence, **Then** it falls back to local files, platform context, or repo-local helpers instead of failing solely because the optional capability is missing.
2. **Given** an answer relies on fallback evidence, **When** the agent reports the result, **Then** it includes the capability path, local file references or citations, and a confidence level.

---

### User Story 3 - Runtime Guidance Stays Semantically Aligned (Priority: P2)

As a maintainer, I want Claude and Codex guidance to share one semantic directive or approved equivalent so runtime behavior does not drift.

**Why this priority**: TACD-001 selected a shared directive pattern, and TACD-002 must apply it consistently across active runtime surfaces.

**Independent Test**: Compare the relevant Claude and Codex guidance surfaces and confirm each points to the shared directive or carries an approved runtime-specific equivalent with matching behavior requirements.

**Acceptance Scenarios**:

1. **Given** a Claude agent and a Codex agent both perform research/context discovery, **When** their updated guidance is reviewed, **Then** both express the same capability-first discovery semantics.
2. **Given** a runtime cannot resolve the shared directive directly, **When** its guidance is updated, **Then** it carries an approved equivalent without changing the behavior contract.

---

### User Story 4 - Generated Payloads Match Source Guidance (Priority: P2)

As a maintainer, I want generated Claude and Codex payloads refreshed from source so installed artifacts match source guidance.

**Why this priority**: Active installed behavior depends on generated payload copies, but source guidance must remain authoritative.

**Independent Test**: Run the documented payload refresh path after source edits and verify generated payload diffs match source-derived changes without hand-editing `dist/**` as the durable source.

**Acceptance Scenarios**:

1. **Given** source guidance changes under `speckit-pro/`, **When** the payload refresh path runs, **Then** generated Claude and Codex payload copies reflect those source changes.
2. **Given** generated payload files differ after refresh, **When** the diff is reviewed, **Then** each generated change can be traced back to source guidance or generation metadata rather than a direct manual payload-only edit.

---

### Edge Cases

- Runtime or dependency metadata requires exact tool or capability IDs; TACD-002 preserves those IDs unless a generic equivalent is proven.
- Historical archive, changelog, or provenance text mentions older named tools; TACD-002 keeps those references when they are clearly historical rather than active behavior guidance.
- A formerly named optional tool is the best installed capability for a task; agents may still use it through capability discovery without treating it as preferred by default.
- A target runtime cannot follow a shared Markdown pointer from its installed context; installed Codex TOML agents may include a compact approved equivalent with a source-note marker that preserves the same semantic directive.
- Generated `dist/**` payloads are stale after source edits; implementation must refresh them through the repository's generation path.
- A narrow behavior pointer touches setup or limitation wording; the change must stay behavior-only and avoid TACD-003 prerequisite messaging.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Active agent behavior guidance MUST express research and context selection as capability categories rather than preferred named optional MCP tool sets.
- **FR-002**: The capability categories MUST cover codebase context, spec context, library documentation, web or domain research, source extraction, installed skills/plugins, and repo-local helpers.
- **FR-003**: Active Claude guidance surfaces in TACD-002 scope MUST point to `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` or include an approved equivalent with the same behavior contract.
- **FR-004**: Active Codex guidance surfaces in TACD-002 scope MUST point to the shared directive when path resolution is stable; generated Codex skill payloads MAY use rewritten pointer paths, and installed Codex TOML agents MAY embed a compact equivalent with the exact source-note marker `Capability discovery equivalent: mirrors speckit-pro/skills/speckit-autopilot/references/capability-discovery.md for installed Codex TOML runtime.` when direct pointer resolution would break.
- **FR-005**: Agent guidance MUST instruct agents to choose the best installed capability for the task need before falling back to local or native platform evidence. When multiple installed capabilities can satisfy the same need, guidance MUST select by task fit, source authority/directness, freshness needs, expected evidence quality, and minimal necessary inventory disclosure; it MUST NOT encode a fixed tool order or fixed capability fallback chain.
- **FR-006**: Agent guidance MUST preserve normal operation when optional installed capabilities are missing, unavailable, or present but unusable by allowing local files, platform context, and repo-local helpers as fallback evidence.
- **FR-007**: Agent outputs informed by research or context discovery MUST report `Capability path: <need> -> <selected capability/source>; Evidence: <citations or local file refs>; Confidence: <high|medium|low> (<brief reason>)`. When fallback evidence is used because no installed capability is available or usable, confidence MUST be `medium` or `low`, not `high`.
- **FR-008**: Agent guidance MUST avoid dumping full installed-tool inventories in normal answers unless inventory details are directly requested, needed for troubleshooting, or required as PR evidence.
- **FR-009**: Formerly named optional tools MAY remain usable when selected through capability discovery, but MUST NOT be described as default preferred capabilities; selected tools may be named in the capability path only when actually selected.
- **FR-010**: Schema-required runtime or dependency metadata IDs MUST be preserved unless TACD-002 provides evidence that a generic equivalent is valid for that schema; preserved IDs MUST be classified separately from active behavior guidance.
- **FR-011**: Historical archive, changelog, and provenance references MUST remain when clearly classified as historical and not active behavior guidance.
- **FR-012**: Generated `dist/**` payloads MUST be refreshed from source through `bash scripts/build-plugin-payloads.sh` rather than hand-edited as the source of truth.
- **FR-013**: TACD-002 MUST NOT replace prerequisite checks, public setup messaging, or plugin limitation documentation except for narrow agent behavior pointers needed by this feature.
- **FR-014**: TACD-002 MUST NOT add final deterministic or eval enforcement owned by TACD-004.
- **FR-015**: The PR review packet MUST trace major directive and agent-guidance changes to changed files, generated payload refresh evidence, and verification results.

### Reviewability Notes *(if applicable)*

- Preserve the accepted setup warning from `docs/ai/specs/.process/TACD-002-design-concept.md`: TACD-002 proceeds despite more than one setup primary surface because the slice is intentionally limited to active docs/process behavior guidance, generated payload refresh, zero projected production files, and no TACD-003 or TACD-004 implementation.
- Exact runtime/dependency identifiers are not reviewability exceptions when they are schema-required metadata rather than active preferred-tool guidance.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: harness/adapter for generated payload refresh only
- **Projected reviewable LOC**: 202 setup estimate; implementation should remain near or below this unless Clarify records a narrower target-surface decision
- **Projected production files**: 0
- **Projected total files**: 7 setup estimate
- **Budget result**: warning accepted
- **Split decision**: Remains one spec because TACD-002 is the active agent-behavior guidance slice. TACD-003 owns prerequisite and user-facing messaging, and TACD-004 owns final enforcement and evals.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- The PR packet MUST include a preserved-ID table covering concrete runtime/dependency IDs that remain in metadata fields.
- Generated payload evidence MUST include the payload builder command, source-to-`dist/**` diff review, and default-suite verification.
- Evidence wording changes MUST be traceable to the shared directive, active guidance surfaces, and any generated payload changes.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Capability Discovery Directive**: The shared semantic behavior contract at `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` that tells agents how to select research/context capabilities by need, report evidence, and handle fallback.
- **Runtime Guidance Surface**: An active Claude or Codex agent/skill instruction file that controls installed agent behavior, including the six TACD-002-scoped Claude agents, six matching Codex TOML agents, and narrow active autopilot references named in Clarifications.
- **Capability Path Report**: The output evidence element naming the path used to gather context, such as installed capability, local file, platform context, or repo-local helper.
- **Fallback Evidence Disclosure**: The confidence-lowering note agents use when no installed capability covers a need and local, native platform, or repo-local evidence is used instead.
- **Generated Payload Copy**: A `dist/**` runtime artifact refreshed from source guidance for installation or marketplace packaging through `bash scripts/build-plugin-payloads.sh`.
- **Schema Metadata ID**: A required runtime or dependency identifier that may name a tool or capability without expressing preferred behavior; examples include Codex dependency values, Claude frontmatter `tools:` allowlist IDs, and generated manifest/path rewrite metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Active TACD-002-scoped behavior guidance contains no preferred named optional MCP wording except when the reference is metadata, historical, provenance, or explicitly selected through capability discovery.
- **SC-002**: Every TACD-002-scoped Claude and Codex guidance surface points to the shared directive at `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` or carries an approved equivalent with matching capability-first semantics.
- **SC-003**: Updated guidance covers both optional-capability-present and no-optional-capability fallback paths, including the compact capability path, evidence, and confidence wording from Clarifications.
- **SC-004**: Generated Claude and Codex payload copies can be shown to be refreshed from source guidance through the repository's generation path.
- **SC-005**: Preserved exact runtime/dependency IDs are documented as schema-required metadata, historical references, provenance, or otherwise non-preferential behavior.
- **SC-006**: The final TACD-002 diff does not implement TACD-003 prerequisite/user-facing messaging or TACD-004 deterministic/eval enforcement.

## Assumptions

- TACD-001 is complete and archived, and TACD-002 may rely on its selected capability-discovery direction.
- Clarify will resolve metadata evidence, generated payload refresh command, and fallback confidence phrasing before planning; the directive path, initial target surface list, runtime-specific equivalent policy, and pre-enforcement pointer verification approach were resolved in Clarify Session 2026-06-18.
- Existing repository scripts and structural tests are sufficient for Specify-phase validation; new deterministic enforcement belongs to TACD-004.
- Generated `dist/**` payloads are install-facing artifacts and source guidance under `speckit-pro/` remains authoritative.
