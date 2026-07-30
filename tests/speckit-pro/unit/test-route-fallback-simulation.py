#!/usr/bin/env python3
"""Route availability, fallback, and recovery simulation: contracts, walk, and replay.

This module is the deterministic coverage for the reference route-resolution
simulator — the preferred-then-fallback walk, the two closed reason-code
vocabularies, the closed effort ladder, and the byte-identical replay of a pinned
scenario corpus.

Contract-structural cases read the three committed schema documents under
``tests/speckit-pro/layer6-efficiency/contracts-claude/``; module-contract cases
exercise ``tests/speckit-pro/layer6-efficiency/lib/claude_route_fallback.py``.

Every check is offline: the simulator is a pure function of a synthetic
environment snapshot, so this module makes zero live model calls and performs no
dispatch.
"""

from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
LIB_DIR = TEST_ROOT / "lib"
LAYER6_LIB_DIR = TEST_ROOT / "layer6-efficiency" / "lib"
for _path in (LIB_DIR, LAYER6_LIB_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from test_result import run_counted  # noqa: E402

# The shared fail-closed schema engine, imported read-only: it is the loader every
# consumer of this contracts directory already goes through, so these cases check
# the committed documents against the engine that will validate instances against
# them rather than against a second reader authored here.
from claude_policy_controls import ControlContractError, load_contract, validate_instance  # noqa: E402

# FR-014a: the ONE canonical serializer, imported rather than re-declared. This is a
# deliberate break with local habit — all six existing canonical_json occurrences
# under unit/ define their own copy, and two of those append a trailing newline the
# library function does not. A local copy here would be a second serializer, and
# because the pinning comparison passes the pinned report through the same local
# copy, a discrepancy against the simulator's real output would CANCEL rather than
# fail.
from claude_successor_freeze import canonical_json  # noqa: E402

try:  # CAR-005 deliverable — absent until the simulator module is implemented.
    import claude_route_fallback  # type: ignore[import-not-found]  # noqa: E402
except ImportError:  # pragma: no cover - exercised only before the module lands
    claude_route_fallback = None  # type: ignore[assignment]


CONTRACT_ROOT = TEST_ROOT / "layer6-efficiency" / "contracts-claude"
JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_ID_PREFIX = "https://racecraft.dev/schemas/car-005/"
SCHEMA_VERSION = "1.0.0"

# The three documents FR-016 permits, and exactly three: no fourth
# shared-definitions document exists, because a cross-document ``$ref`` is what a
# shared document would require and the engine refuses one.
CONTRACT_FILENAMES = (
    "route-policy.schema.json",
    "environment-snapshot-projection.schema.json",
    "route-resolution-report.schema.json",
)


class CommittedContractIdentityTests(unittest.TestCase):
    """FR-016: three committed documents, each self-identifying and version-pinned.

    Identity is asserted before shape because every later case reads one of these
    documents by name. A document that is absent, malformed, or carrying another
    feature's ``$id`` would otherwise surface as a confusing shape failure rather
    than as the missing contract it is.
    """

    def load(self, filename: str) -> dict[str, object]:
        path = CONTRACT_ROOT / filename
        self.assertTrue(path.is_file(), f"{filename} is not committed under contracts-claude/")
        return load_contract(path)

    def test_the_three_documents_are_committed_and_load_through_the_shared_engine(self) -> None:
        for filename in CONTRACT_FILENAMES:
            with self.subTest(document=filename):
                self.assertIsInstance(self.load(filename), dict)

    def test_each_document_declares_the_shared_json_schema_dialect(self) -> None:
        for filename in CONTRACT_FILENAMES:
            with self.subTest(document=filename):
                self.assertEqual(self.load(filename).get("$schema"), JSON_SCHEMA_DIALECT)

    def test_each_document_identifies_itself_by_its_capability_named_id(self) -> None:
        for filename in CONTRACT_FILENAMES:
            with self.subTest(document=filename):
                self.assertEqual(self.load(filename).get("$id"), SCHEMA_ID_PREFIX + filename)

    def test_each_document_pins_its_schema_version_with_const(self) -> None:
        for filename in CONTRACT_FILENAMES:
            with self.subTest(document=filename):
                properties = self.load(filename).get("properties")
                self.assertIsInstance(properties, dict)
                self.assertEqual(properties.get("schema_version"), {"const": SCHEMA_VERSION})


class SimulatorSerializationSurfaceTests(unittest.TestCase):
    """FR-014a and FR-030: the module's serialization surface and its fail-closed helper.

    Serialization is asserted before any walk exists because it is what every later
    byte comparison runs through. A serializer that appended a trailing newline, or
    that a local copy shadowed, would make replay byte-identity unfalsifiable rather
    than merely wrong.
    """

    def setUp(self) -> None:
        self.assertIsNotNone(claude_route_fallback, "claude_route_fallback is not importable")
        self.module = claude_route_fallback

    def test_serialize_report_returns_the_shared_canonical_serializer_output(self) -> None:
        report = {"outcome": "resolved", "agent": "fixture-required-executor", "diagnostics": []}
        self.assertEqual(self.module.serialize_report(report), canonical_json(report))

    def test_serialize_report_appends_no_trailing_newline(self) -> None:
        serialized = self.module.serialize_report({"outcome": "no_safe_route"})
        self.assertFalse(serialized.endswith("\n"))

    def test_serialize_report_sorts_keys_so_dict_order_never_reaches_the_bytes(self) -> None:
        forward = self.module.serialize_report({"agent": "fixture-bounded-analyst", "outcome": "resolved"})
        reverse = self.module.serialize_report({"outcome": "resolved", "agent": "fixture-bounded-analyst"})
        self.assertEqual(forward, reverse)
        self.assertEqual(forward, '{"agent":"fixture-bounded-analyst","outcome":"resolved"}')

    def test_the_module_declares_both_closed_vocabularies_and_the_sub_reason_order(self) -> None:
        report_schema = load_contract(CONTRACT_ROOT / "route-resolution-report.schema.json")
        definitions = report_schema["$defs"]
        self.assertEqual(
            list(self.module.RESOLUTION_CODES),
            definitions["resolutionDiagnostic"]["properties"]["code"]["enum"],
        )
        self.assertEqual(
            list(self.module.POLICY_VIOLATION_CODES),
            definitions["policyViolationDiagnostic"]["properties"]["code"]["enum"],
        )
        self.assertEqual(
            list(self.module.SUB_REASON_ORDER),
            definitions["resolutionDiagnostic"]["properties"]["details"]["properties"]["sub_reason"]["enum"],
        )

    def test_the_fail_closed_helper_raises_rather_than_returning_a_partial_verdict(self) -> None:
        self.assertTrue(issubclass(self.module.RouteFallbackError, AssertionError))
        self.assertIsNone(self.module._require(True, "a satisfied condition returns nothing"))
        with self.assertRaises(self.module.RouteFallbackError):
            self.module._require(False, "an unsatisfied condition raises")


# --------------------------------------------------------------------------- #
# Inline fixture builders                                                       #
# --------------------------------------------------------------------------- #
# The corpus pins whole cases; these builders construct the one-off policy and
# snapshot pairs the behavioural cases below need. A builder rather than a literal
# per case is what keeps each case's DIFFERENCE from a clean environment visible:
# ``snapshot_for`` defaults every route to available, bound exactly as pinned,
# fully effort-capable, probe-available, and probe-successful, so a case that
# rejects a route states only the one dimension it degraded.

EFFORT_LADDER = ("low", "medium", "high", "xhigh", "max")
INLINE_BUDGETS = {"max_probe_attempts": 4, "max_retries": 2, "max_candidate_routes": 4}


def route_of(route_id: str, alias: str, model: str, effort: str = "high") -> dict[str, object]:
    return {
        "route_id": route_id,
        "alias": alias,
        "resolved_model": model,
        "effort": effort,
        "qualified": True,
    }


def policy_of(
    preferred: dict[str, object],
    fallbacks: tuple[dict[str, object], ...] = (),
    *,
    name: str = "fixture-required-executor",
    role_class: str = "required_executor",
) -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "agent": {"name": name, "role_class": role_class},
        "preferred_route": preferred,
        "fallback_routes": [dict(each) for each in fallbacks],
        "budgets": dict(INLINE_BUDGETS),
    }


def snapshot_for(
    *routes: dict[str, object],
    available: tuple[str, ...] | None = None,
    bindings: dict[str, str] | None = None,
    efforts: dict[str, list[str]] | None = None,
    probe: dict[str, bool] | None = None,
    invocation: dict[str, str] | None = None,
    changes: tuple[dict[str, str], ...] = (),
) -> dict[str, object]:
    models = [str(each["resolved_model"]) for each in routes]
    return {
        "schema_version": "1.0.0",
        "available_models": list(models) if available is None else list(available),
        "alias_bindings": (
            {str(each["alias"]): str(each["resolved_model"]) for each in routes}
            if bindings is None
            else dict(bindings)
        ),
        "supported_efforts": (
            {model: list(EFFORT_LADDER) for model in models} if efforts is None else dict(efforts)
        ),
        "probe_availability": ({model: True for model in models} if probe is None else dict(probe)),
        "exact_invocation_probe": (
            {model: "success" for model in models} if invocation is None else dict(invocation)
        ),
        "platform_route_changes": [dict(change) for change in changes],
        "available_models_allowlist": list(models),
    }


class SimulatorCaseMixin:
    """Shared access to the simulator module and its walk."""

    def setUp(self) -> None:  # type: ignore[override]
        self.assertIsNotNone(  # type: ignore[attr-defined]
            claude_route_fallback, "claude_route_fallback is not importable"
        )
        self.module = claude_route_fallback

    def resolve(
        self, policy: dict[str, object], snapshot: dict[str, object], overrides: object = None
    ) -> dict[str, object]:
        return self.module.resolve(policy, snapshot, overrides, policy["budgets"])

    def codes(self, report: dict[str, object]) -> list[str]:
        return [str(entry["code"]) for entry in report["diagnostics"]]

    def only_diagnostic(self, report: dict[str, object], code: str) -> dict[str, object]:
        matches = [entry for entry in report["diagnostics"] if entry["code"] == code]
        self.assertEqual(len(matches), 1, f"expected exactly one {code} diagnostic")  # type: ignore[attr-defined]
        return matches[0]


class ResolutionWalkTests(SimulatorCaseMixin, unittest.TestCase):
    """FR-004 and FR-001: the attempt-ordered walk, and its purity.

    Continuation past a rejected route is not asserted here because no rejection
    rule exists yet at this point in the build; each rejection family's own case
    below asserts that the walk moved on to the next declared fallback.
    """

    def test_the_preferred_route_is_attempted_first_and_selected_when_compatible(self) -> None:
        preferred = route_of("preferred-first", "alias-first", "model-first")
        spare = route_of("fallback-spare", "alias-spare", "model-spare")
        policy = policy_of(preferred, (spare,))
        report = self.resolve(policy, snapshot_for(preferred, spare))
        self.assertEqual(report["outcome"], "resolved")
        self.assertEqual(
            report["attempted_routes"],
            [
                {
                    "route_id": "preferred-first",
                    "alias": "alias-first",
                    "resolved_model": "model-first",
                    "effort": "high",
                    "disposition": "selected",
                }
            ],
        )

    def test_attempted_route_entries_carry_no_redundant_index_field(self) -> None:
        preferred = route_of("preferred-only", "alias-only", "model-only")
        policy = policy_of(preferred)
        report = self.resolve(policy, snapshot_for(preferred))
        for entry in report["attempted_routes"]:
            self.assertEqual(
                set(entry), {"route_id", "alias", "resolved_model", "effort", "disposition"}
            )

    def test_the_report_names_its_subject_and_pins_the_document_version(self) -> None:
        preferred = route_of("preferred-subject", "alias-subject", "model-subject")
        policy = policy_of(preferred, name="fixture-bounded-analyst", role_class="bounded_analyst")
        report = self.resolve(policy, snapshot_for(preferred))
        self.assertEqual(report["agent"], "fixture-bounded-analyst")
        self.assertEqual(report["schema_version"], "1.0.0")

    def test_resolve_is_a_pure_function_of_its_four_arguments(self) -> None:
        preferred = route_of("preferred-pure", "alias-pure", "model-pure")
        policy = policy_of(preferred)
        snapshot = snapshot_for(preferred)
        before = (canonical_json(policy), canonical_json(snapshot))
        first = self.module.serialize_report(self.resolve(policy, snapshot))
        second = self.module.serialize_report(self.resolve(policy, snapshot))
        self.assertEqual(first, second)
        self.assertEqual(before, (canonical_json(policy), canonical_json(snapshot)))

    def test_the_declared_budgets_argument_must_match_the_policys_own_declaration(self) -> None:
        preferred = route_of("preferred-budget", "alias-budget", "model-budget")
        policy = policy_of(preferred)
        with self.assertRaises(self.module.RouteFallbackError):
            self.module.resolve(
                policy,
                snapshot_for(preferred),
                None,
                {"max_probe_attempts": 2, "max_retries": 0, "max_candidate_routes": 2},
            )

    def test_load_corpus_fails_closed_on_a_path_that_is_not_committed(self) -> None:
        with self.assertRaises(self.module.RouteFallbackError):
            self.module.load_corpus(path=CONTRACT_ROOT / "no-such-corpus.json")


class PreferredModelUnavailableTests(SimulatorCaseMixin, unittest.TestCase):
    """FR-006: the closed four-member sub-reason vocabulary, staged in evaluation order.

    The order is the mechanism that makes the vocabulary single-valued, not a
    tie-breaking nicety: the first three predicates partition the alias-binding table
    and cannot co-occur, while ``platform_route_changed`` reads a separate snapshot
    array and is disjoint only because it is evaluated last. Two cases below degrade
    two dimensions at once precisely to hold that order down.
    """

    SPARE = route_of("fallback-bound", "alias-bound", "model-bound")

    def spare_binding(self) -> dict[str, str]:
        return {"alias-bound": "model-bound"}

    def report_for(
        self, preferred: dict[str, object], snapshot: dict[str, object]
    ) -> dict[str, object]:
        return self.resolve(policy_of(preferred, (self.SPARE,)), snapshot)

    def test_the_sub_reason_helpers_are_staged_in_the_schemas_declared_order(self) -> None:
        staged = tuple(name for name, _ in self.module.SUB_REASON_STAGES)
        self.assertEqual(staged, tuple(self.module.SUB_REASON_ORDER))

    def test_an_unbound_alias_reports_alias_unresolved_and_names_no_model(self) -> None:
        preferred = route_of("preferred-unbound", "alias-unbound", "model-unbound")
        report = self.report_for(
            preferred, snapshot_for(preferred, self.SPARE, bindings=self.spare_binding())
        )
        entry = self.only_diagnostic(report, "preferred_model_unavailable")
        self.assertEqual(
            entry["details"],
            {
                "alias": "alias-unbound",
                "route_id": "preferred-unbound",
                "sub_reason": "alias_unresolved",
            },
        )
        self.assertEqual(entry["severity"], "warning")
        self.assertEqual(entry["source"], "route-fallback-simulator")
        self.assertEqual(
            entry["remediation"]["actions"],
            ["Re-probe the environment and confirm the pinned alias and resolved model."],
        )

    def test_a_repointed_alias_reports_the_pinned_and_observed_model_pair(self) -> None:
        preferred = route_of("preferred-drift", "alias-drift", "model-pinned")
        snapshot = snapshot_for(
            preferred,
            self.SPARE,
            available=("model-pinned", "model-observed", "model-bound"),
            bindings={"alias-drift": "model-observed", **self.spare_binding()},
        )
        entry = self.only_diagnostic(
            self.report_for(preferred, snapshot), "preferred_model_unavailable"
        )
        self.assertEqual(
            entry["details"],
            {
                "alias": "alias-drift",
                "observed_resolved_model": "model-observed",
                "pinned_resolved_model": "model-pinned",
                "route_id": "preferred-drift",
                "sub_reason": "alias_repointed",
            },
        )

    def test_an_absent_model_reports_the_missing_resolved_model_id(self) -> None:
        preferred = route_of("preferred-gone", "alias-gone", "model-gone")
        snapshot = snapshot_for(preferred, self.SPARE, available=("model-bound",))
        entry = self.only_diagnostic(
            self.report_for(preferred, snapshot), "preferred_model_unavailable"
        )
        self.assertEqual(
            entry["details"],
            {
                "alias": "alias-gone",
                "pinned_resolved_model": "model-gone",
                "route_id": "preferred-gone",
                "sub_reason": "model_absent",
            },
        )

    def test_a_declared_route_change_over_an_intact_binding_reports_platform_route_changed(
        self,
    ) -> None:
        preferred = route_of("preferred-changed", "alias-changed", "model-changed")
        snapshot = snapshot_for(
            preferred,
            self.SPARE,
            changes=({"alias": "alias-changed", "resolved_model": "model-changed"},),
        )
        entry = self.only_diagnostic(
            self.report_for(preferred, snapshot), "preferred_model_unavailable"
        )
        self.assertEqual(
            entry["details"],
            {
                "alias": "alias-changed",
                "observed_resolved_model": "model-changed",
                "pinned_resolved_model": "model-changed",
                "route_id": "preferred-changed",
                "sub_reason": "platform_route_changed",
            },
        )

    def test_a_repointed_alias_outranks_a_declared_route_change_on_the_same_tuple(self) -> None:
        preferred = route_of("preferred-both", "alias-both", "model-both")
        snapshot = snapshot_for(
            preferred,
            self.SPARE,
            available=("model-both", "model-elsewhere", "model-bound"),
            bindings={"alias-both": "model-elsewhere", **self.spare_binding()},
            changes=({"alias": "alias-both", "resolved_model": "model-both"},),
        )
        entry = self.only_diagnostic(
            self.report_for(preferred, snapshot), "preferred_model_unavailable"
        )
        self.assertEqual(entry["details"]["sub_reason"], "alias_repointed")

    def test_an_absent_model_outranks_a_declared_route_change_on_the_same_tuple(self) -> None:
        preferred = route_of("preferred-absent-both", "alias-absent-both", "model-absent-both")
        snapshot = snapshot_for(
            preferred,
            self.SPARE,
            available=("model-bound",),
            changes=({"alias": "alias-absent-both", "resolved_model": "model-absent-both"},),
        )
        entry = self.only_diagnostic(
            self.report_for(preferred, snapshot), "preferred_model_unavailable"
        )
        self.assertEqual(entry["details"]["sub_reason"], "model_absent")

    def test_the_walk_continues_to_the_next_declared_fallback_after_a_rejection(self) -> None:
        preferred = route_of("preferred-rejected", "alias-rejected", "model-rejected")
        snapshot = snapshot_for(preferred, self.SPARE, available=("model-bound",))
        report = self.report_for(preferred, snapshot)
        self.assertEqual(report["outcome"], "resolved")
        self.assertEqual(
            [(entry["route_id"], entry["disposition"]) for entry in report["attempted_routes"]],
            [("preferred-rejected", "rejected"), ("fallback-bound", "selected")],
        )


class EffortUnsupportedTests(SimulatorCaseMixin, unittest.TestCase):
    """FR-007, FR-007a, SC-013: preflight rejection of an unsupported declared effort.

    The documented runtime does **not** fail an unsupported effort — it silently falls
    back to the highest supported level at or below the declared one. Rejecting at
    preflight is a recorded deliberate divergence, not an oversight: a route whose
    declared effort silently degrades is not the tuple the policy pinned, and no report
    field would record the difference. The degradation case below pins that divergence
    so it cannot be "fixed" toward runtime behaviour without failing.
    """

    SPARE = route_of("fallback-ladder", "alias-ladder", "model-ladder", "medium")

    def test_an_unsupported_declared_effort_names_the_declared_and_supported_efforts(self) -> None:
        preferred = route_of("preferred-max", "alias-max", "model-capped", "max")
        snapshot = snapshot_for(
            preferred,
            self.SPARE,
            efforts={
                "model-capped": ["low", "medium", "high"],
                "model-ladder": ["low", "medium", "high"],
            },
        )
        report = self.resolve(policy_of(preferred, (self.SPARE,)), snapshot)
        entry = self.only_diagnostic(report, "effort_unsupported")
        self.assertEqual(
            entry["details"],
            {
                "declared_effort": "max",
                "route_id": "preferred-max",
                "supported_efforts": ["low", "medium", "high"],
            },
        )
        self.assertEqual(entry["severity"], "warning")
        self.assertEqual(
            entry["remediation"]["actions"],
            ["Declare an effort the model's probed capability set supports."],
        )

    def test_a_supported_declared_effort_emits_no_effort_diagnostic(self) -> None:
        preferred = route_of("preferred-supported", "alias-supported", "model-supported", "high")
        snapshot = snapshot_for(preferred, efforts={"model-supported": ["low", "medium", "high"]})
        report = self.resolve(policy_of(preferred), snapshot)
        self.assertEqual(self.codes(report), [])

    def test_the_route_is_rejected_at_preflight_rather_than_degraded_to_a_lower_level(self) -> None:
        preferred = route_of("preferred-degradable", "alias-degradable", "model-degradable", "max")
        snapshot = snapshot_for(
            preferred,
            self.SPARE,
            efforts={
                "model-degradable": ["low", "medium", "high"],
                "model-ladder": ["low", "medium", "high"],
            },
        )
        report = self.resolve(policy_of(preferred, (self.SPARE,)), snapshot)
        self.assertEqual(
            [(entry["route_id"], entry["disposition"]) for entry in report["attempted_routes"]],
            [("preferred-degradable", "rejected"), ("fallback-ladder", "selected")],
        )

    def test_a_route_with_no_resolvable_model_is_not_also_checked_for_effort_support(self) -> None:
        preferred = route_of("preferred-moved", "alias-moved", "model-pin", "max")
        snapshot = snapshot_for(
            preferred,
            self.SPARE,
            available=("model-pin", "model-elsewhere", "model-ladder"),
            bindings={"alias-moved": "model-elsewhere", "alias-ladder": "model-ladder"},
            efforts={
                "model-pin": ["low"],
                "model-elsewhere": ["low"],
                "model-ladder": ["low", "medium", "high"],
            },
        )
        report = self.resolve(policy_of(preferred, (self.SPARE,)), snapshot)
        self.assertEqual(self.codes(report), ["preferred_model_unavailable"])


class CapabilityProbeUnavailableTests(SimulatorCaseMixin, unittest.TestCase):
    """FR-008 and FR-002a: probe unavailability rejects, and absence is never success.

    This is where CAR-002's ``undetermined`` observation lands. It maps to probe
    **unavailability** rather than to ``success`` or ``absent`` because an observation
    from which no availability claim derives is at least as weak as an absent probe, so
    treating it as selectable would be exactly the substitution FR-008 forbids.
    """

    SPARE = route_of("fallback-probed", "alias-probed", "model-probed")

    def test_a_model_with_probing_marked_unavailable_is_rejected(self) -> None:
        preferred = route_of("preferred-unprobed", "alias-unprobed", "model-unprobed")
        snapshot = snapshot_for(
            preferred,
            self.SPARE,
            probe={"model-unprobed": False, "model-probed": True},
            invocation={"model-unprobed": "absent", "model-probed": "success"},
        )
        report = self.resolve(policy_of(preferred, (self.SPARE,)), snapshot)
        entry = self.only_diagnostic(report, "capability_probe_unavailable")
        self.assertEqual(entry["details"], {"route_id": "preferred-unprobed"})
        self.assertEqual(entry["severity"], "warning")
        self.assertEqual(
            entry["remediation"]["actions"],
            ["Re-run capability probing before trusting this route."],
        )

    def test_probe_absence_is_never_treated_as_probe_success(self) -> None:
        preferred = route_of("preferred-undetermined", "alias-undetermined", "model-undetermined")
        snapshot = snapshot_for(
            preferred,
            self.SPARE,
            probe={"model-undetermined": False, "model-probed": True},
            invocation={"model-undetermined": "absent", "model-probed": "success"},
        )
        report = self.resolve(policy_of(preferred, (self.SPARE,)), snapshot)
        self.assertEqual(
            [(entry["route_id"], entry["disposition"]) for entry in report["attempted_routes"]],
            [("preferred-undetermined", "rejected"), ("fallback-probed", "selected")],
        )

    def test_a_snapshot_omitting_a_models_probe_entry_fails_closed(self) -> None:
        preferred = route_of("preferred-omitted", "alias-omitted", "model-omitted")
        snapshot = snapshot_for(preferred, self.SPARE, probe={"model-probed": True})
        report = self.resolve(policy_of(preferred, (self.SPARE,)), snapshot)
        self.assertIn("capability_probe_unavailable", self.codes(report))

    def test_a_probe_available_model_emits_no_probe_availability_diagnostic(self) -> None:
        preferred = route_of("preferred-available", "alias-available", "model-available")
        report = self.resolve(policy_of(preferred), snapshot_for(preferred))
        self.assertEqual(self.codes(report), [])


class TreatmentProbeFailedTests(SimulatorCaseMixin, unittest.TestCase):
    """FR-009: an exact-invocation probe failure rejects and is never selected."""

    SPARE = route_of("fallback-passing", "alias-passing", "model-passing")

    def test_an_exact_invocation_failure_is_rejected_and_the_walk_continues(self) -> None:
        preferred = route_of("preferred-failing", "alias-failing", "model-failing")
        snapshot = snapshot_for(
            preferred,
            self.SPARE,
            invocation={"model-failing": "failure", "model-passing": "success"},
        )
        report = self.resolve(policy_of(preferred, (self.SPARE,)), snapshot)
        entry = self.only_diagnostic(report, "treatment_probe_failed")
        self.assertEqual(entry["details"], {"route_id": "preferred-failing"})
        self.assertEqual(entry["severity"], "warning")
        self.assertEqual(
            entry["remediation"]["actions"],
            ["Inspect the exact-invocation probe evidence for this route."],
        )
        self.assertEqual(
            [(each["route_id"], each["disposition"]) for each in report["attempted_routes"]],
            [("preferred-failing", "rejected"), ("fallback-passing", "selected")],
        )

    def test_an_absent_exact_invocation_outcome_is_not_itself_a_probe_failure(self) -> None:
        preferred = route_of("preferred-no-record", "alias-no-record", "model-no-record")
        snapshot = snapshot_for(preferred, invocation={"model-no-record": "absent"})
        report = self.resolve(policy_of(preferred), snapshot)
        self.assertNotIn("treatment_probe_failed", self.codes(report))


class DiagnosticEmissionOrderTests(SimulatorCaseMixin, unittest.TestCase):
    """FR-012b: emission is pinned, not merely required to be deterministic.

    Two orders live in the simulator and neither supplies the other. The sub-reason
    order asserted above is *intra-diagnostic* — it picks the single ``sub_reason`` one
    entry carries. The order here is *inter-diagnostic*: it sequences whole entries, and
    conflating the two is how the inter-code sequence stayed unpinned while appearing to
    be covered. The array-level cases assert all four ordering slots the contract fixes,
    including the two that only a policy-document violation or an environment override
    populates, so the whole-array contract is proven here rather than assumed.
    """

    def failing_route_snapshot(self, preferred: dict[str, object]) -> dict[str, object]:
        """A snapshot degrading three independent dimensions of one consultable route."""
        model = str(preferred["resolved_model"])
        return snapshot_for(
            preferred,
            efforts={model: ["low"]},
            probe={model: False},
            invocation={model: "failure"},
        )

    def test_a_route_failing_two_independent_checks_emits_one_diagnostic_per_check(self) -> None:
        preferred = route_of("preferred-two-grounds", "alias-two", "model-two", "max")
        snapshot = snapshot_for(
            preferred,
            efforts={"model-two": ["low", "medium", "high"]},
            invocation={"model-two": "failure"},
        )
        report = self.resolve(policy_of(preferred), snapshot)
        self.assertEqual(
            self.codes(report),
            ["effort_unsupported", "treatment_probe_failed", "no_safe_route"],
        )

    def test_the_inter_code_order_follows_the_resolution_enums_declared_order(self) -> None:
        preferred = route_of("preferred-three-grounds", "alias-three", "model-three", "max")
        report = self.resolve(policy_of(preferred), self.failing_route_snapshot(preferred))
        observed = [code for code in self.codes(report) if code != "no_safe_route"]
        self.assertEqual(
            observed,
            [code for code in self.module.RESOLUTION_CODES if code in set(observed)],
        )
        self.assertEqual(
            observed,
            ["effort_unsupported", "capability_probe_unavailable", "treatment_probe_failed"],
        )

    def test_per_route_entries_are_grouped_in_attempt_order_and_joined_by_route_id(self) -> None:
        preferred = route_of("preferred-first-reject", "alias-one", "model-one", "max")
        second = route_of("fallback-second-reject", "alias-second", "model-second")
        snapshot = snapshot_for(
            preferred,
            second,
            efforts={"model-one": ["low"], "model-second": list(EFFORT_LADDER)},
            invocation={"model-one": "success", "model-second": "failure"},
        )
        report = self.resolve(policy_of(preferred, (second,)), snapshot)
        self.assertEqual(
            [(entry["code"], entry.get("details", {}).get("route_id")) for entry in report["diagnostics"]],
            [
                ("effort_unsupported", "preferred-first-reject"),
                ("treatment_probe_failed", "fallback-second-reject"),
                ("no_safe_route", None),
            ],
        )

    def test_the_terminal_entry_is_unique_last_and_carries_the_verbatim_rollback(self) -> None:
        preferred = route_of("preferred-terminal", "alias-terminal", "model-terminal")
        snapshot = snapshot_for(preferred, invocation={"model-terminal": "failure"})
        report = self.resolve(policy_of(preferred), snapshot)
        terminal = report["diagnostics"][-1]
        self.assertEqual(terminal["code"], "no_safe_route")
        self.assertEqual(self.codes(report).count("no_safe_route"), 1)
        self.assertEqual(terminal["severity"], "error")
        self.assertEqual(
            terminal["remediation"]["actions"],
            [
                "Widen the declared fallback list with qualified routes.",
                "Roll back to the previous plugin release.",
            ],
        )
        self.assertNotIn("details", terminal)

    def test_the_outcome_and_the_terminal_code_are_coupled_in_both_directions(self) -> None:
        clean = route_of("preferred-coupled-clean", "alias-clean", "model-clean")
        resolved = self.resolve(policy_of(clean), snapshot_for(clean))
        self.assertEqual(resolved["outcome"], "resolved")
        self.assertEqual(self.codes(resolved).count("no_safe_route"), 0)

        failing = route_of("preferred-coupled-fail", "alias-fail", "model-fail")
        unresolved = self.resolve(
            policy_of(failing), snapshot_for(failing, invocation={"model-fail": "failure"})
        )
        self.assertEqual(unresolved["outcome"], "no_safe_route")
        self.assertEqual(self.codes(unresolved).count("no_safe_route"), 1)

    def test_a_no_safe_route_report_names_the_policys_own_agent_as_unresolved(self) -> None:
        preferred = route_of("preferred-named", "alias-named", "model-named")
        policy = policy_of(
            preferred, name="fixture-bounded-analyst", role_class="bounded_analyst"
        )
        report = self.resolve(
            policy, snapshot_for(preferred, invocation={"model-named": "failure"})
        )
        self.assertEqual(report["unresolved_agent"], "fixture-bounded-analyst")

    def test_a_resolved_report_names_no_unresolved_agent(self) -> None:
        preferred = route_of("preferred-resolved", "alias-resolved", "model-resolved")
        report = self.resolve(policy_of(preferred), snapshot_for(preferred))
        self.assertNotIn("unresolved_agent", report)

    def test_the_whole_array_assembles_its_four_ordering_slots_in_the_contracted_order(self) -> None:
        marker = {"pre": "pre-walk", "first": "route-one", "second": "route-two"}
        assembled = self.module._assemble_diagnostics(
            pre_walk=[{"code": marker["pre"]}],
            per_route=[[{"code": marker["first"]}], [{"code": marker["second"]}]],
            override=[{"code": "unqualified_override"}],
            terminal=[{"code": "no_safe_route"}],
        )
        self.assertEqual(
            [entry["code"] for entry in assembled],
            [
                "pre-walk",
                "route-one",
                "route-two",
                "unqualified_override",
                "no_safe_route",
            ],
        )


class EffectiveDispatchTupleTests(SimulatorCaseMixin, unittest.TestCase):
    """FR-011 and FR-013: the selected tuple is recorded, and a clean success is silent.

    Recording the tuple is what lets a consumer read what resolution selected without
    re-deriving it from the attempt list. The clean-success case is why ``diagnostics``
    declares no ``minItems``: an empty array is a conforming report, not a defective one.
    """

    def test_the_resolved_path_records_the_four_member_effective_dispatch_tuple(self) -> None:
        preferred = route_of("preferred-tuple", "alias-tuple", "model-tuple", "xhigh")
        report = self.resolve(policy_of(preferred), snapshot_for(preferred))
        self.assertEqual(
            report["effective_dispatch_tuple"],
            {
                "agent": "fixture-required-executor",
                "alias": "alias-tuple",
                "resolved_model": "model-tuple",
                "effort": "xhigh",
            },
        )

    def test_the_tuple_names_the_selected_fallback_rather_than_the_preferred_route(self) -> None:
        preferred = route_of("preferred-skipped", "alias-skipped", "model-skipped")
        spare = route_of("fallback-taken", "alias-taken", "model-taken", "medium")
        snapshot = snapshot_for(preferred, spare, available=("model-taken",))
        report = self.resolve(policy_of(preferred, (spare,)), snapshot)
        self.assertEqual(report["effective_dispatch_tuple"]["alias"], "alias-taken")
        self.assertEqual(report["effective_dispatch_tuple"]["resolved_model"], "model-taken")
        self.assertEqual(report["effective_dispatch_tuple"]["effort"], "medium")

    def test_a_clean_preferred_route_emits_an_empty_diagnostics_array(self) -> None:
        preferred = route_of("preferred-silent", "alias-silent", "model-silent")
        report = self.resolve(policy_of(preferred), snapshot_for(preferred))
        self.assertEqual(report["diagnostics"], [])
        self.assertEqual(report["outcome"], "resolved")

    def test_a_no_safe_route_report_records_no_effective_dispatch_tuple(self) -> None:
        preferred = route_of("preferred-none", "alias-none", "model-none")
        report = self.resolve(
            policy_of(preferred), snapshot_for(preferred, invocation={"model-none": "failure"})
        )
        self.assertNotIn("effective_dispatch_tuple", report)

    def test_a_route_reaching_the_walk_without_a_pinned_model_fails_closed(self) -> None:
        preferred = route_of("preferred-unpinned", "alias-unpinned", "model-unpinned")
        snapshot = snapshot_for(preferred)
        del preferred["resolved_model"]
        with self.assertRaises(self.module.RouteFallbackError):
            self.resolve(policy_of(preferred), snapshot)

    def test_a_route_reaching_the_walk_without_a_pinned_effort_fails_closed(self) -> None:
        preferred = route_of("preferred-effortless", "alias-effortless", "model-effortless")
        snapshot = snapshot_for(preferred)
        del preferred["effort"]
        with self.assertRaises(self.module.RouteFallbackError):
            self.resolve(policy_of(preferred), snapshot)


class ReportScopedFieldTests(SimulatorCaseMixin, unittest.TestCase):
    """FR-024a, FR-025a, FR-026a: the three fields required in *every* report.

    None of them may be stubbed in slice 1. ``release_claim_eligible`` is a closed
    disqualifier list with ``true`` as the residual; ``optional_helper`` is structured
    rather than a diagnostic; ``budgets`` carries the declared caps beside all three
    actual counters. Cap *enforcement* and the exhaustion terminal are separate
    requirements, but the counters and the derivation rule are complete here.
    """

    def test_budgets_echo_the_declared_caps_beside_the_three_actual_counters(self) -> None:
        preferred = route_of("preferred-counted", "alias-counted", "model-counted")
        spare = route_of("fallback-counted", "alias-spare-counted", "model-spare-counted")
        snapshot = snapshot_for(preferred, spare, available=("model-spare-counted",))
        report = self.resolve(policy_of(preferred, (spare,)), snapshot)
        self.assertEqual(
            report["budgets"],
            {
                "declared": dict(INLINE_BUDGETS),
                "actual": {"probe_attempts": 1, "retries": 0, "candidate_routes": 2},
            },
        )

    def test_probe_attempts_skips_a_route_rejected_before_probing_is_reached(self) -> None:
        preferred = route_of("preferred-unreached", "alias-unreached", "model-unreached")
        snapshot = snapshot_for(preferred, available=())
        report = self.resolve(policy_of(preferred), snapshot)
        self.assertEqual(report["budgets"]["actual"]["probe_attempts"], 0)
        self.assertEqual(report["budgets"]["actual"]["candidate_routes"], 1)

    def test_probe_attempts_counts_a_route_rejected_on_a_later_ground(self) -> None:
        preferred = route_of("preferred-probed-then-failed", "alias-pf", "model-pf", "max")
        snapshot = snapshot_for(preferred, efforts={"model-pf": ["low"]})
        report = self.resolve(policy_of(preferred), snapshot)
        self.assertEqual(report["budgets"]["actual"]["probe_attempts"], 1)

    def test_candidate_routes_equals_the_attempt_list_length_and_bounds_probe_attempts(
        self,
    ) -> None:
        preferred = route_of("preferred-bound", "alias-bound-a", "model-bound-a")
        spare = route_of("fallback-bound", "alias-bound-b", "model-bound-b")
        snapshot = snapshot_for(preferred, spare, available=("model-bound-b",))
        actual = self.resolve(policy_of(preferred, (spare,)), snapshot)["budgets"]["actual"]
        self.assertEqual(actual["candidate_routes"], 2)
        self.assertLessEqual(actual["probe_attempts"], actual["candidate_routes"])

    def test_release_claim_eligible_is_true_as_the_residual(self) -> None:
        preferred = route_of("preferred-eligible", "alias-eligible", "model-eligible")
        report = self.resolve(policy_of(preferred), snapshot_for(preferred))
        self.assertIs(report["release_claim_eligible"], True)

    def test_release_claim_eligible_is_false_under_a_no_safe_route_outcome(self) -> None:
        preferred = route_of("preferred-ineligible", "alias-ineligible", "model-ineligible")
        report = self.resolve(
            policy_of(preferred),
            snapshot_for(preferred, invocation={"model-ineligible": "failure"}),
        )
        self.assertIs(report["release_claim_eligible"], False)

    def test_a_repointed_preferred_route_resolving_on_a_qualified_fallback_stays_eligible(
        self,
    ) -> None:
        preferred = route_of("preferred-drifted", "alias-drifted", "model-pin")
        spare = route_of("fallback-qualified", "alias-qualified", "model-qualified")
        snapshot = snapshot_for(
            preferred,
            spare,
            available=("model-pin", "model-moved", "model-qualified"),
            bindings={"alias-drifted": "model-moved", "alias-qualified": "model-qualified"},
        )
        report = self.resolve(policy_of(preferred, (spare,)), snapshot)
        self.assertEqual(report["outcome"], "resolved")
        self.assertIs(report["release_claim_eligible"], True)

    def test_the_disqualifier_list_is_closed_over_the_override_and_violation_grounds(self) -> None:
        derive = self.module._release_claim_eligible
        self.assertIs(derive("resolved", [], None), True)
        self.assertIs(derive("resolved", [], {"CLAUDE_CODE_SUBAGENT_MODEL": "model-x"}), False)
        self.assertIs(derive("no_safe_route", [], None), False)
        for code in self.module.POLICY_VIOLATION_CODES:
            with self.subTest(code=code):
                self.assertIs(derive("resolved", [{"code": code}], None), False)

    def test_optional_helper_records_the_no_helper_declared_state(self) -> None:
        preferred = route_of("preferred-helperless", "alias-helperless", "model-helperless")
        report = self.resolve(policy_of(preferred), snapshot_for(preferred))
        self.assertEqual(
            report["optional_helper"],
            {"consulted": False, "no_helper_path_validated": True, "probe_attempts": 0},
        )

    def test_a_policy_declaring_a_helper_fails_closed_rather_than_claiming_none(self) -> None:
        preferred = route_of("preferred-with-helper", "alias-with-helper", "model-with-helper")
        helper_route = route_of("helper-primary", "alias-helper", "model-helper")
        policy = policy_of(preferred)
        policy["optional_helper"] = {
            "agent": {"name": "fixture-optional-helper", "role_class": "optional_helper"},
            "preferred_route": helper_route,
            "fallback_routes": [],
        }
        with self.assertRaises(self.module.RouteFallbackError):
            self.resolve(policy, snapshot_for(preferred, helper_route))

    def test_every_produced_report_validates_against_the_committed_report_contract(self) -> None:
        preferred = route_of("preferred-valid", "alias-valid", "model-valid")
        spare = route_of("fallback-valid", "alias-valid-spare", "model-valid-spare")
        policy = policy_of(preferred, (spare,))
        for label, snapshot in (
            ("clean", snapshot_for(preferred, spare)),
            ("fallback-selected", snapshot_for(preferred, spare, available=("model-valid-spare",))),
            (
                "no-safe-route",
                snapshot_for(
                    preferred,
                    spare,
                    invocation={"model-valid": "failure", "model-valid-spare": "failure"},
                ),
            ),
        ):
            with self.subTest(snapshot=label):
                report = self.resolve(policy, snapshot)
                self.assertEqual(
                    self.module.validate_instance(report, self.module.REPORT_SCHEMA), report
                )


class ReplayDeterminismTests(unittest.TestCase):
    """FR-014 and SC-002: every corpus case replays byte-identically, twice over.

    Both comparisons run over the string the simulator's own ``serialize_report``
    returns. No local ``canonical_json`` is declared anywhere in this module: the
    established comparison shape re-serializes both sides, so a divergent local copy
    would CANCEL a real discrepancy instead of failing on it.
    """

    def setUp(self) -> None:
        self.assertIsNotNone(claude_route_fallback, "claude_route_fallback is not importable")
        self.module = claude_route_fallback
        self.corpus = self.module.load_corpus()
        self.cases = self.corpus["cases"]

    def replay(self, case: dict[str, object]) -> str:
        policy = case["policy"]
        report = self.module.resolve(
            policy,
            case["snapshot"],
            case["overrides"],
            policy["budgets"],
        )
        return self.module.serialize_report(report)

    def test_the_corpus_envelope_declares_the_replay_fixture_kind(self) -> None:
        self.assertEqual(self.corpus["fixture_kind"], "route_fallback_replay")
        self.assertEqual(self.corpus["schema_version"], "1.0.0")
        self.assertTrue(self.cases, "the corpus declares no cases")

    def test_each_case_replays_byte_identically_to_its_pinned_report(self) -> None:
        for case in self.cases:
            with self.subTest(case=case["case_id"]):
                self.assertEqual(
                    self.replay(case),
                    self.module.serialize_report(case["expected_report"]),
                )

    def test_two_successive_runs_over_identical_inputs_are_byte_identical(self) -> None:
        for case in self.cases:
            with self.subTest(case=case["case_id"]):
                self.assertEqual(self.replay(case), self.replay(case))


class CorpusContractValidationTests(SimulatorCaseMixin, unittest.TestCase):
    """FR-003a and SC-003: every case's three payloads validate against the three contracts.

    The pairing at the end is the point of validating the policy separately from
    replaying it. A route omitting its resolved model or effort must be **admitted** by
    the route contract and **rejected** by the simulator: if the schema were tightened to
    require them, that fixture would fail validation instead of producing the diagnostic
    the requirement asks for, and the failure would be misdiagnosed as a bad fixture
    rather than as an over-constrained contract.
    """

    def setUp(self) -> None:
        super().setUp()
        self.cases = self.module.load_corpus()["cases"]
        self.contracts = {
            "policy": load_contract(CONTRACT_ROOT / "route-policy.schema.json"),
            "snapshot": load_contract(
                CONTRACT_ROOT / "environment-snapshot-projection.schema.json"
            ),
            "expected_report": load_contract(
                CONTRACT_ROOT / "route-resolution-report.schema.json"
            ),
        }

    def test_every_case_payload_validates_against_its_committed_contract(self) -> None:
        for case in self.cases:
            for member, schema in self.contracts.items():
                with self.subTest(case=case["case_id"], payload=member):
                    self.assertEqual(validate_instance(case[member], schema), case[member])

    def test_the_corpus_holds_the_nine_declared_slice_one_cases(self) -> None:
        self.assertEqual(len(self.cases), 9)

    def test_the_route_contract_admits_an_omitted_model_the_simulator_rejects(self) -> None:
        inheriting = {"route_id": "preferred-inherits", "alias": "alias-inherits", "qualified": True}
        policy = policy_of(inheriting)
        self.assertEqual(
            validate_instance(policy, self.contracts["policy"]),
            policy,
        )
        with self.assertRaises(self.module.RouteFallbackError):
            self.resolve(policy, snapshot_for())

    def test_the_route_contract_admits_a_repeated_fallback_the_schema_must_not_forbid(self) -> None:
        preferred = route_of("preferred-repeat", "alias-repeat", "model-repeat")
        policy = policy_of(preferred, (dict(preferred), dict(preferred)))
        self.assertEqual(validate_instance(policy, self.contracts["policy"]), policy)

    def test_an_over_range_declared_budget_is_refused_by_the_policy_contract(self) -> None:
        preferred = route_of("preferred-overbudget", "alias-overbudget", "model-overbudget")
        policy = policy_of(preferred)
        policy["budgets"]["max_probe_attempts"] = 9
        with self.assertRaises(ControlContractError):
            validate_instance(policy, self.contracts["policy"])


# --------------------------------------------------------------------------- #
# Slice-1 assertion obligations                                                 #
# --------------------------------------------------------------------------- #
# Each case below proves a slice-1 guarantee inside slice 1's own diff: every one
# is provable the moment the slice-1 schemas exist, and none waits on the slice
# that first emits the value it constrains.

MODULE_PATH = Path(__file__).resolve()

# FR-017a and FR-019b: the read targets, declared once each so the pointer is a
# stated constant rather than an attribute chain buried inside a comparison.
RESOLUTION_CODE_POINTER = "$defs/resolutionDiagnostic/properties/code/enum"
POLICY_VIOLATION_CODE_POINTER = "$defs/policyViolationDiagnostic/properties/code/enum"
SUB_REASON_POINTER = "$defs/resolutionDiagnostic/properties/details/properties/sub_reason/enum"
DECLARED_EFFORT_POINTER = (
    "$defs/resolutionDiagnostic/properties/details/properties/declared_effort/enum"
)
REMEDIATION_ACTION_POINTER = "$defs/remediation/properties/actions/items/enum"
ROUTE_EFFORT_POINTER = "$defs/route/properties/effort/enum"
DECLARED_BUDGETS_POINTER = "$defs/declaredBudgets"
FROZEN_EFFORT_POINTER = "$defs/tuple/properties/effort/enum"
FROZEN_CAPABILITY_CONTRACT = "successor-capability-freeze.schema.json"

ROADMAP_ROOT = REPO_ROOT / "docs" / "ai" / "specs"
CLAUDE_ROADMAP = ROADMAP_ROOT / "claude-agent-routing-technical-roadmap.md"
CODEX_ROADMAP = ROADMAP_ROOT / "codex-gpt-5-6-agent-routing-technical-roadmap.md"

# Prose anchors, deliberately NOT code tokens: the reason codes are read out of the
# span each pair delimits, so this module never restates the enum it is checking.
CLAUDE_REASON_CODE_SPAN = ("Define stable reason codes (", ")")
CODEX_REASON_CODE_SPAN = ("Require deterministic resolution reasons:", ";")
BACKTICKED_TOKEN = re.compile(r"`([a-z][a-z0-9_]*)`")

# FR-017b and FR-017c: the recorded divergence, held as data. It is a permanent,
# intentional platform difference — Codex splits discovery from probing and Claude
# has no such split — so no reconciliation is attempted, and pinning both spellings
# is what makes a silent edit to either roadmap fail the suite.
CLAUDE_ONLY_REASON_CODE = "capability_probe_unavailable"
CODEX_ONLY_REASON_CODE = "capability_discovery_unavailable"
SHARED_REASON_CODE_COUNT = 4

# FR-019b: the second witness for the policy-violation vocabulary. Declaring these
# members here is correct rather than a break with the read-live discipline — see
# ClosedVocabularySetEqualityTests for why the two enums are treated differently.
POLICY_VIOLATION_MEMBERS = frozenset(
    {
        "fallback_loop",
        "unqualified_adjacent_model",
        "generic_agent_substitution",
        "silent_inherit_materialization",
        "unqualified_override",
    }
)

# FR-007a: the session-level orchestration setting that is deliberately not a model
# effort level, named so its absence from the ladder is asserted rather than assumed.
SESSION_ORCHESTRATION_SETTING = "ultracode"

UNRECOGNISED_DIAGNOSTIC_CODE = "fixture_unrecognised_reason_code"

AGENTS_ROOT = REPO_ROOT / "speckit-pro" / "agents"
AGENT_FRONTMATTER_NAME = re.compile(r"^name:[ \t]*(?P<name>\S+)[ \t]*$", re.MULTILINE)
FIXTURE_NAME_PREFIX = "fixture-"
AGENT_NAME_KEYS = ("agent", "substituted_agent", "unresolved_agent")
SYNTHETIC_ROLE_CLASSES = frozenset({"required_executor", "bounded_analyst", "optional_helper"})
DIAGNOSTIC_SOURCE = "route-fallback-simulator"
CASE_PAYLOAD_MEMBERS = ("policy", "snapshot", "overrides", "expected_report")

# FR-012c and data-model.md section 3: severity is a function of code, and each code
# carries one fixed action allocation. Recorded here because the mapping has no
# token-bearing committed authority — the schemas close the vocabularies but leave
# which member pairs with which code entirely open, which is exactly the authoring
# latitude a byte-compared hand-authored corpus must not have.
SEVERITY_BY_CODE = {
    "preferred_model_unavailable": "warning",
    "effort_unsupported": "warning",
    "capability_probe_unavailable": "warning",
    "treatment_probe_failed": "warning",
    "no_safe_route": "error",
    "fallback_loop": "error",
    "unqualified_adjacent_model": "error",
    "generic_agent_substitution": "error",
    "silent_inherit_materialization": "error",
    "unqualified_override": "warning",
}
ACTIONS_BY_CODE = {
    "preferred_model_unavailable": [
        "Re-probe the environment and confirm the pinned alias and resolved model."
    ],
    "effort_unsupported": ["Declare an effort the model's probed capability set supports."],
    "capability_probe_unavailable": ["Re-run capability probing before trusting this route."],
    "treatment_probe_failed": ["Inspect the exact-invocation probe evidence for this route."],
    "no_safe_route": [
        "Widen the declared fallback list with qualified routes.",
        "Roll back to the previous plugin release.",
    ],
    "fallback_loop": ["Remove the repeated route from the fallback chain."],
    "unqualified_adjacent_model": ["Replace the adjacent model with a qualified route."],
    "generic_agent_substitution": ["Restore the named agent in the fallback route."],
    "silent_inherit_materialization": ["Declare the model and effort explicitly on the route."],
    "unqualified_override": [
        "Unset the unqualified subagent-model override before making release claims."
    ],
}

# The class whose job is to prove serialize_report and the shared library agree.
SERIALIZER_EQUIVALENCE_CLASS = "SimulatorSerializationSurfaceTests"
# The two places a call to the shared library serializer is legitimate, each for a reason
# that is not report serialization: the equivalence case above, and the purity case, which
# hashes the INPUT policy and snapshot to prove resolve mutates neither — inputs are not
# reports, so serialize_report is not the tool for them. Anywhere else it would be a second
# REPORT serializer, which is the trap FR-014a names.
SHARED_SERIALIZER_CALLERS = (SERIALIZER_EQUIVALENCE_CLASS, "ResolutionWalkTests")
# The classes that compare serialized bytes. Named rather than inferred, with the
# names asserted present, so a rename cannot quietly leave the audit covering nothing.
BYTE_COMPARING_CLASSES = ("ReplayDeterminismTests",)
APPROVED_SERIALIZER_CALLS = frozenset({"serialize_report", "replay"})
# A raw json dump has no legitimate place here at all: it is neither of the two
# serializers, and the trailing-newline and key-order guarantees are not its to keep.
BANNED_JSON_CALLS = frozenset({"dumps", "dump"})


def read_by_pointer(document: object, pointer: str) -> object:
    """Resolve a slash-separated JSON pointer against ``document``.

    The enums are read through this rather than by attribute chain so the pointer the
    requirement names is the literal string the test carries.
    """
    node = document
    for token in pointer.split("/"):
        if not isinstance(node, dict) or token not in node:
            raise KeyError(f"{pointer}: no {token!r} under {type(node).__name__}")
        node = node[token]
    return node


def roadmap_reason_codes(path: Path, span: tuple[str, str]) -> tuple[str, ...]:
    """Every backticked token the roadmap declares inside ``span``, in declared order.

    An unmatched anchor returns the empty tuple rather than raising: the callers assert
    non-emptiness with a message naming the anchor, so a roadmap edit that moved the
    declaration surfaces as that rather than as an opaque set difference.
    """
    opening, closing = span
    text = path.read_text(encoding="utf-8")
    start = text.find(opening)
    if start < 0:
        return ()
    start += len(opening)
    end = text.find(closing, start)
    if end < 0:
        return ()
    return tuple(BACKTICKED_TOKEN.findall(text[start:end]))


def module_syntax_tree() -> ast.Module:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"), filename=str(MODULE_PATH))


def binding_kinds(tree: ast.AST, name: str) -> set[str]:
    """Every way ``tree`` binds ``name``, described so a failure names what bound it."""
    kinds: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == name and isinstance(node.ctx, ast.Store):
            kinds.add("assignment")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            kinds.add("function definition")
        elif isinstance(node, ast.ClassDef) and node.name == name:
            kinds.add("class definition")
        elif isinstance(node, ast.arg) and node.arg == name:
            kinds.add("parameter")
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if (alias.asname or alias.name) == name:
                    kinds.add(f"import from {node.module}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if (alias.asname or alias.name.split(".")[0]) == name:
                    kinds.add("plain import")
    return kinds


def called_names(node: ast.AST) -> set[str]:
    """The bare and attribute names of every call inside ``node``."""
    names: set[str] = set()
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Call):
            continue
        if isinstance(sub.func, ast.Name):
            names.add(sub.func.id)
        elif isinstance(sub.func, ast.Attribute):
            names.add(sub.func.attr)
    return names


def declared_classes(tree: ast.Module) -> dict[str, ast.ClassDef]:
    return {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}


def numeric_leaves(value: object, location: str) -> list[tuple[str, object]]:
    """Every non-boolean numeric leaf under ``value``, with the path that reached it."""
    if isinstance(value, dict):
        found: list[tuple[str, object]] = []
        for key, member in value.items():
            found.extend(numeric_leaves(member, f"{location}.{key}"))
        return found
    if isinstance(value, list):
        found = []
        for index, member in enumerate(value):
            found.extend(numeric_leaves(member, f"{location}[{index}]"))
        return found
    if isinstance(value, bool):
        return []
    if isinstance(value, (int, float)):
        return [(location, value)]
    return []


def agent_names_in(value: object) -> set[str]:
    """Every agent name reachable under ``value``, whichever member carries it."""
    names: set[str] = set()
    if isinstance(value, dict):
        for key, member in value.items():
            if key in AGENT_NAME_KEYS:
                if isinstance(member, str):
                    names.add(member)
                elif isinstance(member, dict) and isinstance(member.get("name"), str):
                    names.add(member["name"])
            names |= agent_names_in(member)
    elif isinstance(value, list):
        for member in value:
            names |= agent_names_in(member)
    return names


def shipped_agent_roster() -> set[str]:
    """The shipped roster, listed live: file stems and their declared frontmatter names.

    FR-018 and SC-006: derived rather than transcribed. Eleven agents ship today and one
    more is net-new in a later feature, so a blocklist written into this file would stop
    covering names added after it was written — which is why the ``fixture-`` prefix is
    the positive rule this negative assertion only supplements.
    """
    roster: set[str] = set()
    for path in sorted(AGENTS_ROOT.glob("*.md")):
        roster.add(path.stem)
        match = AGENT_FRONTMATTER_NAME.search(path.read_text(encoding="utf-8"))
        if match is not None:
            roster.add(match.group("name"))
    return roster


class SingleSerializerDisciplineTests(unittest.TestCase):
    """FR-014a and SC-002: one serializer, and every byte comparison taken over it.

    This is a correctness trap, not a style rule. The repository carries eight
    ``canonical_json`` definitions of which three append a trailing newline, and all six
    existing occurrences under ``unit/`` declare their own copy. The established
    comparison shape re-serializes BOTH sides, so a divergent local copy would CANCEL a
    real mismatch rather than fail on it, leaving a green test over a simulator whose
    output differs. A green test over a wrong simulator is the failure mode, so the
    audit is mechanical: a local definition has to be unable to appear, not something a
    reviewer has to notice is absent.
    """

    def setUp(self) -> None:
        self.assertIsNotNone(claude_route_fallback, "claude_route_fallback is not importable")
        self.module = claude_route_fallback
        self.tree = module_syntax_tree()
        self.classes = declared_classes(self.tree)

    def test_the_only_canonical_serializer_binding_is_the_shared_librarys_import(self) -> None:
        self.assertEqual(
            binding_kinds(self.tree, "canonical_json"),
            {"import from claude_successor_freeze"},
        )

    def test_no_second_serializer_is_called_outside_the_two_documented_places(self) -> None:
        for name in SHARED_SERIALIZER_CALLERS:
            self.assertIn(
                name, self.classes, f"{name} is no longer declared, so this audit covers nothing"
            )
        self.assertIn(
            "canonical_json",
            called_names(self.classes[SERIALIZER_EQUIVALENCE_CLASS]),
            f"{SERIALIZER_EQUIVALENCE_CLASS} no longer compares the two serializers",
        )
        allowed = {id(self.classes[name]) for name in SHARED_SERIALIZER_CALLERS}
        offenders: list[str] = []
        for node in self.tree.body:
            where = f"{getattr(node, 'name', type(node).__name__)} (line {node.lineno})"
            banned = set(BANNED_JSON_CALLS)
            if id(node) not in allowed:
                banned.add("canonical_json")
            offenders.extend(f"{where}: {each}" for each in sorted(called_names(node) & banned))
        self.assertEqual(offenders, [])

    def test_every_byte_comparison_is_taken_over_the_simulators_own_serializer(self) -> None:
        for name in BYTE_COMPARING_CLASSES:
            node = self.classes.get(name)
            self.assertIsNotNone(node, f"{name} is no longer declared, so this audit covers nothing")
            compared = 0
            for call in ast.walk(node):
                if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
                    continue
                if call.func.attr != "assertEqual":
                    continue
                if not any(isinstance(argument, ast.Call) for argument in call.args):
                    continue  # a comparison against a literal, not a byte comparison
                compared += 1
                for argument in call.args:
                    approved = (
                        isinstance(argument, ast.Call)
                        and isinstance(argument.func, ast.Attribute)
                        and argument.func.attr in APPROVED_SERIALIZER_CALLS
                    )
                    self.assertTrue(
                        approved,
                        f"{name} line {call.lineno}: a compared value does not come from "
                        f"serialize_report",
                    )
            self.assertGreater(compared, 0, f"{name} takes no byte comparison at all")

    def test_no_pinned_report_serializes_with_a_trailing_newline(self) -> None:
        for case in self.module.load_corpus()["cases"]:
            with self.subTest(case=case["case_id"]):
                serialized = self.module.serialize_report(case["expected_report"])
                self.assertFalse(serialized.endswith("\n"))

    def test_every_number_in_every_pinned_report_is_an_integer(self) -> None:
        checked = 0
        for case in self.module.load_corpus()["cases"]:
            for location, value in numeric_leaves(case["expected_report"], case["case_id"]):
                checked += 1
                with self.subTest(location=location):
                    self.assertNotIsInstance(value, float)
                    self.assertIsInstance(value, int)
        self.assertGreater(
            checked, 0, "no numeric field was reached, so this assertion covers nothing"
        )


class RoadmapParityTests(unittest.TestCase):
    """FR-017 through FR-017c and SC-012: the resolution enum against the roadmap pinning it.

    Both sides are read live from committed files. The five members are deliberately NOT
    transcribed here: a test that restated the enum would absorb the very drift it exists
    to catch, because the schema and the roadmap are two independently committed witnesses
    and a third copy collapses them into one. The prose anchors the codes are read out of
    are not themselves code tokens, so moving the declaration fails loudly instead of
    silently narrowing what is compared.
    """

    def resolution_enum(self) -> list[str]:
        document = load_contract(CONTRACT_ROOT / "route-resolution-report.schema.json")
        return list(read_by_pointer(document, RESOLUTION_CODE_POINTER))

    def claude_roadmap_codes(self) -> tuple[str, ...]:
        codes = roadmap_reason_codes(CLAUDE_ROADMAP, CLAUDE_REASON_CODE_SPAN)
        self.assertTrue(
            codes,
            f"{CLAUDE_ROADMAP.name} declares no reason codes under "
            f"{CLAUDE_REASON_CODE_SPAN[0]!r}",
        )
        return codes

    def codex_roadmap_codes(self) -> tuple[str, ...]:
        codes = roadmap_reason_codes(CODEX_ROADMAP, CODEX_REASON_CODE_SPAN)
        self.assertTrue(
            codes,
            f"{CODEX_ROADMAP.name} declares no reason codes under "
            f"{CODEX_REASON_CODE_SPAN[0]!r}",
        )
        return codes

    def test_the_resolution_enum_equals_the_codes_the_claude_roadmap_pins(self) -> None:
        enum = self.resolution_enum()
        self.assertEqual(len(set(enum)), len(enum), "the enum declares a duplicate member")
        self.assertEqual(set(enum), set(self.claude_roadmap_codes()))

    def test_a_dropped_member_fails_the_parity_comparison(self) -> None:
        enum = self.resolution_enum()
        pinned = set(self.claude_roadmap_codes())
        for member in enum:
            with self.subTest(dropped=member):
                self.assertNotEqual(set(enum) - {member}, pinned)

    def test_an_added_member_fails_the_parity_comparison(self) -> None:
        enum = set(self.resolution_enum())
        self.assertNotIn(UNRECOGNISED_DIAGNOSTIC_CODE, enum)
        self.assertNotEqual(enum | {UNRECOGNISED_DIAGNOSTIC_CODE}, set(self.claude_roadmap_codes()))

    def test_the_cross_platform_divergence_is_pinned_as_test_data(self) -> None:
        claude = set(self.claude_roadmap_codes())
        codex = set(self.codex_roadmap_codes())
        self.assertEqual(claude - codex, {CLAUDE_ONLY_REASON_CODE})
        self.assertEqual(codex - claude, {CODEX_ONLY_REASON_CODE})
        self.assertEqual(len(claude & codex), SHARED_REASON_CODE_COUNT)

    def test_the_schema_carries_the_claude_spelling_of_the_divergent_member(self) -> None:
        enum = set(self.resolution_enum())
        self.assertIn(CLAUDE_ONLY_REASON_CODE, enum)
        self.assertNotIn(CODEX_ONLY_REASON_CODE, enum)


class ClosedVocabularySetEqualityTests(unittest.TestCase):
    """FR-019b, FR-007a, SC-003, and SC-013: the two enums whose second witness is this file.

    The read-live-only discipline FR-017a imposes on the resolution enum deliberately does
    NOT extend to these two, and the difference is the whole point. The resolution enum has
    an independently committed second witness in the Claude roadmap, so restating it here
    would collapse two witnesses into one. The policy-violation vocabulary has none — the
    roadmap names its four rejections in prose only, never as code tokens, and the fifth
    member is this spec's own addition — so the literal here IS the second witness and is
    what makes drift detectable at all. The effort ladder sits between the two: the frozen
    successor-capability contract carries the same five members, so both witnesses are
    asserted and neither alone is trusted.
    """

    def report_enum(self, pointer: str) -> list[str]:
        document = load_contract(CONTRACT_ROOT / "route-resolution-report.schema.json")
        return list(read_by_pointer(document, pointer))

    def route_effort_enum(self) -> list[str]:
        document = load_contract(CONTRACT_ROOT / "route-policy.schema.json")
        return list(read_by_pointer(document, ROUTE_EFFORT_POINTER))

    def frozen_effort_enum(self) -> list[str]:
        document = load_contract(CONTRACT_ROOT / FROZEN_CAPABILITY_CONTRACT)
        return list(read_by_pointer(document, FROZEN_EFFORT_POINTER))

    def test_the_policy_violation_enum_holds_exactly_its_five_declared_members(self) -> None:
        enum = self.report_enum(POLICY_VIOLATION_CODE_POINTER)
        self.assertEqual(len(set(enum)), len(enum), "the enum declares a duplicate member")
        self.assertEqual(set(enum), set(POLICY_VIOLATION_MEMBERS))

    def test_a_dropped_policy_violation_member_fails_the_comparison(self) -> None:
        enum = self.report_enum(POLICY_VIOLATION_CODE_POINTER)
        for member in enum:
            with self.subTest(dropped=member):
                self.assertNotEqual(set(enum) - {member}, set(POLICY_VIOLATION_MEMBERS))

    def test_an_added_policy_violation_member_fails_the_comparison(self) -> None:
        enum = set(self.report_enum(POLICY_VIOLATION_CODE_POINTER))
        self.assertNotEqual(
            enum | {UNRECOGNISED_DIAGNOSTIC_CODE}, set(POLICY_VIOLATION_MEMBERS)
        )

    def test_the_two_closed_vocabularies_are_disjoint(self) -> None:
        resolution = set(self.report_enum(RESOLUTION_CODE_POINTER))
        violations = set(self.report_enum(POLICY_VIOLATION_CODE_POINTER))
        self.assertEqual(resolution & violations, set())

    def test_the_effort_enum_holds_exactly_the_five_member_ladder(self) -> None:
        enum = self.route_effort_enum()
        self.assertEqual(len(set(enum)), len(enum), "the ladder declares a duplicate level")
        self.assertEqual(set(enum), set(EFFORT_LADDER))

    def test_the_effort_enum_matches_the_frozen_successor_capability_contract(self) -> None:
        self.assertEqual(set(self.route_effort_enum()), set(self.frozen_effort_enum()))

    def test_a_dropped_effort_level_fails_the_comparison(self) -> None:
        enum = self.route_effort_enum()
        for member in enum:
            with self.subTest(dropped=member):
                self.assertNotEqual(set(enum) - {member}, set(EFFORT_LADDER))

    def test_an_added_effort_level_fails_the_comparison(self) -> None:
        enum = set(self.route_effort_enum())
        self.assertNotEqual(enum | {SESSION_ORCHESTRATION_SETTING}, set(EFFORT_LADDER))

    def test_the_session_orchestration_setting_is_not_an_effort_level(self) -> None:
        self.assertNotIn(SESSION_ORCHESTRATION_SETTING, set(EFFORT_LADDER))
        self.assertNotIn(SESSION_ORCHESTRATION_SETTING, set(self.route_effort_enum()))
        self.assertNotIn(SESSION_ORCHESTRATION_SETTING, set(self.frozen_effort_enum()))


class InlineNegativeValidationTests(unittest.TestCase):
    """FR-019a, FR-027, and SC-003: two negatives, each provable with zero corpus cases.

    Neither property can be a corpus case, because every corpus case must validate. Both
    travel with the slice-1 keyword they prove — the closure with the enum, the ceiling
    with ``maximum`` — rather than waiting for the slice that first emits the value, which
    is what stops slice 2 having to reopen a slice-1 schema for a one-keyword change.

    The instance and the schema handed to the validator are both built here; the enums and
    the maxima inside them are read LIVE from the shipped documents, because an inline copy
    would prove the closure of this test's own literal rather than of what slice 1 ships.
    Each negative is paired with a positive control over the whole live vocabulary: without
    it the negative is unattributable, since an inline instance malformed for an unrelated
    reason also fails validation and the test would pass while proving nothing.
    """

    def setUp(self) -> None:
        self.report_schema = load_contract(CONTRACT_ROOT / "route-resolution-report.schema.json")

    def any_action(self) -> str:
        """One member of the live action vocabulary; every member is equally valid here."""
        return list(read_by_pointer(self.report_schema, REMEDIATION_ACTION_POINTER))[0]

    def maximal_details(self) -> dict[str, object]:
        """A ``details`` object satisfying every conditional branch in both diagnostic ``$defs``.

        Carrying every conditionally required member at once is what lets the control run
        over the whole vocabulary: the branches only add requirements, ``details`` is open,
        and so one object keeps every code valid and leaves the code itself as the sole
        difference between the control and the negative.
        """
        effort = list(read_by_pointer(self.report_schema, DECLARED_EFFORT_POINTER))
        return {
            "route_id": "inline-negative-route",
            "sub_reason": list(read_by_pointer(self.report_schema, SUB_REASON_POINTER))[0],
            "declared_effort": effort[0],
            "supported_efforts": [effort[0]],
        }

    def diagnostic(self, code: str) -> dict[str, object]:
        return {
            "code": code,
            "message": "an inline diagnostic built for the closure proof",
            "severity": "error",
            "source": DIAGNOSTIC_SOURCE,
            "remediation": {
                "summary": "an inline fixture asks nothing of a consumer",
                "actions": [self.any_action()],
            },
            "details": self.maximal_details(),
        }

    def union_schema(self) -> dict[str, object]:
        """An inline document whose one property is the shipped diagnostics union."""
        return {
            "$schema": JSON_SCHEMA_DIALECT,
            "type": "object",
            "additionalProperties": False,
            "required": ["diagnostic"],
            "properties": {"diagnostic": self.report_schema["properties"]["diagnostics"]["items"]},
            "$defs": self.report_schema["$defs"],
        }

    def inline_report(self, diagnostics: list[dict[str, object]]) -> dict[str, object]:
        """A minimal no-safe-route report, so the union is reached through the shipped array."""
        return {
            "schema_version": SCHEMA_VERSION,
            "agent": "fixture-required-executor",
            "outcome": "no_safe_route",
            "attempted_routes": [],
            "diagnostics": diagnostics,
            "budgets": {
                "declared": dict(INLINE_BUDGETS),
                "actual": {"probe_attempts": 0, "retries": 0, "candidate_routes": 0},
            },
            "release_claim_eligible": False,
            "optional_helper": {
                "consulted": False,
                "no_helper_path_validated": True,
                "probe_attempts": 0,
            },
            "unresolved_agent": "fixture-required-executor",
        }

    def live_codes(self) -> list[str]:
        return list(read_by_pointer(self.report_schema, RESOLUTION_CODE_POINTER)) + list(
            read_by_pointer(self.report_schema, POLICY_VIOLATION_CODE_POINTER)
        )

    def test_an_out_of_vocabulary_diagnostic_code_fails_validation(self) -> None:
        self.assertNotIn(UNRECOGNISED_DIAGNOSTIC_CODE, set(self.live_codes()))
        with self.assertRaises(ControlContractError):
            validate_instance(
                {"diagnostic": self.diagnostic(UNRECOGNISED_DIAGNOSTIC_CODE)}, self.union_schema()
            )

    def test_every_code_in_either_live_vocabulary_validates_under_the_same_schema(self) -> None:
        schema = self.union_schema()
        codes = self.live_codes()
        self.assertTrue(codes, "neither vocabulary declared a member, so the control proves nothing")
        for code in codes:
            with self.subTest(code=code):
                instance = {"diagnostic": self.diagnostic(code)}
                self.assertEqual(validate_instance(instance, schema), instance)

    def test_an_out_of_vocabulary_code_fails_through_the_shipped_diagnostics_array(self) -> None:
        with self.assertRaises(ControlContractError):
            validate_instance(
                self.inline_report([self.diagnostic(UNRECOGNISED_DIAGNOSTIC_CODE)]),
                self.report_schema,
            )
        control = self.inline_report([self.diagnostic(self.live_codes()[0])])
        self.assertEqual(validate_instance(control, self.report_schema), control)

    def test_a_declared_budget_above_the_schema_maximum_fails_validation(self) -> None:
        budgets = load_contract(CONTRACT_ROOT / "route-policy.schema.json")
        schema = read_by_pointer(budgets, DECLARED_BUDGETS_POINTER)
        for field in sorted(schema["properties"]):
            ceiling = schema["properties"][field]["maximum"]
            with self.subTest(budget=field, maximum=ceiling):
                at_ceiling = {**INLINE_BUDGETS, field: ceiling}
                self.assertEqual(validate_instance(dict(at_ceiling), schema), at_ceiling)
                above = {**INLINE_BUDGETS, field: ceiling + 1}
                with self.assertRaises(ControlContractError):
                    validate_instance(above, schema)
                # Rejected rather than clamped: the refused value is still the one declared.
                self.assertEqual(above[field], ceiling + 1)


class CorpusEnvelopeTests(unittest.TestCase):
    """FR-015a and SC-007: the envelope properties no schema document validates.

    The corpus has no schema of its own — exactly three documents are permitted and none
    of them validates the envelope — so these hold mechanically here or nowhere. Both the
    append-only seam rule and the read-one-case guarantee rest on them. Cross-slice
    stability is deliberately NOT claimed as mechanically enforced: a case whose inputs
    and pinned report both moved would still replay consistently, so that half stays
    review-borne rather than being asserted misleadingly.
    """

    def setUp(self) -> None:
        self.assertIsNotNone(claude_route_fallback, "claude_route_fallback is not importable")
        self.module = claude_route_fallback
        self.cases = self.module.load_corpus()["cases"]
        self.case_ids = [case["case_id"] for case in self.cases]

    def test_case_ids_are_unique_across_the_whole_corpus(self) -> None:
        self.assertEqual(len(set(self.case_ids)), len(self.cases))

    def test_every_case_id_is_a_non_empty_string(self) -> None:
        for index, case in enumerate(self.cases):
            with self.subTest(index=index):
                identifier = case.get("case_id")
                self.assertIsInstance(identifier, str)
                self.assertNotEqual(identifier, "")

    def test_every_case_carries_its_own_four_payload_members(self) -> None:
        for case in self.cases:
            for member in CASE_PAYLOAD_MEMBERS:
                with self.subTest(case=case["case_id"], member=member):
                    self.assertIn(member, case)

    def test_a_case_declaring_no_override_carries_an_explicit_null(self) -> None:
        for case in self.cases:
            with self.subTest(case=case["case_id"]):
                declared = case["overrides"]
                self.assertTrue(
                    declared is None or isinstance(declared, dict),
                    f"overrides is {type(declared).__name__}, neither an explicit null nor an object",
                )

    def test_no_cases_payload_names_another_cases_identifier(self) -> None:
        self.assertGreater(
            len(self.cases), 1, "one case cannot reference another, so this proves nothing"
        )
        for case in self.cases:
            payload = self.module.serialize_report(
                {member: case[member] for member in CASE_PAYLOAD_MEMBERS}
            )
            for other in self.case_ids:
                if other == case["case_id"]:
                    continue
                with self.subTest(case=case["case_id"], referenced=other):
                    self.assertNotIn(other, payload)


class FixtureHygieneTests(unittest.TestCase):
    """FR-012c, FR-018, FR-032, SC-006, and SC-013: a synthetic cast, and severity by code.

    The ``fixture-`` prefix is the POSITIVE rule and is what the corpus is held to, because
    the negative one alone goes stale: the shipped roster is listed live rather than
    transcribed, since a blocklist written here stops covering agents added after it was
    written and one is net-new in a later feature.

    Severity being a function of ``code`` is a deliberate divergence from the installed
    runner, whose severity is caller-determined. It is justified because this feature's
    emitter is a hand-authored, byte-compared corpus, where leaving severity to the emitter
    would be unfalsifiable authoring latitude rather than a caller's judgement.
    """

    def setUp(self) -> None:
        self.assertIsNotNone(claude_route_fallback, "claude_route_fallback is not importable")
        self.module = claude_route_fallback
        self.corpus = self.module.load_corpus()
        self.cases = self.corpus["cases"]

    def emitted_diagnostics(self) -> list[tuple[str, dict[str, object]]]:
        emitted: list[tuple[str, dict[str, object]]] = []
        for case in self.cases:
            policy = case["policy"]
            produced = self.module.resolve(
                policy, case["snapshot"], case["overrides"], policy["budgets"]
            )
            for origin, report in (("pinned", case["expected_report"]), ("produced", produced)):
                for entry in report["diagnostics"]:
                    emitted.append((f"{case['case_id']}/{origin}", entry))
        return emitted

    def declared_role_classes(self) -> list[tuple[str, object]]:
        declared: list[tuple[str, object]] = []
        for case in self.cases:
            policy = case["policy"]
            declared.append((case["case_id"], policy["agent"]["role_class"]))
            helper = policy.get("optional_helper")
            if helper is not None:
                declared.append((f"{case['case_id']}/helper", helper["agent"]["role_class"]))
        return declared

    def test_every_agent_name_in_the_corpus_carries_the_fixture_prefix(self) -> None:
        names = agent_names_in(self.cases)
        self.assertTrue(names, "no agent name was reached, so this assertion covers nothing")
        for name in sorted(names):
            with self.subTest(agent=name):
                self.assertTrue(name.startswith(FIXTURE_NAME_PREFIX))

    def test_no_shipped_agent_name_appears_anywhere_in_the_corpus(self) -> None:
        roster = shipped_agent_roster()
        self.assertTrue(roster, f"{AGENTS_ROOT} listed no agent, so this assertion covers nothing")
        corpus = self.module.serialize_report(self.corpus)
        for name in sorted(roster):
            with self.subTest(agent=name):
                self.assertNotIn(name, corpus)

    def test_every_declared_agent_holds_one_of_the_three_synthetic_role_classes(self) -> None:
        declared = self.declared_role_classes()
        self.assertTrue(declared, "no role class was reached, so this assertion covers nothing")
        for location, role_class in declared:
            with self.subTest(agent=location):
                self.assertIn(role_class, SYNTHETIC_ROLE_CLASSES)

    def test_the_severity_and_action_maps_cover_both_closed_vocabularies(self) -> None:
        schema = load_contract(CONTRACT_ROOT / "route-resolution-report.schema.json")
        codes = set(read_by_pointer(schema, RESOLUTION_CODE_POINTER)) | set(
            read_by_pointer(schema, POLICY_VIOLATION_CODE_POINTER)
        )
        self.assertEqual(set(SEVERITY_BY_CODE), codes)
        self.assertEqual(set(ACTIONS_BY_CODE), codes)
        allocated = {action for actions in ACTIONS_BY_CODE.values() for action in actions}
        self.assertEqual(allocated, set(read_by_pointer(schema, REMEDIATION_ACTION_POINTER)))

    def test_every_emitted_diagnostic_carries_the_severity_its_code_fixes(self) -> None:
        emitted = self.emitted_diagnostics()
        self.assertTrue(emitted, "no diagnostic was emitted, so this assertion covers nothing")
        for location, entry in emitted:
            with self.subTest(diagnostic=location, code=entry["code"]):
                self.assertEqual(entry["severity"], SEVERITY_BY_CODE[str(entry["code"])])

    def test_every_emitted_diagnostic_carries_the_actions_its_code_allocates(self) -> None:
        for location, entry in self.emitted_diagnostics():
            with self.subTest(diagnostic=location, code=entry["code"]):
                actions = entry["remediation"]["actions"]
                self.assertEqual(actions, ACTIONS_BY_CODE[str(entry["code"])])

    def test_every_emitted_diagnostic_names_this_module_as_its_source(self) -> None:
        for location, entry in self.emitted_diagnostics():
            with self.subTest(diagnostic=location):
                self.assertEqual(entry["source"], DIAGNOSTIC_SOURCE)


TEST_CASES = (
    CommittedContractIdentityTests,
    SimulatorSerializationSurfaceTests,
    ResolutionWalkTests,
    PreferredModelUnavailableTests,
    EffortUnsupportedTests,
    CapabilityProbeUnavailableTests,
    TreatmentProbeFailedTests,
    DiagnosticEmissionOrderTests,
    EffectiveDispatchTupleTests,
    ReportScopedFieldTests,
    CorpusContractValidationTests,
    ReplayDeterminismTests,
    SingleSerializerDisciplineTests,
    RoadmapParityTests,
    ClosedVocabularySetEqualityTests,
    InlineNegativeValidationTests,
    CorpusEnvelopeTests,
    FixtureHygieneTests,
)


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for case in TEST_CASES:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    return suite


if __name__ == "__main__":
    raise SystemExit(run_counted(build_suite(), label="test-route-fallback-simulation"))
