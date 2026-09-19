#!/usr/bin/env python3
"""Focused deterministic tests for canonical native-evaluation runtime staging."""

from __future__ import annotations

import builtins
import copy
from dataclasses import replace
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
import threading
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
for import_root in (TEST_ROOT / "lib", PLUGIN_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import native_eval_runtime as runtime  # noqa: E402
from native_eval_runtime import (  # noqa: E402
    RuntimeStageError,
    _runtime_identity,
    stage_codex_runtime,
)
from test_result import run_counted  # noqa: E402
from speckit_pro_runner.agent_inventory import (  # noqa: E402
    CODEX_OPTIONAL_AGENT_NAMES,
    CODEX_REQUIRED_AGENT_NAMES,
)


REQUIRED_AGENTS = CODEX_REQUIRED_AGENT_NAMES
OPTIONAL_HELPER = CODEX_OPTIONAL_AGENT_NAMES[0]
DEFAULT_AGENTS = tuple(sorted((*REQUIRED_AGENTS, OPTIONAL_HELPER)))


def tree_snapshot(root: Path) -> dict[str, object]:
    if not root.exists() and not root.is_symlink():
        return {"exists": False, "entries": {}}
    entries: dict[str, dict[str, object]] = {}
    for path in (root, *sorted(root.rglob("*"))):
        metadata = path.lstat()
        mode = metadata.st_mode
        if stat.S_ISDIR(mode):
            kind = "directory"
        elif stat.S_ISREG(mode):
            kind = "file"
        elif stat.S_ISLNK(mode):
            kind = "symlink"
        else:
            kind = "other"
        record: dict[str, object] = {
            "kind": kind,
            "mode": stat.S_IMODE(mode),
            "mtime_ns": metadata.st_mtime_ns,
            "size": metadata.st_size,
        }
        if kind == "file":
            record["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        elif kind == "symlink":
            record["target"] = os.readlink(path)
        relative = "." if path == root else path.relative_to(root).as_posix()
        entries[relative] = record
    return {"exists": True, "entries": entries}


class NativeEvalRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.build_root = self.root / "build"

    def stage(
        self,
        *,
        repo_root: Path = REPO_ROOT,
        build_name: str = "build",
        workspace_name: str = "workspace",
    ):
        workspace = self.root / workspace_name
        workspace.mkdir(exist_ok=True)
        return stage_codex_runtime(repo_root, self.root / build_name, workspace)

    def fixture_repo(self, name: str) -> Path:
        target = self.root / name
        shutil.copytree(
            REPO_ROOT / "speckit-pro",
            target / "speckit-pro",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        shutil.copy2(REPO_ROOT / "LICENSE", target / "LICENSE")
        return target

    def test_stages_complete_payload_base_overlay_and_controlled_pythonpath(self) -> None:
        result = self.stage()

        self.assertEqual(result.payload_root, self.workspace / ".agents")
        self.assertEqual(result.agent_root, self.workspace / ".codex" / "agents")
        self.assertEqual(result.pythonpath, str(self.workspace / ".agents"))
        self.assertEqual(result.proof["pythonpath_relative"], ".agents")
        self.assertTrue((result.payload_root / ".codex-plugin" / "plugin.json").is_file())
        self.assertTrue((result.payload_root / "speckit_pro_runner").is_dir())

        base_reference = Path("skills/speckit-autopilot/contracts/autonomy-boundary.schema.json")
        overlay_reference = Path("skills/install/agents/openai.yaml")
        self.assertEqual(
            (result.payload_root / base_reference).read_bytes(),
            (REPO_ROOT / "speckit-pro" / "skills" / base_reference.relative_to("skills")).read_bytes(),
        )
        self.assertEqual(
            (result.payload_root / overlay_reference).read_bytes(),
            (REPO_ROOT / "speckit-pro" / "codex-skills" / overlay_reference.relative_to("skills")).read_bytes(),
        )
        proof_paths = {item["path"] for item in result.proof["payload"]["files"]}
        self.assertIn(base_reference.as_posix(), proof_paths)
        self.assertIn(overlay_reference.as_posix(), proof_paths)

    def test_materializes_exactly_default_agents_and_retains_optional_activation_state(self) -> None:
        result = self.stage()
        installed = sorted(path.name for path in result.agent_root.glob("*.toml"))
        self.assertEqual(installed, [f"{name}.toml" for name in DEFAULT_AGENTS])
        self.assertEqual(len(result.proof["materializations"]), len(DEFAULT_AGENTS))
        self.assertEqual(
            [item["name"] for item in result.proof["materializations"]],
            list(DEFAULT_AGENTS),
        )
        for name in DEFAULT_AGENTS:
            source = REPO_ROOT / "speckit-pro" / "codex-agents" / f"{name}.toml"
            destination = result.agent_root / f"{name}.toml"
            self.assertEqual(destination.read_bytes(), source.read_bytes())

        helper_source = result.payload_root / "codex-agents" / f"{OPTIONAL_HELPER}.toml"
        self.assertTrue(helper_source.is_file())
        self.assertTrue((result.agent_root / f"{OPTIONAL_HELPER}.toml").is_file())
        self.assertEqual(
            result.proof["optional_helper"],
            {
                "name": OPTIONAL_HELPER,
                "source_path": f".agents/codex-agents/{OPTIONAL_HELPER}.toml",
                "activated": False,
            },
        )

    def test_staged_default_runtime_passes_exact_scaffold_agent_dry_run(self) -> None:
        result = self.stage()
        request = {
            "schema_version": "1.0",
            "request_id": "scaffold-spec-031-agent-check",
            "helper_id": "install-codex-agents",
            "operation": "install-codex-agents",
            "mode": "dry_run",
            "inputs": {
                "destination": ".codex/agents",
                "model": "gpt-5.6-sol",
            },
        }
        environment = dict(os.environ)
        environment["PYTHONPATH"] = result.pythonpath
        completed = subprocess.run(
            [sys.executable, "-m", "speckit_pro_runner"],
            cwd=self.workspace,
            env=environment,
            input=json.dumps(request),
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        response = json.loads(completed.stdout)
        self.assertEqual(response["status"], "ok")
        mutation = response["data"]["mutation"]
        self.assertEqual(mutation["mutation_status"], "no_op")
        self.assertEqual(mutation["planned_operations"], [])
        self.assertEqual(len(mutation["no_op_operations"]), len(DEFAULT_AGENTS))
        self.assertEqual(
            sorted(Path(item["target"]).name for item in mutation["no_op_operations"]),
            [f"{name}.toml" for name in DEFAULT_AGENTS],
        )

    def test_proof_binds_payload_roster_and_each_materialization(self) -> None:
        result = self.stage()
        roster = result.proof["roster"]
        self.assertEqual(len(roster["files"]), len(DEFAULT_AGENTS))
        self.assertEqual(
            [record["name"] for record in roster["files"]],
            sorted([f"{name}.toml" for name in REQUIRED_AGENTS] + [f"{OPTIONAL_HELPER}.toml"]),
        )
        self.assertTrue(roster["source_roster_id"].startswith("sha256:"))
        self.assertTrue(result.proof["payload"]["tree_sha256"].startswith("sha256:"))
        self.assertTrue(result.runtime_identity.startswith("sha256:"))
        for record in result.proof["materializations"]:
            self.assertTrue(record["materialization_id"].startswith("sha256:"))
            self.assertTrue(record["destination_bytes_digest"].startswith("sha256:"))
            self.assertTrue(record["non_route_fields_unchanged"])

    def test_existing_destinations_fail_before_building_or_overwriting(self) -> None:
        cases = (
            ("payload", Path(".agents") / "keep.txt"),
            ("agents", Path(".codex/agents") / "keep.toml"),
        )
        for label, relative in cases:
            with self.subTest(destination=label):
                workspace = self.root / f"workspace-{label}"
                existing = workspace / relative
                existing.parent.mkdir(parents=True)
                existing.write_text("keep", encoding="utf-8")
                build = self.root / f"build-{label}"
                with self.assertRaisesRegex(RuntimeStageError, "destination already exists"):
                    stage_codex_runtime(REPO_ROOT, build, workspace)
                self.assertEqual(existing.read_text(encoding="utf-8"), "keep")
                self.assertFalse(build.exists())

    def test_rejects_nonisolated_build_roots_before_product_build(self) -> None:
        apis = runtime._load_product_apis()
        builder = mock.Mock(side_effect=AssertionError("builder must not run for an invalid root"))
        with mock.patch.object(runtime, "_load_product_apis", return_value=replace(apis, build_payloads=builder)):
            self.build_root.mkdir()
            with self.assertRaisesRegex(RuntimeStageError, "new isolated path"):
                stage_codex_runtime(REPO_ROOT, self.build_root, self.workspace)
            nested_workspace = self.root / "nested-workspace"
            nested_workspace.mkdir()
            with self.assertRaisesRegex(RuntimeStageError, "must be disjoint"):
                stage_codex_runtime(REPO_ROOT, nested_workspace / "build", nested_workspace)
            with self.assertRaisesRegex(RuntimeStageError, "source or dist"):
                stage_codex_runtime(REPO_ROOT, REPO_ROOT / "dist", self.workspace)
        builder.assert_not_called()

    def test_rejects_build_and_workspace_descendants_of_source_or_dist(self) -> None:
        fixture = self.fixture_repo("repo-protected")
        (fixture / "dist").mkdir()
        apis = runtime._load_product_apis()
        builder = mock.Mock(side_effect=AssertionError("builder must not run inside a protected root"))
        cases = (
            ("build-source", fixture / "speckit-pro/runtime-build", self.root / "workspace-build-source"),
            ("build-dist", fixture / "dist/runtime-build", self.root / "workspace-build-dist"),
            ("workspace-source", self.root / "build-workspace-source", fixture / "speckit-pro/runtime-workspace"),
            ("workspace-dist", self.root / "build-workspace-dist", fixture / "dist/runtime-workspace"),
        )
        with mock.patch.object(runtime, "_load_product_apis", return_value=replace(apis, build_payloads=builder)):
            for label, build, workspace in cases:
                with self.subTest(boundary=label):
                    workspace.mkdir(parents=True)
                    with self.assertRaisesRegex(RuntimeStageError, "inside plugin source or dist"):
                        stage_codex_runtime(fixture, build, workspace)
                    self.assertFalse(build.exists())
        builder.assert_not_called()

    def test_allows_isolated_sibling_output_outside_source_and_dist(self) -> None:
        fixture = self.fixture_repo("repo-sibling-output")
        output = fixture / ".native-eval-output"
        workspace = output / "workspace"
        workspace.mkdir(parents=True)
        result = stage_codex_runtime(fixture, output / "build", workspace)
        self.assertEqual(result.payload_root, workspace / ".agents")

    def test_rejects_missing_and_extra_source_roster_members(self) -> None:
        missing = self.fixture_repo("repo-missing")
        (missing / "speckit-pro/codex-agents/analyze-executor.toml").unlink()
        with self.assertRaisesRegex(RuntimeStageError, "incomplete_agent_bundle"):
            self.stage(repo_root=missing, build_name="build-missing", workspace_name="workspace-missing")
        self.assertFalse((self.root / "build-missing").exists())

        extra = self.fixture_repo("repo-extra")
        (extra / "speckit-pro/codex-agents/undeclared.toml").write_text(
            'name = "undeclared"\n', encoding="utf-8"
        )
        with self.assertRaisesRegex(RuntimeStageError, "incomplete_agent_bundle"):
            self.stage(repo_root=extra, build_name="build-extra", workspace_name="workspace-extra")
        self.assertFalse((self.root / "build-extra").exists())

    def test_source_and_agent_mutations_change_runtime_identity(self) -> None:
        baseline_repo = self.fixture_repo("repo-baseline")
        source_repo = self.fixture_repo("repo-source-change")
        agent_repo = self.fixture_repo("repo-agent-change")
        source_path = source_repo / "speckit-pro/skills/speckit-autopilot/contracts/autonomy-boundary.schema.json"
        source_path.write_bytes(source_path.read_bytes() + b"\n")
        agent_path = agent_repo / "speckit-pro/codex-agents/analyze-executor.toml"
        agent_path.write_bytes(agent_path.read_bytes() + b"\n")

        baseline = self.stage(repo_root=baseline_repo, build_name="build-base", workspace_name="workspace-base")
        source_changed = self.stage(
            repo_root=source_repo,
            build_name="build-source",
            workspace_name="workspace-source",
        )
        agent_changed = self.stage(
            repo_root=agent_repo,
            build_name="build-agent",
            workspace_name="workspace-agent",
        )
        same_inputs = self.stage(
            repo_root=baseline_repo,
            build_name="build-same",
            workspace_name="workspace-same",
        )
        self.assertEqual(baseline.runtime_identity, same_inputs.runtime_identity)
        self.assertNotEqual(baseline.runtime_identity, source_changed.runtime_identity)
        self.assertNotEqual(baseline.runtime_identity, agent_changed.runtime_identity)
        self.assertNotEqual(
            baseline.proof["materializations"][0]["materialization_id"],
            agent_changed.proof["materializations"][0]["materialization_id"],
        )

        changed_proof = copy.deepcopy(baseline.proof)
        changed_proof["materializations"][0]["destination_bytes_digest"] = "sha256:" + "0" * 64
        self.assertNotEqual(baseline.runtime_identity, _runtime_identity(changed_proof))

    def test_uses_trusted_builder_code_but_treats_supplied_runner_as_payload_data(self) -> None:
        fixture = self.fixture_repo("repo-untrusted-code")
        staged_module = fixture / "speckit-pro/speckit_pro_runner/gates/payloads.py"
        staged_module.write_text("raise RuntimeError('must not execute fixture code')\n", encoding="utf-8")
        result = self.stage(
            repo_root=fixture,
            build_name="build-untrusted-code",
            workspace_name="workspace-untrusted-code",
        )
        self.assertEqual(
            result.payload_root.joinpath("speckit_pro_runner/gates/payloads.py").read_bytes(),
            staged_module.read_bytes(),
        )

    def test_foreign_product_modules_never_execute_during_trusted_import(self) -> None:
        foreign = self.root / "foreign"
        package = foreign / "speckit_pro_runner"
        (package / "gates").mkdir(parents=True)
        (package / "helpers").mkdir()
        for init in (package / "__init__.py", package / "gates/__init__.py", package / "helpers/__init__.py"):
            init.write_text("", encoding="utf-8")
        marker = self.root / "foreign-executed"
        marker_line = f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n"
        (package / "gates/payloads.py").write_text(marker_line, encoding="utf-8")
        (package / "helpers/install.py").write_text(marker_line, encoding="utf-8")
        (package / "agent_materialization.py").write_text(marker_line, encoding="utf-8")

        for preload in (False, True):
            with self.subTest(preloaded_foreign_parent=preload):
                marker.unlink(missing_ok=True)
                code = textwrap.dedent(
                    f"""
                    import sys
                    from pathlib import Path
                    sys.path.insert(0, {str(TEST_ROOT / 'lib')!r})
                    from native_eval_runtime import PRODUCT_ROOT, RuntimeStageError, _load_product_apis
                    sys.path[:] = [
                        entry for entry in sys.path
                        if Path(entry or '.').resolve() != PRODUCT_ROOT.resolve()
                    ]
                    sys.path.insert(0, {str(foreign)!r})
                    sys.path.append(str(PRODUCT_ROOT))
                    if {preload!r}:
                        import speckit_pro_runner
                    try:
                        _load_product_apis()
                    except RuntimeStageError:
                        outcome = 'rejected'
                    else:
                        outcome = 'loaded'
                    print(outcome)
                    """
                )
                completed = subprocess.run(
                    [sys.executable, "-c", code],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(completed.stdout.strip(), "rejected" if preload else "loaded")
                self.assertFalse(marker.exists())

    def test_concurrent_trusted_imports_serialize_and_restore_sys_path(self) -> None:
        original_path = list(sys.path)
        first_inside_import = threading.Event()
        release_first = threading.Event()
        import_threads: list[int] = []
        results: list[object] = []
        errors: list[BaseException] = []
        real_import = runtime.importlib.import_module

        class ObservedRLock:
            def __init__(self) -> None:
                self.lock = threading.RLock()
                self.guard = threading.Lock()
                self.attempts = 0
                self.second_attempted = threading.Event()

            def __enter__(self):
                with self.guard:
                    self.attempts += 1
                    if self.attempts == 2:
                        self.second_attempted.set()
                self.lock.acquire()
                return self

            def __exit__(self, *_error: object) -> None:
                self.lock.release()

        observed_lock = ObservedRLock()

        def controlled_import(name: str):
            if name == "speckit_pro_runner.gates.payloads":
                import_threads.append(threading.get_ident())
                if len(import_threads) == 1:
                    first_inside_import.set()
                    if not release_first.wait(timeout=5):
                        raise AssertionError("test did not release first import")
            return real_import(name)

        def worker() -> None:
            try:
                results.append(runtime._load_product_apis())
            except BaseException as exc:  # pragma: no cover - asserted below
                errors.append(exc)

        with (
            mock.patch.object(runtime, "_PRODUCT_IMPORT_LOCK", observed_lock),
            mock.patch.object(runtime.importlib, "import_module", side_effect=controlled_import),
        ):
            first = threading.Thread(target=worker)
            first.start()
            self.assertTrue(first_inside_import.wait(timeout=5))
            second = threading.Thread(target=worker)
            second.start()
            try:
                self.assertTrue(observed_lock.second_attempted.wait(timeout=5))
                self.assertEqual(import_threads, [first.ident])
            finally:
                release_first.set()
                first.join(timeout=5)
                second.join(timeout=5)

        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(len(results), 2)
        self.assertEqual(import_threads, [first.ident, second.ident])
        self.assertEqual(sys.path, original_path)

    def test_rejects_source_symlink_and_nonregular_member_before_build(self) -> None:
        outside = self.root / "outside-private-marker.txt"
        outside.write_text("PRIVATE-MARKER-MUST-NOT-BE-COPIED", encoding="utf-8")
        linked = self.fixture_repo("repo-linked-source")
        source = linked / "speckit-pro/codex-skills/install/agents/openai.yaml"
        source.unlink()
        try:
            os.symlink(outside, source)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        with self.assertRaisesRegex(RuntimeStageError, "unsafe source member"):
            self.stage(repo_root=linked, build_name="build-linked", workspace_name="workspace-linked")
        self.assertFalse((self.root / "build-linked").exists())
        self.assertFalse((self.root / "workspace-linked/.agents").exists())

        if not hasattr(os, "mkfifo"):
            return
        nonregular = self.fixture_repo("repo-nonregular-source")
        fifo = nonregular / "speckit-pro/codex-skills/install/blocked.pipe"
        os.mkfifo(fifo)
        with self.assertRaisesRegex(RuntimeStageError, "unsafe source member"):
            self.stage(
                repo_root=nonregular,
                build_name="build-nonregular",
                workspace_name="workspace-nonregular",
            )
        self.assertFalse((self.root / "build-nonregular").exists())

    def test_rejects_license_symlink_and_nonregular_without_reading_external_target(self) -> None:
        outside = self.root / "protected-external-license.txt"
        outside.write_text("PROTECTED-LICENSE-MARKER", encoding="utf-8")
        linked = self.fixture_repo("repo-linked-license")
        license_path = linked / "LICENSE"
        license_path.unlink()
        try:
            os.symlink(outside, license_path)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        external_reads: list[str] = []

        def guarded_open(source: str, real_open: object):
            def guard(file: object, *args: object, **kwargs: object):
                if isinstance(file, (str, os.PathLike)) and Path(file).resolve() == outside.resolve():
                    external_reads.append(source)
                    raise AssertionError("external LICENSE target was read")
                return real_open(file, *args, **kwargs)

            return guard

        guarded_builtin = guarded_open("builtins.open", builtins.open)
        guarded_io = guarded_open("io.open", io.open)
        read_controls = (
            ("builtins.open", lambda: builtins.open(outside, "rb")),
            ("Path.read_bytes", outside.read_bytes),
            ("Path.read_text", outside.read_text),
        )
        with (
            mock.patch("builtins.open", side_effect=guarded_builtin),
            mock.patch("io.open", side_effect=guarded_io),
        ):
            for label, read in read_controls:
                with self.subTest(negative_control=label):
                    with self.assertRaisesRegex(AssertionError, "external LICENSE target was read"):
                        read()
        self.assertEqual(external_reads, ["builtins.open", "io.open", "io.open"])
        external_reads.clear()

        with (
            mock.patch("builtins.open", side_effect=guarded_builtin),
            mock.patch("io.open", side_effect=guarded_io),
        ):
            with self.assertRaisesRegex(RuntimeStageError, "unsafe source member"):
                self.stage(
                    repo_root=linked,
                    build_name="build-linked-license",
                    workspace_name="workspace-linked-license",
                )
        self.assertEqual(external_reads, [])
        self.assertFalse((self.root / "build-linked-license").exists())

        if not hasattr(os, "mkfifo"):
            return
        nonregular = self.fixture_repo("repo-nonregular-license")
        nonregular_license = nonregular / "LICENSE"
        nonregular_license.unlink()
        os.mkfifo(nonregular_license)
        with self.assertRaisesRegex(RuntimeStageError, "unsafe source member"):
            self.stage(
                repo_root=nonregular,
                build_name="build-nonregular-license",
                workspace_name="workspace-nonregular-license",
            )
        self.assertFalse((self.root / "build-nonregular-license").exists())

    def test_staging_never_mutates_checkout_dist_files_directories_or_metadata(self) -> None:
        before = tree_snapshot(REPO_ROOT / "dist")
        self.stage()
        self.assertEqual(tree_snapshot(REPO_ROOT / "dist"), before)

        snapshot_probe = self.root / "snapshot-probe"
        empty = snapshot_probe / "empty"
        empty.mkdir(parents=True)
        probe_before = tree_snapshot(snapshot_probe)
        self.assertIn("empty", probe_before["entries"])
        empty_record = probe_before["entries"]["empty"]
        self.assertEqual(empty_record["kind"], "directory")
        os.chmod(empty, empty_record["mode"] ^ stat.S_IWGRP)
        self.assertNotEqual(tree_snapshot(snapshot_probe), probe_before)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeEvalRuntimeTests)
    raise SystemExit(run_counted(suite, label="test-native-eval-runtime"))
