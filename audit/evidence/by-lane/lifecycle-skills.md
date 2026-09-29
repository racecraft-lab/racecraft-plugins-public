# Evidence for lane `lifecycle-skills` (79 files)
Lines from the whole-repo scans that mention this lane's files. Empty section = none found, not none exists.

## doc-drift (15 lines)

```xml
<doc p="tests/speckit-pro/evals/audit/integration-parity-audit.md" anchors="24" checked="7" drift="3" dated="0">
<a k="file-line" l="133" c="449" why="range-straddles" ref="speckit-status/SKILL.md:194-209" got="Specific Spec Procedure" tgt="speckit-pro/codex-skills/speckit-status/SKILL.md:209"/>
</doc>
<doc p="docs/ai/specs/.process/ART-011-design-concept.md" anchors="12" checked="4" drift="2" dated="0">
<a k="file-line" l="123" c="4" why="past-eof" ref="speckit-pro/codex-skills/grill-me/SKILL.md:129" got="86 lines" tgt="speckit-pro/codex-skills/grill-me/SKILL.md"/>
<a k="file-line" l="306" c="5" why="past-eof" ref="speckit-pro/codex-skills/grill-me/SKILL.md:283-286" got="86 lines" tgt="speckit-pro/codex-skills/grill-me/SKILL.md"/>
</doc>
<doc p="docs/prd-racecraft-identity-system.md" anchors="10" checked="3" drift="1" dated="0">
</doc>
<doc p="speckit-pro/codex-skills/speckit-status/SKILL.md" anchors="12" checked="4" drift="1" dated="0">
</doc>
<doc p="tests/speckit-pro/layer6-integration/performance-fixtures/draft-pr-emission/source/research.md" anchors="84" checked="44" drift="0" dated="17">
<a k="file-line" l="360" c="17" why="range-straddles" kind="dated-record" rec="stamp" ref="speckit-pro/speckit_pro_runner/helpers/install.py:31-44" got="CODEX_LUNA_FALLBACK_MODEL" tgt="speckit-pro/speckit_pro_runner/helpers/install.py:44"/>
<a k="file-line" l="362" c="29" why="range-straddles" kind="dated-record" rec="stamp" ref="install.py:284-307" sym="load_codex_agent_bundle" got="(file scope)" tgt="speckit-pro/speckit_pro_runner/helpers/install.py:307"/>
</doc>
```

## clones (88 lines)

```xml
<group type="2" gid="72" tokens="47" n="2">
<f n="malformed_inventory" p="speckit-pro/speckit_pro_runner/helpers/install.py:5676"/>
<f n="invalid_operation" p="speckit-pro/speckit_pro_runner/helpers/mutation.py:1234"/>
</group>
<group type="3" gid="6" tokens="72" n="2" similarity="0.82">
<f n="readText" p="docs-site/scripts/validate-safe-install-aids.mjs:36"/>
<f n="readJson" p="docs-site/scripts/validate-safe-install-aids.mjs:45"/>
</group>
<group type="3" gid="18" tokens="85" n="2" similarity="0.85">
<f n="_label_names" p="scripts/release_note_policy.py:473"/>
<f n="codex_route_aware_remediation_action_summaries" p="speckit-pro/speckit_pro_runner/helpers/install.py:3720"/>
</group>
<group type="3" gid="55" tokens="252" n="2" similarity="0.93">
<f n="load_case" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:5383"/>
<f n="runner_invocation_case" p="speckit-pro/speckit_pro_runner/helpers/install.py:5010"/>
</group>
<group type="3" gid="56" tokens="98" n="2" similarity="0.83">
<f n="active_runtime_base_data" p="speckit-pro/speckit_pro_runner/gates/active_path_guard.py:5421"/>
<f n="runner_invocation_base_data" p="speckit-pro/speckit_pro_runner/helpers/install.py:5563"/>
</group>
<group type="3" gid="56" tokens="98" n="2" similarity="0.86">
<f n="gate_base_data" p="speckit-pro/speckit_pro_runner/gates/gate_response.py:8"/>
<f n="runner_invocation_base_data" p="speckit-pro/speckit_pro_runner/helpers/install.py:5563"/>
</group>
<group type="3" gid="63" tokens="60" n="2" similarity="0.83">
<f n="codex_agent_windows_file_info" p="speckit-pro/speckit_pro_runner/helpers/install.py:367"/>
<f n="codex_agent_windows_seek_start" p="speckit-pro/speckit_pro_runner/helpers/install.py:389"/>
</group>
<group type="3" gid="63" tokens="76" n="2" similarity="0.81">
<f n="codex_agent_windows_file_info" p="speckit-pro/speckit_pro_runner/helpers/install.py:367"/>
<f n="codex_agent_windows_delete_by_handle" p="speckit-pro/speckit_pro_runner/helpers/install.py:468"/>
</group>
<group type="3" gid="63" tokens="78" n="2" similarity="0.83">
<f n="codex_agent_windows_seek_start" p="speckit-pro/speckit_pro_runner/helpers/install.py:389"/>
<f n="codex_agent_windows_set_mode_by_handle" p="speckit-pro/speckit_pro_runner/helpers/install.py:454"/>
</group>
<group type="3" gid="63" tokens="76" n="2" similarity="0.84">
<f n="codex_agent_windows_seek_start" p="speckit-pro/speckit_pro_runner/helpers/install.py:389"/>
<f n="codex_agent_windows_delete_by_handle" p="speckit-pro/speckit_pro_runner/helpers/install.py:468"/>
</group>
<group type="3" gid="63" tokens="78" n="2" similarity="0.96">
<f n="codex_agent_windows_set_mode_by_handle" p="speckit-pro/speckit_pro_runner/helpers/install.py:454"/>
<f n="codex_agent_windows_delete_by_handle" p="speckit-pro/speckit_pro_runner/helpers/install.py:468"/>
</group>
<group type="3" gid="64" tokens="227" n="2" similarity="0.98">
<f n="previous_state" p="speckit-pro/speckit_pro_runner/helpers/install.py:627"/>
<f n="codex_agent_previous_state_at" p="speckit-pro/speckit_pro_runner/helpers/install.py:4877"/>
</group>
<group type="3" gid="65" tokens="100" n="2" similarity="0.89">
<f n="public_entry_classification" p="speckit-pro/speckit_pro_runner/helpers/install.py:958"/>
<f n="private_entry_classification" p="speckit-pro/speckit_pro_runner/helpers/install.py:970"/>
</group>
<group type="3" gid="66" tokens="489" n="2" similarity="0.81">
<f n="preserve_state_as_backup" p="speckit-pro/speckit_pro_runner/helpers/install.py:1183"/>
<f n="preserve_state_as_backup" p="speckit-pro/speckit_pro_runner/helpers/install.py:1799"/>
</group>
<group type="3" gid="67" tokens="54" n="2" similarity="0.86">
<f n="invalid_route_policy_manifest_path" p="speckit-pro/speckit_pro_runner/helpers/install.py:2474"/>
<f n="runner_identity_mismatch" p="speckit-pro/speckit_pro_runner/helpers/install.py:5515"/>
</group>
<group type="3" gid="68" tokens="78" n="2" similarity="0.95">
<f n="codex_route_aware_required_miss_diagnostic" p="speckit-pro/speckit_pro_runner/helpers/install.py:3362"/>
<f n="codex_route_aware_helper_unresolved_diagnostic" p="speckit-pro/speckit_pro_runner/helpers/install.py:3379"/>
</group>
<group type="3" gid="69" tokens="57" n="2" similarity="0.80">
<f n="codex_agent_destination_identity" p="speckit-pro/speckit_pro_runner/helpers/install.py:4224"/>
<f n="current_file_mode_fd" p="speckit-pro/speckit_pro_runner/helpers/mutation.py:1742"/>
</group>
<group type="3" gid="67" tokens="48" n="2" similarity="0.88">
<f n="runner_identity_mismatch" p="speckit-pro/speckit_pro_runner/helpers/install.py:5515"/>
<f n="invalid_packet_input" p="speckit-pro/speckit_pro_runner/helpers/pr_emission.py:1123"/>
</group>
<group type="3" gid="70" tokens="62" n="2" similarity="0.96">
<f n="parse_version" p="speckit-pro/speckit_pro_runner/helpers/install.py:5546"/>
<f n="parse_version_tuple" p="speckit-pro/speckit_pro_runner/runtime.py:183"/>
</group>
<group type="3" gid="71" tokens="72" n="2" similarity="0.96">
<f n="fake_home_boundary_diagnostic" p="speckit-pro/speckit_pro_runner/helpers/install.py:5648"/>
<f n="repair_target_boundary_diagnostic" p="speckit-pro/speckit_pro_runner/helpers/install.py:5664"/>
</group>
<group type="3" gid="72" tokens="47" n="2" similarity="0.87">
<f n="malformed_inventory" p="speckit-pro/speckit_pro_runner/helpers/install.py:5676"/>
<f n="source_fingerprint_changed" p="speckit-pro/speckit_pro_runner/helpers/mutation.py:1990"/>
</group>
<group type="3" gid="171" tokens="56" n="2" similarity="0.81">
<f n="run_tool" p="tests/speckit-pro/unit/test-agent-memory-ignore.py:28"/>
<f n="run" p="tests/speckit-pro/unit/test-ubiquitous-language-lint.py:36"/>
</group>
```

## churn-decay (6 lines)

```xml
<recent n="40" of="1331" merge_bombs_skipped="5">
<rc p="speckit-pro/speckit_pro_runner/helpers/install.py" age_d="0" w="16"/>
<rc p="speckit-pro/codex-skills/speckit-upgrade/SKILL.md" age_d="0" w="12.4"/>
</recent>
<f p="speckit-pro/speckit_pro_runner/helpers/install.py">
</f>
```

## arch (0 lines)

```xml

```

## deps (2 lines)

```xml
<f p="speckit-pro/speckit_pro_runner/helpers/install.py" includes="22" afferent="2" instab="0.75" transitive="58">
</f>
```
