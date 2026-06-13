---
topic: "DOC-002 unified landing page and IA shell"
slug: "doc-002-unified-landing-page-and-ia-shell"
date: "2026-06-13"
mode: "setup"
spec_id: "DOC-002"
source_input:
  type: "file"
  ref: "docs/roadmap-interactive-documentation.md#DOC-002"
question_count: 13
stop_reason: "natural"
---

# Design Concept: DOC-002 Unified Landing Page And IA Shell

> **Source:** `docs/roadmap-interactive-documentation.md#DOC-002`
> **Date:** 2026-06-13
> **Questions asked:** 13
> **Stop reason:** natural

## Goals

- Create a top-level `docs-site/` Astro/Starlight app for the public docs shell.
- Use docs-site-scoped `pnpm` package scripts so the plugin marketplace repo root stays focused on plugin validation.
- Build a thin, actionable landing page that states the marketplace purpose, current plugin, supported platforms, source-vs-generated-payload distinction, and next paths.
- Create skeletal pages for all 11 DOC-001 IA routes, with route purpose, owner DOC, success criterion, and canonical source links.
- Organize the Starlight sidebar by Diataxis groups: Tutorials, How-to, Reference, and Explanation.
- Add production build plus internal-link validation in DOC-002, while leaving broader accessibility, screenshot, search, and docs CI hardening to DOC-010.
- Keep one DOC-002 workflow, but plan two PR slices if autopilot emits split PRs: first the Astro/Starlight shell and route skeleton, then validation/config hardening.

## Non-goals

- Full platform install content for Claude Code or Codex; DOC-003 and DOC-004 own that content.
- Full first-run, troubleshooting, security/trust, contributor, lifecycle, glossary, search, accessibility, and responsive UX content; later DOC specs own those details.
- Root README or `speckit-pro/README.md` conversion or redirect; DOC-002 uses those files as source evidence only.
- GitHub Pages publish workflow; DOC-002 makes the site Pages-config-ready, while DOC-010 owns docs CI/deployment hardening unless the roadmap changes.
- Interactive widgets beyond basic navigation; DOC-006 owns safe interactive aids.
- Docs versioning; record the future policy trigger, but do not implement versioning in DOC-002.

## Design Tree (Q&A Log)

### Q1. Where should DOC-002 create the Astro/Starlight site shell?

**Branch:** Site location

**Recommended answer:** `docs-site/`
> Creates a clear top-level docs app without colliding with existing Markdown docs or plugin source.

**Alternatives offered:**
- `docs/site`: Keeps the site under docs but risks mixing source docs with generated site app files.
- Repo root: Simplifies package scripts but adds package files directly beside plugin marketplace files.

**User's answer:** `docs-site/`

---

### Q2. How should DOC-002 define package management and build scripts for the docs site?

**Branch:** Package scripts

**Recommended answer:** `pnpm` in `docs-site/`
> This matches the DOC-001 handoff, keeps scripts scoped to the docs app, and avoids changing root plugin validation yet.

**Alternatives offered:**
- Root workspace: Centralizes scripts at repo root but expands the repo-level Node surface immediately.
- Defer scripts: Avoids package decisions now but leaves the scaffold less executable for autopilot.

**User's answer:** `pnpm` in `docs-site/`

---

### Q3. How much content should DOC-002 put on the landing page?

**Branch:** Landing page depth

**Recommended answer:** Thin actionable shell
> The landing page should state purpose, platforms, source-vs-payload distinction, and next paths without duplicating later DOC content.

**Alternatives offered:**
- Full marketing page: Gives a richer first impression but risks bloating DOC-002 beyond route-shell scope.
- Minimal placeholder: Keeps DOC-002 small but may fail the one-screen value and platform-choice acceptance criteria.

**User's answer:** Thin actionable shell

---

### Q4. What should DOC-002 create for the 11 top-level IA routes?

**Branch:** Route shell depth

**Recommended answer:** Skeletal pages
> Creating every route now gives later specs stable targets while preserving their content ownership.

**Alternatives offered:**
- Landing only: Reduces files now but leaves DOC-003 through DOC-010 without stable route targets.
- Full content draft: More complete, but overlaps heavily with later DOC specs and risks a large review surface.

**User's answer:** Skeletal pages

---

### Q5. Should DOC-002 change the root README or plugin README once the docs shell exists?

**Branch:** README handling

**Recommended answer:** Source only
> README files should remain canonical source evidence until the site has real hosted URLs and fuller content.

**Alternatives offered:**
- Add pointers: Adds short docs-site pointers now, but may create premature links before deployment is settled.
- Convert README: Moves users toward the site quickly but exceeds DOC-002 scope and risks disrupting existing marketplace docs.

**User's answer:** Source only

---

### Q6. Should DOC-002 add Starlight internal-link validation immediately?

**Branch:** Validation scope

**Recommended answer:** Basic build only
> Deferring link validation would keep DOC-002 focused on scaffold and route shell, with DOC-010 hardening validation later.

**Alternatives offered:**
- Add validator now: Catches internal link drift earlier but adds community-plugin configuration during the scaffold slice.
- Document only: Records the decision without build enforcement, but gives less confidence than a basic site build.

**User's answer:** Add validator now

---

### Q7. What validation should DOC-002 require after adding the link validator?

**Branch:** Validation boundary

**Recommended answer:** Build plus links
> Run Astro/Starlight production build and internal-link validation, while leaving accessibility, screenshots, search hardening, and broader CI to DOC-010.

**Alternatives offered:**
- Full docs CI: Adds broader automation now but conflicts with DOC-002's non-goal of CI hardening beyond basic build.
- Manual checks only: Keeps implementation simple but weakens confidence in route and link correctness.

**User's answer:** Build plus links

---

### Q8. How should DOC-002 handle GitHub Pages deployment details?

**Branch:** Deployment ownership

**Recommended answer:** Config ready
> Set Astro site/base assumptions and document the expected Pages path without adding a new workflow yet.

**Alternatives offered:**
- Add workflow: Makes deployment executable sooner but expands into CI/deployment work that DOC-010 can own.
- Defer config: Keeps scaffold minimal but risks discovering base/path issues late.

**User's answer:** Other: `1 if we have a spec that covers this in the future, or 2 if we don't.`

**Notes:** The roadmap gives DOC-010 the docs CI/validation hardening lane, so this was clarified in Q9.

---

### Q9. Should DOC-002 stop at Pages-ready config and leave the publish workflow to DOC-010?

**Branch:** Deployment ownership

**Recommended answer:** Config now
> This matches the existing DOC-010 hardening lane while still making base/path assumptions explicit in DOC-002.

**Alternatives offered:**
- Workflow now: Adds a deploy workflow in DOC-002 because no later deployment spec should own it.
- Decide later: Leaves deployment ownership open for Clarify, but weakens the implementation plan.

**User's answer:** Config now

---

### Q10. How should the initial Starlight sidebar organize the 11 routes?

**Branch:** Navigation model

**Recommended answer:** Diataxis groups
> Grouping Tutorial, How-to, Reference, and Explanation routes satisfies AC-2.2 and keeps the IA task-first.

**Alternatives offered:**
- Flat list: Simpler to implement but weaker at showing the docs model and user path structure.
- Platform first: Centers Claude/Codex choice, but buries reference, security, and maintainer paths.

**User's answer:** Diataxis groups

---

### Q11. Where should DOC-002 explain source tree versus generated install payloads?

**Branch:** Source-vs-payload explanation

**Recommended answer:** Landing plus Reference
> This gives first-screen clarity and a stable deeper explanation without overfilling install pages.

**Alternatives offered:**
- Reference only: Keeps landing cleaner but may miss AC-2.4 for first-time visitors.
- Every platform page: Reinforces the concept, but duplicates content later owned by DOC-003 and DOC-004.

**User's answer:** Landing plus Reference

---

### Q12. Should DOC-002 be split because the forward estimate is just over the advisory review-size ceiling?

**Branch:** Slice sizing

**Recommended answer:** Split into two
> The forward estimate was `{"estimated_loc":405,"suggested_slices":2,"status":"warn"}`. A two-slice plan keeps one slice for Astro/Starlight shell and routes, and one for validation/config hardening.

**Alternatives offered:**
- Keep one spec: Accepts a borderline 405 LOC estimate because the shell and build/link validation are one coherent vertical increment.
- Defer split: Leaves slicing to autopilot reviewability gates after spec and plan artifacts exist.

**User's answer:** Split into two

---

### Q13. Should the accepted DOC-002 split stay inside one DOC-002 workflow as two PR slices?

**Branch:** Slice representation

**Recommended answer:** One workflow
> This keeps roadmap identity stable while letting autopilot emit shell/routes first and validation/config second if needed.

**Alternatives offered:**
- Two specs: Creates separate roadmap/spec identities, but requires roadmap changes before scaffold is truly ready.
- Decide later: Records the split risk and leaves exact emission shape to Tasks/Analyze.

**User's answer:** One workflow

## Open Questions

- **What:** Exact Astro/Starlight package versions and link-validator package version.
  **Why deferred:** Version-sensitive source evidence must be refreshed at implementation time.
  **Suggested next step:** Resolve during Plan before package files are committed.

- **What:** Exact GitHub Pages `site`, `base`, and `trailingSlash` settings.
  **Why deferred:** The route shell should be Pages-config-ready, but no publish workflow is created in DOC-002.
  **Suggested next step:** Resolve during Clarify or Plan using current Astro GitHub Pages docs and repository URL.

- **What:** Whether autopilot emits two PR slices or one navigable PR.
  **Why deferred:** The user accepted two slices inside one DOC-002 workflow, but final emission depends on Tasks, reviewability gates, and atomicity routing.
  **Suggested next step:** Preserve the split intent in Tasks and let the PRSG-007/008/009 path decide the concrete PR topology.

## Recommended Next Step

Run setup. This design concept is already part of `$speckit-scaffold-spec DOC-002`; the next command after scaffold completion is `$speckit-autopilot docs/ai/specs/.process/DOC-002-workflow.md`.
