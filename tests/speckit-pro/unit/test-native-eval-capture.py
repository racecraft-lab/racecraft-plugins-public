#!/usr/bin/env python3
"""Native transcript normalization must not turn incomplete evidence into passes."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from test_result import run_counted
from native_eval_capture import CaptureError, file_accesses, normalize_trace
from native_eval_fixture_reads import bind_controller_fixture_read_witnesses


CANARY_TRACE = Path("/private/tmp/speckit-native-entry-canary.91QKOu/run/attempts/bed7e376197242aca25343222c73f137/raw-raw_trace.jsonl")
CODEX_COUNT_THEN_SED = '''/bin/zsh -c "wc -l spec.md && sed -n '1,"'$p'"' spec.md"'''
CODEX_BOUNDED_COUNT_THEN_SED = "/bin/zsh -c \"wc -l spec.md && sed -n '1,9999p' spec.md\""


def stream(events):
    return "\n".join(json.dumps(event) for event in events)


def claude_events():
    return [
        {"type": "system", "subtype": "init", "model": "claude-test", "plugins": [], "tools": ["Skill"]},
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "a", "name": "Skill", "input": {"skill": "speckit-pro:test"}}]}, "parent_tool_use_id": None},
        {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "a", "content": "Loaded skill", "is_error": False}]}},
        {"type": "result", "subtype": "success", "is_error": False, "result": "done", "usage": {"input_tokens": 10, "output_tokens": 2}},
    ]


def claude_hook_prelude(session: str = "hook-session"):
    return [
        {"type": "system", "subtype": "hook_started", "hook_id": "hook-1", "hook_name": "SessionStart:startup",
         "hook_event": "SessionStart", "uuid": "hook-start", "session_id": session},
        {"type": "system", "subtype": "hook_response", "hook_id": "hook-1", "hook_name": "SessionStart:startup",
         "hook_event": "SessionStart", "output": "", "stdout": "", "stderr": "", "exit_code": 0,
         "outcome": "success", "uuid": "hook-response", "session_id": session},
    ]


def codex_events():
    return [
        {"type": "thread.started", "thread_id": "fixture-thread"},
        {"type": "turn.started"},
        {"type": "item.started", "item": {"id": "a", "type": "command_execution", "command": "read fixture", "status": "in_progress"}},
        {"type": "item.completed", "item": {"id": "a", "type": "command_execution", "command": "read fixture", "aggregated_output": "value", "status": "completed", "exit_code": 0}},
        {"type": "item.completed", "item": {"id": "b", "type": "agent_message", "text": "MARKER_TEST"}},
        {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 2}},
    ]


def codex_command_events(command: str, *, status: str = "completed", exit_code: int = 0):
    events = codex_events()
    events[2]["item"]["command"] = command
    events[3]["item"].update(command=command, status=status, exit_code=exit_code)
    return events


class NativeCaptureTests(unittest.TestCase):
    def test_claude_retains_hash_bound_tool_result_completion_positions(self):
        result = normalize_trace("claude", stream(claude_events()))
        output = json.dumps("Loaded skill", ensure_ascii=False, sort_keys=True,
                            separators=(",", ":"), allow_nan=False).encode("utf-8")
        self.assertEqual(result["native_metadata"]["claude_tool_results"], [{
            "tool_call_index": 0,
            "id": "a",
            "native_name": "Skill",
            "tool_use_position": 1,
            "tool_result_position": 2,
            "output_sha256": hashlib.sha256(output).hexdigest(),
            "output_bytes": len(output),
        }])

    def test_claude_read_uses_native_init_cwd_and_preserves_original_tool_evidence(self):
        events = claude_events()
        events[0].update(cwd="/private/tmp/native-eval/workspace", tools=["Read"])
        events[1]["message"]["content"][0].update(
            name="Read",
            input={"file_path": "/private/tmp/native-eval/workspace/input.json"},
        )
        result = normalize_trace("claude", stream(events))
        original = copy.deepcopy(result["tool_calls"])

        self.assertEqual(result["native_metadata"]["cwd"], "/private/tmp/native-eval/workspace")
        self.assertEqual(file_accesses(result), [{
            "operation": "read_file", "path": "input.json", "tool_call_index": 0,
        }])
        self.assertEqual(result["tool_calls"], original)
        self.assertEqual(result["tool_calls"][0]["name"], "Read")
        self.assertEqual(
            result["tool_calls"][0]["input"]["file_path"],
            "/private/tmp/native-eval/workspace/input.json",
        )

    def test_claude_read_rejects_partial_outside_and_noncanonical_paths(self):
        for file_path, extra in (
            ("/private/tmp/native-eval/outside.txt", {}),
            ("/private/tmp/native-eval/workspace/../outside.txt", {}),
            ("./plan.md", {}),
            ("plan.md", {"offset": 1}),
            ("plan.md", {"limit": 20}),
        ):
            with self.subTest(file_path=file_path, extra=extra):
                events = claude_events()
                events[0].update(cwd="/private/tmp/native-eval/workspace", tools=["Read"])
                events[1]["message"]["content"][0].update(
                    name="Read", input={"file_path": file_path, **extra},
                )
                self.assertEqual(file_accesses(normalize_trace("claude", stream(events))), [])

    def test_claude_read_evidence_requires_unaliased_native_provenance(self):
        events = claude_events()
        events[0].update(cwd="/private/tmp/native-eval/workspace", tools=["Read"])
        events[1]["message"]["content"][0].update(
            name="Read", input={"file_path": "plan.md"},
        )
        aliased = normalize_trace(
            "claude", stream(events), tool_aliases={"Read": "read_file"},
        )
        self.assertEqual(aliased["tool_calls"][0]["name"], "read_file")
        self.assertEqual(file_accesses(aliased), [])

    def test_codex_cat_and_explicit_full_sed_are_exact_unbounded_read_operations(self):
        commands = {
            "cat plan.md": "plan.md",
            "/bin/cat -- docs/spec.md": "docs/spec.md",
            "/bin/zsh -c 'cat \"current roadmap.md\"'": "current roadmap.md",
            "sed -n '1,$p' workflow.md": "workflow.md",
            "/usr/bin/sed -n '1,$p' -- docs/tasks.md": "docs/tasks.md",
        }
        for command, path in commands.items():
            with self.subTest(command=command):
                result = normalize_trace("codex", stream(codex_command_events(command)))
                original = copy.deepcopy(result["tool_calls"])
                self.assertEqual(file_accesses(result), [{
                    "operation": "read_file", "path": path, "tool_call_index": 0,
                }])
                self.assertEqual(result["tool_calls"], original)
                self.assertEqual(result["tool_calls"][0]["name"], "command_execution")
                self.assertEqual(result["tool_calls"][0]["input"], {"command": command})

    def test_codex_count_then_full_sed_native_shape_is_exact_read_evidence(self):
        content = "first\nsecond\nthird\n"
        # The command string is parser input, never executed: the confinement
        # contract forbids shell execution from the test tree. Reproduce the
        # `wc -l spec.md` then full `sed` output in Python.
        output = f"{len(content.splitlines()):8d} spec.md\n{content}"
        self.assertEqual(output, f"       3 spec.md\n{content}")

        events = codex_command_events(CODEX_COUNT_THEN_SED)
        events[3]["item"]["aggregated_output"] = output
        result = normalize_trace("codex", stream(events))
        original = copy.deepcopy(result["tool_calls"])
        self.assertEqual(file_accesses(result), [{
            "operation": "read_file", "path": "spec.md", "tool_call_index": 0,
        }])
        self.assertEqual(result["tool_calls"], original)
        self.assertEqual(result["tool_calls"][0]["output"], output)

    def test_codex_count_then_full_sed_rejects_failed_or_ambiguous_variants(self):
        later_failure = CODEX_COUNT_THEN_SED[:-1] + " && false\""
        variants = (
            (CODEX_COUNT_THEN_SED, "failed", 4),
            (later_failure, "failed", 1),
            ('/bin/zsh -c "wc -l spec.md && sed -n \'1,20p\' spec.md"', "completed", 0),
            (CODEX_COUNT_THEN_SED.replace(" spec.md\"", " plan.md\""), "completed", 0),
            (CODEX_COUNT_THEN_SED.replace(" spec.md\"", " $(printf spec.md)\""), "completed", 0),
            (CODEX_COUNT_THEN_SED[:-1] + " > copy.md\"", "completed", 0),
            (CODEX_COUNT_THEN_SED[:-1] + " | head -n 1\"", "completed", 0),
        )
        for command, status, exit_code in variants:
            with self.subTest(command=command, status=status):
                result = normalize_trace(
                    "codex",
                    stream(codex_command_events(command, status=status, exit_code=exit_code)),
                )
                self.assertEqual(file_accesses(result), [])

    def test_codex_bounded_read_requires_explicit_controller_witness(self):
        content = "first\nsecond\nthird\n"
        events = codex_command_events(CODEX_BOUNDED_COUNT_THEN_SED)
        events[3]["item"]["aggregated_output"] = f"       3 spec.md\n{content}"
        result = normalize_trace("codex", stream(events))
        original = copy.deepcopy(result)
        encoded = content.encode("utf-8")

        self.assertEqual(file_accesses(result), [])
        self.assertEqual(file_accesses(result, fixture_read_witnesses={"spec.md": {
            "bytes": len(encoded),
            "sha256": hashlib.sha256(encoded).hexdigest(),
        }}), [{
            "operation": "read_file",
            "path": "spec.md",
            "tool_call_index": 0,
            "provenance": {
                "schema_version": "native-eval-fixture-read-proof/v1",
                "kind": "count_then_bounded_sed",
                "bytes": len(encoded),
                "sha256": hashlib.sha256(encoded).hexdigest(),
                "start_line": 1,
                "end_line": 9999,
                "logical_lines": 3,
                "newline_count": 3,
                "count_header_verified": True,
            },
        }])
        bound = bind_controller_fixture_read_witnesses(result, {"spec.md": {
            "bytes": len(encoded),
            "sha256": hashlib.sha256(encoded).hexdigest(),
        }})
        self.assertEqual(file_accesses(bound), file_accesses(
            result,
            fixture_read_witnesses={"spec.md": {
                "bytes": len(encoded),
                "sha256": hashlib.sha256(encoded).hexdigest(),
            }},
        ))
        self.assertEqual(result, original)

    def test_codex_unsupported_or_ambiguous_commands_are_not_read_evidence(self):
        commands = (
            "echo plan.md",
            "rg plan.md .",
            "sed -n '1,20p' plan.md",
            "cat ../plan.md",
            "cat /private/tmp/native-eval/workspace/plan.md",
            "cat plan.md && echo ok",
            "cat plan.md > copy.md",
            "cat $(printf plan.md)",
            "cat `printf plan.md`",
            "/bin/zsh -c 'cat plan.md; echo ok'",
            "cat *.md",
            "cat -- -",
            "cat 'unterminated",
        )
        for command in commands:
            with self.subTest(command=command):
                result = normalize_trace("codex", stream(codex_command_events(command)))
                self.assertEqual(file_accesses(result), [])

    def test_failed_supported_codex_read_is_excluded_by_success_status(self):
        command = "cat input.json"
        failed = normalize_trace(
            "codex", stream(codex_command_events(command, status="failed", exit_code=4)),
        )
        successful = normalize_trace(
            "codex", stream(codex_command_events(command, status="completed", exit_code=0)),
        )
        self.assertEqual(file_accesses(failed), [])
        self.assertEqual(file_accesses(successful), [{
            "operation": "read_file", "path": "input.json", "tool_call_index": 0,
        }])
        self.assertFalse(failed["tool_calls"][0]["success"])
        self.assertTrue(successful["tool_calls"][0]["success"])

    def test_failed_unsupported_codex_command_preserves_native_provenance(self):
        command = (
            "/bin/zsh -c \"jq -e 'type == \\\"object\\\"' input.json >/dev/null "
            "&& cp input.json receipt.json\""
        )
        result = normalize_trace(
            "codex", stream(codex_command_events(command, status="failed", exit_code=4)),
        )
        self.assertEqual(file_accesses(result), [])
        self.assertFalse(result["tool_calls"][0]["success"])
        self.assertEqual(result["tool_calls"][0]["input"], {"command": command})

    def test_claude_successful_session_start_hook_prelude_is_preserved(self):
        events = claude_hook_prelude() + claude_events()
        events[2].update(session_id="hook-session", uuid="init")
        events[-1].update(session_id="hook-session", uuid="result")
        result = normalize_trace("claude", stream(events))
        self.assertEqual(result["final_text"], "done")
        self.assertEqual(result["native_metadata"]["hook_prelude"], claude_hook_prelude())

    def test_claude_hook_prelude_rejects_orphan_duplicate_mismatch_error_unknown_and_agent_work(self):
        for variation in ("orphan", "duplicate", "mismatch", "error", "unknown", "agent-work"):
            with self.subTest(variation=variation):
                prelude = claude_hook_prelude()
                if variation == "orphan":
                    prelude = prelude[1:]
                elif variation == "duplicate":
                    prelude.insert(1, copy.deepcopy(prelude[0]))
                elif variation == "mismatch":
                    prelude[1]["hook_id"] = "other"
                elif variation == "error":
                    prelude[1].update(exit_code=1, outcome="failure")
                elif variation == "unknown":
                    prelude[1] = {"type": "system", "subtype": "hook_progress", "session_id": "hook-session"}
                else:
                    prelude[1] = {"type": "assistant", "message": {"content": []}, "session_id": "hook-session"}
                events = prelude + claude_events()
                events[len(prelude)].update(session_id="hook-session", uuid="init")
                events[-1].update(session_id="hook-session", uuid="result")
                with self.assertRaises(CaptureError):
                    normalize_trace("claude", stream(events))

    if CANARY_TRACE.is_file():
        def test_replays_installed_claude_2_1_272_session_start_canary_when_available(self):
            result = normalize_trace("claude", CANARY_TRACE.read_text())
            self.assertTrue(result["completed"])
            self.assertEqual(result["final_text"], "DONE")
            self.assertEqual(result["native_metadata"]["hook_prelude"][1]["outcome"], "success")

    def test_json_lines_reject_duplicate_keys_and_non_json_constants(self):
        valid = stream(codex_events())
        duplicated = valid.replace(
            '"thread_id": "fixture-thread"',
            '"thread_id": "first", "thread_id": "fixture-thread"',
            1,
        )
        non_json = valid.replace('"thread_id": "fixture-thread"', '"thread_id": "fixture-thread", "extra": NaN', 1)
        for raw in (duplicated, non_json):
            with self.subTest(raw=raw.splitlines()[0]), self.assertRaises(CaptureError):
                normalize_trace("codex", raw)

    def test_claude_activation_requires_completed_skill_tool(self):
        result = normalize_trace("claude", stream(claude_events()))
        self.assertTrue(result["completed"])
        self.assertEqual(result["activations"], ["test"])
        self.assertEqual(result["final_text"], "done")
        self.assertTrue(result["tool_calls"][0]["success"])

    def test_claude_failed_skill_is_not_activation(self):
        events = claude_events()
        events[2]["message"]["content"][0]["is_error"] = True
        result = normalize_trace("claude", stream(events))
        self.assertEqual(result["activations"], [])
        self.assertFalse(result["tool_calls"][0]["success"])

    def test_foreign_namespace_is_not_normalized_into_target(self):
        events = claude_events()
        events[1]["message"]["content"][0]["input"]["skill"] = "other:test"
        self.assertEqual(normalize_trace("claude", stream(events))["activations"], ["other:test"])

    def test_claude_streaming_continuation_is_one_capture_not_duplicate_trial(self):
        events = claude_events()
        events[0].update(session_id="session", uuid="init-one")
        events[-1].update(session_id="session", uuid="result-one")
        resumed = copy.deepcopy(events[0])
        resumed["uuid"] = "init-two"
        final = copy.deepcopy(events[-1])
        final.update(uuid="result-two", result="finished after worker returned")
        events.insert(-1, resumed)
        events.append(final)
        result = normalize_trace("claude", stream(events))
        self.assertEqual(result["final_text"], "finished after worker returned")
        self.assertEqual(result["native_metadata"]["native_turns"], 2)
        for variation in ("foreign-session", "duplicate-uuid", "early-error"):
            with self.subTest(variation=variation):
                changed = copy.deepcopy(events)
                if variation == "foreign-session":
                    changed[-1]["session_id"] = "other"
                elif variation == "duplicate-uuid":
                    changed[-1]["uuid"] = "result-one"
                else:
                    changed[-2]["is_error"] = True
                with self.assertRaises(CaptureError):
                    normalize_trace("claude", stream(changed))

    def test_claude_cumulative_tree_usage_not_summed_across_results(self):
        events = claude_events()
        events[-1]["modelUsage"] = {"model": {"inputTokens": 3, "cacheReadInputTokens": 20,
            "cacheCreationInputTokens": 4, "outputTokens": 7, "thinkingTokens": 2}}
        result = normalize_trace("claude", stream(events))
        self.assertEqual(result["usage"]["input_tokens"], 27)
        self.assertEqual(result["usage"]["output_tokens"], 7)
        self.assertEqual(result["usage"]["cached_input_tokens"], 20)
        self.assertEqual(result["native_metadata"]["usage_scope"], "cumulative-agent-tree")

    def test_claude_continuation_uses_latest_cumulative_tree_usage(self):
        events = claude_events()
        events[0].update(session_id="session", uuid="init-one")
        events[-1].update(session_id="session", uuid="result-one", modelUsage={"model": {
            "inputTokens": 1, "cacheReadInputTokens": 2, "cacheCreationInputTokens": 3,
            "outputTokens": 4,
        }})
        resumed = copy.deepcopy(events[0])
        resumed["uuid"] = "init-two"
        final = copy.deepcopy(events[-1])
        final.update(uuid="result-two", modelUsage={"model": {
            "inputTokens": 10, "cacheReadInputTokens": 20, "cacheCreationInputTokens": 30,
            "outputTokens": 40,
        }})
        events.extend([resumed, final])
        result = normalize_trace("claude", stream(events))
        self.assertEqual(result["usage"]["input_tokens"], 60)
        self.assertEqual(result["usage"]["output_tokens"], 40)

    def test_claude_preserves_nested_tool_ownership(self):
        events = claude_events()
        events[1]["message"]["content"][0].update(name="Agent", input={"subagent_type": "worker"})
        nested = {"type": "assistant", "parent_tool_use_id": "a", "message": {"content": [
            {"type": "tool_use", "id": "child-read", "name": "Read", "input": {"file_path": "fixture.txt"}}]}}
        result = {"type": "user", "parent_tool_use_id": "a", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "child-read", "content": "value"}]}}
        events[2:2] = [nested, result]
        calls = normalize_trace("claude", stream(events))["tool_calls"]
        self.assertEqual(calls[1]["parent_id"], calls[0]["id"])
        self.assertEqual(calls[1]["output"], "value")

    def test_claude_rejects_orphaned_or_mismatched_nested_ownership(self):
        for variation in ("orphan-event", "mismatched-result", "non-agent-parent"):
            with self.subTest(variation=variation):
                events = claude_events()
                if variation == "orphan-event":
                    events.insert(1, {"type": "assistant", "parent_tool_use_id": "missing",
                        "message": {"content": [{"type": "text", "text": "ignored"}]}})
                else:
                    events[1]["message"]["content"][0].update(name="Agent", input={"subagent_type": "worker"})
                    nested_parent = "a" if variation == "mismatched-result" else "child-read"
                    events[2:2] = [
                        {"type": "assistant", "parent_tool_use_id": nested_parent,
                         "message": {"content": [{"type": "tool_use", "id": "child-read",
                             "name": "Read", "input": {"file_path": "fixture.txt"}}]}},
                        {"type": "user", "parent_tool_use_id": None,
                         "message": {"content": [{"type": "tool_result", "tool_use_id": "child-read",
                             "content": "value"}]}},
                    ]
                with self.assertRaises(CaptureError):
                    normalize_trace("claude", stream(events))

    def test_claude_rejects_malformed_ignored_message_and_earlier_result(self):
        for message in ({"content": "not-native-blocks"}, {}):
            with self.subTest(message=message):
                events = [claude_events()[0], {"type": "assistant", "message": message}, claude_events()[-1]]
                with self.assertRaises(CaptureError):
                    normalize_trace("claude", stream(events))

        events = claude_events()
        events[0].update(session_id="session", uuid="init-one")
        events[-1].update(session_id="session", uuid="result-one")
        resumed = copy.deepcopy(events[0])
        resumed["uuid"] = "init-two"
        final = copy.deepcopy(events[-1])
        final["uuid"] = "result-two"
        events.extend([resumed, final])
        del events[-3]["usage"]
        with self.assertRaises(CaptureError):
            normalize_trace("claude", stream(events))

    def test_claude_tool_result_must_exist_and_be_unambiguous(self):
        for variation in ("missing", "duplicate", "orphan"):
            with self.subTest(variation=variation):
                events = claude_events()
                if variation == "missing":
                    del events[2]
                elif variation == "duplicate":
                    events.insert(3, copy.deepcopy(events[2]))
                else:
                    events[2]["message"]["content"][0]["tool_use_id"] = "unknown"
                with self.assertRaises(CaptureError):
                    normalize_trace("claude", stream(events))

    def test_codex_only_final_exact_marker_counts(self):
        events = codex_events()
        result = normalize_trace("codex", stream(events), skill_markers={"MARKER_TEST": "test"})
        self.assertEqual(result["activations"], ["test"])
        for text in ("I will emit MARKER_TEST", '"MARKER_TEST"', "done"):
            with self.subTest(text=text):
                changed = copy.deepcopy(events)
                changed[-2]["item"]["text"] = text
                result = normalize_trace("codex", stream(changed), skill_markers={"MARKER_TEST": "test"})
                self.assertEqual(result["activations"], [])

    def test_codex_file_edit_is_native_tool_evidence(self):
        events = codex_events()
        events.insert(-1, {"type": "item.completed", "item": {"id": "c", "type": "file_change", "changes": [{"path": "receipt.txt", "kind": "add"}], "status": "completed"}})
        result = normalize_trace("codex", stream(events))
        self.assertEqual([call["name"] for call in result["tool_calls"]], ["command_execution", "file_change"])
        self.assertTrue(result["tool_calls"][-1]["success"])

    def test_codex_collaboration_preserves_observed_operation(self):
        events = codex_events()
        events.insert(-1, {"type": "item.completed", "item": {
            "id": "wait", "type": "collab_tool_call", "tool": "wait", "status": "completed",
            "sender_thread_id": "parent", "receiver_thread_ids": [], "agents_states": {}, "prompt": None,
        }})
        result = normalize_trace(
            "codex", stream(events), tool_aliases={"collab_tool_call": "Agent"},
        )
        call = result["tool_calls"][-1]
        self.assertEqual(call["name"], "wait")
        self.assertNotIn("Agent", [item["name"] for item in result["tool_calls"]])
        self.assertEqual(call["input"]["receiver_thread_ids"], [])

    def test_codex_ambiguous_command_kind_cannot_be_aliased_to_read(self):
        result = normalize_trace(
            "codex", stream(codex_events()), tool_aliases={"command_execution": "Read"},
        )
        self.assertEqual(result["tool_calls"][0]["name"], "command_execution")

    def test_codex_malformed_agent_message_is_not_ignored(self):
        events = codex_events()
        events.insert(-2, {"type": "item.completed", "item": {"id": "bad", "type": "agent_message"}})
        with self.assertRaises(CaptureError):
            normalize_trace("codex", stream(events))

    def test_native_failures_incomplete_and_out_of_order_are_invalid(self):
        for host, source in (("claude", claude_events()), ("codex", codex_events())):
            for variation in ("missing-terminal", "duplicate-terminal", "trailing", "error", "wrong-order"):
                with self.subTest(host=host, variation=variation):
                    events = copy.deepcopy(source)
                    if variation == "missing-terminal":
                        events.pop()
                    elif variation == "duplicate-terminal":
                        events.append(copy.deepcopy(events[-1]))
                    elif variation == "trailing":
                        events.append({"type": "assistant"})
                    elif variation == "error":
                        if host == "claude":
                            events[-1]["is_error"] = True
                        else:
                            events[-1] = {"type": "turn.failed", "error": {"message": "quota exhausted"}}
                    else:
                        events[0], events[1] = events[1], events[0]
                    with self.assertRaises(CaptureError):
                        normalize_trace(host, stream(events))

    def test_codex_dangling_and_duplicate_items_rejected(self):
        events = codex_events()
        del events[3]
        with self.assertRaises(CaptureError):
            normalize_trace("codex", stream(events))
        events = codex_events()
        events.insert(4, copy.deepcopy(events[3]))
        with self.assertRaises(CaptureError):
            normalize_trace("codex", stream(events))

    def test_codex_item_identity_cannot_change_type_during_execution(self):
        events = codex_events()
        events[3]["item"] = {"id": "a", "type": "file_change", "status": "completed", "changes": []}
        with self.assertRaises(CaptureError):
            normalize_trace("codex", stream(events))

    def test_malformed_unknown_or_empty_streams_rejected(self):
        for raw in ("", "[]", "not json", '{}', '{"type": 1}'):
            with self.subTest(raw=raw), self.assertRaises(CaptureError):
                normalize_trace("codex", raw)
        with self.assertRaises(CaptureError):
            normalize_trace("unknown", stream(codex_events()))

    def test_usage_types_are_not_coerced(self):
        for bad in (True, -1, "10"):
            with self.subTest(bad=bad):
                events = codex_events()
                events[-1]["usage"]["input_tokens"] = bad
                with self.assertRaises(CaptureError):
                    normalize_trace("codex", stream(events))


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(NativeCaptureTests), label="test-native-eval-capture"))
