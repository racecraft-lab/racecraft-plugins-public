# Data Integrity Checklist: Repository Foundation for CI/CD Pipeline

**Purpose**: Validate data integrity requirements quality for version management artifacts, JSON structure preservation, and sync script data safety
**Created**: 2026-03-24
**Feature**: [spec.md](../spec.md)

## Requirement Completeness

- [ ] CHK001 - Are version string format requirements defined with an explicit regex pattern for all artifacts (plugin.json, marketplace.json, .release-please-manifest.json)? [Completeness, Spec §FR-004, Spec §Key Entities]
- [x] CHK002 - Is the semver validation requirement specified for the sync script (i.e., must the script validate that version strings read from plugin.json conform to the semver pattern before writing them to marketplace.json)? [Gap -- RESOLVED: Added "Invalid semver in plugin.json" edge case to spec.md, semver validation design to plan.md, and test coverage to FR-012]
- [x] CHK003 - Are all non-version fields in marketplace.json explicitly listed as fields the sync script MUST preserve during writes (name, source, description, owner, top-level metadata)? [Gap -- RESOLVED: Added explicit field preservation and forward-compatibility clause to FR-005]
- [ ] CHK004 - Is the requirement for the release-please-config.json `jsonpath` value (`$.version`) specified with enough precision to distinguish it from alternative JSONPath syntaxes (e.g., dot-notation vs bracket-notation)? [Clarity, Spec §FR-003]
- [x] CHK005 - Are requirements defined for what happens when `.release-please-manifest.json` version does not match plugin.json version at bootstrap time? [Gap -- RESOLVED: Added "Manifest/plugin.json version mismatch at bootstrap" edge case to spec.md]
- [x] CHK006 - Is the relationship between release-please-config.json package keys and .release-please-manifest.json keys specified with a consistency constraint (e.g., keys MUST match exactly)? [Completeness -- PASS: FR-004 now states "Manifest keys MUST match the corresponding `packages` keys in `release-please-config.json` exactly (no trailing slash)"]

## Requirement Clarity

- [ ] CHK007 - Is "valid semver" defined with a specific regex pattern in the spec (not just prose), and is that pattern consistent across all sections that reference it? [Clarity, Spec §Assumptions]
- [x] CHK008 - Is the sync script's JSON write format specified (e.g., indentation, trailing newline, key ordering) to ensure deterministic output for idempotency checks? [Clarity -- PASS: spec.md Assumptions section documents jq output format; plan.md "jq Output Format" section specifies default pretty-print, no --sort-keys]
- [ ] CHK009 - Is "descriptive error message" quantified with minimum content requirements (e.g., must include file path, expected vs actual state) for each error scenario in FR-008? [Clarity, Spec §FR-008]
- [ ] CHK010 - Is "unreadable" in FR-008 defined with exhaustive conditions (file permissions, invalid JSON, empty file), or is the parenthetical clarification sufficient? [Clarity, Spec §FR-008]

## Requirement Consistency

- [ ] CHK011 - Are the semver pattern references consistent between the constitution (`^[0-9]+\.[0-9]+\.[0-9]+$`) and the data model's manifest validation rules? [Consistency, Constitution §III vs Data Model §2]
- [x] CHK012 - Is the release-please-config.json `packages` key format consistent between the data model (no trailing slash: `"speckit-pro"`) and the spec/manifest (trailing slash in manifest: `"speckit-pro/"`)? [Conflict -- RESOLVED: Fixed spec.md FR-004, acceptance scenarios, and clarifications to use `speckit-pro` without trailing slash, matching data model and research.md decision]
- [ ] CHK013 - Are the marketplace.json field names used by the sync script consistent between the spec (§FR-005 references `source` and `version`) and the data model (§4 lists `name`, `source`, `version`)? [Consistency, Spec §FR-005 vs Data Model §4]

## Scenario Coverage

- [ ] CHK014 - Are requirements defined for what happens when the sync script encounters a plugin.json with a version value that is not a string (e.g., a number or null)? [Coverage, Edge Case]
- [ ] CHK015 - Are requirements defined for what happens when marketplace.json contains duplicate plugin entries (same source path appearing twice)? [Coverage, Edge Case]
- [x] CHK016 - Are requirements defined for concurrent execution of the sync script (e.g., two CI jobs running simultaneously)? [Gap -- RESOLVED: Added explicit out-of-scope assumption to spec.md Assumptions section with rationale reference to plan.md Atomic Write Decision]
- [x] CHK017 - Are requirements defined for marketplace.json file encoding (UTF-8, BOM handling) to prevent corruption on cross-platform execution? [Gap -- RESOLVED: Added UTF-8/no-BOM assumption to spec.md Assumptions section]
- [ ] CHK018 - Are requirements defined for what happens when the sync script's jq write-back produces a partial write (e.g., disk full mid-write, process killed)? [Coverage, Spec §Plan: Atomic Write Decision]
- [x] CHK019 - Are requirements defined for marketplace.json entries that have additional fields beyond name/source/version/description (i.e., forward-compatibility of the sync script with future schema extensions)? [Gap -- RESOLVED: Added forward-compatibility clause to FR-005 requiring preservation of "any unknown fields not listed here"]

## Acceptance Criteria Quality

- [ ] CHK020 - Is the acceptance criterion for idempotency (SC-003, FR-009) measurable — does it specify HOW to verify "zero file modifications" (e.g., file timestamp unchanged, git status clean, byte-for-byte comparison)? [Measurability, Spec §SC-003]
- [ ] CHK021 - Is the acceptance criterion for version correctness (SC-002) measurable — does "corrects 100% of version entries" define what "correct" means (exact string match with plugin.json version field)? [Measurability, Spec §SC-002]
- [ ] CHK022 - Are the error message acceptance criteria (SC-006) measurable — is "clear, actionable error message" defined with specific content requirements per failure mode? [Measurability, Spec §SC-006]

## Edge Case Coverage

- [x] CHK023 - Are requirements defined for the case where marketplace.json's `plugins` array is empty (zero entries) — should the sync script succeed silently or warn? [Edge Case -- RESOLVED: Added "Empty plugins array" edge case to spec.md specifying exit success with informational message]
- [ ] CHK024 - Are requirements defined for the case where the `source` field contains a relative path with nested directories (e.g., `./plugins/speckit-pro`) rather than a single-level path? [Edge Case, Spec §FR-005]
- [ ] CHK025 - Are requirements defined for the case where plugin.json version contains a semver pre-release suffix (e.g., `1.0.0-beta.1`)? The constitution regex `^[0-9]+\.[0-9]+\.[0-9]+$` would reject this, but release-please may produce it. [Edge Case, Conflict]
- [ ] CHK026 - Are requirements defined for the case where marketplace.json has JSON comments or trailing commas (non-standard JSON extensions)? [Edge Case]

## Non-Functional Requirements

- [ ] CHK027 - Is the performance requirement (SC-005: under 5 seconds for 10 plugins) specified with a measurement method (wall-clock time, which system, cold/warm)? [Measurability, Spec §SC-005]
- [x] CHK028 - Are data integrity requirements specified for the relationship between `release-please-config.json` and `.release-please-manifest.json` (e.g., must package keys be a subset, superset, or exact match)? [Gap -- RESOLVED: Added explicit key matching constraint to FR-004: "Manifest keys MUST match the corresponding `packages` keys in `release-please-config.json` exactly (no trailing slash)"]

## Dependencies & Assumptions

- [x] CHK029 - Is the assumption that `jq` preserves JSON field ordering documented, and is this assumption validated against jq's actual behavior (jq does preserve object key order)? [Assumption -- RESOLVED: Added jq key ordering assumption to spec.md Assumptions section]
- [ ] CHK030 - Is the assumption that release-please's GenericJson updater correctly handles the `$.version` JSONPath validated against release-please documentation? [Assumption, Spec §FR-003]
- [x] CHK031 - Is the dependency on `jq`'s specific output formatting (indentation style, newline behavior) documented, given that idempotency depends on deterministic output? [Dependency -- RESOLVED: Added jq output format assumption to spec.md Assumptions and jq Output Format design section to plan.md]

## Notes

- Check items off as completed: `[x]`
- Add comments or findings inline
- Items are numbered sequentially for easy reference
- Focus areas: semver validation, marketplace.json structure preservation, release-please jsonpath correctness, manifest version accuracy, partial write safety
