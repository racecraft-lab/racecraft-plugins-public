# SpecKit Workflow: DOC-010 - Search, Accessibility, Deep Links, Docs Validation

**Template Version**: 1.0.0
**Created**: 2026-06-19
**Purpose**: Drive the autopilot through the SpecKit workflow for DOC-010, using the interactive documentation roadmap plus the setup Grill Me decisions.

---

## How to Use This Workflow

Run this workflow from the DOC-010 worktree:

```bash
$speckit-autopilot docs/ai/specs/.process/DOC-010-workflow.md
```

This file is already populated for DOC-010. Do not replace it with the generic workflow template.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during `$speckit-scaffold-spec DOC-010`.
The full Q&A log, Goals, Non-goals, and Open Questions live at:

```text
docs/ai/specs/.process/DOC-010-design-concept.md
```

Re-read the design concept before each phase. It is the source of truth for setup decisions:

- Harden existing docs-site routes; do not add a new top-level route.
- Use Starlight/Pagefind search and harden glossary, heading, and deep-link conventions.
- Combine deterministic checks with manual/browser accessibility and responsive review evidence.
- Add a conditional docs-site validation path to PR Checks.
- Add minimal Playwright smoke coverage for key routes and mobile/desktop viewports.
- Extend existing docs-site validators rather than creating a broad new validation framework.

> Grill Me is human-in-the-loop only. It is not part of the autopilot loop. Once this workflow starts, clarifications happen through `/speckit-clarify` and consensus, never through grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | Complete | Created `spec.md`; G1 passed with 13 FRs, 4 user stories, and 0 clarification markers |
| Clarify | `/speckit-clarify` | Complete | Resolved route list, CI condition, and Playwright smoke/evidence shape; G2 passed |
| Plan | `/speckit-plan` | Complete | Created plan, research, data model, quickstart, and three contracts; G3 and reviewability estimator passed |
| Checklist | `/speckit-checklist` | Complete | Accessibility, UX, reliability, and security remediation evidence was appended; original checklist prompts remain as audit records |
| Tasks | `/speckit-tasks` | Complete | Generated 40 tasks; G5 passed; size-only task reviewability block persisted as marker-plan evidence |
| Analyze | `/speckit-analyze` | Complete | G6 passed with 0 findings; no consensus remediation required |
| Implement | `/speckit-implement` | Pending | Execute focused docs-site hardening with validation evidence |

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | User stories and requirements cover DOC-FR-010 and contain no unresolved placeholders |
| G2 | After Clarify | Route list, CI condition, and Playwright scope are decided or explicitly deferred |
| G3 | After Plan | Constitution gates pass; reviewability budget remains within the DOC-010 slice |
| G4 | After Checklist | All real gaps are remediated or explicitly scoped out with rationale |
| G5 | After Tasks | Tasks cover every user story and keep Playwright minimal |
| G6 | After Analyze | No critical drift between design concept, spec, plan, and tasks |
| G7 | After Implementation | Docs-site validation, focused Playwright smoke, git diff check, and relevant repo tests pass |

---

## Prerequisites

### Worktree and Branch

- Worktree: `.worktrees/doc-010-search-accessibility-deep-links-docs-validation`
- Branch: `doc-010-search-accessibility-deep-links-docs-validation`
- Contract marker: `specs/doc-010-search-accessibility-deep-links-docs-validation/SPEC-MOC.md`
- Design concept: `docs/ai/specs/.process/DOC-010-design-concept.md`

Before starting:

```bash
git rev-parse --abbrev-ref HEAD
git status --short
specify preset resolve spec-template
specify preset resolve plan-template
specify preset resolve tasks-template
```

Expected branch is `doc-010-search-accessibility-deep-links-docs-validation`. Preset resolution should use `.specify/presets/speckit-pro-reviewability/` unless a deliberate higher-priority override exists.

### Constitution Validation

| Principle | DOC-010 Requirement | Verification |
|-----------|---------------------|--------------|
| Plugin Structure Compliance | Do not change plugin behavior or shipped plugin payloads unless a validator proves a docs reference depends on source truth | `git diff --name-only` review |
| Script Safety | Any new or edited script must use existing Node ESM or bash conventions and avoid unsafe shell execution | Source review plus script command run |
| Test Coverage Before Merge | Add validation coverage for new docs-site checks and Playwright smoke | Docs-site validation, Playwright smoke, relevant repo tests |
| Conventional Commits | PR title and commits must use public-readable conventional commit text | PR Checks `validate-pr-title` |
| KISS, Simplicity, YAGNI | Extend existing docs-site validation paths; keep Playwright minimal | Plan complexity table and code review |

### Existing Source Truth

- Roadmap: `docs/ai/specs/interactive-documentation-technical-roadmap.md`
- Product requirement: `docs/prd-interactive-documentation.md` DOC-FR-010, AC-10.1 through AC-10.7
- Stack decision: `docs/ai/research/interactive-documentation-framework-spike.md`
- Current docs-site package: `docs-site/package.json`
- Current docs-site config: `docs-site/astro.config.mjs`
- Existing docs validators:
  - `docs-site/scripts/generate-reference-pages.mjs`
  - `docs-site/scripts/validate-doc006-safe-aids.mjs`
- Current PR Checks workflow: `.github/workflows/pr-checks.yml`

### Reviewability Budget

Setup gate output:

```json
{"mode":"setup","status":"pass","reviewable_loc":395,"production_files":0,"total_files":6,"primary_surfaces":["docs/process"],"warnings":[],"blockers":[]}
```

Grill Me slice-size estimator:

```json
{"estimated_loc":277,"suggested_slices":1,"status":"ok"}
```

If Plan discovers that Playwright coverage pushes the slice above budget, prefer trimming the route list before splitting. Split only if the implementation cannot remain a minimal smoke suite.

---

## Specification Context

| Field | Value |
|-------|-------|
| Spec ID | DOC-010 |
| Name | Search, accessibility, deep links, docs validation |
| Branch | `doc-010-search-accessibility-deep-links-docs-validation` |
| Dependencies | DOC-001, DOC-002, DOC-006; DOC-008 and DOC-009 are archived and complete |
| Enables | Feature complete interactive documentation |
| Priority | P2 |
| Primary surface | Docs/process |

### Acceptance Criteria Summary

From `docs/prd-interactive-documentation.md` DOC-FR-010:

- AC-10.1: Site includes search or a documented search plan, glossary, and stable URL/deep-link conventions.
- AC-10.2: Interactive controls meet keyboard, focus, label, contrast, and static-fallback requirements.
- AC-10.3: Docs CI runs site build, markdown/link checks, manifest consistency, payload consistency, and safe command-snippet checks.
- AC-10.4: Validation avoids networked or destructive commands unless explicitly manual.
- AC-10.5: Site has responsive layouts for mobile and desktop install workflows.
- AC-10.6: Docs pages include source-update guidance so official doc changes become maintenance tasks.
- AC-10.7: Visual regression or screenshot checks are required once the static site exists.

### Scope

- Search, glossary, and deep-link conventions across existing docs-site routes.
- Accessibility and responsive checks for `SafeInstallAids.astro`, `LifecycleFlow.astro`, and related docs content.
- Conditional docs-site PR Checks validation for docs-site changes.
- Minimal Playwright smoke coverage for key routes and mobile/desktop viewports.
- Extension of existing docs-site validators for safe snippets, manifest references, generated references, and source-backed consistency.

### Out of Scope

- New top-level docs route.
- New search provider or custom search plugin.
- Full analytics instrumentation.
- Live install tests in CI.
- Broad visual snapshot suite.
- Browser-side command execution, local file inspection, or destructive validation.
- Plugin behavior changes outside docs validation needs.

---

## Phase 1: Specify

**When to run:** At the start of the new feature specification. Focus on what and why. Output: `specs/doc-010-search-accessibility-deep-links-docs-validation/spec.md`.

### Specify Prompt

```bash
/speckit-specify

## Feature: Search, accessibility, deep links, docs validation

### Problem Statement
The interactive documentation site exists, but the final hardening slice must make it findable, accessible, support-linkable, responsive, and protected against documentation drift. DOC-010 should harden existing Astro/Starlight routes rather than adding a new top-level route.

### Users
- First-time Claude Code and Codex users who need to find install and recovery guidance quickly.
- Support/responders who need stable deep links to glossary terms, reference sections, troubleshooting entries, and release workflow details.
- Maintainers and contributors who need docs-site validation to run consistently in local development and PR Checks.
- Reviewers who need browser evidence that interactive docs components remain usable across desktop and mobile.

### User Stories
1. As a user or support responder, I can search, browse the glossary, and share stable deep links to existing docs-site content so I can answer install, troubleshooting, and release questions without stale anchors.
2. As a keyboard or screen-reader user, I can use the docs-site interactive aids and static fallbacks without relying on inaccessible dynamic behavior.
3. As a maintainer, I can run one docs-site validation path locally and see the matching PR Checks job run when docs-site files change.
4. As a reviewer, I can inspect minimal Playwright smoke evidence for key routes on mobile and desktop without reviewing a broad visual snapshot suite.

### Functional Requirements
- Retain the existing Astro/Starlight docs stack and built-in Starlight/Pagefind search path.
- Define stable heading, glossary, and deep-link conventions for existing docs-site pages, especially support-heavy pages and generated reference pages.
- Preserve or improve keyboard, focus, label, contrast, static fallback, and responsive requirements for `SafeInstallAids.astro` and `LifecycleFlow.astro`.
- Extend existing docs-site validators instead of creating a broad new validation framework.
- Add or update package scripts so local docs validation includes generated reference checks, Astro/Starlight checks, build/link validation, safe-aids validation, and minimal Playwright smoke.
- Add a conditional PR Checks docs job for docs-site changes without changing the plugin test matrix semantics.
- Add minimal Playwright smoke coverage for a small route set and mobile/desktop viewports.
- Ensure validation avoids networked, destructive, or local-user-file commands unless explicitly documented as manual.
- Include source-update guidance for external platform claims so docs changes become maintenance tasks instead of stale assertions.

### Constraints
- Keep the change docs-site and docs-process focused.
- Use `pnpm` inside `docs-site/`, matching `docs-site/package.json`.
- Do not run live plugin install tests in CI.
- Do not add analytics.
- Do not replace Starlight search.
- Do not introduce browser-side local command execution or user JSON inspection.
- Keep Playwright minimal; if budget gets tight, reduce route coverage before splitting.

### Out of Scope
- A new route dedicated to docs quality.
- Full visual regression snapshot infrastructure.
- Accessibility automation that claims complete WCAG conformance by itself.
- Plugin runtime behavior changes.
```

### Specify Results

After running Specify, fill in:

| Metric | Value |
|--------|-------|
| Functional Requirements | 13 |
| User Stories | 4 |
| Acceptance Criteria | 11 acceptance scenarios |
| Clarification markers | 0 |

### Files Generated

- `specs/doc-010-search-accessibility-deep-links-docs-validation/spec.md`

---

## Phase 2: Clarify

**When to run:** Run if Specify leaves ambiguity or if the Plan phase needs a concrete choice. Keep to five targeted questions or fewer.

### Clarify Prompt 1: Route List

```bash
/speckit-clarify Focus on the minimal Playwright and deep-link route list.

Use the design concept's Open Questions. Start from these candidate routes:
- `/`
- `/choose-your-path/`
- `/spec-kit-lifecycle/`
- `/glossary/`
- `/reference/skills/`
- `/contribute-and-release/`

Resolve whether this route list is small enough for DOC-010, and trim it if necessary before implementation.
```

### Clarify Prompt 2: CI Condition

```bash
/speckit-clarify Focus on docs-site PR Checks triggering.

Resolve whether the docs validation job should trigger for:
- `docs-site/**`
- `.github/workflows/pr-checks.yml`
- docs interactive roadmap/PRD/process files that directly affect docs-site validation

Do not alter plugin matrix semantics unless the spec explicitly requires it.
```

### Clarify Prompt 3: Playwright Script Shape

```bash
/speckit-clarify Focus on Playwright script naming and evidence output.

Resolve the local script name, CI script name, whether screenshots are attached as artifacts, and how manual/browser accessibility evidence is recorded in the PR packet.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Route list | 5 | Kept all six logical routes; Playwright base URL owns `/racecraft-plugins-public`; deterministic validation owns full links/anchors; Playwright samples search, deep links, and interactive routes |
| 2 | CI condition | 5 plus 1 consensus item | Use job-level detection, not workflow-level `paths`; expose one stable docs validation gate; split rendered docs-site changes from generated-reference source and docs-validation contract changes; workflow edits run affected docs checks without changing plugin matrix semantics |
| 3 | Playwright script shape | 4 | Use `validate:smoke` and include it in `pnpm --dir docs-site validate`; add stable `validate-docs`; upload short-retention `docs-site-smoke-evidence`; record manual accessibility evidence in existing PR packet sections |

### Consensus Resolution Log

| # | Type | Question/Gap/Finding | Categories | Round | Outcome | Resolution | Analysts Used |
|---|------|----------------------|------------|-------|---------|------------|---------------|
| 1 | Clarify | Non-`docs-site/**` CI trigger allowlist | [codebase, spec] | 1→2 | 2/3 | Recorded split job-level detection: full docs-site validation for rendered docs changes, reference drift validation for generated-reference source changes, and docs-validation contract handling through the stable docs gate | codebase-analyst, spec-context-analyst, domain-researcher |
| 2 | Gap | Permission, credential, secret, token, marketplace, plugin-runtime, and plugin-matrix boundaries for `validate-docs` | [security] | 2 | 3/3 | Added least-privilege required and forbidden CI behavior to `contracts/pr-checks-docs-gate-contract.md` | codebase-analyst, spec-context-analyst, domain-researcher |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output: `specs/doc-010-search-accessibility-deep-links-docs-validation/plan.md` and supporting artifacts.

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Docs site: Astro 6.4.6 and Starlight 0.40.0 in `docs-site/`
- Package manager: pnpm 10.25.0, scoped with `pnpm --dir docs-site ...`
- Existing docs validation: `pnpm reference:check`, `pnpm check`, `pnpm build`, `pnpm validate`
- Existing link validation: `starlight-links-validator` configured in `docs-site/astro.config.mjs`
- Existing source-backed validators: `docs-site/scripts/generate-reference-pages.mjs` and `docs-site/scripts/validate-doc006-safe-aids.mjs`
- CI: `.github/workflows/pr-checks.yml`
- Browser smoke: minimal Playwright coverage added as a docs-site dev dependency if no existing local tool satisfies Q5

## Grounded Implementation Map
- `docs-site/package.json`: add or adjust scripts for safe-aids validation, docs quality validation, and minimal Playwright smoke.
- `docs-site/pnpm-lock.yaml`: update only through pnpm if Playwright or a related dev dependency is added.
- `docs-site/astro.config.mjs`: keep Starlight and `starlight-links-validator`; do not replace search.
- `docs-site/src/content/docs/glossary.md`: harden glossary/deep-link conventions if gaps exist.
- `docs-site/src/content/docs/reference/**`: preserve generated reference pages and stable anchors.
- `docs-site/src/content/docs/choose-your-path.mdx`: ensure interactive aid content remains support-linkable and source-backed.
- `docs-site/src/components/SafeInstallAids.astro`: preserve keyboard, focus, static fallback, copyable guidance only, and responsive behavior.
- `docs-site/src/components/LifecycleFlow.astro`: preserve static fallback and responsive behavior.
- `docs-site/scripts/validate-doc006-safe-aids.mjs`: extend or pair with a focused docs quality validator rather than building a large new suite.
- `docs-site/scripts/generate-reference-pages.mjs`: keep generated reference checks deterministic.
- `.github/workflows/pr-checks.yml`: add conditional docs-site validation without changing plugin detection semantics.
- `docs/ai/specs/.process/DOC-010-design-concept.md`: source of truth for scope decisions.

## Constraints
- Keep Playwright minimal: key routes, mobile and desktop viewports, smoke-level assertions, and artifact evidence only where valuable.
- Avoid networked or destructive validation in CI.
- Do not run live plugin install commands in CI.
- Do not add analytics.
- Do not create a new route unless a later Clarify answer explicitly revises Q1.
- Prefer extending existing validators and scripts over introducing new frameworks.

## Architecture Notes
- Treat Starlight search as the search implementation and make the docs content more findable through stable headings, glossary terms, and support-ready links.
- Treat automated accessibility checks as guardrails, not a full accessibility certification.
- Record manual/browser accessibility and responsive review evidence in the PR packet alongside Playwright results.
- Keep docs-only CI separate from plugin matrix semantics: docs-site changes should validate docs-site behavior, while plugin behavior changes still run the plugin test suite.
- If Playwright requires a local preview server, use Playwright's `webServer` or an equivalent deterministic `pnpm --dir docs-site build` plus preview path. Avoid long-running servers in CI steps that do not shut down.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Complete | Technical context, reviewability, file operations, and implementation plan |
| `research.md` | Complete | Package/script/CI decisions and tradeoffs |
| `data-model.md` | Complete | Docs validation and browser evidence entities |
| `contracts/` | Complete | Browser smoke, docs validation, and PR Checks docs gate contracts |
| `quickstart.md` | Complete | Local validation and reviewer evidence commands |

Plan-phase reviewability estimate:

```json
{"tool":"estimate-reviewable-loc","status":"pass","projected":160,"declared_files":{"production":4,"new":3,"modified":7,"total_entries":10},"greenfield":false}
```

---

## Phase 4: Domain Checklists

Run checklists after Plan so both `spec.md` and `plan.md` are available.

### Recommended Domains

#### 1. Accessibility

Why this domain: DOC-010 directly owns keyboard, focus, label, contrast, static fallback, and screen-reader expectations for interactive docs components.

```bash
/speckit-checklist accessibility

Focus on DOC-010 requirements:
- Keyboard operation, focus visibility, native controls, and status announcements in `SafeInstallAids.astro`
- Static fallback and non-JavaScript readability for `SafeInstallAids.astro` and `LifecycleFlow.astro`
- Mobile/desktop reflow and contrast expectations in docs-site routes
- Manual/browser review evidence that automation cannot prove
- Pay special attention to: avoiding claims that automation alone proves full accessibility compliance
```

#### 2. UX

Why this domain: DOC-010 changes findability, deep-link conventions, route smoke coverage, and responsive install workflows.

```bash
/speckit-checklist ux

Focus on DOC-010 requirements:
- Search, glossary, and stable deep-link conventions across existing routes
- Support-ready anchors for install, troubleshooting, reference, glossary, and release workflow answers
- Mobile and desktop behavior for install workflow routes
- Playwright route list and smoke assertions
- Pay special attention to: keeping the route list small while still representing critical user journeys
```

#### 3. Reliability

Why this domain: DOC-010 adds CI and validation guardrails that should catch docs drift without blocking unrelated plugin-only changes.

```bash
/speckit-checklist reliability

Focus on DOC-010 requirements:
- Conditional docs-site PR Checks behavior
- Deterministic local validation commands
- Generated reference consistency and link validation
- Artifact/evidence expectations for Playwright smoke and manual review
- Pay special attention to: docs-only PRs should not accidentally bypass docs validation or trigger unrelated plugin matrix behavior
```

#### 4. Security

Why this domain: DOC-010 validates command snippets and manifest references, and must avoid unsafe browser or CI execution patterns.

```bash
/speckit-checklist security

Focus on DOC-010 requirements:
- No browser-side local command execution, user JSON inspection, local file reads, or hidden permission grants
- No live install tests or destructive commands in CI
- Safe command-snippet validation remains source-backed and copyable-guidance-only
- Manifest and payload consistency checks do not leak local paths or secrets
- Pay special attention to: Playwright and docs validators must not introduce networked or destructive behavior
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| Accessibility | 21 | 3 remediation entries appended; original prompts retained for audit | FR-005, FR-006, SC-003, SC-004 |
| UX | 18 | 2 remediation entries appended; original prompts retained for audit | FR-002, FR-003, FR-004, FR-010, SC-001, SC-002, SC-006 |
| Reliability | 23 | 2 remediation entries appended; original prompts retained for audit | FR-007, FR-008, FR-009, FR-013, SC-005, SC-006 |
| Security | 22 | 11 remediation entries appended; original prompts retained for audit | FR-011, FR-013, SC-005, SC-006 |
| Total | 84 | 18 remediation entries appended; original prompts retained for audit | All DOC-010 requirements |

---

## Phase 5: Tasks

**When to run:** After checklists complete and gaps are resolved. Output: `specs/doc-010-search-accessibility-deep-links-docs-validation/tasks.md`.

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Organize by user story, not by technical layer.
- Keep each task small, testable, and tied to FR and US markers.
- Mark parallel-safe documentation/content tasks with [P] only when they do not touch the same file.
- Include failing or missing validation first, then implementation, then verification.
- Reference `docs/ai/specs/.process/DOC-010-design-concept.md` for scope decisions.

## Suggested Implementation Phases
1. Foundation: decide docs-site validation command shape, route list, and Playwright script naming.
2. US1: search, glossary, headings, and stable deep links on existing docs-site routes.
3. US2: accessibility, static fallback, and responsive hardening for interactive components.
4. US3: local docs validators and conditional PR Checks docs job.
5. US4: minimal Playwright smoke coverage and PR evidence expectations.
6. Polish: generated reference checks, docs update guidance, and final validation bundle.

## Required Verification Tasks
- `pnpm --dir docs-site reference:check`
- `pnpm --dir docs-site validate`
- focused safe-aids/docs-quality validator command created or updated by DOC-010
- minimal Playwright smoke command created by DOC-010
- `git diff --check`
- relevant SpecKit Pro structural or workflow checks if `.github/workflows/pr-checks.yml`, scripts, or spec markers change

## Non-goals to Preserve
- No new top-level docs route.
- No new search provider.
- No full visual snapshot suite.
- No live install tests in CI.
- No browser-side local command execution or user JSON inspection.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| Total Tasks | 40 |
| Phases | Setup 6; US1 7; US2 6; US3 8; US4 6; polish/cross-cutting verification 7 |
| Parallel Opportunities | 6 `[P]` tasks |
| User Stories Covered | US1, US2, US3, US4 |

G5 output:

```json
{"gate":"G5","pass":true,"reason":"40 tasks found","markers":0,"task_count":40}
```

Task reviewability gate:

| Field | Value |
|-------|-------|
| Status | `block` |
| Mode | `tasks` |
| Exit code | `1` |
| Evidence path | `specs/doc-010-search-accessibility-deep-links-docs-validation/.process/reviewability/tasks-gate.json` |
| Proceed decision | Size-only task-mode block; continue into marker planning |
| Blockers | reviewable LOC 1600 exceeds block threshold 800; total files 58 exceeds block threshold 25 |

---

## Atomicity Route

After Tasks/G5, run the classifier:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/doc-010-search-accessibility-deep-links-docs-validation
```

Record the emitted decision here:

| Field | Value | Meaning |
|-------|-------|---------|
| Route | `one-navigable-PR` | Default/modify-heavy route; do not run PRSG-008 split-PR layer planner |
| Releasable | `true` | `true` or `false` |
| Signals | `change-shape:modify-heavy` | Decisive detector findings |
| Warnings | none | Release-safety warning, if any |

Expected bias from setup: one small docs-site hardening PR unless Tasks reveal independent slices.

## Layer Plan

| Field | Value |
|-------|-------|
| Status | `skipped` |
| Reason | Atomicity route is `one-navigable-PR`, so PRSG-008 split-PR layer planning is not required |
| Planner command | Not run |

## PR Marker Plan Evidence

Authoritative marker state is stored in `docs/ai/specs/.process/autopilot-state.json` as top-level `pr_marker_plan`.

| Field | Value |
|-------|-------|
| Schema version | `pr-marker-plan.v1` |
| Status | `planned` |
| Evidence path | `specs/doc-010-search-accessibility-deep-links-docs-validation/.process/reviewability/pr-marker-plan.json` |
| Fingerprint status | current |
| Ordered marker IDs | `foundation`, `us1`, `us2`, `us3`, `us4` |
| Review order | foundation -> us1 -> us2 -> us3 -> us4 |
| Marker checkpoints | pending |
| Final marker split | pending |
| Packet validation | pending |
| PR mappings | pending |
| Warnings | `reviewability_size_warning` from task reviewability gate |

Source fingerprint:

```json
{
  "feature_spec_sha": "6ac0a5a8c6d745b0402c7bfd106cd073967f113ba65a0a29521abb1500599e06",
  "plan_declared_scope_sha": "4b629f67917e00c4135561a9310598beb853352464b839914b809f5e7a65d5a4",
  "tasks_sha": "b7d6780d04697cc03a5e974673bdf97bd884d52e48412fc1d1421ce74669d552",
  "reviewability_sha": "195268e9fcec1e6a2828d31e9153a81f2a6ccc7f0a455c4cc8f0faf28ee35a79",
  "hazard_route_sha": "5ec383c17e5e7102cc97e81882f023da85a301abb73f39023ddea31b24e349f0"
}
```

| Marker | Review order | Tasks | Folded polish tasks | Checkpoint |
|--------|--------------|-------|---------------------|------------|
| `foundation` | 1 | T001-T006 | none | pending |
| `us1` | 2 | T007-T013 | none | pending |
| `us2` | 3 | T014-T019 | none | pending |
| `us3` | 4 | T020-T027 | none | pending |
| `us4` | 5 | T028-T033 | T034-T040 | pending |

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks.

### Analyze Prompt

```bash
/speckit-analyze

Focus on:
1. Cross-artifact consistency between `docs/ai/specs/.process/DOC-010-design-concept.md`, `spec.md`, `plan.md`, and `tasks.md`.
2. Drift from the Grill Me decisions:
   - existing routes only
   - Starlight search
   - automated plus manual accessibility/responsive evidence
   - conditional docs-site PR Checks
   - minimal Playwright smoke
   - extend existing validators
3. Coverage of DOC-FR-010 AC-10.1 through AC-10.7.
4. Reviewability budget risk from Playwright dependency, lockfile changes, workflow changes, and validator changes.
5. CI semantics: docs validation should not break plugin matrix behavior or bypass docs-site checks.
6. Safety: no networked, destructive, browser-side local command execution, user JSON inspection, or live install tests.
7. Task path accuracy against the current repository structure.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| ANALYZE-000 | None | No cross-artifact drift found across design concept, spec, plan, contracts, tasks, and DOC-FR-010 AC-10.1 through AC-10.7 coverage | No remediation required |

G6 output:

```json
{"gate":"G6","pass":true,"reason":"0 CRITICAL/HIGH findings","markers":0,"details":[]}
```

Marker count:

```json
{"type":"findings","total":0,"critical":0,"high":0,"medium":0,"low":0}
```

Analyze notes:

- Native prerequisite check rejected the DOC-prefixed branch naming unless `SPECIFY_FEATURE=010-search-accessibility-deep-links-docs-validation` is supplied; the feature directory and branch were already pinned by the workflow and autopilot state.
- No unresolved consensus categories remain for DOC-010 artifact drift.

📊 Confidence: 0.96

- Task understanding: 0.96
- Approach clarity: 0.94
- Requirements alignment: 0.96
- Risk assessment: 1.00
- Completeness: 0.96

G6.5 confidence gate output:

```json
{"pass":true,"composite":0.96,"criteria":{"task_understanding":0.96,"approach_clarity":0.94,"requirements_alignment":0.96,"risk_assessment":1.00,"completeness":0.96},"threshold":0.90,"mode":"advisory","recommended_action":"proceed","reason":"composite at or above threshold","input":"docs/ai/specs/.process/DOC-010-workflow.md"}
```

---

## Phase 7: Implement

**When to run:** After tasks are generated, analyzed, and approved.

### Implement Prompt

```bash
/speckit-implement

## Approach
Follow the tasks in order. Use the design concept Q&A log for the reason behind scope decisions. Keep edits narrow and docs-site focused.

## Pre-Implementation Setup
1. Verify branch: `git rev-parse --abbrev-ref HEAD`
2. Verify clean or intentionally scoped worktree: `git status --short`
3. Verify docs-site package manager: `docs-site/package.json` declares `pnpm@10.25.0`
4. Run baseline docs checks when feasible:
   - `pnpm --dir docs-site reference:check`
   - `pnpm --dir docs-site validate`

## Implementation Notes
- Prefer source-backed content changes over general prose.
- Keep stable anchors and headings meaningful for support links.
- Keep Starlight/Pagefind search as the search path.
- Keep Playwright smoke minimal and deterministic.
- If adding `@playwright/test`, update `docs-site/pnpm-lock.yaml` through pnpm and document the command.
- If adding screenshots/artifacts in CI, keep retention and upload conditions explicit.
- Extend existing docs-site validators where practical.
- Do not add live install tests, analytics, browser-side local command execution, or local user file inspection.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| Foundation | T001-T006 | Yes | Added docs-site validation scripts, Playwright dependency/config, initial six-route desktop/mobile smoke scaffold, and focused docs-quality validator. Parent verification passed for syntax, `validate:quality`, `validate:safe-aids`, Playwright test discovery, and `git diff --check`; full browser smoke awaits installed Playwright browser binaries. |
| Search/deep links | | | |
| Accessibility/responsive | | | |
| Docs validation/CI | | | |
| Playwright smoke | | | |
| Polish | | | |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in `tasks.md`
- [ ] `pnpm --dir docs-site reference:check`
- [ ] `pnpm --dir docs-site validate`
- [ ] DOC-010 focused validator command, if added
- [ ] Minimal Playwright smoke command, if added
- [ ] `git diff --check`
- [ ] Relevant SpecKit Pro structural/workflow checks if workflow or scripts changed
- [ ] Manual/browser accessibility and responsive review evidence recorded
- [ ] PR packet includes docs-site validation, Playwright/manual evidence, and source-backed summary
- [ ] Roadmap and traceability records updated only after implementation is complete

---

## Project Structure Reference

```text
racecraft-plugins-public/
├── .github/workflows/pr-checks.yml
├── docs-site/
│   ├── astro.config.mjs
│   ├── package.json
│   ├── pnpm-lock.yaml
│   ├── scripts/
│   │   ├── generate-reference-pages.mjs
│   │   └── validate-doc006-safe-aids.mjs
│   └── src/
│       ├── components/
│       │   ├── LifecycleFlow.astro
│       │   └── SafeInstallAids.astro
│       └── content/docs/
├── docs/
│   ├── ai/specs/interactive-documentation-technical-roadmap.md
│   ├── ai/specs/.process/DOC-010-design-concept.md
│   ├── ai/specs/.process/DOC-010-workflow.md
│   └── prd-interactive-documentation.md
└── specs/doc-010-search-accessibility-deep-links-docs-validation/
    └── SPEC-MOC.md
```

---

## Lessons Learned

Fill this after implementation:

- What worked:
- What changed:
- What to reuse:

---

Template based on SpecKit best practices. Populated for DOC-010 from the interactive documentation roadmap and the DOC-010 design concept doc.
