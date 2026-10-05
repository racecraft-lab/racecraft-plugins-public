#!/usr/bin/env python3
"""Optional manager selection must never create PRs or mix recovery paths."""

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO / "speckit-pro"), str(REPO / "tests/speckit-pro/lib")]
from speckit_pro_runner.helpers import archive_sweep, stack_manager
from speckit_pro_runner.helpers.registry import dispatch_helper
from speckit_pro_runner.json_schema import json_schema_failures
from test_result import run_counted


class StackManagerTestCase(unittest.TestCase):
    """Shared staging for the manager selection and recovery tests."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.skill = self.root / ".claude/skills/gh-stack/SKILL.md"
        self.skill.parent.mkdir(parents=True)
        self.skill.write_text("---\nname: gh-stack\n---\nUse gh stack link with existing PR URLs.\n")
        self.skill_digest = hashlib.sha256(self.skill.read_bytes()).hexdigest()
        self.original_skill_paths = stack_manager.TRUSTED_SKILL_PATHS
        self.original_skill_digest = stack_manager.SKILL_SHA256
        stack_manager.TRUSTED_SKILL_PATHS = (self.skill.resolve(),)
        stack_manager.SKILL_SHA256 = self.skill_digest
        self.addCleanup(setattr, stack_manager, "TRUSTED_SKILL_PATHS", self.original_skill_paths)
        self.addCleanup(setattr, stack_manager, "SKILL_SHA256", self.original_skill_digest)
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



class StackManagerTests(StackManagerTestCase):
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

    def test_repository_local_skill_is_not_trusted(self):
        local = self.root / "gh-stack/SKILL.md"
        local.parent.mkdir()
        local.write_text(self.skill.read_text())
        with patch.object(stack_manager, "probe", side_effect=self.probe):
            result = self.request(skill_path=str(local))
        self.assertEqual("explicit-gh", result["data"]["decision"]["selected_manager"])
        self.assertFalse(result["data"]["decision"]["gh_stack"]["skill_available"])

    def test_codex_user_skill_roots_trust_primary_and_legacy_paths(self):
        home = Path.home()
        self.assertEqual(
            (home / ".claude/skills", home / ".agents/skills", home / ".codex/skills"),
            stack_manager.TRUSTED_SKILL_PARENTS,
        )
        self.assertIn(home / ".agents/skills/gh-stack/SKILL.md", self.original_skill_paths)
        self.assertIn(home / ".codex/skills/gh-stack/SKILL.md", self.original_skill_paths)

    def test_tampered_skill_digest_falls_back(self):
        self.skill.write_text(self.skill.read_text() + "tampered\n")
        with patch.object(stack_manager, "probe", side_effect=self.probe):
            result = self.request()
        self.assertEqual("explicit-gh", result["data"]["decision"]["selected_manager"])
        self.assertFalse(result["data"]["decision"]["gh_stack"]["skill_available"])

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



class StackManagerRecoveryTests(StackManagerTestCase):
    def partial_mutation_path(self):
        with patch.object(stack_manager, "probe", side_effect=self.probe):
            previous = self.request()["data"]["decision"]
        previous["mutation_boundary"]["status"] = "partial_mutation_unknown"
        previous["topology"]["post_mutation"] = previous["topology"]["pre_mutation"][:1]
        path = "specs/example/.process/stack-manager-decision.json"
        (self.root / path).parent.mkdir(parents=True)
        (self.root / path).write_text(json.dumps(previous))
        return path

    def test_reverified_partial_mutation_retries_the_existing_pr_link(self):
        path = self.partial_mutation_path()
        self.calls.clear()
        with patch.object(stack_manager, "probe", side_effect=self.probe):
            result = self.request(previous_decision=path, preference="explicit-gh", reverify_recovery=True)
        self.assertEqual("ok", result["status"], result)
        decision = result["data"]["decision"]
        blocked = self.request(previous_decision=path)["data"]["decision"]
        self.assertEqual("gh-stack", decision["selected_manager"])
        self.assertEqual(blocked["recovery"], decision["recovery"])
        self.assertFalse(decision["fallback_allowed"])
        self.assertEqual(blocked["mutation_boundary"], decision["mutation_boundary"])
        self.assertEqual("partial_mutation_unknown", decision["mutation_boundary"]["status"])
        plan = decision["command_plan"][0]
        self.assertEqual(("link-stack", True), (plan["id"], plan["mutates"]))
        self.assertEqual([x["pr_url"] for x in self.inputs["topology"]], plan["argv"][-2:])
        self.assertFalse(any("create" in c or "edit" in c for c in self.calls))

    def test_recovery_stays_blocked_when_the_prs_no_longer_verify(self):
        path = self.partial_mutation_path()

        def drifted(root, argv):
            result = self.probe(root, argv)
            if argv[:2] == ["gh", "api"] and "/pulls/" in argv[-1]:
                body = json.loads(result["stdout_tail"])
                body["head"]["sha"] = "b" * 40
                result["stdout_tail"] = json.dumps(body)
            return result

        with patch.object(stack_manager, "probe", side_effect=drifted):
            decision = self.request(previous_decision=path, reverify_recovery=True)["data"]["decision"]
        self.assertEqual("blocked", decision["selected_manager"])
        self.assertFalse(decision["fallback_allowed"])
        self.assertEqual("gh-stack", decision["recovery"]["selected_manager"])

    def test_recovery_stays_blocked_when_a_slice_has_no_pr_identity(self):
        path = self.partial_mutation_path()
        record = json.loads((self.root / path).read_text())
        record["topology"]["pre_mutation"][1].pop("pr_url")
        (self.root / path).write_text(json.dumps(record))
        with patch.object(stack_manager, "probe", side_effect=self.probe):
            decision = self.request(previous_decision=path, reverify_recovery=True)["data"]["decision"]
        self.assertEqual("blocked", decision["selected_manager"])


class DecisionContractTests(StackManagerTestCase):
    """Every decision the helper returns fits the shipped schema and says why a manager was not qualified."""

    SCHEMA = json.loads((REPO / "speckit-pro/skills/speckit-autopilot/contracts/stack-manager-decision.schema.json")
                        .read_text(encoding="utf-8"))

    def decision(self, **changes):
        with patch.object(stack_manager, "probe", side_effect=self.probe):
            return self.request(**changes)["data"]["decision"]

    def test_every_decision_satisfies_the_shipped_schema(self):
        path = StackManagerRecoveryTests.partial_mutation_path(self)
        untrusted = self.root / "gh-stack/SKILL.md"
        untrusted.parent.mkdir()
        untrusted.write_text(self.skill.read_text())
        decisions = {"auto": self.decision(), "operator": self.decision(preference="explicit-gh"),
                     "untrusted": self.decision(skill_path=str(untrusted)),
                     "blocked": self.decision(previous_decision=path),
                     "retry": self.decision(previous_decision=path, reverify_recovery=True)}
        for name, decision in decisions.items():
            with self.subTest(decision=name):
                self.assertEqual(json_schema_failures(decision, self.SCHEMA, self.SCHEMA, "decision"), [])

    def test_support_status_names_why_the_skill_did_not_qualify(self):
        untrusted = self.root / "gh-stack/SKILL.md"
        untrusted.parent.mkdir()
        untrusted.write_text(self.skill.read_text())
        self.assertEqual("untrusted_skill", self.decision(skill_path=str(untrusted))["gh_stack"]["support_status"])
        self.assertEqual("operator_preference", self.decision(preference="explicit-gh")["gh_stack"]["support_status"])
        self.assertEqual("missing", self.decision(skill_path=str(self.root / "absent/SKILL.md"))["gh_stack"]["support_status"])
        self.skill.write_text(self.skill.read_text() + "changed\n")
        self.assertEqual("skill_mismatch", self.decision()["gh_stack"]["support_status"])


class SkillPinTests(unittest.TestCase):
    """The pinned gh-stack digest is the committed copy of github/gh-stack's MIT-licensed SKILL.md.

    The fixture holds the bytes `gh skill install github/gh-stack gh-stack --scope user` writes for the
    qualified tag, so a stale pin fails here instead of silently selecting explicit-gh in every run.
    """

    FIXTURE = REPO / "tests/speckit-pro/unit/fixtures/stack-manager/gh-stack-SKILL.md"
    GUIDE = REPO / "speckit-pro/skills/speckit-autopilot/references/stack-manager.md"

    def test_the_pin_is_the_committed_copy_of_the_qualified_tag(self):
        body = self.FIXTURE.read_bytes()
        self.assertEqual(stack_manager.SKILL_SHA256, hashlib.sha256(body).hexdigest())
        self.assertIn(f"github-ref: refs/tags/v{stack_manager.QUALIFIED_VERSION}\n", body.decode("utf-8"))

    def test_the_guidance_states_the_pin_and_its_trusted_roots(self):
        guide = self.GUIDE.read_text(encoding="utf-8")
        for fact in (stack_manager.SKILL_SHA256, stack_manager.QUALIFIED_VERSION,
                     "~/.claude/skills", "~/.agents/skills", "~/.codex/skills"):
            with self.subTest(fact=fact):
                self.assertIn(fact, guide)


class BoundedProbeTests(unittest.TestCase):
    """Both helpers share one gh/git probe: fixed argv, a per-caller allowlist and timeout, one record shape."""

    KEYS = {"argv", "exit_status", "stdout_tail", "stderr_tail"}

    def run_probe(self, module, argv, run):
        with tempfile.TemporaryDirectory() as root, patch("subprocess.run", side_effect=run) as call:
            return module.probe(Path(root), argv), call

    def test_an_unlisted_cli_is_reported_and_never_started(self):
        for module, argv in ((stack_manager, ["curl", "https://example.invalid"]), (archive_sweep, ["git", "status"])):
            with self.subTest(module=module.__name__):
                record, call = self.run_probe(module, argv, AssertionError("must not run"))
                self.assertEqual(set(record), self.KEYS)
                self.assertEqual((record["exit_status"], record["stdout_tail"]), (None, ""))
                self.assertIn("may run here", record["stderr_tail"])
                call.assert_not_called()

    def test_a_timeout_is_reported_with_the_callers_own_limit(self):
        for module, limit in ((stack_manager, 20), (archive_sweep, 30)):
            with self.subTest(module=module.__name__):
                record, call = self.run_probe(module, ["gh", "api", "user"], subprocess.TimeoutExpired("gh", limit))
                self.assertEqual(set(record), self.KEYS)
                self.assertEqual(record["exit_status"], None)
                self.assertIn("timed out", record["stderr_tail"])
                self.assertEqual(call.call_args.kwargs["timeout"], limit)
                self.assertEqual(call.call_args.args[0], ["gh", "api", "user"])

    def test_a_finished_run_keeps_the_exit_status_and_trims_the_output(self):
        done = subprocess.CompletedProcess(["git"], 1, stdout=" out \n", stderr="x" * 5000)
        record, call = self.run_probe(stack_manager, ["git", "rev-parse", "HEAD"], [done])
        self.assertEqual(record, {"argv": ["git", "rev-parse", "HEAD"], "exit_status": 1, "stdout_tail": "out",
                                  "stderr_tail": "x" * 2048})
        self.assertFalse(call.call_args.kwargs["shell"])

    def test_docker_stdout_is_capped_like_stderr(self):
        from speckit_pro_runner import cli_probe
        done = subprocess.CompletedProcess(["docker"], 0, stdout="x" * 5000 + "tail", stderr="x" * 5000)
        with tempfile.TemporaryDirectory() as root, patch("subprocess.run", return_value=done):
            record = cli_probe.probe(Path(root), ["docker", "info"], allowed=("docker",), timeout=10)
        self.assertIsNone(record["exit_status"])
        self.assertEqual("x" * 2044 + "tail", record["stdout_tail"])
        self.assertIn("stdout exceeded", record["stderr_tail"])

    def test_complete_github_json_survives_the_stdout_limit(self):
        document = {"full_name": "example/project", "description": "x" * 9000}
        done = subprocess.CompletedProcess(["gh"], 0, stdout=json.dumps(document), stderr="")
        record, _ = self.run_probe(stack_manager, ["gh", "api", "repos/example/project"], [done])
        self.assertEqual(document, json.loads(record["stdout_tail"]))

    def test_github_stdout_over_the_limit_is_reported_as_a_failed_probe(self):
        done = subprocess.CompletedProcess(["gh"], 0, stdout="x" * (1048576 + 1), stderr="y" * 5000)
        record, _ = self.run_probe(stack_manager, ["gh", "api", "repos/example/project"], [done])
        self.assertIsNone(record["exit_status"])
        self.assertEqual(1048576, len(record["stdout_tail"]))
        self.assertIn("stdout exceeded", record["stderr_tail"])


if __name__ == "__main__":
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite([loader.loadTestsFromTestCase(StackManagerTests),
                                loader.loadTestsFromTestCase(StackManagerRecoveryTests),
                                loader.loadTestsFromTestCase(BoundedProbeTests),
                                loader.loadTestsFromTestCase(DecisionContractTests),
                                loader.loadTestsFromTestCase(SkillPinTests)])
    sys.exit(run_counted(suite, label="test-stack-manager-plan"))
