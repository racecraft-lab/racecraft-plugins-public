# Integration Checklist: Safe Interactive Selector and Validation Aids

**Purpose**: Validate DOC-006 integration requirements before task generation
**Created**: 2026-06-17
**Feature**: [spec.md](../spec.md)
**Domain prompt**: `/speckit-checklist integration`

Focus areas:

- Build-time reads from checked-in marketplace and plugin manifest JSON.
- Repository-only manifest/version checker output.
- Source/dist payload distinction and command metadata freshness.
- Drift between `.claude-plugin`, `.agents/plugins`, `speckit-pro/*plugin.json`, and `dist/**` values.

## Manifest Source Boundaries

- [x] INT001 [Spec FR-007, Plan Technical Context] Are build-time manifest-backed values required to come from checked-in repository JSON or manifest sources? [Completeness]
- [x] INT002 [Spec FR-008, Clarifications: Command metadata source boundary] Is install Markdown parsing explicitly excluded as a machine data source? [Clarity]
- [x] INT003 [Spec FR-008, Plan Implementation Boundaries] Is committed persistent generated selector/checker metadata explicitly disallowed? [Consistency]
- [x] INT004 [Spec FR-009, Data Model: ManifestSource] Are all six source and distribution manifest paths named as required checker inputs? [Coverage]
- [x] INT005 [Spec Clarifications: Metadata checker inputs] Are installed cache files, user home-directory files, pasted JSON, and browser-local configuration excluded as data sources? [Coverage]

## Build-Time Data Flow

- [x] INT006 [Spec FR-007, Plan Summary] Does the spec require docs content generation to read checked-in manifest JSON at build time rather than browser runtime? [Clarity]
- [x] INT007 [Spec FR-007, Clarifications: Command metadata source boundary] Are curated command sequences, prerequisites, success signals, and handoff labels allowed only as checked-in docs metadata when absent from manifests? [Completeness]
- [x] INT008 [Spec FR-007, Clarifications: Command metadata source boundary] Must curated docs metadata use or cross-check JSON-derived variables for manifest-backed fields? [Consistency]
- [x] INT009 [Plan Structure Decision] Is source-derived manifest reading isolated to a small docs data helper instead of scattered across route content? [Simplicity]

## Repository-Only Checker Output

- [x] INT010 [Spec FR-009, FR-011] Is the manifest/version checker scoped to repository metadata rather than local user diagnostics? [Clarity]
- [x] INT011 [Spec FR-010, SC-003] Are compared values, pass or mismatch state, and the expected consistency rule required for every repository metadata comparison? [Measurability]
- [x] INT012 [Spec FR-010, Clarifications: Checker comparison rules] Are equality checks limited to stable consistency fields such as plugin name, version, marketplace source/path, and counterpart presence? [Coverage]
- [x] INT013 [Spec FR-010, Data Model: ManifestConsistencyComparison] Are comparison rows required to carry source labels, displayed values, state, severity, and handoff information? [Completeness]
- [x] INT014 [Spec FR-016, Clarifications: Mismatch and unavailable handoffs] Are mismatch, unavailable, and caution outputs bounded to lightweight handoffs instead of full troubleshooting behavior? [Consistency]

## Source And Distribution Payload Boundaries

- [x] INT015 [Spec FR-009, Data Model: ManifestSource] Are Claude source, Codex source, Claude dist, Codex dist, and marketplace entries represented as distinct repository inputs? [Coverage]
- [x] INT016 [Spec FR-010, Clarifications: Checker comparison rules] Are intentional platform packaging differences displayed as informational context instead of false mismatches? [Clarity]
- [x] INT017 [Spec FR-012, Data Model: GeneratedPayloadDiagramNode] Does the generated-payload diagram distinguish source tree, Claude distribution, Codex distribution, marketplace entries, and Codex cache as separate nodes? [Consistency]
- [x] INT018 [Plan Implementation Boundaries] Does the plan include a stop-and-record rule for actual source manifest mismatches before modifying source manifests? [Risk Control]

## Command Metadata Freshness And Platform Separation

- [x] INT019 [Spec FR-004, FR-007, SC-002] Are selector path command records required to combine curated guidance with JSON-derived manifest-backed values where applicable? [Completeness]
- [x] INT020 [Spec FR-005, FR-006, Clarifications: Platform command boundaries] Are Claude Code and Codex command surfaces required to stay separate in selected path guidance? [Consistency]
- [x] INT021 [Spec Clarifications: Expected success signals] Are expected success signals defined separately for Claude Code and Codex command blocks? [Coverage]
- [x] INT022 [Spec FR-017, Quickstart Focused Validation] Does focused validation require detection of drift between manifest-backed rendered values and the six checked-in manifest files? [Measurability]

## Validation Coverage

- [x] INT023 [Spec FR-017, SC-006] Are passing, mismatch, and unavailable metadata states required in focused metadata/rendering validation? [Coverage]
- [x] INT024 [Spec FR-017, Quickstart Focused Validation] Does validation cover no pasted-JSON or local-diagnostic UI, handoff links, checkpoint coverage, and required selector fields? [Completeness]
- [x] INT025 [Plan Validation Plan, Quickstart] Are standard docs validation and link validation required in addition to the DOC-006 focused fixture? [Consistency]
- [x] INT026 [Constitution IV, Plan Constitution Check] Does the plan tie integration behavior to merge-blocking validation evidence before implementation is considered complete? [Traceability]

## Notes

- No integration requirements gaps were found. Current spec, plan, data model, contract, and quickstart artifacts cover the requested manifest-source, repository-only checker, source/dist boundary, command freshness, and drift-validation concerns.
