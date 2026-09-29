Priority: minor

## Summary

Fixture trees across the test suite are referenced by no test or catalog, or are stored in the argv shape of a deleted Bash script. They look like coverage but assert nothing, and duplicate trees hold the same scenarios. This hides which fixture is the real one when a contract changes.

## Evidence

- **functional-evals-1-003** (minor): The speckit-status/case-{1,2,3,5,6}/ and speckit-coach/case-2/ fixture trees are referenced by no catalog entry, test or runner. Catalog cases 2, 5, 6 use byte-identical copies under fixtures/grounding/ (frozen from headless scenario-roots); case-1 uses status-dashboard/case-1 (differing text) and coach case-2 uses grounding/coach-checklist. plan.md duplicates the headless coach-webhook-project.
  - `tests/speckit-pro/evals/fixtures/functional/speckit-status/case-1/docs/ai/specs/SPEC-021-workflow.md:1`, `tests/speckit-pro/evals/fixtures/functional/speckit-status/case-2/docs/ai/specs/SPEC-013-workflow.md:1`, `tests/speckit-pro/evals/fixtures/functional/speckit-status/case-3/docs/ai/specs/SPEC-013-workflow.md:1`, `tests/speckit-pro/evals/fixtures/functional/speckit-status/case-5/docs/ai/current-quarter-technical-roadmap.md:1`, `tests/speckit-pro/evals/fixtures/functional/speckit-status/case-6/docs/ai/current-technical-roadmap.md:1`, `tests/speckit-pro/evals/fixtures/functional/speckit-coach/case-2/spec.md:1`
- **lifecycle-skills-011** (minor): Only scaffold-contracts/missing/roadmap.txt and bootstrap/roadmap.txt are referenced (catalog.json and test-native-functional-catalog.py). The other 19 files, including all of status-contracts, are orphaned. Parallel live trees (scenario-contracts, functional/speckit-status, status-dashboard) hold the same scenarios, and strings such as 'Push failure recovery' appear nowhere else.
  - `tests/speckit-pro/evals/fixtures/scaffold-contracts/push-rejected/roadmap.txt:1`, `tests/speckit-pro/evals/fixtures/status-contracts/overall-dashboard/docs/ai/current-technical-roadmap.md:1`, `tests/speckit-pro/evals/fixtures/scaffold-contracts/relocation/team-123-legacy.txt:1`
- **pr-emission-and-stack-2-003** (minor): No test reads this fixture (the pr-packet directory is copied wholesale but this file is never opened). It names multi-pr-emission.sh and test-multi-pr-emission.sh, neither of which exists any longer.
  - `tests/speckit-pro/unit/fixtures/pr-packet/split-partial-failure-state.json:18`, `tests/speckit-pro/unit/fixtures/pr-packet/split-partial-failure-state.json:21`
- **runner-core-009** (minor): Eight fixtures are referenced by no test or code: six plan-layers cases (only valid-real, dependency-cycle, malformed-task, path-normalization and the bash-confinement plan are used) and normalization-cases.json and synthetic-paths.json (named only in a fixture plan.md as NEW). They look like coverage but assert nothing.
  - `tests/speckit-pro/unit/fixtures/plan-layers/checkbox-state/tasks.md:1`, `tests/speckit-pro/unit/fixtures/plan-layers/empty-increment/tasks.md:1`, `tests/speckit-pro/unit/fixtures/plan-layers/invalid-dependency/tasks.md:1`, `tests/speckit-pro/unit/fixtures/plan-layers/invalid-reference/tasks.md:1`, `tests/speckit-pro/unit/fixtures/plan-layers/missing-headings/tasks.md:1`, `tests/speckit-pro/unit/fixtures/plan-layers/missing-references/tasks.md:1`, `tests/speckit-pro/unit/fixtures/read-only-helpers/normalization-cases.json:1`, `tests/speckit-pro/unit/fixtures/read-only-helpers/synthetic-paths.json:1`
- **pr-emission-and-stack-2-004** (minor): Golden fixtures are stored as argv lines for a deleted Bash script and translated to runner inputs by FLAG_TO_INPUT, so the tests never use the request shape the skills send. CURRENT_INVENTORY repeats 33 subtest labels that the test matches in order.
  - `tests/speckit-pro/unit/test-estimate-spec-size.py:34`, `tests/speckit-pro/unit/test-estimate-spec-size.py:50`, `tests/speckit-pro/unit/test-estimate-spec-size.py:118`, `tests/speckit-pro/unit/fixtures/estimate-spec-size/multi-slice.args:1`
- **pr-emission-and-stack-2-007** (minor): The request fixture's inputs are byte-identical to pr-split-ratification/preserving-split.json, so the ratification request shape has two sources.
  - `tests/speckit-pro/unit/fixtures/read-only-helpers/requests/ratify-pr-split.json:1`, `tests/speckit-pro/unit/fixtures/pr-split-ratification/preserving-split.json:1`, `tests/speckit-pro/unit/test-ratify-pr-split.py:192`

## Proposed fix

- functional-evals-1-003: Delete the unreferenced speckit-status/case-* and speckit-coach/case-2 trees (keep speckit-coach/case-8), or point the catalog at them and drop the grounding copies.
- lifecycle-skills-011: Delete the unreferenced files, or wire them into catalog cases and add a check that every fixture file is referenced.
- pr-emission-and-stack-2-003: Delete the fixture, or wire a test to it and rewrite its slice records to the current runner helper.
- runner-core-009: Add the missing plan-layers negative tests (each case names a distinct invalid-plan path), or delete the unused fixtures.
- pr-emission-and-stack-2-004: Store the fixtures as runner inputs (like fixtures/read-only-helpers/requests/estimate-spec-size.json), drop the translator, and derive subtest labels from the fixture names.
- pr-emission-and-stack-2-007: Load the request fixture's inputs in test-ratify-pr-split.py and derive the failing variants from it, then delete preserving-split.json.

## Acceptance

- [ ] Each unreferenced tree or file is deleted or wired into a test.
- [ ] A check fails when a file under the named fixture roots is not referenced (at least for the functional and contract fixture roots).
- [ ] estimate-spec-size fixtures are runner requests; ratify-pr-split has one request source.

## Related

- Overlaps files changed by the open stop-policy stack: #850, #852. Land after that stack merges.

Found by the 2026-09 coherence audit.
