#!/usr/bin/env python3
"""Run isolated Claude Layer 2 skill-selection evaluations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import uuid


SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = (SCRIPT_DIR / "../../../speckit-pro").resolve()
DEFAULT_MODEL = "sonnet"
RUNS_PER_QUERY = 3
TRIGGER_THRESHOLD = 0.5
REQUIRED_FLAGS = (
    "--restricted",
    "--plugin-dir",
    "--strict-mcp-config",
    "--mcp-config",
    "--tools",
    "--allowedTools",
    "--output-format",
    "--verbose",
    "--no-session-persistence",
)
ACTIVE_CHILD: subprocess.Popen[bytes] | None = None


class TerminationRequested(Exception):
    """Raised after terminating the owned child so local cleanup can run."""

    def __init__(self, signum: int) -> None:
        super().__init__(f"termination requested by signal {signum}")
        self.signum = signum


def eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


def load_eval_corpus(path: Path) -> tuple[list[dict[str, object]] | None, str]:
    """Validate the selected corpus before staging or launching Claude."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, f"could not read eval file: {exc}"
    if not isinstance(value, list):
        return None, "eval file must contain a JSON list"
    if not value:
        return None, "eval file must contain at least one case"
    seen_queries: set[str] = set()
    for index, entry in enumerate(value, start=1):
        if not isinstance(entry, dict):
            return None, f"eval case {index} must be an object"
        query = entry.get("query")
        should_trigger = entry.get("should_trigger")
        if not isinstance(query, str) or not query.strip() or not isinstance(should_trigger, bool):
            return None, f"eval case {index} requires a non-empty query and boolean should_trigger"
        if query in seen_queries:
            return None, f"eval case {index} duplicates query {query!r}"
        seen_queries.add(query)
    return value, "valid eval corpus"


def available_evals(eval_dir: Path) -> list[str]:
    return [path.name.removesuffix("-trigger.json") for path in sorted(eval_dir.glob("*-trigger.json"))]


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


def stage_measurement_plugin(
    source: Path,
    plugin_root: Path,
    plugin_name: str,
    skill_name: str,
    nonce: str,
) -> tuple[Path, str]:
    """Stage only the exact source description plus a minimal measurement body."""
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
                "When this skill is selected, respond with this nonce before any other text:",
                "",
                nonce,
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
    return skill_dir, f"{plugin_name}:{skill_name}"


def write_empty_mcp_config(path: Path) -> None:
    path.write_text(json.dumps({"mcpServers": {}}, indent=2) + "\n", encoding="utf-8")


def stream_content(event: dict[str, object]) -> list[dict[str, object]]:
    message = event.get("message")
    if not isinstance(message, dict):
        return []
    content = message.get("content")
    if not isinstance(content, list):
        return []
    return [block for block in content if isinstance(block, dict)]


def inspect_claude_stream(
    output: bytes | str,
    plugin_name: str,
    plugin_root: Path,
    expected_skill: str,
    nonce: str,
    requested_model: str,
) -> dict[str, object]:
    """Parse completed stream events and return polarity-independent selection evidence."""
    try:
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="strict")
        events: list[dict[str, object]] = []
        for line in output.splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError("event is not an object")
            events.append(event)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return {"valid": False, "selected": False, "reason": f"invalid stream JSONL: {exc}"}

    results = [(index, event) for index, event in enumerate(events) if event.get("type") == "result"]
    if len(results) != 1 or results[0][0] != len(events) - 1:
        return {"valid": False, "selected": False, "reason": "missing or ambiguous terminal result"}
    result_index, result = results[0]
    if (
        result.get("subtype") != "success"
        or result.get("is_error") is not False
        or result.get("permission_denials") not in (None, [])
    ):
        return {"valid": False, "selected": False, "reason": "Claude terminal result was not successful"}

    if any(
        event.get("type") == "permission_denied"
        or event.get("subtype") in {"permission_denied", "api_retry"}
        or event.get("is_error") is True
        for event in events[:result_index]
    ):
        return {"valid": False, "selected": False, "reason": "Claude reported a denied or failed event"}

    init_events = [
        (index, event)
        for index, event in enumerate(events[:result_index])
        if event.get("type") == "system" and event.get("subtype") == "init"
    ]
    if len(init_events) != 1:
        return {"valid": False, "selected": False, "reason": "missing or ambiguous system init"}
    init_index, init = init_events[0]
    tools = init.get("tools")
    if (
        not isinstance(tools, list)
        or any(not isinstance(tool, str) for tool in tools)
        or len(tools) != len(set(tools))
        or set(tools) not in ({"Skill"}, {"Skill", "EndConversation"})
    ):
        return {"valid": False, "selected": False, "reason": "Skill-only tool inventory was not honored"}
    plugins = init.get("plugins")
    if not isinstance(plugins, list):
        return {"valid": False, "selected": False, "reason": "system init omitted plugin inventory"}
    expected_root = plugin_root.resolve()
    matches = [
        plugin
        for plugin in plugins
        if isinstance(plugin, dict)
        and plugin.get("name") == plugin_name
        and isinstance(plugin.get("path"), str)
        and Path(str(plugin["path"])).resolve() == expected_root
    ]
    plugin_errors = init.get("plugin_errors", [])
    subject_errors = [
        error
        for error in plugin_errors
        if isinstance(error, dict) and error.get("plugin") == plugin_name
    ] if isinstance(plugin_errors, list) else [plugin_errors]
    if len(matches) != 1 or subject_errors:
        return {"valid": False, "selected": False, "reason": "staged plugin was not loaded exactly once"}
    if init.get("mcp_servers", []) != [] or init.get("mcp_server_errors", []) != []:
        return {"valid": False, "selected": False, "reason": "strict empty MCP inventory was not honored"}

    assistant_events = [
        (index, event)
        for index, event in enumerate(events[:result_index])
        if event.get("type") == "assistant" and stream_content(event)
    ]
    if not assistant_events:
        return {"valid": False, "selected": False, "reason": "completed run omitted an assistant response"}

    skill_uses: list[tuple[int, dict[str, object]]] = []
    nonce_locations: list[dict[str, object]] = []
    for event_index, event in assistant_events:
        for block_index, block in enumerate(stream_content(event)):
            if block.get("type") == "tool_use" and block.get("name") == "Skill":
                skill_uses.append((event_index, block))
            if block.get("type") == "text" and isinstance(block.get("text"), str) and nonce in str(block["text"]):
                nonce_locations.append({"event": event_index, "block": block_index})

    intended: list[tuple[int, dict[str, object]]] = []
    competing: list[object] = []
    malformed = False
    for event_index, block in skill_uses:
        tool_id = block.get("id")
        tool_input = block.get("input")
        skill_value = tool_input.get("skill") if isinstance(tool_input, dict) else None
        if not isinstance(tool_id, str) or not tool_id or not isinstance(skill_value, str) or not skill_value:
            malformed = True
        elif skill_value == expected_skill:
            intended.append((event_index, block))
        else:
            competing.append(skill_value)
    if malformed or competing or len(intended) > 1:
        return {
            "valid": False,
            "selected": False,
            "reason": "malformed, competing, or ambiguous Skill selection",
            "nonce_locations": nonce_locations,
        }

    selected = len(intended) == 1
    selected_id: str | None = None
    if selected:
        use_index, use = intended[0]
        if use_index <= init_index:
            return {"valid": False, "selected": False, "reason": "Skill selection preceded system init"}
        selected_id = str(use["id"])
        results_for_use: list[dict[str, object]] = []
        for event in events[use_index + 1 : result_index]:
            if event.get("type") != "user":
                continue
            for block in stream_content(event):
                if block.get("type") == "tool_result" and block.get("tool_use_id") == selected_id:
                    results_for_use.append(block)
        if len(results_for_use) != 1 or results_for_use[0].get("is_error") is True:
            return {
                "valid": False,
                "selected": False,
                "reason": "selected Skill omitted its single successful tool result",
                "nonce_locations": nonce_locations,
            }

    resolved_model = init.get("model") if isinstance(init.get("model"), str) and init.get("model") else None
    return {
        "valid": True,
        "selected": selected,
        "selected_skill": expected_skill if selected else None,
        "selected_tool_use_id": selected_id,
        "nonce_locations": nonce_locations,
        "requested_model": requested_model,
        "resolved_model": resolved_model,
        "reason": "exact completed Skill selection" if selected else "no Skill selection",
    }


def retain_trial_evidence(
    evidence_dir: Path,
    case_number: int,
    trial_number: int,
    stdout: bytes,
    stderr: bytes,
) -> dict[str, str]:
    stem = f"case-{case_number:03d}-trial-{trial_number:02d}"
    stdout_path = evidence_dir / f"{stem}.jsonl"
    stderr_path = evidence_dir / f"{stem}.stderr.log"
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    return {
        "stdout_path": str(stdout_path.resolve()),
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_path": str(stderr_path.resolve()),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
    }


def terminate_child(child: subprocess.Popen[bytes] | None, signum: int = signal.SIGTERM) -> None:
    if child is None or child.poll() is not None:
        return
    try:
        if os.name != "nt":
            os.killpg(child.pid, signum)
        else:
            child.terminate()
    except (OSError, ProcessLookupError):
        pass


def handle_termination(signum: int, _frame: object) -> None:
    terminate_child(ACTIVE_CHILD, signum)
    raise TerminationRequested(signum)


def install_termination_handlers() -> dict[int, object]:
    previous: dict[int, object] = {}
    for name in ("SIGHUP", "SIGTERM"):
        signum = getattr(signal, name, None)
        if not isinstance(signum, int):
            continue
        try:
            previous[signum] = signal.getsignal(signum)
            signal.signal(signum, handle_termination)
        except (OSError, ValueError):
            previous.pop(signum, None)
    return previous


def restore_termination_handlers(previous: dict[int, object]) -> None:
    for signum, handler in previous.items():
        try:
            signal.signal(signum, handler)
        except (OSError, ValueError):
            pass


def run_claude_query(
    executable: str,
    plugin_root: Path,
    mcp_config: Path,
    query: str,
    model: str,
    timeout: int,
) -> tuple[int, bytes, bytes, bool]:
    global ACTIVE_CHILD
    candidate = shutil.which("claude")
    if candidate is None:
        raise OSError("Claude CLI disappeared after initial resolution")
    if candidate != executable:
        raise ValueError("Claude runtime changed after initial resolution")
    command = [
        candidate,
        "--restricted",
        "--plugin-dir", str(plugin_root),
        "--strict-mcp-config",
        "--mcp-config", str(mcp_config),
        "--tools", "Skill",
        "--allowedTools", "Skill",
        "-p", query,
        "--model", model,
        "--output-format", "stream-json",
        "--verbose",
        "--no-session-persistence",
    ]
    child = subprocess.Popen(
        command,
        cwd=plugin_root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy(),
        shell=False,
        start_new_session=os.name != "nt",
    )
    ACTIVE_CHILD = child
    try:
        try:
            stdout, stderr = child.communicate(timeout=timeout)
            return int(child.returncode), stdout, stderr, False
        except subprocess.TimeoutExpired as exc:
            terminate_child(child, signal.SIGKILL)
            stdout, stderr = child.communicate()
            if not stdout and isinstance(exc.output, bytes):
                stdout = exc.output
            if not stderr and isinstance(exc.stderr, bytes):
                stderr = exc.stderr
            return -1, stdout, stderr, True
        except TerminationRequested:
            terminate_child(child)
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                terminate_child(child, signal.SIGKILL)
                child.wait(timeout=5)
            raise
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


def cli_preflight(executable: str) -> tuple[dict[str, object] | None, str]:
    candidate = shutil.which("claude")
    if candidate is None:
        return None, "Claude CLI disappeared before preflight"
    if candidate != executable:
        return None, "Claude runtime changed before preflight"
    version = subprocess.run(
        [candidate, "--version"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    help_result = subprocess.run(
        [candidate, "--help"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    try:
        version_text = version.stdout.decode("utf-8", errors="strict").strip()
        help_text = help_result.stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        return None, f"Claude preflight output is not UTF-8: {exc}"
    missing = [flag for flag in REQUIRED_FLAGS if flag not in help_text]
    if version.returncode != 0 or help_result.returncode != 0 or missing:
        return None, f"Claude preflight failed; unsupported flags: {', '.join(missing) or 'none'}"
    return {"version": version_text, "supported_flags": list(REQUIRED_FLAGS)}, "Claude CLI preflight passed"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill", nargs="?", default="speckit-coach")
    parser.add_argument("--model", default=os.environ.get("EVAL_MODEL", DEFAULT_MODEL))
    parser.add_argument("--evidence-dir", help="Directory for exact per-trial stdout/stderr evidence")
    parser.add_argument("--preflight", action="store_true", help="Validate one selected corpus and CLI without inference")
    parser.add_argument("--timeout", type=int, default=180, help="Per-trial timeout in seconds")
    parser.add_argument("--out", help="Write the opaque result report to this path")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        eval_file = find_eval_file(args.skill)
        skill_source = find_skill_source(args.skill)
        eval_data, corpus_reason = load_eval_corpus(eval_file)
        if eval_data is None:
            raise ValueError(corpus_reason)
        description_lines = source_description_lines(skill_source)
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
    plugin_name = f"speckit-pro-eval-{test_id}"
    skill_name = f"{args.skill}-eval-{test_id}"
    nonce = f"CLAUDE_SKILL_SELECTED_{test_id}"
    plugin_root = Path(tempfile.mkdtemp(prefix=f"claude-trigger-{args.skill}-"))
    exit_code = 1
    previous_handlers = install_termination_handlers()
    try:
        _skill_dir, expected_skill = stage_measurement_plugin(
            skill_source,
            plugin_root,
            plugin_name,
            skill_name,
            nonce,
        )
        mcp_config = plugin_root / "empty-mcp.json"
        write_empty_mcp_config(mcp_config)
        preflight, preflight_reason = cli_preflight(executable)
        if preflight is None:
            raise ValueError(preflight_reason)
        metadata = {
            "skill": args.skill,
            "expected_skill": expected_skill,
            "skill_source": str(skill_source),
            "skill_source_sha256": hashlib.sha256(skill_source.read_bytes()).hexdigest(),
            "source_description_sha256": hashlib.sha256("\n".join(description_lines).encode("utf-8")).hexdigest(),
            "eval_file": str(eval_file),
            "eval_sha256": hashlib.sha256(eval_file.read_bytes()).hexdigest(),
            "case_count": len(eval_data),
            "runs_per_query": RUNS_PER_QUERY,
            "trigger_threshold": TRIGGER_THRESHOLD,
            "requested_model": args.model,
            "preflight": preflight,
        }
        if args.preflight:
            print(json.dumps({"preflight": metadata}, indent=2))
            exit_code = 0
        else:
            if args.evidence_dir:
                evidence_dir = Path(args.evidence_dir).resolve()
                evidence_dir.mkdir(parents=True, exist_ok=False)
            else:
                evidence_dir = Path(tempfile.mkdtemp(prefix=f"claude-trigger-evidence-{args.skill}-"))

            results: list[dict[str, object]] = []
            passed = failed = 0
            for case_number, entry in enumerate(eval_data, start=1):
                selected = invalid = 0
                trial_evidence: list[dict[str, object]] = []
                for trial_number in range(1, RUNS_PER_QUERY + 1):
                    rc, stdout, stderr, timed_out = run_claude_query(
                        executable,
                        plugin_root,
                        mcp_config,
                        str(entry["query"]),
                        args.model,
                        args.timeout,
                    )
                    raw = retain_trial_evidence(evidence_dir, case_number, trial_number, stdout, stderr)
                    parsed = inspect_claude_stream(
                        stdout,
                        plugin_name,
                        plugin_root,
                        expected_skill,
                        nonce,
                        args.model,
                    )
                    valid = rc == 0 and not timed_out and bool(parsed.get("valid"))
                    if not valid:
                        invalid += 1
                    elif parsed.get("selected") is True:
                        selected += 1
                    trial_evidence.append({**parsed, **raw, "exit_code": rc, "timed_out": timed_out})
                should_trigger = bool(entry["should_trigger"])
                passed_case = case_passes(should_trigger, selected, invalid)
                passed += int(passed_case)
                failed += int(not passed_case)
                results.append(
                    {
                        "query": entry["query"],
                        "should_trigger": should_trigger,
                        "selected": selected,
                        "runs": RUNS_PER_QUERY,
                        "trigger_rate": round(selected / RUNS_PER_QUERY, 3),
                        "invalid_runs": invalid,
                        "pass": passed_case,
                        "selection_evidence": trial_evidence,
                    }
                )

            resolved = [
                trial.get("resolved_model")
                for result in results
                for trial in result["selection_evidence"]
                if isinstance(trial.get("resolved_model"), str)
            ]
            report = {
                "metadata": metadata,
                "summary": {
                    "total": len(eval_data),
                    "passed": passed,
                    "failed": failed,
                    "requested_model": args.model,
                    "resolved_model": resolved[0] if resolved and all(model == resolved[0] for model in resolved) else None,
                },
                "results": results,
            }
            if args.out:
                Path(args.out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(report, indent=2))
            exit_code = 0 if failed == 0 else 1
    except TerminationRequested as exc:
        exit_code = 128 + exc.signum
        eprint(f"Termination requested by signal {exc.signum}; terminating owned child and cleaning temporary plugin.")
    except (OSError, ValueError) as exc:
        eprint(f"ERROR: {exc}")
        exit_code = 1
    finally:
        cleanup_error = remove_plugin_root(plugin_root)
        if cleanup_error:
            eprint(f"ERROR: {cleanup_error}")
            exit_code = 2
        restore_termination_handlers(previous_handlers)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
