# Evidence for lane `pr-emission-and-stack-1` (79 files)
Lines from the whole-repo scans that mention this lane's files. Empty section = none found, not none exists.

## doc-drift (22 lines)

```xml
<doc p="docs/ai/specs/.process/ART-001-workflow.md" anchors="63" checked="23" drift="3" dated="0">
<a k="file-line" l="1422" c="29" why="line-moved" ref="speckit_pro_runner/helpers/pr_emission.py:427" sym="required_headings" got="plan_commands" tgt="speckit-pro/speckit_pro_runner/helpers/pr_emission.py:697"/>
</doc>
<doc p="tests/speckit-pro/evals/audit/integration-parity-audit.md" anchors="24" checked="7" drift="3" dated="0">
<a k="file-line" l="134" c="338" why="range-straddles" ref="helpers/stack_manager.py:110-189" sym="dry_run" got="qualify_topology" tgt="speckit-pro/speckit_pro_runner/helpers/stack_manager.py:189"/>
</doc>
<doc p="tests/speckit-pro/layer6-integration/performance-fixtures/draft-pr-emission/source/contracts/draft-packet-mode.md" anchors="53" checked="37" drift="1" dated="0">
</doc>
<doc p="tests/speckit-pro/layer6-integration/performance-fixtures/draft-pr-emission/source/plan.md" anchors="5" checked="3" drift="0" dated="1">
</doc>
<doc p="tests/speckit-pro/layer6-integration/performance-fixtures/draft-pr-emission/source/research.md" anchors="84" checked="44" drift="0" dated="17">
<a k="file-line" l="25" c="4" why="range-straddles" kind="dated-record" rec="stamp" ref="speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json:33-36" got="target" tgt="speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json:36"/>
<a k="file-line" l="85" c="30" why="line-moved" kind="dated-record" rec="stamp" ref="pr-packet.schema.json:66-72" sym="verification_evidence" got="scope_evidence" tgt="speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json:57"/>
<a k="file-line" l="180" c="30" why="line-moved" kind="dated-record" rec="stamp" ref="pr_emission.py:586-626" sym="normalize_scope_evidence" got="normalize_packet_input" tgt="speckit-pro/speckit_pro_runner/helpers/pr_emission.py:857"/>
<a k="file-line" l="182" c="45" why="line-moved" kind="dated-record" rec="stamp" ref="pr_emission.py:628-651" sym="normalize_evidence_list" got="normalize_packet_input" tgt="speckit-pro/speckit_pro_runner/helpers/pr_emission.py:902"/>
</doc>
<weak-file-line p="tests/speckit-pro/layer6-integration/performance-fixtures/draft-pr-emission/source/contracts/draft-packet-mode.md" n="1">
</weak-file-line>
<weak-file-line p="tests/speckit-pro/layer6-integration/performance-fixtures/draft-pr-emission/source/research.md" n="14">
<w l="27" c="4" ref="speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json:442-445" resolves-to="protected_body_fingerprint"/>
<w l="105" c="3" ref="speckit-pro/speckit_pro_runner/helpers/pr_emission.py:325-330" resolves-to="generate_pr_body"/>
</weak-file-line>
```

## clones (60 lines)

```xml
<group type="3" gid="60" tokens="185" n="2" similarity="0.81">
<f n="probe" p="speckit-pro/speckit_pro_runner/helpers/archive_sweep.py:31"/>
<f n="probe" p="speckit-pro/speckit_pro_runner/helpers/stack_manager.py:27"/>
</group>
<group type="3" gid="61" tokens="45" n="2" similarity="0.85">
<f n="_text" p="speckit-pro/speckit_pro_runner/helpers/egress_authorization.py:42"/>
<f n="_text_argument" p="speckit-pro/speckit_pro_runner/research_broker.py:961"/>
</group>
<group type="3" gid="62" tokens="155" n="2" similarity="0.92">
<f n="run_gate_preflight_coverage_helper" p="speckit-pro/speckit_pro_runner/helpers/gate_preflight_coverage.py:128"/>
<f n="run_run_finalization_helper" p="speckit-pro/speckit_pro_runner/helpers/run_finalization.py:279"/>
</group>
<group type="3" gid="67" tokens="48" n="2" similarity="0.88">
<f n="runner_identity_mismatch" p="speckit-pro/speckit_pro_runner/helpers/install.py:5515"/>
<f n="invalid_packet_input" p="speckit-pro/speckit_pro_runner/helpers/pr_emission.py:1123"/>
</group>
<group type="3" gid="73" tokens="40" n="2" similarity="0.80">
<f n="source_fingerprint" p="speckit-pro/speckit_pro_runner/helpers/pr_emission.py:316"/>
<f n="skill_witness" p="tests/speckit-pro/unit/test-native-eval-codex-rollouts.py:459"/>
</group>
<group type="3" gid="74" tokens="67" n="2" similarity="0.82">
<f n="validation_result_placeholder" p="speckit-pro/speckit_pro_runner/helpers/pr_emission.py:777"/>
<f n="check" p="tests/speckit-pro/unit/test-native-eval-runner-result.py:45"/>
</group>
<group type="3" gid="20" tokens="54" n="2" similarity="0.85">
<f n="load_module" p="tests/speckit-pro/layer1-structural/test-structural-regressions.py:23"/>
<f n="_load" p="tests/speckit-pro/unit/test-autopilot-bookkeeping-guard.py:76"/>
</group>
<group type="3" gid="20" tokens="54" n="2" similarity="0.83">
<f n="load_module" p="tests/speckit-pro/layer1-structural/test-structural-regressions.py:23"/>
<f n="load_coverage_validator" p="tests/speckit-pro/unit/test-autopilot-stage-resolution.py:1061"/>
</group>
<group type="3" gid="20" tokens="54" n="2" similarity="0.95">
<f n="load_module" p="tests/speckit-pro/layer1-structural/test-structural-regressions.py:23"/>
<f n="load_helper" p="tests/speckit-pro/unit/test-hosted-windows-preflight.py:27"/>
</group>
<group type="3" gid="91" tokens="67" n="2" similarity="0.88">
<f n="test_agent_instruction_validator_rejects_claude_drift" p="tests/speckit-pro/layer1-structural/test-structural-regressions.py:85"/>
<f n="test_agent_instruction_validator_rejects_unexpected_agent_scope" p="tests/speckit-pro/layer1-structural/test-structural-regressions.py:93"/>
</group>
<group type="3" gid="91" tokens="68" n="2" similarity="0.80">
<f n="test_agent_instruction_validator_rejects_claude_drift" p="tests/speckit-pro/layer1-structural/test-structural-regressions.py:85"/>
<f n="test_tree_snapshot_detects_any_workspace_change" p="tests/speckit-pro/unit/test-functional-headless-runner.py:1246"/>
</group>
<group type="3" gid="91" tokens="66" n="2" similarity="0.82">
<f n="test_agent_instruction_validator_rejects_claude_drift" p="tests/speckit-pro/layer1-structural/test-structural-regressions.py:85"/>
<f n="test_snapshot_tree_excludes_local_worktrees" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:1255"/>
</group>
<group type="3" gid="91" tokens="67" n="2" similarity="0.90">
<f n="test_agent_instruction_validator_rejects_unexpected_agent_scope" p="tests/speckit-pro/layer1-structural/test-structural-regressions.py:93"/>
<f n="test_snapshot_tree_excludes_local_worktrees" p="tests/speckit-pro/unit/test-release-pr-reconciliation.py:1255"/>
</group>
<group type="3" gid="91" tokens="88" n="2" similarity="0.80">
<f n="test_agent_instruction_validator_rejects_unexpected_agent_scope" p="tests/speckit-pro/layer1-structural/test-structural-regressions.py:93"/>
<f n="test_copied_spec_text_is_blocked" p="tests/speckit-pro/unit/test-research-broker.py:264"/>
</group>
<group type="3" gid="92" tokens="56" n="2" similarity="0.84">
<f n="main" p="tests/speckit-pro/layer1-structural/test-structural-regressions.py:206"/>
<f n="main" p="tests/speckit-pro/lib/test_lib.py:226"/>
</group>
```

## churn-decay (0 lines)

```xml

```

## arch (0 lines)

```xml

```

## deps (8 lines)

```xml
<cycle size="20" cost="400" cut="speckit-pro/speckit_pro_runner/author_broker.py -&gt; speckit-pro/speckit_pro_runner/helpers/mutation.py" cutrefs="1">
<f p="speckit-pro/speckit_pro_runner/helpers/run_finalization.py"/>
<f p="speckit-pro/speckit_pro_runner/helpers/pr_emission.py"/>
</cycle>
<f p="speckit-pro/speckit_pro_runner/helpers/pr_emission.py" includes="9" afferent="2" instab="0.67" transitive="58">
</f>
<f p="speckit-pro/speckit_pro_runner/helpers/run_finalization.py" includes="8" afferent="1" instab="0.80" transitive="58">
</f>
```
