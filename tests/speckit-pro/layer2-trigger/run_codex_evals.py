#!/usr/bin/env python3
"""Run Layer 2 trigger evals against a Codex skill via the codex CLI.

Mirrors skill-creator's run_eval.py for Claude. Stages the skill into a
disposable repository with a marker injected into the body, runs each query
through `codex` non-interactively, validates the JSONL lifecycle and exact
marker, then scores trigger/no-trigger correctness against the eval fixture.

Subprocess invocations use `subprocess.run` with a list argument (no shell
involvement), so query strings are passed directly as argv entries and
cannot be interpreted as shell metacharacters.

Usage:
  run_codex_evals.py <skill> [--runs N] [--limit N] [--reasoning EFFORT]
                              [--model MODEL] [--threshold 0.5]

Examples:
  # Smoke test: 3 queries, 1 run each, low reasoning
  run_codex_evals.py grill-me --limit 3 --runs 1 --reasoning low

  # Full eval (slow, costs LLM tokens)
  run_codex_evals.py speckit-coach --runs 3
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid


# Tests live at <repo>/tests/speckit-pro/; the plugin is the sibling <repo>/speckit-pro/.
TESTS_ROOT = pathlib.Path(__file__).resolve().parents[1]      # <repo>/tests/speckit-pro
PLUGIN_ROOT = TESTS_ROOT.parents[1] / "speckit-pro"           # <repo>/speckit-pro
DEFAULT_REASONING_EFFORT = "low"
DEFAULT_MODEL = "gpt-5.6-sol"
DISABLED_FEATURES = (
    "plugins", "apps", "browser_use", "computer_use", "hooks",
    "skill_mcp_dependency_install", "memories",
)
MARKER_PATTERN = re.compile(r"CODEX_SKILL_FIRED:[A-Za-z0-9_-]+")
SKILL_CATALOG_WARNINGS = (
    "Skill descriptions were shortened to fit the skills context budget.",
    "Exceeded skills context budget.",
)


def load_eval_corpus(path: pathlib.Path) -> tuple[list[dict[str, object]] | None, str]:
    """Load a complete trigger corpus before any provider subprocess can run."""
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


def find_eval_file(skill: str) -> pathlib.Path:
    codex_specific = TESTS_ROOT / "layer2-trigger/codex-evals" / f"{skill}-trigger.json"
    shared = TESTS_ROOT / "layer2-trigger/evals" / f"{skill}-trigger.json"
    if codex_specific.exists():
        return codex_specific
    if shared.exists():
        return shared
    sys.exit(f"ERROR: no eval file for skill '{skill}' (tried {codex_specific}, {shared})")


def find_skill_source(skill: str) -> pathlib.Path:
    p = PLUGIN_ROOT / "codex-skills" / skill / "SKILL.md"
    if not p.exists():
        sys.exit(f"ERROR: codex skill not found at {p}")
    return p


def stage_skill_with_marker(src: pathlib.Path, dst_dir: pathlib.Path, new_name: str, marker: str) -> None:
    """Copy SKILL.md to dst_dir, rename it to new_name, prepend a marker requirement to the body."""
    text = src.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        sys.exit(f"ERROR: no YAML frontmatter found in {src}")
    fm_body, skill_body = m.group(1), m.group(2)

    fm_lines = [
        f"name: {new_name}" if ln.startswith("name:") else ln
        for ln in fm_body.split("\n")
    ]
    fm = "\n".join(fm_lines)

    marker_block = (
        "## IMPORTANT EVAL MARKER\n\n"
        "When this skill is invoked, your VERY FIRST action MUST be to print\n"
        "this exact line and nothing else before it:\n\n"
        f"    {marker}\n\n"
        "After printing the marker, proceed normally with the skill below.\n\n"
        "---\n\n"
    )

    dst_dir.mkdir(parents=True, exist_ok=True)
    (dst_dir / "SKILL.md").write_text(f"---\n{fm}\n---\n\n{marker_block}{skill_body}")


def stage_repository_skill(
    src: pathlib.Path,
    workspace: pathlib.Path,
    new_name: str,
    marker: str,
) -> pathlib.Path:
    """Stage one uniquely named skill at Codex's documented repository scope."""
    destination = workspace / ".agents" / "skills" / new_name
    stage_skill_with_marker(src, destination, new_name, marker)
    return destination


def source_skill_description(skill_file: pathlib.Path) -> str:
    """Return the model-visible YAML description for supported repository skills."""
    lines = skill_file.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"source skill has no YAML frontmatter: {skill_file}")
    for index, line in enumerate(lines[1:], start=1):
        if line == "---":
            break
        if not line.startswith("description:"):
            continue
        value = line.removeprefix("description:").strip()
        if value in {">", ">-", "|", "|-"}:
            block: list[str] = []
            for continuation in lines[index + 1 :]:
                if continuation == "":
                    block.append("")
                    continue
                if not continuation.startswith((" ", "\t")):
                    break
                block.append(continuation.strip())
            description = (
                " ".join(part for part in block if part)
                if value.startswith(">")
                else "\n".join(block)
            )
        elif len(value) >= 2 and value[0] == value[-1] == '"':
            try:
                description = json.loads(value)
            except json.JSONDecodeError as exc:
                raise ValueError(f"source skill has an invalid quoted description: {skill_file}") from exc
        elif len(value) >= 2 and value[0] == value[-1] == "'":
            description = value[1:-1].replace("''", "'")
        else:
            description = value
        if not description.strip():
            raise ValueError(f"source skill has an empty description: {skill_file}")
        return description.strip()
    raise ValueError(f"source skill has no description: {skill_file}")


def skill_source_roots() -> tuple[pathlib.Path, ...]:
    """Return documented host skill roots without reading user configuration."""
    home = pathlib.Path.home()
    codex_home_value = os.environ.get("CODEX_HOME")
    if codex_home_value is not None and not codex_home_value.strip():
        raise ValueError("CODEX_HOME is empty")
    codex_home = pathlib.Path(codex_home_value).expanduser() if codex_home_value else home / ".codex"
    if not codex_home.is_absolute():
        raise ValueError("CODEX_HOME must be absolute")
    return home / ".agents" / "skills", codex_home / "skills", pathlib.Path("/etc/codex/skills")


def _canonical_skill_files(root: pathlib.Path) -> set[pathlib.Path]:
    """Enumerate one root, following symlinked directories without allowing cycles."""
    try:
        root_status = root.stat()
    except FileNotFoundError:
        return set()
    except OSError as exc:
        raise OSError(f"could not inspect Codex skill root {root}: {exc}") from exc
    if not stat.S_ISDIR(root_status.st_mode):
        raise ValueError(f"Codex skill root is not a directory: {root}")

    pending = [root.resolve(strict=True)]
    visited: set[tuple[int, int]] = set()
    skills: set[pathlib.Path] = set()
    while pending:
        directory = pending.pop()
        try:
            canonical_directory = directory.resolve(strict=True)
            directory_status = canonical_directory.stat()
            identity = (directory_status.st_dev, directory_status.st_ino)
            if identity in visited:
                continue
            visited.add(identity)
            with os.scandir(canonical_directory) as entries:
                children = list(entries)
        except OSError as exc:
            raise OSError(f"could not inspect Codex skill root {directory}: {exc}") from exc
        for entry in children:
            try:
                if entry.name == "SKILL.md":
                    if not entry.is_file(follow_symlinks=True):
                        raise ValueError(f"Codex skill path is not a file: {entry.path}")
                    skills.add(pathlib.Path(entry.path).resolve(strict=True))
                elif entry.is_dir(follow_symlinks=True):
                    pending.append(pathlib.Path(entry.path))
            except OSError as exc:
                raise OSError(f"could not inspect Codex skill path {entry.path}: {exc}") from exc
    return skills


def enumerate_non_target_skills(target_skill: pathlib.Path) -> tuple[pathlib.Path, ...]:
    """Build a fresh canonical deny list for every non-target host skill."""
    target = target_skill.resolve(strict=True)
    discovered: set[pathlib.Path] = set()
    for root in skill_source_roots():
        discovered.update(_canonical_skill_files(root))
    discovered.discard(target)
    return tuple(sorted(discovered, key=str))


def codex_environment() -> dict[str, str]:
    """Keep the existing login location, not unrelated service credentials."""
    return {
        key: os.environ[key]
        for key in ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "LC_CTYPE", "USER", "CODEX_HOME")
        if key in os.environ
    }


def codex_executable() -> str:
    """Avoid a PATH symlink the fixture sandbox cannot execute for its own helper."""
    executable = shutil.which("codex")
    return str(pathlib.Path(executable).resolve()) if executable else "codex"


def fixture_permission_args(workspace: pathlib.Path) -> list[str]:
    """Use the reviewed native fixture-only policy, without legacy sandbox flags."""
    return [
        "-c", 'default_permissions="trigger-fixture"',
        "-c", 'permissions.trigger-fixture.filesystem={":root"="deny",":minimal"="read",'
        + json.dumps(str(workspace.resolve())) + '="read"}',
        "-c", "permissions.trigger-fixture.network.enabled=false",
        "-c", 'approval_policy="never"',
        "-c", "allow_login_shell=false",
    ]


def enumerate_mcp_servers(workspace: pathlib.Path, timeout: int) -> tuple[str, ...]:
    """Read configured names locally; never initialize servers or retain their config."""
    command = [codex_executable(), "mcp", "list", "--json"]
    for feature in DISABLED_FEATURES:
        command.extend(["--disable", feature])
    command.extend(["-c", 'web_search="disabled"', *fixture_permission_args(workspace)])
    try:
        completed = subprocess.run(
            command, cwd=workspace, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=timeout, env=codex_environment(),
            executable=shutil.which("codex", path=str(pathlib.Path(command[0]).parent)),
            shell=False, check=False,
        )
        if completed.returncode != 0:
            raise ValueError("Codex MCP inventory command failed")
        inventory = json.loads(completed.stdout)
        if not isinstance(inventory, list):
            raise ValueError("Codex MCP inventory is not a list")
        names = [item.get("name") if isinstance(item, dict) else None for item in inventory]
        if any(not isinstance(name, str) or not name.strip() for name in names):
            raise ValueError("Codex MCP inventory omitted a server name")
        if len(set(names)) != len(names):
            raise ValueError("Codex MCP inventory contains duplicate server names")
        return tuple(sorted(names))
    except (OSError, subprocess.TimeoutExpired, UnicodeError, json.JSONDecodeError) as exc:
        # Config values, endpoints and credential-bearing diagnostics are not evidence.
        raise ValueError("Codex MCP inventory could not be read locally") from exc


def skill_isolation_args(
    disabled_skills: tuple[pathlib.Path, ...],
    disabled_mcp_servers: tuple[str, ...] = (),
    *,
    ignore_user_config: bool = True,
) -> list[str]:
    """Build process-local session overrides without mutating saved configuration."""
    entries = ",".join(
        f"{{path={json.dumps(str(path))},enabled=false}}"
        for path in disabled_skills
    )
    args = [
        "--disable", "plugins",
        "-c", "skills.bundled.enabled=false",
        "-c", f"skills.config=[{entries}]",
    ]
    for feature in DISABLED_FEATURES[1:]:
        args.extend(["--disable", feature])
    # Even disabled entries need a transport when exec ignores user config.
    # A TOML table preserves exact names; the CLI does not unquote dotted -c keys.
    # No original endpoints or credentials are copied into these disabled entries.
    # Diagnostics load user config: do not mix a local transport into an existing
    # HTTP transport. They prove disabled entries, not exec's effective registry.
    disabled_entry = (
        f'{{enabled=false,command={json.dumps(sys.executable)},args=["-c","raise SystemExit(1)"]}}'
        if ignore_user_config else "{enabled=false}"
    )
    servers = ",".join(f"{json.dumps(name)}={disabled_entry}" for name in disabled_mcp_servers)
    args.extend(["-c", f"mcp_servers={{{servers}}}", "-c", 'web_search="disabled"'])
    return args


def _prompt_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in _prompt_strings(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _prompt_strings(item)]
    return []


def inspect_catalog_prompt(
    output: bytes,
    target_name: str,
    target_description: str,
    target_skill: pathlib.Path,
    workspace: pathlib.Path,
) -> tuple[dict[str, object] | None, str]:
    """Prove exact target catalog identity without returning the rendered prompt."""
    try:
        prompt_input = json.loads(output.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"Codex catalog preflight returned invalid JSON: {exc}"
    prompt_strings = _prompt_strings(prompt_input)
    warning_present = any(
        warning in text
        for text in prompt_strings
        for warning in SKILL_CATALOG_WARNINGS
    )
    catalogs = [text for text in prompt_strings if "### Available skills" in text]
    if len(catalogs) != 1:
        return None, f"Codex catalog preflight found {len(catalogs)} rendered catalogs"
    catalog = catalogs[0]
    catalog_roots: dict[str, str] = {}
    catalog_roots_valid = True
    if "### Skill roots" in catalog:
        roots_section = catalog.split("### Skill roots", 1)[1].split("### Available skills", 1)[0]
        for line in roots_section.splitlines():
            match = re.fullmatch(r"- `(r[0-9]+)` = `(.+)`", line)
            if match is None:
                continue
            alias, root_text = match.groups()
            if alias in catalog_roots:
                catalog_roots_valid = False
            catalog_roots[alias] = root_text
    available = catalog.split("### Available skills", 1)[1]
    available = available.split("### How to use skills", 1)[0]
    entries = [line for line in available.splitlines() if line.startswith("- ")]
    target_prefix = f"- {target_name}: "
    target_entries = [entry for entry in entries if entry.startswith(target_prefix)]
    target_description_exact = False
    rendered_file_valid = False
    target_file_exact = False
    root_alias_valid = False
    try:
        repository_skill_root = (workspace / ".agents" / "skills").resolve(strict=True)
        target_file = target_skill.resolve(strict=True)
        target_file_valid = (
            target_file.is_file()
            and target_file.parent.parent == repository_skill_root
        )
    except (OSError, RuntimeError, ValueError):
        repository_skill_root = None
        target_file = None
        target_file_valid = False
    entry_payload = target_entries[0][len(target_prefix) :] if len(target_entries) == 1 else ""
    if entry_payload.endswith(")") and " (file: " in entry_payload:
        rendered_description, rendered_file_text = entry_payload[:-1].rsplit(" (file: ", 1)
        target_description_exact = rendered_description == target_description
        rendered_file_path = pathlib.Path(rendered_file_text)
        rendered_candidate: pathlib.Path | None = None
        if rendered_file_path.is_absolute():
            rendered_candidate = rendered_file_path
            root_alias_valid = True
        elif len(rendered_file_path.parts) >= 2 and catalog_roots_valid:
            root_text = catalog_roots.get(rendered_file_path.parts[0])
            if root_text is not None and pathlib.Path(root_text).is_absolute():
                rendered_candidate = pathlib.Path(root_text).joinpath(*rendered_file_path.parts[1:])
                root_alias_valid = True
        if rendered_file_text and rendered_candidate is not None:
            try:
                rendered_file = rendered_candidate.resolve(strict=True)
                rendered_file_valid = rendered_file.is_file()
                target_file_exact = (
                    rendered_file_valid
                    and target_file_valid
                    and rendered_file == target_file
                )
            except (OSError, RuntimeError, ValueError):
                pass
    readiness = {
        "catalog_skill_entries": len(entries),
        "target_entries": len(target_entries),
        "target_description_exact": target_description_exact,
        "root_alias_valid": root_alias_valid,
        "rendered_file_valid": rendered_file_valid,
        "target_file_exact": target_file_exact,
        "target_description_chars": len(target_description),
        "warning_present": warning_present,
        "other_skill_entries": len(entries) - len(target_entries),
        "proof_scope": "catalog-only; debug prompt-input loads user config",
    }
    if not (
        len(entries) == 1
        and len(target_entries) == 1
        and target_description_exact
        and target_file_exact
        and not warning_present
    ):
        return None, f"Codex catalog preflight failed: {json.dumps(readiness, sort_keys=True)}"
    return readiness, "Codex catalog preflight passed"


def offline_catalog_preflight(
    workspace: pathlib.Path,
    target_name: str,
    target_description: str,
    target_skill: pathlib.Path,
    isolation_args: list[str],
    timeout: int,
) -> tuple[dict[str, object] | None, str]:
    """Render the catalog offline with matching supported session overrides."""
    command = [
        codex_executable(), "debug", "prompt-input",
        *fixture_permission_args(workspace), *isolation_args,
    ]
    try:
        completed = subprocess.run(
            command,
            executable=shutil.which("codex", path=str(pathlib.Path(command[0]).parent)),
            cwd=workspace,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            timeout=timeout,
            env=codex_environment(),
            shell=False,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, "Codex catalog preflight timed out"
    except OSError as exc:
        return None, f"Codex catalog preflight could not run: {exc}"
    if completed.returncode != 0:
        return None, f"Codex catalog preflight exited {completed.returncode}"
    return inspect_catalog_prompt(
        completed.stdout,
        target_name,
        target_description,
        target_skill,
        workspace,
    )


def _reported_failure(event: dict[str, object]) -> bool:
    """Recognize only failures in Codex's documented JSONL event union."""
    if event.get("type") in {"error", "turn.failed"}:
        return True
    item = event.get("item")
    return isinstance(item, dict) and item.get("type") == "error"


def inspect_codex_jsonl(
    output: bytes | str,
    marker: str,
    requested_model: str | None = None,
) -> dict[str, object]:
    """Validate one Codex JSONL run and identify only the exact staged marker."""
    events: list[dict[str, object]] = []
    try:
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="strict")
        for line in output.splitlines():
            if line.strip():
                event = json.loads(line)
                if not isinstance(event, dict):
                    raise ValueError("event is not an object")
                events.append(event)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return {"valid": False, "selected": False, "selected_marker": None,
                "isolation_stop": True, "reason": f"invalid JSONL: {exc}"}

    # Inspect every event, including started/failed calls, before lifecycle/marker scoring.
    # A runtime error with no tool-call event remains an invalid trial, not evidence
    # that a connected tool ran. A failed MCP call is still connected-tool activity.
    local_items = {"agent_message", "reasoning", "command_execution", "todo_list", "error"}
    for event in events:
        event_type = event.get("type")
        if isinstance(event_type, str) and event_type in {"item.started", "item.updated", "item.completed"}:
            item = event.get("item")
            item_type = item.get("type") if isinstance(item, dict) else None
            unsafe = not isinstance(item_type, str) or item_type not in local_items
            reason = "connected or unsupported tool item"
        else:
            unsafe = not isinstance(event_type, str) or event_type not in {
                "thread.started", "turn.started", "turn.completed", "turn.failed", "error",
            }
            reason = "unsupported event type"
        if unsafe:
            return {"valid": False, "selected": False, "selected_marker": None,
                    "isolation_stop": True, "reason": reason}

    event_types = [event.get("type") for event in events]
    lifecycle = ("thread.started", "turn.started", "turn.completed")
    if any(event_types.count(event_type) != 1 for event_type in lifecycle):
        return {
            "valid": False,
            "selected": False,
            "selected_marker": None,
            "reason": "missing or ambiguous thread/turn lifecycle",
        }
    lifecycle_positions = tuple(event_types.index(event_type) for event_type in lifecycle)
    if lifecycle_positions != tuple(sorted(lifecycle_positions)):
        return {
            "valid": False,
            "selected": False,
            "selected_marker": None,
            "reason": "thread/turn lifecycle is out of order",
        }
    if any(_reported_failure(event) for event in events):
        return {"valid": False, "selected": False, "selected_marker": None, "reason": "Codex reported a failed run"}
    thread_event = next(event for event in events if event.get("type") == "thread.started")
    thread_id = thread_event.get("thread_id") or thread_event.get("threadId")
    if not isinstance(thread_id, str) or not thread_id:
        return {"valid": False, "selected": False, "selected_marker": None, "reason": "thread start omitted its id"}

    turn_start = lifecycle_positions[1]
    turn_complete = lifecycle_positions[2]
    completed_agent_messages = [
        item.get("text")
        for index, event in enumerate(events)
        if turn_start < index < turn_complete
        if event.get("type") == "item.completed"
        and isinstance((item := event.get("item")), dict)
        and item.get("type") == "agent_message"
        and isinstance(item.get("text"), str)
        and bool(item.get("text").strip())
    ]
    if not completed_agent_messages:
        return {
            "valid": False,
            "selected": False,
            "selected_marker": None,
            "reason": "completed turn omitted its agent response",
        }
    markers = MARKER_PATTERN.findall("\n".join(completed_agent_messages))
    competing = sorted(set(markers) - {marker})
    if competing:
        return {
            "valid": False,
            "selected": False,
            "selected_marker": None,
            "reason": f"competing staged marker(s): {', '.join(competing)}",
        }
    marker_count = markers.count(marker)
    selected = marker_count == 1
    if marker_count > 1:
        return {"valid": False, "selected": False, "selected_marker": None, "reason": "ambiguous repeated staged marker"}
    if selected:
        marker_messages = [message for message in completed_agent_messages if marker in MARKER_PATTERN.findall(message)]
        first_lines = [line.strip() for line in marker_messages[0].splitlines() if line.strip()]
        if not first_lines or first_lines[0] != marker:
            return {
                "valid": False,
                "selected": False,
                "selected_marker": None,
                "reason": "staged marker was not first in its completed message",
            }

    resolved_models = {
        model
        for event in events
        if event.get("type") in {"thread.started", "turn.started"}
        and isinstance((model := event.get("model")), str)
        and model
    }
    if len(resolved_models) > 1:
        return {
            "valid": False,
            "selected": False,
            "selected_marker": None,
            "reason": "Codex reported ambiguous resolved models",
        }
    resolved_model = next(iter(resolved_models), None)
    if requested_model is not None and resolved_model is not None and resolved_model != requested_model:
        return {
            "valid": False,
            "selected": False,
            "selected_marker": None,
            "requested_model": requested_model,
            "resolved_model": resolved_model,
            "reason": "Codex resolved a different model than requested",
        }
    return {
        "valid": True,
        "selected": selected,
        "selected_marker": marker if selected else None,
        "thread_id": thread_id,
        "requested_model": requested_model,
        "resolved_model": resolved_model,
        "reason": "exact staged marker" if selected else "no staged marker",
    }


def retain_run_evidence(
    evidence_dir: pathlib.Path,
    case_number: int,
    run_number: int,
    output: bytes,
    error_output: bytes,
) -> dict[str, str]:
    """Persist the exact provider streams and return immutable path/digest evidence."""
    stem = f"case-{case_number:03d}-trial-{run_number:02d}"
    jsonl_path = evidence_dir / f"{stem}.jsonl"
    stderr_path = evidence_dir / f"{stem}.stderr.log"
    jsonl_path.write_bytes(output)
    stderr_path.write_bytes(error_output)
    return {
        "jsonl_path": str(jsonl_path.resolve()),
        "jsonl_sha256": hashlib.sha256(output).hexdigest(),
        "stderr_path": str(stderr_path.resolve()),
        "stderr_sha256": hashlib.sha256(error_output).hexdigest(),
    }


def remove_workspace(workspace: pathlib.Path) -> str | None:
    """Remove the staged repository and fail loud if any residue remains."""
    try:
        shutil.rmtree(workspace)
    except OSError as exc:
        return f"could not remove disposable eval repository {workspace}: {exc}"
    if workspace.exists():
        return f"disposable eval repository cleanup left residue at {workspace}"
    return None


def case_passes(
    should_trigger: bool,
    triggers: int,
    runs: int,
    threshold: float,
    invalid_runs: int,
) -> bool:
    """Score a case only when every provider run completed truthfully."""
    if runs <= 0 or invalid_runs != 0:
        return False
    return ((triggers / runs) >= threshold) == should_trigger


def run_codex_query(
    workspace: pathlib.Path,
    query: str,
    reasoning: str,
    model: str,
    timeout: int,
    isolation_args: list[str],
) -> tuple[int, bytes, bytes, bool]:
    cmd = [
        codex_executable(), "exec", "--strict-config",
        "--cd", str(workspace),
        *fixture_permission_args(workspace),
        "--ephemeral",
        "--ignore-user-config",
        "--json",
        "-m", model,
        "-c", f'model_reasoning_effort="{reasoning}"',
    ]
    cmd.extend(isolation_args)
    cmd.append(query)
    env = codex_environment()
    try:
        proc = subprocess.run(
            cmd,
            executable=shutil.which("codex", path=str(pathlib.Path(cmd[0]).parent)),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            timeout=timeout,
            env=env,
            shell=False,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr, False
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout if isinstance(e.stdout, bytes) else b""
        stderr = e.stderr if isinstance(e.stderr, bytes) else b""
        return -1, stdout, stderr, True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("skill", help="Codex skill name (looked up under codex-skills/)")
    ap.add_argument("--runs", type=int, default=3, help="Trials per query (default 3)")
    ap.add_argument("--limit", type=int, help="Only run the first N queries from the eval set")
    ap.add_argument(
        "--reasoning",
        default=DEFAULT_REASONING_EFFORT,
        help=f"codex model_reasoning_effort (default: {DEFAULT_REASONING_EFFORT})",
    )
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"Codex model id (default: {DEFAULT_MODEL})")
    ap.add_argument("--threshold", type=float, default=0.5, help="Trigger-rate threshold for pass (default 0.5)")
    ap.add_argument("--timeout", type=int, default=180, help="Per-query timeout seconds (default 180)")
    ap.add_argument("--out", help="Write detailed JSON results to this file")
    ap.add_argument("--evidence-dir", help="Directory for exact per-trial JSONL and stderr evidence")
    args = ap.parse_args()

    eval_file = find_eval_file(args.skill)
    skill_src = find_skill_source(args.skill)
    eval_data, corpus_reason = load_eval_corpus(eval_file)
    if eval_data is None:
        sys.exit(f"ERROR: {corpus_reason}")
    if args.runs <= 0 or not 0.0 <= args.threshold <= 1.0:
        sys.exit("ERROR: --runs must be positive and --threshold must be between 0 and 1")
    if args.limit is not None and args.limit <= 0:
        sys.exit("ERROR: --limit must be positive")
    if args.limit is not None:
        eval_data = eval_data[: args.limit]

    if shutil.which("codex") is None:
        sys.exit("ERROR: codex CLI not on PATH")

    test_uuid = uuid.uuid4().hex[:8]
    test_skill_name = f"{args.skill}-eval-{test_uuid}"
    marker = f"CODEX_SKILL_FIRED:{test_skill_name}"

    if args.evidence_dir:
        evidence_dir = pathlib.Path(args.evidence_dir).resolve()
        evidence_dir.mkdir(parents=True, exist_ok=False)
    else:
        evidence_dir = pathlib.Path(tempfile.mkdtemp(prefix=f"codex-eval-evidence-{args.skill}-"))
    workspace = pathlib.Path(tempfile.mkdtemp(prefix=f"codex-eval-{args.skill}-"))
    exit_code = 1
    try:
        initialized = subprocess.run(
            ["git", "init", "--quiet"],
            cwd=workspace,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
            check=False,
        )
        if initialized.returncode != 0:
            sys.exit(f"ERROR: could not initialize disposable eval repository: {initialized.stderr.strip()}")
        skill_dir = stage_repository_skill(skill_src, workspace, test_skill_name, marker)
        target_skill = skill_dir / "SKILL.md"
        target_description = source_skill_description(skill_src)
        if source_skill_description(target_skill) != target_description:
            raise ValueError("staged Codex skill description differs from its source")
        disabled_skills = enumerate_non_target_skills(target_skill)
        disabled_mcp_servers = enumerate_mcp_servers(workspace, args.timeout)
        isolation_args = skill_isolation_args(disabled_skills, disabled_mcp_servers)
        catalog_args = skill_isolation_args(disabled_skills, disabled_mcp_servers, ignore_user_config=False)
        readiness, readiness_reason = offline_catalog_preflight(
            workspace,
            test_skill_name,
            target_description,
            target_skill,
            catalog_args,
            args.timeout,
        )
        if readiness is None:
            raise ValueError(readiness_reason)

        print(f"Codex Layer 2 trigger eval: {args.skill}", file=sys.stderr)
        print(f"  Eval file:  {eval_file}", file=sys.stderr)
        print(f"  Skill src:  {skill_src}", file=sys.stderr)
        print(f"  Test skill: {test_skill_name}", file=sys.stderr)
        print(f"  Workspace:  {workspace}", file=sys.stderr)
        print(f"  Evidence:   {evidence_dir}", file=sys.stderr)
        print("  Login:      existing Codex session (credential files are not copied)", file=sys.stderr)
        print(f"  Queries:    {len(eval_data)} (x{args.runs} runs)", file=sys.stderr)
        print(f"  Reasoning:  {args.reasoning}", file=sys.stderr)
        print(f"  Model:      {args.model}", file=sys.stderr)
        print(
            "  Catalog:    exactly one target with exact source description "
            "(offline catalog-only proof)",
            file=sys.stderr,
        )
        print("", file=sys.stderr)

        results = []
        passed = failed = 0
        for idx, entry in enumerate(eval_data, start=1):
            query = entry["query"]
            should_trigger = bool(entry["should_trigger"])
            triggers = 0
            invalid_runs = 0
            run_evidence = []
            for run in range(1, args.runs + 1):
                if enumerate_non_target_skills(target_skill) != disabled_skills:
                    raise ValueError("Codex skill roots changed after catalog preflight")
                if enumerate_mcp_servers(workspace, args.timeout) != disabled_mcp_servers:
                    raise ValueError("Codex MCP inventory changed after catalog preflight")
                rc, output, error_output, timed_out = run_codex_query(
                    workspace,
                    query,
                    args.reasoning,
                    args.model,
                    args.timeout,
                    isolation_args,
                )
                raw_evidence = retain_run_evidence(evidence_dir, idx, run, output, error_output)
                evidence = inspect_codex_jsonl(output, marker, requested_model=args.model)
                evidence = {**evidence, **raw_evidence, "timed_out": timed_out}
                if evidence.get("isolation_stop"):
                    (evidence_dir / "isolation-stop.json").write_text(
                        json.dumps({"case": idx, "trial": run, "evidence": evidence}, indent=2),
                        encoding="utf-8",
                    )
                    raise ValueError("Codex isolation violation; retained invalid trial and stopped future queries")
                run_valid = not timed_out and rc == 0 and bool(evidence["valid"])
                if not run_valid:
                    invalid_runs += 1
                    evidence = {
                        **evidence,
                        "reason": (
                            f"timed_out={timed_out}; exit={rc}; {evidence['reason']}; stderr="
                            f"{error_output.decode('utf-8', errors='replace').strip()[:200]}"
                        ),
                    }
                if run_valid and evidence["selected"]:
                    triggers += 1
                run_evidence.append(evidence)
            trigger_rate = triggers / args.runs
            is_pass = case_passes(
                should_trigger,
                triggers,
                args.runs,
                args.threshold,
                invalid_runs,
            )
            if is_pass:
                passed += 1
            else:
                failed += 1
            mark = "PASS" if is_pass else "FAIL"
            expect = "TRIG" if should_trigger else "NOOP"
            print(
                f"  [{idx:2d}/{len(eval_data)}] expect={expect} trig={triggers}/{args.runs} "
                f"invalid={invalid_runs} {mark}  {query[:70]}",
                file=sys.stderr,
            )
            results.append({
                "query": query,
                "should_trigger": should_trigger,
                "triggers": triggers,
                "runs": args.runs,
                "trigger_rate": round(trigger_rate, 3),
                "invalid_runs": invalid_runs,
                "selection_evidence": run_evidence,
                "pass": is_pass,
            })

        resolved_models = [
            evidence.get("resolved_model")
            for result in results
            for evidence in result["selection_evidence"]
        ]
        resolved_model = (
            resolved_models[0]
            if resolved_models
            and all(model == resolved_models[0] and isinstance(model, str) for model in resolved_models)
            else None
        )
        summary = {
            "skill": args.skill,
            "total": len(eval_data),
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / len(eval_data), 3) if eval_data else 0.0,
            "runs_per_query": args.runs,
            "reasoning": args.reasoning,
            "requested_model": args.model,
            "resolved_model": resolved_model,
        }

        report = {"summary": summary, "results": results}
        print("", file=sys.stderr)
        print("===========================", file=sys.stderr)
        print(f"Codex Trigger Eval: {args.skill}", file=sys.stderr)
        print(f"  PASSED: {passed}/{len(eval_data)} ({summary['pass_rate']*100:.0f}%)", file=sys.stderr)
        print(f"  FAILED: {failed}/{len(eval_data)}", file=sys.stderr)
        print("===========================", file=sys.stderr)

        if args.out:
            pathlib.Path(args.out).write_text(json.dumps(report, indent=2))
            print(f"Wrote detailed results to: {args.out}", file=sys.stderr)

        print(json.dumps(report, indent=2))
        exit_code = 0 if failed == 0 else 1
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        exit_code = 1
    finally:
        cleanup_error = remove_workspace(workspace)
        if cleanup_error is not None:
            print(f"ERROR: {cleanup_error}", file=sys.stderr)
            exit_code = 2
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
