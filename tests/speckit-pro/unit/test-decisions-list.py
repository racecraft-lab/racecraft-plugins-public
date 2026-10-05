#!/usr/bin/env python3
"""The runner-owned decisions list: one run-state file of judgments made instead of asking.

The helper is the only writer. Entries come back spec-affecting first, then
authority skips, then notes, each with every field; a malformed entry refuses
the whole batch; the terminal message carries the count and a link only.
"""

import json
import os
from collections.abc import Mapping
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from typing import Any
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO / "speckit-pro"), str(REPO / "tests/speckit-pro/lib")]
from speckit_pro_runner.helpers.registry import MUTATION_HELPERS, dispatch_helper  # noqa: E402
from speckit_pro_runner.trusted_io import resolve_repo_root  # noqa: E402
from test_result import run_counted  # noqa: E402

HELPER_ID = "decisions-list"
WORKFLOW = "specs/001-feature/.process/workflow.md"
LIST_FILE = "specs/001-feature/.process/decisions-list/decisions.json"
TEXT_FIELDS = ("option_chosen", "rejected_alternative", "evidence", "affected_unit")
FIXTURE = REPO / "tests/speckit-pro/unit/fixtures/mutation-helpers/requests" / f"{HELPER_ID}.json"


def entry(kind: str, tag: str) -> dict[str, str]:
    return {"kind": kind, **{name: f"{name} {tag}" for name in TEXT_FIELDS}}


NOTE = entry("readiness_stale", "note")
SKIP = entry("authority_action_skipped", "skip")
SCOPE = entry("scope_answer", "scope")
SPLIT = entry("split_recommendation", "split")
DEFAULT = entry("unratified_default", "default")
PR_PROBLEM = entry("pr_record_problem", "pr")
STOP = entry("unregistered_stop", "stop")
HOOK = entry("optional_hook_run", "hook")


class DecisionsListTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / ".specify").mkdir()
        (self.root / WORKFLOW).parent.mkdir(parents=True)
        (self.root / WORKFLOW).write_text("# Workflow\n", encoding="utf-8")
        previous = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous)

    def call(self, mode: str, **inputs: object) -> dict[str, Any]:
        """Replay the committed request fixture with this test's mode and inputs."""
        document = json.loads(FIXTURE.read_text(encoding="utf-8"))
        document["inputs"] = {**document["inputs"], "workflow_file": WORKFLOW, **inputs}
        request = SimpleNamespace(**{**document, "mode": mode})
        return dispatch_helper(request)

    def append(self, *entries: Mapping[str, object] | str) -> dict[str, Any]:
        return self.call("apply", entries=list(entries))

    def listed(self) -> dict[str, Any]:
        result = self.call("read_only")
        self.assertEqual("ok", result["status"], result)
        return result["data"]

    def test_the_committed_request_fixture_is_served_by_the_registry(self) -> None:
        self.assertIn("read_only", MUTATION_HELPERS[HELPER_ID].modes)
        self.assertEqual(0, self.listed()["count"])

    def test_repo_root_resolution_diagnostics_are_preserved(self) -> None:
        for repo_root in (7, "../outside"):
            with self.subTest(repo_root=repo_root):
                expected = resolve_repo_root({"repo_root": repo_root})
                self.assertIsInstance(expected, dict)
                result = self.call("apply", repo_root=repo_root, entries=[SCOPE])
                self.assertEqual("input_error", result["status"])
                self.assertEqual([expected], result["diagnostics"])
                self.assertFalse((self.root / LIST_FILE).exists())
        with patch("speckit_pro_runner.trusted_io.find_repo_root", return_value=None):
            expected = resolve_repo_root({})
            result = self.call("read_only")
            self.assertEqual("input_error", result["status"])
            self.assertEqual([expected], result["diagnostics"])

    def test_entries_come_back_spec_affecting_then_authority_then_notes(self) -> None:
        first = self.append(NOTE, SKIP, SCOPE, PR_PROBLEM)
        self.assertEqual("ok", first["status"], first)
        self.assertEqual("ok", self.append(SPLIT, DEFAULT, STOP, HOOK)["status"])
        data = self.listed()
        order = [item["kind"] for item in data["entries"]]
        self.assertEqual(
            ["scope_answer", "split_recommendation", "unratified_default", "authority_action_skipped",
             "readiness_stale", "pr_record_problem", "unregistered_stop", "optional_hook_run"], order
        )
        self.assertEqual(8, data["count"])
        for item in data["entries"]:
            self.assertEqual({"seq", "kind", *TEXT_FIELDS}, set(item))
            sent = next(each for each in (NOTE, SKIP, SCOPE, SPLIT, DEFAULT, PR_PROBLEM, STOP, HOOK)
                        if each["kind"] == item["kind"])
            self.assertEqual(sent, {key: value for key, value in item.items() if key != "seq"})

    def test_entries_of_one_class_keep_the_order_they_were_appended(self) -> None:
        self.append(SPLIT)
        self.append(SCOPE)
        kinds = [item["kind"] for item in self.listed()["entries"]]
        self.assertEqual(["split_recommendation", "scope_answer"], kinds)

    def test_apply_response_matches_the_stored_list(self) -> None:
        applied = self.append(SKIP, SCOPE)["data"]
        self.assertEqual(self.listed()["entries"], applied["entries"])

    def test_malformed_entries_are_refused_and_nothing_is_written(self) -> None:
        missing = {key: value for key, value in SCOPE.items() if key != "evidence"}
        malformed = {
            "unknown kind": {**SCOPE, "kind": "vibes"},
            "array kind": {**SCOPE, "kind": []},
            "object kind": {**SCOPE, "kind": {}},
            "missing field": missing,
            "unknown field": {**SCOPE, "mood": "calm"},
            "empty text": {**SCOPE, "evidence": "  "},
            "oversized": {**SCOPE, "evidence": "x" * 1001},
            "non-string": {**SCOPE, "affected_unit": 7},
            "not an object": "scope_answer",
        }
        for label, bad in malformed.items():
            with self.subTest(label):
                result = self.append(NOTE, bad)
                self.assertEqual("input_error", result["status"], result)
                self.assertFalse((self.root / LIST_FILE).exists())
        for label, entries in (("empty batch", []), ("not a list", "x")):
            with self.subTest(label):
                result = self.call("apply", entries=entries)
                self.assertEqual("input_error", result["status"], result)

    def test_a_bad_entry_never_drops_the_good_ones_already_stored(self) -> None:
        self.append(SCOPE)
        self.assertEqual("input_error", self.append({**NOTE, "kind": "vibes"})["status"])
        self.assertEqual(1, self.listed()["count"])

    def test_an_unreadable_stored_list_is_refused_not_replaced(self) -> None:
        target = self.root / LIST_FILE
        target.parent.mkdir(parents=True)
        target.write_text("{not json", encoding="utf-8")
        self.assertEqual("input_error", self.append(SCOPE)["status"])
        self.assertEqual("input_error", self.call("read_only")["status"])
        self.assertEqual("{not json", target.read_text(encoding="utf-8"))

    def test_a_stored_entry_numbered_with_a_non_integer_is_refused(self) -> None:
        self.append(SCOPE)
        target = self.root / LIST_FILE
        target.write_text(target.read_text(encoding="utf-8").replace('"seq": 1', '"seq": true'), encoding="utf-8")
        self.assertEqual("input_error", self.call("read_only")["status"])

    def test_a_stored_non_string_kind_is_refused_not_replaced(self) -> None:
        self.append(SCOPE)
        target = self.root / LIST_FILE
        document = json.loads(target.read_text(encoding="utf-8"))
        for kind in ([], {}):
            with self.subTest(kind=kind):
                document["entries"][0]["kind"] = kind
                original = json.dumps(document)
                target.write_text(original, encoding="utf-8")
                self.assertEqual("input_error", self.call("read_only")["status"])
                self.assertEqual("input_error", self.append(NOTE)["status"])
                self.assertEqual(original, target.read_text(encoding="utf-8"))

    def test_each_repeated_stop_occurrence_is_recorded(self) -> None:
        self.append(STOP)
        self.append(STOP)
        data = self.listed()
        self.assertEqual(2, data["count"])
        self.assertEqual([1, 2], [item["seq"] for item in data["entries"]])

    def test_an_existing_lock_is_refused_without_stealing_it(self) -> None:
        self.append(SCOPE)
        target = self.root / LIST_FILE
        original = target.read_bytes()
        lock = target.with_suffix(".lock")
        lock.mkdir()
        self.assertEqual("input_error", self.append(NOTE)["status"])
        self.assertTrue(lock.is_dir())
        self.assertEqual(original, target.read_bytes())

    def test_dry_run_plans_without_writing(self) -> None:
        result = self.call("dry_run", entries=[SCOPE])
        self.assertEqual("ok", result["status"], result)
        self.assertFalse((self.root / LIST_FILE).exists())

    def test_terminal_message_is_the_count_and_a_link_only(self) -> None:
        self.assertEqual(0, self.listed()["count"])
        self.append(SCOPE, SKIP, NOTE)
        data = self.listed()
        self.assertEqual(LIST_FILE, data["link"])
        self.assertEqual(f"3 decisions recorded: {LIST_FILE}", data["message"])
        for item in data["entries"]:
            for key in TEXT_FIELDS:
                self.assertNotIn(item[key], data["message"])

    def test_the_list_file_stays_out_of_commits(self) -> None:
        self.append(SCOPE)
        ignore = self.root / Path(LIST_FILE).parent / ".gitignore"
        self.assertEqual("*\n", ignore.read_text(encoding="utf-8"))


if __name__ == "__main__":
    sys.exit(
        run_counted(
            unittest.defaultTestLoader.loadTestsFromTestCase(DecisionsListTests),
            label="test-decisions-list",
        )
    )
