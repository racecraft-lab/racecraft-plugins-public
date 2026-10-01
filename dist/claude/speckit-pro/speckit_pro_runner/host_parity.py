"""Host-parity generator core: host blocks, derived Codex limits, pairing.

One authored text serves both hosts. Host-specific lines sit in blocks:

    <!-- host:codex: why Codex needs its own text -->
    Codex-only text.
    <!-- /host -->

The reason after the second colon is optional in the grammar;
`unexplained_blocks` lists the open markers that lack one, so a check can
require a reason for every divergence. `emit_host` keeps the target host's
blocks and drops the other host's. Each marker must sit alone on its line. Markers count everywhere, including inside
fenced code, so an example of the syntax cannot appear verbatim in a source.
Any unbalanced, nested, unknown-host, or inline marker fails closed.

`derive_codex_enforcement` maps a Claude agent's frontmatter tool policy to
Codex limits. The live probe under
`tests/speckit-pro/fixtures/codex-enforcement-probe/` (Codex 0.156.0) found:

- An agent file's `sandbox_mode` is advisory. A spawned agent keeps the
  parent's sandbox, so `advisory_config_keys` never enforces anything.
- No `enabled_tools` form in an agent file hides a plugin broker tool, so no
  such key is emitted.
- A project `PreToolUse` hook sees the calling agent's `agent_type` and can
  deny its `apply_patch` edits and its MCP calls. `derive_codex_hook_policy`
  states that per-role policy. Shell writes cannot be told apart from shell
  reads by a hook, so a read-only role's shell writes stay a prose rule.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .agent_inventory import PLATFORMS


HOSTS = ("claude", "codex")
MUTATION_TOOLS = frozenset({"Write", "Edit", "MultiEdit"})
BROKER_TOOL = re.compile(r"mcp__plugin_speckit-pro_(?P<server>[a-z0-9-]+)__(?P<tool>[a-z0-9_]+)")

_OPEN = re.compile(r"<!-- host:(?P<host>[^ :]*)(?:: (?P<reason>[^<>]*[^<>\s]))? -->")
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


def unexplained_blocks(text: str) -> list[int]:
    """Return the line numbers of open markers that give no reason."""
    emit_host(text, HOSTS[0])
    return [
        number
        for number, line in enumerate(text.splitlines(), start=1)
        if (opened := _OPEN.fullmatch(line.strip())) and opened.group("reason") is None
    ]


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Split a `---` fenced frontmatter into top-level scalar fields and body.

    Indented continuation lines belong to the key above them and are never
    read as keys. A folded `key: >` value is joined with single spaces, as
    YAML folds it; any other block value keeps its raw indicator.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise HostParityError("frontmatter must open with a --- line")
    for index, line in enumerate(lines[1:], start=1):
        if line.rstrip("\r\n") == "---":
            return _frontmatter_fields(lines[1:index]), "".join(lines[index + 1 :])
    raise HostParityError("frontmatter has no closing --- line")


def _frontmatter_fields(lines: list[str]) -> dict[str, str]:
    fields: dict[str, str] = {}
    folded: dict[str, list[str]] = {}
    key = ""
    for number, line in enumerate(lines, start=2):
        bare = line.rstrip("\r\n")
        if not bare.strip() or bare[0] in " \t":
            if key in folded and bare.strip():
                folded[key].append(bare.strip())
            continue
        match = _FRONTMATTER_KEY.fullmatch(bare)
        if match is None:
            raise HostParityError(f"frontmatter line {number} is not a key: {bare!r}")
        key = match.group("key")
        fields[key] = (match.group("value") or "").strip()
        if fields[key] == ">":
            folded[key] = []
    fields.update({name: " ".join(parts) for name, parts in folded.items()})
    return fields


def _tool_list(value: str) -> list[str]:
    return [match.group().rstrip() for match in _LIST_ITEM.finditer(value)]


@dataclass(frozen=True)
class CodexEnforcement:
    """Codex limits derived from one Claude agent's tool policy."""

    sandbox_mode: str
    # Broker tools per server; None when the role has no `tools:` allowlist.
    enabled_tools: dict[str, tuple[str, ...]] | None = None

    def advisory_config_keys(self) -> dict[str, Any]:
        """Agent-file keys to emit. They document intent and enforce nothing:
        the parent's sandbox wins, and `enabled_tools` has no working form."""
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


FILE_EDIT_TOOL = "apply_patch"
# Plugin-relative path of the generated per-role policy the hook applies.
CODEX_HOOK_POLICY_FILE = "speckit_pro_runner/codex_agent_policy.json"


def codex_mcp_tool_name(server: str, tool: str) -> str:
    """Codex's hook name for a plugin MCP tool; it turns `-` into `_`."""
    return f"mcp__{server.replace('-', '_')}__{tool}"


@dataclass(frozen=True)
class CodexHookPolicy:
    """What a Codex `PreToolUse` hook denies for one agent type."""

    agent_type: str
    deny_file_edits: bool
    # Every MCP tool outside this tuple is denied; None leaves MCP tools alone.
    allowed_mcp_tools: tuple[str, ...] | None

    def denies(self, agent_type: str | None, tool_name: str) -> bool:
        """Decide one call. A call from another agent or the parent passes."""
        if agent_type != self.agent_type:
            return False
        if tool_name == FILE_EDIT_TOOL:
            return self.deny_file_edits
        if tool_name.startswith("mcp__") and self.allowed_mcp_tools is not None:
            return tool_name not in self.allowed_mcp_tools
        return False


def _policy_entry(name: str, entry: Any) -> CodexHookPolicy:
    if not isinstance(entry, dict) or not isinstance(entry.get("deny_file_edits"), bool):
        raise HostParityError(f"codex agent policy for {name!r} is malformed")
    allowed = entry.get("allowed_mcp_tools")
    if allowed is not None and not (isinstance(allowed, list) and all(isinstance(tool, str) for tool in allowed)):
        raise HostParityError(f"codex agent policy for {name!r} has a malformed MCP allowlist")
    return CodexHookPolicy(name, entry["deny_file_edits"], None if allowed is None else tuple(allowed))


def load_codex_hook_policies(text: str) -> dict[str, CodexHookPolicy]:
    """Parse the generated policy file; fail closed on any shape it does not know."""
    document = json.loads(text)
    if not isinstance(document, dict) or document.get("schema_version") != 1 or not isinstance(document.get("roles"), dict):
        raise HostParityError("codex agent policy has an unknown shape")
    return {name: _policy_entry(name, entry) for name, entry in document["roles"].items()}


def codex_hook_denial(payload: dict[str, Any], policies: dict[str, CodexHookPolicy]) -> str | None:
    """The deny reason for one `PreToolUse` payload, or None to let the call run.

    Only a spawned agent's payload carries `agent_type`; the parent's never
    does, so the parent's own calls always pass.
    """
    agent_type = payload.get("agent_type")
    tool_name = payload.get("tool_name")
    policy = policies.get(agent_type) if isinstance(agent_type, str) else None
    if policy is None or not isinstance(tool_name, str) or not policy.denies(agent_type, tool_name):
        return None
    # Codex appends its own period and the call details after the reason.
    if tool_name == FILE_EDIT_TOOL:
        return f"{agent_type} is read-only on Codex: it may not edit files with {FILE_EDIT_TOOL}"
    return f"{agent_type} may call only its allowlisted MCP tools; {tool_name} is not one of them"


def derive_codex_hook_policy(agent_type: str, enforcement: CodexEnforcement) -> CodexHookPolicy:
    """Turn derived limits into the hook policy a probe showed Codex enforces."""
    allowed = None
    if enforcement.enabled_tools is not None:
        allowed = tuple(
            codex_mcp_tool_name(server, tool)
            for server, tools in enforcement.enabled_tools.items()
            for tool in tools
        )
    return CodexHookPolicy(agent_type, enforcement.sandbox_mode == "read-only", allowed)


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
