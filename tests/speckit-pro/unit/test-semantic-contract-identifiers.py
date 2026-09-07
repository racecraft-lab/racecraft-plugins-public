#!/usr/bin/env python3
"""Owner tests for semantic persisted-contract identifiers."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
sys.path.insert(0, str(PLUGIN_ROOT))
sys.path.insert(0, str(TEST_ROOT / "lib"))

from speckit_pro_runner.envelope import RunnerRequest  # noqa: E402
from speckit_pro_runner.gates import registry  # noqa: E402
from test_result import run_counted  # noqa: E402


class SemanticContractIdentifierTests(unittest.TestCase):
    def test_release_dispatch_uses_semantic_operations_and_rejects_unknown_inputs(self) -> None:
        release_operations = {
            item.operation for item in registry.GATE_OPERATIONS if item.group == "release"
        }
        self.assertEqual(
            release_operations,
            {"installed-release-readiness", "validate-pr-title"},
        )
        canonical = RunnerRequest(
            request_id="opaque/external id",
            helper_id="release-readiness",
            operation="installed-release-readiness",
            mode="read_only",
            inputs={},
        )
        registered = next(
            item for item in registry.GATE_OPERATIONS
            if item.operation == canonical.operation
        )
        self.assertEqual(registered.helper_id, canonical.helper_id)
        unknown_operation = copy.deepcopy(canonical)
        object.__setattr__(unknown_operation, "operation", "unregistered-release-operation")
        self.assertEqual(registry.dispatch_gate(unknown_operation)["status"], "input_error")
        for invalid in (False, True, "false", 0, None):
            bad = copy.deepcopy(canonical)
            object.__setattr__(bad, "inputs", {"unexpected_input": invalid})
            self.assertEqual(registry.dispatch_gate(bad)["status"], "input_error", invalid)

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SemanticContractIdentifierTests)
    raise SystemExit(run_counted(suite, label="test-semantic-contract-identifiers"))
