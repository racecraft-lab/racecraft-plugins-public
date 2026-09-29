Priority: major

## Summary

The Layer 7 runner invokes /speckit-pro:autopilot, a skill that does not exist, and the Claude grill-me evals name the same wrong commands. The legacy fixtures assume an agent-teams version floor and a --from-phase post flag that the shipped skills do not support. The runner's schema validator disagrees with native pairing, and a live run ends green when its only prose comparison is skipped.

## Evidence

- **parity-layer7-002** (major): Live mode runs `/speckit-pro:autopilot workflow.md`, but the skill is `speckit-autopilot`, so the plugin-qualified name is `/speckit-pro:speckit-autopilot`. The native audit doc lists `speckit-pro:autopilot` as a rejected identifier. The runner test asserts only argv[0] is -p, so the wrong name is untested.
  - `tests/speckit-pro/layer7-parity/run-parity-fixtures.py:418`, `tests/speckit-pro/layer7-parity/01-post-impl-parity/README.md:1`
- **functional-evals-2-001** (major): Claude grill-me evals 5, 6 and 7 name /speckit-pro:scaffold-spec and /speckit-pro:autopilot, which are not skills. The skills are speckit-scaffold-spec and speckit-autopilot. Eval 6 requires the answer to state that exact wrong command, and the Codex twins use the right names.
  - `tests/speckit-pro/layer3-functional/evals/grill-me-evals.json:55`, `tests/speckit-pro/layer3-functional/evals/grill-me-evals.json:71`, `tests/speckit-pro/layer3-functional/evals/grill-me-evals.json:77`, `speckit-pro/skills/grill-me/SKILL.md:34`
- **parity-layer7-003** (major): The legacy fixtures run `claude -p` and require Claude Code >= 2.1.32 for Path A. The autopilot references say teams need version >= 2.1.178 and a positively interactive session, and that `claude -p` always uses ordinary subagents. Both paths therefore take the same route, and the version floor disagrees with the resolver contract.
  - `tests/speckit-pro/layer7-parity/README.md:67`, `tests/speckit-pro/layer7-parity/01-post-impl-parity/README.md:24`, `tests/speckit-pro/layer7-parity/run-parity-fixtures.py:407`
- **integration-layer6-1-004** (minor): Fixture 18's prompt says AGENT_TEAMS_AVAILABLE is false when the env var is unset or Claude Code is older than 2.1.32. The reference and resolver require 2.1.178, an interactive session and passed live UAT, so the fixture states a retired capability rule.
  - `tests/speckit-pro/layer6-integration/dispatch-fixtures/18-post-impl-parallel-subagents/prompt.txt:5-7`, `speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md:77-92`, `speckit-pro/speckit_pro_runner/helpers/read_only.py:3075`
- **parity-layer7-004** (major): The fixture prose relies on a `--from-phase post` flag. The autopilot skills accept `--from-phase` only for specify through implement, so the flag does not exist. The workflow note also cites the stale path `tests/layer7-parity/01-post-impl-parity/`.
  - `tests/speckit-pro/layer7-parity/01-post-impl-parity/workflow.md:80`, `tests/speckit-pro/layer7-parity/01-post-impl-parity/README.md:15`, `tests/speckit-pro/layer7-parity/01-post-impl-parity/workflow.md:76`
- **parity-layer7-005** (major): Two implementations validate the same schema ids, and they disagree. The layer 7 runner rejects extractor `section_text`, which the native fixtures use. Native pairing requires tolerance-1 to use table_row_count and byte-identical to have no extractor. The runner accepts whole-file tolerance-1 and turns it into byte equality, which test-parity-runner.py:670 locks in.
  - `tests/speckit-pro/layer7-parity/run-parity-fixtures.py:26`, `tests/speckit-pro/lib/native_eval_pairing.py:17`, `tests/speckit-pro/lib/native_eval_pairing.py:156`
- **parity-layer7-006** (minor): The README says Layer 7 must not run in CI, while suite-manifest.json runs its dry-run. It also says the canonical catalog is still being integrated, although the catalog is active. (Review note: the README's four-case count is correct; git tracks fixtures 01 to 04.)
  - `tests/speckit-pro/layer7-parity/README.md:104`, `tests/speckit-pro/layer7-parity/README.md:98`, `tests/speckit-pro/layer7-parity/README.md:20`
- **parity-layer7-007** (minor): Field `gate_results` (tolerance key G0_through_G7) reads the Status column of Workflow Overview, which lists seven phases, not gates G0 to G7. The README claims every gate G0-G7 is compared.
  - `tests/speckit-pro/layer7-parity/01-post-impl-parity/expected-equivalence.json:41`, `tests/speckit-pro/layer7-parity/01-post-impl-parity/tolerance.json:31`, `tests/speckit-pro/layer7-parity/README.md:83`
- **parity-layer7-008** (minor): The judge and extractors CLI entry points, and judge byte-identical arms, have no caller besides their unit tests. They are leftovers of the shell-script port. The runner handles byte-identical itself, so judge_files is reached only for unsupported tolerances.
  - `tests/speckit-pro/layer7-parity/lib/judge.py:145`, `tests/speckit-pro/layer7-parity/lib/extractors.py:92`, `tests/speckit-pro/layer7-parity/run-parity-fixtures.py:646`
- **parity-layer7-009** (minor): In live mode a semantic-equivalent field whose values differ only counts as a skip, and main returns 0. A live parity run can end green with the only prose comparison unjudged.
  - `tests/speckit-pro/layer7-parity/run-parity-fixtures.py:676`, `tests/speckit-pro/layer7-parity/run-parity-fixtures.py:736`

## Proposed fix

- parity-layer7-002: Use the real skill name and assert the prompt argv element in test-parity-runner.py.
- functional-evals-2-001: Rename to /speckit-pro:speckit-scaffold-spec and /speckit-pro:speckit-autopilot (and /scaffold-spec to the full name) in prompts, expected_output and expectations of evals 5 to 7.
- parity-layer7-003: State the 2.1.178 floor and the interactive requirement in one place, or mark fixtures 01 and 02 as parser-regression only in the fixture READMEs, not as proof of Path A versus Path B.
- integration-layer6-1-004: Reword the prompt to say the runtime record reports teams unavailable, without a version number.
- parity-layer7-004: Describe how the run reaches Post from the current `--stage` and `--from-phase` grammar, and fix the path.
- parity-layer7-005: Share one contract validator, or version the schema id so each consumer accepts only its own fixtures. Reject whole-file tolerance-1 in the runner.
- parity-layer7-006: Correct the count, scope the CI sentence to `--live`, and update the integration status.
- parity-layer7-007: Extract the real gate results, or rename the field and the README claim.
- parity-layer7-008: Remove the CLI wrappers and unreachable arms, and drop the matching unit-test cases.
- parity-layer7-009: Return non-zero on a live skip, or require an explicit accept-skips flag.

## Acceptance

- [ ] Live mode and grill-me evals 5 to 7 use speckit-autopilot and speckit-scaffold-spec names. test-parity-runner.py asserts the prompt argv element and fails before the fix.
- [ ] Fixture 18 and the parity READMEs state the 2.1.178 floor and interactive requirement in one place, or no version.
- [ ] One contract validator (or distinct schema ids) serves Layer 7 and native pairing; whole-file tolerance-1 is rejected.
- [ ] A live run with an unjudged semantic field exits non-zero unless skips are explicitly accepted.
- [ ] gate_results is renamed or reads real gate results; dead CLI wrappers are removed.

## Related

- Depends on #854

Found by the 2026-09 coherence audit.
