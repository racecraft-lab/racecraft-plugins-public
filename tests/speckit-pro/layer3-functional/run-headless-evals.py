#!/usr/bin/env python3
"""Capture ungraded evidence for the bounded Layer 3 headless canary roster."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Mapping
import uuid

LAYER_ROOT = Path(__file__).resolve().parent
if str(LAYER_ROOT) not in sys.path:
    sys.path.insert(0, str(LAYER_ROOT))
LAYER2_ROOT = LAYER_ROOT.parent / "layer2-trigger"
if str(LAYER2_ROOT) not in sys.path:
    sys.path.insert(0, str(LAYER2_ROOT))

from preview_helpers import read_eval_data
import run_codex_evals as codex_trigger_evals


CATALOG_PATH = LAYER_ROOT / "headless_cases.json"
PROVIDER_API_ENV_NAMES = {
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "CODEX_API_KEY",
    "OPENAI_API_KEY",
}


class EvidenceError(RuntimeError):
    """The run cannot produce trustworthy evidence."""


class HeldLaunch(EvidenceError):
    """A host/case launch is intentionally held pending a safe contract."""


@dataclass(frozen=True)
class Stage:
    root: Path
    plugin_root: Path
    runtime_root: Path
    workspace: Path
    target_skill: Path
    mcp_config: Path
    plugin_digest: str
    fixture_digest: str
    skill_digest: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_opaque_id() -> str:
    return uuid.uuid4().hex


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def snapshot_tree(root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            snapshot[relative] = "symlink:" + os.readlink(path)
        elif path.is_file():
            snapshot[relative] = sha256_file(path)
    return snapshot


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for relative, value in snapshot_tree(root).items():
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(value.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def load_case_catalog(root: Path) -> dict[str, Any]:
    path = root / CATALOG_PATH.relative_to(repo_root())
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("cases"), list):
        raise EvidenceError(f"invalid headless case catalog: {path}")
    for item in data["cases"]:
        if not isinstance(item, dict) or set(item).intersection({"expectations", "expected_output"}):
            raise EvidenceError("headless case catalog must not contain grading rubrics")
    return data


def find_case(catalog: Mapping[str, Any], host: str, skill: str, eval_id: int) -> dict[str, Any]:
    matches = [
        item
        for item in catalog["cases"]
        if item.get("host") == host and item.get("skill") == skill and item.get("eval_id") == eval_id
    ]
    if len(matches) != 1:
        raise EvidenceError(f"expected one H0 case for {host}:{skill}:{eval_id}, found {len(matches)}")
    return dict(matches[0])


def eval_path(root: Path, case: Mapping[str, Any]) -> Path:
    path = root / "tests" / "speckit-pro" / "layer3-functional" / str(case["eval_file"])
    if not path.is_file():
        raise EvidenceError(f"missing eval corpus: {path}")
    return path


def fixture_path(root: Path, case: Mapping[str, Any]) -> Path:
    path = root / str(case["fixture_root"])
    if not path.is_dir():
        raise EvidenceError(f"missing fixture root: {path}")
    return path


def retain_fixture_provenance(root: Path, case: Mapping[str, Any], evidence_dir: Path) -> str | None:
    source = fixture_path(root, case) / "PROVENANCE.json"
    if not source.is_file():
        return None
    target = evidence_dir / "fixture-provenance.json"
    shutil.copy2(source, target)
    return sha256_file(target)


def eval_prompt(root: Path, case: Mapping[str, Any]) -> str:
    data = read_eval_data(eval_path(root, case))
    if not isinstance(data, dict) or not isinstance(data.get("evals"), list):
        raise EvidenceError("eval corpus has invalid shape")
    matches = [item for item in data["evals"] if isinstance(item, dict) and item.get("id") == case["eval_id"]]
    if len(matches) != 1 or not isinstance(matches[0].get("prompt"), str):
        raise EvidenceError("eval case is missing or has an invalid prompt")
    return str(matches[0]["prompt"])


def build_actor_input(root: Path, case: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "prompt": eval_prompt(root, case),
        "fixture": {
            "root": str(case.get("fixture_destination", ".")),
            "note": str(case["fixture_note"]),
        },
        "skill": str(case["invocation"]),
    }


def render_actor_prompt(actor_input: Mapping[str, Any]) -> bytes:
    fixture = actor_input["fixture"]
    text = (
        f"Use {actor_input['skill']} for the following request.\n"
        f"Fixture root: {fixture['root']}\n"
        f"Fixture note: {fixture['note']}\n"
        f"User request: {actor_input['prompt']}\n"
    )
    return text.encode("utf-8")


def git_identity(root: Path) -> tuple[str, str]:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD^{commit}", "HEAD^{tree}"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise EvidenceError("unable to resolve source commit/tree")
    values = completed.stdout.decode("utf-8", errors="strict").splitlines()
    if len(values) != 2:
        raise EvidenceError("unexpected git identity response")
    return values[0], values[1]


def require_source_identity(
    root: Path,
    expected_commit: str,
    expected_tree: str,
    *,
    require_clean: bool = False,
) -> None:
    actual_commit, actual_tree = git_identity(root)
    if (actual_commit, actual_tree) != (expected_commit, expected_tree):
        raise EvidenceError(
            f"source identity mismatch: expected {expected_commit}/{expected_tree}, "
            f"got {actual_commit}/{actual_tree}"
        )
    if require_clean:
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if status.returncode != 0 or status.stdout:
            raise EvidenceError("source worktree is not clean")


def stage_case(root: Path, case: Mapping[str, Any], stage_root: Path) -> Stage:
    host = str(case["host"])
    skill = str(case["skill"])
    plugin_source = root / "dist" / host / "speckit-pro"
    if not plugin_source.is_dir():
        raise EvidenceError(f"missing rendered {host} distribution: {plugin_source}")
    plugin_root = stage_root / "plugin"
    workspace = stage_root / "workspace"
    fixture_destination = Path(str(case.get("fixture_destination", ".")))
    if fixture_destination.is_absolute() or ".." in fixture_destination.parts:
        raise EvidenceError("fixture destination must stay inside the staged workspace")
    fixture_target = workspace / fixture_destination
    fixture_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(plugin_source, plugin_root)
    shutil.copytree(
        fixture_path(root, case),
        fixture_target,
        ignore=shutil.ignore_patterns("PROVENANCE.json"),
    )
    runtime_root = plugin_root
    staged_skill = plugin_root / "skills" / skill / "SKILL.md"
    target_skill = staged_skill
    if not staged_skill.is_file():
        raise EvidenceError(f"rendered skill is missing: {staged_skill}")

    if host == "codex":
        runtime_root = workspace / "speckit-pro"
        shutil.copytree(plugin_root, runtime_root)
        source_skills = plugin_root / "skills"
        target_skills = workspace / ".agents" / "skills"
        if not source_skills.is_dir():
            raise EvidenceError(f"rendered Codex skills are missing: {source_skills}")
        target_skills.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_skills, target_skills)
        target_skill = target_skills / skill / "SKILL.md"
        if not target_skill.is_file() or sha256_file(target_skill) != sha256_file(staged_skill):
            raise EvidenceError("staged Codex target skill differs from rendered source")
        initialized = subprocess.run(
            ["git", "init", "--quiet", str(workspace)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if initialized.returncode != 0:
            raise EvidenceError("unable to initialize disposable Codex fixture repository")

    mcp_config = stage_root / "empty-mcp.json"
    mcp_config.write_text(json.dumps({"mcpServers": {}}, indent=2) + "\n", encoding="utf-8")
    return Stage(
        root=stage_root,
        plugin_root=plugin_root,
        runtime_root=runtime_root,
        workspace=workspace,
        target_skill=target_skill,
        mcp_config=mcp_config,
        plugin_digest=tree_digest(plugin_root),
        fixture_digest=tree_digest(fixture_path(root, case)),
        skill_digest=sha256_file(staged_skill),
    )


def enumerate_non_target_skills(stage: Stage) -> tuple[Path, ...]:
    """Extend Layer 2's host deny list with this stage's sibling skills."""
    try:
        target = stage.target_skill.resolve(strict=True)
        discovered = set(codex_trigger_evals.enumerate_non_target_skills(target))
        discovered.update(codex_trigger_evals._canonical_skill_files(stage.workspace / ".agents" / "skills"))
    except (OSError, ValueError) as error:
        raise EvidenceError(f"could not inspect Codex skill roots: {error}") from error
    discovered.discard(target)
    return tuple(sorted(discovered, key=str))


def skill_isolation_args(disabled_skills: tuple[Path, ...]) -> list[str]:
    """Build process-local Codex isolation overrides without saved-config mutation."""
    entries = ",".join(
        f"{{path={json.dumps(str(path))},enabled=false}}"
        for path in disabled_skills
    )
    return [
        "--disable", "plugins",
        "--disable", "hooks",
        "--disable", "apps",
        "--config", "skills.bundled.enabled=false",
        "--config", f"skills.config=[{entries}]",
        "--config", "mcp_servers={}",
    ]


def claude_skill_policy(case: Mapping[str, Any], stage: Stage) -> dict[str, Any]:
    """Bind the full staged catalog while permitting only the requested Skill."""
    manifest = json.loads((stage.plugin_root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise EvidenceError("Claude staged plugin manifest must be an object")
    namespace = manifest.get("name")
    if namespace != "speckit-pro" or any(key in manifest for key in ("skills", "commands")):
        raise EvidenceError("Claude staged plugin namespace or custom skill paths are ambiguous")
    if (stage.plugin_root / "commands").exists():
        raise EvidenceError("Claude staged command catalog is not supported")
    names = []
    for directory in sorted((stage.plugin_root / "skills").iterdir()):
        entry = directory / "SKILL.md"
        if directory.is_symlink() or not directory.is_dir() or entry.is_symlink() or not entry.is_file():
            raise EvidenceError("Claude staged skill catalog contains an ambiguous entry")
        text = entry.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        if len(parts) != 3 or parts[0].strip():
            raise EvidenceError("Claude staged skill entry has no valid frontmatter")
        declared = [line.removeprefix("name:").strip() for line in parts[1].splitlines() if line.startswith("name:")]
        if declared != [directory.name] or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", directory.name) is None:
            raise EvidenceError("Claude staged skill name is malformed or ambiguous")
        names.append(f"{namespace}:{directory.name}")
    target = str(case["invocation"]).removeprefix("/")
    if target not in names or target != f"{namespace}:{stage.target_skill.parent.name}":
        raise EvidenceError("Claude requested target is not the staged target skill")
    denied = [name for name in names if name != target] + ["init", "security-review"]
    return {
        "target_skill": target,
        "expected_skills": names,
        "settings": {
            "disableClaudeAiConnectors": True,
            "disableBundledSkills": True,
            "skillOverrides": {"doctor": "off"},
            "permissions": {
                "allow": [f"Skill({target})", f"Skill({target} *)"],
                "deny": [rule for name in denied for rule in (f"Skill({name})", f"Skill({name} *)")],
            },
        },
    }


def build_command(
    case: Mapping[str, Any],
    stage: Stage,
    cli: Path,
    model: str,
    reasoning: str | None,
    disabled_skills: tuple[Path, ...] | None = None,
) -> list[str]:
    if not cli.is_absolute() or not model.strip():
        raise EvidenceError("an absolute CLI path and explicit model are required")
    if case.get("launch_policy") == "hold":
        raise HeldLaunch(str(case.get("hold_reason", "launch held")))
    if case["host"] == "claude":
        tools = ",".join(str(item) for item in case["allowed_tools"])
        policy = claude_skill_policy(case, stage)
        return [
            str(cli),
            "-p",
            "--output-format",
            "stream-json",
            "--verbose",
            "--no-session-persistence",
            "--model",
            model,
            "--restricted",
            "--permission-mode",
            "dontAsk",
            "--permission-prompts",
            "none",
            "--tools",
            tools,
            "--strict-mcp-config",
            "--mcp-config",
            str(stage.mcp_config),
            "--settings",
            json.dumps(policy["settings"], separators=(",", ":"), sort_keys=True),
            "--no-chrome",
            "--add-dir",
            str(stage.plugin_root),
            "--plugin-dir",
            str(stage.plugin_root),
        ]
    if case["host"] == "codex":
        if not reasoning:
            raise EvidenceError("Codex requires an explicit reasoning effort")
        if disabled_skills is None:
            disabled_skills = enumerate_non_target_skills(stage)
        command = [
            str(cli),
            "exec",
            "--json",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--ignore-user-config",
            "--model",
            model,
            "--config",
            f'model_reasoning_effort="{reasoning}"',
            "--config",
            'shell_environment_policy.inherit="none"',
            "--config",
            "shell_environment_policy.set={"
            f"PATH={json.dumps(os.environ.get('PATH', ''))},"
            f"PYTHONPATH={json.dumps(str(stage.runtime_root))}"
            "}",
            "--cd",
            str(stage.workspace),
        ]
        command.extend(skill_isolation_args(disabled_skills))
        command.append("-")
        return command
    raise EvidenceError(f"unsupported host: {case['host']}")


def build_process_env(incoming: Mapping[str, str], plugin_root: Path, *, host: str) -> dict[str, str]:
    present = sorted(name for name in PROVIDER_API_ENV_NAMES if name in incoming)
    if present:
        raise EvidenceError("provider API environment override present by name: " + ", ".join(present))
    result = dict(incoming)
    if host == "claude":
        result["DISABLE_AUTOUPDATER"] = "1"
        result["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"
        result.pop("FORCE_AUTOUPDATE_PLUGINS", None)
    existing = result.get("PYTHONPATH")
    result["PYTHONPATH"] = str(plugin_root) if not existing else str(plugin_root) + os.pathsep + existing
    return result


def probe_cli_version(host: str, cli: Path) -> str:
    if host == "claude":
        executable = shutil.which("claude")
    elif host == "codex":
        executable = shutil.which("codex")
    else:
        raise EvidenceError(f"unsupported host: {host}")
    if executable is None:
        raise EvidenceError(f"{host} CLI disappeared before version probe")
    try:
        if Path(executable).resolve(strict=True) != cli.resolve(strict=True):
            raise EvidenceError(f"{host} CLI changed before version probe")
    except OSError as error:
        raise EvidenceError(f"could not resolve {host} CLI before version probe: {error}") from error
    completed = subprocess.run(
        [executable, "--version"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise EvidenceError(f"CLI version probe exited {completed.returncode}")
    try:
        version = completed.stdout.decode("utf-8", errors="strict").strip()
        completed.stderr.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise EvidenceError("CLI version probe emitted non-UTF-8 output") from error
    if not version:
        raise EvidenceError("CLI version probe returned no version")
    return version


def require_execution_platform(platform_name: str) -> None:
    if platform_name != "posix":
        raise HeldLaunch(
            "live headless collection requires POSIX process-group termination; "
            f"unsupported platform: {platform_name}"
        )


def cleanup_process_group(process: subprocess.Popen, *, natural_exit_grace: bool = True) -> dict[str, Any]:
    """Drain only this capture's original POSIX group, including an exited leader."""
    started = time.monotonic()
    record: dict[str, Any] = {
        "pgid": process.pid,
        "initially_present": None,
        "natural_exit_grace_seconds": 0.2 if natural_exit_grace else 0,
        "signals_sent": [],
        "post_kill_probe_errors": [],
        "verified_absent": False,
        "error": None,
    }

    def present() -> bool:
        process.poll()  # Reap the leader, but never use its exit as group absence.
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError as error:
            if error.errno != errno.EPERM or record["signals_sent"][-1:] != ["SIGKILL"]:
                raise
            record["post_kill_probe_errors"].append({
                "elapsed_seconds": time.monotonic() - started,
                "errno": error.errno,
                "error": f"{type(error).__name__}: {error}",
            })
        return True

    try:
        if type(process.pid) is not int or process.pid <= 1 or process.pid in {os.getpid(), os.getpgrp()}:
            record["error"] = "refusing invalid or self-owned process group identity"
            return record
        record["initially_present"] = present()
        if not record["initially_present"]:
            record["verified_absent"] = True
            return record
        if natural_exit_grace:
            for _ in range(4):
                time.sleep(0.05)
                if not present():
                    record["verified_absent"] = True
                    return record
        for sent in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(process.pid, sent)
            except ProcessLookupError:
                record["verified_absent"] = True
                return record
            record["signals_sent"].append(sent.name)
            for _ in range(20):
                if not present():
                    record["verified_absent"] = True
                    return record
                time.sleep(0.05)
        record["error"] = "owned process group absence not verified after bounded TERM/KILL cleanup"
    except (OSError, KeyboardInterrupt) as error:
        record["error"] = f"owned process-group cleanup could not be verified: {type(error).__name__}: {error}"
    finally:
        record["duration_seconds"] = time.monotonic() - started
    return record


def capture_process(
    host: str,
    command: list[str],
    stdin_bytes: bytes,
    evidence_dir: Path,
    cwd: Path,
    env: Mapping[str, str],
    timeout_seconds: int,
) -> dict[str, Any]:
    interruption: dict[str, Any] = {"signal": None, "cleanup_started": False}
    previous_handlers: dict[int, Any] = {}

    def interrupt_capture(signum: int, _frame: Any) -> None:
        interruption["signal"] = signal.Signals(signum).name
        if not interruption["cleanup_started"]:
            raise KeyboardInterrupt

    try:
        try:
            for signum in (signal.SIGTERM, signal.SIGHUP):
                previous = signal.getsignal(signum)
                signal.signal(signum, interrupt_capture)
                previous_handlers[signum] = previous
        except (OSError, ValueError) as error:
            return {"status": "launch_error", "error": f"unable to install scoped capture signal handlers: {error}"}
        result = _capture_process(host, command, stdin_bytes, evidence_dir, cwd, env, timeout_seconds, interruption)
        result["interruption_signal"] = interruption["signal"]
        if interruption["signal"] is not None and result["status"] == "completed_ungraded":
            result["status"] = "interrupted"
        return result
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)


def _capture_process(
    host: str,
    command: list[str],
    stdin_bytes: bytes,
    evidence_dir: Path,
    cwd: Path,
    env: Mapping[str, str],
    timeout_seconds: int,
    interruption: dict[str, Any],
) -> dict[str, Any]:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    started_at = utc_now()
    started = time.monotonic()
    if host == "claude":
        executable = shutil.which("claude")
    elif host == "codex":
        executable = shutil.which("codex")
    else:
        return {
            "status": "launch_error",
            "error": f"unsupported host: {host}",
            "started_at": started_at,
            "finished_at": utc_now(),
            "duration_seconds": time.monotonic() - started,
        }
    if executable is None:
        return {
            "status": "launch_error",
            "error": f"{host} CLI disappeared before execution",
            "started_at": started_at,
            "finished_at": utc_now(),
            "duration_seconds": time.monotonic() - started,
        }
    try:
        if not command or Path(executable).resolve(strict=True) != Path(command[0]).resolve(strict=True):
            raise OSError(f"{host} CLI changed before execution")
    except OSError as error:
        return {
            "status": "launch_error",
            "error": str(error),
            "started_at": started_at,
            "finished_at": utc_now(),
            "duration_seconds": time.monotonic() - started,
        }
    try:
        process = subprocess.Popen(
            [executable, *command[1:]],
            cwd=cwd,
            env=dict(env),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            start_new_session=True,
        )
    except OSError as error:
        return {
            "status": "launch_error",
            "error": str(error),
            "started_at": started_at,
            "finished_at": utc_now(),
            "duration_seconds": time.monotonic() - started,
        }
    status = "completed_ungraded"
    termination_error: str | None = None
    stdout_bytes = stderr_bytes = b""
    needs_drain = False
    try:
        stdout_bytes, stderr_bytes = process.communicate(stdin_bytes, timeout=timeout_seconds)
    except subprocess.TimeoutExpired as timeout_error:
        status = "timeout"
        needs_drain = True
        stdout_bytes = timeout_error.output or b""
        stderr_bytes = timeout_error.stderr or b""
    except KeyboardInterrupt:
        status = "interrupted"
        needs_drain = True
    except OSError as error:
        status = "capture_error"
        termination_error = str(error)
        needs_drain = True
    finally:
        interruption["cleanup_started"] = True
        capture_status = status
        exit_code_before_cleanup = process.returncode
        cleanup = cleanup_process_group(process, natural_exit_grace=status == "completed_ungraded")
        if not cleanup["verified_absent"]:
            status = "process_cleanup_error"
            termination_error = str(cleanup["error"])
        elif status == "completed_ungraded" and cleanup["signals_sent"]:
            status = "unexpected_descendants"
    if needs_drain:
        try:
            stdout_bytes, stderr_bytes = process.communicate(timeout=5)
        except subprocess.TimeoutExpired as drain_error:
            if status != "process_cleanup_error":
                status = "termination_error"
            suffix = "timed out draining pipes after termination"
            termination_error = f"{termination_error}; {suffix}" if termination_error else suffix
            stdout_bytes = drain_error.output or stdout_bytes
            stderr_bytes = drain_error.stderr or stderr_bytes
        except (OSError, KeyboardInterrupt) as error:
            if status != "process_cleanup_error":
                status = "termination_error"
            suffix = f"unable to drain captured pipes: {type(error).__name__}: {error}"
            termination_error = f"{termination_error}; {suffix}" if termination_error else suffix
    (evidence_dir / "stdout.bin").write_bytes(stdout_bytes)
    (evidence_dir / "stderr.bin").write_bytes(stderr_bytes)
    stdout_sha256 = sha256_bytes(stdout_bytes)
    stderr_sha256 = sha256_bytes(stderr_bytes)
    try:
        stdout = stdout_bytes.decode("utf-8", errors="strict")
        stderr = stderr_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        return {
            "status": "output_decode_error" if status == "completed_ungraded" else status,
            "decode_error": str(error),
            "termination_error": termination_error,
            "capture_status": capture_status,
            "exit_code_before_cleanup": exit_code_before_cleanup,
            "process_group_cleanup": cleanup,
            "exit_code": process.returncode,
            "stdout_sha256": stdout_sha256,
            "stderr_sha256": stderr_sha256,
            "started_at": started_at,
            "finished_at": utc_now(),
            "duration_seconds": time.monotonic() - started,
        }
    (evidence_dir / "stdout.txt").write_text(stdout, encoding="utf-8")
    (evidence_dir / "stderr.txt").write_text(stderr, encoding="utf-8")
    if status == "completed_ungraded" and process.returncode != 0:
        status = "process_error"
    return {
        "status": status,
        "exit_code": process.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "stdout_sha256": stdout_sha256,
        "stderr_sha256": stderr_sha256,
        "termination_error": termination_error,
        "capture_status": capture_status,
        "exit_code_before_cleanup": exit_code_before_cleanup,
        "process_group_cleanup": cleanup,
        "started_at": started_at,
        "finished_at": utc_now(),
        "duration_seconds": time.monotonic() - started,
    }


def parse_jsonl(stdout: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(stdout.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as error:
            raise EvidenceError(f"invalid JSONL at line {line_number}: {error}") from error
        if not isinstance(item, dict) or not isinstance(item.get("type"), str):
            raise EvidenceError(f"invalid event at line {line_number}")
        events.append(item)
    if not events:
        raise EvidenceError("provider emitted no JSONL events")
    return events


def parse_events(host: str, stdout: str) -> dict[str, Any]:
    events = parse_jsonl(stdout)
    tool_trace: list[dict[str, Any]] = []
    if host == "codex":
        types = [str(item["type"]) for item in events]
        if any(name.endswith(".failed") for name in types):
            raise EvidenceError("Codex JSONL contains a failed lifecycle event")
        for required in ("thread.started", "turn.started", "turn.completed"):
            if types.count(required) != 1:
                raise EvidenceError(f"expected exactly one {required} event")
        positions = [types.index(name) for name in ("thread.started", "turn.started", "turn.completed")]
        if positions != sorted(positions) or positions[-1] != len(types) - 1:
            raise EvidenceError("Codex lifecycle events are out of order or terminal is not last")
        for event in events:
            if event["type"] != "item.completed" or not isinstance(event.get("item"), dict):
                continue
            item = event["item"]
            if item.get("type") in {"error", "failed"}:
                raise EvidenceError("Codex JSONL contains a failed completed item")
            if item.get("type") in {"command_execution", "mcp_tool_call", "tool_call"}:
                tool_trace.append(item)
        return {
            "terminal_type": "turn.completed",
            "resolved_model": None,
            "resolved_model_evidence": "not emitted by parsed Codex JSONL",
            "tool_trace": tool_trace,
            "event_count": len(events),
        }
    if host == "claude":
        init = [item for item in events if item["type"] == "system" and item.get("subtype") == "init"]
        results = [item for item in events if item["type"] == "result"]
        if len(init) != 1 or len(results) != 1:
            raise EvidenceError("expected exactly one Claude system/init and result event")
        if events.index(init[0]) > events.index(results[0]) or events[-1] is not results[0]:
            raise EvidenceError("Claude lifecycle events are out of order or terminal is not last")
        if results[0].get("is_error") is True:
            raise EvidenceError("Claude result event reports an error")
        completed_tool_use_ids: set[str] = set()
        for event in events:
            message = event.get("message")
            if not isinstance(message, dict):
                continue
            content = message.get("content", [])
            if event["type"] == "assistant" and isinstance(content, list):
                tool_trace.extend(item for item in content if isinstance(item, dict) and item.get("type") == "tool_use")
            if event["type"] == "user" and isinstance(content, list):
                completed_tool_use_ids.update(
                    str(item["tool_use_id"])
                    for item in content
                    if isinstance(item, dict)
                    and item.get("type") == "tool_result"
                    and isinstance(item.get("tool_use_id"), str)
                    and item.get("is_error") is not True
                )
        model = init[0].get("model")
        return {
            "terminal_type": "result",
            "resolved_model": model if isinstance(model, str) else None,
            "resolved_model_evidence": "system/init.model" if isinstance(model, str) else "not emitted",
            "plugins": init[0].get("plugins"),
            "available_tools": init[0].get("tools"),
            "available_skills": init[0].get("skills"),
            "tool_trace": tool_trace,
            "completed_tool_use_ids": sorted(completed_tool_use_ids),
            "event_count": len(events),
        }
    raise EvidenceError(f"unsupported host event stream: {host}")


def require_provider_evidence(
    case: Mapping[str, Any],
    parsed: Mapping[str, Any],
    claude_policy: Mapping[str, Any] | None = None,
) -> None:
    required = {str(item) for item in case.get("required_tools", [])}
    if case["host"] == "claude":
        if claude_policy is None:
            raise EvidenceError("Claude evidence requires the bound staged Skill policy")
        skills = parsed.get("available_skills")
        if (
            not isinstance(skills, list)
            or not all(isinstance(item, str) for item in skills)
            or sorted(skills) != claude_policy["expected_skills"]
        ):
            raise EvidenceError("Claude system/init skill catalog differs from the bound staged catalog")
        available_raw = parsed.get("available_tools")
        available = {str(item) for item in available_raw} if isinstance(available_raw, list) else set()
        allowed = {str(item) for item in case.get("allowed_tools", [])}
        missing = sorted(allowed - available)
        unexpected = sorted(available - allowed)
        plugins = parsed.get("plugins")
        plugin_names = {
            str(item.get("name")) if isinstance(item, dict) else str(item)
            for item in plugins
        } if isinstance(plugins, list) else set()
        if "speckit-pro" not in plugin_names:
            raise EvidenceError("Claude system/init did not prove the speckit-pro plugin loaded")
        if missing or unexpected:
            details = []
            if missing:
                details.append("missing tools: " + ", ".join(missing))
            if unexpected:
                details.append("unexpected tools: " + ", ".join(unexpected))
            raise EvidenceError("Claude system/init tool catalog differs from the allowed set: " + "; ".join(details))
        if parsed.get("resolved_model") is None:
            raise EvidenceError("Claude system/init did not report a resolved model")
        expected_skill = str(case["invocation"]).removeprefix("/")
        if expected_skill != claude_policy["target_skill"]:
            raise EvidenceError("Claude requested target differs from the bound staged Skill policy")
        for item in parsed.get("tool_trace", []):
            if isinstance(item, dict) and item.get("name") == "Skill":
                supplied = item.get("input")
                if not isinstance(supplied, dict) or supplied.get("skill") != expected_skill:
                    raise EvidenceError("Claude trace contains a non-target Skill attempt")
        completed = {str(item) for item in parsed.get("completed_tool_use_ids", [])}
        matching_skill_uses = [
            item
            for item in parsed.get("tool_trace", [])
            if isinstance(item, dict)
            and item.get("name") == "Skill"
            and isinstance(item.get("input"), dict)
            and item["input"].get("skill") == expected_skill
        ]
        if not any(str(item.get("id")) in completed for item in matching_skill_uses):
            raise EvidenceError(
                f"Claude trace did not prove a successful exact Skill invocation: {expected_skill}"
            )
        return
    observed = {
        str(item.get("type"))
        for item in parsed.get("tool_trace", [])
        if isinstance(item, dict)
    }
    missing = sorted(required - observed)
    if missing:
        raise EvidenceError("Codex completed trace is missing required tools: " + ", ".join(missing))


def final_status(process_status: str, cleanup_error: str | None) -> str:
    return "cleanup_error" if cleanup_error else process_status


def write_checksum_index(root: Path) -> None:
    lines = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "sha256.txt":
            lines.append(f"{sha256_file(path)}  {path.relative_to(root).as_posix()}")
    (root / "sha256.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--host", choices=("claude", "codex"), required=True)
    result.add_argument("--skill", choices=("speckit-autopilot", "speckit-coach"), required=True)
    result.add_argument("--eval-id", type=int, required=True)
    result.add_argument("--source-commit", required=True)
    result.add_argument("--source-tree", required=True)
    result.add_argument("--model", required=True)
    result.add_argument("--reasoning", choices=("low", "medium", "high", "xhigh"))
    result.add_argument("--cli", type=Path, required=True)
    result.add_argument("--evidence-dir", type=Path, required=True)
    result.add_argument("--timeout", type=int, default=600)
    result.add_argument("--execute", action="store_true")
    return result


def main(argv: list[str]) -> int:
    args = parser().parse_args(argv)
    root = repo_root()
    evidence_root = args.evidence_dir.resolve()
    if evidence_root.is_relative_to(root.resolve()):
        print("ERROR: evidence directory must be outside the source worktree", file=sys.stderr)
        return 2
    if evidence_root.exists():
        print(f"ERROR: evidence directory already exists: {evidence_root}", file=sys.stderr)
        return 2
    evidence_root.mkdir(parents=True)
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "status": "setup_error",
        "source_commit": args.source_commit,
        "source_tree": args.source_tree,
        "host": args.host,
        "requested_model": args.model,
        "resolved_model": None,
        "reasoning": args.reasoning,
        "cli": str(args.cli),
        "created_at": utc_now(),
        "semantic_grade": "not_performed",
    }
    stage_root: Path | None = None
    cleanup_error: str | None = None
    exit_code = 1
    try:
        require_source_identity(root, args.source_commit, args.source_tree, require_clean=True)
        if not args.cli.is_absolute() or not args.cli.is_file() or not os.access(args.cli, os.X_OK):
            raise EvidenceError("CLI must be an existing executable absolute path")
        manifest["cli_version"] = probe_cli_version(args.host, args.cli)
        catalog = load_case_catalog(root)
        case = find_case(catalog, args.host, args.skill, args.eval_id)
        actor_input = build_actor_input(root, case)
        opaque_id = new_opaque_id()
        case_evidence = evidence_root / "cases" / opaque_id
        case_evidence.parent.mkdir()
        case_evidence.mkdir()
        fixture_provenance_sha256 = retain_fixture_provenance(root, case, case_evidence)
        (case_evidence / "actor-input.json").write_text(
            json.dumps(actor_input, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        stage_root = Path(tempfile.mkdtemp(prefix=f"speckit-l3-{opaque_id}-"))
        stage = stage_case(root, case, stage_root)
        claude_policy = claude_skill_policy(case, stage) if args.host == "claude" else None
        if claude_policy is not None:
            manifest["claude_skill_policy"] = claude_policy
        disabled_skills = (
            enumerate_non_target_skills(stage)
            if args.host == "codex"
            else None
        )
        before = snapshot_tree(stage.workspace)
        before_path = case_evidence / "workspace-before.json"
        before_path.write_text(json.dumps(before, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        manifest.update(
            {
                "opaque_case_id": opaque_id,
                "case_identity": {"skill": args.skill, "eval_id": args.eval_id},
                "eval_file": str(case["eval_file"]),
                "eval_file_sha256": sha256_file(eval_path(root, case)),
                "case_catalog_sha256": sha256_file(root / CATALOG_PATH.relative_to(repo_root())),
                "plugin_tree_sha256": stage.plugin_digest,
                "fixture_tree_sha256": stage.fixture_digest,
                "fixture_provenance_sha256": fixture_provenance_sha256,
                "skill_sha256": stage.skill_digest,
                "workspace_before_sha256": sha256_file(before_path),
            }
        )
        try:
            command = build_command(
                case,
                stage,
                args.cli,
                args.model,
                args.reasoning,
                disabled_skills,
            )
        except HeldLaunch as error:
            manifest.update({"status": "held", "hold_reason": str(error)})
            exit_code = 4
        else:
            manifest["command"] = command
            env = None
            if args.host == "claude":
                env = build_process_env(os.environ, stage.runtime_root, host=args.host)
                manifest["claude_startup_environment"] = {
                    name: env.get(name)
                    for name in (
                        "DISABLE_AUTOUPDATER",
                        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC",
                        "FORCE_AUTOUPDATE_PLUGINS",
                    )
                }
            if not args.execute:
                manifest["status"] = "preflight_only"
                exit_code = 0
            else:
                try:
                    require_execution_platform(os.name)
                except HeldLaunch as error:
                    manifest.update({"status": "held", "hold_reason": str(error)})
                    exit_code = 4
                    process_result = None
                else:
                    if args.host == "codex" and enumerate_non_target_skills(stage) != disabled_skills:
                        raise EvidenceError("Codex skill roots changed after command assembly")
                    if args.host == "claude" and (
                        tree_digest(stage.plugin_root) != stage.plugin_digest
                        or claude_skill_policy(case, stage) != claude_policy
                    ):
                        raise EvidenceError("Claude staged plugin or Skill policy changed after command assembly")
                    if env is None:
                        env = build_process_env(os.environ, stage.runtime_root, host=args.host)
                    process_result = capture_process(
                        args.host,
                        command,
                        render_actor_prompt(actor_input),
                        case_evidence,
                        stage.workspace,
                        env,
                        args.timeout,
                    )
                if process_result is not None:
                    manifest["process"] = {
                        key: value
                        for key, value in process_result.items()
                        if key not in {"stdout", "stderr"}
                    }
                    status = str(process_result["status"])
                    if status == "completed_ungraded":
                        try:
                            parsed = parse_events(args.host, str(process_result["stdout"]))
                        except EvidenceError as error:
                            status = "event_parse_error"
                            manifest["event_error"] = str(error)
                        else:
                            try:
                                require_provider_evidence(case, parsed, claude_policy)
                            except EvidenceError as error:
                                status = "provider_evidence_error"
                                manifest["event_error"] = str(error)
                            manifest["provider_evidence"] = parsed
                            manifest["resolved_model"] = parsed["resolved_model"]
                            (case_evidence / "tool-trace.json").write_text(
                                json.dumps(parsed["tool_trace"], indent=2, sort_keys=True) + "\n",
                                encoding="utf-8",
                            )
                    after = snapshot_tree(stage.workspace)
                    after_path = case_evidence / "workspace-after.json"
                    after_path.write_text(
                        json.dumps(after, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                    manifest["workspace_after_sha256"] = sha256_file(after_path)
                    if before != after and status == "completed_ungraded":
                        status = "workspace_changed"
                    manifest["status"] = status
                    exit_code = 0 if status == "completed_ungraded" else 1
    except (EvidenceError, OSError, ValueError, json.JSONDecodeError) as error:
        manifest.update({"status": "setup_error", "error": str(error)})
        exit_code = 1
    finally:
        if stage_root is not None:
            try:
                shutil.rmtree(stage_root)
            except OSError as error:
                cleanup_error = str(error)
        manifest["cleanup_error"] = cleanup_error
        manifest["status"] = final_status(str(manifest["status"]), cleanup_error)
        manifest["finished_at"] = utc_now()
        (evidence_root / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        write_checksum_index(evidence_root)
    print(json.dumps({"status": manifest["status"], "evidence_dir": str(evidence_root)}))
    return 1 if cleanup_error else exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
