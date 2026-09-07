#!/usr/bin/env python3
"""Contract tests for the architecture graph the viewer page consumes.

The schema file must agree with the validator's enums, the fixture graph must
validate, and every rule the validator enforces must reject a minimal negative
case, including the two rules a schema cannot state: edge endpoints are node
ids, and a pr-scoped graph holds only touched nodes and their one-hop
neighbours.
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

from speckit_pro_runner import architecture_graph  # noqa: E402
from test_result import run_counted  # noqa: E402

SCHEMA_PATH = PLUGIN_ROOT / "speckit_pro_runner" / "contracts" / "architecture-graph.schema.json"
FIXTURES = REPO_ROOT / "tests" / "speckit-pro" / "unit" / "fixtures" / "architecture-graph"
MANIFEST = PLUGIN_ROOT / "artifact-gallery" / "manifest.json"


def graph() -> dict:
    return json.loads((FIXTURES / "pr-graph.json").read_text(encoding="utf-8"))


class ArchitectureGraphTests(unittest.TestCase):
    def test_architecture_graph_contract(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        props = schema["properties"]
        with self.subTest(msg="schema enums and required lists match the validator"):
            self.assertEqual(architecture_graph.SCHEMA_VERSION, props["schema_version"]["const"])
            self.assertEqual(list(architecture_graph.SCOPE_KINDS), props["scope"]["properties"]["kind"]["enum"])
            self.assertEqual(list(architecture_graph.LANGUAGES), props["language"]["enum"])
            self.assertEqual(list(architecture_graph.TOP_FIELDS), schema["required"])
            self.assertEqual(list(architecture_graph.NODE_FIELDS), props["nodes"]["items"]["required"])
            self.assertEqual(list(architecture_graph.EDGE_FIELDS), props["edges"]["items"]["required"])
            self.assertEqual(list(architecture_graph.DELTA_KINDS),
                             props["nodes"]["items"]["properties"]["delta"]["properties"]["kind"]["enum"])
        with self.subTest(msg="fixture pr graph validates"):
            self.assertEqual([], architecture_graph.validate_graph(graph()))
        with self.subTest(msg="repository scope validates without base or touched"):
            g = graph()
            g["scope"] = {"kind": "repository"}
            for node in g["nodes"]:
                node.pop("touched", None)
            self.assertEqual([], architecture_graph.validate_graph(g))

        def mutated(fn) -> dict:
            g = graph()
            fn(g)
            return g

        negatives = {
            "top level not an object": [],
            "wrong schema_version": mutated(lambda g: g.update(schema_version="2.0")),
            "unknown top-level key": mutated(lambda g: g.update(extra=1)),
            "bad language": mutated(lambda g: g.update(language="rust")),
            "bad scope kind": mutated(lambda g: g["scope"].update(kind="branch")),
            "pr scope without touched": mutated(lambda g: g["scope"].pop("touched")),
            "repository scope with touched": mutated(lambda g: g["scope"].update(kind="repository")),
            "node missing path": mutated(lambda g: g["nodes"][1].pop("path")),
            "node unknown field": mutated(lambda g: g["nodes"][1].update(color="red")),
            "duplicate node id": mutated(lambda g: g["nodes"].append(copy.deepcopy(g["nodes"][1]))),
            "bad delta kind": mutated(lambda g: g["nodes"][0]["delta"].update(kind="renamed")),
            "touched flag on an untouched node": mutated(lambda g: g["nodes"][1].update(touched=True)),
            "edge to unknown node": mutated(lambda g: g["edges"].append({"from": "src/queue/api.py", "to": "ghost.py"})),
            "rule on a valid edge": mutated(lambda g: g["edges"][0].update(rule="x")),
            "touched id that is not a node": mutated(lambda g: g["scope"]["touched"].append("missing.py")),
        }
        for label, data in negatives.items():
            with self.subTest(msg=f"rejects: {label}"):
                self.assertTrue(architecture_graph.validate_graph(data), label)
        with self.subTest(msg="pr scope rejects a node two hops from every touched node"):
            data = json.loads((FIXTURES / "out-of-scope.json").read_text(encoding="utf-8"))
            problems = architecture_graph.validate_graph(data)
            self.assertEqual(1, len(problems))
            self.assertIn("c.py", problems[0])

        with self.subTest(msg="gallery manifest carries the planned architecture-viewer entry with no template file"):
            entries = {e["id"]: e for e in json.loads(MANIFEST.read_text(encoding="utf-8"))["templates"]}
            entry = entries["architecture-viewer"]
            self.assertEqual(("planned", "draft-pr", {"origin": "repository"}), (entry["status"], entry["stage"], entry["source"]))
            self.assertEqual({"any_of": ["brownfield_change"]}, entry["trigger"])
            self.assertFalse((PLUGIN_ROOT / "artifact-gallery" / "templates" / "architecture-viewer.html").exists())

        env = {"PYTHONPATH": str(PLUGIN_ROOT), "PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"}
        with self.subTest(msg="CLI exits 0 on the fixture and 1 naming the violation"):
            ok = subprocess.run([sys.executable, "-m", "speckit_pro_runner.architecture_graph", str(FIXTURES / "pr-graph.json")],
                                capture_output=True, text=True, env=env, cwd=REPO_ROOT, check=False)
            self.assertEqual(0, ok.returncode, ok.stderr)
            bad = subprocess.run([sys.executable, "-m", "speckit_pro_runner.architecture_graph", str(FIXTURES / "out-of-scope.json")],
                                 capture_output=True, text=True, env=env, cwd=REPO_ROOT, check=False)
            self.assertEqual(1, bad.returncode)
            self.assertIn("one-hop", bad.stderr)


def main() -> int:
    return run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(ArchitectureGraphTests), label="test-architecture-graph")


if __name__ == "__main__":
    raise SystemExit(main())
