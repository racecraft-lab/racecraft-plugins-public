# Accessibility Checklist: Static docs framework and IA spike

**Purpose**: Validate that DOC-001's accessibility, keyboard, static fallback, and responsive UX requirements are complete, source-backed, measurable, and bounded to the research-only spike. This checklist tests requirements and research quality, not docs-site implementation.
**Created**: 2026-06-12
**Feature**: [spec.md](../spec.md)

**Note**: Generated from `/speckit-checklist accessibility` with focus on framework accessibility testing, keyboard/static fallback support, DOC-010 IA ownership, and avoiding inaccessible rich-interaction promises.

## Framework Accessibility Coverage

- [x] CHK001 - Does the framework comparison include accessibility as a required evaluation dimension for every candidate? [Completeness, Spec §FR-002, Report §Candidate Matrix]
- [x] CHK002 - Is the accessible static or keyboard-usable fallback path treated as a hard blocker before weighted scoring? [Clarity, Spec §Clarifications, Report §Candidate Matrix]
- [x] CHK003 - Are accessibility support claims tied to source evidence or clearly labeled as project discipline instead of framework guarantees? [Traceability, Spec §FR-003, Report §Live Source Evidence]
- [x] CHK004 - Does the comparison distinguish framework support for static/keyboard fallback from future accessibility testing obligations? [Resolved, Spec §FR-002, PRD §DOC-FR-001, Roadmap §DOC-010, Report §Candidate Matrix] - was a gap. Resolved by adding W3C/WAI evidence, a support/evidence-bound note that splits accessible fallback from DOC-010 testing, and a separate accessibility testing and validation handoff row in the candidate matrix.
- [x] CHK005 - Is the repo-native fallback assessed for both Markdown accessibility strengths and missing interactive-aid obligations? [Completeness, Spec §Clarifications, Report §Candidate Matrix]

## Keyboard and Static Fallback Requirements

- [x] CHK006 - Are keyboard-usable controls, focus behavior, labels, contrast, and static fallback requirements represented in the DOC-001 source context? [Traceability, PRD §DOC-FR-006, PRD §DOC-FR-010]
- [x] CHK007 - Does the spike avoid treating MDX/React, Vue, or Astro component support as sufficient evidence of accessible interaction? [Clarity, Spec §Clarifications, Report §Why This Wins]
- [x] CHK008 - Are no-JavaScript or static fallback expectations explicit for route-level interactive aids such as selectors, command blocks, and lifecycle diagrams? [Coverage, PRD §AC-6.2, PRD §AC-6.5, Report §IA Skeleton]
- [x] CHK009 - Does the report constrain future rich interactivity with keyboard/static fallback obligations rather than promising inaccessible interactive behavior? [Resolved, Spec §Clarifications, PRD §DOC-FR-006, Report §Accessibility and Interaction Guardrails] - was a gap. Resolved by adding report guardrails for static fallback, keyboard operation, visible focus, labels or accessible names, status/error text, contrast/reflow, and no browser-side local command execution or config mutation.
- [x] CHK010 - Are browser-side local command execution and config mutation excluded from interactive docs requirements? [Consistency, PRD §Out of scope, Report §Recommended Package and Commands]

## DOC-010 Ownership and IA Hardening

- [x] CHK011 - Does the IA skeleton identify the routes where DOC-010 owns search, accessibility, responsive UX, deep-link, and validation hardening? [Resolved, PRD §DOC-FR-010, Roadmap §DOC-010, Report §DOC-010 Route Hardening Coverage] - was a gap. Resolved by adding DOC-010 hardening coverage for all top-level routes, `/choose-your-path`, `/spec-kit-lifecycle`, and `/glossary`, and by naming DOC-010 as a full-content hardening owner for the affected IA rows.
- [x] CHK012 - Does every route with interactive or visual behavior name a later owner for full content or hardening work? [Traceability, Spec §FR-008, Report §IA Skeleton]
- [x] CHK013 - Are DOC-002 shell ownership and DOC-006/DOC-010 interaction-hardening ownership separated clearly enough for downstream implementers? [Consistency, Spec §FR-008, Report §DOC-002 Consumption]
- [x] CHK014 - Are responsive mobile and desktop install workflow obligations deferred to DOC-010 without being omitted from the handoff? [Coverage, PRD §AC-10.5, Roadmap §DOC-010]

## Scope Boundary and Testability

- [x] CHK015 - Are accessibility checks described as future docs-site validation rather than DOC-001 implementation work? [Scope, Spec §FR-010, Spec §FR-011, Report §Known Gaps and Follow-Ups]
- [x] CHK016 - Are future accessibility validation requirements measurable without requiring DOC-001 to add package files, test tooling, CI, or site config? [Measurability, Spec §SC-005, Report §Scope Boundary Evidence]
- [x] CHK017 - Does the plan keep accessibility and responsive goals report-only until the site exists? [Consistency, Plan §Technical Context, Plan §Constraints]
- [x] CHK018 - Are accessibility-related source inputs and later-owner decisions traceable to the PRD and roadmap rather than invented in the spike report? [Traceability, PRD §DOC-FR-010, Roadmap §DOC-010]
- [x] CHK019 - Does the checklist avoid asking reviewers to verify rendered UI behavior before DOC-002/DOC-006/DOC-010 create the site? [Scope, Spec §FR-011]
- [x] CHK020 - Can a reviewer close accessibility gaps by reading DOC-001 artifacts without running a browser or installing a docs framework? [Measurability, Spec §SC-005, Quickstart §Scenario 3]

## Notes

- Gap-tagged items are requirement-quality gaps that need evidence-grounded edits to DOC-001 artifacts before the checklist can close.
- No item in this checklist verifies a rendered docs site, package install, accessibility test run, or runtime behavior.
- Post-remediation verification pass on 2026-06-12 found no new accessibility gaps after the testing-handoff, interaction-guardrail, and DOC-010 route-hardening edits.
