---
topic: "DOC-010 search, accessibility, deep links, and docs validation"
slug: "DOC-010-design-concept"
date: "2026-06-19"
mode: "setup"
spec_id: "DOC-010"
source_input:
  type: "file"
  ref: "docs/ai/specs/interactive-documentation-technical-roadmap.md"
question_count: 6
stop_reason: "natural"
---

# Design Concept: DOC-010 Search, Accessibility, Deep Links, and Docs Validation

> **Source:** docs/ai/specs/interactive-documentation-technical-roadmap.md
> **Date:** 2026-06-19
> **Questions asked:** 6
> **Stop reason:** natural

## Goals

- Harden the existing Astro/Starlight docs site rather than adding a new top-level route.
- Use Starlight's existing search path and improve glossary, heading, and deep-link conventions so support answers can link to stable targets.
- Combine deterministic validation with explicit manual/browser accessibility and responsive review evidence.
- Add a docs-site PR Checks path for docs-site changes so validation is not only local convention.
- Add minimal Playwright smoke coverage for key docs routes on mobile and desktop, without turning DOC-010 into a broad visual snapshot program.
- Extend existing reference, safe-aids, manifest, and generated-content checks instead of creating a separate validation framework.
- Keep DOC-010 as one slice. The shared estimator returned `{"estimated_loc":277,"suggested_slices":1,"status":"ok"}` for four user stories, about eight files/surfaces, nine functional requirements, and modify-mode work.

## Non-goals

- Adding a new top-level "quality" or "validation" docs route - rejected in Q1.
- Replacing Starlight/Pagefind search or adding a new search plugin - rejected in Q2.
- Claiming accessibility from automation alone - rejected in Q3.
- Keeping docs validation local-only - rejected in Q4.
- Building a full Playwright visual snapshot suite or accessibility-tooling stack in this slice - rejected in Q5.
- Inventing a broad new validator framework when existing docs-site validators can be extended - rejected in Q6.
- Full analytics instrumentation and live install tests in CI remain out of scope per the roadmap.

## Design Tree (Q&A log)

### Q1. For DOC-010, should the implementation prioritize hardening the existing Astro/Starlight docs site rather than adding a new top-level docs route?

**Branch:** Scope envelope

**Recommended answer:** Harden existing site (Recommended)
> The roadmap says DOC-010 is the final hardening slice after DOC-008 and DOC-009, and the current site already has the required route set. Hardening current routes keeps the change small and source-backed.

**Alternatives offered:**
- Add new route: Creates a dedicated quality or validation page, but increases content scope and may duplicate existing reference or contributor routes.
- Validation only: Limits the slice to scripts and CI, leaving search, glossary, and deep-link content hardening for later.

**User's answer:** Harden existing site (Recommended)

---

### Q2. What should DOC-010 treat as the search and deep-link target for the docs site?

**Branch:** Search, glossary, and deep links

**Recommended answer:** Use Starlight search (Recommended)
> DOC-001 chose Astro/Starlight partly because Starlight provides a built-in Pagefind search path. The current site already uses Starlight, so DOC-010 should harden terms, headings, anchors, and support-link conventions before adding another dependency.

**Alternatives offered:**
- Add search plugin: Allows more customization, but adds dependency and maintenance risk without a current blocker.
- Document plan only: Keeps implementation smaller, but leaves findability less verifiable in the final docs slice.

**User's answer:** Use Starlight search (Recommended)

---

### Q3. How far should DOC-010 go on accessibility and responsive validation for the interactive docs components?

**Branch:** Accessibility and responsive UX

**Recommended answer:** Automated plus manual (Recommended)
> The existing `SafeInstallAids.astro` and `LifecycleFlow.astro` components have keyboard, focus, label, static fallback, and responsive requirements that deterministic source checks can help with, but browser inspection is still needed for accessible behavior and layout confidence.

**Alternatives offered:**
- Automated only: Keeps CI cleaner, but may overclaim because many accessibility issues need human/browser inspection.
- Manual only: Avoids tool churn, but gives future PRs weaker regression protection.

**User's answer:** Automated plus manual (Recommended)

---

### Q4. Should DOC-010 add docs-site validation to GitHub PR Checks for docs-site changes?

**Branch:** CI validation

**Recommended answer:** Add docs check (Recommended)
> The PRD acceptance criteria call for docs CI, and current PR Checks focus on plugin changes. A docs-site-specific job can run when docs-site files change without forcing the plugin matrix on docs-only PRs.

**Alternatives offered:**
- Local only: Keeps workflows untouched, but docs drift can still merge if maintainers forget local validation.
- All PRs: Runs docs validation on every PR, but increases CI time even when no docs-site files changed.

**User's answer:** Add docs check (Recommended)

---

### Q5. What level of Playwright coverage should DOC-010 plan for?

**Branch:** Visual and browser regression

**Recommended answer:** Minimal smoke (Recommended)
> The user selected automated Playwright coverage over manual-only evidence. Keeping it to key routes and mobile/desktop smoke checks preserves the intent while staying within the small docs hardening slice.

**Alternatives offered:**
- Full visual suite: Broader coverage and snapshots, but likely too large for DOC-010 and may require splitting the spec.
- A11y plus visual: Adds accessibility tooling on top of screenshots, stronger but higher churn and more dependency risk.

**User's answer:** Minimal smoke (Recommended)

---

### Q6. How should DOC-010 handle command snippets, manifests, and generated reference consistency?

**Branch:** Source-backed validation

**Recommended answer:** Extend existing checks (Recommended)
> The repo already has `docs-site/scripts/generate-reference-pages.mjs` and `docs-site/scripts/validate-doc006-safe-aids.mjs`. Extending that validation path keeps the change simple and avoids a new framework for one docs hardening slice.

**Alternatives offered:**
- New validator suite: Could be cleaner long-term, but adds more scripts and test surface for a one-spec hardening pass.
- Docs prose only: Documents the expected discipline, but leaves no deterministic guard against snippet or manifest drift.

**User's answer:** Extend existing checks (Recommended)

---

## Open Questions

- **What:** Exact Playwright route list and script names.
  **Why deferred:** The interview settled "minimal smoke"; the Plan phase should choose exact route coverage after reading the current docs-site structure and package scripts.
  **Suggested next step:** During Plan, start from `/`, `/choose-your-path/`, `/spec-kit-lifecycle/`, `/glossary/`, and one reference route, then trim if the reviewability budget gets tight.
- **What:** Exact CI change-detection shape for docs validation.
  **Why deferred:** The interview settled conditional docs checks; implementation should fit the existing `.github/workflows/pr-checks.yml` structure after inspecting current job dependencies.
  **Suggested next step:** Prefer a docs-specific detection/output path or a narrow job-level condition rather than altering plugin matrix semantics.

## Recommended Next Step

Run setup's generated workflow with `$speckit-autopilot docs/ai/specs/.process/DOC-010-workflow.md` from inside the DOC-010 worktree.

This design concept is the source of truth for scoping decisions captured during setup. Any drift in downstream artifacts (`spec.md`, `plan.md`, `tasks.md`) from the decisions above is a defect in the downstream artifact unless there is an explicit revision note.
