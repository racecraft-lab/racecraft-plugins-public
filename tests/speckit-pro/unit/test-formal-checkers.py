#!/usr/bin/env python3
"""Deterministic contracts plus explicitly requested native checker qualification."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
sys.path[:0] = [str(PLUGIN_ROOT), str(REPO_ROOT / "tests/speckit-pro/lib")]

from speckit_pro_runner.formal import apalache, catalog, engine, helper
from speckit_pro_runner.formal.evidence import read_checkpoint, record_path
from speckit_pro_runner.formal.process import run_process, start_process
from speckit_pro_runner.helpers.registry import dispatch_helper
from speckit_pro_runner.helpers.read_only import resolve_autopilot_stage, validate_gate
from test_result import run_counted

JAR: str | None = None


class FormalCheckerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.selection = {"schema_version": "1.0", "status": "enabled", "rationale": "Counter rule", "models": [
            {"id": "counter", "behavior": "Stay within the limit", "origin": "new", "evidence": "model"}]}
        self.workflow()
        (self.root / "spec.md").write_text("# Spec\nThe count never exceeds the limit.\n")
        (self.root / "plan.md").write_text("# Plan\nIncrement until the limit.\n")
        source = PLUGIN_ROOT / "skills/speckit-coach/examples/formal/counter"
        shutil.copytree(source, self.root / "formal/counter")
        self.model = {"checker": "apalache", "module": "formal/counter/Counter.tla", "config": "formal/counter/Counter.cfg",
                      "inputs": ["formal/counter/Counter.tla", "formal/counter/Counter.cfg"],
                      "properties": {"Bounded": {"kind": "invariant", "requirement": "FR1"}}, "assumptions": ["Limit = 2"],
                      "mode": "bounded", "init": "Init", "next": "Next", "bounds": {"length": 5},
                      "budget": {"timeout_seconds": 20, "output_bytes": 1048576}}
        self.tool = {"version": "0.62.2", "jar": ".specify/tools/apalache.jar", "sha256": "0" * 64, "java": "java", "heap_mb": 4096}
        self.save_catalog()

    def workflow(self) -> None:
        (self.root / "workflow.md").write_text("# Workflow\n\n## Formal Methods\n\n```json\n" + json.dumps(self.selection) + "\n```\n")

    def save_catalog(self) -> None:
        target = self.root / catalog.CATALOG_PATH
        target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps({"schema_version": "1.0", "tools": {"apalache": self.tool}, "models": {"counter": self.model}}))

    def request(self, mode: str = "dry_run", name: str = "formal-check", **inputs) -> dict:
        args = {"repo_root": str(self.root), "workflow_file": "workflow.md", "spec_file": "spec.md", "plan_file": "plan.md", **inputs}
        return dispatch_helper(SimpleNamespace(helper_id=name, operation=name, mode=mode, request_id="formal-test", inputs=args))

    def passed_model(self, root, model_id, item) -> dict:
        return {"model": model_id, "verdict": "pass", "obligations": [
            {"id": obligation["id"], "verdict": "pass", "exit_code": 0} for obligation in apalache.obligations(item["model"])]}

    def test_disabled_selection_does_not_inspect_or_install_tools(self) -> None:
        self.selection.update(status="none", models=[])
        self.workflow()
        with patch.object(helper, "inspect_tool", side_effect=AssertionError("tool probe forbidden")):
            self.assertEqual("disabled", self.request("apply")["data"]["verdict"])
        self.assertFalse((self.root / catalog.RUNS_PATH).exists())
        self.assertFalse((self.root / catalog.EVIDENCE_PATH).exists())

    def test_pending_new_and_missing_existing_are_distinct(self) -> None:
        (self.root / catalog.CATALOG_PATH).unlink()
        self.assertEqual("pending_authoring", self.request("read_only", "formal-doctor")["data"]["verdict"])
        self.assertEqual("missing_prerequisite", self.request("apply")["status"])
        self.selection["models"][0]["origin"] = "existing"
        self.workflow()
        self.assertEqual("expected_failure", self.request("read_only", "formal-doctor")["status"])

    def test_preview_is_read_only_and_gate_evidence_is_content_bound(self) -> None:
        with patch.object(engine.shutil, "which", return_value=sys.executable), patch.object(helper, "inspect_tool", return_value={"version": "0.62.2", "sha256": "fixture"}), patch.object(helper, "execute_model", side_effect=self.passed_model):
            before = sorted(p.relative_to(self.root) for p in self.root.rglob("*"))
            preview = self.request()
            self.assertEqual("preview", preview["data"]["verdict"])
            self.assertEqual(before, sorted(p.relative_to(self.root) for p in self.root.rglob("*")))
            checked = self.request("apply")
            self.assertEqual("pass", checked["data"]["verdict"])
            self.assertIn("formal/counter/Counter.cfg", checked["data"]["commit_paths"])
            self.assertTrue(helper.current_checkpoint(self.root, "workflow.md")["complete"])
            (self.root / "plan.md").write_text("# Plan\nChanged design\n")
            self.assertEqual("stale", helper.current_checkpoint(self.root, "workflow.md")["verdict"])

    def test_missing_config_and_archival_or_escape_paths_block(self) -> None:
        for path in ("../escape.tla", "specs/feature/model.tla", ".specify/formal-runs/model.tla"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                catalog.confined(self.root, path, durable=True)
        (self.root / self.model["config"]).unlink()
        self.assertEqual("pending_authoring", self.request()["data"]["verdict"])

    def test_typecheck_only_and_incomplete_induction_cannot_pass(self) -> None:
        self.model.update(mode="inductive", bounds={"inductive_invariant": "Bounded"})
        self.save_catalog()
        with patch.object(engine.shutil, "which", return_value=sys.executable), patch.object(helper, "inspect_tool", return_value={"version": "fixture"}), patch.object(helper, "execute_model", side_effect=self.passed_model):
            self.assertEqual("pass", self.request("apply")["data"]["verdict"])
            record = read_checkpoint(self.root, "workflow.md")
            self.assertEqual(["base", "step", "consequence"], [c["id"] for c in record["results"][0]["obligations"]])
            record["results"][0]["obligations"].pop()
            record_path(self.root, "workflow.md", "plan").write_text(json.dumps(record))
            self.assertFalse(helper.current_checkpoint(self.root, "workflow.md")["complete"])
        result = {"output": "Type checking passed\nEXITCODE: OK", "exit_code": 0, "timed_out": False, "output_limited": False}
        self.assertEqual("inconclusive", apalache.verdict(result))

    def test_all_resume_forms_and_g3_require_current_selected_checks(self) -> None:
        overview = "\n## Workflow Overview\n\n| Phase | Prompts | Status |\n|---|---|---|\n"
        overview += "\n".join(f"| {phase} | 1 | Complete |" for phase in ("Specify", "Clarify", "Plan", "Checklist", "Tasks", "Analyze", "Confidence Gate")) + "\n"
        with (self.root / "workflow.md").open("a") as stream:
            stream.write(overview)
        with patch.object(engine.shutil, "which", return_value=sys.executable), patch.object(helper, "inspect_tool", return_value={"version": "fixture"}), patch.object(helper, "execute_model", side_effect=self.passed_model):
            for args in (["--stage", "implement"], ["--from-phase", "implement"], ["--from-phase", "tasks"],
                         ["--stage", "full", "--from-phase", "implement"], ["--stage", "implement", "--advisory"]):
                with self.subTest(args=args):
                    result = resolve_autopilot_stage({"workflow_file": "workflow.md", "autopilot_args": args}, self.root)
                    self.assertEqual(2, result["exit_code"])
                    self.assertIn("--from-phase plan", result["stderr"])
            auto = resolve_autopilot_stage({"workflow_file": "workflow.md"}, self.root)
            self.assertEqual("plan", json.loads(auto["stdout"])["stage"])
            path = self.root / "workflow.md"
            finished = path.read_text()
            path.write_text(finished.replace("| Specify | 1 | Complete |", "| Specify | 1 | Pending |"))
            early = resolve_autopilot_stage({"workflow_file": "workflow.md"}, self.root)
            self.assertIsNone(json.loads(early["stdout"])["from_phase"])
            path.write_text(finished)
            gate = {"gate": "G3", "feature_dir": ".", "workflow_file": "workflow.md"}
            self.assertEqual(1, validate_gate(gate, self.root)["exit_code"])
            self.assertEqual("pass", self.request("apply")["data"]["verdict"])
            self.assertEqual(0, validate_gate(gate, self.root)["exit_code"])
            ready = resolve_autopilot_stage({"workflow_file": "workflow.md"}, self.root)
            self.assertEqual("implement", json.loads(ready["stdout"])["stage"])
            (self.root / "spec.md").write_text("A changed requirement\n")
            stale = resolve_autopilot_stage({"workflow_file": "workflow.md", "autopilot_args": ["--stage", "implement"]}, self.root)
            self.assertEqual(2, stale["exit_code"])

    def test_process_timeout_and_output_budget(self) -> None:
        with self.assertRaises(ValueError):
            start_process(["/bin/sh", "-c", "exit 0"], self.root, {})
        timed = run_process([sys.executable, "-c", "import time; time.sleep(3)"], self.root, self.root / "timeout.log", 1, 4096)
        self.assertEqual("timeout", apalache.verdict(timed))
        noisy = run_process([sys.executable, "-c", "print('X' * 20000)"], self.root, self.root / "output.log", 5, 4096)
        self.assertEqual("inconclusive", apalache.verdict(noisy))
        self.assertLessEqual((self.root / "output.log").stat().st_size, 4096)

    def test_unknown_settings_and_missing_tools_are_actionable(self) -> None:
        self.assertEqual("input_error", self.request("read_only", "formal-doctor", skip_and_log=True)["status"])
        self.assertEqual("missing_tool", self.request("read_only", "formal-doctor")["data"]["verdict"])
        self.tool["version"] = "0.1.0"
        self.save_catalog()
        self.assertEqual("version_mismatch", self.request()["data"]["verdict"])

    def test_missing_java_during_preview_is_an_expected_failure_without_writes(self) -> None:
        with patch.object(helper, "inspect_tool", return_value={"version": "fixture"}), patch.object(engine.shutil, "which", return_value=None):
            result = self.request("apply")
        self.assertEqual("expected_failure", result["status"])
        self.assertEqual("missing_tool", result["data"]["verdict"])
        self.assertFalse(result["data"]["writes_state"])
        self.assertFalse((self.root / catalog.EVIDENCE_PATH).exists())

    def test_apply_validation_errors_report_no_writes(self) -> None:
        for inputs in ({"unknown": True}, {"checkpoint": "invalid"}, {"spec_file": "missing.md"}):
            with self.subTest(inputs=inputs), patch.object(helper, "inspect_tool", return_value={"version": "fixture"}):
                result = self.request("apply", **inputs)
                self.assertEqual("input_error", result["status"])
                self.assertFalse(result["data"]["writes_state"])
                self.assertFalse((self.root / catalog.EVIDENCE_PATH).exists())

    def test_interrupted_workflow_write_reports_the_saved_record(self) -> None:
        with (self.root / "workflow.md").open("a") as stream:
            stream.write("\n## Formal Checkpoints\n\n## Formal Checkpoints\n")
        with patch.object(engine.shutil, "which", return_value=sys.executable), patch.object(helper, "inspect_tool", return_value={"version": "fixture"}):
            result = self.request("apply")
        self.assertEqual("input_error", result["status"])
        self.assertTrue(result["data"]["writes_state"])
        self.assertEqual("running", read_checkpoint(self.root, "workflow.md")["verdict"])

    def test_catalog_cannot_approve_a_replacement_distribution(self) -> None:
        jar = self.root / "replacement.jar"
        with zipfile.ZipFile(jar, "w") as archive:
            archive.writestr("META-INF/MANIFEST.MF", "Implementation-Version: 0.62.2\n\n")
        tool = {**self.tool, "jar": str(jar), "sha256": catalog.digest(jar)}
        with patch.object(engine.shutil, "which", return_value=sys.executable), patch.object(engine.subprocess, "run") as launch:
            with self.assertRaises(catalog.FormalError) as caught:
                engine.inspect_tool(self.root, tool, "apalache")
            self.assertEqual("version_mismatch", caught.exception.verdict)
            launch.assert_not_called()
            with self.assertRaises(catalog.FormalError):
                engine.execute_model(self.root, "counter", {"model": self.model, "tool": tool})
        self.assertFalse((self.root / catalog.RUNS_PATH).exists())

    def test_native_config_cannot_silently_override_or_drop_obligations(self) -> None:
        path = self.root / self.model["config"]
        for config, expected in (("SPECIFICATION Spec", "unsupported"), ("INIT Init\nNEXT Wrong", "invalid_model"),
                                 ("INIT Init\nNEXT Next\nCONSTRAINT Smaller", "unsupported"),
                                 ("INIT Init\nNEXT Next\nINVARIANT Different", "invalid_model")):
            with self.subTest(config=config):
                path.write_text(config)
                self.assertEqual(expected, self.request()["data"]["verdict"])


class NativeApalacheTests(FormalCheckerTests):
    def setUp(self) -> None:
        super().setUp()
        assert JAR is not None
        self.tool.update(jar=JAR, sha256=catalog.digest(Path(JAR)))
        self.save_catalog()

    def test_native_pass_and_seeded_violation(self) -> None:
        passing = self.request("apply")
        self.assertEqual("pass", passing["data"]["verdict"], passing)
        path = self.root / self.model["module"]
        path.write_text(path.read_text().replace("count <= Limit", "count < Limit"))
        failing = self.request("apply")
        self.assertEqual("violation", failing["data"]["verdict"], failing)

    def test_native_errors_and_deadlock(self) -> None:
        path = self.root / self.model["module"]
        original = path.read_text()
        cases = (
            ("syntax", "invalid_model", original.replace("Init == count = 0", "Init == )")),
            ("type", "invalid_model", original.replace("Init == count = 0", 'Init == count = "zero"')),
            ("enabled", "unsupported", original.replace("Bounded == count >= 0 /\\ count <= Limit", "Bounded == ENABLED (count' = count + 1)")),
            ("deadlock", "violation", original.replace("IF count < Limit THEN count' = count + 1 ELSE UNCHANGED count", "count < Limit /\\ count' = count + 1")),
        )
        for label, expected, content in cases:
            with self.subTest(case=label):
                path.write_text(content)
                result = self.request("apply")
                self.assertEqual(expected, result["data"]["verdict"], result)

    def test_native_induction_requires_base_step_and_consequence(self) -> None:
        path = self.root / self.model["module"]
        path.write_text(path.read_text().replace("Spec ==", "Inductive == count \\in Int /\\ Bounded\nSpec =="))
        self.model.update(mode="inductive", bounds={"inductive_invariant": "Inductive"})
        self.save_catalog()
        passing = self.request("apply")
        self.assertEqual("pass", passing["data"]["verdict"], passing)
        path.write_text(path.read_text().replace("Bounded ==", "Strengthening == count \\in Int /\\ count >= 0\nBounded =="))
        self.model["bounds"]["inductive_invariant"] = "Strengthening"
        self.save_catalog()
        failing = self.request("apply")
        self.assertEqual("violation", failing["data"]["verdict"], failing)
        self.assertEqual(["pass", "pass", "violation"], [o["verdict"] for o in failing["data"]["results"][0]["obligations"]])

    def test_native_temporal_property_and_unsupported_fairness(self) -> None:
        path = self.root / self.model["module"]
        original = path.read_text()
        path.write_text(original.replace("Spec ==", "Progress == []<>(count = Limit)\nSpec =="))
        self.model.update(mode="temporal", properties={"Progress": {"kind": "temporal", "requirement": "FR2"}})
        (self.root / self.model["config"]).write_text("CONSTANT Limit = 2\nINIT Init\nNEXT Next\nPROPERTY Progress\n")
        self.save_catalog()
        passing = self.request("apply")
        self.assertEqual("pass", passing["data"]["verdict"], passing)
        path.write_text(original.replace("Spec ==", "Progress == WF_count(Next) => <>(count = Limit)\nSpec =="))
        unsupported = self.request("apply")
        self.assertEqual("unsupported", unsupported["data"]["verdict"], unsupported)

    def test_native_timeout_and_wrong_checksum_do_not_pass(self) -> None:
        self.model["bounds"]["length"] = 10000
        self.model["budget"]["timeout_seconds"] = 1
        self.save_catalog()
        self.assertEqual("timeout", self.request("apply")["data"]["verdict"])
        self.tool["sha256"] = "0" * 64
        self.save_catalog()
        self.assertEqual("version_mismatch", self.request("read_only", "formal-doctor")["data"]["verdict"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apalache-jar")
    args = parser.parse_args()
    JAR = str(Path(args.apalache_jar).resolve()) if args.apalache_jar else None
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(FormalCheckerTests)
    if JAR:
        for name in unittest.defaultTestLoader.getTestCaseNames(NativeApalacheTests):
            if name.startswith("test_native_"):
                suite.addTest(NativeApalacheTests(name))
    raise SystemExit(run_counted(suite, label="test-formal-checkers"))
