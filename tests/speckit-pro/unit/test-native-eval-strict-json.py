#!/usr/bin/env python3
"""One strict JSON contract holds in every native-eval path."""
from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import types
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
        binding = strict_json.ReceiptBinding("controller_rows", "schema/v1", "authority", ValueError)
        strict_json.attach_receipt(observation, [{"check_id": "one"}], binding)
        self.assertEqual(observation["native_metadata"]["controller_rows"], {
            "schema": "schema/v1", "authority": "authority", "checks": [{"check_id": "one"}],
        })
        for candidate in (observation, {}):
            with self.assertRaises(ValueError):
                strict_json.attach_receipt(candidate, [], binding)


class NonFiniteConstantTests(unittest.TestCase):
    """NaN and Infinity are the only defect in each payload below."""

    def test_every_native_path_rejects_the_constants(self) -> None:
        receipt_settings = {"receipt_relative_path": "payload.json", "expected_result": {}}

        def manifest(root: Path, payload: Path) -> None:
            payload.rename(root / ".codex-plugin" / "plugin.json")
            adapters._codex_native_skill_reference(root, "native-skill")

        # name: (payload template, read the payload, expected error class, expected message)
        paths = {
            "codex manifest": (
                '{"name":"speckit-pro","extra":CONSTANT}', manifest,
                adapters.NativeAdapterError, "manifest is unavailable"),
            "claude framework result": (
                '{"schemaVersion":1,"extra":CONSTANT}',
                lambda root, payload: adapters._read_claude_result(
                    types.SimpleNamespace(result_path=payload)),
                adapters.NativeAdapterError, "result is malformed"),
            "claude fixture receipt": (
                '{"extra":CONSTANT}',
                lambda root, payload: adapters._read_claude_fixture_receipt(
                    types.SimpleNamespace(cwd=root), receipt_settings),
                adapters.NativeAdapterError, "receipt is malformed"),
            "store receipt": (
                '{"payload":{"n":CONSTANT},"sha256":"' + "0" * 64 + '"}',
                lambda root, payload: store._read(payload),
                store.StoreError, "invalid JSON constant"),
            "fixture plan": (
                '{"extra":CONSTANT}', lambda root, payload: fixture_setup.load_plan(payload),
                ValueError, "fixture plan could not be read"),
        }
        for name, (template, read, error, pattern) in paths.items():
            for constant in CONSTANTS:
                with self.subTest(path=name, constant=constant):
                    root = Path(self.enterContext(tempfile.TemporaryDirectory()))
                    (root / ".codex-plugin").mkdir()
                    payload = root / "payload.json"
                    payload.write_text(template.replace("CONSTANT", constant), encoding="utf-8")
                    os.chmod(payload, 0o600)
                    with self.assertRaisesRegex(error, pattern):
                        read(root, payload)


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-native-eval-strict-json"))
