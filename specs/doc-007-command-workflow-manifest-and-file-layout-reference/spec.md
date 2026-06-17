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

1. **Given** the generated reference pages are current, **When** a user opens the reference section, **Then** they can navigate to separate subpages for skills, agents, manifests, hooks, scripts, tests, and source-vs-dist layout under `/reference/`.
2. **Given** a command or skill surface exists for Claude Code, Codex, or both runtimes, **When** a user reads the generated row for that surface, **Then** the page presents available invocation forms, purpose, prerequisites, expected output artifact, mapped runtime surfaces, and runtime-specific differences.
3. **Given** a generated reference row states a source fact, **When** a user follows its citation link, **Then** the link points to a real checked-in source path.

---

### User Story 2 - Check source-vs-dist responsibilities (Priority: P2)

As a maintainer, I can inspect generated file-layout and manifest reference pages to know which files are source, generated payload, test-only, release infrastructure, or documentation infrastructure before changing plugin files.

**Why this priority**: Maintainers need a dependable source-of-truth map so future plugin, docs, and release changes do not blur source files with generated payloads.

**Independent Test**: Can be tested by sampling repository surfaces from each generated page and confirming that the page classifies the files, cites source paths, and avoids unsupported claims.

**Acceptance Scenarios**:

1. **Given** a maintainer is reviewing plugin manifest or marketplace files, **When** they open the manifest reference page, **Then** they can distinguish source manifests, distribution manifests, marketplace registry files, generated payload files, and Claude Code versus Codex required and optional manifest fields.
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
- Required source files may be missing or unreadable; generation/check behavior must fail as a source error rather than treating the surface as optional.
- Source files may have malformed JSON, malformed or missing Markdown/frontmatter metadata, or missing expected fields; generation/check behavior should fail clearly as a parsing error rather than publish unsupported rows.
- Generated output may be stale; check mode must report the stale files without writing changes.
- A row may need explanatory context that is not directly present in a source file; that context must appear as an inferred note, separate from source facts.
- Existing links to the reference section may still target `/reference/`; the existing landing page must remain canonical and useful while subpages are added below it.

## Clarifications

### Session 2026-06-17 - IA And Route Shape

- Generated reference subpage basenames are `skills`, `agents`, `manifests`, `hooks`, `scripts`, `tests`, and `source-vs-dist` under the existing `/reference/` route group.
- The current `docs-site/src/content/docs/reference.md` page remains the canonical `/reference/` landing page; DOC-007 expands it into an index/orientation page instead of replacing it, redirecting it, or moving it to `reference/index.*`.
- The Starlight sidebar keeps the existing `Reference` group. The landing page stays first, generated `reference/*` subpages appear after it in a stable order, and `glossary` remains last.
- Public deep links use the deployed base and trailing slash shape `/racecraft-plugins-public/reference/<slug>/`; source files live under `docs-site/src/content/docs/reference/<slug>.*`.
- Existing docs pages that currently point readers to the generic reference landing page are updated with task-relevant deep links: install pages to manifests, skills, agents, hooks, and source-vs-dist where applicable; first-run to skills, scripts, and tests; troubleshooting to source-vs-dist, manifests, and hooks; security/trust to hooks, agents, manifests, and source-vs-dist; and contributor/release to source-vs-dist, scripts, tests, and manifests.
- Roadmap-only surfaces are folded into the seven first-class pages as sections or rows: marketplace and generated manifests under `manifests`, MCP/config where applicable under `hooks` or `manifests`, CI/release validation under `scripts`, and generated payload responsibility under `source-vs-dist`.

### Session 2026-06-17 - Generation Format And Reviewability

- Generated full page content is committed Markdown at `docs-site/src/content/docs/reference/<slug>.md`, not MDX and not browser/component-rendered data.
- Each generated page uses stable section-per-record blocks with ordered labels for purpose, platform mapping, source facts, sources, and inferred notes. Compact tables are allowed only for page navigation or summary, not as the only review surface for source facts.
- Every generated source fact record has a visible `Sources` field with repo-relative path text linked to the public GitHub `blob/main/<path>` URL. Check mode validates the repo-relative path exists locally.
- Inferred notes appear only in a dedicated `Inferred notes` field with `Based on:` source paths; inferred notes must never be mixed into source facts.
- Each generated page includes a short visible generated notice naming the generator and check command and stating that source facts and inferred notes come from checked-in files. Hidden comments may support check mode, but hidden comments are not source evidence.

### Session 2026-06-17 - Accessibility And Static Readability

- Generated reference pages use meaningful heading hierarchy for page titles, section groups, and per-record headings so dense inventories can be scanned by headings and links.
- Compact summaries, lists, or tables must have meaningful labels, headings, or table headers; they may summarize records but must not be the only review surface for source facts, sources, or inferred notes.
- Source citation links use repo-relative path text as the visible link text. Multiple or repeated citations must include distinguishing context such as a fragment, label, or record-specific suffix.
- Required generated reference content must be present in committed Markdown and rendered static HTML without relying on JavaScript-only expansion, filtering, disclosure, or client-rendered data.
- DOC-007 owns generated content structure and link-text accessibility requirements. DOC-010 still owns broader accessibility automation, responsive/browser checks, search, and CI hardening.

### Session 2026-06-17 - Validation And Handoff Boundaries

- DOC-007 adds docs-site package scripts `reference:generate` and `reference:check`. The public commands are `pnpm --dir docs-site reference:generate` and `pnpm --dir docs-site reference:check`, both wrapping `node scripts/generate-reference-pages.mjs` with `--check` for check mode.
- Local docs validation includes reference freshness: `pnpm --dir docs-site validate` runs `reference:check` before the existing Astro check/build sequence. This is local validation, not GitHub Actions wiring.
- Check mode is read-only. It exits `0` when generated output is current, exits `1` for stale generated output while listing stale pages and the `reference:generate` fix command on stdout, and exits `2` for source/parsing/internal errors while naming the source path on stderr.
- Error diagnostics distinguish stale output from source, parsing, output-write, and internal errors. Exit-`2` diagnostics must print to stderr with an error category, a repo-relative source or output path when one exists, or the failing phase when no single path applies.
- Generation must validate and render source-backed reference data in memory before writing generated reference pages. Source, parsing, or internal errors must not publish unsupported reference rows; output-write failures in generate mode exit `2` and name the generated output path.
- Recovery guidance remains local and bounded: stale output points to `pnpm --dir docs-site reference:generate`, source/parsing failures point to the named checked-in file or metadata, and internal/pathless failures point to the failing generator phase without expanding into DOC-008 troubleshooting or DOC-010 CI hardening.
- Source reads are allowlisted to checked-in repository paths: repo manifests, `speckit-pro/`, `dist/claude/`, `dist/codex/`, root scripts, `tests/speckit-pro/`, and docs-site config/content needed for navigation. Allowlist and exclusion checks use normalized repo-relative paths, not absolute checkout path segments, so a repository checked out under a parent `.worktrees/` directory is still valid.
- `.git`, repo-relative `.worktrees`, `node_modules`, user home/cache installs, network sources, user-pasted JSON, and generated `docs-site/src/content/docs/reference/*.md` output are not source evidence. The generated `docs-site/src/content/docs/reference/*.md` files are writable outputs only.
- Checked-in `dist/claude/` and `dist/codex/` files may be cited only as generated-payload inventory evidence. Authoring-source facts about plugin behavior, manifest semantics, skills, agents, hooks, scripts, or tests must cite `speckit-pro/`, repo manifests, root scripts, tests, or docs-site config/content as applicable.
- DOC-010 owns GitHub Actions/docs CI wiring, markdown/link hardening, accessibility automation, search, and broader docs validation decisions. DOC-007 must not edit `.github/workflows/*`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature MUST produce full visible committed Markdown reference subpages at `reference/skills`, `reference/agents`, `reference/manifests`, `reference/hooks`, `reference/scripts`, `reference/tests`, and `reference/source-vs-dist`.
- **FR-002**: The feature MUST preserve `docs-site/src/content/docs/reference.md` as the canonical `/reference/` landing page and orient readers to the generated subpages from that page.
- **FR-003**: Every generated reference row that states a source fact MUST include a visible `Sources` field with repo-relative path text linked to the corresponding public GitHub `blob/main/<path>` URL.
- **FR-004**: Source facts MUST come only from checked-in repository files.
- **FR-005**: Inferred notes MUST appear only in a dedicated `Inferred notes` field with `Based on:` source paths and MUST NOT be presented as direct source evidence.
- **FR-006**: Claude Code and Codex command and skill surfaces MUST be presented in parallel wherever they map to the same user or maintainer concept, and those records MUST show Claude Code invocation, Codex invocation, purpose, prerequisites, and expected output artifact when those fields are applicable and source-backed.
- **FR-007**: Runtime-specific differences between Claude Code and Codex MUST remain visible instead of being collapsed into a single generic description.
- **FR-008**: File-layout references MUST classify relevant files as source, generated payload, test-only, release infrastructure, documentation infrastructure, or other clearly named repository roles.
- **FR-009**: Manifest references MUST distinguish plugin manifests, marketplace registry files, integration manifests, and generated distribution manifests when those categories are present, and Claude Code versus Codex plugin manifest records MUST list required and optional fields separately by runtime.
- **FR-010**: Script, hook, and test references MUST describe repository role and source path without changing the referenced behavior or semantics.
- **FR-011**: The feature MUST provide deterministic generate behavior for the generated reference pages.
- **FR-012**: The feature MUST provide check behavior that detects stale generated reference pages.
- **FR-013**: Check behavior MUST be read-only, MUST NOT create, rewrite, delete, format, or update generated files, docs-site package/config files, or existing docs links, and MUST exit `0` for current output, `1` for stale output, and `2` for source/parsing/internal errors.
- **FR-014**: Generation and check behavior MUST read only allowlisted local checked-in repository paths, evaluated as normalized repo-relative paths: repo manifests, `speckit-pro/`, `dist/claude/`, `dist/codex/`, root scripts, `tests/speckit-pro/`, and docs-site config/content needed for navigation; no network access, browser-side local execution, user-pasted JSON, user-local plugin-install inspection, repo-relative `.git`, repo-relative `.worktrees`, `node_modules`, or generated reference output as source evidence is allowed.
- **FR-015**: The feature MUST NOT change plugin behavior, manifest semantics, generated payload content, marketplace behavior, install flow, hook semantics, or release automation.
- **FR-016**: Generated prose MUST remain public-readable and accessibility-scannable for users, maintainers, and agents, using stable section-per-record Markdown blocks with meaningful headings, ordered labels, visible source fields, and visible inferred-note fields instead of raw metadata dumps or wide evidence-only tables.
- **FR-017**: Generated pages MUST provide stable public links in the `/racecraft-plugins-public/reference/<slug>/` shape that later docs, troubleshooting guides, agents, and release work can cite.
- **FR-018**: The specification and later planning artifacts MUST keep DOC-008 troubleshooting/security/trust depth, DOC-009 contributor workflow depth, and DOC-010 CI hardening out of this implementation slice.
- **FR-019**: The docs sidebar MUST keep the existing Reference group, list the reference landing page first, include generated reference subpages in stable order, and keep the glossary after generated reference entries.
- **FR-020**: Every generated reference page MUST include a visible generated notice naming the generator/check command and declaring that source facts and inferred notes come from checked-in files.
- **FR-021**: The docs-site package MUST expose `reference:generate` and `reference:check`, and `validate` MUST run `reference:check` before the existing docs-site check/build sequence.
- **FR-022**: DOC-007 MUST NOT edit `.github/workflows/*`; later GitHub Actions/docs CI wiring belongs to DOC-010.
- **FR-023**: Existing install, first-run, troubleshooting, security, and contributor documentation MUST include context-specific deep links to the generated reference subpages introduced by DOC-007; links MUST point to the most relevant generated subpage for the reader's current task, and linking only to `/reference/` is insufficient when a generated subpage is more precise.
- **FR-024**: Generated reference pages MUST use a meaningful heading hierarchy for page titles, section groups, and per-record headings so readers can scan dense inventories by headings and links.
- **FR-025**: Generated lists, compact navigation summaries, and compact tables MUST have meaningful labels, headings, or table headers; they MAY summarize records but MUST NOT be the only location where source facts, sources, or inferred notes appear.
- **FR-026**: Source citation links MUST use visible, non-ambiguous link text that includes the repo-relative source path. When one record has multiple citations or repeated paths, the visible link text MUST include distinguishing context such as a fragment, label, or record-specific suffix.
- **FR-027**: Required generated reference content MUST be readable and navigable in committed Markdown and rendered static HTML without depending on JavaScript-only expansion, filtering, disclosure controls, or client-rendered data.
- **FR-028**: Generator error handling MUST classify stale generated output separately from source errors, parsing errors, output-write errors, and internal errors; missing/unreadable required sources, allowlist violations, malformed JSON, malformed or missing frontmatter, missing required metadata fields, generated-output write failures, and pathless internal failures MUST have deterministic dispositions.
- **FR-029**: Generate mode MUST collect, parse, validate, and render source-backed reference data before writing generated reference pages; source, parsing, or internal failures MUST exit `2` without publishing unsupported source facts or inferred notes, and generated-output write failures MUST exit `2` with the generated output path.
- **FR-030**: Exit diagnostics MUST be actionable: exit `1` stale-output diagnostics go to stdout with stale generated page paths and `pnpm --dir docs-site reference:generate`; exit `2` diagnostics go to stderr with an error category, a concise cause, and either the repo-relative source/output path or the failing generator phase when no single path applies.

### Reviewability Notes *(if applicable)*

- Generated reference content may be declared as generated output during planning, but source facts, inferred-note rules, generator behavior, and validation behavior remain reviewable.
- Typed reviewability exceptions are rare operator-owned overrides. Accepted classes are refactor, infra, and upgrade, but generated templates, generated zones, `.process` files, PR bodies, and code fences are not valid provenance.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: docs-site generated reference pages, link-only existing docs updates, and local docs validation
- **Projected reviewable LOC**: Approximately 430 LOC, excluding any clearly declared generated reference output
- **Projected production files**: 0 plugin/runtime production files
- **Projected total files**: Approximately 17 planned files, including seven generated reference subpages and six link-only updates to existing docs pages
- **Budget result**: within budget
- **Split decision**: Remains one spec because it is one documentation reference slice with no plugin behavior, manifest semantics, install-flow, generated payload, marketplace, hook, or release automation changes.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Reference Page**: A generated docs page for one repository surface group, such as skills, agents, manifests, hooks, scripts, tests, or source-vs-dist layout.
- **Reference Landing Page**: The preserved `/reference/` route that orients readers to generated subpages without replacing existing inbound links.
- **Reference Row**: A generated Markdown record block on a reference page that describes one surface, file, or mapping and carries ordered fields for purpose, platform mapping, source facts, visible sources, and inferred notes.
- **Command Skill Reference**: A generated record detail for command or skill surfaces that names runtime invocation forms, prerequisites, expected output artifact, and supporting source paths.
- **Manifest Field Set**: A generated record detail that separates required and optional manifest fields by runtime and manifest category without changing manifest semantics.
- **Source Fact**: A statement derived directly from a checked-in repository file and linked to that file.
- **Inferred Note**: A labeled explanatory statement derived from relationships among source facts rather than copied directly from one source file.
- **Generated Notice**: A visible statement on each generated reference page naming the generator/check command and the checked-in source boundary.
- **Runtime Surface Mapping**: The relationship between Claude Code and Codex surfaces when both runtimes expose comparable plugin concepts.
- **File Classification**: The repository role assigned to a path, such as source, generated payload, test-only, release infrastructure, or documentation infrastructure.
- **Reference Freshness Check**: A local validation result proving generated reference pages match current checked-in source files.
- **Source Allowlist**: The bounded set of normalized repo-relative checked-in repository paths the generator may read as evidence for source facts; generated reference outputs are writable targets only, and checked-in `dist/` payload files are generated-payload inventory evidence rather than authoring source-of-truth evidence.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reader can reach each generated reference subpage from `/racecraft-plugins-public/reference/` or the Reference sidebar group in no more than two navigation steps.
- **SC-002**: 100% of generated rows that state source facts include a citation link to an existing checked-in repository path.
- **SC-003**: A sampled review of generated rows confirms source facts and inferred notes are visibly separated.
- **SC-004**: Local check mode succeeds when generated reference pages are current and fails when at least one generated page is intentionally made stale.
- **SC-005**: Check mode leaves the working tree unchanged when it detects stale generated output or source/parsing/internal errors.
- **SC-006**: Review of the final diff confirms no plugin behavior, manifest semantics, generated payload content, marketplace behavior, install flow, hook semantics, or release automation changed.
- **SC-007**: Maintainers can identify the source-vs-dist responsibility for every first-class surface group named in DOC-007: skills, agents, manifests, hooks, scripts, tests, and source-vs-dist layout, and can identify Claude Code versus Codex required and optional manifest fields.
- **SC-008**: Existing install, first-run, troubleshooting, security, and contributor pages contain task-relevant links to generated reference subpages instead of relying only on the generic `/racecraft-plugins-public/reference/` landing page.
- **SC-009**: Review of all seven committed generated Markdown pages confirms dense-inventory accessibility: each page has a visible generated notice; meaningful page, section, and per-record headings; compact lists or tables have labels or headers; command/skill records expose invocation, prerequisite, and expected-output fields; manifest records separate required and optional fields by runtime; citation links expose repo-relative path text with distinguishing context for multiple citations; and required source facts, sources, and inferred notes are available without JavaScript-only interaction.
- **SC-010**: A reviewer can classify each documented generator failure as stale output, source error, parsing error, output-write error, or internal error and identify the bounded recovery action from the diagnostic.

## Assumptions

- DOC-007 starts from the existing docs-site reference shell and adds generated subpages rather than replacing the broader docs IA.
- The selected first-class generated page set is exactly seven subpages: `skills`, `agents`, `manifests`, `hooks`, `scripts`, `tests`, and `source-vs-dist`.
- Generated reference pages use committed `.md` files so diffs show the final public reference text without requiring reviewers to inspect a component render path.
- Checked-in source files are the only permitted evidence source for generated reference content.
- DOC-010 may later wire `pnpm --dir docs-site validate` and `pnpm --dir docs-site validate:links` into GitHub Actions, but DOC-007 only provides deterministic local behavior and an explicit handoff.
- DOC-008 and DOC-009 can depend on DOC-007 reference links later, but their troubleshooting, security/trust, contributor, update, rollback, and release-workflow depth stays out of this slice.
- Existing docs-page updates for DOC-007 are limited to contextual reference links and brief lead-in text; deeper troubleshooting, security/trust, contributor, update, rollback, and release-workflow procedures remain deferred to DOC-008 and DOC-009.

## Unresolved for Consensus

None.
