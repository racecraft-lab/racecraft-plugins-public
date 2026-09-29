Priority: major

## Summary

Four active Codex trigger queries name files the workspace fixture does not hold, so a model that reads them hits a failed command and the harness rejects the trial. MEASUREMENT.md claims the fixture holds every named file. The qualification record and the frozen campaign drafts pin versions and digests that no longer match, and no test notices.

## Evidence

- **trigger-evals-001** (major): Four active Codex queries name files the workspace fixture does not hold (docs/prd.md, docs/ai/specs/SPEC-027-workflow.md, docs/ai/specs/SPEC-009-workflow.md twice), so a model that reads them hits a failed command, which the harness rejects as an invalid trial. MEASUREMENT.md claims the fixture holds every file named by file-backed queries. The fixture instead carries a root-level SPEC-009-workflow.md and unreferenced plan.md, notes/*, SPEC-015, SPEC-019, SPEC-041 and ubiquitous-language.md.
  - `tests/speckit-pro/layer2-trigger/codex-evals/speckit-prd-trigger.json:23`, `tests/speckit-pro/layer2-trigger/codex-evals/speckit-prd-trigger.json:31`, `tests/speckit-pro/layer2-trigger/codex-evals/speckit-resolve-pr-trigger.json:27`, `tests/speckit-pro/layer2-trigger/codex-evals/speckit-scaffold-spec-trigger.json:27`, `tests/speckit-pro/layer2-trigger/MEASUREMENT.md:113`, `tests/speckit-pro/layer2-trigger/fixtures/codex-workspace/SPEC-009-workflow.md:1`
- **trigger-evals-003** (minor): measurement-capabilities.json records Claude Code 2.1.269 as qualified while the runner, MEASUREMENT.md line 39, the drafts and the test stubs pin 2.1.270. MEASUREMENT.md admits the drift, but no code or test reads the JSON (ripwire grep finds only the prose link), so nothing detects it and the 'qualified' status has no enforcement.
  - `tests/speckit-pro/layer2-trigger/measurement-capabilities.json:4`, `tests/speckit-pro/layer2-trigger/measurement-capabilities.json:21`, `tests/speckit-pro/layer2-trigger/MEASUREMENT.md:5`, `tests/speckit-pro/layer2-trigger/MEASUREMENT.md:39`, `tests/speckit-pro/layer2-trigger/run-trigger-evals.py:34`
- **trigger-evals-004** (minor): Both frozen campaign drafts pin observer and catalog digests that no longer match the tree: compare-trigger-evals.py validate reports identities_current false for each. Only the fixture digest still matches. No test catches the drift, so the drafts cannot be used without a rebind.
  - `tests/speckit-pro/layer2-trigger/campaign-drafts/issue-573-full.draft.json:1542`, `tests/speckit-pro/layer2-trigger/campaign-drafts/issue-573-full.draft.json:1543`, `tests/speckit-pro/layer2-trigger/campaign-drafts/issue-573-pilot.draft.json:79`, `tests/speckit-pro/layer2-trigger/campaign-drafts/issue-573-pilot.draft.json:80`

## Proposed fix

- trigger-evals-001: Add the four missing paths to fixtures/codex-workspace, drop the unreferenced files, and add a unit test that every path-like token in a codex-evals query resolves inside the fixture. Changing the fixture changes the frozen fixture identity, so fold it into the next reviewed freeze.
- trigger-evals-003: Either add a unit test that binds measurement-capabilities.json versions, models and thresholds to the runner constants, or requalify on 2.1.270 and update the record. Consider one shared pin module for the runners, drafts and stub fixtures.
- trigger-evals-004: Rebind the drafts with compare-trigger-evals.py snapshot at the next freeze, and add a check that flags stale draft identities, or delete the drafts once the campaign is closed.

## Acceptance

- [ ] A unit test that fails before the fix: every path-like token in a codex-evals query resolves inside fixtures/codex-workspace.
- [ ] The fixture holds the four missing files and drops the unreferenced ones (fixture identity is refrozen).
- [ ] measurement-capabilities.json is bound to the runner pins by a test, or requalified.
- [ ] Stale campaign drafts are rebound or deleted, with a check for stale identities.

## Related

- None.

Found by the 2026-09 coherence audit.
