#!/usr/bin/env python3
"""Focused public-contract tests for the durable OKF knowledge layer."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
FIXED_TIME = "2026-07-14T12:00:00Z"

if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from test_result import run_counted  # noqa: E402
from speckit_pro_runner.helpers import knowledge as knowledge_helper  # noqa: E402
from speckit_pro_runner.helpers import mutation as mutation_helper  # noqa: E402
from speckit_pro_runner.helpers.registry import MUTATION_HELPERS  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file()
    }


def run_helper(
    root: Path,
    helper_id: str,
    mode: str,
    inputs: dict[str, object] | None = None,
) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    request_inputs = dict(inputs or {})
    request_inputs["repo_root"] = root.relative_to(REPO_ROOT).as_posix()
    payload = {
        "schema_version": "1.0",
        "request_id": f"test-{helper_id}-{mode}",
        "helper_id": helper_id,
        "operation": helper_id,
        "mode": mode,
        "inputs": request_inputs,
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
    try:
        body = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:  # pragma: no cover - assertion aid
        raise AssertionError(
            f"runner emitted invalid JSON\nstdout={completed.stdout!r}\nstderr={completed.stderr!r}"
        ) from exc
    return completed, body


class KnowledgeLayerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(prefix=".knowledge-layer-test-", dir=REPO_ROOT)
        self.work = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def repo(self, name: str) -> Path:
        root = self.work / name
        root.mkdir(parents=True)
        return root

    def write(self, root: Path, relative: str, text: str) -> Path:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def plan(self, root: Path, action: str, **inputs: object) -> dict[str, object]:
        completed, body = run_helper(
            root,
            "knowledge-update-plan",
            "read_only",
            {"action": action, "timestamp": FIXED_TIME, **inputs},
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(body["status"], "ok", body)
        return body["data"]["plan"]

    def apply(
        self,
        root: Path,
        plan: dict[str, object],
        *,
        mode: str = "apply",
        **inputs: object,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        return run_helper(
            root,
            "knowledge-update-apply",
            mode,
            {
                "plan": plan,
                "plan_hash": plan["plan_hash"],
                "expected_snapshot": plan["expected_snapshot"],
                **inputs,
            },
        )

    def apply_direct(self, root: Path, plan: dict[str, object]) -> dict[str, object]:
        entry = MUTATION_HELPERS["knowledge-update-apply"]
        request = SimpleNamespace(
            request_id="test-knowledge-update-apply-direct",
            mode="apply",
            inputs={
                "repo_root": root.relative_to(REPO_ROOT).as_posix(),
                "plan": plan,
                "plan_hash": plan["plan_hash"],
                "expected_snapshot": plan["expected_snapshot"],
            },
        )
        return knowledge_helper.run_knowledge_update_apply(entry, request)

    def init(self, root: Path) -> dict[str, object]:
        plan = self.plan(root, "init")
        completed, body = self.apply(root, plan)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(body["data"]["mutation"]["mutation_status"], "applied")
        return plan

    def candidate(
        self,
        concept_path: str,
        title: str,
        sources: list[Path],
        *,
        body: str = "A reusable, source-backed project decision.",
        project: str | None = None,
    ) -> dict[str, object]:
        value: dict[str, object] = {
            "concept_path": concept_path,
            "type": "decision",
            "title": title,
            "description": f"Reviewed guidance for {title}.",
            "body": body,
            "state": "reviewed",
            "reviewed": True,
            "confidence": "high",
            "sensitivity": "internal",
            "tags": ["tested", "durable"],
            "producer": {"skill": "test-knowledge-layer", "agent": "fixture"},
            "sources": [
                {
                    "path": source.relative_to(self.current_root).as_posix(),
                    "section": "complete test fixture",
                    "line_start": 1,
                    "line_end": 1,
                    "sha256": sha256(source),
                }
                for source in sources
            ],
        }
        if project is not None:
            value["project"] = project
        return value

    def test_init_apply_health_and_idempotent_replan(self) -> None:
        root = self.repo("init")
        initial_plan = self.plan(root, "init")
        self.assertGreater(initial_plan["operation_count"], 0)
        self.assertRegex(initial_plan["plan_hash"], r"^sha256:[a-f0-9]{64}$")

        completed, applied = self.apply(root, initial_plan)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(applied["data"]["writes_state"])
        self.assertEqual(applied["data"]["mutation"]["mutation_status"], "applied")

        _, health_body = run_helper(root, "knowledge-health", "read_only")
        health = health_body["data"]["health"]
        self.assertTrue(health["initialized"])
        self.assertTrue(health["okf_conformant"])
        self.assertTrue(health["profile_healthy"], health["findings"])

        no_op_plan = self.plan(root, "init")
        self.assertEqual(no_op_plan["operation_count"], 0)
        completed, no_op = self.apply(root, no_op_plan)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertFalse(no_op["data"]["writes_state"])
        self.assertEqual(no_op["data"]["mutation"]["mutation_status"], "no_op")

    def test_base_okf_conformance_is_distinct_from_the_trusted_profile(self) -> None:
        root = self.repo("base-vs-profile")
        self.write(
            root,
            "docs/ai/knowledge/patterns/minimal.md",
            "---\ntype: note\ntags: [sales, orders, revenue]\n"
            "x-example-extension:\n  owner: analytics\n  nested:\n    retained: true\n"
            "---\n# Minimal OKF concept\n",
        )

        completed, body = run_helper(root, "knowledge-health", "read_only")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        health = body["data"]["health"]
        self.assertTrue(health["okf_conformant"], health["findings"])
        self.assertFalse(health["profile_healthy"])
        self.assertGreater(health["finding_count"], 0)

        self.write(
            root,
            "docs/ai/knowledge/patterns/duplicate.md",
            "---\ntype: note\ntype: decision\n---\n# Ambiguous concept\n",
        )
        _, duplicate_body = run_helper(root, "knowledge-health", "read_only")
        duplicate_health = duplicate_body["data"]["health"]
        self.assertFalse(duplicate_health["okf_conformant"])
        self.assertIn(
            "invalid_frontmatter",
            {item["code"] for item in duplicate_health["findings"]},
        )

    def test_timestamps_require_timezones_and_reads_return_structured_errors(self) -> None:
        root = self.repo("timestamp-and-read-errors")
        completed, naive = run_helper(
            root,
            "knowledge-update-plan",
            "read_only",
            {"action": "init", "timestamp": "2026-07-14T12:00:00"},
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(naive["diagnostics"][0]["code"], "invalid_input")

        offset = self.plan(root, "init", timestamp="2026-07-14T07:00:00-05:00")
        self.assertEqual(offset["request"]["timestamp"], FIXED_TIME)

        concept = self.write(
            root,
            "docs/ai/knowledge/patterns/unreadable.md",
            "---\ntype: note\n---\n# Unreadable\n",
        )
        with mock.patch.object(knowledge_helper.os, "read", side_effect=PermissionError):
            with self.assertRaises(knowledge_helper.KnowledgeError) as captured:
                knowledge_helper._read_utf8(concept)
        self.assertEqual(captured.exception.code, "unreadable_file")

    @unittest.skipUnless(
        os.name == "posix" and hasattr(os, "O_DIRECTORY") and hasattr(os, "O_NOFOLLOW"),
        "descriptor-relative atomic-write regression requires POSIX dir_fd support",
    )
    def test_atomic_writer_cannot_follow_a_swapped_parent_symlink(self) -> None:
        root = self.repo("atomic-race")
        parent = root / "safe"
        parent.mkdir()
        target = parent / "target.md"
        target.write_text("before\n", encoding="utf-8")
        detached = root / "detached"
        external = self.repo("external")
        external_target = external / "target.md"
        external_target.write_text("external\n", encoding="utf-8")
        real_replace = os.replace
        swapped = False

        def swap_then_replace(
            source: str,
            destination: str,
            *,
            src_dir_fd: int | None = None,
            dst_dir_fd: int | None = None,
        ) -> None:
            nonlocal swapped
            if not swapped:
                parent.rename(detached)
                parent.symlink_to(external, target_is_directory=True)
                swapped = True
            real_replace(
                source,
                destination,
                src_dir_fd=src_dir_fd,
                dst_dir_fd=dst_dir_fd,
            )

        with mock.patch.object(mutation_helper.os, "replace", side_effect=swap_then_replace):
            mutation_helper.write_file_atomic(target, "after", trust_root=root)

        self.assertEqual(external_target.read_text(encoding="utf-8"), "external\n")
        self.assertEqual((detached / "target.md").read_text(encoding="utf-8"), "after\n")

    @unittest.skipUnless(
        os.name == "posix" and hasattr(os, "O_DIRECTORY") and hasattr(os, "O_NOFOLLOW"),
        "conditional atomic-write regression requires POSIX dir_fd support",
    )
    def test_atomic_writer_does_not_replace_a_concurrently_created_target(self) -> None:
        root = self.repo("atomic-no-replace")
        parent = root / "safe"
        parent.mkdir()
        target = parent / "target.md"
        real_link = os.link

        def create_then_link(
            source: str,
            destination: str,
            *,
            src_dir_fd: int | None = None,
            dst_dir_fd: int | None = None,
            follow_symlinks: bool = True,
        ) -> None:
            target.write_text("concurrent\n", encoding="utf-8")
            real_link(
                source,
                destination,
                src_dir_fd=src_dir_fd,
                dst_dir_fd=dst_dir_fd,
                follow_symlinks=follow_symlinks,
            )

        with (
            mock.patch.object(mutation_helper.os, "link", side_effect=create_then_link),
            self.assertRaises(mutation_helper.AtomicWriteConflictError),
        ):
            mutation_helper.write_file_atomic(
                target,
                "planned",
                trust_root=root,
                expected_prior=None,
            )
        self.assertEqual(target.read_text(encoding="utf-8"), "concurrent\n")

    @unittest.skipUnless(
        os.name == "posix" and hasattr(os, "O_DIRECTORY") and hasattr(os, "O_NOFOLLOW"),
        "directory ownership regression requires POSIX dir_fd support",
    )
    def test_atomic_writer_reports_only_directories_it_created(self) -> None:
        root = self.repo("atomic-directory-ownership")
        target = root / "external" / "nested" / "target.md"
        real_mkdir = os.mkdir

        def concurrent_mkdir(
            path: str,
            mode: int = 0o777,
            *,
            dir_fd: int | None = None,
        ) -> None:
            real_mkdir(path, mode=mode, dir_fd=dir_fd)
            raise FileExistsError(path)

        with mock.patch.object(mutation_helper.os, "mkdir", side_effect=concurrent_mkdir):
            created = mutation_helper.write_file_atomic(
                target,
                "planned",
                trust_root=root,
                expected_prior=None,
            )
        self.assertEqual(created, [])
        self.assertEqual(target.read_text(encoding="utf-8"), "planned\n")

    @unittest.skipUnless(
        os.name == "posix" and hasattr(os, "O_DIRECTORY") and hasattr(os, "O_NOFOLLOW"),
        "descriptor-relative removal regression requires POSIX dir_fd support",
    )
    def test_trusted_removal_cannot_follow_swapped_parent_symlinks(self) -> None:
        root = self.repo("trusted-remove-file")
        parent = root / "safe"
        parent.mkdir()
        target = parent / "created.md"
        target.write_text("created\n", encoding="utf-8")
        detached = root / "detached"
        external = self.repo("trusted-remove-file-external")
        external_target = external / "created.md"
        external_target.write_text("external\n", encoding="utf-8")
        real_unlink = os.unlink

        def swap_then_unlink(path: str, *, dir_fd: int | None = None) -> None:
            parent.rename(detached)
            parent.symlink_to(external, target_is_directory=True)
            real_unlink(path, dir_fd=dir_fd)

        with mock.patch.object(mutation_helper.os, "unlink", side_effect=swap_then_unlink):
            mutation_helper.remove_path_trusted(target, trust_root=root)

        self.assertEqual(external_target.read_text(encoding="utf-8"), "external\n")
        self.assertFalse((detached / "created.md").exists())

        directory_root = self.repo("trusted-remove-directory")
        directory_parent = directory_root / "safe"
        directory_parent.mkdir()
        created_directory = directory_parent / "created"
        created_directory.mkdir()
        detached_directory = directory_root / "detached"
        external_directory = self.repo("trusted-remove-directory-external")
        (external_directory / "created").mkdir()
        real_rmdir = os.rmdir

        def swap_then_rmdir(path: str, *, dir_fd: int | None = None) -> None:
            directory_parent.rename(detached_directory)
            directory_parent.symlink_to(external_directory, target_is_directory=True)
            real_rmdir(path, dir_fd=dir_fd)

        with mock.patch.object(mutation_helper.os, "rmdir", side_effect=swap_then_rmdir):
            mutation_helper.remove_path_trusted(
                created_directory,
                trust_root=directory_root,
                directory=True,
            )

        self.assertTrue((external_directory / "created").is_dir())
        self.assertFalse((detached_directory / "created").exists())

    @unittest.skipUnless(os.name == "nt", "Windows atomic-write regression requires Win32")
    def test_windows_atomic_writer_pins_parent_during_replace(self) -> None:
        root = self.repo("windows-atomic-pin")
        parent = root / "safe"
        parent.mkdir()
        target = parent / "target.md"
        target.write_text("before\n", encoding="utf-8")
        detached = root / "detached"
        attempted = False
        real_token_hex = mutation_helper.secrets.token_hex

        def attempt_parent_rename(size: int) -> str:
            nonlocal attempted
            if not attempted:
                attempted = True
                with self.assertRaises(OSError):
                    parent.rename(detached)
            return real_token_hex(size)

        with mock.patch.object(
            mutation_helper.secrets,
            "token_hex",
            side_effect=attempt_parent_rename,
        ):
            mutation_helper.write_file_atomic(target, "after", trust_root=root)

        self.assertTrue(attempted)
        self.assertEqual(target.read_text(encoding="utf-8"), "after\n")
        self.assertFalse(detached.exists())

    @unittest.skipUnless(os.name == "nt", "Windows metadata regression requires Win32")
    def test_windows_atomic_writer_preserves_existing_file_attributes(self) -> None:
        import ctypes
        from ctypes import wintypes

        root = self.repo("windows-atomic-metadata")
        target = self.write(root, "safe/target.md", "before\n")
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
        kernel32.GetFileAttributesW.restype = wintypes.DWORD
        kernel32.SetFileAttributesW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD]
        kernel32.SetFileAttributesW.restype = wintypes.BOOL
        invalid_attributes = 0xFFFFFFFF
        hidden_attribute = 0x00000002
        original_attributes = kernel32.GetFileAttributesW(str(target))
        self.assertNotEqual(original_attributes, invalid_attributes)
        self.assertTrue(
            kernel32.SetFileAttributesW(
                str(target),
                original_attributes | hidden_attribute,
            )
        )
        try:
            mutation_helper.write_file_atomic(target, "after", trust_root=root)
            resulting_attributes = kernel32.GetFileAttributesW(str(target))
            self.assertNotEqual(resulting_attributes, invalid_attributes)
            self.assertTrue(resulting_attributes & hidden_attribute)
            self.assertEqual(target.read_text(encoding="utf-8"), "after\n")
        finally:
            kernel32.SetFileAttributesW(str(target), original_attributes)

    @unittest.skipUnless(os.name == "nt", "Windows reparse regression requires Win32")
    def test_windows_atomic_writer_rejects_reparse_parent(self) -> None:
        root = self.repo("windows-atomic-reparse")
        external = self.repo("windows-atomic-external")
        external_target = external / "target.md"
        external_target.write_text("external\n", encoding="utf-8")
        reparse_parent = root / "linked"
        try:
            reparse_parent.symlink_to(external, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"directory symlink privilege unavailable: {type(exc).__name__}")

        with self.assertRaises(OSError):
            mutation_helper.write_file_atomic(
                reparse_parent / "target.md",
                "after",
                trust_root=root,
            )
        self.assertEqual(external_target.read_text(encoding="utf-8"), "external\n")

    @unittest.skipUnless(os.name == "nt", "Windows trusted-removal regression requires Win32")
    def test_windows_trusted_removal_deletes_files_and_directories_by_handle(self) -> None:
        root = self.repo("windows-trusted-remove")
        target = self.write(root, "safe/created.md", "created\n")
        mutation_helper.remove_path_trusted(target, trust_root=root)
        self.assertFalse(target.exists())

        directory = root / "safe" / "created"
        directory.mkdir()
        mutation_helper.remove_path_trusted(directory, trust_root=root, directory=True)
        self.assertFalse(directory.exists())

    def test_reviewed_promotion_search_scope_and_source_freshness(self) -> None:
        root = self.repo("promotion")
        self.current_root = root
        self.init(root)
        source_a = self.write(root, "docs/sources/decision.md", "Circuit breaker policy.\n")
        source_b = self.write(root, "docs/sources/evidence.md", "Failure-budget evidence.\n")
        candidate = self.candidate(
            "projects/alpha/decisions/circuit-breaker.md",
            "Circuit Breaker Decision",
            [source_a, source_b],
            body="Use a circuit breaker when the downstream failure budget is exhausted.",
            project="alpha",
        )
        promotion = self.plan(root, "promote", candidate=candidate, scope="projects/alpha")
        completed, body = self.apply(root, promotion)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(body["data"]["mutation"]["mutation_status"], "applied")

        beta = self.candidate(
            "projects/beta/decisions/retry.md",
            "Retry Decision",
            [source_a],
            body="Use a bounded retry policy for the beta project.",
            project="beta",
        )
        beta_plan = self.plan(root, "promote", candidate=beta, scope="projects/beta")
        completed, _ = self.apply(root, beta_plan)
        self.assertEqual(completed.returncode, 0, completed.stderr)

        _, health_body = run_helper(
            root, "knowledge-health", "read_only", {"scope": "projects/alpha"}
        )
        health = health_body["data"]["health"]
        self.assertTrue(health["profile_healthy"], health["findings"])
        self.assertEqual(health["concept_count"], 1)
        completed, search = run_helper(
            root,
            "knowledge-search",
            "read_only",
            {
                "query": "decision",
                "scope": "projects/alpha",
                "limit": 1,
                "snapshot_id": health["snapshot_id"],
            },
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(search["data"]["result_count"], 1)
        result = search["data"]["results"][0]
        self.assertTrue(result["path"].startswith("projects/alpha/"), result)
        self.assertTrue(result["id"])
        concept = root / "docs" / "ai" / "knowledge" / result["path"]
        self.assertEqual(result["sha256"], sha256(concept))
        self.assertLessEqual(len(result["snippet"]), 512)
        self.assertIs(result["untrusted_content"], True)
        expected_sources = {
            "docs/sources/decision.md": sha256(source_a),
            "docs/sources/evidence.md": sha256(source_b),
        }
        self.assertEqual(
            {item["path"]: item["sha256"] for item in result["sources"]},
            expected_sources,
        )

        manifest = json.loads(
            (root / "docs" / "ai" / "knowledge" / "manifest.json").read_text(encoding="utf-8")
        )
        entry = next(item for item in manifest["concepts"] if item["path"] == result["path"])
        self.assertEqual(
            {item["path"]: item["sha256"] for item in entry["sources"]},
            expected_sources,
        )

        source_b.write_text("Changed failure-budget evidence.\n", encoding="utf-8")
        _, stale_body = run_helper(
            root, "knowledge-health", "read_only", {"scope": "projects/alpha"}
        )
        stale = stale_body["data"]["health"]
        self.assertTrue(stale["okf_conformant"])
        self.assertFalse(stale["profile_healthy"])
        self.assertIn("stale_source", {finding["code"] for finding in stale["findings"]})

        completed, blocked_rebuild = run_helper(
            root,
            "knowledge-update-plan",
            "read_only",
            {"action": "rebuild", "timestamp": FIXED_TIME},
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(blocked_rebuild["diagnostics"][0]["code"], "stale_source")

    def test_source_preconditions_cover_prewrite_and_postwrite_races(self) -> None:
        root = self.repo("source-races")
        self.current_root = root
        self.init(root)
        source = self.write(root, "docs/source.md", "Reviewed source.\n")
        candidate = self.candidate("decisions/race.md", "Race Decision", [source])
        plan = self.plan(root, "promote", candidate=candidate)
        concept = root / "docs/ai/knowledge/decisions/race.md"
        original_validate = knowledge_helper._validate_apply_operations

        def change_after_recompute(repo_root: Path, operations: list[object]) -> None:
            original_validate(repo_root, operations)
            source.write_text("Changed before the first write.\n", encoding="utf-8")

        with mock.patch.object(
            knowledge_helper,
            "_validate_apply_operations",
            side_effect=change_after_recompute,
        ):
            body = self.apply_direct(root, plan)
        self.assertEqual(body["status"], "expected_failure")
        self.assertEqual(body["diagnostics"][0]["code"], "source_changed")
        self.assertFalse(body["data"]["writes_state"])
        self.assertFalse(concept.exists())

        source.write_text("Reviewed source.\n", encoding="utf-8")
        plan = self.plan(root, "promote", candidate=candidate)
        original_preconditions = knowledge_helper._validate_source_preconditions

        def change_before_result(
            repo_root: Path,
            accepted_plan: dict[str, object],
            *,
            phase: str,
        ) -> None:
            if phase == "resulting":
                source.write_text("Changed after repository writes.\n", encoding="utf-8")
            original_preconditions(repo_root, accepted_plan, phase=phase)

        with mock.patch.object(
            knowledge_helper,
            "_validate_source_preconditions",
            side_effect=change_before_result,
        ):
            body = self.apply_direct(root, plan)
        self.assertEqual(body["status"], "expected_failure")
        self.assertEqual(body["diagnostics"][0]["code"], "source_changed")
        self.assertEqual(body["data"]["mutation"]["mutation_status"], "rolled_back")
        self.assertFalse(body["data"]["writes_state"])
        self.assertFalse(concept.exists())

    def test_concurrent_target_edit_is_preserved_during_rollback(self) -> None:
        root = self.repo("concurrent-target-edit")
        plan = self.plan(root, "init")
        target = root / str(plan["operations"][0]["target"])
        concurrent_content = "external concurrent edit\n"
        original_preconditions = knowledge_helper._validate_source_preconditions

        def change_written_target(
            repo_root: Path,
            accepted_plan: dict[str, object],
            *,
            phase: str,
        ) -> None:
            if phase == "resulting":
                target.write_text(concurrent_content, encoding="utf-8")
            original_preconditions(repo_root, accepted_plan, phase=phase)

        with mock.patch.object(
            knowledge_helper,
            "_validate_source_preconditions",
            side_effect=change_written_target,
        ):
            body = self.apply_direct(root, plan)

        mutation = body["data"]["mutation"]
        self.assertEqual(body["status"], "expected_failure")
        self.assertEqual(body["diagnostics"][0]["code"], "source_changed")
        self.assertEqual(mutation["mutation_status"], "partial_failure")
        self.assertTrue(body["data"]["writes_state"])
        self.assertEqual(target.read_text(encoding="utf-8"), concurrent_content)
        self.assertTrue(
            any("concurrent change preserved" in note for note in mutation["manual_remediation"])
        )

    def test_final_snapshot_detects_an_unplanned_concept_edit(self) -> None:
        root = self.repo("final-snapshot-race")
        self.current_root = root
        self.init(root)
        source = self.write(root, "docs/source.md", "Reviewed source.\n")
        candidate = self.candidate("decisions/final-race.md", "Final Race", [source])
        completed, _ = self.apply(root, self.plan(root, "promote", candidate=candidate))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        concept = root / "docs/ai/knowledge/decisions/final-race.md"
        index = root / "docs/ai/knowledge/index.md"
        index.write_text("stale index\n", encoding="utf-8")
        plan = self.plan(root, "rebuild")
        original_validate = knowledge_helper._validate_resulting_targets

        def edit_after_target_validation(
            backups: list[tuple[Path, bytes | None, str]],
            repo_root: Path,
        ) -> None:
            original_validate(backups, repo_root)
            concept.write_text(
                concept.read_text(encoding="utf-8") + "\nExternal concurrent edit.\n",
                encoding="utf-8",
            )

        with mock.patch.object(
            knowledge_helper,
            "_validate_resulting_targets",
            side_effect=edit_after_target_validation,
        ):
            body = self.apply_direct(root, plan)

        self.assertEqual(body["status"], "expected_failure")
        self.assertEqual(body["diagnostics"][0]["code"], "source_changed")
        self.assertEqual(body["data"]["mutation"]["mutation_status"], "rolled_back")
        self.assertFalse(body["data"]["writes_state"])
        self.assertEqual(index.read_text(encoding="utf-8"), "stale index\n")
        self.assertIn("External concurrent edit.", concept.read_text(encoding="utf-8"))

    def test_source_precondition_limit_matches_contract(self) -> None:
        root = self.repo("source-precondition-limit")
        digest = "0" * 64
        records = [
            {
                "path": f"docs/source-{index:04d}.md",
                "prior_sha256": digest,
                "resulting_sha256": digest,
            }
            for index in range(knowledge_helper.MAX_SOURCE_PRECONDITIONS)
        ]
        schema = json.loads(
            (
                PLUGIN_ROOT
                / "skills"
                / "speckit-autopilot"
                / "contracts"
                / "knowledge-update-plan.schema.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            schema["properties"]["source_preconditions"]["maxItems"],
            knowledge_helper.MAX_SOURCE_PRECONDITIONS,
        )
        with (
            mock.patch.object(
                knowledge_helper,
                "_source_path",
                side_effect=lambda repo_root, raw: repo_root / raw,
            ),
            mock.patch.object(knowledge_helper, "_sha256_file", return_value=digest),
        ):
            knowledge_helper._validate_source_preconditions(
                root,
                {"source_preconditions": records},
                phase="prior",
            )
            with self.assertRaises(knowledge_helper.KnowledgeError) as captured:
                knowledge_helper._validate_source_preconditions(
                    root,
                    {"source_preconditions": [*records, records[0] | {"path": "docs/overflow.md"}]},
                    phase="prior",
                )
        self.assertEqual(captured.exception.code, "invalid_plan")

        concepts = [
            SimpleNamespace(metadata={}, relative_path=f"decisions/source-{index}.md")
            for index in range(2)
        ]
        source_records = [
            [("x-speckit-sources", f"docs/source-{index}.md", digest)]
            for index in range(2)
        ]
        with (
            mock.patch.object(knowledge_helper, "MAX_SOURCE_PRECONDITIONS", 1),
            mock.patch.object(
                knowledge_helper,
                "_source_token_records",
                side_effect=source_records,
            ),
            mock.patch.object(
                knowledge_helper,
                "_source_path",
                side_effect=lambda repo_root, raw: repo_root / raw,
            ),
            mock.patch.object(knowledge_helper, "_sha256_file", return_value=digest),
        ):
            with self.assertRaises(knowledge_helper.KnowledgeError) as construction_error:
                knowledge_helper._build_source_preconditions(
                    root,
                    concepts,
                    [],
                    action="rebuild",
                )
        self.assertEqual(construction_error.exception.code, "plan_too_large")

    def test_tree_inventories_stop_at_their_entry_limits(self) -> None:
        root = self.repo("bounded-inventories")
        for index in range(3):
            self.write(
                root,
                f"docs/ai/knowledge/decisions/item-{index}.md",
                f"# Item {index}\n",
            )
        with mock.patch.object(knowledge_helper, "MAX_KNOWLEDGE_SCAN_ENTRIES", 2):
            with self.assertRaises(knowledge_helper.KnowledgeError) as captured:
                knowledge_helper._load_concepts(root)
        self.assertEqual(captured.exception.code, "oversized_bundle")

        candidate_root = root / "docs/ai/specs/.process/knowledge-candidates"
        candidate_root.mkdir(parents=True)
        for index in range(3):
            (candidate_root / f"candidate-{index}.json").write_text("{}", encoding="utf-8")
        with mock.patch.object(knowledge_helper, "MAX_CANDIDATE_SCAN_ENTRIES", 2):
            _, findings = knowledge_helper._candidate_inventory(root)
        self.assertEqual(findings[0]["code"], "candidate_inventory_too_large")

    def test_legacy_up_fragment_contract_matches_runtime(self) -> None:
        schema = json.loads(
            (
                PLUGIN_ROOT
                / "skills"
                / "speckit-autopilot"
                / "contracts"
                / "knowledge-candidate.schema.json"
            ).read_text(encoding="utf-8")
        )
        legacy_up = "[Demo roadmap](../demo-roadmap-MOC.md#DEMO-001)"
        pattern = schema["properties"]["legacy_up"]["pattern"]
        self.assertIsNotNone(re.fullmatch(pattern, legacy_up))
        self.assertTrue(
            knowledge_helper._legacy_up_targets_project(
                legacy_up,
                "docs/ai/specs/DEMO-001/SPEC-MOC.md",
                "demo",
            )
        )

    def test_secrets_and_stale_plans_or_snapshots_fail_without_writes(self) -> None:
        root = self.repo("conflicts")
        self.current_root = root
        self.init(root)
        source_a = self.write(root, "docs/a.md", "Source A.\n")
        source_b = self.write(root, "docs/b.md", "Source B.\n")

        before_secret = file_snapshot(root)
        secret = self.candidate(
            "decisions/unsafe.md",
            "Unsafe Decision",
            [source_a],
            body="api_key=ABCDEFGHIJKLMNOPQRSTUV",
        )
        completed, rejected = run_helper(
            root,
            "knowledge-update-plan",
            "read_only",
            {"action": "promote", "timestamp": FIXED_TIME, "candidate": secret},
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(rejected["diagnostics"][0]["code"], "sensitive_content")
        self.assertEqual(file_snapshot(root), before_secret)

        stale_plan = self.plan(
            root,
            "promote",
            candidate=self.candidate("decisions/first.md", "First Decision", [source_a]),
        )
        current_plan = self.plan(
            root,
            "promote",
            candidate=self.candidate("decisions/second.md", "Second Decision", [source_b]),
        )
        completed, _ = self.apply(root, current_plan)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        before_stale_apply = file_snapshot(root)

        completed, conflict = self.apply(root, stale_plan)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(conflict["status"], "expected_failure")
        self.assertIn(conflict["diagnostics"][0]["code"], {"plan_changed", "snapshot_changed"})
        self.assertEqual(file_snapshot(root), before_stale_apply)

        completed, snapshot_conflict = run_helper(
            root,
            "knowledge-search",
            "read_only",
            {"query": "decision", "snapshot_id": stale_plan["expected_snapshot"]},
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(snapshot_conflict["diagnostics"][0]["code"], "snapshot_changed")

    def test_apply_lock_serializes_validation_writes_and_rollback(self) -> None:
        root = self.repo("apply-lock")
        plan = self.plan(root, "init")
        before = file_snapshot(root)
        real_writer = knowledge_helper.write_file_atomic
        real_remove = knowledge_helper.remove_path_trusted
        lock_diagnostics: list[str] = []
        write_count = 0

        def nested_apply_code() -> str:
            nested = self.apply_direct(root, plan)
            self.assertEqual(nested["status"], "expected_failure")
            return str(nested["diagnostics"][0]["code"])

        def serialize_then_fail(
            target: Path,
            content: str | bytes,
            *,
            trust_root: Path | None = None,
            expected_prior: bytes | None | object,
            created_directory_records: dict[Path, tuple[int, int]] | None = None,
        ) -> list[mutation_helper.CreatedDirectory]:
            nonlocal write_count
            lock_diagnostics.append(nested_apply_code())
            if write_count >= 1:
                raise OSError("injected write failure after lock check")
            write_count += 1
            return real_writer(
                target,
                content,
                trust_root=trust_root,
                expected_prior=expected_prior,
                created_directory_records=created_directory_records,
            )

        def serialize_remove(
            target: Path,
            *,
            trust_root: Path,
            directory: bool = False,
        ) -> None:
            lock_diagnostics.append(nested_apply_code())
            real_remove(target, trust_root=trust_root, directory=directory)

        with (
            mock.patch.object(knowledge_helper, "write_file_atomic", side_effect=serialize_then_fail),
            mock.patch.object(knowledge_helper, "remove_path_trusted", side_effect=serialize_remove),
        ):
            body = self.apply_direct(root, plan)

        self.assertEqual(body["status"], "expected_failure")
        self.assertEqual(body["data"]["mutation"]["mutation_status"], "rolled_back")
        self.assertGreaterEqual(len(lock_diagnostics), 3)
        self.assertEqual(set(lock_diagnostics), {"mutation_locked"})
        self.assertEqual(file_snapshot(root), before)

    def test_windows_knowledge_mutex_name_is_cross_session(self) -> None:
        self.assertEqual(
            knowledge_helper._windows_knowledge_mutex_name("abc123"),
            "Global\\SpeckitProKnowledge-abc123",
        )

    def test_hash_consistent_malformed_plan_request_is_input_error(self) -> None:
        root = self.repo("malformed-plan-request")
        plan = json.loads(json.dumps(self.plan(root, "init")))
        plan["request"]["timestamp"] = 123
        plan["plan_hash"] = knowledge_helper._plan_hash(plan)

        body = self.apply_direct(root, plan)

        self.assertEqual(body["status"], "input_error")
        self.assertEqual(body["diagnostics"][0]["code"], "invalid_plan")
        self.assertFalse(body["data"]["writes_state"])
        self.assertEqual(body["data"]["mutation"]["mutation_status"], "blocked")
        self.assertFalse((root / "docs" / "ai" / "knowledge").exists())

        malformed = json.loads(json.dumps(self.plan(root, "init")))
        malformed["unexpected"] = True
        malformed["plan_hash"] = knowledge_helper._plan_hash(malformed)
        body = self.apply_direct(root, malformed)
        self.assertEqual(body["status"], "input_error")
        self.assertEqual(body["diagnostics"][0]["code"], "invalid_plan")

        malformed = json.loads(json.dumps(self.plan(root, "init")))
        malformed["operation_count"] += 1
        malformed["plan_hash"] = knowledge_helper._plan_hash(malformed)
        body = self.apply_direct(root, malformed)
        self.assertEqual(body["status"], "input_error")
        self.assertEqual(body["diagnostics"][0]["code"], "invalid_plan")

    def test_apply_recomputation_errors_are_repository_failures(self) -> None:
        root = self.repo("apply-recompute-error")
        self.current_root = root
        self.init(root)
        source = self.write(root, "docs/source.md", "Reviewed source.\n")
        candidate = self.candidate("decisions/source.md", "Source Decision", [source])
        completed, _ = self.apply(root, self.plan(root, "promote", candidate=candidate))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        plan = self.plan(root, "rebuild")
        concept = root / "docs/ai/knowledge/decisions/source.md"
        concept.write_bytes(b"\xffinvalid-utf8")

        body = self.apply_direct(root, plan)
        self.assertEqual(body["status"], "expected_failure")
        self.assertEqual(body["diagnostics"][0]["code"], "invalid_utf8")
        self.assertFalse(body["data"]["writes_state"])

    def test_portable_path_aliases_cannot_overwrite_concepts(self) -> None:
        root = self.repo("portable-path-alias")
        self.current_root = root
        self.init(root)
        source = self.write(root, "docs/source.md", "Reviewed source.\n")
        original = self.candidate("decisions/Foo.md", "Original", [source])
        completed, _ = self.apply(root, self.plan(root, "promote", candidate=original))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        original_path = root / "docs/ai/knowledge/decisions/Foo.md"
        original_bytes = original_path.read_bytes()

        alias = self.candidate("decisions/foo.md", "Alias", [source])
        completed, body = run_helper(
            root,
            "knowledge-update-plan",
            "read_only",
            {"action": "promote", "timestamp": FIXED_TIME, "candidate": alias},
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(body["diagnostics"][0]["code"], "portable_path_collision")
        self.assertEqual(original_path.read_bytes(), original_bytes)

    def test_partial_apply_rolls_back_repository_files(self) -> None:
        root = self.repo("rollback")
        plan = self.plan(root, "init")
        before = file_snapshot(root)

        completed, rejected = self.apply(root, plan, simulate_failure_after=1)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(rejected["status"], "input_error")
        self.assertEqual(rejected["diagnostics"][0]["code"], "invalid_input")
        self.assertEqual(file_snapshot(root), before)

        real_writer = knowledge_helper.write_file_atomic
        write_count = 0

        def fail_after_one(
            target: Path,
            content: str,
            *,
            trust_root: Path | None = None,
            expected_prior: bytes | None | object,
            created_directory_records: dict[Path, tuple[int, int]] | None = None,
        ) -> list[mutation_helper.CreatedDirectory]:
            nonlocal write_count
            if write_count >= 1:
                raise OSError("injected test write failure")
            write_count += 1
            return real_writer(
                target,
                content,
                trust_root=trust_root,
                expected_prior=expected_prior,
                created_directory_records=created_directory_records,
            )

        with mock.patch.object(knowledge_helper, "write_file_atomic", side_effect=fail_after_one):
            body = self.apply_direct(root, plan)
        self.assertEqual(body["status"], "expected_failure")
        self.assertEqual(body["diagnostics"][0]["code"], "write_failure")
        self.assertEqual(body["data"]["mutation"]["mutation_status"], "rolled_back")
        self.assertFalse(body["data"]["writes_state"])
        self.assertEqual(file_snapshot(root), before)
        self.assertFalse((root / "docs" / "ai" / "knowledge").exists())

    def test_rollback_restores_original_bytes_exactly(self) -> None:
        root = self.repo("rollback-exact-bytes")
        self.init(root)
        log = root / "docs/ai/knowledge/log.md"
        manifest = root / "docs/ai/knowledge/manifest.json"
        original_log = b"\xffinvalid-log-without-final-newline"
        original_manifest = b"invalid-manifest-without-final-newline"
        log.write_bytes(original_log)
        manifest.write_bytes(original_manifest)
        plan = self.plan(root, "rebuild")
        self.assertGreaterEqual(plan["operation_count"], 2)
        real_writer = knowledge_helper.write_file_atomic
        write_count = 0

        def fail_after_one(
            target: Path,
            content: str | bytes,
            *,
            trust_root: Path | None = None,
            expected_prior: bytes | None | object,
            created_directory_records: dict[Path, tuple[int, int]] | None = None,
        ) -> list[mutation_helper.CreatedDirectory]:
            nonlocal write_count
            if isinstance(content, bytes):
                return real_writer(
                    target,
                    content,
                    trust_root=trust_root,
                    expected_prior=expected_prior,
                    created_directory_records=created_directory_records,
                )
            if write_count >= 1:
                raise OSError("injected test write failure")
            write_count += 1
            return real_writer(
                target,
                content,
                trust_root=trust_root,
                expected_prior=expected_prior,
                created_directory_records=created_directory_records,
            )

        with mock.patch.object(knowledge_helper, "write_file_atomic", side_effect=fail_after_one):
            body = self.apply_direct(root, plan)

        self.assertEqual(body["status"], "expected_failure")
        self.assertEqual(body["data"]["mutation"]["mutation_status"], "rolled_back")
        self.assertEqual(log.read_bytes(), original_log)
        self.assertEqual(manifest.read_bytes(), original_manifest)

    def test_apply_preserves_unreadable_target_diagnostic(self) -> None:
        root = self.repo("apply-unreadable")
        plan = self.plan(root, "init")
        operation = plan["operations"][0]
        unreadable = knowledge_helper.KnowledgeError(
            "unreadable_file",
            "knowledge update target could not be read",
            details={"path": operation["target"], "error": "PermissionError"},
        )
        with mock.patch.object(
            knowledge_helper,
            "_read_apply_target",
            side_effect=unreadable,
        ):
            body = self.apply_direct(root, plan)

        self.assertEqual(body["status"], "expected_failure")
        self.assertEqual(body["diagnostics"][0]["code"], "unreadable_file")
        self.assertEqual(body["diagnostics"][0]["details"]["error"], "PermissionError")
        self.assertFalse(body["data"]["writes_state"])

        with mock.patch.object(
            knowledge_helper,
            "_validate_apply_operations",
            side_effect=unreadable,
        ):
            body = self.apply_direct(root, plan)
        self.assertEqual(body["status"], "expected_failure")
        self.assertEqual(body["diagnostics"][0]["code"], "unreadable_file")
        self.assertEqual(body["diagnostics"][0]["details"]["path"], operation["target"])

    def test_apply_classifies_oversized_targets_as_repository_failures(self) -> None:
        root = self.repo("apply-oversized")
        plan = self.plan(root, "init")
        target = root / plan["operations"][0]["target"]
        oversized = b"x" * (knowledge_helper.MAX_PLAN_CONTENT_BYTES + 1)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(oversized)

        body = self.apply_direct(root, plan)
        self.assertEqual(body["status"], "expected_failure")
        self.assertEqual(body["diagnostics"][0]["code"], "oversized_concept")
        self.assertFalse(body["data"]["writes_state"])

        target.unlink()
        original_validate = knowledge_helper._validate_apply_operations

        def grow_after_validation(repo_root: Path, operations: list[object]) -> None:
            original_validate(repo_root, operations)
            target.write_bytes(oversized)

        with mock.patch.object(
            knowledge_helper,
            "_validate_apply_operations",
            side_effect=grow_after_validation,
        ):
            body = self.apply_direct(root, plan)
        self.assertEqual(body["status"], "expected_failure")
        self.assertEqual(body["diagnostics"][0]["code"], "oversized_concept")
        self.assertFalse(body["data"]["writes_state"])

    def test_archive_requires_fresh_sources_through_apply(self) -> None:
        root = self.repo("archive-source-freshness")
        self.current_root = root
        self.init(root)
        source = self.write(root, "docs/archive-source.md", "Reviewed archive source.\n")
        candidate = self.candidate("decisions/archive.md", "Archive Decision", [source])
        completed, _ = self.apply(root, self.plan(root, "promote", candidate=candidate))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        concept = root / "docs/ai/knowledge/decisions/archive.md"

        completed, invalid_evidence = run_helper(
            root,
            "knowledge-update-plan",
            "read_only",
            {
                "action": "archive",
                "timestamp": FIXED_TIME,
                "concept_path": "decisions/archive.md",
                "sources": [{"path": source.relative_to(root).as_posix()}],
            },
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(invalid_evidence["diagnostics"][0]["code"], "invalid_input")

        source.write_text("Stale archive source.\n", encoding="utf-8")
        completed, stale = run_helper(
            root,
            "knowledge-update-plan",
            "read_only",
            {
                "action": "archive",
                "timestamp": FIXED_TIME,
                "concept_path": "decisions/archive.md",
            },
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(stale["diagnostics"][0]["code"], "stale_source")

        source.write_text("Reviewed archive source.\n", encoding="utf-8")
        plan = self.plan(root, "archive", concept_path="decisions/archive.md")
        before = file_snapshot(root)
        original_preconditions = knowledge_helper._validate_source_preconditions

        def change_before_result(
            repo_root: Path,
            accepted_plan: dict[str, object],
            *,
            phase: str,
        ) -> None:
            if phase == "resulting":
                source.write_text("Changed during archive apply.\n", encoding="utf-8")
            original_preconditions(repo_root, accepted_plan, phase=phase)

        with mock.patch.object(
            knowledge_helper,
            "_validate_source_preconditions",
            side_effect=change_before_result,
        ):
            body = self.apply_direct(root, plan)
        self.assertEqual(body["status"], "expected_failure")
        self.assertEqual(body["diagnostics"][0]["code"], "source_changed")
        self.assertEqual(body["data"]["mutation"]["mutation_status"], "rolled_back")
        self.assertNotIn('x-speckit-status: "archived"', concept.read_text(encoding="utf-8"))
        after = file_snapshot(root)
        after[source.relative_to(root).as_posix()] = before[source.relative_to(root).as_posix()]
        self.assertEqual(after, before)

    def test_migrated_map_can_be_archived_without_revalidating_cutover_hashes(self) -> None:
        root = self.repo("migrated-map-archive")
        self.current_root = root
        roadmap = self.write(
            root,
            "docs/ai/specs/demo-technical-roadmap.md",
            "# Demo Technical Roadmap\n\n## DEMO-001\n\nReviewed behavior.\n",
        )
        self.write(
            root,
            "docs/ai/specs/demo-roadmap-MOC.md",
            "# Demo Roadmap Map\n\nCurated pre-cutover grouping.\n",
        )
        completed, _ = self.apply(root, self.plan(root, "migrate", reviewed=True))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        concept = root / "docs/ai/knowledge/projects/demo/roadmap.md"
        self.assertIn("x-speckit-migration-sources", concept.read_text(encoding="utf-8"))

        archive = self.plan(
            root,
            "archive",
            concept_path="projects/demo/roadmap.md",
            sources=[{
                "path": roadmap.relative_to(root).as_posix(),
                "section": "archived roadmap",
                "sha256": sha256(roadmap),
            }],
        )
        completed, _ = self.apply(root, archive)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('x-speckit-status: "archived"', concept.read_text(encoding="utf-8"))

    def test_apply_classifies_source_drift_as_repository_failure(self) -> None:
        cases = {
            "stale": "stale_source",
            "missing": "missing_source",
            "oversized": "oversized_source",
        }
        for case, expected_code in cases.items():
            with self.subTest(case=case):
                root = self.repo(f"apply-source-{case}")
                self.current_root = root
                self.init(root)
                source = self.write(root, "docs/source.md", "Reviewed source.\n")
                candidate = self.candidate("decisions/source.md", "Source Decision", [source])
                completed, _ = self.apply(root, self.plan(root, "promote", candidate=candidate))
                self.assertEqual(completed.returncode, 0, completed.stderr)
                plan = self.plan(root, "rebuild")

                if case == "stale":
                    source.write_text("Changed source.\n", encoding="utf-8")
                elif case == "missing":
                    source.unlink()
                else:
                    source.write_bytes(b"x" * (knowledge_helper.MAX_SOURCE_BYTES + 1))

                body = self.apply_direct(root, plan)
                self.assertEqual(body["status"], "expected_failure")
                self.assertEqual(body["diagnostics"][0]["code"], expected_code)
                self.assertFalse(body["data"]["writes_state"])

    def test_rollback_failure_reports_residual_writes(self) -> None:
        root = self.repo("rollback-failure")
        self.init(root)
        manifest = root / "docs/ai/knowledge/manifest.json"
        manifest.write_text("invalid\n", encoding="utf-8")
        plan = self.plan(root, "rebuild")
        self.assertGreaterEqual(plan["operation_count"], 2)
        before = file_snapshot(root)
        real_writer = knowledge_helper.write_file_atomic
        write_count = 0

        def fail_write_and_rollback(
            target: Path,
            content: str,
            *,
            trust_root: Path | None = None,
            expected_prior: bytes | None | object,
            created_directory_records: dict[Path, tuple[int, int]] | None = None,
        ) -> list[mutation_helper.CreatedDirectory]:
            nonlocal write_count
            write_count += 1
            if write_count >= 2:
                raise OSError("injected rollback failure")
            return real_writer(
                target,
                content,
                trust_root=trust_root,
                expected_prior=expected_prior,
                created_directory_records=created_directory_records,
            )

        with mock.patch.object(
            knowledge_helper,
            "write_file_atomic",
            side_effect=fail_write_and_rollback,
        ):
            body = self.apply_direct(root, plan)

        mutation = body["data"]["mutation"]
        self.assertEqual(body["status"], "expected_failure")
        self.assertEqual(mutation["mutation_status"], "partial_failure")
        self.assertTrue(body["data"]["writes_state"])
        self.assertTrue(mutation["live_mutation"])
        self.assertIsNotNone(mutation["failure_operation"])
        self.assertNotEqual(file_snapshot(root), before)

    def test_generated_state_repairs_and_existing_secrets_are_not_searchable(self) -> None:
        root = self.repo("generated-repair")
        self.current_root = root
        self.init(root)
        source = self.write(root, "docs/source.md", "Reviewed source.\n")
        promotion = self.plan(
            root,
            "promote",
            candidate=self.candidate("decisions/searchable.md", "Searchable Decision", [source]),
        )
        completed, _ = self.apply(root, promotion)
        self.assertEqual(completed.returncode, 0, completed.stderr)

        knowledge_root = root / "docs" / "ai" / "knowledge"
        log_path = knowledge_root / "log.md"
        log_path.unlink()
        _, missing_log = run_helper(root, "knowledge-health", "read_only")
        self.assertIn(
            "missing_log",
            {finding["code"] for finding in missing_log["data"]["health"]["findings"]},
        )
        repair = self.plan(root, "rebuild")
        self.assertIn("docs/ai/knowledge/log.md", {op["target"] for op in repair["operations"]})
        completed, _ = self.apply(root, repair)
        self.assertEqual(completed.returncode, 0, completed.stderr)

        manifest_path = knowledge_root / "manifest.json"
        manifest_path.write_bytes(b"\xff\xfeinvalid")
        _, invalid_manifest = run_helper(root, "knowledge-health", "read_only")
        self.assertIn(
            "invalid_manifest",
            {finding["code"] for finding in invalid_manifest["data"]["health"]["findings"]},
        )
        repair = self.plan(root, "rebuild")
        completed, _ = self.apply(root, repair)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        json.loads(manifest_path.read_text(encoding="utf-8"))

        concept_path = knowledge_root / "decisions" / "searchable.md"
        concept_path.write_text(
            concept_path.read_text(encoding="utf-8")
            + "\napi_key=ABCDEFGHIJKLMNOPQRSTUV\n",
            encoding="utf-8",
        )
        _, secret_health = run_helper(root, "knowledge-health", "read_only")
        self.assertIn(
            "sensitive_content",
            {finding["code"] for finding in secret_health["data"]["health"]["findings"]},
        )
        completed, search = run_helper(root, "knowledge-search", "read_only", {"query": "searchable"})
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(search["data"]["result_count"], 0)

    def test_supersession_history_and_source_drift_are_evidence_backed(self) -> None:
        root = self.repo("supersession")
        self.current_root = root
        self.init(root)
        attachment = self.write(
            root,
            "docs/ai/knowledge/attachments/old.txt",
            "Historical attachment.\n",
        )
        old_source = self.write(root, "docs/old.md", "Original reviewed evidence.\n")
        new_source = self.write(root, "docs/new.md", "Replacement reviewed evidence.\n")
        old_plan = self.plan(
            root,
            "promote",
            candidate=self.candidate(
                "decisions/original.md",
                "Original Decision",
                [old_source],
                body="Original decision with [historical evidence](../attachments/old.txt).",
            ),
        )
        completed, _ = self.apply(root, old_plan)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        replacement = self.candidate(
            "decisions/replacement.md",
            "Replacement Decision",
            [new_source],
            body="Use the materially revised replacement decision.",
        )
        rekeyed = dict(replacement)
        rekeyed["id"] = "different-join-key"
        completed, rejected = run_helper(
            root,
            "knowledge-update-plan",
            "read_only",
            {
                "action": "supersede",
                "timestamp": FIXED_TIME,
                "concept_path": "decisions/original.md",
                "replacement": rekeyed,
            },
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(rejected["diagnostics"][0]["code"], "invalid_transition")
        replacement["id"] = "decisions/original"
        supersede = self.plan(
            root,
            "supersede",
            concept_path="decisions/original.md",
            replacement=replacement,
        )
        completed, _ = self.apply(root, supersede)
        self.assertEqual(completed.returncode, 0, completed.stderr)

        _, current = run_helper(root, "knowledge-search", "read_only", {"query": "decision"})
        self.assertEqual(
            {item["path"] for item in current["data"]["results"]},
            {"decisions/replacement.md"},
        )
        _, historical = run_helper(
            root,
            "knowledge-search",
            "read_only",
            {"query": "decision", "include_historical": True},
        )
        self.assertEqual(
            {item["path"] for item in historical["data"]["results"]},
            {"decisions/original.md", "decisions/replacement.md"},
        )

        old_source.write_text("Original evidence changed after supersession.\n", encoding="utf-8")
        attachment.unlink()
        _, drift = run_helper(root, "knowledge-health", "read_only")
        self.assertIn(
            "historical_source_drift",
            {finding["code"] for finding in drift["data"]["health"]["advisories"]},
        )
        self.assertIn(
            "historical_broken_link",
            {finding["code"] for finding in drift["data"]["health"]["advisories"]},
        )
        self.assertTrue(drift["data"]["health"]["profile_healthy"])

    def test_migration_preserves_legacy_memory_sections_and_moc_compatibility(self) -> None:
        root = self.repo("migration")
        memory = self.write(
            root,
            ".specify/memory/spec.md",
            "# Feature Specifications\n\n"
            "## SPEC-101: Alpha\n\nAlpha invariant survives section migration.\n\n"
            "## SPEC-102: Beta\n\nBeta invariant survives section migration.\n",
        )
        plan_memory = self.write(root, ".specify/memory/plan.md", "# Plans\n\n## SPEC-101\n\nAlpha plan.\n")
        changelog = self.write(root, ".specify/memory/changelog.md", "# Changelog\n\n## 2026-07-14\n\nMerged SPEC-101.\n")
        roadmap = self.write(
            root,
            "docs/ai/specs/demo-technical-roadmap.md",
            "# Demo Technical Roadmap\n\n## SPEC-101\n\nBuild the alpha behavior.\n",
        )
        self.write(
            root,
            "docs/ai/specs/future-technical-roadmap.md",
            "# Future Technical Roadmap\n\n## FUT-001\n\nBuild a future behavior.\n",
        )
        roadmap_moc = self.write(
            root,
            "docs/ai/specs/demo-roadmap-MOC.md",
            "---\nstatus: maintenance-window\nrank: 1\nrelated:\n  - \"[Runbook](../runbook.md)\"\n  - \"[Policy](../policy.md)\"\nspec_id: DEMO\nstructureVersion: 1\n---\n"
            "# Demo Roadmap Map\n\nCurated roadmap grouping must survive.\n\n"
            "<!-- GENERATED:INDEX:START (do not edit; regenerated by generate-spec-index) -->\n"
            "old index\n<!-- GENERATED:INDEX:END -->\n",
        )
        spec_moc = self.write(
            root,
            "specs/SPEC-101/SPEC-MOC.md",
            "---\n"
            "up: \"[Demo](../../docs/ai/specs/demo-roadmap-MOC.md)\"\n"
            "status: active\nrelated:\n  - \"[Sibling](../SPEC-102/SPEC-MOC.md)\"\nspec_id: SPEC-101\nstructureVersion: 1\n---\n"
            "# SPEC-101 Map\n\nCurated spec relationship must survive.\n\n"
            "<!-- GENERATED:BACKLINKS:START (do not edit; regenerated by generate-spec-index) -->\n"
            "old backlinks\n<!-- GENERATED:BACKLINKS:END -->\n",
        )
        legacy_before = {path: path.read_bytes() for path in (memory, plan_memory, changelog)}
        pending_migration = self.plan(root, "migrate")
        self.assertTrue(any("review" in warning.lower() for warning in pending_migration["warnings"]))
        completed, pending = self.apply(root, pending_migration)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(pending["data"]["mutation"]["mutation_status"], "applied")
        pending_project = root / "docs/ai/knowledge/projects/demo/roadmap.md"
        pending_spec = root / "docs/ai/knowledge/projects/demo/specs/spec-101.md"
        for pending_map in (pending_project, pending_spec):
            pending_text = pending_map.read_text(encoding="utf-8")
            self.assertIn('x-speckit-authority: "source-backed"', pending_text)
            self.assertIn('x-speckit-status: "review-required"', pending_text)
            self.assertNotIn("x-speckit-legacy-view", pending_text)
        self.assertNotIn("x-speckit-generated-from:", roadmap_moc.read_text(encoding="utf-8"))
        self.assertNotIn("x-speckit-generated-from:", spec_moc.read_text(encoding="utf-8"))

        memory_review = self.plan(root, "migrate", legacy_memory_reviewed=True)
        completed, reviewed_memory = self.apply(root, memory_review)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(reviewed_memory["data"]["mutation"]["mutation_status"], "applied")

        migration = self.plan(root, "migrate", reviewed=True)
        completed, applied = self.apply(root, migration)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(applied["data"]["mutation"]["mutation_status"], "applied")
        self.assertEqual({path: path.read_bytes() for path in legacy_before}, legacy_before)

        settled = self.plan(root, "migrate", legacy_memory_reviewed=True, reviewed=True)
        self.assertEqual(settled["operation_count"], 0)

        concepts = [
            path
            for path in (root / "docs" / "ai" / "knowledge").rglob("*.md")
            if path.name not in {"index.md", "log.md"}
        ]
        alpha = [path for path in concepts if "Alpha invariant" in path.read_text(encoding="utf-8")]
        beta = [path for path in concepts if "Beta invariant" in path.read_text(encoding="utf-8")]
        self.assertEqual(len(alpha), 1)
        self.assertEqual(len(beta), 1)
        self.assertNotEqual(alpha[0], beta[0])

        manifest = json.loads(
            (root / "docs" / "ai" / "knowledge" / "manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            {entry["path"]: entry["sha256"] for entry in manifest["legacy_memory"]},
            {
                ".specify/memory/spec.md": sha256(memory),
                ".specify/memory/plan.md": sha256(plan_memory),
                ".specify/memory/changelog.md": sha256(changelog),
            },
        )
        self.assertEqual(manifest["legacy_memory_status"], "frozen")
        self.assertIn("Curated roadmap grouping must survive.", roadmap_moc.read_text(encoding="utf-8"))
        self.assertIn("Curated spec relationship must survive.", spec_moc.read_text(encoding="utf-8"))
        self.assertIn("x-speckit-generated-from:", roadmap_moc.read_text(encoding="utf-8"))
        self.assertIn("x-speckit-generated-from:", spec_moc.read_text(encoding="utf-8"))
        self.assertIn('status: "maintenance-window"', roadmap_moc.read_text(encoding="utf-8"))
        self.assertIn(
            'related: ["[Runbook](../runbook.md)","[Policy](../policy.md)"]',
            roadmap_moc.read_text(encoding="utf-8"),
        )
        self.assertIn(
            'related: ["[Sibling](../SPEC-102/SPEC-MOC.md)"]',
            spec_moc.read_text(encoding="utf-8"),
        )
        for zone in ("INDEX", "PRS", "BACKLINKS"):
            self.assertIn(f"GENERATED:{zone}:START", spec_moc.read_text(encoding="utf-8"))
        self.assertTrue((root / "docs/ai/specs/future-roadmap-MOC.md").is_file())
        self.assertTrue(roadmap.is_file())

        _, health_body = run_helper(root, "knowledge-health", "read_only")
        health = health_body["data"]["health"]
        finding_codes = {finding["code"] for finding in health["findings"]}
        self.assertTrue(health["okf_conformant"], health["findings"])
        self.assertNotIn("stale_source", finding_codes)
        self.assertNotIn("legacy_memory_pending_review", finding_codes)
        self.assertEqual(health["legacy_memory_status"], "frozen")
        self.assertTrue(health["migration"]["complete"])

    def test_scoped_first_promotion_candidate_inventory_and_project_ids(self) -> None:
        root = self.repo("scoped-first")
        self.current_root = root
        source = self.write(root, "docs/source.md", "Reviewed source.\n")
        alpha = self.candidate(
            "projects/alpha/decisions/spec-001.md",
            "Alpha SPEC-001",
            [source],
            project="alpha",
        )
        alpha["id"] = "SPEC-001"
        first = self.plan(root, "promote", candidate=alpha, scope="projects/alpha")
        targets = {operation["target"] for operation in first["operations"]}
        self.assertIn("docs/ai/knowledge/index.md", targets)
        self.assertIn("docs/ai/knowledge/decisions/index.md", targets)
        completed, _ = self.apply(root, first)
        self.assertEqual(completed.returncode, 0, completed.stderr)

        duplicate = self.candidate(
            "projects/alpha/decisions/duplicate.md",
            "Duplicate Alpha ID",
            [source],
        )
        duplicate["id"] = "SPEC-001"
        completed, duplicate_body = run_helper(
            root,
            "knowledge-update-plan",
            "read_only",
            {"action": "promote", "timestamp": FIXED_TIME, "candidate": duplicate},
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(duplicate_body["diagnostics"][0]["code"], "duplicate_id")

        spoofed = self.candidate(
            "projects/alpha/decisions/spoofed.md",
            "Spoofed Project",
            [source],
            project="beta",
        )
        completed, spoofed_body = run_helper(
            root,
            "knowledge-update-plan",
            "read_only",
            {"action": "promote", "timestamp": FIXED_TIME, "candidate": spoofed},
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(spoofed_body["diagnostics"][0]["code"], "invalid_input")

        beta = self.candidate(
            "projects/beta/decisions/spec-001.md",
            "Beta SPEC-001",
            [source],
            project="beta",
        )
        beta["id"] = "SPEC-001"
        completed, _ = self.apply(
            root,
            self.plan(root, "promote", candidate=beta, scope="projects/beta"),
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

        proposed = self.candidate(
            "projects/alpha/decisions/pending.md",
            "Pending Review",
            [source],
            project="alpha",
        )
        proposed.update({"state": "proposed", "reviewed": False})
        packet = root / "docs/ai/specs/.process/knowledge-candidates/pending.json"
        packet.parent.mkdir(parents=True)
        packet.write_text(json.dumps(proposed), encoding="utf-8")
        malformed_beta = (
            root
            / "docs/ai/specs/.process/knowledge-candidates/projects/beta/malformed.txt"
        )
        malformed_beta.parent.mkdir(parents=True)
        malformed_beta.write_text("not a packet", encoding="utf-8")
        _, report = run_helper(root, "knowledge-health", "read_only", {"scope": "projects/alpha"})
        health = report["data"]["health"]
        self.assertTrue(health["profile_healthy"], health["findings"])
        self.assertEqual(health["candidates"]["pending_review_count"], 1)
        _, global_report = run_helper(root, "knowledge-health", "read_only")
        self.assertIn(
            "invalid_candidate_packet",
            {item["code"] for item in global_report["data"]["health"]["findings"]},
        )

        completed, oversized = run_helper(
            root,
            "knowledge-search",
            "read_only",
            {"query": "x" * 4097},
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(oversized["diagnostics"][0]["code"], "invalid_input")

        alpha_path = root / "docs/ai/knowledge/projects/alpha/decisions/spec-001.md"
        alpha_text = alpha_path.read_text(encoding="utf-8")
        alpha_path.write_text(
            alpha_text.replace(
                'x-speckit-project: "alpha"',
                'x-speckit-project: "beta"',
            ),
            encoding="utf-8",
        )
        _, edited = run_helper(root, "knowledge-health", "read_only", {"scope": "projects/alpha"})
        self.assertIn(
            "invalid_project",
            {item["code"] for item in edited["data"]["health"]["findings"]},
        )

    def test_same_path_map_supersession_restores_health_and_archive_keeps_view(self) -> None:
        root = self.repo("map-history")
        self.current_root = root
        roadmap = self.write(
            root,
            "docs/ai/specs/demo-technical-roadmap.md",
            "# Demo Technical Roadmap\n\n## SPEC-001\n\nOriginal behavior.\n",
        )
        completed, _ = self.apply(root, self.plan(root, "migrate", reviewed=True))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        roadmap.write_text(
            "# Demo Technical Roadmap\n\n## SPEC-001\n\nMaterially revised behavior.\n",
            encoding="utf-8",
        )
        _, stale = run_helper(root, "knowledge-health", "read_only")
        self.assertIn(
            "stale_source",
            {finding["code"] for finding in stale["data"]["health"]["findings"]},
        )
        replacement = {
            "concept_path": "projects/demo/roadmap.md",
            "type": "speckit-project-map",
            "title": "Demo Technical Roadmap",
            "description": "Durable project map for Demo Technical Roadmap.",
            "body": "## Curated map\n\nMaterially revised reviewed map.",
            "state": "reviewed",
            "reviewed": True,
            "id": "demo",
            "project": "demo",
            "legacy_view": "docs/ai/specs/demo-roadmap-MOC.md",
            "confidence": "high",
            "sensitivity": "internal",
            "producer": {"skill": "speckit-prd", "agent": "fixture"},
            "sources": [{
                "path": roadmap.relative_to(root).as_posix(),
                "section": "complete roadmap",
                "line_start": 1,
                "line_end": 5,
                "sha256": sha256(roadmap),
            }],
        }
        plan = self.plan(
            root,
            "supersede",
            concept_path="projects/demo/roadmap.md",
            replacement=replacement,
        )
        completed, _ = self.apply(root, plan)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        histories = list((root / "docs/ai/knowledge/projects/demo/history").glob("roadmap-*.md"))
        self.assertEqual(len(histories), 1)
        current = root / "docs/ai/knowledge/projects/demo/roadmap.md"
        self.assertIn(
            f'x-speckit-supersedes: "projects/demo/history/{histories[0].name}"',
            current.read_text(encoding="utf-8"),
        )
        _, repaired = run_helper(root, "knowledge-health", "read_only")
        self.assertTrue(repaired["data"]["health"]["profile_healthy"], repaired)
        self.assertIn(
            "historical_source_drift",
            {item["code"] for item in repaired["data"]["health"]["advisories"]},
        )

        roadmap.write_text(
            "# Demo Technical Roadmap\n\n## SPEC-001\n\nSecond reviewed revision.\n",
            encoding="utf-8",
        )
        current.write_text(
            current.read_text(encoding="utf-8").replace(
                "---\n# Demo Technical Roadmap",
                'x-speckit-legacy-related:\n  - "[Runbook](../../runbook.md)"\n---\n# Demo Technical Roadmap',
            ),
            encoding="utf-8",
        )
        replacement["body"] = "## Curated map\n\nSecond reviewed map revision."
        replacement["sources"][0]["sha256"] = sha256(roadmap)
        second = self.plan(
            root,
            "supersede",
            concept_path="projects/demo/roadmap.md",
            replacement=replacement,
        )
        completed, _ = self.apply(root, second)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        histories = list((root / "docs/ai/knowledge/projects/demo/history").glob("roadmap-*.md"))
        self.assertEqual(len(histories), 2)
        latest_history = max(histories, key=lambda path: path.stat().st_mtime_ns)
        self.assertNotIn('  - "[Runbook]', latest_history.read_text(encoding="utf-8"))
        _, repeated = run_helper(root, "knowledge-health", "read_only")
        self.assertTrue(repeated["data"]["health"]["profile_healthy"], repeated)

        archive = self.plan(
            root,
            "archive",
            concept_path="projects/demo/roadmap.md",
            sources=[{
                "path": roadmap.relative_to(root).as_posix(),
                "section": "archived roadmap",
                "sha256": sha256(roadmap),
            }],
        )
        completed, _ = self.apply(root, archive)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        legacy = root / "docs/ai/specs/demo-roadmap-MOC.md"
        self.assertTrue(legacy.is_file())
        self.assertIn('status: "archived"', legacy.read_text(encoding="utf-8"))
        self.assertIn("## Verified sources", current.read_text(encoding="utf-8"))

    def test_scoped_map_promotion_projects_its_compatibility_view(self) -> None:
        root = self.repo("map-promotion")
        roadmap = self.write(
            root,
            "docs/ai/specs/gamma-technical-roadmap.md",
            "# Gamma Technical Roadmap\n\n## GAMMA-001\n\nReviewed behavior.\n",
        )
        candidate = {
            "concept_path": "projects/gamma/roadmap.md",
            "type": "speckit-project-map",
            "title": "Gamma Technical Roadmap",
            "description": "Durable project map for Gamma.",
            "body": "## Curated map\n\nReviewed Gamma map.",
            "state": "reviewed",
            "reviewed": True,
            "id": "gamma",
            "project": "gamma",
            "legacy_view": "docs/ai/specs/gamma-roadmap-MOC.md",
            "producer": {"skill": "speckit-prd"},
            "sources": [{
                "path": roadmap.relative_to(root).as_posix(),
                "section": "complete roadmap",
                "sha256": sha256(roadmap),
            }],
        }
        cross_project = dict(candidate)
        cross_project["legacy_view"] = "docs/ai/specs/beta-roadmap-MOC.md"
        completed, rejected = run_helper(
            root,
            "knowledge-update-plan",
            "read_only",
            {
                "action": "promote",
                "timestamp": FIXED_TIME,
                "scope": "projects/gamma",
                "candidate": cross_project,
            },
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(rejected["diagnostics"][0]["code"], "invalid_input")
        promotion = self.plan(
            root,
            "promote",
            candidate=candidate,
            scope="projects/gamma",
        )
        completed, _ = self.apply(root, promotion)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        legacy = root / "docs/ai/specs/gamma-roadmap-MOC.md"
        self.assertTrue(legacy.is_file())
        self.assertIn(
            'x-speckit-generated-from: "docs/ai/knowledge/projects/gamma/roadmap.md"',
            legacy.read_text(encoding="utf-8"),
        )
        _, report = run_helper(
            root,
            "knowledge-health",
            "read_only",
            {"scope": "projects/gamma"},
        )
        self.assertTrue(report["data"]["health"]["profile_healthy"], report)

    def test_orphan_roadmap_moc_requires_reviewed_source_and_modes_are_preserved(self) -> None:
        root = self.repo("orphan")
        self.write(root, "docs/ai/specs/orphan-roadmap-MOC.md", "# Orphan Map\n")
        completed, body = run_helper(
            root,
            "knowledge-update-plan",
            "read_only",
            {"action": "migrate", "timestamp": FIXED_TIME},
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(body["diagnostics"][0]["code"], "review_required")

        clean = self.repo("modes")
        plan = self.plan(clean, "init")
        completed, _ = self.apply(clean, plan)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        manifest = clean / "docs/ai/knowledge/manifest.json"
        expected_mode = stat.S_IMODE(manifest.stat().st_mode)
        manifest.chmod(0o640)
        manifest.write_bytes(b"invalid")
        repair = self.plan(clean, "rebuild")
        completed, _ = self.apply(clean, repair)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(stat.S_IMODE(manifest.stat().st_mode), 0o640)
        self.assertNotEqual(expected_mode, 0o600)

    def test_claude_codex_lifecycle_parity_requires_actual_use_receipts(self) -> None:
        paired_skills = (
            "grill-me",
            "speckit-archive-cleanup",
            "speckit-autopilot",
            "speckit-coach",
            "speckit-install",
            "speckit-prd",
            "speckit-resolve-pr",
            "speckit-scaffold-spec",
            "speckit-status",
            "speckit-upgrade",
        )
        lifecycle_terms = {
            "knowledge-health",
            "knowledge-search",
            "knowledge-update-plan",
            "knowledge-update-apply",
            "knowledge_use_receipt",
            "knowledge_candidates",
        }
        for skill in paired_skills:
            claude = (PLUGIN_ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            codex = (PLUGIN_ROOT / "codex-skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("knowledge-lifecycle.md", claude, skill)
            self.assertIn("knowledge-lifecycle.md", codex, skill)
            self.assertEqual(
                {term for term in lifecycle_terms if term in claude},
                {term for term in lifecycle_terms if term in codex},
                skill,
            )

        for skill in ("grill-me", "speckit-autopilot", "speckit-prd", "speckit-resolve-pr", "speckit-scaffold-spec"):
            for root_name in ("skills", "codex-skills"):
                text = (PLUGIN_ROOT / root_name / skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("knowledge-health", text, f"{root_name}/{skill}")
                self.assertIn("knowledge-search", text, f"{root_name}/{skill}")
                self.assertIn("knowledge_use_receipt", text, f"{root_name}/{skill}")

        lifecycle = (
            PLUGIN_ROOT / "skills" / "speckit-coach" / "references" / "knowledge-lifecycle.md"
        ).read_text(encoding="utf-8")
        lifecycle_prose = " ".join(lifecycle.split())
        self.assertIn("decision or output that consumed them", lifecycle_prose)
        self.assertIn("A receipt proves downstream use", lifecycle_prose)
        self.assertIn("Bundle presence", lifecycle_prose)

        receipt_blocks = re.findall(r"```json\n(.*?)\n```", lifecycle, re.DOTALL)
        self.assertGreaterEqual(len(receipt_blocks), 5)
        empty_receipt = json.loads(receipt_blocks[-1])

        receipt_schema = json.loads(
            (
                PLUGIN_ROOT
                / "skills"
                / "speckit-autopilot"
                / "contracts"
                / "knowledge-use-receipt.schema.json"
            ).read_text(encoding="utf-8")
        )
        required_receipt_fields = set(receipt_schema["required"])
        self.assertEqual(set(empty_receipt), required_receipt_fields)
        self.assertEqual(
            empty_receipt["snapshot_id"],
            "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )
        self.assertEqual(empty_receipt["selected_concepts"], [])
        self.assertEqual(empty_receipt["verified_sources"], [])
        self.assertTrue(
            {
                "snapshot_id",
                "query",
                "selected_concepts",
                "verified_sources",
                "purpose",
                "result",
            }.issubset(required_receipt_fields)
        )
        if "producer" in required_receipt_fields:
            producer = receipt_schema["properties"]["producer"]
            self.assertIn("skill", producer["required"])
            self.assertIn("agent", producer["properties"])
        else:
            self.assertIn("skill", required_receipt_fields)
            self.assertIn("agent", receipt_schema["properties"])

        candidate_files = [*sorted((PLUGIN_ROOT / "agents").glob("*.md"))]
        candidate_files.extend(sorted((PLUGIN_ROOT / "codex-agents").glob("*.toml")))
        checked = 0
        for path in candidate_files:
            text = path.read_text(encoding="utf-8")
            if "## Knowledge Candidates" not in text:
                continue
            checked += 1
            section = text.rsplit("## Knowledge Candidates", 1)[1]
            for token in (
                "`concept_path`",
                "`type`",
                "`title`",
                "`description`",
                "`body`",
                "`state: proposed`",
                "`reviewed: false`",
                "`sources`",
                "`producer`",
            ):
                self.assertIn(token, section, f"{path.name}: {token}")
            self.assertNotIn("`summary`", section, path.name)
            self.assertNotIn("`scope`", section, path.name)
        self.assertGreaterEqual(checked, 10)

        for relative in (
            "tests/speckit-pro/layer3-functional/evals/speckit-scaffold-spec-evals.json",
            "tests/speckit-pro/layer3-functional/codex-evals/speckit-scaffold-spec-evals.json",
        ):
            data = json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))
            knowledge_eval = next(
                case for case in data["evals"] if "SPEC-200" in case["prompt"]
            )
            expectations = " ".join(knowledge_eval["expectations"])
            self.assertIn("installed speckit_pro_runner", expectations)
            self.assertIn("describing the calls without invoking them does not pass", expectations)
            self.assertIn("knowledge-use-receipt.schema.json", expectations)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(KnowledgeLayerTests)
    raise SystemExit(run_counted(suite, label="test-knowledge-layer"))
