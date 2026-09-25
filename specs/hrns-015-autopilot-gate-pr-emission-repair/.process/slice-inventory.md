# HRNS-015 proposed review-slice path inventory

This is the planned **per-PR** changed-path ceiling after the user's instruction to resolve the five-slice budget blockers while preserving all 29 FRs. It supersedes the five-slice baseline. Every listed generated reference page is a conservative candidate: it counts against the planning cap even if the generator ultimately produces no diff. The actual changed-file and LOC gates remain unmeasured. The current `pr_marker_plan` validator rejects duplicate declared paths across markers; common runner, suite-manifest, and generated trust paths recur below. Consequently this is a concrete allocation proposal, **not a valid persisted marker plan or a G6 pass** until that contract is repaired and the exact marker gates run.

## Limits and evidence

- Ordered review increments: A1 → A2 → A3 → B1 → B2 → B3 → C1a1 → C1a2 → C1b → C2a → C2b. This retains every user story, both host variants, the original C1a/C1b distinction, and the A-before-HRNS-016 dependency. Each increment owns an independent RED → fix → GREEN checkpoint before its PR; shared paths may be edited and counted again in a later PR.
- Per PR: at most four changed production Python/schema/active-config paths, and at most 24 total changed paths including tests, fixtures, docs, `dist`, trust files, and generated reference pages. A path is counted once within a PR even if several tasks touch it. An additional path, unexpected generated output, or failed gate stops that increment before PR emission.
- The fixture files below are **one proposed compact dataset per named test group**, with cases inside each file. If RED coverage needs another child file, update this inventory and reallocate before editing. Existing tests amended in a later increment count again. New test module names change generated `reference/tests.md`; skills, scripts, agents, and source-vs-dist pages are conservatively reserved where relevant.
- Refactor inventory: no distinct extra refactor path is named by T003–T030 beyond the production paths listed here. `required_refactor_files=0` is a planned distinct-extra count, not an implementation claim. T015/T017 must confirm it after the refactor-aware helper exists; any newly necessary refactor file enters the owning increment's count and may force a new split.
- Historical 1,442/1,932 LOC numbers and C1a/C1b legacy 520/460 estimates are not measured per-PR results. Reviewable LOC and `pr_marker_plan` fingerprints remain unqualified. The advisory `atomicity-route=one-navigable-PR` remains unchanged; it does not waive these incremental gates.

## Per-PR planned ceiling

| Increment | Scope / tasks | Production paths | Authored / index / test paths | Dist + trust paths | Reference candidates | Total candidate paths | Status |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| A1 | US1 final release note; T003–T004, A1 checkpoint | 3 | 8 | 14 | 2 | **24** | Planned ceiling ≤24; actual LOC/diff unmeasured |
| A2 | US2 packet-only untracked guard; T005, A2 checkpoint | 1 | 5 | 11 | 0 | **16** | Planned ceiling ≤24; actual LOC/diff unmeasured |
| A3 | US3 current verdict plus PRD/roadmap alignment; T006–T008, A3 checkpoint | 2 | 8 | 12 | 1 | **21** | Planned ceiling ≤24; actual LOC/diff unmeasured |
| B1 | US4 visible markers and US5 tracked spec index; T009–T010, B1 checkpoint | 2 | 10 | 10 | 2 | **22** | Planned ceiling ≤24; actual LOC/diff unmeasured |
| B2 | US6 exact named reviewability entry and complete slice budgets; T011–T014, B2 checkpoint | 2 | 7 | 14 | 1 | **22** | Planned ceiling ≤24; actual LOC/diff unmeasured |
| B3 | US7 required-refactor estimate and US8 declared quality commands; T015–T017, B3 checkpoint | 2 | 6 | 10 | 1 | **17** | Planned ceiling ≤24; actual LOC/diff unmeasured |
| C1a1 | US9 canonical 13 Post rows and legacy resume; T018, C1a1 checkpoint | 1 | 8 | 9 | 3 | **20** | Planned ceiling ≤24; actual LOC/diff unmeasured |
| C1a2 | US10 persisted Post completion boundary; T019, C1a2 checkpoint | 1 | 6 | 7 | 2 | **15** | Planned ceiling ≤24; actual LOC/diff unmeasured |
| C1b | US10 executor team teardown; T020–T021, C1b checkpoint | 4 | 11 | 10 | 2 | **23** | Planned ceiling ≤24; actual LOC/diff unmeasured |
| C2a | US11 review pagination/publication, US12 blind spot, US13 status envelopes; T022–T025, C2a checkpoint | 0 | 10 | 6 | 2 | **18** | Planned ceiling ≤24; actual LOC/diff unmeasured |
| C2b | US13 scaffold/phase envelopes and US14 workflow links; T026–T030, C2b checkpoint | 0 | 11 | 9 | 3 | **23** | Planned ceiling ≤24; actual LOC/diff unmeasured |

## Exact path operations

Every repeated shared path is listed in each increment that may change it. `regenerate` means committed generated output from the source and does not permit hand edits.

### A1 — US1 final release note

Tasks: T003–T004, A1 checkpoint. Requirements: FR-001–003, FR-026. Planned changed paths: **24**.

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/pr_emission.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/pr_emission.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/pr_emission.py` | source payload |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/read_only.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| production | modify | `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/SKILL.md` | Claude payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md` | Codex overlay |
| test/manifest | add | `tests/speckit-pro/unit/test-pr-packet-repair.py` | task |
| test/manifest | add | `tests/speckit-pro/unit/fixtures/pr-packet-repair/final-note.json` | task |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` | task |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | new unit module |
| generated reference | regenerate | `docs-site/src/content/docs/reference/skills.md` | skill frontmatter might change |

### A2 — US2 packet-only untracked guard

Tasks: T005, A2 checkpoint. Requirements: FR-004–005, FR-026. Planned changed paths: **16**.

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/mutation.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/mutation.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/mutation.py` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/post-implementation.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/post-implementation.md` | source payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/post-implementation-codex.md` | Codex overlay |
| test/manifest | modify | `tests/speckit-pro/unit/test-pr-packet-repair.py` | task |
| test/manifest | add | `tests/speckit-pro/unit/fixtures/pr-packet-repair/packet-only-untracked.json` | task |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |

### A3 — US3 current verdict plus PRD/roadmap alignment

Tasks: T006–T008, A3 checkpoint. Requirements: FR-006, FR-026–027. Planned changed paths: **21**.

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/pr_emission.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/pr_emission.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/pr_emission.py` | source payload |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/read_only.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/SKILL.md` | Claude payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md` | Codex overlay |
| test/manifest | modify | `tests/speckit-pro/unit/test-pr-packet-repair.py` | task |
| test/manifest | add | `tests/speckit-pro/unit/fixtures/pr-packet-repair/current-verdict.json` | task |
| host/support | modify | `docs/prd-harness-engineering-uplift.md` | task |
| host/support | modify | `docs/ai/specs/harness-engineering-uplift-technical-roadmap.md` | task |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated reference | regenerate | `docs-site/src/content/docs/reference/skills.md` | skill frontmatter might change |

### B1 — US4 visible markers and US5 tracked spec index

Tasks: T009–T010, B1 checkpoint. Requirements: FR-007–010, FR-026. Planned changed paths: **22**.

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/read_only.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | source payload |
| production | modify | `scripts/refresh-release-artifacts.py` | task |
| generated index | regenerate | `specs/formal-001-selective-formal-methods/SPEC-MOC.md` | task |
| host/support | modify | `AGENTS.md` | task |
| test/manifest | add | `tests/speckit-pro/unit/test-marker-visibility.py` | task |
| test/manifest | add | `tests/speckit-pro/unit/fixtures/marker-visibility/cases.json` | task |
| test/manifest | add | `tests/speckit-pro/unit/test-spec-index-freshness.py` | task |
| test/manifest | add | `tests/speckit-pro/unit/fixtures/spec-index-freshness/historical-stale-index.md` | task |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` | task |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | new unit modules |
| generated reference | regenerate | `docs-site/src/content/docs/reference/scripts.md` | release script inventory might change |

### B2 — US6 exact named reviewability entry and complete slice budgets

Tasks: T011–T014, B2 checkpoint. Requirements: FR-011–014, FR-028–029, FR-026. Planned changed paths: **22**.

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/read_only.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/registry.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/registry.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/registry.py` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md` | source payload |
| test/manifest | add | `tests/speckit-pro/unit/test-reviewability-scope.py` | task |
| test/manifest | add | `tests/speckit-pro/unit/fixtures/reviewability-scope/cases.json` | task |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` | task |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | new unit module |

### B3 — US7 required-refactor estimate and US8 declared quality commands

Tasks: T015–T017, B3 checkpoint. Requirements: FR-015–016, FR-026. Planned changed paths: **17**.

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/speckit_pro_runner/helpers/read_only.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/helpers/read_only.py` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/gate-validation.md` | source payload |
| production | modify | `.specify/quality-gates.json` | task |
| test/manifest | add | `tests/speckit-pro/unit/test-size-estimate-refactors.py` | task |
| test/manifest | add | `tests/speckit-pro/unit/test-declared-quality-commands.py` | task |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` | task |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/claude/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` | runner source edited |
| generated trust | regenerate | `dist/codex/speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256` | runner source edited |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | new unit modules |

### C1a1 — US9 canonical 13 Post rows and legacy resume

Tasks: T018, C1a1 checkpoint. Requirements: FR-017–018, FR-026. Planned changed paths: **20**.

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/SKILL.md` | Claude payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md` | Codex overlay |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md` | source payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-autopilot/references/task-list-canonical-codex.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/task-list-canonical-codex.md` | Codex overlay |
| host/support | modify | `speckit-pro/skills/speckit-coach/templates/workflow-template.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-coach/templates/workflow-template.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-coach/templates/workflow-template.md` | source payload |
| test/manifest | add | `tests/speckit-pro/unit/test-post-completion.py` | task |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` | task |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | new test or changed skill/script inventory candidate |
| generated reference | regenerate | `docs-site/src/content/docs/reference/skills.md` | new test or changed skill/script inventory candidate |
| generated reference | regenerate | `docs-site/src/content/docs/reference/scripts.md` | new test or changed skill/script inventory candidate |

### C1a2 — US10 persisted Post completion boundary

Tasks: T019, C1a2 checkpoint. Requirements: FR-018, FR-026. Planned changed paths: **15**.

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| production | modify | `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` | source payload |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/SKILL.md` | Claude payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md` | Codex overlay |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/post-implementation.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/post-implementation.md` | source payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/post-implementation-codex.md` | Codex overlay |
| test/manifest | modify | `tests/speckit-pro/unit/test-post-completion.py` | task |
| generated reference | regenerate | `docs-site/src/content/docs/reference/skills.md` | changed skill/script inventory candidate |
| generated reference | regenerate | `docs-site/src/content/docs/reference/scripts.md` | changed skill/script inventory candidate |

### C1b — US10 executor team teardown

Tasks: T020–T021, C1b checkpoint. Requirements: FR-019, FR-026. Planned changed paths: **23**.

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| host/support | modify | `speckit-pro/agents/phase-executor.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/agents/phase-executor.md` | Claude agent |
| production | modify | `speckit-pro/codex-agents/phase-executor.toml` | task |
| generated | regenerate | `dist/codex/speckit-pro/codex-agents/phase-executor.toml` | Codex agent |
| host/support | modify | `speckit-pro/agents/analyze-executor.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/agents/analyze-executor.md` | Claude agent |
| production | modify | `speckit-pro/codex-agents/analyze-executor.toml` | task |
| generated | regenerate | `dist/codex/speckit-pro/codex-agents/analyze-executor.toml` | Codex agent |
| host/support | modify | `speckit-pro/agents/checklist-executor.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/agents/checklist-executor.md` | Claude agent |
| production | modify | `speckit-pro/codex-agents/checklist-executor.toml` | task |
| generated | regenerate | `dist/codex/speckit-pro/codex-agents/checklist-executor.toml` | Codex agent |
| host/support | modify | `speckit-pro/agents/implement-executor.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/agents/implement-executor.md` | Claude agent |
| production | modify | `speckit-pro/codex-agents/implement-executor.toml` | task |
| generated | regenerate | `dist/codex/speckit-pro/codex-agents/implement-executor.toml` | Codex agent |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` | source payload |
| test/manifest | add | `tests/speckit-pro/layer1-structural/test-team-teardown.py` | task |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` | task |
| generated reference | regenerate | `docs-site/src/content/docs/reference/agents.md` | agent frontmatter might change |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | new structural test |

### C2a — US11 review pagination/publication, US12 blind spot, US13 status envelopes

Tasks: T022–T025, C2a checkpoint. Requirements: FR-020–024, FR-026. Planned changed paths: **18**.

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| host/support | modify | `speckit-pro/skills/speckit-resolve-pr/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-resolve-pr/SKILL.md` | Claude payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-resolve-pr/SKILL.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-resolve-pr/SKILL.md` | Codex overlay |
| host/support | modify | `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | Claude payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | Codex overlay |
| host/support | modify | `speckit-pro/skills/speckit-status/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-status/SKILL.md` | Claude payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-status/SKILL.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-status/SKILL.md` | Codex overlay |
| test/manifest | add | `tests/speckit-pro/unit/test-resolve-pr-protocol.py` | task |
| test/manifest | add | `tests/speckit-pro/unit/test-scaffold-blindspot.py` | task |
| test/manifest | add | `tests/speckit-pro/unit/test-status-envelope-contract.py` | task |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` | task |
| generated reference | regenerate | `docs-site/src/content/docs/reference/skills.md` | skill frontmatter might change |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | new unit modules |

### C2b — US13 scaffold/phase envelopes and US14 workflow links

Tasks: T026–T030, C2b checkpoint. Requirements: FR-024–027. Planned changed paths: **23**.

| Class | Operation | Path | Basis |
| --- | --- | --- | --- |
| host/support | modify | `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | Claude payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-scaffold-spec/SKILL.md` | Codex overlay |
| host/support | modify | `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/phase-execution.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/phase-execution.md` | source payload |
| host/support | modify | `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md` | task |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/phase-execution-codex.md` | Codex overlay |
| host/support | modify | `speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-coach/templates/technical-roadmap-template.md` | source payload |
| host/support | modify | `speckit-pro/README.md` | task |
| generated | regenerate | `dist/claude/speckit-pro/README.md` | source payload |
| generated | regenerate | `dist/codex/speckit-pro/README.md` | source payload |
| test/manifest | add | `tests/speckit-pro/unit/test-scaffold-envelope-contract.py` | task |
| test/manifest | add | `tests/speckit-pro/unit/test-phase-envelope-contract.py` | task |
| test/manifest | add | `tests/speckit-pro/unit/test-roadmap-workflow-links.py` | task |
| test/manifest | add | `tests/speckit-pro/unit/fixtures/roadmap-workflow-links/cases.json` | task |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` | task |
| generated reference | regenerate | `docs-site/src/content/docs/reference/skills.md` | changed source or new test inventory candidate |
| generated reference | regenerate | `docs-site/src/content/docs/reference/tests.md` | changed source or new test inventory candidate |
| generated reference | regenerate | `docs-site/src/content/docs/reference/source-vs-dist.md` | changed source or new test inventory candidate |

## Qualification and stop conditions

The plan is a complete **named candidate path set**, not a measured final diff. `dist` and reference output must be regenerated at each increment and compared with the active marker's exact head/base. Generated pages may be unchanged, but no candidate was omitted from the conservative count. The full file/LOC budget, production classification, test RED/GREEN, host parity, title, release-note fence, runner trust check, and current marker fingerprints must pass before that increment emits a PR. T031 records full CI and cross-cutting acceptance after all increments. No implementation checkbox is complete yet.

The current runner's changed-file-manifest validator treats a path as globally owned by one marker, which conflicts with this required sequential reuse of `read_only.py`, `suite-manifest.json`, the runner manifest/digest, and host guidance. Do not manufacture unique ownership or suppress repeated paths to satisfy it. Resolve and test that product contract before persisting a multi-marker plan. If it remains unresolved, G6 and PR emission remain blocked with the repeated paths above as evidence.
