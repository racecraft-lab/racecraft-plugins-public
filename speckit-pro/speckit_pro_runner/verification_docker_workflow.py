"""Explicit Docker verification through the durable workflow launch reservation.

This emits a separate image-bound evidence contract, never a host-executable
receipt. Replay of this unqualified contract cannot authorize skipped checks.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
import time
from typing import Any
import uuid

from .execution_control import confined_path, durable_json, elapsed, execution_control, require_text
from .verification_docker import validate_location
from .verification_docker_entrypoint import ENVIRONMENT, validate_argv
from .verification_docker_image import execute_image
from .verification_docker_runtime import DockerClient
from .verification_records import (
    PROJECT_PROGRAMS, digest, evidence_directory, runner_binding, sha, tree_bytes, tree_digest, workflow_argv,
)


def docker_configuration(value: Any) -> dict[str, str]:
    keys = {"executable", "endpoint", "base_image", "output_contract"}
    if not isinstance(value, dict) or set(value) != keys or any(not isinstance(item, str) for item in value.values()):
        raise ValueError("docker requires exactly executable, endpoint, base_image, and output_contract strings")
    validate_location(value["base_image"], value["endpoint"])
    executable = Path(value["executable"])
    if not executable.is_absolute() or executable.name != "docker" or ".." in executable.parts:
        raise ValueError("docker executable must be an explicit absolute Docker path")
    if value["output_contract"] != "streams_only":
        raise ValueError("only streams_only outputs are supported; file artifacts require ordinary verification")
    return dict(value)


def evidence_bytes(value: Any) -> bytes:
    def encode(item: Any) -> dict[str, str]:
        if isinstance(item, bytes):
            return {"base64": base64.b64encode(item).decode("ascii")}
        raise TypeError("unexpected Docker evidence value")
    return (json.dumps(value, default=encode, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")


def docker_workflow_execution(root: Path, workflow_name: str, begun: dict[str, Any], config: dict[str, str],
                              argv: list[str], before: dict[str, tuple[int, bytes | None]], directory: Path,
                              execution_id: str) -> tuple[dict[str, Any], bytes]:
    """No client or image can be created before the caller has begun its reservation."""
    client = None
    result: dict[str, Any] = {"completed": False, "exit_code": None, "stdout": b"", "stderr": b""}
    try:
        now, ledger = time.time(), begun["ledger"]
        remaining = min(7200 - elapsed(ledger, now, ledger["started_at"]),
                        5400 - elapsed(ledger, now, ledger["slice_started_at"]))
        if remaining <= 0:
            raise ValueError("verification budget exhausted before Docker preparation")
        client = DockerClient(Path(config["executable"]), config["endpoint"], directory / "cli")
        result = execute_image(client, before, config["base_image"], argv, execution_id, directory / "image", remaining)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result["failure"] = str(exc)[:240]
    try:
        result["inputs_unchanged"] = tree_digest(tree_bytes(root, workflow_name)) == tree_digest(before)
    except (OSError, ValueError):
        result["inputs_unchanged"] = False
    evidence = evidence_bytes({"configuration": config, "result": result, "events": client.events if client else []})
    return result, evidence


def execute_docker_verification(root: Path, inputs: dict[str, Any], mode: str) -> dict[str, Any]:
    if mode not in {"dry_run", "apply"}:
        raise ValueError("Docker verification execution requires dry_run or apply")
    config = docker_configuration(inputs.get("docker"))
    workflow_name = require_text(inputs.get("workflow_file"), "workflow_file")
    command_id = require_text(inputs.get("command_id"), "command_id")
    argv = workflow_argv(confined_path(root, workflow_name), command_id)
    validate_argv(argv)
    if argv[0] not in PROJECT_PROGRAMS:
        raise ValueError("Docker verification requires a supported image-native tool name; use ordinary native verification")
    before = tree_bytes(root, workflow_name)
    snapshot_sha = tree_digest(before)
    if mode == "dry_run":
        return {"command_id": command_id, "argv": argv, "snapshot_sha256": snapshot_sha,
                "writes_state": False, "authorization_granted": False, "reusable": False,
                "isolation_mode": "docker_readonly_unqualified", "output_contract": "streams_only"}
    dispatch_id = require_text(inputs.get("dispatch_id"), "dispatch_id")
    begun = execution_control(root, {"workflow_file": workflow_name, "action": "begin-verification", "dispatch_id": dispatch_id,
                                    "expected_run_id": inputs.get("expected_run_id"), "ledger_path": inputs.get("ledger_path")}, "apply")
    if begun["disposition"] != "continue":
        raise ValueError("verification launch blocked: " + ", ".join(begun["reasons"]))
    execution_id, started = uuid.uuid4().hex, time.monotonic()
    directory_name = f"{evidence_directory(workflow_name)}/{execution_id}"
    directory = confined_path(root, directory_name)
    directory.parent.mkdir(parents=True, exist_ok=True)
    directory.mkdir(mode=0o700)
    source_binding = runner_binding()
    result, evidence = docker_workflow_execution(root, workflow_name, begun, config, argv, before, directory, execution_id)
    for name, body in (("docker-evidence.json", evidence), ("stdout", result["stdout"]), ("stderr", result["stderr"])):
        with (directory / name).open("xb") as handle:
            handle.write(body)
    record = {"schema_version": "docker-verification-record/v1", "execution_id": execution_id, "dispatch_id": dispatch_id,
              "workflow_file": workflow_name, "command_id": command_id, "argv": argv, "snapshot_sha256": snapshot_sha,
              "inputs_unchanged": result["inputs_unchanged"], "environment_sha256": digest(ENVIRONMENT),
              "input_snapshot_verified": result.get("input_readback", {}).get("verified") is True,
              "toolchain": {"kind": "docker-image", "base_reference": config["base_image"],
                            "base_image_id": result.get("base_image", {}).get("Id"), "image_id": result.get("image_id"),
                            "runner_sha256": source_binding},
              "completed": result["completed"], "exit_code": result["exit_code"], "elapsed_seconds": time.monotonic() - started,
              "stdout_sha256": sha(result["stdout"]), "stderr_sha256": sha(result["stderr"]), "evidence_sha256": sha(evidence),
              "output_directory": str(directory), "output_contract": "streams_only", "isolation_mode": "docker_readonly_unqualified",
              "producer": "runner-docker-project-command/v1"}
    record_name = f"{evidence_directory(workflow_name)}/{execution_id}.json"
    durable_json(confined_path(root, record_name), record)
    return {"record_path": record_name, "record": record, "observation_material": dict(record),
            "evidence_path": f"{directory_name}/docker-evidence.json", "writes_state": True, "reusable": False,
            "authorization_granted": False, "requires_independent_native_event": True, "rerun_required": True,
            "limitations": ["docker_isolation_not_independently_qualified", "independent_producer_qualification_pending",
                            "only_stdout_stderr_retained", "private_context_and_build_cache_may_retain_inputs"]}
