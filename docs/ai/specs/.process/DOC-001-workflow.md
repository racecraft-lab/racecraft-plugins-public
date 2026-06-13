# SpecKit Workflow: DOC-001 - Static docs framework and IA spike

**Template Version**: 1.0.0
**Created**: 2026-06-12
**Purpose**: Prepare and execute the research-only spike that selects the static docs-site stack and IA foundation for Racecraft interactive documentation.

---

## Design Concept

This workflow was enriched from a Grill Me interview run during `$speckit-scaffold-spec`.
The full Q&A log, Goals, Non-goals, and Open Questions live at:

```text
docs/ai/specs/.process/DOC-001-design-concept.md
```

The design concept is the source of truth for these setup decisions:

- Produce one default stack recommendation for DOC-002.
- Prioritize rich MDX or equivalent interactivity, while requiring GitHub Pages hosting from this repository.
- Let the chosen framework determine the package manager recommendation.
- Draft routes plus purpose, audience, source evidence, and success criteria; do not write full page copy.
- Refresh live framework/platform docs during the spike.
- Write only the research decision record beyond normal SpecKit artifacts.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | Complete | Created spec with 3 user stories, 11 functional requirements, 6 success criteria, and 0 `[NEEDS CLARIFICATION]` markers |
| Clarify | `/speckit-clarify` | Complete | Completed 3 sessions; G2 passed with 0 clarification markers and no consensus items |
| Plan | `/speckit-plan` | Complete | Created plan, research, data model, quickstart, and early research decision record; G3 passed; reviewability estimate passed with 0 projected production LOC |
| Checklist | `/speckit-checklist` | Complete | Completed documentation-quality, accessibility, and error-handling; G4 passed with 0 `[Gap]` markers |
| Tasks | `/speckit-tasks` | Complete | Created 28 research-only tasks across 5 phases; G5 passed; atomicity route is one navigable PR |
| Analyze | `/speckit-analyze` | Complete | 0 findings; DOC-FR-001 task coverage, live-source refresh tasks, route-level Diataxis IA, and no-implementation boundary verified; G6 passed |
| Implement | `/speckit-implement` | Complete | Research report complete; T001-T028 complete; G7 passed |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | Spec captures stack recommendation, IA skeleton, package/build/test command identification, and no product/plugin behavior changes |
| G2 | After Clarify | Decision rubric, blocker/tradeoff definitions, evidence sources, hosting constraints, IA skeleton contract, and output boundaries are explicit |
| G3 | After Plan | Research matrix and IA skeleton approach are approved; reviewability remains spike-sized |
| G4 | After Checklist | Documentation-quality, accessibility, and error-handling gaps are addressed or marked out of scope |
| G5 | After Tasks | Tasks map to all DOC-FR-001 acceptance criteria and avoid site implementation work |
| G6 | After Analyze | No critical drift from PRD, roadmap, or design concept |
| G7 | After Implementation | Research decision record exists, cites live sources, recommends one default stack, and final diff is limited to the research report plus SpecKit artifacts with no site/package/config/CI/README/plugin behavior mutation |

---

## Prerequisites

### Constitution Validation

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Plugin Structure Compliance | Do not add plugin components or generated payload files in this spike | Verified baseline: current DOC-001 diff is process/spec docs only before implementation |
| Script Safety | Do not add scripts in DOC-001 unless the plan explicitly justifies them; expected output is research markdown only | Verified baseline: no DOC-001 scripts added before implementation |
| Test Coverage Before Merge | Research-only docs branch should at minimum pass structural checks when relevant | Verified baseline: `bash tests/speckit-pro/run-all.sh --layer 1` passed `978/978` |
| KISS, Simplicity & YAGNI | Keep stack decision evidence in one research document; no prototype/package files unless the spec is formally amended | Verified baseline: expected deliverable remains one research markdown decision record |

**Constitution Check:** Verified

---

## Specification Context

| Field | Value |
|-------|-------|
| **Spec ID** | DOC-001 |
| **Name** | Static docs framework and IA spike |
| **Branch** | `doc-001-static-docs-framework-and-ia-spike` |
| **Feature directory** | `specs/doc-001-static-docs-framework-and-ia-spike` |
| **Design Concept** | `docs/ai/specs/.process/DOC-001-design-concept.md` |
| **Dependencies** | None |
| **Enables** | DOC-002 |
| **Priority** | P1 |
| **Reviewability estimate** | Spike; LOC not applicable; setup gate returned pass with 395 projected reviewable LOC for the roadmap entry |

### Success Criteria Summary

- The spike records the recommended site stack, rejected alternatives, and exact reason each was accepted or rejected.
- The spike includes a proposed IA skeleton organized by user tasks and Diataxis mode.
- The spike identifies minimum package manager, build, and test commands for the chosen stack.
- The spike does not modify product/plugin behavior.
- The selected stack must support rich MDX or equivalent interactivity and GitHub Pages hosting from this repository.
- The output surface is limited to `docs/ai/research/interactive-documentation-framework-spike.md` plus SpecKit artifacts.

---

## Phase 1: Specify

**When to run:** At the start of DOC-001. Output: `specs/doc-001-static-docs-framework-and-ia-spike/spec.md`.

### Specify Prompt

```bash
/speckit-specify

## Feature: Static docs framework and IA spike

### Problem Statement
Racecraft needs a static documentation site, but the repository currently has no docs-site package, config, lockfile, or hosting decision. DOC-001 selects the site stack and IA foundation before DOC-002 creates the shell.

### Users
- Maintainers deciding whether the docs-site dependency surface is acceptable.
- Future DOC-002 implementers who need a clear stack and IA handoff.
- Documentation contributors who need to understand the selected build/test commands.

### User Stories
1. As a maintainer, I can review one source-backed recommendation for the docs framework and understand why the alternatives were rejected.
2. As the DOC-002 implementer, I have a concrete IA skeleton and minimum package/build/test commands for the selected stack.
3. As a reviewer, I can confirm the spike did not introduce site scaffolding, package files, or plugin behavior changes.

### Functional Requirements
- Compare Docusaurus/MDX, VitePress, Astro/Starlight, and a repo-native fallback.
- Evaluate static hosting, GitHub Pages support, MDX or equivalent interactivity, search, versioning, accessibility, link checking, docs-as-code workflow, maintenance load, and package/build/test commands.
- Refresh live framework/platform source docs during the spike.
- Recommend one default stack for DOC-002 unless a hard blocker is recorded.
- Draft a Diataxis IA skeleton with route, mode, audience, source evidence, and success criterion for each top-level route.
- Write the result to `docs/ai/research/interactive-documentation-framework-spike.md`.

### Constraints
- Research-only spike: no `package.json`, lockfile, site config, prototype components, CI changes, marketplace changes, plugin behavior changes, or README migration.
- The selected stack must be hostable from this repository through GitHub Pages.
- Let the chosen framework determine the recommended package manager.

### Out of Scope
- Implementing the docs site.
- Migrating README content.
- Creating interactive widgets.
- Adding docs CI.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 11 |
| User Stories | 3 |
| Acceptance Criteria | 6 success criteria; 6 acceptance scenarios |

### Files Generated

- [x] `specs/doc-001-static-docs-framework-and-ia-spike/spec.md`
- [x] `specs/doc-001-static-docs-framework-and-ia-spike/checklists/requirements.md`

---

## Phase 2: Clarify

**When to run:** After Specify if any decision criteria or scope boundary is ambiguous.

### Clarify Prompts

#### Session 1: Framework decision rubric

```bash
/speckit-clarify Focus on framework decision rubric: weight rich MDX/equivalent interactivity, GitHub Pages hosting from this repo, search, versioning, accessibility, link checking, package manager, and maintenance burden. Confirm what counts as a hard blocker vs a tradeoff.
```

#### Session 2: IA skeleton contract

```bash
/speckit-clarify Focus on IA skeleton contract: define the required fields for each route, including route label, Diataxis mode, target audience, source evidence, success criterion, and which later DOC specs own full content.
```

#### Session 3: Research output and no-implementation boundary

```bash
/speckit-clarify Focus on output boundary: confirm that DOC-001 writes only `docs/ai/research/interactive-documentation-framework-spike.md` plus SpecKit artifacts, and explicitly excludes package files, site config, prototype components, CI, README migration, and plugin behavior changes.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Framework decision rubric | 5 | Accepted blocker gates for GitHub Pages-from-this-repo, rich MDX/equivalent reusable-component interactivity, accessible fallback, and no-implementation boundary; search/link checking are high-weight tradeoffs, versioning is medium-weight, package manager follows selected framework, and repo-native fallback is selected only if framework options are blocked or too risky |
| 2 | IA skeleton contract | 5 | Accepted IA route schema with `route_path`, `route_label`, `diataxis_mode`, optional `secondary_modes`, `target_audience`, `route_purpose`, `source_evidence`, `success_criterion`, `shell_owner_doc`, and `full_content_owner_doc`; cover all 11 PRD IA routes; use one primary Diataxis mode plus optional secondary modes; cite local/official route evidence; DOC-002 owns shell and later DOC specs own full content |
| 3 | Output boundary | 5 | Accepted positive allow-list: `docs/ai/research/interactive-documentation-framework-spike.md` plus SpecKit artifacts under `specs/doc-001-static-docs-framework-and-ia-spike/**` and `docs/ai/specs/.process/DOC-001-*`; PRD, roadmap, design concept, README, plugin docs, package files, lockfiles, site config, prototype components, CI, marketplace/generated payloads, and plugin behavior are excluded unless separately amended |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output: `specs/doc-001-static-docs-framework-and-ia-spike/plan.md`.

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Current repo: Bash and Markdown heavy; no docs-site package/config/lockfile at depth 3.
- Candidate frameworks to research: Docusaurus/MDX, VitePress, Astro/Starlight, repo-native fallback.
- Required hosting path: GitHub Pages from this repository.
- Expected deliverable: one research Markdown decision record. Package manager, build, and test commands are report-only recommendations.

## Constraints
- Research-only spike. Do not create site scaffold, package files, lockfiles, CI workflows, marketplace files, generated payloads, or plugin behavior changes.
- Use live source refresh for framework and platform docs.
- The chosen stack should determine the recommended package manager and minimum build/test commands.

## Architecture Notes
- Treat `docs/prd-interactive-documentation.md`, `docs/roadmap-interactive-documentation.md`, `docs/ai/specs/interactive-documentation-technical-roadmap.md`, and `docs/ai/specs/.process/DOC-001-design-concept.md` as source inputs.
- The research matrix should include acceptance/rejection reasons for every candidate.
- The IA skeleton should be route-level, not full content copy. Each route record must include route path, route label, primary Diataxis mode, optional secondary modes, audience, purpose, source evidence, success criterion, shell owner DOC, and full content owner DOC.
- The plan should state how DOC-002 consumes the recommendation.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Complete | Research matrix approach, IA skeleton contract, and DOC-002 handoff |
| `research.md` | Complete | Candidate framework evidence and final recommendation captured as SpecKit research |
| `data-model.md` | Complete | Framework Candidate, Evaluation Criterion, IA Route, Source Evidence, Command Recommendation, and Spike Report entities |
| `quickstart.md` | Complete | Reviewer validation checklist for report, IA skeleton, scope boundary, and DOC-002 handoff |
| `contracts/` | N/A | No API, CLI, service, schema, or runtime interface exposed by DOC-001 |

---

## Phase 4: Domain Checklists

### Recommended Domains

#### 1. documentation-quality Checklist

Why this domain: DOC-001 is a documentation-product spike whose output must be clear, source-backed, and useful to DOC-002.

```bash
/speckit-checklist documentation-quality

Focus on DOC-001 requirements:
- Framework comparison criteria are complete and measurable.
- Each candidate has accepted/rejected rationale.
- The final recommendation is explicit enough for DOC-002.
- IA skeleton fields are clear without drifting into page copy.
- Pay special attention to: stale or unsourced framework/platform claims.
```

#### 2. accessibility Checklist

Why this domain: The selected stack must support future accessible interactive docs and static fallbacks.

```bash
/speckit-checklist accessibility

Focus on DOC-001 requirements:
- Framework comparison includes accessibility testing and keyboard/static fallback support.
- IA skeleton includes routes for accessibility and responsive UX hardening owned by DOC-010.
- The spike does not promise inaccessible interactive behavior.
- Pay special attention to: whether rich interactivity is balanced against accessibility obligations.
```

#### 3. error-handling Checklist

Why this domain: The spike decision must explain fallback behavior when a candidate cannot satisfy GitHub Pages, MDX/interactivity, search, or maintenance constraints.

```bash
/speckit-checklist error-handling

Focus on DOC-001 requirements:
- Hard blockers vs tradeoffs are defined for each framework candidate.
- The repo-native fallback is evaluated seriously, not treated as a missing-data path.
- The recommendation includes a fallback if the chosen stack's GitHub Pages path fails in DOC-002.
- Pay special attention to: ambiguous package/build/test command requirements.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| documentation-quality | 20 | 3 found, 3 remediated, 0 remaining | `checklists/documentation-quality.md`; support-class legend, bounded evidence notes, and Docusaurus version-source wording |
| accessibility | 20 | 3 found, 3 remediated, 0 remaining | `checklists/accessibility.md`; accessibility testing handoff, interaction guardrails, and DOC-010 route hardening coverage |
| error-handling | 20 | 3 found, 3 remediated, 0 remaining | `checklists/error-handling.md`; Astro/Starlight GitHub Pages failure handling, Docusaurus/MDX fallback order, repo-native fallback seriousness, and command-role clarity |

---

## Phase 5: Tasks

**When to run:** After checklist gaps are resolved. Output: `specs/doc-001-static-docs-framework-and-ia-spike/tasks.md`.

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Organize by user story and research deliverable, not by framework layer.
- Include explicit source-refresh tasks for Docusaurus/MDX, VitePress, Astro/Starlight, GitHub Pages hosting, search, accessibility, and package/build/test commands.
- Include one task to write the route-level Diataxis IA skeleton.
- Include one task to verify no site scaffold/package/config/plugin behavior files were modified.
- Mark parallel-safe research tasks with [P] when they touch only the research document.

## Implementation Phases
1. Foundation: create the research artifact structure and source list.
2. Candidate comparison: gather live evidence and score each stack.
3. IA skeleton: draft route-level Diataxis map.
4. Recommendation: choose one default stack and record rejected alternatives.
5. Verification: confirm no implementation creep and run relevant docs/structural checks.

## Constraints
- Output research record: `docs/ai/research/interactive-documentation-framework-spike.md`.
- Do not create `package.json`, lockfiles, site config, prototype components, CI workflows, marketplace files, generated payloads, or plugin behavior changes.
- Do not edit PRD, roadmap, design concept, README, plugin README, or migration content during implementation; treat them as source inputs unless scope is explicitly amended.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| Total Tasks | 28 |
| Phases | 5 |
| Parallel Opportunities | 8 |
| User Stories Covered | 3 user stories; 11 functional requirements |
| G5 Validation | Passed; 28 tasks detected |
| Reviewability Task Gate | Size-only block captured at `specs/doc-001-static-docs-framework-and-ia-spike/.process/reviewability/tasks-gate.json`; continue through final reviewability backstop |

---

## Atomicity Route

Fill after the Tasks phase by running:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/doc-001-static-docs-framework-and-ia-spike
```

Expected initial route: `one-navigable-PR`, because this is a research-only spike with one deliverable.

| Field | Value | Meaning |
|-------|-------|---------|
| Route | `one-navigable-PR` | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope` |
| Releasable | `true` | `true` unless classifier finds release-sensitive behavior |
| Signals | `change-shape:modify-heavy` | Decisive detector findings |
| Warnings | None | Release-safety warnings |

## Layer Plan

| Field | Value |
|-------|-------|
| Status | Skipped |
| Reason | Atomicity route is `one-navigable-PR`; PRSG-008 layer planning only applies to `split-PR` routes |

---

## Phase 6: Analyze

### Analyze Prompt

```bash
/speckit-analyze

Focus on:
1. Cross-artifact consistency between `spec.md`, `plan.md`, `tasks.md`, the PRD, both interactive documentation roadmaps, and `docs/ai/specs/.process/DOC-001-design-concept.md`.
2. Whether every DOC-FR-001 acceptance criterion has task coverage.
3. Whether any task drifts into DOC-002 implementation, package files, site config, CI, README migration, marketplace files, generated payloads, or plugin behavior.
4. Whether live source refresh is represented in tasks, not just assumed.
5. Whether the IA skeleton is route-level and Diataxis-based rather than full content copy.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| N/A | N/A | No findings. `spec.md`, `plan.md`, `tasks.md`, PRD, roadmaps, and DOC-001 design concept are consistent for Phase 6. | G6 passed with marker counts C:0/H:0/M:0/L:0. |

### Confidence Gate

| Field | Value |
|-------|-------|
| Mode | Advisory |
| Threshold | 0.90 |
| Result | Soft-skip |
| Reason | `confidence-gate.sh` returned `NO_DATA` because no synthesizer confidence emit was present; no unresolved findings require consensus |

---

## Phase 7: Implement

### Implement Prompt

```bash
/speckit-implement

## Approach: Research spike

1. Refresh live source evidence for the framework/platform candidates.
2. Write the research decision record at `docs/ai/research/interactive-documentation-framework-spike.md`.
3. Record accepted/rejected rationale for Docusaurus/MDX, VitePress, Astro/Starlight, and repo-native fallback.
4. Recommend one default stack for DOC-002, with package manager, build command, test command, hosting path, and fallback notes.
5. Draft the route-level Diataxis IA skeleton.
6. Verify the diff contains no site scaffold, package files, lockfiles, CI workflows, marketplace files, generated payloads, or plugin behavior changes.

## Verification
- `git diff --name-only` shows only research/spec artifacts expected for DOC-001.
- `rg -n "Docusaurus|VitePress|Starlight|GitHub Pages|MDX" docs/ai/research/interactive-documentation-framework-spike.md` confirms candidate evidence is present.
- `git diff --name-only origin/main...HEAD` contains no package files, lockfiles, site config, prototype components, CI files, README/plugin README migration, marketplace files, generated payloads, or plugin behavior files introduced by DOC-001.
- Run `bash tests/speckit-pro/run-all.sh --layer 1` if structural docs/spec artifacts changed.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| Research artifact setup | T001-T004 | 4/4 | Report shell, source evidence convention, local inputs, and scope boundary recorded |
| Candidate comparison | T005-T014 | 10/10 | Official sources refreshed; candidate matrix, support classes, scoring, and tradeoffs recorded |
| IA skeleton | T015-T018 | 4/4 | 11 route records, command handoff, DOC-002 consumption, and fallback rules recorded |
| Recommendation | T019-T022 | 4/4 | Astro/Starlight selected; alternatives rejected/deferred with Docusaurus/MDX retained as fallback; FR/SC traceability added |
| Verification | T023-T028 | 6/6 | Diff-scope scan, IA coverage, Layer 1, default suite, and PR review packet notes recorded |

---

## Post-Implementation Checklist

- [x] `docs/ai/research/interactive-documentation-framework-spike.md` exists.
- [x] The research record recommends one default stack for DOC-002.
- [x] Rejected alternatives have concrete reasons.
- [x] GitHub Pages hosting from this repo is addressed.
- [x] Minimum package manager, build, and test commands are identified.
- [x] IA skeleton is route-level and Diataxis-organized.
- [x] No product/plugin behavior files changed.
- [x] No site scaffold, package files, lockfiles, or CI workflows were added.
- [x] Relevant validation commands are recorded.

---

## Self-Review

| Question | Finding |
|----------|---------|
| Does the implementation satisfy the spec? | Yes. The research report recommends Astro/Starlight, compares all required candidates, includes the DOC-002 command handoff, and records the route-level IA skeleton. |
| Did DOC-001 stay inside its research-only boundary? | Yes. Forbidden-surface scans found 0 package, lockfile, site config, CI, generated payload, README migration, or plugin behavior changes. |
| Is verification sufficient for this docs/process spike? | Yes. Layer 1 passed, the default deterministic suite passed, G7 passed, post-merge verification passed `2915/2915`, and final reviewability proceeded with marker evidence. |
| What remains risky or deferred? | DOC-002 must refresh Astro/Starlight, selected Starlight plugin, and GitHub Pages docs before scaffolding; DOC-010 owns search, accessibility, responsive, deep-link, and docs validation hardening after the site exists. |

## Post-Implementation Evidence

| Item | Result |
|------|--------|
| Doctor extension check | `specify extension list` passed; verify, verify-tasks, checkpoint, retrospective, speckit-utils, git, and archive extensions are enabled |
| Verify implementation | G7 passed with all 28 tasks complete |
| Verify tasks phantom check | 28/28 tasks checked; no unchecked task markers remain |
| Code review extension | Skipped; review extension is not installed |
| Integration suite | `bash tests/speckit-pro/run-all.sh` passed `2587/2587` |
| Cleanup extension | Skipped; cleanup extension is not installed and archive sweep was dry-run/no-op |
| Final reviewability backstop | Proceeded with `outcome=marker_split`; current final diff is a size-only 32-file block and marker plan is valid for `foundation`, `us1`, `us2`, `us3` |
| Marker emission packet | Dry-run validation passed with 4 marker slices and no branch or PR mutations |
| UAT runbook | Generated at `specs/doc-001-static-docs-framework-and-ia-spike/.process/uat-runbook.md`; author-agent rewrite unavailable, fail-open with parent self-review notes |
| PR body | Generated at `specs/doc-001-static-docs-framework-and-ia-spike/.process/pr-body.md` with review-packet marker and UAT section |
| PR update | Existing PR updated: https://github.com/racecraft-lab/racecraft-plugins-public/pull/163 |
| Review remediation | Initial remote check found PR mergeable with CI still pending; no review decision recorded |
| Retrospective | Skipped in Codex surface; retrospective extension is installed but only exposes a Claude slash-command file here |

---

## Project Structure Reference

```text
docs/
  prd-interactive-documentation.md
  roadmap-interactive-documentation.md
  traceability-interactive-documentation.md
  ai/
    research/
      interactive-documentation-framework-spike.md
    specs/
      interactive-documentation-technical-roadmap.md
      interactive-documentation-roadmap-MOC.md
      .process/
        DOC-001-design-concept.md
        DOC-001-workflow.md
specs/
  doc-001-static-docs-framework-and-ia-spike/
    SPEC-MOC.md
```

---

Template based on SpecKit best practices. Populated for DOC-001 from the interactive documentation PRD, roadmap, and setup Grill Me interview.

### PR packet validation events
- <!-- speckit-pro-pr-packet-validation:event-id=pr-163 --> Blocked PR packet validation for `pr-163`; result `specs/doc-001-static-docs-framework-and-ia-spike/.process/pr-packets/pr-163/validation.json`; rules: `unknown`.
