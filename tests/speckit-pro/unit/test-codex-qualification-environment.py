#!/usr/bin/env python3
"""Focused tests for G56R-003 pre-execution environment contracts."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = (
    ROOT
    / "tests/speckit-pro/layer6-efficiency/lib/qualification_environment.py"
)
SCHEMA_PATH = (
    ROOT
    / "tests/speckit-pro/layer6-efficiency/contracts/environment-contract.schema.json"
)
RUNNER_PATH = (
    ROOT
    / "tests/speckit-pro/layer6-efficiency/run-codex-qualification.py"
)
SMOKE_RUNNER_PATH = (
    ROOT
    / "tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py"
)


def load_module():
    name = f"_g56r_003_environment_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


environment = load_module()


def draft_contract() -> dict:
    return {
        "client_version_range": {
            "minimum": "codex-cli 0.145.0",
            "maximum": "codex-cli 0.145.0",
        },
        "parent_session": {
            "model": "gpt-5.6-sol",
            "effort": "low",
        },
        "controlled_runtime_overrides": {
            field: True for field in environment.CONTROLLED_OVERRIDE_FIELDS
        },
        "authentication_mode": "chatgpt_subscription",
        "ultra_state": "off",
        "frozen_at": "2026-07-26T00:00:00-05:00",
    }


def conforming_observation(contract: dict) -> dict:
    return {
        "client_version": "codex-cli 0.145.0",
        "parent_session": copy.deepcopy(contract["parent_session"]),
        "controlled_runtime_overrides": copy.deepcopy(
            contract["controlled_runtime_overrides"]
        ),
        "authentication_mode": contract["authentication_mode"],
        "ultra_state": "off",
        "observed_at": "2026-07-26T00:01:00-05:00",
    }


class CodexQualificationEnvironmentTests(unittest.TestCase):
    def test_schema_and_runtime_freeze_the_same_observe_only_contract(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            environment.ENVIRONMENT_CONTRACT_SCHEMA_VERSION,
        )
        self.assertEqual(schema["properties"]["ultra_state"], {"const": "off"})
        self.assertEqual(
            set(
                schema["properties"]["controlled_runtime_overrides"]["required"]
            ),
            set(environment.CONTROLLED_OVERRIDE_FIELDS),
        )
        frozen = environment.freeze_environment_contract(draft_contract())
        self.assertEqual(
            environment.validate_environment_contract(frozen),
            frozen,
        )
        self.assertEqual(
            environment.environment_contract_binding(frozen),
            {
                "id": frozen["environment_contract_id"],
                "digest": frozen["environment_contract_digest"],
            },
        )

    def test_conformance_distinguishes_divergence_from_unobservable_evidence(self) -> None:
        frozen = environment.freeze_environment_contract(draft_contract())
        observed = conforming_observation(frozen)
        self.assertEqual(
            environment.evaluate_environment_conformance(
                frozen,
                observed,
            )["status"],
            "conforming",
        )
        ultra = copy.deepcopy(observed)
        ultra["ultra_state"] = "on"
        diverged = environment.evaluate_environment_conformance(frozen, ultra)
        self.assertEqual(diverged["status"], "diverged")
        self.assertEqual(diverged["failure_plane"], "treatment")
        self.assertEqual(
            diverged["failure_code"],
            "treatment_infrastructure_failure",
        )
        missing = copy.deepcopy(observed)
        del missing["authentication_mode"]
        unobservable = environment.evaluate_environment_conformance(
            frozen,
            missing,
        )
        self.assertEqual(unobservable["status"], "unobservable")
        self.assertEqual(unobservable["failure_plane"], "evidence_boundary")
        self.assertEqual(
            unobservable["failure_code"],
            "required_evidence_missing",
        )

    def test_authentication_modes_are_pinned_not_silently_substituted(self) -> None:
        frozen = environment.freeze_environment_contract(draft_contract())
        api_key = conforming_observation(frozen)
        api_key["authentication_mode"] = "api_key"
        result = environment.evaluate_environment_conformance(frozen, api_key)
        self.assertFalse(result["score_eligible"])
        self.assertIn("authentication mode", " ".join(result["findings"]))
        api_contract = draft_contract()
        api_contract["authentication_mode"] = "api_key"
        api_frozen = environment.freeze_environment_contract(api_contract)
        api_observation = conforming_observation(api_frozen)
        self.assertTrue(
            environment.evaluate_environment_conformance(
                api_frozen,
                api_observation,
            )["score_eligible"]
        )

    def test_codex_harness_and_shipped_payload_never_enable_or_disable_ultra(self) -> None:
        runner_source = RUNNER_PATH.read_text(encoding="utf-8").lower()
        smoke_source = SMOKE_RUNNER_PATH.read_text(encoding="utf-8").lower()
        shipped_sources = "\n".join(
            path.read_text(encoding="utf-8", errors="replace").lower()
            for path in (ROOT / "speckit-pro").rglob("*")
            if path.is_file() and path.suffix in {".py", ".toml", ".md", ".json"}
        )
        self.assertNotIn('model_reasoning_effort="ultra"', runner_source)
        self.assertNotIn('model_reasoning_effort = "ultra"', smoke_source)
        self.assertNotIn('model_reasoning_effort = "ultra"', shipped_sources)
        self.assertNotIn("enable_ultra", runner_source + smoke_source + shipped_sources)
        self.assertNotIn("disable_ultra", runner_source + smoke_source + shipped_sources)
        self.assertNotIn("set_ultra", runner_source + smoke_source + shipped_sources)
        self.assertEqual(
            tuple(
                value
                for value in ("xhigh", "high", "medium", "low")
                if value in smoke_source
            ),
            ("xhigh", "high", "medium", "low"),
        )


if __name__ == "__main__":
    unittest.main()
