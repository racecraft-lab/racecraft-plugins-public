# SpecKit Workflow: DOC-008 - Troubleshooting, security, trust, update, rollback

**Template Version**: 1.0.0
**Created**: 2026-06-18
**Purpose**: Prepare DOC-008 for autonomous execution after DOC-007 completed the generated reference library needed by troubleshooting, security, and update/rollback content.

---

## How to Use This Template

1. Start autopilot with this file:

   ```bash
   $speckit-autopilot docs/ai/specs/.process/DOC-008-workflow.md
   ```

2. Keep `docs/ai/specs/.process/DOC-008-design-concept.md` open as the source of truth for the Grill Me decisions behind this scaffold.

3. Track phase status in the table below as autopilot advances.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during `$speckit-scaffold-spec DOC-008`.
The full Q&A log, Goals, Non-goals, and Open Questions live at:

```text
docs/ai/specs/.process/DOC-008-design-concept.md
```

Re-read it before each phase. The design concept is the source of truth for the
three-page DOC-008 IA, symptom-matrix troubleshooting model, fact-bound trust
model, procedural update/rollback depth, shared platform-labeled rows, source
policy, one-slice decision, and validation scope.

> **Note:** Grill Me is human-in-the-loop only. It is not part of the autopilot
> loop. Once this workflow file is populated and autopilot begins,
> clarifications happen via `$speckit-clarify` and the consensus protocol.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `$speckit-specify` | Complete | Created `spec.md`; G1 passed with 0 clarification markers |
| Clarify | `$speckit-clarify` | Complete | G2 passed; route slug, source-link policy, row taxonomy, and update/rollback boundaries are explicit |
| Plan | `$speckit-plan` | Complete | G3 passed; plan keeps DOC-008 docs-only with no plugin behavior changes |
| Checklist | `$speckit-checklist` | Complete | Completed UX, security, error handling, and accessibility; 6 gaps found and fixed; G4 marker count clean |
| Tasks | `$speckit-tasks` | Complete | Generated 40 story-ordered docs tasks with source citation checks; G5 passed |
| Analyze | `$speckit-analyze` | Complete | Remediated AC traceability drift; G6 marker count clean |
| Implement | `$speckit-implement` | Complete | Expanded DOC-008 pages, updated sidebar/links, ran docs validation bundle; G7 passed |

**Status Legend:** Pending | In Progress | Complete | Blocked

### Phase Gates

Each phase requires human review and approval before proceeding:

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | User stories cover troubleshooting, security/trust, and update/rollback; no local execution or security-audit scope creep |
| G2 | After Clarify | Route slug, matrix columns, source policy, platform labeling, and recovery boundaries are explicit |
| G3 | After Plan | Architecture stays docs-only, source citations are feasible, and constitution gates pass |
| G4 | After Checklist | UX, security, error-handling, and accessibility gaps are fixed or intentionally deferred |
| G5 | After Tasks | Tasks are story-ordered, independently reviewable, and include validation for docs build, links, and source references |
| G6 | After Analyze | No critical drift remains between roadmap, design concept, spec, plan, tasks, and validation plan |
| G7 | After Implementation | Docs validation bundle passes and no plugin behavior, manifests, hooks, payloads, release automation, or CI behavior changed |

---

## Prerequisites

### Constitution Validation

Before starting any workflow phase, verify alignment with `.specify/memory/constitution.md`:

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| Plugin Structure Compliance | DOC-008 may cite plugin manifests, hooks, skills, agents, docs, and generated reference pages, but must not change plugin behavior, generated payload semantics, marketplace behavior, install flow, release automation, or CI behavior. | `git diff --name-only` review before PR |
| Script Safety | No new shell scripts are expected. If a small docs validation helper becomes necessary, keep it deterministic, local-file-only, and consistent with existing docs-site tooling. | `bash -n` on touched shell scripts if any are added or changed |
| Test Coverage Before Merge | Docs-site validation, link validation, and source-reference review are required. Layer 1 is required only if plugin/source reference or payload paths are touched. | `pnpm --dir docs-site validate`; `pnpm --dir docs-site validate:links`; optional `bash tests/speckit-pro/run-all.sh --layer 1` |
| KISS, Simplicity & YAGNI | Use existing Starlight pages and generated DOC-007 reference pages. Do not add a live doctor command, a reusable diagnostics engine, or broad DOC-010 CI hardening. | Plan complexity tracking plus code review |
| Conventional Commits | PR title must remain public-readable Conventional Commit text. | PR title check |

**Constitution Check:** Run during autopilot preflight before G1.

### Scaffold Preflight Evidence

| Check | Result | Notes |
|-------|--------|-------|
| `specify` CLI | Passed | `specify 0.10.3.dev0` available before setup |
| Technical roadmap | Found | `docs/ai/specs/interactive-documentation-technical-roadmap.md` |
| DOC-008 status | Ready | Roadmap lists DOC-008 ready after DOC-007 completed in PR #208 |
| Branch/worktree reuse check | Passed | No local or remote DOC-008 branch existed before setup |
| Worktree | Created | `.worktrees/doc-008-troubleshooting-security-trust-update-rollback` |
| Reviewability setup gate | Passed | `status=pass`, 395 reviewable LOC, 0 production files, 6 total files, docs/process primary surface |
| Reviewability preset | Installed | `.specify/presets/speckit-pro-reviewability` refreshed and verified; no preset changes are required in this scaffold commit |
| Preset resolution | Passed | `spec-template`, `plan-template`, and `tasks-template` resolve to `speckit-pro-reviewability v1.0.0` |
| Slice-size advisory | OK | Grill Me estimate: 202 reviewable LOC, 1 suggested slice, `status=ok` |

### Project Commands

| Command | Purpose |
|---------|---------|
| `pnpm --dir docs-site reference:check` | Confirm generated DOC-007 reference pages remain current |
| `pnpm --dir docs-site validate` | Reference freshness check plus Astro content/type check and production build |
| `pnpm --dir docs-site validate:links` | Docs-site link-validation hook |
| `bash tests/speckit-pro/run-all.sh --layer 1` | Structural safety only if plugin/spec surfaces, scripts, manifests, or generated payload paths are touched |
| `bash tests/speckit-pro/run-all.sh` | Full plugin validation only if implementation unexpectedly touches plugin behavior, generated payload semantics, manifests, hooks, scripts, or tests |

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | DOC-008 |
| **Name** | Troubleshooting, security, trust, update, rollback |
| **Branch** | `doc-008-troubleshooting-security-trust-update-rollback` |
| **Feature directory** | `specs/doc-008-troubleshooting-security-trust-update-rollback` |
| **Design Concept** | `docs/ai/specs/.process/DOC-008-design-concept.md` |
| **Technical Roadmap** | `docs/ai/specs/interactive-documentation-technical-roadmap.md` |
| **Prompt Roadmap** | `docs/roadmap-interactive-documentation.md` |
| **Source PRD** | `docs/prd-interactive-documentation.md` |
| **Dependencies** | DOC-003, DOC-004, DOC-007 |
| **Enables** | DOC-010 |
| **Priority** | P1 |

### Roadmap Scope Summary

DOC-008 provides user-facing troubleshooting and security/trust documentation for
Claude Code and Codex install, path, cache, permission, version, CLI, and custom-agent
issues. It also adds update/remove/rollback guidance. The Grill Me interview
refined this to three pages: troubleshooting, security/trust, and a new top-level
update/rollback route, all using shared platform-labeled entries and source-backed
claims.

### Accepted Scope

- Expand `docs-site/src/content/docs/troubleshooting.md` into a symptom matrix with platform labels, likely causes, diagnostic commands/files, recommended fixes, and links to install/reference pages.
- Expand `docs-site/src/content/docs/security-and-trust.md` into a fact-bound trust model separating official vendor behavior, checked-in repository facts, and recommended practice.
- Add a top-level update/rollback route, recommended default `docs-site/src/content/docs/update-and-rollback.md`, linked from install, troubleshooting, and security/trust pages.
- Use existing DOC-007 generated reference pages for source-vs-dist, manifests, hooks, agents, and skills evidence.
- Cite official vendor docs for platform behavior and repository files or generated reference pages for repo-specific behavior.
- Keep Claude Code and Codex differences visible with shared rows and explicit platform labels.

### Out of Scope

- Security audit, certification, formal threat model, or control attestation.
- Live diagnostics command, browser-side shell execution, or automatic local config repair.
- Plugin behavior, manifest semantics, hooks, generated payloads, marketplace behavior, release automation, or CI behavior changes.
- Full contributor/release workflow content owned by DOC-009.
- Search, accessibility hardening across the whole site, deep-link conventions, and docs CI hardening owned by DOC-010.

### Success Criteria Summary

- [ ] AC-8.1: Troubleshooting entries include symptom, likely cause, diagnostic command or file to inspect, and recommended fix.
- [ ] AC-8.2: Security docs explain what a plugin can package on Claude and Codex: skills, agents/subagents, hooks, MCP config, settings/assets where applicable.
- [ ] AC-8.3: Trust model distinguishes repository source, generated payloads, installed cache, user/project agents, and managed-policy controls.
- [ ] AC-8.4: Update/rollback docs cover marketplace refresh, payload rebuild, version sync, and stale install/cache cases.
- [ ] AC-8.5: Docs explicitly state that browser docs do not grant permissions or run local plugin workflows.
- [ ] AC-8.6: Security/evaluator pages cite official vendor docs and label repository-derived behavior separately.

### Key Source Files

- `docs-site/src/content/docs/troubleshooting.md`
- `docs-site/src/content/docs/security-and-trust.md`
- `docs-site/src/content/docs/install/claude-code.md`
- `docs-site/src/content/docs/install/codex.md`
- `docs-site/src/content/docs/reference/source-vs-dist.md`
- `docs-site/src/content/docs/reference/manifests.md`
- `docs-site/src/content/docs/reference/hooks.md`
- `docs-site/src/content/docs/reference/agents.md`
- `docs-site/src/content/docs/reference/skills.md`
- `docs-site/astro.config.mjs`
- `README.md`
- `speckit-pro/README.md`
- `.claude-plugin/marketplace.json`
- `.agents/plugins/marketplace.json`
- `speckit-pro/.claude-plugin/plugin.json`
- `speckit-pro/.codex-plugin/plugin.json`
- `dist/claude/speckit-pro/.claude-plugin/plugin.json`
- `dist/codex/speckit-pro/.codex-plugin/plugin.json`
- `speckit-pro/hooks/hooks.json`
- `speckit-pro/codex-hooks.json`

---

## Phase 1: Specify

**When to run:** At the start of DOC-008. Output: `specs/doc-008-troubleshooting-security-trust-update-rollback/spec.md`.

### Specify Prompt

```bash
$speckit-specify

## Feature: Troubleshooting, security, trust, update, and rollback model

DOC-008 should turn the existing troubleshooting and security/trust route shells
into full user-facing documentation and add a top-level update/rollback route.
It must stay docs-only and source-backed.

### Goals
- Produce three user-facing pages: troubleshooting, security/trust, and update/rollback.
- Make troubleshooting symptom-driven with rows for symptom, likely cause, diagnostic command or file, recommended fix, platform label, and follow-up link.
- Make the trust model fact-bound: separate official vendor behavior, checked-in repository facts, and recommended practice.
- Explain update, refresh, reinstall, remove, rollback, stale payload, stale cache, and version-sync cases without adding a new diagnostics command.
- Use shared rows with Claude Code, Codex, or both labels where concepts overlap.
- Cite official vendor docs for platform behavior and repo files or generated reference pages for Racecraft-specific behavior.

### Users
- Users diagnosing failed installs, stale plugin behavior, missing custom agents, permission prompts, path confusion, version drift, and Spec Kit CLI prerequisite issues.
- Security or platform evaluators deciding whether the marketplace/plugin is acceptable for their machine or team.
- Returning users who need safe update, remove, reinstall, rollback, or stale-cache recovery guidance.

### User Stories
1. As a user, I can match my failure symptom to a likely cause, inspect the right command or file, and apply a safe recommended fix.
2. As a security or platform evaluator, I can understand what SpecKit Pro can package or invoke on Claude Code and Codex, and distinguish official platform behavior from repository facts.
3. As a returning user, I can update, refresh, remove, or rollback a stale or incorrect install without editing generated payloads or installed caches directly.

### Constraints
- Follow `docs/ai/specs/.process/DOC-008-design-concept.md`.
- Use existing Astro/Starlight docs-site conventions.
- Use existing DOC-007 generated reference pages as source-cited supporting material.
- Verify current official Claude Code and OpenAI Codex docs before making platform-behavior claims.
- Browser docs must not execute local commands, request permissions, or modify user configuration.
- Do not change plugin behavior, generated payload semantics, manifests, hooks, release automation, or CI behavior.

### Out of Scope
- Live doctor command or browser-side local diagnostics.
- Security audit, certification, formal threat model, or control attestation.
- Full contributor/release workflow owned by DOC-009.
- Site-wide search, accessibility, deep-link, and docs CI hardening owned by DOC-010.

### Open Questions To Resolve
- Confirm the exact route slug and sidebar placement for the update/rollback page. Recommended default: `update-and-rollback.md` under How-to.
- Confirm the official vendor docs that will be cited for Claude Code plugins/managed settings and Codex plugins/skills/subagents/sandbox/approvals/cache behavior.
- Confirm whether troubleshooting matrix rows need per-platform sections for any failure class that cannot be represented cleanly with shared platform labels.
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 19 after Clarify; 17 after Specify |
| User Stories | 3 |
| Acceptance Criteria | 9 |

### Files Generated

- [x] `specs/doc-008-troubleshooting-security-trust-update-rollback/spec.md`

---

## Phase 2: Clarify

**When to run:** After Specify, if the spec still has route, source, or matrix ambiguity. Maximum 5 targeted questions per session.

### Clarify Prompts

#### Session 1: IA and Route Boundaries

```bash
$speckit-clarify

Focus on DOC-008 IA and route boundaries:
- Confirm the update/rollback route slug, title, and sidebar group.
- Confirm links from install/Claude, install/Codex, troubleshooting, security/trust, and reference pages.
- Confirm what belongs in DOC-008 versus DOC-009 contributor workflow and DOC-010 validation hardening.
- Pay special attention to: avoiding a second contributor guide or broad CI work inside DOC-008.
```

#### Session 2: Troubleshooting Matrix

```bash
$speckit-clarify

Focus on DOC-008 troubleshooting matrix completeness:
- Symptom categories for install, marketplace source, generated payload, cache, permissions/approvals, Spec Kit CLI, GitHub CLI, jq, and Codex custom agents.
- Required row fields: symptom, platform label, likely cause, inspect command/file, recommended fix, and follow-up link.
- How to distinguish safe copyable inspection commands from commands that mutate local config.
- Pay special attention to: stale-source versus stale-installed-cache diagnosis.
```

#### Session 3: Security, Trust, and Sources

```bash
$speckit-clarify

Focus on DOC-008 security/trust and source policy:
- Which official Claude Code and OpenAI Codex docs must be cited for plugin packaging, hooks/MCP/settings, custom agents, sandboxing, approvals, managed settings, and cache behavior.
- How repository-derived claims should cite generated DOC-007 reference pages and checked-in source files.
- How to phrase recommended practice without overclaiming security guarantees.
- Pay special attention to: separating official vendor behavior, repository facts, and recommended practice.
```

#### Session 4: Update and Rollback Recovery

```bash
$speckit-clarify

Focus on DOC-008 update and rollback procedures:
- Marketplace refresh, reinstall, remove, payload rebuild, copied personal payload refresh, custom-agent reinstall, restart, stale cache, version sync, and rollback cases.
- Which commands are safe to document as inspection/checkpoint commands and which should be framed as manual operator actions.
- How to link rollback guidance to source-vs-dist and manifest references.
- Pay special attention to: avoiding a live doctor command or release automation changes.
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | IA and route boundaries | 4 | Route/sidebar already resolved; clarified that reference backlinks belong in hand-authored pages unless DOC-008 explicitly changes the reference generator |
| 2 | Troubleshooting matrix | 5 | Accepted explicit required row categories and a strict read-only inspection boundary after security-tagged consensus and human confirmation |
| 3 | Security, trust, and sources | 5 | Accepted expanded vendor citation inventory, claim-specific source policy, no-overclaim wording, and cache/recovery boundary after security-tagged consensus and human confirmation |
| 4 | Update and rollback recovery | 5 | Clarified recovery-case structure, manual operator action boundaries, payload script handoff, Codex custom-agent reinstall separation, and Codex CLI JSON/runtime-observation wording for installed state |

### Clarify Consensus Notes

- Session 1: Codebase and spec-context analysts agreed that DOC-008 should not hand-edit generated DOC-007 reference subpages for backlinks. Backlinks from reference content must live in hand-authored `reference.md` or be implemented through an explicit reference-generator change.
- Session 2: Codebase, spec-context, and domain-research analysts agreed that troubleshooting coverage must include explicit rows for install failure, marketplace source, generated payload, installed cache/runtime state, permissions/approvals, Spec Kit CLI, GitHub CLI, jq, and Codex custom agents. Security-tagged consensus was human-confirmed before edits.
- Session 2: The `inspect command/file` field is read-only only: state-reporting commands, platform detail views, manual file paths, or source/reference links. Mutating actions such as login, install, remove, reload, restart, approve, edit, set, unset, delete, rebuild, config writes, cache edits, or token/secret-printing commands must stay out of the inspect column and appear only as manual operator recovery steps where appropriate.
- Session 3: Codebase, spec-context, and domain-research analysts agreed that platform claims must cite the narrowest current vendor page for the specific behavior, with expanded Claude Code coverage for plugins reference, plugin marketplaces, managed MCP, and environment/Claude-directory behavior, plus expanded OpenAI Codex coverage for hooks, MCP, config, environment variables, and CLI reference. Security-tagged consensus was human-confirmed before edits.
- Session 3: Cache and recovery wording must classify evidence precisely: vendor-documented cache paths or commands are official vendor behavior; Racecraft source, generated payload, manifest, and DOC-007 reference facts are repository facts; `do not edit installed caches directly` is recommended practice derived from those facts. DOC-008 must not make direct cache deletion, cache edits, or manual cache directory removal the default stale-install or stale-cache recovery path.
- Session 4: Recovery cases must distinguish read-only checkpoints from manual operator actions with expected side effects, reload/restart needs, and source citations. End-user recovery should inspect marketplace/source state, generated or copied payload state, platform-managed refresh/reinstall/remove state, reload/restart state, Codex custom-agent registration, and only then last-resort cache guidance.
- Session 4: Codebase, spec-context, and domain-research analysts agreed that DOC-008 should describe Codex installed plugin state through documented CLI JSON fields and local runtime observations, not as a stable hardcoded cache-path contract. Official Codex claims may cite `CODEX_HOME`, documented `codex plugin ... --json` fields such as `installedPath`, and documented install/list/remove/marketplace commands. Concrete paths from current Racecraft docs, installer output, or the SpecKit Pro install skill are repository/plugin-owned local runtime evidence or machine-observed examples unless current OpenAI Codex docs explicitly document the exact path.
- Session 4: Payload rebuild and version-sync scripts are maintainer/source-infrastructure evidence or handoff references, not DOC-008 end-user recovery commands. Codex custom-agent reinstall remains separate from plugin refresh and must route through `@SpecKit Pro -> install` or `$install` when bundled TOML files change.

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output: `specs/doc-008-troubleshooting-security-trust-update-rollback/plan.md`.

### Plan Prompt

```bash
$speckit-plan

## Tech Stack
- Docs site: Astro 6.4.6 with Starlight 0.40.0.
- Content: committed Markdown/MDX under `docs-site/src/content/docs/`.
- Runtime: docs-site JavaScript ESM on Node for existing scripts; no new runtime dependency planned.
- Validation: `pnpm --dir docs-site reference:check`, `pnpm --dir docs-site validate`, and `pnpm --dir docs-site validate:links`.
- Plugin validation: `bash tests/speckit-pro/run-all.sh --layer 1` only if plugin/spec surfaces, manifests, scripts, hooks, or generated payload paths are touched.

## Constraints
- Follow `docs/ai/specs/.process/DOC-008-design-concept.md`.
- Keep implementation docs-only and local-file/source-citation oriented.
- Do not add a live diagnostic command, browser execution, or CI workflow changes.
- Do not change plugin behavior, manifests, hooks, generated payloads, marketplace behavior, or release automation.
- Verify current official platform docs before making platform claims.

## Architecture Notes
- Expand existing `troubleshooting.md` and `security-and-trust.md`.
- Add a top-level update/rollback page, recommended path `docs-site/src/content/docs/update-and-rollback.md`.
- Update `docs-site/astro.config.mjs` only as needed to expose the new route in the Starlight sidebar.
- Use tables, headings, and stable anchors that support direct support links.
- Prefer links to generated reference pages for manifests, hooks, agents, skills, and source-vs-dist facts instead of duplicating full reference tables.
- Distinguish source facts from recommended practice in page prose.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | Complete | Technical context, declared file operations, constitution check, validation plan |
| `research.md` | Complete | Three-page IA, source policy, matrix model, recovery model, vendor-doc verification |
| `data-model.md` | Complete | Troubleshooting row, trust claim, recovery case, read-only inspection, manual recovery action, rollback anchor, evidence source |
| `contracts/` | Not generated | Omitted because DOC-008 exposes no new API, CLI command, schema, or generated data artifact |
| `quickstart.md` | Complete | Manual validation walkthrough and required docs-site commands |

---

## Phase 4: Domain Checklists

**When to run:** After Plan. Run the focused domains below unless Specify or Plan produces a better risk profile.

### Recommended Checklist Domains

#### 1. UX Checklist

Why this domain: DOC-008 is a support and evaluator reading workflow. The pages must be fast to scan and direct-link friendly.

```bash
$speckit-checklist ux

Focus on DOC-008 requirements:
- Troubleshooting matrix scanability and row-level support usefulness.
- Clear route distinction among troubleshooting, security/trust, and update/rollback.
- Links from install/reference pages into the correct DOC-008 destination.
- Empty or unresolved cases that need handoff to install/reference/contributor pages.
- Pay special attention to: whether users can identify the next inspect command or file without reading the whole page.
```

#### 2. Security Checklist

Why this domain: DOC-008 explains trust boundaries and platform permissions; overclaiming or under-citing would be high risk.

```bash
$speckit-checklist security

Focus on DOC-008 requirements:
- Fact-bound separation of official vendor behavior, repository facts, and recommended practice.
- Coverage of source, generated payloads, installed cache, hooks, MCP/config, agents/custom agents, sandbox, approvals, and managed policy.
- Explicit statement that browser docs do not grant permissions or run workflows.
- Pay special attention to: avoiding guarantees, certifications, or audit claims that are not source-backed.
```

#### 3. Error Handling Checklist

Why this domain: Troubleshooting content is about failure modes and recovery paths.

```bash
$speckit-checklist error-handling

Focus on DOC-008 requirements:
- Failure classes for marketplace, path, cache, version, permissions, CLI prerequisites, and custom-agent registration.
- Clear likely cause and recommended fix for each symptom row.
- Safe recovery flow for update, reinstall, remove, stale cache, and rollback cases.
- Pay special attention to: distinguishing inspection commands from mutating repair steps.
```

#### 4. Accessibility Checklist

Why this domain: DOC-008 relies on dense tables and support matrices that must remain usable with keyboard and screen readers.

```bash
$speckit-checklist accessibility

Focus on DOC-008 requirements:
- Semantic table headers and readable row labels for troubleshooting and update/rollback matrices.
- Stable headings and link text for deep links.
- No reliance on browser-side execution or interactive-only controls.
- Pay special attention to: whether dense matrices remain understandable as static Markdown.
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| UX | 14 | 1 found; 0 remain | FR-003, FR-004, FR-006, FR-017, SC-001, SC-002 |
| Security | 18 | 1 found; 0 remain | FR-006, FR-007, FR-008, FR-009, FR-010, FR-013, FR-014, FR-015, FR-016, SC-003, SC-004, SC-005 |
| Error Handling | 18 | 0 found; 0 remain | FR-003, FR-004, FR-006, FR-011, FR-012, FR-013, FR-015, FR-016, SC-002, SC-006 |
| Accessibility | 18 | 4 found; 0 remain | FR-003, FR-011, FR-017, SC-009, plan page architecture and documentation boundaries |
| **Total** | 68 | 6 found; 0 remain | G4 passed; no Gap markers remain across spec, plan, or checklists |

---

## Phase 5: Tasks

**When to run:** After checklists complete and gaps are resolved. Output: `specs/doc-008-troubleshooting-security-trust-update-rollback/tasks.md`.

### Tasks Prompt

```bash
$speckit-tasks

## Task Structure
- Organize by user story, not by docs layer.
- Keep tasks small and reviewable, with source-citation checks where claims depend on official or repository evidence.
- Mark parallel-safe tasks with [P].
- Include explicit validation tasks for docs-site validate, link validation, and source-reference review.

## Implementation Phases
1. Foundation: route/sidebar plan, source inventory, page model, and validation setup.
2. User Story 1: troubleshooting symptom matrix and links.
3. User Story 2: fact-bound security/trust model and citations.
4. User Story 3: update/rollback procedures and stale-state recovery guidance.
5. Polish: cross-links, accessibility pass, source citation review, docs validation.

## Constraints
- Use `docs/ai/specs/.process/DOC-008-design-concept.md` to preserve the chosen IA and source policy.
- Keep DOC-009 contributor workflow and DOC-010 docs CI hardening out of scope.
- Do not touch plugin runtime behavior, generated payload semantics, manifests, hooks, release automation, or CI behavior unless the spec explicitly identifies a source-data bug and records why.
- If implementation touches plugin/spec surfaces unexpectedly, add `bash tests/speckit-pro/run-all.sh --layer 1` to verification.
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | 40 |
| **Phases** | 6: Setup, Foundational, US1 troubleshooting, US2 security/trust, US3 update/rollback, Polish |
| **Parallel Opportunities** | 8 task-level `[P]` markers; US1/US2/US3 can run in parallel after Foundation by separate page owners; final validation remains serial |
| **User Stories Covered** | 3: US1 = 6 tasks, US2 = 6 tasks, US3 = 7 tasks |

---

## Atomicity Route

After the Tasks phase, autopilot runs the read-only atomicity classifier against
`specs/doc-008-troubleshooting-security-trust-update-rollback` and records its
decision here. This scaffold does not precompute or force a route.

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | `one-navigable-PR` | One navigable documentation PR is appropriate for the three coordinated DOC-008 pages and links. |
| **Releasable** | `true` | Docs-only change with no release-sensitive runtime behavior. |
| **Signals** | `change-shape:modify-heavy` | The classifier saw a modify-heavy docs/process change shape. |
| **Warnings** | None | No release-safety warnings emitted. |

Command:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/doc-008-troubleshooting-security-trust-update-rollback
```

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks to catch cross-artifact drift.

### Analyze Prompt

```bash
$speckit-analyze

Focus on DOC-008:
1. Constitution alignment: docs-only scope, no plugin behavior changes, no live diagnostics command.
2. Coverage gaps: AC-8.1 through AC-8.6 must map to user stories and tasks.
3. Source policy: official vendor behavior, repository facts, and recommended practice must be separated consistently.
4. Page/file scope: tasks should cover troubleshooting, security/trust, update/rollback, sidebar/link updates, and validation.
5. Design concept drift: verify the three-page decision, symptom matrix, fact-bound model, procedural recovery depth, shared platform labels, one-slice decision, and docs validation bundle remain intact.
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| A1 | Medium | `tasks.md` did not explicitly map PRD AC-8.1 through AC-8.6 to DOC-008 user stories and task IDs | Added `Acceptance Criteria Traceability` mapping AC-8.1 through AC-8.6 to user stories and concrete tasks; marker counts returned to zero |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed with no unresolved critical/high coverage gaps.

### Implement Prompt

```bash
$speckit-implement

## Approach: Docs-First Verification

For each task:
1. Confirm the source evidence before writing claims.
2. Update the smallest relevant docs-site page or sidebar entry.
3. Add links to generated DOC-007 reference pages where they already cover source-vs-dist, manifests, hooks, agents, or skills.
4. Keep platform behavior claims tied to official vendor docs and repository behavior tied to checked-in files.
5. Verify with the docs validation bundle before PR creation.

### Pre-Implementation Setup
1. Verify branch: `git rev-parse --abbrev-ref HEAD` should show `doc-008-troubleshooting-security-trust-update-rollback`.
2. Review `docs/ai/specs/.process/DOC-008-design-concept.md`.
3. Review current route shells: `docs-site/src/content/docs/troubleshooting.md` and `docs-site/src/content/docs/security-and-trust.md`.
4. Review generated references under `docs-site/src/content/docs/reference/`.

### Implementation Notes
- Recommended new route: `docs-site/src/content/docs/update-and-rollback.md`.
- Update `docs-site/astro.config.mjs` only as needed to expose the new route.
- Prefer static Markdown tables with clear headers over custom components unless a stronger need appears in the plan.
- Do not edit generated reference pages directly unless `pnpm --dir docs-site reference:generate` is intentionally rerun after source changes.
- If DOC-008 needs a backlink from reference content, place it in a hand-authored page such as `reference.md`; generated-subpage backlinks require an explicit generator change plus regenerate/check verification.
- If source facts appear stale, prefer linking to source files and recording the limitation rather than making unsupported claims.
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| Foundation | T001-T008 | Complete | Reviewed route/sidebar, source inventory, generated DOC-007 references, validation commands, and scope guard |
| User Story 1 | T009-T014 | Complete | Replaced troubleshooting shell with source-cited symptom matrix and read-only inspection boundary |
| User Story 2 | T015-T020 | Complete | Expanded security/trust model with vendor behavior, repository facts, and recommended-practice boundaries |
| User Story 3 | T021-T027 | Complete | Added update/rollback route with recovery cases, stale-cache guardrails, and platform notes |
| Polish | T028-T040 | Complete | Added sidebar/install/reference handoffs, completed citation/accessibility review, and ran validation bundle |

---

## Post-Implementation Checklist

- [x] All tasks are marked complete in `tasks.md` (40/40; G7 passed).
- [x] `pnpm --dir docs-site reference:check` passes.
- [x] `pnpm --dir docs-site validate` passes.
- [x] `pnpm --dir docs-site validate:links` passes.
- [x] Source-reference review confirms platform claims cite official docs and repo-specific claims cite checked-in files or generated reference pages.
- [x] `git diff --name-only` confirms no plugin behavior, generated payload semantics, manifests, hooks, release automation, or CI behavior changed.
- [x] `bash tests/speckit-pro/run-all.sh --layer 1` was not required because implementation touched docs-site content/navigation and DOC-008 process artifacts only; no plugin behavior, manifests, hooks, scripts, tests, generated payload paths, release automation, or CI behavior changed.

### Post-Implementation Evidence

| Item | Status | Evidence |
|------|--------|----------|
| Doctor Extension Check | Skipped | No runnable Codex doctor command was registered; `speckit-utils` commands exist only under `.claude/commands` in this worktree. |
| Verify Implementation | Skipped | `$speckit-verify` is registered only for Claude in `.specify/extensions/.registry`; no runnable Codex command/skill was available. |
| Verify Tasks Phantom Check | Skipped | `$speckit-verify-tasks` is registered only for Claude in `.specify/extensions/.registry`; no runnable Codex command/skill was available. |
| Code Review | Complete | Subagent review found the new route was untracked and the Spec Kit CLI row citation was weak; route file will be staged, and the citation was updated to scripts evidence. |
| Integration Suite | Complete | `pnpm --dir docs-site reference:check`, `pnpm --dir docs-site validate`, `pnpm --dir docs-site validate:links`, `git diff --check`, and G7 all passed. |
| Cleanup | Skipped | No runnable Codex cleanup extension command was installed. |
| Self-Review | Complete | Parent review found no unresolved markers, unsafe cache-default guidance, or generated reference subpage edits. |
| UAT Runbook Generation | Complete | Generated a DOC-008 UAT skeleton during post checks; the file is regenerated transiently for PR body generation rather than committed, keeping the final diff within reviewability limits. |
| Final Reviewability Backstop | Complete | Proceeded with status `warn`: total files 25 exceeded the warn threshold 15 and primary surfaces 4 exceeded the warn threshold 1; no blockers remained after keeping UAT evidence transient. |
| PR Packet/Body Generation | Complete | Generated transient packet/body, edited sanctioned DOC-008 prose fields, passed `validate-pr-packet.sh`, and passed `validate-pr-workflow-contract.sh`. |
| PR Creation | Complete | Created PR #220: <https://github.com/racecraft-lab/racecraft-plugins-public/pull/220>. |
| Review Remediation | Complete | PR was newly created with no review feedback or requested changes to remediate. |
| Retrospective | Skipped | Retrospective extension is registered only for Claude in this worktree; no runnable Codex retrospective command or skill was available. |

---

## Project Structure Reference

```text
docs-site/
  astro.config.mjs
  package.json
  src/content/docs/
    troubleshooting.md
    security-and-trust.md
    update-and-rollback.md
    install/
    reference/
docs/ai/specs/
  interactive-documentation-technical-roadmap.md
  .process/DOC-008-design-concept.md
  .process/DOC-008-workflow.md
specs/doc-008-troubleshooting-security-trust-update-rollback/
  SPEC-MOC.md
```
