# SpecKit Workflow: DOC-004 - Codex marketplace installation path

**Template Version**: 1.0.0
**Created**: 2026-06-14
**Purpose**: Prepare DOC-004 for autonomous execution after DOC-002 created the Astro/Starlight docs-site shell and Codex install route placeholder.

---

## How to Use This Template

1. Start autopilot with this file:

   ```bash
   $speckit-autopilot docs/ai/specs/.process/DOC-004-workflow.md
   ```

2. Keep `docs/ai/specs/.process/DOC-004-design-concept.md` open as the source of truth for the Grill Me decisions behind this scaffold.

3. Track phase status in the table below as autopilot advances.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during `$speckit-scaffold-spec DOC-004`.
The full Q&A log, Goals, Non-goals, and Open Questions live at:

```text
docs/ai/specs/.process/DOC-004-design-concept.md
```

Re-read it before each phase. The design concept is the source of truth for the accepted one-page Codex install route, separate repo/personal/CLI path matrix, custom-agent checklist, bounded trust guidance, official Codex docs refresh requirement, README/plugin README consistency scope, and full-validation bar.

> **Note:** Grill Me is human-in-the-loop only. It is not part of the autopilot loop. Once this workflow file is populated and autopilot begins, clarifications happen via `/speckit-clarify` and the consensus protocol.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | Complete | Created `spec.md` with 4 user stories, 19 FRs, 10 acceptance scenarios, and 0 clarification markers |
| Clarify | `/speckit-clarify` | Complete | 15 questions resolved across official path semantics, custom-agent registration, and scope/validation; 6 consensus items logged; G2 passed |
| Plan | `/speckit-plan` | Complete | Created plan.md, research.md, data-model.md, content contract, and quickstart without changing manifests, payloads, installer behavior, or agent templates |
| Checklist | `/speckit-checklist` | Complete | UX, accessibility, security, and error-handling checklists completed with 0 remaining gaps |
| Tasks | `/speckit-tasks` | Complete | Generated 20 docs-first tasks across setup, foundation, 4 user stories, and validation; G5 passed; reviewability tasks gate passes with warnings |
| Analyze | `/speckit-analyze` | Complete | 3 findings (0C/0H/2M/1L), all remediated; G6 passed |
| Implement | `/speckit-implement` | Complete | Docs-only Codex install guidance implemented; snippet review, accessibility review, docs checks, and full repo suite complete |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

Each phase requires human review and approval before proceeding:

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | User stories cover Codex install contexts, generated payload distinction, custom-agent registration, restart/verification, and bounded safety guidance |
| G2 | After Clarify | Official Codex path semantics, README/site consistency scope, agent checklist contents, and validation commands are explicit |
| G3 | After Plan | Docs architecture is concrete, official-source refresh is recorded, no forbidden plugin behavior changes are planned, and constitution gates pass |
| G4 | After Checklist | Requirement-quality gaps are fixed or explicitly deferred to DOC-007/DOC-008 |
| G5 | After Tasks | Tasks are docs-first, ordered, independently reviewable, and cover all AC-4.* acceptance criteria |
| G6 | After Analyze | No critical consistency drift remains between roadmap, PRD, Design Concept, spec, plan, and tasks |
| G7 | After Implementation | Docs-site validation, full repo suite, command-snippet review, and manual install-flow review are complete |

---

## Prerequisites

### Constitution Validation

Before starting any workflow phase, verify alignment with `.specify/memory/constitution.md`:

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Plugin Structure Compliance | DOC-004 must not change plugin structure, manifests, hooks, skills, agents, generated payloads, or marketplace behavior unless a small docs-contradiction source correction is explicitly justified. | `git diff --name-only` review before PR |
| Script Safety | No new scripts are expected. If a validation helper is touched, preserve `#!/usr/bin/env bash`, `set -euo pipefail`, quoted variables, and clear `jq` use. | `bash -n` on touched scripts plus targeted tests |
| Test Coverage Before Merge | User selected the full repo suite even though this is docs-first. | `bash tests/speckit-pro/run-all.sh` |
| KISS, Simplicity & YAGNI | Prefer one focused Codex install page plus README consistency edits. Do not create a multi-page reference system or broad troubleshooting matrix in DOC-004. | Plan Complexity Tracking plus code review |
| Conventional Commits | PR title must remain a conventional commit. | PR title check |

**Constitution Check:** Verify before G1.

### Scaffold Preflight Evidence

| Check | Result | Notes |
|-------|--------|-------|
| `specify` CLI | Passed | Available on `PATH` as `specify` |
| Technical roadmap | Found | `docs/ai/specs/interactive-documentation-technical-roadmap.md` |
| DOC-004 status | Ready | Roadmap lists DOC-004 as pending/ready; DOC-002 completed and archived |
| Open PR duplicate check | Passed | `gh pr list --state open --search "DOC-004"` returned no open PRs |
| Branch/worktree reuse check | Passed | No local or remote DOC-004 branch/worktree existed before setup |
| Reviewability setup gate | Passed | `reviewability-gate.sh setup docs/ai/specs/interactive-documentation-technical-roadmap.md` returned `status=pass`, projected 395 reviewable LOC, 0 production files, 6 total files |
| Reviewability preset | Installed | `.specify/presets/speckit-pro-reviewability` refreshed; `plan-template` changed |
| Preset resolution | Passed | `spec-template`, `plan-template`, and `tasks-template` resolve to `speckit-pro-reviewability v1.0.0` |
| Slice-size advisory | OK | Grill Me estimate: 260 reviewable LOC, 1 suggested slice, `status=ok` |

### Project Commands

| Command | Purpose |
|---------|---------|
| `cd docs-site && pnpm validate` | Astro type/content check plus production build |
| `cd docs-site && pnpm validate:links` | Current DOC-002 link-validation hook; presently aliases production build |
| `bash tests/speckit-pro/run-all.sh` | Full repo/plugin validation requested during Grill Me Q7 |
| Manual command-snippet review | Confirm Codex marketplace, plugin, skills, subagents, approvals/security, and cache wording against refreshed official OpenAI docs |

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | DOC-004 |
| **Name** | Codex marketplace installation path |
| **Branch** | `doc-004-codex-marketplace-installation-path` |
| **Feature directory** | `specs/doc-004-codex-marketplace-installation-path` |
| **Design Concept** | `docs/ai/specs/.process/DOC-004-design-concept.md` |
| **Roadmap** | `docs/roadmap-interactive-documentation.md` and `docs/ai/specs/interactive-documentation-technical-roadmap.md` |
| **Dependencies** | DOC-002 completed and archived; consume existing `docs-site/` shell and `/install/codex` placeholder |
| **Enables** | DOC-005, DOC-007, and DOC-008 |
| **Priority** | P1 |
| **Reviewability estimate** | Setup gate pass; Grill Me forward estimate 260 LOC, suggested 1 slice, advisory ok |

### Success Criteria Summary

- [x] AC-4.1: The Codex path explains repo marketplace, personal marketplace, and `codex plugin marketplace add` options using current official terminology.
- [x] AC-4.2: The docs state that Codex loads installed plugins from cache and users should update the payload directory or marketplace source before expecting changes.
- [x] AC-4.3: The docs explain why `speckit-pro` has a Codex-only `install` skill for custom-agent TOML templates.
- [x] AC-4.4: The docs separate Codex skill metadata sidecars from custom-agent registration.
- [x] AC-4.5: The docs include sandbox, approval, and network-access implications for `speckit-pro` workflows.
- [x] AC-4.6: The docs validate and correct README personal-marketplace path wording against official Codex path-resolution behavior.

### Accepted Scope

- Expand `docs-site/src/content/docs/install/codex.md` from DOC-002 shell into the full DOC-004 Codex install page.
- Update `README.md` and `speckit-pro/README.md` together so root, plugin, and docs-site install guidance agree.
- Include separate repo-scoped, personal/local, and CLI install contexts.
- Keep generated Codex payload guidance explicit: use `dist/codex/speckit-pro/`, not the mixed source authoring tree.
- Include `@SpecKit Pro -> install`, `$install`, restart, and custom-agent TOML verification guidance.
- Keep trust/sandbox/approval/network guidance bounded to installation safety and link or defer deeper cases to DOC-008.
- Do not change Codex manifests, generated payloads, install scripts, custom-agent TOML files, marketplace behavior, release automation, or plugin runtime behavior.

---

## Phase 1: Specify

**When to run:** At the start of DOC-004. Output: `specs/doc-004-codex-marketplace-installation-path/spec.md`.

### Specify Prompt

```bash
/speckit-specify

## Feature: Codex marketplace installation path

### Problem Statement
Codex users need a precise, source-backed install path for Racecraft Public Plugins and `speckit-pro`. The current README and DOC-002 docs-site shell explain the broad idea, but users still have to resolve repo-scoped marketplace use, personal/local plugin layout, generated Codex payloads, installed cache behavior, `$install`, custom-agent registration, restart, and sandbox/approval implications from scattered sources.

### Users
- Codex users installing `speckit-pro` from this repository or a personal/local plugin layout.
- Existing `speckit-pro` users refreshing or repairing an install after marketplace/plugin updates.
- Maintainers keeping root README, plugin README, and docs-site install guidance consistent.
- Security/platform evaluators who need enough Codex-specific safety context to approve or reject installation.

### User Stories
- As a Codex user, I can choose the right repo-scoped, personal/local, or CLI marketplace path without confusing source tree, generated payload, and installed cache.
- As a Codex user, I can install `speckit-pro`, run the Codex install skill, restart Codex, and verify the expected custom-agent TOML files are registered.
- As a maintainer, I can keep `README.md`, `speckit-pro/README.md`, and the docs-site Codex page consistent after official-source validation.
- As a security-minded user, I can see the bounded sandbox, approvals, network, cache, and trust implications needed before first install, with deeper cases deferred to DOC-008.

### Functional Requirements Seed
- Explain `.agents/plugins/marketplace.json`, `speckit-pro/.codex-plugin/plugin.json`, `dist/codex/speckit-pro/.codex-plugin/plugin.json`, and the installed cache as distinct surfaces.
- Document repo-scoped marketplace use and personal/local plugin layout separately.
- Document `codex plugin marketplace add` only after refreshing official OpenAI Codex docs for current command/path semantics.
- State that personal/local installs should target the generated Codex payload root `dist/codex/speckit-pro/`, not the mixed authoring source tree `speckit-pro/`.
- Explain `@SpecKit Pro -> install` and `$install` as the Codex-only custom-agent registration step.
- Explain why skills ship with the plugin but custom agents must be copied into `.codex/agents/` or `~/.codex/agents/` by the install skill.
- List the expected installer-copied TOML custom-agent files from the current install skill and installer script. Do not list source-only TOML files such as `uat-runbook-author.toml` as expected installed output unless a later plan-approved source correction changes installer behavior.
- Tell users to restart Codex after custom-agent installation.
- Include bounded install-safety guidance for sandbox, approvals, and network access.
- Update `README.md`, `speckit-pro/README.md`, and `docs-site/src/content/docs/install/codex.md` so the three entry points do not contradict each other.
- Preserve cross-links to DOC-007/DOC-008-owned future reference and troubleshooting depth.

### Constraints
- Refresh official OpenAI Codex plugin, build-plugin, skills, subagents, and approvals/security docs before finalizing command/path wording.
- Do not change Codex manifests, marketplace files, generated payloads, install script behavior, custom-agent TOML templates, or release automation unless a tiny docs-contradiction source correction is explicitly approved in the plan.
- Keep Claude Code instructions out of DOC-004 except for cross-links to the DOC-003 path.
- Keep all changes documentation-only unless the spec/plan records a narrow exception.
- Run full repo validation plus docs-site validation before PR readiness.

### Out of Scope
- Claude Code install path content.
- Full troubleshooting matrix, update/rollback model, and complete trust/security reference.
- Live local install testing in CI.
- Browser-side config writes or local command execution.
- New interactive selector components.
- Plugin runtime behavior changes.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 19 |
| User Stories | 4 |
| Acceptance Criteria | AC-4.1 through AC-4.6 covered by FR-001 through FR-019 and SC-001 through SC-007 |

### Files Generated

- [x] `specs/doc-004-codex-marketplace-installation-path/spec.md`
- [x] `specs/doc-004-codex-marketplace-installation-path/checklists/requirements.md`

---

## Phase 2: Clarify

**When to run:** After Specify if any implementation boundary could be interpreted multiple ways. Maximum 5 targeted questions per session.

### Clarify Prompts

#### Session 1: Official Codex path semantics

```bash
/speckit-clarify Focus on official Codex path semantics: confirm current `codex plugin marketplace add` wording, repo-scoped marketplace behavior, personal/local plugin layout, generated payload path expectations, and installed cache terminology against refreshed official OpenAI docs.
```

#### Session 2: Custom-agent registration and verification

```bash
/speckit-clarify Focus on Codex custom-agent registration: confirm how the docs should explain plugin-shipped skills versus copied TOML custom agents, the `@SpecKit Pro -> install` / `$install` step, restart requirement, destination paths, expected file list, and what verification is safe to document without changing installer behavior.
```

#### Session 3: Scope, consistency, and validation

```bash
/speckit-clarify Focus on scope and validation: confirm README/plugin README/docs-site consistency rules, bounded trust guidance versus DOC-008 deferral, forbidden plugin behavior changes, docs-site validation commands, full repo suite requirement, and manual command-snippet review expectations.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Official Codex path semantics | 5 | Document HTTP/HTTPS Git URL support, `--json`, generated-payload copy/sync for personal installs, official installed plugin cache terminology, and skills-vs-custom-agents wording |
| 2 | Custom-agent registration and verification | 5 | Use the installer-copied TOML set for verification, default `$install` to `~/.codex/agents/`, distinguish skill metadata from custom-agent TOML registration, keep verification observational, and add a bounded outside-workspace approval warning |
| 3 | Scope, consistency, and validation | 5 | Keep shared critical invariants across all three entry points, bound trust guidance to install safety, forbid plugin behavior changes, require existing docs-site/full-suite validation commands, and record source-backed command-snippet review |

### Consensus Resolution Log

| # | Type | Question/Gap/Finding | Categories | Round | Outcome | Resolution | Analysts Used |
|---|------|----------------------|------------|-------|---------|------------|---------------|
| 1 | Clarify | `codex plugin marketplace add` source forms | [domain] | 1 | high-confidence | Updated FR-007 to include HTTP or HTTPS Git URLs, `--json`, `owner/repo`, `owner/repo@ref`, `--ref`, and repeatable Git-only `--sparse PATH` | domain-researcher |
| 2 | Clarify | Personal/local generated-payload layout | [codebase, domain, spec] | 1 | 3/3 | Updated Session 1 clarifications, User Story 1 scenario 2, FR-004, and FR-005 to use generated payload plus copy/sync for personal layouts | codebase-analyst, domain-researcher, spec-context-analyst |
| 3 | Clarify | Installed cache terminology | [codebase, domain] | 1 | both-agree | Updated Session 1 clarifications, User Story 1 cache wording, FR-005, edge cases, and assumptions to use official installed plugin cache terminology | codebase-analyst, domain-researcher |
| 4 | Clarify | Expected custom-agent TOML verification list | [codebase, spec] | 1 | both-agree | Updated Session 2 clarifications, User Story 2 scenario 3, FR-011, SC-003, edge cases, and assumptions to verify the installer-copied 9-file TOML set unless a plan-approved source correction changes installer behavior | codebase-analyst, spec-context-analyst |
| 5 | Clarify | `$install` permission and approval implications | [security] | 1 | 3/3 | Updated Session 2 clarifications and FR-013 with a bounded outside-workspace write warning, project-scoped destination option, network distinction, and DOC-008 deferral | codebase-analyst, spec-context-analyst, domain-researcher |
| 6 | Clarify | Install-safety boundary vs DOC-008 | [security] | 1 | 3/3 | Updated Session 3 clarifications, FR-001, FR-013, FR-017, SC-001, SC-005, and assumptions to keep DOC-004 bounded to first-install safety and defer full trust/security/lifecycle depth to DOC-008 | codebase-analyst, spec-context-analyst, domain-researcher |

---

## Phase 3: Plan

**When to run:** After the spec is finalized. Output: `specs/doc-004-codex-marketplace-installation-path/plan.md`.

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Docs framework: existing Astro/Starlight app under `docs-site/`.
- Authoring: Markdown/MDX content pages plus root Markdown README files.
- Package manager: `pnpm` scoped to `docs-site/`.
- Source evidence: refreshed official OpenAI Codex docs, `docs/prd-interactive-documentation.md`, `docs/roadmap-interactive-documentation.md`, `docs/ai/specs/interactive-documentation-technical-roadmap.md`, root README, plugin README, checked-in manifests, generated payload manifest, install skill, custom-agent TOML files, and Codex hook config.
- Runtime services: none.
- Data model: documentation-only route sections, install path matrix, command snippets, custom-agent checklist, and source-evidence notes.
- Validation: `cd docs-site && pnpm validate`, `cd docs-site && pnpm validate:links`, `bash tests/speckit-pro/run-all.sh`, and manual command-snippet review against refreshed official docs.

## Constraints
- Consume the DOC-002 docs-site shell; do not restructure site navigation beyond what DOC-004 needs.
- Keep one focused Codex install page in `docs-site/src/content/docs/install/codex.md`.
- Update README and `speckit-pro/README.md` for consistency because Grill Me Q6 selected "Update all docs now".
- Do not change manifests, payloads, installer behavior, agent TOML templates, release automation, or plugin runtime behavior.
- Keep trust guidance bounded to install safety; defer deep troubleshooting, update, rollback, cache forensics, and full trust model to DOC-008.
- Keep reference-library depth to DOC-007.

## Architecture Notes
- Structure the Codex page around the user's install decision: repo-scoped marketplace, personal/local plugin, or CLI marketplace path.
- Put generated payload guidance near the top: `dist/codex/speckit-pro/` is the installable Codex payload; `speckit-pro/` is the mixed authoring source tree.
- Include a custom-agent registration checklist after plugin install: run install skill, confirm TOML destination, restart Codex, and verify expected agent availability.
- Include a short safety block for sandbox, approvals, and network access, written as install expectations rather than broad security guarantees.
- Include source-evidence links/citations for official OpenAI Codex docs and local checked-in files.
- Treat any mismatch between the install skill prose and actual `speckit-pro/codex-agents/*.toml` contents as a docs/source evidence issue to resolve in spec or plan before implementation.
- Use concise task-first copy, not marketing copy.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Complete | Records official-source refresh, file operations, docs-only scope, reviewability budget, and validation commands |
| `research.md` | Complete | Captures official Codex docs refresh, CLI help evidence, path/cache terminology, and installer-copied TOML decision |
| `data-model.md` | Complete | Models documentation entry points, install paths, Codex surfaces, checklist objects, safety notice, and snippets |
| `contracts/` | Complete | Adds `contracts/codex-install-content-contract.md` for route sections, README invariants, snippet review, and verification list |
| `quickstart.md` | Complete | Defines manual docs verification, command-snippet review, and automated validation guide |

---

## Phase 4: Domain Checklists

**When to run:** After Plan. Use enriched prompts; do not run bare domains.

### Recommended Domains

| Domain | Why it applies |
|--------|----------------|
| UX | The install page must guide first-time Codex users through a task sequence without mixing repo, personal, CLI, payload, and cache concepts. |
| Accessibility | Public docs content must preserve keyboard-readable structure, heading order, link clarity, and copyable command context in the Starlight site. |
| Security | The page covers plugin trust, sandbox, approvals, network access, cache/source boundaries, and install targets. |
| Error-handling | Install/update/remove guidance must explain safe checkpoints and failure classes without becoming the full DOC-008 troubleshooting matrix. |

### Checklist Prompts

#### 1. UX Checklist

```bash
/speckit-checklist ux

Focus on DOC-004 Codex marketplace installation requirements:
- Repo-scoped, personal/local, and CLI install paths are distinguishable at a glance.
- Generated payload, authoring source tree, marketplace metadata, and installed cache are not conflated.
- The custom-agent install/restart/verify sequence is task-first and complete.
- README and docs-site entry points guide users to the same Codex path.
- Pay special attention to: whether a first-time Codex user can choose the right path without reading Claude Code instructions.
```

#### 2. Accessibility Checklist

```bash
/speckit-checklist accessibility

Focus on DOC-004 Codex install docs:
- Headings, lists, tables, and command blocks have clear labels and navigable structure.
- Links describe their destination and do not rely on surrounding prose alone.
- Command snippets are grouped with platform and scope context.
- Safety warnings are text-visible and not color-only.
- Pay special attention to: install path matrix readability on mobile and screen-reader-friendly table alternatives if needed.
```

#### 3. Security Checklist

```bash
/speckit-checklist security

Focus on DOC-004 Codex install trust boundaries:
- Docs distinguish repository source, generated payload, installed cache, plugin skills, custom agents, hooks, sandbox, approvals, and network access.
- Docs avoid promising silent autonomous access or bypassing Codex approvals.
- Docs clearly warn against installing the mixed source tree as a personal Codex plugin.
- Docs cite refreshed official OpenAI sources for Codex approvals/security claims.
- Pay special attention to: bounded safety guidance versus claims that belong to DOC-008.
```

#### 4. Error-Handling Checklist

```bash
/speckit-checklist error-handling

Focus on DOC-004 install/update/remove checkpoints:
- Docs state what users should check when the plugin appears stale after update.
- Docs explain when to rerun `$install` and restart Codex after agent updates.
- Docs mention cache/source mismatch symptoms without duplicating DOC-008 troubleshooting depth.
- Docs provide clear next links for deeper troubleshooting.
- Pay special attention to: personal marketplace path examples and generated-payload path wording.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| UX | 22 | 0 | spec.md, plan.md, data-model.md, contract, quickstart |
| Accessibility | 19 | 6 remediated; 0 remain | Added semantic structure, matrix fallback, table labeling, descriptive-link, command-context, and text-visible safety-warning requirements |
| Security | 22 | 1 remediated; 0 remain | Added bounded lifecycle hook payload awareness to spec, plan, research, data model, contract, and quickstart; DOC-008 retains hook trust/policy depth |
| Error-handling | 18 | 4 remediated; 0 remain | Added bounded stale-after-update checkpoint requirements, cache/source mismatch symptoms, `$install` rerun plus restart trigger for custom-agent updates, and DOC-007/DOC-008 next-link requirements |

---

## Phase 5: Tasks

**When to run:** After checklists complete and all real gaps are resolved. Output: `specs/doc-004-codex-marketplace-installation-path/tasks.md`.

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Small docs-first chunks, each independently reviewable.
- Clear acceptance criteria referencing AC-4.1 through AC-4.6 and FR markers.
- Dependency ordering: source refresh -> source evidence audit -> spec/plan contract updates -> docs implementation -> consistency pass -> validation.
- Mark parallel-safe tasks with [P] only when they do not modify the same Markdown page or source-evidence section.
- Organize by user story, not by technical layer.

## Implementation Phases
1. Foundation and source refresh
   - Refresh official OpenAI Codex docs.
   - Audit local source files: root README, plugin README, `.agents/plugins/marketplace.json`, source and dist Codex manifests, install skill, `codex-agents/*.toml`, and `codex-hooks.json`.
2. User Story 1: install path selection
   - Build the repo/personal/CLI install path matrix.
   - Explain source tree, generated payload, marketplace metadata, and installed cache.
3. User Story 2: custom-agent registration
   - Document `@SpecKit Pro -> install`, `$install`, restart, expected TOML files, and safe verification.
4. User Story 3: docs consistency
   - Update `README.md`, `speckit-pro/README.md`, and `docs-site/src/content/docs/install/codex.md` so they agree.
5. Polish and validation
   - Add bounded sandbox/approval/network guidance.
   - Run docs-site validation, full repo suite, manual command-snippet review, and final source-vs-generated-payload diff review.

## Constraints
- Do not change Codex manifests, generated payloads, installer behavior, custom-agent TOML templates, release automation, or plugin runtime behavior.
- Do not create a broad troubleshooting matrix or reference library; link forward to DOC-007/DOC-008.
- Keep Claude commands out of the Codex install path except for explicit cross-links to the Claude page.
- Preserve existing docs-site Astro/Starlight conventions and route paths.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| Total Tasks | 20 |
| Phases | 7 |
| Parallel Opportunities | 2 `[P]` tasks (`T010`, `T011`) plus review work that may be parallelized after implementation with one final evidence update |
| User Stories Covered | 4 (`US1` install path selection, `US2` custom-agent registration, `US3` consistency, `US4` install safety) |
| Marker Coverage | AC-4.1 through AC-4.6, FR-001 through FR-019, and SC-001 through SC-007 are mapped in `tasks.md` |
| G5 Gate | Pass: `bash speckit-pro/skills/speckit-autopilot/scripts/validate-gate.sh G5 specs/doc-004-codex-marketplace-installation-path` returned `task_count=20` |
| Task Format Check | Pass: local parser found 20 sequential tasks, 2 `[P]`, and all required FR/AC/SC markers |
| Reviewability Tasks Gate | Warn/pass: `reviewability-gate.sh tasks` projected 800 reviewable LOC, 1 production file token, 25 total file tokens, and no blockers |
| Spec Index | Pass after regeneration: `generate-spec-index.sh --check .` reports in-scope maps current |
| Prerequisites | Pass with explicit numeric feature override: `SPECIFY_FEATURE=004-doc-004-codex-marketplace-installation-path .specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks`; bare command rejects the non-numeric DOC branch name |

---

## Atomicity Route

Fill after the Tasks phase / G5. Run:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/doc-004-codex-marketplace-installation-path
```

| Field | Value | Meaning |
|-------|-------|---------|
| Route | `one-navigable-PR` | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope` |
| Releasable | `true` | `true` or `false` |
| Signals | `change-shape:modify-heavy` | Decisive detector findings |
| Hints | None | Advisory detector hints |
| Warnings | None | Release-safety warnings |

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch issues.

### Analyze Prompt

```bash
/speckit-analyze

Focus on:
1. Design Concept drift: verify the plan and tasks preserve one focused Codex page, all-docs consistency updates, bounded safety guidance, official-doc refresh, and full validation.
2. Source freshness: verify official OpenAI Codex docs are refreshed before final command/path wording and that current terminology is cited.
3. Platform leakage: ensure Claude Code commands do not appear as Codex instructions and Codex `$skill` syntax is not rewritten as Claude slash commands.
4. Source/payload/cache consistency: ensure `speckit-pro/`, `dist/codex/speckit-pro/`, `.agents/plugins/marketplace.json`, `.codex-plugin/plugin.json`, and installed cache are distinct.
5. Custom-agent checklist coverage: ensure the expected TOML files, install skill, destination paths, restart requirement, and verification are covered without changing installer behavior.
6. Validation coverage: ensure docs-site validation, full repo suite, and manual command-snippet review are explicit tasks.
```

### Analyze Severity Levels

| Severity | Meaning | Action Required |
|----------|---------|-----------------|
| CRITICAL | Blocks implementation or violates constitution | Must fix before G6 gate |
| HIGH | Significant gap, impacts quality | Should fix |
| MEDIUM | Improvement opportunity | Review and decide |
| LOW | Minor inconsistency | Note for future |

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| A1 | MEDIUM | `tasks.md` referenced most success criteria in task prose but the formal Requirement Coverage table only mapped SC-006 and SC-007, and SC-002 appeared only in a checkpoint. | Added SC-002 to T005/T006 and expanded the Requirement Coverage table to map SC-001 through SC-007 explicitly. |
| A2 | MEDIUM | The command-snippet contract did not explicitly cover every FR-007 marketplace source form, especially `owner/repo@ref` and SSH Git URLs. | Added missing CLI source-form rows to the content contract and tightened T006/T017 so implementation review covers `owner/repo@ref`, SSH Git URLs, repeatable Git-only `--sparse`, and `--json`. |
| A3 | LOW | The historical Specify prompt seed still asked for source TOML files including `uat-runbook-author.toml`, which drifted from the clarified nine installer-copied expected installed files. | Updated the workflow seed to say DOC-004 must list installer-copied TOML files and must not list source-only TOML files as expected installed output without a plan-approved source correction. |

**G6 Validation**: `bash speckit-pro/skills/speckit-autopilot/scripts/count-markers.sh findings specs/doc-004-codex-marketplace-installation-path` and `bash speckit-pro/skills/speckit-autopilot/scripts/validate-gate.sh G6 specs/doc-004-codex-marketplace-installation-path` both pass after remediation.

📊 Confidence: 0.96

- Task understanding: 0.95
- Approach clarity: 0.92
- Requirements alignment: 0.94
- Risk assessment: 1.00
- Completeness: 1.00

**G6.5 Confidence Gate**: Pass: `bash speckit-pro/skills/speckit-autopilot/scripts/confidence-gate.sh docs/ai/specs/.process/DOC-004-workflow.md --threshold 0.90 --mode advisory` returned composite `0.96`, threshold `0.90`, recommendation `proceed`.

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed with no unresolved blocking findings.

### Implement Prompt

```bash
/speckit-implement

## Approach: Docs-First, Source-Backed

For each task, follow this cycle:

1. READ: Re-open the relevant official source, local source file, and Design Concept entry.
2. EDIT: Make the smallest Markdown/content change that satisfies the task.
3. CHECK: Verify the command/path/source claim still matches official docs and checked-in files.
4. VALIDATE: Run the relevant docs-site or repo check before marking the task complete.

### Pre-Implementation Setup

1. Verify branch:
   `git rev-parse --abbrev-ref HEAD`
2. Verify clean starting state except scaffold artifacts:
   `git status --short`
3. Refresh official OpenAI Codex docs for plugins, build plugins, skills, subagents, and approvals/security.
4. Audit local sources:
   - `README.md`
   - `speckit-pro/README.md`
   - `docs-site/src/content/docs/install/codex.md`
   - `.agents/plugins/marketplace.json`
   - `speckit-pro/.codex-plugin/plugin.json`
   - `dist/codex/speckit-pro/.codex-plugin/plugin.json`
   - `speckit-pro/codex-skills/install/SKILL.md`
   - `speckit-pro/codex-agents/*.toml`
   - `speckit-pro/codex-hooks.json`

### Implementation Notes

- Keep Codex docs in Codex syntax: `$install`, `$speckit-*`, and `@SpecKit Pro -> install` where appropriate.
- Keep generated payload guidance explicit: personal/local installs point at `dist/codex/speckit-pro/`.
- Do not edit `dist/**`, manifests, custom-agent TOML files, or installer scripts unless the plan records an explicit exception.
- If official docs contradict existing README guidance, update README, plugin README, and docs-site content together.
- Keep the trust block bounded: sandbox, approvals, network, cache/source distinction, and deeper DOC-008 link.

### Required Verification

1. `cd docs-site && pnpm validate`
2. `cd docs-site && pnpm validate:links`
3. `bash tests/speckit-pro/run-all.sh`
4. Manual review: every Codex command/path snippet is checked against refreshed official docs or local source files.
5. Manual review: `git diff --name-only` contains docs/spec artifacts only unless a plan-approved exception exists.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| Foundation and source refresh | T001-T003 | Complete | OpenAI Codex manual, local CLI help, repo marketplace, source/dist manifests, install skill/script, TOML source set, and hook payloads refreshed; no non-docs source correction required. |
| Install path selection | T004-T007 | Complete | DOC-002 shell replaced with task-first DOC-004 outline; accessible matrix, compact list, CLI source forms, generated-payload warning, installed cache behavior, and bounded stale-update checkpoint are implemented. |
| Custom-agent registration | T008-T009 | Complete | Added Codex-only install checklist, exact nine installer-copied TOML files, skill metadata sidecar distinction, observational verification, no manual cache or TOML edits, and restart/rerun triggers. |
| Docs consistency | T010-T013 | Complete | README, plugin README, and docs-site Codex guide now share repo marketplace, generated payload, installed cache, install skill, restart, nine-file verification, stale-update, safety, and DOC-003/DOC-007/DOC-008 boundary guidance. |
| Install safety | T014-T016 | Complete | Added text-visible sandbox, approval, network, cache/source, destination, outside-workspace, hook-payload, external-auth, and DOC-008 deferral guidance; focused forbidden-claim check passes. |
| Polish and validation | T017-T020 | Complete | Source-backed command/path snippet review, accessibility review, docs-site validation, full repo suite, generated-dist README sync, and PR evidence recorded. |

### Phase 7 Evidence

#### T017 Command And Path Snippet Review

Result: Pass. No README or docs-site copy changes were required.

Sources re-opened for the Phase 7 review:

- Official OpenAI Codex docs: Plugins, Build plugins, Skills, Subagents, Permissions, and Agent approvals and security.
- Local CLI help: `codex plugin marketplace add --help`.
- Checked-in source: `README.md`, `speckit-pro/README.md`, `docs-site/src/content/docs/install/codex.md`, `.agents/plugins/marketplace.json`, `speckit-pro/.codex-plugin/plugin.json`, `dist/codex/speckit-pro/.codex-plugin/plugin.json`, `speckit-pro/codex-skills/install/SKILL.md`, `speckit-pro/codex-skills/install/scripts/install-codex-agents.sh`, `speckit-pro/codex-agents/*.toml`, and `speckit-pro/codex-hooks.json`.

Checklist:

| Snippet group | Evidence | Result |
|---------------|----------|--------|
| `codex` then `/plugins` | OpenAI Plugins docs; README, plugin README, and docs-site all use the Codex plugin browser path only for Codex. | Pass |
| `codex plugin marketplace add` examples | OpenAI Build plugins docs and local CLI help confirm local paths, `owner/repo`, `owner/repo@ref`, HTTP/HTTPS Git URLs, SSH Git URLs, `--ref`, repeatable Git-only `--sparse PATH`, and `--json`. | Pass |
| `.agents/plugins/marketplace.json`, `~/.agents/plugins/marketplace.json`, and `source.path` | OpenAI Build plugins docs plus repo marketplace source confirm repo and personal marketplace wording; local repo entry points `speckit-pro` at `./dist/codex/speckit-pro`. | Pass |
| `dist/codex/speckit-pro/`, `speckit-pro/`, and plugin manifests | Source and generated Codex manifests confirm source uses `./codex-skills/`, generated payload uses `./skills/`, and `speckit-pro/` is not the installable Codex payload. | Pass |
| `~/.codex/plugins/speckit-pro/` and `~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/` | OpenAI Build plugins docs confirm personal plugin layout examples, installed plugin cache terminology, and restart/update guidance. | Pass |
| `@SpecKit Pro -> install`, `$install`, `.codex/agents/`, and `~/.codex/agents/` | Local plugin manifest default prompt, install skill, installer script, and OpenAI Subagents docs confirm custom-agent registration and destination wording. | Pass |
| Nine expected TOML filenames | Install skill and installer script both copy/verify exactly `autopilot-fast-helper.toml`, `phase-executor.toml`, `clarify-executor.toml`, `checklist-executor.toml`, `analyze-executor.toml`, `implement-executor.toml`, `codebase-analyst.toml`, `spec-context-analyst.toml`, and `domain-researcher.toml`; `uat-runbook-author.toml` remains source-only for DOC-004 expected output. | Pass |
| `codex-hooks.json`, sandbox, approvals, and network wording | Source and generated manifests reference `codex-hooks.json`; OpenAI Plugins, Permissions, and Agent approvals/security docs support bounded safety language without claiming approval, sandbox, hook-trust, network, or authentication bypass. | Pass |

#### T018 Accessibility Review

Result: Pass. `docs-site/src/content/docs/install/codex.md` uses semantic section headings for the install decision, source/payload/cache model, install matrix, compact path list, marketplace install, custom-agent registration, verification, stale-update checkpoint, install safety, and source evidence. Links are descriptive, command blocks are introduced with Codex platform and install-scope context, procedures and TOML inventories use lists, the install-safety warning is visible text, and the dense matrix has a compact list alternative for mobile and screen-reader use.

#### T019 Docs-Site Validation

| Command | Result |
|---------|--------|
| `cd docs-site && pnpm validate` | Pass. `astro check` reported 0 errors, 0 warnings, and 0 hints across 3 files; production build generated 12 pages; internal links were valid. |
| `cd docs-site && pnpm validate:links` | Pass. Current DOC-002 link hook ran `pnpm build`; production build generated 12 pages; internal links were valid. |

#### T020 Full Suite And PR Evidence

| Check | Result |
|-------|--------|
| `bash tests/speckit-pro/run-all.sh` | Pass: `2947/2947` passed (`L1 551/551`, Codex L1 `430/430`, `L4 1776/1776`, `L5 190/190`). |
| Generated-dist README sync | CI requires generated payload README files to be current with the source README. `dist/claude/speckit-pro/README.md` and `dist/codex/speckit-pro/README.md` were synced after the first PR check failed `validate-plugin-payload`; no manifests, installer behavior, custom-agent TOML templates, hooks, marketplace behavior, release automation, or runtime code changed. |
| Scope review | Final intended diff is limited to `docs/ai/specs/.process/DOC-004-workflow.md` and `specs/doc-004-codex-marketplace-installation-path/tasks.md` for Phase 7 evidence and task completion. |

PR evidence prepared from `spec.md`, `plan.md`, `tasks.md`, and validation outputs:

- Summary: DOC-004 provides a source-backed Codex install path across the docs-site Codex page, root README, and SpecKit Pro README.
- Why: Codex users need separate repo-scoped, personal/local, and CLI marketplace paths without conflating source, generated payload, installed cache, skills, and custom-agent TOML registration.
- Non-goals: no manifest, generated payload behavior, installer behavior, custom-agent TOML template, hook, release automation, marketplace behavior, or runtime changes. Generated dist README files are synced only because CI enforces current generated payload documentation.
- Review order: review `docs-site/src/content/docs/install/codex.md` first, then README alignment, then SpecKit artifacts and validation evidence.
- Traceability: AC-4.1 through AC-4.6 and FR-001 through FR-019 are mapped in `tasks.md`; Phase 7 validates FR-017, FR-018, SC-005, and SC-006.
- Validation: `pnpm validate`, `pnpm validate:links`, and `bash tests/speckit-pro/run-all.sh` all passed.
- Known gaps: deeper command reference remains DOC-007; trust, troubleshooting, update, remove, rollback, stale-cache forensics, and full security lifecycle remain DOC-008.
- Rollback: documentation/process-only revert; no feature flag, migration, or runtime rollback required.

---

## Post-Implementation Checklist

- [x] All tasks marked complete in tasks.md.
- [x] `docs-site/src/content/docs/install/codex.md` satisfies DOC-004 page scope.
- [x] `README.md` and `speckit-pro/README.md` agree with docs-site Codex install guidance.
- [x] Official OpenAI Codex docs refresh is cited in `research.md` or the relevant implementation evidence.
- [x] No unintended changes to manifests, installer scripts, custom-agent TOML templates, hooks, marketplace behavior, release automation, or plugin runtime behavior; generated dist README files are synced because CI enforces current generated payload documentation.
- [x] `$speckit-doctor` equivalent extension check passes: 5 pass, 0 warn, 0 fail.
- [x] `$speckit-verify` equivalent implementation check passes: 0 critical, 0 high, 0 medium, 0 low findings; 20/20 tasks complete; 19/19 requirements covered.
- [x] `$speckit-verify-tasks` equivalent phantom-task check passes with 20 verified, 0 partial, 0 weak, 0 not found, 0 skipped; report written to `specs/doc-004-codex-marketplace-installation-path/verify-tasks-report.md`.
- [x] `$speckit-review` skipped because the review extension is not installed in `.specify/extensions/.registry`.
- [x] `cd docs-site && pnpm validate` passes.
- [x] `cd docs-site && pnpm validate:links` passes.
- [x] `bash tests/speckit-pro/run-all.sh` passes.
- [x] `$speckit-cleanup` skipped because the cleanup extension is not installed in `.specify/extensions/.registry`.
- [x] Manual command-snippet review complete.
- [x] Final reviewability backstop complete.
- [x] PR packet/body generated and validated.
- [x] PR created.
- [x] Review remediation checked.
- [x] Retrospective complete.

### Post-Implementation Evidence

| Item | Result | Evidence |
|------|--------|----------|
| Doctor extension check | Pass | Templates, agent config, scripts, constitution, and DOC-004 artifacts all present; worktree remained clean. |
| Verify implementation | Pass | 0 critical/high/medium/low findings; 20/20 tasks complete; 19/19 requirements covered; docs-only constitution scope clean. |
| Verify tasks phantom check | Pass | 20 verified, 0 partial, 0 weak, 0 not found, 0 skipped; no flagged items. |
| Integration suite | Pass | `cd docs-site && pnpm validate`, `cd docs-site && pnpm validate:links`, and `bash tests/speckit-pro/run-all.sh` all passed; full suite reported `2947/2947`. |
| Review extension | Skipped | Review extension is not installed. |
| Cleanup extension | Skipped | Cleanup extension is not installed. |
| Final reviewability backstop | Warn/pass | `final-reviewability-backstop.sh` completed with `status=warn`, `blocked_operations=[]`, `reviewable_loc=0`, `production_files=0`, `total_files=25`, and `primary_surface_count=4`; warning evidence is recorded in `specs/doc-004-codex-marketplace-installation-path/.process/final-reviewability/gate-state.json`. |
| PR packet/body generation | Pass | `generate-pr-body.sh` produced a single-PR packet and DOC-004 reviewer body; `validate-pr-packet.sh` passed with `title_value=feat(speckit-pro): Add codex marketplace installation path`, `base_branch=main`, `head_branch=doc-004-codex-marketplace-installation-path`, and `pr_blocked=false`. The packet/body were kept transient for PR creation rather than committed to the branch. |
| PR creation | Pass | Created ready PR #186: `https://github.com/racecraft-lab/racecraft-plugins-public/pull/186`. Initial PR checks found stale generated payload README files, so the branch now includes the CI-required generated dist README sync. |
| Review remediation | Pass | Addressed Copilot comments by setting DOC-004 `SPEC-MOC.md` status to `in-progress`, refreshing the technical roadmap date to 2026-06-15, correcting `phase1.functional_requirements` to enumerate FR-001 through FR-019, regenerating the spec index, and rerunning `bash tests/speckit-pro/run-all.sh` with `2947/2947` passing. |
| Retrospective | Pass | `specs/doc-004-codex-marketplace-installation-path/retrospective.md` records 100% task completion, 100% spec adherence, 0 critical findings, and no proposed spec changes. |

---

## Project Structure Reference

```text
racecraft-plugins-public/
|-- README.md
|-- .agents/plugins/marketplace.json
|-- docs-site/
|   |-- package.json
|   `-- src/content/docs/install/codex.md
|-- docs/
|   |-- prd-interactive-documentation.md
|   |-- roadmap-interactive-documentation.md
|   `-- ai/specs/
|       |-- interactive-documentation-technical-roadmap.md
|       `-- .process/DOC-004-design-concept.md
|-- speckit-pro/
|   |-- README.md
|   |-- .codex-plugin/plugin.json
|   |-- codex-skills/install/SKILL.md
|   |-- codex-agents/*.toml
|   `-- codex-hooks.json
|-- dist/codex/speckit-pro/
|   `-- .codex-plugin/plugin.json
|-- specs/doc-004-codex-marketplace-installation-path/
|   `-- SPEC-MOC.md
`-- tests/speckit-pro/
```

---

## Lessons Learned

### What Worked Well

- Keeping the source-backed snippet checklist grouped by command/path family made the final review practical without duplicating the full docs page.
- Running the full suite and PR checks exposed generated dist README drift; syncing generated README files is required when source README install guidance changes.

### Challenges Encountered

- Initial local validation restored generated payload README files, but CI correctly required them to remain current with the source README. The generated changes were reviewed and committed as documentation-only payload sync.

### Patterns to Reuse

- Record validation-induced generated payload README sync explicitly in the workflow when a docs-only task changes README content that is copied into generated plugin payloads.
- Keep the detailed install guide as the source of truth and keep README surfaces concise but invariant-compatible.

---

## Post-Merge Archive

| Item | Result |
|------|--------|
| PR | #186 `docs(DOC-004): add Codex marketplace installation path` |
| Merge commit | `bc48441c494d34a7df9876c3bdebabc4db8408a5` |
| Merged at | 2026-06-15T20:40:39Z |
| Archive report | `.specify/memory/archive-reports/2026-06-15-doc-003-004-post-merge-hygiene.md` |
| Cleanup | Active spec folder removed from `specs/doc-004-codex-marketplace-installation-path` after recovery commands were recorded |

DOC-004 is complete and archived. The canonical Codex install route remains
`docs-site/src/content/docs/install/codex.md`.
