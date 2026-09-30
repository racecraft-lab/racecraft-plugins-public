"""Claude Code host adapter: trial staging, retained-workspace capture and receipts.

Prepares a sealed Claude plugin-mode trial.  After execution it reads the
Claude result and trace, captures declared artifacts from the retained
workspace, and verifies the Claude fixture receipt and reference access.
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import stat
import sys
import tempfile
from typing import Any, Mapping
import uuid

import native_eval_adapter_common as adapter_common
import native_eval_fixture_setup as fixture_setup
import native_eval_git_observation
import native_eval_git_scaffold
import native_eval_strict_json as strict_json
import native_eval_toolchain
import native_eval_upstream
import native_eval_upstream_scaffold
import native_eval_verification


_CLAUDE_SKILL_NAME = re.compile(
    r"[a-z0-9][a-z0-9._-]*:[a-z0-9][a-z0-9._-]*"
)
_GATED_CLAUDE_TOOLS = frozenset({"Bash", "Write", "Edit", "WebFetch", "WebSearch"})
_CLAUDE_MAX_TURNS = {"ordinary": 50, "nested": 100}
_ARTIFACT_FILE_LIMIT = 1024 * 1024
_ARTIFACT_TOTAL_LIMIT = 8 * 1024 * 1024
_FIXTURE_RECEIPT_LIMIT = 64 * 1024
_CLAUDE_DOCKER_CONFIG_SCHEMA_VERSION = "native-eval-claude-docker-config/v1"
_CLAUDE_DOCKER_CONFIG_DIRECTORY = "docker-config"
_CLAUDE_CONTROLLER_HOME_SCHEMA_VERSION = "native-eval-claude-controller-home/v1"
_CLAUDE_CONTROLLER_HOME_DIRECTORY = "controller-home"
_CLAUDE_CONFIG_ROOT_SCHEMA_VERSION = "native-eval-claude-config-root/v1"
_CLAUDE_REFERENCE_ACCESS_INSTRUCTION = (
    "The selected skill's references directory is mirrored for this evaluation at the exact "
    "absolute directory `{read_root}`. Whenever the skill directs you to read "
    "`references/<path>`, read `{read_root}/<path>` instead. The mirror is byte-identical "
    "installed reference content; do not read the plugin installation path."
)


def _copy_tree(source: Path, destination: Path) -> None:
    adapter_common._require(source.is_dir(), f"native source directory is unavailable: {source}")
    adapter_common._require(not source.is_symlink(), f"native source directory must not be a symlink: {source}")
    for path in source.rglob("*"):
        adapter_common._require(not path.is_symlink(), f"native source tree contains a symlink: {path.relative_to(source)}")
    shutil.copytree(
        source, destination,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
    )
    adapter_common._tree_digest(destination)


def _stage_module(case_dir: Path, module: Any) -> None:
    """Copy one lib module beside the case inputs, read-only, for standalone scaffold runs."""
    source = Path(module.__file__).resolve()
    staged = case_dir / source.name
    shutil.copyfile(source, staged)
    staged.chmod(0o500)


def _offline_git_fixture_result(
    plan_path: Path, attempt: Path, *, host: str = "claude", include_upstream: bool = False,
) -> tuple[dict[str, object], dict[str, object]]:
    with tempfile.TemporaryDirectory(prefix="native-eval-git-preview-", dir=attempt) as temporary:
        workspace = Path(temporary) / "workspace"
        workspace.mkdir(mode=0o700)
        result = fixture_setup.materialize_workspace(fixture_setup.load_plan(plan_path), workspace)
        adapter_common._write_git_controller_exclude(
            workspace,
            adapter_common._git_controller_exclude(result, host=host, include_upstream=include_upstream),
        )
        controls = fixture_setup.snapshot_git_repository_controls(workspace)
        if "worktrees" in result:
            observed = native_eval_git_observation.observe_registered_worktrees(
                workspace, controls, result["git_repository"], result["worktrees"],
            )
            adapter_common._require(adapter_common._worktrees_match_initial(observed),
                     "git fixture worktrees changed during offline materialization")
    adapter_common._require(isinstance(result, dict) and set(result) in (
        {"copied", "git_repository"}, {"copied", "git_repository", "worktrees"},
    )
             and isinstance(result["copied"], list) and isinstance(result["git_repository"], dict),
             "git fixture returned a malformed result")
    return {"schema_version": fixture_setup.GIT_SCHEMA_VERSION, **result}, controls


def _claude_controller_directory_identity(
    attempt: Path, *, kind: str, create: bool,
) -> tuple[Path, dict[str, object]]:
    adapter_common._require(kind in {"home", "docker"}, "Claude controller directory kind is unsupported")
    directory, schema_version, label = {
        "home": (
            _CLAUDE_CONTROLLER_HOME_DIRECTORY,
            _CLAUDE_CONTROLLER_HOME_SCHEMA_VERSION,
            "Claude controller home",
        ),
        "docker": (
            _CLAUDE_DOCKER_CONFIG_DIRECTORY,
            _CLAUDE_DOCKER_CONFIG_SCHEMA_VERSION,
            "Claude Docker config directory",
        ),
    }[kind]
    path = attempt / directory
    if create:
        try:
            path.mkdir(mode=0o700)
        except OSError as exc:
            raise adapter_common.NativeAdapterError(f"{label} could not be created") from exc
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise adapter_common.NativeAdapterError(f"{label} is unavailable") from exc
    adapter_common._require(stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode),
             f"{label} must be a real directory")
    adapter_common._require(stat.S_IMODE(metadata.st_mode) == 0o700,
             f"{label} must have mode 0700")
    try:
        entries = list(path.iterdir())
    except OSError as exc:
        raise adapter_common.NativeAdapterError(f"{label} is unavailable") from exc
    adapter_common._require(not entries, f"{label} must remain empty")
    return path, {
        "schema_version": schema_version,
        "path": directory,
        "kind": "controller-owned-empty-directory",
        "mode": 0o700,
    }


def _claude_config_root_identity(
    attempt: Path, configured_path: Path | None = None,
) -> tuple[Path, dict[str, object]]:
    if configured_path is None:
        explicit = os.environ.get("CLAUDE_CONFIG_DIR")
        if explicit is not None:
            candidate = Path(explicit)
        else:
            home = os.environ.get("HOME")
            adapter_common._require(isinstance(home, str) and bool(home),
                     "Claude controller HOME is unavailable")
            candidate = Path(home) / ".claude"
    else:
        candidate = configured_path
    adapter_common._require(candidate.is_absolute(), "Claude controller config root must be absolute")
    try:
        candidate_metadata = candidate.lstat()
        canonical = candidate.resolve(strict=True)
        metadata = canonical.lstat()
    except OSError as exc:
        raise adapter_common.NativeAdapterError("Claude controller config root is unavailable") from exc
    adapter_common._require(stat.S_ISDIR(candidate_metadata.st_mode)
             and not stat.S_ISLNK(candidate_metadata.st_mode)
             and stat.S_ISDIR(metadata.st_mode)
             and not stat.S_ISLNK(metadata.st_mode),
             "Claude controller config root must be a real directory")
    adapter_common._require(metadata.st_uid == os.getuid(),
             "Claude controller config root must be owned by the current user")
    mode = stat.S_IMODE(metadata.st_mode)
    adapter_common._require(mode & 0o022 == 0,
             "Claude controller config root must not be group/world writable")
    attempt_root = attempt.resolve(strict=True)
    adapter_common._require(not canonical.is_relative_to(attempt_root),
             "Claude controller config root must be outside attempt staging")
    return canonical, {
        "schema_version": _CLAUDE_CONFIG_ROOT_SCHEMA_VERSION,
        "path": str(canonical),
        "kind": "controller-config-directory",
        "mode": mode,
        "uid": metadata.st_uid,
        "device": metadata.st_dev,
        "inode": metadata.st_ino,
    }


def _merge_claude_toolchain_exclusions(
    exclusions: dict[str, object] | None,
) -> dict[str, object]:
    merged = {
        "root_directories": list(exclusions["root_directories"]) if exclusions else [],
        "files": list(exclusions["files"]) if exclusions else [],
    }
    merged["root_directories"].extend((".native-toolchain", "speckit_pro_runner"))
    merged["files"].extend(("bin/python3", "bin/.speckit-python3-runtime"))
    return merged


def _claude_explicit_activation_input(
    prompt: str, skill: object, plugin: Path,
) -> tuple[str, dict[str, object] | None]:
    """Render a functional staged skill as one explicit native user command."""
    if skill is None:
        return prompt, None
    adapter_common._require(isinstance(skill, str)
             and _CLAUDE_SKILL_NAME.fullmatch(skill) is not None,
             "Claude skill is not a canonical namespaced skill")
    leaf = skill.rsplit(":", 1)[1]
    relative = PurePosixPath("skills") / leaf / "SKILL.md"
    source = plugin / Path(relative)
    adapter_common._require(source.is_file() and not source.is_symlink(),
             "Claude staged skill is unavailable")
    payload = source.read_bytes()
    adapter_common._require(payload.startswith(b"---\n"), "Claude staged skill has no strict frontmatter")
    end = payload.find(b"\n---\n", 4)
    adapter_common._require(4 <= end <= 64 * 1024, "Claude staged skill frontmatter is malformed")
    try:
        header = payload[4:end].decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise adapter_common.NativeAdapterError("Claude staged skill frontmatter is not UTF-8") from exc
    fields: dict[str, str] = {}
    for line in header.splitlines():
        match = re.fullmatch(r"([A-Za-z][A-Za-z0-9-]*):[ \t]*(.*)", line)
        if match is None:
            continue
        key, value = match.groups()
        adapter_common._require(key not in fields, f"Claude staged skill has duplicate {key} frontmatter")
        fields[key] = value.strip()
    adapter_common._require(fields.get("name") == leaf,
             "Claude skill name does not match its command")
    adapter_common._require(fields.get("user-invocable") == "true",
             "Claude skill is not explicitly user-invocable")
    rendered = f"/{skill} {prompt}"
    return rendered, {
        "schema_version": "native-claude-explicit-activation-input/v1",
        "skill": skill,
        "canonical_activation": leaf,
        "prompt": rendered,
        "skill_source": {
            "path": relative.as_posix(),
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        },
    }


def _claude_reference_access(
    case_dir: Path, plugin: Path, skill: object,
) -> dict[str, object] | None:
    """Copy one selected skill's references inside the official runner's case boundary."""
    if skill is None:
        return None
    adapter_common._require(isinstance(skill, str)
             and _CLAUDE_SKILL_NAME.fullmatch(skill) is not None,
             "Claude skill is not a canonical namespaced skill")
    leaf = skill.rsplit(":", 1)[1]
    target_relative = PurePosixPath("skills") / leaf / "references"
    target = plugin / Path(target_relative)
    if not target.exists():
        return None
    adapter_common._require(target.is_dir() and not target.is_symlink(),
             "Claude staged skill references are not a plain directory")
    add_dir = ".native-eval-skill-references"
    granted = case_dir / add_dir
    _copy_tree(target, granted)
    tree_sha256 = adapter_common._tree_digest(target)
    adapter_common._require(adapter_common._tree_digest(granted) == tree_sha256,
             "Claude staged skill reference copy differs from its selected source")
    return {
        "schema_version": "native-claude-reference-access/v4",
        "skill": skill,
        "add_dir": add_dir,
        "target": target_relative.as_posix(),
        "tree_sha256": tree_sha256,
    }


def _prepare_claude(
    case: Mapping[str, object], prompt: str, host_settings: Mapping[str, object],
    repo: Path, attempt: Path, model: str, trial_identity: str,
) -> adapter_common.PreparedTrial:
    executable = adapter_common._resolve_executable("claude")
    cli_version = adapter_common._probe_cli_version(executable)
    config_root, config_root_identity = _claude_config_root_identity(attempt)
    controller_home, controller_home_identity = _claude_controller_directory_identity(
        attempt, kind="home", create=True,
    )
    docker_config, docker_config_identity = _claude_controller_directory_identity(
        attempt, kind="docker", create=True,
    )
    plugin = attempt / "plugin"
    explicit_activation: dict[str, object] | None = None
    if case.get("layer") == "trigger":
        prompt, trigger_stage = adapter_common._stage_trigger(
            case, host_settings, repo, plugin, "claude", prompt, trial_identity,
        )
    else:
        _copy_tree(repo / "speckit-pro", plugin)
        trigger_stage = None
    case_dir = plugin / "evals" / str(case["id"])
    adapter_common._require(not case_dir.exists(), "staged plugin already contains the native case")
    case_dir.mkdir(parents=True)
    plan, plan_path = adapter_common._stage_fixture_plan(case, repo, case_dir)
    fixture_read_witnesses = adapter_common._fixture_read_witnesses(case, plan_path)
    required_tools = adapter_common._required_native_tools(case)
    adapter_common._require(not required_tools or case.get("layer") != "trigger",
             "trigger measurements cannot stage an upstream tool integration")
    git_settings: dict[str, object] | None = None
    staged_tree_exclusions: dict[str, object] | None = None
    if plan["schema_version"] == fixture_setup.GIT_SCHEMA_VERSION:
        receipt_relative_path = f"evals/{case['id']}/fixture-receipt.json"
        expected_result, git_controls = _offline_git_fixture_result(
            plan_path, attempt, host="claude", include_upstream=bool(required_tools),
        )
        git_settings = adapter_common._git_runtime_settings(
            expected_result=expected_result,
            git_controls=git_controls,
            host="claude",
            receipt_relative_path=receipt_relative_path,
            include_upstream=bool(required_tools),
        )
        staged_tree_exclusions = {
            "root_directories": [],
            "files": [receipt_relative_path],
        }
    prepared_toolchain: native_eval_toolchain.PreparedNativeToolchain | None = None
    prepared_upstream: native_eval_upstream.PreparedUpstreamIntegration | None = None
    if required_tools:
        prepared_toolchain = native_eval_toolchain.prepare_claude_plugin_toolchain(
            plugin, required_tools=required_tools,
        )
        launchers = prepared_toolchain.runtime_identity.get("launchers")
        python_launcher = launchers.get("python3") if isinstance(launchers, Mapping) else None
        adapter_common._require(
            isinstance(python_launcher, Mapping)
            and python_launcher.get("path") == "bin/python3"
            and (plugin / "bin" / "python3").is_file(),
            "Claude protected Python launcher is not bound to the staged plugin",
        )
        upstream_controller = case_dir / "upstream-controller"
        upstream_controller.mkdir(mode=0o700)
        prepared_upstream = native_eval_upstream.prepare_upstream_integration(
            upstream_controller, host="claude", toolchain=prepared_toolchain,
        )
        adapter_common._validate_upstream_fixture_destinations(
            plan["fixtures"], "claude", prepared_upstream.runtime_identity,
        )
        staged_tree_exclusions = _merge_claude_toolchain_exclusions(staged_tree_exclusions)
        source_prefix = prepared_upstream.project_root.relative_to(plugin).as_posix()
        staged_tree_exclusions = adapter_common._merge_staged_file_exclusions(
            staged_tree_exclusions,
            tuple(f"{source_prefix}/{path}" for path in
                  native_eval_upstream.volatile_manifest_paths(prepared_upstream.runtime_identity)),
        )
    prompt = adapter_common._render_resolved_python(prompt, "claude", plugin, required_tools)
    if trigger_stage is None:
        prompt, explicit_activation = _claude_explicit_activation_input(
            prompt, host_settings.get("skill"), plugin,
        )
    declared_tools = host_settings.get("allowed_tools")
    adapter_common._require(isinstance(declared_tools, list)
             and all(isinstance(tool, str) and tool for tool in declared_tools),
             "Claude allowed_tools are malformed")
    tools = list(declared_tools)
    toolchain_bash_grant = prepared_toolchain is not None and not any(
        tool.partition("(")[0] == "Bash" for tool in tools
    )
    if toolchain_bash_grant:
        tools.append("Bash")
    reference_access = _claude_reference_access(
        case_dir, plugin, host_settings.get("skill"),
    )
    adapter_common._write_text(case_dir / "prompt.md", f"{prompt.rstrip()}\n")
    adapter_common._write_text(
        case_dir / "graders" / "transport.md",
        "---\ntype: regex\ntarget: last_message\npattern: \"[\\\\s\\\\S]*\"\n---\n",
    )
    case_config = (
        f"schema_version: \"1.1\"\nname: {json.dumps(case['id'])}\n"
        "runs: 1\n"
        "execution:\n"
        f"  max_turns: {_CLAUDE_MAX_TURNS[case['resource_class']]}\n"
        f"  timeout_seconds: {case['timeout_seconds']}\n"
        f"  allowed_tools: {json.dumps(tools)}\n"
    )
    system_instructions: list[str] = []
    trigger_instruction = (
        adapter_common._TRIGGER_MEASUREMENT_INSTRUCTIONS["claude"] if trigger_stage is not None else None
    )
    if trigger_instruction is not None:
        system_instructions.append(trigger_instruction)
    if reference_access is not None:
        system_instructions.append(_CLAUDE_REFERENCE_ACCESS_INSTRUCTION.format(
            read_root=str(case_dir / str(reference_access["add_dir"])),
        ))
    if system_instructions:
        case_config += (
            f"  append_system_prompt: {json.dumps(chr(10).join(system_instructions))}\n"
        )
    external_git_receipt = git_settings is not None and not plan["fixtures"] \
        and prepared_upstream is None
    needs_scaffold = bool(plan["fixtures"]) or prepared_upstream is not None \
        or git_settings is not None
    context: list[str] = []
    if reference_access is not None:
        context.append(f"  add_dirs: {json.dumps([reference_access['add_dir']])}\n")
    if needs_scaffold:
        context.append("  scaffold_script: fixture.sh\n")
    if context:
        case_config += "context:\n" + "".join(context)
    if needs_scaffold:
        _stage_module(case_dir, fixture_setup)
        _stage_module(case_dir, strict_json)
        launcher = "#!/bin/sh\nexec " + shlex.quote(str(Path(sys.executable).resolve()))
        if prepared_upstream is not None:
            _stage_module(case_dir, native_eval_upstream)
            _stage_module(case_dir, native_eval_toolchain)
            adapter_common._write_json(case_dir / "upstream-identity.json", prepared_upstream.runtime_identity)
            scaffold = native_eval_upstream_scaffold
            if git_settings is not None:
                scaffold = native_eval_git_scaffold
                adapter_common._write_text(case_dir / "git-controller-exclude.bin", adapter_common._git_controller_exclude(
                    {}, host="claude", include_upstream=True,
                ).decode("utf-8"))
            _stage_module(case_dir, scaffold)
            launcher += f' -B "${{0%/*}}/{Path(scaffold.__file__).name}"\n'
        elif git_settings is not None:
            _stage_module(case_dir, native_eval_git_scaffold)
            launcher += ' -B "${0%/*}/native_eval_git_scaffold.py"'
            if external_git_receipt:
                launcher += " " + shlex.quote(str(case_dir / "fixture-receipt.json"))
            launcher += "\n"
        else:
            launcher += ' "${0%/*}/native_eval_fixture_setup.py" "${0%/*}/fixture-plan.json"\n'
        adapter_common._write_text(case_dir / "fixture.sh", launcher, mode=0o700)
    adapter_common._write_text(case_dir / "case.yaml", case_config)
    result_path = attempt / "framework-result.json"
    trace_path = attempt / "trace.jsonl"
    output_dir = attempt / "framework-output"
    command = [
        executable, "plugin", "eval", str(plugin), "--case", str(case["id"]),
        "--runs", "1", "--ablation", "none", "--concurrency", "1",
        "--no-publish", "--trust-plugin", "--scaffold", "--keep-temp",
        "--model", model, "--output-dir", str(output_dir),
    ]
    granted = [tool for tool in tools
               if tool.partition("(")[0] in _GATED_CLAUDE_TOOLS or tool.startswith("mcp__")]
    if granted:
        command.extend(["--allow-tools", *granted])
    command.extend(["--json", str(result_path)])
    controller_auth = {
        name: os.environ[name]
        for name in adapter_common._CLAUDE_AUTOMATION_AUTH_VARIABLES
        if isinstance(os.environ.get(name), str) and bool(os.environ[name].strip())
    }
    adapter_common._require(len(controller_auth) == 1,
             "Claude native eval isolation requires exactly one documented automation credential")
    settings = {
        "runs": 1, "ablation": "none", "concurrency": 1, "publish": False,
        "trust_plugin": True, "scaffold": True, "keep_temp": True,
        "allowed_tools": tools, "timeout_seconds": case["timeout_seconds"],
        "resource_class": case.get("resource_class"),
        "declared_artifacts": list(adapter_common._declared_artifacts(case, repo)),
        "verification_record_directories": list(
            native_eval_verification.record_directories(case)
        ),
        "trigger_stage": adapter_common._trigger_identity(trigger_stage, attempt),
        **({"claude_reference_access": reference_access}
           if reference_access is not None else {}),
        **({"claude_explicit_activation": explicit_activation}
           if explicit_activation is not None else {}),
        **({
            "required_tools": list(required_tools),
            "declared_allowed_tools": declared_tools,
            "native_toolchain": adapter_common._native_toolchain_identity(prepared_toolchain),
            "toolchain_bash_grant": toolchain_bash_grant,
            "upstream_integration": {
                "host": "claude",
                "source_relative": prepared_upstream.project_root.relative_to(attempt).as_posix(),
                "runtime_identity": json.loads(adapter_common._canonical_json(prepared_upstream.runtime_identity)),
            },
            "upstream_skill_witnesses": native_eval_upstream.skill_witnesses(
                prepared_upstream.runtime_identity
            ),
        } if prepared_toolchain is not None else {}),
        **({"fixture_read_witnesses": fixture_read_witnesses} if fixture_read_witnesses else {}),
        **({"git_fixture": git_settings} if git_settings is not None else {}),
        "controller_auth": {
            "source": next(iter(controller_auth)),
            "subprocess_scrub": True,
        },
        **({"trigger_measurement_instruction": {
            "text": trigger_instruction,
            "bytes": len(trigger_instruction.encode("utf-8")),
            "sha256": hashlib.sha256(trigger_instruction.encode("utf-8")).hexdigest(),
        }, "trigger_tool_exposure_runtime_qualification_required": True}
           if trigger_instruction is not None else {}),
    }
    settings["controller_home"] = controller_home_identity
    settings["docker_config"] = docker_config_identity
    settings["claude_config_root"] = config_root_identity
    environment = adapter_common._base_environment()
    environment["HOME"] = str(controller_home)
    environment["DOCKER_CONFIG"] = str(docker_config)
    environment["CLAUDE_CONFIG_DIR"] = str(config_root)
    environment["CLAUDE_CODE_SUBPROCESS_ENV_SCRUB"] = "1"
    environment.update(controller_auth)
    if prepared_toolchain is not None:
        original_path = environment.get("PATH", "")
        protected_entries = [str(path) for path in prepared_toolchain.path_entries]
        environment["PATH"] = os.pathsep.join([
            *protected_entries,
            *([original_path] if original_path else []),
        ])
        environment["PYTHONPATH"] = str(plugin)
        environment["PYTHONSAFEPATH"] = "1"
    identity = adapter_common._runtime_identity(
        case=case, host="claude", mode="plugin", model=model, executable=executable,
        cli_version=cli_version, staged_root=plugin, skill_root=plugin / "skills",
        fixture_root=case_dir / "fixture-sources", settings=settings, attempt=attempt,
        command=command, environment=environment,
        staged_tree_exclusions=staged_tree_exclusions,
    )
    return adapter_common.PreparedTrial(command, plugin, environment, "claude", "plugin", attempt,
                         trace_path, result_path, None, identity, trigger_stage)


def _read_claude_result(prepared: adapter_common.PreparedTrial) -> dict[str, Any]:
    result_path = prepared.result_path
    if result_path is None or not result_path.is_file() or result_path.is_symlink():
        raise adapter_common.NativeAdapterError("Claude framework result is unavailable")
    try:
        result = strict_json.loads(result_path.read_bytes(), error=ValueError)
    except (OSError, ValueError) as exc:
        raise adapter_common.NativeAdapterError("Claude framework result is malformed") from exc
    adapter_common._require(isinstance(result, dict) and result.get("schemaVersion") == 1,
             "Claude framework result has an unsupported schemaVersion")
    cases = result.get("cases")
    adapter_common._require(isinstance(cases, list) and len(cases) == 1 and isinstance(cases[0], dict),
             "Claude framework result must contain exactly one case")
    expected_case = prepared.runtime_identity.get("case_id")
    adapter_common._require(cases[0].get("name") == expected_case, "Claude framework result case identity changed")
    arms = cases[0].get("arms")
    with_arm = arms.get("with") if isinstance(arms, dict) else None
    adapter_common._require(isinstance(with_arm, list) and len(with_arm) == 1 and isinstance(with_arm[0], dict),
             "Claude framework result must contain exactly one with arm")
    return result


def _read_claude_trace(prepared: adapter_common.PreparedTrial, result: Mapping[str, Any]) -> tuple[bytes, Path]:
    with_arm = result["cases"][0]["arms"]["with"]
    trace_value = with_arm[0].get("tracePath")
    adapter_common._require(isinstance(trace_value, str) and Path(trace_value).is_absolute(),
             "Claude framework result omitted its absolute tracePath")
    trace_path = Path(trace_value)
    adapter_common._require(not trace_path.is_symlink(), "Claude framework tracePath must not be a symlink")
    try:
        trace_path = trace_path.resolve(strict=True)
    except OSError as exc:
        raise adapter_common.NativeAdapterError("Claude framework trace is unavailable") from exc
    adapter_common._require(trace_path.is_file() and trace_path.name == "trace.jsonl" and trace_path.parent.name == "out",
             "Claude framework tracePath has an unexpected layout")
    artifact_root = trace_path.parent.parent
    allowed_roots = {Path(tempfile.gettempdir()).resolve(), Path("/private/tmp").resolve(), Path("/tmp").resolve()}
    adapter_common._require(any(artifact_root.is_relative_to(root) for root in allowed_roots)
             and artifact_root.name.startswith("e-"), "Claude framework artifact root escaped temporary storage")
    adapter_common._require(not artifact_root.is_relative_to(prepared.attempt_dir),
             "Claude retained run must be outside the staged plugin directory")
    try:
        raw_trace = trace_path.read_bytes()
    except OSError as exc:
        raise adapter_common.NativeAdapterError("Claude framework trace could not be read") from exc
    return raw_trace, artifact_root


def _read_declared_file(workspace_fd: int, relative: str) -> bytes | None:
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    adapter_common._require(nofollow != 0 and directory_flag != 0,
             "platform cannot safely inspect retained Claude artifacts")
    parts = PurePosixPath(relative).parts
    directory_fd = os.dup(workspace_fd)
    try:
        for part in parts[:-1]:
            try:
                child_fd = os.open(
                    part, os.O_RDONLY | directory_flag | nofollow | getattr(os, "O_CLOEXEC", 0),
                    dir_fd=directory_fd,
                )
            except FileNotFoundError:
                return None
            except OSError as exc:
                raise adapter_common.NativeAdapterError(
                    f"declared Claude artifact parent is unsafe: {relative}"
                ) from exc
            os.close(directory_fd)
            directory_fd = child_fd
        try:
            file_fd = os.open(
                parts[-1], os.O_RDONLY | nofollow | getattr(os, "O_NONBLOCK", 0)
                | getattr(os, "O_CLOEXEC", 0), dir_fd=directory_fd,
            )
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise adapter_common.NativeAdapterError(f"declared Claude artifact is unsafe: {relative}") from exc
        try:
            metadata = os.fstat(file_fd)
            adapter_common._require(stat.S_ISREG(metadata.st_mode),
                     f"declared Claude artifact is not a regular file: {relative}")
            adapter_common._require(metadata.st_nlink == 1,
                     f"declared Claude artifact is hard-linked: {relative}")
            adapter_common._require(metadata.st_size <= _ARTIFACT_FILE_LIMIT,
                     f"declared Claude artifact exceeds {_ARTIFACT_FILE_LIMIT} bytes: {relative}")
            payload = bytearray()
            while len(payload) <= _ARTIFACT_FILE_LIMIT:
                chunk = os.read(file_fd, min(65536, _ARTIFACT_FILE_LIMIT + 1 - len(payload)))
                if not chunk:
                    break
                payload.extend(chunk)
            adapter_common._require(len(payload) <= _ARTIFACT_FILE_LIMIT,
                     f"declared Claude artifact exceeds {_ARTIFACT_FILE_LIMIT} bytes: {relative}")
            return bytes(payload)
        finally:
            os.close(file_fd)
    finally:
        os.close(directory_fd)


def _prepared_artifact_declarations(prepared: adapter_common.PreparedTrial) -> tuple[str, ...]:
    settings = prepared.runtime_identity.get("settings", {})
    declared = settings.get("declared_artifacts", []) if isinstance(settings, dict) else []
    adapter_common._require(isinstance(declared, list) and all(isinstance(item, str) for item in declared),
             "prepared Claude artifact declaration is malformed")
    adapter_common._require(len(declared) <= adapter_common._ARTIFACT_COUNT_LIMIT and len(set(declared)) == len(declared),
             "prepared Claude artifact declaration is unbounded or duplicated")
    for relative in declared:
        path = PurePosixPath(relative)
        adapter_common._require(not path.is_absolute() and path.parts and "\\" not in relative
                 and relative == path.as_posix()
                 and all(part not in {"", ".", ".."} for part in path.parts),
                 f"declared artifact path is not canonical: {relative}")
    return tuple(declared)


def _prepared_verification_record_directories(prepared: adapter_common.PreparedTrial) -> tuple[str, ...]:
    settings = prepared.runtime_identity.get("settings", {})
    declared = settings.get("verification_record_directories", []) \
        if isinstance(settings, dict) else []
    adapter_common._require(isinstance(declared, list) and all(isinstance(item, str) for item in declared),
             "prepared verification record directories are malformed")
    adapter_common._require(len(declared) <= adapter_common._ARTIFACT_COUNT_LIMIT and len(set(declared)) == len(declared),
             "prepared verification record directories are unbounded or duplicated")
    for relative in declared:
        path = PurePosixPath(relative)
        adapter_common._require(not path.is_absolute() and path.parts and "\\" not in relative
                 and relative == path.as_posix()
                 and all(part not in {"", ".", ".."} for part in path.parts),
                 f"verification record directory is not canonical: {relative}")
    return tuple(declared)


def _descriptor_capture_supported() -> bool:
    return (
        os.name == "posix" and hasattr(os, "O_DIRECTORY") and hasattr(os, "O_NOFOLLOW")
        and hasattr(os, "geteuid") and hasattr(os, "fchmod")
        and os.chmod in os.supports_dir_fd and os.chmod in os.supports_follow_symlinks
    )


def _chmod_no_follow(name: str, mode: int, directory_fd: int) -> None:
    os.chmod(name, mode, dir_fd=directory_fd, follow_symlinks=False)


@contextmanager
def _retained_claude_workspace(retained_root: Path):
    if not _descriptor_capture_supported():
        raise adapter_common.NativeAdapterError(
            "platform lacks Unix descriptor primitives required for safe Claude artifact capture"
        )
    root_fd: int | None = None
    sealed_fd: int | None = None
    workspace_fd: int | None = None
    restoration_error: OSError | None = None
    root_changed = False
    sealed_changed = False
    root_status: os.stat_result | None = None
    sealed_status: os.stat_result | None = None
    try:
        root_fd = os.open(
            retained_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
        )
        root_status = os.fstat(root_fd)
        sealed_status = os.stat("sealed", dir_fd=root_fd, follow_symlinks=False)
        adapter_common._require(stat.S_ISDIR(root_status.st_mode),
                 "Claude retained root is not a real directory")
        adapter_common._require(stat.S_ISDIR(sealed_status.st_mode),
                 "Claude sealed root is not a real directory")
        adapter_common._require(root_status.st_uid == os.geteuid() and sealed_status.st_uid == os.geteuid(),
                 "Claude retained directories are not owned by the current user")
        os.fchmod(root_fd, 0o700)
        root_changed = True
        _chmod_no_follow("sealed", 0o700, root_fd)
        sealed_changed = True
        sealed_fd = os.open(
            "sealed", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0), dir_fd=root_fd,
        )
        observed_sealed = os.fstat(sealed_fd)
        adapter_common._require((observed_sealed.st_dev, observed_sealed.st_ino)
                 == (sealed_status.st_dev, sealed_status.st_ino),
                 "Claude sealed root changed during artifact capture")
        workspace_fd = os.dup(sealed_fd)
        for part in ("home", "cwd"):
            next_fd = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
                | getattr(os, "O_CLOEXEC", 0), dir_fd=workspace_fd,
            )
            os.close(workspace_fd)
            workspace_fd = next_fd
        yield workspace_fd
    except OSError as exc:
        raise adapter_common.NativeAdapterError(f"Claude retained artifacts could not be captured: {exc}") from exc
    finally:
        if workspace_fd is not None:
            try:
                os.close(workspace_fd)
            except OSError as exc:
                restoration_error = exc
        if sealed_changed and sealed_status is not None:
            try:
                if sealed_fd is not None:
                    os.fchmod(sealed_fd, stat.S_IMODE(sealed_status.st_mode))
                elif root_fd is not None:
                    observed = os.stat("sealed", dir_fd=root_fd, follow_symlinks=False)
                    if (observed.st_dev, observed.st_ino) != (sealed_status.st_dev, sealed_status.st_ino):
                        raise OSError("sealed root changed before mode restoration")
                    _chmod_no_follow("sealed", stat.S_IMODE(sealed_status.st_mode), root_fd)
            except OSError as exc:
                restoration_error = exc
        if root_changed and root_fd is not None and root_status is not None:
            try:
                os.fchmod(root_fd, stat.S_IMODE(root_status.st_mode))
            except OSError as exc:
                restoration_error = restoration_error or exc
        if sealed_fd is not None:
            try:
                os.close(sealed_fd)
            except OSError as exc:
                restoration_error = restoration_error or exc
        if root_fd is not None:
            try:
                os.close(root_fd)
            except OSError as exc:
                restoration_error = restoration_error or exc
        if restoration_error is not None:
            raise adapter_common.NativeAdapterError(
                "Claude retained directory modes could not be restored"
            ) from restoration_error


def _write_artifact_capture(
    prepared: adapter_common.PreparedTrial, workspace_fd: int, declared: tuple[str, ...],
    record_directories: tuple[str, ...],
) -> Path:
    pending = prepared.attempt_dir / f".captured-artifacts-{uuid.uuid4().hex}"
    capture_root = prepared.attempt_dir / "captured-artifacts"
    try:
        capture_root.lstat()
    except FileNotFoundError:
        pass
    else:
        raise ValueError("Claude artifact capture path contains stale evidence")
    try:
        pending.mkdir(mode=0o700)
        total_bytes = 0
        captured = list(declared)
        nofollow = getattr(os, "O_NOFOLLOW", 0)
        directory_flag = getattr(os, "O_DIRECTORY", 0)
        for directory in record_directories:
            directory_fd = os.dup(workspace_fd)
            try:
                missing = False
                for part in PurePosixPath(directory).parts:
                    try:
                        child_fd = os.open(
                            part, os.O_RDONLY | directory_flag | nofollow
                            | getattr(os, "O_CLOEXEC", 0), dir_fd=directory_fd,
                        )
                    except FileNotFoundError:
                        missing = True
                        break
                    except OSError as exc:
                        raise adapter_common.NativeAdapterError(
                            f"verification record directory is unsafe: {directory}"
                        ) from exc
                    os.close(directory_fd)
                    directory_fd = child_fd
                if missing:
                    continue
                names = sorted(os.listdir(directory_fd))
                records = [name for name in names if re.fullmatch(r"[a-f0-9]{32}\.json", name)]
                adapter_common._require(len(captured) + len(records) <= adapter_common._ARTIFACT_COUNT_LIMIT,
                         "captured verification records exceed the artifact count limit")
                captured.extend(f"{directory}/{name}" for name in records)
            finally:
                os.close(directory_fd)
        for relative in captured:
            payload = _read_declared_file(workspace_fd, relative)
            if payload is None:
                continue
            total_bytes += len(payload)
            adapter_common._require(total_bytes <= _ARTIFACT_TOTAL_LIMIT,
                     f"declared Claude artifacts exceed {_ARTIFACT_TOTAL_LIMIT} total bytes")
            destination = pending.joinpath(*PurePosixPath(relative).parts)
            destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            adapter_common._atomic_write_once(destination, payload)
            destination.chmod(0o600)
        pending.rename(capture_root)
        directory = os.open(prepared.attempt_dir, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        return capture_root.resolve(strict=True)
    except OSError as exc:
        raise adapter_common.NativeAdapterError(f"Claude artifact capture could not be retained: {exc}") from exc
    finally:
        if pending.exists():
            shutil.rmtree(pending)


def _capture_claude_artifacts(prepared: adapter_common.PreparedTrial, retained_root: Path) -> Path | None:
    declared = _prepared_artifact_declarations(prepared)
    record_directories = _prepared_verification_record_directories(prepared)
    if not declared:
        return None
    with _retained_claude_workspace(retained_root) as workspace_fd:
        return _write_artifact_capture(
            prepared, workspace_fd, declared, record_directories,
        )


def _verify_claude_reference_access(
    prepared: adapter_common.PreparedTrial, settings: Mapping[str, object],
) -> str | None:
    """Verify the immutable selected source and its in-case reference copy."""
    value = settings.get("claude_reference_access")
    if value is None:
        return None
    adapter_common._require(prepared.host == "claude" and prepared.mode == "plugin"
             and isinstance(value, dict)
             and set(value) == {"schema_version", "skill", "add_dir", "target", "tree_sha256"},
             "prepared Claude reference access identity is malformed")
    skill = value["skill"]
    adapter_common._require(value["schema_version"] == "native-claude-reference-access/v4"
             and isinstance(skill, str)
             and _CLAUDE_SKILL_NAME.fullmatch(skill) is not None
             and isinstance(value["add_dir"], str)
             and isinstance(value["tree_sha256"], str)
             and re.fullmatch(r"[0-9a-f]{64}", value["tree_sha256"]) is not None,
             "prepared Claude reference access identity is malformed")
    leaf = skill.rsplit(":", 1)[1]
    target_relative = PurePosixPath("skills") / leaf / "references"
    adapter_common._require(value["target"] == target_relative.as_posix(),
             "prepared Claude reference access target is malformed")
    case_id = prepared.runtime_identity.get("case_id")
    adapter_common._require(isinstance(case_id, str) and adapter_common._CASE_ID.fullmatch(case_id) is not None,
             "prepared Claude reference access case identity is malformed")
    case_dir = prepared.cwd / "evals" / case_id
    target = prepared.cwd.joinpath(*target_relative.parts)
    granted = case_dir / str(value["add_dir"])
    try:
        case_status = case_dir.lstat()
        target_status = target.lstat()
        granted_status = granted.lstat()
    except OSError as exc:
        raise adapter_common.NativeAdapterError("prepared Claude reference access is unavailable") from exc
    adapter_common._require(stat.S_ISDIR(case_status.st_mode) and not stat.S_ISLNK(case_status.st_mode)
             and stat.S_ISDIR(target_status.st_mode) and not stat.S_ISLNK(target_status.st_mode)
             and stat.S_ISDIR(granted_status.st_mode) and not stat.S_ISLNK(granted_status.st_mode),
             "prepared Claude reference access path is unsafe")
    adapter_common._require(value["add_dir"] == ".native-eval-skill-references",
             "prepared Claude reference access target changed")
    adapter_common._require(adapter_common._tree_digest(target) == value["tree_sha256"]
             and adapter_common._tree_digest(granted) == value["tree_sha256"],
             "prepared Claude reference tree changed")
    return None


def _claude_fixture_receipt_path(prepared: adapter_common.PreparedTrial, settings: Mapping[str, object]) -> Path:
    relative = settings["receipt_relative_path"]
    adapter_common._require(isinstance(relative, str), "prepared Claude fixture receipt path is malformed")
    return prepared.cwd.joinpath(*PurePosixPath(relative).parts)


def _read_claude_fixture_receipt(
    prepared: adapter_common.PreparedTrial, settings: Mapping[str, object],
) -> dict[str, object]:
    path = _claude_fixture_receipt_path(prepared, settings)
    try:
        status = path.lstat()
    except OSError as exc:
        raise adapter_common.NativeAdapterError("Claude fixture receipt is unavailable") from exc
    adapter_common._require(stat.S_ISREG(status.st_mode) and not stat.S_ISLNK(status.st_mode)
             and status.st_nlink == 1 and stat.S_IMODE(status.st_mode) == 0o600
             and status.st_size <= _FIXTURE_RECEIPT_LIMIT,
             "Claude fixture receipt is unsafe")
    try:
        payload = path.read_bytes()
        receipt = strict_json.loads(payload, error=ValueError)
    except (OSError, ValueError) as exc:
        raise adapter_common.NativeAdapterError("Claude fixture receipt is malformed") from exc
    adapter_common._require(isinstance(receipt, dict) and receipt == settings["expected_result"],
             "Claude fixture receipt does not match expected Git materialization")
    return receipt


def _verify_retained_claude_upstream(
    prepared: adapter_common.PreparedTrial, retained_root: Path | None,
) -> None:
    settings = prepared.runtime_identity.get("settings")
    upstream = adapter_common._prepared_upstream_integration(
        prepared.attempt_dir,
        settings.get("upstream_integration") if isinstance(settings, dict) else None,
    )
    if upstream is None:
        return
    adapter_common._require(retained_root is not None,
             "Claude retained workspace is unavailable for upstream verification")
    with _retained_claude_workspace(retained_root) as workspace_fd:
        native_eval_upstream.verify_staged_payloads(
            upstream.runtime_identity,
            lambda relative: _read_declared_file(workspace_fd, relative),
        )
