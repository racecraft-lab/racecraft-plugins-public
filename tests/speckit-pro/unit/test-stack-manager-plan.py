#!/usr/bin/env python3
"""Optional manager selection must never create PRs or mix recovery paths."""

import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO / "speckit-pro"), str(REPO / "tests/speckit-pro/lib")]
from speckit_pro_runner.helpers import stack_manager
from speckit_pro_runner.helpers.registry import dispatch_helper
from test_result import run_counted


class StackManagerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.skill = self.root / "gh-stack/SKILL.md"
        self.skill.parent.mkdir()
        self.skill.write_text("---\nname: gh-stack\n---\nUse gh stack link with existing PR URLs.\n")
        self.inputs = {"repo_root": str(self.root), "repository": "example/project", "remote": "origin",
                       "skill_path": str(self.skill), "topology": [
                           {"review_order": 1, "slice_id": "first", "branch": "codex/first", "base_branch": "main", "pr_url": "https://github.com/example/project/pull/11"},
                           {"review_order": 2, "slice_id": "second", "branch": "codex/second", "base_branch": "codex/first", "pr_url": "https://github.com/example/project/pull/12"}]}
        self.calls = []

    def probe(self, root, argv):
        self.calls.append(argv)
        output = ""
        if argv == ["gh", "stack", "--version"]:
            output = "gh-stack version 0.1.1"
        elif argv == ["gh", "stack", "link", "--help"]:
            output = "gh stack link <stack-number | branch-or-pr> PR URLs --remote --base"
        elif argv[:3] == ["git", "remote", "get-url"]:
            output = "https://github.com/example/project.git"
        elif argv[:2] == ["git", "rev-parse"]:
            output = "a" * 40
        elif argv[:2] == ["gh", "api"]:
            if "/pulls/" in argv[-1]:
                index = int(argv[-1].rsplit("/", 1)[1]) - 11
                item = self.inputs["topology"][index]
                output = json.dumps({"html_url": item["pr_url"], "number": 11 + index, "state": "open",
                                     "head": {"ref": item["branch"], "sha": "a" * 40, "repo": {"full_name": "example/project"}},
                                     "base": {"ref": item["base_branch"], "repo": {"full_name": "example/project"}}})
            elif "/stacks?" in argv[-1]:
                output = "[]"
            else:
                output = json.dumps({"full_name": "example/project", "archived": False, "fork": False, "permissions": {"push": True}})
        return {"argv": argv, "exit_status": 0, "stdout_tail": output, "stderr_tail": ""}

    def request(self, **changes):
        return dispatch_helper(SimpleNamespace(helper_id="detect-stack-manager-plan", operation="detect-stack-manager-plan",
                                              request_id="manager-test", mode="dry_run", inputs={**self.inputs, **changes}))

    def test_selected_manager_links_verified_urls_and_preserves_packet_creation(self):
        with patch.object(stack_manager, "probe", side_effect=self.probe):
            result = self.request()
        self.assertEqual("ok", result["status"], result)
        decision = result["data"]["decision"]
        self.assertEqual("gh-stack", decision["selected_manager"])
        self.assertTrue(decision["gh_stack"]["skill_available"])
        self.assertEqual(["gh", "stack", "link", "--remote", "origin", "--base", "main", *[x["pr_url"] for x in self.inputs["topology"]]], decision["command_plan"][0]["argv"])
        self.assertFalse(result["data"]["writes_state"])
        self.assertFalse(any("create" in c or "edit" in c or "link" in c and "--help" not in c for c in self.calls))

    def test_missing_either_capability_and_unsupported_version_fall_back(self):
        for unavailable in ("cli", "skill", "version", "repository"):
            with self.subTest(unavailable=unavailable):
                def changed(root, argv):
                    value = self.probe(root, argv)
                    if unavailable == "cli" and argv == ["gh", "stack", "--version"] or unavailable == "repository" and "/stacks?" in argv[-1]:
                        value["exit_status"] = 1
                    if unavailable == "version" and argv == ["gh", "stack", "--version"]:
                        value["stdout_tail"] = "0.99.0"
                    return value
                with patch.object(stack_manager, "probe", side_effect=changed):
                    result = self.request(skill_path=str(self.root / "missing") if unavailable == "skill" else str(self.skill))
                self.assertEqual("explicit-gh", result["data"]["decision"]["selected_manager"])

    def test_operator_fallback_has_no_tool_probes(self):
        with patch.object(stack_manager, "probe", side_effect=AssertionError("no probes")):
            result = self.request(preference="explicit-gh")
        self.assertEqual("explicit-gh", result["data"]["decision"]["selected_manager"])

    def test_invalid_or_incompatible_topology_cannot_select_stack(self):
        topology = copy.deepcopy(self.inputs["topology"])
        topology[1]["base_branch"] = "main"
        with patch.object(stack_manager, "probe", side_effect=self.probe):
            result = self.request(topology=topology)
        self.assertEqual("explicit-gh", result["data"]["decision"]["selected_manager"])
        topology[1]["branch"] = "--upload-pack=bad"
        self.assertEqual("input_error", self.request(topology=topology)["status"])

    def test_missing_prs_plan_validation_only_and_never_create_duplicates(self):
        topology = copy.deepcopy(self.inputs["topology"])
        for row in topology:
            row.pop("pr_url")
        with patch.object(stack_manager, "probe", side_effect=self.probe):
            decision = self.request(topology=topology)["data"]["decision"]
        self.assertEqual("gh-stack", decision["selected_manager"])
        self.assertFalse(any(c["mutates"] for c in decision["command_plan"]))
        self.assertIn("packet", decision["command_plan"][0]["reason"])

    def test_partial_mutation_requires_recorded_manager_recovery(self):
        with patch.object(stack_manager, "probe", side_effect=self.probe):
            previous = self.request()["data"]["decision"]
        previous["mutation_boundary"]["status"] = "partial_mutation_unknown"
        previous["topology"]["post_mutation"] = previous["topology"]["pre_mutation"][:1]
        path = "specs/example/.process/stack-manager-decision.json"
        (self.root / path).parent.mkdir(parents=True)
        (self.root / path).write_text(json.dumps(previous))
        with patch.object(stack_manager, "probe", side_effect=AssertionError("blocked recovery")):
            result = self.request(previous_decision=path, preference="explicit-gh")
        decision = result["data"]["decision"]
        self.assertEqual("blocked", decision["selected_manager"])
        self.assertFalse(decision["fallback_allowed"])
        self.assertEqual("gh-stack", decision["recovery"]["selected_manager"])
        self.assertEqual(previous["topology"]["post_mutation"], decision["recovery"]["observed_post_failure_topology"])


if __name__ == "__main__":
    sys.exit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(StackManagerTests), label="stack-manager-plan"))
