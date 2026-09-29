# Evidence for lane `coach-and-formal` (75 files)
Lines from the whole-repo scans that mention this lane's files. Empty section = none found, not none exists.

## doc-drift (10 lines)

```xml
<doc p="docs/ai/specs/.process/ART-003-workflow.md" anchors="45" checked="15" drift="7" dated="0">
<a k="file-line" l="1442" c="19" why="past-eof" ref="tasks.md:105" got="31 lines" tgt="specs/formal-001-selective-formal-methods/tasks.md"/>
</doc>
<doc p="docs/ai/specs/.process/G56R-006-workflow.md" anchors="12" checked="5" drift="4" dated="0">
<a k="file-line" l="554" c="71" why="past-eof" ref="tasks.md:228-254" got="31 lines" tgt="specs/formal-001-selective-formal-methods/tasks.md"/>
<a k="file-line" l="555" c="31" why="past-eof" ref="tasks.md:196-226" got="31 lines" tgt="specs/formal-001-selective-formal-methods/tasks.md"/>
</doc>
<doc p="docs/ai/specs/.process/PRSG-008-workflow.md" anchors="11" checked="3" drift="2" dated="0">
<a k="file-line" l="578" c="14" why="past-eof" ref="specs/prsg-008-layer-planner/tasks.md:234" got="31 lines" tgt="specs/formal-001-selective-formal-methods/tasks.md"/>
</doc>
```

## clones (48 lines)

```xml
<group type="3" gid="239" tokens="59" n="2" similarity="0.92">
<f n="save_catalog" p="tests/speckit-pro/unit/test-formal-checkers.py:56"/>
<f n="save_catalog" p="tests/speckit-pro/unit/test-formal-traces.py:56"/>
</group>
<group type="3" gid="240" tokens="54" n="2" similarity="0.93">
<f n="request" p="tests/speckit-pro/unit/test-formal-checkers.py:61"/>
<f n="request" p="tests/speckit-pro/unit/test-formal-traces.py:69"/>
</group>
<group type="3" gid="241" tokens="174" n="2" similarity="0.82">
<f n="test_catalog_cannot_approve_a_replacement_distribution" p="tests/speckit-pro/unit/test-formal-checkers.py:189"/>
<f n="test_tlc_catalog_cannot_approve_replacement_bytes" p="tests/speckit-pro/unit/test-formal-checkers.py:212"/>
</group>
<group type="3" gid="242" tokens="269" n="2" similarity="0.83">
<f n="test_planning_reconciliation_replaces_stale_and_interrupted_evidence" p="tests/speckit-pro/unit/test-formal-checkers.py:287"/>
<f n="test_final_and_post_bind_implementation_files_and_checkpoint_identity" p="tests/speckit-pro/unit/test-formal-checkers.py:316"/>
</group>
<group type="3" gid="243" tokens="169" n="2" similarity="0.84">
<f n="test_native_errors_and_deadlock" p="tests/speckit-pro/unit/test-formal-checkers.py:408"/>
<f n="test_native_tlc_pass_violation_errors_and_deadlock" p="tests/speckit-pro/unit/test-formal-checkers.py:468"/>
</group>
<group type="3" gid="244" tokens="164" n="2" similarity="0.85">
<f n="test_native_temporal_property_and_unsupported_fairness" p="tests/speckit-pro/unit/test-formal-checkers.py:437"/>
<f n="test_native_tlc_fairness_and_liveness_counterexample" p="tests/speckit-pro/unit/test-formal-checkers.py:484"/>
</group>
<group type="3" gid="245" tokens="82" n="2" similarity="0.84">
<f n="test_native_timeout_and_wrong_checksum_do_not_pass" p="tests/speckit-pro/unit/test-formal-checkers.py:450"/>
<f n="test_native_quint_syntax_and_installation_drift" p="tests/speckit-pro/unit/test-formal-checkers.py:563"/>
</group>
<group type="3" gid="313" tokens="82" n="2" similarity="0.86">
<f n="test_notice_records_the_exact_upstream_facts" p="tests/speckit-pro/unit/test-quint-reference-attribution.py:103"/>
<f n="test_readme_names_author_repository_commit_and_license" p="tests/speckit-pro/unit/test-quint-reference-attribution.py:113"/>
</group>
<group type="3" gid="178" tokens="75" n="2" similarity="0.81">
<f n="test_provenance_pins_the_expected_upstream" p="tests/speckit-pro/unit/test-quint-reference-attribution.py:122"/>
<f n="assert_response" p="tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:613"/>
</group>
<group type="3" gid="178" tokens="75" n="2" similarity="0.83">
<f n="test_provenance_pins_the_expected_upstream" p="tests/speckit-pro/unit/test-quint-reference-attribution.py:122"/>
<f n="test_preflight_ok_with_detected_prerequisites" p="tests/speckit-pro/unit/test-speckit-pro-runner.py:195"/>
</group>
<group type="3" gid="314" tokens="142" n="2" similarity="0.81">
<f n="test_verbatim_files_record_the_upstream_hash" p="tests/speckit-pro/unit/test-quint-reference-attribution.py:219"/>
<f n="test_adapted_files_record_the_upstream_hash_and_transform" p="tests/speckit-pro/unit/test-quint-reference-attribution.py:241"/>
</group>
<group type="3" gid="315" tokens="74" n="2" similarity="0.85">
<f n="test_quint_guide_disclosure_links_resolve" p="tests/speckit-pro/unit/test-quint-reference-attribution.py:427"/>
<f n="test_reference_readme_links_resolve" p="tests/speckit-pro/unit/test-quint-reference-attribution.py:435"/>
</group>
```

## churn-decay (11 lines)

```xml
<recent n="40" of="1331" merge_bombs_skipped="5">
<rc p="speckit-pro/skills/speckit-coach/templates/workflow-template.md" age_d="0" w="20.7"/>
</recent>
<f p="speckit-pro/speckit_pro_runner/formal/catalog.py">
</f>
<f p="speckit-pro/speckit_pro_runner/formal/selection.py">
</f>
<f p="tests/speckit-pro/unit/test-formal-checkers.py" layer="test">
</f>
<f p="speckit-pro/skills/speckit-autopilot/references/formal-methods.md">
</f>
```

## arch (0 lines)

```xml

```

## deps (39 lines)

```xml
<godfiles total="92" shown="12" capped="1">
<f p="speckit-pro/speckit_pro_runner/formal/selection.py" afferent="11"/>
<f p="speckit-pro/speckit_pro_runner/formal/catalog.py" afferent="8"/>
<f p="speckit-pro/speckit_pro_runner/formal/traces.py" afferent="5"/>
</godfiles>
<stabledeps violations="26">
<v from="speckit-pro/speckit_pro_runner/formal/catalog.py" to="speckit-pro/speckit_pro_runner/formal/traces.py" gap="0.31"/>
<v from="speckit-pro/speckit_pro_runner/formal/evidence.py" to="speckit-pro/speckit_pro_runner/formal/traces.py" gap="0.21"/>
</stabledeps>
<cycle size="6" cost="36" cut="speckit-pro/speckit_pro_runner/formal/catalog.py -&gt; speckit-pro/speckit_pro_runner/formal/native_config.py" cutrefs="1">
<f p="speckit-pro/speckit_pro_runner/formal/quint.py"/>
<f p="speckit-pro/speckit_pro_runner/formal/engine.py"/>
<f p="speckit-pro/speckit_pro_runner/formal/evidence.py"/>
<f p="speckit-pro/speckit_pro_runner/formal/native_config.py"/>
<f p="speckit-pro/speckit_pro_runner/formal/traces.py"/>
<f p="speckit-pro/speckit_pro_runner/formal/catalog.py"/>
</cycle>
<cycle size="2" cost="4" cut="speckit-pro/speckit_pro_runner/formal/helper.py -&gt; speckit-pro/speckit_pro_runner/formal/lifecycle.py" cutrefs="1">
<f p="speckit-pro/speckit_pro_runner/formal/lifecycle.py"/>
<f p="speckit-pro/speckit_pro_runner/formal/helper.py"/>
</cycle>
<f p="speckit-pro/speckit_pro_runner/formal/helper.py" includes="13" afferent="4" instab="0.69" transitive="13">
</f>
<f p="speckit-pro/speckit_pro_runner/formal/lifecycle.py" includes="7" afferent="1" instab="0.80" transitive="13">
</f>
<f p="speckit-pro/speckit_pro_runner/formal/itf.py" includes="4" afferent="0" instab="1.00" transitive="10">
</f>
<f p="speckit-pro/speckit_pro_runner/formal/catalog.py" includes="9" afferent="8" instab="0.33" transitive="9">
</f>
<f p="speckit-pro/speckit_pro_runner/formal/engine.py" includes="15" afferent="4" instab="0.60" transitive="9">
</f>
<f p="speckit-pro/speckit_pro_runner/formal/evidence.py" includes="10" afferent="4" instab="0.43" transitive="9">
</f>
<f p="speckit-pro/speckit_pro_runner/formal/native_config.py" includes="3" afferent="2" instab="0.33" transitive="9">
</f>
<f p="speckit-pro/speckit_pro_runner/formal/quint.py" includes="10" afferent="4" instab="0.43" transitive="9">
</f>
<f p="speckit-pro/speckit_pro_runner/formal/traces.py" includes="17" afferent="5" instab="0.64" transitive="9">
</f>
```
