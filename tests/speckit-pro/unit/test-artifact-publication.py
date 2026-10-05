#!/usr/bin/env python3
"""Artifact publication through the public runner, with filesystem race probes."""

from __future__ import annotations

import json
import os
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests/speckit-pro/lib"))
from test_result import run_counted  # noqa: E402


def publication_probe(plugin: str, attack: str) -> None:
    sys.path.insert(0, plugin)
    # Load capability predicates before replacing the OS boundary.
    from speckit_pro_runner.helpers import registry  # noqa: F401

    original_replace = os.replace
    events = []

    def replace(source, destination, **kwargs):
        directory = Path("artifacts")
        directory.rename("held-artifacts")
        directory.symlink_to("outside", target_is_directory=True)
        try:
            result = original_replace(source, destination, **kwargs)
            events.append({"event": "publish", "anchored": kwargs.get("src_dir_fd") is not None
                           and kwargs.get("dst_dir_fd") is not None})
        finally:
            directory.unlink()
            Path("held-artifacts").rename(directory)
        if attack == "restore-old":
            original_replace(directory / "old.html", directory / "implementation-plan.html")
        return result

    original_open, original_unlink = os.open, os.unlink

    def anchored_boundary(operation, name, args, kwargs):
        directory = Path("artifacts")
        directory.rename("held-artifacts")
        directory.symlink_to("outside", target_is_directory=True)
        try:
            events.append({"event": "read" if operation is original_open else "cleanup",
                           "anchored": kwargs.get("dir_fd") is not None})
            return operation(name, *args, **kwargs)
        finally:
            directory.unlink()
            Path("held-artifacts").rename(directory)

    def opened(name, *args, **kwargs):
        if attack == "read-swap" and name == "implementation-plan.html":
            return anchored_boundary(original_open, name, args, kwargs)
        if attack == "tamper-temp" and str(name).startswith(".implementation-plan.html.tmp-") and not args[0] & os.O_CREAT:
            Path("artifacts", name).write_text("tampered")
        return original_open(name, *args, **kwargs)

    def unlinked(name, *args, **kwargs):
        if attack == "cleanup-swap" and name == "implementation-plan.html":
            return anchored_boundary(original_unlink, name, args, kwargs)
        return original_unlink(name, *args, **kwargs)

    if attack in {"restore-old", "publish-swap"}:
        os.replace = replace
    os.open, os.unlink = opened, unlinked
    sys.argv = sys.argv[:1]
    try:
        runpy.run_module("speckit_pro_runner", run_name="__main__")
    finally:
        Path("probe-events.json").write_text(json.dumps(events), encoding="utf-8")


class PublicationFixture(unittest.TestCase):
    def setUp(self) -> None:
        scratch = ROOT / ".git/scratch"
        scratch.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / ".specify").mkdir()
        (self.root / "plan.md").write_text("## Declared File Operations\n\n- NEW src/new.py\n", encoding="utf-8")
        (self.root / "artifacts").mkdir()
        (self.root / "outside").mkdir()
        self.page = self.root / "artifacts/implementation-plan.html"
        self.page.write_text("untouched original", encoding="utf-8")
        os.link(self.page, self.root / "artifacts/old.html")
        (self.root / "outside/implementation-plan.html").write_text("outside sentinel", encoding="utf-8")

    def publish(self, attack: str = "", plugin: str = "speckit-pro", mode: str = "apply", **inputs: object) -> dict:
        request = {"schema_version": "1.0", "request_id": "artifact-publication-test",
                   "helper_id": "publish-artifact-page", "operation": "publish-artifact-page", "mode": mode,
                   "inputs": {"plan_file": "plan.md", "page_id": "implementation-plan",
                              "rendered_html": "<html><body>finished page</body></html>", **inputs}}
        if inputs.get("action") == "cleanup":
            request["inputs"].pop("rendered_html")
        completed = subprocess.run(
            [sys.executable, str(Path(__file__)), "--probe", str(ROOT / plugin), attack],
            input=json.dumps(request), text=True, capture_output=True, cwd=self.root, check=False, timeout=15,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        result = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, result["exit_code"], result)
        return result


class PublicationRaceTests(PublicationFixture):
    def test_swap_and_restore_rejects_the_untouched_original(self) -> None:
        for plugin in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            with self.subTest(plugin=plugin):
                if not (self.page.parent / "old.html").exists():
                    os.link(self.page, self.page.parent / "old.html")
                result = self.publish("restore-old", plugin)
                self.assertEqual(result["status"], "expected_failure", result)
                self.assertIn("identity", result["diagnostics"][0]["message"])
                self.assertEqual(json.loads((self.root / "probe-events.json").read_text()),
                                 [{"event": "publish", "anchored": True}])
                self.assertEqual(self.page.read_text(), "untouched original")
                self.assertEqual((self.root / "outside/implementation-plan.html").read_text(), "outside sentinel")

    def test_publish_and_final_read_survive_directory_swap(self) -> None:
        for plugin in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            for attack in ("publish-swap", "read-swap"):
                with self.subTest(plugin=plugin, attack=attack):
                    result = self.publish(attack, plugin)
                    self.assertEqual(result["status"], "ok", result)
                    self.assertEqual(result["data"]["verified_html"], self.page.read_text())
                    self.assertEqual(result["data"]["outcome"], "generated")
                    self.assertTrue(all(event["anchored"] for event in json.loads(
                        (self.root / "probe-events.json").read_text())))
                    self.assertEqual((self.root / "outside/implementation-plan.html").read_text(), "outside sentinel")

    def test_closed_temporary_tampering_is_rejected(self) -> None:
        result = self.publish("tamper-temp")
        self.assertEqual(result["status"], "expected_failure", result)
        self.assertEqual(self.page.read_text(), "untouched original")
        self.assertEqual(list(self.page.parent.glob(".*.tmp-*")), [])

    def test_cleanup_swap_never_removes_outside_file(self) -> None:
        result = self.publish("cleanup-swap", action="cleanup")
        self.assertEqual(result["status"], "ok", result)
        self.assertFalse(self.page.exists())
        self.assertEqual((self.root / "outside/implementation-plan.html").read_text(), "outside sentinel")
        self.assertEqual(json.loads((self.root / "probe-events.json").read_text()),
                         [{"event": "cleanup", "anchored": True}])

    def test_cleanup_removes_only_selected_page_and_owned_temporary_namespace(self) -> None:
        owned = self.root / ("artifacts/.implementation-plan.html.tmp-42-" + "a" * 32)
        owned.write_text("interrupted temporary", encoding="utf-8")
        foreign = self.root / "artifacts/.implementation-plan.html.tmp-foreign"
        foreign.write_text("foreign temporary", encoding="utf-8")
        result = self.publish(action="cleanup")
        self.assertEqual(result["status"], "ok", result)
        self.assertFalse(self.page.exists())
        self.assertFalse(owned.exists())
        self.assertTrue(foreign.exists())
        self.assertEqual(result["data"]["removed_temporaries"], 1)


class PublicationInputTests(PublicationFixture):
    def test_dry_run_and_invalid_inputs_leave_original_untouched(self) -> None:
        self.assertEqual(self.publish(mode="dry_run")["status"], "ok")
        for inputs in ({"page_id": "../outside"}, {"page_id": "/outside/page"},
                       {"action": "remove"}, {"candidate_paths": []}, {"rendered_html": ""},
                       {"expected_sha256": "0" * 64}, {"page_id": "unselected"}):
            with self.subTest(inputs=inputs):
                self.assertEqual(self.publish(**inputs)["status"], "input_error")
        self.assertEqual(self.page.read_text(), "untouched original")

    def test_cleanup_with_wrong_digest_preserves_page_and_temporaries(self) -> None:
        temporary = self.page.parent / (".implementation-plan.html.tmp-42-" + "a" * 32)
        temporary.write_text("interrupted")
        result = self.publish(action="cleanup", expected_sha256="0" * 64)
        self.assertEqual(result["status"], "expected_failure", result)
        self.assertEqual(self.page.read_text(), "untouched original")
        self.assertTrue(temporary.exists())

    def test_symlink_and_fifo_final_paths_fail_closed(self) -> None:
        self.page.unlink()
        self.page.symlink_to(self.root / "outside/implementation-plan.html")
        self.assertNotEqual(self.publish()["status"], "ok")
        self.page.unlink()
        os.mkfifo(self.page)
        self.assertNotEqual(self.publish()["status"], "ok")
        self.assertEqual((self.root / "outside/implementation-plan.html").read_text(), "outside sentinel")

    def test_missing_artifact_directory_is_created_by_runner(self) -> None:
        for child in self.page.parent.iterdir():
            child.unlink()
        self.page.parent.rmdir()
        result = self.publish()
        self.assertEqual(result["status"], "ok", result)
        self.assertEqual(result["data"]["verified_html"], self.page.read_text())


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--probe":
        publication_probe(sys.argv[2], sys.argv[3])
    else:
        raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                     label="test-artifact-publication"))
