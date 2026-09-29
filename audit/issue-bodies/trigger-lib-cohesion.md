Priority: major

## Summary

One historical trigger campaign is hard-coded into durable library code: digest pins, case ids and counts appear as literals across five modules, against the qualification protocol's own rule. The Claude and Codex trigger runners carry near-identical copies of corpus loading, observers and constants, and a library imports a runner script to reach its observers.

## Evidence

- **trigger-evals-002** (major): One historical campaign is hard-coded into durable library and protocol text: reviewed SHA-256 pins, case ids, and counts (137, 138, 410, 411, 414, 891, 1302, 1305) appear as literals in five modules, while a single 2,337-line file mixes those one-off pins with generic validators. qualification-protocol.md line 110 says campaign-specific evidence stays in the record rather than in repository code, and line 272 then documents one recovery scenario's arithmetic. The literal 1305 in trigger_campaign_execution.py duplicates EXPECTED_ACCOUNTING.
  - `tests/speckit-pro/lib/trigger_carry_forward.py:34`, `tests/speckit-pro/lib/trigger_carry_forward.py:41`, `tests/speckit-pro/lib/trigger_carry_forward.py:60`, `tests/speckit-pro/lib/trigger_carry_forward.py:1216`, `tests/speckit-pro/lib/trigger_comparison.py:394`, `tests/speckit-pro/lib/trigger_campaign.py:273`, `tests/speckit-pro/lib/trigger_campaign_execution.py:1165`, `tests/speckit-pro/layer2-trigger/qualification-protocol.md:110`, `tests/speckit-pro/layer2-trigger/qualification-protocol.md:272`
- **trigger-evals-009** (minor): test-trigger-campaign.py and test-trigger-campaign-execution.py copy the contextual_approval and observation builders, and trigger_carry_forward._file_identity clones the shipped validate-autopilot-phase-coverage._stable_file_identity.
  - `tests/speckit-pro/unit/test-trigger-campaign.py:28`, `tests/speckit-pro/unit/test-trigger-campaign-execution.py:65`, `tests/speckit-pro/unit/test-trigger-campaign.py:34`, `tests/speckit-pro/unit/test-trigger-campaign-execution.py:71`, `tests/speckit-pro/lib/trigger_carry_forward.py:187`
- **trigger-evals-005** (minor): The two runners carry near-identical copies of load_eval_corpus, sibling_skill_dirs and the trial-evidence retainer. run-trigger-evals.py redefines CLEANUP_TIMEOUT and DESCENDANT_EXIT_GRACE already defined in lib/trigger_process.py, and run-trigger-evals-codex.py re-implements eval-name listing. The shared lib modules already exist for this purpose.
  - `tests/speckit-pro/layer2-trigger/run-trigger-evals.py:87`, `tests/speckit-pro/layer2-trigger/run_codex_evals.py:106`, `tests/speckit-pro/layer2-trigger/run-trigger-evals.py:155`, `tests/speckit-pro/layer2-trigger/run_codex_evals.py:190`, `tests/speckit-pro/layer2-trigger/run-trigger-evals.py:667`, `tests/speckit-pro/layer2-trigger/run_codex_evals.py:1400`, `tests/speckit-pro/layer2-trigger/run-trigger-evals.py:73`, `tests/speckit-pro/lib/trigger_process.py:15`, `tests/speckit-pro/layer2-trigger/run-trigger-evals-codex.py:20`
- **trigger-evals-006** (minor): run_codex_evals.py (about 76 KB) mixes CLI orchestration with catalog inspection and the JSONL observer, and lib/trigger_comparison.py loads the whole runner script through spec_from_file_location just to call inspect_codex_jsonl and inspect_claude_stream. The library depends upward on a script, and replay imports the full script's top-level state.
  - `tests/speckit-pro/layer2-trigger/run_codex_evals.py:711`, `tests/speckit-pro/layer2-trigger/run_codex_evals.py:1011`, `tests/speckit-pro/layer2-trigger/run_codex_evals.py:1295`, `tests/speckit-pro/lib/trigger_comparison.py:132`, `tests/speckit-pro/lib/trigger_comparison.py:143`
- **trigger-evals-007** (minor): The candidate no-op description exists as four copies: two runner constants, controlled-descriptions.json and candidate.txt. The unit test only checks both runners against the JSON. Both runners also mutate the module global inside main() and restore it in finally.
  - `tests/speckit-pro/layer2-trigger/controlled-descriptions.json:8`, `tests/speckit-pro/layer2-trigger/controlled-descriptions/candidate.txt:1`, `tests/speckit-pro/layer2-trigger/run-trigger-evals.py:45`, `tests/speckit-pro/layer2-trigger/run_codex_evals.py:72`, `tests/speckit-pro/lib/native_eval_trigger.py:24`
- **trigger-evals-008** (minor): codex-evals/ and evals/ are near-identical copies (across 11 shared skills only 1 to 3 queries per file differ, mostly the explicit-invocation query). Both the wrapper and run_codex_evals.find_eval_file fall back to the Claude eval set, but the coverage test requires a codex-evals file for every Codex skill, so the fallback is unreachable. It would also run a query naming speckit-pro:<skill> on Codex.
  - `tests/speckit-pro/layer2-trigger/run-trigger-evals-codex.py:35`, `tests/speckit-pro/layer2-trigger/run_codex_evals.py:137`, `tests/speckit-pro/layer2-trigger/codex-evals/speckit-status-trigger.json:1`, `tests/speckit-pro/layer2-trigger/evals/speckit-status-trigger.json:1`, `tests/speckit-pro/unit/test-trigger-eval-coverage.py:88`

## Proposed fix

- trigger-evals-002: Move the frozen campaign pins and counts into the reviewed component or a single data module read by every validator, derive 891, 1305 and the like from it, keep generic admission logic in trigger_carry_forward.py, and move the recovery scenario out of the protocol doc.
- trigger-evals-009: Put the approval and observation builders in one shared test helper, and import or share the file-identity helper.
- trigger-evals-005: Move corpus loading and sibling discovery into lib/trigger_evidence.py or lib/trigger_process.py, and import the process constants instead of redefining them.
- trigger-evals-006: Extract the observers (inspect_codex_jsonl, inspect_claude_stream and their helpers) into a lib module that both the runners and the comparator import.
- trigger-evals-007: Keep the string in one lib constant that the runners import, and have the JSON and text files be checked against it. Pass the override as a parameter instead of mutating a global.
- trigger-evals-008: Drop the fallback so a missing codex-evals file fails loudly, or store one shared corpus plus per-host overrides.

## Acceptance

- [ ] Campaign pins and counts live in one data module; generic validators stay generic.
- [ ] Shared corpus loading, observers and constants live in tests/speckit-pro/lib and both runners import them.
- [ ] The candidate description has one source, and the Claude-eval fallback for Codex is removed.
- [ ] Layer 2 unit tests pass.

## Related

- Depends on: trigger-inputs-drift (issue number added after filing)

Found by the 2026-09 coherence audit.
