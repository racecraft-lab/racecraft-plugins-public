#!/usr/bin/env python3
"""Scaffold's quality-gates proposal (ADR 0007): measurement rules, confirm-before-write, decline stores nothing."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
LIB_DIR = TEST_DIR.parent / "lib"
sys.path.insert(0, str(LIB_DIR))
sys.path.insert(0, str(REPO_ROOT / "speckit-pro"))

from host_skill_views import host_skill_root  # noqa: E402
from runner_invocation import assert_runner_response, run_runner  # noqa: E402
from readiness_case import current_plugin_revision  # noqa: E402
from test_result import run_counted  # noqa: E402

GATES_FILE = ".specify/quality-gates.json"
REPORT_FILE = ".specify/quality-gates-report.json"
VALID = {"schema_version": "1.0", "thresholds": {"complexity": 10, "crap": 30, "mutation_score_floor": 60}}


def function(file: str, name: str, complexity: int) -> dict[str, object]:
    return dict(file=file, name=name, complexity=complexity, coverage=0.5, crap=1.0)


def envelope(helper_id: str, mode: str, inputs: dict[str, object]) -> dict[str, object]:
    return dict(schema_version="1.0", request_id=f"test-{helper_id}", helper_id=helper_id, operation=helper_id,
                mode=mode, inputs=inputs)


def assert_paths_and_display_are_bounded_to_the_checkout(case) -> None:
    outside = case.tools / "secret.py"
    outside.touch()
    (case.root / "escape.py").symlink_to(outside)
    bad = [outside.as_posix(), "../secret.py", "escape.py", "src/" + "a" * 5000, "src/evil\\path.py"]
    rows = [function(path, "bad", 40) for path in bad]
    rows += [function("src/legacy.py", "x" * 5000, 40) for _ in range(100)]
    write_report(case.root, [*[function("src/ok.py", "ok", 1)] * 2000, *rows])
    data = case.run_helper("dry_run")["data"]
    case.assertEqual(["src/legacy.py"], [row["file"] for row in data["failing_files"]])
    case.assertLessEqual(len(data["failing_files"][0]["functions"]), 20)
    case.assertLessEqual(len(data["failing_files"][0]["functions"][0]["name"]), 200)

def assert_unbounded_complexities_do_not_raise_the_proposed_ceiling(case) -> None:
    write_report(case.root, [function("src/bad.py", "bad", 10**100)] * 10)
    data = case.run_helper("dry_run")["data"]
    case.assertEqual(10, data["proposal"]["thresholds"]["complexity"])
    case.assertEqual("nist-235", data["proposal"]["basis"]["method"])

def assert_malformed_functions_fall_back_and_apply_consumes_the_report(case) -> None:
    for functions in (None, 5, "bad", {}, [None, 4, "bad"]):
        with case.subTest(functions=functions):
            (case.root / REPORT_FILE).write_text(json.dumps({"functions": functions}), encoding="utf-8")
            dry = case.run_helper("dry_run")
            assert_runner_response(case, dry, "ok", 0)
            case.assertEqual("nist-235", dry["data"]["proposal"]["basis"]["method"])
            response = case.run_helper("apply", confirmed=False)
            assert_runner_response(case, response, "ok", 0)
            case.assertTrue(response["data"]["report_removed"])
            case.assertFalse((case.root / REPORT_FILE).exists())

def assert_preview_includes_measured_crap_failures(case) -> None:
    rows = ten_functions()
    rows[0]["crap"] = 90
    rows[0]["file"] = "src/uncovered.py"
    write_report(case.root, rows)
    data = case.run_helper("dry_run")["data"]
    case.assertIn("src/uncovered.py", [row["file"] for row in data["failing_files"]])

def assert_a_yes_cannot_write_a_changed_proposal(case) -> None:
    write_report(case.root, ten_functions())
    shown = case.run_helper("dry_run")["data"]
    write_report(case.root, [function("src/changed.py", "changed", 20)] * 10)
    response = case.run_helper("apply", confirmed=True, proposal_digest=shown.get("proposal_digest", "missing"))
    case.assertEqual("expected_failure", response["status"])
    case.assertEqual("proposal_changed", response["data"]["outcome"])
    case.assertFalse((case.root / GATES_FILE).exists())
    case.assertFalse((case.root / REPORT_FILE).exists())


def observe_quality_gates_source(case) -> dict:
    record = envelope("write-readiness-record", "dry_run", {
        "host": "claude", "execution_mode": "interactive", "plugin_revision": current_plugin_revision(), "observations": []})
    _, response, _ = run_runner(record, cwd=case.root, extra_env={"PATH": str(case.tools)})
    return response["data"]["record"]["items"]["quality_gates"]


def ten_functions() -> list[dict[str, object]]:
    """Nine simple functions (complexity 1 to 9) and one outlier of 40 in a named file."""
    simple = [function("src/ok.py", f"ok{n}", n) for n in range(1, 10)]
    return [*simple, function("src/legacy.py", "tangle", 40)]





def write_report(root, functions: list[dict[str, object]]) -> None:
    (root / REPORT_FILE).write_text(json.dumps({"functions": functions}), encoding="utf-8")



class QualityGatesProposalTest(unittest.TestCase):
    def setUp(self) -> None:
        scratch = [self.enterContext(tempfile.TemporaryDirectory()) for _ in range(2)]
        self.root, self.tools = (Path(name).resolve() for name in scratch)
        (self.root / ".specify").mkdir()


    def run_helper(self, mode: str, **inputs: object) -> dict:
        if inputs.get("confirmed") is True and "proposal_digest" not in inputs:
            inputs["proposal_digest"] = self.run_helper("dry_run", measured=inputs.get("measured", True))["data"].get("proposal_digest", "")
        body = envelope("propose-quality-gates", mode, {"measured": True, **inputs})
        return run_runner(body, cwd=self.root, extra_env={"PATH": str(self.tools)})[1]


    def listing(self) -> dict[str, bytes]:
        return {path.relative_to(self.root).as_posix(): path.read_bytes()
                for path in sorted(self.root.rglob("*")) if path.is_file() and not path.is_symlink()}

    def test_proposal_lets_about_ninety_percent_of_measured_functions_pass_and_names_the_failures(self) -> None:
        write_report(self.root, ten_functions())
        before = self.listing()
        response = self.run_helper("dry_run")
        assert_runner_response(self, response, "ok", 0)
        data = response["data"]
        self.assertEqual("missing", data["status"])
        proposal = data["proposal"]
        self.assertEqual({"complexity": 9, "crap": 30, "mutation_score_floor": 60}, proposal["thresholds"])
        self.assertEqual("percentile-90", proposal["basis"]["method"])
        self.assertEqual(10, proposal["basis"]["measured_functions"])
        self.assertEqual([{"file": "src/legacy.py", "functions": [{"name": "tangle", "complexity": 40}], "functions_truncated": False}],
                         data["failing_files"])
        self.assertEqual(1, data["failing_function_count"])
        self.assertEqual(before, self.listing(), "a dry run writes nothing")
        assert_preview_includes_measured_crap_failures(self)

    def test_nothing_measured_proposes_the_nist_ceiling_of_ten(self) -> None:
        cases = {"declined tool, stale report": (False, ten_functions()), "empty report": (True, [])}
        for label, (measured, functions) in cases.items():
            with self.subTest(label):
                write_report(self.root, functions)  # a stale report must be ignored when nothing was measured
                response = self.run_helper("dry_run", measured=measured)
                assert_runner_response(self, response, "ok", 0)
                proposal = response["data"]["proposal"]
                self.assertEqual({"complexity": 10, "crap": 30, "mutation_score_floor": 60}, proposal["thresholds"])
                self.assertEqual("nist-235", proposal["basis"]["method"])
                self.assertEqual(0, proposal["basis"]["measured_functions"])
                self.assertEqual([], response["data"]["failing_files"])

        assert_unbounded_complexities_do_not_raise_the_proposed_ceiling(self)
        assert_malformed_functions_fall_back_and_apply_consumes_the_report(self)

    def test_the_file_is_written_only_on_a_yes_and_validates(self) -> None:
        from speckit_pro_runner import quality_gates

        write_report(self.root, ten_functions())
        proposal = self.run_helper("dry_run")["data"]["proposal"]
        response = self.run_helper("apply", confirmed=True)
        assert_runner_response(self, response, "ok", 0)
        self.assertEqual("written", response["data"]["outcome"])
        written = json.loads((self.root / GATES_FILE).read_text(encoding="utf-8"))
        self.assertEqual(proposal, written)
        self.assertEqual([], quality_gates.validate(written))
        self.assertFalse((self.root / REPORT_FILE).exists(), "the consumed report is removed")
        (self.root / GATES_FILE).unlink()
        assert_a_yes_cannot_write_a_changed_proposal(self)

    def test_a_decline_writes_nothing_and_stores_no_decline(self) -> None:
        write_report(self.root, ten_functions())
        untouched = {path: content for path, content in self.listing().items() if path != REPORT_FILE}
        response = self.run_helper("apply", confirmed=False)
        assert_runner_response(self, response, "ok", 0)
        self.assertEqual("declined", response["data"]["outcome"])
        self.assertFalse(response["data"]["writes_state"])
        self.assertEqual(untouched, self.listing(), "only the scratch report may disappear")

    def test_only_a_boolean_yes_confirms(self) -> None:
        write_report(self.root, ten_functions())
        before = self.listing()
        for value in ("yes", 1, None):
            with self.subTest(confirmed=value):
                response = self.run_helper("apply", confirmed=value)
                assert_runner_response(self, response, "input_error", 2)
        assert_runner_response(self, self.run_helper("apply"), "input_error", 2)
        self.assertEqual(before, self.listing())

    def test_a_confirmed_file_is_never_overwritten_and_an_invalid_one_is_replaced_only_on_a_yes(self) -> None:
        gates = self.root / GATES_FILE
        gates.write_text(json.dumps({**VALID, "thresholds": {**VALID["thresholds"], "complexity": 7}}), encoding="utf-8")
        present = self.run_helper("dry_run")
        self.assertEqual(("present", None), (present["data"]["status"], present["data"]["proposal"]))
        kept = gates.read_bytes()
        response = self.run_helper("apply", confirmed=True)
        assert_runner_response(self, response, "ok", 0)
        self.assertEqual("already_present", response["data"]["outcome"])
        self.assertEqual(kept, gates.read_bytes())
        gates.write_text('{"schema_version": "2"}', encoding="utf-8")
        invalid = self.run_helper("dry_run")["data"]
        self.assertEqual("invalid", invalid["status"])
        self.assertIn("schema_version", invalid["problems"][0])
        self.assertIsNotNone(invalid["proposal"])
        self.run_helper("apply", confirmed=False)
        self.assertEqual('{"schema_version": "2"}', gates.read_text(encoding="utf-8"))
        self.run_helper("apply", confirmed=True)
        self.assertEqual(VALID["schema_version"], json.loads(gates.read_text(encoding="utf-8"))["schema_version"])

    def test_a_symlinked_target_is_refused_and_the_linked_file_stays_untouched(self) -> None:
        outside = self.tools / "outside.json"
        outside.write_text("keep", encoding="utf-8")
        os.symlink(outside, self.root / GATES_FILE)
        response = self.run_helper("apply", confirmed=True)
        self.assertEqual("expected_failure", response["status"])
        self.assertEqual("write_failed", response["data"]["outcome"])
        self.assertEqual("keep", outside.read_text(encoding="utf-8"))

    def test_the_worst_files_come_first_when_the_list_is_capped(self) -> None:
        crowd = [function(f"src/a{n:02d}.py", "f", 20 + n % 5) for n in range(25)]
        write_report(self.root, [*crowd, function(self.root.joinpath("src/zeta.py").as_posix(), "worst", 80),
                           *[function("src/ok.py", f"ok{n}", 1) for n in range(300)]])
        data = self.run_helper("dry_run")["data"]
        self.assertEqual("src/zeta.py", data["failing_files"][0]["file"])
        self.assertEqual(20, len(data["failing_files"]))
        self.assertTrue(data["failing_files_truncated"])
        self.assertEqual(26, data["failing_file_count"])
        assert_paths_and_display_are_bounded_to_the_checkout(self)






    def test_the_readiness_record_carries_the_observed_quality_gates_source(self) -> None:

        write_report(self.root, ten_functions())
        self.run_helper("apply", confirmed=False)
        declined = observe_quality_gates_source(self)
        self.assertEqual("unavailable", declined["status"])
        self.assertIn("shipped defaults in use", declined["evidence_source"])
        write_report(self.root, ten_functions())
        self.run_helper("apply", confirmed=True)
        confirmed = observe_quality_gates_source(self)
        self.assertEqual("verified", confirmed["status"])
        self.assertRegex(confirmed["fingerprints"][f"file:{GATES_FILE}"], r"^sha256:[0-9a-f]{64}$")

    def test_scaffold_documents_the_request_and_the_step_on_each_host(self) -> None:
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                skill = (host_skill_root(host) / "speckit-scaffold-spec" / "SKILL.md").read_text(encoding="utf-8")
                rows = re.findall(r"\| `propose-quality-gates` \| `(dry_run|apply)` \| `(\{[^`]*\})`", skill)
                self.assertEqual({"dry_run", "apply"}, {mode for mode, _ in rows})
                for _, body in rows:
                    self.assertLessEqual(set(json.loads(body)), {"measured", "confirmed", "proposal_digest"})
                step = skill.split("### 6.4 Propose the Quality Gates", 1)[1].split("\n### ", 1)[0]
                self.assertLess(skill.index("### 6.4 "), skill.index("### 6.5 "))
                self.assertIn("skip the coverage run", step)
                for phrase in ("quality_gate_confirmation", "writes nothing", "Ask once"):
                    self.assertIn(phrase, step)
                if host == "codex":
                    self.assertLessEqual(len(re.search(r"header `([^`]+)`", step).group(1)), 12)
                question = {"claude": "AskUserQuestion", "codex": "request_user_input"}
                self.assertIn(question[host], step)
                self.assertNotIn(question["codex" if host == "claude" else "claude"], step)


def build_suite() -> unittest.TestSuite:
    return unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(QualityGatesProposalTest)])


def main() -> int:
    return run_counted(build_suite(), label="test-quality-gates-proposal")


if __name__ == "__main__":
    raise SystemExit(main())
