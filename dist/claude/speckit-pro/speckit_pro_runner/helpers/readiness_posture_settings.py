"""The Codex configuration inventory behind `codex_approval_posture` (ADR 0008, security finding F1263-946bd436).

Scaffold sends every configuration key set in any effective layer as a dotted TOML key path with its value.
Each key is accounted for in one of three ways, or the posture never verifies:

- a summary fact or posture control already judges it (`MODELED_SETTINGS`);
- it cannot act on approvals, the sandbox, the process environment, egress or execution (`INERT_SETTINGS`);
- it holds its conservative value (`CONSERVATIVE_SETTINGS`).

Any other key, a name this module does not know included, is `outside` when its value was observed and
`unobservable` when it was not. A key absent from every layer keeps the Codex default, which no project file
sets. Key lists follow the Codex configuration reference (learn.chatgpt.com/docs/config-file/config-reference).
Patterns match one segment per `*`; a final `**` matches one or more. Values and key names never reach the
record as text: one digest holds each key path and its class, never a value.
"""

from __future__ import annotations

import re
from typing import Any

from ..agent_materialization import digest
from ..strict_input import SelectionError

UNOBSERVABLE = "unobservable"
MAX_SETTINGS = 512
MAX_KEY = 256
# One TOML key segment: bare, or double-quoted without quotes, escapes or control characters.
SEGMENT_RE = re.compile(r'[A-Za-z0-9_-]+|"[^"\\\x00-\x1f\x7f]+"')


def pattern(key: str) -> tuple[str, ...]:
    """A rule key as segments; a quoted segment may hold dots."""
    return tuple(part.strip('"') for part in re.findall(r'"[^"]*"|[^.]+', key))


def patterns(*keys: str) -> tuple[tuple[str, ...], ...]:
    return tuple(pattern(key) for key in keys)


# Keys a summary fact or posture control judges. Their values are read there, so they are accounted for here.
MODELED_SETTINGS = patterns(
    "approval_policy", *(f"approval_policy.granular.{name}" for name in (
        "sandbox_approval", "rules", "mcp_elicitations", "request_permissions", "skill_approval")),
    "sandbox_mode", "approvals_reviewer",
    *(f"sandbox_workspace_write.{name}" for name in (
        "network_access", "writable_roots", "exclude_slash_tmp", "exclude_tmpdir_env_var")),
    "default_permissions", "permissions.*.**",  # any custom profile in use is `permission_profile=custom`
    "web_search", "tools.web_search", "tools.web_search.**", "features.web_search", "features.web_search_cached",
    "features.web_search_request",
    "features.apps", *(f"apps.*.{name}" for name in (
        "approvals_reviewer", "default_tools_approval_mode", "default_tools_enabled", "destructive_enabled",
        "enabled", "open_world_enabled")), "apps.*.tools.*.approval_mode", "apps.*.tools.*.enabled",
    "auto_review.policy", "auto_review.extra_policy",
    *(f"mcp_servers.*.{name}" for name in (
        "default_tools_approval_mode", "enabled_tools", "disabled_tools", "enabled", "startup_timeout_sec",
        "startup_timeout_ms", "tool_timeout_sec")), "mcp_servers.*.tools.*.approval_mode",
    "plugins.*.enabled", *(f"plugins.*.mcp_servers.*.{name}" for name in (
        "default_tools_approval_mode", "enabled_tools", "disabled_tools", "enabled")),
    "plugins.*.mcp_servers.*.tools.*.approval_mode",
    "features.hooks",  # each loaded hook is judged by codex_hook_trust
)
# Keys that cannot act on approvals, the sandbox, the process environment, egress or execution.
INERT_SETTINGS = patterns(
    "model", "model_reasoning_effort", "model_reasoning_summary", "model_verbosity",
    "model_supports_reasoning_summaries", "model_context_window", "model_auto_compact_token_limit",
    "model_auto_compact_token_limit_scope", "plan_mode_reasoning_effort", "review_model", "service_tier",
    "personality", "hide_agent_reasoning", "show_raw_agent_reasoning", "file_opener", "disable_paste_burst",
    "check_for_update_on_startup", "suppress_unstable_features_warning", "windows_wsl_setup_acknowledged",
    "tool_output_token_limit", "background_terminal_max_timeout", "project_doc_max_bytes",
    "history.persistence", "history.max_bytes", "projects.*.trust_level",
    "marketplaces.*.source", "marketplaces.*.source_type", "marketplaces.*.ref", "marketplaces.*.sparse_paths",
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
BOOLEAN = "boolean"
NAMES = "names"
TEXT = "text"
ANY = "any"
# Keys whose value decides, as (accepted values or a kind, conservative values). Environment filters only
# remove inherited variables, so every well-formed filter is conservative; `set` adds or replaces a variable
# and has no conservative value.
CONSERVATIVE_SETTINGS: dict[str, tuple[Any, Any]] = {
    "allow_login_shell": (BOOLEAN, (False,)),
    "shell_environment_policy.inherit": (("all", "core", "none"), ("core", "none")),
    "shell_environment_policy.ignore_default_excludes": (BOOLEAN, (False,)),
    "shell_environment_policy.experimental_use_profile": (BOOLEAN, (False,)),
    "shell_environment_policy.exclude": (NAMES, ANY),
    "shell_environment_policy.include_only": (NAMES, ANY),
    "shell_environment_policy.filters.*": (("include", "exclude"), ("include", "exclude")),
    "shell_environment_policy.set.*": (TEXT, ()),
}
CONSERVATIVE_PATTERNS = {pattern(key): key for key in CONSERVATIVE_SETTINGS}


def key_path(key: Any) -> tuple[str, ...]:
    """The segments of a dotted TOML key path; quoted segments keep their text without the quotes."""
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
    if rule and rule[-1] == "**":
        head = rule[:-1]
        return len(path) > len(head) and matches(head, path[:len(head)])
    return len(rule) == len(path) and all(want in ("*", got) for want, got in zip(rule, path, strict=True))


def well_formed(value: Any, accepted: Any) -> bool:
    if accepted == BOOLEAN:
        return type(value) is bool
    if accepted == NAMES:
        return isinstance(value, list) and all(isinstance(entry, str) and entry for entry in value)
    if accepted == TEXT:
        return isinstance(value, str)
    return isinstance(value, str) and value in accepted


def setting_class(path: tuple[str, ...], value: Any) -> str:
    """`modeled`, `inert`, `conservative`, `outside` or `unobservable` for one observed key."""
    if isinstance(value, dict):
        raise SelectionError("codex_approval_posture settings name each key of a table by its dotted path")
    if any(matches(rule, path) for rule in MODELED_SETTINGS):
        return "modeled"
    if any(matches(rule, path) for rule in INERT_SETTINGS):
        return "inert"
    if value == UNOBSERVABLE:
        return UNOBSERVABLE
    rule = next((key for segments, key in CONSERVATIVE_PATTERNS.items() if matches(segments, path)), None)
    if rule is None:
        return "outside"
    accepted, conservative = CONSERVATIVE_SETTINGS[rule]
    if not well_formed(value, accepted):
        raise SelectionError(f"codex_approval_posture setting {rule} has a malformed value")
    return "conservative" if conservative == ANY or value in conservative else "outside"


def posture_settings(detail: dict[str, Any]) -> dict[tuple[str, ...], str] | None:
    """Each observed key's class, or None when the inventory is missing or could not be read."""
    if "settings" not in detail or detail["settings"] == UNOBSERVABLE:
        return None
    settings = detail["settings"]
    if not isinstance(settings, dict) or len(settings) > MAX_SETTINGS:
        raise SelectionError(f"codex_approval_posture.posture.settings is an object of at most {MAX_SETTINGS} "
                             "dotted keys, or \"unobservable\"")
    classes = {}
    for key, value in settings.items():
        path = key_path(key)
        classes[path] = setting_class(path, value)
    return classes


def settings_gaps(detail: dict[str, Any]) -> tuple[int, int, str, dict[str, str]]:
    """Counts of keys outside the conservative profile and of unread keys, their summary, and the fingerprint.

    A missing or unreadable inventory counts as one unread key. The fingerprint holds each key path and class, never a value.
    """
    classes = posture_settings(detail)
    if classes is None:
        return 0, 1, UNOBSERVABLE if "settings" in detail else "missing", {}
    outside = sum(kind == "outside" for kind in classes.values())
    unread = sum(kind == UNOBSERVABLE for kind in classes.values())
    text = "accounted" if not outside and not unread else f"{outside} outside, {unread} unobservable"
    return outside, unread, text, {"value:posture_settings": digest(sorted([list(path), kind]
                                                                            for path, kind in classes.items()))}
