# Feature Specification: Command, workflow, manifest, and file-layout reference

**Feature Branch**: `doc-007-command-workflow-manifest-and-file-layout-reference`

**Created**: 2026-06-17

**Status**: Draft

**Input**: User description: "Generate public reference subpages for core SpecKit Pro repository surfaces, with checked-in source citations, parallel Claude Code and Codex presentation, deterministic generate/check behavior, and no plugin behavior changes."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand available plugin surfaces (Priority: P1)

As a SpecKit Pro user, I can open generated reference pages and understand which Claude Code and Codex skills, agents, hooks, manifests, and related repository surfaces apply to my workflow without reading the whole repository.

**Why this priority**: This is the main public value of DOC-007. Users need stable reference pages before troubleshooting, contributor, or release-workflow documentation can depend on deep links.

**Independent Test**: Can be tested by reviewing the generated reference pages from the docs site and confirming that a user can identify the relevant Claude Code or Codex surface, its purpose, runtime differences, and source citation links.

**Acceptance Scenarios**:

1. **Given** the generated reference pages are current, **When** a user opens the reference section, **Then** they can navigate to separate subpages for skills, agents, manifests, hooks, scripts, tests, and source-vs-dist layout.
2. **Given** a surface exists for both Claude Code and Codex, **When** a user reads the generated row for that surface, **Then** the page presents the mapped surfaces in parallel and separates runtime-specific differences.
3. **Given** a generated reference row states a source fact, **When** a user follows its citation link, **Then** the link points to a real checked-in source path.

---

### User Story 2 - Check source-vs-dist responsibilities (Priority: P2)

As a maintainer, I can inspect generated file-layout and manifest reference pages to know which files are source, generated payload, test-only, release infrastructure, or documentation infrastructure before changing plugin files.

**Why this priority**: Maintainers need a dependable source-of-truth map so future plugin, docs, and release changes do not blur source files with generated payloads.

**Independent Test**: Can be tested by sampling repository surfaces from each generated page and confirming that the page classifies the files, cites source paths, and avoids unsupported claims.

**Acceptance Scenarios**:

1. **Given** a maintainer is reviewing plugin manifest or marketplace files, **When** they open the manifest reference page, **Then** they can distinguish source manifests, distribution manifests, marketplace registry files, and generated payload files.
2. **Given** a maintainer is reviewing scripts or tests, **When** they open the generated scripts or tests reference page, **Then** each listed row identifies the checked-in path, the repository role, and whether the row describes a source fact or an inferred note.
3. **Given** a maintainer is preparing a change, **When** they inspect the source-vs-dist layout reference, **Then** they can identify which files should be edited directly and which files are generated or validation-only.

---

### User Story 3 - Detect stale generated references (Priority: P3)

As a reviewer or agent, I can run a local check mode that proves generated reference pages are current with the checked-in source files they cite.

**Why this priority**: Generated docs only reduce drift if stale output is detectable before merge and later CI integration.

**Independent Test**: Can be tested by running the selected local check command against current output, then intentionally changing generated output and confirming the check fails without mutating files.

**Acceptance Scenarios**:

1. **Given** generated reference pages match the checked-in source files, **When** a reviewer runs check mode, **Then** the command succeeds and reports that generated output is current.
2. **Given** generated reference pages are stale, **When** a reviewer runs check mode, **Then** the command fails with an actionable message and does not rewrite files.
3. **Given** DOC-010 owns later CI hardening, **When** a reviewer reads the DOC-007 reference or quickstart handoff, **Then** the future CI wiring boundary is visible but not implemented as part of DOC-007.

### Edge Cases

- Optional repository surfaces may be absent; generated pages should label the surface as absent or omit it without inventing source facts.
- Source files may have malformed metadata or missing expected fields; generation/check behavior should fail clearly rather than publish unsupported rows.
- Generated output may be stale; check mode must report the stale files without writing changes.
- A row may need explanatory context that is not directly present in a source file; that context must appear as an inferred note, separate from source facts.
- Existing links to the reference section may still target the reference landing page; the landing page must remain useful while subpages are added.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature MUST produce full visible reference subpages for skills, agents, manifests, hooks, scripts, tests, and source-vs-dist layout.
- **FR-002**: The feature MUST preserve a useful reference landing page that orients readers to the generated subpages.
- **FR-003**: Every generated reference row that states a source fact MUST link to a real checked-in source path.
- **FR-004**: Source facts MUST come only from checked-in repository files.
- **FR-005**: Inferred notes MUST be labeled separately from source facts and MUST NOT be presented as direct source evidence.
- **FR-006**: Claude Code and Codex surfaces MUST be presented in parallel wherever they map to the same user or maintainer concept.
- **FR-007**: Runtime-specific differences between Claude Code and Codex MUST remain visible instead of being collapsed into a single generic description.
- **FR-008**: File-layout references MUST classify relevant files as source, generated payload, test-only, release infrastructure, documentation infrastructure, or other clearly named repository roles.
- **FR-009**: Manifest references MUST distinguish plugin manifests, marketplace registry files, integration manifests, and generated distribution manifests when those categories are present.
- **FR-010**: Script, hook, and test references MUST describe repository role and source path without changing the referenced behavior or semantics.
- **FR-011**: The feature MUST provide deterministic generate behavior for the generated reference pages.
- **FR-012**: The feature MUST provide check behavior that detects stale generated reference pages.
- **FR-013**: Check behavior MUST be read-only and MUST NOT rewrite generated files.
- **FR-014**: Generation and check behavior MUST read local checked-in repository files only; no network access, browser-side local execution, user-pasted JSON, or user-local plugin-install inspection is allowed.
- **FR-015**: The feature MUST NOT change plugin behavior, manifest semantics, generated payload content, marketplace behavior, install flow, hook semantics, or release automation.
- **FR-016**: Generated prose MUST remain public-readable for users, maintainers, and agents, not merely a raw metadata dump.
- **FR-017**: Generated pages MUST provide stable links that later docs, troubleshooting guides, agents, and release work can cite.
- **FR-018**: The specification and later planning artifacts MUST keep DOC-008 troubleshooting/security/trust depth, DOC-009 contributor workflow depth, and DOC-010 CI hardening out of this implementation slice.

### Reviewability Notes *(if applicable)*

- Generated reference content may be declared as generated output during planning, but source facts, inferred-note rules, generator behavior, and validation behavior remain reviewable.
- Typed reviewability exceptions are rare operator-owned overrides. Accepted classes are refactor, infra, and upgrade, but generated templates, generated zones, `.process` files, PR bodies, and code fences are not valid provenance.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: docs-site generated reference pages and local docs validation
- **Projected reviewable LOC**: Approximately 395 LOC, excluding any clearly declared generated reference output
- **Projected production files**: 0 plugin/runtime production files
- **Projected total files**: 6-10 files, depending on generated subpage grouping chosen during Clarify/Plan
- **Budget result**: within budget
- **Split decision**: Remains one spec because it is one documentation reference slice with no plugin behavior, manifest semantics, install-flow, generated payload, marketplace, hook, or release automation changes.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Reference Page**: A generated docs page for one repository surface group, such as skills, agents, manifests, hooks, scripts, tests, or source-vs-dist layout.
- **Reference Row**: A generated entry on a reference page that describes one surface, file, or mapping and carries source citations.
- **Source Fact**: A statement derived directly from a checked-in repository file and linked to that file.
- **Inferred Note**: A labeled explanatory statement derived from relationships among source facts rather than copied directly from one source file.
- **Runtime Surface Mapping**: The relationship between Claude Code and Codex surfaces when both runtimes expose comparable plugin concepts.
- **File Classification**: The repository role assigned to a path, such as source, generated payload, test-only, release infrastructure, or documentation infrastructure.
- **Reference Freshness Check**: A local validation result proving generated reference pages match current checked-in source files.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reader can reach each generated reference subpage from the reference section in no more than two navigation steps.
- **SC-002**: 100% of generated rows that state source facts include a citation link to an existing checked-in repository path.
- **SC-003**: A sampled review of generated rows confirms source facts and inferred notes are visibly separated.
- **SC-004**: Local check mode succeeds when generated reference pages are current and fails when at least one generated page is intentionally made stale.
- **SC-005**: Check mode leaves the working tree unchanged when it detects stale generated output.
- **SC-006**: Review of the final diff confirms no plugin behavior, manifest semantics, generated payload content, marketplace behavior, install flow, hook semantics, or release automation changed.
- **SC-007**: Maintainers can identify the source-vs-dist responsibility for every first-class surface group named in DOC-007: skills, agents, manifests, hooks, scripts, tests, and source-vs-dist layout.

## Assumptions

- DOC-007 starts from the existing docs-site reference shell and adds generated subpages rather than replacing the broader docs IA.
- Checked-in source files are the only permitted evidence source for generated reference content.
- The selected generate/check command names and docs generation format will be finalized during Clarify/Plan.
- DOC-010 may later wire check mode into GitHub Actions, but DOC-007 only provides deterministic local behavior and an explicit handoff.
- DOC-008 and DOC-009 can depend on DOC-007 reference links later, but their troubleshooting, security/trust, contributor, update, rollback, and release-workflow depth stays out of this slice.

## Unresolved for Consensus

- **[IA]** Exact generated subpage filenames, route slugs, index-page behavior, and sidebar grouping.
- **[Format]** Whether generated full page content is emitted as Markdown, MDX, or data rendered by a docs component.
- **[CI-Handoff]** Whether DOC-010 later wires the check mode into GitHub Actions, and which check command it should use.
