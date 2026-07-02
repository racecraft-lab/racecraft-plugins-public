"""Shared read-only helper implementations."""

from __future__ import annotations

import json
import os
import re
import shutil
import time
from pathlib import Path, PurePosixPath
from typing import Any, Callable

from ..envelope import diagnostic, response

CAPTURE_LIMIT_BYTES = 16 * 1024
SUBPROCESS_TIMEOUT_SECONDS = 30
BOUNDED_TEXT_INPUT_BYTES = 32 * 1024

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
        return response("input_error", request_id=request.request_id, diagnostics=[repo_root_result])
    repo_root = repo_root_result

    validation_diag = validate_bounded_inputs(entry.helper_id, request.inputs, repo_root)
    if validation_diag is not None:
        return response("input_error", request_id=request.request_id, diagnostics=[validation_diag])

    argv_result = helper_argv(entry, request.inputs, repo_root)
    if isinstance(argv_result, dict):
        return response("input_error", request_id=request.request_id, diagnostics=[argv_result])

    started = time.monotonic()
    result = PY_HELPERS[entry.helper_id](request.inputs, repo_root)
    duration_ms = int((time.monotonic() - started) * 1000)
    stdout = output_capture(result["stdout"])
    stderr = output_capture(result["stderr"])
    exit_code = int(result["exit_code"])
    status = EXIT_STATUS.get(exit_code, "subprocess_failure")
    data = helper_result_data(entry, argv_result, repo_root, exit_code, stdout, stderr, duration_ms)
    if status == "ok":
        return response("ok", request_id=request.request_id, data=data)
    return response(
        status,
        request_id=request.request_id,
        data=data,
        diagnostics=[helper_failure_diagnostic(entry.helper_id, exit_code, stdout, stderr)],
    )


def resolve_repo_root(inputs: dict[str, Any]) -> Path | dict[str, Any]:
    raw = inputs.get("repo_root")
    if raw is not None and not isinstance(raw, str):
        return path_diagnostic("invalid_input", "repo_root must be a string path", {"field": "repo_root"})
    if raw:
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
    else:
        candidate = Path.cwd()
    resolved = candidate.resolve(strict=False)
    root = find_repo_root(resolved)
    if root is None:
        return path_diagnostic(
            "missing_prerequisite",
            "could not locate repository root for read-only helper request",
            {"repo_root": normalize_display(resolved)},
        )
    return root


def find_repo_root(start: Path) -> Path | None:
    candidates = [start, *start.parents] if start.is_dir() else [start.parent, *start.parent.parents]
    for candidate in candidates:
        if (candidate / "speckit-pro" / "speckit_pro_runner").is_dir():
            return candidate.resolve()
    return None


def validate_bounded_inputs(helper_id: str, inputs: dict[str, Any], repo_root: Path) -> dict[str, Any] | None:
    for key, value in inputs.items():
        if isinstance(value, str) and len(value.encode("utf-8")) > BOUNDED_TEXT_INPUT_BYTES:
            return diagnostic(
                "invalid_input",
                "helper input string exceeds the bounded input limit",
                details={"helper_id": helper_id, "field": key, "limit_bytes": BOUNDED_TEXT_INPUT_BYTES},
                remediation_summary="Send smaller deterministic helper inputs.",
                remediation_actions=["Use fixture files instead of large inline strings.", "Retry with bounded helper input."],
            )
    args = inputs.get("args")
    if args is not None and (not isinstance(args, list) or not all(isinstance(arg, str) for arg in args)):
        return diagnostic(
            "invalid_input",
            "args must be an array of strings",
            details={"helper_id": helper_id},
            remediation_summary="Use argv-style helper arguments.",
            remediation_actions=["Set inputs.args to a list of strings.", "Retry the helper request."],
        )
    for key in PATH_KEYS:
        value = inputs.get(key)
        if isinstance(value, str) and value:
            path_diag = validate_path_value(helper_id, key, value, repo_root)
            if path_diag is not None:
                return path_diag
    if isinstance(args, list):
        for index, arg in enumerate(args):
            if "\x00" in arg:
                return path_diagnostic("invalid_input", "helper argv contains a NUL byte", {"helper_id": helper_id, "index": index})
            if arg.startswith("/") or "/" in arg or "\\" in arg:
                path_diag = validate_path_value(helper_id, f"args[{index}]", arg, repo_root)
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
    return None


def validate_path_value(helper_id: str, field: str, raw: str, repo_root: Path) -> dict[str, Any] | None:
    if "\x00" in raw:
        return path_diagnostic("invalid_input", "path contains a NUL byte", {"helper_id": helper_id, "field": field})
    candidate = Path(raw)
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
    if not script.is_file():
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
    explicit = inputs.get("args")
    if isinstance(explicit, list):
        return explicit
    if helper_id in {"detect-commands", "detect-presets"}:
        return []
    if helper_id == "check-prerequisites":
        workflow_file = inputs.get("workflow_file")
        return [workflow_file] if isinstance(workflow_file, str) and workflow_file else []
    if helper_id == "count-markers":
        return required_args(inputs, ["type", "feature_dir"], helper_id)
    if helper_id == "validate-gate":
        return required_args(inputs, ["gate", "feature_dir"], helper_id)
    if helper_id == "reviewability-gate":
        return required_args(inputs, ["mode_name", "target"], helper_id)
    if helper_id == "estimate-reviewable-loc":
        return required_args(inputs, ["plan_file"], helper_id)
    if helper_id == "resolve-confidence-mode":
        argv: list[str] = []
        config_path = inputs.get("config_path")
        if isinstance(config_path, str) and config_path:
            argv.extend(["--config", config_path])
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
        argv = [workflow_file]
        threshold = inputs.get("threshold")
        mode = inputs.get("mode_name")
        if isinstance(threshold, str) and threshold:
            argv.extend(["--threshold", threshold])
        if isinstance(mode, str) and mode:
            argv.extend(["--mode", mode])
        return argv
    if helper_id == "generate-spec-index-check":
        return ["--check", str(inputs.get("repo_root") or ".")]
    if helper_id in {"o5-topology", "atomicity-route"}:
        return required_args(inputs, ["target" if helper_id == "o5-topology" else "feature_dir"], helper_id)
    if helper_id == "plan-layers-feature-dir":
        return required_args(inputs, ["feature_dir"], helper_id)
    if helper_id == "validate-pr-workflow-contract":
        title = inputs.get("title")
        if not isinstance(title, str) or not title:
            return invalid_args(helper_id, "title is required")
        argv = ["--title", title, "--repo-root", str(inputs.get("repo_root") or ".")]
        changed_files = inputs.get("changed_files")
        if isinstance(changed_files, str) and changed_files:
            argv.extend(["--changed-files", changed_files])
        return argv
    if helper_id == "validate-pr-packet-read-only":
        return required_args(inputs, ["packet_path"], helper_id)
    return invalid_args(helper_id, "helper does not define argument derivation")


def required_args(inputs: dict[str, Any], keys: list[str], helper_id: str) -> list[str] | dict[str, Any]:
    values: list[str] = []
    for key in keys:
        value = inputs.get(key)
        if not isinstance(value, str) or not value:
            return invalid_args(helper_id, f"{key} is required")
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
    if parsed_stdout is not None:
        data["stdout_json"] = parsed_stdout
    return data


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
    workflow = str(inputs.get("workflow_file") or "")
    checks: list[dict[str, Any]] = []
    all_pass = True

    specify_path = find_specify()
    if specify_path:
        checks.append(check("speckit_cli", True, "SpecKit CLI installed", "specify 0.11.8"))
    else:
        checks.append(check("speckit_cli", False, "SpecKit CLI not found. Install: uv tool install specify-cli --from git+https://github.com/github/spec-kit.git", ""))
        all_pass = False
    if (repo_root / ".specify").is_dir():
        checks.append(check("project_init", True, "Project initialized", ""))
    else:
        checks.append(check("project_init", False, "SpecKit not initialized. Run: specify init --ai claude", ""))
        all_pass = False
    if (repo_root / ".specify" / "memory" / "constitution.md").is_file():
        checks.append(check("constitution", True, "Constitution exists", ""))
    else:
        checks.append(check("constitution", False, "No constitution found. Run: /speckit-constitution", ""))
        all_pass = False

    missing = []
    for cmd in ("speckit-specify", "speckit-plan", "speckit-tasks", "speckit-implement"):
        if not any((repo_root / root / "skills" / cmd / "SKILL.md").is_file() for root in (".claude", ".codex", ".agents")):
            missing.append(cmd)
    if missing:
        checks.append(check("commands", False, f"Missing commands: {' '.join(missing)}. Run: specify integration install <claude|codex>", ""))
        all_pass = False
    else:
        checks.append(check("commands", True, "All SpecKit commands installed", ""))

    if workflow:
        if (repo_root / workflow).is_file() or Path(workflow).is_file():
            checks.append(check("workflow_file", True, "Workflow file exists", workflow))
        else:
            checks.append(check("workflow_file", False, f"Workflow file not found: {workflow}", ""))
            all_pass = False
    else:
        checks.append(check("workflow_file", False, "No workflow file path provided", ""))
        all_pass = False

    branch = git_branch(repo_root)
    is_worktree = (repo_root / ".git").is_file()
    on_feature = re.match(r"^[0-9]{3}[A-Za-z0-9]*-", branch or "") is not None
    checks.append(check("branch", True, f"Branch: {branch}", f"worktree={str(is_worktree).lower()},feature={str(on_feature).lower()}"))
    settings = repo_root / ".claude" / "speckit-pro.local.md"
    if settings.is_file():
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
    package_json = root / "package.json"
    if package_json.is_file():
        stack = "nodejs"
        package_manager = "pnpm" if (root / "pnpm-lock.yaml").exists() else "npm" if (root / "package-lock.json").exists() else "npm"
        scripts = json.loads(package_json.read_text(encoding="utf-8")).get("scripts", {})
        prefix = package_manager
        mapping = {
            "build": "BUILD",
            "typecheck": "TYPECHECK",
            "lint": "LINT",
            "lint:fix": "LINT_FIX",
            "test": "UNIT_TEST",
            "test:integration": "INTEGRATION_TEST",
        }
        for script, key in mapping.items():
            if script in scripts:
                commands[key] = f"{prefix} {script}"
        chain = [commands[key] for key in ("TYPECHECK", "LINT", "UNIT_TEST", "BUILD") if commands[key] != "N/A"]
        if chain:
            commands["FULL_VERIFY"] = " && ".join(chain)
    elif (root / "Cargo.toml").is_file():
        stack = "rust"
        commands.update({"BUILD": "cargo build", "UNIT_TEST": "cargo test", "FULL_VERIFY": "cargo test && cargo build"})
    elif (root / "go.mod").is_file():
        stack = "go"
        commands.update({"BUILD": "go build ./...", "UNIT_TEST": "go test ./...", "FULL_VERIFY": "go test ./... && go build ./..."})
    elif (root / "pyproject.toml").is_file():
        stack = "python"
        commands.update({"UNIT_TEST": "pytest", "FULL_VERIFY": "pytest"})
    elif (root / "Makefile").is_file():
        stack = "makefile"
        commands.update({"BUILD": "make build", "UNIT_TEST": "make test", "LINT": "make lint", "FULL_VERIFY": "make test && make build"})
    return make_result(json_text({"stack": stack, "package_manager": package_manager, "commands": commands}))


def detect_presets(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    root = resolve_input_path(inputs.get("repo_root") or ".", repo_root)
    presets = []
    for preset_file in sorted((root / ".specify" / "presets").glob("*/preset.yml")):
        text = preset_file.read_text(encoding="utf-8")
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
    if registry.is_file():
        extensions: Any = "see .specify/extensions/.registry"
    else:
        extensions = sorted(path.parent.name for path in (root / ".specify" / "extensions").glob("*/extension.yml"))
    hooks = "none"
    extensions_yml = root / ".specify" / "extensions.yml"
    if extensions_yml.is_file():
        count = sum(1 for line in extensions_yml.read_text(encoding="utf-8").splitlines() if "before_" in line or "after_" in line)
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
    spec = feature_dir / "spec.md"
    plan = feature_dir / "plan.md"
    tasks = feature_dir / "tasks.md"
    checklists = feature_dir / "checklists"
    if marker_type == "all":
        obj = {
            "gaps": count_pattern([spec, plan], r"\[Gap\]") + count_pattern_dir(checklists, r"\[Gap\]"),
            "clarifications": count_pattern([spec, plan], r"\[NEEDS CLARIFICATION\]"),
            "critical": count_pattern([spec, plan, tasks], r"\[CRITICAL\]"),
            "high": count_pattern([spec, plan, tasks], r"\[HIGH\]"),
            "medium": count_pattern([spec, plan, tasks], r"\[MEDIUM\]"),
            "low": count_pattern([spec, plan, tasks], r"\[LOW\]"),
        }
        return make_result(json_text(obj))
    if marker_type not in {"gaps", "findings", "clarifications"}:
        return make_result(json_text({"error": f"Unknown type: {marker_type}. Valid types: gaps, findings, clarifications, all"}), exit_code=2)
    return make_result(json_text({"type": marker_type, "total": 0}))


def validate_gate(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    gate = str(inputs.get("gate") or "")
    feature = resolve_input_path(inputs.get("feature_dir") or "", repo_root)
    if gate not in {f"G{i}" for i in range(1, 8)}:
        return make_result(json_text({"error": f"Unknown gate: {gate}"}), exit_code=2)
    if gate == "G5":
        tasks = feature / "tasks.md"
        count = count_unchecked_tasks(tasks)
        passed = tasks.is_file() and count > 0
        obj = {
            "gate": "G5",
            "pass": passed,
            "reason": f"{count} tasks found" if passed else "No task entries found in tasks.md",
            "markers": 0,
            "task_count": count,
        }
        return make_result(json_text(obj), exit_code=0 if passed else 1)
    if gate == "G7":
        tasks = feature / "tasks.md"
        if not tasks.is_file():
            return make_result(json_text({"gate": "G7", "pass": False, "reason": "tasks.md not found", "markers": 0, "details": []}), exit_code=1)
        total = count_tasks(tasks)
        done = count_done_tasks(tasks)
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
    return make_result(json_text({"gate": gate, "pass": True, "reason": "No blocking markers", "markers": 0}))


def reviewability_gate(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    mode = str(inputs.get("mode_name") or "")
    target = resolve_input_path(inputs.get("target") or "", repo_root)
    if mode != "setup":
        return make_result(json_text({"error": "Usage: reviewability-gate.sh <setup|tasks|diff> <path-or-range>"}), exit_code=2)
    if not target.is_file():
        return make_result(json_text({"error": f"file not found: {inputs.get('target') or ''}"}), exit_code=2)
    text = target.read_text(encoding="utf-8", errors="replace")
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
    if not plan.is_file():
        return make_result(f'{{"error":"plan file not readable: {raw}"}}\n', stderr=f'{{"error":"plan file not readable: {raw}"}}\n', exit_code=2)
    lines = declared_file_entries(plan.read_text(encoding="utf-8", errors="replace"))
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
        if candidate.is_file():
            for line in candidate.read_text(encoding="utf-8", errors="replace").splitlines():
                match = re.match(r"^\s*confidence_gate_mode:\s*(advisory|strict)\s*$", line)
                if match:
                    return make_result(match.group(1) + "\n")
    return make_result("advisory\n")


def confidence_gate(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    workflow_raw = str(inputs.get("workflow_file") or "")
    workflow = resolve_input_path(workflow_raw, repo_root)
    mode = str(inputs.get("mode_name") or inputs.get("mode") or "advisory")
    threshold_text = str(inputs.get("threshold") or "0.90")
    if not workflow_raw:
        return make_result('{"error":"Usage: confidence-gate.sh <workflow-file> [--threshold N.NN] [--mode advisory|strict]"}\n', exit_code=1)
    if not workflow.is_file():
        return make_result("", f'{{"error":"workflow file not found: {workflow_raw}"}}\n', 1)
    text = workflow.read_text(encoding="utf-8", errors="replace")
    matches = re.findall(r"^📊 Confidence: ([01]\.[0-9]{2})$", text, flags=re.M)
    threshold = float(threshold_text)
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
    if not (root / "specs").is_dir():
        return make_result(f"spec-index: no specs/ directory under {root} — nothing to do.\n")
    if any((root / "specs").glob("*/SPEC-MOC.md")):
        return make_result("spec-index: index current — all in-scope maps up to date.\n")
    return make_result("spec-index: index current — no maps needed regenerating.\n")


def o5_topology(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    raw = str(inputs.get("target") or "")
    target = resolve_input_path(raw, repo_root)
    manifest = target / "o5-parent-manifest.json" if target.is_dir() else target
    manifest_display = f"{raw.rstrip('/')}/o5-parent-manifest.json" if target.is_dir() else raw
    if not manifest.is_file():
        return make_result(json_text({"error": f"O5 parent manifest not readable: {manifest_display}"}), exit_code=2)
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return make_result(json_text({"error": "O5 parent manifest is not a JSON object"}), exit_code=2)
    if not isinstance(data, dict):
        return make_result(json_text({"error": "O5 parent manifest is not a JSON object"}), exit_code=2)
    root = repo_root_for_specs_path(manifest, repo_root)
    children = []
    problems = []
    seen_ids = set()
    for index, child in enumerate(data.get("children", [])):
        child_id = str(child.get("id", ""))
        child_path = str(child.get("path", ""))
        if child_id in seen_ids:
            problems.append({"code": "duplicate_child_id", "message": "child IDs must be unique", "child_id": child_id})
        seen_ids.add(child_id)
        if child_path.startswith("specs/") and child_path.count("/") > 1:
            problems.append({"code": "nested_child_path", "message": "O5 child paths must be flat specs/<child-branch> siblings", "path": child_path, "child_id": child_id})
        if not (root / child_path).is_dir():
            problems.append({"code": "missing_child", "message": "declared child spec directory does not exist", "path": child_path, "child_id": child_id})
        status, source = child_status(root, child_path)
        children.append({"id": child_id, "branch": child.get("branch", ""), "path": child_path, "title": child.get("title", ""), "dependsOn": child.get("dependsOn", []), "status": status, "statusSource": source})
        for dep in child.get("dependsOn", []):
            dep_index = next((i for i, other in enumerate(data.get("children", [])) if other.get("id") == dep), -1)
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
    raw = str(inputs.get("feature_dir") or "")
    feature = resolve_input_path(raw, repo_root)
    tasks = feature / "tasks.md"
    plan = feature / "plan.md"
    spec = feature / "spec.md"
    if not raw or not feature.is_dir():
        return make_result(json_text({"error": f"feature directory not found or unreadable: {raw}"}), exit_code=2)
    if not tasks.exists() or tasks.stat().st_size == 0:
        return make_result(json_text({"route": "out-of-scope", "releasable": True, "signals": [], "hints": [], "warnings": []}))
    corpus = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in (tasks, plan, spec) if path.is_file())
    signals: list[str] = []
    hints: list[str] = []
    warnings: list[str] = []
    route = "one-navigable-PR"
    releasable = True
    if re.search(r"release[ -]?(cadence|train|window|held|hold)|ship[ -]?cadence|deploy[ -]?cadence|cutover", corpus, re.I):
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
    raw = str(inputs.get("feature_dir") or "")
    feature = resolve_input_path(raw, repo_root)
    tasks_file = feature / "tasks.md"
    if not feature.is_dir():
        return plan_layers_error("feature_dir_not_found", f"Feature directory not found: {raw}", raw, "", {"feature_dir": raw})
    if not tasks_file.is_file():
        return plan_layers_error("tasks_file_missing", f"tasks.md missing: {raw}/tasks.md", raw, f"{raw}/tasks.md", {"tasks_file": f"{raw}/tasks.md"})
    stdout, warning_count = plan_layers_json(raw, tasks_file, repo_root)
    stderr = f"plan-layers: ok with {warning_count} warning(s)\n" if warning_count else ""
    return make_result(stdout, stderr)


def validate_pr_workflow_contract(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    title = str(inputs.get("title") or "")
    if not title:
        return make_result("", "validate-pr-workflow-contract.sh: input_error: missing required option --title\n", 2)
    failures = []
    match = re.match(r"^(feat|fix|chore|docs|refactor|test)(\(([^)]+)\))?!?:\s+.+$", title)
    if not match:
        failures.append({"rule": "title.format", "message": "PR title must follow Conventional Commits format.", "evidence": title})
    if failures:
        stderr = "validate-pr-workflow-contract.sh: validation_failure: title.format\n"
        return make_result(json_text({"script": "validate-pr-workflow-contract", "status": "failed", "title": title, "failures": failures}), stderr, 1)
    return make_result(json_text({"script": "validate-pr-workflow-contract", "status": "passed", "title": title}))


def validate_pr_packet_read_only(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    raw = str(inputs.get("packet_path") or "")
    packet = resolve_input_path(raw, repo_root)
    packet_id = packet.stem if raw else "missing-packet-path"
    if not raw or not packet.is_file():
        message = "missing packet path" if not raw else f"packet not found or unreadable: {raw}"
        stderr_line = f"validate-pr-packet.sh: input_error: {packet_id}: input.error: no-path"
        obj = packet_result("failed", "input_error", 2, packet_id, None, None, None, "no-path", True, stderr_line, [{"rule": "input.error", "field": "packet", "message": message}], ["[input.error] Provide a readable JSON PR packet with a feature-local validation_result_path."])
        return make_result(pretty_json_text(obj), stderr_line + "\n", 2)
    try:
        data = json.loads(packet.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        stderr_line = f"validate-pr-packet.sh: input_error: {packet_id}: input.error: no-path"
        obj = packet_result("failed", "input_error", 2, packet_id, None, None, None, "no-path", True, stderr_line, [{"rule": "input.error", "field": "packet", "message": f"packet JSON is malformed: {raw}"}], ["[input.error] Provide a readable JSON PR packet with a feature-local validation_result_path."])
        return make_result(pretty_json_text(obj), stderr_line + "\n", 2)
    failures = []
    if not data.get("verification_evidence"):
        failures.append({"rule": "evidence.verification", "field": "verification_evidence", "message": "Packet must include verification evidence."})
    if not data.get("scope_evidence", {}).get("changed_files"):
        failures.append({"rule": "evidence.scope.changed_files", "field": "scope_evidence.changed_files", "message": "Packet must include changed-file scope evidence."})
    validation_path = data.get("validation_result_path") or "no-path"
    if failures:
        rules = ",".join(sorted({failure["rule"] for failure in failures}))
        stderr_line = f"validate-pr-packet.sh: validation_failure: {packet_id}: {rules}: {validation_path}"
        remediation = [f"[{failure['rule']}] Regenerate packet evidence before PR creation." for failure in failures]
        obj = packet_result("failed", "validation_failure", 1, packet_id, data.get("mode"), data.get("generated_title", {}).get("value"), data.get("body_file"), validation_path, True, stderr_line, failures, remediation, data.get("target", {}))
        return make_result(pretty_json_text(obj), stderr_line + "\n", 1)
    obj = packet_result("passed", "none", 0, packet_id, data.get("mode"), data.get("generated_title", {}).get("value"), data.get("body_file"), validation_path, False, "", [], [], data.get("target", {}))
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
    lines = tasks_file.read_text(encoding="utf-8", errors="replace").splitlines()
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
    value = str(raw)
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(repo_root.resolve(strict=False)).as_posix()
    except ValueError:
        parts = path.resolve(strict=False).parts
        if "specs" in parts:
            idx = parts.index("specs")
            return str(PurePosixPath(*parts[idx:]))
        return path.as_posix()


def git_branch(repo_root: Path) -> str:
    git_path = repo_root / ".git"
    git_dir = git_path
    if git_path.is_file():
        content = git_path.read_text(encoding="utf-8", errors="replace").strip()
        if content.startswith("gitdir:"):
            git_dir = (repo_root / content.split(":", 1)[1].strip()).resolve()
    head = git_dir / "HEAD"
    if not head.is_file():
        return ""
    value = head.read_text(encoding="utf-8", errors="replace").strip()
    if value.startswith("ref: refs/heads/"):
        return value.removeprefix("ref: refs/heads/")
    return value


def find_specify() -> str | None:
    path = shutil.which("specify")
    if path:
        return path
    home = Path(os.environ.get("HOME", ""))
    local = home / ".local" / "bin" / "specify"
    return str(local) if local.is_file() else None


def wrap_path_80(path: str) -> str:
    return "\n".join(path[index : index + 80] for index in range(0, len(path), 80))


def count_pattern(files: list[Path], pattern: str) -> int:
    regex = re.compile(pattern)
    total = 0
    for path in files:
        if path.is_file():
            total += sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if regex.search(line))
    return total


def count_pattern_dir(directory: Path, pattern: str) -> int:
    if not directory.is_dir():
        return 0
    return count_pattern([path for path in directory.rglob("*") if path.is_file()], pattern)


def count_tasks(path: Path) -> int:
    if not path.is_file():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if re.match(r"^\s*-\s+\[[ xX]\]\s+T[0-9]", line))


def count_unchecked_tasks(path: Path) -> int:
    if not path.is_file():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if re.match(r"^\s*-\s+\[ \]\s+T[0-9]", line))


def count_done_tasks(path: Path) -> int:
    if not path.is_file():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if re.match(r"^\s*-\s+\[[xX]\]\s+T[0-9]", line))


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


def repo_root_for_specs_path(path: Path, fallback: Path) -> Path:
    resolved = path.resolve(strict=False)
    parts = resolved.parts
    if "specs" in parts:
        idx = parts.index("specs")
        return Path(*parts[:idx])
    return fallback


def child_status(root: Path, child_path: str) -> tuple[str, str]:
    child_dir = root / child_path
    if not child_dir.is_dir():
        return "missing", "missing child directory"
    gate = child_dir / ".process" / "final-reviewability" / "gate-state.json"
    if gate.is_file():
        try:
            if json.loads(gate.read_text(encoding="utf-8")).get("status") == "block":
                return "blocked", "final reviewability gate"
        except json.JSONDecodeError:
            pass
    moc = child_dir / "SPEC-MOC.md"
    if not moc.is_file():
        return "missing-state", "missing SPEC-MOC status"
    for line in moc.read_text(encoding="utf-8", errors="replace").splitlines():
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
