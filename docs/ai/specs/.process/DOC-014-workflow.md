# SpecKit Workflow: DOC-014 — SEO and AI discoverability

**Template Version**: 1.0.0
**Created**: 2026-06-25
**Purpose**: Execution workflow for DOC-014. The phase prompts below were enriched from the Grill Me interview at scaffold time; copy-paste them into the autopilot / your AI coding agent as you execute each phase.

---

## Design Concept

This workflow file was enriched from a Grill Me interview run during
`/speckit-pro:speckit-scaffold-spec`. The full Q&A log, Goals, Non-goals, and Open
Questions live at:

```text
docs/ai/specs/.process/DOC-014-design-concept.md
```

Re-read it before each phase if you need to disambiguate a prompt. The
Specify and Clarify Prompts below were populated from that interview,
so the design concept doc is the source of truth for any decision
captured during scoping. Three decisions deliberately **diverge** from the
roadmap text / sibling site — keep them in view:

1. **Allow AI training crawlers** (GPTBot, Google-Extended, CCBot, anthropic-ai,
   ClaudeBot) — the sibling blocks them; we take a max-discoverability posture (Q1).
2. **Use `starlight-llms-txt`** (Starlight-native) rather than porting the sibling's
   `@4hse/astro-llms-txt` (Q3).
3. **Per-page dynamic OG cards** rather than the sibling's single static card (Q6).

> **Note:** Grill Me is human-in-the-loop only. It is **not** part of
> the autopilot loop. Once the workflow file is populated and autopilot
> begins, clarifications happen via `/speckit-clarify` and the
> consensus protocol — never via grill-me.

---

## Workflow Overview

| Phase | Command | Status | Notes |
|-------|---------|--------|-------|
| Specify | `/speckit-specify` | ✅ Complete | G1 pass, 0 clarification markers; 29 FR / 6 US / 18 AC / 10 SC |
| Clarify | `/speckit-clarify` | ⏳ Pending | Seed from design-concept Open Questions (plugin choices) |
| Plan | `/speckit-plan` | ⏳ Pending | |
| Checklist | `/speckit-checklist` | ⏳ Pending | Domains: seo-metadata, performance, error-handling |
| Tasks | `/speckit-tasks` | ⏳ Pending | |
| Analyze | `/speckit-analyze` | ⏳ Pending | Watch for drift from the 3 divergences above |
| Implement | `/speckit-implement` | ⏳ Pending | TDD; port sibling `e2e/seo-*.spec` patterns |

**Status Legend:** ⏳ Pending | 🔄 In Progress | ✅ Complete | ⚠️ Blocked

### Phase Gates (SpecKit Best Practice)

Each phase requires **human review and approval** before proceeding:

| Gate | Checkpoint | Approval Criteria |
|------|------------|-------------------|
| G1 | After Specify | All user stories clear, no `[NEEDS CLARIFICATION]` markers remain |
| G2 | After Clarify | Ambiguities resolved, decisions documented |
| G3 | After Plan | Architecture approved, constitution gates pass, dependencies identified |
| G4 | After Checklist | All `[Gap]` markers addressed |
| G5 | After Tasks | Task coverage verified, dependencies ordered |
| G6 | After Analyze | No `CRITICAL` issues, `WARNING` items reviewed |
| G7 | After Each Implementation Phase | Tests pass, manual verification complete |

---

## Prerequisites

### Constitution Validation

**Before starting any workflow phase**, verify alignment with the project constitution (`.specify/memory/constitution.md`):

| Principle | Requirement | Verification |
|-----------|-------------|--------------|
| VI. KISS, Simplicity & YAGNI | Simplest approach that ships the SEO surface; no speculative config | Plan + code review |
| II. Script Safety | Any new bash (none expected) uses `set -euo pipefail`; docs-site validators are JS ESM | `bash -n` / `pnpm --dir docs-site validate` |
| IV. Test Coverage | New behavior is e2e-tested (port sibling `seo-*.spec` patterns); docs validation green | `pnpm --dir docs-site validate` + `validate:smoke` |
| V. Conventional Commits | PR title `feat(...)` / `docs(...)`, public-readable plain English | CI `validate-pr-title` |

**Constitution Check:** ✅ initial (Specify) — spec aligns with KISS (one spec, no split), test coverage (e2e planned for every SEO surface), and conventional-commits PR policy. Full command verification (`pnpm --dir docs-site validate` / `build` / `validate:smoke`) runs at the Implement gate.

---

## Specification Context

### Basic Information

| Field | Value |
|-------|-------|
| **Spec ID** | DOC-014 |
| **Name** | SEO and AI discoverability |
| **Branch** | `doc-014-seo-and-ai-discoverability` |
| **Dependencies** | DOC-011 (GitHub Pages deploy + noindex staging foundation already shipped) |
| **Enables** | Public launch (DOC-012); DOC-017 (Lighthouse/perf budget depends on DOC-014) |
| **Priority** | P1 |

### Success Criteria Summary

- [ ] All ~19 content pages carry `description:` frontmatter; `validate-docs-quality.mjs` requires its presence; a "refresh meta descriptions" task is recorded in DOC-015's scope.
- [ ] A 3-tier `robots.txt` is served (Astro endpoint): citation/retrieval bots allowed, **AI training bots also allowed**, default-allow `*`, with a `Sitemap:` directive.
- [ ] `starlight-llms-txt` emits `llms.txt` / `llms-full.txt` / `llms-small.txt`, documented as a coding-agent retrieval aid.
- [ ] A per-page raw Markdown (`.md`) variant is served at build time for coding-agent retrieval.
- [ ] JSON-LD `@graph` emits Organization (`@id` + `sameAs` → GitHub org) + WebSite + `SoftwareApplication` (per plugin page, `offers.price: 0`) + a Person/author entity, injected the Starlight way.
- [ ] Per-page Open Graph cards are generated at build time; OG/canonical metadata is correct for the staging `site` and finalizes automatically when DOC-012 flips the domain.
- [ ] Sitemap `<lastmod>` and a visible "Last updated" stamp derive from git commit date (Starlight `lastUpdated`, frontmatter override allowed) — never build time.
- [ ] The AI-discoverability success metric and its measurement source (GSC Generative AI reports + GA4 AI-referrer channel group) are documented, with no numeric target.

---

## Phase 1: Specify

**When to run:** At the start. Focus on **WHAT** and **WHY**, not implementation details. Output: `specs/doc-014-seo-and-ai-discoverability/spec.md`

### Specify Prompt

```bash
/speckit-specify Make the Astro/Starlight docs site indexable, shareable, and discoverable across classic search and AI answer engines, with correct metadata for the eventual production domain.
```

#### Detailed Prompt

```bash
/speckit-specify

## Feature: SEO and AI discoverability (DOC-014)

### Problem Statement
The docs site is deployed to a noindex'd github.io staging URL with zero SEO metadata:
0 of ~19 content pages have meta descriptions, there is no Open Graph setup, no
production-grade robots.txt, no llms.txt, no JSON-LD, and no git-sourced freshness
signal. Before public launch (DOC-012) the site must be discoverable by both classic
search and AI answer/coding engines.

### Users
- Search engines and AI answer engines (ChatGPT Search, Perplexity, Google AI Overviews,
  Claude) — win citation via crawler access + entity clarity.
- Coding agents (Cursor, Claude Code, Copilot) — served by llms.txt tiers AND per-page .md.
- Humans sharing docs pages on social — served by per-page Open Graph cards.

### User Stories
- [US1] A citation crawler can fetch any page (robots.txt allows the citation tier).
- [US2] An AI training crawler can fetch any page (max-discoverability posture — DELIBERATE
  divergence from the sibling site, which blocks the training tier).
- [US3] A coding agent retrieves whole-site content (llms.txt/llms-full.txt) and a single
  page cheaply (per-page .md).
- [US4] A search engine reads correct meta descriptions, canonical URLs, JSON-LD entity
  graph, and a git-accurate sitemap lastmod for every page.
- [US5] A shared page renders a per-page Open Graph card.
- [US6] A maintainer can verify the "AI-discoverable" goal against a documented metric.

### Constraints
- Astro 6.4.6 + Starlight 0.40.0, pnpm 10.25.0, Node >=22.12. Rely on Starlight's built-in
  canonical + `lastUpdated`; do NOT add `astro-seo` (double-emits canonical).
- Keep `site` at the github.io staging value; DOC-012 owns the launch flip to
  plugins.racecraft.co. The DOC-011 noindex guard stays until DOC-012.
- All JSON-LD justified as Google/Bing rich-results + entity disambiguation, NOT as an
  LLM-citation lever (LLMs strip JSON-LD and read visible HTML).
- One spec, no split (~250-300 reviewable LOC; within the ~400 ceiling).

### Out of Scope
- Blocking AI training crawlers (deliberately allowed).
- Prose rewrites / answer-first restructuring / voice-tone (DOC-015 / DOC-019).
- Analytics activation + 404/legal/launch-hygiene (DOC-018).
- A numeric success-metric target (deferred to post-launch baseline).
- FAQPage/HowTo rich-result schema (sunset); `Accept: text/markdown` content negotiation
  (no crawler honors it on Astro static); cosmetic lastmod bumping; the production-domain
  flip (DOC-012).
```

### Specify Results

| Metric | Value |
|--------|-------|
| Functional Requirements | 29 (FR-001–FR-029; incl. 6 scope-boundary negatives FR-024–029) |
| User Stories | 6 (US1-US6; P1: US1/US4, P2: US2/US3, P3: US5/US6) |
| Acceptance Criteria | 18 acceptance scenarios + 10 measurable success criteria (SC-001–SC-010) |

### Files Generated

- [x] `specs/doc-014-seo-and-ai-discoverability/spec.md`
- [x] `specs/doc-014-seo-and-ai-discoverability/checklists/requirements.md` (requirements quality checklist, all-pass)

---

## Phase 2: Clarify

**When to run:** Spec has areas open to interpretation. Max 5 targeted questions per session.
Seed these sessions from the design-concept **Open Questions** (the two plugin-selection
choices are the live ambiguities; the design decisions themselves are settled).

### Clarify Prompts

#### Session 1: Crawler & agent access

```bash
/speckit-clarify Focus on crawler/agent access: confirm the robots.txt 3-tier taxonomy with the training tier ALLOWED (GPTBot, Google-Extended, CCBot, anthropic-ai, ClaudeBot) plus the citation tier (OAI-SearchBot, ChatGPT-User, Claude-SearchBot, Claude-User, PerplexityBot, Perplexity-User) and default-allow *; which Starlight per-page-.md plugin to adopt (starlight-md-txt vs astro-markdown-for-agents) and whether it composes with starlight-llms-txt and starlight-links-validator without build conflict.
```

#### Session 2: Structured data & metadata

```bash
/speckit-clarify Focus on structured data: how to inject the JSON-LD @graph under Starlight (global head: config for Organization + WebSite vs a Head.astro component override for per-page SoftwareApplication + Person); which pages count as "plugin pages" for SoftwareApplication (currently only speckit-pro); the Organization @id + sameAs target (GitHub org); and the exact meta-description authoring approach for ~19 pages plus the validate-docs-quality.mjs presence rule.
```

#### Session 3: Build integration & freshness

```bash
/speckit-clarify Focus on build integration: which per-page OG approach (astro-og-canvas + Starlight component override per HiDeoo's recipe vs the starlight-og plugin) integrates cleanly with the existing passthroughImageService and brand assets; how to source sitemap <lastmod> from git via Starlight lastUpdated plus a sitemap serialize function (with frontmatter override); and confirmation that canonical relies solely on Starlight's built-in (no astro-seo).
```

### Clarify Results

| Session | Focus Area | Questions | Key Outcomes |
|---------|------------|-----------|--------------|
| 1 | Crawler & agent access | | |
| 2 | Structured data & metadata | | |
| 3 | Build integration & freshness | | |

---

## Phase 3: Plan

**When to run:** After spec is finalized. Output: `specs/doc-014-seo-and-ai-discoverability/plan.md`

### Plan Prompt

```bash
/speckit-plan

## Tech Stack
- Framework: Astro 6.4.6 with @astrojs/starlight 0.40.0 (static output)
- Package manager: pnpm 10.25.0 (run scoped: `pnpm --dir docs-site ...`); Node >=22.12
- Existing integrations: starlight-links-validator; passthroughImageService (DOC-013 SVG handling)
- Testing: Playwright 1.61.0 (Chromium-only smoke + e2e), validate-docs-quality.mjs (JS ESM)
- New integrations to add: starlight-llms-txt; a per-page-.md plugin (starlight-md-txt OR
  astro-markdown-for-agents — resolve in Clarify); a per-page OG generator (astro-og-canvas
  + component override OR starlight-og — resolve in Clarify); @astrojs/sitemap if not present

## Constraints
- Rely on Starlight's built-in canonical + lastUpdated. Do NOT add astro-seo (double canonical).
- Keep `site: 'https://racecraft-lab.github.io'` + `base: '/racecraft-plugins-public'`;
  DOC-012 flips the domain. Keep the DOC-011 noindex head guard untouched.
- Port the proven sibling artifacts where they port: the robots.txt 3-tier ENDPOINT
  (src/pages/robots.txt.ts) ports cleanly; the JSON-LD schema FACTORY functions port but the
  layout-based injection must be redone Starlight-style (head: config + Head.astro override).
- ~250-300 reviewable LOC; one spec, no split.

## Architecture Notes
- robots.txt: an Astro endpoint emitting training-allow + citation-allow + default-allow +
  Sitemap:. (DECISION Q1: allow training bots — divergence from sibling, which blocks.)
- JSON-LD: Organization (@id + sameAs → GitHub org) + WebSite global via Starlight head:;
  SoftwareApplication (offers.price 0) per plugin page + Person/author via Head.astro override.
  Justify as rich-results + entity disambiguation only. (DECISION Q5)
- llms.txt: starlight-llms-txt, NOT a port of @4hse/astro-llms-txt. (DECISION Q3)
- per-page .md: build-time distinct .md URLs (no Accept-header negotiation on Astro static).
  (DECISION Q4)
- OG: per-page dynamic cards at build time. (DECISION Q6)
- sitemap lastmod + "Last updated" stamp: git commit date via Starlight lastUpdated + a
  sitemap serialize function; frontmatter override allowed. (DECISION Q7)
- success metric: a documentation artifact defining GSC Generative AI reports + a GA4
  AI-referrer channel group; no numeric target. (DECISION Q9)

Re-read docs/ai/specs/.process/DOC-014-design-concept.md for the full rationale of each decision.
```

### Plan Results

| Artifact | Status | Notes |
|----------|--------|-------|
| `plan.md` | ⏳ | Technical context, execution flow |
| `research.md` | ⏳ | Decision rationales (carry the design-concept citations) |
| `data-model.md` | ⏳ | Schema shapes (Organization/WebSite/SoftwareApplication/Person) |
| `contracts/` | ⏳ | robots.txt taxonomy, JSON-LD field contracts, sitemap lastmod source |
| `quickstart.md` | ⏳ | How to verify SEO surfaces locally |

---

## Phase 4: Domain Checklists

**When to run:** After `/speckit-plan` — validates spec AND plan together.

### Recommended Domains

Target 2-3. Chosen from the spec's risk surface:

#### 1. seo-metadata Checklist (custom domain)

Why this domain: the spec's core risk is metadata correctness — description presence,
canonical URLs, JSON-LD validity, OG tag completeness, robots.txt taxonomy, and sitemap
lastmod accuracy. This is where silent SEO defects hide.

```bash
/speckit-checklist seo-metadata

Focus on SEO and AI discoverability requirements:
- robots.txt 3-tier taxonomy is correct AND ordered (training-allow + citation-allow + default-allow + Sitemap:)
- JSON-LD @graph is valid and the WebSite publisher @id matches the Organization @id; SoftwareApplication carries offers.price 0
- Canonical relies solely on Starlight built-in (no astro-seo double-emit); URLs derive from `site` + `base`
- Every content page has a non-empty `description:`; the validator rejects a missing one
- Pay special attention to: the deliberate divergences (training bots ALLOWED; starlight-llms-txt not the @4hse port; per-page dynamic OG not static) being reflected, not silently reverted
```

#### 2. performance Checklist

Why this domain: per-page OG generation + three new build integrations + a sitemap
serialize function all affect build cost and Core Web Vitals — and DOC-017 will gate
Lighthouse, so DOC-014 must not regress build/runtime perf.

```bash
/speckit-checklist performance

Focus on SEO and AI discoverability requirements:
- Per-page OG image generation does not blow up build time or output size for ~19-26 pages
- New integrations (starlight-llms-txt, per-page .md, OG generator) do not add render-blocking assets
- The static-output build stays within reasonable bounds ahead of DOC-017's Lighthouse budget
- Pay special attention to: build-time cost of dynamic OG and per-page .md generation
```

#### 3. error-handling Checklist

Why this domain: the robots.txt endpoint, build-time OG generation, per-page .md
generation, and git-sourced lastmod each have failure modes (missing git history, missing
frontmatter, generation errors) that must degrade safely.

```bash
/speckit-checklist error-handling

Focus on SEO and AI discoverability requirements:
- lastmod when a file has no git history yet (new page) — frontmatter override / sensible fallback
- OG/.md generation failure for one page does not fail the whole build silently
- robots.txt endpoint always emits a valid response
- Pay special attention to: missing `description:` and missing `lastUpdated` edge cases
```

### Checklist Results

| Checklist | Items | Gaps | Spec References |
|-----------|-------|------|-----------------|
| seo-metadata | | | |
| performance | | | |
| error-handling | | | |
| **Total** | | | |

---

## Phase 5: Tasks

**When to run:** After checklists complete (all gaps resolved). Output: `specs/doc-014-seo-and-ai-discoverability/tasks.md`

### Tasks Prompt

```bash
/speckit-tasks

## Task Structure
- Small, testable chunks; clear acceptance criteria referencing FR-xxx
- Dependency ordering: config/integrations -> components/endpoints -> content frontmatter -> validators/tests
- Mark parallel-safe tasks with [P]
- Organize by user story (US1-US6), not by technical layer

## Implementation Phases
1. Foundation: add integrations (starlight-llms-txt, per-page .md plugin, OG generator, sitemap) to astro.config; wire Starlight lastUpdated
2. US1/US2/US3 (crawler + agent access): robots.txt endpoint (training-allow), llms.txt verify, per-page .md verify
3. US4/US5 (metadata): JSON-LD @graph (Org/WebSite/SoftwareApplication/Person) via head:/Head.astro; per-page OG; sitemap git-lastmod serialize; ~19 description: frontmatter + validate-docs-quality.mjs rule
4. US6 + polish: success-metric definition doc; "Last updated" stamp; cross-cutting verification

## Constraints
- Tests live in docs-site/tests/ (Playwright Chromium-only); port the sibling e2e patterns:
  seo-robots-txt.spec, seo-schema-org.spec, seo-llms-txt.spec, seo-sitemap.spec
- Bound tasks by the Non-goals in the design concept: do NOT block training bots, do NOT add
  astro-seo, do NOT flip the production domain, do NOT author a numeric metric target,
  do NOT rewrite prose (DOC-015)
- Add a "refresh meta descriptions" task reference into DOC-015's scope (cross-spec note, Q2)
- Reference docs/ai/specs/.process/DOC-014-design-concept.md for the "why" behind each decision
```

### Tasks Results

| Metric | Value |
|--------|-------|
| **Total Tasks** | |
| **Phases** | 4 |
| **Parallel Opportunities** | |
| **User Stories Covered** | US1-US6 |

---

## Atomicity Route

**When this is filled:** After the Tasks phase / gate G5, the autopilot SKILL runs
the read-only atomicity classifier and records its decision here. Leave blank during scoping.

The slice-sizing branch (design concept Q10) chose **one spec, no split** (~250-300 LOC,
within the ~400 ceiling). The classifier may still recommend a split-PR emission based on
structural seams; the documented fallback seam is (A) crawler/agent access [robots.txt +
llms.txt + per-page .md] vs (B) discoverability metadata [descriptions + JSON-LD + OG +
sitemap lastmod + metric].

| Field | Value | Meaning |
|-------|-------|---------|
| **Route** | | One of `split-PR`, `one-navigable-PR`, `single-atomic-PR`, `branch-by-abstraction`, or `out-of-scope`. |
| **Releasable** | | `true`, or `false` for a destructive-migration or concurrency-sensitive change. |
| **Signals** | | The decisive detector findings behind the route. |
| **Warnings** | | Any release-safety warning attached to the change. |

To produce the decision, run the classifier against the feature directory:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh specs/doc-014-seo-and-ai-discoverability
```

---

## Phase 6: Analyze

**When to run:** Always run after generating tasks.

### Analyze Prompt

```bash
/speckit-analyze

Focus on:
1. Constitution alignment — KISS/YAGNI (no speculative config), test coverage (e2e for every SEO surface)
2. Coverage gaps — every FR and user story (US1-US6) has a task
3. Consistency between task file paths and the actual docs-site structure
4. DESIGN-CONCEPT DRIFT — flag any downstream artifact that contradicts the design concept's
   decisions. The design concept is the source of truth for scoping. Specifically verify these
   three divergences are intact (a downstream artifact that reverts them is WRONG unless it
   carries an explicit revision note):
   - Q1: AI TRAINING bots are ALLOWED (not blocked like the sibling)
   - Q3: llms.txt uses starlight-llms-txt (NOT a port of @4hse/astro-llms-txt)
   - Q6: Open Graph is PER-PAGE DYNAMIC (not a single static card)
   Also verify: no astro-seo dependency (Q8); no numeric metric target (Q9); JSON-LD justified
   as rich-results/entity-disambiguation only, never as LLM-citation (Q5).
```

### Analysis Results

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| | | | |

---

## Phase 7: Implement

**When to run:** After tasks.md is generated and analyzed (no coverage gaps).

### Implement Prompt

```bash
/speckit-implement

## Approach: TDD-First
For each task: RED (failing test) -> GREEN (minimum impl) -> REFACTOR -> VERIFY.

### Pre-Implementation Setup
1. `pnpm --dir docs-site install` (after adding integrations)
2. `pnpm --dir docs-site validate` passes before changes
3. Confirm you are on branch `doc-014-seo-and-ai-discoverability`

### Implementation Notes
- Port the proven sibling test patterns into docs-site/tests/ (Chromium-only):
  seo-robots-txt.spec (assert training tier ALLOWED here — the inverse of the sibling),
  seo-schema-org.spec (Organization @id == WebSite publisher @id; SoftwareApplication offers.price 0; Person present),
  seo-llms-txt.spec (llms.txt/llms-full.txt/llms-small.txt 200 + non-empty),
  seo-sitemap.spec (lastmod is a valid ISO date sourced from git, not build time)
- robots.txt: port src/pages/robots.txt.ts but MOVE the training tier from Disallow to Allow (Q1)
- JSON-LD: port schema.ts factory functions; redo injection Starlight-style (head: + Head.astro)
- Consult docs/ai/specs/.process/DOC-014-design-concept.md Q&A for the "why" behind edge-case handling
- Decisions in the design concept not reflected in tasks.md are gaps — surface them before coding
```

### Implementation Progress

| Phase | Tasks | Completed | Notes |
|-------|-------|-----------|-------|
| 1 - Foundation (integrations) | | | |
| 2 - Crawler & agent access | | | |
| 3 - Metadata & structured data | | | |
| 4 - Metric + polish | | | |

---

## Post-Implementation Checklist

- [ ] All tasks marked complete in tasks.md
- [ ] Docs validation passes: `pnpm --dir docs-site validate`
- [ ] Smoke + e2e pass: `pnpm --dir docs-site validate:smoke`
- [ ] Build succeeds: `pnpm --dir docs-site build`
- [ ] robots.txt served with training tier ALLOWED + citation tier ALLOWED + Sitemap:
- [ ] JSON-LD validates; sitemap lastmod is git-sourced; per-page OG + .md present
- [ ] All ~19 pages have `description:`; validator rejects a missing one; DOC-015 refresh task recorded
- [ ] Success-metric definition documented (no numeric target)
- [ ] noindex staging guard untouched; `site` unchanged (DOC-012 owns the flip)
- [ ] PR created with a public-readable conventional-commits title and reviewed

---

## Lessons Learned

### What Worked Well

-

### Challenges Encountered

-

### Patterns to Reuse

-

---

## Project Structure Reference

```
docs-site/
├── astro.config.mjs              # site/base, integrations (Starlight, llms-txt, .md, OG, sitemap)
├── src/
│   ├── content/docs/**           # ~19 content pages (add description: frontmatter)
│   ├── components/                # Head.astro override (JSON-LD @graph injection)
│   └── pages/robots.txt.ts        # new — 3-tier endpoint (training tier ALLOWED)
├── public/robots.txt              # DOC-011 staging guard (replaced by the endpoint)
├── scripts/validate-docs-quality.mjs  # add description-presence rule
└── tests/                         # Playwright e2e (port sibling seo-*.spec patterns)
specs/doc-014-seo-and-ai-discoverability/
├── SPEC-MOC.md                    # navigation marker (committed at scaffold)
├── spec.md / plan.md / tasks.md   # generated by the phases above
```

---

Populated from the DOC-014 Grill Me interview (2026-06-25). The design concept doc at
`docs/ai/specs/.process/DOC-014-design-concept.md` is the source of truth for every scoping decision.
