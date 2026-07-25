#!/usr/bin/env python3
"""Focused deterministic tests for Codex successor capability publication."""

from __future__ import annotations

import importlib.util
import base64
import copy
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = ROOT / "tests/speckit-pro/layer6-efficiency/lib/codex_successor_capability.py"
CAPABILITY_MODULE_PATH = ROOT / "tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py"
SCHEMA_PATH = ROOT / "tests/speckit-pro/layer6-efficiency/contracts/successor-capability-freeze.schema.json"
FIXTURE_PATH = ROOT / "tests/speckit-pro/unit/fixtures/capability-treatment-replay/capability-matrix.json"
MANIFEST_PATH = ROOT / "docs/ai/research/codex-agent-route-candidate-manifest.json"

EXPECTED_SUCCESSOR_PUBLIC_API = frozenset({
    "SUCCESSOR_FREEZE_SCHEMA_VERSION",
    "SUCCESSOR_MUTABLE_FIELDS",
    "TOPOLOGY_CONTROL_FIELDS",
    "build_successor_freeze",
    "canonical_bytes",
    "digest",
    "publish_successor_freeze",
    "validate_successor_freeze",
    "validate_successor_request",
})


def load_successor_module(name: str = "g56r_003_codex_successor_capability"):
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_capabilities(name: str = "g56r_003_codex_capabilities"):
    spec = importlib.util.spec_from_file_location(name, CAPABILITY_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {CAPABILITY_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


capabilities = load_capabilities()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def source_capture(manifest: dict, retrieved_at: str = "2026-07-16T00:00:00Z") -> list[dict]:
    captured = []
    for source in manifest["official_source_ledger"]:
        body = "\n".join(item["text"] for item in source["bounded_extracts"])
        current = capabilities.digest(body.encode())
        prior = f"sha256:{source['body_sha256']}"
        redirected = source["requested_url"] != source["canonical_url"]
        captured.append({
            "official_source_ledger_id": source["official_source_ledger_id"],
            "requested_url": source["requested_url"],
            "canonical_url": source["canonical_url"],
            "retrieved_at": retrieved_at,
            "status": "redirected" if redirected else "confirmed_current" if current == prior else "changed",
            "invalidated_claim_ids": copy.deepcopy(source["claim_bindings"]) if redirected or current != prior else [],
            "retrieved_body_b64": base64.b64encode(body.encode()).decode(),
            "retrieved_body_format": "normalized_plain_text",
            "bounded_extracts": copy.deepcopy(source["bounded_extracts"]),
        })
    return captured


def source_refreshes(manifest: dict) -> list[dict]:
    return capabilities.normalize_source_refreshes(manifest, source_capture(manifest))


class CodexSuccessorCapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = load_json(FIXTURE_PATH)
        cls.manifest = load_json(MANIFEST_PATH)
        cls.identity = capabilities.build_client_identity(cls.fixture["client_identity"])

    def predecessor_freeze(self) -> dict:
        case = next(item for item in self.fixture["surface_cases"] if item["case_id"] == "zero_eligible")
        refreshes = source_refreshes(self.manifest)
        observations = [
            capabilities.fixture_observation(surface, value, self.identity["client_identity_id"])
            for surface, value in case["surfaces"].items()
        ]
        matrix, decisions = capabilities.evaluate_surface_matrix(
            observations,
            capabilities.candidate_tuples_from_manifest(self.manifest, refreshes),
        )
        return capabilities.build_freeze(
            self.identity,
            refreshes,
            matrix,
            decisions,
            "2026-07-16T00:00:00Z",
            manifest=self.manifest,
        )

    def successor_request(
        self,
        predecessor: dict,
        successor,
        *,
        catalog_capture: dict | None = None,
        published_at: str = "2026-07-16T00:00:01Z",
        diagnostics: list[dict] | None = None,
    ) -> dict:
        if catalog_capture is None:
            catalog_capture = self.catalog_capture(predecessor, successor)
        diagnostics = diagnostics or [{
            "surface": "cli",
            "captured_at": "2026-07-16T00:00:00Z",
            "reported_effort": "Ordinary",
            "diagnostic_fields": {
                "assignment.supported_effective_model": "gpt-5.6-sol",
                "assignment.supported_effective_effort": "ordinary",
                "discovery.models": ["model-a"],
                "discovery.capabilities": ["tool-use"],
                "availability": True,
            },
        }]
        return {
            "schema_version": successor.SUCCESSOR_FREEZE_SCHEMA_VERSION,
            "predecessor_candidate_freeze_id": predecessor["candidate_freeze_id"],
            "client_identity_id": predecessor["client_identity_id"],
            "account_identity_id": capabilities.digest(b"fixture-account"),
            "source_manifest_digest": predecessor["source_manifest_binding"]["manifest_digest"],
            "source_refresh_set_digest": predecessor["source_refresh_set_digest"],
            "runtime_capability_snapshot_id": predecessor["runtime_capability_snapshot_id"],
            "catalog_capture": catalog_capture,
            "diagnostic_capture_digest": successor.digest(successor.canonical_bytes(diagnostics) + b"\n"),
            "published_at": published_at,
            "successor_mutable_fields": list(successor.SUCCESSOR_MUTABLE_FIELDS),
            "diagnostics": diagnostics,
        }

    def catalog_capture(
        self,
        predecessor: dict,
        successor,
        *,
        visible_models: list[dict] | None = None,
        collected_at: str = "2026-07-16T00:00:00Z",
        valid_until: str = "2026-07-17T00:00:00Z",
    ) -> dict:
        raw_catalog = {
            "command": "codex debug models",
            "client": predecessor["client_identity"]["reported_version"],
            "models": visible_models or [{
                "model": "gpt-5.6-sol",
                "default_effort": "Ordinary",
                "supported_efforts": ["Ordinary", "Ultra"],
            }],
        }
        raw_catalog_bytes = successor.canonical_bytes(raw_catalog) + b"\n"
        raw_catalog_digest = successor.digest(raw_catalog_bytes)
        normalization = [
            {
                "raw_effort": "implicit_default",
                "canonical_effort": "ordinary",
                "evidence_digest": raw_catalog_digest,
                "evidence_ref": f"raw://{raw_catalog_digest}",
            },
            {
                "raw_effort": "Ordinary",
                "canonical_effort": "ordinary",
                "evidence_digest": raw_catalog_digest,
                "evidence_ref": f"raw://{raw_catalog_digest}",
            },
        ]
        catalog_models = []
        for item in raw_catalog["models"]:
            entry = {
                "model": item["model"],
                "default_effort": item["default_effort"],
                "supported_efforts": item["supported_efforts"],
            }
            catalog_models.append({
                **entry,
                "catalog_entry_digest": successor.digest(entry),
            })
        parsed_catalog = {
            "visible_models": catalog_models,
            "defaults": {"effort": "Ordinary"},
            "supported_efforts": sorted({
                effort
                for item in raw_catalog["models"]
                for effort in item["supported_efforts"]
            }),
            "effort_normalization_map": normalization,
        }
        return {
            "schema_version": "codex-debug-models-catalog.v1",
            "command_contract": {
                "argv": ["codex", "debug", "models"],
                "requires_refresh": True,
                "output_format": "json",
            },
            "client_identity": predecessor["client_identity"],
            "account_boundary_id": capabilities.digest(b"fixture-account"),
            "environment_boundary_id": capabilities.digest(b"fixture-environment"),
            "raw_catalog_digest": raw_catalog_digest,
            "raw_evidence_ref": f"raw://{raw_catalog_digest}",
            "parsed_catalog_digest": successor.digest(parsed_catalog),
            "visible_models": catalog_models,
            "defaults": {"effort": "Ordinary"},
            "supported_efforts": parsed_catalog["supported_efforts"],
            "effort_normalization_map": normalization,
            "collected_at": collected_at,
            "valid_until": valid_until,
            "invalidation_triggers": [
                "client_version_change",
                "account_boundary_change",
                "environment_boundary_change",
                "new_codex_debug_models_capture",
            ],
            "authority": {
                "collector": "codex-debug-models",
                "trust": "pinned_client",
                "currentness": "current",
            },
            "sanitization": {
                "allowlist_version": "g56r-003-catalog-capture.v1",
                "result": "pass",
            },
        }

    def test_successor_facade_preserves_closed_public_api(self) -> None:
        successor = load_successor_module()
        self.assertEqual(frozenset(successor.__all__), EXPECTED_SUCCESSOR_PUBLIC_API)
        public_names = frozenset(name for name in vars(successor) if not name.startswith("_"))
        self.assertEqual(public_names, EXPECTED_SUCCESSOR_PUBLIC_API)
        for exported_name in sorted(EXPECTED_SUCCESSOR_PUBLIC_API):
            with self.subTest(exported_name=exported_name):
                self.assertTrue(hasattr(successor, exported_name))

    def test_successor_schema_closes_publication_request_shape(self) -> None:
        schema = load_json(SCHEMA_PATH)
        successor = load_successor_module()
        self.assertEqual(schema["properties"]["schema_version"]["const"], successor.SUCCESSOR_FREEZE_SCHEMA_VERSION)
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            set(schema["required"]),
            {
                "schema_version",
                "predecessor_candidate_freeze_id",
                "client_identity_id",
                "account_identity_id",
                "source_manifest_digest",
                "source_refresh_set_digest",
                "runtime_capability_snapshot_id",
                "catalog_capture",
                "diagnostic_capture_digest",
                "published_at",
                "successor_mutable_fields",
                "diagnostics",
            },
        )
        self.assertEqual(
            schema["properties"]["catalog_capture"],
            {"$ref": "#/$defs/catalogCapture"},
        )
        catalog_capture = schema["$defs"]["catalogCapture"]
        self.assertFalse(catalog_capture["additionalProperties"])
        self.assertEqual(
            set(catalog_capture["required"]),
            {
                "schema_version",
                "command_contract",
                "client_identity",
                "account_boundary_id",
                "environment_boundary_id",
                "raw_catalog_digest",
                "raw_evidence_ref",
                "parsed_catalog_digest",
                "visible_models",
                "defaults",
                "supported_efforts",
                "effort_normalization_map",
                "collected_at",
                "valid_until",
                "invalidation_triggers",
                "authority",
                "sanitization",
            },
        )
        catalog_properties = catalog_capture["properties"]
        self.assertNotIn("raw_catalog_bytes", catalog_properties)
        for nested in (
            "command_contract",
            "client_identity",
            "defaults",
            "authority",
            "sanitization",
        ):
            self.assertFalse(catalog_properties[nested]["additionalProperties"])
        self.assertFalse(catalog_properties["visible_models"]["items"]["additionalProperties"])
        self.assertEqual(
            set(catalog_properties["visible_models"]["items"]["required"]),
            {"model", "default_effort", "supported_efforts", "catalog_entry_digest"},
        )
        self.assertFalse(catalog_properties["effort_normalization_map"]["items"]["additionalProperties"])
        self.assertEqual(
            set(catalog_properties["effort_normalization_map"]["items"]["required"]),
            {"raw_effort", "canonical_effort", "evidence_digest", "evidence_ref"},
        )
        self.assertEqual(
            schema["properties"]["diagnostics"]["items"],
            {"$ref": "#/$defs/diagnostic"},
        )
        self.assertFalse(schema["$defs"]["diagnostic"]["additionalProperties"])
        mutable_rule = schema["properties"]["successor_mutable_fields"]
        self.assertEqual(mutable_rule["prefixItems"], [{"const": item} for item in successor.SUCCESSOR_MUTABLE_FIELDS])
        diagnostic_fields = set(schema["$defs"]["diagnostic"]["properties"])
        self.assertFalse(diagnostic_fields & set(successor.TOPOLOGY_CONTROL_FIELDS))

    def test_successor_build_is_additive_and_diagnostics_do_not_grant_availability(self) -> None:
        successor = load_successor_module()
        predecessor = self.predecessor_freeze()
        request = self.successor_request(predecessor, successor)
        validated_request = successor.validate_successor_request(request, predecessor)
        self.assertIsNone(validated_request["diagnostics"][0]["reported_effort"])
        self.assertEqual(
            validated_request["catalog_capture"]["visible_models"][0]["default_effort"],
            "ordinary",
        )

        successor_freeze = successor.build_successor_freeze(
            predecessor,
            request,
            manifest=self.manifest,
        )
        self.assertEqual(
            successor.validate_successor_freeze(successor_freeze, predecessor, request, manifest=self.manifest),
            successor_freeze,
        )
        self.assertEqual(successor_freeze["supersedes_candidate_freeze_id"], predecessor["candidate_freeze_id"])
        self.assertNotEqual(successor_freeze["candidate_freeze_id"], predecessor["candidate_freeze_id"])
        self.assertGreater(len(successor_freeze["included_candidate_route_ids"]), 0)
        included = [
            item for item in successor_freeze["tuple_decisions"]
            if item["decision"] == "included"
        ]
        self.assertEqual(
            successor_freeze["included_candidate_route_ids"],
            [item["candidate_route_id"] for item in included],
        )
        self.assertTrue(all(item["source_admitted"] for item in included))
        self.assertTrue(all(item["catalog_supported"] for item in included))
        self.assertTrue(all(item["canonical_effort"] == "ordinary" for item in included))
        self.assertTrue(all(item["official_source_bindings"] for item in included))
        self.assertTrue(all(item["catalog_evidence"]["raw_evidence_ref"] == request["catalog_capture"]["raw_evidence_ref"] for item in included))
        source_routes = {item["candidate_route_id"] for item in self.manifest["candidate_routes"]}
        catalog_models = {item["model"] for item in request["catalog_capture"]["visible_models"]}
        self.assertTrue(set(successor_freeze["included_candidate_route_ids"]) <= source_routes)
        self.assertTrue(all(item["canonical_model_id"] in catalog_models for item in included))
        self.assertNotIn("model-a", {item["canonical_model_id"] for item in included})
        self.assertIn(
            "topology_control_not_candidate_effort",
            {
                reason
                for item in successor_freeze["tuple_decisions"]
                if item["decision"] == "excluded"
                for reason in item["reasons"]
            },
        )
        self.assertEqual(successor_freeze["snapshot_authority_failures"], [])
        self.assertNotIn("diagnostics", successor_freeze)
        self.assertNotIn("account_identity_id", successor_freeze)
        self.assertNotIn("raw_catalog_bytes", successor.canonical_bytes(successor_freeze).decode())
        for key in predecessor:
            self.assertEqual(
                successor_freeze["predecessor_freeze"]["frozen_payload"][key],
                predecessor[key],
            )

    def test_successor_publish_uses_retention_helper_without_rewriting_predecessor(self) -> None:
        successor = load_successor_module()
        predecessor = self.predecessor_freeze()
        request = self.successor_request(predecessor, successor)
        predecessor_bytes = successor.canonical_bytes(predecessor) + b"\n"
        raw_catalog_bytes = successor.canonical_bytes({
            "command": "codex debug models",
            "client": predecessor["client_identity"]["reported_version"],
            "models": [{
                "model": "gpt-5.6-sol",
                "default_effort": "Ordinary",
                "supported_efforts": ["Ordinary", "Ultra"],
            }],
        }) + b"\n"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw_root = root / "raw"
            raw_root.mkdir(mode=0o700)
            raw_path = raw_root / f"{request['catalog_capture']['raw_catalog_digest'].removeprefix('sha256:')}.json"
            raw_path.write_bytes(raw_catalog_bytes)
            raw_path.chmod(0o600)
            predecessor_path = root / "predecessor.json"
            successor_path = root / "successor.json"
            predecessor_path.write_bytes(predecessor_bytes)
            result = successor.publish_successor_freeze(
                predecessor_path,
                request,
                successor_path,
                raw_root,
                ROOT,
                manifest=self.manifest,
            )
            self.assertEqual(predecessor_path.read_bytes(), predecessor_bytes)
            committed_successor = json.loads(successor_path.read_text())
            self.assertEqual(result["predecessor_bytes_sha256"], successor.digest(predecessor_bytes))
            self.assertEqual(
                result["successor_bytes_sha256"],
                successor.digest(successor.canonical_bytes(committed_successor) + b"\n"),
            )
            self.assertEqual(result["raw_catalog_evidence_digest"], request["catalog_capture"]["raw_catalog_digest"])
            self.assertEqual(result["raw_catalog_evidence_ref"], request["catalog_capture"]["raw_evidence_ref"])
            self.assertNotIn("diagnostics", committed_successor)
            self.assertNotIn("raw_catalog_bytes", successor.canonical_bytes(committed_successor).decode())
            raw_path.unlink()
            with self.assertRaisesRegex(ValueError, "retained raw catalog evidence"):
                successor.publish_successor_freeze(
                    predecessor_path,
                    request,
                    root / "missing-raw-successor.json",
                    raw_root,
                    ROOT,
                    manifest=self.manifest,
                )
            with self.assertRaisesRegex(ValueError, "additive successor publication"):
                successor.publish_successor_freeze(
                    predecessor_path,
                    request,
                    predecessor_path,
                    raw_root,
                    ROOT,
                    manifest=self.manifest,
                )

    def test_successor_request_fails_closed_for_stale_untrusted_or_mutating_inputs(self) -> None:
        successor = load_successor_module()
        predecessor = self.predecessor_freeze()
        valid = self.successor_request(predecessor, successor)
        cases = []
        cases.append(("empty", {}, "closed successor request"))
        stale = copy.deepcopy(valid)
        stale["published_at"] = predecessor["published_at"]
        cases.append(("stale", stale, "later than predecessor"))
        wrong_client = copy.deepcopy(valid)
        wrong_client["client_identity_id"] = capabilities.digest(b"wrong-client")
        cases.append(("client", wrong_client, "client identity"))
        wrong_account = copy.deepcopy(valid)
        wrong_account["account_identity_id"] = "fixture-account"
        cases.append(("account", wrong_account, "account identity"))
        wrong_source = copy.deepcopy(valid)
        wrong_source["source_manifest_digest"] = capabilities.digest(b"wrong-manifest")
        cases.append(("source", wrong_source, "pinned manifest"))
        wrong_capture = copy.deepcopy(valid)
        wrong_capture["diagnostic_capture_digest"] = capabilities.digest(b"wrong-diagnostics")
        cases.append(("digest", wrong_capture, "diagnostic capture digest"))
        missing_catalog = copy.deepcopy(valid)
        missing_catalog.pop("catalog_capture")
        cases.append(("missing-catalog", missing_catalog, "closed successor request"))
        unknown_catalog = copy.deepcopy(valid)
        unknown_catalog["catalog_capture"]["raw_catalog_bytes"] = "private"
        cases.append(("unknown-catalog", unknown_catalog, "closed catalog capture"))
        wrong_raw_ref = copy.deepcopy(valid)
        wrong_raw_ref["catalog_capture"]["raw_evidence_ref"] = f"raw://{capabilities.digest(b'wrong-raw')}"
        cases.append(("raw-ref", wrong_raw_ref, "raw catalog evidence reference"))
        wrong_environment = copy.deepcopy(valid)
        wrong_environment["catalog_capture"]["environment_boundary_id"] = "fixture-environment"
        cases.append(("environment", wrong_environment, "environment boundary"))
        stale_catalog = copy.deepcopy(valid)
        stale_catalog["catalog_capture"]["valid_until"] = stale_catalog["published_at"]
        cases.append(("stale-catalog", stale_catalog, "stale"))
        untrusted = copy.deepcopy(valid)
        untrusted["catalog_capture"]["authority"]["trust"] = "diagnostic_surface"
        cases.append(("untrusted", untrusted, "collection authority"))
        missing_provenance = copy.deepcopy(valid)
        missing_provenance["catalog_capture"].pop("raw_evidence_ref")
        cases.append(("missing-provenance", missing_provenance, "closed catalog capture"))
        parsed_digest = copy.deepcopy(valid)
        parsed_digest["catalog_capture"]["parsed_catalog_digest"] = capabilities.digest(b"wrong-parsed")
        cases.append(("parsed-digest", parsed_digest, "parsed catalog digest"))
        normalized_without_evidence = copy.deepcopy(valid)
        normalized_without_evidence["catalog_capture"]["effort_normalization_map"][0]["evidence_digest"] = capabilities.digest(b"wrong-normalization")
        cases.append(("normalization-evidence", normalized_without_evidence, "effort normalization evidence"))
        ultra_as_ordinary = copy.deepcopy(valid)
        ultra_as_ordinary["catalog_capture"]["effort_normalization_map"].append({
            "raw_effort": "Ultra",
            "canonical_effort": "ordinary",
            "evidence_digest": ultra_as_ordinary["catalog_capture"]["raw_catalog_digest"],
            "evidence_ref": ultra_as_ordinary["catalog_capture"]["raw_evidence_ref"],
        })
        ultra_as_ordinary["catalog_capture"]["parsed_catalog_digest"] = successor.digest({
            "visible_models": ultra_as_ordinary["catalog_capture"]["visible_models"],
            "defaults": ultra_as_ordinary["catalog_capture"]["defaults"],
            "supported_efforts": ultra_as_ordinary["catalog_capture"]["supported_efforts"],
            "effort_normalization_map": ultra_as_ordinary["catalog_capture"]["effort_normalization_map"],
        })
        cases.append(("ultra-normalization", ultra_as_ordinary, "topology-changing"))
        topology = copy.deepcopy(valid)
        topology["diagnostics"][0]["tuple_decisions"] = []
        topology["diagnostic_capture_digest"] = successor.digest(successor.canonical_bytes(topology["diagnostics"]) + b"\n")
        cases.append(("topology", topology, "topology-changing"))
        secret = copy.deepcopy(valid)
        secret["diagnostics"][0]["diagnostic_fields"]["authorization_token"] = "secret"
        secret["diagnostic_capture_digest"] = successor.digest(successor.canonical_bytes(secret["diagnostics"]) + b"\n")
        cases.append(("secret", secret, "sanitized"))
        for label, request, message in cases:
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, message):
                successor.validate_successor_request(request, predecessor)

        mutated_predecessor = copy.deepcopy(predecessor)
        mutated_predecessor["candidate_freeze_id"] = capabilities.digest(b"historical-mutation")
        with self.assertRaisesRegex(ValueError, "prior freeze"):
            successor.build_successor_freeze(mutated_predecessor, valid, manifest=self.manifest)
        empty_intersection = copy.deepcopy(valid)
        empty_intersection["catalog_capture"] = self.catalog_capture(
            predecessor,
            successor,
            visible_models=[{
                "model": "unmatched-model",
                "default_effort": "Ordinary",
                "supported_efforts": ["Ordinary"],
            }],
        )
        with self.assertRaisesRegex(ValueError, "source/runtime intersection is empty"):
            successor.build_successor_freeze(predecessor, empty_intersection, manifest=self.manifest)
        missing_ordinary_normalization = copy.deepcopy(valid)
        missing_ordinary_normalization["catalog_capture"]["effort_normalization_map"] = [
            item for item in missing_ordinary_normalization["catalog_capture"]["effort_normalization_map"]
            if item["raw_effort"] != "Ordinary"
        ]
        missing_ordinary_normalization["catalog_capture"]["parsed_catalog_digest"] = successor.digest({
            "visible_models": missing_ordinary_normalization["catalog_capture"]["visible_models"],
            "defaults": missing_ordinary_normalization["catalog_capture"]["defaults"],
            "supported_efforts": missing_ordinary_normalization["catalog_capture"]["supported_efforts"],
            "effort_normalization_map": missing_ordinary_normalization["catalog_capture"]["effort_normalization_map"],
        })
        with self.assertRaisesRegex(ValueError, "canonical effort unknown"):
            successor.build_successor_freeze(predecessor, missing_ordinary_normalization, manifest=self.manifest)

    def test_unset_routes_use_the_models_actual_default_effort(self) -> None:
        successor = load_successor_module("g56r_003_successor_model_default")
        predecessor = self.predecessor_freeze()
        catalog = self.catalog_capture(
            predecessor,
            successor,
            visible_models=[{
                "model": "gpt-5.6-sol",
                "default_effort": "Ultra",
                "supported_efforts": ["Ordinary", "Ultra"],
            }],
        )
        request = self.successor_request(
            predecessor,
            successor,
            catalog_capture=catalog,
        )
        with self.assertRaisesRegex(ValueError, "source/runtime intersection is empty"):
            successor.build_successor_freeze(predecessor, request, manifest=self.manifest)

    def test_diagnostic_disagreement_excludes_catalog_supported_tuples(self) -> None:
        successor = load_successor_module("g56r_003_successor_diagnostic_disagreement")
        predecessor = self.predecessor_freeze()
        diagnostics = [{
            "surface": "cli",
            "captured_at": "2026-07-16T00:00:00Z",
            "reported_effort": "Ordinary",
            "diagnostic_fields": {
                "assignment.supported_effective_model": "different-model",
                "assignment.supported_effective_effort": "ordinary",
                "availability": True,
            },
        }]
        request = self.successor_request(
            predecessor,
            successor,
            diagnostics=diagnostics,
        )
        with self.assertRaisesRegex(ValueError, "source/runtime intersection is empty"):
            successor.build_successor_freeze(predecessor, request, manifest=self.manifest)


if __name__ == "__main__":
    unittest.main()
