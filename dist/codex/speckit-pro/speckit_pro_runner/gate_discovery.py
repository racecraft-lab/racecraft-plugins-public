"""Validate the gate discovery table that fills the quality-gate slots.

The table maps a repository signal to the tool and command for one
PROJECT_COMMANDS slot (COMPLEXITY, MUTATION, DEPENDENCY_RULES). The JSON
schema in ``contracts/gate-discovery-table.schema.json`` documents the shape;
this module enforces the same rules with the standard library only, because
nothing in the plugin validates JSON schema locally.

Usage::

    python3 -m speckit_pro_runner.gate_discovery            # shipped table
    python3 -m speckit_pro_runner.gate_discovery table.json # repository override

Exit 0 when the table is valid, 1 with one violation per line on stderr.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
LANGUAGES = ("python", "typescript")
SLOTS = ("COMPLEXITY", "MUTATION", "DEPENDENCY_RULES")
SIGNAL_KINDS = ("file",)
ROW_FIELDS = ("language", "slot", "signal", "tool", "install", "command")
PLACEHOLDERS = frozenset(
    {"ceiling", "complexity_ceiling", "floor", "survival_ceiling", "rules_path", "paths"}
)
DEFAULT_TABLE = Path(__file__).resolve().parent / "gate_discovery_table.json"

_PLACEHOLDER_RE = re.compile(r"\{([^{}]*)\}")


def load_table(path: Path | None = None) -> Any:
    """Read the shipped table, or ``path`` when given, as parsed JSON."""
    target = DEFAULT_TABLE if path is None else path
    return json.loads(target.read_text(encoding="utf-8"))


def validate_table(data: Any) -> list[str]:
    """Return every violation in ``data``; an empty list means valid."""
    problems: list[str] = []
    if not isinstance(data, dict):
        return ["top level must be an object"]
    extra = sorted(set(data) - {"schema_version", "rows"})
    if extra:
        problems.append("unknown top-level keys: " + ", ".join(extra))
    if data.get("schema_version") != SCHEMA_VERSION:
        problems.append(f"schema_version must be {SCHEMA_VERSION!r}")
    rows = data.get("rows")
    if not isinstance(rows, list) or not rows:
        problems.append("rows must be a non-empty array")
        return problems
    seen: set[tuple[str, str, str]] = set()
    for index, row in enumerate(rows):
        prefix = f"rows[{index}]"
        if not isinstance(row, dict):
            problems.append(f"{prefix}: must be an object")
            continue
        missing = [field for field in ROW_FIELDS if field not in row]
        unknown = sorted(set(row) - set(ROW_FIELDS))
        if missing:
            problems.append(f"{prefix}: missing fields: " + ", ".join(missing))
        if unknown:
            problems.append(f"{prefix}: unknown fields: " + ", ".join(unknown))
        for field in ("tool", "install", "command"):
            value = row.get(field)
            if field in row and (not isinstance(value, str) or not value.strip()):
                problems.append(f"{prefix}.{field}: must be a non-empty string")
        language = row.get("language")
        if "language" in row and language not in LANGUAGES:
            problems.append(f"{prefix}.language: must be one of {', '.join(LANGUAGES)}")
        slot = row.get("slot")
        if "slot" in row and slot not in SLOTS:
            problems.append(f"{prefix}.slot: must be one of {', '.join(SLOTS)}")
        signal_path = _validate_signal(prefix, row.get("signal"), problems) if "signal" in row else None
        command = row.get("command")
        if isinstance(command, str):
            for name in _PLACEHOLDER_RE.findall(command):
                if name not in PLACEHOLDERS:
                    problems.append(
                        f"{prefix}.command: unknown placeholder {{{name}}}; allowed: "
                        + ", ".join(sorted(PLACEHOLDERS))
                    )
        if isinstance(language, str) and isinstance(slot, str) and signal_path is not None:
            key = (language, slot, signal_path)
            if key in seen:
                problems.append(f"{prefix}: duplicate (language, slot, signal.path) {key}")
            seen.add(key)
    return problems


def _validate_signal(prefix: str, signal: Any, problems: list[str]) -> str | None:
    if not isinstance(signal, dict):
        problems.append(f"{prefix}.signal: must be an object")
        return None
    unknown = sorted(set(signal) - {"kind", "path"})
    if unknown:
        problems.append(f"{prefix}.signal: unknown fields: " + ", ".join(unknown))
    if signal.get("kind") not in SIGNAL_KINDS:
        problems.append(f"{prefix}.signal.kind: must be one of {', '.join(SIGNAL_KINDS)}")
    path = signal.get("path")
    if not isinstance(path, str) or not path.strip():
        problems.append(f"{prefix}.signal.path: must be a non-empty string")
        return None
    if path.startswith("/") or ".." in path.split("/"):
        problems.append(f"{prefix}.signal.path: must be repository-relative without '..'")
        return None
    return path


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) > 1:
        print("usage: python3 -m speckit_pro_runner.gate_discovery [table.json]", file=sys.stderr)
        return 2
    path = Path(args[0]) if args else None
    try:
        data = load_table(path)
    except (OSError, ValueError) as exc:
        print(f"cannot read table: {exc}", file=sys.stderr)
        return 1
    problems = validate_table(data)
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
