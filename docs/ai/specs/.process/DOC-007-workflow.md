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
| Specify | `/speckit-specify` | Complete | spec.md created: 3 user stories, 30 FRs after clarification/checklist refinement, 10 success criteria, 0 `[NEEDS CLARIFICATION]` |
| Clarify | `/speckit-clarify` | Complete | Sessions 1-3 answered IA, generated Markdown format, source evidence, local validation, and DOC-010 handoff boundaries |
| Plan | `/speckit-plan` | Complete | G3 passed; plan selects a docs-site Node generator, committed Markdown output, local package scripts, and no CI workflow edits |
| Checklist | `/speckit-checklist` | Complete | UX, accessibility, integration/source-data, and error-handling complete; 9 error-handling gaps remediated, 0 remaining |
| Tasks | `/speckit-tasks` | Complete | tasks.md created with 38 story-ordered tasks, 8 parallel opportunities, generator/check-mode validation, and explicit dependency boundaries |
| Analyze | `/speckit-analyze` | Complete | 3 findings remediated (0 critical, 2 high, 1 medium); marker counter clean |
| Implement | `/speckit-implement` | Complete | 38/38 tasks complete; generated reference pages current; docs validation and default plugin suite pass |

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
| `pnpm --dir docs-site reference:generate` | Generate committed reference Markdown pages |
| `pnpm --dir docs-site reference:check` | Confirm generated reference pages are current without writing files |
| `pnpm --dir docs-site validate` | Reference freshness check plus Astro content/type check and production build |
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
| Functional Requirements | 22 after IA, format, validation, and handoff clarifications |
| User Stories | 3 |
| Acceptance Criteria | 9 acceptance scenarios |
| `[NEEDS CLARIFICATION]` markers | 0 |
| Unresolved for consensus | None |

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
| 1 | IA and route shape | 5 answered | Use seven generated subpages under `/reference/`: `skills`, `agents`, `manifests`, `hooks`, `scripts`, `tests`, and `source-vs-dist`; preserve `docs-site/src/content/docs/reference.md` as the canonical landing page; keep Reference sidebar with landing page first, generated subpages next, and glossary last; use public links shaped `/racecraft-plugins-public/reference/<slug>/`; fold roadmap-only surfaces into the seven pages as sections or rows. |
| 2 | Generation format and reviewability | 5 answered | Generate committed Markdown pages at `docs-site/src/content/docs/reference/<slug>.md`; use stable section-per-record blocks with ordered fields for purpose, platform mapping, source facts, sources, and inferred notes; render source citations as visible repo-relative path links to GitHub `blob/main/<path>` URLs; render inferred notes only in a dedicated `Inferred notes` field with `Based on:` source paths; include a visible generated notice naming the generator/check command. |
| 3 | Validation and handoffs | 5 answered | Add `reference:generate` and `reference:check` docs-site package scripts around `node scripts/generate-reference-pages.mjs`; make `validate` run `reference:check` before the existing check/build sequence; check mode exits `0` for current, `1` for stale output, and `2` for source/parsing/internal errors; read only allowlisted checked-in source paths and never generated output as source evidence; hand GitHub Actions/docs CI wiring to DOC-010 without editing `.github/workflows/*`. |

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
- Check mode must be read-only and distinguish `0=current`, `1=stale output`,
  and `2=source/parsing/internal error`.
- Do not edit `.github/workflows/*`; DOC-010 owns GitHub Actions/docs CI
  wiring for the docs validation bundle.
- Do not introduce a reusable docs platform beyond DOC-007 needs.
- Do not change plugin behavior, manifests, install flow, generated payload
  content, marketplace behavior, release automation, or hook semantics.

## Architecture Notes
- Inspect existing DOC-006 patterns in `docs-site/src/data/safe-install-aids.ts`
  and `docs-site/scripts/validate-doc006-safe-aids.mjs` for bounded source-file
  reads and deterministic validation.
- Prefer a small docs-site script such as
  `docs-site/scripts/generate-reference-pages.mjs` with `--check` support that
  writes committed Markdown pages rather than MDX or component-rendered data.
- Candidate generated pages should live under a stable reference route grouping,
  `docs-site/src/content/docs/reference/`, while preserving the existing
  `/reference/` landing page. Generate exactly seven first-class subpages:
  `skills`, `agents`, `manifests`, `hooks`, `scripts`, `tests`, and
  `source-vs-dist`.
- Keep the Starlight `Reference` sidebar group: `reference` first, generated
  reference subpages in stable order, and `glossary` last.
- Treat source facts and inferred notes as separate data fields in the generator
  output so generated content cannot blur evidence with interpretation.
- Render each generated record as stable Markdown sections with visible
  `Sources` and `Inferred notes` fields so diffs remain reviewable.
- Add docs-site package scripts `reference:generate` and `reference:check`
  wrapping `node scripts/generate-reference-pages.mjs`, and update
  `validate` to run `reference:check` before the existing check/build sequence.
- Restrict generator source reads to checked-in allowlisted paths: repo
  manifests, `speckit-pro/`, `dist/claude/`, `dist/codex/`, root scripts,
  `tests/speckit-pro/`, and docs-site config/content needed for navigation.
- Record any complexity tradeoff in the plan's Complexity Tracking table,
  especially because Grill Me selected generated full page content over the
  simpler hand-authored roadmap suggestion.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Complete | Technical context, declared file operations, reviewability budget, constitution checks, and docs-site generator architecture |
| `research.md` | Complete | Decision rationales for committed Markdown generation, explicit source allowlist, source/inference separation, read-only check mode, local validation, and reference IA |
| `data-model.md` | Complete | Reference page, record, source fact, source citation, inferred note, platform mapping, file classification, source allowlist, and freshness-check entities |
| `contracts/` | Complete | `reference-generator.md` CLI contract and `reference-inventory.schema.json` inventory schema |
| `quickstart.md` | Complete | Developer commands for generate, check, docs validation, link validation, scope review, and optional Layer 1 safety check |

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
| UX | 17 | 0 | `spec.md` FR-023/SC-008; `plan.md` link-only existing-docs scope; `checklists/ux.md` |
| Accessibility | 22 | 0 | `spec.md` FR-016/FR-024-FR-027/SC-009; `plan.md` generated Markdown accessibility constraints; `checklists/accessibility.md` |
| Integration | 26 | 0 | `spec.md` FR-014; `plan.md` source allowlist, source-input matrix, source-vs-dist mapping, script handoff, deep-link targets; `checklists/integration.md` |
| Error handling | 30 | 9 -> 0 | `spec.md` FR-013/FR-028-FR-030/SC-005/SC-010; `plan.md` generator error-handling contract; `contracts/reference-generator.md` diagnostics; `data-model.md` FreshnessCheck; `checklists/error-handling.md` |

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
| **Total Tasks** | 38 |
| **Phases** | 6 |
| **Parallel Opportunities** | 8 |
| **User Stories Covered** | 3 |

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
| A1 | HIGH | PRD AC-7.1 command/skill matrix fields were not explicit in spec, plan, tasks, or contracts. | Added source-backed invocation, purpose, prerequisite, and expected-output artifact coverage to `spec.md`, `plan.md`, `data-model.md`, `contracts/`, `tasks.md`, and `quickstart.md`. |
| A2 | HIGH | PRD AC-7.2 manifest required/optional field treatment was not explicit for Claude Code versus Codex. | Added runtime-specific required/optional manifest field coverage to `spec.md`, `plan.md`, `data-model.md`, `contracts/`, `tasks.md`, and `quickstart.md`. |
| A3 | MEDIUM | FR-020 generated notice coverage was not validated across all generated pages and was missing from the inventory schema. | Added page-level `generatedNotice` and `sources` schema requirements, notice validation tasks, and check-mode stale-output handling for missing or changed notices. |

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
| Setup and inventory contract | Complete | 3/3 | Generator entry point, package scripts, and Reference sidebar entries added |
| Foundation | Complete | 5/5 | Source allowlist, diagnostics, data model validation, Markdown rendering, and scope budget implemented |
| User Story 1 - user-facing generated references | Complete | 7/7 | Skills, agents, hooks, manifests, landing page, generated notice, command/skill fields, and manifest field sets implemented |
| User Story 2 - maintainer file-layout references | Complete | 5/5 | Scripts, tests, and source-vs-dist generated pages classify repository roles |
| User Story 3 - validation and stale-output checks | Complete | 9/9 | Generate/check mode, stale-output diagnostics, read-only check behavior, docs validation, and link validation verified |
| Polish and handoffs | Complete | 9/9 | Existing install, first-run, troubleshooting, security, and contributor pages now deep-link to generated subpages |

### Implementation Verification

| Check | Result | Evidence |
|-------|--------|----------|
| `pnpm --dir docs-site reference:check` | Pass | Generated pages are current |
| Stale-output probe | Pass | Intentional `skills.md` edit returned exit 1, listed stale page, printed `pnpm --dir docs-site reference:generate`, and did not rewrite the page |
| `pnpm --dir docs-site validate` | Pass | Astro check/build completed; internal links valid |
| `pnpm --dir docs-site validate:links` | Pass | Astro build completed; internal links valid |
| `bash tests/speckit-pro/run-all.sh --layer 1` | Pass | 993/993 |
| `bash tests/speckit-pro/run-all.sh` | Pass | 3009/3009 across default layers 1, 4, and 5 |
| Scope review | Pass | No `.github/workflows/*`, `speckit-pro/`, root marketplace, generated plugin payload, hook, install-flow, or release automation files changed |

---

## Post-Implementation Checklist

- [x] All tasks marked complete in `tasks.md`.
- [x] Generated reference content is current.
- [x] Generator check mode passes and writes nothing.
- [x] `pnpm --dir docs-site validate` passes.
- [x] `pnpm --dir docs-site validate:links` passes.
- [x] Source citation review confirms every generated row links to a real source path.
- [x] Public-readable prose review confirms inferred notes are labeled separately from source facts.
- [x] `git diff --name-only` confirms no plugin behavior, manifest semantics, install flow, generated payload content, marketplace behavior, or release automation changed.
- [x] Additional plugin suite or Layer 1 checks run if implementation touches plugin/spec/payload surfaces beyond docs reference generation.
- [x] PR packet includes review order, scope budget, traceability, verification evidence, known gaps, rollback/fallback notes, and DOC-008/DOC-009/DOC-010 handoffs.

---

## Self-Review

- PASS: The generated reference pages are deterministic committed Markdown and `pnpm --dir docs-site reference:check` reports them current.
- PASS: Check mode is read-only; an intentional stale edit returned exit 1 with the stale page and generate command, and the page was restored only by explicit regeneration.
- PASS: Scope stayed in docs-site reference generation, link-only docs updates, workflow state, and DOC-007 spec artifacts; no `.github/workflows/*`, plugin source behavior, marketplace files, generated plugin payloads, hook semantics, install flow, or release automation changed.
- PASS: `pnpm --dir docs-site validate`, `pnpm --dir docs-site validate:links`, `bash tests/speckit-pro/run-all.sh --layer 1`, and `bash tests/speckit-pro/run-all.sh` passed after docs-site dependencies were installed.
- WATCH: Reviewability gate is warn-only for primary-surface classification; there are no blockers.

---

## PR Creation

- Draft PR: https://github.com/racecraft-lab/racecraft-plugins-public/pull/208
- Base: `main`
- Head: `doc-007-command-workflow-manifest-and-file-layout-reference`
- Reviewability: warn-only for size and surface count; no blockers.

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
