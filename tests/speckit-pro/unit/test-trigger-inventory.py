#!/usr/bin/env python3
"""Provider-free corpus curation and launch-plan contracts."""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TESTS / "lib"))
from test_result import run_counted
from trigger_evidence import case_id
from trigger_inventory import InventoryError, canonical_sha256, load_inventory, plan_inventory, validate_inventory

LAYER = TESTS / "layer2-trigger"


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.inventory = load_inventory(LAYER / "case-inventory.json")

    @staticmethod
    def replace_explicit_query(value, host, skill, query):
        row = next(
            row for row in value["active"]
            if row["host"] == host and row["skill"] == skill and row["category"] == "explicit"
        )
        row["query"] = query
        row["case_id"] = case_id(host, skill, {"query": query, "should_trigger": True})
        return row

    def test_all_original_occurrences_accounted_for_and_actual_corpora_match(self):
        report = validate_inventory(self.inventory, LAYER)
        self.assertEqual(report["original_cases"], 438)
        self.assertEqual(report["corpora"], 23)
        self.assertEqual(report["protected_cases"], 14)
        self.assertGreaterEqual(report["active_cases"], 161)
        self.assertEqual(report["active_cases"], 217)
        self.assertTrue(report["minimum_reduction_met"])
        self.assertFalse(report["target_200_met"])

    def test_full_launch_arithmetic_and_scope(self):
        plan = plan_inventory(self.inventory, LAYER, "full")
        self.assertEqual(plan["launch_count"], len(plan["roster"]) * 6)
        self.assertEqual(plan["qualification_scope"], "full")
        self.assertFalse(plan["qualification_established"])
        self.assertFalse(plan["launch_authorized"])
        self.assertEqual(plan["trials"], 3)

    def test_explicit_smokes_are_plain_host_specific_named_skill_prompts(self):
        report = validate_inventory(self.inventory, LAYER)
        explicit = [row for row in self.inventory["active"] if row["category"] == "explicit"]
        self.assertEqual(len(explicit), 23)
        self.assertEqual(report["active_cases"], 217)
        self.assertEqual(report["full_launches"], 1302)
        self.assertEqual(plan_inventory(self.inventory, LAYER, "full")["launch_count"], 1302)
        for row in explicit:
            with self.subTest(host=row["host"], skill=row["skill"]):
                target = f"speckit-pro:{row['skill']}" if row["host"] == "claude" else row["skill"]
                self.assertFalse(row["query"].lstrip().startswith(("/", "$")))
                self.assertIn(f"use the {target} skill", row["query"].casefold())
                self.assertIs(row["should_trigger"], True)
                self.assertEqual(row["source_case_ids"], [])

    def test_rejects_previous_native_control_syntax_with_content_valid_identity(self):
        cases = (
            ("claude", "/speckit-pro:grill-me — use this skill for its documented purpose in this repository."),
            ("codex", "$grill-me — use this skill for its documented purpose in this repository."),
            ("codex", "Please use the grill-me skill for its documented purpose in this repository. $grill-me"),
        )
        for host, query in cases:
            with self.subTest(host=host):
                value = copy.deepcopy(self.inventory)
                self.replace_explicit_query(value, host, "grill-me", query)
                with self.assertRaisesRegex(InventoryError, "must not use native control syntax"):
                    validate_inventory(value, LAYER)

    def test_rejects_forged_missing_or_wrong_explicit_target(self):
        value = copy.deepcopy(self.inventory)
        row = next(row for row in value["active"] if row["category"] == "explicit")
        row["case_id"] = "l2-" + "0" * 24
        with self.assertRaisesRegex(InventoryError, "forged or duplicate active identity"):
            validate_inventory(value, LAYER)

        cases = (
            ("claude", "Please use the relevant skill for its documented purpose in this repository."),
            ("claude", "Please use the speckit-pro:speckit-coach skill for its documented purpose in this repository."),
            ("codex", "Please use the relevant skill for its documented purpose in this repository."),
            ("codex", "Please use the speckit-coach skill for its documented purpose in this repository."),
        )
        for host, query in cases:
            with self.subTest(host=host, query=query):
                value = copy.deepcopy(self.inventory)
                self.replace_explicit_query(value, host, "grill-me", query)
                with self.assertRaisesRegex(InventoryError, "must clearly name the exact target skill"):
                    validate_inventory(value, LAYER)

    def test_explicit_repair_preserves_historical_control_and_non_explicit_rows(self):
        active = self.inventory["active"]
        pilot = set(self.inventory["pilot_case_ids"])
        self.assertEqual(len([row for row in active if row["category"] != "explicit"]), 194)
        self.assertEqual(canonical_sha256(self.inventory["source_corpora"]), "84cf65444a26c1016599cb8523b86597b94a48cd971f6e35e7aad7561a6857e8")
        self.assertEqual(canonical_sha256(self.inventory["originals"]), "98dc8212f243d22dddb122851d7d1c5f4bbb16a64145ee37487565d5816f6279")
        self.assertEqual(canonical_sha256([row for row in active if row["category"] != "explicit"]), "badbfff5a6e157b2de4c56220b7af2966dcc44c7e32c4beceae4d8c8f67dc3e8")
        self.assertEqual(canonical_sha256(self.inventory["protected_case_ids"]), "6aea5a7c41f19267cbe4dec849e135797e94243f9c1ab70bbf2e13eb77b620a7")
        self.assertEqual(canonical_sha256(self.inventory["pilot_case_ids"]), "acbae951211b4131bc35ac90af4554074cd82586d65e79a54b79b216c24682c0")
        self.assertEqual(canonical_sha256([row for row in active if row["case_id"] in pilot]), "3b19b1f147dec8748659c8d78c4dfcfaebfdd0d2dd4dfb7ebf8b450543881be7")

    def test_pr_core_keeps_protected_controls_and_expands_related_boundaries(self):
        plan = plan_inventory(self.inventory, LAYER, "pr-core", changed_skills=["speckit-prd"])
        ids = {row["case_id"] for row in plan["roster"]}
        self.assertTrue(set(self.inventory["protected_case_ids"]) <= ids)
        self.assertTrue(any(row["skill"] == "speckit-coach" for row in plan["roster"]))
        self.assertLess(plan["launch_count"], plan_inventory(self.inventory, LAYER, "full")["launch_count"])
        self.assertEqual(plan["qualification_scope"], "pr-core")
        self.assertEqual(plan["corpus_sha256"], canonical_sha256(plan["roster"]))

    def test_unknown_empty_or_global_pr_impact_expands_full(self):
        for arguments in ({}, {"changed_skills": ["unknown-skill"]}, {"changed_paths": ["tests/speckit-pro/lib/trigger_evidence.py"]}):
            with self.subTest(arguments=arguments):
                plan = plan_inventory(self.inventory, LAYER, "pr-core", **arguments)
                self.assertEqual(plan["qualification_scope"], "full")
                self.assertTrue(plan["expanded_to_full"])

    def test_known_skill_path_selects_nonempty_pr_core(self):
        plan = plan_inventory(self.inventory, LAYER, "pr-core", changed_paths=["speckit-pro/codex-skills/speckit-prd/SKILL.md"])
        self.assertEqual(plan["qualification_scope"], "pr-core")
        self.assertGreater(plan["launch_count"], 0)

    def test_pilot_has_eight_cases_and_48_launches_one_behavior_arm(self):
        plan = plan_inventory(self.inventory, LAYER, "pilot")
        self.assertEqual(len(plan["roster"]), 8)
        self.assertEqual(plan["launch_count"], 48)
        self.assertEqual(plan["arms"], ["candidate"])
        self.assertEqual(plan["schedules"], ["serial", "two-worker"])
        for host in ("claude", "codex"):
            self.assertEqual(sum(row["host"] == host for row in plan["roster"]), 4)

    def test_rejects_missing_original_duplicate_active_and_boolean_position(self):
        for edit in (lambda v: v["originals"].pop(), lambda v: v["active"].append(v["active"][0]), lambda v: v["originals"][0].update(original_position=True)):
            value = copy.deepcopy(self.inventory)
            edit(value)
            with self.assertRaises(InventoryError):
                validate_inventory(value, LAYER)

    def test_rejects_stale_snapshot_digest_forged_identity_and_unmapped_disposition(self):
        for edit in (lambda v: v["source_corpora"][0].update(sha256="0" * 64), lambda v: v["originals"][0].update(case_id="l2-forged"), lambda v: v["originals"][0].update(covered_by=[])):
            value = copy.deepcopy(self.inventory)
            edit(value)
            with self.assertRaises(InventoryError):
                validate_inventory(value, LAYER)

    def test_rejects_lost_protected_case_missing_rationale_or_uncovered_boundary(self):
        for edit in (lambda v: v["protected_case_ids"].pop(), lambda v: v["originals"][0].update(rationale=""), lambda v: v["originals"][0].update(boundaries=["invented-uncovered-boundary"])):
            value = copy.deepcopy(self.inventory)
            edit(value)
            with self.assertRaises(InventoryError):
                validate_inventory(value, LAYER)

    def test_repeat_prompts_have_host_skill_specific_rationale(self):
        validate_inventory(self.inventory, LAYER)
        groups = {}
        for row in self.inventory["active"]:
            groups.setdefault((row["host"], row["query"]), []).append(row)
        repeats = [row for rows in groups.values() if len(rows) > 1 for row in rows]
        self.assertTrue(repeats)
        self.assertTrue(all(row["repeat_rationale"] and row["skill"] in row["repeat_rationale"] for row in repeats))

    def test_formal_advice_and_execution_keep_the_topic_overlap(self):
        for host in ("claude", "codex"):
            original = next(row for row in self.inventory["originals"] if row["host"] == host and row["skill"] == "speckit-coach" and row["original_position"] == 30)
            self.assertIn(original["case_id"], {row["case_id"] for row in self.inventory["active"]})

    def test_rejects_forged_reciprocal_original_membership(self):
        value = copy.deepcopy(self.inventory)
        value["active"][1]["source_case_ids"] = []
        with self.assertRaises(InventoryError):
            validate_inventory(value, LAYER)

    def test_malformed_types_fail_closed(self):
        for edit in (lambda v: v["originals"][0].update(rationale=None), lambda v: v["active"][0].update(boundaries="not-a-list")):
            value = copy.deepcopy(self.inventory)
            edit(value)
            with self.assertRaises(InventoryError):
                validate_inventory(value, LAYER)

    def test_cli_is_provider_free_and_rejects_invalid_inventory(self):
        script = LAYER / "plan-trigger-evals.py"
        for scope, count in (("full", 1302), ("pilot", 48)):
            result = subprocess.run([sys.executable, str(script), "--scope", scope], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            self.assertEqual(output["launch_count"], count)
            self.assertIs(output["launch_authorized"], False)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text("{}", encoding="utf-8")
            result = subprocess.run([sys.executable, str(script), "--inventory", str(path)], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIs(json.loads(result.stdout)["valid"], False)

    def test_cli_binds_exact_custom_inventory_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("evals", "codex-evals"):
                shutil.copytree(LAYER / name, root / name)
            path = root / "reviewed-custom.json"
            payload = json.dumps(self.inventory, ensure_ascii=False, indent=4).encode() + b"\n"
            path.write_bytes(payload)
            result = subprocess.run([sys.executable, str(LAYER / "plan-trigger-evals.py"), "--inventory", str(path)], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["inventory_sha256"], hashlib.sha256(payload).hexdigest())


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(InventoryTests), label="test-trigger-inventory"))
