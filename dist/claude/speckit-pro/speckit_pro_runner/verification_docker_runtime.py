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
from .verification_docker_readback import MAX_ARCHIVE_BYTES, SnapshotReadback

CONTAINER_ID = re.compile(r"[0-9a-f]{64}")


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


def execute_container(client: DockerClient, image_id: str, execution_id: str, timeout: float,
                      input_readback: SnapshotReadback | None = None) -> dict[str, Any]:
    """Start once, retain raw output, compare daemon exit state, always reconcile."""
    options = container_options(image_id, execution_id)
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
        reasons = container_reasons(result["before"], image_id, execution_id)
        if reasons:
            raise ValueError("container policy rejected: " + ", ".join(reasons))
        if input_readback is not None:
            result["input_readback"] = input_readback.verify(client, cid, result["before"], deadline)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("verification deadline exhausted before start")
        attached = client.call(["start", "--attach", cid], remaining, check=False)
        result.update({key: attached[key] for key in ("stdout", "stderr", "timed_out", "output_limited")})
        if attached["timed_out"] or attached["output_limited"]:
            client.call(["kill", cid], 20, check=False)
        result["after"] = inspect_container(client, cid)
        if result["after"].get("Id") != cid or result["after"].get("Name") != f"/{name}":
            raise ValueError("container identity changed during verification")
        state = result["after"].get("State", {})
        reasons = container_reasons(result["after"], image_id, execution_id)
        waited = client.call(["wait", cid], 20)["stdout"].decode("ascii").strip()
        exit_code = state.get("ExitCode")
        stopped = (state.get("Status") == "exited" and state.get("Running") is False
                   and type(state.get("Pid")) is int and state["Pid"] == 0 and state.get("OOMKilled") is False
                   and state.get("Dead") is False and not state.get("Error"))
        result["completed"] = (not reasons and stopped and type(exit_code) is int and waited == str(exit_code)
                               and attached["exit_code"] == exit_code
                               and not result["timed_out"] and not result["output_limited"])
        result["exit_code"] = exit_code if result["completed"] else None
        result["policy_reasons"] = reasons
    except (OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired) as exc:
        result["failure"] = str(exc)[:240]
    finally:
        result["cleanup_confirmed"] = cleanup_container(client, name, image_id, execution_id)
    if not result["cleanup_confirmed"]:
        result["completed"], result["exit_code"] = False, None
    return result
