#!/usr/bin/env python3
"""Focused runner contract tests for spec-index check and write behavior."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES = REPO_ROOT / "tests" / "speckit-pro" / "layer1-structural" / "fixtures" / "spec-index"
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"

LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from speckit_pro_runner.helpers.mutation import _spec_index_target_chain_is_safe  # noqa: E402
from test_result import run_counted  # noqa: E402


def runner_request(
    helper_id: str,
    operation: str,
    mode: str,
    inputs: dict[str, object],
) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    payload = {
        "schema_version": "1.0",
        "request_id": f"test-{helper_id}-{mode}",
        "helper_id": helper_id,
        "operation": operation,
        "mode": mode,
        "inputs": inputs,
    }
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(PLUGIN_ROOT) if not existing else f"{PLUGIN_ROOT}{os.pathsep}{existing}"
    completed = subprocess.run(
        [sys.executable, "-m", "speckit_pro_runner"],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=REPO_ROOT,
        env=env,
        shell=False,
        check=False,
    )
    body = json.loads(completed.stdout)
    return completed, body


def check_request(root: Path) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    return runner_request(
        "generate-spec-index-check",
        "generate-spec-index-check",
        "read_only",
        {"repo_root": root.relative_to(REPO_ROOT).as_posix()},
    )


def write_request(
    root: Path,
    mode: str = "apply",
) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    return runner_request(
        "generate-spec-index-write",
        "generate-spec-index-write",
        mode,
        {"repo_root": root.relative_to(REPO_ROOT).as_posix()},
    )


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix())
        if path.is_file()
    }


class GenerateSpecIndexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix=".spec-index-test-", dir=REPO_ROOT)
        self.work = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def copy_fixture(self, name: str) -> Path:
        target = self.work / name
        shutil.copytree(FIXTURES / name, target)
        return target

    def test_check_returns_current_stale_and_error_without_writes(self) -> None:
        cases = (
            ("current-empty", 0, "ok"),
            ("stale-fill", 1, "expected_failure"),
            ("prs-malformed", 2, "input_error"),
        )
        for fixture, expected_exit, expected_status in cases:
            with self.subTest(fixture=fixture):
                root = FIXTURES / fixture
                before = snapshot(root)
                completed, body = check_request(root)
                self.assertEqual(completed.returncode, expected_exit, completed.stderr)
                self.assertEqual(body["exit_code"], expected_exit)
                self.assertEqual(body["status"], expected_status)
                self.assertEqual(snapshot(root), before)

        stale_completed, stale_body = check_request(FIXTURES / "stale-fill")
        self.assertIn("STALE", stale_body["data"]["stdout"]["text"])
        self.assertIn("prsg-901-stale", stale_body["data"]["stdout"]["text"])
        self.assertEqual(stale_completed.stderr.count("\n"), 1)

        error_completed, error_body = check_request(FIXTURES / "prs-malformed")
        self.assertIn("prs.json", error_body["data"]["stderr"]["text"])
        self.assertEqual(error_completed.stderr.count("\n"), 1)

    def test_write_plans_applies_and_is_idempotent_without_touching_curated_content(self) -> None:
        root = self.copy_fixture("stale-fill")
        moc = root / "specs" / "prsg-901-stale" / "SPEC-MOC.md"
        curated_tail = "\n## Curated tail\n\nThis content must survive regeneration.\n"
        moc.write_text(moc.read_text(encoding="utf-8").rstrip("\n") + curated_tail, encoding="utf-8")
        before = moc.read_text(encoding="utf-8")
        curated_prefix = before.split("<!-- GENERATED:INDEX:START", 1)[0]

        dry_run, dry_body = write_request(root, "dry_run")
        self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
        self.assertFalse(dry_body["data"]["writes_state"])
        self.assertEqual(moc.read_text(encoding="utf-8"), before)
        self.assertIn("specs/prsg-901-stale/SPEC-MOC.md", dry_body["data"]["mutation"]["planned_paths"])

        applied, applied_body = write_request(root)
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertTrue(applied_body["data"]["writes_state"])
        self.assertEqual(applied_body["data"]["mutation"]["mutation_status"], "applied")
        self.assertEqual(
            applied_body["data"]["mutation"]["touched_paths"],
            ["specs/prsg-901-stale/SPEC-MOC.md"],
        )

        after = moc.read_text(encoding="utf-8")
        self.assertTrue(after.startswith(curated_prefix))
        self.assertTrue(after.endswith(curated_tail))
        self.assertIn("PRSG-901 \u00b7 PR#117 \u00b7 abc1234", after)
        self.assertIn("- [spec.md](spec.md)", after)
        self.assertIn(
            "<!-- GENERATED:INDEX:START (do not edit; regenerated by generate-spec-index.sh) -->",
            after,
        )

        current, _ = check_request(root)
        self.assertEqual(current.returncode, 0, current.stderr)
        first_write = moc.read_bytes()
        second, second_body = write_request(root)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(second_body["data"]["mutation"]["mutation_status"], "no_op")
        self.assertFalse(second_body["data"]["writes_state"])
        self.assertEqual(moc.read_bytes(), first_write)

    def test_write_rejects_target_swap_between_conflict_check_and_replace(self) -> None:
        from speckit_pro_runner.envelope import RunnerRequest
        from speckit_pro_runner.helpers import mutation, registry

        root = self.copy_fixture("stale-fill")
        moc = root / "specs" / "prsg-901-stale" / "SPEC-MOC.md"
        calls = 0
        real_ensure = mutation.ensure_safe_write_target_fd

        def swap_before_final_guard(parent_fd: int, name: str) -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                moc.write_text("concurrent\n", encoding="utf-8")
            real_ensure(parent_fd, name)

        request = RunnerRequest(
            "test-spec-index-target-swap",
            "generate-spec-index-write",
            "generate-spec-index-write",
            "apply",
            {"repo_root": root.relative_to(REPO_ROOT).as_posix()},
        )
        old_cwd = Path.cwd()
        os.chdir(REPO_ROOT)
        try:
            with patch.object(mutation, "ensure_safe_write_target_fd", side_effect=swap_before_final_guard):
                body = mutation.run_spec_index_write(registry.MUTATION_HELPERS["generate-spec-index-write"], request)
        finally:
            os.chdir(old_cwd)

        self.assertEqual(body["status"], "expected_failure")
        self.assertEqual(body["exit_code"], 1)
        self.assertEqual([diag["code"] for diag in body["diagnostics"]], ["source_changed"])
        self.assertEqual(moc.read_text(encoding="utf-8"), "concurrent\n")
        self.assertFalse(body["data"]["mutation"]["live_mutation"])

    def test_write_acquires_lock_before_rendering_sources(self) -> None:
        from speckit_pro_runner.envelope import RunnerRequest
        from speckit_pro_runner.helpers import mutation, registry

        root = self.copy_fixture("stale-fill")
        lock_acquired = False
        real_acquire = mutation.acquire_mutation_lock
        real_render = mutation.render_spec_index

        def tracking_acquire(repo_root: Path) -> mutation.MutationApplyLock:
            nonlocal lock_acquired
            lock = real_acquire(repo_root)
            lock_acquired = True
            return lock

        def assert_locked_render(target_root: Path):
            self.assertTrue(lock_acquired)
            return real_render(target_root)

        request = RunnerRequest(
            "test-spec-index-lock-before-render",
            "generate-spec-index-write",
            "generate-spec-index-write",
            "apply",
            {"repo_root": root.relative_to(REPO_ROOT).as_posix()},
        )
        old_cwd = Path.cwd()
        os.chdir(REPO_ROOT)
        try:
            with (
                patch.object(mutation, "acquire_mutation_lock", side_effect=tracking_acquire),
                patch.object(mutation, "render_spec_index", side_effect=assert_locked_render),
            ):
                body = mutation.run_spec_index_write(registry.MUTATION_HELPERS["generate-spec-index-write"], request)
        finally:
            os.chdir(old_cwd)

        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["data"]["mutation"]["mutation_status"], "applied")

    def test_write_rejects_render_dependency_change_between_render_and_commit(self) -> None:
        from speckit_pro_runner.envelope import RunnerRequest
        from speckit_pro_runner.helpers import mutation, registry

        root = self.copy_fixture("stale-fill")
        moc = root / "specs" / "prsg-901-stale" / "SPEC-MOC.md"
        before = moc.read_text(encoding="utf-8")
        prs = root / "specs" / "prsg-901-stale" / ".process" / "prs.json"
        real_render = mutation.render_spec_index
        calls = 0

        def mutate_prs_after_initial_render(target_root: Path):
            nonlocal calls
            rendered = real_render(target_root)
            calls += 1
            if calls == 1:
                payload = json.loads(prs.read_text(encoding="utf-8"))
                payload["records"][0]["pr"] = 999
                prs.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            return rendered

        request = RunnerRequest(
            "test-spec-index-render-source-changed",
            "generate-spec-index-write",
            "generate-spec-index-write",
            "apply",
            {"repo_root": root.relative_to(REPO_ROOT).as_posix()},
        )
        old_cwd = Path.cwd()
        os.chdir(REPO_ROOT)
        try:
            with patch.object(mutation, "render_spec_index", side_effect=mutate_prs_after_initial_render):
                body = mutation.run_spec_index_write(registry.MUTATION_HELPERS["generate-spec-index-write"], request)
        finally:
            os.chdir(old_cwd)

        self.assertEqual(body["status"], "expected_failure")
        self.assertEqual([diag["code"] for diag in body["diagnostics"]], ["source_changed"])
        self.assertEqual(moc.read_text(encoding="utf-8"), before)
        self.assertFalse(body["data"]["writes_state"])

    def test_write_rolls_back_render_dependency_change_immediately_before_replace(self) -> None:
        from speckit_pro_runner.envelope import RunnerRequest
        from speckit_pro_runner.helpers import mutation, registry

        root = self.copy_fixture("stale-fill")
        moc = root / "specs" / "prsg-901-stale" / "SPEC-MOC.md"
        before = moc.read_text(encoding="utf-8")
        prs = root / "specs" / "prsg-901-stale" / ".process" / "prs.json"
        real_write = mutation.write_file_atomic
        calls = 0

        def mutate_prs_before_replace(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                payload = json.loads(prs.read_text(encoding="utf-8"))
                payload["records"][0]["pr"] = 1000
                prs.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            return real_write(*args, **kwargs)

        request = RunnerRequest(
            "test-spec-index-render-source-changed-before-replace",
            "generate-spec-index-write",
            "generate-spec-index-write",
            "apply",
            {"repo_root": root.relative_to(REPO_ROOT).as_posix()},
        )
        old_cwd = Path.cwd()
        os.chdir(REPO_ROOT)
        try:
            with patch.object(mutation, "write_file_atomic", side_effect=mutate_prs_before_replace):
                body = mutation.run_spec_index_write(registry.MUTATION_HELPERS["generate-spec-index-write"], request)
        finally:
            os.chdir(old_cwd)

        self.assertEqual(body["status"], "expected_failure")
        self.assertEqual([diag["code"] for diag in body["diagnostics"]], ["source_changed"])
        self.assertEqual(body["data"]["mutation"]["mutation_status"], "partial_failure")
        self.assertEqual(body["data"]["mutation"]["touched_paths"], ["specs/prsg-901-stale/SPEC-MOC.md"])
        self.assertEqual(moc.read_text(encoding="utf-8"), before)
        self.assertFalse(body["data"]["writes_state"])

    def test_current_marker_spelling_is_rendered_and_preserved(self) -> None:
        root = self.copy_fixture("stale-fill")
        moc = root / "specs" / "prsg-901-stale" / "SPEC-MOC.md"
        before = moc.read_text(encoding="utf-8").replace("generate-spec-index.sh", "generate-spec-index")
        moc.write_text(before, encoding="utf-8")

        completed, _ = write_request(root)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        after = moc.read_text(encoding="utf-8")
        self.assertIn("regenerated by generate-spec-index) -->", after)
        self.assertNotIn("regenerated by generate-spec-index.sh) -->", after)
        self.assertIn("- [plan.md](plan.md)", after)

    def test_write_populates_home_indexes_without_rewriting_current_spec_maps(self) -> None:
        root = self.copy_fixture("roadmap-moc")
        home = root / "docs" / "ai" / "specs" / "myproject-roadmap-MOC.md"
        other_home = root / "docs" / "ai" / "specs" / "otherproject-roadmap-MOC.md"
        spec_maps = sorted((root / "specs").glob("*/SPEC-MOC.md"))
        spec_before = {path.relative_to(root).as_posix(): path.read_bytes() for path in spec_maps}

        completed, body = write_request(root)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            body["data"]["mutation"]["touched_paths"],
            [
                "docs/ai/specs/myproject-roadmap-MOC.md",
                "docs/ai/specs/otherproject-roadmap-MOC.md",
            ],
        )

        home_text = home.read_text(encoding="utf-8")
        expected_rows = [
            "- [PRSG-001](../../../specs/prsg-001-foo/SPEC-MOC.md) \u00b7 complete",
            "- [PRSG-002](../../../specs/prsg-002-bar/SPEC-MOC.md) \u00b7",
            "- [PRSG-010](../../../specs/prsg-010-baz/SPEC-MOC.md) \u00b7 in-progress",
            "- [PRSG-011-FLAT-OWNED](../../../specs/prsg-011-flat-owned/spec.md) \u00b7",
        ]
        for row in expected_rows:
            self.assertIn(row, home_text)
        self.assertEqual([home_text.index(row) for row in expected_rows], sorted(home_text.index(row) for row in expected_rows))
        self.assertNotIn("prsg-004-other", home_text)
        self.assertIn("prsg-004-other", other_home.read_text(encoding="utf-8"))
        self.assertEqual(
            {path.relative_to(root).as_posix(): path.read_bytes() for path in spec_maps},
            spec_before,
        )

        current, _ = check_request(root)
        self.assertEqual(current.returncode, 0, current.stderr)

    def test_marker_injection_is_all_or_none(self) -> None:
        inject_root = self.copy_fixture("inject-missing-all")
        injected_moc = inject_root / "specs" / "prsg-902-inject" / "SPEC-MOC.md"
        curated = injected_moc.read_text(encoding="utf-8").rstrip()
        completed, _ = write_request(inject_root)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        injected = injected_moc.read_text(encoding="utf-8")
        self.assertTrue(injected.startswith(curated))
        for zone in ("INDEX", "PRS", "BACKLINKS"):
            self.assertEqual(injected.count(f"GENERATED:{zone}:START"), 1)
            self.assertEqual(injected.count(f"GENERATED:{zone}:END"), 1)
        self.assertIn("regenerated by generate-spec-index) -->", injected)
        self.assertNotIn("regenerated by generate-spec-index.sh) -->", injected)

        skip_root = self.copy_fixture("skip-one-missing")
        skipped_moc = skip_root / "specs" / "prsg-903-skipone" / "SPEC-MOC.md"
        completed, _ = write_request(skip_root)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        skipped = skipped_moc.read_text(encoding="utf-8")
        self.assertNotIn("GENERATED:PRS:START", skipped)
        self.assertIn("- [spec.md](spec.md)", skipped)

    def test_unbalanced_marker_aborts_the_batch_without_writes(self) -> None:
        root = self.copy_fixture("atomicity")
        before = snapshot(root)
        completed, body = write_request(root)
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertEqual(body["status"], "input_error")
        self.assertIn("unbalanced GENERATED:BACKLINKS marker pair", completed.stderr)
        self.assertEqual(snapshot(root), before)

        malformed_root = self.copy_fixture("current-empty")
        malformed_moc = malformed_root / "specs" / "prsg-900-current" / "SPEC-MOC.md"
        malformed_moc.write_text(
            malformed_moc.read_text(encoding="utf-8").replace(
                "<!-- GENERATED:INDEX:END -->",
                "<!-- GENERATED:INDEX:END  -->",
            ),
            encoding="utf-8",
        )
        malformed_before = malformed_moc.read_bytes()
        completed, _ = write_request(malformed_root)
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertIn("unbalanced GENERATED:INDEX marker pair", completed.stderr)
        self.assertEqual(malformed_moc.read_bytes(), malformed_before)

    def test_apply_path_guard_rejects_a_symlinked_parent_directory(self) -> None:
        trust_root = self.work / "trust-root"
        target = trust_root / "maps" / "SPEC-MOC.md"
        target.parent.mkdir(parents=True)
        target.write_text("safe\n", encoding="utf-8")
        self.assertTrue(_spec_index_target_chain_is_safe(target, trust_root))

        outside = self.work / "redirected-maps"
        outside.mkdir()
        (outside / target.name).write_text("outside\n", encoding="utf-8")
        shutil.rmtree(target.parent)
        try:
            target.parent.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"directory symlinks unavailable: {type(exc).__name__}")
        self.assertFalse(_spec_index_target_chain_is_safe(target, trust_root))

    def test_write_registry_is_promoted_with_an_authoritative_python_request(self) -> None:
        completed, body = runner_request(
            "mutation-registry-dispatch",
            "mutation-registry-dispatch",
            "read_only",
            {},
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        helpers = {record["helper_id"]: record for record in body["data"]["helpers"]}
        entry = helpers["generate-spec-index-write"]
        self.assertEqual(entry["promotion_status"], "golden_only")
        self.assertTrue(entry["authoritative_command"])


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(GenerateSpecIndexTests)
    return run_counted(suite, label="test-generate-spec-index")


if __name__ == "__main__":
    raise SystemExit(main())
