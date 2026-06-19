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

**Testing**: `bash -n speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh`,
`bash tests/speckit-pro/run-all.sh --layer 4`,
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
guidance, adjacent coach/autopilot guidance that repeats active preflight or
research-capability wording, and focused deterministic regression coverage

**Reviewability Budget**: Primary surface docs/process; secondary surface
harness/adapter; projected 190 reviewable LOC, 1 production file, 8 total
implementation files; within the TACD-003 roadmap budget. The current plan
estimator reports 8 modified declared entries and 0 new production LOC because
this slice edits existing files. Setup gate warning: the broader roadmap spans
two primary surfaces, but this slice stays as one spec unless implementation
grows beyond this plan.

## Declared File Operations

- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh
- MODIFIED tests/speckit-pro/layer4-scripts/test-check-prerequisites.sh
- MODIFIED speckit-pro/skills/speckit-autopilot/references/prerequisites.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/prerequisites-codex.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/plugin-limitations.md
- MODIFIED speckit-pro/skills/speckit-coach/references/autopilot-guide.md
- MODIFIED speckit-pro/skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/SKILL.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Plan Alignment |
|-----------|--------|----------------|
| I. Plugin Structure Compliance | PASS | Existing plugin layout is preserved; no new plugin component type is introduced. |
| II. Script Safety | PASS | The prerequisite script remains Bash with safe mode, syntax validation through `bash -n`, and JSON work handled through `jq` helpers. |
| III. Semantic Versioning | PASS | No plugin version or release metadata change is planned. |
| IV. Test Coverage Before Merge | PASS | Focused Layer 4 coverage is extended for the changed JSON output; Layer 1 and full verify remain required before implementation completion. |
| V. Conventional Commits | PASS | No commit is created in this phase; later PR title/commit must use an accepted conventional scope. |
| VI. KISS, Simplicity & YAGNI | PASS | One advisory replaces the named optional-tool inventory; no installer, marketplace integration, broad scanner, or eval rewrite is added. |

**Constitution concerns**: None. The only recorded warning is reviewability
surface breadth from the roadmap; the current eight-file plan remains within
the TACD-003 spec budget and does not require a split.

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
   without reporting per-tool availability. Preserve JSON-only stdout and the
   existing stable top-level/check fields so workflow callers and tests can
   parse the output deterministically.
2. Extend `test-check-prerequisites.sh` to assert the new result name, `pass=true`
   behavior, absence of fixed optional-tool inventory, and preservation of
   successful setup when optional capability coverage is absent. Keep the
   existing valid-JSON coverage and add focused assertions for the changed
   advisory field shape plus at least one true prerequisite blocker that remains
   `all_pass=false` with an actionable message. Run `bash -n` against the
   edited prerequisite script before the focused Layer 4 suite.
3. Update active prerequisite, limitation, coach, and autopilot guidance in the
   declared Markdown files to explain capability-first discovery and fallback
   behavior in vendor-neutral language.
4. During docs review, classify any repository-specific claim against Racecraft
   source or generated artifacts and any platform/vendor behavior claim against
   official vendor evidence. Remove or reword claims without the required
   evidence, then record the evidence class in the PR packet.
5. Update adjacent autopilot entrypoint summaries only where they repeat current
   preflight, limitation, or research-capability wording. If review finds a
   declared adjacent file needs no source edit, record the no-op decision in the
   PR packet rather than expanding scope elsewhere.
6. Do not touch Layer 3 evals, Layer 5 pointer coverage, or broad named-tool
   enforcement. Generated payload copies are regenerated only from the declared
   source changes when payload parity requires it; Layer 1 payload validation
   rebuilds `dist/claude/speckit-pro` and `dist/codex/speckit-pro`.

## PR Review Packet Traceability

| Requirement | Planned Files | Verification Evidence |
|-------------|---------------|-----------------------|
| FR-001, FR-011, FR-013 | `check-prerequisites.sh`; `test-check-prerequisites.sh` | `bash -n` for script syntax plus Layer 4 assertions for one successful `capability_coverage` result, no per-tool inventory, JSON-parseable stdout, stable top-level/check fields, and no non-JSON stdout diagnostics |
| FR-002, FR-003, FR-012, FR-014 | `check-prerequisites.sh`; `test-check-prerequisites.sh`; declared active guidance docs | Layer 4 missing-optional-capability fixture remains successful and advisory-only; existing true-blocker fixture remains `all_pass=false` with an actionable message; changed guidance has no escalation instruction triggered solely by absent optional coverage |
| FR-004 | `prerequisites.md`; `prerequisites-codex.md`; `plugin-limitations.md` | Focused changed-doc assertions if the test file adds them; otherwise reviewer traceability plus Layer 1 structural validation |
| FR-005, FR-006 | `autopilot-guide.md`; `speckit-autopilot/SKILL.md`; `codex-skills/speckit-autopilot/SKILL.md`; declared prerequisite and limitation docs | Review packet lists any concrete optional-tool names that remain as platform metadata, exact file references, generated content, or historical provenance |
| Repo/platform evidence boundary | Declared active guidance docs and PR packet traceability | Review evidence classifies repository-specific claims with Racecraft source or generated-artifact citations and platform/vendor behavior claims with official vendor evidence; reviewer checks that no uncited platform behavior claim is introduced |
| FR-007, FR-009 | Plan scope and PR packet non-goals | Review packet names TACD-004 for broad enforcement, eval expectation changes, and pointer coverage |
| FR-008 | `test-check-prerequisites.sh` | `bash tests/speckit-pro/run-all.sh --layer 4` |
| FR-010 | Source docs plus source-derived payload copies only when regenerated from source | PR packet records the payload regeneration command/evidence or states none was required |
| SC-007, SC-008 | `test-check-prerequisites.sh`; PR packet verification evidence | Review packet reports focused JSON parseability and true-blocker preservation evidence from Layer 4, not TACD-004 static/eval enforcement |

The PR description must include what changed, why, non-goals, review order,
scope budget, traceability, verification, known gaps, and rollback/flag notes.
It must also state that missing optional research or context capabilities remain
non-blocking when acceptable fallbacks exist.

Repository-specific guidance separation is verified through review evidence,
not broad static enforcement in TACD-003. The PR packet must include a
`Repo vs Platform Evidence` subsection that lists changed repository-specific
claims with Racecraft source or generated-artifact citations and any
platform/vendor behavior claims with official vendor evidence. Missing evidence
is a docs review blocker for TACD-003; broad automated detection remains
TACD-004 scope.

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
│   ├── SKILL.md
│   ├── scripts/check-prerequisites.sh
│   └── references/
│       ├── prerequisites.md
│       └── plugin-limitations.md
├── skills/speckit-coach/references/
│   └── autopilot-guide.md
├── codex-skills/speckit-autopilot/
│   ├── SKILL.md
│   └── references/
│       └── prerequisites-codex.md
└── tests/speckit-pro/layer4-scripts/
    └── test-check-prerequisites.sh
```

**Structure Decision**: Use the existing single-plugin source tree. The update
is split by existing ownership boundaries: script output, active guidance
Markdown, and focused deterministic shell tests.

## Complexity Tracking

No constitution violations or complexity exceptions are required.
