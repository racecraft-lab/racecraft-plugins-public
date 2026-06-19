# Implementation Plan: TACD-003 Prerequisite and Documentation Messaging

**Branch**: `tacd-003-prerequisite-and-documentation-messaging` | **Date**: 2026-06-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/tacd-003-prerequisite-and-documentation-messaging/spec.md`

## Summary

Replace the fixed optional-tool prerequisite report with one successful
`capability_coverage` advisory, then align active prerequisite and limitation
guidance with capability-first discovery. Keep the slice narrow: one shell
script, focused Layer 4 coverage, and source Markdown updates only where active
setup guidance repeats the old optional-tool framing.

## Technical Context

**Language/Version**: Bash with `set -euo pipefail`; Markdown for active guidance

**Primary Dependencies**: `jq` for JSON emission and assertions; existing
SpecKit Pro shell helpers and docs sources

**Storage**: Checked-in repository files only; no database, browser storage, or
runtime service state

**Testing**: `bash tests/speckit-pro/run-all.sh --layer 4`,
`bash tests/speckit-pro/run-all.sh --layer 1`, and
`bash tests/speckit-pro/run-all.sh`

**Target Platform**: Claude Code and Codex plugin guidance distributed from the
SpecKit Pro marketplace source tree

**Project Type**: Plugin marketplace docs/process and shell harness update

**Performance Goals**: Prerequisite checks remain deterministic and fast enough
for setup/preflight use; no network calls or capability probing beyond existing
local checks

**Constraints**: Keep prerequisite output generic and capability-based; missing
optional capabilities remain non-blocking when fallback evidence is acceptable;
avoid fixed optional-tool preference wording; preserve concrete identifiers only
for platform metadata, exact file references, generated source-derived content,
or historical provenance; leave broad enforcement and eval updates to TACD-004

**Scale/Scope**: One prerequisite output path, active prerequisite/limitation
guidance, and focused deterministic regression coverage

**Reviewability Budget**: Primary surface docs/process; secondary surface
harness/adapter; projected 142 reviewable LOC, 1 production file, 5 total
implementation files; within the TACD-003 roadmap budget. Setup gate warning:
the broader roadmap spans two primary surfaces, but this slice stays as one
spec unless implementation grows beyond this plan.

## Declared File Operations

- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh
- MODIFIED tests/speckit-pro/layer4-scripts/test-check-prerequisites.sh
- MODIFIED speckit-pro/skills/speckit-autopilot/references/prerequisites.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/prerequisites-codex.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/plugin-limitations.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Plan Alignment |
|-----------|--------|----------------|
| I. Plugin Structure Compliance | PASS | Existing plugin layout is preserved; no new plugin component type is introduced. |
| II. Script Safety | PASS | The prerequisite script remains Bash with safe mode and JSON work handled through `jq` helpers. |
| III. Semantic Versioning | PASS | No plugin version or release metadata change is planned. |
| IV. Test Coverage Before Merge | PASS | Focused Layer 4 coverage is extended for the changed JSON output; Layer 1 and full verify remain required before implementation completion. |
| V. Conventional Commits | PASS | No commit is created in this phase; later PR title/commit must use an accepted conventional scope. |
| VI. KISS, Simplicity & YAGNI | PASS | One advisory replaces the named optional-tool inventory; no installer, marketplace integration, broad scanner, or eval rewrite is added. |

**Constitution concerns**: None. The only recorded warning is reviewability
surface breadth from the roadmap; the current five-file plan does not require a
split.

### Post-Design Constitution Re-check

PASS. Research and quickstart artifacts keep the design to one advisory, focused
docs, and existing shell tests. No complexity exception is required.

## Phase 0 Research

See [research.md](research.md). Key decisions:

- Model prerequisite capability coverage as one successful
  `capability_coverage` advisory with no per-tool inventory.
- Use setup-facing capability categories: codebase context, library
  documentation, web/domain research, and source extraction.
- Keep optional capability absence non-blocking unless no acceptable evidence
  path exists or a true setup gate fails.
- Treat generated payloads as source-derived and regenerate them only if source
  changes require parity.

## Phase 1 Design

No data model, API contract, or schema artifact is justified for this slice.
The user-visible behavior is a JSON advisory shape and Markdown guidance update,
both covered by the implementation plan and focused shell tests.

## Implementation Approach

1. Update `check-prerequisites.sh` so the old named optional-server result is
   replaced by one successful `capability_coverage` result. The message should
   describe the four capability categories and note confidence/fallback impact
   without reporting per-tool availability.
2. Extend `test-check-prerequisites.sh` to assert the new result name, `pass=true`
   behavior, absence of fixed optional-tool inventory, and preservation of
   successful setup when optional capability coverage is absent.
3. Update active prerequisite and limitation guidance in the declared Markdown
   files to explain capability-first discovery and fallback behavior in
   vendor-neutral language.
4. Review `speckit-pro/skills/speckit-coach/references/autopilot-guide.md` and
   adjacent autopilot entrypoint summaries for repeated active preflight or
   limitation wording. If an edit is required, amend the plan and budget before
   implementation expands past the five declared files.
5. Do not touch Layer 3 evals, Layer 5 pointer coverage, broad named-tool
   enforcement, or generated payload copies unless a declared source change
   requires parity regeneration.

## PR Review Packet Traceability

| Requirement | Planned Files | Verification Evidence |
|-------------|---------------|-----------------------|
| FR-001, FR-011 | `check-prerequisites.sh`; `test-check-prerequisites.sh` | Layer 4 assertions for one successful `capability_coverage` result and no per-tool inventory |
| FR-002, FR-003 | `check-prerequisites.sh`; `test-check-prerequisites.sh` | Layer 4 missing-optional-capability fixture remains successful and advisory-only |
| FR-004 | `prerequisites.md`; `prerequisites-codex.md`; `plugin-limitations.md` | Focused changed-doc assertions if the test file adds them; otherwise reviewer traceability plus Layer 1 structural validation |
| FR-005, FR-006 | Declared active docs plus reviewed adjacent guide scope | Review packet lists any concrete optional-tool names that remain as platform metadata, exact file references, generated content, or historical provenance |
| FR-007, FR-009 | Plan scope and PR packet non-goals | Review packet names TACD-004 for broad enforcement, eval expectation changes, and pointer coverage |
| FR-008 | `test-check-prerequisites.sh` | `bash tests/speckit-pro/run-all.sh --layer 4` |
| FR-010 | Source docs only; generated payloads only if regenerated from source | PR packet records any regeneration command or states none was required |

The PR description must include what changed, why, non-goals, review order,
scope budget, traceability, verification, known gaps, and rollback/flag notes.
It must also state that missing optional research or context capabilities remain
non-blocking when acceptable fallbacks exist.

## Project Structure

### Documentation (this feature)

```text
specs/tacd-003-prerequisite-and-documentation-messaging/
├── SPEC-MOC.md          # Preserved, not modified by this phase
├── spec.md              # Existing feature specification
├── plan.md              # This Plan phase output
├── research.md          # Phase 0 decision record
├── quickstart.md        # Focused implementation verification guide
└── checklists/
    └── requirements.md  # Existing specification checklist
```

### Source Code (repository root)

```text
speckit-pro/
├── skills/speckit-autopilot/
│   ├── scripts/check-prerequisites.sh
│   └── references/
│       ├── prerequisites.md
│       └── plugin-limitations.md
├── codex-skills/speckit-autopilot/references/
│   └── prerequisites-codex.md
└── tests/speckit-pro/layer4-scripts/
    └── test-check-prerequisites.sh
```

**Structure Decision**: Use the existing single-plugin source tree. The update
is split by existing ownership boundaries: script output, active guidance
Markdown, and focused deterministic shell tests.

## Complexity Tracking

No constitution violations or complexity exceptions are required.
