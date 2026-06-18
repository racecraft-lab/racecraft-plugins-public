---
topic: "TACD-002 Capability Discovery Directive and Agent Updates"
slug: "tacd-002-capability-discovery-directive-and-agent-updates"
date: "2026-06-18"
mode: "scaffold"
source_input:
  type: "roadmap-spec"
  ref: "docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md#tacd-002-capability-discovery-directive-and-agent-updates"
question_count: 6
stop_reason: "ready-for-autopilot"
---

# Design Concept: TACD-002 Capability Discovery Directive and Agent Updates

## Source Context

TACD-002 implements the active agent-behavior slice from the Tool-Agnostic
Capability Discovery roadmap. TACD-001 selected a shared
capability-discovery reference with runtime-specific pointers and approved
equivalents. TACD-002 now applies that decision to active Claude and Codex
agent guidance without taking on prerequisite messaging or final enforcement.

Primary inputs:

- `docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md`
- `docs/ai/research/tool-agnostic-capability-discovery-spike.md`
- `docs/prd-tool-agnostic-capability-discovery.md`
- `docs/ai/specs/tool-agnostic-capability-discovery-design-concept.md`

## Goals

- Create or update the shared capability-discovery directive for active runtime guidance.
- Point relevant Claude Markdown agents and Codex TOML agents at the shared directive or a spike-approved equivalent.
- Replace active preferred-tool wording with capability categories: codebase context, spec context, library documentation, web or domain research, source extraction, installed skills/plugins, and repo-local helpers.
- Preserve backward compatibility by allowing formerly named tools to be selected through discovery when they are the best installed capability.
- Require agent outputs informed by research or context discovery to report capability path, citations or local files, and confidence.
- Refresh generated payload copies from source through the existing distribution path instead of hand-editing generated files.

## Non-goals

- Do not rewrite the SpecKit Pro consensus protocol.
- Do not replace prerequisite or user-facing setup messaging; TACD-003 owns that slice.
- Do not add final static/eval enforcement; TACD-004 owns that slice.
- Do not remove historical archive/changelog/provenance references solely because they contain older tool names.
- Do not remove exact runtime or dependency metadata IDs when a platform schema requires them.
- Do not hand-edit generated `dist/**` payload copies as the source of truth.

## Grill Me Decisions

### Q1. What should TACD-002 use as the primary directive structure?

**Answer:** Shared reference.

Use one shared capability-discovery directive and point Claude/Codex surfaces at
it with runtime-specific notes or approved equivalents. This follows TACD-001's
directive-home recommendation and limits semantic drift.

### Q2. What should the first TACD-002 implementation slice prioritize?

**Answer:** Agent guidance.

Update active Claude/Codex agent behavior first. Leave prerequisite messaging,
plugin limitation wording, and public docs advisory language for TACD-003 unless
an agent reference needs a narrow pointer for behavior.

### Q3. How should TACD-002 treat exact tool IDs in runtime/dependency metadata?

**Answer:** Preserve metadata where schemas require it.

Remove preferred-tool behavior wording, but keep exact IDs when runtime schemas
or dependency declarations require concrete identifiers. Any uncertain metadata
should be reviewed and documented rather than blindly removed.

### Q4. What should updated agents report when capability discovery affects an answer?

**Answer:** Capability path plus confidence.

Agents should report the capability path used, citations or local file
references, and confidence level. They should not dump full installed-tool
inventories by default.

### Q5. How should TACD-002 handle generated Claude/Codex payload copies?

**Answer:** Regenerate from source.

Edit source guidance and refresh generated payloads through the existing
distribution path. Do not patch generated payload files directly as the durable
source of truth.

### Q6. What should count as TACD-002 scaffold completion?

**Answer:** Ready for autopilot.

The scaffold is complete when the design concept, workflow, SPEC-MOC marker,
reviewability preset check, setup commit, pushed branch, and roadmap in-progress
status are in place.

## Design Decisions

- **Directive home:** Shared capability-discovery reference plus runtime-specific
  pointers or approved equivalents.
- **Scope boundary:** Active agent guidance only; prerequisite/docs messaging
  stays with TACD-003 and final enforcement stays with TACD-004.
- **Metadata policy:** Preserve schema-required exact IDs; treat uncertain
  metadata as review-required rather than a behavior preference.
- **Evidence policy:** Agent answers informed by discovery should include
  capability path, citations or local files, and confidence.
- **Distribution policy:** Source guidance is authoritative; generated
  `dist/**` payloads must be regenerated from source.
- **Reviewability decision:** Proceed despite the setup gate warning for more
  than one primary surface because TACD-002 is intentionally a small
  docs/process behavior-guidance slice with zero projected production files and
  no implementation of TACD-003 or TACD-004.

## Open Questions For Clarify

- Which exact shared-reference path gives both Claude and Codex stable runtime
  resolution without duplicating directive content?
- Which active agents must point to the directive for AC-2.2 to be satisfied,
  and which can carry an approved runtime-specific equivalent?
- What command regenerates generated Claude/Codex payloads in this repository,
  and what verification proves those copies are source-derived and refreshed?
- Which runtime/dependency metadata IDs are schema-required and should be
  preserved with review notes instead of removed?
- How should agents phrase confidence when falling back to local files or native
  platform capabilities?

## Recommended Checklist Domains

- **llm-integration:** Validate agent instruction behavior, discovery
  semantics, confidence reporting, and runtime-specific pointer handling.
- **error-handling:** Validate fallback behavior when installed capabilities are
  missing or lower confidence.
- **integration:** Validate Claude/Codex parity, generated payload refresh, and
  pointer target resolution from installed runtime contexts.

## Verification Expectations

- Reviewability setup gate result: warning accepted, not blocked.
- Preset resolution must use `.specify/presets/speckit-pro-reviewability/`.
- Workflow must preserve the roadmap split: TACD-002 behavior guidance only,
  TACD-003 messaging later, TACD-004 enforcement later.
- Before PR creation, rerun the relevant structural and deterministic suite,
  ending with `bash tests/speckit-pro/run-all.sh`.
