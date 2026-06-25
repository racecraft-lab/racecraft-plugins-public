# Feature Specification: SEO and AI Discoverability

**Feature Branch**: `doc-014-seo-and-ai-discoverability`

**Created**: 2026-06-25

**Status**: Draft

**Input**: User description: "Make the docs site discoverable by classic search and AI answer/coding engines before public launch: crawler-access policy, agent-readable content (whole-site and per-page), correct page metadata and structured data, per-page social cards, a git-accurate freshness signal, and a documented success metric — while the site is still on its noindex'd staging URL."

## User Scenarios & Testing *(mandatory)*

<!--
  User stories are prioritized as independently testable journeys. P1 is the
  minimum viable discoverability slice; each later story adds a distinct
  discovery surface and can be verified on its own.
-->

### User Story 1 - Citation crawler can fetch any page (Priority: P1)

An answer-engine citation crawler (the user-agents ChatGPT Search, Perplexity, Claude, and similar use to fetch pages they cite) requests any documentation page. The site's crawler-access policy explicitly permits the citation tier, so the crawler is allowed to read the page and can cite it.

**Why this priority**: Answer-engine citation is the headline goal of the feature. Without an explicit allow for the citation tier and a discoverable sitemap, no other discoverability work can pay off — a page that cannot be fetched cannot be cited or indexed. This is the smallest change that makes the site meaningfully discoverable.

**Independent Test**: Fetch the published crawler-access policy and confirm each named citation-tier user-agent is permitted and the sitemap location is advertised. Can be fully tested by reading the policy file and the sitemap reference without any other part of the feature in place.

**Acceptance Scenarios**:

1. **Given** the crawler-access policy is published at the site root, **When** a citation-tier user-agent (e.g., the OpenAI search/citation agent, the Perplexity citation agent, the Claude citation/user agent) evaluates it, **Then** that user-agent is allowed to fetch every content page.
2. **Given** the crawler-access policy is published, **When** any crawler reads it, **Then** it advertises the absolute location of the sitemap.
3. **Given** a default (unnamed) crawler with no specific rule, **When** it evaluates the policy, **Then** it is allowed to fetch content pages.

---

### User Story 2 - AI training crawler can fetch any page (Priority: P2)

An AI-training crawler (the user-agents that gather content for model training, e.g., GPTBot, Google-Extended, CCBot, anthropic-ai, ClaudeBot) requests any documentation page. The site takes a deliberate max-discoverability posture and permits the training tier, increasing the chance the project appears in base-model knowledge.

**Why this priority**: For a free, open-source developer tool, base-model familiarity is plausible upside at no cost to citation (training and citation crawlers are separate user-agents, so allowing training does not change citation behavior). This is a deliberate divergence from the sibling marketing site, which blocks the training tier. It ranks below P1 because citation access is the primary lever and training access is additive.

**Independent Test**: Fetch the crawler-access policy and confirm each named training-tier user-agent is permitted. Can be tested by reading the policy file alone.

**Acceptance Scenarios**:

1. **Given** the crawler-access policy is published, **When** a training-tier user-agent (GPTBot, Google-Extended, CCBot, anthropic-ai, ClaudeBot) evaluates it, **Then** that user-agent is allowed to fetch every content page.
2. **Given** the policy documents its posture, **When** a maintainer reviews it, **Then** the allow-training decision is recorded as deliberate (so a future maintainer does not "fix" it back to a blocking default).

---

### User Story 3 - Coding agent retrieves whole-site and single-page content (Priority: P2)

A coding agent (e.g., Cursor, Claude Code, Copilot) needs the documentation as agent-readable text. It can retrieve a whole-site digest for broad context and a single page cheaply for targeted lookups, without scraping rendered HTML.

**Why this priority**: This product's documentation is itself consumed by coding agents, so agent-readable retrieval is squarely on-target. It is the one surface the whole-site digest and per-page text variant measurably serve. It ranks at P2 because classic and answer-engine discoverability (P1) is the launch-blocking concern; agent retrieval is high-value but additive.

**Independent Test**: Request the whole-site digest endpoints and a per-page text variant and confirm each returns the corresponding documentation content as plain text/Markdown. Can be tested by fetching those URLs directly.

**Acceptance Scenarios**:

1. **Given** the site is built, **When** an agent requests the whole-site digest, **Then** a concise index digest and a full-content digest are available as plain text.
2. **Given** the site is built, **When** an agent requests the per-page text variant for a content page, **Then** that single page's content is returned as plain text/Markdown at a distinct, fetchable URL.
3. **Given** a content page exists in the rendered site, **When** its per-page text variant is requested, **Then** the variant's content corresponds to the rendered page (no orphaned or missing pages).

---

### User Story 4 - Search engine reads correct metadata for every page (Priority: P1)

A classic search engine (and the structured-data consumers behind rich results) crawls a content page and finds a meta description, a canonical URL, a structured-data entity graph, and a freshness date that reflects the page's real last change.

**Why this priority**: Meta descriptions, canonical URLs, an entity graph, and an accurate freshness signal are the table-stakes metadata that make pages eligible for good search presentation and rich results. Today zero pages have descriptions, so this is foundational, not incremental — it shares P1 with citation access because both are launch-blocking baselines.

**Independent Test**: Crawl each content page and confirm it has a non-empty meta description, a canonical URL, the expected structured-data entities, and a freshness date sourced from the page's real change history. Can be tested per page from rendered output plus the sitemap.

**Acceptance Scenarios**:

1. **Given** any content page, **When** it is rendered, **Then** it carries a non-empty, page-appropriate meta description.
2. **Given** any content page, **When** it is rendered, **Then** it carries exactly one canonical URL (no duplicate canonical links).
3. **Given** the site, **When** a structured-data consumer reads it, **Then** it finds an Organization entity (linked to the project's source-host organization), a WebSite entity, a software-application entity on each plugin page describing it as free, and an author/Person entity.
4. **Given** the sitemap, **When** a search engine reads a page's last-modified date, **Then** that date reflects the page's real last change (its source change history), not the build time; a page MAY pin its own date explicitly.
5. **Given** a content page, **When** it is rendered, **Then** a visible "last updated" date is shown that matches the freshness signal.

---

### User Story 5 - Shared page renders a social card (Priority: P3)

A human shares a specific documentation page on a social platform. The shared link renders a per-page social preview card titled for that page, not a single generic site-wide image.

**Why this priority**: Per-page social cards improve share quality when individual doc pages are posted, which aids human-driven discovery. It ranks P3 because social cards are a share-quality nicety, not a discoverability gate — search and answer-engine access (P1) and agent retrieval (P2) deliver the core value first.

**Independent Test**: Request the social-card image for a content page and confirm a card titled for that page is produced. Can be tested by fetching the per-page card reference and image from rendered output.

**Acceptance Scenarios**:

1. **Given** any content page, **When** it is rendered, **Then** it references a social preview image specific to that page.
2. **Given** a content page, **When** its social card is generated, **Then** the card is titled/labelled for that page.

---

### User Story 6 - Maintainer can verify the discoverability goal (Priority: P3)

A maintainer wants to know whether the "AI-discoverable" goal is being met. The repository documents what "AI-discoverable" means and where it is measured, so the goal is verifiable rather than vague.

**Why this priority**: A goal with no written definition and no measurement source cannot be verified, which would leave the feature's own headline objective unfalsifiable. It ranks P3 because it is documentation of intent (no runtime behavior) and depends on post-launch analytics that this feature does not activate — but the definition must exist now so the goal is meaningful.

**Independent Test**: Read the documented success metric and confirm it defines the "AI-discoverable" measure and names the measurement source(s). Can be tested by reading the documentation alone.

**Acceptance Scenarios**:

1. **Given** the feature is delivered, **When** a maintainer reads the documentation, **Then** "AI-discoverable" is defined as a concrete, observable measure.
2. **Given** the documented metric, **When** a maintainer wants to measure it post-launch, **Then** the documentation names where the measure is observed (the reporting/analytics source).
3. **Given** the site is not yet indexed, **When** the metric is documented, **Then** no numeric target is asserted (the target is explicitly deferred until a post-launch baseline exists).

---

### Edge Cases

- **Staging noindex still in force**: The site is on a noindex'd staging URL until the separate launch feature flips it. All metadata, structured data, sitemap dates, social cards, and crawler-access rules MUST be correct and present even though the staging site instructs search engines not to index it; the existing staging noindex guard MUST remain until launch. Crawler-access permissions and the existence of metadata are independent of the noindex guard.
- **Canonical/site value on staging**: Because canonical URLs derive from the configured site value, and that value stays at the staging host until the launch feature changes it, canonical and sitemap URLs MUST point at the staging host now and finalize automatically when the launch feature changes the single site value. The production domain MUST NOT be hardcoded now (that would advertise URLs that 404 until launch).
- **Duplicate canonical risk**: Adding metadata MUST NOT introduce a second source of canonical links; exactly one canonical URL per page must remain.
- **Per-page text variant vs. whole-site digest overlap**: The per-page text variant and the full-content whole-site digest may cover overlapping content; both surfaces must remain individually fetchable and must not conflict at build time.
- **Pages without an authored description**: Authoring is the goal, but the quality gate must make a missing description a detectable failure rather than silently passing.
- **Content negotiation is not relied upon**: The per-page text variant MUST be served at a distinct, build-time URL; the feature does not rely on request-header content negotiation (no crawler honors it for this static site).

## Requirements *(mandatory)*

### Functional Requirements

#### Crawler access

- **FR-001**: The system MUST publish a crawler-access policy at the site root that explicitly allows the answer-engine citation tier (the OpenAI search/citation agent, the Perplexity citation agent, the Claude citation/user agents) to fetch every content page.
- **FR-002**: The crawler-access policy MUST explicitly allow the AI-training tier (GPTBot, Google-Extended, CCBot, anthropic-ai, ClaudeBot) to fetch every content page, as a deliberate max-discoverability posture.
- **FR-003**: The crawler-access policy MUST allow default/unnamed crawlers to fetch content pages.
- **FR-004**: The crawler-access policy MUST advertise the absolute location of the sitemap.
- **FR-005**: The deliberate decision to allow the training tier (a divergence from the sibling site's blocking posture) MUST be recorded in the feature's documentation so it is not mistaken for an oversight.

#### Agent-readable content

- **FR-006**: The system MUST expose a whole-site agent-readable digest — at minimum a concise index digest and a full-content digest — as plain text generated from the site's own content.
- **FR-007**: The system MUST expose a per-page agent-readable text/Markdown variant for each content page at a distinct, fetchable, build-time URL.
- **FR-008**: Each per-page text variant MUST correspond to a rendered content page, with no orphaned variants and no content pages missing a variant.

#### Page metadata

- **FR-009**: Every content page (all current content pages; approximately nineteen at authoring time) MUST carry a non-empty, page-appropriate meta description.
- **FR-010**: The documentation quality gate MUST fail when any content page is missing a meta description (presence is enforced, not advisory).
- **FR-011**: Every content page MUST carry exactly one canonical URL, derived from the configured site value, with no duplicate canonical links introduced.
- **FR-012**: Canonical URLs and sitemap URLs MUST use the current staging site value and MUST finalize automatically when the single configured site value is later changed at launch; the production domain MUST NOT be hardcoded by this feature.

#### Structured data

- **FR-013**: The system MUST emit a structured-data entity graph site-wide containing an Organization entity (identified and linked to the project's source-host organization) and a WebSite entity.
- **FR-014**: Each plugin page MUST emit a software-application structured-data entity describing the plugin, marked as free (zero price).
- **FR-015**: The system MUST emit an author/Person structured-data entity (linked to its source-host profile) for author/contributor disambiguation.
- **FR-016**: The feature's documentation MUST justify the structured data as a classic-search rich-results and entity-disambiguation mechanism, and MUST NOT claim it as an answer-engine citation lever.

#### Freshness signal

- **FR-017**: The sitemap last-modified date for each page MUST be sourced from the page's real change history (its source commit date), never from build time, and a page MUST be able to pin its own date explicitly when needed.
- **FR-018**: Each content page MUST display a visible "last updated" date consistent with the freshness signal.

#### Social cards

- **FR-019**: Each content page MUST reference a per-page social preview image titled/labelled for that page (not a single site-wide generic image).
- **FR-020**: Per-page social card images MUST be produced for content pages at build time.

#### Success metric

- **FR-021**: The repository MUST document a concrete definition of "AI-discoverable" as an observable measure.
- **FR-022**: The documentation MUST name the measurement source(s) where that measure is observed post-launch.
- **FR-023**: The documented metric MUST NOT assert a numeric target; the target is explicitly deferred until a post-launch baseline exists.

#### Scope boundaries (negative requirements)

- **FR-024**: The feature MUST NOT block any AI-training crawler (the allow posture is deliberate).
- **FR-025**: The feature MUST NOT rewrite documentation prose, restructure content for answer-first ordering, or change voice/tone (owned by separate editorial features).
- **FR-026**: The feature MUST NOT activate analytics, add a custom 404/legal/launch-hygiene surface, or perform the production-domain flip (owned by separate features).
- **FR-027**: The feature MUST NOT add a second canonical-link source alongside the platform's built-in canonical emission.
- **FR-028**: The feature MUST NOT ship sunset rich-result schema types (FAQ/HowTo) and MUST NOT rely on request-header content negotiation for the per-page text variant.
- **FR-029**: The existing staging noindex guard MUST remain in place; this feature MUST NOT remove or weaken it.

### Reviewability Notes *(if applicable)*

- No typed reviewability exception is requested. This feature is ordinary docs-site enhancement work and does not invoke a refactor, infra, or upgrade override. Generated agent-readable digests, per-page text variants, and generated social-card images are build outputs, not hand-reviewed source, and are excluded from the reviewable-LOC estimate below.

### Reviewability Budget *(mandatory)*

- **Primary surface**: docs/process (docs-site configuration, metadata, and content frontmatter)
- **Secondary surfaces, if any**: seed/config (crawler-access policy and site-configuration entries; structured-data and social-card wiring)
- **Projected reviewable LOC**: ~250–300 (site-config + structured-data wiring + sitemap freshness serialize + per-page social-card wiring + ~19 authored descriptions + one quality-gate rule + metric documentation), excluding generated digests, generated per-page text variants, and generated card images
- **Projected production files**: ~25–35 (site configuration, a metadata/head extension point, the crawler-access policy, the success-metric doc, the quality-gate rule, and ~19 content files gaining a description; exact split resolved during planning)
- **Projected total files**: ~30–40 (production files plus the spec/plan/tasks artifacts)
- **Budget result**: within budget
- **Split decision**: Remains one spec. The reviewable surface (~250–300 LOC) is under the block threshold. The pieces are tightly coupled SEO work that touches the same site-configuration and page-head surface; splitting would create artificial seams and two changes that both edit site configuration. A natural A/B seam exists (A: crawler/agent access; B: metadata/structured-data/cards/freshness/metric) and is recorded as the documented fallback only if the post-task atomicity check recommends a split at change-emission time.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals (the FR-024 through FR-029 boundaries), review order, scope budget, traceability, verification evidence, known gaps, and rollback notes (the feature is additive; the staging noindex guard remains, so rollback is removal of the added metadata/policy without affecting indexing posture).
- Traceability MUST map each functional-requirement group (crawler access, agent-readable content, metadata, structured data, freshness, social cards, success metric) and each measurable success criterion to the changed files and the verification evidence (rendered-output checks, the quality-gate run, and policy/sitemap inspection).
- Deferred work MUST name its owning feature: prose/editorial refresh and the meta-description refresh pass (the next editorial feature), analytics activation and launch hygiene (the analytics/hygiene feature), and the production-domain flip plus removal of the noindex guard (the launch feature). A numeric success-metric target is deferred to post-launch baseline.

### Key Entities *(include if feature involves data)*

- **Content page**: A rendered documentation page (approximately nineteen at authoring time). Attributes relevant here: meta description, canonical URL, visible "last updated" date, per-page social card reference, and a per-page agent-readable text variant.
- **Crawler-access policy**: The site-root document declaring which crawler user-agents may fetch which paths, plus the sitemap location. Tiers: citation, training, and default.
- **Agent-readable digest**: Whole-site plain-text representations of the documentation — an index digest and a full-content digest — generated from site content for coding-agent retrieval.
- **Structured-data entity graph**: The machine-readable entity set emitted for search/rich-results — Organization, WebSite, per-plugin software-application, and author/Person — with stable identifiers and links to the project's source-host org and profiles.
- **Sitemap**: The machine-readable list of pages with per-page last-modified dates sourced from real change history.
- **Success-metric definition**: The documented, observable definition of "AI-discoverable" and the named measurement source(s), with no numeric target.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of named citation-tier crawler user-agents are permitted to fetch every content page (verifiable from the published crawler-access policy).
- **SC-002**: 100% of named training-tier crawler user-agents are permitted to fetch every content page (verifiable from the published crawler-access policy).
- **SC-003**: 100% of content pages carry a non-empty meta description (today 0%); the documentation quality gate fails if any page lacks one.
- **SC-004**: 100% of content pages carry exactly one canonical URL (no page has zero or duplicate canonical links).
- **SC-005**: 100% of content pages expose a fetchable per-page agent-readable text variant, and the whole-site index digest and full-content digest are both fetchable.
- **SC-006**: The structured-data entity graph is present site-wide and includes Organization, WebSite, a software-application entity on every plugin page, and an author/Person entity.
- **SC-007**: 100% of content pages report a sitemap last-modified date derived from real change history (none report the build time), and each page shows a matching visible "last updated" date.
- **SC-008**: 100% of content pages reference a per-page-titled social preview image.
- **SC-009**: The repository contains a written, observable definition of "AI-discoverable" and names its measurement source(s), with no numeric target asserted.
- **SC-010**: Canonical and sitemap URLs reflect the staging host while the single configured site value is staging, and the feature introduces no hardcoded production domain.

## Assumptions

- **Content-page count**: There are approximately nineteen content pages at authoring time; the exact set is whatever the docs site renders as content pages when the feature is implemented. Requirements that say "every content page" apply to that full set.
- **Single-value domain flip**: The eventual production-domain change is a single configuration-value change owned by the separate launch feature; this feature relies on that and does not parameterize the value for multiple environments.
- **Platform-native canonical and freshness**: The docs platform natively emits one canonical link from the configured site value and natively supports a real-change-history freshness date; this feature relies on those built-ins rather than adding a parallel mechanism (which would risk duplicate canonical links).
- **Coordination with the editorial feature**: Meta descriptions are authored now to satisfy the presence gate; the subsequent editorial feature is expected to revisit and refresh them after prose work. This requires a coordination note in both features' scopes.
- **Reusable structured-data shapes**: The structured-data entity shapes from the proven sibling site are reusable in substance; only the injection mechanism differs on this platform (resolved during planning).
- **Staging-stays-noindex**: The site remains on its noindex'd staging URL throughout this feature; correctness of metadata is independent of the noindex guard, which remains until the launch feature.
- **No numeric baseline exists**: Because the site is not yet indexed, no meaningful numeric discoverability baseline exists; therefore the success metric is defined without a numeric target by design.
