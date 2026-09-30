#!/usr/bin/env python3
"""Codex PreToolUse hook: hold each SpecKit agent to its Claude tool policy.

Codex ignores an agent file's `sandbox_mode` and has no per-agent MCP
allowlist, so this hook applies the limits instead. The payload of a call
made by a spawned custom agent carries `agent_type`; the parent's payload
does not, so the parent's own calls always pass. For a role listed in
`speckit_pro_runner/codex_agent_policy.json`, generated from the Claude
agents, it denies:

- `apply_patch` when the role is read-only;
- every MCP tool outside the role's broker allowlist.

A hook cannot tell a shell write from a shell read, so a read-only role's
shell writes stay a prose rule in its instructions. Codex runs a plugin hook
only after the operator trusts it, and a hook is a guardrail, not a sandbox.

Anything unexpected fails open: the hook exits 0 with a note on stderr, so a
broken guard degrades to the prose rules instead of locking the operator
out. That includes the interpreter: below Python 3.11, the Installed Runtime
Contract floor, the hook prints one warning and exits 0.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HOOK_VERSION = "agent-policy-v1"
MAX_PAYLOAD = 64 * 1024
PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str]) -> int:
    if sys.version_info < (3, 11):
        print("codex agent policy hook: interpreter below Python 3.11, guard inactive (fail-open)", file=sys.stderr)
        return 0
    if argv != [HOOK_VERSION]:
        print("codex agent policy hook: usage " + HOOK_VERSION, file=sys.stderr)
        return 2
    try:
        sys.path.insert(0, str(PLUGIN_ROOT))
        from speckit_pro_runner.host_parity import (
            CODEX_HOOK_POLICY_FILE,
            codex_hook_denial,
            load_codex_hook_policies,
        )

        raw = sys.stdin.buffer.read(MAX_PAYLOAD + 1)
        if len(raw) > MAX_PAYLOAD:
            raise ValueError("hook input exceeds the bound")
        payload = json.loads(raw or b"{}")
        if not isinstance(payload, dict):
            raise ValueError("hook input must be an object")
        policies = load_codex_hook_policies((PLUGIN_ROOT / CODEX_HOOK_POLICY_FILE).read_text(encoding="utf-8"))
        reason = codex_hook_denial(payload, policies)
        if reason:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }}))
        return 0
    except Exception as exc:  # fail open, see module docstring  # noqa: BLE001
        print(f"codex agent policy hook: no decision ({exc.__class__.__name__}: {exc})", file=sys.stderr)
        return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
