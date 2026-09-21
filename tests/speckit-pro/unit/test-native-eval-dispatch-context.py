#!/usr/bin/env python3
"""Privacy-preserving native dispatch-context qualification."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest


TEST_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TEST_ROOT / "lib"))

from native_eval_dispatch_context import (  # noqa: E402
    DispatchContextProofError,
    MAX_CONTEXTS,
    MAX_CONTEXT_BYTES,
    MAX_CONTEXT_TOTAL_BYTES,
    MAX_JSON_CANDIDATES,
    MAX_JSON_DEPTH,
    MAX_MESSAGE_BYTES,
    MAX_PRECEDING_JSON_BYTES,
    decode_sealed_plan_repair_message,
    qualify_native_dispatch_context,
)
from test_result import run_counted  # noqa: E402


PROMPT = "Design the outline workflow and preserve the human timing decision."
ARCHITECTURE = "The current client exposes no verified visible-delivery callback."
G3 = {
    "schema_version": "1.0",
    "status": "expected_failure",
    "data": {"stdout_json": {"gate": "G3", "pass": False, "markers": 1}},
    "exit_code": 1,
}


class NativeEvalDispatchContextTests(unittest.TestCase):
    def qualify(self, message: str, contexts: dict[str, str] | None = None,
                preceding: object = G3) -> dict[str, object]:
        return qualify_native_dispatch_context(
            message,
            contexts if contexts is not None else {
                "original-plan": PROMPT, "architecture": ARCHITECTURE,
            },
            preceding,
        )

    def test_exact_contexts_and_reserialized_complete_json_match(self) -> None:
        reserialized = json.dumps(G3, indent=2, sort_keys=False)
        message = f"Plan prompt:\n{PROMPT}\nArchitecture:\n{ARCHITECTURE}\nG3:\n{reserialized}"

        result = self.qualify(
            message,
            {"original-plan": f"\n  {PROMPT} \n", "architecture": ARCHITECTURE},
        )

        self.assertEqual(result, {
            "message_sha256": hashlib.sha256(message.encode("utf-8")).hexdigest(),
            "message_bytes": len(message.encode("utf-8")),
            "observed_context_ids": ["architecture", "original-plan"],
            "complete_preceding_json_found": True,
        })

    def test_missing_wrong_partial_context_and_prior_mismatch_are_nonmatches(self) -> None:
        scenarios = {
            "missing": (f"{ARCHITECTURE}\n{json.dumps(G3)}", ["architecture"], True),
            "wrong": (
                f"{PROMPT.replace('human', 'operator')}\n{json.dumps(G3)}", [], True,
            ),
            "partial": (f"{PROMPT[:20]}\n{json.dumps(G3)}", [], True),
            "prior-mismatch": (
                f"{PROMPT}\n{ARCHITECTURE}\n{json.dumps({**G3, 'exit_code': 0})}",
                ["architecture", "original-plan"], False,
            ),
        }
        for label, (message, observed, found) in scenarios.items():
            with self.subTest(label=label):
                result = self.qualify(message)
                self.assertEqual(result["observed_context_ids"], observed)
                self.assertIs(result["complete_preceding_json_found"], found)

    def test_json_comparison_is_type_strict_for_boolean_and_integer(self) -> None:
        prior = {"gate": "G3", "pass": True, "markers": 1}
        result = self.qualify(
            json.dumps({"gate": "G3", "pass": 1, "markers": 1}),
            {"context": "not present"},
            prior,
        )
        self.assertIs(result["complete_preceding_json_found"], False)

    def test_nested_only_object_does_not_count_as_complete_envelope(self) -> None:
        nested = G3["data"]["stdout_json"]
        message = f"Only nested result: {json.dumps(nested)}"
        self.assertIs(self.qualify(message)["complete_preceding_json_found"], False)

    def test_duplicate_and_nonfinite_embedded_json_are_rejected_as_nonmatches(self) -> None:
        messages = (
            '{"schema_version":"1.0","exit_code":1,"exit_code":0}',
            '{"schema_version":"1.0","value":NaN}',
            '{"schema_version":"1.0","value":Infinity}',
        )
        for message in messages:
            with self.subTest(message=message):
                self.assertIs(self.qualify(message)["complete_preceding_json_found"], False)

    def test_escaped_braces_and_quotes_are_decoded_safely(self) -> None:
        prior = {"note": 'literal { brace and "quote"', "pass": False}
        message = "Context follows: " + json.dumps(prior)
        result = self.qualify(message, {"context": "Context follows:"}, prior)
        self.assertTrue(result["complete_preceding_json_found"])

    def test_input_and_candidate_bounds_fail_explicitly(self) -> None:
        cases = {
            "message": ("x" * (MAX_MESSAGE_BYTES + 1), {"context": "x"}, G3),
            "context-count": (
                "message", {f"context-{index}": "x" for index in range(MAX_CONTEXTS + 1)}, G3,
            ),
            "context-bytes": ("message", {"context": "x" * (MAX_CONTEXT_BYTES + 1)}, G3),
            "context-total": (
                "message",
                {
                    f"context-{index}": "x" * MAX_CONTEXT_BYTES
                    for index in range((MAX_CONTEXT_TOTAL_BYTES // MAX_CONTEXT_BYTES) + 1)
                },
                G3,
            ),
            "json-candidates": ("[" * (MAX_JSON_CANDIDATES + 1), {"context": "x"}, G3),
            "preceding-json": (
                "message", {"context": "x"}, {"payload": "x" * MAX_PRECEDING_JSON_BYTES},
            ),
        }
        for label, arguments in cases.items():
            with self.subTest(label=label):
                with self.assertRaises(DispatchContextProofError):
                    qualify_native_dispatch_context(*arguments)

    def test_malformed_trusted_configuration_raises(self) -> None:
        malformed = (
            ({}, G3),
            ({"Bad ID": "text"}, G3),
            ({"context": " \n\t "}, G3),
            ({"context": "text"}, {"value": float("nan")}),
            ({"context": "text"}, ("not", "json")),
        )
        for contexts, prior in malformed:
            with self.subTest(contexts=contexts, prior=prior):
                with self.assertRaises(DispatchContextProofError):
                    self.qualify("message", contexts, prior)

        nested: object = {"leaf": True}
        for _ in range(MAX_JSON_DEPTH + 1):
            nested = {"next": nested}
        with self.assertRaises(DispatchContextProofError):
            self.qualify("message", {"context": "text"}, nested)

    def test_ciphertext_shaped_message_never_leaks_raw_evidence(self) -> None:
        ciphertext = "age1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq"
        message = f"{ciphertext}\n{PROMPT}\n{json.dumps(G3)}"
        result = self.qualify(message, {"original-plan": PROMPT})
        encoded = json.dumps(result, sort_keys=True)

        self.assertEqual(set(result), {
            "message_sha256", "message_bytes", "observed_context_ids",
            "complete_preceding_json_found",
        })
        self.assertNotIn(ciphertext, encoded)
        self.assertNotIn(PROMPT, encoded)
        self.assertNotIn("stdout_json", encoded)


class SealedPlanRepairMessageTests(unittest.TestCase):
    @staticmethod
    def _build_envelope() -> tuple[dict[str, object], str]:
        context_digest = "b" * 64
        executor_message = (
            f"{PROMPT}\n{ARCHITECTURE}\n{json.dumps(G3)}\n"
            f"PLAN_REPAIR_CONTEXT_SHA256={context_digest}"
        )
        body = executor_message.encode("utf-8")
        rendered = {
            "schema": "plan-repair-executor-message/v1",
            "executor_message": executor_message,
            "message_sha256": hashlib.sha256(body).hexdigest(),
            "message_bytes": len(body),
            "context_ids": ["architecture", "original-plan"],
            "g3_attempt_index": 0,
            "context_bundle_sha256": context_digest,
        }
        stdout_text = json.dumps(rendered, separators=(",", ":")) + "\n"
        envelope = {
            "schema_version": "1.0",
            "status": "ok",
            "exit_code": 0,
            "diagnostics": [],
            "data": {
                "helper_id": "render-plan-repair-context",
                "operation": "render-plan-repair-context",
                "mode": "read_only",
                "exit_code": 0,
                "writes_state": False,
                "stdin_request": {
                    "helper_id": "render-plan-repair-context",
                    "operation": "render-plan-repair-context",
                    "mode": "read_only",
                },
                "stdout": {
                    "text": stdout_text,
                    "byte_count": len(stdout_text.encode("utf-8")),
                    "truncated": False,
                },
                "stdout_json": rendered,
            },
        }
        return envelope, executor_message

    def test_decodes_hash_bound_executor_message(self) -> None:
        envelope, executor_message = self._build_envelope()
        transport = json.dumps(envelope, separators=(",", ":"))
        self.assertEqual(decode_sealed_plan_repair_message(transport), executor_message)
        proof = qualify_native_dispatch_context(
            decode_sealed_plan_repair_message(transport) or "",
            {"original-plan": PROMPT, "architecture": ARCHITECTURE},
            G3,
        )
        self.assertEqual(proof["observed_context_ids"], ["architecture", "original-plan"])
        self.assertTrue(proof["complete_preceding_json_found"])

    def test_rejects_mutated_envelope(self) -> None:
        envelope, _executor_message = self._build_envelope()
        for label, mutate in (
            ("hash", lambda value: value["data"]["stdout_json"].__setitem__("message_sha256", "0" * 64)),
            ("bytes", lambda value: value["data"]["stdout_json"].__setitem__("message_bytes", 1)),
            ("stdout", lambda value: value["data"]["stdout"].__setitem__("text", "{}\n")),
            ("status", lambda value: value.__setitem__("status", "expected_failure")),
        ):
            with self.subTest(label=label):
                candidate = json.loads(json.dumps(envelope))
                mutate(candidate)
                self.assertIsNone(
                    decode_sealed_plan_repair_message(
                        json.dumps(candidate, separators=(",", ":")),
                    )
                )


if __name__ == "__main__":
    suite = unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeEvalDispatchContextTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(SealedPlanRepairMessageTests),
    ))
    raise SystemExit(run_counted(
        suite,
        label="test-native-eval-dispatch-context",
    ))
