#!/usr/bin/env python3
"""Unit tests for the manifest-driven run-all.py orchestrator.

Exercises the manifest-driven flag/scope/headline/exit-code contract that
reproduces the runner interface: argument parsing (including unknown
flags -> exit 2), per-layer scope selection from suite-manifest.json, the
summary-line parser, the ``speckit-pro test suite: X/Y passed`` headline
formatting, and the child-outcome disposition taxonomy (crash, failed exit,
missing child, and no-summary pass).

The hyphenated ``run-all.py`` is loaded via importlib. Prints the house
``test-run-all: {passed}/{total} passed`` summary.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import test_result  # noqa: E402


def _load_run_all():
    path = REPO_ROOT / "tests" / "speckit-pro" / "run-all.py"
    spec = importlib.util.spec_from_file_location("run_all", path)
    module = importlib.util.module_from_spec(spec)
    # Register before exec so the @dataclass in run-all.py can resolve its
    # string annotations (from __future__ import annotations) via sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


run_all = _load_run_all()


class ArgParsingTests(unittest.TestCase):
    def test_default_config_runs_deterministic_layers(self) -> None:
        config = run_all.parse_args([])
        self.assertFalse(config.live)
        self.assertFalse(config.run_all)
        self.assertIsNone(config.run_layer)
        self.assertFalse(config.verbose)

    def test_all_flag_enables_live_and_all(self) -> None:
        config = run_all.parse_args(["--all"])
        self.assertTrue(config.run_all)
        self.assertTrue(config.live)

    def test_integration_flag_selects_layer_seven(self) -> None:
        config = run_all.parse_args(["--integration"])
        self.assertEqual(config.run_layer, "7")

    def test_layer_and_live_and_verbose_flags(self) -> None:
        config = run_all.parse_args(["--layer", "4", "--live", "--verbose"])
        self.assertEqual(config.run_layer, "4")
        self.assertTrue(config.live)
        self.assertTrue(config.verbose)

    def test_unknown_flag_raises_usage_error(self) -> None:
        with self.assertRaises(run_all.UsageError):
            run_all.parse_args(["--bogus"])


class ScopeSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = run_all.load_manifest(REPO_ROOT)
        self.by_id = {layer["id"]: layer for layer in self.manifest["layers"]}

    def _runs(self, config):
        return {
            layer["id"]
            for layer in self.manifest["layers"]
            if layer["id"] != "toolchain" and run_all.layer_should_run(layer, config)
        }

    def _ordered_runs(self, config):
        return [layer["id"] for layer in run_all.execution_layers(self.manifest) if run_all.layer_should_run(layer, config)]

    def test_default_runs_only_1_4_5(self) -> None:
        self.assertEqual(self._runs(run_all.parse_args([])), {"1", "4", "5"})

    def test_live_preserves_default_1_4_5_scope(self) -> None:
        self.assertEqual(self._ordered_runs(run_all.parse_args(["--live"])), ["1", "4", "5"])

    def test_all_runs_every_configured_runner_block_but_not_layer_8(self) -> None:
        runs = self._ordered_runs(run_all.parse_args(["--all"]))
        expected = [
            layer["id"]
            for layer in run_all.execution_layers(self.manifest)
            if layer["id"] != "8"
        ]
        self.assertEqual(runs, expected)
        self.assertNotIn("8", runs)

    def test_layer_selection_is_exact(self) -> None:
        self.assertEqual(self._runs(run_all.parse_args(["--layer", "4"])), {"4"})

    def test_integration_selects_only_layer_7(self) -> None:
        self.assertEqual(self._runs(run_all.parse_args(["--integration"])), {"7"})

    def test_toolchain_runs_when_any_of_1_4_5_7_run(self) -> None:
        self.assertTrue(run_all.toolchain_should_run(self.manifest, run_all.parse_args([])))
        self.assertTrue(run_all.toolchain_should_run(self.manifest, run_all.parse_args(["--integration"])))
        self.assertFalse(run_all.toolchain_should_run(self.manifest, run_all.parse_args(["--layer", "2"])))

    def test_live_eval_layers_print_python_command_plans(self) -> None:
        live_eval_layers = [
            layer for layer in self.manifest["layers"]
            if layer.get("live_only") is True and layer.get("execution") == "print-commands"
        ]
        self.assertTrue(live_eval_layers)
        for layer in live_eval_layers:
            layer_id = layer["id"]
            with self.subTest(msg=f"Layer {layer_id} uses Python command plans"):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    run_all.print_layer_commands(layer, REPO_ROOT)
                text = output.getvalue()
                self.assertEqual(self._ordered_runs(run_all.parse_args(["--layer", layer_id])), [layer_id])
                self.assertIn("python3 tests/speckit-pro/", text)
                self.assertNotIn("    bash ", text)
                self.assertTrue(all(script["path"].endswith(".py") for script in layer["scripts"]))


class HeadlineTests(unittest.TestCase):
    def test_passing_headline(self) -> None:
        self.assertIn("speckit-pro test suite: 10/10 passed", run_all.format_headline(10, 0))

    def test_failing_headline_includes_failed_count(self) -> None:
        line = run_all.format_headline(7, 3)
        self.assertIn("speckit-pro test suite: 7/10 passed (3 failed)", line)

    def test_exit_code_maps_from_failures(self) -> None:
        self.assertEqual(run_all.exit_code_for(0), 0)
        self.assertEqual(run_all.exit_code_for(1), 1)


class LayerExecutionRegressionTests(unittest.TestCase):
    def test_direct_child_requires_one_path_stem_owned_summary(self) -> None:
        layer = {
            "id": "4",
            "label": "Script unit tests",
            "integration": False,
            "scripts": [{"path": "tests/speckit-pro/nested-aggregate.py"}],
        }
        cases = (
            ("missing summary", 0, "", (0, 1)),
            ("wrong label only", 0, "nested-child: 1/1 passed\n", (0, 1)),
            (
                "duplicate owned summary",
                0,
                "nested-aggregate: 1/1 passed\nnested-aggregate: 1/1 passed\n",
                (0, 1),
            ),
            ("zero discovery", 0, "nested-aggregate: 0/0 passed\n", (0, 1)),
            ("partial pass", 0, "nested-aggregate: 1/2 passed\n", (1, 1)),
            ("passed exceeds total", 0, "nested-aggregate: 2/1 passed\n", (0, 1)),
            ("nonzero all-pass", 1, "nested-aggregate: 1/1 passed\n", (1, 1)),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            child = root / layer["scripts"][0]["path"]
            child.parent.mkdir(parents=True)
            child.touch()
            for case_name, exit_code, child_output, expected in cases:
                with (
                    self.subTest(case=case_name),
                    mock.patch.object(run_all, "dispatch_script", return_value=(child_output, exit_code)),
                    contextlib.redirect_stdout(io.StringIO()),
                ):
                    self.assertEqual(
                        run_all.run_execute_layer(layer, run_all.parse_args(["--layer", "4"]), root),
                        expected,
                    )

    def test_integration_layer_uses_its_aggregate_summary_once(self) -> None:
        layer = {
            "id": "7",
            "label": "Integration fixtures",
            "integration": True,
            "scripts": [{"path": "tests/speckit-pro/aggregate.py"}],
        }
        child_output = (
            "nested-one: 2/2 passed\n"
            "nested-two: 1/3 passed\n"
            "aggregate: 1/2 passed\n"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            child = root / layer["scripts"][0]["path"]
            child.parent.mkdir(parents=True)
            child.touch()
            with (
                mock.patch.object(run_all, "dispatch_script", return_value=(child_output, 1)),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                passed, failed = run_all.run_execute_layer(
                    layer,
                    run_all.parse_args(["--integration"]),
                    root,
                )
        self.assertEqual((passed, failed), (1, 1))

    def test_selected_layer_with_no_scripts_fails_closed(self) -> None:
        manifest = {
            "layers": [
                {
                    "id": "4",
                    "label": "Script unit tests",
                    "default": True,
                    "live_only": False,
                    "integration": False,
                    "execution": "execute",
                    "scripts": [],
                }
            ]
        }
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as temp_root:
            with (
                mock.patch.object(run_all, "repo_root", return_value=Path(temp_root)),
                mock.patch.object(run_all, "load_manifest", return_value=manifest),
                mock.patch.dict(run_all.os.environ, {"SPECKIT_SKIP_TOOLCHAIN_CHECK": "1"}),
                contextlib.redirect_stdout(output),
            ):
                exit_code = run_all.main(["--layer", "4"])
        self.assertEqual(exit_code, 1)
        self.assertIn("no test scripts discovered", output.getvalue())

    def test_unknown_layer_selects_no_execution_and_fails_closed(self) -> None:
        manifest = {
            "layers": [
                {
                    "id": "4",
                    "label": "Script unit tests",
                    "default": True,
                    "live_only": False,
                    "integration": False,
                    "execution": "execute",
                    "scripts": [{"path": "tests/speckit-pro/unused.py"}],
                }
            ]
        }
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as temp_root:
            with (
                mock.patch.object(run_all, "repo_root", return_value=Path(temp_root)),
                mock.patch.object(run_all, "load_manifest", return_value=manifest),
                mock.patch.dict(run_all.os.environ, {"SPECKIT_SKIP_TOOLCHAIN_CHECK": "1"}),
                contextlib.redirect_stdout(output),
            ):
                exit_code = run_all.main(["--layer", "missing"])
        self.assertEqual(exit_code, 1)
        self.assertIn("no executable layer selected", output.getvalue())

    def test_selected_layer_with_missing_script_fails_closed(self) -> None:
        manifest = {
            "layers": [
                {
                    "id": "4",
                    "label": "Script unit tests",
                    "default": True,
                    "live_only": False,
                    "integration": False,
                    "execution": "execute",
                    "scripts": [{"path": "tests/speckit-pro/missing-child.py"}],
                }
            ]
        }
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as temp_root:
            with (
                mock.patch.object(run_all, "repo_root", return_value=Path(temp_root)),
                mock.patch.object(run_all, "load_manifest", return_value=manifest),
                mock.patch.dict(run_all.os.environ, {"SPECKIT_SKIP_TOOLCHAIN_CHECK": "1"}),
                contextlib.redirect_stdout(output),
            ):
                exit_code = run_all.main(["--layer", "4"])
        self.assertEqual(exit_code, 1)
        self.assertIn("FAIL: missing-child (not found)", output.getvalue())
        self.assertIn("speckit-pro test suite: 0/1 passed (1 failed)", output.getvalue())

    def test_non_python_manifest_entry_is_counted_failure_not_crash(self) -> None:
        manifest = {
            "layers": [
                {
                    "id": "4",
                    "label": "Script unit tests",
                    "default": True,
                    "live_only": False,
                    "integration": False,
                    "execution": "execute",
                    "scripts": [{"path": "tests/speckit-pro/not-python.sh"}],
                }
            ]
        }
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as temp_root:
            root = Path(temp_root)
            script = root / "tests" / "speckit-pro" / "not-python.sh"
            script.parent.mkdir(parents=True, exist_ok=True)
            script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            with (
                mock.patch.object(run_all, "repo_root", return_value=root),
                mock.patch.object(run_all, "load_manifest", return_value=manifest),
                mock.patch.dict(run_all.os.environ, {"SPECKIT_SKIP_TOOLCHAIN_CHECK": "1"}),
                contextlib.redirect_stdout(output),
            ):
                exit_code = run_all.main(["--layer", "4"])
        self.assertEqual(exit_code, 1)
        self.assertIn("FAIL not-python (0/1, 1 failed)", output.getvalue())
        self.assertIn("speckit-pro test suite: 0/1 passed (1 failed)", output.getvalue())


def main() -> int:
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    for case in (
        ArgParsingTests,
        ScopeSelectionTests,
        HeadlineTests,
        LayerExecutionRegressionTests,
    ):
        suite.addTests(loader.loadTestsFromTestCase(case))
    return test_result.run_counted(suite, label="test-run-all")


if __name__ == "__main__":
    raise SystemExit(main())
