# Evidence for lane `structural-layers-2` (54 files)
Lines from the whole-repo scans that mention this lane's files. Empty section = none found, not none exists.

## doc-drift (8 lines)

```xml
<doc p="docs/ai/specs/.process/ART-008-workflow.md" anchors="81" checked="34" drift="7" dated="0">
<a k="file-line" l="1106" c="4" why="range-straddles" ref="validate-tool-scoping.py:29-48" got="READ_ONLY_ROLES" tgt="tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py:48"/>
</doc>
<doc p="tests/speckit-pro/layer1-structural/fixtures/spec-index/roadmap-moc/specs/legacy-thing/SPEC-MOC.md" anchors="2" checked="2" drift="1" dated="0">
</doc>
<weak-file-line p="docs/ai/specs/.process/ART-014-retrospective.md" n="1">
<w l="54" c="2" ref="tests/speckit-pro/suite-manifest.json:130" resolves-to="layers"/>
</weak-file-line>
```

## clones (177 lines)

```xml
<group type="2" gid="99" tokens="131" n="2">
<f n="_check_runtime" p="tests/speckit-pro/layer1-structural/validate-skill-contracts.py:578"/>
<f n="_collect_runtime" p="tests/speckit-pro/layer1-structural/validate-skill-contracts.py:623"/>
</group>
<group type="2" gid="58" tokens="54" n="2">
<f n="emit_checks" p="speckit-pro/speckit_pro_runner/gates/suite.py:495"/>
<f n="emit_checks" p="tests/speckit-pro/run-layer-scripts.py:99"/>
</group>
<group type="2" gid="255" tokens="53" n="3">
<f n="force_stale_mode_b_internal_error" p="tests/speckit-pro/unit/test-moc-lint-exit-codes.py:150"/>
<f n="force_orphan_scan_root_internal_error" p="tests/speckit-pro/unit/test-moc-lint-exit-codes.py:180"/>
<f n="force_stale_scan_root_internal_error" p="tests/speckit-pro/unit/test-moc-lint-exit-codes.py:211"/>
</group>
<group type="3" gid="92" tokens="56" n="2" similarity="0.84">
<f n="main" p="tests/speckit-pro/layer1-structural/test-structural-regressions.py:206"/>
<f n="main" p="tests/speckit-pro/lib/test_lib.py:226"/>
</group>
<group type="3" gid="93" tokens="74" n="2" similarity="0.97">
<f n="_field" p="tests/speckit-pro/layer1-structural/validate-agent-contracts.py:132"/>
<f n="_field" p="tests/speckit-pro/layer1-structural/validate-skill-contracts.py:32"/>
</group>
<group type="3" gid="99" tokens="131" n="2" similarity="0.82">
<f n="_check_runtime" p="tests/speckit-pro/layer1-structural/validate-skill-contracts.py:578"/>
<f n="_check_runtime" p="tests/speckit-pro/layer1-structural/validate-skill-contracts.py:787"/>
</group>
<group type="3" gid="100" tokens="299" n="2" similarity="0.91">
<f n="test_target_resolution" p="tests/speckit-pro/layer1-structural/validate-skill-contracts.py:663"/>
<f n="test_skill_pointer_coverage_and_resolution" p="tests/speckit-pro/layer1-structural/validate-skill-contracts.py:812"/>
</group>
<group type="3" gid="101" tokens="79" n="2" similarity="0.81">
<f n="validate_moc_orphan_moc_frontmatter_field" p="tests/speckit-pro/layer1-structural/validate-spec-lifecycle-contracts.py:254"/>
<f n="_raw_frontmatter_field" p="tests/speckit-pro/layer1-structural/validate-spec-lifecycle-contracts.py:261"/>
</group>
<group type="3" gid="102" tokens="93" n="2" similarity="0.85">
<f n="_frontmatter_block" p="tests/speckit-pro/layer1-structural/validate-spec-lifecycle-contracts.py:416"/>
<f n="stale_body" p="tests/speckit-pro/layer1-structural/validate-spec-lifecycle-contracts.py:458"/>
</group>
<group type="3" gid="103" tokens="85" n="2" similarity="0.82">
<f n="run_moc_orphan" p="tests/speckit-pro/layer1-structural/validate-spec-lifecycle-contracts.py:766"/>
<f n="run_moc_stale" p="tests/speckit-pro/layer1-structural/validate-spec-lifecycle-contracts.py:776"/>
</group>
<group type="3" gid="114" tokens="48" n="2" similarity="0.89">
<f n="test_open_executors_orchestration_capabilities_never_denied" p="tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py:264"/>
<f n="test_skill_driven_executors_keep_skill_and_mutation_surface" p="tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py:306"/>
</group>
<group type="3" gid="115" tokens="87" n="2" similarity="0.82">
<f n="test_read_only_roles_deny_builtin_mutation_primitives" p="tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py:271"/>
<f n="test_brokered_research_roles_deny_raw_research_tools" p="tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py:525"/>
</group>
<group type="3" gid="116" tokens="199" n="2" similarity="0.92">
<f n="test_path_scoped_untrusted_input_authors_pin_exact_tool_allowlists" p="tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py:457"/>
<f n="test_no_tool_observers_pin_exact_tool_allowlists" p="tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py:482"/>
</group>
<group type="3" gid="161" tokens="63" n="2" similarity="0.87">
<f n="frontmatter" p="tests/speckit-pro/lib/structural_helpers.py:79"/>
<f n="body" p="tests/speckit-pro/lib/structural_helpers.py:95"/>
</group>
<group type="3" gid="162" tokens="112" n="2" similarity="0.83">
<f n="test_all_pass_suite_reports_zero_exit" p="tests/speckit-pro/lib/test_lib.py:83"/>
<f n="test_skipped_suite_unit_is_not_reported_as_passed" p="tests/speckit-pro/lib/test_lib.py:109"/>
</group>
<group type="3" gid="20" tokens="51" n="2" similarity="0.86">
<f n="_load_run_all" p="tests/speckit-pro/test-run-all.py:34"/>
<f n="_load" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:76"/>
</group>
<group type="3" gid="20" tokens="51" n="2" similarity="0.94">
<f n="_load_run_all" p="tests/speckit-pro/test-run-all.py:34"/>
<f n="load_coverage_validator" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1061"/>
</group>
<group type="3" gid="20" tokens="51" n="2" similarity="0.84">
<f n="_load_run_all" p="tests/speckit-pro/test-run-all.py:34"/>
<f n="import_checker" p="tests/speckit-pro/unit/test-check-toolchain.py:109"/>
</group>
<group type="3" gid="20" tokens="51" n="2" similarity="0.82">
<f n="_load_run_all" p="tests/speckit-pro/test-run-all.py:34"/>
<f n="load_helper" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:27"/>
</group>
<group type="3" gid="20" tokens="51" n="2" similarity="0.89">
<f n="_load_run_all" p="tests/speckit-pro/test-run-all.py:34"/>
<f n="load_layer_script_dispatcher" p="tests/speckit-pro/unit/test-speckit-pro-gates.py:206"/>
</group>
<group type="3" gid="167" tokens="44" n="2" similarity="0.96">
<f n="test_default_config_runs_deterministic_layers" p="tests/speckit-pro/test-run-all.py:49"/>
<f n="test_full_mode_for_rendered_docs" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:213"/>
</group>
<group type="3" gid="167" tokens="55" n="2" similarity="0.82">
<f n="test_layer_and_live_and_verbose_flags" p="tests/speckit-pro/test-run-all.py:65"/>
<f n="test_path_boundaries_do_not_match_prefix_lookalikes" p="tests/speckit-pro/unit/test-pr-checks-helpers.py:269"/>
</group>
<group type="3" gid="168" tokens="149" n="2" similarity="0.89">
<f n="test_passing_child_prints_no_failure_detail" p="tests/speckit-pro/test-run-all.py:236"/>
<f n="test_integration_layer_uses_its_aggregate_summary_once" p="tests/speckit-pro/test-run-all.py:260"/>
</group>
<group type="3" gid="169" tokens="155" n="2" similarity="0.98">
<f n="test_selected_layer_with_no_scripts_fails_closed" p="tests/speckit-pro/test-run-all.py:288"/>
<f n="test_unknown_layer_selects_no_execution_and_fails_closed" p="tests/speckit-pro/test-run-all.py:314"/>
</group>
<group type="3" gid="169" tokens="167" n="2" similarity="0.95">
<f n="test_selected_layer_with_no_scripts_fails_closed" p="tests/speckit-pro/test-run-all.py:288"/>
<f n="test_selected_layer_with_missing_script_fails_closed" p="tests/speckit-pro/test-run-all.py:340"/>
</group>
<group type="3" gid="169" tokens="203" n="2" similarity="0.84">
<f n="test_selected_layer_with_no_scripts_fails_closed" p="tests/speckit-pro/test-run-all.py:288"/>
<f n="test_non_python_manifest_entry_is_counted_failure_not_crash" p="tests/speckit-pro/test-run-all.py:367"/>
</group>
<group type="3" gid="169" tokens="167" n="2" similarity="0.96">
<f n="test_unknown_layer_selects_no_execution_and_fails_closed" p="tests/speckit-pro/test-run-all.py:314"/>
<f n="test_selected_layer_with_missing_script_fails_closed" p="tests/speckit-pro/test-run-all.py:340"/>
</group>
<group type="3" gid="169" tokens="203" n="2" similarity="0.85">
<f n="test_unknown_layer_selects_no_execution_and_fails_closed" p="tests/speckit-pro/test-run-all.py:314"/>
<f n="test_non_python_manifest_entry_is_counted_failure_not_crash" p="tests/speckit-pro/test-run-all.py:367"/>
</group>
<group type="3" gid="169" tokens="203" n="2" similarity="0.89">
<f n="test_selected_layer_with_missing_script_fails_closed" p="tests/speckit-pro/test-run-all.py:340"/>
<f n="test_non_python_manifest_entry_is_counted_failure_not_crash" p="tests/speckit-pro/test-run-all.py:367"/>
</group>
<group type="3" gid="170" tokens="48" n="2" similarity="0.87">
<f n="main" p="tests/speckit-pro/test-run-all.py:399"/>
<f n="build_suite" p="tests/speckit-pro/unit/test-phase7-task-partition.py:602"/>
</group>
<group type="3" gid="233" tokens="49" n="2" similarity="0.96">
<f n="write" p="tests/speckit-pro/unit/test-feedback-sweep-isolation.py:79"/>
<f n="write_file" p="tests/speckit-pro/unit/test-repo-bash-confinement.py:53"/>
</group>
<group type="3" gid="249" tokens="262" n="2" similarity="0.81">
<f n="test_write_rejects_target_swap_between_conflict_check_and_replace" p="tests/speckit-pro/unit/test-generate-spec-index.py:392"/>
<f n="test_write_rejects_render_dependency_change_between_render_and_commit" p="tests/speckit-pro/unit/test-generate-spec-index.py:463"/>
</group>
<group type="3" gid="249" tokens="237" n="2" similarity="0.84">
<f n="test_write_rejects_target_swap_between_conflict_check_and_replace" p="tests/speckit-pro/unit/test-generate-spec-index.py:392"/>
<f n="test_write_rechecks_applied_map_before_success" p="tests/speckit-pro/unit/test-generate-spec-index.py:540"/>
</group>
<group type="3" gid="249" tokens="266" n="2" similarity="0.82">
<f n="test_write_rejects_target_swap_between_conflict_check_and_replace" p="tests/speckit-pro/unit/test-generate-spec-index.py:392"/>
<f n="test_apply_rejects_target_swap_between_snapshot_and_replace" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:8535"/>
</group>
<group type="3" gid="249" tokens="303" n="2" similarity="0.90">
<f n="test_write_rejects_render_dependency_change_between_render_and_commit" p="tests/speckit-pro/unit/test-generate-spec-index.py:463"/>
<f n="test_write_rolls_back_render_dependency_change_immediately_before_replace" p="tests/speckit-pro/unit/test-generate-spec-index.py:501"/>
</group>
<group type="3" gid="250" tokens="70" n="2" similarity="0.90">
<f n="mutate_prs_after_initial_render" p="tests/speckit-pro/unit/test-generate-spec-index.py:471"/>
<f n="mutate_prs_before_replace" p="tests/speckit-pro/unit/test-generate-spec-index.py:509"/>
</group>
<group type="3" gid="249" tokens="303" n="2" similarity="0.84">
<f n="test_write_rolls_back_render_dependency_change_immediately_before_replace" p="tests/speckit-pro/unit/test-generate-spec-index.py:501"/>
<f n="test_write_rechecks_applied_map_before_success" p="tests/speckit-pro/unit/test-generate-spec-index.py:540"/>
</group>
<group type="3" gid="252" tokens="50" n="2" similarity="0.90">
<f n="test_property_names_apply_to_every_key" p="tests/speckit-pro/unit/test-json-schema-validator.py:63"/>
<f n="test_max_properties_bounds_the_object" p="tests/speckit-pro/unit/test-json-schema-validator.py:100"/>
</group>
<group type="3" gid="253" tokens="76" n="2" similarity="0.87">
<f n="test_pattern_properties_validate_and_are_not_additional" p="tests/speckit-pro/unit/test-json-schema-validator.py:68"/>
<f n="test_dependent_required_needs_the_named_keys" p="tests/speckit-pro/unit/test-json-schema-validator.py:83"/>
</group>
<group type="3" gid="255" tokens="73" n="2" similarity="0.84">
<f n="force_stale_mode_b_internal_error" p="tests/speckit-pro/unit/test-moc-lint-exit-codes.py:150"/>
<f n="force_unreadable_marker" p="tests/speckit-pro/unit/test-moc-lint-exit-codes.py:242"/>
</group>
<group type="3" gid="312" tokens="58" n="2" similarity="0.83">
<f n="scan_for" p="tests/speckit-pro/unit/test-privacy-scan.py:132"/>
<f n="scan_for_non_allowlisted_email" p="tests/speckit-pro/unit/test-privacy-scan.py:141"/>
</group>
<group type="3" gid="326" tokens="59" n="2" similarity="0.84">
<f n="test_python_scans_class_bodies_and_methods_with_separate_bindings" p="tests/speckit-pro/unit/test-repo-bash-confinement.py:341"/>
<f n="test_nested_shell_payloads_are_inspected" p="tests/speckit-pro/unit/test-repo-bash-confinement.py:651"/>
</group>
<group type="3" gid="326" tokens="51" n="2" similarity="0.88">
<f n="test_python_scans_class_bodies_and_methods_with_separate_bindings" p="tests/speckit-pro/unit/test-repo-bash-confinement.py:341"/>
<f n="test_runtime_diagnostics_resolve_format_percent_and_incremental_strings" p="tests/speckit-pro/unit/test-repo-bash-confinement.py:973"/>
</group>
<group type="3" gid="327" tokens="132" n="2" similarity="0.85">
<f n="test_active_instruction_surfaces_block_retired_shell_guidance" p="tests/speckit-pro/unit/test-repo-bash-confinement.py:813"/>
<f n="test_runtime_diagnostic_fields_block_obsolete_shell_remediation" p="tests/speckit-pro/unit/test-repo-bash-confinement.py:914"/>
</group>
```

## churn-decay (15 lines)

```xml
<recent n="40" of="1331" merge_bombs_skipped="5">
<rc p="tests/speckit-pro/suite-manifest.json" age_d="0" w="63.3"/>
<rc p="tests/speckit-pro/layer1-structural/validate-skill-contracts.py" age_d="0" w="30.5"/>
</recent>
<f p="tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py" layer="test">
</f>
<f p="tests/speckit-pro/layer1-structural/validate-skill-contracts.py" layer="test">
</f>
<f p="docs-site/src/content/docs/reference/tests.md">
<s t="sec" n="tests/speckit-pro/test-run-all.py" sc="Records" k="0.0003">
<s t="sec" n="tests/speckit-pro/run-layer-scripts.py" sc="Records" k="0.0003">
<s t="sec" n="tests/speckit-pro/run-all.py" sc="Records" k="0.0003">
</f>
<f p="tests/speckit-pro/lib/test_result.py" layer="test">
</f>
```

## arch (0 lines)

```xml

```

## deps (0 lines)

```xml

```
