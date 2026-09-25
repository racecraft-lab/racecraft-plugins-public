# HRNS-015 slice inventory — Analyze planning baseline

This is the explicit planned changed-path set for the user-ratified C1a/C1b split. Paths are repository-relative and **reserved** even if a generated reference page ultimately has no diff. It is a planning inventory, not an assertion of measured LOC, a passing final diff, a current `pr_marker_plan`, or emitted PRs. A, B, and C2 already exceed the 24-path cap on required-path lower bounds, and T001/T002 must obtain a complete compliant allocation before implementation. This file is committed as planning baseline before marker work; C1a/C1b implementation checkpoints record actual diff and test evidence in their PR packets rather than editing this file.

## Decision and limits

- Review order: A → B → C1a → C1b → C2. The former C1 planned set had a 29-path lower bound and is retired by the user-ratified five-PR decision.
- The independent `atomicity-route` advisory result remains `one-navigable-PR` (`change-shape:modify-heavy`, `releasable: true`). The layer planner remains skipped. The supported five-PR route is a fresh top-level `pr_marker_plan` in workflow/state derived from Tasks, scope, reviewability, and hazard evidence; `multi-pr-emission` consumes it only after current fingerprints, membership/order, checkpoints, and safety gates validate. This document assigns review-slice labels, not schema marker IDs.
- Per-PR limits: at most four production files and fewer than 25 total changed paths, counting authored, tests, manifest, dist, and changed generated reference pages. `Production` follows plan.md: changed Python code, schema, or active config; host instruction Markdown counts toward total paths. C1b classifies its four Codex TOML agent configurations as production, and Claude Markdown agent instructions as host-facing total paths.
- No separate fixture files are planned for C1a/C1b: the new unit and structural test modules contain the failing-first cases. `formal/lifecycle.py`, gate-validation, and phase-execution references are read-only review targets. Any edit to them or any other path requires a revised allocation before the slice proceeds.
- Both slices are **unqualified for actual LOC and final diff**. Installed `estimate-spec-size` with `new_vs_modify=modify` returned C1a 520 LOC (`warn`, 2 suggested slices) for 2 story signals, 2 FR signals, 24 files; C1b 460 LOC (`warn`, 2 suggested slices) for 1/1/22. The helper does not incorporate required-refactor files. Its advisory results are not actual reviewable LOC or a refactor-inclusive pass. The implementation checkpoint measures actual reviewable LOC and every changed path against the 800-LOC/4-production/24-total block limits; a warning or suggested split is disclosed.

## C1a — Post list and completion boundary

Scope: US9 plus US10 Post-completion scenarios; FR-017/018 and FR-026. Primary surface: existing phase-coverage guard. Planned production files: **1** (`validate-autopilot-phase-coverage.py`). Planned total paths: **24** = 10 authored + 12 dist + 2 reserved reference. Target checkpoint: after T019, before T020. No unlisted path may enter this marker without a new inventory and cap result.

| Class | Operation | Path |
| --- | --- | --- |
| production | modify | `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` |
| host instruction | modify | `speckit-pro/skills/speckit-autopilot/SKILL.md` |
| host instruction | modify | `speckit-pro/codex-skills/speckit-autopilot/SKILL.md` |
| host instruction | modify | `speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md` |
| host instruction | modify | `speckit-pro/codex-skills/speckit-autopilot/references/task-list-canonical-codex.md` |
| host instruction | modify | `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` |
| host instruction | modify | `speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md` |
| host instruction | modify | `speckit-pro/skills/speckit-coach/templates/workflow-template.md` |
| test/manifest | add | `tests/speckit-pro/unit/test-post-completion.py` |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py` |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/SKILL.md` |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/SKILL.md` |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md` |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md` |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/task-list-canonical-codex.md` |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/post-implementation.md` |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/post-implementation.md` |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/post-implementation-codex.md` |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-coach/templates/workflow-template.md` |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-coach/templates/workflow-template.md` |
| generated | regenerate | `docs-site/src/content/docs/reference/skills.md` |
| generated | regenerate | `docs-site/src/content/docs/reference/scripts.md` |

## C1b — executor team teardown

Scope: US10 team-teardown scenario; FR-019 and FR-026. Primary surface: eight executor definitions. Planned production files: **4** (Codex TOML active configurations). Planned total paths: **22** = 11 authored + 10 dist + 1 reserved reference. Target checkpoint: T021 after T020 and after the C1a checkpoint. No unlisted path may enter this marker without a new inventory and cap result.

| Class | Operation | Path |
| --- | --- | --- |
| host instruction | modify | `speckit-pro/agents/phase-executor.md` |
| host instruction | modify | `speckit-pro/agents/analyze-executor.md` |
| host instruction | modify | `speckit-pro/agents/checklist-executor.md` |
| host instruction | modify | `speckit-pro/agents/implement-executor.md` |
| production | modify | `speckit-pro/codex-agents/phase-executor.toml` |
| production | modify | `speckit-pro/codex-agents/analyze-executor.toml` |
| production | modify | `speckit-pro/codex-agents/checklist-executor.toml` |
| production | modify | `speckit-pro/codex-agents/implement-executor.toml` |
| host instruction | modify | `speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` |
| test/manifest | add | `tests/speckit-pro/layer1-structural/test-team-teardown.py` |
| test/manifest | modify | `tests/speckit-pro/suite-manifest.json` |
| generated | regenerate | `dist/claude/speckit-pro/agents/phase-executor.md` |
| generated | regenerate | `dist/claude/speckit-pro/agents/analyze-executor.md` |
| generated | regenerate | `dist/claude/speckit-pro/agents/checklist-executor.md` |
| generated | regenerate | `dist/claude/speckit-pro/agents/implement-executor.md` |
| generated | regenerate | `dist/codex/speckit-pro/codex-agents/phase-executor.toml` |
| generated | regenerate | `dist/codex/speckit-pro/codex-agents/analyze-executor.toml` |
| generated | regenerate | `dist/codex/speckit-pro/codex-agents/checklist-executor.toml` |
| generated | regenerate | `dist/codex/speckit-pro/codex-agents/implement-executor.toml` |
| generated | regenerate | `dist/claude/speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` |
| generated | regenerate | `dist/codex/speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` |
| generated | regenerate | `docs-site/src/content/docs/reference/agents.md` |

## Checkpoint proof still required

For each marker, the implementation run must preserve RED-before-fix and GREEN evidence, register and run its test layer, run the quick suite, refresh generated payloads and reference pages, check the exact diff against this set, and record actual LOC, production count, total changed paths, host parity, and PR title/release-note gates. If generated output introduces an unlisted path or the actual count reaches a block line, stop before PR side effects. A, B, and C2 have blocking lower bounds and need complete T001/T002 path inventories, a further owner-ratified compliant allocation, and actual gates.

## A/B/C2 required-path lower-bound audit (blocking)

This audit counts distinct paths named by T003–T017 and T022–T030, their known `dist` fan-out, and the runner trust files generated when runner modules change. It is a **lower bound**, not a complete planned inventory or an implementation pass. No A/B/C2 behavior task starts while these allocations remain above 24 paths.

| Slice | Authored paths already required | Known `dist` paths | Runner trust outputs | Lower bound | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| A | 12 | 13 | 6 | **31** | Blocked (at least seven above 24) |
| B | 14 | 8 | 6 | **28** | Blocked (at least four above 24) |
| C2 | 17 | 13 | 0 | **30** | Blocked (at least six above 24) |

- **A authored (12):** `pr_emission.py`, `read_only.py`, `mutation.py`, packet schema, Claude and Codex autopilot SKILL files, Claude and Codex post-implementation references, PRD, technical roadmap, `test-pr-packet-repair.py`, and suite manifest. The three runner modules each generate Claude/Codex `dist` copies (6); packet schema generates two; paired host skills generate two; post-implementation base generates two and its Codex overlay one, totaling 13 known `dist` paths.
- **B authored (14):** quality-gates config; `refresh-release-artifacts.py`; gate-validation reference; technical-roadmap template; runner `read_only.py` and `registry.py`; formal-001 SPEC-MOC; root `AGENTS.md` from T010; suite manifest; and five test modules (`test-declared-quality-commands.py`, `test-marker-visibility.py`, `test-reviewability-scope.py`, `test-size-estimate-refactors.py`, `test-spec-index-freshness.py`). Gate-validation and template each generate two `dist` copies; the two runner modules each generate two, totaling eight.
- **C2 authored (17):** README; Claude/Codex phase-execution references; Claude/Codex resolve-pr, scaffold-spec, and status SKILL files; technical-roadmap template; suite manifest; and six test modules (`test-phase-envelope-contract.py`, `test-resolve-pr-protocol.py`, `test-roadmap-workflow-links.py`, `test-scaffold-blindspot.py`, `test-scaffold-envelope-contract.py`, `test-status-envelope-contract.py`). README generates two `dist` copies; phase-execution base generates two and the Codex overlay one; each paired resolve-pr/scaffold-spec/status SKILL generates two; template generates two, totaling 13.
- **Runner trust fan-out for A and B (six paths each):** `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`, `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.sha256`, and each of those two files under `dist/claude/speckit-pro/speckit_pro_runner/` and `dist/codex/speckit-pro/speckit_pro_runner/`. The refresh script regenerates these when runner modules change.
- **Missing exact evidence for all three:** child files inside the planned fixture directories (`pr-packet-repair`, `marker-visibility`, `reviewability-scope`, `spec-index-freshness`, `roadmap-workflow-links`); which generated reference pages change; any distinct required-refactor paths beyond the named files; final operation/production classification for each path; actual reviewable LOC; and actual authored/generated diff. These cannot reduce the lower bounds. T001/T002 must enumerate them and obtain an owner-ratified, compliant allocation before any behavior task or PR marker is emitted.
