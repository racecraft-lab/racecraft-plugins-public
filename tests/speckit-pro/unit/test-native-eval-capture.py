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
from native_eval_capture import (
    CaptureError,
    _claude_continuation_bridge,
    file_accesses,
    file_search_results,
    normalize_trace,
)
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


def claude_continuation_trace(session: str = "continuation-session"):
    events = claude_events()
    events[0].update(
        session_id=session, uuid="init-one", cwd="/tmp/work",
        claude_code_version="2.1.278",
    )
    events[1].update(session_id=session, uuid="skill-use")
    events[2].update(session_id=session, uuid="skill-result")
    events.pop()
    tool_use_id = "background-tool"
    task_id = "background-task"
    events.extend([
        {"type": "assistant", "message": {"content": [{
            "type": "tool_use", "id": tool_use_id, "name": "Agent",
            "input": {"description": "Finish UAT", "run_in_background": True},
        }]}, "parent_tool_use_id": None, "session_id": session, "uuid": "agent-use"},
        {"type": "system", "subtype": "task_started", "task_id": task_id,
         "tool_use_id": tool_use_id, "description": "Finish UAT",
         "is_backgrounded": True, "uuid": "task-start", "session_id": session},
        {"type": "user", "message": {"content": [{
            "type": "tool_result", "tool_use_id": tool_use_id,
            "content": "Agent launched", "is_error": False,
        }]}, "parent_tool_use_id": None, "session_id": session, "uuid": "agent-result"},
        {"type": "system", "subtype": "background_tasks_changed", "tasks": [],
         "uuid": "bridge-empty", "session_id": session},
        {"type": "system", "subtype": "task_updated", "task_id": task_id,
         "patch": {"status": "completed", "end_time": 1234},
         "uuid": "bridge-complete", "session_id": session},
        {"type": "system", "subtype": "task_notification", "task_id": task_id,
         "tool_use_id": tool_use_id, "status": "completed",
         "output_file": "/tmp/task.out", "summary": "UAT complete",
         "uuid": "bridge-notification", "session_id": session},
    ])
    resumed = copy.deepcopy(events[0])
    resumed["uuid"] = "init-two"
    events.append(resumed)
    events.extend([
        {"type": "result", "subtype": "success", "is_error": False,
         "result": "waiting for worker", "usage": {"input_tokens": 10, "output_tokens": 2},
         "session_id": session, "uuid": "result-one", "result_index": 0},
        {"type": "result", "subtype": "success", "is_error": False,
         "result": "finished after worker returned",
         "usage": {"input_tokens": 5, "output_tokens": 3},
         "session_id": session, "uuid": "result-two", "result_index": 1,
         "origin": {"kind": "task-notification"}},
    ])
    return events


def claude_backgrounded_bash_continuation_trace(
    status: str = "failed", session: str = "continuation-session",
):
    events = claude_continuation_trace(session)
    task_id = "background-task"
    description = "Search for existing execution-control ledger files"
    output_file = f"/tmp/{session}/tasks/{task_id}.output"
    tool_event = next(event for event in events if event.get("uuid") == "agent-use")
    tool_event["message"]["content"][0].update(
        name="Bash", input={"command": "find / -iname '*execution-control*'"},
    )
    started = next(event for event in events if event.get("uuid") == "task-start")
    started.update(
        description=description, is_backgrounded=False, task_type="local_bash",
    )
    result_index = next(index for index, event in enumerate(events)
                        if event.get("uuid") == "agent-result")
    events[result_index:result_index] = [
        {"type": "system", "subtype": "background_tasks_changed", "tasks": [{
            "task_id": task_id, "task_type": "local_bash", "description": description,
        }], "uuid": "bash-active", "session_id": session},
        {"type": "system", "subtype": "task_updated", "task_id": task_id,
         "patch": {"is_backgrounded": True}, "uuid": "bash-backgrounded",
         "session_id": session},
    ]
    result_event = next(event for event in events if event.get("uuid") == "agent-result")
    result_event["message"]["content"][0].update(
        content=(
            "Command did not complete within its 120s timeout and was moved to the "
            f"background (ID: {task_id}). Output is being written to: {output_file}. "
            "You will be notified when it completes."
        ),
        is_error=False,
    )
    result_event["tool_use_result"] = {
        "stdout": "", "stderr": "", "interrupted": False, "isImage": False,
        "noOutputExpected": False, "backgroundTaskId": task_id,
        "timedOutAfterMs": 120000,
    }
    updated = next(event for event in events if event.get("uuid") == "bridge-complete")
    updated["patch"]["status"] = status
    notification = next(
        event for event in events if event.get("uuid") == "bridge-notification"
    )
    notification.update(
        status=status, output_file=output_file,
        summary=f'Background command "{description}" {status}',
    )
    return events


def claude_hook_prelude(session: str = "hook-session"):
    return [
        {"type": "system", "subtype": "hook_started", "hook_id": "hook-1", "hook_name": "SessionStart:startup",
         "hook_event": "SessionStart", "uuid": "hook-start", "session_id": session},
        {"type": "system", "subtype": "hook_response", "hook_id": "hook-1", "hook_name": "SessionStart:startup",
         "hook_event": "SessionStart", "output": "", "stdout": "", "stderr": "", "exit_code": 0,
         "outcome": "success", "uuid": "hook-response", "session_id": session},
    ]


def claude_cleanup_trace(session: str = "cleanup-session"):
    events = claude_events()
    events[0].update(session_id=session, uuid="init")
    events[-1].update(session_id=session, uuid="result")
    tool_use_id = "cleanup-tool"
    task_id = "cleanup-task"
    description = "Finish the background command"
    events[-1:-1] = [
        {"type": "assistant", "message": {"content": [{
            "type": "tool_use", "id": tool_use_id, "name": "Bash",
            "input": {"command": "sleep 60"},
        }]}, "parent_tool_use_id": None, "session_id": session, "uuid": "tool-use"},
        {"type": "system", "subtype": "task_started", "task_id": task_id,
         "tool_use_id": tool_use_id, "description": description, "is_backgrounded": False,
         "task_type": "local_bash", "uuid": "task-start", "session_id": session},
        {"type": "system", "subtype": "background_tasks_changed",
         "tasks": [{"task_id": task_id, "task_type": "local_bash",
                    "description": description}],
         "uuid": "task-set", "session_id": session},
        {"type": "system", "subtype": "task_updated", "task_id": task_id,
         "patch": {"is_backgrounded": True}, "uuid": "task-backgrounded",
         "session_id": session},
        {"type": "user", "message": {"content": [{
            "type": "tool_result", "tool_use_id": tool_use_id,
            "content": "Command moved to the background", "is_error": False,
        }]}, "parent_tool_use_id": None, "session_id": session, "uuid": "tool-result"},
    ]
    cleanup = [
        {"type": "system", "subtype": "background_tasks_changed", "tasks": [],
         "uuid": "cleanup-empty", "session_id": session},
        {"type": "system", "subtype": "task_updated", "task_id": task_id,
         "patch": {"status": "killed", "end_time": 1234},
         "uuid": "cleanup-killed", "session_id": session},
        {"type": "system", "subtype": "task_notification", "task_id": task_id,
         "tool_use_id": tool_use_id, "status": "stopped", "output_file": "/tmp/task.out",
         "summary": description, "uuid": "cleanup-stopped", "session_id": session},
    ]
    return events, cleanup


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

class NativeCaptureEvidenceRepairTests(unittest.TestCase):
    def test_codex_safe_compound_reads_preserve_full_read_evidence(self):
        command = (
            "/bin/zsh -c \"printf '%s\\n' 'INPUTS' && sed -n '1,999p' plan.md "
            "&& find docs -maxdepth 3 -type f -print | sort\""
        )
        content = "plan line one\nplan line two\n"
        events = codex_command_events(command)
        events[3]["item"]["aggregated_output"] = (
            "INPUTS\n" + content + "docs/plan.md\n"
        )
        result = bind_controller_fixture_read_witnesses(
            normalize_trace("codex", stream(events)),
            {"plan.md": {
                "bytes": len(content.encode("utf-8")),
                "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            }},
        )
        accesses = file_accesses(result)
        self.assertTrue(any(
            row["path"] == "plan.md"
            and row.get("provenance", {}).get("kind") == "compound_bounded_sed"
            for row in accesses
        ))

    def test_codex_compound_reads_reject_forged_partial_and_arbitrary_shell(self):
        content = "one\ntwo\n"
        encoded = content.encode("utf-8")
        witness = {"plan.md": {
            "bytes": len(encoded), "sha256": hashlib.sha256(encoded).hexdigest(),
        }}
        variants = (
            ("sed -n '1,1p' plan.md", "one\n"),
            ("sed -n '1,999p' plan.md", "one\nforged\n"),
            ("sed -n '1,999p' plan.md && python3 helper.py", content),
            ("sed -n '1,999p' plan.md > copy.md", content),
            ("sed -n '1,999p' plan.md | head -1", "one\n"),
            ("sed -n '1,999p' $(printf plan.md)", content),
        )
        for command, output in variants:
            with self.subTest(command=command):
                events = codex_command_events(command)
                events[3]["item"]["aggregated_output"] = output
                result = bind_controller_fixture_read_witnesses(
                    normalize_trace("codex", stream(events)), witness,
                )
                self.assertEqual(file_accesses(result), [])

class NativeCaptureProjectionTests(unittest.TestCase):
    def test_codex_jq_identity_and_nl_are_full_reads_but_jq_projection_is_not(self):
        for command, expected in (
            ("jq . input.json", "input.json"),
            ("jq -- . nested/input.json", "nested/input.json"),
            ("nl -ba docs/plan.md", "docs/plan.md"),
        ):
            with self.subTest(command=command):
                result = normalize_trace("codex", stream(codex_command_events(command)))
                self.assertEqual(file_accesses(result), [{
                    "operation": "read_file", "path": expected, "tool_call_index": 0,
                }])
        projected = normalize_trace(
            "codex", stream(codex_command_events("jq '{id: .id}' input.json")),
        )
        self.assertEqual(file_accesses(projected), [])

class NativeCaptureScopedSearchTests(unittest.TestCase):
    def test_codex_rg_files_uses_only_controller_project_scope(self):
        command = "/bin/zsh -c \"rg --files -g '*roadmap*' -g '*workflow*' .\""
        events = codex_command_events(command)
        events[3]["item"]["aggregated_output"] = (
            "./docs/current-technical-roadmap.md\n"
            ".agents/skills/runtime-roadmap.md\n"
        )
        result = bind_controller_fixture_read_witnesses(
            normalize_trace("codex", stream(events)),
            {
                "README.md": {
                    "bytes": len(b"readme\n"),
                    "sha256": hashlib.sha256(b"readme\n").hexdigest(),
                },
                "docs/current-technical-roadmap.md": {
                    "bytes": len(b"roadmap\n"),
                    "sha256": hashlib.sha256(b"roadmap\n").hexdigest(),
                },
            },
        )
        rows = file_search_results(result, host="codex")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["paths"], ["docs/current-technical-roadmap.md"])
        self.assertEqual(rows[0]["scope"], "controller-project-artifacts")

    def test_codex_rg_files_rejects_partial_wrong_scope_and_failed_results(self):
        command = "rg --files -g '*roadmap*' ."
        witnesses = {
            "docs/current-roadmap.md": {
                "bytes": len(b"one\n"), "sha256": hashlib.sha256(b"one\n").hexdigest(),
            },
            "docs/next-roadmap.md": {
                "bytes": len(b"two\n"), "sha256": hashlib.sha256(b"two\n").hexdigest(),
            },
        }
        for output, status, exit_code in (
            ("docs/current-roadmap.md\n", "completed", 0),
            ("docs/current-roadmap.md\nprivate/forged-roadmap.md\n", "completed", 0),
            ("docs/current-roadmap.md\ndocs/next-roadmap.md\n", "failed", 1),
        ):
            with self.subTest(output=output, status=status):
                events = codex_command_events(command, status=status, exit_code=exit_code)
                events[3]["item"]["aggregated_output"] = output
                result = bind_controller_fixture_read_witnesses(
                    normalize_trace("codex", stream(events)), witnesses,
                )
                self.assertEqual(file_search_results(result, host="codex"), [])


class NativeCaptureContinuationTests(unittest.TestCase):
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

class NativeCaptureClaudePreludeTests(unittest.TestCase):
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

class NativeCaptureActivationTests(unittest.TestCase):
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

class ClaudeContinuationTests(unittest.TestCase):
    def test_claude_streaming_continuation_is_one_capture_not_duplicate_trial(self):
        events = claude_continuation_trace()
        result = normalize_trace("claude", stream(events))
        self.assertEqual(result["final_text"], "finished after worker returned")
        self.assertEqual(result["native_metadata"]["native_turns"], 2)
        self.assertEqual(
            [turn["result_index"] for turn in result["native_metadata"]["claude_turns"]],
            [0, 1],
        )
        bridge = result["native_metadata"]["continuation_bridges"]
        self.assertEqual(len(bridge), 1)
        self.assertEqual(bridge[0]["task_id"], "background-task")
        self.assertEqual(
            [record["subtype"] for record in bridge[0]["records"]],
            ["background_tasks_changed", "task_updated", "task_notification"],
        )

    def test_claude_auto_backgrounded_bash_binds_terminal_outcome(self):
        for status, expected_success in (("completed", True), ("failed", False)):
            with self.subTest(status=status):
                result = normalize_trace(
                    "claude", stream(claude_backgrounded_bash_continuation_trace(status)),
                )
                bash = next(call for call in result["tool_calls"]
                            if call["id"] == "background-tool")
                self.assertIs(bash["success"], expected_success)
                bridge = result["native_metadata"]["continuation_bridges"][0]
                self.assertEqual(bridge["task_type"], "local_bash")
                self.assertEqual(bridge["terminal_status"], status)

    def test_claude_auto_backgrounded_bash_rejects_unbound_or_forged_lifecycle(self):
        for variation in (
            "mismatched-terminal", "unsupported-terminal", "foreground-start",
            "wrong-task-type", "missing-active-set", "missing-background-update",
            "wrong-background-update", "result-before-background-update",
            "wrong-native-task", "missing-native-field", "foreign-result-session",
            "errored-handoff", "mismatched-output-file",
        ):
            with self.subTest(variation=variation):
                events = claude_backgrounded_bash_continuation_trace()
                started_index = next(index for index, event in enumerate(events)
                                     if event.get("uuid") == "task-start")
                active_index = next(index for index, event in enumerate(events)
                                    if event.get("uuid") == "bash-active")
                update_index = next(index for index, event in enumerate(events)
                                    if event.get("uuid") == "bash-backgrounded")
                result_index = next(index for index, event in enumerate(events)
                                    if event.get("uuid") == "agent-result")
                bridge_update = next(
                    event for event in events if event.get("uuid") == "bridge-complete"
                )
                notification = next(
                    event for event in events if event.get("uuid") == "bridge-notification"
                )
                result_event = events[result_index]
                if variation == "mismatched-terminal":
                    notification["status"] = "completed"
                elif variation == "unsupported-terminal":
                    bridge_update["patch"]["status"] = "killed"
                    notification["status"] = "killed"
                elif variation == "foreground-start":
                    events[started_index]["is_backgrounded"] = True
                elif variation == "wrong-task-type":
                    events[started_index]["task_type"] = "local_agent"
                elif variation == "missing-active-set":
                    events.pop(active_index)
                elif variation == "missing-background-update":
                    events.pop(update_index)
                elif variation == "wrong-background-update":
                    events[update_index]["patch"] = {"is_backgrounded": False}
                elif variation == "result-before-background-update":
                    result = events.pop(result_index)
                    events.insert(update_index, result)
                elif variation == "wrong-native-task":
                    result_event["tool_use_result"]["backgroundTaskId"] = "other-task"
                elif variation == "missing-native-field":
                    del result_event["tool_use_result"]["timedOutAfterMs"]
                elif variation == "foreign-result-session":
                    result_event["session_id"] = "other-session"
                elif variation == "errored-handoff":
                    result_event["message"]["content"][0]["is_error"] = True
                else:
                    notification["output_file"] = "/tmp/forged.output"
                with self.assertRaises(CaptureError):
                    normalize_trace("claude", stream(events))

    def test_claude_explicit_agent_still_requires_completed_terminal_pair(self):
        events = claude_continuation_trace()
        next(event for event in events if event.get("uuid") == "bridge-complete")[
            "patch"
        ]["status"] = "failed"
        next(event for event in events if event.get("uuid") == "bridge-notification")[
            "status"
        ] = "failed"
        with self.assertRaisesRegex(CaptureError, "background Agent"):
            normalize_trace("claude", stream(events))

    def test_claude_continuation_allows_same_session_parallel_progress_before_resume(self):
        events = claude_continuation_trace()
        init_index = next(index for index, event in enumerate(events)
                          if event.get("uuid") == "init-two")
        events[init_index - 3]["tasks"] = [{
            "task_id": "remaining-task", "task_type": "local_agent",
            "description": "Still running",
        }]
        interleaved = [
            {"type": "system", "subtype": "task_progress", "task_id": "remaining-task",
             "tool_use_id": "remaining-tool", "session_id": "continuation-session",
             "uuid": "remaining-progress"},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "waiting"}]},
             "parent_tool_use_id": None, "session_id": "continuation-session",
             "uuid": "root-waiting"},
        ]
        events[init_index:init_index] = interleaved
        result = normalize_trace("claude", stream(events))
        self.assertEqual(result["native_metadata"]["native_turns"], 2)
        self.assertEqual(
            result["native_metadata"]["continuation_bridges"][0]["task_id"],
            "background-task",
        )

        unsafe = copy.deepcopy(events)
        unsafe[init_index + 1]["message"]["content"] = [{
            "type": "tool_use", "id": "root-work", "name": "Bash",
            "input": {"command": "echo unsafe"},
        }]
        with self.assertRaisesRegex(CaptureError, "suffix contains root work"):
            normalize_trace("claude", stream(unsafe))

    def test_parallel_task_completion_binds_to_launch_before_prior_resume(self):
        session = "parallel-continuation"
        tool_use_id = "parallel-tool"
        task_id = "parallel-task"
        events = [
            {"type": "system", "subtype": "init", "session_id": session,
             "uuid": "initial-init"},
            {"type": "assistant", "message": {"content": [{
                "type": "tool_use", "id": tool_use_id, "name": "Agent",
                "input": {"description": "Parallel worker", "run_in_background": True},
            }]}, "parent_tool_use_id": None, "session_id": session,
             "uuid": "parallel-agent"},
            {"type": "system", "subtype": "task_started", "task_id": task_id,
             "tool_use_id": tool_use_id, "description": "Parallel worker",
             "is_backgrounded": True, "session_id": session, "uuid": "parallel-start"},
            {"type": "system", "subtype": "init", "session_id": session,
             "uuid": "prior-resume"},
            {"type": "system", "subtype": "background_tasks_changed", "tasks": [],
             "session_id": session, "uuid": "parallel-empty"},
            {"type": "system", "subtype": "task_updated", "task_id": task_id,
             "patch": {"status": "completed", "end_time": 1234},
             "session_id": session, "uuid": "parallel-complete"},
            {"type": "system", "subtype": "task_notification", "task_id": task_id,
             "tool_use_id": tool_use_id, "status": "completed",
             "output_file": "/tmp/parallel.out", "summary": "Worker complete",
             "session_id": session, "uuid": "parallel-notification"},
            {"type": "system", "subtype": "init", "session_id": session,
             "uuid": "current-resume"},
        ]
        bridge = _claude_continuation_bridge(
            events, turn=2, init_index=7, prior_init_index=3,
        )
        self.assertEqual(bridge["task_id"], task_id)
        self.assertEqual(bridge["tool_use_id"], tool_use_id)

    def test_claude_continuation_rejects_unbound_or_ambiguous_turns(self):
        for variation in (
            "foreign-bridge", "missing-bridge", "reordered-bridge", "changed-init",
            "bad-result-index", "bad-result-origin", "duplicate-uuid",
            "failure-then-success", "incomplete-suffix", "foreground-agent",
        ):
            with self.subTest(variation=variation):
                changed = claude_continuation_trace()
                init_index = next(index for index, event in enumerate(changed)
                                  if event.get("uuid") == "init-two")
                if variation == "foreign-bridge":
                    changed[init_index - 2]["session_id"] = "other"
                elif variation == "missing-bridge":
                    changed.pop(init_index - 3)
                elif variation == "reordered-bridge":
                    changed[init_index - 3], changed[init_index - 2] = (
                        changed[init_index - 2], changed[init_index - 3]
                    )
                elif variation == "changed-init":
                    changed[init_index]["model"] = "different-model"
                elif variation == "bad-result-index":
                    changed[-1]["result_index"] = 2
                elif variation == "bad-result-origin":
                    changed[-1]["origin"] = {"kind": "user-prompt"}
                elif variation == "duplicate-uuid":
                    changed[-1]["uuid"] = "result-one"
                elif variation == "failure-then-success":
                    changed[-2].update(is_error=True, subtype="error")
                elif variation == "foreground-agent":
                    agent = next(
                        block for event in changed
                        for block in event.get("message", {}).get("content", [])
                        if isinstance(block, dict) and block.get("name") == "Agent"
                    )
                    agent["input"]["run_in_background"] = False
                else:
                    changed.pop()
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
        events = claude_continuation_trace()
        events[-2]["modelUsage"] = {"model": {
            "inputTokens": 1, "cacheReadInputTokens": 2, "cacheCreationInputTokens": 3,
            "outputTokens": 4,
        }}
        events[-1]["modelUsage"] = {"model": {
            "inputTokens": 10, "cacheReadInputTokens": 20, "cacheCreationInputTokens": 30,
            "outputTokens": 40,
        }}
        result = normalize_trace("claude", stream(events))
        self.assertEqual(result["usage"]["input_tokens"], 60)
        self.assertEqual(result["usage"]["output_tokens"], 40)

class NativeCaptureOwnershipTests(unittest.TestCase):
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

    def test_claude_accepts_bounded_heartbeat_progress_for_owning_tool(self):
        events = claude_events()
        events[1]["message"]["content"][0].update(
            name="Bash", input={"command": "python3 -m bounded_helper"},
        )
        events[2:2] = [{
            "type": "tool_progress", "tool_use_id": "a-heartbeat-0",
            "tool_name": "Bash", "parent_tool_use_id": "a",
            "elapsed_time_seconds": 30, "heartbeat": True,
        }]
        calls = normalize_trace("claude", stream(events))["tool_calls"]
        self.assertEqual(calls[0]["name"], "Bash")

    def test_claude_rejects_unbound_or_malformed_tool_progress(self):
        base = claude_events()
        base[1]["message"]["content"][0].update(
            name="Bash", input={"command": "python3 -m bounded_helper"},
        )
        progress = {
            "type": "tool_progress", "tool_use_id": "a-heartbeat-0",
            "tool_name": "Bash", "parent_tool_use_id": "a",
            "elapsed_time_seconds": 30, "heartbeat": True,
        }
        variations = {
            "wrong-parent": {**progress, "parent_tool_use_id": "missing"},
            "wrong-name": {**progress, "tool_name": "Agent"},
            "not-heartbeat": {**progress, "heartbeat": False},
            "bad-id": {**progress, "tool_use_id": "a-progress-0"},
            "bad-elapsed": {**progress, "elapsed_time_seconds": 0},
        }
        for label, malformed in variations.items():
            with self.subTest(label=label):
                events = copy.deepcopy(base)
                events[2:2] = [malformed]
                with self.assertRaises(CaptureError):
                    normalize_trace("claude", stream(events))

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


class ClaudeCleanupEpilogueTests(unittest.TestCase):
    def test_claude_post_result_cleanup_epilogue_is_preserved(self):
        events, cleanup = claude_cleanup_trace()
        result = normalize_trace("claude", stream(events + cleanup))
        self.assertEqual(result["final_text"], "done")
        self.assertEqual(result["native_metadata"]["native_turns"], 1)
        self.assertEqual(result["native_metadata"]["cleanup_epilogue"], cleanup)

    def test_claude_cleanup_rejects_incomplete_reordered_duplicate_and_non_system_events(self):
        for variation in (
            "missing-first", "missing-middle", "missing-last", "reordered", "duplicate",
            "assistant", "user", "error", "unknown-system", "extra-after",
        ):
            with self.subTest(variation=variation):
                events, cleanup = claude_cleanup_trace()
                if variation.startswith("missing-"):
                    cleanup.pop({"missing-first": 0, "missing-middle": 1, "missing-last": 2}[variation])
                elif variation == "reordered":
                    cleanup[0], cleanup[1] = cleanup[1], cleanup[0]
                elif variation == "duplicate":
                    cleanup.insert(1, copy.deepcopy(cleanup[0]))
                elif variation == "assistant":
                    cleanup[0] = {"type": "assistant", "message": {"content": []}}
                elif variation == "user":
                    cleanup[0] = {"type": "user", "message": {"content": []}}
                elif variation == "error":
                    cleanup[0] = {"type": "error", "subtype": "background_tasks_changed"}
                elif variation == "unknown-system":
                    cleanup[0]["subtype"] = "cleanup_started"
                else:
                    cleanup.append({"type": "system", "subtype": "cleanup_finished"})
                with self.assertRaises(CaptureError):
                    normalize_trace("claude", stream(events + cleanup))

    def test_claude_cleanup_rejects_mismatched_or_malformed_cleanup_identity(self):
        for variation in (
            "nonempty-tasks", "updated-task", "notification-task", "notification-tool",
            "foreign-session", "nested-first", "nested-middle", "nested-last", "missing-uuid",
            "duplicate-uuid", "runtime-uuid", "prelude-uuid", "wrong-update-status", "missing-end-time",
            "boolean-end-time", "extra-update-field", "wrong-notification-status",
            "relative-output", "empty-summary", "different-summary",
        ):
            with self.subTest(variation=variation):
                events, cleanup = claude_cleanup_trace()
                if variation == "nonempty-tasks":
                    cleanup[0]["tasks"] = [{"task_id": "cleanup-task"}]
                elif variation == "updated-task":
                    cleanup[1]["task_id"] = "other-task"
                elif variation == "notification-task":
                    cleanup[2]["task_id"] = "other-task"
                elif variation == "notification-tool":
                    cleanup[2]["tool_use_id"] = "other-tool"
                elif variation == "foreign-session":
                    cleanup[1]["session_id"] = "other-session"
                elif variation.startswith("nested-"):
                    index = {"nested-first": 0, "nested-middle": 1, "nested-last": 2}[variation]
                    cleanup[index]["parent_tool_use_id"] = "parent"
                elif variation == "missing-uuid":
                    cleanup[0]["uuid"] = ""
                elif variation == "duplicate-uuid":
                    cleanup[2]["uuid"] = cleanup[1]["uuid"]
                elif variation == "runtime-uuid":
                    cleanup[0]["uuid"] = "result"
                elif variation == "prelude-uuid":
                    events = claude_hook_prelude("cleanup-session") + events
                    cleanup[0]["uuid"] = "hook-start"
                elif variation == "wrong-update-status":
                    cleanup[1]["patch"]["status"] = "completed"
                elif variation == "missing-end-time":
                    del cleanup[1]["patch"]["end_time"]
                elif variation == "boolean-end-time":
                    cleanup[1]["patch"]["end_time"] = True
                elif variation == "extra-update-field":
                    cleanup[1]["patch"]["reason"] = "shutdown"
                elif variation == "wrong-notification-status":
                    cleanup[2]["status"] = "completed"
                elif variation == "relative-output":
                    cleanup[2]["output_file"] = "task.out"
                elif variation == "empty-summary":
                    cleanup[2]["summary"] = ""
                else:
                    cleanup[2]["summary"] = "different task"
                with self.assertRaises(CaptureError):
                    normalize_trace("claude", stream(events + cleanup))

    def test_claude_cleanup_requires_one_still_active_prior_task_and_tool_use(self):
        for variation in (
            "missing-start", "duplicate-start", "mismatched-start-tool", "nested-start",
            "foreign-start-session", "missing-tool-use", "duplicate-tool-use",
            "completed-before-result", "stopped-before-result", "removed-before-result",
        ):
            with self.subTest(variation=variation):
                events, cleanup = claude_cleanup_trace()
                start_index = next(index for index, event in enumerate(events)
                                   if event.get("subtype") == "task_started")
                if variation == "missing-start":
                    events.pop(start_index)
                elif variation == "duplicate-start":
                    events.insert(start_index + 1, copy.deepcopy(events[start_index]))
                elif variation == "mismatched-start-tool":
                    events[start_index]["tool_use_id"] = "other-tool"
                elif variation == "nested-start":
                    events[start_index]["parent_tool_use_id"] = "parent"
                elif variation == "foreign-start-session":
                    events[start_index]["session_id"] = "other-session"
                elif variation == "missing-tool-use":
                    tool_event = next(event for event in events if event.get("uuid") == "tool-use")
                    tool_event["message"]["content"][0]["id"] = "other-tool"
                elif variation == "duplicate-tool-use":
                    tool_event = next(event for event in events if event.get("uuid") == "tool-use")
                    duplicate = copy.deepcopy(tool_event)
                    duplicate["uuid"] = "second-tool-use"
                    events.insert(start_index, duplicate)
                elif variation == "completed-before-result":
                    events.insert(-1, {"type": "system", "subtype": "task_updated",
                        "task_id": "cleanup-task", "patch": {"status": "completed"},
                        "uuid": "early-complete", "session_id": "cleanup-session"})
                elif variation == "stopped-before-result":
                    events.insert(-1, {"type": "system", "subtype": "task_notification",
                        "task_id": "cleanup-task", "status": "stopped",
                        "uuid": "early-stop", "session_id": "cleanup-session"})
                else:
                    events.insert(-1, {"type": "system", "subtype": "background_tasks_changed",
                        "tasks": [], "uuid": "early-empty", "session_id": "cleanup-session"})
                with self.assertRaises(CaptureError):
                    normalize_trace("claude", stream(events + cleanup))


if __name__ == "__main__":
    suite = unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeCaptureTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeCaptureEvidenceRepairTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeCaptureProjectionTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeCaptureScopedSearchTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeCaptureContinuationTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeCaptureClaudePreludeTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeCaptureActivationTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(ClaudeContinuationTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeCaptureOwnershipTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(ClaudeCleanupEpilogueTests),
    ))
    raise SystemExit(run_counted(suite, label="test-native-eval-capture"))
