"""Host-parity generator core: host blocks, derived Codex limits, pairing.

One authored text serves both hosts. Host-specific lines sit in blocks:

    <!-- host:codex -->
    Codex-only text.
    <!-- /host -->

`emit_host` keeps the target host's blocks and drops the other host's. Each
marker must sit alone on its line. Markers count everywhere, including inside
fenced code, so an example of the syntax cannot appear verbatim in a source.
Any unbalanced, nested, unknown-host, or inline marker fails closed.

`derive_codex_enforcement` maps a Claude agent's frontmatter tool policy to
Codex agent-file limits. The live probe under
`tests/speckit-pro/fixtures/codex-enforcement-probe/` found that Codex
0.156.0 applies neither limit from an agent file: the child keeps the
parent's sandbox, and no `enabled_tools` form hides a plugin broker tool. So
`config_keys` emits `sandbox_mode` as a declaration and no `enabled_tools`
key; both limits stay in prose.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .agent_inventory import PLATFORMS


HOSTS = ("claude", "codex")
MUTATION_TOOLS = frozenset({"Write", "Edit", "MultiEdit"})
BROKER_TOOL = re.compile(r"mcp__plugin_speckit-pro_(?P<server>[a-z0-9-]+)__(?P<tool>[a-z0-9_]+)")

_OPEN = re.compile(r"<!-- host:(?P<host>[^ ]*) -->")
_CLOSE = "<!-- /host -->"
_MARKER_HINT = re.compile(r"<!--\s*/?\s*host\b")
_LIST_ITEM = re.compile(r"[^,\s][^,]*")
_FRONTMATTER_KEY = re.compile(r"(?P<key>[A-Za-z][A-Za-z0-9_-]*):(?:\s+(?P<value>.*))?$")


class HostParityError(ValueError):
    """Raised when a source cannot be split or mapped without guessing."""


def _marker(line: str, number: int) -> tuple[str, str | None] | None:
    """Classify one line as an open marker, a close marker, or text."""
    stripped = line.strip()
    opened = _OPEN.fullmatch(stripped)
    if opened:
        host = opened.group("host")
        if host not in HOSTS:
            raise HostParityError(f"line {number}: unknown host {host!r}")
        return ("open", host)
    if stripped == _CLOSE:
        return ("close", None)
    if _MARKER_HINT.search(line):
        raise HostParityError(f"line {number}: a host marker must be on its own line")
    return None


def emit_host(text: str, host: str) -> str:
    """Return `text` as `host` sees it, with marker lines removed."""
    if host not in HOSTS:
        raise HostParityError(f"unknown host {host!r}; expected one of {HOSTS}")
    kept: list[str] = []
    block: str | None = None
    opened_at = 0
    for number, line in enumerate(text.splitlines(keepends=True), start=1):
        marker = _marker(line, number)
        if marker is None:
            if block in (None, host):
                kept.append(line)
        elif marker[0] == "open":
            if block is not None:
                raise HostParityError(f"line {number}: nested host block inside line {opened_at}")
            block, opened_at = marker[1], number
        elif block is None:
            raise HostParityError(f"line {number}: host block close without an open")
        else:
            block = None
    if block is not None:
        raise HostParityError(f"line {opened_at}: unterminated host block")
    return "".join(kept)


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Split a `---` fenced frontmatter into top-level scalar fields and body.

    Indented continuation lines (a folded `description: >`) belong to the key
    above them and are never read as keys.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise HostParityError("frontmatter must open with a --- line")
    fields: dict[str, str] = {}
    for index, line in enumerate(lines[1:], start=1):
        bare = line.rstrip("\r\n")
        if bare == "---":
            return fields, "".join(lines[index + 1 :])
        if not bare.strip() or bare[0] in " \t":
            continue
        match = _FRONTMATTER_KEY.fullmatch(bare)
        if match is None:
            raise HostParityError(f"frontmatter line {index + 1} is not a key: {bare!r}")
        fields[match.group("key")] = (match.group("value") or "").strip()
    raise HostParityError("frontmatter has no closing --- line")


def _tool_list(value: str) -> list[str]:
    return [match.group().rstrip() for match in _LIST_ITEM.finditer(value)]


@dataclass(frozen=True)
class CodexEnforcement:
    """Codex limits derived from one Claude agent's tool policy."""

    sandbox_mode: str
    enabled_tools: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def config_keys(self) -> dict[str, Any]:
        """Agent-file keys to emit. `enabled_tools` has no working form."""
        return {"sandbox_mode": self.sandbox_mode}


def derive_codex_enforcement(fields: dict[str, str]) -> CodexEnforcement:
    """Derive Codex limits from `tools:` or, without it, `disallowedTools:`."""
    if "tools" not in fields:
        denied = set(_tool_list(fields.get("disallowedTools", "")))
        read_only = MUTATION_TOOLS <= denied
        return CodexEnforcement("read-only" if read_only else "workspace-write")

    allowed = _tool_list(fields["tools"])
    if not allowed:
        raise HostParityError("tools: allowlist is empty")
    servers: dict[str, set[str]] = {}
    for tool in allowed:
        if not tool.startswith("mcp__"):
            continue
        match = BROKER_TOOL.fullmatch(tool)
        if match is None:
            raise HostParityError(f"allowlisted MCP tool {tool} is not a speckit-pro broker tool")
        servers.setdefault(match.group("server"), set()).add(match.group("tool"))
    read_only = MUTATION_TOOLS.isdisjoint(allowed)
    return CodexEnforcement(
        "read-only" if read_only else "workspace-write",
        {server: tuple(sorted(tools)) for server, tools in sorted(servers.items())},
    )


@dataclass(frozen=True)
class PairedRole:
    name: str
    claude_source: str
    codex_source: str


@dataclass(frozen=True)
class PairingManifest:
    paired: dict[str, PairedRole]
    claude_only: tuple[str, ...]
    codex_only: tuple[str, ...]


def pairing_manifest(inventory: dict[str, Any]) -> PairingManifest:
    """Classify each inventory role as paired, Claude-only, or Codex-only.

    A role is paired when it ships a Claude plugin agent and a Codex custom
    agent; slice 2 generates its Codex file. Any other shape fails closed.
    """
    paired: dict[str, PairedRole] = {}
    claude_only: list[str] = []
    codex_only: list[str] = []
    for role in inventory["roles"]:
        name = role["name"]
        kinds = tuple(role[platform]["implementation"] for platform in PLATFORMS)
        if kinds == ("plugin_agent", "custom_agent"):
            paired[name] = PairedRole(name, role["claude_code"]["source"], role["codex"]["source"])
        elif kinds == ("plugin_agent", "isolated_prompt_role"):
            claude_only.append(name)
        elif kinds == ("none", "custom_agent"):
            codex_only.append(name)
        else:
            raise HostParityError(f"role {name} has no pairing rule for implementations {kinds}")
    return PairingManifest(paired, tuple(sorted(claude_only)), tuple(sorted(codex_only)))
