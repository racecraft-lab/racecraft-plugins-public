# Error-Handling Checklist: Static docs framework and IA spike

**Purpose**: Validate that DOC-001's fallback, blocker/tradeoff, repo-native fallback, and command-handoff requirements are complete, source-backed, and bounded to the research-only spike. This checklist tests requirements and research quality, not docs-site implementation.
**Created**: 2026-06-12
**Feature**: [spec.md](../spec.md)

**Note**: Generated from `/speckit-checklist error-handling` with focus on hard blockers vs tradeoffs, serious repo-native fallback evaluation, DOC-002 fallback if the selected stack's GitHub Pages path fails, and ambiguous package/build/test command requirements.

## Hard Blockers vs Tradeoffs

- [x] CHK001 - Are hard blockers explicitly defined before weighted scoring rather than inferred from candidate prose? [Clarity, Spec §Clarifications, Report §Candidate Matrix]
- [x] CHK002 - Does each candidate record GitHub Pages from this repository, reusable interactivity, accessible fallback, and DOC-001 no-implementation boundary outcomes? [Completeness, Spec §Clarifications, Report §Candidate Matrix]
- [x] CHK003 - Are search, link checking, versioning, maintenance load, and package-manager preference treated as weighted tradeoffs unless they create an explicit blocker? [Consistency, Spec §Clarifications, Report §Candidate Matrix]
- [x] CHK004 - Is the Astro/Starlight acceptance rationale specific enough for DOC-002 to know which later evidence would overturn it? [Measurability, Spec §FR-004, Report §Candidate Decisions]

## DOC-002 Failure and Recovery Behavior

- [x] CHK005 - Does the report define what DOC-002 should do if Astro/Starlight GitHub Pages deployment fails after source refresh? [Resolved, Spec §Edge Cases, Spec §FR-004, Report §DOC-002 Failure Handling and Fallback Rules, Report §DOC-002 Consumption] - was a gap. Resolved by adding configuration-vs-hard-blocker failure handling and an explicit Docusaurus/MDX, VitePress, repo-native fallback order.
- [x] CHK006 - Does the failure handling distinguish configuration or base-path issues from true hard blockers? [Clarity, Report §DOC-002 Consumption]
- [x] CHK007 - Is fallback routing bounded to research/report decisions rather than authorizing DOC-001 site, package, config, or CI work? [Scope, Spec §FR-010, Spec §FR-011]
- [x] CHK008 - Are search-provider or package-manager concerns prevented from becoming accidental hard blockers unless they create maintainership or dependency-policy risk? [Consistency, Spec §Clarifications, Report §Why This Wins]

## Repo-Native Fallback

- [x] CHK009 - Is the repo-native fallback evaluated against the same hard blockers and tradeoffs as framework candidates? [Completeness, Spec §FR-001, Spec §FR-002, Report §Candidate Matrix]
- [x] CHK010 - Does the report record repo-native fallback strengths, limitations, and entry conditions instead of treating it as missing data? [Resolved, Spec §Clarifications, Report §Candidate Decisions] - was a gap. Resolved by recasting repo-native Markdown as a serious low-dependency emergency fallback with explicit strengths, limitations, and entry conditions.
- [x] CHK011 - Is the repo-native fallback rejected for default only because it fails required capabilities without extra tooling? [Clarity, Report §Candidate Decisions]
- [x] CHK012 - Does fallback selection remain available if all framework candidates become blocked or too risky for this repository? [Coverage, Spec §Edge Cases, Spec §Clarifications]

## Package, Build, and Test Command Clarity

- [x] CHK013 - Is the package manager recommendation explicitly report-only for DOC-001 and owned by DOC-002 for implementation? [Scope, Spec §FR-006, Spec §FR-010, Report §Recommended Package and Commands]
- [x] CHK014 - Are setup, install, build, preview, validation/test, and deployment command roles separated clearly enough for DOC-002? [Resolved, Spec §SC-004, Data Model §Command Recommendation, Report §Recommended Package and Commands] - was a gap. Resolved by separating scaffold/setup, dependency install, development preview, production build, local static preview, minimum validation/test, and deployment command roles.
- [x] CHK015 - Does the report say DOC-002 must define or normalize actual package scripts after scaffolding? [Clarity, Report §Recommended Package and Commands]
- [x] CHK016 - Is the minimum future validation command identified as the docs-site build/link-check gate rather than a DOC-001 test run? [Measurability, Spec §FR-006, Report §Recommended Package and Commands]

## Scope Boundary and Reviewability

- [x] CHK017 - Are allowed DOC-001 write surfaces and forbidden implementation surfaces consistent across spec, plan, quickstart, and report? [Consistency, Spec §FR-010, Plan §Constraints, Quickstart §Scenario 3, Report §Scope Boundary Evidence]
- [x] CHK018 - Can reviewers close this checklist by reading DOC-001 artifacts without installing a docs framework or running a browser? [Measurability, Spec §SC-005, Quickstart §Scenario 3]
- [x] CHK019 - Are recovery decisions assigned to DOC-002 or later DOC specs without expanding DOC-001 implementation scope? [Scope, Spec §FR-011, Report §DOC-002 Consumption]
- [x] CHK020 - Does the checklist avoid verifying rendered site behavior before DOC-002 creates the shell? [Scope, Spec §FR-011]

## Notes

- Initial error-handling pass found three requirement-quality gaps: selected-stack GitHub Pages failure handling, repo-native fallback seriousness, and command-role clarity.
- All three gaps were remediated inside the DOC-001 research report and SpecKit artifacts.
- Post-remediation verification pass on 2026-06-12 found no new error-handling gaps after the fallback-rule, repo-native fallback, and command-role edits.
- Decision update pass on 2026-06-13 updated selected-stack references from Docusaurus to Astro/Starlight without expanding DOC-001 implementation scope.
