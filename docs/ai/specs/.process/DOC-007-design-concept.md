---
topic: "DOC-007 command, workflow, manifest, and file-layout reference"
slug: "doc-007-command-workflow-manifest-and-file-layout-reference"
date: "2026-06-17"
mode: "setup"
spec_id: "DOC-007"
source_input:
  type: "topic"
  ref: "docs/ai/specs/interactive-documentation-technical-roadmap.md#doc-007-command-workflow-manifest-and-file-layout-reference"
question_count: 8
stop_reason: "natural"
---

# Design Concept: DOC-007 Command, Workflow, Manifest, and File-Layout Reference

> **Source:** docs/ai/specs/interactive-documentation-technical-roadmap.md#doc-007-command-workflow-manifest-and-file-layout-reference
> **Date:** 2026-06-17
> **Questions asked:** 8
> **Stop reason:** natural

## Goals

- Generate reference subpages for core repository surfaces: skills, agents, manifests, hooks, scripts, tests, and source-vs-dist layout.
- Generate full visible page content for the reference section rather than only supporting data.
- Preserve strict source citations: every generated row should link to a real source path, and inferred notes must be labeled separately from source facts.
- Add deterministic generate and check modes so stale generated reference content can be detected locally and in later CI integration.
- Present Claude Code and Codex surfaces in parallel where they map, with separate runtime-specific rows where behavior differs.
- Keep DOC-007 as one slice. Advisory estimate: `estimated_loc=242`, `suggested_slices=1`, `status=ok`.

## Non-goals

- Plugin behavior changes, manifest semantics changes, install-flow changes, or generated payload content changes - answered in Q7.
- Troubleshooting, security/trust, update, rollback, and contributor release workflow depth - owned by DOC-008 and DOC-009 in the roadmap.
- Live docs-site local execution, browser-triggered plugin runs, or user-local diagnostics.
- Broad docs validation/search/accessibility hardening - owned by DOC-010.

## Design Tree (Q&A log)

### Q1. For DOC-007, should the command and file-layout reference be hand-authored from cited source paths, or generated from repository metadata?

**Branch:** Source strategy

**Recommended answer:** Hand-authored from cited source paths.
> The roadmap suggested starting hand-authored because it is the simplest path and avoids tooling before drift is measurable. The repository constitution also favors the smallest change that solves the problem.

**Alternatives offered:**
- Generate tables now: Reduces future drift risk but adds script/tooling scope and likely tests in this slice.
- Hybrid seed: Hand-author the page but add a small checked-in metadata table for later automation.

**User's answer:** Generate tables now.

---

### Q2. What should the DOC-007 generator own?

**Branch:** Generator boundary

**Recommended answer:** Reference data only.
> A data-only generator would limit the blast radius while still reducing inventory drift. It would keep prose reviewable and avoid making generated markdown the main authoring surface.

**Alternatives offered:**
- Full page content: Generate most reference markdown, which is more complete but harder to review and customize.
- Validation only: Do not generate visible tables; only fail if hand-authored references drift.

**User's answer:** Full page content.

---

### Q3. How should generated DOC-007 reference content be exposed in the docs site?

**Branch:** Information architecture

**Recommended answer:** One reference route.
> Replacing the existing route shell would be the smallest IA change and keep DOC-007 within the original "about 6 files" reviewability budget.

**Alternatives offered:**
- Reference subpages: Generate separate pages for skills, agents, manifests, scripts, and tests; easier deep links but more nav work.
- Index plus files: Keep one route visible and generate backing markdown/data files for later subpage expansion.

**User's answer:** Reference subpages.

---

### Q4. Which repository surfaces should DOC-007 treat as first-class generated reference pages?

**Branch:** Coverage depth

**Recommended answer:** Core surfaces.
> Core surfaces match the roadmap scope: skills, agents, manifests, hooks, scripts, tests, and source-vs-dist layout. This avoids noisy exhaustive generated-payload dumps while still covering user, maintainer, and agent lookup needs.

**Alternatives offered:**
- Everything shipped: Include every generated payload file too; most exhaustive but likely noisy and larger.
- User-facing only: Limit to skills, install surfaces, manifests, and hooks; defer tests and maintainer internals.

**User's answer:** Core surfaces (Recommended).

---

### Q5. How strict should source citation and inferred-note handling be in generated reference pages?

**Branch:** Source evidence

**Recommended answer:** Strict citations.
> DOC-007 is a reference slice, so rows need source-path evidence. Separating source facts from inferred notes prevents generated prose from overstating behavior.

**Alternatives offered:**
- Best-effort citations: Most rows cite files, but narrative summaries can be uncited when obvious from context.
- Concise only: Prioritize short readable pages over dense source links and source/inference labeling.

**User's answer:** Strict citations (Recommended).

---

### Q6. What validation should DOC-007 require for generated reference content?

**Branch:** Drift detection

**Recommended answer:** Generate plus check.
> A deterministic generator with a check mode fits the repo's existing validation pattern and makes generated docs reviewable. It lets local validation detect stale output before DOC-010 wires broader CI hardening.

**Alternatives offered:**
- Generate only: Simpler implementation but drift can slip in unless reviewers remember to regenerate.
- Docs build only: Rely on Astro build and link checks; less tooling but weaker drift protection.

**User's answer:** Generate plus check (Recommended).

---

### Q7. How should Claude Code and Codex surfaces be presented in the generated reference?

**Branch:** Platform presentation

**Recommended answer:** Parallel sections.
> The existing install docs are platform-specific, but many plugin surfaces map across Claude Code and Codex. Parallel sections preserve runtime differences without duplicating every concept.

**Alternatives offered:**
- Separate pages: Make Claude and Codex reference pages independent; clearer per runtime but duplicates shared concepts.
- Unified list: Collapse both platforms into one inventory; shortest but can blur runtime-specific behavior.

**User's answer:** Parallel sections (Recommended).

---

### Q8. Which potential DOC-007 expansion should stay out of scope for this slice?

**Branch:** Scope cuts

**Recommended answer:** No behavior changes.
> DOC-007 should document and generate reference content only. Changing plugin behavior, manifests, payload contents, or install flow would widen the slice and overlap with plugin release work.

**Alternatives offered:**
- No CI changes: Allow docs scripts and generated pages, but avoid touching GitHub Actions until DOC-010.
- No generated payload refs: Avoid generated payload detail entirely and focus only on source-tree references.

**User's answer:** No behavior changes (Recommended).

## Open Questions

- **What:** Exact generated subpage filenames and sidebar grouping.
  **Why deferred:** The interview chose subpages, but exact route names should be finalized during Specify/Plan after inspecting Starlight sidebar conventions.
  **Suggested next step:** Resolve in `/speckit-specify` or the first `/speckit-clarify` session.
- **What:** Whether the generator should emit markdown files, MDX files, or data consumed by a component that renders pages.
  **Why deferred:** The user chose generated full page content, but the best file format depends on the docs-site content collection and review ergonomics.
  **Suggested next step:** Resolve in `/speckit-plan` and record the chosen build path.
- **What:** Whether DOC-010 should later wire the check mode into GitHub Actions.
  **Why deferred:** DOC-007 owns the generator and local check; DOC-010 owns CI/docs hardening.
  **Suggested next step:** Mention this handoff in DOC-007 quickstart and DOC-010 dependencies.

## Recommended Next Step

Run setup. DOC-007 exists in the interactive documentation roadmap, and this setup flow should generate `docs/ai/specs/.process/DOC-007-workflow.md` plus `specs/doc-007-command-workflow-manifest-and-file-layout-reference/SPEC-MOC.md`.
