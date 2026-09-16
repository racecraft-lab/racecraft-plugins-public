#!/usr/bin/env python3
"""Focused tests for controller-owned pinned Spec Kit integration staging."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
sys.path.insert(0, str(TEST_ROOT / "lib"))

import native_eval_toolchain as toolchain  # noqa: E402
import native_eval_upstream as upstream  # noqa: E402
from test_result import run_counted  # noqa: E402


class NativeEvalUpstreamTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.launcher = self.root / "bin" / "specify"
        self.launcher.parent.mkdir()
        self.launcher.write_text("fixture\n", encoding="utf-8")
        os.chmod(self.launcher, 0o555)
        receipt = {
            "version": "specify 1.0.1",
            "interpreter": {"resolved_path": sys.executable},
            "executable": {"resolved_path": str(self.launcher)},
            "site_packages": str(self.root),
            "tool_tree": "sha256:tool",
            "python_tree": "sha256:python",
            "distribution": {
                "name": "specify-cli",
                "version": "1.0.1",
                "metadata_sha256": "a" * 64,
                "direct_url_sha256": "b" * 64,
                "direct_url": {
                    "url": upstream.PINNED_URL,
                    "vcs_info": {
                        "vcs": "git",
                        "commit_id": upstream.PINNED_REVISION,
                        "requested_revision": "v1.0.1",
                    },
                },
            },
        }
        self.toolchain = toolchain.PreparedNativeToolchain(
            workspace=self.workspace,
            launcher_dir=self.launcher.parent,
            launchers={"specify": self.launcher},
            path_entries=(self.launcher.parent,),
            environment={
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONNOUSERSITE": "1",
                "PYTHONSAFEPATH": "1",
            },
            readonly_roots=(),
            runtime_identity={"tools": {"specify": receipt}},
        )
        self.verify_patch = mock.patch.object(toolchain, "verify_native_toolchain")
        self.verify_patch.start()
        self.addCleanup(self.verify_patch.stop)

    def _runner(self, expected_host: str):
        def run(command: list[str], cwd: Path, environment):
            self.assertEqual(command[-5:], ["integration", "install", expected_host, "--script", "py"])
            self.assertEqual(environment["HOME"], str(cwd / ".controller-home"))
            self.assertNotIn("SSH_AUTH_SOCK", environment)
            self._write_generated(cwd, expected_host)
            return subprocess.CompletedProcess(command, 0, b"installed\n", b"")
        return run

    def _write_generated(self, root: Path, host: str) -> None:
        skill_root = upstream._HOST_SKILL_ROOTS[host]
        files: dict[str, bytes] = {}
        for name in upstream._SKILLS:
            files[f"{skill_root.as_posix()}/{name}/SKILL.md"] = (
                f"---\nname: {name}\ndescription: generated for {host}\n---\n"
            ).encode()
        for relative in upstream._SHARED_FILES:
            files[relative] = f"shared:{relative}\n".encode()
        files[".specify/integration.json"] = json.dumps({
            "version": "1.0.1",
            "integration_state_schema": 1,
            "installed_integrations": [host],
            "integration_settings": {host: {"script": "py", "invoke_separator": "-"}},
            "integration": host,
            "default_integration": host,
        }).encode()
        files[".specify/init-options.json"] = json.dumps({
            "ai": host, "ai_skills": True, "integration": host,
            "script": "py", "speckit_version": "1.0.1",
        }).encode()
        for relative, body in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            os.chmod(path, 0o755 if "/scripts/" in relative else 0o644)
        manifests = {
            f".specify/integrations/{host}.manifest.json": (host, {
                path: hashlib.sha256(body).hexdigest()
                for path, body in files.items() if path.startswith(f"{skill_root.as_posix()}/")
            }),
            ".specify/integrations/speckit.manifest.json": ("speckit", {
                path: hashlib.sha256(files[path]).hexdigest() for path in upstream._SHARED_FILES
            }),
        }
        for relative, (integration, entries) in manifests.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({
                "integration": integration,
                "version": "1.0.1",
                "installed_at": "2026-09-15T12:34:56+00:00",
                "files": entries,
            }), encoding="utf-8")

    def test_generates_and_stages_exact_host_layout_with_stable_semantic_identity(self) -> None:
        for host, skill_prefix in (("claude", ".claude/skills"), ("codex", ".agents/skills")):
            with self.subTest(host=host):
                controller = self.root / f"controller-{host}"
                controller.mkdir()
                prepared = upstream.prepare_upstream_integration(
                    controller, host=host, toolchain=self.toolchain, runner=self._runner(host),
                )
                self.assertTrue(
                    prepared.runtime_identity["generator"]["python_socket_api_blockade"]
                )
                self.assertFalse(
                    prepared.runtime_identity["generator"]["kernel_network_isolation"]
                )
                self.assertEqual(set(upstream.skill_witnesses(prepared.runtime_identity)), upstream._SKILLS)
                self.assertTrue(all(
                    value["path"].startswith(skill_prefix + "/")
                    for value in upstream.skill_witnesses(prepared.runtime_identity).values()
                ))
                destination = self.root / f"destination-{host}"
                destination.mkdir()
                upstream.stage_upstream_integration(prepared, destination)
                upstream.verify_staged_upstream(prepared.runtime_identity, destination)
                self.assertTrue((destination / skill_prefix / "speckit-specify" / "SKILL.md").is_file())
                self.assertTrue((destination / ".specify/scripts/python/check_prerequisites.py").is_file())

                manifest = prepared.project_root / f".specify/integrations/{host}.manifest.json"
                first_identity = json.loads(json.dumps(prepared.runtime_identity))
                data = json.loads(manifest.read_text(encoding="utf-8"))
                data["installed_at"] = "2026-09-15T13:00:00+00:00"
                manifest.write_text(json.dumps(data), encoding="utf-8")
                upstream.verify_upstream_integration(prepared)
                self.assertEqual(prepared.runtime_identity, first_identity)

    def test_rejects_wrong_layout_collision_links_tamper_and_unpinned_source(self) -> None:
        controller = self.root / "controller"
        controller.mkdir()
        prepared = upstream.prepare_upstream_integration(
            controller, host="codex", toolchain=self.toolchain, runner=self._runner("codex"),
        )
        collision = self.root / "collision"
        (collision / ".agents/skills/speckit-plan").mkdir(parents=True)
        (collision / ".agents/skills/speckit-plan/SKILL.md").write_text("owned\n", encoding="utf-8")
        with self.assertRaisesRegex(upstream.UpstreamStageError, "collides"):
            upstream.stage_upstream_integration(prepared, collision)

        target = prepared.project_root / ".agents/skills/speckit-plan/SKILL.md"
        target.write_text("tampered\n", encoding="utf-8")
        with self.assertRaisesRegex(upstream.UpstreamStageError, "manifest digest|changed"):
            upstream.verify_upstream_integration(prepared)

        other = self.root / "wrong-layout"
        other.mkdir()
        self._write_generated(other, "claude")
        with self.assertRaisesRegex(upstream.UpstreamStageError, "incomplete|undeclared"):
            upstream._output_identity(other, "codex")

        linked = self.root / "linked"
        linked.mkdir()
        self._write_generated(linked, "codex")
        skill = linked / ".agents/skills/speckit-tasks/SKILL.md"
        skill.unlink()
        skill.symlink_to(linked / ".specify/templates/spec-template.md")
        with self.assertRaisesRegex(upstream.UpstreamStageError, "unsafe"):
            upstream._output_identity(linked, "codex")

        invalid = json.loads(json.dumps(self.toolchain.runtime_identity))
        invalid["tools"]["specify"]["distribution"]["direct_url"]["vcs_info"]["commit_id"] = "0" * 40
        bad_toolchain = toolchain.PreparedNativeToolchain(
            **{**self.toolchain.__dict__, "runtime_identity": invalid}
        )
        another = self.root / "unpinned"
        another.mkdir()
        with self.assertRaisesRegex(upstream.UpstreamStageError, "pinned"):
            upstream.prepare_upstream_integration(
                another, host="codex", toolchain=bad_toolchain, runner=self._runner("codex"),
            )

    def test_staging_rejects_ancestor_symlink_without_touching_external_directory(self) -> None:
        controller = self.root / "symlink-controller"
        controller.mkdir()
        prepared = upstream.prepare_upstream_integration(
            controller, host="codex", toolchain=self.toolchain, runner=self._runner("codex"),
        )
        destination = self.root / "symlink-destination"
        destination.mkdir()
        external = self.root / "external"
        for name in upstream._SKILLS:
            (external / "skills" / name).mkdir(parents=True, exist_ok=True)
        (destination / ".agents").symlink_to(external, target_is_directory=True)
        before = sorted(path.relative_to(external).as_posix() for path in external.rglob("*"))

        with self.assertRaisesRegex(upstream.UpstreamStageError, "parent is unsafe"):
            upstream.stage_upstream_integration(prepared, destination)

        self.assertEqual(
            sorted(path.relative_to(external).as_posix() for path in external.rglob("*")), before,
        )
        self.assertFalse(any(path.is_file() for path in external.rglob("*")))

    def test_retained_manifest_rejects_duplicate_keys_and_nonstandard_constants(self) -> None:
        controller = self.root / "manifest-controller"
        controller.mkdir()
        prepared = upstream.prepare_upstream_integration(
            controller, host="claude", toolchain=self.toolchain, runner=self._runner("claude"),
        )
        destination = self.root / "manifest-destination"
        destination.mkdir()
        upstream.stage_upstream_integration(prepared, destination)
        manifest = destination / ".specify/integrations/claude.manifest.json"
        valid = manifest.read_text(encoding="utf-8")
        duplicate = valid.replace(
            '"integration": "claude"',
            '"integration": "wrong", "integration": "claude"',
            1,
        )
        manifest.write_text(duplicate, encoding="utf-8")
        with self.assertRaisesRegex(upstream.UpstreamStageError, "duplicate JSON key"):
            upstream.verify_staged_payloads(
                prepared.runtime_identity, lambda relative: (destination / relative).read_bytes(),
            )

        manifest.write_text(valid.replace('"version": "1.0.1"', '"version": NaN', 1), encoding="utf-8")
        with self.assertRaisesRegex(upstream.UpstreamStageError, "nonstandard JSON constant"):
            upstream.verify_staged_payloads(
                prepared.runtime_identity, lambda relative: (destination / relative).read_bytes(),
            )


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeEvalUpstreamTests)
    raise SystemExit(run_counted(suite, label="test-native-eval-upstream"))
