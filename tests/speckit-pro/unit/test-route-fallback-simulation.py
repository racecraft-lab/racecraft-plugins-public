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
        # Rejected for an unavailable capability probe rather than an exact-invocation
        # failure, so the walk spends no retry and this report ends below every cap —
        # which keeps the closing omission assertion an unconditional claim about the
        # terminal entry's shape rather than one contingent on the at-cap set.
        preferred = route_of("preferred-terminal", "alias-terminal", "model-terminal")
        snapshot = snapshot_for(preferred, probe={"model-terminal": False})
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
        actual, declared = report["budgets"]["actual"], report["budgets"]["declared"]
        self.assertTrue(all(actual[key] < declared[f"max_{key}"] for key in actual))
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
        del preferred["resolved_model"]
        # Asserted against the walk-entry guard rather than through ``resolve``: such a
        # route no longer REACHES the walk, because the pre-walk pass rejects it with
        # ``silent_inherit_materialization`` first. The guard is what keeps a route that
        # arrives by any other path from resolving to an incomplete dispatch tuple.
        with self.assertRaises(self.module.RouteFallbackError):
            self.module._require_pinned_tuple(preferred)

    def test_a_route_reaching_the_walk_without_a_pinned_effort_fails_closed(self) -> None:
        preferred = route_of("preferred-effortless", "alias-effortless", "model-effortless")
        del preferred["effort"]
        with self.assertRaises(self.module.RouteFallbackError):
            self.module._require_pinned_tuple(preferred)


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
        # The prohibition is what matters here: writing the no-helper triple for a policy
        # that DOES declare one would be a false claim, and in a byte-compared corpus a
        # false claim is indistinguishable from a true one until someone reads the policy.
        report = self.resolve(policy, snapshot_for(preferred, helper_route))
        self.assertNotEqual(
            report["optional_helper"],
            {"consulted": False, "no_helper_path_validated": True, "probe_attempts": 0},
        )
        self.assertIs(report["optional_helper"]["consulted"], True)
        # A helper whose consultation cannot be accounted for still fails closed.
        policy["optional_helper"]["preferred_route"] = {
            "route_id": "helper-unaccountable",
            "alias": "alias-helper-unaccountable",
            "qualified": True,
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
        # Held by identity and position rather than by count: appended cases must leave
        # these nine at the head in the same order, and a bare length would still pass if
        # an appended case displaced one of them. The total is asserted separately.
        self.assertEqual(len(SLICE_ONE_CASE_IDS), 9)
        self.assertEqual(
            [case["case_id"] for case in self.cases[: len(SLICE_ONE_CASE_IDS)]],
            list(SLICE_ONE_CASE_IDS),
        )

    def test_the_route_contract_admits_an_omitted_model_the_simulator_rejects(self) -> None:
        inheriting = {"route_id": "preferred-inherits", "alias": "alias-inherits", "qualified": True}
        policy = policy_of(inheriting)
        self.assertEqual(
            validate_instance(policy, self.contracts["policy"]),
            policy,
        )
        # Rejected with a diagnostic rather than at validation, which is the whole reason
        # the route contract leaves both members optional: tightening it would fail this
        # fixture before any diagnostic could be produced.
        report = self.resolve(policy, snapshot_for())
        self.assertEqual(self.codes(report), ["silent_inherit_materialization", "no_safe_route"])
        self.assertEqual(report["attempted_routes"], [])

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
LAYER6_ROOT = TEST_ROOT / "layer6-efficiency"
SIMULATOR_PATH = LAYER6_LIB_DIR / "claude_route_fallback.py"

# FR-029: the simulator is report-only, so no call that mutates a path and no module
# whose reason for existing is mutating one may appear in it. Named as data because a
# failure should say which capability leaked in, and because the two lists are the
# audit's whole surface — an unnamed write primitive would pass silently.
MUTATING_CALLS = frozenset(
    {
        "write_text",
        "write_bytes",
        "write",
        "writelines",
        "unlink",
        "rmdir",
        "mkdir",
        "rename",
        "replace",
        "touch",
        "chmod",
        "symlink_to",
        "hardlink_to",
    }
)
MUTATION_CAPABLE_MODULES = frozenset({"os", "shutil", "tempfile", "subprocess", "io"})
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


def simulator_syntax_tree() -> ast.Module:
    """The simulator module's own syntax tree.

    Read from the committed source rather than from the imported object, because the
    property under test is what the module *may* do, not what one call happened to do:
    a write reachable only on an untaken branch would be invisible to any behavioural
    probe and is exactly what FR-029's report-only obligation forbids.
    """
    source = SIMULATOR_PATH.read_text(encoding="utf-8")
    return ast.parse(source, filename=str(SIMULATOR_PATH))


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


# --------------------------------------------------------------------------- #
# Structural rejections, the override branches, and the helper path             #
# --------------------------------------------------------------------------- #
# The four policy-authoring violations partition by the state they need, and the
# partition is load bearing rather than tidy: three are properties of the policy
# DOCUMENT and are decided before the first route is attempted, while
# ``fallback_loop`` is decided against walk state, on reaching a route already
# attempted. Deciding a loop pre-walk would convert a policy that RESOLVES into a
# failing one, because a duplicate later in the chain is never reached when an
# earlier route resolves — which is exactly what the negative case below pins.

# The nine cases the corpus opened with, in declaration order. Named rather than
# counted, because the appended cases must leave these nine at the head in the same
# order: a bare length would still pass if an appended case displaced one of them.
SLICE_ONE_CASE_IDS = (
    "preferred-absent-fallback-selected",
    "fable-alias-model-absent",
    "alias-unresolved",
    "alias-repointed",
    "platform-route-changed",
    "effort-unsupported",
    "capability-probe-unavailable",
    "treatment-probe-failed",
    "preferred-probe-success-clean",
)

# The cases appended at the tail, in declaration order.
APPENDED_CASE_IDS = (
    "fallback-loop",
    "unqualified-adjacent-model",
    "generic-agent-substitution",
    "silent-inherit-materialization",
    "unqualified-override",
    "override-skipped-by-allowlist",
    "helper-unavailable-continues",
    "budget-exhaustion-of-one",
    "no-safe-route-report-only",
)

# The report's not-consulted helper triple, which is also the no-helper-declared
# triple: identical by design, since whether a helper exists is a property of the
# policy and every case carries its own policy.
NO_HELPER_PATH = {"consulted": False, "no_helper_path_validated": True, "probe_attempts": 0}
UNSPENT_BUDGET = {"probe_attempts": 0, "retries": 0, "candidate_routes": 0}

# The documented environment variable, and the value it accepts to restore normal
# model resolution. The sentinel is a SET value that behaves as unset, so it is the
# no-override state rather than an override.
OVERRIDE_VARIABLE = "CLAUDE_CODE_SUBAGENT_MODEL"
INHERIT_SENTINEL = "inherit"


def unqualified_adjacent_route(
    route_id: str, alias: str, model: str, *, adjacent_to: str
) -> dict[str, object]:
    """A fallback declaring adjacency to a sibling while not itself being qualified."""
    route = route_of(route_id, alias, model)
    route["qualified"] = False
    route["adjacent_to"] = adjacent_to
    return route


def substituting_route(
    route_id: str, alias: str, model: str, *, agent: str, agent_class: str = "generic"
) -> dict[str, object]:
    """A fallback dispatching a different agent than the policy's own subject."""
    route = route_of(route_id, alias, model)
    route["substituted_agent"] = {"name": agent, "class": agent_class}
    return route


def inheriting_route(route_id: str, alias: str, **pinned: str) -> dict[str, object]:
    """A route leaving one or both dispatch members to be materialized by inheritance."""
    return {"route_id": route_id, "alias": alias, "qualified": True, **pinned}


def helper_declaration(
    *routes: dict[str, object], name: str = "fixture-optional-helper"
) -> dict[str, object]:
    """The policy member by which a policy declares its optional helper."""
    preferred, *fallbacks = routes
    return {
        "agent": {"name": name, "role_class": "optional_helper"},
        "preferred_route": dict(preferred),
        "fallback_routes": [dict(each) for each in fallbacks],
    }


def allowlisting(snapshot: dict[str, object], *models: str) -> dict[str, object]:
    """The same snapshot with the organization allowlist narrowed to ``models``.

    Narrowed by replacement rather than by a builder parameter, so the slice-1
    builder every other case reads keeps the signature those cases were written
    against. The allowlist is the one snapshot member with no default worth
    inferring: it is what the organization permits, not what the environment offers.
    """
    return {**snapshot, "available_models_allowlist": list(models)}


def capping(policy: dict[str, object], **caps: int) -> dict[str, object]:
    """The same policy with one or more declared budget caps narrowed.

    A wrapper for the same reason ``allowlisting`` is one: ``policy_of`` is the
    slice-1 builder every earlier case was written against, and narrowing a cap is
    a per-case difference rather than a default worth carrying in that signature.
    """
    declared = dict(policy["budgets"])  # type: ignore[arg-type]
    declared.update(caps)
    return {**policy, "budgets": declared}


class StructuralPreWalkTests(SimulatorCaseMixin, unittest.TestCase):
    """FR-019c, FR-021, FR-022, FR-023: three document-level defects, decided pre-walk.

    Each of the three is decidable by reading the declared routes with no walk state,
    so the pass runs to completion before the first route is attempted and suppresses
    the walk entirely when it emits anything. The report a rejection produces is an
    ordinary valid instance of the one report shape — empty attempt array, all three
    counters unspent, the policy's own agent named unresolved — not an under-specified
    one, which is why the array's lower bound admits zero.
    """

    def setUp(self) -> None:
        super().setUp()
        self.policy_contract = load_contract(CONTRACT_ROOT / "route-policy.schema.json")

    def adjacent_pair(self) -> tuple[dict[str, object], dict[str, object]]:
        anchor = route_of("preferred-anchor", "alias-anchor", "model-anchor")
        adjacent = unqualified_adjacent_route(
            "fallback-adjacent", "alias-adjacent", "model-adjacent", adjacent_to="preferred-anchor"
        )
        return policy_of(anchor, (adjacent,)), snapshot_for(anchor, adjacent)

    def substituting_pair(self) -> tuple[dict[str, object], dict[str, object]]:
        named = route_of("preferred-named-agent", "alias-named-agent", "model-named-agent")
        generic = substituting_route(
            "fallback-generic", "alias-generic", "model-generic", agent="fixture-generic-stand-in"
        )
        return policy_of(named, (generic,)), snapshot_for(named, generic)

    def inheriting_pair(self, **pinned: str) -> tuple[dict[str, object], dict[str, object]]:
        explicit = route_of("preferred-explicit", "alias-explicit", "model-explicit")
        inheriting = inheriting_route("fallback-inheriting", "alias-inheriting", **pinned)
        return policy_of(explicit, (inheriting,)), snapshot_for(explicit)

    # --- the pass itself (FR-019c) ---

    def test_the_pre_walk_pass_is_staged_over_three_codes_and_not_four(self) -> None:
        staged = tuple(name for name, _ in self.module.PRE_WALK_STAGES)
        self.assertEqual(staged, tuple(self.module.PRE_WALK_VIOLATION_CODES))
        self.assertEqual(len(staged), 3)
        self.assertNotIn("fallback_loop", staged)
        self.assertNotIn("unqualified_override", staged)
        self.assertEqual(
            list(staged),
            [code for code in self.module.POLICY_VIOLATION_CODES if code in set(staged)],
        )

    def test_a_pre_walk_rejection_records_an_empty_attempt_array(self) -> None:
        policy, snapshot = self.adjacent_pair()
        self.assertEqual(self.resolve(policy, snapshot)["attempted_routes"], [])

    def test_a_pre_walk_rejection_reports_the_contracted_no_safe_route_shape(self) -> None:
        policy, snapshot = self.adjacent_pair()
        report = self.resolve(policy, snapshot)
        self.assertEqual(report["outcome"], "no_safe_route")
        self.assertEqual(report["unresolved_agent"], "fixture-required-executor")
        self.assertNotIn("effective_dispatch_tuple", report)
        self.assertEqual(report["budgets"]["actual"], dict(UNSPENT_BUDGET))
        self.assertEqual(report["optional_helper"], dict(NO_HELPER_PATH))
        self.assertIs(report["release_claim_eligible"], False)

    def test_the_pass_suppresses_the_walk_even_where_a_route_would_have_resolved(self) -> None:
        policy, snapshot = self.adjacent_pair()
        report = self.resolve(policy, snapshot)
        self.assertEqual(report["budgets"]["actual"]["probe_attempts"], 0)
        clean = self.resolve(policy_of(policy["preferred_route"]), snapshot)
        self.assertEqual(clean["outcome"], "resolved")

    def test_the_attempt_array_is_empty_only_when_the_pass_rejected_the_policy(self) -> None:
        rejected, snapshot = self.adjacent_pair()
        walked = policy_of(rejected["preferred_route"])
        failing = route_of("preferred-terminates", "alias-terminates", "model-terminates")
        for label, policy, environment in (
            ("pre-walk rejection", rejected, snapshot),
            ("clean resolution", walked, snapshot),
            (
                "no safe route",
                policy_of(failing),
                snapshot_for(failing, invocation={"model-terminates": "failure"}),
            ),
        ):
            with self.subTest(input=label):
                report = self.resolve(policy, environment)
                self.assertEqual(
                    report["attempted_routes"] == [],
                    self.module._pre_walk_violations(policy) != [],
                )

    def test_the_pass_violations_lead_the_array_and_the_terminal_entry_closes_it(self) -> None:
        anchor = route_of("preferred-anchor", "alias-anchor", "model-anchor")
        adjacent = unqualified_adjacent_route(
            "fallback-adjacent", "alias-adjacent", "model-adjacent", adjacent_to="preferred-anchor"
        )
        generic = substituting_route(
            "fallback-generic", "alias-generic", "model-generic", agent="fixture-generic-stand-in"
        )
        policy = policy_of(anchor, (adjacent, generic))
        report = self.resolve(policy, snapshot_for(anchor, adjacent, generic))
        self.assertEqual(
            self.codes(report),
            ["unqualified_adjacent_model", "generic_agent_substitution", "no_safe_route"],
        )

    def test_two_violations_on_one_route_follow_the_declaration_order(self) -> None:
        anchor = route_of("preferred-anchor", "alias-anchor", "model-anchor")
        both = substituting_route(
            "fallback-both", "alias-both", "model-both", agent="fixture-generic-stand-in"
        )
        both["qualified"] = False
        both["adjacent_to"] = "preferred-anchor"
        policy = policy_of(anchor, (both,))
        report = self.resolve(policy, snapshot_for(anchor, both))
        self.assertEqual(
            self.codes(report),
            ["unqualified_adjacent_model", "generic_agent_substitution", "no_safe_route"],
        )

    # --- unqualified_adjacent_model (FR-021) ---

    def test_an_unqualified_fallback_adjacent_to_a_qualified_route_is_rejected(self) -> None:
        policy, snapshot = self.adjacent_pair()
        entry = self.only_diagnostic(self.resolve(policy, snapshot), "unqualified_adjacent_model")
        self.assertEqual(entry["severity"], "error")
        self.assertEqual(entry["details"], {"route_id": "fallback-adjacent"})
        self.assertEqual(
            entry["remediation"]["actions"], ["Replace the adjacent model with a qualified route."]
        )

    def test_the_rejected_adjacent_fallback_is_never_selected(self) -> None:
        policy, snapshot = self.adjacent_pair()
        report = self.resolve(policy, snapshot)
        self.assertEqual(
            [entry["route_id"] for entry in report["attempted_routes"]], []
        )
        self.assertNotIn("effective_dispatch_tuple", report)

    def test_a_qualified_route_declaring_adjacency_is_not_rejected(self) -> None:
        anchor = route_of("preferred-anchor", "alias-anchor", "model-anchor")
        adjacent = route_of("fallback-adjacent", "alias-adjacent", "model-adjacent")
        adjacent["adjacent_to"] = "preferred-anchor"
        policy = policy_of(anchor, (adjacent,))
        self.assertEqual(self.module._pre_walk_violations(policy), [])

    def test_an_unqualified_route_declaring_no_adjacency_is_not_rejected_by_this_rule(self) -> None:
        anchor = route_of("preferred-anchor", "alias-anchor", "model-anchor")
        unqualified = route_of("fallback-unqualified", "alias-unqualified", "model-unqualified")
        unqualified["qualified"] = False
        policy = policy_of(anchor, (unqualified,))
        self.assertEqual(self.module._pre_walk_violations(policy), [])

    def test_an_adjacency_naming_no_declared_sibling_fails_closed(self) -> None:
        anchor = route_of("preferred-anchor", "alias-anchor", "model-anchor")
        dangling = unqualified_adjacent_route(
            "fallback-dangling", "alias-dangling", "model-dangling", adjacent_to="no-such-route"
        )
        policy = policy_of(anchor, (dangling,))
        with self.assertRaises(self.module.RouteFallbackError):
            self.module._pre_walk_violations(policy)

    # --- generic_agent_substitution (FR-022) ---

    def test_a_generic_agent_substitution_is_rejected(self) -> None:
        policy, snapshot = self.substituting_pair()
        entry = self.only_diagnostic(self.resolve(policy, snapshot), "generic_agent_substitution")
        self.assertEqual(entry["severity"], "error")
        self.assertEqual(entry["details"], {"route_id": "fallback-generic"})
        self.assertEqual(
            entry["remediation"]["actions"], ["Restore the named agent in the fallback route."]
        )

    def test_a_named_agent_substitution_is_not_rejected(self) -> None:
        named = route_of("preferred-named-agent", "alias-named-agent", "model-named-agent")
        substituting = substituting_route(
            "fallback-named",
            "alias-named",
            "model-named",
            agent="fixture-named-stand-in",
            agent_class="named",
        )
        policy = policy_of(named, (substituting,))
        self.assertEqual(self.module._pre_walk_violations(policy), [])

    # --- silent_inherit_materialization (FR-023) ---

    def test_a_route_omitting_its_resolved_model_is_admitted_then_rejected(self) -> None:
        policy, snapshot = self.inheriting_pair(effort="high")
        self.assertEqual(validate_instance(policy, self.policy_contract), policy)
        entry = self.only_diagnostic(
            self.resolve(policy, snapshot), "silent_inherit_materialization"
        )
        self.assertEqual(entry["severity"], "error")
        self.assertEqual(entry["details"], {"route_id": "fallback-inheriting"})
        self.assertEqual(
            entry["remediation"]["actions"],
            ["Declare the model and effort explicitly on the route."],
        )

    def test_a_route_omitting_its_effort_is_admitted_then_rejected(self) -> None:
        policy, snapshot = self.inheriting_pair(resolved_model="model-inheriting")
        self.assertEqual(validate_instance(policy, self.policy_contract), policy)
        report = self.resolve(policy, snapshot)
        self.assertEqual(self.codes(report), ["silent_inherit_materialization", "no_safe_route"])
        self.assertEqual(report["attempted_routes"], [])

    def test_a_route_omitting_both_members_is_rejected_once_naming_the_first(self) -> None:
        policy, snapshot = self.inheriting_pair()
        report = self.resolve(policy, snapshot)
        self.assertEqual(self.codes(report), ["silent_inherit_materialization", "no_safe_route"])
        self.assertIn("resolved_model", report["diagnostics"][0]["message"])

    def test_a_route_pinning_both_members_explicitly_is_not_rejected(self) -> None:
        explicit = route_of("preferred-explicit", "alias-explicit", "model-explicit")
        spare = route_of("fallback-explicit", "alias-explicit-spare", "model-explicit-spare")
        self.assertEqual(self.module._pre_walk_violations(policy_of(explicit, (spare,))), [])

    def test_the_walk_entry_guard_still_fails_closed_on_an_unpinned_route(self) -> None:
        for member in ("resolved_model", "effort"):
            with self.subTest(omitted=member):
                route = route_of("preferred-guarded", "alias-guarded", "model-guarded")
                del route[member]
                with self.assertRaises(self.module.RouteFallbackError):
                    self.module._require_pinned_tuple(route)


class FallbackLoopTests(SimulatorCaseMixin, unittest.TestCase):
    """FR-020, FR-012b, FR-033d: the one violation decided against walk state.

    It is detected on *reaching* the revisit, which fixes both its position in the
    array — after the last attempted route's entries — and the reason it cannot join
    the pre-walk pass: a duplicate later in a chain whose earlier route resolves is
    never reached, so deciding it from the document alone would fail a policy that
    resolves. Needing the attempt list is also why structural validation is a second
    rule family in this one module rather than a second module.
    """

    def looping_policy(self, *, revisited_effort: str = "high") -> dict[str, object]:
        preferred = route_of("preferred-revisited", "alias-revisited", "model-revisited",
                             revisited_effort)
        detour = route_of("fallback-detour", "alias-detour", "model-detour")
        return policy_of(preferred, (detour, dict(preferred)))

    def failing_snapshot(self, policy: dict[str, object]) -> dict[str, object]:
        routes = _declared(policy)
        return snapshot_for(
            *routes,
            invocation={str(route["resolved_model"]): "failure" for route in routes},
        )

    def test_a_revisited_route_terminates_the_walk_without_repeating_it(self) -> None:
        policy = self.looping_policy()
        report = self.resolve(policy, self.failing_snapshot(policy))
        self.assertEqual(
            [entry["route_id"] for entry in report["attempted_routes"]],
            ["preferred-revisited", "fallback-detour"],
        )
        self.assertEqual(report["outcome"], "no_safe_route")

    def test_the_loop_entry_follows_the_last_attempted_routes_entries(self) -> None:
        policy = self.looping_policy()
        report = self.resolve(policy, self.failing_snapshot(policy))
        self.assertEqual(
            self.codes(report),
            [
                "treatment_probe_failed",
                "treatment_probe_failed",
                "fallback_loop",
                "no_safe_route",
            ],
        )

    def test_the_loop_entry_joins_an_attempted_route_by_its_route_id(self) -> None:
        policy = self.looping_policy()
        report = self.resolve(policy, self.failing_snapshot(policy))
        entry = self.only_diagnostic(report, "fallback_loop")
        self.assertEqual(entry["severity"], "error")
        self.assertEqual(entry["details"], {"route_id": "preferred-revisited"})
        self.assertIn(
            entry["details"]["route_id"],
            [attempted["route_id"] for attempted in report["attempted_routes"]],
        )
        self.assertEqual(
            entry["remediation"]["actions"], ["Remove the repeated route from the fallback chain."]
        )

    def test_the_revisited_route_is_not_consulted_a_second_time(self) -> None:
        policy = self.looping_policy()
        report = self.resolve(policy, self.failing_snapshot(policy))
        self.assertEqual(
            report["budgets"]["actual"],
            {"probe_attempts": 2, "retries": 0, "candidate_routes": 2},
        )

    def test_a_chain_whose_earlier_route_resolves_never_reaches_the_revisit(self) -> None:
        policy = self.looping_policy()
        report = self.resolve(policy, snapshot_for(*_declared(policy)))
        self.assertEqual(report["outcome"], "resolved")
        self.assertEqual(self.codes(report), [])
        self.assertEqual(self.module._pre_walk_violations(policy), [])

    def test_a_loop_is_never_decided_by_the_pre_walk_pass(self) -> None:
        policy = self.looping_policy()
        self.assertEqual(self.module._pre_walk_violations(policy), [])
        report = self.resolve(policy, self.failing_snapshot(policy))
        self.assertNotEqual(report["attempted_routes"], [])

    def test_a_loop_disqualifies_the_environment_from_release_claims(self) -> None:
        policy = self.looping_policy()
        report = self.resolve(policy, self.failing_snapshot(policy))
        self.assertIs(report["release_claim_eligible"], False)


class SubagentModelOverrideTests(SimulatorCaseMixin, unittest.TestCase):
    """FR-024, FR-024a, FR-024b: two branches, one of them deliberately bounded.

    The honored branch records the override as what will dispatch — a HYBRID tuple,
    because the variable sets a model only and no documented subagent-effort override
    exists. The allowlist-skip branch records only that the override did not take
    effect: the documented fallback target there is the *inherited* model, which this
    projection does not carry and must not gain, so naming a model that runs instead
    would be inference. Neither branch moves ``outcome``, which follows the qualified
    walk, and both set ``release_claim_eligible`` false.
    """

    def overridden(self, requested: str = "alias-forced") -> dict[str, str]:
        return {OVERRIDE_VARIABLE: requested}

    def forced(self, effort: str = "xhigh") -> dict[str, object]:
        return route_of("preferred-honored", "alias-honored", "model-honored", effort)

    def environment(self, *routes: dict[str, object], permitted: bool = True) -> dict[str, object]:
        """A snapshot offering the declared routes plus the override's own target."""
        target = route_of("route-forced", "alias-forced", "model-forced")
        snapshot = snapshot_for(*routes, target)
        offered = list(snapshot["available_models"])
        return allowlisting(snapshot, *(offered if permitted else
                                        [each for each in offered if each != "model-forced"]))

    def test_an_honored_override_records_the_hybrid_effective_dispatch_tuple(self) -> None:
        preferred = self.forced()
        report = self.resolve(
            policy_of(preferred), self.environment(preferred), self.overridden()
        )
        self.assertEqual(
            report["effective_dispatch_tuple"],
            {
                "agent": "fixture-required-executor",
                "alias": "alias-forced",
                "resolved_model": "model-forced",
                "effort": "xhigh",
            },
        )
        self.assertEqual(report["override"]["tuple"], report["effective_dispatch_tuple"])
        self.assertEqual(report["override"]["disposition"], "honored")
        self.assertEqual(report["override"]["source"], OVERRIDE_VARIABLE)
        self.assertEqual(report["override"]["requested_model"], "alias-forced")

    def test_the_override_supplies_the_model_while_agent_and_effort_are_retained(self) -> None:
        preferred = self.forced("medium")
        spare = route_of("fallback-retained", "alias-retained", "model-retained", "low")
        snapshot = self.environment(preferred, spare)
        snapshot["available_models"] = ["model-forced", "model-retained"]
        report = self.resolve(policy_of(preferred, (spare,)), snapshot, self.overridden())
        self.assertEqual(report["effective_dispatch_tuple"]["effort"], "low")
        self.assertEqual(report["effective_dispatch_tuple"]["agent"], "fixture-required-executor")
        self.assertEqual(report["override"]["would_have_been"]["outcome"], "resolved")

    def test_the_retained_effort_comes_from_the_preferred_route_when_none_was_selected(self) -> None:
        preferred = self.forced("max")
        snapshot = self.environment(preferred)
        snapshot["exact_invocation_probe"]["model-honored"] = "failure"
        report = self.resolve(policy_of(preferred), snapshot, self.overridden())
        self.assertEqual(report["effective_dispatch_tuple"]["effort"], "max")

    def test_an_override_never_promotes_a_no_safe_route_outcome_to_resolved(self) -> None:
        preferred = self.forced()
        snapshot = self.environment(preferred)
        snapshot["exact_invocation_probe"]["model-honored"] = "failure"
        report = self.resolve(policy_of(preferred), snapshot, self.overridden())
        self.assertEqual(report["outcome"], "no_safe_route")
        self.assertEqual(report["unresolved_agent"], "fixture-required-executor")
        self.assertIn("effective_dispatch_tuple", report)
        self.assertEqual(report["override"]["would_have_been"], {"outcome": "no_safe_route"})

    def test_the_would_have_been_tuple_is_omitted_rather_than_present_as_null(self) -> None:
        preferred = self.forced()
        snapshot = self.environment(preferred)
        snapshot["exact_invocation_probe"]["model-honored"] = "failure"
        would_have_been = self.resolve(
            policy_of(preferred), snapshot, self.overridden()
        )["override"]["would_have_been"]
        self.assertNotIn("effective_dispatch_tuple", would_have_been)
        self.assertEqual(set(would_have_been), {"outcome"})

    def test_the_would_have_been_block_records_the_qualified_resolution(self) -> None:
        preferred = self.forced()
        report = self.resolve(
            policy_of(preferred), self.environment(preferred), self.overridden()
        )
        self.assertEqual(
            report["override"]["would_have_been"],
            {
                "outcome": "resolved",
                "effective_dispatch_tuple": {
                    "agent": "fixture-required-executor",
                    "alias": "alias-honored",
                    "resolved_model": "model-honored",
                    "effort": "xhigh",
                },
            },
        )

    def test_the_override_diagnostic_is_scoped_to_no_route_and_proceeds_at_warning(self) -> None:
        preferred = self.forced()
        report = self.resolve(
            policy_of(preferred), self.environment(preferred), self.overridden()
        )
        entry = self.only_diagnostic(report, "unqualified_override")
        self.assertEqual(entry["severity"], "warning")
        self.assertNotIn("details", entry)
        self.assertEqual(
            entry["remediation"]["actions"],
            ["Unset the unqualified subagent-model override before making release claims."],
        )
        self.assertIs(report["override"]["qualified"], False)

    def test_a_qualified_override_is_in_force_without_the_unqualified_diagnostic(self) -> None:
        preferred = route_of("preferred-matching", "alias-forced", "model-forced", "high")
        snapshot = self.environment(preferred)
        report = self.resolve(policy_of(preferred), snapshot, self.overridden())
        self.assertIs(report["override"]["qualified"], True)
        self.assertEqual(self.codes(report), [])
        self.assertIs(report["release_claim_eligible"], False)

    def test_the_override_entry_sits_between_the_walk_and_the_terminal_entry(self) -> None:
        preferred = self.forced()
        snapshot = self.environment(preferred)
        snapshot["exact_invocation_probe"]["model-honored"] = "failure"
        report = self.resolve(policy_of(preferred), snapshot, self.overridden())
        self.assertEqual(
            self.codes(report),
            ["treatment_probe_failed", "unqualified_override", "no_safe_route"],
        )

    def test_an_override_is_independent_of_the_pre_walk_pass(self) -> None:
        anchor = route_of("preferred-anchor", "alias-anchor", "model-anchor")
        adjacent = unqualified_adjacent_route(
            "fallback-adjacent", "alias-adjacent", "model-adjacent", adjacent_to="preferred-anchor"
        )
        policy = policy_of(anchor, (adjacent,))
        report = self.resolve(policy, self.environment(anchor, adjacent), self.overridden())
        self.assertEqual(
            self.codes(report),
            ["unqualified_adjacent_model", "unqualified_override", "no_safe_route"],
        )
        self.assertEqual(report["attempted_routes"], [])
        self.assertEqual(report["effective_dispatch_tuple"]["resolved_model"], "model-forced")

    def test_any_override_in_force_disqualifies_the_environment(self) -> None:
        preferred = self.forced()
        for label, permitted in (("honored", True), ("skipped", False)):
            with self.subTest(branch=label):
                report = self.resolve(
                    policy_of(preferred),
                    self.environment(preferred, permitted=permitted),
                    self.overridden(),
                )
                self.assertEqual(report["outcome"], "resolved")
                self.assertIs(report["release_claim_eligible"], False)

    # --- the allowlist-skip branch (FR-024b) ---

    def test_an_allowlist_excluded_override_is_skipped_and_records_no_tuple(self) -> None:
        preferred = self.forced()
        report = self.resolve(
            policy_of(preferred),
            self.environment(preferred, permitted=False),
            self.overridden(),
        )
        self.assertEqual(report["override"]["disposition"], "skipped_by_allowlist")
        self.assertNotIn("tuple", report["override"])

    def test_the_skipped_branch_names_no_model_that_runs_instead(self) -> None:
        preferred = self.forced()
        report = self.resolve(
            policy_of(preferred),
            self.environment(preferred, permitted=False),
            self.overridden(),
        )
        self.assertEqual(
            set(report["override"]),
            {"source", "requested_model", "disposition", "qualified", "would_have_been"},
        )

    def test_the_report_tuple_follows_the_qualified_walk_on_the_skipped_branch(self) -> None:
        preferred = self.forced()
        report = self.resolve(
            policy_of(preferred),
            self.environment(preferred, permitted=False),
            self.overridden(),
        )
        self.assertEqual(
            report["effective_dispatch_tuple"],
            {
                "agent": "fixture-required-executor",
                "alias": "alias-honored",
                "resolved_model": "model-honored",
                "effort": "xhigh",
            },
        )

    def test_the_allowlist_gate_is_independent_of_fixture_declared_qualification(self) -> None:
        preferred = route_of("preferred-matching", "alias-forced", "model-forced", "high")
        spare = route_of("fallback-permitted", "alias-permitted", "model-permitted", "high")
        snapshot = self.environment(preferred, spare, permitted=False)
        snapshot["available_models"] = ["model-permitted"]
        report = self.resolve(policy_of(preferred, (spare,)), snapshot, self.overridden())
        self.assertIs(report["override"]["qualified"], True)
        self.assertEqual(report["override"]["disposition"], "skipped_by_allowlist")
        self.assertEqual(self.codes(report), ["preferred_model_unavailable"])

    def test_a_skipped_override_over_a_walk_that_resolved_nothing_fails_closed(self) -> None:
        preferred = self.forced()
        snapshot = self.environment(preferred, permitted=False)
        snapshot["exact_invocation_probe"]["model-honored"] = "failure"
        with self.assertRaises(self.module.RouteFallbackError):
            self.resolve(policy_of(preferred), snapshot, self.overridden())

    def test_the_inherit_sentinel_is_the_no_override_state_rather_than_an_override(self) -> None:
        preferred = self.forced()
        snapshot = self.environment(preferred)
        with self.assertRaises(self.module.RouteFallbackError):
            self.resolve(policy_of(preferred), snapshot, self.overridden(INHERIT_SENTINEL))
        report = self.resolve(policy_of(preferred), snapshot, None)
        self.assertNotIn("override", report)
        self.assertIs(report["release_claim_eligible"], True)

    def test_an_unrecognised_override_mechanism_fails_closed(self) -> None:
        preferred = self.forced()
        snapshot = self.environment(preferred)
        for label, overrides in (
            ("another variable", {"CLAUDE_CODE_MAIN_MODEL": "model-forced"}),
            ("no variable at all", {}),
            ("an empty value", {OVERRIDE_VARIABLE: ""}),
        ):
            with self.subTest(overrides=label):
                with self.assertRaises(self.module.RouteFallbackError):
                    self.resolve(policy_of(preferred), snapshot, overrides)

    def test_a_full_model_id_override_resolves_to_itself(self) -> None:
        preferred = self.forced()
        report = self.resolve(
            policy_of(preferred), self.environment(preferred), self.overridden("model-forced")
        )
        self.assertEqual(report["override"]["requested_model"], "model-forced")
        self.assertEqual(
            report["effective_dispatch_tuple"]["alias"],
            report["effective_dispatch_tuple"]["resolved_model"],
        )


class OptionalHelperPathTests(SimulatorCaseMixin, unittest.TestCase):
    """FR-025, FR-025a, FR-025b: a structured field, and a counter that makes it checkable.

    Helper unavailability is an environment condition, not a policy-authoring defect,
    so it is never a diagnostic and neither closed enum gains a member for it. The
    required ``probe_attempts`` is what turns "not consulted" from a boolean the
    simulator asserts about itself into a measurable zero: an implementation could
    otherwise probe every helper route and still write ``false`` without changing a
    pinned byte. The counter is disjoint from the agent's own, and the attempt list
    is the corroborating evidence a counter alone cannot supply.
    """

    def required(self) -> dict[str, object]:
        return route_of("preferred-required", "alias-required", "model-required")

    def helper_routes(self) -> tuple[dict[str, object], dict[str, object]]:
        return (
            route_of("helper-preferred", "alias-helper-primary", "model-helper-primary", "medium"),
            route_of("helper-fallback", "alias-helper-spare", "model-helper-spare", "medium"),
        )

    def with_helper(self) -> dict[str, object]:
        policy = policy_of(self.required())
        policy["optional_helper"] = helper_declaration(*self.helper_routes())
        return policy

    def unavailable(self) -> dict[str, object]:
        """A snapshot binding every alias but offering only the required agent's model."""
        required = self.required()
        return snapshot_for(required, *self.helper_routes(), available=("model-required",))

    def available(self) -> dict[str, object]:
        return snapshot_for(self.required(), *self.helper_routes())

    def test_an_unavailable_helper_is_not_consulted_and_the_no_helper_path_is_validated(
        self,
    ) -> None:
        report = self.resolve(self.with_helper(), self.unavailable())
        self.assertEqual(report["optional_helper"], dict(NO_HELPER_PATH))

    def test_the_required_agent_still_resolves_when_the_helper_is_unavailable(self) -> None:
        report = self.resolve(self.with_helper(), self.unavailable())
        self.assertEqual(report["outcome"], "resolved")
        self.assertEqual(report["effective_dispatch_tuple"]["resolved_model"], "model-required")
        self.assertIs(report["release_claim_eligible"], True)

    def test_no_attempted_route_entry_names_a_helper_route(self) -> None:
        report = self.resolve(self.with_helper(), self.unavailable())
        helper_ids = {str(route["route_id"]) for route in self.helper_routes()}
        attempted = {str(entry["route_id"]) for entry in report["attempted_routes"]}
        self.assertEqual(attempted & helper_ids, set())
        self.assertEqual(attempted, {"preferred-required"})

    def test_helper_unavailability_emits_no_diagnostic_entry(self) -> None:
        report = self.resolve(self.with_helper(), self.unavailable())
        self.assertEqual(report["diagnostics"], [])
        for vocabulary in (self.module.RESOLUTION_CODES, self.module.POLICY_VIOLATION_CODES):
            self.assertNotIn("helper_unavailable", vocabulary)

    def test_an_available_helper_is_consulted_with_a_non_zero_probe_count(self) -> None:
        report = self.resolve(self.with_helper(), self.available())
        helper = report["optional_helper"]
        self.assertIs(helper["consulted"], True)
        self.assertIs(helper["no_helper_path_validated"], False)
        self.assertGreaterEqual(helper["probe_attempts"], 1)

    def test_the_helper_counter_is_disjoint_from_the_agents_own_counter(self) -> None:
        report = self.resolve(self.with_helper(), self.available())
        self.assertEqual(report["budgets"]["actual"]["probe_attempts"], 1)
        self.assertEqual(report["optional_helper"]["probe_attempts"], 1)
        unavailable = self.resolve(self.with_helper(), self.unavailable())
        self.assertEqual(unavailable["budgets"]["actual"]["probe_attempts"], 1)
        self.assertEqual(unavailable["optional_helper"]["probe_attempts"], 0)

    def test_a_policy_declaring_no_helper_reports_the_third_state(self) -> None:
        report = self.resolve(policy_of(self.required()), snapshot_for(self.required()))
        self.assertEqual(report["optional_helper"], dict(NO_HELPER_PATH))

    def test_the_helper_walk_stops_at_its_first_compatible_route(self) -> None:
        policy = self.with_helper()
        report = self.resolve(policy, self.available())
        self.assertEqual(report["optional_helper"]["probe_attempts"], 1)

    def test_a_helper_route_reaching_consultation_unpinned_fails_closed(self) -> None:
        policy = policy_of(self.required())
        policy["optional_helper"] = helper_declaration(
            inheriting_route("helper-inheriting", "alias-helper-inheriting")
        )
        with self.assertRaises(self.module.RouteFallbackError):
            self.resolve(policy, snapshot_for(self.required()))


# --------------------------------------------------------------------------- #
# Budget caps, exhaustion enumeration, and no-safe-route recovery                #
# --------------------------------------------------------------------------- #
# The three caps are hard caps rather than advisory counters, and their units are
# what make "never exceeds" falsifiable at all: ``probe_attempts`` takes each
# route's FIRST consultation, ``retries`` takes every consultation after it, and
# ``candidate_routes`` takes each candidate entered. Counting every consultation in
# the first would falsify the ``probe_attempts <= candidate_routes`` invariant and
# make one retry unreachable under a probe cap of one — which is the configuration
# the exhaustion case declares.


class BudgetCapTests(SimulatorCaseMixin, unittest.TestCase):
    """FR-026 and FR-026a: three hard caps, three units, one terminal outcome.

    The retry allowance is the walk's **last resort**, spent only when no further
    candidate route may be entered — either the declared chain is exhausted or the
    candidate cap is reached. Advancing to a declared alternative strictly dominates
    re-consulting a route whose outcome the walk already recorded, so a chain with a
    route still to try never spends one. That ordering is what keeps the retry
    counter a measurable quantity rather than a side effect of every rejection.
    """

    def failing(self, route_id: str = "preferred-retried") -> dict[str, object]:
        """A route whose exact-invocation probe outcome is a failure."""
        return route_of(route_id, f"alias-{route_id}", f"model-{route_id}")

    def failing_snapshot(self, *routes: dict[str, object]) -> dict[str, object]:
        return snapshot_for(
            *routes, invocation={str(each["resolved_model"]): "failure" for each in routes}
        )

    # --- candidate_routes: walk breadth (FR-026) ---

    def test_the_walk_truncates_at_the_declared_candidate_cap(self) -> None:
        preferred = self.failing("preferred-capped")
        spare = route_of("fallback-would-resolve", "alias-would-resolve", "model-would-resolve")
        policy = capping(policy_of(preferred, (spare,)), max_candidate_routes=1)
        report = self.resolve(policy, self.failing_snapshot(preferred, spare))
        self.assertEqual(
            [entry["route_id"] for entry in report["attempted_routes"]], ["preferred-capped"]
        )
        self.assertEqual(report["budgets"]["actual"]["candidate_routes"], 1)
        self.assertEqual(report["outcome"], "no_safe_route")

    def test_a_route_the_cap_excluded_is_never_entered_even_though_it_would_resolve(self) -> None:
        preferred = self.failing("preferred-shadowing")
        spare = route_of("fallback-shadowed", "alias-shadowed", "model-shadowed")
        snapshot = self.failing_snapshot(preferred)
        snapshot["available_models"] = [*snapshot["available_models"], "model-shadowed"]
        snapshot["alias_bindings"]["alias-shadowed"] = "model-shadowed"
        snapshot["supported_efforts"]["model-shadowed"] = list(EFFORT_LADDER)
        snapshot["probe_availability"]["model-shadowed"] = True
        snapshot["exact_invocation_probe"]["model-shadowed"] = "success"
        uncapped = self.resolve(policy_of(preferred, (spare,)), snapshot)
        capped = self.resolve(
            capping(policy_of(preferred, (spare,)), max_candidate_routes=1), snapshot
        )
        self.assertEqual(uncapped["outcome"], "resolved")
        self.assertEqual(capped["outcome"], "no_safe_route")
        self.assertNotIn(
            "fallback-shadowed", [entry["route_id"] for entry in capped["attempted_routes"]]
        )

    def test_candidate_routes_equals_the_attempt_length_under_a_truncated_walk(self) -> None:
        preferred = self.failing("preferred-measured")
        spares = tuple(
            route_of(f"fallback-measured-{index}", f"alias-measured-{index}", f"model-m-{index}")
            for index in range(3)
        )
        policy = capping(policy_of(preferred, spares), max_candidate_routes=2)
        report = self.resolve(policy, self.failing_snapshot(preferred, *spares))
        self.assertEqual(
            report["budgets"]["actual"]["candidate_routes"], len(report["attempted_routes"])
        )
        self.assertEqual(report["budgets"]["actual"]["candidate_routes"], 2)

    # --- retries: the exclusive base (FR-026a) ---

    def test_one_declared_retry_admits_two_consultations_of_one_route(self) -> None:
        preferred = self.failing("preferred-twice")
        policy = capping(
            policy_of(preferred), max_probe_attempts=1, max_retries=1, max_candidate_routes=1
        )
        actual = self.resolve(policy, self.failing_snapshot(preferred))["budgets"]["actual"]
        self.assertEqual(actual["probe_attempts"], 1)
        self.assertEqual(actual["retries"], 1)
        self.assertEqual(actual["candidate_routes"], 1)

    def test_a_retry_raises_the_retry_counter_and_never_the_probe_counter(self) -> None:
        preferred = self.failing("preferred-not-reprobed")
        policy = capping(policy_of(preferred), max_probe_attempts=1, max_retries=2)
        actual = self.resolve(policy, self.failing_snapshot(preferred))["budgets"]["actual"]
        self.assertEqual(actual["retries"], 2)
        self.assertEqual(actual["probe_attempts"], 1)
        self.assertLessEqual(actual["probe_attempts"], actual["candidate_routes"])

    def test_the_retry_allowance_is_not_spent_while_a_further_candidate_remains(self) -> None:
        preferred = self.failing("preferred-superseded")
        spare = route_of("fallback-supersedes", "alias-supersedes", "model-supersedes")
        snapshot = snapshot_for(
            preferred, spare, invocation={str(preferred["resolved_model"]): "failure"}
        )
        snapshot["exact_invocation_probe"]["model-supersedes"] = "success"
        report = self.resolve(policy_of(preferred, (spare,)), snapshot)
        self.assertEqual(report["outcome"], "resolved")
        self.assertEqual(report["budgets"]["actual"]["retries"], 0)

    def test_a_route_whose_probe_outcome_is_not_a_failure_incurs_no_retry(self) -> None:
        preferred = route_of("preferred-effort-only", "alias-effort-only", "model-effort-only", "max")
        snapshot = snapshot_for(preferred, efforts={"model-effort-only": ["low"]})
        actual = self.resolve(policy_of(preferred), snapshot)["budgets"]["actual"]
        self.assertEqual(actual["retries"], 0)
        self.assertEqual(actual["probe_attempts"], 1)

    def test_a_route_rejected_before_probing_incurs_no_retry(self) -> None:
        preferred = route_of("preferred-unconsulted", "alias-unconsulted", "model-unconsulted")
        report = self.resolve(policy_of(preferred), snapshot_for(preferred, available=()))
        self.assertEqual(report["budgets"]["actual"], {
            "probe_attempts": 0,
            "retries": 0,
            "candidate_routes": 1,
        })

    # --- the shared cap guarantee (SC-009) ---

    def test_no_actual_counter_ever_exceeds_its_declared_cap(self) -> None:
        preferred = self.failing("preferred-bounded")
        spares = tuple(
            route_of(f"fallback-bounded-{index}", f"alias-bounded-{index}", f"model-b-{index}")
            for index in range(4)
        )
        snapshot = self.failing_snapshot(preferred, *spares)
        for caps in ({"max_candidate_routes": 1}, {"max_retries": 1}, {"max_probe_attempts": 2}):
            with self.subTest(caps=caps):
                policy = capping(policy_of(preferred, spares), **caps)
                budgets = self.resolve(policy, snapshot)["budgets"]
                for member, count in budgets["actual"].items():
                    self.assertLessEqual(count, budgets["declared"][f"max_{member}"])

    def test_every_committed_case_stays_inside_all_three_declared_caps(self) -> None:
        for case in self.module.load_corpus()["cases"]:
            with self.subTest(case=case["case_id"]):
                budgets = case["expected_report"]["budgets"]
                for member, count in budgets["actual"].items():
                    self.assertLessEqual(count, budgets["declared"][f"max_{member}"])

    def test_every_exhaustion_class_terminates_in_no_safe_route_without_a_new_code(self) -> None:
        preferred = self.failing("preferred-terminating")
        spare = self.failing("fallback-terminating")
        snapshot = self.failing_snapshot(preferred, spare)
        for caps in (
            {"max_candidate_routes": 1},
            {"max_retries": 1},
            {"max_probe_attempts": 1, "max_retries": 1, "max_candidate_routes": 1},
        ):
            with self.subTest(caps=caps):
                report = self.resolve(capping(policy_of(preferred, (spare,)), **caps), snapshot)
                self.assertEqual(report["outcome"], "no_safe_route")
                self.assertEqual(self.codes(report)[-1], "no_safe_route")
        self.assertEqual(len(self.module.RESOLUTION_CODES), 5)


class ExhaustedBudgetEnumerationTests(SimulatorCaseMixin, unittest.TestCase):
    """FR-026a and SC-009: which budgets were spent to their limit, and where that is said.

    Comparing one counter to its cap is not sufficient on its own — a walk can reach a
    cap and still resolve — so the at-cap set is recorded on the terminal entry and
    nowhere else, which is what makes its presence mean "spent to the limit **and** the
    walk failed". It is an ARRAY because with more than one cap reached no budget is
    causally privileged: against a static snapshot a further retry returns the same
    outcome, so no observable report content could settle which one terminated the walk.
    """

    def failing(self, route_id: str) -> dict[str, object]:
        return route_of(route_id, f"alias-{route_id}", f"model-{route_id}")

    def failing_snapshot(self, *routes: dict[str, object]) -> dict[str, object]:
        return snapshot_for(
            *routes, invocation={str(each["resolved_model"]): "failure" for each in routes}
        )

    def terminal(self, report: dict[str, object]) -> dict[str, object]:
        return self.only_diagnostic(report, "no_safe_route")

    def exhausted_in(self, report: dict[str, object]) -> list[list[str]]:
        """Every ``details.exhausted_budget`` the report carries, in array order."""
        return [
            list(entry["details"]["exhausted_budget"])
            for entry in report["diagnostics"]
            if "exhausted_budget" in entry.get("details", {})
        ]

    def test_the_class_vocabulary_is_read_live_from_the_contracts_inline_enum(self) -> None:
        declared = read_by_pointer(
            load_contract(CONTRACT_ROOT / "route-resolution-report.schema.json"),
            "$defs/resolutionDiagnostic/properties/details/properties/exhausted_budget/items/enum",
        )
        self.assertEqual(list(self.module.EXHAUSTED_BUDGET_CLASSES), declared)
        self.assertEqual(
            set(self.module.EXHAUSTED_BUDGET_CLASSES),
            set(self.module.BUDGET_CAP_OF),
        )

    def test_all_three_at_cap_classes_are_listed_in_the_enums_declaration_order(self) -> None:
        preferred = self.failing("preferred-all-at-cap")
        policy = capping(
            policy_of(preferred), max_probe_attempts=1, max_retries=1, max_candidate_routes=1
        )
        report = self.resolve(policy, self.failing_snapshot(preferred))
        self.assertEqual(
            self.terminal(report)["details"]["exhausted_budget"],
            list(self.module.EXHAUSTED_BUDGET_CLASSES),
        )

    def test_a_single_at_cap_class_is_recorded_alone(self) -> None:
        preferred = route_of("preferred-only-candidate", "alias-only-cand", "model-only-cand")
        spare = route_of("fallback-unreached", "alias-unreached-cap", "model-unreached-cap")
        snapshot = snapshot_for(preferred, spare, available=("model-unreached-cap",))
        policy = capping(policy_of(preferred, (spare,)), max_candidate_routes=1)
        report = self.resolve(policy, snapshot)
        self.assertEqual(
            self.terminal(report)["details"]["exhausted_budget"], ["candidate_routes"]
        )

    def test_the_field_is_omitted_rather_than_emitted_empty_when_no_class_is_at_cap(self) -> None:
        preferred = route_of("preferred-below-cap", "alias-below-cap", "model-below-cap")
        report = self.resolve(policy_of(preferred), snapshot_for(preferred, available=()))
        terminal = self.terminal(report)
        self.assertNotIn("details", terminal)
        self.assertEqual(self.exhausted_in(report), [])

    def test_the_two_necessarily_empty_at_cap_endings_omit_the_field(self) -> None:
        """A pre-walk rejection fixes all three counters at zero against caps whose
        minimum is one; a rejection over an empty fallback list can end below every cap.
        Both are committed cases, so the omission is pinned rather than only inline."""
        for case_id in (
            "fable-alias-model-absent",
            "unqualified-adjacent-model",
            "generic-agent-substitution",
            "silent-inherit-materialization",
        ):
            with self.subTest(case=case_id):
                case = next(
                    each
                    for each in self.module.load_corpus()["cases"]
                    if each["case_id"] == case_id
                )
                self.assertEqual(self.exhausted_in(case["expected_report"]), [])

    def test_a_resolved_walk_that_reaches_a_cap_records_no_at_cap_set(self) -> None:
        """The conjunction a counter comparison cannot express: counter equals cap on a
        report that nevertheless resolved, so nothing is enumerated anywhere."""
        preferred = route_of("preferred-reached-cap", "alias-reached-a", "model-reached-a")
        spare = route_of("fallback-reached-cap", "alias-reached-b", "model-reached-b")
        snapshot = snapshot_for(preferred, spare, available=("model-reached-b",))
        policy = capping(policy_of(preferred, (spare,)), max_probe_attempts=1)
        report = self.resolve(policy, snapshot)
        self.assertEqual(report["outcome"], "resolved")
        self.assertEqual(
            report["budgets"]["actual"]["probe_attempts"],
            report["budgets"]["declared"]["max_probe_attempts"],
        )
        self.assertEqual(self.exhausted_in(report), [])

    def test_the_at_cap_set_appears_on_the_terminal_entry_and_on_no_other(self) -> None:
        preferred = self.failing("preferred-sole-bearer")
        policy = capping(
            policy_of(preferred), max_probe_attempts=1, max_retries=1, max_candidate_routes=1
        )
        report = self.resolve(policy, self.failing_snapshot(preferred))
        bearers = [
            entry["code"]
            for entry in report["diagnostics"]
            if "exhausted_budget" in entry.get("details", {})
        ]
        self.assertEqual(bearers, ["no_safe_route"])
        self.assertGreater(len(report["diagnostics"]), 1)

    def test_no_committed_case_carries_the_field_outside_a_terminal_entry(self) -> None:
        for case in self.module.load_corpus()["cases"]:
            with self.subTest(case=case["case_id"]):
                for entry in case["expected_report"]["diagnostics"]:
                    if "exhausted_budget" in entry.get("details", {}):
                        self.assertEqual(entry["code"], "no_safe_route")

    def test_every_enumerated_class_actually_equals_its_declared_cap(self) -> None:
        """The set is a pure function of the counters and caps the report already
        carries, so it is re-derivable and cannot disagree with them."""
        for case in self.module.load_corpus()["cases"]:
            report = case["expected_report"]
            budgets = report["budgets"]
            expected = [
                member
                for member in self.module.EXHAUSTED_BUDGET_CLASSES
                if budgets["actual"][member] == budgets["declared"][f"max_{member}"]
            ]
            recorded = self.exhausted_in(report)
            with self.subTest(case=case["case_id"]):
                if report["outcome"] == "no_safe_route" and expected:
                    self.assertEqual(recorded, [expected])
                else:
                    self.assertEqual(recorded, [])


class NoSafeRouteRecoveryTests(SimulatorCaseMixin, unittest.TestCase):
    """FR-029, FR-029a, SC-010: the report-only outcome, and what it owes a consumer.

    The obligations attach to the **outcome**, not to FR-029's stated precondition, so
    they hold however the walk ended — every declared fallback rejected, an empty
    fallback list, a candidate cap reached, or a pre-walk structural rejection. A
    truncated walk ends with routes that were never reached and therefore never
    rejected, yet still terminates here, so a precondition-attached reading would let
    it escape the remediation requirement on a technicality.

    Report-only is asserted structurally rather than promised: the module opens no file
    for writing at all, so there is no shipped agent file it could mutate.
    """

    ROLLBACK = "Roll back to the previous plugin release."

    # Every way a walk can end in no_safe_route, so the outcome-attached obligations are
    # checked over the whole family rather than over the one ending FR-029 names.
    def endings(self) -> list[tuple[str, dict[str, object]]]:
        rejected = route_of("preferred-rejected-all", "alias-rejected-all", "model-rejected-all")
        spare = route_of("fallback-rejected-all", "alias-rejected-spare", "model-rejected-spare")
        every_fallback = self.resolve(
            policy_of(rejected, (spare,)), snapshot_for(rejected, spare, available=())
        )

        lonely = route_of("preferred-no-fallback", "alias-no-fallback", "model-no-fallback")
        empty_list = self.resolve(policy_of(lonely), snapshot_for(lonely, available=()))

        capped = route_of("preferred-cap-ended", "alias-cap-ended", "model-cap-ended")
        reachable = route_of("fallback-cap-ended", "alias-cap-spare", "model-cap-spare")
        cap_reached = self.resolve(
            capping(policy_of(capped, (reachable,)), max_candidate_routes=1),
            snapshot_for(capped, reachable, probe={"model-cap-ended": False}),
        )

        explicit = route_of("preferred-pre-walk", "alias-pre-walk", "model-pre-walk")
        inheriting = inheriting_route("fallback-pre-walk", "alias-pre-walk-inherit")
        pre_walk = self.resolve(policy_of(explicit, (inheriting,)), snapshot_for(explicit))

        return [
            ("every fallback rejected", every_fallback),
            ("empty fallback list", empty_list),
            ("candidate cap reached", cap_reached),
            ("pre-walk rejection", pre_walk),
        ]

    def test_every_ending_names_the_unresolved_agent_and_stays_report_only(self) -> None:
        for label, report in self.endings():
            with self.subTest(ending=label):
                self.assertEqual(report["outcome"], "no_safe_route")
                self.assertEqual(report["unresolved_agent"], report["agent"])
                self.assertIs(report["release_claim_eligible"], False)
                self.assertNotIn("effective_dispatch_tuple", report)

    def test_every_ending_closes_with_one_terminal_entry_bearing_the_rollback(self) -> None:
        for label, report in self.endings():
            with self.subTest(ending=label):
                terminal = [
                    entry for entry in report["diagnostics"] if entry["code"] == "no_safe_route"
                ]
                self.assertEqual(len(terminal), 1)
                self.assertIs(report["diagnostics"][-1], terminal[0])
                self.assertEqual(terminal[0]["severity"], "error")
                self.assertIn(self.ROLLBACK, terminal[0]["remediation"]["actions"])
                self.assertTrue(terminal[0]["remediation"]["summary"])

    def test_the_rollback_action_appears_on_the_terminal_entry_and_on_no_other(self) -> None:
        for label, report in self.endings():
            for entry in report["diagnostics"][:-1]:
                with self.subTest(ending=label, code=entry["code"]):
                    self.assertNotIn(self.ROLLBACK, entry["remediation"]["actions"])
                    self.assertLessEqual(len(entry["remediation"]["actions"]), 3)

    def test_every_attempted_route_of_a_failing_walk_is_recorded_as_rejected(self) -> None:
        for label, report in self.endings():
            with self.subTest(ending=label):
                dispositions = {
                    entry["disposition"] for entry in report["attempted_routes"]
                }
                self.assertLessEqual(dispositions, {"rejected"})

    def test_every_route_scoped_diagnostic_joins_a_route_by_its_key(self) -> None:
        """FR-029a: joinable, not merely co-present. Position is not a key here — a
        variable number of diagnostics is emitted per route, so the two arrays are not
        the same length and cannot be zipped."""
        for label, report in self.endings():
            attempted = {entry["route_id"] for entry in report["attempted_routes"]}
            for entry in report["diagnostics"]:
                if entry["code"] == "no_safe_route":
                    continue
                with self.subTest(ending=label, code=entry["code"]):
                    self.assertIn("route_id", entry["details"])
                    if attempted:
                        self.assertIn(entry["details"]["route_id"], attempted)

    def test_every_committed_failing_case_joins_each_reason_to_its_route(self) -> None:
        for case in self.module.load_corpus()["cases"]:
            report = case["expected_report"]
            if report["outcome"] != "no_safe_route":
                continue
            declared = {case["policy"]["preferred_route"]["route_id"]} | {
                route["route_id"] for route in case["policy"]["fallback_routes"]
            }
            with self.subTest(case=case["case_id"]):
                self.assertEqual(report["diagnostics"][-1]["code"], "no_safe_route")
                self.assertIn(
                    self.ROLLBACK, report["diagnostics"][-1]["remediation"]["actions"]
                )
                for entry in report["diagnostics"][:-1]:
                    self.assertIn(entry["details"]["route_id"], declared)

    # --- report-only, proven structurally (FR-029) ---

    def test_the_simulator_opens_no_file_for_writing_and_imports_no_write_tool(self) -> None:
        tree = simulator_syntax_tree()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = (
                    node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else getattr(node.func, "id", "")
                )
                self.assertNotIn(name, MUTATING_CALLS, f"{name} mutates the filesystem")
                if name == "open":
                    modes = [
                        arg.value
                        for arg in [*node.args, *(kw.value for kw in node.keywords)]
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
                    ]
                    self.assertTrue(
                        all(set(mode) <= set("rbt") for mode in modes),
                        f"open called with a write mode: {modes}",
                    )
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    root = (alias.name or "").split(".")[0]
                    self.assertNotIn(root, MUTATION_CAPABLE_MODULES)
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn((node.module or "").split(".")[0], MUTATION_CAPABLE_MODULES)

    def test_the_only_file_the_simulator_reads_is_the_committed_corpus(self) -> None:
        tree = simulator_syntax_tree()
        readers = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and called_names(node) & {"read_text", "read_bytes", "open"}
        }
        self.assertEqual(readers, {"load_corpus"})

    def test_no_path_the_simulator_declares_reaches_the_shipped_agent_tree(self) -> None:
        declared = (
            self.module.CONTRACT_ROOT,
            self.module.FIXTURE_ROOT,
            self.module.DEFAULT_CORPUS_PATH,
            self.module.REPORT_SCHEMA_PATH,
            self.module.POLICY_SCHEMA_PATH,
            self.module.SNAPSHOT_SCHEMA_PATH,
        )
        for path in declared:
            with self.subTest(path=str(path)):
                self.assertTrue(Path(path).resolve().is_relative_to(LAYER6_ROOT))
                self.assertFalse(Path(path).resolve().is_relative_to(AGENTS_ROOT))


class AppendedScenarioCaseTests(unittest.TestCase):
    """FR-018, FR-019c, FR-024b, FR-025, FR-033b: what the appended cases pin.

    These read the committed corpus rather than building fixtures, because the
    property under test is what the *pinned* cases claim. Byte-identical replay is
    asserted elsewhere over every case; what is asserted here is that the appended
    cases cover the branches one case cannot cover alone — the two opposite override
    dispositions, the empty attempt array of a pre-walk rejection against the
    populated one of an in-walk loop, and the one policy that declares a helper.
    """

    def setUp(self) -> None:
        self.assertIsNotNone(claude_route_fallback, "claude_route_fallback is not importable")
        self.module = claude_route_fallback
        self.cases = {case["case_id"]: case for case in self.module.load_corpus()["cases"]}

    def pinned(self, case_id: str) -> dict[str, object]:
        self.assertIn(case_id, self.cases, f"{case_id} is not committed to the corpus")
        return self.cases[case_id]["expected_report"]

    def test_the_appended_cases_sit_at_the_tail_in_declaration_order(self) -> None:
        declared = list(self.cases)
        self.assertEqual(declared[: len(SLICE_ONE_CASE_IDS)], list(SLICE_ONE_CASE_IDS))
        self.assertEqual(
            declared[len(SLICE_ONE_CASE_IDS) : len(SLICE_ONE_CASE_IDS) + len(APPENDED_CASE_IDS)],
            list(APPENDED_CASE_IDS),
        )

    def test_the_three_pre_walk_cases_record_no_attempts_and_no_spend(self) -> None:
        for case_id in (
            "unqualified-adjacent-model",
            "generic-agent-substitution",
            "silent-inherit-materialization",
        ):
            with self.subTest(case=case_id):
                report = self.pinned(case_id)
                self.assertEqual(report["attempted_routes"], [])
                self.assertEqual(report["budgets"]["actual"], dict(UNSPENT_BUDGET))
                self.assertIs(report["release_claim_eligible"], False)
                self.assertEqual(report["outcome"], "no_safe_route")
                self.assertEqual(report["optional_helper"], dict(NO_HELPER_PATH))

    def test_the_loop_case_records_the_routes_attempted_before_the_revisit(self) -> None:
        report = self.pinned("fallback-loop")
        attempted = [entry["route_id"] for entry in report["attempted_routes"]]
        self.assertEqual(len(attempted), len(set(attempted)))
        self.assertNotEqual(attempted, [])
        loop = [entry for entry in report["diagnostics"] if entry["code"] == "fallback_loop"]
        self.assertEqual(len(loop), 1)
        self.assertIn(loop[0]["details"]["route_id"], attempted)

    def test_a_structural_rejection_case_takes_the_bounded_analyst_as_its_subject(self) -> None:
        subjects = {
            self.cases[case_id]["policy"]["agent"]["role_class"]
            for case_id in APPENDED_CASE_IDS[:4]
        }
        self.assertIn("bounded_analyst", subjects)

    def test_the_two_override_cases_pin_opposite_dispositions(self) -> None:
        honored = self.pinned("unqualified-override")["override"]
        skipped = self.pinned("override-skipped-by-allowlist")["override"]
        self.assertEqual(honored["disposition"], "honored")
        self.assertEqual(skipped["disposition"], "skipped_by_allowlist")
        self.assertIs(honored["qualified"], False)
        self.assertIn("tuple", honored)
        self.assertNotIn("tuple", skipped)
        for report in (self.pinned("unqualified-override"),
                       self.pinned("override-skipped-by-allowlist")):
            self.assertIs(report["release_claim_eligible"], False)
            self.assertIn("effective_dispatch_tuple", report)

    def test_the_two_override_cases_declare_the_same_variable(self) -> None:
        for case_id in ("unqualified-override", "override-skipped-by-allowlist"):
            with self.subTest(case=case_id):
                overrides = self.cases[case_id]["overrides"]
                self.assertEqual(set(overrides), {OVERRIDE_VARIABLE})
                self.assertEqual(self.pinned(case_id)["override"]["source"], OVERRIDE_VARIABLE)

    def test_the_override_allowlists_differ_on_the_requested_target(self) -> None:
        honored = self.cases["unqualified-override"]
        skipped = self.cases["override-skipped-by-allowlist"]
        for case in (honored, skipped):
            requested = case["overrides"][OVERRIDE_VARIABLE]
            target = case["snapshot"]["alias_bindings"].get(requested, requested)
            permitted = target in case["snapshot"]["available_models_allowlist"]
            expected = case["expected_report"]["override"]["disposition"] == "honored"
            with self.subTest(case=case["case_id"]):
                self.assertIs(permitted, expected)

    def test_the_helper_case_is_the_only_case_declaring_a_policy_helper(self) -> None:
        declaring = [
            case_id
            for case_id, case in self.cases.items()
            if "optional_helper" in case["policy"]
        ]
        self.assertEqual(declaring, ["helper-unavailable-continues"])

    def test_the_helper_case_pins_a_measurable_zero_and_a_resolved_required_agent(self) -> None:
        case = self.cases["helper-unavailable-continues"]
        report = case["expected_report"]
        self.assertEqual(report["optional_helper"], dict(NO_HELPER_PATH))
        self.assertEqual(report["outcome"], "resolved")
        helper = case["policy"]["optional_helper"]
        helper_ids = {helper["preferred_route"]["route_id"]} | {
            route["route_id"] for route in helper["fallback_routes"]
        }
        attempted = {entry["route_id"] for entry in report["attempted_routes"]}
        self.assertEqual(attempted & helper_ids, set())
        self.assertEqual(helper["agent"]["role_class"], "optional_helper")

    def test_the_helper_snapshot_offers_none_of_the_helpers_route_models(self) -> None:
        case = self.cases["helper-unavailable-continues"]
        helper = case["policy"]["optional_helper"]
        offered = set(case["snapshot"]["available_models"])
        for route in (helper["preferred_route"], *helper["fallback_routes"]):
            with self.subTest(route=route["route_id"]):
                self.assertNotIn(route["resolved_model"], offered)

    def test_the_exhaustion_case_declares_every_budget_at_one(self) -> None:
        declared = self.cases["budget-exhaustion-of-one"]["policy"]["budgets"]
        self.assertEqual(set(declared.values()), {1})
        self.assertEqual(self.pinned("budget-exhaustion-of-one")["budgets"]["declared"], declared)

    def test_the_exhaustion_case_pins_all_three_counts_at_their_declared_cap(self) -> None:
        budgets = self.pinned("budget-exhaustion-of-one")["budgets"]
        for member, count in budgets["actual"].items():
            with self.subTest(member=member):
                self.assertEqual(count, budgets["declared"][f"max_{member}"])

    def test_the_exhaustion_case_binds_the_retry_class_on_a_failing_preferred_route(self) -> None:
        """The roadmap states retry exhaustion as its own obligation, which a
        probe-only case would leave unproven — so the preferred route's
        exact-invocation outcome is a failure, the one permitted retry re-consults it,
        and no further retry may be taken."""
        case = self.cases["budget-exhaustion-of-one"]
        preferred = case["policy"]["preferred_route"]
        self.assertEqual(
            case["snapshot"]["exact_invocation_probe"][preferred["resolved_model"]], "failure"
        )
        report = case["expected_report"]
        self.assertEqual(report["budgets"]["actual"]["retries"], 1)
        self.assertEqual(report["budgets"]["declared"]["max_retries"], 1)
        rejected = [
            entry["code"]
            for entry in report["diagnostics"]
            if entry.get("details", {}).get("route_id") == preferred["route_id"]
        ]
        self.assertEqual(rejected, ["treatment_probe_failed"])

    def test_the_exhaustion_case_enumerates_all_three_classes_in_enum_order(self) -> None:
        report = self.pinned("budget-exhaustion-of-one")
        terminal = report["diagnostics"][-1]
        self.assertEqual(terminal["code"], "no_safe_route")
        self.assertEqual(
            terminal["details"]["exhausted_budget"],
            list(self.module.EXHAUSTED_BUDGET_CLASSES),
        )
        self.assertEqual(report["outcome"], "no_safe_route")

    def test_the_exhaustion_case_declares_a_route_the_cap_kept_the_walk_from_reaching(
        self,
    ) -> None:
        """The cap is what produced no_safe_route: a later declared route would have
        resolved, and the truncated walk never entered it."""
        case = self.cases["budget-exhaustion-of-one"]
        unreached = case["policy"]["fallback_routes"]
        self.assertNotEqual(unreached, [])
        attempted = {entry["route_id"] for entry in case["expected_report"]["attempted_routes"]}
        for route in unreached:
            with self.subTest(route=route["route_id"]):
                self.assertNotIn(route["route_id"], attempted)
                self.assertIn(route["resolved_model"], case["snapshot"]["available_models"])
                self.assertEqual(
                    case["snapshot"]["exact_invocation_probe"][route["resolved_model"]], "success"
                )

    def test_the_exhaustion_cases_declared_budgets_validate_against_the_policy_contract(
        self,
    ) -> None:
        contract = load_contract(CONTRACT_ROOT / "route-policy.schema.json")
        validate_instance(self.cases["budget-exhaustion-of-one"]["policy"], contract, path="policy")

    def test_the_report_only_case_rejects_every_attempted_route(self) -> None:
        report = self.pinned("no-safe-route-report-only")
        self.assertEqual(report["outcome"], "no_safe_route")
        self.assertEqual(report["unresolved_agent"], report["agent"])
        self.assertIs(report["release_claim_eligible"], False)
        self.assertNotEqual(report["attempted_routes"], [])
        self.assertEqual(
            {entry["disposition"] for entry in report["attempted_routes"]}, {"rejected"}
        )

    def test_the_report_only_case_joins_one_diagnostic_per_failed_check_to_its_route(self) -> None:
        case = self.cases["no-safe-route-report-only"]
        report = case["expected_report"]
        attempted = [entry["route_id"] for entry in report["attempted_routes"]]
        rejections = report["diagnostics"][:-1]
        self.assertEqual([entry["details"]["route_id"] for entry in rejections], attempted)
        self.assertEqual(len(set(entry["code"] for entry in rejections)), len(rejections))

    def test_the_report_only_case_closes_with_the_verbatim_rollback_and_no_repeat(self) -> None:
        report = self.pinned("no-safe-route-report-only")
        terminal = report["diagnostics"][-1]
        self.assertEqual(terminal["code"], "no_safe_route")
        self.assertEqual(terminal["severity"], "error")
        self.assertEqual(len(terminal["remediation"]["actions"]), 2)
        self.assertIn("Roll back to the previous plugin release.", terminal["remediation"]["actions"])
        for entry in report["diagnostics"][:-1]:
            with self.subTest(code=entry["code"]):
                self.assertNotIn(
                    "Roll back to the previous plugin release.", entry["remediation"]["actions"]
                )

    def test_the_report_only_case_ends_below_every_declared_cap(self) -> None:
        """Its at-cap set is empty, so the terminal entry carries no details at all —
        which is what keeps the field's presence meaning 'spent to the limit AND the
        walk failed' rather than merely 'the walk failed'."""
        report = self.pinned("no-safe-route-report-only")
        budgets = report["budgets"]
        for member, count in budgets["actual"].items():
            with self.subTest(member=member):
                self.assertLess(count, budgets["declared"][f"max_{member}"])
        self.assertNotIn("details", report["diagnostics"][-1])

    def test_the_corpus_closes_at_eighteen_cases_with_slice_one_at_the_head(self) -> None:
        declared = list(self.cases)
        self.assertEqual(len(declared), 18)
        self.assertEqual(len(SLICE_ONE_CASE_IDS), 9)
        self.assertEqual(len(APPENDED_CASE_IDS), 9)
        self.assertEqual(declared, [*SLICE_ONE_CASE_IDS, *APPENDED_CASE_IDS])

    def test_each_of_the_three_role_classes_is_a_subject_or_a_declared_helper(self) -> None:
        covered: set[str] = set()
        for case in self.cases.values():
            covered.add(case["policy"]["agent"]["role_class"])
            helper = case["policy"].get("optional_helper")
            if helper is not None:
                covered.add(helper["agent"]["role_class"])
        self.assertEqual(covered, set(SYNTHETIC_ROLE_CLASSES))


# --------------------------------------------------------------------------- #
# SC-001: every mandated scenario is represented, with zero unrepresented        #
# --------------------------------------------------------------------------- #
# Each predicate reads the CONTENT of a case — the codes it emits, the sub-reason
# it carries, the disposition it pins — rather than its ``case_id``, so the
# coverage claim is about substance and survives a rename. Exhaustion is named by
# its terminating class rather than as generic budget exhaustion, because the
# roadmap states retry exhaustion as its own proof obligation.


def emitted_codes(case: dict[str, object]) -> set[str]:
    return {str(entry["code"]) for entry in case["expected_report"]["diagnostics"]}


def emits(code: str):
    return lambda case: code in emitted_codes(case)


def sub_reasons(case: dict[str, object]) -> set[str]:
    return {
        str(entry["details"]["sub_reason"])
        for entry in case["expected_report"]["diagnostics"]
        if "sub_reason" in entry.get("details", {})
    }


def carries_sub_reason(name: str):
    return lambda case: name in sub_reasons(case)


def covers_the_fable_family(case: dict[str, object]) -> bool:
    """The roadmap's own fable scenario, subordinated to preferred-model-absent: the
    pinned model of the real family alias is no longer offered."""
    return any(
        entry["details"].get("sub_reason") == "model_absent"
        and entry["details"].get("alias") == "fable"
        for entry in case["expected_report"]["diagnostics"]
        if "details" in entry
    )


def resolved_through_a_successful_probe(case: dict[str, object]) -> bool:
    tuple_ = case["expected_report"].get("effective_dispatch_tuple")
    if case["expected_report"]["outcome"] != "resolved" or tuple_ is None:
        return False
    probed = case["snapshot"]["exact_invocation_probe"].get(tuple_["resolved_model"])
    return probed == "success"


def override_skipped_by_the_allowlist(case: dict[str, object]) -> bool:
    override = case["expected_report"].get("override")
    return override is not None and override["disposition"] == "skipped_by_allowlist"


def helper_declared_but_not_consulted(case: dict[str, object]) -> bool:
    return "optional_helper" in case["policy"] and (
        case["expected_report"]["optional_helper"]["consulted"] is False
    )


def exhausted_class(name: str):
    def predicate(case: dict[str, object]) -> bool:
        return any(
            name in entry.get("details", {}).get("exhausted_budget", [])
            for entry in case["expected_report"]["diagnostics"]
        )

    return predicate


def ends_with_no_safe_route(case: dict[str, object]) -> bool:
    return case["expected_report"]["outcome"] == "no_safe_route"


MANDATED_SCENARIOS: tuple[tuple[str, object], ...] = (
    ("preferred model absent, including the fable case", covers_the_fable_family),
    ("alias unresolved", carries_sub_reason("alias_unresolved")),
    ("effort unsupported", emits("effort_unsupported")),
    ("probe unavailable", emits("capability_probe_unavailable")),
    ("exact-invocation probe success", resolved_through_a_successful_probe),
    ("exact-invocation probe failure", emits("treatment_probe_failed")),
    ("alias re-pointing", carries_sub_reason("alias_repointed")),
    ("platform route change", carries_sub_reason("platform_route_changed")),
    ("unqualified override", emits("unqualified_override")),
    ("override skipped by the organization allowlist", override_skipped_by_the_allowlist),
    ("fallback loop", emits("fallback_loop")),
    ("unqualified adjacent model", emits("unqualified_adjacent_model")),
    ("generic-agent substitution", emits("generic_agent_substitution")),
    ("silent inherit materialization", emits("silent_inherit_materialization")),
    ("helper unavailable", helper_declared_but_not_consulted),
    ("retry exhaustion", exhausted_class("retries")),
    ("no safe route", ends_with_no_safe_route),
)


class MandatedScenarioCoverageTests(unittest.TestCase):
    """SC-001: the roadmap's scenario list against the committed corpus.

    The count of unrepresented scenarios is the measurable outcome, so it is asserted
    as an empty list rather than as a total — a failure then names which scenarios
    lost their case rather than reporting that some number moved.
    """

    def setUp(self) -> None:
        self.assertIsNotNone(claude_route_fallback, "claude_route_fallback is not importable")
        self.module = claude_route_fallback
        self.cases = self.module.load_corpus()["cases"]

    def matching(self, predicate: object) -> list[str]:
        return [case["case_id"] for case in self.cases if predicate(case)]

    def test_every_mandated_scenario_is_represented_with_zero_unrepresented(self) -> None:
        unrepresented = [name for name, predicate in MANDATED_SCENARIOS if not self.matching(predicate)]
        self.assertEqual(unrepresented, [])

    def test_the_scenario_table_names_each_mandated_scenario_once(self) -> None:
        names = [name for name, _ in MANDATED_SCENARIOS]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(names), 17)

    def test_no_scenario_predicate_is_satisfied_by_every_case(self) -> None:
        """A predicate matching all eighteen would report coverage without
        discriminating, which is the one way this table could pass while proving
        nothing."""
        for name, predicate in MANDATED_SCENARIOS:
            with self.subTest(scenario=name):
                matched = self.matching(predicate)
                self.assertNotEqual(matched, [])
                self.assertLess(len(matched), len(self.cases))

    def test_the_corpus_the_coverage_claim_is_taken_over_holds_eighteen_cases(self) -> None:
        self.assertEqual(len(self.cases), 18)


def _declared(policy: dict[str, object]) -> tuple[dict[str, object], ...]:
    """The policy's declared routes, deduplicated by ``route_id`` in declared order.

    Deduplicated because a looping chain declares the same route twice and the
    snapshot builder would otherwise carry a repeated model.
    """
    seen: dict[str, dict[str, object]] = {}
    for route in (policy["preferred_route"], *policy["fallback_routes"]):
        seen.setdefault(str(route["route_id"]), route)
    return tuple(seen.values())


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
    StructuralPreWalkTests,
    FallbackLoopTests,
    SubagentModelOverrideTests,
    OptionalHelperPathTests,
    BudgetCapTests,
    ExhaustedBudgetEnumerationTests,
    NoSafeRouteRecoveryTests,
    AppendedScenarioCaseTests,
    MandatedScenarioCoverageTests,
)


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for case in TEST_CASES:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    return suite


if __name__ == "__main__":
    raise SystemExit(run_counted(build_suite(), label="test-route-fallback-simulation"))
