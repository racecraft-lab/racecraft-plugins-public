# SpecKit Workflow: XPLAT-001 - Runtime Inventory and Constraints

**Template Version**: 1.0.0
**Created**: 2026-06-25
**Purpose**: Prepare XPLAT-001 for autonomous execution from the cross-platform plugin runtime roadmap and the setup Grill Me decisions.

---

## How to Use This Workflow

Run this workflow from the XPLAT-001 worktree:

```bash
$speckit-autopilot docs/ai/specs/.process/XPLAT-001-workflow.md
```

This file is already populated for XPLAT-001. Do not replace it with the generic workflow template.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during `$speckit-scaffold-spec XPLAT-001`.
The full Q&A log, Goals, Non-goals, and Open Questions live at:

```text
docs/ai/specs/.process/XPLAT-001-design-concept.md
```

Re-read the design concept before each phase. It is the source of truth for setup decisions:

- Produce one concise inventory report plus runtime and supply-chain rubrics.
- Run a whole-repo exhaustive scan, but require invocation-trace evidence before calling anything an active installed-runtime dependency.
- Classify every finding with evidence, runtime relevance, owner bucket, and follow-up spec.
- Put the durable inventory/rubric report under `docs/ai/research/`.
- Use Markdown tables, summary counts, and criteria/weights. Do not score candidates or choose runtime/security models.
- Keep verification static and source-traceable. Native runtime probes and UAT are later XPLAT work.
- Keep XPLAT-001 as one inventory/rubric spike.

> Grill Me is human-in-the-loop only. It is not part of the autopilot loop. Once this workflow starts, clarifications happen through `$speckit-clarify` and consensus, never through grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `$speckit-specify` | Complete | Created spec.md with 14 functional requirements, 3 user stories, and 0 clarification markers |
| Clarify | `$speckit-clarify` | In Progress | Session 1 accepted two-axis classification and static invocation-trace boundaries |
| Plan | `$speckit-plan` | Pending | Plan report structure, scan method, traceability rules, and verification |
| Checklist | `$speckit-checklist` | Pending | Recommended domains: data-integrity, error-handling, security, maintainability |
| Tasks | `$speckit-tasks` | Pending | Generate small report/scanning tasks with owner-bucket traceability |
| Analyze | `$speckit-analyze` | Pending | Check roadmap/design/spec/plan/tasks consistency |
| Implement | `$speckit-implement` | Pending | Produce report, rubrics, static verification, and roadmap handoff notes |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | Scope is inventory/rubrics only, no runtime/security choice, no implementation |
| G2 | After Clarify | Active-runtime evidence standard and owner buckets are unambiguous |
| G3 | After Plan | Plan uses repo-local scans, docs/research report output, and reviewability warning is recorded |
| G4 | After Checklist | All true report/rubric coverage gaps are remediated or explicitly out of scope |
| G5 | After Tasks | Tasks cover scan, classification, rubrics, validation, and roadmap handoff |
| G6 | After Analyze | No critical drift between roadmap, design concept, spec, plan, and tasks |
| G7 | After Implementation | Static scans, report review, spec-map check, and markdown/diff checks pass |

---

## Prerequisites

### Worktree and Branch

- Worktree: `.worktrees/xplat-001-runtime-inventory-constraints`
- Branch: `codex/xplat-001-runtime-inventory-constraints`
- Contract marker: `specs/xplat-001-runtime-inventory-constraints/SPEC-MOC.md`
- Design concept: `docs/ai/specs/.process/XPLAT-001-design-concept.md`

Before starting:

```bash
git rev-parse --abbrev-ref HEAD
git status --short
specify preset resolve spec-template
specify preset resolve plan-template
specify preset resolve tasks-template
```

Expected branch is `codex/xplat-001-runtime-inventory-constraints`. Preset resolution should use `.specify/presets/speckit-pro-reviewability/` unless a deliberate higher-priority override exists.

### Constitution Validation

| Principle | XPLAT-001 Requirement | Verification |
|-----------|-----------------------|--------------|
| Plugin Structure Compliance | Do not change installed plugin runtime behavior in this spec | `git diff --name-only` review |
| Script Safety | Any temporary scan snippets must be straightforward and not become shipped runtime code | command review and no new helper unless planned |
| Test Coverage Before Merge | Static checks must verify report completeness, spec-map freshness, and no scaffold placeholder drift | focused commands listed below |
| Conventional Commits | Setup and implementation commits must use conventional commit text | commit/PR review |
| KISS, Simplicity, YAGNI | Use repo-local scans and Markdown tables; no automation layer unless XPLAT-001 proves it is needed | plan complexity table and code review |

### Existing Source Truth

- Roadmap: `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`
- Product requirement: `docs/prd-cross-platform-plugin-runtime.md`
- Roadmap MOC: `docs/ai/specs/cross-platform-plugin-runtime-roadmap-MOC.md`
- Capability-discovery directive: `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`
- Grounding contract: `speckit-pro/skills/speckit-autopilot/references/grounding.md`
- Installed plugin source: `speckit-pro/skills/**`, `speckit-pro/codex-skills/**`, `speckit-pro/agents/**`, `speckit-pro/codex-agents/**`, `speckit-pro/hooks/**`, `speckit-pro/codex-hooks.json`, `speckit-pro/scripts/**`
- Generated payloads: `dist/claude/speckit-pro/**`, `dist/codex/speckit-pro/**`
- Public docs and release metadata: `docs-site/src/content/docs/**`, `speckit-pro/README.md`, `.release-please-manifest.json`, `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, and plugin manifests

### Reviewability Budget

Setup gate output:

```json
{"mode":"setup","status":"warn","pass":true,"reviewable_loc":250,"production_files":4,"total_files":10,"primary_surface_count":2,"primary_surfaces":["docs/process","harness/adapter"],"greenfield":false,"thresholds":{"warn":{"reviewable_loc":400,"production_files":6,"total_files":15,"primary_surfaces":1},"block":{"reviewable_loc":800,"production_files":8,"total_files":25,"primary_surfaces":1}},"exception_honored":false,"exception_class":null,"exceptions":{"accepted":[],"rejected":[]},"warnings":["primary surfaces 2 exceeds warn threshold 1"],"blockers":[]}
```

Record this warning in `plan.md`. It does not block setup.

### Phase 0 Preflight Results

| Check | Result | Evidence |
|-------|--------|----------|
| SpecKit prerequisites | Pass | `check-prerequisites.sh` returned `all_pass: true` on branch `codex/xplat-001-runtime-inventory-constraints` |
| Archive Sweep | Pass | Archive extension installed; `specs/` contains only `specs/xplat-001-runtime-inventory-constraints`, so no previous active spec cleanup was eligible |
| Confidence gate mode | Advisory | `resolve-confidence-mode.sh -- docs/ai/specs/.process/XPLAT-001-workflow.md` returned `advisory` |
| Codex agents | Pass | Required agents are installed under `~/.codex/agents/`; optional `autopilot-fast-helper` is also installed |
| Project commands | Recorded | `detect-commands.sh` returned all command slots as `N/A`; XPLAT-001 verification remains the workflow-listed static checks |
| Presets/extensions | Recorded | `detect-presets.sh` found `speckit-pro-reviewability`, archive/git/verify/verify-tasks/retrospective/speckit-utils extension surfaces, and configured hooks |

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | XPLAT-001 |
| **Name** | Runtime Inventory and Constraints |
| **Branch** | `codex/xplat-001-runtime-inventory-constraints` |
| **Feature directory** | `specs/xplat-001-runtime-inventory-constraints` |
| **Dependencies** | None |
| **Enables** | XPLAT-002, XPLAT-003, XPLAT-004, XPLAT-005, XPLAT-006, XPLAT-007 |
| **Priority** | P1 |

### Success Criteria Summary

- A maintainer can see the full active runtime surface and no longer has to infer which Bash references matter.
- XPLAT-002 has a clear runtime evaluation rubric and candidate evidence list.
- XPLAT-003 has a clear security/trust evaluation rubric and artifact list.
- Every active Bash dependency has a provisional owner spec: XPLAT-005, XPLAT-006, XPLAT-007, or repository-only exclusion.
- The report is reviewable as Markdown tables under `docs/ai/research/`.

---

## Phase 1: Specify

**When to run:** At the start of XPLAT-001. Focus on what the inventory and rubrics must prove, not how to port the runtime. Output: `specs/xplat-001-runtime-inventory-constraints/spec.md`

### Specify Prompt

```bash
$speckit-specify

## Feature: Runtime Inventory and Constraints

### Problem Statement
SpecKit Pro can install on multiple platforms, but active installed Claude and Codex plugin workflows still depend on Bash-backed helper execution, `jq`, shell quoting, Unix-path assumptions, `chmod`, and related Unix runtime behavior. Before choosing or building a replacement runtime, maintainers need a complete, source-traceable inventory of which references are active installed-runtime dependencies versus generated payload, public docs, repository-only tooling, tests, fixtures, or historical/archive references.

### Users
- Maintainers planning XPLAT-002 and XPLAT-003 decisions.
- Implementers of XPLAT-004 through XPLAT-007 who need owner buckets and evidence.
- Reviewers who need to verify that later runtime work is scoped to real active dependencies.

### User Stories
1. As a maintainer, I can review one Markdown inventory report under `docs/ai/research/` and understand every whole-repo Bash or Unix-runtime assumption by category and owner bucket.
2. As a runtime decision-maker, I can use a weighted runtime evaluation rubric without XPLAT-001 choosing the runtime for me.
3. As a security/trust decision-maker, I can use a weighted supply-chain evaluation rubric without XPLAT-001 choosing the security model for me.

### Constraints
- Run a whole-repo exhaustive scan, but require invocation-trace evidence before marking any finding as an active installed-runtime dependency.
- Each finding must include evidence, runtime relevance, owner bucket, and follow-up spec.
- Durable report format is Markdown with structured tables, owner buckets, and summary counts.
- Runtime/security candidates may be named as evaluation targets only; do not score them or choose a winner.
- Verification is static and source-traceable. No native Windows UAT or smoke probes in this spec.
- This is one inventory/rubric spike.

### Out of Scope
- Selecting the replacement runtime.
- Selecting supply-chain/security controls.
- Porting helpers or changing installed Claude/Codex invocations.
- Rebuilding generated payloads.
- Making public docs claim native Windows support.
- Treating untraced text matches as active runtime blockers.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 14 |
| User Stories | 3 |
| Acceptance Criteria | 7 acceptance scenarios; 8 measurable success criteria |

### Files Generated

- [x] `specs/xplat-001-runtime-inventory-constraints/spec.md`
- [x] `specs/xplat-001-runtime-inventory-constraints/checklists/requirements.md`

---

## Phase 2: Clarify

**When to run:** If Specify leaves any ambiguity around category boundaries, owner buckets, or report acceptance criteria. Maximum 5 questions per session.

### Clarify Prompts

#### Session 1: Inventory Boundaries

```bash
$speckit-clarify Focus on inventory boundaries: classify active installed-runtime dependency, generated payload, public docs, repository-only maintainer tooling, tests/fixtures, and historical/archive references. Confirm how invocation-trace evidence is proven and what counts as enough evidence for active runtime status.
```

#### Session 2: Owner Buckets and Handoff

```bash
$speckit-clarify Focus on owner buckets and follow-up specs: decide how each finding maps to read-only helper, mutation/helper, cutover guidance, repository-only exclusion, XPLAT-005, XPLAT-006, XPLAT-007, or a documented exception.
```

#### Session 3: Rubric Scope

```bash
$speckit-clarify Focus on rubric boundaries: confirm runtime and supply-chain rubrics include criteria, must-have gates, and weights, but do not score candidates or select runtime/security models before XPLAT-002 and XPLAT-003.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Inventory boundaries | 5 | Accepted: two-axis row model; active-runtime requires static caller-to-callee trace; repo-only classification is invocation-based; scan covers all tracked text including hidden paths/dist/docs/tests/archive; docs-only rows remain public-docs claims unless separately traced |
| 2 | Owner buckets and handoff | 5 | Accepted: owner bucket follows traced invocation mode, with consensus confirming separate rows for mixed read/write helpers; public docs claims remain docs-owned unless cutover changes are needed; generated payload rows map to XPLAT-007 with source links; repository-only rows require no installed trace; follow-up exceptions require reason, evidence gap, expiry/removal condition, and named decision |
| 3 | Rubric scope | 1 | Accepted: runtime and supply-chain rubrics are non-scoring templates with pass/fail must-have gates, numeric weights with stated totals, and evidence targets only; XPLAT-001 does not include candidate scoring, ranking, selection, sample scoring, or required control/runtime choices |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output: `specs/xplat-001-runtime-inventory-constraints/plan.md`

### Plan Prompt

```bash
$speckit-plan

## Tech Stack
- Repository type: Claude Code and Codex plugin marketplace.
- Primary implementation language for shipped helper scripts today: Bash with `jq` in places.
- Docs and report artifacts: Markdown under `docs/ai/` and `docs/ai/research/`.
- Tests: shell-based `tests/speckit-pro/run-all.sh`, structural Layer 1, script Layer 4, and default deterministic layers.
- Spec scaffolding: SpecKit CLI with `speckit-pro-reviewability` preset.

## Constraints
- Design concept source: `docs/ai/specs/.process/XPLAT-001-design-concept.md`.
- Roadmap source: `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`.
- Output report target: `docs/ai/research/cross-platform-runtime-inventory.md` unless Plan identifies a clearer name.
- The scan is whole-repo exhaustive for Bash, `.sh`, `jq`, shell quoting, Unix paths, `chmod`, and line-ending assumptions across tracked text files, including hidden tracked paths, `dist/**`, public docs, tests, fixtures, and archive reports. Exclude `.git/`, binary assets, untracked files, vendor caches, and non-text inputs only with rationale.
- Active installed-runtime classification requires static caller-to-callee invocation-trace evidence from installed skills, agents, hooks, generated payloads, or other installed plugin surfaces.
- Classify every finding with evidence, physical/source classification, active runtime status, runtime relevance, owner bucket, and follow-up spec.
- Use a two-axis report row schema: `classification` for source/generated/docs/tests/archive/repo-only/exclusion and `active_runtime_status` for proven active runtime, unproven active runtime, or not active runtime.
- Use Markdown tables with summary counts. Do not add JSON/CSV unless the plan records a concrete review benefit.
- Define runtime and supply-chain criteria, pass/fail must-have gates, and explicit numeric weights with stated totals. Do not score candidates, include sample scoring, rank options, or choose a runtime/security model.
- Static verification only: source scans, traceability review, spec-index check, `git diff --check`, and any relevant markdown/link validation already available.
- Record the setup gate warning about two primary surfaces.

## Architecture Notes
- Treat this as a docs/process spike. No active runtime invocation should change.
- Prefer repo-local commands and deterministic grep/ripgrep scans over a new automation layer unless the plan proves a reusable helper is necessary.
- Classify repository-only tooling by invocation evidence, not path alone; root scripts, release helpers, CI-only helpers, and maintainer tools are not active runtime unless an installed plugin surface invokes them.
- Treat public docs rows as `public-docs-claim`; link them to active-runtime findings only when static invocation traces prove the same dependency.
- Owner bucket follows the traced active invocation mode, not the helper's maximum capability. For mixed read/write helpers, create separate rows when read-only and write/apply modes are traced or materially relevant.
- Use `xplat-005-read-only-helper` only for traced read-only/advisory invocations that do not mutate repository, user-local, or external state. Use `xplat-006-mutation-helper` for traced write/apply/live/install/PR-emission behavior or mutation-capable dry-run/apply behavior whose parity must preserve apply semantics.
- Map active generated payload rows to `xplat-007-cutover-guidance` with source links; do not treat generated payloads as authoritative edit targets.
- Use `follow-up-exception` only for active or probably active rows that cannot honestly map to XPLAT-005, XPLAT-006, XPLAT-007, or an exclusion bucket; require reason, evidence gap, expiry/removal condition, and named follow-up decision.
- Keep candidate runtime/security evidence lists separate from candidate scoring; candidates and controls are evidence targets only until XPLAT-002 and XPLAT-003.
- Include owner buckets that later specs can consume directly:
  - `xplat-005-read-only-helper`
  - `xplat-006-mutation-helper`
  - `xplat-007-cutover-guidance`
  - `repository-only-exclusion`
  - `public-docs-claim`
  - `generated-payload-reference`
  - `historical-or-archive`
  - `follow-up-exception`

## Verification Strategy
- Re-run the search commands used for the inventory and confirm the report covers the result set or explains exclusions.
- Verify active-runtime rows cite static caller-to-callee invocation traces.
- Verify docs-only and repository-only rows are not promoted to active runtime without invocation evidence.
- Run `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"`.
- Run `git diff --check`.
- Run the smallest relevant repo validation command if files outside docs/process change.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Pending | Technical context, scan method, report structure |
| `research.md` | Pending | Optional; prefer the durable docs/ai/research report for final output |
| `data-model.md` | Pending | Inventory row schema and rubric fields if needed |
| `contracts/` | Pending | Not expected unless report schema becomes machine-checked |
| `quickstart.md` | Pending | Maintainer verification guide if useful |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan`. Validate the spec and plan together.

### Recommended Domains

| Domain | Why |
|--------|-----|
| data-integrity | The report must not misclassify active runtime references or lose evidence. |
| error-handling | Scan gaps, ambiguous traces, and unsupported classifications need clear fallback treatment. |
| security | Supply-chain rubric and consumer-trust boundaries must not overclaim guarantees. |
| maintainability | Later XPLAT specs must be able to consume owner buckets without redoing the inventory. |

### Checklist Prompts

#### 1. data-integrity Checklist

```bash
$speckit-checklist data-integrity

Focus on XPLAT-001 requirements:
- Every inventory row has evidence and classification.
- Active runtime rows require invocation-trace evidence.
- Whole-repo scan matches are either represented or explicitly excluded.
- Owner bucket and follow-up spec are present where applicable.
- Pay special attention to false positives from tests, fixtures, archive reports, and public docs.
```

#### 2. error-handling Checklist

```bash
$speckit-checklist error-handling

Focus on XPLAT-001 requirements:
- The plan handles ambiguous references without silently promoting them to blockers.
- Missing or partial traces have a documented classification.
- Static verification failures produce actionable remediation steps.
- Pay special attention to generated payload references whose source-of-truth lives elsewhere.
```

#### 3. security Checklist

```bash
$speckit-checklist security

Focus on XPLAT-001 requirements:
- The supply-chain rubric covers dependency policy, lockfiles, generated payload integrity, vulnerability scanning, provenance, checksums/signatures, SBOMs, and consumer-local verification.
- The report avoids marketing unsupported security guarantees.
- Pay special attention to separating first-release must-have gates from deferred hardening.
```

#### 4. maintainability Checklist

```bash
$speckit-checklist maintainability

Focus on XPLAT-001 requirements:
- Report tables can be consumed by XPLAT-002 through XPLAT-007 without re-triage.
- Owner buckets are stable and named consistently.
- The output is concise enough for PR review despite the whole-repo scan.
- Pay special attention to whether a new machine-readable artifact is truly unnecessary.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| data-integrity | Pending | Pending | Pending |
| error-handling | Pending | Pending | Pending |
| security | Pending | Pending | Pending |
| maintainability | Pending | Pending | Pending |

---

## Phase 5: Tasks

**When to run:** After checklists complete and all true gaps are resolved. Output: `specs/xplat-001-runtime-inventory-constraints/tasks.md`

### Tasks Prompt

```bash
$speckit-tasks

## Task Structure
- Keep tasks story-organized and report-focused.
- Do not create runtime implementation tasks.
- Include explicit tasks for scan command definition, report row schema, whole-repo result classification, runtime rubric, supply-chain rubric, static verification, and roadmap handoff.
- Mark parallel-safe tasks with [P] only when they touch independent report sections or validation scripts.

## Implementation Phases
1. Foundation: report outline, scan command set, inventory row schema, owner buckets.
2. US1: whole-repo inventory and classification table.
3. US2: runtime evaluation rubric and candidate evidence list for XPLAT-002.
4. US3: supply-chain/trust evaluation rubric and artifact list for XPLAT-003.
5. Polish: static verification, spec-map check, roadmap/status notes, and PR review packet evidence.

## Constraints
- Durable report target is under `docs/ai/research/`.
- Specs artifacts stay under `specs/xplat-001-runtime-inventory-constraints/`.
- Do not modify active installed runtime invocations.
- Do not rebuild `dist/`.
- Do not score or select candidates.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| Total Tasks | Pending |
| Phases | Pending |
| Parallel Opportunities | Pending |
| User Stories Covered | Pending |

---

## Atomicity Route

This section is filled after the Tasks phase by the autopilot. Leave it blank during scoping.

| Field | Value | Meaning |
|-------|-------|---------|
| Route | | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| Releasable | | `true`, or `false` for destructive/concurrency-sensitive changes. |
| Signals | | Decisive detector findings. |
| Warnings | | Release-safety warnings. |

To produce the decision:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/xplat-001-runtime-inventory-constraints
```

---

## Phase 6: Analyze

**When to run:** After generating tasks.

### Analyze Prompt

```bash
$speckit-analyze

Focus on:
1. Cross-artifact consistency across roadmap, design concept, spec.md, plan.md, tasks.md, and the docs/ai/research report target.
2. Scope drift: no runtime/security selection, no helper porting, no active invocation changes, no generated payload rebuild.
3. Coverage gaps: every required inventory classification field, runtime rubric field, and supply-chain rubric field has a task.
4. Evidence integrity: active runtime rows require invocation traces, not text matches alone.
5. Reviewability: the setup warning is recorded and implementation tasks remain a one-spike docs/process slice.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| Pending | Pending | Pending | Pending |

---

## Phase 7: Implement

**When to run:** After tasks are generated and analyzed with no unresolved critical findings.

### Implement Prompt

```bash
$speckit-implement

## Approach
- Treat this as an inventory/rubric spike.
- Run the planned whole-repo searches and classify every result.
- Preserve evidence paths and invocation traces in the report.
- Keep the report concise enough for review; use summary counts plus detailed tables.
- Update roadmap progress only as allowed by the workflow and actual completion state.

### Pre-Implementation Setup
1. Verify branch: `git rev-parse --abbrev-ref HEAD`.
2. Verify clean worktree or only expected spec artifacts: `git status --short`.
3. Re-read `docs/ai/specs/.process/XPLAT-001-design-concept.md`.
4. Re-read `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`.
5. Confirm preset resolution with `specify preset resolve spec-template`, `plan-template`, and `tasks-template`.

### Verification Commands
Run at minimum:

```bash
speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"
git diff --check
```

Also run any focused report or docs validation command created by the plan/tasks.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| Foundation | Pending | Pending | Report outline, scan set, schema |
| US1 Inventory | Pending | Pending | Whole-repo scan and classification |
| US2 Runtime rubric | Pending | Pending | XPLAT-002 handoff |
| US3 Supply-chain rubric | Pending | Pending | XPLAT-003 handoff |
| Polish | Pending | Pending | Static checks and roadmap handoff |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in `tasks.md`.
- [ ] Inventory report exists under `docs/ai/research/`.
- [ ] Report covers all planned scan commands or explains exclusions.
- [ ] Active runtime rows include invocation traces.
- [ ] Runtime rubric includes criteria, must-have gates, and weights without scoring candidates.
- [ ] Supply-chain rubric includes criteria, must-have gates, and weights without selecting controls.
- [ ] No active runtime invocation is changed.
- [ ] `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"` passes.
- [ ] `git diff --check` passes.
- [ ] PR packet records scope, non-goals, review order, verification evidence, known gaps, and rollback notes.

---

## Lessons Learned

### What Worked Well

- Pending.

### Challenges Encountered

- Pending.

### Patterns to Reuse

- Pending.
