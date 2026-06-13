---
topic: "Static docs framework and IA spike"
slug: "doc-001-static-docs-framework-and-ia-spike"
date: "2026-06-12"
mode: "setup"
spec_id: "DOC-001"
source_input:
  type: "file"
  ref: "docs/ai/specs/interactive-documentation-technical-roadmap.md#doc-001-static-docs-framework-and-ia-spike"
question_count: 6
stop_reason: "natural"
---

# Design Concept: Static Docs Framework and IA Spike

> **Source:** docs/ai/specs/interactive-documentation-technical-roadmap.md#doc-001-static-docs-framework-and-ia-spike
> **Date:** 2026-06-12
> **Questions asked:** 6
> **Stop reason:** natural

## Goals

- Produce one default static-site stack recommendation that DOC-002 should implement unless the spike records a hard blocker.
- Compare Docusaurus/MDX, VitePress, Astro/Starlight, and a repo-native fallback with current source evidence.
- Prioritize rich MDX or equivalent interactivity, while requiring the selected stack to be hostable from this repository through GitHub Pages.
- Recommend the package manager as part of the selected framework choice rather than preselecting one globally.
- Draft a Diataxis IA skeleton with routes, route purpose, audience, source evidence, and success criteria, without writing full page copy.
- Keep DOC-001 a research-only spike that writes a decision record under `docs/ai/research/` and does not create site scaffolding, package files, or product/plugin behavior changes.

## Non-goals

- Implementing a docs site in DOC-001; implementation belongs to DOC-002.
- Migrating README or `speckit-pro/README.md` content in DOC-001.
- Creating `package.json`, lockfiles, site config, or prototype components unless a later human explicitly reopens the spike scope.
- Choosing a stack from stale assumptions only; framework/platform documentation should be refreshed during the spike.

## Design Tree (Q&A log)

### Q1. For DOC-001, should the framework spike produce one default stack recommendation that DOC-002 is expected to implement unless a blocker appears?

**Branch:** Decision authority

**Recommended answer:** One default stack recommendation.
> A single recommendation creates a clear handoff from the spike to implementation and avoids making DOC-002 repeat framework selection.

**Alternatives offered:**
- Shortlist only: Keeps optionality, but forces DOC-002 to redo the decision.
- Prototype first: Adds evidence, but expands the research-only spike into implementation.

**User's answer:** One default stack recommendation.

---

### Q2. Which criterion should carry the most weight when choosing between Docusaurus, VitePress, Astro/Starlight, and a repo-native fallback?

**Branch:** Framework selection criteria

**Recommended answer:** Low maintenance.
> The repo constitution favors simple, verifiable changes, and a docs site should not add a heavy app surface before the product value is proven.

**Alternatives offered:**
- Interactive MDX power: Optimizes for richer widgets, but increases frontend complexity.
- Fastest first launch: Gets a site online quickly, but can underweight search, versioning, and accessibility.

**User's answer:** Interactive MDX power, with the added requirement that the selected stack must be hostable via GitHub Pages in this repository.

---

### Q3. What package-manager posture should DOC-001 recommend for the future docs site?

**Branch:** Tooling policy

**Recommended answer:** Use pnpm.
> A deterministic lockfile would fit modern static-site tooling, but the repo does not yet have Node tooling and the selected framework may have a stronger default.

**Alternatives offered:**
- Let framework decide: Avoids premature commitment, but leaves a setup decision in the spike output.
- No Node dependency: Keeps the repo lightweight, but likely rules out rich interactive docs.

**User's answer:** Let the framework decision also determine the package manager.

---

### Q4. How detailed should the DOC-001 IA skeleton be before DOC-002 builds the shell?

**Branch:** Information architecture depth

**Recommended answer:** Routes plus purpose.
> This gives DOC-002 enough handoff structure while keeping DOC-001 out of content-authoring work.

**Alternatives offered:**
- Full content outline: More detailed, but turns the spike into page-writing.
- Minimal sitemap: Smaller, but leaves too much ambiguity for the shell.

**User's answer:** Routes plus purpose.

**Clarify session 2 update:** The IA skeleton will use route-level records with route path, route label, primary Diataxis mode, optional secondary modes, audience, purpose, source evidence, success criterion, shell owner DOC, and full content owner DOC. It must cover the 11 PRD IA route labels without drafting full page copy.

---

### Q5. Should DOC-001 require live source refresh for framework and platform docs during the spike, or use the PRD's captured source map as sufficient input?

**Branch:** Evidence freshness

**Recommended answer:** Refresh live.
> Framework capabilities, GitHub Pages support, and platform docs can drift, so the stack decision should cite current sources.

**Alternatives offered:**
- Use PRD snapshot: Faster and reproducible, but may be stale.
- Refresh only winner: Less effort, but weakens the comparison.

**User's answer:** Refresh live.

---

### Q6. What should DOC-001 be allowed to write besides the normal SpecKit workflow artifacts?

**Branch:** Output surface

**Recommended answer:** Research doc only.
> This preserves DOC-001 as a true spike and keeps package/config churn out of the branch until DOC-002.

**Alternatives offered:**
- Research plus ADR: Stronger architecture trail, but duplicates the spike decision record.
- Research plus prototype: Practical proof, but conflicts with the roadmap's no-site-implementation scope.

**User's answer:** Research doc only.

**Clarify session 3 update:** The allowed implementation output is `docs/ai/research/interactive-documentation-framework-spike.md` plus normal DOC-001 SpecKit artifacts under `specs/doc-001-static-docs-framework-and-ia-spike/**` and `docs/ai/specs/.process/DOC-001-*`. PRD, roadmap, design concept, README, plugin documentation, package files, lockfiles, site config, prototypes, CI, marketplace/generated payloads, and plugin behavior are excluded unless a later human explicitly amends scope.

## Resolved and Deferred Questions

- **What:** Final static-site framework and package manager.
  **Resolution:** DOC-001 recommends Astro/Starlight with pnpm as the report-only DOC-002 package-manager handoff. This does not authorize package or lockfile creation in DOC-001.
- **What:** Hosting policy details for GitHub Pages.
  **Resolution:** DOC-001 records Astro/Starlight GitHub Pages feasibility and fallback rules. DOC-002 owns concrete Astro `site`, `base`, `trailingSlash`, workflow, and output-path configuration after refreshing current docs.
- **What:** Exact README content treatment after the site exists.
  **Why deferred:** DOC-001 defines IA, not content migration.
  **Suggested next step:** Carry as a DOC-002 or later content-shell decision.

## Recommended Next Step

Run `$speckit-autopilot` from the DOC-001 worktree using `docs/ai/specs/.process/DOC-001-workflow.md`.
