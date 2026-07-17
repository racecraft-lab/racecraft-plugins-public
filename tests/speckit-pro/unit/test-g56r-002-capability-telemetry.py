#!/usr/bin/env python3
"""Focused deterministic tests for the G56R-002 capability contract."""

from __future__ import annotations

import copy
import base64
import importlib.util
import itertools
import json
import os
import stat
import subprocess
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py"
FIXTURE_PATH = ROOT / "tests/speckit-pro/unit/fixtures/capability-treatment-replay/capability-matrix.json"
MANIFEST_PATH = ROOT / "docs/ai/research/codex-agent-route-candidate-manifest.json"

spec = importlib.util.spec_from_file_location("g56r_002_codex_capabilities", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {MODULE_PATH}")
capabilities = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capabilities)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def source_capture(manifest: dict, retrieved_at: str = "2026-07-16T00:00:00Z") -> list[dict]:
    captured = []
    for source in manifest["official_source_ledger"]:
        body = "\n".join(item["text"] for item in source["bounded_extracts"])
        prior = f"sha256:{source['body_sha256']}"
        current = capabilities.digest(body.encode())
        redirected = source["requested_url"] != source["canonical_url"]
        captured.append({
            "official_source_ledger_id": source["official_source_ledger_id"],
            "requested_url": source["requested_url"],
            "canonical_url": source["canonical_url"],
            "retrieved_at": retrieved_at,
            "status": "redirected" if redirected else "confirmed_current" if current == prior else "changed",
            "invalidated_claim_ids": [],
            "retrieved_body_b64": base64.b64encode(body.encode()).decode(),
            "bounded_extracts": copy.deepcopy(source["bounded_extracts"]),
        })
    return captured


def source_refreshes(manifest: dict, retrieved_at: str = "2026-07-16T00:00:00Z", *, synthetic: bool = False) -> list[dict]:
    return capabilities.normalize_source_refreshes(manifest, source_capture(manifest, retrieved_at), allow_synthetic_manifest=synthetic)


def canary_envelope() -> tuple[dict, dict]:
    contract_id = capabilities.digest({"executor": "fixture-v1"})
    implementation = capabilities.digest(b"fixture-executor")
    approval = {
        "executor_contract_id": contract_id,
        "contract_version": "1.0.0",
        "implementation_digest": implementation,
        "platform": "macos",
        "approval_evidence_digest": capabilities.digest(b"fixture-approval"),
    }
    result = {
        "snapshot_id": capabilities.digest({"snapshot": "fixture"}), "canonical_model_id": "model-a",
        "canonical_effort": "high", "attempt_index": 1, "timeout_seconds": 30,
        "combined_output_cap_bytes": 65536, "executor_contract_id": contract_id,
        "implementation_digest": implementation, "executor_result_digest": "",
        "contract_version": "1.0.0", "platform": "macos", "timeout_enforced": True, "output_cap_enforced": True,
        "process_tree_termination_state": "not_needed", "retry_count": 0, "exit_code": 0,
        "sentinel_observed": True, "terminal_class": "success",
        "availability_disposition": "available_for_pinned_environment", "evidence_digest": "",
    }
    result["evidence_digest"] = capabilities.digest(canary_evidence_bytes(result))
    result["executor_result_digest"] = capabilities.digest({key: value for key, value in result.items() if key not in {"executor_result_digest", "availability_disposition"}})
    return approval, result


def canary_evidence_bytes(result: dict) -> bytes:
    return capabilities.canonical_bytes({
        "schema_version": "1.0.0",
        "snapshot_id": result["snapshot_id"],
        "canonical_model_id": result["canonical_model_id"],
        "canonical_effort": result["canonical_effort"],
        "terminal_class": result["terminal_class"],
        "exit_code": result["exit_code"],
        "sentinel_observed": result["sentinel_observed"],
    }) + b"\n"


class CapabilityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = load_json(FIXTURE_PATH)
        cls.manifest = load_json(MANIFEST_PATH)
        cls.identity = capabilities.build_client_identity(cls.fixture["client_identity"])

    def observations(self, case: dict) -> list[dict]:
        return [
            capabilities.fixture_observation(surface, value, self.identity["client_identity_id"])
            for surface, value in case["surfaces"].items()
        ]

    def authority_tuples(self, case: dict) -> list[dict]:
        tuples = copy.deepcopy(case["source_tuples"])
        for item in tuples:
            instruction = capabilities.digest(b"fixture-instruction")
            item.update({
                "candidate_route_digest": capabilities.digest({"route": item["candidate_route_id"]}),
                "source_ref": "fixtures/fixture-agent.toml",
                "source_sha256": capabilities.digest(b"fixture-agent-source"),
                "instruction_sha256": instruction,
                "role_instruction_sha256": instruction,
                "agent_contract_digest": capabilities.digest(b"fixture-contract"),
                "official_source_bindings": [{
                    "official_source_ledger_id": "OPENAI-DOC-001",
                    "source_refresh_digest": capabilities.digest(b"fixture-source-refresh"),
                }],
                "effort_surface_bindings": [{
                    "effort_surface_record_id": "FIXTURE-ESR-001",
                    "effort_surface_record_digest": capabilities.digest(b"fixture-effort-record"),
                    "official_source_ledger_id": "OPENAI-DOC-001",
                    "source_refresh_digest": capabilities.digest(b"fixture-source-refresh"),
                }],
            })
        return capabilities._AuthorityTupleSet(tuples)

    def test_current_manifest_and_effort_authority_are_strict(self) -> None:
        result = capabilities.validate_manifest(self.manifest)
        self.assertEqual(result["current_source_count"], 22)
        self.assertEqual(result["historical_active_count"], 0)
        self.assertEqual(result["effort_surface_count"], 5)
        self.assertIn("G56R-001-ESR-003", result["quarantined_effort_record_ids"])
        self.assertNotIn(",", result["authoritative_effort_tokens"])
        api_only = copy.deepcopy(self.manifest)
        api_only["effort_surface_records"][-1].update({"support_status": "documented", "documented_values": ["high"]})
        api_only["candidate_routes"][0]["effort_selector"]["requested_value"] = "high"
        refreshes = source_refreshes(api_only, synthetic=True)
        route = capabilities.candidate_tuples_from_manifest(api_only, refreshes, allow_synthetic_manifest=True)[0]
        self.assertFalse(route["source_admitted"])
        self.assertIn("effort_not_source_admitted", route["authority_reasons"])
        missing_owner = copy.deepcopy(self.manifest)
        first_owner = missing_owner["candidate_routes"][0]["agent_contract_id"]
        missing_owner["agent_contracts"] = [
            item for item in missing_owner["agent_contracts"]
            if item["agent_contract_id"] != first_owner
        ]
        with self.assertRaisesRegex(ValueError, "canonical G56R-001"):
            capabilities.validate_manifest(missing_owner)
        with self.assertRaisesRegex(ValueError, "agent-contract owners"):
            capabilities.validate_manifest(missing_owner, allow_synthetic_manifest=True)
        missing_routes = copy.deepcopy(self.manifest); missing_routes["candidate_routes"] = []
        with self.assertRaisesRegex(ValueError, "canonical G56R-001"):
            capabilities.validate_manifest(missing_routes)
        adverse_effort = copy.deepcopy(self.manifest)
        route_record = adverse_effort["candidate_routes"][0]
        effort_record = next(item for item in adverse_effort["effort_surface_records"] if item["effort_surface_record_id"] == "G56R-001-ESR-004")
        effort_record.update({"support_status": "documented", "documented_values": ["high"]})
        route_record["effort_selector"]["requested_value"] = "high"
        route_record["official_source_ledger_ids"].remove(effort_record["official_source_ledger_id"])
        adverse_capture = source_capture(adverse_effort)
        captured_source = next(item for item in adverse_capture if item["official_source_ledger_id"] == effort_record["official_source_ledger_id"])
        source_authority = next(item for item in adverse_effort["official_source_ledger"] if item["official_source_ledger_id"] == effort_record["official_source_ledger_id"])
        captured_source.update({"status": "inaccessible", "retrieved_body_b64": None, "bounded_extracts": [], "invalidated_claim_ids": source_authority["claim_bindings"]})
        adverse_refreshes = capabilities.normalize_source_refreshes(adverse_effort, adverse_capture, allow_synthetic_manifest=True)
        adverse_tuple = capabilities.candidate_tuples_from_manifest(adverse_effort, adverse_refreshes, allow_synthetic_manifest=True)[0]
        self.assertFalse(adverse_tuple["source_admitted"])
        self.assertIn("effort_source_not_admitted", adverse_tuple["authority_reasons"])
        scoped_manifest = copy.deepcopy(self.manifest)
        scoped_route = scoped_manifest["candidate_routes"][0]
        scoped_source = next(item for item in scoped_manifest["official_source_ledger"] if item["official_source_ledger_id"] == scoped_route["official_source_ledger_ids"][0])
        generic_claim = scoped_source["claim_bindings"][0]
        scoped_source["claim_bindings"].append(scoped_route["candidate_route_id"])
        scoped_source["extract_claim_dependencies"] = {
            item["extract_sha256"]: list(scoped_source["claim_bindings"])
            for item in scoped_source["bounded_extracts"]
        }
        scoped_capture = source_capture(scoped_manifest)
        scoped_row = next(item for item in scoped_capture if item["official_source_ledger_id"] == scoped_source["official_source_ledger_id"])
        scoped_row["invalidated_claim_ids"] = [generic_claim]
        generic_only = capabilities.candidate_tuples_from_manifest(
            scoped_manifest,
            capabilities.normalize_source_refreshes(scoped_manifest, scoped_capture, allow_synthetic_manifest=True),
            allow_synthetic_manifest=True,
        )[0]
        self.assertNotIn("source_not_admitted", generic_only["authority_reasons"])
        scoped_row["invalidated_claim_ids"] = [scoped_route["candidate_route_id"]]
        route_specific = capabilities.candidate_tuples_from_manifest(
            scoped_manifest,
            capabilities.normalize_source_refreshes(scoped_manifest, scoped_capture, allow_synthetic_manifest=True),
            allow_synthetic_manifest=True,
        )[0]
        self.assertIn("source_not_admitted", route_specific["authority_reasons"])
        empty_bindings = copy.deepcopy(self.manifest)
        empty_bindings["official_source_ledger"][1]["claim_bindings"] = []
        with self.assertRaisesRegex(ValueError, "claim bindings"):
            capabilities.validate_manifest(empty_bindings, allow_synthetic_manifest=True)

    def test_canonical_json_refreshes_and_identity(self) -> None:
        self.assertEqual(capabilities.canonical_bytes({"b": 1, "a": 2}), b'{"a":2,"b":1}')
        self.assertFalse(hasattr(capabilities, "refreshes_from_manifest"))
        captured = source_capture(self.manifest)
        refreshes = capabilities.normalize_source_refreshes(self.manifest, captured)
        result = capabilities.validate_source_refreshes(self.manifest, refreshes)
        self.assertEqual(result["count"], 22)
        self.assertEqual(result["invalidated_claim_ids"], [])
        self.assertTrue(all(item["bounded_extracts"] for item in refreshes))
        self.assertTrue(all(item["retrieval_evidence_digest"].startswith("sha256:") for item in refreshes))
        self.assertTrue(all("retrieved_body_b64" in item for item in refreshes))
        self.assertEqual(
            self.identity["client_identity_id"],
            capabilities.digest({k: v for k, v in self.identity.items() if k != "client_identity_id"}),
        )
        absolute_client_path = "/" + "Users/private/client"
        for field, value in (("reported_version", absolute_client_path), ("build_identifier", "https://example.invalid/build"), ("build_identifier", "secret\nvalue")):
            with self.assertRaises(ValueError):
                capabilities.build_client_identity({**self.fixture["client_identity"], field: value})
        with self.assertRaisesRegex(ValueError, "closed v1 shape"):
            capabilities.build_client_identity({**self.fixture["client_identity"], "authorization": "sensitive"})
        unrelated_body = copy.deepcopy(captured); unrelated_body[0]["retrieved_body_b64"] = base64.b64encode(b"unrelated").decode()
        with self.assertRaisesRegex(ValueError, "bounded extract"):
            capabilities.normalize_source_refreshes(self.manifest, unrelated_body)
        bad = copy.deepcopy(captured); bad[0]["canonical_url"] = "https://example.invalid/not-authority"
        with self.assertRaisesRegex(ValueError, "identity or URL"):
            capabilities.normalize_source_refreshes(self.manifest, bad)
        insecure = copy.deepcopy(captured); insecure[0]["canonical_url"] = "http://openai.com/unrelated"
        with self.assertRaisesRegex(ValueError, "identity or URL"):
            capabilities.normalize_source_refreshes(self.manifest, insecure)
        approved_redirect = copy.deepcopy(captured); approved_redirect[0].update({"canonical_url": "https://platform.openai.com/docs/moved-source", "status": "redirected"})
        redirected_refreshes = capabilities.normalize_source_refreshes(self.manifest, approved_redirect)
        self.assertEqual(redirected_refreshes[0]["canonical_url"], approved_redirect[0]["canonical_url"])
        self.assertEqual(redirected_refreshes[0]["status"], "redirected")
        redirected_material = copy.deepcopy(approved_redirect)
        redirected_material[0]["bounded_extracts"][0]["text"] += " Updated."
        redirected_material[0]["bounded_extracts"][0]["extract_sha256"] = capabilities.digest(redirected_material[0]["bounded_extracts"][0]["text"].encode()).removeprefix("sha256:")
        redirected_body = "\n".join(item["text"] for item in redirected_material[0]["bounded_extracts"]).encode()
        redirected_material[0].update({
            "retrieved_body_b64": base64.b64encode(redirected_body).decode(),
            "invalidated_claim_ids": self.manifest["official_source_ledger"][0]["claim_bindings"],
        })
        self.assertEqual(capabilities.normalize_source_refreshes(self.manifest, redirected_material)[0]["status"], "redirected")
        redirect_only_manifest = copy.deepcopy(self.manifest)
        redirect_only_source = redirect_only_manifest["official_source_ledger"][0]
        redirect_only_body = "\n".join(item["text"] for item in redirect_only_source["bounded_extracts"]).encode()
        redirect_only_source["body_sha256"] = capabilities.digest(redirect_only_body).removeprefix("sha256:")
        redirect_only_capture = source_capture(redirect_only_manifest)
        redirect_only_capture[0].update({"canonical_url": "https://platform.openai.com/docs/moved-source", "status": "redirected"})
        redirect_only = capabilities.normalize_source_refreshes(redirect_only_manifest, redirect_only_capture, allow_synthetic_manifest=True)
        self.assertEqual(redirect_only[0]["status"], "redirected")
        prefix_attack = copy.deepcopy(captured); prefix_attack[0]["canonical_url"] = "https://platform.openai.com/docs-evil"
        with self.assertRaisesRegex(ValueError, "identity or URL"):
            capabilities.normalize_source_refreshes(self.manifest, prefix_attack)
        for unapproved_url in (
            "https://unapproved.openai.com/docs/moved-source",
            "https://chatgpt.com/codex/moved-source",
            "https://openai.com/docs/moved-source",
            "https://user" + chr(64) + "platform.openai.com/docs/moved-source",
            "https://platform.openai.com:443/docs/moved-source",
            "https://platform.openai.com:bad/docs/moved-source",
            "https://platform.openai.com/docs/../outside",
            "https://platform.openai.com/docs/%2e%2e/outside",
            "https://platform.openai.com/docs/%2Foutside",
            "https://platform.openai.com/docs//outside",
            "https://platform.openai.com/docs?",
            "https://platform.openai.com/docs#",
            "https://platform.openai.com/docs\n",
            "https://platform.openai.com/\tdocs",
            " https://platform.openai.com/docs",
        ):
            unapproved = copy.deepcopy(captured)
            unapproved[0].update({"canonical_url": unapproved_url, "status": "redirected"})
            with self.subTest(unapproved_url=unapproved_url), self.assertRaisesRegex(ValueError, "identity or URL"):
                capabilities.normalize_source_refreshes(self.manifest, unapproved)
        invalid_time = copy.deepcopy(captured); invalid_time[0]["retrieved_at"] = "2026-07-16 00:00:00Z"
        with self.assertRaisesRegex(ValueError, "status or timestamp"):
            capabilities.normalize_source_refreshes(self.manifest, invalid_time)
        adverse = copy.deepcopy(captured); adverse[0].update({"status": "inaccessible", "retrieved_body_b64": None, "bounded_extracts": [], "invalidated_claim_ids": []})
        with self.assertRaisesRegex(ValueError, "invalidate every bound claim"):
            capabilities.normalize_source_refreshes(self.manifest, adverse)
        partial_change = copy.deepcopy(captured)
        changed_source = partial_change[-1]
        changed_source["bounded_extracts"][0]["text"] += " Updated."
        changed_source["bounded_extracts"][0]["extract_sha256"] = capabilities.digest(changed_source["bounded_extracts"][0]["text"].encode()).removeprefix("sha256:")
        changed_body = "\n".join(item["text"] for item in changed_source["bounded_extracts"]).encode()
        changed_source.update({
            "retrieved_body_b64": base64.b64encode(changed_body).decode(),
            "status": "changed",
            "invalidated_claim_ids": ["G56R-V3-PROMPT_ABLATION"],
        })
        wrong_claim = copy.deepcopy(partial_change)
        wrong_claim[-1]["invalidated_claim_ids"] = ["G56R-V3-PROMPT_GUIDANCE"]
        with self.assertRaisesRegex(ValueError, "dependent claims"):
            capabilities.normalize_source_refreshes(self.manifest, wrong_claim)
        partial_refreshes = capabilities.normalize_source_refreshes(self.manifest, partial_change)
        self.assertEqual(partial_refreshes[-1]["invalidated_claim_ids"], changed_source["invalidated_claim_ids"])
        unknown_normalization = copy.deepcopy(captured)
        unknown_normalization[0]["bounded_extracts"][0]["normalization"] = "unreviewed-normalization"
        with self.assertRaisesRegex(ValueError, "retrieved body"):
            capabilities.normalize_source_refreshes(self.manifest, unknown_normalization)
        forged = copy.deepcopy(refreshes); forged_body = b"unrelated body"
        forged[0]["retrieved_body_b64"] = base64.b64encode(forged_body).decode()
        forged[0]["body_digest"] = capabilities.digest(forged_body)
        forged[0]["retrieval_evidence_digest"] = capabilities.digest({
            "canonical_url": forged[0]["canonical_url"], "retrieved_at": forged[0]["retrieved_at"],
            "body_digest": forged[0]["body_digest"], "bounded_extracts": forged[0]["bounded_extracts"],
        })
        with self.assertRaisesRegex(ValueError, "bounded extract"):
            capabilities.validate_source_refreshes(self.manifest, forged)
        unknown_status = copy.deepcopy(refreshes); unknown_status[0]["status"] = "invented"
        with self.assertRaisesRegex(ValueError, "status or invalidation"):
            capabilities.validate_source_refreshes(self.manifest, unknown_status)
        invalidation_drift = copy.deepcopy(refreshes); invalidation_drift[0]["invalidated_claim_ids"] = ["OUT-OF-SCOPE"]
        with self.assertRaisesRegex(ValueError, "status or invalidation"):
            capabilities.validate_source_refreshes(self.manifest, invalidation_drift)
        inconsistent_status = copy.deepcopy(refreshes)
        changed_index = next(index for index, item in enumerate(inconsistent_status) if item["status"] == "changed")
        inconsistent_status[changed_index]["status"] = "confirmed_current"
        with self.assertRaisesRegex(ValueError, "inconsistent with captured evidence"):
            capabilities.validate_source_refreshes(self.manifest, inconsistent_status)
        missing_body = copy.deepcopy(refreshes); missing_body[0]["retrieved_body_b64"] = None; missing_body[0]["body_digest"] = None
        with self.assertRaisesRegex(ValueError, "require a retrieved body"):
            capabilities.validate_source_refreshes(self.manifest, missing_body)
        script_only = copy.deepcopy(captured)
        script_body = f"<html><script>{script_only[0]['bounded_extracts'][0]['text']}</script></html>".encode()
        script_only[0]["retrieved_body_b64"] = base64.b64encode(script_body).decode()
        with self.assertRaisesRegex(ValueError, "bounded extract"):
            capabilities.normalize_source_refreshes(self.manifest, script_only)
        malformed_hidden = copy.deepcopy(captured)
        hidden_body = f"<template></head>{malformed_hidden[0]['bounded_extracts'][0]['text']}</template>".encode()
        malformed_hidden[0]["retrieved_body_b64"] = base64.b64encode(hidden_body).decode()
        with self.assertRaisesRegex(ValueError, "malformed hidden markup"):
            capabilities.normalize_source_refreshes(self.manifest, malformed_hidden)
        for opening in ("<script ", "<template ", "<!-- "):
            incomplete_hidden = copy.deepcopy(captured)
            incomplete_body = f"{opening}{incomplete_hidden[0]['bounded_extracts'][0]['text']}".encode()
            incomplete_hidden[0]["retrieved_body_b64"] = base64.b64encode(incomplete_body).decode()
            with self.subTest(opening=opening), self.assertRaisesRegex(ValueError, "malformed hidden markup"):
                capabilities.normalize_source_refreshes(self.manifest, incomplete_hidden)

    def test_surface_cases_preserve_dispositions(self) -> None:
        for case in self.fixture["surface_cases"]:
            with self.subTest(case=case["case_id"]):
                observations = self.observations(case)
                options = {"aliases": case.get("aliases", {})}
                if "expected_integrity_digest" in case:
                    options["expected_integrity_digest"] = case["expected_integrity_digest"]
                matrix, decisions = capabilities.evaluate_surface_matrix(
                    observations, self.authority_tuples(case), **options,
                )
                self.assertEqual(capabilities.validate_surface_matrix(matrix), matrix)
                self.assertEqual(matrix["validity"], case["expected_validity"])
                if case["expected_decision"] == "none":
                    self.assertEqual(decisions, [])
                else:
                    self.assertTrue(decisions)
                    self.assertEqual(decisions[0]["decision"], case["expected_decision"])
                    self.assertIn("collection_evidence_non_authoritative", decisions[0]["reasons"])
                if case["case_id"] == "hidden_without_source_admission":
                    self.assertEqual(len(decisions), 1)
                    self.assertFalse(decisions[0]["source_admitted"])
                    self.assertIn("source_not_admitted", decisions[0]["reasons"])
                if case["case_id"] == "surface_disagreement":
                    self.assertEqual(len(matrix["disagreements"]), 1)
                    self.assertEqual(set(matrix["disagreements"][0]["surface_values"]), {"app_server", "cli", "interactive_picker"})
                if case["case_id"] == "hidden_picker_omission":
                    self.assertEqual(decisions[0]["surface_disposition"], "agreed")
                    self.assertEqual(decisions[0]["reasons"], ["collection_evidence_non_authoritative"])
                if case["case_id"] == "hidden_state_disagreement":
                    self.assertEqual(decisions[0]["surface_disposition"], "disagreed")
                    self.assertIn("hidden_state_disagreement", decisions[0]["reasons"])
                    self.assertEqual(matrix["disagreements"][0]["disagreement_class"], "hidden_state")
        agreed_case = next(item for item in self.fixture["surface_cases"] if item["case_id"] == "agreed")
        agreed_matrix, _ = capabilities.evaluate_surface_matrix(self.observations(agreed_case), self.authority_tuples(agreed_case))
        for malformed_digest in (None, "", "not-a-digest"):
            with self.subTest(malformed_digest=malformed_digest), self.assertRaisesRegex(ValueError, "sha256 digest"):
                capabilities.evaluate_surface_matrix(
                    self.observations(agreed_case), self.authority_tuples(agreed_case),
                    expected_integrity_digest=malformed_digest,
                )
            malformed_matrix = copy.deepcopy(agreed_matrix)
            malformed_matrix["aggregate_integrity_digest"] = malformed_digest
            malformed_matrix.update({"validity": "invalid", "invalidity_reasons": ["aggregate_hash_mismatch"]})
            malformed_matrix["surface_matrix_id"] = capabilities.digest({
                key: value for key, value in malformed_matrix.items() if key != "surface_matrix_id"
            })
            with self.assertRaisesRegex(ValueError, "sha256 digest"):
                capabilities.validate_surface_matrix(malformed_matrix)
        forged_invalidity = copy.deepcopy(agreed_matrix)
        forged_invalidity.update({"validity": "invalid", "invalidity_reasons": ["aggregate_hash_mismatch"]})
        forged_invalidity["surface_matrix_id"] = capabilities.digest({key: value for key, value in forged_invalidity.items() if key != "surface_matrix_id"})
        with self.assertRaisesRegex(ValueError, "validity is inconsistent"):
            capabilities.validate_surface_matrix(forged_invalidity)
        unequal_clients = self.observations(agreed_case)
        unequal_clients[0]["client_identity_id"] = capabilities.digest(b"different-client")
        unequal_clients[0]["surface_observation_id"] = capabilities.digest({
            key: value for key, value in unequal_clients[0].items() if key != "surface_observation_id"
        })
        unequal_matrix, _ = capabilities.evaluate_surface_matrix(unequal_clients, self.authority_tuples(agreed_case))
        self.assertEqual(unequal_matrix["invalidity_reasons"], ["unprovable_shared_client_identity"])
        self.assertEqual(capabilities.validate_surface_matrix(unequal_matrix), unequal_matrix)
        disagreement_case = next(item for item in self.fixture["surface_cases"] if item["case_id"] == "surface_disagreement")
        disagreement_matrix, _ = capabilities.evaluate_surface_matrix(self.observations(disagreement_case), self.authority_tuples(disagreement_case))
        wrong_class = copy.deepcopy(disagreement_matrix)
        wrong_class["disagreements"][0]["disagreement_class"] = "hidden_state"
        wrong_class["surface_matrix_id"] = capabilities.digest({key: value for key, value in wrong_class.items() if key != "surface_matrix_id"})
        with self.assertRaisesRegex(ValueError, "inconsistent with observed values"):
            capabilities.validate_surface_matrix(wrong_class)
        missing_disagreement = copy.deepcopy(disagreement_matrix)
        missing_disagreement["disagreements"] = []
        missing_disagreement["surface_matrix_id"] = capabilities.digest({key: value for key, value in missing_disagreement.items() if key != "surface_matrix_id"})
        with self.assertRaisesRegex(ValueError, "inventory is incomplete"):
            capabilities.validate_surface_matrix(missing_disagreement)
        partial_observations = self.observations(disagreement_case)
        partial_observations[0]["completeness_state"] = "partial"
        partial_observations[0]["surface_observation_id"] = capabilities.digest({
            key: partial_observations[0][key]
            for key in partial_observations[0]
            if key != "surface_observation_id"
        })
        partial_matrix, partial_decisions = capabilities.evaluate_surface_matrix(
            partial_observations,
            self.authority_tuples(disagreement_case),
        )
        self.assertEqual(capabilities.validate_surface_matrix(partial_matrix), partial_matrix)
        self.assertEqual(len(partial_matrix["disagreements"]), 1)
        self.assertEqual(partial_decisions[0]["surface_disposition"], "disagreed")
        self.assertFalse(capabilities._documented_discovery_unavailable(partial_observations))
        binding = partial_observations[0]["repository_binding"]
        work_item = partial_observations[0]["work_item"]
        unavailable_observations = [
            capabilities.unknown_observation(surface, self.identity["client_identity_id"], binding, work_item)
            for surface in capabilities.SURFACES
        ]
        self.assertTrue(capabilities._documented_discovery_unavailable(unavailable_observations))
        shared_tuples = self.authority_tuples(disagreement_case)
        shared_route = copy.deepcopy(shared_tuples[0])
        shared_route.update({
            "candidate_route_id": "FIXTURE-ROUTE-SHARED",
            "agent_contract_id": "FIXTURE-AGENT-SHARED",
            "candidate_route_digest": capabilities.digest({"route": "FIXTURE-ROUTE-SHARED"}),
        })
        shared_tuples.append(shared_route)
        shared_matrix, shared_decisions = capabilities.evaluate_surface_matrix(
            self.observations(disagreement_case),
            shared_tuples,
        )
        self.assertEqual(capabilities.validate_surface_matrix(shared_matrix), shared_matrix)
        self.assertEqual(len(shared_matrix["disagreements"]), 1)
        self.assertEqual(len(shared_decisions), 2)
        self.assertEqual(len({item["disagreement_digest"] for item in shared_decisions}), 1)
        wrong_reference = copy.deepcopy(disagreement_matrix)
        wrong_reference["disagreements"][0]["evidence_refs"]["cli"] = wrong_reference["disagreements"][0]["evidence_refs"]["app_server"]
        wrong_reference["surface_matrix_id"] = capabilities.digest({key: value for key, value in wrong_reference.items() if key != "surface_matrix_id"})
        with self.assertRaisesRegex(ValueError, "inconsistent with observed values"):
            capabilities.validate_surface_matrix(wrong_reference)
        agreed = next(item for item in self.fixture["surface_cases"] if item["case_id"] == "agreed")
        with self.assertRaisesRegex(ValueError, "alias authority"):
            capabilities.evaluate_surface_matrix(
                self.observations(agreed), self.authority_tuples(agreed),
                aliases={"unrelated-display": "model-a"},
            )
        alias_case = next(item for item in self.fixture["surface_cases"] if item["case_id"] == "one_to_one_alias")
        with self.assertRaisesRegex(ValueError, "alias authority evidence"):
            capabilities.evaluate_surface_matrix(
                self.observations(alias_case), self.authority_tuples(alias_case),
                aliases={"Model A Display": {"canonical_model_id": "model-b", "authority_kind": "machine_readable_identifier", "authority_surface": "cli"}},
            )
        conflicting_alias_observations = self.observations(alias_case)
        conflicting_entry = conflicting_alias_observations[0]["entries"][0]
        conflicting_entry.update({
            "model": "Model A Display", "raw_label": "Model A Display", "machine_id": "model-b",
        })
        conflicting_alias_observations[0]["surface_observation_id"] = capabilities.digest({
            key: value for key, value in conflicting_alias_observations[0].items() if key != "surface_observation_id"
        })
        conflicting_matrix, conflicting_decisions = capabilities.evaluate_surface_matrix(
            conflicting_alias_observations, self.authority_tuples(alias_case), aliases=alias_case["aliases"],
        )
        self.assertEqual(conflicting_matrix["invalidity_reasons"], ["ambiguous_or_duplicate_normalization_key"])
        self.assertEqual(conflicting_decisions[0]["surface_evidence"]["app_server"]["matching_entry"], None)
        self.assertIn("matrix_invalid", conflicting_decisions[0]["reasons"])
        self.assertEqual(capabilities.validate_surface_matrix(conflicting_matrix), conflicting_matrix)
        observations = self.observations(agreed); baseline = None
        for permutation in itertools.permutations(observations):
            matrix, decisions = capabilities.evaluate_surface_matrix(list(permutation), self.authority_tuples(agreed))
            current = capabilities.canonical_bytes([matrix, decisions])
            baseline = current if baseline is None else baseline
            self.assertEqual(current, baseline)
        arbitrary = self.observations(agreed)
        arbitrary[0]["collection_method_id"] = "unreviewed-live-v999"
        arbitrary[0]["method_inputs_digest"] = capabilities.digest({"arbitrary": True})
        arbitrary[0]["surface_observation_id"] = capabilities.digest({key: arbitrary[0][key] for key in arbitrary[0] if key != "surface_observation_id"})
        with self.assertRaisesRegex(ValueError, "closed registry"):
            capabilities.evaluate_surface_matrix(arbitrary, self.authority_tuples(agreed))
        self.assertEqual(capabilities.APPROVED_LIVE_COLLECTION_METHODS, ())

    def test_freeze_ids_bind_all_decisions_and_allow_zero_eligible(self) -> None:
        case = next(item for item in self.fixture["surface_cases"] if item["case_id"] == "zero_eligible")
        refreshes = source_refreshes(self.manifest)
        source_tuples = capabilities.candidate_tuples_from_manifest(self.manifest, refreshes)
        self.assertEqual(len(source_tuples), 23)
        self.assertTrue(all(not item["source_admitted"] for item in source_tuples))
        self.assertTrue(all(item["effort"] is None for item in source_tuples))
        matrix, decisions = capabilities.evaluate_surface_matrix(self.observations(case), source_tuples)
        freeze = capabilities.build_freeze(
            self.identity, refreshes, matrix, decisions, "2026-07-16T00:00:00Z",
            manifest=self.manifest,
        )
        self.assertEqual(capabilities.validate_freeze(freeze, self.manifest), freeze)
        self.assertEqual(freeze["telemetry_profile_id"], capabilities.PENDING_TELEMETRY_PROFILE_ID)
        leaky_identity = copy.deepcopy(freeze)
        leaky_identity["client_identity"]["authorization"] = "sensitive"
        leaky_identity["candidate_freeze_id"] = capabilities.digest(capabilities._freeze_identity_payload(leaky_identity))
        with self.assertRaisesRegex(ValueError, "closed v1 shape"):
            capabilities.validate_freeze(leaky_identity, self.manifest)
        forged_telemetry = copy.deepcopy(freeze)
        forged_telemetry["telemetry_profile_id"] = capabilities.digest(b"forged-telemetry")
        forged_telemetry["candidate_freeze_id"] = capabilities.digest(capabilities._freeze_identity_payload(forged_telemetry))
        with self.assertRaisesRegex(ValueError, "pending-treatment authority"):
            capabilities.validate_freeze(forged_telemetry, self.manifest)
        self.assertEqual(len(freeze["tuple_decisions"]), 23)
        self.assertEqual([d for d in freeze["tuple_decisions"] if d["decision"] == "included"], [])
        self.assertEqual(freeze["runtime_capability_snapshot"]["controlled_repository_snapshot"], matrix["observations"][0]["repository_binding"])
        self.assertEqual(freeze["runtime_capability_snapshot"]["work_item"], {"kind": "fixture", "id": "G56R-002-SYNTHETIC"})
        self.assertEqual(freeze["runtime_capability_snapshot_id"], freeze["runtime_capability_snapshot"]["runtime_capability_snapshot_id"])
        self.assertTrue(all(item["runtime_capability_snapshot_id"] == freeze["runtime_capability_snapshot_id"] for item in freeze["tuple_decisions"]))
        self.assertTrue(all(item["official_source_bindings"] for item in freeze["tuple_decisions"]))
        self.assertTrue(all(item["agent_contract_digest"].startswith("sha256:") for item in freeze["tuple_decisions"]))
        successor = capabilities.build_freeze(
            self.identity, refreshes, matrix, decisions, "2026-07-16T00:00:01Z",
            manifest=self.manifest, predecessor=freeze,
        )
        self.assertNotEqual(successor["candidate_freeze_id"], freeze["candidate_freeze_id"])
        self.assertEqual(successor["supersedes_candidate_freeze_id"], freeze["candidate_freeze_id"])
        self.assertEqual(successor["runtime_capability_snapshot_id"], freeze["runtime_capability_snapshot_id"])
        self.assertEqual(capabilities.validate_freeze(successor, self.manifest, predecessor=freeze), successor)
        with self.assertRaisesRegex(ValueError, "requires its validated predecessor"):
            capabilities.validate_freeze(successor, self.manifest)
        with self.assertRaisesRegex(ValueError, "precedes captured evidence"):
            capabilities.build_freeze(self.identity, refreshes, matrix, decisions, "2026-07-15T23:59:59Z", manifest=self.manifest)
        with self.assertRaisesRegex(ValueError, "publication timestamp"):
            capabilities.build_freeze(self.identity, refreshes, matrix, decisions, "not-a-date", manifest=self.manifest)
        changed_contract = copy.deepcopy(self.manifest)
        changed_contract["agent_contracts"][0]["safety_boundary"] += " changed"
        with self.assertRaisesRegex(ValueError, "canonical G56R-001"):
            capabilities.build_freeze(self.identity, refreshes, matrix, decisions, "2026-07-16T00:00:00Z", manifest=changed_contract)
        wrong_identity = capabilities.build_client_identity({**self.fixture["client_identity"], "build_identifier": "fixture-build-002"})
        with self.assertRaisesRegex(ValueError, "client identity"):
            capabilities.build_freeze(wrong_identity, refreshes, matrix, decisions, "2026-07-16T00:00:00Z", manifest=self.manifest)
        tampered = copy.deepcopy(matrix); tampered["surface_matrix_id"] = capabilities.digest(b"tampered")
        with self.assertRaisesRegex(ValueError, "matrix identity"):
            capabilities.build_freeze(self.identity, refreshes, tampered, decisions, "2026-07-16T00:00:00Z", manifest=self.manifest)
        invented = [{"candidate_route_id": "RUNTIME-INVENTED", "agent_contract_id": "AGENT-INVENTED", "named_agent": "fixture-agent", "model": "model-invented", "effort": "high", "source_admitted": True, "authority_reasons": []}]
        with self.assertRaisesRegex(ValueError, "manifest-bound tuple"):
            capabilities.evaluate_surface_matrix(self.observations(next(item for item in self.fixture["surface_cases"] if item["case_id"] == "agreed")), invented)
        forged = [{"candidate_route_id": "RUNTIME-INVENTED", "agent_contract_id": "AGENT-INVENTED", "named_agent": "fixture-agent", "canonical_model_id": "model-invented", "canonical_effort": "high", "source_admitted": True, "availability_disposition": "supported", "surface_disposition": "agreed", "decision": "included", "reasons": []}]
        with self.assertRaisesRegex(ValueError, "manifest-bound authority"):
            capabilities.build_freeze(self.identity, refreshes, matrix, forged, "2026-07-16T00:00:00Z", manifest=self.manifest)
        with self.assertRaisesRegex(ValueError, "closed v1 shape"):
            capabilities.build_freeze(self.identity, refreshes, matrix, capabilities._BoundDecisionSet(forged), "2026-07-16T00:00:00Z", manifest=self.manifest)
        mutated = capabilities._BoundDecisionSet(copy.deepcopy(decisions))
        mutated[0].update({
            "source_admitted": True,
            "availability_disposition": "supported",
            "surface_disposition": "agreed",
            "decision": "included",
            "reasons": [],
        })
        with self.assertRaisesRegex(ValueError, "manifest-backed matrix evaluation"):
            capabilities.build_freeze(self.identity, refreshes, matrix, mutated, "2026-07-16T00:00:00Z", manifest=self.manifest)
        for field, replacement in (
            ("included_candidate_route_ids", ["FORGED"]),
            ("current_ledger_digest", capabilities.digest(b"forged")),
            ("client_identity_id", capabilities.digest(b"forged-client")),
            ("source_refresh_set_digest", capabilities.digest(b"forged-refresh")),
            ("surface_matrix_id", capabilities.digest(b"forged-matrix")),
            ("candidate_freeze_id", capabilities.digest(b"forged")),
        ):
            tampered_freeze = copy.deepcopy(freeze); tampered_freeze[field] = replacement
            with self.assertRaises(ValueError): capabilities.validate_freeze(tampered_freeze, self.manifest)
        approval, _ = canary_envelope()
        self_approved_freeze = copy.deepcopy(freeze)
        self_approved_freeze["approved_canary_executors"] = [approval]
        self_approved_freeze["candidate_freeze_id"] = capabilities.digest(capabilities._freeze_identity_payload(self_approved_freeze))
        with self.assertRaisesRegex(ValueError, "repository-owned allowlist"):
            capabilities.validate_freeze(self_approved_freeze, self.manifest)

    def test_freeze_cli_round_trips_alias_authority(self) -> None:
        alias_case = next(item for item in self.fixture["surface_cases"] if item["case_id"] == "one_to_one_alias")
        observations = self.observations(alias_case)
        refreshes = source_refreshes(self.manifest)

        with tempfile.TemporaryDirectory() as tmp:
            private_root = Path(tmp)
            private_root.chmod(0o700)

            def write_input(name: str, value: object) -> Path:
                path = private_root / name
                path.write_bytes(capabilities.canonical_bytes(value) + b"\n")
                path.chmod(0o600)
                return path

            refresh_path = write_input("source-refresh.json", refreshes)
            identity_path = write_input("client-identity.json", self.identity)
            aliases_path = write_input("aliases.json", alias_case["aliases"])
            observation_paths = {
                observation["surface"]: write_input(f"{observation['surface']}.json", observation)
                for observation in observations
            }
            freeze_path = private_root / "candidate-freeze.json"

            self.assertEqual(capabilities.main([
                "freeze",
                "--manifest", str(MANIFEST_PATH),
                "--source-refresh", str(refresh_path),
                "--client-identity", str(identity_path),
                "--app-server", str(observation_paths["app_server"]),
                "--cli", str(observation_paths["cli"]),
                "--interactive-picker", str(observation_paths["interactive_picker"]),
                "--aliases", str(aliases_path),
                "--published-at", "2026-07-16T00:00:00Z",
                "--output", str(freeze_path),
            ]), 0)

            freeze = load_json(freeze_path)
            normalization = freeze["surface_matrix"]["normalization_map"]
            self.assertEqual(normalization["Model A Display"]["canonical_model_id"], "model-a")
            self.assertEqual(normalization["Model A Display"]["authority_surface"], "cli")
            self.assertEqual(normalization["Model A Display"]["client_identity_id"], self.identity["client_identity_id"])
            self.assertEqual(
                normalization["Model A Display"]["authority_evidence_ref"],
                next(item for item in observations if item["surface"] == "cli")["raw_evidence_ref"],
            )
            decision_models = {item["canonical_model_id"] for item in freeze["tuple_decisions"]}
            self.assertIn("model-a", decision_models)
            self.assertNotIn("Model A Display", decision_models)
            self.assertEqual(capabilities.validate_freeze(freeze, self.manifest), freeze)
            self.assertEqual(capabilities.main([
                "validate-freeze",
                "--manifest", str(MANIFEST_PATH),
                "--freeze", str(freeze_path),
            ]), 0)

    def test_canary_is_injected_bounded_and_default_denied(self) -> None:
        approval, result = canary_envelope()
        evidence_bytes = canary_evidence_bytes(result)
        denied = capabilities.validate_canary_result(result, evidence_bytes=evidence_bytes)
        self.assertEqual(denied["availability_disposition"], "unknown")
        allowed = capabilities.validate_canary_result(result, [approval], evidence_bytes=evidence_bytes)
        self.assertEqual(allowed["availability_disposition"], "available_for_pinned_environment")
        with self.assertRaisesRegex(ValueError, "requires its content-addressed"):
            capabilities.validate_canary_result(result, [approval], evidence_bytes=None)
        with self.assertRaisesRegex(ValueError, "do not match evidence_digest"):
            capabilities.validate_canary_result(result, [approval], evidence_bytes=b"{}\n")
        with self.assertRaisesRegex(ValueError, "only one canary"):
            capabilities.validate_canary_results([result, result], [approval])
        canary_predecessor = {"canary_results": [result]}
        retained_history = capabilities._successor_canary_results(canary_predecessor, True)
        self.assertEqual(retained_history, [result])
        self.assertIsNot(retained_history, canary_predecessor["canary_results"])
        capabilities._validate_same_snapshot_canary_history(canary_predecessor, retained_history, True)
        with self.assertRaisesRegex(ValueError, "cannot drop or rewrite"):
            capabilities._validate_same_snapshot_canary_history(canary_predecessor, [], True)
        rewritten = copy.deepcopy(result); rewritten["availability_disposition"] = "unknown"
        with self.assertRaisesRegex(ValueError, "cannot drop or rewrite"):
            capabilities._validate_same_snapshot_canary_history(canary_predecessor, [rewritten], True)
        self.assertEqual(capabilities._successor_canary_results(canary_predecessor, False), [])
        with self.assertRaisesRegex(ValueError, "only one canary"):
            capabilities.validate_canary_results([*retained_history, result], [approval])
        replayed = {**result, "canonical_model_id": "model-b"}
        with self.assertRaisesRegex(ValueError, "cannot be replayed"):
            capabilities.validate_canary_results([result, replayed], [approval])
        mismatched = {**result, "canonical_model_id": "model-b"}
        with self.assertRaisesRegex(ValueError, "does not bind"):
            capabilities.validate_canary_result(mismatched, [approval], evidence_bytes=evidence_bytes)
        boolean_bound = {**result, "attempt_index": True}
        boolean_bound["executor_result_digest"] = capabilities.digest({key: value for key, value in boolean_bound.items() if key not in {"executor_result_digest", "availability_disposition"}})
        with self.assertRaisesRegex(ValueError, "primitive types"):
            capabilities.validate_canary_result(boolean_bound, [approval], evidence_bytes=evidence_bytes)
        wrong_platform = {**result, "platform": "linux"}
        wrong_platform["executor_result_digest"] = capabilities.digest({key: value for key, value in wrong_platform.items() if key not in {"executor_result_digest", "availability_disposition"}})
        with self.assertRaisesRegex(ValueError, "platform does not match"):
            capabilities.validate_canary_result(wrong_platform, [approval], evidence_bytes=evidence_bytes)
        self_approved = {**result, "approved": True}
        with self.assertRaisesRegex(ValueError, "closed v1 envelope"):
            capabilities.validate_canary_result(self_approved, [approval], evidence_bytes=evidence_bytes)
        for terminal in capabilities.ERROR_TERMINALS:
            failed = copy.deepcopy(result)
            failed.update({
                "terminal_class": terminal, "exit_code": None, "sentinel_observed": False,
                "process_tree_termination_state": "completed" if terminal in {"timeout", "output_cap_exceeded"} else "not_needed",
            })
            failed["evidence_digest"] = capabilities.digest(canary_evidence_bytes(failed))
            failed["executor_result_digest"] = capabilities.digest({key: value for key, value in failed.items() if key not in {"executor_result_digest", "availability_disposition"}})
            self.assertEqual(capabilities.validate_canary_result(failed, [approval], evidence_bytes=canary_evidence_bytes(failed))["availability_disposition"], "unknown")
        for terminal in ("timeout", "output_cap_exceeded"):
            missing_cleanup = copy.deepcopy(result)
            missing_cleanup.update({"terminal_class": terminal, "exit_code": None, "sentinel_observed": False})
            missing_cleanup["evidence_digest"] = capabilities.digest(canary_evidence_bytes(missing_cleanup))
            missing_cleanup["executor_result_digest"] = capabilities.digest({key: value for key, value in missing_cleanup.items() if key not in {"executor_result_digest", "availability_disposition"}})
            with self.assertRaisesRegex(ValueError, "process-tree cleanup"):
                capabilities.validate_canary_result(missing_cleanup, [approval], evidence_bytes=canary_evidence_bytes(missing_cleanup))
        shared_decisions = [
            {"canonical_model_id": result["canonical_model_id"], "canonical_effort": result["canonical_effort"], "source_admitted": True,
             "reasons": ["surface_evidence_incomplete", "collection_evidence_non_authoritative"]},
            {"canonical_model_id": result["canonical_model_id"], "canonical_effort": result["canonical_effort"], "source_admitted": True,
             "reasons": ["surface_evidence_incomplete", "collection_evidence_non_authoritative"]},
        ]
        unknown_methods = [{"collection_method_id": "unknown-observation-v1"}]
        self.assertEqual(len(capabilities._validate_canary_tuple_binding(shared_decisions, result, result["snapshot_id"], unknown_methods)), 2)
        with self.assertRaisesRegex(ValueError, "documented discovery"):
            capabilities._validate_canary_tuple_binding(
                shared_decisions, result, result["snapshot_id"], [{"collection_method_id": "fixture-enumeration-v1"}],
            )
        predecessor = {
            "runtime_capability_snapshot_id": result["snapshot_id"],
            "tuple_decisions": shared_decisions,
            "surface_matrix": {"observations": unknown_methods},
            "canary_results": [],
            "candidate_freeze_id": capabilities.digest(b"fixture-predecessor"),
        }
        with tempfile.TemporaryDirectory() as tmp:
            raw_root = Path(tmp) / "raw"
            raw_root.mkdir(mode=0o700)
            with self.assertRaisesRegex(ValueError, "regular non-symlink file"):
                capabilities.validate_canary_evidence(raw_root, ROOT, result)
            with mock.patch.object(capabilities, "APPROVED_CANARY_EXECUTORS", (approval,)), mock.patch.object(
                capabilities, "validate_freeze", side_effect=lambda freeze, manifest, **kwargs: freeze,
            ), self.assertRaisesRegex(ValueError, "regular non-symlink file"):
                capabilities.build_canary_successor(
                    predecessor, result, self.manifest, "2026-07-16T00:00:01Z",
                    raw_evidence_root=raw_root, repository_root=ROOT,
                )
            evidence_path = raw_root / f"{result['evidence_digest'].removeprefix('sha256:')}.json"
            evidence_path.write_bytes(evidence_bytes); evidence_path.chmod(0o600)
            self.assertEqual(capabilities.validate_canary_evidence(raw_root, ROOT, result), evidence_bytes)
            with mock.patch.object(capabilities, "APPROVED_CANARY_EXECUTORS", (approval,)), mock.patch.object(
                capabilities, "validate_freeze", side_effect=lambda freeze, manifest, **kwargs: freeze,
            ):
                successor = capabilities.build_canary_successor(
                    predecessor, result, self.manifest, "2026-07-16T00:00:01Z",
                    raw_evidence_root=raw_root, repository_root=ROOT,
                )
            self.assertEqual(successor["canary_results"], [result])
            self.assertEqual(successor["supersedes_candidate_freeze_id"], predecessor["candidate_freeze_id"])
            evidence_path.write_bytes(b"{}\n")
            with self.assertRaisesRegex(ValueError, "content digest as the filename"):
                capabilities.validate_canary_evidence(raw_root, ROOT, result)
            with self.assertRaisesRegex(ValueError, "outside every Git worktree"):
                capabilities.validate_canary_evidence(ROOT, ROOT, result)
        self.assertEqual(capabilities.APPROVED_CANARY_EXECUTORS, ())
        with self.assertRaisesRegex(ValueError, "no repository-approved canary executor"):
            capabilities.main([
                "canary", "--manifest", "unused", "--freeze", "unused", "--model", "model-a",
                "--effort", "high", "--executor-result", "unused",
                "--raw-evidence-root", "unused", "--output", "unused",
            ])

    def test_raw_root_and_sanitizer_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw_root = Path(tmp) / "raw"
            raw_root.mkdir(mode=0o700)
            raw_file = raw_root / "capture.bin"
            raw_file.write_bytes(b"fixture")
            raw_file.chmod(0o600)
            self.assertEqual(stat.S_IMODE(raw_root.stat().st_mode), 0o700)
            capabilities.validate_raw_evidence_root(raw_root, ROOT)
            repository = capabilities.build_repository_binding("0" * 40, "1" * 40)
            work_item = {"kind": "fixture", "id": "G56R-002-RAW-REFERENCE"}
            evidence, retained = capabilities.materialize_unknown_capture(
                raw_root, ROOT, "cli", self.identity["client_identity_id"], repository,
                work_item, "2026-07-16T00:00:00Z",
            )
            self.assertEqual(capabilities.digest(retained.read_bytes()), evidence)
            self.assertEqual(retained.name, f"{evidence.removeprefix('sha256:')}.json")
            self.assertEqual(stat.S_IMODE(retained.stat().st_mode), 0o600)
            observation = capabilities.unknown_observation(
                "cli", self.identity["client_identity_id"], repository, work_item,
                raw_evidence_digest=evidence,
            )
            self.assertEqual(observation["raw_evidence_ref"], f"raw://{evidence}")
            self.assertIsNone(capabilities.validate_unknown_observation_evidence(observation, raw_root, ROOT))
            forged = copy.deepcopy(observation)
            forged_evidence = capabilities.digest(b"arbitrary retained bytes")
            forged.update({
                "raw_evidence_digest": forged_evidence,
                "raw_evidence_ref": f"raw://{forged_evidence}",
                "sanitized_evidence_digest": forged_evidence,
            })
            forged["surface_observation_id"] = capabilities.digest({
                key: value for key, value in forged.items() if key != "surface_observation_id"
            })
            with self.assertRaisesRegex(ValueError, "deterministic attempt record"):
                capabilities.validate_observation(forged)
            observations = []
            for surface in capabilities.SURFACES:
                surface_evidence, _ = capabilities.materialize_unknown_capture(
                    raw_root, ROOT, surface, self.identity["client_identity_id"], repository,
                    work_item, "2026-07-16T00:00:00Z",
                )
                observations.append(capabilities.unknown_observation(
                    surface, self.identity["client_identity_id"], repository, work_item,
                    raw_evidence_digest=surface_evidence,
                ))
            refreshes = source_refreshes(self.manifest)
            source_tuples = capabilities.candidate_tuples_from_manifest(self.manifest, refreshes)
            matrix, decisions = capabilities.evaluate_surface_matrix(observations, source_tuples)
            with self.assertRaisesRegex(ValueError, "raw evidence root"):
                capabilities.build_freeze(
                    self.identity, refreshes, matrix, decisions, "2026-07-16T00:00:00Z",
                    manifest=self.manifest,
                )
            freeze = capabilities.build_freeze(
                self.identity, refreshes, matrix, decisions, "2026-07-16T00:00:00Z",
                manifest=self.manifest, raw_evidence_root=raw_root, repository_root=ROOT,
            )
            self.assertEqual(capabilities.validate_freeze(freeze, self.manifest), freeze)
            raw_file.chmod(0o644)
            with self.assertRaisesRegex(ValueError, "files require 0600"):
                capabilities.validate_raw_evidence_root(raw_root, ROOT)
            raw_file.chmod(0o600)
            child = raw_root / "nested"; child.mkdir(mode=0o755)
            with self.assertRaisesRegex(ValueError, "directories require 0700"):
                capabilities.validate_raw_evidence_root(raw_root, ROOT)
            child.chmod(0o700)
            if os.name != "nt":
                link = raw_root / "escape"; link.symlink_to(Path(tmp).parent)
                with self.assertRaisesRegex(ValueError, "symlink"):
                    capabilities.validate_raw_evidence_root(raw_root, ROOT)
                link.unlink()
            with self.assertRaisesRegex(ValueError, "outside every Git worktree"):
                capabilities.validate_raw_evidence_root(ROOT, ROOT)
            private = Path(tmp) / "capture.json"; private.write_text("{}"); private.chmod(0o600)
            self.assertEqual(capabilities.validate_private_external_file(private, ROOT, "capture"), private.resolve())
            content = b"content-addressed evidence\n"; content_digest = capabilities.digest(content)
            content_path = Path(tmp) / f"{content_digest.removeprefix('sha256:')}.json"
            content_path.write_bytes(content); content_path.chmod(0o600)
            self.assertEqual(capabilities.validate_content_addressed_private_file(content_path, ROOT, "capture"), content_path.resolve())
            self.assertEqual(capabilities.read_content_addressed_private_file(content_path, ROOT, "capture"), (content_path.resolve(), content))
            with self.assertRaisesRegex(ValueError, "content digest as the filename"):
                capabilities.validate_content_addressed_private_file(private, ROOT, "capture")
            with self.assertRaisesRegex(ValueError, "outside every Git worktree"):
                capabilities.validate_private_external_file(ROOT / "capture.json", ROOT, "capture", output=True)
        sanitized = capabilities.sanitize({"surface": "cli", "status": "unknown", "authorization": "secret", "hostname": "machine"}, "surface_status")
        self.assertEqual(sanitized, {"status": "unknown", "surface": "cli"})
        first = capabilities.sanitize({"account": "fixture-sensitive"}, "fixture_identity")
        self.assertEqual(first, capabilities.sanitize({"account": "different-sensitive"}, "fixture_identity"))
        self.assertNotIn("fixture-sensitive", first["account"])
        with self.assertRaisesRegex(ValueError, "forbidden sensitive field"):
            capabilities.sanitize({"status": {"authorization": "secret"}}, "surface_status")
        secret = {"state": "complete", "entries": [{"model": "model-a", "effort": "high", "available": True, "hidden": False, "credentials": {"token": "secret"}}]}
        with self.assertRaisesRegex(ValueError, "undeclared"):
            capabilities.fixture_observation("cli", secret, self.identity["client_identity_id"])
        observation = self.observations(next(item for item in self.fixture["surface_cases"] if item["case_id"] == "agreed"))[0]
        observation["entries"][0]["model"] = "/" + "Users/fixture/private"
        observation["surface_observation_id"] = capabilities.digest({key: observation[key] for key in observation if key != "surface_observation_id"})
        with self.assertRaisesRegex(ValueError, "path or remote"):
            capabilities.validate_observation(observation)
        for bad_model in ("model-a\nAuthorization", "model-a\x1b[31m", "x" * 129, "モデル"):
            with self.subTest(bad_model=bad_model), self.assertRaisesRegex(ValueError, "model or effort"):
                capabilities.fixture_observation(
                    "cli", {"state": "complete", "entries": [{"model": bad_model, "effort": "high", "available": True, "hidden": False}]},
                    self.identity["client_identity_id"],
                )
        machine = capabilities.fixture_observation("cli", {"state": "complete", "entries": [{"model": "Model A", "machine_id": "model-a", "raw_label": "Model A", "effort": "high", "available": True, "hidden": False}]}, self.identity["client_identity_id"])
        self.assertEqual(machine["entries"][0]["machine_id"], "model-a")
        bad_ref = copy.deepcopy(machine); bad_ref["raw_evidence_ref"] += "/private"
        bad_ref["surface_observation_id"] = capabilities.digest({key: bad_ref[key] for key in bad_ref if key != "surface_observation_id"})
        with self.assertRaisesRegex(ValueError, "content addressed"):
            capabilities.validate_observation(bad_ref)
        mismatched_ref = copy.deepcopy(machine); mismatched_ref["raw_evidence_ref"] = f"raw://{capabilities.digest(b'different')}"
        mismatched_ref["surface_observation_id"] = capabilities.digest({key: mismatched_ref[key] for key in mismatched_ref if key != "surface_observation_id"})
        with self.assertRaisesRegex(ValueError, "match raw_evidence_digest"):
            capabilities.validate_observation(mismatched_ref)
        bad_time = copy.deepcopy(machine); bad_time["started_at"] = "2026-07-16 00:00:00Z"
        bad_time["surface_observation_id"] = capabilities.digest({key: bad_time[key] for key in bad_time if key != "surface_observation_id"})
        with self.assertRaisesRegex(ValueError, "collection timestamp"):
            capabilities.validate_observation(bad_time)
        reversed_window = copy.deepcopy(machine); reversed_window.update({"started_at": "2026-07-16T00:00:01Z", "completed_at": "2026-07-16T00:00:00Z"})
        reversed_window["surface_observation_id"] = capabilities.digest({key: reversed_window[key] for key in reversed_window if key != "surface_observation_id"})
        with self.assertRaisesRegex(ValueError, "collection window"):
            capabilities.validate_observation(reversed_window)

    def test_repository_binding_requires_a_clean_committed_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repository = Path(tmp) / "repository"
            repository.mkdir()
            commands = (
                ["git", "init", "-q"],
                ["git", "config", "user.name", "G56R Fixture"],
                ["git", "config", "user.email", "git@github.com"],
                ["git", "config", "commit.gpgsign", "false"],
            )
            for _git, *arguments in commands:
                subprocess.run(["git", *arguments], cwd=repository, check=True, capture_output=True)
            tracked = repository / "tracked.txt"
            tracked.write_text("committed\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=repository, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=repository, check=True, capture_output=True)
            binding = capabilities.repository_binding_from_checkout(repository)
            self.assertEqual(binding["revision"], subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repository, check=True,
                capture_output=True, text=True,
            ).stdout.strip())
            (repository / "untracked.txt").write_text("dirty\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must be clean"):
                capabilities.repository_binding_from_checkout(repository)
            resolved = "a" * 40
            responses = [
                subprocess.CompletedProcess([], 0, stdout="", stderr=""),
                subprocess.CompletedProcess([], 0, stdout=f"{resolved}\n", stderr=""),
                subprocess.CompletedProcess([], 0, stdout=f"{'b' * 40}\n", stderr=""),
                subprocess.CompletedProcess([], 0, stdout=f"{'c' * 40}\n", stderr=""),
            ]
            with mock.patch.object(capabilities.subprocess, "run", side_effect=responses) as run:
                with self.assertRaisesRegex(ValueError, "changed during collection binding"):
                    capabilities.repository_binding_from_checkout(repository)
            self.assertEqual(run.call_args_list[2].args[0][-1], f"{resolved}^{{tree}}")

    def test_json_inputs_executable_hashing_and_publication_are_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            duplicate = root / "duplicate.json"
            duplicate.write_bytes(b'{"key":1,"key":2}\n')
            with self.assertRaisesRegex(ValueError, "duplicate JSON object key"):
                capabilities._read(duplicate)
            invalid_utf8 = root / "invalid-utf8.json"
            invalid_utf8.write_bytes(b'{"key":"\xff"}\n')
            with self.assertRaisesRegex(ValueError, "strict UTF-8 JSON"):
                capabilities._read(invalid_utf8)
            for index, constant in enumerate(("NaN", "Infinity", "-Infinity")):
                nonfinite = root / f"nonfinite-{index}.json"
                nonfinite.write_text(f'{{"value":{constant}}}\n', encoding="utf-8")
                with self.subTest(constant=constant), self.assertRaisesRegex(ValueError, "non-JSON numeric constant"):
                    capabilities._read(nonfinite)
                with self.assertRaisesRegex(ValueError, "non-JSON numeric constant"):
                    capabilities._read(nonfinite, require_canonical=True)
            with self.assertRaises(ValueError):
                capabilities.canonical_bytes({"value": float("nan")})
            noncanonical = root / "noncanonical.json"
            noncanonical.write_text('{"b": 1, "a": 2}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not canonical"):
                capabilities._read(noncanonical, require_canonical=True)
            canonical = root / "canonical.json"
            capabilities._write(canonical, {"b": 1, "a": 2}, append_only=True)
            self.assertEqual(capabilities._read(canonical, require_canonical=True), {"a": 2, "b": 1})
            replacement = root / "replacement.json"
            replacement.write_bytes(b'{}\n')
            with mock.patch.object(capabilities.os, "stat", return_value=replacement.stat()):
                with self.assertRaisesRegex(ValueError, "pathname changed"):
                    capabilities._read_bounded_regular_file(canonical)
            initial = canonical.stat()
            changed_ctime = mock.Mock(
                st_mode=initial.st_mode, st_dev=initial.st_dev, st_ino=initial.st_ino,
                st_size=initial.st_size, st_mtime_ns=initial.st_mtime_ns,
                st_ctime_ns=initial.st_ctime_ns + 1,
            )
            with mock.patch.object(capabilities.os, "fstat", side_effect=[initial, changed_ctime]):
                with self.assertRaisesRegex(ValueError, "changed while"):
                    capabilities._read_bounded_regular_file(canonical)
            with mock.patch.object(capabilities, "PRIVATE_REFRESH_MAX_BYTES", 4):
                with self.assertRaisesRegex(ValueError, "exceeds the maximum size"):
                    capabilities._read_bounded_regular_file(canonical)
            with self.assertRaises(FileExistsError):
                capabilities._write(canonical, {"replacement": True}, append_only=True)
            self.assertEqual(capabilities._read(canonical, require_canonical=True), {"a": 2, "b": 1})
            executable = root / "large-client"
            executable.write_bytes(b"fixture-client" * 200000)
            self.assertEqual(capabilities.digest_regular_file(executable), capabilities.digest(executable.read_bytes()))
            executable_replacement = root / "replacement-client"
            executable_replacement.write_bytes(b"different-client")
            with mock.patch.object(capabilities.os, "stat", return_value=executable_replacement.stat()):
                with self.assertRaisesRegex(ValueError, "pathname changed"):
                    capabilities.digest_regular_file(executable)
            executable_before = executable.stat()
            executable_after = mock.Mock(
                st_mode=executable_before.st_mode, st_dev=executable_before.st_dev,
                st_ino=executable_before.st_ino, st_size=executable_before.st_size,
                st_mtime_ns=executable_before.st_mtime_ns,
                st_ctime_ns=executable_before.st_ctime_ns + 1,
            )
            with mock.patch.object(capabilities.os, "fstat", side_effect=[executable_before, executable_after]):
                with self.assertRaisesRegex(ValueError, "changed while hashing"):
                    capabilities.digest_regular_file(executable)
            growing = root / "growing-client"
            growing.write_bytes(b"grow")
            growing_before = growing.stat()
            growing_after = mock.Mock(
                st_mode=growing_before.st_mode, st_dev=growing_before.st_dev,
                st_ino=growing_before.st_ino, st_size=growing_before.st_size + 1,
                st_mtime_ns=growing_before.st_mtime_ns,
                st_ctime_ns=growing_before.st_ctime_ns + 1,
            )
            with mock.patch.object(capabilities.os, "fstat", side_effect=[growing_before, growing_after]), mock.patch.object(
                capabilities.os, "read", side_effect=lambda descriptor, size: b"x" * size,
            ) as growing_read:
                with self.assertRaisesRegex(ValueError, "changed while hashing"):
                    capabilities.digest_regular_file(growing)
            self.assertEqual(growing_read.call_count, 1)
            private_output = root / "private-output.json"
            with mock.patch.object(capabilities, "Path", type(root)), mock.patch.object(
                capabilities.os, "name", "nt",
            ), mock.patch.object(capabilities.os, "fchmod") as fchmod:
                capabilities._write(private_output, {"private": True}, private=True)
            fchmod.assert_not_called()
            self.assertEqual(capabilities._read(private_output), {"private": True})
            if hasattr(os, "mkfifo"):
                fifo = root / "client-fifo"
                os.mkfifo(fifo)
                with self.assertRaisesRegex(ValueError, "regular file"):
                    capabilities.digest_regular_file(fifo)


if __name__ == "__main__":
    unittest.main()
