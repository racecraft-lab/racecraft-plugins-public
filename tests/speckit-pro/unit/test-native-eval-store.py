#!/usr/bin/env python3
"""Immutable native trial receipts preserve failures and reject stale evidence."""
from concurrent.futures import ThreadPoolExecutor
import copy
import json
from pathlib import Path
import tempfile
import sys
import types
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from test_result import run_counted
from native_eval_store import RunStore, StoreError, _fsync_directory, digest


ROW = {"case_id": "case.one", "host": "claude", "mode": "plugin", "trial": 1}
INPUT = "a" * 64
GRADER = "b" * 64
PAIR_INPUT = "d" * 64
PAIR_GRADER = "e" * 64
OBS = {"completed": True, "error": None, "final_text": "done"}


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "run"

    def captured(self, store):
        attempt = store.reserve(ROW, INPUT)
        raw = attempt / "trace.jsonl"
        raw.write_text('{"type":"result"}\n')
        store.capture(attempt, observation=OBS, error=None, evidence={"trace": raw})
        return attempt

    def graded_arm(self, store, host, mode, seed):
        row = {"case_id": "case.one", "host": host, "mode": mode, "trial": 1}
        attempt = store.reserve(row, seed * 64)
        raw = attempt / "trace.jsonl"
        raw.write_text('{"type":"result"}\n')
        observation = {**OBS, "artifacts": {"workflow.md": host}}
        store.capture(attempt, observation=observation, error=None, evidence={"trace": raw})
        grader = chr(ord(seed) + 2) * 64
        store.grade(attempt, grader, {"status": "pass", "checks": []})
        return store.pair_arm(attempt, grader)

    def rewrite_receipt(self, path, mutate):
        envelope = json.loads(path.read_text())
        mutate(envelope["payload"])
        envelope["sha256"] = digest(envelope["payload"])
        path.write_text(json.dumps(envelope))

    def test_resume_reuses_pass_without_reserving_or_scanning_again(self):
        with RunStore(self.root) as store:
            attempt = self.captured(store)
            store.grade(attempt, GRADER, {"status": "pass", "checks": []})
        with RunStore(self.root) as store:
            self.assertEqual(store.lookup(ROW, INPUT, GRADER)["status"], "pass")
            with self.assertRaises(StoreError):
                store.reserve(ROW, INPUT)
            self.assertEqual(len(store.attempts), 1)

    def test_failures_are_preserved_and_only_explicitly_retried(self):
        with RunStore(self.root) as store:
            first = self.captured(store)
            store.grade(first, GRADER, {"status": "fail", "checks": []})
            with self.assertRaises(StoreError):
                store.reserve(ROW, INPUT)
            second = store.reserve(ROW, INPUT, retry=True)
            self.assertNotEqual(first, second)
            self.assertTrue((first / "capture.json").is_file())
            self.assertEqual(store.lookup(ROW, INPUT, GRADER)["status"], "incomplete")

    def test_change_grader_regrades_capture_without_subject_retry(self):
        with RunStore(self.root) as store:
            attempt = self.captured(store)
            store.grade(attempt, GRADER, {"status": "pass", "checks": []})
        with RunStore(self.root) as store:
            found = store.lookup(ROW, INPUT, "c" * 64)
            self.assertEqual(found["status"], "needs_grade")
            self.assertEqual(found["capture"]["observation"], OBS)
            store.grade(found["attempt"], "c" * 64, {"status": "fail", "checks": []})
            self.assertEqual(len(store.attempts), 1)

    def test_changed_runtime_is_new_trial_identity(self):
        with RunStore(self.root) as store:
            self.captured(store)
            self.assertEqual(store.lookup(ROW, "d" * 64, GRADER)["status"], "not_run")
            store.reserve(ROW, "d" * 64)
            self.assertEqual(len(store.attempts), 2)

    def test_output_before_grade_survives_interruption(self):
        with RunStore(self.root) as store:
            self.captured(store)
        with RunStore(self.root) as store:
            self.assertEqual(store.lookup(ROW, INPUT, GRADER)["status"], "needs_grade")

    def test_incomplete_launch_is_not_automatically_repeated(self):
        with RunStore(self.root) as store:
            store.reserve(ROW, INPUT)
        with RunStore(self.root) as store:
            self.assertEqual(store.lookup(ROW, INPUT, GRADER)["status"], "incomplete")
            with self.assertRaises(StoreError):
                store.reserve(ROW, INPUT)

    def test_concurrent_duplicate_reservations_have_one_winner(self):
        with RunStore(self.root) as store:
            def reserve(_):
                try:
                    return store.reserve(ROW, INPUT)
                except StoreError:
                    return None
            with ThreadPoolExecutor(max_workers=8) as workers:
                results = list(workers.map(reserve, range(16)))
            self.assertEqual(sum(value is not None for value in results), 1)

    def test_second_run_owner_is_rejected(self):
        with RunStore(self.root):
            with self.assertRaises(StoreError), RunStore(self.root):
                pass

    def test_mocked_windows_lock_backend_uses_one_nonblocking_byte(self):
        calls = []
        fake_msvcrt = types.SimpleNamespace(
            LK_NBLCK=7,
            LK_UNLCK=8,
            locking=lambda descriptor, mode, count: calls.append((descriptor, mode, count)),
        )
        with patch("native_eval_store.sys.platform", "win32"), patch.dict(sys.modules, {"msvcrt": fake_msvcrt}):
            with RunStore(self.root) as store:
                self.assertTrue((store.reserve(ROW, INPUT) / "reservation.json").is_file())
        self.assertEqual([call[1:] for call in calls], [(7, 1), (8, 1)])

    def test_windows_skips_directory_fsync_without_claiming_posix_durability(self):
        with patch("native_eval_store.sys.platform", "win32"), patch("native_eval_store.os.open") as open_directory:
            _fsync_directory(self.root)
        open_directory.assert_not_called()

    def test_failed_immutable_link_fails_closed(self):
        with RunStore(self.root) as store, patch("native_eval_store.os.link", side_effect=OSError("unsupported")):
            with self.assertRaises(StoreError):
                store.reserve(ROW, INPUT)

    def test_unsupported_platform_has_no_noop_owner_lock(self):
        with patch("native_eval_store.sys.platform", "unsupported"), patch("native_eval_store.os.name", "unsupported"):
            with self.assertRaises(StoreError):
                RunStore(self.root).__enter__()

    def test_capture_and_grade_cannot_be_overwritten(self):
        with RunStore(self.root) as store:
            attempt = self.captured(store)
            with self.assertRaises(StoreError):
                store.capture(attempt, observation=OBS, error=None, evidence={"trace": attempt / "trace.jsonl"})
            store.grade(attempt, GRADER, {"status": "pass", "checks": []})
            with self.assertRaises(StoreError):
                store.grade(attempt, GRADER, {"status": "fail", "checks": []})

    def test_grade_evidence_is_immutable_confined_and_returned(self):
        with RunStore(self.root) as store:
            attempt = self.captured(store)
            judge_dir = attempt / GRADER
            judge_dir.mkdir()
            request = judge_dir / "request.json"
            request.write_text('{"judge":"request"}')
            store.grade(attempt, GRADER, {"status": "pass", "checks": []}, evidence={"request": request})
            found = store.lookup(ROW, INPUT, GRADER)
            self.assertEqual(found["grade_evidence"]["request"]["path"], f"{GRADER}/request.json")
            with self.assertRaises(StoreError):
                store.grade(attempt, GRADER, {"status": "pass", "checks": []}, evidence={"request": request})
        request.write_text('{"judge":"changed"}')
        with self.assertRaises(StoreError), RunStore(self.root):
            pass

    def test_grade_evidence_rejects_empty_and_unsafe_references(self):
        outside = Path(self.temp.name) / "judge.json"
        outside.write_text("outside")
        with RunStore(self.root) as store:
            attempt = self.captured(store)
            for evidence in ({}, {"request": outside}):
                with self.subTest(evidence=evidence), self.assertRaises(StoreError):
                    store.grade(attempt, GRADER, {"status": "pass", "checks": []}, evidence=evidence)

    def test_pair_receipt_binds_arms_grader_and_judge_evidence_across_resume(self):
        with RunStore(self.root) as store:
            arms = [self.graded_arm(store, "claude", "plugin", "a"),
                    self.graded_arm(store, "codex", "project", "b")]
            pair_dir = store.pair_reserve(PAIR_INPUT, arms)
            grade_dir = pair_dir / "grades" / PAIR_GRADER
            grade_dir.mkdir(parents=True)
            request = grade_dir / "judge-request.json"
            request.write_text('{"request":true}\n')
            store.pair_grade(PAIR_INPUT, PAIR_GRADER, arms,
                             {"status": "fail", "checks": []}, evidence={"request": request})
            found = store.pair_lookup(PAIR_INPUT, PAIR_GRADER, arms)
            self.assertEqual(found["status"], "fail")
            self.assertEqual(found["grade_evidence"]["request"]["path"],
                             f"grades/{PAIR_GRADER}/judge-request.json")
            self.assertEqual(store.pair_lookup(PAIR_INPUT, "f" * 64, arms)["status"],
                             "needs_grade")
        with RunStore(self.root) as store:
            self.assertEqual(store.pair_lookup(PAIR_INPUT, PAIR_GRADER, arms)["status"], "fail")
        request.write_text('{"request":false}\n')
        with self.assertRaises(StoreError), RunStore(self.root):
            pass

    def test_pair_store_rejects_missing_swapped_and_overwrite_transitions(self):
        with RunStore(self.root) as store:
            arms = [self.graded_arm(store, "claude", "plugin", "a"),
                    self.graded_arm(store, "codex", "project", "b")]
            for malformed in (arms[:1], list(reversed(arms))):
                with self.subTest(malformed=malformed), self.assertRaises(StoreError):
                    store.pair_reserve(PAIR_INPUT, malformed)
            store.pair_reserve(PAIR_INPUT, arms)
            store.pair_grade(PAIR_INPUT, PAIR_GRADER, arms,
                             {"status": "pass", "checks": []})
            with self.assertRaises(StoreError):
                store.pair_grade(PAIR_INPUT, PAIR_GRADER, arms,
                                 {"status": "fail", "checks": []})
        pair_grade = self.root / "pairs" / PAIR_INPUT / f"grade-{PAIR_GRADER}.json"
        self.rewrite_receipt(pair_grade, lambda payload: payload.update(input="9" * 64))
        with self.assertRaises(StoreError), RunStore(self.root):
            pass

    def test_published_values_are_detached_from_mutable_callers(self):
        row = copy.deepcopy(ROW)
        observation = copy.deepcopy(OBS)
        verdict = {"status": "pass", "checks": []}
        with RunStore(self.root) as store:
            attempt = store.reserve(row, INPUT)
            raw = attempt / "trace.jsonl"
            raw.write_text('{"type":"result"}\n')
            store.capture(attempt, observation=observation, error=None, evidence={"trace": raw})
            store.grade(attempt, GRADER, verdict)
            row["case_id"] = "changed"
            observation["final_text"] = "changed"
            verdict["status"] = "fail"
            found = store.lookup(ROW, INPUT, GRADER)
            self.assertEqual(found["capture"]["observation"], OBS)
            self.assertEqual(found["status"], "pass")
            self.assertEqual(store.attempts[attempt]["reservation"]["row"], ROW)
            found["capture"]["observation"]["final_text"] = "also changed"
            found["verdict"]["status"] = "fail"
            self.assertEqual(store.lookup(ROW, INPUT, GRADER)["status"], "pass")
            self.assertEqual(store.lookup(ROW, INPUT, GRADER)["capture"]["observation"], OBS)

    def test_invalid_capture_never_receives_behavioral_pass(self):
        with RunStore(self.root) as store:
            attempt = store.reserve(ROW, INPUT)
            raw = attempt / "stderr.txt"
            raw.write_text("quota exhausted")
            store.capture(attempt, observation=None, error="quota", evidence={"stderr": raw})
            self.assertEqual(store.lookup(ROW, INPUT, GRADER)["status"], "invalid")
            with self.assertRaises(StoreError):
                store.grade(attempt, GRADER, {"status": "pass", "checks": []})

    def test_resume_verifies_raw_bytes_and_refuses_tampering(self):
        with RunStore(self.root) as store:
            attempt = self.captured(store)
        (attempt / "trace.jsonl").write_text("altered")
        with self.assertRaises(StoreError), RunStore(self.root):
            pass

    def test_evidence_must_be_confined_regular_file(self):
        outside = Path(self.temp.name) / "outside.txt"
        outside.write_text("outside")
        with RunStore(self.root) as store:
            attempt = store.reserve(ROW, INPUT)
            link = attempt / "link"
            link.symlink_to(outside)
            for path in (outside, link):
                with self.subTest(path=path), self.assertRaises(StoreError):
                    store.capture(attempt, observation=OBS, error=None, evidence={"trace": path})

    def test_bad_identity_and_duplicate_receipts_fail_closed(self):
        with RunStore(self.root) as store:
            for fingerprint in ("", "not-a-hash"):
                with self.assertRaises(StoreError):
                    store.reserve(ROW, fingerprint)
            for trial in (0, True):
                with self.assertRaises(StoreError):
                    store.reserve({**ROW, "trial": trial}, INPUT)

    def test_malformed_stored_record_shapes_fail_closed(self):
        for receipt in ("reservation", "grade"):
            with self.subTest(receipt=receipt):
                root = Path(self.temp.name) / receipt
                with RunStore(root) as store:
                    attempt = self.captured(store)
                    if receipt == "grade":
                        store.grade(attempt, GRADER, {"status": "pass", "checks": []})
                path = attempt / ("reservation.json" if receipt == "reservation" else f"grade-{GRADER}.json")
                self.rewrite_receipt(path, lambda payload: payload.update(unrecognized=True))
                with self.assertRaises(StoreError), RunStore(root):
                    pass

    def test_attempt_directory_identity_is_validated(self):
        with RunStore(self.root) as store:
            attempt = self.captured(store)
        malformed = attempt.with_name("not-an-attempt-id")
        attempt.rename(malformed)
        with self.assertRaises(StoreError), RunStore(self.root):
            pass

    def test_raw_reference_types_do_not_coerce_during_resume(self):
        with RunStore(self.root) as store:
            attempt = store.reserve(ROW, INPUT)
            raw = attempt / "empty.jsonl"
            raw.write_bytes(b"")
            store.capture(attempt, observation=OBS, error=None, evidence={"trace": raw})
        self.rewrite_receipt(
            attempt / "capture.json",
            lambda payload: payload["evidence"]["trace"].update(bytes=False),
        )
        with self.assertRaises(StoreError), RunStore(self.root):
            pass

    def test_raw_evidence_cannot_change_while_capture_is_hashing(self):
        with RunStore(self.root) as store:
            attempt = store.reserve(ROW, INPUT)
            raw = attempt / "trace.jsonl"
            raw.write_bytes(b"old")
            from native_eval_store import hashlib as store_hashlib
            original = store_hashlib.file_digest

            def mutate_after_hash(stream, algorithm):
                value = original(stream, algorithm)
                raw.write_bytes(b"changed")
                return value

            with patch("native_eval_store.hashlib.file_digest", side_effect=mutate_after_hash):
                with self.assertRaises(StoreError):
                    store.capture(attempt, observation=OBS, error=None, evidence={"trace": raw})


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(StoreTests), label="test-native-eval-store"))
