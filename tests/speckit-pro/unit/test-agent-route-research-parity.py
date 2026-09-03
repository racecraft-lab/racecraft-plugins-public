#!/usr/bin/env python3
"""Validate official-source routing research and cross-platform parity."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
import unittest
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
LIB_DIR = TEST_ROOT / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted  # noqa: E402


RESEARCH_ROOT = REPO_ROOT / "docs" / "ai" / "research"
SCHEMA_PATH = RESEARCH_ROOT / "agent-route-candidate-manifest.schema.json"
MANIFEST_PATHS = (
    RESEARCH_ROOT / "claude-agent-route-candidate-manifest.json",
    RESEARCH_ROOT / "codex-agent-route-candidate-manifest.json",
)
LIVE_AGENT_NAMES = {
    "analyze-executor",
    "autopilot-fast-helper",
    "checklist-executor",
    "clarify-executor",
    "codebase-analyst",
    "consensus-synthesizer",
    "domain-researcher",
    "implement-executor",
    "phase-executor",
    "spec-context-analyst",
    "uat-runbook-author",
}
# The candidate-route manifests are frozen research evidence. A role retired from
# the live roster after the freeze stays bound there, so the parity check expects
# the historical catalog, not today's roster.
RETIRED_AGENT_NAMES = {"gate-validator"}
SHARED_AGENT_NAMES = LIVE_AGENT_NAMES | RETIRED_AGENT_NAMES
SHARED_EVIDENCE_CLASSES = {
    "official_documentation",
    "project_input",
    "runtime_verification_needed",
    "qualification_needed",
    "undocumented",
}
SHARED_SOURCE_FAMILIES = {
    "administrative_analytics",
    "authentication",
    "cost_management",
    "documentation_discovery",
    "effort_controls",
    "fast_mode",
    "feature_and_provider_availability",
    "hooks_and_effective_route",
    "interactive_commands",
    "model_catalog",
    "model_configuration_and_resolution",
    "model_lifecycle",
    "model_pricing",
    "noninteractive_output",
    "permissions_and_sandboxing",
    "plugin_agent_contract",
    "skills_and_delegation",
    "statusline_diagnostics",
    "subagent_configuration",
    "telemetry_and_observability",
    "tools_and_mcp",
}
PLATFORM_RULES = {
    "claude_code": {
        "spec_id": "CAR-001",
        "vendor": "anthropic",
        "domains": ("code.claude.com/docs/", "platform.claude.com/docs/"),
    },
    "codex": {
        "spec_id": "G56R-001",
        "vendor": "openai",
        "domains": (
            "learn.chatgpt.com/docs/",
            "developers.openai.com/codex/",
            "developers.openai.com/api/docs/",
            "platform.openai.com/docs/",
        ),
    },
}
TOP_LEVEL_RECORDS = {
    "snapshot": "snapshot",
    "evidence_authority": "evidenceAuthority",
    "immutable_production_comparator": "comparator",
}
ARRAY_RECORDS = {
    "official_source_ledger": "officialSource",
    "effort_surface_records": "effortSurface",
    "project_inputs": "projectInput",
    "agent_contracts": "agentContract",
    "candidate_routes": "candidateRoute",
    "fixture_backlog": "fixture",
    "telemetry_requirements": "telemetry",
    "capability_questions": "capabilityQuestion",
    "traceability": "traceability",
    "decisions": "decision",
    "invalidation_rules": "invalidationRule",
}
ID_FIELDS = {
    "official_source_ledger": "official_source_ledger_id",
    "effort_surface_records": "effort_surface_record_id",
    "project_inputs": "project_input_id",
    "agent_contracts": "agent_contract_id",
    "candidate_routes": "candidate_route_id",
    "fixture_backlog": "fixture_backlog_id",
    "telemetry_requirements": "telemetry_requirement_id",
    "capability_questions": "capability_question_id",
    "decisions": "decision_id",
    "invalidation_rules": "invalidation_rule_id",
}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")


class ManifestContractError(AssertionError):
    """Raised when a routing manifest violates the shared contract."""


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_keys(schema: dict[str, object], definition: str | None = None) -> set[str]:
    node = schema if definition is None else schema["$defs"][definition]
    return set(node["properties"])


def require_exact_keys(
    value: object,
    expected: set[str],
    context: str,
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ManifestContractError(f"{context}: expected object")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ManifestContractError(f"{context}: missing={missing}, extra={extra}")
    return value


def require_unique_ids(records: object, id_field: str, context: str) -> set[str]:
    if not isinstance(records, list) or not records:
        raise ManifestContractError(f"{context}: expected a non-empty list")
    values = [record.get(id_field) for record in records if isinstance(record, dict)]
    if len(values) != len(records) or not all(isinstance(value, str) and value for value in values):
        raise ManifestContractError(f"{context}: every record requires {id_field}")
    if len(values) != len(set(values)):
        raise ManifestContractError(f"{context}: duplicate {id_field}")
    return set(values)


def require_refs(refs: object, allowed: set[str], context: str, *, nonempty: bool = False) -> None:
    if not isinstance(refs, list) or (nonempty and not refs):
        raise ManifestContractError(f"{context}: expected {'non-empty ' if nonempty else ''}list")
    unresolved = sorted(ref for ref in refs if ref not in allowed)
    if unresolved:
        raise ManifestContractError(f"{context}: unresolved refs {unresolved}")


def require_sha256(value: object, context: str) -> None:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise ManifestContractError(f"{context}: expected lowercase SHA-256")


def require_utc_timestamp(value: object, context: str) -> None:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ManifestContractError(f"{context}: expected UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ManifestContractError(f"{context}: invalid timestamp") from exc
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise ManifestContractError(f"{context}: timestamp is not UTC")


def canonical_url_allowed(url: object, domains: tuple[str, ...]) -> bool:
    if not isinstance(url, str):
        return False
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        return False
    normalized = f"{parsed.netloc}/{parsed.path.lstrip('/')}"
    return any(
        normalized == domain.rstrip("/") or normalized.startswith(domain)
        for domain in domains
    )


def validate_manifest(manifest: dict[str, object], schema: dict[str, object]) -> None:
    require_exact_keys(manifest, schema_keys(schema), "manifest")
    if manifest["schema_version"] != "2.0.0":
        raise ManifestContractError("manifest: schema_version must be 2.0.0")
    if manifest["manifest_kind"] != "agent_route_candidate_manifest":
        raise ManifestContractError("manifest: unexpected manifest_kind")
    if manifest["provisional"] is not True:
        raise ManifestContractError("manifest: candidate baseline must remain provisional")

    platform = manifest["platform"]
    if platform not in PLATFORM_RULES:
        raise ManifestContractError(f"manifest: unsupported platform {platform!r}")
    rules = PLATFORM_RULES[platform]
    if manifest["spec_id"] != rules["spec_id"]:
        raise ManifestContractError("manifest: platform/spec_id mismatch")

    for field, definition in TOP_LEVEL_RECORDS.items():
        require_exact_keys(manifest[field], schema_keys(schema, definition), field)
    for field, definition in ARRAY_RECORDS.items():
        records = manifest[field]
        if not isinstance(records, list):
            raise ManifestContractError(f"{field}: expected list")
        for index, record in enumerate(records):
            require_exact_keys(record, schema_keys(schema, definition), f"{field}[{index}]")

    snapshot = manifest["snapshot"]
    require_utc_timestamp(snapshot["captured_at_utc"], "snapshot.captured_at_utc")
    dispositions = snapshot["legacy_fact_dispositions"]
    if not isinstance(dispositions, list):
        raise ManifestContractError("snapshot.legacy_fact_dispositions: expected list")
    for index, disposition in enumerate(dispositions):
        require_exact_keys(
            disposition,
            schema_keys(schema, "factDisposition"),
            f"snapshot.legacy_fact_dispositions[{index}]",
        )

    authority = manifest["evidence_authority"]
    if authority["vendor"] != rules["vendor"]:
        raise ManifestContractError("evidence_authority: platform/vendor mismatch")
    if tuple(authority["authoritative_domains"]) != rules["domains"]:
        raise ManifestContractError("evidence_authority: authoritative domain allowlist drift")
    if set(authority["evidence_classes"]) != SHARED_EVIDENCE_CLASSES:
        raise ManifestContractError("evidence_authority: evidence class drift")

    comparator = manifest["immutable_production_comparator"]
    if not COMMIT_SHA.fullmatch(comparator["commit_sha"]):
        raise ManifestContractError("immutable_production_comparator: invalid commit SHA")

    ids = {
        field: (
            set()
            if field == "capability_questions" and not manifest[field]
            else require_unique_ids(manifest[field], id_field, field)
        )
        for field, id_field in ID_FIELDS.items()
    }
    source_ids = ids["official_source_ledger"]
    effort_ids = ids["effort_surface_records"]
    agent_ids = ids["agent_contracts"]
    fixture_ids = ids["fixture_backlog"]
    question_ids = ids["capability_questions"]

    sources = manifest["official_source_ledger"]
    if {source["source_family"] for source in sources} != SHARED_SOURCE_FAMILIES:
        raise ManifestContractError("official_source_ledger: shared source-family matrix is incomplete")
    for source in sources:
        source_id = source["official_source_ledger_id"]
        if source["vendor"] != rules["vendor"]:
            raise ManifestContractError(f"{source_id}: platform/vendor mismatch")
        if not canonical_url_allowed(source["canonical_url"], rules["domains"]):
            raise ManifestContractError(f"{source_id}: canonical URL is outside the vendor allowlist")
        require_utc_timestamp(source["retrieved_at_utc"], f"{source_id}.retrieved_at_utc")
        require_sha256(source["body_sha256"], f"{source_id}.body_sha256")
        if not isinstance(source["http_status"], int) or not 200 <= source["http_status"] <= 399:
            raise ManifestContractError(f"{source_id}: unsuccessful HTTP status")
        if not isinstance(source["body_bytes"], int) or source["body_bytes"] < 1:
            raise ManifestContractError(f"{source_id}: empty source body")
        extracts = source["bounded_extracts"]
        if not isinstance(extracts, list) or not extracts:
            raise ManifestContractError(f"{source_id}: bounded extract required")
        for index, extract in enumerate(extracts):
            require_exact_keys(
                extract,
                schema_keys(schema, "boundedExtract"),
                f"{source_id}.bounded_extracts[{index}]",
            )
            expected_hash = hashlib.sha256(extract["text"].encode("utf-8")).hexdigest()
            if extract["extract_sha256"] != expected_hash:
                raise ManifestContractError(f"{source_id}: bounded extract hash mismatch")

    for record in manifest["effort_surface_records"]:
        require_refs(
            [record["official_source_ledger_id"]],
            source_ids,
            f"{record['effort_surface_record_id']}.official_source_ledger_id",
            nonempty=True,
        )

    contracts = manifest["agent_contracts"]
    if {contract["agent_name"] for contract in contracts} != SHARED_AGENT_NAMES:
        raise ManifestContractError("agent_contracts: shared twelve-agent catalog drift")
    instruction_hash_by_agent_id: dict[str, str] = {}
    for contract in contracts:
        contract_id = contract["agent_contract_id"]
        require_sha256(contract["source_sha256"], f"{contract_id}.source_sha256")
        require_sha256(contract["instruction_sha256"], f"{contract_id}.instruction_sha256")
        require_refs(contract["fixture_backlog_ids"], fixture_ids, f"{contract_id}.fixture_backlog_ids", nonempty=True)
        require_exact_keys(
            contract["production_route"],
            schema_keys(schema, "productionRoute"),
            f"{contract_id}.production_route",
        )
        instruction_hash_by_agent_id[contract_id] = contract["instruction_sha256"]

    fixture_agent_ids: list[str] = []
    for fixture in manifest["fixture_backlog"]:
        fixture_id = fixture["fixture_backlog_id"]
        require_refs([fixture["agent_contract_id"]], agent_ids, f"{fixture_id}.agent_contract_id", nonempty=True)
        fixture_agent_ids.append(fixture["agent_contract_id"])
    if set(fixture_agent_ids) != agent_ids or len(fixture_agent_ids) != len(agent_ids):
        raise ManifestContractError("fixture_backlog: expected exactly one fixture record per agent")

    candidate_agent_ids: set[str] = set()
    for route in manifest["candidate_routes"]:
        route_id = route["candidate_route_id"]
        require_exact_keys(route["model_selector"], schema_keys(schema, "modelSelector"), f"{route_id}.model_selector")
        require_exact_keys(route["effort_selector"], schema_keys(schema, "effortSelector"), f"{route_id}.effort_selector")
        require_exact_keys(route["lifecycle"], schema_keys(schema, "lifecycle"), f"{route_id}.lifecycle")
        require_refs([route["agent_contract_id"]], agent_ids, f"{route_id}.agent_contract_id", nonempty=True)
        require_refs(route["official_source_ledger_ids"], source_ids, f"{route_id}.official_source_ledger_ids", nonempty=True)
        require_refs(route["effort_surface_record_ids"], effort_ids, f"{route_id}.effort_surface_record_ids", nonempty=True)
        require_refs(route["capability_question_refs"], question_ids, f"{route_id}.capability_question_refs")
        lifecycle_source = route["lifecycle"]["official_source_ledger_id"]
        if lifecycle_source is not None:
            require_refs([lifecycle_source], source_ids, f"{route_id}.lifecycle.official_source_ledger_id", nonempty=True)
        if route["executability_status"] != "not_executable_pending_capability_and_qualification":
            raise ManifestContractError(f"{route_id}: candidate became executable in the baseline")
        if route["role_instruction_sha256"] != instruction_hash_by_agent_id[route["agent_contract_id"]]:
            raise ManifestContractError(f"{route_id}: role instruction hash drift")
        candidate_agent_ids.add(route["agent_contract_id"])
    if candidate_agent_ids != agent_ids:
        raise ManifestContractError("candidate_routes: every shared agent requires at least one candidate")

    for telemetry in manifest["telemetry_requirements"]:
        source_id = telemetry["official_source_ledger_id"]
        if source_id is not None:
            require_refs([source_id], source_ids, f"{telemetry['telemetry_requirement_id']}.official_source_ledger_id", nonempty=True)
    for trace in manifest["traceability"]:
        require_refs(trace["official_source_ledger_ids"], source_ids, f"traceability.{trace['requirement_id']}")
    for disposition in dispositions:
        require_refs(
            disposition["official_source_ledger_ids"],
            source_ids,
            f"legacy_fact_dispositions.{disposition['legacy_fact_id']}",
        )


class AgentRouteResearchParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_json(SCHEMA_PATH)
        cls.manifests = [load_json(path) for path in MANIFEST_PATHS if path.is_file()]

    def test_schema_is_strict_and_symmetric(self) -> None:
        self.assertEqual(self.schema["properties"]["schema_version"]["const"], "2.0.0")
        self.assertFalse(self.schema["additionalProperties"])
        self.assertEqual(set(self.schema["required"]), schema_keys(self.schema))
        for definition in set(TOP_LEVEL_RECORDS.values()) | set(ARRAY_RECORDS.values()):
            node = self.schema["$defs"][definition]
            self.assertFalse(node["additionalProperties"], definition)
            self.assertEqual(set(node["required"]), schema_keys(self.schema, definition), definition)

    def test_present_manifests_satisfy_the_shared_contract(self) -> None:
        self.assertTrue(MANIFEST_PATHS[0].is_file(), "Claude baseline manifest is required")
        for manifest in self.manifests:
            with self.subTest(platform=manifest["platform"]):
                validate_manifest(manifest, self.schema)

    def test_both_platforms_use_identical_record_shapes_when_present(self) -> None:
        if len(self.manifests) < 2:
            self.skipTest("Codex manifest lands on the dependent G56R-001 branch")
        left, right = self.manifests
        self.assertEqual(set(left), set(right))
        for field in ARRAY_RECORDS:
            if left[field] and right[field]:
                self.assertEqual(set(left[field][0]), set(right[field][0]), field)
        self.assertEqual(
            {record["agent_name"] for record in left["agent_contracts"]},
            {record["agent_name"] for record in right["agent_contracts"]},
        )

    def test_vendor_authority_is_fail_closed(self) -> None:
        manifest = copy.deepcopy(self.manifests[0])
        manifest["official_source_ledger"][0]["canonical_url"] = "https://example.com/docs/models"
        with self.assertRaisesRegex(ManifestContractError, "outside the vendor allowlist"):
            validate_manifest(manifest, self.schema)

    def test_unresolved_source_reference_is_rejected(self) -> None:
        manifest = copy.deepcopy(self.manifests[0])
        manifest["candidate_routes"][0]["official_source_ledger_ids"] = ["MISSING-SOURCE"]
        with self.assertRaisesRegex(ManifestContractError, "unresolved refs"):
            validate_manifest(manifest, self.schema)

    def test_empty_capability_questions_satisfies_shared_contract(self) -> None:
        manifest = copy.deepcopy(self.manifests[0])
        manifest["capability_questions"] = []
        for route in manifest["candidate_routes"]:
            route["capability_question_refs"] = []

        validate_manifest(manifest, self.schema)

    def test_other_id_arrays_remain_nonempty(self) -> None:
        for field in ID_FIELDS:
            if field == "capability_questions":
                continue
            with self.subTest(field=field):
                manifest = copy.deepcopy(self.manifests[0])
                manifest[field] = []
                with self.assertRaisesRegex(
                    ManifestContractError,
                    rf"^{field}: expected a non-empty list$",
                ):
                    validate_manifest(manifest, self.schema)

    def test_platform_only_top_level_field_is_rejected(self) -> None:
        manifest = copy.deepcopy(self.manifests[0])
        manifest["platform_only_extension"] = {}
        with self.assertRaisesRegex(ManifestContractError, "extra=.*platform_only_extension"):
            validate_manifest(manifest, self.schema)

    def test_prds_and_roadmaps_bind_the_shared_contract(self) -> None:
        paired_files = (
            REPO_ROOT / "docs" / "prd-claude-agent-routing.md",
            REPO_ROOT / "docs" / "prd-codex-gpt-5-6-agent-routing.md",
            REPO_ROOT / "docs" / "ai" / "specs" / "claude-agent-routing-technical-roadmap.md",
            REPO_ROOT / "docs" / "ai" / "specs" / "codex-gpt-5-6-agent-routing-technical-roadmap.md",
        )
        for path in paired_files:
            text = path.read_text(encoding="utf-8")
            self.assertIn("agent-routing-parity-contract.md", text, path)
            self.assertIn("agent-route-candidate-manifest.schema.json", text, path)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AgentRouteResearchParityTests)
    raise SystemExit(run_counted(suite, label="test-agent-route-research-parity"))
