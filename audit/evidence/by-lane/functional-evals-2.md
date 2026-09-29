# Evidence for lane `functional-evals-2` (89 files)
Lines from the whole-repo scans that mention this lane's files. Empty section = none found, not none exists.

## doc-drift (4 lines)

```xml
<weak-file-line p="docs/ai/research/tool-agnostic-capability-discovery-spike.md" n="9">
<w l="76" c="32" ref="tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json:107-116" resolves-to="evals"/>
<w l="139" c="130" ref="tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json:107-116" resolves-to="evals"/>
</weak-file-line>
```

## clones (45 lines)

```xml
<group type="2" gid="20" tokens="59" n="3">
<f n="load_composer" p="tests/speckit-pro/unit/test-compose-release-notes.py:54"/>
<f n="load_helper" p="tests/speckit-pro/unit/test-docs-artifact.py:24"/>
<f n="import_runner" p="tests/speckit-pro/unit/test-functional-headless-runner.py:33"/>
</group>
<group type="3" gid="91" tokens="68" n="2" similarity="0.80">
<f n="test_agent_instruction_validator_rejects_claude_drift" p="tests/speckit-pro/layer1-structural/test-structural-regressions.py:85"/>
<f n="test_tree_snapshot_detects_any_workspace_change" p="tests/speckit-pro/unit/test-functional-headless-runner.py:1246"/>
</group>
<group type="3" gid="104" tokens="60" n="2" similarity="0.88">
<f n="trigger_names_for_available_message" p="tests/speckit-pro/layer2-trigger/run-trigger-evals-codex.py:20"/>
<f n="available_evals" p="tests/speckit-pro/layer3-functional/run-functional-evals-codex.py:32"/>
</group>
<group type="3" gid="109" tokens="93" n="2" similarity="0.84">
<f n="fixture_permission_args" p="tests/speckit-pro/layer2-trigger/run_codex_evals.py:560"/>
<f n="codex_permission_args" p="tests/speckit-pro/layer3-functional/run-headless-evals.py:372"/>
</group>
<group type="3" gid="110" tokens="272" n="2" similarity="0.95">
<f n="enumerate_mcp_servers" p="tests/speckit-pro/layer2-trigger/run_codex_evals.py:574"/>
<f n="enumerate_codex_mcp_servers" p="tests/speckit-pro/layer3-functional/run-headless-evals.py:383"/>
</group>
<group type="3" gid="111" tokens="125" n="2" similarity="0.85">
<f n="skill_isolation_args" p="tests/speckit-pro/layer2-trigger/run_codex_evals.py:603"/>
<f n="skill_isolation_args" p="tests/speckit-pro/layer3-functional/run-headless-evals.py:349"/>
</group>
<group type="3" gid="112" tokens="197" n="2" similarity="0.85">
<f n="main" p="tests/speckit-pro/layer3-functional/run-functional-evals-codex.py:39"/>
<f n="main" p="tests/speckit-pro/layer3-functional/run-functional-evals.py:35"/>
</group>
<group type="3" gid="113" tokens="131" n="2" similarity="0.82">
<f n="parse_jsonl" p="tests/speckit-pro/layer3-functional/run-headless-evals.py:848"/>
<f n="_events" p="tests/speckit-pro/lib/native_eval_capture.py:297"/>
</group>
<group type="3" gid="246" tokens="57" n="2" similarity="0.85">
<f n="test_actor_environment_refuses_unexecutable_interpreter" p="tests/speckit-pro/unit/test-functional-headless-runner.py:77"/>
<f n="test_unexecutable_actor_is_rejected_before_creating_aliases" p="tests/speckit-pro/unit/test-trigger-signal-restoration.py:80"/>
</group>
<group type="3" gid="247" tokens="221" n="2" similarity="0.81">
<f n="test_claude_stage_change_stops_before_provider_launch" p="tests/speckit-pro/unit/test-functional-headless-runner.py:790"/>
<f n="test_cli_catalog_skill_still_requires_exact_host_and_eval_id" p="tests/speckit-pro/unit/test-functional-headless-runner.py:862"/>
</group>
<group type="3" gid="247" tokens="221" n="2" similarity="0.80">
<f n="test_cli_unknown_skill_rejects_before_readiness" p="tests/speckit-pro/unit/test-functional-headless-runner.py:842"/>
<f n="test_cli_catalog_skill_still_requires_exact_host_and_eval_id" p="tests/speckit-pro/unit/test-functional-headless-runner.py:862"/>
</group>
```

## churn-decay (4 lines)

```xml
<f p="tests/speckit-pro/unit/test-functional-headless-runner.py" layer="test">
</f>
<f p="tests/speckit-pro/layer3-functional/run-headless-evals.py" layer="test">
</f>
```

## arch (0 lines)

```xml

```

## deps (0 lines)

```xml

```
