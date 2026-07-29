#!/usr/bin/env python3
"""Validator for the CAR-004 policy-control registry and its three frozen controls.

The committed schema document at
``tests/speckit-pro/layer6-efficiency/contracts-claude/policy-control-registry.schema.json``
is the single source of truth. This module drives every check *from* that
document rather than restating it, following the ``claude_trace_schema.py``
precedent — which cannot be reused directly because it is frozen CAR-003 code
bound at import to one hard-coded schema path (FR-005, research D1).

It also owns the shared fail-closed schema engine — ``load_contract``,
``validate_instance``, and :class:`ControlContractError` — which
``claude_control_comparison.py`` imports. The engine lives here rather than in a
module of its own for the same reason ``claude_successor_freeze.py`` owns
``canonical_json`` and ``record_digest`` for the whole program: it has exactly
two in-tree callers (research D1).

Every entrypoint is fail-closed: it raises on the first violation and never
returns a partial verdict. Standard library only — no third-party ``jsonschema``
(constitution principle II).
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

# Read-only import: one preimage rule governs every digest in the program, so
# neither the canonical serializer nor the record preimage is re-implemented here
# (research D3).
from claude_successor_freeze import canonical_json, record_digest

# Read-only import of the frozen plane derivation. That module publishes it as
# the single authority on which plane a failure code sits, so restating the
# partition here would author the agreement FR-010c.1 exists to check.
from claude_score_bundle import (
    SERVICE_REROUTE_DISPOSITION_REASON,
    SERVICE_REROUTE_FAILURE_CODE,
    failure_plane_for,
)


REPO_ROOT = Path(__file__).resolve().parents[4]
LAYER6_ROOT = REPO_ROOT / "tests" / "speckit-pro" / "layer6-efficiency"
CONTRACT_ROOT = LAYER6_ROOT / "contracts-claude"
FIXTURE_ROOT = LAYER6_ROOT / "fixtures-controls"
FROZEN_REGISTRY_SCHEMA_PATH = CONTRACT_ROOT / "policy-control-registry.schema.json"
FROZEN_REGISTRY_PATH = FIXTURE_ROOT / "policy-control-registry.json"

# FR-004 and SC-017: the only admissible reference form. Anything else leaves the
# owning document and is refused rather than dereferenced.
REF_PREFIX = "#/$defs/"

# FR-001 and SC-001: the control set is closed at three, one instance per kind.
CONTROL_KINDS = ("unpinned", "adaptive", "orchestration_changing")

# FR-030a: the identity's left-hand side is exactly these three ceilings — the
# ceilings on the three bounded members of the frozen raw token vector. Both cache
# ceilings bound diagnostics FR-016e.4 keeps out of it, so neither can join the
# sum; an identity that only balances once one is added therefore fails closed.
RAW_TOKEN_IDENTITY_SUMMANDS = (
    "max_input_tokens",
    "max_cached_input_tokens",
    "max_output_tokens",
)
RAW_TOKEN_CEILING_MEMBER = "raw_token_ceiling"
CACHE_DIAGNOSTIC_CEILINGS = ("max_cache_read_tokens", "max_cache_write_tokens_by_ttl_class")
CACHE_WRITE_TTL_CLASSES = ("ephemeral_5m", "ephemeral_1h")

# FR-030a and FR-034.6: every numeric bound carries its unit and its comparison
# direction, so category 6 of the twin-handoff record is derived rather than
# transcribed.
BOUND_MEMBERS = ("value", "unit", "direction")

_PATTERN_CACHE: dict[str, re.Pattern[str]] = {}


class ControlContractError(AssertionError):
    """Raised when an instance violates the CAR-004 policy-control contract."""


# --------------------------------------------------------------------------- #
# Shared fail-closed schema engine (imported by claude_control_comparison)      #
# --------------------------------------------------------------------------- #


def load_contract(path: Path) -> dict[str, Any]:
    """Read a committed contract document; raise if it is absent or malformed."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ControlContractError(f"contract document not readable: {path}") from exc
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ControlContractError(f"contract document is not valid JSON: {path}") from exc
    if not isinstance(document, dict):
        raise ControlContractError(f"contract document is not an object: {path}")
    return document


def validate_instance(instance: Any, schema: dict[str, Any], *, path: str = "") -> Any:
    """Validate ``instance`` against ``schema``, raising on the first violation.

    ``schema`` is the root document; every ``$ref`` is resolved against its own
    ``#/$defs/`` and a reference leaving the document fails closed (SC-017).
    """
    _validate(instance, schema, schema, path)
    return instance


def require_utc_timestamp(value: Any, context: str) -> None:
    """The ``format: date-time`` rule: a ``Z``-suffixed, zero-offset UTC instant."""
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ControlContractError(f"{context}: expected UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ControlContractError(f"{context}: invalid timestamp") from exc
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise ControlContractError(f"{context}: timestamp is not UTC")


def _compiled(pattern: str) -> re.Pattern[str]:
    cached = _PATTERN_CACHE.get(pattern)
    if cached is None:
        cached = re.compile(pattern)
        _PATTERN_CACHE[pattern] = cached
    return cached


def _same_value(left: Any, right: Any) -> bool:
    """Strict JSON equality, so ``True`` never satisfies an integer ``const``."""
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left == right
    if isinstance(left, list) or isinstance(right, list):
        return (
            isinstance(left, list)
            and isinstance(right, list)
            and len(left) == len(right)
            and all(_same_value(a, b) for a, b in zip(left, right))
        )
    if isinstance(left, dict) or isinstance(right, dict):
        return (
            isinstance(left, dict)
            and isinstance(right, dict)
            and left.keys() == right.keys()
            and all(_same_value(left[key], right[key]) for key in left)
        )
    return left == right


def _matches_type(instance: Any, type_name: str, path: str) -> bool:
    # ``bool`` is a subclass of ``int``; keep the two disjoint so a boolean never
    # satisfies an ``integer`` field and vice versa (fail-closed).
    if type_name == "null":
        return instance is None
    if type_name == "boolean":
        return isinstance(instance, bool)
    if type_name == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if type_name == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if type_name == "string":
        return isinstance(instance, str)
    if type_name == "object":
        return isinstance(instance, dict)
    if type_name == "array":
        return isinstance(instance, list)
    raise ControlContractError(f"{path}: schema declares unknown type {type_name!r}")


def _resolve_ref(ref: Any, root: dict[str, Any], path: str) -> dict[str, Any]:
    if not isinstance(ref, str) or not ref.startswith(REF_PREFIX):
        raise ControlContractError(
            f"{path}: reference {ref!r} resolves outside the document's own {REF_PREFIX}"
        )
    name = ref[len(REF_PREFIX):]
    definitions = root.get("$defs")
    if not isinstance(definitions, dict) or name not in definitions:
        raise ControlContractError(f"{path}: unknown local definition {name!r}")
    return definitions[name]


def _conforms(instance: Any, node: Any, root: dict[str, Any], path: str) -> bool:
    """Whether ``instance`` satisfies ``node``, for ``not`` / ``anyOf`` / ``if``."""
    try:
        _validate(instance, node, root, path)
    except ControlContractError:
        return False
    return True


def _child_path(path: str, key: str) -> str:
    return f"{path}.{key}" if path else key


def _validate_object(
    instance: dict[str, Any], node: dict[str, Any], root: dict[str, Any], path: str
) -> None:
    properties = node.get("properties", {})
    missing = set(node.get("required", ())) - set(instance)
    if missing:
        raise ControlContractError(f"{path}: missing required keys {sorted(missing)}")
    additional = node.get("additionalProperties")
    extra = sorted(set(instance) - set(properties))
    if additional is False and extra:
        raise ControlContractError(f"{path}: unexpected keys {extra}")
    minimum_properties = node.get("minProperties")
    if minimum_properties is not None and len(instance) < minimum_properties:
        raise ControlContractError(f"{path}: fewer than minProperties {minimum_properties}")
    maximum_properties = node.get("maxProperties")
    if maximum_properties is not None and len(instance) > maximum_properties:
        raise ControlContractError(f"{path}: more than maxProperties {maximum_properties}")
    names = node.get("propertyNames")
    if names is not None:
        for key in sorted(instance):
            _validate(key, names, root, f"{_child_path(path, key)} (property name)")
    for key, subschema in properties.items():
        if key in instance:
            _validate(instance[key], subschema, root, _child_path(path, key))
    # ``additionalProperties`` as a schema constrains every member ``properties``
    # did not name. Four of the frozen CAR-003 documents use this form, so
    # treating the keyword as boolean-only would drop those constraints.
    if isinstance(additional, dict):
        for key in extra:
            _validate(instance[key], additional, root, _child_path(path, key))


def _validate_string(instance: str, node: dict[str, Any], path: str) -> None:
    minimum_length = node.get("minLength")
    if minimum_length is not None and len(instance) < minimum_length:
        raise ControlContractError(f"{path}: shorter than minLength {minimum_length}")
    maximum_length = node.get("maxLength")
    if maximum_length is not None and len(instance) > maximum_length:
        raise ControlContractError(f"{path}: longer than maxLength {maximum_length}")
    pattern = node.get("pattern")
    if pattern is not None and not _compiled(pattern).fullmatch(instance):
        raise ControlContractError(f"{path}: {instance!r} does not match pattern {pattern}")
    if node.get("format") == "date-time":
        require_utc_timestamp(instance, path)


def _validate_array(
    instance: list[Any], node: dict[str, Any], root: dict[str, Any], path: str
) -> None:
    minimum_items = node.get("minItems")
    if minimum_items is not None and len(instance) < minimum_items:
        raise ControlContractError(f"{path}: fewer than minItems {minimum_items}")
    maximum_items = node.get("maxItems")
    if maximum_items is not None and len(instance) > maximum_items:
        raise ControlContractError(f"{path}: more than maxItems {maximum_items}")
    if node.get("uniqueItems") is True:
        serialized = [canonical_json(element) for element in instance]
        if len(set(serialized)) != len(serialized):
            raise ControlContractError(f"{path}: duplicate items under uniqueItems")
    items = node.get("items")
    if items is not None:
        for index, element in enumerate(instance):
            _validate(element, items, root, f"{path}[{index}]")


def _validate_number(instance: Any, node: dict[str, Any], path: str) -> None:
    minimum = node.get("minimum")
    if minimum is not None and instance < minimum:
        raise ControlContractError(f"{path}: below minimum {minimum}")
    maximum = node.get("maximum")
    if maximum is not None and instance > maximum:
        raise ControlContractError(f"{path}: above maximum {maximum}")
    exclusive_minimum = node.get("exclusiveMinimum")
    if exclusive_minimum is not None and instance <= exclusive_minimum:
        raise ControlContractError(f"{path}: not above exclusiveMinimum {exclusive_minimum}")
    exclusive_maximum = node.get("exclusiveMaximum")
    if exclusive_maximum is not None and instance >= exclusive_maximum:
        raise ControlContractError(f"{path}: not below exclusiveMaximum {exclusive_maximum}")


# Every keyword this engine understands, split by the role it plays. A keyword
# outside this set is refused rather than skipped: an ignored keyword and a
# satisfied one produce the same result, which is precisely the confusion a
# fail-closed engine may not permit. Teaching the engine a new keyword is the
# prerequisite for using it in a contract, never the other way round.
SUPPORTED_KEYWORDS = frozenset(
    {
        # Annotations. Carried by the documents, deliberately not enforced.
        "$schema", "$id", "$defs", "title", "description",
        # Reference and composition.
        "$ref", "allOf", "anyOf", "oneOf", "not", "if", "then", "else",
        # Assertions that apply whatever the instance type.
        "type", "const", "enum",
        # Objects.
        "properties", "required", "additionalProperties", "propertyNames",
        "minProperties", "maxProperties",
        # Arrays.
        "items", "minItems", "maxItems", "uniqueItems",
        # Strings.
        "minLength", "maxLength", "pattern", "format",
        # Numbers.
        "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
    }
)


def _validate(instance: Any, node: Any, root: dict[str, Any], path: str) -> None:
    """Recursively validate ``instance`` against one schema node (fail-closed)."""
    if not isinstance(node, dict):
        raise ControlContractError(f"{path}: schema node is not an object")

    unsupported = sorted(set(node) - SUPPORTED_KEYWORDS)
    if unsupported:
        raise ControlContractError(
            f"{path or '<root>'}: schema declares {unsupported}, which this engine does not "
            "implement; an unenforceable keyword is refused rather than ignored"
        )

    if "$ref" in node:
        _validate(instance, _resolve_ref(node["$ref"], root, path), root, path)

    if "type" in node:
        declared = node["type"]
        names = declared if isinstance(declared, list) else [declared]
        if not any(_matches_type(instance, name, path) for name in names):
            got = "null" if instance is None else type(instance).__name__
            raise ControlContractError(f"{path}: expected type {declared}, got {got}")
    if "const" in node and not _same_value(instance, node["const"]):
        raise ControlContractError(f"{path}: expected const {node['const']!r}, got {instance!r}")
    if "enum" in node and not any(_same_value(instance, member) for member in node["enum"]):
        raise ControlContractError(f"{path}: {instance!r} not in enum {node['enum']}")

    for index, branch in enumerate(node.get("allOf", ())):
        _validate(instance, branch, root, f"{path}[allOf {index}]")
    if "anyOf" in node and not any(
        _conforms(instance, branch, root, path) for branch in node["anyOf"]
    ):
        raise ControlContractError(f"{path}: no anyOf branch matched")
    if "oneOf" in node:
        matched = sum(
            1 for branch in node["oneOf"] if _conforms(instance, branch, root, path)
        )
        if matched != 1:
            raise ControlContractError(
                f"{path}: {matched} oneOf branches matched; exactly one must"
            )
    if "not" in node and _conforms(instance, node["not"], root, path):
        raise ControlContractError(f"{path}: matched a schema the document forbids")
    if "if" in node:
        taken = "then" if _conforms(instance, node["if"], root, path) else "else"
        if taken in node:
            _validate(instance, node[taken], root, path)

    # Type-specific keywords apply only to the matching runtime type, matching
    # JSON Schema semantics.
    if isinstance(instance, str):
        _validate_string(instance, node, path)
    elif isinstance(instance, bool):
        pass
    elif isinstance(instance, (int, float)):
        _validate_number(instance, node, path)
    elif isinstance(instance, list):
        _validate_array(instance, node, root, path)
    elif isinstance(instance, dict):
        _validate_object(instance, node, root, path)


# --------------------------------------------------------------------------- #
# Registry, content addressing, and closure at three                            #
# --------------------------------------------------------------------------- #

# The committed contract document is the single source of truth, parsed once.
REGISTRY_SCHEMA: dict[str, Any] = load_contract(FROZEN_REGISTRY_SCHEMA_PATH)


def control_digest(control: Mapping[str, Any]) -> str:
    """A control's content address: the frozen preimage over its own record.

    Only the record's own ``control_digest`` member leaves the preimage, so
    ``frozen_at`` and the declared order of every array — ``escalation_ladder``
    included — are inside it (FR-002, FR-002a, FR-011b).
    """
    return record_digest(control, digest_field="control_digest")


def assert_closed_at_three(registry: Mapping[str, Any]) -> None:
    """FR-001 and SC-001: three controls, one per kind. A fourth arm is refused."""
    controls = registry.get("controls")
    if not isinstance(controls, list) or len(controls) != len(CONTROL_KINDS):
        count = len(controls) if isinstance(controls, list) else "no"
        raise ControlContractError(
            f"the control set is closed at {len(CONTROL_KINDS)}; registry carries {count} controls"
        )
    kinds = [control.get("control_kind") for control in controls]
    if sorted(kinds, key=str) != sorted(CONTROL_KINDS):
        raise ControlContractError(
            f"expected one control per kind {list(CONTROL_KINDS)}, got {kinds}"
        )


def _bound(bounds: Mapping[str, Any], member: str, path: str) -> Mapping[str, Any]:
    entry = bounds.get(member)
    if not isinstance(entry, Mapping):
        raise ControlContractError(f"{path}: smoke bound {member!r} is missing")
    missing = [name for name in BOUND_MEMBERS if name not in entry]
    if missing:
        raise ControlContractError(f"{path}.{member}: bound is missing {missing}")
    return entry


def _validate_smoke_bounds(bounds: Any, path: str = "smoke_bounds") -> None:
    if not isinstance(bounds, Mapping):
        raise ControlContractError(f"{path}: smoke bounds are missing")

    write_classes = bounds.get("max_cache_write_tokens_by_ttl_class")
    if not isinstance(write_classes, Mapping):
        raise ControlContractError(f"{path}: max_cache_write_tokens_by_ttl_class is missing")
    for ttl_class in CACHE_WRITE_TTL_CLASSES:
        _bound(write_classes, ttl_class, f"{path}.max_cache_write_tokens_by_ttl_class")
    for member in bounds:
        if member != "max_cache_write_tokens_by_ttl_class":
            _bound(bounds, member, path)
    # Both cache diagnostics carry a frozen ceiling of their own and stay outside
    # the identity below.
    _bound(bounds, "max_cache_read_tokens", path)

    total = sum(_bound(bounds, member, path)["value"] for member in RAW_TOKEN_IDENTITY_SUMMANDS)
    ceiling = _bound(bounds, RAW_TOKEN_CEILING_MEMBER, path)["value"]
    if total != ceiling:
        raise ControlContractError(
            f"{path}: {' + '.join(RAW_TOKEN_IDENTITY_SUMMANDS)} == {total}, but "
            f"{RAW_TOKEN_CEILING_MEMBER} is {ceiling}; the identity is read over those three "
            f"bounded raw-token ceilings alone and never admits {list(CACHE_DIAGNOSTIC_CEILINGS)}"
        )


def validate_registry(registry: Mapping[str, Any]) -> Mapping[str, Any]:
    """Fail-closed registry semantics: identity, closure, and the token identity."""
    require_utc_timestamp(registry.get("frozen_at"), "frozen_at")
    # FR-005a and SC-018: recompute every bound document's byte digest here, on
    # the path every consumer actually takes. A guard that only the unit test
    # calls does not guard anything.
    verify_car_003_bindings(registry)
    assert_closed_at_three(registry)

    for index, control in enumerate(registry["controls"]):
        path = f"controls[{index}]"
        require_utc_timestamp(control.get("frozen_at"), f"{path}.frozen_at")
        recomputed = control_digest(control)
        if control.get("control_digest") != recomputed:
            raise ControlContractError(
                f"{path}.control_digest does not recompute: recorded "
                f"{control.get('control_digest')!r}, recomputed {recomputed!r}"
            )

    _validate_smoke_bounds(registry.get("smoke_bounds"))
    validate_control_specializations(registry)

    recomputed = record_digest(registry, digest_field="registry_digest")
    if registry.get("registry_digest") != recomputed:
        raise ControlContractError(
            f"registry_digest does not recompute: recorded {registry.get('registry_digest')!r}, "
            f"recomputed {recomputed!r}"
        )
    return registry


# --------------------------------------------------------------------------- #
# Additive-only bindings into the frozen CAR-003 contracts                      #
# --------------------------------------------------------------------------- #


def document_bytes_digest(path: Path) -> str:
    """FR-005a: the SHA-256 of a document's **committed bytes**.

    Deliberately distinct from the FR-002a record preimage, which digests a
    record's canonical JSON: a bound document is verified as bytes, so a reformat
    that preserves the parsed value still moves the digest and fails closed.
    """
    try:
        payload = Path(path).read_bytes()
    except OSError as exc:
        raise ControlContractError(f"bound document not readable: {path}") from exc
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _committed_documents_by_id() -> dict[str, Path]:
    """Index the committed contract documents by the ``$id`` each declares."""
    index: dict[str, Path] = {}
    for path in sorted(CONTRACT_ROOT.glob("*.schema.json")):
        identifier = load_contract(path).get("$id")
        if isinstance(identifier, str):
            index[identifier] = path
    return index


def verify_car_003_bindings(document: Mapping[str, Any]) -> None:
    """FR-004, FR-005, FR-005a: every reference is a data-level ``{id, digest}``.

    A binding is never a ``$ref``: the recorded digest is recomputed from the
    bound document's committed bytes and a drift on either side fails closed
    rather than passing unnoticed (SC-018).
    """
    bindings = document.get("car_003_bindings")
    if not isinstance(bindings, list) or not bindings:
        raise ControlContractError("car_003_bindings is missing or declares no binding")
    index = _committed_documents_by_id()
    for position, binding in enumerate(bindings):
        path = f"car_003_bindings[{position}]"
        if not isinstance(binding, Mapping) or set(binding) != {"id", "digest"}:
            raise ControlContractError(f"{path}: a binding is exactly {{id, digest}}")
        bound = index.get(binding["id"])
        if bound is None:
            raise ControlContractError(
                f"{path}: {binding['id']!r} names no committed contract document"
            )
        recomputed = document_bytes_digest(bound)
        if binding["digest"] != recomputed:
            raise ControlContractError(
                f"{path}: recorded digest {binding['digest']!r} does not match the committed "
                f"bytes of {bound.name} ({recomputed!r})"
            )


# --------------------------------------------------------------------------- #
# Unpinned control (FR-006, FR-007)                                             #
# --------------------------------------------------------------------------- #

# FR-006: the repository carries two frozen documents a reader can reach for
# "the environment contract". The one every CAR-004 requirement means is
# identified by the members it declares rather than by its name: the shared
# runtime document shapes its parent session differently and enumerates
# ``chatgpt_subscription | api_key``.
CLAUDE_ENVIRONMENT_CONTRACT_MEMBERS = (
    "authentication_mode",
    "claude_code_subagent_model_unset",
    "parent_session_effort",
    "parent_session_model",
)
CLAUDE_AUTHENTICATION_MODES = ("api_key", "subscription")


def _is_claude_environment_contract(node: Any) -> bool:
    if not isinstance(node, dict):
        return False
    properties = node.get("properties")
    if not isinstance(properties, dict):
        return False
    if any(member not in properties for member in CLAUDE_ENVIRONMENT_CONTRACT_MEMBERS):
        return False
    modes = properties["authentication_mode"].get("enum")
    return isinstance(modes, list) and sorted(modes) == sorted(CLAUDE_AUTHENTICATION_MODES)


def _find_claude_environment_contract(document: Any) -> dict[str, Any] | None:
    stack: list[Any] = [document]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            if _is_claude_environment_contract(node.get("environment_contract")):
                return node["environment_contract"]
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return None


def pinned_parent_document() -> tuple[str, dict[str, Any]]:
    """FR-006: the committed document whose Claude-side environment contract pins the parent.

    Returns its ``$id`` and the ``environment_contract`` node itself, so the pin's
    admissible effort is read from the bound document rather than transcribed.
    """
    for identifier, path in sorted(_committed_documents_by_id().items()):
        node = _find_claude_environment_contract(load_contract(path))
        if node is not None:
            return identifier, node
    raise ControlContractError(
        "no committed contract document declares the Claude-side environment_contract object"
    )


def validate_unpinned_control(control: Mapping[str, Any]) -> None:
    """FR-006 and FR-007: one arm, inherited resolution, and a bound parent pin."""
    spec = control.get("unpinned")
    if not isinstance(spec, Mapping):
        raise ControlContractError("the unpinned control declares no unpinned specialization")
    if not _same_value(spec.get("arm_count"), 1):
        raise ControlContractError(
            f"arm_count is frozen at 1; a different pin is a new control version rather than a "
            f"second concurrent arm, but the control declares {spec.get('arm_count')!r}"
        )
    if spec.get("model_resolution") != "inherit":
        raise ControlContractError(
            f"model_resolution is frozen at 'inherit' so agents ride the session model; the "
            f"control declares {spec.get('model_resolution')!r}"
        )

    identifier, node = pinned_parent_document()
    binding = spec.get("pinned_parent_binding")
    if not isinstance(binding, Mapping) or set(binding) != {"id", "digest"}:
        raise ControlContractError("pinned_parent_binding is exactly {id, digest}")
    if binding["id"] != identifier:
        raise ControlContractError(
            f"pinned_parent_binding names {binding['id']!r}; the pin is read from {identifier!r}, "
            "the document carrying the Claude-side environment_contract object"
        )
    recomputed = document_bytes_digest(_committed_documents_by_id()[identifier])
    if binding["digest"] != recomputed:
        raise ControlContractError(
            f"pinned_parent_binding digest {binding['digest']!r} does not match the committed "
            f"bytes of the bound document ({recomputed!r})"
        )

    admitted_efforts = node["properties"]["parent_session_effort"]["enum"]
    if spec.get("pinned_parent_effort") not in admitted_efforts:
        raise ControlContractError(
            f"pinned_parent_effort {spec.get('pinned_parent_effort')!r} is not a member of the "
            f"bound document's own effort enum {list(admitted_efforts)}"
        )
    model = spec.get("pinned_parent_model")
    if not isinstance(model, str) or not model:
        raise ControlContractError(f"pinned_parent_model is a recorded string, not {model!r}")


# --------------------------------------------------------------------------- #
# Adaptive control: signal maps and row resolution (FR-008 – FR-010c, FR-015a)  #
# --------------------------------------------------------------------------- #

FROZEN_SCORE_BUNDLE_SCHEMA_PATH = CONTRACT_ROOT / "score-bundle.schema.json"
SCORE_BUNDLE_SCHEMA: dict[str, Any] = load_contract(FROZEN_SCORE_BUNDLE_SCHEMA_PATH)

# Read from the committed bytes, never transcribed: FR-010a only fails closed on
# an upstream membership change while both sides read the same source.
FROZEN_TERMINAL_STATES: tuple[str, ...] = tuple(
    SCORE_BUNDLE_SCHEMA["properties"]["resource_vector"]["properties"]["terminal_state"]["enum"]
)
FROZEN_FAILURE_PLANES: tuple[str, ...] = tuple(
    SCORE_BUNDLE_SCHEMA["properties"]["failure_plane"]["enum"]
)
FROZEN_FAILURE_CODES: tuple[str, ...] = tuple(
    SCORE_BUNDLE_SCHEMA["properties"]["failure_code"]["enum"]
)
FROZEN_PARETO_DIMENSIONS: tuple[str, ...] = tuple(
    SCORE_BUNDLE_SCHEMA["properties"]["resource_vector"]["required"]
)

POLICY_RESPONSES = ("escalate", "hold", "non_scorable")
NONE_SENTINEL = "none"
CLEAN_TERMINAL_STATE = "completed"

# FR-010b: the closed source set, which must cover every source FR-008 admits.
SIGNAL_SOURCES = (
    "failure_code",
    "failure_plane",
    "retry_count",
    "budget_threshold",
    "terminal_state",
)
# Always valued, therefore ranked last: any higher rank would make every source
# below it unreachable, which is the outcome FR-010b fails closed on.
ALWAYS_VALUED_SOURCE = "terminal_state"

SIGNAL_MAP_ENUMS = (
    ("terminal_state_response", FROZEN_TERMINAL_STATES),
    ("failure_plane_response", FROZEN_FAILURE_PLANES),
    ("failure_code_response", FROZEN_FAILURE_CODES),
)


def candidate_code_for(terminal_state: str) -> str:
    """FR-010c.2: the frozen candidate-plane pairing, derived rather than transcribed.

    ``claude_score_bundle`` publishes no terminal-state-keyed map and none may be
    added to it, so the pairing is read from the frozen ``failure_code`` enum
    itself. A derived code the enum does not carry fails the check closed.
    """
    derived = f"candidate_{terminal_state}"
    if derived not in FROZEN_FAILURE_CODES:
        raise ControlContractError(
            f"the candidate-plane pairing derives {derived!r} for terminal state "
            f"{terminal_state!r}, which the frozen failure_code enum does not carry"
        )
    return derived


def _adaptive(control: Mapping[str, Any]) -> Mapping[str, Any]:
    specialization = control.get("adaptive")
    if not isinstance(specialization, Mapping):
        raise ControlContractError("the adaptive control declares no adaptive specialization")
    return specialization


def _require_set_equal(mapping: Any, enum: tuple[str, ...], member: str) -> Mapping[str, Any]:
    if not isinstance(mapping, Mapping):
        raise ControlContractError(f"{member} is missing")
    unmapped = sorted(set(enum) - set(mapping))
    orphaned = sorted(set(mapping) - set(enum))
    if unmapped or orphaned:
        raise ControlContractError(
            f"{member} is not set-equal to its frozen enum: unmapped {unmapped}, "
            f"orphaned {orphaned}"
        )
    for signal, response in mapping.items():
        if response not in POLICY_RESPONSES:
            raise ControlContractError(
                f"{member}[{signal!r}] resolves to {response!r}, outside the closed policy "
                f"response set {list(POLICY_RESPONSES)}"
            )
    return mapping


def validate_signal_maps(control: Mapping[str, Any]) -> None:
    """FR-010, FR-010a, FR-010b, FR-010c: total, single-valued, and consistent."""
    adaptive = _adaptive(control)
    maps = {
        member: _require_set_equal(adaptive.get(member), enum, member)
        for member, enum in SIGNAL_MAP_ENUMS
    }

    precedence = adaptive.get("signal_precedence")
    if not isinstance(precedence, list) or sorted(precedence) != sorted(SIGNAL_SOURCES):
        raise ControlContractError(
            f"signal_precedence must be an ordering of the closed source set "
            f"{list(SIGNAL_SOURCES)}; the control declares {precedence!r}"
        )
    if precedence[-1] != ALWAYS_VALUED_SOURCE:
        raise ControlContractError(
            f"{ALWAYS_VALUED_SOURCE!r} is always valued and must rank last; ranking it at "
            f"position {precedence.index(ALWAYS_VALUED_SOURCE)} leaves every lower source "
            "unreachable"
        )
    if not isinstance(adaptive.get("retry_count_response"), Mapping):
        raise ControlContractError("retry_count holds a rank but declares no mapped response")
    # FR-012a.4: the de-escalation floor is what the streak is compared against,
    # so a control missing it is incomplete here rather than at the comparison.
    threshold = adaptive.get("de_escalation_clean_pass_threshold")
    if isinstance(threshold, bool) or not isinstance(threshold, int) or threshold < 1:
        raise ControlContractError(
            f"de_escalation_clean_pass_threshold is a whole count of clean passes, "
            f"not {threshold!r}"
        )
    triggers = adaptive.get("budget_triggers")
    if not isinstance(triggers, list) or not triggers:
        raise ControlContractError("budget_threshold holds a rank but declares no trigger")
    for position, trigger in enumerate(triggers):
        if trigger.get("response") not in POLICY_RESPONSES:
            raise ControlContractError(
                f"budget_triggers[{position}] resolves to {trigger.get('response')!r}, outside "
                f"the closed policy response set"
            )

    code_map = maps["failure_code_response"]
    plane_map = maps["failure_plane_response"]
    terminal_map = maps["terminal_state_response"]

    # FR-010c.1: the frozen contract derives the plane from the code, so a plane
    # carrying a response its own codes disagree with is unreachable.
    for code, response in code_map.items():
        plane = failure_plane_for(code)
        if plane_map[plane] != response:
            raise ControlContractError(
                f"failure_plane_response[{plane!r}] is {plane_map[plane]!r} while "
                f"failure_code_response[{code!r}] on that plane is {response!r}"
            )

    # FR-010c.2: each non-completed terminal state agrees with its paired code.
    for state, response in terminal_map.items():
        if state == CLEAN_TERMINAL_STATE:
            continue
        paired = candidate_code_for(state)
        if code_map[paired] != response:
            raise ControlContractError(
                f"terminal_state_response[{state!r}] is {response!r} while its paired "
                f"failure_code_response[{paired!r}] is {code_map[paired]!r}"
            )


def _threshold_met(entry: Mapping[str, Any], observed: Any) -> bool:
    if observed is None:
        return False
    direction = entry.get("direction")
    if direction == "at_or_above":
        return observed >= entry["threshold"]
    if direction == "at_or_below":
        return observed <= entry["threshold"]
    raise ControlContractError(f"{direction!r} is not a declared comparison direction")


def resolve_response(control: Mapping[str, Any], row: Mapping[str, Any]) -> str:
    """FR-010b: the response of the first ranked source whose value is not ``none``."""
    adaptive = _adaptive(control)
    enum_sources = {
        "failure_code": ("failure_code_response", row.get("failure_code", NONE_SENTINEL)),
        "failure_plane": ("failure_plane_response", row.get("failure_plane", NONE_SENTINEL)),
        "terminal_state": ("terminal_state_response", row.get("terminal_state")),
    }
    for source in adaptive["signal_precedence"]:
        if source in enum_sources:
            member, value = enum_sources[source]
            mapping = adaptive[member]
            if value not in mapping:
                raise ControlContractError(
                    f"row {source} {value!r} is not a member of {member}; the map is total over "
                    "its frozen enum, so an unmapped signal fails closed"
                )
            if source == ALWAYS_VALUED_SOURCE or value != NONE_SENTINEL:
                return mapping[value]
        elif source == "retry_count":
            entry = adaptive["retry_count_response"]
            if _threshold_met(entry, row.get("retries", 0)):
                return entry["response"]
        elif source == "budget_threshold":
            observations = row.get("budget_observations", {})
            for trigger in adaptive["budget_triggers"]:
                if _threshold_met(trigger, observations.get(trigger["member"])):
                    return trigger["response"]
        else:
            raise ControlContractError(f"{source!r} is not a member of the closed source set")
    raise ControlContractError("no ranked source resolved the row")


# --------------------------------------------------------------------------- #
# Adaptive control: the escalation ladder (FR-011, FR-011a, FR-011b, FR-013)    #
# --------------------------------------------------------------------------- #

FROZEN_FREEZE_SCHEMA_PATH = CONTRACT_ROOT / "successor-capability-freeze.schema.json"

# FR-011a.3: the closed ordered effort ladder, read from the freeze schema's own
# tuple definition rather than restated, so a within-model order is derived from
# the same bytes the freeze validates against.
FROZEN_EFFORT_LADDER: tuple[str, ...] = tuple(
    load_contract(FROZEN_FREEZE_SCHEMA_PATH)["$defs"]["tuple"]["properties"]["effort"]["enum"]
)


def _admitted_routes(freeze: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    admitted = freeze.get("admitted_tuples")
    if not isinstance(admitted, list) or not admitted:
        raise ControlContractError("the bound freeze declares no admitted_tuples")
    routes: dict[str, Mapping[str, Any]] = {}
    for entry in admitted:
        route = entry.get("candidate_route_id")
        if route in routes:
            raise ControlContractError(f"the bound freeze admits {route!r} more than once")
        if entry.get("effort") not in FROZEN_EFFORT_LADDER:
            raise ControlContractError(
                f"admitted tuple {route!r} declares effort {entry.get('effort')!r}, outside the "
                f"frozen ladder {list(FROZEN_EFFORT_LADDER)}"
            )
        routes[route] = entry
    return routes


def validate_escalation_ladder(control: Mapping[str, Any], freeze: Mapping[str, Any]) -> None:
    """FR-011a's four well-formedness rules, all fail-closed."""
    adaptive = _adaptive(control)

    # 1. Binding — exactly one freeze, by identifier and digest together.
    for member in ("candidate_freeze_id", "freeze_digest"):
        if adaptive.get(member) != freeze.get(member):
            raise ControlContractError(
                f"the control binds {member} {adaptive.get(member)!r} but the freeze under "
                f"validation records {freeze.get(member)!r}"
            )

    routes = _admitted_routes(freeze)
    ladder = adaptive.get("escalation_ladder")
    if not isinstance(ladder, list) or not ladder:
        raise ControlContractError("escalation_ladder is missing or declares no entry")

    # 2. Totality — a permutation of the admitted set: no duplicate, no omission.
    duplicated = sorted({route for route in ladder if ladder.count(route) > 1})
    if duplicated:
        raise ControlContractError(f"escalation_ladder repeats {duplicated}")
    unadmitted = sorted(set(ladder) - set(routes))
    omitted = sorted(set(routes) - set(ladder))
    if unadmitted or omitted:
        raise ControlContractError(
            f"escalation_ladder is not a permutation of the bound freeze's admitted set: "
            f"unadmitted {unadmitted}, omitted {omitted}. A route that must be unreachable is "
            "removed at the freeze through excluded_tuples, never by omission here"
        )

    # 3. Within-model order is derived from the frozen effort ladder.
    for position, route in enumerate(ladder):
        for later_route in ladder[position + 1:]:
            earlier, later = routes[route], routes[later_route]
            if earlier["model"] != later["model"]:
                continue
            if FROZEN_EFFORT_LADDER.index(earlier["effort"]) >= FROZEN_EFFORT_LADDER.index(
                later["effort"]
            ):
                raise ControlContractError(
                    f"{route!r} ({earlier['effort']}) is ranked below {later_route!r} "
                    f"({later['effort']}) on model {earlier['model']!r}, contradicting the frozen "
                    f"effort ladder {list(FROZEN_EFFORT_LADDER)}"
                )

    # 4. Cross-model order is authored, one non-empty rationale per step.
    rationales = adaptive.get("escalation_ladder_rationales")
    if not isinstance(rationales, list):
        raise ControlContractError("escalation_ladder_rationales is missing")
    recorded = {(entry["from_route"], entry["to_route"]): entry["rationale"] for entry in rationales}
    cross_model_steps: set[tuple[str, str]] = set()
    for position in range(len(ladder) - 1):
        step = (ladder[position], ladder[position + 1])
        if routes[step[0]]["model"] == routes[step[1]]["model"]:
            continue
        cross_model_steps.add(step)
        rationale = recorded.get(step)
        if not isinstance(rationale, str) or not rationale.strip():
            raise ControlContractError(
                f"the cross-model step {step[0]!r} -> {step[1]!r} records no rationale; no rule "
                "may derive cross-model rank from a model identifier"
            )
    unmatched = sorted(set(recorded) - cross_model_steps)
    if unmatched:
        raise ControlContractError(
            f"escalation_ladder_rationales records {unmatched}, which the ladder does not step"
        )


def _ladder(control: Mapping[str, Any]) -> list[str]:
    ladder = _adaptive(control).get("escalation_ladder")
    if not isinstance(ladder, list) or not ladder:
        raise ControlContractError("escalation_ladder is missing or declares no entry")
    return ladder


def _ladder_position(control: Mapping[str, Any], route_id: str) -> int:
    ladder = _ladder(control)
    if route_id not in ladder:
        # FR-013: a route outside the frozen set is unreachable by construction.
        # Returning None here would make an off-ladder route indistinguishable
        # from the ceiling, which is the "merely discouraged" reading FR-013
        # refuses; the contract's "never raises" governs the ceiling and floor.
        raise ControlContractError(f"{route_id!r} is not an entry on the frozen escalation ladder")
    return ladder.index(route_id)


def next_route(control: Mapping[str, Any], current_route_id: str) -> str | None:
    """FR-011 and FR-011b: index ``i + 1``, or ``None`` at the ceiling — no wrap-around."""
    ladder = _ladder(control)
    position = _ladder_position(control, current_route_id)
    return ladder[position + 1] if position + 1 < len(ladder) else None


def previous_route(control: Mapping[str, Any], current_route_id: str) -> str | None:
    """FR-012a.5: index ``i - 1``, or ``None`` at the floor — no wrap-around."""
    ladder = _ladder(control)
    position = _ladder_position(control, current_route_id)
    return ladder[position - 1] if position > 0 else None


# --------------------------------------------------------------------------- #
# Adaptive control: clean-pass streak accounting (FR-012, FR-012a)              #
# --------------------------------------------------------------------------- #


def _is_clean_pass(control: Mapping[str, Any], objective: Mapping[str, Any]) -> bool:
    """FR-012a.1: measured against the control's own declared definition."""
    adaptive = _adaptive(control)
    declared = adaptive.get("clean_pass_definition")
    if not isinstance(declared, Mapping):
        raise ControlContractError("clean_pass_definition is missing")
    # FR-012a.2: an objective in which the policy escalated is never clean, so
    # the run that licenses a step down is measured at the route it moved to.
    if objective.get("escalated"):
        return False
    if objective.get("terminal_state") != declared["terminal_state"]:
        return False
    if objective.get("failure_code", NONE_SENTINEL) != declared["failure_code"]:
        return False
    if objective.get("retries", 0) > declared["max_retries"]:
        return False
    # The bar is the declared trigger, not a breach: a trigger that fired is the
    # same threshold the policy escalates on.
    observations = objective.get("budget_observations", {})
    for trigger in adaptive["budget_triggers"]:
        if _threshold_met(trigger, observations.get(trigger["member"])):
            return False
    return True


def advance_clean_streak(
    control: Mapping[str, Any], state: Mapping[str, Any], objective: Mapping[str, Any]
) -> dict[str, Any]:
    """Carry the streak across one objective boundary and evaluate de-escalation.

    ``state`` carries the ladder position the policy holds at the boundary — the
    route it moved to if it escalated inside the objective — plus the streak.
    De-escalation is evaluated here and nowhere else, which is what keeps FR-012's
    "never mid-objective" true by construction.
    """
    adaptive = _adaptive(control)
    route = state.get("current_route_id")
    _ladder_position(control, route)
    streak = state.get("clean_streak", 0)
    outcome: dict[str, Any] = {
        "current_route_id": route,
        "clean_streak": streak,
        "clean_pass": False,
        "excluded": False,
        "de_escalation_evaluated": False,
        "de_escalated": False,
    }

    # FR-012a.3: the exclusion outranks the reset-on-non-clean rule, so it is
    # read before anything else about the row.
    if resolve_response(control, objective) == "non_scorable":
        outcome["excluded"] = True
        return outcome

    clean = _is_clean_pass(control, objective)
    outcome["clean_pass"] = clean
    streak = streak + 1 if clean else 0

    threshold = adaptive.get("de_escalation_clean_pass_threshold")
    # A control that declares no threshold cannot be compared against one. Saying
    # so here keeps the failure in this module's currency instead of surfacing as
    # a bare ``int >= None`` TypeError from the comparison below.
    if isinstance(threshold, bool) or not isinstance(threshold, int) or threshold < 1:
        raise ControlContractError(
            f"the adaptive control declares de_escalation_clean_pass_threshold={threshold!r}; "
            "the streak is compared against a whole count of clean passes"
        )
    if streak >= threshold:
        outcome["de_escalation_evaluated"] = True
        target = previous_route(control, route)
        if target is not None:
            outcome["current_route_id"] = target
            outcome["de_escalated"] = True
        # FR-012a.4 and FR-012a.5: the counter resets whether or not a step
        # occurred, so the floor cannot idle holding a spent streak.
        streak = 0

    outcome["clean_streak"] = streak
    return outcome


# --------------------------------------------------------------------------- #
# Bound scope, breach outcomes, and the frozen reroute (FR-014, FR-014a, FR-015a)#
# --------------------------------------------------------------------------- #


def _bound_declaration(control: Mapping[str, Any], member: str) -> Mapping[str, Any]:
    contract = control.get("execution_contract")
    if not isinstance(contract, Mapping):
        raise ControlContractError("the control declares no execution_contract")
    declared = contract.get(member)
    if not isinstance(declared, Mapping):
        raise ControlContractError(f"the execution contract declares no {member}")
    return declared


def evaluate_bounds(
    control: Mapping[str, Any], objective: Mapping[str, Any]
) -> dict[str, Any]:
    """FR-014a: read both bounds over their declared scope and name the breach outcome."""
    retry_bounds = _bound_declaration(control, "retry_bounds")
    cancellation_bounds = _bound_declaration(control, "cancellation_bounds")
    scopes = {retry_bounds.get("counted_over"), cancellation_bounds.get("counted_over")}
    if len(scopes) != 1:
        raise ControlContractError(
            f"both bounds are counted over one scope; the control declares {sorted(scopes, key=str)}"
        )
    declared_scope = scopes.pop()
    if objective.get("counted_over") != declared_scope:
        raise ControlContractError(
            f"the objective is counted over {objective.get('counted_over')!r} while the control "
            f"declares {declared_scope!r}"
        )

    attempts = objective.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        raise ControlContractError("the objective records no attempt to count")
    retries = 0
    duration_ms = 0
    for position, entry in enumerate(attempts):
        if not isinstance(entry, Mapping):
            raise ControlContractError(f"attempts[{position}] is not an attempt record")
        if entry.get("counter_reset_on_escalation"):
            raise ControlContractError(
                f"attempts[{position}] resets a counter on escalation; FR-014a.1 spans every "
                "attempt and every route, so a control cannot buy extra attempts by stepping up"
            )
        # Both counters are read explicitly rather than indexed: an attempt that
        # recorded neither must fail closed in this module's own currency, not as
        # a bare KeyError that escapes every ``except ControlContractError`` the
        # fail-closed design routes callers through.
        for member in ("retries", "duration_ms"):
            value = entry.get(member)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ControlContractError(
                    f"attempts[{position}].{member} is a whole count over the attempt, "
                    f"not {value!r}"
                )
        retries += entry["retries"]
        duration_ms += entry["duration_ms"]

    reading: dict[str, Any] = {
        "counted_over": declared_scope,
        "retries": retries,
        "duration_ms": duration_ms,
        "retry_bound_breached": retries > retry_bounds["max_retries"],
        "cancellation_bound_breached": duration_ms > cancellation_bounds["max_duration_ms"],
        "terminal_state": None,
        "failure_code": None,
    }

    # Both bounds breached records the more severe frozen state, the same
    # fail-safe reading FR-014a applies when it refuses `timed_out`: a doubly
    # breached run must not fold cleaner than a singly breached one.
    breach = None
    if reading["cancellation_bound_breached"]:
        breach = cancellation_bounds["on_breach"]
    elif reading["retry_bound_breached"]:
        breach = retry_bounds["on_breach"]

    if breach is not None:
        paired = candidate_code_for(breach["terminal_state"])
        if breach["failure_code"] != paired:
            raise ControlContractError(
                f"the declared breach pairs {breach['terminal_state']!r} with "
                f"{breach['failure_code']!r}; the frozen candidate-plane pairing is {paired!r}"
            )
        reading["terminal_state"] = breach["terminal_state"]
        reading["failure_code"] = breach["failure_code"]

    recorded = objective.get("recorded_outcome")
    if recorded is not None:
        if breach is None:
            raise ControlContractError(
                "the objective records a breach outcome while staying inside both bounds"
            )
        if (recorded.get("terminal_state"), recorded.get("failure_code")) != (
            reading["terminal_state"],
            reading["failure_code"],
        ):
            raise ControlContractError(
                f"the objective records {recorded!r}; the declared breach outcome is "
                f"{{'terminal_state': {reading['terminal_state']!r}, "
                f"'failure_code': {reading['failure_code']!r}}}"
            )
    return reading


def classify_service_reroute(
    control: Mapping[str, Any], row: Mapping[str, Any]
) -> dict[str, Any]:
    """FR-015 and FR-015a: the frozen observable, and what it may not spend."""
    is_reroute = row.get("failure_code") == SERVICE_REROUTE_FAILURE_CODE
    classified: dict[str, Any] = {
        "service_reroute": is_reroute,
        "response": None,
        "failure_code": SERVICE_REROUTE_FAILURE_CODE if is_reroute else row.get("failure_code"),
        "failure_plane": None,
        "disposition_reason": None,
        "escalation_allowance_spent": None,
        "ladder_position_changed": None,
        "unit_non_scorable": is_reroute,
    }
    if not is_reroute:
        return classified

    plane = failure_plane_for(SERVICE_REROUTE_FAILURE_CODE)
    if row.get("failure_plane") not in (None, plane):
        raise ControlContractError(
            f"the row records failure_plane {row.get('failure_plane')!r}; the frozen contract "
            f"derives {plane!r} from the reroute code"
        )
    response = resolve_response(control, row)
    if response != "non_scorable":
        raise ControlContractError(
            f"a platform-initiated reroute resolves {response!r}; FR-015 fixes it at "
            "'non_scorable' so it can never be recorded or counted as a policy escalation"
        )
    classified.update(
        response=response,
        failure_plane=plane,
        disposition_reason=SERVICE_REROUTE_DISPOSITION_REASON,
        escalation_allowance_spent=False,
        ladder_position_changed=False,
    )
    return classified


# --------------------------------------------------------------------------- #
# Orchestration-changing control: the parent-plus-children fold                 #
# (FR-016, FR-016a, FR-016b, FR-016c, FR-016d.3)                                #
# --------------------------------------------------------------------------- #

ADDITIVE_RULE = "sum"
SEVERITY_FOLD_RULE = "worst_wins_by_severity"
PARENT_ORACLE_RULE = "parent_objective_oracle"
TOPOLOGY_DESCRIPTOR_MEMBERS = ("child_shape", "fan_out", "topology_id")

# FR-016d.1: the spawn graph belongs to the **shared treatment-record contract**,
# which publishes it as a required member of every treatment trace. It is never
# read out of the CAR-002 Claude trace contract, which carries only a nullable
# parent-session configuration string and no spawn structure at all. The member
# names are read from that contract so a rename there fails the check closed.
SHARED_CONTRACT_ROOT = LAYER6_ROOT / "contracts"
FROZEN_TREATMENT_RECORD_SCHEMA_PATH = SHARED_CONTRACT_ROOT / "treatment-record.schema.json"
PARENT_CHILD_GRAPH_MEMBERS: tuple[str, ...] = tuple(
    load_contract(FROZEN_TREATMENT_RECORD_SCHEMA_PATH)["$defs"]["parentChildGraph"]["required"]
)

# FR-016e.1: the frozen four-member raw token vector, deliberately not the frozen
# eight-dimension Pareto vector. Both sets are read from committed bytes so
# FR-016's two phrases resolve to two named member sets rather than to one word.
FROZEN_RAW_TOKEN_MEMBERS: tuple[str, ...] = tuple(
    load_contract(FROZEN_TREATMENT_RECORD_SCHEMA_PATH)["$defs"]["rawTokenVector"]["required"]
)
# FR-016e.2 and FR-030b.2: summed and reported under no ceiling, so it is not an
# input to the quantity the raw_token_ceiling is read against.
UNBOUNDED_RAW_TOKEN_MEMBER = "reasoning_output_tokens"
RAW_TOKEN_CEILING_QUANTITY_MEMBERS: tuple[str, ...] = tuple(
    member for member in FROZEN_RAW_TOKEN_MEMBERS if member != UNBOUNDED_RAW_TOKEN_MEMBER
)

FROZEN_ADDITIVE_RECORDS_SCHEMA_PATH = CONTRACT_ROOT / "car-003-additive-records.schema.json"
_CACHE_DIAGNOSTIC = load_contract(FROZEN_ADDITIVE_RECORDS_SCHEMA_PATH)["$defs"][
    "cacheDiagnosticRecord"
]
FROZEN_CACHE_TTL_CLASSES: tuple[str, ...] = tuple(
    _CACHE_DIAGNOSTIC["properties"]["cache_write_tokens_by_ttl_class"]["propertyNames"]["enum"]
)
# FR-016e.3: each cache quantity is keyed identically to the ceiling that bounds
# it, so a ceiling can never be keyed differently from its measurement.
CACHE_QUANTITY_CEILINGS = {
    "cache_write_tokens_by_ttl_class": "max_cache_write_tokens_by_ttl_class",
    "cache_read_tokens": "max_cache_read_tokens",
}
# FR-016e.4: neither cache quantity is ever read against the input ceiling.
RAW_TOKEN_MEMBER_CEILINGS = {
    "input_tokens": "max_input_tokens",
    "output_tokens": "max_output_tokens",
    "cached_input_tokens": "max_cached_input_tokens",
    UNBOUNDED_RAW_TOKEN_MEMBER: None,
}


def _orchestration(control: Mapping[str, Any]) -> Mapping[str, Any]:
    specialization = control.get("orchestration_changing")
    if not isinstance(specialization, Mapping):
        raise ControlContractError(
            "the orchestration-changing control declares no orchestration_changing specialization"
        )
    return specialization


def _resource_vector(member: Mapping[str, Any]) -> Mapping[str, Any]:
    vector = member.get("resource_vector")
    if not isinstance(vector, Mapping):
        raise ControlContractError(
            f"unit member {member.get('row_id')!r} records no resource_vector"
        )
    return vector


def worst_terminal_state(states: Any, severity_order: Any) -> str:
    """FR-016a: the most severe member state present, by the declared order."""
    if not isinstance(severity_order, (list, tuple)) or not severity_order:
        raise ControlContractError("terminal_state_severity is missing or declares no member")
    if not isinstance(states, (list, tuple)) or not states:
        raise ControlContractError("a unit folds at least the parent's own terminal state")
    worst = None
    rank = -1
    for state in states:
        if state not in severity_order:
            raise ControlContractError(
                f"{state!r} is not a member of the declared severity order "
                f"{list(severity_order)}; a member with no terminal state leaves the unit's "
                "severity undefined and is refused rather than folded over"
            )
        position = list(severity_order).index(state)
        if position > rank:
            rank, worst = position, state
    return str(worst)


def validate_orchestration_control(control: Mapping[str, Any]) -> None:
    """FR-016, FR-016a, FR-016b: the declarations the fold is read against."""
    specialization = _orchestration(control)

    severity = specialization.get("terminal_state_severity")
    if not isinstance(severity, list) or sorted(severity) != sorted(FROZEN_TERMINAL_STATES):
        raise ControlContractError(
            f"terminal_state_severity must be set-equal to the frozen terminal-state enum "
            f"{list(FROZEN_TERMINAL_STATES)}; the control declares {severity!r}"
        )

    rule = specialization.get("aggregation_rule")
    if not isinstance(rule, Mapping) or sorted(rule) != sorted(FROZEN_PARETO_DIMENSIONS):
        raise ControlContractError(
            f"aggregation_rule must be total over the eight Pareto dimensions "
            f"{list(FROZEN_PARETO_DIMENSIONS)}; the control declares "
            f"{sorted(rule) if isinstance(rule, Mapping) else rule!r}"
        )
    if rule.get("terminal_state") != SEVERITY_FOLD_RULE:
        raise ControlContractError(
            f"terminal_state folds as {SEVERITY_FOLD_RULE!r}; a parent projection would let a run "
            "spray failing children and still report a clean state with the cost charged"
        )
    if rule.get("acceptance") != PARENT_ORACLE_RULE:
        raise ControlContractError(
            f"acceptance is {PARENT_ORACLE_RULE!r}; it is never summed, averaged, minimized, or "
            "maximized across children"
        )
    for dimension, combining in rule.items():
        if combining not in (ADDITIVE_RULE, SEVERITY_FOLD_RULE, PARENT_ORACLE_RULE):
            raise ControlContractError(
                f"aggregation_rule[{dimension!r}] declares {combining!r}, which is not a "
                "recognized combining rule"
            )
    if specialization.get("acceptance_rule") != PARENT_ORACLE_RULE:
        raise ControlContractError(
            f"acceptance_rule is {specialization.get('acceptance_rule')!r}, not {PARENT_ORACLE_RULE!r}"
        )
    if not _same_value(specialization.get("acceptance_floor_on_non_completed"), 0):
        raise ControlContractError(
            "acceptance_floor_on_non_completed is the frozen candidate-failure constant 0"
        )

    descriptor = specialization.get("topology_descriptor")
    if not isinstance(descriptor, Mapping) or sorted(descriptor) != sorted(
        TOPOLOGY_DESCRIPTOR_MEMBERS
    ):
        raise ControlContractError(
            f"topology_descriptor is exactly {list(TOPOLOGY_DESCRIPTOR_MEMBERS)}, so "
            "'altering any hash-relevant field' stays decidable over an enumerated member set"
        )
    recomputed = record_digest(descriptor)
    if specialization.get("topology_digest") != recomputed:
        raise ControlContractError(
            f"topology_digest does not recompute: recorded "
            f"{specialization.get('topology_digest')!r}, recomputed {recomputed!r}"
        )

    raw_rule = specialization.get("raw_token_aggregation")
    if not isinstance(raw_rule, Mapping) or sorted(raw_rule) != sorted(FROZEN_RAW_TOKEN_MEMBERS):
        raise ControlContractError(
            f"raw_token_aggregation must be total over the frozen raw token vector "
            f"{list(FROZEN_RAW_TOKEN_MEMBERS)}; the control declares "
            f"{sorted(raw_rule) if isinstance(raw_rule, Mapping) else raw_rule!r}"
        )
    for member, combining in raw_rule.items():
        if combining != ADDITIVE_RULE:
            raise ControlContractError(
                f"raw_token_aggregation[{member!r}] is {combining!r}; all four members sum"
            )

    cache_rule = specialization.get("cache_aggregation")
    if not isinstance(cache_rule, Mapping) or sorted(cache_rule) != sorted(
        CACHE_QUANTITY_CEILINGS
    ):
        raise ControlContractError(
            f"cache_aggregation must declare {sorted(CACHE_QUANTITY_CEILINGS)}; the control "
            f"declares {sorted(cache_rule) if isinstance(cache_rule, Mapping) else cache_rule!r}"
        )
    write_rule = cache_rule.get("cache_write_tokens_by_ttl_class")
    if not isinstance(write_rule, Mapping) or sorted(write_rule) != sorted(
        FROZEN_CACHE_TTL_CLASSES
    ):
        raise ControlContractError(
            f"cache write aggregation must be keyed over the frozen closed class space "
            f"{list(FROZEN_CACHE_TTL_CLASSES)} — the same keys as the ceiling that bounds it — "
            f"but the control declares "
            f"{sorted(write_rule) if isinstance(write_rule, Mapping) else write_rule!r}"
        )
    if any(combining != ADDITIVE_RULE for combining in write_rule.values()):
        raise ControlContractError("every cache write TTL class sums")
    if cache_rule.get("cache_read_tokens") != ADDITIVE_RULE:
        raise ControlContractError("cache_read_tokens sums")

    if specialization.get("unrecorded_quantity_disposition") != "unobserved":
        raise ControlContractError(
            f"unrecorded_quantity_disposition is 'unobserved'; the control declares "
            f"{specialization.get('unrecorded_quantity_disposition')!r}, which would let a "
            "missing diagnostic read as passed or as zero"
        )


def unit_members(rows: Any, control: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """FR-016d and FR-017a: the parent plus the transitive closure of the spawn links.

    Rows are returned parent-first in breadth-first order, so the caller can take
    the head as the parent objective's own row.
    """
    specialization = _orchestration(control)
    if control.get("attribution_level") != "policy":
        raise ControlContractError(
            f"the unit is evaluated at policy level only; the control declares "
            f"attribution_level {control.get('attribution_level')!r}"
        )
    if not isinstance(rows, list) or not rows:
        raise ControlContractError("the unit records no row")

    by_id: dict[str, Mapping[str, Any]] = {}
    parents: list[str] = []
    for position, row in enumerate(rows):
        row_id = row.get("row_id")
        if not isinstance(row_id, str) or not row_id:
            raise ControlContractError(f"rows[{position}] records no row_id")
        if row_id in by_id:
            raise ControlContractError(f"rows[{position}] repeats row_id {row_id!r}")
        by_id[row_id] = row
        if _resource_vector(row).get("terminal_state") is None:
            raise ControlContractError(
                f"{row_id!r} records no terminal state; a hung or unreported member would "
                "otherwise disappear from the fold while its cost was still charged"
            )
        if "spawned_by" not in row:
            raise ControlContractError(
                f"{row_id!r} is neither the parent's own row nor carries an authored spawning "
                "identifier, so the unit boundary is undecidable"
            )
        if row["spawned_by"] is None:
            parents.append(row_id)

    if len(parents) != 1:
        raise ControlContractError(
            f"exactly one row is the parent objective's own; the set carries {parents}"
        )
    parent_id = parents[0]

    children_of: dict[str, list[str]] = {}
    for row_id, row in by_id.items():
        link = row["spawned_by"]
        if link is None:
            continue
        if link not in by_id:
            raise ControlContractError(
                f"{row_id!r} records spawning identifier {link!r}, which names no row in the unit"
            )
        children_of.setdefault(link, []).append(row_id)

    ordered: list[str] = []
    seen: set[str] = set()
    queue = [parent_id]
    while queue:
        current = queue.pop(0)
        if current in seen:
            raise ControlContractError(f"the authored spawn links reach {current!r} twice")
        seen.add(current)
        ordered.append(current)
        queue.extend(sorted(children_of.get(current, ())))

    unreachable = sorted(set(by_id) - seen)
    if unreachable:
        raise ControlContractError(
            f"{unreachable} are outside the parent's spawn closure and would charge a partial "
            "cost to a frozen identity"
        )

    fan_out = specialization["topology_descriptor"]["fan_out"]
    if len(ordered) - 1 > fan_out:
        raise ControlContractError(
            f"the unit carries {len(ordered) - 1} non-parent members against a declared fan-out "
            f"ceiling of {fan_out}; an over-fan-out run is refused rather than aggregated"
        )

    # FR-016d.1: where a member binds the shared contract's graph, the two
    # sources must induce the same membership; a disagreement fails the row
    # closed rather than letting either source win.
    for row_id in ordered:
        bound = by_id[row_id].get("parent_child_graph")
        if bound is None:
            continue
        if sorted(bound) != sorted(PARENT_CHILD_GRAPH_MEMBERS):
            raise ControlContractError(
                f"{row_id!r} binds a graph declaring {sorted(bound)}; the shared treatment-record "
                f"contract requires {list(PARENT_CHILD_GRAPH_MEMBERS)}"
            )
        if bound["parent_execution_trace_id"] != by_id[row_id]["spawned_by"]:
            raise ControlContractError(
                f"{row_id!r} binds a graph naming parent "
                f"{bound['parent_execution_trace_id']!r} while its authored spawn link records "
                f"{by_id[row_id]['spawned_by']!r}"
            )
        if sorted(bound["child_execution_trace_ids"]) != sorted(children_of.get(row_id, ())):
            raise ControlContractError(
                f"{row_id!r} binds a graph whose child set "
                f"{sorted(bound['child_execution_trace_ids'])} disagrees with the authored links "
                f"{sorted(children_of.get(row_id, ()))}"
            )
        if bound["root_execution_trace_id"] != parent_id:
            raise ControlContractError(
                f"{row_id!r} binds a graph rooted at {bound['root_execution_trace_id']!r} while "
                f"the unit is rooted at {parent_id!r}"
            )

    return [by_id[row_id] for row_id in ordered]


def aggregate_objective(
    parent: Mapping[str, Any], children: Any, control: Mapping[str, Any]
) -> dict[str, Any]:
    """Fold one parent-plus-children unit across all eight Pareto dimensions."""
    validate_orchestration_control(control)
    specialization = _orchestration(control)
    members = [parent, *list(children)]

    folded: dict[str, Any] = {}
    for dimension, combining in specialization["aggregation_rule"].items():
        if combining == ADDITIVE_RULE:
            folded[dimension] = sum(_resource_vector(member)[dimension] for member in members)

    # FR-016d.3: a member with no terminal state leaves the unit malformed, so
    # it is refused rather than folded over the remaining members.
    states = [_resource_vector(member).get("terminal_state") for member in members]
    folded["terminal_state"] = worst_terminal_state(
        states, specialization["terminal_state_severity"]
    )

    # FR-016b outranks FR-016c wherever they meet: a unit that failed and never
    # reached its oracle records 0, not null.
    acceptance = _resource_vector(parent).get("acceptance")
    if folded["terminal_state"] != CLEAN_TERMINAL_STATE:
        acceptance = specialization["acceptance_floor_on_non_completed"]
    folded["acceptance"] = acceptance

    # FR-015a.3: terminal_state_severity carries no non-scorable member, so a
    # rerouted member is recorded at unit level rather than folded away.
    folded["non_scorable"] = any(
        member.get("failure_code") == SERVICE_REROUTE_FAILURE_CODE for member in members
    )
    folded["member_count"] = len(members)

    recorded = parent.get("recorded_aggregate")
    if recorded is not None:
        for key, value in recorded.items():
            if key not in folded:
                raise ControlContractError(f"recorded_aggregate names unknown member {key!r}")
            if not _same_value(folded[key], value):
                raise ControlContractError(
                    f"recorded_aggregate[{key!r}] is {value!r}; the fold yields {folded[key]!r}"
                )
    return folded


def _raw_token_vector(member: Mapping[str, Any]) -> Mapping[str, Any]:
    vector = member.get("raw_token_vector")
    if not isinstance(vector, Mapping):
        raise ControlContractError(
            f"unit member {member.get('row_id')!r} records no raw_token_vector"
        )
    return vector


def _sum_or_unobserved(values: list[Any]) -> int | None:
    """``None`` when any member did not record the quantity — never zero."""
    if any(value is None for value in values):
        return None
    for value in values:
        if not isinstance(value, int) or isinstance(value, bool):
            raise ControlContractError(
                f"a recorded quantity is a whole count, not {value!r}"
            )
    return sum(values)


def aggregate_raw_tokens_and_cache(
    members: Any, control: Mapping[str, Any]
) -> dict[str, Any]:
    """FR-016e: sum the frozen four and the two cache diagnostics, promoting neither."""
    validate_orchestration_control(control)
    specialization = _orchestration(control)
    if not isinstance(members, list) or not members:
        raise ControlContractError("the unit records no member to aggregate")

    raw_tokens = {
        member: _sum_or_unobserved(
            [_raw_token_vector(row).get(member) for row in members]
        )
        for member in specialization["raw_token_aggregation"]
    }
    bounded = [raw_tokens[member] for member in RAW_TOKEN_CEILING_QUANTITY_MEMBERS]
    ceiling_quantity = _sum_or_unobserved(bounded)

    unobserved: list[str] = []
    diagnostics = [row.get("cache_diagnostic") for row in members]
    if any(diagnostic is None for diagnostic in diagnostics):
        # FR-016e.5: the aggregate is not computable, so the bound it feeds is
        # recorded unobserved rather than passed and never read as zero.
        cache_write: dict[str, int] | None = None
        cache_read: int | None = None
        unobserved.extend(CACHE_QUANTITY_CEILINGS.values())
    else:
        cache_read = _sum_or_unobserved(
            [diagnostic.get("cache_read_tokens") for diagnostic in diagnostics]
        )
        if cache_read is None:
            unobserved.append(CACHE_QUANTITY_CEILINGS["cache_read_tokens"])
        per_class = {
            ttl_class: _sum_or_unobserved([
                diagnostic.get("cache_write_tokens_by_ttl_class", {}).get(ttl_class)
                for diagnostic in diagnostics
            ])
            for ttl_class in FROZEN_CACHE_TTL_CLASSES
        }
        if any(value is None for value in per_class.values()):
            cache_write = None
            unobserved.append(CACHE_QUANTITY_CEILINGS["cache_write_tokens_by_ttl_class"])
        else:
            cache_write = per_class

    return {
        "raw_tokens": raw_tokens,
        "raw_token_ceiling_members": RAW_TOKEN_CEILING_QUANTITY_MEMBERS,
        "raw_token_ceiling_quantity": ceiling_quantity,
        "cache_write_tokens_by_ttl_class": cache_write,
        "cache_read_tokens": cache_read,
        "bounded_by": {**RAW_TOKEN_MEMBER_CEILINGS, **CACHE_QUANTITY_CEILINGS},
        "unobserved": sorted(set(unobserved)),
        "member_count": len(members),
    }


def validate_control_specializations(registry: Mapping[str, Any]) -> None:
    """Run each control's specialization rules, keyed by its ``control_kind``."""
    for index, control in enumerate(registry.get("controls", ())):
        kind = control.get("control_kind")
        try:
            if kind == "unpinned":
                validate_unpinned_control(control)
            elif kind == "adaptive":
                validate_signal_maps(control)
            elif kind == "orchestration_changing":
                validate_orchestration_control(control)
        except ControlContractError as exc:
            raise ControlContractError(f"controls[{index}] ({kind}): {exc}") from exc


def load_registry(path: Path = FROZEN_REGISTRY_PATH) -> dict[str, Any]:
    """Load the frozen registry instance, schema-validate it, then check semantics."""
    registry = load_contract(path)
    validate_instance(registry, REGISTRY_SCHEMA, path="registry")
    validate_registry(registry)
    return registry


# --------------------------------------------------------------------------- #
# Deterministic replay (FR-026, FR-027, FR-028)                                 #
# --------------------------------------------------------------------------- #

FROZEN_REPLAY_PATH = FIXTURE_ROOT / "control-replay.json"
FROZEN_PARTITION_ENTRIES_PATH = FIXTURE_ROOT / "partition-registry-entries.json"

# One kind per frozen entrypoint the committed cases drive. Closed here so a case
# naming a behaviour no validator owns fails closed instead of replaying nothing.
REPLAY_KINDS = (
    "pin_inheritance",
    "escalation",
    "clean_streak",
    "service_reroute",
    "unit_aggregate",
    "bound_breach",
)

# The replay fixture is harness data rather than a frozen contract, so its shape
# is declared here and checked through the same fail-closed engine the contract
# documents use. Nested payloads stay open at the type level because the
# validators above already own their member rules; what this schema pins is the
# evidence discipline every row must carry (FR-027).
REPLAY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema_version",
        "fixture_kind",
        "description",
        "bound_freeze",
        "bound_freeze_note",
        "cases",
    ],
    "properties": {
        "schema_version": {"const": "1.0.0"},
        "fixture_kind": {"const": "policy_control_replay"},
        "description": {"type": "string", "minLength": 1},
        "bound_freeze": {"type": "object"},
        "bound_freeze_note": {"type": "string", "minLength": 1},
        "cases": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/case"}},
    },
    "$defs": {
        "case": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "case_id",
                "control_kind",
                "replay_kind",
                "proves",
                "requirements",
                "rows",
                "expected",
            ],
            "properties": {
                "case_id": {"type": "string", "minLength": 1},
                "control_kind": {"enum": list(CONTROL_KINDS)},
                "replay_kind": {"enum": list(REPLAY_KINDS)},
                "proves": {"type": "string", "minLength": 1},
                "requirements": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"type": "string", "minLength": 1},
                },
                "initial_state": {"type": "object"},
                "alternate_pinned_parent_model": {"type": "string", "minLength": 1},
                "rows": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/row"}},
                "expected": {"type": "object"},
            },
        },
        "row": {
            "type": "object",
            "additionalProperties": False,
            "required": ["row_id", "objective_id", "scored", "outcome_bearing"],
            "properties": {
                "row_id": {"type": "string", "minLength": 1},
                "objective_id": {"type": "string", "minLength": 1},
                # FR-027 and SC-010: neither is a default the fixture may relax.
                "scored": {"const": False},
                "outcome_bearing": {"const": False},
                "served_model": {"type": "string", "minLength": 1},
                "served_effort": {"enum": list(FROZEN_EFFORT_LADDER)},
                "terminal_state": {"enum": list(FROZEN_TERMINAL_STATES)},
                "failure_code": {"enum": list(FROZEN_FAILURE_CODES)},
                "failure_plane": {"enum": list(FROZEN_FAILURE_PLANES)},
                "retries": {"type": "integer", "minimum": 0},
                "escalated": {"type": "boolean"},
                "budget_observations": {"type": "object"},
                "counted_over": {"enum": ["per_objective", "per_unit"]},
                "attempts": {"type": "array", "minItems": 1, "items": {"type": "object"}},
                "recorded_outcome": {"type": "object"},
                "spawned_by": {"type": ["string", "null"]},
                "resource_vector": {"type": "object"},
                "raw_token_vector": {"type": "object"},
                "cache_diagnostic": {"type": "object"},
                "recorded_aggregate": {"type": "object"},
            },
        },
    },
}


def reserved_partition_entry(path: Path = FROZEN_PARTITION_ENTRIES_PATH) -> dict[str, Any]:
    """The committed entry CAR-004 registers and never consumes.

    Selected by the entry's own ``qualification_eligible`` flag — the member the
    frozen consumption path reads — rather than by a transcribed partition id, so
    re-freezing the reservation moves the guard with it (FR-025a, FR-026).
    """
    entries = load_contract(path).get("entries")
    if not isinstance(entries, list) or not entries:
        raise ControlContractError(f"{path.name} declares no partition registry entry")
    reserved = [entry for entry in entries if entry.get("qualification_eligible")]
    if len(reserved) != 1:
        raise ControlContractError(
            f"{path.name} declares {len(reserved)} qualification-eligible partitions; "
            "the reservation this guard reads is exactly one"
        )
    return dict(reserved[0])


def _row_objective_ids(row: Mapping[str, Any], label: str) -> list[str]:
    """Every objective one row references, over both shapes a row can carry.

    A replay row names a single ``objective_id``; a smoke record carries its
    consumed set as ``objective_ids``. Reading both here is what lets one entry
    point cover both halves of the guard (FR-026).
    """
    referenced: list[str] = []
    single = row.get("objective_id")
    if single is not None:
        referenced.append(str(single))
    many = row.get("objective_ids")
    if isinstance(many, (list, tuple)):
        referenced.extend(str(objective) for objective in many)
    elif many is not None:
        raise ControlContractError(f"row {label}: objective_ids is not an array of identifiers")
    return referenced


def assert_reserved_partition_untouched(
    rows: Iterable[Mapping[str, Any]], reserved_entry: Mapping[str, Any]
) -> None:
    """FR-026: fail if any CAR-004 row — replay or smoke — touches the reservation.

    One entry point serves both enforcement points FR-026a names: the committed
    suite drives it over the replay rows, and the operator smoke drives it over a
    produced record's rows at seal time. An empty or unnamed reservation is
    refused rather than passed, because a guard that certifies non-consumption
    against nothing reads as passing while checking nothing (SC-007).
    """
    reserved_objectives = {str(objective) for objective in reserved_entry.get("objective_ids", ())}
    if not reserved_objectives:
        raise ControlContractError(
            "the reserved partition entry declares no objective; refusing to certify "
            "non-consumption against an empty reservation"
        )
    reserved_partition = str(reserved_entry.get("partition_id") or "")
    if not reserved_partition:
        raise ControlContractError("the reserved partition entry declares no partition_id")

    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ControlContractError(f"row[{index}] is not a record the guard can read")
        label = repr(row["row_id"]) if row.get("row_id") else f"[{index}]"
        if str(row.get("partition_id") or "") == reserved_partition:
            raise ControlContractError(
                f"row {label} names reserved partition {reserved_partition!r}, which is "
                "held untouched for the successor spec"
            )
        for objective in _row_objective_ids(row, label):
            if objective in reserved_objectives:
                raise ControlContractError(
                    f"row {label} references reserved objective {objective!r}, which is "
                    "held untouched for the successor spec"
                )


def _control_of_kind(registry: Mapping[str, Any], kind: str) -> Mapping[str, Any]:
    for control in registry.get("controls", ()):
        if control.get("control_kind") == kind:
            return control
    raise ControlContractError(f"the registry declares no {kind!r} control")


def _single_row(case: Mapping[str, Any]) -> Mapping[str, Any]:
    rows = case["rows"]
    if len(rows) != 1:
        raise ControlContractError(
            f"case {case['case_id']!r} drives a single-row entrypoint but records {len(rows)} rows"
        )
    return rows[0]


def _replay_pin_inheritance(
    case: Mapping[str, Any], registry: Mapping[str, Any], freeze: Mapping[str, Any]
) -> dict[str, Any]:
    """FR-006 and FR-007: the served route is the pin, and a re-pin is a new address."""
    control = _control_of_kind(registry, case["control_kind"])
    validate_unpinned_control(control)
    spec = control["unpinned"]
    repinned = copy.deepcopy(dict(control))
    repinned["unpinned"]["pinned_parent_model"] = case["alternate_pinned_parent_model"]
    return {
        "model_resolution": spec["model_resolution"],
        "arm_count": spec["arm_count"],
        "pinned_parent_model": spec["pinned_parent_model"],
        "pinned_parent_effort": spec["pinned_parent_effort"],
        "served_matches_pin": all(
            row.get("served_model") == spec["pinned_parent_model"]
            and row.get("served_effort") == spec["pinned_parent_effort"]
            for row in case["rows"]
        ),
        "repin_changes_control_digest": control_digest(repinned) != control["control_digest"],
    }


def _replay_escalation(
    case: Mapping[str, Any], registry: Mapping[str, Any], freeze: Mapping[str, Any]
) -> dict[str, Any]:
    """FR-011, FR-011b, FR-013: one step per objective, and no wrap-around."""
    control = _control_of_kind(registry, case["control_kind"])
    validate_escalation_ladder(control, freeze)
    allowance = _adaptive(control)["max_escalations_per_objective"]
    route = case["initial_state"]["current_route_id"]
    spent = 0
    responses: list[str] = []
    positions: list[str] = []
    for row in case["rows"]:
        response = resolve_response(control, row)
        responses.append(response)
        if response == "escalate" and spent < allowance:
            target = next_route(control, route)
            if target is not None:
                route, spent = target, spent + 1
        positions.append(route)
    return {
        "responses": responses,
        "route_after_each_signal": positions,
        "escalations_recorded": spent,
        "max_escalations_per_objective": allowance,
        "next_route_from_final_position": next_route(control, route),
        "ladder_is_permutation_of_the_admitted_set": True,
    }


def _replay_clean_streak(
    case: Mapping[str, Any], registry: Mapping[str, Any], freeze: Mapping[str, Any]
) -> dict[str, Any]:
    """FR-012 and FR-012a: the streak carried across a sequence of boundaries."""
    control = _control_of_kind(registry, case["control_kind"])
    state = dict(case["initial_state"])
    streaks: list[int] = []
    routes: list[str] = []
    excluded = 0
    de_escalations = 0
    for row in case["rows"]:
        outcome = advance_clean_streak(control, state, row)
        state = {
            "current_route_id": outcome["current_route_id"],
            "clean_streak": outcome["clean_streak"],
        }
        streaks.append(outcome["clean_streak"])
        routes.append(outcome["current_route_id"])
        excluded += int(bool(outcome["excluded"]))
        de_escalations += int(bool(outcome["de_escalated"]))
    return {
        "streak_after_each_boundary": streaks,
        "route_after_each_boundary": routes,
        "excluded_objectives": excluded,
        "de_escalations": de_escalations,
    }


def _replay_service_reroute(
    case: Mapping[str, Any], registry: Mapping[str, Any], freeze: Mapping[str, Any]
) -> dict[str, Any]:
    """FR-015 and FR-015a: non-scorable, and spending nothing."""
    control = _control_of_kind(registry, case["control_kind"])
    return classify_service_reroute(control, _single_row(case))


def _replay_unit_aggregate(
    case: Mapping[str, Any], registry: Mapping[str, Any], freeze: Mapping[str, Any]
) -> dict[str, Any]:
    """FR-016 and FR-016e: the parent-plus-children fold, cost and tokens together."""
    control = _control_of_kind(registry, case["control_kind"])
    members = unit_members(case["rows"], control)
    observed = aggregate_objective(members[0], members[1:], control)
    tokens = aggregate_raw_tokens_and_cache(members, control)
    observed.update(
        raw_tokens=tokens["raw_tokens"],
        raw_token_ceiling_quantity=tokens["raw_token_ceiling_quantity"],
        cache_write_tokens_by_ttl_class=tokens["cache_write_tokens_by_ttl_class"],
        cache_read_tokens=tokens["cache_read_tokens"],
        unobserved=tokens["unobserved"],
    )
    return observed


def _replay_bound_breach(
    case: Mapping[str, Any], registry: Mapping[str, Any], freeze: Mapping[str, Any]
) -> dict[str, Any]:
    """FR-014a.4: both breach paths, folded by severity and floored to acceptance 0."""
    control = _control_of_kind(registry, case["control_kind"])
    observed = evaluate_bounds(control, _single_row(case))
    # The severity order and the acceptance floor are declared once, on the
    # orchestration-changing control, so a breached objective is folded against
    # the same declaration a multi-child unit is.
    folding = _orchestration(_control_of_kind(registry, "orchestration_changing"))
    folded = worst_terminal_state([observed["terminal_state"]], folding["terminal_state_severity"])
    observed["folded_terminal_state"] = folded
    observed["folded_acceptance"] = (
        None if folded == CLEAN_TERMINAL_STATE else folding["acceptance_floor_on_non_completed"]
    )
    return observed


_REPLAY_HANDLERS = {
    "pin_inheritance": _replay_pin_inheritance,
    "escalation": _replay_escalation,
    "clean_streak": _replay_clean_streak,
    "service_reroute": _replay_service_reroute,
    "unit_aggregate": _replay_unit_aggregate,
    "bound_breach": _replay_bound_breach,
}


def replay(fixture_path: Path = FROZEN_REPLAY_PATH) -> list[dict[str, Any]]:
    """Replay the committed cases against the frozen controls, fail-closed.

    Every value the replay reads is committed, so the returned list is a pure
    function of committed bytes: digesting it twice yields the same value, which
    is how SC-005's byte-identical claim is tested rather than asserted.
    """
    fixture = load_contract(fixture_path)
    validate_instance(fixture, REPLAY_SCHEMA, path="replay")
    reserved = reserved_partition_entry()
    registry = load_registry()
    freeze = fixture["bound_freeze"]

    outcomes: list[dict[str, Any]] = []
    for index, case in enumerate(fixture["cases"]):
        path = f"cases[{index}] ({case['case_id']})"
        # FR-026: the replay half of the guard, run through the one entry point
        # the smoke half seals with, so a single implementation carries both.
        try:
            assert_reserved_partition_untouched(case["rows"], reserved)
        except ControlContractError as exc:
            raise ControlContractError(f"{path}: {exc}") from exc
        handler = _REPLAY_HANDLERS.get(case["replay_kind"])
        if handler is None:
            raise ControlContractError(f"{path}: {case['replay_kind']!r} drives no frozen rule")
        try:
            observed = handler(case, registry, freeze)
        except ControlContractError as exc:
            raise ControlContractError(f"{path}: {exc}") from exc
        if not _same_value(observed, case["expected"]):
            raise ControlContractError(
                f"{path}: the replay observed {observed!r}; the fixture records "
                f"{case['expected']!r}"
            )
        outcomes.append({
            "case_id": case["case_id"],
            "control_kind": case["control_kind"],
            "replay_kind": case["replay_kind"],
            "observed": observed,
        })
    return outcomes


# --------------------------------------------------------------------------- #
# Bounded smoke record (FR-027, FR-030, FR-030b, FR-030c)                       #
# --------------------------------------------------------------------------- #

SMOKE_RECORD_KIND = "policy_control_smoke"
# FR-030b.1: the one scope all four bounds are counted over. Named on the reading
# so a consumer can tell a unit-scoped budget from a per-node one.
SMOKE_COUNTING_SCOPE = "parent_plus_children_unit"
# FR-030b.3: the 30-minute cap is elapsed over the unit, never the additive
# duration the frozen Pareto rule sums. Both quantities are reported.
SMOKE_WALL_CLOCK_READING = "elapsed_over_unit"
EVIDENCE_ADMISSIBILITY = ("admitted", "refused")
# FR-030c.3: the refusal is CAR-004-owned. It is not a score-plane failure code,
# because a non-scored smoke row produces no score bundle for one to sit on.
API_KEY_REFUSAL_REASON = "observed_authentication_mode_api_key"
REFUSED_AUTHENTICATION_MODE = "api_key"
# FR-032, refused on the same terms as an observed api_key: a pair that did not
# observe disjoint cache state leaves the record inadmissible as evidence, but
# the observation survives on it so the remedy stays a re-run, never a relabel.
CACHE_ISOLATION_REFUSAL_REASON = "observed_cache_isolation_not_disjoint"

SMOKE_RECORD_REQUIRED = (
    "arm_id",
    "authentication_mode",
    "claude_code_subagent_model_unset",
    "confirmation_entries",
    "control_digest",
    "control_id",
    "demonstration_evidence",
    "demonstration_state",
    "elapsed_wall_clock_seconds",
    "objective_attempts",
    "objective_ids",
    "observed_cache_isolation",
    "partition_id",
    "record_kind",
    "schema_version",
    "scored",
    "smoke_id",
)

# The four FR-030 bounds, each named by the ``smoke_bounds`` member that carries
# it, so a rename on the frozen side fails the reading closed rather than
# silently dropping a ceiling.
SMOKE_ATTEMPT_BOUND = "max_attempts"
SMOKE_CANDIDATE_BOUND = "max_candidates"
SMOKE_CONFIRMATION_BOUND = "max_confirmation_entries"
SMOKE_DURATION_BOUND = "max_duration_seconds"


def admissible_authentication_modes() -> tuple[str, ...]:
    """FR-030c.1: the Claude-side enumeration, read live and revalidated set-equal.

    The repository carries frozen members of this name whose enumerations differ,
    so the mode is resolved through the document that declares the Claude-side
    ``environment_contract`` object rather than by field name alone. A membership
    change on the frozen side fails closed instead of being absorbed.
    """
    identifier, node = pinned_parent_document()
    modes = node["properties"]["authentication_mode"].get("enum")
    if not isinstance(modes, list) or sorted(modes) != sorted(CLAUDE_AUTHENTICATION_MODES):
        raise ControlContractError(
            f"{identifier} enumerates authentication_mode as {modes!r}; CAR-004 records the "
            f"mode through the Claude-side member enumerated {list(CLAUDE_AUTHENTICATION_MODES)}"
        )
    return tuple(modes)


def shared_environment_authentication_modes(document: Mapping[str, Any]) -> tuple[str, ...]:
    """The shared runtime member of the same name, named here so it can be refused.

    FR-030c.1 rejects recording a CAR-004 smoke against this enumeration: doing so
    would make the mode incomparable with every CAR-003 record on this platform.
    """
    properties = document.get("properties") if isinstance(document, Mapping) else None
    member = properties.get("authentication_mode") if isinstance(properties, Mapping) else None
    modes = member.get("enum") if isinstance(member, Mapping) else None
    if not isinstance(modes, list) or not modes:
        raise ControlContractError(
            "the shared environment contract declares no authentication_mode enumeration"
        )
    return tuple(modes)


def _registry_control_for(record: Mapping[str, Any], registry: Mapping[str, Any]) -> Mapping[str, Any]:
    for control in registry.get("controls", ()):
        if control.get("control_id") == record.get("control_id"):
            if control.get("control_digest") != record.get("control_digest"):
                raise ControlContractError(
                    f"the record carries control_digest {record.get('control_digest')!r}; the "
                    f"frozen registry records {control.get('control_digest')!r}"
                )
            return control
    raise ControlContractError(
        f"the record names control {record.get('control_id')!r}, which the registry does not carry"
    )


def _smoke_unit_rows(record: Mapping[str, Any]) -> tuple[list[Mapping[str, Any]], int]:
    """Every unit member the record recorded, with the child-dispatch count.

    FR-030b.4: a child dispatch consumes no attempt against ``max_attempts``, so
    the two quantities are counted separately and reported separately.
    """
    attempts = record.get("objective_attempts")
    if not isinstance(attempts, list) or not attempts:
        raise ControlContractError("the smoke record declares no objective attempt")
    rows: list[Mapping[str, Any]] = []
    children = 0
    for index, attempt in enumerate(attempts):
        if not isinstance(attempt, Mapping) or not attempt.get("objective_id"):
            raise ControlContractError(f"objective_attempts[{index}] records no objective_id")
        members = attempt.get("unit_rows")
        if not isinstance(members, list) or not members:
            raise ControlContractError(
                f"objective_attempts[{index}] records no unit row; the bounds are counted over "
                f"the {SMOKE_COUNTING_SCOPE}"
            )
        parents = [row for row in members if row.get("spawned_by") is None]
        if len(parents) != 1:
            raise ControlContractError(
                f"objective_attempts[{index}] records {len(parents)} parentless rows; the unit "
                "boundary is decidable only with exactly one"
            )
        children += len(members) - 1
        rows.extend(members)
    return rows, children


def _smoke_aggregate(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    """FR-030b.2: each ceiling is read against the aggregate of the quantity it names."""
    raw_tokens = {
        member: _sum_or_unobserved([_raw_token_vector(row).get(member) for row in rows])
        for member in FROZEN_RAW_TOKEN_MEMBERS
    }
    ceiling_quantity = _sum_or_unobserved(
        [raw_tokens[member] for member in RAW_TOKEN_CEILING_QUANTITY_MEMBERS]
    )
    diagnostics = [row.get("cache_diagnostic") for row in rows]
    if any(diagnostic is None for diagnostic in diagnostics):
        cache_read: int | None = None
        cache_write: dict[str, int | None] | None = None
    else:
        cache_read = _sum_or_unobserved(
            [diagnostic.get("cache_read_tokens") for diagnostic in diagnostics]
        )
        cache_write = {
            ttl_class: _sum_or_unobserved([
                diagnostic.get("cache_write_tokens_by_ttl_class", {}).get(ttl_class)
                for diagnostic in diagnostics
            ])
            for ttl_class in FROZEN_CACHE_TTL_CLASSES
        }
    return {
        "raw_tokens": raw_tokens,
        "raw_token_ceiling_quantity": ceiling_quantity,
        "cache_read_tokens": cache_read,
        "cache_write_tokens_by_ttl_class": cache_write,
        # FR-030b.3's second quantity, held to the same discipline as every other
        # one in this aggregate: a member that recorded no duration leaves the sum
        # unobserved rather than contributing a zero that reads as "fast".
        "additive_duration_ms": _sum_or_unobserved(
            [row.get("duration_ms") for row in rows]
        ),
    }


def _breach(member: str, consumed: Any, ceiling: Any) -> str | None:
    if consumed is None:
        return None
    return None if consumed <= ceiling else (
        f"{member}: the unit consumed {consumed}, the frozen bound is {ceiling}"
    )


def validate_smoke_record(
    record: Mapping[str, Any], registry: Mapping[str, Any]
) -> Mapping[str, Any]:
    """FR-027, FR-030, FR-030b, FR-030c: read one produced smoke record fail-closed.

    Every refusal but one raises. An observed ``api_key`` is not a schema
    violation: FR-030c.3 requires the observation to survive on the refused
    record, so the reading is returned with ``evidence_admissibility: "refused"``
    and the observed value retained. A refused run therefore stays
    distinguishable from one that never ran, and the remedy is a re-run rather
    than a relabel.
    """
    if not isinstance(record, Mapping):
        raise ControlContractError("the smoke record is not a record this reader can read")
    missing = [member for member in SMOKE_RECORD_REQUIRED if member not in record]
    if missing:
        raise ControlContractError(f"the smoke record is missing {missing}")
    if record["record_kind"] != SMOKE_RECORD_KIND:
        raise ControlContractError(
            f"record_kind is frozen at {SMOKE_RECORD_KIND!r}, not {record['record_kind']!r}"
        )

    control = _registry_control_for(record, registry)

    # FR-027 and FR-030: no CAR-004 row is outcome-bearing. ``False`` is checked
    # by identity so a truthy stand-in such as 0 or "false" cannot pass.
    if record["scored"] is not False:
        raise ControlContractError(
            f"every smoke row is explicitly non-scored; the record records scored="
            f"{record['scored']!r}"
        )

    # FR-026: the seal-time half of the guard, run through the same entry point
    # the committed replay half uses.
    reserved = reserved_partition_entry()
    assert_reserved_partition_untouched([record], reserved)
    rows, child_dispatches = _smoke_unit_rows(record)
    assert_reserved_partition_untouched(record["objective_attempts"], reserved)

    attempts = record["objective_attempts"]
    consumed_objectives = [str(attempt["objective_id"]) for attempt in attempts]
    if sorted(set(consumed_objectives)) != sorted({str(o) for o in record["objective_ids"]}):
        raise ControlContractError(
            f"objective_ids records {sorted(record['objective_ids'])}; the attempts consumed "
            f"{sorted(set(consumed_objectives))}"
        )

    modes = admissible_authentication_modes()
    observed_mode = record["authentication_mode"]
    if observed_mode not in modes:
        raise ControlContractError(
            f"authentication_mode {observed_mode!r} is outside the Claude-side frozen "
            f"enumeration {list(modes)}"
        )

    bounds = registry.get("smoke_bounds")
    _validate_smoke_bounds(bounds)
    aggregate = _smoke_aggregate(rows)

    repetitions = max(consumed_objectives.count(objective) for objective in consumed_objectives)
    elapsed = record["elapsed_wall_clock_seconds"]
    if not isinstance(elapsed, int) or isinstance(elapsed, bool) or elapsed < 0:
        raise ControlContractError(
            f"elapsed_wall_clock_seconds is an elapsed reading over the unit, not {elapsed!r}"
        )
    # Same reading, same discipline: a count is compared against a ceiling below,
    # so a non-count here would surface as a bare TypeError from that comparison
    # rather than as this module's own contract error.
    confirmations = record["confirmation_entries"]
    if not isinstance(confirmations, int) or isinstance(confirmations, bool) or confirmations < 0:
        raise ControlContractError(
            f"confirmation_entries is a count over the unit, not {confirmations!r}"
        )

    consumed: dict[str, Any] = {
        SMOKE_ATTEMPT_BOUND: len(attempts),
        SMOKE_CANDIDATE_BOUND: repetitions,
        SMOKE_CONFIRMATION_BOUND: confirmations,
        SMOKE_DURATION_BOUND: elapsed,
        RAW_TOKEN_CEILING_MEMBER: aggregate["raw_token_ceiling_quantity"],
    }
    for member, ceiling_member in RAW_TOKEN_MEMBER_CEILINGS.items():
        if ceiling_member is not None:
            consumed[ceiling_member] = aggregate["raw_tokens"][member]
    consumed[CACHE_QUANTITY_CEILINGS["cache_read_tokens"]] = aggregate["cache_read_tokens"]

    breaches = [
        finding
        for member, value in consumed.items()
        if (finding := _breach(member, value, _bound(bounds, member, "smoke_bounds")["value"]))
    ]
    write_ceilings = bounds["max_cache_write_tokens_by_ttl_class"]
    written = aggregate["cache_write_tokens_by_ttl_class"] or {}
    for ttl_class in FROZEN_CACHE_TTL_CLASSES:
        finding = _breach(
            f"max_cache_write_tokens_by_ttl_class.{ttl_class}",
            written.get(ttl_class),
            _bound(write_ceilings, ttl_class, "smoke_bounds")["value"],
        )
        if finding:
            breaches.append(finding)
    if breaches:
        raise ControlContractError(
            f"the smoke exceeded its frozen bounds over the {SMOKE_COUNTING_SCOPE}: {breaches}"
        )

    # FR-016e.5 and FR-030b.2: a quantity no member recorded leaves the bound it
    # feeds unobserved. It is never passed and never read as zero.
    unobserved = {member for member, value in consumed.items() if value is None}
    written_per_class = aggregate["cache_write_tokens_by_ttl_class"]
    if written_per_class is None or any(
        written_per_class.get(ttl_class) is None for ttl_class in FROZEN_CACHE_TTL_CLASSES
    ):
        unobserved.add(CACHE_QUANTITY_CEILINGS["cache_write_tokens_by_ttl_class"])

    # FR-032: the record is required to carry its pairwise isolation observations,
    # so they are read here. A required member nothing inspects is decoration.
    isolation = read_record_cache_isolation(record)

    refusal_reasons: list[str] = []
    if observed_mode == REFUSED_AUTHENTICATION_MODE:
        refusal_reasons.append(API_KEY_REFUSAL_REASON)
    if not isolation["all_pairs_disjoint"]:
        refusal_reasons.append(CACHE_ISOLATION_REFUSAL_REASON)

    return {
        "control_id": record["control_id"],
        "control_kind": control["control_kind"],
        "authentication_mode": observed_mode,
        "evidence_admissibility": "refused" if refusal_reasons else "admitted",
        "refusal_reasons": refusal_reasons,
        "counted_over": SMOKE_COUNTING_SCOPE,
        "wall_clock_reading": SMOKE_WALL_CLOCK_READING,
        "consumed": consumed,
        "additive_duration_ms": aggregate["additive_duration_ms"],
        "bounds_unobserved": sorted(unobserved),
        "cache_isolation": isolation,
        "unit_member_count": len(rows),
        "child_dispatch_count": child_dispatches,
        "objective_attempt_count": len(attempts),
    }


# --------------------------------------------------------------------------- #
# Demonstration state and pairwise cache isolation (FR-031, FR-031a, FR-032a)   #
# --------------------------------------------------------------------------- #

# FR-031a.7: CAR-004-owned and closed. A non-scored smoke row produces no score
# bundle, so the state can never be a score-plane failure code.
DEMONSTRATION_STATES = ("demonstrated", "not_demonstrated")
DEMONSTRATED, NOT_DEMONSTRATED = DEMONSTRATION_STATES

# FR-031a.1: the request that asked for a route is not evidence that the route
# was served, so the request is named here in order to be refused.
DISPATCH_REQUEST_SOURCE = "dispatch_request"
DEMONSTRATION_EVIDENCE_SOURCES = ("configured_route_proof", "execution_trace")

DEMONSTRATION_REASONS = (
    "control_not_registered",
    "observable_absent",
    "observable_read_from_dispatch_request",
    "parallel_inequality_not_met",
    "route_did_not_advance_one_ladder_entry",
    "served_route_did_not_move",
    "served_route_does_not_match_pinned_parent",
    "subagent_model_override_not_excluded",
    "unit_has_fewer_than_two_non_parent_members",
    "wall_time_unobserved",
)

# The frozen configured-route proof publishes the three members FR-031a.3 and
# FR-031a.4 read back. A rename on the frozen side fails this module closed at
# import rather than quietly narrowing the observable.
FROZEN_ROUTE_PROOF_MEMBERS: tuple[str, ...] = tuple(
    load_contract(FROZEN_TREATMENT_RECORD_SCHEMA_PATH)["$defs"]["configuredRouteProof"]["required"]
)
ROUTE_OBSERVABLES = ("model", "effort", "candidate_route_id")
if any(member not in FROZEN_ROUTE_PROOF_MEMBERS for member in ROUTE_OBSERVABLES):
    raise ControlContractError(
        f"the frozen configured-route proof no longer declares {list(ROUTE_OBSERVABLES)}; "
        f"it declares {list(FROZEN_ROUTE_PROOF_MEMBERS)}"
    )

# FR-032a.1: the status set is read live from the frozen cache diagnostic, never
# restated, so a membership change there fails this check closed.
ISOLATION_STATUSES: tuple[str, ...] = tuple(
    _CACHE_DIAGNOSTIC["properties"]["observed_cache_isolation"]["properties"]["status"]["enum"]
)
ISOLATION_DISJOINT = "observed_disjoint"
# FR-032a.3: both non-disjoint statuses invalidate the affected smoke under codes
# the frozen score plane already publishes. Neither code is coined here, and the
# plane each sits on is derived rather than transcribed.
ISOLATION_FAILURE_CODES = {
    "observed_shared": "infrastructure_failure",
    "unobserved": "required_evidence_missing",
}
PRECOMMITMENT_MEMBER = "per_arm_ephemeral_root"
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _record_unit_rows(record: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Every unit member the record carries, read leniently: this reader never raises."""
    attempts = record.get("objective_attempts")
    if not isinstance(attempts, list):
        return []
    return [
        row
        for attempt in attempts
        if isinstance(attempt, Mapping)
        for row in (attempt.get("unit_rows") or [])
        if isinstance(row, Mapping)
    ]


def _observed_wall_time_ms(row: Mapping[str, Any]) -> int | None:
    """A whole-millisecond reading, or ``None`` when the member recorded none.

    A malformed value is not a lesser problem than an absent one: both leave the
    wall time unobserved, and neither may raise out of a reader FR-031a requires
    to return a verdict for every record it is handed.
    """
    value = row.get("wall_time_ms")
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _route_observation(
    evidence: Mapping[str, Any], member: str, reasons: list[str]
) -> Mapping[str, Any] | None:
    observation = evidence.get(member)
    if not isinstance(observation, Mapping) or any(
        not observation.get(name) for name in ROUTE_OBSERVABLES
    ):
        reasons.append("observable_absent")
        return None
    return observation


def evaluate_demonstration(
    record: Mapping[str, Any], registry: Mapping[str, Any]
) -> dict[str, Any]:
    """FR-031 and FR-031a: never raises; an unevidenced demonstration is not one.

    The state is derived from the evidence the run produced. The record's own
    recorded state is reported beside it and never allowed to override it, so the
    remedy for a missing observable stays a re-run rather than a relabel.
    """
    reasons: list[str] = []
    served: dict[str, Any] | None = None
    control = next(
        (
            candidate
            for candidate in registry.get("controls", ())
            if candidate.get("control_id") == record.get("control_id")
        ),
        None,
    )
    kind = control.get("control_kind") if isinstance(control, Mapping) else None
    evidence = record.get("demonstration_evidence")
    evidence = evidence if isinstance(evidence, Mapping) else {}
    source = evidence.get("read_back_from")
    override_unset = record.get("claude_code_subagent_model_unset")

    if kind not in CONTROL_KINDS:
        reasons.append("control_not_registered")
    elif source not in DEMONSTRATION_EVIDENCE_SOURCES:
        reasons.append("observable_read_from_dispatch_request")
    elif kind == "adaptive":
        pre = _route_observation(evidence, "pre_escalation", reasons)
        post = _route_observation(evidence, "post_escalation", reasons)
        if pre is not None and post is not None:
            try:
                expected = next_route(control, str(pre["candidate_route_id"]))
            except ControlContractError:
                expected = None
            if expected is None or post["candidate_route_id"] != expected:
                reasons.append("route_did_not_advance_one_ladder_entry")
            elif (post["model"], post["effort"]) == (pre["model"], pre["effort"]):
                # Matching route identifiers alone are insufficient: the served
                # model and effort must move with them.
                reasons.append("served_route_did_not_move")
            else:
                served = dict(post)
        if override_unset is not True:
            reasons.append("subagent_model_override_not_excluded")
    elif kind == "unpinned":
        observation = _route_observation(evidence, "served_route", reasons)
        pin = control.get("unpinned") if isinstance(control.get("unpinned"), Mapping) else {}
        if observation is not None:
            if (observation["model"], observation["effort"]) != (
                pin.get("pinned_parent_model"),
                pin.get("pinned_parent_effort"),
            ):
                reasons.append("served_route_does_not_match_pinned_parent")
            else:
                served = dict(observation)
        if override_unset is not True:
            reasons.append("subagent_model_override_not_excluded")
    else:
        rows = _record_unit_rows(record)
        parents = [row for row in rows if row.get("spawned_by") is None]
        children = [row for row in rows if row.get("spawned_by") is not None]
        if len(parents) != 1 or len(children) < 2:
            reasons.append("unit_has_fewer_than_two_non_parent_members")
        elif any(_observed_wall_time_ms(row) is None for row in parents + children):
            # FR-031a.5: never satisfied by the members that did report, and
            # never with a missing value read as zero, which would make the
            # inequality trivially true and invert the whole check.
            reasons.append("wall_time_unobserved")
        else:
            parent_wall_time = _observed_wall_time_ms(parents[0])
            child_total = sum(_observed_wall_time_ms(row) for row in children)
            if parent_wall_time >= child_total:
                reasons.append("parallel_inequality_not_met")
            else:
                served = {
                    "parent_wall_time_ms": parent_wall_time,
                    "child_wall_time_ms_sum": child_total,
                    "non_parent_member_count": len(children),
                }

    state = NOT_DEMONSTRATED if reasons else DEMONSTRATED
    recorded_state = record.get("demonstration_state")
    return {
        "control_id": record.get("control_id"),
        "control_kind": kind,
        "demonstration_state": state,
        "reasons": sorted(set(reasons)),
        "read_back_from": source,
        "served": served,
        "recorded_state": recorded_state,
        "relabel_refused": recorded_state != state,
        "claude_code_subagent_model_unset": override_unset,
    }


def _isolation_root(pair: Mapping[str, Any], member: str, path: str) -> str | None:
    value = pair.get(member)
    if isinstance(value, str) and ("/" in value or "\\" in value or value.startswith("~")):
        raise ControlContractError(
            f"{path}.{member} records {value!r}; a cache root is recorded as a digest and never "
            "as a filesystem path"
        )
    if value is not None and not (isinstance(value, str) and DIGEST_RE.match(value)):
        raise ControlContractError(f"{path}.{member} is not a sha256 digest: {value!r}")
    return value


def validate_isolation_pair(
    pair: Any, path: str, arm_id: str, arms: list[str] | None = None
) -> dict[str, Any]:
    """One recorded arm pair, read fail-closed.

    Shared by the single-record reading in :func:`validate_smoke_record` and the
    whole-series claim in :func:`evaluate_cache_isolation`, so one recorded pair
    cannot be admissible on one path and refused on the other. ``arms`` is the
    series membership when there is a series to check against; a single record
    knows only its own ``arm_id``.
    """
    if not isinstance(pair, Mapping):
        raise ControlContractError(f"{path} is not a pair record")
    if PRECOMMITMENT_MEMBER in pair:
        raise ControlContractError(
            f"{path} offers the {PRECOMMITMENT_MEMBER!r} precommitment as the "
            "observation; a precommitment that arms will be isolated is not evidence "
            "that they were"
        )
    paired = pair.get("paired_arm_id")
    if arms is not None:
        if paired not in arms or paired == arm_id:
            raise ControlContractError(
                f"{path} pairs {paired!r}, which is not another arm of this series"
            )
    elif not isinstance(paired, str) or not paired or paired == arm_id:
        raise ControlContractError(
            f"{path} pairs {paired!r}, which is not another arm than {arm_id!r}"
        )
    status = pair.get("status")
    if status not in ISOLATION_STATUSES:
        raise ControlContractError(
            f"{path} records status {status!r}, outside the frozen closed set "
            f"{list(ISOLATION_STATUSES)}"
        )
    own = _isolation_root(pair, "arm_cache_root_digest", path)
    other = _isolation_root(pair, "paired_arm_cache_root_digest", path)
    if status == ISOLATION_DISJOINT and (
        own is None or other is None or pair.get("roots_disjoint") is not True
    ):
        raise ControlContractError(
            f"{path} claims {ISOLATION_DISJOINT!r} without both root digests and a true "
            "disjointness flag; it can never be asserted with absent evidence"
        )
    return {
        "paired_arm_id": paired,
        "status": status,
        "roots_disjoint": pair.get("roots_disjoint"),
        "arm_cache_root_digest": own,
        "paired_arm_cache_root_digest": other,
        "failure_code": ISOLATION_FAILURE_CODES.get(status),
        "failure_plane": (
            failure_plane_for(ISOLATION_FAILURE_CODES[status])
            if status in ISOLATION_FAILURE_CODES
            else None
        ),
    }


def read_record_cache_isolation(record: Mapping[str, Any]) -> dict[str, Any]:
    """FR-032, read off the one record a live smoke actually produces.

    The whole-series completeness check needs every arm and so belongs to
    :func:`evaluate_cache_isolation`. What one record can answer on its own is
    whether the pairs it *did* record observed disjoint cache state, and that
    answer is what makes ``observed_cache_isolation`` a requirement rather than
    a decoration.
    """
    observations = record.get("observed_cache_isolation")
    if not isinstance(observations, list) or not observations:
        raise ControlContractError(
            "observed_cache_isolation records no pair; FR-032's claim is discharged pairwise "
            "and an empty list discharges nothing"
        )
    arm_id = str(record.get("arm_id"))
    pairs = [
        validate_isolation_pair(pair, f"observed_cache_isolation[{position}]", arm_id)
        for position, pair in enumerate(observations)
    ]
    seen: dict[str, str] = {}
    for entry in pairs:
        paired = str(entry["paired_arm_id"])
        if paired in seen:
            raise ControlContractError(
                f"observed_cache_isolation records the pair {arm_id!r}/{paired!r} twice"
            )
        seen[paired] = str(entry["status"])
    not_disjoint = sorted(
        paired for paired, status in seen.items() if status != ISOLATION_DISJOINT
    )
    return {
        "arm_id": arm_id,
        "pairs": pairs,
        "all_pairs_disjoint": not not_disjoint,
        "pairs_not_disjoint": not_disjoint,
    }


def evaluate_cache_isolation(series: Any) -> dict[str, Any]:
    """FR-032 and FR-032a: the claim is pairwise over every unordered arm pair.

    Recording only consecutive runs would leave the first-to-last pair unchecked,
    which is a case FR-032 forbids rather than one it excuses.
    """
    if not isinstance(series, list) or len(series) < 2:
        raise ControlContractError("cache isolation is claimed over a series of arms")

    arms: list[str] = []
    for index, arm in enumerate(series):
        arm_id = arm.get("arm_id") if isinstance(arm, Mapping) else None
        if not isinstance(arm_id, str) or not arm_id:
            raise ControlContractError(f"series[{index}] records no arm_id")
        if arm_id in arms:
            raise ControlContractError(f"series[{index}] repeats arm {arm_id!r}")
        arms.append(arm_id)

    recorded: dict[frozenset[str], dict[str, Any]] = {}
    for arm in series:
        arm_id = str(arm["arm_id"])
        observations = arm.get("observed_cache_isolation")
        if not isinstance(observations, list) or not observations:
            raise ControlContractError(f"{arm_id} records no observed_cache_isolation")
        for position, pair in enumerate(observations):
            path = f"{arm_id}.observed_cache_isolation[{position}]"
            read = validate_isolation_pair(pair, path, arm_id, arms)
            status = read["status"]

            key = frozenset({arm_id, str(read["paired_arm_id"])})
            entry = {
                "pair": sorted(key),
                "status": status,
                "roots_disjoint": read["roots_disjoint"],
                "arm_cache_root_digest": read["arm_cache_root_digest"],
                "paired_arm_cache_root_digest": read["paired_arm_cache_root_digest"],
                "failure_code": read["failure_code"],
                "failure_plane": read["failure_plane"],
            }
            existing = recorded.get(key)
            if existing is not None and existing["status"] != status:
                raise ControlContractError(
                    f"{path}: the two arms of {sorted(key)} record different isolation statuses "
                    f"({existing['status']!r} and {status!r})"
                )
            recorded[key] = entry

    expected = {
        frozenset({left, right})
        for position, left in enumerate(arms)
        for right in arms[position + 1:]
    }
    missing = sorted(sorted(pair) for pair in expected - set(recorded))
    if missing:
        raise ControlContractError(
            f"the isolation claim is discharged over every unordered arm pair; {missing} is "
            "unrecorded, leaving that pair unchecked"
        )

    invalidated = sorted({
        arm
        for key, entry in recorded.items()
        if entry["status"] != ISOLATION_DISJOINT
        for arm in key
    })
    return {
        "arms": arms,
        "pairs": [recorded[key] for key in sorted(recorded, key=sorted)],
        "all_pairs_disjoint": not invalidated,
        "invalidated_arms": invalidated,
    }


__all__ = (
    "API_KEY_REFUSAL_REASON",
    "BOUND_MEMBERS",
    "CACHE_DIAGNOSTIC_CEILINGS",
    "CACHE_QUANTITY_CEILINGS",
    "CACHE_WRITE_TTL_CLASSES",
    "CLAUDE_AUTHENTICATION_MODES",
    "CLAUDE_ENVIRONMENT_CONTRACT_MEMBERS",
    "CLEAN_TERMINAL_STATE",
    "CONTRACT_ROOT",
    "CONTROL_KINDS",
    "ControlContractError",
    "DEMONSTRATION_EVIDENCE_SOURCES",
    "DEMONSTRATION_REASONS",
    "DEMONSTRATED",
    "DEMONSTRATION_STATES",
    "DISPATCH_REQUEST_SOURCE",
    "EVIDENCE_ADMISSIBILITY",
    "FIXTURE_ROOT",
    "FROZEN_CACHE_TTL_CLASSES",
    "FROZEN_EFFORT_LADDER",
    "FROZEN_FAILURE_CODES",
    "FROZEN_FAILURE_PLANES",
    "FROZEN_PARETO_DIMENSIONS",
    "FROZEN_PARTITION_ENTRIES_PATH",
    "FROZEN_RAW_TOKEN_MEMBERS",
    "FROZEN_REGISTRY_PATH",
    "FROZEN_REGISTRY_SCHEMA_PATH",
    "FROZEN_REPLAY_PATH",
    "FROZEN_ROUTE_PROOF_MEMBERS",
    "FROZEN_SCORE_BUNDLE_SCHEMA_PATH",
    "FROZEN_TERMINAL_STATES",
    "ISOLATION_DISJOINT",
    "ISOLATION_FAILURE_CODES",
    "ISOLATION_STATUSES",
    "NONE_SENTINEL",
    "NOT_DEMONSTRATED",
    "PARENT_CHILD_GRAPH_MEMBERS",
    "POLICY_RESPONSES",
    "RAW_TOKEN_CEILING_MEMBER",
    "RAW_TOKEN_CEILING_QUANTITY_MEMBERS",
    "RAW_TOKEN_IDENTITY_SUMMANDS",
    "REF_PREFIX",
    "REGISTRY_SCHEMA",
    "REPLAY_KINDS",
    "REPLAY_SCHEMA",
    "ROUTE_OBSERVABLES",
    "SERVICE_REROUTE_DISPOSITION_REASON",
    "SERVICE_REROUTE_FAILURE_CODE",
    "SIGNAL_SOURCES",
    "SMOKE_COUNTING_SCOPE",
    "SMOKE_RECORD_KIND",
    "SMOKE_RECORD_REQUIRED",
    "SMOKE_WALL_CLOCK_READING",
    "TOPOLOGY_DESCRIPTOR_MEMBERS",
    "admissible_authentication_modes",
    "advance_clean_streak",
    "aggregate_objective",
    "aggregate_raw_tokens_and_cache",
    "assert_closed_at_three",
    "assert_reserved_partition_untouched",
    "candidate_code_for",
    "classify_service_reroute",
    "control_digest",
    "document_bytes_digest",
    "evaluate_bounds",
    "evaluate_cache_isolation",
    "evaluate_demonstration",
    "load_contract",
    "load_registry",
    "next_route",
    "pinned_parent_document",
    "previous_route",
    "replay",
    "require_utc_timestamp",
    "reserved_partition_entry",
    "resolve_response",
    "shared_environment_authentication_modes",
    "unit_members",
    "validate_control_specializations",
    "validate_escalation_ladder",
    "validate_instance",
    "validate_orchestration_control",
    "validate_registry",
    "validate_signal_maps",
    "validate_smoke_record",
    "validate_unpinned_control",
    "verify_car_003_bindings",
    "worst_terminal_state",
)
