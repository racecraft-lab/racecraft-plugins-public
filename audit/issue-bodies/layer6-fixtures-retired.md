Priority: major

## Summary

Several Layer 6 dispatch fixtures encode behavior the autopilot contract has retired. Fixture 19 requires per-agent worktree isolation that Phase 7 now forbids, fixture 21 cites a deleted command file, fixture 22 names a missing workflow and a retired shell detector, and fixture 03's sample spec contradicts security-keyword routing. The Layer 6 README calls itself L7, names validators that do not exist, and stops its coverage matrix at fixture 17.

## Evidence

- **integration-layer6-1-001** (major): Fixture 19 requires each Phase 7 [P] worker to carry isolation: worktree and cites a run-partitioning algorithm in phase-execution.md Step 3. The reference forbids per-agent worktree isolation for Phase 7, requires declared disjoint file ownership (T001-T003 declare none, so they serialize), and now partitions through the partition-phase7-tasks helper. The fixture encodes retired behavior and nothing asserts the isolation field.
  - `tests/speckit-pro/layer6-integration/dispatch-fixtures/19-implement-parallel-p-tasks/README.md:5-16`, `tests/speckit-pro/layer6-integration/dispatch-fixtures/19-implement-parallel-p-tasks/prompt.txt:12-27`, `tests/speckit-pro/layer6-integration/dispatch-fixtures/19-implement-parallel-p-tasks/parser-fixture.jsonl:1`, `speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md:171-173`, `speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md:216-219`
- **integration-layer6-2-002** (major): Fixture 19 requires every [P] dispatch to carry isolation: worktree and to use RUNS with exactly 3 dispatches. The current contract forbids per-agent worktree isolation for Phase 7, has no isolation field in the Step 3c Agent template, and takes batches and waves from the partition-phase7-tasks helper rather than from consecutive [P] tags.
  - `tests/speckit-pro/layer6-integration/dispatch-fixtures/19-implement-parallel-p-tasks/prompt.txt:10-23`, `tests/speckit-pro/layer6-integration/dispatch-fixtures/19-implement-parallel-p-tasks/parser-fixture.jsonl:1`, `tests/speckit-pro/layer6-integration/dispatch-fixtures/19-implement-parallel-p-tasks/README.md:6-13`, `speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md:171-174`, `speckit-pro/skills/speckit-autopilot/references/phase-execution.md:2750-2770`
- **integration-layer6-1-005** (minor): The fixture 03 sample spec says Clarify should tag the password-hashing ambiguity [codebase, domain]. The word password is a security keyword, so parse-consensus-categories widens any such item to all three analysts and raises the bar to unanimity. The unit test that guards routing skips this fixture because its prompt has no fenced tagged item. The expected.json only requires one analyst, so the drift is silent.
  - `tests/speckit-pro/layer6-integration/dispatch-fixtures/03-redelegation-chain/sample-spec.md:8-27`, `tests/speckit-pro/layer6-integration/dispatch-fixtures/03-redelegation-chain/README.md:5-20`, `speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md:345-363`
- **integration-layer6-2-003** (minor): The fixture 21 prompt cites commands/resolve-pr.md section 4c, a file that no longer exists (speckit-pro/commands is gone). It also orders unconditional parallel dispatch, while SKILL.md 4c dispatches only with 2 or more partitions and fixes large enough to repay worker setup.
  - `tests/speckit-pro/layer6-integration/dispatch-fixtures/21-resolve-pr-parallel-files/prompt.txt:13-17`, `speckit-pro/skills/speckit-resolve-pr/SKILL.md:125-131`
- **pr-emission-and-stack-1-003** (major): The live prompt names docs/ai/specs/.process/SPEC-914-workflow.md, which does not exist, and uses the Codex `$speckit-autopilot` form while the layer runs Claude (`claude -p`). Other dispatch fixtures embed a self-contained scenario. The replay text says to implement a shared detect-stack-manager.sh, but the shipped detector is the Python helper detect-stack-manager-plan and AGENTS.md forbids new Bash. must_include_terms includes stack_manager_decision, a name no shipped file uses (the helper returns data.decision and the schema is stack-manager-decision). In replay mode the terms are checked against text the fixture itself contains, so they prove nothing.
  - `tests/speckit-pro/layer6-integration/dispatch-fixtures/22-stack-manager-replay/prompt.txt:1`, `tests/speckit-pro/layer6-integration/dispatch-fixtures/22-stack-manager-replay/parser-fixture.jsonl:2`, `tests/speckit-pro/layer6-integration/dispatch-fixtures/22-stack-manager-replay/expected.json:2`, `tests/speckit-pro/layer6-integration/dispatch-fixtures/22-stack-manager-replay/expected.json:17-23`
- **integration-layer6-1-002** (major): The Codex side section names validate-codex-skills.sh and validate-codex-agents.sh as the structural coverage, but neither file exists anywhere in the repo (checks now live in Python validators). The README also calls this layer L7 in six places, while layer 7 in suite-manifest.json is the parity layer (layer7-parity) and this directory is layer 6.
  - `tests/speckit-pro/layer6-integration/README.md:326-341`, `tests/speckit-pro/layer6-integration/README.md:33`, `tests/speckit-pro/layer6-integration/README.md:314`
- **integration-layer6-2-006** (minor): Layer 6 fixtures, prompts and README call themselves L7, but L7 is layer7-parity in suite-manifest.json. The e2e sample specs also say G0 to G6 while the READMEs say G1 to G7. README lines 330-335 name validate-codex-skills.sh and validate-codex-agents.sh, which do not exist (layer1-structural has only .py validators). The README coverage matrix omits dispatch fixtures 18-22 and the Class 4 grounding fixtures and their cost row.
  - `tests/speckit-pro/layer6-integration/e2e-fixtures/01-autopilot-minimal-smoke/prompt.txt:7`, `tests/speckit-pro/layer6-integration/e2e-fixtures/01-autopilot-minimal-smoke/sample-spec.md:1-3`, `tests/speckit-pro/layer6-integration/e2e-fixtures/02-autopilot-extended-pipeline/sample-spec.md:1-3`, `tests/speckit-pro/layer6-integration/e2e-fixtures/02-autopilot-extended-pipeline/README.md:36`, `tests/speckit-pro/layer6-integration/README.md:314`, `tests/speckit-pro/layer6-integration/README.md:330-335`
- **integration-layer6-1-003** (minor): The coverage matrix, subagents-reached list and cost-guard table stop at dispatch fixtures 01-17, and omit fixtures 18-22 (post-impl parallel, Phase 7 parallel, batch consensus, resolve-pr, stack manager) and the Class 4 grounding budget. Fixture 05 is the only dispatch fixture with no README, though the Fixture format section lists README.md for each.
  - `tests/speckit-pro/layer6-integration/README.md:31-72`, `tests/speckit-pro/layer6-integration/README.md:294-302`, `tests/speckit-pro/layer6-integration/dispatch-fixtures/05-clarify-spec-only/expected.json:1`

## Proposed fix

- integration-layer6-1-001: Rewrite the fixture 19 prompt, README and parser fixture to the current contract: no isolation field, tasks with declared disjoint ownership, partition-phase7-tasks batches. Update the citation from Step 3 to Steps 3a-3b.
- integration-layer6-2-002: Rewrite prompt.txt, README.md and parser-fixture.jsonl to the Step 3c template (no isolation, batch and wave wording from partition-phase7-tasks, disjoint owns), and assert that isolation is absent once the parser records it.
- integration-layer6-1-005: Change the sample spec to a keyword-free ambiguity, or state that the item widens to all three and assert that in expected.json.
- integration-layer6-2-003: Cite skills/speckit-resolve-pr/SKILL.md section 4c and state the dispatch-worthiness condition in the prompt and README.
- pr-emission-and-stack-1-003: Rewrite the prompt as a self-contained scenario that names the current helper and schema terms (detect-stack-manager-plan, stack-manager-decision.v1, mutation_boundary), drop the .sh reference, and set must_include_terms to names the shipped contract uses.
- integration-layer6-1-002: Point the Codex section at the actual Python validators (validate-agent-contracts.py, validate-skill-contracts.py or wherever those assertions live) and rename L7 to L6 in the README and in the fixture READMEs and sample specs that repeat it.
- integration-layer6-2-006: Rename L7 to Layer 6 in these files, correct the phase range, point the Codex section at the real .py validators, and extend the coverage matrix to fixtures 18-22 and Class 4.
- integration-layer6-1-003: Add rows for fixtures 18-22 and the grounding class to the matrix and guards, and add a README to fixture 05.

## Acceptance

- [ ] Fixture 19 follows the Step 3c template: no isolation field, disjoint ownership, partition-phase7-tasks batches. Once the parser records isolation, the fixture asserts its absence.
- [ ] Fixtures 03, 21 and 22 describe the current contract and use terms the shipped helpers emit.
- [ ] The Layer 6 README and fixture READMEs say Layer 6, point at the Python validators, and cover fixtures 18 to 22 and Class 4. Fixture 05 has a README.
- [ ] Layer 6 replay passes.

## Related

- Overlaps files changed by the open stop-policy stack: #845, #851. Land after that stack merges.
- Overlaps files changed by the in-progress fix for #832.
- Depends on #855

Found by the 2026-09 coherence audit.
