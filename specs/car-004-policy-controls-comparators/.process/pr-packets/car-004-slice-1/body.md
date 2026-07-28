# feat(car-004): add the three routing policy controls and their comparison rules

## Summary

<!-- speckit-pro-editable:summary:start -->
Freezes the three AC-2.17 policy controls — unpinned, adaptive, and orchestration-changing — and the rule CAR-011 will later apply to them, as two additive content-addressed contracts with committed frozen instances, standard-library validators, deterministic replay fixtures, a reserved-partition guard, and a machine-verified twin-handoff record.
<!-- speckit-pro-editable:summary:end -->

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Two new JSON Schema documents beside the frozen CAR-003 set in `contracts-claude/`, each content-addressed and referenced only through local `#/$defs/`.
- Two new standard-library validator modules in `layer6-efficiency/lib/`, sharing one fail-closed schema engine.
- Four committed frozen instances in a new `fixtures-controls/` directory: the registry, the comparison rule, the reserved partition entries, and the deterministic replay cases.
- A bounded live-smoke driver that prints a plan and seals a record, refusing API-key authentication, scored rows, reserved-partition references, and budget breaches.
- Three durable-named unit test modules registered at Layer 4 in `suite-manifest.json`.
- A twin-handoff record under `docs/ai/specs/.process/` whose first six categories re-derive from the committed artifacts in both directions.
<!-- speckit-pro-editable:what_changed:end -->

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
The comparison rule has to be frozen before anybody can see which side wins, otherwise the rule becomes authorable after the results are visible. That is the exact failure this feature exists to prevent, so CAR-004 ships the question and the procedure and deliberately withholds the answer.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

Read in this order:

1. The two schema documents: `policy-control-registry.schema.json` and `control-comparison.schema.json`.
2. Their frozen instances under `tests/speckit-pro/layer6-efficiency/fixtures-controls/`.
3. `lib/claude_policy_controls.py` — the shared fail-closed schema engine and the per-control rules.
4. `lib/claude_control_comparison.py` — the three-stage comparison procedure.
5. The replay and partition fixtures: `control-replay.json` and `partition-registry-entries.json`.
6. The three unit tests under `tests/speckit-pro/unit/`.
7. The twin-handoff record at `docs/ai/specs/.process/CAR-004-twin-handoff.md`.

Non-goals, so a missing thing is not read as an omission:

- No CAR-004 artifact states or implies which side wins; CAR-011 owns the comparison and the answer.
- No production adaptive-routing or orchestration feature changes; nothing under speckit-pro/ is touched.
- No frozen CAR-003 schema is edited. Additive-only, without exception.
- No new telemetry field is introduced; every adaptive signal binds an already-stable frozen member.
- No unpinned-control matrix over multiple parent sessions; one arm, one pinned parent.
- No scored smoke row and no scored mini-campaign. No supported path requires an API key.

Traceability:

- spec.md FR-001 through FR-037a are mapped per artifact in data-model.md.
- Success criteria SC-001 through SC-031 are mapped to expected outcomes in quickstart.md sections 3 and 5.
- Every one of the plan's fifteen declared file operations has at least one covering task in tasks.md.

## How To UAT

Walk `specs/car-004-policy-controls-comparators/quickstart.md` sections 1 through 4; every step is deterministic and needs no live model call. Section 5 is the developer-local bounded smoke and is still outstanding.

## UAT Runbook

1. `python3 tests/speckit-pro/run-all.py --layer 1` and `--layer 4` — both green before and after.
2. Confirm each row of the quickstart section 3 expected-outcome table against the named test.
3. `git diff --name-status origin/main...HEAD` over `contracts-claude/` and `lib/` — two added lines each, zero modified.
4. `git status --porcelain tests/speckit-pro/layer6-efficiency/results/` — no output.
5. Section 5's three bounded live smokes remain a manual operator step on the subscription path.

## Verification

- `python3 tests/speckit-pro/run-all.py` — 4909 of 4909 passed on the committed tree: L1 1428, L4 3295, L5 186. Zero live model calls. The branch adds 669 assertions across three new Layer 4 modules.
- `python3 tests/speckit-pro/run-all.py --layer 1` — 1428 of 1428 structural checks pass with the two new contract documents and the new fixtures-controls directory in place. This is quickstart sections 1 and 2.
- `python3 tests/speckit-pro/run-all.py --layer 4` — 3295 of 3295 pass. Every row of the quickstart section 3 expected-outcome table maps to a named test in one of the three new modules.
- `git diff --name-status origin/main...HEAD -- tests/speckit-pro/layer6-efficiency/contracts-claude/ and .../lib/` — Two added lines and zero modified lines under contracts-claude, two added and zero modified under lib. No frozen CAR-003 schema or module is edited. This is quickstart section 4.
- `pnpm --dir docs-site reference:generate then reference:check` — Reference pages are current. This gate is not covered by the test suite and fails only in clean continuous integration.
- `git status --porcelain tests/speckit-pro/layer6-efficiency/results/` — No output. Per-run smoke evidence stays operator-only under the existing layer6 gitignore and nothing from it is committed.
- `tests/speckit-pro/layer6-efficiency/run-control-smoke.py` — OUTSTANDING. The three bounded live smokes are developer-local, subscription-authenticated, and executed by hand; they have not been run on this branch. The deterministic plan step prints cleanly for all three controls.

## Scope

- Primary surface: harness/fixtures. Production files 0. Total files in the change set: 33.
- The setup-mode reviewability gate reads pass at reviewable LOC 250, production files 0, total files 15, one primary surface, no warnings and no blockers.
- Diff-mode reviewability is deferred on the authoritative runner, which supports setup mode only. The deferral and the direct measurement are recorded in plan.md under Reviewability Budget.

Changed files:

- docs-site/src/content/docs/reference/tests.md
- docs/ai/specs/.process/CAR-004-design-concept.md
- docs/ai/specs/.process/CAR-004-twin-handoff.md
- docs/ai/specs/.process/CAR-004-workflow.md
- docs/ai/specs/claude-agent-routing-roadmap-MOC.md
- docs/ai/specs/claude-agent-routing-technical-roadmap.md
- specs/car-004-policy-controls-comparators/SPEC-MOC.md
- specs/car-004-policy-controls-comparators/checklists/data-integrity.md
- specs/car-004-policy-controls-comparators/checklists/error-handling.md
- specs/car-004-policy-controls-comparators/checklists/llm-integration.md
- specs/car-004-policy-controls-comparators/checklists/requirements.md
- specs/car-004-policy-controls-comparators/contracts/control-comparison.md
- specs/car-004-policy-controls-comparators/contracts/policy-control-registry.md
- specs/car-004-policy-controls-comparators/contracts/validator-api.md
- specs/car-004-policy-controls-comparators/data-model.md
- specs/car-004-policy-controls-comparators/plan.md
- specs/car-004-policy-controls-comparators/quickstart.md
- specs/car-004-policy-controls-comparators/research.md
- specs/car-004-policy-controls-comparators/spec.md
- specs/car-004-policy-controls-comparators/tasks.md
- tests/speckit-pro/layer6-efficiency/contracts-claude/control-comparison.schema.json
- tests/speckit-pro/layer6-efficiency/contracts-claude/policy-control-registry.schema.json
- tests/speckit-pro/layer6-efficiency/fixtures-controls/control-comparison.json
- tests/speckit-pro/layer6-efficiency/fixtures-controls/control-replay.json
- tests/speckit-pro/layer6-efficiency/fixtures-controls/partition-registry-entries.json
- tests/speckit-pro/layer6-efficiency/fixtures-controls/policy-control-registry.json
- tests/speckit-pro/layer6-efficiency/lib/claude_control_comparison.py
- tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py
- tests/speckit-pro/layer6-efficiency/run-control-smoke.py
- tests/speckit-pro/suite-manifest.json
- tests/speckit-pro/unit/test-control-comparison-dominance.py
- tests/speckit-pro/unit/test-policy-control-contracts.py
- tests/speckit-pro/unit/test-twin-handoff-completeness.py

## Known Gaps

- The three bounded live smokes are not yet run. They are developer-local, never continuous integration, and each one demands a real dispatch on the subscription path; nothing in the packet claims a demonstration that was not observed.
- Two frozen documents answer to the English name environment contract. FR-006 settles the identity as the Claude-side environment_contract object; a binding authored from the name instead fails closed as a digest mismatch rather than passing quietly.
- The reserved partition's integrated_confirmation type is a forecast about CAR-011 made before its consumer exists. A later change is a new registry entry, never an edit.
- Review volume is genuine: roughly 2,000 to 2,700 changed lines, dominated by declarative JSON. Production files are zero, which is why the reviewable-LOC budget still reads clean.
- The 1,000,000-token and 30-minute smoke ceilings keep the moderate confidence at which they were recorded. Serializing them did not upgrade it, and they are hash-relevant, so revising one is a new registry version.
- Enum drift is caught rather than prevented. The frozen enums are read live from score-bundle.schema.json, so a future upstream membership change breaks CAR-004's totality checks; the failure messages name the frozen source so the cause is not misread.

## Rollback

No flag. The change is additive validation assets; reverting the commit removes them with no migration and no effect on any shipped default.
