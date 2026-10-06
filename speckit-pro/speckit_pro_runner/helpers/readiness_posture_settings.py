"""The Codex configuration inventory behind `codex_approval_posture` (ADR 0008, security finding F1263-946bd436).

Scaffold sends every configuration key set in any effective layer as a dotted TOML key path with its value. The
inventory is the evidence: the posture verifies only when every key in it proves the conservative profile.

Key grammar. A key path is one or more segments joined by single dots, with no whitespace. A segment is bare
(letters, digits, `_` and `-`) or a double-quoted string of printable characters without `"` or `\\`. A quoted
segment names the same key as the bare segment with the same text, and a quoted dot stays inside its segment.
Each path is canonicalized once into its segment texts. Two keys with the same canonical path, a key that is
also a table holding another key, and any key outside the grammar make a malformed inventory, which is refused.

Each key is accounted for in one of three ways, or the posture never verifies:

- a summary fact or posture control models it (`MODELED_SETTINGS`), and its value agrees with that fact or
  control; a value that contradicts an observed fact or acting control is `contradicted`, so `unavailable`;
- it cannot act on approvals, the sandbox, the process environment, egress, execution, external content or
  configuration activation (`INERT_SETTINGS`);
- it holds its conservative value (`CONSERVATIVE_SETTINGS`).

Rules name exact leaves; a `*` matches one user-named segment, such as a profile, app or server name, and
nothing matches recursively. Any other key, an unknown descendant of a known table included, is `outside` when
its value was observed and `unobservable` when it was not; so is a modeled or conservative key whose value is
`"unobservable"`. A key absent from every layer keeps the Codex default. Key lists follow the Codex
configuration reference (learn.chatgpt.com/docs/config-file/config-reference). Values and key names never reach
the record as text: one digest holds each key path and its class, never a value.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from ..agent_materialization import digest
from ..strict_input import SelectionError

UNOBSERVABLE = "unobservable"
MAX_SETTINGS = 512
MAX_KEY = 256
# One TOML key segment: bare, or double-quoted without quotes, escapes or control characters.
SEGMENT_RE = re.compile(r'[A-Za-z0-9_-]+|"[^"\\\x00-\x1f\x7f]+"')

Settings = dict[tuple[str, ...], Any]
Check = Callable[[Any], bool]
# What one modeled key, given its path, value and the whole inventory, requires of the summary: each target
# fact or control name with the test its observed value must pass.
Forces = Callable[[tuple[str, ...], Any, Settings], dict[str, Check]]


def pattern(key: str) -> tuple[str, ...]:
    """A rule key as segments; a quoted segment may hold dots."""
    return tuple(part.strip('"') for part in re.findall(r'"[^"]*"|[^.]+', key))


def patterns(*keys: str) -> tuple[tuple[str, ...], ...]:
    return tuple(pattern(key) for key in keys)


BOOLEAN = "boolean"
NAMES = "names"
TEXT = "text"
NUMBER = "number"
SCALAR = "scalar"
ANY = "any"
BROAD_MODES = ("auto", "writes", "approve")
APPROVAL_MODES = ("prompt", *BROAD_MODES)
BUILTIN_PROFILES = {":read-only": "read-only", ":workspace": "workspace", ":danger-full-access": "danger-full-access"}
GRANULAR = ("sandbox_approval", "rules", "mcp_elicitations", "request_permissions", "skill_approval")


def one_of(*values: Any) -> Check:
    return lambda observed: observed in values


def sets(target: str, convert: Callable[[Any], Any] = lambda value: value) -> Forces:
    """The key alone sets the fact or control, so the summary must hold exactly its value."""
    return lambda path, value, settings: {target: one_of(convert(value))}


def never_off(path: tuple[str, ...], settings: Settings) -> bool:
    return False


def broadens(target: str, trigger: tuple[Any, ...], allowed: tuple[Any, ...],
             off: Callable[[tuple[str, ...], Settings], bool] = never_off) -> Forces:
    """One entry of an aggregate control: a value in `trigger` requires `allowed` unless the inventory switches
    its app, server or tool off. Another value settles nothing alone, since other entries decide the aggregate."""
    return lambda path, value, settings: ({target: one_of(*allowed)}
                                          if value in trigger and not off(path, settings) else {})


def nothing(path: tuple[str, ...], value: Any, settings: Settings) -> dict[str, Check]:
    """A disabled-tools list only narrows the tools the other keys enable."""
    return {}


def some_tool(observed: Any) -> bool:
    return observed != "none"


def enables(target: str, off: Callable[[tuple[str, ...], Settings], bool]) -> Forces:
    """An explicit enablement (true, or a non-empty tool list) means a tool is enabled unless the inventory
    switches it off, so the aggregate `target` cannot be `none`."""
    return lambda path, value, settings: ({target: some_tool}
                                          if (value is True or isinstance(value, list) and value)
                                          and not off(path, settings) else {})


def covers(target: str, off: Callable[[tuple[str, ...], Settings], bool]) -> Forces:
    """An approval mode for tools the inventory does not switch off: the aggregate `target` must cover it, so a
    broad mode needs a broad aggregate and `prompt` rules out `none`."""
    return lambda path, value, settings: ({} if off(path, settings) else
                                          {target: one_of(*BROAD_MODES) if value in BROAD_MODES else some_tool})


def app_off(path: tuple[str, ...], settings: Settings) -> bool:
    return settings.get(("features", "apps")) is False or (
        path[1] != "_default" and settings.get(("apps", path[1], "enabled")) is False)


def app_tools_off(path: tuple[str, ...], settings: Settings) -> bool:
    """The app is off, or its tools are off by default (an explicitly enabled tool forces on its own)."""
    return app_off(path, settings) or settings.get(("apps", path[1], "default_tools_enabled")) is False


def app_tool_off(path: tuple[str, ...], settings: Settings) -> bool:
    """The app is off, or the tool is: its own `enabled` decides, else the app's default."""
    return app_off(path, settings) or settings.get(
        (*path[:4], "enabled"), settings.get(("apps", path[1], "default_tools_enabled"))) is False


def tools_off(server: tuple[str, ...], settings: Settings) -> bool:
    """An MCP server switched off, or one whose enabled-tools list is empty."""
    return settings.get((*server, "enabled")) is False or settings.get((*server, "enabled_tools")) == []


def tool_listed_off(server: tuple[str, ...], tool: str, settings: Settings) -> bool:
    """A tool the server's lists switch off: named in `disabled_tools`, or left out of `enabled_tools`."""
    enabled = settings.get((*server, "enabled_tools"))
    disabled = settings.get((*server, "disabled_tools"))
    return (isinstance(disabled, list) and tool in disabled) or (isinstance(enabled, list) and tool not in enabled)


def server_off(path: tuple[str, ...], settings: Settings) -> bool:
    return tools_off(path[:2], settings)


def server_tool_off(path: tuple[str, ...], settings: Settings) -> bool:
    return server_off(path, settings) or tool_listed_off(path[:2], path[3], settings)


def plugin_server_off(path: tuple[str, ...], settings: Settings) -> bool:
    return settings.get((*path[:2], "enabled")) is False or tools_off(path[:4], settings)


def plugin_server_tool_off(path: tuple[str, ...], settings: Settings) -> bool:
    return plugin_server_off(path, settings) or tool_listed_off(path[:4], path[5], settings)


def timeout(target: str, per_second: int = 1) -> Forces:
    """A server timeout the summary must cover: the summary is whole seconds no smaller than it."""
    return lambda path, value, settings: {target: lambda observed: type(observed) is int
                                          and value <= observed * per_second}


def custom_profile(path: tuple[str, ...], value: Any, settings: Settings) -> dict[str, Check]:
    """A leaf of the selected profile, or of a profile named like a built-in one, makes the profile custom."""
    name = path[1]
    if name.startswith(":") or settings.get(("default_permissions",)) == name:
        return {"permission_profile": one_of("custom")}
    return {}


def granular(name: str) -> Forces:
    return lambda path, value, settings: {"approval_policy": one_of("granular"),
                                          f"approval_policy.granular.{name}": one_of(value)}


def switch(on: str, off: str) -> Callable[[Any], str]:
    return lambda value: on if value else off


PERMISSION_LEAVES = (
    "description", "extends", "filesystem.glob_scan_max_depth", "filesystem.*", "filesystem.*.*",
    *(f"network.{name}" for name in (
        "allow_local_binding", "allow_upstream_proxy", "dangerously_allow_all_unix_sockets",
        "dangerously_allow_non_loopback_proxy", "enable_socks5", "enable_socks5_udp", "enabled", "mode",
        "proxy_url", "socks_url", "domains.*", "unix_sockets.*")),
    "workspace_roots.*",
)
WEB_SEARCH_TOOL_LEAVES = ("context_size", "allowed_domains", *(f"location.{name}" for name in (
    "country", "region", "city", "timezone")))
# Keys a summary fact or posture control models, as (accepted values or a kind, what the value requires of
# the summary). Facts are approval_policy (with its granular flags), sandbox_mode, approvals_reviewer and
# both MCP timeouts; every other target is a posture control. A web search tool table enables the tool.
# The tool approval controls aggregate every app, MCP server and plugin MCP server, so each explicit
# enablement or approval mode is reconciled with its aggregate first; only an inventory that switches the app,
# server, plugin or tool off leaves `none` unchallenged.
MODELED_SETTINGS: dict[str, tuple[Any, Forces]] = {
    "approval_policy": (("on-request", "never", "on-failure", "untrusted"), sets("approval_policy")),
    **{f"approval_policy.granular.{name}": (BOOLEAN, granular(name)) for name in GRANULAR},
    "sandbox_mode": (("read-only", "workspace-write", "danger-full-access"), sets("sandbox_mode")),
    "approvals_reviewer": (("user", "auto_review"), sets("approvals_reviewer")),
    "sandbox_workspace_write.network_access": (BOOLEAN, sets("workspace_network_access",
                                                             switch("enabled", "disabled"))),
    "sandbox_workspace_write.writable_roots": (NAMES, sets("workspace_writable_roots", switch("added", "none"))),
    "sandbox_workspace_write.exclude_slash_tmp": (BOOLEAN, sets("workspace_slash_tmp",
                                                                switch("excluded", "writable"))),
    "sandbox_workspace_write.exclude_tmpdir_env_var": (BOOLEAN, sets("workspace_tmpdir",
                                                                     switch("excluded", "writable"))),
    "default_permissions": (TEXT, sets("permission_profile", lambda value: BUILTIN_PROFILES.get(value, "custom"))),
    **{f"permissions.*.{leaf}": (SCALAR, custom_profile) for leaf in PERMISSION_LEAVES},
    "web_search": (("disabled", "cached", "indexed", "live"), sets("web_search")),
    "tools.web_search": (BOOLEAN, sets("web_search_tool", switch("enabled", "disabled"))),
    **{f"tools.web_search.{leaf}": (SCALAR, sets("web_search_tool", lambda value: "enabled"))
       for leaf in WEB_SEARCH_TOOL_LEAVES},
    "features.web_search": (BOOLEAN, broadens("web_search", (True,), ("indexed", "live"))),
    "features.web_search_request": (BOOLEAN, broadens("web_search", (True,), ("indexed", "live"))),
    "features.web_search_cached": (BOOLEAN, broadens("web_search", (True,), ("cached",))),
    "features.apps": (BOOLEAN, broadens("app_tool_approval", (False,), ("none",))),
    "apps.*.approvals_reviewer": (("user", "auto_review"),
                                  broadens("app_approvals_reviewer", ("auto_review",), ("auto_review",))),
    "apps.*.default_tools_approval_mode": (APPROVAL_MODES, covers("app_tool_approval", app_off)),
    "apps.*.default_tools_enabled": (BOOLEAN, enables("app_tool_approval", app_off)),
    "apps.*.enabled": (BOOLEAN, enables("app_tool_approval", app_tools_off)),
    "apps.*.destructive_enabled": (BOOLEAN, broadens("app_destructive_tools", (True,), ("enabled",), app_off)),
    "apps.*.open_world_enabled": (BOOLEAN, broadens("app_open_world_tools", (True,), ("enabled",), app_off)),
    "apps.*.tools.*.approval_mode": (APPROVAL_MODES, covers("app_tool_approval", app_tool_off)),
    "apps.*.tools.*.enabled": (BOOLEAN, enables("app_tool_approval", app_off)),
    "auto_review.policy": (TEXT, sets("auto_review_policy", lambda value: "set")),
    "auto_review.extra_policy": (TEXT, sets("auto_review_policy", lambda value: "set")),
    "mcp_servers.*.default_tools_approval_mode": (APPROVAL_MODES, covers("mcp_tool_approval", server_off)),
    "mcp_servers.*.tools.*.approval_mode": (APPROVAL_MODES, covers("mcp_tool_approval", server_tool_off)),
    "mcp_servers.*.enabled": (BOOLEAN, enables("mcp_tool_approval", server_off)),
    "mcp_servers.*.enabled_tools": (NAMES, enables("mcp_tool_approval", server_off)),
    "mcp_servers.*.disabled_tools": (NAMES, nothing),
    "mcp_servers.*.startup_timeout_sec": (NUMBER, timeout("mcp_startup_timeout_sec")),
    "mcp_servers.*.startup_timeout_ms": (NUMBER, timeout("mcp_startup_timeout_sec", 1000)),
    "mcp_servers.*.tool_timeout_sec": (NUMBER, timeout("mcp_tool_timeout_sec")),
    "plugins.*.mcp_servers.*.default_tools_approval_mode": (APPROVAL_MODES,
                                                            covers("plugin_mcp_tool_approval", plugin_server_off)),
    "plugins.*.mcp_servers.*.tools.*.approval_mode": (APPROVAL_MODES,
                                                      covers("plugin_mcp_tool_approval", plugin_server_tool_off)),
    "plugins.*.mcp_servers.*.enabled": (BOOLEAN, enables("plugin_mcp_tool_approval", plugin_server_off)),
    "plugins.*.mcp_servers.*.enabled_tools": (NAMES, enables("plugin_mcp_tool_approval", plugin_server_off)),
    "plugins.*.mcp_servers.*.disabled_tools": (NAMES, nothing),
}
MODELED_PATTERNS = {pattern(key): key for key in MODELED_SETTINGS}
# Keys that cannot act on approvals, the sandbox, the process environment, egress, execution, external
# content or configuration activation: model choice, display, notices and local history.
INERT_SETTINGS = patterns(
    "model", "model_reasoning_effort", "model_reasoning_summary", "model_verbosity",
    "model_supports_reasoning_summaries", "model_context_window", "model_auto_compact_token_limit",
    "model_auto_compact_token_limit_scope", "plan_mode_reasoning_effort", "review_model", "service_tier",
    "personality", "hide_agent_reasoning", "show_raw_agent_reasoning", "file_opener", "disable_paste_burst",
    "suppress_unstable_features_warning", "windows_wsl_setup_acknowledged",
    "tool_output_token_limit", "background_terminal_max_timeout", "project_doc_max_bytes",
    "history.persistence", "history.max_bytes",
    "mcp_servers.*.tools.*.output_token_limit",
    "agents.default_subagent_model", "agents.default_subagent_reasoning_effort",
    "agents.max_concurrent_threads_per_session", "agents.max_threads", "agents.interrupt_message",
    "features.personality", "features.goals", "features.fast_mode", "features.prevent_idle_sleep",
    "features.enable_request_compression", *(f"features.rollout_budget.{name}" for name in (
        "enabled", "limit_tokens", "prefill_token_weight", "reminder_interval_tokens", "sampling_token_weight")),
    *(f"notice.{name}" for name in (
        "hide_full_access_warning", '"hide_gpt-5.1-codex-max_migration_prompt"', "hide_gpt5_1_migration_prompt",
        "hide_rate_limit_model_nudge", "hide_world_writable_warning", "model_migrations.*")),
    *(f"tui.{name}" for name in (
        "alternate_screen", "animations", "keymap.*.*", "model_availability_nux.*", "notification_condition",
        "notification_method", "notifications", "raw_output_mode", "resume_cwd", "show_tooltips", "status_line",
        "terminal_title", "theme", "vim_mode_default")),
)
# Keys whose value decides, as (accepted values or a kind, conservative values). Environment filters only
# remove inherited variables, so every well-formed filter is conservative; `set` adds or replaces a variable
# and has no conservative value. Project trust activates project configuration, hooks and rules; an enabled
# plugin adds instructions, agents and hooks no summary judges; `features.hooks` turns on hooks beyond the
# shipped ones `codex_hook_trust` compares; a marketplace selects external plugin content; and the update
# check sends a request. Each is conservative only switched off, and a marketplace never is.
CONSERVATIVE_SETTINGS: dict[str, tuple[Any, Any]] = {
    "allow_login_shell": (BOOLEAN, (False,)),
    "shell_environment_policy.inherit": (("all", "core", "none"), ("core", "none")),
    "shell_environment_policy.ignore_default_excludes": (BOOLEAN, (False,)),
    "shell_environment_policy.experimental_use_profile": (BOOLEAN, (False,)),
    "shell_environment_policy.exclude": (NAMES, ANY),
    "shell_environment_policy.include_only": (NAMES, ANY),
    "shell_environment_policy.filters.*": (("include", "exclude"), ("include", "exclude")),
    "shell_environment_policy.set.*": (TEXT, ()),
    "projects.*.trust_level": (("trusted", "untrusted"), ("untrusted",)),
    "plugins.*.enabled": (BOOLEAN, (False,)),
    "features.hooks": (BOOLEAN, (False,)),
    "marketplaces.*.source": (TEXT, ()),
    "marketplaces.*.source_type": (("git", "local"), ()),
    "marketplaces.*.ref": (TEXT, ()),
    "marketplaces.*.sparse_paths": (NAMES, ()),
    "check_for_update_on_startup": (BOOLEAN, (False,)),
}
CONSERVATIVE_PATTERNS = {pattern(key): key for key in CONSERVATIVE_SETTINGS}


def key_path(key: Any) -> tuple[str, ...]:
    """The canonical segments of a dotted TOML key path; quoted segments keep their text without the quotes."""
    if not isinstance(key, str) or not 0 < len(key) <= MAX_KEY:
        raise SelectionError(f"codex_approval_posture settings keys are dotted key paths of at most {MAX_KEY} "
                             "characters")
    segments = []
    rest = key
    while True:
        match = SEGMENT_RE.match(rest)
        if not match:
            raise SelectionError("codex_approval_posture settings keys are dotted TOML key paths, such as "
                                 "shell_environment_policy.set.PATH or projects.\"<name>\".trust_level")
        segments.append(match.group().strip('"'))
        rest = rest[match.end():]
        if not rest:
            return tuple(segments)
        if not rest.startswith(".") or len(rest) == 1:
            raise SelectionError("codex_approval_posture settings keys join their segments with single dots")
        rest = rest[1:]


def matches(rule: tuple[str, ...], path: tuple[str, ...]) -> bool:
    """One path segment per rule segment; `*` matches one user-named segment."""
    return len(rule) == len(path) and all(want in ("*", got) for want, got in zip(rule, path, strict=True))


def rule_for(rules: dict[tuple[str, ...], str], path: tuple[str, ...]) -> str | None:
    return next((key for segments, key in rules.items() if matches(segments, path)), None)


def well_formed(value: Any, accepted: Any) -> bool:
    if accepted == BOOLEAN:
        return type(value) is bool
    if accepted == NAMES:
        return isinstance(value, list) and all(isinstance(entry, str) and entry for entry in value)
    if accepted == TEXT:
        return isinstance(value, str)
    if accepted == NUMBER:
        return type(value) in (int, float) and value > 0
    if accepted == SCALAR:
        return isinstance(value, (str, bool, int, float, list))
    return isinstance(value, str) and value in accepted


def accepted_value(rule: str, value: Any, accepted: Any) -> None:
    if not well_formed(value, accepted):
        raise SelectionError(f"codex_approval_posture setting {rule} has a malformed value")


def contradicts(required: dict[str, Check], summary: dict[str, Any]) -> bool:
    """Whether an observed summary fact or acting control fails what the key requires of it.

    A target is absent only when the caller sent no controls (the posture is then never verified) or when the
    inventory proves the control's precondition off (`proves`), so an absent target cannot act."""
    return any(target in summary and summary[target] != UNOBSERVABLE and not check(summary[target])
               for target, check in required.items())


def setting_class(path: tuple[str, ...], value: Any, settings: Settings, summary: dict[str, Any]) -> str:
    """`modeled`, `contradicted`, `inert`, `conservative`, `outside` or `unobservable` for one observed key."""
    if isinstance(value, dict):
        raise SelectionError("codex_approval_posture settings name each key of a table by its dotted path")
    if any(matches(rule, path) for rule in INERT_SETTINGS):
        return "inert"
    if value == UNOBSERVABLE:
        return UNOBSERVABLE
    modeled = rule_for(MODELED_PATTERNS, path)
    if modeled is not None:
        accepted, forces = MODELED_SETTINGS[modeled]
        accepted_value(modeled, value, accepted)
        return "contradicted" if contradicts(forces(path, value, settings), summary) else "modeled"
    rule = rule_for(CONSERVATIVE_PATTERNS, path)
    if rule is None:
        return "outside"
    accepted, conservative = CONSERVATIVE_SETTINGS[rule]
    accepted_value(rule, value, accepted)
    return "conservative" if conservative == ANY or value in conservative else "outside"


def canonical_settings(settings: dict[str, Any]) -> Settings:
    """Each key once by its canonical path; a repeated path, or a key that is also a table, is malformed."""
    canonical: Settings = {}
    for key, value in settings.items():
        path = key_path(key)
        if path in canonical:
            raise SelectionError("codex_approval_posture settings name one key path twice; a quoted segment and "
                                 "a bare segment with the same text are the same key")
        canonical[path] = value
    tables = {path[:end] for path in canonical for end in range(1, len(path))}
    if tables & canonical.keys():
        raise SelectionError("codex_approval_posture settings give one key both a value and keys under it")
    return canonical


def proves(detail: dict[str, Any], path: tuple[str, ...], value: Any) -> bool:
    """Whether the observed inventory sets `path` to exactly `value`; without a readable inventory, nothing is
    proven."""
    settings = detail.get("settings")
    if not isinstance(settings, dict) or len(settings) > MAX_SETTINGS:
        return False
    found = canonical_settings(settings).get(path)
    return type(found) is type(value) and found == value


def posture_settings(detail: dict[str, Any], summary: dict[str, Any]) -> dict[tuple[str, ...], str] | None:
    """Each observed key's class, or None when the inventory is missing or could not be read."""
    if "settings" not in detail or detail["settings"] == UNOBSERVABLE:
        return None
    settings = detail["settings"]
    if not isinstance(settings, dict) or len(settings) > MAX_SETTINGS:
        raise SelectionError(f"codex_approval_posture.posture.settings is an object of at most {MAX_SETTINGS} "
                             "dotted keys, or \"unobservable\"")
    canonical = canonical_settings(settings)
    return {path: setting_class(path, value, canonical, summary) for path, value in canonical.items()}


def settings_gaps(detail: dict[str, Any], summary: dict[str, Any]) -> tuple[int, int, str, dict[str, str]]:
    """Keys that keep the posture from verifying (outside or contradicted), unread keys, their summary and the
    fingerprint. `summary` maps each observed fact and acting control to its value.

    A missing or unreadable inventory counts as one unread key. The fingerprint holds each key path and class, never a value.
    """
    classes = posture_settings(detail, summary)
    if classes is None:
        return 0, 1, UNOBSERVABLE if "settings" in detail else "missing", {}
    outside = sum(kind == "outside" for kind in classes.values())
    contradicted = sum(kind == "contradicted" for kind in classes.values())
    unread = sum(kind == UNOBSERVABLE for kind in classes.values())
    text = ("accounted" if not outside and not contradicted and not unread
            else f"{outside} outside, {contradicted} contradicted, {unread} unobservable")
    return outside + contradicted, unread, text, {"value:posture_settings": digest(sorted(
        [list(path), kind] for path, kind in classes.items()))}
