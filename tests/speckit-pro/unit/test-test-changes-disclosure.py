#!/usr/bin/env python3
"""Exercise the test-change gate against committed histories, never working files."""

from __future__ import annotations

import os
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "check-test-changes.py"
sys.path.insert(0, str(REPO_ROOT / "tests/speckit-pro/lib"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from test_result import run_counted  # noqa: E402
from git_fixture import commit_baseline, git_stdout  # noqa: E402
from isolated_child import run_python  # noqa: E402
from script_loader import load_script  # noqa: E402

GO = 'package sample\nimport "testing"\nfunc TestKept(t *testing.T) { t.Fatal("kept") }\n'
PYTHON = 'def test_kept():\n    assert True\n'


class GitFixture(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.repo = Path(directory.name)
        for path in ("pkg", "other", "tests/nested", "tests/speckit-pro/unit"):
            (self.repo / path).mkdir(parents=True, exist_ok=True)
        self.environment = {
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1", "PR_BODY": "", "BASE_REF": "base", "HEAD_REF": "HEAD",
        }

    def git(self, *args: str) -> str:
        return git_stdout(self.repo, *args)

    def write(self, path: str, content: str) -> None:
        (self.repo / path).write_text(content, encoding="utf-8")

    def commit(self) -> None:
        commit_baseline(self.repo)

    def base(self, files: dict[str, str]) -> None:
        files = {"tests/speckit-pro/suite-manifest.json": '{"layers": []}\n'} | files
        for path in files:
            self.write(path, files[path])
        self.commit()
        self.git("branch", "base")

    def transition(self, before: dict[str, str], changes: dict[str, str | None]) -> None:
        self.base(before)
        for path, content in changes.items():
            if content is None:
                (self.repo / path).unlink()
            else:
                self.write(path, content)
        self.commit()

    def check(self, body: str = "", **environment: str) -> subprocess.CompletedProcess[str]:
        return run_python(
            [str(SCRIPT)], cwd=self.repo,
            env_extra=self.environment | {"PR_BODY": body} | environment,
            encoding="utf-8",
        )

    def expect(self, status: int, body: str = "", **environment: str) -> str:
        result = self.check(body, **environment)
        output = result.stdout + result.stderr
        self.assertEqual(status, result.returncode, output)
        self.assertIn("Test changes", output)
        return output


class UnchangedTests(GitFixture):
    def test_no_test_changes_and_empty_test_inventory_pass(self) -> None:
        self.transition({"README.md": "before\n", "tests/test_sample.py": PYTHON}, {"README.md": "after\n"})
        self.expect(0)
        self.expect(0, BASE_REF="HEAD")

    def test_repository_without_test_files_passes(self) -> None:
        self.transition({"README.md": "before\n"}, {"README.md": "after\n"})
        self.expect(0)


class RemovalTests(GitFixture):
    def test_manifest_registered_files_at_either_ref_are_tests(self) -> None:
        paths = ("tests/speckit-pro/unit/validate-old.py", "tests/speckit-pro/unit/validate-new.py")
        manifest = "tests/speckit-pro/suite-manifest.json"
        self.base({
            manifest: json.dumps({"layers": [{"scripts": [{"path": paths[0]}]}]}),
            paths[0]: PYTHON, paths[1]: PYTHON,
        })
        self.write(manifest, json.dumps({"layers": [{"scripts": [{"path": paths[1]}]}]}))
        self.write(paths[0], "")
        self.write(paths[1], PYTHON.replace("assert True", "pass"))
        self.commit()
        output = self.expect(1)
        self.assertIn(f'`test_kept` (`{paths[0]}`)', output)
        for path in paths:
            self.assertIn(f'`{path}` (1 net assertion line lost)', output)

    def test_removed_go_test_requires_exact_name_in_the_section(self) -> None:
        self.base({"pkg/sample_test.go": GO})
        self.write("pkg/sample_test.go", "package sample\n")
        self.commit()
        output = self.expect(1)
        self.assertIn("`TestKept`", output)
        self.assertIn("`pkg/sample_test.go` (1 net assertion line lost)", output)
        self.expect(1, "TestKept pkg/sample_test.go\n## Test changes\nTestKeptExtra")
        self.expect(1, "## Test changes\nTestKept\n## Other\npkg/sample_test.go")
        self.expect(0, "## Test changes\nTestKept pkg/sample_test.go")

    def test_renamed_python_class_test_requires_the_old_name(self) -> None:
        before = "class Sample:\n    def test_before(self):\n        assert True\n"
        path = "tests/test_sample.py"
        self.base({path: before})
        self.write(path, before.replace("test_before", "test_after"))
        self.commit()
        result = self.check()
        self.assertEqual(1, result.returncode)
        self.assertEqual(
            "::error::Test changes require disclosure in a ## Test changes section.\n"
            "Missing disclosures (paste into the PR body):\n## Test changes\n"
            "- Removed or renamed `test_before` (`tests/test_sample.py`).\n",
            result.stderr,
        )
        self.expect(1, "## Test changes\ntest_after")
        self.expect(0, "## Test changes\ntest_before")


class MoveTests(GitFixture):
    def test_go_move_in_same_package_passes_but_other_package_does_not(self) -> None:
        self.base({"pkg/old_test.go": GO})
        (self.repo / "pkg/old_test.go").unlink()
        self.write("pkg/new_test.go", GO)
        self.commit()
        self.expect(0)
        (self.repo / "pkg/new_test.go").unlink()
        self.write("other/new_test.go", GO)
        self.commit()
        self.expect(1)

    def test_existing_python_namesake_does_not_hide_a_removal(self) -> None:
        self.transition(
            {"tests/test_old.py": PYTHON, "tests/nested/new_test.py": PYTHON},
            {"tests/test_old.py": None},
        )
        self.assertIn("`test_kept` (`tests/test_old.py`)", self.expect(1))

    def test_python_move_requires_same_directory(self) -> None:
        source = 'def test_invalid_input_fails_closed():\n    assert check("bad") == 1\n'
        self.base({"tests/test_old.py": source})
        (self.repo / "tests/test_old.py").unlink()
        self.write("tests/new_test.py", source)
        self.commit()
        self.expect(0)
        (self.repo / "tests/new_test.py").unlink()
        self.write("tests/nested/new_test.py", source.replace('assert check("bad") == 1', "pass"))
        self.commit()
        self.assertIn('`test_invalid_input_fails_closed` (`tests/test_old.py`)', self.expect(1))


class AssertionTests(GitFixture):
    def test_commented_assertions_are_losses_and_literals_do_not_count(self) -> None:
        python = 'def test_gate():\n    assert check("bad") == 1\n'
        go = 'package sample\nfunc TestGate(t *testing.T) {\n    t.Fatal("bad")\n}\n'
        self.transition(
            {"tests/test_gate.py": python, "pkg/gate_test.go": go},
            {
                "tests/test_gate.py": python.replace('    assert', '    # assert') + '    pass\n',
                "pkg/gate_test.go": go.replace('    t.Fatal', '    // t.Fatal'),
            },
        )
        output = self.expect(1)
        self.assertIn('`tests/test_gate.py` (1 net assertion line lost)', output)
        self.assertIn('`pkg/gate_test.go` (1 net assertion line lost)', output)
        self.write("tests/test_gate.py", python + '''    # assert False
    """assert False
    self.assertEqual(1, 2)
    """
    text = 'pytest.raises(Error)'
''')
        self.write("pkg/gate_test.go", go + '''// t.Fatal("bad")
/* require.Fail(t)
assert.False(t) */
var text = "t.Fatal("
var raw = `
t.Error("bad")
`
''')
        self.commit()
        self.expect(0)

    def test_assertion_losses_require_each_file_path_and_report_net_count(self) -> None:
        self.base({"pkg/sample_test.go": GO, "tests/test_sample.py": PYTHON})
        self.write("pkg/sample_test.go", GO.replace('t.Fatal("kept")', "_ = t"))
        self.write("tests/test_sample.py", PYTHON.replace("assert True", "pass"))
        self.commit()
        output = self.expect(1)
        self.assertEqual(2, output.count("net assertion line lost"))
        output = self.expect(1, "## Test changes\npkg/sample_test.go")
        self.assertIn("- Lost assertions: `tests/test_sample.py`", output)
        self.expect(0, "## Test changes\npkg/sample_test.go tests/test_sample.py")


class DeletedFileTests(GitFixture):
    def test_go_inventory_needs_no_go_and_excludes_receiver_methods(self) -> None:
        source = GO + '''func BenchmarkWork(b *testing.B) {}
func FuzzWork(f *testing.F) {}
func ExampleWork() {}
func (r Receiver) TestMethod(t *testing.T) {}
func Testhelper(t *testing.T) {}
'''
        self.base({"pkg/sample_test.go": source})
        with tempfile.TemporaryDirectory() as directory:
            git = shutil.which("git")
            self.assertIsNotNone(git)
            (Path(directory) / "git").symlink_to(str(git))
            path = directory + os.pathsep + os.pathsep.join(("/usr/bin", "/bin"))
            self.assertIsNone(shutil.which("go", path=path))
            self.assertIsNone(shutil.which("gofmt", path=path))
            self.expect(0, PATH=path)
            self.write("pkg/sample_test.go", "package sample\n")
            self.commit()
            output = self.expect(1, PATH=path)
        for name in ("TestKept", "BenchmarkWork", "FuzzWork", "ExampleWork"):
            self.assertIn(f"`{name}`", output)
        self.assertNotIn("TestMethod", output)
        self.assertNotIn("Testhelper", output)

    def test_deleted_test_files_list_every_function_and_cover_layer_script_names(self) -> None:
        files = {
            "pkg/sample_test.go": GO + "func ExampleSample() {}\n",
            "tests/speckit-pro/unit/test-sample.py": PYTHON + "def test_other():\n    pass\n",
        }
        self.base(files)
        for path in files:
            (self.repo / path).unlink()
        self.commit()
        output = self.expect(1)
        for name in ("TestKept", "ExampleSample", "test_kept", "test_other"):
            self.assertIn(f"`{name}`", output)
        self.expect(0, "## Test changes\nTestKept ExampleSample test_kept test_other")

    def test_benchmarks_fuzz_and_examples_ignore_comments_and_strings(self) -> None:
        source = GO + '''func BenchmarkWork(b *testing.B) {}
func FuzzWork(f *testing.F) {}
func ExampleWork() {}
/* func TestComment(t *testing.T) {} */
var text = `
func TestString(t *testing.T) {}
`
'''
        self.base({"pkg/sample_test.go": source})
        (self.repo / "pkg/sample_test.go").unlink()
        self.commit()
        output = self.expect(1)
        for name in ("TestKept", "BenchmarkWork", "FuzzWork", "ExampleWork"):
            self.assertIn(f"`{name}`", output)
        self.assertNotIn("TestComment", output)
        self.assertNotIn("TestString", output)


class FailClosedTests(GitFixture):
    def test_missing_or_malformed_manifest_at_either_ref_fails_closed(self) -> None:
        path = "tests/speckit-pro/suite-manifest.json"
        self.base({"tests/test_sample.py": PYTHON})
        for value in (None, "{", "[]", '{"layers": [{}]}', '{"layers": [{"scripts": [null]}]}'):
            with self.subTest(value=value):
                if value is None:
                    (self.repo / path).unlink()
                else:
                    self.write(path, value)
                self.commit()
                output = self.expect(1)
                self.assertIn("suite-manifest.json", output)
                # Reverse refs so the broken manifest is also checked at the merge-base.
                broken = self.git("rev-parse", "HEAD")
                self.write(path, '{"layers": []}\n')
                self.commit()
                self.assertIn("suite-manifest.json", self.expect(1, BASE_REF=broken))

    def test_git_errors_and_missing_inputs_fail_closed(self) -> None:
        self.base({"tests/test_sample.py": PYTHON})
        for environment in ({"BASE_REF": "missing"}, {"HEAD_REF": "missing"}, {"BASE_REF": ""}):
            with self.subTest(environment=environment):
                self.assertIn("::error::", self.expect(1, **environment))

    def test_unparseable_python_and_go_fail_even_with_disclosure(self) -> None:
        self.base({"tests/test_sample.py": PYTHON, "pkg/sample_test.go": GO})
        for path, source in (
            ("tests/test_sample.py", "def test_broken(:\n"),
            ("pkg/sample_test.go", "package sample\nfunc TestBroken( {\n"),
            ("pkg/sample_test.go", "func TestFragment(t *testing.T) {}\n"),
        ):
            with self.subTest(path=path):
                self.write(path, source)
                self.commit()
                self.assertIn("unparseable", self.expect(1, "## Test changes\ntest_kept TestKept"))
                self.write(path, PYTHON if path.endswith(".py") else GO)


class ComparisonTests(GitFixture):
    def test_fence_with_info_string_cannot_close_an_enclosing_fence(self) -> None:
        self.transition({"tests/test_sample.py": PYTHON}, {"tests/test_sample.py": None})
        for opening, fake_close, close in (
            ("```text", "```md", "```"),
            ("~~~~text", "~~~", "~~~~"),
            ("> ```text", "> ```md", "> ```"),
            ("- ```text", "  ```md", "  ```"),
        ):
            with self.subTest(opening=opening):
                body = f"{opening}\n{fake_close}\n## Test changes\ntest_kept tests/test_sample.py\n{close}"
                self.expect(1, body)
        self.expect(0, "```text\nexample\n```\n## Test changes\ntest_kept tests/test_sample.py")

    def test_three_dot_comparison_ignores_base_only_changes_and_working_files(self) -> None:
        self.base({"tests/test_sample.py": PYTHON})
        self.git("checkout", "-qb", "topic")
        self.write("README.md", "topic\n")
        self.commit()
        topic = self.git("rev-parse", "HEAD")
        self.git("checkout", "-q", "base")
        self.write("tests/test_sample.py", PYTHON + "def test_base_only():\n    pass\n")
        self.commit()
        self.git("checkout", "-q", "topic")
        self.write("tests/test_sample.py", "invalid working file")
        self.expect(0, HEAD_REF=topic)

    def test_disclosure_heading_in_comment_or_fence_does_not_count(self) -> None:
        self.base({"tests/test_sample.py": PYTHON, "README.md": "fixture\n"})
        self.git("rm", "tests/test_sample.py")
        self.commit()
        for body in ("<!--\n## Test changes\ntest_kept\n-->", "```md\n## Test changes\ntest_kept\n```"):
            with self.subTest(body=body):
                self.expect(1, body)


class WorkflowTests(unittest.TestCase):
    def test_job_uses_full_history_exact_pr_head_and_environment_inputs(self) -> None:
        workflow = (REPO_ROOT / ".github/workflows/pr-metadata.yml").read_text(encoding="utf-8")
        job = workflow.split("  validate-test-changes:\n", 1)[1]
        self.assertIn("edited", workflow.split("  workflow_dispatch:", 1)[0])
        for contract in (
            "fetch-depth: 0", "persist-credentials: false",
            "permissions: {contents: read, pull-requests: read}",
            "'manual-validate-test-changes' || 'validate-test-changes'",
            "BASE_REF:", "github.event.pull_request.base.sha", "HEAD_REF:",
            "github.event.pull_request.head.sha", "PR_BODY:", "PR_INCLUDE_BASE_REF: 'true'",
            "run: python3 scripts/check-test-changes.py",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, job)
        self.assertFalse(any("${{" in line for line in job.splitlines() if "run:" in line))
        self.assertNotIn("actions/setup-go", job)

    def test_manual_metadata_can_supply_the_authenticated_base_ref(self) -> None:
        metadata = load_script("test_change_metadata", REPO_ROOT / "scripts/pr_metadata.py")
        sha = "a" * 40
        pr = {
            "number": 1, "state": "open", "title": "test", "body": "", "labels": [], "draft": False,
            "base": {"ref": "main", "repo": {"full_name": "example/project"}},
            "head": {"ref": "topic", "sha": sha, "repo": {"full_name": "example/project"}},
        }
        environment = {
            "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REPOSITORY": "example/project",
            "PR_NUMBER": "1", "GITHUB_REF": "refs/heads/topic", "GITHUB_SHA": sha,
            "PR_INCLUDE_BASE_REF": "true",
        }
        fetch = mock.Mock(return_value=pr)
        self.assertEqual("refs/remotes/origin/main", metadata.manual_pr_metadata(environment, fetch=fetch)["base_ref"])
        for value in (None, "", 123):
            with self.subTest(value=value), self.assertRaises(ValueError):
                pr["base"]["ref"] = value
                metadata.manual_pr_metadata(environment, fetch=fetch)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    raise SystemExit(run_counted(suite, label="test-test-changes-disclosure"))
