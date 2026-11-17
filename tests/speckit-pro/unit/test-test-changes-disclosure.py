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

    def expect_function_changes(
        self, path: str, header: str, function: str, cases: dict[str, tuple[str, str, str | None]],
    ) -> None:
        """Commit one function per case, its body at base then at head, and expect each case's disclosure or none."""
        before, after = (
            header + "".join(function.format(name=name, body=case[side]) for name, case in cases.items())
            for side in (0, 1)
        )
        self.transition({path: before}, {path: after})
        output = self.expect(1)
        for name, (_, _, needed) in cases.items():
            with self.subTest(name=name):
                if needed is None:
                    self.assertNotIn(f"`{name}`", output)
                else:
                    self.assertIn(f"`{path}` ({needed}) in `{name}`", output)


class UnchangedTests(GitFixture):
    def test_no_test_changes_and_empty_test_inventory_pass(self) -> None:
        self.transition({"README.md": "before\n", "tests/test_sample.py": PYTHON}, {"README.md": "after\n"})
        self.expect(0)
        self.expect(0, BASE_REF="HEAD")

    def test_repository_without_test_files_passes(self) -> None:
        self.transition({"README.md": "before\n"}, {"README.md": "after\n"})
        self.expect(0)


class RemovalTests(GitFixture):
    def test_removal_disclosure_pairs_name_and_path_on_each_line(self) -> None:
        paths = ("tests/test_kept.py", "tests/nested/test_other.py")
        self.transition({path: PYTHON for path in paths}, {path: None for path in paths})
        for body in (
            "## Test changes\ntests/test_kept.py tests/nested/test_other.py",
            "## Test changes\ntest_kept tests/test_kept.py",
            "## Test changes\ntest_kept\ntests/test_kept.py\ntests/nested/test_other.py",
        ):
            with self.subTest(body=body):
                output = self.expect(1, body)
                self.assertIn('`test_kept` (`tests/nested/test_other.py`)', output)
        output = self.expect(1, "## Test changes\ntest_kept tests/test_kept.py tests/nested/test_other.py")
        self.assertEqual(1, output.count("- Removed or renamed `test_kept`"))
        self.expect(0, "## Test changes\ntest_kept tests/test_kept.py\ntest_kept tests/nested/test_other.py")

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
            "- Removed or renamed `test_before` (`tests/test_sample.py`).\n"
            "- Lost assertions: `tests/test_sample.py` (1 net assertion line lost) in `test_before` of `Sample`.\n",
            result.stderr,
        )
        self.expect(1, "## Test changes\ntest_after")
        self.expect(0, "## Test changes\ntest_before tests/test_sample.py")


class MoveTests(GitFixture):
    def test_same_directory_rename_reports_two_lost_assertions_at_old_path(self) -> None:
        source = 'def test_one():\n    x = 1\n    assert x == 1\n    assert x > 0\n'
        self.transition(
            {"tests/test_a.py": source},
            {"tests/test_a.py": None, "tests/test_b.py": 'def test_one():\n    x = 1\n'},
        )
        output = self.expect(1)
        self.assertIn('`tests/test_a.py` (2 net assertion lines lost)', output)
        self.assertNotIn("Removed or renamed", output)
        self.expect(1, "## Test changes\ntests/test_a.py")
        self.expect(0, "## Test changes\ntest_one tests/test_a.py")

    def test_same_directory_rename_preserves_every_assertion(self) -> None:
        source = PYTHON + '    assert 1 == 1\n'
        self.transition(
            {"tests/test_a.py": source},
            {"tests/test_a.py": None, "tests/test_b.py": source},
        )
        self.expect(0)

    def test_vanished_files_share_only_new_file_assertions_in_the_same_scope(self) -> None:
        self.transition(
            {"tests/test_a.py": PYTHON, "tests/test_b.py": PYTHON, "tests/test_kept.py": PYTHON},
            {
                "tests/test_a.py": None, "tests/test_b.py": None,
                "tests/test_c.py": PYTHON,
                "tests/nested/test_d.py": PYTHON,
                "tests/test_kept.py": PYTHON + '    assert 1 == 1\n',
            },
        )
        output = self.expect(1)
        self.assertEqual(1, output.count("net assertion line lost"))
        self.assertIn('`tests/test_b.py` (1 net assertion line lost)', output)

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
    def test_fstring_literal_assertions_do_not_hide_two_lost_lines(self) -> None:
        path = "tests/test_sample.py"
        before = 'def test_one():\n    x = 1\n    assert x == 1\n    assert x > 0\n'
        after = 'def test_one():\n    x = 1\n    print(f"assert x == 1 {x}")\n    print(f"assert x > 0 {x}")\n'
        self.transition({path: before}, {path: after})
        self.assertIn(f'`{path}` (2 net assertion lines lost)', self.expect(1))

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
        self.write("tests/test_gate.py", '"""Module docstring: assert False\nself.assertTrue(False)\n"""\n' + python + '''    # assert False
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
        self.git("branch", "literal-base")
        self.write("tests/test_gate.py", python)
        self.write("pkg/gate_test.go", go)
        self.commit()
        self.expect(0, BASE_REF="literal-base")

    def test_assertion_losses_require_each_file_path_and_report_net_count(self) -> None:
        self.base({"pkg/sample_test.go": GO, "tests/test_sample.py": PYTHON})
        self.write("pkg/sample_test.go", GO.replace('t.Fatal("kept")', "_ = t"))
        self.write("tests/test_sample.py", PYTHON.replace("assert True", "pass"))
        self.commit()
        output = self.expect(1)
        self.assertEqual(2, output.count("net assertion line lost"))
        output = self.expect(1, "## Test changes\npkg/sample_test.go")
        self.assertIn("- Lost assertions: `tests/test_sample.py`", output)
        self.expect(1, "## Test changes\npkg/sample_test.go tests/test_sample.py")
        self.expect(0, "## Test changes\nTestKept pkg/sample_test.go\ntest_kept tests/test_sample.py")


def asserts(prefix: str, count: int) -> str:
    return "".join(f"    assert {prefix}{index} == {index}\n" for index in range(count))


class FunctionMoveTests(GitFixture):
    def test_rename_cannot_borrow_assertions_from_an_unrelated_new_file(self) -> None:
        self.transition(
            {"tests/test_a.py": "def test_a():\n" + asserts("x", 3)},
            {
                "tests/test_a.py": None, "tests/test_b.py": "def test_a():\n    pass\n",
                "tests/test_c.py": "def test_c():\n" + asserts("y", 3),
            },
        )
        output = self.expect(1, "## Test changes\ntests/test_a.py")
        self.assertIn("- Lost assertions: `tests/test_a.py` (3 net assertion lines lost) in `test_a`.", output)
        self.expect(0, "## Test changes\ntest_a tests/test_a.py")

    def test_split_moves_a_function_with_its_assertions(self) -> None:
        before = "def test_a():\n" + asserts("x", 2) + "def test_b():\n" + asserts("y", 2)
        self.transition(
            {"tests/test_a.py": before},
            {"tests/test_a.py": "def test_a():\n" + asserts("x", 2), "tests/test_a2.py": "def test_b():\n" + asserts("y", 2)},
        )
        self.expect(0)

    def test_function_moved_into_an_existing_file_keeps_its_assertions(self) -> None:
        moved = "def test_one():\n" + asserts("x", 2)
        self.transition(
            {"tests/test_a.py": moved, "tests/test_b.py": PYTHON},
            {"tests/test_a.py": None, "tests/test_b.py": PYTHON + moved},
        )
        self.expect(0)

    def test_function_moved_to_another_directory_needs_disclosure(self) -> None:
        helper = "def check_value(value):\n    assert value > 0\n"
        self.transition(
            {"tests/test_a.py": PYTHON + helper},
            {"tests/test_a.py": PYTHON + "    assert 1 == 1\n", "tests/nested/test_helpers.py": helper},
        )
        output = self.expect(1)
        self.assertIn("- Lost assertions: `tests/test_a.py` (1 net assertion line lost) in `check_value`.", output)
        self.expect(0, "## Test changes\ncheck_value tests/test_a.py")


class AssertionChangeTests(GitFixture):
    def test_rewritten_assertions_with_the_same_count_need_disclosure(self) -> None:
        python = 'def test_one(value):\n    assert value == "abc"\n    self.assertEqual(\n        1,\n        value,\n    )\n'
        go = 'package sample\ntype fixture struct{}\nfunc (f *fixture) check(t *testing.T) {\n    t.Fatalf("want %d", 1)\n}\n'
        self.transition(
            {"tests/test_sample.py": python, "pkg/sample_test.go": go},
            {
                "tests/test_sample.py": python.replace('"abc"', '"abd"').replace("        1,", "        2,"),
                "pkg/sample_test.go": go.replace("t.Fatalf", "t.Errorf"),
            },
        )
        output = self.expect(1, "## Test changes\ntests/test_sample.py pkg/sample_test.go")
        self.assertIn("- Changed assertions: `tests/test_sample.py` (2 assertion lines changed) in `test_one`.", output)
        self.assertIn("- Changed assertions: `pkg/sample_test.go` (1 assertion line changed) in `check` of `fixture`.", output)
        self.expect(0, "## Test changes\ntest_one tests/test_sample.py\ncheck pkg/sample_test.go")

    def test_added_assertions_and_comment_edits_alone_pass(self) -> None:
        before = "def test_one(value):\n    assert value  # first\n"
        self.transition(
            {"tests/test_sample.py": before},
            {"tests/test_sample.py": before.replace("# first", "# renamed comment") + "    assert   value > 0\n"},
        )
        self.expect(0)

    def test_printed_disclosures_pasted_back_pass(self) -> None:
        self.transition(
            {
                "tests/test_class.py": "import sys\nassert sys\nclass Sample:\n    def test_before(self):\n"
                                       "        self.assertTrue(1)\n    def test_kept(self):\n        assert 1\n",
                "pkg/sample_test.go": GO + 'type fixture struct{}\nfunc (f fixture) check(t *testing.T) {\n    t.Error("x")\n}\n',
            },
            {
                "tests/test_class.py": "class Sample:\n    def test_after(self):\n        self.assertTrue(1)\n"
                                       "    def test_kept(self):\n        assert 2\n",
                "pkg/sample_test.go": 'package sample\ntype fixture struct{}\nfunc (f fixture) check(t *testing.T) {\n}\n',
            },
        )
        output = self.expect(1)
        for line in (
            "- Lost assertions: `tests/test_class.py` (1 net assertion line lost) at module level.",
            "- Lost assertions: `tests/test_class.py` (1 net assertion line lost) in `test_before` of `Sample`.",
            "- Changed assertions: `tests/test_class.py` (1 assertion line changed) in `test_kept` of `Sample`.",
            "- Lost assertions: `pkg/sample_test.go` (1 net assertion line lost) in `check` of `fixture`.",
            "- Lost assertions: `pkg/sample_test.go` (1 net assertion line lost) in `TestKept`.",
        ):
            self.assertIn(line, output)
        self.expect(0, "## Test changes\n" + output.split("## Test changes\n", 1)[1])


class AssertionSpellingTests(GitFixture):
    def test_every_assertion_spelling_counts(self) -> None:
        python = "def test_one(x):\n    assert(False)\n    assert(x == 1)\n"
        go = (
            "package sample\nfunc TestOne(t *testing.T) {\n    t.Fail()\n    t.FailNow()\n    t.Fatal (1)\n}\n"
            "func BenchmarkOne(b *testing.B) {\n    b.Fatal(1)\n}\nfunc helper(tb testing.TB) {\n    tb.Error(1)\n}\n"
        )
        self.transition(
            {"tests/test_one.py": python, "pkg/one_test.go": go},
            {
                "tests/test_one.py": "def test_one(x):\n    pass\n",
                "pkg/one_test.go": "package sample\nfunc TestOne(t *testing.T) {}\n"
                                   "func BenchmarkOne(b *testing.B) {}\nfunc helper(tb testing.TB) {}\n",
            },
        )
        output = self.expect(1)
        for line in (
            "`tests/test_one.py` (2 net assertion lines lost) in `test_one`",
            "`pkg/one_test.go` (3 net assertion lines lost) in `TestOne`",
            "`pkg/one_test.go` (1 net assertion line lost) in `BenchmarkOne`",
            "`pkg/one_test.go` (1 net assertion line lost) in `helper`",
        ):
            self.assertIn(line, output)

    def test_whitespace_inside_string_literals_is_compared_exactly(self) -> None:
        cases = {
            "tests/test_sample.py": ("test_one", 'def test_one(value):\n    assert " " not in value\n', '" "', '"  "'),
            "pkg/sample_test.go": ("TestOne", 'package sample\nfunc TestOne(t *testing.T) {\n    t.Fatal("a\tb")\n}\n', "a\tb", "a b"),
        }
        self.transition(
            {path: case[1] for path, case in cases.items()},
            {path: case[1].replace(case[2], case[3]) for path, case in cases.items()},
        )
        output = self.expect(1)
        for path, case in cases.items():
            self.assertIn(f"`{path}` (1 assertion line changed) in `{case[0]}`", output)


class PythonSyntaxTreeTests(GitFixture):
    PATH = "tests/test_sample.py"

    def test_assertions_are_read_as_whole_statements(self) -> None:
        self.expect_function_changes(self.PATH, "", "def {name}(self, value):\n    {body}\n", {
            "test_string_tail": (
                'assert """a\nb""" not in value', 'assert """a\nbc""" not in value', "1 assertion line changed",
            ),
            "test_string_newlines": (
                'assert ("""\n\n""" not in value)', 'assert ("""\n\n\n""" not in value)', "1 assertion line changed",
            ),
            "test_split_selector": ("(self\n        .assertEqual(1, 1))", "pass", "1 net assertion line lost"),
            # A fixture helper whose name only starts with `fail` is not an assertion.
            "test_fail_calls": (
                'self.fail("first")\n    pytest.fail("second")\n    self.failing_write()', "pass",
                "2 net assertion lines lost",
            ),
            "test_shared_line": ("assert value; assert value > 1", "assert value", "1 net assertion line lost"),
            "test_reformatted": (
                'assert(value == "a")\n    self.assertEqual(1, value)',
                "assert value == 'a'  # same check\n    self.assertEqual(\n        1,\n        value,\n    )",
                None,
            ),
        })

    def test_code_too_deep_to_read_fails_closed_naming_the_file_and_ref(self) -> None:
        self.transition(
            {self.PATH: PYTHON},
            {self.PATH: "def test_kept():\n    assert " + " + ".join(["1"] * 5000) + "\n"},
        )
        output = self.expect(1, "## Test changes\ntest_kept " + self.PATH)
        self.assertIn(f"unparseable test file {self.PATH} at {self.git('rev-parse', 'HEAD')}", output)
        self.assertNotIn("Traceback", output)


class GoTokenStreamTests(GitFixture):
    PATH = "pkg/sample_test.go"

    def test_assertions_are_read_as_whole_calls(self) -> None:
        function = "func {name}(t *testing.T) {{\n    {body}\n}}\n"
        self.expect_function_changes(self.PATH, "package sample\n", function, {
            "TestSplitSelector": (
                't.\n    Error("bad")\n    require.\n        NoError(t, nil)', "", "2 net assertion lines lost",
            ),
            "TestRawString": (
                "t.Fatal(`a\n\nb`)\n    t.Error(`c\nd`)", "t.Fatal(`a\nb`)\n    t.Error(`c\nde`)", "2 assertion lines changed",
            ),
            "TestSharedLine": (
                'if testing.Short() { t.Error("a") } else { t.Error("b") }',
                'if testing.Short() { t.Error("a") } else {}',
                "1 net assertion line lost",
            ),
            "TestChainedCall": ("assert.New(t).Equal(1, 1)", "assert.New(t).Equal(1, 2)", "1 assertion line changed"),
            "TestReformatted": (
                't.Fatalf("want %d, got %d", 1, 2)',
                't.Fatalf( // values\n        "want %d, got %d",\n        1, 2,\n    )',
                None,
            ),
        })

    def test_receiver_methods_are_keyed_by_type_through_type_parameters_and_parentheses(self) -> None:
        before = (
            "package sample\nfunc (s *Stack[T]) check(t *testing.T) {\n    t.Error(1)\n}\n"
            "func ((*fixture)) check(t *testing.T) {\n    t.Error(2)\n}\n"
        )
        self.transition({self.PATH: before}, {self.PATH: before.replace("    t.Error(1)\n", "").replace("(2)", "(3)")})
        output = self.expect(1)
        self.assertIn(f"`{self.PATH}` (1 net assertion line lost) in `check` of `Stack`", output)
        self.assertIn(f"`{self.PATH}` (1 assertion line changed) in `check` of `fixture`", output)

    def test_unreadable_go_fails_closed_naming_the_file_and_ref(self) -> None:
        self.base({self.PATH: GO})
        for source in ('var text = "open\n', "/* open\n", "var text = 'x\n", "var value = 1 ? 2\n"):
            with self.subTest(source=source):
                self.write(self.PATH, GO + source)
                self.commit()
                output = self.expect(1, "## Test changes\nTestKept " + self.PATH)
                self.assertIn(f"unparseable test file {self.PATH} at {self.git('rev-parse', 'HEAD')}", output)
                self.assertNotIn("Traceback", output)


class DeletedFileTests(GitFixture):
    def test_deleted_file_assertions_are_lost_even_when_names_are_disclosed(self) -> None:
        path = "tests/test_sample.py"
        self.transition({path: PYTHON + '    assert 1 == 1\n'}, {path: None})
        self.assertIn(f'`{path}` (2 net assertion lines lost)', self.expect(1))
        self.expect(0, f"## Test changes\ntest_kept {path}")

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
        self.expect(0, "## Test changes\nTestKept ExampleSample pkg/sample_test.go\n"
                    "test_kept test_other tests/speckit-pro/unit/test-sample.py")

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
    def test_disclosure_job_pins_python_to_the_pr_checks_version_and_action(self) -> None:
        workflows = REPO_ROOT / ".github/workflows"
        checks = (workflows / "pr-checks.yml").read_text(encoding="utf-8")
        metadata = (workflows / "pr-metadata.yml").read_text(encoding="utf-8")
        setup = checks.split("      - name: Set up Python 3.11\n", 1)[1].split("\n\n", 1)[0]
        job = metadata.split("  validate-test-changes:\n", 1)[1]
        self.assertIn(setup, job)
        self.assertLess(job.index(setup), job.index("run: python3"))

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
