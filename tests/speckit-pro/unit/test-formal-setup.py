#!/usr/bin/env python3
"""Tool setup recovery and explicit installed-consumer qualification."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
PLUGIN = ROOT / "speckit-pro"
sys.path.insert(0, str(ROOT / "tests/speckit-pro/lib"))
from test_result import run_counted

SCRIPTS = "skills/speckit-coach/scripts"
spec = importlib.util.spec_from_file_location("formal_setup", PLUGIN / SCRIPTS / "setup-formal-tools.py")
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)
CACHE: Path | None = None


class SetupTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.base = self.root / ".specify/tools/formal"

    def test_preview_never_installs_or_writes(self) -> None:
        with patch.object(setup, "download", side_effect=AssertionError("no download")), patch.object(setup.subprocess, "run", side_effect=AssertionError("no process")):
            result = setup.setup(self.root, ["apalache", "tlc", "quint"], False)
        self.assertEqual("preview", result["verdict"])
        self.assertFalse(result["writes_state"])
        self.assertEqual([], list(self.root.iterdir()))

    def test_missing_cache_does_not_fall_back_to_network(self) -> None:
        with patch.object(setup, "download", side_effect=AssertionError("no download")), self.assertRaises(OSError):
            setup.setup(self.root, ["tlc"], True, self.root)
        self.assertFalse((self.base / "tlc-1.7.4").exists())

    def test_mismatched_download_cannot_create_a_tool(self) -> None:
        (self.root / setup.TOOLS["tlc"]["asset"]).write_bytes(b"wrong release")
        with self.assertRaisesRegex(ValueError, "checksum"):
            setup.setup(self.root, ["tlc"], True, self.root)
        self.assertFalse((self.base / "tlc-1.7.4").exists())

    def test_existing_modified_install_is_preserved(self) -> None:
        target = self.base / "tlc-1.7.4/tla2tools.jar"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"operator file")
        with self.assertRaisesRegex(ValueError, "Existing formal tool"):
            setup.setup(self.root, ["tlc"], True)
        self.assertEqual(b"operator file", target.read_bytes())

    def test_outside_symlinks_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as elsewhere:
            outside = Path(elsewhere).resolve()
            self.base.mkdir(parents=True)
            for name in ("tlc-1.7.4", "quint-0.32.0", ".gitignore"):
                with self.subTest(name=name):
                    link = self.base / name
                    link.unlink(missing_ok=True)
                    link.symlink_to(outside)
                    with self.assertRaises(ValueError):
                        setup.setup(self.root, ["quint" if name.startswith("quint") else "tlc"], True)
                    link.unlink()
            self.assertEqual([], list(outside.iterdir()))

    def test_interrupted_quint_install_requires_inspection(self) -> None:
        (self.base / "quint-0.32.0").mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "interrupted"):
            setup.setup(self.root, ["quint"], True)

    def test_quint_identity_accepts_relative_root_with_internal_links(self) -> None:
        (self.root / "compiler.js").write_text("compiler bytes")
        (self.root / "quint").symlink_to("compiler.js")
        relative = Path(os.path.relpath(self.root, Path.cwd()))
        self.assertEqual(setup.tree_digest(self.root), setup.tree_digest(relative))

    def test_archive_extracts_only_regular_pinned_member(self) -> None:
        archive_path = self.root / "tool.tgz"
        for kind in (tarfile.REGTYPE, tarfile.SYMTYPE):
            with tarfile.open(archive_path, "w:gz") as archive:
                member = tarfile.TarInfo("release/lib/tool.jar")
                member.type = kind
                member.size = 3 if kind == tarfile.REGTYPE else 0
                member.linkname = "../../outside"
                archive.addfile(member, io.BytesIO(b"jar") if member.size else None)
                ignored = tarfile.TarInfo("../../unexpected")
                archive.addfile(ignored)
            jar = self.root / "verified.jar"
            tool = {"download_sha256": setup.digest(archive_path), "member": member.name, "sha256": hashlib.sha256(b"jar").hexdigest()}
            if kind == tarfile.REGTYPE:
                setup.materialize_jar(archive_path, jar, tool)
                self.assertEqual(b"jar", jar.read_bytes())
                jar.unlink()
            else:
                with self.assertRaisesRegex(ValueError, "regular checker JAR"):
                    setup.materialize_jar(archive_path, jar, tool)


class NativeSetupTests(unittest.TestCase):
    def test_install_reuse_and_installed_consumer_checkpoints(self) -> None:
        with tempfile.TemporaryDirectory(prefix="formal-consumer-") as temporary:
            root = Path(temporary).resolve()
            old = root / ".specify/tools/formal/tlc-older/operator.txt"
            old.parent.mkdir(parents=True)
            old.write_text("preserve previous release")
            selected = ["apalache", "tlc", "quint"]
            result = setup.setup(root, selected, True, CACHE)
            self.assertEqual(result["tools"], setup.setup(root, selected, True, CACHE)["tools"])
            self.assertEqual("preserve previous release", old.read_text())
            shutil.copytree(PLUGIN / "skills/speckit-coach/examples/formal/counter", root / "formal/counter")
            catalog = json.loads((root / "formal/counter/catalog.json").read_text())
            catalog["tools"] = result["tools"]
            catalog["models"]["counter"]["implementation_inputs"] = ["counter.py"]
            (root / "counter.py").write_text("count = min(count + 1, 2)\n")
            (root / ".specify/formal-methods.json").write_text(json.dumps(catalog))
            (root / "spec.md").write_text("The count stays within zero and two.\n")
            (root / "plan.md").write_text("Increment until the limit, then stay.\n")
            selection = {"schema_version": "1.0", "status": "enabled", "rationale": "Qualification", "models": [{"id": "counter", "behavior": "Counter bound", "origin": "existing", "evidence": "model"}]}
            for name, payload in (("source", PLUGIN), ("claude", ROOT / "dist/claude/speckit-pro"), ("codex", ROOT / "dist/codex/speckit-pro")):
                with self.subTest(payload=name):
                    installed = root / "installed" / name
                    shutil.copytree(payload, installed)
                    if name == "codex":
                        env = setup.runtime_environment()
                        env["PYTHONPATH"] = str(installed)
                        request = {"schema_version": "1.0", "helper_id": "install-codex-agents", "operation": "install-codex-agents", "mode": "apply",
                                   "inputs": {"repo_root": str(root), "destination": ".codex/agents", "model": "gpt-5.6-sol"}}
                        materialized = subprocess.run([sys.executable, "-m", "speckit_pro_runner"], input=json.dumps(request), env=env, cwd=root,
                                                      capture_output=True, text=True, check=False, timeout=60)
                        self.assertEqual(0, materialized.returncode, materialized.stdout + materialized.stderr)
                        self.assertIn("formal-model-author", (root / ".codex/agents/formal-model-author.toml").read_text())
                    wrapper = installed / SCRIPTS / "run-formal-ci.py"
                    workflow = root / "workflow.md"
                    workflow.write_text("# Legacy workflow\n")
                    command = [sys.executable, str(wrapper), "--repo-root", str(root), "--workflow", "workflow.md", "--spec", "spec.md", "--plan", "plan.md", "--checkpoint", "plan"]
                    disabled = subprocess.run(command, cwd=root.parent, capture_output=True, text=True, check=False, timeout=60)
                    self.assertEqual(0, disabled.returncode, disabled.stdout + disabled.stderr)
                    self.assertEqual("disabled", json.loads(disabled.stdout)["data"]["verdict"])
                    workflow.write_text("# Workflow\n\n## Formal Methods\n\n```json\n" + json.dumps(selection) + "\n```\n")
                    for checkpoint in ("plan", "final", "post"):
                        command[-1] = checkpoint
                        checked = subprocess.run(command, cwd=root.parent, capture_output=True, text=True, check=False, timeout=120)
                        self.assertEqual(0, checked.returncode, checked.stdout + checked.stderr)
                        self.assertEqual("pass", json.loads(checked.stdout)["data"]["verdict"])
                    (root / "formal/counter/Counter.tla").write_text((root / "formal/counter/Counter.tla").read_text().replace("count <= Limit", "count < Limit"))
                    failed = subprocess.run(command, cwd=root.parent, capture_output=True, text=True, check=False, timeout=120)
                    self.assertNotEqual(0, failed.returncode, failed.stdout)
                    self.assertEqual("violation", json.loads(failed.stdout)["data"]["verdict"])
                    shutil.copyfile(PLUGIN / "skills/speckit-coach/examples/formal/counter/Counter.tla", root / "formal/counter/Counter.tla")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-setup", action="store_true", help="Authorize isolated pinned tool installation and real checks from source and installed payloads")
    parser.add_argument("--download-cache", type=Path)
    args = parser.parse_args()
    CACHE = args.download_cache
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SetupTests)
    if args.native_setup:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(NativeSetupTests))
    raise SystemExit(run_counted(suite, label="test-formal-setup"))
