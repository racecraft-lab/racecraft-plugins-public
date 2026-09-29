#!/usr/bin/env python3
"""Runner trust roster, payload source gates, and runner-invocation vocabulary."""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
RUNNER_DIR = PLUGIN_ROOT / "speckit_pro_runner"
RELEASE_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "installed-plugin-release"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
for _import_root in (PLUGIN_ROOT, LIB_DIR):
    if str(_import_root) not in sys.path:
        sys.path.insert(0, str(_import_root))
from speckit_pro_runner import envelope, runtime  # noqa: E402
from speckit_pro_runner.gates import payloads, release  # noqa: E402
from speckit_pro_runner.helpers import install  # noqa: E402
from test_result import run_counted  # noqa: E402

RUNTIME_LOADED_JSON = (
    "gate_discovery_table.json",
    "install_inventory.json",
    "contracts/task-results.schema.json",
)


def load_refresh_script():  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(
        "refresh_release_artifacts_roster", REPO_ROOT / "scripts" / "refresh-release-artifacts.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_runner(root: Path) -> Path:
    package_dir = root / "speckit-pro" / "speckit_pro_runner"
    shutil.copytree(RUNNER_DIR, package_dir, ignore=shutil.ignore_patterns("__pycache__"))
    return package_dir


class RunnerTrustRosterTests(unittest.TestCase):
    def test_runtime_loaded_json_changes_break_verification(self) -> None:
        refresh = load_refresh_script()
        for name in RUNTIME_LOADED_JSON:
            with self.subTest(file=name), tempfile.TemporaryDirectory() as tmp:
                package_dir = copy_runner(Path(tmp))
                refresh.refresh_runner_trust_metadata(Path(tmp))
                target = package_dir / name
                target.write_text(target.read_text(encoding="utf-8") + "\n", encoding="utf-8")

                report = runtime.metadata_report(package_dir.parent, package_dir, check_metadata=True)

                self.assertEqual("mismatch", report["verification_status"])

    def test_refresh_script_records_the_runtime_roster(self) -> None:
        refresh = load_refresh_script()
        with tempfile.TemporaryDirectory() as tmp:
            package_dir = copy_runner(Path(tmp))
            refresh.refresh_runner_trust_metadata(Path(tmp))
            report = runtime.metadata_report(package_dir.parent, package_dir, check_metadata=True)

        self.assertEqual("verified", report["verification_status"])
        recorded = {record["path"]["value"] for record in report["runner_files"]}
        for name in RUNTIME_LOADED_JSON:
            self.assertIn(f"speckit_pro_runner/{name}", recorded)
        self.assertNotIn(f"speckit_pro_runner/{runtime.MANIFEST_NAME}", recorded)

    def test_payload_gate_flags_stale_runtime_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dist_root = Path(tmp) / "dist"
            payloads.build_installed_plugin_payloads(REPO_ROOT, dist_root)
            payload_root = dist_root / "claude" / "speckit-pro"
            table = payload_root / "speckit_pro_runner" / "gate_discovery_table.json"
            table.write_text(table.read_text(encoding="utf-8") + "\n", encoding="utf-8")

            mismatches = payloads.payload_trust_metadata_mismatches(payload_root)

        self.assertEqual(
            {"speckit_pro_runner/speckit-pro-runner.manifest.json", "speckit_pro_runner/speckit-pro-runner.sha256"},
            set(mismatches),
        )


class PayloadRequiredSourceTests(unittest.TestCase):
    def test_build_fails_when_a_required_source_directory_is_missing(self) -> None:
        required = sorted(
            {*payloads.CLAUDE_REQUIRED_PAYLOAD_PATHS, *payloads.CODEX_REQUIRED_PAYLOAD_PATHS, "skills", "codex-skills"}
        )
        self.assertIn("agents", required)
        self.assertIn("codex-agents", required)
        for missing in required:
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as tmp:
                repo_root = Path(tmp) / "repo"
                source = repo_root / "speckit-pro"
                for name in required:
                    if name != missing:
                        (source / name).mkdir(parents=True)
                expected = re.escape(f"required source path missing: {source / missing}")
                with self.assertRaisesRegex(FileNotFoundError, expected):
                    payloads.build_installed_plugin_payloads(repo_root, Path(tmp) / "dist")


class RunnerInvocationVocabularyTests(unittest.TestCase):
    def test_operation_enum_matches_the_envelope(self) -> None:
        vocabulary = sorted(envelope.SUPPORTED_RUNNER_OPERATIONS)
        self.assertEqual(vocabulary, sorted(release.RUNNER_OPERATIONS))
        contracts = RELEASE_FIXTURES / "contracts"
        schema = json.loads((contracts / "runner-invocation.schema.json").read_text(encoding="utf-8"))
        release_schema = json.loads((contracts / "release-readiness.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(vocabulary, sorted(schema["properties"]["operation"]["enum"]))
        record_schema = release_schema["$defs"]["runner_invocation"]
        self.assertEqual(vocabulary, sorted(record_schema["properties"]["operation"]["enum"]))

    def test_records_report_the_operation_they_send(self) -> None:
        cases = json.loads((RELEASE_FIXTURES / "runner-invocation-cases.json").read_text(encoding="utf-8"))["cases"]
        for case in (item for item in cases if "candidate_results" in item):
            with self.subTest(case_id=case["case_id"]):
                record, _diagnostics = install.runner_invocation_record(case, None, REPO_ROOT)
                self.assertEqual(record["runner_request"]["operation"], record["operation"])
                self.assertIn(record["operation"], envelope.SUPPORTED_RUNNER_OPERATIONS)


def build_suite() -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    return unittest.TestSuite(
        loader.loadTestsFromTestCase(case)
        for case in (RunnerTrustRosterTests, PayloadRequiredSourceTests, RunnerInvocationVocabularyTests)
    )


def main() -> int:
    return run_counted(build_suite(), label="test-runner-trust-and-payload-gates")


if __name__ == "__main__":
    raise SystemExit(main())
