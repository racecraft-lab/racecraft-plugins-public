"""The optional hooks a project registers for one Spec Kit event, read from `.specify/extensions.yml`.

Spec Kit writes this file as block YAML: `hooks:`, then one key per event, then a
list of entries. The standard library has no YAML reader, so this module reads
only that shape and fails closed on anything else, naming the line. Mandatory
hooks are never returned: the loaded upstream command runs those itself.
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
ITEM = re.compile(r"^( *)- ([A-Za-z_][\w-]*):[ \t]*(.*)$")
EMPTY_VALUES = frozenset({"", "null", "~"})


def scalar(raw: str) -> str:
    """One plain or quoted YAML scalar, without its quotes or trailing comment."""
    text = raw.strip()
    if text[:1] in {'"', "'"}:
        quote = text[0]
        end = text.find(quote, 1)
        return text[1:end] if end > 0 else text[1:]
    return re.sub(r"[ \t]+#.*$", "", text).strip()


def flag(fields: dict[str, str], name: str, where: str) -> bool:
    """A true/false field that Spec Kit defaults to true when absent."""
    value = scalar(fields.get(name, "true")).lower()
    if value not in {"true", "false"}:
        raise ValueError(f"{HOOK_FILE} {where}: {name} must be true or false")
    return value == "true"


def hook_entries(text: str, event: str) -> list[tuple[int, dict[str, str]]]:
    """Each entry's line number and top-level fields under `hooks.<event>`, in file order."""
    entries: list[tuple[int, dict[str, str]]] = []
    in_hooks = in_event = False
    event_indent: int | None = None
    dash_indent = -1
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
            dash_indent = indent
            entries.append((number, {item[2]: item[3]}))
            continue
        field = FIELD.match(line)
        if field is not None and indent == dash_indent + 2:
            entries[-1][1][field[2]] = field[3]
        elif indent <= dash_indent + 2:
            raise ValueError(f"{HOOK_FILE} line {number}: expected a hook entry field")
    return entries


def optional_hooks(root: Path, event: str) -> list[dict[str, str]]:
    """Enabled, unconditional, optional hooks for `event`, lowest priority number first.

    A missing file means no hooks. A file the runner cannot read, or reads but
    cannot interpret, raises ValueError so the caller never guesses.
    """
    path = root / HOOK_FILE
    text = trusted_text(path, root)
    if text is None:
        if os.path.lexists(path):
            raise ValueError(f"{HOOK_FILE} is not a readable regular file inside the project")
        return []
    ranked: list[tuple[int, dict[str, str]]] = []
    for number, fields in hook_entries(text, event):
        where = f"entry at line {number}"
        extension, command = scalar(fields.get("extension", "")), scalar(fields.get("command", ""))
        if not IDENTIFIER.fullmatch(extension) or not IDENTIFIER.fullmatch(command):
            raise ValueError(f"{HOOK_FILE} {where}: extension and command must be plain ids")
        try:
            priority = int(scalar(fields.get("priority", str(DEFAULT_PRIORITY))))
        except ValueError:
            raise ValueError(f"{HOOK_FILE} {where}: priority must be an integer") from None
        enabled, optional = flag(fields, "enabled", where), flag(fields, "optional", where)
        if enabled and optional and scalar(fields.get("condition", "")).lower() in EMPTY_VALUES:
            ranked.append((priority, {"extension": extension, "command": command}))
    return [hook for _, hook in sorted(ranked, key=lambda pair: pair[0])]
