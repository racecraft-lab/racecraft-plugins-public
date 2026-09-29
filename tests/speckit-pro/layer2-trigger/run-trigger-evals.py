#!/usr/bin/env python3
"""Run isolated Claude Layer 2 skill-selection evaluations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import signal
import subprocess
import sys
import tempfile
# Unused here, but tests patch time.monotonic and time.sleep through this module.
import time  # noqa: F401
import uuid


SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_LIB = SCRIPT_DIR.parent / "lib"
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))
import trigger_process as processes  # noqa: E402
import trigger_evidence as evidence_records  # noqa: E402
import trigger_comparison as experiment_evidence  # noqa: E402
import trigger_first_selection_guard as first_selection_guard  # noqa: E402
from trigger_claude_observer import inspect_claude_stream  # noqa: E402

PLUGIN_ROOT = (SCRIPT_DIR / "../../../speckit-pro").resolve()
DEFAULT_MODEL = "claude-sonnet-5"
PINNED_CLAUDE_VERSION = "2.1.270 (Claude Code)"
PINNED_DOCTOR_RUNNING = "Running: native (2.1.270)"
PINNED_MANAGED_SETTINGS = (
    "Managed settings (remote): not fetched — requires an Enterprise or Team subscription"
)
PINNED_ORGANIZATION_POLICY = "Organization policy: not applicable to Pro and Max accounts"
MACOS_MANAGED_ROOT = Path("/Library/Application Support/ClaudeCode")
LINUX_MANAGED_ROOT = Path("/etc/claude-code")
RUNS_PER_QUERY = 3
TRIGGER_THRESHOLD = 0.5
NO_SPECKIT_SKILL_NAME = evidence_records.NO_SPECKIT_SKILL_NAME
NO_SPECKIT_SKILL_DESCRIPTION = evidence_records.NO_SPECKIT_SKILL_DESCRIPTION
MEASUREMENT_STUB_SENTENCE = (
    "This skill is a measurement stub used by the repository's skill-selection test suite. It is not a real "
    "workflow and contains no injected instruction."
)
REQUIRED_FLAGS = (
    "--restricted",
    "--setting-sources",
    "--plugin-dir",
    "--strict-mcp-config",
    "--mcp-config",
    "--tools",
    "--allowedTools",
    "--settings",
    "--permission-mode",
    "--permission-prompts",
    "--output-format",
    "--include-hook-events",
    "--verbose",
    "--no-session-persistence",
)
ACTIVE_CHILD: subprocess.Popen[bytes] | None = None
CLEANUP_TIMEOUT = processes.CLEANUP_TIMEOUT
DESCENDANT_EXIT_GRACE = processes.DESCENDANT_EXIT_GRACE


ClaudeQueryError = processes.QueryError


TerminationRequested = processes.TerminationRequested


def eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


load_eval_corpus = evidence_records.load_eval_corpus
available_evals = evidence_records.available_evals


def find_eval_file(skill: str) -> Path:
    path = PLUGIN_ROOT.parent / "tests" / "speckit-pro" / "layer2-trigger" / "evals" / f"{skill}-trigger.json"
    if not path.is_file():
        available = ", ".join(available_evals(path.parent)) or "none"
        raise ValueError(f"eval file not found for {skill!r}; available: {available}")
    return path


def find_skill_source(skill: str) -> Path:
    for relative in (f"skills/{skill}/SKILL.md", f"codex-skills/{skill}/SKILL.md"):
        path = PLUGIN_ROOT / relative
        if path.is_file():
            return path
    raise ValueError(f"skill not found for requested skill {skill!r}")


def source_description_lines(source: Path) -> list[str]:
    """Return the source YAML description field without rewriting its value."""
    text = source.read_text(encoding="utf-8")
    match = re.match(r"^---\n(?P<frontmatter>.*?)\n---(?:\n|$)", text, re.DOTALL)
    if match is None:
        raise ValueError(f"source skill has no YAML frontmatter: {source}")
    lines = match.group("frontmatter").splitlines()
    for index, line in enumerate(lines):
        if not line.startswith("description:"):
            continue
        description = [line]
        for continuation in lines[index + 1 :]:
            if continuation.startswith((" ", "\t")) or not continuation:
                description.append(continuation)
                continue
            break
        if line.removeprefix("description:").strip() or len(description) > 1:
            return description
    raise ValueError(f"source skill has no non-empty description: {source}")


sibling_skill_dirs = evidence_records.sibling_skill_dirs


def _stage_first_selection_guard(plugin_root: Path) -> None:
    """Install the native PostToolUse stop guard into one staged plugin."""
    guard_name = "trigger_first_selection_guard.py"
    scripts_dir = plugin_root / "scripts"
    scripts_dir.mkdir()
    shutil.copy2(Path(str(first_selection_guard.__file__)), scripts_dir / guard_name)
    hooks_dir = plugin_root / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "hooks.json").write_text(
        json.dumps(
            {
                "description": "Stop a Layer 2 trial after its first successful Skill call",
                "hooks": {
                    first_selection_guard.HOOK_EVENT: [{
                        "matcher": "Skill",
                        "hooks": [{
                            "type": "command",
                            "command": sys.executable,
                            "args": [f"${{CLAUDE_PLUGIN_ROOT}}/scripts/{guard_name}"],
                            "timeout": 5,
                        }],
                    }]
                },
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )


def _write_sibling_skill(plugin_root: Path, name: str, description_lines: list[str]) -> None:
    sibling_dir = plugin_root / "skills" / name
    sibling_dir.mkdir(parents=True)
    body = ["---", f"name: {name}", "\n".join(description_lines), "---", "",
            "This sibling skill is part of a selection check. If it is selected,",
            "say so in one line and stop.", ""]
    (sibling_dir / "SKILL.md").write_text("\n".join(body), encoding="utf-8")


def _sibling_descriptions(siblings: dict[str, Path | str] | None) -> dict[str, list[str]]:
    """Description lines per staged sibling; a ``str`` source is a literal description."""
    descriptions = {NO_SPECKIT_SKILL_NAME: [f"description: {NO_SPECKIT_SKILL_DESCRIPTION}"]}
    for name, source in (siblings or {}).items():
        if name == NO_SPECKIT_SKILL_NAME and not isinstance(source, str):
            raise ValueError(f"reserved sibling skill name: {NO_SPECKIT_SKILL_NAME}")
        descriptions[name] = [f"description: {source}"] if isinstance(source, str) else source_description_lines(source)
    return descriptions


def stage_measurement_plugin(
    source: Path,
    plugin_root: Path,
    plugin_name: str,
    skill_name: str,
    nonce: str,
    siblings: dict[str, Path | str] | None = None,
) -> tuple[Path, str]:
    """Stage only the exact source description plus a minimal measurement body.

    ``siblings`` maps each sibling skill name to its source SKILL.md. Siblings are
    staged with their exact descriptions and a minimal body carrying no nonce, so a
    should-not-trigger query has its real destination in the catalog. The reserved
    no-op skill may appear only with a ``str`` value, which replaces its default
    description; that is how a controlled experiment varies it without a global.
    """
    for sibling_name, description_lines in sorted(_sibling_descriptions(siblings).items()):
        if sibling_name == skill_name:
            raise ValueError("sibling skill name collides with the measured skill")
        _write_sibling_skill(plugin_root, sibling_name, description_lines)
    skill_dir = plugin_root / "skills" / skill_name
    skill_dir.mkdir(parents=True)
    description = "\n".join(source_description_lines(source))
    (skill_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                f"name: {skill_name}",
                description,
                "---",
                "",
                MEASUREMENT_STUB_SENTENCE,
                "When this skill is selected, reply with this nonce as the first line of your reply:",
                "",
                nonce,
                "",
                "Then stop: do not invoke any skill again and do not continue the task.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    manifest_dir = plugin_root / ".claude-plugin"
    manifest_dir.mkdir()
    (manifest_dir / "plugin.json").write_text(
        json.dumps({"name": plugin_name, "version": "0.0.0"}, indent=2) + "\n",
        encoding="utf-8",
    )
    _stage_first_selection_guard(plugin_root)
    return skill_dir, f"{plugin_name}:{skill_name}"


def write_empty_mcp_config(path: Path) -> None:
    path.write_text(json.dumps({"mcpServers": {}}, indent=2) + "\n", encoding="utf-8")


retain_trial_evidence = evidence_records.retain_trial_evidence


def terminate_child(child: subprocess.Popen[bytes] | None, signum: int = signal.SIGTERM) -> bool:
    return processes.terminate_child(child, signum)


def cleanup_child(
    child: subprocess.Popen[bytes], *, observations: list[dict[str, object]] | None = None,
) -> bool:
    return processes.cleanup_child(child, observations=observations, timeout=CLEANUP_TIMEOUT,
                                   grace=DESCENDANT_EXIT_GRACE, terminate=terminate_child)


handle_termination = processes.handle_termination
install_termination_handlers = processes.install_termination_handlers
restore_termination_handlers = processes.restore_termination_handlers


def claude_environment() -> dict[str, str]:
    """Keep login location and locale while excluding inherited Claude controls."""
    environment = {
        key: os.environ[key]
        for key in ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "LC_CTYPE", "USER")
        if key in os.environ
    }
    environment.update({
        "DISABLE_AUTOUPDATER": "1",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        "CLAUDE_CODE_MAX_RETRIES": "0",
    })
    return environment


def _claude_launch_contract(command: list[str], environment: dict[str, str], model: str) -> dict[str, object]:
    settings_sources = [
        command[index + 1]
        for index, argument in enumerate(command[:-1])
        if argument == "--setting-sources"
    ]
    return {
        "config_isolated": (
            "--restricted" in command
            and "--strict-mcp-config" in command
            and settings_sources == [""]
        ),
        "retries_disabled": environment.get("CLAUDE_CODE_MAX_RETRIES") == "0",
        "requested_model": model,
        "model_provider": "anthropic-claude-code",
        "model_identity_evidence": "native-init-and-assistant-events",
    }


def run_claude_query(
    executable: str,
    plugin_root: Path,
    mcp_config: Path,
    query: str,
    model: str,
    timeout: int,
    *,
    expected_skill: str,
    sibling_skills: tuple[str, ...] = (),
    process_evidence: dict[str, object] | None = None,
) -> tuple[int, bytes, bytes, bool]:
    global ACTIVE_CHILD
    candidate = shutil.which("claude")
    if candidate is None:
        raise OSError("Claude CLI disappeared after initial resolution")
    if candidate != executable:
        raise ValueError("Claude runtime changed after initial resolution")
    plugin_name, separator, _skill_name = expected_skill.partition(":")
    no_speckit_skill = (
        f"{plugin_name}:{NO_SPECKIT_SKILL_NAME}" if separator else NO_SPECKIT_SKILL_NAME
    )
    sibling_skills = tuple(sorted({*sibling_skills, no_speckit_skill}))
    command = [
        candidate,
        "--restricted",
        "--setting-sources", "",
        "--plugin-dir", str(plugin_root),
        "--strict-mcp-config",
        "--mcp-config", str(mcp_config),
        "--tools", "Skill",
        "--allowedTools", f"Skill({expected_skill})", f"Skill({expected_skill} *)",
        *(rule for sibling in sibling_skills for rule in (f"Skill({sibling})", f"Skill({sibling} *)")),
        "--permission-mode", "dontAsk",
        "--permission-prompts", "none",
        "--settings", json.dumps({
            "disableBundledSkills": True,
            "skillOverrides": {"doctor": "off"},
            "permissions": {"deny": [
                "Skill(init)", "Skill(init *)", "Skill(security-review)", "Skill(security-review *)"
            ]},
        }),
        "-p", query,
        "--model", model,
        "--output-format", "stream-json",
        "--include-hook-events",
        "--verbose",
        "--no-session-persistence",
    ]
    environment = claude_environment()
    if process_evidence is not None:
        process_evidence["launch_contract"] = _claude_launch_contract(command, environment, model)
        process_evidence["launch_contract"]["query_sha256"] = hashlib.sha256(query.encode()).hexdigest()
    child = subprocess.Popen(
        command,
        cwd=plugin_root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
        shell=False,
        start_new_session=os.name != "nt",
    )
    ACTIVE_CHILD = child
    try:
        return processes.supervise_child(child, timeout, cleanup=cleanup_child,
                                         cleanup_timeout=CLEANUP_TIMEOUT, evidence=process_evidence)
    finally:
        ACTIVE_CHILD = None


def remove_plugin_root(plugin_root: Path) -> str | None:
    try:
        shutil.rmtree(plugin_root)
    except OSError as exc:
        return f"could not remove disposable plugin {plugin_root}: {exc}"
    if plugin_root.exists():
        return f"disposable plugin cleanup left residue at {plugin_root}"
    return None


def case_passes(should_trigger: bool, selected: int, invalid: int) -> bool:
    if invalid != 0:
        return False
    return ((selected / RUNS_PER_QUERY) >= TRIGGER_THRESHOLD) == should_trigger


def _claude_managed_policy_checks(environment: dict[str, str]) -> tuple[dict[str, bool] | None, str | None]:
    try:
        managed_root = MACOS_MANAGED_ROOT if sys.platform == "darwin" else LINUX_MANAGED_ROOT
        managed_paths = [
            managed_root / "managed-settings.json",
            managed_root / "managed-mcp.json",
            managed_root / "CLAUDE.md",
        ]
        drop_in_root = managed_root / "managed-settings.d"
        if drop_in_root.exists():
            if not drop_in_root.is_dir():
                return None, "Claude managed-settings drop-in path is not a directory"
            managed_paths.extend(sorted(drop_in_root.glob("*.json")))
        preference_check = True
        if sys.platform == "darwin":
            exported = subprocess.run(
                ["/usr/bin/defaults", "export", "com.anthropic.claudecode", "-"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                env=environment,
                shell=False,
                check=False,
            )
            preferences = plistlib.loads(exported.stdout)
            preference_check = exported.returncode == 0 and isinstance(preferences, dict) and not preferences
    except (OSError, subprocess.TimeoutExpired, plistlib.InvalidFileException) as exc:
        return None, f"Claude managed-settings preflight could not inspect local policy: {exc}"
    return {
        "system_files_absent": not any(path.exists() for path in managed_paths),
        "managed_preferences_empty": preference_check,
    }, None


def cli_preflight(executable: str) -> tuple[dict[str, object] | None, str]:
    candidate = shutil.which("claude")
    if candidate is None:
        return None, "Claude CLI disappeared before preflight"
    if candidate != executable:
        return None, "Claude runtime changed before preflight"
    if sys.platform not in {"darwin", "linux"}:
        return None, "Claude qualification requires the audited POSIX managed-settings surface"
    environment = claude_environment()
    try:
        version = subprocess.run(
            [candidate, "--version"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
            shell=False,
            check=False,
        )
        help_result = subprocess.run(
            [candidate, "--help"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
            shell=False,
            check=False,
        )
        doctor = subprocess.run(
            [candidate, "doctor"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            env=environment,
            shell=False,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"Claude preflight could not run: {exc}"
    try:
        version_text = version.stdout.decode("utf-8", errors="strict").strip()
        help_text = help_result.stdout.decode("utf-8", errors="strict")
        doctor_text = doctor.stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        return None, f"Claude preflight output is not UTF-8: {exc}"
    missing = [flag for flag in REQUIRED_FLAGS if flag not in help_text]
    doctor_checks = {
        "running": PINNED_DOCTOR_RUNNING in doctor_text,
        "managed_settings_absent": PINNED_MANAGED_SETTINGS in doctor_text,
        "organization_policy_absent": PINNED_ORGANIZATION_POLICY in doctor_text,
    }
    managed_checks, managed_error = _claude_managed_policy_checks(environment)
    if managed_checks is None:
        return None, str(managed_error)
    if (
        version.returncode != 0
        or help_result.returncode != 0
        or doctor.returncode != 0
        or version_text != PINNED_CLAUDE_VERSION
        or missing
        or not all(doctor_checks.values())
        or not all(managed_checks.values())
    ):
        return None, f"Claude preflight failed; unsupported flags: {', '.join(missing) or 'none'}"
    return {
        "version": version_text,
        "supported_flags": list(REQUIRED_FLAGS),
        "settings_sources": [],
        "managed_settings": "absent",
        "organization_policy": "not-applicable",
        "request_retries": 0,
        "doctor_checks": doctor_checks,
        "managed_checks": managed_checks,
    }, "Claude CLI preflight passed"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill", nargs="?", default="speckit-coach")
    parser.add_argument("--model", default=os.environ.get("EVAL_MODEL", DEFAULT_MODEL))
    parser.add_argument("--evidence-dir", help="Directory for exact per-trial stdout/stderr evidence")
    parser.add_argument("--preflight", action="store_true", help="Validate one selected corpus and CLI without inference")
    parser.add_argument("--timeout", type=int, default=180, help="Per-trial timeout in seconds")
    parser.add_argument("--out", help="Write the opaque result report to this path")
    parser.add_argument("--case-id", help="Run exactly this stable case identity; keeps all three trials")
    parser.add_argument("--no-op-description-file", help="Frozen single-line controlled experiment description")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        eval_file = find_eval_file(args.skill)
        skill_source = find_skill_source(args.skill)
        eval_data, corpus_reason = load_eval_corpus(eval_file)
        if eval_data is None:
            raise ValueError(corpus_reason)
        eval_data = evidence_records.select_case("claude", args.skill, eval_data, args.case_id)
        no_op_description = evidence_records.description_override(args.no_op_description_file, NO_SPECKIT_SKILL_DESCRIPTION)
        description_lines = source_description_lines(skill_source)
        if args.out and Path(args.out).exists():
            raise ValueError("--out already exists; previous reports are immutable")
    except (OSError, UnicodeError, ValueError) as exc:
        eprint(f"ERROR: {exc}")
        return 1
    if args.timeout <= 0:
        eprint("ERROR: --timeout must be positive")
        return 1
    executable = shutil.which("claude")
    if executable is None:
        eprint("ERROR: claude CLI not on PATH")
        return 1

    test_id = uuid.uuid4().hex[:12]
    plugin_name = f"skill-catalog-eval-{test_id}"
    skill_name = f"{args.skill}-eval-{test_id}"
    nonce = f"CLAUDE_SKILL_SELECTED_{test_id}"
    plugin_root = Path(tempfile.mkdtemp(prefix=f"claude-trigger-{args.skill}-"))
    sibling_sources = {sibling.name: sibling / "SKILL.md" for sibling in sibling_skill_dirs(skill_source)}
    exit_code = 1
    evidence_dir = None
    previous_handlers = install_termination_handlers()
    try:
        _skill_dir, expected_skill = stage_measurement_plugin(
            skill_source,
            plugin_root,
            plugin_name,
            skill_name,
            nonce,
            {**sibling_sources, NO_SPECKIT_SKILL_NAME: no_op_description},
        )
        sibling_skills = tuple(
            f"{plugin_name}:{name}"
            for name in sorted({*sibling_sources, NO_SPECKIT_SKILL_NAME})
        )
        mcp_config = plugin_root / "empty-mcp.json"
        write_empty_mcp_config(mcp_config)
        preflight, preflight_reason = cli_preflight(executable)
        if preflight is None:
            raise ValueError(preflight_reason)
        metadata = {
            "trial_timeout_seconds": args.timeout,
            "input_snapshot": experiment_evidence.measurement_snapshot(),
            "replay_context": {"host": "claude", "plugin_name": plugin_name, "plugin_root": str(plugin_root.resolve()),
                               "expected_skill": expected_skill, "nonce": nonce, "requested_model": args.model,
                               "sibling_skills": list(sibling_skills), "source_skill": args.skill,
                               "no_op_description": no_op_description,
                               "staged_skill_bodies": {path.parent.name: path.read_text(encoding="utf-8")
                                   for path in sorted((plugin_root / "skills").glob("*/SKILL.md"))}},
            "no_op_description_sha256": hashlib.sha256(no_op_description.encode()).hexdigest(),
            "skill": args.skill,
            "expected_skill": expected_skill,
            "skill_source": str(skill_source),
            "skill_source_sha256": hashlib.sha256(skill_source.read_bytes()).hexdigest(),
            "source_description_sha256": hashlib.sha256("\n".join(description_lines).encode("utf-8")).hexdigest(),
            "eval_file": str(eval_file),
            "eval_sha256": hashlib.sha256(eval_file.read_bytes()).hexdigest(),
            "sibling_skills": list(sibling_skills),
            "sibling_description_sha256": {
                name: hashlib.sha256("\n".join(source_description_lines(path)).encode("utf-8")).hexdigest()
                for name, path in sorted(sibling_sources.items())
            },
            "case_count": len(eval_data),
            "runs_per_query": RUNS_PER_QUERY,
            "trigger_threshold": TRIGGER_THRESHOLD,
            "requested_model": args.model,
            "qualification_eligible": args.model == DEFAULT_MODEL,
            "preflight": preflight,
        }
        if args.preflight:
            print(json.dumps({"preflight": metadata}, indent=2))
            exit_code = 0
        else:
            if args.evidence_dir:
                requested_dir = Path(args.evidence_dir).resolve()
                requested_dir.mkdir(parents=True, exist_ok=False)
                evidence_dir = requested_dir
            else:
                evidence_dir = Path(tempfile.mkdtemp(prefix=f"claude-trigger-evidence-{args.skill}-"))

            batch = evidence_records.TrialBatch(
                "claude", args.skill, evidence_dir, RUNS_PER_QUERY, TRIGGER_THRESHOLD,
                qualification_eligible=args.model == DEFAULT_MODEL,
            )
            evidence_records.write_json_once(evidence_dir / "replay-context.json", metadata["replay_context"])
            results, stop_exit = evidence_records.run_trials(
                batch, eval_data,
                lambda query, execution: run_claude_query(
                    executable, plugin_root, mcp_config, query, args.model, args.timeout,
                    expected_skill=expected_skill, sibling_skills=sibling_skills, process_evidence=execution,
                ),
                lambda stdout: inspect_claude_stream(
                    stdout, plugin_name, plugin_root, expected_skill, nonce, args.model, frozenset(sibling_skills),
                ),
                lambda case, trial, stdout, stderr: retain_trial_evidence(evidence_dir, case, trial, stdout, stderr),
            )
            if experiment_evidence.measurement_snapshot() != metadata["input_snapshot"]:
                raise ValueError("public measurement inputs changed during native execution")
            passed = sum(result["pass"] is True for result in results)
            failed = sum(result["pass"] is False for result in results)
            if stop_exit is not None and stop_exit >= 128:
                eprint(f"Termination requested by signal {stop_exit - 128}; terminating owned child and cleaning temporary plugin.")

            resolved = [
                trial.get("resolved_model")
                for result in results
                for trial in result["selection_evidence"]
            ]
            qualification_eligible = (
                args.model == DEFAULT_MODEL
                and all(result["status"] == "complete" for result in results)
                and all(
                    trial["qualification_eligible"] is True
                    for result in results
                    for trial in result["selection_evidence"]
                )
            )
            report = {
                "metadata": metadata,
                "summary": {
                    "total": len(eval_data),
                    "passed": passed,
                    "failed": failed,
                    "complete": all(result["status"] == "complete" for result in results),
                    "not_run": sum(result["status"] == "not_run" for result in results),
                    "requested_model": args.model,
                    "qualification_eligible": qualification_eligible,
                    "resolved_model": resolved[0]
                    if resolved
                    and all(isinstance(model, str) and model and model == resolved[0] for model in resolved)
                    else None,
                },
                "results": results,
            }
            if args.out:
                evidence_records.write_json_once(Path(args.out), report)
            print(json.dumps(report, indent=2))
            exit_code = stop_exit if stop_exit is not None else 0 if failed == 0 else 1
    except (TerminationRequested, KeyboardInterrupt) as exc:
        signum = exc.signum if isinstance(exc, TerminationRequested) else signal.SIGINT
        exit_code = 128 + signum
        eprint(f"Termination requested by signal {signum}; terminating owned child and cleaning temporary plugin.")
    except (OSError, ValueError) as exc:
        eprint(f"ERROR: {exc}")
        exit_code = 1
    finally:
        cleanup_error = remove_plugin_root(plugin_root)
        if cleanup_error:
            eprint(f"ERROR: {cleanup_error}")
            exit_code = 2
        restore_termination_handlers(previous_handlers)
        if evidence_dir is not None:
            try:
                evidence_records.retain_cleanup_receipt(evidence_dir, plugin_root, exit_code, cleanup_error)
            except OSError as exc:
                eprint(f"ERROR: cannot retain workspace cleanup receipt: {exc}")
                exit_code = 2
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
