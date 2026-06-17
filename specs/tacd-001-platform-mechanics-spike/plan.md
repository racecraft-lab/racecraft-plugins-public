# Implementation Plan: Platform Mechanics Spike

**Branch**: `tacd-001-platform-mechanics-spike` | **Date**: 2026-06-17 | **Spec**: `specs/tacd-001-platform-mechanics-spike/spec.md`

**Input**: Feature specification from `specs/tacd-001-platform-mechanics-spike/spec.md`

## Summary

TACD-001 is a research spike that produces one canonical report:
`docs/ai/research/tool-agnostic-capability-discovery-spike.md`. The report will
audit current named optional-tool references, verify Claude Code and Codex
capability-discovery mechanics, recommend the directive home for TACD-002, define
active-vs-historical allowlist categories for TACD-004, and document sanitized
probe evidence where source inspection alone is not enough.

This slice does not rewrite active runtime guidance, prerequisite messaging,
public docs messaging, generated payload semantics, plugin versions, or final
enforcement tests. It records evidence and handoffs only.

## Technical Context

**Language/Version**: Markdown research artifacts plus local shell probes; inputs include Markdown, TOML, YAML, JSON, and Bash.

**Primary Dependencies**: Local repository tools only: `rg`, `git`, `jq`, `nl`, `sed`, and existing SpecKit shell scripts.

**Storage**: N/A - no application state or persistent runtime storage.

**Testing**: Static source inventory commands, report-content checks, `git diff --name-only` scope review, and targeted SpecKit layer checks only if plugin/runtime/test surfaces are touched.

**Target Platform**: Public Claude Code and Codex plugin marketplace repository.

**Project Type**: Documentation/process research spike.

**Performance Goals**: Inventory commands must be local and reviewable; the report must classify 100% of in-scope audited findings with source paths, line context, classification, and rationale.

**Constraints**: Keep TACD-001 to report plus appendix probes; sanitize probe summaries; do not commit raw runtime inventories, connector lists, session IDs, request IDs, access tokens, absolute machine paths, or full tool/plugin/MCP inventories; preserve historical and provenance references.

**Scale/Scope**: One canonical report plus Plan-phase artifacts. No production code, scripts, generated payload rebuilds, or final enforcement fixtures.

**Reviewability Budget**: Primary surface `docs/process`; projected 300-600 lines of Markdown report content; 0 production files; 1 implementation file; within budget.

## Declared File Operations

- NEW docs/ai/research/tool-agnostic-capability-discovery-spike.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Plan Decision |
|-----------|--------|--------------------------|
| I. Plugin Structure Compliance | PASS | TACD-001 only inspects plugin agents, skills, metadata, generated payloads, and tests as evidence. It does not change plugin directory layout, manifests, hooks, agents, or skills. |
| II. Script Safety | PASS | No new script is planned. Appendix probes are documented commands in the report. If implementation proves a helper is unavoidable, it must use Bash safety requirements and get Layer 4 coverage, but the current plan does not require one. |
| III. Semantic Versioning | PASS | No plugin version or release metadata changes are planned. |
| IV. Test Coverage Before Merge | PASS | No production behavior changes are planned. Verification is source inventory, report-content checks, and scope review; Layer 1/5 run only if active plugin/spec/test surfaces are unexpectedly touched. |
| V. Conventional Commits | PASS | PR title can use `docs(speckit-pro): add TACD-001 capability discovery spike` or equivalent. |
| VI. KISS, Simplicity & YAGNI | PASS | One report with an appendix is simpler than reusable probe infrastructure or early enforcement. TACD-002/TACD-003/TACD-004 own behavior and enforcement changes. |

**Post-Design Re-check**: PASS. Phase 1 artifacts keep the scope to one report,
structured report entities, and a validation guide. No complexity exception is
needed.

## Project Structure

### Documentation (this feature)

```text
specs/tacd-001-platform-mechanics-spike/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/
│   └── requirements.md
└── tasks.md              # Created later by /speckit-tasks
```

`contracts/` is intentionally omitted. TACD-001 does not expose an external API,
CLI schema, or machine contract; the report shape is documented in
`data-model.md` and validated through `quickstart.md`.

### Source / Evidence Surfaces

```text
docs/
  ai/
    research/
      tool-agnostic-capability-discovery-spike.md
    specs/
      .process/TACD-001-design-concept.md
      .process/TACD-001-workflow.md
      tool-agnostic-capability-discovery-technical-roadmap.md
  prd-tool-agnostic-capability-discovery.md
speckit-pro/
  agents/
  codex-agents/
  skills/speckit-autopilot/
  codex-skills/speckit-autopilot/
  .codex-plugin/plugin.json
  .claude-plugin/plugin.json
dist/
  claude/speckit-pro/
  codex/speckit-pro/
tests/speckit-pro/
  layer3-functional/
  layer5-tool-scoping/
```

**Structure Decision**: Keep implementation output in `docs/ai/research/`.
Feature-phase planning artifacts stay under `specs/tacd-001-platform-mechanics-spike/`.
All runtime and test files are evidence sources only unless a later TACD slice
changes them.

## Complexity Tracking

No constitution violations or reviewability exceptions.

## Phase 0: Research Decisions

`research.md` records the Plan-phase decisions:

- canonical report path and section architecture
- local-first source inventory strategy
- runtime-by-capability matrix with source-backed, probe-backed, unsupported,
  unresolved, and environment-specific evidence states
- sanitized probe appendix rules
- directive-home recommendation rule
- TACD-004 allowlist category set
- explicit contracts omission

No unresolved clarification markers remain for Plan.

## Phase 1: Design Artifacts

`data-model.md` defines the report entities that implementation must fill:

- Named-Tool Reference
- Runtime Surface
- Capability Mechanics Evidence
- Runtime-by-Capability Matrix Cell
- Sanitized Probe Summary
- Directive-Home Recommendation
- Allowlist Category
- Downstream Handoff
- Verification Evidence

`quickstart.md` defines reviewer validation for report existence, required
sections, source inventory reproducibility, probe sanitization, no-behavior-change
scope review, and G3 readiness.

`contracts/` is intentionally omitted because the report is not a callable API or
runtime interface.

## Source Inventory Plan

Implementation will run and summarize explicit local inventory commands instead
of relying on broad impressions. Required commands include:

```bash
rg -n "Tavily|tavily|Context7|context7|RepoPrompt|repoprompt|MCP|mcp" speckit-pro tests/speckit-pro docs -S
rg -n "capability|capabilities|installed tool|app connector|MCP|mcp" speckit-pro tests/speckit-pro docs -S
find speckit-pro/agents speckit-pro/codex-agents -maxdepth 1 -type f | sort
find dist/claude/speckit-pro dist/codex/speckit-pro -maxdepth 3 -type f | sort
```

Plan-time evidence confirms the inventory is necessary:

- Claude agent frontmatter can declare concrete MCP tools, for example
  `speckit-pro/agents/codebase-analyst.md` lines 12-16 and
  `speckit-pro/agents/domain-researcher.md` lines 11-17.
- Claude agent prose currently prefers named MCP capabilities with fallbacks,
  for example `speckit-pro/agents/codebase-analyst.md` lines 54-67 and
  `speckit-pro/agents/domain-researcher.md` lines 53-67.
- Codex TOML agents carry equivalent prose in runtime instructions, for example
  `speckit-pro/codex-agents/codebase-analyst.toml` lines 35-52 and
  `speckit-pro/codex-agents/domain-researcher.toml` lines 33-49.
- The prerequisite script has a hardcoded informational MCP set in
  `speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh`
  lines 115-142.
- Plugin limitation docs name MCP servers and fallbacks in
  `speckit-pro/skills/speckit-autopilot/references/plugin-limitations.md`
  lines 30-38 and 68-81.
- Codex dependency metadata names concrete MCP dependencies in
  `speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml` lines 9-16.
- Functional evals encode named optional-tool expectations in
  `tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json`
  lines 107-116 and
  `tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json`
  lines 112-120.
- Layer 5 enforces named tool allowlists for active agent files in
  `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.sh` lines 240-250.
- Generated payloads duplicate active source content, for example
  `dist/claude/speckit-pro/agents/codebase-analyst.md` lines 12-19 and
  `dist/codex/speckit-pro/codex-agents/codebase-analyst.toml` lines 35-52.

The final report must classify each finding at reference level, not only at file
level.

## Platform Mechanics Plan

The report will include a runtime-by-capability matrix:

| Runtime | Installed Tools | MCP / App Connectors | Skills / Plugins | Repo-Local Helpers |
|---------|-----------------|----------------------|------------------|--------------------|
| Claude Code | Source/probe-backed from plugin agent tool declarations and parent-session inheritance mechanics. | Source/probe-backed where local plugin docs and minimal command probes show parent-session exposure. | Source-backed from plugin skill layout and generated Claude payloads; probe-backed only if runtime discovery needs confirmation. | Source-backed from `Read`/`Grep`/`Glob` fallback guidance and repo scripts. |
| Codex | Source/probe-backed from TOML agents and current Codex tool-discovery surfaces. | Source/probe-backed from Codex plugin/skill metadata and available tool discovery. | Source-backed from `speckit-pro/codex-skills/**`, installed plugin cache metadata, and active skill surfaces. | Source-backed from shell, local files, and repo helper scripts. |

Each matrix cell must be labeled `source-backed`, `probe-backed`, `unsupported`,
`unresolved`, or `environment-specific`. Probe appendix entries publish only
sanitized command summaries and conclusions.

## Directive-Home Recommendation Rule

Recommend shared reference plus per-agent pointers only if the report defines
both:

- static pointer coverage for active Claude agents, Codex agents, relevant skill
  entrypoints/references, pointer-target resolution, and approved
  runtime-specific equivalents
- planned functional eval coverage for Claude and Codex that proves
  vendor-neutral optional-tool setup, missing-capability fallback,
  installed-capability selection without vendor preference, capability
  path/citation/confidence reporting, and directive application in research or
  codebase-context tasks

If either runtime lacks a reliable pointer path or planned eval coverage, the
report must recommend runtime-specific directive copies with a shared
source-of-truth note.

## TACD-004 Allowlist Categories

The report will hand TACD-004 a category set that distinguishes:

- active runtime guidance
- active runtime/dependency metadata
- prerequisite/user-facing messaging
- deterministic/eval expectation
- dependency metadata
- generated source-derived duplicate
- historical/provenance
- fixture/test-only
- explicitly out of scope

Generic MCP/app/installed-tool vocabulary is not a named-tool finding unless it
is tied to concrete tools, concrete prerequisites, or a vendor/server list.

## Verification Plan

Minimum Plan/implementation verification:

```bash
test -s specs/tacd-001-platform-mechanics-spike/plan.md
test -s specs/tacd-001-platform-mechanics-spike/research.md
test -s specs/tacd-001-platform-mechanics-spike/data-model.md
test -s specs/tacd-001-platform-mechanics-spike/quickstart.md
bash speckit-pro/skills/speckit-autopilot/scripts/validate-gate.sh G3 specs/tacd-001-platform-mechanics-spike
bash speckit-pro/skills/speckit-autopilot/scripts/count-markers.sh all specs/tacd-001-platform-mechanics-spike
test -s docs/ai/research/tool-agnostic-capability-discovery-spike.md
git diff --name-only
```

Run `bash tests/speckit-pro/run-all.sh --layer 1` or
`bash tests/speckit-pro/run-all.sh --layer 5` only if implementation unexpectedly
touches active plugin/spec/test surfaces. The intended final diff should be
research/report artifacts only.

## Downstream Handoff

- **TACD-002**: behavior-changing agent and skill guidance updates based on the
  chosen directive-home recommendation.
- **TACD-003**: prerequisite, plugin limitation, coaching, and public docs
  messaging updates based on the report's user-facing categories.
- **TACD-004**: deterministic checks and functional eval updates based on the
  allowlist categories, pointer coverage rules, and eval-plan scenarios.
