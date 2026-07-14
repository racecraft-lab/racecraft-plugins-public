#!/usr/bin/env python3
"""Offline, read-only validation for the G56R-001 research handoff."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
import tomllib
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
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
INSTRUCTION_SOURCE_PATHS = {
    name: Path(
        f"speckit-pro/agents/{name}.md"
        if name in ABSENT_AGENTS
        else f"speckit-pro/codex-agents/{name}.toml"
    )
    for name in AGENT_NAMES
}
SURFACES = {"cli", "desktop_app", "app_server", "non_interactive"}
AGENT_FIELDS = {
    "agent_name",
    "agent_contract",
    "production_route",
    "candidates",
    "route_policy_inventory",
    "source_observations",
    "surface_records",
    "fixture_contract",
    "telemetry_requirements",
    "classified_unknowns",
    "provenance",
    "invalidation_triggers",
}
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
CANDIDATE_FIELDS = {
    "candidate_route_id",
    "agent_contract_id",
    "model_id",
    "reasoning_effort",
    "treatment",
    "instruction_hash",
    "contract_hash",
    "project_eligibility",
    "installation_availability",
    "capability_requirements",
    "rationale",
    "known_incompatibilities",
    "qualification_requirements",
    "provenance",
    "invalidation_triggers",
}
PROHIBITED_CANDIDATE_CLAIMS = {"executable", "qualified", "preferred", "fallback_rank"}
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
PLATFORM_FEATURES = {
    "model_identifiers",
    "custom_agent_fields",
    "reasoning_controls",
    "capability_discovery",
    "telemetry",
    "reroute_events",
    "non_interactive_output",
}
OFFICIAL_LOCATORS = {
    "https://developers.openai.com/codex/models": {
        "Recommended models; Choose a model",
    },
    "https://developers.openai.com/codex/config-reference": {
        "model_reasoning_effort",
    },
    "https://developers.openai.com/codex/subagents": {
        "Custom agents; Custom agent file schema",
        "Reasoning effort (model_reasoning_effort)",
    },
    "https://developers.openai.com/codex/app-server": {
        "Models / List models (model/list)",
        "Models / List models (model/list); supportedReasoningEfforts",
        "Models / List models (model/list); Model provider capabilities; Experimental features",
        "Events / Turn events; model/rerouted",
    },
    "https://developers.openai.com/codex/config-advanced": {
        "Observability and telemetry",
    },
    "https://developers.openai.com/codex/cyber-safety": {
        "How it works; False positives",
    },
    "https://developers.openai.com/codex/noninteractive": {
        "Make output machine-readable; --json; --output-schema",
    },
}
SURFACE_RECORD_KEYS = {
    (feature, surface)
    for feature in PLATFORM_FEATURES
    for surface in SURFACES
}
INTEGRATION_CLASSES = {
    "source",
    "installer",
    "skill",
    "validation",
    "evaluation",
    "generated_payload",
    "cache",
    "installed_state",
}
PROVENANCE_FIELDS = {
    "evidence_id",
    "evidence_class",
    "classification",
    "exact_locator",
    "observed_or_retrieved_on",
    "surface",
    "feature",
    "documented_scope",
    "applicability",
    "conflict_status",
    "invalidation_triggers",
}
PROJECTION_START = "<!-- g56r-001-agreement-projection:start -->"
PROJECTION_END = "<!-- g56r-001-agreement-projection:end -->"
NARRATIVE_HASH_MARKER = re.compile(
    r"<!-- g56r-001-human-narrative-sha256:(sha256:[0-9a-f]{64}) -->"
)
HASH_VALUE = re.compile(r"^sha256:[0-9a-f]{64}$")
LOGICAL_LOCATOR = re.compile(
    r"^[a-z][a-z0-9_-]*(?:/[A-Za-z0-9][A-Za-z0-9._-]*)+$"
)

RFC3339 = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
LOCAL_PATH = re.compile(
    r"(?:^|[\s\"'=])(?:"
    r"/(?:Users|home|root|private|var|tmp|opt|etc|usr|bin|sbin|Library)(?:/|(?=$))"
    r"|/(?!/)[A-Za-z0-9._~-]+/[A-Za-z0-9._~+/-]+"
    r"|[A-Za-z]:[\\/]"
    r"|\\\\[^\\/\s]+[\\/]"
    r")",
    re.IGNORECASE,
)
SECRET_VALUE = re.compile(
    r"(?:\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"
    r"|\bsk(?:-[A-Za-z0-9]+)*-[A-Za-z0-9_-]{8,}"
    r"|\b(?:sk|ghp|github_pat)_[A-Za-z0-9_-]{8,}"
    r"|\bAKIA[0-9A-Z]{16}\b"
    r"|\bxox[baprs]-[A-Za-z0-9-]{8,}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----)",
    re.IGNORECASE,
)
LOCAL_IDENTITY = re.compile(
    r"(?:\b(?:username|user|hostname|host)\s*[:=]\s*[A-Za-z0-9._-]+"
    r"|\b[A-Za-z0-9._-]+@[A-Za-z0-9._-]+\b"
    r"|\b[A-Za-z0-9-]+\.local\b)",
    re.IGNORECASE,
)
SENSITIVE_KEYS = {
    "absolute_path",
    "access_token",
    "api_key",
    "credential",
    "credentials",
    "home_path",
    "hostname",
    "password",
    "private_key",
    "secret",
    "secrets",
    "username",
}


def normalize(value: object) -> object:
    """Recursively normalize strings to NFC and LF without changing other whitespace."""

    if isinstance(value, str):
        return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {normalize(key): normalize(item) for key, item in value.items()}
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


def instruction_body(repo_root: Path, agent_name: str) -> tuple[str | None, str | None]:
    """Return the decoded instruction body while preserving body whitespace."""

    source_path = INSTRUCTION_SOURCE_PATHS[agent_name]
    try:
        source = (repo_root / source_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return None, f"unable to read {source_path.as_posix()} as UTF-8: {exc}"

    if agent_name in ABSENT_AGENTS:
        normalized = normalize(source)
        assert isinstance(normalized, str)
        frontmatter = re.match(r"\A---\n.*?^---\n", normalized, flags=re.DOTALL | re.MULTILINE)
        if frontmatter is None:
            return None, f"{source_path.as_posix()} has invalid frontmatter boundaries"
        return normalized[frontmatter.end():], None

    try:
        parsed = tomllib.loads(source)
    except tomllib.TOMLDecodeError as exc:
        return None, f"unable to parse {source_path.as_posix()} as TOML: {exc}"
    body = parsed.get("developer_instructions")
    if not isinstance(body, str):
        return None, f"{source_path.as_posix()} has no decoded developer_instructions string"
    return body, None


def manifest_content_hash(manifest: dict[str, Any]) -> str:
    payload = copy.deepcopy(manifest)
    handoff = payload.get("handoff")
    if isinstance(handoff, dict):
        binding = handoff.get("admission_binding")
        if isinstance(binding, dict):
            binding.pop("manifest_content_hash", None)
    return canonical_hash(payload)


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


def _slug(value: str) -> str:
    return "-".join(filter(None, re.split(r"[^a-z0-9]+", value.lower())))


def _is_nonempty(value: object) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return False


def _missing_fields(value: object, required: set[str]) -> list[str]:
    return sorted(required - set(value)) if isinstance(value, dict) else sorted(required)


def _nonempty_string_list(value: object) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and bool(item.strip()) for item in value)
    )


def _official_openai_url(value: object) -> bool:
    return isinstance(value, str) and bool(
        re.match(r"^https://(?:[a-z0-9-]+\.)*openai\.com/", value, re.IGNORECASE)
    )


def _date_in_workday(value: object, started: datetime, deadline: datetime) -> bool:
    if not isinstance(value, str):
        return False
    try:
        observed = date.fromisoformat(value)
    except ValueError:
        return False
    return started.date() <= observed <= deadline.date()


def _invalid_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number {value}")


def _load_manifest(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return None, [f"unable to read {MANIFEST_PATH.as_posix()}: {exc}"]
    if raw.startswith(b"\xef\xbb\xbf"):
        return None, [f"invalid manifest encoding: {MANIFEST_PATH.as_posix()} has a UTF-8 BOM"]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return None, [f"invalid manifest encoding: {MANIFEST_PATH.as_posix()} is not UTF-8: {exc}"]
    try:
        value = json.loads(text, parse_constant=_invalid_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        return None, [f"invalid manifest JSON: {exc}"]
    if not isinstance(value, dict):
        return None, ["manifest root must be an object"]
    return value, []


def _parse_timestamp(value: object, field: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not RFC3339.fullmatch(value):
        errors.append(f"handoff.{field} must be an RFC 3339 timestamp with an explicit UTC offset")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"handoff.{field} is not a valid timestamp")
        return None
    if parsed.utcoffset() is None:
        errors.append(f"handoff.{field} must include a UTC offset")
        return None
    return parsed


def _iter_values(value: object, location: str = "manifest"):
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{location}.{key}"
            yield child, key, item
            yield from _iter_values(item, child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _iter_values(item, f"{location}[{index}]")


def _validate_sanitization(manifest: dict[str, Any], narrative: str, errors: list[str]) -> None:
    violations: list[str] = []
    for location, key, value in _iter_values(manifest):
        if key.lower() in SENSITIVE_KEYS:
            violations.append(f"{location} uses prohibited field {key!r}")
        if isinstance(value, str) and (
            LOCAL_PATH.search(value)
            or LOCAL_IDENTITY.search(value)
            or SECRET_VALUE.search(value)
        ):
            violations.append(f"{location} contains machine-local or secret material")
    if (
        LOCAL_PATH.search(narrative)
        or LOCAL_IDENTITY.search(narrative)
        or SECRET_VALUE.search(narrative)
    ):
        violations.append("narrative contains machine-local or secret material")
    for violation in sorted(set(violations)):
        errors.append(f"sanitization violation: {violation}")


def _validate_envelope(manifest: dict[str, Any], errors: list[str]) -> None:
    if manifest.get("manifest_type") != "agent_route_candidate_manifest":
        errors.append("manifest_type must be 'agent_route_candidate_manifest'")
    if manifest.get("manifest_version") != 1:
        errors.append("manifest_version must be 1")
    research_date = manifest.get("research_date")
    if not isinstance(research_date, str):
        errors.append("research_date must be an ISO date")
    else:
        try:
            parsed_date = date.fromisoformat(research_date)
        except ValueError:
            errors.append("research_date must be an ISO date")
        else:
            if parsed_date.isoformat() != research_date:
                errors.append("research_date must use YYYY-MM-DD")
    prohibited_tables = {"contracts", "routes", "candidates", "evidence"} & set(manifest)
    if prohibited_tables:
        errors.append(
            "manifest must be agent-centric; prohibited top-level tables: "
            + ", ".join(sorted(prohibited_tables))
        )


def _validate_agents(manifest: dict[str, Any], errors: list[str]) -> None:
    agents = manifest.get("agents")
    if not isinstance(agents, list):
        errors.append("agents must be an array")
        return
    records = [record for record in agents if isinstance(record, dict)]
    if len(records) != len(agents):
        errors.append("every agent record must be an object")
    names = [record.get("agent_name") for record in records]
    if len(names) != len(set(names)):
        errors.append("agent names must be unique")
    if set(names) != AGENT_NAMES or len(names) != len(AGENT_NAMES):
        missing = sorted(AGENT_NAMES - set(names))
        extra = sorted(set(names) - AGENT_NAMES, key=str)
        errors.append(f"agent set must contain exactly 12 named agents; missing={missing}, extra={extra}")

    present: set[object] = set()
    absent: set[object] = set()
    current_fixtures: set[object] = set()
    missing_fixtures: set[object] = set()
    for record in records:
        name = record.get("agent_name")
        if set(record) != AGENT_FIELDS:
            errors.append(
                f"agent {name!r} fields must match the exact agent-centric schema; "
                f"missing={sorted(AGENT_FIELDS - set(record))}, "
                f"extra={sorted(set(record) - AGENT_FIELDS)}"
            )
        route = record.get("production_route")
        status = route.get("status") if isinstance(route, dict) else None
        if status == "present":
            present.add(name)
        elif status == "absent":
            absent.add(name)
        else:
            errors.append(f"agent {name!r} production_route.status must be present or absent")

        fixture = record.get("fixture_contract")
        fixture_status = fixture.get("status") if isinstance(fixture, dict) else None
        fixture_path = fixture.get("fixture_path") if isinstance(fixture, dict) else None
        if fixture_status == "current":
            current_fixtures.add(name)
            if not isinstance(fixture_path, str) or fixture_path.startswith(("/", "\\")):
                errors.append(f"agent {name!r} current fixture must use a repository-relative path")
        elif fixture_status == "missing":
            missing_fixtures.add(name)
            if fixture_path is not None:
                errors.append(f"agent {name!r} missing fixture must use a null fixture_path")
        else:
            errors.append(f"agent {name!r} fixture_contract.status must be current or missing")

        surface_records = record.get("surface_records")
        if not isinstance(surface_records, list):
            errors.append(f"agent {name!r} surface_records must be an array")
            continue
        surface_keys = [
            (item.get("feature"), item.get("surface"))
            for item in surface_records
            if isinstance(item, dict)
        ]
        if len(surface_keys) != len(set(surface_keys)) or set(surface_keys) != SURFACE_RECORD_KEYS:
            errors.append(
                f"agent {name!r} surface records must contain every required feature/surface pair exactly once"
            )

    if present != AGENT_NAMES - ABSENT_AGENTS or absent != ABSENT_AGENTS:
        errors.append(
            "production routes must be exactly 10 present and 2 absent only for "
            "consensus-synthesizer and gate-validator"
        )
    if current_fixtures != CURRENT_FIXTURES or missing_fixtures != AGENT_NAMES - CURRENT_FIXTURES:
        errors.append("fixture inventory must be exactly 3 current and 9 missing for the declared agents")


def _validate_hash(value: object, location: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not HASH_VALUE.fullmatch(value):
        errors.append(f"{location} must be lowercase sha256:<64hex>")


def _validate_candidate(
    name: object,
    contract: dict[str, Any],
    candidate: object,
    index: int,
    errors: list[str],
) -> dict[str, Any] | None:
    location = f"agent {name!r} candidate[{index}]"
    if not isinstance(candidate, dict):
        errors.append(f"{location} must be an object")
        return None
    missing = sorted(CANDIDATE_FIELDS - set(candidate))
    if missing:
        errors.append(f"{location} candidate required fields missing: {missing}")
    prohibited = sorted(PROHIBITED_CANDIDATE_CLAIMS & set(candidate))
    if prohibited:
        errors.append(f"{location} has prohibited candidate claim fields: {prohibited}")

    candidate_id = candidate.get("candidate_route_id")
    model_id = candidate.get("model_id")
    effort = candidate.get("reasoning_effort")
    treatment = candidate.get("treatment")
    if all(isinstance(value, str) and value for value in (name, model_id, effort, treatment)):
        expected_prefix = (
            f"candidate-route/{name}/{_slug(model_id)}/{_slug(effort)}/{_slug(treatment)}/v"
        )
        readable = (
            isinstance(candidate_id, str)
            and candidate_id.startswith(expected_prefix)
            and re.fullmatch(re.escape(expected_prefix) + r"[1-9][0-9]*", candidate_id)
        )
        if not readable:
            errors.append(f"{location} candidate_route_id is not the readable canonical ID")
    else:
        errors.append(f"{location} model_id, reasoning_effort, and treatment must be non-empty strings")

    if candidate.get("agent_contract_id") != contract.get("agent_contract_id"):
        errors.append(f"{location} candidate contract binding has the wrong agent_contract_id")
    if candidate.get("contract_hash") != contract.get("contract_hash"):
        errors.append(f"{location} candidate contract binding has the wrong contract_hash")
    if candidate.get("instruction_hash") != contract.get("instruction_hash"):
        errors.append(f"{location} candidate instruction binding has the wrong instruction_hash")
    _validate_hash(candidate.get("instruction_hash"), f"{location}.instruction_hash", errors)
    _validate_hash(candidate.get("contract_hash"), f"{location}.contract_hash", errors)

    eligibility = candidate.get("project_eligibility")
    eligibility_status = eligibility.get("status") if isinstance(eligibility, dict) else None
    if (
        not isinstance(eligibility, dict)
        or eligibility_status not in {"eligible", "excluded"}
        or not _is_nonempty(eligibility.get("basis"))
        or not _nonempty_string_list(eligibility.get("evidence_ids"))
    ):
        errors.append(f"{location} project_eligibility must record status, basis, and evidence_ids")

    availability = candidate.get("installation_availability")
    if not isinstance(availability, dict) or availability.get("status") != "unresolved_g56r_002":
        errors.append(f"{location} installation_availability.status must remain unresolved_g56r_002")

    capabilities = candidate.get("capability_requirements")
    if not isinstance(capabilities, dict) or set(capabilities) != CAPABILITY_FIELDS:
        errors.append(f"{location} capability_requirements must contain the exact ten fields")
    elif any(not _is_nonempty(capabilities[field]) for field in CAPABILITY_FIELDS):
        errors.append(f"{location} capability_requirements values must be explicit and non-empty")

    rationale = candidate.get("rationale")
    if (
        not isinstance(rationale, dict)
        or not _is_nonempty(rationale.get("classification"))
        or not _is_nonempty(rationale.get("summary"))
        or not _nonempty_string_list(rationale.get("evidence_ids"))
    ):
        errors.append(f"{location} rationale must record classification, summary, and evidence_ids")

    incompatibilities = candidate.get("known_incompatibilities")
    exclusion_effect = False
    if not isinstance(incompatibilities, list):
        errors.append(f"{location} known_incompatibilities must be an explicit array")
    else:
        for incompatibility_index, incompatibility in enumerate(incompatibilities):
            if not isinstance(incompatibility, dict):
                errors.append(f"{location} incompatibility[{incompatibility_index}] must be an object")
                continue
            required = {"contract_field", "description", "evidence_ids", "eligibility_effect"}
            if not required <= set(incompatibility):
                errors.append(f"{location} incompatibility[{incompatibility_index}] is incomplete")
            elif not _nonempty_string_list(incompatibility.get("evidence_ids")):
                errors.append(
                    f"{location} incompatibility[{incompatibility_index}] evidence_ids must be non-empty"
                )
            if incompatibility.get("eligibility_effect") not in {"none", "exclude"}:
                errors.append(f"{location} incompatibility[{incompatibility_index}] has invalid eligibility_effect")
            if incompatibility.get("eligibility_effect") == "exclude":
                exclusion_effect = True
    if exclusion_effect and eligibility_status != "excluded":
        errors.append(f"{location} hard incompatibility with exclude effect must make the candidate excluded")
    if eligibility_status == "excluded" and not exclusion_effect:
        errors.append(f"{location} excluded candidate requires a cited exclusion incompatibility")

    qualification = candidate.get("qualification_requirements")
    qualification_fields = {
        "status",
        "capability_checks",
        "fixture",
        "required_artifacts",
        "telemetry",
        "owner_spec",
    }
    if not isinstance(qualification, dict) or not qualification_fields <= set(qualification):
        errors.append(f"{location} qualification_requirements are incomplete")
    elif qualification.get("status") not in {"unqualified", "not_applicable_excluded"}:
        errors.append(f"{location} qualification status is invalid")
    elif eligibility_status == "eligible" and qualification.get("status") != "unqualified":
        errors.append(f"{location} eligible candidate must remain unqualified")
    elif eligibility_status == "excluded" and qualification.get("status") != "not_applicable_excluded":
        errors.append(f"{location} excluded candidate qualification must be not_applicable_excluded")
    if isinstance(qualification, dict) and (
        not _nonempty_string_list(qualification.get("capability_checks"))
        or not _is_nonempty(qualification.get("fixture"))
        or not _nonempty_string_list(qualification.get("required_artifacts"))
        or not _nonempty_string_list(qualification.get("telemetry"))
        or qualification.get("owner_spec") not in {"G56R-002", "G56R-003"}
    ):
        errors.append(f"{location} qualification requirement values must be non-empty and valid")

    provenance = candidate.get("provenance")
    if not isinstance(provenance, list) or not provenance:
        errors.append(f"{location} provenance must be non-empty")
    else:
        provenance_ids = {
            record.get("evidence_id")
            for record in provenance
            if isinstance(record, dict) and isinstance(record.get("evidence_id"), str)
        }
        evidence_references = [
            ("project_eligibility", eligibility.get("evidence_ids") if isinstance(eligibility, dict) else None),
            ("rationale", rationale.get("evidence_ids") if isinstance(rationale, dict) else None),
        ]
        if isinstance(incompatibilities, list):
            evidence_references.extend(
                (
                    f"known_incompatibilities[{incompatibility_index}]",
                    incompatibility.get("evidence_ids"),
                )
                for incompatibility_index, incompatibility in enumerate(incompatibilities)
                if isinstance(incompatibility, dict)
            )
        for reference_location, evidence_ids in evidence_references:
            if not isinstance(evidence_ids, list):
                continue
            dangling = sorted(set(evidence_ids) - provenance_ids, key=str)
            if dangling:
                errors.append(
                    f"{location}.{reference_location} has dangling evidence_ids: {dangling}"
                )
    if not _nonempty_string_list(candidate.get("invalidation_triggers")):
        errors.append(f"{location} candidate invalidation_triggers must contain concrete values")
    return candidate


def _validate_identities_and_candidates(manifest: dict[str, Any], errors: list[str]) -> None:
    agents = manifest.get("agents")
    if not isinstance(agents, list):
        return
    contract_ids: list[object] = []
    candidate_ids: list[object] = []
    records = [record for record in agents if isinstance(record, dict)]
    for record in records:
        name = record.get("agent_name")
        contract = record.get("agent_contract")
        if not isinstance(contract, dict):
            errors.append(f"agent {name!r} agent_contract must be an object")
            continue
        contract_id = contract.get("agent_contract_id")
        contract_ids.append(contract_id)
        if not isinstance(name, str) or not isinstance(contract_id, str) or not re.fullmatch(
            rf"agent-contract/{re.escape(name)}/v[1-9][0-9]*", contract_id
        ):
            errors.append(f"agent {name!r} agent_contract_id is not the readable canonical ID")
        _validate_hash(contract.get("instruction_hash"), f"agent {name!r} instruction_hash", errors)
        _validate_hash(contract.get("contract_hash"), f"agent {name!r} contract_hash", errors)
        missing_semantics = [field for field in SEMANTIC_FIELDS if not _is_nonempty(contract.get(field))]
        if missing_semantics:
            errors.append(f"agent {name!r} semantic contract fields are incomplete: {missing_semantics}")
        else:
            payload = {"agent_name": name, **{field: contract[field] for field in SEMANTIC_FIELDS}}
            if contract.get("contract_hash") != canonical_hash(payload):
                errors.append(f"agent {name!r} canonical contract_hash does not match its semantic payload")

        candidates = record.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            errors.append(f"agent {name!r} candidates must be a non-empty array")
            valid_candidates: list[dict[str, Any]] = []
        else:
            valid_candidates = []
            for index, candidate in enumerate(candidates):
                validated = _validate_candidate(name, contract, candidate, index, errors)
                if validated is not None:
                    valid_candidates.append(validated)
                    candidate_ids.append(validated.get("candidate_route_id"))

        tuples = {
            (candidate.get("model_id"), candidate.get("reasoning_effort"), candidate.get("treatment"))
            for candidate in valid_candidates
        }
        for model_id, effort, treatment in tuples:
            if treatment != "unchanged" and (model_id, effort, "unchanged") not in tuples:
                errors.append(
                    f"agent {name!r} treatment {treatment!r} requires a matching unchanged control"
                )

        route = record.get("production_route")
        if not isinstance(route, dict):
            continue
        status = route.get("status")
        route_bindings = (
            "candidate_route_id",
            "model_id",
            "reasoning_effort",
            "instruction_hash",
            "contract_hash",
        )
        if status == "present":
            if route.get("instruction_hash") != contract.get("instruction_hash"):
                errors.append(f"agent {name!r} production route instruction binding drift")
            if route.get("contract_hash") != contract.get("contract_hash"):
                errors.append(f"agent {name!r} production route contract binding drift")
            matching = [
                candidate
                for candidate in valid_candidates
                if candidate.get("candidate_route_id") == route.get("candidate_route_id")
            ]
            if len(matching) != 1:
                errors.append(f"agent {name!r} production route must bind one declared candidate")
            else:
                candidate = matching[0]
                compared = (
                    "model_id",
                    "reasoning_effort",
                    "instruction_hash",
                    "contract_hash",
                )
                if any(route.get(field) != candidate.get(field) for field in compared):
                    errors.append(f"agent {name!r} production route candidate tuple binding drift")
            if route.get("absence_reason") is not None:
                errors.append(f"agent {name!r} present route must use null absence_reason")
        elif status == "absent":
            if any(route.get(field) is not None for field in route_bindings):
                errors.append(f"agent {name!r} absent route bindings must all be null")
            if not _is_nonempty(route.get("absence_reason")):
                errors.append(f"agent {name!r} absent route requires a cited absence_reason")

    if len(contract_ids) != len(set(contract_ids)):
        errors.append("agent_contract_id values must be globally unique")
    if len(candidate_ids) != len(set(candidate_ids)):
        errors.append("candidate_route_id values must be globally unique")


def _validate_instruction_sources(
    manifest: dict[str, Any], repo_root: Path, errors: list[str]
) -> None:
    agents = manifest.get("agents")
    if not isinstance(agents, list):
        return
    for record in agents:
        if not isinstance(record, dict):
            continue
        name = record.get("agent_name")
        contract = record.get("agent_contract")
        if not isinstance(name, str) or name not in INSTRUCTION_SOURCE_PATHS:
            continue
        if not isinstance(contract, dict):
            continue
        body, source_error = instruction_body(repo_root, name)
        if source_error is not None:
            errors.append(source_error)
            continue
        assert body is not None
        expected = instruction_hash(body)
        if contract.get("instruction_hash") != expected:
            errors.append(
                f"agent {name!r} instruction_hash does not match complete decoded source body"
            )

def _validate_admission_binding(manifest: dict[str, Any], errors: list[str]) -> None:
    handoff = manifest.get("handoff")
    if not isinstance(handoff, dict) or handoff.get("decision") != "go":
        return
    binding = handoff.get("admission_binding")
    if not isinstance(binding, dict):
        errors.append("go handoff requires admission_binding")
        return
    if binding.get("manifest_type") != manifest.get("manifest_type"):
        errors.append("admission manifest_type binding drift")
    if binding.get("manifest_version") != manifest.get("manifest_version"):
        errors.append("admission manifest_version binding drift")
    if not _is_nonempty(binding.get("research_revision")):
        errors.append("admission research_revision must be non-empty")

    agents = manifest.get("agents")
    records = [record for record in agents if isinstance(record, dict)] if isinstance(agents, list) else []
    production_routes = []
    contracts = []
    candidates = []
    for record in sorted(records, key=lambda item: str(item.get("agent_name"))):
        name = record.get("agent_name")
        route = record.get("production_route") if isinstance(record.get("production_route"), dict) else {}
        contract = record.get("agent_contract") if isinstance(record.get("agent_contract"), dict) else {}
        production_routes.append(
            {
                "agent_name": name,
                **{
                    field: route.get(field)
                    for field in (
                        "status",
                        "candidate_route_id",
                        "model_id",
                        "reasoning_effort",
                        "instruction_hash",
                        "contract_hash",
                    )
                },
            }
        )
        contracts.append(
            {
                "agent_name": name,
                **{
                    field: contract.get(field)
                    for field in ("agent_contract_id", "instruction_hash", "contract_hash")
                },
            }
        )
        record_candidates = record.get("candidates")
        if isinstance(record_candidates, list):
            for candidate in sorted(
                (item for item in record_candidates if isinstance(item, dict)),
                key=lambda item: str(item.get("candidate_route_id")),
            ):
                candidates.append(
                    {
                        "agent_name": name,
                        **{
                            field: candidate.get(field)
                            for field in (
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
                )
    if normalize(binding.get("production_routes")) != normalize(production_routes):
        errors.append("admission production route binding does not match the manifest")
    if normalize(binding.get("contracts")) != normalize(contracts):
        errors.append("admission contract binding does not match the manifest")
    if normalize(binding.get("candidates")) != normalize(candidates):
        errors.append("admission candidate binding does not match the manifest")
    snapshot = binding.get("capability_snapshot_requirement")
    if not isinstance(snapshot, dict) or snapshot.get("owner_spec") != "G56R-002":
        errors.append("admission capability_snapshot_requirement must be owned by G56R-002")

    recorded_hash = binding.get("manifest_content_hash")
    _validate_hash(recorded_hash, "handoff.admission_binding.manifest_content_hash", errors)
    if recorded_hash != manifest_content_hash(manifest):
        errors.append("handoff.admission_binding.manifest_content_hash does not match canonical content")


def _validate_inventory(manifest: dict[str, Any], errors: list[str]) -> None:
    required = {
        "entry_id", "locator", "integration_class", "role", "affected_agents",
        "policy_fields", "authority_class", "evidence_class", "relationship",
        "canonical_input_entry_id", "upstream_entry_ids", "downstream_entry_ids",
        "revision_or_version", "observed_on", "mismatch_status", "defect_owner",
    }
    entries: list[dict[str, Any]] = []
    for agent in manifest.get("agents", []):
        if not isinstance(agent, dict):
            continue
        inventory = agent.get("route_policy_inventory")
        if not isinstance(inventory, list) or not inventory:
            errors.append(f"agent {agent.get('agent_name')!r} route-policy inventory must be non-empty")
            continue
        for entry in inventory:
            if not isinstance(entry, dict):
                errors.append(f"agent {agent.get('agent_name')!r} inventory entry must be an object")
                continue
            missing = _missing_fields(entry, required)
            if missing:
                errors.append(f"inventory entry {entry.get('entry_id')!r} missing fields: {missing}")
            if agent.get("agent_name") not in entry.get("affected_agents", []):
                errors.append(f"inventory entry {entry.get('entry_id')!r} omits its enclosing agent")
            if entry.get("mismatch_status") != "matches" and not _is_nonempty(entry.get("defect_owner")):
                errors.append(f"mismatching inventory entry {entry.get('entry_id')!r} requires a defect owner")
            if entry.get("relationship") == "derived_output" and not _is_nonempty(
                entry.get("canonical_input_entry_id")
            ):
                errors.append(f"derived inventory entry {entry.get('entry_id')!r} must name its canonical input")
            entries.append(entry)
    ids = [entry.get("entry_id") for entry in entries]
    if len(ids) != len(set(ids)):
        errors.append("route-policy inventory entry IDs must be unique")
    by_id = {entry.get("entry_id"): entry for entry in entries}
    claude_agents = ABSENT_AGENTS
    physical_entries = {
        *(f"RP-SRC-CODEX-{name}" for name in AGENT_NAMES - ABSENT_AGENTS),
        *(f"RP-PAYLOAD-CODEX-{name}" for name in AGENT_NAMES - ABSENT_AGENTS),
        *(f"RP-SRC-CLAUDE-{name}" for name in claude_agents),
        *(f"RP-PAYLOAD-CLAUDE-{name}" for name in claude_agents),
    }
    actual_physical = {
        entry_id
        for entry_id in by_id
        if isinstance(entry_id, str)
        and re.fullmatch(r"RP-(?:SRC|PAYLOAD)-(?:CODEX|CLAUDE)-[a-z0-9-]+", entry_id)
    }
    missing_physical = sorted(physical_entries - actual_physical)
    unexpected_physical = sorted(actual_physical - physical_entries)
    if missing_physical or unexpected_physical:
        errors.append(
            "route-policy physical source/payload inventory must match the exact scoped set; "
            f"missing={missing_physical}, unexpected={unexpected_physical}"
        )
    for entry_id in sorted(physical_entries & set(by_id)):
        expected_class = "source" if entry_id.startswith("RP-SRC-") else "generated_payload"
        if by_id[entry_id].get("integration_class") != expected_class:
            errors.append(f"inventory entry {entry_id!r} must use integration_class {expected_class!r}")
    parity_payload_consumers = {"RP-PAYLOAD-PROOF", "RP-CACHE-PROOF", "RP-VAL-DERIVED"}
    if parity_payload_consumers <= set(by_id):
        for name in sorted(ABSENT_AGENTS):
            entry_id = f"RP-PAYLOAD-CLAUDE-{name}"
            entry = by_id.get(entry_id)
            if isinstance(entry, dict) and set(entry.get("downstream_entry_ids", [])) != parity_payload_consumers:
                errors.append(
                    f"inventory entry {entry_id!r} must link to the exact parity payload proof consumers"
                )
    for entry in entries:
        entry_id = entry.get("entry_id")
        for downstream in entry.get("downstream_entry_ids", []):
            if downstream not in by_id or entry_id not in by_id[downstream].get("upstream_entry_ids", []):
                errors.append(f"inventory link {entry_id!r} -> {downstream!r} is missing or not reciprocal")
        for upstream in entry.get("upstream_entry_ids", []):
            if upstream not in by_id or entry_id not in by_id[upstream].get("downstream_entry_ids", []):
                errors.append(f"inventory link {upstream!r} -> {entry_id!r} is missing or not reciprocal")
        canonical = entry.get("canonical_input_entry_id")
        if canonical is not None and canonical not in by_id:
            errors.append(f"inventory link for {entry_id!r} names missing canonical input {canonical!r}")
    classes = {entry.get("integration_class") for entry in entries}
    if classes != INTEGRATION_CLASSES:
        errors.append(f"route-policy inventory integration classes must be exact; found={sorted(classes, key=str)}")


def _validate_provenance(
    records: object,
    *,
    location: str,
    revision: str | None,
    started: datetime | None,
    deadline: datetime | None,
    errors: list[str],
    platform_features: set[object],
) -> None:
    if not isinstance(records, list) or not records:
        errors.append(f"{location} provenance must be a non-empty array")
        return
    classifications = {
        "platform_fact", "project_fact", "reasonable_inference", "proposed_policy",
        "unverified_assumption", "environment_observation", "conflict",
    }
    conflicts = {"none", "resolved_by_authority", "blocking_no_go", "nonblocking_deferred"}
    records_by_id = {
        record.get("evidence_id"): record
        for record in records
        if isinstance(record, dict) and isinstance(record.get("evidence_id"), str)
    }
    for index, record in enumerate(records):
        item = f"{location} provenance[{index}]"
        missing = _missing_fields(record, PROVENANCE_FIELDS)
        if missing:
            errors.append(f"{item} missing fields: {missing}")
            continue
        assert isinstance(record, dict)
        if record.get("classification") not in classifications:
            errors.append(f"{item} has invalid classification")
        if record.get("conflict_status") not in conflicts:
            errors.append(f"{item} has invalid conflict disposition")
        if record.get("conflict_status") == "resolved_by_authority":
            resolution = record.get("authority_resolution")
            if _missing_fields(resolution, {"winning_evidence_id", "authority_basis"}):
                errors.append(f"{item} resolved authority conflict must name a winning evidence source and basis")
            else:
                assert isinstance(resolution, dict)
                winner = records_by_id.get(resolution.get("winning_evidence_id"))
                if winner is None:
                    errors.append(f"{item} resolved authority winner does not resolve within provenance")
                elif str(winner.get("applicability", "")).startswith("not_stated"):
                    errors.append(f"{item} resolved authority winner cannot be not_stated evidence")
                elif (
                    winner.get("surface") != record.get("surface")
                    or winner.get("feature") != record.get("feature")
                ):
                    errors.append(f"{item} resolved authority winner must match the conflict surface and feature")
            if str(record.get("applicability", "")).startswith("not_stated"):
                errors.append(f"{item} not_stated evidence cannot be an authority-conflict competitor")
        if not _is_nonempty(record.get("invalidation_triggers")):
            errors.append(f"{item} requires invalidation triggers")
        classification = record.get("classification")
        if classification == "platform_fact":
            source_url = record.get("source_url")
            if not _official_openai_url(source_url):
                errors.append(f"{item} platform fact must cite an official OpenAI URL")
            elif source_url not in OFFICIAL_LOCATORS:
                errors.append(f"{item} platform fact must use a registered frozen official source URL")
            elif record.get("exact_locator") not in OFFICIAL_LOCATORS[source_url]:
                errors.append(f"{item} exact locator does not belong to its recorded official source URL")
            if started is None or deadline is None or not _date_in_workday(
                record.get("observed_or_retrieved_on"), started, deadline
            ):
                errors.append(f"{item} violates official-evidence freshness")
            platform_features.add(record.get("feature"))
        if classification == "environment_observation" and (
            started is None
            or deadline is None
            or not _date_in_workday(record.get("observed_or_retrieved_on"), started, deadline)
        ):
            errors.append(f"{item} violates environment-observation freshness")
        if classification == "project_fact":
            project_fields = {"repository_path", "repository_revision", "evidence_role"}
            if _missing_fields(record, project_fields):
                errors.append(f"{item} project fact lacks repository provenance")
            elif revision is not None and record.get("repository_revision") != revision:
                errors.append(f"{item} project revision differs from the pinned research revision")
            path = record.get("repository_path")
            if not isinstance(path, str) or path.startswith(("/", "\\")) or ".." in Path(path).parts:
                errors.append(f"{item} repository_path must be repository-relative")
        if record.get("conflict_status") == "nonblocking_deferred":
            deferred = {"owner_spec", "impact", "required_follow_up"}
            if _missing_fields(record, deferred):
                errors.append(f"{item} deferred conflict lacks owner, impact, or follow-up")


def _validate_record_details(manifest: dict[str, Any], errors: list[str]) -> None:
    handoff = manifest.get("handoff") if isinstance(manifest.get("handoff"), dict) else {}
    binding = handoff.get("admission_binding") if isinstance(handoff, dict) else None
    revision = binding.get("research_revision") if isinstance(binding, dict) else None
    try:
        started = datetime.fromisoformat(str(handoff.get("started_at")).replace("Z", "+00:00"))
        deadline = datetime.fromisoformat(str(handoff.get("deadline_at")).replace("Z", "+00:00"))
    except ValueError:
        started = deadline = None
    platform_features: set[object] = set()
    for agent in manifest.get("agents", []):
        if not isinstance(agent, dict):
            continue
        name = agent.get("agent_name")
        contract = agent.get("agent_contract") if isinstance(agent.get("agent_contract"), dict) else {}
        route = agent.get("production_route") if isinstance(agent.get("production_route"), dict) else {}
        official_evidence = {
            item.get("evidence_id"): item
            for item in agent.get("provenance", [])
            if isinstance(item, dict)
            and item.get("classification") == "platform_fact"
            and _official_openai_url(item.get("source_url"))
        }
        mappings = contract.get("semantic_mappings")
        if name in ABSENT_AGENTS:
            mapped_fields = [item.get("contract_field") for item in mappings if isinstance(item, dict)] if isinstance(mappings, list) else []
            if len(mapped_fields) != 12 or set(mapped_fields) != set(SEMANTIC_FIELDS):
                errors.append(f"agent {name!r} semantic mappings must cover the exact twelve contract fields")
            else:
                for mapping in mappings:
                    required = {
                        "contract_field", "claude_repository_path", "claude_repository_revision",
                        "claude_exact_locator", "mapping_status", "justification",
                        "mapped_codex_contract_value",
                    }
                    if _missing_fields(mapping, required):
                        errors.append(f"agent {name!r} semantic mapping is incomplete")
                        continue
                    field = mapping["contract_field"]
                    if mapping.get("mapping_status") not in {"preserved", "codex_adapted", "not_applicable"}:
                        errors.append(f"agent {name!r} semantic mapping status is invalid")
                    if mapping.get("mapping_status") != "preserved" and not _is_nonempty(mapping.get("justification")):
                        errors.append(f"agent {name!r} adapted semantic mapping requires justification")
                    if normalize(mapping.get("mapped_codex_contract_value")) != normalize(contract.get(field)):
                        errors.append(f"agent {name!r} semantic mapping mapped Codex value disagrees with {field}")
        elif mappings is not None:
            errors.append(f"agent {name!r} must not declare parity semantic mappings")

        observations = agent.get("source_observations")
        classes = [item.get("evidence_class") for item in observations if isinstance(item, dict)] if isinstance(observations, list) else []
        if len(classes) != 3 or set(classes) != {"tracked_source", "cached_source", "installed_state"}:
            errors.append(f"agent {name!r} source observation classes must be exactly tracked, cached, and installed")
        else:
            common = {
                "evidence_class", "agent_name", "model_id", "reasoning_effort",
                "instruction_hash", "contract_hash", "observed_on", "surface", "version",
                "mismatch_status", "defect_owner",
            }
            for observation in observations:
                if _missing_fields(observation, common):
                    errors.append(f"agent {name!r} source observation is incomplete")
                    continue
                evidence_class = observation["evidence_class"]
                allowed_fields = common | (
                    {"repository_path", "repository_revision", "evidence_role"}
                    if evidence_class == "tracked_source"
                    else {"logical_locator"}
                )
                extra_fields = sorted(set(observation) - allowed_fields)
                if extra_fields:
                    errors.append(
                        f"agent {name!r} source observation contains prohibited fields: {extra_fields}"
                    )
                expected_route_binding = {
                    "model_id": route.get("model_id"),
                    "reasoning_effort": route.get("reasoning_effort"),
                    "instruction_hash": contract.get("instruction_hash"),
                    "contract_hash": contract.get("contract_hash"),
                }
                if observation.get("agent_name") != name or (
                    (evidence_class == "tracked_source" or observation.get("mismatch_status") == "matches")
                    and any(
                        observation.get(field) != value
                        for field, value in expected_route_binding.items()
                    )
                ):
                    errors.append(f"agent {name!r} source observation binding disagrees with its route or contract")
                if evidence_class == "tracked_source":
                    if _missing_fields(observation, {"repository_path", "repository_revision", "evidence_role"}):
                        errors.append(f"agent {name!r} tracked source observation lacks repository provenance")
                    elif revision is not None and observation.get("repository_revision") != revision:
                        errors.append(f"agent {name!r} tracked source observation has revision drift")
                else:
                    logical_locator = observation.get("logical_locator")
                    if not isinstance(logical_locator, str) or not LOGICAL_LOCATOR.fullmatch(
                        logical_locator
                    ):
                        errors.append(f"agent {name!r} environment observation requires a logical locator")
                    if started is None or deadline is None or not _date_in_workday(observation.get("observed_on"), started, deadline):
                        errors.append(f"agent {name!r} environment source observation violates freshness")
                if observation.get("mismatch_status") != "matches" and not _is_nonempty(observation.get("defect_owner")):
                    errors.append(f"agent {name!r} mismatching source observation requires a defect owner")

        for surface in agent.get("surface_records", []):
            required = {"surface", "feature", "applicability", "evidence_ids", "documented_scope", "conflict_status"}
            if _missing_fields(surface, required):
                errors.append(f"agent {name!r} surface record is incomplete")
            elif surface.get("applicability") not in {"documented", "undocumented", "not_applicable"}:
                errors.append(f"agent {name!r} surface record applicability is invalid")
            elif surface.get("conflict_status") not in {
                "none", "resolved_by_authority", "blocking_no_go", "nonblocking_deferred",
            }:
                errors.append(f"agent {name!r} surface record conflict disposition is invalid")
            elif not _nonempty_string_list(surface.get("evidence_ids")) or not all(
                evidence_id in official_evidence
                and official_evidence[evidence_id].get("surface") == surface.get("surface")
                and official_evidence[evidence_id].get("feature") == surface.get("feature")
                for evidence_id in surface.get("evidence_ids", [])
            ):
                surface_kind = (
                    "not_applicable surface"
                    if surface.get("applicability") == "not_applicable"
                    else "surface record"
                )
                errors.append(
                    f"agent {name!r} {surface_kind} requires surface- and feature-matched official evidence"
                )
            elif any(
                official_evidence[evidence_id].get("conflict_status")
                != surface.get("conflict_status")
                for evidence_id in surface.get("evidence_ids", [])
            ):
                errors.append(f"agent {name!r} surface conflict disposition disagrees with cited provenance")
            elif surface.get("conflict_status") == "resolved_by_authority":
                resolution = surface.get("authority_resolution")
                if _missing_fields(resolution, {"winning_evidence_id", "authority_basis"}):
                    errors.append(
                        f"agent {name!r} resolved surface authority conflict must name a winning evidence source and basis"
                    )
                else:
                    assert isinstance(resolution, dict)
                    winner_id = resolution.get("winning_evidence_id")
                    winner = official_evidence.get(winner_id)
                    if winner_id not in surface.get("evidence_ids", []):
                        errors.append(f"agent {name!r} surface authority winner must be cited by the surface record")
                    elif winner is None or str(winner.get("applicability", "")).startswith("not_stated"):
                        errors.append(f"agent {name!r} surface authority winner cannot be not_stated evidence")
                    if any(
                        official_evidence[evidence_id].get("authority_resolution") != resolution
                        for evidence_id in surface.get("evidence_ids", [])
                    ):
                        errors.append(f"agent {name!r} surface authority resolution disagrees with cited provenance")
                if any(
                    str(official_evidence[evidence_id].get("applicability", "")).startswith("not_stated")
                    for evidence_id in surface.get("evidence_ids", [])
                ):
                    errors.append(f"agent {name!r} not_stated evidence cannot be a surface authority competitor")

        fixture = agent.get("fixture_contract")
        fixture_fields = {
            "status", "fixture_path", "representative_task", "input_type", "expected_behavior",
            "expected_output_shape", "hard_contract_assertions", "evidence_class",
        }
        if _missing_fields(fixture, fixture_fields) or not isinstance(fixture, dict):
            errors.append(f"agent {name!r} fixture contract is incomplete")
        elif set(fixture.get("hard_contract_assertions", [])) != set(SEMANTIC_FIELDS):
            errors.append(f"agent {name!r} fixture contract must assert all hard contract fields")
        elif fixture.get("status") == "missing" and fixture.get("evidence_class") != "non_release_evidence":
            errors.append(f"agent {name!r} missing fixture evidence must be non_release_evidence")
        elif (
            any(
                not _is_nonempty(fixture.get(field))
                for field in ("representative_task", "input_type", "expected_behavior", "expected_output_shape")
            )
            or fixture.get("evidence_class") not in {"current_release_evidence", "non_release_evidence"}
        ):
            errors.append(f"agent {name!r} fixture contract values must be non-empty and valid")

        telemetry = agent.get("telemetry_requirements")
        telemetry_fields = {"field_or_proof", "purpose", "required_for", "owner_spec", "current_status"}
        if not isinstance(telemetry, list) or not telemetry:
            errors.append(f"agent {name!r} telemetry requirements must be non-empty")
        elif any(_missing_fields(item, telemetry_fields) for item in telemetry):
            errors.append(f"agent {name!r} telemetry requirements are incomplete")
        elif any(item.get("current_status") != "deferred" for item in telemetry):
            errors.append(f"agent {name!r} telemetry requirements must remain deferred")
        elif any(
            not _is_nonempty(item.get("field_or_proof"))
            or not _is_nonempty(item.get("purpose"))
            or item.get("required_for") not in {"capability_preflight", "scored_qualification"}
            or item.get("owner_spec") not in {"G56R-002", "G56R-003"}
            for item in telemetry
        ):
            errors.append(f"agent {name!r} telemetry requirement values must be non-empty and valid")

        if not _nonempty_string_list(agent.get("invalidation_triggers")):
            errors.append(f"agent {name!r} agent invalidation_triggers must contain concrete values")
        if not _nonempty_string_list(route.get("invalidation_triggers")):
            errors.append(f"agent {name!r} production route invalidation_triggers must contain concrete values")

        unknowns = agent.get("classified_unknowns")
        unknown_fields = {"unknown_id", "class", "question", "impact", "owner_spec", "required_follow_up", "status"}
        if not isinstance(unknowns, list):
            errors.append(f"agent {name!r} classified unknowns must be an explicit array")
        else:
            for unknown in unknowns:
                if _missing_fields(unknown, unknown_fields) or unknown.get("class") not in {
                    "documentation", "inventory", "executable_capability", "scored_qualification"
                }:
                    errors.append(f"agent {name!r} classified unknown is incomplete or unclassified")
                elif unknown.get("class") in {"documentation", "inventory"} and unknown.get("status") != "closed":
                    errors.append(f"agent {name!r} G56R-001 unknown must be closed")
                elif unknown.get("class") == "executable_capability" and unknown.get("owner_spec") != "G56R-002":
                    errors.append(f"agent {name!r} executable-capability unknown must be owned by G56R-002")
                elif unknown.get("class") == "scored_qualification" and unknown.get("owner_spec") != "G56R-003":
                    errors.append(f"agent {name!r} scored-qualification unknown must be owned by G56R-003")

        _validate_provenance(
            agent.get("provenance"), location=f"agent {name!r}", revision=revision,
            started=started, deadline=deadline, errors=errors, platform_features=platform_features,
        )
        _validate_provenance(
            route.get("provenance"), location=f"agent {name!r} production route", revision=revision,
            started=started, deadline=deadline, errors=errors, platform_features=platform_features,
        )
        for index, candidate in enumerate(agent.get("candidates", [])):
            if isinstance(candidate, dict):
                _validate_provenance(
                    candidate.get("provenance"), location=f"agent {name!r} candidate[{index}]",
                    revision=revision, started=started, deadline=deadline, errors=errors,
                    platform_features=platform_features,
                )
    if platform_features != PLATFORM_FEATURES:
        errors.append(f"platform provenance must cover the exact required feature set; found={sorted(platform_features, key=str)}")


def _validate_agreement(narrative: str, manifest: dict[str, Any], errors: list[str]) -> None:
    narrative_hash_matches = NARRATIVE_HASH_MARKER.findall(narrative)
    if len(narrative_hash_matches) != 1:
        errors.append("human-readable narrative content hash marker is missing or duplicated")
    elif narrative_hash_matches[0] != human_narrative_hash(narrative):
        errors.append("human-readable narrative content hash does not match the prose")
    start = narrative.find(PROJECTION_START)
    end = narrative.find(PROJECTION_END, start + len(PROJECTION_START)) if start >= 0 else -1
    if start < 0 or end < 0:
        errors.append("Markdown/JSON agreement projection markers are missing")
        return
    block = narrative[start + len(PROJECTION_START):end].strip()
    if not block.startswith("```json\n") or not block.endswith("\n```"):
        errors.append("Markdown/JSON agreement projection must be a fenced JSON object")
        return
    try:
        projection = json.loads(block.removeprefix("```json\n").removesuffix("\n```"), parse_constant=_invalid_constant)
    except (json.JSONDecodeError, ValueError) as exc:
        errors.append(f"Markdown/JSON agreement projection is invalid JSON: {exc}")
        return
    if normalize(projection) != normalize(manifest):
        errors.append("Markdown/JSON agreement projection does not match the manifest")


def _validate_handoff(manifest: dict[str, Any], errors: list[str]) -> None:
    handoff = manifest.get("handoff")
    required = {
        "decision", "started_at", "deadline_at", "stopped_at", "completed_artifacts",
        "completion_checks", "unmet_conditions", "admission_binding",
    }
    if _missing_fields(handoff, required) or not isinstance(handoff, dict):
        errors.append("handoff is incomplete")
        return
    decision = handoff.get("decision")
    checks = handoff.get("completion_checks")
    check_fields = {"gate_id", "requirement_refs", "condition", "status", "evidence_ids"}
    if not isinstance(checks, list) or any(_missing_fields(item, check_fields) for item in checks):
        errors.append("handoff completion checks are incomplete")
        statuses: list[object] = []
        gate_ids: list[object] = []
    else:
        statuses = [item.get("status") for item in checks]
        gate_ids = [item.get("gate_id") for item in checks]
        if len(gate_ids) != len(set(gate_ids)) or set(gate_ids) != GATE_IDS:
            errors.append("handoff completion checks must cover each objective gate exactly once")
    completed = set(handoff.get("completed_artifacts", [])) if isinstance(handoff.get("completed_artifacts"), list) else set()
    expected_artifacts = {
        NARRATIVE_PATH.as_posix(), MANIFEST_PATH.as_posix(),
        "specs/g56r-001-candidate-route-baseline/check-artifacts.py",
    }
    if completed != expected_artifacts:
        errors.append("handoff completed_artifacts must name the exact three research delivery files")
    unmet = handoff.get("unmet_conditions")
    blocking_conflict = any(
        isinstance(value, dict) and value.get("conflict_status") == "blocking_no_go"
        for _location, _key, value in _iter_values(manifest)
    )
    if decision == "go":
        if any(status != "pass" for status in statuses) or unmet != [] or blocking_conflict:
            errors.append("handoff decision go is not reproduced by completion checks and conflicts")
        if not isinstance(handoff.get("admission_binding"), dict):
            errors.append("handoff decision go requires an admission binding")
    elif decision == "no_go":
        if handoff.get("admission_binding") is not None:
            errors.append("handoff decision no_go requires a null admission binding")
        unmet_fields = {
            "gate_id", "requirement_refs", "condition", "available_evidence_ids",
            "impact", "owner_spec", "required_follow_up",
        }
        if not isinstance(unmet, list) or not unmet:
            errors.append("handoff decision no_go requires unmet conditions")
        elif any(_missing_fields(item, unmet_fields) for item in unmet):
            errors.append("handoff unmet condition is incomplete")
        if statuses and all(status == "pass" for status in statuses) and not blocking_conflict:
            errors.append("handoff decision no_go is not reproduced by completion checks or conflicts")
    else:
        errors.append("handoff decision must be go or no_go")


def _validate_timestamps(manifest: dict[str, Any], errors: list[str]) -> None:
    handoff = manifest.get("handoff")
    if not isinstance(handoff, dict):
        errors.append("handoff must be an object")
        return
    started = _parse_timestamp(handoff.get("started_at"), "started_at", errors)
    stopped = _parse_timestamp(handoff.get("stopped_at"), "stopped_at", errors)
    deadline = _parse_timestamp(handoff.get("deadline_at"), "deadline_at", errors)
    if started is None or stopped is None or deadline is None:
        return
    if not started <= stopped <= deadline:
        errors.append("handoff timestamp order must satisfy started_at <= stopped_at <= deadline_at")
    if deadline - started > timedelta(days=1):
        errors.append("handoff workday must not extend beyond one day")
    if manifest.get("research_date") != started.date().isoformat():
        errors.append("research_date must match the started_at calendar date")


def validate_repository(repo_root: Path = REPO_ROOT) -> list[str]:
    """Return deterministic validation failures without mutating the repository."""

    root = Path(repo_root)
    missing = [
        path for path in (NARRATIVE_PATH, MANIFEST_PATH)
        if not (root / path).is_file()
    ]
    if missing:
        return [f"missing artifact: {path.as_posix()}" for path in missing]

    try:
        narrative = (root / NARRATIVE_PATH).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [f"unable to read {NARRATIVE_PATH.as_posix()} as UTF-8: {exc}"]
    manifest, errors = _load_manifest(root / MANIFEST_PATH)
    if manifest is None:
        return errors

    try:
        _validate_envelope(manifest, errors)
        _validate_agents(manifest, errors)
        _validate_identities_and_candidates(manifest, errors)
        _validate_instruction_sources(manifest, root, errors)
        _validate_admission_binding(manifest, errors)
        _validate_inventory(manifest, errors)
        _validate_record_details(manifest, errors)
        _validate_timestamps(manifest, errors)
        _validate_sanitization(manifest, narrative, errors)
        _validate_agreement(narrative, manifest, errors)
        _validate_handoff(manifest, errors)
    except (AttributeError, KeyError, TypeError, ValueError):
        errors.append("manifest contains invalid field types")
    return errors


def main() -> int:
    errors = validate_repository()
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        print(f"G56R-001 artifacts: FAIL ({len(errors)} error(s))", file=sys.stderr)
        return 1
    print("G56R-001 artifacts: PASS (12 agents; 10 present; 2 absent; 3 current fixtures; 9 missing)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
