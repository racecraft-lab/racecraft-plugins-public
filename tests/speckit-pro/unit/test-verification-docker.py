#!/usr/bin/env python3
"""Provider-free tests for immutable Docker verification inputs and policy."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import stat
import subprocess
import sys
import tarfile
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "speckit-pro"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from test_result import run_counted
from speckit_pro_runner.verification_docker import (
    archive_snapshot, build_context, container_options, container_reasons, validate_base_image, validate_location,
)
from speckit_pro_runner import verification_docker_entrypoint as entrypoint
from speckit_pro_runner.verification_docker_runtime import DockerClient, capture_process, cleanup_container, execute_container

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
        self.assertIn("--log-driver=none", options)
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
                           "LogConfig": {"Type": "none", "Config": {}},
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


class DockerEntrypointTests(unittest.TestCase):
    def test_context_contains_only_captured_inputs_and_fixed_launcher(self):
        files = {".": (0o755, None), "check.py": (0o644, b"print('ok')")}
        with tempfile.TemporaryDirectory() as directory:
            context = Path(directory) / "context"
            binding = build_context(context, files, REFERENCE, ["python3", "check.py"])
            self.assertEqual(set(path.name for path in context.iterdir()),
                             {"Dockerfile", "snapshot.tar", "entrypoint.py", "request.json", ".dockerignore"})
            self.assertEqual(json.loads((context / "request.json").read_bytes()), {"argv": ["python3", "check.py"]})
            dockerfile = (context / "Dockerfile").read_text()
            self.assertTrue(dockerfile.startswith(f"FROM {REFERENCE}\n"))
            self.assertIn("ADD snapshot.tar /inputs/\n", dockerfile)
            self.assertFalse(any(line.startswith(("RUN", "VOLUME", "ONBUILD")) for line in dockerfile.splitlines()))
            self.assertEqual(binding, {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                       for path in context.iterdir()})
            with self.assertRaises(FileExistsError):
                build_context(context, files, REFERENCE, ["python3"])

    def test_invalid_command_never_creates_a_context(self):
        with tempfile.TemporaryDirectory() as directory:
            context = Path(directory) / "context"
            for argv in ([], "python3", [""], [True], ["python3", "bad\x00argument"], ["python3"] * 257,
                         ["python3", "x" * 65537]):
                with self.subTest(argv_type=type(argv).__name__), self.assertRaises(ValueError):
                    build_context(context, {".": (0o755, None)}, REFERENCE, argv)
                self.assertFalse(context.exists())

    def test_filter_rejects_other_abis_and_all_socket_and_io_uring_syscalls(self):
        instructions = entrypoint.filter_instructions()
        def evaluate(number, architecture):
            accumulator, index = 0, 0
            while index < len(instructions):
                code, yes, no, value = instructions[index]
                if code == 0x20:
                    accumulator = {0: number, 4: architecture}[value]
                elif code == 0x15:
                    index += yes if accumulator == value else no
                elif code == 0x06:
                    return value
                else:
                    self.fail("unexpected BPF instruction")
                index += 1
            self.fail("filter has no return")
        denied = set(range(198, 213)) | {242, 243, 269, 425, 426, 427}
        for number in range(500):
            self.assertEqual(evaluate(number, 0xC00000B7), 0x00050001 if number in denied else 0x7FFF0000)
            self.assertEqual(evaluate(number, 0xC000003E), 0x80000000)

    def test_unsupported_host_never_calls_prctl(self):
        with patch.object(entrypoint.sys, "platform", "darwin"), patch.object(entrypoint.ctypes, "CDLL") as libc:
            with self.assertRaises(ValueError):
                entrypoint.restrict_network()
            libc.assert_not_called()

    def test_filter_install_failure_prevents_command_execution(self):
        with patch.object(entrypoint, "restrict_network", side_effect=OSError("filter refused")), \
             patch.object(entrypoint.os, "execvpe") as execute:
            with self.assertRaises(OSError):
                entrypoint.launch(["python3", "check.py"])
            execute.assert_not_called()

    def test_prctl_failure_is_fail_closed_without_executing_a_host_filter(self):
        status = "Threads: 1\nSeccomp: 2\nSeccomp_filters: 1\nCapEff: 00000000\nNoNewPrivs: 1\n"
        for responses in ((-1,), (0, -1), (0, 0)):
            libc = SimpleNamespace(prctl=Mock(side_effect=responses))
            with self.subTest(responses=responses), patch.object(entrypoint.sys, "platform", "linux"), \
                 patch.object(entrypoint.sys, "byteorder", "little"), \
                 patch.object(entrypoint.os, "uname", return_value=SimpleNamespace(machine="aarch64"), create=True), \
                 patch.object(entrypoint.os, "getuid", return_value=65532, create=True), \
                 patch.object(entrypoint.Path, "read_text", return_value=status), \
                 patch.object(entrypoint.ctypes, "CDLL", return_value=libc):
                if -1 in responses:
                    with self.assertRaises(OSError):
                        entrypoint.restrict_network()
                else:
                    entrypoint.restrict_network()
                self.assertEqual(libc.prctl.call_count, len(responses))

    def test_launch_uses_direct_argv_and_fixed_environment_after_filter(self):
        order = []
        with patch.object(entrypoint, "restrict_network", side_effect=lambda: order.append("filter")), \
             patch.object(entrypoint.os, "chdir") as chdir, \
             patch.object(entrypoint.os, "execvpe", side_effect=lambda *args: order.append(args)):
            entrypoint.launch(["python3", "check.py", "literal;argument"])
        self.assertEqual(order[0], "filter")
        self.assertEqual(order[1], ("python3", ["python3", "check.py", "literal;argument"], entrypoint.ENVIRONMENT))
        self.assertEqual(entrypoint.ENVIRONMENT["TMPDIR"], "/outputs")
        self.assertEqual(entrypoint.ENVIRONMENT["HOME"], "/outputs")
        chdir.assert_called_once_with("/inputs")


class DockerRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "posix", "Docker transport requires a POSIX host")
    def test_transport_uses_explicit_socket_and_private_empty_config(self):
        original_stat = Path.stat
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "docker"
            executable.write_bytes(b"constructor-only fixture")
            executable.chmod(0o755)
            def observed_stat(path, *args, **kwargs):
                if path == root / "daemon.sock":
                    return SimpleNamespace(st_mode=stat.S_IFSOCK | 0o600)
                return original_stat(path, *args, **kwargs)
            # Pure constructor test; no live socket or daemon is required by the suite.
            with patch.object(Path, "stat", observed_stat):
                client = DockerClient(executable, f"unix://{root}/daemon.sock", root / "config")
            self.assertEqual(client.prefix, ["--host", f"unix://{root}/daemon.sock",
                                             "--config", str(root / "config")])
            self.assertEqual(client.environment["PATH"], str(root.resolve()))
            self.assertEqual(set(client.environment), {"HOME", "DOCKER_CONFIG", "PATH", "LANG"})
            self.assertEqual(list((root / "config").iterdir()), [])
            self.assertEqual((root / "config").stat().st_mode & 0o777, 0o700)
            with patch.object(Path, "stat", observed_stat), self.assertRaises(FileExistsError):
                DockerClient(executable, f"unix://{root}/daemon.sock", root / "config")

    def test_transport_non_socket_is_rejected_before_creating_config(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "docker"
            executable.write_bytes(b"constructor-only fixture")
            executable.chmod(0o755)
            fake = root / "not-a-socket"
            fake.touch()
            with self.assertRaises(ValueError):
                DockerClient(executable, f"unix://{fake}", root / "config")
            self.assertFalse((root / "config").exists())

    def test_transport_rejects_non_docker_executables(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config"
            with self.assertRaises(ValueError):
                DockerClient(Path(sys.executable), "unix:///tmp/unused.sock", config)
            self.assertFalse(config.exists())

    @unittest.skipUnless(os.name == "posix", "Docker capture backend requires a POSIX host")
    def test_capture_preserves_both_streams_and_real_exit_code(self):
        process = subprocess.Popen([sys.executable, "-c", "import sys; print('out'); print('err', file=sys.stderr); sys.exit(7)"],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        result = capture_process(process, 5, 1024)
        self.assertEqual((result["exit_code"], result["stdout"], result["stderr"]), (7, b"out\n", b"err\n"))
        self.assertFalse(result["timed_out"] or result["output_limited"])

    @unittest.skipUnless(os.name == "posix", "Docker capture backend requires a POSIX host")
    def test_capture_stops_at_timeout_or_output_limit(self):
        for source, timeout, flag in (("import time; time.sleep(10)", 0.1, "timed_out"),
                                      ("import os; os.write(1, b'x' * 100000)", 5, "output_limited")):
            with self.subTest(flag=flag):
                process = subprocess.Popen([sys.executable, "-c", source], stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, start_new_session=True)
                result = capture_process(process, timeout, 1024)
                self.assertTrue(result[flag])
                self.assertLessEqual(len(result["stdout"]) + len(result["stderr"]), 1024)

    def test_container_lifecycle_uses_observed_exit_and_confirms_removal(self):
        cid, calls = "d" * 64, []
        exists = False
        state = {"Status": "exited", "Running": False, "Pid": 0, "ExitCode": 7, "OOMKilled": False,
                 "Dead": False, "Error": ""}
        info = {"Id": cid, "Image": IMAGE_ID, "Name": f"/speckit-verifier-{EXECUTION_ID}",
                "Config": {"Labels": {"org.racecraft.verification": EXECUTION_ID}}, "State": state}
        def call(args, timeout, check=True):
            nonlocal exists
            calls.append(args)
            output = b""
            if args[0] == "create":
                exists = True
                output = cid.encode() + b"\n"
            elif args[0] == "ps" and exists:
                output = cid.encode() + b"\n"
            elif args[0] == "rm":
                exists = False
            elif args[0] == "inspect":
                output = json.dumps([info]).encode()
            elif args[0] == "wait":
                output = b"7\n"
            elif args[0] == "start":
                return {"exit_code": 7, "stdout": b"result", "stderr": b"", "timed_out": False, "output_limited": False}
            return {"exit_code": 0, "stdout": output, "stderr": b"", "timed_out": False, "output_limited": False}
        with patch("speckit_pro_runner.verification_docker_runtime.container_reasons", return_value=[]):
            result = execute_container(SimpleNamespace(call=call), IMAGE_ID, EXECUTION_ID, 5)
        self.assertEqual(result["exit_code"], 7)
        self.assertTrue(result["completed"] and result["cleanup_confirmed"])
        self.assertFalse(result["reusable"])
        self.assertEqual(sum(args[0] == "start" for args in calls), 1)
        self.assertIn(["rm", "--force", cid], calls)
        self.assertEqual(calls[-1], ["ps", "--all", "--no-trunc", "--filter", f"id={cid}", "--format", "{{.ID}}"])

    def test_existing_container_name_is_never_started_or_removed(self):
        calls = []
        def call(args, timeout, check=True):
            calls.append(args)
            return {"exit_code": 0, "stdout": b"existing\n", "stderr": b"", "timed_out": False, "output_limited": False}
        with self.assertRaises(ValueError):
            execute_container(SimpleNamespace(call=call), IMAGE_ID, EXECUTION_ID, 5)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], "ps")

    def test_wrong_inspected_identity_is_never_started(self):
        cid = "d" * 64
        def call(args, timeout, check=True):
            output = b""
            if args[0] == "create":
                output = cid.encode()
            elif args[0] == "inspect":
                output = json.dumps([{"Id": "e" * 64}]).encode()
            return {"exit_code": 0, "stdout": output, "stderr": b"", "timed_out": False, "output_limited": False}
        client = SimpleNamespace(call=Mock(side_effect=call))
        with patch("speckit_pro_runner.verification_docker_runtime.container_reasons", return_value=[]):
            result = execute_container(client, IMAGE_ID, EXECUTION_ID, 5)
        self.assertFalse(result["completed"])
        self.assertFalse(any(item.args[0][0] == "start" for item in client.call.call_args_list))

    def test_cleanup_refuses_wrong_owner_and_does_not_treat_daemon_errors_as_absence(self):
        info = {"Id": "d" * 64, "Image": IMAGE_ID, "Name": f"/speckit-verifier-{EXECUTION_ID}",
                "Config": {"Labels": {"org.racecraft.verification": "someone-else"}}}
        for responses in ([{"stdout": b"d" * 64}, {"stdout": json.dumps([info]).encode()}],
                          [ValueError("daemon unavailable")]):
            client = SimpleNamespace(call=Mock(side_effect=responses))
            with self.subTest(responses=len(responses)):
                self.assertFalse(cleanup_container(client, f"speckit-verifier-{EXECUTION_ID}", IMAGE_ID, EXECUTION_ID))
                self.assertFalse(any(item.args[0][0] == "rm" for item in client.call.call_args_list))


if __name__ == "__main__":
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case)
                               for case in (DockerInputTests, DockerPolicyTests, DockerEntrypointTests, DockerRuntimeTests))
    raise SystemExit(run_counted(suite, label="test-verification-docker"))
