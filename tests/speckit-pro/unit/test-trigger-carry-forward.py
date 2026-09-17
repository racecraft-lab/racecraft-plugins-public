#!/usr/bin/env python3
"""Threat-family tests for immutable trigger case carry-forward; no providers."""
from __future__ import annotations

import copy
from dataclasses import replace
import hashlib
import importlib.machinery
import json
import os
from pathlib import Path
import runpy
import sqlite3
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
import trigger_campaign_execution as execution
import trigger_carry_forward as carry
import trigger_comparison as comparison
from test_result import run_counted


def reference(path: Path) -> dict:
    return {"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def case_tree_descriptor(case_root: Path, arm: str, case_id: str) -> dict:
    rows = [{"path": path.relative_to(case_root).as_posix(),
             "bytes": len(path.read_bytes()),
             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in sorted(case_root.rglob("*")) if path.is_file()]
    return {"arm": arm, "case_id": case_id, "root": str(case_root),
            "file_count": len(rows),
            "files_manifest_sha256": hashlib.sha256(json.dumps(
                rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}


def ledger_fixture(status: str = "complete") -> tuple[dict, dict]:
    case_ids = [f"case-{number:03d}" for number in range(137)]
    partial = carry.PARTIAL_CASE_ID
    manifest = {"roster": [{"case_id": case_id} for case_id in [*case_ids, partial,
                *(f"fresh-{number:03d}" for number in range(79))]]}
    launches = [{"arm": "serial:baseline", "case_id": case_id, "trial_number": trial,
                 "status": status, "reserved_at": 1.0, "completed_at": 2.0}
                for case_id in case_ids for trial in (1, 2, 3)]
    launches += [{"arm": "serial:baseline", "case_id": partial, "trial_number": trial,
                  "status": "invalid", "reserved_at": 1.0, "completed_at": 2.0}
                 for trial in (1, 2, 3)]
    snapshot = {"schema_version": "trigger-campaign-ledger/v1", "launch_budget": 1302,
                "reserved_launches": 414, "unknown_launches": 0, "launches": launches}
    return manifest, snapshot


def plan_fixture(case_ids=("carried",), fresh_ids=("fresh",)):
    carried_trials = frozenset(("baseline", case_id, trial) for case_id in case_ids for trial in (1, 2, 3))
    fresh = frozenset({*(("baseline", case_id) for case_id in fresh_ids),
                       *(("candidate", case_id) for case_id in (*case_ids, *fresh_ids))})
    fresh_trials = frozenset((arm, case_id, trial) for arm, case_id in fresh for trial in (1, 2, 3))
    return SimpleNamespace(carried_case_ids=tuple(case_ids), fresh_case_ids=tuple(fresh_ids),
                           carried_trials=carried_trials, fresh_trials=fresh_trials,
                           component_sha256="a" * 64)


def terminal_history_fixture(root: Path):
    campaign_test = runpy.run_path(str(ROOT / "unit/test-trigger-campaign.py"))
    output = (root / "history").resolve()
    review_root = (root / "history-review").resolve()
    output.mkdir()
    review_root.mkdir()
    manifest = campaign_test["full_manifest"](output)
    inventory_source = ROOT / "layer2-trigger/case-inventory.json"
    manifest["inventory_sha256"] = hashlib.sha256(inventory_source.read_bytes()).hexdigest()
    approval = campaign_test["standing_approval"](manifest)
    (output / "manifest.json").write_text(json.dumps(manifest))
    (output / "approval.json").write_text(json.dumps(approval))
    (output / "inventory.json").write_bytes(inventory_source.read_bytes())
    authorization = {"manifest_sha256": comparison.json_digest(manifest),
                     "approval_sha256": comparison.json_digest(approval), "launch_budget": 1302}
    connection = sqlite3.connect(output / "ledger.sqlite3")
    connection.execute("CREATE TABLE authorization (id INTEGER PRIMARY KEY, binding TEXT NOT NULL)")
    connection.execute("CREATE TABLE launches (arm TEXT, case_id TEXT, trial INTEGER, status TEXT, reserved_at REAL, completed_at REAL)")
    connection.execute("INSERT INTO authorization VALUES (1, ?)",
                       (json.dumps(authorization, sort_keys=True),))
    case_id = manifest["roster"][0]["case_id"]
    connection.executemany("INSERT INTO launches VALUES (?, ?, ?, 'invalid', 1.0, 2.0)",
                           [("serial:baseline", case_id, trial) for trial in (1, 2, 3)])
    connection.commit()
    connection.close()
    _authorization, snapshot = __import__("trigger_campaign").read_ledger(output / "ledger.sqlite3")
    (output / "terminal-ledger.json").write_text(json.dumps(snapshot))
    case_root = output / "serial" / "baseline" / case_id
    evidence_root = case_root / "evidence"
    evidence_root.mkdir(parents=True)
    runner = {"pid": 41001, "command": ["/trusted/python", "runner.py"],
              "started_at": 1.0}
    execution_record = {"runner_exit_code": 1, "finished_at": 2.0}
    workspace = str((root / "removed-workspace").resolve())
    (case_root / "launch.json").write_text(json.dumps(runner))
    (case_root / "execution.json").write_text(json.dumps(execution_record))
    (evidence_root / "arm-cleanup.json").write_text(json.dumps({
        "schema_version": "trigger-arm-cleanup/v1", "workspace": workspace,
        "workspace_removed": True, "runner_exit_code": 1, "cleanup_error": None,
    }))
    (evidence_root / "replay-context.json").write_text(json.dumps({
        "host": "claude", "plugin_root": workspace,
    }))
    groups = []
    for trial in (1, 2, 3):
        pgid = 42000 + trial
        (evidence_root / f"{trial}.trial.json").write_text(json.dumps({
            "case_id": case_id, "trial_number": trial, "child_pid": pgid,
            "child_pgid": pgid, "cleanup_verified": True, "cleanup_error": None,
            "unexpected_descendants": False,
            "cleanup_observations": [{"pgid": pgid, "errno": 3}],
        }))
        groups.append({"pgid": pgid, "completed_at": 2.0})
    lease = root / "lease.lock"
    lease.write_text(json.dumps({"schema_version": "trigger-global-lease/v1", "state": "idle",
                                 "campaign": str(output)}))
    core = {
        "generation_id": "charge-only", "output_root": str(output),
        "review_root": str(review_root),
        "manifest": reference(output / "manifest.json"),
        "approval": reference(output / "approval.json"),
        "ledger": reference(output / "ledger.sqlite3"),
        "terminal_ledger": reference(output / "terminal-ledger.json"),
        "inventory": reference(output / "inventory.json"), "nested_carry_forward": None,
        "evidence": [],
        "ownership": {"runners": [runner], "groups": groups, "workspaces": [workspace],
                      "lease_path": str(lease.resolve()),
                      "cases": [case_tree_descriptor(case_root, "baseline", case_id)]},
    }
    review = {"reviewer": "independent-reviewer", "review_id": "charge-only-review",
              "reviewed_at": "2026-09-15T00:00:00.000Z", "source_commit": "a" * 40,
              "source_tree_sha256": "b" * 64, "segment_sha256": comparison.json_digest(core)}
    logical = copy.deepcopy(manifest)
    logical["output_directory"] = str((root / "logical").resolve())
    return {**core, "review": review}, logical


def multi_generation_fixture(root: Path):
    campaign_test = runpy.run_path(str(ROOT / "unit/test-trigger-campaign.py"))
    logical = campaign_test["full_manifest"]((root / "logical").resolve())
    request = copy.deepcopy(logical)
    request["arms"] = ["candidate"]
    request["output_directory"] = str((root / "fresh").resolve())
    logical["output_directory"] = request["output_directory"]
    case_ids = tuple(row["case_id"] for row in logical["roster"])
    groups = (case_ids[:137], (), case_ids[137:])
    charges = (414, 3, 243)
    invalids = (3, 3, 3)
    segments = []
    sources = []
    histories = []
    for number, (name, ids, charged, invalid) in enumerate(zip(
            ("original", "failed-c2", "recovery"), groups, charges, invalids, strict=True)):
        root_path = (root / name).resolve()
        review_path = (root / f"{name}-review").resolve()
        trials = frozenset(("baseline", case_id, trial) for case_id in ids for trial in (1, 2, 3))
        complete = frozenset(("baseline", case_id) for case_id in ids)
        bad = frozenset(("candidate", case_ids[0], trial) for trial in range(1, invalid + 1))
        segment = carry.HistoricalSegmentPlan(
            name, root_path, review_path, logical, {}, {}, f"{number + 1}" * 64,
            complete, trials,
            bad, charged, invalid, 0, tuple(), None,
            (Path("/tmp") / f"speckit-trigger-native-{os.getuid()}.lock").resolve(),
        )
        segments.append(segment)
        histories.append({"generation_id": name})
        if ids:
            index = {"summary": {case_id: {"target_hits": 1, "pass": True} for case_id in ids}}
            sources.append(carry.HistoricalEvidenceSource(
                name, root_path, "baseline", logical, index, ids,
                {"claude": frozenset({"claude-sonnet-test"}),
                 "codex": frozenset({"gpt-5.6-sol"})},
            ))
    current = logical["identities"]["observer"]
    component = {
        "schema_version": carry.MULTI_GENERATION_SCHEMA_VERSION,
        "logical_manifest": logical, "histories": histories,
        "observer_replays": [
            {"generation_id": source.generation_id, "arm": source.arm,
             "observer_sha256": current, "current_observer_sha256": current,
             "replay": None} for source in sources
        ],
        "accounting": {"logical_full_trials": 1302, "carried_trials": 651,
                       "fresh_launch_ceiling": 651, "historical_charged_launches": 660,
                       "invalid_launches": 9, "unknown_launches": 0,
                       "maximum_total_charged_attempts": 1311},
        "policy": {"automatic_retries": 0, "refunds": False, "regrades": False,
                   "resets": False, "new_generation_invalid_reruns": True},
    }
    return request, component, segments, sources


class MultiGenerationCarryForwardTests(unittest.TestCase):
    def test_v2_charge_only_history_rejects_omitted_ownership_artifacts(self):
        with tempfile.TemporaryDirectory() as temp:
            segment, logical = terminal_history_fixture(Path(temp))
            for omitted in (("cases",), ("runners", "groups", "workspaces")):
                with self.subTest(omitted=omitted):
                    changed = copy.deepcopy(segment)
                    for name in omitted:
                        changed["ownership"][name] = []
                    core = {key: value for key, value in changed.items() if key != "review"}
                    changed["review"]["segment_sha256"] = comparison.json_digest(core)
                    with mock.patch("trigger_campaign.validate_approval"), \
                         mock.patch.object(carry, "_current_process_snapshot", return_value=()), \
                         self.assertRaisesRegex(ValueError, "ownership"):
                        carry._validate_historical_segment(
                            changed, logical, Path(temp) / "fresh")

    def test_v2_charge_only_history_rejects_a_live_replay_workspace_hidden_by_cleanup(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            segment, logical = terminal_history_fixture(root)
            live = (root / "live-staging-workspace").resolve()
            live.mkdir()
            case = segment["ownership"]["cases"][0]
            case_root = Path(case["root"])
            context_path = case_root / "evidence/replay-context.json"
            context_path.write_text(json.dumps({"host": "claude", "plugin_root": str(live)}))
            segment["ownership"]["cases"] = [case_tree_descriptor(
                case_root, case["arm"], case["case_id"])]
            core = {key: value for key, value in segment.items() if key != "review"}
            segment["review"]["segment_sha256"] = comparison.json_digest(core)
            with mock.patch("trigger_campaign.validate_approval"), \
                 mock.patch.object(carry, "_current_process_snapshot", return_value=()), \
                 self.assertRaisesRegex(ValueError, "workspace"):
                carry._validate_historical_segment(
                    segment, logical, root / "fresh")

    def test_v2_exact_651_660_651_1311_union_uses_disjoint_valid_coverage(self):
        with tempfile.TemporaryDirectory() as temp:
            request, component, segments, sources = multi_generation_fixture(Path(temp))
            with mock.patch.object(carry, "_validate_historical_segment", side_effect=segments), \
                 mock.patch.object(carry, "_validate_historical_evidence", side_effect=[(sources[0],), (), (sources[1],)]), \
                 mock.patch.object(comparison, "measurement_snapshot", return_value={}), \
                 mock.patch.object(comparison, "snapshot_identities",
                                   return_value=component["logical_manifest"]["identities"]):
                plan = carry.validate_multi_generation_carry_forward(
                    component, request, comparison.json_digest(request))
            self.assertEqual(len(plan.carried_trials), 651)
            self.assertEqual(len(plan.fresh_trials), 651)
            self.assertEqual(plan.historical_charged_launches, 660)
            self.assertEqual(plan.maximum_total_charged_attempts, 1311)
            self.assertEqual({arm for arm, _case_id in plan.fresh}, {"candidate"})
            baseline = carry.multi_source_index(plan, "baseline", None)
            candidate = carry.multi_source_index(plan, "candidate", {"fresh": "candidate"})
            self.assertEqual(baseline["schema_version"], carry.MULTI_SOURCE_INDEX_SCHEMA_VERSION)
            self.assertNotIn("fresh", {source["kind"] for source in baseline["sources"]})
            self.assertEqual(carry.multi_source_union(baseline, plan, "baseline")[1], None)
            self.assertEqual(carry.multi_source_union(candidate, plan, "candidate")[1]["kind"],
                             "fresh")

            duplicate = copy.deepcopy(component)
            overlapping = copy.deepcopy(segments[2])
            overlapping = carry.HistoricalSegmentPlan(
                overlapping.generation_id, overlapping.root, overlapping.review_root,
                overlapping.manifest,
                overlapping.approval, overlapping.snapshot, overlapping.ledger_sha256,
                frozenset({next(iter(segments[0].complete_pairs))}),
                frozenset({next(iter(segments[0].complete_trials))}),
                overlapping.invalid_identities, overlapping.charged_trials,
                overlapping.invalid_trials, overlapping.unknown_trials,
                overlapping.evidence, overlapping.nested_carry_forward,
                overlapping.lease_path)
            with mock.patch.object(carry, "_validate_historical_segment",
                                   side_effect=[segments[0], segments[1], overlapping]), \
                 mock.patch.object(carry, "_validate_historical_evidence",
                                   side_effect=[(sources[0],), (), (sources[1],)]), \
                 mock.patch.object(comparison, "measurement_snapshot", return_value={}), \
                 mock.patch.object(comparison, "snapshot_identities", return_value=component["logical_manifest"]["identities"]), \
                 self.assertRaisesRegex(ValueError, "overlap"):
                carry.validate_multi_generation_carry_forward(
                    duplicate, request, comparison.json_digest(request))

    def test_v2_rejects_fresh_output_nested_with_either_historical_direction(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            for fresh, historical in (
                    (root / "historical-parent" / "fresh", root / "historical-parent"),
                    (root / "fresh-parent" / "campaign",
                     root / "fresh-parent" / "campaign" / "history")):
                with self.subTest(fresh=fresh, historical=historical):
                    fresh.parent.mkdir(parents=True, exist_ok=True)
                    request, component, segments, _sources = multi_generation_fixture(root)
                    request["output_directory"] = str(fresh)
                    component["logical_manifest"]["output_directory"] = str(fresh)
                    nested = [replace(segments[0], root=historical), *segments[1:]]
                    with mock.patch.object(carry, "_validate_historical_segment",
                                           side_effect=nested), \
                         mock.patch.object(comparison, "measurement_snapshot", return_value={}), \
                         mock.patch.object(comparison, "snapshot_identities",
                                           return_value=component["logical_manifest"]["identities"]), \
                         self.assertRaisesRegex(ValueError, "non-overlapping"):
                        carry.validate_multi_generation_carry_forward(
                            component, request, comparison.json_digest(request))
                    self.assertFalse(fresh.exists())

    def test_v2_next_generation_can_request_only_remaining_candidate_roster(self):
        with tempfile.TemporaryDirectory() as temp:
            request, component, segments, sources = multi_generation_fixture(Path(temp))
            carried_candidate = component["logical_manifest"]["roster"][0]["case_id"]
            recovery = segments[2]
            pair = ("candidate", carried_candidate)
            trials = frozenset(("candidate", carried_candidate, trial) for trial in (1, 2, 3))
            recovery = carry.HistoricalSegmentPlan(
                recovery.generation_id, recovery.root, recovery.review_root,
                recovery.manifest, recovery.approval,
                recovery.snapshot, recovery.ledger_sha256,
                recovery.complete_pairs | {pair}, recovery.complete_trials | trials,
                recovery.invalid_identities, recovery.charged_trials + 3,
                recovery.invalid_trials, recovery.unknown_trials,
                recovery.evidence, recovery.nested_carry_forward,
                recovery.lease_path)
            candidate_source = carry.HistoricalEvidenceSource(
                recovery.generation_id, recovery.root, "candidate", recovery.manifest,
                {"summary": {carried_candidate: {"target_hits": 2, "pass": True}}},
                (carried_candidate,), sources[1].models)
            current = component["logical_manifest"]["identities"]["observer"]
            component["observer_replays"].append(
                {"generation_id": candidate_source.generation_id,
                 "arm": candidate_source.arm, "observer_sha256": current,
                 "current_observer_sha256": current, "replay": None})
            request["roster"] = request["roster"][1:]
            request["corpus_sha256"] = comparison.json_digest(request["roster"])
            component["accounting"].update(
                carried_trials=654, fresh_launch_ceiling=648,
                historical_charged_launches=663,
                maximum_total_charged_attempts=1311)
            with mock.patch.object(carry, "_validate_historical_segment",
                                   side_effect=[segments[0], segments[1], recovery]), \
                 mock.patch.object(carry, "_validate_historical_evidence",
                                   side_effect=[(sources[0],), (), (sources[1], candidate_source)]), \
                 mock.patch.object(comparison, "measurement_snapshot", return_value={}), \
                 mock.patch.object(comparison, "snapshot_identities",
                                   return_value=component["logical_manifest"]["identities"]):
                plan = carry.validate_multi_generation_carry_forward(
                    component, request, comparison.json_digest(request))
            self.assertEqual(len(plan.fresh_trials), 648)
            self.assertNotIn(pair, plan.fresh)

    def test_v2_rejects_missing_union_duplicate_roots_and_unreviewed_nested_lineage(self):
        with tempfile.TemporaryDirectory() as temp:
            request, component, segments, sources = multi_generation_fixture(Path(temp))
            identities = component["logical_manifest"]["identities"]

            missing = copy.deepcopy(request)
            missing["roster"] = missing["roster"][:-1]
            missing["corpus_sha256"] = comparison.json_digest(missing["roster"])
            with mock.patch.object(carry, "_validate_historical_segment",
                                   side_effect=segments), \
                 mock.patch.object(carry, "_validate_historical_evidence",
                                   side_effect=[(sources[0],), (), (sources[1],)]), \
                 mock.patch.object(comparison, "measurement_snapshot", return_value={}), \
                 mock.patch.object(comparison, "snapshot_identities", return_value=identities), \
                 self.assertRaisesRegex(ValueError, "exact disjoint logical complement"):
                carry.validate_multi_generation_carry_forward(
                    component, missing, comparison.json_digest(missing))

            duplicate = [segments[0], segments[0], segments[2]]
            with mock.patch.object(carry, "_validate_historical_segment",
                                   side_effect=duplicate), \
                 mock.patch.object(comparison, "measurement_snapshot", return_value={}), \
                 mock.patch.object(comparison, "snapshot_identities", return_value=identities), \
                 self.assertRaisesRegex(ValueError, "duplicated"):
                carry.validate_multi_generation_carry_forward(
                    component, request, comparison.json_digest(request))

            unreviewed = carry.HistoricalSegmentPlan(
                segments[2].generation_id, segments[2].root, segments[2].review_root,
                segments[2].manifest, segments[2].approval, segments[2].snapshot,
                segments[2].ledger_sha256, segments[2].complete_pairs,
                segments[2].complete_trials, segments[2].invalid_identities,
                segments[2].charged_trials, segments[2].invalid_trials,
                segments[2].unknown_trials, segments[2].evidence,
                {"schema_version": carry.MULTI_GENERATION_SCHEMA_VERSION,
                 "histories": []}, segments[2].lease_path)
            with mock.patch.object(carry, "_validate_historical_segment",
                                   side_effect=[segments[0], segments[1], unreviewed]), \
                 mock.patch.object(comparison, "measurement_snapshot", return_value={}), \
                 mock.patch.object(comparison, "snapshot_identities", return_value=identities), \
                 self.assertRaisesRegex(ValueError, "exact reviewed subset"):
                carry.validate_multi_generation_carry_forward(
                    component, request, comparison.json_digest(request))

            legacy_nested = {"schema_version": carry.SCHEMA_VERSION}
            legacy_child = carry.HistoricalSegmentPlan(
                segments[2].generation_id, segments[2].root, segments[2].review_root,
                segments[2].manifest, segments[2].approval, segments[2].snapshot,
                segments[2].ledger_sha256, segments[2].complete_pairs,
                segments[2].complete_trials, segments[2].invalid_identities,
                segments[2].charged_trials, segments[2].invalid_trials,
                segments[2].unknown_trials, segments[2].evidence, legacy_nested,
                segments[2].lease_path)
            missing_anchor = SimpleNamespace(
                source_root=(Path(temp) / "omitted-generation").resolve(),
                source_manifest=component["logical_manifest"])
            with mock.patch.object(carry, "_validate_historical_segment",
                                   side_effect=[segments[0], segments[1], legacy_child]), \
                 mock.patch.object(carry, "validate_carry_forward",
                                   return_value=missing_anchor), \
                 mock.patch.object(comparison, "measurement_snapshot", return_value={}), \
                 mock.patch.object(comparison, "snapshot_identities", return_value=identities), \
                 self.assertRaisesRegex(ValueError, "omitted"):
                carry.validate_multi_generation_carry_forward(
                    component, request, comparison.json_digest(request))

    def test_v2_reviewed_partial_index_is_bound_to_distinct_review_root(self):
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            output = (parent / "history").resolve()
            review = (parent / "review").resolve()
            output.mkdir()
            review.mkdir()
            logical = {"arms": ["baseline", "candidate"],
                       "roster": [{"case_id": "case-b"}, {"case_id": "case-a"}],
                       "identities": {"observer": "a" * 64}}
            index_path = review / "partial-index.json"
            index_path.write_text(json.dumps({"schema_version": "trigger-evidence-index/v1",
                                              "summary": {"case-b": {"target_hits": 2,
                                                                        "pass": True}}}))
            nested_path = output / "trial-record.json"
            nested_path.write_text('{"retained":true}')
            nested_reference = reference(nested_path)
            descriptor = {"kind": "reviewed-partial", "arm": "baseline",
                          "index": reference(index_path), "case_ids": ["case-b"]}
            segment = SimpleNamespace(
                generation_id="interrupted", root=output, review_root=review,
                manifest=logical, evidence=(descriptor,), nested_carry_forward=None,
                complete_pairs=frozenset({("baseline", "case-b")}),
            )
            def secure_replay(_manifest, source_root, _index, _arm, _cases, options):
                self.assertEqual(options["artifact_reader"](source_root, nested_reference),
                                 b'{"retained":true}')
                return {}, True
            with mock.patch.object(comparison, "validate_experiment",
                                   return_value={"case-b": {}}), \
                 mock.patch.object(comparison, "_read_arm", side_effect=secure_replay), \
                 mock.patch.object(comparison, "_resolved_models",
                                   return_value={"claude": {"claude-sonnet-test"}}):
                sources = carry._validate_historical_evidence(segment, logical, {})
            self.assertEqual(sources[0].root, output)
            self.assertEqual(sources[0].case_ids, ("case-b",))

            nested_path.write_text('{"forged":true}')
            with mock.patch.object(comparison, "validate_experiment",
                                   return_value={"case-b": {}}), \
                 mock.patch.object(comparison, "_read_arm", side_effect=secure_replay), \
                 self.assertRaisesRegex(ValueError, "digest changed"):
                carry._validate_historical_evidence(segment, logical, {})
            nested_path.write_text('{"retained":true}')

            retained = index_path.read_text()
            def replace_reviewed_index(*_args):
                index_path.write_text(retained + " ")
                return {}, True
            with mock.patch.object(comparison, "validate_experiment",
                                   return_value={"case-b": {}}), \
                 mock.patch.object(comparison, "_read_arm", side_effect=replace_reviewed_index), \
                 mock.patch.object(comparison, "_resolved_models", return_value={}), \
                 self.assertRaisesRegex(ValueError, "digest changed"):
                carry._validate_historical_evidence(segment, logical, {})

    def test_v2_terminal_history_reads_exact_sqlite_bytes_without_carrying_invalid_pair(self):
        with tempfile.TemporaryDirectory() as temp:
            segment, logical = terminal_history_fixture(Path(temp))
            with mock.patch.object(carry, "_current_process_snapshot", return_value=()):
                result = carry._validate_historical_segment(segment, logical, Path(temp) / "fresh")
            self.assertEqual(result.charged_trials, 3)
            self.assertEqual(result.invalid_trials, 3)
            self.assertEqual(result.complete_trials, frozenset())
            terminal = Path(segment["output_root"]) / segment["terminal_ledger"]["path"]
            retained = terminal.read_bytes()
            terminal.write_text(terminal.read_text() + " ")
            with mock.patch.object(carry, "_current_process_snapshot", return_value=()), \
                 self.assertRaisesRegex(ValueError, "digest"):
                carry._validate_historical_segment(segment, logical, Path(temp) / "fresh")
            terminal.write_bytes(retained)
            lease = Path(segment["ownership"]["lease_path"])
            lease.write_text(json.dumps({"schema_version": "trigger-global-lease/v1",
                                         "state": "active", "campaign": segment["output_root"]}))
            with mock.patch.object(carry, "_current_process_snapshot", return_value=()), \
                 self.assertRaisesRegex(ValueError, "not terminal and idle"):
                carry._validate_historical_segment(segment, logical, Path(temp) / "fresh")

    def test_v2_later_v5_history_accepts_only_its_reviewed_request_subset(self):
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            segment, logical = terminal_history_fixture(parent)
            output = Path(segment["output_root"])
            request = copy.deepcopy(logical)
            request["arms"] = ["candidate"]
            request["roster"] = request["roster"][1:]
            request["corpus_sha256"] = comparison.json_digest(request["roster"])
            request["output_directory"] = str(output)
            nested = {"schema_version": carry.MULTI_GENERATION_SCHEMA_VERSION}
            approval = {"schema_version": "trigger-campaign-approval/v5", "launch_budget": 3}
            (output / "manifest.json").write_text(json.dumps(request))
            (output / "approval.json").write_text(json.dumps(approval))
            authorization = {
                "manifest_sha256": comparison.json_digest(request),
                "approval_sha256": comparison.json_digest(approval),
                "launch_budget": 3,
                "carry_forward_sha256": comparison.json_digest(nested),
            }
            connection = sqlite3.connect(output / "ledger.sqlite3")
            connection.execute("DELETE FROM authorization")
            connection.execute("DELETE FROM launches")
            connection.execute("INSERT INTO authorization VALUES (1, ?)",
                               (json.dumps(authorization, sort_keys=True),))
            case_id = request["roster"][0]["case_id"]
            connection.executemany(
                "INSERT INTO launches VALUES ('serial:candidate', ?, ?, 'invalid', 1.0, 2.0)",
                [(case_id, trial) for trial in (1, 2, 3)])
            connection.commit()
            connection.close()
            old_case_root = output / "serial" / "baseline" / logical["roster"][0]["case_id"]
            case_root = output / "serial" / "candidate" / case_id
            case_root.parent.mkdir(parents=True)
            old_case_root.rename(case_root)
            for trial_path in sorted((case_root / "evidence").glob("*.trial.json")):
                trial = json.loads(trial_path.read_text())
                trial["case_id"] = case_id
                trial_path.write_text(json.dumps(trial))
            segment["ownership"]["cases"] = [
                case_tree_descriptor(case_root, "candidate", case_id)]
            _authorization, snapshot = __import__("trigger_campaign").read_ledger(
                output / "ledger.sqlite3")
            (output / "terminal-ledger.json").write_text(json.dumps(snapshot))
            segment.update(
                manifest=reference(output / "manifest.json"),
                approval=reference(output / "approval.json"),
                ledger=reference(output / "ledger.sqlite3"),
                terminal_ledger=reference(output / "terminal-ledger.json"),
                nested_carry_forward=nested,
            )
            core = {key: value for key, value in segment.items() if key != "review"}
            segment["review"]["segment_sha256"] = comparison.json_digest(core)
            with mock.patch("trigger_campaign.validate_approval"), \
                 mock.patch.object(carry, "_current_process_snapshot", return_value=()):
                result = carry._validate_historical_segment(
                    segment, logical, parent / "fresh")
            self.assertEqual(tuple(result.manifest["roster"]), tuple(request["roster"]))
            self.assertEqual(result.invalid_trials, 3)

    def test_v2_observer_replay_binds_each_source_to_final_and_rejects_third_observer(self):
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            output = (parent / "history").resolve()
            review = (parent / "review").resolve()
            output.mkdir()
            review.mkdir()
            comparison_test = runpy.run_path(str(ROOT / "unit/test-trigger-comparison.py"))
            logical, indexes = comparison_test["evidence_fixture"](output)
            old_observer = comparison.json_digest({"lib/old.py": "a" * 64})
            final_observer = logical["identities"]["observer"]
            case_id = logical["roster"][0]["case_id"]
            source_manifest = copy.deepcopy(logical)
            source_manifest["identities"]["observer"] = old_observer
            source_index = copy.deepcopy(indexes[0])
            source_index["identities"] = copy.deepcopy(source_manifest["identities"])
            source_index["experiment_sha256"] = comparison.json_digest(source_manifest)
            replay_trials = []
            for indexed in source_index["trials"]:
                record = json.loads(comparison.read_artifact(output, indexed["record"]))
                projection = carry._projection(record)
                replay_trials.append({
                    "arm": "baseline", "case_id": case_id,
                    "trial_number": indexed["trial_number"],
                    "record_sha256": indexed["record"]["sha256"],
                    "stdout_sha256": indexed["stdout"]["sha256"],
                    "replay_context_sha256": comparison.json_digest(
                        indexed["replay_context"]),
                    "original": projection, "current": projection,
                })
            source = carry.HistoricalEvidenceSource(
                "c2-generation", output, "baseline", source_manifest,
                source_index, (case_id,), {})
            artifact = {
                "schema_version": carry.OBSERVER_REPLAY_SCHEMA_VERSION,
                "source_index_sha256": comparison.json_digest(source.index),
                "equality_projection": list(carry.PROJECTION_FIELDS),
                "original_closure": {"module_namespace": "historical"},
                "current_closure": {"module_namespace": "final"},
                "trials": replay_trials,
            }
            with mock.patch.object(carry, "_validate_closure"):
                carry._validate_observer_replay(artifact, source, final_observer)
            replay_path = review / "observer-replay.json"
            replay_path.write_text(json.dumps(artifact))
            item = {"generation_id": source.generation_id, "arm": source.arm,
                    "observer_sha256": old_observer,
                    "current_observer_sha256": final_observer,
                    "replay": reference(replay_path)}
            history = SimpleNamespace(generation_id=source.generation_id,
                                      review_root=review)
            logical = {"identities": {"observer": final_observer}}
            with mock.patch.object(carry, "_validate_closure"):
                carry._validate_observer_replays(
                    [item], logical, (source,), (history,), {old_observer, final_observer})

            third = copy.deepcopy(item)
            third["observer_sha256"] = "d" * 64
            third_source = carry.HistoricalEvidenceSource(
                source.generation_id, source.root, source.arm,
                {"identities": {"observer": third["observer_sha256"]}},
                source.index, source.case_ids, source.models)
            with self.assertRaisesRegex(ValueError, "unreviewed"):
                carry._validate_observer_replays(
                    [third], logical, (third_source,), (history,),
                    {old_observer, final_observer})

            retained = replay_path.read_text()
            def drift(*_args):
                replay_path.write_text(retained + " ")
            with mock.patch.object(carry, "_validate_observer_replay", side_effect=drift), \
                 self.assertRaisesRegex(ValueError, "digest changed"):
                carry._validate_observer_replays(
                    [item], logical, (source,), (history,), {old_observer, final_observer})

            rejected_path = output / "baseline/rejected.jsonl"
            rejected_path.write_bytes(b"not a native event stream")
            rejected_index = copy.deepcopy(source_index)
            rejected_index["trials"][0]["stdout"] = comparison.artifact_reference(
                output, rejected_path)
            rejected_source = carry.HistoricalEvidenceSource(
                source.generation_id, source.root, source.arm, source.manifest,
                rejected_index, source.case_ids, source.models)
            rejected_artifact = copy.deepcopy(artifact)
            rejected_artifact["source_index_sha256"] = comparison.json_digest(rejected_index)
            rejected_artifact["trials"][0]["stdout_sha256"] = rejected_index[
                "trials"][0]["stdout"]["sha256"]
            with mock.patch.object(carry, "_validate_closure"), \
                 self.assertRaisesRegex(ValueError, "historical/final|rejected"):
                carry._validate_observer_replay(
                    rejected_artifact, rejected_source, final_observer)

    def test_v5_lineage_drift_stops_before_lease_activation_reservation_or_provider(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            case = {"case_id": "candidate-case"}
            plan = carry.MultiGenerationPlan(
                {}, "a" * 64, {"arms": ["baseline", "candidate"]}, tuple(), tuple(),
                frozenset({("baseline", case["case_id"])}),
                frozenset(("baseline", case["case_id"], trial) for trial in (1, 2, 3)),
                frozenset({("candidate", case["case_id"])}),
                frozenset(("candidate", case["case_id"], trial) for trial in (1, 2, 3)),
                {}, 3, 6, 9)
            request = SimpleNamespace(
                manifest={"arms": ["candidate"], "roster": [case]}, output=root,
                carry_forward={})
            rows, guards, activations = [], [], []
            class Ledger:
                def snapshot(self):
                    return {"launches": list(rows)}
                def reserve_case(self, *_args, **_kwargs):
                    rows.append("reserved")
                def prepare_publication(self, callback):
                    callback()
            def guard():
                guards.append(True)
                if len(guards) == 2:
                    raise ValueError("historical raw bytes changed")
            with mock.patch.object(execution, "execute_case",
                                   side_effect=AssertionError("provider called")) as provider, \
                 self.assertRaisesRegex(ValueError, "raw bytes"):
                execution._run_schedule(
                    request, "serial", 1, Ledger(), threading.Event(), plan, guard,
                    lambda: activations.append(True))
            provider.assert_not_called()
            self.assertEqual(rows, [])
            self.assertEqual(activations, [])
            self.assertEqual(list(root.iterdir()), [])


class CarryForwardThreatTests(unittest.TestCase):
    def test_clean_boundary_mode_uses_dedicated_admission_contract(self):
        component = {"mode": carry.CLEAN_BOUNDARY_MODE}
        sentinel = object()
        with mock.patch.object(carry, "validate_clean_boundary_carry_forward",
                               return_value=sentinel) as validator:
            result = carry.validate_multi_generation_carry_forward(
                component, {}, "manifest-digest")
        self.assertIs(result, sentinel)
        validator.assert_called_once_with(
            component, {}, "manifest-digest", approval=None,
            check_lease=True,
        )

    def test_threat_1_legacy_version_smuggling_rejected_before_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture = runpy.run_path(str(ROOT / "unit/test-trigger-campaign-execution.py"))["request_fixture"](Path(temp))
            request = execution.CampaignRequest(**{**fixture.__dict__, "carry_forward": {"schema_version": carry.SCHEMA_VERSION}})
            with mock.patch.object(Path, "mkdir", side_effect=AssertionError("mutation")), \
                 mock.patch.object(execution, "CampaignLedger", side_effect=AssertionError("ledger")), \
                 mock.patch.object(execution, "_global_lease", side_effect=AssertionError("lease")), \
                 self.assertRaisesRegex(ValueError, "versioned approval"):
                execution.run_campaign(request)

    def test_threat_2_count_list_forgery_cannot_change_ledger_derivation(self):
        manifest, snapshot = ledger_fixture()
        ordered, identities = carry._validate_terminal_ledger(snapshot, manifest)
        self.assertEqual(len(ordered), 137)
        self.assertEqual(len(identities), 411)
        for mutation in ("duplicate", "partial", "boolean"):
            bad = copy.deepcopy(snapshot)
            if mutation == "duplicate":
                bad["launches"][-1] = copy.deepcopy(bad["launches"][0])
            elif mutation == "partial":
                bad["launches"][0]["status"] = "invalid"
            else:
                bad["launches"][0]["trial_number"] = True
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                carry._validate_terminal_ledger(bad, manifest)

    def test_threat_3_predecessor_state_forgery_and_sidecars_fail_closed(self):
        manifest, snapshot = ledger_fixture()
        bad = copy.deepcopy(snapshot)
        bad["unknown_launches"] = 1
        with self.assertRaises(ValueError):
            carry._validate_terminal_ledger(bad, manifest)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            ledger = root / "ledger.sqlite3"
            ledger.write_bytes(b"frozen")
            (root / "ledger.sqlite3-wal").write_bytes(b"live")
            with self.assertRaisesRegex(ValueError, "sidecar"):
                carry._assert_sidecars_absent(root, reference(ledger))

    @unittest.skipUnless(os.name == "posix", "descriptor no-follow contract is POSIX")
    def test_threat_4_filesystem_attacks_are_bounded_and_single_descriptor(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            path = root / "safe.json"
            path.write_bytes(b"{}")
            ref = reference(path)
            self.assertEqual(carry.read_external_file(root, ref, "safe", max_bytes=2), b"{}")
            with self.assertRaisesRegex(ValueError, "size"):
                carry.read_external_file(root, ref, "safe", max_bytes=1)
            path.chmod(0o666)
            with self.assertRaisesRegex(ValueError, "mode"):
                carry.read_external_file(root, ref, "safe", max_bytes=2)
            path.chmod(0o644)
            target = root / "target"
            target.write_bytes(b"{}")
            link = root / "link"
            link.symlink_to(target)
            with self.assertRaises(ValueError):
                carry.read_external_file(root, {"path": "link", "sha256": ref["sha256"]}, "link", max_bytes=2)
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp).resolve()
            ancestor, root = parent / "ancestor", parent / "ancestor/source"
            root.mkdir(parents=True)
            path = root / "safe.json"
            path.write_bytes(b"{}")
            real_canonical = carry._canonical_root
            def race(raw, label):
                result = real_canonical(raw, label)
                ancestor.rename(parent / "moved")
                ancestor.symlink_to(parent / "moved", target_is_directory=True)
                return result
            with mock.patch.object(carry, "_canonical_root", side_effect=race), \
                 self.assertRaisesRegex(ValueError, "ancestor"):
                carry.read_external_file(root, reference(path), "race", max_bytes=2)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            path = root / "safe.json"
            path.write_bytes(b"{}")
            os.link(path, root / "alias.json")
            with self.assertRaisesRegex(ValueError, "identity"):
                carry.read_external_file(root, reference(path), "hardlink", max_bytes=2)

    def test_threat_5_cleanup_identity_uses_fingerprint_not_recycled_pid(self):
        command = ["/trusted/python", "runner.py"]
        unrelated = SimpleNamespace(returncode=0,
            stdout="501 Sun Sep 14 20:00:00 2026 /different/process\n")
        self.assertFalse(carry.predecessor_runner_is_live(15029, command, 1789426246.0,
                                                         runner=lambda *args, **kwargs: unrelated,
                                                         probe=lambda *_args: None))
        failed = SimpleNamespace(returncode=2, stdout="", stderr="inspection failed")
        with self.assertRaisesRegex(ValueError, "inconclusive"):
            carry.predecessor_runner_is_live(15029, command, 1789426246.0,
                                             runner=lambda *args, **kwargs: failed,
                                             probe=lambda *_args: None)
        later = SimpleNamespace(returncode=0,
            stdout="501 999 15228 Sun Sep 14 23:59:59 2026 unrelated\n")
        self.assertFalse(carry.predecessor_process_group_is_live(
            15228, 1789426282.0, runner=lambda *args, **kwargs: later,
            probe=lambda *_args: None))
        inventory = {
            "runners": [{"pid": 7670, "command": ["/trusted/python", "runner.py"],
                         "started_at": 100.0}],
            "groups": [{"pgid": 7685, "completed_at": 110.0}],
        }
        nonterminal_carried_group = ({"uid": os.getuid(), "pid": 7685, "pgid": 7685,
                                      "started_at": 109.0, "command": "child"},)
        self.assertFalse(carry._ownership_is_absent(inventory, nonterminal_carried_group))
        recycled_group = ({**nonterminal_carried_group[0], "started_at": 113.0},)
        self.assertTrue(carry._ownership_is_absent(inventory, recycled_group))
        with self.assertRaisesRegex(ValueError, "inspection failed"):
            carry._current_process_snapshot(
                runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(PermissionError("denied")))

    def test_threat_6_dual_replay_closure_rejects_cache_or_source_confusion(self):
        files = {"lib/a.py": "1" * 64}
        observer = comparison.json_digest(files)
        closure = {"observer_sha256": observer, "source_commit": "a" * 40,
                   "root": "/private/tmp/original-closure", "files": files, "loaded_files": files,
                   "module_namespace": "original_replay", "import_isolation": True,
                   "module_files": {"original_replay:parser":
                                    "/private/tmp/original-closure/tests/speckit-pro/lib/a.py"}}
        carry._validate_closure(closure, observer, current=False)
        for mutation in ({**closure, "import_isolation": False},
                         {**closure, "loaded_files": {"lib/a.py": "2" * 64}},
                         {**closure, "module_files": {"parser": "/tmp/escape.py"}}):
            with self.assertRaises(ValueError):
                carry._validate_closure(mutation, observer, current=False)
        generator = runpy.run_path(str(ROOT / "layer2-trigger/generate-carry-forward-replay.py"))
        projection_record = {"valid": True, "trial_valid": True, "checks": {"typed": True}}
        checker = lambda _record: {"typed": True}
        generator["record_projection"](projection_record, {"valid": True}, checker=checker)
        with self.assertRaisesRegex(ValueError, "parser rejected"):
            generator["record_projection"](projection_record, {"valid": False}, checker=checker)
        with self.assertRaisesRegex(ValueError, "checks disagree"):
            generator["record_projection"]({**projection_record, "checks": {"typed": False}},
                                            {"valid": True}, checker=checker)
        with tempfile.TemporaryDirectory() as temp:
            closure = Path(temp).resolve()
            loaded = closure / "tests/speckit-pro/lib/parser.py"
            loaded.parent.mkdir(parents=True)
            source = b"VALUE = 'reviewed'\n"
            loaded.write_bytes(source)
            expected = {"lib/parser.py": hashlib.sha256(source).hexdigest()}
            sources = generator["_reviewed_closure_sources"](closure, expected)
            loaded.write_bytes(b"VALUE = 'substituted'\n")
            finder = generator["_ClosedBytesFinder"](closure, sources, expected)
            sys.meta_path.insert(0, finder)
            try:
                with mock.patch.object(importlib.machinery.SourceFileLoader, "get_data",
                                       side_effect=AssertionError("path loader reopened source")):
                    module = finder.load("trigger_test_parser", "lib/parser.py")
            finally:
                sys.meta_path.remove(finder)
                sys.modules.pop("trigger_test_parser", None)
            self.assertEqual(module.VALUE, "reviewed")
            self.assertEqual(finder.consumed, expected)

    def test_threat_6_fresh_worker_rejects_unapproved_stdlib_shadow(self):
        with tempfile.TemporaryDirectory() as temp:
            closure = Path(temp).resolve()
            lib = closure / "tests/speckit-pro/lib"
            lib.mkdir(parents=True)
            marker = closure / "shadow-executed"
            source = b"import shlex\nVALUE = shlex.split('alpha beta')\n"
            (lib / "parser.py").write_bytes(source)
            (lib / "shlex.py").write_text(
                f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n"
                "def split(_value): return ['shadow']\n")
            expected = {"lib/parser.py": hashlib.sha256(source).hexdigest()}
            script = f"""
import json, runpy, sys
from pathlib import Path
g = runpy.run_path({str(ROOT / 'layer2-trigger/generate-carry-forward-replay.py')!r})
closure = Path({str(closure)!r})
sources = g['_reviewed_closure_sources'](closure, {expected!r})
finder = g['_ClosedBytesFinder'](closure, sources, {expected!r})
finder.sanitize_paths()
sys.meta_path.insert(0, finder)
try:
    module = finder.load('parser', 'lib/parser.py')
finally:
    sys.meta_path.remove(finder)
print(json.dumps({{'value': module.VALUE, 'consumed': finder.consumed}}))
"""
            completed = subprocess.run([sys.executable, "-c", script], check=True,
                                       capture_output=True, text=True,
                                       env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            result = json.loads(completed.stdout)
            self.assertEqual(result, {"value": ["alpha", "beta"], "consumed": expected})
            self.assertFalse(marker.exists())

    def test_threat_7_behavior_failures_are_mandatory_not_selection_inputs(self):
        manifest, snapshot = ledger_fixture()
        ordered, _identities = carry._validate_terminal_ledger(snapshot, manifest)
        self.assertEqual(len(ordered), 137)
        self.assertNotIn(carry.PARTIAL_CASE_ID, ordered)
        self.assertEqual(carry.BEHAVIOR_FAILURES,
                         frozenset({"l2-1b43ca2d753dec02b20c5e17", "l2-d714c484e5bbf90475418772"}))

    def test_threat_8_carried_rows_or_overlap_cannot_enter_fresh_ledger(self):
        plan = plan_fixture()
        fresh = [{"arm": "serial:baseline", "case_id": "fresh", "trial_number": trial}
                  | {"status": "complete"} for trial in (1, 2, 3)]
        carry.validate_fresh_ledger(plan, fresh)
        with self.assertRaises(ValueError):
            carry.validate_fresh_ledger(plan, [*fresh,
                {"arm": "serial:baseline", "case_id": "carried", "trial_number": 1}])

    def test_threat_9_between_case_drift_stops_all_later_reservations(self):
        plan = plan_fixture()
        rows, calls = [], []
        state = {"changed": False, "guards": 0}
        class Ledger:
            def snapshot(self):
                return {"launches": list(rows)}
            def reserve_case(self, arm, case_id):
                rows.extend({"arm": arm, "case_id": case_id, "trial_number": trial,
                             "status": "unknown"} for trial in (1, 2, 3))
            def finish_case(self, arm, case_id, status):
                for row in rows:
                    if (row["arm"], row["case_id"]) == (arm, case_id):
                        row["status"] = status
        def provider(*_args):
            calls.append(True)
            state["changed"] = True
            return 0
        def guard():
            state["guards"] += 1
            if state["changed"]:
                raise ValueError("source drift after first fresh case")
        stop = threading.Event()
        with tempfile.TemporaryDirectory() as temp:
            request = SimpleNamespace(manifest={"arms": ["baseline", "candidate"],
                                      "roster": [{"case_id": "carried"}, {"case_id": "fresh"}]},
                                      output=Path(temp), carry_forward={})
            with mock.patch.object(execution, "execute_case", side_effect=provider), \
                 mock.patch.object(execution, "_settle_case", return_value="complete"), \
                 mock.patch.object(execution, "_build_schedule_index", return_value={}), \
                 self.assertRaisesRegex(ValueError, "source drift"):
                execution._run_schedule(request, "serial", 1, Ledger(), stop, plan, guard)
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(rows), 3)
        self.assertTrue(stop.is_set())

    def test_threat_10_partial_publication_is_not_reconstructed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "new"
            root.mkdir()
            (root / "carry-forward-lineage.json").write_text("{}")
            request = SimpleNamespace(output=root)
            with self.assertRaisesRegex(ValueError, "partial"):
                execution._publish_carry_request(request, plan_fixture())
            self.assertEqual([path.name for path in root.iterdir()], ["carry-forward-lineage.json"])

    def test_threat_11_carry_timing_is_non_contiguous_and_ineligible(self):
        manifest = {"experiment_id": "new", "roster": [{"case_id": f"case-{n}"} for n in range(217)]}
        plan = SimpleNamespace(component={}, source_root=Path("/tmp/old"), source_manifest={},
                               partial_manifest={}, source_index={}, carried_case_ids=tuple(f"case-{n}" for n in range(137)),
                               fresh_case_ids=tuple(f"case-{n}" for n in range(137, 217)))
        index = carry.source_aware_index(manifest, plan, {})
        self.assertTrue(index["non_contiguous"])
        self.assertFalse(index["timing_eligible"])

    def test_clean_boundary_schedule_reserves_only_the_remaining_336_codex_trials(self):
        case_ids = tuple(f"case-{number:03d}" for number in range(217))
        carried_ids, fresh_ids = case_ids[:105], case_ids[105:]
        logical = {"experiment_id": "clean-boundary", "arms": ["candidate"],
                   "roster": [{"case_id": case_id} for case_id in case_ids]}
        plan = carry.MultiGenerationPlan(
            {"mode": carry.CLEAN_BOUNDARY_MODE}, "a" * 64, logical, tuple(), tuple(),
            frozenset(("candidate", case_id) for case_id in carried_ids),
            frozenset(("candidate", case_id, trial) for case_id in carried_ids
                      for trial in (1, 2, 3)),
            frozenset(("candidate", case_id) for case_id in fresh_ids),
            frozenset(("candidate", case_id, trial) for case_id in fresh_ids
                      for trial in (1, 2, 3)),
            {}, 336, 315, 651)
        rows = []

        class Ledger:
            def snapshot(self):
                return {"launches": list(rows)}

            def reserve_case(self, arm, case_id):
                rows.extend({"arm": arm, "case_id": case_id, "trial_number": trial,
                             "status": "unknown"} for trial in (1, 2, 3))

            def finish_case(self, arm, case_id, status):
                for row in rows:
                    if row["arm"] == arm and row["case_id"] == case_id:
                        row["status"] = status

        with tempfile.TemporaryDirectory() as temp:
            request = SimpleNamespace(
                manifest={"arms": ["candidate"],
                          "roster": [{"case_id": case_id} for case_id in fresh_ids]},
                output=Path(temp), carry_forward={})
            with mock.patch.object(execution, "execute_case", return_value=0) as provider, \
                 mock.patch.object(execution, "_settle_case", return_value="complete"), \
                 mock.patch.object(execution, "_build_schedule_index", return_value={}):
                execution._run_schedule(request, "serial", 1, Ledger(), threading.Event(), plan,
                                        lineage_guard=lambda: None)
        self.assertEqual(provider.call_count, len(fresh_ids))
        self.assertEqual(len(rows), 336)
        self.assertEqual({(row["case_id"], row["trial_number"]) for row in rows},
                         {(case_id, trial) for case_id in fresh_ids for trial in (1, 2, 3)})

    def test_threat_12_source_union_preserves_exit_code_separation(self):
        manifest = {"experiment_id": "new", "roster": [{"case_id": f"case-{n}"} for n in range(217)]}
        carried = [f"case-{n}" for n in range(137)]
        fresh = [f"case-{n}" for n in range(137, 217)]
        index = {"schema_version": carry.INDEX_SCHEMA_VERSION, "experiment_id": "new",
                 "experiment_sha256": comparison.json_digest(manifest), "arm": "baseline",
                 "non_contiguous": True, "timing_eligible": False, "carry_forward": {},
                 "sources": [{"kind": "carried", "root": "/tmp/old", "manifest": {}, "index": {}, "case_ids": carried},
                             {"kind": "fresh", "root": None, "manifest": {}, "index": {}, "case_ids": fresh}]}
        carry.source_aware_union(index, manifest, "baseline")
        bad = copy.deepcopy(index)
        bad["sources"][1]["case_ids"][0] = carried[0]
        with self.assertRaises(ValueError):
            carry.source_aware_union(bad, manifest, "baseline")
        self.assertEqual(comparison.compare_evidence(manifest, Path("."), {}, {})["exit_code"], 2)

    def test_scaled_positive_scheduler_skips_carried_and_reserves_each_fresh_case_once(self):
        plan = plan_fixture()
        manifest = {"arms": ["baseline", "candidate"],
                    "roster": [{"case_id": "carried"}, {"case_id": "fresh"}]}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = SimpleNamespace(manifest=manifest, output=root, carry_forward={})
            rows = []
            class Ledger:
                def snapshot(self):
                    return {"launches": list(rows)}
                def reserve_case(self, arm, case_id):
                    rows.extend({"arm": arm, "case_id": case_id, "trial_number": trial, "status": "unknown"}
                                for trial in (1, 2, 3))
                def finish_case(self, arm, case_id, status):
                    for row in rows:
                        if row["arm"] == arm and row["case_id"] == case_id:
                            row["status"] = status
            ledger = Ledger()
            with mock.patch.object(execution, "execute_case", return_value=0) as provider, \
                 mock.patch.object(execution, "_settle_case", return_value="complete"), \
                 mock.patch.object(execution, "_build_schedule_index", return_value={}):
                execution._run_schedule(request, "serial", 1, ledger, threading.Event(), plan,
                                        lineage_guard=lambda: None)
            self.assertEqual(provider.call_count, 3)
            self.assertEqual(len(rows), 9)
            self.assertFalse(any(row["case_id"] == "carried" and row["arm"] == "serial:baseline" for row in rows))


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-trigger-carry-forward"))
