#!/usr/bin/env python3
"""Artifact publication through the public runner, with filesystem race probes."""

from __future__ import annotations

import hashlib
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

    original_replace, original_stat, original_rename, original_link = os.replace, os.stat, os.rename, os.link
    events = []
    fired = False
    stat_calls = 0

    def replaced_basename(source, destination, **kwargs):
        nonlocal fired
        if not fired and destination == "implementation-plan.html":
            fired = True
            source_fd = kwargs.get("src_dir_fd")
            original_replace(source, "saved-written.html", src_dir_fd=source_fd, dst_dir_fd=source_fd)
            if attack == "rename-temp-symlink":
                os.symlink("../outside/implementation-plan.html", source, dir_fd=source_fd)
            elif attack == "rename-temp-hardlink":
                os.link("victim.html", source, src_dir_fd=source_fd, dst_dir_fd=source_fd)
            else:
                fd = os.open(source, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=source_fd)
                try:
                    os.write(fd, b"attacker bytes")
                finally:
                    os.close(fd)
            events.append({"event": "temporary-rename", "anchored": source_fd is not None})
        return original_replace(source, destination, **kwargs)

    def statted(name, *args, **kwargs):
        nonlocal fired, stat_calls
        result = original_stat(name, *args, **kwargs)
        if name == "implementation-plan.html" and kwargs.get("dir_fd") is not None:
            stat_calls += 1
        if not fired and stat_calls == 2 and name == "implementation-plan.html":
            fired = True
            directory_fd = kwargs["dir_fd"]
            original_replace(name, "saved-owned.html", src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
            original_replace("victim.html", name, src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
            events.append({"event": "cleanup-rename", "anchored": True})
        return result

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

    original_open, original_unlink, original_fsync = os.open, os.unlink, os.fsync

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
        nonlocal fired
        if attack == "temporary-collision" and str(name).startswith(".implementation-plan.html.tmp-") and args[0] & os.O_CREAT:
            fd = original_open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, **kwargs)
            try:
                os.write(fd, b"foreign collision")
            finally:
                os.close(fd)
            events.append({"event": "temporary-collision", "anchored": kwargs.get("dir_fd") is not None})
        if attack == "captured-entry" and not fired and name == "entry":
            fired = True
            fd = kwargs["dir_fd"]
            original_replace(name, "saved-owned", src_dir_fd=fd, dst_dir_fd=fd)
            changed = original_open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=fd)
            try:
                os.write(changed, b"replacement victim")
            finally:
                os.close(changed)
            events.append({"event": "captured-entry", "anchored": True})
        if attack == "read-swap" and name == "implementation-plan.html":
            return anchored_boundary(original_open, name, args, kwargs)
        return original_open(name, *args, **kwargs)

    def rename_cleanup(source, destination, **kwargs):
        nonlocal fired
        if attack.startswith("rename-cleanup") and not fired and source == "implementation-plan.html":
            fired = True
            fd = kwargs["src_dir_fd"]
            original_replace(source, "saved-owned.html", src_dir_fd=fd, dst_dir_fd=fd)
            if attack == "rename-cleanup-bytes":
                original_replace("saved-owned.html", source, src_dir_fd=fd, dst_dir_fd=fd)
                changed = original_open(source, os.O_WRONLY | os.O_TRUNC, dir_fd=fd)
                try:
                    os.write(changed, b"replacement victim")
                finally:
                    os.close(changed)
            else:
                original_replace("victim.html", source, src_dir_fd=fd, dst_dir_fd=fd)
            events.append({"event": "cleanup-rename", "anchored": True})
        if attack == "cleanup-swap" and source == "implementation-plan.html":
            directory = Path("artifacts")
            directory.rename("held-artifacts")
            directory.symlink_to("outside", target_is_directory=True)
            try:
                events.append({"event": "cleanup", "anchored": kwargs.get("src_dir_fd") is not None})
                return original_rename(source, destination, **kwargs)
            finally:
                directory.unlink()
                Path("held-artifacts").rename(directory)
        result = original_rename(source, destination, **kwargs)
        if attack == "after-capture" and source == "implementation-plan.html":
            fd = kwargs["src_dir_fd"]
            original_link("victim.html", source, src_dir_fd=fd, dst_dir_fd=fd)
            events.append({"event": "after-capture", "anchored": True})
        return result

    def unlinked(name, *args, **kwargs):
        if attack == "cleanup-swap" and name == "implementation-plan.html":
            return anchored_boundary(original_unlink, name, args, kwargs)
        return original_unlink(name, *args, **kwargs)

    def synced(fd):
        result = original_fsync(fd)
        if attack == "tamper-temp":
            for path in Path("artifacts").glob(".implementation-plan.html.tmp-*"):
                observed = path.stat()
                held = os.fstat(fd)
                if (held.st_dev, held.st_ino) == (observed.st_dev, observed.st_ino):
                    os.pwrite(fd, b"tampered", 0)
                    os.ftruncate(fd, 8)
                    events.append({"event": "temporary-bytes", "anchored": True})
        return result

    def linked(source, destination, **kwargs):
        nonlocal fired
        if attack.startswith("rollback-link") and not fired and source == "previous":
            fired = True
            fd = kwargs["src_dir_fd"]
            original_replace(source, "saved-previous", src_dir_fd=fd, dst_dir_fd=fd)
            if attack == "rollback-link-symlink":
                os.symlink("../../outside/implementation-plan.html", source, dir_fd=fd)
            else:
                changed = original_open(source, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=fd)
                try:
                    os.write(changed, b"attacker rollback bytes")
                finally:
                    os.close(changed)
            events.append({"event": "rollback-link", "anchored": True})
        return original_link(source, destination, **kwargs)

    os.link = linked
    os.fsync = synced
    if attack in {"restore-old", "publish-swap"}:
        os.replace = replace
    if attack.startswith("rename-temp"):
        os.replace = replaced_basename
    if attack == "rename-cleanup":
        os.stat = statted
    if attack == "post-replace-failure" or attack.startswith("rollback-link"):
        from speckit_pro_runner.helpers import artifact_publication
        original_binding = artifact_publication.verify_directory_binding
        binding_calls = 0

        def binding(*args):
            nonlocal binding_calls
            binding_calls += 1
            if binding_calls == 2:
                events.append({"event": "post-replace-failure", "anchored": True})
                raise ValueError("injected final directory validation failure")
            return original_binding(*args)

        artifact_publication.verify_directory_binding = binding
    os.open, os.unlink, os.rename = opened, unlinked, rename_cleanup
    sys.argv = sys.argv[:1]
    try:
        runpy.run_module("speckit_pro_runner", run_name="__main__")
    finally:
        Path("probe-events.json").write_text(json.dumps(events), encoding="utf-8")


class PublicationFixture(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
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
            if self.page.is_file():
                request["inputs"].setdefault("expected_sha256", hashlib.sha256(self.page.read_bytes()).hexdigest())
                observed = self.page.stat()
                request["inputs"].setdefault("expected_file_identity", [observed.st_dev, observed.st_ino])
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

    def test_temporary_basename_rename_fails_closed_without_attacker_final(self) -> None:
        for plugin in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            with self.subTest(plugin=plugin):
                self.page.write_text("untouched original")
                result = self.publish("rename-temp", plugin)
                self.assertEqual(result["status"], "expected_failure", result)
                self.assertEqual(self.page.read_text(), "untouched original")
                self.assertEqual(json.loads((self.root / "probe-events.json").read_text()),
                                 [{"event": "temporary-rename", "anchored": True}])

    def test_temporary_link_substitutions_fail_closed_and_preserve_old(self) -> None:
        for plugin in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            for attack in ("rename-temp-symlink", "rename-temp-hardlink"):
                with self.subTest(plugin=plugin, attack=attack):
                    if self.page.is_symlink():
                        self.page.unlink()
                    self.page.write_text("untouched original")
                    (self.root / "outside/implementation-plan.html").write_text("outside sentinel")
                    (self.page.parent / "victim.html").write_text("<html><body>finished page</body></html>")
                    result = self.publish(attack, plugin)
                    self.assertEqual(result["status"], "expected_failure", result)
                    self.assertFalse(self.page.is_symlink())
                    self.assertEqual(self.page.read_text(), "untouched original")
                    self.assertEqual((self.root / "outside/implementation-plan.html").read_text(), "outside sentinel")
                    self.assertEqual(json.loads((self.root / "probe-events.json").read_text()),
                                     [{"event": "temporary-rename", "anchored": True}])

    def test_cleanup_basename_rename_preserves_replacement(self) -> None:
        for plugin in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            with self.subTest(plugin=plugin):
                self.page.write_text("untouched original")
                (self.page.parent / "victim.html").write_text("replacement victim")
                result = self.publish("rename-cleanup", plugin, action="cleanup")
                self.assertEqual(result["status"], "expected_failure", result)
                self.assertEqual(self.page.read_text(), "replacement victim")
                self.assertEqual(json.loads((self.root / "probe-events.json").read_text()),
                                 [{"event": "cleanup-rename", "anchored": True}])

    def test_cleanup_replacement_after_capture_is_preserved_and_reported(self) -> None:
        for plugin in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            with self.subTest(plugin=plugin):
                self.page.write_text("untouched original")
                (self.page.parent / "victim.html").write_text("replacement victim")
                result = self.publish("after-capture", plugin, action="cleanup")
                self.assertEqual(result["status"], "expected_failure", result)
                self.assertEqual(self.page.read_text(), "replacement victim")
                self.assertEqual(json.loads((self.root / "probe-events.json").read_text()),
                                 [{"event": "after-capture", "anchored": True}])

    def test_cleanup_capture_rejects_links_special_files_and_changed_bytes(self) -> None:
        for plugin in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            for variant in ("symlink", "hardlink", "fifo", "bytes"):
                with self.subTest(plugin=plugin, variant=variant):
                    if self.page.exists() or self.page.is_symlink():
                        self.page.unlink()
                    self.page.write_text("untouched original")
                    victim = self.page.parent / "victim.html"
                    if victim.exists() or victim.is_symlink():
                        victim.unlink()
                    if variant == "symlink":
                        victim.symlink_to("../outside/implementation-plan.html")
                    elif variant == "fifo":
                        os.mkfifo(victim)
                    elif variant == "hardlink":
                        os.link(self.page.parent / "old.html", victim)
                    else:
                        victim.write_text("replacement victim")
                    result = self.publish("rename-cleanup-" + variant, plugin, action="cleanup")
                    self.assertEqual(result["status"], "expected_failure", result)
                    self.assertTrue(self.page.exists() or self.page.is_symlink())
                    self.assertEqual((self.root / "outside/implementation-plan.html").read_text(), "outside sentinel")
                    self.assertEqual(json.loads((self.root / "probe-events.json").read_text()),
                                     [{"event": "cleanup-rename", "anchored": True}])

    def test_temporary_collision_never_cleans_an_entry_it_did_not_create(self) -> None:
        for plugin in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            with self.subTest(plugin=plugin):
                result = self.publish("temporary-collision", plugin)
                self.assertEqual(result["status"], "expected_failure", result)
                self.assertEqual(self.page.read_text(), "untouched original")
                self.assertTrue(all(path.read_text() == "foreign collision"
                                    for path in self.page.parent.glob(".implementation-plan.html.tmp-*")))
                self.assertEqual(json.loads((self.root / "probe-events.json").read_text()),
                                 [{"event": "temporary-collision", "anchored": True}])

    def test_captured_entry_rename_is_preserved_without_unlink(self) -> None:
        for plugin in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            with self.subTest(plugin=plugin):
                self.page.write_text("untouched original")
                result = self.publish("captured-entry", plugin, action="cleanup")
                self.assertEqual(result["status"], "expected_failure", result)
                self.assertEqual(self.page.read_text(), "replacement victim")
                self.assertTrue(any(path.read_text() == "untouched original"
                                    for path in self.page.parent.glob(".artifact-recovery-*/saved-owned")))
                self.assertEqual(json.loads((self.root / "probe-events.json").read_text()),
                                 [{"event": "captured-entry", "anchored": True}])

    def test_open_temporary_tampering_is_rejected(self) -> None:
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

    def test_cleanup_preserves_unreceipted_temporaries(self) -> None:
        owned = self.root / ("artifacts/.implementation-plan.html.tmp-42-" + "a" * 32)
        owned.write_text("interrupted temporary", encoding="utf-8")
        foreign = self.root / "artifacts/.implementation-plan.html.tmp-foreign"
        foreign.write_text("foreign temporary", encoding="utf-8")
        result = self.publish(action="cleanup")
        self.assertEqual(result["status"], "ok", result)
        self.assertFalse(self.page.exists())
        self.assertTrue(owned.exists())
        self.assertTrue(foreign.exists())
        self.assertEqual(result["data"]["removed_temporaries"], 0)


class PublicationInputTests(PublicationFixture):
    def test_dry_run_and_invalid_inputs_leave_original_untouched(self) -> None:
        self.assertEqual(self.publish(mode="dry_run")["status"], "ok")
        for inputs in ({"page_id": "../outside"}, {"page_id": "/outside/page"},
                       {"action": "remove"}, {"candidate_paths": []}, {"rendered_html": ""},
                       {"expected_sha256": "0" * 64}, {"page_id": "unselected"}):
            with self.subTest(inputs=inputs):
                self.assertEqual(self.publish(**inputs)["status"], "input_error")
        self.assertEqual(self.page.read_text(), "untouched original")

    def test_deselected_page_can_be_removed_only_with_its_receipt(self) -> None:
        original = self.page
        for plugin in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            with self.subTest(plugin=plugin):
                self.page = original.parent / "module-map.html"
                (self.root / "plan.md").write_text("## Declared File Operations\n\n- MODIFIED src/existing.py\n")
                published = self.publish(plugin=plugin, page_id="module-map")
                self.assertEqual(published["status"], "ok", published)
                (self.root / "plan.md").write_text("## Declared File Operations\n\n- NEW src/new.py\n")
                receipt = published["data"]
                removed = self.publish(plugin=plugin, page_id="module-map", action="cleanup",
                                       expected_sha256=receipt["sha256"], expected_file_identity=receipt["file_identity"])
                self.assertEqual(removed["status"], "ok", removed)
                self.assertTrue(removed["data"]["removed"])
                self.assertFalse(self.page.exists())
        self.page = original

    def test_cleanup_requires_a_publication_receipt(self) -> None:
        for plugin in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            with self.subTest(plugin=plugin):
                self.assertEqual(self.publish(plugin=plugin, action="cleanup", expected_sha256=None)["status"], "input_error")
                self.assertEqual(self.page.read_text(), "untouched original")

    def test_rollback_link_substitution_preserves_old_without_attacker_final(self) -> None:
        for plugin in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            with self.subTest(plugin=plugin):
                self.page.write_text("untouched original")
                result = self.publish("rollback-link", plugin)
                self.assertEqual(result["status"], "expected_failure", result)
                self.assertFalse(self.page.exists())
                self.assertTrue(any(path.read_text() == "untouched original"
                                    for path in self.page.parent.glob(".artifact-recovery-*/saved-previous")))
                self.assertEqual(json.loads((self.root / "probe-events.json").read_text()),
                                 [{"event": "post-replace-failure", "anchored": True},
                                  {"event": "rollback-link", "anchored": True}])

    def test_rollback_link_symlink_substitution_is_quarantined(self) -> None:
        for plugin in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            with self.subTest(plugin=plugin):
                if self.page.is_symlink():
                    self.page.unlink()
                self.page.write_text("untouched original")
                result = self.publish("rollback-link-symlink", plugin)
                self.assertEqual(result["status"], "expected_failure", result)
                self.assertFalse(self.page.is_symlink())
                self.assertFalse(self.page.exists())
                self.assertEqual((self.root / "outside/implementation-plan.html").read_text(), "outside sentinel")
                self.assertTrue(any(path.read_text() == "untouched original"
                                    for path in self.page.parent.glob(".artifact-recovery-*/saved-previous")))

    def test_cleanup_receipt_rejects_replacements_and_malformed_identity(self) -> None:
        for plugin in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            for identity in (None, [], [True, 0], [-1, 1], ["1", "2"], [0, 0]):
                with self.subTest(plugin=plugin, identity=identity):
                    result = self.publish(plugin=plugin, action="cleanup", expected_file_identity=identity)
                    expected = "expected_failure" if identity == [0, 0] else "input_error"
                    self.assertEqual(result["status"], expected, result)
                    self.assertEqual(self.page.read_text(), "untouched original")

    def test_post_replace_failure_restores_the_previous_page(self) -> None:
        for plugin in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            with self.subTest(plugin=plugin):
                self.page.write_text("untouched original")
                result = self.publish("post-replace-failure", plugin)
                self.assertEqual(result["status"], "expected_failure", result)
                self.assertEqual(self.page.read_text(), "untouched original")
                self.assertEqual(json.loads((self.root / "probe-events.json").read_text()),
                                 [{"event": "post-replace-failure", "anchored": True}])

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
