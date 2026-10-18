#!/usr/bin/env python3
"""Nested mode runs each planning phase in a phase driver; a phase advances only on a passing re-verify (ADR 0026)."""

from __future__ import annotations

import re
import sys
import tomllib
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
sys.path[:0] = [str(REPO_ROOT / "speckit-pro"), str(TEST_DIR.parent / "lib")]

from host_skill_views import host_skill_root  # noqa: E402
from script_loader import load_script  # noqa: E402
from test_result import run_counted  # noqa: E402

from speckit_pro_runner.agent_inventory import AGENT_INVENTORY  # noqa: E402

BRIEF = load_script("phase_brief_cases", TEST_DIR / "test-phase-brief.py")
ENVELOPE = load_script("phase_envelope_cases", TEST_DIR / "test-phase-envelope.py")

PHASES = ("Specify", "Clarify", "Plan", "Checklist", "Tasks", "Analyze")
INNER_EXECUTORS = {"Clarify": "clarify-executor", "Checklist": "checklist-executor", "Analyze": "analyze-executor"}
FEATURE = "specs/example"
DRIVER_READ_LIMIT_BYTES = 8_000


def brief(phase: str, **extra: object) -> dict:
    inputs = {"phase": phase, "workflow_file": "docs/workflow.md", "feature_dir": FEATURE, **extra}
    with BRIEF.project():
        return BRIEF.dispatch_brief(inputs)


class NestedBriefTests(unittest.TestCase):
    def test_a_nested_plan_stage_dispatches_one_phase_driver_per_phase(self) -> None:
        dispatched = [brief(phase, mode="nested") for phase in PHASES]
        self.assertEqual(["ok"] * 6, [result["status"] for result in dispatched])
        data = [result["data"] for result in dispatched]
        self.assertEqual(["phase-executor"] * 6, [item["agent"] for item in data])
        self.assertEqual([INNER_EXECUTORS.get(phase) for phase in PHASES], [item["inner_agent"] for item in data])
        self.assertEqual(["nested"] * 6, [item["mode"] for item in data])

    def test_the_root_brief_carries_no_inner_dispatch_material(self) -> None:
        for phase in PHASES:
            data = brief(phase, mode="nested")["data"]
            with self.subTest(phase=phase):
                self.assertEqual([], data["slices"])
                self.assertEqual([], data["waves"])

    def test_the_driver_reads_the_inner_dispatch_facts_from_the_flat_brief(self) -> None:
        for phase, inner in INNER_EXECUTORS.items():
            with self.subTest(phase=phase):
                self.assertEqual(inner, brief(phase, mode="flat")["data"]["agent"])
                self.assertTrue(brief(phase, mode="flat")["data"]["slices"])

    def test_flat_mode_is_unchanged(self) -> None:
        for phase in PHASES:
            with self.subTest(phase=phase):
                implicit = brief(phase)["data"]
                explicit = brief(phase, mode="flat")["data"]
                for data in (implicit, explicit):  # run-owned Tasks paths and directory identities differ per project
                    data["inputs"].pop("tasks_output", None)
                self.assertEqual(BRIEF.comparable_brief(implicit), BRIEF.comparable_brief(explicit))
                self.assertNotIn("mode", implicit)
                self.assertNotIn("inner_agent", implicit)

    def test_nested_mode_refuses_wave_inputs_and_unknown_modes(self) -> None:
        refused = [brief("Checklist", mode="nested", domains=["security"], max_agents=2),
                   brief("Clarify", mode="nested", items=[{"line": "x"}], max_agents=2),
                   brief("Plan", mode="deep"), brief("Plan", mode=True)]
        self.assertEqual(["input_error"] * 4, [result["status"] for result in refused])

    def test_the_driver_model_follows_the_phase_executor_row(self) -> None:
        role = next(role for role in AGENT_INVENTORY["roles"] if role["name"] == "phase-executor")
        model = brief("Checklist", mode="nested")["data"]["model"]
        self.assertEqual(role["claude_code"]["model"], model["claude"]["model"])
        self.assertEqual(role["claude_code"]["effort"], model["claude"]["effort"])


class AdvanceTests(unittest.TestCase):
    """The runner, not skill prose, says whether a phase may advance."""

    def assert_reverified_advance(self, expected: bool, *, expected_status=None, **project_inputs):
        result = ENVELOPE.verify_project(ENVELOPE.good_envelope(), **project_inputs)
        if expected_status is not None:
            self.assertEqual(expected_status, result["status"])
        self.assertIs(expected, result["data"]["advance"])

    def test_a_passing_re_verify_advances(self) -> None:
        self.assert_reverified_advance(True, expected_status="ok")

    def test_a_failing_re_verify_does_not_advance(self) -> None:
        cases = {"claimed gate fails on disk": ENVELOPE.good_envelope(gates=[{"id": "G1", "result": "fail"}]),
                 "driver reports blocked": ENVELOPE.good_envelope(status="blocked", blocker="needs input"),
                 "artifact missing": ENVELOPE.good_envelope(artifacts=[f"{FEATURE}/absent.md"]),
                 "malformed envelope": {"phase": "Specify"}}
        for label, envelope in cases.items():
            with self.subTest(label), ENVELOPE.project():
                result = ENVELOPE.verify(envelope)
                self.assertEqual("expected_failure", result["status"])
                self.assertIs(False, result["data"]["advance"])

    def test_a_failure_on_disk_evidence_does_not_advance(self) -> None:
        self.assert_reverified_advance(False, spec_text="# Spec\n\n[NEEDS CLARIFICATION] open\n")


class OptionalTasksHookFixture(unittest.TestCase):
    AUDIT = {"extension": "audit", "command": "speckit.audit.run", "event": "after_tasks"}

    def tasks_hooks(self, *, payloads=False, audit_enabled="true", **inputs):
        configuration = BRIEF.extensions_yml(BRIEF.hook("before_tasks", "speckit.audit.run", "audit"),
                                            BRIEF.hook("after_tasks", "speckit.audit.run", "audit", enabled=audit_enabled),
                                            BRIEF.hook("after_tasks", "speckit.other.run", "other"))
        with BRIEF.project(configuration):
            request = {"phase": "Tasks", "mode": "nested", "workflow_file": "docs/workflow.md", "feature_dir": FEATURE, **inputs}
            return BRIEF.payload_briefs(request, include_status=True) if payloads else BRIEF.dispatch_brief(request)


class OptionalTasksHookTests(OptionalTasksHookFixture):
    def test_confirmed_optional_after_tasks_hook_is_selected_for_the_driver(self):
        result = self.tasks_hooks(confirmed_after_tasks_hooks=[self.AUDIT])
        self.assertEqual(result["status"], "ok", result)
        handoff = result["data"]["after_tasks_hooks"]
        self.assertEqual([hook["command"] for hook in handoff["run"]], ["speckit.audit.run"])
        self.assertEqual([hook["command"] for hook in handoff["skip"]], ["speckit.other.run"])
        self.assertEqual(handoff["run"][0]["event"], "after_tasks")

    def test_unconfirmed_optional_after_tasks_hooks_are_selected_for_skip(self):
        handoff = self.tasks_hooks()["data"]["after_tasks_hooks"]
        self.assertEqual(handoff["run"], [])
        self.assertEqual([hook["command"] for hook in handoff["skip"]], ["speckit.audit.run", "speckit.other.run"])

    def test_confirmations_match_each_identity_field_and_never_another_event(self):
        for field, value in (("extension", "other"), ("command", "speckit.other.run"), ("event", "before_tasks"),
                             ("command", "speckit.audit.run ")):
            result = self.tasks_hooks(confirmed_after_tasks_hooks=[{**self.AUDIT, field: value}])
            with self.subTest(field=field, value=value):
                self.assertEqual(result["status"], "input_error")
                self.assertEqual(result["data"], {})

    def test_malformed_or_blanket_approvals_never_dispatch_hooks(self):
        for value in (True, None, "approved", {}, [True], [{"approved": True}], [{**self.AUDIT, "all_events": True}],
                      [{**self.AUDIT, "command": None}]):
            with self.subTest(value=value):
                self.assertEqual(self.tasks_hooks(confirmed_after_tasks_hooks=value)["status"], "input_error")

    def test_repeated_exact_confirmations_select_one_run(self):
        handoff = self.tasks_hooks(confirmed_after_tasks_hooks=[self.AUDIT, self.AUDIT])["data"]["after_tasks_hooks"]
        self.assertEqual(len(handoff["run"]), 1)
        self.assertEqual(len(handoff["skip"]), 1)

    def test_confirmation_input_is_confined_to_nested_tasks(self):
        results = [self.tasks_hooks(mode="flat", confirmed_after_tasks_hooks=[self.AUDIT]),
                   self.tasks_hooks(phase="Plan", confirmed_after_tasks_hooks=[self.AUDIT])]
        self.assertEqual([result["status"] for result in results], ["input_error", "input_error"])


class TasksHookHandoffTests(OptionalTasksHookFixture):
    def test_shipped_hosts_select_the_same_confirmed_run_and_unconfirmed_skip(self):
        reports = self.tasks_hooks(payloads=True, confirmed_after_tasks_hooks=[self.AUDIT])
        self.assertEqual([report["status"] for report in reports], ["ok", "ok"])
        self.assertEqual(reports[0]["data"]["after_tasks_hooks"], reports[1]["data"]["after_tasks_hooks"])
        self.assertEqual(len(reports[0]["data"]["after_tasks_hooks"]["run"]), 1)

    def test_confirmation_cannot_override_a_disabled_hook(self):
        refused = self.tasks_hooks(audit_enabled="false", confirmed_after_tasks_hooks=[self.AUDIT])
        self.assertEqual(refused["status"], "input_error")
        self.assertEqual(refused["data"], {})

    def test_confirmations_survive_a_second_brief_with_the_same_g4_binding(self):
        configuration = BRIEF.extensions_yml(BRIEF.hook("after_tasks", "speckit.audit.run", "audit"))
        with BRIEF.project(configuration):
            request = BRIEF.with_tasks_fixture_evidence({"phase": "Tasks", "mode": "nested",
                                                        "workflow_file": "docs/workflow.md", "feature_dir": FEATURE})
            initial = BRIEF.dispatch_brief(request)
            confirmed = BRIEF.dispatch_brief({**request, "confirmed_after_tasks_hooks": [self.AUDIT]})
        self.assertEqual((initial["status"], confirmed["status"]), ("ok", "ok"))
        self.assertEqual(initial["data"]["after_tasks_hooks"]["run"], [])
        self.assertEqual(len(confirmed["data"]["after_tasks_hooks"]["run"]), 1)
        self.assertEqual(initial["data"]["inputs"]["tasks_output"]["feature_identity"],
                         confirmed["data"]["inputs"]["tasks_output"]["feature_identity"])


def nested_section(host: str) -> str:
    """The nested-mode part of the autopilot skill as this host loads it, whitespace folded."""
    text = (host_skill_root(host) / "speckit-autopilot" / "SKILL.md").read_text(encoding="utf-8")
    start = text.index("### Nested mode: phase drivers")
    return " ".join(text[start:text.index("\n## ", start)].split())


# What the root must say in nested mode, and what each host's section must leave out.
ROOT_RULES = ("validate-gate` G4", "`feature_identity`", "mode=nested", "brief.agent", "reads only the envelope", "never reads a planning artifact",
              "helper_id=verify-phase-envelope", "data.advance", "never advance",
              "`expected_phase` (the root's requested phase from `brief.phase`, never from the envelope)")
HOST_TOOLS = {"claude": ("`Agent`", "spawn_agent"), "codex": ("spawn_agent", "`Agent`")}


class SkillContractTests(unittest.TestCase):
    def test_both_hosts_delegate_confirmed_tasks_hooks_with_the_binding_and_record_skips(self) -> None:
        root_needles = ("confirmed_after_tasks_hooks", "brief.after_tasks_hooks", "never publishes again")
        driver_needles = ("brief.after_tasks_hooks.run", "brief.after_tasks_hooks.skip", "optional_hook_run",
                          "authority_action_skipped", "optional_hooks_run", "optional_hooks_skipped", "read-tasks-output")
        for host in HOST_TOOLS:
            root = nested_section(host)
            reference = (host_skill_root(host) / "speckit-autopilot/references/phase-driver.md").read_text(encoding="utf-8")
            driver = reference[reference.index("## Nested-mode phase driver"):reference.index("## Phase executor summary")]
            with self.subTest(host=host):
                self.assertTrue(all(needle in root for needle in root_needles), root)
                self.assertTrue(all(needle in driver for needle in driver_needles), driver)
                self.assertNotIn("So it skips optional `after_tasks`", root)

    def test_each_host_roots_dispatch_a_driver_and_advance_only_on_the_runner_verdict(self) -> None:
        for host, (own_tool, other_tool) in HOST_TOOLS.items():
            section = nested_section(host)
            with self.subTest(host=host):
                for needle in (*ROOT_RULES, own_tool, *(("`$` plus `brief.inputs.skill`", 'fork_turns="none"') if host == "codex" else ())):
                    self.assertIn(needle, section)
                self.assertNotIn(other_tool, section)

    def test_publication_and_formal_checks_finish_before_verification(self) -> None:
        for host in HOST_TOOLS:
            section = nested_section(host)
            verify = section.index("Then request `helper_id=verify-phase-envelope")
            with self.subTest(host=host):
                self.assertLess(section.index("publish-tasks-output"), verify)
                self.assertLess(section.index("formal-check"), verify)

    def test_the_nesting_preflight_no_longer_says_drivers_are_pending(self) -> None:
        for host in HOST_TOOLS:
            text = (host_skill_root(host) / "speckit-autopilot" / "SKILL.md").read_text(encoding="utf-8")
            self.assertNotIn("until they ship", text, host)


class DriverAgentTests(unittest.TestCase):
    def test_both_host_agents_define_the_driver_and_dispatch_only_inner_executors(self) -> None:
        source = (REPO_ROOT / "speckit-pro/agents/phase-executor.md").read_text(encoding="utf-8")
        generated = tomllib.loads((REPO_ROOT / "speckit-pro/codex-agents/phase-executor.toml").read_text(encoding="utf-8"))
        needles = ("Phase driver", "phase-envelope/v1", "mode=flat", "2,048", "never dispatch `phase-executor`",
                   *INNER_EXECUTORS.values())
        for host, text in (("claude", source), ("codex", generated["developer_instructions"])):
            with self.subTest(host=host):
                self.assertIn("phase-driver.md#nested-mode-phase-driver", text)
                reference = (host_skill_root(host) / "speckit-autopilot/references/phase-driver.md").read_text(encoding="utf-8")
                start = reference.index("## Nested-mode phase driver")
                text += reference[start:reference.index("\n## ", start + 1)]
                for needle in needles:
                    self.assertIn(needle, text)

    def test_the_driver_reads_only_small_references_at_start(self) -> None:
        """A driver loads each reference the agent names in full, so each must stay small (issue 1308)."""
        source = (REPO_ROOT / "speckit-pro/agents/phase-executor.md").read_text(encoding="utf-8")
        generated = tomllib.loads((REPO_ROOT / "speckit-pro/codex-agents/phase-executor.toml").read_text(encoding="utf-8"))
        for host, text in (("claude", source), ("codex", generated["developer_instructions"])):
            names = set(re.findall(r"<plugin-root>/skills/speckit-autopilot/references/([\w-]+\.md)", text))
            with self.subTest(host=host):
                self.assertTrue(names, "the agent must name its reference files")
                for name in sorted(names):
                    size = (host_skill_root(host) / "speckit-autopilot/references" / name).stat().st_size
                    self.assertLessEqual(size, DRIVER_READ_LIMIT_BYTES, f"{name} is {size} bytes")


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-phase-driver"))
