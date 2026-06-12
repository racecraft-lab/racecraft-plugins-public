# Implementation Plan: Non-Stopping Reviewability Markers

**Branch**: `prsg-013-reviewability-markers` | **Date**: 2026-06-12 | **Spec**: `specs/prsg-013-reviewability-markers/spec.md`

**Input**: Feature specification from `specs/prsg-013-reviewability-markers/spec.md`

## Summary

Autopilot will treat parseable reviewability sizing results as PR-shaping input, persist a top-level `pr_marker_plan`, implement and checkpoint in marker order, and let final PR emission consume those markers instead of stopping on full-diff size alone. Correctness and safety gates remain blocking, while valid size-only `warn` or `block` results become structured evidence for scoped PR packets.

## Technical Context

**Language/Version**: Bash 4+ shell scripts, Markdown skill guidance, JSON Schema 2020-12

**Primary Dependencies**: `bash`, `jq`, `git`, `gh` at PR-emission boundaries, existing SpecKit Pro shell harness

**Storage**: Repository files only: `autopilot-state.json`, workflow evidence blocks, JSON contract schemas, and generated PR packet artifacts

**Testing**: Layer 4 shell fixtures, paired Claude/Codex Layer 3 functional evals, Codex parity validation, structural validation, and default `bash tests/speckit-pro/run-all.sh`

**Target Platform**: SpecKit Pro plugin marketplace surfaces for Claude and Codex

**Project Type**: Shell and Markdown plugin automation with JSON state contracts

**Performance Goals**: Deterministic marker planning and PR-emission decisions in shell fixtures; no network dependency before `gh`-based PR emission

**Constraints**: Reviewability sizing must not stop implementation for a valid spec; correctness and safety gates still stop; `reviewability-gate.sh tasks` remains caller-compatible unless a compatibility-safe extension is proven; marker state is persisted in `autopilot-state.json` and workflow evidence, not as authoritative `tasks.md` mutations; implementation checkpoints preserve marker order

**Scale/Scope**: Three user stories, eighteen functional requirements, one top-level marker-plan state object, one final-backstop marker-aware outcome, and paired Claude/Codex Layer 3 eval coverage for the end-to-end behavior

**Reviewability Budget**: Primary surface `harness/adapter`; secondary surfaces `docs/process` and `scheduler/runtime`; projected full-feature reviewable LOC 700-1,200; projected production files 9-11; projected total files 17-19; budget result is warning accepted with required marker-based split evidence. The implementation must produce scoped PR markers whose individual review scopes are expected to stay below single-PR review limits, or carry structured warnings when no safe subdivision exists.

## Declared File Operations

- MODIFIED speckit-pro/skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/phase-execution.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/gate-validation.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/post-implementation.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md
- NEW speckit-pro/skills/speckit-autopilot/contracts/pr-marker-plan.schema.json
- MODIFIED speckit-pro/skills/speckit-autopilot/contracts/final-reviewability-gate-state.schema.json
- MODIFIED speckit-pro/skills/speckit-autopilot/contracts/multi-pr-emission-state.schema.json
- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh
- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/final-reviewability-backstop.sh
- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md
- MODIFIED tests/speckit-pro/layer4-scripts/test-plan-layers.sh
- MODIFIED tests/speckit-pro/layer4-scripts/test-final-reviewability-backstop.sh
- MODIFIED tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
- MODIFIED tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json
- MODIFIED tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Evidence |
|------|--------|----------|
| Plugin Structure Compliance | PASS | Changes stay inside the existing `speckit-pro/` plugin layout and its test suite. |
| Script Safety | PASS | Script changes must preserve `#!/usr/bin/env bash`, `set -euo pipefail`, quoted variables, checked results, executability, and `bash -n` validity. |
| Semantic Versioning | PASS | No manual plugin version edit is planned; release-please remains authoritative. |
| Test Coverage Before Merge | PASS | Layer 4 fixtures cover marker planning, final backstop, and multi-PR emission; paired Claude/Codex Layer 3 evals cover the non-stopping autopilot guidance contract and mirror parity. |
| Conventional Commits | PASS | No commit is created by this phase; implementation PR title must use a valid conventional commit. |
| KISS, Simplicity & YAGNI | PASS | The design adds one persisted marker-plan contract and extends existing shell/guidance surfaces instead of introducing a new orchestration layer. |
| Reviewability Budget | WARNING ACCEPTED | The full feature exceeds single-PR review budget, but the split decision is to keep PRSG-013 as one spec and require marker-based implementation checkpoints and PR emission. |

**Primary review surface**: `harness/adapter`

**Secondary review surfaces**: `docs/process`, `scheduler/runtime`

**Split decision**: Keep PRSG-013 as one prerequisite spec because the behavior is one product outcome. Implementation and emission must use markers for Foundation, each user story, and safe in-story subdivisions. If a story has no safe subdivision, the original story marker continues with a structured warning. If hazard collapse is required, implementation still checkpoints original markers and emits one full-spec PR with marker evidence.

**PR review packet source**: Marker-aware PR packets must include what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, rollback or feature-flag notes, and structured marker warnings.

## Project Structure

### Documentation (this feature)

```text
specs/prsg-013-reviewability-markers/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── pr-marker-plan.schema.json
│   └── marker-split-result.schema.json
├── checklists/
│   ├── requirements.md
│   ├── state-management.md
│   ├── error-handling.md
│   ├── api-contracts.md
│   └── llm-integration.md
├── SPEC-MOC.md
└── spec.md
```

### Source Code (repository root)

```text
speckit-pro/
├── skills/speckit-autopilot/
│   ├── SKILL.md
│   ├── contracts/
│   │   ├── pr-marker-plan.schema.json
│   │   ├── final-reviewability-gate-state.schema.json
│   │   └── multi-pr-emission-state.schema.json
│   ├── references/
│   │   ├── gate-validation.md
│   │   ├── phase-execution.md
│   │   ├── post-implementation.md
│   │   └── workflow-file-protocol.md
│   └── scripts/
│       ├── plan-layers.sh
│       ├── final-reviewability-backstop.sh
│       └── multi-pr-emission.sh
└── codex-skills/speckit-autopilot/
    ├── SKILL.md
    └── references/
        ├── phase-execution-codex.md
        └── post-implementation-codex.md

tests/speckit-pro/
├── layer4-scripts/
│   ├── test-plan-layers.sh
│   ├── test-final-reviewability-backstop.sh
│   └── test-multi-pr-emission.sh
└── layer3-functional/
    ├── evals/speckit-autopilot-evals.json
    └── codex-evals/speckit-autopilot-evals.json
```

**Structure Decision**: Extend the existing autopilot shell/guidance surfaces and their Codex mirrors. Marker planning belongs with layer planning because it is derived from generated task structure; final backstop and multi-PR emission consume the persisted marker plan instead of inferring boundaries from one mixed diff.

## State And Evidence Contract

- `source_fingerprint` MUST include hashes for the feature spec, the plan-declared file/test scope, generated tasks, captured reviewability evidence, and the recorded hazard route. Resume and final emission must treat any mismatch as stale state rather than reusing marker checkpoints.
- Workflow evidence MUST mirror the persisted `pr_marker_plan` values that affect review and resume: `schema_version`, `feature_id`, `status`, `source_fingerprint`, `markers[].id`, `markers[].review_order`, marker warnings, checkpoint evidence, and emission mapping. Free-text workflow summaries may explain those values but must not introduce independent marker IDs, order, warnings, or PR mappings.
- Resume preservation is marker-scoped. A marker can keep `implementation_checkpoint` and `emission_mapping` only when its ID, source boundary, task IDs, folded Polish task IDs, and source fingerprint still match. Otherwise those fields reset to pending before implementation or emission continues.
- Safe subdivision replaces the parent user-story marker for scoped emission. `us<N>-part<M>` child markers carry `parent_marker_id=us<N>` and occupy the parent's review-order position in task order; the parent `us<N>` marker is not emitted as a separate scoped PR.
- Polish folding is deterministic: fold into the nearest preceding non-Polish marker that owns the dependency and declared file/test scope; otherwise fold into the next eligible non-Polish marker. Record `folded_polish_target_reason` on the marker so workflow evidence and PR packets can explain the decision.

## LLM Guidance Contract

Autopilot guidance changes MUST make the non-stopping reviewability behavior explicit to future agents. The touched Claude guidance surfaces are `speckit-pro/skills/speckit-autopilot/SKILL.md`, `references/phase-execution.md`, `references/gate-validation.md`, `references/post-implementation.md`, and `references/workflow-file-protocol.md`. The touched Codex mirrors are `speckit-pro/codex-skills/speckit-autopilot/SKILL.md`, `references/phase-execution-codex.md`, and `references/post-implementation-codex.md`. There is no separate Codex `gate-validation.md`; its behavior must be reflected in the Codex SKILL and phase-execution guidance rather than introducing a duplicate reference.

Agent-facing guidance MUST use one proceed/stop matrix:

- Post-G5 task reviewability `pass`, `warn`, honored `exception`, and valid current size-only `status=block` evidence continue to marker planning. A valid size-only block may carry warnings, but it is not a request to stop, manually re-slice, rewrite task boundaries, or wait for operator re-scope.
- Final full-diff size block plus a current, valid, fingerprint-matched `pr_marker_plan` proceeds with `status=proceed`, `outcome=marker_split`, and marker-aware PR emission.
- Hazard collapse preserves original marker checkpoint evidence, emits a single `full-spec` packet, and records warning evidence; it is not a manual stop.
- Correctness and safety conditions from FR-014 remain stops. Missing, stale, malformed, or fingerprint-mismatched marker plans at final emission stop before PR body generation or PR side effects.

Future-agent evidence prompts MUST ask agents to record the proof that a size-only block became marker input: captured reviewability exit code, status, mode, reason, and evidence path; why the block is size-only; marker-plan schema version and evidence path; source-fingerprint validation result; ordered marker IDs and review order; per-marker implementation checkpoint evidence; structured warning objects; final-backstop `marker_split` evidence path and outcome; marker packet validation status; packet paths; and emitted PR number/URL mappings when present.

Claude/Codex parity is semantic equivalence, not byte identity. Each runtime may use its own voice and mechanics, but paired guidance and paired eval cases MUST preserve the same proceed/stop matrix, the same evidence prompts, and the same ban on manual re-slicing stops for size alone. The paired Layer 3 evals must include a valid size-only block case for both runtimes and assert that each continues with marker evidence. Codex parity validation remains required for structural mirror health.

## Marker-Aware Script API Contracts

PRSG-013 adds marker-aware paths without changing legacy consumers by default:

- `plan-layers.sh <feature-dir>` remains the PRSG-008-compatible read-only call: it reads `<feature-dir>/tasks.md`, writes stable JSON to stdout, writes diagnostics to stderr, writes no files, and keeps exit codes `0` for `status=ok`, `1` for `status=invalid_plan`, and `2` for `status=input_error`.
- Marker planning is opt-in and explicit. The marker-aware call MUST accept the feature directory plus the captured task reviewability result, recorded hazard route, current autopilot state path, and a marker-plan output path. It MUST emit a stable machine-readable marker-planning result, create a candidate `pr_marker_plan` JSON file only at the requested output path, and leave `autopilot-state.json` and workflow prose updates to the autopilot caller after schema validation succeeds.
- Marker-aware `plan-layers.sh` status values are `ok`, `invalid_plan`, and `input_error`; the emitted `pr_marker_plan.status` values remain `planned`, `checkpointing`, `emission_ready`, `emitted`, `collapsed`, `stale`, and `invalid`. A valid size-only reviewability `block` may produce `status=ok` with structured marker warnings; malformed task structure, unusable reviewability evidence, stale fingerprints, invalid marker JSON, or unsafe hazard evidence produce nonzero correctness-stop output.
- Runtime evidence paths stored in marker plans, checkpoint evidence, final-backstop results, and emission packets MUST be repo-relative. Runtime evidence is rooted under `specs/prsg-013-reviewability-markers/.process/`, with marker-plan artifacts under `.process/marker-plan/`, reviewability captures under `.process/reviewability/`, and per-marker emission packets or verification logs under `.process/emission/<marker-id>/`. Contract and fixture references may point at `specs/prsg-013-reviewability-markers/contracts/`, `speckit-pro/skills/speckit-autopilot/contracts/`, or `tests/speckit-pro/layer4-scripts/fixtures/`, but persisted runtime evidence MUST NOT use absolute paths.
- PR mappings are not file paths. `emission_mapping.pr_number` is either absent/null before creation or a positive integer after creation; `emission_mapping.pr_url` is either absent/null before creation or the HTTPS URL returned by the PR operation. Hazard-collapsed mappings MUST preserve `source_marker_ids` for every original marker they include.

### Final Backstop Marker Split API

- `final-reviewability-backstop.sh` keeps its existing PRSG-010 behavior when no marker-plan input is supplied.
- The marker-aware path MUST accept or resolve the current `pr_marker_plan` from `autopilot-state.json`, validate it against `pr-marker-plan.schema.json`, verify the current source fingerprint, and write a `marker-split-result.schema.json` evidence file under `specs/prsg-013-reviewability-markers/.process/marker-plan/final-marker-split-result.json`.
- When the final full-diff result is size-blocked and the marker plan is valid and fingerprint-matched, the command MUST return `status=proceed`, `outcome=marker_split`, `mode=final`, include full-diff evidence, marker count/order, warning objects, and marker emission handoff data, and exit `0`.
- When the marker plan is missing, stale, malformed, fingerprint-mismatched, or not emission-ready, the command MUST return `status=stop`, `outcome=correctness_stop`, exit nonzero, and MUST NOT invoke PR body generation, `gh pr create`, or marker-based multi-PR emission.

### Multi-PR Marker Emission API

- `multi-pr-emission.sh` keeps its existing PRSG-009 layer-plan mode for legacy slice consumers.
- The marker-aware mode MUST consume the validated `pr_marker_plan` plus the final `marker_split` result, not infer review boundaries from the legacy layer-plan `increments[]` when markers are available.
- Non-hazard emission MUST produce one marker packet per emitted marker in `review_order`. Each packet MUST include `marker_id`, `source_marker_ids`, `review_order`, declared files/tests, final-backstop `marker_split` evidence path, traceability, verification evidence, warning objects, rollback or feature-flag notes, and pending PR mapping.
- Hazard-collapsed emission MUST produce exactly one packet with `marker_id=full-spec`, `source_marker_ids` listing the original markers in order, route `hazard_collapsed`, preserved marker checkpoints, and structured warnings explaining the collapse.
- The command MUST validate marker packets before body generation or PR side effects. Invalid, stale, placeholder-filled, marker-mismatched, or scope-mismatched packets remain correctness stops.

### Contract Fixture Requirements

- Layer 4 fixtures MUST prove stable machine-readable stdout or persisted JSON for the marker-aware `plan-layers.sh`, `final-reviewability-backstop.sh`, and `multi-pr-emission.sh` paths. Fixture assertions MUST cover status/outcome values, exit codes, marker order, evidence paths, warning object shape, and no-side-effect correctness stops.
- Marker-plan fixtures MUST cover Foundation plus user-story markers, Polish folding, safe subdivision, no-safe-boundary warning, hazard collapse, stale fingerprint rejection, and malformed marker state rejection.
- Final-backstop fixtures MUST cover full-diff size block plus valid marker plan (`marker_split`, exit `0`) and full-diff size block plus missing/stale/malformed marker plan (`correctness_stop`, nonzero exit).
- Multi-PR emission fixtures MUST cover non-hazard per-marker packets, hazard-collapsed `full-spec` packet mapping, packet validation before PR body generation, scoped verification evidence paths, and blocked side-effect behavior.
- Task-gate compatibility fixtures MUST show `reviewability-gate.sh tasks` still returns the stable task-mode exit/status contract while the autopilot caller interprets valid size-only `status=block` stdout as marker input.
- Contract schemas in `specs/prsg-013-reviewability-markers/contracts/` and production schemas in `speckit-pro/skills/speckit-autopilot/contracts/` MUST parse with `jq empty`; Layer 4 tests MUST assert the emitted JSON fields named by those schemas rather than relying on prose-only checks.
- Paired Claude and Codex functional eval cases MUST cover a valid size-only reviewability block and assert that both runtimes continue implementation with marker evidence, include the required evidence fields, and do not instruct a manual re-slicing stop for size alone.

## Error Handling Semantics

- The post-G5 caller of `reviewability-gate.sh tasks` MUST guard the invocation under `set -euo pipefail`, capture stdout and exit code, and branch on parsed JSON rather than allowing exit 1 to abort implementation:

  ```bash
  code=0
  task_gate_json="$("<SKILL_SCRIPTS>/reviewability-gate.sh" tasks "$FEATURE_DIR")" || code=$?
  ```

- Post-G5 task reviewability handling is an allowlist, not a blanket continue:
  - `code == 0` with parseable task-mode `status` of `pass`, `warn`, or honored `exception` proceeds to marker planning.
  - `code == 1` with parseable task-mode `status=block`, current feature linkage, readable evidence, and only reviewability size blockers proceeds to marker planning with structured warning evidence. This preserves the lower-level task-gate exit-code contract.
  - `code == 2`, invalid JSON, missing or unexpected `status`/`mode`, stale or unreadable evidence, unreadable plan/task artifacts, non-size blockers, or any nonzero exit not covered by the valid size-only block case is a correctness stop.
  - Unknown task/final statuses, including a `not_estimated` value from a surface that is not explicitly contracted to be advisory in this feature, are not marker input and must stop unless a future compatibility-safe contract adds an explicit non-stopping rule.
- The final pre-PR backstop MUST return `marker_split` and exit successfully only when the full-diff result is size-blocked and the current `pr_marker_plan` is valid, current, and fingerprint-matched. Missing, stale, malformed, or fingerprint-mismatched marker plans produce `correctness_stop`, exit nonzero, and do not invoke marker-based PR emission.
- Marker-aware PR packets MUST be schema/contract validated before PR body generation, `gh pr create`, or any equivalent PR side effect. Invalid, stale, placeholder-filled, or marker-mismatched packets are correctness stops; structured marker warnings may be rendered into PR bodies only after packet validation succeeds.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Full-feature reviewability warning above single-PR budget | The behavior spans task gate handling, marker persistence, implementation ordering, final backstop, and PR emission, which must agree on one contract. | Splitting into separate specs would leave intermediate states where sizing is non-stopping but PR emission cannot consume durable markers, or PR emission expects markers that earlier phases do not produce. |
| Marker-plan state contract added | PR emission needs durable, fingerprinted evidence that survives resume and cannot rely on transient prose edits. | Rewriting `tasks.md` with marker comments would make generated task prose authoritative state and would be harder to validate for staleness. |
