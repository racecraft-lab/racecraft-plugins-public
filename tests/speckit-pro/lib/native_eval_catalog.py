"""Canonical, provider-free native-evaluation catalog contracts."""

from __future__ import annotations

import hashlib
import fnmatch
import json
import math
from pathlib import Path, PurePosixPath
import re
from typing import Any, Iterable

from native_eval_git_grading import CHECK_FIELDS as NATIVE_GIT_FINAL_STATE_FIELDS
from native_eval_git_grading import validate_check as validate_native_git_final_state_check
from native_eval_pairing import compile_pair_plan
from native_eval_runner_result import CHECK_FIELDS as NATIVE_RUNNER_RESULT_FIELDS
from native_eval_runner_result import validate_check as validate_native_runner_result_check
from native_eval_verification import CHECK_FIELDS as NATIVE_VERIFICATION_POINTER_FIELDS
from native_eval_verification import validate_check as validate_native_verification_pointer_check


SCHEMA_VERSION = "native-eval-catalog/v1"
LAYERS = frozenset({"trigger", "functional", "integration", "parity"})
HOSTS = ("claude", "codex")
NATIVE_SYNTHESIS_MECHANISMS = {
    "claude": {"mode": "dedicated_subagent", "role": "speckit-pro:consensus-synthesizer"},
    "codex": {"mode": "dedicated_subagent", "role": "consensus-synthesizer"},
}
RESOURCE_CLASSES = frozenset({"ordinary", "nested"})
REQUIRED_TOOLS = frozenset({"specify"})
MAX_TIMEOUT_SECONDS = 3600
GIT_FIXTURE_RECIPE = "baseline-feature-origin-main/v1"
_GIT_RESERVED_ROOTS = frozenset({".agents", ".claude", ".codex", ".git"})
CHECK_TYPES = frozenset({
    "selection", "text", "file_exists", "json_field", "response_json_field",
    "tool_used", "tool_order", "file_access", "file_search", "semantic", "subagent_returns_before_parent_file_change",
    "native_synthesis_mechanism", "native_subagent_dispatch", "native_plan_repair_context",
    "native_git_final_state", "native_verification_pointer", "native_runner_result",
})
_STABLE_ID = re.compile(r"[a-z0-9][a-z0-9._-]*")
_CROSS_HOST_RUBRIC = re.compile(
    r"\bcross[- ]host\b|\bboth\s+(?:native\s+)?(?:hosts?|arms?|observations?)\b|"
    r"\bbetween\s+(?:the\s+)?(?:two\s+)?(?:hosts?|arms?)\b|"
    r"\bclaude\b[\s\S]*\bcodex\b|\bcodex\b[\s\S]*\bclaude\b",
    re.IGNORECASE,
)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _nonempty_text(value: object, label: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{label} must be nonempty text")
    return value


def _stable_id(value: object, label: str) -> str:
    text = _nonempty_text(value, label)
    _require(_STABLE_ID.fullmatch(text) is not None, f"{label} is not a stable identifier")
    return text


def _unique_text_list(value: object, label: str, *, nonempty: bool = False) -> list[str]:
    _require(isinstance(value, list), f"{label} must be a list")
    _require(not nonempty or bool(value), f"{label} must be nonempty")
    result = [_nonempty_text(item, f"{label} item") for item in value]
    _require(len(result) == len(set(result)), f"{label} contains duplicates")
    return result


def _relative_path(value: object, label: str) -> PurePosixPath:
    text = _nonempty_text(value, label)
    _require("\\" not in text, f"{label} must use repository-style separators")
    path = PurePosixPath(text)
    _require(not path.is_absolute(), f"{label} must be relative")
    _require(text == path.as_posix() and all(part not in {"", ".", ".."} for part in path.parts),
             f"{label} is not a canonical relative path")
    return path


def _json_value(value: object, label: str) -> None:
    _require(_is_json_value(value), f"{label} must be a strict JSON value")
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a strict JSON value") from exc


def _is_json_value(value: object) -> bool:
    if value is None or type(value) in {bool, int, str}:
        return True
    if type(value) is float:
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_is_json_value(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _is_json_value(item) for key, item in value.items())
    return False


def _regex(value: object, label: str) -> str:
    pattern = _nonempty_text(value, label)
    try:
        re.compile(pattern)
    except re.error as exc:
        raise ValueError(f"{label} is not a valid regular expression: {exc}") from exc
    return pattern


def _validate_fixture(fixture: object, repo_root: Path, case_id: str) -> PurePosixPath:
    _require(isinstance(fixture, dict) and set(fixture) == {"source", "destination"},
             f"case {case_id} has a malformed fixture")
    source = _relative_path(fixture["source"], f"case {case_id} fixture source")
    destination = _relative_path(fixture["destination"], f"case {case_id} fixture destination")
    _require(source.parts[:2] == ("tests", "speckit-pro"),
             f"case {case_id} fixture source must be under tests/speckit-pro")
    tests_root = (repo_root / "tests" / "speckit-pro").resolve(strict=True)
    try:
        resolved = repo_root.joinpath(*source.parts).resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"case {case_id} fixture source is missing: {source}") from exc
    _require(resolved.is_relative_to(tests_root), f"case {case_id} fixture source escaped tests/speckit-pro")
    _require(resolved.is_file(), f"case {case_id} fixture source must be a file")
    return destination


def _validate_fixture_destinations(destinations: list[PurePosixPath], case_id: str) -> None:
    _require(len(destinations) == len(set(destinations)), f"case {case_id} has duplicate fixture destinations")
    for index, left in enumerate(destinations):
        for right in destinations[index + 1:]:
            shared_prefix = left.parts == right.parts[:len(left.parts)]
            shared_prefix = shared_prefix or right.parts == left.parts[:len(right.parts)]
            _require(not shared_prefix, f"case {case_id} has overlapping fixture destinations")


def _validate_git_fixture(value: object, repo_root: Path, case_id: str) -> list[PurePosixPath]:
    _require(isinstance(value, dict) and set(value) in (
        {"recipe", "baseline"}, {"recipe", "baseline", "worktrees"},
    ),
             f"case {case_id} has malformed git_fixture")
    _require(value["recipe"] == GIT_FIXTURE_RECIPE,
             f"case {case_id} has unsupported git fixture recipe")
    baseline = value["baseline"]
    _require(isinstance(baseline, list) and bool(baseline),
             f"case {case_id} git fixture baseline must be nonempty")
    destinations = [_validate_fixture(fixture, repo_root, case_id) for fixture in baseline]
    _validate_fixture_destinations(destinations, case_id)
    _require(all(destination.parts[0].casefold() not in _GIT_RESERVED_ROOTS for destination in destinations),
             f"case {case_id} git fixture cannot target a reserved runtime path")
    if "worktrees" in value:
        rows = value["worktrees"]
        _require(isinstance(rows, list) and 1 <= len(rows) <= 4,
                 f"case {case_id} git worktrees must contain one to four entries")
        paths: set[str] = set()
        branches: set[str] = set()
        for row in rows:
            _require(isinstance(row, dict) and set(row) == {"path", "branch", "revision"},
                     f"case {case_id} git worktree entry has malformed fields")
            path, branch, revision = row["path"], row["branch"], row["revision"]
            _require(isinstance(path, str)
                     and re.fullmatch(r"\.worktrees/[a-z0-9][a-z0-9-]{0,63}", path) is not None,
                     f"case {case_id} git worktree path must be a confined .worktrees child")
            _require(isinstance(branch, str)
                     and re.fullmatch(r"scenario/[a-z0-9][a-z0-9-]{0,63}", branch) is not None,
                     f"case {case_id} git worktree branch must be a scenario branch")
            _require(revision in {"baseline", "feature"},
                     f"case {case_id} git worktree revision must be baseline or feature")
            _require(path not in paths and branch not in branches,
                     f"case {case_id} git worktrees contain a duplicate path or branch")
            paths.add(path)
            branches.add(branch)
        _require(all(destination.parts[0].casefold() != ".worktrees" for destination in destinations),
                 f"case {case_id} git worktrees reserve the .worktrees directory")
    return destinations


def _validate_host(host: object, case_id: str, host_name: str) -> None:
    _require(isinstance(host, dict) and set(host) == {"skill", "allowed_tools", "modes"},
             f"case {case_id} has malformed {host_name} settings")
    skill = host["skill"]
    _require(skill is None or isinstance(skill, str) and bool(skill.strip()),
             f"case {case_id} {host_name} skill must be nonempty text or null")
    _unique_text_list(host["allowed_tools"], f"case {case_id} {host_name} allowed_tools")
    _unique_text_list(host["modes"], f"case {case_id} {host_name} modes", nonempty=True)


def _check_label(case_id: str, check_id: str, field: str) -> str:
    return f"case {case_id} check {check_id} {field}"


def _validate_selection_check(check: dict[str, Any], case_id: str, check_id: str) -> None:
    expected = _unique_text_list(check["expected"], _check_label(case_id, check_id, "expected"))
    allowed_extra = _unique_text_list(check["allowed_extra"], _check_label(case_id, check_id, "allowed_extra"))
    _require(set(expected).isdisjoint(allowed_extra), _check_label(case_id, check_id, "repeats allowed selections"))


def _validate_text_check(check: dict[str, Any], case_id: str, check_id: str) -> None:
    if check["source"] != "final_text":
        _relative_path(check["source"], _check_label(case_id, check_id, "source"))
    _regex(check["pattern"], _check_label(case_id, check_id, "pattern"))


def _validate_file_exists_check(check: dict[str, Any], case_id: str, check_id: str) -> None:
    _relative_path(check["path"], _check_label(case_id, check_id, "path"))
    _require(type(check["exists"]) is bool, _check_label(case_id, check_id, "exists must be boolean"))


def _validate_json_field_check(check: dict[str, Any], case_id: str, check_id: str) -> None:
    _relative_path(check["path"], _check_label(case_id, check_id, "path"))
    field_path = check["field_path"]
    _require(isinstance(field_path, list) and bool(field_path),
             _check_label(case_id, check_id, "field_path must be nonempty"))
    _require(all(isinstance(part, str) and bool(part) or type(part) is int and part >= 0 for part in field_path),
             _check_label(case_id, check_id, "field_path is malformed"))
    _json_value(check["expected"], _check_label(case_id, check_id, "expected"))
    if "alternatives" in check:
        alternatives = check["alternatives"]
        _require(isinstance(alternatives, list) and bool(alternatives),
                 _check_label(case_id, check_id, "alternatives must be a nonempty list"))
        for index, value in enumerate(alternatives):
            _json_value(value, _check_label(case_id, check_id, f"alternatives[{index}]"))


def _validate_response_json_field_check(check: dict[str, Any], case_id: str, check_id: str) -> None:
    field_path = check["field_path"]
    _require(isinstance(field_path, list) and bool(field_path),
             _check_label(case_id, check_id, "field_path must be nonempty"))
    _require(all(isinstance(part, str) and bool(part) or type(part) is int and part >= 0
                 for part in field_path),
             _check_label(case_id, check_id, "field_path is malformed"))
    expected = check["expected_by_host"]
    _require(isinstance(expected, dict) and set(expected) == set(HOSTS),
             _check_label(case_id, check_id, "expected_by_host must define exactly claude and codex"))
    for host in HOSTS:
        _json_value(expected[host], _check_label(case_id, check_id, f"expected_by_host.{host}"))


def _validate_tool_used_check(check: dict[str, Any], case_id: str, check_id: str) -> None:
    _nonempty_text(check["name"], _check_label(case_id, check_id, "name"))
    minimum, maximum = check["min"], check["max"]
    _require(type(minimum) is int and type(maximum) is int and 0 <= minimum <= maximum,
             _check_label(case_id, check_id, "requires integer 0 <= min <= max"))
    if "input_regex" in check:
        _regex(check["input_regex"], _check_label(case_id, check_id, "input_regex"))
    if "include_failed" in check:
        _require(type(check["include_failed"]) is bool,
                 _check_label(case_id, check_id, "include_failed must be boolean"))


def _validate_tool_order_check(check: dict[str, Any], case_id: str, check_id: str) -> None:
    before = _nonempty_text(check["before"], _check_label(case_id, check_id, "before"))
    after = _nonempty_text(check["after"], _check_label(case_id, check_id, "after"))
    _require(before != after, _check_label(case_id, check_id, "tool order must name different tools"))


def _validate_file_access_check(check: dict[str, Any], case_id: str, check_id: str) -> None:
    _require(check["operation"] == "read_file",
             _check_label(case_id, check_id, "operation must be read_file"))
    _relative_path(check["path"], _check_label(case_id, check_id, "path"))


def _search_glob(value: object) -> str:
    _require(isinstance(value, str) and re.fullmatch(r"\*\*/[A-Za-z0-9*?_.-]+", value) is not None,
             "file search pattern must be a recursive basename glob")
    return value[3:]


def _validate_file_search_check(check: dict[str, Any], case_id: str, check_id: str) -> None:
    basename = _search_glob(check.get("pattern"))
    matches = check.get("matches")
    _require(isinstance(matches, list), "file search matches must be a list")
    for value in matches:
        path = _relative_path(value, _check_label(case_id, check_id, "search match"))
        _require(fnmatch.fnmatchcase(path.name, basename), "file search match must satisfy its pattern")
    _require(len(set(matches)) == len(matches), "file search matches must be unique")


def _validate_semantic_check(check: dict[str, Any], case_id: str, check_id: str) -> None:
    _nonempty_text(check["rubric"], _check_label(case_id, check_id, "rubric"))


def _validate_subagent_returns_before_parent_file_change(
    check: dict[str, Any], case_id: str, check_id: str,
) -> None:
    _relative_path(check["path"], _check_label(case_id, check_id, "path"))


def _validate_native_synthesis_mechanism(
    check: dict[str, Any], case_id: str, check_id: str,
) -> None:
    _relative_path(check["artifact_path"], _check_label(case_id, check_id, "artifact_path"))
    per_host = check["per_host"]
    _require(isinstance(per_host, dict) and set(per_host) == set(HOSTS),
             _check_label(case_id, check_id, "per_host must define exactly claude and codex"))
    for host in HOSTS:
        settings = per_host[host]
        _require(isinstance(settings, dict) and set(settings) == {"mode", "role"},
                 _check_label(case_id, check_id, f"has malformed {host} settings"))
        expected = NATIVE_SYNTHESIS_MECHANISMS[host]
        _require(settings["mode"] == expected["mode"],
                 _check_label(case_id, check_id,
                              f"{host} mode must be {expected['mode']}"))
        _require(settings["role"] == expected["role"],
                 _check_label(case_id, check_id,
                              f"{host} role must be {expected['role']}"))


def _validate_native_subagent_dispatch(
    check: dict[str, Any], case_id: str, check_id: str,
) -> None:
    label = _check_label(case_id, check_id, "expected")
    expected = check["expected"]
    _require(isinstance(expected, list) and bool(expected), f"{label} must be nonempty")
    pairs: list[tuple[str, str]] = []
    for item in expected:
        _require(isinstance(item, dict) and set(item) == {"item_id", "role"},
                 f"{label} item is malformed")
        pairs.append((
            _stable_id(item["item_id"], f"{label} item_id"),
            _stable_id(item["role"], f"{label} role"),
        ))
    _require(len(pairs) == len(set(pairs)), f"{label} contains duplicates")
    forbidden = [
        _stable_id(role, _check_label(case_id, check_id, "forbidden_roles item"))
        for role in _unique_text_list(
            check["forbidden_roles"], _check_label(case_id, check_id, "forbidden_roles"),
        )
    ]
    _require(set(forbidden).isdisjoint(role for _item_id, role in pairs),
             _check_label(case_id, check_id, "forbidden_roles overlap expected roles"))


def _validate_native_plan_repair_context(
    check: dict[str, Any], case_id: str, check_id: str,
) -> None:
    contexts = check["contexts"]
    _require(isinstance(contexts, dict) and 1 <= len(contexts) <= 16,
             _check_label(case_id, check_id, "contexts must contain 1 to 16 entries"))
    for context_id, path in contexts.items():
        _stable_id(context_id, _check_label(case_id, check_id, "context id"))
        _relative_path(path, _check_label(case_id, check_id, "context path"))
    _relative_path(
        check["g3_request_path"], _check_label(case_id, check_id, "g3_request_path"),
    )
    _stable_id(
        check["executor_role"], _check_label(case_id, check_id, "executor_role"),
    )
    _require(type(check["max_repairs"]) is int and check["max_repairs"] == 2,
             _check_label(case_id, check_id, "max_repairs must be exactly 2"))
    _require(isinstance(check["terminal_outcome"], str)
             and check["terminal_outcome"] in {"pass", "unresolved"},
             _check_label(case_id, check_id, "terminal_outcome must be pass or unresolved"))


def _validate_native_git_final_state(
    check: dict[str, Any], case_id: str, check_id: str,
) -> None:
    validate_native_git_final_state_check(check, _check_label(case_id, check_id, "contract"))


def _validate_native_verification_pointer(
    check: dict[str, Any], case_id: str, check_id: str,
) -> None:
    validate_native_verification_pointer_check(
        check, _check_label(case_id, check_id, "contract")
    )


def _validate_native_runner_result(
    check: dict[str, Any], case_id: str, check_id: str,
) -> None:
    validate_native_runner_result_check(
        check, _check_label(case_id, check_id, "contract")
    )


_CHECK_FIELDS = {
    "selection": {"expected", "allowed_extra"},
    "text": {"source", "pattern"},
    "file_exists": {"path", "exists"},
    "json_field": {"path", "field_path", "expected"},
    "response_json_field": {"field_path", "expected_by_host"},
    "tool_used": {"name", "min", "max"},
    "tool_order": {"before", "after"},
    "file_access": {"operation", "path"},
    "file_search": {"pattern", "matches"},
    "semantic": {"rubric"},
    "subagent_returns_before_parent_file_change": {"path"},
    "native_synthesis_mechanism": {"artifact_path", "per_host"},
    "native_subagent_dispatch": {"expected", "forbidden_roles"},
    "native_plan_repair_context": {
        "contexts", "g3_request_path", "executor_role", "max_repairs", "terminal_outcome",
    },
    "native_git_final_state": set(NATIVE_GIT_FINAL_STATE_FIELDS),
    "native_verification_pointer": set(NATIVE_VERIFICATION_POINTER_FIELDS),
    "native_runner_result": set(NATIVE_RUNNER_RESULT_FIELDS),
}
_CHECK_VALIDATORS = {
    "selection": _validate_selection_check,
    "text": _validate_text_check,
    "file_exists": _validate_file_exists_check,
    "json_field": _validate_json_field_check,
    "response_json_field": _validate_response_json_field_check,
    "tool_used": _validate_tool_used_check,
    "tool_order": _validate_tool_order_check,
    "file_access": _validate_file_access_check,
    "file_search": _validate_file_search_check,
    "semantic": _validate_semantic_check,
    "subagent_returns_before_parent_file_change": _validate_subagent_returns_before_parent_file_change,
    "native_synthesis_mechanism": _validate_native_synthesis_mechanism,
    "native_subagent_dispatch": _validate_native_subagent_dispatch,
    "native_plan_repair_context": _validate_native_plan_repair_context,
    "native_git_final_state": _validate_native_git_final_state,
    "native_verification_pointer": _validate_native_verification_pointer,
    "native_runner_result": _validate_native_runner_result,
}


def _validate_check(check: object, requirement_ids: set[str], case_id: str) -> None:
    _require(isinstance(check, dict), f"case {case_id} has a malformed check")
    check_id = _stable_id(check.get("id"), f"case {case_id} check id")
    requirement = _stable_id(check.get("requirement"), _check_label(case_id, check_id, "requirement"))
    _require(requirement in requirement_ids, _check_label(case_id, check_id, "references an unknown requirement"))
    check_type = check.get("type")
    _require(isinstance(check_type, str) and check_type in CHECK_TYPES,
             _check_label(case_id, check_id, "has an unknown type"))
    required = {"id", "requirement", "type"} | _CHECK_FIELDS[check_type]
    optional = ({"input_regex", "include_failed"} if check_type == "tool_used" else
                {"alternatives"} if check_type == "json_field" else
                {"registered_worktrees_unchanged"} if check_type == "native_git_final_state" else set())
    allowed = required | optional
    _require(required <= set(check) <= allowed, _check_label(case_id, check_id, "has malformed parameters"))
    _CHECK_VALIDATORS[check_type](check, case_id, check_id)


def _validate_case(case: object, repo_root: Path) -> None:
    base_fields = {
        "id", "layer", "capability", "requirements", "prompt", "fixtures",
        "hosts", "checks", "native_differences", "provenance", "timeout_seconds",
        "resource_class",
    }
    _require(isinstance(case, dict), "catalog contains a malformed case")
    layer = case.get("layer")
    if layer == "parity":
        _require("pairing" in case, "parity case must define pairing")
    else:
        _require("pairing" not in case, "pairing is forbidden outside parity cases")
    fields = base_fields | ({"pairing"} if layer == "parity" else set())
    if "git_fixture" in case:
        fields |= {"git_fixture"}
    if "required_tools" in case:
        fields |= {"required_tools"}
    _require(isinstance(case, dict) and set(case) == fields, "catalog contains a malformed case")
    case_id = _stable_id(case["id"], "case id")
    _require(isinstance(case["layer"], str) and case["layer"] in LAYERS,
             f"case {case_id} has an unknown layer")
    timeout = case["timeout_seconds"]
    _require(type(timeout) is int and 1 <= timeout <= MAX_TIMEOUT_SECONDS,
             f"case {case_id} timeout_seconds must be an integer from 1 through {MAX_TIMEOUT_SECONDS}")
    _require(isinstance(case["resource_class"], str) and case["resource_class"] in RESOURCE_CLASSES,
             f"case {case_id} has an unknown resource_class")
    if "required_tools" in case:
        required_tools = _unique_text_list(
            case["required_tools"], f"case {case_id} required_tools", nonempty=True,
        )
        unknown_tools = sorted(set(required_tools) - REQUIRED_TOOLS)
        _require(not unknown_tools,
                 f"case {case_id} has an unsupported required tool: {unknown_tools!r}")
    _nonempty_text(case["capability"], f"case {case_id} capability")
    prompt = _nonempty_text(case["prompt"], f"case {case_id} prompt")
    placeholders = re.findall(r"{{[^{}]*}}", prompt)
    _require(all(item == "{{skill}}" for item in placeholders)
             and not re.search(r"{{|}}", prompt.replace("{{skill}}", "")),
             f"case {case_id} prompt contains an unsupported placeholder")
    requirements = case["requirements"]
    _require(isinstance(requirements, list) and bool(requirements), f"case {case_id} has no requirements")
    requirement_ids: list[str] = []
    for requirement in requirements:
        _require(isinstance(requirement, dict) and set(requirement) == {"id", "description"},
                 f"case {case_id} has a malformed requirement")
        requirement_ids.append(_stable_id(requirement["id"], f"case {case_id} requirement id"))
        _nonempty_text(requirement["description"], f"case {case_id} requirement description")
    _require(len(requirement_ids) == len(set(requirement_ids)), f"case {case_id} has duplicate requirement ids")
    fixtures = case["fixtures"]
    _require(isinstance(fixtures, list), f"case {case_id} fixtures must be a list")
    destinations = [_validate_fixture(fixture, repo_root, case_id) for fixture in fixtures]
    _validate_fixture_destinations(destinations, case_id)
    if "git_fixture" in case:
        baseline_destinations = _validate_git_fixture(case["git_fixture"], repo_root, case_id)
        _require(all(destination.parts[0].casefold() not in _GIT_RESERVED_ROOTS for destination in destinations),
                 f"case {case_id} git fixture cannot target a reserved runtime path")
        for destination in destinations:
            for baseline_destination in baseline_destinations:
                shared_prefix = destination.parts == baseline_destination.parts[:len(destination.parts)]
                shared_prefix = shared_prefix or baseline_destination.parts == destination.parts[:len(baseline_destination.parts)]
                _require(destination == baseline_destination or not shared_prefix,
                         f"case {case_id} has overlapping fixture destinations")
        if "worktrees" in case["git_fixture"]:
            _require(all(destination.parts[0].casefold() != ".worktrees" for destination in destinations),
                     f"case {case_id} git worktrees reserve the .worktrees directory")
    hosts = case["hosts"]
    _require(isinstance(hosts, dict) and set(hosts) == set(HOSTS),
             f"case {case_id} must define exactly claude and codex")
    for host_name in HOSTS:
        _validate_host(hosts[host_name], case_id, host_name)
    if "{{skill}}" in prompt:
        _require(all(hosts[name]["skill"] is not None for name in HOSTS),
                 f"case {case_id} cannot interpolate a null host skill")
    checks = case["checks"]
    _require(isinstance(checks, list) and bool(checks), f"case {case_id} has no checks")
    for check in checks:
        _validate_check(check, set(requirement_ids), case_id)
        if check.get("type") == "semantic":
            _require(_CROSS_HOST_RUBRIC.search(check["rubric"]) is None,
                     f"case {case_id} per-host semantic check requires cross-host evidence; use pairing")
    declared_artifacts = {
        check["path"] for check in checks
        if check.get("type") in {"json_field", "file_exists"}
        and (check.get("type") != "file_exists" or check.get("exists") is True)
    }
    declared_artifacts.update(
        check["source"] for check in checks
        if check.get("type") == "text" and check.get("source") != "final_text"
    )
    mechanism_checks = [check for check in checks if check.get("type") == "native_synthesis_mechanism"]
    for check in mechanism_checks:
        _require(check["artifact_path"] in declared_artifacts,
                 f"case {case_id} native synthesis artifact_path must be declared by an artifact check")
    _require(not mechanism_checks or any(check.get("type") == "file_access" for check in checks),
             f"case {case_id} native synthesis mechanism requires at least one file_access check")
    dispatch_checks = [check for check in checks if check.get("type") == "native_subagent_dispatch"]
    _require(not dispatch_checks or case["resource_class"] == "nested",
             f"case {case_id} native subagent dispatch requires nested resource_class")
    plan_repair_checks = [
        check for check in checks if check.get("type") == "native_plan_repair_context"
    ]
    _require(not plan_repair_checks or case["resource_class"] == "nested",
             f"case {case_id} native Plan-repair context requires nested resource_class")
    _require(not plan_repair_checks or case.get("required_tools") == ["specify"],
             f"case {case_id} native Plan-repair context requires required_tools [specify]")
    git_final_state_checks = [
        check for check in checks if check.get("type") == "native_git_final_state"
    ]
    _require(not git_final_state_checks or "git_fixture" in case,
             f"case {case_id} native Git final state requires git_fixture")
    _require(not any(check.get("registered_worktrees_unchanged") for check in git_final_state_checks)
             or bool(case.get("git_fixture", {}).get("worktrees")),
             f"case {case_id} registered worktree preservation requires declared worktrees")
    verification_checks = [
        check for check in checks if check.get("type") == "native_verification_pointer"
    ]
    _require(len(verification_checks) <= 1,
             f"case {case_id} has ambiguous native verification pointer checks")
    runner_result_checks = [
        check for check in checks if check.get("type") == "native_runner_result"
    ]
    _require(len(runner_result_checks) <= 1,
             f"case {case_id} has ambiguous native runner result checks")
    declared_fixture_paths = {destination.as_posix() for destination in destinations}
    for check in runner_result_checks:
        _require(check["request_path"] in declared_fixture_paths,
                 f"case {case_id} native runner request_path must reference a declared fixture")
    for check in plan_repair_checks:
        required_fixture_paths = {*check["contexts"].values(), check["g3_request_path"]}
        _require(required_fixture_paths <= declared_fixture_paths,
                 f"case {case_id} native Plan-repair context must reference declared fixtures")
    check_ids = [check["id"] for check in checks]
    _require(len(check_ids) == len(set(check_ids)), f"case {case_id} has duplicate check ids")
    covered = {check["requirement"] for check in checks}
    _require(covered == set(requirement_ids), f"case {case_id} has uncovered requirements")
    if case["layer"] == "parity":
        compile_pair_plan(case, repo_root)
    _unique_text_list(case["native_differences"], f"case {case_id} native_differences")
    _unique_text_list(case["provenance"], f"case {case_id} provenance", nonempty=True)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    _require(len(pairs) == len({key for key, _value in pairs}), "duplicate JSON key")
    return dict(pairs)


def load_catalog(path: str | Path, repo_root: str | Path) -> dict[str, Any]:
    """Load strict JSON and return it only after full catalog validation."""
    try:
        catalog = json.loads(
            Path(path).read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=lambda token: (_ for _ in ()).throw(ValueError(f"invalid constant {token}")),
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not load native evaluation catalog: {exc}") from exc
    return validate_catalog(catalog, repo_root)


def validate_catalog(catalog: object, repo_root: str | Path) -> dict[str, Any]:
    """Validate schema, coverage, hosts, checks, and fixture containment."""
    try:
        root = Path(repo_root).resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"repository root is unavailable: {repo_root}") from exc
    _require(root.is_dir(), "repository root must be a directory")
    _require(isinstance(catalog, dict) and set(catalog) == {"schema_version", "cases"},
             "catalog must contain only schema_version and cases")
    _require(catalog["schema_version"] == SCHEMA_VERSION, "unsupported native evaluation catalog schema")
    cases = catalog["cases"]
    _require(isinstance(cases, list) and bool(cases), "catalog cases must be nonempty")
    for case in cases:
        _validate_case(case, root)
    case_ids = [case["id"] for case in cases]
    _require(len(case_ids) == len(set(case_ids)), "catalog has duplicate case ids")
    return catalog


def _filter_values(value: object, label: str) -> set[str] | None:
    if value is None:
        return None
    _require(isinstance(value, (list, tuple, set, frozenset)) and bool(value),
             f"{label} filter must be a nonempty collection")
    items = [_nonempty_text(item, f"{label} filter item") for item in value]
    _require(len(items) == len(set(items)), f"{label} filter contains duplicates")
    return set(items)


def select_cases(
    catalog: dict[str, Any],
    layers: Iterable[str] | None = None,
    case_ids: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Select in catalog order; reject unknown filters and empty results."""
    _require(isinstance(catalog, dict) and isinstance(catalog.get("cases"), list) and bool(catalog["cases"]),
             "catalog has no selectable cases")
    cases = catalog["cases"]
    available_layers = {case.get("layer") for case in cases if isinstance(case, dict)}
    available_ids = {case.get("id") for case in cases if isinstance(case, dict)}
    requested_layers = _filter_values(layers, "layers")
    requested_ids = _filter_values(case_ids, "case_ids")
    if requested_layers is not None:
        _require(requested_layers <= available_layers, "layers filter contains unknown values")
    if requested_ids is not None:
        _require(requested_ids <= available_ids, "case_ids filter contains unknown values")
    selected = [
        case for case in cases
        if (requested_layers is None or case["layer"] in requested_layers)
        and (requested_ids is None or case["id"] in requested_ids)
    ]
    _require(bool(selected), "case filters selected no cases")
    return selected


def plan_trials(
    cases: list[dict[str, Any]],
    hosts: tuple[str, ...] = HOSTS,
    runs: int = 1,
) -> list[dict[str, object]]:
    """Expand cases, requested hosts, declared modes, and one-based trials."""
    _require(isinstance(cases, list) and bool(cases), "trial planning requires selected cases")
    _require(isinstance(hosts, (list, tuple)) and bool(hosts), "trial planning requires hosts")
    _require(all(isinstance(host, str) and bool(host) for host in hosts), "trial hosts are malformed")
    _require(len(hosts) == len(set(hosts)), "trial hosts contain duplicates")
    _require(set(hosts) <= set(HOSTS), "trial planning contains an unknown host")
    _require(type(runs) is int and 1 <= runs <= 50, "runs must be an integer from 1 through 50")
    rows: list[dict[str, object]] = []
    for case in cases:
        _require(isinstance(case, dict) and isinstance(case.get("id"), str), "trial case is malformed")
        case_hosts = case.get("hosts")
        _require(isinstance(case_hosts, dict), f"case {case['id']} has no host settings")
        for host in hosts:
            _require(host in case_hosts, f"case {case['id']} does not support requested host {host}")
            modes = case_hosts[host].get("modes") if isinstance(case_hosts[host], dict) else None
            _require(isinstance(modes, list) and bool(modes), f"case {case['id']} host {host} has no modes")
            for mode in modes:
                for trial in range(1, runs + 1):
                    rows.append({"case_id": case["id"], "host": host, "mode": mode, "trial": trial})
    return rows


def input_fingerprint(
    case: dict[str, Any],
    host: str,
    mode: str,
    runtime_identity: object,
) -> str:
    """Bind trial inputs and runtime identity, deliberately excluding grader identity."""
    _require(isinstance(case, dict) and isinstance(case.get("id"), str), "fingerprint case is malformed")
    hosts = case.get("hosts")
    _require(isinstance(hosts, dict) and host in hosts, "fingerprint host is not declared by the case")
    host_settings = hosts[host]
    _require(isinstance(host_settings, dict) and mode in host_settings.get("modes", []),
             "fingerprint mode is not declared by the case host")
    valid_identity = isinstance(runtime_identity, str) and bool(runtime_identity.strip())
    valid_identity = valid_identity or isinstance(runtime_identity, dict) and bool(runtime_identity)
    _require(valid_identity, "runtime_identity must be a nonempty string or object")
    case_input_keys = ["id", "prompt", "fixtures", "timeout_seconds", "resource_class"]
    if "required_tools" in case:
        case_input_keys.append("required_tools")
    payload = {
        "schema_version": "native-eval-input/v1",
        "case_inputs": {key: case[key] for key in case_input_keys},
        "host_settings": host_settings,
        "host": host,
        "mode": mode,
        "runtime_identity": runtime_identity,
    }
    _json_value(payload, "fingerprint input")
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


__all__ = (
    "CHECK_TYPES", "GIT_FIXTURE_RECIPE", "HOSTS", "LAYERS", "MAX_TIMEOUT_SECONDS", "REQUIRED_TOOLS",
    "RESOURCE_CLASSES",
    "SCHEMA_VERSION", "input_fingerprint", "load_catalog", "plan_trials",
    "select_cases", "validate_catalog",
)
