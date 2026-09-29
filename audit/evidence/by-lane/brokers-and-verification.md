# Evidence for lane `brokers-and-verification` (81 files)
Lines from the whole-repo scans that mention this lane's files. Empty section = none found, not none exists.

## doc-drift (7 lines)

```xml
<doc p="tests/speckit-pro/evals/audit/unit-execution-contract-audit.md" anchors="5" checked="3" drift="2" dated="0">
<a k="file-line" l="28" c="112" why="line-moved" ref="tests/speckit-pro/unit/test-execution-control.py:619-623" sym="DockerVerificationTests" got="test_unbound_mismatched_or_ordinary_requests_are_refused_without_mutation" tgt="tests/speckit-pro/unit/test-execution-control.py:3058"/>
</doc>
<weak-file-line p="tests/speckit-pro/evals/audit/unit-execution-contract-audit.md" n="2">
<w l="26" c="169" ref="tests/speckit-pro/unit/test-verification-docker.py:362" resolves-to="DockerRuntimeTests"/>
<w l="26" c="308" ref="tests/speckit-pro/unit/test-verification-git.py:27" resolves-to="GitSnapshotTests"/>
</weak-file-line>
```

## clones (518 lines)

```xml
<group type="2" gid="38" tokens="145" n="2">
<f n="_reserve_gate_remediation" p="speckit-pro/speckit_pro_runner/execution_control.py:1205"/>
<f n="_reserve_increment_review" p="speckit-pro/speckit_pro_runner/execution_control.py:1219"/>
</group>
<group type="2" gid="22" tokens="141" n="2">
<f n="_write_state" p="speckit-pro/speckit_pro_runner/author_broker.py:78"/>
<f n="_write_private_json" p="speckit-pro/speckit_pro_runner/sweep_isolation.py:746"/>
</group>
<group type="2" gid="35" tokens="106" n="3">
<f n="main" p="speckit-pro/speckit_pro_runner/author_broker.py:489"/>
<f n="main" p="speckit-pro/speckit_pro_runner/research_broker.py:1080"/>
<f n="main" p="speckit-pro/speckit_pro_runner/sweep_broker.py:317"/>
</group>
<group type="2" gid="32" tokens="97" n="2">
<f n="_ensure_private_root" p="speckit-pro/speckit_pro_runner/author_broker.py:66"/>
<f n="_ensure_private_directory" p="speckit-pro/speckit_pro_runner/sweep_isolation.py:734"/>
</group>
<group type="2" gid="373" tokens="87" n="2">
<f n="test_phase_boundary_never_shares_batch_or_wave" p="tests/speckit-pro/unit/test-task-execution.py:218"/>
<f n="test_repeated_phase_title_preserves_dispatch_boundary" p="tests/speckit-pro/unit/test-task-execution.py:276"/>
</group>
<group type="2" gid="213" tokens="77" n="2">
<f n="run" p="tests/speckit-pro/unit/test-crap-score.py:29"/>
<f n="run" p="tests/speckit-pro/unit/test-mutation-score.py:42"/>
</group>
<group type="2" gid="370" tokens="74" n="2">
<f n="test_tdd_unit_cannot_span_routes_or_phases" p="tests/speckit-pro/unit/test-task-execution.py:189"/>
<f n="test_tdd_unit_cannot_cross_repeated_phase_title" p="tests/speckit-pro/unit/test-task-execution.py:284"/>
</group>
<group type="2" gid="368" tokens="51" n="3">
<f n="test_dependency_between_batches_serializes_waves" p="tests/speckit-pro/unit/test-task-execution.py:84"/>
<f n="test_shared_and_ancestor_ownership_serializes" p="tests/speckit-pro/unit/test-task-execution.py:90"/>
<f n="test_case_alias_ownership_serializes" p="tests/speckit-pro/unit/test-task-execution.py:96"/>
</group>
<group type="2" gid="371" tokens="46" n="2">
<f n="test_declared_file_reference_must_be_owned" p="tests/speckit-pro/unit/test-task-execution.py:140"/>
<f n="test_explicit_extensionless_paths_still_require_ownership" p="tests/speckit-pro/unit/test-task-execution.py:318"/>
</group>
<group type="3" gid="19" tokens="46" n="2" similarity="0.93">
<f n="parse_json_array" p="scripts/resolve_release_prs.py:25"/>
<f n="_json_object" p="speckit-pro/speckit_pro_runner/verification_docker_runtime.py:214"/>
</group>
<group type="3" gid="21" tokens="58" n="2" similarity="0.93">
<f n="_payload" p="speckit-pro/scripts/sweep-isolation-hook.py:64"/>
<f n="payload" p="speckit-pro/scripts/workflow-guard-hook.py:72"/>
</group>
<group type="3" gid="22" tokens="178" n="2" similarity="0.80">
<f n="_write_attestation" p="speckit-pro/scripts/sweep-isolation-hook.py:105"/>
<f n="_write_state" p="speckit-pro/speckit_pro_runner/author_broker.py:78"/>
</group>
<group type="3" gid="19" tokens="48" n="2" similarity="0.94">
<f n="load_state" p="speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:628"/>
<f n="_json_object" p="speckit-pro/speckit_pro_runner/verification_docker_runtime.py:214"/>
</group>
<group type="3" gid="19" tokens="46" n="2" similarity="0.93">
<f n="_parse_toml" p="speckit-pro/speckit_pro_runner/agent_materialization.py:170"/>
<f n="_json_object" p="speckit-pro/speckit_pro_runner/verification_docker_runtime.py:214"/>
</group>
<group type="3" gid="34" tokens="289" n="2" similarity="0.90">
<f n="handle_message" p="speckit-pro/speckit_pro_runner/author_broker.py:462"/>
<f n="handle_message" p="speckit-pro/speckit_pro_runner/research_broker.py:1051"/>
</group>
<group type="3" gid="34" tokens="362" n="2" similarity="0.89">
<f n="handle_message" p="speckit-pro/speckit_pro_runner/author_broker.py:462"/>
<f n="handle_message" p="speckit-pro/speckit_pro_runner/sweep_broker.py:266"/>
</group>
<group type="3" gid="36" tokens="190" n="2" similarity="0.97">
<f n="_validate_increment_allowances" p="speckit-pro/speckit_pro_runner/execution_control.py:413"/>
<f n="_validate_gate_allowances" p="speckit-pro/speckit_pro_runner/execution_control.py:434"/>
</group>
<group type="3" gid="37" tokens="142" n="2" similarity="0.91">
<f n="_review_remediation" p="speckit-pro/speckit_pro_runner/execution_control.py:916"/>
<f n="_gate_remediation" p="speckit-pro/speckit_pro_runner/execution_control.py:1010"/>
</group>
<group type="3" gid="60" tokens="185" n="2" similarity="0.81">
<f n="probe" p="speckit-pro/speckit_pro_runner/helpers/archive_sweep.py:31"/>
<f n="probe" p="speckit-pro/speckit_pro_runner/helpers/stack_manager.py:27"/>
</group>
<group type="3" gid="61" tokens="45" n="2" similarity="0.85">
<f n="_text" p="speckit-pro/speckit_pro_runner/helpers/egress_authorization.py:42"/>
<f n="_text_argument" p="speckit-pro/speckit_pro_runner/research_broker.py:961"/>
</group>
<group type="3" gid="76" tokens="61" n="2" similarity="0.97">
<f n="sweep_cut_utf8" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:3396"/>
<f n="_bounded_comment_body" p="speckit-pro/speckit_pro_runner/sweep_isolation.py:428"/>
</group>
<group type="3" gid="83" tokens="117" n="2" similarity="0.89">
<f n="codex_preview_prompt_resource" p="speckit-pro/speckit_pro_runner/preview_launcher.py:57"/>
<f n="codex_prompt_resource" p="speckit-pro/speckit_pro_runner/sweep_launcher.py:157"/>
</group>
<group type="3" gid="84" tokens="378" n="2" similarity="0.84">
<f n="codex_preview_command" p="speckit-pro/speckit_pro_runner/preview_launcher.py:95"/>
<f n="codex_command" p="speckit-pro/speckit_pro_runner/sweep_launcher.py:231"/>
</group>
<group type="3" gid="34" tokens="362" n="2" similarity="0.82">
<f n="handle_message" p="speckit-pro/speckit_pro_runner/research_broker.py:1051"/>
<f n="handle_message" p="speckit-pro/speckit_pro_runner/sweep_broker.py:266"/>
</group>
<group type="3" gid="85" tokens="123" n="2" similarity="0.88">
<f n="_run_git" p="speckit-pro/speckit_pro_runner/sweep_isolation.py:118"/>
<f n="_run_gh" p="speckit-pro/speckit_pro_runner/sweep_isolation.py:438"/>
</group>
<group type="3" gid="86" tokens="105" n="2" similarity="0.83">
<f n="record_broker_error" p="speckit-pro/speckit_pro_runner/sweep_isolation.py:997"/>
<f n="broker_error_counts" p="speckit-pro/speckit_pro_runner/sweep_isolation.py:1013"/>
</group>
<group type="3" gid="87" tokens="158" n="2" similarity="0.84">
<f n="_codex_version" p="speckit-pro/speckit_pro_runner/sweep_launcher.py:439"/>
<f n="_verify_codex_features" p="speckit-pro/speckit_pro_runner/sweep_launcher.py:462"/>
</group>
<group type="3" gid="87" tokens="149" n="2" similarity="0.87">
<f n="_codex_version" p="speckit-pro/speckit_pro_runner/sweep_launcher.py:439"/>
<f n="_claude_version" p="speckit-pro/speckit_pro_runner/sweep_launcher.py:602"/>
</group>
<group type="3" gid="88" tokens="66" n="2" similarity="0.83">
<f n="string_list" p="speckit-pro/speckit_pro_runner/task_execution.py:125"/>
<f n="_nonempty_unique" p="tests/speckit-pro/run-native-evals.py:150"/>
</group>
<group type="3" gid="89" tokens="62" n="2" similarity="0.97">
<f n="inspect_image" p="speckit-pro/speckit_pro_runner/verification_docker_image.py:24"/>
<f n="inspect_container" p="speckit-pro/speckit_pro_runner/verification_docker_runtime.py:267"/>
</group>
<group type="3" gid="90" tokens="290" n="2" similarity="0.82">
<f n="decode_evidence" p="speckit-pro/speckit_pro_runner/verification_docker_qualification.py:120"/>
<f n="decode" p="speckit-pro/speckit_pro_runner/verification_docker_qualification.py:123"/>
</group>
<group type="3" gid="91" tokens="88" n="2" similarity="0.80">
<f n="test_agent_instruction_validator_rejects_unexpected_agent_scope" p="tests/speckit-pro/layer1-structural/test-structural-regressions.py:93"/>
<f n="test_copied_spec_text_is_blocked" p="tests/speckit-pro/unit/test-research-broker.py:264"/>
</group>
<group type="3" gid="97" tokens="49" n="2" similarity="0.80">
<f n="run_builder" p="tests/speckit-pro/layer1-structural/validate-payload-contracts.py:33"/>
<f n="run_hook" p="tests/speckit-pro/unit/test-claude-hooks.py:26"/>
</group>
<group type="3" gid="120" tokens="81" n="2" similarity="0.84">
<f n="_git" p="tests/speckit-pro/layer6-integration/run-feedback-sweep-isolation-smoke.py:108"/>
<f n="git" p="tests/speckit-pro/unit/test-feedback-sweep-isolation.py:36"/>
</group>
<group type="3" gid="176" tokens="59" n="2" similarity="0.82">
<f n="test_vendored_extension_accepts_the_positional_single_feature_form" p="tests/speckit-pro/unit/test-archive-invocation-contract.py:160"/>
<f n="test_hidden_html_comments_and_scripts_are_removed" p="tests/speckit-pro/unit/test-research-broker.py:169"/>
</group>
<group type="3" gid="177" tokens="77" n="2" similarity="0.87">
<f n="run_runner" p="tests/speckit-pro/unit/test-artifact-freshness.py:172"/>
<f n="run_runner" p="tests/speckit-pro/unit/test-feedback-sweep-parse.py:180"/>
</group>
<group type="3" gid="179" tokens="65" n="2" similarity="0.81">
<f n="test_non_brokered_receipts_never_verify_a_page" p="tests/speckit-pro/unit/test-artifact-review.py:137"/>
<f n="test_escaping_and_noncanonical_paths_block" p="tests/speckit-pro/unit/test-task-execution.py:102"/>
</group>
<group type="3" gid="120" tokens="80" n="2" similarity="0.80">
<f n="git" p="tests/speckit-pro/unit/test-atomicity-additive-routing.py:31"/>
<f n="git" p="tests/speckit-pro/unit/test-feedback-sweep-isolation.py:36"/>
</group>
<group type="3" gid="191" tokens="67" n="2" similarity="0.85">
<f n="test_claude_explicit_loader_does_not_reinvoke_the_active_skill" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:27"/>
<f n="test_codex_child_process_starts_only_from_the_empty_runtime" p="tests/speckit-pro/unit/test-feedback-sweep-isolation.py:1042"/>
</group>
<group type="3" gid="191" tokens="58" n="2" similarity="0.90">
<f n="test_codex_requires_direct_update_plan_invocation" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:36"/>
<f n="test_codex_child_process_starts_only_from_the_empty_runtime" p="tests/speckit-pro/unit/test-feedback-sweep-isolation.py:1042"/>
</group>
<group type="3" gid="191" tokens="56" n="2" similarity="0.84">
<f n="test_count_growth_is_not_acceptance_and_checkpoint_is_not_completion" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:166"/>
<f n="test_codex_child_process_starts_only_from_the_empty_runtime" p="tests/speckit-pro/unit/test-feedback-sweep-isolation.py:1042"/>
</group>
<group type="3" gid="191" tokens="53" n="2" similarity="0.84">
<f n="test_g4_names_the_deferral" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:362"/>
<f n="test_codex_child_process_starts_only_from_the_empty_runtime" p="tests/speckit-pro/unit/test-feedback-sweep-isolation.py:1042"/>
</group>
<group type="3" gid="201" tokens="236" n="2" similarity="0.83">
<f n="setUp" p="tests/speckit-pro/unit/test-batched-task-results.py:26"/>
<f n="setUp" p="tests/speckit-pro/unit/test-task-execution.py:21"/>
</group>
<group type="3" gid="97" tokens="52" n="2" similarity="0.88">
<f n="run_hook" p="tests/speckit-pro/unit/test-claude-hooks.py:26"/>
<f n="run_runner" p="tests/speckit-pro/unit/test-integration-runners.py:37"/>
</group>
<group type="3" gid="97" tokens="41" n="2" similarity="0.91">
<f n="run_hook" p="tests/speckit-pro/unit/test-claude-hooks.py:26"/>
<f n="run_extractor" p="tests/speckit-pro/unit/test-parity-extractors.py:27"/>
</group>
<group type="3" gid="213" tokens="78" n="2" similarity="0.89">
<f n="run" p="tests/speckit-pro/unit/test-crap-score.py:29"/>
<f n="run_hook" p="tests/speckit-pro/unit/test-workflow-guard-hook.py:36"/>
</group>
<group type="3" gid="215" tokens="79" n="2" similarity="0.87">
<f n="test_prepare_rejects_other_internal_directories" p="tests/speckit-pro/unit/test-docs-artifact.py:86"/>
<f n="test_unsupported_object_dependencies_are_rejected" p="tests/speckit-pro/unit/test-verification-git.py:144"/>
</group>
<group type="3" gid="218" tokens="111" n="2" similarity="0.93">
<f n="test_unknown_families_share_budget_and_nested_hardener_reuses_reservation" p="tests/speckit-pro/unit/test-execution-control.py:142"/>
<f n="test_failed_nested_correction_cannot_launder_another_cycle" p="tests/speckit-pro/unit/test-execution-control.py:152"/>
</group>
<group type="3" gid="218" tokens="111" n="2" similarity="0.81">
<f n="test_unknown_families_share_budget_and_nested_hardener_reuses_reservation" p="tests/speckit-pro/unit/test-execution-control.py:142"/>
<f n="test_expected_tdd_red_is_not_repair_but_verification_red_is_failure" p="tests/speckit-pro/unit/test-execution-control.py:186"/>
</group>
<group type="3" gid="219" tokens="42" n="2" similarity="0.80">
<f n="authorize" p="tests/speckit-pro/unit/test-execution-control.py:498"/>
<f n="correct" p="tests/speckit-pro/unit/test-execution-control.py:2117"/>
</group>
<group type="3" gid="220" tokens="427" n="2" similarity="0.86">
<f n="test_approved_replan_opens_a_fresh_allowance_and_keeps_history" p="tests/speckit-pro/unit/test-execution-control.py:895"/>
<f n="test_operator_stage_transition_opens_a_fresh_allowance_and_keeps_history" p="tests/speckit-pro/unit/test-execution-control.py:981"/>
</group>
<group type="3" gid="221" tokens="130" n="2" similarity="0.88">
<f n="test_both_hosts_document_the_stage_allowance" p="tests/speckit-pro/unit/test-execution-control.py:1090"/>
<f n="test_both_hosts_document_the_metadata_only_correction" p="tests/speckit-pro/unit/test-execution-control.py:2386"/>
</group>
<group type="3" gid="222" tokens="478" n="2" similarity="0.87">
<f n="test_review_fix_inside_owned_paths_is_admitted_after_run_wide_exhaustion_up_to_the_bound" p="tests/speckit-pro/unit/test-execution-control.py:1148"/>
<f n="test_documentation_only_g6_remediation_is_admitted_after_run_wide_exhaustion_up_to_the_bound" p="tests/speckit-pro/unit/test-execution-control.py:1924"/>
</group>
<group type="3" gid="223" tokens="396" n="2" similarity="0.87">
<f n="test_forged_or_overspent_increment_records_fail_closed" p="tests/speckit-pro/unit/test-execution-control.py:1278"/>
<f n="test_forged_or_overspent_gate_records_fail_closed" p="tests/speckit-pro/unit/test-execution-control.py:2015"/>
</group>
<group type="3" gid="224" tokens="232" n="2" similarity="0.99">
<f n="test_stage_epoch_archives_increment_allowances" p="tests/speckit-pro/unit/test-execution-control.py:1308"/>
<f n="test_stage_epoch_archives_gate_allowances" p="tests/speckit-pro/unit/test-execution-control.py:2048"/>
</group>
<group type="3" gid="225" tokens="155" n="2" similarity="0.87">
<f n="test_both_hosts_turn_an_exhausted_budget_into_a_deferral" p="tests/speckit-pro/unit/test-execution-control.py:1516"/>
<f n="test_both_hosts_remediate_while_converging_and_defer_only_on_non_convergence" p="tests/speckit-pro/unit/test-execution-control.py:1893"/>
</group>
<group type="3" gid="226" tokens="102" n="2" similarity="0.86">
<f n="test_a_correction_that_leaves_the_failing_set_unchanged_or_larger_defers" p="tests/speckit-pro/unit/test-execution-control.py:1707"/>
<f n="test_a_narrowed_command_or_a_removed_check_is_not_progress" p="tests/speckit-pro/unit/test-execution-control.py:1741"/>
</group>
<group type="3" gid="226" tokens="89" n="2" similarity="0.85">
<f n="test_a_correction_that_leaves_the_failing_set_unchanged_or_larger_defers" p="tests/speckit-pro/unit/test-execution-control.py:1707"/>
<f n="test_a_failed_correction_or_a_missing_after_state_never_counts_as_progress" p="tests/speckit-pro/unit/test-execution-control.py:1751"/>
</group>
<group type="3" gid="226" tokens="102" n="2" similarity="0.84">
<f n="test_a_narrowed_command_or_a_removed_check_is_not_progress" p="tests/speckit-pro/unit/test-execution-control.py:1741"/>
<f n="test_a_failed_correction_or_a_missing_after_state_never_counts_as_progress" p="tests/speckit-pro/unit/test-execution-control.py:1751"/>
</group>
<group type="3" gid="219" tokens="50" n="2" similarity="0.83">
<f n="gate_fix" p="tests/speckit-pro/unit/test-execution-control.py:1919"/>
<f n="correct" p="tests/speckit-pro/unit/test-execution-control.py:2117"/>
</group>
<group type="3" gid="227" tokens="103" n="2" similarity="0.81">
<f n="test_a_sidecar_absent_from_the_baseline_is_refused" p="tests/speckit-pro/unit/test-execution-control.py:2187"/>
<f n="test_a_scope_change_under_an_open_budget_spends_an_ordinary_cycle" p="tests/speckit-pro/unit/test-execution-control.py:2248"/>
</group>
<group type="3" gid="228" tokens="76" n="2" similarity="0.85">
<f n="test_forged_receipt_and_failed_command_cannot_pass" p="tests/speckit-pro/unit/test-execution-control.py:2644"/>
<f n="test_output_relocation_is_bound_to_independent_observation" p="tests/speckit-pro/unit/test-execution-control.py:2747"/>
</group>
<group type="3" gid="229" tokens="70" n="2" similarity="0.84">
<f n="test_workflow_shell_jq_and_unsupported_executables_are_rejected" p="tests/speckit-pro/unit/test-execution-control.py:2775"/>
<f n="test_docker_command_cannot_silently_rewrite_a_host_executable" p="tests/speckit-pro/unit/test-execution-control.py:3135"/>
</group>
<group type="3" gid="230" tokens="242" n="2" similarity="0.87">
<f n="test_replan_epoch_is_a_real_runner_route" p="tests/speckit-pro/unit/test-execution-control.py:2913"/>
<f n="test_stage_epoch_is_a_real_runner_route" p="tests/speckit-pro/unit/test-execution-control.py:3016"/>
</group>
<group type="3" gid="231" tokens="178" n="2" similarity="0.94">
<f n="test_increment_review_allowance_is_a_real_runner_route" p="tests/speckit-pro/unit/test-execution-control.py:2967"/>
<f n="test_gate_remediation_allowance_is_a_real_runner_route" p="tests/speckit-pro/unit/test-execution-control.py:2983"/>
</group>
<group type="3" gid="231" tokens="210" n="2" similarity="0.83">
<f n="test_increment_review_allowance_is_a_real_runner_route" p="tests/speckit-pro/unit/test-execution-control.py:2967"/>
<f n="test_metadata_only_correction_is_a_real_runner_route" p="tests/speckit-pro/unit/test-execution-control.py:2997"/>
</group>
<group type="3" gid="232" tokens="64" n="2" similarity="0.81">
<f n="test_docker_requires_ledger_reservation_before_daemon_access" p="tests/speckit-pro/unit/test-execution-control.py:3082"/>
<f n="test_invalid_git_scope_refuses_before_reservation_and_daemon" p="tests/speckit-pro/unit/test-verification-git.py:246"/>
</group>
<group type="3" gid="233" tokens="49" n="2" similarity="0.96">
<f n="write" p="tests/speckit-pro/unit/test-feedback-sweep-isolation.py:79"/>
<f n="write_file" p="tests/speckit-pro/unit/test-repo-bash-confinement.py:53"/>
</group>
<group type="3" gid="234" tokens="274" n="2" similarity="0.81">
<f n="test_claude_hook_failure_names_a_code_owned_reason_class" p="tests/speckit-pro/unit/test-feedback-sweep-isolation.py:1476"/>
<f n="test_claude_hook_refusal_never_echoes_untrusted_payload_text" p="tests/speckit-pro/unit/test-feedback-sweep-isolation.py:1547"/>
</group>
<group type="3" gid="235" tokens="219" n="2" similarity="0.86">
<f n="test_claude_hook_rejects_a_symlinked_attestation_record" p="tests/speckit-pro/unit/test-feedback-sweep-isolation.py:1699"/>
<f n="test_parent_rejects_a_symlinked_claude_attestation_record" p="tests/speckit-pro/unit/test-feedback-sweep-isolation.py:1730"/>
</group>
<group type="3" gid="236" tokens="199" n="2" similarity="0.88">
<f n="test_both_surfaces_ship_the_same_adversarial_isolation_eval" p="tests/speckit-pro/unit/test-feedback-sweep-isolation.py:1830"/>
<f n="test_both_surfaces_ship_the_same_sweep_behavior_regression_eval" p="tests/speckit-pro/unit/test-feedback-sweep-isolation.py:1895"/>
</group>
<group type="3" gid="237" tokens="62" n="2" similarity="0.81">
<f n="test_both_classifier_prompts_define_all_four_dispositions" p="tests/speckit-pro/unit/test-feedback-sweep-isolation.py:1862"/>
<f n="test_both_analyst_prompts_define_perspectives_and_synthesis_mapping" p="tests/speckit-pro/unit/test-feedback-sweep-isolation.py:1876"/>
</group>
<group type="3" gid="177" tokens="80" n="2" similarity="0.84">
<f n="run_runner" p="tests/speckit-pro/unit/test-feedback-sweep-parse.py:180"/>
<f n="_runner" p="tests/speckit-pro/unit/test-finalize-run.py:389"/>
</group>
<group type="3" gid="238" tokens="72" n="2" similarity="0.80">
<f n="test_nothing_left_completes_without_a_request" p="tests/speckit-pro/unit/test-finalize-run.py:208"/>
<f n="test_v2_profile_is_qualified_only_after_hermetic_dependency_checks" p="tests/speckit-pro/unit/test-verification-git.py:90"/>
</group>
<group type="3" gid="254" tokens="55" n="2" similarity="0.90">
<f n="test_a_supported_version_is_echoed" p="tests/speckit-pro/unit/test-mcp-protocol-negotiation.py:39"/>
<f n="test_an_unsupported_version_gets_the_latest_supported_one" p="tests/speckit-pro/unit/test-mcp-protocol-negotiation.py:45"/>
</group>
<group type="3" gid="254" tokens="50" n="2" similarity="0.87">
<f n="test_a_supported_version_is_echoed" p="tests/speckit-pro/unit/test-mcp-protocol-negotiation.py:39"/>
<f n="test_missing_params_get_the_latest_supported_version" p="tests/speckit-pro/unit/test-mcp-protocol-negotiation.py:51"/>
</group>
<group type="3" gid="254" tokens="55" n="2" similarity="0.90">
<f n="test_an_unsupported_version_gets_the_latest_supported_one" p="tests/speckit-pro/unit/test-mcp-protocol-negotiation.py:45"/>
<f n="test_missing_params_get_the_latest_supported_version" p="tests/speckit-pro/unit/test-mcp-protocol-negotiation.py:51"/>
</group>
<group type="3" gid="177" tokens="130" n="2" similarity="0.86">
<f n="_run" p="tests/speckit-pro/unit/test-ratify-pr-split.py:46"/>
<f n="run_helper" p="tests/speckit-pro/unit/test-research-broker-preflight.py:363"/>
</group>
<group type="3" gid="177" tokens="129" n="2" similarity="0.86">
<f n="_run" p="tests/speckit-pro/unit/test-ratify-pr-split.py:46"/>
<f n="test_runner_rejects_unknown_inputs" p="tests/speckit-pro/unit/test-research-broker-preflight.py:409"/>
</group>
<group type="3" gid="328" tokens="45" n="2" similarity="0.98">
<f n="write_key" p="tests/speckit-pro/unit/test-research-broker-preflight.py:72"/>
<f n="write_key" p="tests/speckit-pro/unit/test-research-broker.py:149"/>
</group>
<group type="3" gid="329" tokens="119" n="2" similarity="0.86">
<f n="test_ready_with_key_file_is_ok_and_jev_mode" p="tests/speckit-pro/unit/test-research-broker-preflight.py:84"/>
<f n="test_unusable_key_file_is_error_and_every_chunk_drops" p="tests/speckit-pro/unit/test-research-broker-preflight.py:118"/>
</group>
<group type="3" gid="329" tokens="119" n="2" similarity="0.84">
<f n="test_ready_with_key_file_is_ok_and_jev_mode" p="tests/speckit-pro/unit/test-research-broker-preflight.py:84"/>
<f n="test_environment_only_credential_is_ready_but_warns" p="tests/speckit-pro/unit/test-research-broker-preflight.py:179"/>
</group>
<group type="3" gid="329" tokens="119" n="2" similarity="0.83">
<f n="test_ready_with_key_file_is_ok_and_jev_mode" p="tests/speckit-pro/unit/test-research-broker-preflight.py:84"/>
<f n="test_context7_environment_key_is_configured_with_warning" p="tests/speckit-pro/unit/test-research-broker-preflight.py:251"/>
</group>
<group type="3" gid="329" tokens="112" n="2" similarity="0.88">
<f n="test_no_credential_source_is_warning_and_sanitizer_only" p="tests/speckit-pro/unit/test-research-broker-preflight.py:97"/>
<f n="test_unusable_key_file_is_error_and_every_chunk_drops" p="tests/speckit-pro/unit/test-research-broker-preflight.py:118"/>
</group>
<group type="3" gid="329" tokens="88" n="2" similarity="0.83">
<f n="test_no_credential_source_is_warning_and_sanitizer_only" p="tests/speckit-pro/unit/test-research-broker-preflight.py:97"/>
<f n="test_binary_missing_with_credential_is_error" p="tests/speckit-pro/unit/test-research-broker-preflight.py:135"/>
</group>
<group type="3" gid="329" tokens="88" n="2" similarity="0.87">
<f n="test_no_credential_source_is_warning_and_sanitizer_only" p="tests/speckit-pro/unit/test-research-broker-preflight.py:97"/>
<f n="test_binary_older_than_minimum_without_credential_is_warning" p="tests/speckit-pro/unit/test-research-broker-preflight.py:154"/>
</group>
<group type="3" gid="329" tokens="98" n="2" similarity="0.90">
<f n="test_no_credential_source_is_warning_and_sanitizer_only" p="tests/speckit-pro/unit/test-research-broker-preflight.py:97"/>
<f n="test_environment_only_credential_is_ready_but_warns" p="tests/speckit-pro/unit/test-research-broker-preflight.py:179"/>
</group>
<group type="3" gid="329" tokens="88" n="2" similarity="0.82">
<f n="test_no_credential_source_is_warning_and_sanitizer_only" p="tests/speckit-pro/unit/test-research-broker-preflight.py:97"/>
<f n="test_tavily_environment_key_is_configured_with_warning" p="tests/speckit-pro/unit/test-research-broker-preflight.py:231"/>
</group>
<group type="3" gid="329" tokens="95" n="2" similarity="0.82">
<f n="test_no_credential_source_is_warning_and_sanitizer_only" p="tests/speckit-pro/unit/test-research-broker-preflight.py:97"/>
<f n="test_context7_environment_key_is_configured_with_warning" p="tests/speckit-pro/unit/test-research-broker-preflight.py:251"/>
</group>
<group type="3" gid="329" tokens="112" n="2" similarity="0.89">
<f n="test_unusable_key_file_is_error_and_every_chunk_drops" p="tests/speckit-pro/unit/test-research-broker-preflight.py:118"/>
<f n="test_environment_only_credential_is_ready_but_warns" p="tests/speckit-pro/unit/test-research-broker-preflight.py:179"/>
</group>
<group type="3" gid="329" tokens="112" n="2" similarity="0.81">
<f n="test_unusable_key_file_is_error_and_every_chunk_drops" p="tests/speckit-pro/unit/test-research-broker-preflight.py:118"/>
<f n="test_context7_environment_key_is_configured_with_warning" p="tests/speckit-pro/unit/test-research-broker-preflight.py:251"/>
</group>
<group type="3" gid="329" tokens="52" n="2" similarity="0.84">
<f n="test_explicit_key_file_path_that_is_absent_is_configured" p="tests/speckit-pro/unit/test-research-broker-preflight.py:129"/>
<f n="test_context7_key_file_is_configured" p="tests/speckit-pro/unit/test-research-broker-preflight.py:245"/>
</group>
<group type="3" gid="329" tokens="69" n="2" similarity="0.82">
<f n="test_binary_missing_with_credential_is_error" p="tests/speckit-pro/unit/test-research-broker-preflight.py:135"/>
<f n="test_binary_older_than_minimum_without_credential_is_warning" p="tests/speckit-pro/unit/test-research-broker-preflight.py:154"/>
</group>
<group type="3" gid="329" tokens="70" n="2" similarity="0.87">
<f n="test_binary_missing_with_credential_is_error" p="tests/speckit-pro/unit/test-research-broker-preflight.py:135"/>
<f n="test_missing_tavily_key_is_warning_search_unavailable" p="tests/speckit-pro/unit/test-research-broker-preflight.py:209"/>
</group>
<group type="3" gid="329" tokens="68" n="2" similarity="0.89">
<f n="test_binary_missing_with_credential_is_error" p="tests/speckit-pro/unit/test-research-broker-preflight.py:135"/>
<f n="test_tavily_key_file_with_group_bits_is_error" p="tests/speckit-pro/unit/test-research-broker-preflight.py:217"/>
</group>
<group type="3" gid="329" tokens="68" n="2" similarity="0.83">
<f n="test_binary_missing_with_credential_is_error" p="tests/speckit-pro/unit/test-research-broker-preflight.py:135"/>
<f n="test_context7_key_file_is_configured" p="tests/speckit-pro/unit/test-research-broker-preflight.py:245"/>
</group>
<group type="3" gid="329" tokens="95" n="2" similarity="0.83">
<f n="test_binary_missing_with_credential_is_error" p="tests/speckit-pro/unit/test-research-broker-preflight.py:135"/>
<f n="test_context7_environment_key_is_configured_with_warning" p="tests/speckit-pro/unit/test-research-broker-preflight.py:251"/>
</group>
<group type="3" gid="329" tokens="75" n="2" similarity="0.81">
<f n="test_binary_missing_with_credential_is_error" p="tests/speckit-pro/unit/test-research-broker-preflight.py:135"/>
<f n="test_symlinked_key_file_is_not_regular" p="tests/speckit-pro/unit/test-research-broker-preflight.py:261"/>
</group>
<group type="3" gid="329" tokens="69" n="2" similarity="0.89">
<f n="test_binary_older_than_minimum_without_credential_is_warning" p="tests/speckit-pro/unit/test-research-broker-preflight.py:154"/>
<f n="test_tavily_environment_key_is_configured_with_warning" p="tests/speckit-pro/unit/test-research-broker-preflight.py:231"/>
</group>
<group type="3" gid="329" tokens="63" n="2" similarity="0.82">
<f n="test_unparseable_version_fails_closed" p="tests/speckit-pro/unit/test-research-broker-preflight.py:161"/>
<f n="test_empty_variables_count_as_unset" p="tests/speckit-pro/unit/test-research-broker-preflight.py:189"/>
</group>
<group type="3" gid="329" tokens="70" n="2" similarity="0.81">
<f n="test_unparseable_version_fails_closed" p="tests/speckit-pro/unit/test-research-broker-preflight.py:161"/>
<f n="test_missing_tavily_key_is_warning_search_unavailable" p="tests/speckit-pro/unit/test-research-broker-preflight.py:209"/>
</group>
<group type="3" gid="329" tokens="63" n="2" similarity="0.81">
<f n="test_unparseable_version_fails_closed" p="tests/speckit-pro/unit/test-research-broker-preflight.py:161"/>
<f n="test_tavily_key_file_with_group_bits_is_error" p="tests/speckit-pro/unit/test-research-broker-preflight.py:217"/>
</group>
<group type="3" gid="329" tokens="61" n="2" similarity="0.84">
<f n="test_unparseable_version_fails_closed" p="tests/speckit-pro/unit/test-research-broker-preflight.py:161"/>
<f n="test_context7_is_optional_and_keyless_is_not_a_warning" p="tests/speckit-pro/unit/test-research-broker-preflight.py:237"/>
</group>
<group type="3" gid="329" tokens="61" n="2" similarity="0.83">
<f n="test_unparseable_version_fails_closed" p="tests/speckit-pro/unit/test-research-broker-preflight.py:161"/>
<f n="test_context7_key_file_is_configured" p="tests/speckit-pro/unit/test-research-broker-preflight.py:245"/>
</group>
<group type="3" gid="329" tokens="107" n="2" similarity="0.80">
<f n="test_unknown_check_exit_code_fails_closed" p="tests/speckit-pro/unit/test-research-broker-preflight.py:168"/>
<f n="test_context7_environment_key_is_configured_with_warning" p="tests/speckit-pro/unit/test-research-broker-preflight.py:251"/>
</group>
<group type="3" gid="329" tokens="98" n="2" similarity="0.83">
<f n="test_environment_only_credential_is_ready_but_warns" p="tests/speckit-pro/unit/test-research-broker-preflight.py:179"/>
<f n="test_context7_environment_key_is_configured_with_warning" p="tests/speckit-pro/unit/test-research-broker-preflight.py:251"/>
</group>
<group type="3" gid="329" tokens="63" n="2" similarity="0.81">
<f n="test_empty_variables_count_as_unset" p="tests/speckit-pro/unit/test-research-broker-preflight.py:189"/>
<f n="test_context7_key_file_is_configured" p="tests/speckit-pro/unit/test-research-broker-preflight.py:245"/>
</group>
<group type="3" gid="329" tokens="70" n="2" similarity="0.86">
<f n="test_missing_tavily_key_is_warning_search_unavailable" p="tests/speckit-pro/unit/test-research-broker-preflight.py:209"/>
<f n="test_tavily_key_file_with_group_bits_is_error" p="tests/speckit-pro/unit/test-research-broker-preflight.py:217"/>
</group>
<group type="3" gid="329" tokens="95" n="2" similarity="0.85">
<f n="test_missing_tavily_key_is_warning_search_unavailable" p="tests/speckit-pro/unit/test-research-broker-preflight.py:209"/>
<f n="test_context7_environment_key_is_configured_with_warning" p="tests/speckit-pro/unit/test-research-broker-preflight.py:251"/>
</group>
<group type="3" gid="329" tokens="75" n="2" similarity="0.81">
<f n="test_missing_tavily_key_is_warning_search_unavailable" p="tests/speckit-pro/unit/test-research-broker-preflight.py:209"/>
<f n="test_symlinked_key_file_is_not_regular" p="tests/speckit-pro/unit/test-research-broker-preflight.py:261"/>
</group>
<group type="3" gid="329" tokens="63" n="2" similarity="0.86">
<f n="test_tavily_key_file_with_group_bits_is_error" p="tests/speckit-pro/unit/test-research-broker-preflight.py:217"/>
<f n="test_context7_key_file_is_configured" p="tests/speckit-pro/unit/test-research-broker-preflight.py:245"/>
</group>
<group type="3" gid="329" tokens="75" n="2" similarity="0.88">
<f n="test_tavily_key_file_with_group_bits_is_error" p="tests/speckit-pro/unit/test-research-broker-preflight.py:217"/>
<f n="test_symlinked_key_file_is_not_regular" p="tests/speckit-pro/unit/test-research-broker-preflight.py:261"/>
</group>
<group type="3" gid="329" tokens="58" n="2" similarity="0.85">
<f n="test_context7_is_optional_and_keyless_is_not_a_warning" p="tests/speckit-pro/unit/test-research-broker-preflight.py:237"/>
<f n="test_context7_key_file_is_configured" p="tests/speckit-pro/unit/test-research-broker-preflight.py:245"/>
</group>
<group type="3" gid="177" tokens="130" n="2" similarity="0.85">
<f n="run_helper" p="tests/speckit-pro/unit/test-research-broker-preflight.py:363"/>
<f n="test_runner_rejects_unknown_inputs" p="tests/speckit-pro/unit/test-research-broker-preflight.py:409"/>
</group>
<group type="3" gid="330" tokens="79" n="2" similarity="0.90">
<f n="test_secret_shapes_are_blocked" p="tests/speckit-pro/unit/test-research-broker.py:236"/>
<f n="test_local_paths_are_blocked" p="tests/speckit-pro/unit/test-research-broker.py:253"/>
</group>
<group type="3" gid="331" tokens="57" n="2" similarity="0.95">
<f n="test_severity_turns_quarantine_into_block_but_does_not_block_alone" p="tests/speckit-pro/unit/test-research-broker.py:295"/>
<f n="test_permissive_policy_moves_only_the_action_threshold" p="tests/speckit-pro/unit/test-research-broker.py:302"/>
</group>
<group type="3" gid="332" tokens="84" n="2" similarity="0.80">
<f n="test_no_time_left_fails_the_fetch_without_a_request" p="tests/speckit-pro/unit/test-research-broker.py:457"/>
<f n="test_deterministic_outbound_block_happens_in_both_modes_before_fetch" p="tests/speckit-pro/unit/test-research-broker.py:498"/>
</group>
<group type="3" gid="332" tokens="84" n="2" similarity="0.85">
<f n="test_no_time_left_fails_the_fetch_without_a_request" p="tests/speckit-pro/unit/test-research-broker.py:457"/>
<f n="test_key_file_wins_and_a_broken_file_does_not_fall_back" p="tests/speckit-pro/unit/test-research-broker.py:557"/>
</group>
<group type="3" gid="332" tokens="78" n="2" similarity="0.83">
<f n="test_deterministic_outbound_block_happens_in_both_modes_before_fetch" p="tests/speckit-pro/unit/test-research-broker.py:498"/>
<f n="test_key_file_wins_and_a_broken_file_does_not_fall_back" p="tests/speckit-pro/unit/test-research-broker.py:557"/>
</group>
<group type="3" gid="332" tokens="78" n="2" similarity="0.81">
<f n="test_deterministic_outbound_block_happens_in_both_modes_before_fetch" p="tests/speckit-pro/unit/test-research-broker.py:498"/>
<f n="test_broken_context7_key_file_does_not_fall_back_to_keyless" p="tests/speckit-pro/unit/test-research-broker.py:571"/>
</group>
<group type="3" gid="332" tokens="78" n="2" similarity="0.83">
<f n="test_key_file_wins_and_a_broken_file_does_not_fall_back" p="tests/speckit-pro/unit/test-research-broker.py:557"/>
<f n="test_broken_context7_key_file_does_not_fall_back_to_keyless" p="tests/speckit-pro/unit/test-research-broker.py:571"/>
</group>
<group type="3" gid="368" tokens="54" n="2" similarity="0.93">
<f n="test_dependency_between_batches_serializes_waves" p="tests/speckit-pro/unit/test-task-execution.py:84"/>
<f n="test_capability_changes_break_batches" p="tests/speckit-pro/unit/test-task-execution.py:113"/>
</group>
<group type="3" gid="369" tokens="58" n="2" similarity="0.88">
<f n="test_symlink_escape_blocks" p="tests/speckit-pro/unit/test-task-execution.py:108"/>
<f n="test_symlink_descendants_require_narrower_explicit_ownership" p="tests/speckit-pro/unit/test-task-execution.py:323"/>
</group>
<group type="3" gid="370" tokens="62" n="2" similarity="0.89">
<f n="test_split_tdd_completion_blocks_test_only_green" p="tests/speckit-pro/unit/test-task-execution.py:127"/>
<f n="test_completed_task_requires_completed_prerequisites" p="tests/speckit-pro/unit/test-task-execution.py:177"/>
</group>
<group type="3" gid="370" tokens="74" n="2" similarity="0.85">
<f n="test_split_tdd_completion_blocks_test_only_green" p="tests/speckit-pro/unit/test-task-execution.py:127"/>
<f n="test_tdd_unit_cannot_span_routes_or_phases" p="tests/speckit-pro/unit/test-task-execution.py:189"/>
</group>
<group type="3" gid="371" tokens="50" n="2" similarity="0.88">
<f n="test_declared_file_reference_must_be_owned" p="tests/speckit-pro/unit/test-task-execution.py:140"/>
<f n="test_slash_separated_prose_does_not_invent_file_ownership" p="tests/speckit-pro/unit/test-task-execution.py:291"/>
</group>
<group type="3" gid="372" tokens="82" n="2" similarity="0.84">
<f n="test_internal_symlink_alias_ownership_serializes" p="tests/speckit-pro/unit/test-task-execution.py:196"/>
<f n="test_unicode_normalization_aliases_are_not_parallel" p="tests/speckit-pro/unit/test-task-execution.py:268"/>
</group>
<group type="3" gid="374" tokens="82" n="2" similarity="0.99">
<f n="test_root_level_references_require_ownership" p="tests/speckit-pro/unit/test-task-execution.py:226"/>
<f n="test_escaping_title_references_are_not_silently_dropped" p="tests/speckit-pro/unit/test-task-execution.py:244"/>
</group>
<group type="3" gid="381" tokens="54" n="2" similarity="0.87">
<f n="test_unsupported_host_never_calls_prctl" p="tests/speckit-pro/unit/test-verification-docker.py:254"/>
<f n="test_filter_install_failure_prevents_command_execution" p="tests/speckit-pro/unit/test-verification-docker.py:260"/>
</group>
```

## churn-decay (28 lines)

```xml
<recent n="40" of="1331" merge_bombs_skipped="5">
<rc p="speckit-pro/speckit_pro_runner/execution_control.py" age_d="0" w="19.8"/>
<rc p="tests/speckit-pro/unit/test-execution-control.py" age_d="0" w="17.7"/>
</recent>
<f p="speckit-pro/speckit_pro_runner/sweep_launcher.py">
</f>
<f p="speckit-pro/scripts/mutation-score.py">
</f>
<f p="tests/speckit-pro/unit/test-feedback-sweep-parse.py" layer="test">
</f>
<f p="tests/speckit-pro/unit/test-task-execution.py" layer="test">
</f>
<f p="speckit-pro/speckit_pro_runner/verification_records.py">
</f>
<f p="tests/speckit-pro/unit/test-feedback-sweep-isolation.py" layer="test">
</f>
<f p="speckit-pro/speckit_pro_runner/sweep_isolation.py">
</f>
<f p="tests/speckit-pro/unit/test-execution-control.py" layer="test">
</f>
<f p="speckit-pro/speckit_pro_runner/verification_docker_workflow.py">
</f>
<f p="speckit-pro/speckit_pro_runner/verification_docker_qualification.py">
</f>
<f p="speckit-pro/speckit_pro_runner/verification_docker_runtime.py">
</f>
<f p="speckit-pro/speckit_pro_runner/execution_control.py">
</f>
```

## arch (12 lines)

```xml
<v from="./speckit-pro/speckit_pro_runner/execution_control.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/read_only.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/execution_control.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/read_only.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/execution_control.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/read_only.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/execution_control.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/read_only.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/sweep_isolation.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/mutation.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/sweep_isolation.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/read_only.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/sweep_isolation.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/read_only.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/task_results.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/mutation.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/task_results.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/mutation.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/task_results.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/mutation.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/task_results.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/read_only.py" toLayer="helpers" baselined="1"/>
<v from="./speckit-pro/speckit_pro_runner/task_results.py" fromLayer="core" to="./speckit-pro/speckit_pro_runner/helpers/read_only.py" toLayer="helpers" baselined="1"/>
```

## deps (45 lines)

```xml
<godfiles total="92" shown="12" capped="1">
<f p="speckit-pro/speckit_pro_runner/execution_control.py" afferent="10"/>
<f p="speckit-pro/speckit_pro_runner/task_execution.py" afferent="7"/>
</godfiles>
<stabledeps violations="26">
<v from="speckit-pro/speckit_pro_runner/execution_control.py" to="speckit-pro/speckit_pro_runner/task_results.py" gap="0.34"/>
<v from="speckit-pro/speckit_pro_runner/verification_records.py" to="speckit-pro/speckit_pro_runner/verification_docker_workflow.py" gap="0.33"/>
<v from="speckit-pro/speckit_pro_runner/helpers/mutation.py" to="speckit-pro/speckit_pro_runner/execution_control.py" gap="0.23"/>
<v from="speckit-pro/speckit_pro_runner/verification_records.py" to="speckit-pro/speckit_pro_runner/verification_docker_qualification.py" gap="0.20"/>
<v from="speckit-pro/speckit_pro_runner/sweep_isolation.py" to="speckit-pro/speckit_pro_runner/helpers/read_only.py" gap="0.17"/>
</stabledeps>
<cycle size="2" cost="4" cut="speckit-pro/speckit_pro_runner/verification_docker_readback.py -&gt; speckit-pro/speckit_pro_runner/verification_docker_runtime.py" cutrefs="1">
<f p="speckit-pro/speckit_pro_runner/verification_docker_runtime.py"/>
<f p="speckit-pro/speckit_pro_runner/verification_docker_readback.py"/>
</cycle>
<cycle size="20" cost="400" cut="speckit-pro/speckit_pro_runner/author_broker.py -&gt; speckit-pro/speckit_pro_runner/helpers/mutation.py" cutrefs="1">
<f p="speckit-pro/speckit_pro_runner/helpers/archive_sweep.py"/>
<f p="speckit-pro/speckit_pro_runner/task_results.py"/>
<f p="speckit-pro/speckit_pro_runner/verification_docker_qualification.py"/>
<f p="speckit-pro/speckit_pro_runner/verification_git.py"/>
<f p="speckit-pro/speckit_pro_runner/verification_docker_workflow.py"/>
<f p="speckit-pro/speckit_pro_runner/verification_records.py"/>
<f p="speckit-pro/speckit_pro_runner/sweep_isolation.py"/>
<f p="speckit-pro/speckit_pro_runner/sweep_launcher.py"/>
</cycle>
<f p="speckit-pro/speckit_pro_runner/sweep_broker.py" includes="7" afferent="0" instab="1.00" transitive="59">
</f>
<f p="speckit-pro/speckit_pro_runner/execution_control.py" includes="26" afferent="10" instab="0.57" transitive="58">
</f>
<f p="speckit-pro/speckit_pro_runner/helpers/archive_sweep.py" includes="9" afferent="1" instab="0.67" transitive="58">
</f>
<f p="speckit-pro/speckit_pro_runner/sweep_isolation.py" includes="20" afferent="5" instab="0.38" transitive="58">
</f>
<f p="speckit-pro/speckit_pro_runner/sweep_launcher.py" includes="13" afferent="2" instab="0.33" transitive="58">
</f>
<f p="speckit-pro/speckit_pro_runner/task_results.py" includes="16" afferent="1" instab="0.91" transitive="58">
</f>
<f p="speckit-pro/speckit_pro_runner/verification_docker_qualification.py" includes="14" afferent="3" instab="0.70" transitive="58">
</f>
<f p="speckit-pro/speckit_pro_runner/verification_docker_workflow.py" includes="16" afferent="2" instab="0.83" transitive="58">
</f>
<f p="speckit-pro/speckit_pro_runner/verification_git.py" includes="9" afferent="1" instab="0.67" transitive="58">
</f>
<f p="speckit-pro/speckit_pro_runner/verification_records.py" includes="20" afferent="5" instab="0.50" transitive="58">
</f>
```
