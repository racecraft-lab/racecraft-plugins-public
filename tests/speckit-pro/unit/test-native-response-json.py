#!/usr/bin/env python3
"""Focused contract tests for host-specific strict response JSON grading."""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
sys.path.insert(0, str(TEST_ROOT / "lib"))

from native_eval_grading import grade_observation  # noqa: E402
from test_result import run_counted  # noqa: E402


EXPECTED = {
    "claude": [
        {"step": "Post the implementation summary", "why": "Keep the review record current."},
        {"step": "Resolve addressed review threads", "why": "Leave only active findings open."},
    ],
    "codex": [
        {"step": "Post the implementation summary", "why": "Keep the review record current."},
        {"step": "Request the next review pass", "why": "Codex does not resolve Claude review threads."},
    ],
}


def check() -> dict[str, object]:
    return {
        "id": "post-steps",
        "requirement": "post-steps",
        "type": "response_json_field",
        "field_path": ["Post"],
        "expected_by_host": copy.deepcopy(EXPECTED),
    }


def case(value: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "requirements": [{"id": "post-steps"}],
        "checks": [value or check()],
    }


def observation(
    value: object, *, encoded: bool = False, cwd: str | None = None,
    tool_calls: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {
        "completed": True,
        "error": None,
        "final_text": value if encoded else json.dumps(value, allow_nan=False),
        "activations": [],
        "tool_calls": tool_calls or [],
        "artifacts": {},
        "usage": {},
    }
    if cwd is not None:
        result["native_metadata"] = {"cwd": cwd}
    return result


def _grade_response(response: object, *, host: str | None = "claude",
                    value: dict[str, object] | None = None, encoded: bool = False) -> str:
    return str(grade_observation(
        case(value), observation(response, encoded=encoded), host=host,
    )["status"])


def _grade_command(command: str) -> str:
    forbidden = {
        "id": "forbidden", "requirement": "forbidden", "type": "tool_used",
        "name": "command_execution", "input_regex": "relocate-process-artifacts",
        "min": 0, "max": 0,
    }
    test_case = {"requirements": [{"id": "forbidden"}], "checks": [forbidden]}
    call = {
        "name": "command_execution", "input": {"command": command},
        "success": True,
    }
    return str(grade_observation(
        test_case, observation({}, tool_calls=[call]), host="codex",
    )["status"])


class NativeResponseJsonTests(unittest.TestCase):
    def grade(self, response: object, *, host: str | None = "claude",
              value: dict[str, object] | None = None, encoded: bool = False) -> str:
        return _grade_response(response, host=host, value=value, encoded=encoded)

    def test_each_host_matches_only_its_declared_post_steps(self) -> None:
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                self.assertEqual(self.grade({"Post": EXPECTED[host]}, host=host), "pass")
                other = "codex" if host == "claude" else "claude"
                self.assertEqual(self.grade({"Post": EXPECTED[other]}, host=host), "fail")

    def test_array_order_omissions_and_extras_fail(self) -> None:
        expected = EXPECTED["claude"]
        variants = [
            list(reversed(expected)),
            expected[:1],
            [*expected, {"step": "Undeclared action", "why": "Not in the contract."}],
        ]
        for value in variants:
            with self.subTest(value=value):
                self.assertEqual(self.grade({"Post": value}), "fail")

    def test_response_must_be_one_complete_strict_json_value(self) -> None:
        valid = json.dumps({"Post": EXPECTED["claude"]})
        malformed = [
            '{"Post": [], "Post": []}',
            '{"Post": NaN}',
            valid[:-1],
            f"```json\n{valid}\n```",
            valid + " trailing prose",
        ]
        for text in malformed:
            with self.subTest(text=text):
                self.assertEqual(self.grade(text, encoded=True), "fail")

    def test_field_selection_and_strict_scalar_types(self) -> None:
        value = check()
        value["field_path"] = ["metrics", 0, "count"]
        value["expected_by_host"] = {"claude": 1, "codex": 2}
        self.assertEqual(self.grade({"metrics": [{"count": 1}]}, value=value), "pass")
        for mismatch in (True, 1.0):
            with self.subTest(mismatch=mismatch):
                self.assertEqual(
                    self.grade({"metrics": [{"count": mismatch}]}, value=value),
                    "fail",
                )
        self.assertEqual(self.grade({"metrics": []}, value=value), "fail")
        self.assertEqual(self.grade({"other": [{"count": 1}]}, value=value), "fail")

    def test_invalid_field_path_selectors_are_catalog_invalid(self) -> None:
        for field_path in ([], [""], [-1], [True]):
            value = check()
            value["field_path"] = field_path
            with self.subTest(field_path=field_path):
                self.assertEqual(self.grade({"Post": EXPECTED["claude"]}, value=value),
                                 "invalid")

    def test_expected_mapping_must_have_two_strict_json_values(self) -> None:
        malformed = [
            {"claude": EXPECTED["claude"]},
            {"claude": EXPECTED["claude"], "codex": EXPECTED["codex"], "other": []},
            {"claude": {"not-json"}, "codex": EXPECTED["codex"]},
            {"claude": math.nan, "codex": EXPECTED["codex"]},
        ]
        for mapping in malformed:
            value = check()
            value["expected_by_host"] = mapping
            with self.subTest(mapping=mapping):
                self.assertEqual(self.grade({"Post": EXPECTED["claude"]}, value=value),
                                 "invalid")

    def test_missing_or_untrusted_host_is_invalid(self) -> None:
        response = {"Post": EXPECTED["claude"]}
        for host in (None, "other"):
            with self.subTest(host=host):
                self.assertEqual(self.grade(response, host=host), "invalid")


class NativeResponseJsonPathAndToolTests(unittest.TestCase):
    def test_stage_absolute_path_matches_only_its_trusted_cwd_relative_path(self) -> None:
        value = check()
        value["field_path"] = ["source_path"]
        value["expected_by_host"] = {
            "claude": ".worktrees/spec-021/docs/plan.md",
            "codex": ".worktrees/spec-021/docs/plan.md",
        }
        cwd = "/private/tmp/native-eval/workspace"
        response = {"source_path": cwd + "/.worktrees/spec-021/docs/plan.md"}
        result = grade_observation(case(value), observation(response, cwd=cwd), host="codex")
        self.assertEqual(result["status"], "pass")
        for actual, trusted_cwd in (
            ("/private/tmp/native-eval/outside/docs/plan.md", cwd),
            (cwd + "/.worktrees/spec-021/docs/plan.md", "/private/tmp/other"),
            (cwd + "/.worktrees/spec-021/../spec-021/docs/plan.md", cwd),
        ):
            with self.subTest(actual=actual, trusted_cwd=trusted_cwd):
                result = grade_observation(
                    case(value), observation({"source_path": actual}, cwd=trusted_cwd),
                    host="codex",
                )
                self.assertEqual(result["status"], "fail")

    def test_search_text_does_not_count_as_a_forbidden_command_invocation(self) -> None:
        self.assertEqual(
            _grade_command("rg -n 'relocate-process-artifacts' .agents docs"), "pass",
        )
        self.assertEqual(
            _grade_command("/bin/zsh -c \"grep -R 'relocate-process-artifacts' docs\""),
            "pass",
        )
        self.assertEqual(_grade_command("relocate-process-artifacts --dry-run"), "fail")
        # Ambiguous compound shell remains fail-closed rather than hiding a
        # possible invocation behind a search command.
        self.assertEqual(
            _grade_command("rg -n relocate-process-artifacts docs || relocate-process-artifacts"),
            "fail",
        )


class NativeResponseJsonProjectionTests(unittest.TestCase):
    def test_structured_id_projection_accepts_only_unique_exact_ids(self) -> None:
        value = check()
        value["field_path"] = ["observed_extensions"]
        value["expected_by_host"] = {
            "claude": ["verify", "review"], "codex": ["verify", "review"],
        }
        accepted = (
            [{"id": "review", "status": "configured"}, {"id": "verify"}],
            {"targets": [{"id": "verify", "purpose": "checks"}, {"id": "review"}]},
        )
        for actual in accepted:
            with self.subTest(actual=actual):
                self.assertEqual(
                    _grade_response({"observed_extensions": actual}, host="codex", value=value),
                    "pass",
                )
        rejected = (
            [{"id": "verify"}],
            [{"id": "verify"}, {"id": "verify"}],
            [{"id": "verify"}, {"id": 2}],
            {"targets": [{"id": "verify"}, {"id": "review"}], "extra": True},
            {"items": [{"id": "verify"}, {"id": "review"}]},
        )
        for actual in rejected:
            with self.subTest(actual=actual):
                self.assertEqual(
                    _grade_response({"observed_extensions": actual}, host="codex", value=value),
                    "fail",
                )


if __name__ == "__main__":
    suite = unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromTestCase(test_case)
        for test_case in (
            NativeResponseJsonTests,
            NativeResponseJsonPathAndToolTests,
            NativeResponseJsonProjectionTests,
        )
    )
    raise SystemExit(run_counted(suite, label="test-native-response-json"))
