"""Explicit Docker verification through the durable workflow launch reservation.

This emits a separate image-bound evidence contract, never a host-executable
receipt. Replay of this unqualified contract cannot authorize skipped checks.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
import tempfile
import time
from typing import Any
import uuid

from .execution_control import (confined_path, durable_json, evidence_directory, execution_control, ignore_owned_directory,
                                record_failing_checks, require_text, worktree_evidence)
from .failing_checks import fingerprint as failing_check_fingerprint
from .verification_docker import validate_base_image, validate_location
from .verification_docker_entrypoint import ENVIRONMENT, QUALIFIED_ENVIRONMENT, validate_argv
from .verification_docker_image import execute_image, inspect_image
from .verification_docker_runtime import DockerClient
from .verification_git import capture_git_metadata
from .verification_docker_qualification import (
    MAX_EVIDENCE_BYTES, PROFILE, RECORD_KEYS, SCHEMA, SHA256, decode_evidence, event_log_sha256, execution_closure_sha256,
    observation_material, qualification_reasons, revalidation_input_sha256,
)
from .verification_evidence import (
    COMMAND_TIMEOUT_SECONDS, MAX_BYTES, MAX_FILES, PROJECT_PROGRAMS, digest, evidence_directories, read_bounded_regular,
    runner_binding, sha, tree_bytes, tree_digest, workflow_argv,
)


def docker_configuration(value: Any) -> dict[str, str]:
    keys = {"executable", "endpoint", "base_image", "output_contract"}
    allowed = (keys, keys | {"qualification_profile"})
    if (not isinstance(value, dict) or set(value) not in allowed
            or any(not isinstance(item, str) for item in value.values())):
        raise ValueError("docker requires exact string configuration fields")
    if "qualification_profile" in value and value["qualification_profile"] != PROFILE:
        raise ValueError("unsupported Docker qualification profile")
    validate_location(value["base_image"], value["endpoint"])
    executable = Path(value["executable"])
    if not executable.is_absolute() or executable.name != "docker" or ".." in executable.parts:
        raise ValueError("docker executable must be an explicit absolute Docker path")
    if value["output_contract"] != "streams_only":
        raise ValueError("only streams_only outputs are supported; file artifacts require ordinary verification")
    return dict(value)


def docker_input_snapshot(root: Path, workflow_name: str, git_settings: Any = None, *, qualified: bool = False) -> tuple[dict, dict | None]:
    """Include Git only with explicit source authority, within one combined bound."""
    files = tree_bytes(root, workflow_name)
    binding = None
    if git_settings is not None:
        metadata, binding = capture_git_metadata(root, git_settings, qualified=qualified)
        if files.keys() & metadata.keys():
            raise ValueError("Git metadata collides with project inputs")
        files.update(metadata)
    if len(files) > MAX_FILES or sum(len(body) for _, body in files.values() if body is not None) > MAX_BYTES:
        raise ValueError("combined Docker input closure exceeds bounded snapshot; use ordinary verification")
    return files, binding


def evidence_bytes(value: Any) -> bytes:
    def encode(item: Any) -> dict[str, str]:
        if isinstance(item, bytes):
            return {"base64": base64.b64encode(item).decode("ascii")}
        raise TypeError("unexpected Docker evidence value")
    return (json.dumps(value, default=encode, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")


def docker_workflow_execution(root: Path, workflow_name: str, begun: dict[str, Any], config: dict[str, str],
                              argv: list[str], snapshot: tuple[dict, dict | None], directory: Path,
                              execution_id: str) -> tuple[dict[str, Any], bytes]:
    """No client or image can be created before the caller has begun its reservation."""
    before, git_binding = snapshot
    client = None
    result: dict[str, Any] = {"completed": False, "exit_code": None, "stdout": b"", "stderr": b""}
    try:
        client = DockerClient(Path(config["executable"]), config["endpoint"], directory / "cli")
        qualified = config.get("qualification_profile") == PROFILE
        client.qualified = qualified
        if qualified:
            result["engine_before"] = client.engine_binding()
        image_result = execute_image(client, before, config["base_image"], argv, execution_id, directory / "image", COMMAND_TIMEOUT_SECONDS)
        result.update(image_result)
        if qualified:
            result["base_image_after"] = inspect_image(client, config["base_image"])
            validate_base_image(result["base_image_after"], config["base_image"])
            result["engine_after"] = client.engine_binding()
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result["failure"] = str(exc)[:240]
        result["completed"], result["exit_code"] = False, None
    try:
        after, after_binding = docker_input_snapshot(root, workflow_name, git_binding["directories"] if git_binding else None,
                                                     qualified=config.get("qualification_profile") == PROFILE)
        result["inputs_unchanged"] = tree_digest(after) == tree_digest(before) and after_binding == git_binding
    except (OSError, ValueError):
        result["inputs_unchanged"] = False
    evidence = evidence_bytes({"configuration": config, "git_snapshot": git_binding,
                               "result": result, "events": client.events if client else []})
    return result, evidence


def qualified_evidence(config: dict[str, str], git_binding: dict[str, Any], result: dict[str, Any],
                       evidence: bytes, snapshot_sha: str, argv: list[str], source_binding: str,
                       execution_id: str) -> bytes:
    events = decode_evidence(evidence)["events"]
    result["event_log_sha256"] = event_log_sha256(events)
    result["execution_closure_sha256"] = execution_closure_sha256(config, git_binding, result, events)
    try:
        result["revalidation_input_sha256"] = revalidation_input_sha256(
            configuration=config, snapshot_sha256=snapshot_sha, git_snapshot=git_binding, argv=argv,
            environment_sha256=digest(QUALIFIED_ENVIRONMENT), runner_sha256=source_binding,
            engine_binding=result["engine_before"], base_image=result["base_image"])
    except (ValueError, KeyError, TypeError):
        result["revalidation_input_sha256"] = digest({"incomplete_qualified_execution": execution_id})
    result["qualification_reasons"] = qualification_reasons(result, git_binding, events)
    return evidence_bytes({"configuration": config, "git_snapshot": git_binding, "result": result, "events": events})


def verification_record(config: dict[str, str], workflow_name: str, command_id: str, argv: list[str],
                        snapshot_sha: str, result: dict[str, Any], source_binding: str, execution_id: str,
                        dispatch_id: str, directory: Path, directory_name: str, elapsed_seconds: float,
                        evidence: bytes, git_binding: dict[str, Any] | None) -> dict[str, Any]:
    environment = QUALIFIED_ENVIRONMENT if config.get("qualification_profile") == PROFILE else ENVIRONMENT
    record = {"schema_version": "docker-verification-record/v1", "execution_id": execution_id, "dispatch_id": dispatch_id,
              "workflow_file": workflow_name, "command_id": command_id, "argv": argv, "snapshot_sha256": snapshot_sha,
              "inputs_unchanged": result["inputs_unchanged"], "environment_sha256": digest(environment),
              "input_snapshot_verified": result.get("input_readback", {}).get("verified") is True,
              "toolchain": {"kind": "docker-image", "base_reference": config["base_image"],
                            "base_image_id": result.get("base_image", {}).get("Id"), "image_id": result.get("image_id"),
                            "runner_sha256": source_binding},
              "completed": result["completed"], "exit_code": result["exit_code"], "elapsed_seconds": elapsed_seconds,
              "stdout_sha256": sha(result["stdout"]), "stderr_sha256": sha(result["stderr"]), "evidence_sha256": sha(evidence),
              "output_directory": str(directory), "output_contract": "streams_only", "isolation_mode": "docker_readonly_unqualified",
              "producer": "runner-docker-project-command/v1"}
    if config.get("qualification_profile") == PROFILE:
        record.update(schema_version="docker-verification-record/v2", configuration=config, git_snapshot=git_binding,
                      post_input_snapshot_verified=result.get("post_input_readback", {}).get("verified") is True,
                      event_log_sha256=result["event_log_sha256"], execution_closure_sha256=result["execution_closure_sha256"],
                      revalidation_input_sha256=result["revalidation_input_sha256"], output_directory=directory_name,
                      isolation_mode="docker_readonly_qualified", producer="runner-docker-project-command/v2")
        record["toolchain"].update(cli=result.get("engine_before", {}).get("cli"), engine=result.get("engine_before"),
                                   base_image=result.get("base_image"))
    return record


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
    git_settings = inputs.get("git_snapshot")
    qualified = config.get("qualification_profile") == PROFILE
    if qualified and git_settings is None:
        raise ValueError("qualified Docker verification requires an explicit Git snapshot")
    before, git_binding = docker_input_snapshot(root, workflow_name, git_settings, qualified=qualified)
    snapshot_sha = tree_digest(before)
    head_evidence = worktree_evidence(root)
    if mode == "dry_run":
        result = {"command_id": command_id, "argv": argv, "snapshot_sha256": snapshot_sha, "git_snapshot": git_binding,
                  "writes_state": False, "authorization_granted": False, "reusable": False,
                  "isolation_mode": "docker_readonly_qualified" if qualified else "docker_readonly_unqualified",
                  "output_contract": "streams_only"}
        if qualified:
            result["qualification_profile"] = PROFILE
        return result
    dispatch_id = require_text(inputs.get("dispatch_id"), "dispatch_id")
    begun = execution_control(root, {"workflow_file": workflow_name, "action": "begin-verification", "dispatch_id": dispatch_id,
                                    "expected_run_id": inputs.get("expected_run_id"), "ledger_path": inputs.get("ledger_path")}, "apply")
    if begun["disposition"] != "continue":
        raise ValueError("verification launch blocked: " + ", ".join(begun["reasons"]))
    execution_id, started = uuid.uuid4().hex, time.monotonic()
    directory_name = f"{evidence_directory(workflow_name)}/{execution_id}"
    directory = confined_path(root, directory_name)
    ignore_owned_directory(directory.parent)
    directory.mkdir(mode=0o700)
    source_binding = runner_binding()
    result, evidence = docker_workflow_execution(root, workflow_name, begun, config, argv,
                                               (before, git_binding), directory, execution_id)
    if qualified:
        evidence = qualified_evidence(config, git_binding, result, evidence, snapshot_sha, argv, source_binding, execution_id)
    for name, body in (("docker-evidence.json", evidence), ("stdout", result["stdout"]), ("stderr", result["stderr"])):
        with (directory / name).open("xb") as handle:
            handle.write(body)
    record = verification_record(config, workflow_name, command_id, argv, snapshot_sha, result, source_binding,
                                 execution_id, dispatch_id, directory, directory_name, time.monotonic() - started,
                                 evidence, git_binding)
    record_name = f"{evidence_directory(workflow_name)}/{execution_id}.json"
    record_path = confined_path(root, record_name)
    durable_json(record_path, record)
    record_failing_checks(root, {**inputs, "workflow_file": workflow_name},
                          {**failing_check_fingerprint(command_id, argv, result["exit_code"], result["completed"],
                                                       result["stdout"], result["stderr"]), **head_evidence})
    observation = observation_material(sha(record_path.read_bytes()), record) if qualified else dict(record)
    return {"record_path": record_name, "record": record, "observation_material": observation,
            "evidence_path": f"{directory_name}/docker-evidence.json", "writes_state": True, "reusable": False,
            "authorization_granted": False, "requires_independent_native_event": True, "rerun_required": True,
            "limitations": (["independent_parent_validation_required", "private_context_and_build_cache_may_retain_inputs"]
                            if qualified else ["docker_isolation_not_independently_qualified", "independent_producer_qualification_pending",
                                               "only_stdout_stderr_retained", "private_context_and_build_cache_may_retain_inputs"])
                           + (git_binding["limitations"] if git_binding else [])}


def validate_docker_record(root: Path, workflow_name: str, command_id: str, record_name: str,
                           record_body: bytes, record: dict[str, Any], observation: Any) -> list[str]:
    reasons: list[str] = []
    try:
        if set(record) != RECORD_KEYS or record.get("schema_version") != SCHEMA:
            raise ValueError("invalid Docker verification record version")
        if any(SHA256.fullmatch(record.get(key, "")) is None for key in (
                "snapshot_sha256", "environment_sha256", "stdout_sha256", "stderr_sha256", "evidence_sha256",
                "event_log_sha256", "execution_closure_sha256", "revalidation_input_sha256")):
            raise ValueError("Docker verification record contains a malformed digest")
        if record.get("output_contract") != "streams_only" or record.get("isolation_mode") != "docker_readonly_qualified" or record.get("producer") != "runner-docker-project-command/v2":
            raise ValueError("Docker verification record contract is not qualified v2")
        execution_id = require_text(record.get("execution_id"), "execution_id")
        record_directory = Path(record_name).parent.as_posix()
        directory_name = f"{record_directory}/{execution_id}"
        if (record_directory not in evidence_directories(workflow_name) or record.get("output_directory") != directory_name
                or Path(record_name).stem != execution_id):
            raise ValueError("Docker evidence path is not bound to the execution identity")
        directory = confined_path(root, directory_name)
        evidence_body = read_bounded_regular(directory / "docker-evidence.json", MAX_EVIDENCE_BYTES,
                                              "retained Docker evidence")
        stdout = read_bounded_regular(directory / "stdout", MAX_EVIDENCE_BYTES, "retained Docker stdout")
        stderr = read_bounded_regular(directory / "stderr", MAX_EVIDENCE_BYTES, "retained Docker stderr")
        expected_observation = observation_material(sha(record_body), record)
        if (not isinstance(observation, dict) or set(observation) != {"native_event_id", "docker_qualification"}
                or not isinstance(observation.get("native_event_id"), str) or not observation["native_event_id"].strip()):
            reasons.append("missing_independent_native_event")
        elif {"docker_qualification": observation.get("docker_qualification")} != expected_observation:
            reasons.append("native_event_disagrees_with_docker_closure")
        evidence = decode_evidence(evidence_body)
        result, events = evidence["result"], evidence["events"]
        if (not isinstance(result, dict) or not isinstance(events, list)
                or not isinstance(evidence.get("configuration"), dict)
                or not isinstance(evidence.get("git_snapshot"), dict)):
            raise ValueError("Docker evidence result or events are invalid")
        if sha(evidence_body) != record.get("evidence_sha256") or sha(stdout) != record.get("stdout_sha256") or sha(stderr) != record.get("stderr_sha256"):
            reasons.append("retained_docker_output_changed")
        if result.get("stdout") != stdout or result.get("stderr") != stderr:
            reasons.append("retained_streams_disagree_with_evidence")
        if evidence.get("git_snapshot") != record.get("git_snapshot"):
            reasons.append("git_snapshot_disagrees_with_evidence")
        toolchain = record.get("toolchain")
        if (not isinstance(toolchain, dict) or set(toolchain) != {"kind", "base_reference", "base_image_id", "image_id",
                                                    "runner_sha256", "cli", "engine", "base_image"}
                or toolchain.get("kind") != "docker-image"
                or toolchain.get("base_reference") != record.get("configuration", {}).get("base_image")
                or toolchain.get("base_image_id") != result.get("base_image", {}).get("Id")
                or toolchain.get("image_id") != result.get("image_id")
                or toolchain.get("engine") != result.get("engine_before")
                or toolchain.get("cli") != result.get("engine_before", {}).get("cli")
                or toolchain.get("base_image") != result.get("base_image")):
            reasons.append("docker_toolchain_disagrees_with_evidence")
        input_readback, post_readback = result.get("input_readback"), result.get("post_input_readback")
        if (not isinstance(input_readback, dict) or not isinstance(post_readback, dict)
                or record.get("input_snapshot_verified") is not (input_readback.get("verified") is True)
                or record.get("post_input_snapshot_verified") is not (post_readback.get("verified") is True)):
            reasons.append("docker_readback_receipt_disagrees_with_evidence")
        event_sha = event_log_sha256(events)
        closure_sha = execution_closure_sha256(evidence["configuration"], evidence["git_snapshot"], result, events)
        if event_sha != record.get("event_log_sha256") or closure_sha != record.get("execution_closure_sha256"):
            reasons.append("docker_execution_closure_changed")
        computed_qualification_reasons = qualification_reasons(result, evidence["git_snapshot"], events)
        reasons.extend(computed_qualification_reasons)
        if result.get("qualification_reasons") != computed_qualification_reasons:
            reasons.append("docker_qualification_receipt_changed")
        if reasons:
            return reasons
        if (record.get("workflow_file"), record.get("command_id"), record.get("argv")) != (
                workflow_name, command_id, workflow_argv(confined_path(root, workflow_name), command_id)):
            reasons.append("command_binding_changed")
        configuration = docker_configuration(evidence["configuration"])
        if configuration.get("qualification_profile") != PROFILE or record.get("configuration") != configuration:
            reasons.append("docker_configuration_changed")
        git_snapshot = record.get("git_snapshot")
        if not isinstance(git_snapshot, dict):
            raise ValueError("qualified Docker record omitted Git binding")
        files, current_git = docker_input_snapshot(root, workflow_name, git_snapshot.get("directories"), qualified=True)
        snapshot_sha256 = tree_digest(files)
        current_runner = runner_binding()
        if (snapshot_sha256 != record.get("snapshot_sha256")
                or digest(QUALIFIED_ENVIRONMENT) != record.get("environment_sha256")
                or current_runner != record.get("toolchain", {}).get("runner_sha256")):
            reasons.append("docker_current_input_closure_changed")
        if reasons:
            return reasons
        with tempfile.TemporaryDirectory(prefix="speckit-docker-validation-") as temporary:
            client = DockerClient(Path(configuration["executable"]), configuration["endpoint"], Path(temporary) / "cli")
            engine = client.engine_binding()
            base = inspect_image(client, configuration["base_image"])
            validate_base_image(base, configuration["base_image"])
            if client.engine_binding() != engine:
                raise ValueError("Docker engine changed during current-state validation")
        current_sha = revalidation_input_sha256(configuration=configuration, snapshot_sha256=snapshot_sha256,
                                                git_snapshot=current_git, argv=record["argv"],
                                                environment_sha256=digest(QUALIFIED_ENVIRONMENT), runner_sha256=current_runner,
                                                engine_binding=engine, base_image=base)
        if current_sha != record.get("revalidation_input_sha256"):
            reasons.append("docker_current_input_closure_changed")
        if record.get("inputs_unchanged") is not True or record.get("completed") is not True or record.get("exit_code") != 0:
            reasons.append("docker_verification_not_successful")
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError) as exc:
        reasons.append(f"unverifiable_docker_record: {str(exc)[:160]}")
    return reasons
