#!/usr/bin/env python3
"""One strict JSON contract holds in every native-eval path."""
from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest

TEST_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TEST_ROOT / "lib"))

import native_eval_adapters as adapters  # noqa: E402
import native_eval_fixture_setup as fixture_setup  # noqa: E402
import native_eval_store as store  # noqa: E402
from test_result import run_counted  # noqa: E402

CONSTANTS = ("NaN", "Infinity", "-Infinity")


class HelperTests(unittest.TestCase):
    def setUp(self) -> None:
        import native_eval_strict_json as strict_json
        self.strict_json = strict_json

    def test_loads_accepts_plain_json_text_and_bytes(self) -> None:
        self.assertEqual(self.strict_json.loads('{"a":[1,2.5,null]}', error=ValueError), {"a": [1, 2.5, None]})
        self.assertEqual(self.strict_json.loads(b'{"a":1}', error=ValueError), {"a": 1})

    def test_loads_raises_the_callers_error_class_for_every_defect(self) -> None:
        class CallerError(Exception):
            pass

        defects = ['{"a":1,"a":2}', '{"a":NaN}', '[Infinity]', '[-Infinity]', '{"a":',
                   "[" * 100000, b"\xff", ""]
        for text in defects:
            with self.subTest(text=str(text)[:20]):
                with self.assertRaises(CallerError):
                    self.strict_json.loads(text, error=CallerError)

    def test_loads_prefixes_the_label(self) -> None:
        with self.assertRaisesRegex(ValueError, "^receipt: "):
            self.strict_json.loads("[NaN]", error=ValueError, label="receipt")

    def test_stream_reads_concatenated_values_and_rejects_constants(self) -> None:
        self.assertEqual(self.strict_json.stream('{"a":1} [2]\n', error=ValueError), [{"a": 1}, [2]])
        for text in ('{"a":1} {"a":NaN}', '{"a":1', '{"a":1,"a":2}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.strict_json.stream(text, error=ValueError)

    def test_strict_equal_preserves_types_and_order(self) -> None:
        equal = self.strict_json.strict_equal
        self.assertTrue(equal({"a": [1, {"b": None}]}, {"a": [1, {"b": None}]}))
        self.assertFalse(equal(1, True))
        self.assertFalse(equal(1, 1.0))
        self.assertFalse(equal([1, 2], [2, 1]))
        self.assertFalse(equal({"a": 1}, {"a": 1, "b": 2}))


class ReceiptTests(unittest.TestCase):
    def test_attach_receipt_binds_once_under_the_callers_key(self) -> None:
        import native_eval_strict_json as strict_json
        observation = {"native_metadata": {}}
        strict_json.attach_receipt(
            observation, [{"check_id": "one"}], key="controller_rows",
            schema="schema/v1", authority="authority", error=ValueError,
        )
        self.assertEqual(observation["native_metadata"]["controller_rows"], {
            "schema": "schema/v1", "authority": "authority", "checks": [{"check_id": "one"}],
        })
        with self.assertRaises(ValueError):
            strict_json.attach_receipt(
                observation, [], key="controller_rows",
                schema="schema/v1", authority="authority", error=ValueError,
            )
        with self.assertRaises(ValueError):
            strict_json.attach_receipt(
                {}, [], key="controller_rows",
                schema="schema/v1", authority="authority", error=ValueError,
            )


class NonFiniteConstantTests(unittest.TestCase):
    """NaN and Infinity are the only defect in each payload below."""

    def setUp(self) -> None:
        self.temp = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def test_codex_plugin_manifest_rejects_constants(self) -> None:
        for index, constant in enumerate(CONSTANTS):
            with self.subTest(constant=constant):
                root = self.temp / str(index)
                (root / ".codex-plugin").mkdir(parents=True)
                (root / ".codex-plugin" / "plugin.json").write_text(
                    '{"name":"speckit-pro","extra":' + constant + "}", encoding="utf-8")
                with self.assertRaisesRegex(adapters.NativeAdapterError, "manifest is unavailable"):
                    adapters._codex_native_skill_reference(root, "native-skill")

    def test_claude_framework_result_rejects_constants(self) -> None:
        for index, constant in enumerate(CONSTANTS):
            with self.subTest(constant=constant):
                attempt = self.temp / ("result-" + str(index))
                attempt.mkdir()
                result = attempt / "result.json"
                result.write_text('{"schemaVersion":1,"extra":' + constant + "}", encoding="utf-8")
                prepared = adapters.PreparedTrial(
                    command=[], cwd=attempt, environment={}, host="claude", mode="plugin",
                    attempt_dir=attempt, trace_path=None, result_path=result,
                    artifact_root=None, runtime_identity={},
                )
                with self.assertRaisesRegex(adapters.NativeAdapterError, "result is malformed"):
                    adapters._read_claude_result(prepared)

    def test_claude_fixture_receipt_rejects_constants(self) -> None:
        for index, constant in enumerate(CONSTANTS):
            with self.subTest(constant=constant):
                attempt = self.temp / ("receipt-" + str(index))
                attempt.mkdir()
                receipt = attempt / "receipt.json"
                receipt.write_text('{"extra":' + constant + "}", encoding="utf-8")
                os.chmod(receipt, 0o600)
                prepared = adapters.PreparedTrial(
                    command=[], cwd=attempt, environment={}, host="claude", mode="plugin",
                    attempt_dir=attempt, trace_path=None, result_path=None,
                    artifact_root=None, runtime_identity={},
                )
                settings = {"receipt_relative_path": "receipt.json", "expected_result": {}}
                with self.assertRaisesRegex(adapters.NativeAdapterError, "receipt is malformed"):
                    adapters._read_claude_fixture_receipt(prepared, settings)

    def test_store_receipt_rejects_constants(self) -> None:
        for index, constant in enumerate(CONSTANTS):
            with self.subTest(constant=constant):
                path = self.temp / ("store-" + str(index) + ".json")
                path.write_text('{"payload":{"n":' + constant + '},"sha256":"' + "0" * 64 + '"}',
                                encoding="utf-8")
                with self.assertRaisesRegex(store.StoreError, "invalid JSON constant"):
                    store._read(path)

    def test_fixture_plan_rejects_constants(self) -> None:
        for index, constant in enumerate(CONSTANTS):
            with self.subTest(constant=constant):
                path = self.temp / ("plan-" + str(index) + ".json")
                path.write_text('{"extra":' + constant + "}", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "fixture plan could not be read"):
                    fixture_setup.load_plan(path)


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-native-eval-strict-json"))
