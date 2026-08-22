# Implementation Plan: Arm The Accidentally-Advisory State Bookkeeping Checks

**Branch**: `art-017-state-bookkeeping-checks` | **Date**: 2026-08-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/art-017-state-bookkeeping-checks/spec.md`

## Summary

ART-017 makes three current-run autopilot state invariants blocking under the exact `--rule status-evidence` invocation the autopilot already runs. The implementation stays surgical: add `in_progress_errors`, `duplicate_state_steps`, and `state_order_errors` to the existing status-evidence rule, flip those three intent verdicts to `gated` in the same change, prove each key with isolated negative controls, preserve legacy coverage advisories as nonblocking, narrow the authored autopilot guidance, and regenerate derived payload/reference/proof surfaces through repository tooling.

## Technical Context

**Language/Version**: Python 3.11+ standard library for authored tooling and tests.

**Primary Dependencies**: Python standard library only for implementation (`argparse`, `json`, `pathlib`, `subprocess`, `tempfile`, `unittest`). Existing release/reference tooling is repository-owned and invoked as generated-artifact maintenance, not as a new runtime dependency.

**Storage**: Markdown workflow files and JSON `autopilot-state.json` files. ART-017 preserves the existing report shape and problem-key names.

**Testing**: Existing Python `unittest` coverage in `tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py`, dispatched directly and through `python3 tests/speckit-pro/run-all.py`.

**Target Platform**: SpecKit Pro maintainer worktrees and CI on supported local/CI Python 3.11+ environments.

**Project Type**: Public Claude Code and Codex plugin marketplace repository; this slice changes shared SpecKit Pro guard behavior and one authored skill paragraph.

**Performance Goals**: No new network, package-install, or long-running runtime path. Validation remains deterministic over the supplied workflow/state pair and emits the complete JSON report before deciding the scoped exit code.

**Constraints**: Quote and implement "Use status-evidence (Recommended)" by adding exactly the three named keys to the existing `status-evidence` tuple, with no helper-level grouping. Quote and implement "Keep them atomic (Recommended)" by moving rule membership and each intent verdict together. Keep `missing_state_prefixes` and `missing_state_post_items` visible but nonblocking under `status-evidence`. Discover corpus paths from the git index with an argument-array subprocess, `shell=False`, repository-root `cwd`, NUL-delimited output, and stable repo-relative sorting; enumeration, decoding, file-read, and JSON-parse failures fail the corpus test rather than skip it. Do not hand-edit generated Codex skills, `dist/**`, installed-cache proofs, or generated docs references.

**Scale/Scope**: One vertical slice. Authored production files are limited to the validator script and one authored autopilot skill paragraph; authored tests stay in the existing bookkeeping guard unit module. Setup estimated 125 LOC and one slice; the warning was accepted because only the roadmap-wide surface count crossed the reviewability warning threshold.

**Reviewability Budget**: The setup forward estimate remains 125 reviewable LOC across the one vertical slice. The G3 plan-phase `estimate-reviewable-loc` helper returned `status: pass`, `projected: 0`, and three modified entries because its production-file classifier recognized zero production files among the validator script, authored Markdown, and unit-test paths. Both results are advisory inputs rather than an implementation measurement. Split decision: no split, because rule membership, intent classification, isolated controls, tracked-pair corpus evidence, and the narrow authored explanation are one independently testable repair.

## Declared File Operations

- MODIFIED speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py
- MODIFIED speckit-pro/skills/speckit-autopilot/SKILL.md
- MODIFIED tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Plan Verdict | Evidence |
|-----------|--------------|----------|
| I. Plugin Structure Compliance | PASS | No new plugin directory or manifest surface. Authored plugin source changes are treated as release inputs, with generated payloads/proofs/references refreshed by tooling after implementation. |
| II. Cross-Platform Runtime & Script Safety | PASS | Authored implementation remains Python 3.11+ standard library. No Bash, `jq`, PowerShell, package-install, or shell text-processing implementation path is introduced. |
| III. Semantic Versioning | PASS | ART-017 does not manually edit plugin version fields. Release-please remains authoritative for version movement. |
| IV. Test Coverage Before Merge | PASS WITH REQUIRED IMPLEMENTATION EVIDENCE | The plan adds focused Layer 4 unit coverage for the three newly blocking keys, legacy advisory behavior, clean control behavior, report-shape preservation, and tracked authority-matched workflow/state pairs. Full suite proof is required before ready/merge. |
| V. Conventional Commits | PASS | The eventual PR title and commits must use the repository conventional format. Plan-stage work does not create a commit in this executor. |
| VI. KISS, Simplicity & YAGNI | PASS | The change is explicit per-key membership plus explicit per-key intent verdicts. No new rule, derived verdict system, fail-fast report mode, or broader advisory-key reclassification is planned. |

Post-design re-check: PASS. The design artifacts below preserve the same boundaries and do not introduce additional authored source files, dependencies, storage, or rule abstractions.

## Project Structure

### Documentation (this feature)

```text
specs/art-017-state-bookkeeping-checks/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- status-evidence-guard.md
`-- tasks.md              # Created later by /speckit-tasks
```

### Source Code (repository root)

```text
speckit-pro/
`-- skills/
    `-- speckit-autopilot/
        |-- SKILL.md
        `-- scripts/
            `-- validate-autopilot-phase-coverage.py

tests/
`-- speckit-pro/
    `-- unit/
        `-- test-autopilot-bookkeeping-guard.py

dist/                         # Generated by scripts/refresh-release-artifacts.py
docs-site/                    # Reference pages generated/checked by pnpm scripts
docs/ai/specs/.process/       # Generated installed-cache proof/evidence outputs
tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/
                              # Generated installed-cache fixture mirrors
```

**Structure Decision**: Use the existing single-repository plugin/tooling layout. ART-017 changes the authored validator, the authored skill guidance paragraph, and the existing unit-test module only. Generated mirrors, payloads, installed-cache fixtures, proof JSON, and docs reference pages are derived outputs and must be regenerated by repository tooling rather than hand-edited.

## Phase 0 Research Summary

Research is complete with no unresolved clarification markers.

- Decision: Use the existing `status-evidence` rule.
- Decision: Keep rule membership and intent verdict updates atomic.
- Decision: Use one shared clean builder with three isolated state mutations.
- Decision: Preserve the full JSON report shape and existing problem-key names.
- Decision: Cover tracked authority-matched adjacent workflow/state pairs only.
- Decision: Narrow the authored autopilot paragraph only, then regenerate derived surfaces.
- Decision: Develop independently from ART-008 and serialize only the final integration boundary: record the latest-main HEAD, rebase, regenerate release artifacts, run the independent release-artifact `--check`, generate/check docs references, run the targeted bookkeeping test, and run the full suite against that same HEAD before ready/merge.

Details are recorded in [research.md](./research.md).

## Phase 1 Design Summary

Data entities and validation rules are recorded in [data-model.md](./data-model.md). The relevant command/report contract is recorded in [contracts/status-evidence-guard.md](./contracts/status-evidence-guard.md). End-to-end validation steps are recorded in [quickstart.md](./quickstart.md).

## Implementation Approach

1. Add RED tests first in `tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py`.
2. Extend the existing fixture support into one shared clean workflow/state builder.
3. Add three isolated mutation tests for `in_progress_errors`, `duplicate_state_steps`, and `state_order_errors`; each must assert exit code `1`, the target list non-empty, and every other problem key selected by `status-evidence` empty under the exact scoped invocation.
4. Keep or add a clean control proving the same invocation exits `0`.
5. Add a legacy advisory control proving `missing_state_prefixes` and `missing_state_post_items` remain reported but nonblocking under `status-evidence`.
6. Add a tracked-pair corpus regression that obtains tracked paths from `["git", "ls-files", "-z"]` at the repository root with `shell=False`, decodes and sorts repo-relative paths deterministically, and classifies every tracked workflow candidate as eligible or excluded with a reason. Fail on discovery/read/JSON errors, require at least one eligible authority-matched adjacent state, invoke every eligible pair exactly once, and assert candidate, eligible, excluded, invoked, and passed counts reconcile.
7. Move the three ART-017 keys into the `status-evidence` rule tuple and flip their `PROBLEM_KEY_INTENT` verdicts to `gated` with reasons tied to current-run state integrity.
8. Narrow the authored autopilot paragraph in `speckit-pro/skills/speckit-autopilot/SKILL.md` so it distinguishes legacy structural coverage debt from the three blocking state invariants.
9. Regenerate derived release, payload, proof, installed-cache, Codex, and docs-reference surfaces through the existing repository commands.
10. At final integration, record the latest-main HEAD and run in order against that same rebased tree: `python3 scripts/refresh-release-artifacts.py`, `python3 scripts/refresh-release-artifacts.py --check`, `pnpm --dir docs-site reference:generate`, `pnpm --dir docs-site reference:check`, `python3 tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py`, and `python3 tests/speckit-pro/run-all.py`. Do not reuse pre-rebase or pre-regeneration green evidence.

## Requirement Traceability

| Requirement | Design/Implementation Surface | Verification |
|-------------|--------------------------------|--------------|
| FR-001 through FR-003 | `RULE_PROBLEM_KEYS["status-evidence"]` in the validator | Three isolated negative controls exit `1` under exact scoped invocation. |
| FR-004 | Validator rule tuple and legacy advisory tests | Control proves coverage debt remains reported but nonblocking under `status-evidence`. |
| FR-005 through FR-006 | `PROBLEM_KEY_INTENT` entries for the three ART-017 keys | Existing gated-verdict rule-map consistency test plus updated reasons. |
| FR-007 through FR-008 | CLI/report contract preserved in validator | Report-shape and key-name assertions; scoped exit-code tests. |
| FR-009 through FR-011 | Shared clean builder and isolated mutations in unit tests | Each negative control exits `1` with its target list non-empty and every other status-evidence-selected key empty; the clean control exits `0`. |
| FR-012 through FR-015 | Git-index tracked authority-matched pair census and corpus regression | Deterministic candidate/eligible/excluded/invoked/passed counts reconcile; at least one eligible pair exists; discovery/read/parse failures fail closed; missing/mismatched/synthetic states are excluded with reasons. |
| FR-016 | Authored autopilot `SKILL.md` paragraph | Prose review plus regenerated downstream mirrors. |
| FR-017 through FR-018 | Ordered final integration and generated artifact commands | Record latest-main HEAD; run `python3 scripts/refresh-release-artifacts.py` and `--check`; generate/check docs references; run targeted bookkeeping coverage and the full suite against the same tree. |
| FR-019 | PR packet generated after planning/task/analyze phases | Draft PR packet must include scope, traceability, verification, generated-artifact status, known gaps, and ART-008 integration note. |

## Complexity Tracking

No constitution violations require a complexity exception.
