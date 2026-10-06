#!/usr/bin/env python3
"""Planning briefs through the runner's public helper dispatch seam."""

from pathlib import Path
from itertools import product
import json
import os
import subprocess
import sys
import tempfile
import tomllib
from unittest.mock import patch
from types import SimpleNamespace
import unittest

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO / "speckit-pro"), str(REPO / "tests/speckit-pro/lib")]
from speckit_pro_runner.helpers import phase_brief
from speckit_pro_runner.helpers.registry import dispatch_helper  # noqa: E402
from test_result import run_counted  # noqa: E402
from host_skill_views import host_skill_root  # noqa: E402


def dispatch_brief(inputs, request_id=None):
    """Exercise the public dispatch seam with a complete caller-owned input set."""
    return dispatch_helper(SimpleNamespace(helper_id="phase-brief", operation="phase-brief",
                                           mode="read_only", request_id=request_id, inputs=inputs))


REFERENCES = REPO / "speckit-pro/skills/speckit-autopilot/references"
WHOLE_REFERENCES = ("capability-discovery.md", "grounding.md", "execution-efficiency.md", "consensus-protocol.md")
SLICE_AGENTS = ("clarify-executor", "checklist-executor", "analyze-executor")
UNSUPPORTED_SEPARATORS = ("\r", "\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029")


def reference_probe(root, references, cases):
    """Run the section and dispatch seams using the selected shipped runner."""
    program = '''
import json, sys, tempfile
from pathlib import Path
from types import SimpleNamespace
from speckit_pro_runner.helpers import phase_brief
from speckit_pro_runner.helpers.registry import dispatch_helper
references, cases = json.load(sys.stdin)
reports = []
with tempfile.TemporaryDirectory() as directory:
    phase_brief.REFERENCES = Path(directory)
    for case in cases:
        for name, text in references.items():
            (Path(directory) / name).write_bytes(text.encode("utf-8"))
        (Path(directory) / case["name"]).write_bytes(case["text"].encode("utf-8"))
        try:
            section = phase_brief.reference_section(case["name"], case["heading"])
            report = {"section": section}
        except ValueError as error:
            report = {"error": str(error)}
        report["dispatch"] = []
        for phase in ("Clarify", "Checklist", "Analyze"):
            inputs = {"phase": phase, "workflow_file": "docs/workflow.md", "feature_dir": "specs/example"}
            request = SimpleNamespace(helper_id="phase-brief", operation="phase-brief", mode="read_only",
                                      request_id="encoding-probe", inputs=inputs)
            report["dispatch"].append(dispatch_helper(request))
        reports.append(report)
print(json.dumps(reports))
'''
    done = subprocess.run([sys.executable, "-c", program], cwd=root,
                          env={**os.environ, "PYTHONPATH": str(root)},
                          input=json.dumps([references, cases]), text=True, capture_output=True, check=False)
    if done.returncode:
        raise AssertionError(done.stderr + done.stdout)
    return json.loads(done.stdout)


def reference_encoding_cases(separators):
    """Place each boundary fixture in every named slice's reference window."""
    references = {name: "".join("## " + heading + "\nsafe\n" for heading in headings)
                  for name, headings in phase_brief.EXECUTOR_SLICES}
    windows = [(name, heading) for name, headings in phase_brief.EXECUTOR_SLICES for heading in headings]
    markers = {
        "equal": ("## Next\n", ""),
        "higher": ("# Next\n", ""),
        "backtick": ("```\n## Hidden\nkept\n```\n", "\n```\n## Hidden\nkept\n```"),
        "tilde": ("~~~\n## Hidden\nkept\n~~~\n", "\n~~~\n## Hidden\nkept\n~~~"),
    }
    cases = []
    for (name, heading), separator, (marker, (body, tail)) in product(windows, separators, markers.items()):
        target = "## " + heading + "\nsafe\n"
        replacement = "## " + heading + "\nsafe" + separator + body + "## Excluded\nEXCLUDED\n"
        text = references[name].replace(target, replacement)
        if separator in ("\n", "\r\n"):
            text = text.replace("safe", "safe\ttext").replace("\r\n", "\n").replace("\n", separator)
        cases.append({"name": name, "heading": heading, "text": text, "separator": separator, "marker": marker,
                      "expected": "## " + heading + "\nsafe\ttext" + tail})
    return references, cases


RUNNER_ROOTS = (("source", REPO / "speckit-pro"), ("claude", REPO / "dist/claude/speckit-pro"),
                ("codex", REPO / "dist/codex/speckit-pro"))


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
                result = dispatch_brief({"phase": phase, "workflow_file": "docs/workflow.md", "feature_dir": "specs/example"})
                self.assertEqual(result["data"]["inputs"].get("instruction"), instruction)
                skill = None if phase == "Clarify" else "speckit-" + phase.lower()
                self.assertEqual(result["data"]["inputs"].get("skill"), skill)

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
                self.assertEqual(reports[0], dispatch_brief(request["inputs"])["data"])

    def test_invalid_requests_return_no_dispatch_facts(self):
        valid = {"phase": "Plan", "workflow_file": "docs/workflow.md", "feature_dir": "specs/example"}
        invalid = [{**valid, "phase": value} for value in ("Implement", "", "plan", [], None)]
        invalid += [{**valid, key: ""} for key in ("workflow_file", "feature_dir")]
        invalid += [{**valid, "feature_dir": value} for value in ("/", "///")]
        invalid += [{key: value for key, value in valid.items() if key != missing} for missing in valid]
        invalid += [{**valid, "model": "override"}]
        for inputs in invalid:
            with self.subTest(inputs=inputs):
                result = dispatch_brief(inputs)
                self.assertEqual(result["status"], "input_error")
                self.assertEqual(result["data"], {})

    def test_unsafe_paths_return_no_dispatch_facts(self):
        valid = {"phase": "Plan", "workflow_file": "docs/workflow.md", "feature_dir": "specs/example"}
        cases = [("feature_dir", value) for value in (
            "../example", "specs/../../example", "specs/..", r"specs\..\example",
            "/specs/example", "//server/specs", r"C:\specs\example", r"C:specs\example", r"\specs\example",
        )]
        cases += [("workflow_file", value) for value in ("../workflow.md", "docs/../workflow.md", r"docs\..\workflow.md")]
        for key in ("feature_dir", "workflow_file"):
            for control in ("\n", "\r", "\t", "\x00", "\x1f", "\x7f", "\x85", "\u2028", "\u2029"):
                cases.extend((key, value) for value in (control + valid[key], valid[key] + control, "docs/" + control + "example"))
        for key, value in cases:
            with self.subTest(key=key, value=value):
                result = dispatch_brief({**valid, key: value}, request_id="unsafe-path")
                self.assertEqual(result["status"], "input_error")
                self.assertEqual(result["data"], {})
                self.assertEqual(result["request_id"], "unsafe-path")
                self.assertEqual(result["diagnostics"][0]["code"], "invalid_phase_brief")

    def test_loaded_commands_can_read_extension_configuration(self):
        for phase in ("Specify", "Clarify", "Plan", "Checklist", "Tasks", "Analyze"):
            with self.subTest(phase=phase):
                result = dispatch_brief({"phase": phase, "workflow_file": "docs/workflow.md", "feature_dir": "specs/example"})
                self.assertIn(".specify/extensions.yml", result["data"]["readable_files"])

    def test_safe_path_text_is_preserved(self):
        for feature, workflow in (("specs/example/", "docs/workflow.md"),
                                  ("specs/version..two", "/workflow.md"),
                                  (r"specs\example", r"C:\docs\workflow.md")):
            with self.subTest(feature=feature, workflow=workflow):
                result = dispatch_brief({"phase": "Plan", "workflow_file": workflow, "feature_dir": feature})
                self.assertEqual(result["status"], "ok")
                self.assertEqual(result["data"]["inputs"]["feature_dir"], feature.rstrip("/"))
                self.assertEqual(result["data"]["inputs"]["workflow_file"], workflow)

    def test_prompt_sections_match_the_workflow_template(self):
        template = (REPO / "speckit-pro/skills/speckit-coach/templates/workflow-template.md").read_text()
        for phase in ("Specify", "Clarify", "Plan", "Checklist", "Tasks", "Analyze"):
            with self.subTest(phase=phase):
                result = dispatch_brief({"phase": phase, "workflow_file": "docs/workflow.md", "feature_dir": "specs/example"})
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
                if host == "codex":
                    self.assertIn('"$" + brief.inputs.skill', loop)

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
                result = dispatch_brief({"phase": phase, "workflow_file": "docs/workflow.md", "feature_dir": "specs/example"})
                self.assertEqual(result["status"], "ok", result)
                brief = result["data"]
                self.assertEqual(set(brief), {"schema_version", "phase", "agent", "inputs", "readable_files",
                                              "gate", "slices", "waves", "model", "hooks"})
                self.assertEqual(brief["schema_version"], "phase-brief/v1")
                self.assertEqual(brief["phase"], phase)
                self.assertEqual(set(brief["inputs"]), {"workflow_file", "feature_dir", "instruction", "skill", "prompt_section"})
                self.assertEqual(brief["agent"], agent)
                self.assertEqual(brief["gate"], gate)
                self.assertEqual(brief["inputs"]["workflow_file"], "docs/workflow.md")
                self.assertEqual(brief["inputs"]["feature_dir"], "specs/example")
                self.assertEqual(brief["readable_files"], ["docs/workflow.md", ".specify/memory/constitution.md", ".specify/extensions.yml"] + ["specs/example/" + name for name in artifacts])
                self.assertEqual([brief[key] for key in ("waves", "hooks")], [[], []])
                self.assertEqual(bool(brief["slices"]), agent in SLICE_AGENTS)


class PhaseBriefModelTests(unittest.TestCase):
    def test_brief_names_the_model_for_each_dispatch(self):
        # The owner's plan-stage table (issue 1150); Specify and Tasks run phase-executor below its Plan default.
        sonnet, plan_claude = {"model": "sonnet", "effort": "high"}, {"model": "opus", "effort": "high"}
        sol_medium, sol_high = {"model": "gpt-6-sol", "effort": "medium"}, {"model": "gpt-6-sol", "effort": "high"}
        cases = (("Specify", sonnet, sol_medium), ("Clarify", sonnet, sol_medium), ("Plan", plan_claude, sol_high),
                 ("Checklist", sonnet, sol_medium), ("Tasks", sonnet, sol_medium), ("Analyze", sonnet, sol_medium))
        for phase, claude, codex in cases:
            with self.subTest(phase=phase):
                brief = dispatch_brief({"phase": phase, "workflow_file": "docs/workflow.md", "feature_dir": "specs/example"})["data"]
                self.assertEqual(brief["model"], {"claude": claude, "codex": codex})

    def test_both_hosts_dispatch_the_briefed_model(self):
        needles = {"claude": ("model: brief.model.claude.model",),
                   "codex": ("model=brief.model.codex.model", "reasoning_effort=brief.model.codex.effort", 'fork_turns="none"')}
        for host, expected in needles.items():
            with self.subTest(host=host):
                skill = (host_skill_root(host) / "speckit-autopilot/SKILL.md").read_text()
                loop = skill.split("## Step 2: Main Execution Loop", 1)[1]
                for needle in expected:
                    self.assertIn(needle, loop)
                if host == "codex":
                    self.assertNotIn("model_reasoning_effort=", loop)


class CodexEffectiveEffortTests(unittest.TestCase):
    def test_codex_dispatch_runs_the_effort_the_table_names(self):
        # Custom-file effort wins over explicit spawn effort, which wins over [agents] defaults.
        # https://learn.chatgpt.com/docs/agent-configuration/subagents#custom-agents
        # This is a static configuration check, not a live Codex runtime precedence test.
        table = {"Specify": "medium", "Clarify": "medium", "Plan": "high", "Checklist": "medium", "Tasks": "medium", "Analyze": "medium"}
        for phase, expected in table.items():
            with self.subTest(phase=phase):
                brief = dispatch_brief({"phase": phase, "workflow_file": "docs/workflow.md", "feature_dir": "specs/example"})["data"]
                agent = tomllib.loads((REPO / "speckit-pro/codex-agents" / (brief["agent"] + ".toml")).read_text())
                self.assertEqual(agent.get("model_reasoning_effort", brief["model"]["codex"]["effort"]), expected)


class RetryLadderTopRungTests(unittest.TestCase):
    def test_third_rung_stays_the_strongest_model_at_max_effort(self):
        # ADR 0004: the plan-stage table lowers executor effort; a failing check still escalates to the top.
        from speckit_pro_runner.helpers import run_finalization
        rung = "strongest model at max effort"
        self.assertIn(rung, (REPO / "docs/adr/0004-retry-ladder.md").read_text())
        self.assertIn(rung, (REFERENCES / "stop-policy.md").read_text())
        self.assertIn(rung, run_finalization._tier_steps("tier3"))


class PhaseBriefSliceTests(unittest.TestCase):
    def test_invalid_structure_returns_no_dispatch_material(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(phase_brief, "REFERENCES", Path(directory)):
            path = Path(directory) / "capability-discovery.md"
            path.write_text("## Capability Categories\nbody\n## Next\nSetext\n===\n")
            result = dispatch_brief({"phase": "Clarify", "workflow_file": "docs/workflow.md", "feature_dir": "specs/example"})
        self.assertEqual(result["status"], "internal_failure")
        self.assertEqual(result["data"], {})
        self.assertIn("setext underline", result["diagnostics"][0]["message"])
        self.assertNotIn(directory, result["diagnostics"][0]["message"])

    def test_payload_hosts_enforce_reference_structure(self):
        expected = "## Target\n<!--\n## Hidden\n```\n-->\nbody\t```"
        program = ("import json,sys; from pathlib import Path; "
                   "from speckit_pro_runner.helpers import phase_brief; "
                   "phase_brief.REFERENCES=Path(sys.argv[1]); "
                   "print(json.dumps(phase_brief.reference_section('sample.md','Target')))")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.md"
            for host in ("claude", "codex"):
                payload = REPO / "dist" / host / "speckit-pro"
                for invalid in (False, True):
                    with self.subTest(host=host, invalid=invalid):
                        text = expected + "\n## Next\n" + ("Setext\n===\n" if invalid else "excluded\n")
                        path.write_bytes(text.replace("\n", "\r\n").encode())
                        done = subprocess.run([sys.executable, "-c", program, directory], cwd=payload,
                                              env={**os.environ, "PYTHONPATH": str(payload)},
                                              text=True, capture_output=True, check=False)
                        if invalid:
                            self.assertNotEqual(done.returncode, 0)
                            self.assertIn("setext underline", done.stderr)
                        else:
                            self.assertEqual(done.returncode, 0, done.stderr)
                            self.assertEqual(json.loads(done.stdout), expected)

    def test_setext_underlines_are_refused_in_reference_structure(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(phase_brief, "REFERENCES", Path(directory)):
            path = Path(directory) / "sample.md"
            for underline in ("=", "---", "   === \t", "  -\t"):
                for position in ("before", "inside", "after"):
                    with self.subTest(underline=underline, position=position):
                        invalid = "Setext\n" + underline + "\n"
                        parts = {"before": invalid + "## Target\nbody\n## Next\n",
                                 "inside": "## Target\nbody\n\n" + invalid + "tail\n",
                                 "after": "## Target\nbody\n## Next\n" + invalid}
                        path.write_text(parts[position])
                        with self.assertRaisesRegex(ValueError, "setext underline.*ATX"):
                            phase_brief.reference_section("sample.md", "Target")
            for body in ("```\nSetext\n===\n```", "<!--\nSetext\n---\n-->",
                         "    ===", "= =", "- - -", "***"):
                with self.subTest(body=body):
                    expected = "## Target\n" + body
                    path.write_text(expected + "\n## Next\n")
                    self.assertEqual(phase_brief.reference_section("sample.md", "Target"), expected)

    def test_only_lf_and_crlf_split_reference_lines(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(phase_brief, "REFERENCES", Path(directory)):
            path = Path(directory) / "sample.md"
            for separator in ("\n", "\r\n"):
                with self.subTest(separator=repr(separator)):
                    path.write_bytes(separator.join(("## Target", "body", "## Next", "excluded")).encode())
                    self.assertEqual(phase_brief.reference_section("sample.md", "Target"), "## Target\nbody")

    def test_comments_hide_headings_and_fences(self):
        cases = (
            "<!--\n## Hidden\n```\n~~~\n-->\nkept",
            "   <!-- ## Hidden --> ```\nkept",
            "```\n<!--\n```\nkept",
        )
        with tempfile.TemporaryDirectory() as directory, patch.object(phase_brief, "REFERENCES", Path(directory)):
            for body in cases:
                with self.subTest(body=body):
                    expected = "## Target\n" + body
                    (Path(directory) / "sample.md").write_text(expected + "\n## Next\nexcluded\n")
                    self.assertEqual(phase_brief.reference_section("sample.md", "Target"), expected)
            (Path(directory) / "sample.md").write_text("<!--\n## Target\n```\n-->\n## Target\nreal\n## Next\n")
            self.assertEqual(phase_brief.reference_section("sample.md", "Target"), "## Target\nreal")

    def test_unreadable_reference_diagnostic_is_relative(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(phase_brief, "REFERENCES", Path(directory)):
            result = dispatch_brief({"phase": "Clarify", "workflow_file": "docs/workflow.md", "feature_dir": "specs/example"})
        self.assertEqual(result["status"], "internal_failure")
        message = result["diagnostics"][0]["message"]
        self.assertNotIn(directory, message)
        self.assertIn("capability-discovery.md", message)
        self.assertIn("Capability Categories", message)

    def test_section_fences_and_heading_boundaries(self):
        # CommonMark 0.31.2 sections 4.2 and 4.5; return original bytes as lines.
        cases = (
            ("## Target", "```", "~~~\n## inside", "```"),
            ("## Target", "~~~~", "~~~\n## inside", "~~~~~"),
            ("## Target", "````", "```\n## inside", "`````"),
            ("## Target", "```", "``` info\n## inside", "```"),
            ("## Target", "```", "    ```\n## inside", "```"),
            (" ## Target", " ```python", "  ### inside", "   ``` \t"),
            ("  ##\tTarget ###", "   ~~~info", "## inside", " ~~~~"),
            ("   ## Target", "    ```", "    ## code", ""),
            ("## Target", "```bad`info", "body", ""),
        )
        with tempfile.TemporaryDirectory() as directory, patch.object(phase_brief, "REFERENCES", Path(directory)):
            for heading, opener, content, closer in cases:
                with self.subTest(heading=heading, opener=opener, content=content):
                    expected = "\n".join((heading, opener, content, closer)).rstrip()
                    (Path(directory) / "sample.md").write_text(expected + "\n  ## Next\nexcluded\n")
                    self.assertEqual(phase_brief.reference_section("sample.md", "Target"), expected)
            for boundary in ("#", "##\tNext", "   ## Next ###"):
                with self.subTest(boundary=boundary):
                    (Path(directory) / "sample.md").write_text("## Target\nbody\n" + boundary + "\nexcluded\n")
                    self.assertEqual(phase_brief.reference_section("sample.md", "Target"), "## Target\nbody")

    def test_unclosed_reference_fence_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(phase_brief, "REFERENCES", Path(directory)):
            for opener, false_close in (("````", "```"), ("~~~", "```"), ("```", "``` info")):
                with self.subTest(opener=opener, false_close=false_close):
                    (Path(directory) / "sample.md").write_text("## Target\n" + opener + "\n" + false_close + "\n## Next\nexcluded\n")
                    with self.assertRaisesRegex(ValueError, "unclosed fence"):
                        phase_brief.reference_section("sample.md", "Target")

    def test_executor_briefs_carry_their_slices(self):
        sources = [(REFERENCES / name).read_text() for name in WHOLE_REFERENCES]
        for phase in ("Clarify", "Checklist", "Analyze"):
            with self.subTest(phase=phase):
                slices = dispatch_brief({"phase": phase, "workflow_file": "docs/workflow.md", "feature_dir": "specs/example"})["data"]["slices"]
                self.assertGreaterEqual(len(slices), 3)
                for text in slices:
                    self.assertIsInstance(text, str)
                    self.assertTrue(any(text in source for source in sources), "slice is not a verbatim excerpt: " + text[:60])
                    self.assertFalse(any(text.strip() == source.strip() for source in sources), "slice is a whole reference")
                joined = "\n".join(slices)
                for needle in ("## Research Broker Rule", "## Discovery Step", "## Inventory Disclosure", "## Security Keywords", "## G1", "### Category tags"):
                    self.assertIn(needle, joined)
                whole = sum(len(source.splitlines()) for source in sources)
                self.assertLess(len(joined.splitlines()), whole // 8)

    def test_both_hosts_insert_the_slices_verbatim(self):
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                skill = (host_skill_root(host) / "speckit-autopilot/SKILL.md").read_text()
                loop = skill.split("## Step 2: Main Execution Loop", 1)[1]
                self.assertIn("brief.slices", loop)
                self.assertIn("verbatim", loop.split("brief.slices", 1)[1][:400])


class PhaseBriefEncodingTests(unittest.TestCase):
    def assert_reference_encoding_rejected(self, text):
        with tempfile.TemporaryDirectory() as directory, patch.object(phase_brief, "REFERENCES", Path(directory)):
            (Path(directory) / "sample.md").write_bytes(text.encode())
            with self.assertRaisesRegex(ValueError, "unsupported control or line separator"):
                phase_brief.reference_section("sample.md", "Target")

    def test_reference_rejects_nonstandard_heading_boundaries(self):
        levels = [(level, boundary) for level in range(1, 7) for boundary in range(1, level + 1)]
        for separator, (level, boundary) in product(UNSUPPORTED_SEPARATORS, levels):
            with self.subTest(separator=repr(separator), level=level, boundary=boundary):
                text = "#" * level + " Target\nsafe" + separator + "#" * boundary + " Next\nEXCLUDED\n"
                self.assert_reference_encoding_rejected(text)

    def test_reference_rejects_nonstandard_fence_boundaries(self):
        for separator, fence, edge in product(UNSUPPORTED_SEPARATORS, ("```", "~~~"), ("opener", "closer")):
            with self.subTest(separator=repr(separator), fence=fence, edge=edge):
                text = ("## Target\nsafe" + separator + fence + "\n## Hidden\nkept\n" + fence + "\n## Next\nEXCLUDED\n"
                        if edge == "opener" else "## Target\n" + fence + "\nkept" + separator + fence + "\n## Next\nEXCLUDED\n")
                self.assert_reference_encoding_rejected(text)

    def test_reference_rejects_controls_throughout_the_document(self):
        # Enumerate C0/C1 independently of the production Unicode-category check.
        controls = [chr(code) for code in (*range(32), *range(127, 160)) if code not in (9, 10)]
        controls += ["\u2028", "\u2029"]
        templates = {
            "before": "prefix{control}text\n## Target\nsafe\n## Next\nEXCLUDED\n",
            "inside": "## Target\nsafe{control}text\n## Next\nEXCLUDED\n",
            "after": "## Target\nsafe\n## Next\nEXCLUDED{control}text\n",
            "comment": "## Target\n<!--\nhidden{control}text\n-->\n## Next\nEXCLUDED\n",
            "comment_opener": "## Target\nsafe{control}<!--\nhidden\n-->\n## Next\nEXCLUDED\n",
            "comment_closer": "## Target\n<!--\nhidden{control}-->\n## Next\nEXCLUDED\n",
            "fence": "## Target\n```\nhidden{control}text\n```\n## Next\nEXCLUDED\n",
            "setext": "## Target\nsafe{control}===\n## Next\nEXCLUDED\n",
        }
        for control, (position, template) in product(controls, templates.items()):
            with self.subTest(control=repr(control), position=position):
                self.assert_reference_encoding_rejected(template.format(control=control))


class PhaseBriefEncodingHostTests(unittest.TestCase):
    def check_reference_encoding(self, separators, verify):
        references, cases = reference_encoding_cases(separators)
        for host, root in RUNNER_ROOTS:
            reports = reference_probe(root, references, cases)
            self.assertEqual(len(reports), len(cases))
            for case, report in zip(cases, reports, strict=True):
                with self.subTest(host=host, name=case["name"], heading=case["heading"],
                                  separator=repr(case["separator"]), marker=case["marker"]):
                    self.assertEqual(len(report["dispatch"]), 3)
                    verify(case, report)

    def assert_invalid_encoding_rejected(self, case, report):
        self.assertIn("unsupported control or line separator", report.get("error", ""))
        for result in report["dispatch"]:
            self.assertEqual(result["status"], "internal_failure")
            self.assertEqual(result["data"], {})
            self.assertEqual(result["request_id"], "encoding-probe")
            self.assertIn("unsupported control or line separator", result["diagnostics"][0]["message"])

    def assert_supported_encoding_preserved(self, case, report):
        self.assertEqual(report.get("section"), case["expected"])
        for result in report["dispatch"]:
            self.assertEqual(result["status"], "ok")
            self.assertIn(case["expected"], result["data"]["slices"])
            self.assertNotIn("EXCLUDED", "\n".join(result["data"]["slices"]))

    def test_all_hosts_and_slice_windows_reject_invalid_encoding(self):
        self.check_reference_encoding(UNSUPPORTED_SEPARATORS, self.assert_invalid_encoding_rejected)

    def test_all_hosts_and_slice_windows_preserve_supported_encoding(self):
        self.check_reference_encoding(("\n", "\r\n"), self.assert_supported_encoding_preserved)


class PhaseBriefEncodingPathTests(unittest.TestCase):
    def test_reference_encoding_checks_bytes_after_link_or_rename(self):
        for separator, marker, topology in product(UNSUPPORTED_SEPARATORS, ("## Next", "```"), ("link", "rename")):
            with self.subTest(separator=repr(separator), marker=marker, topology=topology):
                with tempfile.TemporaryDirectory() as directory, patch.object(phase_brief, "REFERENCES", Path(directory)):
                    target = Path(directory) / "sample.md"
                    replacement = Path(directory) / "replacement.md"
                    text = "## Target\nsafe" + separator + marker + "\nEXCLUDED\n"
                    if marker == "```":
                        text += "```\n"
                    replacement.write_bytes(text.encode())
                    if topology == "link":
                        target.symlink_to(replacement.name)
                    else:
                        target.write_text("## Target\nsafe\n## Next\n")
                        replacement.replace(target)
                    with self.assertRaisesRegex(ValueError, "unsupported control or line separator"):
                        phase_brief.reference_section("sample.md", "Target")


class PhaseBriefExecutorContractTests(unittest.TestCase):
    def test_no_executor_is_told_to_read_the_references_whole(self):
        sources = [(REPO / "speckit-pro/agents" / (name + ".md")) for name in SLICE_AGENTS]
        sources += [(REPO / "speckit-pro/codex-agents" / (name + ".toml")) for name in SLICE_AGENTS]
        for host, folder in (("claude", "agents"), ("codex", "codex-agents")):
            suffix = ".md" if host == "claude" else ".toml"
            sources += [REPO / "dist" / host / "speckit-pro" / folder / (name + suffix) for name in SLICE_AGENTS]
        for path in sources:
            with self.subTest(agent=str(path.relative_to(REPO))):
                text = " ".join(path.read_text().split())
                for forbidden in ("Reference dir", "Protocol:` line, which", "absolute path on your prompt"):
                    self.assertNotIn(forbidden, text)
                if path.suffix == ".md" or "claude" in path.parts:
                    self.assertIn("reference slices", text)

    def test_repair_reservation_keeps_its_source_pointer(self):
        roots = ((REPO / "speckit-pro/agents", ".md"), (REPO / "speckit-pro/codex-agents", ".toml"),
                 (REPO / "dist/claude/speckit-pro/agents", ".md"), (REPO / "dist/codex/speckit-pro/codex-agents", ".toml"))
        for root, suffix in roots:
            for name in ("checklist-executor", "analyze-executor"):
                with self.subTest(agent=name, root=str(root.relative_to(REPO))):
                    text = " ".join((root / (name + suffix)).read_text().split())
                    reservation = text.split("Your repairs spend", 1)[1].split("5.", 1)[0]
                    self.assertIn("a nested loop has no allowance of its own", reservation)
                    self.assertIn("skills/speckit-autopilot/references/execution-efficiency.md", reservation)
                    self.assertNotIn("Read", reservation)

    def test_dispatch_omits_whole_reference_paths(self):
        for runtime in ("claude", "codex"):
            loop = (host_skill_root(runtime) / "speckit-autopilot/SKILL.md").read_text().split("## Step 2: Main Execution Loop", 1)[1]
            self.assertNotIn("`Reference dir:` lines (`references/consensus-protocol.md`)", loop, runtime)


if __name__ == "__main__":
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case) for case in (PhaseBriefTests, PhaseBriefModelTests, CodexEffectiveEffortTests, RetryLadderTopRungTests, PhaseBriefSliceTests, PhaseBriefEncodingTests, PhaseBriefEncodingHostTests, PhaseBriefEncodingPathTests, PhaseBriefExecutorContractTests))
    sys.exit(run_counted(suite, label="test-phase-brief"))
