#!/usr/bin/env python3
"""Phase envelope contract and runner re-verification through the public helper dispatch seam."""
from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO / "speckit-pro"), str(REPO / "tests/speckit-pro/lib")]
from speckit_pro_runner.envelope import parse_request  # noqa: E402
from speckit_pro_runner.helpers import phase_envelope  # noqa: E402
from speckit_pro_runner.helpers.registry import HELPERS, dispatch_helper  # noqa: E402
from speckit_pro_runner.runtime import handle_request  # noqa: E402
from test_result import run_counted  # noqa: E402

FEATURE = "specs/example"
WORKFLOW = "docs/workflow.md"


def good_envelope(**fields):
    envelope = {
        "schema_version": "phase-envelope/v1", "phase": "Specify", "status": "pass",
        "next_action": "Run the Clarify phase.", "artifacts": [f"{FEATURE}/spec.md"],
        "gates": [{"id": "G1", "result": "pass"}], "counts": {"markers": 0},
        "blocker": "", "usage": {"input_tokens": 1200, "output_tokens": 300, "tool_calls": 9},
    }
    envelope.update(fields)
    return envelope


@contextmanager
def project(spec_text="# Spec\n\nNo open questions.\n"):
    """A throwaway Spec Kit project, so verification never reads this repository's own specs."""
    # The project sits inside an owned outer directory, so a test can place an outside file next to it safely.
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory).resolve() / "project"
        root.mkdir()
        (root / ".specify").mkdir()
        (root / FEATURE).mkdir(parents=True)
        (root / "docs").mkdir()
        (root / WORKFLOW).write_text("# Workflow\n", encoding="utf-8")
        (root / FEATURE / "spec.md").write_text(spec_text, encoding="utf-8")
        previous = Path.cwd()
        os.chdir(root)
        try:
            yield root
        finally:
            os.chdir(previous)


def verify(envelope, **inputs):
    request = SimpleNamespace(helper_id="verify-phase-envelope", operation="verify-phase-envelope", mode="read_only",
                              request_id=None, inputs={"envelope": envelope, "workflow_file": WORKFLOW,
                                                       "feature_dir": FEATURE, **inputs})
    return dispatch_helper(request)


def mismatch(result):
    return result["data"]["mismatch"]["code"]


class EnvelopeContractTests(unittest.TestCase):
    def test_a_complete_envelope_is_accepted(self):
        self.assertEqual(phase_envelope.envelope_failures(good_envelope()), [])

    def test_every_missing_field_is_rejected(self):
        for field in good_envelope():
            envelope = good_envelope()
            del envelope[field]
            with self.subTest(field=field):
                failures = phase_envelope.envelope_failures(envelope)
                self.assertTrue(failures)
                self.assertIn(field, json.dumps(failures))

    def test_an_envelope_over_the_byte_cap_is_rejected(self):
        padded = good_envelope(artifacts=[f"{FEATURE}/{'a' * 150}-{index}.md" for index in range(16)])
        size = len(json.dumps(padded, separators=(",", ":")).encode())
        self.assertGreater(size, phase_envelope.ENVELOPE_LIMIT_BYTES, "fixture must exceed the cap")
        failures = phase_envelope.envelope_failures(padded)
        self.assertEqual(failures[0]["rule"], "packet.schema.size")
        # The cap bounds multibyte text by encoded bytes, not characters.
        wide = good_envelope(blocker="é" * 240)
        self.assertEqual(phase_envelope.envelope_failures(wide), [])
        self.assertEqual(phase_envelope.envelope_failures(good_envelope(next_action="x" * 5000))[0]["rule"], "packet.schema.size")

    def test_unknown_fields_and_wrong_types_are_rejected(self):
        for label, envelope in (
            ("extra field", good_envelope(extra=1)),
            ("unknown phase", good_envelope(phase="Implement")),
            ("unknown status", good_envelope(status="done")),
            ("negative count", good_envelope(counts={"markers": -1})),
            ("blocker too long", good_envelope(blocker="x" * 241)),
            ("empty next action", good_envelope(next_action="")),
            ("gate without result", good_envelope(gates=[{"id": "G1"}])),
            ("unknown gate id", good_envelope(gates=[{"id": "G9", "result": "pass"}])),
            ("no gates", good_envelope(gates=[])),
            ("usage missing a counter", good_envelope(usage={"input_tokens": 1})),
        ):
            with self.subTest(label):
                self.assertTrue(phase_envelope.envelope_failures(envelope))

    def test_a_non_object_envelope_is_rejected(self):
        rejected = [phase_envelope.envelope_failures(value) != [] for value in (None, [], "text", 3)]
        self.assertEqual(rejected, [True] * 4)


class SourceEvidenceTests(unittest.TestCase):
    """The gate's source files must be readable and valid whatever the driver lists as changed."""

    def test_an_analyze_pass_over_absent_planning_files_fails(self):
        with project() as root:
            (root / FEATURE / "spec.md").unlink()
            (root / WORKFLOW).write_text("| Severity | Resolution |\n| --- | --- |\n", encoding="utf-8")
            envelope = good_envelope(phase="Analyze", artifacts=[], gates=[{"id": "G6", "result": "pass"}], counts={"markers": 0})
            result = verify(envelope)
        self.assertEqual(result["status"], "expected_failure")
        self.assertEqual(mismatch(result), "gate_evidence_missing")

    def test_invalid_utf8_source_evidence_fails_even_when_listed_or_unlisted(self):
        for artifacts in ([], [f"{FEATURE}/spec.md"]):
            with self.subTest(artifacts=artifacts), project() as root:
                (root / FEATURE / "spec.md").write_bytes(b"\xff")
                result = verify(good_envelope(artifacts=artifacts))
                self.assertEqual(result["status"], "expected_failure")
                self.assertIn(mismatch(result), ("gate_evidence_unparseable", "artifact_missing"))

    def test_an_empty_source_file_fails(self):
        with project() as root:
            (root / FEATURE / "spec.md").write_bytes(b"")
            self.assertEqual(mismatch(verify(good_envelope(artifacts=[]))), "gate_evidence_missing")

    def checklist_project(self, root, report=b"clean report\n"):
        for name in ("spec.md", "plan.md"):
            (root / FEATURE / name).write_text("clean\n", encoding="utf-8")
        (root / FEATURE / "checklists").mkdir()
        (root / FEATURE / "checklists" / "domain.md").write_bytes(report)

    def checklist_envelope(self, artifacts):
        return good_envelope(phase="Checklist", artifacts=artifacts, gates=[{"id": "G4", "result": "pass"}], counts={"markers": 0})

    def test_a_corrupt_or_empty_checklist_report_fails_listed_or_not(self):
        report = f"{FEATURE}/checklists/domain.md"
        for label, content, artifacts in (("corrupt unlisted", b"\xff", []), ("corrupt listed", b"\xff", [report]),
                                          ("empty unlisted", b"", [])):
            with self.subTest(label), project() as root:
                self.checklist_project(root, content)
                result = verify(self.checklist_envelope(artifacts))
                self.assertEqual(result["status"], "expected_failure")
                self.assertIn(mismatch(result), ("gate_evidence_missing", "gate_evidence_unparseable"))

    def test_a_clean_checklist_report_still_passes(self):
        with project() as root:
            self.checklist_project(root)
            self.assertEqual(verify(self.checklist_envelope([]))["status"], "ok")

    def test_every_gate_source_must_be_valid_for_every_gate(self):
        # One corrupt byte in any file a gate reads fails that gate, whichever gate claims it.
        cases = [("Specify", "G1", ["spec.md"]), ("Clarify", "G2", ["spec.md"]), ("Plan", "G3", ["plan.md"]),
                 ("Tasks", "G5", ["tasks.md"]), ("Analyze", "G6", ["spec.md", "plan.md", "tasks.md", "docs/workflow.md"])]
        for phase, gate, files in cases:
            for name in files:
                with self.subTest(gate=gate, file=name), project() as root:
                    for clean in ("spec.md", "plan.md", "tasks.md"):
                        (root / FEATURE / clean).write_text("clean\n", encoding="utf-8")
                    target = root / name if name.startswith("docs/") else root / FEATURE / name
                    target.write_bytes(b"\xff")
                    envelope = good_envelope(phase=phase, artifacts=[], gates=[{"id": gate, "result": "pass"}], counts={})
                    self.assertEqual(mismatch(verify(envelope)), "gate_evidence_unparseable")
        with project() as root:
            (root / FEATURE / "tasks.md").write_bytes(b"\xff")
            envelope = good_envelope(artifacts=[], gates=[{"id": "G1", "result": "pass"}, {"id": "G7", "result": "pass"}], counts={})
            self.assertEqual(mismatch(verify(envelope)), "gate_evidence_unparseable")

    def test_an_empty_workflow_fails_every_gate_that_consults_it(self):
        # G3, G5 and G7 read the workflow for the formal checkpoint, where an empty file disables it.
        cases = [("Plan", ["G3"]), ("Tasks", ["G5"]), ("Specify", ["G1", "G7"])]
        for phase, gates in cases:
            with self.subTest(gates=gates), project() as root:
                for clean in ("spec.md", "plan.md", "tasks.md"):
                    (root / FEATURE / clean).write_text("clean\n", encoding="utf-8")
                (root / WORKFLOW).write_bytes(b"")
                envelope = good_envelope(phase=phase, artifacts=[], gates=[{"id": gate, "result": "pass"} for gate in gates], counts={})
                self.assertEqual(mismatch(verify(envelope)), "gate_evidence_missing")

    def test_an_empty_artifact_directory_fails(self):
        with project() as root:
            (root / FEATURE / "checklists").mkdir()
            result = verify(good_envelope(artifacts=[f"{FEATURE}/checklists"]))
        self.assertEqual(mismatch(result), "artifact_missing")


class ReverifyTests(unittest.TestCase):
    def test_matching_evidence_passes_with_a_compact_answer(self):
        with project():
            result = verify(good_envelope())
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["data"], {"verdict": "pass", "phase": "Specify", "next_action": "Run the Clarify phase."})

    def test_a_claimed_pass_over_failing_disk_evidence_is_rejected(self):
        with project(spec_text="# Spec\n\n[NEEDS CLARIFICATION: scope]\n"):
            result = verify(good_envelope(counts={}))
        self.assertEqual(result["status"], "expected_failure")
        self.assertEqual(result["data"]["verdict"], "fail")
        self.assertEqual(mismatch(result), "gate_claim_mismatch")
        self.assertIn("G1", result["data"]["mismatch"]["detail"])

    def test_a_claimed_failure_over_passing_disk_evidence_is_also_a_mismatch(self):
        with project():
            envelope = good_envelope(status="fail", gates=[{"id": "G1", "result": "fail"}], blocker="G1 failed")
            result = verify(envelope)
        self.assertEqual(result["status"], "expected_failure")
        self.assertEqual(mismatch(result), "gate_claim_mismatch")

    def test_a_missing_artifact_path_fails(self):
        with project():
            result = verify(good_envelope(artifacts=[f"{FEATURE}/spec.md", f"{FEATURE}/plan.md"]))
        self.assertEqual(result["status"], "expected_failure")
        self.assertEqual(mismatch(result), "artifact_missing")
        self.assertIn("plan.md", result["data"]["mismatch"]["detail"])

    def test_an_empty_artifact_fails(self):
        with project() as root:
            (root / FEATURE / "plan.md").write_bytes(b"")
            result = verify(good_envelope(artifacts=[f"{FEATURE}/plan.md"]))
        self.assertEqual(mismatch(result), "artifact_missing")

    def test_unsafe_artifact_paths_fail(self):
        with project() as root:
            (root.parent / "outside.md").write_text("outside\n", encoding="utf-8")
            for path in ("../outside.md", "/etc/hosts", "..\\outside.md", f"{FEATURE}/../../outside.md"):
                with self.subTest(path=path):
                    result = verify(good_envelope(artifacts=[path]))
                    self.assertEqual(result["status"], "expected_failure")
                    self.assertEqual(mismatch(result), "artifact_path_invalid")
            (root / "link.md").symlink_to(root.parent / "outside.md")
            result = verify(good_envelope(artifacts=["link.md"]))
            self.assertEqual(mismatch(result), "artifact_missing")

    def test_unparseable_gate_evidence_fails_and_never_passes(self):
        garbage = {"stdout": "not json", "stderr": "", "exit_code": 0}
        for label, stdout in (("garbage", garbage), ("empty", {"stdout": "", "stderr": "", "exit_code": 0}),
                              ("no verdict", {"stdout": "{\"gate\":\"G1\"}\n", "stderr": "", "exit_code": 0}),
                              ("non-boolean verdict", {"stdout": "{\"gate\":\"G1\",\"pass\":\"yes\"}\n", "stderr": "", "exit_code": 0}),
                              ("array", {"stdout": "[true]\n", "stderr": "", "exit_code": 0})):
            with self.subTest(label), project(), patch.object(phase_envelope, "validate_gate", return_value=stdout):
                result = verify(good_envelope())
            self.assertEqual(result["status"], "expected_failure")
            self.assertEqual(mismatch(result), "gate_evidence_unparseable")

    def test_a_gate_that_raises_fails_closed(self):
        with project(), patch.object(phase_envelope, "validate_gate", side_effect=OSError("unreadable")):
            result = verify(good_envelope())
        self.assertEqual(result["status"], "expected_failure")
        self.assertEqual(mismatch(result), "gate_evidence_unparseable")

    def test_the_phase_gate_must_be_claimed(self):
        with project():
            result = verify(good_envelope(phase="Plan", artifacts=[f"{FEATURE}/spec.md"]))
        self.assertEqual(mismatch(result), "phase_gate_missing")

    def test_a_pass_status_cannot_carry_a_failed_gate(self):
        with project(spec_text="[NEEDS CLARIFICATION: x]\n"):
            envelope = good_envelope(gates=[{"id": "G1", "result": "fail"}], counts={})
            result = verify(envelope)
        self.assertEqual(mismatch(result), "status_contradicts_gates")

    def test_a_driver_reported_failure_is_not_a_pass(self):
        with project(spec_text="[NEEDS CLARIFICATION: x]\n"):
            envelope = good_envelope(status="blocked", gates=[{"id": "G1", "result": "fail"}], counts={},
                                     blocker="Spec still has open questions.")
            result = verify(envelope)
        self.assertEqual(result["status"], "expected_failure")
        self.assertEqual(mismatch(result), "phase_not_passed")
        self.assertIn("open questions", result["data"]["mismatch"]["detail"])

    def test_a_count_that_disagrees_with_the_gate_is_rejected(self):
        with project():
            result = verify(good_envelope(counts={"markers": 3}))
        self.assertEqual(mismatch(result), "count_mismatch")

    def test_a_malformed_envelope_fails_the_phase(self):
        with project():
            envelope = good_envelope()
            del envelope["usage"]
            result = verify(envelope)
        self.assertEqual(result["status"], "expected_failure")
        self.assertEqual(mismatch(result), "envelope_invalid")

    def test_request_shape_errors_are_input_errors(self):
        with project():
            for label, inputs in (("workflow", {"workflow_file": ""}), ("feature", {"feature_dir": "../escape"}),
                                  ("absolute feature", {"feature_dir": "/tmp"})):
                with self.subTest(label):
                    self.assertEqual(verify(good_envelope(), **inputs)["status"], "input_error")
            request = SimpleNamespace(helper_id="verify-phase-envelope", operation="verify-phase-envelope",
                                      mode="read_only", request_id=None, inputs={"envelope": good_envelope()})
            self.assertEqual(dispatch_helper(request)["status"], "input_error")

    def test_the_helper_is_registered_read_only_and_returns_a_compact_answer(self):
        self.assertIn("verify-phase-envelope", HELPERS)
        raw = {"schema_version": "1.0", "helper_id": "verify-phase-envelope", "operation": "verify-phase-envelope",
               "mode": "read_only", "answer_format": "compact",
               "inputs": {"envelope": good_envelope(), "workflow_file": WORKFLOW, "feature_dir": FEATURE}}
        request, error = parse_request(json.dumps(raw))
        self.assertIsNone(error)
        with project():
            result = handle_request(request)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["next_action"], "Run the Clarify phase.")
        self.assertLessEqual(len(json.dumps(result).encode()), 16384)

    def test_verification_does_not_mutate_the_envelope(self):
        envelope = good_envelope()
        before = copy.deepcopy(envelope)
        with project():
            verify(envelope)
        self.assertEqual(envelope, before)


if __name__ == "__main__":
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case) for case in (EnvelopeContractTests, SourceEvidenceTests, ReverifyTests))
    sys.exit(run_counted(suite, label="test-phase-envelope"))
