"""Install inventory doctor and repair helpers."""

from __future__ import annotations

import copy
import json
import os
import platform as platform_module
import re
import stat
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path, PurePosixPath
from typing import Any

from ..envelope import diagnostic, is_diagnostic, response
from ..merge_utils import deep_merge
from ..path_utils import resolves_to_current_python, sha256_text
from .mutation import empty_mutation, operation_record, run_mutation_helper, validate_target_path
from .read_only import find_repo_root, is_relative_to, repo_relative, resolve_input_path

INVENTORY_NAME = "install_inventory.json"
FAKE_HOME_FIXTURE_ROOT = Path("tests") / "speckit-pro" / "unit" / "fixtures"
XPLAT_008_FIXTURE_ROOT = FAKE_HOME_FIXTURE_ROOT / "installed-plugin-release"
DEFAULT_RUNNER_INVOCATION_CASES = XPLAT_008_FIXTURE_ROOT / "runner-invocation-cases.json"
XPLAT_008_PROMOTION_RECORDS = XPLAT_008_FIXTURE_ROOT / "promotion-records.json"
DEFAULT_INSTALL_HEALTH_CASES = XPLAT_008_FIXTURE_ROOT / "install-health-repair-cases.json"
MINIMUM_PYTHON = (3, 11, 0)
REQUIRED_CODEX_AGENT_NAMES = frozenset(
    {
        "analyze-executor.toml",
        "artifact-author.toml",
        "autopilot-fast-helper.toml",
        "checklist-executor.toml",
        "clarify-executor.toml",
        "codebase-analyst.toml",
        "domain-researcher.toml",
        "implement-executor.toml",
        "phase-executor.toml",
        "spec-context-analyst.toml",
        "sweep-analyst.toml",
        "sweep-classifier.toml",
        "uat-runbook-author.toml",
    }
)
SUPPORTED_CODEX_AGENT_MODELS = frozenset({"gpt-5.5", "gpt-5.4"})


def run_runner_invocation_gate(entry: Any, request: Any) -> dict[str, Any]:
    repo_root = find_repo_root(Path.cwd())
    if repo_root is None:
        return response(
            "missing_prerequisite",
            request_id=request.request_id,
            data=runner_invocation_base_data(entry, request.operation, "missing_prerequisite"),
            diagnostics=[diagnostic("missing_prerequisite", "could not locate repository root for runner invocation request")],
        )

    case_result = runner_invocation_case(repo_root, request.inputs)
    if is_diagnostic(case_result):
        return response(
            "input_error",
            request_id=request.request_id,
            data=runner_invocation_base_data(entry, request.operation, "input_error"),
            diagnostics=[case_result],
        )
    case = case_result

    record, diagnostics = runner_invocation_record(case, request.request_id, repo_root)
    passed = record["status"] == "pass"
    status = "ok" if passed else "expected_failure"
    data = runner_invocation_base_data(entry, request.operation, status)
    data["runner_invocation"] = record
    if passed:
        return response("ok", request_id=request.request_id, data=data)

    data["gate"]["gate_status"] = "fail"
    data["gate"]["blocking"] = True
    return response("expected_failure", request_id=request.request_id, data=data, diagnostics=diagnostics)


def run_install_helper(entry: Any, request: Any) -> dict[str, Any]:
    if request.helper_id == "install-codex-agents":
        return run_codex_agent_install(entry, request)

    repo_root = find_repo_root(Path.cwd())
    if repo_root is None:
        return response(
            "missing_prerequisite",
            request_id=request.request_id,
            diagnostics=[diagnostic("missing_prerequisite", "could not locate repository root for install helper request")],
        )

    if request.helper_id == "install-health-repair":
        return run_install_health_repair(entry, request, repo_root)

    install_root_result = install_root_from_inputs(request.inputs, repo_root)
    if isinstance(install_root_result, dict):
        return response("input_error", request_id=request.request_id, diagnostics=[install_root_result])
    install_root = install_root_result

    inventory_result = inventory_from_inputs(request.inputs, repo_root)
    if is_diagnostic(inventory_result):
        return response("input_error", request_id=request.request_id, diagnostics=[inventory_result])
    inventory = inventory_result

    fake_home = request.inputs.get("fake_home") is True
    if fake_home:
        fake_diag = fake_home_boundary_diagnostic(install_root, repo_root)
        if fake_diag is not None:
            return response("input_error", request_id=request.request_id, diagnostics=[fake_diag])

    doctor = doctor_report(install_root, inventory, repo_root, fake_home=fake_home)

    if request.helper_id == "doctor-preflight":
        return response(
            "ok",
            request_id=request.request_id,
            data={
                "helper_id": entry.helper_id,
                "operation": entry.operation,
                "mode": request.mode,
                "promotion_status": entry.promotion_status,
                "comparison_mode": entry.comparison_mode,
                "writes_state": False,
                "doctor": doctor,
            },
        )

    if request.helper_id == "doctor-repair" and request.inputs.get("fake_home") is not True:
        diag = diagnostic(
            "real_home_refused",
            "doctor-repair refuses to mutate a non-fixture home/install root",
            details={"install_root": repo_relative(install_root, repo_root)},
            remediation_summary="Run repair only against a fake-home fixture until active cutover.",
            remediation_actions=["Set fake_home true for tests.", "Use read-only doctor-preflight for real installs."],
        )
        return response("input_error", request_id=request.request_id, data={"doctor": doctor}, diagnostics=[diag])

    repair_ops: list[dict[str, Any]] = []
    for record in inventory["files"]:
        if record["path"] not in doctor["missing_files"] and record["path"] not in doctor["checksum_mismatches"]:
            continue
        target = install_root / record["path"]
        repair_diag = repair_target_boundary_diagnostic(target, install_root, repo_root)
        if repair_diag is not None:
            return response("input_error", request_id=request.request_id, data={"doctor": doctor}, diagnostics=[repair_diag])
        repair_ops.append(
            {
                "operation_id": f"repair:{record['path']}",
                "kind": "write_file",
                "target": target.relative_to(repo_root).as_posix(),
                "content": record["content"],
            }
        )
    return run_mutation_helper(entry, request, operations=repair_ops, extra_data={"doctor": doctor})


def run_codex_agent_install(entry: Any, request: Any) -> dict[str, Any]:
    source_dir = codex_plugin_root() / "codex-agents"
    source_result = load_codex_agent_bundle(source_dir, request.inputs)
    if is_diagnostic(source_result):
        return response("input_error", request_id=request.request_id, diagnostics=[source_result])
    rendered, model = source_result

    destination_result = codex_agent_destination(request.inputs)
    if is_diagnostic(destination_result):
        return response("input_error", request_id=request.request_id, diagnostics=[destination_result])
    destination = destination_result
    unsafe = codex_agent_destination_diagnostic(destination)
    if unsafe is not None:
        return response("input_error", request_id=request.request_id, diagnostics=[unsafe])

    mutation = empty_mutation(request.mode)
    planned: list[tuple[str, Path, bytes]] = []
    for name, content in rendered.items():
        target = destination / name
        operation = {"operation_id": f"install-codex-agent:{name}", "kind": "write_file", "target": target.as_posix()}
        try:
            previous_state = codex_agent_previous_state(target)
        except OSError as exc:
            return response(
                "input_error",
                request_id=request.request_id,
                diagnostics=[
                    diagnostic(
                        "unsafe_agent_destination",
                        "Codex agent destination contains an unsafe managed entry",
                        details={"path": target.as_posix(), "error": str(exc)},
                    )
                ],
            )
        current = previous_state[0] if previous_state is not None else None
        if current == content:
            mutation["no_op_operations"].append(operation_record(operation))
            continue
        planned.append((name, target, content))
        mutation["planned_operations"].append(operation_record(operation))
        mutation["planned_paths"].append(target.as_posix())

    mutation["live_mutation"] = request.mode == "apply" and bool(planned)
    data = codex_agent_install_data(entry, request, mutation, source_dir, destination, model, rendered)
    if request.mode == "dry_run":
        mutation["mutation_status"] = "planned" if planned else "no_op"
        return response("ok", request_id=request.request_id, data=data)

    if not planned:
        mutation["mutation_status"] = "no_op"
        data["restart_required"] = False
        data["verification"] = {"status": "verified", "matched_files": sorted(rendered)}
        return response("ok", request_id=request.request_id, data=data)

    previous: dict[str, tuple[bytes, int] | None] = {}
    destination_existed = destination.exists()
    destination_parent_existed = destination.parent.exists()
    destination_identity: tuple[int, int] | None = None
    failed_name: str | None = None
    try:
        destination.mkdir(parents=True, exist_ok=True)
        unsafe = codex_agent_destination_diagnostic(destination)
        if unsafe is not None:
            raise OSError("destination changed before apply")
        destination_identity = codex_agent_destination_identity(destination)
        for index, (name, target, content) in enumerate(planned):
            failed_name = name
            if not codex_agent_target_is_safe(target, destination, destination_identity):
                raise OSError(f"unsafe destination entry: {name}")
            previous[name] = codex_agent_previous_state(target)
            write_codex_agent_atomic(target, content, destination, destination_identity)
            operation = {"operation_id": f"install-codex-agent:{name}", "kind": "write_file", "target": target.as_posix()}
            mutation["applied_operations"].append(operation_record(operation))
            mutation["touched_paths"].append(target.as_posix())

        mismatches = verify_codex_agent_install(destination, rendered)
        if mismatches:
            raise OSError(f"post-copy verification failed: {', '.join(mismatches)}")
    except OSError as exc:
        rollback_failures = rollback_codex_agent_install(destination, previous, destination_identity)
        cleanup_codex_agent_destination(
            destination,
            destination_existed=destination_existed,
            destination_parent_existed=destination_parent_existed,
        )
        mutation["mutation_status"] = "partial_failure" if rollback_failures else "blocked"
        if failed_name is not None:
            failed_target = destination / failed_name
            mutation["failure_operation"] = operation_record(
                {
                    "operation_id": f"install-codex-agent:{failed_name}",
                    "kind": "write_file",
                    "target": failed_target.as_posix(),
                }
            )
        mutation["manual_remediation"] = (
            ["Restore the reported files manually before retrying."] if rollback_failures else []
        )
        data["writes_state"] = bool(rollback_failures)
        data["rollback_succeeded"] = not rollback_failures
        data["restart_required"] = bool(rollback_failures)
        data["verification"] = {"status": "failed", "matched_files": []}
        return response(
            "expected_failure",
            request_id=request.request_id,
            data=data,
            diagnostics=[
                diagnostic(
                    "codex_agent_install_failed",
                    "Codex agent installation failed and rollback was attempted",
                    details={"error": str(exc), "rollback_failures": rollback_failures},
                    remediation_summary="Inspect the destination and retry after resolving the reported failure.",
                    remediation_actions=mutation["manual_remediation"] or ["Retry the same request in dry_run mode."],
                )
            ],
        )

    mutation["mutation_status"] = "applied"
    data["writes_state"] = True
    data["verification"] = {"status": "verified", "matched_files": sorted(rendered)}
    return response("ok", request_id=request.request_id, data=data)


def codex_plugin_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_codex_agent_bundle(source_dir: Path, inputs: dict[str, Any]) -> tuple[dict[str, bytes], str] | dict[str, Any]:
    raw_model = inputs["model"] if "model" in inputs else os.environ.get("SPECKIT_CODEX_MODEL") or "gpt-5.5"
    if not isinstance(raw_model, str) or raw_model not in SUPPORTED_CODEX_AGENT_MODELS:
        return diagnostic(
            "unsupported_codex_model",
            "model must be gpt-5.5 or gpt-5.4",
            details={"model": raw_model},
            remediation_summary="Choose a supported explicit Codex agent model.",
            remediation_actions=["Set inputs.model to gpt-5.5 or gpt-5.4."],
        )
    if not source_dir.is_dir() or source_dir.is_symlink():
        return diagnostic("missing_agent_bundle", "bundled codex-agents directory is missing or unsafe")
    if any(source_dir.glob("*.md")):
        return diagnostic("legacy_agent_bundle", "bundled codex-agents directory contains legacy Markdown agents")
    source_files = sorted(source_dir.glob("*.toml"), key=lambda path: path.name)
    source_names = {path.name for path in source_files}
    missing = sorted(REQUIRED_CODEX_AGENT_NAMES - source_names)
    unexpected = sorted(source_names - REQUIRED_CODEX_AGENT_NAMES)
    if missing or unexpected:
        return diagnostic(
            "incomplete_agent_bundle",
            "bundled Codex agent set does not match the required inventory",
            details={"missing_files": missing, "unexpected_files": unexpected},
            remediation_summary="Restore the complete bundled agent set before installing.",
            remediation_actions=["Repair or reinstall the SpecKit Pro plugin."],
        )
    rendered: dict[str, bytes] = {}
    try:
        for path in source_files:
            if path.is_symlink() or not path.is_file():
                raise OSError(path.name)
            source_bytes = path.read_bytes()
            source_text = source_bytes.decode("utf-8")
            source_policy = tomllib.loads(source_text)
            if source_policy.get("name") != path.stem:
                raise ValueError(f"{path.name}: name must match filename")
            expected_source_model = "gpt-5.3-codex-spark" if path.name == "autopilot-fast-helper.toml" else "gpt-5.5"
            if source_policy.get("model") != expected_source_model:
                raise ValueError(f"{path.name}: unexpected source model")

            if raw_model == "gpt-5.4" and expected_source_model == "gpt-5.5":
                rendered_text, replacement_count = re.subn(
                    r'^model = "gpt-5\.5"$',
                    'model = "gpt-5.4"',
                    source_text,
                    flags=re.MULTILINE,
                )
                if replacement_count != 1:
                    raise ValueError(f"{path.name}: expected exactly one model rewrite")
                rendered_policy = tomllib.loads(rendered_text)
                if rendered_policy.get("model") != "gpt-5.4":
                    raise ValueError(f"{path.name}: model rewrite did not validate")
                rendered[path.name] = rendered_text.encode("utf-8")
            else:
                rendered[path.name] = source_bytes
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError, ValueError) as exc:
        return diagnostic(
            "unsafe_agent_bundle",
            "bundled Codex agent templates could not be read safely",
            details={"error": type(exc).__name__, "message": str(exc)},
        )
    return rendered, raw_model


def codex_agent_destination(inputs: dict[str, Any]) -> Path | dict[str, Any]:
    default = Path.home() / ".codex" / "agents"
    raw = inputs.get("destination")
    if raw is None:
        candidate = default
    elif not isinstance(raw, str) or not raw.strip():
        return diagnostic("invalid_destination", "destination must be a non-empty path string")
    else:
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
    candidate = candidate.absolute()
    allowed = {
        default.absolute(),
        (Path.cwd() / ".codex" / "agents").absolute(),
    }
    if candidate not in allowed:
        return diagnostic(
            "invalid_destination",
            "destination must be the user or current-project Codex agents directory",
            details={"destination": candidate.as_posix()},
            remediation_summary="Use ~/.codex/agents or .codex/agents.",
            remediation_actions=["Retry with a Codex-native agent destination."],
        )
    return candidate


def codex_agent_destination_diagnostic(destination: Path) -> dict[str, Any] | None:
    for path in (destination, *destination.parents):
        if path.exists() and path.is_symlink():
            return diagnostic(
                "unsafe_agent_destination",
                "Codex agent destination must not traverse symlinks",
                details={"path": path.as_posix()},
            )
        if path == path.parent:
            break
    if destination.exists() and not destination.is_dir():
        return diagnostic("unsafe_agent_destination", "Codex agent destination is not a directory")
    return None


def codex_agent_destination_identity(destination: Path) -> tuple[int, int]:
    metadata = destination.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise OSError("destination is not a stable directory")
    return metadata.st_dev, metadata.st_ino


def codex_agent_previous_state(target: Path) -> tuple[bytes, int] | None:
    try:
        metadata = target.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(metadata.st_mode):
        raise OSError("managed target is not a regular file")

    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(target, flags)
        opened_metadata = os.fstat(descriptor)
        if (opened_metadata.st_dev, opened_metadata.st_ino) != (metadata.st_dev, metadata.st_ino):
            raise OSError("managed target changed while being read")
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = None
            content = handle.read()
            opened_metadata = os.fstat(handle.fileno())
            if (opened_metadata.st_dev, opened_metadata.st_ino) != (metadata.st_dev, metadata.st_ino):
                raise OSError("managed target changed while being read")
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return content, opened_metadata.st_mode


def rollback_codex_agent_install(
    destination: Path,
    previous: dict[str, tuple[bytes, int] | None],
    destination_identity: tuple[int, int] | None,
) -> list[str]:
    failures: list[str] = []
    for name, state in reversed(list(previous.items())):
        target = destination / name
        try:
            if state is None:
                if not codex_agent_target_is_safe(target, destination, destination_identity):
                    raise OSError("rollback target became unsafe")
                if target.exists():
                    target.unlink()
            else:
                content, mode = state
                write_codex_agent_atomic(target, content, destination, destination_identity, mode=mode)
        except OSError:
            failures.append(name)
    return sorted(failures)


def cleanup_codex_agent_destination(
    destination: Path,
    *,
    destination_existed: bool,
    destination_parent_existed: bool,
) -> None:
    for path, existed in ((destination, destination_existed), (destination.parent, destination_parent_existed)):
        if existed:
            continue
        try:
            path.rmdir()
        except OSError:
            # Cleanup is best-effort and must not replace the install or rollback result.
            pass


def write_codex_agent_atomic(
    target: Path,
    content: bytes,
    destination: Path,
    destination_identity: tuple[int, int] | None,
    *,
    mode: int | None = None,
) -> None:
    if not codex_agent_target_is_safe(target, destination, destination_identity):
        raise OSError("unsafe target path")
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{target.name}.",
            suffix=".tmp",
            dir=destination,
            delete=False,
        ) as handle:
            tmp_path = Path(handle.name)
            handle.write(content)
            if mode is not None:
                descriptor_chmod = getattr(os, "fchmod", None)
                if not callable(descriptor_chmod):
                    raise OSError("safe descriptor-based mode restoration is unavailable")
                descriptor_chmod(handle.fileno(), mode & 0o7777)
            handle.flush()
            os.fsync(handle.fileno())
        if codex_agent_destination_identity(destination) != destination_identity:
            raise OSError("destination changed after temporary file creation")
        if not codex_agent_target_is_safe(target, destination, destination_identity):
            raise OSError("target path changed before replace")
        os.replace(tmp_path, target)
        tmp_path = None
        if codex_agent_destination_identity(destination) != destination_identity:
            raise OSError("destination changed during replace")
        installed_state = codex_agent_previous_state(target)
        if installed_state is None or installed_state[0] != content:
            raise OSError("target changed after replace")
        if mode is not None and (installed_state[1] & 0o7777) != (mode & 0o7777):
            raise OSError("target mode changed after replace")
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink()
            except OSError:
                pass


def codex_agent_target_is_safe(
    target: Path,
    destination: Path,
    destination_identity: tuple[int, int] | None,
) -> bool:
    try:
        current_identity = codex_agent_destination_identity(destination)
    except OSError:
        return False
    if destination_identity is None or current_identity != destination_identity or target.parent != destination:
        return False
    try:
        metadata = target.lstat()
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return stat.S_ISREG(metadata.st_mode)


def verify_codex_agent_install(destination: Path, rendered: dict[str, bytes]) -> list[str]:
    mismatches: list[str] = []
    for name, content in rendered.items():
        target = destination / name
        try:
            state = codex_agent_previous_state(target)
            if state is None or state[0] != content:
                mismatches.append(name)
        except OSError:
            mismatches.append(name)
    return sorted(mismatches)


def codex_agent_install_data(
    entry: Any,
    request: Any,
    mutation: dict[str, Any],
    source_dir: Path,
    destination: Path,
    model: str,
    rendered: dict[str, bytes],
) -> dict[str, Any]:
    return {
        "helper_id": entry.helper_id,
        "operation": entry.operation,
        "mode": request.mode,
        "promotion_status": entry.promotion_status,
        "comparison_mode": entry.comparison_mode,
        "writes_state": False,
        "source": source_dir.as_posix(),
        "destination": destination.as_posix(),
        "model": model,
        "agent_files": sorted(rendered),
        "restart_required": request.mode == "apply",
        "verification": {"status": "planned", "matched_files": []},
        "mutation": mutation,
    }


def run_install_health_repair(entry: Any, request: Any, repo_root: Path) -> dict[str, Any]:
    case_result = install_health_case(repo_root, request.inputs)
    if is_diagnostic(case_result):
        return response("input_error", request_id=request.request_id, diagnostics=[case_result])
    case = case_result

    installed_cache_path = str(case.get("installed_cache_path") or "tests/speckit-pro/unit/fixtures/installed-plugin-release/fake-home/speckit-pro")
    findings = normalize_install_health_findings(case.get("findings"))
    repair_actions = normalize_install_health_actions(case.get("repair_actions"), findings)
    failures = install_health_action_failures(repair_actions)
    has_manual = any(action.get("action_type") == "manual_remediation" for action in repair_actions)
    health_status = "fail" if failures else "manual_remediation_required" if has_manual else "pass"
    install_health = {
        "schema_version": "1.0",
        "feature_id": "XPLAT-008",
        "installed_cache_path": installed_cache_path,
        "findings": findings,
        "repair_actions": repair_actions,
        "status": health_status,
    }

    data = {
        "helper_id": entry.helper_id,
        "operation": entry.operation,
        "mode": request.mode,
        "promotion_status": entry.promotion_status,
        "comparison_mode": entry.comparison_mode,
        "writes_state": False,
        "install_health_repair": install_health,
    }
    if failures:
        diag = diagnostic(
            "install_health_repair_blocked",
            "install-health repair evidence includes unsafe autoheal or broad reinstall behavior",
            details={"case_id": case.get("case_id"), "failures": failures},
            remediation_summary="Limit autoheal to trusted checksum-backed artifacts and emit manual remediation for unsafe drift.",
            remediation_actions=["Inspect data.install_health_repair.repair_actions.", "Replace broad reinstall or unverified autoheal actions with manual remediation."],
        )
        return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diag])
    return response("ok", request_id=request.request_id, data=data)


def install_health_case(repo_root: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    raw = inputs.get("case_file", DEFAULT_INSTALL_HEALTH_CASES.as_posix())
    if not isinstance(raw, str) or not raw:
        return diagnostic("invalid_case_file", "case_file must be a non-empty string")
    path = resolve_case_path(raw, repo_root)
    if not is_relative_to(path.resolve(strict=False), repo_root.resolve(strict=False)):
        return diagnostic("invalid_case_file", "case_file must stay inside the repository")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return diagnostic(
            "invalid_case_file",
            "install-health repair case fixture could not be loaded",
            details={"case_file": raw, "error": type(exc).__name__},
        )
    cases = document.get("cases")
    if not isinstance(cases, list):
        return diagnostic("invalid_case_file", "install-health repair fixture must contain cases")
    case_id = inputs.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        case_id = "ready"
    selected = next((item for item in cases if isinstance(item, dict) and item.get("case_id") == case_id), None)
    if selected is None:
        return diagnostic("unknown_fixture_case", "install-health repair fixture case was not found", details={"case_id": case_id})
    base = copy.deepcopy(document.get("base_case", {}))
    if not isinstance(base, dict):
        base = {}
    overrides = selected.get("overrides")
    if isinstance(overrides, dict):
        deep_merge(base, overrides)
    base["case_id"] = case_id
    base["expected_status"] = selected.get("expected_status")
    return base


def normalize_install_health_findings(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    findings: list[dict[str, Any]] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        classification = str(item.get("classification") or "unsafe_unknown")
        artifact_path = normalize_artifact_path(item.get("artifact_path"), fallback=f"unknown-{index}.txt")
        trusted = classification in {"trusted_missing", "trusted_stale"}
        findings.append(
            {
                "finding_id": str(item.get("finding_id") or f"finding-{index}"),
                "artifact_path": artifact_path,
                "artifact_kind": str(item.get("artifact_kind") or ("runner_file" if trusted else "unknown")),
                "source_identity": item.get("source_identity") if isinstance(item.get("source_identity"), str) else None,
                "release_channel_or_tag": item.get("release_channel_or_tag") if isinstance(item.get("release_channel_or_tag"), str) else None,
                "expected_digest": normalize_digest(item.get("expected_digest"), fallback=None),
                "actual_digest": normalize_digest(item.get("actual_digest"), fallback=None),
                "classification": classification,
                "repair_allowed": bool(item.get("repair_allowed")) if "repair_allowed" in item else trusted,
            }
        )
    return findings


def normalize_install_health_actions(raw: Any, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    actions: list[dict[str, Any]] = []
    for finding in findings:
        finding_id = str(finding.get("finding_id"))
        target_path = str(finding.get("artifact_path"))
        if (
            finding.get("classification") in {"trusted_missing", "trusted_stale"}
            and finding.get("repair_allowed") is True
            and has_trusted_repair_evidence(finding)
        ):
            actions.append(
                {
                    "action_id": f"autoheal:{finding_id}",
                    "finding_id": finding_id,
                    "action_type": "autoheal_refresh",
                    "target_path": target_path,
                    "source_path": str(finding.get("source_identity") or "speckit-pro"),
                    "digest_verified": True,
                    "status": "completed",
                    "message": "Trusted checksum-backed artifact refreshed from the source payload inventory.",
                    "manual_steps": [],
                }
            )
            continue
        actions.append(
            {
                "action_id": f"manual:{finding_id}",
                "finding_id": finding_id,
                "action_type": "manual_remediation",
                "target_path": target_path,
                "source_path": None,
                "digest_verified": False,
                "status": "blocked",
                "message": "Unsafe installed-cache drift requires exact manual remediation; autoheal is not allowed.",
                "manual_steps": [
                    f"Inspect installed artifact {target_path}.",
                    "Restore the plugin from a trusted marketplace release or remove the unsafe drift manually.",
                ],
            }
        )
    return actions


def has_trusted_repair_evidence(finding: dict[str, Any]) -> bool:
    for key in ("source_identity", "release_channel_or_tag", "expected_digest"):
        value = finding.get(key)
        if not isinstance(value, str) or not value:
            return False
    return True


def install_health_action_failures(actions: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    for action in actions:
        action_id = str(action.get("action_id") or "unknown-action")
        action_type = action.get("action_type")
        target_path = str(action.get("target_path") or "")
        target_parts = PurePosixPath(target_path.replace("\\", "/")).parts
        broad = action.get("operation_scope") == "broad_reinstall" or target_path in {"", ".", "/"} or "reinstall" in str(action.get("message", "")).lower()
        unsafe_path = target_path.startswith("/") or any(part in {"", ".", ".."} for part in target_parts)
        if action_type == "autoheal_refresh":
            if action.get("status") != "completed" or action.get("digest_verified") is not True or not action.get("source_path") or broad or unsafe_path:
                failures.append(action_id)
        elif action_type == "manual_remediation":
            steps = action.get("manual_steps")
            if action.get("status") != "blocked" or action.get("digest_verified") is not False or not isinstance(steps, list) or not steps:
                failures.append(action_id)
        else:
            failures.append(action_id)
    return failures


def normalize_artifact_path(value: Any, *, fallback: str) -> str:
    text = value if isinstance(value, str) and value else fallback
    return text.replace("\\", "/").lstrip("/")


def normalize_digest(value: Any, *, fallback: str | None) -> str | None:
    text = value if isinstance(value, str) else fallback
    if text is None:
        return None
    return text if len(text) == 64 and all(char in "0123456789abcdef" for char in text) else fallback


def runner_invocation_case(repo_root: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    raw = inputs.get("case_file", DEFAULT_RUNNER_INVOCATION_CASES.as_posix())
    if not isinstance(raw, str) or not raw:
        return diagnostic("invalid_case_file", "case_file must be a non-empty string")
    path = resolve_case_path(raw, repo_root)
    if not is_relative_to(path.resolve(strict=False), repo_root.resolve(strict=False)):
        return diagnostic("invalid_case_file", "case_file must stay inside the repository")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return diagnostic(
            "invalid_case_file",
            "runner invocation case fixture could not be loaded",
            details={"case_file": raw, "error": type(exc).__name__},
        )
    cases = document.get("cases")
    if not isinstance(cases, list):
        return diagnostic("invalid_case_file", "runner invocation fixture must contain cases")
    case_id = inputs.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        case_id = str(cases[0].get("case_id")) if cases and isinstance(cases[0], dict) else ""
    selected = next((item for item in cases if isinstance(item, dict) and item.get("case_id") == case_id), None)
    if selected is None:
        return diagnostic("unknown_fixture_case", "runner invocation fixture case was not found", details={"case_id": case_id})
    return dict(selected)


def runner_invocation_record(case: dict[str, Any], request_id: str | None, repo_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    product = normalize_enum(case.get("product"), {"claude", "codex"}, "claude")
    platform_name = normalize_enum(case.get("platform"), {"windows", "macos", "linux"}, host_platform())
    operation = normalize_enum(
        case.get("operation"),
        {"preflight", "scaffold", "status", "autopilot-dry-run", "doctor", "update", "autoheal"},
        "preflight",
    )
    surface_path = str(case.get("surface_path") or "speckit-pro/skills/speckit-status/SKILL.md")
    cache_root = str(case.get("cache_root") or ".")
    request_id_value = request_id or f"xplat-008-{product}-{platform_name}-{operation}"
    resolution, diagnostics = resolve_python_interpreter(platform_name, case, cache_root)
    fixture_backed = isinstance(case.get("candidate_results"), list)

    runner_request = {
        "schema_version": "1.0",
        "request_id": f"{request_id_value}:runtime-info",
        "helper_id": "runner",
        "operation": "runtime-info",
        "mode": "read_only",
        "inputs": {
            "source": "xplat-008-installed-runtime",
            "product": product,
            "platform": platform_name,
            "surface_path": surface_path,
        },
    }
    accepted = bool(resolution["accepted"])
    invocation = {
        "argv": [*resolution["invocation_argv_prefix"], "-m", "speckit_pro_runner"] if accepted else [],
        "stdin_mode": "single_json_request",
        "stdout_mode": "single_json_response",
        "stderr_mode": "diagnostics_only",
        "shell_used": False,
    }
    runner_response = None
    if accepted and fixture_backed:
        runner_response = {
            "schema_version": "1.0",
            "status": "ok",
            "exit_code": 0,
            "legacy_exit_code": None,
            "diagnostics": [],
            "evidence_source": "fixture",
            "data": {
                "invoked_module": "speckit_pro_runner",
                "cache_root": cache_root,
            },
        }
    elif accepted:
        runner_response, execution_diag = execute_runner_runtime_info(
            invocation["argv"],
            runner_request,
            repo_root,
            cache_root,
            selected_candidate=resolution["attempted_candidates"][-1],
        )
        if execution_diag is not None:
            diagnostics = [execution_diag]
    passed = accepted and not diagnostics
    record = {
        "schema_version": "1.0",
        "request_id": request_id_value,
        "product": product,
        "platform": platform_name,
        "surface_path": surface_path,
        "operation": operation,
        "interpreter_resolution": resolution,
        "invocation": invocation,
        "runner_request": runner_request,
        "runner_response": runner_response,
        "status": "pass" if passed else "blocked",
        "diagnostics": diagnostics,
    }
    return record, diagnostics


def resolve_python_interpreter(platform_name: str, case: dict[str, Any], cache_root: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    raw_results = case.get("candidate_results")
    if isinstance(raw_results, list):
        candidate_records = [item for item in raw_results if isinstance(item, dict)]
    else:
        candidate_records = probe_host_candidates(platform_name)

    attempted: list[str] = []
    last_version: str | None = None
    failure_messages: list[str] = []
    for record in candidate_records:
        candidate = str(record.get("candidate") or "")
        if not candidate:
            continue
        attempted.append(candidate)
        if not allowed_python_candidate(platform_name, candidate):
            failure_messages.append(f"{candidate}: unsupported Python candidate")
            continue
        returncode = int(record.get("returncode", 0)) if isinstance(record.get("returncode", 0), int) else 1
        version = record.get("version")
        version_text = str(version) if isinstance(version, str) and version else None
        if version_text:
            last_version = version_text
        if returncode != 0:
            stderr = str(record.get("stderr") or "candidate failed")
            failure_messages.append(f"{candidate}: {stderr}")
            continue
        if version_text is None:
            failure_messages.append(f"{candidate}: version unavailable")
            continue
        if parse_version(version_text) < MINIMUM_PYTHON:
            failure_messages.append(f"{candidate}: Python {version_text} is below 3.11")
            continue
        resolved = str(record.get("resolved_executable") or candidate.split()[0])
        if not allowed_python_executable(platform_name, resolved):
            failure_messages.append(f"{candidate}: unsupported resolved executable")
            continue
        invocation_prefix = record_invocation_prefix(record)
        if invocation_prefix is None:
            invocation_prefix = invocation_prefix_for_candidate(platform_name, candidate, resolved)
        if not allowed_python_invocation_prefix(platform_name, invocation_prefix):
            failure_messages.append(f"{candidate}: unsupported invocation prefix")
            continue
        return {
            "attempted_candidates": attempted,
            "resolved_executable": resolved,
            "invocation_argv_prefix": invocation_prefix,
            "version": version_text,
            "accepted": True,
            "minimum_version": "3.11",
            "failure_code": None,
            "diagnostic": f"Accepted Python {version_text} for installed cache {cache_root}.",
        }, []

    diag = diagnostic(
        str(case.get("expected_failure_code") or "python_runtime_unavailable"),
        "no Python 3.11+ interpreter was available for installed runner invocation",
        details={"attempted_candidates": attempted, "platform": platform_name, "cache_root": cache_root},
        remediation_summary="Install or expose Python 3.11+ and retry the installed SpecKit Pro workflow.",
        remediation_actions=["Install Python 3.11 or newer.", "Retry without adding a shell wrapper or jq fallback."],
    )
    resolution = {
        "attempted_candidates": attempted or candidate_order(platform_name),
        "resolved_executable": None,
        "invocation_argv_prefix": [],
        "version": last_version,
        "accepted": False,
        "minimum_version": "3.11",
        "failure_code": diag["code"],
        "diagnostic": "; ".join(failure_messages) or "No Python candidates were attempted.",
    }
    return resolution, [diag]


def probe_host_candidates(platform_name: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for candidate in candidate_order(platform_name):
        argv = probe_argv_for_candidate(candidate)
        try:
            completed = probe_python_candidate(candidate)
        except (OSError, subprocess.TimeoutExpired) as exc:
            records.append({"candidate": candidate, "returncode": 1, "stderr": f"{type(exc).__name__}: {exc}"})
            continue
        stdout = completed.stdout.splitlines()
        records.append(
            {
                "candidate": candidate,
                "returncode": int(completed.returncode),
                "version": stdout[0] if stdout else None,
                "resolved_executable": stdout[1] if len(stdout) > 1 else argv[0],
                "invocation_argv_prefix": invocation_prefix_for_live_probe(candidate, stdout[1] if len(stdout) > 1 else argv[0]),
                "stderr": completed.stderr.strip(),
            }
        )
    return records


def probe_python_candidate(candidate: str) -> subprocess.CompletedProcess[str]:
    probe_source = "import platform, sys; print(platform.python_version()); print(sys.executable)"
    if candidate in {"py -V:3", "py -3"}:
        return subprocess.run(
            ["py", "-3", "-c", probe_source],
            text=True,
            capture_output=True,
            timeout=5,
            shell=False,
            check=False,
        )
    if candidate == "python3":
        return subprocess.run(
            ["python3", "-c", probe_source],
            text=True,
            capture_output=True,
            timeout=5,
            shell=False,
            check=False,
        )
    if candidate == "python":
        return subprocess.run(
            ["python", "-c", probe_source],
            text=True,
            capture_output=True,
            timeout=5,
            shell=False,
            check=False,
        )
    raise OSError(f"unsupported Python probe candidate: {candidate}")


def probe_argv_for_candidate(candidate: str) -> list[str]:
    argv = candidate.split()
    if argv[:2] == ["py", "-V:3"]:
        return ["py", "-3"]
    return argv


def record_invocation_prefix(record: dict[str, Any]) -> list[str] | None:
    raw = record.get("invocation_argv_prefix")
    if isinstance(raw, list) and raw and all(isinstance(item, str) and item for item in raw):
        return list(raw)
    return None


def allowed_python_candidate(platform_name: str, candidate: str) -> bool:
    return allowed_python_program(platform_name, candidate.split()[0] if candidate.split() else "")


def allowed_python_invocation_prefix(platform_name: str, prefix: list[str]) -> bool:
    if not prefix:
        return False
    if not allowed_python_program(platform_name, prefix[0]):
        return False
    if len(prefix) == 1:
        return program_name(prefix[0]) != "py"
    return platform_name == "windows" and len(prefix) == 2 and program_name(prefix[0]) == "py" and prefix[1] == "-3"


def allowed_python_executable(platform_name: str, executable: str) -> bool:
    return allowed_python_program(platform_name, executable)


def allowed_python_program(platform_name: str, value: str) -> bool:
    name = program_name(value)
    return (
        name in {"python", "python3"}
        or bool(re.fullmatch(r"python3(?:\.\d+){1,2}", name))
        or (platform_name == "windows" and name == "py")
    )


def program_name(value: str) -> str:
    name = value.replace("\\", "/").rsplit("/", 1)[-1].lower()
    return name.removesuffix(".exe")


def invocation_prefix_for_live_probe(candidate: str, resolved_executable: str) -> list[str]:
    argv = candidate.split()
    if argv and argv[0].lower() == "py":
        return probe_argv_for_candidate(candidate)
    return probe_argv_for_candidate(candidate) if argv else [resolved_executable]


def invocation_prefix_for_candidate(platform_name: str, candidate: str, resolved_executable: str) -> list[str]:
    argv = candidate.split()
    if platform_name == "windows" and argv and argv[0].lower() == "py":
        selector: str | None = None
        if len(argv) > 1:
            selector = "-3" if argv[1] == "-V:3" else argv[1]
        if selector and selector.startswith("-"):
            executable_name = resolved_executable.replace("\\", "/").rsplit("/", 1)[-1].lower()
            if executable_name in {"py", "py.exe"}:
                return [resolved_executable, selector]
    return [resolved_executable]


def execute_runner_runtime_info(
    argv: list[str],
    runner_request: dict[str, Any],
    repo_root: Path,
    cache_root: str,
    *,
    selected_candidate: str | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    cache_path = Path(cache_root.replace("\\", "/"))
    cwd = cache_path if cache_path.is_absolute() else repo_root / cache_path
    if not cwd.is_dir():
        return None, diagnostic(
            "runner_cache_missing",
            "selected installed cache root does not exist",
            details={"cache_root": cache_root},
            remediation_summary="Install or rebuild the plugin payload before claiming installed runner invocation readiness.",
            remediation_actions=["Verify the recorded cache_root exists.", "Repair or reinstall the plugin payload and retry."],
        )
    if not (cwd / "speckit_pro_runner" / "__main__.py").is_file():
        return None, diagnostic(
            "runner_payload_missing",
            "selected installed cache root does not contain speckit_pro_runner",
            details={"cache_root": cache_root},
            remediation_summary="Ship the runner package inside the installed plugin payload.",
            remediation_actions=["Rebuild generated Claude and Codex payloads.", "Verify speckit_pro_runner/__main__.py exists in the installed cache."],
        )
    try:
        completed = run_python_runner_subprocess(
            argv,
            selected_candidate=selected_candidate,
            input_text=json.dumps(runner_request),
            cwd=cwd,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, diagnostic(
            "runner_invocation_failed",
            "selected Python interpreter could not execute speckit_pro_runner",
            details={"error": type(exc).__name__, "cache_root": cache_root},
            remediation_summary="Verify the selected interpreter can run the installed speckit_pro_runner package.",
            remediation_actions=["Run the recorded argv from the installed plugin cache.", "Repair the installed cache or select another Python 3.11+ interpreter."],
        )
    try:
        parsed_value = json.loads(completed.stdout)
    except json.JSONDecodeError:
        parsed = {
            "schema_version": "1.0",
            "status": "subprocess_failure",
            "exit_code": completed.returncode,
            "legacy_exit_code": None,
            "diagnostics": [],
            "data": {
                "stdout_preview": completed.stdout[:200],
                "stderr_preview": completed.stderr[:200],
            },
        }
    else:
        if not isinstance(parsed_value, dict):
            parsed = malformed_runner_response(completed, type(parsed_value).__name__)
            return parsed, diagnostic(
                "runner_response_malformed",
                "selected Python interpreter returned non-object JSON for runner runtime-info",
                details={"exit_code": completed.returncode, "parsed_type": type(parsed_value).__name__},
                remediation_summary="Repair the installed runner payload before claiming invocation readiness.",
                remediation_actions=["Verify the installed runner emits a JSON object envelope.", "Retry after reinstalling or repairing the plugin cache."],
            )
        parsed = parsed_value
    if completed.returncode == 0 and parsed.get("status") == "ok":
        identity_diag = validate_runner_runtime_response(parsed, cwd, cache_root)
        if identity_diag is None:
            return parsed, None
        return parsed, identity_diag
    return parsed, diagnostic(
        "runner_invocation_failed",
        "selected Python interpreter did not return a successful runner runtime-info response",
        details={"exit_code": completed.returncode, "status": parsed.get("status")},
        remediation_summary="Repair the installed runner payload before claiming invocation readiness.",
        remediation_actions=["Inspect runner_response for stdout/stderr diagnostics.", "Retry after reinstalling or repairing the plugin cache."],
    )


def run_python_runner_subprocess(
    argv: list[str],
    *,
    selected_candidate: str | None,
    input_text: str,
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    if selected_candidate in {"py -V:3", "py -3"}:
        if len(argv) < 2 or program_name(argv[0]) != "py" or argv[1] != "-3":
            raise OSError("selected py launcher invocation does not match its validated prefix")
        return subprocess.run(
            ["py", "-3", *argv[2:]],
            input=input_text,
            text=True,
            capture_output=True,
            timeout=10,
            shell=False,
            cwd=cwd,
            check=False,
        )
    if selected_candidate == "python3":
        if not argv or program_name(argv[0]) != "python3":
            raise OSError("selected python3 invocation does not match its validated prefix")
        return subprocess.run(
            ["python3", *argv[1:]],
            input=input_text,
            text=True,
            capture_output=True,
            timeout=10,
            shell=False,
            cwd=cwd,
            check=False,
        )
    if selected_candidate == "python":
        if not argv or program_name(argv[0]) != "python":
            raise OSError("selected python invocation does not match its validated prefix")
        return subprocess.run(
            ["python", *argv[1:]],
            input=input_text,
            text=True,
            capture_output=True,
            timeout=10,
            shell=False,
            cwd=cwd,
            check=False,
        )
    if selected_candidate is not None or not argv or not resolves_to_current_python(argv[0]):
        raise OSError("runner invocation executable is not the active Python interpreter")
    return subprocess.run(
        [sys.executable, *argv[1:]],
        input=input_text,
        text=True,
        capture_output=True,
        timeout=10,
        shell=False,
        cwd=cwd,
        check=False,
    )


def malformed_runner_response(completed: subprocess.CompletedProcess[str], parsed_type: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "status": "subprocess_failure",
        "exit_code": completed.returncode,
        "legacy_exit_code": None,
        "diagnostics": [],
        "data": {
            "stdout_preview": completed.stdout[:200],
            "stderr_preview": completed.stderr[:200],
            "parsed_type": parsed_type,
        },
    }


def validate_runner_runtime_response(parsed: dict[str, Any], cwd: Path, cache_root: str) -> dict[str, Any] | None:
    data = parsed.get("data")
    report = data.get("report") if isinstance(data, dict) else None
    if not isinstance(report, dict):
        return runner_identity_mismatch(cache_root, "runner runtime-info response did not include a report")

    expected = {
        "runner_name": "speckit_pro_runner",
        "runner_contract_id": "speckit-pro-runner",
        "selected_runtime_name": "python-stdlib-runner",
        "source_vs_installed_context": "installed_payload",
    }
    for key, value in expected.items():
        if report.get(key) != value:
            return runner_identity_mismatch(
                cache_root,
                "runner runtime-info response did not match installed runner identity",
                details={"field": key, "expected": value, "actual": report.get(key)},
            )

    paths = report.get("paths")
    if not isinstance(paths, dict):
        return runner_identity_mismatch(cache_root, "runner runtime-info response did not include path records")

    required_paths = {
        "plugin_root": ".",
        "runner_package": "speckit_pro_runner",
        "manifest_file": "speckit_pro_runner/speckit-pro-runner.manifest.json",
        "checksum_file": "speckit_pro_runner/speckit-pro-runner.sha256",
    }
    for key, expected_value in required_paths.items():
        record = paths.get(key)
        if not isinstance(record, dict) or record.get("value") != expected_value:
            return runner_identity_mismatch(
                cache_root,
                "runner runtime-info response path records did not match installed payload layout",
                details={
                    "field": key,
                    "expected": expected_value,
                    "actual": record.get("value") if isinstance(record, dict) else None,
                },
            )
        if key != "plugin_root" and not (cwd / expected_value).exists():
            return runner_identity_mismatch(
                cache_root,
                "runner runtime-info response path record does not exist in installed payload",
                details={"field": key, "path": expected_value},
            )
    return None


def runner_identity_mismatch(cache_root: str, message: str, *, details: dict[str, Any] | None = None) -> dict[str, Any]:
    merged_details: dict[str, Any] = {"cache_root": cache_root}
    if details:
        merged_details.update(details)
    return diagnostic(
        "runner_identity_mismatch",
        message,
        details=merged_details,
        remediation_summary="Ensure the selected installed cache executes the shipped SpecKit Pro runner package.",
        remediation_actions=[
            "Rebuild generated Claude and Codex payloads.",
            "Verify runtime-info reports the expected runner identity and installed payload paths.",
        ],
    )


def candidate_order(platform_name: str) -> list[str]:
    if platform_name == "windows":
        return ["py -V:3", "py -3", "python", "python3"]
    return ["python3", "python"]


def host_platform() -> str:
    system = platform_module.system().lower()
    if system.startswith("win"):
        return "windows"
    if system == "darwin":
        return "macos"
    return "linux"


def parse_version(version: str) -> tuple[int, int, int]:
    parts: list[int] = []
    for part in version.split(".")[:3]:
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)  # type: ignore[return-value]


def normalize_enum(value: Any, allowed: set[str], fallback: str) -> str:
    text = value if isinstance(value, str) else fallback
    return text if text in allowed else fallback


def runner_invocation_base_data(entry: Any, operation: str, status: str) -> dict[str, Any]:
    gate_status = "pass"
    if status in {"expected_failure", "subprocess_failure"}:
        gate_status = "fail"
    elif status == "missing_prerequisite":
        gate_status = "skipped"
    elif status == "input_error":
        gate_status = "input_error"
    promotion_record = XPLAT_008_PROMOTION_RECORDS.as_posix()
    case_file = DEFAULT_RUNNER_INVOCATION_CASES.as_posix()
    return {
        "gate": {
            "gate_id": entry.helper_id,
            "operation": operation,
            "gate_status": gate_status,
            "promoted": status != "input_error",
            "blocking": status != "ok",
            "comparison_ids": [f"xplat-008-{operation}"],
            "promotion_record": promotion_record,
        },
        "artifacts": [
            {"path": promotion_record, "kind": "promotion_record"},
            {"path": case_file, "kind": "fixture"},
        ],
    }


def install_root_from_inputs(inputs: dict[str, Any], repo_root: Path) -> Path | dict[str, Any]:
    raw = inputs.get("install_root")
    if not isinstance(raw, str) or not raw:
        return diagnostic(
            "invalid_input",
            "install_root is required",
            details={"field": "install_root"},
            remediation_summary="Send a repo-relative fake install root for fixture-backed repair.",
            remediation_actions=["Set install_root to a directory inside the repo fixture tree."],
        )
    path_diag = validate_target_path(f"{raw}/.speckit-pro-install-probe", repo_root)
    if path_diag is not None:
        return path_diag
    return resolve_input_path(raw, repo_root)


def resolve_case_path(raw: str, repo_root: Path) -> Path:
    path = Path(raw.replace("\\", "/"))
    return path if path.is_absolute() else repo_root / path


def inventory_from_inputs(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    raw = inputs.get("inventory")
    if raw is None:
        inventory_path = repo_root / "speckit-pro" / "speckit_pro_runner" / INVENTORY_NAME
        try:
            raw = json.loads(inventory_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return diagnostic(
                "malformed_inventory",
                "install inventory could not be loaded",
                details={"path": repo_relative(inventory_path, repo_root), "error": type(exc).__name__},
                remediation_summary="Refresh the committed install inventory.",
                remediation_actions=["Regenerate install_inventory.json.", "Retry doctor-preflight."],
            )
    if not isinstance(raw, dict):
        return malformed_inventory("inventory must be an object")
    files = raw.get("files")
    if not isinstance(files, list):
        return malformed_inventory("inventory.files must be an array")
    normalized_files: list[dict[str, str]] = []
    for index, item in enumerate(files):
        if not isinstance(item, dict):
            return malformed_inventory("inventory file records must be objects", index=index)
        path = item.get("path")
        content = item.get("content")
        digest = item.get("sha256", "skip")
        if not isinstance(path, str) or not path:
            return malformed_inventory("inventory file path must be repo-relative without traversal", index=index)
        normalized_path = path.replace("\\", "/")
        parts = PurePosixPath(normalized_path).parts
        if normalized_path.startswith("/") or any(part in {"", ".", ".."} for part in parts):
            return malformed_inventory("inventory file path must be repo-relative without traversal", index=index)
        if not isinstance(content, str):
            return malformed_inventory("inventory file content must be a string", index=index)
        if not isinstance(digest, str) or not digest:
            return malformed_inventory("inventory sha256 must be a string", index=index)
        normalized_files.append({"path": normalized_path, "content": content, "sha256": digest})
    return {"files": normalized_files}


def fake_home_boundary_diagnostic(install_root: Path, repo_root: Path) -> dict[str, Any] | None:
    allowed_root = repo_root / FAKE_HOME_FIXTURE_ROOT
    if is_relative_to(install_root.resolve(strict=False), allowed_root.resolve(strict=False)):
        return None
    return diagnostic(
        "fake_home_boundary_refused",
        "fake_home true is only trusted inside the fixture fake-home boundary",
        details={"install_root": repo_relative(install_root, repo_root), "allowed_root": repo_relative(allowed_root, repo_root)},
        remediation_summary="Use fake_home only with repo fixture roots until active install cutover.",
        remediation_actions=[
            "Move the install_root under tests/speckit-pro/unit/fixtures.",
            "Use doctor-preflight without fake_home for real installs.",
        ],
    )


def repair_target_boundary_diagnostic(target: Path, install_root: Path, repo_root: Path) -> dict[str, Any] | None:
    if is_relative_to(target.resolve(strict=False), install_root.resolve(strict=False)):
        return None
    return diagnostic(
        "install_root_escape",
        "repair target escapes the selected install_root",
        details={"target": repo_relative(target, repo_root), "install_root": repo_relative(install_root, repo_root)},
        remediation_summary="Keep install inventory repair paths inside install_root.",
        remediation_actions=["Remove traversal from the inventory path.", "Retry doctor-repair with a normalized inventory."],
    )


def malformed_inventory(message: str, *, index: int | None = None) -> dict[str, Any]:
    details: dict[str, Any] = {}
    if index is not None:
        details["file_index"] = index
    return diagnostic(
        "malformed_inventory",
        message,
        details=details,
        remediation_summary="Use the committed install inventory schema.",
        remediation_actions=["Inspect install_inventory.json.", "Retry with files containing path, content, and sha256."],
    )


def doctor_report(install_root: Path, inventory: dict[str, Any], repo_root: Path, *, fake_home: bool) -> dict[str, Any]:
    missing: list[str] = []
    mismatches: list[str] = []
    for record in inventory["files"]:
        target = install_root / record["path"]
        if not target.is_file():
            missing.append(record["path"])
            continue
        digest = record["sha256"]
        if digest != "skip" and sha256_text(target.read_text(encoding="utf-8", errors="replace")) != digest:
            mismatches.append(record["path"])

    status = "complete"
    if missing or mismatches:
        status = "safe_repair" if fake_home else "blocked"
    return {
        "status": status,
        "install_root": repo_relative(install_root, repo_root),
        "fake_home": fake_home,
        "missing_files": missing,
        "checksum_mismatches": mismatches,
        "safe_repairs": missing + mismatches if fake_home else [],
        "unsafe_manual_remediations": [] if fake_home else missing + mismatches,
        "blocked": bool((missing or mismatches) and not fake_home),
        "inventory_file_count": len(inventory["files"]),
    }
