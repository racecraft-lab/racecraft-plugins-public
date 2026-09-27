#!/usr/bin/env python3
"""Archive Sweep candidates: enumerate specs, exclude the current target, prove merges.

The stock archive extension archives one feature per run, so SpecKit Pro owns
the sweep enumeration. Only a spec whose merged pull request the helper can
observe may be archived; any spec whose evidence it cannot read stays active.
"""

import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO / "speckit-pro"), str(REPO / "tests/speckit-pro/lib")]
from speckit_pro_runner.helpers import archive_sweep  # noqa: E402
from speckit_pro_runner.helpers.registry import HELPERS, dispatch_helper  # noqa: E402
from test_result import run_counted  # noqa: E402

HELPER_ID = "list-archive-candidates"


def merged_pr(number: int, sha: str) -> dict[str, object]:
    return {
        "number": number,
        "url": f"https://github.com/example/project/pull/{number}",
        "mergeCommit": {"oid": sha},
    }


class ArchiveSweepCandidateTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / ".specify").mkdir()
        previous = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous)
        self.calls: list[list[str]] = []
        self.answers: dict[str, dict[str, object]] = {}

    def spec(self, name: str, *, with_spec: bool = True) -> None:
        directory = self.root / "specs" / name
        directory.mkdir(parents=True)
        if with_spec:
            (directory / "spec.md").write_text(f"# {name}\n", encoding="utf-8")

    def answer(self, branch: str, *, exit_status: int | None = 0, stdout: object = "[]") -> None:
        text = stdout if isinstance(stdout, str) else json.dumps(stdout)
        self.answers[branch] = {"exit_status": exit_status, "stdout_tail": text, "stderr_tail": ""}

    def probe(self, root: Path, argv: list[str]) -> dict[str, object]:
        self.calls.append(argv)
        self.assertEqual(self.root, root)
        branch = argv[argv.index("--head") + 1]
        return {"argv": argv, **self.answers.get(branch, {"exit_status": 0, "stdout_tail": "[]", "stderr_tail": ""})}

    def request(self, **inputs: object) -> dict[str, object]:
        request = SimpleNamespace(
            helper_id=HELPER_ID,
            operation=HELPER_ID,
            request_id="archive-sweep-test",
            mode="read_only",
            inputs=inputs,
        )
        with patch.object(archive_sweep, "probe", side_effect=self.probe):
            return dispatch_helper(request)

    def test_registered_as_read_only_helper(self) -> None:
        self.assertIn(HELPER_ID, HELPERS)
        self.assertEqual(HELPER_ID, HELPERS[HELPER_ID].operation)
        fixture = REPO / "tests/speckit-pro/unit/fixtures/read-only-helpers/requests" / f"{HELPER_ID}.json"
        self.assertEqual(HELPER_ID, json.loads(fixture.read_text(encoding="utf-8"))["helper_id"])

    def test_lists_merged_candidates_in_ascending_order_and_excludes_current_target(self) -> None:
        for name in ("003-third", "001-first", "002-second", "004-current"):
            self.spec(name)
        self.answer("001-first", stdout=[merged_pr(11, "a" * 40)])
        self.answer("003-third", stdout=[merged_pr(13, "c" * 40)])
        result = self.request(current_target="specs/004-current/")
        self.assertEqual("ok", result["status"], result)
        data = result["data"]
        self.assertFalse(data["writes_state"])
        self.assertEqual("specs/004-current", data["excluded_current_spec"])
        self.assertEqual(["specs/001-first", "specs/003-third"], data["archive_order"])
        self.assertEqual(["specs/002-second"], data["not_merged"])
        self.assertEqual([], data["unknown"])
        self.assertEqual(
            ["specs/001-first", "specs/002-second", "specs/003-third"],
            [row["spec_dir"] for row in data["candidates"]],
        )
        first = data["candidates"][0]
        self.assertEqual("merged", first["merge_evidence"])
        self.assertEqual(11, first["pr_number"])
        self.assertEqual("a" * 40, first["merge_sha"])
        queried = [argv[argv.index("--head") + 1] for argv in self.calls]
        self.assertNotIn("004-current", queried)
        for argv in self.calls:
            self.assertEqual(["gh", "pr", "list"], argv[:3])
            self.assertIn("merged", argv)

    def test_skips_directories_without_spec_and_symlinked_directories(self) -> None:
        self.spec("001-real")
        self.spec("002-draft", with_spec=False)
        (self.root / "specs" / "003-link").symlink_to(self.root / "specs" / "001-real", target_is_directory=True)
        self.answer("001-real", stdout=[merged_pr(5, "b" * 40)])
        data = self.request(current_target="specs/009-new")["data"]
        self.assertEqual(["specs/001-real"], [row["spec_dir"] for row in data["candidates"]])
        self.assertEqual(["specs/001-real"], data["archive_order"])

    def test_missing_specs_root_reports_no_candidates(self) -> None:
        result = self.request(current_target="specs/001-new")
        self.assertEqual("ok", result["status"], result)
        self.assertEqual([], result["data"]["candidates"])
        self.assertEqual([], result["data"]["archive_order"])
        self.assertEqual([], self.calls)

    def test_unreadable_evidence_fails_closed_to_unknown(self) -> None:
        cases = {
            "001-exit": {"exit_status": 1, "stdout": ""},
            "002-missing-gh": {"exit_status": None, "stdout": ""},
            "003-bad-json": {"exit_status": 0, "stdout": "not json"},
            "004-no-sha": {"exit_status": 0, "stdout": [{"number": 4, "url": "https://example.test/4", "mergeCommit": None}]},
            "005-bool-number": {"exit_status": 0, "stdout": [{"number": True, "url": "u", "mergeCommit": {"oid": "d" * 40}}]},
            "006-object": {"exit_status": 0, "stdout": {"number": 6}},
        }
        for name, answer in cases.items():
            self.spec(name)
            self.answer(name, exit_status=answer["exit_status"], stdout=answer["stdout"])
        result = self.request(current_target="specs/999-current")
        self.assertEqual("ok", result["status"], result)
        data = result["data"]
        self.assertEqual([], data["archive_order"])
        self.assertEqual([], data["not_merged"])
        self.assertEqual(sorted(f"specs/{name}" for name in cases), data["unknown"])
        for row in data["candidates"]:
            with self.subTest(spec=row["spec_dir"]):
                self.assertEqual("unknown", row["merge_evidence"])
                self.assertTrue(row["reason"])

    def test_directory_name_that_is_not_a_branch_is_unknown_without_a_query(self) -> None:
        self.spec("-leading-dash")
        data = self.request(current_target="specs/001-current")["data"]
        self.assertEqual(["specs/-leading-dash"], data["unknown"])
        self.assertEqual([], self.calls)

    def test_current_target_is_required_and_repo_relative(self) -> None:
        for inputs in ({}, {"current_target": ""}, {"current_target": "../specs/x"}, {"current_target": 7}):
            with self.subTest(inputs=inputs):
                result = self.request(**inputs)
                self.assertEqual("input_error", result["status"], result)
        result = self.request(current_target="specs/x", surprise=True)
        self.assertEqual("input_error", result["status"], result)


if __name__ == "__main__":
    sys.exit(
        run_counted(
            unittest.defaultTestLoader.loadTestsFromTestCase(ArchiveSweepCandidateTests),
            label="test-archive-sweep-candidates",
        )
    )
