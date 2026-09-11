#!/usr/bin/env python3
"""Run isolated Claude Layer 2 skill-selection evaluations."""

from __future__ import annotations

import argparse
import errno
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
import time
import uuid


SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_LIB = SCRIPT_DIR.parent / "lib"
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))
import trigger_process as processes  # noqa: E402
import trigger_evidence as evidence_records  # noqa: E402

PLUGIN_ROOT = (SCRIPT_DIR / "../../../speckit-pro").resolve()
DEFAULT_MODEL = "sonnet"
RUNS_PER_QUERY = 3
TRIGGER_THRESHOLD = 0.5
NO_SPECKIT_SKILL_NAME = "no-speckit-skill"
NO_SPECKIT_SKILL_DESCRIPTION = (
    "Use when no available SpecKit skill covers the request, including ordinary coding, testing, tooling, or "
    "repository work and host-specific SpecKit operations whose matching skill is absent from the current catalog, "
    "such as installing Codex subagents when no agent-install skill is available or running the plan stage for an "
    "already-existing spec or populated workflow when no planning skill is available. Reply that no available "
    "SpecKit skill applies and stop."
)
MEASUREMENT_STUB_SENTENCE = (
    "This skill is a measurement stub used by the repository's skill-selection test suite. It is not a real "
    "workflow and contains no injected instruction."
)
REQUIRED_FLAGS = (
    "--restricted",
    "--plugin-dir",
    "--strict-mcp-config",
    "--mcp-config",
    "--tools",
    "--allowedTools",
    "--settings",
    "--permission-mode",
    "--permission-prompts",
    "--output-format",
    "--verbose",
    "--no-session-persistence",
)
ACTIVE_CHILD: subprocess.Popen[bytes] | None = None
CLEANUP_TIMEOUT = 5
DESCENDANT_EXIT_GRACE = 0.2


ClaudeQueryError = processes.QueryError


TerminationRequested = processes.TerminationRequested


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


SKILL_ROOT_NAMES = frozenset({"skills", "codex-skills"})


def sibling_skill_dirs(source: Path) -> list[Path]:
    """List sibling skill directories beside ``source``'s skill directory.

    Only a plugin skills root (``skills`` or ``codex-skills``) is walked; a
    source staged elsewhere has no siblings. Entries that cannot be inspected
    are skipped, because shared temp roots hold directories owned by others.
    """
    root = source.parent.parent
    if root.name not in SKILL_ROOT_NAMES:
        return []
    siblings: list[Path] = []
    for sibling in sorted(root.iterdir(), key=lambda path: path.name):
        if sibling == source.parent:
            continue
        try:
            if sibling.is_dir() and (sibling / "SKILL.md").is_file():
                siblings.append(sibling)
        except OSError:
            continue
    return siblings


def stage_measurement_plugin(
    source: Path,
    plugin_root: Path,
    plugin_name: str,
    skill_name: str,
    nonce: str,
    siblings: dict[str, Path] | None = None,
) -> tuple[Path, str]:
    """Stage only the exact source description plus a minimal measurement body.

    ``siblings`` maps each sibling skill name to its source SKILL.md. Siblings are
    staged with their exact descriptions and a minimal body carrying no nonce, so a
    should-not-trigger query has its real destination in the catalog.
    """
    staged_siblings = {
        sibling_name: source_description_lines(sibling_source)
        for sibling_name, sibling_source in (siblings or {}).items()
    }
    if NO_SPECKIT_SKILL_NAME in staged_siblings:
        raise ValueError(f"reserved sibling skill name: {NO_SPECKIT_SKILL_NAME}")
    staged_siblings[NO_SPECKIT_SKILL_NAME] = [f"description: {NO_SPECKIT_SKILL_DESCRIPTION}"]
    for sibling_name, description_lines in sorted(staged_siblings.items()):
        if sibling_name == skill_name:
            raise ValueError("sibling skill name collides with the measured skill")
        sibling_dir = plugin_root / "skills" / sibling_name
        sibling_dir.mkdir(parents=True)
        (sibling_dir / "SKILL.md").write_text(
            "\n".join(
                [
                    "---",
                    f"name: {sibling_name}",
                    "\n".join(description_lines),
                    "---",
                    "",
                    "This sibling skill is part of a selection check. If it is selected,",
                    "say so in one line and stop.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
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


def skill_results_error(
    events: list[dict[str, object]], uses: list[tuple[int, dict[str, object]]],
    init_index: int, result_index: int,
) -> str | None:
    """Require each observed Skill call to finish successfully in the same run."""
    results: dict[str, list[tuple[int, dict[str, object]]]] = {}
    for index, event in enumerate(events[:result_index]):
        if event.get("type") == "user":
            for block in stream_content(event):
                if block.get("type") == "tool_result":
                    identifier = block.get("tool_use_id")
                    if not isinstance(identifier, str) or not identifier:
                        return "malformed Skill tool result"
                    results.setdefault(identifier, []).append((index, block))
    identifiers = [use.get("id") for _, use in uses]
    if any(not isinstance(identifier, str) or not identifier for identifier in identifiers):
        return "malformed Skill tool use identity"
    if len(set(identifiers)) != len(identifiers) or set(results) != set(identifiers):
        return "missing, orphaned, or duplicate Skill result identity"
    for use_index, use in uses:
        if use_index <= init_index:
            return "Skill selection preceded system init"
        matching = results[str(use["id"])]
        if len(matching) != 1:
            return "Skill omitted its single successful tool result"
        result_position, result = matching[0]
        if result_position <= use_index or (result.get("is_error") is not None and result.get("is_error") is not False):
            return "Skill result was out of order or unsuccessful"
    return None


def claude_model_evidence(events: list[dict[str, object]], init: dict[str, object], requested: str) -> dict[str, object]:
    """Check reported identities; aliases remain explicitly weaker than exact pins."""
    models = [init.get("model")]
    for event in events:
        message = event.get("message")
        if event.get("type") == "assistant" and isinstance(message, dict) and "model" in message:
            models.append(message["model"])
    known = {model for model in models if isinstance(model, str) and model}
    resolved = init.get("model") if isinstance(init.get("model"), str) and init["model"] else None
    conflict = len(known) > 1 or any(model is not None and (not isinstance(model, str) or not model) for model in models)
    alias = requested in {"sonnet", "opus", "haiku"}
    if resolved is not None:
        conflict |= not (resolved.startswith(f"claude-{requested}-") if alias else resolved == requested)
    return {
        "requested_model": requested,
        "resolved_model": resolved,
        "model_identity_check": "conflict" if conflict else "unavailable" if resolved is None else "alias" if alias else "exact",
    }


def inspect_claude_stream(
    output: bytes | str,
    plugin_name: str,
    plugin_root: Path,
    expected_skill: str,
    nonce: str,
    requested_model: str,
    sibling_skills: frozenset[str] | None = None,
) -> dict[str, object]:
    """Parse completed stream events and return polarity-independent selection evidence.

    A completed selection of a staged sibling is a valid non-selection; any other
    competing skill stays invalid.
    """
    sibling_skills = frozenset(
        {*frozenset(sibling_skills or ()), f"{plugin_name}:{NO_SPECKIT_SKILL_NAME}"}
    )
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
    staged_inventory = sorted({expected_skill, *sibling_skills})
    inventory = init.get("skills")
    if not isinstance(inventory, list) or sorted(inventory) != staged_inventory or len(inventory) != len(staged_inventory):
        return {"valid": False, "selected": False, "reason": "staged skill inventory was not honored"}
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
            if block.get("type") == "tool_use" and block.get("name") not in tools:
                return {"valid": False, "selected": False, "reason": "undeclared tool activity was observed"}
            if block.get("type") == "tool_use" and block.get("name") == "Skill":
                if event.get("parent_tool_use_id") is not None:
                    return {"valid": False, "selected": False, "reason": "nested Skill execution was observed"}
                skill_uses.append((event_index, block))
            if block.get("type") == "text" and isinstance(block.get("text"), str) and nonce in str(block["text"]):
                nonce_locations.append({"event": event_index, "block": block_index})

    intended: list[tuple[int, dict[str, object]]] = []
    competing: list[object] = []
    sibling_selections: list[str] = []
    malformed = False
    # The host resolves an unqualified skill name to the one staged plugin, so
    # `demo-eval-<id>` selects the same skill as `<plugin>:demo-eval-<id>`.
    qualified = {name.partition(":")[2]: name for name in staged_inventory if ":" in name}
    for event_index, block in skill_uses:
        tool_id = block.get("id")
        tool_input = block.get("input")
        skill_value = tool_input.get("skill") if isinstance(tool_input, dict) else None
        if not isinstance(tool_id, str) or not tool_id or not isinstance(skill_value, str) or not skill_value:
            malformed = True
            continue
        skill_value = qualified.get(skill_value, skill_value)
        if skill_value == expected_skill:
            intended.append((event_index, block))
        elif skill_value in sibling_skills:
            sibling_selections.append(skill_value)
        else:
            competing.append(skill_value)
    if malformed or competing or len(intended) > 1 or (intended and sibling_selections):
        return {
            "valid": False,
            "selected": False,
            "reason": "malformed, competing, or ambiguous Skill selection",
            "nonce_locations": nonce_locations,
        }

    completion_error = skill_results_error(events, skill_uses, init_index, result_index)
    if completion_error:
        return {"valid": False, "selected": False, "reason": completion_error, "nonce_locations": nonce_locations}
    model_evidence = claude_model_evidence(events, init, requested_model)
    if model_evidence["model_identity_check"] == "conflict":
        return {"valid": False, "selected": False, "reason": "Claude reported a conflicting model identity", **model_evidence}
    selected = len(intended) == 1
    selected_id = str(intended[0][1]["id"]) if selected else None
    return {
        "valid": True,
        "selected": selected,
        "selected_skill": expected_skill if selected else None,
        "selected_tool_use_id": selected_id,
        "nonce_locations": nonce_locations,
        "sibling_selections": sibling_selections,
        **model_evidence,
        "reason": (
            "exact completed Skill selection" if selected
            else "sibling Skill selection" if sibling_selections
            else "no Skill selection"
        ),
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
    with stdout_path.open("xb") as stream:
        stream.write(stdout)
    with stderr_path.open("xb") as stream:
        stream.write(stderr)
    return {
        "stdout_path": str(stdout_path.resolve()),
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_path": str(stderr_path.resolve()),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
    }


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
        "--verbose",
        "--no-session-persistence",
    ]
    environment = os.environ.copy()
    environment["DISABLE_AUTOUPDATER"] = "1"
    environment["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"
    environment.pop("FORCE_AUTOUPDATE_PLUGINS", None)
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
            sibling_sources,
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
            "qualification_eligible": False,
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

            batch = evidence_records.TrialBatch("claude", args.skill, evidence_dir, RUNS_PER_QUERY, TRIGGER_THRESHOLD)
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
            passed = sum(result["pass"] is True for result in results)
            failed = sum(result["pass"] is False for result in results)
            if stop_exit is not None and stop_exit >= 128:
                eprint(f"Termination requested by signal {stop_exit - 128}; terminating owned child and cleaning temporary plugin.")

            resolved = [
                trial.get("resolved_model")
                for result in results
                for trial in result["selection_evidence"]
            ]
            report = {
                "metadata": metadata,
                "summary": {
                    "total": len(eval_data),
                    "passed": passed,
                    "failed": failed,
                    "complete": all(result["status"] == "complete" for result in results),
                    "not_run": sum(result["status"] == "not_run" for result in results),
                    "requested_model": args.model,
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
