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
)


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for case in TEST_CASES:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    return suite


if __name__ == "__main__":
    raise SystemExit(run_counted(build_suite(), label="test-route-fallback-simulation"))
