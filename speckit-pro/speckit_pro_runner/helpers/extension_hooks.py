"""The optional hooks a project registers for Spec Kit events, read from `.specify/extensions.yml`.

Spec Kit writes this file as block YAML: `hooks:`, then one key per event, then a
list of entries. The standard library has no YAML reader, so this module reads
only that shape and fails closed on anything else, naming the line. Mandatory
hooks are never returned: the loaded upstream command runs those itself.

Quoted values keep their type: a quoted `"true"` is text, not a boolean, and a
quoted `"null"` is a condition, not an absent one. A hook condition is run the
way Spec Kit v1.1.0 runs it for `env.NAME is set` and `env.NAME ==|!= 'value'`;
any other condition raises, so a registration is never lost without a word.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from ..trusted_io import trusted_text

HOOK_FILE = ".specify/extensions.yml"
DEFAULT_PRIORITY = 10
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
FIELD = re.compile(r"^( *)([A-Za-z_][\w-]*):[ \t]*(.*)$")
ITEM = re.compile(r"^( *)-( +)([A-Za-z_][\w-]*):[ \t]*(.*)$")
EMPTY_VALUES = frozenset({"", "null", "~"})
CLOSING_QUOTE_TAIL = re.compile(r"(?:[ \t]+#.*)?[ \t]*")
ENV_SET = re.compile(r"env\.([A-Za-z0-9_]+)\s+is\s+set", re.IGNORECASE)
ENV_COMPARE = re.compile(r"""env\.([A-Za-z0-9_]+)\s*(==|!=)\s*["']([^"']+)["']""", re.IGNORECASE)


def parse_scalar(raw: str) -> tuple[str, bool]:
    """One YAML scalar and whether it was quoted; malformed quoting raises."""
    text = raw.strip()
    if text[:1] not in {'"', "'"}:
        return re.sub(r"[ \t]+#.*$", "", text).strip(), False
    quote, out, index = text[0], [], 1
    while index < len(text):
        char = text[index]
        if char == quote:
            if quote == "'" and text[index + 1 : index + 2] == "'":
                out.append("'")
                index += 2
                continue
            if CLOSING_QUOTE_TAIL.fullmatch(text[index + 1 :]) is None:
                raise ValueError("text follows a closing quote")
            return "".join(out), True
        if quote == '"' and char == "\\":
            following = text[index + 1 : index + 2]
            if following not in {'"', "\\"}:
                raise ValueError("unsupported escape in a quoted value")
            out.append(following)
            index += 2
            continue
        out.append(char)
        index += 1
    raise ValueError("unterminated quoted value")


def scalar(raw: str) -> str:
    return parse_scalar(raw)[0]


def flag(fields: dict[str, str], name: str) -> bool:
    """A true/false field that Spec Kit defaults to true when absent; a quoted value is text, so it raises."""
    value, quoted = parse_scalar(fields.get(name, "true"))
    if quoted or value.lower() not in {"true", "false"}:
        raise ValueError(f"{name} must be an unquoted true or false")
    return value.lower() == "true"


def condition_met(fields: dict[str, str]) -> bool:
    """True when the entry has no condition or its env condition holds; any other condition raises."""
    text, quoted = parse_scalar(fields.get("condition", ""))
    if text.strip() == "" or (text in EMPTY_VALUES and not quoted):
        return True
    if (match := ENV_SET.fullmatch(text.strip())) is not None:
        return match[1].upper() in os.environ
    if (match := ENV_COMPARE.fullmatch(text.strip())) is not None:
        return (os.environ.get(match[1].upper(), "") == match[3]) == (match[2] == "==")
    raise ValueError("condition is not one the runner evaluates (env.NAME is set, env.NAME == or != 'value')")


def hook_entries(text: str, event: str) -> list[tuple[int, dict[str, str]]]:
    """Each entry's line number and top-level fields under `hooks.<event>`, in file order."""
    entries: list[tuple[int, dict[str, str]]] = []
    in_hooks = in_event = False
    event_indent: int | None = None
    dash_indent = field_indent = -1
    current_field = ""
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" in line[: len(line) - len(line.lstrip())]:
            raise ValueError(f"{HOOK_FILE} line {number}: indentation must use spaces")
        indent = len(line) - len(line.lstrip(" "))
        if indent == 0 and not line.startswith("- "):
            if FIELD.match(line) is None:
                raise ValueError(f"{HOOK_FILE} line {number}: expected a top-level key")
            in_hooks = line.split(":", 1)[0] == "hooks"
            in_event = False
            rest = scalar(line.split(":", 1)[1])
            if in_hooks and rest not in {"", "{}"}:
                raise ValueError(f"{HOOK_FILE} line {number}: hooks must be a mapping of events")
            continue
        if not in_hooks:
            continue
        if indent == 0:
            raise ValueError(f"{HOOK_FILE} line {number}: hooks must be a mapping of events")
        if not line.lstrip().startswith("- ") and (event_indent is None or indent == event_indent):
            match = FIELD.match(line)
            if match is None:
                raise ValueError(f"{HOOK_FILE} line {number}: expected an event name")
            event_indent = indent
            name, value = match[2], scalar(match[3])
            in_event = name == event
            if value not in {"", "[]"}:
                raise ValueError(f"{HOOK_FILE} line {number}: {name} must be a list of hook entries")
            continue
        if not in_event:
            continue
        item = ITEM.match(line)
        if item is not None and (not entries or indent <= dash_indent):
            dash_indent, field_indent = indent, len(item[1]) + 1 + len(item[2])
            current_field = item[3]
            entries.append((number, {item[3]: item[4]}))
            continue
        field = FIELD.match(line)
        if not entries or indent < field_indent or (indent == field_indent and field is None):
            raise ValueError(f"{HOOK_FILE} line {number}: expected a hook entry")
        if indent == field_indent and field is not None:
            current_field = field[2]
            entries[-1][1][field[2]] = field[3]
        elif current_field not in {"description", "prompt"}:
            raise ValueError(f"{HOOK_FILE} line {number}: {current_field} must be a single-line scalar")
    return entries


def entry_hook(fields: dict[str, str]) -> tuple[int, dict[str, str]] | None:
    """Priority and the {extension, command} record for an entry that should be listed; None when it should not."""
    extension, command = scalar(fields.get("extension", "")), scalar(fields.get("command", ""))
    if not IDENTIFIER.fullmatch(extension) or not IDENTIFIER.fullmatch(command):
        raise ValueError("extension and command must be plain ids")
    try:
        priority = int(scalar(fields.get("priority", str(DEFAULT_PRIORITY))))
    except ValueError:
        raise ValueError("priority must be an integer") from None
    enabled, optional = flag(fields, "enabled"), flag(fields, "optional")
    if enabled and optional and condition_met(fields):
        return priority, {"extension": extension, "command": command}
    return None


def optional_hooks(root: Path, events: tuple[str, ...]) -> list[dict[str, str]]:
    """Enabled optional hooks whose condition holds, per event in the order given, lowest priority number first.

    A hook registered under several events is listed once, at its first place.
    A missing file means no hooks. A file the runner cannot read or interpret
    raises ValueError so the caller never guesses.
    """
    path = root / HOOK_FILE
    text = trusted_text(path, root)
    if text is None:
        if os.path.lexists(path):
            raise ValueError(f"{HOOK_FILE} is not a readable regular file inside the project")
        return []
    listed: list[dict[str, str]] = []
    for event in events:
        ranked: list[tuple[int, dict[str, str]]] = []
        for number, fields in hook_entries(text, event):
            try:
                found = entry_hook(fields)
            except ValueError as exc:
                raise ValueError(f"{HOOK_FILE} entry at line {number}: {exc}") from None
            if found is not None:
                ranked.append(found)
        listed.extend(hook for _, hook in sorted(ranked, key=lambda pair: pair[0]) if hook not in listed)
    return listed
