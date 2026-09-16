"""Pure contracts for deterministic, evidence-bound native-evaluation pairs."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
from typing import Any, Mapping, Sequence


PAIR_SCHEMA_VERSION = "native-eval-pair/v1"
PAIR_PLAN_SCHEMA_VERSION = "native-eval-pair-plan/v1"
PAIR_INPUT_SCHEMA_VERSION = "native-eval-pair-input/v1"
PAIR_GRADER_SCHEMA_VERSION = "native-eval-pair-grader/v1"
EXPECTED_SCHEMA_VERSION = "speckit.layer7.expected-equivalence.v1"
TOLERANCE_SCHEMA_VERSION = "speckit.layer7.tolerance.v1"
HOSTS = ("claude", "codex")
TOLERANCES = frozenset({"byte-identical", "exact", "semantic-equivalent", "tolerance-1"})
_STABLE_ID = re.compile(r"[a-z0-9][a-z0-9._-]*")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_SEMANTIC_HOST_LABEL = re.compile(r"\b(?:claude|codex|agent teams?|path [ab])\b", re.IGNORECASE)


class PairingError(ValueError):
    """Raised when a pair contract or its captured evidence is malformed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PairingError(message)


def _text(value: object, label: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{label} must be nonempty text")
    return value


def _identifier(value: object, label: str) -> str:
    result = _text(value, label)
    _require(_STABLE_ID.fullmatch(result) is not None, f"{label} must be a stable identifier")
    return result


def _relative(value: object, label: str) -> PurePosixPath:
    text = _text(value, label)
    _require("\\" not in text, f"{label} must use repository-style separators")
    path = PurePosixPath(text)
    _require(not path.is_absolute() and text == path.as_posix(), f"{label} must be a canonical relative path")
    _require(bool(path.parts) and all(part not in {"", ".", ".."} for part in path.parts),
             f"{label} must be a canonical relative path")
    return path


def _json_value(value: object) -> bool:
    if value is None or type(value) in {bool, int, str}:
        return True
    if type(value) is float:
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_json_value(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _json_value(item) for key, item in value.items())
    return False


def _canonical(value: object, label: str) -> bytes:
    _require(_json_value(value), f"{label} must be a strict JSON value")
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    _require(len(pairs) == len({key for key, _value in pairs}), "pair contract contains a duplicate JSON key")
    return dict(pairs)


def _contract_path(repo_root: Path, value: object, label: str) -> tuple[str, Path]:
    relative = _relative(value, label)
    _require(relative.parts[:2] == ("tests", "speckit-pro"), f"{label} must be under tests/speckit-pro")
    tests_root = (repo_root / "tests" / "speckit-pro").resolve(strict=True)
    try:
        resolved = repo_root.joinpath(*relative.parts).resolve(strict=True)
    except OSError as exc:
        raise PairingError(f"{label} is missing: {relative}") from exc
    _require(resolved.is_relative_to(tests_root), f"{label} escaped tests/speckit-pro")
    _require(resolved.is_file(), f"{label} must be a file")
    return relative.as_posix(), resolved


def _load_contract(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=lambda token: (_ for _ in ()).throw(PairingError(f"invalid constant {token}")),
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PairingError(f"could not load {label}: {exc}") from exc
    _require(isinstance(value, dict), f"{label} must contain an object")
    return value


def _unique_text_list(value: object, label: str) -> list[str]:
    _require(isinstance(value, list), f"{label} must be a list")
    result = [_text(item, f"{label} item") for item in value]
    _require(len(result) == len(set(result)), f"{label} contains duplicates")
    return result


def _expected_shape(expected: dict[str, Any], label: str) -> None:
    base = {"schema", "fixture_id", "description", "compare", "fail_fast", "report_format"}
    invariant = {"required_invariants", "required_invariants_source"}
    _require(set(expected) in {frozenset(base), frozenset(base | invariant)}, f"{label} has an ambiguous schema")
    _require(expected["schema"] == EXPECTED_SCHEMA_VERSION, f"{label} has an unsupported schema")
    _text(expected["fixture_id"], f"{label} fixture_id")
    _text(expected["description"], f"{label} description")
    _require(type(expected["fail_fast"]) is bool, f"{label} fail_fast must be boolean")
    _require(expected["report_format"] == "field-level-diff", f"{label} report_format is unsupported")


def _tolerance_shape(tolerance: dict[str, Any], label: str) -> None:
    _require(set(tolerance) == {"schema", "fixture_id", "description", "fields"},
             f"{label} has an ambiguous schema")
    _require(tolerance["schema"] == TOLERANCE_SCHEMA_VERSION, f"{label} has an unsupported schema")
    _text(tolerance["fixture_id"], f"{label} fixture_id")
    _text(tolerance["description"], f"{label} description")


def _compile_comparison(
    entry: object, index: int, tolerance_fields: dict[str, Any], check_id: str,
) -> dict[str, Any]:
    label = f"pair check {check_id} compare[{index}]"
    _require(isinstance(entry, dict), f"{label} must be an object")
    base = {"field", "source", "tolerance_key"}
    extracted = {"section_selector", "extractor"}
    _require(set(entry) in {frozenset(base), frozenset(base | extracted)}, f"{label} has an ambiguous schema")
    field = _identifier(entry["field"], f"{label} field")
    source = _relative(entry["source"], f"{label} source").as_posix()
    tolerance_key = _text(entry["tolerance_key"], f"{label} tolerance_key")
    _require(tolerance_key in tolerance_fields, f"{label} references an unknown tolerance")
    tolerance_entry = tolerance_fields[tolerance_key]
    _require(isinstance(tolerance_entry, dict) and set(tolerance_entry) == {"tolerance", "rationale"},
             f"pair check {check_id} tolerance {tolerance_key} has an ambiguous schema")
    tolerance_type = tolerance_entry["tolerance"]
    _require(tolerance_type in TOLERANCES,
             f"pair check {check_id} tolerance {tolerance_key} is unsupported")
    rationale = _text(tolerance_entry["rationale"], f"pair check {check_id} tolerance {tolerance_key} rationale")
    section = entry.get("section_selector")
    extractor = entry.get("extractor")
    if extractor is not None:
        _require(isinstance(section, str) and section.startswith("## ") and bool(section[3:].strip()),
                 f"{label} section_selector must name an H2 section")
        valid_extractor = extractor == "table_row_count" or (
            isinstance(extractor, str) and extractor.startswith("table_column:") and bool(extractor[13:].strip())
        )
        _require(valid_extractor, f"{label} extractor is unsupported")
    if tolerance_type == "byte-identical":
        _require(extractor is None, f"{label} byte-identical must compare a complete artifact")
    if tolerance_type == "semantic-equivalent":
        _require(extractor is not None, f"{label} semantic-equivalent requires an extractor")
        _require(_SEMANTIC_HOST_LABEL.search(rationale) is None,
                 f"{label} semantic rubric must not reveal provider or legacy path labels")
    if tolerance_type == "tolerance-1":
        _require(extractor == "table_row_count", f"{label} tolerance-1 requires table_row_count")
    result = {
        "id": f"{check_id}.{field}",
        "field": field,
        "source": source,
        "tolerance": tolerance_type,
        "rubric": rationale,
    }
    if extractor is not None:
        result.update({"section_selector": section, "extractor": extractor})
    return result


def _compile_invariants(
    expected: dict[str, Any], invariant_keys: list[str], check_id: str,
) -> tuple[dict[str, Any], dict[str, str] | None]:
    if not invariant_keys:
        return {}, None
    invariants = expected.get("required_invariants")
    source = expected.get("required_invariants_source")
    _require(isinstance(invariants, dict) and bool(invariants),
             f"pair check {check_id} selected invariants but its plan defines none")
    _require(all(key in invariants for key in invariant_keys),
             f"pair check {check_id} selected an unknown invariant")
    _require(isinstance(source, dict) and set(source) == {
        "source", "section_selector", "key_column", "value_column",
    }, f"pair check {check_id} invariant source has an ambiguous schema")
    artifact = _relative(source["source"], f"pair check {check_id} invariant source").as_posix()
    section = _text(source["section_selector"], f"pair check {check_id} invariant section")
    _require(section.startswith("## ") and bool(section[3:].strip()),
             f"pair check {check_id} invariant section must name an H2 section")
    key_column = _text(source["key_column"], f"pair check {check_id} invariant key_column")
    value_column = _text(source["value_column"], f"pair check {check_id} invariant value_column")
    selected = {key: invariants[key] for key in invariant_keys}
    for key, value in selected.items():
        valid = type(value) is bool or isinstance(value, str) and bool(value)
        valid = valid or isinstance(value, list) and bool(value) and all(
            isinstance(item, str) and bool(item) for item in value
        )
        _require(valid, f"pair check {check_id} selected invariant {key} has an unsupported value")
    return selected, {
        "source": artifact,
        "section_selector": section,
        "key_column": key_column,
        "value_column": value_column,
    }


def _compile_check(check: object, repo_root: Path, requirement_ids: set[str]) -> dict[str, Any]:
    _require(isinstance(check, dict), "pairing contains a malformed check")
    fields = {"id", "requirement", "type", "expected_path", "tolerance_path", "invariant_keys"}
    _require(set(check) == fields, "pairing check has an ambiguous schema")
    check_id = _identifier(check["id"], "pairing check id")
    requirement = _identifier(check["requirement"], f"pair check {check_id} requirement")
    _require(requirement in requirement_ids, f"pair check {check_id} references an unknown requirement")
    _require(check["type"] == "comparison_plan", f"pair check {check_id} has an unsupported type")
    invariant_keys = _unique_text_list(check["invariant_keys"], f"pair check {check_id} invariant_keys")
    expected_name, expected_path = _contract_path(repo_root, check["expected_path"],
                                                  f"pair check {check_id} expected_path")
    tolerance_name, tolerance_path = _contract_path(repo_root, check["tolerance_path"],
                                                     f"pair check {check_id} tolerance_path")
    _require(expected_path.parent == tolerance_path.parent,
             f"pair check {check_id} contracts must share one fixture directory")
    expected = _load_contract(expected_path, f"pair check {check_id} expected contract")
    tolerance = _load_contract(tolerance_path, f"pair check {check_id} tolerance contract")
    _expected_shape(expected, f"pair check {check_id} expected contract")
    _tolerance_shape(tolerance, f"pair check {check_id} tolerance contract")
    fixture_id = expected["fixture_id"]
    _require(fixture_id == tolerance["fixture_id"] == expected_path.parent.name,
             f"pair check {check_id} fixture identities do not match")
    tolerance_fields = tolerance["fields"]
    _require(isinstance(tolerance_fields, dict) and bool(tolerance_fields),
             f"pair check {check_id} tolerances must be a nonempty object")
    compare = expected["compare"]
    _require(isinstance(compare, list) and bool(compare), f"pair check {check_id} comparisons must be nonempty")
    criteria = [_compile_comparison(entry, index, tolerance_fields, check_id)
                for index, entry in enumerate(compare)]
    criterion_ids = [criterion["id"] for criterion in criteria]
    _require(len(criterion_ids) == len(set(criterion_ids)), f"pair check {check_id} has duplicate comparison fields")
    used_tolerances = {entry["tolerance_key"] for entry in compare}
    _require(used_tolerances == set(tolerance_fields),
             f"pair check {check_id} tolerances and comparisons do not have exact coverage")
    invariants, invariant_source = _compile_invariants(expected, invariant_keys, check_id)
    artifacts = {criterion["source"] for criterion in criteria}
    if invariant_source is not None:
        _require(invariant_source["source"] in artifacts,
                 f"pair check {check_id} invariant source must also be compared")
        artifacts.add(invariant_source["source"])
    return {
        "id": check_id,
        "requirement": requirement,
        "type": "comparison_plan",
        "contracts": {"expected_path": expected_name, "tolerance_path": tolerance_name},
        "criteria": criteria,
        "invariants": invariants,
        "invariant_source": invariant_source,
        "declared_artifact_paths": sorted(artifacts),
    }


def compile_pair_plan(case: Mapping[str, Any], repo_root: str | Path) -> dict[str, Any]:
    """Validate and compile one parity case's explicit pair contract."""
    _require(isinstance(case, Mapping), "pair case must be an object")
    case_id = _identifier(case.get("id"), "pair case id")
    _require(case.get("layer") == "parity", f"case {case_id} is not a parity case")
    pairing = case.get("pairing")
    _require(isinstance(pairing, dict) and set(pairing) == {"schema", "arms", "checks"},
             f"case {case_id} pairing has an ambiguous schema")
    _require(pairing["schema"] == PAIR_SCHEMA_VERSION, f"case {case_id} pairing schema is unsupported")
    arms = pairing["arms"]
    _require(isinstance(arms, dict) and tuple(arms) == HOSTS,
             f"case {case_id} pairing arms must be ordered claude then codex")
    hosts = case.get("hosts")
    _require(isinstance(hosts, dict), f"case {case_id} has no host settings")
    for host in HOSTS:
        mode = _text(arms[host], f"case {case_id} pairing {host} mode")
        settings = hosts.get(host)
        _require(isinstance(settings, dict) and mode in settings.get("modes", []),
                 f"case {case_id} pairing {host} mode is not declared")
    requirements = case.get("requirements")
    _require(isinstance(requirements, list), f"case {case_id} requirements are malformed")
    requirement_ids = {entry.get("id") for entry in requirements if isinstance(entry, dict)}
    checks = pairing["checks"]
    _require(isinstance(checks, list) and bool(checks), f"case {case_id} pairing checks must be nonempty")
    try:
        root = Path(repo_root).resolve(strict=True)
    except OSError as exc:
        raise PairingError(f"repository root is unavailable: {repo_root}") from exc
    compiled = [_compile_check(check, root, requirement_ids) for check in checks]
    check_ids = [check["id"] for check in compiled]
    _require(len(check_ids) == len(set(check_ids)), f"case {case_id} has duplicate pairing check ids")
    host_check_ids = {check.get("id") for check in case.get("checks", []) if isinstance(check, dict)}
    _require(host_check_ids.isdisjoint(check_ids), f"case {case_id} reuses a per-host check id for pairing")
    artifacts = sorted({path for check in compiled for path in check["declared_artifact_paths"]})
    return {
        "schema_version": PAIR_PLAN_SCHEMA_VERSION,
        "case_id": case_id,
        "arms": dict(arms),
        "checks": compiled,
        "declared_artifact_paths": artifacts,
    }


def _sha(value: object, label: str) -> str:
    result = _text(value, label)
    _require(_SHA256.fullmatch(result) is not None, f"{label} must be a lowercase SHA-256")
    return result


def _arm_identity(arm: object, label: str) -> dict[str, object]:
    _require(isinstance(arm, dict), f"{label} must be an object")
    required = {
        "case_id", "host", "mode", "trial", "input_fingerprint", "capture_sha256",
        "grade_identity", "grade_sha256",
    }
    _require(required <= set(arm), f"{label} is missing evidence identities")
    trial = arm["trial"]
    _require(type(trial) is int and trial >= 1, f"{label} trial must be a positive integer")
    return {
        "case_id": _identifier(arm["case_id"], f"{label} case_id"),
        "host": _text(arm["host"], f"{label} host"),
        "mode": _text(arm["mode"], f"{label} mode"),
        "trial": trial,
        "input_fingerprint": _sha(arm["input_fingerprint"], f"{label} input_fingerprint"),
        "capture_sha256": _sha(arm["capture_sha256"], f"{label} capture_sha256"),
        "grade_identity": _sha(arm["grade_identity"], f"{label} grade_identity"),
        "grade_sha256": _sha(arm["grade_sha256"], f"{label} grade_sha256"),
    }


def _validated_arm_identities(case_id: str, plan: Mapping[str, Any], arms: object) -> list[dict[str, object]]:
    _require(isinstance(arms, (list, tuple)) and len(arms) == 2, "pair requires exactly two arms")
    identities = [_arm_identity(arm, f"pair arm {index}") for index, arm in enumerate(arms)]
    _require(tuple(identity["host"] for identity in identities) == HOSTS,
             "pair arms must be ordered claude then codex; duplicate or swapped arms are invalid")
    _require(all(identity["case_id"] == case_id for identity in identities), "pair arms have the wrong case_id")
    _require(identities[0]["trial"] == identities[1]["trial"], "pair arms have different trials")
    declared = plan.get("arms")
    _require(isinstance(declared, dict), "compiled pair plan has malformed arms")
    _require(all(identity["mode"] == declared[identity["host"]] for identity in identities),
             "pair arm mode does not match the compiled plan")
    return identities


def pair_input_fingerprint(case_id: str, plan: Mapping[str, Any], arms: Sequence[Mapping[str, Any]]) -> str:
    """Bind both subject inputs, immutable captures, and independent grade identities."""
    stable_case_id = _identifier(case_id, "pair case id")
    identities = _validated_arm_identities(stable_case_id, plan, arms)
    payload = {
        "schema_version": PAIR_INPUT_SCHEMA_VERSION,
        "case_id": stable_case_id,
        "trial": identities[0]["trial"],
        "arms": identities,
    }
    return hashlib.sha256(_canonical(payload, "pair input fingerprint payload")).hexdigest()


def pair_grader_fingerprint(plan: Mapping[str, Any], grader_identity: object) -> str:
    """Bind pair-only comparison rules separately from captured subject evidence."""
    valid_identity = isinstance(grader_identity, str) and bool(grader_identity.strip())
    valid_identity = valid_identity or isinstance(grader_identity, dict) and bool(grader_identity)
    _require(valid_identity, "pair grader_identity must be a nonempty string or object")
    payload = {
        "schema_version": PAIR_GRADER_SCHEMA_VERSION,
        "plan": plan,
        "grader_identity": grader_identity,
    }
    return hashlib.sha256(_canonical(payload, "pair grader fingerprint payload")).hexdigest()


def _table(text: str, section_selector: str) -> list[str]:
    lines = text.splitlines()
    matches = [index for index, line in enumerate(lines) if line == section_selector]
    _require(bool(matches), f"section not found: {section_selector}")
    _require(len(matches) == 1, f"section is ambiguous: {section_selector}")
    start = matches[0] + 1
    section: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        section.append(line)
    table: list[str] = []
    started = False
    for line in section:
        if line.startswith("|"):
            started = True
            table.append(line)
        elif started:
            break
    _require(len(table) >= 2, f"section table not found: {section_selector}")
    _validate_table(table, section_selector)
    return table


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.split("|")[1:-1]]


def _validate_table(table: list[str], section_selector: str) -> None:
    _require(all(line.startswith("|") and line.endswith("|") for line in table),
             f"table rows must have leading and trailing pipes: {section_selector}")
    header = _cells(table[0])
    _require(bool(header) and all(header), f"table header is malformed: {section_selector}")
    _require(len(header) == len(set(header)), f"table header contains duplicate columns: {section_selector}")
    separator = _cells(table[1])
    _require(len(separator) == len(header), f"table separator width is malformed: {section_selector}")
    _require(all(re.fullmatch(r":?-{3,}:?", cell) is not None for cell in separator),
             f"table separator is malformed: {section_selector}")
    _require(all(len(_cells(line)) == len(header) for line in table[2:]),
             f"table data row width is malformed: {section_selector}")


def _column_values(text: str, section_selector: str, column: str) -> list[str]:
    table = _table(text, section_selector)
    header = _cells(table[0])
    try:
        index = header.index(column)
    except ValueError as exc:
        raise PairingError(f"table column not found: {column}") from exc
    values: list[str] = []
    for line in table[2:]:
        cells = _cells(line)
        values.append(cells[index])
    return values


def _extract(text: str, criterion: Mapping[str, Any]) -> str:
    extractor = criterion.get("extractor")
    if extractor is None:
        return text
    section = criterion["section_selector"]
    if extractor == "table_row_count":
        return str(max(0, len(_table(text, section)) - 2))
    return "\n".join(_column_values(text, section, extractor.removeprefix("table_column:")))


def _invariant_text(value: object) -> str:
    if type(value) is bool:
        return str(value).lower()
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _result(status: str, checks: list[dict[str, str]], semantic_request: dict[str, object] | None = None) -> dict[str, object]:
    result: dict[str, object] = {"status": status, "checks": checks}
    if semantic_request is not None:
        result["semantic_request"] = semantic_request
    return result


def _arm_evidence_failure(
    arm: object, identity: Mapping[str, object], index: int,
) -> dict[str, object] | None:
    grade = arm.get("grade") if isinstance(arm, dict) else None
    if not isinstance(grade, dict) or grade.get("status") not in {"pass", "fail", "invalid", "needs_judge"}:
        return _result("invalid", [{
            "id": "pair.arms", "verdict": "invalid", "reason": f"arm_{index + 1} grade is malformed",
        }])
    if grade["status"] == "fail":
        return _result("fail", [{
            "id": "pair.arms", "verdict": "fail",
            "reason": f"independent grade failed for {identity['host']} arm",
        }])
    if grade["status"] != "pass":
        return _result("invalid", [{
            "id": "pair.arms", "verdict": "invalid",
            "reason": f"independent grade is not terminal-pass for {identity['host']} arm",
        }])
    observation = arm.get("observation")
    artifacts = observation.get("artifacts") if isinstance(observation, dict) else None
    valid_artifacts = isinstance(artifacts, dict) and all(
        isinstance(key, str) and isinstance(value, str) for key, value in artifacts.items()
    )
    if not valid_artifacts:
        return _result("invalid", [{
            "id": "pair.arms", "verdict": "invalid", "reason": f"arm_{index + 1} artifacts are malformed",
        }])
    return None


def _arm_failure(case_id: str, plan: Mapping[str, Any], arms: object) -> dict[str, object] | None:
    try:
        identities = _validated_arm_identities(case_id, plan, arms)
    except PairingError as exc:
        return _result("invalid", [{"id": "pair.arms", "verdict": "invalid", "reason": str(exc)}])
    for index, (arm, identity) in enumerate(zip(arms, identities, strict=True)):
        failure = _arm_evidence_failure(arm, identity, index)
        if failure is not None:
            return failure
    return None


def _artifact(arm: Mapping[str, Any], path: str) -> str:
    artifacts = arm["observation"]["artifacts"]
    _require(path in artifacts, f"captured artifact is missing: {path}")
    return artifacts[path]


def _check_invariants(plan: Mapping[str, Any], arms: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, str]], str | None]:
    rows: list[dict[str, str]] = []
    for check in plan["checks"]:
        if not check["invariants"]:
            continue
        source = check["invariant_source"]
        for arm_index, arm in enumerate(arms):
            label = f"arm_{arm_index + 1}"
            try:
                text = _artifact(arm, source["source"])
                keys = _column_values(text, source["section_selector"], source["key_column"])
                values = _column_values(text, source["section_selector"], source["value_column"])
                _require(len(keys) == len(values) and len(keys) == len(set(keys)),
                         "invariant evidence must contain unique key/value rows")
            except PairingError as exc:
                rows.append({"id": f"{check['id']}.invariants.{label}", "verdict": "invalid", "reason": str(exc)})
                return rows, "invalid"
            observed = dict(zip(keys, values, strict=True))
            failures = [key for key, expected in check["invariants"].items()
                        if observed.get(key) != _invariant_text(expected)]
            if failures:
                rows.append({
                    "id": f"{check['id']}.invariants.{label}", "verdict": "fail",
                    "reason": f"independent invariant mismatch: {', '.join(failures)}",
                })
                return rows, "fail"
            rows.append({
                "id": f"{check['id']}.invariants.{label}", "verdict": "pass",
                "reason": "all explicitly selected invariants matched",
            })
    return rows, None


def _criterion_values(criterion: Mapping[str, Any], arms: Sequence[Mapping[str, Any]]) -> tuple[str, str]:
    values = []
    for arm in arms:
        values.append(_extract(_artifact(arm, criterion["source"]), criterion))
    return values[0], values[1]


def _semantic_verdicts(pending: list[dict[str, Any]], verdicts: object) -> tuple[dict[str, dict[str, object]] | None, str | None]:
    expected = {item["id"] for item in pending}
    if not isinstance(verdicts, dict) or set(verdicts) != expected:
        return None, "semantic verdicts must contain exactly the pending pair criterion ids"
    normalized: dict[str, dict[str, object]] = {}
    for criterion_id in sorted(expected):
        verdict = verdicts[criterion_id]
        if not isinstance(verdict, dict) or set(verdict) != {"passed", "evidence"}:
            return None, f"semantic verdict {criterion_id} is malformed"
        evidence = verdict["evidence"]
        if type(verdict["passed"]) is not bool or not isinstance(evidence, list) or not evidence:
            return None, f"semantic verdict {criterion_id} requires a boolean and evidence"
        if not all(isinstance(item, str) and bool(item.strip()) for item in evidence):
            return None, f"semantic verdict {criterion_id} has malformed evidence"
        normalized[criterion_id] = verdict
    return normalized, None


def _collect_comparisons(
    plan: Mapping[str, Any], arms: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, str]], list[tuple[dict[str, Any], str, str]]]:
    deterministic: list[dict[str, str]] = []
    semantic: list[tuple[dict[str, Any], str, str]] = []
    for check in plan["checks"]:
        for criterion in check["criteria"]:
            left, right = _criterion_values(criterion, arms)
            tolerance = criterion["tolerance"]
            if tolerance == "semantic-equivalent":
                semantic.append((criterion, left, right))
                continue
            passed = _deterministic_match(criterion, tolerance, left, right)
            deterministic.append({
                "id": criterion["id"], "verdict": "pass" if passed else "fail",
                "reason": f"{tolerance} comparison {'matched' if passed else 'differed'}",
            })
    return deterministic, semantic


def _deterministic_match(criterion: Mapping[str, Any], tolerance: str, left: str, right: str) -> bool:
    if tolerance != "tolerance-1":
        return left == right
    try:
        return abs(int(left) - int(right)) <= 1
    except ValueError as exc:
        raise PairingError(f"criterion {criterion['id']} did not produce integers") from exc


def _prepare_semantic(
    semantic: list[tuple[dict[str, Any], str, str]], rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    pending: list[dict[str, Any]] = []
    for criterion, left, right in semantic:
        if left == right:
            rows.append({
                "id": criterion["id"], "verdict": "pass",
                "reason": "semantic values were exactly equal",
            })
        else:
            pending.append({"id": criterion["id"], "rubric": criterion["rubric"],
                            "arm_a": left, "arm_b": right})
    return pending


def _blinded_request(pending: list[dict[str, Any]]) -> dict[str, object]:
    return {
        "semantic_criteria": [{"id": item["id"], "rubric": item["rubric"]} for item in pending],
        "evidence": {
            "arm_a": {item["id"]: item["arm_a"] for item in pending},
            "arm_b": {item["id"]: item["arm_b"] for item in pending},
        },
        "evidence_references": [
            reference for item in pending for reference in (f"arm_a/{item['id']}", f"arm_b/{item['id']}")
        ],
    }


def _apply_semantic_verdicts(
    rows: list[dict[str, str]], pending: list[dict[str, Any]], semantic_verdicts: object,
) -> dict[str, object]:
    verdicts, error = _semantic_verdicts(pending, semantic_verdicts)
    if error is not None:
        rows.append({"id": "pair.semantic", "verdict": "invalid", "reason": error})
        return _result("invalid", rows)
    semantic_rows = [{
        "id": item["id"],
        "verdict": "pass" if verdicts[item["id"]]["passed"] else "fail",
        "reason": "semantic judge accepted equivalence" if verdicts[item["id"]]["passed"]
        else "semantic judge rejected equivalence",
    } for item in pending]
    rows.extend(semantic_rows)
    return _result("fail" if any(row["verdict"] == "fail" for row in rows) else "pass", rows)


def grade_pair(
    case: Mapping[str, Any],
    plan: Mapping[str, Any],
    arms: Sequence[Mapping[str, Any]],
    semantic_verdicts: Mapping[str, Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """Grade a Claude/Codex pair only after both arms independently pass."""
    try:
        case_id = _identifier(case.get("id"), "pair case id")
        _require(plan.get("schema_version") == PAIR_PLAN_SCHEMA_VERSION, "compiled pair plan schema is unsupported")
        _require(plan.get("case_id") == case_id, "compiled pair plan belongs to a different case")
        checks = plan.get("checks")
        _require(isinstance(checks, list) and bool(checks),
                 "compiled pair checks must be nonempty")
        _require(all(isinstance(check, Mapping) and isinstance(check.get("criteria"), list)
                     and bool(check["criteria"]) for check in checks),
                 "compiled pair comparison criteria must be nonempty")
    except PairingError as exc:
        return _result("invalid", [{"id": "pair.contract", "verdict": "invalid", "reason": str(exc)}])
    failed_arm = _arm_failure(case_id, plan, arms)
    if failed_arm is not None:
        return failed_arm
    invariant_rows, invariant_status = _check_invariants(plan, arms)
    if invariant_status is not None:
        return _result(invariant_status, invariant_rows)
    try:
        deterministic, semantic = _collect_comparisons(plan, arms)
    except (KeyError, TypeError, PairingError) as exc:
        invariant_rows.append({"id": "pair.evidence", "verdict": "invalid", "reason": str(exc)})
        return _result("invalid", invariant_rows)
    rows = invariant_rows + deterministic
    if any(row["verdict"] == "fail" for row in deterministic):
        return _result("fail", rows)
    pending = _prepare_semantic(semantic, rows)
    if not pending:
        if semantic_verdicts not in (None, {}):
            rows.append({
                "id": "pair.semantic", "verdict": "invalid", "reason": "no semantic verdicts were requested",
            })
            return _result("invalid", rows)
        return _result("pass", rows)
    if semantic_verdicts is None:
        rows.extend({
            "id": item["id"], "verdict": "needs_judge", "reason": "semantic comparison requires a judge",
        } for item in pending)
        return _result("needs_judge", rows, _blinded_request(pending))
    return _apply_semantic_verdicts(rows, pending, semantic_verdicts)


__all__ = (
    "EXPECTED_SCHEMA_VERSION", "HOSTS", "PAIR_GRADER_SCHEMA_VERSION", "PAIR_INPUT_SCHEMA_VERSION",
    "PAIR_PLAN_SCHEMA_VERSION", "PAIR_SCHEMA_VERSION", "PairingError", "TOLERANCE_SCHEMA_VERSION",
    "TOLERANCES", "compile_pair_plan", "grade_pair", "pair_grader_fingerprint",
    "pair_input_fingerprint",
)
