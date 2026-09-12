"""Isolated verification executions and independently observed receipt replay.

Trust boundary: native_observation is supplied by the orchestrating parent from
the actual native tool event, never reconstructed from a worker or receipt. The
runner cannot authenticate its CLI caller. Absent a recovered native event,
reuse is denied. Digests establish equality, not authority.

The wrapper copies the entire bounded local input tree (including ignored and
dirty files), rejects symlinks, and runs direct PROJECT_COMMANDS in that sealed
copy. Unsupported closures/commands require ordinary verification, not reuse.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

from .agent_materialization import canonical_bytes
from .execution_control import confined_path, durable_json, elapsed, execution_control, require_text

SCHEMA = "verification-record/v1"
COMMAND_IDS = {"BUILD", "TYPECHECK", "LINT", "UNIT_TEST", "INTEGRATION_TEST", "FULL_VERIFY",
               "COMPLEXITY", "MUTATION", "DEPENDENCY_RULES"}
MAX_FILES = 50000
MAX_BYTES = 512 * 1024 * 1024


def digest(value: Any) -> str:
    return sha(canonical_bytes(value))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def project_command(workflow: Path, command_id: str) -> list[str]:
    if command_id not in COMMAND_IDS:
        raise ValueError("command_id must select a non-mutating PROJECT_COMMANDS slot")
    text = workflow.read_text(encoding="utf-8")
    blocks = re.findall(r"^## PROJECT_COMMANDS\s*\n```json\s*\n(.*?)\n```", text, re.M | re.S)
    if len(blocks) != 1:
        raise ValueError("persist one PROJECT_COMMANDS JSON section in the workflow first")
    commands = json.loads(blocks[0])
    command = commands.get(command_id) if isinstance(commands, dict) else None
    if not isinstance(command, str) or not command.strip() or command == "N/A":
        raise ValueError("selected PROJECT_COMMANDS slot is unavailable")
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    argv = list(lexer)
    if not argv or any(set(arg) & set(";&|<>`\n") for arg in argv) or any("$(" in arg for arg in argv):
        raise ValueError("compound or interpolated commands require ordinary native verification")
    if any(Path(arg).is_absolute() for arg in argv[1:]):
        raise ValueError("absolute command inputs escape the isolated snapshot")
    if any(".." in Path(arg).parts for arg in argv[1:]):
        raise ValueError("parent-relative command inputs escape the isolated snapshot")
    return argv


def evidence_directory(workflow_name: str) -> str:
    return (Path(workflow_name).parent / ".process/verification").as_posix()


def tree_bytes(root: Path, workflow_name: str) -> dict[str, bytes]:
    excluded = {evidence_directory(workflow_name),
                (Path(workflow_name).parent / ".process/execution-control").as_posix()}
    files: dict[str, bytes] = {}
    total = 0
    for directory, names, filenames in os.walk(root, followlinks=False):
        base = Path(directory)
        for name in list(names):
            path = base / name
            relative = path.relative_to(root).as_posix()
            if name == ".git" or relative in excluded:
                names.remove(name)
            elif path.is_symlink():
                raise ValueError("symlink input closure requires ordinary verification")
        for name in sorted(filenames):
            path = base / name
            relative = path.relative_to(root).as_posix()
            if relative in excluded or name == ".git":
                continue
            if path.is_symlink() or not path.is_file():
                raise ValueError("non-regular input closure requires ordinary verification")
            data = path.read_bytes()
            files[relative] = data
            total += len(data)
            if len(files) > MAX_FILES or total > MAX_BYTES:
                raise ValueError("input closure exceeds bounded snapshot; use ordinary verification")
    return files


def tree_digest(files: dict[str, bytes]) -> str:
    return digest({name: sha(data) for name, data in sorted(files.items())})


def environment_binding() -> tuple[dict[str, str], str]:
    environment = dict(os.environ)
    environment.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1")
    # Do not persist values: credentials may be inherited by an authorized check.
    return environment, digest(environment)


def toolchain_binding(argv: list[str]) -> tuple[str, dict[str, str]]:
    executable = shutil.which(argv[0])
    if executable is None:
        raise ValueError("verification executable unavailable")
    path = Path(executable).resolve()
    runner_root = Path(__file__).parent
    runner_files = {source.relative_to(runner_root).as_posix(): sha(source.read_bytes())
                    for source in runner_root.rglob("*") if source.is_file() and source.suffix in {".py", ".json"}}
    return str(path), {"executable": str(path), "executable_sha256": sha(path.read_bytes()),
                       "runner_sha256": digest(runner_files)}


def materialize(root: Path, files: dict[str, bytes]) -> None:
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        path.chmod(0o444)


def observation_material(record: dict[str, Any]) -> dict[str, Any]:
    keys = ("execution_id", "dispatch_id", "command_id", "argv", "workflow_file", "snapshot_sha256", "environment_sha256",
            "toolchain", "exit_code", "stdout_sha256", "stderr_sha256", "inputs_unchanged", "snapshot_unchanged",
            "producer", "completed", "elapsed_seconds", "isolation_mode")
    return {key: record[key] for key in keys}


def run_snapshot_command(argv: list[str], snapshot: Path, environment: dict[str, str], timeout: float) -> tuple[int | None, bytes, bytes, bool]:
    """Own the process group, including timeout cleanup; never retry a launch."""
    with subprocess.Popen(argv, cwd=snapshot, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          start_new_session=os.name == "posix") as process:
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            return process.returncode, stdout, stderr, True
        except subprocess.TimeoutExpired:
            if os.name == "posix":
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    process.kill()
            else:
                process.kill()
            stdout, stderr = process.communicate()
            return None, stdout, stderr, False


def execute_verification(root: Path, inputs: dict[str, Any], mode: str) -> dict[str, Any]:
    """Invoke only the workflow command selected by an authorized parent request."""
    if mode not in {"dry_run", "apply"}:
        raise ValueError("verification execution requires dry_run or apply")
    workflow_name = require_text(inputs.get("workflow_file"), "workflow_file")
    command_id = require_text(inputs.get("command_id"), "command_id")
    workflow = confined_path(root, workflow_name)
    argv = project_command(workflow, command_id)
    executable, toolchain = toolchain_binding(argv)
    environment, environment_sha = environment_binding()
    before = tree_bytes(root, workflow_name)
    snapshot_sha = tree_digest(before)
    if mode == "dry_run":
        return {"command_id": command_id, "argv": argv, "snapshot_sha256": snapshot_sha,
                "writes_state": False, "authorization_granted": False, "reusable": False}
    dispatch_id = require_text(inputs.get("dispatch_id"), "dispatch_id")
    begun = execution_control(root, {"workflow_file": workflow_name, "action": "begin-verification", "dispatch_id": dispatch_id,
                                    "expected_run_id": inputs.get("expected_run_id"), "ledger_path": inputs.get("ledger_path")}, "apply")
    if begun["disposition"] != "continue":
        raise ValueError("verification launch blocked: " + ", ".join(begun["reasons"]))
    execution_id = uuid.uuid4().hex
    record_name = f"{evidence_directory(workflow_name)}/{execution_id}.json"
    record_path = confined_path(root, record_name)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="speckit-verify-") as temporary:
        temporary_root = Path(temporary)
        snapshot = temporary_root / "inputs"
        outputs = temporary_root / "outputs"
        snapshot.mkdir()
        outputs.mkdir()
        materialize(snapshot, before)
        environment.update(TMPDIR=str(outputs), TMP=str(outputs), TEMP=str(outputs),
                           XDG_CACHE_HOME=str(outputs), SPECKIT_VERIFICATION_OUTPUT_DIR=str(outputs))
        now = time.time()
        ledger = begun["ledger"]
        remaining = min(7200 - elapsed(ledger, now, ledger["started_at"]),
                        5400 - elapsed(ledger, now, ledger["slice_started_at"]))
        if remaining <= 0:
            raise ValueError("verification budget exhausted while preparing isolated inputs")
        exit_code, stdout, stderr, completed = run_snapshot_command([executable, *argv[1:]], snapshot, environment, remaining)
        snapshot_unchanged = tree_digest(tree_bytes(snapshot, workflow_name)) == snapshot_sha
    unchanged = tree_digest(tree_bytes(root, workflow_name)) == snapshot_sha
    record = {"schema_version": SCHEMA, "execution_id": execution_id, "dispatch_id": dispatch_id, "command_id": command_id,
              "argv": argv, "workflow_file": workflow_name, "snapshot_sha256": snapshot_sha,
              "environment_sha256": environment_sha, "toolchain": toolchain, "exit_code": exit_code,
              "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr), "inputs_unchanged": unchanged,
              "snapshot_unchanged": snapshot_unchanged, "producer": "runner-isolated-project-command/v1",
              "completed": completed, "elapsed_seconds": time.monotonic() - started,
              "isolation_mode": "copy_only"}
    durable_json(record_path, record)
    return {"record_path": record_name, "record": record, "observation_material": observation_material(record),
            "writes_state": True, "reusable": False, "requires_independent_native_event": True,
            "authorization_granted": False, "rerun_required": True,
            "limitations": ["copy_only_is_not_qualified_immutable_isolation"]}


def isolation_reasons(record: dict[str, Any], observation: Any) -> list[str]:
    """Only the host that really enforced isolation can qualify its native event.

    The portable wrapper currently emits copy_only. This validation seam allows
    a separately qualified host implementation; it never upgrades a copy-only
    execution, and its positive fixtures are not runtime qualification evidence.
    """
    if record.get("isolation_mode") != "qualified_readonly_snapshot":
        return ["copy_only_is_not_qualified_immutable_isolation"]
    isolation = observation.get("qualified_isolation") if isinstance(observation, dict) else None
    if not isinstance(isolation, dict) or isolation.get("schema_version") != "native-isolation/v1":
        return ["missing_qualified_isolation_event"]
    for key in ("execution_id", "snapshot_sha256", "environment_sha256", "toolchain"):
        if isolation.get(key) != record.get(key):
            return ["isolation_event_binding_mismatch"]
    for key in ("readonly_snapshot_identity", "isolated_output_identity", "qualification_id"):
        if not isinstance(isolation.get(key), str) or not isolation[key].strip():
            return ["isolation_event_incomplete"]
    external = isolation.get("external_input_sha256")
    if not isinstance(external, str) or not re.fullmatch(r"[0-9a-f]{64}", external):
        return ["external_input_closure_missing"]
    if isolation.get("current_external_input_sha256") != external:
        return ["external_input_closure_changed"]
    return []


def validate_execution_record(root: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    """Compare a record to current inputs AND an independently recovered event."""
    reasons = []
    try:
        workflow_name = require_text(inputs.get("workflow_file"), "workflow_file")
        command_id = require_text(inputs.get("command_id"), "command_id")
        name = require_text(inputs.get("record_path"), "record_path")
        if Path(name).parent.as_posix() != evidence_directory(workflow_name):
            raise ValueError("record_path is not this workflow's verification evidence")
        record = json.loads(confined_path(root, name).read_text(encoding="utf-8"))
        if not isinstance(record, dict) or record.get("schema_version") != SCHEMA:
            raise ValueError("invalid verification record")
        observation = inputs.get("native_observation")
        if not isinstance(observation, dict) or not isinstance(observation.get("native_event_id"), str) or not observation["native_event_id"].strip():
            reasons.append("missing_independent_native_event")
        elif {key: value for key, value in observation.items() if key not in {"native_event_id", "qualified_isolation"}} != observation_material(record):
            reasons.append("native_event_disagrees_with_receipt")
        reasons.extend(isolation_reasons(record, observation))
        argv = project_command(confined_path(root, workflow_name), command_id)
        _, toolchain = toolchain_binding(argv)
        _, environment_sha = environment_binding()
        if record.get("workflow_file") != workflow_name or record.get("command_id") != command_id or record.get("argv") != argv:
            reasons.append("command_binding_changed")
        if record.get("toolchain") != toolchain or record.get("environment_sha256") != environment_sha:
            reasons.append("toolchain_or_environment_changed")
        if record.get("snapshot_sha256") != tree_digest(tree_bytes(root, workflow_name)):
            reasons.append("input_snapshot_changed")
        if type(record.get("exit_code")) is not int or record["exit_code"] != 0 or record.get("completed") is not True:
            reasons.append("command_not_successfully_completed")
        if record.get("inputs_unchanged") is not True or record.get("snapshot_unchanged") is not True:
            reasons.append("inputs_changed_during_verification")
    except (ValueError, OSError, KeyError, TypeError) as exc:
        reasons.append(f"unverifiable_record: {str(exc)[:160]}")
    return {"reusable": not reasons, "rerun_required": bool(reasons), "reasons": reasons,
            "writes_state": False, "trust_boundary": "independent_parent_native_event"}
