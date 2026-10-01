"""Agent roster facts derived from the authoritative agent inventory.

Validators call these instead of restating sandbox, profile, and host-scope
facts by hand, so a new inventory role needs no second edit.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_PLUGIN_ROOT = Path(__file__).resolve().parents[3] / "speckit-pro"
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))

from speckit_pro_runner.agent_inventory import AGENT_INVENTORY  # noqa: E402

# Roles whose prompt is skill-driven or a bounded rule-applier, so they carry no
# capability-discovery pointer on either host. This is policy, not an inventory fact.
CAPABILITY_POINTER_EXEMPT = frozenset(
    {"consensus-synthesizer", "consensus-tiebreaker", "phase-executor"}
)


def _roles(inventory: dict[str, Any], host: str, implementation: str, *, same: bool) -> list[dict[str, Any]]:
    """Roles whose ``host`` implementation equals (``same``) or differs from ``implementation``."""
    return [
        role for role in inventory["roles"]
        if (role[host]["implementation"] == implementation) == same
    ]


def codex_sandbox_policy(inventory: dict[str, Any] = AGENT_INVENTORY) -> dict[str, str]:
    """Sandbox mode of every role shipped as a Codex custom agent."""
    return {
        role["name"]: role["codex"]["sandbox"]
        for role in _roles(inventory, "codex", "custom_agent", same=True)
    }


def claude_only_roles(inventory: dict[str, Any] = AGENT_INVENTORY) -> frozenset[str]:
    """Roles with a Claude agent but no Codex custom agent."""
    absent_on_codex = _roles(inventory, "codex", "custom_agent", same=False)
    return frozenset(r["name"] for r in absent_on_codex if r["claude_code"]["implementation"] != "none")


def codex_only_roles(inventory: dict[str, Any] = AGENT_INVENTORY) -> frozenset[str]:
    """Roles with a Codex custom agent but no Claude agent."""
    return frozenset(r["name"] for r in _roles(inventory, "claude_code", "none", same=True))


def capability_exempt_roles(
    runtime: str, inventory: dict[str, Any] = AGENT_INVENTORY
) -> frozenset[str]:
    """Roles that carry no capability-discovery pointer on the given host."""
    absent = claude_only_roles(inventory) if runtime == "claude" else codex_only_roles(inventory)
    return absent | CAPABILITY_POINTER_EXEMPT
