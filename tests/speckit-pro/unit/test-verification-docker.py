#!/usr/bin/env python3
"""Provider-free tests for immutable Docker verification inputs and policy."""

from __future__ import annotations

import copy
import hashlib
import io
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
from speckit_pro_runner.verification_docker_image import cleanup_image, execute_image, validate_built_image
from speckit_pro_runner.verification_docker_readback import SnapshotReadback, verify_snapshot_archive

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
            self.assertIn("ADD snapshot.tar /\n", dockerfile)
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

    def test_image_archive_preserves_the_source_root_as_an_explicit_directory(self):
        files = {".": (0o751, None), "check.py": (0o640, b"check")}
        with tempfile.TemporaryDirectory() as directory:
            context = Path(directory) / "context"
            build_context(context, files, REFERENCE, ["python3", "check.py"])
            with tarfile.open(context / "snapshot.tar") as archive:
                self.assertEqual(archive.getnames(), ["inputs", "inputs/check.py"])
                root = archive.getmember("inputs")
                self.assertEqual((root.mode, root.uid, root.gid), (0o751, 65532, 65532))

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
    @unittest.skipUnless(os.name == "posix", "Docker capture backend requires a POSIX host")
    def test_capture_streams_archive_stdout_to_owned_file_with_the_same_byte_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "archive"
            process = subprocess.Popen([sys.executable, "-c", "import os; os.write(1, b'x' * 100000)"],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
            with output.open("xb") as sink:
                result = capture_process(process, 5, 1024, stdout_file=sink)
            self.assertTrue(result["output_limited"])
            self.assertEqual(result["stdout"], b"")
            self.assertEqual(output.read_bytes(), b"x" * 1024)
            self.assertEqual(result["stdout_size"], 1024)
            self.assertEqual(result["stdout_sha256"], hashlib.sha256(b"x" * 1024).hexdigest())

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

    def test_input_readback_mismatch_prevents_workload_start_and_still_cleans_up(self):
        cid, calls = "d" * 64, []
        info = {"Id": cid, "Name": f"/speckit-verifier-{EXECUTION_ID}",
                "State": {"Status": "created", "Running": False, "Pid": 0}}
        def call(args, timeout, check=True, **kwargs):
            calls.append(args)
            output = b""
            if args[0] == "create":
                output = cid.encode()
            elif args[0] == "inspect":
                output = json.dumps([info]).encode()
            elif args[0] == "cp":
                archive_snapshot(kwargs["archive"], {".": (0o755, None)})
                return {"stdout_sha256": hashlib.sha256(kwargs["archive"].read_bytes()).hexdigest()}
            return {"stdout": output}
        with tempfile.TemporaryDirectory() as directory, \
             patch("speckit_pro_runner.verification_docker_runtime.container_reasons", return_value=[]), \
             patch("speckit_pro_runner.verification_docker_runtime.cleanup_container", return_value=True) as cleanup:
            result = execute_container(SimpleNamespace(call=call), IMAGE_ID, EXECUTION_ID, 5,
                                       SnapshotReadback({".": (0o751, None)}, Path(directory) / "archive"))
        self.assertFalse(result["completed"])
        self.assertNotIn("input_readback", result)
        self.assertFalse(any(args[0] == "start" for args in calls))
        self.assertTrue(any(args[0] == "cp" for args in calls))
        cleanup.assert_called_once()

    def test_cleanup_refuses_wrong_owner_and_does_not_treat_daemon_errors_as_absence(self):
        info = {"Id": "d" * 64, "Image": IMAGE_ID, "Name": f"/speckit-verifier-{EXECUTION_ID}",
                "Config": {"Labels": {"org.racecraft.verification": "someone-else"}}}
        for responses in ([{"stdout": b"d" * 64}, {"stdout": json.dumps([info]).encode()}],
                          [ValueError("daemon unavailable")]):
            client = SimpleNamespace(call=Mock(side_effect=responses))
            with self.subTest(responses=len(responses)):
                self.assertFalse(cleanup_container(client, f"speckit-verifier-{EXECUTION_ID}", IMAGE_ID, EXECUTION_ID))
                self.assertFalse(any(item.args[0][0] == "rm" for item in client.call.call_args_list))


class DockerReadbackTests(unittest.TestCase):
    def setUp(self):
        self.files = {".": (0o751, None), "empty": (0o705, None), "file": (0o640, b"unchanged\x00bytes")}

    def archive(self, path, *, change=None, extra=None):
        with tarfile.open(path, "w", format=tarfile.PAX_FORMAT) as archive:
            for name, (mode, body) in self.files.items():
                member = tarfile.TarInfo("." if name == "." else f"./{name}")
                member.mode, member.uid, member.gid = mode, 65532, 65532
                member.type = tarfile.DIRTYPE if body is None else tarfile.REGTYPE
                member.size = len(body) if body is not None else 0
                if change:
                    change(member)
                archive.addfile(member, io.BytesIO(body) if body is not None and member.isfile() else None)
            if extra:
                archive.addfile(extra)

    def test_readback_compares_every_entry_byte_mode_and_owner_without_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "readback.tar"
            self.archive(path)
            result = verify_snapshot_archive(path, self.files)
            self.assertTrue(result["verified"])
            self.assertEqual(result["entries"], len(self.files))
            self.assertEqual(result["archive_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_root_mode_byte_and_missing_entry_mismatches_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "readback.tar"
            self.archive(path)
            for expected in ({**self.files, ".": (0o755, None)},
                             {**self.files, "file": (0o640, b"x" * len(self.files["file"][1]))},
                             {**self.files, "missing": (0o644, b"")},
                             {name: value for name, value in self.files.items() if name != "empty"}):
                with self.subTest(expected=expected), self.assertRaises(ValueError):
                    verify_snapshot_archive(path, expected)

    def test_unsafe_members_duplicates_and_unbound_metadata_are_rejected(self):
        def mutate(member, key, value):
            if member.name == "./file":
                setattr(member, key, value)
        cases = (("name", "../escape"), ("name", "/absolute"), ("name", "./empty"),
                 ("name", "./a/../file"), ("name", "././file"), ("uid", 0), ("gid", 0),
                 ("type", tarfile.SYMTYPE), ("type", tarfile.LNKTYPE), ("type", tarfile.FIFOTYPE),
                 ("pax_headers", {"SCHILY.xattr.user.hidden": "unbound"}))
        with tempfile.TemporaryDirectory() as directory:
            for index, (key, value) in enumerate(cases):
                path = Path(directory) / f"{index}.tar"
                self.archive(path, change=lambda member: mutate(member, key, value))
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    verify_snapshot_archive(path, self.files)

    def test_truncation_trailing_payload_and_archive_limit_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "readback.tar"
            self.archive(path)
            original = path.read_bytes()
            for data in (original[:100], original[:2048], original + b"unexpected archive payload"):
                path.write_bytes(data)
                with self.subTest(size=len(data)), self.assertRaises(ValueError):
                    verify_snapshot_archive(path, self.files)
            path.write_bytes(original)
            with patch("speckit_pro_runner.verification_docker_readback.MAX_ARCHIVE_BYTES", 1), self.assertRaises(ValueError):
                verify_snapshot_archive(path, self.files)


class DockerImageTests(unittest.TestCase):
    def setUp(self):
        self.tag = f"speckit-verifier:{EXECUTION_ID}"
        self.built_id = "sha256:" + "d" * 64
        self.base = {"Id": IMAGE_ID, "RepoDigests": [REFERENCE], "Os": "linux", "Architecture": "arm64",
                     "Config": {"OnBuild": None, "Volumes": None},
                     "RootFS": {"Type": "layers", "Layers": ["sha256:" + "e" * 64]}}
        self.built = {**copy.deepcopy(self.base), "Id": self.built_id, "RepoTags": [self.tag]}
        self.built["Config"]["Labels"] = {"org.racecraft.verification": EXECUTION_ID}
        self.built["RootFS"]["Layers"].append("sha256:" + "f" * 64)

    def test_built_image_binds_exact_id_owner_platform_and_base_layers(self):
        validate_built_image(self.built, self.base, self.built_id, EXECUTION_ID)
        for key, value in (("Id", IMAGE_ID), ("RepoTags", []), ("Os", "windows"),
                           ("Architecture", "amd64"), ("RootFS", None),
                           ("RootFS", {"Type": "layers", "Layers": ["sha256:" + "f" * 64]}),
                           ("Config", {"OnBuild": ["RUN false"]}),
                           ("Config", {"Volumes": {"/inputs": {}}, "Labels": self.built["Config"]["Labels"]}),
                           ("Config", {"Labels": {"org.racecraft.verification": "wrong"}})):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_built_image({**self.built, key: value}, self.base, self.built_id, EXECUTION_ID)

    def test_build_run_and_cleanup_preserve_nonzero_result_and_private_context(self):
        calls, exists = [], False
        def call(args, timeout, check=True):
            nonlocal exists
            calls.append(args)
            self.assertGreater(timeout, 0)
            output = b""
            if args[:2] == ["image", "inspect"]:
                output = json.dumps([self.base if args[2] == REFERENCE else self.built]).encode()
            elif args[:2] == ["image", "ls"] and exists:
                output = self.built_id.encode()
            elif args[0] == "build":
                exists = True
                Path(args[args.index("--iidfile") + 1]).write_text(self.built_id)
            elif args[:2] == ["image", "rm"]:
                exists = False
            return {"stdout": output, "stderr": b"", "exit_code": 0, "timed_out": False, "output_limited": False}
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory) / "evidence"
            with patch("speckit_pro_runner.verification_docker_image.execute_container",
                       return_value={"completed": True, "exit_code": 23, "stdout": b"out", "stderr": b"err",
                                     "cleanup_confirmed": True, "reusable": False}) as launch:
                result = execute_image(SimpleNamespace(call=call), {".": (0o755, None)}, REFERENCE,
                                       ["python3", "check.py"], EXECUTION_ID, evidence, 30)
            self.assertTrue(result["completed"] and result["image_tag_cleanup_confirmed"])
            self.assertEqual(result["exit_code"], 23)
            self.assertFalse(result["reusable"])
            self.assertTrue(result["build_cache_may_retain_inputs"])
            self.assertEqual(evidence.stat().st_mode & 0o777, 0o700)
            self.assertEqual(result["base_image"]["Id"], IMAGE_ID)
            self.assertEqual(result["built_image"]["Id"], self.built_id)
            self.assertIn("snapshot.tar", result["context_binding"])
            launch.assert_called_once()
            build = next(args for args in calls if args[0] == "build")
            for option in ("--pull=false", "--network=none", "--platform=linux/arm64",
                           f"--label=org.racecraft.verification={EXECUTION_ID}"):
                self.assertIn(option, build)
            self.assertEqual(sum(args[0] == "build" for args in calls), 1)
            self.assertIn(["image", "rm", "--no-prune", self.tag], calls)

    def test_existing_tag_and_invalid_base_never_build_or_remove(self):
        for existing, base in ((True, self.base), (False, {**self.base, "Architecture": "amd64"})):
            def call(args, timeout, check=True):
                if args[:2] == ["image", "inspect"]:
                    return {"stdout": json.dumps([base]).encode()}
                return {"stdout": self.built_id.encode() if existing else b""}
            client = SimpleNamespace(call=Mock(side_effect=call))
            with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
                execute_image(client, {".": (0o755, None)}, REFERENCE, ["python3"], EXECUTION_ID,
                              Path(directory) / "evidence", 30)
            self.assertFalse(any(item.args[0][0] == "build" or item.args[0][:2] == ["image", "rm"]
                                 for item in client.call.call_args_list))

    def test_failed_build_is_not_retried_or_launched_and_cleanup_is_uncertain(self):
        def call(args, timeout, check=True):
            if args[:2] == ["image", "inspect"]:
                return {"stdout": json.dumps([self.base]).encode()}
            if args[0] == "build":
                raise ValueError("build transport timed out")
            return {"stdout": b""}
        client = SimpleNamespace(call=Mock(side_effect=call))
        with tempfile.TemporaryDirectory() as directory, \
             patch("speckit_pro_runner.verification_docker_image.execute_container") as launch:
            result = execute_image(client, {".": (0o755, None)}, REFERENCE, ["python3"], EXECUTION_ID,
                                   Path(directory) / "evidence", 30)
        launch.assert_not_called()
        self.assertFalse(result["completed"] or result["image_tag_cleanup_confirmed"])
        self.assertEqual(sum(item.args[0][0] == "build" for item in client.call.call_args_list), 1)
        self.assertIn("failure", result)

    def test_image_cleanup_refuses_unknown_identity_owner_or_daemon_errors(self):
        for info in ({**self.built, "Id": IMAGE_ID}, {**self.built, "Config": None},
                     {**self.built, "RepoTags": []}):
            client = SimpleNamespace(call=Mock(side_effect=[{"stdout": self.built_id.encode()},
                                                           {"stdout": json.dumps([info]).encode()}]))
            self.assertFalse(cleanup_image(client, self.built_id, EXECUTION_ID))
            self.assertFalse(any(item.args[0][:2] == ["image", "rm"] for item in client.call.call_args_list))
        client = SimpleNamespace(call=Mock(side_effect=ValueError("daemon unavailable")))
        self.assertFalse(cleanup_image(client, self.built_id, EXECUTION_ID))
        self.assertFalse(cleanup_image(client, None, EXECUTION_ID))

    def test_invalid_build_request_is_rejected_before_daemon_access(self):
        client = SimpleNamespace(call=Mock())
        for reference, argv, timeout in (("python:latest", ["python3"], 30),
                                          (REFERENCE, ["python3", "bad\u0000arg"], 30),
                                          (REFERENCE, ["python3"], float("inf")),
                                          (REFERENCE, ["python3"], 0)):
            with self.subTest(reference=reference, timeout=timeout), tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
                execute_image(client, {".": (0o755, None)}, reference, argv, EXECUTION_ID,
                              Path(directory) / "evidence", timeout)
        client.call.assert_not_called()


if __name__ == "__main__":
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case)
                               for case in (DockerInputTests, DockerPolicyTests, DockerEntrypointTests, DockerRuntimeTests, DockerReadbackTests, DockerImageTests))
    raise SystemExit(run_counted(suite, label="test-verification-docker"))
