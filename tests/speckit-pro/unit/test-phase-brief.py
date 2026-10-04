#!/usr/bin/env python3
"""Planning briefs through the runner's public helper dispatch seam."""

from pathlib import Path
import json
import os
import subprocess
import sys
from types import SimpleNamespace
import unittest

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO / "speckit-pro"), str(REPO / "tests/speckit-pro/lib")]
from speckit_pro_runner.helpers.registry import dispatch_helper  # noqa: E402
from test_result import run_counted  # noqa: E402
from host_skill_views import host_skill_root  # noqa: E402


class PhaseBriefTests(unittest.TestCase):
    def test_dispatch_input_names_the_action(self):
        cases = {"Specify": "Run the speckit-specify skill with:",
                 "Clarify": "Prepare a Clarify Question Set for:",
                 "Plan": "Run the speckit-plan skill with:",
                 "Checklist": "Run the speckit-checklist skill with:",
                 "Tasks": "Run the speckit-tasks skill with:",
                 "Analyze": "Run the speckit-analyze skill with:"}
        for phase, instruction in cases.items():
            with self.subTest(phase=phase):
                result = dispatch_helper(SimpleNamespace(
                    helper_id="phase-brief", operation="phase-brief", mode="read_only", request_id=None,
                    inputs={"phase": phase, "workflow_file": "docs/workflow.md", "feature_dir": "specs/example"},
                ))
                self.assertEqual(result["data"]["inputs"].get("instruction"), instruction)

    def test_payload_hosts_return_identical_briefs(self):
        for phase in ("Specify", "Clarify", "Plan", "Checklist", "Tasks", "Analyze"):
            with self.subTest(phase=phase):
                request = {"schema_version": "1.0", "helper_id": "phase-brief",
                           "operation": "phase-brief", "mode": "read_only",
                           "inputs": {"phase": phase, "workflow_file": "docs/workflow.md", "feature_dir": "specs/example"}}
                reports = []
                for host in ("claude", "codex"):
                    payload = REPO / "dist" / host / "speckit-pro"
                    done = subprocess.run([sys.executable, "-m", "speckit_pro_runner"],
                                          cwd=payload, env={**os.environ, "PYTHONPATH": str(payload)},
                                          input=json.dumps(request), text=True, capture_output=True, check=False)
                    self.assertEqual(done.returncode, 0, done.stderr + done.stdout)
                    reports.append(json.loads(done.stdout)["data"])
                self.assertEqual(reports[0], reports[1])
                self.assertEqual(reports[0], dispatch_helper(SimpleNamespace(**request, request_id=None))["data"])

    def test_invalid_requests_return_no_dispatch_facts(self):
        valid = {"phase": "Plan", "workflow_file": "docs/workflow.md", "feature_dir": "specs/example"}
        invalid = [{**valid, "phase": value} for value in ("Implement", "", "plan", [], None)]
        invalid += [{**valid, key: ""} for key in ("workflow_file", "feature_dir")]
        invalid += [{key: value for key, value in valid.items() if key != missing} for missing in valid]
        invalid += [{**valid, "model": "override"}]
        for inputs in invalid:
            with self.subTest(inputs=inputs):
                result = dispatch_helper(SimpleNamespace(helper_id="phase-brief", operation="phase-brief",
                                                        mode="read_only", request_id=None, inputs=inputs))
                self.assertEqual(result["status"], "input_error")
                self.assertEqual(result["data"], {})

    def test_prompt_sections_match_the_workflow_template(self):
        template = (REPO / "speckit-pro/skills/speckit-coach/templates/workflow-template.md").read_text()
        for phase in ("Specify", "Clarify", "Plan", "Checklist", "Tasks", "Analyze"):
            with self.subTest(phase=phase):
                result = dispatch_helper(SimpleNamespace(
                    helper_id="phase-brief", operation="phase-brief", mode="read_only", request_id=None,
                    inputs={"phase": phase, "workflow_file": "docs/workflow.md", "feature_dir": "specs/example"},
                ))
                self.assertIn("\n### " + result["data"]["inputs"]["prompt_section"] + "\n", template)

    def test_both_hosts_dispatch_from_brief(self):
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                skill = (host_skill_root(host) / "speckit-autopilot/SKILL.md").read_text()
                loop = skill.split("## Step 2: Main Execution Loop", 1)[1]
                self.assertIn("helper_id=phase-brief operation=phase-brief mode=read_only", loop)
                self.assertIn("brief.agent", loop)
                self.assertIn("brief.inputs", loop)
                self.assertIn("brief.readable_files", loop)
                self.assertIn("gate=brief.gate", loop)
                dispatch = ('Agent(subagent_type: "speckit-pro:" + brief.agent' if host == "claude"
                            else "spawn_agent(agent_type=brief.agent")
                self.assertIn(dispatch, loop)
                self.assertIn("brief.inputs.instruction + workflow prompt", loop)

    def test_six_planning_briefs(self):
        cases = (
            ("Specify", "phase-executor", "G1", []),
            ("Clarify", "clarify-executor", "G2", ["spec.md"]),
            ("Plan", "phase-executor", "G3", ["spec.md"]),
            ("Checklist", "checklist-executor", "G4", ["spec.md", "plan.md", "checklists/"]),
            ("Tasks", "phase-executor", "G5", ["spec.md", "plan.md", "research.md", "data-model.md", "contracts/", "quickstart.md"]),
            ("Analyze", "analyze-executor", "G6", ["spec.md", "plan.md", "tasks.md", "checklists/"]),
        )
        for phase, agent, gate, artifacts in cases:
            with self.subTest(phase=phase):
                result = dispatch_helper(SimpleNamespace(
                    helper_id="phase-brief", operation="phase-brief", mode="read_only", request_id=None,
                    inputs={"phase": phase, "workflow_file": "docs/workflow.md", "feature_dir": "specs/example"},
                ))
                self.assertEqual(result["status"], "ok", result)
                brief = result["data"]
                self.assertEqual(brief["agent"], agent)
                self.assertEqual(brief["gate"], gate)
                self.assertEqual(brief["inputs"]["workflow_file"], "docs/workflow.md")
                self.assertEqual(brief["inputs"]["feature_dir"], "specs/example")
                self.assertEqual(brief["readable_files"], ["docs/workflow.md", ".specify/memory/constitution.md"] + ["specs/example/" + name for name in artifacts])
                self.assertEqual([brief[key] for key in ("slices", "waves", "model", "hooks")], [[], [], None, []])


if __name__ == "__main__":
    sys.exit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(PhaseBriefTests), label="test-phase-brief"))
