#!/usr/bin/env python3
"""Deterministic contracts for repository Bash confinement."""

from __future__ import annotations

import ast
import inspect
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "repository-bash-confinement"
ALLOWLIST_FILE = FIXTURE_DIR / "allowlist.json"
CASES_FILE = FIXTURE_DIR / "confinement-guard-cases.json"
RESULT_CONTRACT = FIXTURE_DIR / "contracts" / "repo-bash-confinement-result.schema.json"
TEMP_ALLOWLIST = "tests/speckit-pro/unit/fixtures/repository-bash-confinement/allowlist.json"

for path in (PLUGIN_ROOT, LIB_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from speckit_pro_runner.gates import active_path_guard  # noqa: E402
from test_result import run_counted  # noqa: E402


ALLOWLIST_DOCUMENT = json.loads(ALLOWLIST_FILE.read_text(encoding="utf-8"))
CASES = json.loads(CASES_FILE.read_text(encoding="utf-8"))["cases"]
CASES_BY_ID = {case["case_id"]: case for case in CASES}
CANONICAL_PATHS = [entry["path"] for entry in ALLOWLIST_DOCUMENT["entries"]]


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        shell=False,
        check=True,
    )


def write_file(root: Path, relative: str, content: str | bytes) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


@contextmanager
def temporary_repo(
    files: list[dict[str, str]] | None = None,
    *,
    allowlist: dict[str, object] | None = None,
    include_vendored: bool = True,
):
    with tempfile.TemporaryDirectory(prefix="repository-bash-confinement-") as tmp:
        root = Path(tmp)
        (root / "speckit-pro" / "speckit_pro_runner").mkdir(parents=True)
        (root / "tests" / "speckit-pro").mkdir(parents=True)
        document = ALLOWLIST_DOCUMENT if allowlist is None else allowlist
        write_file(root, TEMP_ALLOWLIST, json.dumps(document, indent=2) + "\n")
        if include_vendored:
            for path in CANONICAL_PATHS:
                write_file(root, path, "#!/usr/bin/env bash\nexit 0\n")
        for item in files or []:
            write_file(root, item["path"], item["content"])
        git(root, "init", "--quiet")
        git(root, "add", "-A")
        yield root


def guard_request(root: Path, *, allowlist_file: str = TEMP_ALLOWLIST):
    return SimpleNamespace(
        operation="repo-bash-confinement",
        request_id="test-repo-bash-confinement",
        mode="read_only",
        inputs={"repo_root": str(root), "allowlist_file": allowlist_file},
    )


def run_guard(root: Path, *, allowlist_file: str = TEMP_ALLOWLIST) -> dict[str, object]:
    return active_path_guard.run_active_path_guard(
        SimpleNamespace(helper_id="active-path-guard"),
        guard_request(root, allowlist_file=allowlist_file),
    )


class RepoBashConfinementTests(unittest.TestCase):
    def assert_result_contract(self, data: dict[str, object]) -> None:
        schema = json.loads(RESULT_CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(
            schema["properties"]["contract_id"]["const"],
            "repository-bash-confinement",
        )
        self.assertEqual(schema["properties"]["enumeration"]["properties"]["source"]["const"], "git ls-files -z")
        expected_allowlist_count = len(active_path_guard.REPOSITORY_BASH_CONFINEMENT_ALLOWLIST_PATHS)
        self.assertEqual(
            schema["properties"]["allowlist"]["properties"]["entry_count"]["maximum"],
            expected_allowlist_count,
        )
        for field in schema["required"]:
            self.assertIn(field, data)
        self.assertEqual(data["schema_version"], schema["properties"]["schema_version"]["const"])
        self.assertEqual(data["contract_id"], schema["properties"]["contract_id"]["const"])
        self.assertIn(data["status"], schema["properties"]["status"]["enum"])
        self.assertIs(type(data["blocking_count"]), int)
        self.assertGreaterEqual(data["blocking_count"], 0)
        self.assertIsInstance(data["classified_counts"], dict)
        self.assertTrue(
            all(isinstance(key, str) and type(value) is int and value >= 0 for key, value in data["classified_counts"].items())
        )
        self.assertIsInstance(data["findings"], list)
        for finding in data["findings"]:
            for field in schema["$defs"]["finding"]["required"]:
                self.assertIn(field, finding)
            self.assertIsInstance(finding["path"], str)
            self.assertIsInstance(finding["category"], str)
            self.assertIn(finding["classification"], {"blocking_repo_bash", "vendored_specify_helper"})
            self.assertTrue(finding.get("line") is None or type(finding["line"]) is int)

        enumeration = data["enumeration"]
        self.assertEqual(
            set(enumeration),
            {
                "active_instruction_values",
                "runtime_diagnostic_values",
                "source",
                "workflow_run_values",
                "tracked_file_count",
            },
        )
        inspection_fields = (
            "active_instruction_values",
            "runtime_diagnostic_values",
            "workflow_run_values",
        )
        inspection_states = {enumeration[field] for field in inspection_fields}
        self.assertEqual(len(inspection_states), 1)
        inspection_state = next(iter(inspection_states))
        for field in inspection_fields:
            self.assertIn(
                inspection_state,
                schema["properties"]["enumeration"]["properties"][field]["enum"],
            )
        self.assertEqual(enumeration["source"], "git ls-files -z")
        self.assertIs(type(enumeration["tracked_file_count"]), int)
        self.assertGreaterEqual(enumeration["tracked_file_count"], 0)

        allowlist = data["allowlist"]
        self.assertEqual(set(allowlist), {"path", "entry_count", "release_readiness_excluded"})
        self.assertIsInstance(allowlist["path"], str)
        self.assertTrue(allowlist["path"])
        self.assertIs(type(allowlist["entry_count"]), int)
        self.assertGreaterEqual(allowlist["entry_count"], 0)
        self.assertLessEqual(allowlist["entry_count"], expected_allowlist_count)
        self.assertIs(type(allowlist["release_readiness_excluded"]), bool)

        self.assertEqual(data["total_finding_count"], len(data["findings"]))
        self.assertEqual(data["truncated_finding_count"], 0)
        if inspection_state == "inspected":
            self.assertEqual(allowlist["entry_count"], expected_allowlist_count)
            self.assertIs(allowlist["release_readiness_excluded"], True)
            self.assertEqual(
                data["blocking_count"],
                sum(item["classification"] == "blocking_repo_bash" for item in data["findings"]),
            )
        else:
            self.assertEqual(data["status"], "fail")
            self.assertGreater(data["blocking_count"], 0)
            self.assertEqual(data["findings"], [])
            self.assertEqual(allowlist["release_readiness_excluded"], allowlist["entry_count"] > 0)
        self.assertEqual(sum(data["classified_counts"].values()), len(data["findings"]))

    def test_fixture_matrix_and_result_contract(self) -> None:
        for case in CASES:
            with self.subTest(case_id=case["case_id"]):
                with temporary_repo(case.get("files")) as root:
                    result = run_guard(root)
                self.assert_result_contract(result["data"])
                self.assertEqual(result["data"]["status"], case["expected_status"])
                if case["expected_status"] == "pass":
                    self.assertEqual(result["status"], "ok")
                    self.assertEqual(result["data"]["blocking_count"], 0)
                else:
                    self.assertEqual(result["status"], "expected_failure")
                    self.assertGreater(result["data"]["blocking_count"], 0)
                    self.assertIn(case["expected_category"], {item["category"] for item in result["data"]["findings"]})

    def test_allowlisted_entries_are_excluded_negative_controls(self) -> None:
        with temporary_repo() as root:
            result = run_guard(root)
        findings = result["data"]["findings"]
        allowlisted = [item for item in findings if item["classification"] == "vendored_specify_helper"]
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["data"]["blocking_count"], 0)
        self.assertEqual(len(allowlisted), len(active_path_guard.REPOSITORY_BASH_CONFINEMENT_ALLOWLIST_PATHS))
        self.assertTrue(all(item["release_readiness_excluded"] is True for item in allowlisted))
        self.assertEqual(
            result["data"]["classified_counts"],
            {"vendored_specify_helper": len(active_path_guard.REPOSITORY_BASH_CONFINEMENT_ALLOWLIST_PATHS)},
        )
        self.assertNotIn("bash_free", result["data"]["classified_counts"])
        self.assertTrue(result["data"]["allowlist"]["release_readiness_excluded"])

    def test_exact_allowlist_rejects_substitution_and_missing_file(self) -> None:
        substituted = json.loads(json.dumps(ALLOWLIST_DOCUMENT))
        substituted["entries"][-1]["path"] = ".specify/scripts/bash/substitute.sh"
        with temporary_repo(allowlist=substituted) as root:
            result = run_guard(root)
        self.assert_result_contract(result["data"])
        self.assertEqual(result["status"], "input_error")
        self.assertEqual([item["code"] for item in result["diagnostics"]], ["invalid_allowlist"])

        with temporary_repo() as root:
            missing_path = root / CANONICAL_PATHS[-1]
            missing_path.unlink()
            git(root, "add", "-A")
            result = run_guard(root)
        self.assert_result_contract(result["data"])
        self.assertEqual(result["status"], "input_error")
        self.assertEqual([item["code"] for item in result["diagnostics"]], ["invalid_allowlist"])
        self.assertEqual(result["diagnostics"][0]["details"]["missing"], [CANONICAL_PATHS[-1]])

        with temporary_repo() as root:
            result = run_guard(root, allowlist_file="missing-allowlist.json")
        self.assert_result_contract(result["data"])
        self.assertEqual(result["status"], "input_error")
        self.assertEqual([item["code"] for item in result["diagnostics"]], ["invalid_allowlist"])

    def test_shebang_scope_and_binary_fallback(self) -> None:
        files = [
            {"path": "tools/posix-runner", "content": "#!/bin/sh\nexit 0\n"},
            {"path": "tools/zsh-runner", "content": "#!/usr/bin/env zsh\nexit 0\n"},
            {"path": "tools/windows.ps1", "content": "#!/usr/bin/env pwsh\nexit 0\n"},
        ]
        with temporary_repo(files) as root:
            write_file(root, "tools/binary", b"\xff\xfe\x00bash")
            write_file(root, "tools/binary.sh", b"\xff\xfe\x00")
            git(root, "add", "-A")
            result = run_guard(root)
        blocking_paths = {item["path"] for item in result["data"]["findings"] if item["classification"] == "blocking_repo_bash"}
        self.assertIn("tools/posix-runner", blocking_paths)
        self.assertIn("tools/binary.sh", blocking_paths)
        self.assertNotIn("tools/binary", blocking_paths)
        self.assertNotIn("tools/zsh-runner", blocking_paths)
        self.assertNotIn("tools/windows.ps1", blocking_paths)

    def test_python_command_vocabulary_is_exact_and_tracks_dynamic_sources(self) -> None:
        source = """
import shutil
import subprocess

def cmd_path(name):
    return shutil.which(name) or ''

def run_command(argv):
    return subprocess.run(argv, shell=False)

def check():
    bash_path = cmd_path('bash')
    jq_path = shutil.which('jq')
    run_command([bash_path, '--version'])
    subprocess.run([jq_path, '-e', '.'])
    subprocess.run(['sh', '-c', 'echo ok'])
    subprocess.run(['sh', '-c', 'jq -e . result.json'])
    subprocess.run(['zsh', '-c', 'echo ok'])
    subprocess.run(['pwsh', '-File', 'check.ps1'])
"""
        findings = active_path_guard.repo_bash_python_findings("tools/check.py", source)
        self.assertEqual(len(findings), 4)
        self.assertTrue(all(item.category == "command_argv_subprocess" for item in findings))
        unresolved = [item for item in findings if item.pattern == "<dynamic executable>"]
        self.assertEqual(len(unresolved), 1)
        self.assertIn("cannot be statically resolved", unresolved[0].reason)
        self.assertEqual(active_path_guard.REPO_BASH_COMMAND_NAMES, {"bash", "bash.exe", "jq", "jq.exe"})

    def test_python_scans_class_bodies_and_methods_with_separate_bindings(self) -> None:
        source = """
import subprocess

class SafeRunner:
    @staticmethod
    def run(argv):
        return argv

class Checks:
    class_call = subprocess.run(['bash', '--version'])

    def method(self):
        return subprocess.run(['jq', '--version'])

class Shadowed:
    subprocess = SafeRunner
    class_call = subprocess.run(['bash', '--version'])

class ReboundAfterCall:
    class_call = subprocess.run(['bash', '--help'])
    subprocess = SafeRunner
    safe_call = subprocess.run(['bash', '--safe'])

class MethodBindings:
    subprocess = SafeRunner

    def method(self):
        return subprocess.run(['bash', '--method'])
"""
        findings = active_path_guard.repo_bash_python_findings("tools/class-checks.py", source)
        self.assertEqual(len(findings), 4)
        self.assertEqual(
            {item.pattern for item in findings},
            {"bash --version", "jq --version", "bash --help", "bash --method"},
        )

    def test_conditional_subprocess_rebinding_does_not_hide_forbidden_calls(self) -> None:
        sources = {
            "if": """
import subprocess

if False:
    subprocess = safe_runner

subprocess.run(['bash', '--version'])
""",
            "loop": """
import subprocess

for runner in optional_runners:
    subprocess = runner

subprocess.run(['bash', '--version'])
""",
            "try": """
import subprocess

try:
    initialize_runner()
except RuntimeError:
    subprocess = safe_runner

subprocess.run(['bash', '--version'])
""",
        }
        for control_flow, source in sources.items():
            with self.subTest(control_flow=control_flow):
                findings = active_path_guard.repo_bash_python_findings(
                    f"tools/{control_flow}-rebind.py",
                    source,
                )
                self.assertEqual([item.pattern for item in findings], ["bash --version"])

    def test_structural_json_scans_only_execution_values(self) -> None:
        hook_content = json.dumps(
            {
                "description": "bash and jq prose",
                "hooks": [{"command": "python3 check.py"}, {"note": "bash"}],
            }
        )
        package_content = json.dumps(
            {
                "description": "jq prose",
                "dependencies": {"bash-parser": "1.0.0"},
                "scripts": {"check": "python3 check.py"},
            }
        )
        self.assertEqual(active_path_guard.repo_bash_json_findings("hooks.json", hook_content), [])
        self.assertEqual(active_path_guard.repo_bash_json_findings("package.json", package_content), [])

        nested_hook = json.dumps({"hooks": [{"command": "cmd.exe /c jq -e . result.json"}]})
        nested_package = json.dumps({"scripts": {"check": "sh -c 'jq -e . result.json'"}})
        self.assertEqual(len(active_path_guard.repo_bash_json_findings("hooks.json", nested_hook)), 1)
        self.assertEqual(len(active_path_guard.repo_bash_json_findings("package.json", nested_package)), 1)

    def test_workflow_scans_only_run_values_and_preserves_fixture_categories(self) -> None:
        prose_only = """\
name: Mentions bash and jq
env:
  NOTE: use tools/check.sh only in historical prose
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: example/bash-action@v1
      - run: python3 scripts/check.py
"""
        tracked = {"scripts/check.py"}
        self.assertEqual(
            active_path_guard.repo_bash_workflow_findings(
                ".github/workflows/prose.yml",
                prose_only,
                tracked,
            ),
            [],
        )

        expected_categories = {
            "workflow-multiline-control-logic-fails": "workflow_shell_logic",
            "workflow-jq-and-shell-script-fail": "workflow_forbidden_command",
            "workflow-inline-python-heredoc-fails": "workflow_heredoc",
            "workflow-sentinel-shell-logic-fails": "workflow_shell_logic",
            "workflow-untracked-runner-input-fails": "workflow_untracked_input",
        }
        for case_id, expected_category in expected_categories.items():
            with self.subTest(case_id=case_id):
                workflow = CASES_BY_ID[case_id]["files"][0]
                findings = active_path_guard.repo_bash_workflow_findings(
                    workflow["path"],
                    workflow["content"],
                    set(),
                )
                self.assertTrue(findings)
                self.assertIn(expected_category, {finding.category for finding in findings})

    def test_workflow_boundary_allows_only_thin_direct_dispatch(self) -> None:
        tracked = {"requests/check.json", "scripts/check.py"}
        allowed = (
            "python3 scripts/check.py --mode ci",
            'python3 scripts/check.py --message "alpha; beta | gamma && delta || epsilon"',
            'python3 scripts/check.py --message ";"',
            "PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < requests/check.json",
            "pnpm --dir docs-site validate",
            "corepack prepare pnpm@10.25.0 --activate",
            '"${RUNNER_TEMP}/actionlint" .github/workflows/*.yml',
            'echo \'status=pass\' >> "$GITHUB_OUTPUT"',
            'echo "## Summary" >> "$GITHUB_STEP_SUMMARY"',
        )
        for value in allowed:
            with self.subTest(value=value):
                self.assertIsNone(active_path_guard.repo_bash_workflow_run_failure(value, tracked))

        blocked = {
            "set -euo pipefail": "workflow_shell_logic",
            "for item in one two; do echo $item; done": "workflow_shell_logic",
            "if test -f result.json; then python3 scripts/check.py; fi": "workflow_shell_logic",
            "check() { python3 scripts/check.py; }": "workflow_shell_logic",
            "python3 - <<'PY'": "workflow_heredoc",
            "python3 scripts/check.py $(git rev-parse HEAD)": "workflow_shell_logic",
            "bash scripts/check.py": "workflow_forbidden_command",
            "jq -e . result.json": "workflow_forbidden_command",
            "tools/check.sh": "workflow_forbidden_command",
            'echo "status=pass" >> "$OTHER_OUTPUT"': "workflow_shell_logic",
            "python3 scripts/check.py 2>&1": "workflow_shell_logic",
        }
        for value, expected_category in blocked.items():
            with self.subTest(value=value):
                failure = active_path_guard.repo_bash_workflow_run_failure(value, tracked)
                self.assertIsNotNone(failure)
                self.assertEqual(failure[0], expected_category)

    def test_workflow_python_dispatch_paths_are_tracked_and_confined(self) -> None:
        tracked = {"scripts/check.py", "scripts/not-python.txt"}
        self.assertIsNone(
            active_path_guard.repo_bash_workflow_run_failure(
                "python3 ./scripts/check.py --mode ci",
                tracked,
            )
        )
        blocked = (
            "python3 /tmp/external.py",
            "python3 C:/tmp/external.py",
            "python3 ../external.py",
            "python3 ~/external.py",
            "python3 scripts/untracked.py",
            "python3 scripts/not-python.txt",
        )
        for value in blocked:
            with self.subTest(value=value):
                candidate = value.split()[1]
                candidate_tracked = tracked if "untracked" in candidate else tracked | {candidate}
                failure = active_path_guard.repo_bash_workflow_run_failure(value, candidate_tracked)
                self.assertIsNotNone(failure)
                self.assertEqual(failure[0], "workflow_dispatch")

        invalid_python_shell_targets = (
            "/tmp/external.py",
            "C:/tmp/external.py",
            "../external.py",
            "~/external.py",
            "scripts/untracked.py",
            "scripts/not-python.txt",
        )
        for target in invalid_python_shell_targets:
            with self.subTest(shell_python_target=target):
                content = (
                    "jobs:\n"
                    "  check:\n"
                    "    steps:\n"
                    "      - shell: python\n"
                    f"        run: import runpy; runpy.run_path({target!r}, run_name='__main__')\n"
                )
                findings = active_path_guard.repo_bash_workflow_findings(
                    ".github/workflows/python-shell.yml",
                    content,
                    tracked if "untracked" in target else tracked | {target},
                )
                self.assertEqual([item.category for item in findings], ["workflow_dispatch"])

    def test_workflow_python_targets_reject_expansion_globs_and_drive_prefixes(self) -> None:
        blocked_targets = (
            "scripts/$TARGET.py",
            "scripts/${TARGET}.py",
            "scripts/*.py",
            "scripts/check?.py",
            "scripts/[ab].py",
            "scripts/{one,two}.py",
            "C:tools/check.py",
            "C:/tools/check.py",
            "C:\\tools\\check.py",
        )
        for target in blocked_targets:
            with self.subTest(target=target):
                tracked = {active_path_guard.normalize_path(target)}
                failure = active_path_guard.repo_bash_workflow_dispatch_path_failure(
                    target,
                    tracked,
                )
                self.assertIsNotNone(failure)

        for command in (
            "python3 'scripts/$TARGET.py'",
            "python3 scripts/*.py",
            "python3 C:tools/check.py",
        ):
            with self.subTest(command=command):
                target = command.split(maxsplit=1)[1].strip("'")
                failure = active_path_guard.repo_bash_workflow_run_failure(
                    command,
                    {active_path_guard.normalize_path(target)},
                )
                self.assertIsNotNone(failure)
                self.assertEqual(failure[0], "workflow_dispatch")

    def test_workflow_python_dispatch_rejects_tracked_external_symlink(self) -> None:
        workflow = {
            "path": ".github/workflows/external-python.yml",
            "content": (
                "jobs:\n"
                "  check:\n"
                "    steps:\n"
                "      - run: python3 scripts/external.py\n"
            ),
        }
        with tempfile.TemporaryDirectory(prefix="external-python-confinement-") as outside:
            outside_target = Path(outside) / "external.py"
            outside_target.write_text("print('external')\n", encoding="utf-8")
            with temporary_repo([workflow]) as root:
                link = root / "scripts" / "external.py"
                link.parent.mkdir(parents=True, exist_ok=True)
                try:
                    link.symlink_to(outside_target)
                except OSError as exc:
                    self.skipTest(f"symlink creation unavailable: {exc}")
                git(root, "add", "scripts/external.py")
                result = run_guard(root)
        self.assertEqual(result["status"], "expected_failure")
        self.assertIn(
            "workflow_dispatch",
            {item["category"] for item in result["data"]["findings"]},
        )

    def test_workflow_contexts_ignore_defaults_run_mapping(self) -> None:
        content = """\
defaults:
  run:
    shell: bash
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - run: python3 scripts/check.py
"""
        contexts = active_path_guard.workflow_run_contexts(content)
        self.assertEqual(len(contexts), 1)
        self.assertIn("python3 scripts/check.py", contexts[0][2])

    def test_allowlist_count_diagnostics_follow_the_canonical_set(self) -> None:
        short = json.loads(json.dumps(ALLOWLIST_DOCUMENT))
        short["entries"].pop()
        with temporary_repo(allowlist=short) as root:
            result = run_guard(root)
        details = result["diagnostics"][0]["details"]
        self.assertEqual(
            details["expected_entry_count"],
            len(active_path_guard.REPOSITORY_BASH_CONFINEMENT_ALLOWLIST_PATHS),
        )
        self.assertEqual(details["actual_entry_count"], len(short["entries"]))

    def test_nested_shell_payloads_are_inspected(self) -> None:
        source = """
import os
import subprocess

os.system("sh -c 'jq -e . result.json'")
subprocess.run(['cmd.exe', '/c', 'jq', '-e', '.', 'result.json'], shell=False)
"""
        findings = active_path_guard.repo_bash_python_findings("tools/nested.py", source)
        self.assertEqual(len(findings), 2)
        self.assertEqual({item.category for item in findings}, {"os_system", "command_argv_subprocess"})

    def test_sys_executable_is_safe_only_when_import_is_unshadowed(self) -> None:
        imported = "import subprocess\nimport sys\nsubprocess.run([sys.executable, '--version'])\n"
        self.assertEqual(active_path_guard.repo_bash_python_findings("tools/imported-sys.py", imported), [])

        shadowed = """
import subprocess
import sys

class Runtime:
    executable = 'bash'

sys = Runtime()
subprocess.run([sys.executable, '--version'])
"""
        findings = active_path_guard.repo_bash_python_findings("tools/shadowed-sys.py", shadowed)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].pattern, "<dynamic> --version")
        self.assertIn("cannot be statically resolved", findings[0].reason)

        unrelated_shadow = """
import subprocess
import sys

def unrelated():
    sys = object()
    return sys

def check():
    subprocess.run([sys.executable, '--version'])
"""
        self.assertEqual(
            active_path_guard.repo_bash_python_findings("tools/unrelated-shadow.py", unrelated_shadow),
            [],
        )

    def test_argv_mutations_preserve_static_bash_detection(self) -> None:
        expected_patterns = {
            "subscript-argv-assignment-fails": "bash --version",
            "list-augassign-argv-fails": "bash --version",
            "string-augassign-argv-fails": "bash --version",
            "insert-argv-mutation-fails": "bash --version",
            "append-argv-mutation-fails": "bash",
            "extend-argv-mutation-fails": "jq --version",
        }
        for case_id, expected_pattern in expected_patterns.items():
            with self.subTest(case_id=case_id):
                file = CASES_BY_ID[case_id]["files"][0]
                findings = active_path_guard.repo_bash_python_findings(file["path"], file["content"])
                self.assertEqual([item.pattern for item in findings], [expected_pattern])

        safe_file = CASES_BY_ID["safe-argv-mutations-pass"]["files"][0]
        self.assertEqual(active_path_guard.repo_bash_python_findings(safe_file["path"], safe_file["content"]), [])

    def test_from_sys_executable_is_safe_without_trusting_dynamic_imports(self) -> None:
        safe_file = CASES_BY_ID["from-sys-executable-passes"]["files"][0]
        self.assertEqual(active_path_guard.repo_bash_python_findings(safe_file["path"], safe_file["content"]), [])

        aliased = "import subprocess\nfrom sys import executable as python\nsubprocess.run([python, '--version'])\n"
        self.assertEqual(active_path_guard.repo_bash_python_findings("tools/aliased-executable.py", aliased), [])

        for case_id in (
            "from-sys-executable-rebound-import-fails",
            "sys-module-rebound-import-fails",
        ):
            with self.subTest(case_id=case_id):
                rebound = CASES_BY_ID[case_id]["files"][0]
                findings = active_path_guard.repo_bash_python_findings(rebound["path"], rebound["content"])
                self.assertEqual(len(findings), 1)
                self.assertEqual(findings[0].pattern, "<dynamic> --version")

        dynamic_file = CASES_BY_ID["dynamic-sys-import-fails-closed"]["files"][0]
        findings = active_path_guard.repo_bash_python_findings(dynamic_file["path"], dynamic_file["content"])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].pattern, "<dynamic> --version")

        shadowed = """
import subprocess
from sys import executable

executable = input('runtime: ')
subprocess.run([executable, '--version'])
"""
        findings = active_path_guard.repo_bash_python_findings("tools/shadowed-executable.py", shadowed)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].pattern, "<dynamic> --version")

    def test_active_instruction_surfaces_block_retired_shell_guidance(self) -> None:
        files = [
            {
                "path": ".claude/skills/custom-review/SKILL.md",
                "content": "Run scripts/review-pr.sh before opening the PR.\n",
            },
            {
                "path": "docs-site/src/content/docs/troubleshooting.md",
                "content": "Install jq and run it to repair the generated payload.\n",
            },
            {
                "path": ".claude/agents/custom-auditor.md",
                "content": "Run Bash to validate the release.\n",
            },
        ]
        with temporary_repo(files) as root:
            result = run_guard(root)
        blocking = [
            item for item in result["data"]["findings"] if item["classification"] == "blocking_repo_bash"
        ]
        self.assertEqual(result["status"], "expected_failure")
        self.assertEqual(
            {item["category"] for item in blocking},
            {"instruction_command", "instruction_script_path"},
        )
        self.assertEqual(
            {item["path"] for item in blocking},
            {
                ".claude/agents/custom-auditor.md",
                ".claude/skills/custom-review/SKILL.md",
                "docs-site/src/content/docs/troubleshooting.md",
            },
        )

    def test_active_instruction_classification_preserves_supported_context(self) -> None:
        files = [
            {
                "path": ".claude/skills/speckit-plan/SKILL.md",
                "content": "Run .specify/scripts/bash/setup-plan.sh --json from the repo root.\n",
            },
            {
                "path": ".claude/claude-security-guidance.md",
                "content": (
                    "Historical context: scripts/generate-pr-body.sh and external jq were retired.\n"
                    "Use gh pr view --json title --jq .title; gh --jq is not the external executable.\n"
                ),
            },
            {
                "path": "docs-site/src/content/docs/install/codex.md",
                "content": "The installed runtime does not require Bash, Git Bash, or external jq.\n",
            },
            {
                "path": ".github/copilot-instructions.md",
                "content": "Do not add a Bash or jq dependency. Use specify init --script sh when requested.\n",
            },
        ]
        with temporary_repo(files) as root:
            result = run_guard(root)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["data"]["blocking_count"], 0)

    def test_actionable_instruction_does_not_inherit_adjacent_history(self) -> None:
        content = (
            "Historical context: the old release helper was removed.\n"
            "Run scripts/revive-release.sh before publishing.\n"
            "Do not restore the retired helper.\n"
            "Install jq before validating the payload.\n"
        )
        findings = active_path_guard.repo_bash_instruction_findings("README.md", content)
        self.assertEqual(
            {(item.line, item.pattern) for item in findings},
            {
                (2, "scripts/revive-release.sh"),
                (4, "Install jq"),
            },
        )

        wrapped_negative = (
            "The installed runtime does not\n"
            "require Bash for validation.\n"
            "Operators must not\n"
            "install jq for this workflow.\n"
            "Do not add a required\n"
            "Bash or `jq` dependency to repository tests.\n"
        )
        self.assertEqual(
            active_path_guard.repo_bash_instruction_findings("README.md", wrapped_negative),
            [],
        )

    def test_operator_directive_does_not_inherit_adjacent_history(self) -> None:
        content = (
            "Historical context: scripts/retired-release.sh was removed.\n"
            "Operators should run scripts/revive-release.sh before publishing.\n"
        )
        findings = active_path_guard.repo_bash_instruction_findings("README.md", content)
        self.assertEqual(
            [(item.line, item.pattern) for item in findings],
            [(2, "scripts/revive-release.sh")],
        )

    def test_runtime_diagnostic_fields_block_obsolete_shell_remediation(self) -> None:
        files = [
            {
                "path": "speckit-pro/speckit_pro_runner/helpers/stale.py",
                "content": (
                    "def check():\n"
                    "    return diagnostic(\n"
                    "        'failed',\n"
                    "        'repair failed',\n"
                    "        remediation_actions=['Use scripts/repair-install.sh for mutation behavior.'],\n"
                    "    )\n"
                ),
            },
            {
                "path": "speckit-pro/speckit_pro_runner/helpers/stale_registry.py",
                "content": (
                    "ENTRY = MutationEntry(\n"
                    "    'id', 'operation', (), None, 'deferred', 'fixture', 'python', (), (),\n"
                    "    'Use tools/retry-release.sh until cutover.',\n"
                    ")\n"
                ),
            },
        ]
        with temporary_repo(files) as root:
            result = run_guard(root)
        blocking = [
            item for item in result["data"]["findings"] if item["classification"] == "blocking_repo_bash"
        ]
        self.assertEqual(result["status"], "expected_failure")
        self.assertEqual({item["category"] for item in blocking}, {"runtime_instruction_script_path"})
        self.assertEqual(len(blocking), 2)

    def test_runtime_diagnostics_resolve_static_names_and_containers(self) -> None:
        source = """
TOOL_PREFIX = 'j'
TOOL = TOOL_PREFIX + 'q'
SCRIPT = 'scripts/repair' + '-install.sh'
REMEDIATION = (
    f'Install {TOOL} before retrying.',
    {'fallback': [f'Run {SCRIPT} before retrying.']},
)
UNUSED = 'Run scripts/unrelated.sh from an implementation-only constant.'

def check():
    return diagnostic(
        'failed',
        'repair failed',
        remediation_actions=REMEDIATION,
    )
"""
        findings = active_path_guard.repo_bash_runtime_diagnostic_findings(
            "speckit-pro/speckit_pro_runner/helpers/static.py",
            source,
        )
        self.assertEqual(
            {item.pattern for item in findings},
            {"Install jq", "scripts/repair-install.sh"},
        )

    def test_runtime_diagnostics_resolve_format_percent_and_incremental_strings(self) -> None:
        source = """
FORMAT_ACTION = 'Install {} before retrying.'.format('jq')
PERCENT_ACTION = 'Run %s before retrying.' % 'scripts/repair-install.sh'

def check():
    incremental_action = 'Use '
    incremental_action += 'bash before retrying.'
    actions = []
    actions.append('Run scripts/rebuild-cache.sh before retrying.')
    return diagnostic(
        'failed',
        'repair failed',
        remediation_actions=[FORMAT_ACTION, PERCENT_ACTION, incremental_action, actions],
    )
"""
        findings = active_path_guard.repo_bash_runtime_diagnostic_findings(
            "speckit-pro/speckit_pro_runner/helpers/incremental.py",
            source,
        )
        self.assertEqual(
            {item.pattern for item in findings},
            {
                "Install jq",
                "scripts/repair-install.sh",
                "Use bash",
                "scripts/rebuild-cache.sh",
            },
        )

    def test_runtime_diagnostics_fail_closed_only_for_dangerous_dynamic_templates(self) -> None:
        source = """
UNRELATED = 'Install jq from an implementation-only constant.'

def check(tool, error):
    message = 'Run scripts/not-emitted.sh before retrying.'
    return diagnostic(
        'failed',
        f'Validation failed: {error}',
        remediation_actions=[
            f'Run {tool} before retrying.',
            f'Retry after reviewing {error}.',
        ],
    )
"""
        findings = active_path_guard.repo_bash_runtime_diagnostic_findings(
            "speckit-pro/speckit_pro_runner/helpers/dynamic.py",
            source,
        )
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].category, "runtime_instruction_dynamic")
        self.assertIn("<dynamic>", findings[0].pattern)

    def test_runtime_provenance_and_negative_diagnostics_remain_non_blocking(self) -> None:
        files = [
            {
                "path": "speckit-pro/speckit_pro_runner/helpers/provenance.py",
                "content": (
                    "def report():\n"
                    "    return {\n"
                    "        'inactive_provenance': {'prior_script': 'scripts/retired.sh'},\n"
                    "        'message': 'The retired Bash helper was removed.',\n"
                    "        'remediation_actions': ['Do not restore external jq.'],\n"
                    "    }\n"
                ),
            }
        ]
        with temporary_repo(files) as root:
            result = run_guard(root)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["data"]["blocking_count"], 0)

    def test_symlink_targets_are_confined_before_content_reads(self) -> None:
        with tempfile.TemporaryDirectory(prefix="repository-bash-outside-") as outside:
            outside_target = Path(outside) / "outside"
            outside_target.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            with temporary_repo() as root:
                link = root / "tools" / "external"
                link.parent.mkdir(parents=True, exist_ok=True)
                try:
                    link.symlink_to(outside_target)
                except OSError as exc:
                    self.skipTest(f"symlink creation unavailable: {exc}")
                git(root, "add", "tools/external")
                result = run_guard(root)
            self.assertEqual(result["status"], "ok")

            with temporary_repo() as root:
                link = root / "tools" / "external.sh"
                link.parent.mkdir(parents=True, exist_ok=True)
                link.symlink_to(outside_target)
                git(root, "add", "tools/external.sh")
                result = run_guard(root)
            self.assertEqual(result["status"], "expected_failure")
            self.assertIn("tools/external.sh", {item["path"] for item in result["data"]["findings"]})

    def test_git_enumeration_uses_exact_argv_and_fails_closed(self) -> None:
        real_run = subprocess.run
        with temporary_repo() as root:
            with patch.object(active_path_guard.subprocess, "run", wraps=real_run) as mocked:
                result = run_guard(root)
        self.assertEqual(result["status"], "ok")
        call = mocked.call_args_list[0]
        self.assertEqual(call.args[0], ["git", "ls-files", "-z"])
        self.assertEqual(call.kwargs["cwd"].resolve(), root.resolve())
        self.assertIs(call.kwargs["shell"], False)
        self.assertEqual(call.kwargs["timeout"], 30)

        with temporary_repo() as root:
            with patch.object(active_path_guard.subprocess, "run", side_effect=FileNotFoundError("git")):
                result = run_guard(root)
        self.assert_result_contract(result["data"])
        self.assertEqual(result["status"], "missing_prerequisite")
        self.assertEqual(result["exit_code"], 3)
        self.assertEqual([item["code"] for item in result["diagnostics"]], ["missing_prerequisite"])

        with tempfile.TemporaryDirectory(prefix="repository-bash-no-git-") as tmp:
            root = Path(tmp)
            (root / "speckit-pro" / "speckit_pro_runner").mkdir(parents=True)
            (root / "tests" / "speckit-pro").mkdir(parents=True)
            write_file(root, TEMP_ALLOWLIST, json.dumps(ALLOWLIST_DOCUMENT))
            result = run_guard(root)
        self.assert_result_contract(result["data"])
        self.assertEqual(result["status"], "missing_prerequisite")
        self.assertEqual(result["exit_code"], 3)
        self.assertEqual([item["code"] for item in result["diagnostics"]], ["missing_prerequisite"])

    def test_error_envelopes_do_not_claim_zero_blocks_or_completed_inspection(self) -> None:
        with temporary_repo() as root:
            allowlist_error = run_guard(root, allowlist_file="missing-allowlist.json")
        self.assertEqual(allowlist_error["status"], "input_error")
        self.assertGreater(allowlist_error["data"]["blocking_count"], 0)
        self.assertEqual(
            {
                allowlist_error["data"]["enumeration"][field]
                for field in (
                    "active_instruction_values",
                    "runtime_diagnostic_values",
                    "workflow_run_values",
                )
            },
            {"not_inspected"},
        )

        with temporary_repo() as root:
            with patch.object(active_path_guard.subprocess, "run", side_effect=FileNotFoundError("git")):
                git_error = run_guard(root)
        self.assertEqual(git_error["status"], "missing_prerequisite")
        self.assertGreater(git_error["data"]["blocking_count"], 0)
        self.assertEqual(
            {
                git_error["data"]["enumeration"][field]
                for field in (
                    "active_instruction_values",
                    "runtime_diagnostic_values",
                    "workflow_run_values",
                )
            },
            {"not_inspected"},
        )

    def test_guard_does_not_accept_fixed_file_inputs(self) -> None:
        with temporary_repo([{"path": "tools/stray.sh", "content": "#!/bin/sh\n"}]) as root:
            request = guard_request(root)
            request.inputs["files"] = []
            result = active_path_guard.run_active_path_guard(SimpleNamespace(helper_id="active-path-guard"), request)
        self.assertEqual(result["status"], "input_error")
        self.assertEqual(
            [item["code"] for item in result["diagnostics"]],
            ["unsupported_gate_inputs"],
        )


class RepoBashConfinementDurabilityTests(unittest.TestCase):
    def test_registry_release_and_default_suite_composition(self) -> None:
        from speckit_pro_runner.gates import registry, release

        operations = [item for item in registry.GATE_OPERATIONS if item.operation == "repo-bash-confinement"]
        self.assertEqual(len(operations), 1)
        self.assertTrue(operations[0].implemented)

        source = inspect.getsource(release.live_installed_release_gate_evidence)
        tree = ast.parse(source)
        release_checks = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "installed_release_check"
            and len(node.args) > 1
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "repo_bash_confinement"
            and isinstance(node.args[1], ast.Constant)
            and node.args[1].value == "active_repo_bash_dependency"
        ]
        self.assertEqual(len(release_checks), 1)

        manifest = json.loads((REPO_ROOT / "tests" / "speckit-pro" / "suite-manifest.json").read_text(encoding="utf-8"))
        layer4 = next(layer for layer in manifest["layers"] if layer["id"] == "4")
        members = [item for item in layer4["scripts"] if item["path"] == "tests/speckit-pro/unit/test-repo-bash-confinement.py"]
        self.assertEqual(len(members), 1)
        self.assertTrue(layer4["default"])


if __name__ == "__main__":
    names = sys.argv[1:] or ["RepoBashConfinementTests", "RepoBashConfinementDurabilityTests"]
    suite = unittest.defaultTestLoader.loadTestsFromNames(names, module=sys.modules[__name__])
    raise SystemExit(run_counted(suite, label="test-repo-bash-confinement"))
