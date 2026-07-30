#!/usr/bin/env python3
"""Route availability, fallback, and recovery simulation: contracts, walk, and replay.

This module is the deterministic coverage for the reference route-resolution
simulator — the preferred-then-fallback walk, the two closed reason-code
vocabularies, the closed effort ladder, and the byte-identical replay of a pinned
scenario corpus.

Contract-structural cases read the three committed schema documents under
``tests/speckit-pro/layer6-efficiency/contracts-claude/``; module-contract cases
exercise ``tests/speckit-pro/layer6-efficiency/lib/claude_route_fallback.py``.

Every check is offline: the simulator is a pure function of a synthetic
environment snapshot, so this module makes zero live model calls and performs no
dispatch.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
LIB_DIR = TEST_ROOT / "lib"
LAYER6_LIB_DIR = TEST_ROOT / "layer6-efficiency" / "lib"
for _path in (LIB_DIR, LAYER6_LIB_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from test_result import run_counted  # noqa: E402

# The shared fail-closed schema engine, imported read-only: it is the loader every
# consumer of this contracts directory already goes through, so these cases check
# the committed documents against the engine that will validate instances against
# them rather than against a second reader authored here.
from claude_policy_controls import load_contract  # noqa: E402

# FR-014a: the ONE canonical serializer, imported rather than re-declared. This is a
# deliberate break with local habit — all six existing canonical_json occurrences
# under unit/ define their own copy, and two of those append a trailing newline the
# library function does not. A local copy here would be a second serializer, and
# because the pinning comparison passes the pinned report through the same local
# copy, a discrepancy against the simulator's real output would CANCEL rather than
# fail.
from claude_successor_freeze import canonical_json  # noqa: E402

try:  # CAR-005 deliverable — absent until the simulator module is implemented.
    import claude_route_fallback  # type: ignore[import-not-found]  # noqa: E402
except ImportError:  # pragma: no cover - exercised only before the module lands
    claude_route_fallback = None  # type: ignore[assignment]


CONTRACT_ROOT = TEST_ROOT / "layer6-efficiency" / "contracts-claude"
JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_ID_PREFIX = "https://racecraft.dev/schemas/car-005/"
SCHEMA_VERSION = "1.0.0"

# The three documents FR-016 permits, and exactly three: no fourth
# shared-definitions document exists, because a cross-document ``$ref`` is what a
# shared document would require and the engine refuses one.
CONTRACT_FILENAMES = (
    "route-policy.schema.json",
    "environment-snapshot-projection.schema.json",
    "route-resolution-report.schema.json",
)


class CommittedContractIdentityTests(unittest.TestCase):
    """FR-016: three committed documents, each self-identifying and version-pinned.

    Identity is asserted before shape because every later case reads one of these
    documents by name. A document that is absent, malformed, or carrying another
    feature's ``$id`` would otherwise surface as a confusing shape failure rather
    than as the missing contract it is.
    """

    def load(self, filename: str) -> dict[str, object]:
        path = CONTRACT_ROOT / filename
        self.assertTrue(path.is_file(), f"{filename} is not committed under contracts-claude/")
        return load_contract(path)

    def test_the_three_documents_are_committed_and_load_through_the_shared_engine(self) -> None:
        for filename in CONTRACT_FILENAMES:
            with self.subTest(document=filename):
                self.assertIsInstance(self.load(filename), dict)

    def test_each_document_declares_the_shared_json_schema_dialect(self) -> None:
        for filename in CONTRACT_FILENAMES:
            with self.subTest(document=filename):
                self.assertEqual(self.load(filename).get("$schema"), JSON_SCHEMA_DIALECT)

    def test_each_document_identifies_itself_by_its_capability_named_id(self) -> None:
        for filename in CONTRACT_FILENAMES:
            with self.subTest(document=filename):
                self.assertEqual(self.load(filename).get("$id"), SCHEMA_ID_PREFIX + filename)

    def test_each_document_pins_its_schema_version_with_const(self) -> None:
        for filename in CONTRACT_FILENAMES:
            with self.subTest(document=filename):
                properties = self.load(filename).get("properties")
                self.assertIsInstance(properties, dict)
                self.assertEqual(properties.get("schema_version"), {"const": SCHEMA_VERSION})


class SimulatorSerializationSurfaceTests(unittest.TestCase):
    """FR-014a and FR-030: the module's serialization surface and its fail-closed helper.

    Serialization is asserted before any walk exists because it is what every later
    byte comparison runs through. A serializer that appended a trailing newline, or
    that a local copy shadowed, would make replay byte-identity unfalsifiable rather
    than merely wrong.
    """

    def setUp(self) -> None:
        self.assertIsNotNone(claude_route_fallback, "claude_route_fallback is not importable")
        self.module = claude_route_fallback

    def test_serialize_report_returns_the_shared_canonical_serializer_output(self) -> None:
        report = {"outcome": "resolved", "agent": "fixture-required-executor", "diagnostics": []}
        self.assertEqual(self.module.serialize_report(report), canonical_json(report))

    def test_serialize_report_appends_no_trailing_newline(self) -> None:
        serialized = self.module.serialize_report({"outcome": "no_safe_route"})
        self.assertFalse(serialized.endswith("\n"))

    def test_serialize_report_sorts_keys_so_dict_order_never_reaches_the_bytes(self) -> None:
        forward = self.module.serialize_report({"agent": "fixture-bounded-analyst", "outcome": "resolved"})
        reverse = self.module.serialize_report({"outcome": "resolved", "agent": "fixture-bounded-analyst"})
        self.assertEqual(forward, reverse)
        self.assertEqual(forward, '{"agent":"fixture-bounded-analyst","outcome":"resolved"}')

    def test_the_module_declares_both_closed_vocabularies_and_the_sub_reason_order(self) -> None:
        report_schema = load_contract(CONTRACT_ROOT / "route-resolution-report.schema.json")
        definitions = report_schema["$defs"]
        self.assertEqual(
            list(self.module.RESOLUTION_CODES),
            definitions["resolutionDiagnostic"]["properties"]["code"]["enum"],
        )
        self.assertEqual(
            list(self.module.POLICY_VIOLATION_CODES),
            definitions["policyViolationDiagnostic"]["properties"]["code"]["enum"],
        )
        self.assertEqual(
            list(self.module.SUB_REASON_ORDER),
            definitions["resolutionDiagnostic"]["properties"]["details"]["properties"]["sub_reason"]["enum"],
        )

    def test_the_fail_closed_helper_raises_rather_than_returning_a_partial_verdict(self) -> None:
        self.assertTrue(issubclass(self.module.RouteFallbackError, AssertionError))
        self.assertIsNone(self.module._require(True, "a satisfied condition returns nothing"))
        with self.assertRaises(self.module.RouteFallbackError):
            self.module._require(False, "an unsatisfied condition raises")


TEST_CASES = (CommittedContractIdentityTests, SimulatorSerializationSurfaceTests)


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for case in TEST_CASES:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    return suite


if __name__ == "__main__":
    raise SystemExit(run_counted(build_suite(), label="test-route-fallback-simulation"))
