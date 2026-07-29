#!/usr/bin/env python3
"""Twin-handoff record completeness: both-directions derivation against the committed artifacts.

The twin-handoff record is how the Codex-side twin learns what this side froze.
It is only useful if it is complete, so this module re-derives its factual
categories from the committed contract documents, frozen instances, and registry
entries and diffs in **both** directions: a delivered member missing from the
record fails, and a recorded member absent from the artifacts fails too. It also
holds the mirror-obligation and sanctioned-divergence rules.

The record itself lives under ``docs/ai/specs/.process/`` — cross-platform
coordination, not repository validation — and never inside the test tree. It is
**located by what it describes** rather than named: see :func:`live_handoff_record`
for why a permanently-registered suite test must not hard-code one spec's
artifact path.

Every check is offline and makes zero live model calls.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
LIB_DIR = TEST_ROOT / "lib"
LAYER6_LIB_DIR = TEST_ROOT / "layer6-efficiency" / "lib"
for _path in (LIB_DIR, LAYER6_LIB_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from test_result import run_counted  # noqa: E402

try:  # G56R-004 T007 deliverable — absent until the Codex mirror helpers land.
    import codex_policy_controls  # type: ignore[import-not-found]  # noqa: E402
except ImportError:  # pragma: no cover - exercised only during the T006 RED phase
    codex_policy_controls = None  # type: ignore[assignment]


PROCESS_ROOT = REPO_ROOT / "docs" / "ai" / "specs" / ".process"

CONTRACTS_DIR = TEST_ROOT / "layer6-efficiency" / "contracts-claude"
FIXTURES_DIR = TEST_ROOT / "layer6-efficiency" / "fixtures-controls"
REGISTRY_SCHEMA = CONTRACTS_DIR / "policy-control-registry.schema.json"
COMPARISON_SCHEMA = CONTRACTS_DIR / "control-comparison.schema.json"
REGISTRY_INSTANCE = FIXTURES_DIR / "policy-control-registry.json"
COMPARISON_INSTANCE = FIXTURES_DIR / "control-comparison.json"
PARTITION_INSTANCE = FIXTURES_DIR / "partition-registry-entries.json"

CAR_004_HANDOFF = PROCESS_ROOT / "CAR-004-twin-handoff.md"
G56R_CONTRACTS_DIR = TEST_ROOT / "layer6-efficiency" / "contracts-codex-specification"
G56R_FIXTURES_DIR = TEST_ROOT / "layer6-efficiency" / "fixtures-codex-controls"
G56R_REGISTRY_SCHEMA = G56R_CONTRACTS_DIR / "policy-control-registry.schema.json"
G56R_REGISTRY_INSTANCE = G56R_FIXTURES_DIR / "policy-control-registry.json"

CAR_003_ID_PREFIX = "https://racecraft.dev/schemas/car-003/"
CAR_003_ADDITIVE_RECORDS_ID = f"{CAR_003_ID_PREFIX}car-003-additive-records.schema.json"


def live_handoff_record() -> Path | None:
    """The handoff record describing the contracts this module derives from.

    Located by what it *describes* rather than by a filename carrying a spec ID.
    A permanently-registered suite test naming one spec's ``.process/`` artifact
    is what made the CAR-003 contracts load-bearing and forced a relocation
    before that spec could be archived; hard-coding a name here would rebuild
    that trap. Several handoff records coexist under ``.process/`` — each one
    names the contract documents it hands off, so the right record is the one
    naming the registry schema committed in this test tree.

    Returns ``None`` once that record has been archived away. The contracts it
    described stay in the test tree, but there is no live record left to
    reconcile them against, and the module says so instead of failing on a
    missing file.
    """
    if not PROCESS_ROOT.is_dir():
        return None
    registry_id = json.loads(REGISTRY_SCHEMA.read_text(encoding="utf-8"))["$id"]
    for path in sorted(PROCESS_ROOT.glob("*-twin-handoff.md")):
        if registry_id in path.read_text(encoding="utf-8"):
            return path
    return None


RECORD_PATH = live_handoff_record()

# Categories 1-6 are re-derived here; 7 and 8 are authored decision semantics and
# guard behaviors that add no schema member. [FR-034a, research D12]
DERIVED_CATEGORIES = (1, 2, 3, 4, 5, 6)
AUTHORED_CATEGORIES = (7, 8)

OBLIGATIONS = ("mirror_required", "sanctioned_divergence", "car_owned")
REQUIRED_ENTRY_FIELDS = (
    "category",
    "member_id",
    "contract_id",
    "hash_relevant",
    "requirement",
    "rationale",
    "mirror_obligation",
)
REQUIREMENT_PATTERN = re.compile(r"^FR-\d{3}[a-z]?(?:\.\d+)?$")

# FR-035a keeps the divergence confined to enumeration values, so it may not be
# classified against a contract document, a declared member, a frozen numeric, or
# a decision-semantics entry.
DIVERGENCE_INELIGIBLE_CATEGORIES = (1, 2, 6, 7)
DIVERGENCE_FIELDS = (
    "member_id",
    "category",
    "claude_side_authority",
    "codex_side_authority",
    "why_platform_value_not_logic_divergence",
    "expected_twin_action",
    "status",
)

RECONCILIATION_HEADING = "## Reconciliation candidates"
RECONCILIATION_STATEMENT = "There are zero reconciliation candidates at publication."
PUBLISHED_PATTERN = re.compile(r"^\*\*Published\*\*: (\d{4}-\d{2}-\d{2})$", re.MULTILINE)
NOTIFIED_PATTERN = re.compile(r"^\*\*Notified\*\*: (\S.*)$", re.MULTILINE)

EMPTY_DIFFERENCES: dict[str, list[str]] = {
    "missing_from_record": [],
    "absent_from_artifacts": [],
    "mismatched": [],
    "duplicated": [],
}

_JSON_BLOCK = re.compile(r"^```json\n(.*?)^```", re.MULTILINE | re.DOTALL)


# --------------------------------------------------------------------------
# Record parsing
# --------------------------------------------------------------------------


def parse_record(text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return the mirror-membership block and the sanctioned-divergence block.

    The record carries prose for a human reader plus exactly two fenced JSON
    blocks, in that order. [research D12]
    """
    blocks = _JSON_BLOCK.findall(text)
    if len(blocks) != 2:
        raise AssertionError(
            f"the record must carry exactly two fenced JSON blocks, found {len(blocks)}"
        )
    return json.loads(blocks[0]), json.loads(blocks[1])


# --------------------------------------------------------------------------
# Derivation of categories 1-6 from the committed artifacts
# --------------------------------------------------------------------------


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _escape(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def _walk(node: Any, pointer: str, visit: Callable[[Any, str], None]) -> None:
    visit(node, pointer)
    if isinstance(node, dict):
        for key, value in node.items():
            _walk(value, f"{pointer}/{_escape(str(key))}", visit)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            _walk(value, f"{pointer}/{index}", visit)


def _resolve(document: Any, pointer: str) -> Any:
    node = document
    for token in pointer.lstrip("#").split("/"):
        if not token:
            continue
        node = node[int(token)] if isinstance(node, list) else node[token]
    return node


def _instance_identity(path: Path) -> str:
    """The platform-neutral identity of a frozen instance.

    Sites are addressed as ``<document identity>#<JSON Pointer>`` rather than by
    repository path, because the twin's own copies sit at different paths.
    """
    document = _load(path)
    for key in ("registry_id", "comparison_id", "fixture_kind"):
        if key in document:
            return str(document[key])
    raise AssertionError(f"{path.name} declares no document identity")


def _control_pointer(registry: Any, control_kind: str) -> str:
    for index, control in enumerate(registry["controls"]):
        if control.get("control_kind") == control_kind:
            return f"#/controls/{index}"
    raise AssertionError(f"the registry declares no {control_kind} control")


def _document_facts() -> dict[tuple[int, str], dict[str, Any]]:
    """Category 1 — contract documents by ``$id``, ``schema_version``, and bytes."""
    facts: dict[tuple[int, str], dict[str, Any]] = {}
    for path in (REGISTRY_SCHEMA, COMPARISON_SCHEMA):
        document = _load(path)
        schema_id = document["$id"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        facts[(1, schema_id)] = {
            "category": 1,
            "member_id": schema_id,
            "contract_id": schema_id,
            "hash_relevant": False,
            "path": path.relative_to(REPO_ROOT).as_posix(),
            "schema_version": document["properties"]["schema_version"]["const"],
            "sha256": f"sha256:{digest}",
        }
    return facts


def _declared_member_facts() -> dict[tuple[int, str], dict[str, Any]]:
    """Category 2 — every declared object, by JSON Pointer, with its required subset."""
    facts: dict[tuple[int, str], dict[str, Any]] = {}
    for path in (REGISTRY_SCHEMA, COMPARISON_SCHEMA):
        document = _load(path)
        schema_id = document["$id"]

        def visit(node: Any, pointer: str, schema_id: str = schema_id) -> None:
            if not isinstance(node, dict):
                return
            if node.get("type") != "object" or "properties" not in node:
                return
            member_id = f"{schema_id}{pointer}"
            facts[(2, member_id)] = {
                "category": 2,
                "member_id": member_id,
                "contract_id": schema_id,
                "hash_relevant": True,
                "properties": sorted(node["properties"]),
                "required": sorted(node.get("required", [])),
            }

        _walk(document, "#", visit)
    return facts


def _closed_enumeration_facts() -> dict[tuple[int, str], dict[str, Any]]:
    """Category 3 — every ``enum`` and ``const`` with every one of its members."""
    facts: dict[tuple[int, str], dict[str, Any]] = {}
    for path in (REGISTRY_SCHEMA, COMPARISON_SCHEMA):
        document = _load(path)
        schema_id = document["$id"]
        groups: dict[tuple[str, str], list[str]] = {}
        values: dict[tuple[str, str], Any] = {}

        def visit(node: Any, pointer: str) -> None:
            if not isinstance(node, dict):
                return
            for kind in ("enum", "const"):
                if kind in node:
                    key = (kind, json.dumps(node[kind], sort_keys=True))
                    groups.setdefault(key, []).append(pointer)
                    values[key] = node[kind]

        _walk(document, "#", visit)
        for key, sites in groups.items():
            kind = key[0]
            members = values[key] if kind == "enum" else [values[key]]
            ordered = sorted(f"{schema_id}{site}" for site in sites)
            facts[(3, ordered[0])] = {
                "category": 3,
                "member_id": ordered[0],
                "contract_id": schema_id,
                "hash_relevant": True,
                "kind": kind,
                "members": members,
                "sites": ordered,
            }
    return facts


def _identifier_facts() -> dict[tuple[int, str], dict[str, Any]]:
    """Category 4 — the stable identifiers the twin binds rather than re-derives."""
    registry = _load(REGISTRY_INSTANCE)
    comparison = _load(COMPARISON_INSTANCE)
    partitions = _load(PARTITION_INSTANCE)
    registry_identity = _instance_identity(REGISTRY_INSTANCE)
    comparison_identity = _instance_identity(COMPARISON_INSTANCE)
    partition_identity = _instance_identity(PARTITION_INSTANCE)
    registry_schema_id = _load(REGISTRY_SCHEMA)["$id"]
    comparison_schema_id = _load(COMPARISON_SCHEMA)["$id"]
    orchestration = _control_pointer(registry, "orchestration_changing")

    sightings: list[tuple[str, str, str, bool, str]] = [
        (
            "registry_id",
            registry["registry_id"],
            f"{registry_identity}#/registry_id",
            True,
            registry_schema_id,
        ),
        (
            "comparison_id",
            comparison["comparison_id"],
            f"{comparison_identity}#/comparison_id",
            True,
            comparison_schema_id,
        ),
        (
            "topology_id",
            _resolve(registry, f"{orchestration}/orchestration_changing/topology_descriptor")[
                "topology_id"
            ],
            f"{registry_identity}{orchestration}/orchestration_changing"
            "/topology_descriptor/topology_id",
            True,
            registry_schema_id,
        ),
        (
            "partition_id",
            comparison["reserved_partition_binding"]["id"],
            f"{comparison_identity}#/reserved_partition_binding/id",
            False,
            CAR_003_ADDITIVE_RECORDS_ID,
        ),
    ]
    for index, control in enumerate(registry["controls"]):
        sightings.append(
            (
                "control_id",
                control["control_id"],
                f"{registry_identity}#/controls/{index}/control_id",
                True,
                registry_schema_id,
            )
        )
    for index, entry in enumerate(partitions["entries"]):
        sightings.append(
            (
                "partition_id",
                entry["partition_id"],
                f"{partition_identity}#/entries/{index}/partition_id",
                False,
                CAR_003_ADDITIVE_RECORDS_ID,
            )
        )
    for path in (REGISTRY_SCHEMA, COMPARISON_SCHEMA):
        schema_id = _load(path)["$id"]
        sightings.append(("schema_id", schema_id, f"{schema_id}#/$id", False, schema_id))

    facts: dict[tuple[int, str], dict[str, Any]] = {}
    for kind, value, site, hash_relevant, contract_id in sightings:
        entry = facts.setdefault(
            (4, value),
            {
                "category": 4,
                "member_id": value,
                "contract_id": contract_id,
                "hash_relevant": hash_relevant,
                "kind": kind,
                "sites": [],
            },
        )
        entry["sites"].append(site)
    for entry in facts.values():
        entry["sites"] = sorted(entry["sites"])
    return facts


def _binding_facts() -> dict[tuple[int, str], dict[str, Any]]:
    """Category 5 — every frozen CAR-003 ``$id`` and digest this feature binds."""
    facts: dict[tuple[int, str], dict[str, Any]] = {}
    for instance_path, schema_path in (
        (REGISTRY_INSTANCE, REGISTRY_SCHEMA),
        (COMPARISON_INSTANCE, COMPARISON_SCHEMA),
    ):
        document = _load(instance_path)
        identity = _instance_identity(instance_path)
        schema_id = _load(schema_path)["$id"]
        found: dict[tuple[str, str], list[str]] = {}

        def visit(node: Any, pointer: str) -> None:
            if not isinstance(node, dict) or set(node) != {"id", "digest"}:
                return
            if not str(node["id"]).startswith(CAR_003_ID_PREFIX):
                return
            found.setdefault((node["id"], node["digest"]), []).append(pointer)

        _walk(document, "#", visit)
        for (bound_id, digest), sites in found.items():
            ordered = sorted(f"{identity}{site}" for site in sites)
            facts[(5, ordered[0])] = {
                "category": 5,
                "member_id": ordered[0],
                "contract_id": schema_id,
                "hash_relevant": True,
                "bound_id": bound_id,
                "digest": digest,
                "sites": ordered,
            }
    return facts


def _numeric_facts() -> dict[tuple[int, str], dict[str, Any]]:
    """Category 6 — every frozen numeric with its unit and comparison direction."""
    facts: dict[tuple[int, str], dict[str, Any]] = {}
    registry_schema_id = _load(REGISTRY_SCHEMA)["$id"]
    comparison_schema_id = _load(COMPARISON_SCHEMA)["$id"]
    schema_by_instance = {
        REGISTRY_INSTANCE: registry_schema_id,
        COMPARISON_INSTANCE: comparison_schema_id,
    }

    # Bounds declare their own unit and direction, so they are discovered by shape.
    for instance_path, schema_id in schema_by_instance.items():
        document = _load(instance_path)
        identity = _instance_identity(instance_path)

        def visit(node: Any, pointer: str, schema_id: str = schema_id, identity: str = identity) -> None:
            if not isinstance(node, dict) or set(node) != {"value", "unit", "direction"}:
                return
            member_id = f"{identity}{pointer}"
            facts[(6, member_id)] = {
                "category": 6,
                "member_id": member_id,
                "contract_id": schema_id,
                "hash_relevant": True,
                "value": node["value"],
                "unit": node["unit"],
                "direction": node["direction"],
            }

        _walk(document, "#", visit)

    # The per-component relative margin map carries a class beside its direction.
    comparison = _load(COMPARISON_INSTANCE)
    comparison_identity = _instance_identity(COMPARISON_INSTANCE)
    for component, margin in comparison["dominance_rule"]["margin_map"].items():
        member_id = f"{comparison_identity}#/dominance_rule/margin_map/{_escape(component)}"
        facts[(6, member_id)] = {
            "category": 6,
            "member_id": member_id,
            "contract_id": comparison_schema_id,
            "hash_relevant": True,
            "value": margin.get("relative_margin"),
            "unit": margin["unit"],
            "direction": margin["direction"],
            "class": margin["class"],
        }

    # The remaining frozen scalars state no unit beside themselves, so this check
    # is the authority on the unit and direction each is read under.
    registry = _load(REGISTRY_INSTANCE)
    adaptive = _control_pointer(registry, "adaptive")
    scalars = (
        (
            REGISTRY_INSTANCE,
            f"{adaptive}/adaptive/de_escalation_clean_pass_threshold",
            "clean objectives",
            "at_or_above",
        ),
        (COMPARISON_INSTANCE, "#/confidence_method/confidence_level", "probability", "at_or_above"),
        (COMPARISON_INSTANCE, "#/confidence_method/alpha", "probability", "at_or_below"),
        (COMPARISON_INSTANCE, "#/multiplicity_position/family_wise_alpha", "probability", "at_or_below"),
    )
    for instance_path, pointer, unit, direction in scalars:
        document = _load(instance_path)
        member_id = f"{_instance_identity(instance_path)}{pointer}"
        facts[(6, member_id)] = {
            "category": 6,
            "member_id": member_id,
            "contract_id": schema_by_instance[instance_path],
            "hash_relevant": True,
            "value": _resolve(document, pointer),
            "unit": unit,
            "direction": direction,
        }
    return facts


def derive_membership() -> dict[tuple[int, str], dict[str, Any]]:
    """Re-derive categories 1-6 from the committed artifacts. [FR-034a]"""
    derived: dict[tuple[int, str], dict[str, Any]] = {}
    for producer in (
        _document_facts,
        _declared_member_facts,
        _closed_enumeration_facts,
        _identifier_facts,
        _binding_facts,
        _numeric_facts,
    ):
        derived.update(producer())
    return derived


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------


def diff_membership(
    derived: dict[tuple[int, str], dict[str, Any]], entries: list[dict[str, Any]]
) -> dict[str, list[str]]:
    """Diff the record against the artifacts in both directions. [FR-034a, SC-011]"""
    recorded: dict[tuple[int, str], dict[str, Any]] = {}
    duplicated: list[str] = []
    for entry in entries:
        if entry.get("category") not in DERIVED_CATEGORIES:
            continue
        key = (entry["category"], entry.get("member_id"))
        if key in recorded:
            duplicated.append(f"{key[0]} {key[1]}")
            continue
        recorded[key] = entry

    missing = [f"{key[0]} {key[1]}" for key in sorted(set(derived) - set(recorded))]
    absent = [f"{key[0]} {key[1]}" for key in sorted(set(recorded) - set(derived))]
    mismatched: list[str] = []
    for key in sorted(set(derived) & set(recorded)):
        facts = derived[key]
        entry = recorded[key]
        for field, value in facts.items():
            if entry.get(field) != value:
                mismatched.append(f"{key[0]} {key[1]}: {field}")
        undeclared = set(entry) - set(facts) - set(REQUIRED_ENTRY_FIELDS)
        for field in sorted(undeclared):
            mismatched.append(f"{key[0]} {key[1]}: undeclared field {field}")
    return {
        "missing_from_record": sorted(missing),
        "absent_from_artifacts": sorted(absent),
        "mismatched": sorted(mismatched),
        "duplicated": sorted(duplicated),
    }


def obligation_errors(entries: list[dict[str, Any]]) -> list[str]:
    """Every entry carries the seven required fields and exactly one obligation. [FR-034]"""
    errors: list[str] = []
    for entry in entries:
        label = f"{entry.get('category')} {entry.get('member_id')}"
        for field in REQUIRED_ENTRY_FIELDS:
            if field not in entry:
                errors.append(f"{label}: missing {field}")
        obligation = entry.get("mirror_obligation")
        if isinstance(obligation, list):
            errors.append(f"{label}: carries {len(obligation)} obligations, not one")
        elif obligation is not None and obligation not in OBLIGATIONS:
            errors.append(f"{label}: obligation {obligation!r} is outside the closed set")
        requirement = entry.get("requirement", "")
        if not isinstance(requirement, str) or not REQUIREMENT_PATTERN.match(requirement):
            errors.append(f"{label}: requirement {requirement!r} is not a CAR-004 requirement")
        rationale = entry.get("rationale", "")
        if not isinstance(rationale, str) or not rationale.strip() or "\n" in rationale:
            errors.append(f"{label}: rationale is empty or is not one line")
    return errors


def divergence_errors(
    entries: list[dict[str, Any]], divergences: list[dict[str, Any]]
) -> list[str]:
    """The sanctioned-divergence set is closed at exactly one entry. [FR-035, FR-035a]"""
    errors: list[str] = []
    claimed = [
        entry for entry in entries if entry.get("mirror_obligation") == "sanctioned_divergence"
    ]
    if len(claimed) != 1:
        errors.append(f"{len(claimed)} entries claim the sanctioned-divergence obligation, not 1")
    if len(divergences) != 1:
        errors.append(f"the divergence block carries {len(divergences)} entries, not 1")
    if errors:
        return errors

    entry = claimed[0]
    divergence = divergences[0]
    for field in DIVERGENCE_FIELDS:
        if field not in divergence:
            errors.append(f"the divergence entry is missing {field}")
    if divergence.get("member_id") != entry["member_id"]:
        errors.append("the divergence entry names a member no entry classifies as one")
    if divergence.get("category") != entry["category"]:
        errors.append("the divergence entry and its member disagree on the category")
    if entry["category"] in DIVERGENCE_INELIGIBLE_CATEGORIES:
        errors.append(
            f"the divergence is classified against category {entry['category']}, "
            "which FR-035a keeps mirror-identical"
        )
    if divergence.get("expected_twin_action") != "none":
        errors.append("the divergence records a twin action other than none")
    if divergence.get("status") != "closed_nothing_owed":
        errors.append("the divergence is not closed with nothing owed")
    return errors


def reconciliation_errors(text: str, entries: list[dict[str, Any]]) -> list[str]:
    """At publication the reconciliation candidate list is explicitly empty. [FR-036a]"""
    errors: list[str] = []
    if RECONCILIATION_HEADING not in text:
        errors.append("the record carries no reconciliation candidate section")
    if RECONCILIATION_STATEMENT not in text:
        errors.append("the empty reconciliation candidate list is left implicit")
    for entry in entries:
        if entry.get("reconciliation_candidate"):
            errors.append(f"{entry.get('member_id')} is flagged as a reconciliation candidate")
        if entry.get("mirror_obligation") == "reconciliation_candidate":
            errors.append(f"{entry.get('member_id')} carries a reconciliation-candidate obligation")
    return errors


def publication_errors(text: str, entries: list[dict[str, Any]]) -> list[str]:
    """The record states its publication date and notification reference. [FR-037a]"""
    errors: list[str] = []
    if not PUBLISHED_PATTERN.search(text):
        errors.append("the record states no publication date")
    if not NOTIFIED_PATTERN.search(text):
        errors.append("the record states no G56R-004 notification reference")
    if RECORD_PATH is not None:
        for entry in entries:
            if RECORD_PATH.name in str(entry.get("member_id")):
                errors.append("the record enrolls itself as a hash-relevant member")
    return errors


class G56R004TwinMirrorTests(unittest.TestCase):
    """T006 RED: the Codex registry subset mirrors CAR-004 with one divergence."""

    def setUp(self) -> None:
        self.assertIsNotNone(
            codex_policy_controls,
            "codex_policy_controls is not importable; T007 must implement G56R-004 mirror helpers",
        )
        self.module = codex_policy_controls

    def mirror_report(self) -> dict[str, Any]:
        return self.module.validate_car_004_twin_mirror(
            car_handoff_path=CAR_004_HANDOFF,
            codex_registry_schema_path=G56R_REGISTRY_SCHEMA,
            codex_registry_instance_path=G56R_REGISTRY_INSTANCE,
        )

    def test_categories_one_through_six_match_car_004_in_both_directions(self) -> None:
        report = self.mirror_report()
        self.assertEqual(report["compared_categories"], list(DERIVED_CATEGORIES))
        self.assertEqual(report["differences"], EMPTY_DIFFERENCES)

    def test_the_only_sanctioned_divergence_is_justified_high_effort(self) -> None:
        report = self.mirror_report()
        self.assertEqual(
            report["sanctioned_divergences"],
            [
                {
                    "category": 3,
                    "car_value": "orchestration_changing",
                    "codex_value": "justified_high_effort",
                    "unchanged_values": ["adaptive", "unpinned"],
                }
            ],
        )

    def test_registry_zeros_units_enums_and_numerics_are_preserved(self) -> None:
        report = self.mirror_report()
        preserved = report["preserved_literals"]
        for literal_group in ("zeros", "units", "enums", "numerics"):
            with self.subTest(literal_group=literal_group):
                self.assertTrue(preserved[literal_group])
        self.assertEqual(preserved["zeros"]["max_confirmation_entries"], 0)
        self.assertEqual(preserved["units"]["raw_token_ceiling"], "tokens")
        self.assertIn("justified_high_effort", preserved["enums"]["control_kind"])
        self.assertEqual(preserved["numerics"]["raw_token_ceiling"], 1000000)


class TwinHandoffCompletenessTests(unittest.TestCase):
    def setUp(self) -> None:
        if RECORD_PATH is None:
            self.skipTest(
                "no live handoff record under docs/ai/specs/.process/ names the registry schema "
                "committed in this test tree; the record this module reconciles has been archived"
            )
        self.record_text = RECORD_PATH.read_text(encoding="utf-8")

    def test_validator_module_directory_is_on_the_import_path(self) -> None:
        self.assertTrue(LAYER6_LIB_DIR.is_dir())
        self.assertIn(str(LAYER6_LIB_DIR), sys.path)

    def test_handoff_records_live_outside_the_test_tree(self) -> None:
        self.assertTrue(PROCESS_ROOT.is_dir())
        self.assertNotIn(TEST_ROOT, PROCESS_ROOT.parents)

    # --- record shape -----------------------------------------------------

    def test_the_record_parses_into_exactly_two_machine_read_blocks(self) -> None:
        entries, divergences = parse_record(self.record_text)
        self.assertIsInstance(entries, list)
        self.assertIsInstance(divergences, list)
        self.assertTrue(entries, "the mirror-membership block is empty")

    def test_every_derived_category_is_represented_in_the_record(self) -> None:
        entries, _ = parse_record(self.record_text)
        recorded = {entry["category"] for entry in entries}
        for category in DERIVED_CATEGORIES:
            self.assertIn(category, recorded, f"category {category} carries no entry")

    def test_the_authored_categories_are_represented_in_the_record(self) -> None:
        entries, _ = parse_record(self.record_text)
        recorded = {entry["category"] for entry in entries}
        for category in AUTHORED_CATEGORIES:
            self.assertIn(category, recorded, f"category {category} carries no entry")

    # --- FR-034a: both-directions derivation ------------------------------

    def test_categories_one_through_six_diff_to_zero_in_both_directions(self) -> None:
        entries, _ = parse_record(self.record_text)
        differences = diff_membership(derive_membership(), entries)
        self.assertEqual(
            differences,
            EMPTY_DIFFERENCES,
            "the record and the committed artifacts disagree",
        )

    def test_a_delivered_member_absent_from_the_record_fails(self) -> None:
        entries, _ = parse_record(self.record_text)
        for category in DERIVED_CATEGORIES:
            seeded = [
                entry for entry in copy.deepcopy(entries) if entry["category"] != category
            ]
            differences = diff_membership(derive_membership(), seeded)
            self.assertTrue(
                differences["missing_from_record"],
                f"dropping every category {category} entry was not reported",
            )

    def test_a_recorded_member_absent_from_the_artifacts_fails(self) -> None:
        entries, _ = parse_record(self.record_text)
        seeded = copy.deepcopy(entries)
        invented = copy.deepcopy(seeded[0])
        invented["member_id"] = f"{invented['member_id']}-invented"
        seeded.append(invented)
        differences = diff_membership(derive_membership(), seeded)
        self.assertTrue(
            differences["absent_from_artifacts"],
            "an invented member was not reported",
        )

    def test_a_derived_fact_that_drifts_from_the_artifacts_fails(self) -> None:
        entries, _ = parse_record(self.record_text)
        seeded = copy.deepcopy(entries)
        for entry in seeded:
            if entry["category"] == 1:
                entry["sha256"] = "sha256:" + "0" * 64
                break
        differences = diff_membership(derive_membership(), seeded)
        self.assertTrue(
            differences["mismatched"],
            "a drifted committed-bytes digest was not reported",
        )

    def test_a_duplicated_member_fails(self) -> None:
        entries, _ = parse_record(self.record_text)
        seeded = copy.deepcopy(entries)
        seeded.append(copy.deepcopy(seeded[0]))
        differences = diff_membership(derive_membership(), seeded)
        self.assertTrue(differences["duplicated"], "a duplicated member was not reported")

    def test_an_undeclared_field_on_a_derived_entry_fails(self) -> None:
        entries, _ = parse_record(self.record_text)
        seeded = copy.deepcopy(entries)
        seeded[0]["invented_field"] = "unmirrorable"
        differences = diff_membership(derive_membership(), seeded)
        self.assertTrue(
            differences["mismatched"],
            "an undeclared field on a derived entry was not reported",
        )

    # --- FR-034: obligations ----------------------------------------------

    def test_every_entry_carries_exactly_one_obligation_from_the_closed_set(self) -> None:
        entries, _ = parse_record(self.record_text)
        self.assertEqual(obligation_errors(entries), [])
        self.assertEqual(
            OBLIGATIONS, ("mirror_required", "sanctioned_divergence", "car_owned")
        )

    def test_an_entry_carrying_no_obligation_is_rejected(self) -> None:
        entries, _ = parse_record(self.record_text)
        seeded = copy.deepcopy(entries)
        del seeded[0]["mirror_obligation"]
        self.assertTrue(obligation_errors(seeded))

    def test_an_entry_carrying_more_than_one_obligation_is_rejected(self) -> None:
        entries, _ = parse_record(self.record_text)
        seeded = copy.deepcopy(entries)
        seeded[0]["mirror_obligation"] = ["mirror_required", "car_owned"]
        self.assertTrue(obligation_errors(seeded))

    def test_an_obligation_outside_the_closed_set_is_rejected(self) -> None:
        entries, _ = parse_record(self.record_text)
        seeded = copy.deepcopy(entries)
        seeded[0]["mirror_obligation"] = "reconciliation_candidate"
        self.assertTrue(obligation_errors(seeded))

    def test_every_obligation_is_publishable_because_none_is_a_candidate(self) -> None:
        entries, _ = parse_record(self.record_text)
        self.assertNotIn("reconciliation_candidate", OBLIGATIONS)
        self.assertEqual(reconciliation_errors(self.record_text, entries), [])

    def test_an_entry_flagged_as_a_reconciliation_candidate_is_rejected(self) -> None:
        entries, _ = parse_record(self.record_text)
        seeded = copy.deepcopy(entries)
        seeded[0]["reconciliation_candidate"] = True
        self.assertTrue(
            reconciliation_errors(self.record_text, seeded)
        )

    def test_the_reconciliation_candidate_list_is_explicitly_empty(self) -> None:
        text = self.record_text
        self.assertIn(RECONCILIATION_HEADING, text)
        self.assertIn(RECONCILIATION_STATEMENT, text)
        entries, _ = parse_record(text)
        self.assertEqual(reconciliation_errors(text, entries), [])

    def test_a_record_that_leaves_the_candidate_list_unstated_is_rejected(self) -> None:
        text = self.record_text.replace(RECONCILIATION_STATEMENT, "")
        entries, _ = parse_record(text)
        self.assertTrue(reconciliation_errors(text, entries))

    # --- FR-035, FR-035a: sanctioned divergence ---------------------------

    def test_the_sanctioned_divergence_set_is_closed_at_exactly_one_entry(self) -> None:
        entries, divergences = parse_record(self.record_text)
        self.assertEqual(len(divergences), 1)
        self.assertEqual(divergence_errors(entries, divergences), [])

    def test_a_second_sanctioned_divergence_is_rejected(self) -> None:
        entries, divergences = parse_record(self.record_text)
        seeded = copy.deepcopy(divergences)
        seeded.append(copy.deepcopy(seeded[0]))
        self.assertTrue(divergence_errors(entries, seeded))

    def test_a_second_entry_claiming_the_divergence_obligation_is_rejected(self) -> None:
        entries, divergences = parse_record(self.record_text)
        seeded = copy.deepcopy(entries)
        for entry in seeded:
            if entry["mirror_obligation"] != "sanctioned_divergence":
                entry["mirror_obligation"] = "sanctioned_divergence"
                break
        self.assertTrue(divergence_errors(seeded, divergences))

    def test_a_divergence_classified_against_an_ineligible_category_is_rejected(self) -> None:
        entries, divergences = parse_record(self.record_text)
        self.assertEqual(DIVERGENCE_INELIGIBLE_CATEGORIES, (1, 2, 6, 7))
        for category in DIVERGENCE_INELIGIBLE_CATEGORIES:
            seeded_entries = copy.deepcopy(entries)
            seeded_divergences = copy.deepcopy(divergences)
            for entry in seeded_entries:
                if entry["mirror_obligation"] == "sanctioned_divergence":
                    entry["mirror_obligation"] = "mirror_required"
            for entry in seeded_entries:
                if entry["category"] == category:
                    entry["mirror_obligation"] = "sanctioned_divergence"
                    seeded_divergences[0]["member_id"] = entry["member_id"]
                    seeded_divergences[0]["category"] = category
                    break
            self.assertTrue(
                divergence_errors(seeded_entries, seeded_divergences),
                f"a divergence classified against category {category} was accepted",
            )

    def test_the_divergence_entry_is_reachable_without_either_roadmap(self) -> None:
        _, divergences = parse_record(self.record_text)
        entry = divergences[0]
        for field in DIVERGENCE_FIELDS:
            self.assertIn(field, entry)
        self.assertEqual(entry["expected_twin_action"], "none")
        self.assertEqual(entry["status"], "closed_nothing_owed")

    # --- FR-037a: publication -------------------------------------------

    def test_the_record_states_its_publication_date_and_notification_reference(self) -> None:
        text = self.record_text
        entries, _ = parse_record(text)
        self.assertEqual(publication_errors(text, entries), [])

    def test_a_record_with_no_notification_reference_is_rejected(self) -> None:
        text = self.record_text
        entries, _ = parse_record(text)
        seeded = "\n".join(
            line for line in text.splitlines() if not line.startswith("**Notified**:")
        )
        self.assertTrue(publication_errors(seeded, entries))


if __name__ == "__main__":
    suite = unittest.TestSuite()
    for case in (G56R004TwinMirrorTests, TwinHandoffCompletenessTests):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    raise SystemExit(run_counted(suite, label="test-twin-handoff-completeness"))
