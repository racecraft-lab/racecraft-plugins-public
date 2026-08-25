#!/usr/bin/env python3
"""Stdlib-only tests for XPLAT-006 mutation-capable runner helpers."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
import unittest
import hashlib
import ctypes
import errno
from pathlib import Path, PosixPath
from types import SimpleNamespace
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "mutation-helpers"
CONTRACT_DIR = FIXTURE_DIR / "contracts"
REQUEST_SCHEMA = CONTRACT_DIR / "mutation-helper-request.schema.json"
RESULT_SCHEMA = CONTRACT_DIR / "mutation-helper-result.schema.json"
PROMOTION_SCHEMA = CONTRACT_DIR / "helper-promotion-record.schema.json"
CODEX_AGENT_ROUTING_CASES = FIXTURE_DIR / "codex-agent-routing" / "cases.json"


class FakeWindowsKernel32:
    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
    CREATE_NEW = 1
    OPEN_EXISTING = 3
    GENERIC_WRITE = 0x40000000
    DELETE = 0x00010000
    ERROR_FILE_NOT_FOUND = 2
    ERROR_ACCESS_DENIED = 5
    ERROR_ALREADY_EXISTS = 183
    FILE_ATTRIBUTE_READONLY = 0x00000001
    FILE_ATTRIBUTE_DIRECTORY = 0x00000010
    FILE_ATTRIBUTE_NORMAL = 0x00000080
    FILE_BEGIN = 0

    def __init__(self) -> None:
        self.next_handle = 1000
        self.handles: dict[int, dict[str, object]] = {}
        self.last_error = 0
        self._chmod = os.chmod
        self.createfile_calls: list[dict[str, object]] = []
        self.rename_calls: list[dict[str, object]] = []
        self.file_basic_info_calls: list[dict[str, object]] = []
        self.file_disposition_calls: list[dict[str, object]] = []
        self.deletefile_calls: list[PosixPath] = []
        self.close_handles: list[int] = []
        self.events: list[str] = []
        self.fail_close = False
        self.fail_close_once_paths: set[PosixPath] = set()
        self.fail_close_paths: set[PosixPath] = set()
        self.fail_hardlink = False
        self.fail_write = False
        self.fail_file_info = False
        self.deny_delete_paths: set[PosixPath] = set()
        self.before_deletefile = None
        self.before_file_disposition = None

    def get_last_error(self) -> int:
        return self.last_error

    def set_last_error(self, error: int) -> None:
        self.last_error = error

    def CreateFileW(
        self,
        path: object,
        desired_access: int,
        share_mode: int,
        security_attributes: object,
        creation_disposition: int,
        flags_and_attributes: int,
        template_file: object,
    ) -> int:
        del security_attributes, template_file
        target = PosixPath(str(path))
        self.createfile_calls.append(
            {
                "path": target,
                "desired_access": desired_access,
                "share_mode": share_mode,
                "creation_disposition": creation_disposition,
                "flags_and_attributes": flags_and_attributes,
            }
        )
        if creation_disposition == self.OPEN_EXISTING and self._has_exclusive_open(target):
            self.set_last_error(self.ERROR_ACCESS_DENIED)
            return self.INVALID_HANDLE_VALUE
        try:
            if creation_disposition == self.CREATE_NEW:
                flags = os.O_RDWR | os.O_CREAT | os.O_EXCL
                fd = os.open(target, flags, 0o600)
            elif creation_disposition == self.OPEN_EXISTING:
                if not target.exists():
                    self.set_last_error(self.ERROR_FILE_NOT_FOUND)
                    return self.INVALID_HANDLE_VALUE
                flags = os.O_RDWR if desired_access & self.GENERIC_WRITE else os.O_RDONLY
                fd = os.open(target, flags)
            else:
                self.set_last_error(self.ERROR_ACCESS_DENIED)
                return self.INVALID_HANDLE_VALUE
        except FileExistsError:
            self.set_last_error(self.ERROR_ALREADY_EXISTS)
            return self.INVALID_HANDLE_VALUE
        except FileNotFoundError:
            self.set_last_error(self.ERROR_FILE_NOT_FOUND)
            return self.INVALID_HANDLE_VALUE
        except OSError:
            self.set_last_error(self.ERROR_ACCESS_DENIED)
            return self.INVALID_HANDLE_VALUE
        handle = self.next_handle
        self.next_handle += 1
        self.handles[handle] = {"fd": fd, "path": target, "share_mode": share_mode}
        if target.is_dir():
            self.events.append(f"CreateFileW:dir:{handle}")
        return handle

    def _has_exclusive_open(self, target: PosixPath) -> bool:
        return any(record["path"] == target and record["share_mode"] == 0 for record in self.handles.values())

    def CloseHandle(self, handle: int) -> int:
        self.close_handles.append(handle)
        self.events.append(f"CloseHandle:{handle}")
        record = self.handles.get(handle)
        if record is not None and PosixPath(record["path"]) in self.fail_close_once_paths:
            self.fail_close_once_paths.remove(PosixPath(record["path"]))
            self.set_last_error(6)
            return 0
        if record is not None and PosixPath(record["path"]) in self.fail_close_paths:
            self.set_last_error(6)
            return 0
        record = self.handles.pop(handle, None)
        if record is not None:
            try:
                os.close(int(record["fd"]))
            except OSError:
                pass
        if self.fail_close:
            self.set_last_error(6)
            return 0
        return 1

    def GetFileInformationByHandle(self, handle: int, info_pointer: object) -> int:
        if self.fail_file_info:
            self.set_last_error(self.ERROR_ACCESS_DENIED)
            return 0
        record = self.handles[handle]
        fd = int(record["fd"])
        path = PosixPath(record["path"])
        metadata = os.fstat(fd)
        info = info_pointer._obj
        info.dwFileAttributes = self.FILE_ATTRIBUTE_DIRECTORY if stat.S_ISDIR(metadata.st_mode) else 0x00000080
        if not stat.S_ISDIR(metadata.st_mode) and stat.S_IMODE(metadata.st_mode) & 0o222 == 0:
            info.dwFileAttributes |= self.FILE_ATTRIBUTE_READONLY
        info.dwVolumeSerialNumber = metadata.st_dev & 0xFFFFFFFF
        info.nFileSizeHigh = (metadata.st_size >> 32) & 0xFFFFFFFF
        info.nFileSizeLow = metadata.st_size & 0xFFFFFFFF
        info.nNumberOfLinks = metadata.st_nlink
        info.nFileIndexHigh = (metadata.st_ino >> 32) & 0xFFFFFFFF
        info.nFileIndexLow = metadata.st_ino & 0xFFFFFFFF
        if path.is_dir():
            info.dwFileAttributes |= self.FILE_ATTRIBUTE_DIRECTORY
        return 1

    def ReadFile(
        self,
        handle: int,
        buffer: object,
        bytes_to_read: int,
        bytes_read_pointer: object,
        overlapped: object,
    ) -> int:
        del overlapped
        data = os.read(int(self.handles[handle]["fd"]), bytes_to_read)
        ctypes.memmove(buffer, data, len(data))
        bytes_read_pointer._obj.value = len(data)
        return 1

    def WriteFile(
        self,
        handle: int,
        buffer: object,
        bytes_to_write: int,
        bytes_written_pointer: object,
        overlapped: object,
    ) -> int:
        del overlapped
        data = ctypes.string_at(buffer, bytes_to_write)
        written = os.write(int(self.handles[handle]["fd"]), data)
        bytes_written_pointer._obj.value = written
        if self.fail_write:
            self.set_last_error(self.ERROR_ACCESS_DENIED)
            return 0
        return 1

    def FlushFileBuffers(self, handle: int) -> int:
        try:
            os.fsync(int(self.handles[handle]["fd"]))
        except OSError:
            return 0
        return 1

    def SetFilePointerEx(self, handle: int, distance: object, new_pointer: object, move_method: int) -> int:
        del new_pointer
        if move_method != self.FILE_BEGIN:
            self.set_last_error(self.ERROR_ACCESS_DENIED)
            return 0
        offset = int(getattr(distance, "value", distance))
        try:
            os.lseek(int(self.handles[handle]["fd"]), offset, os.SEEK_SET)
        except OSError:
            self.set_last_error(self.ERROR_ACCESS_DENIED)
            return 0
        return 1

    def SetFileInformationByHandle(self, handle: int, info_class: int, rename_info_buffer: object, buffer_size: int) -> int:
        if info_class == 0:
            del buffer_size
            basic_info_buffer = getattr(rename_info_buffer, "_obj", rename_info_buffer)
            basic_info = FakeWindowsFileBasicInfo.from_buffer(basic_info_buffer)
            target = PosixPath(self.handles[handle]["path"])
            attributes = int(basic_info.FileAttributes)
            self.file_basic_info_calls.append({"handle": handle, "path": target, "attributes": attributes})
            self._chmod(target, 0o400 if attributes & self.FILE_ATTRIBUTE_READONLY else 0o600)
            return 1
        if info_class == 4:
            disposition_buffer = getattr(rename_info_buffer, "_obj", rename_info_buffer)
            disposition = FakeWindowsFileDispositionInfo.from_buffer(disposition_buffer)
            if buffer_size != ctypes.sizeof(FakeWindowsFileDispositionInfo) or int(disposition.DeleteFile) != 1:
                self.set_last_error(self.ERROR_ACCESS_DENIED)
                return 0
            target = PosixPath(self.handles[handle]["path"])
            fd = int(self.handles[handle]["fd"])
            original = os.fstat(fd)
            if self.before_file_disposition is not None:
                self.before_file_disposition(target)
            self.file_disposition_calls.append(
                {"handle": handle, "path": target, "buffer_size": buffer_size, "delete_file": int(disposition.DeleteFile)}
            )
            try:
                if stat.S_IMODE(os.fstat(fd).st_mode) & 0o222 == 0:
                    self.set_last_error(self.ERROR_ACCESS_DENIED)
                    return 0
                try:
                    current = target.stat()
                except FileNotFoundError:
                    return 1
                if (current.st_dev, current.st_ino) == (original.st_dev, original.st_ino):
                    os.unlink(target)
            except FileNotFoundError:
                self.set_last_error(self.ERROR_FILE_NOT_FOUND)
                return 0
            except OSError:
                self.set_last_error(self.ERROR_ACCESS_DENIED)
                return 0
            return 1
        del buffer_size
        source = PosixPath(self.handles[handle]["path"])
        header = install_windows_rename_header(rename_info_buffer)
        name = install_windows_rename_name(rename_info_buffer, header.FileNameLength)
        root = self.handles[int(header.RootDirectory)]["path"]
        target = PosixPath(root) / name
        self.rename_calls.append(
            {
                "info_class": info_class,
                "replace": bool(header.ReplaceIfExists),
                "root": int(header.RootDirectory),
                "name": name,
            }
        )
        self.events.append("SetFileInformationByHandle")
        if target.exists() and not header.ReplaceIfExists:
            self.set_last_error(self.ERROR_ALREADY_EXISTS)
            return 0
        os.rename(source, target)
        self.handles[handle]["path"] = target
        return 1

    def CreateHardLinkW(self, new_link: object, existing_file: object, security_attributes: object) -> int:
        del security_attributes
        if self.fail_hardlink:
            self.set_last_error(self.ERROR_ACCESS_DENIED)
            return 0
        new_path = PosixPath(str(new_link))
        existing_path = PosixPath(str(existing_file))
        if new_path.exists():
            self.set_last_error(self.ERROR_ALREADY_EXISTS)
            return 0
        os.link(existing_path, new_path)
        return 1

    def DeleteFileW(self, path: object) -> int:
        target = PosixPath(str(path))
        self.deletefile_calls.append(target)
        if self.before_deletefile is not None:
            self.before_deletefile(target)
        if target in self.deny_delete_paths or self._has_exclusive_open(target):
            self.set_last_error(self.ERROR_ACCESS_DENIED)
            return 0
        if target.exists() and stat.S_IMODE(target.stat().st_mode) & 0o222 == 0:
            self.set_last_error(self.ERROR_ACCESS_DENIED)
            return 0
        try:
            os.unlink(target)
        except FileNotFoundError:
            self.set_last_error(self.ERROR_FILE_NOT_FOUND)
            return 0
        return 1


class FakeWindowsFileRenameInfoHeader(ctypes.Structure):
    _fields_ = [
        ("ReplaceIfExists", ctypes.c_int),
        ("RootDirectory", ctypes.c_void_p),
        ("FileNameLength", ctypes.c_uint32),
    ]


class FakeWindowsFileBasicInfo(ctypes.Structure):
    _fields_ = [
        ("CreationTime", ctypes.c_longlong),
        ("LastAccessTime", ctypes.c_longlong),
        ("LastWriteTime", ctypes.c_longlong),
        ("ChangeTime", ctypes.c_longlong),
        ("FileAttributes", ctypes.c_uint32),
    ]


class FakeWindowsFileDispositionInfo(ctypes.Structure):
    _fields_ = [("DeleteFile", ctypes.c_ubyte)]


def install_windows_rename_header(rename_info_buffer: object) -> FakeWindowsFileRenameInfoHeader:
    return FakeWindowsFileRenameInfoHeader.from_buffer(rename_info_buffer)


def windows_file_rename_info_filename_offset() -> int:
    return FakeWindowsFileRenameInfoHeader.FileNameLength.offset + ctypes.sizeof(ctypes.c_uint32)


def install_windows_rename_name(rename_info_buffer: object, byte_length: int) -> str:
    offset = windows_file_rename_info_filename_offset()
    address = ctypes.addressof(rename_info_buffer) + offset
    return ctypes.string_at(address, byte_length).decode("utf-16le")

if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))


from speckit_pro_runner.envelope import RunnerRequest
from speckit_pro_runner.agent_materialization import materialize_agent_policy
from speckit_pro_runner.helpers import mutation, registry


def runner_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(PLUGIN_ROOT) if not existing else f"{PLUGIN_ROOT}{os.pathsep}{existing}"
    return env


def helper_request(
    helper_id: str,
    *,
    operation: str | None = None,
    mode: str = "dry_run",
    inputs: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "request_id": f"test-{helper_id}-{mode}",
        "helper_id": helper_id,
        "operation": operation or helper_id,
        "mode": mode,
        "inputs": inputs or {},
    }


def run_runner(
    request: object,
    *,
    cwd: Path = REPO_ROOT,
    env_overrides: dict[str, str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], dict[str, object], list[dict[str, object]]]:
    env = runner_env()
    if env_overrides:
        env.update(env_overrides)
    completed = subprocess.run(
        [sys.executable, "-m", "speckit_pro_runner"],
        input=json.dumps(request) if not isinstance(request, str) else request,
        text=True,
        capture_output=True,
        cwd=cwd,
        env=env,
        shell=False,
        check=False,
    )
    response = json.loads(completed.stdout) if completed.stdout.strip() else {}
    stderr_records = [json.loads(line) for line in completed.stderr.splitlines() if line.strip()]
    return completed, response, stderr_records


def command_stdin_fixture(command: str) -> Path:
    if "<" not in command:
        raise AssertionError(f"authoritative_command must include a stdin fixture: {command}")
    stdin_path = command.split("<", 1)[1].strip()
    if not stdin_path or any(char.isspace() for char in stdin_path):
        raise AssertionError(f"authoritative_command must use one stdin fixture path: {command}")
    return REPO_ROOT / stdin_path


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def route_policy_digest(value: object) -> str:
    return f"sha256:{hashlib.sha256(canonical_json_bytes(value)).hexdigest()}"


def routing_fixture_document() -> dict[str, object]:
    return json.loads(CODEX_AGENT_ROUTING_CASES.read_text(encoding="utf-8"))


def routing_required_agents() -> list[str]:
    document = routing_fixture_document()
    required = document["required_agents"]
    if not isinstance(required, list):
        raise AssertionError("routing fixture required_agents must be a list")
    return [str(agent) for agent in required]


def routing_optional_helper() -> str:
    helper = routing_fixture_document()["optional_helper"]
    if not isinstance(helper, str):
        raise AssertionError("routing fixture optional_helper must be a string")
    return helper


def route_rendered_optional_helper_bytes() -> bytes:
    helper_source = (PLUGIN_ROOT / "codex-agents" / f"{routing_optional_helper()}.toml").read_text(encoding="utf-8")
    return helper_source.replace(
        'model = "gpt-5.3-codex-spark"\n',
        'model = "gpt-5.3-codex-spark"\nmodel_reasoning_effort = "high"\n',
        1,
    ).encode("utf-8")


def routing_capability_snapshot() -> dict[str, object]:
    document = routing_fixture_document()
    base_case = document["base_case"]
    if not isinstance(base_case, dict) or not isinstance(base_case.get("capability_snapshot"), dict):
        raise AssertionError("routing fixture capability_snapshot must be an object")
    return dict(base_case["capability_snapshot"])


def routing_native_unavailable_snapshot(label: str) -> dict[str, object]:
    snapshot = routing_capability_snapshot()
    snapshot["snapshot_id"] = f"snapshot:g56r-006:{label}"
    snapshot["native_discovery"] = False
    snapshot["available_routes"] = []
    snapshot["child_probe_results"] = []
    return snapshot


def codex_agent_source_roster_document(source_dir: Path | None = None) -> dict[str, object]:
    root = source_dir or PLUGIN_ROOT / "codex-agents"
    files = [
        {"name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in sorted(root.glob("*.toml"), key=lambda item: item.name)
    ]
    return {
        "schema_version": "1.0.0",
        "source_roster_id": route_policy_digest(files),
        "files": files,
    }


def codex_agent_source_digests() -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((PLUGIN_ROOT / "codex-agents").glob("*.toml"), key=lambda item: item.name)
    }


def codex_agent_non_route_contract_digest(agent_name: str) -> str:
    source = PLUGIN_ROOT / "codex-agents" / f"{agent_name}.toml"
    return materialize_agent_policy(
        source_relative_path=f"speckit-pro/codex-agents/{agent_name}.toml",
        source_bytes=source.read_bytes(),
    ).non_route_fields_digest


def route_policy_route(raw: dict[str, object]) -> dict[str, object]:
    return {
        "route_id": raw["route_id"],
        "model": raw["model"],
        "model_reasoning_effort": raw["model_reasoning_effort"],
        "capabilities": list(raw["capabilities"]),
        "probe_id": raw.get("probe_id"),
    }


def finalize_route_policy_manifest(manifest: dict[str, object]) -> dict[str, object]:
    manifest["manifest_id"] = route_policy_digest(
        {key: value for key, value in manifest.items() if key != "manifest_id"}
    )
    return manifest


def valid_route_policy_manifest() -> dict[str, object]:
    document = routing_fixture_document()
    base_case = document["base_case"]
    if not isinstance(base_case, dict) or not isinstance(base_case.get("manifest"), dict):
        raise AssertionError("routing fixture base manifest must be an object")
    base_manifest = base_case["manifest"]
    required_route = route_policy_route(base_manifest["required_route"])
    required_fallback = route_policy_route(base_manifest["required_fallback"])
    helper_route = route_policy_route(base_manifest["helper_route"])
    required_policies = {}
    for agent in routing_required_agents():
        required_policies[agent] = {
            "policy_id": f"policy:{agent}",
            "agent_name": agent,
            "preferred_route": dict(required_route),
            "fallback_routes": [dict(required_fallback)],
            "required_capabilities": list(required_route["capabilities"]),
            "non_route_contract_digest": codex_agent_non_route_contract_digest(agent),
        }
    manifest = {
        "schema_version": base_manifest["schema_version"],
        "manifest_id": "",
        "provenance_id": base_manifest["provenance_id"],
        "source_roster": codex_agent_source_roster_document(),
        "required_agent_policies": required_policies,
        "optional_helper": {
            "helper_name": routing_optional_helper(),
            "policy_id": f"policy:{routing_optional_helper()}",
            "preferred_route": helper_route,
            "fallback_routes": [],
            "no_helper": dict(base_manifest["no_helper"]),
        },
        "bounded_probes": dict(base_manifest["bounded_probes"]),
    }
    return finalize_route_policy_manifest(manifest)


def strict_override_required_miss_manifest(agent_name: str = "analyze-executor") -> dict[str, object]:
    manifest = valid_route_policy_manifest()
    policy = manifest["required_agent_policies"][agent_name]
    policy["fallback_routes"][0]["route_id"] = f"required-fallback-miss:{agent_name}"
    policy["fallback_routes"][0]["model"] = "gpt-5.3-codex-spark"
    return finalize_route_policy_manifest(manifest)


def strict_override_invalid_no_helper_manifest() -> dict[str, object]:
    manifest = valid_route_policy_manifest()
    manifest["optional_helper"]["no_helper"]["allowed"] = False
    manifest["optional_helper"]["no_helper"]["reason"] = "fixture rejects required-only continuation"
    return finalize_route_policy_manifest(manifest)


def strict_override_helper_compatible_manifest() -> dict[str, object]:
    manifest = valid_route_policy_manifest()
    helper_compatible_required_route = {
        "route_id": "required-helper-compatible",
        "model": "gpt-5.3-codex-spark",
        "model_reasoning_effort": "xhigh",
        "capabilities": ["reasoning", "tools"],
        "probe_id": None,
    }
    for policy in manifest["required_agent_policies"].values():
        policy["fallback_routes"].append(dict(helper_compatible_required_route))
    return finalize_route_policy_manifest(manifest)


def bounded_probe_required_manifest() -> dict[str, object]:
    manifest = valid_route_policy_manifest()
    bind_required_primary_probe(manifest)
    return finalize_route_policy_manifest(manifest)


def bind_required_primary_probe(manifest: dict[str, object]) -> None:
    for policy in manifest["required_agent_policies"].values():
        policy["preferred_route"]["probe_id"] = "probe-required-primary"
    manifest["bounded_probes"] = {
        "probe-required-primary": {
            "probe_id": "probe-required-primary",
            "candidate_route_id": "required-primary",
            "purpose": "deterministically establish required primary availability",
            "bounds": {"max_calls": 1},
            "expected_result_shape": {"available": "boolean"},
        }
    }


class MutationHelperTests(unittest.TestCase):
    def assert_response(self, response: dict[str, object], status: str, exit_code: int) -> None:
        self.assertEqual(response["schema_version"], "1.0")
        self.assertEqual(response["status"], status)
        self.assertEqual(response["exit_code"], exit_code)
        self.assertIsNone(response["legacy_exit_code"])
        self.assertIsInstance(response["diagnostics"], list)
        self.assertIsInstance(response["data"], dict)

    @staticmethod
    def fail_on_autopilot_agent_write(real_write: object) -> object:
        def fail_write(
            target: Path,
            content: bytes,
            target_dir: Path,
            identity: tuple[int, int] | None,
            *,
            mode: int | None = None,
            expected_state: object = None,
            cleanup_race_state: object = None,
        ) -> object:
            if target.name == "autopilot-fast-helper.toml":
                raise OSError("injected test failure")
            return real_write(
                target,
                content,
                target_dir,
                identity,
                mode=mode,
                expected_state=expected_state,
                cleanup_race_state=cleanup_race_state,
            )

        return fail_write

    def test_install_subprocess_dispatch_preserves_selected_python_candidate(self) -> None:
        from speckit_pro_runner.helpers import install

        cases = [
            ("py -V:3", ["py", "-3", "-m", "speckit_pro_runner"], ["py", "-3", "-m", "speckit_pro_runner"]),
            ("python3", ["python3", "-m", "speckit_pro_runner"], ["python3", "-m", "speckit_pro_runner"]),
            ("python", ["python", "-m", "speckit_pro_runner"], ["python", "-m", "speckit_pro_runner"]),
        ]
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="{}", stderr="")

        for selected_candidate, argv, expected_argv in cases:
            with self.subTest(selected_candidate=selected_candidate):
                with patch.object(install.subprocess, "run", return_value=completed) as mocked_run:
                    result = install.run_python_runner_subprocess(
                        argv,
                        selected_candidate=selected_candidate,
                        input_text="{}",
                        cwd=REPO_ROOT,
                    )

                self.assertIs(result, completed)
                self.assertEqual(mocked_run.call_args.args[0], expected_argv)
                self.assertIs(mocked_run.call_args.kwargs["shell"], False)

    def temp_repo_path(self, name: str) -> tuple[tempfile.TemporaryDirectory[str], Path, str]:
        tmp = tempfile.TemporaryDirectory(dir=FIXTURE_DIR)
        path = Path(tmp.name) / name
        return tmp, path, path.relative_to(REPO_ROOT).as_posix()

    def temp_clean_git_repo(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        self.run_git(root, "init", "--quiet")
        self.run_git(root, "config", "user.email", "git@github.com")
        self.run_git(root, "config", "user.name", "XPLAT Tests")
        self.run_git(root, "config", "commit.gpgsign", "false")
        (root / ".gitkeep").write_text("fixture\n", encoding="utf-8")
        marker = root / "speckit-pro" / "speckit_pro_runner"
        marker.mkdir(parents=True)
        (marker / ".gitkeep").write_text("runner marker\n", encoding="utf-8")
        self.run_git(root, "add", ".gitkeep")
        self.run_git(root, "add", "speckit-pro/speckit_pro_runner/.gitkeep")
        self.run_git(root, "commit", "--quiet", "-m", "init")
        return tmp, root

    def run_git(self, cwd: Path, *args: str) -> None:
        subprocess.run(
            ["git", *args],
            cwd=cwd,
            text=True,
            capture_output=True,
            shell=False,
            check=True,
        )

    def write_route_policy_manifest(self, root: Path, manifest: dict[str, object], name: str = "route-policy.json") -> Path:
        path = root / ".codex" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def write_valid_route_policy_manifest(self, root: Path, name: str = "route-policy.json") -> Path:
        return self.write_route_policy_manifest(root, valid_route_policy_manifest(), name=name)

    def route_aware_inputs(self, manifest_path: Path, git_root: Path, *, destination: str | None = ".codex/agents") -> dict[str, object]:
        inputs: dict[str, object] = {
            "route_policy_manifest": manifest_path.relative_to(git_root).as_posix(),
            "test_overrides": {"codex_capability_snapshot": routing_capability_snapshot()},
        }
        if destination is not None:
            inputs["destination"] = destination
        return inputs

    def assert_route_aware_snapshot_response(
        self,
        response: dict[str, object],
        *,
        manifest_path: Path,
        git_root: Path,
        expected_snapshot: dict[str, object],
        expected_manifest: dict[str, object] | None = None,
    ) -> None:
        manifest = expected_manifest or valid_route_policy_manifest()
        routing = response["data"]["routing"]
        self.assertEqual(routing["schema_version"], "1.0")
        self.assertEqual(routing["mode"], "route_aware")
        self.assertEqual(routing["manifest"]["path"], manifest_path.relative_to(git_root).as_posix())
        self.assertEqual(routing["manifest"]["manifest_id"], manifest["manifest_id"])
        snapshot = routing["runtime_capability_snapshot"]
        self.assertEqual(snapshot["snapshot_id"], expected_snapshot["snapshot_id"])
        self.assertEqual(snapshot["adapter_id"], expected_snapshot["adapter_id"])
        self.assertEqual(snapshot["child_probe_results"], expected_snapshot["child_probe_results"])
        self.assertEqual(snapshot["observation_evidence"]["available_routes"], expected_snapshot["available_routes"])
        self.assertEqual(snapshot["observation_evidence"]["native_discovery"], expected_snapshot["native_discovery"])

    def assert_route_aware_required_resolution(
        self,
        response: dict[str, object],
        *,
        expected_snapshot: dict[str, object],
        selected_route_id: str = "required-primary",
        expected_attempt_count: int = 1,
    ) -> None:
        routing = response["data"]["routing"]
        required_records = routing["required_agents"]
        required_agents = routing_required_agents()
        self.assertEqual([record["agent_name"] for record in required_records], required_agents)
        self.assertEqual(len(required_records), len(required_agents))
        self.assertEqual(routing["strict_override"]["status"], "absent")
        self.assertFalse(routing["strict_override"]["requested"])
        self.assertEqual(routing["strict_override"]["required_agents_evaluated"], 0)
        self.assertFalse(routing["strict_override"]["fallback_suppressed"])

        for agent_name, record in zip(required_agents, required_records, strict=True):
            with self.subTest(agent_name=agent_name):
                self.assertEqual(record["snapshot_id"], expected_snapshot["snapshot_id"])
                self.assertEqual(record["policy_id"], f"policy:{agent_name}")
                self.assertEqual(record["terminal_outcome"], "resolved")
                self.assertEqual(record["selected_route"]["route_id"], selected_route_id)
                self.assertEqual(record["selected_route"]["model"], "gpt-5.5" if selected_route_id == "required-primary" else "gpt-5.4")
                self.assertEqual(record["selected_route"]["model_reasoning_effort"], "xhigh")
                self.assertEqual(len(record["attempted_routes"]), expected_attempt_count)
                self.assertEqual(record["attempted_routes"][0]["route_id"], "required-primary")
                self.assertEqual(record["attempted_routes"][-1]["outcome"], "selected")
                if expected_attempt_count == 2:
                    self.assertEqual(record["attempted_routes"][0]["outcome"], "rejected")
                    self.assertEqual(record["attempted_routes"][0]["reason"], "route_unavailable")
                    self.assertEqual(record["attempted_routes"][1]["route_id"], "required-fallback")
                self.assertEqual(record["rejection_reasons"], [] if expected_attempt_count == 1 else ["required-primary: route_unavailable"])
                self.assertRegex(record["route_resolution_id"], r"^sha256:[0-9a-f]{64}$")
                self.assertRegex(record["resolved_agent_policy_id"], r"^sha256:[0-9a-f]{64}$")
                self.assertRegex(record["materialization_id"], r"^sha256:[0-9a-f]{64}$")
                proof = record["materialization_proof"]
                source_path = PLUGIN_ROOT / "codex-agents" / f"{agent_name}.toml"
                self.assertEqual(proof["source_path"], f"speckit-pro/codex-agents/{agent_name}.toml")
                self.assertEqual(proof["source_bytes_digest"], f"sha256:{hashlib.sha256(source_path.read_bytes()).hexdigest()}")
                self.assertRegex(proof["destination_bytes_digest"], r"^sha256:[0-9a-f]{64}$")
                self.assertEqual(proof["selected_model"], record["selected_route"]["model"])
                self.assertEqual(proof["selected_model_reasoning_effort"], "xhigh")
                self.assertTrue(proof["non_route_fields_unchanged"])
                self.assertEqual(
                    proof["materializer_binding"]["path"],
                    "speckit-pro/speckit_pro_runner/agent_materialization.py",
                )

    def assert_route_aware_helper_installed(self, response: dict[str, object], *, expected_snapshot: dict[str, object]) -> None:
        helper = response["data"]["routing"]["optional_helper_decision"]
        self.assertEqual(helper["helper_name"], routing_optional_helper())
        self.assertEqual(helper["outcome"], "installed")
        self.assertEqual(helper["terminal_outcome"], "resolved")
        self.assertEqual(helper["snapshot_id"], expected_snapshot["snapshot_id"])
        self.assertEqual(helper["policy_id"], f"policy:{routing_optional_helper()}")
        self.assertEqual(helper["selected_route"]["route_id"], "helper-primary")
        self.assertEqual(helper["selected_route"]["model"], "gpt-5.3-codex-spark")
        self.assertEqual(helper["selected_route"]["model_reasoning_effort"], "high")
        self.assertEqual([attempt["route_id"] for attempt in helper["attempted_routes"]], ["helper-primary"])
        self.assertEqual(helper["rejection_reasons"], [])
        self.assertFalse(helper["no_helper_validation"]["selected"])
        self.assertIsNone(helper["managed_ownership_proof"])
        self.assertEqual(helper["manual_remediation"], [])
        self.assertRegex(helper["route_resolution_id"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(helper["resolved_agent_policy_id"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(helper["materialization_id"], r"^sha256:[0-9a-f]{64}$")

    def assert_route_aware_no_mutation_yet(self, response: dict[str, object]) -> None:
        recovery = response["data"]["routing"]["recovery_or_mutation"]
        mutation = response["data"]["mutation"]
        self.assertEqual(recovery["planned_writes"], mutation["planned_paths"])
        self.assertEqual(recovery["planned_removals"], [])
        self.assertEqual(recovery["applied_writes"], [])
        self.assertEqual(recovery["applied_removals"], [])
        self.assertEqual(recovery["recovery_record"]["rollback_outcome"], "not_required")
        self.assertFalse(recovery["writes_state"])
        self.assertFalse(recovery["restart_required"])

    def assert_route_aware_required_destination_bytes(self, response: dict[str, object], destination: Path) -> None:
        required_records = response["data"]["routing"]["required_agents"]
        for record in required_records:
            agent_name = record["agent_name"]
            target = destination / f"{agent_name}.toml"
            with self.subTest(agent_name=agent_name):
                target_bytes = target.read_bytes()
                target_digest = f"sha256:{hashlib.sha256(target_bytes).hexdigest()}"
                self.assertEqual(target_digest, record["materialization_proof"]["destination_bytes_digest"])
                parsed = tomllib.loads(target_bytes.decode("utf-8"))
                self.assertEqual(parsed["model"], record["selected_route"]["model"])
                self.assertEqual(parsed["model_reasoning_effort"], record["selected_route"]["model_reasoning_effort"])

    def assert_route_aware_rollback_success_evidence(
        self,
        response: dict[str, object],
        destination: Path,
        prior_agent_bytes: dict[str, bytes],
        prior_mode: int,
        failed_agent_name: str,
    ) -> None:
        mutation = response["data"]["mutation"]
        recovery = response["data"]["routing"]["recovery_or_mutation"]
        record = recovery["recovery_record"]
        required_files = [f"{agent_name}.toml" for agent_name in routing_required_agents()]
        failed_target = (destination / f"{failed_agent_name}.toml").resolve().as_posix()

        self.assertEqual(mutation["mutation_status"], "partial_failure")
        self.assertEqual(response["data"]["verification"], {"status": "failed", "matched_files": []})
        self.assertFalse(response["data"]["rollback_succeeded"])
        self.assertTrue(response["data"]["writes_state"])
        self.assertTrue(response["data"]["restart_required"])
        self.assertTrue(recovery["writes_state"])
        self.assertTrue(recovery["restart_required"])
        self.assertRegex(record["pre_state_id"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(record["pre_state_id"], record["final_state_id"])
        self.assertEqual(record["rollback_outcome"], "restored")
        self.assertEqual(record["terminal_outcome"], "uncertain_state")
        self.assertEqual(record["state_status"], "uncertain")
        self.assertEqual([action["reason"] for action in record["manual_remediation"]], ["cleanup_incomplete", "concurrent_file_preserved"])
        self.assertEqual([action["name"] for action in record["prior_state"]], required_files)
        for state in record["prior_state"]:
            agent_name = state["name"].removesuffix(".toml")
            self.assertTrue(state["existed"])
            self.assertEqual(state["mode"], oct(prior_mode))
            self.assertEqual(state["digest"], f"sha256:{hashlib.sha256(prior_agent_bytes[agent_name]).hexdigest()}")

        self.assertEqual(len(record["staged_actions"]), len(required_files))
        self.assertEqual(len(record["applied_actions"]), 1)
        self.assertEqual(record["failed_actions"][0]["operation_id"], mutation["failure_operation"]["operation_id"])
        self.assertEqual(record["failed_actions"][0]["target"], failed_target)
        self.assertEqual([action["name"] for action in record["rolled_back_actions"]], required_files[:1])
        self.assertTrue(any(error["kind"] == "preserved_cleanup_entry" for error in record["cleanup_errors"]))
        self.assertEqual(record["cleanup_actions"], [])
        self.assertEqual(recovery["planned_writes"], mutation["planned_paths"])
        self.assertEqual(recovery["applied_writes"], mutation["touched_paths"])
        self.assertEqual(recovery["planned_removals"], [])
        self.assertEqual(recovery["applied_removals"], [])

        for agent_name, content in prior_agent_bytes.items():
            target = destination / f"{agent_name}.toml"
            with self.subTest(restored_agent=agent_name):
                self.assertEqual(target.read_bytes(), content)
                self.assertEqual(target.stat().st_mode & 0o7777, prior_mode)

    def assert_route_aware_rollback_failure_evidence(
        self,
        response: dict[str, object],
        destination: Path,
        prior_agent_bytes: dict[str, bytes],
        prior_mode: int,
        failed_agent_name: str,
        unrestored_agent_name: str,
    ) -> None:
        mutation = response["data"]["mutation"]
        recovery = response["data"]["routing"]["recovery_or_mutation"]
        record = recovery["recovery_record"]
        failed_target = (destination / f"{failed_agent_name}.toml").resolve().as_posix()
        unrestored_target = (destination / f"{unrestored_agent_name}.toml").resolve().as_posix()

        self.assertEqual(mutation["mutation_status"], "partial_failure")
        self.assertEqual(response["data"]["verification"], {"status": "failed", "matched_files": []})
        self.assertFalse(response["data"]["rollback_succeeded"])
        self.assertTrue(response["data"]["writes_state"])
        self.assertTrue(response["data"]["restart_required"])
        self.assertTrue(recovery["writes_state"])
        self.assertTrue(recovery["restart_required"])
        self.assertRegex(record["pre_state_id"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(record["final_state_id"], r"^sha256:[0-9a-f]{64}$")
        self.assertNotEqual(record["pre_state_id"], record["final_state_id"])
        self.assertEqual(record["rollback_outcome"], "unrestored")
        self.assertEqual(record["terminal_outcome"], "uncertain_state")
        self.assertEqual(record["state_status"], "uncertain")
        self.assertEqual(record["failed_actions"][0]["operation_id"], mutation["failure_operation"]["operation_id"])
        self.assertEqual(record["failed_actions"][0]["target"], failed_target)
        self.assertEqual(record["unrestored_actions"], [{"name": f"{unrestored_agent_name}.toml", "target": unrestored_target}])
        self.assertEqual(
            record["rollback_errors"],
            [{"name": f"{unrestored_agent_name}.toml", "target": unrestored_target, "error": "OSError"}],
        )
        self.assertTrue(any(item["reason"] == "rollback_unrestored" for item in record["manual_remediation"]))
        if record["cleanup_errors"]:
            self.assertTrue(any(item["reason"] == "cleanup_incomplete" for item in record["manual_remediation"]))
        remediation = next(item for item in record["manual_remediation"] if item["reason"] == "rollback_unrestored")
        self.assertEqual(remediation["action_type"], "manual_remediation")
        self.assertEqual(remediation["reason"], "rollback_unrestored")
        self.assertEqual(remediation["paths"], [unrestored_target])
        self.assertIn("Restart", remediation["summary"])
        self.assertEqual(recovery["planned_writes"], mutation["planned_paths"])
        self.assertEqual(recovery["applied_writes"], mutation["touched_paths"])
        self.assertEqual(recovery["planned_removals"], [])
        self.assertEqual(recovery["applied_removals"], [])

        for agent_name, content in prior_agent_bytes.items():
            target = destination / f"{agent_name}.toml"
            with self.subTest(rollback_failure_agent=agent_name):
                if agent_name == unrestored_agent_name:
                    self.assertNotEqual(target.read_bytes(), content)
                else:
                    self.assertEqual(target.read_bytes(), content)
                    self.assertEqual(target.stat().st_mode & 0o7777, prior_mode)

    def assert_route_aware_apply_mutation_evidence(self, response: dict[str, object]) -> None:
        mutation = response["data"]["mutation"]
        recovery = response["data"]["routing"]["recovery_or_mutation"]
        self.assertEqual(mutation["mutation_status"], "applied")
        self.assertEqual(recovery["planned_writes"], mutation["planned_paths"])
        self.assertEqual(
            sorted([*recovery["applied_writes"], *recovery["applied_removals"]]),
            sorted(mutation["touched_paths"]),
        )
        self.assertTrue(recovery["writes_state"])
        self.assertTrue(recovery["restart_required"])
        self.assertTrue(response["data"]["writes_state"])
        self.assertTrue(response["data"]["restart_required"])

    def assert_strict_required_override_evidence(
        self,
        response: dict[str, object],
        *,
        model: str,
        expected_status: str,
    ) -> None:
        routing = response["data"]["routing"]
        strict = routing["strict_override"]
        self.assertTrue(strict["requested"])
        self.assertEqual(strict["status"], expected_status)
        self.assertEqual(strict["model"], model)
        self.assertEqual(strict["required_agents_evaluated"], len(routing_required_agents()))
        self.assertTrue(strict["fallback_suppressed"])
        self.assertEqual(len(strict["evaluated_tuples"]), len(routing_required_agents()))

        required_agents = routing_required_agents()
        self.assertEqual([item["agent_name"] for item in strict["evaluated_tuples"]], required_agents)
        self.assertEqual([record["agent_name"] for record in routing["required_agents"]], required_agents)
        for record in routing["required_agents"]:
            with self.subTest(agent_name=record["agent_name"]):
                self.assertEqual(len(record["attempted_routes"]), 1)
                attempt = record["attempted_routes"][0]
                self.assertEqual(attempt["model"], model)
                self.assertEqual(attempt["model_reasoning_effort"], "xhigh")
                self.assertTrue(attempt["route_id"].startswith(f"strict-override:{record['agent_name']}:"))
                if record["terminal_outcome"] == "resolved":
                    self.assertEqual(attempt["outcome"], "selected")
                    self.assertEqual(record["selected_route"]["route_id"], attempt["route_id"])
                    self.assertEqual(record["selected_route"]["model"], model)

    def assert_strict_required_override_zero_mutation(self, response: dict[str, object]) -> None:
        mutation = response["data"]["mutation"]
        recovery = response["data"]["routing"]["recovery_or_mutation"]
        self.assertEqual(mutation["planned_operations"], [])
        self.assertEqual(mutation["applied_operations"], [])
        self.assertEqual(mutation["planned_paths"], [])
        self.assertEqual(mutation["touched_paths"], [])
        self.assertFalse(mutation["live_mutation"])
        self.assertEqual(recovery["planned_writes"], [])
        self.assertEqual(recovery["planned_removals"], [])
        self.assertEqual(recovery["applied_writes"], [])
        self.assertEqual(recovery["applied_removals"], [])
        self.assertFalse(recovery["writes_state"])
        self.assertFalse(recovery["restart_required"])
        self.assertFalse(response["data"]["writes_state"])
        self.assertFalse(response["data"]["restart_required"])

    def assert_route_aware_required_miss_zero_mutation(
        self,
        response: dict[str, object],
        *,
        expected_snapshot: dict[str, object],
        prior_agent_bytes: dict[str, bytes],
        destination: Path,
    ) -> None:
        mutation = response["data"]["mutation"]
        recovery = response["data"]["routing"]["recovery_or_mutation"]
        record = recovery["recovery_record"]
        self.assertEqual(mutation["mutation_status"], "blocked")
        self.assertEqual(mutation["planned_operations"], [])
        self.assertEqual(mutation["applied_operations"], [])
        self.assertEqual(mutation["planned_paths"], [])
        self.assertEqual(mutation["touched_paths"], [])
        self.assertFalse(mutation["live_mutation"])
        self.assertEqual(recovery["planned_writes"], [])
        self.assertEqual(recovery["planned_removals"], [])
        self.assertEqual(recovery["applied_writes"], [])
        self.assertEqual(recovery["applied_removals"], [])
        self.assertFalse(recovery["writes_state"])
        self.assertFalse(recovery["restart_required"])
        self.assertFalse(response["data"]["writes_state"])
        self.assertFalse(response["data"]["restart_required"])
        self.assertEqual(record["terminal_outcome"], "no_mutation")
        self.assertEqual(record["no_mutation_reason"], "required_route_unresolved")
        self.assertEqual(record["rollback_outcome"], "not_required")
        self.assertEqual(record["manual_remediation"], [])
        self.assertEqual(record["staged_actions"], [])
        self.assertEqual(record["applied_actions"], [])
        self.assertEqual(record["rolled_back_actions"], [])
        self.assertEqual(record["cleanup_actions"], [])
        self.assertEqual(record["cleanup_errors"], [])
        self.assertEqual(record["failed_actions"], [])
        self.assertRegex(record["pre_state_id"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(record["pre_state_id"], record["final_state_id"])

        records = response["data"]["routing"]["required_agents"]
        self.assertEqual([item["agent_name"] for item in records], routing_required_agents())
        for item in records:
            agent_name = item["agent_name"]
            with self.subTest(agent_name=agent_name):
                self.assertEqual(item["snapshot_id"], expected_snapshot["snapshot_id"])
                self.assertEqual(item["terminal_outcome"], "unresolved")
                self.assertIsNone(item["selected_route"])
                self.assertIsNone(item["resolved_agent_policy_id"])
                self.assertIsNone(item["materialization_id"])
                self.assertIsNone(item["materialization_proof"])
                self.assertEqual([attempt["route_id"] for attempt in item["attempted_routes"]], ["required-primary", "required-fallback"])
                self.assertEqual([attempt["outcome"] for attempt in item["attempted_routes"]], ["rejected", "rejected"])
                self.assertEqual([attempt["reason"] for attempt in item["attempted_routes"]], ["route_unavailable", "route_unavailable"])
                self.assertEqual(
                    item["rejection_reasons"],
                    ["required-primary: route_unavailable", "required-fallback: route_unavailable"],
                )
                self.assertEqual((destination / f"{agent_name}.toml").read_bytes(), prior_agent_bytes[agent_name])

    def assert_strict_helper_override_evidence(
        self,
        response: dict[str, object],
        *,
        model: str,
        helper_status: str,
        helper_outcome: str,
    ) -> None:
        strict = response["data"]["routing"]["strict_override"]
        helper = response["data"]["routing"]["optional_helper_decision"]
        self.assertTrue(strict["requested"])
        self.assertEqual(strict["model"], model)
        self.assertTrue(strict["helper_evaluated"])
        helper_evidence = strict["helper_tuple"]
        self.assertEqual(helper_evidence["helper_name"], routing_optional_helper())
        self.assertEqual(helper_evidence["model"], model)
        self.assertEqual(helper_evidence["status"], helper_status)
        self.assertEqual(helper["outcome"], helper_outcome)
        self.assertEqual(len(helper["attempted_routes"]), 1)
        self.assertEqual(helper["attempted_routes"][0]["model"], model)
        self.assertTrue(helper["attempted_routes"][0]["route_id"].startswith(f"strict-override:{routing_optional_helper()}:"))

    def assert_route_aware_helper_omitted_no_file(self, response: dict[str, object], destination: Path) -> None:
        helper = response["data"]["routing"]["optional_helper_decision"]
        self.assertEqual(helper["helper_name"], routing_optional_helper())
        self.assertEqual(helper["outcome"], "omitted")
        self.assertEqual(helper["terminal_outcome"], "omitted")
        self.assertIsNone(helper["selected_route"])
        self.assertIsNone(helper["resolved_agent_policy_id"])
        self.assertIsNone(helper["materialization_id"])
        self.assertIsNone(helper["materialization_proof"])
        self.assertTrue(helper["no_helper_validation"]["allowed"])
        self.assertTrue(helper["no_helper_validation"]["selected"])
        self.assertEqual(helper["no_helper_validation"]["existing_helper_state"], "absent")
        self.assertEqual(helper["managed_ownership_proof"], {"status": "not_required", "reason": "helper_absent"})
        self.assertEqual(helper["manual_remediation"], [])
        self.assertEqual(len(helper["attempted_routes"]), 1)
        self.assertEqual(helper["attempted_routes"][0]["route_id"], "helper-primary")
        self.assertEqual(helper["attempted_routes"][0]["outcome"], "rejected")
        self.assertEqual(helper["attempted_routes"][0]["reason"], "route_unavailable")
        self.assertEqual(helper["rejection_reasons"], ["helper-primary: route_unavailable"])
        self.assertFalse((destination / f"{routing_optional_helper()}.toml").exists())

    def assert_route_aware_managed_helper_removal(
        self,
        response: dict[str, object],
        *,
        proof_status: str,
    ) -> None:
        helper = response["data"]["routing"]["optional_helper_decision"]
        self.assertEqual(helper["outcome"], "removed")
        self.assertEqual(helper["terminal_outcome"], "removed")
        self.assertTrue(helper["no_helper_validation"]["allowed"])
        self.assertTrue(helper["no_helper_validation"]["selected"])
        self.assertEqual(helper["no_helper_validation"]["existing_helper_state"], "managed")
        proof = helper["managed_ownership_proof"]
        self.assertEqual(proof["status"], proof_status)
        self.assertEqual(proof["helper_name"], routing_optional_helper())
        self.assertRegex(proof["existing_digest"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(helper["manual_remediation"], [])

    def assert_route_aware_helper_removal_evidence(self, response: dict[str, object], destination: Path) -> None:
        mutation = response["data"]["mutation"]
        recovery = response["data"]["routing"]["recovery_or_mutation"]
        helper_path = (destination / f"{routing_optional_helper()}.toml").resolve().as_posix()
        self.assertIn(helper_path, recovery["planned_removals"])
        self.assertNotIn(helper_path, recovery["planned_writes"])
        for operation in mutation["planned_operations"]:
            if operation.get("target") == helper_path:
                self.assertEqual(operation["kind"], "remove_file")
                break
        else:
            raise AssertionError("helper removal operation was not planned")

    def assert_route_aware_unmanaged_helper_preserved(
        self,
        response: dict[str, object],
        destination: Path,
    ) -> None:
        helper_path = (destination / f"{routing_optional_helper()}.toml").resolve().as_posix()
        helper = response["data"]["routing"]["optional_helper_decision"]
        self.assertEqual(helper["outcome"], "preserved")
        self.assertEqual(helper["terminal_outcome"], "preserved")
        self.assertTrue(helper["no_helper_validation"]["allowed"])
        self.assertTrue(helper["no_helper_validation"]["selected"])
        self.assertEqual(helper["no_helper_validation"]["existing_helper_state"], "unmanaged")
        proof = helper["managed_ownership_proof"]
        self.assertEqual(proof["status"], "absent")
        self.assertEqual(proof["reason"], "ownership_proof_absent")
        self.assertEqual(proof["helper_name"], routing_optional_helper())
        self.assertEqual(proof["destination"], helper_path)
        self.assertRegex(proof["existing_digest"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(len(helper["manual_remediation"]), 1)
        remediation = helper["manual_remediation"][0]
        self.assertEqual(remediation["action_type"], "manual_remediation")
        self.assertEqual(remediation["reason"], "unmanaged_helper_preserved")
        self.assertEqual(remediation["path"], helper_path)
        self.assertIn("preserved", remediation["summary"])

    def assert_route_aware_helper_preserved_without_removal(
        self,
        response: dict[str, object],
        destination: Path,
        helper_bytes: bytes,
    ) -> None:
        mutation = response["data"]["mutation"]
        recovery = response["data"]["routing"]["recovery_or_mutation"]
        helper_path = destination / f"{routing_optional_helper()}.toml"
        helper_path_text = helper_path.resolve().as_posix()
        self.assertEqual(helper_path.read_bytes(), helper_bytes)
        self.assertNotIn(helper_path_text, recovery["planned_removals"])
        self.assertNotIn(helper_path_text, recovery["applied_removals"])
        self.assertNotIn(helper_path_text, recovery["planned_writes"])
        self.assertNotIn(helper_path_text, recovery["applied_writes"])
        self.assertFalse(
            any(
                operation.get("target") == helper_path_text
                for operation in [*mutation["planned_operations"], *mutation["applied_operations"]]
            )
        )

    def assert_schema_contract_response(self, response: dict[str, object], result_schema: dict[str, object]) -> None:
        self.assertIn(response["status"], result_schema["properties"]["status"]["enum"])
        self.assertIsInstance(response["diagnostics"], list)
        diagnostic_schema = result_schema["$defs"]["diagnostic"]
        for diag in response["diagnostics"]:
            self.assertIsInstance(diag, dict)
            for required in diagnostic_schema["required"]:
                self.assertIn(required, diag)
            self.assertEqual(diag["source"], "runner")
        mutation = response["data"].get("mutation")
        if mutation is None:
            return
        mutation_schema = result_schema["$defs"]["mutation"]
        for required in mutation_schema["required"]:
            self.assertIn(required, mutation)
        self.assertIn(mutation["mutation_status"], mutation_schema["properties"]["mutation_status"]["enum"])
        self.assertIsInstance(mutation["dirty_worktree"], bool)
        operation_schema = result_schema["$defs"]["operation_record"]
        for field in ["planned_operations", "applied_operations", "skipped_operations", "no_op_operations"]:
            for operation in mutation[field]:
                self.assertIn(operation["kind"], operation_schema["properties"]["kind"]["enum"])
                if operation["kind"] == "write_file":
                    self.assertIn("target", operation)
                    self.assertNotIn("command", operation)
                if operation["kind"] == "command_plan":
                    self.assertIn("command", operation)
                    self.assertNotIn("target", operation)

    def test_mutation_registry_lists_promoted_contracts_without_cutover(self) -> None:
        promotion_schema = json.loads(PROMOTION_SCHEMA.read_text(encoding="utf-8"))
        completed, response, stderr_records = run_runner(
            helper_request("mutation-registry-dispatch", operation="mutation-registry-dispatch", mode="read_only")
        )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(stderr_records, [])
        self.assert_response(response, "ok", 0)
        data = response["data"]
        helper_ids = [record["helper_id"] for record in data["helpers"]]
        self.assertIn("doctor-preflight", helper_ids)
        self.assertIn("generate-pr-body", helper_ids)
        self.assertIn("relocate-process-artifacts", helper_ids)
        self.assertEqual(data["active_cutover"], False)
        self.assertEqual(data["mode"], "mutation")
        for record in data["helpers"]:
            self.assertNotIn("script", record)
            self.assertNotEqual(record["promotion_status"], "python_authoritative")
            active_record = {key: value for key, value in record.items() if key != "inactive_provenance"}
            self.assertNotIn(".sh", json.dumps(active_record, sort_keys=True))
            if record["promotion_status"] in {"deferred", "out_of_scope"}:
                self.assertEqual(record["authoritative_command"], "")
            else:
                self.assertTrue(command_stdin_fixture(record["authoritative_command"]).is_file())
            promotion = record["promotion"]
            for required in promotion_schema["required"]:
                self.assertIn(required, promotion)
            self.assertEqual(promotion["helper_id"], record["helper_id"])
            self.assertIn(promotion["promotion_status"], promotion_schema["properties"]["promotion_status"]["enum"])
        prior_scripts = {
            record["helper_id"]: record.get("inactive_provenance", {}).get("prior_script")
            for record in data["helpers"]
        }
        self.assertIsNone(prior_scripts["install-codex-agents"])
        install_record = next(record for record in data["helpers"] if record["helper_id"] == "install-codex-agents")
        self.assertEqual(install_record["promotion"]["bash_reference_ids"], ["install-codex-agents"])
        self.assertEqual(prior_scripts["install-curated-set"], "speckit-pro/scripts/install-curated-set.sh")
        self.assertEqual(prior_scripts["generate-pr-body"], "speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh")
        self.assertEqual(prior_scripts["multi-pr-emission"], "speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh")
        rollbacks = {
            record["helper_id"]: record["promotion"]["rollback"]
            for record in data["helpers"]
        }
        self.assertEqual(
            rollbacks["install-codex-agents"],
            "Retry in dry_run mode and preserve the previous same-named Codex agent files before applying again.",
        )
        self.assertEqual(
            rollbacks["install-curated-set"],
            "Keep install-curated-set deferred until a Python runner implementation is promoted.",
        )
        self.assertEqual(
            rollbacks["generate-pr-body"],
            "Retry the registered generate-pr-body operation in dry_run mode before applying again.",
        )
        self.assertEqual(
            rollbacks["multi-pr-emission"],
            "Keep live PR mutation deferred; use the registered multi-pr-emission operation only for command-plan capture.",
        )

    def test_codex_source_roster_excludes_sweep_roles_and_includes_optional_helper(self) -> None:
        from speckit_pro_runner.helpers import install

        roster = install.codex_agent_source_roster(PLUGIN_ROOT / "codex-agents")
        self.assertNotIn("code", roster)
        source_names = [record["name"] for record in roster["files"]]
        self.assertEqual(source_names, list(install.CODEX_SOURCE_AGENT_TOML_NAMES))
        self.assertEqual(len(source_names), 11)
        self.assertNotIn("sweep-classifier.toml", source_names)
        self.assertNotIn("sweep-analyst.toml", source_names)
        self.assertIn(f"{install.CODEX_OPTIONAL_HELPER_NAME}.toml", source_names)
        self.assertEqual(registry.CODEX_REQUIRED_AGENT_NAMES, tuple(routing_required_agents()))
        self.assertEqual(registry.CODEX_OPTIONAL_HELPER_NAME, routing_optional_helper())

        with tempfile.TemporaryDirectory() as source_tmp:
            fake_plugin = Path(source_tmp) / "speckit-pro"
            shutil.copytree(PLUGIN_ROOT / "codex-agents", fake_plugin / "codex-agents")
            (fake_plugin / "codex-agents" / "autopilot-fast-helper.toml").unlink()

            missing_helper = install.codex_agent_source_roster(fake_plugin / "codex-agents")

        self.assertEqual(missing_helper["code"], "incomplete_agent_bundle")
        self.assertEqual(missing_helper["details"]["missing_files"], ["autopilot-fast-helper.toml"])

    def test_codex_route_policy_manifest_loads_strict_roster_metadata(self) -> None:
        from speckit_pro_runner.helpers import install

        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            manifest = valid_route_policy_manifest()
            manifest_path = self.write_route_policy_manifest(git_root, manifest)

            loaded = install.load_codex_route_policy_manifest(
                manifest_path.relative_to(git_root).as_posix(),
                git_root,
                PLUGIN_ROOT / "codex-agents",
            )

        self.assertNotIn("code", loaded)
        self.assertEqual(loaded["path"], ".codex/route-policy.json")
        self.assertEqual(loaded["schema_version"], "1.0.0")
        self.assertEqual(loaded["manifest_id"], manifest["manifest_id"])
        self.assertEqual(loaded["source_roster_id"], manifest["source_roster"]["source_roster_id"])
        self.assertEqual(loaded["provenance_id"], manifest["provenance_id"])
        self.assertEqual(loaded["required_agents"], routing_required_agents())
        self.assertEqual(loaded["optional_helper"], routing_optional_helper())
        self.assertEqual(loaded["source_files"], [record["name"] for record in manifest["source_roster"]["files"]])

    def test_codex_route_policy_manifest_rejects_closed_schema_version_digest_and_rosters(self) -> None:
        from speckit_pro_runner.helpers import install

        def mutated_manifest(
            edit: object,
            *,
            refresh_source_roster_id: bool = False,
            refresh_manifest_id: bool = True,
        ) -> dict[str, object]:
            manifest = valid_route_policy_manifest()
            edit(manifest)
            if refresh_source_roster_id:
                source_roster = manifest["source_roster"]
                source_roster["source_roster_id"] = route_policy_digest(source_roster["files"])
            if refresh_manifest_id:
                finalize_route_policy_manifest(manifest)
            return manifest

        cases = [
            (
                "unsupported-version",
                lambda manifest: manifest.__setitem__("schema_version", "2.0.0"),
                "unsupported_schema_version",
            ),
            (
                "unknown-top-level-key",
                lambda manifest: manifest.__setitem__("unknown_key", True),
                "unknown_top_level_keys",
            ),
            (
                "manifest-id",
                lambda manifest: manifest.__setitem__("manifest_id", f"sha256:{'0' * 64}"),
                "manifest_id_mismatch",
                False,
                False,
            ),
            (
                "source-roster-digest",
                lambda manifest: manifest["source_roster"].__setitem__("source_roster_id", f"sha256:{'0' * 64}"),
                "source_roster_id_mismatch",
            ),
            (
                "missing-required-agent",
                lambda manifest: manifest["required_agent_policies"].pop("uat-runbook-author"),
                "required_agent_policy_roster_mismatch",
            ),
            (
                "unknown-required-policy-key",
                lambda manifest: manifest["required_agent_policies"]["analyze-executor"].__setitem__(
                    "unknown_key",
                    True,
                ),
                "required_agent_policy_schema_mismatch",
            ),
            (
                "invalid-required-capabilities-type",
                lambda manifest: manifest["required_agent_policies"]["analyze-executor"].__setitem__(
                    "required_capabilities",
                    "capability-that-route-does-not-have",
                ),
                "required_agent_capabilities_invalid",
            ),
            (
                "invalid-non-route-contract-digest",
                lambda manifest: manifest["required_agent_policies"]["analyze-executor"].__setitem__(
                    "non_route_contract_digest",
                    "not-a-digest",
                ),
                "required_agent_non_route_contract_digest_invalid",
            ),
            (
                "mismatched-non-route-contract-digest",
                lambda manifest: manifest["required_agent_policies"]["analyze-executor"].__setitem__(
                    "non_route_contract_digest",
                    f"sha256:{'1' * 64}",
                ),
                "required_agent_non_route_contract_digest_mismatch",
            ),
            (
                "wrong-optional-helper",
                lambda manifest: manifest["optional_helper"].__setitem__("helper_name", "not-the-helper"),
                "optional_helper_mismatch",
            ),
            (
                "invalid-no-helper-allowed-type",
                lambda manifest: manifest["optional_helper"]["no_helper"].__setitem__("allowed", "false"),
                "optional_helper_no_helper_allowed_not_boolean",
            ),
            (
                "partial-bounded-probe",
                lambda manifest: (
                    bind_required_primary_probe(manifest),
                    manifest["bounded_probes"].__setitem__(
                        "probe-required-primary",
                        {
                            "probe_id": "probe-required-primary",
                            "candidate_route_id": "required-primary",
                        },
                    ),
                ),
                "bounded_probe_schema_mismatch",
            ),
            (
                "bounded-probe-id-mismatch",
                lambda manifest: (
                    bind_required_primary_probe(manifest),
                    manifest["bounded_probes"].__setitem__(
                        "probe-required-primary",
                        {
                            "probe_id": "different-probe",
                            "candidate_route_id": "required-primary",
                            "purpose": "test",
                            "bounds": {"max_calls": 1},
                            "expected_result_shape": {"available": "boolean"},
                        },
                    ),
                ),
                "bounded_probe_id_mismatch",
            ),
            (
                "bounded-probe-route-binding-mismatch",
                lambda manifest: (
                    bind_required_primary_probe(manifest),
                    manifest["bounded_probes"].__setitem__(
                        "probe-required-primary",
                        {
                            "probe_id": "probe-required-primary",
                            "candidate_route_id": "required-fallback",
                            "purpose": "test",
                            "bounds": {"max_calls": 1},
                            "expected_result_shape": {"available": "boolean"},
                        },
                    ),
                ),
                "bounded_probe_route_binding_mismatch",
            ),
            (
                "reused-route-id-definition-mismatch",
                lambda manifest: manifest["required_agent_policies"]["analyze-executor"]["preferred_route"].__setitem__(
                    "model",
                    "model-not-observed-by-route-id",
                ),
                "route_id_definition_mismatch",
            ),
            (
                "source-roster-missing-optional-helper",
                lambda manifest: manifest["source_roster"].__setitem__(
                    "files",
                    [
                        record
                        for record in manifest["source_roster"]["files"]
                        if record["name"] != "autopilot-fast-helper.toml"
                    ],
                ),
                "source_roster_files_mismatch",
                True,
            ),
        ]

        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            for case in cases:
                label, edit, reason, *flags = case
                refresh_source_roster_id = bool(flags[0]) if flags else False
                refresh_manifest_id = bool(flags[1]) if len(flags) > 1 else True
                with self.subTest(label=label):
                    path = self.write_route_policy_manifest(
                        git_root,
                        mutated_manifest(
                            edit,
                            refresh_source_roster_id=refresh_source_roster_id,
                            refresh_manifest_id=refresh_manifest_id,
                        ),
                        name=f"{label}.json",
                    )

                    result = install.load_codex_route_policy_manifest(
                        path.relative_to(git_root).as_posix(),
                        git_root,
                        PLUGIN_ROOT / "codex-agents",
                    )

                    self.assertEqual(result["code"], "invalid_route_policy_manifest")
                    self.assertEqual(result["details"]["reason"], reason)

    def test_codex_route_policy_manifest_path_must_be_trusted_regular_repo_file(self) -> None:
        from speckit_pro_runner.helpers import install

        tmp, git_root = self.temp_clean_git_repo()
        with tmp, tempfile.TemporaryDirectory() as outside_tmp:
            outside_path = Path(outside_tmp) / "route-policy.json"
            outside_path.write_text(json.dumps(valid_route_policy_manifest()), encoding="utf-8")

            outside = install.load_codex_route_policy_manifest(
                outside_path.as_posix(),
                git_root,
                PLUGIN_ROOT / "codex-agents",
            )
            self.assertEqual(outside["code"], "invalid_route_policy_manifest_path")

            link = git_root / ".codex" / "route-policy-link.json"
            link.parent.mkdir(parents=True, exist_ok=True)
            try:
                link.symlink_to(outside_path)
            except OSError:
                self.skipTest("symlink creation is unavailable")

            linked = install.load_codex_route_policy_manifest(
                link.relative_to(git_root).as_posix(),
                git_root,
                PLUGIN_ROOT / "codex-agents",
            )
            self.assertEqual(linked["code"], "invalid_route_policy_manifest_path")

    def test_install_codex_agents_rejects_supplied_invalid_route_policy_manifest_before_static_writes(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            manifest = valid_route_policy_manifest()
            manifest["schema_version"] = "2.0.0"
            finalize_route_policy_manifest(manifest)
            path = self.write_route_policy_manifest(git_root, manifest)
            destination = git_root / ".codex" / "agents"

            completed, response, stderr_records = run_runner(
                helper_request(
                    "install-codex-agents",
                    mode="apply",
                    inputs={
                        "destination": ".codex/agents",
                        "route_policy_manifest": path.relative_to(git_root).as_posix(),
                    },
                ),
                cwd=git_root,
            )

        self.assertEqual(completed.returncode, 2)
        self.assert_response(response, "input_error", 2)
        self.assertEqual([diag["code"] for diag in stderr_records], ["invalid_route_policy_manifest"])
        self.assertFalse(destination.exists())

    def test_install_codex_agents_rejects_truthy_string_no_helper_authorization(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            manifest = valid_route_policy_manifest()
            manifest["optional_helper"]["no_helper"]["allowed"] = "false"
            finalize_route_policy_manifest(manifest)
            path = self.write_route_policy_manifest(git_root, manifest)
            destination = git_root / ".codex" / "agents"

            completed, response, stderr_records = run_runner(
                helper_request(
                    "install-codex-agents",
                    mode="apply",
                    inputs={
                        "destination": ".codex/agents",
                        "route_policy_manifest": path.relative_to(git_root).as_posix(),
                    },
                ),
                cwd=git_root,
            )

        self.assertEqual(completed.returncode, 2)
        self.assert_response(response, "input_error", 2)
        self.assertEqual([diag["code"] for diag in stderr_records], ["invalid_route_policy_manifest"])
        self.assertFalse(destination.exists())

    def test_install_codex_agents_route_aware_captures_injected_snapshot_once(self) -> None:
        from speckit_pro_runner.helpers import install
        from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            manifest_path = self.write_valid_route_policy_manifest(git_root)
            expected_snapshot = routing_capability_snapshot()
            request = SimpleNamespace(
                request_id="test-route-aware-captures-snapshot-once",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="dry_run",
                inputs=self.route_aware_inputs(manifest_path, git_root),
            )
            old_cwd = Path.cwd()
            os.chdir(git_root)
            try:
                with patch.object(install, "capture_codex_runtime_capabilities", return_value=expected_snapshot) as adapter:
                    response = install.run_codex_agent_install(MUTATION_HELPERS["install-codex-agents"], request)
            finally:
                os.chdir(old_cwd)

        self.assert_response(response, "ok", 0)
        self.assertEqual(adapter.call_count, 1)
        self.assert_route_aware_snapshot_response(
            response,
            manifest_path=manifest_path,
            git_root=git_root,
            expected_snapshot=expected_snapshot,
        )

    def test_install_codex_agents_route_aware_uses_manifest_admitted_probe_when_native_discovery_unavailable(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            manifest = bounded_probe_required_manifest()
            manifest_path = self.write_route_policy_manifest(git_root, manifest)
            base_snapshot = routing_native_unavailable_snapshot("probe-success")
            admitted_probe = {
                "probe_id": "probe-required-primary",
                "route_id": "required-primary",
                "status": "success",
                "available": True,
            }
            rogue_probe = {
                "probe_id": "probe-rogue",
                "route_id": "required-fallback",
                "status": "success",
                "available": True,
            }
            expected_snapshot = dict(base_snapshot)
            expected_snapshot["child_probe_results"] = [admitted_probe]
            inputs = self.route_aware_inputs(manifest_path, git_root)
            inputs["test_overrides"] = {
                "codex_capability_snapshot": base_snapshot,
                "codex_probe_results": [admitted_probe, rogue_probe],
            }

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", inputs=inputs),
                cwd=git_root,
            )

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(stderr_records, [])
        self.assert_response(response, "ok", 0)
        self.assert_route_aware_snapshot_response(
            response,
            manifest_path=manifest_path,
            git_root=git_root,
            expected_snapshot=expected_snapshot,
            expected_manifest=manifest,
        )
        self.assert_route_aware_required_resolution(response, expected_snapshot=expected_snapshot)
        self.assert_route_aware_helper_omitted_no_file(response, git_root / ".codex" / "agents")
        self.assert_route_aware_no_mutation_yet(response)
        self.assertTrue(
            all(record["snapshot_id"] == expected_snapshot["snapshot_id"] for record in response["data"]["routing"]["required_agents"])
        )

    def test_install_codex_agents_route_aware_probe_failure_and_insufficient_results_do_not_widen_candidates(self) -> None:
        cases = [
            (
                "probe-failed",
                [{"probe_id": "probe-required-primary", "route_id": "required-primary", "status": "failed", "available": False}],
                "probe_failed",
            ),
            (
                "probe-insufficient",
                [{"probe_id": "probe-required-primary", "route_id": "required-primary", "status": "success"}],
                "probe_insufficient_result",
            ),
            (
                "unmanifested-probe-success",
                [{"probe_id": "probe-rogue", "route_id": "required-primary", "status": "success", "available": True}],
                "probe_result_missing",
            ),
        ]
        for label, probe_results, expected_reason in cases:
            with self.subTest(label=label):
                tmp, git_root = self.temp_clean_git_repo()
                with tmp, tempfile.TemporaryDirectory() as home_tmp:
                    fake_home = Path(home_tmp).resolve()
                    manifest = bounded_probe_required_manifest()
                    manifest_path = self.write_route_policy_manifest(git_root, manifest)
                    base_snapshot = routing_native_unavailable_snapshot(label)
                    inputs = self.route_aware_inputs(manifest_path, git_root, destination=None)
                    inputs["test_overrides"] = {
                        "codex_capability_snapshot": base_snapshot,
                        "codex_probe_results": probe_results,
                    }
                    env = {"HOME": str(fake_home), "USERPROFILE": str(fake_home)}

                    completed, response, stderr_records = run_runner(
                        helper_request("install-codex-agents", mode="apply", inputs=inputs),
                        cwd=git_root,
                        env_overrides=env,
                    )

                    self.assertEqual(completed.returncode, 1)
                    self.assertEqual([diag["code"] for diag in stderr_records], ["codex_route_required_agent_unresolved"])
                    self.assert_response(response, "expected_failure", 1)
                    routing = response["data"]["routing"]
                    snapshot = routing["runtime_capability_snapshot"]
                    self.assertEqual(snapshot["snapshot_id"], base_snapshot["snapshot_id"])
                    self.assertFalse(snapshot["observation_evidence"]["native_discovery"])
                    self.assertEqual(snapshot["observation_evidence"]["available_routes"], [])
                    self.assertEqual(
                        [result["probe_id"] for result in snapshot["child_probe_results"]],
                        ["probe-required-primary"] if label != "unmanifested-probe-success" else [],
                    )
                    self.assertEqual([record["agent_name"] for record in routing["required_agents"]], routing_required_agents())
                    for record in routing["required_agents"]:
                        self.assertEqual(record["snapshot_id"], base_snapshot["snapshot_id"])
                        self.assertEqual(record["terminal_outcome"], "unresolved")
                        self.assertEqual(record["attempted_routes"][0]["route_id"], "required-primary")
                        self.assertEqual(record["attempted_routes"][0]["reason"], expected_reason)
                    self.assert_strict_required_override_zero_mutation(response)
                    self.assertFalse((fake_home / ".codex" / "agents").exists())

    def test_install_codex_agents_route_aware_dry_run_uses_fake_home_and_routing_response(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp, tempfile.TemporaryDirectory() as home_tmp:
            fake_home = Path(home_tmp).resolve()
            manifest_path = self.write_valid_route_policy_manifest(git_root)
            expected_snapshot = routing_capability_snapshot()
            env = {"HOME": str(fake_home), "USERPROFILE": str(fake_home)}

            completed, response, stderr_records = run_runner(
                helper_request(
                    "install-codex-agents",
                    inputs=self.route_aware_inputs(manifest_path, git_root, destination=None),
                ),
                cwd=git_root,
                env_overrides=env,
            )

            self.assertEqual(completed.returncode, 0)
            self.assertEqual(stderr_records, [])
            self.assert_response(response, "ok", 0)
            self.assertEqual(response["data"]["destination"], (fake_home / ".codex" / "agents").as_posix())
            self.assertFalse((fake_home / ".codex" / "agents").exists())
            self.assertNotEqual(response["data"]["destination"], (Path.home() / ".codex" / "agents").as_posix())
            self.assert_route_aware_snapshot_response(
                response,
                manifest_path=manifest_path,
                git_root=git_root,
                expected_snapshot=expected_snapshot,
            )

    def test_install_codex_agents_route_aware_dry_run_resolves_required_roster_before_writes(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            manifest_path = self.write_valid_route_policy_manifest(git_root)
            expected_snapshot = routing_capability_snapshot()

            completed, response, stderr_records = run_runner(
                helper_request(
                    "install-codex-agents",
                    inputs=self.route_aware_inputs(manifest_path, git_root),
                ),
                cwd=git_root,
            )

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(stderr_records, [])
        self.assert_response(response, "ok", 0)
        self.assertEqual(response["data"]["mutation"]["mutation_status"], "planned")
        self.assertEqual(len(response["data"]["mutation"]["planned_operations"]), 11)
        self.assert_route_aware_snapshot_response(
            response,
            manifest_path=manifest_path,
            git_root=git_root,
            expected_snapshot=expected_snapshot,
        )
        self.assert_route_aware_required_resolution(response, expected_snapshot=expected_snapshot)
        self.assert_route_aware_helper_installed(response, expected_snapshot=expected_snapshot)
        self.assert_route_aware_no_mutation_yet(response)

    def test_install_codex_agents_route_aware_dry_run_uses_required_fallbacks_from_same_snapshot(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            manifest_path = self.write_valid_route_policy_manifest(git_root)
            expected_snapshot = routing_capability_snapshot()
            expected_snapshot["available_routes"] = ["required-fallback", "helper-primary"]
            inputs = self.route_aware_inputs(manifest_path, git_root)
            inputs["test_overrides"] = {"codex_capability_snapshot": expected_snapshot}

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", inputs=inputs),
                cwd=git_root,
            )

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(stderr_records, [])
        self.assert_response(response, "ok", 0)
        self.assert_route_aware_snapshot_response(
            response,
            manifest_path=manifest_path,
            git_root=git_root,
            expected_snapshot=expected_snapshot,
        )
        self.assert_route_aware_required_resolution(
            response,
            expected_snapshot=expected_snapshot,
            selected_route_id="required-fallback",
            expected_attempt_count=2,
        )
        self.assert_route_aware_helper_installed(response, expected_snapshot=expected_snapshot)

    def test_install_codex_agents_route_aware_apply_installs_missing_required_fallback_bytes(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        before_source_digests = codex_agent_source_digests()
        with tmp:
            manifest_path = self.write_valid_route_policy_manifest(git_root)
            expected_snapshot = routing_capability_snapshot()
            expected_snapshot["available_routes"] = ["required-fallback", "helper-primary"]
            inputs = self.route_aware_inputs(manifest_path, git_root)
            inputs["test_overrides"] = {"codex_capability_snapshot": expected_snapshot}
            destination = git_root / ".codex" / "agents"

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", mode="apply", inputs=inputs),
                cwd=git_root,
            )

            self.assertEqual(completed.returncode, 0)
            self.assertEqual(stderr_records, [])
            self.assert_response(response, "ok", 0)
            self.assert_route_aware_snapshot_response(
                response,
                manifest_path=manifest_path,
                git_root=git_root,
                expected_snapshot=expected_snapshot,
            )
            self.assert_route_aware_required_resolution(
                response,
                expected_snapshot=expected_snapshot,
                selected_route_id="required-fallback",
                expected_attempt_count=2,
            )
            self.assert_route_aware_apply_mutation_evidence(response)
            self.assert_route_aware_required_destination_bytes(response, destination)
            matched = set(response["data"]["verification"]["matched_files"])
            self.assertTrue({f"{agent}.toml" for agent in routing_required_agents()} <= matched)
        self.assertEqual(codex_agent_source_digests(), before_source_digests)

    def test_install_codex_agents_route_aware_apply_refreshes_stale_required_bytes_only_after_complete_plan(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        before_source_digests = codex_agent_source_digests()
        with tmp:
            manifest_path = self.write_valid_route_policy_manifest(git_root)
            expected_snapshot = routing_capability_snapshot()
            destination = git_root / ".codex" / "agents"
            destination.mkdir(parents=True)
            unrelated = destination / "user-owned-agent.toml"
            unrelated.write_text("user owned\n", encoding="utf-8")
            for agent_name in routing_required_agents():
                (destination / f"{agent_name}.toml").write_text(f"stale {agent_name}\n", encoding="utf-8")

            completed, response, stderr_records = run_runner(
                helper_request(
                    "install-codex-agents",
                    mode="apply",
                    inputs=self.route_aware_inputs(manifest_path, git_root),
                ),
                cwd=git_root,
            )

            self.assertEqual(completed.returncode, 1)
            self.assert_response(response, "expected_failure", 1)
            cleanup_errors = response["diagnostics"][0]["details"]["cleanup_errors"]
            self.assertTrue(any(error["kind"] == "preserved_cleanup_entry" for error in cleanup_errors))
            self.assert_route_aware_snapshot_response(
                response,
                manifest_path=manifest_path,
                git_root=git_root,
                expected_snapshot=expected_snapshot,
            )
            self.assert_route_aware_required_resolution(response, expected_snapshot=expected_snapshot)
            self.assertEqual(response["data"]["mutation"]["mutation_status"], "partial_failure")
            self.assert_route_aware_required_destination_bytes(response, destination)
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "user owned\n")
        self.assertEqual(codex_agent_source_digests(), before_source_digests)

    def test_install_codex_agents_route_aware_apply_failure_restores_prior_required_bytes_and_modes(self) -> None:
        from speckit_pro_runner.helpers import install
        from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

        tmp, git_root = self.temp_clean_git_repo()
        with tmp, tempfile.TemporaryDirectory() as home_tmp:
            fake_home = Path(home_tmp).resolve()
            manifest_path = self.write_valid_route_policy_manifest(git_root)
            expected_snapshot = routing_capability_snapshot()
            expected_snapshot["available_routes"] = ["required-primary", "required-fallback"]
            destination = fake_home / ".codex" / "agents"
            destination.mkdir(parents=True)
            prior_mode = 0o640
            prior_agent_bytes = {
                agent_name: f"previous route-aware install {agent_name}\n".encode("utf-8")
                for agent_name in routing_required_agents()
            }
            for agent_name, content in prior_agent_bytes.items():
                target = destination / f"{agent_name}.toml"
                target.write_bytes(content)
                target.chmod(prior_mode)
            failed_agent_name = routing_required_agents()[1]
            failed_once = False
            real_write = install.write_codex_agent_atomic

            def fail_second_required_write(
                target: Path,
                content: bytes,
                target_dir: Path,
                identity: tuple[int, int] | None,
                *,
                mode: int | None = None,
                expected_state: object = None,
                cleanup_race_state: object = None,
            ) -> object:
                nonlocal failed_once
                if target.name == f"{failed_agent_name}.toml" and not failed_once:
                    failed_once = True
                    raise OSError("injected route-aware write failure")
                return real_write(
                    target,
                    content,
                    target_dir,
                    identity,
                    mode=mode,
                    expected_state=expected_state,
                    cleanup_race_state=cleanup_race_state,
                )

            request = SimpleNamespace(
                request_id="test-route-aware-rollback-success",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="apply",
                inputs=self.route_aware_inputs(manifest_path, git_root, destination=None),
            )
            request.inputs["test_overrides"] = {"codex_capability_snapshot": expected_snapshot}
            old_cwd = Path.cwd()
            os.chdir(git_root)
            try:
                with (
                    patch.dict(os.environ, {"HOME": str(fake_home), "USERPROFILE": str(fake_home)}),
                    patch.object(install, "write_codex_agent_atomic", side_effect=fail_second_required_write),
                ):
                    response = install.run_codex_agent_install(MUTATION_HELPERS["install-codex-agents"], request)
            finally:
                os.chdir(old_cwd)

            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["codex_agent_install_failed"])
            self.assert_route_aware_snapshot_response(
                response,
                manifest_path=manifest_path,
                git_root=git_root,
                expected_snapshot=expected_snapshot,
            )
            self.assert_route_aware_required_resolution(response, expected_snapshot=expected_snapshot)
            self.assert_route_aware_rollback_success_evidence(
                response,
                destination,
                prior_agent_bytes,
                prior_mode,
                failed_agent_name,
            )

    def test_install_codex_agents_route_aware_apply_reports_unrestored_rollback_failure(self) -> None:
        from speckit_pro_runner.helpers import install
        from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

        tmp, git_root = self.temp_clean_git_repo()
        with tmp, tempfile.TemporaryDirectory() as home_tmp:
            fake_home = Path(home_tmp).resolve()
            manifest_path = self.write_valid_route_policy_manifest(git_root)
            expected_snapshot = routing_capability_snapshot()
            expected_snapshot["available_routes"] = ["required-primary", "required-fallback"]
            destination = fake_home / ".codex" / "agents"
            destination.mkdir(parents=True)
            prior_mode = 0o640
            prior_agent_bytes = {
                agent_name: f"rollback failure previous {agent_name}\n".encode("utf-8")
                for agent_name in routing_required_agents()
            }
            for agent_name, content in prior_agent_bytes.items():
                target = destination / f"{agent_name}.toml"
                target.write_bytes(content)
                target.chmod(prior_mode)
            failed_agent_name = routing_required_agents()[1]
            unrestored_agent_name = routing_required_agents()[0]
            failed_once = False
            real_write = install.write_codex_agent_atomic

            def fail_second_required_write_and_first_rollback(
                target: Path,
                content: bytes,
                target_dir: Path,
                identity: tuple[int, int] | None,
                *,
                mode: int | None = None,
                expected_state: object = None,
                cleanup_race_state: object = None,
            ) -> object:
                nonlocal failed_once
                if target.name == f"{failed_agent_name}.toml" and not failed_once:
                    failed_once = True
                    raise OSError("injected route-aware write failure")
                if target.name == f"{unrestored_agent_name}.toml" and failed_once and mode is not None:
                    raise OSError("injected route-aware rollback failure")
                return real_write(
                    target,
                    content,
                    target_dir,
                    identity,
                    mode=mode,
                    expected_state=expected_state,
                    cleanup_race_state=cleanup_race_state,
                )

            request = SimpleNamespace(
                request_id="test-route-aware-rollback-failure",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="apply",
                inputs=self.route_aware_inputs(manifest_path, git_root, destination=None),
            )
            request.inputs["test_overrides"] = {"codex_capability_snapshot": expected_snapshot}
            old_cwd = Path.cwd()
            os.chdir(git_root)
            try:
                with (
                    patch.dict(os.environ, {"HOME": str(fake_home), "USERPROFILE": str(fake_home)}),
                    patch.object(install, "write_codex_agent_atomic", side_effect=fail_second_required_write_and_first_rollback),
                ):
                    response = install.run_codex_agent_install(MUTATION_HELPERS["install-codex-agents"], request)
            finally:
                os.chdir(old_cwd)

            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["codex_agent_install_failed"])
            self.assert_route_aware_snapshot_response(
                response,
                manifest_path=manifest_path,
                git_root=git_root,
                expected_snapshot=expected_snapshot,
            )
            self.assert_route_aware_required_resolution(response, expected_snapshot=expected_snapshot)
            self.assert_route_aware_rollback_failure_evidence(
                response,
                destination,
                prior_agent_bytes,
                prior_mode,
                failed_agent_name,
                unrestored_agent_name,
            )

    def test_install_codex_agents_route_aware_recovery_reports_cleanup_actions(self) -> None:
        from speckit_pro_runner.helpers import install
        from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

        tmp, git_root = self.temp_clean_git_repo()
        with tmp, tempfile.TemporaryDirectory() as home_tmp:
            fake_home = Path(home_tmp).resolve()
            manifest_path = self.write_valid_route_policy_manifest(git_root)
            expected_snapshot = routing_capability_snapshot()
            expected_snapshot["available_routes"] = ["required-primary", "required-fallback"]
            failed_agent_name = routing_required_agents()[1]
            real_write = install.write_codex_agent_atomic

            def fail_second_write(
                target: Path,
                content: bytes,
                target_dir: Path,
                identity: tuple[int, int] | None,
                *,
                mode: int | None = None,
                expected_state: object = None,
                cleanup_race_state: object = None,
            ) -> object:
                if target.name == f"{failed_agent_name}.toml":
                    raise OSError("injected route-aware write failure")
                return real_write(
                    target,
                    content,
                    target_dir,
                    identity,
                    mode=mode,
                    expected_state=expected_state,
                    cleanup_race_state=cleanup_race_state,
                )

            request = SimpleNamespace(
                request_id="test-route-aware-cleanup-evidence",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="apply",
                inputs=self.route_aware_inputs(manifest_path, git_root, destination=None),
            )
            request.inputs["test_overrides"] = {"codex_capability_snapshot": expected_snapshot}
            old_cwd = Path.cwd()
            os.chdir(git_root)
            try:
                with (
                    patch.dict(os.environ, {"HOME": str(fake_home), "USERPROFILE": str(fake_home)}),
                    patch.object(install, "write_codex_agent_atomic", side_effect=fail_second_write),
                ):
                    response = install.run_codex_agent_install(MUTATION_HELPERS["install-codex-agents"], request)
            finally:
                os.chdir(old_cwd)

            record = response["data"]["routing"]["recovery_or_mutation"]["recovery_record"]
            self.assert_response(response, "expected_failure", 1)
            self.assertEqual(len(record["applied_actions"]), 1)
            self.assertEqual(len(record["rolled_back_actions"]), 1)
            self.assertEqual(record["cleanup_actions"], [])
            self.assertTrue(any(error["kind"] == "preserved_cleanup_entry" for error in record["cleanup_errors"]))
            directory_error = next(error for error in record["cleanup_errors"] if error["kind"] == "remove_directory")
            self.assertEqual(directory_error["error"], "identity_bound_directory_removal_unavailable")
            self.assertFalse((fake_home / ".codex" / "agents").exists())
            self.assertTrue((fake_home / ".codex").exists())

    def test_install_codex_agents_route_aware_no_clobber_preserves_exact_cleanup_provenance(self) -> None:
        from speckit_pro_runner.helpers import install
        from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

        tmp, git_root = self.temp_clean_git_repo()
        with tmp, tempfile.TemporaryDirectory() as home_tmp:
            fake_home = Path(home_tmp).resolve()
            manifest_path = self.write_valid_route_policy_manifest(git_root)
            expected_snapshot = routing_capability_snapshot()
            expected_snapshot["available_routes"] = ["required-primary", "required-fallback"]
            cleanup_path = fake_home / ".codex" / "agents" / ".agent.toml.exact-owned.cleanup"
            cleanup_error = {
                "kind": "preserved_cleanup_entry",
                "target": cleanup_path.as_posix(),
                "error": "fd_bound_delete_unavailable",
            }

            def fail_with_exact_owned_cleanup(
                target: Path,
                content: bytes,
                target_dir: Path,
                identity: tuple[int, int] | None,
                *,
                mode: int | None = None,
                expected_state: object = None,
                cleanup_race_state: object = None,
            ) -> object:
                del target, content, target_dir, identity, mode, expected_state, cleanup_race_state
                cleanup_path.parent.mkdir(parents=True, exist_ok=True)
                cleanup_path.write_bytes(b"exact installer-owned cleanup\n")
                raise install.CodexAgentNoClobberConflict(
                    "injected exact installer cleanup",
                    [cleanup_path.as_posix()],
                    [cleanup_error],
                )

            request = SimpleNamespace(
                request_id="test-route-aware-no-clobber-exact-cleanup-provenance",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="apply",
                inputs=self.route_aware_inputs(manifest_path, git_root, destination=None),
            )
            request.inputs["test_overrides"] = {"codex_capability_snapshot": expected_snapshot}
            old_cwd = Path.cwd()
            os.chdir(git_root)
            try:
                with (
                    patch.dict(os.environ, {"HOME": str(fake_home), "USERPROFILE": str(fake_home)}),
                    patch.object(install, "write_codex_agent_atomic", side_effect=fail_with_exact_owned_cleanup),
                ):
                    response = install.run_codex_agent_install(MUTATION_HELPERS["install-codex-agents"], request)
            finally:
                os.chdir(old_cwd)

            self.assert_response(response, "expected_failure", 1)
            cleanup_errors = response["diagnostics"][0]["details"]["cleanup_errors"]
            self.assertIn(cleanup_error, cleanup_errors)
            self.assertNotIn(
                {
                    "kind": "preserved_concurrent_file",
                    "target": cleanup_path.as_posix(),
                    "error": "no_clobber_conflict",
                },
                cleanup_errors,
            )
            recovery_errors = response["data"]["routing"]["recovery_or_mutation"]["recovery_record"]["cleanup_errors"]
            self.assertIn(cleanup_error, recovery_errors)
            self.assertNotIn(
                {
                    "kind": "preserved_concurrent_file",
                    "target": cleanup_path.as_posix(),
                    "error": "no_clobber_conflict",
                },
                recovery_errors,
            )
            remediation = response["data"]["mutation"]["manual_remediation"]
            cleanup_action = next(action for action in remediation if action["reason"] == "cleanup_incomplete")
            self.assertIn(cleanup_path.as_posix(), cleanup_action["paths"])
            self.assertNotIn("concurrent_file_preserved", [action["reason"] for action in remediation])

    def test_install_codex_agents_route_aware_reports_helper_removal_as_failed_operation(self) -> None:
        from speckit_pro_runner.helpers import install
        from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            manifest_path = self.write_valid_route_policy_manifest(git_root)
            expected_snapshot = routing_capability_snapshot()
            expected_snapshot["available_routes"] = ["required-primary", "required-fallback"]
            destination = git_root / ".codex" / "agents"
            destination.mkdir(parents=True)
            helper_name = f"{routing_optional_helper()}.toml"
            helper_path = destination / helper_name
            helper_path.write_bytes(route_rendered_optional_helper_bytes())
            inputs = self.route_aware_inputs(manifest_path, git_root)
            inputs["test_overrides"] = {"codex_capability_snapshot": expected_snapshot}
            request = SimpleNamespace(
                request_id="test-route-aware-helper-removal-failure",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="apply",
                inputs=inputs,
            )
            real_remove = install.remove_codex_agent_if_unchanged

            def fail_helper_removal(target: Path, *args: object, **kwargs: object) -> None:
                if target.name == helper_name:
                    raise OSError("injected helper removal failure")
                real_remove(target, *args, **kwargs)

            old_cwd = Path.cwd()
            os.chdir(git_root)
            try:
                with patch.object(install, "remove_codex_agent_if_unchanged", side_effect=fail_helper_removal):
                    response = install.run_codex_agent_install(MUTATION_HELPERS["install-codex-agents"], request)
            finally:
                os.chdir(old_cwd)

            mutation = response["data"]["mutation"]
            failed = response["data"]["routing"]["recovery_or_mutation"]["recovery_record"]["failed_actions"]
            self.assert_response(response, "expected_failure", 1)
            self.assertEqual(mutation["failure_operation"]["kind"], "remove_file")
            self.assertEqual(mutation["failure_operation"]["operation_id"], f"remove-codex-agent:{helper_name}")
            self.assertEqual(failed[0]["kind"], "remove_file")
            self.assertEqual(failed[0]["name"], helper_name)
            self.assertTrue(helper_path.exists())

    def test_install_codex_agents_route_aware_reports_post_copy_verification_failure_action(self) -> None:
        from speckit_pro_runner.helpers import install
        from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

        tmp, git_root = self.temp_clean_git_repo()
        with tmp, tempfile.TemporaryDirectory() as home_tmp:
            fake_home = Path(home_tmp).resolve()
            manifest_path = self.write_valid_route_policy_manifest(git_root)
            expected_snapshot = routing_capability_snapshot()
            expected_snapshot["available_routes"] = ["required-primary", "required-fallback"]
            request = SimpleNamespace(
                request_id="test-route-aware-post-copy-verification-failure",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="apply",
                inputs=self.route_aware_inputs(manifest_path, git_root, destination=None),
            )
            request.inputs["test_overrides"] = {"codex_capability_snapshot": expected_snapshot}
            mismatch = "analyze-executor.toml"
            old_cwd = Path.cwd()
            os.chdir(git_root)
            try:
                with (
                    patch.dict(os.environ, {"HOME": str(fake_home), "USERPROFILE": str(fake_home)}),
                    patch.object(install, "verify_codex_agent_install", return_value=[mismatch]),
                ):
                    response = install.run_codex_agent_install(MUTATION_HELPERS["install-codex-agents"], request)
            finally:
                os.chdir(old_cwd)

            mutation = response["data"]["mutation"]
            record = response["data"]["routing"]["recovery_or_mutation"]["recovery_record"]
            self.assert_response(response, "expected_failure", 1)
            self.assertEqual(mutation["failure_operation"]["kind"], "verify_files")
            self.assertEqual(mutation["failure_operation"]["operation_id"], "verify-codex-agent-install")
            self.assertEqual(
                record["failed_actions"],
                [{
                    "operation_id": "verify-codex-agent-install",
                    "kind": "verify_files",
                    "targets": [(fake_home / ".codex" / "agents" / mismatch).as_posix()],
                }],
            )
            self.assertEqual(len(record["applied_actions"]), len(routing_required_agents()))
            self.assertEqual(len(record["rolled_back_actions"]), len(routing_required_agents()))
            self.assertTrue(response["data"]["writes_state"])

    def test_install_codex_agents_no_clobber_write_preserves_final_window_edit(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "analyze-executor.toml"
            target.write_bytes(b"captured\n")
            expected = install.codex_agent_previous_state(target)
            identity = install.codex_agent_destination_identity(destination)
            concurrent = b"concurrent final-window edit\n"
            real_move = install.codex_agent_native_rename_no_replace
            injected = False

            def edit_before_move(directory_fd: int, source: str, backup: str) -> None:
                nonlocal injected
                if source == target.name and not injected:
                    injected = True
                    target.write_bytes(concurrent)
                real_move(directory_fd, source, backup)

            with patch.object(install, "codex_agent_native_rename_no_replace", side_effect=edit_before_move):
                with self.assertRaisesRegex(OSError, "target changed before no-clobber install"):
                    install.write_codex_agent_atomic(
                        target,
                        b"installer bytes\n",
                        destination,
                        identity,
                        expected_state=expected,
                    )

            self.assertEqual(target.read_bytes(), concurrent)
            self.assertEqual(list(destination.glob(".*.bak")), [])

    def test_install_codex_agents_no_clobber_removal_preserves_final_window_edit(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "autopilot-fast-helper.toml"
            target.write_bytes(b"captured helper\n")
            expected = install.codex_agent_previous_state(target)
            assert expected is not None
            identity = install.codex_agent_destination_identity(destination)
            concurrent = b"concurrent helper edit\n"
            real_move = install.codex_agent_native_rename_no_replace
            injected = False

            def edit_before_move(directory_fd: int, source: str, backup: str) -> None:
                nonlocal injected
                if source == target.name and not injected:
                    injected = True
                    target.write_bytes(concurrent)
                real_move(directory_fd, source, backup)

            with patch.object(install, "codex_agent_native_rename_no_replace", side_effect=edit_before_move):
                with self.assertRaisesRegex(OSError, "removal target changed before no-clobber removal"):
                    install.remove_codex_agent_if_unchanged(target, expected, destination, identity)

            self.assertEqual(target.read_bytes(), concurrent)
            self.assertEqual(list(destination.glob(".*.bak")), [])

    def test_install_codex_agents_no_clobber_write_preserves_entry_created_after_move(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "analyze-executor.toml"
            target.write_bytes(b"captured\n")
            expected = install.codex_agent_previous_state(target)
            identity = install.codex_agent_destination_identity(destination)
            concurrent = b"concurrent entry after move\n"
            real_move = install.codex_agent_native_rename_no_replace
            injected = False

            def create_before_temp_publish(directory_fd: int, source: str, target_name: str) -> None:
                nonlocal injected
                if target_name == target.name and source.endswith(".tmp") and not injected:
                    injected = True
                    target.write_bytes(concurrent)
                real_move(directory_fd, source, target_name)

            with patch.object(install, "codex_agent_native_rename_no_replace", side_effect=create_before_temp_publish):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.write_codex_agent_atomic(
                        target,
                        b"installer bytes\n",
                        destination,
                        identity,
                        expected_state=expected,
                    )

            self.assertEqual(target.read_bytes(), concurrent)
            backups = list(destination.glob(".*.bak"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), b"captured\n")
            self.assertIn(backups[0].as_posix(), raised.exception.preserved_paths)
            self.assertIn(target.as_posix(), raised.exception.preserved_paths)
            self.assertTrue(any(".cleanup-dir/" in path and path.endswith(".tmp") for path in raised.exception.preserved_paths))

    def test_install_codex_agents_no_clobber_removal_preserves_entry_created_after_move(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "autopilot-fast-helper.toml"
            target.write_bytes(b"captured helper\n")
            expected = install.codex_agent_previous_state(target)
            assert expected is not None
            identity = install.codex_agent_destination_identity(destination)
            concurrent = b"concurrent helper after move\n"
            real_move = install.codex_agent_native_rename_no_replace
            injected = False

            def create_after_move(directory_fd: int, source: str, backup: str) -> None:
                nonlocal injected
                real_move(directory_fd, source, backup)
                if source == target.name and not injected:
                    injected = True
                    target.write_bytes(concurrent)

            with patch.object(install, "codex_agent_native_rename_no_replace", side_effect=create_after_move):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.remove_codex_agent_if_unchanged(target, expected, destination, identity)

            self.assertEqual(target.read_bytes(), concurrent)
            backups = list(destination.glob(".*.bak"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), b"captured helper\n")
            self.assertEqual(raised.exception.preserved_paths, [backups[0].as_posix(), target.as_posix()])

    def test_install_codex_agents_write_failure_packaging_retains_primary_when_backup_cleanup_raises(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "analyze-executor.toml"
            target.write_bytes(b"captured\n")
            expected = install.codex_agent_previous_state(target)
            identity = install.codex_agent_destination_identity(destination)

            def backup_cleanup_raises(self: object, name: str, expected_state: object) -> object:
                if name.endswith(".bak"):
                    raise OSError("secondary backup cleanup failure")
                raise AssertionError("only backup cleanup should be reached")

            with (
                patch.object(install.secrets, "token_hex", return_value="tempid"),
                patch.object(install.AnchoredAgentDir, "cleanup_owned_entry", backup_cleanup_raises),
            ):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.write_codex_agent_atomic(
                        target,
                        b"installer bytes\n",
                        destination,
                        identity,
                        expected_state=expected,
                    )

            backups = list(destination.glob(".*.bak"))
            self.assertEqual(len(backups), 1)
            self.assertIn("secondary backup cleanup failure", str(raised.exception))
            self.assertIn(backups[0].as_posix(), raised.exception.preserved_paths)
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": backups[0].as_posix(), "error": "secondary_backup_cleanup_failure"},
                raised.exception.cleanup_errors,
            )

    def test_install_codex_agents_write_failure_packaging_retains_primary_when_target_read_raises(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "analyze-executor.toml"
            target.write_bytes(b"captured\n")
            expected = install.codex_agent_previous_state(target)
            identity = install.codex_agent_destination_identity(destination)
            real_previous = install.AnchoredAgentDir.previous_state

            def target_read_raises(self: object, name: str) -> object:
                if name == target.name:
                    raise OSError("secondary target read failure")
                return real_previous(self, name)

            with patch.object(install.AnchoredAgentDir, "previous_state", target_read_raises):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.write_codex_agent_atomic(
                        target,
                        b"installer bytes\n",
                        destination,
                        identity,
                        expected_state=expected,
                    )

            self.assertIn("target changed during no-clobber install", str(raised.exception))
            self.assertIn(target.as_posix(), raised.exception.preserved_paths)
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": target.as_posix(), "error": "secondary_target_read_failure"},
                raised.exception.cleanup_errors,
            )

    def test_install_codex_agents_removal_failure_packaging_retains_primary_when_backup_cleanup_raises(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "autopilot-fast-helper.toml"
            target.write_bytes(b"captured helper\n")
            expected = install.codex_agent_previous_state(target)
            assert expected is not None
            identity = install.codex_agent_destination_identity(destination)

            def backup_cleanup_raises(self: object, name: str, expected_state: object) -> object:
                if name.endswith(".bak"):
                    raise OSError("secondary backup cleanup failure")
                raise AssertionError("only backup cleanup should be reached")

            with patch.object(install.AnchoredAgentDir, "cleanup_owned_entry", backup_cleanup_raises):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.remove_codex_agent_if_unchanged(target, expected, destination, identity)

            backups = list(destination.glob(".*.bak"))
            self.assertEqual(len(backups), 1)
            self.assertIn("secondary backup cleanup failure", str(raised.exception))
            self.assertIn(backups[0].as_posix(), raised.exception.preserved_paths)
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": backups[0].as_posix(), "error": "secondary_backup_cleanup_failure"},
                raised.exception.cleanup_errors,
            )

    def test_install_codex_agents_removal_failure_packaging_retains_primary_when_target_read_raises(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "autopilot-fast-helper.toml"
            target.write_bytes(b"captured helper\n")
            expected = install.codex_agent_previous_state(target)
            assert expected is not None
            identity = install.codex_agent_destination_identity(destination)
            real_previous = install.AnchoredAgentDir.previous_state
            target_created = False

            def target_read_raises_after_create(self: object, name: str) -> object:
                nonlocal target_created
                if name == target.name:
                    if target.exists():
                        target_created = True
                        raise OSError("secondary target read failure")
                    target.write_bytes(b"concurrent removal target\n")
                    target_created = True
                    raise OSError("secondary target read failure")
                return real_previous(self, name)

            with patch.object(install.AnchoredAgentDir, "previous_state", target_read_raises_after_create):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.remove_codex_agent_if_unchanged(target, expected, destination, identity)

            self.assertTrue(target_created)
            self.assertIn("secondary target read failure", str(raised.exception))
            self.assertIn(target.as_posix(), raised.exception.preserved_paths)
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": target.as_posix(), "error": "secondary_target_read_failure"},
                raised.exception.cleanup_errors,
            )

    def test_install_codex_agents_write_restore_failure_packaging_retains_primary_when_restore_raises(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "analyze-executor.toml"
            target.write_bytes(b"captured\n")
            expected = install.codex_agent_previous_state(target)
            assert expected is not None
            identity = install.codex_agent_destination_identity(destination)
            real_previous = install.AnchoredAgentDir.previous_state

            def mismatched_backup_state(self: object, name: str) -> object:
                state = real_previous(self, name)
                if name.endswith(".bak") and state is not None:
                    return install.CodexAgentFileState(
                        content=b"changed backup state\n",
                        mode=state.mode,
                        device=state.device,
                        inode=state.inode,
                    )
                return state

            def restore_raises(self: object, backup_name: str, target_name: str) -> None:
                del self, backup_name, target_name
                raise OSError("secondary restore failure")

            with (
                patch.object(install.AnchoredAgentDir, "previous_state", mismatched_backup_state),
                patch.object(install.AnchoredAgentDir, "restore_backup_no_clobber", restore_raises),
            ):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.write_codex_agent_atomic(
                        target,
                        b"installer bytes\n",
                        destination,
                        identity,
                        expected_state=expected,
                    )

            backups = list(destination.glob(".*.bak"))
            self.assertEqual(len(backups), 1)
            self.assertIn("target changed before no-clobber install", str(raised.exception))
            self.assertIn(backups[0].as_posix(), raised.exception.preserved_paths)
            self.assertIn(target.as_posix(), raised.exception.preserved_paths)
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": backups[0].as_posix(), "error": "secondary_restore_failure"},
                raised.exception.cleanup_errors,
            )
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": target.as_posix(), "error": "secondary_restore_failure"},
                raised.exception.cleanup_errors,
            )

    def test_install_codex_agents_write_restore_failure_packaging_merges_recovery_copy_failure(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "analyze-executor.toml"
            target.write_bytes(b"captured\n")
            failed_copy = (destination / ".failed-recovery-copy").as_posix()
            expected = install.codex_agent_previous_state(target)
            assert expected is not None
            identity = install.codex_agent_destination_identity(destination)
            real_previous = install.AnchoredAgentDir.previous_state

            def mismatched_backup_state(self: object, name: str) -> object:
                state = real_previous(self, name)
                if name.endswith(".bak") and state is not None:
                    return install.CodexAgentFileState(
                        content=b"changed backup state\n",
                        mode=state.mode,
                        device=state.device,
                        inode=state.inode,
                    )
                return state

            def restore_recovery_fails(self: object, backup_name: str, target_name: str) -> None:
                del self, backup_name, target_name
                raise install.CodexAgentRecoveryCopyFailure(
                    "secondary recovery copy failure",
                    [failed_copy],
                    [target.as_posix()],
                )

            with (
                patch.object(install.AnchoredAgentDir, "previous_state", mismatched_backup_state),
                patch.object(install.AnchoredAgentDir, "restore_backup_no_clobber", restore_recovery_fails),
            ):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.write_codex_agent_atomic(
                        target,
                        b"installer bytes\n",
                        destination,
                        identity,
                        expected_state=expected,
                    )

            backups = list(destination.glob(".*.bak"))
            self.assertEqual(len(backups), 1)
            self.assertIn("target changed before no-clobber install", str(raised.exception))
            self.assertIn(backups[0].as_posix(), raised.exception.preserved_paths)
            self.assertIn(target.as_posix(), raised.exception.preserved_paths)
            self.assertIn(
                {"kind": "recovery_copy_failed", "target": failed_copy, "error": "recovery_copy_incomplete"},
                raised.exception.cleanup_errors,
            )
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": target.as_posix(), "error": "secondary_restore_failure"},
                raised.exception.cleanup_errors,
            )

    def test_install_codex_agents_removal_restore_failure_packaging_retains_primary_when_restore_raises(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "autopilot-fast-helper.toml"
            target.write_bytes(b"captured helper\n")
            expected = install.codex_agent_previous_state(target)
            assert expected is not None
            identity = install.codex_agent_destination_identity(destination)
            real_previous = install.AnchoredAgentDir.previous_state

            def mismatched_backup_state(self: object, name: str) -> object:
                state = real_previous(self, name)
                if name.endswith(".bak") and state is not None:
                    return install.CodexAgentFileState(
                        content=b"changed helper state\n",
                        mode=state.mode,
                        device=state.device,
                        inode=state.inode,
                    )
                return state

            def restore_raises(self: object, backup_name: str, target_name: str) -> None:
                del self, backup_name, target_name
                raise OSError("secondary restore failure")

            with (
                patch.object(install.AnchoredAgentDir, "previous_state", mismatched_backup_state),
                patch.object(install.AnchoredAgentDir, "restore_backup_no_clobber", restore_raises),
            ):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.remove_codex_agent_if_unchanged(target, expected, destination, identity)

            backups = list(destination.glob(".*.bak"))
            self.assertEqual(len(backups), 1)
            self.assertIn("removal target changed before no-clobber removal", str(raised.exception))
            self.assertIn(backups[0].as_posix(), raised.exception.preserved_paths)
            self.assertIn(target.as_posix(), raised.exception.preserved_paths)
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": backups[0].as_posix(), "error": "secondary_restore_failure"},
                raised.exception.cleanup_errors,
            )
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": target.as_posix(), "error": "secondary_restore_failure"},
                raised.exception.cleanup_errors,
            )

    def test_install_codex_agents_removal_restore_failure_packaging_merges_recovery_copy_failure(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "autopilot-fast-helper.toml"
            target.write_bytes(b"captured helper\n")
            failed_copy = (destination / ".failed-removal-recovery-copy").as_posix()
            expected = install.codex_agent_previous_state(target)
            assert expected is not None
            identity = install.codex_agent_destination_identity(destination)
            real_previous = install.AnchoredAgentDir.previous_state

            def mismatched_backup_state(self: object, name: str) -> object:
                state = real_previous(self, name)
                if name.endswith(".bak") and state is not None:
                    return install.CodexAgentFileState(
                        content=b"changed helper state\n",
                        mode=state.mode,
                        device=state.device,
                        inode=state.inode,
                    )
                return state

            def restore_recovery_fails(self: object, backup_name: str, target_name: str) -> None:
                del self, backup_name, target_name
                raise install.CodexAgentRecoveryCopyFailure(
                    "secondary recovery copy failure",
                    [failed_copy],
                    [target.as_posix()],
                )

            with (
                patch.object(install.AnchoredAgentDir, "previous_state", mismatched_backup_state),
                patch.object(install.AnchoredAgentDir, "restore_backup_no_clobber", restore_recovery_fails),
            ):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.remove_codex_agent_if_unchanged(target, expected, destination, identity)

            backups = list(destination.glob(".*.bak"))
            self.assertEqual(len(backups), 1)
            self.assertIn("removal target changed before no-clobber removal", str(raised.exception))
            self.assertIn(backups[0].as_posix(), raised.exception.preserved_paths)
            self.assertIn(target.as_posix(), raised.exception.preserved_paths)
            self.assertIn(
                {"kind": "recovery_copy_failed", "target": failed_copy, "error": "recovery_copy_incomplete"},
                raised.exception.cleanup_errors,
            )
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": target.as_posix(), "error": "secondary_restore_failure"},
                raised.exception.cleanup_errors,
            )

    def test_install_codex_agents_reports_persistent_backup_cleanup_failure(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "analyze-executor.toml"
            target.write_bytes(b"captured prior\n")
            expected = install.codex_agent_previous_state(target)
            identity = install.codex_agent_destination_identity(destination)
            real_unlink = install.os.unlink

            def reject_backup_cleanup(path: object, *args: object, **kwargs: object) -> None:
                if str(path).endswith(".bak") and target.exists() and target.read_bytes() == b"installer bytes\n":
                    raise OSError("persistent backup cleanup failure")
                real_unlink(path, *args, **kwargs)

            with patch.object(install.os, "unlink", side_effect=reject_backup_cleanup):
                install.write_codex_agent_atomic(
                    target,
                    b"installer bytes\n",
                    destination,
                    identity,
                    expected_state=expected,
                )

            self.assertEqual(target.read_bytes(), b"installer bytes\n")
            backups = list(destination.glob(".*.cleanup-dir/*"))
            self.assertTrue(any(path.read_bytes() == b"captured prior\n" for path in backups))

    def test_install_codex_agents_write_cleanup_race_recreates_prior_backup(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "analyze-executor.toml"
            target.write_bytes(b"captured prior\n")
            expected = install.codex_agent_previous_state(target)
            identity = install.codex_agent_destination_identity(destination)
            concurrent = destination / ".concurrent-write"
            concurrent.write_bytes(b"concurrent cleanup-window edit\n")
            real_unlink = install.os.unlink
            real_replace = os.replace
            injected = False

            def replace_during_backup_cleanup(path: object, *args: object, **kwargs: object) -> None:
                nonlocal injected
                if (
                    str(path).endswith(".bak")
                    and target.exists()
                    and target.read_bytes() == b"installer bytes\n"
                    and not injected
                ):
                    injected = True
                    real_replace(concurrent, target)
                real_unlink(path, *args, **kwargs)

            with patch.object(install.os, "unlink", side_effect=replace_during_backup_cleanup):
                install.write_codex_agent_atomic(
                    target,
                    b"installer bytes\n",
                    destination,
                    identity,
                    expected_state=expected,
                )

            self.assertFalse(injected)
            self.assertEqual(target.read_bytes(), b"installer bytes\n")
            backups = list(destination.glob(".*.cleanup-dir/*"))
            self.assertTrue(any(path.read_bytes() == b"captured prior\n" for path in backups))

    def test_install_codex_agents_removal_cleanup_race_recreates_prior_backup(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "autopilot-fast-helper.toml"
            target.write_bytes(b"captured helper\n")
            expected = install.codex_agent_previous_state(target)
            assert expected is not None
            identity = install.codex_agent_destination_identity(destination)
            real_unlink = install.os.unlink
            injected = False

            def create_during_backup_cleanup(path: object, *args: object, **kwargs: object) -> None:
                nonlocal injected
                if str(path).endswith(".bak") and not target.exists() and not injected:
                    injected = True
                    target.write_bytes(b"concurrent removal-window edit\n")
                real_unlink(path, *args, **kwargs)

            with patch.object(install.os, "unlink", side_effect=create_during_backup_cleanup):
                install.remove_codex_agent_if_unchanged(target, expected, destination, identity)

            self.assertFalse(injected)
            self.assertFalse(target.exists())
            backups = list(destination.glob(".*.cleanup-dir/*"))
            self.assertTrue(any(path.read_bytes() == b"captured helper\n" for path in backups))

    def test_install_codex_agents_restore_cleanup_race_recreates_prior_backup(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            backup = destination / ".agent.toml.initial.bak"
            target = destination / "agent.toml"
            backup.write_bytes(b"captured rollback state\n")
            concurrent = destination / ".concurrent-restore"
            concurrent.write_bytes(b"concurrent restore-window edit\n")
            real_unlink = install.os.unlink
            real_replace = os.replace
            injected = False

            def replace_during_backup_cleanup(path: object, *args: object, **kwargs: object) -> None:
                nonlocal injected
                if str(path).endswith(".bak") and not injected:
                    injected = True
                    real_replace(concurrent, target)
                real_unlink(path, *args, **kwargs)

            with patch.object(install.os, "unlink", side_effect=replace_during_backup_cleanup):
                install.codex_agent_restore_backup_no_clobber(backup, target)

            self.assertFalse(injected)
            self.assertEqual(target.read_bytes(), b"captured rollback state\n")
            self.assertFalse(backup.exists())
            self.assertEqual(list(destination.glob(".*.cleanup-dir/*")), [])

    def test_install_codex_agents_transient_temp_cleanup_does_not_report_removed_path(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "analyze-executor.toml"
            target.write_bytes(b"captured prior\n")
            expected = install.codex_agent_previous_state(target)
            identity = install.codex_agent_destination_identity(destination)
            real_unlink = install.os.unlink
            rejected = False

            def reject_first_temp_cleanup(path: object, *args: object, **kwargs: object) -> None:
                nonlocal rejected
                if str(path).endswith(".tmp") and not rejected:
                    rejected = True
                    raise OSError("transient temp cleanup failure")
                real_unlink(path, *args, **kwargs)

            with patch.object(install.os, "unlink", side_effect=reject_first_temp_cleanup):
                install.write_codex_agent_atomic(
                    target,
                    b"installer bytes\n",
                    destination,
                    identity,
                    expected_state=expected,
                )

            self.assertFalse(rejected)
            self.assertEqual(target.read_bytes(), b"installer bytes\n")
            self.assertFalse(any(path.name.endswith(".tmp") for path in destination.glob(".*.cleanup-dir/*")))

    def test_install_codex_agents_temp_cleanup_preserves_takeover_entry(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "analyze-executor.toml"
            identity = install.codex_agent_destination_identity(destination)
            concurrent = b"concurrent temp takeover\n"
            injected = False

            def takeover_temp_before_failed_publish(directory_fd: int, source: str, target_name: str) -> None:
                nonlocal injected
                if source.endswith(".tmp") and target_name == target.name and not injected:
                    injected = True
                    (destination / source).unlink()
                    (destination / str(source)).write_bytes(concurrent)
                    raise OSError("injected publish failure after temp takeover")
                raise OSError("injected publish failure")

            with patch.object(install, "codex_agent_native_rename_no_replace", side_effect=takeover_temp_before_failed_publish):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.write_codex_agent_atomic(
                        target,
                        b"installer bytes\n",
                        destination,
                        identity,
                        expected_state=None,
                    )

            temps = list(destination.glob(".*.tmp"))
            self.assertEqual(len(temps), 1)
            self.assertEqual(temps[0].read_bytes(), concurrent)
            self.assertIn(temps[0].as_posix(), raised.exception.preserved_paths)

    def test_install_codex_agents_backup_cleanup_preserves_takeover_entry(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "analyze-executor.toml"
            target.write_bytes(b"captured prior\n")
            expected = install.codex_agent_previous_state(target)
            identity = install.codex_agent_destination_identity(destination)
            real_state_matches = install.AnchoredAgentDir.state_matches
            concurrent = b"concurrent backup takeover\n"
            injected = False

            def takeover_backup_before_cleanup(agent_dir: object, name: str, expected_state: object) -> bool:
                nonlocal injected
                if name == target.name and expected_state is not None and not injected:
                    backups = list(destination.glob(".*.bak"))
                    if backups:
                        injected = True
                        backups[0].write_bytes(concurrent)
                return real_state_matches(agent_dir, name, expected_state)

            with patch.object(install.AnchoredAgentDir, "state_matches", takeover_backup_before_cleanup):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.write_codex_agent_atomic(
                        target,
                        b"installer bytes\n",
                        destination,
                        identity,
                        expected_state=expected,
                    )

            backups = list(destination.glob(".*.bak"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), concurrent)
            self.assertEqual(target.read_bytes(), b"installer bytes\n")
            self.assertEqual(raised.exception.preserved_paths, [backups[0].as_posix(), target.as_posix()])

    def test_install_codex_agents_cleanup_owned_entry_final_unlink_takeover_preserves_victim(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target_name = "agent.tmp"
            target = destination / target_name
            target.write_bytes(b"installer-owned cleanup\n")
            identity = install.codex_agent_destination_identity(destination)
            agent_dir = install.AnchoredAgentDir.open(destination, identity)
            state = agent_dir.previous_state(target_name)
            assert state is not None

            try:
                with patch.object(install.secrets, "token_hex", return_value="cleanupid"):
                    conflicts = agent_dir.cleanup_owned_entry(target_name, state)
            finally:
                agent_dir.close()

            preserved = destination / ".cleanupid.cleanup-dir" / ".cleanupid.cleanup.agent.tmp"
            private_dir = destination / ".cleanupid.cleanup-dir"
            self.assertFalse((destination / ".cleanupid.cleanup.agent.tmp").exists())
            self.assertEqual(preserved.read_bytes(), b"installer-owned cleanup\n")
            self.assertEqual(conflicts.preserved_private_paths, [preserved.as_posix(), private_dir.as_posix()])
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": private_dir.as_posix(), "error": "private_quarantine_dir_not_empty"},
                conflicts.cleanup_errors,
            )

    def test_install_codex_agents_cleanup_private_restore_no_replace_preserves_public_takeover(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target_name = "agent.tmp"
            target = destination / target_name
            target.write_bytes(b"installer-owned cleanup\n")
            identity = install.codex_agent_destination_identity(destination)
            agent_dir = install.AnchoredAgentDir.open(destination, identity)
            state = agent_dir.previous_state(target_name)
            assert state is not None
            cleanup_name = ".cleanupid.cleanup.agent.tmp"
            cleanup_path = destination / cleanup_name
            real_unlink = install.os.unlink
            real_no_replace_between = install.codex_agent_native_rename_no_replace_between
            injected = False

            def force_private_unlink_failure(path: object, *args: object, **kwargs: object) -> None:
                if path == cleanup_name and kwargs.get("dir_fd") != agent_dir.directory_fd:
                    raise OSError("injected private unlink failure")
                real_unlink(path, *args, **kwargs)

            def inject_public_takeover_before_private_restore(
                source_directory_fd: int,
                source_name: str,
                target_directory_fd: int,
                target_name: str,
            ) -> None:
                nonlocal injected
                if (
                    source_name == cleanup_name
                    and target_name == cleanup_name
                    and target_directory_fd == agent_dir.directory_fd
                    and source_directory_fd != agent_dir.directory_fd
                    and not injected
                ):
                    injected = True
                    cleanup_path.write_bytes(b"public takeover must survive\n")
                    raise FileExistsError(errno.EEXIST, "public takeover", cleanup_name)
                real_no_replace_between(source_directory_fd, source_name, target_directory_fd, target_name)

            try:
                with (
                    patch.object(install.secrets, "token_hex", return_value="cleanupid"),
                    patch.object(install.os, "unlink", side_effect=force_private_unlink_failure),
                    patch.object(
                        install,
                        "codex_agent_native_rename_no_replace_between",
                        side_effect=inject_public_takeover_before_private_restore,
                    ),
                ):
                    conflicts = agent_dir.cleanup_owned_entry(target_name, state)
            finally:
                agent_dir.close()

            preserved = destination / ".cleanupid.cleanup-dir" / ".cleanupid.cleanup.agent.tmp"
            private_dir = destination / ".cleanupid.cleanup-dir"
            self.assertFalse(injected)
            self.assertFalse(cleanup_path.exists())
            self.assertEqual(conflicts.preserved_private_paths, [preserved.as_posix(), private_dir.as_posix()])
            self.assertEqual(preserved.read_bytes(), b"installer-owned cleanup\n")
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": private_dir.as_posix(), "error": "private_quarantine_dir_not_empty"},
                conflicts.cleanup_errors,
            )

    def test_install_codex_agents_posix_cleanup_preserves_verified_quarantine_without_unlink(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target_name = "agent.tmp"
            target = destination / target_name
            target.write_bytes(b"installer-owned cleanup\n")
            hardlink = destination / "agent-hardlink.tmp"
            os.link(target, hardlink)
            identity = install.codex_agent_destination_identity(destination)
            agent_dir = install.AnchoredAgentDir.open(destination, identity)
            state = agent_dir.previous_state(target_name)
            assert state is not None
            real_unlink = install.os.unlink
            private_unlink_attempted = False

            def reject_private_quarantine_unlink(path: object, *args: object, **kwargs: object) -> None:
                nonlocal private_unlink_attempted
                if path == ".cleanupid.cleanup.agent.tmp" and kwargs.get("dir_fd") != agent_dir.directory_fd:
                    private_unlink_attempted = True
                    raise AssertionError("POSIX cleanup must preserve verified quarantine instead of unlinking it")
                real_unlink(path, *args, **kwargs)

            try:
                with (
                    patch.object(install.secrets, "token_hex", return_value="cleanupid"),
                    patch.object(install.os, "unlink", side_effect=reject_private_quarantine_unlink),
                ):
                    conflicts = agent_dir.cleanup_owned_entry(target_name, state)
            finally:
                agent_dir.close()

            preserved = destination / ".cleanupid.cleanup-dir" / ".cleanupid.cleanup.agent.tmp"
            private_dir = destination / ".cleanupid.cleanup-dir"
            self.assertFalse(private_unlink_attempted)
            self.assertEqual(conflicts.preserved_private_paths, [preserved.as_posix(), private_dir.as_posix()])
            self.assertEqual(preserved.read_bytes(), b"installer-owned cleanup\n")
            self.assertEqual(hardlink.read_bytes(), b"installer-owned cleanup\n")
            self.assertGreaterEqual(preserved.stat().st_nlink, 2)
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": private_dir.as_posix(), "error": "private_quarantine_dir_not_empty"},
                conflicts.cleanup_errors,
            )

    def test_install_codex_agents_posix_private_quarantine_collision_preserves_both_entries(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target_name = "agent.tmp"
            target = destination / target_name
            target.write_bytes(b"installer-owned cleanup\n")
            identity = install.codex_agent_destination_identity(destination)
            agent_dir = install.AnchoredAgentDir.open(destination, identity)
            state = agent_dir.previous_state(target_name)
            assert state is not None
            cleanup_name = ".moveid.cleanup.agent.tmp"
            private_dir_name = ".dirid.cleanup-dir"
            public_cleanup = destination / cleanup_name
            private_victim = destination / private_dir_name / cleanup_name
            victim_link = destination / "victim-hardlink.tmp"
            real_open = install.os.open
            injected = False

            def inject_private_destination_collision(path: object, flags: int, *args: object, **kwargs: object) -> int:
                nonlocal injected
                if path == private_dir_name and kwargs.get("dir_fd") == agent_dir.directory_fd and not injected:
                    injected = True
                    private_victim.write_bytes(b"private victim\n")
                    os.link(private_victim, victim_link)
                return real_open(path, flags, *args, **kwargs)

            try:
                with (
                    patch.object(install.secrets, "token_hex", side_effect=["moveid", "dirid"]),
                    patch.object(install.os, "open", side_effect=inject_private_destination_collision),
                ):
                    result = agent_dir.cleanup_owned_entry(target_name, state)
            finally:
                agent_dir.close()

            self.assertTrue(injected)
            self.assertEqual(public_cleanup.read_bytes(), b"installer-owned cleanup\n")
            self.assertEqual(private_victim.read_bytes(), b"private victim\n")
            self.assertEqual(victim_link.read_bytes(), b"private victim\n")
            self.assertEqual(private_victim.stat().st_ino, victim_link.stat().st_ino)
            self.assertGreaterEqual(victim_link.stat().st_nlink, 2)
            self.assertIn(public_cleanup.as_posix(), result.public_conflicts)
            self.assertIn(private_victim.as_posix(), result.preserved_private_paths)
            self.assertIn(
                {
                    "kind": "preserved_cleanup_entry",
                    "target": public_cleanup.as_posix(),
                    "error": "private_quarantine_collision",
                },
                result.cleanup_errors,
            )
            self.assertIn(
                {
                    "kind": "preserved_concurrent_file",
                    "target": private_victim.as_posix(),
                    "error": "private_quarantine_collision",
                },
                result.cleanup_errors,
            )
            self.assertNotIn(
                {
                    "kind": "preserved_cleanup_entry",
                    "target": private_victim.as_posix(),
                    "error": "fd_bound_delete_unavailable",
                },
                result.cleanup_errors,
            )
            remediation = install.codex_route_aware_cleanup_manual_remediation(result.cleanup_errors)
            cleanup_action = next(action for action in remediation if action["reason"] == "cleanup_incomplete")
            concurrent_action = next(action for action in remediation if action["reason"] == "concurrent_file_preserved")
            self.assertIn(public_cleanup.as_posix(), cleanup_action["paths"])
            self.assertNotIn(private_victim.as_posix(), cleanup_action["paths"])
            self.assertIn(private_victim.as_posix(), concurrent_action["paths"])
            concurrent_text = " ".join([concurrent_action["summary"], *concurrent_action["recommended_actions"]])
            self.assertIn("unknown/private concurrent data", concurrent_text)

    def test_install_codex_agents_posix_private_quarantine_file_not_found_preserves_private_residue(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            cleanup_name = ".lost.cleanup.agent.tmp"
            public_cleanup = destination / cleanup_name
            public_cleanup.write_bytes(b"installer-owned cleanup\n")
            identity = install.codex_agent_destination_identity(destination)
            agent_dir = install.AnchoredAgentDir.open(destination, identity)
            expected_state = agent_dir.previous_state(cleanup_name)
            assert expected_state is not None
            private_dir_name = ".dirid.cleanup-dir"
            private_victim = destination / private_dir_name / cleanup_name

            def fail_missing_after_private_residue(*_args: object, **_kwargs: object) -> None:
                public_cleanup.unlink()
                private_victim.write_bytes(b"private residue after missing source\n")
                raise FileNotFoundError(cleanup_name)

            try:
                with (
                    patch.object(install.secrets, "token_hex", return_value="dirid"),
                    patch.object(
                        install,
                        "codex_agent_native_rename_no_replace_between",
                        side_effect=fail_missing_after_private_residue,
                    ),
                ):
                    result = agent_dir.cleanup_verified_quarantine(cleanup_name, expected_state)
            finally:
                agent_dir.close()

            self.assertFalse(public_cleanup.exists())
            self.assertEqual(private_victim.read_bytes(), b"private residue after missing source\n")
            self.assertEqual(result.public_conflicts, [])
            self.assertEqual(result.preserved_private_paths, [private_victim.as_posix(), (destination / private_dir_name).as_posix()])
            self.assertIn(
                {
                    "kind": "preserved_concurrent_file",
                    "target": private_victim.as_posix(),
                    "error": "private_quarantine_file_not_found",
                },
                result.cleanup_errors,
            )
            self.assertFalse(
                any(
                    error["kind"] == "preserved_cleanup_entry" and error["target"] == private_victim.as_posix()
                    for error in result.cleanup_errors
                )
            )
            remediation = install.codex_route_aware_cleanup_manual_remediation(result.cleanup_errors)
            self.assertNotIn("cleanup_incomplete", [action["reason"] for action in remediation])
            concurrent_action = next(action for action in remediation if action["reason"] == "concurrent_file_preserved")
            self.assertEqual(concurrent_action["paths"], [private_victim.as_posix(), (destination / private_dir_name).as_posix()])
            self.assertIn(
                "unknown/private concurrent data",
                " ".join([concurrent_action["summary"], *concurrent_action["recommended_actions"]]),
            )

    def test_install_codex_agents_posix_private_quarantine_move_error_classifies_public_and_private(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            cleanup_name = ".failed.cleanup.agent.tmp"
            public_cleanup = destination / cleanup_name
            public_cleanup.write_bytes(b"installer-owned cleanup\n")
            identity = install.codex_agent_destination_identity(destination)
            agent_dir = install.AnchoredAgentDir.open(destination, identity)
            expected_state = agent_dir.previous_state(cleanup_name)
            assert expected_state is not None
            private_dir_name = ".dirid.cleanup-dir"
            private_victim = destination / private_dir_name / cleanup_name

            def fail_move_after_private_leaf(*_args: object, **_kwargs: object) -> None:
                private_victim.write_bytes(b"private victim after failed move\n")
                raise OSError("injected move failure")

            try:
                with (
                    patch.object(install.secrets, "token_hex", return_value="dirid"),
                    patch.object(
                        install,
                        "codex_agent_native_rename_no_replace_between",
                        side_effect=fail_move_after_private_leaf,
                    ),
                ):
                    result = agent_dir.cleanup_verified_quarantine(cleanup_name, expected_state)
            finally:
                agent_dir.close()

            self.assertEqual(public_cleanup.read_bytes(), b"installer-owned cleanup\n")
            self.assertEqual(private_victim.read_bytes(), b"private victim after failed move\n")
            self.assertEqual(result.public_conflicts, [public_cleanup.as_posix()])
            self.assertEqual(result.preserved_private_paths, [private_victim.as_posix(), (destination / private_dir_name).as_posix()])
            self.assertIn(
                {
                    "kind": "preserved_cleanup_entry",
                    "target": public_cleanup.as_posix(),
                    "error": "private_quarantine_move_failed",
                },
                result.cleanup_errors,
            )
            self.assertIn(
                {
                    "kind": "preserved_concurrent_file",
                    "target": private_victim.as_posix(),
                    "error": "private_quarantine_move_failed",
                },
                result.cleanup_errors,
            )
            remediation = install.codex_route_aware_cleanup_manual_remediation(result.cleanup_errors)
            cleanup_action = next(action for action in remediation if action["reason"] == "cleanup_incomplete")
            concurrent_action = next(action for action in remediation if action["reason"] == "concurrent_file_preserved")
            self.assertEqual(cleanup_action["paths"], [public_cleanup.as_posix()])
            self.assertEqual(concurrent_action["paths"], [private_victim.as_posix(), (destination / private_dir_name).as_posix()])

    def test_install_codex_agents_posix_private_quarantine_post_move_mismatch_classifies_public_original(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            cleanup_name = ".mismatch.cleanup.agent.tmp"
            public_cleanup = destination / cleanup_name
            public_cleanup.write_bytes(b"installer-owned cleanup\n")
            identity = install.codex_agent_destination_identity(destination)
            agent_dir = install.AnchoredAgentDir.open(destination, identity)
            expected_state = agent_dir.previous_state(cleanup_name)
            assert expected_state is not None
            private_dir_name = ".dirid.cleanup-dir"
            private_victim = destination / private_dir_name / cleanup_name

            def report_success_with_private_victim(*_args: object, **_kwargs: object) -> None:
                private_victim.write_bytes(b"private victim after reported move\n")

            try:
                with (
                    patch.object(install.secrets, "token_hex", return_value="dirid"),
                    patch.object(
                        install,
                        "codex_agent_native_rename_no_replace_between",
                        side_effect=report_success_with_private_victim,
                    ),
                ):
                    result = agent_dir.cleanup_verified_quarantine(cleanup_name, expected_state)
            finally:
                agent_dir.close()

            self.assertEqual(public_cleanup.read_bytes(), b"installer-owned cleanup\n")
            self.assertEqual(private_victim.read_bytes(), b"private victim after reported move\n")
            self.assertEqual(result.public_conflicts, [public_cleanup.as_posix()])
            self.assertEqual(result.preserved_private_paths, [private_victim.as_posix(), (destination / private_dir_name).as_posix()])
            self.assertIn(
                {
                    "kind": "preserved_cleanup_entry",
                    "target": public_cleanup.as_posix(),
                    "error": "private_quarantine_identity_mismatch",
                },
                result.cleanup_errors,
            )
            self.assertIn(
                {
                    "kind": "preserved_concurrent_file",
                    "target": private_victim.as_posix(),
                    "error": "private_quarantine_identity_mismatch",
                },
                result.cleanup_errors,
            )
            self.assertFalse(
                any(
                    error["kind"] == "preserved_cleanup_entry" and error["target"] == private_victim.as_posix()
                    for error in result.cleanup_errors
                )
            )
            remediation = install.codex_route_aware_cleanup_manual_remediation(result.cleanup_errors)
            cleanup_action = next(action for action in remediation if action["reason"] == "cleanup_incomplete")
            concurrent_action = next(action for action in remediation if action["reason"] == "concurrent_file_preserved")
            self.assertEqual(cleanup_action["paths"], [public_cleanup.as_posix()])
            self.assertEqual(concurrent_action["paths"], [private_victim.as_posix(), (destination / private_dir_name).as_posix()])

    def test_install_codex_agents_posix_private_quarantine_public_read_error_is_concurrent_unknown(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            cleanup_name = ".unreadable.cleanup.agent.tmp"
            public_cleanup = destination / cleanup_name
            public_cleanup.write_bytes(b"installer-owned cleanup\n")
            identity = install.codex_agent_destination_identity(destination)
            agent_dir = install.AnchoredAgentDir.open(destination, identity)
            expected_state = agent_dir.previous_state(cleanup_name)
            assert expected_state is not None
            real_previous_state = agent_dir.previous_state
            classify_public = False

            def fail_public_classification(name: str) -> object:
                if classify_public and name == cleanup_name:
                    raise OSError("injected public read error")
                return real_previous_state(name)

            def fail_move(*_args: object, **_kwargs: object) -> None:
                nonlocal classify_public
                classify_public = True
                raise OSError("injected move failure")

            try:
                with (
                    patch.object(install.secrets, "token_hex", return_value="dirid"),
                    patch.object(agent_dir, "previous_state", side_effect=fail_public_classification),
                    patch.object(install, "codex_agent_native_rename_no_replace_between", side_effect=fail_move),
                ):
                    result = agent_dir.cleanup_verified_quarantine(cleanup_name, expected_state)
            finally:
                agent_dir.close()

            self.assertEqual(public_cleanup.read_bytes(), b"installer-owned cleanup\n")
            self.assertIn(public_cleanup.as_posix(), result.public_conflicts)
            self.assertIn(
                {
                    "kind": "preserved_concurrent_file",
                    "target": public_cleanup.as_posix(),
                    "error": "private_quarantine_move_failed",
                },
                result.cleanup_errors,
            )
            self.assertNotIn(
                {
                    "kind": "cleanup_incomplete",
                    "target": public_cleanup.as_posix(),
                    "error": "private_quarantine_move_failed",
                },
                result.cleanup_errors,
            )
            remediation = install.codex_route_aware_cleanup_manual_remediation(result.cleanup_errors)
            self.assertEqual([action["reason"] for action in remediation], ["concurrent_file_preserved"])

    def test_install_codex_agents_posix_private_quarantine_mkdir_failure_preserves_public_cleanup(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            cleanup_name = ".mkdirfail.cleanup.agent.tmp"
            public_cleanup = destination / cleanup_name
            public_cleanup.write_bytes(b"installer-owned cleanup\n")
            identity = install.codex_agent_destination_identity(destination)
            agent_dir = install.AnchoredAgentDir.open(destination, identity)
            expected_state = agent_dir.previous_state(cleanup_name)
            assert expected_state is not None

            try:
                with patch.object(install.os, "mkdir", side_effect=OSError("injected mkdir failure")):
                    result = agent_dir.cleanup_verified_quarantine(cleanup_name, expected_state)
            finally:
                agent_dir.close()

            self.assertEqual(public_cleanup.read_bytes(), b"installer-owned cleanup\n")
            self.assertEqual(result.public_conflicts, [public_cleanup.as_posix()])
            self.assertIn(
                {
                    "kind": "preserved_cleanup_entry",
                    "target": public_cleanup.as_posix(),
                    "error": "private_quarantine_dir_unavailable",
                },
                result.cleanup_errors,
            )

    def test_install_codex_agents_posix_private_quarantine_open_failure_preserves_private_dir_unknown(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            cleanup_name = ".openfail.cleanup.agent.tmp"
            public_cleanup = destination / cleanup_name
            public_cleanup.write_bytes(b"installer-owned cleanup\n")
            private_dir_name = ".dirid.cleanup-dir"
            private_dir = destination / private_dir_name
            identity = install.codex_agent_destination_identity(destination)
            agent_dir = install.AnchoredAgentDir.open(destination, identity)
            expected_state = agent_dir.previous_state(cleanup_name)
            assert expected_state is not None
            real_open = install.os.open

            def fail_private_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
                if path == private_dir_name and kwargs.get("dir_fd") == agent_dir.directory_fd:
                    raise OSError("injected private open failure")
                return real_open(path, flags, *args, **kwargs)

            try:
                with (
                    patch.object(install.secrets, "token_hex", return_value="dirid"),
                    patch.object(install.os, "open", side_effect=fail_private_open),
                ):
                    result = agent_dir.cleanup_verified_quarantine(cleanup_name, expected_state)
            finally:
                agent_dir.close()

            self.assertEqual(public_cleanup.read_bytes(), b"installer-owned cleanup\n")
            self.assertTrue(private_dir.exists())
            self.assertIn(public_cleanup.as_posix(), result.public_conflicts)
            self.assertIn(private_dir.as_posix(), result.preserved_private_paths)
            self.assertIn(
                {
                    "kind": "preserved_cleanup_entry",
                    "target": public_cleanup.as_posix(),
                    "error": "private_quarantine_open_failed",
                },
                result.cleanup_errors,
            )
            self.assertIn(
                {
                    "kind": "preserved_concurrent_file",
                    "target": private_dir.as_posix(),
                    "error": "private_quarantine_open_failed",
                },
                result.cleanup_errors,
            )

    def test_install_codex_agents_posix_private_quarantine_close_and_rmdir_failures_are_evidence(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            cleanup_name = ".cleanupfail.cleanup.agent.tmp"
            public_cleanup = destination / cleanup_name
            public_cleanup.write_bytes(b"installer-owned cleanup\n")
            private_dir_name = ".dirid.cleanup-dir"
            private_dir = destination / private_dir_name
            private_leaf = private_dir / cleanup_name
            identity = install.codex_agent_destination_identity(destination)
            agent_dir = install.AnchoredAgentDir.open(destination, identity)
            expected_state = agent_dir.previous_state(cleanup_name)
            assert expected_state is not None
            real_open = install.os.open
            real_close = install.os.close
            real_rmdir = install.os.rmdir
            private_fds: set[int] = set()

            def record_private_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
                descriptor = real_open(path, flags, *args, **kwargs)
                if path == private_dir_name and kwargs.get("dir_fd") == agent_dir.directory_fd:
                    private_fds.add(descriptor)
                return descriptor

            def fail_private_close(descriptor: int) -> None:
                real_close(descriptor)
                if descriptor in private_fds:
                    raise OSError("injected private close failure")

            def fail_private_rmdir(path: object, *args: object, **kwargs: object) -> None:
                if path == private_dir_name and kwargs.get("dir_fd") == agent_dir.directory_fd:
                    raise OSError("injected private rmdir failure")
                real_rmdir(path, *args, **kwargs)

            try:
                with (
                    patch.object(install.secrets, "token_hex", return_value="dirid"),
                    patch.object(install.os, "open", side_effect=record_private_open),
                    patch.object(install.os, "close", side_effect=fail_private_close),
                    patch.object(install.os, "rmdir", side_effect=fail_private_rmdir),
                ):
                    result = agent_dir.cleanup_verified_quarantine(cleanup_name, expected_state)
            finally:
                agent_dir.close()

            self.assertFalse(public_cleanup.exists())
            self.assertEqual(private_leaf.read_bytes(), b"installer-owned cleanup\n")
            self.assertIn(private_leaf.as_posix(), result.preserved_private_paths)
            self.assertIn(
                {"kind": "close_descriptor", "target": private_dir.as_posix(), "error": "OSError"},
                result.cleanup_errors,
            )
            self.assertIn(
                {"kind": "remove_directory", "target": private_dir.as_posix(), "error": "OSError"},
                result.cleanup_errors,
            )

    def test_install_codex_agents_posix_private_quarantine_real_enotempty_reports_private_dir_unknown(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            cleanup_name = ".enotempty.cleanup.agent.tmp"
            public_cleanup = destination / cleanup_name
            public_cleanup.write_bytes(b"installer-owned cleanup\n")
            private_dir_name = ".dirid.cleanup-dir"
            private_dir = destination / private_dir_name
            unknown_child = private_dir / "unknown-child"
            identity = install.codex_agent_destination_identity(destination)
            agent_dir = install.AnchoredAgentDir.open(destination, identity)
            expected_state = agent_dir.previous_state(cleanup_name)
            assert expected_state is not None
            real_move = install.codex_agent_native_rename_no_replace_between

            def move_then_add_unknown_child(*args: object, **kwargs: object) -> None:
                real_move(*args, **kwargs)
                unknown_child.write_bytes(b"unknown child\n")

            try:
                with (
                    patch.object(install.secrets, "token_hex", return_value="dirid"),
                    patch.object(install, "codex_agent_native_rename_no_replace_between", side_effect=move_then_add_unknown_child),
                ):
                    result = agent_dir.cleanup_verified_quarantine(cleanup_name, expected_state)
            finally:
                agent_dir.close()

            self.assertFalse(public_cleanup.exists())
            self.assertEqual(unknown_child.read_bytes(), b"unknown child\n")
            self.assertIn(private_dir.as_posix(), result.preserved_private_paths)
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": private_dir.as_posix(), "error": "private_quarantine_dir_not_empty"},
                result.cleanup_errors,
            )

    def test_install_codex_agents_posix_private_quarantine_late_rmdir_child_reports_private_dir_unknown(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            cleanup_name = ".latechild.cleanup.agent.tmp"
            public_cleanup = destination / cleanup_name
            public_cleanup.write_bytes(b"installer-owned cleanup\n")
            private_dir_name = ".dirid.cleanup-dir"
            private_dir = destination / private_dir_name
            private_leaf = private_dir / cleanup_name
            late_child = private_dir / "late-child"
            identity = install.codex_agent_destination_identity(destination)
            agent_dir = install.AnchoredAgentDir.open(destination, identity)
            expected_state = agent_dir.previous_state(cleanup_name)
            assert expected_state is not None
            real_rmdir = install.os.rmdir

            def inject_late_child_before_rmdir(path: object, *args: object, **kwargs: object) -> None:
                if path == private_dir_name and kwargs.get("dir_fd") == agent_dir.directory_fd:
                    late_child.write_bytes(b"late concurrent child\n")
                    raise OSError(errno.ENOTEMPTY, "directory not empty")
                real_rmdir(path, *args, **kwargs)

            try:
                with (
                    patch.object(install.secrets, "token_hex", return_value="dirid"),
                    patch.object(install.os, "rmdir", side_effect=inject_late_child_before_rmdir),
                ):
                    result = agent_dir.cleanup_verified_quarantine(cleanup_name, expected_state)
            finally:
                agent_dir.close()

            self.assertFalse(public_cleanup.exists())
            self.assertEqual(private_leaf.read_bytes(), b"installer-owned cleanup\n")
            self.assertEqual(late_child.read_bytes(), b"late concurrent child\n")
            self.assertIn(private_leaf.as_posix(), result.preserved_private_paths)
            self.assertIn(private_dir.as_posix(), result.preserved_private_paths)
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": private_dir.as_posix(), "error": "private_quarantine_dir_not_empty"},
                result.cleanup_errors,
            )

    def test_install_codex_agents_posix_private_quarantine_backslash_child_reports_private_dir_unknown(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            cleanup_name = ".backslash.cleanup.agent.tmp"
            public_cleanup = destination / cleanup_name
            public_cleanup.write_bytes(b"installer-owned cleanup\n")
            private_dir_name = ".dirid.cleanup-dir"
            private_dir = destination / private_dir_name
            private_leaf = private_dir / cleanup_name
            backslash_child = private_dir / "valid\\posix-child"
            identity = install.codex_agent_destination_identity(destination)
            agent_dir = install.AnchoredAgentDir.open(destination, identity)
            expected_state = agent_dir.previous_state(cleanup_name)
            assert expected_state is not None
            real_move = install.codex_agent_native_rename_no_replace_between

            def move_then_add_backslash_child(*args: object, **kwargs: object) -> None:
                real_move(*args, **kwargs)
                backslash_child.write_bytes(b"valid POSIX backslash child\n")

            try:
                with (
                    patch.object(install.secrets, "token_hex", return_value="dirid"),
                    patch.object(install, "codex_agent_native_rename_no_replace_between", side_effect=move_then_add_backslash_child),
                ):
                    result = agent_dir.cleanup_verified_quarantine(cleanup_name, expected_state)
            finally:
                agent_dir.close()

            self.assertFalse(public_cleanup.exists())
            self.assertEqual(private_leaf.read_bytes(), b"installer-owned cleanup\n")
            self.assertEqual(backslash_child.read_bytes(), b"valid POSIX backslash child\n")
            self.assertIn(private_dir.as_posix(), result.preserved_private_paths)
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": private_dir.as_posix(), "error": "private_quarantine_dir_not_empty"},
                result.cleanup_errors,
            )

    def test_install_codex_agents_posix_cleanup_restore_collision_read_error_reports_both_names(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target_name = "agent.tmp"
            target = destination / target_name
            target.write_bytes(b"installer-owned cleanup\n")
            cleanup_name = ".moveid.cleanup.agent.tmp"
            cleanup_path = destination / cleanup_name
            identity = install.codex_agent_destination_identity(destination)
            agent_dir = install.AnchoredAgentDir.open(destination, identity)
            expected_state = agent_dir.previous_state(target_name)
            assert expected_state is not None
            real_rename = install.codex_agent_native_rename_no_replace
            restore_collision = False
            real_previous = agent_dir.previous_state

            def move_then_recreate(directory_fd: int, source: str, target_name_arg: str) -> None:
                nonlocal restore_collision
                if source == target_name:
                    real_rename(directory_fd, source, target_name_arg)
                    cleanup_path.write_bytes(b"mismatched cleanup bytes\n")
                    target.write_bytes(b"recreated target bytes\n")
                    return
                if source == cleanup_name and target_name_arg == target_name:
                    restore_collision = True
                    raise FileExistsError(target_name)
                real_rename(directory_fd, source, target_name_arg)

            def target_read_error(name: str) -> object:
                if restore_collision and name == target_name:
                    raise OSError("injected recreated-target read error")
                return real_previous(name)

            try:
                with (
                    patch.object(install.secrets, "token_hex", return_value="moveid"),
                    patch.object(install, "codex_agent_native_rename_no_replace", side_effect=move_then_recreate),
                    patch.object(agent_dir, "previous_state", side_effect=target_read_error),
                ):
                    result = agent_dir.cleanup_owned_entry(target_name, expected_state)
            finally:
                agent_dir.close()

            self.assertEqual(cleanup_path.read_bytes(), b"mismatched cleanup bytes\n")
            self.assertEqual(target.read_bytes(), b"recreated target bytes\n")
            self.assertEqual(result.public_conflicts, [cleanup_path.as_posix(), target.as_posix()])
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": cleanup_path.as_posix(), "error": "cleanup_restore_collision"},
                result.cleanup_errors,
            )
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": target.as_posix(), "error": "cleanup_restore_collision"},
                result.cleanup_errors,
            )

    def test_install_codex_agents_posix_cleanup_restore_success_without_reappearance_has_no_phantom_source(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target_name = "agent.tmp"
            target = destination / target_name
            target.write_bytes(b"installer-owned cleanup\n")
            cleanup_name = ".moveid.cleanup.agent.tmp"
            cleanup_path = destination / cleanup_name
            identity = install.codex_agent_destination_identity(destination)
            agent_dir = install.AnchoredAgentDir.open(destination, identity)
            expected_state = agent_dir.previous_state(target_name)
            assert expected_state is not None
            real_rename = install.codex_agent_native_rename_no_replace

            def mismatch_then_restore(directory_fd: int, source: str, target_name_arg: str) -> None:
                if source == target_name:
                    real_rename(directory_fd, source, target_name_arg)
                    cleanup_path.write_bytes(b"mismatched cleanup bytes\n")
                    return
                real_rename(directory_fd, source, target_name_arg)

            try:
                with (
                    patch.object(install.secrets, "token_hex", return_value="moveid"),
                    patch.object(install, "codex_agent_native_rename_no_replace", side_effect=mismatch_then_restore),
                ):
                    result = agent_dir.cleanup_owned_entry(target_name, expected_state)
            finally:
                agent_dir.close()

            self.assertFalse(cleanup_path.exists())
            self.assertEqual(target.read_bytes(), b"mismatched cleanup bytes\n")
            self.assertEqual(result.public_conflicts, [target.as_posix()])
            self.assertNotIn(cleanup_path.as_posix(), result.preserved_paths)
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": target.as_posix(), "error": "cleanup_restore_collision"},
                result.cleanup_errors,
            )

    def test_install_codex_agents_posix_cleanup_restore_success_reclassifies_source_reappearance(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target_name = "agent.tmp"
            target = destination / target_name
            target.write_bytes(b"installer-owned cleanup\n")
            cleanup_name = ".moveid.cleanup.agent.tmp"
            cleanup_path = destination / cleanup_name
            identity = install.codex_agent_destination_identity(destination)
            agent_dir = install.AnchoredAgentDir.open(destination, identity)
            expected_state = agent_dir.previous_state(target_name)
            assert expected_state is not None
            real_rename = install.codex_agent_native_rename_no_replace
            restored = False

            def mismatch_then_restore_with_source_reappearance(directory_fd: int, source: str, target_name_arg: str) -> None:
                nonlocal restored
                if source == target_name:
                    real_rename(directory_fd, source, target_name_arg)
                    cleanup_path.write_bytes(b"mismatched cleanup bytes\n")
                    return
                if source == cleanup_name and target_name_arg == target_name:
                    real_rename(directory_fd, source, target_name_arg)
                    cleanup_path.write_bytes(b"source reappeared after restore\n")
                    restored = True
                    return
                real_rename(directory_fd, source, target_name_arg)

            try:
                with (
                    patch.object(install.secrets, "token_hex", return_value="moveid"),
                    patch.object(install, "codex_agent_native_rename_no_replace", side_effect=mismatch_then_restore_with_source_reappearance),
                ):
                    result = agent_dir.cleanup_owned_entry(target_name, expected_state)
            finally:
                agent_dir.close()

            self.assertTrue(restored)
            self.assertEqual(target.read_bytes(), b"mismatched cleanup bytes\n")
            self.assertEqual(cleanup_path.read_bytes(), b"source reappeared after restore\n")
            self.assertEqual(result.public_conflicts, [cleanup_path.as_posix(), target.as_posix()])
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": cleanup_path.as_posix(), "error": "cleanup_restore_collision"},
                result.cleanup_errors,
            )
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": target.as_posix(), "error": "cleanup_restore_collision"},
                result.cleanup_errors,
            )

    def test_install_codex_agents_posix_uncertain_entry_takeover_is_not_laundered_as_cleanup(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            uncertain_name = ".agent.toml.tempid.tmp"
            uncertain_path = destination / uncertain_name
            uncertain_path.write_bytes(b"concurrent victim at uncertain name\n")
            identity = install.codex_agent_destination_identity(destination)
            agent_dir = install.AnchoredAgentDir.open(destination, identity)
            try:
                result = agent_dir.preserve_uncertain_entry(uncertain_name, "temp_state_capture_unavailable")
            finally:
                agent_dir.close()

            self.assertEqual(uncertain_path.read_bytes(), b"concurrent victim at uncertain name\n")
            self.assertEqual(result.public_conflicts, [uncertain_path.as_posix()])
            self.assertEqual(result.preserved_private_paths, [])
            self.assertEqual(
                result.cleanup_errors,
                [
                    {
                        "kind": "preserved_concurrent_file",
                        "target": uncertain_path.as_posix(),
                        "error": "temp_state_capture_unavailable",
                    }
                ],
            )
            remediation = install.codex_route_aware_cleanup_manual_remediation(result.cleanup_errors)
            self.assertEqual([action["reason"] for action in remediation], ["concurrent_file_preserved"])
            self.assertEqual(remediation[0]["paths"], [uncertain_path.as_posix()])

    def test_install_codex_agents_posix_uncertain_entry_read_error_is_not_cleanup_incomplete(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            uncertain_name = ".agent.toml.tempid.tmp"
            uncertain_path = destination / uncertain_name
            uncertain_path.write_bytes(b"unreadable uncertain victim\n")
            identity = install.codex_agent_destination_identity(destination)
            agent_dir = install.AnchoredAgentDir.open(destination, identity)
            try:
                with patch.object(agent_dir, "previous_state", side_effect=OSError("injected read error")):
                    result = agent_dir.preserve_uncertain_entry(uncertain_name, "temp_state_capture_unavailable")
            finally:
                agent_dir.close()

            self.assertEqual(uncertain_path.read_bytes(), b"unreadable uncertain victim\n")
            self.assertEqual(result.public_conflicts, [uncertain_path.as_posix()])
            self.assertEqual(
                result.cleanup_errors,
                [
                    {
                        "kind": "preserved_concurrent_file",
                        "target": uncertain_path.as_posix(),
                        "error": "temp_state_capture_unavailable",
                    }
                ],
            )
            remediation = install.codex_route_aware_cleanup_manual_remediation(result.cleanup_errors)
            self.assertEqual([action["reason"] for action in remediation], ["concurrent_file_preserved"])
            self.assertNotIn("cleanup_incomplete", [action["reason"] for action in remediation])

    def test_install_codex_agents_posix_temp_fsync_capture_failure_preserves_name_swap(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "agent.toml"
            identity = install.codex_agent_destination_identity(destination)
            temp_name = ".agent.toml.tempid.tmp"
            temp_path = destination / temp_name
            owner_path = destination / ".owner-temp"
            real_fsync = install.os.fsync
            real_previous_state = install.AnchoredAgentDir.previous_state
            swapped = False

            def fail_fsync_after_temp_name_swap(descriptor: int) -> None:
                nonlocal swapped
                if not swapped and temp_path.exists():
                    swapped = True
                    os.rename(temp_path, owner_path)
                    temp_path.write_bytes(b"concurrent temp-name replacement\n")
                    raise OSError("forced fsync failure after temp-name swap")
                real_fsync(descriptor)

            def fail_temp_capture(agent_dir: object, name: str) -> object:
                if name == temp_name:
                    raise OSError("forced temp identity capture failure")
                return real_previous_state(agent_dir, name)

            with (
                patch.object(install.secrets, "token_hex", return_value="tempid"),
                patch.object(install.os, "fsync", side_effect=fail_fsync_after_temp_name_swap),
                patch.object(install.AnchoredAgentDir, "previous_state", fail_temp_capture),
            ):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.write_codex_agent_atomic(
                        target,
                        b"installer bytes\n",
                        destination,
                        identity,
                        expected_state=None,
                    )

            self.assertTrue(swapped)
            self.assertFalse(target.exists())
            self.assertEqual(temp_path.read_bytes(), b"concurrent temp-name replacement\n")
            self.assertIn(temp_path.as_posix(), raised.exception.preserved_paths)

    def test_install_codex_agents_posix_publish_consumes_temp_with_move_not_hardlink(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "agent.toml"
            identity = install.codex_agent_destination_identity(destination)

            with patch.object(
                install.AnchoredAgentDir,
                "link_no_replace",
                side_effect=AssertionError("installer temp publication must not hardlink"),
            ):
                state = install.write_codex_agent_atomic(
                    target,
                    b"installer bytes\n",
                    destination,
                    identity,
                    expected_state=None,
                )

            self.assertEqual(state.content, b"installer bytes\n")
            self.assertEqual(target.read_bytes(), b"installer bytes\n")
            self.assertEqual(list(destination.glob(".*.tmp")), [])

    def test_install_codex_agents_cleanup_public_conflict_not_classified_by_path_substring(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "outer.cleanup-dir" / "agents"
            destination.mkdir(parents=True)
            target = destination / "agent.toml"
            target.write_bytes(b"captured prior\n")
            expected = install.codex_agent_previous_state(target)
            identity = install.codex_agent_destination_identity(destination)
            real_cleanup = install.AnchoredAgentDir.cleanup_owned_entry

            def public_conflict_for_backup(
                agent_dir: object,
                name: str,
                expected_state: object,
                cleanup_errors: object = None,
            ) -> object:
                del cleanup_errors
                if name.endswith(".bak"):
                    path = agent_dir.evidence_path(target.name)
                    result_class = getattr(install, "CodexAgentCleanupResult", None)
                    if result_class is not None:
                        return result_class(public_conflicts=[path])
                    return [path]
                return real_cleanup(agent_dir, name, expected_state)

            with patch.object(install.AnchoredAgentDir, "cleanup_owned_entry", public_conflict_for_backup):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.write_codex_agent_atomic(
                        target,
                        b"installer bytes\n",
                        destination,
                        identity,
                        expected_state=expected,
                    )

            self.assertIn(target.as_posix(), raised.exception.preserved_paths)

    def test_install_codex_agents_wrapped_no_clobber_preserves_cleanup_errors(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "agent.toml"
            identity = install.codex_agent_destination_identity(destination)
            cleanup_error = {
                "kind": "close_handle",
                "target": (destination / ".agent.toml.cleanup").as_posix(),
                "error": "OSError",
            }
            real_publish = install.AnchoredAgentDir.rename_no_replace

            def fail_publish_with_cleanup_evidence(self: object, source_name: str, target_name: str) -> None:
                if target_name == target.name:
                    raise install.CodexAgentNoClobberConflict("injected no-clobber", ["preserved-path"], [cleanup_error])
                return real_publish(self, source_name, target_name)

            with patch.object(install.AnchoredAgentDir, "rename_no_replace", fail_publish_with_cleanup_evidence):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.write_codex_agent_atomic(
                        target,
                        b"installer bytes\n",
                        destination,
                        identity,
                        expected_state=None,
                    )

            self.assertIn(cleanup_error, raised.exception.cleanup_errors)
            self.assertTrue(any(error["kind"] == "preserved_cleanup_entry" for error in raised.exception.cleanup_errors))
            self.assertIn("preserved-path", raised.exception.preserved_paths)

    def test_install_codex_agents_temp_cleanup_stays_anchored_after_directory_swap(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            destination = root / "agents"
            destination.mkdir()
            target = destination / "analyze-executor.toml"
            identity = install.codex_agent_destination_identity(destination)
            moved = root / "moved-agents"
            replacement_temp: Path | None = None
            real_identity = install.codex_agent_destination_identity
            injected = False

            def swap_after_temp_exists(path: Path) -> tuple[int, int]:
                nonlocal injected, replacement_temp
                if path == destination and not injected:
                    temps = list(destination.glob(".*.tmp"))
                    if temps:
                        injected = True
                        temp_name = temps[0].name
                        destination.rename(moved)
                        destination.mkdir()
                        replacement_temp = destination / temp_name
                        replacement_temp.write_bytes(b"replacement temp must survive\n")
                return real_identity(path)

            with patch.object(install, "codex_agent_destination_identity", side_effect=swap_after_temp_exists):
                with self.assertRaisesRegex(OSError, "destination .*during|destination .*after|destination .*before"):
                    install.write_codex_agent_atomic(
                        target,
                        b"installer bytes\n",
                        destination,
                        identity,
                        expected_state=None,
                    )

            assert replacement_temp is not None
            self.assertEqual(replacement_temp.read_bytes(), b"replacement temp must survive\n")
            self.assertEqual(list(moved.glob(".*.tmp")), [])
            self.assertFalse(target.exists())

    def test_install_codex_agents_backup_move_close_error_does_not_hide_moved_backup(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target = destination / "agent.toml"
            target.write_bytes(b"original target bytes\n")
            real_close = install.os.close
            close_calls = 0

            def close_then_report(descriptor: int) -> None:
                nonlocal close_calls
                close_calls += 1
                real_close(descriptor)
                raise OSError("injected anchored directory close failure")

            with patch.object(install.os, "close", side_effect=close_then_report):
                backup = install.codex_agent_move_target_to_backup(target, destination)

            self.assertEqual(close_calls, 1)
            self.assertFalse(target.exists())
            self.assertEqual(backup.read_bytes(), b"original target bytes\n")

    def test_install_codex_agents_anchored_read_close_error_does_not_mask_state(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target = destination / "agent.toml"
            target.write_bytes(b"readable state\n")
            directory_fd = install.codex_agent_open_anchored_directory(
                destination,
                install.codex_agent_destination_identity(destination),
            )
            real_close = install.os.close
            try:
                with patch.object(install.os, "close", side_effect=lambda descriptor: (_ for _ in ()).throw(OSError("injected read close failure"))):
                    state = install.codex_agent_previous_state_at(directory_fd, target.name)
            finally:
                real_close(directory_fd)

            self.assertIsNotNone(state)
            assert state is not None
            self.assertEqual(state.content, b"readable state\n")

    def test_install_codex_agents_restore_close_error_does_not_mask_restored_state(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            backup = destination / ".agent.toml.initial.bak"
            target = destination / "agent.toml"
            backup.write_bytes(b"captured rollback state\n")
            real_close = install.os.close

            def close_then_report(descriptor: int) -> None:
                real_close(descriptor)
                raise OSError("injected restore close failure")

            with patch.object(install.os, "close", side_effect=close_then_report):
                install.codex_agent_restore_backup_no_clobber(backup, target)

            self.assertEqual(target.read_bytes(), b"captured rollback state\n")
            self.assertFalse(backup.exists())

    def test_install_codex_agents_recovery_copy_evidence_is_anchor_relative_after_directory_move(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            destination = root / "agents"
            destination.mkdir()
            source = destination / "source.toml"
            source.write_bytes(b"original bytes\n")
            state = install.codex_agent_previous_state(source)
            assert state is not None
            identity = install.codex_agent_destination_identity(destination)
            moved = root / "moved-agents"
            real_open = install.os.open
            injected = False

            def move_after_copy_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
                nonlocal injected
                descriptor = real_open(path, flags, *args, **kwargs)
                if kwargs.get("dir_fd") is not None and flags & os.O_CREAT and not injected:
                    injected = True
                    destination.rename(moved)
                    destination.mkdir()
                return descriptor

            with patch.object(install.os, "open", side_effect=move_after_copy_open):
                with self.assertRaises(install.CodexAgentRecoveryCopyFailure) as raised:
                    install.codex_agent_preserve_state_as_backup(
                        state,
                        destination / "agent.toml",
                        destination,
                        identity,
                    )

            self.assertEqual(len(raised.exception.failed_paths), 1)
            self.assertTrue(raised.exception.failed_paths[0].startswith("anchored-agent-dir:"))
            self.assertNotEqual(raised.exception.failed_paths[0], (destination / "agent.toml").as_posix())
            backups = list(moved.glob(".*.bak"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), state.content)
            self.assertEqual(list(destination.iterdir()), [])

    def test_install_codex_agents_anchored_backend_fails_closed_when_dir_fd_is_unavailable(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            identity = install.codex_agent_destination_identity(destination)

            with patch.object(install, "CODEX_AGENT_OPEN_SUPPORTS_DIR_FD", False):
                with self.assertRaisesRegex(OSError, "descriptor-relative anchored directory"):
                    install.AnchoredAgentDir.open(destination, identity)

    def test_install_codex_agents_windows_backend_opens_directory_without_share_delete(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                directory_handle = agent_dir.directory_fd
                agent_dir.close()

            self.assertEqual(fake.createfile_calls[0]["path"], destination)
            self.assertEqual(int(fake.createfile_calls[0]["share_mode"]) & 0x00000004, 0)
            self.assertNotEqual(int(fake.createfile_calls[0]["share_mode"]) & 0x00000001, 0)
            self.assertNotEqual(int(fake.createfile_calls[0]["share_mode"]) & 0x00000002, 0)
            self.assertNotEqual(int(fake.createfile_calls[0]["flags_and_attributes"]) & 0x02000000, 0)
            self.assertIn(directory_handle, fake.close_handles)

    def test_install_codex_agents_windows_rename_info_uses_native_filename_offset(self) -> None:
        from speckit_pro_runner.helpers import install

        rename_info, _size = install.codex_agent_windows_file_rename_info("backup.toml", 1234)
        encoded = "backup.toml".encode("utf-16le")
        native_offset = windows_file_rename_info_filename_offset()

        self.assertEqual(native_offset, 20)
        self.assertEqual(ctypes.sizeof(FakeWindowsFileRenameInfoHeader), 24)
        self.assertEqual(
            ctypes.string_at(ctypes.addressof(rename_info) + native_offset, len(encoded)),
            encoded,
        )

    def test_install_codex_agents_windows_open_canonicalizes_identity_from_directory_handle(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            metadata = destination.lstat()
            expected_identity = (metadata.st_dev & 0xFFFFFFFF, metadata.st_ino)
            fake = FakeWindowsKernel32()

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install, "codex_agent_destination_identity", return_value=(1, 2)),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, None)
                try:
                    self.assertEqual(agent_dir.identity, expected_identity)
                finally:
                    agent_dir.close()

    def test_install_codex_agents_windows_open_rejects_expected_identity_mismatch(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            fake = FakeWindowsKernel32()

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
            ):
                with self.assertRaisesRegex(OSError, "destination changed before anchored operation"):
                    install.AnchoredAgentDir.open(destination, (123, 456))

            self.assertEqual(len(fake.close_handles), 1)

    def test_install_codex_agents_windows_no_replace_rename_uses_root_handle_and_replace_false(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            source = destination / "agent.toml"
            source.write_bytes(b"windows source\n")
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install.secrets, "token_hex", return_value="abcdef"),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                directory_handle = agent_dir.directory_fd
                backup_name = agent_dir.move_target_to_backup(source.name)
                agent_dir.close()

            self.assertEqual(backup_name, ".agent.toml.abcdef.bak")
            self.assertFalse(source.exists())
            self.assertEqual((destination / backup_name).read_bytes(), b"windows source\n")
            self.assertEqual(fake.rename_calls[0]["info_class"], 3)
            self.assertFalse(fake.rename_calls[0]["replace"])
            self.assertEqual(fake.rename_calls[0]["root"], directory_handle)

    def test_install_codex_agents_windows_no_replace_rename_maps_existing_target(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            source = destination / "agent.toml"
            source.write_bytes(b"windows source\n")
            target = destination / "existing.toml"
            target.write_bytes(b"already here\n")
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                with self.assertRaises(FileExistsError):
                    install.codex_agent_windows_rename_no_replace(agent_dir, source.name, target.name)
                agent_dir.close()

            self.assertEqual(source.read_bytes(), b"windows source\n")
            self.assertEqual(target.read_bytes(), b"already here\n")
            self.assertFalse(fake.rename_calls[0]["replace"])

    def test_install_codex_agents_windows_rename_close_error_is_non_masking(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            source = destination / "agent.toml"
            source.write_bytes(b"windows source\n")
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                fake.fail_close = True
                with self.assertRaises(OSError):
                    install.codex_agent_windows_rename_no_replace(agent_dir, source.name, "backup.toml")
                fake.fail_close = False
                agent_dir.close()

            self.assertFalse(source.exists())
            self.assertEqual((destination / "backup.toml").read_bytes(), b"windows source\n")

    def test_install_codex_agents_windows_publish_rename_close_failure_preserves_committed_target(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target = destination / "agent.toml"
            temp_path = destination / ".agent.toml.tokenid.tmp"
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()
            fake.fail_close_paths.add(target)

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install.secrets, "token_hex", return_value="tokenid"),
            ):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.write_codex_agent_atomic(
                        target,
                        b"windows publish bytes\n",
                        destination,
                        identity,
                        expected_state=None,
                    )

            self.assertFalse(temp_path.exists())
            self.assertEqual(target.read_bytes(), b"windows publish bytes\n")
            self.assertNotIn("target changed", str(raised.exception))
            self.assertEqual(raised.exception.preserved_paths, [target.as_posix()])
            self.assertIn(
                {"kind": "close_handle", "target": target.as_posix(), "error": "OSError"},
                raised.exception.cleanup_errors,
            )
            self.assertTrue(any(record["path"] == target for record in fake.handles.values()))

    def test_install_codex_agents_windows_write_backup_rename_close_failure_preserves_attempted_destination(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target = destination / "agent.toml"
            target.write_bytes(b"windows original\n")
            expected = install.codex_agent_previous_state(target)
            assert expected is not None
            identity = install.codex_agent_destination_identity(destination)
            backup_path = destination / ".agent.toml.tokenid.bak"
            fake = FakeWindowsKernel32()
            fake.fail_close_paths.add(backup_path)

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install.secrets, "token_hex", return_value="tokenid"),
            ):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.write_codex_agent_atomic(
                        target,
                        b"windows replacement\n",
                        destination,
                        identity,
                        expected_state=expected,
                    )

            self.assertFalse(target.exists())
            self.assertEqual(backup_path.read_bytes(), b"windows original\n")
            self.assertIn(backup_path.as_posix(), raised.exception.preserved_paths)
            self.assertIn(
                {"kind": "close_handle", "target": backup_path.as_posix(), "error": "OSError"},
                raised.exception.cleanup_errors,
            )
            self.assertTrue(any(record["path"] == backup_path for record in fake.handles.values()))

    def test_install_codex_agents_windows_removal_backup_rename_close_failure_preserves_attempted_destination(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target = destination / "agent.toml"
            target.write_bytes(b"windows original removal\n")
            expected = install.codex_agent_previous_state(target)
            assert expected is not None
            identity = install.codex_agent_destination_identity(destination)
            backup_path = destination / ".agent.toml.tokenid.bak"
            fake = FakeWindowsKernel32()
            fake.fail_close_paths.add(backup_path)

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install.secrets, "token_hex", return_value="tokenid"),
            ):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.remove_codex_agent_if_unchanged(target, expected, destination, identity)

            self.assertFalse(target.exists())
            self.assertEqual(backup_path.read_bytes(), b"windows original removal\n")
            self.assertIn(backup_path.as_posix(), raised.exception.preserved_paths)
            self.assertIn(
                {"kind": "close_handle", "target": backup_path.as_posix(), "error": "OSError"},
                raised.exception.cleanup_errors,
            )
            self.assertTrue(any(record["path"] == backup_path for record in fake.handles.values()))

    def test_install_codex_agents_windows_restore_rename_close_failure_omits_absent_backup(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            backup = destination / ".agent.toml.tokenid.bak"
            backup.write_bytes(b"windows backup bytes\n")
            target = destination / "agent.toml"
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()
            fake.fail_close_paths.add(target)

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                try:
                    with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                        agent_dir.restore_backup_no_clobber(backup.name, target.name)
                finally:
                    agent_dir.close()

            self.assertFalse(backup.exists())
            self.assertEqual(target.read_bytes(), b"windows backup bytes\n")
            self.assertEqual(raised.exception.preserved_paths, [target.as_posix()])
            self.assertNotIn(backup.as_posix(), raised.exception.preserved_paths)
            self.assertIn(
                {"kind": "close_handle", "target": target.as_posix(), "error": "OSError"},
                raised.exception.cleanup_errors,
            )

    def test_install_codex_agents_windows_rename_primary_and_close_failure_is_structured(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            source = destination / "agent.toml"
            source.write_bytes(b"windows source\n")
            target = destination / "backup.toml"
            target.write_bytes(b"already here\n")
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()
            fake.fail_close_once_paths.add(source)

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                try:
                    with self.assertRaises(OSError) as raised:
                        install.codex_agent_windows_rename_no_replace(agent_dir, source.name, target.name)
                finally:
                    agent_dir.close()

            exc = raised.exception
            self.assertTrue(hasattr(exc, "primary_error"))
            self.assertIsInstance(exc.primary_error, FileExistsError)
            self.assertIsInstance(exc.close_error, OSError)
            self.assertEqual(exc.source_name, source.name)
            self.assertEqual(exc.target_name, target.name)
            self.assertEqual(exc.outcome, "not_committed")
            self.assertEqual(getattr(exc, "__notes__", []), [])
            self.assertEqual(source.read_bytes(), b"windows source\n")
            self.assertEqual(target.read_bytes(), b"already here\n")

    def test_install_codex_agents_windows_rename_close_evidence_targets_by_outcome_and_serializes_manual(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                try:
                    committed = install.CodexAgentWindowsRenameCommittedCloseFailure("source.tmp", "target.toml", OSError())
                    not_committed = install.CodexAgentWindowsRenameFailure(
                        "source.tmp",
                        "target.toml",
                        OSError("primary"),
                        OSError("close"),
                        "not_committed",
                    )
                    unknown = install.CodexAgentWindowsRenameFailure(
                        "source.tmp",
                        "target.toml",
                        OSError("primary"),
                        OSError("close"),
                        "unknown",
                    )

                    self.assertEqual(
                        agent_dir.close_handle_cleanup_errors_for_rename(committed),
                        [{"kind": "close_handle", "target": (destination / "target.toml").as_posix(), "error": "OSError"}],
                    )
                    self.assertEqual(
                        agent_dir.close_handle_cleanup_errors_for_rename(not_committed),
                        [{"kind": "close_handle", "target": (destination / "source.tmp").as_posix(), "error": "OSError"}],
                    )
                    self.assertEqual(
                        agent_dir.close_handle_cleanup_errors_for_rename(unknown),
                        [
                            {"kind": "close_handle", "target": (destination / "source.tmp").as_posix(), "error": "OSError"},
                            {"kind": "close_handle", "target": (destination / "target.toml").as_posix(), "error": "OSError"},
                        ],
                    )
                    self.assertEqual(
                        install.codex_route_aware_cleanup_manual_remediation(
                            [
                                *agent_dir.close_handle_cleanup_errors_for_rename(committed),
                                *agent_dir.close_handle_cleanup_errors_for_rename(not_committed),
                                *agent_dir.close_handle_cleanup_errors_for_rename(unknown),
                            ]
                        ),
                        [],
                    )
                finally:
                    agent_dir.close()

    def test_install_codex_agents_windows_restore_rename_failure_does_not_preserve_absent_entries(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            backup = destination / ".agent.toml.tokenid.bak"
            backup.write_bytes(b"windows backup bytes\n")
            target = destination / "agent.toml"
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()

            def disappear_then_fail(source_name: str, target_name: str) -> None:
                self.assertEqual(source_name, backup.name)
                self.assertEqual(target_name, target.name)
                backup.unlink()
                raise OSError("restore rename failed after both entries disappeared")

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                try:
                    with patch.object(agent_dir, "rename_no_replace", side_effect=disappear_then_fail):
                        with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                            agent_dir.restore_backup_no_clobber(backup.name, target.name)
                finally:
                    agent_dir.close()

            self.assertFalse(backup.exists())
            self.assertFalse(target.exists())
            self.assertEqual(raised.exception.preserved_paths, [])
            self.assertEqual(raised.exception.cleanup_errors, [])

    def test_install_codex_agents_windows_publish_primary_and_close_failure_does_not_preserve_absent_target(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target = destination / "agent.toml"
            temp_path = destination / ".agent.toml.tokenid.tmp"
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()
            real_set_file_information = fake.SetFileInformationByHandle
            failed_publish = False

            def fail_publish_rename(handle: int, info_class: int, rename_info_buffer: object, buffer_size: int) -> int:
                nonlocal failed_publish
                if (
                    info_class == install.WINDOWS_FILE_RENAME_INFO_CLASS
                    and PosixPath(fake.handles[handle]["path"]) == temp_path
                    and not failed_publish
                ):
                    failed_publish = True
                    fake.fail_close_once_paths.add(temp_path)
                    fake.set_last_error(fake.ERROR_ACCESS_DENIED)
                    return 0
                return real_set_file_information(handle, info_class, rename_info_buffer, buffer_size)

            fake.SetFileInformationByHandle = fail_publish_rename  # type: ignore[method-assign]

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install.secrets, "token_hex", return_value="tokenid"),
            ):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.write_codex_agent_atomic(
                        target,
                        b"windows publish bytes\n",
                        destination,
                        identity,
                        expected_state=None,
                    )

            self.assertFalse(temp_path.exists())
            self.assertFalse(target.exists())
            self.assertEqual(raised.exception.preserved_paths, [])
            self.assertIn(
                {"kind": "close_handle", "target": temp_path.as_posix(), "error": "OSError"},
                raised.exception.cleanup_errors,
            )
            self.assertFalse(
                any(error["kind"] == "preserved_cleanup_entry" for error in raised.exception.cleanup_errors)
            )

    def test_install_codex_agents_windows_backup_primary_and_close_failure_keeps_primary_classification(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target = destination / "agent.toml"
            target.write_bytes(b"windows original\n")
            expected = install.codex_agent_previous_state(target)
            assert expected is not None
            backup_path = destination / ".agent.toml.tokenid.bak"
            backup_path.write_bytes(b"concurrent backup occupant\n")
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()
            real_set_file_information = fake.SetFileInformationByHandle

            def fail_backup_close_after_rename_attempt(
                handle: int,
                info_class: int,
                rename_info_buffer: object,
                buffer_size: int,
            ) -> int:
                result = real_set_file_information(handle, info_class, rename_info_buffer, buffer_size)
                if info_class == install.WINDOWS_FILE_RENAME_INFO_CLASS:
                    fake.fail_close_once_paths.add(target)
                return result

            fake.SetFileInformationByHandle = fail_backup_close_after_rename_attempt  # type: ignore[method-assign]

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install.secrets, "token_hex", return_value="tokenid"),
            ):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.write_codex_agent_atomic(
                        target,
                        b"windows replacement\n",
                        destination,
                        identity,
                        expected_state=expected,
                    )

            self.assertEqual(target.read_bytes(), b"windows original\n")
            self.assertEqual(backup_path.read_bytes(), b"concurrent backup occupant\n")
            self.assertEqual(raised.exception.preserved_paths, [backup_path.as_posix(), target.as_posix()])
            self.assertIn(
                {"kind": "close_handle", "target": target.as_posix(), "error": "OSError"},
                raised.exception.cleanup_errors,
            )
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": backup_path.as_posix(), "error": "backup_rename_failed"},
                raised.exception.cleanup_errors,
            )

    def test_install_codex_agents_windows_restore_primary_and_close_failure_reports_close_and_final_state(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            backup = destination / ".agent.toml.tokenid.bak"
            backup.write_bytes(b"windows backup bytes\n")
            target = destination / "agent.toml"
            target.write_bytes(b"concurrent target bytes\n")
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()
            real_set_file_information = fake.SetFileInformationByHandle

            def fail_restore_close_after_rename_attempt(
                handle: int,
                info_class: int,
                rename_info_buffer: object,
                buffer_size: int,
            ) -> int:
                result = real_set_file_information(handle, info_class, rename_info_buffer, buffer_size)
                if info_class == install.WINDOWS_FILE_RENAME_INFO_CLASS:
                    fake.fail_close_once_paths.add(backup)
                return result

            fake.SetFileInformationByHandle = fail_restore_close_after_rename_attempt  # type: ignore[method-assign]

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                try:
                    with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                        agent_dir.restore_backup_no_clobber(backup.name, target.name)
                finally:
                    agent_dir.close()

            self.assertEqual(backup.read_bytes(), b"windows backup bytes\n")
            self.assertEqual(target.read_bytes(), b"concurrent target bytes\n")
            self.assertEqual(raised.exception.preserved_paths, [backup.as_posix(), target.as_posix()])
            self.assertIn(
                {"kind": "close_handle", "target": backup.as_posix(), "error": "OSError"},
                raised.exception.cleanup_errors,
            )
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": target.as_posix(), "error": "backup_restore_rename_failed"},
                raised.exception.cleanup_errors,
            )

    def test_install_codex_agents_windows_cleanup_primary_and_close_failure_reports_close_without_relabeling(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target_name = "agent.tmp"
            target = destination / target_name
            target.write_bytes(b"windows installer-owned cleanup\n")
            cleanup_name = ".cleanupid.cleanup.agent.tmp"
            cleanup_path = destination / cleanup_name
            cleanup_path.write_bytes(b"concurrent cleanup occupant\n")
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()
            real_set_file_information = fake.SetFileInformationByHandle

            def fail_cleanup_close_after_rename_attempt(
                handle: int,
                info_class: int,
                rename_info_buffer: object,
                buffer_size: int,
            ) -> int:
                result = real_set_file_information(handle, info_class, rename_info_buffer, buffer_size)
                if info_class == install.WINDOWS_FILE_RENAME_INFO_CLASS:
                    fake.fail_close_once_paths.add(target)
                return result

            fake.SetFileInformationByHandle = fail_cleanup_close_after_rename_attempt  # type: ignore[method-assign]

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install.secrets, "token_hex", return_value="cleanupid"),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                try:
                    state = agent_dir.previous_state(target_name)
                    assert state is not None
                    result = agent_dir.cleanup_owned_entry(target_name, state)
                finally:
                    agent_dir.close()

            self.assertEqual(cleanup_path.read_bytes(), b"concurrent cleanup occupant\n")
            self.assertEqual(target.read_bytes(), b"windows installer-owned cleanup\n")
            self.assertEqual(result.public_conflicts, [cleanup_path.as_posix(), target.as_posix()])
            self.assertIn(
                {"kind": "close_handle", "target": target.as_posix(), "error": "OSError"},
                result.cleanup_errors,
            )
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": cleanup_path.as_posix(), "error": "cleanup_rename_failed"},
                result.cleanup_errors,
            )

    def test_install_codex_agents_windows_cleanup_close_rename_mismatch_returns_candidate_and_source(self) -> None:
        from speckit_pro_runner.helpers import install

        mismatch_cases = ["content", "reparse", "directory", "device", "inode"]
        for mismatch in mismatch_cases:
            with self.subTest(mismatch=mismatch), tempfile.TemporaryDirectory() as tmp:
                destination = Path(tmp).resolve()
                target_name = "agent.tmp"
                target = destination / target_name
                target.write_bytes(b"windows installer-owned cleanup\n")
                identity = install.codex_agent_destination_identity(destination)
                fake = FakeWindowsKernel32()
                cleanup_name = ".cleanupid.cleanup.agent.tmp"
                cleanup_path = destination / cleanup_name
                real_set_file_information = fake.SetFileInformationByHandle
                real_windows_file_info = install.codex_agent_windows_file_info
                real_windows_read_all = install.codex_agent_windows_read_all
                rename_finished = False

                def close_fail_recreate_and_mutate_candidate(
                    handle: int,
                    info_class: int,
                    rename_info_buffer: object,
                    buffer_size: int,
                ) -> int:
                    nonlocal rename_finished
                    result = real_set_file_information(handle, info_class, rename_info_buffer, buffer_size)
                    if (
                        result
                        and info_class == install.WINDOWS_FILE_RENAME_INFO_CLASS
                        and PosixPath(fake.handles[handle]["path"]) == cleanup_path
                        and not rename_finished
                    ):
                        rename_finished = True
                        fake.fail_close_once_paths.add(cleanup_path)
                        target.write_bytes(b"windows recreated source during cleanup verify\n")
                        if mismatch == "content":
                            cleanup_path.write_bytes(b"windows mismatched cleanup content\n")
                    return result

                def mutated_file_info(handle: int) -> object:
                    info = real_windows_file_info(handle)
                    record = fake.handles.get(handle)
                    if record is not None and PosixPath(record["path"]) == cleanup_path and rename_finished:
                        if mismatch == "reparse":
                            info.dwFileAttributes |= install.WINDOWS_FILE_ATTRIBUTE_REPARSE_POINT
                        elif mismatch == "directory":
                            info.dwFileAttributes |= fake.FILE_ATTRIBUTE_DIRECTORY
                        elif mismatch == "device":
                            info.dwVolumeSerialNumber = int(info.dwVolumeSerialNumber) ^ 1
                        elif mismatch == "inode":
                            info.nFileIndexLow = int(info.nFileIndexLow) ^ 1
                    return info

                def mutated_read_all(handle: int) -> bytes:
                    record = fake.handles.get(handle)
                    if (
                        mismatch == "content"
                        and record is not None
                        and PosixPath(record["path"]) == cleanup_path
                        and rename_finished
                    ):
                        return b"windows mismatched cleanup content\n"
                    return real_windows_read_all(handle)

                fake.SetFileInformationByHandle = close_fail_recreate_and_mutate_candidate  # type: ignore[method-assign]

                with (
                    patch.object(install.os, "name", "nt"),
                    patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                    patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                    patch.object(install.secrets, "token_hex", return_value="cleanupid"),
                    patch.object(install, "codex_agent_windows_file_info", side_effect=mutated_file_info),
                    patch.object(install, "codex_agent_windows_read_all", side_effect=mutated_read_all),
                ):
                    agent_dir = install.AnchoredAgentDir.open(destination, identity)
                    try:
                        state = agent_dir.previous_state(target_name)
                        assert state is not None
                        result = agent_dir.cleanup_owned_entry(target_name, state)
                    finally:
                        agent_dir.close()

                self.assertEqual(target.read_bytes(), b"windows recreated source during cleanup verify\n")
                self.assertTrue(cleanup_path.exists())
                self.assertEqual(result.public_conflicts, [cleanup_path.as_posix(), target.as_posix()])
                self.assertIn(
                    {
                        "kind": "preserved_concurrent_file",
                        "target": cleanup_path.as_posix(),
                        "error": "cleanup_rename_close_failure",
                    },
                    result.cleanup_errors,
                )
                self.assertIn(
                    {
                        "kind": "preserved_concurrent_file",
                        "target": target.as_posix(),
                        "error": "cleanup_rename_close_failure",
                    },
                    result.cleanup_errors,
                )

    def test_install_codex_agents_windows_recovery_copy_verifies_exclusive_handle_without_path_reopen(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            identity = install.codex_agent_destination_identity(destination)
            state = install.CodexAgentFileState(
                content=b"windows recovery bytes\n",
                mode=stat.S_IFREG | 0o751,
                device=11,
                inode=22,
            )
            fake = FakeWindowsKernel32()

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install.os, "chmod", side_effect=AssertionError("path chmod is forbidden under exclusive handle")),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                try:
                    preserved = agent_dir.preserve_state_as_backup(state, "agent.toml")
                finally:
                    agent_dir.close()

            preserved_path = destination / Path(preserved).name
            self.assertEqual(preserved_path.read_bytes(), state.content)
            self.assertFalse(
                any(
                    call["path"] == preserved_path and call["creation_disposition"] == FakeWindowsKernel32.OPEN_EXISTING
                    for call in fake.createfile_calls
                )
            )

    def test_install_codex_agents_windows_recovery_copy_applies_readonly_mode_via_exclusive_handle(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            identity = install.codex_agent_destination_identity(destination)
            state = install.CodexAgentFileState(
                content=b"readonly recovery bytes\n",
                mode=stat.S_IFREG | 0o444,
                device=11,
                inode=22,
            )
            fake = FakeWindowsKernel32()

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install.os, "chmod", side_effect=AssertionError("path chmod is forbidden under exclusive handle")),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                try:
                    preserved = agent_dir.preserve_state_as_backup(state, "agent.toml")
                finally:
                    agent_dir.close()

            preserved_path = destination / Path(preserved).name
            self.assertEqual(preserved_path.read_bytes(), state.content)
            self.assertEqual(stat.S_IMODE(preserved_path.stat().st_mode), 0o400)
            self.assertTrue(
                any(
                    call["path"] == preserved_path
                    and int(call["attributes"]) & FakeWindowsKernel32.FILE_ATTRIBUTE_READONLY
                    for call in fake.file_basic_info_calls
                )
            )
            self.assertFalse(
                any(
                    call["path"] == preserved_path and call["creation_disposition"] == FakeWindowsKernel32.OPEN_EXISTING
                    for call in fake.createfile_calls
                )
            )

    def test_install_codex_agents_windows_recovery_copy_failure_preserves_unreadable_target_unknown(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target = destination / "agent.toml"
            target.write_bytes(b"windows unreadable target\n")
            identity = install.codex_agent_destination_identity(destination)
            state = install.CodexAgentFileState(
                content=b"windows recovery bytes\n",
                mode=stat.S_IFREG | 0o600,
                device=11,
                inode=22,
            )
            fake = FakeWindowsKernel32()
            fake.fail_write = True

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install.secrets, "token_hex", return_value="copyid"),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                try:
                    with patch.object(agent_dir, "previous_state", side_effect=OSError("injected target read error")):
                        with self.assertRaises(install.CodexAgentRecoveryCopyFailure) as raised:
                            agent_dir.preserve_state_as_backup(state, target.name)
                finally:
                    agent_dir.close()

            copy_path = destination / ".agent.toml.copyid.bak"
            self.assertEqual(raised.exception.failed_paths, [copy_path.as_posix()])
            self.assertEqual(raised.exception.preserved_paths, [target.as_posix()])
            cleanup_errors = [
                {"kind": "recovery_copy_failed", "target": path, "error": "recovery_copy_incomplete"}
                for path in raised.exception.failed_paths
            ]
            cleanup_errors.extend(
                install.codex_agent_unproven_preserved_path_records(
                    raised.exception.preserved_paths,
                    cleanup_errors,
                    "no_clobber_conflict",
                )
            )
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": target.as_posix(), "error": "no_clobber_conflict"},
                cleanup_errors,
            )

    def test_install_codex_agents_windows_file_disposition_info_is_one_byte_boolean(self) -> None:
        from speckit_pro_runner.helpers import install

        self.assertEqual(install._WindowsFileDispositionInfo._fields_, [("DeleteFile", ctypes.c_ubyte)])
        self.assertEqual(ctypes.sizeof(install._WindowsFileDispositionInfo), 1)

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target = destination / "agent.tmp"
            target.write_bytes(b"delete through handle\n")
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                try:
                    handle = agent_dir.open_child_handle(
                        target.name,
                        install.WINDOWS_GENERIC_READ
                        | install.WINDOWS_FILE_WRITE_ATTRIBUTES
                        | install.WINDOWS_DELETE,
                        0,
                        install.WINDOWS_OPEN_EXISTING,
                    )
                    try:
                        install.codex_agent_windows_delete_by_handle(handle)
                    finally:
                        install.codex_agent_windows_close_handle(handle)
                finally:
                    agent_dir.close()

            self.assertEqual(fake.file_disposition_calls[0]["buffer_size"], 1)
            self.assertEqual(fake.file_disposition_calls[0]["delete_file"], 1)

    def test_install_codex_agents_windows_target_is_safe_close_failure_raises_close_handle(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target = destination / "agent.toml"
            target.write_bytes(b"safe target whose handle close fails\n")
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()
            fake.fail_close_paths.add(target)

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                try:
                    with self.assertRaisesRegex(OSError, "CloseHandle"):
                        agent_dir.target_is_safe(target.name)
                finally:
                    agent_dir.close()

    def test_install_codex_agents_windows_temp_write_capture_failure_preserves_name_swap_without_deletefile(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target = destination / "agent.toml"
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()
            temp_name = ".agent.toml.tempid.tmp"
            temp_path = destination / temp_name
            owner_path = destination / ".owner-temp"
            real_write_file = fake.WriteFile
            swapped = False

            def fail_write_after_temp_name_swap(
                handle: int,
                buffer: object,
                bytes_to_write: int,
                bytes_written_pointer: object,
                overlapped: object,
            ) -> int:
                nonlocal swapped
                result = real_write_file(handle, buffer, bytes_to_write, bytes_written_pointer, overlapped)
                if not swapped:
                    swapped = True
                    os.rename(temp_path, owner_path)
                    temp_path.write_bytes(b"concurrent windows temp-name replacement\n")
                    fake.fail_file_info = True
                fake.set_last_error(fake.ERROR_ACCESS_DENIED)
                return 0 if result else result

            fake.WriteFile = fail_write_after_temp_name_swap  # type: ignore[method-assign]

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install.secrets, "token_hex", return_value="tempid"),
            ):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.write_codex_agent_atomic(
                        target,
                        b"installer bytes\n",
                        destination,
                        identity,
                        expected_state=None,
                    )

            self.assertTrue(swapped)
            self.assertEqual(fake.deletefile_calls, [])
            self.assertFalse(target.exists())
            self.assertEqual(temp_path.read_bytes(), b"concurrent windows temp-name replacement\n")
            self.assertIn(temp_path.as_posix(), raised.exception.preserved_paths)

    def test_install_codex_agents_windows_successful_temp_close_failure_returns_cleanup_evidence(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()
            temp_name = ".agent.toml.tempid.tmp"
            temp_path = destination / temp_name
            fake.fail_close_paths.add(temp_path)

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install.secrets, "token_hex", return_value="tempid"),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                try:
                    with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                        agent_dir.create_temp_file("agent.toml", b"installer bytes\n", None)
                finally:
                    agent_dir.close()

            self.assertEqual(temp_path.read_bytes(), b"installer bytes\n")
            self.assertIn(temp_path.as_posix(), raised.exception.preserved_paths)
            self.assertIn(
                {"kind": "close_handle", "target": temp_path.as_posix(), "error": "OSError"},
                raised.exception.cleanup_errors,
            )
            self.assertTrue(any(record["path"] == temp_path for record in fake.handles.values()))

    def test_install_codex_agents_windows_temp_cleanup_preserves_takeover_entry(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target = destination / "agent.toml"
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()
            concurrent = b"windows concurrent temp takeover\n"

            def takeover_temp_before_failed_publish(agent_dir: object, source_name: str, target_name: str) -> None:
                del agent_dir, target_name
                temp_path = destination / source_name
                temp_path.unlink()
                temp_path.write_bytes(concurrent)
                raise OSError("injected Windows publish failure after temp takeover")

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install, "codex_agent_windows_rename_no_replace", side_effect=takeover_temp_before_failed_publish),
            ):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.write_codex_agent_atomic(
                        target,
                        b"windows installer bytes\n",
                        destination,
                        identity,
                        expected_state=None,
                    )

            temps = list(destination.glob(".*.tmp"))
            self.assertEqual(len(temps), 1)
            self.assertEqual(temps[0].read_bytes(), concurrent)
            self.assertIn(temps[0].as_posix(), raised.exception.preserved_paths)

    def test_install_codex_agents_windows_cleanup_handle_delete_preserves_final_takeover(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target_name = "agent.tmp"
            target = destination / target_name
            target.write_bytes(b"windows installer-owned cleanup\n")
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()
            cleanup_name = ".cleanupid.cleanup.agent.tmp"
            cleanup_path = destination / cleanup_name
            injected = False

            def inject_takeover(target_path: PosixPath) -> None:
                nonlocal injected
                if target_path == cleanup_path and not injected:
                    injected = True
                    target_path.unlink()
                    target_path.write_bytes(b"windows final takeover must survive\n")

            fake.before_deletefile = inject_takeover
            fake.before_file_disposition = inject_takeover

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install.secrets, "token_hex", return_value="cleanupid"),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                try:
                    state = agent_dir.previous_state(target_name)
                    assert state is not None
                    conflicts = agent_dir.cleanup_owned_entry(target_name, state)
                finally:
                    agent_dir.close()

            self.assertTrue(injected)
            self.assertEqual(cleanup_path.read_bytes(), b"windows final takeover must survive\n")
            self.assertIn(cleanup_path.as_posix(), conflicts)

    def test_install_codex_agents_windows_cleanup_unreadable_after_delete_failure_is_concurrent_unknown(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target_name = "agent.tmp"
            target = destination / target_name
            target.write_bytes(b"windows installer-owned cleanup\n")
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()
            cleanup_name = ".cleanupid.cleanup.agent.tmp"
            cleanup_path = destination / cleanup_name
            delete_failed = False

            def fail_handle_delete(_handle: int) -> None:
                nonlocal delete_failed
                delete_failed = True
                raise OSError("injected handle delete failure")

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install.secrets, "token_hex", return_value="cleanupid"),
                patch.object(install, "codex_agent_windows_delete_by_handle", side_effect=fail_handle_delete),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                real_previous = agent_dir.previous_state

                def cleanup_read_error(name: str) -> object:
                    if delete_failed and name == cleanup_name:
                        raise OSError("injected cleanup read error")
                    return real_previous(name)

                try:
                    state = agent_dir.previous_state(target_name)
                    assert state is not None
                    with patch.object(agent_dir, "previous_state", side_effect=cleanup_read_error):
                        result = agent_dir.cleanup_owned_entry(target_name, state)
                finally:
                    agent_dir.close()

            self.assertEqual(cleanup_path.read_bytes(), b"windows installer-owned cleanup\n")
            self.assertIn(cleanup_path.as_posix(), result.public_conflicts)
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": cleanup_path.as_posix(), "error": "OSError"},
                result.cleanup_errors,
            )
            self.assertNotIn(
                {"kind": "cleanup_incomplete", "target": cleanup_path.as_posix(), "error": "OSError"},
                result.cleanup_errors,
            )

    def test_install_codex_agents_windows_cleanup_moved_state_mismatch_reports_cleanup_and_recreated_target(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target_name = "agent.tmp"
            target = destination / target_name
            target.write_bytes(b"windows installer-owned cleanup\n")
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()
            cleanup_name = ".cleanupid.cleanup.agent.tmp"
            cleanup_path = destination / cleanup_name
            real_windows_rename = install.codex_agent_windows_rename_no_replace
            mismatch_ready = False

            def move_then_recreate(agent_dir: object, source: str, target_name_arg: str) -> None:
                nonlocal mismatch_ready
                real_windows_rename(agent_dir, source, target_name_arg)
                if source == target_name:
                    cleanup_path.write_bytes(b"windows mismatched cleanup\n")
                    target.write_bytes(b"windows recreated target\n")
                    mismatch_ready = True

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install.secrets, "token_hex", return_value="cleanupid"),
                patch.object(install, "codex_agent_windows_rename_no_replace", side_effect=move_then_recreate),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                real_previous = agent_dir.previous_state

                def target_read_error(name: str) -> object:
                    if mismatch_ready and name == target_name:
                        raise OSError("injected recreated-target read error")
                    return real_previous(name)

                try:
                    state = agent_dir.previous_state(target_name)
                    assert state is not None
                    with patch.object(agent_dir, "previous_state", side_effect=target_read_error):
                        result = agent_dir.cleanup_owned_entry(target_name, state)
                finally:
                    agent_dir.close()

            self.assertEqual(cleanup_path.read_bytes(), b"windows mismatched cleanup\n")
            self.assertEqual(target.read_bytes(), b"windows recreated target\n")
            self.assertEqual(result.public_conflicts, [cleanup_path.as_posix(), target.as_posix()])
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": cleanup_path.as_posix(), "error": "cleanup_moved_state_mismatch"},
                result.cleanup_errors,
            )
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": target.as_posix(), "error": "cleanup_moved_state_mismatch"},
                result.cleanup_errors,
            )

    def test_install_codex_agents_windows_cleanup_result_records_close_failure_without_collector(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target_name = "agent.tmp"
            target = destination / target_name
            target.write_bytes(b"windows installer-owned cleanup\n")
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()
            cleanup_name = ".cleanupid.cleanup.agent.tmp"
            cleanup_path = destination / cleanup_name
            fake.fail_close_paths.add(cleanup_path)

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install.secrets, "token_hex", return_value="cleanupid"),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                try:
                    state = agent_dir.previous_state(target_name)
                    assert state is not None
                    result = agent_dir.cleanup_owned_entry(target_name, state)
                finally:
                    agent_dir.close()

            self.assertEqual(result.public_conflicts, [])
            self.assertEqual(result.preserved_private_paths, [])
            self.assertGreaterEqual(
                result.cleanup_errors.count({"kind": "close_handle", "target": cleanup_path.as_posix(), "error": "OSError"}),
                2,
            )

    def test_install_codex_agents_windows_cleanup_records_close_failure_after_successful_handle_delete(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target_name = "agent.tmp"
            target = destination / target_name
            target.write_bytes(b"windows installer-owned cleanup\n")
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()
            cleanup_name = ".cleanupid.cleanup.agent.tmp"
            cleanup_path = destination / cleanup_name
            fake.fail_close_paths.add(cleanup_path)

            def delete_by_path_for_close_test(handle: int) -> None:
                PosixPath(fake.handles[handle]["path"]).unlink()

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install.secrets, "token_hex", return_value="cleanupid"),
                patch.object(install, "codex_agent_windows_delete_by_handle", side_effect=delete_by_path_for_close_test),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                try:
                    state = agent_dir.previous_state(target_name)
                    assert state is not None
                    result = agent_dir.cleanup_owned_entry(target_name, state)
                finally:
                    agent_dir.close()

            self.assertEqual(result.public_conflicts, [])
            self.assertEqual(result.preserved_private_paths, [])
            self.assertFalse(cleanup_path.exists())
            self.assertGreaterEqual(
                result.cleanup_errors.count({"kind": "close_handle", "target": cleanup_path.as_posix(), "error": "OSError"}),
                2,
            )
            self.assertTrue(any(record["path"] == cleanup_path for record in fake.handles.values()))

    def test_install_codex_agents_windows_cleanup_rename_close_failure_reports_recreated_source(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target_name = "agent.tmp"
            target = destination / target_name
            target.write_bytes(b"windows installer-owned cleanup\n")
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()
            cleanup_name = ".cleanupid.cleanup.agent.tmp"
            cleanup_path = destination / cleanup_name
            fake.fail_close_paths.add(cleanup_path)
            real_set_file_information = fake.SetFileInformationByHandle
            recreated = False

            def rename_then_recreate_source(
                handle: int,
                info_class: int,
                rename_info_buffer: object,
                buffer_size: int,
            ) -> int:
                nonlocal recreated
                result = real_set_file_information(handle, info_class, rename_info_buffer, buffer_size)
                if (
                    result
                    and info_class == install.WINDOWS_FILE_RENAME_INFO_CLASS
                    and PosixPath(fake.handles[handle]["path"]) == cleanup_path
                    and not recreated
                ):
                    recreated = True
                    target.write_bytes(b"windows recreated source after cleanup rename\n")
                return result

            fake.SetFileInformationByHandle = rename_then_recreate_source  # type: ignore[method-assign]

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install.secrets, "token_hex", return_value="cleanupid"),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                try:
                    state = agent_dir.previous_state(target_name)
                    assert state is not None
                    result = agent_dir.cleanup_owned_entry(target_name, state)
                finally:
                    agent_dir.close()

            self.assertTrue(recreated)
            self.assertEqual(target.read_bytes(), b"windows recreated source after cleanup rename\n")
            self.assertFalse(cleanup_path.exists())
            self.assertIn(target.as_posix(), result.public_conflicts)
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": target.as_posix(), "error": "cleanup_rename_close_failure"},
                result.cleanup_errors,
            )
            self.assertIn(
                {"kind": "close_handle", "target": cleanup_path.as_posix(), "error": "OSError"},
                result.cleanup_errors,
            )

    def test_install_codex_agents_windows_cleanup_generic_rename_error_classifies_candidate_and_source(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target_name = "agent.tmp"
            target = destination / target_name
            target.write_bytes(b"windows installer-owned cleanup\n")
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()
            cleanup_name = ".cleanupid.cleanup.agent.tmp"
            cleanup_path = destination / cleanup_name

            def rename_then_mismatch_and_recreate(
                agent_dir: object,
                source_name: str,
                target_name_arg: str,
            ) -> None:
                del agent_dir
                if source_name == target_name and target_name_arg == cleanup_name:
                    os.rename(target, cleanup_path)
                    cleanup_path.write_bytes(b"windows mismatched cleanup candidate\n")
                    target.write_bytes(b"windows recreated source after generic rename error\n")
                    raise OSError("generic post-rename failure")
                raise AssertionError("unexpected rename call")

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install.secrets, "token_hex", return_value="cleanupid"),
                patch.object(install, "codex_agent_windows_rename_no_replace", side_effect=rename_then_mismatch_and_recreate),
            ):
                agent_dir = install.AnchoredAgentDir.open(destination, identity)
                try:
                    state = agent_dir.previous_state(target_name)
                    assert state is not None
                    result = agent_dir.cleanup_owned_entry(target_name, state)
                finally:
                    agent_dir.close()

            self.assertEqual(cleanup_path.read_bytes(), b"windows mismatched cleanup candidate\n")
            self.assertEqual(target.read_bytes(), b"windows recreated source after generic rename error\n")
            self.assertEqual(result.public_conflicts, [cleanup_path.as_posix(), target.as_posix()])
            self.assertFalse(any(error["kind"] == "close_handle" for error in result.cleanup_errors))
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": cleanup_path.as_posix(), "error": "cleanup_rename_failed"},
                result.cleanup_errors,
            )
            self.assertIn(
                {"kind": "preserved_concurrent_file", "target": target.as_posix(), "error": "cleanup_rename_failed"},
                result.cleanup_errors,
            )

    def test_install_codex_agents_windows_temp_close_failure_is_cleanup_evidence_before_directory_removal(self) -> None:
        from speckit_pro_runner.helpers import install
        from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            destination = root / ".codex" / "agents"
            fake = FakeWindowsKernel32()

            def fail_write(
                handle: int,
                buffer: object,
                bytes_to_write: int,
                bytes_written_pointer: object,
                overlapped: object,
            ) -> int:
                del handle, buffer, bytes_to_write, overlapped
                bytes_written_pointer._obj.value = 0
                fake.set_last_error(fake.ERROR_ACCESS_DENIED)
                return 0

            fake.WriteFile = fail_write  # type: ignore[method-assign]
            request = SimpleNamespace(
                request_id="test-windows-close-cleanup-evidence",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="apply",
                inputs={},
            )
            real_rmdir = Path.rmdir

            def reject_directory_removal_while_anchor_open(path: Path) -> None:
                if path == destination and any(record["path"] == destination for record in fake.handles.values()):
                    raise OSError("directory anchor still open")
                real_rmdir(path)

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install, "codex_plugin_root", return_value=PLUGIN_ROOT),
                patch.object(install, "codex_agent_destination", return_value=destination),
                patch.object(install, "load_codex_agent_bundle", return_value=({"agent.toml": b"installer bytes\n"}, "gpt-5.5")),
                patch.object(Path, "rmdir", autospec=True, side_effect=reject_directory_removal_while_anchor_open),
            ):
                fake.fail_close = True
                response = install.run_codex_agent_install(MUTATION_HELPERS["install-codex-agents"], request)

            self.assert_response(response, "expected_failure", 1)
            cleanup_errors = response["diagnostics"][0]["details"]["cleanup_errors"]
            self.assertTrue(any(error["kind"] == "close_handle" for error in cleanup_errors))
            self.assertTrue(
                any(error["kind"] == "close_handle" and error["target"] == destination.as_posix() for error in cleanup_errors)
            )
            self.assertTrue(any(error["kind"] == "remove_directory" for error in cleanup_errors))
            self.assertTrue(destination.exists())

    def test_install_codex_agents_windows_success_reports_final_anchor_close_failure(self) -> None:
        from speckit_pro_runner.helpers import install
        from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            destination = root / ".codex" / "agents"
            fake = FakeWindowsKernel32()
            fake.fail_close_paths.add(destination)
            request = SimpleNamespace(
                request_id="test-windows-success-final-close-failure",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="apply",
                inputs={},
            )

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install, "codex_plugin_root", return_value=PLUGIN_ROOT),
                patch.object(install, "codex_agent_destination", return_value=destination),
                patch.object(install, "load_codex_agent_bundle", return_value=({"agent.toml": b"installer bytes\n"}, "gpt-5.5")),
            ):
                response = install.run_codex_agent_install(MUTATION_HELPERS["install-codex-agents"], request)

            self.assert_response(response, "expected_failure", 1)
            details = response["diagnostics"][0]["details"]
            self.assertEqual(details["cleanup_errors"][0]["kind"], "close_handle")
            self.assertEqual(details["cleanup_errors"][0]["target"], destination.as_posix())
            self.assertTrue(any(record["path"] == destination for record in fake.handles.values()))

    def test_install_codex_agents_windows_write_apply_does_not_fail_on_nt_backend(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target = destination / "agent.toml"
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
            ):
                state = install.write_codex_agent_atomic(
                    target,
                    b"windows install\n",
                    destination,
                    identity,
                    expected_state=None,
                )

            self.assertEqual(state.content, b"windows install\n")
            self.assertEqual(target.read_bytes(), b"windows install\n")

    def test_install_codex_agents_windows_readonly_rollback_write_uses_handle_bound_cleanup(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target_name = "agent.toml"
            target = destination / target_name
            identity = install.codex_agent_destination_identity(destination)
            state = install.CodexAgentFileState(
                content=b"readonly rollback bytes\n",
                mode=stat.S_IFREG | 0o444,
                device=11,
                inode=22,
            )
            fake = FakeWindowsKernel32()

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install.os, "chmod", side_effect=AssertionError("path chmod is forbidden for Windows rollback cleanup")),
            ):
                failures, cleanup_errors = install.rollback_codex_agent_install(
                    destination,
                    {target_name: state},
                    identity,
                    expected_current={target_name: None},
                )

            self.assertEqual(failures, [])
            self.assertEqual(cleanup_errors, [])
            self.assertEqual(target.read_bytes(), state.content)
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o400)
            self.assertFalse(
                any(target_name in path.name and ".cleanup." in path.name for path in fake.deletefile_calls)
            )

    def test_install_codex_agents_windows_readonly_write_rejects_target_swap_before_mode_apply(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target = destination / "agent.toml"
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()
            real_apply_mode = install.WindowsAnchoredAgentDir.apply_child_mode_verified
            injected = False

            def swap_target_before_mode_apply(
                agent_dir: object,
                name: str,
                mode: int,
                expected_state: object,
            ) -> object:
                nonlocal injected
                if not injected and name == target.name:
                    injected = True
                    target.unlink()
                    target.write_bytes(b"concurrent replacement must survive\n")
                return real_apply_mode(agent_dir, name, mode, expected_state)

            def delete_by_path_for_mode_test(handle: int) -> None:
                PosixPath(fake.handles[handle]["path"]).unlink()

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
                patch.object(install.WindowsAnchoredAgentDir, "apply_child_mode_verified", swap_target_before_mode_apply),
                patch.object(install, "codex_agent_windows_delete_by_handle", side_effect=delete_by_path_for_mode_test),
            ):
                with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                    install.write_codex_agent_atomic(
                        target,
                        b"readonly installer bytes\n",
                        destination,
                        identity,
                        mode=stat.S_IFREG | 0o444,
                        expected_state=None,
                    )

            self.assertTrue(injected)
            self.assertEqual(target.read_bytes(), b"concurrent replacement must survive\n")
            self.assertIn(target.as_posix(), raised.exception.preserved_paths)
            self.assertNotEqual(stat.S_IMODE(target.stat().st_mode), 0o400)

    def test_install_codex_agents_windows_directory_handle_outlives_backup_rename(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target = destination / "agent.toml"
            target.write_bytes(b"prior\n")
            expected = install.codex_agent_previous_state(target)
            identity = install.codex_agent_destination_identity(destination)
            fake = FakeWindowsKernel32()

            with (
                patch.object(install.os, "name", "nt"),
                patch.object(install.ctypes, "WinDLL", return_value=fake, create=True),
                patch.object(install.ctypes, "get_last_error", side_effect=fake.get_last_error, create=True),
            ):
                install.write_codex_agent_atomic(
                    target,
                    b"windows replacement\n",
                    destination,
                    identity,
                    expected_state=expected,
                )

            directory_handle = int(fake.rename_calls[0]["root"])
            self.assertLess(
                fake.events.index("SetFileInformationByHandle"),
                fake.events.index(f"CloseHandle:{directory_handle}"),
            )

    def test_install_codex_agents_darwin_renameatx_missing_fails_closed(self) -> None:
        from speckit_pro_runner.helpers import install

        with (
            patch.object(install.sys, "platform", "darwin"),
            patch.object(install.ctypes, "CDLL", return_value=SimpleNamespace()),
        ):
            with self.assertRaisesRegex(OSError, "renameatx_np is unavailable"):
                install.codex_agent_native_rename_no_replace(3, "source.toml", "target.toml")

    def test_install_codex_agents_native_no_replace_uses_platform_flags_and_eexist(self) -> None:
        from speckit_pro_runner.helpers import install

        class RenameProbe:
            def __init__(self) -> None:
                self.calls: list[tuple[int, bytes, int, bytes, int]] = []
                self.argtypes: object | None = None
                self.restype: object | None = None

            def __call__(self, source_fd: int, source: bytes, target_fd: int, target: bytes, flags: int) -> int:
                self.calls.append((source_fd, source, target_fd, target, flags))
                install.ctypes.set_errno(install.errno.EEXIST)
                return -1

        for platform_name, symbol, expected_flag in (
            ("darwin", "renameatx_np", 0x00000004),
            ("linux", "renameat2", 0x00000001),
        ):
            with self.subTest(platform=platform_name):
                probe = RenameProbe()
                library = SimpleNamespace(**{symbol: probe})
                with (
                    patch.object(install.sys, "platform", platform_name),
                    patch.object(install.ctypes, "CDLL", return_value=library),
                ):
                    with self.assertRaises(FileExistsError):
                        install.codex_agent_native_rename_no_replace(7, "source.toml", "target.toml")
                self.assertEqual(probe.calls, [(7, b"source.toml", 7, b"target.toml", expected_flag)])

    def test_install_codex_agents_native_no_replace_rejects_unsupported_platform(self) -> None:
        from speckit_pro_runner.helpers import install

        with patch.object(install.sys, "platform", "freebsd14"):
            with self.assertRaisesRegex(OSError, "anchored atomic no-replace rename is unavailable"):
                install.codex_agent_native_rename_no_replace(3, "source.toml", "target.toml")

    def test_install_codex_agents_rollback_cleanup_race_preserves_original_state_and_paths(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "agent.toml"
            target.write_bytes(b"original user bytes\n")
            target.chmod(0o751)
            original_state = install.codex_agent_previous_state(target)
            assert original_state is not None
            target.write_bytes(b"installer bytes\n")
            target.chmod(0o644)
            installer_state = install.codex_agent_previous_state(target)
            assert installer_state is not None
            identity = install.codex_agent_destination_identity(destination)
            concurrent = destination / ".concurrent-rollback"
            concurrent.write_bytes(b"concurrent rollback edit\n")
            real_unlink = install.os.unlink
            real_replace = os.replace
            injected = False

            def replace_during_rollback_cleanup(path: object, *args: object, **kwargs: object) -> None:
                nonlocal injected
                if (
                    str(path).endswith(".bak")
                    and target.exists()
                    and target.read_bytes() == original_state.content
                    and not injected
                ):
                    injected = True
                    real_replace(concurrent, target)
                real_unlink(path, *args, **kwargs)

            with patch.object(install.os, "unlink", side_effect=replace_during_rollback_cleanup):
                failures, cleanup_errors = install.rollback_codex_agent_install(
                    destination,
                    {target.name: original_state},
                    identity,
                    expected_current={target.name: installer_state},
                )

            self.assertFalse(injected)
            self.assertEqual(failures, [])
            self.assertEqual(cleanup_errors, [])
            self.assertEqual(target.read_bytes(), original_state.content)
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o751)
            backups = list(destination.glob(".*.cleanup-dir/*"))
            self.assertTrue(any(path.read_bytes() == installer_state.content for path in backups))

    def test_install_codex_agents_recovery_copy_refuses_replaced_destination(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            destination = root / "agents"
            destination.mkdir()
            source = destination / "source.toml"
            source.write_bytes(b"original bytes\n")
            state = install.codex_agent_previous_state(source)
            assert state is not None
            identity = install.codex_agent_destination_identity(destination)
            moved = root / "moved-agents"
            outside = root / "outside"
            outside.mkdir()
            destination.rename(moved)
            destination.symlink_to(outside, target_is_directory=True)

            with self.assertRaises(install.CodexAgentRecoveryCopyFailure):
                install.codex_agent_preserve_state_as_backup(
                    state,
                    destination / "agent.toml",
                    destination,
                    identity,
                )

            self.assertEqual(list(outside.iterdir()), [])
            self.assertEqual(list(moved.glob(".*.bak")), [])

    def test_install_codex_agents_backup_move_does_not_relinquish_candidate_before_native_move(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target = destination / "agent.toml"
            target.write_bytes(b"original target bytes\n")
            real_unlink = Path.unlink
            relinquished = False

            def detect_placeholder_unlink(path: Path, *args: object, **kwargs: object) -> None:
                nonlocal relinquished
                if path.suffix == ".bak" and target.exists():
                    relinquished = True
                real_unlink(path, *args, **kwargs)

            with patch.object(Path, "unlink", autospec=True, side_effect=detect_placeholder_unlink):
                backup = install.codex_agent_move_target_to_backup(target, destination)

            self.assertFalse(relinquished)
            self.assertFalse(target.exists())
            self.assertEqual(backup.read_bytes(), b"original target bytes\n")

    def test_install_codex_agents_backup_move_retries_native_no_replace_collision(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            target = destination / "agent.toml"
            target.write_bytes(b"original target bytes\n")
            identity = install.codex_agent_destination_identity(destination)
            real_move = install.codex_agent_native_rename_no_replace
            collision: Path | None = None
            injected = False

            def collide_once(directory_fd: int, source: str, backup: str) -> None:
                nonlocal collision, injected
                if not injected:
                    injected = True
                    collision = destination / backup
                    collision.write_bytes(b"concurrent backup-name entry\n")
                real_move(directory_fd, source, backup)

            with patch.object(install, "codex_agent_native_rename_no_replace", side_effect=collide_once):
                backup = install.codex_agent_move_target_to_backup(target, destination, identity)

            assert collision is not None
            self.assertEqual(collision.read_bytes(), b"concurrent backup-name entry\n")
            self.assertEqual(backup.read_bytes(), b"original target bytes\n")
            self.assertNotEqual(collision, backup)

    def test_install_codex_agents_restore_refuses_replacement_directory(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            destination = root / "agents"
            destination.mkdir()
            backup_name = ".agent.toml.initial.bak"
            original_backup = destination / backup_name
            original_backup.write_bytes(b"original backup bytes\n")
            identity = install.codex_agent_destination_identity(destination)
            moved = root / "moved-agents"
            destination.rename(moved)
            destination.mkdir()
            replacement_backup = destination / backup_name
            replacement_backup.write_bytes(b"replacement-directory bytes\n")

            with self.assertRaisesRegex(OSError, "destination changed"):
                install.codex_agent_restore_backup_no_clobber(
                    replacement_backup,
                    destination / "agent.toml",
                    destination,
                    identity,
                )

            self.assertEqual(replacement_backup.read_bytes(), b"replacement-directory bytes\n")
            self.assertFalse((destination / "agent.toml").exists())
            self.assertEqual((moved / backup_name).read_bytes(), b"original backup bytes\n")

    def test_install_codex_agents_recovery_copy_detects_post_open_directory_move(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            destination = root / "agents"
            destination.mkdir()
            source = destination / "source.toml"
            source.write_bytes(b"original bytes\n")
            state = install.codex_agent_previous_state(source)
            assert state is not None
            identity = install.codex_agent_destination_identity(destination)
            moved = root / "moved-agents"
            real_open = install.os.open
            injected = False

            def move_after_copy_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
                nonlocal injected
                descriptor = real_open(path, flags, *args, **kwargs)
                if kwargs.get("dir_fd") is not None and flags & os.O_CREAT and not injected:
                    injected = True
                    destination.rename(moved)
                    destination.mkdir()
                return descriptor

            with patch.object(install.os, "open", side_effect=move_after_copy_open):
                with self.assertRaises(install.CodexAgentRecoveryCopyFailure) as raised:
                    install.codex_agent_preserve_state_as_backup(
                        state,
                        destination / "agent.toml",
                        destination,
                        identity,
                    )

            self.assertEqual(len(raised.exception.failed_paths), 1)
            self.assertTrue(raised.exception.failed_paths[0].startswith("anchored-agent-dir:"))
            backups = list(moved.glob(".*.bak"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), state.content)
            self.assertEqual(list(destination.iterdir()), [])

    def test_install_codex_agents_recovery_copy_precreate_failure_reports_no_phantom_path(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            source = destination / "source.toml"
            source.write_bytes(b"original bytes\n")
            state = install.codex_agent_previous_state(source)
            assert state is not None
            identity = install.codex_agent_destination_identity(destination)
            real_open = install.os.open

            def reject_copy_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
                if kwargs.get("dir_fd") is not None and flags & os.O_CREAT:
                    raise PermissionError("injected copy-open failure")
                return real_open(path, flags, *args, **kwargs)

            with patch.object(install.os, "open", side_effect=reject_copy_open):
                with self.assertRaises(install.CodexAgentRecoveryCopyFailure) as raised:
                    install.codex_agent_preserve_state_as_backup(
                        state,
                        destination / "agent.toml",
                        destination,
                        identity,
                    )

            self.assertEqual(raised.exception.failed_paths, [])
            self.assertEqual(list(destination.glob(".*.bak")), [])

    def test_install_codex_agents_recovery_copy_close_errors_are_non_masking_and_exhaustive(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            source = destination / "source.toml"
            source.write_bytes(b"original bytes\n")
            state = install.codex_agent_previous_state(source)
            assert state is not None
            identity = install.codex_agent_destination_identity(destination)
            real_close = install.os.close
            close_calls: list[int] = []

            def close_then_report(descriptor: int) -> None:
                close_calls.append(descriptor)
                real_close(descriptor)
                raise OSError("injected close evidence failure")

            with patch.object(install.os, "close", side_effect=close_then_report):
                with self.assertRaises(install.CodexAgentRecoveryCopyFailure) as raised:
                    install.codex_agent_preserve_state_as_backup(
                        state,
                        destination / "agent.toml",
                        destination,
                        identity,
                    )

            self.assertEqual(len(close_calls), 2)
            self.assertIn("descriptor cleanup errors=1", str(raised.exception))
            self.assertEqual(len(raised.exception.failed_paths), 1)

    def test_install_codex_agents_incomplete_recovery_copy_is_not_preserved_evidence(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            source = destination / "source.toml"
            source.write_bytes(b"exact original bytes\n")
            source.chmod(0o751)
            state = install.codex_agent_previous_state(source)
            assert state is not None
            identity = install.codex_agent_destination_identity(destination)

            with patch.object(install.os, "fchmod", side_effect=OSError("injected mode failure")):
                with self.assertRaises(install.CodexAgentRecoveryCopyFailure) as raised:
                    install.codex_agent_preserve_state_as_backup(
                        state,
                        destination / "agent.toml",
                        destination,
                        identity,
                    )

            self.assertNotIsInstance(raised.exception, install.CodexAgentNoClobberConflict)
            errors = [
                {"kind": "recovery_copy_failed", "target": path, "error": "recovery_copy_incomplete"}
                for path in raised.exception.failed_paths
            ]
            actions = install.codex_route_aware_cleanup_manual_remediation(errors)
            self.assertEqual(actions[0]["reason"], "recovery_copy_failed")
            self.assertTrue(all(Path(path).exists() for path in raised.exception.failed_paths))

    def test_install_codex_agents_posix_recovery_copy_failure_preserves_unreadable_target_unknown(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve()
            source = destination / "source.toml"
            source.write_bytes(b"exact original bytes\n")
            target = destination / "agent.toml"
            target.write_bytes(b"unreadable target after copy failure\n")
            state = install.codex_agent_previous_state(source)
            assert state is not None
            identity = install.codex_agent_destination_identity(destination)
            real_previous_state = install.AnchoredAgentDir.previous_state

            def unreadable_target(self: object, name: str) -> object:
                if name == target.name:
                    raise OSError("injected target read error")
                return real_previous_state(self, name)

            with (
                patch.object(install.os, "fchmod", side_effect=OSError("injected mode failure")),
                patch.object(install.AnchoredAgentDir, "previous_state", unreadable_target),
            ):
                with self.assertRaises(install.CodexAgentRecoveryCopyFailure) as raised:
                    install.codex_agent_preserve_state_as_backup(
                        state,
                        target,
                        destination,
                        identity,
                    )

            self.assertEqual(len(raised.exception.failed_paths), 1)
            self.assertEqual(raised.exception.preserved_paths, [target.as_posix()])
            cleanup_errors = [
                {"kind": "recovery_copy_failed", "target": path, "error": "recovery_copy_incomplete"}
                for path in raised.exception.failed_paths
            ]
            cleanup_errors.extend(
                install.codex_agent_unproven_preserved_path_records(
                    raised.exception.preserved_paths,
                    cleanup_errors,
                    "no_clobber_conflict",
                )
            )
            actions = install.codex_route_aware_cleanup_manual_remediation(cleanup_errors)
            self.assertEqual([action["reason"] for action in actions], ["concurrent_file_preserved", "recovery_copy_failed"])
            self.assertEqual(actions[0]["paths"], [target.as_posix()])
            self.assertEqual(actions[1]["paths"], raised.exception.failed_paths)

    def test_install_codex_agents_cleanup_reports_directory_removal_errors(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / ".codex" / "agents"
            destination.mkdir(parents=True)
            with patch.object(Path, "rmdir", side_effect=OSError("injected cleanup failure")):
                actions, errors = install.cleanup_codex_agent_destination(
                    destination,
                    destination_existed=False,
                    destination_parent_existed=False,
                )

            self.assertEqual(actions, [])
            self.assertEqual(
                [error["target"] for error in errors],
                [destination.as_posix(), destination.parent.as_posix()],
            )
            self.assertTrue(all(error["error"] == "OSError" for error in errors))
            self.assertEqual(
                install.codex_route_aware_cleanup_manual_remediation(errors)[0]["paths"],
                [destination.as_posix(), destination.parent.as_posix()],
            )

    def test_install_codex_agents_cleanup_refuses_replacement_destination_identity(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            destination = root / ".codex" / "agents"
            destination.mkdir(parents=True)
            identity = install.codex_agent_destination_identity(destination)
            moved = root / "moved-agents"
            destination.rename(moved)
            destination.mkdir(parents=True)
            (destination / "replacement.toml").write_text("replacement must survive\n", encoding="utf-8")

            actions, errors = install.cleanup_codex_agent_destination(
                destination,
                destination_existed=False,
                destination_parent_existed=False,
                destination_identity=identity,
            )

            self.assertEqual(actions, [])
            self.assertTrue((destination / "replacement.toml").exists())
            self.assertEqual(errors[0]["kind"], "remove_directory")
            self.assertEqual(errors[0]["error"], "destination_identity_mismatch")

    def test_install_codex_agents_cleanup_directory_quarantine_uses_no_replace_move(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            destination = root / ".codex" / "agents"
            destination.mkdir(parents=True)
            identity = install.codex_agent_destination_identity(destination)
            quarantine = destination.parent / ".agents.dirrace.cleanup-dir"
            real_no_replace = install.codex_agent_native_rename_no_replace
            injected = False
            victim_identity: tuple[int, int] | None = None

            def inject_concurrent_quarantine(directory_fd: int, source_name: str, target_name: str) -> None:
                nonlocal injected, victim_identity
                if source_name == "agents" and target_name == ".agents.dirrace.cleanup-dir" and not injected:
                    injected = True
                    quarantine.mkdir()
                    victim_identity = install.codex_agent_destination_identity(quarantine)
                    raise FileExistsError(errno.EEXIST, "concurrent quarantine", target_name)
                real_no_replace(directory_fd, source_name, target_name)

            with (
                patch.object(install.secrets, "token_hex", return_value="dirrace"),
                patch.object(install, "codex_agent_native_rename_no_replace", side_effect=inject_concurrent_quarantine),
            ):
                actions, errors = install.cleanup_codex_agent_destination(
                    destination,
                    destination_existed=False,
                    destination_parent_existed=False,
                    destination_identity=identity,
                )

            self.assertTrue(injected)
            self.assertEqual(actions, [])
            self.assertTrue(quarantine.exists())
            self.assertEqual(install.codex_agent_destination_identity(quarantine), victim_identity)
            self.assertEqual(errors[0]["kind"], "remove_directory")
            self.assertIn(errors[0]["error"], {"cleanup_name_conflict", "cleanup_name_unavailable", "FileExistsError"})

    def test_install_codex_agents_cleanup_directory_final_removal_fails_closed_on_quarantine_swap(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            destination = root / ".codex" / "agents"
            destination.mkdir(parents=True)
            identity = install.codex_agent_destination_identity(destination)
            quarantine = destination.parent / ".agents.finalswap.cleanup-dir"
            moved = root / "moved-quarantine"
            real_rmdir = Path.rmdir

            def replace_quarantine_before_path_rmdir(path: Path) -> None:
                if path == quarantine and quarantine.exists():
                    quarantine.rename(moved)
                    quarantine.mkdir()
                    (quarantine / "replacement.txt").write_text("replacement must survive\n", encoding="utf-8")
                real_rmdir(path)

            with (
                patch.object(install.secrets, "token_hex", return_value="finalswap"),
                patch.object(Path, "rmdir", autospec=True, side_effect=replace_quarantine_before_path_rmdir),
            ):
                actions, errors = install.cleanup_codex_agent_destination(
                    destination,
                    destination_existed=False,
                    destination_parent_existed=False,
                    destination_identity=identity,
                )

            self.assertEqual(actions, [])
            self.assertTrue(quarantine.exists())
            self.assertEqual(errors[0]["kind"], "remove_directory")
            self.assertIn(
                errors[0]["error"],
                {"identity_bound_directory_removal_unavailable", "destination_replaced_during_cleanup"},
            )

    def test_install_codex_agents_cleanup_enforces_created_parent_identity(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            parent = root / ".codex"
            destination = parent / "agents"
            parent.mkdir()
            parent_identity = install.codex_agent_destination_identity(parent)
            moved = root / "moved-codex"
            parent.rename(moved)
            parent.mkdir()
            (parent / "replacement.txt").write_text("replacement must survive\n", encoding="utf-8")

            actions, errors = install.cleanup_codex_agent_destination(
                destination,
                destination_existed=True,
                destination_parent_existed=False,
                destination_parent_identity=parent_identity,
            )

            self.assertEqual(actions, [])
            self.assertTrue((parent / "replacement.txt").exists())
            self.assertEqual(errors[0]["kind"], "remove_directory")
            self.assertEqual(errors[0]["target"], parent.as_posix())
            self.assertEqual(errors[0]["error"], "destination_identity_mismatch")

    def test_install_codex_agents_cleanup_final_rmdir_swap_preserves_replacement_directory(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            destination = root / ".codex" / "agents"
            destination.mkdir(parents=True)
            identity = install.codex_agent_destination_identity(destination)
            real_rmdir = Path.rmdir

            def swap_before_public_rmdir(path: Path) -> None:
                if path == destination:
                    raise AssertionError("identity-bound cleanup must not path-rmdir the public destination")
                real_rmdir(path)

            with patch.object(Path, "rmdir", autospec=True, side_effect=swap_before_public_rmdir):
                actions, errors = install.cleanup_codex_agent_destination(
                    destination,
                    destination_existed=False,
                    destination_parent_existed=False,
                    destination_identity=identity,
                )

            self.assertEqual(actions, [])
            self.assertFalse(destination.exists())
            self.assertEqual(errors[0]["kind"], "remove_directory")
            self.assertEqual(errors[0]["error"], "identity_bound_directory_removal_unavailable")

    def test_install_codex_agents_no_clobber_restore_reports_both_preserved_entries(self) -> None:
        from speckit_pro_runner.helpers import install

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            backup = root / ".agent.toml.conflict.bak"
            target = root / "agent.toml"
            backup.write_bytes(b"first concurrent version\n")
            target.write_bytes(b"second concurrent version\n")

            with self.assertRaises(install.CodexAgentNoClobberConflict) as raised:
                install.codex_agent_restore_backup_no_clobber(backup, target)

            self.assertEqual(raised.exception.preserved_paths, [backup.as_posix(), target.as_posix()])
            self.assertEqual(backup.read_bytes(), b"first concurrent version\n")
            self.assertEqual(target.read_bytes(), b"second concurrent version\n")
            actions = install.codex_route_aware_cleanup_manual_remediation(
                [
                    {"kind": "preserved_concurrent_file", "target": path, "error": "no_clobber_conflict"}
                    for path in raised.exception.preserved_paths
                ]
            )
            self.assertEqual(actions[0]["reason"], "concurrent_file_preserved")
            self.assertEqual(actions[0]["paths"], [backup.as_posix(), target.as_posix()])

    def test_install_codex_agents_route_aware_refuses_concurrent_edit_before_write(self) -> None:
        from speckit_pro_runner.helpers import install
        from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

        tmp, git_root = self.temp_clean_git_repo()
        with tmp, tempfile.TemporaryDirectory() as home_tmp:
            fake_home = Path(home_tmp).resolve()
            manifest_path = self.write_valid_route_policy_manifest(git_root)
            expected_snapshot = routing_capability_snapshot()
            expected_snapshot["available_routes"] = ["required-primary", "required-fallback"]
            destination = fake_home / ".codex" / "agents"
            destination.mkdir(parents=True)
            agent_names = routing_required_agents()
            prior = {
                name: f"prior {name}\n".encode("utf-8")
                for name in agent_names
            }
            for name, content in prior.items():
                (destination / f"{name}.toml").write_bytes(content)
            changed_name = agent_names[1]
            changed_target = destination / f"{changed_name}.toml"
            concurrent_bytes = b"concurrent user edit before installer write\n"
            real_matches = install.codex_agent_state_matches
            changed = False

            def change_before_match(target: Path, expected: object) -> bool:
                nonlocal changed
                if target == changed_target and not changed:
                    changed = True
                    target.write_bytes(concurrent_bytes)
                return real_matches(target, expected)

            request = SimpleNamespace(
                request_id="test-route-aware-concurrent-pre-write",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="apply",
                inputs=self.route_aware_inputs(manifest_path, git_root, destination=None),
            )
            request.inputs["test_overrides"] = {"codex_capability_snapshot": expected_snapshot}
            old_cwd = Path.cwd()
            os.chdir(git_root)
            try:
                with (
                    patch.dict(os.environ, {"HOME": str(fake_home), "USERPROFILE": str(fake_home)}),
                    patch.object(install, "codex_agent_state_matches", side_effect=change_before_match),
                ):
                    response = install.run_codex_agent_install(MUTATION_HELPERS["install-codex-agents"], request)
            finally:
                os.chdir(old_cwd)

            self.assert_response(response, "expected_failure", 1)
            self.assertFalse(response["data"]["rollback_succeeded"])
            self.assertTrue(response["data"]["writes_state"])
            self.assertEqual(changed_target.read_bytes(), concurrent_bytes)
            self.assertEqual((destination / f"{agent_names[0]}.toml").read_bytes(), prior[agent_names[0]])
            self.assertIn(
                f"{changed_name}.toml",
                response["data"]["routing"]["recovery_or_mutation"]["recovery_record"]["rollback_failures"],
            )

    def test_install_codex_agents_route_aware_rollback_preserves_concurrent_edit(self) -> None:
        from speckit_pro_runner.helpers import install
        from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

        tmp, git_root = self.temp_clean_git_repo()
        with tmp, tempfile.TemporaryDirectory() as home_tmp:
            fake_home = Path(home_tmp).resolve()
            manifest_path = self.write_valid_route_policy_manifest(git_root)
            expected_snapshot = routing_capability_snapshot()
            expected_snapshot["available_routes"] = ["required-primary", "required-fallback"]
            destination = fake_home / ".codex" / "agents"
            destination.mkdir(parents=True)
            agent_names = routing_required_agents()
            for name in agent_names:
                (destination / f"{name}.toml").write_bytes(f"prior {name}\n".encode("utf-8"))
            installed_then_changed = agent_names[0]
            failed_name = agent_names[1]
            changed_target = destination / f"{installed_then_changed}.toml"
            concurrent_bytes = b"concurrent user edit after installer write\n"
            real_write = install.write_codex_agent_atomic
            failed_once = False
            changed_once = False

            def fail_after_concurrent_edit(
                target: Path,
                content: bytes,
                target_dir: Path,
                identity: tuple[int, int] | None,
                *,
                mode: int | None = None,
                expected_state: object = None,
                cleanup_race_state: object = None,
            ) -> object:
                nonlocal failed_once, changed_once
                if target.name == f"{failed_name}.toml" and not failed_once:
                    failed_once = True
                    raise OSError("injected failure after concurrent edit")
                installed_state = real_write(
                    target,
                    content,
                    target_dir,
                    identity,
                    mode=mode,
                    expected_state=expected_state,
                    cleanup_race_state=cleanup_race_state,
                )
                if target == changed_target and not changed_once:
                    changed_once = True
                    changed_target.write_bytes(concurrent_bytes)
                return installed_state

            request = SimpleNamespace(
                request_id="test-route-aware-concurrent-rollback",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="apply",
                inputs=self.route_aware_inputs(manifest_path, git_root, destination=None),
            )
            request.inputs["test_overrides"] = {"codex_capability_snapshot": expected_snapshot}
            old_cwd = Path.cwd()
            os.chdir(git_root)
            try:
                with (
                    patch.dict(os.environ, {"HOME": str(fake_home), "USERPROFILE": str(fake_home)}),
                    patch.object(install, "write_codex_agent_atomic", side_effect=fail_after_concurrent_edit),
                ):
                    response = install.run_codex_agent_install(MUTATION_HELPERS["install-codex-agents"], request)
            finally:
                os.chdir(old_cwd)

            self.assert_response(response, "expected_failure", 1)
            self.assertFalse(response["data"]["rollback_succeeded"])
            self.assertTrue(response["data"]["writes_state"])
            self.assertEqual(changed_target.read_bytes(), concurrent_bytes)
            self.assertIn(
                f"{installed_then_changed}.toml",
                response["data"]["routing"]["recovery_or_mutation"]["recovery_record"]["rollback_failures"],
            )

    def test_install_codex_agents_route_aware_dry_run_omits_unavailable_helper_when_no_file_exists(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            manifest_path = self.write_valid_route_policy_manifest(git_root)
            expected_snapshot = routing_capability_snapshot()
            expected_snapshot["available_routes"] = ["required-primary", "required-fallback"]
            inputs = self.route_aware_inputs(manifest_path, git_root)
            inputs["test_overrides"] = {"codex_capability_snapshot": expected_snapshot}
            destination = git_root / ".codex" / "agents"

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", inputs=inputs),
                cwd=git_root,
            )

            self.assertEqual(completed.returncode, 0)
            self.assertEqual(stderr_records, [])
            self.assert_response(response, "ok", 0)
            self.assert_route_aware_snapshot_response(
                response,
                manifest_path=manifest_path,
                git_root=git_root,
                expected_snapshot=expected_snapshot,
            )
            self.assert_route_aware_required_resolution(response, expected_snapshot=expected_snapshot)
            self.assert_route_aware_helper_omitted_no_file(response, destination)
            self.assert_route_aware_no_mutation_yet(response)
            self.assertEqual(
                len(response["data"]["mutation"]["planned_operations"]),
                len(routing_required_agents()),
            )

    def test_install_codex_agents_route_aware_apply_omits_unavailable_helper_and_installs_required_roster(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            manifest_path = self.write_valid_route_policy_manifest(git_root)
            expected_snapshot = routing_capability_snapshot()
            expected_snapshot["available_routes"] = ["required-primary", "required-fallback"]
            inputs = self.route_aware_inputs(manifest_path, git_root)
            inputs["test_overrides"] = {"codex_capability_snapshot": expected_snapshot}
            destination = git_root / ".codex" / "agents"

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", mode="apply", inputs=inputs),
                cwd=git_root,
            )

            self.assertEqual(completed.returncode, 0)
            self.assertEqual(stderr_records, [])
            self.assert_response(response, "ok", 0)
            self.assert_route_aware_required_resolution(response, expected_snapshot=expected_snapshot)
            self.assert_route_aware_helper_omitted_no_file(response, destination)
            self.assert_route_aware_apply_mutation_evidence(response)
            self.assert_route_aware_required_destination_bytes(response, destination)
            self.assertEqual(
                len(response["data"]["mutation"]["applied_operations"]),
                len(routing_required_agents()),
            )

    def test_install_codex_agents_route_aware_rejects_caller_asserted_helper_provenance(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            manifest_path = self.write_valid_route_policy_manifest(git_root)
            expected_snapshot = routing_capability_snapshot()
            expected_snapshot["available_routes"] = ["required-primary", "required-fallback"]
            destination = git_root / ".codex" / "agents"
            destination.mkdir(parents=True)
            helper_path = destination / f"{routing_optional_helper()}.toml"
            helper_bytes = b"plugin managed helper\n"
            helper_path.write_bytes(helper_bytes)
            inputs = self.route_aware_inputs(manifest_path, git_root)
            inputs["test_overrides"] = {"codex_capability_snapshot": expected_snapshot}
            inputs["managed_helper_provenance"] = {
                "helper_name": routing_optional_helper(),
                "destination": ".codex/agents/autopilot-fast-helper.toml",
                "installer_id": "install-codex-agents",
                "source_roster_id": valid_route_policy_manifest()["source_roster"]["source_roster_id"],
                "manifest_id": valid_route_policy_manifest()["manifest_id"],
                "destination_digest": f"sha256:{hashlib.sha256(helper_bytes).hexdigest()}",
            }

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", inputs=inputs),
                cwd=git_root,
            )

            self.assertEqual(completed.returncode, 0)
            self.assertEqual(stderr_records, [])
            self.assert_response(response, "ok", 0)
            self.assert_route_aware_required_resolution(response, expected_snapshot=expected_snapshot)
            self.assert_route_aware_unmanaged_helper_preserved(response, destination)
            self.assert_route_aware_helper_preserved_without_removal(response, destination, helper_bytes)
            self.assertTrue(helper_path.exists())

    def test_install_codex_agents_route_aware_apply_removes_managed_helper_by_known_rendered_digest(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            manifest_path = self.write_valid_route_policy_manifest(git_root)
            expected_snapshot = routing_capability_snapshot()
            expected_snapshot["available_routes"] = ["required-primary", "required-fallback"]
            destination = git_root / ".codex" / "agents"
            destination.mkdir(parents=True)
            helper_path = destination / f"{routing_optional_helper()}.toml"
            helper_path.write_bytes(route_rendered_optional_helper_bytes())
            inputs = self.route_aware_inputs(manifest_path, git_root)
            inputs["test_overrides"] = {"codex_capability_snapshot": expected_snapshot}

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", mode="apply", inputs=inputs),
                cwd=git_root,
            )

            self.assertEqual(completed.returncode, 1)
            self.assert_response(response, "expected_failure", 1)
            cleanup_errors = response["diagnostics"][0]["details"]["cleanup_errors"]
            self.assertTrue(any(error["kind"] == "preserved_cleanup_entry" for error in cleanup_errors))
            self.assert_route_aware_required_resolution(response, expected_snapshot=expected_snapshot)
            self.assert_route_aware_managed_helper_removal(response, proof_status="known_rendered_digest")
            self.assertEqual(response["data"]["mutation"]["mutation_status"], "partial_failure")
            self.assert_route_aware_required_destination_bytes(response, destination)
            self.assertFalse(helper_path.exists())

    def test_install_codex_agents_route_aware_helper_removal_collision_fails_with_preserved_paths(self) -> None:
        from speckit_pro_runner.helpers import install
        from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            manifest_path = self.write_valid_route_policy_manifest(git_root)
            destination = git_root / ".codex" / "agents"
            initial_snapshot = routing_capability_snapshot()
            initial_request = SimpleNamespace(
                request_id="test-route-aware-helper-removal-collision-setup",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="apply",
                inputs=self.route_aware_inputs(manifest_path, git_root),
            )
            initial_request.inputs["test_overrides"] = {"codex_capability_snapshot": initial_snapshot}
            old_cwd = Path.cwd()
            os.chdir(git_root)
            try:
                initial_response = install.run_codex_agent_install(
                    MUTATION_HELPERS["install-codex-agents"],
                    initial_request,
                )
            finally:
                os.chdir(old_cwd)
            self.assert_response(initial_response, "ok", 0)

            helper_path = destination / f"{routing_optional_helper()}.toml"
            prior_helper = helper_path.read_bytes()
            required_only_snapshot = routing_capability_snapshot()
            required_only_snapshot["available_routes"] = ["required-primary", "required-fallback"]
            collision_request = SimpleNamespace(
                request_id="test-route-aware-helper-removal-collision",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="apply",
                inputs=self.route_aware_inputs(manifest_path, git_root),
            )
            collision_request.inputs["test_overrides"] = {"codex_capability_snapshot": required_only_snapshot}
            concurrent_helper = b"concurrent user helper\n"
            real_move = install.codex_agent_native_rename_no_replace
            injected = False

            def create_after_helper_move(directory_fd: int, source: str, backup: str) -> None:
                nonlocal injected
                real_move(directory_fd, source, backup)
                if source == helper_path.name and not injected:
                    injected = True
                    helper_path.write_bytes(concurrent_helper)

            os.chdir(git_root)
            try:
                with patch.object(install, "codex_agent_native_rename_no_replace", side_effect=create_after_helper_move):
                    response = install.run_codex_agent_install(
                        MUTATION_HELPERS["install-codex-agents"],
                        collision_request,
                    )
            finally:
                os.chdir(old_cwd)

            self.assert_response(response, "expected_failure", 1)
            self.assertEqual(response["data"]["mutation"]["failure_operation"]["kind"], "remove_file")
            self.assertEqual(helper_path.read_bytes(), concurrent_helper)
            backups = list(destination.glob(f".{helper_path.name}.*.bak"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), prior_helper)
            recovery = response["data"]["routing"]["recovery_or_mutation"]["recovery_record"]
            self.assertEqual(
                [error["target"] for error in recovery["cleanup_errors"] if error["kind"] == "preserved_concurrent_file"],
                [backups[0].resolve().as_posix(), helper_path.resolve().as_posix()],
            )
            self.assertIn("concurrent_file_preserved", [action["reason"] for action in recovery["manual_remediation"]])

    def test_install_codex_agents_route_aware_apply_preserves_unmanaged_same_name_helpers(self) -> None:
        rendered_helper = route_rendered_optional_helper_bytes()
        cases = [
            ("filename-only", b"same filename without TOML proof\n"),
            ("syntactic-toml", b'name = "autopilot-fast-helper"\nmodel = "user-owned-model"\n'),
            ("parsed-equivalent", b"# comment is not byte proof\n" + rendered_helper),
            (
                "normalized-content",
                rendered_helper.replace(
                    b'model = "gpt-5.3-codex-spark"\n',
                    b'model    =    "gpt-5.3-codex-spark"\n',
                    1,
                ),
            ),
            (
                "user-modified-same-name",
                b'name = "autopilot-fast-helper"\n'
                b'description = "User-owned helper with the same filename."\n'
                b'model = "gpt-5.3-codex-spark"\n'
                b'developer_instructions = """Do user-specific work only."""\n',
            ),
        ]
        for label, helper_bytes in cases:
            with self.subTest(label=label):
                tmp, git_root = self.temp_clean_git_repo()
                with tmp, tempfile.TemporaryDirectory() as home_tmp:
                    fake_home = Path(home_tmp).resolve()
                    manifest_path = self.write_valid_route_policy_manifest(git_root)
                    expected_snapshot = routing_capability_snapshot()
                    expected_snapshot["available_routes"] = ["required-primary", "required-fallback"]
                    destination = fake_home / ".codex" / "agents"
                    destination.mkdir(parents=True)
                    helper_path = destination / f"{routing_optional_helper()}.toml"
                    helper_path.write_bytes(helper_bytes)
                    inputs = self.route_aware_inputs(manifest_path, git_root, destination=None)
                    inputs["test_overrides"] = {"codex_capability_snapshot": expected_snapshot}
                    env = {"HOME": str(fake_home), "USERPROFILE": str(fake_home)}

                    completed, response, stderr_records = run_runner(
                        helper_request("install-codex-agents", mode="apply", inputs=inputs),
                        cwd=git_root,
                        env_overrides=env,
                    )

                    self.assertEqual(completed.returncode, 0)
                    self.assertEqual(stderr_records, [])
                    self.assert_response(response, "ok", 0)
                    self.assert_route_aware_required_resolution(response, expected_snapshot=expected_snapshot)
                    self.assert_route_aware_unmanaged_helper_preserved(response, destination)
                    self.assert_route_aware_apply_mutation_evidence(response)
                    self.assert_route_aware_required_destination_bytes(response, destination)
                    self.assert_route_aware_helper_preserved_without_removal(response, destination, helper_bytes)

    def test_install_codex_agents_strict_required_override_uses_one_tuple_per_required_agent(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            manifest_path = self.write_valid_route_policy_manifest(git_root)
            expected_snapshot = routing_capability_snapshot()
            expected_snapshot["available_routes"] = ["required-fallback", "helper-primary"]
            inputs = self.route_aware_inputs(manifest_path, git_root)
            inputs["strict_model_override"] = "gpt-5.4"
            inputs["test_overrides"] = {"codex_capability_snapshot": expected_snapshot}

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", inputs=inputs),
                cwd=git_root,
            )

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(stderr_records, [])
        self.assert_response(response, "ok", 0)
        self.assert_route_aware_snapshot_response(
            response,
            manifest_path=manifest_path,
            git_root=git_root,
            expected_snapshot=expected_snapshot,
        )
        self.assert_strict_required_override_evidence(response, model="gpt-5.4", expected_status="compatible")
        self.assert_route_aware_no_mutation_yet(response)

    def test_install_codex_agents_strict_required_override_miss_reports_all_required_without_writes(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            manifest = strict_override_required_miss_manifest()
            manifest_path = self.write_route_policy_manifest(git_root, manifest)
            expected_snapshot = routing_capability_snapshot()
            expected_snapshot["available_routes"] = ["required-fallback", "helper-primary"]
            inputs = self.route_aware_inputs(manifest_path, git_root)
            inputs["strict_model_override"] = "gpt-5.4"
            inputs["test_overrides"] = {"codex_capability_snapshot": expected_snapshot}
            destination = git_root / ".codex" / "agents"

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", mode="apply", inputs=inputs),
                cwd=git_root,
            )

            self.assertEqual(completed.returncode, 1)
            self.assertEqual([diag["code"] for diag in stderr_records], ["codex_strict_override_required_unresolved"])
            self.assert_response(response, "expected_failure", 1)
            self.assert_route_aware_snapshot_response(
                response,
                manifest_path=manifest_path,
                git_root=git_root,
                expected_snapshot=expected_snapshot,
                expected_manifest=manifest,
            )
            self.assert_strict_required_override_evidence(response, model="gpt-5.4", expected_status="incompatible")
            records = {record["agent_name"]: record for record in response["data"]["routing"]["required_agents"]}
            self.assertEqual(records["analyze-executor"]["terminal_outcome"], "unresolved")
            self.assertIsNone(records["analyze-executor"]["selected_route"])
            self.assertEqual(records["analyze-executor"]["attempted_routes"][0]["outcome"], "rejected")
            self.assertEqual(records["analyze-executor"]["attempted_routes"][0]["reason"], "strict_override_route_missing")
            self.assert_strict_required_override_zero_mutation(response)
            self.assertFalse(destination.exists())

    def test_install_codex_agents_route_aware_required_miss_preserves_fake_home_prior_state(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp, tempfile.TemporaryDirectory() as home_tmp:
            fake_home = Path(home_tmp).resolve()
            manifest_path = self.write_valid_route_policy_manifest(git_root)
            expected_snapshot = routing_capability_snapshot()
            expected_snapshot["available_routes"] = []
            destination = fake_home / ".codex" / "agents"
            destination.mkdir(parents=True)
            prior_agent_bytes = {
                agent_name: f"previous known-good {agent_name}\n".encode("utf-8")
                for agent_name in routing_required_agents()
            }
            for agent_name, content in prior_agent_bytes.items():
                (destination / f"{agent_name}.toml").write_bytes(content)
            inputs = self.route_aware_inputs(manifest_path, git_root, destination=None)
            inputs["test_overrides"] = {"codex_capability_snapshot": expected_snapshot}
            env = {"HOME": str(fake_home), "USERPROFILE": str(fake_home)}

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", mode="apply", inputs=inputs),
                cwd=git_root,
                env_overrides=env,
            )

            self.assertEqual(completed.returncode, 1)
            self.assertEqual([diag["code"] for diag in stderr_records], ["codex_route_required_agent_unresolved"])
            self.assert_response(response, "expected_failure", 1)
            self.assert_route_aware_snapshot_response(
                response,
                manifest_path=manifest_path,
                git_root=git_root,
                expected_snapshot=expected_snapshot,
            )
            self.assert_route_aware_required_miss_zero_mutation(
                response,
                expected_snapshot=expected_snapshot,
                prior_agent_bytes=prior_agent_bytes,
                destination=destination,
            )

    def test_install_codex_agents_strict_helper_override_installs_compatible_helper(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            manifest = strict_override_helper_compatible_manifest()
            manifest_path = self.write_route_policy_manifest(git_root, manifest)
            expected_snapshot = routing_capability_snapshot()
            expected_snapshot["available_routes"] = ["required-helper-compatible", "helper-primary"]
            inputs = self.route_aware_inputs(manifest_path, git_root)
            inputs["strict_model_override"] = "gpt-5.3-codex-spark"
            inputs["test_overrides"] = {"codex_capability_snapshot": expected_snapshot}

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", inputs=inputs),
                cwd=git_root,
            )

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(stderr_records, [])
        self.assert_response(response, "ok", 0)
        self.assert_route_aware_snapshot_response(
            response,
            manifest_path=manifest_path,
            git_root=git_root,
            expected_snapshot=expected_snapshot,
            expected_manifest=manifest,
        )
        self.assert_strict_helper_override_evidence(
            response,
            model="gpt-5.3-codex-spark",
            helper_status="compatible",
            helper_outcome="installed",
        )
        helper = response["data"]["routing"]["optional_helper_decision"]
        self.assertEqual(helper["selected_route"]["model"], "gpt-5.3-codex-spark")
        self.assertEqual(helper["selected_route"]["model_reasoning_effort"], "high")

    def test_install_codex_agents_strict_helper_override_uses_valid_no_helper_without_helper_fallback(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            manifest_path = self.write_valid_route_policy_manifest(git_root)
            expected_snapshot = routing_capability_snapshot()
            expected_snapshot["available_routes"] = ["required-fallback"]
            inputs = self.route_aware_inputs(manifest_path, git_root)
            inputs["strict_model_override"] = "gpt-5.4"
            inputs["test_overrides"] = {"codex_capability_snapshot": expected_snapshot}

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", inputs=inputs),
                cwd=git_root,
            )

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(stderr_records, [])
        self.assert_response(response, "ok", 0)
        self.assert_strict_required_override_evidence(response, model="gpt-5.4", expected_status="compatible")
        self.assert_strict_helper_override_evidence(
            response,
            model="gpt-5.4",
            helper_status="incompatible_no_helper",
            helper_outcome="omitted",
        )
        helper = response["data"]["routing"]["optional_helper_decision"]
        self.assertIsNone(helper["selected_route"])
        self.assertTrue(helper["no_helper_validation"]["selected"])
        self.assertEqual(helper["attempted_routes"][0]["reason"], "strict_override_route_missing")

    def test_install_codex_agents_strict_helper_override_invalid_no_helper_fails_before_mutation(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            manifest = strict_override_invalid_no_helper_manifest()
            manifest_path = self.write_route_policy_manifest(git_root, manifest)
            expected_snapshot = routing_capability_snapshot()
            expected_snapshot["available_routes"] = ["required-fallback"]
            inputs = self.route_aware_inputs(manifest_path, git_root)
            inputs["strict_model_override"] = "gpt-5.4"
            inputs["test_overrides"] = {"codex_capability_snapshot": expected_snapshot}
            destination = git_root / ".codex" / "agents"

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", mode="apply", inputs=inputs),
                cwd=git_root,
            )

            self.assertEqual(completed.returncode, 1)
            self.assertEqual([diag["code"] for diag in stderr_records], ["codex_strict_override_helper_unresolved"])
            self.assert_response(response, "expected_failure", 1)
            self.assert_route_aware_snapshot_response(
                response,
                manifest_path=manifest_path,
                git_root=git_root,
                expected_snapshot=expected_snapshot,
                expected_manifest=manifest,
            )
            self.assert_strict_required_override_evidence(response, model="gpt-5.4", expected_status="compatible")
            self.assert_strict_helper_override_evidence(
                response,
                model="gpt-5.4",
                helper_status="unresolved",
                helper_outcome="unresolved",
            )
            self.assert_strict_required_override_zero_mutation(response)
            self.assertFalse(destination.exists())

    def test_install_codex_agents_static_mode_does_not_capture_capability_snapshot(self) -> None:
        from speckit_pro_runner.helpers import install
        from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            request = SimpleNamespace(
                request_id="test-static-mode-skips-snapshot",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="dry_run",
                inputs={"destination": ".codex/agents", "model": "gpt-5.5"},
            )
            old_cwd = Path.cwd()
            os.chdir(git_root)
            try:
                with patch.object(install, "capture_codex_runtime_capabilities", side_effect=AssertionError("static mode captured capabilities")):
                    response = install.run_codex_agent_install(MUTATION_HELPERS["install-codex-agents"], request)
            finally:
                os.chdir(old_cwd)

        self.assert_response(response, "ok", 0)
        self.assertNotIn("routing", response["data"])
        self.assertEqual(response["data"]["agent_files"], list(install.CODEX_SOURCE_AGENT_TOML_NAMES))
        self.assertEqual(response["data"]["model"], "gpt-5.5")
        self.assertEqual(response["data"]["mutation"]["mutation_status"], "planned")
        self.assertEqual(len(response["data"]["mutation"]["planned_operations"]), 11)
        self.assertEqual(response["data"]["verification"], {"status": "planned", "matched_files": []})
        self.assertFalse(response["data"]["writes_state"])
        self.assertFalse(response["data"]["restart_required"])

    def test_unpromoted_helpers_fail_closed_before_dispatch_in_all_mutation_modes(self) -> None:
        cases = [
            (
                "install-curated-set",
                "deferred",
                {
                    "operations": [
                        {
                            "operation_id": "adversarial-generic-write",
                            "kind": "write_file",
                            "target": "generated/adversarial.md",
                            "content": "generic dispatch must not write\n",
                        }
                    ]
                },
            ),
            (
                "generate-uat-skeleton",
                "deferred",
                {
                    "output_path": "generated/adversarial.md",
                    "content": "PR-emission dispatch must not write\n",
                },
            ),
            (
                "detect-stack-manager-plan",
                "out_of_scope",
                {
                    "commands": [["gh", "pr", "create"]],
                    "output_path": "generated/adversarial.md",
                    "content": "out-of-scope dispatch must not write\n",
                },
            ),
        ]

        for helper_id, promotion_status, inputs in cases:
            for mode in ("dry_run", "apply"):
                with self.subTest(helper_id=helper_id, mode=mode):
                    tmp, git_root = self.temp_clean_git_repo()
                    with tmp:
                        target = git_root / "generated" / "adversarial.md"
                        completed, response, stderr_records = run_runner(
                            helper_request(helper_id, mode=mode, inputs=inputs),
                            cwd=git_root,
                        )

                        self.assertEqual(completed.returncode, 1)
                        self.assert_response(response, "expected_failure", 1)
                        self.assertEqual([diag["code"] for diag in stderr_records], ["helper_not_promoted"])
                        self.assertEqual(response["data"]["promotion_status"], promotion_status)
                        self.assertFalse(response["data"]["writes_state"])
                        mutation = response["data"]["mutation"]
                        self.assertEqual(mutation["mode"], mode)
                        self.assertEqual(mutation["mutation_status"], "blocked")
                        self.assertEqual(mutation["planned_operations"], [])
                        self.assertEqual(mutation["applied_operations"], [])
                        self.assertEqual(mutation["planned_paths"], [])
                        self.assertEqual(mutation["touched_paths"], [])
                        self.assertFalse(mutation["live_mutation"])
                        self.assertFalse(target.exists())

    def test_install_codex_agents_refreshes_stale_files_and_preserves_unrelated_agents(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            destination = git_root / ".codex" / "agents"
            destination.mkdir(parents=True)
            stale = destination / "analyze-executor.toml"
            unrelated = destination / "user-owned-agent.toml"
            stale.write_text("stale\n", encoding="utf-8")
            unrelated.write_text("user owned\n", encoding="utf-8")
            inputs = {"destination": ".codex/agents", "model": "gpt-5.5"}

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", inputs=inputs),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(stderr_records, [])
            self.assert_response(response, "ok", 0)
            self.assertEqual(response["data"]["mutation"]["mutation_status"], "planned")
            self.assertEqual(len(response["data"]["mutation"]["planned_operations"]), 11)
            self.assertEqual(stale.read_text(encoding="utf-8"), "stale\n")

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", mode="apply", inputs=inputs),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assert_response(response, "expected_failure", 1)
            self.assertEqual(response["data"]["mutation"]["mutation_status"], "partial_failure")
            cleanup_errors = response["diagnostics"][0]["details"]["cleanup_errors"]
            self.assertTrue(any(error["kind"] == "preserved_cleanup_entry" for error in cleanup_errors))
            self.assertTrue(response["data"]["writes_state"])
            self.assertTrue(response["data"]["restart_required"])
            self.assertEqual(response["data"]["verification"]["status"], "verified")
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "user owned\n")
            for source in sorted((PLUGIN_ROOT / "codex-agents").glob("*.toml")):
                self.assertEqual((destination / source.name).read_bytes(), source.read_bytes())

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", mode="apply", inputs=inputs),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(stderr_records, [])
            self.assert_response(response, "ok", 0)
            mutation = response["data"]["mutation"]
            self.assertEqual(mutation["mutation_status"], "no_op")
            self.assertEqual(mutation["planned_operations"], [])
            self.assertEqual(len(mutation["no_op_operations"]), 11)
            self.assertFalse(response["data"]["restart_required"])

    def test_install_codex_agents_defaults_to_fake_user_home_without_touching_real_home(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp, tempfile.TemporaryDirectory() as home_tmp:
            fake_home = Path(home_tmp).resolve()
            destination = fake_home / ".codex" / "agents"
            destination.mkdir(parents=True)
            unrelated = destination / "user-owned-agent.toml"
            unrelated.write_bytes(b"user owned\n")
            env = {"HOME": str(fake_home), "USERPROFILE": str(fake_home)}

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", mode="apply", inputs={"model": "gpt-5.5"}),
                cwd=git_root,
                env_overrides=env,
            )
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(stderr_records, [])
            self.assert_response(response, "ok", 0)
            self.assertEqual(response["data"]["destination"], destination.as_posix())
            self.assertTrue(response["data"]["restart_required"])
            self.assertEqual(unrelated.read_bytes(), b"user owned\n")
            for source in sorted((PLUGIN_ROOT / "codex-agents").glob("*.toml")):
                self.assertEqual((destination / source.name).read_bytes(), source.read_bytes())

            completed, response, stderr_records = run_runner(
                helper_request("install-codex-agents", mode="apply", inputs={"model": "gpt-5.5"}),
                cwd=git_root,
                env_overrides=env,
            )
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(stderr_records, [])
            self.assertEqual(response["data"]["mutation"]["mutation_status"], "no_op")
            self.assertFalse(response["data"]["restart_required"])

    def test_install_codex_agents_applies_strict_gpt_5_4_destination_rewrite(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            completed, response, stderr_records = run_runner(
                helper_request(
                    "install-codex-agents",
                    mode="apply",
                    inputs={"destination": ".codex/agents", "model": "gpt-5.4"},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(stderr_records, [])
            self.assert_response(response, "ok", 0)
            destination = (git_root / ".codex" / "agents").resolve()
            spark = (destination / "autopilot-fast-helper.toml").read_text(encoding="utf-8")
            self.assertIn('model = "gpt-5.3-codex-spark"', spark)
            for target in sorted(destination.glob("*.toml")):
                if target.name == "autopilot-fast-helper.toml":
                    continue
                self.assertIn('model = "gpt-5.4"', target.read_text(encoding="utf-8"), target.name)

    def test_install_codex_agents_rejects_invalid_model_and_incomplete_source_before_writes(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            destination = (git_root / ".codex" / "agents").resolve()
            completed, response, stderr_records = run_runner(
                helper_request(
                    "install-codex-agents",
                    mode="apply",
                    inputs={"destination": ".codex/agents", "model": "unsupported"},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["unsupported_codex_model"])
            self.assertFalse(destination.exists())

        with tempfile.TemporaryDirectory() as source_tmp:
            fake_plugin = Path(source_tmp) / "speckit-pro"
            shutil.copytree(PLUGIN_ROOT / "codex-agents", fake_plugin / "codex-agents")
            (fake_plugin / "codex-agents" / "uat-runbook-author.toml").unlink()
            request = SimpleNamespace(
                request_id="test-incomplete-codex-agent-source",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="dry_run",
                inputs={"destination": ".codex/agents", "model": "gpt-5.5"},
            )
            from speckit_pro_runner.helpers import install
            from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

            with patch.object(install, "codex_plugin_root", return_value=fake_plugin):
                response = install.run_codex_agent_install(MUTATION_HELPERS["install-codex-agents"], request)
            self.assertEqual(response["status"], "input_error")
            self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["incomplete_agent_bundle"])

        with tempfile.TemporaryDirectory() as source_tmp:
            fake_plugin = Path(source_tmp) / "speckit-pro"
            shutil.copytree(PLUGIN_ROOT / "codex-agents", fake_plugin / "codex-agents")
            analyze = fake_plugin / "codex-agents" / "analyze-executor.toml"
            analyze.write_text(
                analyze.read_text(encoding="utf-8").replace('model = "gpt-5.5"', "model = 'gpt-5.5'", 1),
                encoding="utf-8",
            )
            request = SimpleNamespace(
                request_id="test-noncanonical-codex-agent-model",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="dry_run",
                inputs={"destination": ".codex/agents", "model": "gpt-5.4"},
            )
            from speckit_pro_runner.helpers import install
            from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

            with patch.object(install, "codex_plugin_root", return_value=fake_plugin):
                response = install.run_codex_agent_install(MUTATION_HELPERS["install-codex-agents"], request)
            self.assertEqual(response["status"], "input_error")
            self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["unsafe_agent_bundle"])

    def test_install_codex_agents_rolls_back_failed_batch(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            destination = git_root / ".codex" / "agents"
            destination.mkdir(parents=True)
            destination = destination.resolve()
            stale = destination / "analyze-executor.toml"
            unrelated = destination / "user-owned-agent.toml"
            stale.write_bytes(b"stale\xff\n")
            stale.chmod(0o640)
            unrelated.write_bytes(b"user owned\n")
            request = SimpleNamespace(
                request_id="test-codex-agent-rollback",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="apply",
                inputs={"destination": ".codex/agents", "model": "gpt-5.5"},
            )
            from speckit_pro_runner.helpers import install
            from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

            with (
                patch.object(install, "codex_agent_destination", return_value=destination),
                patch.object(install, "write_codex_agent_atomic", side_effect=self.fail_on_autopilot_agent_write(install.write_codex_agent_atomic)),
            ):
                response = install.run_codex_agent_install(MUTATION_HELPERS["install-codex-agents"], request)

            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["codex_agent_install_failed"])
            self.assertFalse(response["data"]["rollback_succeeded"])
            self.assertTrue(response["data"]["writes_state"])
            self.assertTrue(response["data"]["restart_required"])
            cleanup_errors = response["diagnostics"][0]["details"]["cleanup_errors"]
            self.assertTrue(any(error["kind"] == "preserved_cleanup_entry" for error in cleanup_errors))
            self.assertEqual(stale.read_bytes(), b"stale\xff\n")
            self.assertEqual(stale.stat().st_mode & 0o7777, 0o640)
            self.assertEqual(unrelated.read_bytes(), b"user owned\n")
            self.assertEqual(sorted(path.name for path in destination.glob("*.toml")), ["analyze-executor.toml", "user-owned-agent.toml"])

    def test_install_codex_agents_mode_restore_fails_closed_without_fchmod(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp).resolve() / "agents"
            destination.mkdir()
            target = destination / "analyze-executor.toml"
            from speckit_pro_runner.helpers import install

            identity = install.codex_agent_destination_identity(destination)
            with patch.object(install.os, "fchmod", None):
                with self.assertRaisesRegex(OSError, "descriptor-based mode restoration"):
                    install.write_codex_agent_atomic(
                        target,
                        b"restored\n",
                        destination,
                        identity,
                        mode=0o640,
                    )

            self.assertFalse(target.exists())
            residue = list(destination.iterdir())
            self.assertEqual(len(residue), 1)
            self.assertTrue(residue[0].name.startswith(".analyze-executor.toml."))
            self.assertTrue(residue[0].name.endswith(".tmp"))
            self.assertEqual(residue[0].read_bytes(), b"restored\n")

    def test_install_codex_agents_snapshot_uses_open_descriptor_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp).resolve() / "analyze-executor.toml"
            target.write_bytes(b"existing\n")
            target.chmod(0o600)
            from speckit_pro_runner.helpers import install

            real_open = install.os.open

            def chmod_after_open(path: object, flags: int) -> int:
                descriptor = real_open(path, flags)
                Path(path).chmod(0o640)
                return descriptor

            with patch.object(install.os, "open", side_effect=chmod_after_open):
                state = install.codex_agent_previous_state(target)

            self.assertIsNotNone(state)
            assert state is not None
            self.assertEqual(state.content, b"existing\n")
            self.assertEqual(state.mode & 0o7777, 0o640)

    def test_install_codex_agents_rollback_never_chmods_swapped_symlink_target(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp, tempfile.TemporaryDirectory() as outside_tmp:
            destination = git_root / ".codex" / "agents"
            destination.mkdir(parents=True)
            destination = destination.resolve()
            stale = destination / "analyze-executor.toml"
            stale.write_bytes(b"stale\n")
            stale.chmod(0o640)
            outside = Path(outside_tmp).resolve() / "outside.toml"
            outside.write_bytes(b"outside\n")
            outside.chmod(0o600)
            outside_mode = outside.stat().st_mode & 0o7777
            request = SimpleNamespace(
                request_id="test-codex-agent-rollback-symlink-swap",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="apply",
                inputs={"destination": ".codex/agents", "model": "gpt-5.5"},
            )
            from speckit_pro_runner.helpers import install
            from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

            real_move = install.codex_agent_native_rename_no_replace
            move_count = 0

            def swap_after_rollback_move(directory_fd: int, source: str, backup: str) -> None:
                nonlocal move_count
                real_move(directory_fd, source, backup)
                if source == stale.name and backup.endswith(".bak"):
                    move_count += 1
                if move_count == 2 and not (destination / source).exists():
                    (destination / source).symlink_to(outside)

            with (
                patch.object(install, "codex_agent_destination", return_value=destination),
                patch.object(install, "write_codex_agent_atomic", side_effect=self.fail_on_autopilot_agent_write(install.write_codex_agent_atomic)),
                patch.object(install, "codex_agent_native_rename_no_replace", side_effect=swap_after_rollback_move),
            ):
                response = install.run_codex_agent_install(MUTATION_HELPERS["install-codex-agents"], request)

            self.assert_response(response, "expected_failure", 1)
            self.assertFalse(response["data"]["rollback_succeeded"])
            self.assertTrue(response["data"]["writes_state"])
            self.assertTrue(response["data"]["restart_required"])
            self.assertEqual(outside.read_bytes(), b"outside\n")
            self.assertEqual(outside.stat().st_mode & 0o7777, outside_mode)

    def test_install_codex_agents_rejects_non_codex_and_symlink_destinations(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            completed, response, stderr_records = run_runner(
                helper_request(
                    "install-codex-agents",
                    mode="apply",
                    inputs={"destination": "agents", "model": "gpt-5.5"},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["invalid_destination"])
            self.assertFalse((git_root / "agents").exists())

            with tempfile.TemporaryDirectory() as outside:
                codex_dir = git_root / ".codex"
                try:
                    codex_dir.symlink_to(Path(outside), target_is_directory=True)
                except OSError:
                    self.skipTest("symlink creation is unavailable")
                completed, response, stderr_records = run_runner(
                    helper_request(
                        "install-codex-agents",
                        mode="apply",
                        inputs={"destination": ".codex/agents", "model": "gpt-5.5"},
                    ),
                    cwd=git_root,
                )
                self.assertEqual(completed.returncode, 2)
                self.assert_response(response, "input_error", 2)
                self.assertEqual([diag["code"] for diag in stderr_records], ["unsafe_agent_destination"])
                self.assertEqual(list(Path(outside).iterdir()), [])

    def test_install_codex_agents_rejects_managed_leaf_symlink_before_writes(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp, tempfile.TemporaryDirectory() as outside_tmp:
            destination = git_root / ".codex" / "agents"
            destination.mkdir(parents=True)
            outside = Path(outside_tmp) / "outside.toml"
            outside.write_bytes(b"outside\xff\n")
            try:
                (destination / "analyze-executor.toml").symlink_to(outside)
            except OSError:
                self.skipTest("symlink creation is unavailable")

            completed, response, stderr_records = run_runner(
                helper_request(
                    "install-codex-agents",
                    mode="apply",
                    inputs={"destination": ".codex/agents", "model": "gpt-5.5"},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["unsafe_agent_destination"])
            self.assertEqual(outside.read_bytes(), b"outside\xff\n")
            self.assertEqual(sorted(path.name for path in destination.iterdir()), ["analyze-executor.toml"])

    def test_install_codex_agents_blocks_destination_identity_change(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            destination = git_root / ".codex" / "agents"
            destination.mkdir(parents=True)
            destination = destination.resolve()
            request = SimpleNamespace(
                request_id="test-codex-agent-destination-race",
                helper_id="install-codex-agents",
                operation="install-codex-agents",
                mode="apply",
                inputs={"destination": ".codex/agents", "model": "gpt-5.5"},
            )
            from speckit_pro_runner.helpers import install
            from speckit_pro_runner.helpers.registry import MUTATION_HELPERS

            real_identity = install.codex_agent_destination_identity(destination)
            changed_identity = (real_identity[0], real_identity[1] + 1)
            identities = [real_identity, changed_identity]

            def destination_identity_changes(_path: Path) -> tuple[int, int]:
                if identities:
                    return identities.pop(0)
                return changed_identity

            with (
                patch.object(install, "codex_agent_destination", return_value=destination),
                patch.object(install, "codex_agent_destination_identity", side_effect=destination_identity_changes),
            ):
                response = install.run_codex_agent_install(MUTATION_HELPERS["install-codex-agents"], request)

            self.assert_response(response, "expected_failure", 1)
            self.assertFalse(response["data"]["rollback_succeeded"])
            self.assertTrue(response["data"]["writes_state"])
            residue = list(destination.iterdir())
            self.assertEqual(len(residue), 1)
            self.assertTrue(residue[0].name.endswith(".cleanup-dir"))
            self.assertTrue(any(path.name.endswith(".tmp") for path in residue[0].iterdir()))

    def test_dry_run_reports_planned_write_without_mutating(self) -> None:
        tmp, target, rel = self.temp_repo_path("dry-run-output.json")
        with tmp:
            completed, response, stderr_records = run_runner(
                helper_request(
                    "mutation-foundation",
                    inputs={
                        "operations": [
                            {
                                "operation_id": "write-json",
                                "kind": "write_file",
                                "target": rel,
                                "content": "{\"ok\":true}\n",
                            }
                        ]
                    },
                )
            )
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(stderr_records, [])
            self.assert_response(response, "ok", 0)
            mutation = response["data"]["mutation"]
            self.assertEqual(mutation["mode"], "dry_run")
            self.assertEqual(mutation["mutation_status"], "planned")
            self.assertEqual(len(mutation["planned_operations"]), 1)
            self.assertEqual(mutation["applied_operations"], [])
            self.assertFalse(target.exists())

    def test_apply_writes_complete_file_with_final_newline(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            target = git_root / "generated" / "apply-output.md"
            rel = "generated/apply-output.md"
            completed, response, stderr_records = run_runner(
                helper_request(
                    "mutation-foundation",
                    mode="apply",
                    inputs={
                        "operations": [
                            {
                                "operation_id": "write-md",
                                "kind": "write_file",
                                "target": rel,
                                "content": "# Generated\n",
                            }
                        ]
                    },
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(stderr_records, [])
            self.assert_response(response, "ok", 0)
            self.assertEqual(target.read_text(encoding="utf-8"), "# Generated\n")
            mutation = response["data"]["mutation"]
            self.assertEqual(mutation["mutation_status"], "applied")
            self.assertEqual(len(mutation["applied_operations"]), 1)
            self.assertEqual(mutation["touched_paths"], [rel])

    def test_apply_rechecks_all_applied_targets_before_success(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            first = git_root / "generated" / "first.md"
            second = git_root / "generated" / "second.md"
            request = RunnerRequest(
                "test-final-applied-target-recheck",
                "mutation-foundation",
                "mutation-foundation",
                "apply",
                {
                    "operations": [
                        {
                            "operation_id": "write-first",
                            "kind": "write_file",
                            "target": "generated/first.md",
                            "content": "first\n",
                        },
                        {
                            "operation_id": "write-second",
                            "kind": "write_file",
                            "target": "generated/second.md",
                            "content": "second\n",
                        },
                    ]
                },
            )
            real_write = mutation.write_file_atomic

            def mutate_first_after_second(target: Path, content: str | bytes, **kwargs):
                result = real_write(target, content, **kwargs)
                if Path(target).name == second.name:
                    first.write_text("concurrent\n", encoding="utf-8")
                return result

            old_cwd = Path.cwd()
            os.chdir(git_root)
            try:
                with patch.object(mutation, "write_file_atomic", side_effect=mutate_first_after_second):
                    response = mutation.run_mutation_helper(registry.MUTATION_HELPERS["mutation-foundation"], request)
            finally:
                os.chdir(old_cwd)

            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["source_changed"])
            self.assertEqual(response["data"]["mutation"]["mutation_status"], "partial_failure")
            self.assertEqual(response["data"]["mutation"]["touched_paths"], ["generated/first.md", "generated/second.md"])
            self.assertEqual(first.read_text(encoding="utf-8"), "concurrent\n")
            self.assertFalse(second.exists())
            self.assertTrue(response["data"]["writes_state"])

    def test_apply_rejects_dirty_worktree_without_touching_target(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            (git_root / "untracked.txt").write_text("dirty\n", encoding="utf-8")
            target = git_root / "generated" / "dirty-output.md"
            rel = "generated/dirty-output.md"
            completed, response, stderr_records = run_runner(
                helper_request(
                    "mutation-foundation",
                    mode="apply",
                    inputs={
                        "operations": [{"operation_id": "dirty", "kind": "write_file", "target": rel, "content": "dirty\n"}],
                    },
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in stderr_records], ["dirty_worktree"])
            self.assertFalse(response["data"]["writes_state"])
            self.assertEqual(response["data"]["mutation"]["dirty_worktree"], True)
            self.assertFalse(target.exists())

    def test_apply_rechecks_dirty_worktree_after_lock_acquisition(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            target = git_root / "generated" / "locked-dirty.md"
            real_acquire = mutation.acquire_mutation_lock

            def dirty_after_lock(root: Path) -> mutation.MutationApplyLock:
                lock = real_acquire(root)
                (git_root / "concurrent-untracked.txt").write_text("dirty\n", encoding="utf-8")
                return lock

            request = RunnerRequest(
                "test-dirty-after-lock",
                "mutation-foundation",
                "mutation-foundation",
                "apply",
                {
                    "operations": [
                        {
                            "operation_id": "write-after-lock",
                            "kind": "write_file",
                            "target": "generated/locked-dirty.md",
                            "content": "blocked\n",
                        }
                    ]
                },
            )
            old_cwd = Path.cwd()
            os.chdir(git_root)
            try:
                with patch.object(mutation, "acquire_mutation_lock", side_effect=dirty_after_lock):
                    response = mutation.run_mutation_helper(registry.MUTATION_HELPERS["mutation-foundation"], request)
            finally:
                os.chdir(old_cwd)

            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["dirty_worktree"])
            self.assertEqual(response["data"]["mutation"]["dirty_worktree"], True)
            self.assertFalse(target.exists())

    def test_mutation_lock_does_not_write_to_untrusted_gitdir_file_target(self) -> None:
        from speckit_pro_runner.helpers import mutation

        with tempfile.TemporaryDirectory() as repo, tempfile.TemporaryDirectory() as external_gitdir:
            repo_root = Path(repo)
            external = Path(external_gitdir)
            (repo_root / ".git").write_text(f"gitdir: {external}\n", encoding="utf-8")

            lock = mutation.acquire_mutation_lock(repo_root)
            try:
                self.assertFalse((external / "speckit-pro-mutation.lock").exists())
                self.assertTrue(mutation.mutation_lock_path(repo_root).is_file())
            finally:
                lock.release()

    def test_mutation_lock_directory_can_be_reused_on_python_311(self) -> None:
        from speckit_pro_runner.helpers import mutation

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(mutation.tempfile, "gettempdir", return_value=tmp):
                first = mutation.mutation_lock_dir()
                second = mutation.mutation_lock_dir()

        self.assertEqual(first, second)

    def test_installed_cache_prefers_nearest_specify_root_over_ancestor_source_checkout(self) -> None:
        from speckit_pro_runner.helpers import read_only

        with tempfile.TemporaryDirectory() as tmp:
            source_root = Path(tmp) / "source"
            (source_root / "speckit-pro" / "speckit_pro_runner").mkdir(parents=True)
            worktree_root = source_root / ".worktrees" / "feature"
            (worktree_root / ".specify").mkdir(parents=True)

            self.assertEqual(read_only.find_repo_root(worktree_root), worktree_root.resolve(strict=False))

    def test_apply_rejects_when_git_status_cannot_prove_clean_worktree(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            target = git_root / "generated" / "status-error.md"
            completed, response, stderr_records = run_runner(
                helper_request(
                    "mutation-foundation",
                    mode="apply",
                    inputs={
                        "test_overrides": {"git_status_error": True},
                        "operations": [
                            {
                                "operation_id": "status-error",
                                "kind": "write_file",
                                "target": "generated/status-error.md",
                                "content": "blocked\n",
                            }
                        ],
                    },
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in stderr_records], ["git_status_unavailable"])
            self.assertFalse(response["data"]["writes_state"])
            self.assertEqual(response["data"]["mutation"]["dirty_worktree"], False)
            self.assertFalse(target.exists())

    def test_apply_no_op_succeeds_without_touching_dirty_worktree(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            (git_root / "untracked.txt").write_text("dirty\n", encoding="utf-8")
            completed, response, stderr_records = run_runner(
                helper_request("mutation-foundation", mode="apply", inputs={"operations": []}),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(stderr_records, [])
            self.assert_response(response, "ok", 0)
            mutation = response["data"]["mutation"]
            self.assertEqual(mutation["mutation_status"], "no_op")
            self.assertEqual(mutation["applied_operations"], [])
            self.assertEqual(mutation["touched_paths"], [])
            self.assertFalse(mutation["dirty_worktree"])

    def test_path_escape_and_symlink_targets_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as outside, tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as inside:
            outside_path = Path(outside) / "outside.md"
            outside_path.write_text("outside\n", encoding="utf-8")
            link = Path(inside) / "escape.md"
            try:
                link.symlink_to(outside_path)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            rel = link.relative_to(REPO_ROOT).as_posix()
            completed, response, stderr_records = run_runner(
                helper_request(
                    "mutation-foundation",
                    mode="apply",
                    inputs={"operations": [{"operation_id": "escape", "kind": "write_file", "target": rel, "content": "x\n"}]},
                )
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["unsupported_path"])

            completed, response, stderr_records = run_runner(
                helper_request(
                    "mutation-foundation",
                    mode="apply",
                    inputs={
                        "operations": [
                            {
                                "operation_id": "absolute-escape",
                                "kind": "write_file",
                                "target": str(outside_path),
                                "content": "x\n",
                            }
                        ]
                    },
                )
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["unsupported_path"])

    def test_preflight_rejects_parent_file_before_apply_writes(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            parent_file = git_root / "parent-is-file"
            parent_file.write_text("not a directory\n", encoding="utf-8")
            target = parent_file / "child.md"
            rel = "parent-is-file/child.md"
            completed, response, stderr_records = run_runner(
                helper_request(
                    "mutation-foundation",
                    mode="apply",
                    inputs={"operations": [{"operation_id": "write-failure", "kind": "write_file", "target": rel, "content": "x\n"}]},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["unsupported_path"])
            self.assertFalse(target.exists())

    def test_batch_write_conflicts_are_rejected_before_apply_writes(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            parent = git_root / "generated" / "parent.md"
            child = parent / "child.md"
            completed, response, stderr_records = run_runner(
                helper_request(
                    "mutation-foundation",
                    mode="apply",
                    inputs={
                        "operations": [
                            {
                                "operation_id": "parent",
                                "kind": "write_file",
                                "target": "generated/parent.md",
                                "content": "parent\n",
                            },
                            {
                                "operation_id": "child",
                                "kind": "write_file",
                                "target": "generated/parent.md/child.md",
                                "content": "child\n",
                            },
                        ]
                    },
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["conflicting_operations"])
            self.assertFalse(parent.exists())
            self.assertFalse(child.exists())

            completed, response, stderr_records = run_runner(
                helper_request(
                    "mutation-foundation",
                    mode="apply",
                    inputs={
                        "operations": [
                            {
                                "operation_id": "same-id",
                                "kind": "write_file",
                                "target": "generated/parent.md",
                                "content": "parent\n",
                            },
                            {
                                "operation_id": "same-id",
                                "kind": "write_file",
                                "target": "generated/parent.md/child.md",
                                "content": "child\n",
                            },
                        ]
                    },
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["invalid_input"])
            self.assertFalse(parent.exists())
            self.assertFalse(child.exists())

    def test_partial_failure_reports_applied_operation_and_manual_remediation(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            first = git_root / "nested" / "new" / "first.md"
            second = git_root / "second.md"
            first_rel = "nested/new/first.md"
            second_rel = "second.md"
            completed, response, stderr_records = run_runner(
                helper_request(
                    "mutation-foundation",
                    mode="apply",
                    inputs={
                        "simulate_failure_after": 1,
                        "operations": [
                            {"operation_id": "first", "kind": "write_file", "target": first_rel, "content": "first\n"},
                            {"operation_id": "second", "kind": "write_file", "target": second_rel, "content": "second\n"},
                        ],
                    },
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in stderr_records], ["partial_failure"])
            mutation = response["data"]["mutation"]
            self.assertEqual([op["operation_id"] for op in mutation["applied_operations"]], ["first"])
            self.assertEqual(mutation["failure_operation"]["operation_id"], "second")
            self.assertTrue(mutation["manual_remediation"])
            self.assertTrue(mutation["live_mutation"])
            self.assertFalse(response["data"]["writes_state"])
            self.assertFalse(first.exists())
            self.assertFalse(second.exists())
            self.assertFalse((git_root / "nested").exists())

    def test_apply_write_preserves_existing_file_mode_and_rechecks_source_fingerprints(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            source = git_root / "source.md"
            source.write_text("source\n", encoding="utf-8")
            target = git_root / "tool.sh"
            target.write_text("#!/bin/sh\n", encoding="utf-8")
            target.chmod(0o755)
            self.run_git(git_root, "add", "source.md", "tool.sh")
            self.run_git(git_root, "commit", "--quiet", "-m", "sources")

            completed, response, stderr_records = run_runner(
                helper_request(
                    "mutation-foundation",
                    mode="apply",
                    inputs={
                        "operations": [
                            {
                                "operation_id": "update-target",
                                "kind": "write_file",
                                "target": "tool.sh",
                                "content": "#!/bin/sh\necho updated\n",
                                "source_fingerprints": {
                                    "source": {
                                        "path": "source.md",
                                        "algorithm": "sha256",
                                        "sha256": "0" * 64,
                                        "size_bytes": 999,
                                    }
                                },
                            }
                        ]
                    },
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in stderr_records], ["source_changed"])
            self.assertEqual(target.read_text(encoding="utf-8"), "#!/bin/sh\n")

            source_bytes = source.read_bytes()
            completed, response, stderr_records = run_runner(
                helper_request(
                    "mutation-foundation",
                    mode="apply",
                    inputs={
                        "operations": [
                            {
                                "operation_id": "update-target",
                                "kind": "write_file",
                                "target": "tool.sh",
                                "content": "#!/bin/sh\necho updated\n",
                                "source_fingerprints": {
                                    "source": {
                                        "path": "source.md",
                                        "algorithm": "sha256",
                                        "sha256": hashlib.sha256(source_bytes).hexdigest(),
                                        "size_bytes": len(source_bytes),
                                    }
                                },
                            }
                        ]
                    },
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok", 0)
            self.assertEqual(stderr_records, [])
            self.assertEqual(os.stat(target).st_mode & 0o777, 0o755)
            self.assertTrue(response["data"]["mutation"]["live_mutation"])

    @unittest.skipIf(os.name == "nt", "POSIX umask behavior is not portable to Windows")
    def test_apply_write_respects_umask_for_new_files(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            target = git_root / "new.md"
            old_umask = os.umask(0o077)
            try:
                completed, response, stderr_records = run_runner(
                    helper_request(
                        "mutation-foundation",
                        mode="apply",
                        inputs={
                            "operations": [
                                {
                                    "operation_id": "new-file",
                                    "kind": "write_file",
                                    "target": "new.md",
                                    "content": "created\n",
                                }
                            ]
                        },
                    ),
                    cwd=git_root,
                )
            finally:
                os.umask(old_umask)

            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok", 0)
            self.assertEqual(stderr_records, [])
            self.assertEqual(os.stat(target).st_mode & 0o777, 0o600)

    def test_apply_rechecks_source_fingerprints_after_write_and_rolls_back(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            source = git_root / "source.md"
            source.write_text("source\n", encoding="utf-8")
            self.run_git(git_root, "add", "source.md")
            self.run_git(git_root, "commit", "--quiet", "-m", "source")
            source_bytes = source.read_bytes()
            request = RunnerRequest(
                "test-post-write-source-recheck",
                "mutation-foundation",
                "mutation-foundation",
                "apply",
                {
                    "operations": [
                        {
                            "operation_id": "write-validation",
                            "kind": "write_file",
                            "target": "validation.json",
                            "content": "{}\n",
                            "source_fingerprints": {
                                "packet": {
                                    "path": "source.md",
                                    "algorithm": "sha256",
                                    "sha256": hashlib.sha256(source_bytes).hexdigest(),
                                    "size_bytes": len(source_bytes),
                                }
                            },
                        }
                    ]
                },
            )
            real_write = mutation.write_file_atomic

            def mutate_source_after_write(
                target: Path,
                content: str,
                *,
                trust_root: Path | None = None,
                expected_snapshot: dict[str, object] | None = None,
            ) -> dict[str, object]:
                result = real_write(target, content, trust_root=trust_root, expected_snapshot=expected_snapshot)
                source.write_text("changed\n", encoding="utf-8")
                return result

            old_cwd = Path.cwd()
            os.chdir(git_root)
            try:
                with patch.object(mutation, "write_file_atomic", side_effect=mutate_source_after_write):
                    response = mutation.run_mutation_helper(registry.MUTATION_HELPERS["mutation-foundation"], request)
            finally:
                os.chdir(old_cwd)

            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["source_changed"])
            self.assertFalse((git_root / "validation.json").exists())
            self.assertTrue(response["data"]["mutation"]["live_mutation"])
            self.assertFalse(response["data"]["writes_state"])

    def test_post_write_snapshot_rejects_concurrent_replacement(self) -> None:
        from speckit_pro_runner.helpers import mutation

        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            git_root = git_root.resolve()
            target = git_root / "target.md"
            snapshots = {"target.md": mutation.snapshot_write_target(target, git_root)}
            write_result = mutation.write_file_atomic(target, "applied\n", trust_root=git_root)
            target.write_text("concurrent\n", encoding="utf-8")

            diag = mutation.snapshot_changed_diagnostic_after_write(
                "target.md",
                target,
                snapshots,
                git_root,
                expected_digest=str(write_result["digest"]),
                expected_mode=write_result["mode"],
            )
            errors = mutation.rollback_applied_writes(["target.md"], snapshots, git_root)

            self.assertIsNotNone(diag)
            self.assertEqual(diag["code"], "source_changed")
            self.assertEqual(errors, ["target.md:source_changed"])
            self.assertEqual(target.read_text(encoding="utf-8"), "concurrent\n")

    def test_rollback_preserves_parent_created_after_snapshot(self) -> None:
        from speckit_pro_runner.helpers import mutation

        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            git_root = git_root.resolve()
            parent = git_root / "nested"
            target = parent / "new.md"
            snapshots = {"nested/new.md": mutation.snapshot_write_target(target, git_root)}
            self.assertEqual(snapshots["nested/new.md"]["created_parent_dirs"], ["nested"])
            parent.mkdir()

            write_result = mutation.write_file_atomic(
                target,
                "applied\n",
                trust_root=git_root,
                expected_snapshot=snapshots["nested/new.md"],
            )
            diag = mutation.snapshot_changed_diagnostic_after_write(
                "nested/new.md",
                target,
                snapshots,
                git_root,
                expected_digest=str(write_result["digest"]),
                expected_mode=write_result["mode"],
                expected_created_parent_dirs=write_result["created_parent_dirs"],
            )
            errors = mutation.rollback_applied_writes(["nested/new.md"], snapshots, git_root)

            self.assertIsNone(diag)
            self.assertEqual(write_result["created_parent_dirs"], [])
            self.assertEqual(errors, [])
            self.assertFalse(target.exists())
            self.assertTrue(parent.is_dir())

    def test_apply_tracks_successful_write_when_final_parent_close_fails(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            request = RunnerRequest(
                "test-final-parent-close-after-replace",
                "mutation-foundation",
                "mutation-foundation",
                "apply",
                {
                    "operations": [
                        {
                            "operation_id": "write-new",
                            "kind": "write_file",
                            "target": "new.md",
                            "content": "new\n",
                        }
                    ]
                },
            )
            real_replace = mutation.os.replace
            real_close = mutation.os.close
            replace_seen = False
            failed_fd: int | None = None

            def tracking_replace(*args, **kwargs):
                nonlocal replace_seen
                result = real_replace(*args, **kwargs)
                replace_seen = True
                return result

            def fail_first_close_after_replace(fd: int) -> None:
                nonlocal failed_fd
                if replace_seen and failed_fd is None:
                    failed_fd = fd
                    raise OSError("injected close failure")
                real_close(fd)

            old_cwd = Path.cwd()
            os.chdir(git_root)
            try:
                with (
                    patch.object(mutation.os, "replace", side_effect=tracking_replace),
                    patch.object(mutation.os, "close", side_effect=fail_first_close_after_replace),
                ):
                    response = mutation.run_mutation_helper(registry.MUTATION_HELPERS["mutation-foundation"], request)
            finally:
                os.chdir(old_cwd)
                if failed_fd is not None:
                    try:
                        real_close(failed_fd)
                    except OSError:
                        pass

            self.assert_response(response, "ok", 0)
            self.assertEqual(response["data"]["mutation"]["applied_operations"][0]["operation_id"], "write-new")
            self.assertEqual(response["data"]["mutation"]["touched_paths"], ["new.md"])
            self.assertTrue(response["data"]["writes_state"])
            self.assertEqual((git_root / "new.md").read_text(encoding="utf-8"), "new\n")

    def test_apply_cleans_parent_created_before_traversal_failure(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            request = RunnerRequest(
                "test-created-parent-traversal-failure",
                "mutation-foundation",
                "mutation-foundation",
                "apply",
                {
                    "operations": [
                        {
                            "operation_id": "write-new",
                            "kind": "write_file",
                            "target": "nested/new.md",
                            "content": "new\n",
                        }
                    ]
                },
            )
            real_open = mutation.os.open

            def fail_reopen_created_parent(path, *args, **kwargs):
                if path == "nested" and (git_root / "nested").exists():
                    raise OSError("injected parent traversal failure")
                return real_open(path, *args, **kwargs)

            old_cwd = Path.cwd()
            os.chdir(git_root)
            try:
                with patch.object(mutation.os, "open", side_effect=fail_reopen_created_parent):
                    response = mutation.run_mutation_helper(registry.MUTATION_HELPERS["mutation-foundation"], request)
            finally:
                os.chdir(old_cwd)

            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["write_failure"])
            self.assertFalse((git_root / "nested").exists())
            self.assertFalse(response["data"]["writes_state"])

    def test_apply_reports_temp_unlink_failure_after_failed_replace(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            request = RunnerRequest(
                "test-temp-unlink-cleanup-failure",
                "mutation-foundation",
                "mutation-foundation",
                "apply",
                {
                    "operations": [
                        {
                            "operation_id": "write-new",
                            "kind": "write_file",
                            "target": "new.md",
                            "content": "new\n",
                        }
                    ]
                },
            )
            real_unlink = mutation.os.unlink

            def fail_replace(*args, **kwargs):
                raise OSError("injected replace failure")

            def fail_temp_unlink(path, *args, **kwargs):
                if isinstance(path, str) and path.startswith(".new.md.tmp-"):
                    raise OSError("injected temp cleanup failure")
                return real_unlink(path, *args, **kwargs)

            old_cwd = Path.cwd()
            os.chdir(git_root)
            try:
                with (
                    patch.object(mutation.os, "replace", side_effect=fail_replace),
                    patch.object(mutation.os, "unlink", side_effect=fail_temp_unlink),
                ):
                    response = mutation.run_mutation_helper(registry.MUTATION_HELPERS["mutation-foundation"], request)
            finally:
                os.chdir(old_cwd)

            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["write_failure"])
            self.assertTrue(any(error.endswith(":OSError") for error in response["diagnostics"][0]["details"]["rollback_errors"]))
            self.assertTrue(response["data"]["writes_state"])
            self.assertEqual(len(list(git_root.glob(".new.md.tmp-*"))), 1)
            self.assertFalse((git_root / "new.md").exists())

    def test_apply_rejects_target_swap_between_snapshot_and_replace(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            target = git_root / "target.md"
            target.write_text("original\n", encoding="utf-8")
            self.run_git(git_root, "add", "target.md")
            self.run_git(git_root, "commit", "--quiet", "-m", "target")
            calls = 0
            real_ensure = mutation.ensure_safe_write_target_fd

            def swap_before_final_guard(parent_fd: int, name: str) -> None:
                nonlocal calls
                calls += 1
                if calls == 2:
                    target.write_text("concurrent\n", encoding="utf-8")
                real_ensure(parent_fd, name)

            request = RunnerRequest(
                "test-target-swap-before-replace",
                "mutation-foundation",
                "mutation-foundation",
                "apply",
                {
                    "operations": [
                        {
                            "operation_id": "update-target",
                            "kind": "write_file",
                            "target": "target.md",
                            "content": "updated\n",
                        }
                    ]
                },
            )
            old_cwd = Path.cwd()
            os.chdir(git_root)
            try:
                with patch.object(mutation, "ensure_safe_write_target_fd", side_effect=swap_before_final_guard):
                    response = mutation.run_mutation_helper(registry.MUTATION_HELPERS["mutation-foundation"], request)
            finally:
                os.chdir(old_cwd)

            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["source_changed"])
            self.assertEqual(target.read_text(encoding="utf-8"), "concurrent\n")
            self.assertFalse(response["data"]["mutation"]["live_mutation"])
            self.assertFalse(response["data"]["writes_state"])

    def test_write_failure_cleanup_errors_mark_writes_state(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            request = RunnerRequest(
                "test-cleanup-errors",
                "mutation-foundation",
                "mutation-foundation",
                "apply",
                {
                    "operations": [
                        {
                            "operation_id": "write-new",
                            "kind": "write_file",
                            "target": "nested/new.md",
                            "content": "new\n",
                        }
                    ]
                },
            )
            injected = OSError("injected")
            setattr(injected, "cleanup_errors", ["nested:OSError"])

            old_cwd = Path.cwd()
            os.chdir(git_root)
            try:
                with patch.object(mutation, "write_file_atomic", side_effect=injected):
                    response = mutation.run_mutation_helper(registry.MUTATION_HELPERS["mutation-foundation"], request)
            finally:
                os.chdir(old_cwd)

            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["write_failure"])
            self.assertEqual(response["diagnostics"][0]["details"]["rollback_errors"], ["nested:OSError"])
            self.assertTrue(response["data"]["mutation"]["live_mutation"])
            self.assertTrue(response["data"]["writes_state"])

    def test_apply_file_writes_fail_closed_on_unsupported_descriptor_platform(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            request = RunnerRequest(
                "test-unsupported-platform",
                "mutation-foundation",
                "mutation-foundation",
                "apply",
                {
                    "operations": [
                        {
                            "operation_id": "write-new",
                            "kind": "write_file",
                            "target": "new.md",
                            "content": "new\n",
                        }
                    ]
                },
            )
            old_cwd = Path.cwd()
            os.chdir(git_root)
            try:
                with patch.object(mutation, "descriptor_mutation_supported", return_value=False):
                    response = mutation.run_mutation_helper(registry.MUTATION_HELPERS["mutation-foundation"], request)
            finally:
                os.chdir(old_cwd)

            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in response["diagnostics"]], ["unsupported_platform"])
            self.assertFalse(response["data"]["mutation"]["live_mutation"])
            self.assertFalse(response["data"]["writes_state"])
            self.assertFalse((git_root / "new.md").exists())

    def test_rollback_refuses_concurrent_edits_and_reports_directory_cleanup_errors(self) -> None:
        from speckit_pro_runner.helpers import mutation

        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            git_root = git_root.resolve()
            target = git_root / "existing.md"
            target.write_text("original\n", encoding="utf-8")
            snapshots = {"existing.md": mutation.snapshot_write_target(target, git_root)}
            mutation.write_file_atomic(target, "applied\n", trust_root=git_root)
            applied = mutation.snapshot_write_target(target, git_root)
            snapshots["existing.md"]["applied_digest"] = applied["digest"]
            snapshots["existing.md"]["applied_mode"] = applied["mode"]
            target.write_text("concurrent\n", encoding="utf-8")

            errors = mutation.rollback_applied_writes(["existing.md"], snapshots, git_root)

            self.assertEqual(errors, ["existing.md:source_changed"])
            self.assertEqual(target.read_text(encoding="utf-8"), "concurrent\n")

            residual_dir = git_root / "nested" / "created"
            residual_dir.mkdir(parents=True)
            (residual_dir / "residual.txt").write_text("leftover\n", encoding="utf-8")
            cleanup_errors = mutation.remove_created_parent_dirs(["nested", "nested/created"], git_root)
            self.assertEqual(cleanup_errors, ["nested/created:OSError", "nested:OSError"])

            with tempfile.TemporaryDirectory() as outside:
                outside_root = Path(outside)
                outside_created = outside_root / "created"
                outside_created.mkdir()
                swapped = git_root / "swapped"
                try:
                    swapped.symlink_to(outside_root, target_is_directory=True)
                except (OSError, NotImplementedError):
                    self.skipTest("symlink creation is unavailable")
                cleanup_errors = mutation.remove_created_parent_dirs(["swapped", "swapped/created"], git_root)
                self.assertTrue(outside_created.is_dir())
                self.assertTrue(any(error.startswith("swapped/created:") for error in cleanup_errors))

    def test_doctor_preflight_detects_missing_files_and_repair_uses_fake_home(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            install_root = git_root / "tests" / "speckit-pro" / "unit" / "fixtures" / "fake-home"
            root_rel = install_root.relative_to(git_root).as_posix()
            inventory = {
                "files": [
                    {"path": "agents/a.md", "content": "agent\n", "sha256": "skip"},
                    {"path": "runner/runner.py", "content": "runner\n", "sha256": "skip"},
                ]
            }
            completed, response, stderr_records = run_runner(
                helper_request(
                    "doctor-preflight",
                    mode="read_only",
                    inputs={"install_root": root_rel, "inventory": inventory, "fake_home": True},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok", 0)
            self.assertEqual(stderr_records, [])
            doctor = response["data"]["doctor"]
            self.assertEqual(doctor["status"], "safe_repair")
            self.assertEqual(len(doctor["missing_files"]), 2)

            completed, response, stderr_records = run_runner(
                helper_request(
                    "doctor-repair",
                    mode="apply",
                    inputs={"install_root": root_rel, "inventory": inventory, "fake_home": True},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok", 0)
            self.assertEqual(stderr_records, [])
            self.assertTrue((install_root / "agents" / "a.md").is_file())
            self.assertTrue((install_root / "runner" / "runner.py").is_file())

            completed, response, stderr_records = run_runner(
                helper_request(
                    "doctor-preflight",
                    mode="read_only",
                    inputs={"install_root": root_rel, "inventory": inventory, "fake_home": True},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok", 0)
            self.assertEqual(stderr_records, [])
            self.assertEqual(response["data"]["doctor"]["status"], "complete")

            completed, response, stderr_records = run_runner(
                helper_request(
                    "doctor-preflight",
                    mode="read_only",
                    inputs={"install_root": root_rel, "inventory": {"files": "bad"}, "fake_home": True},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["malformed_inventory"])

    def test_doctor_repair_refuses_non_fake_home(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            install_root = git_root / "tests" / "speckit-pro" / "unit" / "fixtures" / "fake-home"
            completed, response, stderr_records = run_runner(
                helper_request(
                    "doctor-repair",
                    mode="apply",
                    inputs={"install_root": install_root.relative_to(git_root).as_posix(), "inventory": {"files": []}},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["real_home_refused"])

    def test_doctor_repair_rejects_fake_home_outside_fixture_boundary(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            completed, response, stderr_records = run_runner(
                helper_request(
                    "doctor-repair",
                    mode="apply",
                    inputs={"install_root": "speckit-pro", "inventory": {"files": []}, "fake_home": True},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["fake_home_boundary_refused"])

    def test_doctor_repair_rejects_backslash_traversal_inventory_path(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            install_root = git_root / "tests" / "speckit-pro" / "unit" / "fixtures" / "fake-home"
            completed, response, stderr_records = run_runner(
                helper_request(
                    "doctor-repair",
                    mode="apply",
                    inputs={
                        "install_root": install_root.relative_to(git_root).as_posix(),
                        "inventory": {
                            "files": [
                                {
                                    "path": "..\\escaped.md",
                                    "content": "escape\n",
                                    "sha256": "skip",
                                }
                            ]
                        },
                        "fake_home": True,
                    },
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 2)
            self.assert_response(response, "input_error", 2)
            self.assertEqual([diag["code"] for diag in stderr_records], ["malformed_inventory"])
            self.assertFalse((git_root / "tests" / "speckit-pro" / "unit" / "fixtures" / "escaped.md").exists())

    def test_pr_emission_apply_writes_generated_body_and_command_plans_do_not_execute_gh(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            target = git_root / "generated" / "pr-body.md"
            rel = "generated/pr-body.md"
            completed, response, stderr_records = run_runner(
                helper_request(
                    "generate-pr-body",
                    mode="apply",
                    inputs={"output_path": rel, "title": "feat(XPLAT-006): helper port", "sections": ["Summary", "Verification"]},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok", 0)
            self.assertEqual(stderr_records, [])
            text = target.read_text(encoding="utf-8")
            self.assertIn("# feat(XPLAT-006): helper port", text)
            self.assertTrue(text.endswith("\n"))

            completed, response, stderr_records = run_runner(
                helper_request(
                    "multi-pr-emission",
                    inputs={"commands": [["gh", "pr", "create", "--draft"]], "live_mutation_approved": False},
                )
            )
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok", 0)
            self.assertEqual(stderr_records, [])
            mutation = response["data"]["mutation"]
            self.assertEqual(mutation["mutation_status"], "planned")
            self.assertEqual(mutation["applied_operations"], [])
            self.assertFalse(mutation["live_mutation"])

            completed, response, stderr_records = run_runner(
                helper_request(
                    "multi-pr-emission",
                    mode="apply",
                    inputs={"commands": [["gh", "pr", "create", "--draft"]], "live_mutation_approved": True},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in stderr_records], ["deferred_live_mutation"])
            mutation = response["data"]["mutation"]
            self.assertEqual(mutation["mutation_status"], "blocked")
            self.assertEqual(mutation["applied_operations"], [])
            self.assertFalse(mutation["live_mutation"])

            completed, response, stderr_records = run_runner(
                helper_request("generate-uat-skeleton", mode="apply", inputs={}),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in stderr_records], ["helper_not_promoted"])
            mutation = response["data"]["mutation"]
            self.assertEqual(mutation["mutation_status"], "blocked")
            self.assertEqual(mutation["applied_operations"], [])
            self.assertFalse(mutation["live_mutation"])

    def test_pr_packet_output_apply_emits_valid_packet_and_body_then_persists_validation(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            inputs = {
                "packet_path": "specs/prsg-999-packet/.process/pr-packets/prsg-999.json",
                "body_file": "specs/prsg-999-packet/.process/pr-packets/prsg-999/body.md",
                "validation_result_path": "specs/prsg-999-packet/.process/pr-packets/prsg-999/validation.json",
                "source_feature_dir": "specs/prsg-999-packet",
                "target": {"base_branch": "main", "head_branch": "agent/prsg-999-packet"},
                "title_type": "feat",
                "title_scope": "PRSG-999",
                "title_description": "Generate reviewer packet",
                "changed_files": ["specs/prsg-999-packet/spec.md"],
                "verification": ["python3 tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py passed"],
                "summary": "Adds a generated reviewer packet for a completed SpecKit workflow.",
                "what_changed": ["Writes the PR body.", "Writes the PR packet JSON.", "Declares the validation result path."],
                "why_it_matters": "Autopilot can continue to PR creation without inventing packet metadata.",
                "how_to_review": ["Inspect the emitted packet.", "Run validate-pr-packet-read-only."],
                "how_to_uat": "No manual UAT is required for this fixture.",
                "known_gaps": ["No known gaps for this fixture."],
                "non_goals": ["No live GitHub PR mutation is performed by this helper."],
            }

            completed, response, stderr_records = run_runner(
                helper_request("pr-packet-output", mode="apply", inputs=inputs),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok", 0)
            self.assertEqual(stderr_records, [])
            mutation = response["data"]["mutation"]
            self.assertEqual(mutation["mutation_status"], "applied")
            self.assertTrue(mutation["live_mutation"])
            self.assertEqual(
                mutation["touched_paths"],
                [inputs["body_file"], inputs["packet_path"]],
            )

            packet_path = git_root / inputs["packet_path"]
            body_path = git_root / inputs["body_file"]
            validation_path = git_root / inputs["validation_result_path"]
            self.assertTrue(packet_path.is_file())
            self.assertTrue(body_path.is_file())
            self.assertFalse(validation_path.exists())
            self.assertIn("## Summary", body_path.read_text(encoding="utf-8"))
            self.assertIn("## UAT Runbook", body_path.read_text(encoding="utf-8"))
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            self.assertEqual(packet["packet_id"], "prsg-999")
            self.assertEqual(packet["generated_title"]["value"], "feat(PRSG-999): Generate reviewer packet")
            self.assertEqual(packet["target"], inputs["target"])

            completed, response, stderr_records = run_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    mode="read_only",
                    inputs={"packet_path": inputs["packet_path"]},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok", 0)
            self.assertEqual(stderr_records, [])
            validation_result = response["data"]["stdout_json"]
            self.assertEqual(validation_result["status"], "passed")
            self.assertFalse(validation_result["pr_blocked"])
            self.assertIn("source_fingerprints", validation_result)
            self.assertEqual(set(validation_result["source_fingerprints"]), {"body", "packet"})
            packet["validation_result"] = validation_result
            packet_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            completed, response, stderr_records = run_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    mode="read_only",
                    inputs={"packet_path": inputs["packet_path"]},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok", 0)
            self.assertEqual(stderr_records, [])

            completed, response, stderr_records = run_runner(
                helper_request(
                    "validate-pr-packet-write",
                    mode="apply",
                    inputs={"packet_path": inputs["packet_path"]},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in stderr_records], ["dirty_worktree"])
            self.assertFalse(validation_path.exists())

            self.run_git(git_root, "add", inputs["body_file"], inputs["packet_path"])
            self.run_git(git_root, "commit", "--quiet", "-m", "packet artifacts")

            completed, response, stderr_records = run_runner(
                helper_request(
                    "validate-pr-packet-write",
                    mode="apply",
                    inputs={"packet_path": inputs["packet_path"]},
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok", 0)
            self.assertEqual(stderr_records, [])
            self.assertEqual(response["data"]["mutation"]["mutation_status"], "applied")
            self.assertEqual(response["data"]["validation_source"], "validate-pr-packet-read-only")
            self.assertTrue(validation_path.is_file())
            persisted = json.loads(validation_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["packet_id"], "prsg-999")
            self.assertEqual(persisted["status"], "passed")
            self.assertEqual(set(persisted["source_fingerprints"]), {"body", "packet"})

    def test_pr_packet_output_rejects_mismatched_paths_invalid_mode_and_invalid_body(self) -> None:
        from speckit_pro_runner.helpers.pr_emission import build_packet_body

        base_inputs = {
            "packet_path": "specs/prsg-999-packet/.process/pr-packets/prsg-999.json",
            "source_feature_dir": "specs/prsg-999-packet",
            "target": {"base_branch": "main", "head_branch": "agent/prsg-999-packet"},
            "title_type": "feat",
            "title_scope": "PRSG-999",
            "title_description": "Generate reviewer packet",
            "changed_files": ["specs/prsg-999-packet/spec.md"],
            "verification": ["python3 tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py passed"],
        }
        body_without_uat_runbook = build_packet_body(
            "feat(PRSG-999): Generate reviewer packet",
            summary="Summary.",
            what_changed="- Change.",
            why_it_matters="Reason.",
            how_to_review="- Review.",
            how_to_uat="No manual UAT.",
            verification="- Tests passed.",
            scope="- specs/prsg-999-packet/spec.md",
            known_gaps="- None.",
        ).replace("\n## UAT Runbook\n\nNo manual UAT.\n", "\n", 1)
        cases = {
            "feature_mismatch": {"source_feature_dir": "specs/other-feature"},
            "packet_id_mismatch": {"packet_id": "other-packet"},
            "body_escape": {"body_file": "README.md"},
            "validation_escape": {"validation_result_path": "specs/prsg-999-packet/.process/pr-packets/other/validation.json"},
            "invalid_mode": {"mode": "splti"},
            "invalid_body": {"body": "hello\n"},
            "custom_body_missing_uat_runbook": {"body": body_without_uat_runbook},
            "invalid_scope_evidence": {"scope_evidence": {"changed_files": ["README.md"]}},
            "invalid_verification_evidence": {"verification_evidence": [{"kind": "verification", "source": "tests"}]},
            "invalid_source_markers": {"source_markers": [{"marker_id": "prsg-999", "source": "specs/prsg-999-packet"}]},
            "invalid_rejected_title_candidate": {"rejected_title_candidates": [{"value": "bad"}]},
            "invalid_budget_result": {"budget_result": "surprise"},
            "invalid_split_slice": {"mode": "split", "split_slice": {"slice_id": "slice-1"}},
        }
        for name, override in cases.items():
            with self.subTest(name=name):
                completed, response, stderr_records = run_runner(
                    helper_request("pr-packet-output", inputs={**base_inputs, **override})
                )
                self.assertEqual(completed.returncode, 2)
                self.assert_response(response, "input_error", 2)
                self.assertEqual([diag["code"] for diag in stderr_records], ["invalid_input"])

    def test_pr_packet_output_draft_mode_emits_two_block_packet_that_passes_read_only_validation(self) -> None:
        from speckit_pro_runner.helpers.read_only import protected_body_sha256

        title = "feat(prsg-998): Open a draft pull request at the plan boundary"
        draft_body = "\n".join(
            [
                f"# {title}",
                "",
                "## Artifacts",
                "",
                "| Artifact | Purpose | Open |",
                "| --- | --- | --- |",
                "| Implementation Plan | Lay out the phases of a planned change so a reviewer can see the shape before any code exists. | `open specs/prsg-998-draft/artifacts/implementation-plan.html` |",
                "| Spec Explainer | Explain what the feature does and why it is worth building, in plain English. | `open specs/prsg-998-draft/artifacts/spec-explainer.html` |",
                "",
                "## Resume",
                "",
                "Stage: plan. Stopped at the plan-stage boundary for review.",
                "Resume with: `/speckit-pro:speckit-autopilot <workflow-file> --stage implement`",
                "",
            ]
        )

        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            inputs = {
                "packet_path": "specs/prsg-998-draft/.process/pr-packets/prsg-998.json",
                "body_file": "specs/prsg-998-draft/.process/pr-packets/prsg-998/body.md",
                "validation_result_path": "specs/prsg-998-draft/.process/pr-packets/prsg-998/validation.json",
                "source_feature_dir": "specs/prsg-998-draft",
                "target": {"base_branch": "main", "head_branch": "agent/prsg-998-draft"},
                "mode": "draft",
                "title_type": "feat",
                "title_scope": "prsg-998",
                "title_description": "Open a draft pull request at the plan boundary",
                "body": draft_body,
                "verification_evidence": [],
                "scope_evidence": {
                    "reviewable_loc": 0,
                    "production_files": 0,
                    "total_files": 0,
                    "budget_result": "within_budget",
                    "changed_files": [],
                    "non_goals": [
                        "Implementation evidence is not produced at the plan-stage boundary.",
                        "Flipping the draft pull request to ready is out of scope for this packet.",
                    ],
                },
            }

            completed, response, stderr_records = run_runner(
                helper_request("pr-packet-output", mode="apply", inputs=inputs),
                cwd=git_root,
            )
            self.assertEqual(stderr_records, [])
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok", 0)
            mutation = response["data"]["mutation"]
            self.assertEqual(mutation["mutation_status"], "applied")
            self.assertEqual(
                mutation["touched_paths"],
                [inputs["body_file"], inputs["packet_path"]],
            )

            body_path = git_root / inputs["body_file"]
            packet_path = git_root / inputs["packet_path"]
            self.assertTrue(body_path.is_file())
            self.assertTrue(packet_path.is_file())
            self.assertFalse((git_root / inputs["validation_result_path"]).exists())
            # The orchestrator composes the draft body, so it is used verbatim and the
            # reviewer-packet build_packet_body fallback is never reached.
            self.assertEqual(body_path.read_text(encoding="utf-8"), draft_body)

            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            self.assertEqual(packet["mode"], "draft")
            self.assertEqual(packet["packet_id"], "prsg-998")
            self.assertEqual(packet["generated_title"]["value"], title)
            self.assertEqual(packet["required_headings"], ["Artifacts", "Resume"])
            self.assertEqual(packet["editable_fields"], [])
            self.assertEqual(packet["verification_evidence"], [])
            self.assertEqual(packet["scope_evidence"], inputs["scope_evidence"])
            self.assertEqual(
                packet["uat"],
                {"how_to_uat": "", "uat_runbook_heading": "", "uat_source": "packet-input"},
            )
            self.assertEqual(packet["protected_body_fingerprint"]["elided_fields"], [])
            self.assertEqual(
                packet["protected_body_fingerprint"]["value"],
                protected_body_sha256(draft_body),
            )
            self.assertNotIn("split_slice", packet)

            completed, response, stderr_records = run_runner(
                helper_request(
                    "validate-pr-packet-read-only",
                    mode="read_only",
                    inputs={"packet_path": inputs["packet_path"]},
                ),
                cwd=git_root,
            )
            self.assertEqual(stderr_records, [])
            self.assertEqual(completed.returncode, 0)
            self.assert_response(response, "ok", 0)
            validation_result = response["data"]["stdout_json"]
            self.assertEqual(validation_result["failures"], [])
            self.assertEqual(validation_result["status"], "passed")
            self.assertIs(validation_result["pr_blocked"], False)
            self.assertEqual(validation_result["mode"], "draft")

    def test_pr_packet_output_rejects_unknown_mode_and_names_the_mode_field(self) -> None:
        inputs = {
            "packet_path": "specs/prsg-998-draft/.process/pr-packets/prsg-998.json",
            "source_feature_dir": "specs/prsg-998-draft",
            "target": {"base_branch": "main", "head_branch": "agent/prsg-998-draft"},
            "title_type": "feat",
            "title_scope": "prsg-998",
            "title_description": "Generate reviewer packet",
            "changed_files": ["specs/prsg-998-draft/spec.md"],
            "verification": ["mutation helper unit tests passed"],
            "mode": "drafts",
        }
        completed, response, stderr_records = run_runner(
            helper_request("pr-packet-output", inputs=inputs)
        )
        self.assertEqual(completed.returncode, 2)
        self.assert_response(response, "input_error", 2)
        self.assertEqual([diag["code"] for diag in stderr_records], ["invalid_input"])
        self.assertEqual(stderr_records[0]["details"]["field"], "mode")
        self.assertEqual(
            stderr_records[0]["message"],
            "mode must be single, split, or draft when provided",
        )

    def test_required_headings_returns_draft_blocks_and_preserves_reviewer_headings(self) -> None:
        from speckit_pro_runner.helpers.pr_emission import required_headings

        reviewer_headings = [
            "Summary",
            "What Changed",
            "Why It Matters",
            "How To Review",
            "How To UAT",
            "Verification",
            "Scope",
            "Known Gaps",
        ]
        self.assertEqual(required_headings(mode="draft"), ["Artifacts", "Resume"])
        self.assertEqual(required_headings(mode="single"), reviewer_headings)
        self.assertEqual(required_headings(mode="split"), reviewer_headings)

    def test_validate_pr_packet_write_ignores_fabricated_validation_and_requires_current_packet_pass(self) -> None:
        tmp, git_root = self.temp_clean_git_repo()
        with tmp:
            packet_rel = "specs/prsg-997-bad/.process/pr-packets/prsg-997.json"
            validation_rel = "specs/prsg-997-bad/.process/pr-packets/prsg-997/validation.json"
            packet_path = git_root / packet_rel
            packet_path.parent.mkdir(parents=True)
            packet_path.write_text('{"schema_version":"1.0.0"}\n', encoding="utf-8")
            self.run_git(git_root, "add", packet_rel)
            self.run_git(git_root, "commit", "--quiet", "-m", "invalid packet")

            completed, response, stderr_records = run_runner(
                helper_request(
                    "validate-pr-packet-write",
                    mode="apply",
                    inputs={
                        "packet_path": packet_rel,
                        "validation_result": {
                            "schema_version": "1.0.0",
                            "packet_id": "prsg-997",
                            "status": "passed",
                            "pr_blocked": False,
                        },
                    },
                ),
                cwd=git_root,
            )
            self.assertEqual(completed.returncode, 1)
            self.assert_response(response, "expected_failure", 1)
            self.assertEqual([diag["code"] for diag in stderr_records], ["packet_validation_failed"])
            self.assertFalse((git_root / validation_rel).exists())

    def test_contract_schemas_match_runner_fixture_envelopes(self) -> None:
        request_schema = json.loads(REQUEST_SCHEMA.read_text(encoding="utf-8"))
        result_schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(
            request_schema["required"],
            ["schema_version", "helper_id", "operation", "mode", "inputs"],
        )
        self.assertNotIn("boundary_context", request_schema["properties"])
        self.assertNotIn("approval_evidence", request_schema["properties"])
        self.assertEqual(
            set(request_schema["properties"]["mode"]["enum"]),
            {"read_only", "dry_run", "apply"},
        )

        allowed_request_fields = set(request_schema["properties"])
        for fixture_path in sorted((FIXTURE_DIR / "requests").glob("*.json")):
            request = json.loads(fixture_path.read_text(encoding="utf-8"))
            self.assertFalse(set(request) - allowed_request_fields, fixture_path.name)
            for required in request_schema["required"]:
                self.assertIn(required, request, fixture_path.name)
            self.assertIn(request["mode"], request_schema["properties"]["mode"]["enum"])
            completed, response, stderr_records = run_runner(request)
            self.assertEqual(completed.returncode, response["exit_code"])
            self.assertEqual([diag["code"] for diag in stderr_records], [diag["code"] for diag in response["diagnostics"]])
            self.assert_schema_contract_response(response, result_schema)

    def test_fixture_manifests_cover_mutation_helpers(self) -> None:
        fixture_manifest = json.loads((FIXTURE_DIR / "fixture-manifest.json").read_text(encoding="utf-8"))
        promotion_records = json.loads((FIXTURE_DIR / "promotion-records.json").read_text(encoding="utf-8"))
        promotion_schema = json.loads(PROMOTION_SCHEMA.read_text(encoding="utf-8"))
        promotion_fields = set(promotion_schema["properties"])
        self.assertGreaterEqual(len(fixture_manifest["helpers"]), 6)
        self.assertGreaterEqual(len(promotion_records["helpers"]), 6)
        for record in fixture_manifest["helpers"]:
            self.assertIn("helper_id", record)
            self.assertIn("modes", record)
            self.assertIn("failure_classes", record)
            self.assertIn("authoritative_command", record)
            fixture_path = command_stdin_fixture(record["authoritative_command"])
            self.assertTrue(fixture_path.is_file(), record["authoritative_command"])
            request = json.loads(fixture_path.read_text(encoding="utf-8"))
            self.assertEqual(request["helper_id"], record["helper_id"])
            self.assertEqual(request["operation"], record["operation"])
            self.assertIn(request["mode"], record["modes"])
            completed, response, stderr_records = run_runner(request)
            self.assertEqual(completed.returncode, response["exit_code"])
            self.assertEqual([diag["code"] for diag in stderr_records], [diag["code"] for diag in response["diagnostics"]])
        for record in promotion_records["helpers"]:
            self.assertFalse(set(record) - promotion_fields, record["helper_id"])
            for required in promotion_schema["required"]:
                self.assertIn(required, record)
            self.assertIn(record["promotion_status"], {"golden_only", "bash_compared", "deferred", "out_of_scope"})
            self.assertIn("rollback", record)
            self.assertNotIn(".sh", record["rollback"])
            self.assertNotIn("scripts authoritative", record["rollback"].lower())


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MutationHelperTests)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    total = result.testsRun
    failed = len(result.failures) + len(result.errors)
    passed = total - failed
    print(f"test-speckit-pro-mutation-helpers: {passed}/{total} passed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
