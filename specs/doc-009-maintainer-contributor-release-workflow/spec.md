# Feature Specification: Maintainer and Contributor Release Workflow

**Feature Branch**: `doc-009-maintainer-contributor-release-workflow`

**Created**: 2026-06-18

**Status**: Draft

**Input**: User description: "Deepen the existing `/contribute-and-release` docs route into a source-backed release workflow for maintainers, contributors, reviewers, and docs maintainers."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Classify the Change Path (Priority: P1)

As a contributor, I can identify whether my change is docs-only, plugin source, generated payload, marketplace, or release automation work and see the checks required for that path.

**Why this priority**: Correctly classifying the change path prevents contributors from editing generated output, skipping required validation, or confusing CI behavior with release readiness.

**Independent Test**: Can be tested by reviewing the page with one example from each change type and confirming the contributor can name the source surface, generated surface, and required validation for each.

**Acceptance Scenarios**:

1. **Given** a contributor has a docs-only change, **When** they read the change-type guidance, **Then** they can distinguish non-site Markdown from docs-site content and name the expected PR evidence.
2. **Given** a contributor has a plugin source or generated payload change, **When** they read the change-type guidance, **Then** they can tell whether to edit source, rebuild payloads, sync marketplaces, or leave generated files untouched.

---

### User Story 2 - Complete Release Readiness (Priority: P1)

As a maintainer, I can complete a release-readiness checklist that covers source/dist parity, Claude/Codex marketplace parity, manifest version consistency, generated payload validation, full deterministic tests, and docs-site validation when relevant.

**Why this priority**: Maintainers need one operational checklist that turns source edits into reviewable PRs without reconstructing release policy from scripts, workflows, manifests, and generated payloads.

**Independent Test**: Can be tested by applying the checklist to a hypothetical plugin source PR and a docs-site PR, then confirming each required parity and validation item is present.

**Acceptance Scenarios**:

1. **Given** a plugin-changing PR, **When** a maintainer uses the checklist, **Then** they can verify source/dist parity, marketplace parity, version consistency, generated payload validation, and the release-readiness test expectation.
2. **Given** a docs-site PR, **When** a maintainer uses the checklist, **Then** they can identify docs-site validation as required in addition to the release-readiness expectation.

---

### User Story 3 - Review PR Metadata and Evidence (Priority: P2)

As a reviewer, I can verify that a PR title and body follow Conventional Commit and public-readable guidance and include the right validation evidence.

**Why this priority**: Reviewers need a quick way to decide whether the PR is ready for public review and compatible with CI and release automation.

**Independent Test**: Can be tested by comparing sample PR titles and bodies against the page guidance and confirming that invalid titles, internal-only descriptions, and missing evidence are caught.

**Acceptance Scenarios**:

1. **Given** a PR title, **When** a reviewer checks it against the page, **Then** they can determine whether it follows the required Conventional Commit shape and public-readable wording.
2. **Given** a PR body, **When** a reviewer checks it against the page, **Then** they can find what changed, why, non-goals, review order, scope budget, traceability, validation evidence, and any deferred work.

---

### User Story 4 - Understand Docs-Only CI and DOC-010 Handoff (Priority: P3)

As a docs maintainer, I can see current docs-only CI behavior and the future DOC-010 handoff for docs-site CI hardening.

**Why this priority**: Docs maintainers need the page to be honest about current CI coverage without implementing future docs-site CI work in DOC-009.

**Independent Test**: Can be tested by reading the docs-only section and confirming it explains current PR Checks behavior, docs-site validation expectations, and the DOC-010 boundary.

**Acceptance Scenarios**:

1. **Given** a docs-only PR, **When** a docs maintainer reads the page, **Then** they can see that the plugin matrix is skipped when no plugin, test, dist, marketplace, script, release config, or workflow paths change, while PR title validation and the sentinel still matter.
2. **Given** a docs-site validation or CI hardening question, **When** a docs maintainer reads the page, **Then** they can see that DOC-010 owns future docs-site CI hardening rather than DOC-009.

### Edge Cases

- A PR changes both docs-site content and plugin source, requiring both docs-site validation and plugin release-readiness validation.
- A PR changes generated payloads or marketplace registries without a matching source or version-sync explanation.
- A release-please PR is validated through observable release workflow behavior: payload sync on the release PR branch plus manual `PR Checks` dispatch. Any explanation of GitHub-token event behavior must be caveated to `GITHUB_TOKEN` recursion rules and sourced.
- Generated reference pages drift from their generator output and must be handled through the generator contract, not hand edits.
- A docs-only PR passes current repository CI but still lacks the validation evidence expected for a release-ready review.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The documentation MUST deepen `docs-site/src/content/docs/contribute-and-release.md` as the single `/contribute-and-release` page for the maintainer and contributor release workflow.
- **FR-002**: The page MUST map authoring source, generated payloads, Claude marketplace registry, Codex marketplace registry, manifest version fields, docs-site files, generated reference pages, CI behavior, release-please, and PR conventions.
- **FR-003**: The page MUST include a change-type decision matrix covering docs-only, plugin source, generated payload/dist, marketplace registry, and release automation changes.
- **FR-004**: For each change type, the page MUST name the source surface, generated or synchronized surfaces, required checks, and review evidence contributors should include without repeating a full command block in every change-type section.
- **FR-005**: The contributor path MUST explain how to pick the smallest source surface, avoid editing generated payloads unless the change is a generated sync, use Conventional Commit PR titles, write public-readable PR bodies, and include validation evidence.
- **FR-006**: The maintainer release-readiness path MUST include source/dist parity, Claude/Codex marketplace parity, manifest version consistency, generated payload validation, full deterministic tests, and docs-site validation when relevant.
- **FR-007**: The page MUST present `bash tests/speckit-pro/run-all.sh` as the release-readiness test expectation.
- **FR-008**: The page MUST require `pnpm --dir docs-site validate` when docs-site files change and MUST explain that this validation includes the docs reference check, type check, and build according to the docs-site package scripts.
- **FR-009**: The page MUST explain current docs-only PR Checks behavior from `.github/workflows/pr-checks.yml`, including changed-plugin detection, skipped plugin matrix behavior, `validate-plugins`, and PR title validation.
- **FR-010**: The page MUST explain release automation as observable maintainer behavior: release-please PR creation, release PR payload sync, manual PR Checks dispatch for release-please PR branches, GitHub Release publication, and post-release payload/marketplace sync PR behavior.
- **FR-011**: The page MUST state that release-please owns release version bumps for plugin manifests and that marketplace versions are synchronized from platform plugin manifests by the marketplace sync script.
- **FR-012**: The page MUST link to deeper repository guidance and generated reference pages instead of duplicating all `CLAUDE.md`, workflow, script, or generated reference internals.
- **FR-013**: The page MUST state that generated reference pages remain generated and that drift should be corrected through the existing generator contract rather than hand-editing generated output.
- **FR-014**: The page MUST explicitly hand current docs-site CI hardening, search, accessibility, deep-link, and responsive validation work to DOC-010 without implementing or promising those behaviors in DOC-009.
- **FR-015**: The page MUST provide a final release-readiness checklist that covers the DOC-009 acceptance criteria and can be used directly during review.

### DOC-009 Acceptance Criteria

- **AC-9.1**: The change-type matrix lists required checks for docs-only, plugin source, generated payload/dist, marketplace, and release automation changes.
- **AC-9.2**: The maintainer path explains `bash scripts/build-plugin-payloads.sh`, `bash scripts/sync-marketplace-versions.sh`, and `bash tests/speckit-pro/run-all.sh`.
- **AC-9.3**: Version guidance states which version fields are release-please-owned, generated, synchronized, or manually reviewed.
- **AC-9.4**: The final checklist covers source/dist parity, Claude/Codex marketplace parity, manifest version consistency, and generated payload validation.
- **AC-9.5**: Contributor guidance includes Conventional Commit and public-readable PR title/body expectations.
- **AC-9.6**: Docs-only CI behavior is explained from `.github/workflows/pr-checks.yml`, and future docs-site CI hardening is explicitly handed to DOC-010.

### Source Evidence Requirements

- The implementation MUST source every command, CI, release, version, generated-surface, and marketplace behavior claim from primary files such as `AGENTS.md`, `CLAUDE.md`, `.github/workflows/pr-checks.yml`, `.github/workflows/release.yml`, `release-please-config.json`, `.release-please-manifest.json`, `scripts/build-plugin-payloads.sh`, `scripts/sync-marketplace-versions.sh`, `tests/speckit-pro/run-all.sh`, and `docs-site/package.json`.
- The implementation MUST use `docs/ai/specs/.process/DOC-009-design-concept.md` for scope decisions.
- The implementation MUST preserve the existing DOC-002 route shell ownership history while replacing the shell content with DOC-009's full workflow content.

### Reviewability Notes *(if applicable)*

- DOC-009 is documentation work. It must not change CI, release automation behavior, scripts, manifests, generated payloads, marketplace registries, or version fields unless a source citation is broken and a narrow fix is explicitly approved.
- Generated reference pages and generated payloads are not valid hand-edit targets for this spec.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: docs-site content
- **Projected reviewable LOC**: 380
- **Projected production files**: 0
- **Projected total files**: about 6
- **Budget result**: within budget
- **Split decision**: This remains one spec because the user-facing deliverable is a single existing documentation route with supporting source citations and no behavior changes.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major DOC-009 requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name DOC-010 for docs-site CI hardening, search, accessibility, deep-link, responsive, or validation-hardening work.

### Key Entities *(include if feature involves data)*

- **Change Type**: A category of repository change such as docs-only, plugin source, generated payload, marketplace registry, or release automation.
- **Source Surface**: The authoring file or workflow source that should be edited first for a change type.
- **Generated Surface**: A payload, marketplace registry, or reference page that should be produced or checked through an existing generator or sync contract.
- **Validation Evidence**: The commands, CI behavior, or source-backed checks a contributor includes so maintainers and reviewers can verify readiness.
- **Release Automation Event**: An observable maintainer-facing event such as release-please opening a PR, syncing release PR payloads, publishing a release, or opening a post-release sync PR.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A contributor can classify all five supported change types and name the required validation evidence for each within five minutes of reading the page.
- **SC-002**: A maintainer can use the final checklist to verify 100% of required parity, version consistency, generated payload, release-readiness, and docs-site validation items for a relevant PR.
- **SC-003**: A reviewer can determine whether a PR title and body meet Conventional Commit, public-readable, and validation-evidence expectations within three minutes.
- **SC-004**: The page makes no unsourced claims about CI, release automation, generated payloads, or marketplace behavior.
- **SC-005**: The page clearly distinguishes current docs-only CI behavior from DOC-010 future docs-site CI hardening, with no promise that DOC-009 implements DOC-010 behavior.
- **SC-006**: Each DOC-009 acceptance criterion AC-9.1 through AC-9.6 maps to a visible page section or checklist item.

## Clarifications

### Session 1 - Page Structure

- Command examples will use one consolidated release-readiness block, while the change-type matrix labels which commands and evidence apply to each path.
- Generated reference pages will be linked from a source-of-truth map and the final checklist, with sparse inline links on first mention rather than repeated links in every release section.
- `pnpm --dir docs-site validate` is required for changes under `docs-site/`; non-site Markdown docs changes still need appropriate PR evidence and the release-readiness expectation stated by the page.
- The published page order will be: purpose, source-of-truth map, change-type matrix, contributor path, maintainer readiness, version and release automation guidance, final checklist, and DOC-010 handoff.

### Session 2 - Source-Fact Boundaries

- Every command, CI, release, version, generated-surface, and marketplace behavior claim must cite primary source files; generated reference pages can be reader-facing links but do not replace primary source citations.
- Docs-only PR Checks behavior must be stated from `.github/workflows/pr-checks.yml`: plugin tests skip only when no plugin-affecting paths changed, while `validate-pr-title` and the `validate-plugins` sentinel still matter.
- Release-please PR guidance must describe observable repo behavior first: the Release workflow syncs generated payloads for the release PR branch, then manually dispatches `PR Checks`. Any GitHub-token rationale must be scoped to `GITHUB_TOKEN` recursion behavior instead of phrased as an absolute platform rule.
- Release-please owns source plugin manifest version bumps for both Claude Code and Codex manifests. Generated payload manifests under `dist/` are rebuilt from source. Marketplace registry versions are synchronized from the platform manifest paths by `scripts/sync-marketplace-versions.sh` and are not normal manual edit targets.
- Docs-site validation claims must cite `docs-site/package.json`; `validate` runs the checked-in docs-site validation script chain and must not be described as DOC-010 hardening.

### Session 3 - Validation and DOC-010 Handoff

- `pnpm --dir docs-site validate` is required for any change under `docs-site/**`; non-site Markdown docs do not require it unless they affect docs-site generation or output.
- `pnpm --dir docs-site reference:check` is included in `docs-site` validation and may also be listed as a focused preflight when checking generated reference drift or generator output directly.
- `bash tests/speckit-pro/run-all.sh` is the release-readiness expectation for maintainer review, especially plugin or release-affecting changes; it must not be described as a promise that current CI runs the full suite for every PR.
- Mixed docs-site plus plugin or release-surface PRs need both validation lanes, plus payload rebuild or marketplace sync evidence when those generated/synchronized surfaces are relevant.
- DOC-009 documents current local docs-site validation and current PR Checks behavior. DOC-010 owns adding or hardening docs-site CI for site build, Markdown/link validation, search, accessibility, deep links, responsive checks, manifest/payload consistency, and safe command-snippet validation.

## Assumptions

- The target page remains `docs-site/src/content/docs/contribute-and-release.md`; DOC-009 does not create a new route.
- The page uses a change-type matrix plus a final release-readiness checklist rather than duplicating a full command block in every section.
- Generated reference pages are linked from the source-of-truth map and checklist where relevant; they are not hand-edited as part of DOC-009.
- Docs-site changes require `pnpm --dir docs-site validate`; non-site Markdown changes still need appropriate PR evidence and the release-readiness expectation stated by the page.
- DOC-010 owns future docs-site CI hardening and related search, accessibility, deep-link, responsive, and validation-hardening work.
