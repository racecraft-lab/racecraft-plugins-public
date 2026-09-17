#!/usr/bin/env python3
"""Freeze the single permitted trigger behavior difference without providers."""
from __future__ import annotations

import ast
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest import mock

TESTS = Path(__file__).resolve().parents[1]
LAYER = TESTS / "layer2-trigger"
sys.path.insert(0, str(TESTS / "lib"))
from test_result import run_counted


class ControlledDescriptionTests(unittest.TestCase):
    def test_frozen_arm_bytes_and_provenance(self):
        manifest = json.loads((LAYER / "controlled-descriptions.json").read_text())
        self.assertEqual(manifest["baseline_ref"], "01dc73d40305109e81dff0c9c21a3d4b5e9b1fcd")
        expected = {
            "baseline": "49efb809edca1849750ecffdc59ae78c64f0b3f23c469b2e38f7572c74bd1844",
            "candidate": "a4572888c5e2ccbc1d052be89ec4dde453ab3d09c3630006523a07aba43c21e8",
        }
        for arm, digest in expected.items():
            with self.subTest(arm=arm):
                reference = manifest["files"][arm]
                payload = (LAYER / reference["path"]).read_bytes()
                self.assertEqual(hashlib.sha256(payload).hexdigest(), digest)
                self.assertEqual(reference["sha256"], digest)
                self.assertEqual(payload.decode(), manifest[arm] + "\n")
        self.assertNotEqual(manifest["baseline"], manifest["candidate"])
        self.assertFalse(manifest["launch_authorized"])
        self.assertEqual(manifest["native_qualification"], "pending")

    def test_setup_failures_do_not_leak_description_into_next_invocation(self):
        cases = (
            ("run-trigger-evals.py", "temporary-directory"),
            ("run-trigger-evals.py", "siblings"),
            ("run-trigger-evals.py", "handlers"),
            ("run_codex_evals.py", "temporary-directory"),
            ("run_codex_evals.py", "existing-evidence"),
            ("run_codex_evals.py", "handlers"),
        )
        manifest = json.loads((LAYER / "controlled-descriptions.json").read_text())
        override = str(LAYER / manifest["files"]["baseline"]["path"])
        for filename, failure in cases:
            with self.subTest(host=filename, failure=failure), tempfile.TemporaryDirectory() as temporary:
                main = runpy.run_path(str(LAYER / filename))["main"]
                state = main.__globals__
                original = state["NO_SPECKIT_SKILL_DESCRIPTION"]
                argv = ["speckit-coach", "--no-op-description-file", override]
                with ExitStack() as patches:
                    patches.enter_context(mock.patch.object(state["shutil"], "which", return_value="/stub/provider"))
                    process = patches.enter_context(mock.patch.object(state["subprocess"], "Popen", side_effect=AssertionError("provider launch forbidden")))
                    if failure == "existing-evidence":
                        argv += ["--evidence-dir", temporary]
                    elif failure == "temporary-directory":
                        patches.enter_context(mock.patch.object(state["tempfile"], "mkdtemp", side_effect=OSError("setup failure")))
                    else:
                        patches.enter_context(mock.patch.object(state["tempfile"], "mkdtemp", return_value=temporary))
                        target = "sibling_skill_dirs" if failure == "siblings" else "install_termination_handlers"
                        replacement = mock.Mock(side_effect=OSError("setup failure"))
                        patches.enter_context(mock.patch.dict(state, {target: replacement}) if filename == "run-trigger-evals.py"
                                              else mock.patch.object(state["processes"], target, replacement))
                    patches.enter_context(mock.patch.object(sys, "argv", [filename, *argv]))
                    with self.assertRaises(OSError):
                        main(argv) if filename == "run-trigger-evals.py" else main()
                    process.assert_not_called()
                    self.assertEqual(state["NO_SPECKIT_SKILL_DESCRIPTION"], original)
                    self.assertEqual(state["evidence_records"].description_override(None, state["NO_SPECKIT_SKILL_DESCRIPTION"]), original)

    def test_both_current_hosts_use_the_approved_candidate(self):
        manifest = json.loads((LAYER / "controlled-descriptions.json").read_text())
        for path in manifest["source_paths"]:
            with self.subTest(path=path):
                tree = ast.parse((TESTS.parents[1] / path).read_text())
                values = [ast.literal_eval(node.value) for node in tree.body
                          if isinstance(node, ast.Assign)
                          and any(isinstance(target, ast.Name)
                                  and target.id == manifest["symbol"] for target in node.targets)]
                self.assertEqual(values, [manifest["candidate"]])


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(ControlledDescriptionTests), label="test-trigger-controlled-description"))
