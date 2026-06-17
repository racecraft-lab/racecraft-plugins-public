# SpecKit Workflow: TACD-001 - Platform Mechanics Spike

**Template Version**: 1.0.0
**Created**: 2026-06-17
**Purpose**: Prepare TACD-001 for autonomous execution as the platform-risk spike for tool-agnostic capability discovery.

---

## How to Use This Template

1. Start autopilot with this file:

   ```bash
   $speckit-autopilot docs/ai/specs/.process/TACD-001-workflow.md
   ```

2. Keep `docs/ai/specs/.process/TACD-001-design-concept.md` open as the source of truth for the Grill Me decisions behind this scaffold.

3. Track phase status in the table below as autopilot advances.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during `$speckit-scaffold-spec TACD-001`.
The full Q&A log, Goals, Non-goals, and Open Questions live at:

```text
docs/ai/specs/.process/TACD-001-design-concept.md
```

Re-read it before each phase. The design concept is the source of truth for the accepted report-plus-probes deliverable, both-runtime scope, static-plus-eval-plan proof bar, active-vs-historical allowlist policy, and research-appendix probe boundary.

> **Note:** Grill Me is human-in-the-loop only. It is not part of the autopilot loop. Once this workflow file is populated and autopilot begins, clarifications happen via `/speckit-clarify` and the consensus protocol.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | Complete | Created `spec.md` with 14 FRs, 3 user stories, 9 acceptance scenarios, and 0 clarification markers |
| Clarify | `/speckit-clarify` | Complete | Three clarify sessions resolved audit categories, probe evidence shape, sanitized appendix boundaries, and directive-home proof bar |
| Plan | `/speckit-plan` | Complete | Created plan, research, data model, and quickstart; contracts intentionally omitted |
| Checklist | `/speckit-checklist` | Complete | Integration, LLM Integration, and Error Handling checklists complete with 0 remaining gaps |
| Tasks | `/speckit-tasks` | Complete | Created 30 tasks across 6 phases; G5 passed; marker plan created from size-only reviewability block |
| Analyze | `/speckit-analyze` | Complete | 1 LOW task-phase drift finding remediated; marker counter clean; G6 passed |
| Implement | `/speckit-implement` | Complete | Added report and completed all 30 tasks; marker checkpoints recorded at `a8db2762` |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

Each phase requires human review and approval before proceeding:

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | Requirements define a report-plus-probes spike, both runtime coverage, active-vs-historical categories, and no shipped behavior changes |
| G2 | After Clarify | Audit scope, probe output shape, directive-home proof bar, and allowlist boundaries are explicit |
| G3 | After Plan | Spike report architecture, source inventory method, reproducible probe appendix, and recommendation rubric are concrete |
| G4 | After Checklist | Integration, LLM/tooling, and error-handling gaps are fixed or intentionally deferred |
| G5 | After Tasks | Tasks are research-first, bounded to TACD-001, and do not implement TACD-002/TACD-003/TACD-004 |
| G6 | After Analyze | No critical drift remains between PRD, roadmap, design concept, spec, plan, tasks, and report contract |
| G7 | After Implementation | Spike report exists, probe appendix is reproducible, audit categories are actionable, and no runtime behavior or final enforcement changed |

---

## Prerequisites

### Constitution Validation

Before starting any workflow phase, verify alignment with `.specify/memory/constitution.md`:

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Plugin Structure Compliance | TACD-001 may read plugin skills, agents, Codex agents, manifests, hooks, scripts, and tests as evidence, but must not change shipped plugin behavior or generated payload semantics. | `git diff --name-only` review before PR |
| Script Safety | No new shell script is expected. If a probe helper becomes necessary, it must use `#!/usr/bin/env bash`, `set -euo pipefail`, quoted variables, and clear `jq` usage. | `bash -n` on touched shell scripts |
| Test Coverage Before Merge | A research spike should verify deterministic repo state with targeted static commands and run Layer 1 if active plugin/spec surfaces are touched. | `bash tests/speckit-pro/run-all.sh --layer 1` if plugin/spec surfaces change |
| KISS, Simplicity & YAGNI | Prefer a single spike report with an appendix of reproducible commands/results. Do not create a reusable discovery framework, installer, or final enforcement layer in TACD-001. | Plan complexity review and code review |
| Conventional Commits | PR title must remain public-readable Conventional Commit text. | PR title check |

**Constitution Check:** Run during autopilot preflight before G1.

### Scaffold Preflight Evidence

| Check | Result | Notes |
|-------|--------|-------|
| `specify` CLI | Passed | `specify 0.10.3.dev0` available before setup |
| Technical roadmap | Found | `docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md` |
| TACD-001 status | Pending | Roadmap lists TACD-001 as the first unblocked TACD spec |
| Branch/worktree reuse check | Passed | No local or remote `tacd-001` branch existed before setup |
| Worktree | Created | `.worktrees/tacd-001-platform-mechanics-spike` from `origin/main` |
| Reviewability setup gate | Passed with warning | Setup gate passed; warning was roadmap-level primary-surface count 2 exceeding warning threshold 1 |
| Reviewability preset | Installed | `.specify/presets/speckit-pro-reviewability` refreshed; `plan-template` changed |
| Preset resolution | Passed | `spec-template`, `plan-template`, and `tasks-template` resolve to `speckit-pro-reviewability v1.0.0` |
| Slice-size advisory | OK | Research spike estimate: 0 reviewable LOC, 1 suggested slice, `status=ok` |

### Project Commands

| Command | Purpose |
|---------|---------|
| `rg -n "Tavily|tavily|Context7|context7|RepoPrompt|repoprompt|MCP|mcp" speckit-pro tests/speckit-pro docs -S` | Candidate audit for named optional-tool references |
| `bash tests/speckit-pro/run-all.sh --layer 1` | Structural safety if active plugin/spec surfaces are touched |
| `bash tests/speckit-pro/run-all.sh --layer 5` | Tool-scoping context check if agent tool declarations are inspected or probe findings touch tool lists |
| `bash tests/speckit-pro/run-all.sh` | Default deterministic verification if any plugin/test files change |

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | TACD-001 |
| **Name** | Platform Mechanics Spike |
| **Branch** | `tacd-001-platform-mechanics-spike` |
| **Feature directory** | `specs/tacd-001-platform-mechanics-spike` |
| **Design Concept** | `docs/ai/specs/.process/TACD-001-design-concept.md` |
| **Technical Roadmap** | `docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md` |
| **Source PRD** | `docs/prd-tool-agnostic-capability-discovery.md` |
| **Dependencies** | None |
| **Enables** | TACD-002, TACD-003, TACD-004 |
| **Priority** | P1 |
| **Reviewability estimate** | Research spike; LOC sizing not applicable |

### Roadmap Scope Summary

TACD-001 verifies how Claude and Codex agents can discover and use installed tools, MCP/app connectors, skills/plugins, and repo-local helpers without hardcoding a vendor-specific MCP list. It audits active named-tool references, verifies platform mechanics, recommends whether a shared directive reference plus per-agent pointers is reliable, and identifies where historical named-tool references may remain.

### Success Criteria Summary

- [ ] AC-1.1: A spike report audits current Claude and Codex runtime surfaces that reference optional research/context tools, including agent definitions, skill references, prerequisite checks, plugin limitation docs, and tests/evals.
- [ ] AC-1.2: The spike verifies how each runtime can direct agents to discover and use installed tools, MCP/app connectors, skills/plugins, and repo-local helpers without hardcoding a vendor-specific MCP list.
- [ ] AC-1.3: The spike recommends the directive home. Preferred outcome is a shared reference plus pointers, but only if deterministic checks and evals can validate it reliably.
- [ ] AC-1.4: The spike identifies exact file categories where historical named-tool references may remain, and where active guidance must become vendor-neutral.

### Accepted Scope

- Produce `docs/ai/research/tool-agnostic-capability-discovery-spike.md` as the canonical spike report and decision record.
- Include reproducible probe commands/results in the report appendix where platform mechanics need evidence.
- Audit active references in Claude agents, Codex agents, autopilot skills/references, prerequisite scripts, plugin limitation docs, and tests/evals.
- Check both Claude Code and Codex mechanics for installed tools, MCP/app connectors, skills/plugins, and repo-local helpers.
- Recommend the directive home using a static audit plus an eval-plan proof bar.
- Define active-vs-historical named-tool categories to hand TACD-004 an enforceable allowlist design.

### Out of Scope

- Editing runtime agent behavior beyond minimal probe evidence recorded in the report.
- Updating prerequisite messaging or public docs guidance.
- Writing final deterministic enforcement tests or functional eval updates.
- Running live AI evals as a TACD-001 requirement.
- Installing, bundling, or recommending any replacement third-party MCP servers or connectors.
- Removing historical archive/changelog/provenance or intentionally historical fixture references.

### Key Source Files

- `docs/prd-tool-agnostic-capability-discovery.md`
- `docs/ai/specs/tool-agnostic-capability-discovery-design-concept.md`
- `docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md`
- `speckit-pro/agents/*.md`
- `speckit-pro/codex-agents/*.toml`
- `speckit-pro/skills/speckit-autopilot/SKILL.md`
- `speckit-pro/skills/speckit-autopilot/references/*.md`
- `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`
- `speckit-pro/codex-skills/speckit-autopilot/references/*.md`
- `speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh`
- `speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml`
- `tests/speckit-pro/layer3-functional/evals/*.json`
- `tests/speckit-pro/layer3-functional/codex-evals/*.json`
- `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.sh`

---

## Phase 1: Specify

**When to run:** At the start of TACD-001. Output: `specs/tacd-001-platform-mechanics-spike/spec.md`.

### Specify Prompt

```bash
/speckit-specify

## Feature: Platform Mechanics Spike

### Problem Statement
SpecKit Pro currently has active guidance, prerequisites, and eval expectations that name optional tools such as Tavily, Context7, and RepoPrompt as preferred research/context enhancements. Before TACD-002 rewrites agent behavior, TACD-001 must prove how Claude Code and Codex can express capability-first discovery without hardcoding a vendor-specific MCP list.

### Users
- Maintainers deciding where the capability-discovery directive should live.
- Future TACD-002 implementers who need exact active surfaces and runtime mechanics.
- TACD-004 test authors who need a defensible active-vs-historical allowlist.
- Users indirectly, because the later behavior should work whether they have native tools, MCP/app connectors, installed skills/plugins, or only local fallbacks.

### User Stories
1. As a maintainer, I can read a spike report that inventories all active named-tool references and separates active guidance from historical/provenance references.
2. As a TACD-002 implementer, I can see a recommendation for the directive home and the evidence behind it, including whether shared reference plus per-agent pointers is viable.
3. As a TACD-004 test author, I can use the report's allowlist categories and eval-plan recommendations to write deterministic checks and functional evals without over-banning historical text.

### Functional Requirements Seed
- Produce `docs/ai/research/tool-agnostic-capability-discovery-spike.md` as the canonical report.
- Audit active references to optional research/context tools across Claude agents, Codex agents, autopilot skills/references, prerequisite scripts, plugin limitation docs, dependency metadata, and tests/evals.
- Classify each finding as active runtime guidance, prerequisite/user-facing messaging, deterministic/eval expectation, dependency metadata, historical/provenance, or fixture/test-only.
- Verify both Claude Code and Codex mechanics for directing agents to discover installed tools, MCP/app connectors, skills/plugins, and repo-local helpers.
- Record reproducible probe commands/results in the report appendix where mechanics cannot be established from source inspection alone.
- Recommend the directive home: shared reference plus pointers if static checks and eval-plan scenarios can validate it reliably; otherwise recommend a runtime-specific equivalent.
- Define the exact active-vs-historical named-tool categories that TACD-004 should enforce later.
- Do not rewrite active agent guidance, prerequisite behavior, public docs messaging, or final tests in TACD-001.

### Constraints
- Follow `docs/ai/specs/.process/TACD-001-design-concept.md`.
- Keep TACD-001 research-first: report plus appendix probes only.
- Use local repository evidence first; cite exact source paths and line contexts in the spike report.
- If current official platform docs are needed during implementation, cite the official source and keep the resulting decision in the report.
- Do not remove historical references from changelogs, archives, or intentionally historical fixtures.
- Do not edit plugin versions or generated payload semantics.

### Out of Scope
- Implementing the shared directive or runtime-specific equivalent.
- Updating prerequisites or user-facing docs.
- Adding final enforcement tests or functional eval expectations.
- Running live AI evals as a hard requirement.
- Installing or recommending new third-party tools.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 14 |
| User Stories | 3 |
| Acceptance Criteria | 9 |

### Files Generated

- [x] `specs/tacd-001-platform-mechanics-spike/spec.md`
- [x] `specs/tacd-001-platform-mechanics-spike/checklists/requirements.md`

---

## Phase 2: Clarify

**When to run:** After Specify when audit, probe, or proof-bar boundaries could be interpreted multiple ways.

### Clarify Prompts

#### Session 1: Audit Categories And Allowlist Boundaries

```bash
/speckit-clarify Focus on TACD-001 audit categories: distinguish active runtime guidance, prerequisite/user-facing messaging, dependency metadata, deterministic/eval expectations, historical/provenance references, and fixture/test-only references. Define what later specs must change versus what can remain.
```

#### Session 2: Platform Mechanics And Probe Evidence

```bash
/speckit-clarify Focus on TACD-001 platform mechanics: decide exactly what evidence is needed to verify Claude Code and Codex installed-capability discovery paths, including installed tools, MCP/app connectors, skills/plugins, and repo-local helpers. Keep probes reproducible and report-appendix-only.
```

#### Session 3: Directive-Home Proof Bar

```bash
/speckit-clarify Focus on the TACD-001 directive-home recommendation: define when shared reference plus per-agent pointers is valid, what static checks would prove pointer coverage, and what functional eval scenarios TACD-004 should add later.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Audit categories and allowlist boundaries | 5 | Classified exact runtime schema/tool IDs as runtime/dependency metadata with conditional rewrite only after equivalent discovery is proven; generic MCP/app wording is not a finding unless tied to concrete tools; prerequisite messaging belongs to TACD-003; generated payloads are source-derived duplicates |
| 2 | Platform mechanics and probe evidence | 4 | Report must use a runtime-by-capability matrix with source-backed, probe-backed, unsupported, unresolved, or environment-specific cells; Claude evidence separates declared plugin/agent surfaces from connected parent-session capabilities; Codex evidence separates bundled templates/metadata from installed runtime state; appendix probes publish sanitized summaries only |
| 3 | Directive-home proof bar | 4 | Shared reference plus per-agent pointers is valid only when both static pointer coverage and planned functional eval coverage are defined for Claude and Codex; active Claude agents, Codex agents, relevant skill entrypoints/references, and TACD-004 test/eval expectations need pointers or approved equivalents; TACD-004 should check pointer coverage, target resolution, approved equivalents, and active named-tool prose outside approved categories |

### Consensus Resolution Log

| # | Type | Question/Gap/Finding | Categories | Round | Outcome | Resolution | Analysts Used |
|---|------|----------------------|------------|-------|---------|------------|---------------|
| 1 | Clarify | How should exact concrete tool IDs in runtime schemas be classified? | [codebase, spec, domain] | 1 | 3/3 | Active runtime/dependency metadata; TACD-002 may remove or genericize only after TACD-001 proves an equivalent discovery path preserves access and invocation behavior | codebase-analyst, spec-context-analyst, domain-researcher |
| 2 | Clarify | Should appendix probes include raw runtime inventories or only sanitized summaries? | [security] | 1 | 3/3 | Sanitized summaries only; raw runtime inventories, transcripts, session/request IDs, local paths, full plugin/tool/MCP inventories, connector lists, and access tokens stay transient and uncommitted | codebase-analyst, spec-context-analyst, domain-researcher |

---

## Phase 3: Plan

**When to run:** After the spec and clarify decisions are stable. Output: `specs/tacd-001-platform-mechanics-spike/plan.md`.

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Repository type: public Claude Code and Codex plugin marketplace.
- Runtime surfaces: Markdown Claude agents, TOML Codex agents, skills, references, scripts, generated payloads, and shell-based tests.
- Test runner: `bash tests/speckit-pro/run-all.sh` with deterministic Layers 1, 4, and 5 by default.
- Research output: Markdown spike report under `docs/ai/research/`.

## Constraints
- Follow `docs/ai/specs/.process/TACD-001-design-concept.md`.
- Treat TACD-001 as a spike: report plus reproducible appendix probes, not shipped behavior changes.
- Use local repo source paths and line references as evidence.
- Keep probe commands local, deterministic where possible, and documented in the spike report.
- Do not edit active runtime guidance, prerequisite messaging, docs messaging, or final enforcement tests in this slice.
- Do not remove historical/provenance references.

## Architecture Notes
- Create `docs/ai/research/tool-agnostic-capability-discovery-spike.md` with sections for audit inventory, platform mechanics, directive-home recommendation, active-vs-historical allowlist, TACD-002/TACD-003/TACD-004 handoff, probe appendix, and verification evidence.
- Use explicit source inventory commands for named optional-tool references and capability-discovery wording.
- For Claude Code, inspect plugin agent Markdown frontmatter/tool declarations, skill references, plugin limitation docs, and current generated Claude payload behavior.
- For Codex, inspect TOML agent instructions, Codex skill references, Codex dependency metadata, and current plugin/skill surfaces available to this repo.
- Recommendation rule: choose shared reference plus pointers only if static pointer checks and planned functional evals can validate coverage; otherwise recommend runtime-specific directive copies with a shared source-of-truth note.
- Treat probe appendix output as evidence only. Do not create final enforcement fixtures or long-lived generated outputs unless Plan proves a minimal committed artifact is required.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Complete | Defines one canonical report, source inventory, mechanics matrix, directive-home rule, and verification approach |
| `research.md` | Complete | Records Plan decisions for report architecture, local-first inventory, sanitized probes, matrix evidence, and allowlist categories |
| `data-model.md` | Complete | Defines report entities for findings, runtime surfaces, mechanics evidence, probe summaries, recommendations, handoffs, and verification |
| `contracts/` | Omitted | Not needed because TACD-001 has no API, CLI, schema, parser grammar, or runtime contract |
| `quickstart.md` | Complete | Defines reviewer validation for Plan artifacts, inventory reproduction, report structure, probe sanitization, scope review, and markers |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan`; validate both spec and plan together.

### Recommended Domain Checklists

#### 1. Integration Checklist

Why this domain: TACD-001 coordinates behavior across Claude Code, Codex, skills, agents, prerequisite scripts, dependency metadata, and tests/evals.

```bash
/speckit-checklist integration

Focus on TACD-001 requirements:
- Complete source inventory across Claude agents, Codex agents, skills/references, prerequisite scripts, plugin limitation docs, dependency metadata, and tests/evals.
- Both-runtime mechanics for installed tools, MCP/app connectors, skills/plugins, and repo-local helpers.
- Handoffs from TACD-001 to TACD-002, TACD-003, and TACD-004.
- Pay special attention to: avoiding a recommendation that works for one runtime but not the other.
```

#### 2. LLM Integration Checklist

Why this domain: The directive-home decision affects how phase agents and consensus agents choose research/context capabilities and report confidence.

```bash
/speckit-checklist llm-integration

Focus on TACD-001 requirements:
- Capability-first discovery language for AI agents without naming preferred optional MCPs.
- Evidence expectations: capability path used, citations or local files, and confidence level.
- Static-plus-eval-plan proof bar for the directive home.
- Pay special attention to: whether planned eval scenarios can prove behavior rather than only pointer presence.
```

#### 3. Error-Handling Checklist

Why this domain: Missing optional capabilities should degrade confidence, not block progress, and TACD-001 must capture that behavior without implementing TACD-003.

```bash
/speckit-checklist error-handling

Focus on TACD-001 requirements:
- Fallback behavior when installed tools, MCP/app connectors, skills/plugins, or repo-local helpers are absent.
- How the spike report records unsupported or unverified runtime mechanics.
- Active-vs-historical categories when named-tool references are ambiguous.
- Pay special attention to: preventing the spike from silently turning uncertainty into implementation assumptions.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| Integration | 14 | 0 | Source inventory, runtime mechanics, cross-runtime consistency, downstream handoffs, and no-behavior-change scope are covered |
| LLM Integration | 18 | 2 remediated, 0 remaining | Added confidence rubric and behavior-observable eval-plan requirements to spec and plan |
| Error Handling | 20 | 4 remediated, 0 remaining | Added absent-capability disposition, confidence-rationale fields, ambiguous/requires-review handling, and no-assumption validation |

---

## Phase 5: Tasks

**When to run:** After checklists complete and all gaps are resolved. Output: `specs/tacd-001-platform-mechanics-spike/tasks.md`.

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Organize as research-first tasks that produce a spike report.
- Mark parallel-safe audit tasks with [P] only when they touch separate report sections or independent evidence files.
- Keep TACD-001 bounded to report and reproducible appendix probes.
- Include verification tasks before treating the directive-home recommendation as final.

## Implementation Phases
1. Setup and audit inventory skeleton.
2. Claude Code runtime-surface audit and mechanics evidence.
3. Codex runtime-surface audit and mechanics evidence.
4. Active-vs-historical allowlist recommendation.
5. Directive-home recommendation and TACD-002/TACD-003/TACD-004 handoff.
6. Verification, source citation review, and no-behavior-change scope review.

## Constraints
- Reference `docs/ai/specs/.process/TACD-001-design-concept.md`.
- Do not implement TACD-002 agent guidance changes.
- Do not implement TACD-003 prerequisite/docs messaging changes.
- Do not implement TACD-004 enforcement tests or functional eval updates.
- Keep any probes documented in `docs/ai/research/tool-agnostic-capability-discovery-spike.md` as appendix evidence.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | 30 |
| **Phases** | 6 |
| **Parallel Opportunities** | 4 |
| **User Stories Covered** | US1: 10 tasks; US2: 5 tasks; US3: 4 tasks; shared setup: 5; verification: 6 |

---

## Atomicity Route

After Tasks/G5, autopilot records the atomicity route here:

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | `one-navigable-PR` | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | `true` | `true`, or `false` for release-sensitive changes. |
| **Signals** | `change-shape:modify-heavy` | Decisive detector findings behind the route. |
| **Warnings** | None | Release-safety warnings, if any. |

To produce the decision, run the classifier against the feature directory:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/tacd-001-platform-mechanics-spike
```

### PR Marker Plan

| Field | Value |
|-------|-------|
| **Schema** | `pr-marker-plan.v1` |
| **Status** | `emission_ready` |
| **Evidence** | `specs/tacd-001-platform-mechanics-spike/.process/marker-plan/pr-marker-plan.json` |
| **Reviewability Input** | `specs/tacd-001-platform-mechanics-spike/.process/marker-plan/reviewability-task-gate.json` (`status=block`, `is_size_only=true`, exit code 1) |
| **Atomicity Input** | `specs/tacd-001-platform-mechanics-spike/.process/marker-plan/atomicity-route.json` |
| **Ordered Markers** | 1. `foundation` (`T001`-`T005`); 2. `us1` (`T006`-`T015`); 3. `us3` (`T016`-`T019`); 4. `us2` (`T020`-`T024`, folded polish `T025`-`T030`) |
| **Warnings** | `reviewability_size_warning`: task gate block is marker-planning input |
| **Checkpoints** | `foundation`, `us1`, `us3`, and `us2` complete at `a8db2762` |
| **Final Marker Split** | Pending |
| **Packet Validation** | Pending |
| **PR Mappings** | Pending |

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```bash
/speckit-analyze

Focus on TACD-001 consistency:
1. Verify the PRD, roadmap, design concept, spec, plan, and tasks agree that TACD-001 is a report-plus-probes spike.
2. Verify both Claude Code and Codex runtime mechanics are covered.
3. Verify the active-vs-historical allowlist categories are precise enough for TACD-004.
4. Verify the directive-home proof bar uses static audit plus eval-plan scenarios, not live eval execution as a prerequisite.
5. Verify no task rewrites active agent behavior, prerequisite messaging, docs messaging, or final enforcement tests.
6. Verify the spike report path, appendix probe evidence, citations, and downstream handoffs are explicit.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| A1 | LOW | `tasks.md` needed clearer separation between Claude Code and Codex audit work while staying compatible with marker planning. | Kept one parser-valid US1 marker and added separate Phase 2a Claude Code and Phase 3 Codex subsections; updated dependencies, parallel wording, and MVP strategy text. Re-run marker counter: 0 findings (`0C/0H/0M/0L`). |

### Confidence Gate

| Field | Value |
|-------|-------|
| **Mode** | `advisory` |
| **Threshold** | `0.90` |
| **Result** | `NO_DATA` soft skip |
| **Evidence** | `specs/tacd-001-platform-mechanics-spike/.process/confidence-gate.json` |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed with no blocking gaps.

### Implement Prompt

```bash
/speckit-implement

## Approach
Follow tasks.md in order. Treat TACD-001 as a research spike:

1. AUDIT: Build the source inventory with exact repo paths and active-vs-historical categories.
2. PROBE: Record only minimal reproducible commands/results needed to verify platform mechanics.
3. DECIDE: Recommend the directive home and explain why shared reference plus pointers is or is not reliable.
4. HANDOFF: Write explicit next-step guidance for TACD-002, TACD-003, and TACD-004.
5. VERIFY: Review citations, run targeted checks, and confirm the diff does not change runtime behavior or final enforcement.

### Pre-Implementation Setup
1. Verify branch: `git rev-parse --abbrev-ref HEAD` should show `tacd-001-platform-mechanics-spike`.
2. Review `docs/ai/specs/.process/TACD-001-design-concept.md`.
3. Review `docs/prd-tool-agnostic-capability-discovery.md` and `docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md`.
4. Confirm no runtime behavior files need edits unless the plan explicitly identifies a probe artifact that cannot stay report-only.

### Implementation Notes
- Canonical report path: `docs/ai/research/tool-agnostic-capability-discovery-spike.md`.
- Cite source paths and line contexts for every active guidance category.
- Label uncertain findings rather than guessing.
- Do not remove named-tool references in TACD-001; classify them for later specs.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| `foundation` | `T001`-`T005` | Complete | Report skeleton, scope, confidence rubric, inventory command plan, and no-behavior-change guardrail |
| `us1` | `T006`-`T015` | Complete | Claude Code and Codex runtime-surface audit and mechanics evidence |
| `us3` | `T016`-`T019` | Complete | Active-vs-historical allowlist and TACD-004 recommendations |
| `us2` | `T020`-`T030` | Complete | Directive-home recommendation, downstream handoff, verification, citation review, and no-behavior-change scope review |

---

## Post-Implementation Checklist

- [x] `docs/ai/research/tool-agnostic-capability-discovery-spike.md` exists and cites source paths.
- [x] Probe appendix commands/results are reproducible or explicitly marked as environment-specific.
- [x] Active-vs-historical categories are specific enough for TACD-004.
- [x] TACD-002/TACD-003/TACD-004 handoffs are explicit.
- [x] No active runtime guidance, prerequisite behavior, docs messaging, generated payload semantics, or final enforcement tests changed outside the spike scope.
- [x] Targeted verification ran and results are recorded in PR packet and workflow evidence.

### Post Verification Results

| Item | Status | Evidence |
|------|--------|----------|
| Doctor Extension Check | Pass | Equivalent checks from `.specify/extensions/speckit-utils/commands/doctor.md`; no files changed |
| Verify Implementation | Warn | Equivalent `$speckit-verify` checks passed for TACD artifacts; upstream numeric branch-name prerequisite warned on `tacd-001-platform-mechanics-spike` |
| Verify Tasks Phantom Check | Pass with warning | 30 completed tasks parsed; no phantom tasks; same upstream branch-name warning |
| Code Review | Skipped | Review extension command not installed in `.specify/extensions/.registry` |
| Integration Suite | Pass | `bash tests/speckit-pro/run-all.sh` -> `3009/3009 passed` |
| Privacy Scan Fix | Pass | Removed local absolute home path from `autopilot-state.json`; `test-privacy-scan` and full suite pass |

---

## Project Structure Reference

```text
docs/
  ai/
    research/
      tool-agnostic-capability-discovery-spike.md
    specs/
      .process/TACD-001-design-concept.md
      .process/TACD-001-workflow.md
      tool-agnostic-capability-discovery-technical-roadmap.md
docs/prd-tool-agnostic-capability-discovery.md
speckit-pro/
  agents/
  codex-agents/
  skills/speckit-autopilot/
  codex-skills/speckit-autopilot/
tests/speckit-pro/
  layer3-functional/
  layer5-tool-scoping/
specs/tacd-001-platform-mechanics-spike/
```
