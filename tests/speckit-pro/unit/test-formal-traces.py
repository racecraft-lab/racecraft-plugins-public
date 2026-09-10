#!/usr/bin/env python3
"""Trace integrity contracts; opt-in native tests execute three real implementations."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
sys.path[:0] = [str(PLUGIN_ROOT), str(REPO_ROOT / "tests/speckit-pro/lib")]

from speckit_pro_runner.formal import catalog, engine, helper, itf, quint, traces
from speckit_pro_runner.formal.evidence import read_checkpoint, record_path
from speckit_pro_runner.helpers.registry import dispatch_helper
from test_result import run_counted

OPTIONS = None


class TraceFixture(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        source = PLUGIN_ROOT / "skills/speckit-coach/examples/formal/counter-traces"
        shutil.copytree(source, self.root / "formal/counter")
        self.selection = {"schema_version": "1.0", "status": "enabled", "rationale": "Check the actual counter transitions",
                          "models": [{"id": "counter", "behavior": "Increment by exactly one", "origin": "existing", "evidence": "model_and_trace"}]}
        (self.root / "workflow.md").write_text("# Workflow\n\n## Formal Methods\n```json\n" + json.dumps(self.selection) + "\n```\n")
        (self.root / "spec.md").write_text("Increment by one until the limit, then hold.\n")
        (self.root / "plan.md").write_text("Capture each counter action and resulting state atomically.\n")
        self.trace_path = ".specify/formal-traces/counter/observed.itf.json"
        self.model = {"checker": "apalache", "module": "formal/counter/Counter.tla", "config": "formal/counter/Counter.cfg",
                      "inputs": ["formal/counter/Counter.tla", "formal/counter/Counter.cfg"],
                      "implementation_inputs": ["formal/counter/counter.py", "formal/counter/counter.mts", "formal/counter/CounterTrace.swift", "adapter_test.py"],
                      "properties": {"Bounded": {"kind": "invariant", "requirement": "FR1"}}, "assumptions": ["Start = 0, Limit = 2"],
                      "mode": "bounded", "init": "Init", "next": "Next", "bounds": {"length": 5},
                      "budget": {"timeout_seconds": 60, "output_bytes": 1048576},
                      "trace": {"format": "itf", "paths": [self.trace_path], "projection": {"count": "count"},
                                "actions": {"increment": "Increment", "hold": "Hold"}, "init": "Init", "next": "Next", "adapter_test": "adapter_test.py", "max_states": 20}}
        # Freeze the executed adapter harness in the producer's declared implementation inputs.
        shutil.copyfile(__file__, self.root / "adapter_test.py")
        self.tools = {"apalache": {"version": "0.62.2", "jar": ".specify/tools/apalache.jar", "sha256": "0" * 64, "java": "java", "heap_mb": 4096}}
        self.save_catalog()

    def save_catalog(self) -> None:
        target = self.root / catalog.CATALOG_PATH
        target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps({"schema_version": "1.0", "tools": self.tools, "models": {"counter": self.model}}))

    def observed(self, values=(0, 1, 2, 2)) -> dict:
        return {"vars": ["count"], "states": [
            {"#meta": {"index": i, **({"action": "hold" if value == values[i - 1] else "increment"} if i else {})},
             "count": {"#bigint": str(value)}} for i, value in enumerate(values)]}

    def stamp(self, trace=None) -> None:
        traces.write_trace(self.root, "counter", self.trace_path, trace or self.observed(), traces.binding(self.root, "counter"))

    def request(self, mode="dry_run", checkpoint="final") -> dict:
        inputs = {"repo_root": str(self.root), "workflow_file": "workflow.md", "spec_file": "spec.md", "plan_file": "plan.md", "checkpoint": checkpoint}
        return dispatch_helper(SimpleNamespace(helper_id="formal-check", operation="formal-check", mode=mode, request_id="trace-test", inputs=inputs))


class TraceContractTests(TraceFixture):
    def test_quint_main_is_required_with_an_actionable_diagnostic(self) -> None:
        self.model["language"] = "quint"
        with self.assertRaisesRegex(ValueError, "Quint model.main"):
            catalog.validate_language(self.model)

    def test_schema_enforces_language_checker_mode_and_module_profiles(self) -> None:
        from speckit_pro_runner.helpers.read_only import json_schema_failures
        schema = json.loads((PLUGIN_ROOT / "speckit_pro_runner/contracts/formal-methods.schema.json").read_text())
        quint_model = {**self.model, "language": "quint", "main": "Counter", "module": "formal/counter/Counter.qnt"}
        for model in (self.model, {**self.model, "language": "tla"}, quint_model,
                      {**self.model, "checker": "tlc", "mode": "finite", "bounds": {"max_set_size": 1000}}):
            with self.subTest(valid=model):
                self.assertEqual([], json_schema_failures(model, schema["$defs"]["model"], schema, "model"))
        invalid = [{k: v for k, v in quint_model.items() if k != "main"},
                   {**quint_model, "checker": "tlc"}, {**quint_model, "mode": "inductive"},
                   {**quint_model, "module": "formal/counter/Counter.tla"},
                   {**self.model, "module": "formal/counter/Counter.qnt"}, {**self.model, "main": "Counter"},
                   {**self.model, "mode": "finite"}, {**self.model, "checker": "tlc", "mode": "bounded"}]
        for model in invalid:
            with self.subTest(invalid=model):
                self.assertTrue(json_schema_failures(model, schema["$defs"]["model"], schema, "model"))

    def test_assignment_hints_preserve_data_and_constraints(self) -> None:
        value = {"kind": "NameEx", "name": "x", "type": "Untyped"}
        unchanged = {"kind": "OperEx", "oper": "UNCHANGED", "args": [value]}
        result = traces.declarative_ir(unchanged)
        self.assertEqual("EQ", result["oper"])
        self.assertEqual("PRIME", result["args"][0]["oper"])
        self.assertEqual(value, result["args"][0]["args"][0])
        assignment = {"kind": "OperEx", "oper": "Apalache!:=", "args": [value, {"kind": "ValEx", "value": "data := unchanged"}]}
        self.assertEqual({**assignment, "oper": "EQ"}, traces.declarative_ir(assignment))
        self.assertEqual(unchanged["oper"], "UNCHANGED")

    def test_lossless_values_and_rejected_encodings(self) -> None:
        self.assertEqual("9007199254740993", itf.literal({"#bigint": "9007199254740993"}))
        self.assertEqual("<<TRUE, 2>>", itf.literal([True, {"#bigint": "2"}]))
        self.assertEqual("{1, 2}", itf.literal({"#set": [{"#bigint": "2"}, {"#bigint": "1"}, {"#bigint": "1"}]}))
        self.assertEqual('[name |-> "Ada"]', itf.literal({"name": "Ada"}))
        self.assertIn(":>", itf.literal({"#map": [["key", {"#bigint": "3"}]]}))
        for value in (0, 1.5, float("nan"), None, {}, {"#bigint": 1}, {"#bigint": "01"},
                      {"#map": [["a", True], ["a", False]]}, {"tag": "Case", "value": True}, {"#unsupported": []}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                itf.literal(value)

    def test_malformed_mismatched_and_counterexample_traces_fail(self) -> None:
        invalid = []
        for update in ({"vars": ["other"]}, {"loop": 1}, {"states": []}, {"params": ["unapproved"]}):
            invalid.append({**self.observed(), **update})
        invalid.append({**self.observed(), "#meta": {"invalid": float("nan")}})
        for index, key, value in ((1, "index", 2), (1, "action", "invented"), (0, "action", "increment")):
            trace = self.observed()
            trace["states"][index]["#meta"][key] = value
            invalid.append(trace)
        for trace in invalid:
            with self.subTest(trace=trace), self.assertRaises(ValueError):
                traces.write_trace(self.root, "counter", self.trace_path, trace, traces.binding(self.root, "counter"))
        self.stamp()
        path = self.root / self.trace_path
        path.write_text('{"vars": ["count"], "vars": ["other"]}')
        with self.assertRaisesRegex(catalog.FormalError, "Invalid ITF JSON"):
            traces.load_trace(self.root, "counter", self.model, self.trace_path)
        path.write_text('{"#meta":{"invalid":NaN}}')
        with self.assertRaisesRegex(catalog.FormalError, "non-finite"):
            traces.load_trace(self.root, "counter", self.model, self.trace_path)

    def test_producer_binding_rejects_edits_during_or_after_capture(self) -> None:
        before = traces.binding(self.root, "counter")
        path = self.root / "formal/counter/counter.py"
        original = path.read_text()
        path.write_text(original + "\n# changed\n")
        with self.assertRaisesRegex(catalog.FormalError, "changed while producing"):
            traces.write_trace(self.root, "counter", self.trace_path, self.observed(), before)
        self.stamp()
        path.write_text(original)
        with self.assertRaisesRegex(catalog.FormalError, "does not match"):
            traces.load_trace(self.root, "counter", self.model, self.trace_path)
        self.stamp()
        self.model["trace"]["actions"]["increment"] = "Hold"
        self.save_catalog()
        with self.assertRaises(catalog.FormalError):
            traces.load_trace(self.root, "counter", self.model, self.trace_path)

    def test_preview_requires_fresh_traces_and_reports_the_full_query(self) -> None:
        with patch.object(helper, "inspect_tool", return_value={"version": "fixture"}), patch.object(engine.shutil, "which", return_value=sys.executable):
            self.assertEqual("missing_trace", self.request()["data"]["verdict"])
            self.stamp()
            before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
            result = self.request()
            self.assertEqual("preview", result["data"]["verdict"], result)
            self.assertEqual("complete_observed_trace_reachable", result["data"]["trace_checks"]["counter"][0]["query"])
            self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()})
            (self.root / "formal/counter/counter.py").write_text("# changed implementation\n")
            self.assertEqual("stale_trace", self.request()["data"]["verdict"])

    def test_incomplete_trace_receipt_and_changed_raw_trace_block_resume(self) -> None:
        self.stamp()
        receipt = {"path": self.trace_path, "sha256": catalog.digest(self.root / self.trace_path), "verdict": "pass", "states": 4,
                   "transitions": 3, "exit_code": 12, "query": "complete_observed_trace_reachable"}
        result = {"model": "counter", "verdict": "pass", "obligations": [{"id": "bounded", "verdict": "pass", "exit_code": 0}], "traces": [receipt]}
        with patch.object(helper, "inspect_tool", return_value={"version": "fixture"}), patch.object(engine.shutil, "which", return_value=sys.executable), patch.object(helper, "execute_model", return_value=result):
            self.assertEqual("pass", self.request("apply")["data"]["verdict"])
            self.assertTrue(helper.current_checkpoint(self.root, "workflow.md", "final")["complete"])
            record = read_checkpoint(self.root, "workflow.md", "final")
            for field in ("transitions", "states", "sha256", "query"):
                damaged = copy.deepcopy(record)
                damaged["results"][0]["traces"][0].pop(field)
                record_path(self.root, "workflow.md", "final").write_text(json.dumps(damaged))
                self.assertFalse(helper.current_checkpoint(self.root, "workflow.md", "final")["complete"])
            record_path(self.root, "workflow.md", "final").write_text(json.dumps(record))
            self.stamp(self.observed((0, 2, 2)))
            self.assertFalse(helper.current_checkpoint(self.root, "workflow.md", "final")["complete"])


class NativeTraceTests(TraceFixture):
    def profile(self, checker: str) -> None:
        assert OPTIONS is not None
        jar = OPTIONS.tlc_jar if checker == "tlc" else OPTIONS.apalache_jar
        self.tools[checker] = {"version": "1.7.4" if checker == "tlc" else "0.62.2", "jar": str(Path(jar).resolve()),
                               "sha256": catalog.digest(Path(jar)), "java": "java", "heap_mb": 4096}
        self.model["checker"] = checker
        if checker == "tlc":
            self.model.update(mode="finite", bounds={"max_set_size": 1000000})
        self.save_catalog()

    def produce(self, language: str, start: int = 0, limit: int = 2) -> dict:
        source = self.root / "formal/counter"
        before = traces.binding(self.root, "counter")
        if language == "python":
            completed = subprocess.run([sys.executable, str(source / "counter.py"), str(start), str(limit)], check=True, capture_output=True, text=True, timeout=30)
        elif language == "typescript":
            compiler = Path(OPTIONS.typescript_compiler)
            subprocess.run(["node", str(compiler), "--noEmit", "--strict", "--target", "es2022", "--module", "nodenext",
                            "--ignoreConfig", "--types", "node", "--typeRoots", OPTIONS.typescript_type_roots, str(source / "counter.mts")], check=True, capture_output=True, text=True, timeout=30)
            completed = subprocess.run(["node", str(source / "counter.mts"), str(start), str(limit)], check=True, capture_output=True, text=True, timeout=30)
        else:
            executable = source / "counter-swift"
            subprocess.run(["swiftc", "-strict-concurrency=complete", "-warnings-as-errors", "-module-cache-path", str(self.root / "swift-cache"),
                            str(source / "CounterTrace.swift"), "-o", str(executable)], check=True, capture_output=True, text=True, timeout=120)
            completed = subprocess.run(["swift", "-module-cache-path", str(self.root / "swift-cache"), str(source / "CounterTrace.swift"), str(start), str(limit)], check=True, capture_output=True, text=True, timeout=30)
        trace = json.loads(completed.stdout)
        traces.write_trace(self.root, "counter", self.trace_path, trace, before)
        return trace

    def test_native_three_languages_and_seeded_implementation_defects(self) -> None:
        self.profile(OPTIONS.checker)
        for language, filename, old, new in (("python", "counter.py", "self.count += 1", "self.count += 2"),
                                             ("typescript", "counter.mts", "this.count += 1n", "this.count += 2n"),
                                             ("swift", "CounterTrace.swift", "count += 1", "count += 2")):
            with self.subTest(language=language):
                self.produce(language)
                result = self.request("apply")
                self.assertEqual("pass", result["data"]["verdict"], result)
                self.assertTrue(helper.current_checkpoint(self.root, "workflow.md", "final")["complete"])
                source = self.root / "formal/counter" / filename
                original = source.read_text()
                self.assertIn(old, original)
                source.write_text(original.replace(old, new))
                trace = self.produce(language)
                self.assertTrue(all(0 <= int(s["count"]["#bigint"]) <= 2 for s in trace["states"]))
                result = self.request("apply")
                self.assertEqual("trace_violation", result["data"]["verdict"], result)
                self.assertEqual("pass", result["data"]["results"][0]["obligations"][0]["verdict"])
                source.write_text(original)

    def test_native_large_integer_has_no_javascript_precision_loss(self) -> None:
        self.profile("apalache")
        start = 9007199254740993
        (self.root / self.model["config"]).write_text(f"CONSTANTS Start = {start}\n Limit = {start + 2}\nINIT Init\nNEXT Next\nINVARIANT Bounded\n")
        for language in ("python", "typescript", "swift"):
            with self.subTest(language=language):
                trace = self.produce(language, start, start + 2)
                self.assertEqual(str(start), trace["states"][0]["count"]["#bigint"])
                result = self.request("apply")
                self.assertEqual("pass", result["data"]["verdict"], result)

    def test_native_entire_sequence_preserves_hidden_state(self) -> None:
        self.profile(OPTIONS.checker)
        path = self.root / self.model["module"]
        path.write_text("---- MODULE Counter ----\nEXTENDS Integers\nCONSTANT\n \\* @type: Int;\n Start\nCONSTANT\n \\* @type: Int;\n Limit\nVARIABLE\n \\* @type: Int;\n count\nVARIABLE\n \\* @type: Int;\n hidden\n"
                        "Init == count = 0 /\\ hidden = 0\nIncrement == (count = 0 /\\ count' = 1 /\\ hidden' = 1) \\/ (count = 1 /\\ hidden = 0 /\\ count' = 2 /\\ hidden' = 0)\n"
                        "Hold == UNCHANGED <<count, hidden>>\nNext == Increment \\/ Hold\nBounded == count >= 0 /\\ count <= 2\n====\n")
        self.stamp(self.observed((0, 1, 2)))
        result = self.request("apply")
        self.assertEqual("trace_violation", result["data"]["verdict"], result)

    def test_native_quint_models_constrain_observed_implementation(self) -> None:
        self.profile("apalache")
        source = PLUGIN_ROOT / "skills/speckit-coach/examples/formal/counter-quint"
        shutil.copytree(source, self.root / "formal/quint")
        self.model.update(language="quint", main="Counter", init="init", next="step", module="formal/quint/Counter.qnt", config="formal/quint/Counter.cfg",
                          inputs=["formal/quint/Counter.qnt", "formal/quint/Counter.cfg"])
        self.model["trace"].update(init="init", next="step")
        self.tools["quint"] = {"version": "0.32.0", "root": str(Path(OPTIONS.quint_root).resolve()),
                               "tree_sha256": quint.tree_digest(Path(OPTIONS.quint_root)), "node": "node"}
        self.save_catalog()
        self.produce("python")
        result = self.request("apply")
        self.assertEqual("pass", result["data"]["verdict"], result)
        self.stamp(self.observed((0, 2, 2)))
        result = self.request("apply")
        self.assertEqual("trace_violation", result["data"]["verdict"], result)

    def test_native_supported_itf_collections_and_scalars(self) -> None:
        self.profile(OPTIONS.checker)
        values = {
            "flag": ("Bool", True), "label": ("Str", "lambda λ"),
            "sequence": ("Seq(Int)", [{"#bigint": "1"}, {"#bigint": "2"}]),
            "pair": ("<<Int, Bool>>", {"#tup": [{"#bigint": "1"}, True]}),
            "bag": ("Set(Int)", {"#set": [{"#bigint": "2"}, {"#bigint": "1"}]}),
            "lookup": ("Int -> Str", {"#map": [[{"#bigint": "1"}, "one"]]}),
            "record": ("{name: Str}", {"name": "Ada"}),
        }
        declarations = "\n".join(f"VARIABLE\n \\* @type: {hint};\n {name}" for name, (hint, _) in values.items())
        initial = " /\\ ".join(f"{name} = {itf.literal(value)}" for name, (_, value) in values.items())
        path = self.root / self.model["module"]
        path.write_text("---- MODULE Counter ----\nEXTENDS Integers, TLC\n" + declarations + "\nInit == " + initial + "\nHold == UNCHANGED <<" + ", ".join(values) + ">>\nNext == Hold\nBounded == TRUE\n====\n")
        (self.root / self.model["config"]).write_text("INIT Init\nNEXT Next\nINVARIANT Bounded\n")
        self.model["trace"].update(projection={name: name for name in values}, actions={"hold": "Hold"})
        self.save_catalog()
        rows = [{"#meta": {"index": i, **({"action": "hold"} if i else {})}, **{name: value for name, (_, value) in values.items()}} for i in range(2)]
        self.stamp({"vars": list(values), "states": rows})
        result = self.request("apply")
        self.assertEqual("pass", result["data"]["verdict"], result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apalache-jar")
    parser.add_argument("--tlc-jar")
    parser.add_argument("--quint-root")
    parser.add_argument("--typescript-compiler", help="Installed TypeScript bin/tsc path (native qualification only)")
    parser.add_argument("--typescript-type-roots", help="Installed @types directory containing Node.js declarations")
    parser.add_argument("--checker", choices=("apalache", "tlc"), default="apalache")
    OPTIONS = parser.parse_args()
    if OPTIONS.checker == "tlc" and not OPTIONS.tlc_jar:
        parser.error("--checker=tlc requires --tlc-jar")
    if OPTIONS.apalache_jar and not (OPTIONS.typescript_compiler and OPTIONS.typescript_type_roots):
        parser.error("native trace qualification requires explicit TypeScript compiler and type-root paths")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TraceContractTests)
    if OPTIONS.apalache_jar:
        suite.addTest(NativeTraceTests("test_native_three_languages_and_seeded_implementation_defects"))
        suite.addTest(NativeTraceTests("test_native_entire_sequence_preserves_hidden_state"))
        suite.addTest(NativeTraceTests("test_native_supported_itf_collections_and_scalars"))
        if OPTIONS.checker == "apalache":
            suite.addTest(NativeTraceTests("test_native_large_integer_has_no_javascript_precision_loss"))
        if OPTIONS.quint_root:
            suite.addTest(NativeTraceTests("test_native_quint_models_constrain_observed_implementation"))
    raise SystemExit(run_counted(suite, label="test-formal-traces"))
