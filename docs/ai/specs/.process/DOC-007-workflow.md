# SpecKit Workflow: DOC-007 - Command, workflow, manifest, and file-layout reference

**Template Version**: 1.0.0
**Created**: 2026-06-17
**Purpose**: Prepare DOC-007 for autonomous execution after DOC-006 completed the safe interactive aids tier.

---

## How to Use This Template

1. Start autopilot with this file:

   ```bash
   $speckit-autopilot docs/ai/specs/.process/DOC-007-workflow.md
   ```

2. Keep `docs/ai/specs/.process/DOC-007-design-concept.md` open as the source of truth for the Grill Me decisions behind this scaffold.

3. Track phase status in the table below as autopilot advances.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during `$speckit-scaffold-spec DOC-007`.
The full Q&A log, Goals, Non-goals, and Open Questions live at:

```text
docs/ai/specs/.process/DOC-007-design-concept.md
```

Re-read it before each phase. The design concept is the source of truth for
generated reference pages, core surface coverage, strict source citations,
generate/check validation, parallel Claude Code/Codex presentation, and the
"no plugin behavior changes" scope cut.

> **Note:** Grill Me is human-in-the-loop only. It is not part of the autopilot
> loop. Once this workflow file is populated and autopilot begins,
> clarifications happen via `/speckit-clarify` and the consensus protocol.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | Complete | spec.md created: 3 user stories, 18 FRs, 9 acceptance scenarios, 0 `[NEEDS CLARIFICATION]`; 3 consensus items carried forward |
| Clarify | `/speckit-clarify` | In Progress | Session 1 is resolving route names/sidebar and reference landing-page behavior |
| Plan | `/speckit-plan` | Pending | Choose deterministic generator architecture and docs-site integration |
| Checklist | `/speckit-checklist` | Pending | Run UX, accessibility, integration/source-data, and error-handling checklists |
| Tasks | `/speckit-tasks` | Pending | Generate story-ordered tasks for generator, pages, validation, and docs checks |
| Analyze | `/speckit-analyze` | Pending | Check consistency across roadmap, design concept, spec, plan, and tasks |
| Implement | `/speckit-implement` | Pending | Implement only after G6 passes |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

Each phase requires human review and approval before proceeding:

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | User stories define generated reference subpages, source citation rules, generated/check behavior, and no behavior changes |
| G2 | After Clarify | Route names/sidebar shape, generated file format, and DOC-010 CI handoff are explicit |
| G3 | After Plan | Generator architecture is deterministic, bounded to docs reference content, and constitution gates pass |
| G4 | After Checklist | UX, accessibility, integration/source-data, and error-handling gaps are fixed or intentionally deferred |
| G5 | After Tasks | Tasks are story-ordered, independently reviewable, and include generator check-mode validation |
| G6 | After Analyze | No critical drift remains between roadmap, design concept, spec, plan, tasks, and validation plan |
| G7 | After Implementation | Generated pages are current, docs-site validation passes, links are valid, and no plugin behavior/payload semantics changed |

---

## Prerequisites

### Constitution Validation

Before starting any workflow phase, verify alignment with `.specify/memory/constitution.md`:

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Plugin Structure Compliance | DOC-007 may read plugin manifests, skills, agents, hooks, scripts, and tests as source evidence, but must not change plugin behavior, generated payload semantics, marketplace behavior, or release automation. | `git diff --name-only` review before PR |
| Script Safety | If a generator/check script is added, keep it deterministic, local-file-only, and plain Node or Bash consistent with docs-site tooling; shell scripts must use `#!/usr/bin/env bash` and `set -euo pipefail`. | `bash -n` on touched shell scripts; run the generator in `--check` mode |
| Test Coverage Before Merge | Generated reference pages need a stale-output check plus docs-site validation and link validation. Run the plugin suite only if plugin/spec surfaces or generated payload semantics are touched. | generator `--check`; `pnpm --dir docs-site validate`; `pnpm --dir docs-site validate:links`; targeted repo checks |
| KISS, Simplicity & YAGNI | Generate only DOC-007 reference pages for core surfaces. Do not introduce a reusable docs platform, browser-side diagnostics, or broad search/CI hardening. | Plan Complexity Tracking plus code review |
| Conventional Commits | PR title must remain public-readable Conventional Commit text. | PR title check |

**Constitution Check:** Run during autopilot preflight before G1.

### Archive Sweep Startup

| Field | Result |
|-------|--------|
| Archive extension | Available, `archive` v1.1.0 |
| Current target excluded | `specs/doc-007-command-workflow-manifest-and-file-layout-reference` |
| Prior active specs | None in active `specs/**` after DOC-006 cleanup |
| Cleanup mode | No cleanup expected before DOC-007 merge |

### Scaffold Preflight Evidence

| Check | Result | Notes |
|-------|--------|-------|
| `specify` CLI | Passed | Found on `PATH` before setup |
| Technical roadmap | Found | `docs/ai/specs/interactive-documentation-technical-roadmap.md` |
| DOC-007 status | Ready | Roadmap lists DOC-007 as ready after DOC-003 and DOC-004 |
| Branch/worktree reuse check | Passed | No local or remote DOC-007 branch/worktree existed before setup |
| Worktree | Created | `.worktrees/doc-007-command-workflow-manifest-and-file-layout-reference` from `origin/main` |
| Reviewability setup gate | Passed | `status=pass`, 395 reviewable LOC, 0 production files, 6 total files, docs/process primary surface |
| Reviewability preset | Installed | `.specify/presets/speckit-pro-reviewability` refreshed; `plan-template` changed |
| Preset resolution | Passed | `spec-template`, `plan-template`, and `tasks-template` resolve to `speckit-pro-reviewability v1.0.0` |
| Slice-size advisory | OK | Grill Me estimate: 242 reviewable LOC, 1 suggested slice, `status=ok` |

### Project Commands

| Command | Purpose |
|---------|---------|
| generator `--check` command chosen during Plan | Confirm generated reference pages are current |
| `pnpm --dir docs-site validate` | Astro content/type check plus production build |
| `pnpm --dir docs-site validate:links` | Docs-site link-validation hook |
| `bash tests/speckit-pro/run-all.sh --layer 1` | Structural safety if source/plugin references or generated payload paths are touched |
| `bash tests/speckit-pro/run-all.sh` | Full plugin validation if implementation touches plugin/spec surfaces, scripts outside docs-site, manifests, or generated payloads |

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | DOC-007 |
| **Name** | Command, workflow, manifest, and file-layout reference |
| **Branch** | `doc-007-command-workflow-manifest-and-file-layout-reference` |
| **Feature directory** | `specs/doc-007-command-workflow-manifest-and-file-layout-reference` |
| **Design Concept** | `docs/ai/specs/.process/DOC-007-design-concept.md` |
| **Technical Roadmap** | `docs/ai/specs/interactive-documentation-technical-roadmap.md` |
| **Prompt Roadmap** | `docs/roadmap-interactive-documentation.md` |
| **Dependencies** | DOC-003, DOC-004 |
| **Enables** | DOC-008, DOC-009 |
| **Priority** | P2 |

### Roadmap Scope Summary

DOC-007 provides stable reference pages for all plugin and repo surfaces:
Claude commands/skills, Codex skills, agents/subagents, hooks, MCP/config
surfaces, manifests, marketplace files, generated payloads, scripts, tests, CI,
release files, and repo structure. The Grill Me interview refined this to
generated reference subpages for core surfaces with strict source citations and
a deterministic `--check` mode.

### Success Criteria Summary

- [ ] Generated reference subpages cover core surfaces: skills, agents, manifests, hooks, scripts, tests, and source-vs-dist layout.
- [ ] Generated pages distinguish source facts from inferred notes.
- [ ] Every generated row links to a real source path.
- [ ] Claude Code and Codex surfaces appear in parallel sections where they map, with runtime-specific differences kept visible.
- [ ] The generator has a deterministic check mode that detects stale generated pages.
- [ ] The implementation does not change plugin behavior, manifest semantics, install flow, generated payload content, or release automation.

---

## Phase 1: Specify

**When to run:** At the start of DOC-007. Output: `specs/doc-007-command-workflow-manifest-and-file-layout-reference/spec.md`.

### Specify Prompt

```bash
/speckit-specify

## Feature: Command, workflow, manifest, and file-layout reference

DOC-007 should turn the existing docs-site reference shell into generated
reference subpages for core repository surfaces. The implementation must produce
full visible reference page content, not only hidden metadata. Source facts must
come from checked-in repository files and every generated row must link to a
real source path. Inferred notes are allowed only when labeled separately from
source facts.

### Goals
- Generate reference subpages for skills, agents, manifests, hooks, scripts,
  tests, and source-vs-dist layout.
- Present Claude Code and Codex surfaces in parallel where they map, with
  runtime-specific differences clearly separated.
- Add deterministic generate and check behavior so stale generated reference
  pages can be detected locally and later wired into DOC-010 CI hardening.
- Keep docs prose public-readable and useful to users, maintainers, and agents.

### Users
- Users evaluating which SpecKit Pro skill, agent, hook, or marketplace surface
  applies to their workflow.
- Maintainers checking source-vs-dist responsibilities before changing plugin
  files.
- Agents needing stable deep links and source citations during later docs,
  troubleshooting, or release work.

### User Stories
1. As a user, I can open generated reference pages and understand the Claude
   Code and Codex skill/agent/hook surfaces without reading the whole repo.
2. As a maintainer, I can inspect generated file-layout and manifest reference
   pages to know which files are source, generated payload, test-only, or release
   infrastructure.
3. As a reviewer or agent, I can run a check mode that proves generated
   reference pages are current with the source files they cite.

### Constraints
- Use existing docs-site/Starlight conventions.
- Read checked-in repository files only; no network access and no browser-side
  local execution.
- Do not accept user-pasted JSON or inspect user-local plugin installs.
- Do not change plugin behavior, manifest semantics, generated payload content,
  marketplace behavior, install flow, or release automation.
- Keep DOC-008 troubleshooting/security/trust depth and DOC-009 contributor
  workflow depth out of scope.

### Open Questions To Resolve
- Exact generated subpage filenames and sidebar grouping.
- Whether generated full page content should be emitted as markdown, MDX, or
  data rendered by a docs component.
- Whether DOC-010 should later wire the check mode into GitHub Actions.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 18 |
| User Stories | 3 |
| Acceptance Criteria | 9 acceptance scenarios |
| `[NEEDS CLARIFICATION]` markers | 0 |
| Unresolved for consensus | 3: [IA], [Format], [CI-Handoff] |

### Files Generated

- [x] `specs/doc-007-command-workflow-manifest-and-file-layout-reference/spec.md`
- [x] `specs/doc-007-command-workflow-manifest-and-file-layout-reference/checklists/requirements.md`
- [x] `.specify/feature.json`

---

## Phase 2: Clarify

**When to run:** After Specify when the spec has areas that could be interpreted multiple ways.

### Clarify Prompts

#### Session 1: IA And Route Shape

```bash
/speckit-clarify Focus on DOC-007 reference IA: choose generated subpage filenames, sidebar grouping, index-page behavior, route slugs, and how existing links to `/reference/` should continue to work.
```

#### Session 2: Generation Format And Reviewability

```bash
/speckit-clarify Focus on DOC-007 generated content format: decide whether generated full page content is markdown, MDX, or component-rendered data; define how source citations and inferred notes appear in reviewable diffs.
```

#### Session 3: Validation And Handoff Boundaries

```bash
/speckit-clarify Focus on DOC-007 validation and handoffs: define generate/check commands, stale-output failure behavior, local-only source reads, and the handoff to DOC-010 for CI integration.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | IA and route shape | Pending | Pending |
| 2 | Generation format and reviewability | Pending | Pending |
| 3 | Validation and handoffs | Pending | Pending |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output: `specs/doc-007-command-workflow-manifest-and-file-layout-reference/plan.md`.

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Docs site: Astro/Starlight under `docs-site/`
- Docs package manager: pnpm lockfile under `docs-site/pnpm-lock.yaml`
- Plugin source: `speckit-pro/`
- Generated payloads: `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/`
- Tests: shell suite under `tests/speckit-pro/`; docs-site validation commands under `docs-site/package.json`
- SpecKit project state: `.specify/` plus docs process files under `docs/ai/specs/.process/`

## Constraints
- Follow `docs/ai/specs/.process/DOC-007-design-concept.md`.
- Generator must be deterministic and local-file-only.
- Generated pages must carry strict source citations and label inferred notes.
- Check mode must fail when generated reference pages are stale.
- Do not introduce a reusable docs platform beyond DOC-007 needs.
- Do not change plugin behavior, manifests, install flow, generated payload
  content, marketplace behavior, release automation, or hook semantics.

## Architecture Notes
- Inspect existing DOC-006 patterns in `docs-site/src/data/safe-install-aids.ts`
  and `docs-site/scripts/validate-doc006-safe-aids.mjs` for bounded source-file
  reads and deterministic validation.
- Prefer a small docs-site script such as
  `docs-site/scripts/generate-reference-pages.mjs` with `--check` support, unless
  Clarify chooses a different file format.
- Candidate generated pages should live under a stable reference route grouping,
  for example `docs-site/src/content/docs/reference/`, while preserving the
  existing `/reference/` landing page.
- Treat source facts and inferred notes as separate data fields in the generator
  output so generated content cannot blur evidence with interpretation.
- Record any complexity tradeoff in the plan's Complexity Tracking table,
  especially because Grill Me selected generated full page content over the
  simpler hand-authored roadmap suggestion.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Pending | Technical context, execution flow, selected generator architecture |
| `research.md` | Pending | Decision rationales for generation format, source citation model, and check mode |
| `data-model.md` | Pending | Surface inventory, source fact, inferred note, platform mapping, generated page |
| `contracts/` | Pending | Schema for generated reference inventory if useful |
| `quickstart.md` | Pending | Developer commands for generate, check, docs validation, and link validation |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan`; validate both spec and plan together.

### Recommended Domain Checklists

#### 1. UX Checklist

Why this domain: DOC-007 changes public docs navigation and reference reading flows.

```bash
/speckit-checklist ux

Focus on DOC-007 requirements:
- Generated reference subpages, index route, and sidebar grouping.
- Deep links from existing install, first-run, troubleshooting, security, and contributor pages.
- Parallel Claude Code/Codex sections that stay scannable.
- Pay special attention to: generated full page content remaining useful to humans rather than becoming a raw file dump.
```

#### 2. Accessibility Checklist

Why this domain: Reference tables/lists must remain navigable and readable in generated docs.

```bash
/speckit-checklist accessibility

Focus on DOC-007 requirements:
- Generated tables or lists with meaningful headings and link text.
- Source-path links that remain screen-reader friendly.
- Generated page structure that does not depend on JavaScript.
- Pay special attention to: dense generated inventories staying readable with keyboard navigation and assistive technology.
```

#### 3. Integration Checklist

Why this domain: The generator reads many repository source files and must keep source-vs-dist boundaries correct.

```bash
/speckit-checklist integration

Focus on DOC-007 requirements:
- Source reads from `speckit-pro/`, `dist/claude/`, `dist/codex/`, manifests, scripts, and tests.
- Strict source citation links for every generated row.
- Deterministic generate/check behavior and stale-output failure mode.
- Pay special attention to: avoiding source facts that silently become inferred prose.
```

#### 4. Error-Handling Checklist

Why this domain: Check mode and source-file parsing need clear behavior when files are missing, malformed, or intentionally absent.

```bash
/speckit-checklist error-handling

Focus on DOC-007 requirements:
- Missing source files, malformed JSON, missing frontmatter, and absent optional surfaces.
- Check-mode exit behavior and actionable error messages.
- Handoff when generated reference content is stale.
- Pay special attention to: failing safely without mutating files in check mode.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| UX | Pending | Pending | Pending |
| Accessibility | Pending | Pending | Pending |
| Integration | Pending | Pending | Pending |
| Error handling | Pending | Pending | Pending |

---

## Phase 5: Tasks

**When to run:** After checklists complete and all gaps are resolved. Output: `specs/doc-007-command-workflow-manifest-and-file-layout-reference/tasks.md`.

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Organize by user story, not by technical layer.
- Mark parallel-safe tasks with [P] only when they touch separate files.
- Include tests or checks before relying on generated output.
- Keep generator, generated pages, and validation tasks small and reviewable.

## Implementation Phases
1. Setup and source inventory contract.
2. User Story 1 - generated user-facing reference pages for skills, agents, hooks, and manifests.
3. User Story 2 - generated maintainer file-layout, scripts, tests, and source-vs-dist pages.
4. User Story 3 - generate/check command, stale-output validation, docs validation, and review packet.
5. Polish - links from existing shell pages, source citations, public-readable wording, and handoff notes for DOC-008/DOC-009/DOC-010.

## Constraints
- Reference `docs/ai/specs/.process/DOC-007-design-concept.md`.
- Do not change plugin behavior, generated payload semantics, install flow, marketplace behavior, or release automation.
- Keep generated output deterministic and reviewable.
- Include validation for strict source citations and source-fact vs inferred-note separation.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | Pending |
| **Phases** | Pending |
| **Parallel Opportunities** | Pending |
| **User Stories Covered** | Pending |

---

## Atomicity Route

After Tasks/G5, autopilot records the atomicity route here:

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | Pending | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | Pending | `true`, or `false` for release-sensitive changes. |
| **Signals** | Pending | Decisive detector findings behind the route. |
| **Warnings** | Pending | Release-safety warnings, if any. |

To produce the decision, run the classifier against the feature directory:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/doc-007-command-workflow-manifest-and-file-layout-reference
```

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```bash
/speckit-analyze

Focus on DOC-007 consistency:
1. Verify spec.md, plan.md, tasks.md, and the Design Concept agree that DOC-007 generates full reference subpages.
2. Verify every generated reference row has a real source path citation requirement.
3. Verify source facts and inferred notes are separated across spec, data model, generator plan, and tasks.
4. Verify check mode is read-only and detects stale generated pages.
5. Verify no task changes plugin behavior, manifest semantics, install flow, generated payload content, marketplace behavior, or release automation.
6. Verify DOC-008, DOC-009, and DOC-010 handoffs are explicit but not implemented in this slice.
7. Verify validation includes generator check mode, docs-site validation, link validation, and any focused source inventory tests.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| Pending | Pending | Pending | Pending |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed with no blocking gaps.

### Implement Prompt

```bash
/speckit-implement

## Approach
Follow tasks.md in order. Use TDD or check-first implementation where practical:

1. RED: Add or run the generator check/test that should fail before generated reference output exists or is current.
2. GREEN: Implement the smallest deterministic generator/page change needed.
3. REFACTOR: Keep source parsing explicit and readable; avoid broad abstractions.
4. VERIFY: Run generator check mode, docs-site validation, link validation, and any focused source inventory tests.

## Pre-Implementation Setup
1. Confirm branch is `doc-007-command-workflow-manifest-and-file-layout-reference`.
2. Confirm worktree is clean before implementation.
3. Read `docs/ai/specs/.process/DOC-007-design-concept.md`, `spec.md`, `plan.md`, and `tasks.md`.
4. Confirm docs-site dependencies are available before running docs validation.

## Implementation Notes
- Use existing docs-site patterns from DOC-002 through DOC-006.
- Keep generated reference pages public-readable, not raw implementation dumps.
- Preserve existing install, first-run, lifecycle, troubleshooting, security, and contributor route links.
- Do not run shell commands from browser UI and do not inspect user-local installs.
- If the generator reads JSON, parse JSON structurally rather than with ad hoc string matching.
- If the generator parses Markdown/frontmatter, use a deterministic parser or a simple bounded parser with focused tests.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| Setup and inventory contract | Pending | 0/0 | Pending tasks generation |
| User Story 1 - user-facing generated references | Pending | 0/0 | Pending tasks generation |
| User Story 2 - maintainer file-layout references | Pending | 0/0 | Pending tasks generation |
| User Story 3 - validation and stale-output checks | Pending | 0/0 | Pending tasks generation |
| Polish and handoffs | Pending | 0/0 | Pending tasks generation |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in `tasks.md`.
- [ ] Generated reference content is current.
- [ ] Generator check mode passes and writes nothing.
- [ ] `pnpm --dir docs-site validate` passes.
- [ ] `pnpm --dir docs-site validate:links` passes.
- [ ] Source citation review confirms every generated row links to a real source path.
- [ ] Public-readable prose review confirms inferred notes are labeled separately from source facts.
- [ ] `git diff --name-only` confirms no plugin behavior, manifest semantics, install flow, generated payload content, marketplace behavior, or release automation changed.
- [ ] Additional plugin suite or Layer 1 checks run if implementation touches plugin/spec/payload surfaces beyond docs reference generation.
- [ ] PR packet includes review order, scope budget, traceability, verification evidence, known gaps, rollback/fallback notes, and DOC-008/DOC-009/DOC-010 handoffs.

---

## Project Structure Reference

```text
racecraft-plugins-public/
├── docs-site/
│   ├── scripts/
│   └── src/content/docs/
├── docs/
│   ├── roadmap-interactive-documentation.md
│   └── ai/specs/
├── speckit-pro/
│   ├── agents/
│   ├── codex-agents/
│   ├── codex-skills/
│   ├── hooks/
│   ├── scripts/
│   └── skills/
├── dist/
│   ├── claude/speckit-pro/
│   └── codex/speckit-pro/
├── scripts/
├── tests/speckit-pro/
└── specs/doc-007-command-workflow-manifest-and-file-layout-reference/
```

---

Template based on SpecKit best practices and populated for DOC-007 from the technical roadmap plus the Design Concept.
