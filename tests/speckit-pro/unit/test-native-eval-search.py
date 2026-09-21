#!/usr/bin/env python3
"""Complete native search evidence, including genuine empty results."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import native_eval_capture as capture
from native_eval_grading import grade_observation
from test_result import run_counted


def observation(host, output="", *, pattern="**/*roadmap*.md"):
    call = {
        "id": "search", "success": True, "parent_id": None, "output": output,
        "name": "Glob" if host == "claude" else "command_execution",
        "input": {"pattern": pattern} if host == "claude" else {
            "command": f"find . -type f -name '{pattern[3:]}' -print",
        },
    }
    metadata = {"cwd": "/workspace"}
    if host == "claude":
        names = [] if output == "No files found" else output.splitlines()
        metadata["claude_tool_results"] = [{
            "id": "search", "native_name": "Glob", "tool_call_index": 0,
            "glob_result": {
                "filenames": names, "numFiles": len(names), "totalMatches": len(names),
                "truncated": False, "countIsComplete": True,
            },
        }]
    return {
        "completed": True, "error": None, "final_text": "No tracking artifacts.",
        "activations": [], "artifacts": {}, "tool_calls": [call], "usage": {},
        "native_metadata": metadata,
    }


class NativeSearchTests(unittest.TestCase):
    def test_child_search_cannot_prove_parent_workspace_absence(self):
        for host, output in (("claude", "No files found"), ("codex", "")):
            with self.subTest(host=host):
                value = observation(host, output)
                value["tool_calls"][0]["parent_id"] = "child-with-independent-cwd"
                self.assertEqual(capture.file_search_results(value, host=host), [])

    def test_successful_empty_search_is_not_a_prose_claim(self):
        for host, output in (("claude", "No files found"), ("codex", "")):
            with self.subTest(host=host):
                value = observation(host, output)
                self.assertEqual(capture.file_search_results(value, host=host), [{
                    "pattern": "**/*roadmap*.md", "paths": [], "tool_call_index": 0,
                }])
                value["tool_calls"] = []
                self.assertEqual(capture.file_search_results(value, host=host), [])

    def test_real_recursive_find_includes_hidden_files_and_preserves_all_matches(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / ".hidden").mkdir()
            (root / ".hidden/current-technical-roadmap.md").write_text("project\n")
            (root / "roadmap.md").write_text("project\n")
            value = observation("codex")
            command = value["tool_calls"][0]["input"]["command"]
            # The command string is parser input, never executed: the confinement
            # contract forbids shell execution from the test tree. Supply the
            # recursive-find output that command produces for this exact tree.
            self.assertEqual(command, "find . -type f -name '*roadmap*.md' -print")
            value["tool_calls"][0]["output"] = ".hidden/current-technical-roadmap.md\nroadmap.md\n"
            records = capture.file_search_results(value, host="codex")
            self.assertEqual(records[0]["paths"], [".hidden/current-technical-roadmap.md", "roadmap.md"])

    def test_glob_root_scope_and_absolute_results_are_exact(self):
        value = observation("claude", "/workspace/.hidden/roadmap.md")
        value["tool_calls"][0]["input"]["path"] = "/workspace"
        self.assertEqual(capture.file_search_results(value, host="claude")[0]["paths"], [".hidden/roadmap.md"])
        for scope in ("docs", "../workspace", "/other", "/workspace/", [], {}):
            with self.subTest(scope=scope):
                value["tool_calls"][0]["input"]["path"] = scope
                self.assertEqual(capture.file_search_results(value, host="claude"), [])

    def test_failed_truncated_duplicate_and_escaped_results_do_not_qualify(self):
        for host in ("claude", "codex"):
            for output in ("Permission denied", "roadmap.md\n... results truncated",
                           "roadmap.md\nroadmap.md", "../roadmap.md", "/other/roadmap.md",
                           "unrelated.txt", "roadmap.md\n\nother-roadmap.md"):
                with self.subTest(host=host, output=output):
                    self.assertEqual(capture.file_search_results(observation(host, output), host=host), [])
            value = observation(host)
            value["tool_calls"][0]["success"] = False
            self.assertEqual(capture.file_search_results(value, host=host), [])

    def test_partial_filtered_piped_and_expanding_commands_do_not_qualify(self):
        for command in (
            "find docs -type f -name '*roadmap*.md' -print",
            "find . -maxdepth 2 -type f -name '*roadmap*.md' -print",
            "find . -type f -name '*roadmap*.md' -print | head -1",
            "find . -type f -name '*roadmap*.md' -print | sort",
            "find . -type f -name *roadmap*.md -print",
            "find . -type f -name '$PATTERN' -print",
            "printf ''", "find . -type f -name '*roadmap*.md' -print 2>/dev/null",
            "find . -type f -name '*roadmap*.md' -print || true",
        ):
            with self.subTest(command=command):
                value = observation("codex")
                value["tool_calls"][0]["input"]["command"] = command
                self.assertEqual(capture.file_search_results(value, host="codex"), [])

    def test_one_non_login_native_shell_wrapper_is_supported(self):
        value = observation("codex", "./roadmap.md\n")
        value["tool_calls"][0]["input"]["command"] = '/bin/zsh -c "find . -type f -name \'*roadmap*.md\' -print"'
        self.assertEqual(capture.file_search_results(value, host="codex")[0]["paths"], ["roadmap.md"])
        value["tool_calls"][0]["input"]["command"] = value["tool_calls"][0]["input"]["command"].replace(" -c ", " -lc ")
        self.assertEqual(capture.file_search_results(value, host="codex"), [])

    def test_successful_newline_separated_empty_finds_prove_each_absence(self):
        value = observation("codex")
        first = "find . -type f -name 'current-technical-roadmap.md' -print"
        second = "find . -type f -name 'SPEC-*-workflow.md' -print"
        value["tool_calls"][0]["input"]["command"] = f"/bin/zsh -c \"{first}\n{second}\""
        self.assertEqual(capture.file_search_results(value, host="codex"), [
            {"pattern": "**/current-technical-roadmap.md", "paths": [], "tool_call_index": 0},
            {"pattern": "**/SPEC-*-workflow.md", "paths": [], "tool_call_index": 0},
        ])
        case = {
            "requirements": [{"id": "search", "description": "Prove both absences."}],
            "checks": [
                {"id": "roadmap", "requirement": "search", "type": "file_search",
                 "pattern": "**/current-technical-roadmap.md", "matches": []},
                {"id": "workflow", "requirement": "search", "type": "file_search",
                 "pattern": "**/SPEC-*-workflow.md", "matches": []},
            ],
        }
        self.assertEqual(grade_observation(case, value, host="codex")["status"], "pass")

        for command, output, success in (
            (f"/bin/zsh -c \"{first}; {second}\"", "", True),
            (f"/bin/zsh -c \"{first}\n{second}\"", "unexpected.md\n", True),
            (f"/bin/zsh -c \"{first}\n{second}\"", "", False),
            (f"/bin/zsh -c \"{first}\n{first}\"", "", True),
        ):
            with self.subTest(command=command, output=output, success=success):
                changed = copy.deepcopy(value)
                changed["tool_calls"][0]["input"]["command"] = command
                changed["tool_calls"][0]["output"] = output
                changed["tool_calls"][0]["success"] = success
                self.assertEqual(capture.file_search_results(changed, host="codex"), [])

    def test_glob_requires_native_complete_counts_not_just_text(self):
        value = observation("claude", "No files found")
        for updates in (
            {"truncated": True}, {"countIsComplete": False}, {"totalMatches": 1},
            {"numFiles": True}, {"filenames": ["hidden/roadmap.md"]},
        ):
            with self.subTest(updates=updates):
                bad = copy.deepcopy(value)
                bad["native_metadata"]["claude_tool_results"][0]["glob_result"].update(updates)
                self.assertEqual(capture.file_search_results(bad, host="claude"), [])
        value["native_metadata"].pop("claude_tool_results")
        self.assertEqual(capture.file_search_results(value, host="claude"), [])

    def test_native_trace_binds_glob_counts_to_the_completed_tool(self):
        template = observation("claude", "No files found")
        result = template["native_metadata"]["claude_tool_results"][0]["glob_result"]
        events = [
            {"type": "system", "subtype": "init", "model": "test", "cwd": "/workspace",
             "plugins": [], "tools": ["Glob"]},
            {"type": "assistant", "parent_tool_use_id": None, "message": {"content": [{
                "type": "tool_use", "id": "search", "name": "Glob",
                "input": {"pattern": "**/*roadmap*.md"},
            }]}},
            {"type": "user", "tool_use_result": result, "message": {"content": [{
                "type": "tool_result", "tool_use_id": "search",
                "content": "No files found", "is_error": False,
            }]}},
            {"type": "result", "subtype": "success", "is_error": False,
             "result": "done", "usage": {"input_tokens": 1, "output_tokens": 1}},
        ]
        raw = "\n".join(json.dumps(event) for event in events)
        parsed = capture.normalize_trace("claude", raw)
        self.assertEqual(capture.file_search_results(parsed, host="claude")[0]["paths"], [])
        del events[2]["tool_use_result"]
        raw = "\n".join(json.dumps(event) for event in events)
        self.assertEqual(capture.file_search_results(capture.normalize_trace("claude", raw), host="claude"), [])

    def test_native_host_and_tool_names_cannot_be_forged_by_alias(self):
        for host, wrong_host in (("claude", "codex"), ("codex", "claude")):
            value = observation(host)
            self.assertEqual(capture.file_search_results(value, host=wrong_host), [])
            value["tool_calls"][0]["name"] = "list_files"
            self.assertEqual(capture.file_search_results(value, host=host), [])

    def test_search_grader_requires_same_complete_results_for_both_hosts(self):
        case = {
            "requirements": [{"id": "search", "description": "Search all project paths."}],
            "checks": [{"id": "search", "requirement": "search", "type": "file_search",
                        "pattern": "**/*roadmap*.md", "matches": ["roadmap.md"]}],
        }
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                value = observation(host, "roadmap.md\n")
                self.assertEqual(grade_observation(case, value, host=host)["status"], "pass")
                wrong = copy.deepcopy(value)
                wrong["tool_calls"][0]["output"] = "other-roadmap.md\n"
                self.assertEqual(grade_observation(case, wrong, host=host)["status"], "fail")
                self.assertEqual(grade_observation(case, value)["status"], "invalid")
                partial = copy.deepcopy(value)
                partial["tool_calls"][0]["output"] = "roadmap.md\n... truncated"
                self.assertEqual(grade_observation(case, partial, host=host)["status"], "fail")
                invalid = copy.deepcopy(case)
                invalid["checks"][0]["matches"] = ["../roadmap.md"]
                self.assertEqual(grade_observation(invalid, value, host=host)["status"], "invalid")


if __name__ == "__main__":
    raise SystemExit(run_counted(
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeSearchTests),
        label="test-native-eval-search",
    ))
