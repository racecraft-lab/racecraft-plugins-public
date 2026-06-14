# SpecKit Workflow: DOC-002 - Unified landing page and IA shell

**Template Version**: 1.0.0
**Created**: 2026-06-13
**Purpose**: Prepare DOC-002 for autonomous execution after the DOC-001 framework spike selected Astro/Starlight and produced the route-level IA contract.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during `$speckit-scaffold-spec DOC-002`.
The full Q&A log, Goals, Non-goals, and Open Questions live at:

```text
docs/ai/specs/.process/DOC-002-design-concept.md
```

Re-read it before each phase. The design concept is the source of truth for the accepted `docs-site/` path, docs-site-scoped `pnpm`, thin landing-page scope, 11-route shell, Starlight internal-link validation, Pages-ready config without publish workflow, and two-PR-slice intent inside one DOC-002 workflow.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | Complete | spec.md created and checklist-remediated: 23 FRs, 3 user stories, 7 acceptance scenarios, 12 SCs; 0 clarification markers; preserves DOC-002 two-slice intent |
| Clarify | `/speckit-clarify` | Complete | Skipped by G1 routing: `spec.md` had zero clarification markers |
| Plan | `/speckit-plan` | Complete | plan.md, research.md, data-model.md, route-shell contract, and quickstart created; Astro/Starlight, pnpm, Pages-ready config, and build-integrated link validation selected |
| Checklist | `/speckit-checklist` | Complete | UX, accessibility, reliability, and error-handling complete; 25 gaps remediated, 0 remaining |
| Tasks | `/speckit-tasks` | Complete | 43 tasks across Foundation, US1-US3, and Polish; 14 parallel-safe; FR-001 through FR-023 mapped; G5 passed; task reviewability evidence recorded |
| Analyze | `/speckit-analyze` | Complete | 3 findings remediated; explicit AC-2.1 through AC-2.5 task coverage added; checklist and workflow state reconciled; marker counter clean |
| Implement | `/speckit-implement` | In Progress | Landing page complete; starting route-shell and Diataxis navigation tasks T013-T026 |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | User stories cover landing, IA shell, source-vs-payload explanation, build/link validation, and Pages-ready config |
| G2 | After Clarify | Site path, package scripts, Pages config, route ownership, and validation scope are explicit |
| G3 | After Plan | Astro/Starlight architecture, scripts, routes, and validation commands are concrete and within DOC-002 scope |
| G4 | After Checklist | All true gaps are remediated or explicitly deferred to DOC-003 through DOC-010 |
| G5 | After Tasks | Tasks are vertical and preserve the accepted two-slice intent inside one DOC-002 workflow |
| G6 | After Analyze | No CRITICAL findings and no drift from the design concept, DOC-001 decision record, or roadmap boundaries |
| G7 | After Implementation | Production build and internal-link validation pass; route shell satisfies AC-2.1 through AC-2.5 |

---

## Prerequisites

### Constitution Validation

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Plugin source safety | DOC-002 must not change plugin behavior, marketplace manifests, generated payloads, hooks, agents, or release automation unless a later DOC spec explicitly owns it | `git diff --name-only` review before PR |
| Reviewability | Setup gate passed with projected 395 reviewable LOC, 0 production files, 6 total files, and no blockers; accepted split intent is two PR slices inside one DOC-002 workflow | `bash speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh setup docs/roadmap-interactive-documentation.md` |
| Docs validation | DOC-002 must define and run a production build plus internal-link validation for `docs-site/` | `cd docs-site && pnpm build` plus the selected Starlight link-validation command |
| Accessibility fallback | Route shells must not hide critical platform choices, source-vs-payload explanations, route orientation, or future DOC-006 enhancement fallbacks behind inaccessible dynamic behavior | Manual review of semantic static content, native links, heading order, visible focus preservation, non-color-only meaning, and Starlight defaults |
| Existing repo checks | If plugin/spec scaffold files are touched, keep structural checks green | `bash tests/speckit-pro/run-all.sh --layer 1` |

**Constitution Check:** Verified before G1.

### Autopilot Preflight

| Check | Result | Evidence |
|-------|--------|----------|
| Archive Sweep | Complete | Archive extension installed; no previously merged active specs under `specs/**`; current target `specs/doc-002-unified-landing-page-and-ia-shell` excluded |
| Prerequisites | Pass | `check-prerequisites.sh docs/ai/specs/.process/DOC-002-workflow.md` |
| Confidence Gate Mode | Advisory | `resolve-confidence-mode.sh -- docs/ai/specs/.process/DOC-002-workflow.md` |
| Reviewability Setup | Pass | 395 reviewable LOC, 0 production files, 6 total files, primary surface `docs/process` |
| Spec Index | Current | `generate-spec-index.sh --check` |
| Structural Baseline | Pass | `bash tests/speckit-pro/run-all.sh --layer 1` -> 979/979 passed |

### Project Commands

Initial command detection returned `N/A` for build, typecheck, lint, unit,
integration, and full verification because `docs-site/` does not exist before
DOC-002 implementation. Re-detect after the site scaffold is created.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | DOC-002 |
| **Name** | Unified landing page and IA shell |
| **Branch** | `doc-002-unified-landing-page-and-ia-shell` |
| **Feature directory** | `specs/doc-002-unified-landing-page-and-ia-shell` |
| **Design Concept** | `docs/ai/specs/.process/DOC-002-design-concept.md` |
| **Roadmap** | `docs/roadmap-interactive-documentation.md` and `docs/ai/specs/interactive-documentation-technical-roadmap.md` |
| **Dependencies** | DOC-001 completed and archived; consume `docs/ai/research/interactive-documentation-framework-spike.md` |
| **Enables** | DOC-003, DOC-004, DOC-006, and DOC-010 |
| **Priority** | P1 |
| **Reviewability estimate** | Setup gate pass; Grill Me forward estimate 405 LOC, suggested 2 slices, advisory warn |

### Success Criteria Summary

- [ ] AC-2.1: Landing page states marketplace purpose, current plugin, primary value, and supported platforms in one screen.
- [ ] AC-2.2: IA exposes Tutorials, How-to, Reference, and Explanation sections.
- [ ] AC-2.3: Claude Code and Codex paths are selectable from the first interaction.
- [ ] AC-2.4: Docs distinguish authoring source `speckit-pro/` from generated install payloads under `dist/claude/**` and `dist/codex/**`.
- [ ] AC-2.5: Every top-level nav label has a stated purpose and success criterion.

### Accepted Slice Intent

Keep one DOC-002 workflow and one roadmap identity. If autopilot's atomicity and layer-planning path supports split PRs, prefer:

1. **Shell and routes:** create the Astro/Starlight `docs-site/` app, landing page, Diataxis sidebar, and 11 skeletal route pages.
2. **Validation and config hardening:** add internal-link validation, Pages-ready config documentation, and final build/link verification.

If the classifier returns `one-navigable-PR`, preserve the same review order in the PR body.

---

## Phase 1: Specify

**When to run:** At the start of DOC-002. Output: `specs/doc-002-unified-landing-page-and-ia-shell/spec.md`.

### Specify Prompt

```bash
/speckit-specify

## Feature: Unified landing page and IA shell

### Problem Statement
Racecraft Public Plugins and `speckit-pro` need a public static docs shell so first-time users understand what the marketplace is, which platforms are supported, why source and generated payloads differ, and where to go next. DOC-001 selected Astro/Starlight and produced the 11-route IA skeleton; DOC-002 turns that decision record into the first usable site foundation.

### Users
- First-time users deciding between Claude Code and Codex paths.
- Existing plugin users looking for reference, troubleshooting, security, lifecycle, and contributor entry points.
- Maintainers who need a docs shell that later DOC specs can fill without changing route contracts.

### User Stories
- As a first-time visitor, I can understand Racecraft Public Plugins, the current `speckit-pro` plugin, supported platforms, and the next action from the first screen.
- As a user with a specific task, I can navigate to one of the 11 top-level IA routes and see that route's purpose, owner DOC, success criterion, and source evidence.
- As a maintainer, I can build the Astro/Starlight site and validate internal links before publishing or handing the shell to later DOC specs.

### Functional Requirements Seed
- Create `docs-site/` as the Astro/Starlight site app.
- Use docs-site-scoped `pnpm` scripts for install, build, preview, and link validation.
- Implement a thin landing page, not a full marketing page and not a placeholder.
- Create skeletal pages for: Start, Install: Claude Code, Install: Codex, First Run, Choose Your Path, Reference, Troubleshooting, Security & Trust, Contribute & Release, Spec Kit Lifecycle, and Glossary.
- Organize navigation by Diataxis groups: Tutorials, How-to, Reference, and Explanation.
- Explain source tree versus generated install payloads on the landing page and the Reference shell.
- Add internal-link validation now, plus production build verification.
- Make Astro/Starlight Pages configuration explicit, but do not add a GitHub Pages publish workflow.

### Constraints
- Consume `docs/ai/research/interactive-documentation-framework-spike.md`; do not reopen framework selection unless a true hard blocker appears.
- Keep README files as source evidence only; do not convert or redirect them in DOC-002.
- Do not implement full platform install content, interactive widgets, broad docs CI hardening, docs versioning, or plugin behavior changes.
- Keep one DOC-002 workflow with two-slice intent: shell/routes first, validation/config second.

### Out of Scope
- Full Claude Code install content, Codex install content, first-run tutorial, troubleshooting matrix, security/trust model, maintainer workflow, search/accessibility hardening, responsive screenshots, docs deployment workflow, analytics, and live local command execution.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 23 |
| User Stories | 3 |
| Acceptance Criteria | AC-2.1 through AC-2.5 covered by 7 acceptance scenarios and 12 measurable outcomes |

### Files Generated

- [x] `specs/doc-002-unified-landing-page-and-ia-shell/spec.md`

---

## Phase 2: Clarify

**When to run:** After Specify if any implementation boundary could be interpreted multiple ways.

### Clarify Prompts

#### Session 1: Site scaffold and Pages-ready config

```bash
/speckit-clarify Focus on site scaffold and Pages-ready config: confirm the `docs-site/` path, package scripts, Astro `site`/`base`/`trailingSlash` assumptions, and the exact boundary between DOC-002 config and DOC-010 publish workflow.
```

#### Session 2: IA shell and content ownership

```bash
/speckit-clarify Focus on IA shell and content ownership: confirm every top-level route's purpose, Diataxis group, owner DOC, success criterion, source evidence, and what skeletal content is enough for DOC-002 without drifting into DOC-003 through DOC-010.
```

#### Session 3: Validation and slicing

```bash
/speckit-clarify Focus on validation and slicing: confirm Starlight internal-link validation package choice, production build command, what counts as sufficient manual nav inspection, and how the two accepted PR slices should map to tasks.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Site scaffold and Pages-ready config | 0 | Skipped by G1 routing because `spec.md` had zero clarification markers |
| 2 | IA shell and content ownership | 0 | Skipped by G1 routing because `spec.md` had zero clarification markers |
| 3 | Validation and slicing | 0 | Skipped by G1 routing because `spec.md` had zero clarification markers |

---

## Phase 3: Plan

**When to run:** After the spec is finalized. Output: `specs/doc-002-unified-landing-page-and-ia-shell/plan.md`.

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Docs framework: Astro with Starlight, unless refreshed official-source evidence finds a true hard blocker.
- Authoring: Markdown/MDX pages and Starlight navigation/sidebar conventions.
- Package manager: `pnpm` scoped to `docs-site/`.
- Search: Starlight/Pagefind defaults are acceptable for DOC-002; DOC-010 hardens search policy.
- Validation: production build plus selected Starlight internal-link validation.
- Deployment target: GitHub Pages from this repository; DOC-002 records config assumptions but does not add the publish workflow.
- Backend/database/runtime services: none.

## Constraints
- Use the DOC-001 decision record and IA skeleton as the input contract.
- Keep README files as source evidence only.
- Keep plugin behavior, generated payloads, marketplace manifests, hooks, agents, and release automation out of scope.
- Leave full platform content and docs CI/deployment hardening to later DOC specs.
- Preserve the accepted two-slice intent inside one DOC-002 workflow.

## Architecture Notes
- Create `docs-site/` as the docs app root.
- Use Diataxis sidebar groups: Tutorials, How-to, Reference, Explanation.
- Include all 11 route shells from the DOC-001 IA skeleton.
- Put source-vs-generated-payload explanation on the landing page and Reference shell.
- Add link validation now because Q6 selected it over deferral; keep validation limited to build plus links because Q7 rejected broader CI hardening.
- Make Pages config explicit now because Q9 selected config now and workflow later.
- Treat exact package versions, Astro Pages settings, and validator package choice as Plan decisions based on refreshed current docs.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Complete | Technical context, Declared File Operations, reviewability budget, split decision, PR packet source, Pages config, and command roles |
| `research.md` | Complete | Astro/Starlight, package versions, GitHub Pages config, sidebar, Pagefind, and link-validator decisions |
| `data-model.md` | Complete | Documentation site, route shell, navigation group, source evidence, and validation command role model |
| `contracts/` | Complete | `contracts/route-shell-manifest.json` records route shells, validation boundaries, and docs-site commands |
| `quickstart.md` | Complete | Local docs-site install, dev, build, link validation, full validation, preview, and review checks |

---

## Phase 4: Domain Checklists

**When to run:** After Plan. Use enriched prompts; do not run bare domains.

### Recommended Domains

#### 1. UX Checklist

Why this domain: DOC-002 is a public-facing navigation and landing-page shell.

```bash
/speckit-checklist ux

Focus on DOC-002 requirements:
- Landing page explains purpose, plugin, supported platforms, and next action within one screen.
- Claude Code and Codex paths are selectable from the first interaction.
- Diataxis sidebar groups make Tutorials, How-to, Reference, and Explanation discoverable.
- Every route shell has enough content to orient users without taking over later DOC specs.
- Pay special attention to: thin actionable shell versus empty placeholder or oversized marketing page.
```

#### 2. Accessibility Checklist

Why this domain: The docs site is public and must preserve static/keyboard fallback for navigation and future interactive aids.

```bash
/speckit-checklist accessibility

Focus on DOC-002 requirements:
- Critical platform choice and source-vs-payload explanation are available as static content.
- Navigation, links, headings, focus order, and Starlight defaults support keyboard and screen-reader use.
- Skeletal pages do not rely on inaccessible widgets or hidden JavaScript-only behavior.
- Pay special attention to: route shells that later DOC-006 interactive aids may enhance without breaking static fallback.
```

#### 3. Reliability Checklist

Why this domain: DOC-002 introduces a new docs build and link-validation surface.

```bash
/speckit-checklist reliability

Focus on DOC-002 requirements:
- `pnpm` scripts are documented and runnable from `docs-site/`.
- Production build and internal-link validation failure modes are clear.
- Pages-ready config assumptions are explicit even without a publish workflow.
- Pay special attention to: avoiding flaky or network-dependent validation in the minimum completion gate.
```

#### 4. Error-Handling Checklist

Why this domain: DOC-001 identified fallback rules if Astro/Starlight hits a true hard blocker.

```bash
/speckit-checklist error-handling

Focus on DOC-002 requirements:
- Framework hard blockers are distinct from fixable configuration errors.
- Fallback order is Docusaurus/MDX, then VitePress, then repo-native Markdown.
- Missing package manager, build failure, link validation failure, and Pages base/path mismatch have clear next actions.
- Pay special attention to: not reopening framework selection for ordinary config failures.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| UX | 15 | 2 -> 0 | 15/15 traceable |
| Accessibility | 19 | 9 -> 0 | 19/19 traceable |
| Reliability | 19 | 7 -> 0 | 19/19 traceable |
| Error Handling | 25 | 7 -> 0 | 25/25 traceable; `checklists/error-handling.md`; framework blocker contract, setup/build/link/Pages next actions, and fallback boundary |
| **Total** | 78 | 25 -> 0 | All selected checklist domains complete with zero remaining gap markers |

---

## Phase 5: Tasks

**When to run:** After checklists complete. Output: `specs/doc-002-unified-landing-page-and-ia-shell/tasks.md`.

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Organize by user story and accepted slice intent, not by horizontal layers.
- Keep tasks small enough for shell/routes and validation/config to be reviewed separately.
- Add tests or validation tasks before implementation where feasible.
- Mark parallel-safe tasks with [P].
- Reference `docs/ai/specs/.process/DOC-002-design-concept.md` for scope decisions.

## Implementation Phases
1. Foundation: refresh official docs, create `docs-site/`, define package scripts, and establish Astro/Starlight config.
2. User Story 1: landing page with marketplace purpose, `speckit-pro`, platform choice, and source-vs-payload explanation.
3. User Story 2: 11 route shells and Diataxis sidebar groups with owner DOC and success criteria.
4. User Story 3: production build, internal-link validation, Pages-ready config notes, and quickstart.
5. Polish: verify route coverage, README-as-source boundaries, no plugin behavior drift, and final review packet evidence.

## Constraints
- Do not create a GitHub Pages publish workflow in DOC-002.
- Do not convert README files or duplicate full install/troubleshooting/security/reference content.
- Do not touch plugin marketplace manifests, generated payloads, hooks, agents, or release automation.
- Preserve the two-slice review order: shell/routes first, validation/config second.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | 43 |
| **Phases** | 5: Foundation, User Story 1, User Story 2, User Story 3, Polish |
| **Parallel Opportunities** | 14 |
| **User Stories Covered** | 3 |
| **FR Coverage** | FR-001 through FR-023 mapped in `tasks.md` Coverage Matrix |
| **Reviewability Notes** | Slice 1 is T001-T026 for shell/routes; Slice 2 is T027-T043 for validation/config hardening and final review evidence; PR packet tasks cover review order, traceability, verification evidence, non-goals, and scope budget |
| **Unresolved Items** | None |

### Task Reviewability Gate

| Field | Value |
|-------|-------|
| **Status** | `block` |
| **Mode** | `tasks` |
| **Exit Code** | 1 |
| **Evidence** | `specs/doc-002-unified-landing-page-and-ia-shell/.process/reviewability/tasks-gate.json` |
| **Reviewable LOC** | 1720 |
| **Production Files** | 2 |
| **Total Files** | 75 |
| **Decision** | Size-only task estimate recorded; no correctness block. Continue to Analyze and preserve final reviewability backstop before PR creation. |

---

## Atomicity Route

To produce the decision after Tasks, run the classifier against the feature directory:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/doc-002-unified-landing-page-and-ia-shell
```

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | `one-navigable-PR` | One navigable PR; preserve shell/routes before validation/config in review order |
| **Releasable** | `true` | No destructive or concurrency-sensitive release warning |
| **Signals** | `change-shape:modify-heavy` | Decisive detector findings |
| **Warnings** | None | Release-safety warnings |

## Layer Plan

| Field | Value |
|-------|-------|
| **Status** | Skipped |
| **Reason** | Atomicity route is `one-navigable-PR`, so PRSG-008 layer planning is not required |

---

## Phase 6: Analyze

**When to run:** Always run after Tasks.

### Analyze Prompt

```bash
/speckit-analyze

Focus on:
1. Cross-artifact consistency across spec.md, plan.md, tasks.md, `docs/ai/specs/.process/DOC-002-design-concept.md`, and `docs/ai/research/interactive-documentation-framework-spike.md`.
2. Scope drift: reject full platform content, README conversion, publish workflow, broad docs CI hardening, analytics, plugin behavior changes, generated payload changes, or interactive widgets beyond basic navigation.
3. Acceptance coverage for AC-2.1 through AC-2.5.
4. Validation coverage for production build and internal-link validation.
5. Two-slice intent: shell/routes first and validation/config second, unless atomicity routing documents a safer one-PR path.
6. Fallback logic: distinguish true Astro/Starlight hard blockers from fixable configuration errors.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| F1 | MEDIUM | `tasks.md` mapped FR-001 through FR-023 but did not explicitly map AC-2.1 through AC-2.5, even though Analyze focuses on acceptance coverage. | Added an Acceptance Coverage Matrix to `tasks.md` mapping AC-2.1 through AC-2.5 to task IDs and verification notes. |
| F2 | MEDIUM | UX, accessibility, and reliability checklists still contained unchecked items while the workflow Checklist Results table reported zero remaining gaps. | Marked satisfied checklist items resolved after confirming coverage in spec, plan, research, data model, route contract, quickstart, and tasks. |
| F3 | LOW | Specify Results table still said 17 functional requirements and 7 measurable outcomes after the current spec expanded to FR-001 through FR-023 and SC-001 through SC-012. | Updated the workflow Specify Results counts to 23 functional requirements and 12 measurable outcomes. |

### Pre-Implement Confidence

📊 Confidence: 0.94

- Task understanding: 0.96
- Approach clarity: 0.94
- Requirements alignment: 0.95
- Risk assessment: 0.91
- Completeness: 0.94

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed.

### Implement Prompt

```bash
/speckit-implement

## Approach: Docs-site validation first

1. Confirm branch `doc-002-unified-landing-page-and-ia-shell`.
2. Re-read `docs/ai/specs/.process/DOC-002-design-concept.md`.
3. Implement the minimum Astro/Starlight shell needed for AC-2.1 through AC-2.5.
4. Keep route pages skeletal and owner-doc-labeled.
5. Run `pnpm build` and selected link validation from `docs-site/`.
6. Run repo structural checks if SpecKit scaffold artifacts or plugin surfaces are touched.

## Implementation Notes
- `docs-site/` is the docs app root.
- README files are source evidence only.
- Landing and Reference shell explain source tree versus generated payloads.
- Do not add GitHub Pages publish workflow in DOC-002.
- Do not broaden validation beyond production build plus internal links.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| Foundation | T001-T007 | Complete | Created `docs-site/` package/config baseline and content directories; dependency install and validation scripts remain owned by Slice 2 |
| Landing page | T008-T012 | Complete | Created thin `index.mdx` with platform links and source-vs-payload explanation |
| Route shell | T013-T026 | In Progress | Next group creates route shells and final Diataxis sidebar groups |
| Validation/config | Pending | Pending | Pending |
| Polish | Pending | Pending | Pending |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in `tasks.md`.
- [ ] `docs-site/` package scripts documented.
- [ ] Production build passes.
- [ ] Internal-link validation passes.
- [ ] All 11 route shells exist and are reachable.
- [ ] Landing page satisfies AC-2.1 through AC-2.4.
- [ ] Every top-level nav label has purpose and success criterion.
- [ ] README files remain source evidence only.
- [ ] No plugin behavior, marketplace, generated payload, hook, agent, or release automation drift.
- [ ] PR packet records the accepted split or one-PR fallback with evidence.

---

## Lessons Learned

### What Worked Well

- Pending.

### Challenges Encountered

- Pending.

### Patterns to Reuse

- Pending.
