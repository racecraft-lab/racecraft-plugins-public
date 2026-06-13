# Documentation-Quality Checklist: Static docs framework and IA spike

**Purpose**: Validate that DOC-001's documentation requirements and spike output are complete, source-backed, measurable, and ready for DOC-002 handoff. This checklist tests requirements and research quality, not docs-site implementation.
**Created**: 2026-06-12
**Feature**: [spec.md](../spec.md)

**Note**: Generated from `/speckit-checklist documentation-quality` with focus on complete/measurable framework criteria, candidate acceptance/rejection rationale, DOC-002 handoff clarity, IA skeleton field clarity, and stale or unsourced framework/platform claims.

## Framework Comparison Completeness

- [x] CHK001 - Does the spike require and provide all four candidate stacks: Docusaurus/MDX, VitePress, Astro/Starlight, and repo-native fallback? [Completeness, Spec §FR-001, Report §Candidate Matrix]
- [x] CHK002 - Are all required comparison dimensions represented: static hosting, GitHub Pages, reusable interactivity, search, versioning, accessibility, link checking, docs-as-code workflow, maintenance load, commands, and support class? [Completeness, Spec §FR-002, Spec §SC-001, Report §Candidate Matrix]
- [x] CHK003 - Are support-class labels defined consistently for each candidate/capability rather than only embedded in some narrative cells? [Resolved, Spec §FR-002, Spec §Clarifications, Data Model §Evaluation Criterion] - was a gap. Resolved by adding Report §Support Class Legend and Evidence Bounds, then rewriting Report §Candidate Matrix cells with explicit built-in, official, official third-party hosted, community, external/manual, unsupported/blocked, unknown/weak, process-only, or qualitative labels.
- [x] CHK004 - Are hard blockers distinguished from weighted tradeoffs so the recommendation can be audited without reinterpreting the rubric? [Clarity, Spec §Clarifications, Report §Candidate Matrix]

## Candidate Decision Rationale

- [x] CHK005 - Does each candidate have an explicit accept, reject, defer, or fallback decision and a rationale tied to the comparison criteria? [Completeness, Spec §FR-004, Spec §FR-005, Report §Candidate Decisions]
- [x] CHK006 - Is the Astro/Starlight acceptance rationale measurable enough for DOC-002 to know what evidence would overturn it? [Measurability, Spec §FR-004, Report §DOC-002 Consumption]
- [x] CHK007 - Are negative claims about VitePress and Astro/Starlight first-party versioning or link-checking bounded by the refreshed source set and retrieval date rather than stated as unsupported absolutes? [Resolved, Spec §FR-003, Spec §Edge Cases, Report §Candidate Decisions] - was a gap. Resolved by adding Report §Support Class Legend and Evidence Bounds plus bounded-evidence notes under VitePress and Astro/Starlight candidate decisions, explicitly limiting the negative finding to the official source set refreshed on 2026-06-12.

## Source Evidence Freshness

- [x] CHK008 - Do current framework/platform claims in the spike report include official or local source evidence and the applicable retrieval/update dates, including `2026-06-12` and `2026-06-13`? [Traceability, Spec §FR-003, Spec §SC-006, Report §Live Source Evidence]
- [x] CHK009 - Does the plan avoid stale or unsourced framework-version assumptions, including the Docusaurus 3.10.x claim in Technical Context? [Resolved, Plan §Technical Context, Spec §FR-003] - was a gap. Resolved by changing Plan §Technical Context to state that official Docusaurus docs were refreshed at version 3.10.1 on 2026-06-12, that this is evidence only, and that DOC-002 must refresh current docs before installation.
- [x] CHK010 - Are third-party, community, paid, official, built-in, and unsupported capabilities distinguished wherever they affect acceptance or rejection? [Clarity, Spec §Clarifications, Data Model §Framework Candidate]

## DOC-002 Handoff Quality

- [x] CHK011 - Is exactly one default stack recommended for DOC-002 unless a hard blocker appears? [Clarity, Spec §FR-004, Report §Decision]
- [x] CHK012 - Can DOC-002 identify the recommended package manager plus minimum package, build, preview, test, and deployment commands without consulting another file? [Completeness, Spec §FR-006, Spec §SC-004, Report §Recommended Package and Commands]
- [x] CHK013 - Does the report state which DOC owns shell creation and which later DOC specs own route content? [Traceability, Spec §FR-008, Report §IA Skeleton, Report §DOC-002 Consumption]

## IA Skeleton Quality

- [x] CHK014 - Does every top-level IA route include route path, route label, primary Diataxis mode, optional secondary modes, target audience, route purpose, source evidence, success criterion, shell owner DOC, and full content owner DOC? [Completeness, Spec §FR-008, Report §IA Skeleton]
- [x] CHK015 - Are the 11 required PRD route labels covered with no placeholder values? [Coverage, Spec §Clarifications, Spec §SC-003, Report §IA Skeleton]
- [x] CHK016 - Are route purposes concise route-level skeleton fields rather than full page copy or implementation content? [Scope, Spec §Clarifications, Report §IA Skeleton]
- [x] CHK017 - Is every route's success criterion objectively checkable by a DOC-002 or later implementer? [Measurability, Spec §FR-008, Report §IA Skeleton]

## Scope Boundary and Reviewability

- [x] CHK018 - Are DOC-001 allowed write surfaces and forbidden implementation surfaces explicit and consistent across spec, plan, quickstart, and report? [Consistency, Spec §FR-010, Spec §FR-011, Plan §Constraints, Report §Scope Boundary Evidence]
- [x] CHK019 - Are package/build/test commands clearly report-only recommendations that do not authorize DOC-001 package, lockfile, site config, CI, README, marketplace, generated payload, or plugin behavior changes? [Clarity, Spec §FR-006, Spec §FR-010, Report §Recommended Package and Commands]
- [x] CHK020 - Can final diff scope be verified against the research-only boundary without interpreting implementation behavior? [Measurability, Spec §SC-005, Quickstart §Scenario 3]

## Notes

- Gap-tagged items are requirement-quality gaps that need evidence-grounded edits to DOC-001 artifacts before the checklist can close.
- No item in this checklist verifies a rendered docs site, package install, or runtime behavior.
- Post-remediation verification pass on 2026-06-12 found no new documentation-quality gaps after the support-class, evidence-bound, and Docusaurus-version-source edits.
- Decision update pass on 2026-06-13 updated the default-stack rationale to Astro/Starlight, added Astro portfolio context, and recorded Starlight community versioning/link-validation plugin evidence.
