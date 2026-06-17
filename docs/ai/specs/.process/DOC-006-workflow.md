# SpecKit Workflow: DOC-006 - Safe interactive selector and validation aids

**Template Version**: 1.0.0
**Created**: 2026-06-16
**Purpose**: Prepare DOC-006 for autonomous execution after the platform installation paths and first-run tutorial are in place.

---

## How to Use This Template

1. Start autopilot with this file:

   ```bash
   $speckit-autopilot docs/ai/specs/.process/DOC-006-workflow.md
   ```

2. Keep `docs/ai/specs/.process/DOC-006-design-concept.md` open as the source of truth for the Grill Me decisions behind this scaffold.

3. Track phase status in the table below as autopilot advances.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during `$speckit-scaffold-spec DOC-006`.
The full Q&A log, Goals, Non-goals, and Open Questions live at:

```text
docs/ai/specs/.process/DOC-006-design-concept.md
```

Re-read it before each phase. The design concept is the source of truth for the accepted `choose-your-path` surface, source-derived build-time metadata boundary, static-first interaction model, repo-only version checker, accessible payload diagram, lightweight troubleshooting handoff, and focused validation scope.

> **Note:** Grill Me is human-in-the-loop only. It is not part of the autopilot loop. Once this workflow file is populated and autopilot begins, clarifications happen via `/speckit-clarify` and the consensus protocol.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | Complete | Created `spec.md` with 17 functional requirements, 3 user stories, 10 acceptance scenarios, and 0 clarification markers |
| Clarify | `/speckit-clarify` | Complete | Completed 3 sessions; clarified metadata source boundary, interaction/fallback/accessibility, repository-only checker, handoffs, first-run checklist scope, and validation coverage |
| Plan | `/speckit-plan` | Complete | Created plan, research, data model, quickstart, and schema contract; G3 passed; reviewability estimator passed at 80 projected production LOC |
| Checklist | `/speckit-checklist` | Complete | Completed UX, accessibility, integration/source-data, and error-handling checklists; G4 passed with 0 remaining gaps |
| Tasks | `/speckit-tasks` | Complete | Created 32 docs-first tasks across setup, foundation, 3 user stories, and polish; G5 passed; size-only reviewability block produced a 4-marker review plan |
| Analyze | `/speckit-analyze` | Complete | 1 MEDIUM task explicit-review finding remediated; marker counter clean; G6 recommended pass |
| Implement | `/speckit-implement` | Complete | Implemented route-preserving MDX, safe install aids component, source-derived metadata helper, focused validator, static fallback tables, repository checker, payload diagram, and first-run checklist |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

Each phase requires human review and approval before proceeding:

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | Requirements cover selector, install-scope choice, copyable commands, manifest/version checker, payload diagram, first-run checklist, static fallbacks, keyboard access, and no local execution |
| G2 | After Clarify | Source-derived metadata, checker input boundary, fallback behavior, and troubleshooting handoff scope are explicit |
| G3 | After Plan | Docs architecture is concrete, no new generator creep exists, source JSON reads are bounded, and constitution gates pass |
| G4 | After Checklist | UX, accessibility, integration/source-data, and error-handling gaps are fixed or explicitly deferred |
| G5 | After Tasks | Tasks are docs-first, ordered by user story, independently reviewable, and protect AC-6.* acceptance criteria |
| G6 | After Analyze | No critical consistency drift remains between roadmap, PRD, Design Concept, spec, plan, tasks, and validation plan |
| G7 | After Implementation | Docs-site validation, link validation, focused fixture/test evidence, keyboard/static fallback review, and command-safety review are complete |

---

## Prerequisites

### Constitution Validation

Before starting any workflow phase, verify alignment with `.specify/memory/constitution.md`:

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Plugin Structure Compliance | DOC-006 should not change plugin manifests, hooks, skills, agents, generated payloads, marketplace behavior, or release automation unless a direct source-data bug is found and documented. | `git diff --name-only` review before PR |
| Script Safety | No new shell scripts are expected. If a focused validation helper is added, preserve `#!/usr/bin/env bash`, `set -euo pipefail`, quoted variables, and clear `jq` use. | `bash -n` on touched scripts plus targeted tests |
| Test Coverage Before Merge | Docs-site checks and a focused metadata/rendering fixture or test are required. Run the full repo suite if plugin/spec surfaces or generated payloads are touched. | `cd docs-site && pnpm validate`; `cd docs-site && pnpm validate:links`; focused fixture/test; `bash tests/speckit-pro/run-all.sh` when applicable |
| KISS, Simplicity & YAGNI | Keep the aids static-first and build-time read-only. Do not add a reusable metadata generator, pasted JSON checker, or rich app widget in this slice. | Plan Complexity Tracking plus code review |
| Conventional Commits | PR title must remain a conventional commit. | PR title check |

**Constitution Check:** Verified by autopilot preflight on 2026-06-17. `check-prerequisites.sh` passed with SpecKit CLI `specify 0.10.3.dev0`, branch `doc-006-safe-interactive-selector-and-validation-aids`, and worktree isolation enabled. MCP research servers are not configured, so agents will use built-in fallbacks.

### Archive Sweep Startup

| Field | Result |
|-------|--------|
| Archive extension | Available, `archive` v1.1.0 |
| Current target excluded | `specs/doc-006-safe-interactive-selector-and-validation-aids` |
| Eligible previously merged specs | None |
| Cleanup applied | No |
| `safeToApplyCleanup` | `false` |
| Tier-2 relocation | Suppressed: active spec already has `SPEC-MOC.md` `structureVersion: 1` and no relocatable PROCESS artifacts |

### Scaffold Preflight Evidence

| Check | Result | Notes |
|-------|--------|-------|
| `specify` CLI | Passed | Available on `PATH`; local binary path intentionally omitted from committed process evidence |
| Technical roadmap | Found | `docs/ai/specs/interactive-documentation-technical-roadmap.md` |
| DOC-006 status | Ready | Roadmap lists DOC-006 as ready after DOC-002, DOC-003, and DOC-004 |
| Branch/worktree reuse check | Passed | No local or remote DOC-006 branch existed before setup |
| Worktree | Created | `.worktrees/doc-006-safe-interactive-selector-and-validation-aids` from `origin/main` |
| Reviewability setup gate | Passed | `reviewability-gate.sh setup docs/ai/specs/interactive-documentation-technical-roadmap.md` returned `status=pass`, 395 reviewable LOC, 0 production files, 6 total files, no blockers |
| Reviewability preset | Installed | `.specify/presets/speckit-pro-reviewability` refreshed; `plan-template` changed |
| Preset resolution | Passed | `spec-template`, `plan-template`, and `tasks-template` resolve to `speckit-pro-reviewability v1.0.0` |
| Slice-size advisory | OK | Grill Me estimate: 227 reviewable LOC, 1 suggested slice, `status=ok` |

### Project Commands

| Command | Purpose |
|---------|---------|
| `cd docs-site && pnpm validate` | Astro type/content check plus production build |
| `cd docs-site && pnpm validate:links` | Current docs-site link-validation hook; presently aliases production build |
| Focused metadata/rendering fixture or test | Protect source-derived selector/checker data against manifest and command drift |
| `bash tests/speckit-pro/run-all.sh` | Full repo/plugin validation if implementation touches plugin/spec surfaces, scripts, manifests, or generated payloads |
| Manual keyboard/static fallback review | Confirm selector/checker controls, fallback tables, and payload diagram remain usable without unsafe browser execution |

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | DOC-006 |
| **Name** | Safe interactive selector and validation aids |
| **Branch** | `doc-006-safe-interactive-selector-and-validation-aids` |
| **Feature directory** | `specs/doc-006-safe-interactive-selector-and-validation-aids` |
| **Design Concept** | `docs/ai/specs/.process/DOC-006-design-concept.md` |
| **Roadmap** | `docs/roadmap-interactive-documentation.md` and `docs/ai/specs/interactive-documentation-technical-roadmap.md` |
| **Dependencies** | DOC-002 site shell, DOC-003 Claude install path, DOC-004 Codex install path, and DOC-005 first-run/lifecycle content |
| **Enables** | DOC-010 search, accessibility, deep links, and docs validation hardening |
| **Priority** | P1 |
| **Reviewability estimate** | Setup gate pass; Grill Me forward estimate 227 LOC, suggested 1 slice, advisory ok |

### Success Criteria Summary

- [ ] AC-6.1: The platform/path selector outputs only documentation guidance and copyable commands; it does not edit user config.
- [ ] AC-6.2: Copyable command blocks include platform labels, install-scope labels, prerequisite notes, and expected success signals.
- [ ] AC-6.3: The manifest/version checker compares displayed repository metadata from checked-in JSON and explains what must stay in sync.
- [ ] AC-6.4: The payload diagram shows source tree, Claude dist, Codex dist, marketplace entries, and Codex cache as distinct nodes.
- [ ] AC-6.5: Interactive components remain usable by keyboard and degrade to static Markdown tables or equivalent semantic fallback content.
- [ ] AC-6.6: The first-run checklist includes checkpoints but never runs shell commands from the browser.

### Accepted Scope

- Enhance `docs-site/src/content/docs/choose-your-path.md` as the first home for the selector/checker experience.
- Add the smallest Astro/Starlight-compatible component or data helper needed to render platform/path and install-scope choices.
- Derive command and manifest metadata from checked-in repository files at docs build time without committing a generated metadata artifact.
- Render copyable command blocks with platform/scope labels, prerequisites, expected success signals, and static fallback tables.
- Add a repo-only manifest/version checker that compares checked-in source and generated payload marketplace/manifest values and explains update/release handoffs.
- Add an accessible generated-payload diagram with text/table fallback content.
- Add a first-run checklist and lightweight troubleshooting handoffs for unresolved selector/checker states.
- Add focused validation that protects source-derived metadata/rendering plus docs-site validation and link validation.

### Key Decisions From Grill Me

- Q1: "Enhance Choose Your Path" is the primary surface.
- Q2 and Q3: Metadata is "Generated from source" but bounded to "Build-time read only"; no committed generated file and no full generator script.
- Q4: Use "Static-first enhancement" rather than a richer app widget or tables-only fallback.
- Q5: Use "Lightweight handoff only" for troubleshooting; DOC-008 owns the full troubleshooting matrix.
- Q6: The checker reports "Repo consistency only"; it does not accept pasted user JSON.
- Q7: Deliver the payload diagram as an "Accessible static diagram" backed by text/table content.
- Q8: Completion requires "Docs plus focused fixture" validation.

### Out of Scope

- Live local doctor command, browser-side shell execution, or browser-side plugin execution.
- Auto-editing Claude Code or Codex user configuration.
- A pasted JSON checker for user-local files.
- A reusable metadata generator script or committed generated metadata output.
- Full troubleshooting matrix, trust model, update, rollback, and cache diagnosis; those belong to DOC-008.
- Full command, workflow, manifest, and file-layout reference; that belongs to DOC-007.
- Search, broad accessibility hardening, deep-link conventions, and docs CI hardening; those belong to DOC-010.

### Key Source Files

- `docs-site/src/content/docs/choose-your-path.md`
- `docs-site/src/content/docs/install/claude-code.md`
- `docs-site/src/content/docs/install/codex.md`
- `docs-site/src/content/docs/first-run.md`
- `docs-site/src/content/docs/spec-kit-lifecycle.mdx`
- `docs-site/src/components/LifecycleFlow.astro`
- `docs-site/src/content.config.ts`
- `.claude-plugin/marketplace.json`
- `.agents/plugins/marketplace.json`
- `speckit-pro/.claude-plugin/plugin.json`
- `speckit-pro/.codex-plugin/plugin.json`
- `dist/claude/speckit-pro/.claude-plugin/plugin.json`
- `dist/codex/speckit-pro/.codex-plugin/plugin.json`
- `scripts/build-plugin-payloads.sh`
- `docs/prd-interactive-documentation.md`
- `docs/roadmap-interactive-documentation.md`
- `docs/ai/specs/interactive-documentation-technical-roadmap.md`

---

## Phase 1: Specify

**When to run:** At the start of DOC-006. Output: `specs/doc-006-safe-interactive-selector-and-validation-aids/spec.md`.

### Specify Prompt

```bash
/speckit-specify

## Feature: Safe interactive selector and validation aids

### Problem Statement
Users can now read separate Claude Code, Codex, first-run, and lifecycle docs, but they still need a safe way to choose the right platform path, install scope, commands, metadata checks, and first-run checkpoints without executing local plugin workflows from the browser. DOC-006 should enhance the existing `choose-your-path` docs route with static-first selector and checker aids that derive their facts from checked-in repository metadata at build time.

### Users
- New installers who are not sure whether they need Claude Code, Codex, repository-scoped install, personal marketplace install, or generated payload guidance.
- Returning users who need the correct copyable command sequence and expected success signal for their platform/scope.
- Maintainers and evaluators who need a visible repository consistency check across marketplace and plugin manifest versions.
- Users who need safe first-run checkpoints and lightweight handoffs when selector/checker output indicates a mismatch.

### User Stories
- As a new user, I can choose my platform and install scope on `choose-your-path` and receive only the relevant commands, prerequisites, expected success signals, and next docs links.
- As a user or evaluator, I can inspect a repository-only manifest/version checker that compares checked-in marketplace and plugin manifest values and explains what must stay in sync.
- As a cautious first-run user, I can review a generated payload diagram and first-run checklist with static fallback content and no browser-side local command execution.

### Functional Requirements Seed
- Enhance `docs-site/src/content/docs/choose-your-path.md` as the primary DOC-006 surface instead of creating a separate route.
- Provide a platform/path selector for Claude Code and Codex paths, including install-scope choices where supported.
- Provide copyable command blocks with visible platform labels, install-scope labels, prerequisite notes, expected success signals, and handoff links.
- Source command/checker facts from checked-in repository JSON/manifests at docs build time. Do not commit a generated metadata file.
- Provide a manifest/version checker that compares repository source and generated payload marketplace/manifest versions and explains expected consistency.
- Provide an accessible generated-payload diagram showing source tree, Claude dist, Codex dist, marketplace entries, and Codex cache as distinct nodes.
- Provide a first-run checklist with checkpoints for Spec Kit CLI, constitution, GitHub CLI, `jq`, branch/worktree state, platform install route, scaffold output, and docs validation.
- Ensure all interactive aids are keyboard usable and have semantic static fallback tables or equivalent static content.
- Ensure browser behavior never runs shell commands, reads local user files, writes config, installs plugins, or invokes local plugin workflows.
- Add lightweight troubleshooting handoffs from selector/checker mismatch states to existing or DOC-008-owned troubleshooting content.
- Add focused validation for source-derived metadata/rendering in addition to docs-site validation and link validation.

### Constraints
- Use the existing Astro/Starlight docs-site patterns and avoid adding dependencies unless Plan proves there is no simpler local pattern.
- Keep metadata derivation read-only at build time; no prebuild-generated file, no persistent generator output, and no config mutation.
- Preserve platform boundaries: Claude Code command guidance must not leak into Codex command sequences, and Codex `$skill` invocation must not be described as Claude slash-command usage.
- Keep the checker repository-scoped. It may compare checked-in marketplace/plugin JSON values, but it must not accept pasted user JSON or inspect local user config.
- Keep troubleshooting to lightweight handoffs only. DOC-008 owns the full troubleshooting matrix, security/trust model, update, and rollback.
- Keep validation proportional: docs-site checks plus focused metadata/rendering fixture are required; full repo suite is conditional on plugin/source/script/manifest changes.

### Out of Scope
- Live local doctor command.
- Auto-editing user config.
- Pasted JSON checker for local user files.
- Full command/reference matrix.
- Full troubleshooting, security/trust, update, rollback, or cache-diagnosis content.
- Search/deep-link/docs CI hardening beyond the focused fixture needed for this slice.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 17 |
| User Stories | 3 |
| Acceptance Criteria | 10 acceptance scenarios plus 7 measurable success criteria |

### Files Generated

- [x] `specs/doc-006-safe-interactive-selector-and-validation-aids/spec.md`
- [x] `specs/doc-006-safe-interactive-selector-and-validation-aids/checklists/requirements.md`

---

## Phase 2: Clarify

**When to run:** After Specify if any implementation boundary could be interpreted multiple ways. Maximum 5 targeted questions per session.

### Clarify Prompts

#### Session 1: Metadata derivation and command boundaries

```bash
/speckit-clarify Focus on DOC-006 metadata derivation: confirm exactly which checked-in marketplace and plugin manifest files are read at docs build time, how command metadata is derived without a committed generated file, how Claude Code and Codex command surfaces stay separated, and what success signals each command block must show.
```

#### Session 2: Interaction, fallback, and accessibility

```bash
/speckit-clarify Focus on DOC-006 interaction design: confirm the smallest static-first Astro/Starlight selector pattern, keyboard behavior, semantic fallback tables, copy-button behavior if included, and how the payload diagram remains accessible without relying on pointer-only interaction.
```

#### Session 3: Checker, checklist, and handoff boundaries

```bash
/speckit-clarify Focus on DOC-006 checker and handoffs: confirm that the manifest/version checker is repository-only, that it does not accept pasted user JSON, how mismatch states hand off to troubleshooting/update docs, and which first-run checklist checkpoints belong in this slice versus DOC-008 or DOC-010.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Metadata derivation and command boundaries | 5 | Resolved checker input files, command metadata source boundary, platform command separation, expected success signals, and focused validation. Consensus confirmed that manifest-backed facts are read from JSON while command templates/success text may live in a small checked-in docs metadata helper. |
| 2 | Interaction, fallback, and accessibility | 5 | Resolved route-preserving MDX/component shape, native keyboard behavior, visible fallback table/list requirements, progressive copy-button boundary, and text-backed payload diagram requirements. No consensus was needed. |
| 3 | Checker, checklist, and handoff boundaries | 5 | Resolved repository-only checker scope, stable equality-check fields versus informational packaging differences, lightweight mismatch/unavailable handoffs, first-run checklist ownership, and focused validation coverage. No consensus was needed. |

### Consensus Resolution Log

| # | Type | Question/Gap/Finding | Categories | Round | Outcome | Resolution | Analysts Used |
|---|------|----------------------|------------|-------|---------|------------|---------------|
| 1 | Clarify | What counts as command metadata derived from source when command sequences are not fully present in JSON manifests? | [codebase, spec] | 1 | both-agree | Clarified that manifest-backed values are read from checked-in JSON/manifests at build time, while command templates, prerequisites, success signals, and handoff labels may live in a small checked-in docs metadata helper covered by focused validation; no Markdown parsing or generated metadata output. | codebase-analyst, spec-context-analyst |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output: `specs/doc-006-safe-interactive-selector-and-validation-aids/plan.md`.

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Docs site: Astro 6.4.6 and Starlight 0.40.0 under `docs-site/`.
- Content: Markdown/MDX content under `docs-site/src/content/docs/`.
- Components: Astro components under `docs-site/src/components/`.
- Data source: checked-in JSON and manifests from the repository, read at docs build time.
- Validation: `pnpm --dir docs-site validate`, `pnpm --dir docs-site validate:links`, plus a focused metadata/rendering fixture or test.

## Constraints
- Follow the Design Concept at `docs/ai/specs/.process/DOC-006-design-concept.md`.
- Use the existing `choose-your-path` route as the primary surface.
- Quote and preserve the Q&A decisions that drive implementation:
  - Q1 chose "Enhance Choose Your Path".
  - Q3 chose "Build-time read only" for source-derived metadata.
  - Q4 chose "Static-first enhancement".
  - Q5 chose "Lightweight handoff only" for troubleshooting.
  - Q6 chose "Repo consistency only" for the checker.
  - Q7 chose "Accessible static diagram".
  - Q8 chose "Docs plus focused fixture".
- Do not add a reusable generator, committed generated data file, pasted JSON checker, rich app widget, local browser command execution, or auto-config editing.
- Keep the implementation inside docs-site and docs/process files unless Plan records a direct source-data bug.

## Architecture Notes
- Prefer a small source-derived data helper or Astro component that imports or reads checked-in JSON at build time and renders plain, semantic content.
- Keep static fallback content visible and reviewable. Interactivity may enhance filtering/selection, but the page must still communicate all command paths without JavaScript.
- Model selector outputs as documentation guidance: command, platform, scope, prerequisite, expected signal, and next link.
- Model checker output as repository consistency facts and explanatory status, not as a user-local diagnostic.
- Keep payload diagram content text-backed so screen readers and static review can validate source -> dist -> marketplace -> install/cache boundaries.
- Include a focused fixture/test that fails if source-derived command/checker metadata drifts from expected checked-in files.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Complete | Technical context, execution flow, declared file operations, constitution gates, and validation plan |
| `research.md` | Complete | Decision rationales for source-derived metadata, static-first interaction, checker scope, handoffs, and validation |
| `data-model.md` | Complete | Selector/checker/diagram/checklist data structures |
| `contracts/` | Complete | `contracts/doc006-safe-aids.schema.json` |
| `quickstart.md` | Complete | Developer validation steps |

### Plan Reviewability Advisory

| Field | Result |
|-------|--------|
| G3 gate | Passed |
| Plan estimator status | `pass` |
| Projected production LOC | 80 |
| Declared files | 2 production files, 4 new files, 1 modified file, 5 total entries |
| Notes | Manual plan estimate remains 450-700 reviewable LOC, below block threshold and scoped to one docs route slice. |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan` validates both spec and plan together.

### Recommended Domains

| Domain | Why this domain matters |
|--------|-------------------------|
| `ux` | DOC-006 is a user-facing selector/checker flow with copyable commands, labels, expected signals, and first-run checkpoints. |
| `accessibility` | The selector, checker, payload diagram, and fallbacks must be keyboard usable and semantically understandable. |
| `integration` | The docs render facts derived from repository JSON/manifests and must stay consistent with source/dist marketplace and plugin metadata. |
| `error-handling` | Mismatch states and unsupported selections need safe handoffs without implying browser-side local diagnostics. |

### Checklist Prompts

#### 1. UX Checklist

```bash
/speckit-checklist ux

Focus on DOC-006 requirements:
- Platform/path and install-scope selector flow on `choose-your-path`.
- Copyable command blocks with visible platform/scope labels, prerequisites, expected success signals, and next links.
- First-run checklist and selector mismatch handoffs.
- Pay special attention to: whether users can get the right command sequence without reading unrelated platform guidance.
```

#### 2. Accessibility Checklist

```bash
/speckit-checklist accessibility

Focus on DOC-006 requirements:
- Keyboard operation for selector/checker controls.
- Semantic fallback tables or equivalent static content.
- Accessible generated-payload diagram with text-backed explanation.
- Pay special attention to: whether the page remains usable without JavaScript or pointer-only interaction.
```

#### 3. Integration Checklist

```bash
/speckit-checklist integration

Focus on DOC-006 requirements:
- Build-time reads from checked-in marketplace and plugin manifest JSON.
- Repository-only manifest/version checker output.
- Source/dist payload distinction and command metadata freshness.
- Pay special attention to: drift between `.claude-plugin`, `.agents/plugins`, `speckit-pro/*plugin.json`, and `dist/**` values.
```

#### 4. Error-Handling Checklist

```bash
/speckit-checklist error-handling

Focus on DOC-006 requirements:
- Unsupported or ambiguous selector states.
- Manifest/version mismatch explanations.
- Safe handoffs to troubleshooting/update/release docs without claiming a local diagnostic was run.
- Pay special attention to: preventing browser-side shell execution, config writes, or local file inspection.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| UX | 26 | 0 | `spec.md`, `plan.md`, `data-model.md`, `quickstart.md` |
| Accessibility | 23 | 1 found, 1 fixed, 0 remaining | Added explicit accessible name, role, and selected/current/expanded state requirements when custom controls are used. |
| Integration | 26 | 0 | `spec.md`, `plan.md`, `data-model.md`, `contracts/doc006-safe-aids.schema.json`, `quickstart.md` |
| Error Handling | 17 | 1 found, 1 fixed, 0 remaining | Added unsupported/ambiguous selector-state requirements and validation coverage without local diagnostics or repair claims. |
| **Total** | 92 | 2 found, 2 fixed, 0 remaining | G4 passed; no `[Gap]` markers remain across spec, plan, or checklists. |

---

## Phase 5: Tasks

**When to run:** After checklists complete and all gaps are resolved. Output: `specs/doc-006-safe-interactive-selector-and-validation-aids/tasks.md`.

### Tasks Prompt

```bash
/speckit-tasks

## Inputs
- `specs/doc-006-safe-interactive-selector-and-validation-aids/spec.md`
- `specs/doc-006-safe-interactive-selector-and-validation-aids/plan.md`
- `docs/ai/specs/.process/DOC-006-design-concept.md`

## Task Structure
- Organize by user story, not by technical layer.
- Preserve the non-goals from the Design Concept: no local doctor command, no auto-config edits, no pasted JSON checker, no committed generated metadata, no full troubleshooting matrix.
- Include a foundation task for source-derived metadata/data helper only if Plan confirms it is needed.
- Include RED/GREEN validation tasks for the focused metadata/rendering fixture before implementing dependent rendering behavior.
- Keep copyable command blocks, selector output, checker output, payload diagram fallback, and first-run checklist independently reviewable.
- Mark parallel-safe tasks with [P] only when they touch separate files.

## Expected User Story Groups
1. User gets the right platform/path and install-scope command sequence from `choose-your-path`.
2. User or evaluator sees repository manifest/version consistency and generated payload boundaries.
3. User follows first-run checkpoints and safe handoffs without browser-side local execution.

## Constraints
- Use docs-site paths and existing Astro/Starlight conventions.
- Avoid adding dependencies unless Plan records a justified exception.
- Add or update validation only in the smallest focused test/fixture surface needed for source-derived metadata rendering.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| Total Tasks | 32 |
| Phases | 6 |
| Parallel Opportunities | 3 explicit `[P]` setup tasks plus story-level review boundaries after foundation |
| User Stories Covered | 3 |
| Gate G5 | Passed: 32 tasks found and 0 unresolved markers |
| Reviewability task gate | Size-only block: 1280 reviewable LOC and 48 total files exceeded block thresholds; persisted as marker-planning input |

---

## Atomicity Route

**When this is filled:** After the Tasks phase / gate G5, autopilot runs the read-only atomicity classifier and records its decision here.

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/doc-006-safe-interactive-selector-and-validation-aids
```

| Field | Value | Meaning |
|-------|-------|---------|
| Route | `one-navigable-PR` | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| Releasable | `true` | `true`, or `false` for a destructive-migration or concurrency-sensitive change. |
| Signals | `change-shape:modify-heavy` | Decisive detector findings. |
| Warnings | None | Release-safety warnings. |

### Marker Plan

The tasks reviewability result was a valid size-only block, so autopilot generated a durable PR marker plan at:

```text
specs/doc-006-safe-interactive-selector-and-validation-aids/.process/marker-plan/pr-marker-plan.json
```

| Marker | Review Order | Task Boundary | Notes |
|--------|--------------|---------------|-------|
| `foundation` | 1 | T001-T011 | Setup, focused RED checks, source-derived metadata helper, and pre-render validation |
| `us1` | 2 | T012-T017 | Selector controls, static fallback table, selected path output, unsupported states, and route placement |
| `us2` | 3 | T018-T022 | Repository manifest/version checker states and informational packaging rows |
| `us3` | 4 | T023-T027 plus folded polish T028-T032 | Payload diagram, first-run checklist, safe handoff copy, validation, and review packet checks |

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch consistency issues.

### Analyze Prompt

```bash
/speckit-analyze

Focus on DOC-006 consistency:
1. Verify the spec, plan, tasks, and Design Concept agree on `choose-your-path` as the primary surface.
2. Verify source-derived metadata remains build-time read-only with no committed generated file or full generator script.
3. Verify checker scope is repository consistency only and does not accept pasted user JSON or inspect local config.
4. Verify selector/checker/payload diagram interactions have keyboard behavior and static fallback coverage.
5. Verify troubleshooting is a lightweight handoff only and does not absorb DOC-008.
6. Verify tasks include docs validation, link validation, focused metadata/rendering fixture evidence, and manual command-safety/static-fallback review.
7. Verify no task changes plugin behavior, manifests, marketplace files, generated payloads, release automation, or install behavior unless an explicit source-data defect is documented.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| A1 | MEDIUM | `tasks.md` included docs validation, link validation, focused fixture evidence, keyboard checks, and safe rendering work, but did not make the manual command-safety/static-fallback review explicit in a task. | Amended T032 to require manual command-safety and static-fallback review for selector, checker, payload diagram, first-run checklist, and copyable command blocks; added T032 to FR-014, FR-015, and FR-017 coverage. |

### Confidence Gate

| Field | Value |
|-------|-------|
| Gate | G6.5 |
| Mode | Advisory |
| Threshold | 0.90 |
| Result | Soft skip |
| Reason | `confidence-gate.sh` returned `NO_DATA` because no synthesizer confidence emit exists in this environment. No unresolved Analyze consensus items remain, so autopilot proceeds under the advisory fail-open path. |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed with no blocking coverage gaps.

### Implement Prompt

```bash
/speckit-implement

## Approach: Test/fixture first for source-derived data

For tasks touching derived command/checker metadata:
1. RED: Add or update the focused fixture/test that describes expected source-derived data or rendered output.
2. GREEN: Implement the smallest data helper/component/content change needed.
3. REFACTOR: Remove duplication while preserving static fallback content.
4. VERIFY: Run docs validation, link validation, the focused fixture/test, and manual keyboard/static-fallback review.

## Implementation Notes
- Preserve the public `choose-your-path` route while converting the content source to `docs-site/src/content/docs/choose-your-path.mdx` for component placement.
- Use existing docs-site component patterns; prefer one small Astro component/data helper over a rich app surface.
- Read checked-in JSON/manifests at build time only.
- Do not write generated metadata files.
- Do not run shell commands from browser UI.
- Do not accept pasted user JSON.
- Do not auto-edit user config.
- Preserve route handoffs to install pages, first-run, lifecycle, reference, troubleshooting, and security/trust pages.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| Foundation | T001-T011 | 11/11 | Converted route to MDX, added JavaScript-compatible docs data helper, added focused validator, confirmed RED state before component integration, and loaded all six manifest inputs from repo root during docs build. |
| User Story 1 - Selector and commands | T012-T017 | 6/6 | Rendered native radio selector, complete static fallback table, selected-path panels, visible command blocks, optional copy buttons, unsupported/unavailable/ambiguous state text, and route placement. |
| User Story 2 - Checker and payload diagram | T018-T022 | 5/5 | Rendered repository-only checker with 7 pass/info rows, compared values, consistency rules, manifest input availability, mismatch/unavailable fixture coverage, and no user JSON or local config inspection. |
| User Story 3 - First-run checklist and handoffs | T023-T027 | 5/5 | Rendered text-backed payload diagram, first-run checkpoints, safe handoff copy, native controls, visible focus styling, and static content that remains available without selector scripting. |
| Validation and review packet | T028-T032 | 5/5 | Focused validator, docs validation, link validation, full verify, built-HTML manifest review, command-safety/static-fallback review, full SpecKit suite, UAT runbook, PR packet, packet validation, and hazard-collapsed PR route evidence passed. |

---

## Post-Implementation Checklist

- [x] All tasks marked complete in `tasks.md`.
- [x] `pnpm --dir docs-site validate` passes.
- [x] `pnpm --dir docs-site validate:links` passes.
- [x] Focused metadata/rendering fixture or test passes.
- [x] Manual keyboard/source review completed for selector/checker controls.
- [x] Static fallback review completed without relying on JavaScript.
- [x] Command-safety review confirms no browser-side local execution, config writes, plugin runs, or local file inspection.
- [x] Full `bash tests/speckit-pro/run-all.sh` run completed because spec/process surfaces changed.
- [x] PR review packet includes review order, scope budget, traceability, verification evidence, known gaps, and rollback/fallback notes.

---

## Project Structure Reference

```text
racecraft-plugins-public/
├── docs-site/
│   └── src/
│       ├── components/
│       └── content/docs/
├── docs/
│   ├── prd-interactive-documentation.md
│   ├── roadmap-interactive-documentation.md
│   └── ai/specs/
├── speckit-pro/
├── dist/
├── tests/speckit-pro/
└── specs/doc-006-safe-interactive-selector-and-validation-aids/
```

---

Template based on SpecKit best practices and populated for DOC-006 from the technical roadmap plus the Design Concept.

### PR packet validation events
- `pr-packet` validation passed; result `specs/doc-006-safe-interactive-selector-and-validation-aids/.process/pr-packets/pr-packet/validation.json`; PR creation unblocked.
- Final reviewability emitted marker evidence, then collapsed to one aggregate PR because marker checkpoints resolved to the same completed implementation state; live marker-split emission would create unsafe duplicate or empty slice branches.
