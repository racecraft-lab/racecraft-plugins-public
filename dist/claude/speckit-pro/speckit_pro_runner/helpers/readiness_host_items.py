"""Readiness items that depend on the host (ADR 0008): permission probe, plugin scope, MCP state, hooks.

Scaffold passes raw observations; this module derives each item's status and
action, so a caller cannot claim `verified` for a denied probe or a stale
scope. Three items exist only on Claude Code and are recorded
`not_applicable` on Codex. Hook definitions and trust state are recorded on
both hosts. The record holds names, states and digests, never an absolute
path; an absolute interpreter appears only in the rules printed to the user.
"""

from __future__ import annotations

import re
from typing import Any

from ..agent_materialization import digest
from ..strict_input import SelectionError
from ..sweep_isolation import secret_matches
from .readiness_record import MAX_TEXT, NOT_OBSERVED_ACTION, clean_text, make_item

CLAUDE_ONLY_ITEMS = ("permission_probe", "plugin_scope", "mcp_authentication")
HOST_ITEMS = (*CLAUDE_ONLY_ITEMS, "hooks")
DETAIL_KEYS = {"permission_probe": "probes", "plugin_scope": "scope", "mcp_authentication": "servers",
               "hooks": "hooks"}
PROBES = ("runner_request", "git_status")
PROBE_OUTCOMES = ("passed", "denied", "prompted")
SCOPES = ("user", "project", "local")
MCP_STATES = ("connected", "needs_authentication", "pending_approval", "failed", "rejected", "disabled", "unknown")
TRUST_STATES = ("trusted", "untrusted", "unobservable")
NAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9_.:-]{0,63}")  # a plugin MCP server is `plugin:<plugin>:<server>`
# Letters, digits and `_.+-` only: no wildcard, quote, comma, parenthesis, whitespace or shell metacharacter.
COMMAND_RE = re.compile(r"[A-Za-z0-9_.+/][A-Za-z0-9_./+-]*")
VERSION_RE = re.compile(r"[0-9A-Za-z][0-9A-Za-z.+-]{0,39}")
INTERPRETER_PLACEHOLDER = "<interpreter>"
NOT_APPLICABLE_SOURCE = "Claude Code only; Codex records its own approval, sandbox and trust items"


def describe(source: str, summary: str, label: str) -> str:
    """`source: summary` as one record line; a long summary is cut so the line fits the record limit."""
    return clean_text(f"{source}: {summary}"[:MAX_TEXT - 1], label)


def listed(raw: dict[str, Any], key: str, label: str) -> list[dict[str, Any]]:
    entries = raw[key]
    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
        raise SelectionError(f"{label}.{key} must be a list of objects")
    return entries


def choice(value: Any, allowed: tuple[str, ...], label: str) -> str:
    if value not in allowed:
        raise SelectionError(f"{label} must be one of {list(allowed)}")
    return str(value)


def name_text(value: Any, label: str) -> str:
    """A short name safe to store and print; the same pattern bounds every hook, server and probe name."""
    text = clean_text(value, label)
    return text if NAME_RE.fullmatch(text) else _refuse_name(label)


def _refuse_name(label: str) -> str:
    raise SelectionError(f"{label} must be a short name of letters, digits, dots, hyphens or underscores")


def allow_rule_texts(probes: list[dict[str, Any]], command_label: str) -> list[str]:
    """Claude Code `Tool(pattern)` rules for each failed probe; `command_label` stands in for the interpreter."""
    rules: list[str] = []
    for probe in probes:
        if probe["outcome"] == "passed":
            continue
        if probe["probe"] == "runner_request":
            rules += [f"Bash({command_label} -m speckit_pro_runner:*)", "Bash(printf:*)"]
        else:
            rules.append("Bash(git status:*)")
    return rules


def parse_probes(raw: dict[str, Any]) -> list[dict[str, Any]]:
    probes = listed(raw, "probes", "permission_probe")
    parsed = []
    for probe in probes:
        outcome = choice(probe.get("outcome"), PROBE_OUTCOMES, "permission_probe outcome")
        entry: dict[str, Any] = {"probe": choice(probe.get("probe"), PROBES, "permission_probe probe"),
                                 "outcome": outcome}
        if entry["probe"] == "runner_request" and outcome != "passed":
            command = probe.get("command")
            if not isinstance(command, str) or not COMMAND_RE.fullmatch(command) or len(command) > 120 or ".." in command.split("/") \
                    or secret_matches(command):
                raise SelectionError("a failed runner_request probe needs the interpreter `command` it used")
            entry["command"] = command
        parsed.append(entry)
    return parsed


def rules_for(probes: list[dict[str, Any]], recorded: bool) -> list[str]:
    """Rules for the failed probes. A recorded rule shows a placeholder for an absolute interpreter path."""
    rules: list[str] = []
    for probe in probes:
        command = probe.get("command", INTERPRETER_PLACEHOLDER)
        rules += allow_rule_texts([probe], INTERPRETER_PLACEHOLDER if recorded and command.startswith("/") else command)
    return rules


def observe_permission_probe(raw: dict[str, Any], observed_at: str, source: str) -> dict[str, Any]:
    probes = parse_probes(raw)
    if not probes:
        return make_item("unknown", source, observed_at, {}, NOT_OBSERVED_ACTION)
    summary = ", ".join(f"{probe['probe']}={probe['outcome']}" for probe in probes)
    prints = {"value:probes": digest(summary)}
    source = describe(source, summary, "permission_probe.evidence_source")
    rules = rules_for(probes, recorded=True)
    if rules:
        return make_item("unavailable", source, observed_at, prints, clean_text(
            "Add these allow rules to permissions.allow in .claude/settings.local.json or your user settings, "
            "then rerun scaffold: " + "; ".join(rules), "permission_probe.action"))
    missing = [name for name in PROBES if name not in {probe["probe"] for probe in probes}]
    if missing:
        return make_item("unknown", source, observed_at, prints,
                         f"Run the {', '.join(missing)} probe, then rerun scaffold.")
    return make_item("verified", source, observed_at, prints)


def observe_plugin_scope(raw: dict[str, Any], observed_at: str, source: str) -> dict[str, Any]:
    scope = raw["scope"]
    if not isinstance(scope, dict):
        raise SelectionError("plugin_scope.scope must be an object")
    where = choice(scope.get("scope"), SCOPES, "plugin_scope scope")
    versions = {}
    for key in ("loaded_version", "expected_version"):
        value = scope.get(key)
        if value is not None and (not isinstance(value, str) or not VERSION_RE.fullmatch(value)):
            raise SelectionError(f"plugin_scope {key} must be a version string")
        versions[key] = value
    loaded, expected = versions["loaded_version"], versions["expected_version"]
    prints = {f"value:{key}": digest(value) for key, value in {"scope": where, **versions}.items()
              if value is not None}
    if loaded is None or expected is None:
        return make_item("unknown", clean_text(f"{source}: effective {where} scope version not observed", "source"),
                         observed_at, prints,
                         "Run `claude plugin list` to read the effective scope and version of speckit-pro, "
                         "then rerun scaffold.")
    source = describe(source, f"{where} scope loads {loaded}, expected {expected}", "plugin_scope.evidence_source")
    if loaded == expected:
        return make_item("verified", source, observed_at, prints)
    return make_item("unavailable", source, observed_at, prints, clean_text(
        f"Run `claude plugin update speckit-pro --scope {where}`, then run /reload-plugins or restart "
        "Claude Code and rerun scaffold.", "plugin_scope.action"))


MCP_ACTIONS = {
    "needs_authentication": "Run `claude mcp login {server}`",
    "pending_approval": "Run `claude` in this project and accept the workspace trust dialog for {server}",
    "failed": "Check why {server} failed to connect with `claude mcp list`",
    "rejected": "Remove {server} from disabledMcpjsonServers in settings",
    "disabled": "Re-enable {server} with /mcp",
}


def observe_mcp_authentication(raw: dict[str, Any], observed_at: str, source: str) -> dict[str, Any]:
    servers = [(name_text(entry.get("server"), "mcp_authentication server"),
                choice(entry.get("state"), MCP_STATES, "mcp_authentication state"))
               for entry in listed(raw, "servers", "mcp_authentication")]
    if not servers:
        return make_item("unknown", source, observed_at, {}, "Run /mcp to read each required server's state, "
                         "then rerun scaffold.")
    summary = ", ".join(f"{server}={state}" for server, state in servers)
    prints = {"value:servers": digest(summary)}
    source = describe(source, summary, "mcp_authentication.evidence_source")
    failing = [(server, state) for server, state in servers if state in MCP_ACTIONS]
    if failing:
        steps = "; ".join(MCP_ACTIONS[state].format(server=server) for server, state in failing)
        return make_item("unavailable", source, observed_at, prints,
                         clean_text(f"{steps}, then rerun scaffold.", "mcp_authentication.action"))
    if any(state == "unknown" for _, state in servers):
        return make_item("unknown", source, observed_at, prints,
                         "Run /mcp to read each required server's state, then rerun scaffold.")
    return make_item("verified", source, observed_at, prints)


def observe_hooks(raw: dict[str, Any], observed_at: str, source: str, host: str) -> dict[str, Any]:
    hooks = [(name_text(entry.get("hook"), "hooks hook"), entry.get("defined"),
              choice(entry.get("trust"), TRUST_STATES, "hooks trust"))
             for entry in listed(raw, "hooks", "hooks")]
    if any(not isinstance(defined, bool) for _, defined, _ in hooks):
        raise SelectionError("hooks needs a boolean `defined` on each entry")
    if not hooks:
        return make_item("unknown", source, observed_at, {}, "Check the required hooks in /hooks, then rerun scaffold.")
    summary = ", ".join(f"{name}={'missing' if not defined else trust}" for name, defined, trust in hooks)
    prints = {"value:hooks": digest(summary)}
    source = describe(source, summary, "hooks.evidence_source")
    if any(not defined for _, defined, _ in hooks):
        return make_item("unavailable", source, observed_at, prints,
                         "Update the speckit-pro plugin so its required hooks are defined, then rerun scaffold.")
    if any(trust == "untrusted" for _, _, trust in hooks):
        review = ("Review and trust the hooks in /hooks, then restart Codex and rerun scaffold." if host == "codex"
                  else "Enable the speckit-pro plugin, check its hooks in /hooks, accept the workspace trust "
                       "dialog, then rerun scaffold.")
        return make_item("unavailable", source, observed_at, prints, review)
    if any(trust == "unobservable" for _, _, trust in hooks):
        return make_item("unknown", source, observed_at, prints,
                         "Check the required hooks in /hooks, then rerun scaffold.")
    return make_item("verified", source, observed_at, prints)


def host_item(raw: dict[str, Any], host: str, observed_at: str) -> tuple[str, dict[str, Any]]:
    """Derive one host-dependent item from its raw observation. `raw["item"]` is in `HOST_ITEMS`."""
    name = str(raw["item"])
    key = DETAIL_KEYS[name]
    if not raw.keys() <= {"item", "evidence_source", key}:
        raise SelectionError(f"{name} takes only item, evidence_source and {key}; its status is derived")
    if name in CLAUDE_ONLY_ITEMS and host != "claude":
        raise SelectionError(f"{name} is Claude Code only; the helper records it not_applicable on {host}")
    source = clean_text(raw.get("evidence_source"), f"{name}.evidence_source")
    if key not in raw:
        return name, make_item("unknown", source, observed_at, {}, NOT_OBSERVED_ACTION)
    if name == "permission_probe":
        return name, observe_permission_probe(raw, observed_at, source)
    if name == "plugin_scope":
        return name, observe_plugin_scope(raw, observed_at, source)
    if name == "mcp_authentication":
        return name, observe_mcp_authentication(raw, observed_at, source)
    return name, observe_hooks(raw, observed_at, source, host)


def fill_missing(items: dict[str, dict[str, Any]], host: str, observed_at: str) -> None:
    """Record each item scaffold did not send: not_applicable off Claude Code, otherwise unknown."""
    for name in HOST_ITEMS:
        if name in items:
            continue
        if name in CLAUDE_ONLY_ITEMS and host != "claude":
            items[name] = make_item("not_applicable", NOT_APPLICABLE_SOURCE, observed_at, {})
        else:
            items[name] = make_item("unknown", "not observed by scaffold", observed_at, {}, NOT_OBSERVED_ACTION)


def allow_rules(inputs: dict[str, Any]) -> list[str]:
    """The rules to print for a denied probe, with the interpreter exactly as the request used it."""
    for raw in inputs.get("observations", []):
        if isinstance(raw, dict) and raw.get("item") == "permission_probe" and "probes" in raw:
            return rules_for(parse_probes(raw), recorded=False)
    return []
