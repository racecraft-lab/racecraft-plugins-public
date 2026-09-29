#!/usr/bin/env python3
"""Layer-4 tests that Layer 6 dispatch fixtures detect serial, foreground and isolated dispatch."""

from __future__ import annotations

import contextlib
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "tests" / "speckit-pro"
LAYER6 = TESTS_ROOT / "layer6-integration"
FIXTURES = LAYER6 / "test-fixtures"
REDUCE = LAYER6 / "reduce-transcript-fixture.py"
for value in (LAYER6, LAYER6 / "lib", TESTS_ROOT / "lib"):
    if str(value) not in sys.path:
        sys.path.insert(0, str(value))

import transcript_helpers as helpers  # noqa: E402
from lib import fixture_runner  # noqa: E402
from test_result import run_counted  # noqa: E402


class TranscriptDispatchShapeTests(unittest.TestCase):
    def fixture(self, name: str) -> Path:
        return FIXTURES / name

    def test_dispatch_shape_is_recorded(self) -> None:
        serial = helpers.extract_orchestrator_dispatches(self.fixture("serial-dispatch.jsonl"))
        foreground = helpers.extract_orchestrator_dispatches(self.fixture("foreground-dispatch.jsonl"))
        split = helpers.extract_orchestrator_dispatches(self.fixture("parallel-split-message-dispatch.jsonl"))
        self.assertEqual([item["message_index"] for item in serial], [0, 1, 2])
        self.assertEqual([item["message_index"] for item in foreground], [0, 0, 0])
        # Stream events that share a message id are one assistant message.
        self.assertEqual([item["message_index"] for item in split], [0, 0, 0])
        self.assertEqual([item["run_in_background"] for item in serial], [True, True, True])
        self.assertEqual([item["run_in_background"] for item in foreground], [None, None, None])
        self.assertEqual({item["isolation"] for item in serial}, {"worktree"})
        self.assertEqual({item["isolation"] for item in foreground}, {None})
        self.assertEqual(helpers.largest_same_message_dispatch_group(self.fixture("serial-dispatch.jsonl")), 1)
        self.assertEqual(helpers.largest_same_message_dispatch_group(self.fixture("foreground-dispatch.jsonl")), 3)
        self.assertEqual(helpers.largest_same_message_dispatch_group(self.fixture("parallel-split-message-dispatch.jsonl")), 3)
        self.assertEqual(
            helpers.largest_same_message_dispatch_group(
                self.fixture("serial-dispatch.jsonl"), "speckit-pro:domain-researcher"
            ),
            0,
        )
        self.assertFalse(helpers.assert_all_dispatches_background(self.fixture("foreground-dispatch.jsonl")))
        self.assertTrue(helpers.assert_all_dispatches_background(self.fixture("serial-dispatch.jsonl")))
        self.assertFalse(helpers.assert_all_dispatches_isolated(self.fixture("foreground-dispatch.jsonl"), "worktree"))
        self.assertTrue(helpers.assert_all_dispatches_isolated(self.fixture("serial-dispatch.jsonl"), "worktree"))
        worktree = self.fixture("worktree-isolated-dispatch.jsonl")
        self.assertFalse(helpers.assert_no_dispatch_isolation(worktree, "worktree"))
        self.assertTrue(helpers.assert_no_dispatch_isolation(self.fixture("foreground-dispatch.jsonl"), "worktree"))


class DispatchFixtureShapeTests(unittest.TestCase):
    def replay_reporter(self, fixture: Path) -> "fixture_runner.Reporter":
        reporter = fixture_runner.Reporter()
        with contextlib.redirect_stderr(io.StringIO()):
            fixture_runner.assert_dispatch_fixture(fixture, "replay", reporter, check_terms=True)
        return reporter

    def broken_case(self, root: Path, name: str, source: Path, expected: dict[str, object]) -> Path:
        """Write a fixture dir that replays a broken transcript against a real fixture's expectations."""
        case = root / name
        case.mkdir()
        events = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
        blocks = [block for event in events for block in (event.get("message") or {}).get("content", [])]
        for block in blocks:
            if block.get("name") == "Agent":
                block["input"]["subagent_type"] = expected["must_dispatch_to"][0]
        (case / "parser-fixture.jsonl").write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")
        (case / "expected.json").write_text(json.dumps(expected), encoding="utf-8")
        return case

    def test_dispatch_fixtures_reject_serial_and_foreground_dispatch(self) -> None:
        names = ("19-implement-parallel-p-tasks", "20-consensus-multi-item-batch", "21-resolve-pr-parallel-files")
        broken = ("serial-dispatch.jsonl", "foreground-dispatch.jsonl")
        with tempfile.TemporaryDirectory() as temporary:
            for name in names:
                fixture = LAYER6 / "dispatch-fixtures" / name
                expected = json.loads((fixture / "expected.json").read_text(encoding="utf-8"))
                self.assertTrue(expected.get("same_message_dispatch_groups"), name)
                self.assertIs(expected.get("must_run_in_background"), True, name)
                passing = self.replay_reporter(fixture)
                self.assertEqual(passing.passed, passing.total, name)
                for transcript in broken:
                    case = self.broken_case(Path(temporary), f"{name}-{transcript}", LAYER6 / "test-fixtures" / transcript, expected)
                    failing = self.replay_reporter(case)
                    self.assertLess(failing.passed, failing.total, f"{name} accepted {transcript}")

    def test_fixture_19_rejects_worktree_isolated_phase_7_workers(self) -> None:
        fixture = LAYER6 / "dispatch-fixtures" / "19-implement-parallel-p-tasks"
        expected = json.loads((fixture / "expected.json").read_text(encoding="utf-8"))
        self.assertEqual(expected.get("forbidden_isolation"), "worktree")
        self.assertNotIn("required_isolation", expected)
        source = LAYER6 / "test-fixtures" / "worktree-isolated-dispatch.jsonl"
        with tempfile.TemporaryDirectory() as temporary:
            case = self.broken_case(Path(temporary), "19-worktree-isolated", source, expected)
            failing = self.replay_reporter(case)
        self.assertLess(failing.passed, failing.total)
        clean = self.replay_reporter(fixture)
        self.assertEqual(clean.passed, clean.total)

    def test_fixture_21_caps_dispatches_at_the_per_file_partition(self) -> None:
        expected = json.loads(
            (LAYER6 / "dispatch-fixtures" / "21-resolve-pr-parallel-files" / "expected.json").read_text(encoding="utf-8")
        )
        self.assertEqual(expected["max_dispatch_count"], 3)


class ReducerDispatchShapeTests(unittest.TestCase):
    def test_reduce_keeps_dispatch_shape_and_message_grouping(self) -> None:
        source = LAYER6 / "test-fixtures" / "parallel-split-message-dispatch.jsonl"
        with tempfile.TemporaryDirectory() as temporary:
            reduced = subprocess.run(
                [sys.executable, str(REDUCE), str(source)],
                text=True,
                capture_output=True,
                shell=False,
                check=False,
            )
            self.assertEqual(reduced.returncode, 0, reduced.stderr)
            reduced_path = Path(temporary) / "reduced.jsonl"
            reduced_path.write_text(reduced.stdout, encoding="utf-8")
            dispatches = helpers.extract_orchestrator_dispatches(reduced_path)
        self.assertEqual([item["message_index"] for item in dispatches], [0, 0, 0])
        self.assertEqual({item["run_in_background"] for item in dispatches}, {True})
        self.assertEqual({item["isolation"] for item in dispatches}, {"worktree"})
        self.assertNotIn("msg_A", reduced.stdout)


class Layer6FixtureContractTests(unittest.TestCase):
    """Layer 6 fixture prose and terms must name the shipped contract, not retired behavior."""

    DISPATCH = LAYER6 / "dispatch-fixtures"
    AUTOPILOT_REFERENCES = REPO_ROOT / "speckit-pro" / "skills" / "speckit-autopilot" / "references"
    RETIRED = (r"\.sh\b", r"\bL7\b", r"commands/resolve-pr\.md")

    def fixture_text_files(self) -> list[Path]:
        names = {"README.md", "prompt.txt", "sample-spec.md"}
        return sorted(path for path in LAYER6.rglob("*") if path.name in names and "performance-fixtures" not in path.parts)

    def test_fixture_prose_names_no_retired_files_or_layer_names(self) -> None:
        offences = [
            f"{path.relative_to(LAYER6)}: {pattern}"
            for path in [*self.fixture_text_files(), LAYER6 / "README.md"]
            for pattern in self.RETIRED
            if re.search(pattern, path.read_text(encoding="utf-8"))
        ]
        self.assertEqual(offences, [])

    def test_every_dispatch_fixture_has_a_readme(self) -> None:
        missing = [path.name for path in sorted(self.DISPATCH.iterdir()) if not (path / "README.md").is_file()]
        self.assertEqual(missing, [])

    def test_stack_manager_terms_come_from_the_shipped_contract(self) -> None:
        expected = json.loads((self.DISPATCH / "22-stack-manager-replay" / "expected.json").read_text(encoding="utf-8"))
        schema_path = REPO_ROOT / "speckit-pro" / "skills" / "speckit-autopilot" / "contracts" / "stack-manager-decision.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        registry = (REPO_ROOT / "speckit-pro" / "speckit_pro_runner" / "helpers" / "registry.py").read_text(encoding="utf-8")
        shipped = {*schema["properties"], schema["properties"]["schema_version"]["const"]}
        shipped |= {term for term in expected["must_include_terms"] if f'"{term}"' in registry}
        self.assertEqual(sorted(set(expected["must_include_terms"]) - shipped), [])

    def test_redelegation_sample_spec_avoids_the_security_keywords(self) -> None:
        protocol = (self.AUTOPILOT_REFERENCES / "consensus-protocol.md").read_text(encoding="utf-8")
        block = protocol.split("## Security Keywords", 1)[1].split("```")[1]
        keywords = [word.strip() for word in block.replace("\n", " ").split(",") if word.strip()]
        spec = (self.DISPATCH / "03-redelegation-chain" / "sample-spec.md").read_text(encoding="utf-8").casefold()
        # Only the fixture's own scenario counts, so drop the note that explains the avoidance.
        scenario = spec.split("## feature", 1)[1]
        found = [word for word in keywords if re.search(rf"(?<![a-z]){re.escape(word.casefold())}s?(?![a-z])", scenario)]
        self.assertEqual(found, [])

    def test_parallel_task_fixture_cites_the_partition_helper(self) -> None:
        prompt = (self.DISPATCH / "19-implement-parallel-p-tasks" / "prompt.txt").read_text(encoding="utf-8")
        phase_execution = (self.AUTOPILOT_REFERENCES / "phase-execution.md").read_text(encoding="utf-8")
        self.assertIn("partition-phase7-tasks", prompt)
        self.assertIn("partition-phase7-tasks", phase_execution)
        self.assertIn("Steps 3a-3c", prompt)
        self.assertNotIn("isolation: \"worktree\"", prompt)


if __name__ == "__main__":
    suite = unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromTestCase(case)
        for case in (
            TranscriptDispatchShapeTests,
            DispatchFixtureShapeTests,
            ReducerDispatchShapeTests,
            Layer6FixtureContractTests,
        )
    )
    raise SystemExit(run_counted(suite, label="test-dispatch-fixture-shape"))
