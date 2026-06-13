# Feature Specification: Static docs framework and IA spike

**Feature Branch**: `doc-001-static-docs-framework-and-ia-spike`

**Created**: 2026-06-12

**Status**: Draft

**Input**: User description: "Racecraft needs a static documentation site, but the repository currently has no docs-site package, config, lockfile, or hosting decision. DOC-001 selects the site stack and IA foundation before DOC-002 creates the shell."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review the framework recommendation (Priority: P1)

As a maintainer, I can review one source-backed recommendation for the docs framework and understand why the alternatives were rejected.

**Why this priority**: Maintainers need to approve the dependency and hosting direction before any docs-site package or shell is created.

**Independent Test**: A reviewer opens the spike report and verifies that exactly one default stack is recommended, that each rejected alternative has a rationale, and that every conclusion is backed by current source evidence.

**Acceptance Scenarios**:

1. **Given** the repository has no docs-site package, config, lockfile, or hosting decision, **When** a maintainer reviews the spike report, **Then** the report identifies one recommended default stack for DOC-002 unless it records a hard blocker.
2. **Given** Docusaurus/MDX, VitePress, Astro/Starlight, and the repo-native fallback are compared, **When** a maintainer reviews the comparison, **Then** each non-selected option has a clear rejection rationale tied to the evaluation criteria.

---

### User Story 2 - Handoff IA and commands to DOC-002 (Priority: P2)

As the DOC-002 implementer, I have a concrete IA skeleton and minimum package, build, and test commands for the selected stack.

**Why this priority**: DOC-002 should be able to create the docs-site shell without reopening stack selection or top-level IA decisions.

**Independent Test**: A DOC-002 implementer can use only the spike report to identify the top-level documentation routes, the Diataxis mode for each route, the intended audience, source evidence, success criteria, recommended package manager, and minimum command set.

**Acceptance Scenarios**:

1. **Given** DOC-002 is ready to create the docs-site shell, **When** the implementer reads the IA section, **Then** every top-level route includes its route path, Diataxis mode, audience, source evidence, and success criterion.
2. **Given** the selected stack determines the package manager, **When** the implementer reads the command section, **Then** the report lists the minimum package, build, and test commands needed for the selected stack.

---

### User Story 3 - Confirm research-only scope (Priority: P3)

As a reviewer, I can confirm the spike did not introduce site scaffolding, package files, or plugin behavior changes.

**Why this priority**: DOC-001 must remain a bounded research spike so DOC-002 owns site creation and behavior changes.

**Independent Test**: A reviewer inspects the diff and verifies the only implementation output is the research report and SpecKit planning artifacts, with no docs-site scaffold or runtime behavior changes.

**Acceptance Scenarios**:

1. **Given** the spike is complete, **When** a reviewer inspects changed files, **Then** there are no new or modified package files, lockfiles, site config files, prototype components, CI files, marketplace files, plugin behavior files, or README migration changes.
2. **Given** the spike report recommends a stack, **When** a reviewer checks the repository, **Then** the recommendation is documented only as research and does not create or configure the docs site.

---

### Edge Cases

- If live framework or platform source documentation is temporarily unavailable, the report must record the gap, avoid relying on stale unsupported claims, and use the best available official or primary source evidence.
- If every candidate has a hard blocker for GitHub Pages hosting from this repository, the report must record the blocker and recommend the least risky fallback instead of forcing a preferred framework.
- If a candidate supports an evaluation criterion only through third-party plugins or paid services, the report must distinguish that support from built-in or first-party support.
- If source evidence conflicts across framework or platform docs, the report must prefer the most current official source and note the conflict.
- If an IA route lacks enough source evidence or a measurable success criterion, the route must be revised or omitted from the top-level skeleton.

## Requirements *(mandatory)*

### Clarifications

- Hard blockers before weighted scoring are GitHub Pages hosting from this repository, rich MDX or equivalent reusable-component interactivity, an accessible static or keyboard-usable fallback path, and the DOC-001 no-implementation boundary.
- Search and link checking are high-weight tradeoffs; versioning is a medium/future tradeoff; accessibility support is a hard blocker only if the stack prevents accessible fallback behavior.
- Candidate support must distinguish built-in, official, official third-party hosted, community, community plugin listed by official docs, external/manual, and unsupported capabilities.
- Portfolio alignment is a strategic maintainability factor because the upcoming Racecraft Systems website and Focusengine product website are expected to use Astro.
- Maintenance burden is a scoring penalty and tie-breaker after blockers are satisfied.
- The repo-native fallback must be evaluated seriously, but selected only if framework candidates are blocked or introduce unacceptable risk for this repository.
- If DOC-002 finds a hard blocker for Astro/Starlight GitHub Pages deployment, it must record the blocker and follow the fallback order in the report: Astro/Starlight configuration fix if feasible, Docusaurus/MDX, VitePress, then repo-native Markdown fallback.
- Configuration-only GitHub Pages failures, such as base path, trailing slash, workflow, or package-script naming issues, are not stack-selection failures if Astro/Starlight still satisfies the hard blockers.
- Each IA route record must include `route_path`, `route_label`, `diataxis_mode`, optional `secondary_modes`, `target_audience`, `route_purpose`, `source_evidence`, `success_criterion`, `shell_owner_doc`, and `full_content_owner_doc`.
- The IA skeleton must cover these 11 PRD route labels: Start, Install: Claude Code, Install: Codex, First Run, Choose Your Path, Reference, Troubleshooting, Security & Trust, Contribute & Release, Spec Kit Lifecycle, and Glossary.
- Each route has one primary Diataxis mode from Tutorial, How-to, Reference, or Explanation; mixed routes may name secondary modes when the route purpose requires them.
- Each route's source evidence must cite at least one local artifact or official URL with a short evidence note; current platform or framework claims in the spike report must include retrieval date.
- DOC-002 is the shell owner for the IA skeleton; `full_content_owner_doc` must name the later DOC spec or specs that own detailed content.
- DOC-001 may write only `docs/ai/research/interactive-documentation-framework-spike.md` plus normal SpecKit artifacts under `specs/doc-001-static-docs-framework-and-ia-spike/**` and `docs/ai/specs/.process/DOC-001-*`.
- PRD, roadmap, design concept, README, plugin README, marketplace, generated payload, package, lockfile, site config, prototype component, CI, and plugin behavior files are source inputs or later-spec surfaces, not DOC-001 implementation targets.
- Package manager, build, and test commands are report-only recommendations in DOC-001; conflicting evidence or hard blockers are recorded in the report with fallback recommendation and no prototype or scope expansion.
- Package/build/test commands are command roles in DOC-001. DOC-002 owns actual package scripts after scaffolding and must normalize or document any script-name differences.
- Search availability and package-manager preference are not hard blockers unless they create unacceptable dependency, cost, policy, or maintainership risk.

### Functional Requirements

- **FR-001**: The spike MUST produce one source-backed comparison of Docusaurus/MDX, VitePress, Astro/Starlight, and a repo-native fallback.
- **FR-002**: The comparison MUST evaluate each candidate for static hosting, GitHub Pages support, MDX or equivalent reusable-component interactivity, search, versioning, accessibility, link checking, docs-as-code workflow, maintenance load, package/build/test commands, and support class for each capability.
- **FR-003**: The spike MUST refresh live framework and platform source documentation during research, record follow-up evidence when the recommendation changes, and preserve enough source evidence for reviewers to validate the recommendation.
- **FR-004**: The spike MUST recommend one default stack for DOC-002 unless a hard blocker is recorded.
- **FR-005**: The spike MUST explain why each non-selected alternative was rejected or deferred.
- **FR-006**: The spike MUST identify the package manager recommended by the selected stack and list the minimum package, build, and test commands for DOC-002.
- **FR-007**: The spike MUST draft a Diataxis IA skeleton for the docs site.
- **FR-008**: Each top-level IA route MUST include route path, route label, primary Diataxis mode, optional secondary modes, target audience, route purpose, source evidence, success criterion, shell owner DOC, and full content owner DOC.
- **FR-009**: The spike result MUST be written to `docs/ai/research/interactive-documentation-framework-spike.md`.
- **FR-010**: Completion evidence MUST show that DOC-001 did not add or modify package files, lockfiles, site config, prototype components, CI files, README or plugin README migration, marketplace files, generated payload files, or plugin behavior.
- **FR-011**: The spike MUST leave docs-site implementation, README migration, interactive widgets, and docs CI creation out of scope for DOC-001 and defer that work to DOC-002 or later work.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: N/A
- **Projected reviewable LOC**: 200-450 lines, excluding generated or unchanged template content
- **Projected production files**: 1 research report; 0 production code files
- **Projected total files**: 3-5 files, including SpecKit artifacts and the research report
- **Budget result**: within budget
- **Split decision**: This remains one research spike because it selects a docs framework and IA foundation without implementation changes. DOC-002 owns shell creation and any docs-site files.
- **Exception provenance, if any**: N/A

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.

### Key Entities *(include if feature involves data)*

- **Framework Candidate**: A docs-site option under evaluation, including Docusaurus/MDX, VitePress, Astro/Starlight, and the repo-native fallback.
- **Evaluation Criterion**: A comparison dimension reviewers need to approve or reject a candidate, such as hosting, interactivity, search, versioning, accessibility, link checking, workflow fit, maintenance load, and commands.
- **IA Route**: A proposed top-level documentation path with route label, primary Diataxis mode, optional secondary modes, target audience, route purpose, source evidence, success criterion, `shell_owner_doc`, and `full_content_owner_doc`.
- **Spike Report**: The research artifact that records evidence, comparison, recommendation, IA skeleton, commands, non-goals, and verification scope.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The report covers all 4 required candidate stacks across at least 10 required evaluation dimensions.
- **SC-002**: A maintainer can identify the recommended stack and the rejection rationale for every alternative in under 5 minutes.
- **SC-003**: The IA skeleton includes no placeholder values and provides every required route field, including later content ownership, for every top-level route.
- **SC-004**: A DOC-002 implementer can identify the recommended package manager plus minimum package, build, and test commands without consulting files outside the spike report.
- **SC-005**: A reviewer can verify from the final diff that 0 package files, lockfiles, site config files, prototype components, CI files, README or plugin README migration files, marketplace files, generated payload files, or plugin behavior files were changed by DOC-001.
- **SC-006**: The report records refreshed source evidence for framework and platform claims with retrieval dates matching the initial spike and any later decision update.

## Assumptions

- GitHub Pages is the required baseline hosting target for the selected stack.
- The repo-native fallback means continuing repository-native Markdown documentation without a dedicated docs-site framework or shell.
- DOC-001 starts from a repository state with no docs-site package, config, lockfile, or hosting decision.
- DOC-002 will create the docs-site shell after this spike is accepted.
- Any framework-specific package manager recommendation belongs in the research report and does not authorize DOC-001 to create package files or lockfiles.
- DOC-001 records the selected stack's recommended package manager and commands, but does not standardize repository tooling.
- PRD, roadmap, design concept, README, and plugin documentation corrections discovered during DOC-001 are follow-up work unless a separate explicit scope amendment is made.
