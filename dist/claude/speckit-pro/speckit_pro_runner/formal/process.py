"""Bound checker stdout, wall time, and the excerpt returned to the parent."""

from __future__ import annotations

import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any


def run_process(argv: list[str], cwd: Path, log: Path, timeout: int, output_bytes: int) -> dict[str, Any]:
    env = dict(os.environ)
    for key in ("JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS", "TLA_LIBRARY", "CONFIG_FILE", "OUT_DIR", "RUN_DIR", "SMT_ENCODING", "SMT_SOLVER"):
        env.pop(key, None)
    started = time.monotonic()
    result: dict[str, Any] = {"argv": argv, "exit_code": None, "timed_out": False, "output_limited": False}
    with log.open("wb") as output:
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
        reader = threading.Thread(target=capture, args=(process, output, output_bytes, result), daemon=True)
        reader.start()
        try:
            result["exit_code"] = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            result["timed_out"] = True
            process.kill()
            result["exit_code"] = process.wait()
        finally:
            reader.join(timeout=5)
            if reader.is_alive():
                result["output_limited"] = True
    result["duration_ms"] = round((time.monotonic() - started) * 1000)
    result["output"] = log.read_bytes().decode("utf-8", errors="replace")
    return result


def capture(process: subprocess.Popen, output: Any, limit: int, result: dict[str, Any]) -> None:
    total = 0
    assert process.stdout is not None
    with process.stdout:
        while chunk := process.stdout.read(8192):
            allowed = min(len(chunk), max(0, limit - total))
            output.write(chunk[:allowed])
            total += len(chunk)
            if total > limit:
                result["output_limited"] = True
                process.kill()
                break
