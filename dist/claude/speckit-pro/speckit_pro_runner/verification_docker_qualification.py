"""Docker v2 execution closure and current-state reuse validation."""

from __future__ import annotations

import base64
import json
import math
from pathlib import Path
import re
import tempfile
from typing import Any

from .execution_control import confined_path, require_text
from .verification_records import _read_bounded_regular, digest, evidence_directory, runner_binding, sha, tree_digest, workflow_argv

SCHEMA = "docker-verification-record/v2"
PROFILE = "docker-qualified/v2"
OBSERVATION_SCHEMA = "docker-native-observation/v2"
SHA256 = re.compile(r"[0-9a-f]{64}")
MAX_EVIDENCE_BYTES = 64 * 1024 * 1024
MAX_EVIDENCE_DEPTH = 32
MAX_EVIDENCE_NODES = 200_000
RECORD_KEYS = {"schema_version", "execution_id", "dispatch_id", "workflow_file", "command_id", "argv",
               "snapshot_sha256", "inputs_unchanged", "input_snapshot_verified", "post_input_snapshot_verified",
               "environment_sha256", "configuration", "git_snapshot", "toolchain", "completed", "exit_code",
               "elapsed_seconds", "stdout_sha256", "stderr_sha256", "evidence_sha256", "event_log_sha256",
               "execution_closure_sha256", "revalidation_input_sha256", "output_directory", "output_contract",
               "isolation_mode", "producer"}


def bound_value(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"byte_count": len(value), "sha256": sha(value)}
    if isinstance(value, dict):
        return {key: bound_value(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [bound_value(item) for item in value]
    return value


def base_image_binding(info: dict[str, Any]) -> dict[str, Any]:
    keys = ("Id", "RepoDigests", "Os", "Architecture", "Variant", "RootFS", "Config")
    binding = {key: info.get(key) for key in keys}
    if not isinstance(binding["Id"], str) or not isinstance(binding["RepoDigests"], list):
        raise ValueError("base image identity is incomplete")
    return binding


def event_log_sha256(events: list[dict[str, Any]]) -> str:
    return digest(bound_value(events))


def execution_closure_sha256(configuration: dict[str, Any], git_snapshot: dict[str, Any],
                             result: dict[str, Any], events: list[dict[str, Any]]) -> str:
    excluded = {"execution_closure_sha256", "revalidation_input_sha256", "event_log_sha256", "qualification_reasons"}
    material = {key: value for key, value in result.items() if key not in excluded}
    return digest(bound_value({"configuration": configuration, "git_snapshot": git_snapshot,
                               "result": material, "events": events}))


def revalidation_input_sha256(*, configuration: dict[str, Any], snapshot_sha256: str,
                              git_snapshot: dict[str, Any], argv: list[str], environment_sha256: str,
                              runner_sha256: str, engine_binding: dict[str, Any], base_image: dict[str, Any]) -> str:
    return digest({"configuration": configuration, "snapshot_sha256": snapshot_sha256,
                   "git_snapshot": git_snapshot, "argv": argv, "environment_sha256": environment_sha256,
                   "runner_sha256": runner_sha256, "engine_binding": engine_binding,
                   "base_image": base_image_binding(base_image)})


def event_sequence_reasons(events: Any) -> list[str]:
    expected = [("version",), ("info",), ("image", "inspect"), ("image", "ls"), ("build",),
                ("image", "inspect"), ("ps",), ("create",), ("inspect",), ("cp",), ("start",),
                ("inspect",), ("wait",), ("cp",), ("ps",), ("inspect",), ("rm",), ("ps",),
                ("image", "ls"), ("image", "inspect"), ("image", "rm"), ("image", "ls"),
                ("image", "inspect"), ("version",), ("info",)]
    if not isinstance(events, list) or len(events) != len(expected):
        return ["docker_event_sequence_incomplete"]
    for event, prefix in zip(events, expected):
        if not isinstance(event, dict):
            return ["docker_event_shape_invalid"]
        argv = event.get("argv")
        if (not isinstance(argv, list) or any(not isinstance(item, str) for item in argv)
                or tuple(argv[:len(prefix)]) != prefix):
            return ["docker_event_sequence_changed"]
        if (event.get("timed_out") is not False or event.get("output_limited") is not False
                or type(event.get("exit_code")) is not int or event["exit_code"] != 0):
            return ["docker_event_unsuccessful"]
    return []


def qualification_reasons(result: dict[str, Any], git_snapshot: Any, events: Any) -> list[str]:
    reasons = event_sequence_reasons(events)
    if not isinstance(git_snapshot, dict) or git_snapshot.get("profile") != "git-hermetic-relocated/v2" or git_snapshot.get("qualified") is not True:
        reasons.append("git_snapshot_not_qualified")
    if result.get("engine_before") != result.get("engine_after") or not isinstance(result.get("engine_before"), dict):
        reasons.append("docker_engine_changed_during_execution")
    if result.get("base_image") != result.get("base_image_after") or not isinstance(result.get("base_image"), dict):
        reasons.append("docker_base_image_changed_during_execution")
    if result.get("completed") is not True or result.get("exit_code") != 0:
        reasons.append("command_not_successfully_completed")
    if result.get("inputs_unchanged") is not True:
        reasons.append("source_or_git_changed_during_execution")
    input_readback, post_readback = result.get("input_readback"), result.get("post_input_readback")
    if (not isinstance(input_readback, dict) or input_readback.get("verified") is not True
            or not isinstance(post_readback, dict) or post_readback.get("verified") is not True):
        reasons.append("dual_input_readback_missing")
    if not isinstance(result.get("runtime_attestation"), dict):
        reasons.append("runtime_attestation_missing")
    if result.get("cleanup_confirmed") is not True or result.get("image_tag_cleanup_confirmed") is not True:
        reasons.append("docker_cleanup_unconfirmed")
    return reasons


def observation_material(record_sha256: str, record: dict[str, Any]) -> dict[str, Any]:
    return {"docker_qualification": {"schema_version": OBSERVATION_SCHEMA, "record_sha256": record_sha256,
            **{key: record[key] for key in ("evidence_sha256", "event_log_sha256", "execution_closure_sha256",
                                            "revalidation_input_sha256")}}}


def decode_evidence(body: bytes) -> dict[str, Any]:
    nodes = [0]

    def decode(value: Any, depth: int = 0) -> Any:
        nodes[0] += 1
        if depth > MAX_EVIDENCE_DEPTH or nodes[0] > MAX_EVIDENCE_NODES:
            raise ValueError("Docker evidence structure exceeds its bound")
        if isinstance(value, dict) and set(value) == {"base64"}:
            if not isinstance(value["base64"], str):
                raise ValueError("Docker evidence contains an invalid byte wrapper")
            try:
                return base64.b64decode(value["base64"], validate=True)
            except ValueError as exc:
                raise ValueError("Docker evidence contains invalid base64") from exc
        if isinstance(value, dict):
            if any(not isinstance(key, str) for key in value):
                raise ValueError("Docker evidence contains a non-string object key")
            return {key: decode(item, depth + 1) for key, item in value.items()}
        if isinstance(value, list):
            return [decode(item, depth + 1) for item in value]
        if value is None or type(value) in (bool, int, str) or (type(value) is float and math.isfinite(value)):
            return value
        raise ValueError("Docker evidence contains an unsupported value")
    try:
        value = decode(json.loads(body))
    except (json.JSONDecodeError, UnicodeDecodeError, RecursionError) as exc:
        raise ValueError("Docker evidence is not valid JSON") from exc
    if not isinstance(value, dict) or set(value) != {"configuration", "git_snapshot", "result", "events"}:
        raise ValueError("Docker evidence shape is invalid")
    return value


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
        directory_name = f"{evidence_directory(workflow_name)}/{execution_id}"
        if record.get("output_directory") != directory_name or Path(record_name).stem != execution_id:
            raise ValueError("Docker evidence path is not bound to the execution identity")
        directory = confined_path(root, directory_name)
        evidence_body = _read_bounded_regular(directory / "docker-evidence.json", MAX_EVIDENCE_BYTES,
                                              "retained Docker evidence")
        stdout = _read_bounded_regular(directory / "stdout", MAX_EVIDENCE_BYTES, "retained Docker stdout")
        stderr = _read_bounded_regular(directory / "stderr", MAX_EVIDENCE_BYTES, "retained Docker stderr")
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
        from .verification_docker_workflow import docker_configuration, docker_input_snapshot
        configuration = docker_configuration(evidence["configuration"])
        if configuration.get("qualification_profile") != PROFILE or record.get("configuration") != configuration:
            reasons.append("docker_configuration_changed")
        git_snapshot = record.get("git_snapshot")
        if not isinstance(git_snapshot, dict):
            raise ValueError("qualified Docker record omitted Git binding")
        files, current_git = docker_input_snapshot(root, workflow_name, git_snapshot.get("directories"), qualified=True)
        snapshot_sha256 = tree_digest(files)
        from .verification_docker_entrypoint import QUALIFIED_ENVIRONMENT
        current_runner = runner_binding()
        if (snapshot_sha256 != record.get("snapshot_sha256")
                or digest(QUALIFIED_ENVIRONMENT) != record.get("environment_sha256")
                or current_runner != record.get("toolchain", {}).get("runner_sha256")):
            reasons.append("docker_current_input_closure_changed")
        if reasons:
            return reasons
        from .verification_docker import validate_base_image
        from .verification_docker_image import inspect_image
        from .verification_docker_runtime import DockerClient
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
