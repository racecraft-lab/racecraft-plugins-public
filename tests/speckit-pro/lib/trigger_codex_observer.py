"""Parse a Codex JSONL trial and its skill catalog into typed selection observations.

Both the Codex runner and the provider-free comparator replay recorded streams
through this module, so neither has to load the other's script."""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import shlex


MARKER_PATTERN = re.compile(r"CODEX_SKILL_SELECTED:[A-Za-z0-9_-]+")
SKILL_CATALOG_WARNINGS = (
    "Skill descriptions were shortened to fit the skills context budget.",
    "Exceeded skills context budget.",
)


def _catalog_locator_alias(locator: str, skill_name: str) -> str | None:
    """Return the alias from one canonical catalog-relative skill locator."""
    parts = pathlib.PurePosixPath(locator).parts
    if (
        len(parts) == 3
        and re.fullmatch(r"r[0-9]+", parts[0]) is not None
        and parts[1:] == (skill_name, "SKILL.md")
        and locator == f"{parts[0]}/{skill_name}/SKILL.md"
    ):
        return parts[0]
    return None


def _prompt_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in _prompt_strings(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _prompt_strings(item)]
    return []


def _catalog_entry_identity(
    payload: str,
    expected: tuple[str, str, pathlib.Path | None],
    repository_skill_root: pathlib.Path | None,
    catalog_roots: dict[str, str],
) -> dict[str, object]:
    """Validate one catalog entry's description and canonical source locator."""
    name, description, expected_file = expected
    result: dict[str, object] = {
        "description_exact": False,
        "alias_valid": False,
        "file_valid": False,
        "file_exact": False,
        "locator": None,
        "alias": None,
    }
    if not payload.endswith(")") or " (file: " not in payload or expected_file is None:
        return result
    rendered_description, locator = payload[:-1].rsplit(" (file: ", 1)
    result["description_exact"] = rendered_description == description
    locator_path = pathlib.Path(locator)
    candidate: pathlib.Path | None = None
    try:
        if locator_path.is_absolute():
            result["alias_valid"] = locator_path == expected_file
            candidate = locator_path if result["alias_valid"] else None
        else:
            alias = _catalog_locator_alias(locator, name)
            root_text = catalog_roots.get(alias) if alias is not None else None
            root_path = pathlib.Path(root_text) if root_text is not None else None
            if (
                root_path is not None
                and root_path.is_absolute()
                and root_path.resolve(strict=True) == repository_skill_root
            ):
                result["alias_valid"] = True
                result["alias"] = alias
                candidate = root_path / name / "SKILL.md"
        if candidate is not None:
            rendered_file = candidate.resolve(strict=True)
            result["file_valid"] = rendered_file.is_file()
            result["file_exact"] = result["file_valid"] and rendered_file == expected_file
        if all(result[key] for key in ("description_exact", "alias_valid", "file_exact")):
            result["locator"] = locator
    except (OSError, RuntimeError, ValueError):
        # An unresolvable catalog path fails the identity check: the flags recorded so far
        # stay as set, and no locator is reported.
        result["locator"] = None
    return result


def _catalog_root_map(catalog: str) -> tuple[dict[str, str], bool]:
    """Parse unique Codex catalog root aliases without accepting partial lines."""
    roots: dict[str, str] = {}
    valid = True
    if "### Skill roots" not in catalog:
        return roots, valid
    section = catalog.split("### Skill roots", 1)[1].split("### Available skills", 1)[0]
    for line in section.splitlines():
        match = re.fullmatch(r"- `(r[0-9]+)` = `(.+)`", line)
        if match is None:
            continue
        alias, root_text = match.groups()
        valid = valid and alias not in roots
        roots[alias] = root_text
    return roots, valid


def inspect_catalog_prompt(
    output: bytes,
    target_name: str,
    target_description: str,
    target_skill: pathlib.Path,
    workspace: pathlib.Path,
    siblings: dict[str, str] | None = None,
) -> tuple[dict[str, object] | None, str]:
    """Prove exact target catalog identity without returning the rendered prompt.

    With ``siblings`` (name to exact description), the catalog must also hold exactly
    one entry per sibling with that description and no other entries.
    """
    siblings = dict(siblings or {})
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
    catalog_roots, catalog_roots_valid = _catalog_root_map(catalog)
    available = catalog.split("### Available skills", 1)[1]
    available = available.split("### How to use skills", 1)[0]
    entries = [line for line in available.splitlines() if line.startswith("- ")]
    target_prefix = f"- {target_name}: "
    target_entries = [entry for entry in entries if entry.startswith(target_prefix)]
    target_description_exact = False
    rendered_file_valid = False
    target_file_exact = False
    root_alias_valid = False
    skill_root_alias: str | None = None
    skill_source_locators: dict[str, str] = {}
    source_locators_exact = True
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
    expected_descriptions = {target_name: target_description, **siblings}
    sibling_entries = 0
    sibling_entries_exact = True
    relative_aliases: set[str] = set()
    relative_locator_count = 0
    for name, description in expected_descriptions.items():
        prefix = f"- {name}: "
        matching = [entry[len(prefix):] for entry in entries if entry.startswith(prefix)]
        if name != target_name:
            sibling_entries += len(matching)
        try:
            expected_file = (
                (target_file if target_file_valid else None)
                if name == target_name
                else (repository_skill_root / name / "SKILL.md").resolve(strict=True)
            )
        except (OSError, RuntimeError, TypeError, ValueError):
            expected_file = None
        identity = _catalog_entry_identity(
            matching[0] if len(matching) == 1 else "",
            (name, description, expected_file),
            repository_skill_root,
            catalog_roots if catalog_roots_valid else {},
        )
        entry_exact = identity["locator"] is not None
        locator = identity["locator"]
        alias = identity["alias"]
        if isinstance(locator, str):
            skill_source_locators[name] = locator
        if isinstance(alias, str):
            relative_aliases.add(alias)
            relative_locator_count += 1
        source_locators_exact = source_locators_exact and entry_exact
        if name == target_name:
            target_description_exact = bool(identity["description_exact"])
            rendered_file_valid = bool(identity["file_valid"])
            target_file_exact = bool(identity["file_exact"])
            root_alias_valid = bool(identity["alias_valid"])
        else:
            sibling_entries_exact = sibling_entries_exact and entry_exact
    if len(relative_aliases) == 1 and relative_locator_count == len(expected_descriptions):
        skill_root_alias = next(iter(relative_aliases))
    elif relative_aliases:
        source_locators_exact = False
    readiness = {
        "catalog_skill_entries": len(entries),
        "target_entries": len(target_entries),
        "sibling_entries": sibling_entries,
        "sibling_entries_exact": sibling_entries_exact,
        "target_description_exact": target_description_exact,
        "root_alias_valid": root_alias_valid,
        "rendered_file_valid": rendered_file_valid,
        "target_file_exact": target_file_exact,
        "skill_root_alias": skill_root_alias,
        "skill_source_locators": skill_source_locators,
        "source_locators_exact": source_locators_exact,
        "target_description_chars": len(target_description),
        "warning_present": warning_present,
        "other_skill_entries": len(entries) - len(target_entries),
        "proof_scope": "catalog-only; debug prompt-input loads user config",
    }
    if not (
        len(entries) == 1 + len(siblings)
        and len(target_entries) == 1
        and sibling_entries == len(siblings)
        and sibling_entries_exact
        and target_description_exact
        and target_file_exact
        and source_locators_exact
        and not warning_present
    ):
        return None, f"Codex catalog preflight failed: {json.dumps(readiness, sort_keys=True)}"
    return readiness, "Codex catalog preflight passed"


def _reported_failure(event: dict[str, object]) -> bool:
    """Recognize only failures in Codex's documented JSONL event union."""
    if event.get("type") in {"error", "turn.failed"}:
        return True
    item = event.get("item")
    if not isinstance(item, dict):
        return False
    if item.get("type") == "error":
        return True
    if item.get("type") == "command_execution":
        if item.get("status") in {"failed", "declined"}:
            return True
        if event.get("type") == "item.completed":
            return item.get("status") != "completed" or type(item.get("exit_code")) is not int or item["exit_code"] != 0
    return False


def _invalid_codex_observation(reason: str, *, isolation_stop: bool = False) -> dict[str, object]:
    return {
        "valid": False,
        "selected": False,
        "selected_marker": None,
        "selected_skill": None,
        "selected_skill_set": [],
        "qualification_observed": False,
        "observation_scope": "codex-body-read-attestation",
        "isolation_stop": isolation_stop,
        "reason": reason,
    }


def _valid_witness_source_locator(value: object, skill_name: str) -> bool:
    return value is None or (
        isinstance(value, str)
        and _catalog_locator_alias(value, skill_name) is not None
    )


def _validated_marker_map(
    target_skill: str,
    witnesses: dict[str, dict[str, str]],
) -> tuple[dict[str, str] | None, str | None]:
    if target_skill not in witnesses or not witnesses:
        return None, "selection witnesses omit the target skill"
    marker_to_skill: dict[str, str] = {}
    for skill_name, witness in witnesses.items():
        marker = witness.get("marker") if isinstance(witness, dict) else None
        path = witness.get("path") if isinstance(witness, dict) else None
        relative_path = witness.get("relative_path") if isinstance(witness, dict) else None
        source_locator = witness.get("source_locator") if isinstance(witness, dict) else None
        digest = witness.get("sha256") if isinstance(witness, dict) else None
        body = witness.get("body") if isinstance(witness, dict) else None
        if (
            not isinstance(skill_name, str)
            or not isinstance(marker, str)
            or MARKER_PATTERN.fullmatch(marker) is None
            or not isinstance(path, str)
            or not pathlib.Path(path).is_absolute()
            or not isinstance(relative_path, str)
            or not relative_path
            or not _valid_witness_source_locator(source_locator, skill_name)
            or not isinstance(digest, str)
            or not isinstance(body, str)
            or hashlib.sha256(body.encode("utf-8")).hexdigest() != digest
            or body.count(marker) != 1
            or marker in marker_to_skill
        ):
            return None, "selection witness is malformed"
        marker_to_skill[marker] = skill_name
    return marker_to_skill, None


def _decode_codex_events(output: bytes | str) -> tuple[list[dict[str, object]] | None, str | None]:
    try:
        text = output.decode("utf-8", errors="strict") if isinstance(output, bytes) else output
        events = []
        for line in text.splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError("event is not an object")
            events.append(event)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return None, f"invalid JSONL: {exc}"
    return events, None


def _codex_isolation_error(events: list[dict[str, object]]) -> str | None:
    local_items = {"agent_message", "reasoning", "command_execution", "error"}
    lifecycle_events = {"thread.started", "turn.started", "turn.completed", "turn.failed", "error"}
    for event in events:
        event_type = event.get("type")
        if isinstance(event_type, str) and event_type in {"item.started", "item.updated", "item.completed"}:
            item = event.get("item")
            item_type = item.get("type") if isinstance(item, dict) else None
            if not isinstance(item_type, str) or item_type not in local_items:
                return "connected or unsupported tool item"
        elif not isinstance(event_type, str) or event_type not in lifecycle_events:
            return "unsupported event type"
    return None


def _shell_command_tokens(command: str) -> list[str] | None:
    try:
        wrapper = shlex.split(command)
        if (
            len(wrapper) != 3
            or pathlib.Path(wrapper[0]).name not in {"bash", "sh", "zsh"}
            or wrapper[1] != "-c"
        ):
            return None
        return shlex.split(wrapper[2])
    except ValueError:
        return None


def _sed_range_covers_body(tokens: list[str], body: str) -> bool:
    """Accept only a canonical first-line range that includes the complete body."""
    if len(tokens) != 4 or tokens[:2] != ["sed", "-n"]:
        return False
    matched = re.fullmatch(r"1,([1-9][0-9]*)p", tokens[2])
    if matched is None:
        return False
    endpoint = matched.group(1)
    final_body_line = str(len(body.splitlines()))
    return (len(endpoint), endpoint) >= (len(final_body_line), final_body_line)


def _exact_codex_body_read_skill(
    command: str,
    command_output: str,
    witnesses: dict[str, dict[str, str]],
) -> str | None:
    body_matches = [
        name for name, witness in witnesses.items()
        if command_output == witness["body"]
    ]
    if len(body_matches) != 1:
        return None
    skill_name = body_matches[0]
    if any(witness["marker"] in command for witness in witnesses.values()):
        return None
    tokens = _shell_command_tokens(command)
    if tokens is None:
        try:
            tokens = shlex.split(command)
        except ValueError:
            return None
    if _sed_range_covers_body(tokens, witnesses[skill_name]["body"]):
        read_path = tokens[3]
    elif tokens[:-1] in (["cat"], ["command", "cat"]):
        read_path = tokens[-1]
    else:
        return None
    if read_path == "SKILL.md":
        return skill_name if tokens[0] == "sed" else None
    if tokens[0] == "sed" and read_path == f"{skill_name}/SKILL.md":
        return skill_name
    exact_locations = {
        location
        for location in (
            witnesses[skill_name]["path"],
            witnesses[skill_name]["relative_path"],
            witnesses[skill_name].get("source_locator"),
        )
        if isinstance(location, str)
    }
    return skill_name if read_path in exact_locations else None


def _leading_compound_codex_body_skill(
    command: str,
    witnesses: dict[str, dict[str, str]],
) -> str | None:
    """Recognize an exact staged-body read at the start of a compound shell command."""
    tokens = _shell_command_tokens(command)
    if tokens is None:
        return None
    if len(tokens) < 6 or tokens[:2] != ["sed", "-n"] or tokens[4] != "&&":
        return None
    read_path = tokens[3]
    matches = [
        name
        for name, witness in witnesses.items()
        if read_path in {
            location
            for location in (
                witness["path"], witness["relative_path"], witness.get("source_locator"),
            )
            if isinstance(location, str)
        }
    ]
    if len(matches) != 1:
        return None
    if not _sed_range_covers_body(tokens[:4], witnesses[matches[0]]["body"]):
        return None
    tail_tokens = tokens[5:]
    if any(
        location in token
        for witness in witnesses.values()
        for location in (
            witness["path"], witness["relative_path"], witness.get("source_locator"),
        )
        if isinstance(location, str)
        for token in tail_tokens
    ):
        return None
    if any(witness["marker"] in command for witness in witnesses.values()):
        return None
    return matches[0]


def _leading_compound_codex_body_read(
    command: str,
    command_output: str,
    witnesses: dict[str, dict[str, str]],
) -> str | None:
    skill_name = _leading_compound_codex_body_skill(command, witnesses)
    if skill_name is None:
        return None
    body = witnesses[skill_name]["body"]
    if not command_output.startswith(body):
        return None
    suffix = command_output[len(body):]
    if any(
        witness["body"] in suffix or witness["marker"] in suffix
        for witness in witnesses.values()
    ):
        return None
    return skill_name


def _post_start_marker_codex_body_read(
    events: list[dict[str, object]],
    command_start: int,
    turn_complete: int,
    command: str,
    witnesses: dict[str, dict[str, str]],
) -> str | None:
    skill_name = _leading_compound_codex_body_skill(command, witnesses)
    if skill_name is None:
        return None
    marker = witnesses[skill_name]["marker"]
    for event in events[command_start + 1:turn_complete]:
        item = event.get("item")
        if (
            event.get("type") == "item.completed"
            and isinstance(item, dict)
            and item.get("type") == "agent_message"
            and isinstance(item.get("text"), str)
            and marker in MARKER_PATTERN.findall(item["text"])
        ):
            return skill_name
    return None


def _append_post_start_codex_body_read(
    events: list[dict[str, object]],
    turn_complete: int,
    command_starts: dict[str, tuple[str, int]],
    reads: list[dict[str, str]],
    witnesses: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    read_ids = {read["command_item_id"] for read in reads}
    pending_ids = set(command_starts) - read_ids
    if len(pending_ids) != 1:
        return reads
    item_id = pending_ids.pop()
    command, command_start = command_starts[item_id]
    skill_name = _post_start_marker_codex_body_read(
        events, command_start, turn_complete, command, witnesses,
    )
    if skill_name is None or skill_name in {read["skill"] for read in reads}:
        return reads
    return [*reads, {
        "skill": skill_name,
        "path": witnesses[skill_name]["path"],
        "sha256": witnesses[skill_name]["sha256"],
        "command_item_id": item_id,
        "read_mode": "post-start-marker",
    }]


def _codex_body_read_error(
    command_starts: dict[str, tuple[str, int]],
    reads: list[dict[str, str]],
) -> str | None:
    if set(command_starts) != {read["command_item_id"] for read in reads}:
        return "command execution lacked a completed or post-start marker body-read attestation"
    if len({read["skill"] for read in reads}) > 1:
        return "multiple staged skill bodies were read"
    return None


def codex_body_read_match(
    command: str,
    command_output: str,
    witnesses: dict[str, dict[str, str]],
) -> tuple[str, str] | None:
    exact_match = _exact_codex_body_read_skill(command, command_output, witnesses)
    if exact_match is not None:
        return exact_match, "exact-output"
    compound_match = _leading_compound_codex_body_read(command, command_output, witnesses)
    if compound_match is None:
        return None
    return compound_match, "leading-compound-output"


def _completed_codex_body_read_match(
    events: list[dict[str, object]],
    command_start: tuple[str, int],
    turn_complete: int,
    command_output: str,
    witnesses: dict[str, dict[str, str]],
) -> tuple[str, str] | None:
    command, start_index = command_start
    match = codex_body_read_match(command, command_output, witnesses)
    if match is not None:
        return match
    if any(
        witness["body"] in command_output or witness["marker"] in command_output
        for witness in witnesses.values()
    ):
        return None
    skill_name = _post_start_marker_codex_body_read(
        events, start_index, turn_complete, command, witnesses,
    )
    return (skill_name, "post-start-marker") if skill_name is not None else None


def _codex_body_reads(
    events: list[dict[str, object]],
    turn_start: int,
    turn_complete: int,
    witnesses: dict[str, dict[str, str]],
) -> tuple[list[str], list[dict[str, str]], str | None]:
    command_starts: dict[str, tuple[str, int]] = {}
    consulted: list[str] = []
    reads: list[dict[str, str]] = []
    for index, event in enumerate(events):
        if not turn_start < index < turn_complete:
            continue
        item = event.get("item")
        if not isinstance(item, dict) or item.get("type") != "command_execution":
            continue
        item_id = item.get("id")
        command = item.get("command")
        if not isinstance(item_id, str) or not item_id or not isinstance(command, str) or not command:
            return [], [], "command execution omitted its identity or command"
        if event.get("type") == "item.started":
            if item_id in command_starts:
                return [], [], "command execution started more than once"
            command_starts[item_id] = (command, index)
            continue
        if event.get("type") == "item.updated":
            if command_starts.get(item_id, ("", -1))[0] != command:
                return [], [], "command execution update was not bound to its start"
            continue
        if event.get("type") != "item.completed" or command_starts.get(item_id, ("", -1))[0] != command:
            return [], [], "command execution completion was not bound to its start"
        command_output = item.get("aggregated_output")
        if not isinstance(command_output, str):
            return [], [], "command execution omitted its output"
        match = _completed_codex_body_read_match(
            events, command_starts[item_id], turn_complete, command_output, witnesses,
        )
        if match is None:
            return [], [], "command was not an exact staged skill-body read"
        skill_name, read_mode = match
        if skill_name in consulted:
            return [], [], "staged skill body was read more than once"
        consulted.append(skill_name)
        reads.append({
            "skill": skill_name,
            "path": witnesses[skill_name]["path"],
            "sha256": witnesses[skill_name]["sha256"],
            "command_item_id": item_id,
            "read_mode": read_mode,
        })
    reads = _append_post_start_codex_body_read(
        events, turn_complete, command_starts, reads, witnesses,
    )
    consulted = [read["skill"] for read in reads]
    if read_error := _codex_body_read_error(command_starts, reads):
        return [], [], read_error
    return consulted, reads, None


def _codex_selected_marker(
    messages: list[str],
    marker_to_skill: dict[str, str],
    consulted: list[str],
) -> tuple[str | None, str | None, str | None]:
    emitted = MARKER_PATTERN.findall("\n".join(messages))
    unknown = sorted(set(emitted) - set(marker_to_skill))
    if unknown:
        return None, None, f"unknown staged marker(s): {', '.join(unknown)}"
    if len(emitted) > 1:
        return None, None, "ambiguous repeated or competing staged markers"
    selected_marker = emitted[0] if emitted else None
    selected_skill = marker_to_skill.get(selected_marker) if selected_marker else None
    if selected_marker is None:
        return None, None, None
    marker_message = next(message for message in messages if selected_marker in MARKER_PATTERN.findall(message))
    first_lines = [line.strip() for line in marker_message.splitlines() if line.strip()]
    if not first_lines or first_lines[0] != selected_marker:
        return None, None, "staged marker was not first in its completed message"
    if selected_skill not in consulted:
        return None, None, "staged marker was not corroborated by its exact skill-body read"
    return selected_marker, selected_skill, None


def inspect_codex_jsonl(
    output: bytes | str,
    target_skill: str,
    witnesses: dict[str, dict[str, str]],
    requested_model: str | None = None,
) -> dict[str, object]:
    """Validate one run and bind its selected marker to an exact staged-body read."""
    scope = "codex-body-read-attestation"
    marker_to_skill, witness_error = _validated_marker_map(target_skill, witnesses)
    if marker_to_skill is None:
        return _invalid_codex_observation(str(witness_error), isolation_stop=True)
    events, decode_error = _decode_codex_events(output)
    if events is None:
        return _invalid_codex_observation(str(decode_error), isolation_stop=True)

    # Inspect every event, including started/failed calls, before lifecycle/marker scoring.
    # A runtime error with no tool-call event remains an invalid trial, not evidence
    # that a connected tool ran. A failed MCP call is still connected-tool activity.
    isolation_error = _codex_isolation_error(events)
    if isolation_error:
        return _invalid_codex_observation(isolation_error, isolation_stop=True)

    event_types = [event.get("type") for event in events]
    lifecycle = ("thread.started", "turn.started", "turn.completed")
    if any(event_types.count(event_type) != 1 for event_type in lifecycle):
        return _invalid_codex_observation("missing or ambiguous thread/turn lifecycle")
    lifecycle_positions = tuple(event_types.index(event_type) for event_type in lifecycle)
    if lifecycle_positions != (0, 1, len(events) - 1):
        return _invalid_codex_observation("thread/turn lifecycle is out of order")
    if any(_reported_failure(event) for event in events):
        return _invalid_codex_observation("Codex reported a failed run")
    thread_event = next(event for event in events if event.get("type") == "thread.started")
    thread_id = thread_event.get("thread_id") or thread_event.get("threadId")
    if not isinstance(thread_id, str) or not thread_id:
        return _invalid_codex_observation("thread start omitted its id")

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
        return _invalid_codex_observation("completed turn omitted its agent response")

    consulted, read_witnesses, read_error = _codex_body_reads(
        events, turn_start, turn_complete, witnesses,
    )
    if read_error:
        return _invalid_codex_observation(read_error, isolation_stop=True)
    selected_marker, selected_skill, marker_error = _codex_selected_marker(
        completed_agent_messages, marker_to_skill, consulted,
    )
    if marker_error:
        return _invalid_codex_observation(marker_error)

    resolved_models = {
        model
        for event in events
        if event.get("type") in {"thread.started", "turn.started"}
        and isinstance((model := event.get("model")), str)
        and model
    }
    if len(resolved_models) > 1:
        return _invalid_codex_observation("Codex reported ambiguous resolved models")
    resolved_model = next(iter(resolved_models), None)
    if requested_model is not None and resolved_model is not None and resolved_model != requested_model:
        result = _invalid_codex_observation("Codex resolved a different model than requested")
        result.update(requested_model=requested_model, resolved_model=resolved_model)
        return result
    selected = selected_skill == target_skill
    sibling_selections = [selected_skill] if selected_skill is not None and not selected else []
    return {
        "valid": True,
        "selected": selected,
        "selected_marker": selected_marker,
        "selected_skill": selected_skill,
        "selected_skill_set": [selected_skill] if selected_skill is not None else [],
        "sibling_selections": sibling_selections,
        "consulted_skills": consulted,
        "read_witnesses": read_witnesses,
        "thread_id": thread_id,
        "requested_model": requested_model,
        "resolved_model": resolved_model,
        "model_identity_check": "exact" if resolved_model is not None else "requested-only",
        "qualification_observed": True,
        "observation_scope": scope,
        "reason": (
            "body-read-attested target selection"
            if selected
            else "body-read-attested sibling selection"
            if selected_skill is not None
            else "consultation without selection"
            if consulted
            else "no skill selection"
        ),
    }
