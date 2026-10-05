"""ADR 0001 checks shared by structural and synthetic adapter tests."""

from __future__ import annotations

from collections.abc import Sequence
import re
import tomllib


_FORBIDDEN = re.compile(
    r"\b(?:taskcreate|taskget|taskupdate|tasklist|todowrite|update_plan|claude_code_enable_tasks)(?:\b|_)"
)


def forbidden_task_tools(value: object) -> list[str]:
    """Match decoded strings and mapping keys without introducing escape sequences."""
    if isinstance(value, str):
        return _FORBIDDEN.findall(value.casefold())
    if isinstance(value, dict):
        return forbidden_task_tools(list(value)) + forbidden_task_tools(list(value.values()))
    if isinstance(value, (list, tuple)):
        return [match for item in value for match in forbidden_task_tools(item)]
    return []


def codex_config_overrides(command: Sequence[str]) -> list[dict[str, object]]:
    """Decode emitted TOML overrides, failing on missing or malformed values."""
    overrides = []
    arguments = iter(command)
    for argument in arguments:
        if argument in {"--config", "-c"}:
            try:
                value = next(arguments)
            except StopIteration as exc:
                raise ValueError("missing Codex configuration override") from exc
        elif argument.startswith(("--config=", "-c=")):
            value = argument.split("=", 1)[1]
        else:
            continue
        overrides.append(tomllib.loads(value))
    return overrides
