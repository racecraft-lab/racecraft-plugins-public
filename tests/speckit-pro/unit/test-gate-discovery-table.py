#!/usr/bin/env python3
"""Contract tests for the gate discovery table and its stdlib validator.

The shipped table must validate, the schema file must agree with the
validator's enums, and every rule the validator enforces must reject a
minimal negative case so a silently permissive validator cannot pass.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
SHARED_LIB = REPO_ROOT / "tests" / "speckit-pro" / "lib"
for _root in (SHARED_LIB, PLUGIN_ROOT):
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from speckit_pro_runner import gate_discovery  # noqa: E402
from test_result import run_counted  # noqa: E402

SCHEMA_PATH = PLUGIN_ROOT / "speckit_pro_runner" / "contracts" / "gate-discovery-table.schema.json"


def valid_table() -> dict:
    return {
        "schema_version": "1.0",
        "rows": [
            {
                "language": "python",
                "slot": "DEPENDENCY_RULES",
                "signal": {"kind": "file", "path": ".importlinter"},
                "tool": "import-linter",
                "install": "pip install import-linter",
                "command": "lint-imports --config {rules_path}",
            }
        ],
    }


def mutated(**changes: object) -> dict:
    table = valid_table()
    row = table["rows"][0]
    for key, value in changes.items():
        if value is None:
            row.pop(key, None)
        else:
            row[key] = value
    return table


class GateDiscoveryTableTests(unittest.TestCase):
    def test_gate_discovery_contract(self) -> None:
        shipped = gate_discovery.load_table()
        with self.subTest(msg="shipped table validates"):
            self.assertEqual([], gate_discovery.validate_table(shipped))
        with self.subTest(msg="shipped table covers every slot for both languages"):
            covered = {(row["language"], row["slot"]) for row in shipped["rows"]}
            expected = {(lang, slot) for lang in gate_discovery.LANGUAGES for slot in gate_discovery.SLOTS}
            self.assertEqual(expected, covered)

        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        row_props = schema["properties"]["rows"]["items"]["properties"]
        with self.subTest(msg="schema enums match the validator"):
            self.assertEqual(list(gate_discovery.LANGUAGES), row_props["language"]["enum"])
            self.assertEqual(list(gate_discovery.SLOTS), row_props["slot"]["enum"])
            self.assertEqual(gate_discovery.SCHEMA_VERSION, schema["properties"]["schema_version"]["const"])
            self.assertEqual(list(gate_discovery.ROW_FIELDS), schema["properties"]["rows"]["items"]["required"])
        with self.subTest(msg="schema placeholder list matches the validator"):
            described = schema["properties"]["rows"]["items"]["properties"]["command"]["description"]
            for name in gate_discovery.PLACEHOLDERS:
                self.assertIn("{" + name + "}", described)

        with self.subTest(msg="minimal valid table passes"):
            self.assertEqual([], gate_discovery.validate_table(valid_table()))

        negatives = {
            "top level not an object": [],
            "wrong schema_version": {**valid_table(), "schema_version": "2.0"},
            "unknown top-level key": {**valid_table(), "extra": 1},
            "empty rows": {"schema_version": "1.0", "rows": []},
            "row not an object": {"schema_version": "1.0", "rows": ["x"]},
            "missing field": mutated(install=None),
            "unknown field": mutated(priority=1),
            "empty tool": mutated(tool="  "),
            "bad language": mutated(language="rust"),
            "bad slot": mutated(slot="FORMAL_CHECK"),
            "signal not an object": mutated(signal="pyproject.toml"),
            "signal unknown kind": mutated(signal={"kind": "env", "path": "X"}),
            "signal unknown field": mutated(signal={"kind": "file", "path": "a", "glob": "*"}),
            "signal absolute path": mutated(signal={"kind": "file", "path": "/etc/passwd"}),
            "signal parent segment": mutated(signal={"kind": "file", "path": "../x"}),
            "unknown placeholder": mutated(command="tool {bogus}"),
        }
        for label, table in negatives.items():
            with self.subTest(msg=f"rejects: {label}"):
                self.assertTrue(gate_discovery.validate_table(table), label)

        with self.subTest(msg="rejects duplicate (language, slot, signal.path)"):
            table = valid_table()
            table["rows"].append(copy.deepcopy(table["rows"][0]))
            problems = gate_discovery.validate_table(table)
            self.assertTrue(any("duplicate" in problem for problem in problems), problems)
        with self.subTest(msg="same slot with a different signal path is allowed (first match wins)"):
            table = valid_table()
            second = copy.deepcopy(table["rows"][0])
            second["signal"]["path"] = "pyproject.toml"
            table["rows"].append(second)
            self.assertEqual([], gate_discovery.validate_table(table))

        env = {"PYTHONPATH": str(PLUGIN_ROOT), "PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"}
        with self.subTest(msg="CLI exits 0 on the shipped table"):
            result = subprocess.run(
                [sys.executable, "-m", "speckit_pro_runner.gate_discovery"],
                capture_output=True, text=True, env=env, cwd=REPO_ROOT, check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
        with self.subTest(msg="CLI exits 1 and names the violation on a bad override"):
            bad = REPO_ROOT / "tests" / "speckit-pro" / "unit" / "fixtures" / "gate-discovery" / "bad-slot.json"
            result = subprocess.run(
                [sys.executable, "-m", "speckit_pro_runner.gate_discovery", str(bad)],
                capture_output=True, text=True, env=env, cwd=REPO_ROOT, check=False,
            )
            self.assertEqual(1, result.returncode)
            self.assertIn("rows[0].slot", result.stderr)


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(GateDiscoveryTableTests)


def main() -> int:
    return run_counted(build_suite(), label="test-gate-discovery-table")


if __name__ == "__main__":
    raise SystemExit(main())
