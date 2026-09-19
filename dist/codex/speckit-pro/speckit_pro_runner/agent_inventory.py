"""Validated, versioned inventory of shipped cross-client agent roles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


AGENT_INVENTORY_PATH = Path(__file__).with_name("agent_inventory.json")
SCHEMA_VERSION = "1.0.0"
PLATFORMS = ("claude_code", "codex")
CATEGORIES = frozenset({"shared", "sweep_security", "optional_helper"})
IMPLEMENTATIONS = frozenset({"plugin_agent", "custom_agent", "isolated_prompt_role", "none"})
INSTALL_STATUSES = frozenset({"required", "optional", "not_installed"})
ROLE_KEYS = frozenset({"name", "category", "exception_reason", *PLATFORMS})
PLATFORM_KEYS = frozenset(
    {"implementation", "source", "install_status", "order", "model", "effort", "sandbox", "memory"}
)


class AgentInventoryError(ValueError):
    """Raised when the checked-in agent inventory is incomplete or ambiguous."""


def load_agent_inventory(path: Path = AGENT_INVENTORY_PATH) -> dict[str, Any]:
    """Load and fail closed on malformed, duplicate, or unexplained role entries."""
    try:
        inventory = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AgentInventoryError(f"could not load agent inventory {path}: {exc}") from exc

    if not isinstance(inventory, dict) or set(inventory) != {"schema_version", "roles"}:
        raise AgentInventoryError("agent inventory must contain exactly schema_version and roles")
    if inventory["schema_version"] != SCHEMA_VERSION:
        raise AgentInventoryError(
            f"unsupported agent inventory schema_version: {inventory['schema_version']!r}"
        )
    roles = inventory["roles"]
    if not isinstance(roles, list) or not roles:
        raise AgentInventoryError("agent inventory roles must be a non-empty list")

    names: set[str] = set()
    orders: dict[tuple[str, str], set[int]] = {}
    for index, role in enumerate(roles):
        if not isinstance(role, dict) or set(role) != ROLE_KEYS:
            raise AgentInventoryError(f"role {index} must contain exactly {sorted(ROLE_KEYS)}")
        name = role["name"]
        if not isinstance(name, str) or not name or name in names:
            raise AgentInventoryError(f"role {index} has a missing or duplicate name: {name!r}")
        names.add(name)
        category = role["category"]
        if category not in CATEGORIES:
            raise AgentInventoryError(f"role {name} has unsupported category: {category!r}")
        reason = role["exception_reason"]
        if category == "shared" and reason is not None:
            raise AgentInventoryError(f"shared role {name} must not declare an exception")
        if category != "shared" and (not isinstance(reason, str) or not reason.strip()):
            raise AgentInventoryError(f"platform-specific role {name} requires an exception_reason")

        for platform in PLATFORMS:
            record = role[platform]
            if not isinstance(record, dict) or set(record) != PLATFORM_KEYS:
                raise AgentInventoryError(
                    f"role {name} platform {platform} must contain exactly {sorted(PLATFORM_KEYS)}"
                )
            implementation = record["implementation"]
            status = record["install_status"]
            if implementation not in IMPLEMENTATIONS or status not in INSTALL_STATUSES:
                raise AgentInventoryError(
                    f"role {name} platform {platform} has unsupported implementation or install status"
                )
            source = record["source"]
            if implementation == "none":
                if source is not None or status != "not_installed":
                    raise AgentInventoryError(
                        f"role {name} platform {platform} implementation none must be not_installed without source"
                    )
            elif not isinstance(source, str) or not source:
                raise AgentInventoryError(f"role {name} platform {platform} requires a source path")
            order = record["order"]
            if status == "not_installed":
                if order is not None:
                    raise AgentInventoryError(
                        f"role {name} platform {platform} not_installed entry must not have order"
                    )
            elif not isinstance(order, int) or order < 0:
                raise AgentInventoryError(
                    f"role {name} platform {platform} installed entry requires a non-negative order"
                )
            else:
                order_key = (platform, status)
                used_orders = orders.setdefault(order_key, set())
                if order in used_orders:
                    raise AgentInventoryError(
                        f"role {name} platform {platform} duplicates {status} order {order}"
                    )
                used_orders.add(order)

        _validate_role_shape(role)
    return inventory


def _validate_role_shape(role: dict[str, Any]) -> None:
    name = role["name"]
    category = role["category"]
    claude = role["claude_code"]
    codex = role["codex"]
    if category == "shared":
        if (claude["implementation"], claude["install_status"]) != ("plugin_agent", "required"):
            raise AgentInventoryError(f"shared role {name} must be a required Claude plugin agent")
        if (codex["implementation"], codex["install_status"]) != ("custom_agent", "required"):
            raise AgentInventoryError(f"shared role {name} must be a required Codex custom agent")
    elif category == "sweep_security":
        if (claude["implementation"], claude["install_status"]) != ("plugin_agent", "required"):
            raise AgentInventoryError(f"sweep role {name} must be a required Claude plugin agent")
        if (codex["implementation"], codex["install_status"]) != (
            "isolated_prompt_role",
            "not_installed",
        ):
            raise AgentInventoryError(f"sweep role {name} must remain a non-installed Codex prompt role")
    elif (claude["implementation"], claude["install_status"]) != ("none", "not_installed") or (
        codex["implementation"], codex["install_status"]
    ) != ("custom_agent", "optional"):
        raise AgentInventoryError(
            f"optional helper {name} must be absent on Claude and optional on Codex"
        )


def platform_agent_names(
    inventory: dict[str, Any], platform: str, install_status: str
) -> tuple[str, ...]:
    """Return one platform roster in its stable installation order."""
    if platform not in PLATFORMS or install_status not in INSTALL_STATUSES:
        raise AgentInventoryError(f"unsupported platform or install status: {platform}/{install_status}")
    selected = [
        (role[platform]["order"], role["name"])
        for role in inventory["roles"]
        if role[platform]["install_status"] == install_status
    ]
    return tuple(name for _, name in sorted(selected))


def inventory_source_errors(plugin_root: Path, inventory: dict[str, Any]) -> list[str]:
    """Return closed-world source-roster errors for authored agent definitions."""
    errors: list[str] = []
    expected_agent_files = {
        platform: {
            role[platform]["source"]
            for role in inventory["roles"]
            if role[platform]["implementation"] in {"plugin_agent", "custom_agent"}
        }
        for platform in PLATFORMS
    }
    discovered_agent_files = {
        "claude_code": {
            path.relative_to(plugin_root).as_posix()
            for path in (plugin_root / "agents").glob("*.md")
            if path.is_file()
        },
        "codex": {
            path.relative_to(plugin_root).as_posix()
            for path in (plugin_root / "codex-agents").glob("*.toml")
            if path.is_file()
        },
    }
    for platform in PLATFORMS:
        missing = sorted(expected_agent_files[platform] - discovered_agent_files[platform])
        unexpected = sorted(discovered_agent_files[platform] - expected_agent_files[platform])
        if missing:
            errors.append(f"{platform} missing agent sources: {', '.join(missing)}")
        if unexpected:
            errors.append(f"{platform} unexpected agent sources: {', '.join(unexpected)}")

    for role in inventory["roles"]:
        for platform in PLATFORMS:
            source = role[platform]["source"]
            if source is None:
                continue
            path = plugin_root / source
            if not path.is_file() or path.is_symlink():
                errors.append(
                    f"{role['name']} {platform} source must be a regular file: {source}"
                )
    return errors


AGENT_INVENTORY = load_agent_inventory()
CLAUDE_REQUIRED_AGENT_NAMES = platform_agent_names(AGENT_INVENTORY, "claude_code", "required")
CODEX_REQUIRED_AGENT_NAMES = platform_agent_names(AGENT_INVENTORY, "codex", "required")
CODEX_OPTIONAL_AGENT_NAMES = platform_agent_names(AGENT_INVENTORY, "codex", "optional")
