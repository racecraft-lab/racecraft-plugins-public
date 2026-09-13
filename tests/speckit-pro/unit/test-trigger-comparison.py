#!/usr/bin/env python3
"""Provider-free comparison contracts; native streams are replayed, not mocked."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
import trigger_comparison as comparison
import trigger_evidence as evidence
from test_result import run_counted


class ComparisonTests(unittest.TestCase):
    def test_manifest_rejects_boolean_numbers_and_identity_drift(self):
        manifest = minimal_manifest()
        comparison.validate_experiment(manifest)
        for key, value in (("trials", True), ("threshold", True), ("trials", 2),
                           ("trial_timeout_seconds", True), ("trial_timeout_seconds", 0),
                           ("trial_timeout_seconds", -1), ("trial_timeout_seconds", 180.0),
                           ("trial_timeout_seconds", None)):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                comparison.validate_experiment({**manifest, key: value})
        bad = copy.deepcopy(manifest)
        bad["roster"][0]["query"] = "changed"
        with self.assertRaises(ValueError):
            comparison.validate_experiment(bad)

    def test_missing_timeout_is_not_an_approved_trial_policy(self):
        manifest = minimal_manifest()
        del manifest["trial_timeout_seconds"]
        with self.assertRaisesRegex(ValueError, "timeout"):
            comparison.validate_experiment(manifest)

    def test_replay_refuses_changed_or_missing_native_timeout(self):
        for host in ("claude", "codex"):
            with self.subTest(host=host), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                manifest, indexes = evidence_fixture(root, host=host)
                report_path = root / "candidate/report.json"
                original = json.loads(report_path.read_text())
                for timeout in (181, True, None):
                    with self.subTest(timeout=timeout):
                        report = copy.deepcopy(original)
                        report["metadata"]["trial_timeout_seconds"] = timeout
                        report_path.write_text(json.dumps(report))
                        for item in indexes[1]["trials"]:
                            item["report"] = comparison.artifact_reference(root, report_path)
                        self.assertEqual(comparison.compare_evidence(manifest, root, *indexes)["exit_code"], 2)

    def test_raw_hit_regressions_are_not_hidden_by_boolean_grade(self):
        for polarity, before, after in ((True, 3, 2), (False, 0, 1)):
            verdict = comparison.compare_hits(polarity, before, after)
            self.assertTrue(verdict["candidate_pass"])
            self.assertTrue(verdict["regression"])
        verdict = comparison.compare_hits(True, 0, 1)
        self.assertFalse(verdict["candidate_pass"])
        self.assertFalse(verdict["regression"])

    def test_artifact_cannot_escape_or_change(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "record.json"
            path.write_text("{}")
            ref = comparison.artifact_reference(root, path)
            self.assertEqual(comparison.read_artifact(root, ref), b"{}")
            path.write_text("[]")
            with self.assertRaises(ValueError):
                comparison.read_artifact(root, ref)
            with self.assertRaises(ValueError):
                comparison.read_artifact(root, {"path": "../outside", "sha256": "0" * 64})

    def test_real_parser_replay_and_summary_forgery(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, indexes = evidence_fixture(root)
            result = comparison.compare_evidence(manifest, root, indexes[0], indexes[1])
            self.assertEqual(result["exit_code"], 0, result)
            indexes[1]["trials"].reverse()
            self.assertEqual(comparison.compare_evidence(manifest, root, *indexes)["exit_code"], 0)
            for mutation in ("selected", "missing", "duplicate", "bool", "context", "cleanup", "pin"):
                with self.subTest(mutation=mutation):
                    bad = copy.deepcopy(indexes)
                    if mutation == "selected":
                        bad[1]["trials"][0]["selected"] = False
                    elif mutation == "missing":
                        bad[1]["trials"].pop()
                    elif mutation == "duplicate":
                        bad[1]["trials"].append(bad[1]["trials"][0])
                    elif mutation == "bool":
                        bad[1]["trials"][0]["trial_number"] = True
                    elif mutation == "context":
                        bad[1]["trials"][0].pop("replay_context")
                    elif mutation == "cleanup":
                        bad[1]["cleanup"] = []
                    else:
                        bad[1]["pins"]["claude"]["model"] = "wrong"
                    self.assertEqual(comparison.compare_evidence(manifest, root, *bad)["exit_code"], 2)

    def test_incomplete_historical_evidence_is_diagnostic(self):
        result = comparison.compare_evidence(minimal_manifest(), Path("."), {}, {})
        self.assertEqual(result["exit_code"], 2)
        self.assertFalse(result["qualification"])

    def test_codex_replays_retained_full_witness_bodies(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, indexes = evidence_fixture(root, host="codex")
            result = comparison.compare_evidence(manifest, root, *indexes)
            self.assertEqual(result["exit_code"], 0, result)
            context = indexes[1]["trials"][0]["replay_context"]
            context["witnesses"][context["target_skill"]].pop("body")
            self.assertEqual(comparison.compare_evidence(manifest, root, *indexes)["exit_code"], 2)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO is a POSIX adversarial input")
    def test_fifo_artifact_rejected_without_reading(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            os.mkfifo(root / "fifo")
            with self.assertRaisesRegex(ValueError, "regular"):
                comparison.read_artifact(root, {"path": "fifo", "sha256": "0" * 64})


def minimal_manifest():
    entry = {"query": "Use demo", "should_trigger": True}
    roster = [{"case_id": evidence.case_id("claude", "demo", entry), "host": "claude", "skill": "demo", **entry}]
    return {
        "schema_version": "trigger-experiment/v1", "experiment_id": "test", "trials": 3,
        "threshold": 0.5, "trial_timeout_seconds": 180, "qualification_scope": "pr-core", "roster": roster,
        "corpus_sha256": comparison.json_digest(roster), "inventory_sha256": "1" * 64,
        "pins": {"claude": {"model": "claude-sonnet-test", "cli_version": "test"}},
        "identities": {"observer": comparison.observer_digest(), "catalog": "2" * 64, "fixture": "3" * 64},
        "controlled_difference": {"path": "no-op-description", "baseline_sha256": "4" * 64, "candidate_sha256": "5" * 64},
        "arms": ["baseline", "candidate"],
    }


def evidence_fixture(root, host="claude", entry_override=None, selected_pattern=(True, True, True)):
    spec = importlib.util.spec_from_file_location("trigger_fixture_source", ROOT / "unit/test-trigger-eval-runners.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    manifest = minimal_manifest()
    snapshot = comparison.measurement_snapshot()
    manifest["identities"] = comparison.snapshot_identities(snapshot)
    inventory = root / "inventory.json"
    inventory.write_bytes((ROOT / "layer2-trigger/case-inventory.json").read_bytes())
    active = json.loads(inventory.read_bytes())["active"]
    selected = entry_override or next(row for row in active if row["host"] == host and row["should_trigger"])
    model = "claude-sonnet-test" if host == "claude" else "gpt-5.6-sol"
    manifest["pins"] = {host: {"model": model, "cli_version": "test"}}
    manifest["roster"] = [{key: selected[key] for key in ("case_id", "host", "skill", "query", "should_trigger")}]
    manifest["corpus_sha256"] = comparison.json_digest(manifest["roster"])
    manifest["inventory_sha256"] = hashlib.sha256(inventory.read_bytes()).hexdigest()
    for arm in manifest["arms"]:
        (root / f"{arm}-description.txt").write_text(f"{arm} no-op description")
        manifest["controlled_difference"][f"{arm}_sha256"] = hashlib.sha256((root / f"{arm}-description.txt").read_bytes()).hexdigest()
    indexes = []
    for arm in manifest["arms"]:
        directory = root / arm
        directory.mkdir()
        entry = manifest["roster"][0]
        context, streams, preflight, catalog = native_fixture(helper, root, host, entry, model, arm, selected_pattern)
        records = []
        report_trials = []
        for number in range(1, 4):
            raw = streams[number - 1]
            stdout = directory / f"{number}.jsonl"
            stderr = directory / f"{number}.stderr"
            stdout.write_bytes(raw)
            stderr.write_bytes(b"")
            parsed = comparison.replay(raw, context)
            execution = {
                "provider_exit_code": 0, "timed_out": False, "interrupted_by_signal": None,
                "cleanup_verified": True, "cleanup_error": None, "cleanup_scope": "owned-process-group",
                "unexpected_descendants": False, "child_pid": 1234, "child_pgid": 1234,
                "cleanup_observations": [{"pgid": 1234, "errno": 3}], "process_error": None,
                "launch_contract": {"config_isolated": True, "retries_disabled": True, "requested_model": model,
                                    "stdin_prompt_isolated": True, "login_state_source": "CODEX_HOME",
                                    "shell_home_isolated": True, "scratch_directory_isolated": True,
                                    "query_sha256": hashlib.sha256(entry["query"].encode()).hexdigest()},
            }
            record = evidence.make_trial_record(host, entry["skill"], entry, 1, number,
                {**parsed, "qualification_eligible": True},
                {"stdout_path": str(stdout), "stdout_sha256": hashlib.sha256(raw).hexdigest(),
                 "stderr_path": str(stderr), "stderr_sha256": hashlib.sha256(b"").hexdigest()}, execution)
            record_path = directory / f"{number}.trial.json"
            record_path.write_text(json.dumps(record))
            report_trials.append({**record, "trial_record_path": str(record_path), "trial_record_sha256": hashlib.sha256(record_path.read_bytes()).hexdigest()})
            records.append({"case_id": entry["case_id"], "trial_number": number, "selected": selected_pattern[number - 1],
                "record": comparison.artifact_reference(root, record_path),
                "stdout": comparison.artifact_reference(root, stdout), "stderr": comparison.artifact_reference(root, stderr),
                "replay_context": context})
        report = directory / "report.json"
        passed = (sum(selected_pattern) / 3 >= 0.5) == entry["should_trigger"]
        report.write_text(json.dumps({"metadata": {"replay_context": context, "input_snapshot": snapshot,
            "preflight": preflight, "catalog_preflight": catalog, "trial_timeout_seconds": manifest["trial_timeout_seconds"],
            "no_op_description_sha256": manifest["controlled_difference"][f"{arm}_sha256"]},
            "summary": {"total": 1, "passed": int(passed), "failed": int(not passed), "complete": True, "not_run": 0,
                        "requested_model": model, "qualification_eligible": True},
            "results": [evidence.case_result(host, entry["skill"], entry, report_trials, 3, 0.5)]}))
        for record in records:
            record["report"] = comparison.artifact_reference(root, report)
        cleanup = directory / "arm-cleanup.json"
        cleanup.write_text(json.dumps({"schema_version": "trigger-arm-cleanup/v1", "workspace": str((root / "removed").resolve()),
                                     "workspace_removed": True, "runner_exit_code": 0 if passed else 1, "cleanup_error": None}))
        indexes.append({"schema_version": "trigger-evidence-index/v1", "experiment_id": manifest["experiment_id"],
            "experiment_sha256": comparison.json_digest(manifest), "arm": arm, "pins": copy.deepcopy(manifest["pins"]),
            "identities": manifest["identities"], "trials": records, "cleanup": [comparison.artifact_reference(root, cleanup)],
            "inventory": comparison.artifact_reference(root, inventory),
            "controlled_description": comparison.artifact_reference(root, root / f"{arm}-description.txt"),
            "summary": {entry["case_id"]: {"target_hits": sum(selected_pattern), "pass": passed}}, "complete": True})
    return manifest, indexes


def native_fixture(helper, root, host, entry, model, arm, selected_pattern):
    parser = comparison._parser(host)
    target = f"{entry['skill']}-eval-0123456789ab"
    source = parser.find_skill_source(entry["skill"])
    workspace = (root / "removed").resolve()
    context = {"host": host, "source_skill": entry["skill"], "requested_model": model, "no_op_description": f"{arm} no-op description"}
    with mock.patch.object(parser, "NO_SPECKIT_SKILL_DESCRIPTION", context["no_op_description"]):
        if host == "claude":
            siblings = {path.name: path / "SKILL.md" for path in parser.sibling_skill_dirs(source)}
            parser.stage_measurement_plugin(source, workspace, "catalog", target, "nonce", siblings)
            context.update(plugin_name="catalog", plugin_root=str(workspace), expected_skill=f"catalog:{target}", nonce="nonce",
                sibling_skills=[f"catalog:{name}" for name in (*siblings, "no-speckit-skill")],
                staged_skill_bodies={path.parent.name: path.read_text() for path in (workspace / "skills").glob("*/SKILL.md")})
            streams = []
            for selected in selected_pattern:
                events = [json.loads(line) for line in helper.claude_stream(workspace, "catalog", f"catalog:{target}", "nonce", selected=selected).splitlines()]
                events[0]["skills"] = [f"catalog:{target}", *context["sibling_skills"]]
                streams.append("\n".join(map(json.dumps, events)).encode())
            preflight = {"version": "test", "request_retries": 0, "settings_sources": [], "doctor_checks": {"fixture": True}, "managed_checks": {"fixture": True}}
            catalog = None
        else:
            marker = parser.selection_marker(target, "0123456789ab")
            parser.stage_repository_skill(source, workspace, target, marker)
            siblings, markers = parser.stage_sibling_skills(source, workspace, "0123456789ab")
            witnesses = parser.skill_witnesses(workspace, {target: marker, **markers})
            for name, witness in witnesses.items():
                witness["source_locator"] = f"r0/{name}/SKILL.md"
            context.update(target_skill=target, workspace=str(workspace), witnesses=witnesses)
            streams = [helper.codex_stream(witnesses, selected_skill=target if selected else None) for selected in selected_pattern]
            preflight = {"version": "test", "request_max_retries": 0, "stream_max_retries": 0, "unbounded_connection_retries": False}
            catalog = {"target_entries": 1, "sibling_entries_exact": True, "target_description_exact": True,
                       "target_file_exact": True, "source_locators_exact": True, "warning_present": False}
    shutil.rmtree(workspace)
    return context, streams, preflight, catalog


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(ComparisonTests), label="test-trigger-comparison"))
