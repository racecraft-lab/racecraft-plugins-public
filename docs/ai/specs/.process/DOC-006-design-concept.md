---
topic: "Safe interactive selector and validation aids"
slug: "doc-006-safe-interactive-selector-and-validation-aids"
date: "2026-06-16"
mode: "setup"
spec_id: "DOC-006"
source_input:
  type: "file"
  ref: "docs/ai/specs/interactive-documentation-technical-roadmap.md#DOC-006"
question_count: 8
stop_reason: "natural"
---

# Design Concept: Safe Interactive Selector and Validation Aids

> **Source:** `docs/ai/specs/interactive-documentation-technical-roadmap.md#DOC-006`
> **Date:** 2026-06-16
> **Questions asked:** 8
> **Stop reason:** natural

## Goals

- Enhance the existing `choose-your-path` route as the first home for DOC-006 selector and checker aids.
- Keep the experience static-first: accessible controls, visible fallback tables, copyable commands, and no browser-side local command execution.
- Source selector and checker data from checked-in repository files at docs build time without committing a generated metadata artifact.
- Compare repository marketplace and plugin manifest consistency only; explain expected equality and link to update or release guidance.
- Provide an accessible generated-payload diagram backed by a text/table fallback.
- Include lightweight troubleshooting handoffs for selector/checker failure states while leaving the full troubleshooting matrix to DOC-008.
- Require docs validation plus a focused fixture or test that protects source-derived command/checker rendering.

## Non-goals

- Do not create a separate DOC-006 top-level route unless implementation discovers that `choose-your-path` cannot hold the aids cleanly. See Q1.
- Do not add a reusable metadata generator script or committed generated metadata file in this slice. See Q2 and Q3.
- Do not accept pasted user JSON, inspect local user config, run shell commands from the browser, or auto-edit Claude/Codex configuration. See Q4 and Q6.
- Do not build the full troubleshooting decision tree or troubleshooting matrix; route unresolved states to DOC-008-owned troubleshooting content. See Q5.
- Do not require the full repository test suite unless implementation changes plugin source, shared scripts, manifests, or payload-generation behavior. See Q8.

## Design Tree (Q&A log)

### Q1. Where should DOC-006 make the safe selector/checker experience show up first?

**Branch:** Information architecture

**Recommended answer:** Enhance Choose Your Path
> This keeps the selector where users already decide between Claude, Codex, and install scope, with links into existing install and first-run pages.

**Alternatives offered:**
- Create a new page: Gives the aids a dedicated route, but adds navigation and maintenance surface.
- Embed across pages: Puts aids near each install tutorial, but risks duplicating command metadata and fallback tables.

**User's answer:** Enhance Choose Your Path

---

### Q2. How should DOC-006 source the command and manifest metadata used by the selector/checker?

**Branch:** Metadata ownership

**Recommended answer:** Hand-authored docs data
> A small, reviewable metadata file would avoid generator scope creep for this slice.

**Alternatives offered:**
- Generated from source: Reduces manual drift later, but can turn DOC-006 into tooling work.
- Inline only: Fastest to write, but makes static fallbacks and tests harder to keep aligned.

**User's answer:** Generated from source

**Notes:** This answer was bounded by Q3 so the implementation remains source-derived and read-only.

---

### Q3. What should "generated from source" mean for DOC-006?

**Branch:** Metadata generation boundary

**Recommended answer:** Build-time read only
> Docs components should read checked-in JSON/manifests directly at build time and render derived metadata, with no generated files to commit.

**Alternatives offered:**
- Committed generated file: Easier to inspect, but adds source/generated drift.
- Full generator script: Creates a reusable generator now, but expands DOC-006 into tooling work beyond the docs-aid slice.

**User's answer:** Build-time read only

---

### Q4. How interactive should the DOC-006 selector/checker be in this slice?

**Branch:** Interaction model

**Recommended answer:** Static-first enhancement
> Use Astro/Starlight-friendly markup with minimal client behavior, visible static tables, keyboard support, and no local command execution.

**Alternatives offered:**
- Richer app widget: More polished interaction, but likely needs more JavaScript and testing surface.
- Static tables only: Lowest risk, but does not deliver the selector/checker experience promised by DOC-006.

**User's answer:** Static-first enhancement

---

### Q5. Should DOC-006 include the troubleshooting decision-tree scaffold mentioned in the product roadmap?

**Branch:** Scope cut

**Recommended answer:** Lightweight handoff only
> Add safe next-step routing from selector/checker states while leaving the full troubleshooting matrix to DOC-008.

**Alternatives offered:**
- Include full scaffold: Creates a visible decision tree now, but risks overlapping DOC-008 and expanding this spec.
- Defer entirely: Keeps DOC-006 narrower, but leaves selector failure states without a clear handoff.

**User's answer:** Lightweight handoff only

---

### Q6. What should the manifest/version checker report for DOC-006?

**Branch:** Checker behavior

**Recommended answer:** Repo consistency only
> Compare checked-in marketplace and plugin manifest values, explain expected equality, and link to update/release docs without accepting user files.

**Alternatives offered:**
- Paste JSON checker: Lets users compare local copied JSON, but adds input handling and validation complexity.
- Maintainer-only view: Focuses on source/dist marketplace parity for contributors, but is less useful to new installers.

**User's answer:** Repo consistency only

---

### Q7. How should the generated payload diagram be delivered in DOC-006?

**Branch:** Payload explanation

**Recommended answer:** Accessible static diagram
> Use text-backed visual structure with an adjacent table/list so screen readers and static fallback both work.

**Alternatives offered:**
- Mermaid-only diagram: Fast to author, but may be less controllable in Starlight and weaker as a fallback.
- Interactive graph: More expressive, but likely too much behavior for this safe-aids slice.

**User's answer:** Accessible static diagram

---

### Q8. What validation should DOC-006 require before implementation is considered done?

**Branch:** Validation

**Recommended answer:** Docs plus focused fixture
> Run docs-site validate/link checks and add a focused metadata/rendering fixture or test for source-derived commands/checker data.

**Alternatives offered:**
- Docs checks only: Keeps validation light, but may miss drift between source JSON and rendered selector/checker metadata.
- Full repo suite required: Max confidence, but disproportionate for a docs-site-only slice unless plugin files change.

**User's answer:** Docs plus focused fixture

---

## Open Questions

- **What:** Exact component/file breakdown for the source-derived metadata helper and selector UI.
  **Why deferred:** This belongs in the Plan phase after the implementation shape is inspected in the docs-site.
  **Suggested next step:** In Plan, choose the smallest Astro/Starlight pattern that can read repository JSON at build time and render both interactive and static fallback views.
- **What:** Whether DOC-006 should split into multiple implementation PRs.
  **Why deferred:** The scaffold-time estimator returned `{"estimated_loc":227,"suggested_slices":1,"status":"ok"}` for 5 user stories, 6 files/surfaces, 6 functional requirements, and modify mode.
  **Suggested next step:** Keep DOC-006 as one vertical docs-site slice unless Plan discovers the source-derived metadata helper materially increases reviewable LOC.

## Recommended Next Step

Run setup through the generated workflow file, then start autopilot with:

```text
$speckit-autopilot docs/ai/specs/.process/DOC-006-workflow.md
```
