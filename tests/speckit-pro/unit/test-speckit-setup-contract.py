#!/usr/bin/env python3
"""Project SpecKit skills call only script options their scripts accept."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO_ROOT / "speckit-pro"), str(REPO_ROOT / "tests/speckit-pro/lib")]

from speckit_pro_runner.gates import payloads  # noqa: E402
from speckit_pro_runner.helpers.read_only import (  # noqa: E402
    check_prerequisites,
    detect_presets,
    setup_contract_mismatches,
    template_resolution_error,
)
from readiness_case import ReadinessCase  # noqa: E402
from test_result import run_counted  # noqa: E402

SCRIPT = """#!/usr/bin/env bash
while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            JSON_MODE=true
            ;;
        --require-tasks|--include-tasks)
            ;;
{extra}        *)
            echo "ERROR: Unknown option '$1'." >&2
            exit 1
            ;;
    esac
    shift
done
"""
TEMPLATE_CASE = "        --template)\n            shift\n            ;;\n"
CALL = "1. Run `.specify/scripts/bash/check-prerequisites.sh --json --template checklist-template` from repo root.\n"


class SetupContract(unittest.TestCase):
    def repo(self, *, script_extra: str = "", skill: str = CALL, script: bool = True) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name).resolve()
        skill_path = root / ".claude/skills/speckit-checklist/SKILL.md"
        skill_path.parent.mkdir(parents=True)
        skill_path.write_text(skill, encoding="utf-8")
        if script:
            script_path = root / ".specify/scripts/bash/check-prerequisites.sh"
            script_path.parent.mkdir(parents=True)
            script_path.write_text(SCRIPT.format(extra=script_extra), encoding="utf-8")
        return root

    def test_an_option_the_script_rejects_is_a_mismatch(self) -> None:
        self.assertEqual(
            [".claude/skills/speckit-checklist/SKILL.md: check-prerequisites.sh --template"],
            setup_contract_mismatches(self.repo()),
        )

    def test_an_accepted_option_passes_including_alternation_labels(self) -> None:
        skill = CALL + "Run `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks` once.\n"
        self.assertEqual([], setup_contract_mismatches(self.repo(script_extra=TEMPLATE_CASE, skill=skill)))

    def test_a_missing_script_is_a_mismatch(self) -> None:
        self.assertEqual(
            [".claude/skills/speckit-checklist/SKILL.md: check-prerequisites.sh is missing"],
            setup_contract_mismatches(self.repo(script=False)),
        )

    def test_prerequisite_check_fails_closed_on_a_mismatch(self) -> None:
        result = check_prerequisites({"workflow_file": ""}, self.repo())
        report = json.loads(result["stdout"])
        [setup] = [item for item in report["checks"] if item["check"] == "setup_contract"]
        self.assertFalse(setup["pass"])
        self.assertFalse(report["all_pass"])
        self.assertIn("check-prerequisites.sh --template", setup["detail"])

    def test_this_repository_skills_match_their_scripts(self) -> None:
        self.assertEqual([], setup_contract_mismatches(REPO_ROOT))



class TemplateResolution(unittest.TestCase):
    """SpecKit parses preset manifests with PyYAML from the first Python 3 on PATH."""

    def repo(self, *, preset: bool) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name).resolve()
        (root / ".specify/presets/speckit-pro-reviewability").mkdir(parents=True)
        if preset:
            (root / ".specify/presets/speckit-pro-reviewability/preset.yml").write_text("schema_version: '1.0'\n")
        return root

    def probe(self, *, yaml: bool, python3: str | None = "/tools/python3"):
        calls: list[list[str]] = []

        def run(argv, **kwargs):
            calls.append(list(argv))
            self.assertIs(kwargs.get("shell", False), False)
            code = 1 if argv[-1] == "import yaml" and not yaml else 0
            if argv[0] == "python3" and python3 is None:
                raise FileNotFoundError(argv[0])
            return subprocess.CompletedProcess(argv, code, "", "")

        which = {"python3": python3, "python": "/tools/python"}.get
        return calls, patch("speckit_pro_runner.helpers.read_only.shutil.which", side_effect=lambda name, **kwargs: which(name)), \
            patch("speckit_pro_runner.helpers.read_only.subprocess.run", side_effect=run)

    def test_a_preset_manifest_needs_pyyaml_in_the_path_python(self) -> None:
        calls, which, run = self.probe(yaml=False)
        with which, run:
            error = template_resolution_error(self.repo(preset=True))
        self.assertIsNotNone(error)
        self.assertIn("/tools/python3", error)
        self.assertIn("PyYAML", error)
        self.assertEqual(["python3", "-c", "import yaml"], calls[-1])

    def test_pyyaml_present_or_no_preset_manifest_passes(self) -> None:
        calls, which, run = self.probe(yaml=True)
        with which, run:
            self.assertIsNone(template_resolution_error(self.repo(preset=True)))
        calls, which, run = self.probe(yaml=False)
        with which, run:
            self.assertIsNone(template_resolution_error(self.repo(preset=False)))
        self.assertEqual([], calls)

    def test_python_falls_back_like_speckit_and_none_fails_closed(self) -> None:
        calls, which, run = self.probe(yaml=True, python3=None)
        with which, run:
            self.assertIsNone(template_resolution_error(self.repo(preset=True)))
        self.assertEqual("python", calls[-1][0])
        with patch("speckit_pro_runner.helpers.read_only.shutil.which", return_value=None):
            self.assertIn("no Python 3", template_resolution_error(self.repo(preset=True)) or "")

    def test_windows_is_not_probed(self) -> None:
        calls, which, run = self.probe(yaml=False)
        with which, run, patch("speckit_pro_runner.helpers.read_only.sys.platform", "win32"):
            self.assertIsNone(template_resolution_error(self.repo(preset=True)))
        self.assertEqual([], calls)

    def test_prerequisite_check_reports_the_missing_dependency(self) -> None:
        calls, which, run = self.probe(yaml=False)
        with which, run:
            report = json.loads(check_prerequisites({"workflow_file": ""}, self.repo(preset=True))["stdout"])
        [item] = [entry for entry in report["checks"] if entry["check"] == "template_resolution"]
        self.assertFalse(item["pass"])
        self.assertFalse(report["all_pass"])


PRESET_ID = "speckit-pro-reviewability"
PRESET_TEMPLATES = ("spec-template", "plan-template", "tasks-template")


def specify(root: Path, args: list[str]) -> tuple[int, str]:
    """The `specify` v1.1.0 surface scaffold uses, as checked against the pinned CLI by hand.

    `preset add --dev DIR --priority N` copies DIR to .specify/presets/<id>/ and registers it;
    `preset resolve NAME` names the top layer that provides the template.
    """
    presets = root / ".specify/presets"
    if args[:3] == ["preset", "add", "--dev"] and args[4:5] == ["--priority"]:
        source = Path(args[3])
        shutil.copytree(source, presets / source.name)
        (presets / ".registry").write_text(json.dumps({"presets": {source.name: {"priority": int(args[5])}}}))
        return 0, ""
    if args[:2] == ["preset", "resolve"]:
        hits = sorted(presets.glob(f"*/templates/{args[2]}.md"))
        return (0, hits[0].relative_to(root).as_posix()) if hits else (1, "")
    return 2, ""


class ReviewabilityPreset(ReadinessCase):
    """A fresh project (`self.root`: `specify init`, no preset) gets the shipped reviewability preset."""

    def state(self, root: Path) -> dict[str, object]:
        return json.loads(detect_presets({"repo_root": str(root)}, root)["stdout"])["reviewability_preset"]

    def test_a_fresh_project_ends_with_the_preset_installed_and_step_5_0_passing(self) -> None:
        root = self.root
        before = self.state(root)
        self.assertEqual("missing", before["status"])
        self.assertEqual(["preset", "add", "--dev"], before["add_args"][:3])
        self.assertEqual(["--priority", "5"], before["add_args"][4:])
        self.assertEqual((0, ""), specify(root, before["add_args"]))
        after = self.state(root)
        self.assertEqual(("installed", []), (after["status"], after["add_args"]))
        for name in PRESET_TEMPLATES:
            with self.subTest(template=name):
                self.assertEqual(
                    (0, f".specify/presets/{PRESET_ID}/templates/{name}.md"), specify(root, ["preset", "resolve", name])
                )
        # Step 5.0 also requires the PATH interpreter to parse preset manifests.
        # Probe the external interpreter boundary; keep prerequisite policy real.
        for yaml_available in (True, False):
            with self.subTest(yaml_available=yaml_available), \
                    patch("speckit_pro_runner.helpers.read_only.sys.platform", "linux"), \
                    patch("speckit_pro_runner.helpers.read_only.shutil.which", return_value="/tools/python3"), \
                    patch("speckit_pro_runner.helpers.read_only.subprocess.run", side_effect=lambda argv, **kwargs:
                          subprocess.CompletedProcess(argv, int(argv[-1] == "import yaml" and not yaml_available), "", "")):
                report = json.loads(check_prerequisites({"workflow_file": ""}, root)["stdout"])
                [resolution] = [item for item in report["checks"] if item["check"] == "template_resolution"]
                self.assertEqual(yaml_available, resolution["pass"])
                if not yaml_available:
                    self.assertFalse(report["all_pass"])

    def test_a_registered_preset_needs_no_command_and_an_unregistered_one_is_added(self) -> None:
        root = self.root
        shutil.copytree(REPO_ROOT / ".specify/presets" / PRESET_ID, root / ".specify/presets" / PRESET_ID)
        self.assertEqual("missing", self.state(root)["status"])
        shutil.copy(REPO_ROOT / ".specify/presets/.registry", root / ".specify/presets/.registry")
        self.assertEqual("installed", self.state(root)["status"])

    def test_a_malformed_registry_never_reports_the_preset_installed(self) -> None:
        root = self.root
        shutil.copytree(REPO_ROOT / ".specify/presets" / PRESET_ID, root / ".specify/presets" / PRESET_ID)
        for registry in ([PRESET_ID], {"presets": [PRESET_ID]}, {"presets": PRESET_ID}, {"presets": None}, "invalid"):
            with self.subTest(registry=registry):
                (root / ".specify/presets/.registry").write_text(json.dumps(registry))
                state = self.state(root)
                self.assertEqual("missing", state["status"])
                self.assertEqual(["preset", "add", "--dev"], state["add_args"][:3])

    def test_the_shipped_preset_replaces_the_three_core_templates(self) -> None:
        manifest = (REPO_ROOT / ".specify/presets" / PRESET_ID / "preset.yml").read_text(encoding="utf-8")
        for name in PRESET_TEMPLATES:
            with self.subTest(template=name):
                self.assertIn(f'replaces: "{name}"', manifest)
                self.assertTrue((REPO_ROOT / ".specify/presets" / PRESET_ID / "templates" / f"{name}.md").is_file())

    def test_both_host_payloads_carry_the_preset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            payloads.build_installed_plugin_payloads(REPO_ROOT, Path(tmp))
            for host in ("claude", "codex"):
                with self.subTest(host=host):
                    shipped = Path(tmp) / host / "speckit-pro/presets" / PRESET_ID
                    self.assertTrue((shipped / "preset.yml").is_file())
                    for name in PRESET_TEMPLATES:
                        self.assertTrue((shipped / "templates" / f"{name}.md").is_file())


if __name__ == "__main__":
    suite = unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromTestCase(case) for case in (SetupContract, TemplateResolution, ReviewabilityPreset)
    )
    raise SystemExit(run_counted(suite, label="test-speckit-setup-contract"))
