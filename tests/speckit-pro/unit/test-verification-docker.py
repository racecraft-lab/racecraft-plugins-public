#!/usr/bin/env python3
"""Provider-free tests for immutable Docker verification inputs and policy."""

from __future__ import annotations

import copy
import hashlib
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "speckit-pro"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from test_result import run_counted
from speckit_pro_runner.verification_docker import (
    archive_snapshot, container_options, container_reasons, validate_base_image, validate_location,
)

REFERENCE = "python@sha256:" + "a" * 64
IMAGE_ID = "sha256:" + "b" * 64
EXECUTION_ID = "c" * 32


class DockerInputTests(unittest.TestCase):
    def test_location_requires_a_digest_and_local_unix_endpoint(self):
        self.assertEqual(validate_location(REFERENCE, "unix:///tmp/docker.sock"), (REFERENCE, "/tmp/docker.sock"))
        for reference, endpoint in (("python:latest", "unix:///tmp/docker.sock"),
                                    (REFERENCE + "\nRUN false", "unix:///tmp/docker.sock"),
                                    (REFERENCE, "tcp://example.com:2375"),
                                    (REFERENCE, "unix://relative/docker.sock"),
                                    (REFERENCE, "unix:///tmp/../docker.sock"),
                                    (REFERENCE, "unix:///tmp/docker.sock?query")):
            with self.subTest(reference=reference, endpoint=endpoint), self.assertRaises(ValueError):
                validate_location(reference, endpoint)

    def test_base_image_requires_the_observed_digest_and_supported_platform(self):
        info = {"Id": IMAGE_ID, "RepoDigests": [REFERENCE], "Os": "linux", "Architecture": "arm64",
                "Config": {"OnBuild": None, "Volumes": None}}
        self.assertEqual(validate_base_image(info, REFERENCE), IMAGE_ID)
        for key, value in (("Id", "latest"), ("RepoDigests", []), ("RepoDigests", REFERENCE), ("Os", "windows"), ("Architecture", "amd64")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_base_image({**info, key: value}, REFERENCE)
        for key, value in (("OnBuild", ["RUN false"]), ("OnBuild", False), ("Volumes", {"/inputs": {}}), ("Volumes", [])):
            bad = copy.deepcopy(info)
            bad["Config"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_base_image(bad, REFERENCE)

    def test_archive_is_deterministic_and_preserves_bytes_directories_and_modes(self):
        files = {".": (0o750, None), "empty": (0o700, None), "check.py": (0o755, b"print('ok')\n"),
                 "fixture.txt": (0o640, b"dirty ignored input\x00")}
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "one.tar", Path(directory) / "two.tar"
            digest = archive_snapshot(first, files)
            self.assertEqual(archive_snapshot(second, dict(reversed(list(files.items())))), digest)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(hashlib.sha256(first.read_bytes()).hexdigest(), digest)
            with tarfile.open(first) as archive:
                self.assertEqual(set(archive.getnames()), set(files))
                for member in archive.getmembers():
                    mode, body = files[member.name]
                    self.assertEqual(member.mode, mode)
                    self.assertEqual((member.uid, member.gid, member.mtime), (65532, 65532, 0))
                    self.assertEqual(member.isdir(), body is None)
                    if body is not None:
                        self.assertEqual(archive.extractfile(member).read(), body)

    def test_invalid_snapshot_is_rejected_before_creating_an_archive(self):
        cases = ({"../escape": (0o644, b"x")}, {"/absolute": (0o644, b"x")},
                 {"a//b": (0o644, b"x")}, {"a\\b": (0o644, b"x")},
                 {"a\x00b": (0o644, b"x")}, {".": (0o644, b"not a directory")},
                 {".": (True, None)}, {".": (0o10000, None)}, {".": (0o755, "not bytes")},
                 {".": (0o755, None), "missing/child": (0o644, b"x")},
                 {".": (0o755, None), "file": (0o644, b"x"), "file/child": (0o644, b"x")})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "snapshot.tar"
            for files in cases:
                with self.subTest(files=files), self.assertRaises(ValueError):
                    archive_snapshot(path, files)
                self.assertFalse(path.exists())

    def test_archive_never_overwrites_an_existing_target(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "snapshot.tar"
            path.write_bytes(b"keep")
            with self.assertRaises(FileExistsError):
                archive_snapshot(path, {".": (0o755, None)})
            self.assertEqual(path.read_bytes(), b"keep")

    def test_archive_enforces_entry_and_byte_limits_before_writing(self):
        files = {".": (0o755, None), "file": (0o644, b"four")}
        with tempfile.TemporaryDirectory() as directory:
            for name, value in (("MAX_SNAPSHOT_ENTRIES", 1), ("MAX_SNAPSHOT_BYTES", 3)):
                path = Path(directory) / f"{name}.tar"
                with self.subTest(limit=name), patch(f"speckit_pro_runner.verification_docker.{name}", value):
                    with self.assertRaises(ValueError):
                        archive_snapshot(path, files)
                    self.assertFalse(path.exists())


class DockerPolicyTests(unittest.TestCase):
    def test_options_preserve_the_tested_restrictions_without_host_mounts(self):
        options = container_options(IMAGE_ID, EXECUTION_ID)
        for option in ("--pull=never", "--platform=linux/arm64", "--read-only", "--network=none",
                       "--cap-drop=ALL", "--security-opt=no-new-privileges=true", "--user=65532:65532",
                       "--pids-limit=32", "--memory=256m", "--memory-swap=256m", "--cpus=1", "--ipc=none"):
            self.assertIn(option, options)
        self.assertFalse(any(option.startswith(("--mount", "--volume", "--privileged", "--device")) for option in options))
        self.assertEqual(options[-4:], [IMAGE_ID, "-I", "-S", "/__speckit/entrypoint.py"])
        self.assertIn("--entrypoint=/usr/local/bin/python3", options)
        self.assertIn("--workdir=/inputs", options)
        self.assertIn(f"--name=speckit-verifier-{EXECUTION_ID}", options)
        for image_id, execution_id in (("python:latest", EXECUTION_ID), (IMAGE_ID, "../../bad")):
            with self.assertRaises(ValueError):
                container_options(image_id, execution_id)

    def test_policy_configuration_matches_and_tampering_is_rejected(self):
        config = {
            "Image": IMAGE_ID, "Mounts": [],
            "Config": {"User": "65532:65532", "WorkingDir": "/inputs",
                       "Entrypoint": ["/usr/local/bin/python3"],
                       "Cmd": ["-I", "-S", "/__speckit/entrypoint.py"], "Labels": {"org.racecraft.verification": EXECUTION_ID}},
            "HostConfig": {"ReadonlyRootfs": True, "NetworkMode": "none", "Privileged": False,
                           "Memory": 268435456, "MemorySwap": 268435456, "NanoCpus": 1000000000,
                           "PidsLimit": 32, "IpcMode": "none", "PublishAllPorts": False,
                           "CapDrop": ["ALL"], "CapAdd": None, "Binds": None,
                           "SecurityOpt": ["no-new-privileges=true"], "Devices": [], "DeviceRequests": None,
                           "PortBindings": {}, "PidMode": "", "RestartPolicy": {"Name": "no"},
                           "Tmpfs": {"/outputs": "rw,nosuid,nodev,noexec,size=16777216,uid=65532,gid=65532,mode=0700"}},
        }
        self.assertEqual(container_reasons(config, IMAGE_ID, EXECUTION_ID), [])
        changes = (("ReadonlyRootfs", False), ("ReadonlyRootfs", 1), ("NetworkMode", "bridge"),
                   ("Privileged", True), ("Binds", ["/:/host:ro"]), ("CapAdd", ["SYS_ADMIN"]),
                   ("SecurityOpt", ["no-new-privileges=true", "seccomp=unconfined"]),
                   ("Tmpfs", {}), ("PidMode", "host"), ("Memory", 0), ("PidsLimit", -1))
        for key, value in changes:
            changed = copy.deepcopy(config)
            changed["HostConfig"][key] = value
            with self.subTest(key=key, value=value):
                self.assertTrue(container_reasons(changed, IMAGE_ID, EXECUTION_ID))
        for key, value in (("Image", "sha256:" + "d" * 64), ("Mounts", [{"Source": "/host"}])):
            with self.subTest(key=key):
                self.assertTrue(container_reasons({**config, key: value}, IMAGE_ID, EXECUTION_ID))
        for key, value in (("User", "0"), ("WorkingDir", "/"), ("Entrypoint", ["sh"]), ("Cmd", ["other"]), ("Labels", {})):
            changed = copy.deepcopy(config)
            changed["Config"][key] = value
            with self.subTest(key=key):
                self.assertTrue(container_reasons(changed, IMAGE_ID, EXECUTION_ID))


if __name__ == "__main__":
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case)
                               for case in (DockerInputTests, DockerPolicyTests))
    raise SystemExit(run_counted(suite, label="test-verification-docker"))
