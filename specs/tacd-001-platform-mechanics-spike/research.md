# TACD-001 Plan Research

**Feature**: `tacd-001-platform-mechanics-spike`
**Date**: 2026-06-17
**Scope**: Plan-phase decisions for the Platform Mechanics Spike.

## Decision: Use One Canonical Spike Report

**Decision**: Implementation will create
`docs/ai/research/tool-agnostic-capability-discovery-spike.md` as the single
canonical TACD-001 report and decision record.

**Rationale**: The spec requires one report plus reproducible appendix probes.
Keeping the output in one Markdown file keeps review focused and avoids creating
a reusable framework before TACD-002/TACD-003/TACD-004 prove what should change.

**Alternatives considered**:

- Separate report plus committed probe fixtures: rejected for Plan because the
  accepted probe boundary is report appendix evidence only unless a minimal
  artifact becomes unavoidable.
- Early enforcement tests: rejected because TACD-004 owns final deterministic
  checks and functional eval updates.

## Decision: Use Local Source Inventory Before Probes

**Decision**: The report will classify local repository source evidence first,
then use minimal probes only for runtime mechanics that source inspection cannot
prove.

**Rationale**: TACD-001 must preserve shipped behavior and avoid committing raw
runtime inventories. Source inspection is deterministic and reviewable; probes
are only evidence for runtime availability, pointer consumption, or installed
capability discovery mechanics.

**Alternatives considered**:

- Probe-first runtime inventory: rejected because raw installed tools, connector
  lists, and environment-specific identifiers must not be committed.
- Source-only decision: rejected because the directive-home recommendation may
  depend on mechanics that are not fully represented by repository files.

## Decision: Publish Sanitized Probe Summaries Only

**Decision**: Probe appendix entries will include command or inspection method,
purpose, sanitized observed result, reviewer-facing conclusion, and evidence
state. Raw transcripts, full inventories, local paths, access tokens, connector
lists, request/session IDs, and usage/cost fields stay transient and uncommitted.

**Rationale**: The spec requires reproducibility without leaking
machine-specific or sensitive runtime inventory details.

**Alternatives considered**:

- Commit raw JSON inventories: rejected by FR-015 and unnecessary for reviewers.
- Omit probes entirely: rejected because unresolved mechanics must be labeled or
  probed rather than assumed.

## Decision: Runtime-by-Capability Matrix Is Required

**Decision**: The report will use a matrix crossing Claude Code and Codex with
installed tools, MCP/app connectors, skills/plugins, and repo-local helpers. Each
cell will be marked `source-backed`, `probe-backed`, `unsupported`,
`unresolved`, or `environment-specific`.

**Rationale**: Clarify decisions require the matrix shape and evidence states.
The matrix makes it hard to overfit the recommendation to one runtime.

**Alternatives considered**:

- Narrative-only platform mechanics: rejected because it is harder for TACD-002
  and TACD-004 to validate coverage.
- Separate Claude-only and Codex-only reports: rejected because the directive
  home decision depends on parity.

## Decision: Classify Concrete Tool IDs as Metadata Unless Prose Prefers Them

**Decision**: Concrete tool IDs in schemas, frontmatter tool allowlists, MCP
invocation metadata, or Codex dependency metadata will be classified as active
runtime/dependency metadata unless surrounding prose turns them into a preferred
tool recommendation.

**Rationale**: Clarify decisions say exact runtime schema/tool IDs are active
runtime/dependency metadata and should be rewritten only after equivalent
discovery is proven.

**Alternatives considered**:

- Treat every named tool as a prohibited active-guidance finding: rejected
  because it would over-ban platform metadata and test fixtures.
- Ignore metadata completely: rejected because TACD-002 and TACD-004 still need
  to know which runtime declarations exist.

## Decision: Generic Capability Vocabulary Is Not a Finding by Itself

**Decision**: Generic terms like `MCP`, `app connector`, `installed tool`,
`plugin`, or `capability` are not named-tool findings unless they are tied to a
concrete vendor/server list, concrete tool ID, or prerequisite expectation.

**Rationale**: TACD work is meant to preserve capability-first vocabulary while
removing hardcoded optional-tool preference.

**Alternatives considered**:

- Ban generic MCP/app vocabulary: rejected because the product still needs to
  describe capability classes.
- Audit only vendor names: rejected because concrete MCP server IDs can appear
  without vendor-brand wording.

## Decision: Directive Home Requires Static Coverage Plus Eval Plan

**Decision**: Recommend shared reference plus per-agent pointers only if the
report defines both static pointer coverage and planned functional eval coverage
for Claude Code and Codex. Otherwise recommend runtime-specific directive copies
with a shared source-of-truth note.

**Rationale**: The design concept and clarify decisions set a static-plus-eval
proof bar. Pointer presence alone does not prove that agents apply the directive
in behavior.

**Alternatives considered**:

- Shared reference by default: rejected unless coverage and eval-plan evidence
  can prove it.
- Runtime-specific copies by default: acceptable fallback, but the report should
  still test whether the shared reference is viable.

## Decision: Omit Contracts

**Decision**: Do not create a `contracts/` directory in Plan.

**Rationale**: TACD-001 does not define an API, CLI, schema, parser grammar, or
external integration contract. The report structure is captured as data entities
in `data-model.md` and reviewer validation in `quickstart.md`.

**Alternatives considered**:

- Markdown report schema in `contracts/`: rejected as unnecessary process
  overhead for a human-reviewed research report.
- JSON schema for findings: rejected because TACD-004 will own enforceable
  checks after the report defines categories.

## Plan-Time Source Inventory Evidence

The following local evidence demonstrates the required audit surfaces:

- `speckit-pro/agents/codebase-analyst.md` lines 12-16 declare RepoPrompt MCP
  tool IDs; lines 54-67 prefer RepoPrompt with local fallbacks.
- `speckit-pro/agents/domain-researcher.md` lines 11-17 declare Tavily and
  Context7 MCP tools plus WebSearch/WebFetch fallbacks; lines 53-67 prefer
  those MCP paths when installed.
- `speckit-pro/codex-agents/codebase-analyst.toml` lines 35-52 carries Codex
  prose for RepoPrompt-preferred discovery with generic local fallbacks.
- `speckit-pro/codex-agents/domain-researcher.toml` lines 33-49 carries Codex
  prose for Tavily, extraction, and library-doc preferred paths.
- `speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh`
  lines 115-142 contains the hardcoded informational MCP server report.
- `speckit-pro/skills/speckit-autopilot/references/plugin-limitations.md`
  lines 30-38 and 68-81 document MCP availability, named optional servers, and
  fallbacks.
- `speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml` lines 9-16
  declares Codex MCP dependency metadata.
- `tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json`
  lines 107-116 and
  `tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json`
  lines 112-120 encode named optional-tool eval expectations.
- `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.sh` lines 240-250
  validates named research tool declarations.
- `dist/claude/speckit-pro/agents/codebase-analyst.md` lines 12-19 and
  `dist/codex/speckit-pro/codex-agents/codebase-analyst.toml` lines 35-52 show
  generated payloads duplicate active source content and must be classified as
  generated source-derived duplicates unless the source differs.

## Research Resolution

All Plan-phase technical unknowns are resolved. Remaining open questions from
the design concept are implementation questions for the spike report and must be
answered in `docs/ai/research/tool-agnostic-capability-discovery-spike.md`.
