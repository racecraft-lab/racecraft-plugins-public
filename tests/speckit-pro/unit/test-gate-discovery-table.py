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
import tempfile
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
        with self.subTest(msg="optional probe is accepted"):
            self.assertEqual([], gate_discovery.validate_table(mutated(probe=["lint-imports"])))
        with self.subTest(msg="schema declares probe optional with the same shape"):
            self.assertIn("probe", row_props)
            self.assertNotIn("probe", schema["properties"]["rows"]["items"]["required"])

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
            "probe not a list": mutated(probe="lint-imports"),
            "probe empty": mutated(probe=[]),
            "probe with path": mutated(probe=["bin/lint-imports"]),
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


class GateSlotResolutionTests(unittest.TestCase):
    """resolve_slots fills PROJECT_COMMANDS slots from the table."""

    def _resolve(self, root: Path, stack: str, present: set[str] = frozenset()) -> dict:
        return gate_discovery.resolve_slots(
            root, stack, file_exists=lambda path: path.is_file(), which=lambda name: name in present
        )

    def test_resolve_slots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.subTest(msg="unknown stack leaves every slot unconfigured"):
                slots = self._resolve(root, "rust")
                self.assertEqual({"status": "unconfigured", "command": "N/A"}, slots["COMPLEXITY"])
            with self.subTest(msg="python with no signal files stays unconfigured"):
                self.assertTrue(all(s["status"] == "unconfigured" for s in self._resolve(root, "python").values()))
            (root / "pyproject.toml").write_text("", encoding="utf-8")
            slots = self._resolve(root, "python", {"radon"})
            with self.subTest(msg="thresholds and rules_path substituted; paths and plugin_root left literal"):
                cmd = slots["COMPLEXITY"]["command"]
                self.assertIn("--ceiling 30 --complexity-ceiling 8", cmd)
                self.assertIn("{paths}", cmd)
                self.assertIn("{plugin_root}/scripts/crap-score.py", cmd)
                self.assertEqual("lint-imports --config pyproject.toml", slots["DEPENDENCY_RULES"]["command"])
            with self.subTest(msg="tool_present is false when any probe name is missing"):
                self.assertIs(False, slots["COMPLEXITY"]["tool_present"])
                self.assertIs(True, self._resolve(root, "python", {"radon", "coverage"})["COMPLEXITY"]["tool_present"])
            with self.subTest(msg="populated slot carries tool, install, and signal"):
                self.assertEqual({"populated", "pip install radon coverage", "pyproject.toml"},
                                 {slots["COMPLEXITY"]["status"], slots["COMPLEXITY"]["install"], slots["COMPLEXITY"]["signal"]})
            with self.subTest(msg="mutation slot unconfigured without its signal"):
                self.assertEqual("N/A", slots["MUTATION"]["command"])
            (root / ".importlinter").write_text("", encoding="utf-8")
            with self.subTest(msg="first matching row in file order wins"):
                self.assertEqual("lint-imports --config .importlinter", self._resolve(root, "python")["DEPENDENCY_RULES"]["command"])
            override = root / ".specify" / "gate-discovery.json"
            override.parent.mkdir()
            override.write_text(json.dumps({"schema_version": "1.0", "rows": [{
                "language": "python", "slot": "DEPENDENCY_RULES", "signal": {"kind": "file", "path": "pyproject.toml"},
                "tool": "custom", "install": "none", "command": "custom-lint {rules_path}"}]}), encoding="utf-8")
            with self.subTest(msg="valid repository override outranks the shipped table"):
                self.assertEqual("custom-lint pyproject.toml", self._resolve(root, "python")["DEPENDENCY_RULES"]["command"])
            override.write_text(json.dumps({"schema_version": "1.0", "rows": [{"slot": "BOGUS"}]}), encoding="utf-8")
            with self.subTest(msg="invalid override is reported and ignored"):
                slots = self._resolve(root, "python")
                self.assertEqual("lint-imports --config .importlinter", slots["DEPENDENCY_RULES"]["command"])
                self.assertTrue(any("rows[0]" in p for p in slots["DEPENDENCY_RULES"]["override_ignored"]))
            with self.subTest(msg="nodejs maps to typescript rows"):
                (root / "package.json").write_text("{}", encoding="utf-8")
                self.assertIn("--language typescript", self._resolve(root, "nodejs")["COMPLEXITY"]["command"])


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for case in (GateDiscoveryTableTests, GateSlotResolutionTests):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    return suite


def main() -> int:
    return run_counted(build_suite(), label="test-gate-discovery-table")


if __name__ == "__main__":
    raise SystemExit(main())
