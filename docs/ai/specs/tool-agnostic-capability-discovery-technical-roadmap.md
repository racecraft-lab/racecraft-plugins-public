# Tool-Agnostic Capability Discovery Implementation Roadmap

**Replace named optional MCP preferences in SpecKit Pro with capability-first discovery across Claude and Codex agents.**

This document defines the **SPEC catalog** for Tool-Agnostic Capability Discovery: an ordered set of specifications derived from the source PRD. Each SPEC corresponds 1:1 to a Feature / Acceptance-Criteria group in the PRD (`AC-N.*`), preserving traceability from PRD -> roadmap -> spec. Each specification is executed end-to-end through the SpecKit workflow before moving to the next, and is prepared for autopilot with `$speckit-scaffold-spec SPEC-NNN`, which reads this roadmap as its input.

**Source PRD:** [../../prd-tool-agnostic-capability-discovery.md](../../prd-tool-agnostic-capability-discovery.md)
**Roadmap MOC:** [tool-agnostic-capability-discovery-roadmap-MOC.md](tool-agnostic-capability-discovery-roadmap-MOC.md)
**Spec ID prefix:** `TACD-###`
**Branch:** one branch per TACD spec; TACD-001, TACD-002, TACD-003, and TACD-004 completed and archived their shipped stacks
**Tracker:** N/A

---

## Table of Contents

1. [Roadmap Overview](#roadmap-overview)
2. [Dependency Graph](#dependency-graph)
3. [Progress Tracking](#progress-tracking)
4. [Specification Sections](#specification-sections)

---

## Roadmap Overview

The feature is decomposed into **4 specifications** across **4 dependency tiers**:

| Tier | Specs | Purpose | Parallelization |
|------|-------|---------|-----------------|
| **1** | TACD-001 | Verify platform mechanics and choose the directive structure | Sequential |
| **2** | TACD-002 | Update active agent behavior across Claude and Codex | Sequential after spike |
| **3** | TACD-003 | Update prerequisites and user-facing docs messaging | Sequential after directive update |
| **4** | TACD-004 | Add deterministic and eval coverage for the vendor-neutral contract | Sequential after behavior and messaging settle |

**Execution Order:** TACD-001 -> TACD-002 -> TACD-003 -> TACD-004

**Dependency Constraints:**
- TACD-002 requires TACD-001 because the spike chooses the directive home and verifies runtime mechanics.
- TACD-003 requires TACD-001 and TACD-002 so messaging describes the implemented behavior, not an assumed design.
- TACD-004 requires all earlier specs so tests and evals lock the final active contract.

## Reviewability Contract

Every spec must fit a human review budget before setup and again before PR creation. The size metric counts **production code only** - documentation, tests, and config do not contribute to the reviewable-LOC count.

- Warn above 400 reviewable production LOC, 6 production files, or 15 total files. Touching more than one primary surface is also a warning, not a block.
- Block above 800 reviewable production LOC, 8 production files, or 25 total files, unless this roadmap records a typed exception pragma.
- A slice that adds only net-new files gets a 1.5x greenfield allowance on production-LOC thresholds.
- Primary surfaces are schema/migration, API, UI, scheduler/runtime, harness/adapter, seed/config, and docs/process.
- PR descriptions are review packets. They must include what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback/flag notes.

---

## Dependency Graph

```text
TACD-001 (Platform Mechanics Spike)
    |
    v
TACD-002 (Capability Discovery Directive and Agent Updates)
    |
    v
TACD-003 (Prerequisite and Documentation Messaging)
    |
    v
TACD-004 (Verification Coverage)
    |
    v
FEATURE COMPLETE
```

---

## Progress Tracking

| Spec | Name | Status | Workflow File | Next Phase |
|------|------|--------|---------------|------------|
| TACD-001 | Platform Mechanics Spike | Complete | [.process/TACD-001-workflow.md](.process/TACD-001-workflow.md) | Archived after PRs #211-#214 and #216; use the spike report's directive-home and allowlist recommendations to scaffold TACD-002 |
| TACD-002 | Capability Discovery Directive and Agent Updates | Complete | [.process/TACD-002-workflow.md](.process/TACD-002-workflow.md) | Archived after PRs #221-#226; use the shared directive and marker-emission hardening as TACD-003/TACD-004 inputs |
| TACD-003 | Prerequisite and Documentation Messaging | Complete | [.process/TACD-003-workflow.md](.process/TACD-003-workflow.md) | Archived after PR #230; use the generic advisory and active guidance updates as TACD-004 inputs |
| TACD-004 | Verification Coverage | Complete | [.process/TACD-004-workflow.md](.process/TACD-004-workflow.md) | Archived after PR #240; the vendor-neutral verification guards, the `strip_codex_guard` payload fix, rebuilt payloads, and rewritten evals now live in source/generator/test paths |

**Status Legend:** Pending | In Progress | Complete | Blocked

---

## Specification Sections

### TACD-001: Platform Mechanics Spike

**Priority:** P1 | **Depends On:** None | **Enables:** TACD-002, TACD-003, TACD-004

**Status:** Complete and archived after PRs #211-#214 merged the spike stack and PR #216 adopted the spike decisions into the PRD and roadmap.

**Goal:** Verify how Claude and Codex agents can discover and use installed tools, MCP/app connectors, skills/plugins, and repo-local helpers without hardcoding a vendor-specific MCP list.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 0 |
Production files: 0 |
Total files: 3 |
Budget result: within budget (research spike; LOC sizing not applicable)

**Scope:**
- Audit active references to optional research/context tools across Claude agents, Codex agents, autopilot skills, prerequisite scripts, plugin limitation docs, and tests/evals.
- Verify runtime mechanics for dynamic installed-capability discovery in Claude and Codex, including whether shared-reference pointers are reliable in each agent context.
- Record the selected directive home: a shared capability-discovery reference with runtime-specific pointers and approved equivalents.
- Produce an allowlist recommendation that separates active guidance from historical references in changelogs, archives, and fixtures.
- This is a Spike: it answers platform/testability questions and should not directly rewrite shipped agent behavior.

**Out of Scope:**
- Editing runtime agent behavior beyond minimal probe fixtures.
- Updating prerequisite messaging or user docs.
- Writing final static/eval enforcement.

**Key Decisions:**
- **Spike-first decision (2026-06-17):** The PRD starts with this spike because Claude and Codex expose agent/tool configuration differently, and directive validation must be proven before behavior edits.
- **Directive-home decision (TACD-001):** Use a shared capability-discovery reference with runtime-specific pointers and approved equivalents. TACD-004 must prove static pointer coverage, target resolution, and behavior-observable eval scenarios.
- **Allowlist decision (TACD-001):** Enforce active guidance by category: active runtime guidance is blocked after TACD-002, prerequisite/user-facing messaging is blocked after TACD-003, deterministic/eval expectations are blocked after TACD-004, and historical/provenance or generated source-derived duplicates may remain when clearly classified.
- **Archive decision (2026-06-18):** The active spec folder was removed after post-merge provenance was recorded. The canonical decision record is `docs/ai/research/tool-agnostic-capability-discovery-spike.md`, and raw spec artifacts remain recoverable through `.specify/memory/archive-reports/2026-06-18-tacd-001-post-merge-hygiene.md`.

**Key Files:**
- `docs/ai/research/tool-agnostic-capability-discovery-spike.md` - spike report and decision record.
- `speckit-pro/agents/*.md` - Claude agent surfaces to audit.
- `speckit-pro/codex-agents/*.toml` - Codex agent surfaces to audit.
- `speckit-pro/skills/speckit-autopilot/references/plugin-limitations.md` - current optional-tool caveats.
- `tests/speckit-pro/` - static/eval surfaces to classify for later enforcement.

---

### TACD-002: Capability Discovery Directive and Agent Updates

**Priority:** P1 | **Depends On:** TACD-001 | **Enables:** TACD-003, TACD-004

**Status:** Complete and archived after PRs #221-#226 merged the capability-discovery directive, agent guidance updates, generated payload refresh, and marker-emission hardening.

**Goal:** Update active Claude and Codex agent behavior to follow the spike-approved capability-discovery directive.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 230 |
Production files: 0 |
Total files: 8 |
Budget result: within budget

**Scope:**
- Implement the TACD-001 directive home: a shared capability-discovery reference with runtime-specific pointers and approved equivalents.
- Update relevant Claude Markdown agents and Codex TOML agents so they choose tools by capability: codebase context, spec context, library documentation, web/domain research, source extraction, installed skills/plugins, and repo-local helpers.
- Remove active preferred-tool wording for named optional MCPs from runtime guidance while preserving historical references where TACD-001 permits them.
- Require agents to report capability path, citations or local files, and confidence level when research/context discovery informs an answer.
- Preserve backward compatibility by allowing discovery to use formerly named tools if the user's runtime exposes them as the best available capability.
- Preserve exact runtime/dependency metadata IDs only where the platform schema or dependency declaration requires them, unless TACD-002 proves an equivalent generic declaration path that TACD-004 can enforce.

**Out of Scope:**
- Rewriting the consensus protocol.
- Implementing prerequisite or docs messaging changes outside direct agent behavior.
- Final static/eval enforcement, which belongs to TACD-004.

**Key Decisions:**
- **Capability-first decision (2026-06-17):** Agents select by needed capability, not by vendor-specific MCP names.
- **Evidence decision (2026-06-17):** Agent outputs should report capability path plus confidence rather than full inventories.
- **Directive-home decision (TACD-001):** TACD-002 adopts the shared reference plus runtime-specific pointer structure, with approved equivalents only where runtime loading requires them.
- **Archive decision (2026-06-18):** The active spec folder was removed after post-merge provenance was recorded. The shared directive, runtime guidance, generated payloads, marker-emission hardening, and regression tests remain in source and generated payload paths; raw spec artifacts remain recoverable through `.specify/memory/archive-reports/2026-06-18-tacd-002-post-merge-hygiene.md`.

**Key Files:**
- `speckit-pro/agents/codebase-analyst.md` - Claude codebase context behavior.
- `speckit-pro/agents/domain-researcher.md` - Claude domain research behavior.
- `speckit-pro/agents/clarify-executor.md` - Claude clarify research behavior.
- `speckit-pro/agents/checklist-executor.md` - Claude checklist remediation behavior.
- `speckit-pro/agents/analyze-executor.md` - Claude analysis remediation behavior.
- `speckit-pro/agents/implement-executor.md` - Claude implementation research behavior.
- `speckit-pro/codex-agents/*.toml` - Codex agent behavior.
- `speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml` - Codex skill dependency metadata.
- `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` - shared capability-discovery directive.
- `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh` - marker-emission source-dir and branch-prefix separation.

---

### TACD-003: Prerequisite and Documentation Messaging

**Priority:** P1 | **Depends On:** TACD-001, TACD-002 | **Enables:** TACD-004

**Status:** Complete and archived after PR #230 merged the prerequisite advisory, active guidance, generated payload refresh, focused tests, and PR packet evidence.

**Goal:** Replace hardcoded optional-MCP prerequisite and user-facing messaging with a generic capability advisory that matches the implemented directive.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 142 |
Production files: 1 |
Total files: 5 |
Budget result: within budget

**Scope:**
- Replace the autopilot prerequisite check's hardcoded optional MCP report with a generic, non-blocking capability advisory that aligns with the TACD-002 directive.
- Update active autopilot references so missing optional capabilities degrade confidence instead of failing setup.
- Update plugin limitation and coach/autopilot docs to describe capability-first discovery and fallback behavior in vendor-neutral language.
- Name capability types, not concrete tool IDs, except where a platform schema or exact file reference requires a concrete identifier.
- Avoid enumerating formerly named optional tools as a preferred set in active docs, setup output, or coaching guidance.

**Out of Scope:**
- Removing historical archive/changelog references.
- Reworking agent behavior already handled by TACD-002.
- Adding a tool installer or marketplace integration.

**Key Decisions:**
- **Prerequisite decision (2026-06-17):** Keep a non-blocking advisory, but make it generic rather than tied to a specific optional MCP set.
- **Wording decision (2026-06-17):** Active guidance names capabilities, not tool IDs.
- **Archive decision (2026-06-19):** The active spec folder was removed after post-merge provenance was recorded. The advisory behavior, active guidance, generated payloads, and focused tests remain in source and generated payload paths; raw spec artifacts remain recoverable through `.specify/memory/archive-reports/2026-06-19-tacd-003-post-merge-hygiene.md`.

**Key Files:**
- `speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh` - prerequisite advisory behavior.
- `speckit-pro/skills/speckit-autopilot/references/prerequisites.md` - Claude autopilot prerequisite docs.
- `speckit-pro/codex-skills/speckit-autopilot/references/prerequisites-codex.md` - Codex prerequisite docs.
- `speckit-pro/skills/speckit-autopilot/references/plugin-limitations.md` - active plugin limitation guidance.
- `speckit-pro/skills/speckit-coach/references/autopilot-guide.md` - coaching explanation of consensus research capabilities.

---

### TACD-004: Verification Coverage

**Priority:** P1 | **Depends On:** TACD-001, TACD-002, TACD-003 | **Enables:** Complete feature

**Status:** Complete and archived after PR #240 merged the vendor-neutral verification guards, the `strip_codex_guard` payload-build fix, rebuilt payloads, and the rewritten functional evals.

**Goal:** Add deterministic checks and functional eval coverage so SpecKit Pro stays vendor-neutral about optional research/context tools, and fix the Claude payload-build defect (`strip_codex_guard`) that truncates skill bodies — locking it with a body-completeness regression check.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 292 |
Production files: 1 |
Total files: 10 |
Budget result: within budget

**Scope:**
- Add or update deterministic tests that fail when active runtime guidance reintroduces a hardcoded named optional-tool contract outside the TACD-001 category allowlist (named-tool guard in Layer 5).
- Verify relevant Claude and Codex agents point to the shared capability-discovery reference or carry an approved runtime-specific equivalent, using a literal path match plus a small enumerated approved-equivalent allowlist (Layer 1 pointer coverage).
- Add target-resolution checks so directive pointers resolve from the installed `dist/claude/**` and `dist/codex/**` payload layouts, not just the source tree.
- Rework the Layer 5 block so the formerly-required named MCP tools (`mcp__tavily-mcp__*`, `mcp__context7__*`, `mcp__RepoPrompt__*`) are removed from the scoping contract entirely.
- Update Claude and Codex functional eval expectations across all four eval files so optional-tool questions are answered in vendor-neutral terms, asserting both the absence of a preferred named set and an affirmative capability-first answer.
- Include behavior-observable eval scenarios for installed-capability discovery, fallback behavior, evidence path, citations or local file references, and lower-confidence reporting when fallback quality is lower (validated against committed fixtures; no live run gates merge).
- Fix `strip_codex_guard` in `scripts/build-plugin-payloads.sh` to strip only the Codex guard block (to the next heading / EOF) instead of truncating to end-of-file, rebuild `dist/` so all skill bodies are restored, and add a deterministic body-completeness check that fails if any `dist/claude` SKILL.md is truncated relative to its source minus the guard section.
- Verify the default deterministic suite with `bash tests/speckit-pro/run-all.sh`.

**Out of Scope:**
- Live AI eval execution unless the implementation PR explicitly chooses to run the slower local eval suite.
- New test layers or broad harness rewrites.
- Behavior changes outside the directive and messaging already implemented.
- A separate hotfix branch for the payload-build defect — it is bundled into this spec.

**Key Decisions:**
- **Verification decision (2026-06-17):** Use static checks plus eval coverage; static-only is insufficient for behavior, eval-only is too costly and non-deterministic.
- **Payload-fix bundling (2026-06-19):** A pre-existing `strip_codex_guard` defect truncated the Claude payload body for 8 of 10 skills. The builder scans for a single-line terminator phrase to end the guard block; in the 8 affected skills that phrase is line-wrapped across two source lines, so the single-line check never matches and the strip runs to end-of-file, dropping the whole body. (The 2 unaffected skills keep the phrase on one unbroken line.) The fix replaces the terminator scan with a section-boundary scan; it, the `dist/` rebuild, and a body-completeness regression check are bundled into TACD-004 rather than fast-tracked as a separate hotfix.
- **Tool-scoping decision (2026-06-19):** Remove the named MCP tool assertions from Layer 5 entirely (vendor neutrality enforced at the contract level) rather than retaining them as optional-but-named.
- **Archive decision (2026-06-22):** The active spec folder was removed after post-merge provenance was recorded. The payload-build fix, deterministic verification guards, rewritten evals, and regenerated payloads remain in source and generated payload paths; raw spec artifacts remain recoverable through `.specify/memory/archive-reports/2026-06-22-tacd-004-post-merge-hygiene.md`.

**Key Files:**
- `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.sh` - named-tool guard + removal of the named-MCP assertions.
- `tests/speckit-pro/layer1-structural/` - pointer-coverage, target-resolution, and payload body-completeness validators.
- `scripts/build-plugin-payloads.sh` - `strip_codex_guard` fix.
- `dist/claude/**` and `dist/codex/**` - regenerated payload copies (source-derived).
- `tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json` - Claude functional evals.
- `tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json` - Codex functional evals.
- `tests/speckit-pro/layer3-functional/evals/speckit-coach-evals.json` - Claude coaching evals.
- `tests/speckit-pro/layer3-functional/codex-evals/speckit-coach-evals.json` - Codex coaching evals.

---

## Decomposition Principles

When breaking this feature into specs:

1. Each spec is independently executable through the full SpecKit workflow.
2. Platform-risk discovery comes first because it determines the safe implementation shape.
3. Agent behavior changes precede messaging so docs describe real behavior.
4. Verification comes last so checks lock the final agreed contract.
5. Each spec gets its own directory: `specs/tacd-<number>-<name>/`.

## Environment & Deployment Context

### Existing Infrastructure (No Changes Needed)

| Resource | Detail |
|----------|--------|
| Plugin marketplace | Existing `speckit-pro/` plugin package for Claude Code and Codex install surfaces. |
| Test runner | Existing shell-based `tests/speckit-pro/run-all.sh` with deterministic default layers. |
| Agent surfaces | Existing Claude Markdown agents and Codex TOML agents. |

### Changes Required

| Change | Where | Detail |
|--------|-------|--------|
| Capability directive | TACD-001 selected structure | Shared capability-discovery reference with runtime-specific pointers and approved equivalents; TACD-004 must prove pointer coverage, target resolution, and behavior-observable evals. |
| Agent guidance | `speckit-pro/agents/`, `speckit-pro/codex-agents/` | Replace named optional-tool preferences with capability-first discovery. |
| Prerequisite advisory | `check-prerequisites.sh` and references | Replace hardcoded optional MCP check with generic advisory. |
| Verification | `tests/speckit-pro/` | Static checks and eval updates for vendor-neutral behavior. |

### Local Development Setup

| Requirement | How |
|-------------|-----|
| Shell test dependencies | Use existing Bash + `jq` workflow. |
| Default verification | `bash tests/speckit-pro/run-all.sh` |
| Focused structural check | `bash tests/speckit-pro/run-all.sh --layer 1` |
| Focused tool-scoping check | `bash tests/speckit-pro/run-all.sh --layer 5` |

---

## References

- **Source PRD:** [../../prd-tool-agnostic-capability-discovery.md](../../prd-tool-agnostic-capability-discovery.md)
- **Design concept:** [tool-agnostic-capability-discovery-design-concept.md](tool-agnostic-capability-discovery-design-concept.md)
- **Roadmap MOC:** [tool-agnostic-capability-discovery-roadmap-MOC.md](tool-agnostic-capability-discovery-roadmap-MOC.md)
- **TACD-001 spike report:** [../research/tool-agnostic-capability-discovery-spike.md](../research/tool-agnostic-capability-discovery-spike.md)
- **TACD-001 archive report:** [../../../.specify/memory/archive-reports/2026-06-18-tacd-001-post-merge-hygiene.md](../../../.specify/memory/archive-reports/2026-06-18-tacd-001-post-merge-hygiene.md)
- **TACD-002 archive report:** [../../../.specify/memory/archive-reports/2026-06-18-tacd-002-post-merge-hygiene.md](../../../.specify/memory/archive-reports/2026-06-18-tacd-002-post-merge-hygiene.md)
- **TACD-003 archive report:** [../../../.specify/memory/archive-reports/2026-06-19-tacd-003-post-merge-hygiene.md](../../../.specify/memory/archive-reports/2026-06-19-tacd-003-post-merge-hygiene.md)
- **TACD-004 archive report:** [../../../.specify/memory/archive-reports/2026-06-22-tacd-004-post-merge-hygiene.md](../../../.specify/memory/archive-reports/2026-06-22-tacd-004-post-merge-hygiene.md)
- **Constitution:** [.specify/memory/constitution.md](../../../.specify/memory/constitution.md)
- **Project Standards:** [AGENTS.md](../../../AGENTS.md), [CLAUDE.md](../../../CLAUDE.md)
