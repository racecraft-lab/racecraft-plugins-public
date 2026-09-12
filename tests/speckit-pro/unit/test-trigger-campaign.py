#!/usr/bin/env python3
"""Campaign budgets and recovery without native providers."""
from __future__ import annotations

import concurrent.futures
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lib"))
import trigger_campaign as campaign
from test_result import run_counted


def approval(digest="a" * 64, budget=6):
    return {"schema_version": "trigger-campaign-approval/v1", "manifest_sha256": digest,
            "launch_budget": budget, "source": {"role": "user", "message_id": "user-message-123",
                "content": f"Approve trigger campaign {digest} with launch budget {budget}."}}


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


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(CampaignTests), label="test-trigger-campaign"))
