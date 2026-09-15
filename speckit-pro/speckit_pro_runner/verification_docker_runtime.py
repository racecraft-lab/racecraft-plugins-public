"""Bounded local Docker transport and owned-container lifecycle.

This runs only an already prepared image. It does not grant workflow launch
authority or qualify reuse; the existing execution ledger and parent native
observation remain required at the integration boundary.
"""

from __future__ import annotations

from contextlib import nullcontext
import hashlib
import json
import math
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import time
from typing import Any, BinaryIO

from .verification_docker import container_options, container_reasons, validate_location
from .verification_docker_entrypoint import INJECTED_FILE_SHA256, RUNTIME_PREFIX
from .verification_docker_readback import MAX_ARCHIVE_BYTES, SnapshotReadback

CONTAINER_ID = re.compile(r"[0-9a-f]{64}")
SHA256 = re.compile(r"[0-9a-f]{64}")
ENGINE_INFO_KEYS = ("ID", "ServerVersion", "OperatingSystem", "OSType", "Architecture", "KernelVersion",
                    "DockerRootDir", "Driver", "CgroupDriver", "CgroupVersion", "SecurityOptions",
                    "DefaultRuntime", "Runtimes", "InitBinary", "Isolation", "Rootless", "ExperimentalBuild",
                    "LiveRestoreEnabled", "HTTPProxy", "HTTPSProxy", "NoProxy", "Plugins", "Containerd",
                    "CDISpecDirs", "DiscoveredDevices")


class CapturedOutput:
    """One byte budget for memory or archive output, with separately bounded stderr."""

    def __init__(self, limit: int, stdout_file: BinaryIO | None):
        self.limit, self.stdout_file = limit, stdout_file
        self.buffers = {"stdout": bytearray(), "stderr": bytearray()}
        self.counts = {"stdout": 0, "stderr": 0}
        self.stdout_digest = hashlib.sha256()

    def append(self, channel: str, chunk: bytes) -> bool:
        capacity = self.limit - self.counts["stdout"] - self.counts["stderr"]
        if channel == "stderr":
            capacity = min(capacity, 8 * 1024 * 1024 - self.counts["stderr"])
        accepted = chunk[:capacity]
        if self.stdout_file is not None and channel == "stdout":
            self.stdout_file.write(accepted)
            self.stdout_digest.update(accepted)
        else:
            self.buffers[channel].extend(accepted)
        self.counts[channel] += len(accepted)
        return len(chunk) > capacity

    def result(self) -> dict[str, Any]:
        result = {key: bytes(value) for key, value in self.buffers.items()}
        if self.stdout_file is not None:
            result.update(stdout_size=self.counts["stdout"], stdout_sha256=self.stdout_digest.hexdigest())
        return result


def capture_process(process: subprocess.Popen[bytes], timeout: float,
                    output_bytes: int = 8 * 1024 * 1024, *, stdout_file: BinaryIO | None = None) -> dict[str, Any]:
    """Own and capture an already started process; this function cannot launch one."""
    result = {"timed_out": False, "output_limited": False}
    try:
        if (type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0
                or type(output_bytes) is not int or output_bytes <= 0):
            raise ValueError("positive finite process limits are required")
        output = CapturedOutput(output_bytes, stdout_file)
        deadline = time.monotonic() + timeout
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ, "stdout")
            selector.register(process.stderr, selectors.EVENT_READ, "stderr")
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    result["timed_out"] = True
                    break
                for key, _ in selector.select(min(remaining, 0.1)):
                    chunk = os.read(key.fd, 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    if output.append(key.data, chunk):
                        result["output_limited"] = True
                        break
                if result["output_limited"]:
                    break
        if not result["timed_out"] and not result["output_limited"]:
            try:
                process.wait(timeout=max(0.001, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                result["timed_out"] = True
    finally:
        if process.poll() is None or result["timed_out"] or result["output_limited"]:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass  # The owned process group has already terminated.
        process.wait(timeout=5)
        process.stdout.close()
        process.stderr.close()
    return {**result, **output.result(), "exit_code": process.returncode}


class DockerClient:
    """Explicit local daemon, trusted CLI, private credential-free CLI config."""

    def __init__(self, executable: Path, endpoint: str, directory: Path):
        if os.name != "posix" or not directory.is_absolute():
            raise ValueError("Docker transport requires a POSIX host and absolute private config path")
        _, socket_name = validate_location("validation@sha256:" + "0" * 64, endpoint)
        resolved = executable.resolve(strict=True)
        mode = resolved.stat().st_mode
        if (not executable.is_absolute() or resolved.name != "docker" or not stat.S_ISREG(mode)
                or mode & 0o022 or not os.access(resolved, os.X_OK)):
            raise ValueError("Docker executable is not a trusted absolute executable")
        if not stat.S_ISSOCK(Path(socket_name).stat().st_mode):
            raise ValueError("Docker endpoint is not a local Unix socket")
        directory.mkdir(mode=0o700)
        self.directory = directory
        self.executable = resolved
        self.endpoint = endpoint
        self.executable_sha256, self._executable_identity = _executable_binding(resolved)
        self.prefix = ["--host", endpoint, "--config", str(directory)]
        self.environment = {"HOME": str(directory), "DOCKER_CONFIG": str(directory),
                            "PATH": str(resolved.parent), "LANG": "C.UTF-8"}
        self.events: list[dict[str, Any]] = []

    def call(self, args: list[str], timeout: float, check: bool = True, archive: Path | None = None) -> dict[str, Any]:
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("positive finite Docker timeout is required")
        # PATH contains only the validated Docker binary's directory. No caller
        # can substitute another program; the capture helper only reads pipes.
        with archive.open("xb") if archive is not None else nullcontext() as sink:
            process = subprocess.Popen(["docker", *self.prefix, *args], cwd=self.directory, env=self.environment,
                                       stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       start_new_session=True)
            result = capture_process(process, timeout, MAX_ARCHIVE_BYTES if archive is not None else 8 * 1024 * 1024, stdout_file=sink)
        if archive is not None:
            result["stdout_path"] = str(archive)
        self.events.append({"argv": args, **result})
        if check and (result["exit_code"] != 0 or result["timed_out"] or result["output_limited"]):
            raise ValueError(f"Docker {args[0]} did not complete successfully")
        return result

    def engine_binding(self) -> dict[str, Any]:
        """Bind the client, negotiated API, daemon, runtime and platform settings."""
        current_sha256, current_identity = _executable_binding(self.executable)
        if current_sha256 != self.executable_sha256 or current_identity != self._executable_identity:
            raise ValueError("Docker executable changed during verification")
        version = _json_object(_binding_output(self, ["version", "--format", "{{json .}}"]), "version")
        info = _json_object(_binding_output(self, ["info", "--format", "{{json .}}"]), "info")
        client, server = version.get("Client"), version.get("Server")
        if not isinstance(client, dict) or not isinstance(server, dict):
            raise ValueError("Docker version omitted client or server identity")
        common_version_keys = ("Version", "ApiVersion", "GitCommit", "GoVersion", "Os", "Arch")
        selected_version = {"client": {key: client.get(key) for key in common_version_keys},
                            "server": {key: server.get(key) for key in (*common_version_keys, "MinAPIVersion")}}
        if any(not isinstance(value, str) or not value for side in selected_version.values() for value in side.values()):
            raise ValueError("Docker version identity is incomplete")
        selected_info = {key: info.get(key) for key in ENGINE_INFO_KEYS}
        for key in ("HTTPProxy", "HTTPSProxy", "NoProxy"):
            raw = selected_info[key]
            selected_info[key] = {"present": raw not in (None, ""),
                                  "sha256": hashlib.sha256(str(raw or "").encode("utf-8")).hexdigest()}
        required = ("ID", "ServerVersion", "OperatingSystem", "OSType", "Architecture", "KernelVersion",
                    "DockerRootDir", "Driver", "CgroupDriver", "CgroupVersion", "SecurityOptions",
                    "DefaultRuntime", "Runtimes", "InitBinary")
        if any(selected_info.get(key) in (None, "", [], {}) for key in required):
            raise ValueError("Docker daemon/runtime identity is incomplete")
        if selected_info["OSType"] != "linux" or selected_info["Architecture"] not in {"aarch64", "arm64"}:
            raise ValueError("Docker daemon must report Linux/arm64")
        return {"schema_version": "docker-engine-binding/v2",
                "cli": {"path": str(self.executable), "sha256": self.executable_sha256},
                "endpoint": self.endpoint, "version": selected_version, "info": selected_info}


def _executable_binding(path: Path) -> tuple[str, tuple[int, int, int, int]]:
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        body_sha256 = hashlib.file_digest(stream, "sha256").hexdigest()
        after = os.fstat(stream.fileno())
    identity = (before.st_dev, before.st_ino, before.st_mode, before.st_size)
    if identity != (after.st_dev, after.st_ino, after.st_mode, after.st_size):
        raise ValueError("Docker executable changed while being read")
    return body_sha256, identity


def _retain_digests_only(event: dict[str, Any]) -> None:
    """Version/info may contain private daemon settings; retain exact hashes only."""
    for channel in ("stdout", "stderr"):
        body = event.get(channel)
        if isinstance(body, bytes):
            event[f"{channel}_size"] = len(body)
            event[f"{channel}_sha256"] = hashlib.sha256(body).hexdigest()
            event[channel] = b""


def _binding_output(client: DockerClient, argv: list[str]) -> bytes:
    result = client.call(argv, 20, check=False)
    body = result["stdout"]
    _retain_digests_only(client.events[-1])
    if result["exit_code"] != 0 or result["timed_out"] or result["output_limited"]:
        raise ValueError(f"Docker {argv[0]} identity observation failed")
    return body


def _json_object(body: bytes, name: str) -> dict[str, Any]:
    try:
        value = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"Docker {name} did not return JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Docker {name} did not return one object")
    return value


def split_runtime_frame(stdout: bytes, *, required: bool) -> tuple[dict[str, Any] | None, bytes]:
    """Consume only the launcher's first length/digest-framed observation."""
    if not stdout.startswith(RUNTIME_PREFIX):
        if required:
            raise ValueError("qualified Docker output omitted the launcher runtime frame")
        return None, stdout
    header, separator, remainder = stdout.partition(b"\n")
    if not separator:
        raise ValueError("launcher runtime frame header is incomplete")
    fields = header[len(RUNTIME_PREFIX):].split(b" ")
    if len(fields) != 2 or not fields[0].isdigit() or len(fields[1]) != 64:
        raise ValueError("launcher runtime frame header is malformed")
    length, expected = int(fields[0]), fields[1].decode("ascii", "strict")
    if not 1 <= length <= 8192 or SHA256.fullmatch(expected) is None or len(remainder) < length + 1 or remainder[length:length + 1] != b"\n":
        raise ValueError("launcher runtime frame boundaries are invalid")
    payload, workload = remainder[:length], remainder[length + 1:]
    if hashlib.sha256(payload).hexdigest() != expected:
        raise ValueError("launcher runtime frame digest disagrees")
    value = _json_object(payload, "launcher runtime frame")
    if (set(value) != {"schema_version", "launcher_pid", "init", "workload_executable", "confinement", "injected_files"}
            or value["schema_version"] != "docker-launcher-runtime/v2"):
        raise ValueError("launcher runtime frame schema is invalid")
    init, executable = value["init"], value["workload_executable"]
    confinement, injected_files = value["confinement"], value["injected_files"]
    expected_injected = {path: {"sha256": digest, "writable": False}
                         for path, digest in INJECTED_FILE_SHA256.items()}
    if (type(value["launcher_pid"]) is not int or value["launcher_pid"] <= 1
            or not isinstance(init, dict) or set(init) != {"pid", "path", "sha256", "cmdline_sha256"} or init["pid"] != 1
            or not isinstance(executable, dict) or set(executable) != {"path", "sha256"}
            or any(not isinstance(item.get("path"), str) or not item["path"].startswith("/")
                   or SHA256.fullmatch(item.get("sha256", "")) is None for item in (init, executable))
            or SHA256.fullmatch(init.get("cmdline_sha256", "")) is None
            or not isinstance(confinement, dict)
            or confinement != {"uid": 65532, "gid": 65532, "threads": "1", "seccomp": "2",
                               "seccomp_filters": confinement.get("seccomp_filters"),
                               "cap_eff": "0000000000000000", "no_new_privs": "1"}
            or not str(confinement.get("seccomp_filters", "")).isdigit()
            or int(confinement["seccomp_filters"]) < 2
            or injected_files != expected_injected):
        raise ValueError("launcher runtime frame is incomplete or weakened")
    return value, workload


def inspect_container(client: DockerClient, target: str) -> dict[str, Any]:
    rows = json.loads(client.call(["inspect", target], 20)["stdout"])
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise ValueError("Docker inspect did not return exactly one container")
    return rows[0]


def cleanup_container(client: DockerClient, name: str, image_id: str, execution_id: str) -> bool:
    """Remove only the matching owned ID; daemon errors never prove absence."""
    try:
        listed = client.call(["ps", "--all", "--no-trunc", "--filter", f"name=^/{name}$", "--format", "{{.ID}}"], 20)
        if not listed["stdout"].strip():
            return True
        info = inspect_container(client, name)
        cid = info.get("Id")
        if (not isinstance(cid, str) or CONTAINER_ID.fullmatch(cid) is None or info.get("Image") != image_id
                or info.get("Name") != f"/{name}"
                or info.get("Config", {}).get("Labels", {}).get("org.racecraft.verification") != execution_id):
            return False
        client.call(["rm", "--force", cid], 20)
        remaining = client.call(["ps", "--all", "--no-trunc", "--filter", f"id={cid}", "--format", "{{.ID}}"], 20)
        return not remaining["stdout"].strip()
    except (OSError, ValueError, TypeError, AttributeError, subprocess.TimeoutExpired):
        return False


def _stopped_container(state: Any) -> bool:
    return (isinstance(state, dict) and state.get("Status") == "exited" and state.get("Running") is False
            and type(state.get("Pid")) is int and state["Pid"] == 0 and state.get("OOMKilled") is False
            and state.get("Dead") is False and not state.get("Error"))


def _completed_execution(result: dict[str, Any], reasons: list[str], stopped: bool, exit_code: Any,
                         waited: str, attached_exit: Any, required_attestation: bool) -> bool:
    return (not reasons and stopped and type(exit_code) is int and waited == str(exit_code)
            and attached_exit == exit_code and not result["timed_out"] and not result["output_limited"]
            and (not required_attestation or result["runtime_attestation"] is not None)
            and (not required_attestation or result.get("post_input_readback", {}).get("verified") is True))


def execute_container(client: DockerClient, image_id: str, execution_id: str, timeout: float,
                      input_readback: SnapshotReadback | None = None) -> dict[str, Any]:
    """Start once, retain raw output, compare daemon exit state, always reconcile."""
    required_attestation = input_readback.require_attestation if input_readback is not None else False
    options = container_options(image_id, execution_id, qualified=required_attestation)
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("positive finite execution timeout is required")
    name = f"speckit-verifier-{execution_id}"
    existing = client.call(["ps", "--all", "--no-trunc", "--filter", f"name=^/{name}$", "--format", "{{.ID}}"], 20)
    if existing["stdout"].strip():
        raise ValueError("verification container name already exists; refusing launch or cleanup")
    result = {"container_name": name, "image_id": image_id, "execution_id": execution_id,
              "completed": False, "exit_code": None, "stdout": b"", "stderr": b"", "reusable": False}
    deadline = time.monotonic() + timeout
    try:
        created = client.call(options, min(timeout, 20))
        cid = created["stdout"].decode("ascii").strip()
        if CONTAINER_ID.fullmatch(cid) is None:
            raise ValueError("Docker create did not return a full container ID")
        result["container_id"] = cid
        result["before"] = inspect_container(client, cid)
        if result["before"].get("Id") != cid or result["before"].get("Name") != f"/{name}":
            raise ValueError("inspected container does not match the owned creation identity")
        reasons = container_reasons(result["before"], image_id, execution_id, qualified=required_attestation)
        if reasons:
            raise ValueError("container policy rejected: " + ", ".join(reasons))
        if input_readback is not None:
            result["input_readback"] = input_readback.verify(client, cid, result["before"], deadline)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("verification deadline exhausted before start")
        attached = client.call(["start", "--attach", cid], remaining, check=False)
        result.update({key: attached[key] for key in ("stdout", "stderr", "timed_out", "output_limited")})
        result["runtime_attestation"] = None
        if required_attestation:
            result["runtime_attestation"], result["stdout"] = split_runtime_frame(result["stdout"], required=True)
        if attached["timed_out"] or attached["output_limited"]:
            client.call(["kill", cid], 20, check=False)
        result["after"] = inspect_container(client, cid)
        if result["after"].get("Id") != cid or result["after"].get("Name") != f"/{name}":
            raise ValueError("container identity changed during verification")
        state = result["after"].get("State", {})
        reasons = container_reasons(result["after"], image_id, execution_id, qualified=required_attestation)
        waited = client.call(["wait", cid], 20)["stdout"].decode("ascii").strip()
        exit_code = state.get("ExitCode") if isinstance(state, dict) else None
        stopped = _stopped_container(state)
        if input_readback is not None and input_readback.require_attestation and stopped:
            result["post_input_readback"] = input_readback.verify_after(client, cid, result["after"], deadline)
        result["completed"] = _completed_execution(result, reasons, stopped, exit_code, waited,
                                                   attached["exit_code"], required_attestation)
        result["exit_code"] = exit_code if result["completed"] else None
        result["policy_reasons"] = reasons
    except (OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired) as exc:
        result["failure"] = str(exc)[:240]
    finally:
        result["cleanup_confirmed"] = cleanup_container(client, name, image_id, execution_id)
    if not result["cleanup_confirmed"]:
        result["completed"], result["exit_code"] = False, None
    return result
