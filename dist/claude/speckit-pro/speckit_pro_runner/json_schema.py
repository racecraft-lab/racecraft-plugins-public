"""Stdlib JSON Schema validator shared by the runner and the shipped autopilot scripts.

It asserts the JSON Schema 2020-12 keywords the shipped contracts use and
imports nothing beyond the standard library, so a script installed with the
plugin can load it without pulling in the runner helpers.
"""

from __future__ import annotations

import re
from typing import Any


# The stdlib validator asserts the JSON Schema 2020-12 keywords the shipped
# contracts use. Annotation keywords are accepted and assert nothing; `format`
# is annotation-only, as in the 2020-12 default vocabulary. Any other keyword
# is a definition failure, so a constraint the validator cannot check never
# passes on nothing.
ASSERTED_SCHEMA_KEYWORDS = frozenset({
    "$ref", "oneOf", "anyOf", "allOf", "not", "if", "then", "else", "type", "const", "enum",
    "properties", "patternProperties", "additionalProperties", "propertyNames", "required",
    "dependentRequired", "minProperties", "maxProperties",
    "minItems", "maxItems", "prefixItems", "items", "contains", "uniqueItems",
    "minLength", "maxLength", "pattern", "minimum", "exclusiveMinimum", "maximum",
})
ANNOTATION_SCHEMA_KEYWORDS = frozenset({
    "$schema", "$id", "$defs", "$comment", "title", "description", "default", "examples",
    "format", "deprecated", "readOnly", "writeOnly",
})


Failures = list[dict[str, Any]]


def json_schema_failures(
    value: Any,
    schema: Any,
    root_schema: dict[str, Any],
    field: str,
) -> Failures:
    if schema is True:
        return []
    if schema is False or not isinstance(schema, dict):
        return [schema_failure("definition", field, "Value is rejected by the packet schema.")]

    failures: Failures = []
    for keyword in sorted(schema.keys() - ASSERTED_SCHEMA_KEYWORDS - ANNOTATION_SCHEMA_KEYWORDS):
        failures.append(schema_failure("definition", field, f"Unsupported schema keyword: {keyword}"))
    _check_reference(value, schema, root_schema, field, failures)
    _check_one_of(value, schema, root_schema, field, failures)
    if not _check_type(value, schema, field, failures):
        return failures
    for check in _VALUE_CHECKS:
        check(value, schema, root_schema, field, failures)
    return failures


def _check_reference(value: Any, schema: dict[str, Any], root_schema: dict[str, Any], field: str, failures: Failures) -> None:
    reference = schema.get("$ref")
    if not isinstance(reference, str):
        return
    resolved = resolve_local_schema_reference(reference, root_schema)
    if resolved is None:
        failures.append(schema_failure("definition", field, f"Unresolvable schema reference: {reference}"))
    else:
        failures.extend(json_schema_failures(value, resolved, root_schema, field))


def _check_one_of(value: Any, schema: dict[str, Any], root_schema: dict[str, Any], field: str, failures: Failures) -> None:
    one_of = schema.get("oneOf")
    if not isinstance(one_of, list):
        return
    matches = sum(json_schema_probe(value, candidate, root_schema, field, failures) for candidate in one_of)
    if matches != 1:
        failures.append(schema_failure("one_of", field, "Value must match exactly one allowed packet schema shape."))


def _check_type(value: Any, schema: dict[str, Any], field: str, failures: Failures) -> bool:
    """Return False, after recording the failure, when the value has the wrong type."""
    expected_type = schema.get("type")
    if expected_type is None or json_schema_type_matches(value, expected_type):
        return True
    expected = ", ".join(expected_type) if isinstance(expected_type, list) else str(expected_type)
    failures.append(schema_failure("type", field, f"Value must have schema type: {expected}."))
    return False


def _check_const_enum(value: Any, schema: dict[str, Any], _root: dict[str, Any], field: str, failures: Failures) -> None:
    if "const" in schema and not json_values_equal(value, schema["const"]):
        failures.append(schema_failure("const", field, "Value does not match the schema constant."))
    enum = schema.get("enum")
    if isinstance(enum, list) and not any(json_values_equal(value, candidate) for candidate in enum):
        failures.append(schema_failure("enum", field, "Value is not one of the schema's allowed values."))


def _check_alternatives(value: Any, schema: dict[str, Any], root_schema: dict[str, Any], field: str, failures: Failures) -> None:
    any_of = schema.get("anyOf")
    if isinstance(any_of, list) and not any(
        [json_schema_probe(value, candidate, root_schema, field, failures) for candidate in any_of]
    ):
        failures.append(schema_failure("any_of", field, "Value must match at least one allowed schema shape."))
    all_of = schema.get("allOf")
    if isinstance(all_of, list):
        for candidate in all_of:
            failures.extend(json_schema_failures(value, candidate, root_schema, field))


def _check_conditional_and_not(value: Any, schema: dict[str, Any], root_schema: dict[str, Any], field: str, failures: Failures) -> None:
    condition = schema.get("if")
    if isinstance(condition, dict):
        matched = json_schema_probe(value, condition, root_schema, field, failures)
        branch = schema.get("then") if matched else schema.get("else")
        if branch is not None:
            failures.extend(json_schema_failures(value, branch, root_schema, field))
    negated = schema.get("not")
    if isinstance(negated, dict) and json_schema_probe(value, negated, root_schema, field, failures):
        failures.append(schema_failure("not", field, "Value matches a packet schema shape that is forbidden here."))


def _schema_container(schema: dict[str, Any], keyword: str, kind: type) -> Any:
    """The keyword's value when it is a `kind` (dict or list), else an empty one."""
    found = schema.get(keyword)
    return found if isinstance(found, kind) else kind()


def _check_property_counts(value: Any, schema: dict[str, Any], _root: dict[str, Any], field: str, failures: Failures) -> None:
    if not isinstance(value, dict):
        return
    minimum_properties = schema.get("minProperties")
    if isinstance(minimum_properties, int) and len(value) < minimum_properties:
        noun = "property" if minimum_properties == 1 else "properties"
        failures.append(schema_failure("min_properties", field, f"Object must contain at least {minimum_properties} {noun}."))
    maximum_properties = schema.get("maxProperties")
    if isinstance(maximum_properties, int) and len(value) > maximum_properties:
        failures.append(schema_failure("max_properties", field, f"Object must contain at most {maximum_properties} properties."))


def _check_dependent_required(value: Any, schema: dict[str, Any], _root: dict[str, Any], field: str, failures: Failures) -> None:
    if not isinstance(value, dict):
        return
    for trigger, dependencies in _schema_container(schema, "dependentRequired", dict).items():
        if trigger not in value or not isinstance(dependencies, list):
            continue
        for key in dependencies:
            if isinstance(key, str) and key not in value:
                missing_field = schema_child_field(field, key)
                failures.append(
                    schema_failure(
                        "dependent_required",
                        missing_field,
                        f"Schema field {missing_field} is required when {schema_child_field(field, str(trigger))} is present.",
                    )
                )


def _check_property_names(value: Any, schema: dict[str, Any], root_schema: dict[str, Any], field: str, failures: Failures) -> None:
    name_schema = schema.get("propertyNames")
    if not isinstance(value, dict) or name_schema is None:
        return
    for key in sorted(value.keys()):
        key_field = schema_child_field(field, str(key))
        if not json_schema_probe(key, name_schema, root_schema, key_field, failures):
            failures.append(schema_failure("property_names", key_field, "Property name is not allowed by the schema."))


def _check_required_and_properties(value: Any, schema: dict[str, Any], root_schema: dict[str, Any], field: str, failures: Failures) -> None:
    if not isinstance(value, dict):
        return
    for key in _schema_container(schema, "required", list):
        if isinstance(key, str) and key not in value:
            missing_field = schema_child_field(field, key)
            failures.append(schema_failure("required", missing_field, f"Required schema field is missing: {missing_field}."))
    for key, child_schema in _schema_container(schema, "properties", dict).items():
        if key in value:
            failures.extend(json_schema_failures(value[key], child_schema, root_schema, schema_child_field(field, key)))


def _check_additional_properties(value: Any, schema: dict[str, Any], root_schema: dict[str, Any], field: str, failures: Failures) -> None:
    if not isinstance(value, dict):
        return
    pattern_matched: set[str] = set()
    for key in sorted(value.keys()):
        for key_pattern, child_schema in _schema_container(schema, "patternProperties", dict).items():
            try:
                matched = re.search(key_pattern, key) is not None
            except re.error:
                failures.append(schema_failure("definition", field, f"Invalid patternProperties pattern: {key_pattern}"))
                continue
            if matched:
                pattern_matched.add(key)
                failures.extend(json_schema_failures(value[key], child_schema, root_schema, schema_child_field(field, key)))
    additional_keys = value.keys() - _schema_container(schema, "properties", dict).keys() - pattern_matched
    additional = schema.get("additionalProperties")
    for key in sorted(additional_keys):
        extra_field = schema_child_field(field, str(key))
        if additional is False:
            failures.append(schema_failure("additional_properties", extra_field, f"Schema does not allow packet field: {extra_field}."))
        elif isinstance(additional, dict):
            failures.extend(json_schema_failures(value[key], additional, root_schema, extra_field))


def _check_array_items(value: Any, schema: dict[str, Any], root_schema: dict[str, Any], field: str, failures: Failures) -> None:
    if not isinstance(value, list):
        return
    minimum_items = schema.get("minItems")
    if isinstance(minimum_items, int) and len(value) < minimum_items:
        failures.append(schema_failure("min_items", field, f"Array must contain at least {minimum_items} item(s)."))
    maximum_items = schema.get("maxItems")
    if isinstance(maximum_items, int) and len(value) > maximum_items:
        failures.append(schema_failure("max_items", field, f"Array must contain at most {maximum_items} item(s)."))
    prefix_items = _schema_container(schema, "prefixItems", list)
    for index, child_schema in enumerate(prefix_items[: len(value)]):
        failures.extend(json_schema_failures(value[index], child_schema, root_schema, f"{field}[{index}]"))
    item_schema = schema.get("items")
    if item_schema is not None:
        for index in range(len(prefix_items), len(value)):
            failures.extend(json_schema_failures(value[index], item_schema, root_schema, f"{field}[{index}]"))


def _check_array_contents(value: Any, schema: dict[str, Any], root_schema: dict[str, Any], field: str, failures: Failures) -> None:
    if not isinstance(value, list):
        return
    contains = schema.get("contains")
    if contains is not None and not any(
        [json_schema_probe(item, contains, root_schema, field, failures) for item in value]
    ):
        failures.append(schema_failure("contains", field, "Array must contain at least one item matching the schema."))
    if schema.get("uniqueItems") is True:
        identities = [json_value_identity(item) for item in value]
        if len(set(identities)) != len(identities):
            failures.append(schema_failure("unique_items", field, "Array items must be unique."))


def _check_string(value: Any, schema: dict[str, Any], _root: dict[str, Any], field: str, failures: Failures) -> None:
    if not isinstance(value, str):
        return
    minimum_length = schema.get("minLength")
    if isinstance(minimum_length, int) and len(value) < minimum_length:
        failures.append(schema_failure("min_length", field, f"String must contain at least {minimum_length} character(s)."))
    maximum_length = schema.get("maxLength")
    if isinstance(maximum_length, int) and len(value) > maximum_length:
        failures.append(schema_failure("max_length", field, f"String must contain at most {maximum_length} character(s)."))
    pattern = schema.get("pattern")
    if isinstance(pattern, str):
        try:
            matches = re.search(pattern, value) is not None
        except re.error:
            matches = False
        if not matches:
            failures.append(schema_failure("pattern", field, "String does not match the packet schema pattern."))


# keyword, failure rule, message template, and the comparison that fails the bound
_NUMBER_BOUNDS = (
    ("minimum", "minimum", "Number must be at least {bound}.", lambda value, bound: value < bound),
    ("exclusiveMinimum", "exclusive_minimum", "Number must be greater than {bound}.", lambda value, bound: value <= bound),
    ("maximum", "maximum", "Number must be at most {bound}.", lambda value, bound: value > bound),
)


def _check_number(value: Any, schema: dict[str, Any], _root: dict[str, Any], field: str, failures: Failures) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return
    for keyword, rule, template, violates in _NUMBER_BOUNDS:
        bound = schema.get(keyword)
        if isinstance(bound, (int, float)) and violates(value, bound):
            failures.append(schema_failure(rule, field, template.format(bound=bound)))


_VALUE_CHECKS = (
    _check_const_enum,
    _check_alternatives,
    _check_conditional_and_not,
    _check_property_counts,
    _check_dependent_required,
    _check_property_names,
    _check_required_and_properties,
    _check_additional_properties,
    _check_array_items,
    _check_array_contents,
    _check_string,
    _check_number,
)


def json_schema_probe(
    value: Any,
    schema: Any,
    root_schema: dict[str, Any],
    field: str,
    failures: list[dict[str, Any]],
) -> bool:
    """Report whether value matches schema, keeping any definition failures.

    Applicators such as anyOf, oneOf, not, if, contains, and propertyNames only
    need to know whether a subschema matched, but an unsupported keyword inside
    that subschema must still fail the whole validation.
    """
    found = json_schema_failures(value, schema, root_schema, field)
    for failure in found:
        if failure["rule"] == "packet.schema.definition" and failure not in failures:
            failures.append(failure)
    return not found


def resolve_local_schema_reference(reference: str, root_schema: dict[str, Any]) -> Any | None:
    if not reference.startswith("#/"):
        return None
    resolved: Any = root_schema
    for token in reference[2:].split("/"):
        key = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(resolved, dict) or key not in resolved:
            return None
        resolved = resolved[key]
    return resolved


def json_schema_type_matches(value: Any, expected: Any) -> bool:
    expected_types = expected if isinstance(expected, list) else [expected]
    type_checks = {
        "array": lambda candidate: isinstance(candidate, list),
        "boolean": lambda candidate: isinstance(candidate, bool),
        "integer": lambda candidate: isinstance(candidate, int) and not isinstance(candidate, bool),
        "null": lambda candidate: candidate is None,
        "number": lambda candidate: isinstance(candidate, (int, float)) and not isinstance(candidate, bool),
        "object": lambda candidate: isinstance(candidate, dict),
        "string": lambda candidate: isinstance(candidate, str),
    }
    return any(isinstance(name, str) and name in type_checks and type_checks[name](value) for name in expected_types)


def json_values_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    return type(left) is type(right) and left == right


def json_value_identity(value: Any) -> Any:
    """A hashable key under which two values are equal exactly when JSON says so."""
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return (type(value).__name__, value)
    if isinstance(value, (int, float)):
        return ("number", value)
    if isinstance(value, list):
        return ("array", tuple(json_value_identity(item) for item in value))
    if isinstance(value, dict):
        return ("object", tuple(sorted((key, json_value_identity(item)) for key, item in value.items())))
    return ("other", repr(value))


def schema_child_field(parent: str, child: str) -> str:
    return f"{parent}.{child}" if parent else child


def schema_failure(keyword: str, field: str, message: str) -> dict[str, Any]:
    return {
        "rule": f"packet.schema.{keyword}",
        "field": field or "packet",
        "message": message,
    }
