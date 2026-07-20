#!/usr/bin/env python3
"""Bounded JSON-schema and retained-string validation."""

from __future__ import annotations

from treatment_trace_io import *

def _read_manifest_snapshot(path: Path) -> dict:
    manifest = _read_json_file(path)
    if not isinstance(manifest, dict):
        raise ValueError("candidate manifest must be a JSON object")
    _validate_resource_bounds(manifest)
    _capability_module().validate_manifest(manifest)
    return manifest


def _validate_schema_timestamp(value: str, label: str) -> None:
    if RFC3339_UTC_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be an RFC3339 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise ValueError(f"{label} must be an RFC3339 timestamp") from exc
    if parsed.utcoffset() is None:
        raise ValueError(f"{label} must be an RFC3339 UTC timestamp")


def _validate_resource_bounds(value: object, *, depth: int = 0, counter: list[int] | None = None) -> None:
    if counter is None: counter = [0]
    counter[0] += 1
    if counter[0] > MAX_TOTAL_NODES: raise ValueError("treatment input exceeds the maximum node count")
    if depth > MAX_NESTING_DEPTH: raise ValueError("treatment input exceeds the maximum nesting depth")
    if isinstance(value, str) and len(value) > MAX_RETAINED_STRING_LENGTH:
        raise ValueError("treatment input contains an oversized retained string")
    if isinstance(value, (list, dict)):
        if len(value) > MAX_COLLECTION_ITEMS: raise ValueError("treatment input contains an oversized collection")
        if isinstance(value, dict):
            for key, item in value.items():
                _validate_resource_bounds(key, depth=depth + 1, counter=counter)
                _validate_resource_bounds(item, depth=depth + 1, counter=counter)
        else:
            for item in value:
                _validate_resource_bounds(item, depth=depth + 1, counter=counter)


def _json_type_matches(value: object, expected: str) -> bool:
    return {
        "null": value is None,
        "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "string": isinstance(value, str),
        "array": isinstance(value, list),
        "object": isinstance(value, dict),
    }.get(expected, False)


def _schema_matches(value: object, schema: object, root: dict, path: str) -> bool:
    try:
        _validate_schema_instance(value, schema, root, path)
    except ValueError:
        return False
    return True


def _resolve_schema_ref(root: dict, reference: str) -> object:
    if not reference.startswith("#/"):
        raise ValueError("treatment schema may only use local references")
    current: object = root
    for token in reference[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or token not in current:
            raise ValueError("treatment schema contains an unresolved local reference")
        current = current[token]
    return current


def _validate_schema_instance(value: object, schema: object, root: dict, path: str = "$") -> None:
    if schema is True: return
    if schema is False or not isinstance(schema, dict):
        raise ValueError(f"{path} is rejected by the treatment JSON Schema")
    if "$ref" in schema:
        _validate_schema_instance(value, _resolve_schema_ref(root, schema["$ref"]), root, path)
    for branch in schema.get("allOf", []):
        _validate_schema_instance(value, branch, root, path)
    if "anyOf" in schema and not any(_schema_matches(value, branch, root, path) for branch in schema["anyOf"]):
        raise ValueError(f"{path} does not match any allowed treatment schema shape")
    if "oneOf" in schema and sum(_schema_matches(value, branch, root, path) for branch in schema["oneOf"]) != 1:
        raise ValueError(f"{path} does not match exactly one treatment schema shape")
    if "not" in schema and _schema_matches(value, schema["not"], root, path):
        raise ValueError(f"{path} matches a prohibited treatment schema shape")
    if "if" in schema:
        branch = schema.get("then") if _schema_matches(value, schema["if"], root, path) else schema.get("else")
        if branch is not None: _validate_schema_instance(value, branch, root, path)
    if "const" in schema and not _same_json_value(value, schema["const"], path):
        raise ValueError(f"{path} does not match its treatment schema constant")
    if "enum" in schema and not any(_same_json_value(value, item, path) for item in schema["enum"]):
        raise ValueError(f"{path} is outside its treatment schema enum")
    if "type" in schema:
        expected = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_json_type_matches(value, item) for item in expected):
            raise ValueError(f"{path} has the wrong treatment schema type")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0): raise ValueError(f"{path} is shorter than allowed")
        if "pattern" in schema and re.search(schema["pattern"], value) is None: raise ValueError(f"{path} does not match its pattern")
        if schema.get("format") == "date-time": _validate_schema_timestamp(value, path)
    if isinstance(value, int) and not isinstance(value, bool) and "minimum" in schema and value < schema["minimum"]:
        raise ValueError(f"{path} is below its minimum")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0): raise ValueError(f"{path} has too few items")
        if schema.get("uniqueItems") and len({canonical_bytes(item) for item in value}) != len(value):
            raise ValueError(f"{path} must contain unique items")
        if isinstance(schema.get("items"), dict):
            for index, item in enumerate(value): _validate_schema_instance(item, schema["items"], root, f"{path}[{index}]")
    if isinstance(value, dict):
        missing = set(schema.get("required", [])) - set(value)
        if missing: raise ValueError(f"{path} is missing required treatment schema fields")
        properties = schema.get("properties", {})
        for index, (key, item) in enumerate(value.items()):
            if key in properties:
                _validate_schema_instance(item, properties[key], root, f"{path}.{key}")
            elif schema.get("additionalProperties") is False:
                raise ValueError(f"{path} contains an undeclared treatment schema field")
            elif isinstance(schema.get("additionalProperties"), dict):
                _validate_schema_instance(item, schema["additionalProperties"], root, f"{path}.<field:{index}>")


def _same_json_value(actual: object, expected: object, label: str) -> bool:
    try:
        return canonical_bytes(actual) == canonical_bytes(expected)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be canonical JSON") from exc


def _contains_ip_address(value: str) -> bool:
    for candidate in IP_CANDIDATE_RE.findall(value):
        try:
            ipaddress.ip_address(candidate)
        except ValueError:
            continue
        return True
    return False


def _validate_retained_strings(value: object, label: str = "treatment bundle",
                               *, reject_two_label_hostnames: bool = False) -> None:
    if isinstance(value, str):
        forbidden = (
            any(ord(char) < 32 for char in value)
            or (EVIDENCE_REF_RE.fullmatch(value) is None and ABSOLUTE_PATH_RE.search(value))
            or TRAVERSAL_RE.search(value)
            or REMOTE_RE.search(value)
            or CREDENTIAL_RE.search(value)
            or UNLABELED_CREDENTIAL_RE.search(value)
            or PII_RE.search(value)
            or HOSTNAME_RE.search(value)
            or reject_two_label_hostnames and REPLAY_HOSTNAME_RE.search(value)
            or INTERNAL_HOSTNAME_RE.search(value)
            or _contains_ip_address(value)
        )
        if forbidden:
            raise ValueError(f"{label} retains forbidden private or credential-bearing text")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_retained_strings(
                item, f"{label}[{index}]",
                reject_two_label_hostnames=reject_two_label_hostnames,
            )
    elif isinstance(value, dict):
        for index, (key, item) in enumerate(value.items()):
            _validate_retained_strings(
                key, f"{label} object key {index}",
                reject_two_label_hostnames=reject_two_label_hostnames,
            )
            _validate_retained_strings(
                item, f"{label} object value {index}",
                reject_two_label_hostnames=reject_two_label_hostnames,
            )

__all__ = [name for name in globals() if not name.startswith("__")]
