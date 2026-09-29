# Evidence for lane `release-tooling` (69 files)
Lines from the whole-repo scans that mention this lane's files. Empty section = none found, not none exists.

## doc-drift (16 lines)

```xml
<doc p="docs/ai/research/tool-agnostic-capability-discovery-spike.md" anchors="51" checked="18" drift="16" dated="0">
<a k="file-line" l="90" c="224" why="range-straddles" ref="speckit-pro/.claude-plugin/plugin.json:1-20" got="dependencies" tgt="speckit-pro/.claude-plugin/plugin.json:20"/>
<a k="file-line" l="94" c="187" why="range-straddles" ref="speckit-pro/.codex-plugin/plugin.json:22-43" got="defaultPrompt" tgt="speckit-pro/.codex-plugin/plugin.json:43"/>
<a k="file-line" l="120" c="296" why="range-straddles" ref="speckit-pro/.codex-plugin/plugin.json:22-43" got="defaultPrompt" tgt="speckit-pro/.codex-plugin/plugin.json:43"/>
</doc>
<doc p="tests/speckit-pro/layer6-integration/performance-fixtures/draft-pr-emission/source/research.md" anchors="84" checked="44" drift="0" dated="17">
<a k="file-line" l="151" c="5" why="past-eof" kind="dated-record" rec="stamp" ref="speckit-pro/speckit_pro_runner/gates/release.py:1242-1245" got="747 lines" tgt="speckit-pro/speckit_pro_runner/gates/release.py"/>
</doc>
<weak-file-line p="docs/ai/specs/.process/ART-001-workflow.md" n="1">
<w l="1426" c="31" ref="scripts/release_note_policy.py:508" resolves-to="validate_release_note"/>
</weak-file-line>
<weak-file-line p="docs/ai/specs/.process/ART-002-workflow.md" n="3">
<w l="1585" c="33" ref="speckit-pro/speckit_pro_runner/gates/payloads.py:303" resolves-to="build_installed_plugin_payloads"/>
</weak-file-line>
<weak-file-line p="tests/speckit-pro/evals/audit/unit-release-tooling-audit.md" n="3">
</weak-file-line>
```

## clones (727 lines)

```xml
<group type="2" gid="12" tokens="109" n="2">
<f n="changed_files_for_base" p="scripts/check-go-module.py:50"/>
<f n="changed_files_for_base" p="scripts/classify-docs-validation.py:129"/>
</group>
<group type="2" gid="29" tokens="68" n="2">
<f n="_workflow_table_rows" p="speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:4414"/>
<f n="_table_row_indexes" p="tests/speckit-pro/layer1-structural/validate-ci-release-contracts.py:1093"/>
</group>
<group type="2" gid="20" tokens="59" n="3">
<f n="load_composer" p="tests/speckit-pro/unit/test-compose-release-notes.py:54"/>
<f n="load_helper" p="tests/speckit-pro/unit/test-docs-artifact.py:24"/>
<f n="import_runner" p="tests/speckit-pro/unit/test-functional-headless-runner.py:33"/>
</group>
<group type="2" gid="20" tokens="57" n="2">
<f n="load_module" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:25"/>
<f n="load_module" p="tests/speckit-pro/unit/test-typesafe-jev-release-build.py:33"/>
</group>
<group type="2" gid="194" tokens="52" n="2">
<f n="test_rename_out_of_preflight_surface_still_runs_heavy_jobs" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:521"/>
<f n="test_docs_only_change_skips_heavy_jobs" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:538"/>
</group>
<group type="2" gid="20" tokens="49" n="3">
<f n="import_checker" p="tests/speckit-pro/unit/test-check-toolchain.py:109"/>
<f n="import_runner" p="tests/speckit-pro/unit/test-parity-runner.py:112"/>
<f n="import_runner" p="tests/speckit-pro/unit/test-trigger-signal-restoration.py:43"/>
</group>
<group type="2" gid="203" tokens="49" n="2">
<f n="inventory_check" p="tests/speckit-pro/unit/test-compose-release-notes.py:43"/>
<f n="inventory_check" p="tests/speckit-pro/unit/test-release-note-policy.py:40"/>
</group>
<group type="2" gid="166" tokens="44" n="2">
<f n="_architecture_family" p="tests/speckit-pro/run-container-preflight.py:152"/>
<f n="_architecture_family" p="tests/speckit-pro/run-hosted-windows-preflight.py:139"/>
</group>
<group type="2" gid="11" tokens="42" n="3">
<f n="run_go" p="scripts/build-typesafe-jev-release.py:149"/>
<f n="run_verify_binary" p="scripts/build-typesafe-jev-release.py:176"/>
<f n="run_smoke_binary" p="scripts/build-typesafe-jev-release.py:185"/>
</group>
<group type="3" gid="10" tokens="52" n="2" similarity="0.85">
<f n="append_summary" p="scripts/audit-release-notes.py:32"/>
<f n="_write_step_summary" p="scripts/compose-release-notes.py:586"/>
</group>
<group type="3" gid="11" tokens="42" n="2" similarity="0.98">
<f n="run_go" p="scripts/build-typesafe-jev-release.py:149"/>
<f n="run_gh" p="scripts/build-typesafe-jev-release.py:158"/>
</group>
<group type="3" gid="11" tokens="49" n="2" similarity="0.88">
<f n="run_go" p="scripts/build-typesafe-jev-release.py:149"/>
<f n="run_installer" p="scripts/build-typesafe-jev-release.py:167"/>
</group>
<group type="3" gid="11" tokens="49" n="2" similarity="0.90">
<f n="run_gh" p="scripts/build-typesafe-jev-release.py:158"/>
<f n="run_installer" p="scripts/build-typesafe-jev-release.py:167"/>
</group>
<group type="3" gid="13" tokens="96" n="2" similarity="0.88">
<f n="run_go" p="scripts/check-go-module.py:102"/>
<f n="run_gofmt" p="scripts/check-go-module.py:122"/>
</group>
<group type="3" gid="10" tokens="56" n="2" similarity="0.85">
<f n="_write_step_summary" p="scripts/compose-release-notes.py:586"/>
<f n="_write_github_output" p="scripts/compose-release-notes.py:597"/>
</group>
<group type="3" gid="10" tokens="61" n="2" similarity="0.80">
<f n="_write_github_output" p="scripts/compose-release-notes.py:597"/>
<f n="append_plugin_matrix" p="scripts/emit-plugin-matrix.py:20"/>
</group>
<group type="3" gid="14" tokens="181" n="2" similarity="0.87">
<f n="run_known_command" p="scripts/refresh-local-plugin.py:84"/>
<f n="_execute" p="scripts/sync_release_pr.py:92"/>
</group>
<group type="3" gid="15" tokens="83" n="2" similarity="0.89">
<f n="ensure_claude_marketplace_is_local" p="scripts/refresh-local-plugin.py:259"/>
<f n="ensure_codex_marketplace_is_local" p="scripts/refresh-local-plugin.py:316"/>
</group>
<group type="3" gid="16" tokens="141" n="2" similarity="0.96">
<f n="refresh_claude_install" p="scripts/refresh-local-plugin.py:281"/>
<f n="refresh_codex_install" p="scripts/refresh-local-plugin.py:333"/>
</group>
<group type="3" gid="18" tokens="85" n="2" similarity="0.85">
<f n="_label_names" p="scripts/release_note_policy.py:473"/>
<f n="codex_route_aware_remediation_action_summaries" p="speckit-pro/speckit_pro_runner/helpers/install.py:3720"/>
</group>
<group type="3" gid="19" tokens="44" n="2" similarity="0.95">
<f n="parse_json_array" p="scripts/resolve_release_prs.py:25"/>
<f n="_parse_toml" p="speckit-pro/speckit_pro_runner/agent_materialization.py:170"/>
</group>
<group type="3" gid="19" tokens="46" n="2" similarity="0.93">
<f n="parse_json_array" p="scripts/resolve_release_prs.py:25"/>
<f n="_json_object" p="speckit-pro/speckit_pro_runner/verification_docker_runtime.py:214"/>
</group>
<group type="3" gid="20" tokens="64" n="2" similarity="0.95">
<f n="regenerated_artifact_paths" p="scripts/sync_release_pr.py:70"/>
<f n="_load_coverage_tests" p="tests/speckit-pro/unit/test-autonomy-boundary-receipt-replay.py:38"/>
</group>
<group type="3" gid="20" tokens="64" n="2" similarity="0.92">
<f n="regenerated_artifact_paths" p="scripts/sync_release_pr.py:70"/>
<f n="load_privacy_scan_module" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:78"/>
</group>
<group type="3" gid="20" tokens="64" n="2" similarity="0.81">
<f n="regenerated_artifact_paths" p="scripts/sync_release_pr.py:70"/>
<f n="load_composer" p="tests/speckit-pro/unit/test-compose-release-notes.py:54"/>
</group>
<group type="3" gid="20" tokens="64" n="2" similarity="0.85">
<f n="regenerated_artifact_paths" p="scripts/sync_release_pr.py:70"/>
<f n="load_gate_tests" p="tests/speckit-pro/unit/test-installed-release-gates.py:21"/>
</group>
<group type="3" gid="20" tokens="64" n="2" similarity="0.85">
<f n="regenerated_artifact_paths" p="scripts/sync_release_pr.py:70"/>
<f n="load_script_module" p="tests/speckit-pro/unit/test-integration-runners.py:49"/>
</group>
<group type="3" gid="20" tokens="64" n="2" similarity="0.84">
<f n="regenerated_artifact_paths" p="scripts/sync_release_pr.py:70"/>
<f n="load_script" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:32"/>
</group>
<group type="3" gid="30" tokens="50" n="2" similarity="0.97">
<f n="workflow_criteria_rows" p="speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:4435"/>
<f n="criteria_row_indexes" p="tests/speckit-pro/layer1-structural/validate-ci-release-contracts.py:1112"/>
</group>
<group type="3" gid="57" tokens="141" n="2" similarity="0.84">
<f n="output_root_from_inputs" p="speckit-pro/speckit_pro_runner/gates/payloads.py:859"/>
<f n="install_root_from_case" p="speckit-pro/speckit_pro_runner/gates/payloads.py:883"/>
</group>
<group type="3" gid="20" tokens="54" n="2" similarity="0.95">
<f n="load_module" p="tests/speckit-pro/layer1-structural/test-structural-regressions.py:23"/>
<f n="load_helper" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:27"/>
</group>
<group type="3" gid="91" tokens="66" n="2" similarity="0.82">
<f n="test_agent_instruction_validator_rejects_claude_drift" p="tests/speckit-pro/layer1-structural/test-structural-regressions.py:85"/>
<f n="test_snapshot_tree_excludes_local_worktrees" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:1255"/>
</group>
<group type="3" gid="91" tokens="67" n="2" similarity="0.90">
<f n="test_agent_instruction_validator_rejects_unexpected_agent_scope" p="tests/speckit-pro/layer1-structural/test-structural-regressions.py:93"/>
<f n="test_snapshot_tree_excludes_local_worktrees" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:1255"/>
</group>
<group type="3" gid="94" tokens="215" n="2" similarity="0.86">
<f n="_split_mapping" p="tests/speckit-pro/layer1-structural/validate-ci-release-contracts.py:40"/>
<f n="_scalar_sane" p="tests/speckit-pro/layer1-structural/validate-ci-release-contracts.py:94"/>
</group>
<group type="3" gid="95" tokens="73" n="2" similarity="0.87">
<f n="_scalar_values" p="tests/speckit-pro/layer1-structural/validate-ci-release-contracts.py:669"/>
<f n="_run_commands" p="tests/speckit-pro/layer1-structural/validate-ci-release-contracts.py:707"/>
</group>
<group type="3" gid="96" tokens="111" n="2" similarity="0.88">
<f n="_named_step_block" p="tests/speckit-pro/layer1-structural/validate-ci-release-contracts.py:673"/>
<f n="_python_function_block" p="tests/speckit-pro/layer1-structural/validate-ci-release-contracts.py:682"/>
</group>
<group type="3" gid="20" tokens="60" n="2" similarity="0.87">
<f n="load_coverage_validator" p="tests/speckit-pro/layer1-structural/validate-ci-release-contracts.py:1188"/>
<f n="load_validator_module" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:62"/>
</group>
<group type="3" gid="20" tokens="60" n="2" similarity="0.84">
<f n="load_coverage_validator" p="tests/speckit-pro/layer1-structural/validate-ci-release-contracts.py:1188"/>
<f n="load_coverage_validator" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1061"/>
</group>
<group type="3" gid="20" tokens="60" n="2" similarity="0.87">
<f n="load_coverage_validator" p="tests/speckit-pro/layer1-structural/validate-ci-release-contracts.py:1188"/>
<f n="load_composer" p="tests/speckit-pro/unit/test-compose-release-notes.py:54"/>
</group>
<group type="3" gid="20" tokens="60" n="2" similarity="0.87">
<f n="load_coverage_validator" p="tests/speckit-pro/layer1-structural/validate-ci-release-contracts.py:1188"/>
<f n="load_module" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:25"/>
</group>
<group type="3" gid="20" tokens="60" n="2" similarity="0.89">
<f n="load_coverage_validator" p="tests/speckit-pro/layer1-structural/validate-ci-release-contracts.py:1188"/>
<f n="import_script" p="tests/speckit-pro/unit/test-trigger-eval-runners.py:57"/>
</group>
<group type="3" gid="97" tokens="49" n="2" similarity="0.80">
<f n="run_builder" p="tests/speckit-pro/layer1-structural/validate-payload-contracts.py:33"/>
<f n="run_hook" p="tests/speckit-pro/unit/test-claude-hooks.py:26"/>
</group>
<group type="3" gid="98" tokens="718" n="2" similarity="0.82">
<f n="validate_claude_payload" p="tests/speckit-pro/layer1-structural/validate-payload-contracts.py:414"/>
<f n="validate_codex_payload" p="tests/speckit-pro/layer1-structural/validate-payload-contracts.py:459"/>
</group>
<group type="3" gid="20" tokens="90" n="2" similarity="0.81">
<f n="_codex_helpers" p="tests/speckit-pro/lib/native_eval_adapters.py:330"/>
<f n="load_gate_tests" p="tests/speckit-pro/unit/test-installed-release-gates.py:21"/>
</group>
<group type="3" gid="123" tokens="59" n="2" similarity="0.83">
<f n="_write_text" p="tests/speckit-pro/lib/native_eval_adapters.py:539"/>
<f n="_append_outputs" p="tests/speckit-pro/run-container-preflight.py:136"/>
</group>
<group type="3" gid="165" tokens="48" n="2" similarity="0.96">
<f n="_write_json" p="tests/speckit-pro/run-container-preflight.py:111"/>
<f n="_write_json" p="tests/speckit-pro/run-hosted-windows-preflight.py:55"/>
</group>
<group type="3" gid="165" tokens="48" n="2" similarity="0.80">
<f n="_write_json" p="tests/speckit-pro/run-hosted-windows-preflight.py:55"/>
<f n="write_route_policy_manifest" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:705"/>
</group>
<group type="3" gid="20" tokens="51" n="2" similarity="0.84">
<f n="_load_run_all" p="tests/speckit-pro/test-run-all.py:34"/>
<f n="import_checker" p="tests/speckit-pro/unit/test-check-toolchain.py:109"/>
</group>
<group type="3" gid="20" tokens="51" n="2" similarity="0.82">
<f n="_load_run_all" p="tests/speckit-pro/test-run-all.py:34"/>
<f n="load_helper" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:27"/>
</group>
<group type="3" gid="167" tokens="44" n="2" similarity="0.96">
<f n="test_default_config_runs_deterministic_layers" p="tests/speckit-pro/test-run-all.py:49"/>
<f n="test_full_mode_for_rendered_docs" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:213"/>
</group>
<group type="3" gid="167" tokens="55" n="2" similarity="0.82">
<f n="test_layer_and_live_and_verbose_flags" p="tests/speckit-pro/test-run-all.py:65"/>
<f n="test_path_boundaries_do_not_match_prefix_lookalikes" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:269"/>
</group>
<group type="3" gid="20" tokens="59" n="2" similarity="0.82">
<f n="_load_coverage_tests" p="tests/speckit-pro/unit/test-autonomy-boundary-receipt-replay.py:38"/>
<f n="load_composer" p="tests/speckit-pro/unit/test-compose-release-notes.py:54"/>
</group>
<group type="3" gid="20" tokens="63" n="2" similarity="0.88">
<f n="_load_coverage_tests" p="tests/speckit-pro/unit/test-autonomy-boundary-receipt-replay.py:38"/>
<f n="load_gate_tests" p="tests/speckit-pro/unit/test-installed-release-gates.py:21"/>
</group>
<group type="3" gid="20" tokens="64" n="2" similarity="0.87">
<f n="_load_coverage_tests" p="tests/speckit-pro/unit/test-autonomy-boundary-receipt-replay.py:38"/>
<f n="load_script" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:32"/>
</group>
<group type="3" gid="20" tokens="58" n="2" similarity="0.82">
<f n="_load_coverage_tests" p="tests/speckit-pro/unit/test-autonomy-boundary-receipt-replay.py:38"/>
<f n="load_module" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:25"/>
</group>
<group type="3" gid="20" tokens="49" n="2" similarity="0.90">
<f n="_load" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:76"/>
<f n="load_helper" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:27"/>
</group>
<group type="3" gid="20" tokens="57" n="2" similarity="0.82">
<f n="_load" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:76"/>
<f n="load_module" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:25"/>
</group>
<group type="3" gid="20" tokens="59" n="2" similarity="0.98">
<f n="load_validator_module" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:62"/>
<f n="load_composer" p="tests/speckit-pro/unit/test-compose-release-notes.py:54"/>
</group>
<group type="3" gid="20" tokens="64" n="2" similarity="0.89">
<f n="load_validator_module" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:62"/>
<f n="load_script" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:32"/>
</group>
<group type="3" gid="20" tokens="59" n="2" similarity="0.95">
<f n="load_validator_module" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:62"/>
<f n="load_module" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:25"/>
</group>
<group type="3" gid="20" tokens="63" n="2" similarity="0.85">
<f n="load_privacy_scan_module" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:78"/>
<f n="load_gate_tests" p="tests/speckit-pro/unit/test-installed-release-gates.py:21"/>
</group>
<group type="3" gid="194" tokens="54" n="2" similarity="0.85">
<f n="test_complete_workflow_and_state_pass" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:479"/>
<f n="test_non_windows_platform_is_rejected_before_subprocesses" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:200"/>
</group>
<group type="3" gid="194" tokens="64" n="2" similarity="0.81">
<f n="test_complete_workflow_and_state_pass" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:479"/>
<f n="test_native_arm64_matches_windows_arm64_role" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:210"/>
</group>
<group type="3" gid="194" tokens="47" n="2" similarity="0.82">
<f n="test_complete_workflow_and_state_pass" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:479"/>
<f n="test_mutable_spec_kit_ref_is_rejected_before_subprocesses" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:269"/>
</group>
<group type="3" gid="194" tokens="60" n="2" similarity="0.80">
<f n="test_missing_confidence_gate_in_workflow_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3567"/>
<f n="test_rename_out_of_preflight_surface_still_runs_heavy_jobs" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:521"/>
</group>
<group type="3" gid="194" tokens="54" n="2" similarity="0.83">
<f n="test_missing_confidence_gate_in_state_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3574"/>
<f n="test_non_windows_platform_is_rejected_before_subprocesses" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:200"/>
</group>
<group type="3" gid="194" tokens="64" n="2" similarity="0.81">
<f n="test_missing_confidence_gate_in_state_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3574"/>
<f n="test_native_arm64_matches_windows_arm64_role" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:210"/>
</group>
<group type="3" gid="194" tokens="49" n="2" similarity="0.83">
<f n="test_missing_confidence_gate_in_state_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3574"/>
<f n="test_mutable_spec_kit_ref_is_rejected_before_subprocesses" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:269"/>
</group>
<group type="3" gid="194" tokens="49" n="2" similarity="0.80">
<f n="test_missing_confidence_gate_in_state_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3574"/>
<f n="test_deletion_only_on_preflight_surface_still_runs_heavy_jobs" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:530"/>
</group>
<group type="3" gid="194" tokens="54" n="2" similarity="0.87">
<f n="test_missing_post_items_in_state_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3580"/>
<f n="test_non_windows_platform_is_rejected_before_subprocesses" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:200"/>
</group>
<group type="3" gid="194" tokens="64" n="2" similarity="0.81">
<f n="test_missing_post_items_in_state_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3580"/>
<f n="test_native_arm64_matches_windows_arm64_role" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:210"/>
</group>
<group type="3" gid="194" tokens="49" n="2" similarity="0.83">
<f n="test_missing_post_items_in_state_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3580"/>
<f n="test_mutable_spec_kit_ref_is_rejected_before_subprocesses" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:269"/>
</group>
<group type="3" gid="194" tokens="49" n="2" similarity="0.80">
<f n="test_missing_post_items_in_state_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3580"/>
<f n="test_deletion_only_on_preflight_surface_still_runs_heavy_jobs" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:530"/>
</group>
<group type="3" gid="194" tokens="60" n="2" similarity="0.82">
<f n="test_collapsed_later_phase_plan_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3586"/>
<f n="test_non_windows_platform_is_rejected_before_subprocesses" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:200"/>
</group>
<group type="3" gid="194" tokens="64" n="2" similarity="0.87">
<f n="test_collapsed_later_phase_plan_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3586"/>
<f n="test_native_arm64_matches_windows_arm64_role" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:210"/>
</group>
<group type="3" gid="194" tokens="76" n="2" similarity="0.82">
<f n="test_collapsed_later_phase_plan_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3586"/>
<f n="test_native_arm64_is_rejected_for_windows_x64_role" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:240"/>
</group>
<group type="3" gid="194" tokens="60" n="2" similarity="0.80">
<f n="test_collapsed_later_phase_plan_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3586"/>
<f n="test_rename_out_of_preflight_surface_still_runs_heavy_jobs" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:521"/>
</group>
<group type="3" gid="194" tokens="55" n="2" similarity="0.88">
<f n="test_malformed_state_is_input_error" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3614"/>
<f n="test_non_windows_platform_is_rejected_before_subprocesses" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:200"/>
</group>
<group type="3" gid="194" tokens="64" n="2" similarity="0.89">
<f n="test_malformed_state_is_input_error" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3614"/>
<f n="test_native_arm64_matches_windows_arm64_role" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:210"/>
</group>
<group type="3" gid="194" tokens="76" n="2" similarity="0.84">
<f n="test_malformed_state_is_input_error" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3614"/>
<f n="test_native_arm64_is_rejected_for_windows_x64_role" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:240"/>
</group>
<group type="3" gid="194" tokens="61" n="2" similarity="0.81">
<f n="test_malformed_state_is_input_error" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3614"/>
<f n="test_malformed_runner_json_fails_closed" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:252"/>
</group>
<group type="3" gid="194" tokens="66" n="2" similarity="0.83">
<f n="test_malformed_state_is_input_error" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3614"/>
<f n="test_draft_pull_request_defers_heavy_preflight_without_git_diff" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:509"/>
</group>
<group type="3" gid="194" tokens="55" n="2" similarity="0.90">
<f n="test_malformed_state_is_input_error" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3614"/>
<f n="test_rename_out_of_preflight_surface_still_runs_heavy_jobs" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:521"/>
</group>
<group type="3" gid="20" tokens="49" n="2" similarity="0.89">
<f n="load_coverage_validator" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1061"/>
<f n="import_checker" p="tests/speckit-pro/unit/test-check-toolchain.py:109"/>
</group>
<group type="3" gid="20" tokens="59" n="2" similarity="0.81">
<f n="load_coverage_validator" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1061"/>
<f n="load_composer" p="tests/speckit-pro/unit/test-compose-release-notes.py:54"/>
</group>
<group type="3" gid="20" tokens="49" n="2" similarity="0.87">
<f n="load_coverage_validator" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1061"/>
<f n="load_helper" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:27"/>
</group>
<group type="3" gid="202" tokens="74" n="2" similarity="0.94">
<f n="run_checker" p="tests/speckit-pro/unit/test-check-toolchain.py:62"/>
<f n="run_script" p="tests/speckit-pro/unit/test-eval-runner-skill-selection.py:587"/>
</group>
<group type="3" gid="202" tokens="74" n="2" similarity="0.89">
<f n="run_checker" p="tests/speckit-pro/unit/test-check-toolchain.py:62"/>
<f n="run_cli" p="tests/speckit-pro/unit/test-parity-judge.py:52"/>
</group>
<group type="3" gid="202" tokens="74" n="2" similarity="0.83">
<f n="run_checker" p="tests/speckit-pro/unit/test-check-toolchain.py:62"/>
<f n="run_sync" p="tests/speckit-pro/unit/test-sync-marketplace-versions.py:24"/>
</group>
<group type="3" gid="202" tokens="74" n="2" similarity="0.92">
<f n="run_checker" p="tests/speckit-pro/unit/test-check-toolchain.py:62"/>
<f n="run_script" p="tests/speckit-pro/unit/test-transcript-tools.py:29"/>
</group>
<group type="3" gid="20" tokens="59" n="2" similarity="0.81">
<f n="import_checker" p="tests/speckit-pro/unit/test-check-toolchain.py:109"/>
<f n="load_composer" p="tests/speckit-pro/unit/test-compose-release-notes.py:54"/>
</group>
<group type="3" gid="20" tokens="49" n="2" similarity="0.84">
<f n="import_checker" p="tests/speckit-pro/unit/test-check-toolchain.py:109"/>
<f n="load_helper" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:27"/>
</group>
<group type="3" gid="20" tokens="63" n="2" similarity="0.80">
<f n="load_composer" p="tests/speckit-pro/unit/test-compose-release-notes.py:54"/>
<f n="load_gate_tests" p="tests/speckit-pro/unit/test-installed-release-gates.py:21"/>
</group>
<group type="3" gid="20" tokens="59" n="2" similarity="0.89">
<f n="load_composer" p="tests/speckit-pro/unit/test-compose-release-notes.py:54"/>
<f n="load_script_module" p="tests/speckit-pro/unit/test-integration-runners.py:49"/>
</group>
<group type="3" gid="20" tokens="64" n="2" similarity="0.91">
<f n="load_composer" p="tests/speckit-pro/unit/test-compose-release-notes.py:54"/>
<f n="load_script" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:32"/>
</group>
<group type="3" gid="20" tokens="59" n="2" similarity="0.97">
<f n="load_composer" p="tests/speckit-pro/unit/test-compose-release-notes.py:54"/>
<f n="load_module" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:25"/>
</group>
<group type="3" gid="20" tokens="59" n="2" similarity="0.98">
<f n="load_composer" p="tests/speckit-pro/unit/test-compose-release-notes.py:54"/>
<f n="import_script" p="tests/speckit-pro/unit/test-trigger-eval-runners.py:57"/>
</group>
<group type="3" gid="204" tokens="101" n="2" similarity="0.85">
<f n="request_json" p="tests/speckit-pro/unit/test-compose-release-notes.py:741"/>
<f n="request_json" p="tests/speckit-pro/unit/test-compose-release-notes.py:812"/>
</group>
<group type="3" gid="204" tokens="74" n="2" similarity="0.88">
<f n="request_json" p="tests/speckit-pro/unit/test-compose-release-notes.py:741"/>
<f n="request_json" p="tests/speckit-pro/unit/test-compose-release-notes.py:897"/>
</group>
<group type="3" gid="205" tokens="544" n="2" similarity="0.81">
<f n="test_live_rerun_reuses_persisted_snapshot_despite_mutable_pr_metadata" p="tests/speckit-pro/unit/test-compose-release-notes.py:799"/>
<f n="test_failed_patch_rerun_recomposes_identical_bytes_from_same_snapshot" p="tests/speckit-pro/unit/test-compose-release-notes.py:934"/>
</group>
<group type="3" gid="204" tokens="112" n="2" similarity="0.85">
<f n="request_json" p="tests/speckit-pro/unit/test-compose-release-notes.py:812"/>
<f n="request_json" p="tests/speckit-pro/unit/test-compose-release-notes.py:945"/>
</group>
<group type="3" gid="206" tokens="123" n="2" similarity="0.88">
<f n="test_networking_and_dependencies_stay_stdlib_only" p="tests/speckit-pro/unit/test-compose-release-notes.py:1080"/>
<f n="top_level_imports" p="tests/speckit-pro/unit/test-release-note-policy.py:24"/>
</group>
<group type="3" gid="194" tokens="59" n="2" similarity="0.85">
<f n="test_absent_log_aggregates_to_zero_without_failing" p="tests/speckit-pro/unit/test-consensus-routing-helpers.py:339"/>
<f n="test_rename_out_of_preflight_surface_still_runs_heavy_jobs" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:521"/>
</group>
<group type="3" gid="202" tokens="68" n="2" similarity="0.89">
<f n="run_script" p="tests/speckit-pro/unit/test-eval-runner-skill-selection.py:587"/>
<f n="run_sync" p="tests/speckit-pro/unit/test-sync-marketplace-versions.py:24"/>
</group>
<group type="3" gid="194" tokens="64" n="2" similarity="0.90">
<f n="test_non_windows_platform_is_rejected_before_subprocesses" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:200"/>
<f n="test_native_arm64_matches_windows_arm64_role" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:210"/>
</group>
<group type="3" gid="194" tokens="76" n="2" similarity="0.83">
<f n="test_non_windows_platform_is_rejected_before_subprocesses" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:200"/>
<f n="test_native_arm64_is_rejected_for_windows_x64_role" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:240"/>
</group>
<group type="3" gid="194" tokens="54" n="2" similarity="0.89">
<f n="test_non_windows_platform_is_rejected_before_subprocesses" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:200"/>
<f n="test_mutable_spec_kit_ref_is_rejected_before_subprocesses" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:269"/>
</group>
<group type="3" gid="194" tokens="66" n="2" similarity="0.83">
<f n="test_non_windows_platform_is_rejected_before_subprocesses" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:200"/>
<f n="test_draft_pull_request_defers_heavy_preflight_without_git_diff" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:509"/>
</group>
<group type="3" gid="194" tokens="54" n="2" similarity="0.87">
<f n="test_non_windows_platform_is_rejected_before_subprocesses" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:200"/>
<f n="test_rename_out_of_preflight_surface_still_runs_heavy_jobs" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:521"/>
</group>
<group type="3" gid="194" tokens="54" n="2" similarity="0.82">
<f n="test_non_windows_platform_is_rejected_before_subprocesses" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:200"/>
<f n="test_deletion_only_on_preflight_surface_still_runs_heavy_jobs" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:530"/>
</group>
<group type="3" gid="194" tokens="76" n="2" similarity="0.87">
<f n="test_native_arm64_matches_windows_arm64_role" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:210"/>
<f n="test_native_arm64_is_rejected_for_windows_x64_role" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:240"/>
</group>
<group type="3" gid="194" tokens="64" n="2" similarity="0.82">
<f n="test_native_arm64_matches_windows_arm64_role" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:210"/>
<f n="test_malformed_runner_json_fails_closed" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:252"/>
</group>
<group type="3" gid="194" tokens="66" n="2" similarity="0.83">
<f n="test_native_arm64_matches_windows_arm64_role" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:210"/>
<f n="test_draft_pull_request_defers_heavy_preflight_without_git_diff" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:509"/>
</group>
<group type="3" gid="194" tokens="64" n="2" similarity="0.84">
<f n="test_native_arm64_matches_windows_arm64_role" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:210"/>
<f n="test_rename_out_of_preflight_surface_still_runs_heavy_jobs" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:521"/>
</group>
<group type="3" gid="194" tokens="76" n="2" similarity="0.83">
<f n="test_native_arm64_is_rejected_for_windows_x64_role" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:240"/>
<f n="test_missing_preflight_metadata_fails_with_valid_ok_envelope" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:390"/>
</group>
<group type="3" gid="194" tokens="76" n="2" similarity="0.86">
<f n="test_native_arm64_is_rejected_for_windows_x64_role" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:240"/>
<f n="test_draft_pull_request_defers_heavy_preflight_without_git_diff" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:509"/>
</group>
<group type="3" gid="194" tokens="61" n="2" similarity="0.90">
<f n="test_malformed_runner_json_fails_closed" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:252"/>
<f n="test_longer_version_does_not_match_expected_version_by_substring" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:261"/>
</group>
<group type="3" gid="194" tokens="61" n="2" similarity="0.86">
<f n="test_malformed_runner_json_fails_closed" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:252"/>
<f n="test_subprocess_failure_fails_closed" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:278"/>
</group>
<group type="3" gid="194" tokens="78" n="2" similarity="0.86">
<f n="test_malformed_runner_json_fails_closed" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:252"/>
<f n="test_pipx_probe_timeout_does_not_fall_back_to_bootstrap" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:356"/>
</group>
<group type="3" gid="194" tokens="68" n="2" similarity="0.90">
<f n="test_malformed_runner_json_fails_closed" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:252"/>
<f n="test_non_ok_response_status_fails_even_with_zero_process_exit" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:366"/>
</group>
<group type="3" gid="194" tokens="82" n="2" similarity="0.85">
<f n="test_malformed_runner_json_fails_closed" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:252"/>
<f n="test_unverified_preflight_metadata_fails_with_valid_ok_envelope" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:377"/>
</group>
<group type="3" gid="194" tokens="74" n="2" similarity="0.89">
<f n="test_malformed_runner_json_fails_closed" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:252"/>
<f n="test_missing_preflight_metadata_fails_with_valid_ok_envelope" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:390"/>
</group>
<group type="3" gid="194" tokens="61" n="2" similarity="0.81">
<f n="test_malformed_runner_json_fails_closed" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:252"/>
<f n="test_structurally_invalid_response_envelope_fails_closed" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:400"/>
</group>
<group type="3" gid="194" tokens="61" n="2" similarity="0.83">
<f n="test_malformed_runner_json_fails_closed" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:252"/>
<f n="test_rename_out_of_preflight_surface_still_runs_heavy_jobs" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:521"/>
</group>
<group type="3" gid="194" tokens="55" n="2" similarity="0.91">
<f n="test_longer_version_does_not_match_expected_version_by_substring" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:261"/>
<f n="test_subprocess_failure_fails_closed" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:278"/>
</group>
<group type="3" gid="194" tokens="68" n="2" similarity="0.85">
<f n="test_longer_version_does_not_match_expected_version_by_substring" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:261"/>
<f n="test_non_ok_response_status_fails_even_with_zero_process_exit" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:366"/>
</group>
<group type="3" gid="194" tokens="60" n="2" similarity="0.85">
<f n="test_longer_version_does_not_match_expected_version_by_substring" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:261"/>
<f n="test_structurally_invalid_response_envelope_fails_closed" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:400"/>
</group>
<group type="3" gid="194" tokens="50" n="2" similarity="0.81">
<f n="test_longer_version_does_not_match_expected_version_by_substring" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:261"/>
<f n="test_deletion_only_on_preflight_surface_still_runs_heavy_jobs" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:530"/>
</group>
<group type="3" gid="194" tokens="43" n="2" similarity="0.83">
<f n="test_mutable_spec_kit_ref_is_rejected_before_subprocesses" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:269"/>
<f n="test_deletion_only_on_preflight_surface_still_runs_heavy_jobs" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:530"/>
</group>
<group type="3" gid="194" tokens="68" n="2" similarity="0.81">
<f n="test_subprocess_failure_fails_closed" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:278"/>
<f n="test_non_ok_response_status_fails_even_with_zero_process_exit" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:366"/>
</group>
<group type="3" gid="194" tokens="60" n="2" similarity="0.89">
<f n="test_subprocess_failure_fails_closed" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:278"/>
<f n="test_structurally_invalid_response_envelope_fails_closed" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:400"/>
</group>
<group type="3" gid="194" tokens="78" n="2" similarity="0.85">
<f n="test_pipx_probe_timeout_does_not_fall_back_to_bootstrap" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:356"/>
<f n="test_non_ok_response_status_fails_even_with_zero_process_exit" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:366"/>
</group>
<group type="3" gid="194" tokens="82" n="2" similarity="0.86">
<f n="test_pipx_probe_timeout_does_not_fall_back_to_bootstrap" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:356"/>
<f n="test_unverified_preflight_metadata_fails_with_valid_ok_envelope" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:377"/>
</group>
<group type="3" gid="194" tokens="78" n="2" similarity="0.89">
<f n="test_pipx_probe_timeout_does_not_fall_back_to_bootstrap" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:356"/>
<f n="test_missing_preflight_metadata_fails_with_valid_ok_envelope" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:390"/>
</group>
<group type="3" gid="194" tokens="82" n="2" similarity="0.87">
<f n="test_non_ok_response_status_fails_even_with_zero_process_exit" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:366"/>
<f n="test_unverified_preflight_metadata_fails_with_valid_ok_envelope" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:377"/>
</group>
<group type="3" gid="194" tokens="74" n="2" similarity="0.87">
<f n="test_non_ok_response_status_fails_even_with_zero_process_exit" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:366"/>
<f n="test_missing_preflight_metadata_fails_with_valid_ok_envelope" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:390"/>
</group>
<group type="3" gid="194" tokens="68" n="2" similarity="0.81">
<f n="test_non_ok_response_status_fails_even_with_zero_process_exit" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:366"/>
<f n="test_structurally_invalid_response_envelope_fails_closed" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:400"/>
</group>
<group type="3" gid="194" tokens="68" n="2" similarity="0.80">
<f n="test_non_ok_response_status_fails_even_with_zero_process_exit" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:366"/>
<f n="test_rename_out_of_preflight_surface_still_runs_heavy_jobs" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:521"/>
</group>
<group type="3" gid="194" tokens="82" n="2" similarity="0.95">
<f n="test_unverified_preflight_metadata_fails_with_valid_ok_envelope" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:377"/>
<f n="test_missing_preflight_metadata_fails_with_valid_ok_envelope" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:390"/>
</group>
<group type="3" gid="251" tokens="224" n="2" similarity="0.82">
<f n="test_manual_change_detection_always_selects_heavy_preflight" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:457"/>
<f n="test_windows_availability_preserves_defaults_and_authoritative_disables" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:547"/>
</group>
<group type="3" gid="251" tokens="191" n="2" similarity="0.80">
<f n="test_manual_change_detection_always_selects_heavy_preflight" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:457"/>
<f n="test_required_sentinel_writes_stable_verdict_evidence" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:604"/>
</group>
<group type="3" gid="251" tokens="218" n="2" similarity="0.82">
<f n="test_manual_change_detection_always_selects_heavy_preflight" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:457"/>
<f n="test_windows_smoke_fails_closed_when_no_direct_interpreter_is_available" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:846"/>
</group>
<group type="3" gid="194" tokens="66" n="2" similarity="0.86">
<f n="test_draft_pull_request_defers_heavy_preflight_without_git_diff" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:509"/>
<f n="test_rename_out_of_preflight_surface_still_runs_heavy_jobs" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:521"/>
</group>
<group type="3" gid="194" tokens="52" n="2" similarity="0.88">
<f n="test_rename_out_of_preflight_surface_still_runs_heavy_jobs" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:521"/>
<f n="test_deletion_only_on_preflight_surface_still_runs_heavy_jobs" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:530"/>
</group>
<group type="3" gid="20" tokens="63" n="2" similarity="0.86">
<f n="load_gate_tests" p="tests/speckit-pro/unit/test-installed-release-gates.py:21"/>
<f n="load_script_module" p="tests/speckit-pro/unit/test-integration-runners.py:49"/>
</group>
<group type="3" gid="20" tokens="64" n="2" similarity="0.83">
<f n="load_gate_tests" p="tests/speckit-pro/unit/test-installed-release-gates.py:21"/>
<f n="load_script" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:32"/>
</group>
<group type="3" gid="20" tokens="63" n="2" similarity="0.80">
<f n="load_gate_tests" p="tests/speckit-pro/unit/test-installed-release-gates.py:21"/>
<f n="load_module" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:25"/>
</group>
<group type="3" gid="20" tokens="64" n="2" similarity="0.87">
<f n="load_script_module" p="tests/speckit-pro/unit/test-integration-runners.py:49"/>
<f n="load_script" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:32"/>
</group>
<group type="3" gid="20" tokens="57" n="2" similarity="0.92">
<f n="load_script_module" p="tests/speckit-pro/unit/test-integration-runners.py:49"/>
<f n="load_module" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:25"/>
</group>
<group type="3" gid="258" tokens="51" n="2" similarity="0.82">
<f n="setUp" p="tests/speckit-pro/unit/test-native-eval-adapters.py:394"/>
<f n="setUp" p="tests/speckit-pro/unit/test-refresh-local-plugin.py:75"/>
</group>
<group type="3" gid="202" tokens="65" n="2" similarity="0.90">
<f n="run_cli" p="tests/speckit-pro/unit/test-parity-judge.py:52"/>
<f n="run_sync" p="tests/speckit-pro/unit/test-sync-marketplace-versions.py:24"/>
</group>
<group type="3" gid="20" tokens="64" n="2" similarity="0.94">
<f n="load_script" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:32"/>
<f n="load_module" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:25"/>
</group>
<group type="3" gid="20" tokens="64" n="2" similarity="0.93">
<f n="load_script" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:32"/>
<f n="import_script" p="tests/speckit-pro/unit/test-trigger-eval-runners.py:57"/>
</group>
<group type="3" gid="167" tokens="59" n="2" similarity="0.85">
<f n="test_full_mode_for_rendered_docs" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:213"/>
<f n="test_reference_mode_for_generated_reference_source" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:242"/>
</group>
<group type="3" gid="167" tokens="55" n="2" similarity="0.89">
<f n="test_full_mode_for_rendered_docs" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:213"/>
<f n="test_path_boundaries_do_not_match_prefix_lookalikes" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:269"/>
</group>
<group type="3" gid="309" tokens="45" n="2" similarity="0.96">
<f n="test_detect_failure_and_cancellation_fail_first" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:352"/>
<f n="test_test_failure_and_cancellation_fail" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:361"/>
</group>
<group type="3" gid="309" tokens="45" n="2" similarity="0.96">
<f n="test_detect_failure_and_cancellation_fail_first" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:352"/>
<f n="test_artifact_failure_and_cancellation_fail" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:370"/>
</group>
<group type="3" gid="309" tokens="47" n="2" similarity="0.93">
<f n="test_detect_failure_and_cancellation_fail_first" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:352"/>
<f n="test_go_failure_cancellation_and_missing_result_fail" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:379"/>
</group>
<group type="3" gid="309" tokens="45" n="2" similarity="0.96">
<f n="test_test_failure_and_cancellation_fail" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:361"/>
<f n="test_artifact_failure_and_cancellation_fail" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:370"/>
</group>
<group type="3" gid="309" tokens="47" n="2" similarity="0.93">
<f n="test_test_failure_and_cancellation_fail" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:361"/>
<f n="test_go_failure_cancellation_and_missing_result_fail" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:379"/>
</group>
<group type="3" gid="309" tokens="47" n="2" similarity="0.93">
<f n="test_artifact_failure_and_cancellation_fail" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:370"/>
<f n="test_go_failure_cancellation_and_missing_result_fail" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:379"/>
</group>
<group type="3" gid="310" tokens="79" n="2" similarity="0.92">
<f n="test_main_emits_exact_github_error_message" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:392"/>
<f n="test_missing_base_ref_fails" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:511"/>
</group>
<group type="3" gid="311" tokens="45" n="2" similarity="0.92">
<f n="test_module_wrapper_and_workflow_changes_run_go" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:476"/>
<f n="test_other_changes_skip_go" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:486"/>
</group>
<group type="3" gid="318" tokens="77" n="2" similarity="0.92">
<f n="test_sanitization_strips_html_images_and_neutralizes_structure" p="tests/speckit-pro/unit/test-release-note-policy.py:109"/>
<f n="test_sanitization_entities_and_transform_order_cannot_recreate_markup" p="tests/speckit-pro/unit/test-release-note-policy.py:246"/>
</group>
<group type="3" gid="20" tokens="59" n="2" similarity="0.98">
<f n="load_module" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:25"/>
<f n="import_script" p="tests/speckit-pro/unit/test-trigger-eval-runners.py:57"/>
</group>
<group type="3" gid="319" tokens="64" n="2" similarity="0.81">
<f n="test_conflict_outside_regenerated_artifacts_fails_the_sync" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:198"/>
<f n="test_merge_failure_without_a_conflicted_path_keeps_the_git_diagnostic" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:213"/>
</group>
<group type="3" gid="319" tokens="80" n="2" similarity="0.86">
<f n="test_conflict_outside_regenerated_artifacts_fails_the_sync" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:198"/>
<f n="test_manifest_conflict_beside_an_unmanaged_one_still_fails" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:325"/>
</group>
<group type="3" gid="320" tokens="158" n="2" similarity="0.85">
<f n="test_dispatch_stops_and_reports_child_failure_with_parent_status" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:402"/>
<f n="test_dispatch_reports_which_workflow_failed" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:426"/>
</group>
<group type="3" gid="321" tokens="96" n="2" similarity="0.87">
<f n="api" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:494"/>
<f n="fake" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:497"/>
</group>
<group type="3" gid="322" tokens="152" n="2" similarity="0.93">
<f n="test_runner_requests_stop_on_first_failure" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:789"/>
<f n="test_runner_requests_normalize_signal_status_and_stop" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:812"/>
</group>
<group type="3" gid="323" tokens="56" n="2" similarity="0.87">
<f n="fake_run" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:1207"/>
<f n="failing_run" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:1393"/>
</group>
<group type="3" gid="324" tokens="173" n="2" similarity="0.82">
<f n="test_check_mode_reports_executable_mode_drift" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:1315"/>
<f n="test_check_mode_never_mutates_tracked_or_untracked_source_files" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:1414"/>
</group>
<group type="3" gid="323" tokens="63" n="2" similarity="0.95">
<f n="mode_drift_run" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:1321"/>
<f n="fake_run" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:1353"/>
</group>
<group type="3" gid="323" tokens="59" n="2" similarity="0.84">
<f n="mode_drift_run" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:1321"/>
<f n="failing_run" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:1393"/>
</group>
<group type="3" gid="323" tokens="75" n="2" similarity="0.85">
<f n="mode_drift_run" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:1321"/>
<f n="mutating_isolated_run" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:1421"/>
</group>
<group type="3" gid="323" tokens="75" n="2" similarity="0.90">
<f n="fake_run" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:1353"/>
<f n="mutating_isolated_run" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:1421"/>
</group>
<group type="3" gid="165" tokens="48" n="2" similarity="0.84">
<f n="write_route_policy_manifest" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:705"/>
<f n="create_marketplace" p="tests/speckit-pro/unit/test-sync-marketplace-versions.py:40"/>
</group>
<group type="3" gid="165" tokens="48" n="2" similarity="0.83">
<f n="write_route_policy_manifest" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:705"/>
<f n="create_codex_marketplace" p="tests/speckit-pro/unit/test-sync-marketplace-versions.py:46"/>
</group>
<group type="3" gid="202" tokens="72" n="2" similarity="0.86">
<f n="run_sync" p="tests/speckit-pro/unit/test-sync-marketplace-versions.py:24"/>
<f n="run_script" p="tests/speckit-pro/unit/test-transcript-tools.py:29"/>
</group>
<group type="3" gid="165" tokens="44" n="2" similarity="0.98">
<f n="create_marketplace" p="tests/speckit-pro/unit/test-sync-marketplace-versions.py:40"/>
<f n="create_codex_marketplace" p="tests/speckit-pro/unit/test-sync-marketplace-versions.py:46"/>
</group>
<group type="3" gid="165" tokens="56" n="2" similarity="0.80">
<f n="create_codex_marketplace" p="tests/speckit-pro/unit/test-sync-marketplace-versions.py:46"/>
<f n="create_codex_plugin" p="tests/speckit-pro/unit/test-sync-marketplace-versions.py:61"/>
</group>
```

## churn-decay (15 lines)

```xml
<recent n="40" of="1331" merge_bombs_skipped="5">
<rc p="speckit-pro/.codex-plugin/plugin.json" age_d="0" w="50.9"/>
<rc p="speckit-pro/CHANGELOG.md" age_d="0" w="49.9"/>
</recent>
<f p="tests/speckit-pro/unit/test-release-pr-reconciliation.py" layer="test">
</f>
<f p="scripts/build-typesafe-jev-release.py">
</f>
<f p="docs-site/src/content/docs/reference/tests.md">
<s t="sec" n="tests/speckit-pro/run-hosted-windows-preflight.py" sc="Records" k="0.0003">
<s t="sec" n="tests/speckit-pro/run-container-preflight.py" sc="Records" k="0.0003">
<s t="sec" n="tests/speckit-pro/check-toolchain.py" sc="Records" k="0.0003">
</f>
<f p="speckit-pro/speckit_pro_runner/gates/payloads.py">
</f>
```

## arch (0 lines)

```xml

```

## deps (0 lines)

```xml

```
