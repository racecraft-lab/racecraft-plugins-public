"""Readiness items that depend on the host (ADR 0008): permission probe, plugin scope, MCP state, hooks.

Scaffold passes raw observations; this module derives each item's status and
action, so a caller cannot claim `verified` for a denied probe or a stale
scope. Three items exist only on Claude Code and are recorded
`not_applicable` on Codex. Hook definitions and trust state are recorded on
both hosts. The record holds names, states and digests, never an absolute
path; an absolute interpreter appears only in the rules printed to the user.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..agent_materialization import digest
from ..strict_input import SelectionError
from ..sweep_isolation import secret_matches
from .readiness_values import MAX_TEXT, NOT_OBSERVED_ACTION, clean_text, make_item

CLAUDE_ONLY_ITEMS = ("permission_probe", "plugin_scope", "mcp_authentication")
CODEX_TRUST_ITEMS = ("codex_approval_posture", "codex_hook_trust", "codex_local_access")
CODEX_ONLY_ITEMS = ("codex_agents", "extension_versions", *CODEX_TRUST_ITEMS)
HOST_ITEMS = (*CLAUDE_ONLY_ITEMS, "hooks", *CODEX_ONLY_ITEMS)
DETAIL_KEYS = {"permission_probe": "probes", "plugin_scope": "scope", "mcp_authentication": "servers",
               "hooks": "hooks", "codex_agents": "agents", "extension_versions": "extensions",
               "codex_approval_posture": "posture", "codex_hook_trust": "hooks", "codex_local_access": "access"}
PROBES = ("runner_request", "git_status")
PROBE_OUTCOMES = ("passed", "denied", "prompted")
SCOPES = ("user", "project", "local")
MCP_STATES = ("connected", "needs_authentication", "pending_approval", "failed", "rejected", "disabled", "unknown")
TRUST_STATES = ("trusted", "untrusted", "unobservable")
NAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9_.:-]{0,63}")  # a plugin MCP server is `plugin:<plugin>:<server>`
# Letters, digits and `_./+-` only: no wildcard, quote, comma, parenthesis, whitespace or shell metacharacter.
COMMAND_RE = re.compile(r"[A-Za-z0-9_.+/][A-Za-z0-9_./+-]*")
VERSION_RE = re.compile(r"[0-9A-Za-z][0-9A-Za-z.+-]{0,39}")
INTERPRETER_PLACEHOLDER = "<interpreter>"
NOT_APPLICABLE_SOURCE = "Claude Code only; Codex records its own approval, sandbox and trust items"
CODEX_NOT_APPLICABLE_SOURCE = "Codex only; Claude Code loads its agents from the plugin and records its own scope item"


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
    text = pattern_text(value, NAME_RE, "a short name", label)
    return clean_text(text, label)


def allow_rule_texts(probes: list[dict[str, Any]], command_label: str) -> list[str]:
    """Claude Code `Tool(pattern)` rules for each failed probe; `command_label` stands in for the interpreter."""
    rules: list[str] = []
    for probe in probes:
        outcome = choice(probe["outcome"], PROBE_OUTCOMES, "permission_probe outcome")
        name = choice(probe["probe"], PROBES, "permission_probe probe")
        if outcome == "passed":
            continue
        if name == "runner_request":
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
    """Printed rules retain the command; recorded rules omit interpreter directories."""
    rules: list[str] = []
    for probe in probes:
        command = probe.get("command", INTERPRETER_PLACEHOLDER)
        label = INTERPRETER_PLACEHOLDER if command.startswith("/") else command.rsplit("/", 1)[-1]
        rules += allow_rule_texts([probe], label if recorded else command)
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


def observe_plugin_scope(raw: dict[str, Any], observed_at: str, source: str,
                         plugin_revision: str) -> dict[str, Any]:
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
    prints = {f"value:{key}": digest(value) for key, value in {"scope": where, "plugin_revision": plugin_revision, **versions}.items()
              if value is not None}
    if loaded is None or expected is None:
        return make_item("unknown", clean_text(f"{source}: effective {where} scope version not observed", "source"),
                         observed_at, prints,
                         "Run `claude plugin list` to read the effective scope and version of speckit-pro, "
                         "then rerun scaffold.")
    source = describe(source, f"{where} scope loads {loaded}, expected {expected}, record revision {plugin_revision}",
                      "plugin_scope.evidence_source")
    if loaded == expected == plugin_revision:
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
    status = hook_trust_status([trust for _, _, trust in hooks])
    if status == "unavailable":
        review = (LEGACY_CODEX_HOOK_ACTION if host == "codex"
                  else "Enable the speckit-pro plugin, check its hooks in /hooks, accept the workspace trust "
                       "dialog, then rerun scaffold.")
        return make_item("unavailable", source, observed_at, prints, review)
    if status == "unknown":
        return make_item("unknown", source, observed_at, prints,
                         "Check the required hooks in /hooks, then rerun scaffold.")
    if host == "codex":
        return make_item("unknown", source, observed_at, prints,
                         "Record legacy hook evidence as incomplete; supply the complete codex_hook_trust "
                         "observation, then rerun scaffold.")
    return make_item("verified", source, observed_at, prints)


def host_item(raw: dict[str, Any], host: str, observed_at: str, plugin_revision: str) -> tuple[str, dict[str, Any]]:
    """Derive one host-dependent item from its raw observation. `raw["item"]` is in `HOST_ITEMS`."""
    name = str(raw["item"])
    key = DETAIL_KEYS[name]
    if not raw.keys() <= {"item", "evidence_source", key}:
        raise SelectionError(f"{name} takes only item, evidence_source and {key}; its status is derived")
    if name in CLAUDE_ONLY_ITEMS and host != "claude":
        raise SelectionError(f"{name} is Claude Code only; the helper records it not_applicable on {host}")
    if name in CODEX_ONLY_ITEMS and host != "codex":
        raise SelectionError(f"{name} is Codex only; the helper records it not_applicable on {host}")
    source = clean_text(raw.get("evidence_source"), f"{name}.evidence_source")
    if key not in raw:
        return name, make_item("unknown", source, observed_at, {}, NOT_OBSERVED_ACTION)
    if name == "permission_probe":
        return name, observe_permission_probe(raw, observed_at, source)
    if name == "plugin_scope":
        return name, observe_plugin_scope(raw, observed_at, source, plugin_revision)
    if name == "mcp_authentication":
        return name, observe_mcp_authentication(raw, observed_at, source)
    if name == "codex_agents":
        return name, observe_codex_agents(raw, observed_at, source, plugin_revision)
    if name == "extension_versions":
        return name, observe_extension_versions(raw, observed_at, source)
    if name in CODEX_TRUST_ITEMS:
        return name, CODEX_TRUST_OBSERVERS[name](raw, observed_at, source)
    return name, observe_hooks(raw, observed_at, source, host)


def fill_missing(items: dict[str, dict[str, Any]], host: str, observed_at: str) -> None:
    """Record each item scaffold did not send: not_applicable off its host, otherwise unknown."""
    for name in HOST_ITEMS:
        if name in items:
            continue
        if name in CLAUDE_ONLY_ITEMS and host != "claude":
            items[name] = make_item("not_applicable", NOT_APPLICABLE_SOURCE, observed_at, {})
        elif name in CODEX_ONLY_ITEMS and host != "codex":
            items[name] = make_item("not_applicable", CODEX_NOT_APPLICABLE_SOURCE, observed_at, {})
        else:
            items[name] = make_item("unknown", "not observed by scaffold", observed_at, {}, NOT_OBSERVED_ACTION)


def allow_rules(inputs: dict[str, Any]) -> list[str]:
    """The rules to print for a denied probe, with the interpreter exactly as the request used it."""
    for raw in inputs.get("observations", []):
        if isinstance(raw, dict) and raw.get("item") == "permission_probe" and "probes" in raw:
            return rules_for(parse_probes(raw), recorded=False)
    return []


# --- Codex-only items: installed agents and extension versions -------------------------------------------------
AGENT_STATES = ("current", "stale", "missing")
REPAIRS = ("none", "applied", "declined", "failed")
STATIC_INSTALL_KEYS = {"destination", "model", "luna_fallback"}
ROUTED_INSTALL_KEYS = {"destination", "route_policy_manifest", "strict_model_override"}
RESTART_ACTION = ("Rerun scaffold after you restart Codex so it loads the repaired agents; "
                  "installing them does not change the running session.")


def installation_digest(raw: Any) -> str:
    """Digest of the selected installation inputs, replayed exactly as the install helper takes them (#1048).

    A static installation may name `model` and `luna_fallback`; a route-aware one names
    `route_policy_manifest` and may add `strict_model_override`. Neither takes a `routing_mode` key, and the
    two shapes never mix. Only the digest is recorded, so a destination path never reaches the record.
    """
    if not isinstance(raw, dict):
        raise SelectionError("codex_agents.installation must be an object")
    routed = "route_policy_manifest" in raw
    allowed = ROUTED_INSTALL_KEYS if routed else STATIC_INSTALL_KEYS
    needed = {"route_policy_manifest"} if routed else set()
    if not needed <= raw.keys() <= allowed:
        raise SelectionError(f"codex_agents.installation takes {sorted(allowed)} and needs {sorted(needed)}")
    texts = {key: value for key, value in raw.items() if key != "luna_fallback"}
    if not all(isinstance(value, str) and value.strip() for value in texts.values()) \
            or not isinstance(raw.get("luna_fallback", False), bool):
        raise SelectionError("codex_agents.installation needs text values and a boolean luna_fallback")
    return digest(json.dumps(raw, sort_keys=True))


def pattern_text(value: Any, pattern: re.Pattern[str], what: str, label: str) -> str:
    """`value` when it is text that fully matches `pattern`; anything else, such as a path or a sentence, is refused."""
    if isinstance(value, str) and pattern.fullmatch(value):
        return value
    raise SelectionError(f"{label} must be {what}")


def revision_text(value: Any, label: str) -> str:
    return pattern_text(value, VERSION_RE, "a version string", label)


def observe_codex_agents(raw: dict[str, Any], observed_at: str, source: str, plugin_revision: str) -> dict[str, Any]:
    detail = raw["agents"]
    needed = {"installation", "inventory", "expected_revision"}
    if not isinstance(detail, dict) or not needed <= detail.keys() <= needed | {"loaded_revision"}:
        raise SelectionError("codex_agents.agents takes installation, inventory, loaded_revision, expected_revision")
    prints = {"value:installation_inputs": installation_digest(detail.get("installation"))}
    inventory = [(name_text(entry.get("agent"), "codex_agents agent"),
                  choice(entry.get("state"), AGENT_STATES, "codex_agents state"),
                  choice(entry.get("repair"), REPAIRS, "codex_agents repair"))
                 for entry in listed(detail, "inventory", "codex_agents")]
    if any(state == "current" and repair != "none" for _, state, repair in inventory):
        raise SelectionError("codex_agents current agents must have repair none")
    expected = revision_text(detail.get("expected_revision"), "codex_agents expected_revision")
    if expected != plugin_revision:
        raise SelectionError("codex_agents expected_revision must match plugin_revision")
    loaded = detail.get("loaded_revision")
    if loaded is not None:
        loaded = revision_text(loaded, "codex_agents loaded_revision")
    prints["value:expected_revision"] = digest(expected)
    if not inventory:
        return make_item("unknown", source, observed_at, prints,
                         "Run the install-codex-agents dry run with the selected installation inputs, "
                         "then rerun scaffold.")
    summary = ", ".join(f"{name}={state}" + ("" if repair == "none" else f" ({repair})")
                        for name, state, repair in inventory)
    prints["value:inventory"] = digest(summary)
    source = describe(source, summary, "codex_agents.evidence_source")
    if any(state != "current" and repair != "applied" for _, state, repair in inventory):
        return make_item("unavailable", source, observed_at, prints, clean_text(
            "Run $speckit-pro:install with the selected installation inputs, restart Codex, then rerun scaffold.",
            "codex_agents.action"))
    if loaded is None:
        return make_item("unknown", source, observed_at, prints, RESTART_ACTION)
    prints["value:loaded_revision"] = digest(loaded)
    if loaded != expected:
        return make_item("unavailable", describe(source, f"session loaded {loaded}, expected {expected}",
                                                 "codex_agents.evidence_source"), observed_at, prints, RESTART_ACTION)
    return make_item("verified", source, observed_at, prints)


def observe_extension_versions(raw: dict[str, Any], observed_at: str, source: str) -> dict[str, Any]:
    entries = []
    for entry in listed(raw, "extensions", "extension_versions"):
        versions = {}
        for key in ("installed", "expected"):
            value = entry.get(key)
            versions[key] = None if value is None else revision_text(value, f"extension_versions {key}")
        entries.append((name_text(entry.get("extension"), "extension_versions extension"), versions["installed"],
                        versions["expected"]))
    if not entries:
        return make_item("unknown", source, observed_at, {}, "Read the installed extension versions with "
                         "`specify extension list`, then rerun scaffold.")
    summary = ", ".join(f"{name}={installed or 'not installed'}"
                        + (f" (expected {expected})" if expected not in (None, installed) else "")
                        for name, installed, expected in entries)
    prints = {"value:extensions": digest(summary)}
    source = describe(source, summary, "extension_versions.evidence_source")
    steps = [f"Run `specify extension add {name}`" if installed is None else f"Run `specify extension update {name}`"
             for name, installed, expected in entries if installed is None or (expected and installed != expected)]
    if steps:
        action = "; ".join(steps) + ", then rerun scaffold."
        if len(action) > MAX_TEXT:  # many drifted extensions: one fixed line instead of a refused record
            action = ("Run `specify extension list`, then `specify extension update` for each drifted extension "
                      "and `specify extension add <id>` for each missing one, then rerun scaffold.")
        return make_item("unavailable", source, observed_at, prints, clean_text(action, "extension_versions.action"))
    if any(expected is None for _, _, expected in entries):
        return make_item("unknown", source, observed_at, prints, "Name the expected version of each extension "
                         "(its project pin or the curated set), then rerun scaffold.")
    return make_item("verified", source, observed_at, prints)


# --- Codex-only items: approval posture, hook trust and local access (ADR 0008) --------------------------------
# These record observed facts, never consent. Every printed action comes from a fixed template, and every
# recorded value is an enumerated word, a bounded integer, a name or a hex digest, never free text or a path.
NEVER_BROADEN = "Scaffold never broadens permissions or disables a control."
# Legacy hook evidence has no exact hash, so its action never asks the user to trust anything.
LEGACY_CODEX_HOOK_ACTION = ("Send a complete codex_hook_trust observation that verifies each hook's identity and exact hash "
                            "against the shipped definitions, then rerun scaffold. Never trust a hook that is not "
                            "verified. " + NEVER_BROADEN)
POSTURE_CHOICES = {
    "approval_policy": ("on-request", "never", "on-failure"),
    "sandbox_mode": ("read-only", "workspace-write", "danger-full-access"),
    "approvals_reviewer": ("user", "auto_review"),
    "mcp_approval_mode": ("auto", "prompt", "writes", "approve"),
    "mcp_consent": ("granted", "not_granted"),
    "external_delegation": ("allowed", "blocked"),
}
POSTURE_TIMEOUTS = ("mcp_startup_timeout_sec", "mcp_tool_timeout_sec")
MAX_TIMEOUT_SECONDS = 86400
HASH_RE = re.compile(r"(?:(?i:sha256):)?[0-9a-fA-F]{64}")
GRANULAR_KEYS = ("sandbox_approval", "rules", "mcp_elicitations", "request_permissions", "skill_approval")
POSTURE_DEFAULT_TIMEOUTS = {"mcp_startup_timeout_sec": 10, "mcp_tool_timeout_sec": 60}
LOOPBACK_STATES = ("allowed", "blocked", "unobservable")
TEMP_DIR_STATES = ("healthy", "leaky", "unobservable")
POSTURE_ACTIONS = {
    "external_delegation": "Keep external delegation blocked; record the limit and continue independent work. " + NEVER_BROADEN,
    "mcp_consent": "Keep MCP consent ungranted; record the limit and continue work that does not require MCP. " + NEVER_BROADEN,
}


def hash_text(value: Any, label: str) -> str:
    """SHA-256 as printed; comparisons normalize case and the optional prefix."""
    return pattern_text(value, HASH_RE, "a hex digest", label)


def optional_hash(value: Any, label: str) -> str | None:
    return None if value is None else hash_text(value, label)


def exact_fingerprint(value: str) -> str:
    return "sha256:" + hash_text(value, "fingerprint").lower().removeprefix("sha256:")


def hook_trust_status(states: list[str]) -> str:
    """One trust rule for both definition and exact-hash observations."""
    if "untrusted" in states:
        return "unavailable"
    return "unknown" if not states or "unobservable" in states else "verified"


def shipped_codex_hooks() -> dict[str, str] | None:
    """Codex 0.160 normalized definition hashes; no expanded local paths enter the identity.

    Matches openai/codex rust-v0.160.0 hooks/engine/discovery.rs::hook_hash and
    config/fingerprint.rs::version_for_toml, checked against live hooks/list.
    Unsupported shipped shapes supply no verified evidence.
    """
    try:
        events = json.loads((Path(__file__).parents[2] / "codex-hooks.json").read_text(encoding="utf-8"))["hooks"]
        expected = {}
        for event, groups in events.items():
            for group_index, group in enumerate(groups):
                for handler_index, handler in enumerate(group["hooks"]):
                    if handler.keys() - {"type", "command", "timeout"} or handler["type"] != "command":
                        return None
                    identity = {"event_name": re.sub(r"(?<!^)(?=[A-Z])", "_", event).lower(),
                                "hooks": [{**handler, "async": False}]}
                    if "matcher" in group:
                        identity["matcher"] = group["matcher"]
                    expected[f"{event}:{group_index}:{handler_index}"] = digest(identity)
        return expected or None
    except (OSError, ValueError, KeyError, TypeError):
        return None


def observe_codex_approval_posture(raw: dict[str, Any], observed_at: str, source: str) -> dict[str, Any]:
    detail = raw["posture"]
    if not isinstance(detail, dict) or detail.keys() != {*POSTURE_CHOICES, *POSTURE_TIMEOUTS}:
        raise SelectionError(f"codex_approval_posture.posture takes {sorted({*POSTURE_CHOICES, *POSTURE_TIMEOUTS})}")
    facts: dict[str, str] = {}
    for key, allowed in POSTURE_CHOICES.items():
        value = detail[key]
        if key == "approval_policy" and isinstance(value, dict):
            granular = value.get("granular")
            if value.keys() != {"granular"} or not isinstance(granular, dict) or granular.keys() != set(GRANULAR_KEYS) \
                    or any(type(flag) is not bool for flag in granular.values()):
                raise SelectionError("approval_policy granular needs exactly five boolean prompt categories")
            facts[key] = "granular(" + ",".join(f"{name}={str(granular[name]).lower()}" for name in GRANULAR_KEYS) + ")"
        else:
            facts[key] = choice(value, (*allowed, "unobservable"), f"codex_approval_posture {key}")
    for key in POSTURE_TIMEOUTS:
        value = detail[key]  # null means the setting is absent, so Codex uses its documented default
        if value is not None and value != "unobservable" and (type(value) is not int
                                                              or not 0 < value <= MAX_TIMEOUT_SECONDS):
            raise SelectionError(f"codex_approval_posture {key} must be whole seconds, null or \"unobservable\"")
        facts[key] = "default" if value is None else str(value)
    summary = ", ".join(f"{key}={value}" for key, value in facts.items())
    prints = {"value:posture": digest(summary)}
    source = describe(source, summary, "codex_approval_posture.evidence_source")
    refused = [key for key in POSTURE_ACTIONS if facts[key] in ("blocked", "not_granted")]
    if refused:
        return make_item("unavailable", source, observed_at, prints, POSTURE_ACTIONS[refused[0]])
    if facts["sandbox_mode"] == "danger-full-access" or facts["mcp_approval_mode"] in ("auto", "writes", "approve") \
            or any(type(detail[key]) is int and detail[key] > limit for key, limit in POSTURE_DEFAULT_TIMEOUTS.items()):
        return make_item("unavailable", source, observed_at, prints,
                         "Keep current controls; review the observed posture against the conservative scaffold profile "
                         "before using the affected capability. " + NEVER_BROADEN)
    if "unobservable" in facts.values():
        return make_item("unknown", source, observed_at, prints, "Read the Codex approval, sandbox, reviewer and "
                         "MCP settings from an effective running-thread source; leave unreadable values unobservable "
                         "and rerun scaffold. " + NEVER_BROADEN)
    return make_item("verified", source, observed_at, prints)


def observe_codex_hook_trust(raw: dict[str, Any], observed_at: str, source: str) -> dict[str, Any]:
    hooks = []
    enablement = []
    for entry in listed(raw, "hooks", "codex_hook_trust"):
        if not entry.keys() <= {"hook", "state", "hash", "enabled"}:
            raise SelectionError("codex_hook_trust entries take hook, state, hash and enabled")
        state = choice(entry.get("state"), TRUST_STATES, "codex_hook_trust state")
        enabled = entry.get("enabled")
        if enabled is not None and type(enabled) is not bool:
            raise SelectionError("codex_hook_trust enabled must be a boolean or null when unobservable")
        enablement.append("untrusted" if enabled is False else "unobservable" if enabled is None else "trusted")
        found = optional_hash(entry.get("hash"), "codex_hook_trust hash")
        if state == "trusted" and found is None:
            raise SelectionError("a trusted codex_hook_trust entry needs the exact `hash` that was trusted")
        hooks.append((name_text(entry.get("hook"), "codex_hook_trust hook"), state, found))
    if len({name for name, _, _ in hooks}) != len(hooks):
        raise SelectionError("codex_hook_trust names each hook once")
    hooks.sort(key=lambda hook: hook[1] != "untrusted")  # untrusted first, so a long list never cuts them from the evidence
    if not hooks:
        return make_item("unknown", source, observed_at, {}, "Review the hooks in /hooks, then rerun scaffold.")
    summary = ", ".join(f"{name}={state}" + (f" {found}" if found else "") for name, state, found in hooks)
    prints = {"value:hook_hashes": digest([(name, state, exact_fingerprint(found) if found else None)
                                          for name, state, found in hooks]),
              "value:hook_enablement": digest(enablement),
              **{f"hook:{name}": exact_fingerprint(found) for name, _, found in hooks if found}}
    source = describe(source, summary, "codex_hook_trust.evidence_source")
    expected = shipped_codex_hooks()
    if expected is None:
        return make_item("unknown", source, observed_at, prints,
                         "Inspect the shipped hook definitions and the supported Codex hash contract, then rerun scaffold.")
    if {name for name, _, _ in hooks} != expected.keys() or any(
            found is not None and exact_fingerprint(found) != expected.get(name) for name, _, found in hooks):
        return make_item("unavailable", source, observed_at, prints,
                         "Compare every shipped hook handler and exact hash with the loaded plugin; keep current controls "
                         "and rerun scaffold after resolving missing or changed definitions. " + NEVER_BROADEN)
    status = hook_trust_status([state for _, state, _ in hooks] + enablement)
    if status == "unavailable":
        if "untrusted" in enablement:
            return make_item("unavailable", source, observed_at, prints,
                             "Keep current controls; review why a required shipped hook is disabled, then rerun scaffold. "
                             + NEVER_BROADEN)
        return make_item("unavailable", source, observed_at, prints,
                         "Review and trust the hooks in /hooks, then restart Codex and rerun scaffold. " + NEVER_BROADEN)
    if status == "unknown":
        return make_item("unknown", source, observed_at, prints, "Review the hooks in /hooks, then rerun scaffold.")
    return make_item("verified", source, observed_at, prints)


def observe_codex_local_access(raw: dict[str, Any], observed_at: str, source: str) -> dict[str, Any]:
    detail = raw["access"]
    if not isinstance(detail, dict) or detail.keys() != {"loopback", "temp_dir", "egress_policy_ref",
                                                          "egress_policy_digest"}:
        raise SelectionError("codex_local_access.access takes loopback, temp_dir, egress_policy_ref, "
                             "egress_policy_digest")
    loopback = choice(detail["loopback"], LOOPBACK_STATES, "codex_local_access loopback")
    temp_dir = choice(detail["temp_dir"], TEMP_DIR_STATES, "codex_local_access temp_dir")
    reference = detail["egress_policy_ref"]
    reference = None if reference is None else name_text(reference, "codex_local_access egress_policy_ref")
    policy_digest = optional_hash(detail["egress_policy_digest"], "codex_local_access egress_policy_digest")
    if (reference is None) != (policy_digest is None):
        raise SelectionError("codex_local_access names the egress policy by both reference and digest, or neither")
    policy = f"{reference} {policy_digest}" if reference and policy_digest else "unobservable"
    summary = f"loopback={loopback}, temp_dir={temp_dir}, egress_policy={policy}"
    prints = {"value:access": digest({"loopback": loopback, "temp_dir": temp_dir, "egress_policy_ref": reference,
                                      "egress_policy_digest": exact_fingerprint(policy_digest) if policy_digest else None})}
    if policy_digest:
        prints["value:egress_policy_digest"] = exact_fingerprint(policy_digest)
    source = describe(source, summary, "codex_local_access.evidence_source")
    steps = []
    if loopback == "blocked":
        steps.append("Keep loopback blocked under current controls; record the affected capability as unavailable")
    if temp_dir == "leaky":
        steps.append("Fix the temporary directory so sensitive files stay owner-only")
    if steps:
        return make_item("unavailable", source, observed_at, prints,
                         "; ".join(steps) + ", then rerun scaffold. " + NEVER_BROADEN)
    if "unobservable" in (loopback, temp_dir, policy):
        return make_item("unknown", source, observed_at, prints, "Run the bounded loopback and temporary directory "
                         "checks and name the egress policy and its digest, then rerun scaffold.")
    return make_item("verified", source, observed_at, prints)


CODEX_TRUST_OBSERVERS = {"codex_approval_posture": observe_codex_approval_posture,
                         "codex_hook_trust": observe_codex_hook_trust,
                         "codex_local_access": observe_codex_local_access}


def names_item(observations: list[Any], name: str) -> bool:
    """Whether the caller sent an observation for `name`, whatever it holds."""
    return any(isinstance(raw, dict) and raw.get("item") == name for raw in observations)


def reconcile_codex_items(items: dict[str, dict[str, Any]], observed_at: str, legacy_hooks_observed: bool) -> None:
    """One Codex trust result and no caller override of the runner's temporary probe.

    Any legacy `hooks` observation, an empty one included, overlaps exact `codex_hook_trust` evidence.
    """
    trust = items["codex_hook_trust"]
    if trust["fingerprints"]:
        if legacy_hooks_observed:
            raise SelectionError("Codex hooks and codex_hook_trust observations overlap; use only the exact-hash observation")
        items["hooks"] = trust
    access = items["codex_local_access"]
    local = items["local_capability"]
    if (local["status"] == "unavailable" and access["status"] != "unavailable") \
            or (local["status"] == "unknown" and access["status"] == "verified"):
        items["codex_local_access"] = make_item(
            local["status"], describe(access["evidence_source"], "runner temporary probe=" + local["status"],
                                      "codex_local_access.evidence_source"),
            observed_at, {**access["fingerprints"], **local["fingerprints"]}, local["action"])
