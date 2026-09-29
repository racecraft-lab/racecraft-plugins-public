#!/usr/bin/env python3
"""Contracts for the purpose-based unit-test and fixture layout."""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
UNIT_ROOT = TEST_ROOT / "unit"
FIXTURE_ROOT = UNIT_ROOT / "fixtures"
LIB_DIR = TEST_ROOT / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted  # noqa: E402


SPEC_ID_NAME = re.compile(
    r"[a-z][a-z0-9]*[-_]\d{3}[a-z]?",
    re.IGNORECASE,
)
CANONICAL_SPEC_ID_NAME = re.compile(
    r"\b(?P<family>[a-z][a-z0-9]*)-\d{3}[a-z]?\b",
    re.IGNORECASE,
)
SPEC_ID_PREFIX_NAME = re.compile(
    r"^\*\*Spec ID prefix:\*\*\s*`?(?P<family>[a-z][a-z0-9]*)-###",
    re.IGNORECASE | re.MULTILINE,
)
PURPOSE_NAMED_ROOTS = (
    FIXTURE_ROOT,
    TEST_ROOT / "parity",
    TEST_ROOT / "layer6-integration" / "dispatch-fixtures",
    TEST_ROOT / "layer7-parity",
)
SCRIPT_SUFFIXES = frozenset(
    {
        ".bash",
        ".bat",
        ".cjs",
        ".cmd",
        ".cts",
        ".fish",
        ".js",
        ".jsx",
        ".lua",
        ".mjs",
        ".mts",
        ".php",
        ".pl",
        ".ps1",
        ".psm1",
        ".py",
        ".pyw",
        ".r",
        ".rb",
        ".sh",
        ".tcl",
        ".ts",
        ".tsx",
        ".zsh",
    }
)
SCRIPT_DIRECTORY_NAMES = frozenset({"bin", "hooks", "scripts"})
GENERATED_SCRIPT_PREFIXES = ("dist/",)
NON_AUTHORED_DIRECTORY_NAMES = frozenset(
    {"node_modules", "third_party", "vendor", "vendored"}
)


def _is_repository_authored_script(path: str, mode: str) -> bool:
    relative = Path(path)
    normalized = relative.as_posix()
    if any(normalized.startswith(prefix) for prefix in GENERATED_SCRIPT_PREFIXES):
        return False
    if any(part in NON_AUTHORED_DIRECTORY_NAMES for part in relative.parts):
        return False
    return (
        mode == "100755"
        or relative.suffix.lower() in SCRIPT_SUFFIXES
        or any(part in SCRIPT_DIRECTORY_NAMES for part in relative.parts[:-1])
    )


def _repository_spec_families(repo_root: Path = REPO_ROOT) -> frozenset[str]:
    families: set[str] = set()
    roadmap_root = repo_root / "docs" / "ai" / "specs"
    for path in roadmap_root.rglob("*.md"):
        content = path.read_text(encoding="utf-8")
        families.update(
            match.group("family").casefold()
            for match in SPEC_ID_PREFIX_NAME.finditer(content)
        )
        families.update(
            match.group("family").casefold()
            for match in CANONICAL_SPEC_ID_NAME.finditer(path.as_posix())
        )
    for path in (repo_root / "specs").iterdir():
        if path.is_dir():
            families.update(
                match.group("family").casefold()
                for match in CANONICAL_SPEC_ID_NAME.finditer(path.as_posix())
            )
    return frozenset(families)


def _contains_repository_spec_id(value: str, families: frozenset[str]) -> bool:
    normalized = value.casefold()
    return any(
        re.search(rf"{re.escape(family)}[-_]\d{{3}}[a-z]?", normalized)
        for family in families
    )


SUITE_LOADER_ATTRIBUTES = frozenset({"loadTestsFromModule", "discover", "main"})


def unreferenced_test_cases(source: str) -> list[str]:
    """TestCase classes with tests that no suite builder in ``source`` mentions.

    A module that loads by module, discovery or ``unittest.main`` runs them all.
    Otherwise a class must appear by name (or as a string for loadTestsFromNames)
    outside its own definition, or its tests never run and the suite still passes.
    """
    tree = ast.parse(source)
    if any(isinstance(node, ast.Attribute) and node.attr in SUITE_LOADER_ATTRIBUTES for node in ast.walk(tree)):
        return []
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}

    def base_names(node: ast.ClassDef) -> list[str]:
        return [b.id if isinstance(b, ast.Name) else b.attr for b in node.bases if isinstance(b, (ast.Name, ast.Attribute))]

    def inherits_tests(node: ast.ClassDef, seen: frozenset[str] = frozenset()) -> tuple[bool, bool]:
        """(is a TestCase, has test methods) through same-file bases."""
        is_case = "TestCase" in base_names(node)
        has_tests = any(isinstance(m, ast.FunctionDef) and m.name.startswith("test") for m in node.body)
        for name in base_names(node):
            if name in classes and name not in seen:
                base_case, base_tests = inherits_tests(classes[name], seen | {node.name})
                is_case, has_tests = is_case or base_case, has_tests or base_tests
        return is_case, has_tests

    mentioned: set[str] = set()

    class Mentions(ast.NodeVisitor):
        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            for child in [*node.decorator_list, *node.body]:
                self.visit(child)

        def visit_Name(self, node: ast.Name) -> None:
            mentioned.add(node.id)

        def visit_Constant(self, node: ast.Constant) -> None:
            if isinstance(node.value, str):
                mentioned.add(node.value)

    Mentions().visit(tree)
    covered = set(mentioned)
    pending = [name for name in classes if name in mentioned]
    while pending:  # a listed subclass runs the tests it inherits
        for base in base_names(classes[pending.pop()]):
            if base in classes and base not in covered:
                covered.add(base)
                pending.append(base)
    return sorted(name for name, node in classes.items() if all(inherits_tests(node)) and name not in covered)


class UnitLayoutTests(unittest.TestCase):
    def test_unit_directory_replaces_the_opaque_layer_name(self) -> None:
        self.assertTrue(UNIT_ROOT.is_dir())
        self.assertFalse((UNIT_ROOT.parent / "layer4-scripts").exists())

    def test_support_paths_are_purpose_named(self) -> None:
        violations: list[str] = []
        for root in PURPOSE_NAMED_ROOTS:
            for path in root.rglob("*"):
                relative = path.relative_to(root)
                if "__pycache__" in relative.parts:
                    continue
                for part in relative.parts:
                    if part == "specs":
                        break
                    if SPEC_ID_NAME.search(part):
                        violations.append(f"{root.relative_to(TEST_ROOT)}/{relative}")
                        break
        self.assertEqual(violations, [])

    def test_support_fixture_ids_follow_purpose_directories(self) -> None:
        violations: list[str] = []
        for root in PURPOSE_NAMED_ROOTS:
            for path in root.rglob("*.json"):
                relative = path.relative_to(root)
                if "specs" in relative.parts:
                    continue
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    # Negative fixtures intentionally include malformed JSON.
                    continue
                if not isinstance(payload, dict):
                    continue
                fixture_id = payload.get("fixture_id")
                if not isinstance(fixture_id, str):
                    continue
                purpose = path.parent.name
                purpose_aligned = fixture_id == purpose or fixture_id.startswith(f"{purpose}-")
                if SPEC_ID_NAME.search(fixture_id) or not purpose_aligned:
                    violations.append(
                        f"{path.relative_to(TEST_ROOT)}: {fixture_id!r} does not match {purpose!r}"
                    )
        self.assertEqual(violations, [])

    def test_unit_test_method_names_are_behavior_named(self) -> None:
        violations: list[str] = []
        spec_families = _repository_spec_families()
        for path in sorted(UNIT_ROOT.glob("test-*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    if _contains_repository_spec_id(node.name, spec_families):
                        violations.append(f"{path.relative_to(TEST_ROOT)}::{node.name}")
        self.assertEqual(violations, [])

    def test_repository_spec_families_include_process_declarations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory)
            process_root = repo_root / "docs" / "ai" / "specs" / ".process"
            process_root.mkdir(parents=True)
            (repo_root / "specs").mkdir()
            (process_root / "ALPHA-002-workflow.md").write_text("", encoding="utf-8")
            (process_root / "BETA-014-workflow.md").write_text("", encoding="utf-8")

            families = _repository_spec_families(repo_root)

        self.assertTrue(_contains_repository_spec_id("test_alpha_002_guard", families))
        self.assertTrue(_contains_repository_spec_id("test_beta_014_guard", families))

    def test_repository_spec_id_detection_is_restricted_to_declared_families(
        self,
    ) -> None:
        families = frozenset({"alpha"})

        self.assertTrue(
            _contains_repository_spec_id("test-alpha-002-capability.py", families)
        )
        self.assertFalse(
            _contains_repository_spec_id("test-pr-366-capability.py", families)
        )

    def test_script_name_guard_covers_repository_authored_locations(self) -> None:
        self.assertEqual(GENERATED_SCRIPT_PREFIXES, ("dist/",))
        covered = (
            ("scripts/test-alpha-002-capability-telemetry.py", "100644"),
            ("docs-site/scripts/alpha-002-reference.mjs", "100644"),
            (".specify/extensions/git/scripts/bash/alpha-002-commit.sh", "100644"),
            (".claude/hooks/alpha-002-guard.py", "100644"),
            ("bin/alpha-002-check", "100755"),
        )
        excluded = (
            ("dist/codex/alpha-002-generated.py", "100644"),
            ("vendor/alpha-002-upstream.sh", "100644"),
        )
        for path, mode in covered:
            self.assertTrue(_is_repository_authored_script(path, mode), path)
        for path, mode in excluded:
            self.assertFalse(_is_repository_authored_script(path, mode), path)

    def test_spec_id_pattern_detects_compound_script_names(self) -> None:
        for name in (
            "alpha-002.test.py",
            "check.alpha-002.mjs",
            "checkalpha-002helper.ts",
        ):
            self.assertIsNotNone(SPEC_ID_NAME.search(Path(name).stem), name)

    def test_spec_id_pattern_detects_underscore_separators(self) -> None:
        for name in (
            "alpha_002.test.py",
            "beta_010.test.py",
            "check.alpha_002.mjs",
            "checkalpha_002helper.ts",
        ):
            self.assertIsNotNone(SPEC_ID_NAME.search(Path(name).stem), name)

    def test_tracked_authored_script_files_are_behavior_named(self) -> None:
        completed = subprocess.run(
            ["git", "ls-files", "--stage", "-z"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            shell=False,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        violations: list[str] = []
        spec_families = _repository_spec_families()
        for record in completed.stdout.split("\0"):
            if not record:
                continue
            metadata, relative = record.split("\t", 1)
            mode = metadata.split(" ", 1)[0]
            if not _is_repository_authored_script(relative, mode):
                continue
            if _contains_repository_spec_id(Path(relative).stem, spec_families):
                violations.append(relative)
        self.assertEqual(violations, [], completed.stdout + completed.stderr)

    def test_manifest_uses_the_unit_namespace(self) -> None:
        manifest = json.loads(
            (TEST_ROOT / "suite-manifest.json").read_text(encoding="utf-8")
        )
        layer = next(item for item in manifest["layers"] if item["id"] == "4")
        self.assertEqual(layer["label"], "Unit Tests")
        for script in layer["scripts"]:
            path = script["path"]
            self.assertTrue(
                path.startswith("tests/speckit-pro/unit/")
                or path in {"tests/speckit-pro/test-run-all.py", "tests/speckit-pro/lib/test_lib.py"},
                path,
            )


class UnitRosterTests(unittest.TestCase):
    def test_every_unit_test_script_is_registered_in_the_unit_layer(self) -> None:
        manifest = json.loads(
            (TEST_ROOT / "suite-manifest.json").read_text(encoding="utf-8")
        )
        layer = next(item for item in manifest["layers"] if item["id"] == "4")
        registered = {script["path"] for script in layer["scripts"]}
        discovered = {
            path.relative_to(REPO_ROOT).as_posix()
            for path in UNIT_ROOT.glob("test-*.py")
        }
        self.assertEqual(sorted(discovered - registered), [])

    def test_every_registered_test_case_is_added_to_its_suite(self) -> None:
        manifest = json.loads((TEST_ROOT / "suite-manifest.json").read_text(encoding="utf-8"))
        scripts = [
            script["path"]
            for layer in manifest["layers"]
            for script in layer.get("scripts", [])
            if script["path"].endswith(".py")
        ]
        self.assertTrue(scripts)
        unrun = {
            path: names
            for path in scripts
            if (names := unreferenced_test_cases((REPO_ROOT / path).read_text(encoding="utf-8")))
        }
        self.assertEqual(unrun, {})

    def test_unreferenced_test_case_detection_finds_a_class_missing_from_a_hand_list(self) -> None:
        listed = (
            "import unittest\n"
            "class A(unittest.TestCase):\n    def test_a(self): pass\n"
            "class B(unittest.TestCase):\n    def test_b(self): pass\n"
            "suite = unittest.defaultTestLoader.loadTestsFromTestCase(A)\n"
        )
        self.assertEqual(["B"], unreferenced_test_cases(listed))
        self.assertEqual([], unreferenced_test_cases(listed + "loader.loadTestsFromTestCase(B)\n"))
        self.assertEqual([], unreferenced_test_cases(listed + "unittest.defaultTestLoader.loadTestsFromModule(m)\n"))
        self.assertEqual([], unreferenced_test_cases(listed + "names = ['B']\n"))
        inherited = "import unittest\nclass Base(unittest.TestCase):\n    def test_x(self): pass\nclass Child(Base): pass\nsuite = [Child]\n"
        self.assertEqual([], unreferenced_test_cases(inherited))
        self.assertEqual(["Base", "Child"], unreferenced_test_cases(inherited.replace("suite = [Child]", "")))


if __name__ == "__main__":
    suite = unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromTestCase(case)
        for case in (UnitLayoutTests, UnitRosterTests)
    )
    raise SystemExit(run_counted(suite, label="test-unit-layout"))
