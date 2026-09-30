"""Parse a Claude stream-json trial into a typed selection observation.

Both the Claude runner and the provider-free comparator replay recorded streams
through this module, so neither has to load the other's script."""
from __future__ import annotations

import json
from pathlib import Path

import trigger_first_selection_guard as first_selection_guard
from trigger_evidence import NO_SPECKIT_SKILL_NAME


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


def first_selection_guard_evidence(
    events: list[dict[str, object]],
    uses: list[tuple[int, dict[str, object]]],
    result_index: int,
    terminal: dict[str, object],
) -> tuple[dict[str, object] | None, str | None]:
    """Validate the native hook receipt that stops a completed Skill selection."""
    hook_events = [
        (index, event)
        for index, event in enumerate(events[:result_index])
        if isinstance(event.get("subtype"), str)
        and str(event["subtype"]).startswith("hook_")
    ]
    if not uses:
        if hook_events or terminal.get("terminal_reason") == "hook_stopped":
            return None, "first-selection guard stop appeared without a Skill selection"
        return {"observed": False}, None
    if len(uses) != 1:
        return None, "first-selection guard requires exactly one Skill selection"

    use_index, use = uses[0]
    tool_use_id = use.get("id")
    if not isinstance(tool_use_id, str) or not tool_use_id:
        return None, "first-selection guard received malformed Skill identity"
    started = [item for item in hook_events if item[1].get("subtype") == "hook_started"]
    responses = [item for item in hook_events if item[1].get("subtype") == "hook_response"]
    progress = [item for item in hook_events if item[1].get("subtype") == "hook_progress"]
    if len(hook_events) != 2 + len(progress) or len(started) != 1 or len(responses) != 1:
        return None, "missing or ambiguous first-selection guard receipt"
    started_index, started_event = started[0]
    response_index, response = responses[0]
    tool_result_index = next(
        index
        for index, event in enumerate(events[:result_index])
        if event.get("type") == "user"
        and any(
            block.get("type") == "tool_result"
            and block.get("tool_use_id") == tool_use_id
            for block in stream_content(event)
        )
    )
    if (
        not use_index < started_index < response_index < tool_result_index < result_index
        or any(not started_index < index < response_index for index, _event in progress)
    ):
        return None, "first-selection guard receipt was out of order"
    if any(
        not isinstance(event.get("stdout"), str)
        or not isinstance(event.get("stderr"), str)
        for _index, event in progress
    ):
        return None, "first-selection guard progress was malformed"
    if any(
        index > use_index and event.get("type") == "assistant"
        for index, event in enumerate(events[:result_index])
    ):
        return None, "assistant activity continued after the Skill selection"

    hook_id = started_event.get("hook_id")
    if (
        started_event.get("type") != "system"
        or response.get("type") != "system"
        or not isinstance(hook_id, str)
        or not hook_id
        or any(
            event.get("type") != "system"
            or event.get("hook_id") != hook_id
            or event.get("hook_name") != first_selection_guard.HOOK_NAME
            or event.get("hook_event") != first_selection_guard.HOOK_EVENT
            for _index, event in hook_events
        )
    ):
        return None, "first-selection guard identity did not match"

    expected_output = json.dumps(
        {
            "continue": False,
            "stopReason": f"{first_selection_guard.RECEIPT_PREFIX}:{tool_use_id}",
        },
        ensure_ascii=True,
        separators=(",", ":"),
    ) + "\n"
    if (
        response.get("outcome") != "success"
        or type(response.get("exit_code")) is not int
        or response.get("exit_code") != 0
        or response.get("stdout") != expected_output
        or response.get("output") != expected_output
        or response.get("stderr") != ""
    ):
        return None, "first-selection guard did not return its exact successful receipt"
    if terminal.get("terminal_reason") != "hook_stopped":
        return None, "Skill selection did not terminate through the first-selection guard"
    return {
        "observed": True,
        "hook_id": hook_id,
        "hook_name": first_selection_guard.HOOK_NAME,
        "hook_event": first_selection_guard.HOOK_EVENT,
        "tool_use_id": tool_use_id,
        "progress_events": len(progress),
        "receipt": expected_output.rstrip("\n"),
    }, None


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


def _claude_nonce_error(
    assistant_events: list[tuple[int, dict[str, object]]],
    intended: list[tuple[int, dict[str, object]]],
    nonce_locations: list[dict[str, object]],
    nonce: str,
) -> str | None:
    if not intended:
        return "target nonce appeared without its native Skill selection" if nonce_locations else None
    if not nonce_locations:
        return None
    if len(nonce_locations) != 1:
        return "selected target emitted multiple nonce attestations"
    location = nonce_locations[0]
    nonce_event = next(event for index, event in assistant_events if index == location["event"])
    nonce_block = stream_content(nonce_event)[int(location["block"])]
    first_lines = [line.strip() for line in str(nonce_block["text"]).splitlines() if line.strip()]
    if location["event"] <= intended[0][0] or not first_lines or first_lines[0] != nonce:
        return "target nonce was not first in a post-selection assistant message"
    return None


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
    if (
        malformed
        or competing
        or len(intended) > 1
        or len(sibling_selections) > 1
        or (intended and sibling_selections)
    ):
        return {
            "valid": False,
            "selected": False,
            "reason": "malformed, competing, or ambiguous Skill selection",
            "nonce_locations": nonce_locations,
        }

    completion_error = skill_results_error(events, skill_uses, init_index, result_index)
    if completion_error:
        return {"valid": False, "selected": False, "reason": completion_error, "nonce_locations": nonce_locations}
    guard_evidence, guard_error = first_selection_guard_evidence(
        events, skill_uses, result_index, result
    )
    if guard_error:
        return {
            "valid": False,
            "selected": False,
            "reason": guard_error,
            "nonce_locations": nonce_locations,
        }
    model_evidence = claude_model_evidence(events, init, requested_model)
    if model_evidence["model_identity_check"] == "conflict":
        return {"valid": False, "selected": False, "reason": "Claude reported a conflicting model identity", **model_evidence}
    selected = len(intended) == 1
    selected_id = str(intended[0][1]["id"]) if selected else None
    nonce_error = _claude_nonce_error(assistant_events, intended, nonce_locations, nonce)
    if nonce_error:
        return {
            "valid": False,
            "selected": False,
            "reason": nonce_error,
            "nonce_locations": nonce_locations,
            **model_evidence,
        }
    selected_skill = expected_skill if selected else sibling_selections[0] if sibling_selections else None
    return {
        "valid": True,
        "selected": selected,
        "selected_skill": selected_skill,
        "selected_skill_set": [selected_skill] if selected_skill is not None else [],
        "selected_tool_use_id": selected_id,
        "nonce_locations": nonce_locations,
        "sibling_selections": sibling_selections,
        "first_selection_guard": guard_evidence,
        **model_evidence,
        "qualification_observed": True,
        "observation_scope": "claude-native-skill-tool",
        "reason": (
            "exact completed Skill selection" if selected
            else "sibling Skill selection" if sibling_selections
            else "no Skill selection"
        ),
    }
