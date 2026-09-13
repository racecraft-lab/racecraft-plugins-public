"""Isolated verification executions and independently observed receipt replay.

Trust boundary: native_observation is supplied by the orchestrating parent from
the actual native tool event, never reconstructed from a worker or receipt. The
runner cannot authenticate its CLI caller. Absent a recovered native event,
reuse is denied. Digests establish equality, not authority.

The wrapper copies the bounded local input tree (including ignored and dirty
files, directory structure, and modes), rejects symlinks, and runs direct
PROJECT_COMMANDS in that copy. A copy is not immutable isolation. Unsupported
closures/commands require ordinary verification, not reuse.
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
import sys
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
PROJECT_PROGRAMS = {"python", "python3", "node", "npm", "npx", "pnpm", "yarn", "bun", "cargo", "go",
                    "make", "pytest", "lint-imports", "uv", "ruff", "mypy"}


def digest(value: Any) -> str:
    return sha(canonical_bytes(value))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def project_program(raw: str, search_path: str | None = None) -> tuple[str, str]:
    """Bind supported direct tools; never reinterpret a requested executable."""
    name = Path(raw).name.removesuffix(".exe")
    if name.casefold() in {"bash", "sh", "zsh", "fish", "csh", "ksh", "pwsh", "powershell", "cmd", "jq", "env"}:
        raise ValueError("shell/JQ wrappers require ordinary native verification")
    found = shutil.which(raw, path=search_path)
    if found is None or not Path(found).is_absolute():
        raise ValueError("missing or relative executable resolution requires ordinary native verification")
    invocation = os.path.abspath(found)
    if invocation == os.path.abspath(sys.executable):
        return "current_python", invocation
    if name not in PROJECT_PROGRAMS or Path(found).suffix.casefold() in {".bat", ".cmd"}:
        raise ValueError("unsupported executable requires ordinary native verification")
    named = shutil.which(name, path=search_path)
    if named is None or not Path(named).is_absolute() or os.path.abspath(named) != invocation:
        raise ValueError("custom executable resolution requires ordinary native verification")
    return name, invocation


def workflow_argv(workflow: Path, command_id: str) -> list[str]:
    """Parse direct workflow arguments without resolving a host toolchain."""
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


def project_command(workflow: Path, command_id: str) -> list[str]:
    argv = workflow_argv(workflow, command_id)
    project_program(argv[0])
    return argv


def evidence_directory(workflow_name: str) -> str:
    return (Path(workflow_name).parent / ".process/verification").as_posix()


def tree_bytes(root: Path, workflow_name: str) -> dict[str, tuple[int, bytes | None]]:
    excluded = {evidence_directory(workflow_name),
                (Path(workflow_name).parent / ".process/execution-control").as_posix()}
    files: dict[str, tuple[int, bytes | None]] = {}
    walk_errors: list[OSError] = []
    total = 0
    for directory, names, filenames in os.walk(root, followlinks=False, onerror=walk_errors.append):
        base = Path(directory)
        files[base.relative_to(root).as_posix()] = (base.stat().st_mode & 0o7777, None)
        if len(files) > MAX_FILES:
            raise ValueError("input closure exceeds bounded snapshot; use ordinary verification")
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
            files[relative] = (path.stat().st_mode & 0o7777, data)
            total += len(data)
            if len(files) > MAX_FILES or total > MAX_BYTES:
                raise ValueError("input closure exceeds bounded snapshot; use ordinary verification")
    if walk_errors:
        raise ValueError("unreadable input closure requires ordinary verification") from walk_errors[0]
    return files


def tree_digest(files: dict[str, tuple[int, bytes | None]]) -> str:
    return digest({name: {"mode": mode, "sha256": sha(data) if data is not None else None}
                   for name, (mode, data) in sorted(files.items())})


def environment_binding(outputs: Path) -> tuple[dict[str, str], str]:
    environment = dict(os.environ)
    environment.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1", TMPDIR=str(outputs), TMP=str(outputs),
                       TEMP=str(outputs), XDG_CACHE_HOME=str(outputs), SPECKIT_VERIFICATION_OUTPUT_DIR=str(outputs))
    # Do not persist values: credentials may be inherited by an authorized check.
    return environment, digest(environment)


def runner_binding() -> str:
    runner_root = Path(__file__).parent
    runner_files = {source.relative_to(runner_root).as_posix(): sha(source.read_bytes())
                    for source in runner_root.rglob("*") if source.is_file() and source.suffix in {".py", ".json"}}
    return digest(runner_files)


def toolchain_binding(argv: list[str]) -> tuple[str, dict[str, str]]:
    _, executable = project_program(argv[0])
    path = Path(executable)
    return str(path), {"executable": str(path), "executable_sha256": sha(path.read_bytes()),
                       "runner_sha256": runner_binding()}


def materialize(root: Path, files: dict[str, tuple[int, bytes | None]]) -> None:
    for name, (mode, content) in files.items():
        path = root / name
        if content is None:
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            path.chmod(mode)
    # Apply directory modes last so a read-only parent does not block copying.
    for name, (mode, content) in sorted(files.items(), key=lambda item: len(Path(item[0]).parts), reverse=True):
        if content is None:
            (root / name).chmod(mode)


def observation_material(record: dict[str, Any]) -> dict[str, Any]:
    keys = ("execution_id", "dispatch_id", "command_id", "argv", "workflow_file", "snapshot_sha256", "environment_sha256",
            "toolchain", "exit_code", "stdout_sha256", "stderr_sha256", "inputs_unchanged", "snapshot_unchanged",
            "producer", "completed", "elapsed_seconds", "isolation_mode", "output_directory")
    return {key: record[key] for key in keys}


def open_snapshot_process(argv: list[str], snapshot: Path, environment: dict[str, str],
                          expected_executable: str | None) -> subprocess.Popen[bytes]:
    """Launch one finite, path-bound direct project tool without a shell."""
    program, resolved = project_program(argv[0], environment.get("PATH"))
    if expected_executable is not None and resolved != expected_executable:
        raise ValueError("toolchain executable changed; ordinary native verification is required")
    # Each executable prefix is visible to the repository's static confinement
    # gate. Keep the finite dispatch here: a caller-supplied executable or a
    # generic subprocess wrapper would erase the command boundary.
    if program == "current_python":
        executable = sys.executable
    elif program == "python":
        executable = shutil.which("python", path=environment.get("PATH"))
    elif program == "python3":
        executable = shutil.which("python3", path=environment.get("PATH"))
    elif program == "node":
        executable = shutil.which("node", path=environment.get("PATH"))
    elif program == "npm":
        executable = shutil.which("npm", path=environment.get("PATH"))
    elif program == "npx":
        executable = shutil.which("npx", path=environment.get("PATH"))
    elif program == "pnpm":
        executable = shutil.which("pnpm", path=environment.get("PATH"))
    elif program == "yarn":
        executable = shutil.which("yarn", path=environment.get("PATH"))
    elif program == "bun":
        executable = shutil.which("bun", path=environment.get("PATH"))
    elif program == "cargo":
        executable = shutil.which("cargo", path=environment.get("PATH"))
    elif program == "go":
        executable = shutil.which("go", path=environment.get("PATH"))
    elif program == "make":
        executable = shutil.which("make", path=environment.get("PATH"))
    elif program == "pytest":
        executable = shutil.which("pytest", path=environment.get("PATH"))
    elif program == "lint-imports":
        executable = shutil.which("lint-imports", path=environment.get("PATH"))
    elif program == "uv":
        executable = shutil.which("uv", path=environment.get("PATH"))
    elif program == "ruff":
        executable = shutil.which("ruff", path=environment.get("PATH"))
    elif program == "mypy":
        executable = shutil.which("mypy", path=environment.get("PATH"))
    else:
        raise ValueError("unsupported executable requires ordinary native verification")
    if executable is None or not Path(executable).is_absolute() or os.path.abspath(executable) != resolved:
        raise ValueError("toolchain resolution changed; ordinary native verification is required")
    return subprocess.Popen([executable, *argv[1:]], cwd=snapshot, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False,
                            start_new_session=os.name == "posix")


def run_snapshot_command(argv: list[str], snapshot: Path, environment: dict[str, str], timeout: float,
                         *, expected_executable: str | None = None) -> tuple[int | None, bytes, bytes, bool]:
    """Own the process group, including timeout cleanup; never retry a launch."""
    with open_snapshot_process(argv, snapshot, environment, expected_executable) as process:
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
    if "docker" in inputs:
        from .verification_docker_workflow import execute_docker_verification

        return execute_docker_verification(root, inputs, mode)
    if mode not in {"dry_run", "apply"}:
        raise ValueError("verification execution requires dry_run or apply")
    workflow_name = require_text(inputs.get("workflow_file"), "workflow_file")
    command_id = require_text(inputs.get("command_id"), "command_id")
    workflow = confined_path(root, workflow_name)
    argv = project_command(workflow, command_id)
    executable, toolchain = toolchain_binding(argv)
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
        environment, environment_sha = environment_binding(outputs)
        now = time.time()
        ledger = begun["ledger"]
        remaining = min(7200 - elapsed(ledger, now, ledger["started_at"]),
                        5400 - elapsed(ledger, now, ledger["slice_started_at"]))
        if remaining <= 0:
            raise ValueError("verification budget exhausted while preparing isolated inputs")
        exit_code, stdout, stderr, completed = run_snapshot_command(argv, snapshot, environment, remaining, expected_executable=executable)
        snapshot_unchanged = tree_digest(tree_bytes(snapshot, workflow_name)) == snapshot_sha
    unchanged = tree_digest(tree_bytes(root, workflow_name)) == snapshot_sha
    record = {"schema_version": SCHEMA, "execution_id": execution_id, "dispatch_id": dispatch_id, "command_id": command_id,
              "argv": argv, "workflow_file": workflow_name, "snapshot_sha256": snapshot_sha,
              "environment_sha256": environment_sha, "output_directory": str(outputs), "toolchain": toolchain, "exit_code": exit_code,
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
    for key in ("execution_id", "snapshot_sha256", "environment_sha256", "toolchain", "output_directory"):
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
        output_directory = Path(require_text(record.get("output_directory"), "output_directory"))
        if not output_directory.is_absolute():
            raise ValueError("output_directory must be the absolute executed output path")
        _, environment_sha = environment_binding(output_directory)
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
