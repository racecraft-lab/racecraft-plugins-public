# Accessibility Checklist: Safe Interactive Selector and Validation Aids

**Purpose**: Validate DOC-006 accessibility requirements before task generation
**Created**: 2026-06-17
**Feature**: [spec.md](../spec.md)
**Domain prompt**: `/speckit-checklist accessibility`

Focus areas:

- Keyboard operation for selector/checker controls.
- Semantic fallback tables or equivalent static content.
- Accessible generated-payload diagram with text-backed explanation.
- Whether the page remains usable without JavaScript or pointer-only interaction.

## Keyboard Operation

- [x] A11Y001 [Spec FR-014, Clarifications: Keyboard behavior, SC-005] Are keyboard operation requirements defined for all selector, checker, diagram, and checklist aids? [Completeness]
- [x] A11Y002 [Clarifications: Keyboard behavior] Are Tab and Shift+Tab order, Space/Enter activation, visible focus, and selected-state distinction specified clearly enough for implementation? [Clarity]
- [x] A11Y003 [Spec US3 AC-3.2, SC-005] Are keyboard-only expectations measurable through user scenario acceptance criteria and success criteria? [Acceptance Criteria]
- [x] A11Y004 [Spec FR-014, Clarifications: Keyboard behavior] Do the requirements prefer native controls where possible, reducing custom control accessibility risk? [Consistency]
- [x] A11Y005 [Spec Clarifications: Keyboard behavior] Does the spec require selected/current state to be programmatically exposed for assistive technologies when custom controls are used, rather than relying only on visual distinction? [Coverage]

## Static Fallback And No-JavaScript Use

- [x] A11Y006 [Spec US1 AC-1.1, US3 AC-3.1, FR-014, SC-004] Are no-JavaScript requirements defined for selector fallback, checker comparison content, payload diagram content, and first-run checklist content? [Completeness]
- [x] A11Y007 [Clarifications: Semantic fallback content] Is `noscript`-only fallback explicitly insufficient, with complete semantic content required in normal static HTML? [Clarity]
- [x] A11Y008 [Clarifications: Semantic fallback content, SC-002] Are required selector fallback fields complete: platform, scope, prerequisites, command label or sequence, success signal, and next link? [Coverage]
- [x] A11Y009 [Spec FR-010, Clarifications: Semantic fallback content, SC-003] Are checker fallback requirements complete enough to expose compared values, expected rules, states, and handoffs without scripting? [Coverage]
- [x] A11Y010 [Plan Performance Goals, Implementation Boundaries] Are progressive-enhancement requirements constrained so static content remains complete and primary? [Consistency]

## Pointer Independence

- [x] A11Y011 [Spec FR-014, Clarifications: Keyboard behavior] Are selector and checker interactions specified so pointer input is optional rather than required? [Coverage]
- [x] A11Y012 [Clarifications: Accessible payload diagram] Does the diagram requirement prohibit information that depends on hover, drag, zoom, click, or pointer-only interaction? [Coverage]
- [x] A11Y013 [Clarifications: Copy affordance boundary] Are copy controls optional progressive enhancement, with raw commands still visible and selectable outside JavaScript behavior? [Consistency]

## Semantic Structure And Assistive Technology

- [x] A11Y014 [Spec FR-012, Clarifications: Accessible payload diagram, Data Model: GeneratedPayloadDiagramNode] Are payload diagram nodes required to exist as real headings, list items, or table rows with explanatory text? [Completeness]
- [x] A11Y015 [Spec FR-014, Clarifications: Semantic fallback content] Are selector, checker, diagram, and checklist facts required in semantic tables, lists, headings, or equivalent static content? [Completeness]
- [x] A11Y016 [Clarifications: Copy affordance boundary] If copy buttons are included, are they required to be native buttons with visible clipboard failure/status text and visible raw commands? [Coverage]
- [x] A11Y017 [Spec FR-015, FR-011] Are accessibility requirements consistent with safety boundaries that prohibit browser-side local execution, local file reads, pasted JSON diagnostics, and local workflow invocation? [Consistency]

## Diagram And First-Run Checklist

- [x] A11Y018 [Spec FR-012, Clarifications: Accessible payload diagram] Are required diagram nodes defined: source tree, Claude distribution, Codex distribution, marketplace entries, and Codex cache? [Completeness]
- [x] A11Y019 [Spec FR-013, Clarifications: First-run checklist scope] Are required first-run checkpoint categories documented and bounded to safe readiness review? [Completeness]
- [x] A11Y020 [Spec US3 Independent Test, Quickstart Manual Review Checklist] Are diagram and checklist accessibility expectations tied to manual keyboard/static-fallback review? [Traceability]

## Validation Coverage

- [x] A11Y021 [Spec FR-017, SC-006, Plan Validation Plan] Does focused validation cover source-derived metadata/rendering risks that standard docs validation would miss? [Coverage]
- [x] A11Y022 [Quickstart Manual Review Checklist] Are manual review requirements present for no-JavaScript/static HTML and keyboard-only traversal? [Coverage]
- [x] A11Y023 [Plan Validation Plan, Quickstart] Are standard docs validation and link validation still required alongside focused accessibility-relevant review? [Consistency]

## Notes

- Initial accessibility pass found one requirements-quality gap around programmatic selected/current state for custom controls; resolved in `spec.md` under Clarifications: Keyboard behavior.
