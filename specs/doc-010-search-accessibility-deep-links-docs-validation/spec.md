# Feature Specification: Search, Accessibility, Deep Links, Docs Validation

**Feature Branch**: `doc-010-search-accessibility-deep-links-docs-validation`

**Created**: 2026-06-18

**Status**: Draft

**Input**: User description: "Search, accessibility, deep links, docs validation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find And Share Support Guidance (Priority: P1)

First-time Claude Code and Codex users, support responders, and maintainers can search existing documentation, browse glossary-style entries, and share stable links to install, troubleshooting, reference, and release workflow content.

**Why this priority**: Findability and stable support links are the core value of the hardening slice; without them, the interactive docs remain difficult to support and easy to drift.

**Independent Test**: Can be tested by opening the existing documentation site, searching for install, recovery, glossary, reference, and release topics, then copying deep links and confirming they resolve to the intended content.

**Acceptance Scenarios**:

1. **Given** a user needs install or recovery help, **When** they search or browse the docs site, **Then** the relevant existing support content is discoverable without visiting a new docs-quality route.
2. **Given** a support responder links to a glossary term or reference section, **When** another user opens that link, **Then** the page lands on the intended anchored content.
3. **Given** a heading or glossary anchor changes, **When** docs validation runs, **Then** stale or broken deep links are reported before review.

---

### User Story 2 - Use Interactive Aids Accessibly (Priority: P2)

Keyboard and screen-reader users can use the interactive install and lifecycle documentation aids, or their static fallbacks, without depending on inaccessible dynamic behavior.

**Why this priority**: The existing interactive documentation cannot be considered hardened if primary learning aids exclude keyboard or assistive technology users.

**Independent Test**: Can be tested by navigating the interactive aids with a keyboard and screen-reader-oriented inspection, then disabling or bypassing dynamic behavior to verify the fallback content still communicates the same guidance.

**Acceptance Scenarios**:

1. **Given** a keyboard-only user opens an interactive aid, **When** they tab through controls and content, **Then** focus order is predictable, focus is visible, and all meaningful actions are reachable.
2. **Given** a screen-reader user reaches the same aid, **When** labels and state are announced, **Then** each control and result has a meaningful accessible name and relationship.
3. **Given** dynamic behavior is unavailable, **When** the user reads the page fallback, **Then** the same install or lifecycle guidance remains available in static content.

---

### User Story 3 - Run One Matching Docs Validation Path (Priority: P3)

Maintainers and contributors can run one local docs validation path and see the corresponding PR Checks docs gate react only to docs-site, generated-reference source, or docs-validation contract changes.

**Why this priority**: A single documented validation path reduces review friction and keeps documentation drift from becoming a manual review burden.

**Independent Test**: Can be tested by running the local docs validation command, then confirming the conditional PR Checks docs gate uses job-level changed-file detection for the relevant docs validation surface while leaving the plugin test matrix semantics unchanged.

**Acceptance Scenarios**:

1. **Given** a contributor changes docs-site content, **When** they run the local validation path, **Then** generated reference checks, site checks, build/link validation, safe-aids validation, and minimal browser smoke are covered together.
2. **Given** a docs-site change opens a PR, **When** PR Checks evaluate changed paths, **Then** the docs job runs conditionally and reports the same validation categories.
3. **Given** a plugin-only change opens a PR, **When** PR Checks evaluate changed paths, **Then** the existing plugin test matrix semantics are not changed by DOC-010.

---

### User Story 4 - Review Minimal Browser Evidence (Priority: P4)

Reviewers can inspect compact browser smoke evidence for key existing docs routes across desktop and mobile without reviewing a broad visual snapshot suite.

**Why this priority**: Browser evidence helps reviewers trust interactive docs behavior, but the evidence must stay small enough to review within the slice budget.

**Independent Test**: Can be tested by reviewing the smoke output for the selected route set and confirming that desktop and mobile viewports cover navigation, search/deep-link reachability, and interactive aid usability.

**Acceptance Scenarios**:

1. **Given** a reviewer opens the PR evidence, **When** they inspect browser smoke results, **Then** they see key routes covered on both desktop and mobile.
2. **Given** the smoke route set grows beyond the agreed budget, **When** scope is reduced, **Then** route coverage is reduced before the feature is split.

### Edge Cases

- A heading or glossary term is renamed after support links have been shared.
- A generated reference page changes structure and silently removes an anchor.
- Search indexes content but returns stale or low-signal results for install, recovery, troubleshooting, or release questions.
- Interactive aids render in narrow viewports where labels, focus rings, or control groups could overlap.
- Dynamic behavior fails or is disabled, leaving only static fallback content.
- CI runs on changes that do not touch docs-site files and must not trigger a new docs job.
- Validation encounters commands that would require network access, live plugin installation, destructive actions, or local user files.
- Automated validation encounters install, recovery, cleanup, marketplace, or credentialed guidance that would mutate a machine, call a live service, require credentials, inspect local user state, or rely on hidden permission grants.
- Manifest, payload, generated-reference, log, smoke artifact, or PR packet evidence could expose local absolute paths, secrets, tokens, environment values, browser profile state, or user-specific filesystem details.
- Browser smoke encounters external platform links, marketplace links, analytics, telemetry, or production-only navigation that cannot be proven from the configured local docs preview.
- External platform behavior changes after the docs make a source-backed claim.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The docs site MUST retain the existing documentation stack and built-in search path; DOC-010 MUST NOT replace the current search system or add a new top-level docs-quality route.
- **FR-002**: Existing support-heavy pages MUST define stable heading and deep-link conventions for install, recovery, troubleshooting, glossary, generated reference, and release workflow content.
- **FR-003**: Glossary terms and generated reference sections MUST expose shareable anchors that remain stable unless an intentional source update records the change.
- **FR-004**: Users MUST be able to find install, recovery, troubleshooting, reference, and release workflow guidance from existing docs-site navigation, search, or linked sections.
- **FR-005**: `SafeInstallAids.astro` MUST preserve or improve keyboard navigation, visible focus, labels, native or semantic controls, accessible status announcements for selector and copy-result changes, contrast, static fallback content, and responsive behavior.
- **FR-006**: `LifecycleFlow.astro` MUST preserve or improve keyboard navigation, visible focus, labels, native or semantic HTML before custom ARIA patterns, contrast, static fallback content, and responsive behavior.
- **FR-007**: Existing docs-site validators MUST be extended to cover generated reference checks, deterministic internal link and anchor validation, site checks, build/link validation, safe-aids validation, and minimal browser smoke without creating a broad new validation framework.
- **FR-008**: The docs-site package scripts MUST provide one local docs validation path that runs the full DOC-010 validation set and focused subcommands where useful.
- **FR-009**: PR Checks MUST include a stable docs validation gate that uses job-level changed-file detection rather than workflow-level path filters, preserves existing plugin test matrix semantics, distinguishes rendered docs-site changes, generated-reference source changes, and docs-validation contract changes, and ensures docs-site-only PRs do not force unrelated plugin matrix jobs unless those PRs also touch plugin or generated-reference source inputs.
- **FR-010**: Browser smoke coverage MUST remain minimal, cover the logical route set `/`, `/choose-your-path/`, `/spec-kit-lifecycle/`, `/glossary/`, `/reference/skills/`, and `/contribute-and-release/`, and include both mobile and desktop viewports while relying on the Playwright base URL for the deployed `/racecraft-plugins-public` path prefix.
- **FR-011**: Automated validation MUST avoid networked, destructive, live plugin install, browser-side local command execution, and local-user-file inspection commands unless such actions are explicitly documented as manual-only.
- **FR-012**: Documentation that makes external platform claims MUST include source-update guidance so future changes become explicit maintenance work rather than stale assertions.
- **FR-013**: Reviewer-facing evidence MUST connect changed docs-site surfaces to validation output, browser smoke coverage, the 7-day-retention `docs-site-smoke-evidence` artifact, manual accessibility review notes, known gaps, and rollback or fallback notes.

### Validation Safety Boundaries

- Automated DOC-010 validation MUST use checked-in repository sources, generated docs output, and the local docs-site preview as inputs. It MUST NOT read local user files, user JSON/config/cache, browser profiles, environment secrets or values, or user-supplied payloads, and it MUST NOT request or rely on hidden permission grants.
- Command snippets, install guidance, rollback guidance, manifest references, payload references, and generated-reference facts MUST be validated by source-backed static inspection and copyable-guidance review only. Automated validation MUST NOT execute copyable commands, browser-side local commands, live plugin or marketplace installs, destructive cleanup, or local machine inspection.
- Playwright smoke MUST be limited to the configured docs-site baseURL, the six logical DOC-010 routes, sampled internal links, and local preview or build artifacts. It MUST NOT submit analytics or production telemetry, follow unintended external navigation, execute install flows, or use production services to prove claims.
- Validation output, logs, smoke artifacts, and PR packet evidence MUST use repo-relative paths and actionable source references. They MUST avoid local absolute paths, secrets, tokens, environment values, user-specific filesystem details, browser profile state, and broad unrelated browser artifacts.
- Manual-only actions MUST be labeled as manual-only and MUST NOT be implied as CI execution. Copy buttons and selectors expose guidance text only and do not create an automated execution contract.
- If a command snippet, manifest field, payload value, generated-reference claim, or external-platform assertion cannot be verified from checked-in source without local user state, user JSON, credentials, or networked marketplace behavior, validation MUST fail with a sanitized repo-relative remediation message or require a documented manual-only/source-update exception.
- The `validate-docs` PR gate MUST preserve existing plugin test semantics and docs-only scope. Docs-site-only PRs MUST NOT require new workflow permissions, credentials, secrets, marketplace access, plugin runtime execution, or plugin-matrix fan-out unless the PR also changes plugin or generated-reference source inputs covered by existing semantics.

### Support Anchor Inventory Scope

DOC-010 defines support-ready anchors by owning page family and support purpose, not by freezing every generated Starlight slug in the spec.

The anchor inventory scope is:

- **Install guidance**: `/install/claude-code/`, `/install/codex/`, and `/choose-your-path/` sections for install decisions, source/payload/cache separation, install path matrices, verification, stale update checkpoints, install safety, selector results, and static fallback links.
- **Recovery and troubleshooting**: `/troubleshooting/` and `/update-and-rollback/` sections for symptom matrix entries, read-only inspection boundaries, recovery cases, stale cache, rollback, and version sync.
- **Generated reference**: `/reference/` and generated `/reference/**` pages, especially `/reference/skills/`, including generated record headings, command or skill reference sections, prerequisites, source facts, and inferred notes.
- **Glossary**: `/glossary/` terms for marketplace, payload, source tree, skill, agent, hook, cache, constitution, lifecycle, and other DOC-010 support terms.
- **Release workflow**: `/contribute-and-release/` sections for source of truth, change type matrix, contributor path, release readiness, version fields, release automation, PR Checks behavior, and final checklist.

Scope rules:

- Designated support-heavy headings, glossary terms, troubleshooting entries, generated reference records, and release workflow sections MUST expose stable shareable anchors or document an intentional exception.
- Generated reference anchors are owned by the generator and `reference:check` validation.
- Renamed or removed anchors MUST include an intentional source update, redirecting link update, or documented exception.
- Deterministic docs validation owns complete internal link and anchor coverage; Playwright samples representative deep links only.

### Browser Smoke Route Rationale

The six DOC-010 smoke routes are representative critical journeys, not an exhaustive page crawl:

| Route | Critical journey represented |
|-------|------------------------------|
| `/` | Entry, platform choice, and search start point for install, reference, and release guidance. |
| `/choose-your-path/` | Install path selection, `SafeInstallAids` interaction, copyable guidance, and static fallback links. |
| `/spec-kit-lifecycle/` | Lifecycle and gate understanding, `LifecycleFlow` content, platform action comparison, and fallback readability. |
| `/glossary/` | Support terminology discovery and shareable glossary anchors. |
| `/reference/skills/` | Representative generated reference page with source-cited records and stable generated anchors. |
| `/contribute-and-release/` | Maintainer and contributor release workflow, PR evidence, validation, and rollback-oriented support content. |

This route set stays small because it covers entry/search, install selection, lifecycle guidance, glossary terms, generated reference behavior, and release workflow evidence. Install, troubleshooting, and recovery pages remain in the full support-anchor validation scope, but Playwright only samples representative links and interactions.

### Reviewability Notes *(if applicable)*

- This feature is a docs-site and docs-process hardening slice. It may touch content, validation scripts, workflow configuration, and the existing interactive docs components, but it must not change plugin runtime behavior.
- If scope pressure appears, reduce browser smoke route coverage before splitting the feature.
- No typed reviewability exception is expected.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process
- **Secondary surfaces, if any**: UI, harness/adapter
- **Projected reviewable LOC**: 275-395 excluding generated or lockfile churn
- **Projected production files**: 0-6
- **Projected total files**: 6-10
- **Budget result**: within budget
- **Split decision**: Remains one spec because it is the final docs hardening slice and the route coverage is intentionally minimal. If the budget tightens, route coverage is reduced before creating a follow-up spec.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Browser and manual accessibility evidence MUST be recorded in existing reviewer-visible PR packet sections, including `How To UAT`, `Verification`, traceability, and `Known Gaps` when applicable.
- PR packet evidence MUST include an automation-safety note listing validation commands run and confirming that command snippets and copyable guidance were statically inspected rather than executed.
- PR packet evidence MUST confirm that automated validation did not use live plugin or marketplace installs, destructive cleanup, browser-side local commands, local user files, user JSON/cache, environment secrets or values, hidden permission grants, analytics, or production telemetry.
- Browser smoke evidence MUST summarize the compact `docs-site-smoke-evidence` artifact, including routes, viewports, included report/screenshot/trace files, retention, and confirmation that artifacts omit local absolute paths, sensitive values, user-specific state, and unrelated broad browser captures.
- Validation findings shown in the PR packet MUST use repo-relative source references and sanitized messages suitable for reviewer-visible evidence.
- Deferred work MUST name the follow-up spec or issue.

### Accessibility Review Requirements

- Interactive aid controls MUST use native HTML controls where they satisfy the interaction need; any custom control pattern MUST document its role, name, state, keyboard operation, and fallback relationship.
- `SafeInstallAids.astro` MUST expose changed selector guidance and copy-result outcomes as visible text and programmatically determinable polite status updates without moving focus.
- Manual review MUST check that focus indicators remain visible and unclipped, text and meaningful control indicators retain sufficient contrast, and non-excepted content reflows without overlapped labels or required two-dimensional scrolling on both desktop and mobile-sized layouts.
- Tables, command blocks, and generated reference content MAY use contained horizontal scrolling where their structure requires it, but surrounding prose, labels, controls, and individual readable content MUST remain usable in one scrolling direction.
- Automation MAY provide guardrails for labels, status regions, focus targets, fallback content, smoke routes, and link/anchor drift; it MUST NOT be described as proving full accessibility conformance.

### Key Entities *(include if feature involves data)*

- **Documentation Page**: An existing docs-site page that contains install, recovery, troubleshooting, reference, glossary, or release workflow guidance.
- **Deep Link Anchor**: A stable link target for a heading, glossary term, troubleshooting entry, generated reference section, or release workflow detail.
- **Interactive Aid**: An existing documentation component that helps users understand safe installation or lifecycle flow behavior.
- **Static Fallback**: Non-dynamic content that preserves the same guidance when interactivity is unavailable or inaccessible.
- **Validation Path**: The local and PR Checks docs validation sequence that protects generated references, links, accessibility requirements, safe aids, and browser smoke coverage.
- **Generated Reference Source Input**: A non-`docs-site/**` repository file or directory read by generated reference or safe-aids validation, such as plugin manifests, skill or agent definitions, hooks, scripts, tests, README files, or generated distribution manifest files.
- **Browser Smoke Evidence**: Compact route and viewport evidence that demonstrates key docs interactions remain usable on desktop and mobile.
- **External Platform Claim**: A documentation assertion about Claude Code, Codex, marketplaces, search behavior, PR Checks, or release tooling that requires source-update guidance.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of DOC-010-designated support-heavy headings, glossary terms, generated reference sections, troubleshooting entries, and release workflow details have stable links or an intentional documented exception.
- **SC-002**: A user can locate install, recovery, troubleshooting, reference, and release workflow guidance from existing docs navigation, search, or shared links in no more than three meaningful interactions per topic.
- **SC-003**: Keyboard-only review of the interactive aids can complete every primary action with visible, unclipped focus and without pointer-only behavior on both desktop and mobile-sized layouts.
- **SC-004**: Static fallback review confirms that each interactive aid preserves the essential install or lifecycle guidance when dynamic behavior is unavailable.
- **SC-005**: One local docs validation command covers generated reference checks, site checks, build/link validation, safe-aids validation, and minimal browser smoke; PR Checks expose one stable docs validation gate that runs full docs-site validation for rendered docs changes and reference drift validation for generated-reference source changes. Reviewers can also verify from local or CI output that automated validation stayed within checked-in source and local preview boundaries and did not execute snippets, inspect local user files, inspect user JSON, read environment secrets, perform live installs, run destructive commands, execute browser-side local commands, or request hidden permission grants.
- **SC-006**: Minimal browser smoke evidence covers the six DOC-010 logical routes across desktop and mobile viewports, with one search smoke from `/`, sampled representative deep links, focused interactive checks on `/choose-your-path/` and `/spec-kit-lifecycle/`, and no broad visual snapshot suite. Smoke evidence remains limited to compact `docs-site-smoke-evidence` artifacts that omit local absolute paths, sensitive values, user-state traces, and unrelated broad browser artifacts.
- **SC-007**: 100% of external platform claims touched by DOC-010 include source-update guidance or are removed if no supportable source-update path exists.

## Assumptions

- Existing docs-site routes already contain the install, troubleshooting, reference, glossary, and release workflow content to harden.
- Existing Starlight search remains the search experience, and this feature improves findability through content, anchors, and validation rather than replacing search.
- The Playwright smoke script is `validate:smoke`; it is included in `pnpm --dir docs-site validate`, and Playwright configuration handles CI-specific reporter/artifact behavior.
- The stable PR Checks docs job or gate name is `validate-docs`.
- CI uploads one compact smoke artifact named `docs-site-smoke-evidence` with 7-day retention; screenshots and reports are review artifacts and are not committed.
- Browser smoke uses logical Starlight routes while Playwright configuration owns the deployed base path, including `/racecraft-plugins-public`.
- Deterministic docs validation owns full internal link and anchor coverage; Playwright samples representative deep links instead of visiting every support anchor.
- Automated search smoke starts from `/` with high-value terms such as install, release, or reference and asserts at least one known result link.
- Accessibility smoke focuses on `SafeInstallAids` behavior on `/choose-your-path/` and `LifecycleFlow` static or reflow content on `/spec-kit-lifecycle/`; broader accessibility and responsive judgment remains manual reviewer evidence.
- The docs-site package already uses `pnpm`, and DOC-010 keeps local validation inside the docs-site package boundary where applicable.
- PR Checks can conditionally detect docs-site, generated-reference source, and docs-validation contract file changes without changing plugin runtime tests.
- PR Checks keep the workflow triggered for all pull requests and use job-level conditions so required checks do not remain pending because of workflow-level path filtering.
- Generated-reference source detection is maintained as the real transitive input list for `reference:check` and safe-aids validation; it is not a broad all-docs or all-process glob.
- Minimal browser smoke is sufficient reviewer evidence for this slice; full visual regression and complete accessibility certification remain out of scope.
- Live plugin install tests, analytics, browser-side local command execution, and local user JSON inspection remain out of scope for automated validation.
