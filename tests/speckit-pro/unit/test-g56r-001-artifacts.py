#!/usr/bin/env python3
"""Focused contracts for the G56R-001 research artifact checker."""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[3]
CHECKER = REPO_ROOT / "specs" / "g56r-001-candidate-route-baseline" / "check-artifacts.py"
NARRATIVE_PATH = Path("docs/ai/research/codex-agent-route-candidates.md")
MANIFEST_PATH = Path("docs/ai/research/codex-agent-route-candidate-manifest.json")
AGENT_NAMES = {
    "analyze-executor",
    "autopilot-fast-helper",
    "checklist-executor",
    "clarify-executor",
    "codebase-analyst",
    "consensus-synthesizer",
    "domain-researcher",
    "gate-validator",
    "implement-executor",
    "phase-executor",
    "spec-context-analyst",
    "uat-runbook-author",
}
ABSENT_AGENTS = {"consensus-synthesizer", "gate-validator"}
CURRENT_FIXTURES = {"codebase-analyst", "domain-researcher", "spec-context-analyst"}
SURFACES = {"cli", "desktop_app", "app_server", "non_interactive"}
SEMANTIC_FIELDS = (
    "role_boundary",
    "authorization_boundaries",
    "safety_requirements",
    "grounding_requirements",
    "mutation_policy",
    "tool_requirements",
    "skill_requirements",
    "mcp_requirements",
    "sandbox_expectations",
    "output_contract",
    "supported_client_assumptions",
    "representative_tasks",
)
CAPABILITY_FIELDS = {
    "model",
    "modalities",
    "reasoning_effort",
    "custom_agents",
    "tools",
    "skills",
    "mcp",
    "sandbox",
    "mutation",
    "clients",
}
GATE_IDS = {
    "artifact_presence",
    "agent_route_coverage",
    "contract_completeness",
    "candidate_completeness",
    "provenance_freshness",
    "cross_artifact_agreement",
    "fixture_contracts",
    "telemetry_requirements",
    "classified_unknowns",
    "sanitization",
    "conflict_disposition",
}
PLATFORM_FEATURES = (
    "model_identifiers",
    "custom_agent_fields",
    "reasoning_controls",
    "capability_discovery",
    "telemetry",
    "reroute_events",
    "non_interactive_output",
)
INTEGRATION_CLASSES = (
    "installer",
    "skill",
    "validation",
    "evaluation",
    "generated_payload",
    "cache",
    "installed_state",
)
PROJECTION_START = "<!-- g56r-001-agreement-projection:start -->"
PROJECTION_END = "<!-- g56r-001-agreement-projection:end -->"
NARRATIVE_HASH_MARKER = re.compile(
    r"<!-- g56r-001-human-narrative-sha256:(sha256:[0-9a-f]{64}) -->"
)
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted  # noqa: E402


def load_checker() -> ModuleType:
    spec = importlib.util.spec_from_file_location("g56r_001_check_artifacts", CHECKER)
    if spec is None or spec.loader is None:
        raise AssertionError(f"unable to load checker: {CHECKER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_text(root: Path, relative: Path, content: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def normalize(value: object) -> object:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    return value


def canonical_hash(value: object) -> str:
    encoded = json.dumps(
        normalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def instruction_hash(body: str) -> str:
    normalized = normalize(body)
    assert isinstance(normalized, str)
    return f"sha256:{hashlib.sha256(normalized.encode('utf-8')).hexdigest()}"


def fixture_instruction_body(name: str) -> str:
    return f"Role instructions for {name}.\r\nPreserve hard boundaries.\r"


def slug(value: str) -> str:
    return "-".join(filter(None, re.split(r"[^a-z0-9]+", value.lower())))


def expected_manifest_hash(manifest: dict[str, object]) -> str:
    payload = copy.deepcopy(manifest)
    payload["handoff"]["admission_binding"].pop("manifest_content_hash", None)
    return canonical_hash(payload)


def refresh_manifest_hash(manifest: dict[str, object]) -> None:
    manifest["handoff"]["admission_binding"]["manifest_content_hash"] = expected_manifest_hash(manifest)


def human_narrative_hash(narrative: str) -> str:
    start = narrative.find(PROJECTION_START)
    end = narrative.find(PROJECTION_END, start + len(PROJECTION_START)) if start >= 0 else -1
    if start >= 0 and end >= 0:
        narrative = (
            narrative[:start]
            + PROJECTION_START
            + "\n"
            + PROJECTION_END
            + narrative[end + len(PROJECTION_END):]
        )
    narrative = NARRATIVE_HASH_MARKER.sub(
        "<!-- g56r-001-human-narrative-sha256:<content-hash> -->",
        narrative,
    )
    narrative = re.sub(
        r"(?m)^\*\*Manifest content hash:\*\* `sha256:[0-9a-f]{64}`$",
        "**Manifest content hash:** `<manifest-content-hash>`",
        narrative,
    )
    normalized = normalize(narrative)
    assert isinstance(normalized, str)
    return f"sha256:{hashlib.sha256(normalized.encode('utf-8')).hexdigest()}"


def project_provenance(name: str) -> dict[str, object]:
    return {
        "evidence_id": f"project-{name}",
        "evidence_class": "tracked_source",
        "classification": "project_fact",
        "exact_locator": f"agent definition for {name}",
        "observed_or_retrieved_on": "2026-07-14",
        "surface": "repository",
        "feature": "agent route and semantic contract",
        "documented_scope": "pinned repository revision",
        "applicability": "documented",
        "conflict_status": "none",
        "invalidation_triggers": ["repository revision changes"],
        "repository_path": f"speckit-pro/codex-agents/{name}.toml",
        "repository_revision": "0123456789abcdef",
        "evidence_role": "canonical tracked agent definition",
    }


def surface_provenance(name: str, feature: str, surface: str) -> dict[str, object]:
    sources = {
        "model_identifiers": (
            "https://developers.openai.com/codex/models",
            "Recommended models; Choose a model",
        ),
        "reasoning_controls": (
            "https://developers.openai.com/codex/config-reference",
            "model_reasoning_effort",
        ),
        "custom_agent_fields": (
            "https://developers.openai.com/codex/subagents",
            "Custom agents; Custom agent file schema",
        ),
        "capability_discovery": (
            "https://developers.openai.com/codex/app-server",
            "Models / List models (model/list); Model provider capabilities; Experimental features",
        ),
        "telemetry": (
            "https://developers.openai.com/codex/config-advanced",
            "Observability and telemetry",
        ),
        "reroute_events": (
            "https://developers.openai.com/codex/cyber-safety",
            "How it works; False positives",
        ),
        "non_interactive_output": (
            "https://developers.openai.com/codex/noninteractive",
            "Make output machine-readable; --json; --output-schema",
        ),
    }
    source_url, exact_locator = sources[feature]
    return {
        "evidence_id": f"surface-{name}-{feature}-{surface}",
        "evidence_class": "official_openai",
        "classification": "platform_fact",
        "exact_locator": exact_locator,
        "observed_or_retrieved_on": "2026-07-14",
        "surface": surface,
        "feature": feature,
        "documented_scope": f"{feature} evidence scoped to {surface}.",
        "applicability": "documented_for_named_scope_only",
        "conflict_status": "none",
        "invalidation_triggers": ["official documentation changes"],
        "source_url": source_url,
    }


def basic_manifest() -> dict[str, object]:
    agents = []
    for agent_index, name in enumerate(sorted(AGENT_NAMES)):
        absent = name in ABSENT_AGENTS
        semantics = {
            field: (
                f"{field} for {name}: permitted behavior is bounded; prohibited behavior is rejected; "
                "stop and escalate to the parent agent on conflict."
            )
            for field in SEMANTIC_FIELDS
        }
        semantics["authorization_boundaries"] = (
            f"Authorization for {name}: permitted work follows the parent task; prohibited expansion "
            "requires stopping; only the parent or maintainer may approve escalation."
        )
        body = fixture_instruction_body(name)
        contract = {
            "agent_contract_id": f"agent-contract/{name}/v1",
            "instruction_hash": instruction_hash(body),
            **semantics,
        }
        contract["contract_hash"] = canonical_hash({"agent_name": name, **semantics})
        if absent:
            contract["semantic_mappings"] = [
                {
                    "contract_field": field,
                    "claude_repository_path": f"speckit-pro/agents/{name}.md",
                    "claude_repository_revision": "0123456789abcdef",
                    "claude_exact_locator": f"instruction body semantics for {field}",
                    "mapping_status": "codex_adapted",
                    "justification": "Preserve the semantic boundary without Claude transport syntax.",
                    "mapped_codex_contract_value": semantics[field],
                }
                for field in SEMANTIC_FIELDS
            ]
        model_id = "gpt-5.4"
        reasoning_effort = "high"
        candidate_id = (
            f"candidate-route/{name}/{slug(model_id)}/{slug(reasoning_effort)}/unchanged/v1"
        )
        candidate = {
            "candidate_route_id": candidate_id,
            "agent_contract_id": contract["agent_contract_id"],
            "model_id": model_id,
            "reasoning_effort": reasoning_effort,
            "treatment": "unchanged",
            "instruction_hash": contract["instruction_hash"],
            "contract_hash": contract["contract_hash"],
            "project_eligibility": {
                "status": "eligible",
                "basis": "immutable production baseline or evidence-supported parity candidate",
                "evidence_ids": [f"project-{name}"],
            },
            "installation_availability": {
                "status": "unresolved_g56r_002",
                "observations": [],
            },
            "capability_requirements": {
                field: f"requirement for {field}"
                for field in sorted(CAPABILITY_FIELDS)
            },
            "rationale": {
                "classification": "hypothesis",
                "summary": "Retain the unchanged attribution control without ranking it.",
                "evidence_ids": [f"project-{name}"],
            },
            "known_incompatibilities": [],
            "qualification_requirements": {
                "status": "unqualified",
                "capability_checks": ["versioned capability snapshot"],
                "fixture": f"fixture contract for {name}",
                "required_artifacts": ["capability result", "fixture result"],
                "telemetry": ["effective route proof"],
                "owner_spec": "G56R-002",
            },
            "provenance": [project_provenance(name)],
            "invalidation_triggers": ["tracked route or contract changes"],
        }
        source_entry_id = f"inventory/{name}/source"
        consumer_entry_id = f"inventory/{name}/consumer"
        inventory = [
            {
                "entry_id": source_entry_id,
                "locator": f"speckit-pro/codex-agents/{name}.toml",
                "integration_class": "source",
                "role": "producer",
                "affected_agents": [name],
                "policy_fields": ["model_id", "reasoning_effort", "instructions"],
                "authority_class": "canonical_project_source",
                "evidence_class": "tracked_source",
                "relationship": "canonical_input",
                "canonical_input_entry_id": None,
                "upstream_entry_ids": [],
                "downstream_entry_ids": [consumer_entry_id],
                "revision_or_version": "0123456789abcdef",
                "observed_on": "2026-07-14",
                "mismatch_status": "matches",
                "defect_owner": None,
            },
            {
                "entry_id": consumer_entry_id,
                "locator": f"codex_plugin_payload/speckit-pro/codex-agents/{name}.toml",
                "integration_class": INTEGRATION_CLASSES[agent_index % len(INTEGRATION_CLASSES)],
                "role": "consumer",
                "affected_agents": [name],
                "policy_fields": ["model_id", "reasoning_effort", "instructions"],
                "authority_class": "derived_output",
                "evidence_class": "tracked_source",
                "relationship": "derived_output",
                "canonical_input_entry_id": source_entry_id,
                "upstream_entry_ids": [source_entry_id],
                "downstream_entry_ids": [],
                "revision_or_version": "0123456789abcdef",
                "observed_on": "2026-07-14",
                "mismatch_status": "matches",
                "defect_owner": None,
            },
        ]
        physical_families = ["CLAUDE"] if absent else ["CODEX"]
        for family in physical_families:
            physical_source = f"RP-SRC-{family}-{name}"
            physical_payload = f"RP-PAYLOAD-{family}-{name}"
            inventory.extend(
                [
                    {
                        "entry_id": physical_source,
                        "locator": f"speckit-pro/{'codex-agents' if family == 'CODEX' else 'agents'}/{name}.{'toml' if family == 'CODEX' else 'md'}",
                        "integration_class": "source",
                        "role": "producer",
                        "affected_agents": [name],
                        "policy_fields": ["model_id", "reasoning_effort", "instructions"],
                        "authority_class": "canonical_project_source",
                        "evidence_class": "tracked_source",
                        "relationship": "canonical_input",
                        "canonical_input_entry_id": None,
                        "upstream_entry_ids": [],
                        "downstream_entry_ids": [physical_payload],
                        "revision_or_version": "0123456789abcdef",
                        "observed_on": "2026-07-14",
                        "mismatch_status": "matches",
                        "defect_owner": None,
                    },
                    {
                        "entry_id": physical_payload,
                        "locator": f"dist/{family.lower()}/speckit-pro/{'codex-agents' if family == 'CODEX' else 'agents'}/{name}.{'toml' if family == 'CODEX' else 'md'}",
                        "integration_class": "generated_payload",
                        "role": "producer_consumer",
                        "affected_agents": [name],
                        "policy_fields": ["model_id", "reasoning_effort", "instructions"],
                        "authority_class": "derived_output",
                        "evidence_class": "tracked_source",
                        "relationship": "derived_output",
                        "canonical_input_entry_id": physical_source,
                        "upstream_entry_ids": [physical_source],
                        "downstream_entry_ids": [],
                        "revision_or_version": "0123456789abcdef",
                        "observed_on": "2026-07-14",
                        "mismatch_status": "matches",
                        "defect_owner": None,
                    },
                ]
            )
        agents.append(
            {
                "agent_name": name,
                "agent_contract": contract,
                "production_route": {
                    "status": "absent" if absent else "present",
                    "candidate_route_id": None if absent else candidate_id,
                    "model_id": None if absent else model_id,
                    "reasoning_effort": None if absent else reasoning_effort,
                    "instruction_hash": None if absent else contract["instruction_hash"],
                    "contract_hash": None if absent else contract["contract_hash"],
                    "absence_reason": (
                        f"No tracked Codex production route exists for {name}; see project-{name}."
                        if absent
                        else None
                    ),
                    "provenance": [project_provenance(name)],
                    "invalidation_triggers": ["tracked route changes"],
                },
                "candidates": [candidate],
                "route_policy_inventory": inventory,
                "source_observations": [
                    {
                        "evidence_class": "tracked_source",
                        "agent_name": name,
                        "model_id": None if absent else model_id,
                        "reasoning_effort": None if absent else reasoning_effort,
                        "instruction_hash": contract["instruction_hash"],
                        "contract_hash": contract["contract_hash"],
                        "observed_on": "2026-07-14",
                        "surface": "repository",
                        "version": None,
                        "repository_path": f"speckit-pro/codex-agents/{name}.toml",
                        "repository_revision": "0123456789abcdef",
                        "evidence_role": "canonical tracked agent definition",
                        "mismatch_status": "matches",
                        "defect_owner": None,
                    },
                    {
                        "evidence_class": "cached_source",
                        "agent_name": name,
                        "model_id": None if absent else model_id,
                        "reasoning_effort": None if absent else reasoning_effort,
                        "instruction_hash": contract["instruction_hash"],
                        "contract_hash": contract["contract_hash"],
                        "observed_on": "2026-07-14",
                        "surface": "cli",
                        "version": "2.19.1",
                        "logical_locator": f"codex_plugin_cache/speckit-pro/codex-agents/{name}",
                        "mismatch_status": "matches",
                        "defect_owner": None,
                    },
                    {
                        "evidence_class": "installed_state",
                        "agent_name": name,
                        "model_id": None if absent else model_id,
                        "reasoning_effort": None if absent else reasoning_effort,
                        "instruction_hash": contract["instruction_hash"],
                        "contract_hash": contract["contract_hash"],
                        "observed_on": "2026-07-14",
                        "surface": "cli",
                        "version": "2.19.1",
                        "logical_locator": f"installed_codex_plugin/speckit-pro/codex-agents/{name}",
                        "mismatch_status": "matches",
                        "defect_owner": None,
                    },
                ],
                "surface_records": [
                    {
                        "surface": surface,
                        "applicability": "undocumented",
                        "feature": feature,
                        "evidence_ids": [f"surface-{name}-{feature}-{surface}"],
                        "documented_scope": "not_stated",
                        "conflict_status": "none",
                    }
                    for feature in sorted(PLATFORM_FEATURES)
                    for surface in sorted(SURFACES)
                ],
                "fixture_contract": {
                    "status": "current" if name in CURRENT_FIXTURES else "missing",
                    "fixture_path": (
                        f"tests/speckit-pro/layer6-efficiency/fixtures/{name}"
                        if name in CURRENT_FIXTURES
                        else None
                    ),
                    "representative_task": f"Exercise the {name} role contract.",
                    "input_type": "bounded agent task packet",
                    "expected_behavior": "Preserve all hard role boundaries and stop on conflict.",
                    "expected_output_shape": "structured findings and completion status",
                    "hard_contract_assertions": list(SEMANTIC_FIELDS),
                    "evidence_class": (
                        "current_release_evidence"
                        if name in CURRENT_FIXTURES
                        else "non_release_evidence"
                    ),
                },
                "telemetry_requirements": [
                    {
                        "field_or_proof": "effective route identity",
                        "purpose": "bind capability results to the tested candidate",
                        "required_for": "capability_preflight",
                        "owner_spec": "G56R-002",
                        "current_status": "deferred",
                    }
                ],
                "classified_unknowns": [
                    {
                        "unknown_id": f"unknown/{name}/installation-availability",
                        "class": "executable_capability",
                        "question": f"Is the candidate route installable for {name}?",
                        "impact": "Blocks runtime admission but not project eligibility.",
                        "owner_spec": "G56R-002",
                        "required_follow_up": "Evaluate against a versioned capability snapshot.",
                        "status": "deferred",
                    }
                ],
                "provenance": [
                    project_provenance(name),
                    *(
                        surface_provenance(name, feature, surface)
                        for feature in sorted(PLATFORM_FEATURES)
                        for surface in sorted(SURFACES)
                    ),
                ],
                "invalidation_triggers": [
                    "tracked route changes",
                    "official platform documentation changes",
                ],
            }
        )
    manifest = {
        "manifest_type": "agent_route_candidate_manifest",
        "manifest_version": 1,
        "research_date": "2026-07-14",
        "agents": agents,
        "handoff": {
            "decision": "go",
            "started_at": "2026-07-14T09:00:00-05:00",
            "stopped_at": "2026-07-14T16:00:00-05:00",
            "deadline_at": "2026-07-14T17:00:00-05:00",
            "completed_artifacts": [
                NARRATIVE_PATH.as_posix(),
                MANIFEST_PATH.as_posix(),
                "specs/g56r-001-candidate-route-baseline/check-artifacts.py",
            ],
            "completion_checks": [
                {
                    "gate_id": gate_id,
                    "requirement_refs": ["FR-024"],
                    "condition": f"Objective {gate_id} validation passes.",
                    "status": "pass",
                    "evidence_ids": [f"check-{gate_id}"],
                }
                for gate_id in sorted(GATE_IDS)
            ],
            "unmet_conditions": [],
            "admission_binding": {
                "manifest_type": "agent_route_candidate_manifest",
                "manifest_version": 1,
                "research_revision": "0123456789abcdef",
                "manifest_content_hash": "sha256:" + "0" * 64,
                "production_routes": [
                    {
                        "agent_name": record["agent_name"],
                        **{
                            key: record["production_route"][key]
                            for key in (
                                "status",
                                "candidate_route_id",
                                "model_id",
                                "reasoning_effort",
                                "instruction_hash",
                                "contract_hash",
                            )
                        },
                    }
                    for record in agents
                ],
                "contracts": [
                    {
                        "agent_name": record["agent_name"],
                        **{
                            key: record["agent_contract"][key]
                            for key in ("agent_contract_id", "instruction_hash", "contract_hash")
                        },
                    }
                    for record in agents
                ],
                "candidates": [
                    {
                        "agent_name": record["agent_name"],
                        **{
                            key: candidate[key]
                            for key in (
                                "candidate_route_id",
                                "agent_contract_id",
                                "model_id",
                                "reasoning_effort",
                                "treatment",
                                "instruction_hash",
                                "contract_hash",
                            )
                        },
                    }
                    for record in agents
                    for candidate in record["candidates"]
                ],
                "capability_snapshot_requirement": {
                    "owner_spec": "G56R-002",
                    "status": "required_at_admission",
                },
            },
        },
    }
    refresh_manifest_hash(manifest)
    return manifest


def write_artifacts(root: Path, manifest: dict[str, object]) -> None:
    for name in sorted(AGENT_NAMES):
        body = fixture_instruction_body(name)
        if name in ABSENT_AGENTS:
            write_text(
                root,
                Path(f"speckit-pro/agents/{name}.md"),
                f"---\nname: {name}\n---\n{body}",
            )
        else:
            write_text(
                root,
                Path(f"speckit-pro/codex-agents/{name}.toml"),
                f"name = {json.dumps(name)}\n"
                f"developer_instructions = {json.dumps(body)}\n",
            )
    narrative_prefix = (
        "# Candidate Route Baseline\n\n"
        "<!-- g56r-001-human-narrative-sha256:sha256:"
        + "0" * 64
        + " -->\n\n"
        "started_at: 2026-07-14T09:00:00-05:00\n"
        "deadline_at: 2026-07-14T17:00:00-05:00\n\n"
        "## Normalized agreement projection\n\n"
    )
    narrative_template = narrative_prefix + f"{PROJECTION_START}\n{PROJECTION_END}\n"
    narrative_prefix = NARRATIVE_HASH_MARKER.sub(
        "<!-- g56r-001-human-narrative-sha256:"
        + human_narrative_hash(narrative_template)
        + " -->",
        narrative_prefix,
    )
    projection = json.dumps(
        normalize(manifest),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    write_text(
        root,
        NARRATIVE_PATH,
        narrative_prefix
        + f"{PROJECTION_START}\n```json\n{projection}\n```\n{PROJECTION_END}\n",
    )
    write_text(
        root,
        MANIFEST_PATH,
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    )


class G56R001ArtifactTests(unittest.TestCase):
    def require_checker(self) -> ModuleType:
        self.assertTrue(CHECKER.is_file(), f"checker does not exist: {CHECKER}")
        return load_checker()

    def validation_errors(
        self,
        checker: ModuleType,
        manifest: dict[str, object],
    ) -> list[str]:
        refresh_manifest_hash(manifest)
        with tempfile.TemporaryDirectory(prefix="g56r-001-artifacts-") as temporary:
            root = Path(temporary)
            write_artifacts(root, manifest)
            return checker.validate_repository(root)

    def test_missing_manifest_failure_names_the_fixed_artifact(self) -> None:
        checker = self.require_checker()
        with tempfile.TemporaryDirectory(prefix="g56r-001-artifacts-") as temporary:
            root = Path(temporary)
            write_text(root, NARRATIVE_PATH, "# Candidate Route Baseline\n")

            errors = checker.validate_repository(root)

        self.assertEqual(errors, [f"missing artifact: {MANIFEST_PATH.as_posix()}"])

    def test_checker_uses_only_the_two_fixed_artifact_paths(self) -> None:
        checker = self.require_checker()

        self.assertEqual(checker.NARRATIVE_PATH, NARRATIVE_PATH)
        self.assertEqual(checker.MANIFEST_PATH, MANIFEST_PATH)

    def test_checker_source_is_offline_and_dependency_free(self) -> None:
        self.require_checker()
        tree = ast.parse(CHECKER.read_text(encoding="utf-8"), filename=str(CHECKER))
        imported_roots = {
            alias.name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_roots.update(
            node.module.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        )

        self.assertTrue(
            imported_roots.isdisjoint(
                {"http", "httpx", "openai", "requests", "socket", "subprocess", "urllib"}
            ),
            imported_roots,
        )

    def test_canonical_research_revision_is_a_reachable_head_ancestor(self) -> None:
        manifest = json.loads((REPO_ROOT / MANIFEST_PATH).read_text(encoding="utf-8"))
        revision = manifest["handoff"]["admission_binding"]["research_revision"]
        self.assertRegex(revision, r"^[0-9a-f]{40}$")

        exists = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "cat-file", "-e", f"{revision}^{{commit}}"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(
            exists.returncode,
            0,
            f"pinned research revision is not a reachable commit: {revision}",
        )

        ancestor = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", revision, "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(
            ancestor.returncode,
            0,
            f"pinned research revision is not an ancestor of HEAD: {revision}",
        )

    def test_missing_artifact_check_is_read_only(self) -> None:
        checker = self.require_checker()
        with tempfile.TemporaryDirectory(prefix="g56r-001-artifacts-") as temporary:
            root = Path(temporary)
            write_text(root, NARRATIVE_PATH, "# Candidate Route Baseline\n")
            before = snapshot(root)

            checker.validate_repository(root)

            self.assertEqual(snapshot(root), before)

    def test_validates_envelope_and_exact_agent_route_sets(self) -> None:
        checker = self.require_checker()
        with tempfile.TemporaryDirectory(prefix="g56r-001-artifacts-") as temporary:
            root = Path(temporary)
            manifest = basic_manifest()
            write_artifacts(root, manifest)
            self.assertEqual(checker.validate_repository(root), [])

            wrong_envelope = copy.deepcopy(manifest)
            wrong_envelope["manifest_version"] = 2
            write_artifacts(root, wrong_envelope)
            self.assertTrue(
                any("manifest_version must be 1" in error for error in checker.validate_repository(root))
            )

            missing_agent = copy.deepcopy(manifest)
            missing_agent["agents"] = missing_agent["agents"][:-1]
            write_artifacts(root, missing_agent)
            self.assertTrue(
                any("agent set" in error for error in checker.validate_repository(root))
            )

            wrong_route = copy.deepcopy(manifest)
            wrong_route["agents"][0]["production_route"]["status"] = "absent"
            write_artifacts(root, wrong_route)
            self.assertTrue(
                any("production routes" in error for error in checker.validate_repository(root))
            )

    def test_validates_fixture_inventory_and_four_independent_surfaces(self) -> None:
        checker = self.require_checker()
        with tempfile.TemporaryDirectory(prefix="g56r-001-artifacts-") as temporary:
            root = Path(temporary)
            manifest = basic_manifest()
            wrong_fixture = copy.deepcopy(manifest)
            wrong_fixture["agents"][0]["fixture_contract"]["status"] = "current"
            write_artifacts(root, wrong_fixture)
            self.assertTrue(
                any("fixture inventory" in error for error in checker.validate_repository(root))
            )

            missing_surface = copy.deepcopy(manifest)
            missing_surface["agents"][0]["surface_records"].pop()
            write_artifacts(root, missing_surface)
            self.assertTrue(
                any("feature/surface pair" in error for error in checker.validate_repository(root))
            )

    def test_validates_workday_timestamps_and_sanitization(self) -> None:
        checker = self.require_checker()
        with tempfile.TemporaryDirectory(prefix="g56r-001-artifacts-") as temporary:
            root = Path(temporary)
            manifest = basic_manifest()
            bad_time = copy.deepcopy(manifest)
            bad_time["handoff"]["stopped_at"] = "2026-07-14T18:00:00-05:00"
            write_artifacts(root, bad_time)
            self.assertTrue(
                any("timestamp order" in error for error in checker.validate_repository(root))
            )

            unsafe = copy.deepcopy(manifest)
            unsafe["agents"][0]["local_locator"] = "/" + "Users" + "/alice/.codex/private.toml"
            write_artifacts(root, unsafe)
            self.assertTrue(
                any("sanitization" in error for error in checker.validate_repository(root))
            )

    def test_sanitization_rejects_absolute_paths_identities_and_secrets(self) -> None:
        checker = self.require_checker()
        unsafe_values = (
            "/etc/passwd",
            "/opt/company/private.toml",
            "builduser@ci-host",
            "freds-macbook.local",
            "sk-proj-" + "a" * 32,
        )
        with tempfile.TemporaryDirectory(prefix="g56r-001-artifacts-") as temporary:
            root = Path(temporary)
            for unsafe_value in unsafe_values:
                manifest = basic_manifest()
                manifest["agents"][0]["source_observations"][2]["logical_locator"] = unsafe_value
                write_artifacts(root, manifest)

                self.assertTrue(
                    any("sanitization" in error for error in checker.validate_repository(root)),
                    unsafe_value,
                )

            bare_identity = basic_manifest()
            bare_identity["agents"][0]["source_observations"][2]["logical_locator"] = "alice"
            write_artifacts(root, bare_identity)
            self.assertTrue(
                any("requires a logical locator" in error for error in checker.validate_repository(root))
            )

            extra_identity = basic_manifest()
            extra_identity["agents"][0]["source_observations"][2]["display_name"] = "alice"
            write_artifacts(root, extra_identity)
            self.assertTrue(
                any("prohibited fields" in error for error in checker.validate_repository(root))
            )

            unmodeled_identity = basic_manifest()
            unmodeled_identity["agents"][0]["note"] = "alice"
            write_artifacts(root, unmodeled_identity)
            self.assertTrue(
                any("exact agent-centric schema" in error for error in checker.validate_repository(root))
            )

    def test_canonical_hash_normalizes_unicode_and_line_endings(self) -> None:
        checker = self.require_checker()
        self.assertTrue(hasattr(checker, "canonical_hash"), "checker must expose canonical_hash")
        decomposed = {"text": "Cafe\u0301\r\nline\r", "nested": ["A\u030a"]}
        normalized = {"text": "Café\nline\n", "nested": ["Å"]}

        self.assertEqual(checker.canonical_hash(decomposed), canonical_hash(normalized))
        self.assertEqual(checker.canonical_hash(decomposed), checker.canonical_hash(normalized))

    def test_instruction_hashes_are_recomputed_from_source_bodies(self) -> None:
        checker = self.require_checker()
        with tempfile.TemporaryDirectory(prefix="g56r-001-artifacts-") as temporary:
            root = Path(temporary)
            manifest = basic_manifest()
            write_artifacts(root, manifest)
            source = root / "speckit-pro" / "codex-agents" / "analyze-executor.toml"
            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    "Preserve hard boundaries.", "Preserve changed boundaries."
                ),
                encoding="utf-8",
            )

            self.assertTrue(
                any(
                    "instruction_hash does not match complete decoded source body" in error
                    for error in checker.validate_repository(root)
                )
            )

    def test_claude_frontmatter_exclusion_preserves_body_separator_whitespace(self) -> None:
        checker = self.require_checker()
        with tempfile.TemporaryDirectory(prefix="g56r-001-artifacts-") as temporary:
            root = Path(temporary)
            write_text(
                root,
                Path("speckit-pro/agents/consensus-synthesizer.md"),
                "---\nname: consensus-synthesizer\n---\n\n# Consensus Synthesizer\n",
            )

            body, error = checker.instruction_body(root, "consensus-synthesizer")

            self.assertIsNone(error)
            self.assertEqual(body, "\n# Consensus Synthesizer\n")

    def test_readable_ids_and_hash_format_are_enforced(self) -> None:
        checker = self.require_checker()
        with tempfile.TemporaryDirectory(prefix="g56r-001-artifacts-") as temporary:
            root = Path(temporary)
            manifest = basic_manifest()
            invalid_id = copy.deepcopy(manifest)
            invalid_id["agents"][0]["agent_contract"]["agent_contract_id"] = "contract-1"
            write_artifacts(root, invalid_id)
            self.assertTrue(
                any("agent_contract_id" in error for error in checker.validate_repository(root))
            )

            invalid_hash = copy.deepcopy(manifest)
            invalid_hash["agents"][0]["agent_contract"]["instruction_hash"] = "SHA256:ABC"
            write_artifacts(root, invalid_hash)
            self.assertTrue(
                any("instruction_hash" in error for error in checker.validate_repository(root))
            )

    def test_contract_hash_is_recomputed_from_the_semantic_payload(self) -> None:
        checker = self.require_checker()
        with tempfile.TemporaryDirectory(prefix="g56r-001-artifacts-") as temporary:
            root = Path(temporary)
            manifest = basic_manifest()
            manifest["agents"][0]["agent_contract"]["role_boundary"] += " changed"
            write_artifacts(root, manifest)

            self.assertTrue(
                any("canonical contract_hash" in error for error in checker.validate_repository(root))
            )

    def test_manifest_content_hash_omits_only_its_own_field(self) -> None:
        checker = self.require_checker()
        self.assertTrue(
            hasattr(checker, "manifest_content_hash"),
            "checker must expose manifest_content_hash",
        )
        manifest = basic_manifest()
        first = checker.manifest_content_hash(manifest)
        manifest["handoff"]["admission_binding"]["manifest_content_hash"] = "sha256:" + "f" * 64
        second = checker.manifest_content_hash(manifest)
        manifest["research_date"] = "2026-07-15"

        self.assertEqual(first, second)
        self.assertNotEqual(second, checker.manifest_content_hash(manifest))

    def test_route_candidate_and_admission_bindings_are_exact(self) -> None:
        checker = self.require_checker()
        with tempfile.TemporaryDirectory(prefix="g56r-001-artifacts-") as temporary:
            root = Path(temporary)
            manifest = basic_manifest()
            manifest["agents"][0]["candidates"][0]["contract_hash"] = "sha256:" + "0" * 64
            write_artifacts(root, manifest)

            errors = checker.validate_repository(root)

            self.assertTrue(any("candidate contract binding" in error for error in errors), errors)
            self.assertTrue(any("admission candidate binding" in error for error in errors), errors)

    def test_candidate_shape_and_unchanged_controls_are_required(self) -> None:
        checker = self.require_checker()
        with tempfile.TemporaryDirectory(prefix="g56r-001-artifacts-") as temporary:
            root = Path(temporary)
            manifest = basic_manifest()
            incomplete = copy.deepcopy(manifest)
            incomplete["agents"][0]["candidates"][0].pop("rationale")
            write_artifacts(root, incomplete)
            self.assertTrue(
                any("candidate required fields" in error for error in checker.validate_repository(root))
            )

            no_control = copy.deepcopy(manifest)
            candidate = no_control["agents"][0]["candidates"][0]
            candidate["treatment"] = "compact-context"
            candidate["candidate_route_id"] = candidate["candidate_route_id"].replace(
                "/unchanged/", "/compact-context/"
            )
            write_artifacts(root, no_control)
            self.assertTrue(
                any("unchanged control" in error for error in checker.validate_repository(root))
            )

    def test_eligibility_is_independent_from_installation_availability(self) -> None:
        checker = self.require_checker()
        with tempfile.TemporaryDirectory(prefix="g56r-001-artifacts-") as temporary:
            root = Path(temporary)
            manifest = basic_manifest()
            available = copy.deepcopy(manifest)
            available["agents"][0]["candidates"][0]["installation_availability"]["status"] = "available"
            write_artifacts(root, available)
            self.assertTrue(
                any("unresolved_g56r_002" in error for error in checker.validate_repository(root))
            )

            incompatible = copy.deepcopy(manifest)
            candidate = incompatible["agents"][0]["candidates"][0]
            candidate["known_incompatibilities"] = [
                {
                    "contract_field": "safety_requirements",
                    "description": "Cannot preserve the hard safety boundary.",
                    "evidence_ids": ["project-analyze-executor"],
                    "eligibility_effect": "exclude",
                }
            ]
            write_artifacts(root, incompatible)
            self.assertTrue(
                any("hard incompatibility" in error for error in checker.validate_repository(root))
            )

            ignored_hard_boundary = copy.deepcopy(manifest)
            candidate = ignored_hard_boundary["agents"][0]["candidates"][0]
            candidate["known_incompatibilities"] = [
                {
                    "contract_field": "safety_requirements",
                    "description": "Cannot preserve the hard safety boundary.",
                    "evidence_ids": ["project-analyze-executor"],
                    "eligibility_effect": "none",
                }
            ]
            write_artifacts(root, ignored_hard_boundary)
            errors = checker.validate_repository(root)
            self.assertTrue(any("must use exclude eligibility_effect" in error for error in errors), errors)
            self.assertTrue(any("must make the candidate excluded" in error for error in errors), errors)

            malformed_incompatibility = copy.deepcopy(manifest)
            candidate = malformed_incompatibility["agents"][0]["candidates"][0]
            candidate["known_incompatibilities"] = [
                {
                    "contract_field": "safety_requirement",
                    "description": "",
                    "evidence_ids": ["project-analyze-executor"],
                    "eligibility_effect": "none",
                }
            ]
            write_artifacts(root, malformed_incompatibility)
            errors = checker.validate_repository(root)
            self.assertTrue(any("contract_field must name" in error for error in errors), errors)
            self.assertTrue(any("description must be non-empty" in error for error in errors), errors)

    def test_route_policy_inventory_links_and_mismatch_ownership_are_validated(self) -> None:
        checker = self.require_checker()
        with tempfile.TemporaryDirectory(prefix="g56r-001-artifacts-") as temporary:
            root = Path(temporary)
            manifest = basic_manifest()
            orphaned = copy.deepcopy(manifest)
            orphaned["agents"][0]["route_policy_inventory"][0]["downstream_entry_ids"] = [
                "inventory/missing/consumer"
            ]
            write_artifacts(root, orphaned)
            self.assertTrue(
                any("inventory link" in error for error in checker.validate_repository(root))
            )

            unowned = copy.deepcopy(manifest)
            unowned["agents"][0]["route_policy_inventory"][1]["mismatch_status"] = "mismatch"
            write_artifacts(root, unowned)
            self.assertTrue(
                any("mismatching inventory entry" in error for error in checker.validate_repository(root))
            )

            extra_claude = copy.deepcopy(manifest)
            agent = extra_claude["agents"][0]
            codex_source = next(
                item for item in agent["route_policy_inventory"]
                if item["entry_id"].startswith("RP-SRC-CODEX-")
            )
            codex_payload = next(
                item for item in agent["route_policy_inventory"]
                if item["entry_id"].startswith("RP-PAYLOAD-CODEX-")
            )
            name = agent["agent_name"]
            claude_source = copy.deepcopy(codex_source)
            claude_payload = copy.deepcopy(codex_payload)
            claude_source["entry_id"] = f"RP-SRC-CLAUDE-{name}"
            claude_source["downstream_entry_ids"] = [f"RP-PAYLOAD-CLAUDE-{name}"]
            claude_payload["entry_id"] = f"RP-PAYLOAD-CLAUDE-{name}"
            claude_payload["canonical_input_entry_id"] = claude_source["entry_id"]
            claude_payload["upstream_entry_ids"] = [claude_source["entry_id"]]
            agent["route_policy_inventory"].extend([claude_source, claude_payload])
            write_artifacts(root, extra_claude)
            self.assertTrue(
                any("exact scoped set" in error for error in checker.validate_repository(root))
            )

    def test_provenance_freshness_surfaces_and_source_observations_are_validated(self) -> None:
        checker = self.require_checker()
        with tempfile.TemporaryDirectory(prefix="g56r-001-artifacts-") as temporary:
            root = Path(temporary)
            manifest = basic_manifest()
            stale = copy.deepcopy(manifest)
            stale["agents"][0]["provenance"][1]["observed_or_retrieved_on"] = "2026-07-13"
            write_artifacts(root, stale)
            self.assertTrue(
                any("freshness" in error for error in checker.validate_repository(root))
            )

            unofficial = copy.deepcopy(manifest)
            unofficial["agents"][0]["provenance"][1]["source_url"] = "https://example.com/models"
            write_artifacts(root, unofficial)
            self.assertTrue(
                any("official OpenAI" in error for error in checker.validate_repository(root))
            )

            wrong_locator = copy.deepcopy(manifest)
            wrong_locator["agents"][0]["provenance"][1]["exact_locator"] = (
                "Custom agents; Custom agent file schema"
            )
            write_artifacts(root, wrong_locator)
            self.assertTrue(
                any("locator does not belong" in error for error in checker.validate_repository(root))
            )

            unregistered_official = copy.deepcopy(manifest)
            unregistered_official["agents"][0]["provenance"][1]["source_url"] = (
                "https://developers.openai.com/codex/overview"
            )
            write_artifacts(root, unregistered_official)
            self.assertTrue(
                any("registered frozen official source" in error for error in checker.validate_repository(root))
            )

            missing_observation = copy.deepcopy(manifest)
            missing_observation["agents"][0]["source_observations"].pop()
            write_artifacts(root, missing_observation)
            self.assertTrue(
                any("source observation classes" in error for error in checker.validate_repository(root))
            )

            incomplete_surface = copy.deepcopy(manifest)
            incomplete_surface["agents"][0]["surface_records"][0].pop("documented_scope")
            write_artifacts(root, incomplete_surface)
            self.assertTrue(
                any("surface record" in error for error in checker.validate_repository(root))
            )

            inherited_surface = copy.deepcopy(manifest)
            inherited_surface["agents"][0]["surface_records"][0]["evidence_ids"] = [
                inherited_surface["agents"][0]["surface_records"][1]["evidence_ids"][0]
            ]
            write_artifacts(root, inherited_surface)
            self.assertTrue(
                any(
                    "surface- and feature-matched official evidence" in error
                    for error in checker.validate_repository(root)
                )
            )

    def test_resolved_authority_requires_an_explicit_applicable_winner(self) -> None:
        checker = self.require_checker()
        manifest = basic_manifest()
        agent = manifest["agents"][0]
        surface = next(
            item for item in agent["surface_records"]
            if item["surface"] == "cli" and item["feature"] == "reasoning_controls"
        )
        primary = next(
            item for item in agent["provenance"]
            if item.get("evidence_id") == surface["evidence_ids"][0]
        )
        competitor = copy.deepcopy(primary)
        competitor.update({
            "evidence_id": "surface-reasoning-subagents-cli",
            "source_url": "https://developers.openai.com/codex/subagents",
            "exact_locator": "Reasoning effort (model_reasoning_effort)",
        })
        primary["conflict_status"] = "resolved_by_authority"
        competitor["conflict_status"] = "resolved_by_authority"
        agent["provenance"].append(competitor)
        surface["conflict_status"] = "resolved_by_authority"
        surface["evidence_ids"].append(competitor["evidence_id"])

        errors = self.validation_errors(checker, manifest)

        self.assertTrue(any("must name a winning evidence source" in error for error in errors), errors)

    def test_not_stated_evidence_cannot_win_or_compete_in_authority_resolution(self) -> None:
        checker = self.require_checker()
        manifest = basic_manifest()
        agent = manifest["agents"][0]
        surface = next(
            item for item in agent["surface_records"]
            if item["surface"] == "cli" and item["feature"] == "reasoning_controls"
        )
        primary = next(
            item for item in agent["provenance"]
            if item.get("evidence_id") == surface["evidence_ids"][0]
        )
        competitor = copy.deepcopy(primary)
        competitor.update({
            "evidence_id": "surface-reasoning-subagents-cli",
            "source_url": "https://developers.openai.com/codex/subagents",
            "exact_locator": "Reasoning effort (model_reasoning_effort)",
            "applicability": "not_stated_for_named_surface",
        })
        resolution = {
            "winning_evidence_id": competitor["evidence_id"],
            "authority_basis": "narrower explicit surface and feature scope",
        }
        primary.update({"conflict_status": "resolved_by_authority", "authority_resolution": resolution})
        competitor.update({"conflict_status": "resolved_by_authority", "authority_resolution": resolution})
        agent["provenance"].append(competitor)
        surface.update({
            "conflict_status": "resolved_by_authority",
            "evidence_ids": [primary["evidence_id"], competitor["evidence_id"]],
            "authority_resolution": resolution,
        })

        errors = self.validation_errors(checker, manifest)

        self.assertTrue(any("not_stated evidence" in error for error in errors), errors)

    def test_authority_winner_must_match_conflict_surface_and_feature(self) -> None:
        checker = self.require_checker()
        for mismatch in ("feature", "surface"):
            with self.subTest(mismatch=mismatch):
                manifest = basic_manifest()
                provenance = manifest["agents"][0]["provenance"]
                subject = next(
                    item for item in provenance
                    if item.get("surface") == "cli" and item.get("feature") == "reasoning_controls"
                )
                winner = next(
                    item for item in provenance
                    if (
                        mismatch == "feature"
                        and item.get("surface") == subject["surface"]
                        and item.get("feature") != subject["feature"]
                    ) or (
                        mismatch == "surface"
                        and item.get("surface") != subject["surface"]
                        and item.get("feature") == subject["feature"]
                    )
                )
                subject.update({
                    "conflict_status": "resolved_by_authority",
                    "authority_resolution": {
                        "winning_evidence_id": winner["evidence_id"],
                        "authority_basis": "claimed narrower scope",
                    },
                })

                errors = self.validation_errors(checker, manifest)

                self.assertTrue(any("match the conflict surface and feature" in error for error in errors), errors)

    def test_surface_authority_resolution_must_match_cited_provenance(self) -> None:
        checker = self.require_checker()
        manifest = basic_manifest()
        agent = manifest["agents"][0]
        surface = next(
            item for item in agent["surface_records"]
            if item["surface"] == "cli" and item["feature"] == "reasoning_controls"
        )
        provenance = next(
            item for item in agent["provenance"]
            if item.get("evidence_id") == surface["evidence_ids"][0]
        )
        provenance.update({
            "conflict_status": "resolved_by_authority",
            "authority_resolution": {
                "winning_evidence_id": provenance["evidence_id"],
                "authority_basis": "narrower explicit feature scope",
            },
        })
        surface.update({
            "conflict_status": "resolved_by_authority",
            "authority_resolution": {
                "winning_evidence_id": provenance["evidence_id"],
                "authority_basis": "different unsupported basis",
            },
        })

        errors = self.validation_errors(checker, manifest)

        self.assertTrue(any("resolution disagrees with cited provenance" in error for error in errors), errors)

    def test_parity_semantic_mappings_are_complete_and_exact(self) -> None:
        checker = self.require_checker()
        with tempfile.TemporaryDirectory(prefix="g56r-001-artifacts-") as temporary:
            root = Path(temporary)
            manifest = basic_manifest()
            parity = next(
                record for record in manifest["agents"]
                if record["agent_name"] == "consensus-synthesizer"
            )
            parity["agent_contract"]["semantic_mappings"].pop()
            write_artifacts(root, manifest)
            self.assertTrue(
                any("semantic mappings" in error for error in checker.validate_repository(root))
            )

            mismatch = basic_manifest()
            parity = next(
                record for record in mismatch["agents"]
                if record["agent_name"] == "gate-validator"
            )
            parity["agent_contract"]["semantic_mappings"][0]["mapped_codex_contract_value"] = "drift"
            write_artifacts(root, mismatch)
            self.assertTrue(
                any("mapped Codex value" in error for error in checker.validate_repository(root))
            )

    def test_fixture_telemetry_and_unknown_contracts_are_complete(self) -> None:
        checker = self.require_checker()
        with tempfile.TemporaryDirectory(prefix="g56r-001-artifacts-") as temporary:
            root = Path(temporary)
            manifest = basic_manifest()
            incomplete_fixture = copy.deepcopy(manifest)
            incomplete_fixture["agents"][0]["fixture_contract"].pop("expected_output_shape")
            write_artifacts(root, incomplete_fixture)
            self.assertTrue(
                any("fixture contract" in error for error in checker.validate_repository(root))
            )

            no_telemetry = copy.deepcopy(manifest)
            no_telemetry["agents"][0]["telemetry_requirements"] = []
            write_artifacts(root, no_telemetry)
            self.assertTrue(
                any("telemetry requirements" in error for error in checker.validate_repository(root))
            )

            unclassified = copy.deepcopy(manifest)
            unclassified["agents"][0]["classified_unknowns"][0]["class"] = "unknown"
            write_artifacts(root, unclassified)
            self.assertTrue(
                any("classified unknown" in error for error in checker.validate_repository(root))
            )

    def test_markdown_projection_must_agree_with_the_manifest(self) -> None:
        checker = self.require_checker()
        with tempfile.TemporaryDirectory(prefix="g56r-001-artifacts-") as temporary:
            root = Path(temporary)
            manifest = basic_manifest()
            write_artifacts(root, manifest)
            narrative_path = root / NARRATIVE_PATH
            narrative = narrative_path.read_text(encoding="utf-8")
            narrative_path.write_text(
                narrative.replace("agent-contract/analyze-executor/v1", "agent-contract/analyze-executor/v9", 1),
                encoding="utf-8",
            )

            self.assertTrue(
                any("Markdown/JSON agreement" in error for error in checker.validate_repository(root))
            )

    def test_human_narrative_content_hash_rejects_prose_drift(self) -> None:
        checker = self.require_checker()
        with tempfile.TemporaryDirectory(prefix="g56r-001-artifacts-") as temporary:
            root = Path(temporary)
            manifest = basic_manifest()
            write_artifacts(root, manifest)
            narrative_path = root / NARRATIVE_PATH
            narrative = narrative_path.read_text(encoding="utf-8")
            narrative_path.write_text(
                narrative.replace(
                    "started_at:",
                    "Contradictory summary: 99 agents and no production routes.\nstarted_at:",
                ),
                encoding="utf-8",
            )

            errors = checker.validate_repository(root)

            self.assertTrue(any("narrative content hash" in error for error in errors), errors)

    def test_handoff_checks_reproduce_the_terminal_decision(self) -> None:
        checker = self.require_checker()
        with tempfile.TemporaryDirectory(prefix="g56r-001-artifacts-") as temporary:
            root = Path(temporary)
            manifest = basic_manifest()
            failed_gate = copy.deepcopy(manifest)
            failed_gate["handoff"]["completion_checks"][0]["status"] = "fail"
            write_artifacts(root, failed_gate)
            self.assertTrue(
                any("handoff decision" in error for error in checker.validate_repository(root))
            )

            blocking_conflict = copy.deepcopy(manifest)
            blocking_conflict["agents"][0]["provenance"][0]["conflict_status"] = "blocking_no_go"
            write_artifacts(root, blocking_conflict)
            self.assertTrue(
                any("handoff decision" in error for error in checker.validate_repository(root))
            )

            undisposed_conflict = copy.deepcopy(manifest)
            undisposed_conflict["agents"][0]["provenance"][0]["classification"] = "conflict"
            write_artifacts(root, undisposed_conflict)
            self.assertTrue(
                any(
                    "conflict classification requires an explicit conflict disposition" in error
                    for error in checker.validate_repository(root)
                )
            )

            malformed_no_go = copy.deepcopy(manifest)
            malformed_no_go["handoff"]["decision"] = "no_go"
            malformed_no_go["handoff"]["admission_binding"] = None
            malformed_no_go["handoff"]["unmet_conditions"] = [{"gate_id": "artifact_presence"}]
            write_artifacts(root, malformed_no_go)
            self.assertTrue(
                any("unmet condition" in error for error in checker.validate_repository(root))
            )

    def test_candidate_policy_claim_fields_are_prohibited(self) -> None:
        checker = self.require_checker()
        claims = {
            "executable": True,
            "qualified": True,
            "preferred": True,
            "fallback_rank": 1,
        }
        for field, value in claims.items():
            with self.subTest(field=field):
                manifest = basic_manifest()
                manifest["agents"][0]["candidates"][0][field] = value

                errors = self.validation_errors(checker, manifest)

                self.assertTrue(any("prohibited candidate claim" in error for error in errors), errors)

    def test_candidate_evidence_references_resolve_within_provenance(self) -> None:
        checker = self.require_checker()
        for owner in ("project_eligibility", "rationale"):
            manifest = basic_manifest()
            manifest["agents"][0]["candidates"][0][owner]["evidence_ids"] = [
                "missing-evidence"
            ]

            errors = self.validation_errors(checker, manifest)

            self.assertTrue(
                any("dangling evidence_ids" in error for error in errors),
                (owner, errors),
            )

        manifest = basic_manifest()
        manifest["agents"][0]["candidates"][0]["known_incompatibilities"] = [
            {
                "contract_field": "tools",
                "description": "An evidenced incompatibility.",
                "evidence_ids": ["missing-evidence"],
                "eligibility_effect": "none",
            }
        ]

        errors = self.validation_errors(checker, manifest)

        self.assertTrue(any("dangling evidence_ids" in error for error in errors), errors)

    def test_source_observations_bind_to_the_enclosing_route_and_contract(self) -> None:
        checker = self.require_checker()
        corruptions = {
            "agent_name": "phase-executor",
            "model_id": "gpt-invalid",
            "reasoning_effort": "low",
            "instruction_hash": "sha256:" + "1" * 64,
            "contract_hash": "sha256:" + "2" * 64,
        }
        for field, value in corruptions.items():
            with self.subTest(field=field):
                manifest = basic_manifest()
                manifest["agents"][0]["source_observations"][0][field] = value

                errors = self.validation_errors(checker, manifest)

                self.assertTrue(any("source observation binding" in error for error in errors), errors)

    def test_owned_cache_and_installed_source_mismatches_are_permitted(self) -> None:
        checker = self.require_checker()
        for evidence_class in ("cached_source", "installed_state"):
            with self.subTest(evidence_class=evidence_class):
                manifest = basic_manifest()
                observation = next(
                    item for item in manifest["agents"][0]["source_observations"]
                    if item["evidence_class"] == evidence_class
                )
                observation.update(
                    {
                        "model_id": "gpt-observed-drift",
                        "reasoning_effort": "low",
                        "instruction_hash": "sha256:" + "1" * 64,
                        "contract_hash": "sha256:" + "2" * 64,
                        "mismatch_status": "mismatch",
                        "defect_owner": "G56R-002",
                    }
                )

                self.assertEqual(self.validation_errors(checker, manifest), [])

        wrong_agent = basic_manifest()
        observation = next(
            item for item in wrong_agent["agents"][0]["source_observations"]
            if item["evidence_class"] == "installed_state"
        )
        observation.update(
            {
                "agent_name": "phase-executor",
                "mismatch_status": "mismatch",
                "defect_owner": "G56R-002",
            }
        )
        errors = self.validation_errors(checker, wrong_agent)
        self.assertTrue(any("source observation binding" in error for error in errors), errors)

    def test_nonempty_fixture_telemetry_qualification_and_invalidation_values(self) -> None:
        checker = self.require_checker()
        cases = (
            ("fixture", "fixture contract values"),
            ("telemetry", "telemetry requirement values"),
            ("qualification", "qualification requirement values"),
            ("agent_invalidation", "agent invalidation_triggers"),
            ("route_invalidation", "production route invalidation_triggers"),
            ("candidate_invalidation", "candidate invalidation_triggers"),
        )
        for case, expected in cases:
            with self.subTest(case=case):
                manifest = basic_manifest()
                agent = manifest["agents"][0]
                if case == "fixture":
                    agent["fixture_contract"]["representative_task"] = " "
                elif case == "telemetry":
                    agent["telemetry_requirements"][0]["purpose"] = ""
                elif case == "qualification":
                    agent["candidates"][0]["qualification_requirements"]["capability_checks"] = []
                elif case == "agent_invalidation":
                    agent["invalidation_triggers"] = []
                elif case == "route_invalidation":
                    agent["production_route"]["invalidation_triggers"] = [" "]
                else:
                    agent["candidates"][0]["invalidation_triggers"] = [""]

                errors = self.validation_errors(checker, manifest)

                self.assertTrue(any(expected in error for error in errors), errors)

    def test_environment_freshness_and_not_applicable_official_evidence(self) -> None:
        checker = self.require_checker()
        stale_environment = basic_manifest()
        observation = stale_environment["agents"][0]["provenance"][0]
        observation["classification"] = "environment_observation"
        observation["evidence_class"] = "installed_state"
        observation["observed_or_retrieved_on"] = "2026-07-13"
        errors = self.validation_errors(checker, stale_environment)
        self.assertTrue(any("environment-observation freshness" in error for error in errors), errors)

        unsupported_surface = basic_manifest()
        agent = unsupported_surface["agents"][0]
        agent["surface_records"][0]["applicability"] = "not_applicable"
        agent["surface_records"][0]["evidence_ids"] = [f"project-{agent['agent_name']}"]
        errors = self.validation_errors(checker, unsupported_surface)
        self.assertTrue(any("not_applicable surface" in error for error in errors), errors)

    def test_not_applicable_requires_feature_matched_official_evidence(self) -> None:
        checker = self.require_checker()
        manifest = basic_manifest()
        agent = manifest["agents"][0]
        surface = next(item for item in agent["surface_records"] if item["surface"] == "cli")
        official = next(
            item for item in agent["provenance"]
            if item["classification"] == "platform_fact"
            and item["surface"] == "cli"
            and item["feature"] != surface["feature"]
        )
        self.assertNotEqual(surface["feature"], official["feature"])
        surface["applicability"] = "not_applicable"
        surface["evidence_ids"] = [official["evidence_id"]]

        errors = self.validation_errors(checker, manifest)

        self.assertTrue(any("feature-matched official evidence" in error for error in errors), errors)

    def test_malformed_valid_json_returns_errors_instead_of_type_errors(self) -> None:
        checker = self.require_checker()
        cases = (
            "agents_null",
            "agent_name_list",
            "surface_object",
            "candidate_id_list",
            "inventory_id_object",
            "gate_id_object",
        )
        for case in cases:
            with self.subTest(case=case):
                manifest = basic_manifest()
                if case == "agents_null":
                    manifest["agents"] = None
                elif case == "agent_name_list":
                    manifest["agents"][0]["agent_name"] = []
                elif case == "surface_object":
                    manifest["agents"][0]["surface_records"][0]["surface"] = {}
                elif case == "candidate_id_list":
                    manifest["agents"][0]["candidates"][0]["candidate_route_id"] = []
                elif case == "inventory_id_object":
                    manifest["agents"][0]["route_policy_inventory"][0]["entry_id"] = {}
                else:
                    manifest["handoff"]["completion_checks"][0]["gate_id"] = {}
                try:
                    errors = self.validation_errors(checker, manifest)
                except TypeError as exc:
                    self.fail(f"checker raised TypeError for {case}: {exc}")
                self.assertTrue(errors)


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(G56R001ArtifactTests)


def main() -> int:
    return run_counted(build_suite(), label="test-g56r-001-artifacts")


if __name__ == "__main__":
    raise SystemExit(main())
