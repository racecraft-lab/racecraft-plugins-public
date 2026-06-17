# Feature Specification: Platform Mechanics Spike

**Feature Branch**: `tacd-001-platform-mechanics-spike`

**Created**: 2026-06-17

**Status**: Draft

**Input**: User description: "Platform Mechanics Spike for tool-agnostic capability discovery across Claude Code and Codex, producing a research report plus appendix probes without changing shipped behavior."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Audit Named-Tool References (Priority: P1)

As a maintainer, I can read a spike report that inventories current optional research/context tool references and separates active guidance from historical or provenance references.

**Why this priority**: TACD-002 cannot safely rewrite active guidance until maintainers know which current references are active runtime behavior, user-facing messaging, dependency metadata, deterministic expectations, historical records, or fixtures.

**Independent Test**: Review the spike report and confirm every audited named-tool reference is listed with a category, source path, line context, and rationale.

**Acceptance Scenarios**:

1. **Given** the repository contains references to optional tools such as Tavily, Context7, RepoPrompt, MCP, or app connectors, **When** a maintainer opens the report, **Then** each in-scope reference is classified with evidence from the local repository.
2. **Given** a reference appears only in changelogs, archives, provenance, or intentionally historical fixtures, **When** the report classifies it, **Then** it is clearly marked as historical/provenance or fixture/test-only and is not treated as active guidance to remove in TACD-001.
3. **Given** a reference appears in active agent, skill, prerequisite, docs, metadata, or eval surfaces, **When** the report classifies it, **Then** the report identifies whether later work should rewrite, preserve, or test that category.

---

### User Story 2 - Recommend Directive Home (Priority: P2)

As a TACD-002 implementer, I can see a recommendation for where the capability-discovery directive should live and the evidence behind that recommendation.

**Why this priority**: The next behavior-changing slice needs a defensible choice between a shared reference plus per-agent pointers and runtime-specific equivalents.

**Independent Test**: Review the recommendation section and verify it explains the Claude Code and Codex mechanics, the proof bar, and the reason the preferred directive home is or is not viable.

**Acceptance Scenarios**:

1. **Given** both Claude Code and Codex need capability-first discovery, **When** the implementer reads the report, **Then** the report explains how each runtime can direct agents to discover installed tools, MCP/app connectors, skills/plugins, and repo-local helpers.
2. **Given** a shared directive reference plus per-agent pointers is preferred only if it can be validated reliably, **When** the report recommends a directive home, **Then** it states the static checks and planned eval scenarios needed to prove coverage.
3. **Given** one runtime cannot reliably consume a shared directive pointer, **When** the report makes its recommendation, **Then** it recommends a runtime-specific equivalent and explains the evidence gap.

---

### User Story 3 - Define TACD-004 Enforcement Categories (Priority: P3)

As a TACD-004 test author, I can use the report's active-vs-historical categories and eval-plan recommendations to write deterministic checks and functional evals without over-banning legitimate historical text.

**Why this priority**: Future enforcement should prevent new vendor-specific active guidance while preserving useful provenance and intentionally historical fixtures.

**Independent Test**: Use the report's category table to draft a deterministic allowlist and confirm each proposed check has clear allowed and disallowed categories.

**Acceptance Scenarios**:

1. **Given** TACD-004 must enforce vendor-neutral active guidance later, **When** a test author reads the report, **Then** the report identifies exact categories that should be blocked, allowed, or reviewed.
2. **Given** live AI evals are out of scope for TACD-001, **When** the test author reads the eval-plan section, **Then** the report describes functional eval scenarios without requiring those evals to run in TACD-001.
3. **Given** historical references may remain, **When** deterministic checks are designed from the report, **Then** the allowlist protects changelogs, archive records, provenance, and intentionally historical fixtures from false positives.

### Edge Cases

- A named-tool reference appears in generated or distributed payloads as copied source content; the report must classify the reference by whether that payload is active shipped guidance, generated evidence, or historical fixture material.
- A runtime mechanic cannot be established from local source inspection alone; the report must record a minimal reproducible probe command/result or label the mechanic as unresolved.
- A source path includes both active guidance and historical notes; the report must classify findings at the reference level, not only at the file level.
- A current official platform document is needed to establish runtime mechanics; the report must cite the official source and keep the decision grounded in the report.
- The audit finds no active reference in a requested surface; the report must record the surface as checked instead of silently omitting it.
- A concrete tool ID appears in a runtime schema, agent `tools` allowlist, MCP invocation field, or Codex dependency metadata; the report must classify it as runtime/dependency metadata and not as prose preference unless surrounding guidance makes a named-tool recommendation.
- Generic platform vocabulary such as "MCP", "app connector", or "installed tool" is not itself a named-tool finding unless it is tied to a concrete vendor/server list or creates a prerequisite expectation.
- A runtime-capability probe emits machine-specific or sensitive inventory details; the report must publish only a sanitized summary and keep any raw capture transient and uncommitted.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: TACD-001 MUST produce `docs/ai/research/tool-agnostic-capability-discovery-spike.md` as the canonical report and decision record.
- **FR-002**: The report MUST audit active references to optional research/context tools across Claude agents, Codex agents, autopilot skills and references, prerequisite scripts, plugin limitation documents, dependency metadata, and tests/evals.
- **FR-003**: Each audited finding MUST include a source path, line context, named capability or tool reference, classification, and rationale; generic capability-class language is audited only when tied to concrete named tools or prerequisite expectations.
- **FR-004**: The report MUST classify findings as active runtime guidance, active runtime/dependency metadata, prerequisite/user-facing messaging, deterministic/eval expectation, dependency metadata, historical/provenance, fixture/test-only, generated source-derived duplicate, or explicitly out of scope.
- **FR-005**: The report MUST verify both Claude Code and Codex mechanics for directing agents to discover installed tools, MCP/app connectors, skills/plugins, and repo-local helpers.
- **FR-006**: Where runtime mechanics cannot be established from source inspection alone, the report MUST include reproducible probe commands and observed results in an appendix.
- **FR-006a**: The platform-mechanics section MUST use a runtime-by-capability matrix covering Claude Code and Codex against installed tools, MCP/app connectors, skills/plugins, and repo-local helpers, with each cell marked source-backed, probe-backed, unsupported, unresolved, or environment-specific.
- **FR-006b**: Probe appendix entries MUST include the command or inspection method, purpose, sanitized observed result, reviewer-facing conclusion, and whether the evidence is source-backed, probe-backed, unsupported, unresolved, or environment-specific.
- **FR-006c**: The report MUST define and apply a confidence rubric for each runtime-by-capability matrix cell and Capability Mechanics Evidence record. Confidence measures how strongly the evidence supports the mechanics conclusion, not whether a named tool is preferred. The rubric MUST cover source-backed, probe-backed, environment-specific, unsupported, and unresolved evidence states; `high` requires direct active source or sanitized probe evidence with no known conflict, `medium` covers indirect, partial, template-only, or condition-dependent evidence, and `low` covers missing, conflicting, ambiguous, or local-only evidence. `unresolved` mechanics MUST always be low confidence and name the missing evidence plus downstream owner or reviewer decision needed.
- **FR-007**: The report MUST recommend the directive home: shared reference plus per-agent pointers only when both static pointer coverage and planned functional eval coverage are defined for Claude Code and Codex; otherwise it MUST recommend a runtime-specific equivalent.
- **FR-008**: The report MUST define exact active-vs-historical named-tool categories that TACD-004 should enforce later.
- **FR-009**: The report MUST recommend deterministic checks and functional eval-plan scenarios for TACD-004 without adding final enforcement tests in TACD-001, including checks for pointer coverage, pointer target resolution from Claude and Codex locations, approved runtime-specific equivalents, and active named-tool prose outside approved categories.
- **FR-009a**: TACD-004 eval-plan recommendations MUST cover both Claude and Codex paths for vendor-neutral optional-tool setup, missing-capability fallback, installed-capability selection without vendor preference, capability path/citations/confidence reporting, and directive application in a research or codebase-context task.
- **FR-009b**: TACD-004 functional eval-plan recommendations MUST include behavior-observable assertions, not only pointer coverage or pointer-target resolution. Each planned eval scenario MUST specify runtime, setup assumption, task prompt shape, expected observable response behavior, required response evidence, and failure signals. The assertions MUST cover capability-first selection without named optional-tool preference, use or acknowledgement of a scenario-declared installed capability when available, graceful fallback when absent, capability path plus citations or local files plus confidence reporting, and directive application during at least one research or codebase-context task for both Claude Code and Codex. TACD-001 MUST only document these planned scenarios and MUST NOT add, update, or execute final TACD-004 eval tests.
- **FR-010**: The report MUST identify handoffs to TACD-002, TACD-003, and TACD-004, including what each later slice should change or validate; prerequisite and user-facing named-tool messaging belongs to TACD-003, while behavior-changing agent guidance belongs to TACD-002.
- **FR-011**: TACD-001 MUST NOT rewrite active agent guidance, prerequisite behavior, public docs messaging, final test expectations, plugin versions, or generated payload semantics.
- **FR-012**: TACD-001 MUST use local repository evidence first and cite official platform sources only when current platform mechanics cannot be established locally.
- **FR-013**: The report MUST label unresolved mechanics or ambiguous categories explicitly instead of converting uncertainty into implementation assumptions.
- **FR-013a**: For each runtime-by-capability matrix cell, the report MUST record the expected report-level disposition when the capability is absent, unsupported, unavailable, or unverified: documented fallback path, explicit unsupported state, explicit unresolved state, or downstream owner decision needed. TACD-001 MUST NOT implement or change that fallback behavior.
- **FR-013b**: If a named-tool reference could reasonably be active guidance, runtime/dependency metadata, historical/provenance, generated duplicate, or fixture-only, the report MUST classify it as `ambiguous/requires-review` with low confidence until source evidence resolves the category; it MUST NOT silently choose the more convenient category.
- **FR-014**: TACD-001 MUST preserve historical references in changelogs, archives, provenance records, and intentionally historical fixtures.
- **FR-015**: TACD-001 MUST NOT commit raw runtime inventories, raw transcripts, session IDs, request IDs, absolute machine paths, full tool/plugin/MCP inventories, connector lists, access tokens, usage/quota/cost fields, or other environment-specific identifiers.
- **FR-016**: Claude Code mechanics evidence MUST distinguish declared agent/plugin surfaces from currently connected parent-session capabilities; Codex mechanics evidence MUST distinguish bundled templates/metadata from installed runtime agents, skills, plugins, and tool-discovery surfaces.

### Reviewability Notes *(if applicable)*

- TACD-001 is a research spike. Any reviewability exception must be limited to process or documentation evidence and must not justify runtime behavior changes.
- Generated payloads may be inspected as evidence, but generated payload semantics must not be edited in this slice.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: N/A
- **Projected reviewable LOC**: 300-600 lines of Markdown research/report content, excluding phase artifacts
- **Projected production files**: 0
- **Projected total files**: 1 canonical report plus appendix content in the same report
- **Budget result**: within budget
- **Split decision**: Keep as one spike slice because the accepted scope is one research report plus appendix probes; behavior changes are explicitly reserved for TACD-002, TACD-003, and TACD-004.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Named-Tool Reference**: A source occurrence naming an optional research/context tool, connector, MCP server, skill/plugin, or repo-local helper capability; generic capability-class wording is excluded unless tied to a concrete tool/server list or prerequisite expectation.
- **Runtime Surface**: A Claude Code or Codex agent, skill, reference, prerequisite message, limitation document, dependency metadata record, generated payload, test, or eval that may influence behavior or expectations.
- **Capability Mechanics Evidence**: Source-backed or probe-backed evidence showing how a runtime can discover and use installed capabilities without a hardcoded vendor list.
- **Runtime-by-Capability Matrix**: A report table that records Claude Code and Codex evidence for installed tools, MCP/app connectors, skills/plugins, and repo-local helpers, with each cell marked source-backed, probe-backed, unsupported, unresolved, or environment-specific and paired with confidence, confidence rationale, and absent-capability disposition.
- **Sanitized Probe Summary**: A report appendix entry that preserves the reproducible command, reduced observed result, and conclusion while excluding raw environment inventories, session/request identifiers, local paths, and connector/tool/plugin lists.
- **Directive-Home Recommendation**: The report decision that chooses shared reference plus pointers or a runtime-specific equivalent.
- **Directive Pointer Coverage**: The set of active Claude agents, Codex agents, relevant skill entrypoints/references, and TACD-004 test/eval expectations that must point to the shared directive or an approved runtime-specific equivalent before shared-reference adoption is considered reliable.
- **Allowlist Category**: A TACD-004 enforcement category that distinguishes active guidance, runtime/dependency metadata, prerequisite/user-facing messaging, deterministic/eval expectations, generated source-derived duplicates, historical/provenance, fixture-only text, and ambiguous references requiring review.
- **Runtime/Dependency Metadata**: A concrete tool ID or dependency entry required by a runtime schema, agent allowlist, MCP invocation contract, or Codex skill/plugin metadata; later specs should preserve it until an equivalent capability-discovery path is proven.
- **Downstream Handoff**: A TACD-002, TACD-003, or TACD-004 action identified by the report for later implementation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of in-scope audited named-tool findings in the report include a source path, line context, classification, and rationale.
- **SC-002**: The report covers both Claude Code and Codex and addresses all four capability classes: installed tools, MCP/app connectors, skills/plugins, and repo-local helpers.
- **SC-003**: The directive-home recommendation includes an explicit pass/fail rationale for shared reference plus per-agent pointers and names the static pointer checks, pointer-target resolution checks, runtime-specific-equivalent rules, and functional eval scenarios needed for validation.
- **SC-004**: TACD-004 receives a complete category set that distinguishes active guidance, runtime/dependency metadata, prerequisite/user-facing messaging, deterministic/eval expectations, generated source-derived duplicates, historical/provenance, fixture/test-only references, and ambiguous references requiring review.
- **SC-005**: The final TACD-001 diff contains no changes to active runtime guidance, prerequisite behavior, public docs messaging, final enforcement tests, plugin versions, or generated payload semantics.
- **SC-006**: Any platform-mechanics probe included in the appendix has enough command/result detail for a reviewer to reproduce it or understand why it is environment-specific.
- **SC-007**: No committed probe evidence contains raw session identifiers, request identifiers, absolute local paths, raw full transcripts, full runtime inventory dumps, access tokens, connector lists, or unsanitized plugin/tool/MCP inventories.
- **SC-008**: 100% of runtime-by-capability matrix cells include an evidence state, confidence level, and one-sentence confidence rationale that follows the report confidence rubric.
- **SC-009**: TACD-004 eval-plan recommendations include observable assertions and failure signals for each Claude Code and Codex scenario, proving behavior beyond pointer presence or target resolution.

## Assumptions

- The existing design concept at `docs/ai/specs/.process/TACD-001-design-concept.md` is the source of truth for TACD-001 scope and confirms a report-plus-probes spike.
- The existing feature directory is `specs/tacd-001-platform-mechanics-spike`; no new branch or feature directory is needed.
- Live AI eval execution is not required for TACD-001; planned eval scenarios are sufficient for the proof bar.
- Local repository evidence is the default source of truth; official platform docs are used only when local files cannot prove current runtime mechanics.
- The spike may inspect generated and distributed files as evidence, but any behavior-changing edits belong to later TACD specs.
- Generated `dist/**` or payload occurrences are audited as source-derived duplicates when they copy active source guidance; later specs should edit source files and rebuild payloads rather than hand-edit generated outputs.
- Source inspection is sufficient when repository files prove a capability path. Appendix probes are needed only when source inspection cannot establish runtime availability, installation state, or discovery mechanics.
