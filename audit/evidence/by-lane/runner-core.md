# Evidence for lane `runner-core` (94 files)
Lines from the whole-repo scans that mention this lane's files. Empty section = none found, not none exists.

## doc-drift (65 lines)

```xml
<doc p="docs/ai/research/tool-agnostic-capability-discovery-spike.md" anchors="51" checked="18" drift="16" dated="0">
</doc>
<doc p="docs/ai/specs/.process/ART-003-workflow.md" anchors="45" checked="15" drift="7" dated="0">
<a k="file-line" l="1053" c="3" why="range-straddles" ref="speckit_pro_runner/helpers/read_only.py:906-914" got="(file scope)" tgt="speckit-pro/speckit_pro_runner/helpers/read_only.py:914"/>
</doc>
<doc p="docs/ai/specs/html-artifacts-technical-roadmap.md" anchors="46" checked="23" drift="3" dated="0">
<a k="file-line" l="1092" c="3" why="range-straddles" ref="speckit-pro/speckit_pro_runner/helpers/read_only.py:1063-1090" got="scaffold_placement_payload" tgt="speckit-pro/speckit_pro_runner/helpers/read_only.py:1090"/>
<a k="file-line" l="1324" c="69" why="line-moved" ref="read_only.py:8306" sym="count_done_tasks" got="trusted_file_exists" tgt="speckit-pro/speckit_pro_runner/helpers/read_only.py:8806"/>
</doc>
<doc p="docs/ai/specs/.process/ART-006-workflow.md" anchors="21" checked="6" drift="1" dated="0">
<a k="file-line" l="788" c="64" why="line-moved" ref="read_only.py:3939-3940" sym="is_production_file" got="sweep_redact" tgt="speckit-pro/speckit_pro_runner/helpers/read_only.py:8858"/>
</doc>
<doc p="tests/speckit-pro/layer6-integration/performance-fixtures/draft-pr-emission/source/contracts/draft-packet-mode.md" anchors="53" checked="37" drift="1" dated="0">
<a k="file-line" l="85" c="2" why="range-straddles" ref="speckit-pro/speckit_pro_runner/helpers/read_only.py:2669-2671" got="(file scope)" tgt="speckit-pro/speckit_pro_runner/helpers/read_only.py:2671"/>
</doc>
<doc p="docs/ai/specs/.process/ART-007-workflow.md" anchors="72" checked="38" drift="0" dated="1">
<a k="file-line" l="947" c="26" why="range-straddles" kind="dated-record" rec="block" ref="read_only.py:2669-2671" got="(file scope)" tgt="speckit-pro/speckit_pro_runner/helpers/read_only.py:2671"/>
</doc>
<doc p="docs/ai/specs/gate-tooling-decision.md" anchors="20" checked="10" drift="0" dated="1">
</doc>
<doc p="tests/speckit-pro/layer6-integration/performance-fixtures/draft-pr-emission/source/plan.md" anchors="5" checked="3" drift="0" dated="1">
<a k="file-line" l="132" c="11" why="range-straddles" kind="dated-record" rec="stamp" ref="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:424-441" got="routing_required_agents" tgt="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:441"/>
</doc>
<doc p="tests/speckit-pro/layer6-integration/performance-fixtures/draft-pr-emission/source/research.md" anchors="84" checked="44" drift="0" dated="17">
<a k="file-line" l="232" c="50" why="line-moved" kind="dated-record" rec="stamp" ref="read_only.py:1196-1209" sym="workflow_table_rows" got="resolve_scaffold_worktree_placement" tgt="speckit-pro/speckit_pro_runner/helpers/read_only.py:2705"/>
<a k="file-line" l="275" c="3" why="range-straddles" kind="dated-record" rec="stamp" ref="speckit-pro/speckit_pro_runner/envelope.py:78-91" got="(file scope)" tgt="speckit-pro/speckit_pro_runner/envelope.py:91"/>
<a k="file-line" l="343" c="6" why="range-straddles" kind="dated-record" rec="stamp" ref="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:901-926" got="test_resolve_workflow_binding_covers_registered_worktree_relations" tgt="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:926"/>
</doc>
<weak-file-line p=".specify/memory/archive-reports/2026-08-14-art-003-gap-triage-amendment.md" n="1">
<w l="120" c="3" ref="speckit-pro/speckit_pro_runner/helpers/read_only.py:4143" resolves-to="sweep_redact_outbound"/>
</weak-file-line>
<weak-file-line p=".specify/memory/archive-reports/2026-08-18-art-007-post-merge-hygiene.md" n="2">
<w l="228" c="4" ref="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:35" resolves-to="AUTOPILOT_STAGE_WORKFLOW_FILE"/>
</weak-file-line>
<weak-file-line p="docs/ai/research/tool-agnostic-capability-discovery-spike.md" n="9">
</weak-file-line>
<weak-file-line p="docs/ai/specs/.process/ART-006-workflow.md" n="2">
<w l="933" c="19" ref="speckit-pro/speckit_pro_runner/helpers/read_only.py:961" resolves-to="resolve_workflow_binding"/>
</weak-file-line>
<weak-file-line p="docs/ai/specs/.process/ART-007-workflow.md" n="1">
<w l="919" c="3" ref="speckit-pro/speckit_pro_runner/helpers/read_only.py:2369-2378" resolves-to="g5_gate_task_loops"/>
</weak-file-line>
<weak-file-line p="docs/ai/specs/html-artifacts-technical-roadmap.md" n="5">
<w l="1605" c="21" ref="tests/speckit-pro/unit/test-architecture-graph.py:95-100" resolves-to="test_architecture_graph_contract"/>
</weak-file-line>
<weak-file-line p="tests/speckit-pro/evals/audit/unit-remaining-support-audit.md" n="9">
<w l="29" c="257" ref="tests/speckit-pro/unit/test-speckit-pro-runner.py:292" resolves-to="test_manifest_and_checksum_cover_runner_sources"/>
<w l="29" c="404" ref="tests/speckit-pro/unit/test-speckit-pro-gates.py:430" resolves-to="test_public_result_schema_validation_enforces_owned_assertion_keywords"/>
<w l="29" c="460" ref="tests/speckit-pro/unit/test-speckit-pro-gates.py:1966" resolves-to="test_plugin_bash_confinement_zero_bash_guard_blocks_physical_uppercase_script_files"/>
<w l="29" c="517" ref="tests/speckit-pro/unit/test-speckit-pro-gates.py:2009" resolves-to="test_plugin_bash_confinement_zero_bash_guard_blocks_physical_uppercase_script_files"/>
<w l="29" c="574" ref="tests/speckit-pro/unit/test-speckit-pro-gates.py:2080" resolves-to="test_installed_release_payload_completeness_blocks_seeded_negative_cases"/>
<w l="29" c="635" ref="tests/speckit-pro/unit/test-speckit-pro-gates.py:2136" resolves-to="test_installed_release_payload_completeness_apply_builds_runner_payloads_without_shell"/>
<w l="35" c="361" ref="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2795" resolves-to="packet_failure_rules"/>
<w l="35" c="481" ref="tests/speckit-pro/unit/test-speckit-pro-gates.py:1544" resolves-to="test_installed_release_active_runtime_guard_fixtures_block_only_active_runtime_findings"/>
<w l="39" c="92" ref="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3110" resolves-to="test_validate_pr_workflow_contract_unreadable_changed_files_is_input_error"/>
</weak-file-line>
<weak-file-line p="tests/speckit-pro/layer6-integration/performance-fixtures/draft-pr-emission/source/contracts/draft-packet-mode.md" n="1">
<w l="46" c="2" ref="speckit-pro/speckit_pro_runner/helpers/read_only.py:2369-2378" resolves-to="g5_gate_task_loops"/>
</weak-file-line>
<weak-file-line p="tests/speckit-pro/layer6-integration/performance-fixtures/draft-pr-emission/source/research.md" n="14">
<w l="44" c="2" ref="speckit-pro/speckit_pro_runner/helpers/read_only.py:2374-2378" resolves-to="g5_gate_task_loops"/>
<w l="68" c="3" ref="speckit-pro/speckit_pro_runner/helpers/read_only.py:2872-2875" resolves-to="observation_pull_requests"/>
<w l="222" c="3" ref="speckit-pro/speckit_pro_runner/helpers/read_only.py:1258-1263" resolves-to="resolve_scaffold_worktree_placement"/>
<w l="500" c="3" ref="speckit-pro/speckit_pro_runner/helpers/read_only.py:4185-4186" resolves-to="sweep_fence_marks"/>
</weak-file-line>
```

## clones (1379 lines)

```xml
<group type="2" gid="44" tokens="190" n="2">
<f n="python_static_command_assignments" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:3413"/>
<f n="python_static_bool_assignments" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:3434"/>
</group>
<group type="2" gid="41" tokens="171" n="2">
<f n="repo_bash_which_aliases" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:2818"/>
<f n="repo_bash_sys_aliases" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:2836"/>
</group>
<group type="2" gid="26" tokens="145" n="2">
<f n="_json_schema_type_matches" p="speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:1406"/>
<f n="json_schema_type_matches" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:7016"/>
</group>
<group type="2" gid="333" tokens="127" n="3">
<f n="run_runner" p="tests/speckit-pro/unit/test-speckit-pro-gates.py:85"/>
<f n="run_runner" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:395"/>
<f n="run_runner" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:271"/>
</group>
<group type="2" gid="177" tokens="80" n="2">
<f n="_runner" p="tests/speckit-pro/unit/test-finalize-run.py:389"/>
<f n="_runner" p="tests/speckit-pro/unit/test-gate-preflight-coverage.py:47"/>
</group>
<group type="2" gid="47" tokens="77" n="2">
<f n="latest_partial_static_assignment" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:3666"/>
<f n="latest_static_assignment" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:3682"/>
</group>
<group type="2" gid="25" tokens="73" n="2">
<f n="_json_values_equal" p="speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:1398"/>
<f n="json_values_equal" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:7030"/>
</group>
<group type="2" gid="178" tokens="64" n="3">
<f n="assert_response" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:613"/>
<f n="assert_response" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:595"/>
<f n="assert_response" p="tests/speckit-pro/unit/test-speckit-pro-runner.py:144"/>
</group>
<group type="2" gid="50" tokens="63" n="2">
<f n="classify_raw_finding" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:4380"/>
<f n="classify_installed_runtime_raw_finding" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:4403"/>
</group>
<group type="2" gid="77" tokens="62" n="2">
<f n="sweep_pr_feedback" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:3570"/>
<f n="check_artifact_freshness" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:4588"/>
</group>
<group type="2" gid="53" tokens="58" n="2">
<f n="remediation_for" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:4951"/>
<f n="installed_runtime_remediation_for" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:4969"/>
</group>
<group type="2" gid="45" tokens="56" n="3">
<f n="is_os_system_call" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:3509"/>
<f n="is_shell_backed_subprocess_call" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:3523"/>
<f n="is_subprocess_call" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:3537"/>
</group>
<group type="2" gid="337" tokens="56" n="2">
<f n="command_stdin_fixture" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:419"/>
<f n="command_stdin_fixture" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:304"/>
</group>
<group type="2" gid="58" tokens="54" n="2">
<f n="emit_checks" p="speckit-pro/speckit_pro_runner/gates/suite.py:495"/>
<f n="emit_checks" p="tests/speckit-pro/run-layer-scripts.py:99"/>
</group>
<group type="2" gid="347" tokens="53" n="2">
<f n="move_after_copy_open" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3974"/>
<f n="move_after_copy_open" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5810"/>
</group>
<group type="2" gid="17" tokens="47" n="2">
<f n="sha256_file" p="scripts/refresh-release-artifacts.py:368"/>
<f n="sha256_file" p="speckit-pro/speckit_pro_runner/path_utils.py:28"/>
</group>
<group type="2" gid="72" tokens="47" n="2">
<f n="malformed_inventory" p="speckit-pro/speckit_pro_runner/helpers/install.py:5676"/>
<f n="invalid_operation" p="speckit-pro/speckit_pro_runner/helpers/mutation.py:1234"/>
</group>
<group type="3" gid="23" tokens="129" n="2" similarity="0.82">
<f n="_pending_value_paths" p="speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:1003"/>
<f n="iter_input_strings" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:8750"/>
</group>
<group type="3" gid="27" tokens="79" n="2" similarity="0.95">
<f n="_resolve_schema_reference" p="speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:1423"/>
<f n="resolve_local_schema_reference" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:7004"/>
</group>
<group type="3" gid="31" tokens="108" n="2" similarity="0.90">
<f n="main" p="speckit-pro/speckit_pro_runner/architecture_graph.py:161"/>
<f n="main" p="speckit-pro/speckit_pro_runner/gate_discovery.py:267"/>
</group>
<group type="3" gid="39" tokens="51" n="2" similarity="0.86">
<f n="repo_bash_instruction_finding" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:1157"/>
<f n="repo_bash_workflow_finding" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:2071"/>
</group>
<group type="3" gid="40" tokens="53" n="2" similarity="0.86">
<f n="add" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:2239"/>
<f n="add_event" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:2359"/>
</group>
<group type="3" gid="42" tokens="65" n="2" similarity="0.94">
<f n="repo_bash_command_source_call" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:2900"/>
<f n="repo_bash_trusted_which_call" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:2912"/>
</group>
<group type="3" gid="43" tokens="229" n="2" similarity="0.94">
<f n="repo_bash_env_argv_contains_forbidden" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:2980"/>
<f n="partial_env_delegation_contains_forbidden" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:3838"/>
</group>
<group type="3" gid="43" tokens="216" n="2" similarity="0.80">
<f n="repo_bash_env_argv_contains_forbidden" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:2980"/>
<f n="env_delegated_argvs" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:3871"/>
</group>
<group type="3" gid="44" tokens="198" n="2" similarity="0.98">
<f n="python_static_command_assignments" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:3413"/>
<f n="python_partial_command_assignments" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:3455"/>
</group>
<group type="3" gid="46" tokens="48" n="2" similarity="0.96">
<f n="static_subprocess_arg_value" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:3646"/>
<f n="partial_static_subprocess_argv" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:3654"/>
</group>
<group type="3" gid="48" tokens="220" n="2" similarity="0.91">
<f n="guard_response" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:4156"/>
<f n="active_runtime_guard_response" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:4186"/>
</group>
<group type="3" gid="49" tokens="399" n="2" similarity="0.96">
<f n="scan_sources" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:4254"/>
<f n="scan_installed_runtime_sources" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:4302"/>
</group>
<group type="3" gid="51" tokens="169" n="2" similarity="0.83">
<f n="installed_runtime_source_checkout_helper_reference" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:4667"/>
<f n="installed_runtime_baseline_source_checkout_helper_reference" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:4886"/>
</group>
<group type="3" gid="52" tokens="61" n="2" similarity="0.80">
<f n="installed_runtime_changed_source_checkout_helper_reference" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:4740"/>
<f n="installed_runtime_generated_payload_helper_reference" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:4749"/>
</group>
<group type="3" gid="54" tokens="68" n="2" similarity="0.84">
<f n="git_ref_exists" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:5255"/>
<f n="git_stdout" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:5271"/>
</group>
<group type="3" gid="55" tokens="252" n="2" similarity="0.93">
<f n="load_case" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:5383"/>
<f n="runner_invocation_case" p="speckit-pro/speckit_pro_runner/helpers/install.py:5010"/>
</group>
<group type="3" gid="56" tokens="75" n="2" similarity="0.99">
<f n="base_data" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:5406"/>
<f n="active_runtime_base_data" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:5421"/>
</group>
<group type="3" gid="56" tokens="98" n="2" similarity="0.83">
<f n="active_runtime_base_data" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:5421"/>
<f n="runner_invocation_base_data" p="speckit-pro/speckit_pro_runner/helpers/install.py:5563"/>
</group>
<group type="3" gid="56" tokens="98" n="2" similarity="0.86">
<f n="gate_base_data" p="speckit-pro/speckit_pro_runner/gates/gate_response.py:8"/>
<f n="runner_invocation_base_data" p="speckit-pro/speckit_pro_runner/helpers/install.py:5563"/>
</group>
<group type="3" gid="59" tokens="65" n="2" similarity="0.84">
<f n="command_result" p="speckit-pro/speckit_pro_runner/gates/suite.py:522"/>
<f n="_spec_index_write_data" p="speckit-pro/speckit_pro_runner/helpers/mutation.py:746"/>
</group>
<group type="3" gid="62" tokens="155" n="2" similarity="0.92">
<f n="run_gate_preflight_coverage_helper" p="speckit-pro/speckit_pro_runner/helpers/gate_preflight_coverage.py:128"/>
<f n="run_run_finalization_helper" p="speckit-pro/speckit_pro_runner/helpers/run_finalization.py:279"/>
</group>
<group type="3" gid="69" tokens="57" n="2" similarity="0.80">
<f n="codex_agent_destination_identity" p="speckit-pro/speckit_pro_runner/helpers/install.py:4224"/>
<f n="current_file_mode_fd" p="speckit-pro/speckit_pro_runner/helpers/mutation.py:1742"/>
</group>
<group type="3" gid="70" tokens="62" n="2" similarity="0.96">
<f n="parse_version" p="speckit-pro/speckit_pro_runner/helpers/install.py:5546"/>
<f n="parse_version_tuple" p="speckit-pro/speckit_pro_runner/runtime.py:183"/>
</group>
<group type="3" gid="72" tokens="47" n="2" similarity="0.87">
<f n="malformed_inventory" p="speckit-pro/speckit_pro_runner/helpers/install.py:5676"/>
<f n="source_fingerprint_changed" p="speckit-pro/speckit_pro_runner/helpers/mutation.py:1990"/>
</group>
<group type="3" gid="75" tokens="73" n="2" similarity="0.84">
<f n="registry_report" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:98"/>
<f n="mutation_registry_report" p="speckit-pro/speckit_pro_runner/helpers/registry.py:648"/>
</group>
<group type="3" gid="76" tokens="61" n="2" similarity="0.97">
<f n="sweep_cut_utf8" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:3396"/>
<f n="_bounded_comment_body" p="speckit-pro/speckit_pro_runner/sweep_isolation.py:428"/>
</group>
<group type="3" gid="78" tokens="192" n="2" similarity="0.91">
<f n="_spec_index_walk_regular_files" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:5543"/>
<f n="visit" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:5546"/>
</group>
<group type="3" gid="79" tokens="67" n="2" similarity="0.88">
<f n="_spec_index_repo_structure_current" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:5615"/>
<f n="_spec_index_active_feature" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:5627"/>
</group>
<group type="3" gid="80" tokens="96" n="2" similarity="0.90">
<f n="trusted_bytes_descriptor" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:8446"/>
<f n="trusted_regular_file_bytes_and_mode" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:8468"/>
</group>
<group type="3" gid="81" tokens="318" n="2" similarity="0.86">
<f n="trusted_open_regular_file" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:8491"/>
<f n="trusted_open_directory" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:8544"/>
</group>
<group type="3" gid="82" tokens="131" n="2" similarity="0.82">
<f n="git_is_worktree" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:8645"/>
<f n="git_diff_changed_paths" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:8718"/>
</group>
<group type="3" gid="165" tokens="48" n="2" similarity="0.80">
<f n="_write_json" p="tests/speckit-pro/run-hosted-windows-preflight.py:55"/>
<f n="write_route_policy_manifest" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:705"/>
</group>
<group type="3" gid="20" tokens="51" n="2" similarity="0.89">
<f n="_load_run_all" p="tests/speckit-pro/test-run-all.py:34"/>
<f n="load_layer_script_dispatcher" p="tests/speckit-pro/unit/test-speckit-pro-gates.py:206"/>
</group>
<group type="3" gid="178" tokens="67" n="2" similarity="0.82">
<f n="test_valid_pending_record_is_not_a_validation_failure" p="tests/speckit-pro/unit/test-artifact-review.py:108"/>
<f n="assert_response" p="tests/speckit-pro/unit/test-speckit-pro-gates.py:240"/>
</group>
<group type="3" gid="178" tokens="64" n="2" similarity="0.84">
<f n="test_valid_pending_record_is_not_a_validation_failure" p="tests/speckit-pro/unit/test-artifact-review.py:108"/>
<f n="assert_response" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:613"/>
</group>
<group type="3" gid="197" tokens="42" n="2" similarity="0.90">
<f n="runner_env" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1030"/>
<f n="runner_env" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:243"/>
</group>
<group type="3" gid="20" tokens="45" n="2" similarity="0.81">
<f n="load_coverage_validator" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1061"/>
<f n="load_layer_script_dispatcher" p="tests/speckit-pro/unit/test-speckit-pro-gates.py:206"/>
</group>
<group type="3" gid="178" tokens="71" n="2" similarity="0.80">
<f n="test_a_strict_mode_gate_stop_never_auto_detects_implement" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1575"/>
<f n="assert_response" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:613"/>
</group>
<group type="3" gid="248" tokens="51" n="2" similarity="0.91">
<f n="valid_table" p="tests/speckit-pro/unit/test-gate-discovery-table.py:33"/>
<f n="pairing" p="tests/speckit-pro/unit/test-native-eval-contracts.py:67"/>
</group>
<group type="3" gid="249" tokens="266" n="2" similarity="0.82">
<f n="test_write_rejects_target_swap_between_conflict_check_and_replace" p="tests/speckit-pro/unit/test-generate-spec-index.py:392"/>
<f n="test_apply_rejects_target_swap_between_snapshot_and_replace" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8535"/>
</group>
<group type="3" gid="178" tokens="75" n="2" similarity="0.81">
<f n="test_provenance_pins_the_expected_upstream" p="tests/speckit-pro/unit/test-quint-reference-attribution.py:122"/>
<f n="assert_response" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:613"/>
</group>
<group type="3" gid="178" tokens="75" n="2" similarity="0.83">
<f n="test_provenance_pins_the_expected_upstream" p="tests/speckit-pro/unit/test-quint-reference-attribution.py:122"/>
<f n="test_preflight_ok_with_detected_prerequisites" p="tests/speckit-pro/unit/test-speckit-pro-runner.py:195"/>
</group>
<group type="3" gid="333" tokens="127" n="2" similarity="0.86">
<f n="run_runner" p="tests/speckit-pro/unit/test-speckit-pro-gates.py:85"/>
<f n="run_runner" p="tests/speckit-pro/unit/test-speckit-pro-runner.py:38"/>
</group>
<group type="3" gid="178" tokens="67" n="2" similarity="0.98">
<f n="assert_response" p="tests/speckit-pro/unit/test-speckit-pro-gates.py:240"/>
<f n="assert_response" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:613"/>
</group>
<group type="3" gid="334" tokens="230" n="2" similarity="0.96">
<f n="test_zero_bash_unknown_input_matches_the_public_result_schema" p="tests/speckit-pro/unit/test-speckit-pro-gates.py:351"/>
<f n="test_repo_bash_unknown_input_matches_the_public_result_schema" p="tests/speckit-pro/unit/test-speckit-pro-gates.py:374"/>
</group>
<group type="3" gid="335" tokens="122" n="2" similarity="0.84">
<f n="test_classify_shell_finding_blocks_active_gate_candidates" p="tests/speckit-pro/unit/test-speckit-pro-gates.py:3006"/>
<f n="test_active_path_guard_request_fixture_scans_current_repo_clean" p="tests/speckit-pro/unit/test-speckit-pro-gates.py:3050"/>
</group>
<group type="3" gid="336" tokens="253" n="2" similarity="0.95">
<f n="test_gate_implementations_avoid_shell_execution" p="tests/speckit-pro/unit/test-speckit-pro-gates.py:3061"/>
<f n="test_suite_implementation_uses_no_shell_true_os_system_or_command_string_subprocess" p="tests/speckit-pro/unit/test-speckit-pro-gates.py:3092"/>
</group>
<group type="3" gid="178" tokens="71" n="2" similarity="0.83">
<f n="assert_response" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:613"/>
<f n="test_full_launch_arithmetic_and_scope" p="tests/speckit-pro/unit/test-trigger-inventory.py:48"/>
</group>
<group type="3" gid="165" tokens="48" n="2" similarity="0.84">
<f n="write_route_policy_manifest" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:705"/>
<f n="create_marketplace" p="tests/speckit-pro/unit/test-sync-marketplace-versions.py:40"/>
</group>
<group type="3" gid="165" tokens="48" n="2" similarity="0.83">
<f n="write_route_policy_manifest" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:705"/>
<f n="create_codex_marketplace" p="tests/speckit-pro/unit/test-sync-marketplace-versions.py:46"/>
</group>
<group type="3" gid="338" tokens="118" n="2" similarity="0.82">
<f n="assert_route_aware_no_mutation_yet" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:814"/>
<f n="assert_route_aware_apply_mutation_evidence" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:948"/>
</group>
<group type="3" gid="338" tokens="126" n="2" similarity="0.81">
<f n="assert_route_aware_no_mutation_yet" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:814"/>
<f n="assert_route_aware_managed_helper_removal" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1111"/>
</group>
<group type="3" gid="339" tokens="551" n="2" similarity="0.82">
<f n="assert_route_aware_rollback_success_evidence" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:838"/>
<f n="assert_route_aware_rollback_failure_evidence" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:891"/>
</group>
<group type="3" gid="340" tokens="144" n="2" similarity="0.98">
<f n="test_install_codex_agents_rejects_supplied_invalid_route_policy_manifest_before_static_writes" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1542"/>
<f n="test_install_codex_agents_rejects_truthy_string_no_helper_authorization" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1568"/>
</group>
<group type="3" gid="340" tokens="138" n="2" similarity="0.84">
<f n="test_install_codex_agents_rejects_supplied_invalid_route_policy_manifest_before_static_writes" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1542"/>
<f n="test_preflight_rejects_parent_file_before_apply_writes" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8048"/>
</group>
<group type="3" gid="340" tokens="138" n="2" similarity="0.80">
<f n="test_install_codex_agents_rejects_supplied_invalid_route_policy_manifest_before_static_writes" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1542"/>
<f n="test_doctor_repair_refuses_non_fake_home" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8755"/>
</group>
<group type="3" gid="340" tokens="144" n="2" similarity="0.82">
<f n="test_install_codex_agents_rejects_truthy_string_no_helper_authorization" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1568"/>
<f n="test_preflight_rejects_parent_file_before_apply_writes" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8048"/>
</group>
<group type="3" gid="341" tokens="217" n="2" similarity="0.83">
<f n="test_install_codex_agents_route_aware_dry_run_uses_required_fallbacks_from_same_snapshot" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1796"/>
<f n="test_install_codex_agents_route_aware_apply_installs_missing_required_fallback_bytes" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1827"/>
</group>
<group type="3" gid="341" tokens="182" n="2" similarity="0.88">
<f n="test_install_codex_agents_route_aware_dry_run_uses_required_fallbacks_from_same_snapshot" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1796"/>
<f n="test_install_codex_agents_route_aware_dry_run_omits_unavailable_helper_when_no_file_exists" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6321"/>
</group>
<group type="3" gid="341" tokens="175" n="2" similarity="0.84">
<f n="test_install_codex_agents_route_aware_dry_run_uses_required_fallbacks_from_same_snapshot" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1796"/>
<f n="test_install_codex_agents_route_aware_apply_omits_unavailable_helper_and_installs_required_roster" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6353"/>
</group>
<group type="3" gid="341" tokens="154" n="2" similarity="0.94">
<f n="test_install_codex_agents_route_aware_dry_run_uses_required_fallbacks_from_same_snapshot" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1796"/>
<f n="test_install_codex_agents_strict_required_override_uses_one_tuple_per_required_agent" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6569"/>
</group>
<group type="3" gid="341" tokens="201" n="2" similarity="0.85">
<f n="test_install_codex_agents_route_aware_dry_run_uses_required_fallbacks_from_same_snapshot" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1796"/>
<f n="test_install_codex_agents_strict_helper_override_installs_compatible_helper" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6673"/>
</group>
<group type="3" gid="341" tokens="193" n="2" similarity="0.81">
<f n="test_install_codex_agents_route_aware_dry_run_uses_required_fallbacks_from_same_snapshot" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1796"/>
<f n="test_install_codex_agents_strict_helper_override_uses_valid_no_helper_without_helper_fallback" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6709"/>
</group>
<group type="3" gid="341" tokens="210" n="2" similarity="0.82">
<f n="test_install_codex_agents_route_aware_dry_run_uses_required_fallbacks_from_same_snapshot" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1796"/>
<f n="test_install_codex_agents_strict_helper_override_invalid_no_helper_fails_before_mutation" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6739"/>
</group>
<group type="3" gid="341" tokens="217" n="2" similarity="0.88">
<f n="test_install_codex_agents_route_aware_apply_installs_missing_required_fallback_bytes" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1827"/>
<f n="test_install_codex_agents_route_aware_dry_run_omits_unavailable_helper_when_no_file_exists" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6321"/>
</group>
<group type="3" gid="341" tokens="217" n="2" similarity="0.87">
<f n="test_install_codex_agents_route_aware_apply_installs_missing_required_fallback_bytes" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1827"/>
<f n="test_install_codex_agents_route_aware_apply_omits_unavailable_helper_and_installs_required_roster" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6353"/>
</group>
<group type="3" gid="341" tokens="217" n="2" similarity="0.81">
<f n="test_install_codex_agents_route_aware_apply_installs_missing_required_fallback_bytes" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1827"/>
<f n="test_install_codex_agents_strict_helper_override_installs_compatible_helper" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6673"/>
</group>
<group type="3" gid="341" tokens="217" n="2" similarity="0.82">
<f n="test_install_codex_agents_route_aware_apply_installs_missing_required_fallback_bytes" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1827"/>
<f n="test_install_codex_agents_strict_helper_override_invalid_no_helper_fails_before_mutation" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6739"/>
</group>
<group type="3" gid="342" tokens="481" n="2" similarity="0.97">
<f n="test_install_codex_agents_route_aware_apply_failure_restores_prior_required_bytes_and_modes" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1901"/>
<f n="test_install_codex_agents_route_aware_apply_reports_unrestored_rollback_failure" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1986"/>
</group>
<group type="3" gid="342" tokens="450" n="2" similarity="0.82">
<f n="test_install_codex_agents_route_aware_apply_failure_restores_prior_required_bytes_and_modes" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1901"/>
<f n="test_install_codex_agents_route_aware_refuses_concurrent_edit_before_write" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6181"/>
</group>
<group type="3" gid="342" tokens="461" n="2" similarity="0.85">
<f n="test_install_codex_agents_route_aware_apply_failure_restores_prior_required_bytes_and_modes" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1901"/>
<f n="test_install_codex_agents_route_aware_rollback_preserves_concurrent_edit" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6242"/>
</group>
<group type="3" gid="342" tokens="481" n="2" similarity="0.80">
<f n="test_install_codex_agents_route_aware_apply_reports_unrestored_rollback_failure" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1986"/>
<f n="test_install_codex_agents_route_aware_refuses_concurrent_edit_before_write" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6181"/>
</group>
<group type="3" gid="342" tokens="481" n="2" similarity="0.84">
<f n="test_install_codex_agents_route_aware_apply_reports_unrestored_rollback_failure" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:1986"/>
<f n="test_install_codex_agents_route_aware_rollback_preserves_concurrent_edit" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6242"/>
</group>
<group type="3" gid="343" tokens="192" n="2" similarity="0.97">
<f n="test_install_codex_agents_no_clobber_write_preserves_final_window_edit" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2315"/>
<f n="test_install_codex_agents_no_clobber_removal_preserves_final_window_edit" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2349"/>
</group>
<group type="3" gid="343" tokens="241" n="2" similarity="0.82">
<f n="test_install_codex_agents_no_clobber_write_preserves_final_window_edit" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2315"/>
<f n="test_install_codex_agents_no_clobber_removal_preserves_entry_created_after_move" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2418"/>
</group>
<group type="3" gid="343" tokens="192" n="2" similarity="0.81">
<f n="test_install_codex_agents_no_clobber_write_preserves_final_window_edit" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2315"/>
<f n="test_install_codex_agents_backup_move_retries_native_no_replace_collision" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5737"/>
</group>
<group type="3" gid="343" tokens="241" n="2" similarity="0.83">
<f n="test_install_codex_agents_no_clobber_removal_preserves_final_window_edit" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2349"/>
<f n="test_install_codex_agents_no_clobber_removal_preserves_entry_created_after_move" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2418"/>
</group>
<group type="3" gid="343" tokens="191" n="2" similarity="0.80">
<f n="test_install_codex_agents_no_clobber_removal_preserves_final_window_edit" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2349"/>
<f n="test_install_codex_agents_backup_move_retries_native_no_replace_collision" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5737"/>
</group>
<group type="3" gid="343" tokens="311" n="2" similarity="0.81">
<f n="test_install_codex_agents_no_clobber_write_preserves_entry_created_after_move" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2378"/>
<f n="test_install_codex_agents_no_clobber_removal_preserves_entry_created_after_move" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2418"/>
</group>
<group type="3" gid="343" tokens="311" n="2" similarity="0.81">
<f n="test_install_codex_agents_no_clobber_write_preserves_entry_created_after_move" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2378"/>
<f n="test_install_codex_agents_backup_cleanup_preserves_takeover_entry" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2677"/>
</group>
<group type="3" gid="343" tokens="241" n="2" similarity="0.81">
<f n="test_install_codex_agents_no_clobber_removal_preserves_entry_created_after_move" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2418"/>
<f n="test_install_codex_agents_temp_cleanup_preserves_takeover_entry" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2642"/>
</group>
<group type="3" gid="343" tokens="267" n="2" similarity="0.83">
<f n="test_install_codex_agents_no_clobber_removal_preserves_entry_created_after_move" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2418"/>
<f n="test_install_codex_agents_backup_cleanup_preserves_takeover_entry" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2677"/>
</group>
<group type="3" gid="343" tokens="316" n="2" similarity="0.80">
<f n="test_install_codex_agents_no_clobber_removal_preserves_entry_created_after_move" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2418"/>
<f n="test_install_codex_agents_recovery_copy_evidence_is_anchor_relative_after_directory_move" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3958"/>
</group>
<group type="3" gid="343" tokens="293" n="2" similarity="0.83">
<f n="test_install_codex_agents_no_clobber_removal_preserves_entry_created_after_move" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2418"/>
<f n="test_install_codex_agents_recovery_copy_detects_post_open_directory_move" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5794"/>
</group>
<group type="3" gid="343" tokens="247" n="2" similarity="0.82">
<f n="test_install_codex_agents_temp_cleanup_preserves_takeover_entry" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2642"/>
<f n="test_install_codex_agents_windows_temp_cleanup_preserves_takeover_entry" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5025"/>
</group>
<group type="3" gid="343" tokens="324" n="2" similarity="0.83">
<f n="test_install_codex_agents_cleanup_owned_entry_final_unlink_swap_fails_closed" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2742"/>
<f n="test_install_codex_agents_posix_cleanup_preserves_verified_quarantine_without_unlink" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2852"/>
</group>
<group type="3" gid="343" tokens="318" n="2" similarity="0.82">
<f n="test_install_codex_agents_cleanup_owned_entry_final_unlink_swap_fails_closed" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2742"/>
<f n="test_install_codex_agents_posix_private_quarantine_open_failure_preserves_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3249"/>
</group>
<group type="3" gid="343" tokens="313" n="2" similarity="0.85">
<f n="test_install_codex_agents_cleanup_owned_entry_final_unlink_swap_fails_closed" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2742"/>
<f n="test_install_codex_agents_posix_private_quarantine_late_rmdir_child_reports_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3400"/>
</group>
<group type="3" gid="343" tokens="312" n="2" similarity="0.84">
<f n="test_install_codex_agents_cleanup_owned_entry_final_unlink_swap_fails_closed" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2742"/>
<f n="test_install_codex_agents_posix_cleanup_restore_success_without_reappearance_has_no_phantom_source" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3543"/>
</group>
<group type="3" gid="343" tokens="336" n="2" similarity="0.83">
<f n="test_install_codex_agents_cleanup_owned_entry_final_unlink_swap_fails_closed" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2742"/>
<f n="test_install_codex_agents_posix_cleanup_restore_success_reclassifies_source_reappearance" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3585"/>
</group>
<group type="3" gid="343" tokens="324" n="2" similarity="0.88">
<f n="test_install_codex_agents_posix_cleanup_preserves_verified_quarantine_without_unlink" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2852"/>
<f n="test_install_codex_agents_posix_private_quarantine_open_failure_preserves_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3249"/>
</group>
<group type="3" gid="343" tokens="324" n="2" similarity="0.82">
<f n="test_install_codex_agents_posix_cleanup_preserves_verified_quarantine_without_unlink" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2852"/>
<f n="test_install_codex_agents_posix_private_quarantine_real_enotempty_reports_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3361"/>
</group>
<group type="3" gid="343" tokens="324" n="2" similarity="0.89">
<f n="test_install_codex_agents_posix_cleanup_preserves_verified_quarantine_without_unlink" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2852"/>
<f n="test_install_codex_agents_posix_private_quarantine_late_rmdir_child_reports_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3400"/>
</group>
<group type="3" gid="343" tokens="324" n="2" similarity="0.83">
<f n="test_install_codex_agents_posix_cleanup_preserves_verified_quarantine_without_unlink" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2852"/>
<f n="test_install_codex_agents_posix_private_quarantine_backslash_child_reports_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3444"/>
</group>
<group type="3" gid="343" tokens="324" n="2" similarity="0.85">
<f n="test_install_codex_agents_posix_cleanup_preserves_verified_quarantine_without_unlink" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2852"/>
<f n="test_install_codex_agents_posix_cleanup_restore_success_without_reappearance_has_no_phantom_source" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3543"/>
</group>
<group type="3" gid="343" tokens="336" n="2" similarity="0.83">
<f n="test_install_codex_agents_posix_cleanup_preserves_verified_quarantine_without_unlink" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2852"/>
<f n="test_install_codex_agents_posix_cleanup_restore_success_reclassifies_source_reappearance" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3585"/>
</group>
<group type="3" gid="344" tokens="395" n="2" similarity="0.88">
<f n="test_install_codex_agents_posix_private_quarantine_file_not_found_preserves_private_residue" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2977"/>
<f n="test_install_codex_agents_posix_private_quarantine_move_error_classifies_public_and_private" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3038"/>
</group>
<group type="3" gid="344" tokens="414" n="2" similarity="0.88">
<f n="test_install_codex_agents_posix_private_quarantine_file_not_found_preserves_private_residue" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:2977"/>
<f n="test_install_codex_agents_posix_private_quarantine_post_move_mismatch_classifies_public_original" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3097"/>
</group>
<group type="3" gid="344" tokens="414" n="2" similarity="0.95">
<f n="test_install_codex_agents_posix_private_quarantine_move_error_classifies_public_and_private" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3038"/>
<f n="test_install_codex_agents_posix_private_quarantine_post_move_mismatch_classifies_public_original" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3097"/>
</group>
<group type="3" gid="343" tokens="321" n="2" similarity="0.81">
<f n="test_install_codex_agents_posix_private_quarantine_public_read_error_is_concurrent_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3161"/>
<f n="test_install_codex_agents_posix_private_quarantine_open_failure_preserves_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3249"/>
</group>
<group type="3" gid="343" tokens="373" n="2" similarity="0.80">
<f n="test_install_codex_agents_posix_private_quarantine_public_read_error_is_concurrent_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3161"/>
<f n="test_install_codex_agents_posix_cleanup_restore_collision_read_error_reports_both_names" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3485"/>
</group>
<group type="3" gid="343" tokens="247" n="2" similarity="0.81">
<f n="test_install_codex_agents_posix_private_quarantine_mkdir_failure_preserves_public_cleanup" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3218"/>
<f n="test_install_codex_agents_posix_private_quarantine_real_enotempty_reports_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3361"/>
</group>
<group type="3" gid="343" tokens="208" n="2" similarity="0.83">
<f n="test_install_codex_agents_posix_private_quarantine_mkdir_failure_preserves_public_cleanup" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3218"/>
<f n="test_install_codex_agents_posix_uncertain_entry_read_error_is_not_cleanup_incomplete" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3671"/>
</group>
<group type="3" gid="343" tokens="318" n="2" similarity="0.83">
<f n="test_install_codex_agents_posix_private_quarantine_open_failure_preserves_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3249"/>
<f n="test_install_codex_agents_posix_private_quarantine_real_enotempty_reports_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3361"/>
</group>
<group type="3" gid="343" tokens="318" n="2" similarity="0.92">
<f n="test_install_codex_agents_posix_private_quarantine_open_failure_preserves_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3249"/>
<f n="test_install_codex_agents_posix_private_quarantine_late_rmdir_child_reports_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3400"/>
</group>
<group type="3" gid="343" tokens="318" n="2" similarity="0.84">
<f n="test_install_codex_agents_posix_private_quarantine_open_failure_preserves_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3249"/>
<f n="test_install_codex_agents_posix_private_quarantine_backslash_child_reports_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3444"/>
</group>
<group type="3" gid="343" tokens="373" n="2" similarity="0.84">
<f n="test_install_codex_agents_posix_private_quarantine_open_failure_preserves_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3249"/>
<f n="test_install_codex_agents_posix_cleanup_restore_collision_read_error_reports_both_names" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3485"/>
</group>
<group type="3" gid="343" tokens="318" n="2" similarity="0.88">
<f n="test_install_codex_agents_posix_private_quarantine_open_failure_preserves_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3249"/>
<f n="test_install_codex_agents_posix_cleanup_restore_success_without_reappearance_has_no_phantom_source" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3543"/>
</group>
<group type="3" gid="343" tokens="336" n="2" similarity="0.88">
<f n="test_install_codex_agents_posix_private_quarantine_open_failure_preserves_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3249"/>
<f n="test_install_codex_agents_posix_cleanup_restore_success_reclassifies_source_reappearance" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3585"/>
</group>
<group type="3" gid="343" tokens="443" n="2" similarity="0.82">
<f n="test_install_codex_agents_posix_private_quarantine_close_and_rmdir_failures_are_evidence" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3301"/>
<f n="test_install_codex_agents_posix_cleanup_restore_collision_read_error_reports_both_names" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3485"/>
</group>
<group type="3" gid="343" tokens="313" n="2" similarity="0.86">
<f n="test_install_codex_agents_posix_private_quarantine_real_enotempty_reports_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3361"/>
<f n="test_install_codex_agents_posix_private_quarantine_late_rmdir_child_reports_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3400"/>
</group>
<group type="3" gid="343" tokens="262" n="2" similarity="0.97">
<f n="test_install_codex_agents_posix_private_quarantine_real_enotempty_reports_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3361"/>
<f n="test_install_codex_agents_posix_private_quarantine_backslash_child_reports_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3444"/>
</group>
<group type="3" gid="343" tokens="273" n="2" similarity="0.91">
<f n="test_install_codex_agents_posix_private_quarantine_real_enotempty_reports_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3361"/>
<f n="test_install_codex_agents_posix_cleanup_restore_success_without_reappearance_has_no_phantom_source" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3543"/>
</group>
<group type="3" gid="343" tokens="336" n="2" similarity="0.81">
<f n="test_install_codex_agents_posix_private_quarantine_real_enotempty_reports_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3361"/>
<f n="test_install_codex_agents_posix_cleanup_restore_success_reclassifies_source_reappearance" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3585"/>
</group>
<group type="3" gid="343" tokens="313" n="2" similarity="0.89">
<f n="test_install_codex_agents_posix_private_quarantine_late_rmdir_child_reports_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3400"/>
<f n="test_install_codex_agents_posix_private_quarantine_backslash_child_reports_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3444"/>
</group>
<group type="3" gid="343" tokens="373" n="2" similarity="0.81">
<f n="test_install_codex_agents_posix_private_quarantine_late_rmdir_child_reports_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3400"/>
<f n="test_install_codex_agents_posix_cleanup_restore_collision_read_error_reports_both_names" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3485"/>
</group>
<group type="3" gid="343" tokens="313" n="2" similarity="0.89">
<f n="test_install_codex_agents_posix_private_quarantine_late_rmdir_child_reports_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3400"/>
<f n="test_install_codex_agents_posix_cleanup_restore_success_without_reappearance_has_no_phantom_source" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3543"/>
</group>
<group type="3" gid="343" tokens="336" n="2" similarity="0.86">
<f n="test_install_codex_agents_posix_private_quarantine_late_rmdir_child_reports_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3400"/>
<f n="test_install_codex_agents_posix_cleanup_restore_success_reclassifies_source_reappearance" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3585"/>
</group>
<group type="3" gid="343" tokens="273" n="2" similarity="0.91">
<f n="test_install_codex_agents_posix_private_quarantine_backslash_child_reports_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3444"/>
<f n="test_install_codex_agents_posix_cleanup_restore_success_without_reappearance_has_no_phantom_source" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3543"/>
</group>
<group type="3" gid="343" tokens="336" n="2" similarity="0.82">
<f n="test_install_codex_agents_posix_private_quarantine_backslash_child_reports_private_dir_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3444"/>
<f n="test_install_codex_agents_posix_cleanup_restore_success_reclassifies_source_reappearance" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3585"/>
</group>
<group type="3" gid="343" tokens="373" n="2" similarity="0.85">
<f n="test_install_codex_agents_posix_cleanup_restore_collision_read_error_reports_both_names" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3485"/>
<f n="test_install_codex_agents_posix_cleanup_restore_success_without_reappearance_has_no_phantom_source" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3543"/>
</group>
<group type="3" gid="343" tokens="373" n="2" similarity="0.91">
<f n="test_install_codex_agents_posix_cleanup_restore_collision_read_error_reports_both_names" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3485"/>
<f n="test_install_codex_agents_posix_cleanup_restore_success_reclassifies_source_reappearance" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3585"/>
</group>
<group type="3" gid="345" tokens="62" n="2" similarity="0.80">
<f n="move_then_recreate" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3504"/>
<f n="mismatch_then_restore_with_source_reappearance" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3603"/>
</group>
<group type="3" gid="343" tokens="336" n="2" similarity="0.90">
<f n="test_install_codex_agents_posix_cleanup_restore_success_without_reappearance_has_no_phantom_source" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3543"/>
<f n="test_install_codex_agents_posix_cleanup_restore_success_reclassifies_source_reappearance" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3585"/>
</group>
<group type="3" gid="343" tokens="350" n="2" similarity="0.82">
<f n="test_install_codex_agents_posix_cleanup_restore_success_reclassifies_source_reappearance" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3585"/>
<f n="test_install_codex_agents_windows_cleanup_primary_and_close_failure_reports_close_without_relabeling" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4593"/>
</group>
<group type="3" gid="343" tokens="208" n="2" similarity="0.90">
<f n="test_install_codex_agents_posix_uncertain_entry_takeover_is_not_laundered_as_cleanup" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3638"/>
<f n="test_install_codex_agents_posix_uncertain_entry_read_error_is_not_cleanup_incomplete" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3671"/>
</group>
<group type="3" gid="346" tokens="130" n="2" similarity="0.88">
<f n="test_install_codex_agents_backup_move_close_error_does_not_hide_moved_backup" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3893"/>
<f n="test_install_codex_agents_restore_close_error_does_not_mask_restored_state" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3938"/>
</group>
<group type="3" gid="346" tokens="154" n="2" similarity="0.82">
<f n="test_install_codex_agents_backup_move_close_error_does_not_hide_moved_backup" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3893"/>
<f n="test_install_codex_agents_backup_move_does_not_relinquish_candidate_before_native_move" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5714"/>
</group>
<group type="3" gid="343" tokens="316" n="2" similarity="0.96">
<f n="test_install_codex_agents_recovery_copy_evidence_is_anchor_relative_after_directory_move" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:3958"/>
<f n="test_install_codex_agents_recovery_copy_detects_post_open_directory_move" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5794"/>
</group>
<group type="3" gid="343" tokens="155" n="2" similarity="0.84">
<f n="test_install_codex_agents_windows_open_canonicalizes_identity_from_directory_handle" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4049"/>
<f n="test_install_codex_agents_windows_target_is_safe_close_failure_raises_close_handle" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4916"/>
</group>
<group type="3" gid="343" tokens="155" n="2" similarity="0.84">
<f n="test_install_codex_agents_windows_open_canonicalizes_identity_from_directory_handle" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4049"/>
<f n="test_install_codex_agents_windows_write_apply_does_not_fail_on_nt_backend" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5498"/>
</group>
<group type="3" gid="343" tokens="171" n="2" similarity="0.82">
<f n="test_install_codex_agents_windows_open_canonicalizes_identity_from_directory_handle" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4049"/>
<f n="test_install_codex_agents_windows_directory_handle_outlives_backup_rename" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5609"/>
</group>
<group type="3" gid="343" tokens="144" n="2" similarity="0.83">
<f n="test_install_codex_agents_windows_open_rejects_expected_identity_mismatch" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4070"/>
<f n="test_install_codex_agents_windows_write_apply_does_not_fail_on_nt_backend" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5498"/>
</group>
<group type="3" gid="343" tokens="235" n="2" similarity="0.81">
<f n="test_install_codex_agents_windows_no_replace_rename_uses_root_handle_and_replace_false" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4087"/>
<f n="test_install_codex_agents_windows_no_replace_rename_maps_existing_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4115"/>
</group>
<group type="3" gid="343" tokens="235" n="2" similarity="0.81">
<f n="test_install_codex_agents_windows_no_replace_rename_uses_root_handle_and_replace_false" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4087"/>
<f n="test_install_codex_agents_windows_rename_close_error_is_non_masking" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4141"/>
</group>
<group type="3" gid="343" tokens="198" n="2" similarity="0.89">
<f n="test_install_codex_agents_windows_no_replace_rename_maps_existing_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4115"/>
<f n="test_install_codex_agents_windows_rename_close_error_is_non_masking" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4141"/>
</group>
<group type="3" gid="343" tokens="251" n="2" similarity="0.83">
<f n="test_install_codex_agents_windows_no_replace_rename_maps_existing_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4115"/>
<f n="test_install_codex_agents_windows_restore_rename_close_failure_omits_absent_backup" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4272"/>
</group>
<group type="3" gid="343" tokens="262" n="2" similarity="0.81">
<f n="test_install_codex_agents_windows_no_replace_rename_maps_existing_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4115"/>
<f n="test_install_codex_agents_windows_restore_rename_failure_does_not_preserve_absent_entries" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4400"/>
</group>
<group type="3" gid="343" tokens="198" n="2" similarity="0.82">
<f n="test_install_codex_agents_windows_no_replace_rename_maps_existing_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4115"/>
<f n="test_install_codex_agents_windows_target_is_safe_close_failure_raises_close_handle" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4916"/>
</group>
<group type="3" gid="343" tokens="198" n="2" similarity="0.81">
<f n="test_install_codex_agents_windows_no_replace_rename_maps_existing_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4115"/>
<f n="test_install_codex_agents_windows_write_apply_does_not_fail_on_nt_backend" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5498"/>
</group>
<group type="3" gid="343" tokens="198" n="2" similarity="0.83">
<f n="test_install_codex_agents_windows_no_replace_rename_maps_existing_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4115"/>
<f n="test_install_codex_agents_windows_directory_handle_outlives_backup_rename" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5609"/>
</group>
<group type="3" gid="343" tokens="181" n="2" similarity="0.84">
<f n="test_install_codex_agents_windows_rename_close_error_is_non_masking" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4141"/>
<f n="test_install_codex_agents_windows_target_is_safe_close_failure_raises_close_handle" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4916"/>
</group>
<group type="3" gid="343" tokens="181" n="2" similarity="0.84">
<f n="test_install_codex_agents_windows_rename_close_error_is_non_masking" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4141"/>
<f n="test_install_codex_agents_windows_write_apply_does_not_fail_on_nt_backend" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5498"/>
</group>
<group type="3" gid="343" tokens="181" n="2" similarity="0.82">
<f n="test_install_codex_agents_windows_rename_close_error_is_non_masking" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4141"/>
<f n="test_install_codex_agents_windows_directory_handle_outlives_backup_rename" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5609"/>
</group>
<group type="3" gid="343" tokens="271" n="2" similarity="0.92">
<f n="test_install_codex_agents_windows_publish_rename_close_failure_preserves_committed_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4166"/>
<f n="test_install_codex_agents_windows_write_backup_rename_close_failure_preserves_attempted_destination" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4202"/>
</group>
<group type="3" gid="343" tokens="266" n="2" similarity="0.91">
<f n="test_install_codex_agents_windows_publish_rename_close_failure_preserves_committed_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4166"/>
<f n="test_install_codex_agents_windows_removal_backup_rename_close_failure_preserves_attempted_destination" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4240"/>
</group>
<group type="3" gid="343" tokens="266" n="2" similarity="0.84">
<f n="test_install_codex_agents_windows_publish_rename_close_failure_preserves_committed_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4166"/>
<f n="test_install_codex_agents_windows_restore_rename_close_failure_omits_absent_backup" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4272"/>
</group>
<group type="3" gid="343" tokens="334" n="2" similarity="0.81">
<f n="test_install_codex_agents_windows_publish_rename_close_failure_preserves_committed_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4166"/>
<f n="test_install_codex_agents_windows_publish_primary_and_close_failure_does_not_preserve_absent_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4435"/>
</group>
<group type="3" gid="343" tokens="266" n="2" similarity="0.87">
<f n="test_install_codex_agents_windows_publish_rename_close_failure_preserves_committed_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4166"/>
<f n="test_install_codex_agents_windows_successful_temp_close_failure_returns_cleanup_evidence" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4993"/>
</group>
<group type="3" gid="343" tokens="271" n="2" similarity="0.99">
<f n="test_install_codex_agents_windows_write_backup_rename_close_failure_preserves_attempted_destination" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4202"/>
<f n="test_install_codex_agents_windows_removal_backup_rename_close_failure_preserves_attempted_destination" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4240"/>
</group>
<group type="3" gid="343" tokens="271" n="2" similarity="0.83">
<f n="test_install_codex_agents_windows_write_backup_rename_close_failure_preserves_attempted_destination" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4202"/>
<f n="test_install_codex_agents_windows_restore_rename_close_failure_omits_absent_backup" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4272"/>
</group>
<group type="3" gid="343" tokens="334" n="2" similarity="0.83">
<f n="test_install_codex_agents_windows_write_backup_rename_close_failure_preserves_attempted_destination" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4202"/>
<f n="test_install_codex_agents_windows_publish_primary_and_close_failure_does_not_preserve_absent_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4435"/>
</group>
<group type="3" gid="343" tokens="349" n="2" similarity="0.82">
<f n="test_install_codex_agents_windows_write_backup_rename_close_failure_preserves_attempted_destination" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4202"/>
<f n="test_install_codex_agents_windows_backup_primary_and_close_failure_keeps_primary_classification" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4488"/>
</group>
<group type="3" gid="343" tokens="271" n="2" similarity="0.89">
<f n="test_install_codex_agents_windows_write_backup_rename_close_failure_preserves_attempted_destination" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4202"/>
<f n="test_install_codex_agents_windows_successful_temp_close_failure_returns_cleanup_evidence" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4993"/>
</group>
<group type="3" gid="343" tokens="271" n="2" similarity="0.80">
<f n="test_install_codex_agents_windows_write_backup_rename_close_failure_preserves_attempted_destination" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4202"/>
<f n="test_install_codex_agents_windows_cleanup_result_records_close_failure_without_collector" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5215"/>
</group>
<group type="3" gid="343" tokens="314" n="2" similarity="0.80">
<f n="test_install_codex_agents_windows_write_backup_rename_close_failure_preserves_attempted_destination" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4202"/>
<f n="test_install_codex_agents_windows_cleanup_records_close_failure_after_successful_handle_delete" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5250"/>
</group>
<group type="3" gid="343" tokens="265" n="2" similarity="0.83">
<f n="test_install_codex_agents_windows_removal_backup_rename_close_failure_preserves_attempted_destination" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4240"/>
<f n="test_install_codex_agents_windows_restore_rename_close_failure_omits_absent_backup" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4272"/>
</group>
<group type="3" gid="343" tokens="334" n="2" similarity="0.82">
<f n="test_install_codex_agents_windows_removal_backup_rename_close_failure_preserves_attempted_destination" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4240"/>
<f n="test_install_codex_agents_windows_publish_primary_and_close_failure_does_not_preserve_absent_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4435"/>
</group>
<group type="3" gid="343" tokens="349" n="2" similarity="0.81">
<f n="test_install_codex_agents_windows_removal_backup_rename_close_failure_preserves_attempted_destination" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4240"/>
<f n="test_install_codex_agents_windows_backup_primary_and_close_failure_keeps_primary_classification" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4488"/>
</group>
<group type="3" gid="343" tokens="265" n="2" similarity="0.90">
<f n="test_install_codex_agents_windows_removal_backup_rename_close_failure_preserves_attempted_destination" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4240"/>
<f n="test_install_codex_agents_windows_successful_temp_close_failure_returns_cleanup_evidence" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4993"/>
</group>
<group type="3" gid="343" tokens="265" n="2" similarity="0.80">
<f n="test_install_codex_agents_windows_removal_backup_rename_close_failure_preserves_attempted_destination" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4240"/>
<f n="test_install_codex_agents_windows_cleanup_result_records_close_failure_without_collector" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5215"/>
</group>
<group type="3" gid="343" tokens="314" n="2" similarity="0.80">
<f n="test_install_codex_agents_windows_removal_backup_rename_close_failure_preserves_attempted_destination" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4240"/>
<f n="test_install_codex_agents_windows_cleanup_records_close_failure_after_successful_handle_delete" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5250"/>
</group>
<group type="3" gid="343" tokens="285" n="2" similarity="0.85">
<f n="test_install_codex_agents_windows_restore_rename_close_failure_omits_absent_backup" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4272"/>
<f n="test_install_codex_agents_windows_rename_primary_and_close_failure_is_structured" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4305"/>
</group>
<group type="3" gid="343" tokens="262" n="2" similarity="0.81">
<f n="test_install_codex_agents_windows_restore_rename_close_failure_omits_absent_backup" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4272"/>
<f n="test_install_codex_agents_windows_restore_rename_failure_does_not_preserve_absent_entries" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4400"/>
</group>
<group type="3" gid="343" tokens="336" n="2" similarity="0.86">
<f n="test_install_codex_agents_windows_restore_rename_close_failure_omits_absent_backup" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4272"/>
<f n="test_install_codex_agents_windows_restore_primary_and_close_failure_reports_close_and_final_state" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4543"/>
</group>
<group type="3" gid="343" tokens="253" n="2" similarity="0.81">
<f n="test_install_codex_agents_windows_restore_rename_close_failure_omits_absent_backup" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4272"/>
<f n="test_install_codex_agents_windows_successful_temp_close_failure_returns_cleanup_evidence" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4993"/>
</group>
<group type="3" gid="343" tokens="251" n="2" similarity="0.81">
<f n="test_install_codex_agents_windows_restore_rename_close_failure_omits_absent_backup" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4272"/>
<f n="test_install_codex_agents_windows_cleanup_result_records_close_failure_without_collector" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5215"/>
</group>
<group type="3" gid="343" tokens="262" n="2" similarity="0.82">
<f n="test_install_codex_agents_windows_restore_rename_failure_does_not_preserve_absent_entries" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4400"/>
<f n="test_install_codex_agents_windows_temp_cleanup_preserves_takeover_entry" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5025"/>
</group>
<group type="3" gid="343" tokens="349" n="2" similarity="0.82">
<f n="test_install_codex_agents_windows_publish_primary_and_close_failure_does_not_preserve_absent_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4435"/>
<f n="test_install_codex_agents_windows_backup_primary_and_close_failure_keeps_primary_classification" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4488"/>
</group>
<group type="3" gid="343" tokens="334" n="2" similarity="0.81">
<f n="test_install_codex_agents_windows_publish_primary_and_close_failure_does_not_preserve_absent_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4435"/>
<f n="test_install_codex_agents_windows_temp_write_capture_failure_preserves_name_swap_without_deletefile" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4939"/>
</group>
<group type="3" gid="343" tokens="376" n="2" similarity="0.80">
<f n="test_install_codex_agents_windows_publish_primary_and_close_failure_does_not_preserve_absent_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4435"/>
<f n="test_install_codex_agents_windows_cleanup_rename_close_failure_reports_recreated_source" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5291"/>
</group>
<group type="3" gid="343" tokens="349" n="2" similarity="0.94">
<f n="test_install_codex_agents_windows_backup_primary_and_close_failure_keeps_primary_classification" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4488"/>
<f n="test_install_codex_agents_windows_restore_primary_and_close_failure_reports_close_and_final_state" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4543"/>
</group>
<group type="3" gid="343" tokens="350" n="2" similarity="0.91">
<f n="test_install_codex_agents_windows_backup_primary_and_close_failure_keeps_primary_classification" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4488"/>
<f n="test_install_codex_agents_windows_cleanup_primary_and_close_failure_reports_close_without_relabeling" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4593"/>
</group>
<group type="3" gid="343" tokens="349" n="2" similarity="0.81">
<f n="test_install_codex_agents_windows_backup_primary_and_close_failure_keeps_primary_classification" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4488"/>
<f n="test_install_codex_agents_windows_temp_write_capture_failure_preserves_name_swap_without_deletefile" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4939"/>
</group>
<group type="3" gid="343" tokens="376" n="2" similarity="0.85">
<f n="test_install_codex_agents_windows_backup_primary_and_close_failure_keeps_primary_classification" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4488"/>
<f n="test_install_codex_agents_windows_cleanup_rename_close_failure_reports_recreated_source" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5291"/>
</group>
<group type="3" gid="343" tokens="350" n="2" similarity="0.93">
<f n="test_install_codex_agents_windows_restore_primary_and_close_failure_reports_close_and_final_state" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4543"/>
<f n="test_install_codex_agents_windows_cleanup_primary_and_close_failure_reports_close_without_relabeling" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4593"/>
</group>
<group type="3" gid="343" tokens="400" n="2" similarity="0.81">
<f n="test_install_codex_agents_windows_restore_primary_and_close_failure_reports_close_and_final_state" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4543"/>
<f n="test_install_codex_agents_windows_cleanup_moved_state_mismatch_reports_cleanup_and_recreated_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5157"/>
</group>
<group type="3" gid="343" tokens="376" n="2" similarity="0.85">
<f n="test_install_codex_agents_windows_restore_primary_and_close_failure_reports_close_and_final_state" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4543"/>
<f n="test_install_codex_agents_windows_cleanup_rename_close_failure_reports_recreated_source" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5291"/>
</group>
<group type="3" gid="343" tokens="378" n="2" similarity="0.81">
<f n="test_install_codex_agents_windows_restore_primary_and_close_failure_reports_close_and_final_state" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4543"/>
<f n="test_install_codex_agents_windows_cleanup_generic_rename_error_classifies_candidate_and_source" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5354"/>
</group>
<group type="3" gid="343" tokens="400" n="2" similarity="0.86">
<f n="test_install_codex_agents_windows_cleanup_primary_and_close_failure_reports_close_without_relabeling" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4593"/>
<f n="test_install_codex_agents_windows_cleanup_moved_state_mismatch_reports_cleanup_and_recreated_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5157"/>
</group>
<group type="3" gid="343" tokens="376" n="2" similarity="0.91">
<f n="test_install_codex_agents_windows_cleanup_primary_and_close_failure_reports_close_without_relabeling" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4593"/>
<f n="test_install_codex_agents_windows_cleanup_rename_close_failure_reports_recreated_source" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5291"/>
</group>
<group type="3" gid="343" tokens="378" n="2" similarity="0.87">
<f n="test_install_codex_agents_windows_cleanup_primary_and_close_failure_reports_close_without_relabeling" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4593"/>
<f n="test_install_codex_agents_windows_cleanup_generic_rename_error_classifies_candidate_and_source" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5354"/>
</group>
<group type="3" gid="348" tokens="78" n="2" similarity="0.84">
<f n="close_fail_recreate_and_mutate_candidate" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4666"/>
<f n="rename_then_recreate_source" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5307"/>
</group>
<group type="3" gid="343" tokens="279" n="2" similarity="0.90">
<f n="test_install_codex_agents_windows_recovery_copy_verifies_exclusive_handle_without_path_reopen" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4750"/>
<f n="test_install_codex_agents_windows_recovery_copy_applies_readonly_mode_via_exclusive_handle" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4785"/>
</group>
<group type="3" gid="343" tokens="253" n="2" similarity="0.80">
<f n="test_install_codex_agents_windows_recovery_copy_verifies_exclusive_handle_without_path_reopen" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4750"/>
<f n="test_install_codex_agents_windows_successful_temp_close_failure_returns_cleanup_evidence" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4993"/>
</group>
<group type="3" gid="343" tokens="252" n="2" similarity="0.85">
<f n="test_install_codex_agents_windows_recovery_copy_verifies_exclusive_handle_without_path_reopen" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4750"/>
<f n="test_install_codex_agents_windows_readonly_rollback_write_uses_handle_bound_cleanup" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5523"/>
</group>
<group type="3" gid="343" tokens="279" n="2" similarity="0.84">
<f n="test_install_codex_agents_windows_recovery_copy_applies_readonly_mode_via_exclusive_handle" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4785"/>
<f n="test_install_codex_agents_windows_readonly_rollback_write_uses_handle_bound_cleanup" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5523"/>
</group>
<group type="3" gid="343" tokens="154" n="2" similarity="0.85">
<f n="test_install_codex_agents_windows_target_is_safe_close_failure_raises_close_handle" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4916"/>
<f n="test_install_codex_agents_windows_write_apply_does_not_fail_on_nt_backend" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5498"/>
</group>
<group type="3" gid="343" tokens="171" n="2" similarity="0.84">
<f n="test_install_codex_agents_windows_target_is_safe_close_failure_raises_close_handle" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4916"/>
<f n="test_install_codex_agents_windows_directory_handle_outlives_backup_rename" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5609"/>
</group>
<group type="3" gid="343" tokens="312" n="2" similarity="0.82">
<f n="test_install_codex_agents_windows_temp_write_capture_failure_preserves_name_swap_without_deletefile" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4939"/>
<f n="test_install_codex_agents_windows_temp_cleanup_preserves_takeover_entry" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5025"/>
</group>
<group type="3" gid="343" tokens="318" n="2" similarity="0.80">
<f n="test_install_codex_agents_windows_temp_write_capture_failure_preserves_name_swap_without_deletefile" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4939"/>
<f n="test_install_codex_agents_windows_readonly_write_rejects_target_swap_before_mode_apply" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5560"/>
</group>
<group type="3" gid="343" tokens="253" n="2" similarity="0.83">
<f n="test_install_codex_agents_windows_successful_temp_close_failure_returns_cleanup_evidence" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4993"/>
<f n="test_install_codex_agents_windows_cleanup_result_records_close_failure_without_collector" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5215"/>
</group>
<group type="3" gid="343" tokens="314" n="2" similarity="0.81">
<f n="test_install_codex_agents_windows_successful_temp_close_failure_returns_cleanup_evidence" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:4993"/>
<f n="test_install_codex_agents_windows_cleanup_records_close_failure_after_successful_handle_delete" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5250"/>
</group>
<group type="3" gid="343" tokens="258" n="2" similarity="0.85">
<f n="test_install_codex_agents_windows_cleanup_handle_delete_preserves_final_takeover" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5062"/>
<f n="test_install_codex_agents_windows_cleanup_result_records_close_failure_without_collector" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5215"/>
</group>
<group type="3" gid="343" tokens="400" n="2" similarity="0.92">
<f n="test_install_codex_agents_windows_cleanup_unreadable_after_delete_failure_is_concurrent_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5104"/>
<f n="test_install_codex_agents_windows_cleanup_moved_state_mismatch_reports_cleanup_and_recreated_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5157"/>
</group>
<group type="3" gid="343" tokens="343" n="2" similarity="0.80">
<f n="test_install_codex_agents_windows_cleanup_unreadable_after_delete_failure_is_concurrent_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5104"/>
<f n="test_install_codex_agents_windows_cleanup_records_close_failure_after_successful_handle_delete" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5250"/>
</group>
<group type="3" gid="343" tokens="378" n="2" similarity="0.81">
<f n="test_install_codex_agents_windows_cleanup_unreadable_after_delete_failure_is_concurrent_unknown" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5104"/>
<f n="test_install_codex_agents_windows_cleanup_generic_rename_error_classifies_candidate_and_source" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5354"/>
</group>
<group type="3" gid="343" tokens="400" n="2" similarity="0.84">
<f n="test_install_codex_agents_windows_cleanup_moved_state_mismatch_reports_cleanup_and_recreated_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5157"/>
<f n="test_install_codex_agents_windows_cleanup_rename_close_failure_reports_recreated_source" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5291"/>
</group>
<group type="3" gid="343" tokens="400" n="2" similarity="0.86">
<f n="test_install_codex_agents_windows_cleanup_moved_state_mismatch_reports_cleanup_and_recreated_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5157"/>
<f n="test_install_codex_agents_windows_cleanup_generic_rename_error_classifies_candidate_and_source" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5354"/>
</group>
<group type="3" gid="343" tokens="314" n="2" similarity="0.86">
<f n="test_install_codex_agents_windows_cleanup_result_records_close_failure_without_collector" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5215"/>
<f n="test_install_codex_agents_windows_cleanup_records_close_failure_after_successful_handle_delete" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5250"/>
</group>
<group type="3" gid="343" tokens="376" n="2" similarity="0.80">
<f n="test_install_codex_agents_windows_cleanup_records_close_failure_after_successful_handle_delete" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5250"/>
<f n="test_install_codex_agents_windows_cleanup_rename_close_failure_reports_recreated_source" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5291"/>
</group>
<group type="3" gid="343" tokens="378" n="2" similarity="0.82">
<f n="test_install_codex_agents_windows_cleanup_records_close_failure_after_successful_handle_delete" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5250"/>
<f n="test_install_codex_agents_windows_cleanup_generic_rename_error_classifies_candidate_and_source" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5354"/>
</group>
<group type="3" gid="343" tokens="378" n="2" similarity="0.84">
<f n="test_install_codex_agents_windows_cleanup_rename_close_failure_reports_recreated_source" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5291"/>
<f n="test_install_codex_agents_windows_cleanup_generic_rename_error_classifies_candidate_and_source" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5354"/>
</group>
<group type="3" gid="343" tokens="171" n="2" similarity="0.87">
<f n="test_install_codex_agents_windows_write_apply_does_not_fail_on_nt_backend" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5498"/>
<f n="test_install_codex_agents_windows_directory_handle_outlives_backup_rename" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5609"/>
</group>
<group type="3" gid="349" tokens="200" n="2" similarity="0.80">
<f n="test_install_codex_agents_recovery_copy_precreate_failure_reports_no_phantom_path" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5835"/>
<f n="test_install_codex_agents_recovery_copy_close_errors_are_non_masking_and_exhaustive" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5864"/>
</group>
<group type="3" gid="350" tokens="170" n="2" similarity="0.91">
<f n="test_install_codex_agents_cleanup_refuses_replacement_destination_identity" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5998"/>
<f n="test_install_codex_agents_cleanup_enforces_created_parent_identity" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6101"/>
</group>
<group type="3" gid="350" tokens="167" n="2" similarity="0.88">
<f n="test_install_codex_agents_cleanup_refuses_replacement_destination_identity" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:5998"/>
<f n="test_install_codex_agents_cleanup_final_rmdir_swap_preserves_replacement_directory" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6128"/>
</group>
<group type="3" gid="350" tokens="274" n="2" similarity="0.83">
<f n="test_install_codex_agents_cleanup_directory_quarantine_uses_no_replace_move" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6023"/>
<f n="test_install_codex_agents_cleanup_directory_final_removal_fails_closed_on_quarantine_swap" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6063"/>
</group>
<group type="3" gid="350" tokens="228" n="2" similarity="0.84">
<f n="test_install_codex_agents_cleanup_directory_final_removal_fails_closed_on_quarantine_swap" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6063"/>
<f n="test_install_codex_agents_cleanup_final_rmdir_swap_preserves_replacement_directory" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6128"/>
</group>
<group type="3" gid="350" tokens="170" n="2" similarity="0.81">
<f n="test_install_codex_agents_cleanup_enforces_created_parent_identity" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6101"/>
<f n="test_install_codex_agents_cleanup_final_rmdir_swap_preserves_replacement_directory" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6128"/>
</group>
<group type="3" gid="342" tokens="461" n="2" similarity="0.83">
<f n="test_install_codex_agents_route_aware_refuses_concurrent_edit_before_write" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6181"/>
<f n="test_install_codex_agents_route_aware_rollback_preserves_concurrent_edit" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6242"/>
</group>
<group type="3" gid="341" tokens="182" n="2" similarity="0.95">
<f n="test_install_codex_agents_route_aware_dry_run_omits_unavailable_helper_when_no_file_exists" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6321"/>
<f n="test_install_codex_agents_route_aware_apply_omits_unavailable_helper_and_installs_required_roster" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6353"/>
</group>
<group type="3" gid="341" tokens="182" n="2" similarity="0.85">
<f n="test_install_codex_agents_route_aware_dry_run_omits_unavailable_helper_when_no_file_exists" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6321"/>
<f n="test_install_codex_agents_strict_required_override_uses_one_tuple_per_required_agent" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6569"/>
</group>
<group type="3" gid="341" tokens="201" n="2" similarity="0.82">
<f n="test_install_codex_agents_route_aware_dry_run_omits_unavailable_helper_when_no_file_exists" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6321"/>
<f n="test_install_codex_agents_strict_helper_override_installs_compatible_helper" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6673"/>
</group>
<group type="3" gid="341" tokens="193" n="2" similarity="0.82">
<f n="test_install_codex_agents_route_aware_dry_run_omits_unavailable_helper_when_no_file_exists" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6321"/>
<f n="test_install_codex_agents_strict_helper_override_uses_valid_no_helper_without_helper_fallback" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6709"/>
</group>
<group type="3" gid="341" tokens="210" n="2" similarity="0.83">
<f n="test_install_codex_agents_route_aware_dry_run_omits_unavailable_helper_when_no_file_exists" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6321"/>
<f n="test_install_codex_agents_strict_helper_override_invalid_no_helper_fails_before_mutation" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6739"/>
</group>
<group type="3" gid="341" tokens="175" n="2" similarity="0.83">
<f n="test_install_codex_agents_route_aware_apply_omits_unavailable_helper_and_installs_required_roster" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6353"/>
<f n="test_install_codex_agents_strict_required_override_uses_one_tuple_per_required_agent" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6569"/>
</group>
<group type="3" gid="341" tokens="193" n="2" similarity="0.81">
<f n="test_install_codex_agents_route_aware_apply_omits_unavailable_helper_and_installs_required_roster" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6353"/>
<f n="test_install_codex_agents_strict_helper_override_uses_valid_no_helper_without_helper_fallback" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6709"/>
</group>
<group type="3" gid="341" tokens="210" n="2" similarity="0.81">
<f n="test_install_codex_agents_route_aware_apply_omits_unavailable_helper_and_installs_required_roster" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6353"/>
<f n="test_install_codex_agents_strict_helper_override_invalid_no_helper_fails_before_mutation" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6739"/>
</group>
<group type="3" gid="341" tokens="201" n="2" similarity="0.86">
<f n="test_install_codex_agents_strict_required_override_uses_one_tuple_per_required_agent" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6569"/>
<f n="test_install_codex_agents_strict_helper_override_installs_compatible_helper" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6673"/>
</group>
<group type="3" gid="341" tokens="193" n="2" similarity="0.83">
<f n="test_install_codex_agents_strict_required_override_uses_one_tuple_per_required_agent" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6569"/>
<f n="test_install_codex_agents_strict_helper_override_uses_valid_no_helper_without_helper_fallback" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6709"/>
</group>
<group type="3" gid="341" tokens="210" n="2" similarity="0.83">
<f n="test_install_codex_agents_strict_required_override_uses_one_tuple_per_required_agent" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6569"/>
<f n="test_install_codex_agents_strict_helper_override_invalid_no_helper_fails_before_mutation" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6739"/>
</group>
<group type="3" gid="341" tokens="282" n="2" similarity="0.82">
<f n="test_install_codex_agents_strict_required_override_miss_reports_all_required_without_writes" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6596"/>
<f n="test_install_codex_agents_strict_helper_override_installs_compatible_helper" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6673"/>
</group>
<group type="3" gid="341" tokens="282" n="2" similarity="0.84">
<f n="test_install_codex_agents_strict_required_override_miss_reports_all_required_without_writes" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6596"/>
<f n="test_install_codex_agents_strict_helper_override_invalid_no_helper_fails_before_mutation" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6739"/>
</group>
<group type="3" gid="341" tokens="201" n="2" similarity="0.91">
<f n="test_install_codex_agents_strict_helper_override_installs_compatible_helper" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6673"/>
<f n="test_install_codex_agents_strict_helper_override_uses_valid_no_helper_without_helper_fallback" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6709"/>
</group>
<group type="3" gid="341" tokens="210" n="2" similarity="0.85">
<f n="test_install_codex_agents_strict_helper_override_installs_compatible_helper" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6673"/>
<f n="test_install_codex_agents_strict_helper_override_invalid_no_helper_fails_before_mutation" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:6739"/>
</group>
<group type="3" gid="340" tokens="113" n="2" similarity="0.80">
<f n="test_install_codex_agents_rejects_unrecognized_luna_fallback_env_value" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:7311"/>
<f n="test_doctor_repair_refuses_non_fake_home" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8755"/>
</group>
<group type="3" gid="340" tokens="95" n="2" similarity="0.88">
<f n="test_install_codex_agents_rejects_unrecognized_luna_fallback_env_value" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:7311"/>
<f n="test_doctor_repair_rejects_fake_home_outside_fixture_boundary" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8771"/>
</group>
<group type="3" gid="351" tokens="178" n="2" similarity="0.80">
<f n="test_dry_run_reports_planned_write_without_mutating" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:7642"/>
<f n="test_apply_writes_complete_file_with_final_newline" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:7672"/>
</group>
<group type="3" gid="351" tokens="178" n="2" similarity="0.80">
<f n="test_dry_run_reports_planned_write_without_mutating" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:7642"/>
<f n="test_apply_no_op_succeeds_without_touching_dirty_worktree" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:7984"/>
</group>
<group type="3" gid="351" tokens="163" n="2" similarity="0.81">
<f n="test_apply_writes_complete_file_with_final_newline" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:7672"/>
<f n="test_apply_no_op_succeeds_without_touching_dirty_worktree" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:7984"/>
</group>
<group type="3" gid="340" tokens="164" n="2" similarity="0.91">
<f n="test_apply_rejects_dirty_worktree_without_touching_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:7754"/>
<f n="test_apply_rejects_when_git_status_cannot_prove_clean_worktree" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:7955"/>
</group>
<group type="3" gid="340" tokens="164" n="2" similarity="0.88">
<f n="test_apply_rejects_dirty_worktree_without_touching_target" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:7754"/>
<f n="test_preflight_rejects_parent_file_before_apply_writes" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8048"/>
</group>
<group type="3" gid="249" tokens="266" n="2" similarity="0.80">
<f n="test_apply_rechecks_dirty_worktree_after_lock_acquisition" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:7873"/>
<f n="test_apply_rejects_target_swap_between_snapshot_and_replace" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8535"/>
</group>
<group type="3" gid="249" tokens="208" n="2" similarity="0.83">
<f n="test_apply_rechecks_dirty_worktree_after_lock_acquisition" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:7873"/>
<f n="test_apply_file_writes_fail_closed_on_unsupported_descriptor_platform" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8618"/>
</group>
<group type="3" gid="340" tokens="156" n="2" similarity="0.80">
<f n="test_apply_rejects_when_git_status_cannot_prove_clean_worktree" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:7955"/>
<f n="test_preflight_rejects_parent_file_before_apply_writes" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8048"/>
</group>
<group type="3" gid="340" tokens="156" n="2" similarity="0.81">
<f n="test_apply_rejects_when_git_status_cannot_prove_clean_worktree" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:7955"/>
<f n="test_doctor_repair_rejects_backslash_traversal_inventory_path" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8786"/>
</group>
<group type="3" gid="340" tokens="133" n="2" similarity="0.83">
<f n="test_preflight_rejects_parent_file_before_apply_writes" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8048"/>
<f n="test_apply_write_respects_umask_for_new_files" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8239"/>
</group>
<group type="3" gid="340" tokens="154" n="2" similarity="0.81">
<f n="test_preflight_rejects_parent_file_before_apply_writes" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8048"/>
<f n="test_doctor_repair_rejects_backslash_traversal_inventory_path" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8786"/>
</group>
<group type="3" gid="352" tokens="192" n="2" similarity="0.83">
<f n="test_post_write_snapshot_rejects_concurrent_replacement" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8329"/>
<f n="test_rollback_preserves_parent_created_after_snapshot" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8355"/>
</group>
<group type="3" gid="249" tokens="297" n="2" similarity="0.80">
<f n="test_apply_cleans_parent_created_before_traversal_failure" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8449"/>
<f n="test_apply_reports_temp_unlink_failure_after_failed_replace" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8488"/>
</group>
<group type="3" gid="249" tokens="215" n="2" similarity="0.81">
<f n="test_apply_cleans_parent_created_before_traversal_failure" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8449"/>
<f n="test_write_failure_cleanup_errors_mark_writes_state" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8582"/>
</group>
<group type="3" gid="249" tokens="196" n="2" similarity="0.90">
<f n="test_write_failure_cleanup_errors_mark_writes_state" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8582"/>
<f n="test_apply_file_writes_fail_closed_on_unsupported_descriptor_platform" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8618"/>
</group>
<group type="3" gid="340" tokens="113" n="2" similarity="0.87">
<f n="test_doctor_repair_refuses_non_fake_home" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8755"/>
<f n="test_doctor_repair_rejects_fake_home_outside_fixture_boundary" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8771"/>
</group>
<group type="3" gid="340" tokens="154" n="2" similarity="0.85">
<f n="test_doctor_repair_refuses_non_fake_home" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8755"/>
<f n="test_doctor_repair_rejects_backslash_traversal_inventory_path" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8786"/>
</group>
<group type="3" gid="353" tokens="231" n="2" similarity="0.84">
<f n="test_validate_agent_install_detects_missing_unexpected_nonregular_and_symlink" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:329"/>
<f n="test_validate_agent_install_accepts_valid_external_package" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:357"/>
</group>
<group type="3" gid="354" tokens="189" n="2" similarity="0.85">
<f n="test_path_boundary_rejects_traversal_and_symlink_escape" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:886"/>
<f n="test_repo_root_symlink_escape_is_rejected" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1521"/>
</group>
<group type="3" gid="354" tokens="189" n="2" similarity="0.80">
<f n="test_path_boundary_rejects_traversal_and_symlink_escape" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:886"/>
<f n="test_generate_spec_index_ignores_symlinked_spec_children" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2158"/>
</group>
<group type="3" gid="355" tokens="183" n="2" similarity="0.92">
<f n="test_registered_worktree_entries_ignores_only_explicitly_prunable_entries" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1297"/>
<f n="test_registered_worktree_entries_fails_closed_on_unreadable_registered_entry" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1324"/>
</group>
<group type="3" gid="356" tokens="183" n="2" similarity="0.87">
<f n="test_resolve_workflow_binding_rejects_external_symlink_alias_into_worktree" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1380"/>
<f n="test_resolve_workflow_binding_allows_in_worktree_symlink_with_same_owner" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1401"/>
</group>
<group type="3" gid="354" tokens="173" n="2" similarity="0.86">
<f n="test_explicit_repo_root_cannot_redefine_trust_boundary" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1507"/>
<f n="test_repo_root_symlink_escape_is_rejected" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1521"/>
</group>
<group type="3" gid="354" tokens="173" n="2" similarity="0.82">
<f n="test_repo_root_symlink_escape_is_rejected" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1521"/>
<f n="test_generate_spec_index_ignores_symlinked_spec_children" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2158"/>
</group>
<group type="3" gid="357" tokens="103" n="2" similarity="0.96">
<f n="test_find_repo_root_rejects_symlinked_plugin_anchor" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1541"/>
<f n="test_find_repo_root_rejects_symlinked_specify_anchor" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1595"/>
</group>
<group type="3" gid="357" tokens="103" n="2" similarity="0.82">
<f n="test_find_repo_root_rejects_symlinked_plugin_anchor" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1541"/>
<f n="test_git_branch_rejects_untrusted_gitdir_pointer" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3136"/>
</group>
<group type="3" gid="357" tokens="106" n="2" similarity="0.90">
<f n="test_find_repo_root_rejects_symlinked_plugin_anchor" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1541"/>
<f n="test_git_branch_rejects_symlinked_git_paths" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4053"/>
</group>
<group type="3" gid="357" tokens="116" n="2" similarity="0.86">
<f n="test_find_repo_root_rejects_symlinked_plugin_anchor" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1541"/>
<f n="test_git_branch_rejects_symlinked_head_escape" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4080"/>
</group>
<group type="3" gid="357" tokens="94" n="2" similarity="0.92">
<f n="test_find_repo_root_falls_back_to_specify_project_root" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1556"/>
<f n="test_find_repo_root_prefers_nearest_specify_anchor_over_ancestor_runner" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1568"/>
</group>
<group type="3" gid="357" tokens="94" n="2" similarity="0.92">
<f n="test_find_repo_root_falls_back_to_specify_project_root" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1556"/>
<f n="test_find_repo_root_prefers_vendored_runner_over_specify_fallback" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1581"/>
</group>
<group type="3" gid="357" tokens="83" n="2" similarity="0.82">
<f n="test_find_repo_root_falls_back_to_specify_project_root" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1556"/>
<f n="test_git_branch_reports_head_for_detached_checkout" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4068"/>
</group>
<group type="3" gid="357" tokens="94" n="2" similarity="0.81">
<f n="test_find_repo_root_falls_back_to_specify_project_root" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1556"/>
<f n="test_repo_root_for_specs_path_uses_rightmost_specs_segment" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4097"/>
</group>
<group type="3" gid="357" tokens="94" n="2" similarity="0.87">
<f n="test_find_repo_root_prefers_nearest_specify_anchor_over_ancestor_runner" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1568"/>
<f n="test_find_repo_root_prefers_vendored_runner_over_specify_fallback" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1581"/>
</group>
<group type="3" gid="357" tokens="94" n="2" similarity="0.80">
<f n="test_find_repo_root_prefers_nearest_specify_anchor_over_ancestor_runner" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1568"/>
<f n="test_git_branch_reports_head_for_detached_checkout" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4068"/>
</group>
<group type="3" gid="357" tokens="94" n="2" similarity="0.81">
<f n="test_find_repo_root_prefers_vendored_runner_over_specify_fallback" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1581"/>
<f n="test_git_branch_reports_head_for_detached_checkout" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4068"/>
</group>
<group type="3" gid="357" tokens="96" n="2" similarity="0.85">
<f n="test_find_repo_root_rejects_symlinked_specify_anchor" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1595"/>
<f n="test_git_branch_rejects_untrusted_gitdir_pointer" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3136"/>
</group>
<group type="3" gid="357" tokens="106" n="2" similarity="0.91">
<f n="test_find_repo_root_rejects_symlinked_specify_anchor" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1595"/>
<f n="test_git_branch_rejects_symlinked_git_paths" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4053"/>
</group>
<group type="3" gid="357" tokens="116" n="2" similarity="0.87">
<f n="test_find_repo_root_rejects_symlinked_specify_anchor" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1595"/>
<f n="test_git_branch_rejects_symlinked_head_escape" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4080"/>
</group>
<group type="3" gid="358" tokens="186" n="2" similarity="0.94">
<f n="test_detect_commands_defaults_package_json_only_node_to_npm" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1705"/>
<f n="test_detect_commands_reads_text_bun_lock_as_bun" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1722"/>
</group>
<group type="3" gid="358" tokens="186" n="2" similarity="0.83">
<f n="test_detect_commands_reads_text_bun_lock_as_bun" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1722"/>
<f n="test_promoted_helper_runs_without_bash_on_path" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4231"/>
</group>
<group type="3" gid="359" tokens="134" n="2" similarity="0.81">
<f n="test_confidence_gate_computes_composite_from_criterion_mean" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1948"/>
<f n="test_confidence_gate_ignores_the_severity_legend_table" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2042"/>
</group>
<group type="3" gid="359" tokens="134" n="2" similarity="0.85">
<f n="test_confidence_gate_computes_composite_from_criterion_mean" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1948"/>
<f n="test_confidence_gate_falls_back_to_the_stated_line_without_criteria" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2081"/>
</group>
<group type="3" gid="359" tokens="134" n="2" similarity="0.82">
<f n="test_confidence_gate_computes_composite_from_criterion_mean" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1948"/>
<f n="test_confidence_gate_surfaces_a_stated_versus_computed_mismatch" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2110"/>
</group>
<group type="3" gid="359" tokens="100" n="2" similarity="0.82">
<f n="test_confidence_gate_rounds_the_criterion_mean_to_two_decimals" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1961"/>
<f n="test_confidence_gate_ignores_the_severity_legend_table" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2042"/>
</group>
<group type="3" gid="359" tokens="85" n="2" similarity="0.84">
<f n="test_confidence_gate_rounds_the_criterion_mean_to_two_decimals" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1961"/>
<f n="test_confidence_gate_reports_no_data_without_either_source" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2121"/>
</group>
<group type="3" gid="359" tokens="140" n="2" similarity="0.88">
<f n="test_confidence_gate_stops_deducting_once_the_resolution_cell_is_filled" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1994"/>
<f n="test_confidence_gate_ignores_unresolved_medium_and_low_rows" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2011"/>
</group>
<group type="3" gid="359" tokens="150" n="2" similarity="0.88">
<f n="test_confidence_gate_stops_deducting_once_the_resolution_cell_is_filled" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1994"/>
<f n="test_confidence_gate_ignores_bracket_severity_prose_in_the_log" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2022"/>
</group>
<group type="3" gid="359" tokens="140" n="2" similarity="0.82">
<f n="test_confidence_gate_stops_deducting_once_the_resolution_cell_is_filled" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1994"/>
<f n="test_confidence_gate_ignores_the_severity_legend_table" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2042"/>
</group>
<group type="3" gid="359" tokens="140" n="2" similarity="0.85">
<f n="test_confidence_gate_stops_deducting_once_the_resolution_cell_is_filled" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:1994"/>
<f n="test_confidence_gate_floors_the_composite_at_zero" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2068"/>
</group>
<group type="3" gid="359" tokens="110" n="2" similarity="0.83">
<f n="test_confidence_gate_ignores_unresolved_medium_and_low_rows" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2011"/>
<f n="test_confidence_gate_ignores_the_severity_legend_table" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2042"/>
</group>
<group type="3" gid="359" tokens="127" n="2" similarity="0.84">
<f n="test_confidence_gate_ignores_unresolved_medium_and_low_rows" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2011"/>
<f n="test_confidence_gate_reads_only_the_most_recent_analysis_table" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2053"/>
</group>
<group type="3" gid="359" tokens="122" n="2" similarity="0.80">
<f n="test_confidence_gate_ignores_unresolved_medium_and_low_rows" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2011"/>
<f n="test_confidence_gate_floors_the_composite_at_zero" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2068"/>
</group>
<group type="3" gid="359" tokens="100" n="2" similarity="0.83">
<f n="test_confidence_gate_ignores_the_severity_legend_table" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2042"/>
<f n="test_confidence_gate_reads_a_deduction_as_agreement_not_mismatch" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2095"/>
</group>
<group type="3" gid="359" tokens="126" n="2" similarity="0.83">
<f n="test_confidence_gate_falls_back_to_the_stated_line_without_criteria" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2081"/>
<f n="test_confidence_gate_surfaces_a_stated_versus_computed_mismatch" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2110"/>
</group>
<group type="3" gid="360" tokens="196" n="2" similarity="0.83">
<f n="test_validate_pr_packet_reports_oversized_json_integer_as_input_error" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2244"/>
<f n="test_validate_pr_packet_rejects_validation_result_path_not_owned_by_packet" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2474"/>
</group>
<group type="3" gid="360" tokens="196" n="2" similarity="0.84">
<f n="test_validate_pr_packet_reports_oversized_json_integer_as_input_error" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2244"/>
<f n="test_validate_pr_packet_rejects_packet_id_that_disagrees_with_filename" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2672"/>
</group>
<group type="3" gid="360" tokens="203" n="2" similarity="0.81">
<f n="test_validate_pr_packet_rejects_schema_minimal_false_pass" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2271"/>
<f n="test_validate_pr_packet_rejects_packet_id_that_disagrees_with_filename" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2672"/>
</group>
<group type="3" gid="360" tokens="188" n="2" similarity="0.98">
<f n="test_validate_pr_packet_rejects_validation_result_path_not_owned_by_packet" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2474"/>
<f n="test_validate_pr_packet_rejects_packet_id_that_disagrees_with_filename" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2672"/>
</group>
<group type="3" gid="361" tokens="135" n="2" similarity="0.82">
<f n="test_validate_pr_packet_rejects_draft_that_carries_split_slice" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2851"/>
<f n="test_validate_pr_packet_still_rejects_an_unknown_mode_value" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2961"/>
</group>
<group type="3" gid="361" tokens="116" n="2" similarity="0.97">
<f n="test_validate_pr_packet_rejects_draft_that_carries_split_slice" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2851"/>
<f n="test_validate_pr_packet_rejects_draft_that_declares_editable_fields" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3021"/>
</group>
<group type="3" gid="361" tokens="126" n="2" similarity="0.88">
<f n="test_validate_pr_packet_rejects_draft_that_carries_split_slice" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2851"/>
<f n="test_validate_pr_packet_still_rejects_single_required_headings_that_are_not_reviewer_set" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3043"/>
</group>
<group type="3" gid="361" tokens="135" n="2" similarity="0.80">
<f n="test_validate_pr_packet_still_rejects_an_unknown_mode_value" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2961"/>
<f n="test_validate_pr_packet_rejects_draft_that_declares_editable_fields" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3021"/>
</group>
<group type="3" gid="361" tokens="135" n="2" similarity="0.86">
<f n="test_validate_pr_packet_still_rejects_an_unknown_mode_value" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:2961"/>
<f n="test_validate_pr_packet_still_rejects_single_required_headings_that_are_not_reviewer_set" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3043"/>
</group>
<group type="3" gid="361" tokens="126" n="2" similarity="0.88">
<f n="test_validate_pr_packet_rejects_draft_that_declares_editable_fields" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3021"/>
<f n="test_validate_pr_packet_still_rejects_single_required_headings_that_are_not_reviewer_set" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3043"/>
</group>
<group type="3" gid="362" tokens="120" n="2" similarity="0.83">
<f n="test_validate_pr_workflow_contract_unreadable_changed_files_is_input_error" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3098"/>
<f n="test_validate_pr_workflow_contract_matches_bash_when_origin_main_is_missing" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3119"/>
</group>
<group type="3" gid="362" tokens="87" n="2" similarity="0.83">
<f n="test_validate_pr_workflow_contract_matches_bash_when_origin_main_is_missing" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3119"/>
<f n="test_claude_subagent_runtime_rejects_unknown_execution_mode" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4215"/>
</group>
<group type="3" gid="357" tokens="93" n="2" similarity="0.91">
<f n="test_git_branch_rejects_untrusted_gitdir_pointer" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3136"/>
<f n="test_git_branch_accepts_worktree_named_for_its_branch" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3178"/>
</group>
<group type="3" gid="357" tokens="97" n="2" similarity="0.89">
<f n="test_git_branch_rejects_untrusted_gitdir_pointer" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3136"/>
<f n="test_git_branch_accepts_same_repo_worktree_metadata_name" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3198"/>
</group>
<group type="3" gid="357" tokens="99" n="2" similarity="0.87">
<f n="test_git_branch_rejects_untrusted_gitdir_pointer" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3136"/>
<f n="test_git_branch_rejects_worktree_metadata_without_backpointer" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3213"/>
</group>
<group type="3" gid="357" tokens="105" n="2" similarity="0.86">
<f n="test_git_branch_rejects_untrusted_gitdir_pointer" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3136"/>
<f n="test_git_branch_rejects_worktree_metadata_pointing_elsewhere" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3234"/>
</group>
<group type="3" gid="357" tokens="106" n="2" similarity="0.85">
<f n="test_git_branch_rejects_untrusted_gitdir_pointer" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3136"/>
<f n="test_git_branch_rejects_symlinked_git_paths" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4053"/>
</group>
<group type="3" gid="357" tokens="83" n="2" similarity="0.91">
<f n="test_git_branch_rejects_untrusted_gitdir_pointer" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3136"/>
<f n="test_git_branch_reports_head_for_detached_checkout" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4068"/>
</group>
<group type="3" gid="357" tokens="116" n="2" similarity="0.81">
<f n="test_git_branch_rejects_untrusted_gitdir_pointer" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3136"/>
<f n="test_git_branch_rejects_symlinked_head_escape" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4080"/>
</group>
<group type="3" gid="357" tokens="97" n="2" similarity="0.95">
<f n="test_git_branch_accepts_worktree_named_for_its_branch" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3178"/>
<f n="test_git_branch_accepts_same_repo_worktree_metadata_name" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3198"/>
</group>
<group type="3" gid="357" tokens="99" n="2" similarity="0.96">
<f n="test_git_branch_accepts_worktree_named_for_its_branch" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3178"/>
<f n="test_git_branch_rejects_worktree_metadata_without_backpointer" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3213"/>
</group>
<group type="3" gid="357" tokens="105" n="2" similarity="0.91">
<f n="test_git_branch_accepts_worktree_named_for_its_branch" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3178"/>
<f n="test_git_branch_rejects_worktree_metadata_pointing_elsewhere" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3234"/>
</group>
<group type="3" gid="357" tokens="106" n="2" similarity="0.82">
<f n="test_git_branch_accepts_worktree_named_for_its_branch" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3178"/>
<f n="test_git_branch_rejects_symlinked_git_paths" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4053"/>
</group>
<group type="3" gid="357" tokens="93" n="2" similarity="0.83">
<f n="test_git_branch_accepts_worktree_named_for_its_branch" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3178"/>
<f n="test_git_branch_reports_head_for_detached_checkout" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4068"/>
</group>
<group type="3" gid="357" tokens="99" n="2" similarity="0.97">
<f n="test_git_branch_accepts_same_repo_worktree_metadata_name" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3198"/>
<f n="test_git_branch_rejects_worktree_metadata_without_backpointer" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3213"/>
</group>
<group type="3" gid="357" tokens="105" n="2" similarity="0.96">
<f n="test_git_branch_accepts_same_repo_worktree_metadata_name" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3198"/>
<f n="test_git_branch_rejects_worktree_metadata_pointing_elsewhere" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3234"/>
</group>
<group type="3" gid="357" tokens="106" n="2" similarity="0.84">
<f n="test_git_branch_accepts_same_repo_worktree_metadata_name" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3198"/>
<f n="test_git_branch_rejects_symlinked_git_paths" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4053"/>
</group>
<group type="3" gid="357" tokens="97" n="2" similarity="0.82">
<f n="test_git_branch_accepts_same_repo_worktree_metadata_name" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3198"/>
<f n="test_git_branch_reports_head_for_detached_checkout" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4068"/>
</group>
<group type="3" gid="357" tokens="116" n="2" similarity="0.81">
<f n="test_git_branch_accepts_same_repo_worktree_metadata_name" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3198"/>
<f n="test_git_branch_rejects_symlinked_head_escape" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4080"/>
</group>
<group type="3" gid="357" tokens="105" n="2" similarity="0.93">
<f n="test_git_branch_rejects_worktree_metadata_without_backpointer" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3213"/>
<f n="test_git_branch_rejects_worktree_metadata_pointing_elsewhere" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3234"/>
</group>
<group type="3" gid="357" tokens="106" n="2" similarity="0.81">
<f n="test_git_branch_rejects_worktree_metadata_without_backpointer" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3213"/>
<f n="test_git_branch_rejects_symlinked_git_paths" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4053"/>
</group>
<group type="3" gid="357" tokens="99" n="2" similarity="0.80">
<f n="test_git_branch_rejects_worktree_metadata_without_backpointer" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3213"/>
<f n="test_git_branch_reports_head_for_detached_checkout" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4068"/>
</group>
<group type="3" gid="357" tokens="106" n="2" similarity="0.81">
<f n="test_git_branch_rejects_worktree_metadata_pointing_elsewhere" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3234"/>
<f n="test_git_branch_rejects_symlinked_git_paths" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4053"/>
</group>
<group type="3" gid="357" tokens="105" n="2" similarity="0.81">
<f n="test_git_branch_rejects_worktree_metadata_pointing_elsewhere" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3234"/>
<f n="test_git_branch_reports_head_for_detached_checkout" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4068"/>
</group>
<group type="3" gid="357" tokens="93" n="2" similarity="0.88">
<f n="test_check_prerequisites_honors_feature_json_feature_directory" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3256"/>
<f n="test_check_prerequisites_honors_specify_feature_directory_env" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3379"/>
</group>
<group type="3" gid="357" tokens="93" n="2" similarity="0.82">
<f n="test_check_prerequisites_honors_feature_json_feature_directory" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3256"/>
<f n="test_git_branch_reports_head_for_detached_checkout" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4068"/>
</group>
<group type="3" gid="357" tokens="110" n="2" similarity="0.82">
<f n="test_check_prerequisites_honors_specify_feature_directory_env" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3379"/>
<f n="test_check_prerequisites_reports_no_feature_without_state_or_branch" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3391"/>
</group>
<group type="3" gid="357" tokens="134" n="2" similarity="0.90">
<f n="test_check_prerequisites_reports_no_feature_without_state_or_branch" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3391"/>
<f n="test_check_prerequisites_ignores_blank_feature_directory" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3406"/>
</group>
<group type="3" gid="363" tokens="176" n="2" similarity="0.84">
<f n="test_validate_gate_g5_rejects_a_gate_task_that_waits_on_its_dependents" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3517"/>
<f n="test_validate_gate_g5_fails_empty_requirement_coverage_rows" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3627"/>
</group>
<group type="3" gid="364" tokens="185" n="2" similarity="0.89">
<f n="test_estimate_reviewable_loc_does_not_count_marker_evidence_toward_the_path_budget" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3782"/>
<f n="test_estimate_reviewable_loc_does_not_count_the_implementation_notes_record" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3808"/>
</group>
<group type="3" gid="365" tokens="130" n="2" similarity="0.83">
<f n="test_detect_commands_prefers_root_marker_over_runner_script" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3863"/>
<f n="test_detect_commands_runner_discovery_is_deterministic" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:3987"/>
</group>
<group type="3" gid="357" tokens="106" n="2" similarity="0.85">
<f n="test_git_branch_rejects_symlinked_git_paths" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4053"/>
<f n="test_git_branch_reports_head_for_detached_checkout" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4068"/>
</group>
<group type="3" gid="357" tokens="116" n="2" similarity="0.95">
<f n="test_git_branch_rejects_symlinked_git_paths" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4053"/>
<f n="test_git_branch_rejects_symlinked_head_escape" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4080"/>
</group>
<group type="3" gid="357" tokens="116" n="2" similarity="0.82">
<f n="test_git_branch_reports_head_for_detached_checkout" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4068"/>
<f n="test_git_branch_rejects_symlinked_head_escape" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4080"/>
</group>
<group type="3" gid="366" tokens="64" n="2" similarity="0.95">
<f n="test_count_markers_modes_match_bash_reference" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4250"/>
<f n="test_validate_gate_modes_match_bash_reference" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:4260"/>
</group>
```

## churn-decay (26 lines)

```xml
<recent n="40" of="1331" merge_bombs_skipped="5">
<rc p="speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json" age_d="0" w="166"/>
<rc p="speckit-pro/speckit_pro_runner/helpers/read_only.py" age_d="0" w="41.9"/>
<rc p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py" age_d="0" w="36.7"/>
<rc p="speckit-pro/speckit_pro_runner/helpers/registry.py" age_d="0" w="23.8"/>
<rc p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py" age_d="0" w="21.1"/>
<rc p="tests/speckit-pro/unit/fixtures/read-only-helpers/fixture-manifest.json" age_d="0" w="14"/>
</recent>
<f p="tests/speckit-pro/unit/test-speckit-pro-gates.py" layer="test">
</f>
<f p="speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json">
</f>
<f p="speckit-pro/speckit_pro_runner/helpers/registry.py">
</f>
<f p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py" layer="test">
</f>
<f p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py">
</f>
<f p="speckit-pro/speckit_pro_runner/envelope.py">
</f>
<f p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py" layer="test">
</f>
<f p="speckit-pro/speckit_pro_runner/helpers/read_only.py">
</f>
<f p="speckit-pro/speckit_pro_runner/gates/registry.py">
</f>
```

## arch (15 lines)

```xml
<v from="./speckit-pro/speckit_pro_runner/author_broker.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/mutation.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/author_broker.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/read_only.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/execution_control.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/read_only.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/execution_control.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/read_only.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/execution_control.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/read_only.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/execution_control.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/read_only.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/helpers/read_only.py" fromLayer="helpers" to="./speckit-pro/speckit_pro_runner/runtime.py" toLayer="entry" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/sweep_isolation.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/mutation.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/sweep_isolation.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/read_only.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/sweep_isolation.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/read_only.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/task_results.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/mutation.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/task_results.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/mutation.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/task_results.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/mutation.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/task_results.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/read_only.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/task_results.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/read_only.py" toLayer="helpers" baselined="1"/>
```

## deps (33 lines)

```xml
<godfiles total="92" shown="12" capped="1">
<f p="speckit-pro/speckit_pro_runner/envelope.py" afferent="21"/>
<f p="speckit-pro/speckit_pro_runner/helpers/read_only.py" afferent="16"/>
<f p="speckit-pro/speckit_pro_runner/helpers/mutation.py" afferent="8"/>
<f p="speckit-pro/speckit_pro_runner/__init__.py" afferent="7"/>
<f p="speckit-pro/speckit_pro_runner/path_utils.py" afferent="6"/>
</godfiles>
<stabledeps violations="26">
<v from="speckit-pro/speckit_pro_runner/helpers/read_only.py" to="speckit-pro/speckit_pro_runner/author_broker.py" gap="0.26"/>
<v from="speckit-pro/speckit_pro_runner/helpers/mutation.py" to="speckit-pro/speckit_pro_runner/execution_control.py" gap="0.23"/>
<v from="speckit-pro/speckit_pro_runner/runtime.py" to="speckit-pro/speckit_pro_runner/helpers/registry.py" gap="0.22"/>
<v from="speckit-pro/speckit_pro_runner/helpers/mutation.py" to="speckit-pro/speckit_pro_runner/helpers/read_only.py" gap="0.21"/>
<v from="speckit-pro/speckit_pro_runner/helpers/read_only.py" to="speckit-pro/speckit_pro_runner/runtime.py" gap="0.17"/>
<v from="speckit-pro/speckit_pro_runner/sweep_isolation.py" to="speckit-pro/speckit_pro_runner/helpers/read_only.py" gap="0.17"/>
</stabledeps>
<cycle size="20" cost="400" cut="speckit-pro/speckit_pro_runner/author_broker.py -&gt; speckit-pro/speckit_pro_runner/helpers/mutation.py" cutrefs="1">
<f p="speckit-pro/speckit_pro_runner/helpers/gate_preflight_coverage.py"/>
<f p="speckit-pro/speckit_pro_runner/helpers/registry.py"/>
</cycle>
<f p="speckit-pro/speckit_pro_runner/__main__.py" includes="4" afferent="0" instab="1.00" transitive="59">
</f>
<f p="speckit-pro/speckit_pro_runner/gates/registry.py" includes="8" afferent="1" instab="0.86" transitive="58">
</f>
<f p="speckit-pro/speckit_pro_runner/helpers/gate_preflight_coverage.py" includes="5" afferent="1" instab="0.67" transitive="58">
</f>
<f p="speckit-pro/speckit_pro_runner/helpers/mutation.py" includes="14" afferent="8" instab="0.33" transitive="58">
</f>
<f p="speckit-pro/speckit_pro_runner/helpers/read_only.py" includes="33" afferent="16" instab="0.54" transitive="58">
</f>
<f p="speckit-pro/speckit_pro_runner/helpers/registry.py" includes="16" afferent="1" instab="0.93" transitive="58">
</f>
<f p="speckit-pro/speckit_pro_runner/runtime.py" includes="12" afferent="2" instab="0.71" transitive="58">
</f>
```
