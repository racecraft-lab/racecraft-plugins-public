# Evidence for lane `native-eval-harness` (93 files)
Lines from the whole-repo scans that mention this lane's files. Empty section = none found, not none exists.

## doc-drift (26 lines)

```xml
<doc p="docs/ai/specs/.process/ART-006-design-concept.md" anchors="38" checked="15" drift="12" dated="1">
<a k="file-line" l="310" c="2" why="range-straddles" ref="tests/speckit-pro/unit/test-unit-layout.py:122-141" got="test_support_paths_are_purpose_named" tgt="tests/speckit-pro/unit/test-unit-layout.py:141"/>
<a k="file-line" l="388" c="4" why="range-straddles" kind="dated-record" rec="block" ref="tests/speckit-pro/unit/test-unit-layout.py:122-141" got="test_support_paths_are_purpose_named" tgt="tests/speckit-pro/unit/test-unit-layout.py:141"/>
<a k="file-line" l="412" c="46" why="range-straddles" ref="tests/speckit-pro/unit/test-unit-layout.py:273-294" got="(file scope)" tgt="tests/speckit-pro/unit/test-unit-layout.py:294"/>
</doc>
<doc p="docs/ai/specs/.process/G56R-006-workflow.md" anchors="12" checked="5" drift="4" dated="0">
<a k="const" l="285" c="105" why="const-value" ref="total_entries=55" want="55" got="0" tgt="tests/speckit-pro/lib/native_eval_claude_activation.py:519"/>
</doc>
<doc p="tests/speckit-pro/evals/audit/integration-parity-audit.md" anchors="24" checked="7" drift="3" dated="0">
</doc>
<doc p="tests/speckit-pro/evals/audit/unit-execution-contract-audit.md" anchors="5" checked="3" drift="2" dated="0">
</doc>
<doc p="docs/ai/specs/.process/TACD-003-workflow.md" anchors="12" checked="6" drift="1" dated="0">
<a k="const" l="376" c="17" why="const-value" ref="total_entries=8" want="8" got="0" tgt="tests/speckit-pro/lib/native_eval_claude_activation.py:519"/>
</doc>
<doc p="docs/ai/specs/.process/XPLAT-007-workflow.md" anchors="3" checked="2" drift="1" dated="0">
<a k="const" l="400" c="138" why="const-value" ref="total_entries=24" want="24" got="0" tgt="tests/speckit-pro/lib/native_eval_claude_activation.py:519"/>
</doc>
<doc p="tests/speckit-pro/evals/audit/unit-final-remainder-audit.md" anchors="7" checked="6" drift="1" dated="0">
</doc>
<doc p="tests/speckit-pro/evals/audit/functional-audit.md" anchors="22" checked="8" drift="0" dated="1">
</doc>
<weak-file-line p="tests/speckit-pro/evals/audit/unit-execution-contract-audit.md" n="2">
</weak-file-line>
<weak-file-line p="tests/speckit-pro/evals/audit/unit-remaining-support-audit.md" n="9">
</weak-file-line>
```

## clones (819 lines)

```xml
<group type="2" gid="139" tokens="104" n="4">
<f n="_strict_equal" p="tests/speckit-pro/lib/native_eval_execution.py:2228"/>
<f n="_strict_equal" p="tests/speckit-pro/lib/native_eval_grading.py:181"/>
<f n="_strict_equal" p="tests/speckit-pro/lib/native_eval_runner_result.py:124"/>
<f n="_strict_equal" p="tests/speckit-pro/lib/native_eval_verification.py:130"/>
</group>
<group type="2" gid="130" tokens="90" n="2">
<f n="_is_json_value" p="tests/speckit-pro/lib/native_eval_catalog.py:98"/>
<f n="_json_value" p="tests/speckit-pro/lib/native_eval_pairing.py:56"/>
</group>
<group type="2" gid="156" tokens="74" n="2">
<f n="_output_text" p="tests/speckit-pro/lib/native_eval_runner_result.py:145"/>
<f n="_output_text" p="tests/speckit-pro/lib/native_eval_verification.py:144"/>
</group>
<group type="2" gid="129" tokens="71" n="2">
<f n="_path" p="tests/speckit-pro/lib/native_eval_runner_result.py:39"/>
<f n="_path" p="tests/speckit-pro/lib/native_eval_verification.py:50"/>
</group>
<group type="2" gid="142" tokens="67" n="2">
<f n="_returned_content" p="tests/speckit-pro/lib/native_eval_execution.py:1988"/>
<f n="_returned_content" p="tests/speckit-pro/lib/native_eval_grading.py:439"/>
</group>
<group type="2" gid="134" tokens="60" n="2">
<f n="_loads" p="tests/speckit-pro/lib/native_eval_runner_result.py:113"/>
<f n="_loads" p="tests/speckit-pro/lib/native_eval_verification.py:119"/>
</group>
<group type="2" gid="122" tokens="55" n="2">
<f n="_codex_skill_name" p="tests/speckit-pro/lib/native_eval_adapters.py:469"/>
<f n="_skill_name" p="tests/speckit-pro/lib/native_eval_trigger.py:105"/>
</group>
<group type="2" gid="157" tokens="52" n="2">
<f n="attach_receipt" p="tests/speckit-pro/lib/native_eval_runner_result.py:322"/>
<f n="attach_receipt" p="tests/speckit-pro/lib/native_eval_verification.py:290"/>
</group>
<group type="2" gid="154" tokens="47" n="2">
<f n="runner_checks" p="tests/speckit-pro/lib/native_eval_runner_result.py:86"/>
<f n="verification_checks" p="tests/speckit-pro/lib/native_eval_verification.py:71"/>
</group>
<group type="2" gid="73" tokens="40" n="3">
<f n="skill_witness" p="tests/speckit-pro/unit/test-native-eval-codex-rollouts.py:459"/>
<f n="skill_witness" p="tests/speckit-pro/unit/test-native-eval-execution.py:48"/>
<f n="witness" p="tests/speckit-pro/unit/test-native-eval-skill-reads.py:33"/>
</group>
<group type="3" gid="73" tokens="40" n="2" similarity="0.80">
<f n="source_fingerprint" p="speckit-pro/speckit_pro_runner/helpers/pr_emission.py:316"/>
<f n="skill_witness" p="tests/speckit-pro/unit/test-native-eval-codex-rollouts.py:459"/>
</group>
<group type="3" gid="74" tokens="67" n="2" similarity="0.82">
<f n="validation_result_placeholder" p="speckit-pro/speckit_pro_runner/helpers/pr_emission.py:777"/>
<f n="check" p="tests/speckit-pro/unit/test-native-eval-runner-result.py:45"/>
</group>
<group type="3" gid="88" tokens="66" n="2" similarity="0.83">
<f n="string_list" p="speckit-pro/speckit_pro_runner/task_execution.py:125"/>
<f n="_nonempty_unique" p="tests/speckit-pro/run-native-evals.py:150"/>
</group>
<group type="3" gid="20" tokens="60" n="2" similarity="0.89">
<f n="load_coverage_validator" p="tests/speckit-pro/layer1-structural/validate-ci-release-contracts.py:1188"/>
<f n="import_script" p="tests/speckit-pro/unit/test-trigger-eval-runners.py:57"/>
</group>
<group type="3" gid="113" tokens="131" n="2" similarity="0.82">
<f n="parse_jsonl" p="tests/speckit-pro/layer3-functional/run-headless-evals.py:848"/>
<f n="_events" p="tests/speckit-pro/lib/native_eval_capture.py:297"/>
</group>
<group type="3" gid="121" tokens="44" n="2" similarity="0.93">
<f n="invariant_value" p="tests/speckit-pro/layer7-parity/run-parity-fixtures.py:263"/>
<f n="_invariant_text" p="tests/speckit-pro/lib/native_eval_pairing.py:451"/>
</group>
<group type="3" gid="20" tokens="90" n="2" similarity="0.81">
<f n="_codex_helpers" p="tests/speckit-pro/lib/native_eval_adapters.py:330"/>
<f n="load_gate_tests" p="tests/speckit-pro/unit/test-installed-release-gates.py:21"/>
</group>
<group type="3" gid="123" tokens="59" n="2" similarity="0.83">
<f n="_write_text" p="tests/speckit-pro/lib/native_eval_adapters.py:539"/>
<f n="_append_outputs" p="tests/speckit-pro/run-container-preflight.py:136"/>
</group>
<group type="3" gid="124" tokens="152" n="2" similarity="1.00">
<f n="_prepared_artifact_declarations" p="tests/speckit-pro/lib/native_eval_adapters.py:3482"/>
<f n="_prepared_verification_record_directories" p="tests/speckit-pro/lib/native_eval_adapters.py:3498"/>
</group>
<group type="3" gid="125" tokens="54" n="2" similarity="0.92">
<f n="_descriptor_capture_supported" p="tests/speckit-pro/lib/native_eval_adapters.py:3515"/>
<f n="_descriptor_collection_supported" p="tests/speckit-pro/lib/native_eval_claude_activation.py:447"/>
</group>
<group type="3" gid="126" tokens="98" n="2" similarity="0.96">
<f n="_atomic_write_once" p="tests/speckit-pro/lib/native_eval_adapters.py:3696"/>
<f n="_write_bytes_once" p="tests/speckit-pro/lib/native_eval_execution.py:101"/>
</group>
<group type="3" gid="127" tokens="66" n="2" similarity="0.86">
<f n="_codex_tokens" p="tests/speckit-pro/lib/native_eval_capture.py:83"/>
<f n="_tokens" p="tests/speckit-pro/lib/native_eval_fixture_reads.py:175"/>
</group>
<group type="3" gid="128" tokens="71" n="2" similarity="0.83">
<f n="_unique_text_list" p="tests/speckit-pro/lib/native_eval_catalog.py:72"/>
<f n="_filter_values" p="tests/speckit-pro/lib/native_eval_catalog.py:762"/>
</group>
<group type="3" gid="128" tokens="61" n="2" similarity="0.85">
<f n="_unique_text_list" p="tests/speckit-pro/lib/native_eval_catalog.py:72"/>
<f n="_paths" p="tests/speckit-pro/lib/native_eval_git_grading.py:41"/>
</group>
<group type="3" gid="128" tokens="61" n="2" similarity="0.87">
<f n="_unique_text_list" p="tests/speckit-pro/lib/native_eval_catalog.py:72"/>
<f n="_path_list" p="tests/speckit-pro/lib/native_eval_git_observation.py:1009"/>
</group>
<group type="3" gid="128" tokens="61" n="2" similarity="0.88">
<f n="_unique_text_list" p="tests/speckit-pro/lib/native_eval_catalog.py:72"/>
<f n="_unique_text_list" p="tests/speckit-pro/lib/native_eval_pairing.py:106"/>
</group>
<group type="3" gid="129" tokens="84" n="2" similarity="0.81">
<f n="_relative_path" p="tests/speckit-pro/lib/native_eval_catalog.py:80"/>
<f n="_absolute_posix_path" p="tests/speckit-pro/lib/native_eval_claude_activation.py:88"/>
</group>
<group type="3" gid="129" tokens="77" n="2" similarity="0.85">
<f n="_relative_path" p="tests/speckit-pro/lib/native_eval_catalog.py:80"/>
<f n="_relative_path" p="tests/speckit-pro/lib/native_eval_fixture_setup.py:32"/>
</group>
<group type="3" gid="129" tokens="79" n="2" similarity="0.90">
<f n="_relative_path" p="tests/speckit-pro/lib/native_eval_catalog.py:80"/>
<f n="_relative" p="tests/speckit-pro/lib/native_eval_pairing.py:46"/>
</group>
<group type="3" gid="129" tokens="72" n="2" similarity="0.87">
<f n="_relative_path" p="tests/speckit-pro/lib/native_eval_catalog.py:80"/>
<f n="_path" p="tests/speckit-pro/lib/native_eval_runner_result.py:39"/>
</group>
<group type="3" gid="131" tokens="142" n="2" similarity="0.82">
<f n="_validate_fixture" p="tests/speckit-pro/lib/native_eval_catalog.py:119"/>
<f n="_contract_path" p="tests/speckit-pro/lib/native_eval_pairing.py:80"/>
</group>
<group type="3" gid="132" tokens="57" n="2" similarity="0.92">
<f n="_validate_selection_check" p="tests/speckit-pro/lib/native_eval_catalog.py:224"/>
<f n="_validate_tool_order_check" p="tests/speckit-pro/lib/native_eval_catalog.py:283"/>
</group>
<group type="3" gid="133" tokens="161" n="2" similarity="0.82">
<f n="_validate_json_field_check" p="tests/speckit-pro/lib/native_eval_catalog.py:241"/>
<f n="_validate_response_json_field_check" p="tests/speckit-pro/lib/native_eval_catalog.py:257"/>
</group>
<group type="3" gid="134" tokens="85" n="2" similarity="0.85">
<f n="load_catalog" p="tests/speckit-pro/lib/native_eval_catalog.py:730"/>
<f n="_strict_json_evidence" p="tests/speckit-pro/lib/native_eval_execution.py:1545"/>
</group>
<group type="3" gid="134" tokens="80" n="2" similarity="0.91">
<f n="load_catalog" p="tests/speckit-pro/lib/native_eval_catalog.py:730"/>
<f n="_load_contract" p="tests/speckit-pro/lib/native_eval_pairing.py:93"/>
</group>
<group type="3" gid="134" tokens="79" n="2" similarity="0.81">
<f n="load_catalog" p="tests/speckit-pro/lib/native_eval_catalog.py:730"/>
<f n="_loads" p="tests/speckit-pro/lib/native_eval_runner_result.py:113"/>
</group>
<group type="3" gid="128" tokens="71" n="2" similarity="0.82">
<f n="_filter_values" p="tests/speckit-pro/lib/native_eval_catalog.py:762"/>
<f n="_path_list" p="tests/speckit-pro/lib/native_eval_git_observation.py:1009"/>
</group>
<group type="3" gid="129" tokens="84" n="2" similarity="0.83">
<f n="_absolute_posix_path" p="tests/speckit-pro/lib/native_eval_claude_activation.py:88"/>
<f n="_path" p="tests/speckit-pro/lib/native_eval_git_grading.py:31"/>
</group>
<group type="3" gid="129" tokens="84" n="2" similarity="0.83">
<f n="_absolute_posix_path" p="tests/speckit-pro/lib/native_eval_claude_activation.py:88"/>
<f n="_path" p="tests/speckit-pro/lib/native_eval_runner_result.py:39"/>
</group>
<group type="3" gid="135" tokens="55" n="2" similarity="0.92">
<f n="_json_line" p="tests/speckit-pro/lib/native_eval_claude_activation.py:124"/>
<f n="_loads" p="tests/speckit-pro/lib/native_eval_codex_rollouts.py:125"/>
</group>
<group type="3" gid="136" tokens="76" n="2" similarity="0.81">
<f n="_opaque" p="tests/speckit-pro/lib/native_eval_codex_rollouts.py:814"/>
<f n="controller_git_metadata" p="tests/speckit-pro/unit/test-native-parity-catalog.py:74"/>
</group>
<group type="3" gid="137" tokens="296" n="2" similarity="0.89">
<f n="_skill_witnesses" p="tests/speckit-pro/lib/native_eval_codex_rollouts.py:851"/>
<f n="_witnesses" p="tests/speckit-pro/lib/native_eval_skill_reads.py:70"/>
</group>
<group type="3" gid="138" tokens="381" n="2" similarity="0.90">
<f n="collect_native_tree" p="tests/speckit-pro/lib/native_eval_codex_rollouts.py:2465"/>
<f n="collect_native_skill_injections" p="tests/speckit-pro/lib/native_eval_codex_rollouts.py:2531"/>
</group>
<group type="3" gid="139" tokens="107" n="2" similarity="0.90">
<f n="_json_equal" p="tests/speckit-pro/lib/native_eval_dispatch_context.py:109"/>
<f n="_strict_equal" p="tests/speckit-pro/lib/native_eval_execution.py:2228"/>
</group>
<group type="3" gid="134" tokens="85" n="2" similarity="0.91">
<f n="_strict_json_evidence" p="tests/speckit-pro/lib/native_eval_execution.py:1545"/>
<f n="_load_contract" p="tests/speckit-pro/lib/native_eval_pairing.py:93"/>
</group>
<group type="3" gid="140" tokens="59" n="2" similarity="0.83">
<f n="_codex_root_thread" p="tests/speckit-pro/lib/native_eval_execution.py:1830"/>
<f n="skill_witnesses" p="tests/speckit-pro/lib/native_eval_upstream.py:264"/>
</group>
<group type="3" gid="140" tokens="59" n="2" similarity="0.85">
<f n="_codex_root_thread" p="tests/speckit-pro/lib/native_eval_execution.py:1830"/>
<f n="volatile_manifest_paths" p="tests/speckit-pro/lib/native_eval_upstream.py:272"/>
</group>
<group type="3" gid="141" tokens="118" n="2" similarity="0.91">
<f n="_dispatch_message_attribution" p="tests/speckit-pro/lib/native_eval_execution.py:1892"/>
<f n="_dispatch_message_proof" p="tests/speckit-pro/lib/native_eval_grading.py:595"/>
</group>
<group type="3" gid="141" tokens="118" n="2" similarity="0.87">
<f n="_dispatch_message_attribution" p="tests/speckit-pro/lib/native_eval_execution.py:1892"/>
<f n="_opaque_message" p="tests/speckit-pro/unit/test-native-eval-contracts.py:142"/>
</group>
<group type="3" gid="143" tokens="134" n="2" similarity="0.92">
<f n="_strict_json_stream" p="tests/speckit-pro/lib/native_eval_execution.py:2242"/>
<f n="_json_stream" p="tests/speckit-pro/lib/native_eval_runner_result.py:155"/>
</group>
<group type="3" gid="143" tokens="133" n="2" similarity="0.92">
<f n="_strict_json_stream" p="tests/speckit-pro/lib/native_eval_execution.py:2242"/>
<f n="_json_stream" p="tests/speckit-pro/lib/native_eval_verification.py:154"/>
</group>
<group type="3" gid="144" tokens="100" n="2" similarity="0.85">
<f n="_validated_plan_repair_g3_request" p="tests/speckit-pro/lib/native_eval_execution.py:3323"/>
<f n="_validated_plan_repair_context_request" p="tests/speckit-pro/lib/native_eval_execution.py:3334"/>
</group>
<group type="3" gid="145" tokens="372" n="2" similarity="0.84">
<f n="_judge" p="tests/speckit-pro/lib/native_eval_execution.py:4444"/>
<f n="_pair_judge" p="tests/speckit-pro/lib/native_eval_execution.py:4580"/>
</group>
<group type="3" gid="129" tokens="83" n="2" similarity="0.90">
<f n="_relative_path" p="tests/speckit-pro/lib/native_eval_fixture_setup.py:32"/>
<f n="_path" p="tests/speckit-pro/lib/native_eval_git_grading.py:31"/>
</group>
<group type="3" gid="129" tokens="77" n="2" similarity="0.81">
<f n="_relative_path" p="tests/speckit-pro/lib/native_eval_fixture_setup.py:32"/>
<f n="_safe_path" p="tests/speckit-pro/lib/native_eval_git_observation.py:1026"/>
</group>
<group type="3" gid="129" tokens="79" n="2" similarity="0.82">
<f n="_relative_path" p="tests/speckit-pro/lib/native_eval_fixture_setup.py:32"/>
<f n="_relative" p="tests/speckit-pro/lib/native_eval_pairing.py:46"/>
</group>
<group type="3" gid="129" tokens="77" n="2" similarity="0.95">
<f n="_relative_path" p="tests/speckit-pro/lib/native_eval_fixture_setup.py:32"/>
<f n="_path" p="tests/speckit-pro/lib/native_eval_runner_result.py:39"/>
</group>
<group type="3" gid="146" tokens="70" n="2" similarity="0.83">
<f n="_source_root_and_workspace" p="tests/speckit-pro/lib/native_eval_fixture_setup.py:79"/>
<f n="_workspace_directory" p="tests/speckit-pro/lib/native_eval_fixture_setup.py:92"/>
</group>
<group type="3" gid="146" tokens="76" n="2" similarity="0.84">
<f n="_source_root_and_workspace" p="tests/speckit-pro/lib/native_eval_fixture_setup.py:79"/>
<f n="_git_executable" p="tests/speckit-pro/lib/native_eval_fixture_setup.py:302"/>
</group>
<group type="3" gid="147" tokens="92" n="2" similarity="0.84">
<f n="read_regular" p="tests/speckit-pro/lib/native_eval_fixture_setup.py:424"/>
<f n="_regular_text" p="tests/speckit-pro/lib/native_eval_git_observation.py:413"/>
</group>
<group type="3" gid="147" tokens="87" n="2" similarity="0.86">
<f n="read_regular" p="tests/speckit-pro/lib/native_eval_fixture_setup.py:424"/>
<f n="_real_directory" p="tests/speckit-pro/lib/native_eval_git_observation.py:427"/>
</group>
<group type="3" gid="147" tokens="67" n="2" similarity="0.80">
<f n="read_regular" p="tests/speckit-pro/lib/native_eval_fixture_setup.py:424"/>
<f n="_regular_metadata" p="tests/speckit-pro/lib/native_eval_git_observation.py:449"/>
</group>
<group type="3" gid="148" tokens="220" n="2" similarity="0.92">
<f n="_worktree_records" p="tests/speckit-pro/lib/native_eval_fixture_setup.py:547"/>
<f n="_validate_expected_worktrees" p="tests/speckit-pro/lib/native_eval_git_observation.py:168"/>
</group>
<group type="3" gid="129" tokens="83" n="2" similarity="0.81">
<f n="_path" p="tests/speckit-pro/lib/native_eval_git_grading.py:31"/>
<f n="_safe_path" p="tests/speckit-pro/lib/native_eval_git_observation.py:1026"/>
</group>
<group type="3" gid="129" tokens="83" n="2" similarity="0.92">
<f n="_path" p="tests/speckit-pro/lib/native_eval_git_grading.py:31"/>
<f n="_path" p="tests/speckit-pro/lib/native_eval_runner_result.py:39"/>
</group>
<group type="3" gid="128" tokens="59" n="2" similarity="0.83">
<f n="_paths" p="tests/speckit-pro/lib/native_eval_git_grading.py:41"/>
<f n="_path_list" p="tests/speckit-pro/lib/native_eval_git_observation.py:1009"/>
</group>
<group type="3" gid="128" tokens="48" n="2" similarity="0.97">
<f n="_paths" p="tests/speckit-pro/lib/native_eval_git_grading.py:41"/>
<f n="_unique_text_list" p="tests/speckit-pro/lib/native_eval_pairing.py:106"/>
</group>
<group type="3" gid="149" tokens="241" n="2" similarity="0.85">
<f n="observe_registered_worktrees" p="tests/speckit-pro/lib/native_eval_git_observation.py:68"/>
<f n="snapshot_git_topology" p="tests/speckit-pro/lib/native_eval_git_observation.py:108"/>
</group>
<group type="3" gid="150" tokens="261" n="2" similarity="0.89">
<f n="_status" p="tests/speckit-pro/lib/native_eval_git_observation.py:923"/>
<f n="_topology_status" p="tests/speckit-pro/lib/native_eval_git_observation.py:956"/>
</group>
<group type="3" gid="128" tokens="59" n="2" similarity="0.86">
<f n="_path_list" p="tests/speckit-pro/lib/native_eval_git_observation.py:1009"/>
<f n="_unique_text_list" p="tests/speckit-pro/lib/native_eval_pairing.py:106"/>
</group>
<group type="3" gid="151" tokens="52" n="2" similarity="0.90">
<f n="_nul_entries" p="tests/speckit-pro/lib/native_eval_git_observation.py:1017"/>
<f n="_decode_lines" p="tests/speckit-pro/lib/native_eval_git_observation.py:1111"/>
</group>
<group type="3" gid="129" tokens="71" n="2" similarity="0.82">
<f n="_safe_path" p="tests/speckit-pro/lib/native_eval_git_observation.py:1026"/>
<f n="_path" p="tests/speckit-pro/lib/native_eval_runner_result.py:39"/>
</group>
<group type="3" gid="141" tokens="102" n="2" similarity="0.96">
<f n="_dispatch_message_proof" p="tests/speckit-pro/lib/native_eval_grading.py:595"/>
<f n="_opaque_message" p="tests/speckit-pro/unit/test-native-eval-contracts.py:142"/>
</group>
<group type="3" gid="152" tokens="266" n="2" similarity="0.94">
<f n="_validate_plan_repair_command_receipts" p="tests/speckit-pro/lib/native_eval_grading.py:877"/>
<f n="_validate_plan_repair_renderer_receipts" p="tests/speckit-pro/lib/native_eval_grading.py:907"/>
</group>
<group type="3" gid="129" tokens="79" n="2" similarity="0.84">
<f n="_relative" p="tests/speckit-pro/lib/native_eval_pairing.py:46"/>
<f n="_path" p="tests/speckit-pro/lib/native_eval_runner_result.py:39"/>
</group>
<group type="3" gid="153" tokens="50" n="2" similarity="0.82">
<f n="_canonical" p="tests/speckit-pro/lib/native_eval_pairing.py:68"/>
<f n="_digest" p="tests/speckit-pro/lib/native_eval_runtime.py:456"/>
</group>
<group type="3" gid="153" tokens="44" n="2" similarity="0.80">
<f n="_canonical" p="tests/speckit-pro/lib/native_eval_pairing.py:68"/>
<f n="absence_bytes" p="tests/speckit-pro/lib/native_eval_verification.py:389"/>
</group>
<group type="3" gid="134" tokens="80" n="2" similarity="0.80">
<f n="_load_contract" p="tests/speckit-pro/lib/native_eval_pairing.py:93"/>
<f n="_loads" p="tests/speckit-pro/lib/native_eval_runner_result.py:113"/>
</group>
<group type="3" gid="155" tokens="47" n="2" similarity="0.97">
<f n="request_paths" p="tests/speckit-pro/lib/native_eval_runner_result.py:94"/>
<f n="pointer_artifacts" p="tests/speckit-pro/lib/native_eval_verification.py:79"/>
</group>
<group type="3" gid="155" tokens="54" n="2" similarity="0.90">
<f n="request_paths" p="tests/speckit-pro/lib/native_eval_runner_result.py:94"/>
<f n="record_directories" p="tests/speckit-pro/lib/native_eval_verification.py:98"/>
</group>
<group type="3" gid="143" tokens="134" n="2" similarity="1.00">
<f n="_json_stream" p="tests/speckit-pro/lib/native_eval_runner_result.py:155"/>
<f n="_json_stream" p="tests/speckit-pro/lib/native_eval_verification.py:154"/>
</group>
<group type="3" gid="158" tokens="218" n="2" similarity="0.84">
<f n="grade" p="tests/speckit-pro/lib/native_eval_store.py:409"/>
<f n="pair_grade" p="tests/speckit-pro/lib/native_eval_store.py:495"/>
</group>
<group type="3" gid="159" tokens="315" n="2" similarity="0.89">
<f n="_tree_receipt" p="tests/speckit-pro/lib/native_eval_toolchain.py:589"/>
<f n="visit" p="tests/speckit-pro/lib/native_eval_toolchain.py:601"/>
</group>
<group type="3" gid="160" tokens="338" n="2" similarity="0.89">
<f n="_copy_protected_tree" p="tests/speckit-pro/lib/native_eval_toolchain.py:665"/>
<f n="visit" p="tests/speckit-pro/lib/native_eval_toolchain.py:678"/>
</group>
<group type="3" gid="140" tokens="59" n="2" similarity="0.85">
<f n="skill_witnesses" p="tests/speckit-pro/lib/native_eval_upstream.py:264"/>
<f n="volatile_manifest_paths" p="tests/speckit-pro/lib/native_eval_upstream.py:272"/>
</group>
<group type="3" gid="155" tokens="54" n="2" similarity="0.93">
<f n="pointer_artifacts" p="tests/speckit-pro/lib/native_eval_verification.py:79"/>
<f n="record_directories" p="tests/speckit-pro/lib/native_eval_verification.py:98"/>
</group>
<group type="3" gid="171" tokens="70" n="2" similarity="0.84">
<f n="run_status_evidence_report" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:256"/>
<f n="_run_coverage_guard" p="tests/speckit-pro/unit/test-native-functional-catalog.py:729"/>
</group>
<group type="3" gid="184" tokens="225" n="2" similarity="0.82">
<f n="test_resume_re_attests_a_stale_boundary_before_the_coverage_guard" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:485"/>
<f n="test_codex_autopilot_worktree_handoff_contract" p="tests/speckit-pro/unit/test-eval-runner-skill-selection.py:676"/>
</group>
<group type="3" gid="184" tokens="199" n="2" similarity="0.82">
<f n="test_resume_re_attests_a_stale_boundary_before_the_coverage_guard" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:485"/>
<f n="test_claude_autopilot_same_session_cd_handoff_contract" p="tests/speckit-pro/unit/test-eval-runner-skill-selection.py:711"/>
</group>
<group type="3" gid="20" tokens="59" n="2" similarity="0.97">
<f n="load_validator_module" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:62"/>
<f n="import_script" p="tests/speckit-pro/unit/test-trigger-eval-runners.py:57"/>
</group>
<group type="3" gid="202" tokens="74" n="2" similarity="0.94">
<f n="run_checker" p="tests/speckit-pro/unit/test-check-toolchain.py:62"/>
<f n="run_script" p="tests/speckit-pro/unit/test-eval-runner-skill-selection.py:587"/>
</group>
<group type="3" gid="20" tokens="59" n="2" similarity="0.98">
<f n="load_composer" p="tests/speckit-pro/unit/test-compose-release-notes.py:54"/>
<f n="import_script" p="tests/speckit-pro/unit/test-trigger-eval-runners.py:57"/>
</group>
<group type="3" gid="209" tokens="62" n="2" similarity="0.83">
<f n="test_each_single_category_tag_routes_to_its_own_analyst" p="tests/speckit-pro/unit/test-consensus-routing-helpers.py:130"/>
<f n="test_unbounded_sed_still_rejects_expansion_and_incomplete_output" p="tests/speckit-pro/unit/test-native-eval-fixture-reads.py:104"/>
</group>
<group type="3" gid="214" tokens="65" n="2" similarity="0.86">
<f n="setUp" p="tests/speckit-pro/unit/test-docs-artifact.py:38"/>
<f n="setUp" p="tests/speckit-pro/unit/test-native-eval-execution.py:2356"/>
</group>
<group type="3" gid="202" tokens="68" n="2" similarity="0.93">
<f n="run_script" p="tests/speckit-pro/unit/test-eval-runner-skill-selection.py:587"/>
<f n="run_cli" p="tests/speckit-pro/unit/test-parity-judge.py:52"/>
</group>
<group type="3" gid="202" tokens="68" n="2" similarity="0.89">
<f n="run_script" p="tests/speckit-pro/unit/test-eval-runner-skill-selection.py:587"/>
<f n="run_sync" p="tests/speckit-pro/unit/test-sync-marketplace-versions.py:24"/>
</group>
<group type="3" gid="202" tokens="72" n="2" similarity="0.97">
<f n="run_script" p="tests/speckit-pro/unit/test-eval-runner-skill-selection.py:587"/>
<f n="run_script" p="tests/speckit-pro/unit/test-transcript-tools.py:29"/>
</group>
<group type="3" gid="248" tokens="51" n="2" similarity="0.91">
<f n="valid_table" p="tests/speckit-pro/unit/test-gate-discovery-table.py:33"/>
<f n="pairing" p="tests/speckit-pro/unit/test-native-eval-contracts.py:67"/>
</group>
<group type="3" gid="20" tokens="59" n="2" similarity="0.91">
<f n="load_script_module" p="tests/speckit-pro/unit/test-integration-runners.py:49"/>
<f n="import_script" p="tests/speckit-pro/unit/test-trigger-eval-runners.py:57"/>
</group>
<group type="3" gid="256" tokens="178" n="2" similarity="0.84">
<f n="native_case" p="tests/speckit-pro/unit/test-native-eval-adapters.py:45"/>
<f n="case" p="tests/speckit-pro/unit/test-native-eval-contracts.py:40"/>
</group>
<group type="3" gid="256" tokens="144" n="2" similarity="0.84">
<f n="checkout_runtime_case" p="tests/speckit-pro/unit/test-native-eval-adapters.py:71"/>
<f n="case" p="tests/speckit-pro/unit/test-native-eval-contracts.py:40"/>
</group>
<group type="3" gid="257" tokens="72" n="2" similarity="0.93">
<f n="verify_test_upstream" p="tests/speckit-pro/unit/test-native-eval-adapters.py:344"/>
<f n="verify_test_staged_upstream" p="tests/speckit-pro/unit/test-native-eval-adapters.py:352"/>
</group>
<group type="3" gid="258" tokens="51" n="2" similarity="0.82">
<f n="setUp" p="tests/speckit-pro/unit/test-native-eval-adapters.py:394"/>
<f n="setUp" p="tests/speckit-pro/unit/test-refresh-local-plugin.py:75"/>
</group>
<group type="3" gid="259" tokens="225" n="2" similarity="0.83">
<f n="test_claude_staged_controller_directories_reject_tampering_before_launch" p="tests/speckit-pro/unit/test-native-eval-adapters.py:1386"/>
<f n="test_claude_controller_config_root_tampering_fails_before_launch" p="tests/speckit-pro/unit/test-native-eval-adapters.py:1484"/>
</group>
<group type="3" gid="260" tokens="237" n="2" similarity="0.82">
<f n="test_codex_transport_returns_exact_trace_and_process_evidence" p="tests/speckit-pro/unit/test-native-eval-adapters.py:3905"/>
<f n="test_judge_transport_preserves_malformed_result_and_exact_process_streams" p="tests/speckit-pro/unit/test-native-eval-adapters.py:4021"/>
</group>
<group type="3" gid="261" tokens="150" n="2" similarity="0.91">
<f n="claude_events" p="tests/speckit-pro/unit/test-native-eval-capture.py:34"/>
<f n="claude_fixture_read_trace" p="tests/speckit-pro/unit/test-native-eval-execution.py:447"/>
</group>
<group type="3" gid="261" tokens="158" n="2" similarity="0.90">
<f n="claude_events" p="tests/speckit-pro/unit/test-native-eval-capture.py:34"/>
<f n="claude_agent_trace" p="tests/speckit-pro/unit/test-native-eval-execution.py:464"/>
</group>
<group type="3" gid="261" tokens="156" n="2" similarity="0.88">
<f n="claude_events" p="tests/speckit-pro/unit/test-native-eval-capture.py:34"/>
<f n="claude_runner_result_trace" p="tests/speckit-pro/unit/test-native-eval-execution.py:935"/>
</group>
<group type="3" gid="262" tokens="61" n="2" similarity="0.87">
<f n="test_replays_installed_claude_2_1_272_session_start_canary_when_available" p="tests/speckit-pro/unit/test-native-eval-capture.py:582"/>
<f n="test_claude_activation_requires_completed_skill_tool" p="tests/speckit-pro/unit/test-native-eval-capture.py:601"/>
</group>
<group type="3" gid="263" tokens="47" n="2" similarity="0.98">
<f n="identity" p="tests/speckit-pro/unit/test-native-eval-claude-activation.py:140"/>
<f n="identity" p="tests/speckit-pro/unit/test-native-eval-execution.py:426"/>
</group>
<group type="3" gid="263" tokens="47" n="2" similarity="0.86">
<f n="identity" p="tests/speckit-pro/unit/test-native-eval-claude-activation.py:140"/>
<f n="runner_command_item" p="tests/speckit-pro/unit/test-native-eval-execution.py:1839"/>
</group>
<group type="3" gid="264" tokens="89" n="2" similarity="0.99">
<f n="meta" p="tests/speckit-pro/unit/test-native-eval-codex-rollouts.py:51"/>
<f n="rollout_meta" p="tests/speckit-pro/unit/test-native-eval-execution.py:1025"/>
</group>
<group type="3" gid="265" tokens="71" n="2" similarity="0.93">
<f n="delivery_record" p="tests/speckit-pro/unit/test-native-eval-codex-rollouts.py:130"/>
<f n="user_message" p="tests/speckit-pro/unit/test-native-eval-codex-rollouts.py:482"/>
</group>
<group type="3" gid="265" tokens="71" n="2" similarity="0.91">
<f n="delivery_record" p="tests/speckit-pro/unit/test-native-eval-codex-rollouts.py:130"/>
<f n="rollout_message" p="tests/speckit-pro/unit/test-native-eval-execution.py:1042"/>
</group>
<group type="3" gid="265" tokens="71" n="2" similarity="0.97">
<f n="user_message" p="tests/speckit-pro/unit/test-native-eval-codex-rollouts.py:482"/>
<f n="rollout_message" p="tests/speckit-pro/unit/test-native-eval-execution.py:1042"/>
</group>
<group type="3" gid="266" tokens="161" n="2" similarity="0.87">
<f n="skill_records" p="tests/speckit-pro/unit/test-native-eval-codex-rollouts.py:500"/>
<f n="native_skill_records" p="tests/speckit-pro/unit/test-native-eval-execution.py:1061"/>
</group>
<group type="3" gid="267" tokens="100" n="2" similarity="0.86">
<f n="test_multiple_known_siblings_are_preserved_in_rollout_order" p="tests/speckit-pro/unit/test-native-eval-codex-rollouts.py:1694"/>
<f n="test_expected_and_extra_activation_are_both_preserved_for_shared_grading" p="tests/speckit-pro/unit/test-native-eval-codex-rollouts.py:1707"/>
</group>
<group type="3" gid="267" tokens="100" n="2" similarity="0.85">
<f n="test_multiple_known_siblings_are_preserved_in_rollout_order" p="tests/speckit-pro/unit/test-native-eval-codex-rollouts.py:1694"/>
<f n="test_stale_or_inherited_skill_injection_cannot_satisfy_current_turn" p="tests/speckit-pro/unit/test-native-eval-codex-rollouts.py:1740"/>
</group>
<group type="3" gid="267" tokens="84" n="2" similarity="0.88">
<f n="test_expected_and_extra_activation_are_both_preserved_for_shared_grading" p="tests/speckit-pro/unit/test-native-eval-codex-rollouts.py:1707"/>
<f n="test_stale_or_inherited_skill_injection_cannot_satisfy_current_turn" p="tests/speckit-pro/unit/test-native-eval-codex-rollouts.py:1740"/>
</group>
<group type="3" gid="256" tokens="151" n="2" similarity="0.83">
<f n="case" p="tests/speckit-pro/unit/test-native-eval-contracts.py:40"/>
<f n="catalog_case" p="tests/speckit-pro/unit/test-native-eval-entrypoint.py:25"/>
</group>
<group type="3" gid="256" tokens="185" n="2" similarity="0.81">
<f n="case" p="tests/speckit-pro/unit/test-native-eval-contracts.py:40"/>
<f n="make_case" p="tests/speckit-pro/unit/test-native-eval-pairing.py:110"/>
</group>
<group type="3" gid="268" tokens="65" n="2" similarity="0.98">
<f n="git_final_state_check" p="tests/speckit-pro/unit/test-native-eval-contracts.py:106"/>
<f n="final_state_check" p="tests/speckit-pro/unit/test-native-eval-git-grading.py:29"/>
</group>
<group type="3" gid="74" tokens="55" n="2" similarity="0.98">
<f n="runner_result_check" p="tests/speckit-pro/unit/test-native-eval-contracts.py:130"/>
<f n="check" p="tests/speckit-pro/unit/test-native-eval-runner-result.py:45"/>
</group>
<group type="3" gid="269" tokens="176" n="2" similarity="0.89">
<f n="test_file_access_check_requires_one_exact_read_file_path" p="tests/speckit-pro/unit/test-native-eval-contracts.py:690"/>
<f n="test_subagent_return_check_requires_one_canonical_path" p="tests/speckit-pro/unit/test-native-eval-contracts.py:831"/>
</group>
<group type="3" gid="270" tokens="62" n="2" similarity="0.84">
<f n="test_fixed_git_recipe_rejects_empty_semantic_diff" p="tests/speckit-pro/unit/test-native-eval-contracts.py:1673"/>
<f n="test_v1_entrypoint_rejects_v2_before_any_workspace_effect" p="tests/speckit-pro/unit/test-native-eval-contracts.py:1681"/>
</group>
<group type="3" gid="271" tokens="172" n="2" similarity="0.81">
<f n="test_git_inspection_binds_controls_before_any_repository_git_command" p="tests/speckit-pro/unit/test-native-eval-contracts.py:1720"/>
<f n="test_git_inspection_rejects_redirects_and_symlinks_before_git" p="tests/speckit-pro/unit/test-native-eval-contracts.py:1737"/>
</group>
<group type="3" gid="272" tokens="183" n="2" similarity="0.83">
<f n="_build_envelope" p="tests/speckit-pro/unit/test-native-eval-dispatch-context.py:176"/>
<f n="plan_repair_renderer_response" p="tests/speckit-pro/unit/test-native-eval-execution.py:688"/>
</group>
<group type="3" gid="256" tokens="185" n="2" similarity="0.83">
<f n="catalog_case" p="tests/speckit-pro/unit/test-native-eval-entrypoint.py:25"/>
<f n="make_case" p="tests/speckit-pro/unit/test-native-eval-pairing.py:110"/>
</group>
<group type="3" gid="273" tokens="94" n="2" similarity="0.87">
<f n="git_observation" p="tests/speckit-pro/unit/test-native-eval-execution.py:201"/>
<f n="git_observation" p="tests/speckit-pro/unit/test-native-eval-git-grading.py:50"/>
</group>
<group type="3" gid="274" tokens="43" n="2" similarity="0.98">
<f n="assert_verified_capture" p="tests/speckit-pro/unit/test-native-eval-execution.py:317"/>
<f n="assert_rejected_parent_synthesis" p="tests/speckit-pro/unit/test-native-eval-execution.py:323"/>
</group>
<group type="3" gid="263" tokens="47" n="2" similarity="0.88">
<f n="identity" p="tests/speckit-pro/unit/test-native-eval-execution.py:426"/>
<f n="runner_command_item" p="tests/speckit-pro/unit/test-native-eval-execution.py:1839"/>
</group>
<group type="3" gid="261" tokens="158" n="2" similarity="0.95">
<f n="claude_fixture_read_trace" p="tests/speckit-pro/unit/test-native-eval-execution.py:447"/>
<f n="claude_agent_trace" p="tests/speckit-pro/unit/test-native-eval-execution.py:464"/>
</group>
<group type="3" gid="261" tokens="156" n="2" similarity="0.97">
<f n="claude_fixture_read_trace" p="tests/speckit-pro/unit/test-native-eval-execution.py:447"/>
<f n="claude_runner_result_trace" p="tests/speckit-pro/unit/test-native-eval-execution.py:935"/>
</group>
<group type="3" gid="261" tokens="158" n="2" similarity="0.94">
<f n="claude_agent_trace" p="tests/speckit-pro/unit/test-native-eval-execution.py:464"/>
<f n="claude_runner_result_trace" p="tests/speckit-pro/unit/test-native-eval-execution.py:935"/>
</group>
<group type="3" gid="275" tokens="94" n="2" similarity="0.93">
<f n="verification_record" p="tests/speckit-pro/unit/test-native-eval-execution.py:577"/>
<f n="record" p="tests/speckit-pro/unit/test-native-eval-verification.py:60"/>
</group>
<group type="3" gid="276" tokens="210" n="2" similarity="0.97">
<f n="codex_verification_rollout" p="tests/speckit-pro/unit/test-native-eval-execution.py:953"/>
<f n="codex_runner_result_rollout" p="tests/speckit-pro/unit/test-native-eval-execution.py:982"/>
</group>
<group type="3" gid="214" tokens="56" n="2" similarity="0.89">
<f n="setUp" p="tests/speckit-pro/unit/test-native-eval-execution.py:2356"/>
<f n="setUp" p="tests/speckit-pro/unit/test-native-eval-runtime.py:81"/>
</group>
<group type="3" gid="277" tokens="270" n="2" similarity="0.83">
<f n="test_fixture_read_witness_change_is_a_new_subject_input" p="tests/speckit-pro/unit/test-native-eval-execution.py:2489"/>
<f n="test_codex_controller_plugin_name_binds_fresh_and_retained_rollout_parsing" p="tests/speckit-pro/unit/test-native-eval-execution.py:2972"/>
</group>
<group type="3" gid="277" tokens="219" n="2" similarity="0.82">
<f n="test_fixture_read_witness_change_is_a_new_subject_input" p="tests/speckit-pro/unit/test-native-eval-execution.py:2489"/>
<f n="test_codex_historical_capture_without_native_rollout_needs_renormalization" p="tests/speckit-pro/unit/test-native-eval-execution.py:3187"/>
</group>
<group type="3" gid="277" tokens="219" n="2" similarity="0.83">
<f n="test_claude_historical_capture_without_activation_raw_needs_renormalization" p="tests/speckit-pro/unit/test-native-eval-execution.py:2769"/>
<f n="test_codex_historical_capture_without_native_rollout_needs_renormalization" p="tests/speckit-pro/unit/test-native-eval-execution.py:3187"/>
</group>
<group type="3" gid="277" tokens="270" n="2" similarity="0.84">
<f n="test_codex_controller_plugin_name_binds_fresh_and_retained_rollout_parsing" p="tests/speckit-pro/unit/test-native-eval-execution.py:2972"/>
<f n="test_codex_historical_capture_without_native_rollout_needs_renormalization" p="tests/speckit-pro/unit/test-native-eval-execution.py:3187"/>
</group>
<group type="3" gid="278" tokens="123" n="2" similarity="0.82">
<f n="test_codex_controller_plugin_name_rejects_changed_protected_tree" p="tests/speckit-pro/unit/test-native-eval-execution.py:2999"/>
<f n="test_nested_order_check_is_invalid_when_cross_thread_timeline_is_ambiguous" p="tests/speckit-pro/unit/test-native-eval-execution.py:5445"/>
</group>
<group type="3" gid="279" tokens="122" n="2" similarity="0.92">
<f n="test_codex_missing_or_malformed_witness_and_cwd_fail_closed" p="tests/speckit-pro/unit/test-native-eval-execution.py:3174"/>
<f n="test_v2_git_observation_missing_error_malformed_and_tampered_are_invalid" p="tests/speckit-pro/unit/test-native-eval-execution.py:4418"/>
</group>
<group type="3" gid="279" tokens="117" n="2" similarity="0.95">
<f n="test_codex_missing_or_malformed_witness_and_cwd_fail_closed" p="tests/speckit-pro/unit/test-native-eval-execution.py:3174"/>
<f n="test_claude_absence_rejects_partial_truncated_wrong_session_and_malformed_runner" p="tests/speckit-pro/unit/test-native-eval-execution.py:4743"/>
</group>
<group type="3" gid="279" tokens="162" n="2" similarity="0.82">
<f n="test_codex_missing_or_malformed_witness_and_cwd_fail_closed" p="tests/speckit-pro/unit/test-native-eval-execution.py:3174"/>
<f n="test_native_runner_rejects_unauthenticated_or_incomplete_commands_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:5250"/>
</group>
<group type="3" gid="279" tokens="137" n="2" similarity="0.87">
<f n="test_codex_missing_or_malformed_witness_and_cwd_fail_closed" p="tests/speckit-pro/unit/test-native-eval-execution.py:3174"/>
<f n="test_causal_wrong_order_early_later_and_wrong_writer_fail_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:5279"/>
</group>
<group type="3" gid="279" tokens="115" n="2" similarity="0.89">
<f n="test_codex_missing_or_malformed_witness_and_cwd_fail_closed" p="tests/speckit-pro/unit/test-native-eval-execution.py:3174"/>
<f n="test_causal_codex_wrong_or_absent_action_turn_is_invalid" p="tests/speckit-pro/unit/test-native-eval-execution.py:5315"/>
</group>
<group type="3" gid="280" tokens="293" n="2" similarity="0.80">
<f n="test_pair_request_checkpoint_failure_is_terminal_without_judge_call" p="tests/speckit-pro/unit/test-native-eval-execution.py:3276"/>
<f n="test_judge_request_build_failure_is_terminal_without_judge_call" p="tests/speckit-pro/unit/test-native-eval-execution.py:3515"/>
</group>
<group type="3" gid="281" tokens="324" n="2" similarity="0.83">
<f n="test_native_dispatch_attribution_passes_both_hosts_and_replays_without_subjects" p="tests/speckit-pro/unit/test-native-eval-execution.py:4059"/>
<f n="test_causal_returns_pass_both_hosts_and_regrade_wrong_path_without_launches" p="tests/speckit-pro/unit/test-native-eval-execution.py:4135"/>
</group>
<group type="3" gid="281" tokens="324" n="2" similarity="0.87">
<f n="test_native_dispatch_attribution_passes_both_hosts_and_replays_without_subjects" p="tests/speckit-pro/unit/test-native-eval-execution.py:4059"/>
<f n="test_native_verification_record_is_retained_and_replayed_for_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:4460"/>
</group>
<group type="3" gid="281" tokens="401" n="2" similarity="0.81">
<f n="test_native_dispatch_attribution_passes_both_hosts_and_replays_without_subjects" p="tests/speckit-pro/unit/test-native-eval-execution.py:4059"/>
<f n="test_claude_complete_bound_run_without_runner_is_behavior_fail_and_regrades" p="tests/speckit-pro/unit/test-native-eval-execution.py:4667"/>
</group>
<group type="3" gid="281" tokens="406" n="2" similarity="0.84">
<f n="test_native_dispatch_attribution_passes_both_hosts_and_replays_without_subjects" p="tests/speckit-pro/unit/test-native-eval-execution.py:4059"/>
<f n="test_native_runner_expected_failure_is_bound_fresh_and_replayed_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:4950"/>
</group>
<group type="3" gid="281" tokens="306" n="2" similarity="0.85">
<f n="test_causal_returns_pass_both_hosts_and_regrade_wrong_path_without_launches" p="tests/speckit-pro/unit/test-native-eval-execution.py:4135"/>
<f n="test_native_verification_record_is_retained_and_replayed_for_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:4460"/>
</group>
<group type="3" gid="281" tokens="269" n="2" similarity="0.84">
<f n="test_causal_returns_pass_both_hosts_and_regrade_wrong_path_without_launches" p="tests/speckit-pro/unit/test-native-eval-execution.py:4135"/>
<f n="test_regrade_restores_hash_bound_artifact_absence_without_relaunch" p="tests/speckit-pro/unit/test-native-eval-execution.py:5457"/>
</group>
<group type="3" gid="279" tokens="122" n="2" similarity="0.97">
<f n="test_v2_git_observation_missing_error_malformed_and_tampered_are_invalid" p="tests/speckit-pro/unit/test-native-eval-execution.py:4418"/>
<f n="test_claude_absence_rejects_partial_truncated_wrong_session_and_malformed_runner" p="tests/speckit-pro/unit/test-native-eval-execution.py:4743"/>
</group>
<group type="3" gid="279" tokens="166" n="2" similarity="0.83">
<f n="test_v2_git_observation_missing_error_malformed_and_tampered_are_invalid" p="tests/speckit-pro/unit/test-native-eval-execution.py:4418"/>
<f n="test_native_runner_claim_only_is_invalid_and_wrong_outcome_fails_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:5232"/>
</group>
<group type="3" gid="279" tokens="162" n="2" similarity="0.85">
<f n="test_v2_git_observation_missing_error_malformed_and_tampered_are_invalid" p="tests/speckit-pro/unit/test-native-eval-execution.py:4418"/>
<f n="test_native_runner_rejects_unauthenticated_or_incomplete_commands_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:5250"/>
</group>
<group type="3" gid="279" tokens="137" n="2" similarity="0.93">
<f n="test_v2_git_observation_missing_error_malformed_and_tampered_are_invalid" p="tests/speckit-pro/unit/test-native-eval-execution.py:4418"/>
<f n="test_causal_wrong_order_early_later_and_wrong_writer_fail_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:5279"/>
</group>
<group type="3" gid="279" tokens="122" n="2" similarity="0.87">
<f n="test_v2_git_observation_missing_error_malformed_and_tampered_are_invalid" p="tests/speckit-pro/unit/test-native-eval-execution.py:4418"/>
<f n="test_causal_codex_wrong_or_absent_action_turn_is_invalid" p="tests/speckit-pro/unit/test-native-eval-execution.py:5315"/>
</group>
<group type="3" gid="281" tokens="406" n="2" similarity="0.84">
<f n="test_native_verification_record_is_retained_and_replayed_for_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:4460"/>
<f n="test_native_runner_expected_failure_is_bound_fresh_and_replayed_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:4950"/>
</group>
<group type="3" gid="281" tokens="306" n="2" similarity="0.80">
<f n="test_native_verification_record_is_retained_and_replayed_for_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:4460"/>
<f n="test_regrade_restores_hash_bound_artifact_absence_without_relaunch" p="tests/speckit-pro/unit/test-native-eval-execution.py:5457"/>
</group>
<group type="3" gid="282" tokens="119" n="2" similarity="0.89">
<f n="test_claude_runner_accepts_only_the_exact_native_cwd_prelude" p="tests/speckit-pro/unit/test-native-eval-execution.py:4526"/>
<f n="test_claude_runner_accepts_only_the_bounded_tmp_capture_pipeline" p="tests/speckit-pro/unit/test-native-eval-execution.py:4549"/>
</group>
<group type="3" gid="279" tokens="166" n="2" similarity="0.81">
<f n="test_claude_absence_rejects_partial_truncated_wrong_session_and_malformed_runner" p="tests/speckit-pro/unit/test-native-eval-execution.py:4743"/>
<f n="test_native_runner_claim_only_is_invalid_and_wrong_outcome_fails_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:5232"/>
</group>
<group type="3" gid="279" tokens="162" n="2" similarity="0.83">
<f n="test_claude_absence_rejects_partial_truncated_wrong_session_and_malformed_runner" p="tests/speckit-pro/unit/test-native-eval-execution.py:4743"/>
<f n="test_native_runner_rejects_unauthenticated_or_incomplete_commands_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:5250"/>
</group>
<group type="3" gid="279" tokens="137" n="2" similarity="0.91">
<f n="test_claude_absence_rejects_partial_truncated_wrong_session_and_malformed_runner" p="tests/speckit-pro/unit/test-native-eval-execution.py:4743"/>
<f n="test_causal_wrong_order_early_later_and_wrong_writer_fail_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:5279"/>
</group>
<group type="3" gid="279" tokens="117" n="2" similarity="0.90">
<f n="test_claude_absence_rejects_partial_truncated_wrong_session_and_malformed_runner" p="tests/speckit-pro/unit/test-native-eval-execution.py:4743"/>
<f n="test_causal_codex_wrong_or_absent_action_turn_is_invalid" p="tests/speckit-pro/unit/test-native-eval-execution.py:5315"/>
</group>
<group type="3" gid="283" tokens="388" n="2" similarity="0.82">
<f n="test_invalid_claude_absence_capture_is_renormalized_without_relaunch" p="tests/speckit-pro/unit/test-native-eval-execution.py:4755"/>
<f n="test_invalid_claude_verification_recovers_deleted_record_from_bound_response" p="tests/speckit-pro/unit/test-native-eval-execution.py:4787"/>
</group>
<group type="3" gid="283" tokens="400" n="2" similarity="0.88">
<f n="test_invalid_claude_absence_capture_is_renormalized_without_relaunch" p="tests/speckit-pro/unit/test-native-eval-execution.py:4755"/>
<f n="test_invalid_codex_capture_is_renormalized_without_subject_relaunch" p="tests/speckit-pro/unit/test-native-eval-execution.py:5368"/>
</group>
<group type="3" gid="283" tokens="400" n="2" similarity="0.83">
<f n="test_invalid_claude_verification_recovers_deleted_record_from_bound_response" p="tests/speckit-pro/unit/test-native-eval-execution.py:4787"/>
<f n="test_invalid_codex_capture_is_renormalized_without_subject_relaunch" p="tests/speckit-pro/unit/test-native-eval-execution.py:5368"/>
</group>
<group type="3" gid="279" tokens="168" n="2" similarity="0.87">
<f n="test_absent_verification_evidence_variants_stay_infrastructure_invalid" p="tests/speckit-pro/unit/test-native-eval-execution.py:4934"/>
<f n="test_causal_wrong_order_early_later_and_wrong_writer_fail_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:5279"/>
</group>
<group type="3" gid="279" tokens="166" n="2" similarity="0.97">
<f n="test_native_runner_claim_only_is_invalid_and_wrong_outcome_fails_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:5232"/>
<f n="test_native_runner_rejects_unauthenticated_or_incomplete_commands_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:5250"/>
</group>
<group type="3" gid="279" tokens="166" n="2" similarity="0.84">
<f n="test_native_runner_claim_only_is_invalid_and_wrong_outcome_fails_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:5232"/>
<f n="test_native_runner_rejects_codex_command_from_wrong_cwd" p="tests/speckit-pro/unit/test-native-eval-execution.py:5268"/>
</group>
<group type="3" gid="279" tokens="162" n="2" similarity="0.86">
<f n="test_native_runner_rejects_unauthenticated_or_incomplete_commands_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:5250"/>
<f n="test_native_runner_rejects_codex_command_from_wrong_cwd" p="tests/speckit-pro/unit/test-native-eval-execution.py:5268"/>
</group>
<group type="3" gid="279" tokens="162" n="2" similarity="0.81">
<f n="test_native_runner_rejects_unauthenticated_or_incomplete_commands_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:5250"/>
<f n="test_causal_wrong_order_early_later_and_wrong_writer_fail_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:5279"/>
</group>
<group type="3" gid="279" tokens="137" n="2" similarity="0.82">
<f n="test_causal_wrong_order_early_later_and_wrong_writer_fail_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:5279"/>
<f n="test_causal_codex_wrong_or_absent_action_turn_is_invalid" p="tests/speckit-pro/unit/test-native-eval-execution.py:5315"/>
</group>
<group type="3" gid="279" tokens="165" n="2" similarity="0.81">
<f n="test_causal_wrong_order_early_later_and_wrong_writer_fail_both_hosts" p="tests/speckit-pro/unit/test-native-eval-execution.py:5279"/>
<f n="test_nested_codex_no_child_cycle_and_wrong_cwd_fail_closed" p="tests/speckit-pro/unit/test-native-eval-execution.py:5353"/>
</group>
<group type="3" gid="136" tokens="81" n="2" similarity="0.84">
<f n="controller_record" p="tests/speckit-pro/unit/test-native-eval-git-grading.py:67"/>
<f n="controller_git_metadata" p="tests/speckit-pro/unit/test-native-parity-catalog.py:74"/>
</group>
<group type="3" gid="284" tokens="64" n="2" similarity="0.86">
<f n="test_correct_empty_tables_remain_valid" p="tests/speckit-pro/unit/test-native-eval-pairing.py:185"/>
<f n="test_deterministic_mismatch_fails_without_semantic_judging" p="tests/speckit-pro/unit/test-native-eval-pairing.py:242"/>
</group>
<group type="3" gid="285" tokens="157" n="2" similarity="0.90">
<f n="test_byte_identical_compares_the_complete_declared_artifact" p="tests/speckit-pro/unit/test-native-eval-pairing.py:257"/>
<f n="test_numeric_tolerance_one_is_not_byte_equality" p="tests/speckit-pro/unit/test-native-eval-pairing.py:268"/>
</group>
<group type="3" gid="286" tokens="268" n="2" similarity="0.83">
<f n="test_global_host_bound_applies_to_jobs_from_multiple_layers" p="tests/speckit-pro/unit/test-native-eval-pool.py:22"/>
<f n="test_judge_uses_the_same_codex_capacity_and_is_not_run_inside_subject" p="tests/speckit-pro/unit/test-native-eval-pool.py:58"/>
</group>
<group type="3" gid="287" tokens="142" n="2" similarity="0.82">
<f n="test_failure_is_not_retried_and_callback_exception_is_invalid" p="tests/speckit-pro/unit/test-native-eval-pool.py:93"/>
<f n="test_duplicate_followup_is_invalid_and_never_executes" p="tests/speckit-pro/unit/test-native-eval-pool.py:153"/>
</group>
<group type="3" gid="288" tokens="209" n="2" similarity="0.82">
<f n="test_stop_event_prevents_new_launches_but_drains_running_work" p="tests/speckit-pro/unit/test-native-eval-pool.py:127"/>
<f n="test_judge_queued_after_codex_stop_is_held_not_discarded" p="tests/speckit-pro/unit/test-native-eval-pool.py:226"/>
</group>
<group type="3" gid="289" tokens="67" n="2" similarity="0.93">
<f n="test_response_only_claim_without_controller_authority_is_invalid" p="tests/speckit-pro/unit/test-native-eval-runner-result.py:271"/>
<f n="test_pointer_without_controller_authority_is_invalid" p="tests/speckit-pro/unit/test-native-eval-verification.py:219"/>
</group>
<group type="3" gid="290" tokens="45" n="2" similarity="0.84">
<f n="fixture_repo" p="tests/speckit-pro/unit/test-native-eval-runtime.py:100"/>
<f n="_install_claude_plugin" p="tests/speckit-pro/unit/test-native-eval-toolchain.py:157"/>
</group>
<group type="3" gid="291" tokens="74" n="2" similarity="0.83">
<f n="guarded_open" p="tests/speckit-pro/unit/test-native-eval-runtime.py:495"/>
<f n="guard" p="tests/speckit-pro/unit/test-native-eval-runtime.py:496"/>
</group>
<group type="3" gid="292" tokens="95" n="2" similarity="0.80">
<f n="test_child_search_cannot_prove_parent_workspace_absence" p="tests/speckit-pro/unit/test-native-eval-search.py:44"/>
<f n="test_successful_empty_search_is_not_a_prose_claim" p="tests/speckit-pro/unit/test-native-eval-search.py:51"/>
</group>
<group type="3" gid="292" tokens="73" n="2" similarity="0.86">
<f n="test_child_search_cannot_prove_parent_workspace_absence" p="tests/speckit-pro/unit/test-native-eval-search.py:44"/>
<f n="test_native_host_and_tool_names_cannot_be_forged_by_alias" p="tests/speckit-pro/unit/test-native-eval-search.py:190"/>
</group>
<group type="3" gid="293" tokens="123" n="2" similarity="0.81">
<f n="test_resume_reuses_pass_without_reserving_or_scanning_again" p="tests/speckit-pro/unit/test-native-eval-store.py:56"/>
<f n="test_change_grader_regrades_capture_without_subject_retry" p="tests/speckit-pro/unit/test-native-eval-store.py:77"/>
</group>
<group type="3" gid="294" tokens="64" n="2" similarity="0.82">
<f n="test_output_before_grade_survives_interruption" p="tests/speckit-pro/unit/test-native-eval-store.py:95"/>
<f n="test_incomplete_launch_is_not_automatically_repeated" p="tests/speckit-pro/unit/test-native-eval-store.py:101"/>
</group>
<group type="3" gid="295" tokens="48" n="2" similarity="0.89">
<f n="test_resume_verifies_raw_bytes_and_refuses_tampering" p="tests/speckit-pro/unit/test-native-eval-store.py:259"/>
<f n="test_attempt_directory_identity_is_validated" p="tests/speckit-pro/unit/test-native-eval-store.py:299"/>
</group>
<group type="3" gid="296" tokens="271" n="2" similarity="0.92">
<f n="test_generated_python_launcher_forwards_arguments_and_closes_environment" p="tests/speckit-pro/unit/test-native-eval-toolchain.py:222"/>
<f n="test_claude_plugin_launcher_forwards_arguments_and_closes_environment" p="tests/speckit-pro/unit/test-native-eval-toolchain.py:772"/>
</group>
<group type="3" gid="297" tokens="65" n="2" similarity="0.80">
<f n="test_qualification_rejects_staged_bytes_changed_after_identity_binding" p="tests/speckit-pro/unit/test-native-eval-trigger.py:118"/>
<f n="test_codex_unqualified_no_skill_marker_remains_invalid" p="tests/speckit-pro/unit/test-native-eval-trigger.py:292"/>
</group>
<group type="3" gid="298" tokens="158" n="2" similarity="0.82">
<f n="test_claude_qualification_returns_target_wrong_and_genuine_no_selection" p="tests/speckit-pro/unit/test-native-eval-trigger.py:146"/>
<f n="test_claude_no_skill_witness_is_preserved_but_not_a_product_activation" p="tests/speckit-pro/unit/test-native-eval-trigger.py:165"/>
</group>
<group type="3" gid="299" tokens="157" n="2" similarity="0.84">
<f n="test_codex_qualification_requires_matching_read_and_fresh_marker" p="tests/speckit-pro/unit/test-native-eval-trigger.py:212"/>
<f n="test_codex_no_skill_witness_is_preserved_but_not_a_product_activation" p="tests/speckit-pro/unit/test-native-eval-trigger.py:274"/>
</group>
<group type="3" gid="300" tokens="89" n="2" similarity="0.88">
<f n="_runner" p="tests/speckit-pro/unit/test-native-eval-upstream.py:76"/>
<f n="run" p="tests/speckit-pro/unit/test-native-eval-upstream.py:77"/>
</group>
<group type="3" gid="301" tokens="59" n="2" similarity="0.82">
<f n="pointer" p="tests/speckit-pro/unit/test-native-eval-verification.py:104"/>
<f n="is_bound" p="tests/speckit-pro/unit/test-native-parity-catalog.py:865"/>
</group>
<group type="3" gid="302" tokens="81" n="2" similarity="0.89">
<f n="test_genuine_copy_only_record_and_exact_pointer_pass" p="tests/speckit-pro/unit/test-native-eval-verification.py:211"/>
<f n="test_subject_pointer_cannot_outrank_controller_absence" p="tests/speckit-pro/unit/test-native-eval-verification.py:448"/>
</group>
<group type="3" gid="303" tokens="47" n="2" similarity="0.90">
<f n="observation" p="tests/speckit-pro/unit/test-native-functional-catalog.py:425"/>
<f n="observation" p="tests/speckit-pro/unit/test-native-parity-catalog.py:57"/>
</group>
<group type="3" gid="304" tokens="104" n="2" similarity="0.87">
<f n="test_confidence_format_accepts_any_nonempty_value_without_a_hidden_enum" p="tests/speckit-pro/unit/test-native-functional-catalog.py:2159"/>
<f n="test_same_keywords_do_not_bypass_ordered_format_checks" p="tests/speckit-pro/unit/test-native-functional-catalog.py:2176"/>
</group>
<group type="3" gid="305" tokens="130" n="2" similarity="0.96">
<f n="run" p="tests/speckit-pro/unit/test-native-parity-catalog.py:602"/>
<f n="request" p="tests/speckit-pro/unit/test-native-parity-catalog.py:785"/>
</group>
<group type="3" gid="306" tokens="548" n="2" similarity="0.84">
<f n="scaffold_case" p="tests/speckit-pro/unit/test-native-scaffold-noninteractive.py:59"/>
<f n="ambiguity_case" p="tests/speckit-pro/unit/test-native-worktree-migration.py:37"/>
</group>
<group type="3" gid="20" tokens="64" n="2" similarity="0.93">
<f n="load_script" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:32"/>
<f n="import_script" p="tests/speckit-pro/unit/test-trigger-eval-runners.py:57"/>
</group>
<group type="3" gid="20" tokens="59" n="2" similarity="0.98">
<f n="load_module" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:25"/>
<f n="import_script" p="tests/speckit-pro/unit/test-trigger-eval-runners.py:57"/>
</group>
<group type="3" gid="379" tokens="294" n="2" similarity="0.80">
<f n="test_codex_timeout_drains_inherited_pipes_and_removes_owned_descendant" p="tests/speckit-pro/unit/test-trigger-eval-runners.py:503"/>
<f n="test_codex_completed_leader_cannot_leave_an_owned_descendant" p="tests/speckit-pro/unit/test-trigger-eval-runners.py:548"/>
</group>
```

## churn-decay (5 lines)

```xml
<f p="docs-site/src/content/docs/reference/tests.md">
<s t="sec" n="tests/speckit-pro/run-native-evals.py" sc="Records" k="0.0003">
</f>
<f p="tests/speckit-pro/unit/test-trigger-eval-runners.py" layer="test">
</f>
```

## arch (0 lines)

```xml

```

## deps (21 lines)

```xml
<godfiles total="92" shown="12" capped="1">
<f p="tests/speckit-pro/lib/native_eval_catalog.py" afferent="9"/>
</godfiles>
<f p="tests/speckit-pro/lib/native_eval_execution.py" includes="30" afferent="0" instab="1.00" transitive="24">
</f>
<f p="tests/speckit-pro/lib/native_eval_adapters.py" includes="28" afferent="1" instab="0.90" transitive="12">
</f>
<f p="tests/speckit-pro/lib/native_eval_judge.py" includes="7" afferent="1" instab="0.67" transitive="11">
</f>
<f p="tests/speckit-pro/lib/native_eval_claude_activation.py" includes="9" afferent="1" instab="0.50" transitive="10">
</f>
<f p="tests/speckit-pro/lib/native_eval_grading.py" includes="13" afferent="2" instab="0.75" transitive="10">
</f>
<f p="tests/speckit-pro/lib/native_eval_capture.py" includes="9" afferent="3" instab="0.40" transitive="9">
</f>
<f p="tests/speckit-pro/lib/native_eval_codex_rollouts.py" includes="10" afferent="1" instab="0.67" transitive="9">
</f>
<f p="tests/speckit-pro/lib/native_eval_store.py" includes="19" afferent="1" instab="0.67" transitive="9">
</f>
<f p="tests/speckit-pro/lib/native_eval_dispatch_context.py" includes="6" afferent="1" instab="0.50" transitive="8">
</f>
```
