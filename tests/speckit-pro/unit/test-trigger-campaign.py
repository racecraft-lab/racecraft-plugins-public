#!/usr/bin/env python3
"""Campaign budgets and recovery without native providers."""
from __future__ import annotations

import concurrent.futures
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
import trigger_campaign as campaign
import trigger_comparison as comparison
from test_result import run_counted
from trigger_inventory import load_inventory, plan_inventory


def approval(digest="a" * 64, budget=6):
    return {"schema_version": "trigger-campaign-approval/v1", "manifest_sha256": digest,
            "launch_budget": budget, "source": {"role": "user", "message_id": "user-message-123",
                "content": f"Approve trigger campaign {digest} with launch budget {budget}."}}


def contextual_approval(digest="a" * 64, budget=6, response="approved"):
    session = "retained-session-123"
    request_id = "assistant-message-123"
    response_id = "user-message-456"
    request = f"Approve trigger campaign {digest} with launch budget {budget}."

    def observation(role, message_id, timestamp, ordinal, content):
        return {"role": role, "message_id": message_id, "session_id": session,
                "timestamp": timestamp, "source_ordinal": ordinal, "content": content,
                "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
                "source_line_sha256": hashlib.sha256(f"retained:{message_id}:{content}".encode()).hexdigest()}

    return {"schema_version": "trigger-campaign-approval/v2", "manifest_sha256": digest,
            "launch_budget": budget, "recorder_observation": {
                "observer": "trusted-orchestrator", "session_id": session,
                "adjacent_user_visible_message_ids": [request_id, response_id],
                "request": observation("assistant", request_id, "2026-09-14T16:00:00.000Z", 100, request),
                "response": observation("user", response_id, "2026-09-14T16:00:01.000Z", 101, response)}}


def full_manifest(output):
    inventory = json.loads((ROOT / "layer2-trigger/case-inventory.json").read_bytes())
    roster = [{key: row[key] for key in ("case_id", "host", "skill", "query", "should_trigger")}
              for row in inventory["active"]]
    return {
        "schema_version": "trigger-experiment/v1", "experiment_id": "standing-campaign-test",
        "trials": 3, "threshold": 0.5, "trial_timeout_seconds": 180,
        "qualification_scope": "full", "roster": roster,
        "corpus_sha256": campaign.json_digest(roster), "inventory_sha256": "1" * 64,
        "pins": {host: {"model": model, "cli_version": "test"} for host, model in
                 (("claude", "claude-sonnet-test"), ("codex", "gpt-5.6-sol"))},
        "identities": {"observer": "2" * 64, "catalog": "3" * 64, "fixture": "4" * 64},
        "controlled_difference": {"path": "no-op-description", "baseline_sha256": "5" * 64,
                                  "candidate_sha256": "6" * 64},
        "arms": ["baseline", "candidate"], "output_directory": str(output.resolve()),
    }


def standing_approval(manifest, *, grant=None, quota=None, latest="approved"):
    session = "retained-session-123"
    grant = grant or "Listen I APPROVE EVERYTHING that blocks or could block this goal from being achieved."
    quota = quota or "just run until the quota is run out"

    def observation(message_id, timestamp, ordinal, content):
        return {"role": "user", "message_id": message_id, "session_id": session,
                "timestamp": timestamp, "source_ordinal": ordinal, "content": content,
                "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
                "source_line_sha256": hashlib.sha256(f"retained:{message_id}:{content}".encode()).hexdigest()}

    digest = campaign.json_digest(manifest)
    grant_observation = observation("user-grant-123", "2026-09-12T23:05:29.095Z", 6605, grant)
    quota_observation = observation("user-quota-456", "2026-09-14T16:55:51.704Z", 28489, quota)
    latest_observation = observation("user-latest-789", "2026-09-14T17:30:00.000Z", 29538, latest)
    continuity = {
        "reference_manifest_sha256": "7" * 64, "assessment_sha256": "8" * 64,
        "result": "unchanged",
        "unchanged_dimensions": [
            "qualification_scope", "roster", "arms", "trials", "trial_timeout_seconds", "threshold",
            "corpus_sha256", "inventory_sha256", "pins", "controlled_difference",
            "identities.catalog", "identities.fixture", "acceptance_rules",
        ],
        "permitted_binding_changes": ["experiment_id", "output_directory", "identities.observer"],
    }
    predecessor_output = str((Path(manifest["output_directory"]).parent / "old-campaign").resolve())
    predecessor = {
        "manifest_sha256": "7" * 64, "ledger_sha256": "d" * 64,
        "output_directory": predecessor_output, "launch_budget": 1302,
        "charged_launches": 312, "unreserved_launches": 990, "unknown_launches": 0,
        "terminal": True, "reuse": False, "reset": False, "refund": False, "regrade": False,
    }
    return {
        "schema_version": "trigger-campaign-approval/v3", "manifest_sha256": digest,
        "launch_budget": 1302,
        "standing_authority": {
            "scope_id": "issue-573-full-trigger-qualification/v1",
            "approved_plan_sha256": "642d7fc3117118f4963c9583de8017662a95ff3698e31bea26dd4b851986ccc4",
            "recorder": "trusted-orchestrator", "session_id": session,
            "grant": grant_observation, "quota_directive": quota_observation,
            "reviewed_through": {
                "reviewer": "independent-reviewer", "review_id": "standing-review-789",
                "session_id": session, "reviewed_at": "2026-09-14T18:00:00.000Z",
                "latest_user": latest_observation,
                "reviewed_interval_sha256": campaign.json_digest(
                    [grant_observation, quota_observation, latest_observation]),
                "source_sha256": "a" * 64, "revocation_found": False,
            },
        },
        "campaign_exercise": {
            "scope_id": "issue-573-full-trigger-qualification/v1", "reviewed_manifest": manifest,
            "schedule": {"name": "serial", "workers": 1}, "case_count": 217,
            "trial_count": 3, "arm_count": 2, "launch_count": 1302,
            "review": {
                "reviewer": "independent-reviewer", "review_id": "manifest-review-012",
                "reviewed_at": "2026-09-14T18:05:00.000Z", "source_commit": "b" * 40,
                "source_tree_sha256": "c" * 64, "observer_sha256": manifest["identities"]["observer"],
                "manifest_sha256": digest, "launch_budget": 1302,
                "approved_plan_sha256": "642d7fc3117118f4963c9583de8017662a95ff3698e31bea26dd4b851986ccc4",
                "continuity_sha256": campaign.json_digest(continuity),
                "predecessor_sha256": campaign.json_digest(predecessor),
            },
            "continuity": continuity,
            "predecessor": predecessor,
            "constraints": {
                "campaign_count": 1, "automatic_retries": 0, "unknown_outcomes_charged": True,
                "available_quota_only": True, "quota_purchase": False, "quota_reset": False,
                "credit_redemption": False, "old_approval_reuse": False,
            },
        },
    }


def v4_approval(manifest, component):
    standing = standing_approval(manifest)["standing_authority"]
    source = component["source"]
    observer_binding = {"old": component["compatibility"]["old_observer_sha256"],
                        "new": component["compatibility"]["new_observer_sha256"],
                        "dual_replay": source["dual_replay"]}
    digest = campaign.json_digest(manifest)
    return {"schema_version": "trigger-campaign-approval/v4", "manifest_sha256": digest,
            "launch_budget": 891, "standing_authority": standing, "carry_forward_review": {
                "reviewer": "independent-reviewer", "review_id": "carry-forward-source-review",
                "reviewed_at": "2026-09-14T20:00:00.000Z", "source_commit": "b" * 40,
                "source_tree_sha256": "c" * 64, "manifest_sha256": digest, "launch_budget": 891,
                "approved_plan_sha256": standing["approved_plan_sha256"],
                "carry_forward_sha256": campaign.json_digest(component),
                "source_sha256": campaign.json_digest(source),
                "cohort_sha256": campaign.json_digest(component["cohort"]),
                "compatibility_sha256": campaign.json_digest(component["compatibility"]),
                "accounting_sha256": campaign.json_digest(component["accounting"]),
                "observer_closures_sha256": campaign.json_digest(observer_binding),
                "source_stability_review_sha256": source["source_stability_review"]["sha256"],
            }}


def v5_approval(manifest, component):
    standing = standing_approval(full_manifest(Path("/tmp/v5-logical-root")))["standing_authority"]
    digest = campaign.json_digest(manifest)
    review = {
        "reviewer": "independent-reviewer", "review_id": "multi-generation-review",
        "reviewed_at": "2026-09-14T20:00:00.000Z", "source_commit": "b" * 40,
        "source_tree_sha256": "c" * 64, "manifest_sha256": digest,
        "logical_manifest_sha256": campaign.json_digest(component["logical_manifest"]),
        "launch_budget": 651, "approved_plan_sha256": standing["approved_plan_sha256"],
        "carry_forward_sha256": campaign.json_digest(component),
        "histories_sha256": campaign.json_digest(component["histories"]),
        "accounting_sha256": campaign.json_digest(component["accounting"]),
        "observer_replays_sha256": campaign.json_digest(component["observer_replays"]),
    }
    return {"schema_version": "trigger-campaign-approval/v5", "manifest_sha256": digest,
            "launch_budget": 651, "standing_authority": standing,
            "carry_forward_review": review}


class MultiGenerationApprovalTests(unittest.TestCase):
    def test_v5_binds_subset_manifest_and_full_multi_generation_plan(self):
        logical = full_manifest(Path("/tmp/v5-logical-root"))
        manifest = copy.deepcopy(logical)
        manifest["arms"] = ["candidate"]
        manifest["output_directory"] = "/tmp/v5-fresh-root"
        component = {
            "schema_version": "trigger-case-carry-forward/v2",
            "logical_manifest": logical,
            "histories": [{"generation_id": name} for name in ("original", "failed-c2", "recovery")],
            "observer_replays": [{"observer_sha256": logical["identities"]["observer"]}],
            "accounting": {"historical_charged_launches": 660, "carried_trials": 651,
                           "fresh_launch_ceiling": 651, "maximum_total_charged_attempts": 1311,
                           "invalid_launches": 9, "logical_full_trials": 1302},
        }
        record = v5_approval(manifest, component)
        campaign.validate_approval(record, campaign.json_digest(manifest), 651,
                                   carry_forward=component)

        smuggled = {**component, "schema_version": "trigger-case-carry-forward/v1"}
        with self.assertRaisesRegex(ValueError, "requires its reviewed V2"):
            campaign.validate_approval(record, campaign.json_digest(manifest), 651,
                                       carry_forward=smuggled)

        legacy = standing_approval(logical)
        with self.assertRaises(ValueError):
            campaign.validate_approval(legacy, campaign.json_digest(manifest), 651,
                                       carry_forward=component)
        legacy_component = {
            "source": {"source_stability_review": {"sha256": "d" * 64},
                       "dual_replay": {"path": "dual.json", "sha256": "e" * 64}},
            "cohort": {}, "compatibility": {"old_observer_sha256": "1" * 64,
                                                "new_observer_sha256": "2" * 64},
            "accounting": {},
        }
        legacy_v4 = v4_approval(manifest, legacy_component)
        with self.assertRaisesRegex(ValueError, "fresh ceiling"):
            campaign.validate_approval(legacy_v4, campaign.json_digest(manifest), 651,
                                       carry_forward=legacy_component)
        for field in ("histories_sha256", "accounting_sha256", "observer_replays_sha256"):
            changed = copy.deepcopy(record)
            changed["carry_forward_review"][field] = "f" * 64
            with self.subTest(field=field), self.assertRaises(ValueError):
                campaign.validate_approval(changed, campaign.json_digest(manifest), 651,
                                           carry_forward=component)


class CarryForwardTests(unittest.TestCase):
    def test_v4_extends_standing_authority_without_fabricated_confirmation(self):
        manifest = full_manifest(Path("/tmp/new-carry-root"))
        component = {"source": {"source_stability_review": {"sha256": "d" * 64},
                                "dual_replay": {"path": "dual.json", "sha256": "e" * 64}},
                     "cohort": {}, "compatibility": {"old_observer_sha256": "1" * 64,
                                                       "new_observer_sha256": "2" * 64},
                     "accounting": {}}
        record = v4_approval(manifest, component)
        self.assertNotIn("source", record)
        campaign.validate_approval(record, campaign.json_digest(manifest), 891,
                                   carry_forward=component)

    def test_v4_rejects_unreviewed_lineage_and_boolean_budget(self):
        manifest = full_manifest(Path("/tmp/new-carry-root"))
        component = {"source": {"source_stability_review": {"sha256": "d" * 64},
                                "dual_replay": {"path": "dual.json", "sha256": "e" * 64}},
                     "cohort": {}, "compatibility": {"old_observer_sha256": "1" * 64,
                                                       "new_observer_sha256": "2" * 64},
                     "accounting": {}}
        record = v4_approval(manifest, component)
        for changed in ({**record, "launch_budget": True},
                        {**record, "carry_forward_review": {**record["carry_forward_review"],
                                                            "cohort_sha256": "f" * 64}}):
            with self.assertRaises(ValueError):
                campaign.validate_approval(changed, campaign.json_digest(manifest), 891,
                                           carry_forward=component)


class CampaignTests(unittest.TestCase):
    def test_self_asserted_approval_is_not_authority(self):
        with self.assertRaises(ValueError):
            campaign.validate_approval({"approved": True}, "a" * 64, 6)
        campaign.validate_approval(approval(), "a" * 64, 6)
        for field, value in (("role", "assistant"), ("content", "approved"), ("message_id", "")):
            record = approval()
            record["source"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                campaign.validate_approval(record, "a" * 64, 6)

    def test_contextual_v2_accepts_only_narrow_whole_response_affirmatives(self):
        for response in ("approved", " Approved. ", "YES!", "authorized, please proceed.",
                         "I approve. Please finish the goal!", "Approved, finish the goal."):
            with self.subTest(response=response):
                campaign.validate_approval(contextual_approval(response=response), "a" * 64, 6)

        for response in ("unapproved", '"approved"', "say approved", "not approved", "no, approved",
                         "approved?", "approved if the tests pass", "I approve unless the budget changes",
                         "if everything matches, I approve", "I would approve", "maybe approved",
                         "approved, but not yet", "approved. cancel it", "approved. I revoke approval",
                         "approved. no"):
            with self.subTest(response=response), self.assertRaises(ValueError):
                campaign.validate_approval(contextual_approval(response=response), "a" * 64, 6)

    def test_contextual_v2_rejects_malformed_provenance_binding_and_sequence(self):
        valid = contextual_approval()
        cases = []

        def changed(label, *path_and_value):
            value = copy.deepcopy(valid)
            target = value
            *path, replacement = path_and_value
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = replacement
            cases.append((label, value))

        changed("wrong top-level manifest", "manifest_sha256", "b" * 64)
        changed("wrong top-level budget", "launch_budget", 9)
        changed("bool top-level budget", "launch_budget", True)
        changed("untrusted recorder", "recorder_observation", "observer", "assistant")
        changed("request role", "recorder_observation", "request", "role", "user")
        changed("response role", "recorder_observation", "response", "role", "assistant")
        changed("empty request id", "recorder_observation", "request", "message_id", "")
        changed("equal message ids", "recorder_observation", "response", "message_id", "assistant-message-123")
        changed("different session", "recorder_observation", "response", "session_id", "another-session")
        changed("bool ordinal", "recorder_observation", "response", "source_ordinal", True)
        changed("equal ordinal", "recorder_observation", "response", "source_ordinal", 100)
        changed("reversed ordinal", "recorder_observation", "response", "source_ordinal", 99)
        changed("equal timestamp", "recorder_observation", "response", "timestamp", "2026-09-14T16:00:00.000Z")
        changed("reversed timestamp", "recorder_observation", "response", "timestamp", "2026-09-14T15:59:59.000Z")
        changed("malformed timestamp", "recorder_observation", "response", "timestamp", "later")
        changed("changed content", "recorder_observation", "response", "content", "yes")
        changed("bad content hash", "recorder_observation", "request", "content_sha256", "0" * 64)
        changed("bad source-line hash", "recorder_observation", "response", "source_line_sha256", True)
        changed("nonadjacent sequence", "recorder_observation", "adjacent_user_visible_message_ids",
                ["assistant-message-123", "intervening-message", "user-message-456"])
        changed("reversed adjacency", "recorder_observation", "adjacent_user_visible_message_ids",
                ["user-message-456", "assistant-message-123"])
        changed("competing request", "recorder_observation", "adjacent_user_visible_message_ids",
                ["competing-assistant-request", "user-message-456"])
        for label, record in cases:
            with self.subTest(label=label), self.assertRaises(ValueError):
                campaign.validate_approval(record, "a" * 64, 6)

        canonical = f"Approve trigger campaign {'a' * 64} with launch budget 6."
        for label, content in (
            ("wrong request manifest", f"Approve trigger campaign {'b' * 64} with launch budget 6."),
            ("wrong request budget", f"Approve trigger campaign {'a' * 64} with launch budget 9."),
            ("appended competing request", canonical + "\n" +
             f"Approve trigger campaign {'b' * 64} with launch budget 6."),
        ):
            record = contextual_approval()
            request = record["recorder_observation"]["request"]
            request["content"] = content
            request["content_sha256"] = hashlib.sha256(content.encode()).hexdigest()
            with self.subTest(label=label), self.assertRaisesRegex(
                    ValueError, "request does not bind the exact manifest and launch budget"):
                campaign.validate_approval(record, "a" * 64, 6)
        with self.assertRaises(ValueError):
            campaign.validate_approval(valid, "a" * 64, True)

    def test_contextual_v2_entire_record_is_immutable_ledger_authorization(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "ledger.sqlite3"
            record = contextual_approval()
            ledger = campaign.CampaignLedger(path, "a" * 64, record, 6)
            ledger.reserve_case("candidate", "case-one")
            resumed = campaign.CampaignLedger(path, "a" * 64, copy.deepcopy(record), 6)
            with self.assertRaises(ValueError):
                resumed.require_reconciled()

            changed = contextual_approval(response="yes")
            with self.assertRaisesRegex(ValueError, "ledger authorization is immutable"):
                campaign.CampaignLedger(path, "a" * 64, changed, 6)
            with self.assertRaises(ValueError):
                campaign.CampaignLedger(path, "b" * 64, contextual_approval("b" * 64), 6)

            ledger.finish_case("candidate", "case-one", "invalid")
            campaign.CampaignLedger(path, "a" * 64, record, 6).require_reconciled()
            with self.assertRaises(ValueError):
                ledger.reserve_case("candidate", "case-one")

    def test_standing_v3_accepts_only_genuine_closed_grant_and_existing_quota_shapes(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = full_manifest(Path(temp) / "new-campaign")
            record = standing_approval(manifest)
            campaign.validate_approval(record, campaign.json_digest(manifest), 1302)
            alternate = standing_approval(
                manifest, grant="listen, i approve everything that blocks or could block this goal from being achieved!",
                quota="Run until the quota is run out.")
            campaign.validate_approval(alternate, campaign.json_digest(manifest), 1302)

    def test_standing_v3_rejects_fake_mismatched_revoked_or_extra_authority(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = full_manifest(Path(temp) / "new-campaign")
            valid = standing_approval(manifest)
            cases = []

            def changed(label, *path_and_value):
                value = copy.deepcopy(valid)
                target = value
                *path, replacement = path_and_value
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = replacement
                cases.append((label, value))

            changed("assistant grant", "standing_authority", "grant", "role", "assistant")
            changed("mismatched session", "standing_authority", "quota_directive", "session_id", "other")
            changed("bad retained hash", "standing_authority", "grant", "content_sha256", "0" * 64)
            changed("bool ordinal", "standing_authority", "quota_directive", "source_ordinal", True)
            changed("reversed sequence", "standing_authority", "quota_directive", "source_ordinal", 6000)
            changed("revoked", "standing_authority", "reviewed_through", "revocation_found", True)
            changed("mismatched endpoint", "standing_authority", "reviewed_through", "latest_user", "session_id", "other")
            changed("stale endpoint", "standing_authority", "reviewed_through", "latest_user", "source_ordinal", 20000)
            changed("stale review", "standing_authority", "reviewed_through", "reviewed_at", "2026-09-14T17:00:00.000Z")
            changed("untrusted recorder", "standing_authority", "recorder", "assistant")
            changed("untrusted reviewer", "standing_authority", "reviewed_through", "reviewer", "orchestrator")
            extra = copy.deepcopy(valid)
            extra["standing_authority"]["scope_approved"] = True
            cases.append(("unknown extra", extra))
            for label, record in cases:
                with self.subTest(label=label), self.assertRaises(ValueError):
                    campaign.validate_approval(record, campaign.json_digest(manifest), 1302)

            denied = standing_approval(manifest, latest="I revoke my approval.")
            with self.assertRaisesRegex(ValueError, "explicitly revokes or denies"):
                campaign.validate_approval(denied, campaign.json_digest(manifest), 1302)

            for label, field, content in (
                ("quoted grant", "grant", '"I approve everything needed to finish this goal."'),
                ("relabeled annotation", "grant",
                 "approved and stop asking me for approvals. I approve everything needed to finish this goal"),
                ("copied request", "grant", "Approve trigger campaign deadbeef with launch budget 1302."),
                ("conditional grant", "grant", "If nothing changes, I approve everything needed to finish this goal."),
                ("denied grant", "grant", "I do not approve everything needed to finish this goal."),
                ("limited quota", "quota_directive", "run until the quota is run out unless it takes too long"),
                ("reversed quota", "quota_directive", "run until the quota is run out; stop now"),
            ):
                record = standing_approval(manifest)
                observed = record["standing_authority"][field]
                observed["content"] = content
                observed["content_sha256"] = hashlib.sha256(content.encode()).hexdigest()
                with self.subTest(label=label), self.assertRaises(ValueError):
                    campaign.validate_approval(record, campaign.json_digest(manifest), 1302)

    def test_standing_v3_rejects_manifest_budget_scope_or_continuity_disagreement(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = full_manifest(Path(temp) / "new-campaign")
            valid = standing_approval(manifest)
            cases = []

            def changed(label, *path_and_value):
                value = copy.deepcopy(valid)
                target = value
                *path, replacement = path_and_value
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = replacement
                cases.append((label, value))

            changed("wrong digest", "manifest_sha256", "e" * 64)
            changed("wrong budget", "launch_budget", 1301)
            changed("bool budget", "launch_budget", True)
            changed("wrong scope", "campaign_exercise", "scope_id", "another-scope")
            changed("parallel schedule", "campaign_exercise", "schedule", "workers", 2)
            changed("wrong case count", "campaign_exercise", "case_count", 216)
            changed("wrong launch count", "campaign_exercise", "launch_count", 1296)
            changed("changed manifest", "campaign_exercise", "reviewed_manifest", "threshold", 0.6)
            changed("wrong plan binding", "campaign_exercise", "review", "approved_plan_sha256", "f" * 64)
            wrong_plan = copy.deepcopy(valid)
            wrong_plan["standing_authority"]["approved_plan_sha256"] = "f" * 64
            wrong_plan["campaign_exercise"]["review"]["approved_plan_sha256"] = "f" * 64
            cases.append(("wrong consistent plan binding", wrong_plan))
            changed("wrong observer binding", "campaign_exercise", "review", "observer_sha256", "f" * 64)
            changed("wrong continuity digest", "campaign_exercise", "review", "continuity_sha256", "f" * 64)
            changed("changed experiment", "campaign_exercise", "continuity", "result", "changed")
            changed("old manifest reused", "campaign_exercise", "predecessor", "manifest_sha256",
                    campaign.json_digest(manifest))
            changed("old output reused", "campaign_exercise", "predecessor", "output_directory",
                    manifest["output_directory"])
            changed("old budget incomplete", "campaign_exercise", "predecessor", "unreserved_launches", 989)
            changed("old ledger reused", "campaign_exercise", "predecessor", "reuse", True)
            changed("quota purchase", "campaign_exercise", "constraints", "quota_purchase", True)
            for label, record in cases:
                with self.subTest(label=label), self.assertRaises(ValueError):
                    campaign.validate_approval(record, campaign.json_digest(manifest), 1302)

    def test_standing_v3_entire_record_is_immutable_ledger_authorization(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = full_manifest(root / "new-campaign")
            digest = campaign.json_digest(manifest)
            record = standing_approval(manifest)
            path = root / "ledger.sqlite3"
            campaign.CampaignLedger(path, digest, record, 1302)
            campaign.CampaignLedger(path, digest, copy.deepcopy(record), 1302)
            changed = copy.deepcopy(record)
            changed["standing_authority"]["reviewed_through"]["source_sha256"] = "e" * 64
            with self.assertRaisesRegex(ValueError, "ledger authorization is immutable"):
                campaign.CampaignLedger(path, digest, changed, 1302)

    def test_atomic_reservations_persist_and_never_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "ledger.sqlite3"
            ledger = campaign.CampaignLedger(path, "a" * 64, approval(), 6)
            ledger.reserve_case("candidate", "case-one")
            ledger.finish_case("candidate", "case-one", "complete")
            resumed = campaign.CampaignLedger(path, "a" * 64, approval(), 6)
            with self.assertRaises(ValueError):
                resumed.reserve_case("candidate", "case-one")
            resumed.reserve_case("candidate", "case-two")
            with self.assertRaises(ValueError):
                resumed.reserve_case("candidate", "case-three")
            self.assertEqual(resumed.snapshot()["reserved_launches"], 6)
            self.assertEqual(resumed.snapshot()["unknown_launches"], 3)

    def test_concurrent_reservation_cannot_overspend(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger = campaign.CampaignLedger(Path(temp) / "ledger.sqlite3", "a" * 64, approval(budget=3), 3)
            def reserve(key):
                try:
                    ledger.reserve_case("candidate", key)
                    return True
                except ValueError:
                    return False
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(reserve, ["first", "second"]))
            self.assertEqual(sum(results), 1)
            self.assertEqual(ledger.snapshot()["reserved_launches"], 3)

    def test_unknown_outcome_blocks_resume_until_read_only_reconciliation(self):
        with tempfile.TemporaryDirectory() as temp:
            ledger = campaign.CampaignLedger(Path(temp) / "ledger.sqlite3", "a" * 64, approval(), 6)
            ledger.reserve_case("candidate", "case-one")
            with self.assertRaises(ValueError):
                ledger.require_reconciled()
            ledger.finish_case("candidate", "case-one", "invalid")
            ledger.require_reconciled()
            with self.assertRaises(ValueError):
                ledger.reserve_case("candidate", "case-one")

    def test_ledger_cannot_change_manifest_budget_or_approval_on_resume(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "ledger.sqlite3"
            campaign.CampaignLedger(path, "a" * 64, approval(), 6)
            with self.assertRaises(ValueError):
                campaign.CampaignLedger(path, "b" * 64, approval("b" * 64), 6)
            with self.assertRaises(ValueError):
                campaign.CampaignLedger(path, "a" * 64, approval(budget=9), 9)

    def test_two_workers_need_measured_bound_profile(self):
        self.assertEqual(campaign.worker_limit(1, None, "a" * 64), 1)
        for workers in (True, 0, 3):
            with self.assertRaises(ValueError):
                campaign.worker_limit(workers, None, "a" * 64)
        with self.assertRaises(ValueError):
            campaign.worker_limit(2, {"qualified": True}, "a" * 64)



class CampaignDraftBindingTests(unittest.TestCase):
    """Committed freeze drafts must keep binding the shipped corpus.

    ``compare-trigger-evals.py validate`` is the launch-time gate, but nothing
    ran it over the drafts kept in the repository, so a corpus revision that
    landed after they were generated left both of them unable to validate
    against the inventory they name. Rebind them from the provider-free planner
    whenever the inventory changes; the freeze-time model, CLI, observer,
    catalog, fixture and description pins stay with the draft.
    """

    def test_committed_campaign_drafts_match_the_provider_free_planner(self):
        layer = ROOT / "layer2-trigger"
        inventory_path = layer / "case-inventory.json"
        inventory = load_inventory(inventory_path)
        drafts = {"issue-573-pilot.draft.json": "pilot", "issue-573-full.draft.json": "full"}
        for name, scope in sorted(drafts.items()):
            with self.subTest(draft=name):
                draft = json.loads((layer / "campaign-drafts" / name).read_bytes())
                plan = plan_inventory(inventory, layer, scope, inventory_path=inventory_path)
                cases = comparison.validate_inventory_binding(draft, inventory)
                self.assertEqual(len(cases), len(plan["roster"]))
                for field in ("roster", "corpus_sha256", "inventory_sha256", "arms",
                              "trials", "threshold", "qualification_scope"):
                    self.assertEqual(draft[field], plan[field], field)
                self.assertEqual(draft["launch_budget_requested"], plan["launch_count"])


if __name__ == "__main__":
    suite = unittest.TestSuite([
        unittest.defaultTestLoader.loadTestsFromTestCase(CampaignTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(MultiGenerationApprovalTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(CarryForwardTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(CampaignDraftBindingTests),
    ])
    raise SystemExit(run_counted(suite, label="test-trigger-campaign"))
