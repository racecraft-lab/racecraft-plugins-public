"""Bounded local Docker transport and owned-container lifecycle.

This runs only an already prepared image. It does not grant workflow launch
authority or qualify reuse; the existing execution ledger and parent native
observation remain required at the integration boundary.
"""

from __future__ import annotations

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
from typing import Any

from .verification_docker import container_options, container_reasons, validate_location

CONTAINER_ID = re.compile(r"[0-9a-f]{64}")


def capture_command(argv: list[str], cwd: Path, environment: dict[str, str], timeout: float,
                    output_bytes: int = 8 * 1024 * 1024) -> dict[str, Any]:
    """Capture separate streams without unbounded communicate() allocations."""
    if os.name != "posix":
        raise ValueError("Docker capture backend requires a POSIX host")
    if (type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0
            or type(output_bytes) is not int or output_bytes <= 0):
        raise ValueError("positive finite process limits are required")
    deadline = time.monotonic() + timeout
    result = {"stdout": bytearray(), "stderr": bytearray(), "timed_out": False, "output_limited": False}
    process = subprocess.Popen(argv, cwd=cwd, env=environment, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    try:
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
                    capacity = output_bytes - len(result["stdout"]) - len(result["stderr"])
                    result[key.data].extend(chunk[:capacity])
                    if len(chunk) > capacity:
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
    return {**result, "stdout": bytes(result["stdout"]), "stderr": bytes(result["stderr"]),
            "exit_code": process.returncode}


class DockerClient:
    """Explicit local daemon, trusted CLI, private credential-free CLI config."""

    def __init__(self, executable: Path, endpoint: str, directory: Path):
        if os.name != "posix" or not directory.is_absolute():
            raise ValueError("Docker transport requires a POSIX host and absolute private config path")
        _, socket_name = validate_location("validation@sha256:" + "0" * 64, endpoint)
        resolved = executable.resolve(strict=True)
        mode = resolved.stat().st_mode
        if not executable.is_absolute() or not stat.S_ISREG(mode) or mode & 0o022 or not os.access(resolved, os.X_OK):
            raise ValueError("Docker executable is not a trusted absolute executable")
        if not stat.S_ISSOCK(Path(socket_name).stat().st_mode):
            raise ValueError("Docker endpoint is not a local Unix socket")
        directory.mkdir(mode=0o700)
        self.directory = directory
        self.prefix = [str(resolved), "--host", endpoint, "--config", str(directory)]
        self.environment = {"HOME": str(directory), "DOCKER_CONFIG": str(directory),
                            "PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8"}
        self.events: list[dict[str, Any]] = []

    def call(self, args: list[str], timeout: float, check: bool = True) -> dict[str, Any]:
        result = capture_command([*self.prefix, *args], self.directory, self.environment, timeout)
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


def execute_container(client: DockerClient, image_id: str, execution_id: str, timeout: float) -> dict[str, Any]:
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
