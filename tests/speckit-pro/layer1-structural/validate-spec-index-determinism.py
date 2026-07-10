#!/usr/bin/env python3
"""Spec-index helper contract check (port of validate-spec-index-determinism.sh).

XPLAT-010 count-parity port (T038, US2). Python 3.11+ standard library only.
Validates that the Python runner owns read-only spec-index checking, that write
mode remains explicitly deferred, that invoking the read-only helper leaves the
fixture tree unchanged, and that the roadmap-MOC template still exposes the
INDEX sentinels. Every former ``assert_*``/``_pass``/``_fail`` execution maps to
one counted ``subTest`` unit; names are reproduced via ``subTest(msg=...)`` for
a 1:1 baseline match.

The shell predecessor executes two assertions under the same
``generate-spec-index-write is registered as deferred`` current-test name; in
verbose mode the second appears as a bare ``PASS``. The port records both as
counted subTests with the same name, preserving the true ``16/16`` assertion
count instead of the malformed 15-line verbose capture.

Baseline: ``tests/speckit-pro/parity/bash-to-python/validate-spec-index-determinism-baseline.txt``
(TOTAL: 16).
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

RUNNER_DIR = REPO_ROOT / "speckit-pro" / "speckit_pro_runner"
FIXTURE_ROOT = REPO_ROOT / "tests" / "speckit-pro" / "layer1-structural" / "fixtures" / "spec-index" / "determinism"
TEMPLATE = REPO_ROOT / "speckit-pro" / "skills" / "speckit-coach" / "templates" / "roadmap-moc-template.md"

REGISTRY_REQ = {
    "schema_version": "1.0",
    "request_id": "l1-helper-registry",
    "helper_id": "helper-registry-dispatch",
    "operation": "helper-registry-dispatch",
    "mode": "read_only",
    "inputs": {},
}
MUTATION_REGISTRY_REQ = {
    "schema_version": "1.0",
    "request_id": "l1-mutation-registry",
    "helper_id": "mutation-registry-dispatch",
    "operation": "mutation-registry-dispatch",
    "mode": "read_only",
    "inputs": {},
}
CHECK_REQ = {
    "schema_version": "1.0",
    "request_id": "l1-generate-spec-index-check",
    "helper_id": "generate-spec-index-check",
    "operation": "generate-spec-index-check",
    "mode": "read_only",
    "inputs": {
        "repo_root": "tests/speckit-pro/layer1-structural/fixtures/spec-index/determinism",
    },
}


def _runner_request(payload: dict[str, object]) -> str:
    env = os.environ.copy()
    plugin_root = REPO_ROOT / "speckit-pro"
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = plugin_root.as_posix() if not existing else f"{plugin_root.as_posix()}{os.pathsep}{existing}"
    completed = subprocess.run(
        [sys.executable, "-m", "speckit_pro_runner"],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        env=env,
        shell=False,
        check=False,
    )
    return completed.stdout


def _snapshot(root: Path) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    for path in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix()):
        digest = hashlib.sha1(path.read_bytes()).hexdigest()
        records.append((path.relative_to(root).as_posix(), digest))
    return records


def _first_line_containing(path: Path, needle: str) -> str:
    if not path.is_file():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if needle in line:
            return line
    return ""


class ValidateSpecIndexDeterminism(unittest.TestCase):
    def test_spec_index_helper_contract(self) -> None:
        with self.subTest(msg="runner package exists at the contracted path"):
            self.assertTrue(
                (RUNNER_DIR / "__main__.py").is_file(),
                f"FAIL: runner entrypoint not found at {RUNNER_DIR / '__main__.py'}",
            )

        registry_json = _runner_request(REGISTRY_REQ)
        with self.subTest(msg="read-only registry dispatch succeeds"):
            self.assertIn('"status":"ok"', registry_json)
        with self.subTest(msg="generate-spec-index-check is registered"):
            self.assertIn('"helper_id":"generate-spec-index-check"', registry_json)
        with self.subTest(msg="generate-spec-index-check is Python-authoritative"):
            self.assertIn('"promotion_status":"python_authoritative"', registry_json)

        mutation_registry_json = _runner_request(MUTATION_REGISTRY_REQ)
        with self.subTest(msg="mutation registry dispatch succeeds"):
            self.assertIn('"status":"ok"', mutation_registry_json)
        with self.subTest(msg="generate-spec-index-write is registered as deferred"):
            self.assertIn('"helper_id":"generate-spec-index-write"', mutation_registry_json)
        with self.subTest(msg="generate-spec-index-write is registered as deferred"):
            self.assertIn('"promotion_status":"deferred"', mutation_registry_json)

        snap_before = _snapshot(FIXTURE_ROOT)
        check_json = _runner_request(CHECK_REQ)
        snap_after = _snapshot(FIXTURE_ROOT)

        with self.subTest(msg="generate-spec-index-check request succeeds"):
            self.assertIn('"status":"ok"', check_json)
        with self.subTest(msg="generate-spec-index-check reports the helper id"):
            self.assertIn('"helper_id":"generate-spec-index-check"', check_json)
        with self.subTest(msg="generate-spec-index-check uses shell:false"):
            self.assertIn('"shell":false', check_json)
        with self.subTest(msg="generate-spec-index-check records writes_state:false"):
            self.assertIn('"writes_state":false', check_json)
        with self.subTest(msg="generate-spec-index-check leaves fixture bytes unchanged"):
            self.assertEqual(snap_before, snap_after, "read-only helper must not mutate spec-index fixtures")

        with self.subTest(msg="roadmap-MOC template exists at the contracted path"):
            self.assertTrue(TEMPLATE.is_file(), f"FAIL: roadmap-MOC template not found at {TEMPLATE}")

        tpl_index_start = _first_line_containing(TEMPLATE, "GENERATED:INDEX:START")
        tpl_index_end = _first_line_containing(TEMPLATE, "GENERATED:INDEX:END")

        with self.subTest(msg="template INDEX sentinels are present"):
            self.assertTrue(
                tpl_index_start and tpl_index_end,
                "missing INDEX sentinel in roadmap-MOC template",
            )
        with self.subTest(msg="template INDEX:START keeps the sentinel grammar"):
            self.assertEqual(
                "<!-- GENERATED:INDEX:START (do not edit; regenerated by generate-spec-index) -->",
                tpl_index_start,
                "template INDEX:START sentinel drifted",
            )
        with self.subTest(msg="template INDEX:END keeps the sentinel grammar"):
            self.assertEqual(
                "<!-- GENERATED:INDEX:END -->",
                tpl_index_end,
                "template INDEX:END sentinel drifted",
            )


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateSpecIndexDeterminism)


def main() -> int:
    return run_counted(build_suite(), label="validate-spec-index-determinism")


if __name__ == "__main__":
    raise SystemExit(main())
