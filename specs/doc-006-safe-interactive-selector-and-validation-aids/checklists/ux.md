# UX Checklist: Safe Interactive Selector and Validation Aids

**Purpose**: Validate DOC-006 user-flow and interaction requirements before task generation
**Created**: 2026-06-17
**Feature**: [spec.md](../spec.md)
**Domain prompt**: `/speckit-checklist ux`

Focus areas:

- Platform/path and install-scope selector flow on `choose-your-path`.
- Copyable command blocks with visible platform/scope labels, prerequisites, expected success signals, and next links.
- First-run checklist and selector mismatch handoffs.
- Whether users can get the right command sequence without reading unrelated platform guidance.

## Selector Decision Flow

- [x] UX001 [Spec FR-001, FR-002, SC-001] The primary selector surface is the existing `choose-your-path` route, so users start in the same place where platform choice is expected.
- [x] UX002 [Spec FR-002, FR-003, AC-1.4] Platform and supported install-scope choices are required, including scope updates for paths with multiple supported scopes.
- [x] UX003 [Spec FR-005, FR-006, Clarifications: Platform command boundaries] Selected Claude Code and Codex guidance must keep command records separate and use the correct command vocabulary for each platform.
- [x] UX004 [Spec SC-001, SC-002] Requirements define a measurable user outcome for finding the correct path and require complete field coverage for every supported selector path.
- [x] UX005 [Spec Edge Cases] Paths with no additional install-scope choices must still present complete guidance without implying unsupported scopes.

## Command Guidance

- [x] UX006 [Spec FR-004, SC-002] Each selected path must show platform label, install-scope label where applicable, prerequisites, copyable command blocks, expected success signals, and next documentation links.
- [x] UX007 [Spec Clarifications: Expected success signals] Claude Code success signals and Codex success signals are defined separately enough for users to verify the selected path without cross-reading the other platform page.
- [x] UX008 [Spec Clarifications: Copy affordance boundary] Copy buttons are optional progressive enhancement, while raw commands remain visible and selectable in normal code blocks.
- [x] UX009 [Spec FR-015, Edge Cases] Browser behavior is explicitly forbidden from running shell commands, reading local files, writing config, installing plugins, or invoking local plugin workflows.
- [x] UX010 [Plan Implementation Boundaries] The plan keeps command guidance in one route-centered docs slice and prohibits install Markdown parsing as a data source.

## Static Fallback And Progressive Enhancement

- [x] UX011 [Spec FR-014, SC-004] Selector, checker, diagram, and checklist content must remain present as semantic static fallback content when scripting is unavailable.
- [x] UX012 [Spec Clarifications: Semantic fallback content] The selector fallback must include every supported path with platform, scope, prerequisites, command label or sequence, success signal, and next link; `noscript`-only fallback is insufficient.
- [x] UX013 [Spec Clarifications: Static-first component shape] The component shape allows MDX plus one small Astro component while preserving complete static HTML.
- [x] UX014 [Plan Performance Goals] Progressive enhancement is constrained to small, non-blocking filtering or selection behavior.

## Handoffs And Mismatch States

- [x] UX015 [Spec FR-016, Clarifications: Mismatch and unavailable handoffs] Mismatch, unavailable, and caution states must show the consistency rule, compared or unavailable values, and lightweight handoffs.
- [x] UX016 [Spec Clarifications: Mismatch and unavailable handoffs] Handoffs are explicitly prevented from becoming cache diagnosis, update procedure, rollback guide, symptom matrix, or security/trust model content.
- [x] UX017 [Data Model: TroubleshootingHandoff] Handoff records include audience and scope, which is enough to keep installer, maintainer, and evaluator next links distinct.

## First-Run Checklist And Diagram UX

- [x] UX018 [Spec FR-012, Clarifications: Accessible payload diagram] The payload diagram requirements identify all required nodes and require information to be available through text-backed headings, list items, or table rows.
- [x] UX019 [Spec FR-013, Data Model: FirstRunCheckpoint] First-run checkpoint coverage includes platform route, Spec Kit CLI, constitution, roadmap or SPEC-ID, `gh`, `jq`, branch/worktree state, scaffold output, and docs validation evidence.
- [x] UX020 [Spec US3 Independent Test, AC-3.1] Static fallback expectations cover the generated payload diagram and first-run checklist when browser scripting is disabled.

## Keyboard And Interaction Clarity

- [x] UX021 [Spec FR-014, AC-3.2, SC-005] Keyboard-only use is specified for selector, checker, diagram, and checklist controls.
- [x] UX022 [Spec Clarifications: Keyboard behavior] Tab order, Space/Enter activation, visible focus, and selected-state distinction are explicitly required.
- [x] UX023 [Plan Validation Plan, Quickstart] Manual keyboard/static fallback review and focused metadata/rendering validation are both required before implementation is considered done.

## Validation Coverage

- [x] UX024 [Spec FR-017, SC-006] Focused validation must cover selector required fields, command-surface leakage, checker states, handoff links, first-run checkpoint coverage, and manifest-backed field drift.
- [x] UX025 [Quickstart: Focused Validation] The focused validation command has explicit coverage for required selector fields, command separation, pass/mismatch/unavailable states, no local diagnostic UI, handoff links, checkpoint coverage, and source drift.
- [x] UX026 [Plan Validation Plan] Standard docs validation and link validation remain required alongside the focused fixture.

## Notes

- No UX gaps were found in the current spec and plan. The implementation still needs to prove the requirements through the focused fixture, docs validation, link validation, and manual keyboard/static fallback review defined in the plan and quickstart.
