#!/usr/bin/env python3
"""The runner's stdlib JSON Schema validator asserts every keyword it meets."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
sys.path[:0] = [str(PLUGIN_ROOT), str(REPO_ROOT / "tests/speckit-pro/lib")]

from speckit_pro_runner.helpers.read_only import (  # noqa: E402
    ANNOTATION_SCHEMA_KEYWORDS,
    ASSERTED_SCHEMA_KEYWORDS,
    json_schema_failures,
)
from test_result import run_counted  # noqa: E402

SCHEMA_MAP_KEYWORDS = ("properties", "patternProperties", "$defs")
SCHEMA_VALUE_KEYWORDS = ("items", "additionalProperties", "propertyNames", "not", "if", "then", "else", "contains")
SCHEMA_LIST_KEYWORDS = ("allOf", "anyOf", "oneOf", "prefixItems")


def failures(value: Any, schema: dict[str, Any]) -> list[dict[str, Any]]:
    return json_schema_failures(value, schema, schema, "$")


def rules(value: Any, schema: dict[str, Any]) -> set[str]:
    return {failure["rule"].removeprefix("packet.schema.") for failure in failures(value, schema)}


def schema_keywords(schema: Any, found: set[str]) -> None:
    if not isinstance(schema, dict):
        return
    for keyword, child in schema.items():
        found.add(keyword)
        if keyword in SCHEMA_MAP_KEYWORDS and isinstance(child, dict):
            for nested in child.values():
                schema_keywords(nested, found)
        elif keyword in SCHEMA_VALUE_KEYWORDS:
            schema_keywords(child, found)
        elif keyword in SCHEMA_LIST_KEYWORDS and isinstance(child, list):
            for nested in child:
                schema_keywords(nested, found)


class KeywordAssertions(unittest.TestCase):
    def test_unique_items_rejects_duplicates_by_json_equality(self) -> None:
        schema = {"type": "array", "uniqueItems": True}
        self.assertIn("unique_items", rules([1, 1], schema))
        self.assertIn("unique_items", rules([{"a": 1}, {"a": 1}], schema))
        self.assertEqual([], failures([1, True, "1"], schema))

    def test_any_of_requires_at_least_one_match(self) -> None:
        schema = {"anyOf": [{"type": "string"}, {"type": "integer"}]}
        self.assertIn("any_of", rules(1.5, schema))
        self.assertEqual([], failures("x", schema))

    def test_property_names_apply_to_every_key(self) -> None:
        schema = {"type": "object", "propertyNames": {"pattern": "^[a-z]+$"}}
        self.assertIn("property_names", rules({"Upper": 1}, schema))
        self.assertEqual([], failures({"lower": 1}, schema))

    def test_pattern_properties_validate_and_are_not_additional(self) -> None:
        schema = {
            "type": "object",
            "patternProperties": {"^x-": {"type": "string"}},
            "additionalProperties": False,
        }
        self.assertIn("type", rules({"x-a": 1}, schema))
        self.assertEqual([], failures({"x-a": "s"}, schema))
        self.assertIn("additional_properties", rules({"y": "s"}, schema))

    def test_max_length_counts_characters(self) -> None:
        schema = {"type": "string", "maxLength": 3}
        self.assertIn("max_length", rules("abcd", schema))
        self.assertEqual([], failures("abc", schema))

    def test_dependent_required_needs_the_named_keys(self) -> None:
        schema = {"type": "object", "dependentRequired": {"a": ["b"]}}
        self.assertIn("dependent_required", rules({"a": 1}, schema))
        self.assertEqual([], failures({"a": 1, "b": 2}, schema))
        self.assertEqual([], failures({"b": 2}, schema))

    def test_contains_needs_one_matching_item(self) -> None:
        schema = {"type": "array", "contains": {"const": "x"}}
        self.assertIn("contains", rules(["y"], schema))
        self.assertIn("contains", rules([], schema))
        self.assertEqual([], failures(["y", "x"], schema))

    def test_exclusive_minimum_rejects_the_bound(self) -> None:
        schema = {"type": "number", "exclusiveMinimum": 0}
        self.assertIn("exclusive_minimum", rules(0, schema))
        self.assertEqual([], failures(0.5, schema))

    def test_max_properties_bounds_the_object(self) -> None:
        schema = {"type": "object", "maxProperties": 1}
        self.assertIn("max_properties", rules({"a": 1, "b": 2}, schema))
        self.assertEqual([], failures({"a": 1}, schema))


class UnknownKeywordsFailClosed(unittest.TestCase):
    def test_an_unknown_keyword_is_a_definition_failure(self) -> None:
        schema = {"type": "array", "unevaluatedItems": False}
        found = failures([1], schema)
        self.assertEqual(["packet.schema.definition"], [failure["rule"] for failure in found])
        self.assertIn("unevaluatedItems", found[0]["message"])

    def test_an_unknown_keyword_inside_a_probed_subschema_still_fails(self) -> None:
        bad = {"type": "string", "unevaluatedItems": False}
        probes = {
            "anyOf": {"anyOf": [bad, {"type": "integer"}]},
            "oneOf": {"oneOf": [bad, {"type": "integer"}]},
            "not": {"not": bad},
            "if": {"if": bad, "then": {"type": "string"}},
            "contains": {"type": "array", "contains": bad},
            "propertyNames": {"type": "object", "propertyNames": bad},
        }
        values = {"contains": ["x"], "propertyNames": {"x": 1}}
        for keyword, schema in probes.items():
            with self.subTest(keyword=keyword):
                self.assertIn("definition", rules(values.get(keyword, "x"), schema))

    def test_annotation_keywords_assert_nothing(self) -> None:
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "urn:example",
            "$comment": "note",
            "title": "t",
            "description": "d",
            "default": 1,
            "examples": [1],
            "format": "date-time",
            "deprecated": False,
            "readOnly": False,
            "writeOnly": False,
            "type": "string",
        }
        self.assertEqual([], failures("not a date", schema))

    def test_the_keyword_sets_do_not_overlap(self) -> None:
        self.assertEqual(set(), ASSERTED_SCHEMA_KEYWORDS & ANNOTATION_SCHEMA_KEYWORDS)


class ShippedSchemas(unittest.TestCase):
    def test_every_shipped_schema_uses_only_known_keywords(self) -> None:
        schemas = sorted(PLUGIN_ROOT.rglob("*.schema.json"))
        self.assertTrue(schemas, "no shipped schemas found")
        known = ASSERTED_SCHEMA_KEYWORDS | ANNOTATION_SCHEMA_KEYWORDS
        for path in schemas:
            with self.subTest(schema=path.name):
                found: set[str] = set()
                schema_keywords(json.loads(path.read_text(encoding="utf-8")), found)
                self.assertEqual(set(), found - known)


if __name__ == "__main__":
    suite = unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromTestCase(case)
        for case in (KeywordAssertions, UnknownKeywordsFailClosed, ShippedSchemas)
    )
    raise SystemExit(run_counted(suite, label="test-json-schema-validator"))
