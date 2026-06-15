# SpecKit Workflow: DOC-003 - Claude Code Marketplace Installation Path

**Template Version**: 1.0.0
**Created**: 2026-06-14
**Purpose**: Prepare and execute the Claude Code install-path documentation slice.

---

## How to Use This Workflow

Run this workflow from the `doc-003-claude-code-marketplace-installation-path`
branch. Keep the implementation docs-only unless a later phase explicitly
shows that a source file is misleading Claude Code users and must be corrected
for install accuracy.

The next command is:

```bash
$speckit-autopilot docs/ai/specs/.process/DOC-003-workflow.md
```

---

## Design Concept

This workflow was enriched from the Grill Me setup interview. The full Q&A log,
Goals, Non-goals, and Open Questions live at:

```text
docs/ai/specs/.process/DOC-003-design-concept.md
```

Re-read it before each phase. If a downstream artifact contradicts the design
concept, treat the downstream artifact as wrong unless it carries an explicit
revision note approved during the workflow.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | Complete | Created `spec.md` and requirements checklist; G1 passed with 0 clarification markers. |
| Clarify | `/speckit-clarify` | Complete | Skipped by G1 routing: no `[NEEDS CLARIFICATION]` markers remained after Specify. |
| Plan | `/speckit-plan` | Complete | Created docs-only plan artifacts; G3 passed and reviewability estimate projected 0 production LOC. |
| Checklist | `/speckit-checklist` | Complete | UX, accessibility, security, and error-handling checklists passed; G4 passed with 0 gaps. |
| Tasks | `/speckit-tasks` | Complete | Created 39 tasks across 9 phases; G5 passed and marker planning produced 5 review markers. |
| Analyze | `/speckit-analyze` | Complete | 0 findings; G6 passed with no critical/high drift. |
| Implement | `/speckit-implement` | Complete | Updated Claude install route and install-relevant terminology; G7 passed. |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

Each phase requires human review and approval before proceeding.

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | Claude install scope, non-goals, source authority, and success checks are explicit. |
| G2 | After Clarify | No unresolved questions remain about terminology, verification, or trust depth. |
| G3 | After Plan | Plan is docs-only, references real file paths, and stays inside the DOC-003 slice. |
| G4 | After Checklist | Gaps are either fixed in spec/plan or explicitly deferred to DOC-007/DOC-008. |
| G5 | After Tasks | Tasks cover DOC-003 acceptance criteria and avoid Codex procedure work. |
| G6 | After Analyze | No critical drift remains between design concept, spec, plan, and tasks. |
| G7 | After Implementation | Docs validation passes and the Claude page is manually reviewed for command leakage. |

---

## Prerequisites

### Constitution Validation

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Plugin Structure Compliance | Do not change plugin runtime layout or generated payloads unless a docs source correction requires it. | `bash tests/speckit-pro/run-all.sh --layer 1` if plugin metadata or manifests change. |
| Script Safety | No shell scripts are expected in DOC-003. If a script changes, it must keep `#!/usr/bin/env bash` and `set -euo pipefail`. | `bash -n <script>` and relevant Layer 4 test. |
| Semantic Versioning | Do not manually bump plugin versions as part of docs work. | `git diff` shows no manual version edits. |
| Test Coverage Before Merge | Docs-only changes should validate the docs site and targeted links. | `pnpm --dir docs-site validate`; add repo tests only if runtime files change. |
| Conventional Commits | PR title must be public-readable and conventional. | PR title shape: `docs: document Claude Code install path` or equivalent. |
| KISS, Simplicity & YAGNI | Prefer one canonical Claude install route and concise cross-links over duplicate command matrices. | Review spec, plan, and docs diff for duplication. |

**Constitution Check:** Verified after G1; DOC-003 remains docs/process-only with no runtime/plugin layout change.

### Reviewability Budget

- Setup gate input: `docs/ai/specs/interactive-documentation-technical-roadmap.md`
- Setup gate result: pass
- Reviewable LOC: 395
- Production files: 0
- Total files: 6
- Primary surface: docs/process
- Advisory Grill Me estimate: 220 LOC, 1 slice, status `ok`

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| Spec ID | DOC-003 |
| Name | Claude Code marketplace installation path |
| Branch | `doc-003-claude-code-marketplace-installation-path` |
| Dependencies | DOC-002 completed and archived after PRs #173-#177 |
| Enables | DOC-005, DOC-007, DOC-008 |
| Priority | P1 |
| Tool count | No runtime tool changes expected; this is docs/process work. |
| Tool names | Claude Code `/plugin` UI and namespaced `/speckit-pro:<skill>` invocations are documented, not modified. |

### Roadmap Scope

DOC-003 ships the Claude-specific install/update/uninstall and invocation docs.
It must document:

- `/plugin marketplace add racecraft-lab/racecraft-plugins-public`
- `/plugin install speckit-pro@racecraft-plugins-public`
- `/plugin marketplace update racecraft-plugins-public`
- `/plugin uninstall speckit-pro@racecraft-plugins-public`
- `/reload-plugins` after install, enable/disable, update, or uninstall events when the user wants to stay in the same Claude Code session
- verification through `/plugin`, `/speckit-pro:speckit-status`, and `/speckit-pro:speckit-coach`
- update, uninstall, marketplace removal, and reinstall checks
- `/speckit-pro:*` namespacing
- skills, agents, hooks, MCP/settings, managed marketplaces, and generated Claude payloads
- legacy/current wording around deprecated command-folder language, consolidated around skills

### Success Criteria Summary

- [ ] Claude Code users can add the marketplace, install SpecKit Pro, reload plugins, verify it, update it, uninstall it, remove the marketplace when appropriate, and reinstall it from one canonical route.
- [ ] User-facing docs consistently prefer "skills" terminology over deprecated "commands" wording where the Claude install path would otherwise be misleading.
- [ ] The page cites official Claude Code docs for platform behavior and repository files for this marketplace/plugin's exact source and payload paths.
- [ ] The page includes a deep Claude-specific trust section without becoming the full DOC-008 troubleshooting/rollback matrix.
- [ ] Codex install details are limited to a cross-link to the Codex install route.

---

## Phase 1: Specify

**When to run:** At the start of this feature specification. Focus on what the
Claude Code user must be able to do, why the route exists, and what is out of
scope. Output: `specs/doc-003-claude-code-marketplace-installation-path/spec.md`.

### Specify Prompt

```bash
/speckit-specify "Ship the Claude Code marketplace installation path for SpecKit Pro. The primary deliverable is docs-site/src/content/docs/install/claude-code.md as the canonical user route. The page must cover add marketplace, install, reload plugins, verify, update, uninstall, marketplace removal, and reinstall checks for /plugin-based Claude Code usage; explain /speckit-pro:<skill> namespacing; consolidate install-relevant wording around skills rather than deprecated command-folder language; cite official Claude Code docs plus repository source/generated payload files; include deep Claude-specific trust guidance for skills, agents, hooks, MCP/settings, generated payloads, and managed marketplaces; and limit Codex details to a cross-link. Do not change plugin runtime behavior, regenerate payloads, bump versions, or build the full troubleshooting matrix."
```

### Detailed Prompt

```bash
/speckit-specify

## Feature: Claude Code Marketplace Installation Path

### Problem Statement
The docs-site Claude install route is currently a DOC-002 shell. Claude Code
users need a complete, source-backed path for adding the Racecraft marketplace,
installing SpecKit Pro, reloading plugins, verifying the namespaced skill
surface, updating, uninstalling, removing the marketplace when appropriate, and
understanding the trust implications before running plugin skills.

### Users
- Claude Code users installing SpecKit Pro from the public Racecraft marketplace.
- Evaluators who need to inspect source, generated payloads, hooks, and agents before install.
- Maintainers who need docs that distinguish authoring source from generated Claude install payloads.

### User Stories
- As a Claude Code user, I can add the Racecraft marketplace and install SpecKit Pro with exact commands.
- As a Claude Code user, I can verify the install through `/plugin`, `/speckit-pro:speckit-status`, and `/speckit-pro:speckit-coach`.
- As a Claude Code user, I can update, uninstall, remove the marketplace when appropriate, and reinstall the plugin without guessing at lifecycle commands.
- As an evaluator, I can see which skills, agents, hooks, MCP/settings, and generated payload files affect trust before install.
- As a maintainer, I can see source and generated payload paths without confusing deprecated command-folder wording for current skill-based usage.

### Constraints
- Primary surface is docs/process; production files should stay at 0.
- The canonical page is `docs-site/src/content/docs/install/claude-code.md`.
- Patch install-relevant README/AGENTS wording broadly enough to eliminate command-vs-skill confusion, but avoid unrelated repository-maintainer rewrites.
- Official Claude Code docs are the authority for platform behavior; repository manifests and payloads are the authority for this plugin's exact paths.
- Use `pnpm --dir docs-site validate` for docs-site validation.

### Out of Scope
- Codex install instructions except a cross-link to `/install/codex/`.
- Full troubleshooting matrix, rollback procedures, and every failure mode.
- Plugin runtime behavior changes, generated payload regeneration, version bumps, or release automation changes.
- Side-by-side Claude/Codex command comparison.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 14 |
| User Stories | 5 |
| Acceptance Criteria | 14 acceptance scenarios across 5 user stories |

### Files Generated

- [x] `specs/doc-003-claude-code-marketplace-installation-path/spec.md`
- [x] `specs/doc-003-claude-code-marketplace-installation-path/checklists/requirements.md`

---

## Phase 2: Clarify

**When to run:** Use Clarify only if Specify leaves ambiguity. Maximum 5 targeted
questions per session.

### Clarify Prompts

#### Session 1: Terminology And Source Authority

```bash
/speckit-clarify "Focus on terminology and source authority for DOC-003: every install-relevant user-facing surface should prefer skills over deprecated command-folder wording; official Claude Code docs should anchor platform behavior; repository source and dist/claude payloads should anchor SpecKit Pro specifics. Resolve any ambiguity about which README/AGENTS wording must change in this slice versus later DOC-007/docs-hygiene work."
```

#### Session 2: Lifecycle And Verification

```bash
/speckit-clarify "Focus on Claude Code install lifecycle verification for DOC-003: add marketplace, install, /reload-plugins, verify with /plugin UI, verify /speckit-pro:speckit-status, sanity-check /speckit-pro:speckit-coach, update, uninstall, marketplace removal, and reinstall. Resolve any ambiguity about exact success criteria and what should be deferred to DOC-008 troubleshooting."
```

#### Session 3: Trust Depth And Platform Separation

```bash
/speckit-clarify "Focus on trust depth and platform separation for DOC-003: include deep Claude-specific trust context for skills, agents, hooks, MCP/settings, generated payloads, and managed marketplaces, while limiting Codex details to a cross-link. Resolve where the trust section belongs and what belongs later in DOC-008."
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Terminology and source authority | 0 | Skipped by G1: no clarification markers remained in `spec.md`. |
| 2 | Lifecycle and verification | 0 | Skipped by G1: lifecycle and verification requirements are explicit in FR-002 through FR-007. |
| 3 | Trust depth and platform separation | 0 | Skipped by G1: trust/source/Codex-boundary requirements are explicit in FR-008 through FR-013. |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output:
`specs/doc-003-claude-code-marketplace-installation-path/plan.md`.

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Docs site: Astro 6.4.6 with Starlight 0.40.0.
- Content format: Markdown under `docs-site/src/content/docs/`.
- Package manager: pnpm 10.25.0 from `docs-site/package.json`.
- Repository docs: Markdown in `README.md`, `AGENTS.md`, `speckit-pro/README.md`, and docs-site pages.
- Plugin source: `speckit-pro/skills`, `speckit-pro/agents`, `speckit-pro/hooks/hooks.json`, `speckit-pro/.claude-plugin/plugin.json`.
- Generated Claude payload: `dist/claude/speckit-pro/` and `.claude-plugin/marketplace.json`.
- Testing: `pnpm --dir docs-site validate`; add `bash tests/speckit-pro/run-all.sh --layer 1` only if plugin manifests, hooks, agents, skills, or generated payloads change.

## Constraints
- Keep DOC-003 docs-only unless a source wording patch is directly required for install accuracy.
- Do not regenerate `dist/**`, bump versions, change plugin behavior, or edit release automation.
- Preserve Codex scope for DOC-004; the Claude page may cross-link but must not explain Codex install steps.
- Source authority decision from the design concept: cite both official Claude Code docs and repository source/dist files.
- User's Q2 decision: consolidate on skills terminology rather than command-folder language anywhere install-relevant.
- User's Q7 decision: include a deep Claude-specific trust section, but do not absorb the full DOC-008 troubleshooting matrix.

## Architecture Notes
- Treat `docs-site/src/content/docs/install/claude-code.md` as the canonical user route.
- Keep install commands in one sequential procedure section, then verification, lifecycle maintenance, and trust/reference sections.
- Prefer local relative links for docs-site pages and stable GitHub/source paths only where external repository citations are necessary.
- If README/AGENTS changes are needed, keep them limited to install-facing terminology and command-to-skill corrections.
- The design concept at `docs/ai/specs/.process/DOC-003-design-concept.md` is the source of truth for scope and non-goals.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Complete | Docs-only implementation plan and declared file operations. |
| `research.md` | Complete | Records official Claude Code docs and repository source/generated-payload citation policy. |
| `data-model.md` | Complete | Models documentation concepts and validation relationships only; no runtime data storage. |
| `contracts/` | Omitted | No API, schema, parser, or CLI grammar contract is introduced by DOC-003. |
| `quickstart.md` | Complete | Docs validation scenarios for install route, lifecycle, trust inventory, terminology, and runtime-surface boundaries. |

Plan-phase reviewability estimate:

- Status: pass
- Projected production LOC: 0
- Declared file entries: 8
- Outcome: advisory pass; continue to domain checklists.

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan`. Validate spec and plan together.

### Recommended Domains

#### 1. UX Checklist

Why this domain: The primary deliverable is a user-facing install route with a
step-by-step procedure.

```bash
/speckit-checklist ux

Focus on DOC-003 Claude install requirements:
- The add/install/verify/update/remove flow is ordered the way a first-time Claude Code user will follow it.
- The page makes the canonical path obvious without duplicating Codex procedure detail.
- Verification steps are concrete and low-risk: /plugin UI, /speckit-pro:speckit-status, and /speckit-pro:speckit-coach.
- Pay special attention to: whether deep trust content interrupts the install flow or belongs after verification.
```

#### 2. Accessibility Checklist

Why this domain: The docs page must stay scannable, linkable, and usable in a
static docs site.

```bash
/speckit-checklist accessibility

Focus on DOC-003 Claude install requirements:
- Headings, lists, and code blocks are structured for screen readers and deep links.
- Link text identifies the destination without relying on surrounding prose.
- Command examples are copyable and not hidden in dense tables.
- Pay special attention to: avoiding overloaded comparison tables that mix Claude and Codex command forms.
```

#### 3. Security Checklist

Why this domain: DOC-003 includes a deep trust section about plugin install
surfaces.

```bash
/speckit-checklist security

Focus on DOC-003 Claude install requirements:
- Trust guidance names the installed surfaces: skills, agents, hooks, MCP/settings, generated Claude payloads, and marketplace metadata.
- The page distinguishes official Claude Code behavior from repository-specific claims.
- Managed marketplace and source inspection guidance is accurate without becoming a full rollback matrix.
- Pay special attention to: avoiding unsupported claims about sandboxing or hook behavior.
```

#### 4. Error Handling Checklist

Why this domain: The page covers remove/reinstall and basic failure recovery,
while DOC-008 owns the full troubleshooting matrix.

```bash
/speckit-checklist error-handling

Focus on DOC-003 Claude install requirements:
- Basic recovery is defined for wrong marketplace, missing plugin, failed verification, update, remove, and reinstall.
- Each recovery path says when to move to troubleshooting instead of expanding DOC-003.
- Codex-specific failures are routed to the Codex page or later DOC-008.
- Pay special attention to: keeping rollback and cache-depth content out of this slice unless required for Claude install safety.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| ux | 14 | 1 found, 1 fixed, 0 remaining | FR-008, plan Structure Decision: progressive trust disclosure. |
| accessibility | 13 | 6 found, 6 fixed, 0 remaining | FR-015 through FR-018 and SC-007 added for accessible headings, links, code blocks, and no mixed Claude/Codex command table. |
| security | 19 | 4 found, 4 fixed, 0 remaining | FR-019 through FR-021 added for sandboxing/hook/managed-marketplace claim boundaries and trust-surface specificity. |
| error-handling | 24 | 7 found, 7 fixed, 0 remaining | FR-022 through FR-024 and SC-008 added for concise basic recovery and DOC-008/Codex routing. |
| Total | 70 | 18 found, 18 fixed, 0 remaining | G4 passed with 0 `[Gap]` markers across all checklist files. |

---

## Phase 5: Tasks

**When to run:** After checklists complete and gaps are resolved.
Output: `specs/doc-003-claude-code-marketplace-installation-path/tasks.md`.

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Organize tasks by user-visible docs outcome: source audit, Claude page content, terminology consistency, validation.
- Keep each task small and testable.
- Mark parallel-safe tasks with [P] only when they do not touch the same Markdown files.
- Reference `spec.md`, `plan.md`, and `docs/ai/specs/.process/DOC-003-design-concept.md`.
- Use the design concept's non-goals to reject tasks that implement Codex install docs, full troubleshooting, payload regeneration, version changes, or runtime behavior changes.

## Implementation Phases
1. Source audit: collect official Claude Code docs links and repo source/dist evidence.
2. Claude install page: replace the DOC-002 shell with full add/install/verify/update/remove/reinstall content and deep trust guidance.
3. Terminology consistency: update install-relevant README/AGENTS/docs wording to prefer skills over deprecated command-folder language.
4. Cross-links and boundaries: link Codex route without embedding Codex procedure; route full troubleshooting/rollback to later docs.
5. Validation: run docs-site validation and targeted repo checks if non-doc surfaces changed.

## Constraints
- Primary canonical file: `docs-site/src/content/docs/install/claude-code.md`.
- Likely supporting files: `README.md`, `AGENTS.md`, `speckit-pro/README.md`, `docs-site/src/content/docs/reference.md`, `docs-site/src/content/docs/security-and-trust.md`, or `docs-site/src/content/docs/troubleshooting.md` only if needed for navigation or boundary clarity.
- Do not edit `dist/**`, package versions, generated payloads, plugin manifests, hooks, or agents unless a later approved plan explicitly requires it.
- Validation command: `pnpm --dir docs-site validate`.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| Total Tasks | 39 |
| Phases | 9 |
| Parallel Opportunities | 8 |
| User Stories Covered | 5 |
| Functional Requirement Coverage | FR-001 through FR-024 mapped. |
| Success Criteria Coverage | SC-001 through SC-008 mapped. |
| G5 Gate | Passed: 39 tasks found, 0 markers. |
| Task Reviewability Gate | Size-only block: `reviewable_loc=1560`, `total_files=47`, `production_files=1`; evidence in `specs/doc-003-claude-code-marketplace-installation-path/.process/reviewability/tasks-gate.json`. |

---

## Atomicity Route

After the Tasks phase / G5 gate, the autopilot SKILL runs the read-only
atomicity classifier and records its decision here. Leave the cells blank
during scoping.

| Field | Value | Meaning |
|-------|-------|---------|
| Route | `one-navigable-PR` | One navigable docs PR with review markers, not a runtime split. |
| Releasable | `true` | No destructive migration or concurrency-sensitive change. |
| Signals | `change-shape:modify-heavy` | The change is docs-heavy and should be reviewed by story markers. |
| Warnings | None | No release-safety warning attached to the change. |

To produce the decision, run:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/doc-003-claude-code-marketplace-installation-path
```

### Review Plan

| Field | Value |
|-------|-------|
| Status | Single install-instruction PR |
| Review Shape | One Claude Code install route aligned to DOC-004's Codex install route structure. |
| Review Focus | Compare Claude Code-specific content against the shared install-page section skeleton. |
| Warning Count | 1 historical reviewability size warning, resolved by keeping the PR single and navigable. |
| Output | PR #187: `https://github.com/racecraft-lab/racecraft-plugins-public/pull/187` |
| Layer Plan | Skipped because atomicity route is `one-navigable-PR`, not `split-PR`. |

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```bash
/speckit-analyze

Focus on:
1. Constitution alignment: docs-only scope, no manual version bumps, no runtime behavior changes, no speculative rewrites.
2. Design-concept consistency: ensure spec, plan, and tasks follow Q1-Q9 from `docs/ai/specs/.process/DOC-003-design-concept.md`.
3. Command-vs-skill wording: flag any install-relevant surface that still tells users to rely on deprecated command-folder wording instead of plugin skills.
4. Codex leakage: verify the Claude page cross-links to Codex but does not explain Codex install procedure.
5. Source authority: verify official Claude Code docs are used for platform behavior, and repository source/dist files are used for SpecKit Pro specifics.
6. DOC-008 boundary: flag rollback, cache-depth, or full troubleshooting content that should be deferred unless needed for safe install/update/remove basics.
7. Validation coverage: ensure tasks include `pnpm --dir docs-site validate` and any targeted repo tests required by changed files.
```

### Analyze Severity Levels

| Severity | Meaning | Action Required |
|----------|---------|-----------------|
| CRITICAL | Violates scope, contradicts design concept, or produces wrong install commands. | Must fix before G6. |
| HIGH | Significant docs gap, misleading trust claim, or missing validation. | Should fix before implementation. |
| MEDIUM | Useful improvement or clarity issue. | Review and decide. |
| LOW | Minor wording or consistency issue. | Note for future if not fixed. |

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| A-000 | None | Analyze found 0 findings across constitution alignment, design-concept consistency, command-vs-skill wording, Codex leakage, source authority, DOC-008 boundary, and validation coverage. | No changes required; G6 passed. |

### Pre-Implementation Confidence

📊 Confidence: 0.94

- Task understanding: 0.96
- Approach clarity: 0.93
- Requirements alignment: 0.95
- Risk assessment: 0.91
- Completeness: 0.95

Confidence rationale: Analyze found no findings, G6 passed, tasks map every FR/SC, reviewability is size-only with marker planning, and implementation remains docs-only with `pnpm --dir docs-site validate` as the required verification command.

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed with no critical
coverage gaps.

### Implement Prompt

```bash
/speckit-implement

## Approach: Docs-First Validation

For each task, follow this cycle:

1. RED: Identify the current docs gap, stale wording, or missing validation target.
2. GREEN: Make the smallest Markdown/content edit that satisfies the accepted task.
3. REFACTOR: Consolidate duplicated command wording and keep the canonical Claude path clear.
4. VERIFY: Run the relevant docs validation and manually review the rendered source for Claude/Codex separation.

### Pre-Implementation Setup

1. Verify branch: `git rev-parse --abbrev-ref HEAD` should print `doc-003-claude-code-marketplace-installation-path`.
2. Review design concept: `docs/ai/specs/.process/DOC-003-design-concept.md`.
3. Review source docs: `docs-site/src/content/docs/install/claude-code.md`, `README.md`, `AGENTS.md`, and `speckit-pro/README.md`.
4. Review repository evidence: `.claude-plugin/marketplace.json`, `speckit-pro/.claude-plugin/plugin.json`, `dist/claude/speckit-pro/.claude-plugin/plugin.json`, `speckit-pro/agents/`, and `speckit-pro/hooks/hooks.json`.

### Implementation Notes

- Keep the Claude route self-contained for first install, reload, verification, update, uninstall, marketplace removal, and reinstall.
- Use exact Claude Code commands only where official docs and repo evidence support them.
- Prefer "skill" / "plugin skill" language for SpecKit Pro invocation.
- Explain agents, hooks, MCP/settings, generated payloads, and managed marketplace trust clearly, without unsupported security claims.
- Route Codex users to the Codex install page; do not teach Codex commands here.
- Do not edit generated payloads or plugin manifests as part of docs implementation unless the spec/plan/tasks explicitly justify the change.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Source audit | T001-T006 | 6/6 | Official Claude docs and repository source/generated evidence audited. |
| 2 - Scope and reviewability gate | T007-T008 | 2/2 | Docs-only boundaries confirmed before page edits. |
| 3 - US1 install route | T009-T013 | 5/5 | First-time Racecraft marketplace install and verification path added. |
| 4 - US2 skill verification | T014-T016 | 3/3 | Namespaced SpecKit Pro skill checks added. |
| 5 - US3 lifecycle and recovery | T017-T021 | 5/5 | Update, uninstall, remove, reinstall, and basic recovery added. |
| 6 - US4 trust surfaces | T022-T026 | 5/5 | Source-backed trust inventory and security boundaries added. |
| 7 - US5 terminology consistency | T027-T030 | 4/4 | Install-relevant README and AGENTS terminology aligned. |
| 8 - Cross-links and boundaries | T031-T033 | 3/3 | Codex and DOC-008 content routed out of DOC-003. |
| 9 - Validation and PR evidence | T034-T039 | 6/6 | Quickstart checks, docs validation, scope checks, and PR evidence prepared. |

### Implementation Results

| Evidence | Result |
|----------|--------|
| G7 Gate | Passed: all 39 tasks complete. |
| Docs Validation | `pnpm --dir docs-site validate` passed after installing docs-site dependencies from the lockfile. |
| Command Coverage | Required install, reload, `/plugin`, `/speckit-pro:speckit-status`, and `/speckit-pro:speckit-coach` checks present. |
| Lifecycle Coverage | Update, uninstall, marketplace removal, reinstall, and bounded recovery guidance present. |
| Runtime Scope | No changes under `dist/`, plugin source/runtime paths, release automation, or GitHub workflows. |
| Final Reviewability | Proceeded as a single install-instruction PR after DOC-003 was aligned to DOC-004's page structure; stale marker-split candidate artifacts were removed. |
| PR Packet | Generated `specs/doc-003-claude-code-marketplace-installation-path/.process/pr-packet/pr-packet.json` and `pr-body.md`; `validate-pr-packet.sh` passed. |
| Marker Emission | Not applicable after structure alignment; stale candidate marker-split artifacts were removed from PR #187. |
| PR Creation | Ready PR #187 remains the single Claude Code install-instruction PR: `https://github.com/racecraft-lab/racecraft-plugins-public/pull/187`. |

---

## Post-Implementation Checklist

- [x] All tasks are marked complete in `tasks.md`.
- [x] `pnpm --dir docs-site validate` passes.
- [x] `bash tests/speckit-pro/run-all.sh --layer 1` is not required because plugin manifests, hooks, agents, skills, payload references, and structural files were not changed.
- [x] Manual review confirms the Claude page contains no Codex procedure leakage.
- [x] Manual review confirms install-relevant docs use skills terminology consistently.
- [x] Manual review confirms DOC-008 troubleshooting/rollback depth was not absorbed into DOC-003.
- [x] PR body/packet generated with a public-readable conventional title.
- [x] PR created with a public-readable conventional title: `https://github.com/racecraft-lab/racecraft-plugins-public/pull/187`.

---

## Project Structure Reference

```text
racecraft-plugins-public/
├── AGENTS.md
├── README.md
├── .claude-plugin/marketplace.json
├── docs-site/
│   ├── package.json
│   └── src/content/docs/install/claude-code.md
├── docs/ai/specs/interactive-documentation-technical-roadmap.md
├── speckit-pro/
│   ├── README.md
│   ├── .claude-plugin/plugin.json
│   ├── agents/
│   ├── hooks/hooks.json
│   └── skills/
├── dist/claude/speckit-pro/
└── specs/doc-003-claude-code-marketplace-installation-path/
```

---

Template based on SpecKit best practices. Populated for DOC-003 from the
technical roadmap and the setup Design Concept.

### PR packet validation events
- <!-- speckit-pro-pr-packet-validation:event-id=pr-packet --> Blocked PR packet validation for `pr-packet`; result `specs/doc-003-claude-code-marketplace-installation-path/.process/pr-packets/pr-packet/validation.json`; rules: `unknown`.

---

## Post-Merge Archive

| Item | Result |
|------|--------|
| PR | #187 `docs(DOC-003): add Claude Code install route` |
| Merge commit | `afc197a278001c7b8c2ffeb973c359971676d597` |
| Merged at | 2026-06-15T20:26:31Z |
| Archive report | `.specify/memory/archive-reports/2026-06-15-doc-003-004-post-merge-hygiene.md` |
| Cleanup | Active spec folder removed from `specs/doc-003-claude-code-marketplace-installation-path` after recovery commands were recorded |

DOC-003 is complete and archived. The canonical Claude install route remains
`docs-site/src/content/docs/install/claude-code.md`.
