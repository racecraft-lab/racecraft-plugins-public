"""Value-free preflight for the research broker's screening dependencies.

The research broker screens fetched web and docs content. It uses Jev through
the typesafe-jev plugin's `evaluate` binary when a credential source exists, and
a stricter deterministic sanitizer when none does. This module decides which,
without ever reading a Jev credential:

- The binary is found the way the typesafe-jev launcher finds it:
  `EVALUATE_BIN`, then `~/.local/libexec/racecraft-jev/evaluate`.
- `evaluate version` gives the binary version. Older than the first release
  with `evaluate call` counts as unusable.
- `evaluate call --check --plugin-defaults` loads the credential in Go and
  exits with a code: 0 usable, 3 nothing configured, 4 configured but unusable.
- When the binary is missing, "configured" is decided by presence only: a
  `stat` of the key-file paths and a name test on the provider variables.

"Configured" means a credential source exists, not that it loads. A source that
exists but fails is an error, never a quiet downgrade to sanitizer-only.

The Tavily and Context7 key sources are checked the same presence-only way.
Output names states, reason codes, and `~`-relative paths. It never carries a
key value or raw child output.
"""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

TOOL_NAME = "research-broker-preflight"
CONTRACT_VERSION = 1

# Binary location, identical to the typesafe-jev launcher.
BINARY_VARIABLE = "EVALUATE_BIN"
BINARY_NAME = "evaluate"
DEFAULT_BINARY_PARTS = (".local", "libexec", "racecraft-jev", "evaluate")
# The first typesafe-jev release that ships `evaluate call`.
MINIMUM_EVALUATE_VERSION = (0, 9, 0)

# Jev credential sources, primary then fallback: (provider, key variable, key-file variable).
JEV_KEY_DIRECTORY_PARTS = (".config", "racecraft-jev")
JEV_CREDENTIALS = (
    ("typesafe", "TYPESAFE_API_KEY", "JEV_API_KEY_FILE"),
    ("openrouter", "OPENROUTER_API_KEY", "JEV_FALLBACK_API_KEY_FILE"),
)
# Backend settings the broker pins so the user's shell cannot re-route it.
JEV_PLUGIN_SETTINGS = {
    "JEV_PROVIDER": "typesafe",
    "JEV_FALLBACK_PROVIDER": "openrouter",
    "JEV_REQUEST_TIMEOUT": "45s",
}
# The Jev model family the screening thresholds were calibrated on. The broker
# does not force a model id, because a retired id would fail every call; it
# records the answering model and marks any other family as unpinned.
JEV_CALIBRATED_MODEL = "jev-1.13"

# Variables a Jev child process may receive. Everything else is dropped.
CHILD_ENVIRONMENT_NAMES = frozenset(
    {
        "HOME",
        "PATH",
        "TMPDIR",
        "SYSTEMROOT",
        *JEV_PLUGIN_SETTINGS,
        *(name for _, name, _ in JEV_CREDENTIALS),
        *(name for _, _, name in JEV_CREDENTIALS),
    }
)

# Research credentials the broker reads itself (OD-13): a private key file, or
# the environment variable as an alternative.
SEARCH_KEY_DIRECTORY_PARTS = (".config", "speckit-pro")
SEARCH_CREDENTIALS = {
    "tavily": ("tavily.key", "TAVILY_API_KEY"),
    "context7": ("context7.key", "CONTEXT7_API_KEY"),
}
MAX_KEY_FILE_BYTES = 8 * 1024

# Neither probe touches the network. Short caps keep the broker's first tool
# call inside the host's MCP tool timeout even when the binary hangs.
VERSION_TIMEOUT_SECONDS = 5.0
CHECK_TIMEOUT_SECONDS = 10.0
VERSION_PATTERN = re.compile(r"\bv?(\d+)\.(\d+)\.(\d+)\b")

SEVERITY_ORDER = {"ok": 0, "warning": 1, "error": 2}


@dataclass(frozen=True)
class ProcessResult:
    """Exit code and stdout of one child run. `exit_code` is None on timeout or launch failure."""

    exit_code: int | None
    stdout: bytes


Runner = Callable[[list[str], dict[str, str], "bytes | None", float], ProcessResult]


def run_process(argv: list[str], env: dict[str, str], stdin: bytes | None, timeout: float) -> ProcessResult:
    """Run one `evaluate` child without a shell. Its stderr is discarded, never forwarded.

    The executable is re-resolved by its fixed name inside the resolved
    directory, so the command can only ever be the `evaluate` binary.
    """
    candidate = Path(argv[0])
    # A literal name, so the command is statically the `evaluate` binary.
    executable = shutil.which("evaluate", path=str(candidate.parent))
    if executable is None or Path(executable) != candidate:
        return ProcessResult(None, b"")
    try:
        completed = subprocess.run(
            [executable, *argv[1:]],
            input=stdin,
            stdin=None if stdin is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=env,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ProcessResult(None, b"")
    return ProcessResult(completed.returncode, completed.stdout)


def _value(env: Mapping[str, str], name: str) -> str:
    """An empty variable counts as unset."""
    return env.get(name) or ""


def home_directory(env: Mapping[str, str]) -> Path:
    home = _value(env, "HOME") or _value(env, "USERPROFILE")
    return Path(home) if home else Path.home()


def display_path(path: Path, home: Path) -> str:
    """A path for output: `~`-relative inside HOME, the bare file name elsewhere."""
    try:
        return "~/" + path.relative_to(home).as_posix()
    except ValueError:
        return path.name


def resolve_binary(env: Mapping[str, str], home: Path) -> Path | None:
    explicit = _value(env, BINARY_VARIABLE)
    candidate = Path(explicit) if explicit else home.joinpath(*DEFAULT_BINARY_PARTS)
    # The child is always run by its fixed name, so an override must name a
    # file called `evaluate`.
    if candidate.name != BINARY_NAME:
        return None
    try:
        info = candidate.stat()
    except OSError:
        return None
    if not stat.S_ISREG(info.st_mode) or not os.access(candidate, os.X_OK):
        return None
    return candidate


def jev_child_environment(env: Mapping[str, str], home: Path) -> dict[str, str]:
    """The allowlisted environment for an `evaluate` child.

    The provider key variables are copied through only when already set, so the
    Go binary, not this process, decides whether they hold a usable key.
    """
    child: dict[str, str] = {"HOME": str(home), "PATH": _value(env, "PATH") or os.defpath}
    for name in ("TMPDIR", "SYSTEMROOT", *(n for _, _, n in JEV_CREDENTIALS), *(n for _, n, _ in JEV_CREDENTIALS)):
        if _value(env, name):
            child[name] = env[name]
    child.update(JEV_PLUGIN_SETTINGS)
    return child


def jev_credential_sources(env: Mapping[str, str], home: Path) -> dict[str, bool]:
    """Presence only: which Jev credential sources exist. No file is opened."""
    key_directory = home.joinpath(*JEV_KEY_DIRECTORY_PARTS)
    explicit_file = any(_value(env, file_variable) for _, _, file_variable in JEV_CREDENTIALS)
    default_file = any(os.path.lexists(key_directory / f"{provider}.key") for provider, _, _ in JEV_CREDENTIALS)
    environment = any(_value(env, key_variable) for _, key_variable, _ in JEV_CREDENTIALS)
    return {"explicit_file": explicit_file, "default_file": default_file, "environment": environment}


def parse_version(stdout: bytes) -> tuple[int, int, int] | None:
    match = VERSION_PATTERN.search(stdout.decode("utf-8", "replace"))
    if match is None:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _format_version(version: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in version)


def _item(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


INSTALL_HINT = "Install or update the typesafe-jev plugin, then run its binary installer."
KEY_HINT = "Put a key in ~/.config/racecraft-jev/typesafe.key (mode 0600) to enable Jev screening."


def probe_jev(env: Mapping[str, str], home: Path, runner: Runner = run_process) -> dict[str, Any]:
    """Classify the Jev screening state. Returns the `jev` section of the preflight record."""
    sources = jev_credential_sources(env, home)
    configured = any(sources.values())
    file_source = sources["explicit_file"] or sources["default_file"]
    credential_source = "key_file" if file_source else ("environment" if sources["environment"] else "none")
    section: dict[str, Any] = {
        "binary": "missing",
        "binary_version": None,
        "minimum_version": _format_version(MINIMUM_EVALUATE_VERSION),
        "credential_source": credential_source,
        "check_exit_code": None,
    }

    def finish(state: str, severity: str, code: str, message: str) -> dict[str, Any]:
        usable = state == "ready"
        section.update(
            {
                "state": state,
                "severity": severity,
                "usable": usable,
                # A configured-but-broken source keeps `jev` mode: every chunk is
                # dropped and reported rather than silently sanitizer-screened.
                "screening_mode": "jev" if usable or severity == "error" else "sanitizer-only",
                "finding": _item(code, message) if code else None,
            }
        )
        return section

    binary = resolve_binary(env, home)
    if binary is None:
        if configured:
            return finish(
                "binary_missing_with_credential", "error", "jev_binary_missing_with_credential",
                f"A Jev credential is configured but the evaluate binary is missing. {INSTALL_HINT}",
            )
        return finish(
            "binary_missing", "warning", "jev_binary_missing",
            f"The evaluate binary is missing, so research runs sanitizer-only. {INSTALL_HINT}",
        )
    section["binary"] = "present"
    child_env = jev_child_environment(env, home)

    version_result = runner([str(binary), "version"], child_env, None, VERSION_TIMEOUT_SECONDS)
    version = parse_version(version_result.stdout) if version_result.exit_code == 0 else None
    if version is None:
        severity = "error" if configured else "warning"
        return finish(
            "binary_unusable", severity, "jev_binary_unusable",
            f"The evaluate binary did not report a version. {INSTALL_HINT}",
        )
    section["binary_version"] = _format_version(version)
    if version < MINIMUM_EVALUATE_VERSION:
        minimum = _format_version(MINIMUM_EVALUATE_VERSION)
        if configured:
            return finish(
                "binary_outdated", "error", "jev_binary_outdated",
                f"The evaluate binary is older than {minimum} and has no call command. {INSTALL_HINT}",
            )
        return finish(
            "binary_outdated", "warning", "jev_binary_outdated",
            f"The evaluate binary is older than {minimum}; research runs sanitizer-only. {INSTALL_HINT}",
        )

    check = runner([str(binary), "call", "--check", "--plugin-defaults"], child_env, None, CHECK_TIMEOUT_SECONDS)
    section["check_exit_code"] = check.exit_code
    if check.exit_code == 0:
        if credential_source == "environment":
            return finish(
                "ready", "warning", "jev_environment_only_credential",
                "The Jev key is set only as an environment variable. The broker runs as an MCP server and may "
                "not see it, which would run research sanitizer-only. Use a key file instead.",
            )
        return finish("ready", "ok", "", "")
    if check.exit_code == 3:
        return finish(
            "no_credential", "warning", "jev_no_credential",
            f"No Jev credential is configured, so research runs sanitizer-only. {KEY_HINT}",
        )
    if check.exit_code == 4:
        return finish(
            "credential_unusable", "error", "jev_credential_unusable",
            "A Jev credential is configured but unusable (check the key file mode, size, and content). "
            "Research drops every chunk until it is fixed.",
        )
    return finish(
        "check_failed", "error", "jev_check_failed",
        "The Jev credential check failed. Research drops every chunk until it passes.",
    )


def key_file_problem(path: Path) -> str | None:
    """Presence-only validation of a private key file. Returns a reason code, or None when usable.

    The rules match the broker's own load: the path itself must be a regular
    file (a symlink is refused, as the broker opens with O_NOFOLLOW), readable
    by this user, with no group or other bits, and 1 byte to 8 KiB.
    """
    try:
        info = path.lstat()
    except OSError:
        return "key_file_unreadable"
    if not stat.S_ISREG(info.st_mode):
        return "key_file_not_regular"
    if not os.access(path, os.R_OK):
        return "key_file_unreadable"
    if os.name == "posix" and stat.S_IMODE(info.st_mode) & 0o077:
        return "key_file_permissions"
    if info.st_size == 0:
        return "key_file_empty"
    if info.st_size > MAX_KEY_FILE_BYTES:
        return "key_file_too_large"
    return None


def search_key_source(name: str, env: Mapping[str, str], home: Path) -> dict[str, Any]:
    """Where a research key comes from. A present key file always wins over the variable."""
    file_name, variable = SEARCH_CREDENTIALS[name]
    path = home.joinpath(*SEARCH_KEY_DIRECTORY_PARTS, file_name)
    if os.path.lexists(path):
        problem = key_file_problem(path)
        return {
            "state": "unusable" if problem else "configured",
            "source": "key_file",
            "reason": problem,
            "path": display_path(path, home),
            "path_obj": path,
            "variable": variable,
        }
    if _value(env, variable):
        return {"state": "configured", "source": "environment", "reason": None, "path": None, "path_obj": None, "variable": variable}
    return {"state": "missing", "source": "none", "reason": None, "path": None, "path_obj": None, "variable": variable}


def _public(section: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in section.items() if key != "path_obj"}


def research_broker_preflight(env: Mapping[str, str] | None = None, runner: Runner = run_process) -> dict[str, Any]:
    """Build the full preflight record: Jev screening, Tavily search, Context7 docs."""
    env = os.environ if env is None else env
    home = home_directory(env)
    warnings: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []

    def record(severity: str, item: dict[str, str] | None) -> None:
        if item is None:
            return
        (errors if severity == "error" else warnings).append(item)

    jev = probe_jev(env, home, runner)
    record(jev["severity"], jev.pop("finding"))

    search = search_key_source("tavily", env, home)
    search["provider"] = "tavily"
    if search["state"] == "missing":
        search["severity"] = "warning"
        record("warning", _item(
            "search_unavailable",
            "No Tavily key is configured, so research_search returns search_unavailable. Put a free key in "
            "~/.config/speckit-pro/tavily.key (mode 0600) or set TAVILY_API_KEY.",
        ))
    elif search["state"] == "unusable":
        search["severity"] = "error"
        record("error", _item("search_credential_unusable", f"The Tavily key file is unusable ({search['reason']})."))
    elif search["source"] == "environment":
        search["severity"] = "warning"
        record("warning", _item(
            "search_environment_only_credential",
            "The Tavily key is set only as an environment variable, which an MCP server may not see. Use a key file.",
        ))
    else:
        search["severity"] = "ok"

    docs = search_key_source("context7", env, home)
    docs["provider"] = "context7"
    if docs["state"] == "missing":
        # Context7 is optional: without a key, docs_query uses the keyless tier.
        docs["state"] = "keyless"
        docs["severity"] = "ok"
    elif docs["state"] == "unusable":
        docs["severity"] = "error"
        record("error", _item("docs_credential_unusable", f"The Context7 key file is unusable ({docs['reason']})."))
    elif docs["source"] == "environment":
        docs["severity"] = "warning"
        record("warning", _item(
            "docs_environment_only_credential",
            "The Context7 key is set only as an environment variable, which an MCP server may not see. Use a key file.",
        ))
    else:
        docs["severity"] = "ok"

    severity = max((jev["severity"], search["severity"], docs["severity"]), key=SEVERITY_ORDER.__getitem__)
    return {
        "tool": TOOL_NAME,
        "contract_version": CONTRACT_VERSION,
        "severity": severity,
        "screening_mode": jev["screening_mode"],
        "jev": jev,
        "search": _public(search),
        "docs": _public(docs),
        "warnings": warnings,
        "errors": errors,
    }


def run_research_broker_preflight_helper(entry: Any, request: Any) -> dict[str, Any]:
    """Runner helper entry point: read-only, no inputs, value-free."""
    from .envelope import diagnostic, response

    if request.inputs:
        return response(
            "input_error",
            request_id=request.request_id,
            diagnostics=[
                diagnostic(
                    "invalid_input",
                    "research-broker-preflight takes no inputs",
                    details={"unexpected_inputs": sorted(request.inputs)},
                    remediation_summary="Send an empty inputs object.",
                    remediation_actions=["Remove every field from inputs.", "Retry the request."],
                )
            ],
        )
    data = research_broker_preflight()
    data["helper_id"] = entry.helper_id
    data["writes_state"] = False
    if data["severity"] != "error":
        return response("ok", request_id=request.request_id, data=data)
    diagnostics = [
        diagnostic(
            item["code"],
            item["message"],
            remediation_summary="Fix the configured research credential or binary, then rerun the preflight.",
            remediation_actions=[
                "Read the error message for the failing source.",
                "Rerun research-broker-preflight after the fix.",
            ],
        )
        for item in data["errors"]
    ]
    return response("expected_failure", request_id=request.request_id, data=data, diagnostics=diagnostics)
