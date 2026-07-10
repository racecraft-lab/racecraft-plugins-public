"""Repo-local suite gate operations for XPLAT-007 US1."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..envelope import diagnostic, response

CAPTURE_LIMIT_BYTES = 16 * 1024
DEFAULT_TIMEOUT_SECONDS = 300
PROMOTION_RECORD = "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/promotion-records.json"
LAYER_SCRIPT_DISPATCHER = "tests/speckit-pro/run-layer-scripts.py"
LAYER_SCRIPT_TIMEOUT_SECONDS = 1800
SUITE_MANIFEST_PATH = "tests/speckit-pro/suite-manifest.json"
TOOLCHAIN_CHECKER = "tests/speckit-pro/check-toolchain.py"
TOOLCHAIN_MODES = {"tests", "shell", "docs", "all"}


class SuiteManifestError(Exception):
    """Raised when tests/speckit-pro/suite-manifest.json is absent/unreadable/invalid.

    The suite manifest is the single per-layer source of truth for suite
    composition (XPLAT-010 FR-007/FR-008). The gate derives its roster from it
    and fails closed — never falling back to a hardcoded default — when it
    cannot be loaded.
    """


def load_suite_manifest(repo_root: Path) -> dict[str, Any]:
    """Load and shape-check the suite manifest; raise SuiteManifestError on failure."""
    path = repo_root / SUITE_MANIFEST_PATH
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SuiteManifestError(f"suite manifest not found: {SUITE_MANIFEST_PATH}") from exc
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SuiteManifestError(f"suite manifest is not valid JSON: {SUITE_MANIFEST_PATH}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != "1.0":
        raise SuiteManifestError("suite manifest schema_version must be '1.0'")
    layers = data.get("layers")
    if not isinstance(layers, list) or not layers:
        raise SuiteManifestError("suite manifest must carry a non-empty layers array")
    for layer in layers:
        if not isinstance(layer, dict) or not all(
            field in layer for field in ("id", "default", "live_only", "dispatch", "scripts")
        ):
            raise SuiteManifestError("suite manifest layer is missing a required field")
    return data


def manifest_default_suite(manifest: dict[str, Any]) -> tuple[str, ...]:
    return tuple(layer["id"] for layer in manifest["layers"] if layer["default"])


def manifest_extended_suite(manifest: dict[str, Any]) -> tuple[str, ...]:
    return tuple(layer["id"] for layer in manifest["layers"] if not layer["live_only"])


def manifest_allowed_layers(manifest: dict[str, Any]) -> frozenset[str]:
    return frozenset(
        layer["id"] for layer in manifest["layers"] if not layer["live_only"] and layer["id"] != "toolchain"
    )


def manifest_ai_eval_layers(manifest: dict[str, Any]) -> frozenset[str]:
    return frozenset(layer["id"] for layer in manifest["layers"] if layer["live_only"])


def _runner_repo_root() -> Path:
    # gates/suite.py -> gates -> speckit_pro_runner -> speckit-pro -> repo root.
    return Path(__file__).resolve().parents[3]


def _derive_module_roster() -> tuple[tuple[str, ...], tuple[str, ...], frozenset[str], frozenset[str], str | None]:
    try:
        manifest = load_suite_manifest(_runner_repo_root())
    except SuiteManifestError as exc:
        return (), (), frozenset(), frozenset(), str(exc)
    return (
        manifest_default_suite(manifest),
        manifest_extended_suite(manifest),
        manifest_allowed_layers(manifest),
        manifest_ai_eval_layers(manifest),
        None,
    )


# Derived solely from the manifest at import; the gate fails closed when the
# manifest is unavailable (SUITE_MANIFEST_ERROR set) rather than using a
# hardcoded default suite.
DEFAULT_SUITE, EXTENDED_SUITE, ALLOWED_LAYERS, AI_EVAL_LAYERS, SUITE_MANIFEST_ERROR = _derive_module_roster()
STATUS_BY_EXIT_CODE = {
    0: "ok",
    1: "expected_failure",
    2: "input_error",
    3: "missing_prerequisite",
}
STATUS_DIAGNOSTIC = {
    "expected_failure": "gate_expected_failure",
    "input_error": "gate_input_error",
    "missing_prerequisite": "gate_missing_prerequisite",
    "subprocess_failure": "gate_subprocess_failure",
}
STATUS_MESSAGES = {
    "expected_failure": "suite gate command reported an expected failure",
    "input_error": "suite gate command reported invalid input",
    "missing_prerequisite": "suite gate command is missing a prerequisite",
    "subprocess_failure": "suite gate command failed outside the expected exit contract",
}


@dataclass(frozen=True)
class CommandSpec:
    command_id: str
    argv: tuple[str, ...]
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    internal: bool = False


def run_suite_gate(entry: Any, request: Any) -> dict[str, Any]:
    repo_root_result = resolve_repo_root(request.inputs)
    if isinstance(repo_root_result, dict):
        status = "missing_prerequisite" if repo_root_result["code"] == "missing_prerequisite" else "input_error"
        return response(status, request_id=request.request_id, data=base_data(entry, request.operation, status), diagnostics=[repo_root_result])
    repo_root = repo_root_result

    if SUITE_MANIFEST_ERROR is not None:
        diag = diagnostic(
            "suite_manifest_unavailable",
            "suite gate cannot resolve its layer roster because the suite manifest is unavailable",
            details={"manifest_path": SUITE_MANIFEST_PATH, "error": SUITE_MANIFEST_ERROR},
            remediation_summary="Restore the suite manifest in the source checkout.",
            remediation_actions=[f"Restore {SUITE_MANIFEST_PATH}.", "Retry the suite-gate request."],
        )
        return response(
            "missing_prerequisite",
            request_id=request.request_id,
            data=base_data(entry, request.operation, "missing_prerequisite"),
            diagnostics=[diag],
        )

    operation = request.operation
    if operation == "run-default-suite":
        return run_default_suite(entry, request, repo_root)
    if operation == "run-layer":
        return run_layer(entry, request, repo_root)
    if operation == "run-toolchain-preflight":
        return run_toolchain_preflight(entry, request, repo_root)
    if operation == "run-ai-evals":
        return run_ai_evals(entry, request, repo_root)
    if operation == "run-integration-suite":
        return run_command_set(entry, request, repo_root, ["layer-7"])
    if operation == "run-parity-suite":
        return run_command_set(entry, request, repo_root, ["layer-8"])
    return response(
        "input_error",
        request_id=request.request_id,
        data=base_data(entry, operation, "input_error"),
        diagnostics=[
            diagnostic(
                "unknown_gate_operation",
                "suite gate operation is not implemented by the suite module",
                details={"operation": operation},
            )
        ],
    )


def run_default_suite(entry: Any, request: Any, repo_root: Path) -> dict[str, Any]:
    suite_result = requested_suite(request.inputs)
    if isinstance(suite_result, dict):
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[suite_result])
    command_ids = [suite_item_to_command_id(item) for item in suite_result]
    return run_command_set(entry, request, repo_root, command_ids)


def run_layer(entry: Any, request: Any, repo_root: Path) -> dict[str, Any]:
    layer = request.inputs.get("layer")
    if not isinstance(layer, str) or layer not in ALLOWED_LAYERS:
        diag = diagnostic(
            "invalid_layer",
            "run-layer requires one supported deterministic layer",
            details={"layer": layer, "supported_layers": sorted(ALLOWED_LAYERS)},
            remediation_summary="Send a supported run-layer request.",
            remediation_actions=["Set inputs.layer to 1, 4, 5, 7, or 8.", "Retry the suite-gate request."],
        )
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[diag])
    return run_command_set(entry, request, repo_root, [suite_item_to_command_id(layer)])


def run_toolchain_preflight(entry: Any, request: Any, repo_root: Path) -> dict[str, Any]:
    mode = request.inputs.get("mode", "tests")
    if not isinstance(mode, str) or mode not in TOOLCHAIN_MODES:
        diag = diagnostic(
            "invalid_toolchain_mode",
            "run-toolchain-preflight requires a supported toolchain mode",
            details={"mode": mode, "supported_modes": ["tests", "shell", "docs", "all"]},
            remediation_summary="Send a supported toolchain preflight mode.",
            remediation_actions=["Set inputs.mode to tests, shell, docs, or all.", "Retry the request."],
        )
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[diag])
    return run_command_set(entry, request, repo_root, ["toolchain"])


def run_ai_evals(entry: Any, request: Any, repo_root: Path) -> dict[str, Any]:
    layers_result = requested_ai_layers(request.inputs)
    if isinstance(layers_result, dict):
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[layers_result])
    layers = layers_result
    available_tools = available_ai_tools(request.inputs)
    try:
        manifest = load_suite_manifest(repo_root)
    except SuiteManifestError as exc:
        diag = diagnostic(
            "suite_manifest_unavailable",
            "AI eval dispatch cannot resolve manifest-backed runner references",
            details={"manifest_path": SUITE_MANIFEST_PATH, "error": str(exc)},
            remediation_summary="Restore the suite manifest in the source checkout.",
            remediation_actions=[f"Restore {SUITE_MANIFEST_PATH}.", "Retry run-ai-evals."],
        )
        return response(
            "missing_prerequisite",
            request_id=request.request_id,
            data=base_data(entry, request.operation, "missing_prerequisite"),
            diagnostics=[diag],
        )
    planned_dispatch = [ai_dispatch_plan(layer, repo_root, available_tools, manifest) for layer in layers]
    missing_by_layer = {
        plan["layer"]: plan["missing_tools"]
        for plan in planned_dispatch
        if plan["missing_tools"]
    }
    status = "missing_prerequisite" if missing_by_layer else "ok"
    data = base_data(entry, request.operation, status)
    data["suite"] = {
        "operation": request.operation,
        "summary": {
            "total": len(planned_dispatch),
            "passed": 0 if missing_by_layer else len(planned_dispatch),
            "failed": 0,
            "skipped": len(missing_by_layer),
        },
        "results": [],
        "planned_dispatch": planned_dispatch,
    }
    if not missing_by_layer:
        return response("ok", request_id=request.request_id, data=data)

    diag = diagnostic(
        "gate_missing_prerequisite",
        "AI eval dispatch is missing required local runners",
        details={"missing_by_layer": missing_by_layer},
        remediation_summary="Install or expose the required local eval runners before dispatching AI eval layers.",
        remediation_actions=["Install the missing runner CLIs.", "Retry run-ai-evals from the same source checkout."],
    )
    return response("missing_prerequisite", request_id=request.request_id, data=data, diagnostics=[diag])


def run_command_set(entry: Any, request: Any, repo_root: Path, command_ids: list[str]) -> dict[str, Any]:
    commands: list[CommandSpec] = []
    for command_id in command_ids:
        command_result = command_spec(command_id, request.inputs, repo_root)
        if isinstance(command_result, dict):
            return response(
                "input_error",
                request_id=request.request_id,
                data=base_data(entry, request.operation, "input_error"),
                diagnostics=[command_result],
            )
        commands.append(command_result)

    results = [run_command(command, repo_root) for command in commands]
    status = aggregate_status(results)
    data = base_data(entry, request.operation, status)
    data["suite"] = {
        "operation": request.operation,
        "summary": summarize_results(results),
        "results": results,
        "planned_dispatch": [],
    }
    if status == "ok":
        return response("ok", request_id=request.request_id, data=data)
    return response(status, request_id=request.request_id, data=data, diagnostics=[gate_diagnostic(status, results)])


def requested_suite(inputs: dict[str, Any]) -> tuple[str, ...] | dict[str, Any]:
    raw = inputs.get("suite")
    if raw is None:
        raw = list(DEFAULT_SUITE)
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        return diagnostic(
            "invalid_suite",
            "run-default-suite inputs.suite must be a list of suite item ids",
            details={"supported_suite_items": list(EXTENDED_SUITE)},
            remediation_summary="Send a structured suite list.",
            remediation_actions=["Use suite entries toolchain, 1, 4, 5, 7, and 8.", "Retry the request."],
        )
    invalid = [item for item in raw if item not in EXTENDED_SUITE]
    if invalid:
        return diagnostic(
            "invalid_suite",
            "run-default-suite received unsupported suite item ids",
            details={"invalid": invalid, "supported_suite_items": list(EXTENDED_SUITE)},
            remediation_summary="Send only supported suite item ids.",
            remediation_actions=["Remove unsupported suite entries.", "Retry the request."],
        )
    return tuple(raw)


def requested_ai_layers(inputs: dict[str, Any]) -> tuple[str, ...] | dict[str, Any]:
    raw = inputs.get("layers", ["2", "3", "6"])
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        return diagnostic(
            "invalid_ai_eval_layers",
            "run-ai-evals inputs.layers must be a list of eval layer ids",
            details={"supported_layers": sorted(AI_EVAL_LAYERS)},
            remediation_summary="Send a supported AI eval layer list.",
            remediation_actions=["Use layers 2, 3, and 6.", "Retry the request."],
        )
    invalid = [item for item in raw if item not in AI_EVAL_LAYERS]
    if invalid:
        return diagnostic(
            "invalid_ai_eval_layers",
            "run-ai-evals received unsupported layer ids",
            details={"invalid": invalid, "supported_layers": sorted(AI_EVAL_LAYERS)},
            remediation_summary="Send only supported AI eval layer ids.",
            remediation_actions=["Remove unsupported layers.", "Retry the request."],
        )
    return tuple(raw)


def suite_item_to_command_id(item: str) -> str:
    if item == "toolchain":
        return "toolchain"
    return f"layer-{item}"


def command_spec(command_id: str, inputs: dict[str, Any], repo_root: Path) -> CommandSpec | dict[str, Any]:
    overrides = inputs.get("test_commands", {})
    if overrides is None:
        overrides = {}
    if not isinstance(overrides, dict):
        return unsafe_command_diagnostic(command_id, "test_commands must be an object keyed by command id")
    if command_id in overrides:
        return command_spec_from_override(command_id, overrides[command_id])
    return default_command_spec(command_id, inputs, repo_root)


def command_spec_from_override(command_id: str, raw: Any) -> CommandSpec | dict[str, Any]:
    if not isinstance(raw, dict):
        return unsafe_command_diagnostic(command_id, "command override must be an object with an argv list")
    if raw.get("shell") is True:
        return unsafe_command_diagnostic(command_id, "command override must not request shell execution")
    argv = raw.get("argv")
    if not isinstance(argv, list) or not argv or not all(isinstance(item, str) and item for item in argv):
        return unsafe_command_diagnostic(command_id, "command override argv must be a non-empty list of strings")
    unsafe = unsafe_argv_reason(argv)
    if unsafe:
        return unsafe_command_diagnostic(command_id, unsafe)
    timeout = raw.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)
    if not isinstance(timeout, int) or timeout <= 0 or timeout > DEFAULT_TIMEOUT_SECONDS:
        return unsafe_command_diagnostic(command_id, "command override timeout_seconds must be a positive bounded integer")
    return CommandSpec(command_id=command_id, argv=tuple(argv), timeout_seconds=timeout)


def default_command_spec(command_id: str, inputs: dict[str, Any], repo_root: Path) -> CommandSpec | dict[str, Any]:
    if command_id == "toolchain":
        return toolchain_command_spec(command_id, inputs, repo_root)
    if command_id in {"layer-1", "layer-4", "layer-5", "layer-7", "layer-8"}:
        return external_layer_script_spec(command_id)
    return unsafe_command_diagnostic(command_id, "unknown suite command id")


def internal_command_spec(command_id: str) -> CommandSpec:
    return CommandSpec(
        command_id=command_id,
        argv=(sys.executable, "-m", "speckit_pro_runner"),
        internal=True,
    )


def toolchain_command_spec(command_id: str, inputs: dict[str, Any], repo_root: Path) -> CommandSpec | dict[str, Any]:
    mode = inputs.get("mode", "tests")
    if not isinstance(mode, str) or mode not in TOOLCHAIN_MODES:
        return unsafe_command_diagnostic(command_id, "toolchain mode must be one of all, docs, shell, or tests")
    checker = repo_root / TOOLCHAIN_CHECKER
    if checker.is_file():
        return CommandSpec(
            command_id=command_id,
            argv=(sys.executable, TOOLCHAIN_CHECKER, "--mode", mode),
        )
    return internal_command_spec(command_id)


def external_layer_script_spec(command_id: str) -> CommandSpec:
    layer = command_id.split("-", 1)[1]
    return CommandSpec(
        command_id=command_id,
        argv=(sys.executable, LAYER_SCRIPT_DISPATCHER, "--layer", layer),
        timeout_seconds=LAYER_SCRIPT_TIMEOUT_SECONDS,
    )


def run_command(command: CommandSpec, repo_root: Path) -> dict[str, Any]:
    if command.internal:
        return run_internal_command(command, repo_root)
    missing = missing_executable(command.argv[0], repo_root)
    if missing:
        return command_result(command, "missing_prerequisite", 3, "", f"missing executable: {command.argv[0]}\n", 0)
    if not resolves_to_current_python(command.argv[0], repo_root):
        return command_result(
            command,
            "input_error",
            2,
            "",
            f"suite command executable must resolve to the active Python interpreter: {command.argv[0]}\n",
            0,
        )
    if LAYER_SCRIPT_DISPATCHER in command.argv and not (repo_root / LAYER_SCRIPT_DISPATCHER).is_file():
        return command_result(
            command,
            "missing_prerequisite",
            3,
            "",
            f"missing layer dispatcher: {LAYER_SCRIPT_DISPATCHER}; restore it from the source checkout — the layer dispatcher is repo-side and not shipped in payloads\n",
            0,
        )
    started = time.monotonic()
    try:
        completed = subprocess.run(
            [sys.executable, *command.argv[1:]],
            cwd=repo_root,
            text=True,
            capture_output=True,
            timeout=command.timeout_seconds,
            shell=False,
            check=False,
        )
        duration_ms = int((time.monotonic() - started) * 1000)
        exit_code = int(completed.returncode)
        status = STATUS_BY_EXIT_CODE.get(exit_code, "subprocess_failure")
        return command_result(command, status, exit_code, completed.stdout, completed.stderr, duration_ms)
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return command_result(command, "subprocess_failure", 124, stdout, stderr, duration_ms)
    except OSError as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        return command_result(command, "missing_prerequisite", 3, "", f"{type(exc).__name__}: {exc}\n", duration_ms)


def run_internal_command(command: CommandSpec, repo_root: Path) -> dict[str, Any]:
    started = time.monotonic()
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
            exit_code = run_internal_suite_check(command.command_id, repo_root)
        duration_ms = int((time.monotonic() - started) * 1000)
        status = STATUS_BY_EXIT_CODE.get(exit_code, "subprocess_failure")
        return command_result(command, status, exit_code, stdout_buffer.getvalue(), stderr_buffer.getvalue(), duration_ms)
    except Exception as exc:  # pragma: no cover - defensive envelope boundary
        duration_ms = int((time.monotonic() - started) * 1000)
        return command_result(command, "subprocess_failure", 4, stdout_buffer.getvalue(), f"{type(exc).__name__}: {exc}\n", duration_ms)


def run_internal_suite_check(command_id: str, repo_root: Path) -> int:
    if command_id == "toolchain":
        return check_toolchain(repo_root)
    print(f"unknown internal suite command: {command_id}", file=sys.stderr)
    return 2


def emit_checks(label: str, checks: list[tuple[str, bool, str]]) -> int:
    passed = 0
    for name, ok, detail in checks:
        if ok:
            passed += 1
            print(f"PASS {name}: {detail}")
        else:
            print(f"FAIL {name}: {detail}", file=sys.stderr)
    print(f"{label}: {passed}/{len(checks)} passed")
    return 0 if passed == len(checks) else 1


def check_toolchain(repo_root: Path) -> int:
    checks = [
        ("python >= 3.11", sys.version_info >= (3, 11), platform_python()),
        ("repo root", (repo_root / "speckit-pro").is_dir(), repo_root.as_posix()),
        ("runner package", (repo_root / "speckit-pro" / "speckit_pro_runner").is_dir(), "speckit-pro/speckit_pro_runner"),
        ("git available", shutil.which("git") is not None, shutil.which("git") or "missing"),
        ("json parser", True, "stdlib json"),
    ]
    return emit_checks("toolchain preflight", checks)


def platform_python() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def command_result(
    command: CommandSpec,
    status: str,
    exit_code: int,
    stdout: str,
    stderr: str,
    duration_ms: int,
) -> dict[str, Any]:
    return {
        "command_id": command.command_id,
        "argv": list(command.argv),
        "shell": False,
        "timeout_seconds": command.timeout_seconds,
        "status": status,
        "exit_code": exit_code,
        "duration_ms": duration_ms,
        "stdout": output_capture(stdout),
        "stderr": output_capture(stderr),
    }


def output_capture(text: str) -> dict[str, Any]:
    encoded = text.encode("utf-8", errors="replace")
    truncated = len(encoded) > CAPTURE_LIMIT_BYTES
    if truncated:
        captured = encoded[:CAPTURE_LIMIT_BYTES].decode("utf-8", errors="replace")
    else:
        captured = text
    return {
        "text": captured,
        "byte_count": len(encoded),
        "truncated": truncated,
        "limit_bytes": CAPTURE_LIMIT_BYTES,
    }


def aggregate_status(results: list[dict[str, Any]]) -> str:
    statuses = {result["status"] for result in results}
    for status in ("subprocess_failure", "input_error", "missing_prerequisite", "expected_failure"):
        if status in statuses:
            return status
    return "ok"


def summarize_results(results: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "total": len(results),
        "passed": sum(1 for result in results if result["status"] == "ok"),
        "failed": sum(1 for result in results if result["status"] in {"expected_failure", "input_error", "subprocess_failure"}),
        "skipped": sum(1 for result in results if result["status"] == "missing_prerequisite"),
    }


def base_data(entry: Any, operation: str, status: str) -> dict[str, Any]:
    gate_status = "pass"
    if status in {"expected_failure", "subprocess_failure"}:
        gate_status = "fail"
    elif status == "missing_prerequisite":
        gate_status = "skipped"
    elif status == "input_error":
        gate_status = "input_error"
    return {
        "gate": {
            "gate_id": entry.helper_id,
            "operation": operation,
            "gate_status": gate_status,
            "promoted": status != "input_error",
            "blocking": status != "ok",
            "comparison_ids": comparison_ids(operation),
            "promotion_record": PROMOTION_RECORD,
        },
        "artifacts": [
            {
                "path": PROMOTION_RECORD,
                "kind": "fixture",
            }
        ],
    }


def comparison_ids(operation: str) -> list[str]:
    if operation == "run-default-suite":
        return ["us1-default-suite-toolchain-l1-l4-l5-l7-l8"]
    if operation == "run-ai-evals":
        return ["us1-ai-eval-dispatch"]
    return [f"us1-{operation}"]


def gate_diagnostic(status: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    failing = [
        {
            "command_id": result["command_id"],
            "status": result["status"],
            "exit_code": result["exit_code"],
        }
        for result in results
        if result["status"] != "ok"
    ]
    return diagnostic(
        STATUS_DIAGNOSTIC.get(status, "gate_subprocess_failure"),
        STATUS_MESSAGES.get(status, "suite gate failed"),
        details={"results": failing},
        remediation_summary="Inspect the structured suite result and fix the first failing gate.",
        remediation_actions=["Review data.suite.results for stdout, stderr, and exit code.", "Retry the same runner request."],
    )


def unsafe_command_diagnostic(command_id: str, reason: str) -> dict[str, Any]:
    return diagnostic(
        "unsafe_command_spec",
        "suite gate command specs must use argv-list subprocesses",
        details={"command_id": command_id, "reason": reason},
        remediation_summary="Use structured argv lists for suite-gate command dispatch.",
        remediation_actions=["Remove shell strings and shell=True.", "Retry with an argv array."],
    )


def unsafe_argv_reason(argv: list[str]) -> str:
    shell_tools = {"bash", "sh", "zsh", "pwsh", "powershell", "jq"}
    executable = Path(argv[0]).name.lower()
    if executable in shell_tools:
        return f"command override executable is forbidden in promoted suite gates: {executable}"
    for item in argv:
        lowered = item.lower()
        name = Path(lowered).name
        if name in shell_tools:
            return f"command override includes forbidden shell tool: {name}"
        if lowered.endswith(".sh"):
            return "command override must not invoke .sh files in promoted suite gates"
    return ""


def resolve_repo_root(inputs: dict[str, Any]) -> Path | dict[str, Any]:
    invocation_root = find_repo_root(Path.cwd())
    if invocation_root is None:
        return diagnostic(
            "missing_prerequisite",
            "could not locate repository root for suite gate request",
            details={"cwd": str(Path.cwd())},
            remediation_summary="Run the suite gate from a SpecKit Pro source checkout.",
            remediation_actions=["Change to the repository root.", "Retry the runner request."],
        )
    raw = inputs.get("repo_root")
    if raw is not None and not isinstance(raw, str):
        return diagnostic(
            "invalid_repo_root",
            "repo_root must be a string path when provided",
            details={"field": "repo_root"},
            remediation_summary="Send a valid repo_root path.",
            remediation_actions=["Set repo_root to . or omit it.", "Retry the request."],
        )
    if not raw:
        return invocation_root
    if "\x00" in raw:
        return diagnostic(
            "invalid_repo_root",
            "repo_root contains a NUL byte",
            details={"field": "repo_root"},
            remediation_summary="Send a valid repo_root path.",
            remediation_actions=["Remove the NUL byte.", "Retry the request."],
        )
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = invocation_root / candidate
    resolved = candidate.resolve(strict=False)
    if not is_relative_to(resolved, invocation_root):
        return diagnostic(
            "invalid_repo_root",
            "repo_root escapes the source checkout trust boundary",
            details={"repo_root": raw},
            remediation_summary="Keep suite-gate paths inside the source checkout.",
            remediation_actions=["Set repo_root to .", "Retry the request."],
        )
    if not (resolved / "speckit-pro" / "speckit_pro_runner").is_dir():
        return diagnostic(
            "missing_prerequisite",
            "repo_root does not contain the SpecKit Pro runner package",
            details={"repo_root": raw},
            remediation_summary="Run the suite gate from a valid source checkout.",
            remediation_actions=["Set repo_root to the repository root.", "Retry the request."],
        )
    return resolved


def find_repo_root(start: Path) -> Path | None:
    candidates = [start, *start.parents] if start.is_dir() else [start.parent, *start.parent.parents]
    for candidate in candidates:
        if (candidate / "speckit-pro" / "speckit_pro_runner").is_dir() and (candidate / "tests" / "speckit-pro").is_dir():
            return candidate.resolve(strict=False)
    return None


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def rel(path: Path, repo_root: Path) -> str:
    return path.resolve(strict=False).relative_to(repo_root.resolve(strict=False)).as_posix()


def missing_executable(executable: str, repo_root: Path) -> bool:
    path = Path(executable)
    has_path_separator = os.sep in executable or (os.altsep is not None and os.altsep in executable)
    if path.is_absolute() or has_path_separator:
        candidate = path if path.is_absolute() else repo_root / path
        return not candidate.exists()
    return shutil.which(executable) is None


def resolves_to_current_python(executable: str, repo_root: Path) -> bool:
    path = Path(executable)
    has_path_separator = os.sep in executable or (os.altsep is not None and os.altsep in executable)
    if path.is_absolute():
        candidate = path
    elif has_path_separator:
        candidate = repo_root / path
    else:
        resolved = shutil.which(executable)
        if resolved is None:
            return False
        candidate = Path(resolved)
    try:
        return candidate.samefile(sys.executable)
    except OSError:
        return candidate.resolve(strict=False) == Path(sys.executable).resolve(strict=False)


def available_ai_tools(inputs: dict[str, Any]) -> set[str]:
    overrides = inputs.get("test_overrides", {})
    if isinstance(overrides, dict) and isinstance(overrides.get("available_tools"), list):
        return {tool for tool in overrides["available_tools"] if isinstance(tool, str)}
    return {tool for tool in ("claude", "codex") if shutil.which(tool) is not None}


def ai_dispatch_plan(
    layer: str,
    repo_root: Path,
    available_tools: set[str],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    required = ai_required_tools(layer)
    missing = [tool for tool in required if tool not in available_tools]
    return {
        "layer": layer,
        "command_id": f"layer-{layer}",
        "required_tools": required,
        "missing_tools": missing,
        "bash_references": [],
        "runner_references": manifest_runner_references(layer, manifest),
        "python_entrypoint": "python -m speckit_pro_runner",
        "repo_root": rel(repo_root, repo_root) or ".",
    }


def ai_required_tools(layer: str) -> list[str]:
    if layer in {"2", "3"}:
        return ["claude", "codex"]
    return ["claude"]


def manifest_runner_references(layer: str, manifest: dict[str, Any]) -> list[str]:
    for entry in manifest["layers"]:
        if entry["id"] != layer:
            continue
        return [script["path"] for script in entry["scripts"]]
    return []


__all__ = ("run_suite_gate",)
