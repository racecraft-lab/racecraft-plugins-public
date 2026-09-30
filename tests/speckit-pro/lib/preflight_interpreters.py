"""Probe the Python interpreters a hosted Windows runner offers, and pick the active one.

The container preflight dispatcher calls this only for the Windows smoke role. Each
candidate gets three evidence files (stdout, stderr, exit code) and one record; the
selected interpreter is the supported candidate that is the running Python.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from preflight_architecture import resolve_architectures
from preflight_evidence import write_json, write_text

# Candidate launcher command -> evidence file slug. Order is probe order.
INTERPRETER_SLUGS = {
    "py -V:3": "py-V-3",
    "py -3": "py-3",
    "python": "python",
    "python3": "python3",
}
INTERPRETER_CANDIDATES = tuple(INTERPRETER_SLUGS)
PROBE_TIMEOUT_SECONDS = 120
INTERPRETER_PROBE_CODE = (
    "import json,os,platform,sys;"
    "print(json.dumps({"
    "'major':sys.version_info.major,"
    "'minor':sys.version_info.minor,"
    "'micro':sys.version_info.micro,"
    "'executable':sys.executable,"
    "'machine':platform.machine(),"
    "'processor_architecture':os.environ.get('PROCESSOR_ARCHITECTURE',''),"
    "'processor_architew6432':os.environ.get('PROCESSOR_ARCHITEW6432','')"
    "},separators=(',',':')))"
)


def same_executable(left: str, right: str) -> bool:
    return os.path.normcase(os.path.abspath(left)) == os.path.normcase(
        os.path.abspath(right)
    )


def _write_probe_files(evidence_dir: Path, slug: str, stdout: str, stderr: str, exit_code: int) -> None:
    write_text(evidence_dir / f"probe-{slug}.json", stdout)
    write_text(evidence_dir / f"probe-{slug}.stderr.txt", stderr)
    write_text(evidence_dir / f"probe-{slug}.exit-code.txt", f"{exit_code}\n")


def _parse_probe(stdout: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(stdout)
    except (TypeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _classify(payload: dict[str, Any], expected_architecture: str) -> dict[str, Any]:
    numbers = [payload.get(part) for part in ("major", "minor", "micro")]
    major, minor = numbers[0], numbers[1]
    all_ints = all(type(item) is int for item in numbers)
    version_supported = all_ints and (major > 3 or (major == 3 and minor >= 11))
    architectures = resolve_architectures(
        str(payload.get("machine") or ""),
        str(payload.get("processor_architecture") or ""),
        str(payload.get("processor_architew6432") or ""),
    )
    architecture_supported = (
        architectures.process_family == expected_architecture
        and architectures.native_family == expected_architecture
        and not architectures.emulated
    )
    interpreter = str(payload.get("executable") or "")
    supported = bool(version_supported and architecture_supported and interpreter)
    return {
        "status": "supported" if supported else "rejected",
        "supported": supported,
        "version": ".".join(str(item) for item in numbers) if all_ints else "",
        "interpreter": interpreter,
        "architecture": architectures.process,
        "architecture_family": architectures.process_family,
        "native_architecture": architectures.native,
        "native_architecture_family": architectures.native_family,
        "architecture_family_expected": expected_architecture,
        "architecture_emulated": architectures.emulated,
    }


def probe_interpreter(
    candidate: str, expected_architecture: str, evidence_dir: Path, *, cwd: Path,
) -> dict[str, Any]:
    slug = INTERPRETER_SLUGS[candidate]
    launcher = candidate.split()[0]
    path = shutil.which(launcher)
    record: dict[str, Any] = {
        "candidate": candidate,
        "command": path or "",
        "exit_code": 127,
        "supported": False,
        "selected": False,
        "status": "missing",
    }
    if path is None:
        _write_probe_files(evidence_dir, slug, "", f"{launcher} was not found on PATH\n", 127)
        return record
    try:
        completed = subprocess.run(
            [*candidate.split(), "-c", INTERPRETER_PROBE_CODE],
            cwd=cwd, capture_output=True, text=True, check=False, shell=False,
            timeout=PROBE_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        _write_probe_files(evidence_dir, slug, "", f"{type(exc).__name__}: {exc}\n", 124)
        return {**record, "exit_code": 124, "status": "probe_error", "error_type": type(exc).__name__}
    _write_probe_files(evidence_dir, slug, completed.stdout, completed.stderr, completed.returncode)
    record["exit_code"] = completed.returncode
    if completed.returncode != 0:
        return {**record, "status": "probe_failed"}
    payload = _parse_probe(completed.stdout)
    if payload is None:
        return {**record, "status": "invalid_probe"}
    return {**record, **_classify(payload, expected_architecture)}


def probe_interpreters(
    expected_architecture: str, evidence_dir: Path, *, cwd: Path,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Probe every candidate; select the supported one that is the running Python."""
    records = [
        probe_interpreter(candidate, expected_architecture, evidence_dir, cwd=cwd)
        for candidate in INTERPRETER_CANDIDATES
    ]
    selected = next(
        (
            record for record in records
            if record["supported"] and same_executable(str(record["interpreter"]), sys.executable)
        ),
        None,
    )
    for record in records:
        record["selected"] = record is selected
    write_json(evidence_dir / "interpreter-probes.json", records)
    return selected, records
