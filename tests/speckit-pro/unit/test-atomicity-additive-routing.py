#!/usr/bin/env python3
"""Regression coverage for conservative additive multi-seam atomicity routing."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
sys.path.insert(0, str(REPO_ROOT / "speckit-pro"))
sys.path.insert(0, str(TEST_ROOT / "lib"))

from native_eval_catalog import load_catalog  # noqa: E402
from native_eval_fixture_setup import materialize_workspace  # noqa: E402
from speckit_pro_runner.helpers.read_only import atomicity_route  # noqa: E402
from test_result import run_counted  # noqa: E402


FEATURE = "specs/atomicity-additive"


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout.strip()


def write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def task_plan(*, dependency: bool = False, shared: bool = False, one_seam: bool = False) -> str:
    alpha_source = "src/shared.py" if shared else "src/alpha.py"
    beta_source = "src/shared.py" if shared else "src/beta.py"
    beta = "" if one_seam else f"""
## Phase 2: User Story 2 - Beta (Priority: P1)

- [ ] T003 [P] [US2] Add Beta in `{beta_source}`.
- [ ] T004 [US2] Test Beta in `tests/test_beta.py`.
"""
    dependency_row = (
        "- **US2**: Depends on US1.\n"
        if dependency and not one_seam
        else ("" if one_seam else "- **US2**: Depends on No prerequisites.\n")
    )
    delivery = "" if one_seam else "2. Complete US2: T003-T004.\n"
    return f"""# Tasks

## Phase 1: User Story 1 - Alpha (Priority: P1)

- [ ] T001 [P] [US1] Add Alpha in `{alpha_source}`.
- [ ] T002 [US1] Test Alpha in `tests/test_alpha.py`.
{beta}
## Dependencies & Execution Order

### Phase Dependencies

- **US1**: Depends on No prerequisites.
{dependency_row}
### Incremental Delivery

1. Complete US1: T001-T002.
{delivery}
"""


class AtomicityAdditiveRoutingTests(unittest.TestCase):
    def repository(
        self,
        tasks: str,
        *,
        feature_files: dict[str, str] | None = None,
        baseline_files: dict[str, str] | None = None,
    ):
        temporary = tempfile.TemporaryDirectory(prefix="atomicity-additive-")
        root = Path(temporary.name).resolve()
        git(root, "init", "--quiet", "--initial-branch=main")
        git(root, "config", "user.name", "Atomicity Test")
        git(root, "config", "user.email", "native-eval@example.invalid")
        git(root, "config", "commit.gpgsign", "false")
        write(root, "README.md", "# Atomicity fixture\n")
        for relative, text in (baseline_files or {}).items():
            write(root, relative, text)
        git(root, "add", "--all")
        git(root, "commit", "--quiet", "-m", "baseline")
        git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
        git(root, "switch", "--quiet", "-c", "feature")
        write(root, f"{FEATURE}/spec.md", "# Independent additive capabilities\n")
        write(root, f"{FEATURE}/plan.md", "# Plan\n")
        write(root, f"{FEATURE}/tasks.md", tasks)
        for relative, text in (feature_files or {}).items():
            write(root, relative, text)
        git(root, "add", "--all")
        git(root, "commit", "--quiet", "-m", "feature")
        return temporary, root

    def route(self, root: Path, feature: str = FEATURE) -> dict:
        result = atomicity_route({"feature_dir": feature}, root)
        self.assertEqual(result["exit_code"], 0, result)
        return json.loads(result["stdout"])

    def independent_files(self, *, shared: bool = False) -> dict[str, str]:
        alpha = "src/shared.py" if shared else "src/alpha.py"
        beta = "src/shared.py" if shared else "src/beta.py"
        return {
            alpha: "ALPHA = True\n",
            beta: "BETA = True\n" if beta != alpha else "ALPHA = True\nBETA = True\n",
            "tests/test_alpha.py": "def test_alpha():\n    assert True\n",
            "tests/test_beta.py": "def test_beta():\n    assert True\n",
        }

    def test_independent_additive_multi_seam_routes_split(self) -> None:
        temporary, root = self.repository(
            task_plan(), feature_files=self.independent_files(),
        )
        with temporary:
            result = self.route(root)
        self.assertEqual(result["route"], "split-PR")
        self.assertTrue(result["releasable"])
        self.assertEqual(result["signals"], [
            "change-shape:additive-only",
            "topology:independent-multi-seam",
            "source-proof:direct-python-imports-only",
        ])

    def test_one_seam_abstains(self) -> None:
        temporary, root = self.repository(
            task_plan(one_seam=True),
            feature_files={
                "src/alpha.py": "ALPHA = True\n",
                "tests/test_alpha.py": "def test_alpha():\n    assert True\n",
            },
        )
        with temporary:
            self.assertEqual(self.route(root)["route"], "one-navigable-PR")

    def test_dependency_and_shared_file_each_abstain(self) -> None:
        cases = (
            ("dependency", task_plan(dependency=True), self.independent_files()),
            ("shared", task_plan(shared=True), self.independent_files(shared=True)),
        )
        for label, tasks, files in cases:
            with self.subTest(case=label):
                temporary, root = self.repository(tasks, feature_files=files)
                with temporary:
                    self.assertEqual(self.route(root)["route"], "one-navigable-PR")

    def test_cross_seam_python_import_abstains_despite_false_task_independence(self) -> None:
        files = self.independent_files()
        files["src/alpha.py"] = "from src.beta import BETA\n\nALPHA = BETA\n"
        temporary, root = self.repository(task_plan(), feature_files=files)
        with temporary:
            self.assertEqual(self.route(root)["route"], "one-navigable-PR")

    def test_unsupported_or_dynamic_dependency_evidence_abstains(self) -> None:
        unsupported_tasks = task_plan().replace(".py", ".ts")
        unsupported_files = {
            path.replace(".py", ".ts"): text
            for path, text in self.independent_files().items()
        }
        dynamic_files = self.independent_files()
        dynamic_files["src/alpha.py"] = (
            "import importlib\n\n"
            "beta = importlib.import_module('src.beta')\n"
            "ALPHA = beta.BETA\n"
        )
        aliased_dynamic_files = self.independent_files()
        aliased_dynamic_files["src/alpha.py"] = (
            "from importlib import import_module as load\n\n"
            "beta = load('src.beta')\n"
            "ALPHA = beta.BETA\n"
        )
        invalid_relative_files = self.independent_files()
        invalid_relative_files["src/alpha.py"] = (
            "from .. import unrelated\n\n"
            "ALPHA = True\n"
        )
        builtin_dynamic_files = self.independent_files()
        builtin_dynamic_files["src/alpha.py"] = (
            "import builtins as runtime\n\n"
            "beta = runtime.__import__('src.beta', fromlist=['BETA'])\n"
            "ALPHA = beta.BETA\n"
        )
        cases = (
            ("unsupported-language", unsupported_tasks, unsupported_files),
            ("dynamic-import", task_plan(), dynamic_files),
            ("aliased-dynamic-import", task_plan(), aliased_dynamic_files),
            ("builtin-attribute-dynamic-import", task_plan(), builtin_dynamic_files),
            ("relative-import-beyond-package", task_plan(), invalid_relative_files),
        )
        for label, tasks, files in cases:
            with self.subTest(case=label):
                temporary, root = self.repository(tasks, feature_files=files)
                with temporary:
                    self.assertEqual(self.route(root)["route"], "one-navigable-PR")

    def test_guarded_and_release_held_cutovers_never_split(self) -> None:
        cases = (
            ("guarded", "Guarded cutover requires a coordinated deployment.", "one-navigable-PR"),
            ("release-held", "Release-held cutover requires a coordinated deployment.", "single-atomic-PR"),
        )
        for label, hazard, expected_route in cases:
            with self.subTest(case=label):
                tasks = task_plan() + f"\n## Delivery constraint\n\n{hazard}\n"
                temporary, root = self.repository(tasks, feature_files=self.independent_files())
                with temporary:
                    result = self.route(root)
                self.assertEqual(result["route"], expected_route)
                self.assertIn("hint:release-cadence:weak", result["hints"])

    def test_real_modified_file_abstains_and_reports_modify_heavy(self) -> None:
        files = self.independent_files()
        temporary, root = self.repository(
            task_plan(),
            baseline_files={"src/alpha.py": "ALPHA = False\n"},
            feature_files=files,
        )
        with temporary:
            result = self.route(root)
        self.assertEqual(result["route"], "one-navigable-PR")
        self.assertIn("change-shape:modify-heavy", result["signals"])

    def test_destructive_migration_keeps_hard_atomic_priority(self) -> None:
        tasks = task_plan() + "\n- [ ] T099 DROP `migrations/schema.sql` before release.\n"
        files = {**self.independent_files(), "migrations/schema.sql": "DROP TABLE old_data;\n"}
        temporary, root = self.repository(tasks, feature_files=files)
        with temporary:
            result = self.route(root)
        self.assertEqual(result["route"], "single-atomic-PR")
        self.assertFalse(result["releasable"])
        self.assertEqual(result["signals"][0], "hard-atomic:destructive-migration")

    def test_missing_empty_and_malformed_topology_never_split(self) -> None:
        temporary, root = self.repository(task_plan(), feature_files=self.independent_files())
        with temporary:
            missing = atomicity_route({"feature_dir": "specs/missing"}, root)
            self.assertEqual(missing["exit_code"], 2)
            write(root, f"{FEATURE}/tasks.md", "")
            self.assertEqual(self.route(root)["route"], "out-of-scope")

        malformed = """# Tasks
## Phase 1: User Story 1 - Alpha
- [ ] T001 [US1] Add `src/alpha.py`.
## Phase 2: User Story 2 - Beta
- [ ] T001 [US2] Add `src/beta.py`.
"""
        temporary, root = self.repository(
            malformed, feature_files=self.independent_files(),
        )
        with temporary:
            self.assertEqual(self.route(root)["route"], "one-navigable-PR")

        ambiguous = task_plan().replace(
            "- **US2**: Depends on No prerequisites.\n", "",
        )
        temporary, root = self.repository(
            ambiguous, feature_files=self.independent_files(),
        )
        with temporary:
            self.assertEqual(self.route(root)["route"], "one-navigable-PR")

        ambiguous = task_plan().replace(
            "Depends on No prerequisites.", "Depends on an unspecified seam.", 1,
        )
        temporary, root = self.repository(
            ambiguous, feature_files=self.independent_files(),
        )
        with temporary:
            self.assertEqual(self.route(root)["route"], "one-navigable-PR")

    def test_current_parity01_fixture_has_real_additive_split_evidence(self) -> None:
        catalog = load_catalog(TEST_ROOT / "evals" / "catalog.json", REPO_ROOT)
        case = next(row for row in catalog["cases"] if row["id"] == "parity.01-post-implementation-outcome")

        def record(row: dict[str, str]) -> dict[str, str]:
            payload = (REPO_ROOT / row["source"]).read_bytes()
            return {**row, "sha256": hashlib.sha256(payload).hexdigest()}

        plan = {
            "schema_version": "native-eval-fixtures/v2",
            "source_root": str(REPO_ROOT),
            "fixtures": [record(row) for row in case["fixtures"]],
            "git_repository": {
                "recipe": case["git_fixture"]["recipe"],
                "baseline": [record(row) for row in case["git_fixture"]["baseline"]],
            },
        }
        with tempfile.TemporaryDirectory(prefix="atomicity-parity01-") as raw_tmp:
            workspace = Path(raw_tmp).resolve()
            materialize_workspace(plan, workspace)
            result = self.route(workspace, "specs/parity-01")
        self.assertEqual(result["route"], "split-PR")
        self.assertEqual(result["signals"], [
            "change-shape:additive-only",
            "topology:independent-multi-seam",
            "source-proof:direct-python-imports-only",
        ])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(AtomicityAdditiveRoutingTests)
    raise SystemExit(run_counted(suite, label="test-atomicity-additive-routing"))
