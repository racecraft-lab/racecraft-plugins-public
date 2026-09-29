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
from speckit_pro_runner.json_schema import json_schema_failures  # noqa: E402
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
            "edges with no nodes at all": mutated(lambda g: (g["nodes"].clear(), g["scope"]["touched"].clear())),
            "rule on a valid edge": mutated(lambda g: g["edges"][0].update(rule="x")),
            "invalid edge without a rule": mutated(lambda g: g["edges"][0].update(valid=False)),
            "invalid edge with a blank rule": mutated(lambda g: g["edges"][0].update(valid=False, rule=" ")),
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


def _pr_graph_with(edit) -> dict:
    data = graph()
    edit(data)
    return data


# Graphs the schema states a rule for. The validator and the schema must both reject each one.
SCHEMA_STATED_NEGATIVES = {
    "wrong schema_version": lambda g: g.update(schema_version="2.0"),
    "unknown top-level key": lambda g: g.update(extra=1),
    "bad language": lambda g: g.update(language="rust"),
    "bad scope kind": lambda g: g["scope"].update(kind="branch"),
    "pr scope without base": lambda g: g["scope"].pop("base"),
    "pr scope without touched": lambda g: g["scope"].pop("touched"),
    "pr scope with empty touched": lambda g: g["scope"].update(touched=[]),
    "repository scope with base": lambda g: g.update(scope={"kind": "repository", "base": "origin/main"}),
    "repository scope with touched": lambda g: g.update(scope={"kind": "repository", "touched": ["a.py"]}),
    "node missing path": lambda g: g["nodes"][1].pop("path"),
    "node unknown field": lambda g: g["nodes"][1].update(color="red"),
    "bad delta kind": lambda g: g["nodes"][0]["delta"].update(kind="renamed"),
    "rule on a valid edge": lambda g: g["edges"][0].update(rule="x"),
    "invalid edge without a rule": lambda g: g["edges"][0].update(valid=False),
}

# Rules only the validator can state: they compare values across the document or trim blanks.
VALIDATOR_ONLY_NEGATIVES = {
    "duplicate node id": lambda g: g["nodes"].append(copy.deepcopy(g["nodes"][1])),
    "touched flag on an untouched node": lambda g: g["nodes"][1].update(touched=True),
    "edge to unknown node": lambda g: g["edges"].append({"from": "src/queue/api.py", "to": "ghost.py"}),
    "touched id that is not a node": lambda g: g["scope"]["touched"].append("missing.py"),
    "invalid edge with a blank rule": lambda g: g["edges"][0].update(valid=False, rule=" "),
}


class ArchitectureGraphSchemaParityTests(unittest.TestCase):
    """The schema and the validator agree on every rule the schema can state."""

    @staticmethod
    def schema_rejects(data: object) -> bool:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        return bool(json_schema_failures(data, schema, schema, "graph"))

    def test_both_accept_the_pr_and_repository_graphs(self) -> None:
        repository = _pr_graph_with(lambda g: g.update(scope={"kind": "repository"}))
        for label, data in (("pr", graph()), ("repository", repository)):
            with self.subTest(graph=label):
                self.assertEqual([], architecture_graph.validate_graph(data))
                self.assertFalse(self.schema_rejects(data))

    def assert_agreement(self, violations: dict, *, schema_rejects: bool) -> None:
        for label, edit in violations.items():
            with self.subTest(violation=label):
                data = _pr_graph_with(edit)
                self.assertTrue(architecture_graph.validate_graph(data), "validator")
                self.assertEqual(self.schema_rejects(data), schema_rejects, "schema")

    def test_both_reject_every_schema_stated_violation(self) -> None:
        self.assert_agreement(SCHEMA_STATED_NEGATIVES, schema_rejects=True)

    def test_validator_only_rules_are_not_claimed_by_the_schema(self) -> None:
        self.assert_agreement(VALIDATOR_ONLY_NEGATIVES, schema_rejects=False)


def main() -> int:
    suite = unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromTestCase(case)
        for case in (ArchitectureGraphTests, ArchitectureGraphSchemaParityTests)
    )
    return run_counted(suite, label="test-architecture-graph")


if __name__ == "__main__":
    raise SystemExit(main())
