"""Install inventory doctor and repair helpers."""

from __future__ import annotations

import hashlib
import json
import platform as platform_module
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

from ..envelope import diagnostic, response
from .mutation import resolve_candidate_path, run_mutation_helper, validate_target_path
from .read_only import find_repo_root, is_relative_to, repo_relative

INVENTORY_NAME = "install_inventory.json"
FAKE_HOME_FIXTURE_ROOT = Path("tests") / "speckit-pro" / "layer4-scripts" / "fixtures"
XPLAT_008_FIXTURE_ROOT = FAKE_HOME_FIXTURE_ROOT / "xplat-008-release"
DEFAULT_RUNNER_INVOCATION_CASES = XPLAT_008_FIXTURE_ROOT / "runner-invocation-cases.json"
MINIMUM_PYTHON = (3, 11, 0)


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
    repo_root = find_repo_root(Path.cwd())
    if repo_root is None:
        return response(
            "missing_prerequisite",
            request_id=request.request_id,
            diagnostics=[diagnostic("missing_prerequisite", "could not locate repository root for install helper request")],
        )

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
        runner_response, execution_diag = execute_runner_runtime_info(invocation["argv"], runner_request, repo_root, cache_root)
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
        invocation_prefix = record_invocation_prefix(record)
        if invocation_prefix is None:
            invocation_prefix = invocation_prefix_for_candidate(platform_name, candidate, resolved)
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
            completed = subprocess.run(
                [*argv, "-c", "import platform, sys; print(platform.python_version()); print(sys.executable)"],
                text=True,
                capture_output=True,
                timeout=5,
                shell=False,
                check=False,
            )
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


def invocation_prefix_for_live_probe(candidate: str, resolved_executable: str) -> list[str]:
    argv = candidate.split()
    if argv and argv[0].lower() == "py":
        return probe_argv_for_candidate(candidate)
    return [resolved_executable]


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
        completed = subprocess.run(
            argv,
            input=json.dumps(runner_request),
            text=True,
            capture_output=True,
            timeout=10,
            shell=False,
            cwd=cwd,
            check=False,
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
        parsed = json.loads(completed.stdout)
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
    promotion_record = "tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/runner-invocation-cases.json"
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
        "artifacts": [{"path": promotion_record, "kind": "fixture"}],
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
    return resolve_candidate_path(raw, repo_root)


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
            "Move the install_root under tests/speckit-pro/layer4-scripts/fixtures.",
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


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_diagnostic(value: Any) -> bool:
    return isinstance(value, dict) and value.get("source") == "runner" and "code" in value
