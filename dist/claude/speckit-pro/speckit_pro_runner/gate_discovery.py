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
OPTIONAL_ROW_FIELDS = ("probe",)
PLACEHOLDERS = frozenset(
    {"ceiling", "complexity_ceiling", "floor", "survival_ceiling", "rules_path", "paths", "plugin_root"}
)
DEFAULT_TABLE = Path(__file__).resolve().parent / "gate_discovery_table.json"
REPO_OVERRIDE = ".specify/gate-discovery.json"
STACK_LANGUAGE = {"python": "python", "nodejs": "typescript"}
# Hard-coded fallbacks. A repository quality-gates.json, once it exists,
# replaces these; until then every populated slot runs against them.
DEFAULT_THRESHOLDS = {
    "ceiling": "30",
    "complexity_ceiling": "8",
    "floor": "60",
    "survival_ceiling": "40",
}

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
        unknown = sorted(set(row) - set(ROW_FIELDS) - set(OPTIONAL_ROW_FIELDS))
        if missing:
            problems.append(f"{prefix}: missing fields: " + ", ".join(missing))
        if unknown:
            problems.append(f"{prefix}: unknown fields: " + ", ".join(unknown))
        for field in ("tool", "install", "command"):
            value = row.get(field)
            if field in row and (not isinstance(value, str) or not value.strip()):
                problems.append(f"{prefix}.{field}: must be a non-empty string")
        probe = row.get("probe")
        if "probe" in row and (
            not isinstance(probe, list)
            or not probe
            or any(not isinstance(name, str) or not name.strip() or "/" in name for name in probe)
        ):
            problems.append(f"{prefix}.probe: must be a non-empty array of bare executable names")
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


def resolve_slots(
    repo_root: Path,
    stack: str,
    *,
    file_exists: Any,
    which: Any,
) -> dict[str, dict[str, Any]]:
    """Fill the quality-gate slots for ``stack`` from the discovery table.

    A repository override at ``.specify/gate-discovery.json`` is consulted
    before the shipped table when it validates; an invalid override is
    reported and ignored. Within one slot the first row whose signal file
    exists wins. Thresholds and ``{rules_path}`` are substituted here;
    ``{paths}`` and ``{plugin_root}`` stay literal because the orchestrator
    fills them at run time, which also keeps machine-specific paths out of
    the recorded workflow file. ``file_exists(path)`` and ``which(name)`` are
    injected so the caller keeps its own trust rules for filesystem access.
    """
    slots: dict[str, dict[str, Any]] = {
        slot: {"status": "unconfigured", "command": "N/A"} for slot in SLOTS
    }
    language = STACK_LANGUAGE.get(stack)
    if language is None:
        return slots
    rows: list[dict[str, Any]] = []
    override_path = repo_root / REPO_OVERRIDE
    if file_exists(override_path):
        try:
            override = load_table(override_path)
        except (OSError, ValueError) as exc:
            override_problems = [f"cannot read table: {exc}"]
        else:
            override_problems = validate_table(override)
        if override_problems:
            for slot_entry in slots.values():
                slot_entry["override_ignored"] = override_problems
        else:
            rows.extend(override["rows"])
    rows.extend(load_table()["rows"])
    for row in rows:
        if row["language"] != language:
            continue
        entry = slots[row["slot"]]
        if entry["status"] == "populated":
            continue
        signal_path = row["signal"]["path"]
        if not file_exists(repo_root / signal_path):
            continue
        command = row["command"]
        for name, value in {**DEFAULT_THRESHOLDS, "rules_path": signal_path}.items():
            command = command.replace("{" + name + "}", value)
        probe = row.get("probe", [])
        entry.update(
            {
                "status": "populated",
                "command": command,
                "tool": row["tool"],
                "install": row["install"],
                "signal": signal_path,
                "tool_present": all(which(name) for name in probe) if probe else None,
            }
        )
    return slots


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
