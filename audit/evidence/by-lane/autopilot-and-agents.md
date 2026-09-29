# Evidence for lane `autopilot-and-agents` (70 files)
Lines from the whole-repo scans that mention this lane's files. Empty section = none found, not none exists.

## doc-drift (38 lines)

```xml
<doc p="docs/ai/research/tool-agnostic-capability-discovery-spike.md" anchors="51" checked="18" drift="16" dated="0">
<a k="file-line" l="68" c="37" why="range-straddles" ref="speckit-pro/agents/domain-researcher.md:11-18" got="Domain Researcher — Consensus Agent" tgt="speckit-pro/agents/domain-researcher.md:18"/>
<a k="file-line" l="75" c="32" why="past-eof" ref="speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml:9-16" got="7 lines" tgt="speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml"/>
<a k="file-line" l="93" c="235" why="past-eof" ref="speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml:9-16" got="7 lines" tgt="speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml"/>
<a k="file-line" l="120" c="347" why="past-eof" ref="speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml:9-16" got="7 lines" tgt="speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml"/>
<a k="file-line" l="137" c="120" why="past-eof" ref="speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml:9-16" got="7 lines" tgt="speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml"/>
</doc>
<doc p="docs/ai/specs/.process/ART-006-design-concept.md" anchors="38" checked="15" drift="12" dated="1">
<a k="file-line" l="319" c="29" why="past-eof" ref="codex-skills/speckit-autopilot/SKILL.md:986-992" got="825 lines" tgt="speckit-pro/codex-skills/speckit-autopilot/SKILL.md"/>
</doc>
<doc p="docs/ai/specs/.process/ART-014-workflow.md" anchors="138" checked="84" drift="6" dated="0">
<a k="file-line" l="1832" c="3" why="range-straddles" ref="validate-autopilot-phase-coverage.py:257-481" got="PROBLEM_KEY_INTENT" tgt="speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:481"/>
<a k="file-line" l="1847" c="3" why="range-straddles" ref="validate-autopilot-phase-coverage.py:1529-1583" got="_marker_tasks_sha_text" tgt="speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:1583"/>
</doc>
<doc p="speckit-pro/codex-skills/speckit-autopilot/references/prerequisites-codex.md" anchors="110" checked="49" drift="2" dated="0">
</doc>
<doc p="tests/speckit-pro/evals/audit/unit-execution-contract-audit.md" anchors="5" checked="3" drift="2" dated="0">
<a k="file-line" l="27" c="153" why="range-straddles" ref="tests/speckit-pro/unit/test-autopilot-execution-contract.py:25-81" got="test_both_hosts_load_one_durable_contract" tgt="tests/speckit-pro/unit/test-autopilot-execution-contract.py:81"/>
</doc>
<doc p="speckit-pro/codex-skills/speckit-autopilot/references/task-list-canonical-codex.md" anchors="20" checked="7" drift="1" dated="0">
</doc>
<doc p="speckit-pro/skills/speckit-autopilot/references/phase-execution.md" anchors="183" checked="60" drift="1" dated="0">
</doc>
<doc p="speckit-pro/skills/speckit-autopilot/references/post-implementation.md" anchors="17" checked="5" drift="1" dated="0">
</doc>
<weak-file-line p="docs/ai/research/tool-agnostic-capability-discovery-spike.md" n="9">
<w l="70" c="35" ref="speckit-pro/codex-agents/codebase-analyst.toml:35-52" resolves-to="developer_instructions"/>
<w l="71" c="36" ref="speckit-pro/codex-agents/domain-researcher.toml:33-49" resolves-to="developer_instructions"/>
<w l="72" c="31" ref="speckit-pro/codex-agents/implement-executor.toml:69-99" resolves-to="developer_instructions"/>
<w l="95" c="197" ref="speckit-pro/codex-agents/codebase-analyst.toml:40-52" resolves-to="developer_instructions"/>
<w l="136" c="183" ref="speckit-pro/codex-agents/domain-researcher.toml:33-49" resolves-to="developer_instructions"/>
</weak-file-line>
<weak-file-line p="docs/ai/specs/html-artifacts-technical-roadmap.md" n="5">
<w l="1021" c="6" ref="speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:1298" resolves-to="_read_repo_file_by_descriptor"/>
</weak-file-line>
<weak-file-line p="tests/speckit-pro/layer6-integration/performance-fixtures/implementation-notes/source/plan.md" n="1">
<w l="249" c="37" ref="speckit-pro/agents/implement-executor.md:164" resolves-to="Summary Format"/>
</weak-file-line>
```

## clones (724 lines)

```xml
<group type="2" gid="26" tokens="145" n="2">
<f n="_json_schema_type_matches" p="speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:1406"/>
<f n="json_schema_type_matches" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:7016"/>
</group>
<group type="2" gid="25" tokens="73" n="2">
<f n="_json_values_equal" p="speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:1398"/>
<f n="json_values_equal" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:7030"/>
</group>
<group type="2" gid="29" tokens="68" n="2">
<f n="_workflow_table_rows" p="speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:4414"/>
<f n="_table_row_indexes" p="tests/speckit-pro/layer1-structural/validate-ci-release-contracts.py:1093"/>
</group>
<group type="2" gid="186" tokens="48" n="2">
<f n="test_claude_phase_seven_applies_a_recorded_decision_to_ambiguous_wording" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:878"/>
<f n="test_codex_phase_seven_applies_a_recorded_decision_to_ambiguous_wording" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:884"/>
</group>
<group type="2" gid="197" tokens="40" n="2">
<f n="runner_env" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1030"/>
<f n="runner_env" p="tests/speckit-pro/unit/test-estimate-spec-size.py:42"/>
</group>
<group type="3" gid="19" tokens="44" n="2" similarity="0.95">
<f n="parse_json_array" p="scripts/resolve_release_prs.py:25"/>
<f n="_parse_toml" p="speckit-pro/speckit_pro_runner/agent_materialization.py:170"/>
</group>
<group type="3" gid="20" tokens="64" n="2" similarity="0.92">
<f n="regenerated_artifact_paths" p="scripts/sync_release_pr.py:70"/>
<f n="load_privacy_scan_module" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:78"/>
</group>
<group type="3" gid="19" tokens="48" n="2" similarity="0.94">
<f n="load_state" p="speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:628"/>
<f n="_json_object" p="speckit-pro/speckit_pro_runner/verification_docker_runtime.py:214"/>
</group>
<group type="3" gid="23" tokens="129" n="2" similarity="0.82">
<f n="_pending_value_paths" p="speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:1003"/>
<f n="iter_input_strings" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:8750"/>
</group>
<group type="3" gid="24" tokens="48" n="2" similarity="0.97">
<f n="_stable_file_identity" p="speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:1055"/>
<f n="_file_identity" p="tests/speckit-pro/lib/trigger_carry_forward.py:187"/>
</group>
<group type="3" gid="27" tokens="79" n="2" similarity="0.95">
<f n="_resolve_schema_reference" p="speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:1423"/>
<f n="resolve_local_schema_reference" p="speckit-pro/speckit_pro_runner/helpers/read_only.py:7004"/>
</group>
<group type="3" gid="28" tokens="76" n="2" similarity="0.93">
<f n="_git_file_at_commit" p="speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:1597"/>
<f n="_git_commit_exists" p="speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:1856"/>
</group>
<group type="3" gid="30" tokens="50" n="2" similarity="0.97">
<f n="workflow_criteria_rows" p="speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:4435"/>
<f n="criteria_row_indexes" p="tests/speckit-pro/layer1-structural/validate-ci-release-contracts.py:1112"/>
</group>
<group type="3" gid="19" tokens="46" n="2" similarity="0.93">
<f n="_parse_toml" p="speckit-pro/speckit_pro_runner/agent_materialization.py:170"/>
<f n="_json_object" p="speckit-pro/speckit_pro_runner/verification_docker_runtime.py:214"/>
</group>
<group type="3" gid="20" tokens="54" n="2" similarity="0.85">
<f n="load_module" p="tests/speckit-pro/layer1-structural/test-structural-regressions.py:23"/>
<f n="_load" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:76"/>
</group>
<group type="3" gid="20" tokens="54" n="2" similarity="0.83">
<f n="load_module" p="tests/speckit-pro/layer1-structural/test-structural-regressions.py:23"/>
<f n="load_coverage_validator" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1061"/>
</group>
<group type="3" gid="20" tokens="60" n="2" similarity="0.87">
<f n="load_coverage_validator" p="tests/speckit-pro/layer1-structural/validate-ci-release-contracts.py:1188"/>
<f n="load_validator_module" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:62"/>
</group>
<group type="3" gid="20" tokens="60" n="2" similarity="0.84">
<f n="load_coverage_validator" p="tests/speckit-pro/layer1-structural/validate-ci-release-contracts.py:1188"/>
<f n="load_coverage_validator" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1061"/>
</group>
<group type="3" gid="20" tokens="51" n="2" similarity="0.86">
<f n="_load_run_all" p="tests/speckit-pro/test-run-all.py:34"/>
<f n="_load" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:76"/>
</group>
<group type="3" gid="20" tokens="51" n="2" similarity="0.94">
<f n="_load_run_all" p="tests/speckit-pro/test-run-all.py:34"/>
<f n="load_coverage_validator" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1061"/>
</group>
<group type="3" gid="171" tokens="64" n="2" similarity="0.90">
<f n="run_tool" p="tests/speckit-pro/unit/test-agent-memory-ignore.py:28"/>
<f n="run_status_evidence_report" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:256"/>
</group>
<group type="3" gid="171" tokens="56" n="2" similarity="0.81">
<f n="run_tool" p="tests/speckit-pro/unit/test-agent-memory-ignore.py:28"/>
<f n="run" p="tests/speckit-pro/unit/test-ubiquitous-language-lint.py:36"/>
</group>
<group type="3" gid="172" tokens="71" n="2" similarity="0.81">
<f n="test_nested_override_is_reported" p="tests/speckit-pro/unit/test-agent-memory-ignore.py:64"/>
<f n="test_symlink_ignore_file_is_rejected" p="tests/speckit-pro/unit/test-agent-memory-ignore.py:82"/>
</group>
<group type="3" gid="172" tokens="78" n="2" similarity="0.91">
<f n="test_symlink_ignore_file_is_rejected" p="tests/speckit-pro/unit/test-agent-memory-ignore.py:82"/>
<f n="test_symlink_memory_directory_is_rejected" p="tests/speckit-pro/unit/test-agent-memory-ignore.py:91"/>
</group>
<group type="3" gid="173" tokens="76" n="2" similarity="0.87">
<f n="test_budget_bound_roles_reserve_their_last_turns_for_partial_results" p="tests/speckit-pro/unit/test-agent-terminal-contracts.py:160"/>
<f n="test_artifact_author_reads_the_gallery_the_orchestrator_passes" p="tests/speckit-pro/unit/test-agent-terminal-contracts.py:202"/>
</group>
<group type="3" gid="173" tokens="76" n="2" similarity="0.81">
<f n="test_budget_bound_roles_reserve_their_last_turns_for_partial_results" p="tests/speckit-pro/unit/test-agent-terminal-contracts.py:160"/>
<f n="test_security_relevant_field_is_in_every_output_format" p="tests/speckit-pro/unit/test-consensus-analyst-shared-prose.py:200"/>
</group>
<group type="3" gid="20" tokens="59" n="2" similarity="0.82">
<f n="_load_coverage_tests" p="tests/speckit-pro/unit/test-autonomy-boundary-receipt-replay.py:38"/>
<f n="load_validator_module" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:62"/>
</group>
<group type="3" gid="20" tokens="62" n="2" similarity="0.97">
<f n="_load_coverage_tests" p="tests/speckit-pro/unit/test-autonomy-boundary-receipt-replay.py:38"/>
<f n="load_privacy_scan_module" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:78"/>
</group>
<group type="3" gid="20" tokens="45" n="2" similarity="0.92">
<f n="_load" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:76"/>
<f n="load_coverage_validator" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1061"/>
</group>
<group type="3" gid="20" tokens="49" n="2" similarity="0.90">
<f n="_load" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:76"/>
<f n="load_helper" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:27"/>
</group>
<group type="3" gid="20" tokens="57" n="2" similarity="0.82">
<f n="_load" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:76"/>
<f n="load_module" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:25"/>
</group>
<group type="3" gid="171" tokens="88" n="2" similarity="0.84">
<f n="run_status_evidence_report" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:256"/>
<f n="_run" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:2004"/>
</group>
<group type="3" gid="171" tokens="70" n="2" similarity="0.84">
<f n="run_status_evidence_report" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:256"/>
<f n="_run_coverage_guard" p="tests/speckit-pro/unit/test-native-functional-catalog.py:729"/>
</group>
<group type="3" gid="183" tokens="57" n="2" similarity="0.84">
<f n="test_recorded_gate_pass_requires_a_terminal_row" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:385"/>
<f n="test_terminal_row_after_open_row_is_an_ordering_error" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:392"/>
</group>
<group type="3" gid="184" tokens="221" n="2" similarity="0.83">
<f n="test_source_contract_places_preflight_before_every_phase_seven_entry" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:450"/>
<f n="test_resume_re_attests_a_stale_boundary_before_the_coverage_guard" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:485"/>
</group>
<group type="3" gid="184" tokens="225" n="2" similarity="0.82">
<f n="test_resume_re_attests_a_stale_boundary_before_the_coverage_guard" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:485"/>
<f n="test_codex_autopilot_worktree_handoff_contract" p="tests/speckit-pro/unit/test-eval-runner-skill-selection.py:676"/>
</group>
<group type="3" gid="184" tokens="199" n="2" similarity="0.82">
<f n="test_resume_re_attests_a_stale_boundary_before_the_coverage_guard" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:485"/>
<f n="test_claude_autopilot_same_session_cd_handoff_contract" p="tests/speckit-pro/unit/test-eval-runner-skill-selection.py:711"/>
</group>
<group type="3" gid="185" tokens="52" n="2" similarity="0.92">
<f n="assert_deferral_rules" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:619"/>
<f n="assert_class_rules" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:811"/>
</group>
<group type="3" gid="186" tokens="86" n="2" similarity="0.89">
<f n="test_codex_phase_seven_defers_a_blocked_action_and_continues" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:643"/>
<f n="test_claude_phase_seven_mirrors_the_deferral_rule" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:672"/>
</group>
<group type="3" gid="186" tokens="86" n="2" similarity="0.85">
<f n="test_codex_phase_seven_defers_a_blocked_action_and_continues" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:643"/>
<f n="test_claude_phase_execution_states_the_class_rule" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:839"/>
</group>
<group type="3" gid="186" tokens="86" n="2" similarity="0.86">
<f n="test_codex_phase_seven_defers_a_blocked_action_and_continues" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:643"/>
<f n="test_codex_phase_seven_records_drift_and_continues" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:933"/>
</group>
<group type="3" gid="187" tokens="95" n="2" similarity="0.81">
<f n="test_codex_entrypoint_and_post_audit_allow_an_honest_deferred_end" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:658"/>
<f n="test_claude_entrypoint_and_recovery_mirror_the_deferred_end" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:685"/>
</group>
<group type="3" gid="186" tokens="77" n="2" similarity="0.81">
<f n="test_claude_phase_seven_mirrors_the_deferral_rule" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:672"/>
<f n="test_claude_phase_execution_states_the_class_rule" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:839"/>
</group>
<group type="3" gid="186" tokens="71" n="2" similarity="0.93">
<f n="test_claude_phase_seven_mirrors_the_deferral_rule" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:672"/>
<f n="test_codex_phase_seven_records_drift_and_continues" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:933"/>
</group>
<group type="3" gid="186" tokens="57" n="2" similarity="0.84">
<f n="test_codex_phase_execution_states_the_class_rule" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:831"/>
<f n="test_claude_phase_seven_applies_a_recorded_decision_to_ambiguous_wording" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:878"/>
</group>
<group type="3" gid="186" tokens="77" n="2" similarity="0.82">
<f n="test_claude_phase_execution_states_the_class_rule" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:839"/>
<f n="test_codex_phase_seven_records_drift_and_continues" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:933"/>
</group>
<group type="3" gid="186" tokens="67" n="2" similarity="0.80">
<f n="test_claude_phase_seven_applies_a_recorded_decision_to_ambiguous_wording" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:878"/>
<f n="test_codex_phase_seven_records_drift_and_continues" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:933"/>
</group>
<group type="3" gid="188" tokens="98" n="2" similarity="0.85">
<f n="test_writable_roots_are_sorted_strings_and_malformed_input_never_crashes" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:1103"/>
<f n="test_automatic_review_and_prior_execution_are_not_authorization" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:1230"/>
</group>
<group type="3" gid="189" tokens="87" n="2" similarity="0.83">
<f n="test_both_hosts_digest_event_ids_and_remediate_privacy_errors_once" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:1818"/>
<f n="test_both_hosts_route_budget_splits_through_the_helper" p="tests/speckit-pro/unit/test-ratify-pr-split.py:201"/>
</group>
<group type="3" gid="189" tokens="107" n="2" similarity="0.84">
<f n="test_both_hosts_digest_external_ids_in_every_committed_record" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:1920"/>
<f n="test_both_hosts_route_budget_splits_through_the_helper" p="tests/speckit-pro/unit/test-ratify-pr-split.py:201"/>
</group>
<group type="3" gid="171" tokens="124" n="2" similarity="0.80">
<f n="_run" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:2004"/>
<f n="test_state_named_relatively_from_a_subdirectory_is_still_compared" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:2042"/>
</group>
<group type="3" gid="171" tokens="90" n="2" similarity="0.91">
<f n="_run" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:2004"/>
<f n="_emitted_problem_keys" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:2256"/>
</group>
<group type="3" gid="171" tokens="124" n="2" similarity="0.80">
<f n="test_state_named_relatively_from_a_subdirectory_is_still_compared" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:2042"/>
<f n="_emitted_problem_keys" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:2256"/>
</group>
<group type="3" gid="190" tokens="182" n="2" similarity="0.80">
<f n="test_state_without_a_workflow_file_key_skips_the_comparison" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:2075"/>
<f n="test_supplied_workflow_outside_the_repository_fails" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:2136"/>
</group>
<group type="3" gid="191" tokens="67" n="2" similarity="0.93">
<f n="test_claude_explicit_loader_does_not_reinvoke_the_active_skill" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:27"/>
<f n="test_codex_requires_direct_update_plan_invocation" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:36"/>
</group>
<group type="3" gid="191" tokens="74" n="2" similarity="0.89">
<f n="test_claude_explicit_loader_does_not_reinvoke_the_active_skill" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:27"/>
<f n="test_native_dispatch_keeps_direct_route_and_owned_cleanup" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:156"/>
</group>
<group type="3" gid="191" tokens="67" n="2" similarity="0.86">
<f n="test_claude_explicit_loader_does_not_reinvoke_the_active_skill" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:27"/>
<f n="test_g4_names_the_deferral" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:362"/>
</group>
<group type="3" gid="191" tokens="67" n="2" similarity="0.85">
<f n="test_claude_explicit_loader_does_not_reinvoke_the_active_skill" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:27"/>
<f n="test_codex_child_process_starts_only_from_the_empty_runtime" p="tests/speckit-pro/unit/test-feedback-sweep-isolation.py:1042"/>
</group>
<group type="3" gid="191" tokens="74" n="2" similarity="0.88">
<f n="test_codex_requires_direct_update_plan_invocation" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:36"/>
<f n="test_native_dispatch_keeps_direct_route_and_owned_cleanup" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:156"/>
</group>
<group type="3" gid="191" tokens="58" n="2" similarity="0.93">
<f n="test_codex_requires_direct_update_plan_invocation" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:36"/>
<f n="test_g4_names_the_deferral" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:362"/>
</group>
<group type="3" gid="191" tokens="58" n="2" similarity="0.90">
<f n="test_codex_requires_direct_update_plan_invocation" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:36"/>
<f n="test_codex_child_process_starts_only_from_the_empty_runtime" p="tests/speckit-pro/unit/test-feedback-sweep-isolation.py:1042"/>
</group>
<group type="3" gid="191" tokens="74" n="2" similarity="0.81">
<f n="test_native_dispatch_keeps_direct_route_and_owned_cleanup" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:156"/>
<f n="test_g4_names_the_deferral" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:362"/>
</group>
<group type="3" gid="191" tokens="56" n="2" similarity="0.84">
<f n="test_count_growth_is_not_acceptance_and_checkpoint_is_not_completion" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:166"/>
<f n="test_codex_child_process_starts_only_from_the_empty_runtime" p="tests/speckit-pro/unit/test-feedback-sweep-isolation.py:1042"/>
</group>
<group type="3" gid="191" tokens="53" n="2" similarity="0.84">
<f n="test_g4_names_the_deferral" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:362"/>
<f n="test_codex_child_process_starts_only_from_the_empty_runtime" p="tests/speckit-pro/unit/test-feedback-sweep-isolation.py:1042"/>
</group>
<group type="3" gid="192" tokens="58" n="2" similarity="0.84">
<f n="test_workflow_protocol_lists_the_record_on_both_hosts" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:369"/>
<f n="test_pr_body_tells_the_reviewer_the_boxes_are_theirs" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:377"/>
</group>
<group type="3" gid="192" tokens="47" n="2" similarity="0.96">
<f n="test_pr_body_tells_the_reviewer_the_boxes_are_theirs" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:377"/>
<f n="test_both_hosts_keep_one_live_ratification_value" p="tests/speckit-pro/unit/test-ratify-pr-split.py:222"/>
</group>
<group type="3" gid="192" tokens="47" n="2" similarity="0.93">
<f n="test_pr_body_tells_the_reviewer_the_boxes_are_theirs" p="tests/speckit-pro/unit/test-autopilot-execution-contract.py:377"/>
<f n="test_split_evidence_is_no_longer_operator_only" p="tests/speckit-pro/unit/test-ratify-pr-split.py:229"/>
</group>
<group type="3" gid="193" tokens="47" n="2" similarity="0.89">
<f n="test_permission_mode_guidance_is_consistent_across_skill_and_references" p="tests/speckit-pro/unit/test-autopilot-permission-mode-guidance.py:61"/>
<f n="test_grounding_note_is_byte_identical" p="tests/speckit-pro/unit/test-consensus-analyst-shared-prose.py:191"/>
</group>
<group type="3" gid="193" tokens="49" n="2" similarity="0.88">
<f n="test_permission_mode_guidance_is_consistent_across_skill_and_references" p="tests/speckit-pro/unit/test-autopilot-permission-mode-guidance.py:61"/>
<f n="test_terminal_deliverable_is_identical_modulo_the_section_triple" p="tests/speckit-pro/unit/test-consensus-analyst-shared-prose.py:231"/>
</group>
<group type="3" gid="20" tokens="59" n="2" similarity="0.81">
<f n="load_validator_module" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:62"/>
<f n="load_coverage_validator" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1061"/>
</group>
<group type="3" gid="20" tokens="59" n="2" similarity="0.98">
<f n="load_validator_module" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:62"/>
<f n="load_composer" p="tests/speckit-pro/unit/test-compose-release-notes.py:54"/>
</group>
<group type="3" gid="20" tokens="59" n="2" similarity="0.87">
<f n="load_validator_module" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:62"/>
<f n="load_script_module" p="tests/speckit-pro/unit/test-integration-runners.py:49"/>
</group>
<group type="3" gid="20" tokens="64" n="2" similarity="0.89">
<f n="load_validator_module" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:62"/>
<f n="load_script" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:32"/>
</group>
<group type="3" gid="20" tokens="59" n="2" similarity="0.95">
<f n="load_validator_module" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:62"/>
<f n="load_module" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:25"/>
</group>
<group type="3" gid="20" tokens="59" n="2" similarity="0.97">
<f n="load_validator_module" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:62"/>
<f n="import_script" p="tests/speckit-pro/unit/test-trigger-eval-runners.py:57"/>
</group>
<group type="3" gid="20" tokens="63" n="2" similarity="0.85">
<f n="load_privacy_scan_module" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:78"/>
<f n="load_gate_tests" p="tests/speckit-pro/unit/test-installed-release-gates.py:21"/>
</group>
<group type="3" gid="20" tokens="62" n="2" similarity="0.85">
<f n="load_privacy_scan_module" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:78"/>
<f n="load_script_module" p="tests/speckit-pro/unit/test-integration-runners.py:49"/>
</group>
<group type="3" gid="194" tokens="60" n="2" similarity="0.88">
<f n="test_complete_workflow_and_state_pass" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:479"/>
<f n="test_missing_confidence_gate_in_workflow_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3567"/>
</group>
<group type="3" gid="194" tokens="49" n="2" similarity="0.92">
<f n="test_complete_workflow_and_state_pass" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:479"/>
<f n="test_missing_confidence_gate_in_state_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3574"/>
</group>
<group type="3" gid="194" tokens="49" n="2" similarity="0.94">
<f n="test_complete_workflow_and_state_pass" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:479"/>
<f n="test_missing_post_items_in_state_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3580"/>
</group>
<group type="3" gid="194" tokens="60" n="2" similarity="0.86">
<f n="test_complete_workflow_and_state_pass" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:479"/>
<f n="test_collapsed_later_phase_plan_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3586"/>
</group>
<group type="3" gid="194" tokens="55" n="2" similarity="0.86">
<f n="test_complete_workflow_and_state_pass" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:479"/>
<f n="test_malformed_state_is_input_error" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3614"/>
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
<group type="3" gid="195" tokens="60" n="2" similarity="0.82">
<f n="test_pending_markers_await_their_first_checkpoint" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:726"/>
<f n="test_awaiting_marker_row_must_read_pending" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:744"/>
</group>
<group type="3" gid="196" tokens="67" n="2" similarity="0.87">
<f n="test_completed_phase_rejects_pending_verification_fields" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:819"/>
<f n="test_plan_phase_and_checkpoint_statuses_must_agree" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:833"/>
</group>
<group type="3" gid="196" tokens="67" n="2" similarity="0.87">
<f n="test_completed_phase_rejects_pending_verification_fields" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:819"/>
<f n="test_checkpointing_phase_must_not_project_as_completed" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:843"/>
</group>
<group type="3" gid="196" tokens="71" n="2" similarity="0.83">
<f n="test_completed_phase_rejects_pending_verification_fields" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:819"/>
<f n="test_every_implementation_phase_requires_a_declared_marker_owner" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:853"/>
</group>
<group type="3" gid="196" tokens="74" n="2" similarity="0.87">
<f n="test_completed_phase_rejects_pending_verification_fields" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:819"/>
<f n="test_malformed_marker_task_arrays_fail_without_crashing" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:964"/>
</group>
<group type="3" gid="196" tokens="74" n="2" similarity="0.88">
<f n="test_completed_phase_rejects_pending_verification_fields" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:819"/>
<f n="test_emitted_mapping_requires_packet_and_pr_identity" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:978"/>
</group>
<group type="3" gid="196" tokens="71" n="2" similarity="0.88">
<f n="test_completed_phase_rejects_pending_verification_fields" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:819"/>
<f n="test_top_level_emitted_requires_every_marker_mapping_emitted" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:997"/>
</group>
<group type="3" gid="196" tokens="64" n="2" similarity="0.89">
<f n="test_plan_phase_and_checkpoint_statuses_must_agree" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:833"/>
<f n="test_checkpointing_phase_must_not_project_as_completed" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:843"/>
</group>
<group type="3" gid="196" tokens="71" n="2" similarity="0.81">
<f n="test_plan_phase_and_checkpoint_statuses_must_agree" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:833"/>
<f n="test_top_level_emitted_requires_every_marker_mapping_emitted" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:997"/>
</group>
<group type="3" gid="196" tokens="71" n="2" similarity="0.85">
<f n="test_checkpointing_phase_must_not_project_as_completed" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:843"/>
<f n="test_every_implementation_phase_requires_a_declared_marker_owner" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:853"/>
</group>
<group type="3" gid="196" tokens="74" n="2" similarity="0.83">
<f n="test_checkpointing_phase_must_not_project_as_completed" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:843"/>
<f n="test_emitted_mapping_requires_packet_and_pr_identity" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:978"/>
</group>
<group type="3" gid="196" tokens="74" n="2" similarity="0.83">
<f n="test_every_implementation_phase_requires_a_declared_marker_owner" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:853"/>
<f n="test_malformed_marker_task_arrays_fail_without_crashing" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:964"/>
</group>
<group type="3" gid="196" tokens="74" n="2" similarity="0.86">
<f n="test_every_implementation_phase_requires_a_declared_marker_owner" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:853"/>
<f n="test_emitted_mapping_requires_packet_and_pr_identity" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:978"/>
</group>
<group type="3" gid="196" tokens="71" n="2" similarity="0.85">
<f n="test_every_implementation_phase_requires_a_declared_marker_owner" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:853"/>
<f n="test_top_level_emitted_requires_every_marker_mapping_emitted" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:997"/>
</group>
<group type="3" gid="196" tokens="95" n="2" similarity="0.81">
<f n="test_every_implementation_phase_requires_a_declared_marker_owner" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:853"/>
<f n="test_v2_marker_plan_requires_changed_file_manifest_reference" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3468"/>
</group>
<group type="3" gid="196" tokens="84" n="2" similarity="0.84">
<f n="test_complete_checkpoint_requires_terminal_evidence" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:869"/>
<f n="test_emitted_mapping_requires_packet_and_pr_identity" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:978"/>
</group>
<group type="3" gid="196" tokens="74" n="2" similarity="0.94">
<f n="test_malformed_marker_task_arrays_fail_without_crashing" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:964"/>
<f n="test_top_level_emitted_requires_every_marker_mapping_emitted" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:997"/>
</group>
<group type="3" gid="196" tokens="74" n="2" similarity="0.81">
<f n="test_emitted_mapping_requires_packet_and_pr_identity" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:978"/>
<f n="test_top_level_emitted_requires_every_marker_mapping_emitted" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:997"/>
</group>
<group type="3" gid="194" tokens="60" n="2" similarity="0.84">
<f n="test_missing_confidence_gate_in_workflow_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3567"/>
<f n="test_missing_confidence_gate_in_state_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3574"/>
</group>
<group type="3" gid="194" tokens="60" n="2" similarity="0.84">
<f n="test_missing_confidence_gate_in_workflow_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3567"/>
<f n="test_missing_post_items_in_state_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3580"/>
</group>
<group type="3" gid="194" tokens="60" n="2" similarity="0.92">
<f n="test_missing_confidence_gate_in_workflow_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3567"/>
<f n="test_collapsed_later_phase_plan_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3586"/>
</group>
<group type="3" gid="194" tokens="60" n="2" similarity="0.90">
<f n="test_missing_confidence_gate_in_workflow_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3567"/>
<f n="test_malformed_state_is_input_error" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3614"/>
</group>
<group type="3" gid="194" tokens="60" n="2" similarity="0.80">
<f n="test_missing_confidence_gate_in_workflow_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3567"/>
<f n="test_rename_out_of_preflight_surface_still_runs_heavy_jobs" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:521"/>
</group>
<group type="3" gid="194" tokens="49" n="2" similarity="0.96">
<f n="test_missing_confidence_gate_in_state_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3574"/>
<f n="test_missing_post_items_in_state_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3580"/>
</group>
<group type="3" gid="194" tokens="60" n="2" similarity="0.88">
<f n="test_missing_confidence_gate_in_state_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3574"/>
<f n="test_collapsed_later_phase_plan_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3586"/>
</group>
<group type="3" gid="194" tokens="55" n="2" similarity="0.87">
<f n="test_missing_confidence_gate_in_state_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3574"/>
<f n="test_malformed_state_is_input_error" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3614"/>
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
<group type="3" gid="194" tokens="60" n="2" similarity="0.88">
<f n="test_missing_post_items_in_state_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3580"/>
<f n="test_collapsed_later_phase_plan_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3586"/>
</group>
<group type="3" gid="194" tokens="55" n="2" similarity="0.83">
<f n="test_missing_post_items_in_state_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3580"/>
<f n="test_malformed_state_is_input_error" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3614"/>
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
<group type="3" gid="194" tokens="60" n="2" similarity="0.87">
<f n="test_collapsed_later_phase_plan_fails" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3586"/>
<f n="test_malformed_state_is_input_error" p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py:3614"/>
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
<group type="3" gid="197" tokens="42" n="2" similarity="0.90">
<f n="runner_env" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1030"/>
<f n="runner_env" p="tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:243"/>
</group>
<group type="3" gid="177" tokens="107" n="2" similarity="0.81">
<f n="run_runner" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1038"/>
<f n="run_estimator" p="tests/speckit-pro/unit/test-estimate-spec-size.py:74"/>
</group>
<group type="3" gid="177" tokens="109" n="2" similarity="0.81">
<f n="run_runner" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1038"/>
<f n="_run" p="tests/speckit-pro/unit/test-ratify-pr-split.py:46"/>
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
<group type="3" gid="20" tokens="45" n="2" similarity="0.81">
<f n="load_coverage_validator" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1061"/>
<f n="load_layer_script_dispatcher" p="tests/speckit-pro/unit/test-speckit-pro-gates.py:206"/>
</group>
<group type="3" gid="198" tokens="63" n="2" similarity="0.84">
<f n="test_explicit_stage_argument_resolves_from_argv" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1081"/>
<f n="test_from_phase_never_conflicts_with_an_auto_detected_stage" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1094"/>
</group>
<group type="3" gid="198" tokens="76" n="2" similarity="0.88">
<f n="test_explicit_stage_argument_resolves_from_argv" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1081"/>
<f n="test_planning_predicate_covers_the_six_rows_plus_the_confidence_gate" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1144"/>
</group>
<group type="3" gid="198" tokens="63" n="2" similarity="0.80">
<f n="test_explicit_stage_argument_resolves_from_argv" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1081"/>
<f n="test_recorded_stage_reads_the_basic_information_row" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1153"/>
</group>
<group type="3" gid="198" tokens="63" n="2" similarity="0.88">
<f n="test_explicit_stage_argument_resolves_from_argv" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1081"/>
<f n="test_envelope_echoes_the_confidence_gate_status_row" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1478"/>
</group>
<group type="3" gid="198" tokens="63" n="2" similarity="0.82">
<f n="test_explicit_stage_argument_resolves_from_argv" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1081"/>
<f n="test_the_field_is_the_same_row_the_planning_predicate_reads" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1530"/>
</group>
<group type="3" gid="198" tokens="63" n="2" similarity="0.83">
<f n="test_explicit_stage_argument_resolves_from_argv" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1081"/>
<f n="test_auto_detection_resolves_the_expected_stage_and_source" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1556"/>
</group>
<group type="3" gid="198" tokens="76" n="2" similarity="0.84">
<f n="test_planning_predicate_covers_the_six_rows_plus_the_confidence_gate" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1144"/>
<f n="test_envelope_echoes_the_confidence_gate_status_row" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1478"/>
</group>
<group type="3" gid="198" tokens="76" n="2" similarity="0.81">
<f n="test_planning_predicate_covers_the_six_rows_plus_the_confidence_gate" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1144"/>
<f n="test_the_field_is_the_same_row_the_planning_predicate_reads" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1530"/>
</group>
<group type="3" gid="198" tokens="76" n="2" similarity="0.84">
<f n="test_planning_predicate_covers_the_six_rows_plus_the_confidence_gate" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1144"/>
<f n="test_auto_detection_resolves_the_expected_stage_and_source" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1556"/>
</group>
<group type="3" gid="198" tokens="62" n="2" similarity="0.80">
<f n="test_recorded_stage_reads_the_basic_information_row" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1153"/>
<f n="test_envelope_echoes_the_confidence_gate_status_row" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1478"/>
</group>
<group type="3" gid="198" tokens="62" n="2" similarity="0.87">
<f n="test_recorded_stage_reads_the_basic_information_row" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1153"/>
<f n="test_the_field_is_the_same_row_the_planning_predicate_reads" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1530"/>
</group>
<group type="3" gid="198" tokens="62" n="2" similarity="0.83">
<f n="test_recorded_stage_reads_the_basic_information_row" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1153"/>
<f n="test_auto_detection_resolves_the_expected_stage_and_source" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1556"/>
</group>
<group type="3" gid="199" tokens="61" n="2" similarity="0.88">
<f n="test_unreadable_workflow_file_is_rejected_rather_than_defaulted" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1181"/>
<f n="test_empty_workflow_file_input_is_rejected" p="tests/speckit-pro/unit/test-consensus-routing-helpers.py:389"/>
</group>
<group type="3" gid="200" tokens="49" n="2" similarity="0.80">
<f n="test_gap_note_after_the_link_still_parses_the_identity" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1254"/>
<f n="test_the_envelope_adds_corroboration_as_a_ninth_key" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1424"/>
</group>
<group type="3" gid="200" tokens="44" n="2" similarity="0.95">
<f n="test_each_status_is_produced_by_its_own_input" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1313"/>
<f n="test_a_successful_observation_is_classified_against_the_recorded_identity" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1321"/>
</group>
<group type="3" gid="200" tokens="44" n="2" similarity="0.92">
<f n="test_each_status_is_produced_by_its_own_input" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1313"/>
<f n="test_an_extra_open_pull_request_outranks_every_later_rule" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1331"/>
</group>
<group type="3" gid="200" tokens="51" n="2" similarity="0.84">
<f n="test_each_status_is_produced_by_its_own_input" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1313"/>
<f n="test_an_absent_observation_is_skipped_with_the_recorded_identity_intact" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1361"/>
</group>
<group type="3" gid="200" tokens="43" n="2" similarity="0.96">
<f n="test_a_successful_observation_is_classified_against_the_recorded_identity" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1321"/>
<f n="test_an_extra_open_pull_request_outranks_every_later_rule" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1331"/>
</group>
<group type="3" gid="200" tokens="51" n="2" similarity="0.84">
<f n="test_a_successful_observation_is_classified_against_the_recorded_identity" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1321"/>
<f n="test_an_absent_observation_is_skipped_with_the_recorded_identity_intact" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1361"/>
</group>
<group type="3" gid="200" tokens="43" n="2" similarity="0.82">
<f n="test_a_successful_observation_is_classified_against_the_recorded_identity" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1321"/>
<f n="test_the_envelope_adds_corroboration_as_a_ninth_key" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1424"/>
</group>
<group type="3" gid="200" tokens="51" n="2" similarity="0.81">
<f n="test_an_extra_open_pull_request_outranks_every_later_rule" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1331"/>
<f n="test_an_absent_observation_is_skipped_with_the_recorded_identity_intact" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1361"/>
</group>
<group type="3" gid="200" tokens="43" n="2" similarity="0.81">
<f n="test_an_extra_open_pull_request_outranks_every_later_rule" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1331"/>
<f n="test_the_envelope_adds_corroboration_as_a_ninth_key" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1424"/>
</group>
<group type="3" gid="198" tokens="62" n="2" similarity="0.85">
<f n="test_envelope_echoes_the_confidence_gate_status_row" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1478"/>
<f n="test_the_field_is_the_same_row_the_planning_predicate_reads" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1530"/>
</group>
<group type="3" gid="198" tokens="60" n="2" similarity="0.90">
<f n="test_envelope_echoes_the_confidence_gate_status_row" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1478"/>
<f n="test_auto_detection_resolves_the_expected_stage_and_source" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1556"/>
</group>
<group type="3" gid="198" tokens="62" n="2" similarity="0.85">
<f n="test_the_field_is_the_same_row_the_planning_predicate_reads" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1530"/>
<f n="test_auto_detection_resolves_the_expected_stage_and_source" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1556"/>
</group>
<group type="3" gid="178" tokens="71" n="2" similarity="0.80">
<f n="test_a_strict_mode_gate_stop_never_auto_detects_implement" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1575"/>
<f n="test_the_basis_reports_completion_when_no_row_is_open" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1596"/>
</group>
<group type="3" gid="178" tokens="71" n="2" similarity="0.80">
<f n="test_a_strict_mode_gate_stop_never_auto_detects_implement" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1575"/>
<f n="test_reordered_groups_route_to_operator" p="tests/speckit-pro/unit/test-ratify-pr-split.py:101"/>
</group>
<group type="3" gid="178" tokens="71" n="2" similarity="0.80">
<f n="test_a_strict_mode_gate_stop_never_auto_detects_implement" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1575"/>
<f n="assert_response" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:613"/>
</group>
<group type="3" gid="170" tokens="51" n="2" similarity="0.90">
<f n="build_suite" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1855"/>
<f n="build_suite" p="tests/speckit-pro/unit/test-phase7-task-partition.py:602"/>
</group>
<group type="3" gid="207" tokens="48" n="2" similarity="0.87">
<f n="test_shared_input_bullets_are_byte_identical" p="tests/speckit-pro/unit/test-consensus-analyst-shared-prose.py:169"/>
<f n="test_codex_mirrors_carry_the_shared_input_bullets" p="tests/speckit-pro/unit/test-consensus-analyst-shared-prose.py:259"/>
</group>
<group type="3" gid="193" tokens="49" n="2" similarity="0.91">
<f n="test_grounding_note_is_byte_identical" p="tests/speckit-pro/unit/test-consensus-analyst-shared-prose.py:191"/>
<f n="test_terminal_deliverable_is_identical_modulo_the_section_triple" p="tests/speckit-pro/unit/test-consensus-analyst-shared-prose.py:231"/>
</group>
<group type="3" gid="208" tokens="108" n="2" similarity="0.81">
<f n="aggregate" p="tests/speckit-pro/unit/test-consensus-routing-helpers.py:112"/>
<f n="partition" p="tests/speckit-pro/unit/test-phase7-task-partition.py:45"/>
</group>
<group type="3" gid="209" tokens="62" n="2" similarity="0.83">
<f n="test_each_single_category_tag_routes_to_its_own_analyst" p="tests/speckit-pro/unit/test-consensus-routing-helpers.py:130"/>
<f n="test_unbounded_sed_still_rejects_expansion_and_incomplete_output" p="tests/speckit-pro/unit/test-native-eval-fixture-reads.py:104"/>
</group>
<group type="3" gid="194" tokens="51" n="2" similarity="0.91">
<f n="test_security_keyword_in_the_item_text_widens_a_narrow_tag" p="tests/speckit-pro/unit/test-consensus-routing-helpers.py:144"/>
<f n="test_unknown_tag_routes_to_all_three" p="tests/speckit-pro/unit/test-consensus-routing-helpers.py:219"/>
</group>
<group type="3" gid="194" tokens="59" n="2" similarity="0.85">
<f n="test_security_keyword_in_the_item_text_widens_a_narrow_tag" p="tests/speckit-pro/unit/test-consensus-routing-helpers.py:144"/>
<f n="test_absent_log_aggregates_to_zero_without_failing" p="tests/speckit-pro/unit/test-consensus-routing-helpers.py:339"/>
</group>
<group type="3" gid="210" tokens="95" n="2" similarity="0.84">
<f n="test_reference_example_yields_the_documented_escape_rate" p="tests/speckit-pro/unit/test-consensus-routing-helpers.py:267"/>
<f n="test_the_record_names_its_tool_and_inputs" p="tests/speckit-pro/unit/test-phase7-task-partition.py:524"/>
</group>
<group type="3" gid="211" tokens="67" n="2" similarity="0.93">
<f n="test_arrow_alone_counts_as_an_escape_without_an_outcome_column" p="tests/speckit-pro/unit/test-consensus-routing-helpers.py:287"/>
<f n="test_spaced_and_emphasized_arrow_counts_as_an_escalation" p="tests/speckit-pro/unit/test-consensus-routing-helpers.py:300"/>
</group>
<group type="3" gid="211" tokens="67" n="2" similarity="0.93">
<f n="test_arrow_alone_counts_as_an_escape_without_an_outcome_column" p="tests/speckit-pro/unit/test-consensus-routing-helpers.py:287"/>
<f n="test_unreadable_round_cell_counts_as_round_one" p="tests/speckit-pro/unit/test-consensus-routing-helpers.py:328"/>
</group>
<group type="3" gid="211" tokens="60" n="2" similarity="0.98">
<f n="test_spaced_and_emphasized_arrow_counts_as_an_escalation" p="tests/speckit-pro/unit/test-consensus-routing-helpers.py:300"/>
<f n="test_unreadable_round_cell_counts_as_round_one" p="tests/speckit-pro/unit/test-consensus-routing-helpers.py:328"/>
</group>
<group type="3" gid="194" tokens="59" n="2" similarity="0.82">
<f n="test_absent_log_aggregates_to_zero_without_failing" p="tests/speckit-pro/unit/test-consensus-routing-helpers.py:339"/>
<f n="test_threshold_percent_is_an_input" p="tests/speckit-pro/unit/test-consensus-routing-helpers.py:367"/>
</group>
<group type="3" gid="194" tokens="59" n="2" similarity="0.85">
<f n="test_absent_log_aggregates_to_zero_without_failing" p="tests/speckit-pro/unit/test-consensus-routing-helpers.py:339"/>
<f n="test_rename_out_of_preflight_surface_still_runs_heavy_jobs" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:521"/>
</group>
<group type="3" gid="199" tokens="64" n="2" similarity="0.86">
<f n="test_empty_workflow_file_input_is_rejected" p="tests/speckit-pro/unit/test-consensus-routing-helpers.py:389"/>
<f n="test_a_missing_tasks_file_is_an_input_error" p="tests/speckit-pro/unit/test-phase7-task-partition.py:483"/>
</group>
```

## churn-decay (60 lines)

```xml
<recent n="40" of="1331" merge_bombs_skipped="5">
<rc p="speckit-pro/skills/speckit-autopilot/SKILL.md" age_d="0" w="70.4"/>
<rc p="speckit-pro/skills/speckit-autopilot/references/phase-execution.md" age_d="0" w="70.1"/>
<rc p="speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md" age_d="0" w="63.4"/>
<rc p="speckit-pro/codex-skills/speckit-autopilot/SKILL.md" age_d="0" w="63"/>
<rc p="speckit-pro/codex-skills/speckit-autopilot/references/prerequisites-codex.md" age_d="0" w="28.7"/>
<rc p="speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md" age_d="0" w="26.1"/>
<rc p="speckit-pro/skills/speckit-autopilot/references/gate-validation.md" age_d="0" w="25.9"/>
<rc p="speckit-pro/skills/speckit-autopilot/references/post-implementation.md" age_d="0" w="25.4"/>
<rc p="speckit-pro/skills/speckit-autopilot/references/prerequisites.md" age_d="0" w="22.6"/>
<rc p="speckit-pro/skills/speckit-autopilot/references/execution-efficiency.md" age_d="0" w="18.8"/>
<rc p="speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md" age_d="0" w="18.3"/>
<rc p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py" age_d="0" w="16.7"/>
<rc p="speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py" age_d="0" w="16.2"/>
<rc p="speckit-pro/agents/checklist-executor.md" age_d="0" w="14.6"/>
<rc p="speckit-pro/agents/analyze-executor.md" age_d="0" w="13.4"/>
<rc p="speckit-pro/codex-skills/speckit-autopilot/references/error-recovery-codex.md" age_d="0" w="12.6"/>
<rc p="speckit-pro/codex-agents/checklist-executor.toml" age_d="0" w="12.5"/>
<rc p="speckit-pro/agents/clarify-executor.md" age_d="0" w="12.5"/>
<rc p="speckit-pro/codex-agents/analyze-executor.toml" age_d="0" w="11.7"/>
<rc p="speckit-pro/agents/consensus-synthesizer.md" age_d="0" w="11.6"/>
</recent>
<f p="speckit-pro/skills/speckit-autopilot/SKILL.md">
</f>
<f p="speckit-pro/codex-skills/speckit-autopilot/references/prerequisites-codex.md">
</f>
<f p="speckit-pro/skills/speckit-autopilot/references/prerequisites.md">
</f>
<f p="speckit-pro/skills/speckit-autopilot/references/task-list-canonical.md">
</f>
<f p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py" layer="test">
</f>
<f p="speckit-pro/speckit_pro_runner/agent_materialization.py">
</f>
<f p="speckit-pro/codex-skills/speckit-autopilot/references/task-list-canonical-codex.md">
</f>
<f p="speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md">
</f>
<f p="tests/speckit-pro/unit/test-autopilot-phase-coverage.py" layer="test">
</f>
<f p="speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md">
</f>
<f p="speckit-pro/skills/speckit-autopilot/references/post-implementation.md">
</f>
<f p="speckit-pro/skills/speckit-autopilot/references/gate-validation.md">
</f>
<f p="speckit-pro/skills/speckit-autopilot/references/capability-discovery.md">
</f>
<f p="speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md">
</f>
<f p="speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md">
</f>
<f p="speckit-pro/skills/speckit-autopilot/references/phase-execution.md">
</f>
<f p="speckit-pro/skills/speckit-autopilot/references/execution-efficiency.md">
</f>
<f p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py" layer="test">
</f>
<f p="speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py">
</f>
```

## arch (0 lines)

```xml

```

## deps (0 lines)

```xml

```
