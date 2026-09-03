#!/usr/bin/env python3
"""Unit tests for the Phase 7 task-partition runner helper.

The autopilot orchestrator used to execute the partition rules in context:
read tasks.md, group consecutive same-agent [P] tasks into parallel runs,
degrade a one-task run to a singleton, split each parallel run into waves, and
route every task to an agent by keyword. That is a deterministic procedure, so
it belongs in the runner where it can be tested. These tests cover each routing
branch, grouping across an agent change, wave splitting, the degrade rule, and
untagged tasks.

The helper is exercised in process against a temporary root so the fixtures can
state exactly one behavior each; the request-envelope path is covered by
test-speckit-pro-read-only-helpers.py.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
SHARED_LIB = REPO_ROOT / "tests" / "speckit-pro" / "lib"

if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))

from test_result import run_counted  # noqa: E402

from speckit_pro_runner.helpers.read_only import partition_phase7_tasks  # noqa: E402

IMPLEMENT_EXECUTOR = "speckit-pro:implement-executor"
DOMAIN_RESEARCHER = "speckit-pro:domain-researcher"
ORCHESTRATOR_DIRECT = "orchestrator-direct"


def partition(body: str, **inputs: object) -> tuple[dict[str, object], int]:
    """Run the helper over ``body`` written into a temporary repository root."""
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root).resolve()
        tasks_file = root / "tasks.md"
        tasks_file.write_text(body, encoding="utf-8")
        request: dict[str, object] = {"tasks_file": "tasks.md"}
        request.update(inputs)
        result = partition_phase7_tasks(request, root)
    return json.loads(result["stdout"]), int(result["exit_code"])


def tasks_body(*lines: str) -> str:
    return "\n".join(("## Phase 1: Setup", "", *lines, ""))


def route_of(line: str, **inputs: object) -> str:
    payload, exit_code = partition(tasks_body(line), **inputs)
    assert exit_code == 0, payload
    runs = payload["runs"]
    assert len(runs) == 1, runs
    return runs[0]["agent"]


class RoutingTests(unittest.TestCase):
    def test_project_agent_wins_when_a_project_keyword_matches(self) -> None:
        agent = route_of(
            "- [ ] T001 Add the payments checkout module",
            project_agent_name="acme-developer",
            project_agent_keywords=["checkout", "ledger"],
        )
        self.assertEqual(agent, "acme-developer")

    def test_project_agent_needs_both_a_name_and_a_keyword_hit(self) -> None:
        with self.subTest(msg="no name"):
            agent = route_of(
                "- [ ] T001 Add the payments checkout module",
                project_agent_keywords=["checkout"],
            )
            self.assertEqual(agent, IMPLEMENT_EXECUTOR)
        with self.subTest(msg="no keyword hit"):
            agent = route_of(
                "- [ ] T001 Add the payments module",
                project_agent_name="acme-developer",
                project_agent_keywords=["checkout"],
            )
            self.assertEqual(agent, IMPLEMENT_EXECUTOR)

    def test_project_keywords_match_case_insensitively_on_whole_words(self) -> None:
        with self.subTest(msg="case insensitive"):
            agent = route_of(
                "- [ ] T001 Add the Checkout module",
                project_agent_name="acme-developer",
                project_agent_keywords=["checkout"],
            )
            self.assertEqual(agent, "acme-developer")
        with self.subTest(msg="not a substring match"):
            agent = route_of(
                "- [ ] T001 Add the checkouts module",
                project_agent_name="acme-developer",
                project_agent_keywords=["checkout"],
            )
            self.assertEqual(agent, IMPLEMENT_EXECUTOR)

    def test_test_keywords_route_to_the_implement_executor(self) -> None:
        for title in (
            "Write the contract test for the ledger endpoint",
            "Add a unit test for the parser",
            "Cover the integration path end to end",
            "Add failing tests in src/parser.test.ts",
        ):
            with self.subTest(msg=title):
                self.assertEqual(route_of(f"- [ ] T001 {title}"), IMPLEMENT_EXECUTOR)

    def test_research_keywords_route_to_the_domain_researcher(self) -> None:
        for title in (
            "Research the upstream pagination contract",
            "Investigate the retry semantics",
            "Explore API options for the billing provider",
        ):
            with self.subTest(msg=title):
                self.assertEqual(route_of(f"- [ ] T001 {title}"), DOMAIN_RESEARCHER)

    def test_verification_keywords_route_to_the_orchestrator(self) -> None:
        for title in (
            "Verify the migration applies cleanly",
            "Run the deterministic suite",
            "Check the generated payload digests",
            "Build the docs site bundle",
            "Lint the runner package",
        ):
            with self.subTest(msg=title):
                self.assertEqual(route_of(f"- [ ] T001 {title}"), ORCHESTRATOR_DIRECT)

    def test_a_verify_keyword_away_from_the_head_does_not_route_the_task(self) -> None:
        """Branch (d) is the verification-only branch, so it reads the head.

        Matching a verify keyword anywhere in the description sent
        implementation work to ``orchestrator-direct``, the one branch that
        dispatches no agent and injects no TDD protocol. In every line below
        the keyword is an ordinary noun or a subordinate clause rather than the
        purpose of the task, so the task belongs to the executor.
        """
        for title in (
            "Add the required validate-release-note check (workflow)",
            "Write the fixture's deleted-tests ledger, then run the default-suite gate",
            "Register the helper in the dispatch table and check the manifest",
            "Port the parser and lint the result",
        ):
            with self.subTest(msg=title):
                self.assertEqual(route_of(f"- [ ] T001 {title}"), IMPLEMENT_EXECUTOR)

    def test_markdown_emphasis_does_not_hide_the_leading_verb(self) -> None:
        """A bolded opening verb is still the opening verb."""
        for title in (
            "**Verify** the generated payload digests",
            "*Run* the deterministic suite",
        ):
            with self.subTest(msg=title):
                self.assertEqual(route_of(f"- [ ] T001 {title}"), ORCHESTRATOR_DIRECT)

    def test_a_leading_build_verb_is_the_documented_ambiguous_head(self) -> None:
        """``build`` reads both ways at the head, and verification wins.

        Anchoring branch (d) to the leading verb removes the keyword-anywhere
        misroutes, but a task that opens with ``Build`` still reaches
        ``orchestrator-direct`` even when it means implementation work. Rule 7
        in the phase-execution reference records this residual: an author who
        means implementation opens with ``Implement``, ``Add``, or ``Create``.
        """
        self.assertEqual(
            route_of("- [ ] T001 Build the export lead registry in read_only.py"),
            ORCHESTRATOR_DIRECT,
        )

    def test_an_unmatched_task_falls_back_to_the_implement_executor(self) -> None:
        self.assertEqual(
            route_of("- [ ] T001 Add the ledger posting module"),
            IMPLEMENT_EXECUTOR,
        )

    def test_a_backticked_identifier_does_not_route_the_task(self) -> None:
        """Inline code spans are names, not description words.

        ``check-prerequisites`` is a helper name, so the verify keyword
        ``check`` inside it must not send implementation work to
        ``orchestrator-direct``, the one branch that dispatches no agent.
        """
        agent = route_of(
            "- [ ] T001 [US1] Port and register `check-prerequisites` behavior "
            "in `speckit-pro/speckit_pro_runner/helpers/read_only.py`"
        )
        self.assertEqual(agent, IMPLEMENT_EXECUTOR)

    def test_a_backticked_path_does_not_outrank_a_plain_keyword(self) -> None:
        """The plain words decide, even when a code span holds a keyword.

        ``test`` inside the backticked file name used to win branch (b) and
        beat the ``run`` in the description itself.
        """
        agent = route_of(
            "- [ ] T001 Run the deterministic suite in "
            "`tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py`"
        )
        self.assertEqual(agent, ORCHESTRATOR_DIRECT)

    def test_a_bare_path_still_outranks_a_plain_verify_keyword(self) -> None:
        """Only code spans are stripped, so a bare path still carries keywords.

        ``test`` inside ``src/parser.test.ts`` is branch (b) and must beat the
        ``Run`` that would otherwise send this to ``orchestrator-direct``.
        """
        agent = route_of("- [ ] T001 Run the failing cases in src/parser.test.ts")
        self.assertEqual(agent, IMPLEMENT_EXECUTOR)

    def test_a_project_keyword_inside_a_code_span_does_not_reach_branch_a(self) -> None:
        agent = route_of(
            "- [ ] T001 Add the `checkout` module docs",
            project_agent_name="acme-developer",
            project_agent_keywords=["checkout"],
        )
        self.assertEqual(agent, IMPLEMENT_EXECUTOR)

    def test_the_first_matching_branch_wins(self) -> None:
        with self.subTest(msg="project agent beats a test keyword"):
            agent = route_of(
                "- [ ] T001 Add the checkout unit test",
                project_agent_name="acme-developer",
                project_agent_keywords=["checkout"],
            )
            self.assertEqual(agent, "acme-developer")
        with self.subTest(msg="a test keyword beats a research keyword"):
            agent = route_of("- [ ] T001 Research and unit test the parser")
            self.assertEqual(agent, IMPLEMENT_EXECUTOR)
        with self.subTest(msg="a research keyword beats a leading verification verb"):
            agent = route_of("- [ ] T001 Check the retry budget and investigate the API")
            self.assertEqual(agent, DOMAIN_RESEARCHER)
        with self.subTest(msg="a test keyword beats a leading verification verb"):
            agent = route_of("- [ ] T001 Check the parser unit test coverage")
            self.assertEqual(agent, IMPLEMENT_EXECUTOR)


class GroupingTests(unittest.TestCase):
    def test_consecutive_same_agent_parallel_tasks_form_one_run(self) -> None:
        payload, exit_code = partition(
            tasks_body(
                "- [ ] T001 [P] Add a unit test for the parser",
                "- [ ] T002 [P] Add a contract test for the writer",
                "- [ ] T003 [P] Add an integration test for the loader",
            )
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            payload["runs"],
            [
                {
                    "kind": "parallel",
                    "agent": IMPLEMENT_EXECUTOR,
                    "group": "Phase 1: Setup",
                    "tasks": ["T001", "T002", "T003"],
                    "waves": [["T001", "T002", "T003"]],
                }
            ],
        )

    def test_an_agent_change_flushes_the_open_parallel_run(self) -> None:
        payload, exit_code = partition(
            tasks_body(
                "- [ ] T001 [P] Add a unit test for the parser",
                "- [ ] T002 [P] Add a contract test for the writer",
                "- [ ] T003 [P] Research the upstream pagination contract",
                "- [ ] T004 [P] Investigate the retry semantics",
            )
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            [(run["kind"], run["agent"], run["tasks"]) for run in payload["runs"]],
            [
                ("parallel", IMPLEMENT_EXECUTOR, ["T001", "T002"]),
                ("parallel", DOMAIN_RESEARCHER, ["T003", "T004"]),
            ],
        )

    def test_an_untagged_task_flushes_the_run_and_becomes_a_singleton(self) -> None:
        payload, exit_code = partition(
            tasks_body(
                "- [ ] T001 [P] Add a unit test for the parser",
                "- [ ] T002 [P] Add a contract test for the writer",
                "- [ ] T003 Add the ledger posting module",
                "- [ ] T004 [P] Add a unit test for the ledger",
                "- [ ] T005 [P] Add a contract test for the ledger",
            )
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            [(run["kind"], run["tasks"]) for run in payload["runs"]],
            [
                ("parallel", ["T001", "T002"]),
                ("singleton", ["T003"]),
                ("parallel", ["T004", "T005"]),
            ],
        )

    def test_every_untagged_task_is_its_own_singleton_run(self) -> None:
        payload, exit_code = partition(
            tasks_body(
                "- [ ] T001 Add the ledger posting module",
                "- [ ] T002 Add the ledger reversal module",
            )
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            [(run["kind"], run["tasks"]) for run in payload["runs"]],
            [("singleton", ["T001"]), ("singleton", ["T002"])],
        )
        self.assertNotIn("waves", payload["runs"][0])

    def test_a_lone_parallel_task_degrades_to_a_singleton(self) -> None:
        payload, exit_code = partition(
            tasks_body(
                "- [ ] T001 [P] Add a unit test for the parser",
                "- [ ] T002 [P] Research the upstream pagination contract",
                "- [ ] T003 [P] Investigate the retry semantics",
            )
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            [(run["kind"], run["tasks"]) for run in payload["runs"]],
            [("singleton", ["T001"]), ("parallel", ["T002", "T003"])],
        )

    def test_a_parallel_run_never_straddles_a_phase_group(self) -> None:
        body = "\n".join(
            (
                "## Phase 1: Setup",
                "",
                "- [ ] T001 [P] Add a unit test for the parser",
                "",
                "## Phase 2: Foundational",
                "",
                "- [ ] T002 [P] Add a contract test for the writer",
                "- [ ] T003 [P] Add an integration test for the loader",
                "",
            )
        )
        payload, exit_code = partition(body)
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            [(run["kind"], run["group"], run["tasks"]) for run in payload["runs"]],
            [
                ("singleton", "Phase 1: Setup", ["T001"]),
                ("parallel", "Phase 2: Foundational", ["T002", "T003"]),
            ],
        )

    def test_a_subheading_does_not_break_a_parallel_run(self) -> None:
        body = "\n".join(
            (
                "## Phase 1: Setup",
                "",
                "- [ ] T001 [P] Add a unit test for the parser",
                "",
                "### The writer",
                "",
                "- [ ] T002 [P] Add a contract test for the writer",
                "",
            )
        )
        payload, exit_code = partition(body)
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            [(run["kind"], run["tasks"]) for run in payload["runs"]],
            [("parallel", ["T001", "T002"])],
        )

    def test_a_completed_task_keeps_its_place_in_the_partition(self) -> None:
        payload, exit_code = partition(
            tasks_body(
                "- [x] T001 [P] Add a unit test for the parser",
                "- [ ] T002 [P] Add a contract test for the writer",
            )
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["runs"][0]["tasks"], ["T001", "T002"])
        self.assertEqual(payload["task_count"], 2)

    def test_a_story_tag_does_not_change_the_partition(self) -> None:
        payload, exit_code = partition(
            tasks_body(
                "- [ ] T001 [P] [US1] Add a unit test for the parser",
                "- [ ] T002 [P] [US2] Add a contract test for the writer",
            )
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            [(run["kind"], run["tasks"]) for run in payload["runs"]],
            [("parallel", ["T001", "T002"])],
        )


class WaveTests(unittest.TestCase):
    def test_a_parallel_run_splits_into_order_preserving_waves(self) -> None:
        payload, exit_code = partition(
            tasks_body(
                "- [ ] T001 [P] Add a unit test for the parser",
                "- [ ] T002 [P] Add a unit test for the writer",
                "- [ ] T003 [P] Add a unit test for the loader",
                "- [ ] T004 [P] Add a unit test for the router",
                "- [ ] T005 [P] Add a unit test for the emitter",
            ),
            wave_size=2,
        )
        self.assertEqual(exit_code, 0)
        run = payload["runs"][0]
        self.assertEqual(run["tasks"], ["T001", "T002", "T003", "T004", "T005"])
        self.assertEqual(run["waves"], [["T001", "T002"], ["T003", "T004"], ["T005"]])
        self.assertEqual(payload["wave_size"], 2)

    def test_the_default_wave_size_is_the_conservative_runtime_default(self) -> None:
        payload, exit_code = partition(
            tasks_body(
                "- [ ] T001 [P] Add a unit test for the parser",
                "- [ ] T002 [P] Add a unit test for the writer",
                "- [ ] T003 [P] Add a unit test for the loader",
                "- [ ] T004 [P] Add a unit test for the router",
                "- [ ] T005 [P] Add a unit test for the emitter",
            )
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["wave_size"], 4)
        self.assertEqual(
            payload["runs"][0]["waves"],
            [["T001", "T002", "T003", "T004"], ["T005"]],
        )

    def test_a_wave_size_of_one_still_reports_a_parallel_run(self) -> None:
        payload, exit_code = partition(
            tasks_body(
                "- [ ] T001 [P] Add a unit test for the parser",
                "- [ ] T002 [P] Add a unit test for the writer",
            ),
            wave_size=1,
        )
        self.assertEqual(exit_code, 0)
        run = payload["runs"][0]
        self.assertEqual(run["kind"], "parallel")
        self.assertEqual(run["waves"], [["T001"], ["T002"]])


class RejectionTests(unittest.TestCase):
    def test_a_missing_tasks_file_is_an_input_error(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root).resolve()
            result = partition_phase7_tasks({"tasks_file": "tasks.md"}, root)
        self.assertEqual(int(result["exit_code"]), 2)
        self.assertIn("tasks_file", json.loads(result["stdout"])["error"])

    def test_a_missing_tasks_file_input_is_an_input_error(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            result = partition_phase7_tasks({}, Path(raw_root).resolve())
        self.assertEqual(int(result["exit_code"]), 2)

    def test_a_non_positive_wave_size_is_an_input_error(self) -> None:
        payload, exit_code = partition(
            tasks_body("- [ ] T001 [P] Add a unit test for the parser"),
            wave_size=0,
        )
        self.assertEqual(exit_code, 2)
        self.assertIn("wave_size", payload["error"])

    def test_project_agent_keywords_must_be_a_list_of_strings(self) -> None:
        payload, exit_code = partition(
            tasks_body("- [ ] T001 Add the ledger posting module"),
            project_agent_name="acme-developer",
            project_agent_keywords="checkout",
        )
        self.assertEqual(exit_code, 2)
        self.assertIn("project_agent_keywords", payload["error"])

    def test_a_duplicate_task_id_fails_the_partition(self) -> None:
        payload, exit_code = partition(
            tasks_body(
                "- [ ] T001 Add the ledger posting module",
                "- [ ] T001 Add the ledger reversal module",
            )
        )
        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["errors"][0]["code"], "duplicate_task_id")


class ContractTests(unittest.TestCase):
    def test_the_record_names_its_tool_and_inputs(self) -> None:
        payload, exit_code = partition(
            tasks_body("- [ ] T001 Add the ledger posting module")
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["tool"], "partition-phase7-tasks")
        self.assertEqual(payload["contract_version"], 1)
        self.assertEqual(payload["tasks_file"], "tasks.md")
        self.assertEqual(payload["task_count"], 1)
        self.assertEqual(payload["errors"], [])

    def test_an_empty_task_list_produces_no_runs(self) -> None:
        payload, exit_code = partition("## Phase 1: Setup\n\nNo tasks yet.\n")
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["runs"], [])
        self.assertEqual(payload["task_count"], 0)

    def test_tasks_before_any_heading_are_partitioned_without_a_group(self) -> None:
        payload, exit_code = partition(
            "- [ ] T001 [P] Add a unit test for the parser\n"
            "- [ ] T002 [P] Add a contract test for the writer\n"
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["runs"][0]["group"], None)
        self.assertEqual(payload["runs"][0]["tasks"], ["T001", "T002"])


def build_suite() -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    for case in (RoutingTests, GroupingTests, WaveTests, RejectionTests, ContractTests):
        suite.addTests(loader.loadTestsFromTestCase(case))
    return suite


def main() -> int:
    return run_counted(build_suite(), label="test-phase7-task-partition")


if __name__ == "__main__":
    raise SystemExit(main())
