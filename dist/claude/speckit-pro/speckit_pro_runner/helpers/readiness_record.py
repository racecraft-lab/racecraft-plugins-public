"""Scaffold's readiness record (ADR 0008): one local, git-ignored snapshot per host and worktree.

Scaffold observes the shared preparation items and hands each observation to
this helper, which stamps it, fingerprints the inputs it names, and writes
`.specify/readiness/<host>.json` owner-only. The runner observes three items
itself: local capability health, the quality-gates source and the verification-Docker fit. Missing
evidence is recorded `unknown`; an `unavailable` or `unknown` item must name
the action the user takes, so scaffold finishes after a declined or failed
fix. The record has no overall verdict, stores no credential, and holds no
absolute local path: text that looks like either is refused, and inputs are
kept only as digests.
"""

from __future__ import annotations

import os
import re
import shutil
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from .. import cli_probe, quality_gates
from ..agent_materialization import digest
from ..envelope import diagnostic, response
from ..atomic_write import write_bytes_atomic
from ..canonical_json import canonical_bytes
from ..private_state import ensure_private_directory
from ..strict_input import SelectionError
from ..trusted_io import find_repo_root, trusted_bytes
from ..verification_docker import DAEMON_ARCHITECTURES, PLATFORM, PLATFORM_OS
from . import readiness_host_items as host_items
from .readiness_values import NOT_OBSERVED_ACTION, clean_text, make_item

SCHEMA_VERSION = "readiness-record/v1"
HOSTS = ("claude", "codex")
STATUSES = ("verified", "unavailable", "unknown", "not_applicable")
NEEDS_ACTION = ("unavailable", "unknown")
# Items scaffold observes and passes in. The runner observes the rest.
CALLER_ITEMS = ("plugin_payload", "project_integration", "github_auth", "mcp_servers", "typesafe_jev",
                "reviewability_report", "formal_methods")
RUNNER_ITEMS = ("local_capability", "quality_gates", "verification_docker")
RECORD_DIRECTORY = ".specify/readiness"
INPUT_KEYS = frozenset({"host", "host_version", "execution_mode", "plugin_revision", "observations"})
OBSERVATION_KEYS = frozenset({"item", "status", "evidence_source", "action", "files", "values"})
VALUE_NAME_RE = re.compile(r"[a-z][a-z0-9_]{0,40}")
EXECUTION_MODES = ("interactive", "answers-file")
DOCKER_PROBE_SECONDS = 10


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fingerprint_files(paths: Any, root: Path, label: str) -> dict[str, str]:
    if not isinstance(paths, list):
        raise SelectionError(f"{label}.files must be a list of repository-relative paths")
    prints: dict[str, str] = {}
    for raw in paths:
        text = clean_text(raw, f"{label}.files entry")
        relative = PurePosixPath(text)
        if relative.is_absolute() or ".." in relative.parts or "\\" in text:
            raise SelectionError(f"{label}.files entry {text!r} must stay inside the repository")
        prints[f"file:{relative.as_posix()}"] = fingerprint_file(root, relative)
    return prints


def fingerprint_file(root: Path, relative: PurePosixPath) -> str:
    """A digest, `missing` for an absent file, or `unreadable` for one the runner cannot read safely."""
    content = trusted_bytes(root / relative, root)
    if content is not None:
        return digest(content)
    return "unreadable" if os.path.lexists(root / relative) else "missing"


def fingerprint_values(values: Any, label: str) -> dict[str, str]:
    if not isinstance(values, dict):
        raise SelectionError(f"{label}.values must map names to text")
    prints: dict[str, str] = {}
    for name, value in values.items():
        if not isinstance(name, str) or not VALUE_NAME_RE.fullmatch(name) or not isinstance(value, str):
            raise SelectionError(f"{label}.values needs lowercase names and text values")
        clean_text(name, f"{label}.values name")
        prints[f"value:{name}"] = digest(value)
    return prints


def caller_item(raw: Any, root: Path, observed_at: str) -> tuple[str, dict[str, Any]]:
    if not isinstance(raw, dict) or not raw.keys() <= OBSERVATION_KEYS:
        raise SelectionError(f"each observation takes only {sorted(OBSERVATION_KEYS)}")
    name = raw.get("item")
    if name not in CALLER_ITEMS:
        raise SelectionError(f"item must be one of {list(CALLER_ITEMS)}; the runner observes {list(RUNNER_ITEMS)}")
    status = raw.get("status")
    if status not in STATUSES:
        raise SelectionError(f"{name}: status must be one of {list(STATUSES)}")
    action = None
    if status in NEEDS_ACTION:
        if "action" not in raw:
            raise SelectionError(f"{name}: a {status} item must name the action the user takes")
        action = clean_text(raw["action"], f"{name}.action")
    fingerprints = {**fingerprint_files(raw.get("files", []), root, name),
                    **fingerprint_values(raw.get("values", {}), name)}
    if status == "verified" and not any(value.startswith("sha256:") for value in fingerprints.values()):
        raise SelectionError(f"{name}: verified evidence needs an input fingerprint")
    if name == "reviewability_report" and status == "verified" and (
            "value:spec_id" not in fingerprints or not any(key.startswith("file:") and value.startswith("sha256:")
                                                          for key, value in fingerprints.items())):
        raise SelectionError("reviewability_report: verified evidence needs a report or roadmap file and spec_id")
    return name, make_item(status, clean_text(raw.get("evidence_source"), f"{name}.evidence_source"),
                           observed_at, fingerprints, action)


def probe_temporary_directory(directory: Path) -> str | None:
    """The first problem with `directory` as scratch space for sensitive files, or None."""
    descriptor, name = tempfile.mkstemp(prefix="speckit-readiness-", dir=directory)
    try:
        os.write(descriptor, b"probe")
        mode = stat.S_IMODE(os.fstat(descriptor).st_mode)
    finally:
        os.close(descriptor)
        os.unlink(name)
    if os.name == "nt":
        return None  # POSIX modes are not observable here, so only the write is proven.
    if mode & 0o077:
        return f"a temporary file is readable beyond its owner (mode {mode:03o})"
    directory_mode = stat.S_IMODE(directory.stat().st_mode)
    if directory_mode & 0o002 and not directory_mode & stat.S_ISVTX:
        return "the temporary directory is world-writable without the sticky bit"
    return None


def observe_local_capability() -> dict[str, Any]:
    """Probe temporary storage with one write, a mode read and a directory check."""
    observed_at = now()
    try:
        directory = Path(tempfile.gettempdir())
        problem = probe_temporary_directory(directory)
    except OSError as error:
        return make_item("unavailable", f"temporary storage probe failed: {type(error).__name__}", observed_at, {},
                         "Make the temporary directory writable by this user, then rerun scaffold.")
    fingerprints = {"value:temp_dir": digest(str(directory))}
    if problem is not None:
        return make_item("unavailable", problem, observed_at, fingerprints,
                         "Fix the temporary directory so sensitive files stay owner-only.")
    if os.name == "nt":
        return make_item("unknown", "temporary write passed; owner-only modes are unobservable", observed_at, fingerprints,
                         "Verify the record and sensitive temporary files have owner-only access, then rerun scaffold.")
    return make_item("verified", "temporary file write and owner-only mode probe", observed_at, fingerprints)


def observe_quality_gates(root: Path) -> dict[str, Any]:
    """The confirmed file and its digest, or the shipped defaults with the reason they apply."""
    observed_at = now()
    content = trusted_bytes(root / quality_gates.FILE_PATH, root)
    status, problems, _ = quality_gates.observe(None if content is None else content.decode("utf-8", "replace"))
    key = f"file:{quality_gates.FILE_PATH}"
    if status == "present":
        return make_item("verified", "confirmed quality-gates file", observed_at, {key: digest(content or b"")})
    fingerprints = {key: fingerprint_file(root, PurePosixPath(quality_gates.FILE_PATH))}
    if status == "invalid":
        reason = problems[0]
    else:
        reason = f"{quality_gates.FILE_PATH} is {fingerprints[key]}"
    try:
        reason = clean_text(reason, "reason")
    except SelectionError:
        reason = "the first validation problem was withheld because it held a path or a credential"
    return make_item("unavailable", f"shipped defaults in use: {reason}", observed_at, fingerprints,
                     "Confirm a quality-gates proposal when scaffold offers one, or run the speckit-coach "
                     "quality gates flow.")


def observe_verification_docker(root: Path) -> dict[str, Any]:
    """Ask a present Docker CLI two read-only questions: is its endpoint local, and is the daemon Linux/arm64?

    Verification Docker runs only against a local Unix socket (ADR 0005), so a remote
    context or host never counts as a fit. Nothing is installed or started, and the
    daemon's own words are never recorded.
    """
    observed_at = now()
    no_fit_action = f"Verification Docker needs a local {PLATFORM} Docker daemon; this host has none."

    def unavailable(evidence: str, action: str = no_fit_action) -> dict[str, Any]:
        return make_item("unavailable", evidence, observed_at, {}, action)

    if shutil.which("docker") is None:
        return unavailable("the Docker CLI is not installed")
    # Reject a remote override before any CLI call can contact its daemon.
    host = os.environ.get("DOCKER_HOST")
    if host and not host.startswith("unix://"):
        return unavailable("the Docker daemon is not reached over a local socket")
    endpoint = cli_probe.probe(root, ["docker", "context", "inspect", "--format", "{{.Endpoints.docker.Host}}"],
                               allowed=("docker",), timeout=DOCKER_PROBE_SECONDS)
    if endpoint["exit_status"] != 0:
        return unavailable("no Docker daemon answered", "Start the Docker daemon, then rerun scaffold.")
    if not endpoint["stdout_tail"].startswith("unix://"):
        return unavailable("the Docker daemon is not reached over a local socket")
    platform = cli_probe.probe(root, ["docker", "info", "--format", "{{.OSType}}/{{.Architecture}}"],
                               allowed=("docker",), timeout=DOCKER_PROBE_SECONDS)
    if platform["exit_status"] != 0:
        return unavailable("no Docker daemon answered", "Start the Docker daemon, then rerun scaffold.")
    os_type, _, architecture = platform["stdout_tail"].partition("/")
    if os_type == PLATFORM_OS and architecture in DAEMON_ARCHITECTURES:
        return make_item("verified", f"a local {PLATFORM} Docker daemon answered", observed_at, {})
    return unavailable(f"the Docker daemon does not report {PLATFORM}")


def build_record(inputs: dict[str, Any], root: Path) -> dict[str, Any]:
    if not isinstance(inputs, dict) or not {"host", "execution_mode", "plugin_revision", "observations"} <= inputs.keys() \
            or not inputs.keys() <= INPUT_KEYS:
        raise SelectionError(f"inputs take {sorted(INPUT_KEYS)}; host_version may be omitted when unobservable")
    if inputs["host"] not in HOSTS:
        raise SelectionError(f"host must be one of {list(HOSTS)}")
    if inputs["execution_mode"] not in EXECUTION_MODES:
        raise SelectionError(f"execution_mode must be one of {list(EXECUTION_MODES)}")
    observations = inputs["observations"]
    if not isinstance(observations, list):
        raise SelectionError("observations must be a list")
    plugin_revision = clean_text(inputs["plugin_revision"], "plugin_revision")
    observed_at = now()
    items: dict[str, dict[str, Any]] = {}
    for raw in observations:
        if isinstance(raw, dict) and raw.get("item") in host_items.HOST_ITEMS:
            name, item = host_items.host_item(raw, inputs["host"], observed_at, plugin_revision)
        else:
            name, item = caller_item(raw, root, observed_at)
        if name in items:
            raise SelectionError(f"{name} is observed twice")
        items[name] = item
    host_items.fill_missing(items, inputs["host"], observed_at)
    for name in CALLER_ITEMS:
        items.setdefault(name, make_item("unknown", "not observed by scaffold", observed_at, {}, NOT_OBSERVED_ACTION))
    items["local_capability"] = observe_local_capability()
    if inputs["host"] == "codex":
        host_items.reconcile_codex_items(items, observed_at, host_items.names_item(observations, "hooks"))
    items["quality_gates"] = observe_quality_gates(root)
    items["verification_docker"] = observe_verification_docker(root)
    host_version = inputs.get("host_version")
    return {
        "schema_version": SCHEMA_VERSION,
        "binding": {"worktree": digest(str(root))},
        "host": inputs["host"],
        "host_version": None if host_version is None else clean_text(host_version, "host_version"),
        "execution_mode": inputs["execution_mode"],
        "plugin_revision": plugin_revision,
        "observed_at": observed_at,
        "items": {name: items[name] for name in sorted(items)},
    }


def write_record(root: Path, record: dict[str, Any]) -> str:
    specify = root / ".specify"
    # ensure_private_directory would create the directory through a symlinked parent, so check it first.
    if specify.is_symlink() or not specify.is_dir():
        raise SelectionError("unsafe .specify directory: it must be a real directory")
    directory = root / RECORD_DIRECTORY
    ensure_private_directory(directory, label="unsafe readiness directory", violation=SelectionError)
    # Both writes walk the path without following links, refuse a linked target, and replace atomically.
    # A self-ignoring directory keeps the record out of version control in every worktree.
    write_bytes_atomic(directory / ".gitignore", b"*\n", trust_root=root, mode=0o600)
    write_bytes_atomic(directory / f"{record['host']}.json", canonical_bytes(record) + b"\n",
                       trust_root=root, mode=0o600)
    return f"{RECORD_DIRECTORY}/{record['host']}.json"


def run_readiness_record_helper(entry: Any, request: Any) -> dict[str, Any]:
    root = find_repo_root(Path.cwd())
    if root is None or not (root / ".specify").is_dir():
        return response("missing_prerequisite", request_id=request.request_id, diagnostics=[diagnostic(
            "missing_prerequisite", "the readiness record needs a SpecKit project with a .specify directory",
            remediation_summary="Initialize SpecKit in this project, then rerun scaffold.",
            remediation_actions=["Run the SpecKit install flow.", "Rerun scaffold."])])
    try:
        record = build_record(request.inputs, root)
    except SelectionError as error:
        return response("input_error", request_id=request.request_id, diagnostics=[diagnostic(
            "invalid_input", str(error), remediation_summary="Send observations the record can hold.",
            remediation_actions=["Correct the named field.", "Retry the request."])])
    data: dict[str, Any] = {"helper_id": entry.helper_id, "operation": entry.operation, "mode": request.mode,
                            "writes_state": False, "record": record,
                            "allow_rules": host_items.allow_rules(request.inputs)}
    if request.mode == "apply":
        try:
            data["record_path"] = write_record(root, record)
        except (OSError, SelectionError) as error:
            return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diagnostic(
                "write_failure", f"the readiness record could not be written: {getattr(error, 'strerror', None) or error}",
                remediation_summary="Scaffold continues; autopilot treats a missing record as no evidence.",
                remediation_actions=["Report the failure in the scaffold closing report.",
                                     "Fix the .specify directory permissions and rerun scaffold."])])
        data["writes_state"] = True
    return response("ok", request_id=request.request_id, data=data)
