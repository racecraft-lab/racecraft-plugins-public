"""Generate each paired role's Codex agent TOML from its Claude agent source.

A paired role's `agents/<name>.md` is its only authored source. The Codex
file takes:

- `name` and `description` from the Claude frontmatter;
- `model` and `model_reasoning_effort` from the inventory's Codex record;
- `sandbox_mode` derived from the Claude tool policy. The key is advisory
  (see `host_parity`), and the inventory's `codex.sandbox` must equal it;
- `developer_instructions` from the Claude body as Codex sees it
  (`emit_host(body, "codex")`).

It also writes `speckit_pro_runner/codex_agent_policy.json`, each paired
role's `PreToolUse` policy, which `scripts/codex-agent-policy-hook.py` applies.

`scripts/refresh-release-artifacts.py` writes the files; its `--check` mode
fails when a committed file differs from what this module renders.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

from .host_parity import (
    CODEX_HOOK_POLICY_FILE,
    HostParityError,
    derive_codex_enforcement,
    derive_codex_hook_policy,
    emit_host,
    pairing_manifest,
    split_frontmatter,
)


GENERATED_NOTICE = (
    "# Generated from {source} by scripts/refresh-release-artifacts.py.\n"
    "# Edit the source; a hand edit here fails the generated-artifact check.\n"
)


def _basic_string(value: str) -> str:
    """One-line TOML basic string."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _multiline_string(value: str) -> str:
    """TOML multi-line basic string that keeps plain quotes readable."""
    escaped = value.replace("\\", "\\\\").replace('"""', '""\\"')
    if escaped.endswith('"'):
        escaped = escaped[:-1] + '\\"'
    return f'"""\n{escaped}"""'


def render_codex_agent(name: str, claude_text: str, codex_record: dict[str, Any], source: str) -> str:
    """Render one Codex agent file; fail closed on any source it cannot map."""
    fields, body = split_frontmatter(claude_text)
    if fields.get("name") != name:
        raise HostParityError(f"{source}: frontmatter name {fields.get('name')!r} is not {name!r}")
    description = fields.get("description", "")
    if not description or description == ">":
        raise HostParityError(f"{source}: frontmatter has no description")
    sandbox = derive_codex_enforcement(fields).advisory_config_keys()["sandbox_mode"]
    if codex_record["sandbox"] != sandbox:
        raise HostParityError(
            f"{name}: inventory codex.sandbox {codex_record['sandbox']!r} differs from "
            f"{sandbox!r}, derived from the tool policy in {source}"
        )
    instructions = emit_host(body.lstrip("\n"), "codex")
    values = {
        "name": name,
        "description": description,
        "model": codex_record["model"],
        "model_reasoning_effort": codex_record["effort"],
        "sandbox_mode": sandbox,
        "developer_instructions": instructions,
    }
    lines = [f"{key} = {_basic_string(value)}" for key, value in values.items() if key != "developer_instructions"]
    text = GENERATED_NOTICE.format(source=source) + "\n".join(lines)
    text += f"\ndeveloper_instructions = {_multiline_string(instructions)}\n"
    if tomllib.loads(text) != values:
        raise HostParityError(f"{name}: rendered TOML does not parse back to its source values")
    return text


def render_codex_hook_policy(sources: dict[str, str]) -> str:
    """Render the per-role hook policy from each paired role's Claude source text."""
    roles = {}
    for name, claude_text in sorted(sources.items()):
        fields, _ = split_frontmatter(claude_text)
        policy = derive_codex_hook_policy(name, derive_codex_enforcement(fields))
        roles[name] = {
            "deny_file_edits": policy.deny_file_edits,
            "allowed_mcp_tools": None if policy.allowed_mcp_tools is None else list(policy.allowed_mcp_tools),
        }
    document = {
        "generated_from": "agents/*.md by scripts/refresh-release-artifacts.py",
        "schema_version": 1,
        "roles": roles,
    }
    return json.dumps(document, indent=2) + "\n"


def generated_codex_files(plugin_root: Path, inventory: dict[str, Any]) -> dict[str, str]:
    """Map each generated Codex file's plugin-relative path to its rendered text."""
    records = {role["name"]: role["codex"] for role in inventory["roles"]}
    rendered: dict[str, str] = {}
    sources: dict[str, str] = {}
    for name, role in sorted(pairing_manifest(inventory).paired.items()):
        sources[name] = (plugin_root / role.claude_source).read_text(encoding="utf-8")
        rendered[role.codex_source] = render_codex_agent(
            name, sources[name], records[name], role.claude_source
        )
    rendered[CODEX_HOOK_POLICY_FILE] = render_codex_hook_policy(sources)
    return rendered


def refresh_codex_agents(plugin_root: Path, inventory: dict[str, Any]) -> list[str]:
    """Write every generated Codex file; return the paths that changed."""
    changed: list[str] = []
    for relative, text in generated_codex_files(plugin_root, inventory).items():
        target = plugin_root / relative
        if target.is_file() and target.read_text(encoding="utf-8") == text:
            continue
        target.write_text(text, encoding="utf-8")
        changed.append(f"speckit-pro/{relative}")
    return changed
