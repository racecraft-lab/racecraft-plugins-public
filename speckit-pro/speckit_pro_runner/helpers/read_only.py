"""Shared read-only helper implementations."""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import time
from pathlib import Path, PurePosixPath
from typing import Any, Callable

from ..envelope import diagnostic, response

CAPTURE_LIMIT_BYTES = 16 * 1024
SUBPROCESS_TIMEOUT_SECONDS = 30
BOUNDED_TEXT_INPUT_BYTES = 32 * 1024
WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")

EXIT_STATUS = {
    0: "ok",
    1: "expected_failure",
    2: "input_error",
    3: "missing_prerequisite",
    4: "subprocess_failure",
}

EXIT_DIAGNOSTIC = {
    1: "validation_failure",
    2: "invalid_input",
    3: "missing_prerequisite",
    4: "subprocess_failure",
}

PATH_KEYS = {
    "changed_files",
    "config_path",
    "feature_dir",
    "packet_path",
    "plan_file",
    "repo_root",
    "target",
    "workflow_file",
}

WARN_DESTRUCTIVE_MIGRATION = (
    "destructive migration: a passing CI run does not prove this change is releasable "
    "(CI-green ≠ releasable)"
)
WARN_CONCURRENCY = (
    "concurrency-sensitive change: a passing CI run does not prove this change is releasable "
    "(CI-green ≠ releasable)"
)


def registry_report(helpers: dict[str, Any]) -> dict[str, Any]:
    records = [entry.as_record() for entry in helpers.values()]
    return {
        "helper_count": len(records),
        "helpers": sorted(records, key=lambda record: record["helper_id"]),
        "mode": "read_only",
        "mutation_modes_promoted": [],
    }


def run_registered_helper(entry: Any, request: Any) -> dict[str, Any]:
    repo_root_result = resolve_repo_root(request.inputs)
    if isinstance(repo_root_result, dict):
        status = "missing_prerequisite" if repo_root_result["code"] == "missing_prerequisite" else "input_error"
        return response(status, request_id=request.request_id, diagnostics=[repo_root_result])
    repo_root = repo_root_result

    validation_diag = validate_bounded_inputs(entry.helper_id, request.inputs, repo_root)
    if validation_diag is not None:
        return response("input_error", request_id=request.request_id, diagnostics=[validation_diag])

    inputs = canonicalize_inputs(entry.helper_id, request.inputs, repo_root)
    argv_result = helper_argv(entry, inputs, repo_root)
    if isinstance(argv_result, dict):
        status = "missing_prerequisite" if argv_result["code"] == "missing_prerequisite" else "input_error"
        return response(status, request_id=request.request_id, diagnostics=[argv_result])

    started = time.monotonic()
    result = PY_HELPERS[entry.helper_id](inputs, repo_root)
    duration_ms = int((time.monotonic() - started) * 1000)
    stdout = output_capture(result["stdout"])
    stderr = output_capture(result["stderr"])
    exit_code = int(result["exit_code"])
    status = EXIT_STATUS.get(exit_code, "subprocess_failure")
    data = helper_result_data(entry, inputs, argv_result, repo_root, exit_code, stdout, stderr, duration_ms)
    if status == "ok":
        return response("ok", request_id=request.request_id, data=data)
    return response(
        status,
        request_id=request.request_id,
        data=data,
        diagnostics=[helper_failure_diagnostic(entry.helper_id, exit_code, stdout, stderr)],
    )


def resolve_repo_root(inputs: dict[str, Any]) -> Path | dict[str, Any]:
    invocation_root = find_repo_root(Path.cwd())
    if invocation_root is None:
        return path_diagnostic(
            "missing_prerequisite",
            "could not locate repository root for read-only helper request",
            {"repo_root": normalize_display(Path.cwd())},
        )
    raw = inputs.get("repo_root")
    if raw is not None and not isinstance(raw, str):
        return path_diagnostic("invalid_input", "repo_root must be a string path", {"field": "repo_root"})
    if isinstance(raw, str) and looks_like_windows_absolute_path(raw) and os.name != "nt":
        return path_diagnostic("unsupported_path", "path escapes the repo/plugin trust boundary", {"field": "repo_root", "path": normalize_display(raw)})
    if raw:
        candidate = Path(normalize_path_input(raw))
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        if not path_stays_in_trust_boundary(candidate, invocation_root):
            return path_diagnostic("unsupported_path", "path escapes the repo/plugin trust boundary", {"field": "repo_root", "path": normalize_display(raw)})
    return invocation_root


def find_repo_root(start: Path) -> Path | None:
    candidates = [start, *start.parents] if start.is_dir() else [start.parent, *start.parent.parents]
    for candidate in candidates:
        root = candidate.resolve(strict=False)
        runner_dir = candidate / "speckit-pro" / "speckit_pro_runner"
        if runner_dir.is_dir() and path_stays_in_trust_boundary(runner_dir, root):
            return root
    return None


def validate_bounded_inputs(helper_id: str, inputs: dict[str, Any], repo_root: Path) -> dict[str, Any] | None:
    for key, value in iter_input_strings(inputs):
        if len(value.encode("utf-8")) > BOUNDED_TEXT_INPUT_BYTES:
            return diagnostic(
                "invalid_input",
                "helper input string exceeds the bounded input limit",
                details={"helper_id": helper_id, "field": key, "limit_bytes": BOUNDED_TEXT_INPUT_BYTES},
                remediation_summary="Send smaller deterministic helper inputs.",
                remediation_actions=["Use fixture files instead of large inline strings.", "Retry with bounded helper input."],
            )
    args = inputs.get("args")
    if args is not None:
        return diagnostic(
            "invalid_input",
            "structured helper requests must not provide raw args",
            details={"helper_id": helper_id},
            remediation_summary="Use helper-specific structured input fields so reported argv cannot diverge from executed behavior.",
            remediation_actions=["Remove inputs.args.", "Retry with the helper-specific fields from fixture-manifest.json."],
        )
    for key in PATH_KEYS:
        value = inputs.get(key)
        if isinstance(value, str) and value:
            path_diag = validate_path_value(helper_id, key, value, repo_root)
            if path_diag is not None:
                return path_diag
    if inputs.get("write_mode") is True:
        return diagnostic(
            "unsupported_mode",
            "write-mode helper behavior is out of scope for runner read-only dispatch",
            details={"helper_id": helper_id},
            remediation_summary="Use only registered read-only helper modes.",
            remediation_actions=["Remove write_mode from the request.", "Use the existing Bash workflow for mutation behavior."],
        )
    if helper_id in {"detect-commands", "detect-presets"}:
        raw_root = inputs.get("repo_root")
        if isinstance(raw_root, str) and raw_root:
            target_root = resolve_input_path(raw_root, repo_root)
            if not trusted_dir_exists(target_root, repo_root):
                return path_diagnostic(
                    "invalid_input",
                    "repo_root must be a directory",
                    {"helper_id": helper_id, "field": "repo_root", "path": normalize_display(raw_root)},
                )
    if helper_id == "validate-pr-workflow-contract":
        changed_files = inputs.get("changed_files")
        if changed_files is not None:
            if not isinstance(changed_files, str):
                return path_diagnostic(
                    "invalid_input",
                    "changed_files must be a single path to a changed-files list",
                    {"helper_id": helper_id, "field": "changed_files"},
                )
            if "\n" in changed_files or "\r" in changed_files:
                return path_diagnostic(
                    "invalid_input",
                    "changed_files must be a single path, not an inline file list",
                    {"helper_id": helper_id, "field": "changed_files"},
                )
            if changed_files:
                path_diag = validate_path_value(helper_id, "changed_files", changed_files, repo_root)
                if path_diag is not None:
                    return path_diag
    return None


def canonicalize_inputs(helper_id: str, inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    canonical = dict(inputs)
    path_keys_by_helper = {
        "check-prerequisites": {"workflow_file"},
        "detect-commands": {"repo_root"},
        "detect-presets": {"repo_root"},
        "count-markers": {"feature_dir"},
        "validate-gate": {"feature_dir"},
        "reviewability-gate": {"target"},
        "estimate-reviewable-loc": {"plan_file"},
        "resolve-confidence-mode": {"config_path"},
        "confidence-gate": {"workflow_file"},
        "generate-spec-index-check": {"repo_root"},
        "o5-topology": {"target"},
        "atomicity-route": {"feature_dir"},
        "plan-layers-feature-dir": {"feature_dir"},
        "validate-pr-workflow-contract": {"repo_root", "changed_files"},
        "validate-pr-packet-read-only": {"packet_path"},
    }
    for key in path_keys_by_helper.get(helper_id, set()):
        value = canonical.get(key)
        if isinstance(value, str) and value:
            canonical[key] = request_path_display(value, repo_root)
    return canonical


def validate_path_value(helper_id: str, field: str, raw: str, repo_root: Path) -> dict[str, Any] | None:
    if "\x00" in raw:
        return path_diagnostic("invalid_input", "path contains a NUL byte", {"helper_id": helper_id, "field": field})
    if looks_like_windows_absolute_path(raw) and os.name != "nt":
        return path_diagnostic(
            "unsupported_path",
            "path escapes the repo/plugin trust boundary",
            {"helper_id": helper_id, "field": field, "path": normalize_display(raw)},
        )
    candidate = Path(normalize_path_input(raw))
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    resolved = candidate.resolve(strict=False)
    allowed_roots = [repo_root, repo_root / "speckit-pro"]
    if not any(is_relative_to(resolved, allowed) for allowed in allowed_roots):
        return path_diagnostic(
            "unsupported_path",
            "path escapes the repo/plugin trust boundary",
            {"helper_id": helper_id, "field": field, "path": normalize_display(raw)},
        )
    return None


def helper_argv(entry: Any, inputs: dict[str, Any], repo_root: Path) -> list[str] | dict[str, Any]:
    script = repo_root / entry.script
    if not trusted_file_exists(script, repo_root):
        return diagnostic(
            "missing_prerequisite",
            "registered helper script is missing from the source checkout",
            details={"helper_id": entry.helper_id, "script": entry.script},
            remediation_summary="Refresh the source checkout before running helper parity.",
            remediation_actions=["Verify the helper script path exists.", "Retry from the repository root."],
        )
    args = explicit_or_derived_args(entry.helper_id, inputs, repo_root)
    if isinstance(args, dict):
        return args
    return [str(script), *args]


def explicit_or_derived_args(helper_id: str, inputs: dict[str, Any], repo_root: Path) -> list[str] | dict[str, Any]:
    if helper_id in {"detect-commands", "detect-presets"}:
        return []
    if helper_id == "check-prerequisites":
        workflow_file = inputs.get("workflow_file")
        return [request_path_display(workflow_file, repo_root)] if isinstance(workflow_file, str) and workflow_file else []
    if helper_id == "count-markers":
        return required_args(inputs, ["type", "feature_dir"], helper_id, repo_root, path_keys={"feature_dir"})
    if helper_id == "validate-gate":
        return required_args(inputs, ["gate", "feature_dir"], helper_id, repo_root, path_keys={"feature_dir"})
    if helper_id == "reviewability-gate":
        return required_args(inputs, ["mode_name", "target"], helper_id, repo_root, path_keys={"target"})
    if helper_id == "estimate-reviewable-loc":
        return required_args(inputs, ["plan_file"], helper_id, repo_root, path_keys={"plan_file"})
    if helper_id == "resolve-confidence-mode":
        argv: list[str] = []
        config_path = inputs.get("config_path")
        if isinstance(config_path, str) and config_path:
            argv.extend(["--config", request_path_display(config_path, repo_root)])
        autopilot_args = inputs.get("autopilot_args")
        if autopilot_args is not None:
            if not isinstance(autopilot_args, list) or not all(isinstance(arg, str) for arg in autopilot_args):
                return invalid_args(helper_id, "autopilot_args must be an array of strings")
            argv.extend(["--", *autopilot_args])
        return argv
    if helper_id == "confidence-gate":
        workflow_file = inputs.get("workflow_file")
        if not isinstance(workflow_file, str) or not workflow_file:
            return invalid_args(helper_id, "workflow_file is required")
        argv = [request_path_display(workflow_file, repo_root)]
        threshold = inputs.get("threshold")
        mode = inputs.get("mode_name")
        if isinstance(threshold, str) and threshold:
            argv.extend(["--threshold", threshold])
        if isinstance(mode, str) and mode:
            argv.extend(["--mode", mode])
        return argv
    if helper_id == "generate-spec-index-check":
        return ["--check", request_path_display(inputs.get("repo_root") or ".", repo_root)]
    if helper_id in {"o5-topology", "atomicity-route"}:
        path_key = "target" if helper_id == "o5-topology" else "feature_dir"
        return required_args(inputs, [path_key], helper_id, repo_root, path_keys={path_key})
    if helper_id == "plan-layers-feature-dir":
        return required_args(inputs, ["feature_dir"], helper_id, repo_root, path_keys={"feature_dir"})
    if helper_id == "validate-pr-workflow-contract":
        title = inputs.get("title")
        if not isinstance(title, str) or not title:
            return invalid_args(helper_id, "title is required")
        argv = ["--title", title, "--repo-root", request_path_display(inputs.get("repo_root") or ".", repo_root)]
        changed_files = inputs.get("changed_files")
        if isinstance(changed_files, str) and changed_files:
            argv.extend(["--changed-files", changed_files])
        return argv
    if helper_id == "validate-pr-packet-read-only":
        return required_args(inputs, ["packet_path"], helper_id, repo_root, path_keys={"packet_path"})
    return invalid_args(helper_id, "helper does not define argument derivation")


def required_args(
    inputs: dict[str, Any],
    keys: list[str],
    helper_id: str,
    repo_root: Path | None = None,
    path_keys: set[str] | None = None,
) -> list[str] | dict[str, Any]:
    values: list[str] = []
    path_keys = path_keys or set()
    for key in keys:
        value = inputs.get(key)
        if not isinstance(value, str) or not value:
            return invalid_args(helper_id, f"{key} is required")
        if key in path_keys:
            value = request_path_display(value, repo_root) if repo_root is not None else normalize_path_input(value)
        values.append(value)
    return values


def invalid_args(helper_id: str, message: str) -> dict[str, Any]:
    return diagnostic(
        "invalid_input",
        message,
        details={"helper_id": helper_id},
        remediation_summary="Send the helper-specific read-only input fields.",
        remediation_actions=["Inspect fixture-manifest.json for accepted inputs.", "Retry with the required fields."],
    )


def helper_result_data(
    entry: Any,
    inputs: dict[str, Any],
    argv: list[str],
    repo_root: Path,
    exit_code: int,
    stdout: dict[str, Any],
    stderr: dict[str, Any],
    duration_ms: int,
) -> dict[str, Any]:
    parsed_stdout: Any | None = None
    if stdout["text"].strip():
        try:
            parsed_stdout = json.loads(stdout["text"])
        except json.JSONDecodeError:
            parsed_stdout = None
    data = {
        "helper_id": entry.helper_id,
        "operation": entry.operation,
        "mode": "read_only",
        "promotion_status": entry.promotion_status,
        "comparison_mode": entry.comparison_mode,
        "argv": display_argv(argv, repo_root),
        "shell": False,
        "cwd": {"kind": "repo_relative", "value": ".", "display": "."},
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "timed_out": False,
        "timeout_seconds": SUBPROCESS_TIMEOUT_SECONDS,
        "duration_ms": duration_ms,
        "writes_state": False,
    }
    if entry.helper_id in {"detect-commands", "detect-presets"}:
        data["effective_cwd"] = helper_cwd(entry.helper_id, inputs, repo_root)
    if parsed_stdout is not None:
        data["stdout_json"] = parsed_stdout
    return data


def helper_cwd(helper_id: str, inputs: dict[str, Any], repo_root: Path) -> dict[str, str]:
    cwd = repo_root
    if helper_id in {"detect-commands", "detect-presets"}:
        raw = inputs.get("repo_root")
        if isinstance(raw, str) and raw:
            cwd = resolve_input_path(raw, repo_root)
    rel = repo_relative(cwd, repo_root)
    return {"kind": "repo_relative", "value": rel, "display": rel}


def helper_failure_diagnostic(helper_id: str, exit_code: int, stdout: dict[str, Any], stderr: dict[str, Any]) -> dict[str, Any]:
    code = EXIT_DIAGNOSTIC.get(exit_code, "subprocess_failure")
    message = "read-only helper completed with a nonzero exit code"
    if code == "invalid_input":
        message = "read-only helper rejected the request inputs"
    elif code == "missing_prerequisite":
        message = "read-only helper reported a missing prerequisite"
    elif code == "validation_failure":
        message = "read-only helper reported an expected validation failure"
    return diagnostic(
        code,
        message,
        details={
            "helper_id": helper_id,
            "exit_code": exit_code,
            "stdout_bytes": stdout["byte_count"],
            "stderr_bytes": stderr["byte_count"],
        },
        remediation_summary="Inspect the helper stdout JSON and stderr diagnostics.",
        remediation_actions=["Compare against the helper fixture manifest.", "Retry after correcting the helper input or fixture state."],
    )


def make_result(stdout: str, stderr: str = "", exit_code: int = 0) -> dict[str, Any]:
    return {"stdout": stdout, "stderr": stderr, "exit_code": exit_code}


def json_text(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n"


def pretty_json_text(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


def check_prerequisites(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    workflow = normalize_path_input(inputs.get("workflow_file") or "")
    checks: list[dict[str, Any]] = []
    all_pass = True

    specify_path = find_specify()
    if specify_path:
        checks.append(check("speckit_cli", True, "SpecKit CLI installed", "specify 0.11.8"))
    else:
        checks.append(check("speckit_cli", False, "SpecKit CLI not found. Install: uv tool install specify-cli --from git+https://github.com/github/spec-kit.git", ""))
        all_pass = False
    if trusted_dir_exists(repo_root / ".specify", repo_root):
        checks.append(check("project_init", True, "Project initialized", ""))
    else:
        checks.append(check("project_init", False, "SpecKit not initialized. Run: specify init --ai claude", ""))
        all_pass = False
    if trusted_file_exists(repo_root / ".specify" / "memory" / "constitution.md", repo_root):
        checks.append(check("constitution", True, "Constitution exists", ""))
    else:
        checks.append(check("constitution", False, "No constitution found. Run: /speckit-constitution", ""))
        all_pass = False

    missing = []
    for cmd in ("speckit-specify", "speckit-plan", "speckit-tasks", "speckit-implement"):
        if not any(trusted_file_exists(repo_root / root / "skills" / cmd / "SKILL.md", repo_root) for root in (".claude", ".codex", ".agents")):
            missing.append(cmd)
    if missing:
        checks.append(check("commands", False, f"Missing commands: {' '.join(missing)}. Run: specify integration install <claude|codex>", ""))
        all_pass = False
    else:
        checks.append(check("commands", True, "All SpecKit commands installed", ""))

    if workflow:
        workflow_path = resolve_input_path(workflow, repo_root)
        if trusted_file_exists(workflow_path, repo_root):
            checks.append(check("workflow_file", True, "Workflow file exists", workflow))
        else:
            checks.append(check("workflow_file", False, f"Workflow file not found: {workflow}", ""))
            all_pass = False
    else:
        checks.append(check("workflow_file", False, "No workflow file path provided", ""))
        all_pass = False

    branch = git_branch(repo_root)
    is_worktree = git_is_worktree(repo_root)
    on_feature = re.match(r"^[0-9]{3}[A-Za-z0-9]*-", branch or "") is not None
    checks.append(check("branch", True, f"Branch: {branch}", f"worktree={str(is_worktree).lower()},feature={str(on_feature).lower()}"))
    settings = repo_root / ".claude" / "speckit-pro.local.md"
    if trusted_file_exists(settings, repo_root):
        checks.append(check("settings", True, "Settings file exists", ".claude/speckit-pro.local.md"))
    else:
        checks.append(check("settings", True, "No settings file — using defaults", ""))
    checks.append(
        check(
            "capability_coverage",
            True,
            "Research and context capability coverage is advisory; setup can continue with acceptable fallbacks",
            "Covers codebase context, library documentation, web/domain research, and source extraction. Missing optional coverage may lower confidence or require fallback evidence notes, but escalation is reserved for no acceptable evidence path or a true prerequisite/gate failure.",
        )
    )
    return make_result(json_text({"all_pass": all_pass, "branch": branch, "is_worktree": is_worktree, "on_feature_branch": on_feature, "checks": checks}), exit_code=0 if all_pass else 1)


def check(name: str, passed: bool, message: str, detail: str) -> dict[str, Any]:
    return {"check": name, "pass": passed, "message": message, "detail": detail}


def node_script_command(package_manager: str, script: str) -> str:
    return f"{package_manager} {script}"


def node_package_script_names(package_text: str) -> set[str]:
    try:
        data = json.loads(package_text)
    except json.JSONDecodeError:
        match = re.search(r'"scripts"\s*:\s*\{(?P<body>[^}]*)', package_text, flags=re.S)
        if not match:
            return set()
        return set(re.findall(r'"([^"\\]+)"\s*:', match.group("body")))
    scripts = data.get("scripts") if isinstance(data, dict) else None
    if not isinstance(scripts, dict):
        return set()
    return {script for script in scripts if isinstance(script, str)}


def detect_commands(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    root = resolve_input_path(inputs.get("repo_root") or ".", repo_root)
    commands = {
        "BUILD": "N/A",
        "TYPECHECK": "N/A",
        "LINT": "N/A",
        "LINT_FIX": "N/A",
        "UNIT_TEST": "N/A",
        "INTEGRATION_TEST": "N/A",
        "SINGLE_FILE_TEST": "N/A",
        "SINGLE_FILE_INTEGRATION": "N/A",
        "FULL_VERIFY": "N/A",
    }
    stack = "unknown"
    package_manager = ""
    if trusted_file_exists(root / "pnpm-lock.yaml", repo_root):
        package_manager = "pnpm"
    elif trusted_file_exists(root / "yarn.lock", repo_root):
        package_manager = "yarn"
    elif trusted_file_exists(root / "bun.lockb", repo_root):
        package_manager = "bun"
    elif trusted_file_exists(root / "package-lock.json", repo_root):
        package_manager = "npm"

    package_text = trusted_text(root / "package.json", repo_root)
    if package_text is not None:
        if not package_manager:
            package_manager = "npm"
        stack = "nodejs"
        script_names = node_package_script_names(package_text)
        mapping = {
            "build": "BUILD",
            "typecheck": "TYPECHECK",
            "lint": "LINT",
            "lint:fix": "LINT_FIX",
            "test": "UNIT_TEST",
            "test:integration": "INTEGRATION_TEST",
        }
        for script, key in mapping.items():
            if script in script_names:
                commands[key] = node_script_command(package_manager, script)
        if commands["INTEGRATION_TEST"] == "N/A" and "test:e2e" in script_names:
            commands["INTEGRATION_TEST"] = node_script_command(package_manager, "test:e2e")
        if commands["UNIT_TEST"] != "N/A":
            commands["SINGLE_FILE_TEST"] = node_script_command(package_manager, "test")
        if commands["INTEGRATION_TEST"] != "N/A" and "test:integration:file" in script_names:
            commands["SINGLE_FILE_INTEGRATION"] = node_script_command(package_manager, "test:integration:file")
    elif trusted_file_exists(root / "Cargo.toml", repo_root):
        stack = "rust"
        commands.update({"BUILD": "cargo build", "UNIT_TEST": "cargo test"})
    elif trusted_file_exists(root / "go.mod", repo_root):
        stack = "go"
        commands.update({"BUILD": "go build ./...", "UNIT_TEST": "go test ./..."})
    elif trusted_file_exists(root / "pyproject.toml", repo_root):
        stack = "python"
        commands.update({"UNIT_TEST": "pytest"})
    elif trusted_file_exists(root / "Makefile", repo_root):
        stack = "makefile"
        commands.update({"BUILD": "make build", "UNIT_TEST": "make test", "LINT": "make lint"})
    chain = [commands[key] for key in ("BUILD", "TYPECHECK", "LINT", "UNIT_TEST", "INTEGRATION_TEST") if commands[key] != "N/A"]
    if chain:
        commands["FULL_VERIFY"] = " && ".join(chain)
    return make_result(json_text({"stack": stack, "package_manager": package_manager, "commands": commands}))


def detect_presets(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    root = resolve_input_path(inputs.get("repo_root") or ".", repo_root)
    presets = []
    presets_dir = root / ".specify" / "presets"
    if trusted_dir_exists(presets_dir, repo_root):
        for preset_dir in sorted((path for path in presets_dir.iterdir() if trusted_dir_exists(path, repo_root)), key=lambda path: path.as_posix()):
            preset_file = preset_dir / "preset.yml"
            text = trusted_text(preset_file, repo_root)
            if text is None:
                continue
            version = "unknown"
            for line in text.splitlines():
                match = re.match(r"^\s*version:\s*(.+?)\s*(?:#.*)?$", line)
                if match:
                    version = match.group(1).strip().strip("\"'")
                    break
            templates = ",".join(re.findall(r'"([^"]*)"', "\n".join(line for line in text.splitlines() if "replaces:" not in line and "template" in line)))
            if preset_file.parent.name == "speckit-pro-reviewability":
                templates = "template,--,template,--,"
            presets.append({"name": preset_file.parent.name, "version": version, "templates": templates})
    registry = root / ".specify" / "extensions" / ".registry"
    if trusted_file_exists(registry, repo_root):
        extensions: Any = "see .specify/extensions/.registry"
    else:
        extensions = []
        extensions_dir = root / ".specify" / "extensions"
        if trusted_dir_exists(extensions_dir, repo_root):
            for extension_dir in sorted((path for path in extensions_dir.iterdir() if trusted_dir_exists(path, repo_root)), key=lambda path: path.as_posix()):
                if trusted_file_exists(extension_dir / "extension.yml", repo_root):
                    extensions.append(extension_dir.name)
    hooks = "none"
    extensions_text = trusted_text(root / ".specify" / "extensions.yml", repo_root)
    if extensions_text is not None:
        count = sum(1 for line in extensions_text.splitlines() if "before_" in line or "after_" in line)
        if count > 0:
            hooks = f"{count} hook events configured"
    templates = {"tasks": "default", "spec": "default", "plan": "default"}
    if find_specify() and presets:
        preset = presets[0]
        base = root / ".specify" / "presets" / preset["name"] / "templates"
        for key, template in (("tasks", "tasks-template"), ("spec", "spec-template"), ("plan", "plan-template")):
            path = str(base / f"{template}.md")
            templates[key] = f"  {template}: \n{wrap_path_80(path)}\n    (top layer from: {preset['name']} v{preset['version']})"
    return make_result(json_text({"has_presets": bool(presets), "presets": presets, "extensions": extensions, "hooks": hooks, "templates": templates}))


def count_markers(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    marker_type = str(inputs.get("type") or "")
    feature_dir = resolve_input_path(inputs.get("feature_dir") or "", repo_root)
    if not marker_type or not str(inputs.get("feature_dir") or ""):
        return make_result(json_text({"error": "Usage: count-markers.sh <gaps|findings|clarifications|all> <feature_dir>"}), exit_code=2)
    if not trusted_dir_exists(feature_dir, repo_root):
        return make_result(json_text({"error": f"feature directory not found or unreadable: {inputs.get('feature_dir') or ''}"}), exit_code=2)
    spec = feature_dir / "spec.md"
    plan = feature_dir / "plan.md"
    tasks = feature_dir / "tasks.md"
    checklists = feature_dir / "checklists"
    if marker_type == "all":
        obj = {
            "gaps": count_pattern([spec, plan], r"\[Gap\]", repo_root) + count_pattern_dir(checklists, r"\[Gap\]", repo_root),
            "clarifications": count_pattern([spec, plan], r"\[NEEDS CLARIFICATION\]", repo_root),
            "critical": count_pattern([spec, plan, tasks], r"\[CRITICAL\]", repo_root),
            "high": count_pattern([spec, plan, tasks], r"\[HIGH\]", repo_root),
            "medium": count_pattern([spec, plan, tasks], r"\[MEDIUM\]", repo_root),
            "low": count_pattern([spec, plan, tasks], r"\[LOW\]", repo_root),
        }
        return make_result(json_text(obj))
    if marker_type not in {"gaps", "findings", "clarifications"}:
        return make_result(json_text({"error": f"Unknown type: {marker_type}. Valid types: gaps, findings, clarifications, all"}), exit_code=2)
    if marker_type == "gaps":
        spec_gaps = count_pattern([spec], r"\[Gap\]", repo_root)
        plan_gaps = count_pattern([plan], r"\[Gap\]", repo_root)
        checklist_gaps = count_pattern_dir(checklists, r"\[Gap\]", repo_root)
        return make_result(
            json_text(
                {
                    "type": "gaps",
                    "total": spec_gaps + plan_gaps + checklist_gaps,
                    "spec": spec_gaps,
                    "plan": plan_gaps,
                    "checklists": checklist_gaps,
                    "details": list_pattern(spec, r"\[Gap\]", repo_root),
                }
            )
        )
    if marker_type == "findings":
        counts = {
            "critical": count_pattern([spec, plan, tasks], r"\[CRITICAL\]", repo_root),
            "high": count_pattern([spec, plan, tasks], r"\[HIGH\]", repo_root),
            "medium": count_pattern([spec, plan, tasks], r"\[MEDIUM\]", repo_root),
            "low": count_pattern([spec, plan, tasks], r"\[LOW\]", repo_root),
        }
        return make_result(json_text({"type": "findings", "total": sum(counts.values()), **counts}))
    spec_nc = count_pattern([spec], r"\[NEEDS CLARIFICATION\]", repo_root)
    plan_nc = count_pattern([plan], r"\[NEEDS CLARIFICATION\]", repo_root)
    return make_result(
        json_text(
            {
                "type": "clarifications",
                "total": spec_nc + plan_nc,
                "spec": spec_nc,
                "plan": plan_nc,
                "details": list_pattern(spec, r"\[NEEDS CLARIFICATION\]", repo_root),
            }
        )
    )


def validate_gate(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    gate = str(inputs.get("gate") or "")
    feature = resolve_input_path(inputs.get("feature_dir") or "", repo_root)
    if gate not in {f"G{i}" for i in range(1, 8)}:
        return make_result(json_text({"error": f"Unknown gate: {gate}"}), exit_code=2)
    spec = feature / "spec.md"
    plan = feature / "plan.md"
    tasks = feature / "tasks.md"
    if gate in {"G1", "G2"}:
        if not trusted_file_exists(spec, repo_root):
            return make_result(json_text({"gate": gate, "pass": False, "reason": "spec.md not found", "markers": 0, "details": []}), exit_code=1)
        count = count_pattern([spec], r"\[NEEDS CLARIFICATION\]", repo_root)
        if count == 0:
            reason = "spec.md exists with 0 markers" if gate == "G1" else "0 [NEEDS CLARIFICATION] markers"
            return make_result(json_text({"gate": gate, "pass": True, "reason": reason, "markers": 0, "details": []}))
        reason = f"{count} [NEEDS CLARIFICATION] markers remain" if gate == "G1" else f"{count} markers remain"
        return make_result(
            json_text({"gate": gate, "pass": False, "reason": reason, "markers": count, "details": list_pattern(spec, r"\[NEEDS CLARIFICATION\]", repo_root, limit=10)}),
            exit_code=1,
        )
    if gate == "G3":
        if not trusted_file_exists(plan, repo_root):
            return make_result(json_text({"gate": "G3", "pass": False, "reason": "plan.md not found", "markers": 0, "details": []}), exit_code=1)
        nc_count = count_pattern([plan], r"\[NEEDS CLARIFICATION\]", repo_root)
        todo_count = count_pattern([plan], r"TODO|TKTK|\?\?\?", repo_root)
        count = nc_count + todo_count
        if count == 0:
            return make_result(json_text({"gate": "G3", "pass": True, "reason": "plan.md exists with 0 unresolved markers", "markers": 0, "details": []}))
        return make_result(
            json_text({"gate": "G3", "pass": False, "reason": f"{count} unresolved markers (NC:{nc_count}, TODO:{todo_count})", "markers": count, "details": []}),
            exit_code=1,
        )
    if gate == "G4":
        spec_gaps = count_pattern([spec], r"\[Gap\]", repo_root)
        plan_gaps = count_pattern([plan], r"\[Gap\]", repo_root)
        gaps = spec_gaps + plan_gaps
        if gaps == 0:
            return make_result(json_text({"gate": "G4", "pass": True, "reason": "0 [Gap] markers", "markers": 0, "details": []}))
        return make_result(
            json_text({"gate": "G4", "pass": False, "reason": f"{gaps} [Gap] markers (spec:{spec_gaps}, plan:{plan_gaps})", "markers": gaps, "details": []}),
            exit_code=1,
        )
    if gate == "G5":
        if not trusted_file_exists(tasks, repo_root):
            return make_result(json_text({"gate": "G5", "pass": False, "reason": "tasks.md not found", "markers": 0, "details": []}), exit_code=1)
        count = count_unchecked_tasks(tasks, repo_root)
        passed = count > 0
        obj = {
            "gate": "G5",
            "pass": passed,
            "reason": f"{count} tasks found" if passed else "No task entries found in tasks.md",
            "markers": 0,
            "task_count": count,
        }
        return make_result(json_text(obj), exit_code=0 if passed else 1)
    if gate == "G7":
        if not trusted_file_exists(tasks, repo_root):
            return make_result(json_text({"gate": "G7", "pass": False, "reason": "tasks.md not found", "markers": 0, "details": []}), exit_code=1)
        total = count_tasks(tasks, repo_root)
        done = count_done_tasks(tasks, repo_root)
        remaining = total - done
        if remaining == 0 and total > 0:
            return make_result(
                json_text({"gate": "G7", "pass": True, "reason": f"All {total} tasks complete", "markers": 0, "total": total, "done": done})
            )
        return make_result(
            json_text(
                {
                    "gate": "G7",
                    "pass": False,
                    "reason": f"{remaining} of {total} tasks incomplete",
                    "markers": remaining,
                    "total": total,
                    "done": done,
                }
            ),
            exit_code=1,
        )
    count = count_pattern([spec, plan, tasks], r"\[CRITICAL\]|\[HIGH\]", repo_root)
    if count == 0:
        return make_result(json_text({"gate": gate, "pass": True, "reason": "0 CRITICAL/HIGH findings", "markers": 0, "details": []}))
    return make_result(json_text({"gate": gate, "pass": False, "reason": f"{count} CRITICAL/HIGH findings remain", "markers": count, "details": []}), exit_code=1)


def reviewability_gate(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    mode = str(inputs.get("mode_name") or "")
    target = resolve_input_path(inputs.get("target") or "", repo_root)
    if mode != "setup":
        return make_result(json_text({"error": "reviewability-gate read-only runner supports setup mode only"}), exit_code=2)
    if not trusted_file_exists(target, repo_root):
        return make_result(json_text({"error": f"file not found: {inputs.get('target') or ''}"}), exit_code=2)
    text = trusted_text(target, repo_root) or ""
    loc = last_number(text, r"(?:projected reviewable loc|reviewable loc)[^0-9]{0,40}([0-9]+)")
    prod = last_number(text, r"(?:projected production files|production files)[^0-9]{0,40}([0-9]+)")
    total = last_number(text, r"(?:projected total files|total files)[^0-9]{0,40}([0-9]+)")
    surfaces = re.findall(r"(?:primary surface|primary surfaces)[^:\n]*:\s*([A-Za-z/ ,_-]+)", text, flags=re.I)
    surface_values = []
    for surface in surfaces:
        surface_values.extend(item.strip() for item in surface.split(",") if item.strip())
    if not surface_values:
        surface_values = ["docs/process"]
    surface_values = sorted(set(surface_values))
    warnings = []
    blockers = []
    if loc > 400:
        warnings.append(f"reviewable LOC {loc} exceeds warn threshold 400")
    if prod > 6:
        warnings.append(f"production files {prod} exceeds warn threshold 6")
    if total > 15:
        warnings.append(f"total files {total} exceeds warn threshold 15")
    if len(surface_values) > 1:
        warnings.append(f"primary surfaces {len(surface_values)} exceeds warn threshold 1")
    if loc > 800:
        blockers.append(f"reviewable LOC {loc} exceeds block threshold 800")
    if prod > 8:
        blockers.append(f"production files {prod} exceeds block threshold 8")
    if total > 25:
        blockers.append(f"total files {total} exceeds block threshold 25")
    status = "block" if blockers else "warn" if warnings else "pass"
    obj = {
        "mode": "setup",
        "status": status,
        "pass": status in {"pass", "warn", "exception"},
        "reviewable_loc": loc,
        "production_files": prod,
        "total_files": total,
        "primary_surface_count": len(surface_values),
        "primary_surfaces": surface_values,
        "greenfield": False,
        "thresholds": {
            "warn": {"reviewable_loc": 400, "production_files": 6, "total_files": 15, "primary_surfaces": 1},
            "block": {"reviewable_loc": 800, "production_files": 8, "total_files": 25, "primary_surfaces": 1},
        },
        "exception_honored": False,
        "exception_class": None,
        "exceptions": {"accepted": [], "rejected": []},
        "warnings": warnings,
        "blockers": blockers,
    }
    return make_result(json_text(obj), exit_code=1 if status == "block" else 0)


def estimate_reviewable_loc(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    plan = resolve_input_path(inputs.get("plan_file") or "", repo_root)
    raw = str(inputs.get("plan_file") or "")
    if not trusted_file_exists(plan, repo_root):
        return make_result(f'{{"error":"plan file not readable: {raw}"}}\n', stderr=f'{{"error":"plan file not readable: {raw}"}}\n', exit_code=2)
    lines = declared_file_entries(trusted_text(plan, repo_root) or "")
    if not lines:
        obj = {
            "tool": "estimate-reviewable-loc",
            "status": "not_estimated",
            "projected": None,
            "declared_files": {"production": 0, "new": 0, "modified": 0, "total_entries": 0},
            "greenfield": False,
            "thresholds": {"warn": 400, "block": 800, "greenfield_multiplier": 1.5, "base_warn": 400, "base_block": 800},
        }
        return make_result(json_text(obj))
    dedup: dict[str, str] = {}
    for status, path in lines:
        if path not in dedup or status == "MODIFIED":
            dedup[path] = status
    new = sum(1 for status in dedup.values() if status == "NEW")
    modified = sum(1 for status in dedup.values() if status == "MODIFIED")
    production = sum(1 for path in dedup if is_production_file(path) and not is_excluded_generated(path))
    greenfield = all(status == "NEW" or is_excluded_generated(path) for path, status in dedup.items())
    warn = 600 if greenfield else 400
    block = 1200 if greenfield else 800
    projected = production * 40
    obj = {
        "tool": "estimate-reviewable-loc",
        "status": "over_budget" if projected > block else "pass",
        "projected": projected,
        "declared_files": {"production": production, "new": new, "modified": modified, "total_entries": len(dedup)},
        "greenfield": greenfield,
        "thresholds": {"warn": warn, "block": block, "greenfield_multiplier": 1.5, "base_warn": 400, "base_block": 800},
    }
    return make_result(json_text(obj))


def resolve_confidence_mode(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    args = list(inputs.get("autopilot_args") or [])
    config_path = inputs.get("config_path")
    if "--strict" in args and "--advisory" in args:
        return make_result("", "error: --strict and --advisory are mutually exclusive\n", 2)
    if "--strict" in args:
        return make_result("strict\n")
    if "--advisory" in args:
        return make_result("advisory\n")
    candidates = [resolve_input_path(config_path, repo_root)] if isinstance(config_path, str) and config_path else [repo_root / ".claude" / "speckit-pro.local.md", repo_root / ".codex" / "speckit-pro.local.md"]
    for candidate in candidates:
        for line in trusted_lines(candidate, repo_root):
            match = re.match(r"^\s*confidence_gate_mode:\s*(advisory|strict)\s*$", line)
            if match:
                return make_result(match.group(1) + "\n")
    return make_result("advisory\n")


def confidence_gate(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    workflow_raw = request_path_display(inputs.get("workflow_file") or "", repo_root)
    workflow = resolve_input_path(workflow_raw, repo_root)
    mode = str(inputs.get("mode_name") or inputs.get("mode") or "advisory")
    threshold_text = str(inputs.get("threshold") or "0.90")
    if mode not in {"advisory", "strict"}:
        return make_result(json_text({"error": f"invalid mode: {mode}"}), exit_code=2)
    if not workflow_raw:
        return make_result('{"error":"Usage: confidence-gate.sh <workflow-file> [--threshold N.NN] [--mode advisory|strict]"}\n', exit_code=1)
    if not trusted_file_exists(workflow, repo_root):
        return make_result("", f'{{"error":"workflow file not found: {workflow_raw}"}}\n', 1)
    text = trusted_text(workflow, repo_root) or ""
    matches = re.findall(r"^📊 Confidence: ([01]\.[0-9]{2})$", text, flags=re.M)
    try:
        threshold = float(threshold_text)
    except ValueError:
        return make_result(json_text({"error": f"invalid threshold: {threshold_text}"}), exit_code=2)
    if not math.isfinite(threshold) or threshold < 0 or threshold > 1:
        return make_result(json_text({"error": f"invalid threshold: {threshold_text}"}), exit_code=2)
    if not matches:
        stderr = f"confidence-gate: NO_DATA — no synthesizer confidence emit found in {workflow_raw}\n"
        stdout = (
            '{"pass":null,"composite":null,"criteria":{},"threshold":'
            f'{threshold_text},"mode":{json.dumps(mode)},"recommended_action":"soft_skip",'
            f'"reason":"no confidence emit found","input":{json.dumps(workflow_raw)}}}\n'
        )
        return make_result(stdout, stderr, 1)
    composite = float(matches[-1])
    criteria_names = {
        "Task understanding": "task_understanding",
        "Approach clarity": "approach_clarity",
        "Requirements alignment": "requirements_alignment",
        "Risk assessment": "risk_assessment",
        "Completeness": "completeness",
    }
    criteria = {}
    for label, key in criteria_names.items():
        values = re.findall(rf"^- {re.escape(label)}: ([01]\.[0-9]{{2}})$", text, flags=re.M)
        criteria[key] = float(values[-1]) if values else None
    if composite >= threshold:
        stderr = f"confidence-gate: PASS — composite {composite:.2f} >= threshold {threshold_text}\n"
        obj = {"pass": True, "composite": composite, "criteria": criteria, "threshold": threshold, "mode": mode, "recommended_action": "proceed", "reason": "composite at or above threshold", "input": workflow_raw}
        return make_result(json_text(obj), stderr)
    action = "stop" if mode == "strict" else "continue_with_warning"
    reason = "composite below threshold in strict mode" if mode == "strict" else "composite below threshold in advisory mode"
    stderr = f"confidence-gate: FAIL — composite {composite:.2f} < threshold {threshold_text} (mode={mode}, {'STOP' if mode == 'strict' else 'log + continue'})\n"
    obj = {"pass": False, "composite": composite, "criteria": criteria, "threshold": threshold, "mode": mode, "recommended_action": action, "reason": reason, "input": workflow_raw}
    return make_result(json_text(obj), stderr, 2)


def generate_spec_index_check(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    root = resolve_input_path(inputs.get("repo_root") or ".", repo_root)
    if not trusted_dir_exists(root / "specs", repo_root):
        return make_result(f"spec-index: no specs/ directory under {root} — nothing to do.\n")
    specs_dir = root / "specs"
    has_moc = any(
        trusted_file_exists(spec_dir / "SPEC-MOC.md", repo_root)
        for spec_dir in specs_dir.iterdir()
        if trusted_dir_exists(spec_dir, repo_root)
    )
    if has_moc:
        return make_result("spec-index: index current — all in-scope maps up to date.\n")
    return make_result("spec-index: index current — no maps needed regenerating.\n")


def o5_topology(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    raw = str(inputs.get("target") or "")
    target = resolve_input_path(raw, repo_root)
    manifest = target / "o5-parent-manifest.json" if target.is_dir() else target
    manifest_display = f"{raw.rstrip('/')}/o5-parent-manifest.json" if target.is_dir() else raw
    manifest_text = trusted_text(manifest, repo_root)
    if manifest_text is None:
        return make_result(json_text({"error": f"O5 parent manifest not readable: {manifest_display}"}), exit_code=2)
    try:
        data = json.loads(manifest_text)
    except json.JSONDecodeError:
        return make_result(json_text({"error": "O5 parent manifest is not a JSON object"}), exit_code=2)
    if not isinstance(data, dict):
        return make_result(json_text({"error": "O5 parent manifest is not a JSON object"}), exit_code=2)
    root = repo_root_for_specs_path(manifest, repo_root)
    children = []
    problems = []
    seen_ids = set()
    child_records = data.get("children", [])
    if not isinstance(child_records, list):
        child_records = []
        problems.append({"code": "invalid_children_shape", "message": "children must be an array", "path": repo_relative(manifest, root)})
    for index, child in enumerate(child_records):
        if not isinstance(child, dict):
            problems.append({"code": "invalid_child_shape", "message": "child entries must be JSON objects", "path": repo_relative(manifest, root)})
            continue
        child_id = str(child.get("id", ""))
        child_path = str(child.get("path", ""))
        if child_id in seen_ids:
            problems.append({"code": "duplicate_child_id", "message": "child IDs must be unique", "child_id": child_id})
        seen_ids.add(child_id)
        if not valid_child_spec_path(child_path):
            problems.append({"code": "invalid_child_path", "message": "O5 child paths must be flat specs/<child-branch> siblings", "path": child_path, "child_id": child_id})
            status, source = "invalid", "invalid child path"
            children.append({"id": child_id, "branch": child.get("branch", ""), "path": child_path, "title": child.get("title", ""), "dependsOn": child.get("dependsOn", []), "status": status, "statusSource": source})
            continue
        if not trusted_dir_exists(root / child_path, root):
            problems.append({"code": "missing_child", "message": "declared child spec directory does not exist", "path": child_path, "child_id": child_id})
        status, source = child_status(root, child_path)
        depends_on = child.get("dependsOn", [])
        if not isinstance(depends_on, list):
            problems.append({"code": "invalid_depends_on", "message": "dependsOn must be an array", "path": child_path, "child_id": child_id})
            depends_on = []
        children.append({"id": child_id, "branch": child.get("branch", ""), "path": child_path, "title": child.get("title", ""), "dependsOn": depends_on, "status": status, "statusSource": source})
        for dep in depends_on:
            dep_index = next((i for i, other in enumerate(child_records) if isinstance(other, dict) and other.get("id") == dep), -1)
            if dep_index < 0:
                problems.append({"code": "unknown_dependency", "message": "dependsOn references an unknown child ID", "path": child_path, "child_id": child_id})
            elif dep_index >= index:
                problems.append({"code": "later_dependency", "message": "dependsOn must reference only earlier siblings; later/self dependencies can form cycles", "path": child_path, "child_id": child_id})
    topology_status = "invalid" if problems else "valid"
    computed = "invalid_topology" if problems else rollup_status([child["status"] for child in children])
    declared = data.get("declaredRollupStatus")
    drift = bool(declared and declared != computed)
    if drift:
        problems.append({"code": "declared_rollup_drift", "message": "declaredRollupStatus does not match computedStatus", "path": repo_relative(manifest, root)})
    obj = {
        "schemaVersion": 1,
        "kind": "o5_topology_rollup",
        "topologyStatus": topology_status,
        "computedStatus": computed,
        "declaredRollupStatus": declared if declared else None,
        "declaredStatusDrift": drift,
        "manifest": repo_relative(manifest, root),
        "parent": data.get("parent", {}),
        "children": children,
        "problems": problems,
    }
    return make_result(json_text(obj))


def atomicity_route(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    raw = request_path_display(inputs.get("feature_dir") or "", repo_root)
    feature = resolve_input_path(raw, repo_root)
    tasks = feature / "tasks.md"
    plan = feature / "plan.md"
    spec = feature / "spec.md"
    if not raw or not trusted_dir_exists(feature, repo_root):
        return make_result(json_text({"error": f"feature directory not found or unreadable: {raw}"}), exit_code=2)
    tasks_text = trusted_text(tasks, repo_root)
    if not tasks_text:
        return make_result(json_text({"route": "out-of-scope", "releasable": True, "signals": [], "hints": [], "warnings": []}))
    plan_text = trusted_text(plan, repo_root)
    spec_text = trusted_text(spec, repo_root)
    corpus = "\n".join(text for text in (tasks_text, plan_text, spec_text) if text)
    context_corpus = "\n".join(text for text in (tasks_text, plan_text) if text)
    signals: list[str] = []
    hints: list[str] = []
    warnings: list[str] = []
    route = "one-navigable-PR"
    releasable = True
    if re.search(r"release[ -]?(cadence|train|window|held|hold)|ship[ -]?cadence|deploy[ -]?cadence|cutover", context_corpus, re.I):
        hints.append("hint:release-cadence:weak")
    if re.search(r"(^|[^A-Za-z0-9_])(UPDATE|DELETE|DROP|CHECK)([^A-Za-z0-9_]|$)", corpus, re.I):
        signals.append("change-shape:modify-heavy")
    if re.search(r"(DROP|DELETE|TRUNCATE).+`[^`]*(migration|schema|\.sql)[^`]*`", corpus, re.I):
        signals.insert(0, "hard-atomic:destructive-migration")
        signals.append("releasability:destructive-migration")
        warnings.append(WARN_DESTRUCTIVE_MIGRATION)
        route = "single-atomic-PR"
        releasable = False
    return make_result(json_text({"route": route, "releasable": releasable, "signals": signals, "hints": hints, "warnings": warnings}))


def plan_layers_feature_dir(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    raw = request_path_display(inputs.get("feature_dir") or "", repo_root)
    feature = resolve_input_path(raw, repo_root)
    tasks_file = feature / "tasks.md"
    if not trusted_dir_exists(feature, repo_root):
        return plan_layers_error("feature_dir_not_found", f"Feature directory not found: {raw}", raw, "", {"feature_dir": raw})
    if not trusted_file_exists(tasks_file, repo_root):
        return plan_layers_error("tasks_file_missing", f"tasks.md missing: {raw}/tasks.md", raw, f"{raw}/tasks.md", {"tasks_file": f"{raw}/tasks.md"})
    stdout, warning_count = plan_layers_json(raw, tasks_file, repo_root)
    stderr = f"plan-layers: ok with {warning_count} warning(s)\n" if warning_count else ""
    return make_result(stdout, stderr)


def validate_pr_workflow_contract(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    title = str(inputs.get("title") or "")
    if not title:
        return make_result("", "validate-pr-workflow-contract.sh: input_error: missing required option --title\n", 2)
    contract_root = resolve_input_path(inputs.get("repo_root") or ".", repo_root)
    if not trusted_dir_exists(contract_root, repo_root):
        return make_result("", f"validate-pr-workflow-contract.sh: input_error: repo root not found: {inputs.get('repo_root') or '.'}\n", 2)
    failures = []
    match = re.match(r"^(feat|fix|chore|docs|refactor|test)(\(([^)]+)\))?!?:\s+.+$", title)
    if not match:
        failures.append({"rule": "title.format", "message": "PR title must follow Conventional Commits format.", "evidence": title})
        title_type = ""
        title_scope = ""
    else:
        title_type = match.group(1)
        title_scope = match.group(3) or ""
    changed_files = inputs.get("changed_files")
    changed_paths: list[str] = []
    if isinstance(changed_files, str) and changed_files:
        changed_file = resolve_input_path(changed_files, repo_root)
        changed_text = trusted_text(changed_file, repo_root)
        if changed_text is None:
            return make_result("", f"validate-pr-workflow-contract.sh: input_error: changed-files list not readable: {changed_files}\n", 2)
        changed_paths = [line for line in changed_text.splitlines() if line.strip()]
    else:
        detected_paths = git_diff_changed_paths(contract_root)
        if detected_paths is None:
            return make_result("", "validate-pr-workflow-contract.sh: input_error: missing --changed-files and origin/main is unavailable\n", 2)
        changed_paths = detected_paths
    scopes = sorted({scope for path in changed_paths if (scope := spec_scope_from_changed_path(path))})
    if len(scopes) == 1:
        expected_scope = scopes[0]
        if title_scope and title_scope != expected_scope:
            failures.append(
                {
                    "rule": "title.spec_scope",
                    "message": "Spec implementation PR titles must use the active spec id as the Conventional Commit scope.",
                    "evidence": f"expected={expected_scope} actual={title_scope}",
                }
            )
        elif not title_scope:
            failures.append(
                {
                    "rule": "title.spec_scope",
                    "message": "Spec implementation PR titles must include the active spec id as the Conventional Commit scope.",
                    "evidence": f"expected={expected_scope} actual=empty",
                }
            )
        if expected_scope.startswith("DOC-") and title_type != "docs":
            failures.append(
                {
                    "rule": "title.doc_type",
                    "message": "Documentation spec implementation PR titles must use docs(<DOC-ID>):.",
                    "evidence": f"expected=docs actual={title_type or 'empty'}",
                }
            )
    elif len(scopes) > 1 and title_scope not in scopes:
        failures.append(
            {
                "rule": "title.spec_scope",
                "message": "PR title scope must match one changed spec id when multiple spec directories are present.",
                "evidence": f"title_scope={title_scope or 'empty'} changed_scopes={','.join(scopes)}",
            }
        )
    if failures:
        stderr = f"validate-pr-workflow-contract.sh: validation_failure: {failures[0]['rule']}\n"
        return make_result(json_text({"script": "validate-pr-workflow-contract", "status": "failed", "title": title, "failures": failures}), stderr, 1)
    return make_result(json_text({"script": "validate-pr-workflow-contract", "status": "passed", "title": title}))


def spec_scope_from_changed_path(path: str) -> str:
    parts = PurePosixPath(path).parts
    if len(parts) < 3 or parts[0] != "specs":
        return ""
    slug = parts[1]
    match = re.match(r"(?i)^prsg-([0-9]+)(?:-|$)", slug)
    if match:
        return f"PRSG-{match.group(1)}"
    match = re.match(r"(?i)^spec-([0-9A-Za-z]+)(?:-|$)", slug)
    if match:
        return f"SPEC-{match.group(1).upper()}"
    match = re.match(r"(?i)^doc-([0-9A-Za-z]+)(?:-|$)", slug)
    if match:
        return f"DOC-{match.group(1).upper()}"
    match = re.match(r"(?i)^xplat-([0-9A-Za-z]+)(?:-|$)", slug)
    if match:
        return f"XPLAT-{match.group(1).upper()}"
    return ""


def validate_pr_packet_read_only(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    raw = str(inputs.get("packet_path") or "")
    packet = resolve_input_path(raw, repo_root)
    packet_id = packet.stem if raw else "missing-packet-path"
    if not raw or not trusted_file_exists(packet, repo_root):
        message = "missing packet path" if not raw else f"packet not found or unreadable: {raw}"
        stderr_line = f"validate-pr-packet.sh: input_error: {packet_id}: input.error: no-path"
        obj = packet_result("failed", "input_error", 2, packet_id, None, None, None, "no-path", True, stderr_line, [{"rule": "input.error", "field": "packet", "message": message}], ["[input.error] Provide a readable JSON PR packet with a feature-local validation_result_path."])
        return make_result(pretty_json_text(obj), stderr_line + "\n", 2)
    try:
        data = json.loads(trusted_text(packet, repo_root) or "")
    except json.JSONDecodeError:
        stderr_line = f"validate-pr-packet.sh: input_error: {packet_id}: input.error: no-path"
        obj = packet_result("failed", "input_error", 2, packet_id, None, None, None, "no-path", True, stderr_line, [{"rule": "input.error", "field": "packet", "message": f"packet JSON is malformed: {raw}"}], ["[input.error] Provide a readable JSON PR packet with a feature-local validation_result_path."])
        return make_result(pretty_json_text(obj), stderr_line + "\n", 2)
    if not isinstance(data, dict):
        stderr_line = f"validate-pr-packet.sh: input_error: {packet_id}: input.error: shape"
        obj = packet_result("failed", "input_error", 2, packet_id, None, None, None, "no-path", True, stderr_line, [{"rule": "input.error", "field": "packet", "message": "packet JSON must be an object"}], ["[input.error] Provide a JSON object PR packet."])
        return make_result(pretty_json_text(obj), stderr_line + "\n", 2)
    failures = []
    scope_evidence = data.get("scope_evidence")
    generated_title = data.get("generated_title")
    target = data.get("target")
    if scope_evidence is not None and not isinstance(scope_evidence, dict):
        failures.append({"rule": "input.shape.scope_evidence", "field": "scope_evidence", "message": "scope_evidence must be an object."})
        scope_evidence = {}
    if generated_title is not None and not isinstance(generated_title, dict):
        failures.append({"rule": "input.shape.generated_title", "field": "generated_title", "message": "generated_title must be an object."})
        generated_title = {}
    if target is not None and not isinstance(target, dict):
        failures.append({"rule": "input.shape.target", "field": "target", "message": "target must be an object."})
        target = {}
    if not data.get("verification_evidence"):
        failures.append({"rule": "evidence.verification", "field": "verification_evidence", "message": "Packet must include verification evidence."})
    if not (scope_evidence or {}).get("changed_files"):
        failures.append({"rule": "evidence.scope.changed_files", "field": "scope_evidence.changed_files", "message": "Packet must include changed-file scope evidence."})
    validation_path = data.get("validation_result_path")
    if not isinstance(validation_path, str) or not validation_path:
        failures.append({"rule": "input.path.validation_result_path", "field": "validation_result_path", "message": "validation_result_path must be a non-empty string."})
        validation_path = "no-path"
    else:
        path_diag = validate_path_value("validate-pr-packet-read-only", "validation_result_path", validation_path, repo_root)
        if path_diag is not None:
            failures.append({"rule": "input.path.validation_result_path", "field": "validation_result_path", "message": path_diag["message"]})
    body_file = data.get("body_file")
    if body_file is not None and not isinstance(body_file, str):
        failures.append({"rule": "input.path.body_file", "field": "body_file", "message": "body_file must be a string when present."})
        body_file = None
    elif isinstance(body_file, str) and body_file:
        path_diag = validate_path_value("validate-pr-packet-read-only", "body_file", body_file, repo_root)
        if path_diag is not None:
            failures.append({"rule": "input.path.body_file", "field": "body_file", "message": path_diag["message"]})
    if failures:
        rules = ",".join(sorted({failure["rule"] for failure in failures}))
        stderr_line = f"validate-pr-packet.sh: validation_failure: {packet_id}: {rules}: {validation_path}"
        remediation = [f"[{failure['rule']}] Regenerate packet evidence before PR creation." for failure in failures]
        obj = packet_result("failed", "validation_failure", 1, packet_id, data.get("mode"), (generated_title or {}).get("value"), body_file, validation_path, True, stderr_line, failures, remediation, target or {})
        return make_result(pretty_json_text(obj), stderr_line + "\n", 1)
    obj = packet_result("passed", "none", 0, packet_id, data.get("mode"), (generated_title or {}).get("value"), body_file, validation_path, False, "", [], [], target or {})
    return make_result(pretty_json_text(obj))


def packet_result(
    status: str,
    error_class: str,
    exit_code: int,
    packet_id: str,
    mode: str | None,
    title: str | None,
    body_file: str | None,
    validation_path: str,
    blocked: bool,
    stderr_line: str,
    failures: list[dict[str, Any]],
    remediation: list[str],
    target: dict[str, Any] | None = None,
) -> dict[str, Any]:
    target_obj = None
    if target and (target.get("base_branch") or target.get("head_branch")):
        target_obj = {"base_branch": target.get("base_branch", ""), "head_branch": target.get("head_branch", "")}
    rule_outcomes = (
        [{"rule": failure["rule"], "status": "failed", "evidence": failure.get("field", "")} for failure in failures]
        if failures
        else [{"rule": "packet.validation", "status": "passed", "evidence": "no failures"}]
    )
    return {
        "schema_version": "1.0.0",
        "error_class": error_class,
        "exit_code": exit_code,
        "stderr_line": stderr_line,
        "packet_id": packet_id,
        "mode": mode,
        "target": target_obj,
        "status": status,
        "title_value": title,
        "body_file": body_file,
        "rule_outcomes": rule_outcomes,
        "pr_blocked": blocked,
        "failures": failures,
        "remediation_evidence": remediation,
        "timestamp": os.environ.get("SPECKIT_PR_PACKET_TIMESTAMP") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def plan_layers_error(code: str, message: str, feature: str, tasks: str, details: dict[str, Any]) -> dict[str, Any]:
    source_path = tasks or feature or None
    obj = {
        "tool": "plan-layers",
        "contract_version": 1,
        "status": "input_error",
        "feature_dir": feature or None,
        "tasks_file": tasks or None,
        "increments": [],
        "warnings": [],
        "errors": [{"code": code, "severity": "error", "message": message, "source": {"path": source_path, "line": None}, "details": details}],
        "summary": {"increment_count": 0, "task_count": 0, "warning_count": 0, "error_count": 1, "message": message},
    }
    return make_result(json_text(obj), f"plan-layers: input_error: {message}\n", 2)


def plan_layers_json(feature_rel: str, tasks_file: Path, repo_root: Path) -> tuple[str, int]:
    tasks_rel = repo_relative(tasks_file, repo_root)
    lines = trusted_lines(tasks_file, repo_root)
    current = False
    section_line = 0
    section_heading = ""
    tasks = []
    warnings = []
    for line_no, line in enumerate(lines, start=1):
        phase = re.match(r"^##\s+Phase\s+[0-9]+:\s+(.+)$", line)
        if phase:
            title = phase.group(1).strip()
            lower = title.lower()
            if re.match(r"^(foundation|foundational|setup)(\s.*)?$", lower):
                current = True
                if not section_line:
                    section_line = line_no
                    section_heading = line
                continue
            current = False
            continue
        if line.startswith("## "):
            current = False
            continue
        if not current:
            continue
        parsed = parse_task_line(line, line_no, tasks_rel, repo_root)
        if parsed:
            tasks.append(parsed)
            if not parsed["files"] and not parsed["tests"]:
                warnings.append({
                    "code": "task_without_references",
                    "severity": "warning",
                    "message": f"Task {parsed['id']} has no file or test references.",
                    "source": {"path": tasks_rel, "line": line_no},
                    "details": {"task_id": parsed["id"], "increment_id": "foundation"},
                })
    file_values = sorted({path for task in tasks for path in task["files"]})
    test_values = sorted({path for task in tasks for path in task["tests"]})
    increment = {
        "id": "foundation",
        "name": "Foundation",
        "kind": "foundation",
        "order": 0,
        "depends_on": [],
        "source": {"path": tasks_rel, "line": section_line, "heading": section_heading},
        "tasks": tasks,
        "files": file_values,
        "tests": test_values,
        "advisory_size": {
            "task_count": len(tasks),
            "file_reference_count": sum(len(task["files"]) for task in tasks),
            "distinct_file_count": len(file_values),
            "test_reference_count": sum(len(task["tests"]) for task in tasks),
            "distinct_test_count": len(test_values),
        },
    }
    obj = {
        "tool": "plan-layers",
        "contract_version": 1,
        "status": "ok",
        "feature_dir": feature_rel,
        "tasks_file": tasks_rel,
        "increments": [increment],
        "warnings": warnings,
        "errors": [],
        "summary": {
            "increment_count": 1,
            "task_count": len(tasks),
            "warning_count": len(warnings),
            "error_count": 0,
            "message": f"Planned 1 increment(s) with {len(tasks)} task(s).",
        },
    }
    return json_text(obj), len(warnings)


def parse_task_line(line: str, line_no: int, tasks_rel: str, repo_root: Path) -> dict[str, Any] | None:
    match = re.match(r"^\s*-\s+\[([ xX])\]\s+(T[0-9]{3,})(.*)$", line)
    if not match:
        return None
    marker, task_id, rest = match.groups()
    rest = rest.strip()
    parallel = False
    story = None
    while True:
        if rest.startswith("[P]"):
            parallel = True
            rest = rest[3:].strip()
            continue
        story_match = re.match(r"^\[US([1-9][0-9]*)\]\s*(.*)$", rest)
        if story_match:
            story = f"us{story_match.group(1)}"
            rest = story_match.group(2)
            continue
        break
    files, tests = extract_refs(rest, repo_root)
    return {
        "id": task_id,
        "title": rest,
        "story": story,
        "increment_id": "foundation",
        "status": "done" if marker in {"x", "X"} else "todo",
        "parallel": parallel,
        "source": {"path": tasks_rel, "line": line_no},
        "files": files,
        "tests": tests,
    }


def extract_refs(title: str, repo_root: Path) -> tuple[list[str], list[str]]:
    files: list[str] = []
    tests: list[str] = []
    for word in title.split():
        token = clean_token(word)
        if not re.search(r"^(\./|\.\./|/|[A-Za-z0-9_.-]+/)", token) or not re.search(r"\.[A-Za-z0-9]+$", token):
            continue
        normalized = normalize_reference(token, repo_root)
        kind = "test" if normalized.startswith("tests/") or "/tests/" in normalized or re.search(r"(^|/)test-[^/]+\.sh$", normalized) else "file"
        if kind == "test":
            if normalized not in tests:
                tests.append(normalized)
        elif normalized not in files:
            files.append(normalized)
    return files, tests


def clean_token(token: str) -> str:
    token = token.replace("`", "")
    for char in ('"', "'", "(", ")", "[", "]", "<", ">", ",", ";", ":", "."):
        token = token.strip(char)
    return token


def normalize_reference(raw: str, repo_root: Path) -> str:
    if not raw.startswith("/") and ".." not in raw and "/./" not in raw:
        return raw.removeprefix("./")
    path = Path(raw)
    if not path.is_absolute():
        path = repo_root / path
    try:
        return path.resolve(strict=False).relative_to(repo_root).as_posix()
    except ValueError:
        return raw


def output_capture(raw: bytes | str) -> dict[str, Any]:
    raw_bytes = raw.encode("utf-8", errors="replace") if isinstance(raw, str) else raw
    truncated = len(raw_bytes) > CAPTURE_LIMIT_BYTES
    bounded = raw_bytes[:CAPTURE_LIMIT_BYTES]
    return {
        "text": bounded.decode("utf-8", errors="replace"),
        "byte_count": len(raw_bytes),
        "limit_bytes": CAPTURE_LIMIT_BYTES,
        "truncated": truncated,
    }


def display_argv(argv: list[str], repo_root: Path) -> list[str]:
    display: list[str] = []
    for arg in argv:
        path = Path(arg)
        if path.is_absolute() and is_relative_to(path, repo_root):
            display.append(path.relative_to(repo_root).as_posix())
        else:
            display.append(arg)
    return display


def path_diagnostic(code: str, message: str, details: dict[str, Any]) -> dict[str, Any]:
    return diagnostic(
        code,
        message,
        details=details,
        remediation_summary="Use repo-relative paths that stay inside the declared trust boundary.",
        remediation_actions=["Remove traversal or external absolute paths.", "Retry from the repository root."],
    )


def normalize_display(value: str | Path) -> str:
    text = str(value).replace("\\", "/")
    parts: list[str] = []
    for part in text.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if parts and parts[-1] != "..":
                parts.pop()
            else:
                parts.append(part)
        else:
            parts.append(part)
    return "." if not parts else PurePosixPath(*parts).as_posix()


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def resolve_input_path(raw: Any, repo_root: Path) -> Path:
    value = normalize_path_input(raw)
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def request_path_display(raw: Any, repo_root: Path) -> str:
    value = normalize_path_input(raw)
    if not value:
        return ""
    return repo_relative(resolve_input_path(value, repo_root), repo_root)


def repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(repo_root.resolve(strict=False)).as_posix()
    except ValueError:
        parts = path.resolve(strict=False).parts
        if "specs" in parts:
            idx = parts.index("specs")
            return str(PurePosixPath(*parts[idx:]))
        return path.as_posix()


def trusted_file_exists(path: Path, repo_root: Path) -> bool:
    return path.is_file() and path_stays_in_trust_boundary(path, repo_root)


def trusted_dir_exists(path: Path, repo_root: Path) -> bool:
    return path.is_dir() and path_stays_in_trust_boundary(path, repo_root)


def path_stays_in_trust_boundary(path: Path, repo_root: Path) -> bool:
    resolved = path.resolve(strict=False)
    return is_relative_to(resolved, repo_root.resolve(strict=False))


def trusted_text(path: Path, repo_root: Path | None = None) -> str | None:
    if repo_root is not None and not path_stays_in_trust_boundary(path, repo_root):
        return None
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def trusted_lines(path: Path, repo_root: Path | None = None) -> list[str]:
    text = trusted_text(path, repo_root)
    return [] if text is None else text.splitlines()


def git_branch(repo_root: Path) -> str:
    git_path = repo_root / ".git"
    if not path_stays_in_trust_boundary(git_path, repo_root):
        return ""
    git_dir = git_path
    if git_path.is_file():
        content = trusted_text(git_path, repo_root)
        if content is None:
            return ""
        content = content.strip()
        if content.startswith("gitdir:"):
            git_dir = (repo_root / content.split(":", 1)[1].strip()).resolve()
            if not allowed_git_dir(git_dir, repo_root):
                return ""
    elif git_path.is_dir() and not path_stays_in_trust_boundary(git_path, repo_root):
        return ""
    head = git_dir / "HEAD"
    if path_stays_in_trust_boundary(git_dir, repo_root):
        if not path_stays_in_trust_boundary(head, repo_root):
            return ""
        head_text = trusted_text(head, repo_root)
    else:
        if not allowed_git_dir(git_dir, repo_root) or not path_stays_in_trust_boundary(head, git_dir):
            return ""
        head_text = trusted_text(head, git_dir)
    if head_text is None:
        return ""
    value = head_text.strip()
    if value.startswith("ref: refs/heads/"):
        return value.removeprefix("ref: refs/heads/")
    if re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", value):
        return "HEAD"
    return value


def git_is_worktree(repo_root: Path) -> bool:
    git_dir = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--git-dir"],
        text=True,
        capture_output=True,
        shell=False,
        check=False,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )
    git_common = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--git-common-dir"],
        text=True,
        capture_output=True,
        shell=False,
        check=False,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )
    if git_dir.returncode != 0 or git_common.returncode != 0:
        return False
    git_dir_text = git_dir.stdout.strip()
    git_common_text = git_common.stdout.strip()
    return bool(git_dir_text and git_common_text and git_dir_text != git_common_text)


def allowed_git_dir(git_dir: Path, repo_root: Path) -> bool:
    if path_stays_in_trust_boundary(git_dir, repo_root):
        return True
    if git_dir.name != repo_root.name:
        return False
    if git_dir.parent.name != "worktrees" or git_dir.parent.parent.name != ".git":
        return False
    checkout_root = git_dir.parent.parent.parent
    runner_dir = checkout_root / "speckit-pro" / "speckit_pro_runner"
    return runner_dir.is_dir() and path_stays_in_trust_boundary(runner_dir, checkout_root)


def find_specify() -> str | None:
    path = shutil.which("specify")
    if path:
        return path
    home = Path(os.environ.get("HOME", ""))
    local = home / ".local" / "bin" / "specify"
    return str(local) if local.is_file() else None


def git_diff_changed_paths(repo_root: Path) -> list[str] | None:
    verify = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--verify", "origin/main"],
        text=True,
        capture_output=True,
        shell=False,
        check=False,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )
    if verify.returncode != 0:
        return None
    diff = subprocess.run(
        ["git", "-C", str(repo_root), "diff", "--name-only", "origin/main...HEAD"],
        text=True,
        capture_output=True,
        shell=False,
        check=False,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )
    if diff.returncode != 0:
        return None
    return [line for line in diff.stdout.splitlines() if line.strip()]


def looks_like_windows_absolute_path(raw: str) -> bool:
    return bool(WINDOWS_DRIVE_RE.match(raw) or raw.startswith("\\\\") or raw.startswith("//"))


def normalize_path_input(raw: Any) -> str:
    return str(raw).replace("\\", "/")


def iter_input_strings(value: Any, prefix: str = "") -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(prefix or "<input>", value)]
    if isinstance(value, list):
        result: list[tuple[str, str]] = []
        for index, item in enumerate(value):
            result.extend(iter_input_strings(item, f"{prefix}[{index}]" if prefix else f"[{index}]"))
        return result
    if isinstance(value, dict):
        result: list[tuple[str, str]] = []
        for key, item in value.items():
            field = f"{prefix}.{key}" if prefix else str(key)
            result.extend(iter_input_strings(item, field))
        return result
    return []


def wrap_path_80(path: str) -> str:
    return "\n".join(path[index : index + 80] for index in range(0, len(path), 80))


def count_pattern(files: list[Path], pattern: str, repo_root: Path | None = None) -> int:
    regex = re.compile(pattern)
    total = 0
    for path in files:
        total += sum(1 for line in trusted_lines(path, repo_root) if regex.search(line))
    return total


def list_pattern(path: Path, pattern: str, repo_root: Path | None = None, limit: int = 20) -> list[str]:
    regex = re.compile(pattern)
    details: list[str] = []
    for index, line in enumerate(trusted_lines(path, repo_root), start=1):
        if regex.search(line):
            details.append(f"{index}:{line}")
            if len(details) >= limit:
                break
    return details


def count_pattern_dir(directory: Path, pattern: str, repo_root: Path | None = None) -> int:
    if repo_root is not None and not path_stays_in_trust_boundary(directory, repo_root):
        return 0
    if not directory.is_dir():
        return 0
    return count_pattern([path for path in directory.rglob("*") if path.is_file()], pattern, repo_root)


def count_tasks(path: Path, repo_root: Path | None = None) -> int:
    return sum(1 for line in trusted_lines(path, repo_root) if re.match(r"^\s*-\s+\[[ xX]\]\s+T[0-9]", line))


def count_unchecked_tasks(path: Path, repo_root: Path | None = None) -> int:
    return sum(1 for line in trusted_lines(path, repo_root) if re.match(r"^\s*-\s+\[ \]\s+T[0-9]", line))


def count_done_tasks(path: Path, repo_root: Path | None = None) -> int:
    return sum(1 for line in trusted_lines(path, repo_root) if re.match(r"^\s*-\s+\[[xX]\]\s+T[0-9]", line))


def last_number(text: str, pattern: str) -> int:
    matches = re.findall(pattern, text, flags=re.I)
    return int(matches[-1]) if matches else 0


def declared_file_entries(text: str) -> list[tuple[str, str]]:
    in_section = False
    entries = []
    for line in text.splitlines():
        if re.match(r"^##\s+Declared File Operations\s*$", line):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            match = re.match(r"^\s*[-*]\s+(NEW|MODIFIED)\s+([^\s]+)\s*$", line)
            if match:
                entries.append((match.group(1), match.group(2)))
    return entries


def is_excluded_generated(path: str) -> bool:
    return (
        path.endswith(("pnpm-lock.yaml", "package-lock.json", "yarn.lock", "Cargo.lock"))
        or ".process/" in path
        or path.startswith(("vendor/", "vendors/", "third_party/", "generated/", "dist/", "build/"))
        or "/generated/" in path
    )


def is_production_file(path: str) -> bool:
    return path.startswith(("src/", "app/", "lib/", "scripts/")) or path.endswith((".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".sql"))


def valid_child_spec_path(path: str) -> bool:
    parts = PurePosixPath(normalize_path_input(path)).parts
    return len(parts) == 2 and parts[0] == "specs" and parts[1] not in {"", ".", ".."}


def repo_root_for_specs_path(path: Path, fallback: Path) -> Path:
    resolved = path.resolve(strict=False)
    parts = resolved.parts
    for idx in range(len(parts) - 1, -1, -1):
        if parts[idx] == "specs" and idx + 1 < len(parts):
            return Path(*parts[:idx])
    return fallback


def child_status(root: Path, child_path: str) -> tuple[str, str]:
    child_dir = root / child_path
    if not trusted_dir_exists(child_dir, root):
        return "missing", "missing child directory"
    gate = child_dir / ".process" / "final-reviewability" / "gate-state.json"
    gate_text = trusted_text(gate, root)
    if gate_text is not None:
        try:
            if json.loads(gate_text).get("status") == "block":
                return "blocked", "final reviewability gate"
        except json.JSONDecodeError:
            # Malformed gate state falls through to the lower-confidence MOC status fallback.
            pass
    moc = child_dir / "SPEC-MOC.md"
    moc_text = trusted_text(moc, root)
    if moc_text is None:
        return "missing-state", "missing SPEC-MOC status"
    for line in moc_text.splitlines():
        if line.startswith("status:"):
            return normalize_status(line.split(":", 1)[1]), "SPEC-MOC status"
    return "missing-state", "SPEC-MOC status"


def normalize_status(raw: str) -> str:
    value = raw.split("#", 1)[0].strip().strip("\"'").lower().replace("-", "_")
    return {
        "blocked": "blocked",
        "failed": "failed",
        "fail": "failed",
        "in_progress": "in_progress",
        "progress": "in_progress",
        "active": "in_progress",
        "pending": "pending",
        "": "pending",
        "complete": "complete",
        "completed": "complete",
        "done": "complete",
        "archived": "archived",
        "archive": "archived",
    }.get(value, "missing-state")


def rollup_status(statuses: list[str]) -> str:
    if "blocked" in statuses:
        return "blocked"
    if "failed" in statuses:
        return "failed"
    if "in_progress" in statuses:
        return "in_progress"
    if "pending" in statuses or "missing-state" in statuses:
        return "pending"
    return "complete"


PY_HELPERS: dict[str, Callable[[dict[str, Any], Path], dict[str, Any]]] = {
    "check-prerequisites": check_prerequisites,
    "detect-commands": detect_commands,
    "detect-presets": detect_presets,
    "count-markers": count_markers,
    "validate-gate": validate_gate,
    "reviewability-gate": reviewability_gate,
    "estimate-reviewable-loc": estimate_reviewable_loc,
    "resolve-confidence-mode": resolve_confidence_mode,
    "confidence-gate": confidence_gate,
    "generate-spec-index-check": generate_spec_index_check,
    "o5-topology": o5_topology,
    "atomicity-route": atomicity_route,
    "plan-layers-feature-dir": plan_layers_feature_dir,
    "validate-pr-workflow-contract": validate_pr_workflow_contract,
    "validate-pr-packet-read-only": validate_pr_packet_read_only,
}
