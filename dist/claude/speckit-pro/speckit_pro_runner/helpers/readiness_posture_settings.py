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

The key table (`CODEX_KEYS`, security finding F1263-13e52d6c) is the single source of every key path the
checker reads: each row names the exact path pattern Codex reads the key from, the effect Codex gives it, and
where that is documented (the configuration reference, and the loader source where the reference is silent).
The three rule lists are checked against the table when the module loads, and an off switch is read only
through `read`, which fills a table row's user-named segments. A key path with no row has no effect for the
checker: it can never switch anything off, and when present it is `outside` (or `unobservable`).

Rules name exact leaves; a `*` matches one user-named segment, such as a profile, app or server name, and
nothing matches recursively. A name Codex gives another meaning in one position is reserved there (`reserved`):
`_default` is the apps default table, so `*` never stands for it as an app id, while `apps._default` has its
own rows for the five keys Codex reads there and `apps._default.default_tools_enabled`, which Codex ignores,
matches nothing; and in `plugins.*.enabled`, `*` stands only for a `<name>@<marketplace>` key whose marketplace
the inventory itself configures as a local or Git source, the one provably local source, since a remote
installation replaces the local enabled state of every other key. Elsewhere `_default` is an ordinary name. Any other key, an unknown
descendant of a known table included, is `outside` when its value was observed and `unobservable` when it was
not; so is a modeled or conservative key whose value is `"unobservable"`. A key absent from every layer keeps
the Codex default. Values and key names never reach the record as text: one digest holds each key path and
its class, never a value.
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
DEFAULTS = "_default"
# One TOML key segment: bare, or double-quoted without quotes, escapes or control characters.
SEGMENT_RE = re.compile(r'[A-Za-z0-9_-]+|"[^"\\\x00-\x1f\x7f]+"')

Settings = dict[tuple[str, ...], Any]
Check = Callable[[Any], bool]
# What one modeled key, given its path, value and the whole inventory, requires of the summary: each target
# fact or control name with the test its observed value must pass.
Forces = Callable[[tuple[str, ...], Any, Settings], dict[str, Check]]
Off = Callable[[tuple[str, ...], Settings], bool]
# One key table row: the rule list the key belongs to, the effect Codex gives it, and where that is documented.
Row = tuple[str, str, str]


def pattern(key: str) -> tuple[str, ...]:
    """A rule key as segments; a quoted segment may hold dots."""
    return tuple(part.strip('"') for part in re.findall(r'"[^"]*"|[^.]+', key))


def patterns(*keys: str) -> tuple[tuple[str, ...], ...]:
    return tuple(pattern(key) for key in keys)


# Marketplace sources Codex loads from the user's own configuration (`marketplaces.<name>.source_type`,
# core-plugins/src/marketplace_policy.rs policy_filtered_plugin_config). A plugin from one of them is local; a
# remote installation replaces the local enabled state of any other plugin key (core-plugins/src/loader.rs
# merge_configured_plugins_with_remote_installed, merge_remote_plugin_config; remote.rs names the remote families).
LOCAL_SOURCES = ("local", "git")


def local_plugin(settings: Settings | None, name: str) -> bool:
    """Whether `name` is a `<name>@<marketplace>` plugin key (core-plugin-common/src/plugin_id.rs PluginId::parse)
    whose marketplace the inventory configures as a local source; without an inventory nothing is proven."""
    plugin, at, marketplace = name.rpartition("@")
    return bool(at and plugin and settings is not None
                and read(settings, "marketplaces.*.source_type", marketplace) in LOCAL_SOURCES)


def reserved(rule: tuple[str, ...], index: int, name: str, settings: Settings | None) -> bool:
    """Whether `*` at `index` of `rule` never stands for `name`, since Codex gives it another meaning there."""
    if rule[:index] == ("apps",):
        return name == DEFAULTS
    if rule == ("plugins", "*", "enabled"):
        return not local_plugin(settings, name)
    return False


def matches(rule: tuple[str, ...], path: tuple[str, ...], settings: Settings | None = None) -> bool:
    """One path segment per rule segment; `*` matches one user-named segment that is not reserved there, which
    for a plugin's own switch the inventory must prove."""
    return len(rule) == len(path) and all(
        want == got or (want == "*" and not reserved(rule, index, got, settings))
        for index, (want, got) in enumerate(zip(rule, path, strict=True)))


def rule_for(rules: dict[tuple[str, ...], str], path: tuple[str, ...], settings: Settings | None = None) -> str | None:
    return next((key for segments, key in rules.items() if matches(segments, path, settings)), None)


MODELED = "modeled"
INERT = "inert"
CONSERVATIVE = "conservative"
REFERENCE = "learn.chatgpt.com/docs/config-file/config-reference#configtoml"
# Loader sources, under github.com/openai/codex codex-rs, for effects the reference leaves implicit.
PLUGIN_FEATURE = "core/src/mcp.rs selected_plugins (Feature::Plugins gates every plugin MCP contribution)"
LOCAL_PROOF = ("core-plugins/src/marketplace_policy.rs policy_filtered_plugin_config; core-plugins/src/remote.rs "
               "remote_plugin_canonical_marketplace_name; core-plugin-common/src/plugin_id.rs PluginId::parse")
HOOKS_ALIAS = "features/src/legacy.rs ALIASES (codex_hooks maps to the hooks feature)"
REMOTE_CATALOG = "core-plugins/src/manager.rs remote_global_catalog_active"
CONTENT_DEFAULT = "config/src/config_toml.rs DEFAULT_PROJECT_DOC_MAX_BYTES (32 KiB, Option<usize>; 0 skips the docs)"
APP_POLICY = "connectors/src/app_tool_policy.rs app_tool_policy_from_apps_config"
APP_ENABLED = "connectors/src/app_tool_policy.rs app_is_enabled; config/src/types.rs AppConfig, AppsDefaultConfig"
MCP_FILTER = "codex-mcp/src/tools.rs ToolFilter::allows"
PLUGIN_LOADER = "core-plugins/src/loader.rs"
STRICT = "config/src/loader/mod.rs validate_config_toml_strictly (an unknown key is ignored unless strict)"


def row(kind: str, effect: str, source: str = "") -> Row:
    """A key table row: the reference row of the same name, plus the loader source where one is needed."""
    return kind, effect, REFERENCE + (f"; {source}" if source else "")


def rows(kind: str, effect: str, *keys: str, source: str = "") -> dict[str, Row]:
    return {key: row(kind, effect, source) for key in keys}


APP_ID = "apps.*"
APP_DEFAULTS = f"apps.{DEFAULTS}"
MCP = "mcp_servers.*"
PLUGIN_MCP = "plugins.*.mcp_servers.*"
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
GRANULAR = ("sandbox_approval", "rules", "mcp_elicitations", "request_permissions", "skill_approval")
# Keys that cannot act on approvals, the sandbox, the process environment, egress, execution, external
# content or configuration activation: model choice, display, notices and local history.
INERT_SETTINGS = patterns(
    "model", "model_reasoning_effort", "model_reasoning_summary", "model_verbosity",
    "model_supports_reasoning_summaries", "model_context_window", "model_auto_compact_token_limit",
    "model_auto_compact_token_limit_scope", "plan_mode_reasoning_effort", "review_model", "service_tier",
    "personality", "hide_agent_reasoning", "show_raw_agent_reasoning", "file_opener", "disable_paste_burst",
    "suppress_unstable_features_warning", "windows_wsl_setup_acknowledged",
    "background_terminal_max_timeout", "history.persistence", "history.max_bytes",
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
INERT_EFFECT = "model choice, display, notice, limit or local history setting; cannot act"
# The key table: every key path the checker reads, under the exact pattern Codex reads it from (`*` is one
# user-named id; `_default` is literal), with the effect Codex gives it and its citation. Off switches say
# which value switches what off; a key Codex reads only under a concrete id says so.
CODEX_KEYS: dict[str, Row] = {
    "approval_policy": row(MODELED, "when Codex pauses for approval before executing commands"),
    **rows(MODELED, "whether that approval prompt category surfaces instead of being auto-rejected",
           *(f"approval_policy.granular.{name}" for name in GRANULAR)),
    "sandbox_mode": row(MODELED, "the sandbox policy for filesystem and network access; `read-only` leaves the "
                                 "workspace-write keys without effect"),
    "approvals_reviewer": row(MODELED, "who reviews eligible approval prompts under on-request or granular "
                                       "policies; `auto_review` is the reviewer subagent"),
    "sandbox_workspace_write.network_access": row(MODELED, "outbound network inside the workspace-write sandbox"),
    "sandbox_workspace_write.writable_roots": row(MODELED, "additional writable roots under workspace-write"),
    "sandbox_workspace_write.exclude_slash_tmp": row(MODELED, "whether /tmp stays out of the writable roots"),
    "sandbox_workspace_write.exclude_tmpdir_env_var": row(MODELED, "whether $TMPDIR stays out of the writable roots"),
    "default_permissions": row(MODELED, "the permissions profile for sandboxed tool calls: a built-in, or a "
                                        "custom `permissions.<name>` profile"),
    **rows(MODELED, "one rule of a custom permissions profile; it acts when the profile is selected or named "
                    "like a built-in", *(f"permissions.*.{leaf}" for leaf in PERMISSION_LEAVES)),
    "web_search": row(MODELED, "the web search mode"),
    "tools.web_search": row(MODELED, "the web search tool; the table form enables it with options"),
    **rows(MODELED, "an option of the web search tool table, which enables the tool",
           *(f"tools.web_search.{leaf}" for leaf in WEB_SEARCH_TOOL_LEAVES)),
    "features.web_search": row(MODELED, "deprecated legacy web search toggle"),
    "features.web_search_request": row(MODELED, "deprecated legacy toggle; `true` maps to `web_search = \"live\"`"),
    "features.web_search_cached": row(MODELED, "deprecated legacy toggle; `true` maps to `web_search = \"cached\"`"),
    "features.apps": row(MODELED, "app (connector) integrations; `false` switches every app off"),
    f"{APP_DEFAULTS}.approvals_reviewer": row(MODELED, "default reviewer for app tool approval prompts unless "
                                                       "overridden per app"),
    f"{APP_DEFAULTS}.default_tools_approval_mode": row(MODELED, "default approval for app tools without per-app "
                                                                "or per-tool overrides", APP_POLICY),
    f"{APP_DEFAULTS}.destructive_enabled": row(MODELED, "default allow/deny for app tools with "
                                                        "`destructive_hint = true` (a tool without hints counts "
                                                        "as hinted) unless set per app", APP_POLICY),
    f"{APP_DEFAULTS}.enabled": row(MODELED, "default enabled state for apps with no `[apps.<id>]` table; an app "
                                            "with any key set keeps its own `enabled` (default true), so `false` "
                                            "switches off no app the inventory names", APP_ENABLED),
    f"{APP_DEFAULTS}.open_world_enabled": row(MODELED, "default allow/deny for app tools with "
                                                       "`open_world_hint = true` unless set per app", APP_POLICY),
    f"{APP_ID}.approvals_reviewer": row(MODELED, "reviewer for this app's tool approval prompts"),
    f"{APP_ID}.default_tools_approval_mode": row(MODELED, "default approval for this app's tools unless a "
                                                          "per-tool override exists", APP_POLICY),
    f"{APP_ID}.default_tools_enabled": row(MODELED, "default enabled state for this app's tools unless a per-tool "
                                                    "`enabled` overrides it; `false` switches the app's tools off. "
                                                    "Read for a concrete app id only: under `_default` Codex "
                                                    "ignores it", f"{APP_POLICY}; {STRICT}"),
    f"{APP_ID}.destructive_enabled": row(MODELED, "allow or block this app's tools with `destructive_hint = true`",
                                         APP_POLICY),
    f"{APP_ID}.enabled": row(MODELED, "`false` switches this app off", APP_ENABLED),
    f"{APP_ID}.open_world_enabled": row(MODELED, "allow or block this app's tools with `open_world_hint = true`",
                                        APP_POLICY),
    f"{APP_ID}.tools.*.approval_mode": row(MODELED, "per-tool approval override for one app tool", APP_POLICY),
    f"{APP_ID}.tools.*.enabled": row(MODELED, "per-tool enabled override: `false` switches the tool off, `true` "
                                              "enables it over the app default", APP_POLICY),
    "auto_review.policy": row(MODELED, "local policy instructions for automatic review"),
    "auto_review.extra_policy": row(MODELED, "additional local policy for automatic review"),
    f"{MCP}.default_tools_approval_mode": row(MODELED, "default approval for this server's tools unless a "
                                                       "per-tool override exists"),
    f"{MCP}.tools.*.approval_mode": row(MODELED, "per-tool approval override for one MCP tool"),
    f"{MCP}.enabled": row(MODELED, "`false` switches this MCP server off"),
    f"{MCP}.enabled_tools": row(MODELED, "allow list of this server's tools: a tool left out is off, and `[]` "
                                         "exposes none", MCP_FILTER),
    f"{MCP}.disabled_tools": row(MODELED, "deny list applied after `enabled_tools`: a listed tool is off",
                                 MCP_FILTER),
    f"{MCP}.startup_timeout_sec": row(MODELED, "this server's startup timeout, default 10 s"),
    f"{MCP}.startup_timeout_ms": row(MODELED, "alias of `startup_timeout_sec` in whole milliseconds (u64)",
                                     "config/src/mcp_types.rs RawMcpServerConfig"),
    f"{MCP}.tool_timeout_sec": row(MODELED, "this server's per-tool timeout, default 60 s"),
    f"{PLUGIN_MCP}.default_tools_approval_mode": row(MODELED, "default approval for a plugin-provided server's "
                                                              "tools", PLUGIN_LOADER),
    f"{PLUGIN_MCP}.tools.*.approval_mode": row(MODELED, "per-tool approval override for a plugin-provided MCP "
                                                        "tool", PLUGIN_LOADER),
    f"{PLUGIN_MCP}.enabled": row(MODELED, "`false` switches this plugin-provided MCP server off", PLUGIN_LOADER),
    f"{PLUGIN_MCP}.enabled_tools": row(MODELED, "allow list of a plugin-provided server's tools: a tool left out "
                                                "is off, and `[]` exposes none", f"{PLUGIN_LOADER}; {MCP_FILTER}"),
    f"{PLUGIN_MCP}.disabled_tools": row(MODELED, "deny list applied after `enabled_tools`: a listed tool is off",
                                        f"{PLUGIN_LOADER}; {MCP_FILTER}"),
    "allow_login_shell": row(CONSERVATIVE, "login-shell semantics for shell tools; `false` is conservative"),
    "shell_environment_policy.inherit": row(CONSERVATIVE, "baseline environment inheritance; `core` or `none` "
                                                          "is conservative"),
    "shell_environment_policy.ignore_default_excludes": row(CONSERVATIVE, "keeps KEY, SECRET and TOKEN variables "
                                                                          "when true; `false` is conservative"),
    "shell_environment_policy.experimental_use_profile": row(CONSERVATIVE, "spawns subprocesses through the user "
                                                                           "shell profile; `false` is conservative"),
    **rows(CONSERVATIVE, "removes inherited variables only, so every well-formed filter is conservative",
           "shell_environment_policy.exclude", "shell_environment_policy.include_only",
           "shell_environment_policy.filters.*"),
    "shell_environment_policy.set.*": row(CONSERVATIVE, "adds or replaces one variable; no conservative value"),
    "projects.*.trust_level": row(CONSERVATIVE, "`trusted` activates project configuration, hooks and rules; "
                                                "`untrusted` is conservative"),
    "plugins.*.enabled": row(CONSERVATIVE, "`false` switches off a plugin from a marketplace the inventory "
                                           "configures as a local or Git source, its MCP servers included; no "
                                           "summary judges an enabled plugin's instructions, agents and hooks. "
                                           "`*` stands for that key only: a remote installation replaces the "
                                           "local enabled state of a plugin from any other source, so a remote "
                                           "family, a managed, unconfigured or user-named marketplace, and a "
                                           "bare name prove nothing", f"{PLUGIN_LOADER}; {LOCAL_PROOF}"),
    "features.plugins": row(CONSERVATIVE, "plugin availability; `false` switches off every plugin contribution, "
                                          "MCP servers included, whatever the plugin's source", PLUGIN_FEATURE),
    "features.remote_plugin": row(CONSERVATIVE, "the remote plugin catalog; `false` is conservative, and cached "
                                                "remote installs still merge, so it never makes a managed "
                                                "plugin's local `enabled` provable", REMOTE_CATALOG),
    "features.hooks": row(CONSERVATIVE, "lifecycle hooks beyond the shipped ones `codex_hook_trust` compares; "
                                        "`false` is conservative"),
    "features.codex_hooks": row(CONSERVATIVE, "deprecated alias of `features.hooks`; judged alone, so either "
                                              "spelling at `true` is outside", HOOKS_ALIAS),
    "project_doc_max_bytes": row(CONSERVATIVE, "whole bytes of project instructions read into the model's context "
                                               "(0 reads none); conservative at or under the 32 KiB default",
                                 CONTENT_DEFAULT),
    "tool_output_token_limit": row(CONSERVATIVE, "whole tokens of tool output kept in history (Option<usize>); the "
                                                 "model sets the default, so no value is provably conservative",
                                   "config/src/config_toml.rs ConfigToml"),
    f"{MCP}.tools.*.output_token_limit": row(CONSERVATIVE, "whole non-zero tokens of one MCP tool's serialized "
                                                           "output (NonZeroUsize); the model sets the default, so "
                                                           "no value is provably conservative",
                                             "config/src/mcp_types.rs McpServerToolConfig"),
    **rows(CONSERVATIVE, "selects external plugin content; no conservative value", "marketplaces.*.source",
           "marketplaces.*.source_type", "marketplaces.*.ref", "marketplaces.*.sparse_paths"),
    "check_for_update_on_startup": row(CONSERVATIVE, "sends an update request on startup; `false` is conservative"),
    **{".".join(f'"{part}"' if "." in part else part for part in rule): row(INERT, INERT_EFFECT)
       for rule in INERT_SETTINGS},
}


def check_table(kind: str, rules: dict[str, Any]) -> None:
    """One rule list must name exactly the key table rows of its kind, so no rule exists without a row."""
    expected = {key for key, (row_kind, _, _) in CODEX_KEYS.items() if row_kind == kind}
    if set(rules) != expected:
        raise LookupError(f"the {kind} settings rules and the Codex key table disagree: "
                          f"{sorted(set(rules) ^ expected)}")


def read(settings: Settings, rule: str, *names: str) -> Any:
    """The inventory's value of key table row `rule` with its `*` segments filled by `names`, or None when the
    filled path is not one Codex reads that key from (a reserved name under `*`); a key with no row never
    switches anything off."""
    if rule not in CODEX_KEYS:
        raise LookupError(f"{rule} is not in the Codex key table")
    segments = iter(names)
    path = tuple(next(segments) if segment == "*" else segment for segment in pattern(rule))
    return settings.get(path) if matches(pattern(rule), path, settings) else None


BOOLEAN = "boolean"
NAMES = "names"
TEXT = "text"
NUMBER = "number"
COUNT = "count"
POSITIVE_COUNT = "positive count"
SCALAR = "scalar"
ANY = "any"
BROAD_MODES = ("auto", "writes", "approve")
APPROVAL_MODES = ("prompt", *BROAD_MODES)
BUILTIN_PROFILES = {":read-only": "read-only", ":workspace": "workspace", ":danger-full-access": "danger-full-access"}


def one_of(*values: Any) -> Check:
    return lambda observed: observed in values


def sets(target: str, convert: Callable[[Any], Any] = lambda value: value) -> Forces:
    """The key alone sets the fact or control, so the summary must hold exactly its value."""
    return lambda path, value, settings: {target: one_of(convert(value))}


def never_off(path: tuple[str, ...], settings: Settings) -> bool:
    return False


def broadens(target: str, trigger: tuple[Any, ...], allowed: tuple[Any, ...], off: Off = never_off) -> Forces:
    """One entry of an aggregate control: a value in `trigger` requires `allowed` unless the inventory switches
    its app, server or tool off. Another value settles nothing alone, since other entries decide the aggregate."""
    return lambda path, value, settings: ({target: one_of(*allowed)}
                                          if value in trigger and not off(path, settings) else {})


def nothing(path: tuple[str, ...], value: Any, settings: Settings) -> dict[str, Check]:
    """A disabled-tools list only narrows the tools the other keys enable."""
    return {}


def some_tool(observed: Any) -> bool:
    return observed != "none"


def enables(target: str, off: Off) -> Forces:
    """An explicit enablement (true, or a non-empty tool list) means a tool is enabled unless the inventory
    switches it off, so the aggregate `target` cannot be `none`."""
    return lambda path, value, settings: ({target: some_tool}
                                          if (value is True or isinstance(value, list) and value)
                                          and not off(path, settings) else {})


def covers(target: str, off: Off) -> Forces:
    """An approval mode for tools the inventory does not switch off: the aggregate `target` must cover it, so a
    broad mode needs a broad aggregate and `prompt` rules out `none`."""
    return lambda path, value, settings: ({} if off(path, settings) else
                                          {target: one_of(*BROAD_MODES) if value in BROAD_MODES else some_tool})


# Off switches. Each reads the key table through `read`, so a switch Codex reads only for a concrete app id
# (`default_tools_enabled`, a per-tool `enabled`) is unset under `_default`, and `apps._default.enabled` never
# switches off an app the inventory names.
def off_at(settings: Settings, rule: str, *names: str) -> bool:
    """Whether the inventory sets key table row `rule`, filled by `names`, to false."""
    return read(settings, rule, *names) is False


def apps_off(path: tuple[str, ...], settings: Settings) -> bool:
    """`features.apps = false` switches every app off."""
    return off_at(settings, "features.apps")


def or_app_key_off(off: Off, rule: str) -> Off:
    """`off`, or the app's key table row `rule` (an `apps.*` leaf) set to false; `_default` never fills it."""
    return lambda path, settings: off(path, settings) or off_at(settings, rule, path[1])


# Apps are off, or this app is.
app_off: Off = or_app_key_off(apps_off, f"{APP_ID}.enabled")
# The app is off, or its tools are off by default (an explicitly enabled tool forces on its own).
app_tools_off: Off = or_app_key_off(app_off, f"{APP_ID}.default_tools_enabled")


def app_tool_off(path: tuple[str, ...], settings: Settings) -> bool:
    """The app is off, or the tool is: its own `enabled` decides, else the app's default."""
    own = read(settings, f"{APP_ID}.tools.*.enabled", path[1], path[3])
    return app_off(path, settings) or (
        read(settings, f"{APP_ID}.default_tools_enabled", path[1]) if own is None else own) is False


def tools_off(server: str, settings: Settings, *names: str) -> bool:
    """An MCP server (`server` is its key table prefix) switched off, or one whose enabled-tools list is empty."""
    return off_at(settings, f"{server}.enabled", *names) or read(settings, f"{server}.enabled_tools", *names) == []


def tool_listed_off(server: str, settings: Settings, names: tuple[str, ...], tool: str) -> bool:
    """A tool the server's lists switch off: named in `disabled_tools`, or left out of `enabled_tools`."""
    enabled = read(settings, f"{server}.enabled_tools", *names)
    disabled = read(settings, f"{server}.disabled_tools", *names)
    return (isinstance(disabled, list) and tool in disabled) or (isinstance(enabled, list) and tool not in enabled)


def server_off(path: tuple[str, ...], settings: Settings) -> bool:
    return tools_off(MCP, settings, path[1])


def server_tool_off(path: tuple[str, ...], settings: Settings) -> bool:
    return server_off(path, settings) or tool_listed_off(MCP, settings, (path[1],), path[3])


def plugin_server_off(path: tuple[str, ...], settings: Settings) -> bool:
    """Plugins are off, this plugin is (a user-configured marketplace only), or its server is."""
    return off_at(settings, "features.plugins") or off_at(settings, "plugins.*.enabled", path[1]) \
        or tools_off(PLUGIN_MCP, settings, path[1], path[3])


def plugin_server_tool_off(path: tuple[str, ...], settings: Settings) -> bool:
    return plugin_server_off(path, settings) or tool_listed_off(PLUGIN_MCP, settings, (path[1], path[3]), path[5])


def timeout(target: str, per_second: int = 1) -> Forces:
    """A server timeout the summary must cover: the summary is whole seconds no smaller than it."""
    return lambda path, value, settings: {target: lambda observed: type(observed) is int
                                          and value <= observed * per_second}


def custom_profile(path: tuple[str, ...], value: Any, settings: Settings) -> dict[str, Check]:
    """A leaf of the selected profile, or of a profile named like a built-in one, makes the profile custom."""
    name = path[1]
    if name.startswith(":") or read(settings, "default_permissions") == name:
        return {"permission_profile": one_of("custom")}
    return {}


def granular(name: str) -> Forces:
    return lambda path, value, settings: {"approval_policy": one_of("granular"),
                                          f"approval_policy.granular.{name}": one_of(value)}


def switch(on: str, off: str) -> Callable[[Any], str]:
    return lambda value: on if value else off


def app_rules(prefix: str, off: Off, enabled_off: Off) -> dict[str, tuple[Any, Forces]]:
    """The app keys Codex reads both per app and under `_default`, as (accepted values, what they require);
    `enabled_off` is what switches off the tools an `enabled = true` would enable."""
    return {
        f"{prefix}.approvals_reviewer": (("user", "auto_review"),
                                         broadens("app_approvals_reviewer", ("auto_review",), ("auto_review",))),
        f"{prefix}.default_tools_approval_mode": (APPROVAL_MODES, covers("app_tool_approval", off)),
        f"{prefix}.enabled": (BOOLEAN, enables("app_tool_approval", enabled_off)),
        f"{prefix}.destructive_enabled": (BOOLEAN, broadens("app_destructive_tools", (True,), ("enabled",), off)),
        f"{prefix}.open_world_enabled": (BOOLEAN, broadens("app_open_world_tools", (True,), ("enabled",), off)),
    }


def mcp_rules(prefix: str, target: str, off: Off, tool_off: Off) -> dict[str, tuple[Any, Forces]]:
    """The tool policy keys of an MCP server or a plugin-provided one, as (accepted values, what they require)."""
    return {
        f"{prefix}.default_tools_approval_mode": (APPROVAL_MODES, covers(target, off)),
        f"{prefix}.tools.*.approval_mode": (APPROVAL_MODES, covers(target, tool_off)),
        f"{prefix}.enabled": (BOOLEAN, enables(target, off)),
        f"{prefix}.enabled_tools": (NAMES, enables(target, off)),
        f"{prefix}.disabled_tools": (NAMES, nothing),
    }


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
    # `_default` has no `default_tools_enabled`, so only `features.apps` switches its keys off.
    **app_rules(APP_DEFAULTS, app_off, app_off),
    **app_rules(APP_ID, app_off, app_tools_off),
    f"{APP_ID}.default_tools_enabled": (BOOLEAN, enables("app_tool_approval", app_off)),
    f"{APP_ID}.tools.*.approval_mode": (APPROVAL_MODES, covers("app_tool_approval", app_tool_off)),
    f"{APP_ID}.tools.*.enabled": (BOOLEAN, enables("app_tool_approval", app_off)),
    "auto_review.policy": (TEXT, sets("auto_review_policy", lambda value: "set")),
    "auto_review.extra_policy": (TEXT, sets("auto_review_policy", lambda value: "set")),
    **mcp_rules(MCP, "mcp_tool_approval", server_off, server_tool_off),
    f"{MCP}.startup_timeout_sec": (NUMBER, timeout("mcp_startup_timeout_sec")),
    f"{MCP}.startup_timeout_ms": (POSITIVE_COUNT, timeout("mcp_startup_timeout_sec", 1000)),
    f"{MCP}.tool_timeout_sec": (NUMBER, timeout("mcp_tool_timeout_sec")),
    **mcp_rules(PLUGIN_MCP, "plugin_mcp_tool_approval", plugin_server_off, plugin_server_tool_off),
}
check_table(MODELED, MODELED_SETTINGS)
MODELED_PATTERNS = {pattern(key): key for key in MODELED_SETTINGS}
PROJECT_DOC_MAX_BYTES = 32 * 1024
# Keys whose value decides, as (accepted values or a kind, conservative values or a test). Environment filters only
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
    "features.plugins": (BOOLEAN, (False,)),
    "features.remote_plugin": (BOOLEAN, (False,)),
    "features.hooks": (BOOLEAN, (False,)),
    "features.codex_hooks": (BOOLEAN, (False,)),
    "project_doc_max_bytes": (COUNT, lambda value: value <= PROJECT_DOC_MAX_BYTES),
    "tool_output_token_limit": (COUNT, ()),
    f"{MCP}.tools.*.output_token_limit": (POSITIVE_COUNT, ()),
    "marketplaces.*.source": (TEXT, ()),
    "marketplaces.*.source_type": (("git", "local"), ()),
    "marketplaces.*.ref": (TEXT, ()),
    "marketplaces.*.sparse_paths": (NAMES, ()),
    "check_for_update_on_startup": (BOOLEAN, (False,)),
}
check_table(CONSERVATIVE, CONSERVATIVE_SETTINGS)
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


def well_formed(value: Any, accepted: Any) -> bool:
    if accepted == BOOLEAN:
        return type(value) is bool
    if accepted == NAMES:
        return isinstance(value, list) and all(isinstance(entry, str) and entry for entry in value)
    if accepted == TEXT:
        return isinstance(value, str)
    if accepted == NUMBER:
        return type(value) in (int, float) and value > 0
    if accepted == COUNT:
        return type(value) is int and value >= 0
    if accepted == POSITIVE_COUNT:
        return type(value) is int and value > 0
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
    modeled = rule_for(MODELED_PATTERNS, path, settings)
    if modeled is not None:
        accepted, forces = MODELED_SETTINGS[modeled]
        accepted_value(modeled, value, accepted)
        return "contradicted" if contradicts(forces(path, value, settings), summary) else "modeled"
    rule = rule_for(CONSERVATIVE_PATTERNS, path, settings)
    if rule is None:
        return "outside"
    accepted, conservative = CONSERVATIVE_SETTINGS[rule]
    accepted_value(rule, value, accepted)
    held = conservative(value) if callable(conservative) else conservative == ANY or value in conservative
    return "conservative" if held else "outside"


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


def proves(detail: dict[str, Any], rule: str, value: Any) -> bool:
    """Whether the observed inventory sets the key table row `rule` to exactly `value`; without a readable
    inventory, nothing is proven."""
    settings = detail.get("settings")
    if not isinstance(settings, dict) or len(settings) > MAX_SETTINGS:
        return False
    found = read(canonical_settings(settings), rule)
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
