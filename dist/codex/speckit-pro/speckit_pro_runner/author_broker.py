"""Capability-bound author and preview broker for untrusted formal-input agents."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import stat
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
import sys

from .artifact_review import OBSERVATION_CLOCK_SKEW
from .helpers.mutation import validate_target_path, write_file_atomic
from .helpers.read_only import repo_relative, resolve_input_path

SERVER_INFO = {"name": "speckit-pro-author-broker", "version": "1.0.0"}
SESSION_VERSION = 1
DEFAULT_TTL_SECONDS = 15 * 60
MAX_PERMITTED_PATHS = 64
MAX_CONTENT_BYTES = 1024 * 1024
SESSION_ID_RE = re.compile(r"^[0-9a-f]{32}$")
CAPABILITY_RE = re.compile(r"^author-cap:v1:([0-9a-f]{32}):([0-9a-f]{64})$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
PREVIEW_VERDICTS = ("verified", "denied", "unavailable")
BROKER_ERROR_CODES = (
    "schema_validation",
    "path_violation",
    "receipt_violation",
    "content_too_large",
    "preview_mismatch",
    "unsupported_kind",
)


class BrokerViolation(ValueError):
    """A broker request violated its closed trust boundary."""


STATE_ROOT_VARIABLE = "SPECKIT_AUTHOR_BROKER_STATE_ROOT"


def _state_root() -> Path:
    """Resolve the private session root, honouring an explicit launcher override.

    A capability is minted in one process and redeemed in another. When an
    isolated launcher starts the redeeming broker it cannot rely on the child
    inheriting the same TMPDIR, so it names the root outright. The value is
    still validated by _ensure_private_root, which refuses a symlink, a
    non-directory, or a root this user does not own.
    """
    override = os.environ.get(STATE_ROOT_VARIABLE)
    if override:
        return Path(override)
    uid = getattr(os, "getuid", lambda: 0)()
    return Path(tempfile.gettempdir()) / f"speckit-pro-author-broker-{uid}"


def _ensure_private_root(root: Path) -> None:
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = root.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise BrokerViolation("private author broker root is unsafe")
    uid = getattr(os, "getuid", lambda: info.st_uid)()
    if info.st_uid != uid:
        raise BrokerViolation("private author broker root has the wrong owner")
    if stat.S_IMODE(info.st_mode) & 0o077:
        os.chmod(root, 0o700)


def _write_state(path: Path, state: dict[str, Any]) -> None:
    encoded = (json.dumps(state, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            fd = -1
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if fd >= 0:
            os.close(fd)
        try:
            temporary.unlink()
        except FileNotFoundError:
            # Atomic replacement may have already removed the temporary path.
            pass


def _safe_session_path(root: Path, session_id: str) -> Path:
    if SESSION_ID_RE.fullmatch(session_id) is None:
        raise BrokerViolation("session id is malformed")
    session_path = root / session_id
    try:
        info = session_path.lstat()
    except OSError as exc:
        raise BrokerViolation("author broker session is unavailable") from exc
    uid = getattr(os, "getuid", lambda: info.st_uid)()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode) or info.st_uid != uid:
        raise BrokerViolation("author broker session directory is unsafe")
    if stat.S_IMODE(info.st_mode) & 0o077:
        raise BrokerViolation("author broker session directory is unsafe")
    return session_path


def _read_state(root: Path, session_id: str) -> dict[str, Any]:
    if SESSION_ID_RE.fullmatch(session_id) is None:
        raise BrokerViolation("session id is malformed")
    session_path = _safe_session_path(root, session_id)
    path = session_path / "state.json"
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError as exc:
        raise BrokerViolation("author broker session is unavailable") from exc
    try:
        info = os.fstat(fd)
        uid = getattr(os, "getuid", lambda: info.st_uid)()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != uid or stat.S_IMODE(info.st_mode) & 0o077:
            raise BrokerViolation("author broker session state is unsafe")
        if info.st_size > 1024 * 1024:
            raise BrokerViolation("author broker session state is too large")
        with os.fdopen(fd, "rb") as handle:
            fd = -1
            state = json.loads(handle.read().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BrokerViolation("author broker session state is unreadable") from exc
    finally:
        if fd >= 0:
            os.close(fd)
    if not isinstance(state, dict) or state.get("session_id") != session_id or state.get("version") != SESSION_VERSION:
        raise BrokerViolation("author broker session state is invalid")
    if time.time() > float(state.get("expires_at", 0)):
        raise BrokerViolation("author broker session has expired")
    return state


def _canonical_paths(repo_root: Path, values: Any) -> tuple[str, ...]:
    if not isinstance(values, list) or not values or len(values) > MAX_PERMITTED_PATHS or len(set(values)) != len(values):
        raise BrokerViolation("permitted_paths must be a non-empty unique array")
    result: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value:
            raise BrokerViolation("permitted_paths entries must be non-empty text")
        diagnostic = validate_target_path(value, repo_root)
        if diagnostic is not None:
            raise BrokerViolation("permitted path escapes the repository or crosses a symlink")
        normalized = repo_relative(resolve_input_path(value, repo_root), repo_root)
        if any(part.casefold() == ".git" for part in PurePosixPath(normalized).parts):
            raise BrokerViolation("permitted paths cannot name git metadata")
        result.append(normalized)
    return tuple(result)


def _mint_capability(state: dict[str, Any]) -> str:
    binding = {
        "session_id": state["session_id"],
        "kind": state["kind"],
        "repo_root": state["repo_root"],
        "nonce": state["nonce"],
    }
    digest = hmac.new(
        bytes.fromhex(state["receipt_key"]),
        json.dumps(binding, sort_keys=True, separators=(",", ":")).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"author-cap:v1:{state['session_id']}:{digest}"


def _resolve_capability(capability: str) -> dict[str, Any]:
    match = CAPABILITY_RE.fullmatch(capability) if isinstance(capability, str) else None
    if match is None:
        raise BrokerViolation("author broker capability is malformed")
    state = _read_state(_state_root(), match.group(1))
    expected = _mint_capability(state)
    if not hmac.compare_digest(expected, capability):
        raise BrokerViolation("author broker capability is invalid")
    return state


def _hash_file(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def create_formal_session(
    *, repo_root: str, workflow_file: str, model_id: str, permitted_paths: list[str], ttl_seconds: int = DEFAULT_TTL_SECONDS
) -> dict[str, Any]:
    if not isinstance(repo_root, str) or not repo_root:
        raise BrokerViolation("repo_root is required")
    if not isinstance(workflow_file, str) or not workflow_file or not isinstance(model_id, str) or not model_id:
        raise BrokerViolation("workflow_file and model_id are required")
    root = Path(repo_root).resolve(strict=True)
    if not root.is_dir():
        raise BrokerViolation("repo_root must be a directory")
    canonical = _canonical_paths(root, permitted_paths)
    state_root = _state_root()
    _ensure_private_root(state_root)
    session_id = secrets.token_hex(16)
    session_path = state_root / session_id
    session_path.mkdir(mode=0o700)
    _safe_session_path(state_root, session_id)
    state = {
        "version": SESSION_VERSION,
        "session_id": session_id,
        "kind": "formal",
        "repo_root": str(root),
        "workflow_file": workflow_file,
        "model_id": model_id,
        "permitted_paths": list(canonical),
        "nonce": secrets.token_hex(16),
        "receipt_key": secrets.token_hex(32),
        "created_at": time.time(),
        "expires_at": time.time() + ttl_seconds,
    }
    _write_state(session_path / "state.json", state)
    return {"session_id": session_id, "capability": _mint_capability(state), "permitted_paths": list(canonical)}


def create_preview_session(
    *, repo_root: str, artifact_path: str, expected_sha256: str, ttl_seconds: int = DEFAULT_TTL_SECONDS
) -> dict[str, Any]:
    if not isinstance(repo_root, str) or not repo_root:
        raise BrokerViolation("repo_root is required")
    if not isinstance(artifact_path, str) or not artifact_path or not SHA256_RE.fullmatch(expected_sha256):
        raise BrokerViolation("artifact_path and expected_sha256 are required")
    root = Path(repo_root).resolve(strict=True)
    if not root.is_dir():
        raise BrokerViolation("repo_root must be a directory")
    diagnostic = validate_target_path(artifact_path, root)
    if diagnostic is not None:
        raise BrokerViolation("artifact path escapes the repository or crosses a symlink")
    normalized = repo_relative(resolve_input_path(artifact_path, root), root)
    artifact = root / normalized
    if not artifact.is_file():
        raise BrokerViolation("artifact path is not a regular file")
    if _hash_file(artifact) != expected_sha256:
        raise BrokerViolation("artifact bytes do not match expected_sha256")
    state_root = _state_root()
    _ensure_private_root(state_root)
    session_id = secrets.token_hex(16)
    session_path = state_root / session_id
    session_path.mkdir(mode=0o700)
    _safe_session_path(state_root, session_id)
    state = {
        "version": SESSION_VERSION,
        "session_id": session_id,
        "kind": "preview",
        "repo_root": str(root),
        "artifact_path": normalized,
        "expected_sha256": expected_sha256,
        "nonce": secrets.token_hex(16),
        "receipt_key": secrets.token_hex(32),
        "created_at": time.time(),
        "expires_at": time.time() + ttl_seconds,
    }
    _write_state(session_path / "state.json", state)
    return {"session_id": session_id, "capability": _mint_capability(state), "artifact_sha256": expected_sha256}


def write_formal_file(*, capability: str, target: str, content: str) -> dict[str, Any]:
    state = _resolve_capability(capability)
    if state.get("kind") != "formal":
        raise BrokerViolation("formal write capability is required")
    if not isinstance(target, str) or not target:
        raise BrokerViolation("target is required")
    if not isinstance(content, str):
        raise BrokerViolation("content must be text")
    if len(content.encode("utf-8")) > MAX_CONTENT_BYTES:
        raise BrokerViolation("formal content exceeds the broker limit")
    root = Path(state["repo_root"])
    diagnostic = validate_target_path(target, root)
    if diagnostic is not None:
        raise BrokerViolation("target escapes the repository or crosses a symlink")
    normalized = repo_relative(resolve_input_path(target, root), root)
    if normalized not in state["permitted_paths"]:
        raise BrokerViolation("target is outside the permitted output list")
    write_result = write_file_atomic(root / normalized, content, trust_root=root)
    return {"target": normalized, "sha256": write_result["digest"]}


def submit_preview_verdict(*, capability: str, verdict: str) -> dict[str, Any]:
    state = _resolve_capability(capability)
    if state.get("kind") != "preview":
        raise BrokerViolation("preview capability is required")
    if verdict not in PREVIEW_VERDICTS:
        raise BrokerViolation("preview verdict is outside the closed vocabulary")
    root = Path(state["repo_root"])
    artifact = root / state["artifact_path"]
    if validate_target_path(state["artifact_path"], root) is not None:
        raise BrokerViolation("preview artifact changed after session creation")
    try:
        digest = _hash_file(artifact)
    except OSError as exc:
        raise BrokerViolation("preview artifact changed after session creation") from exc
    if digest != state["expected_sha256"]:
        raise BrokerViolation("preview artifact changed after session creation")
    session_path = _safe_session_path(_state_root(), state["session_id"])
    claim = session_path / "preview-submitted"
    try:
        fd = os.open(claim, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    except FileExistsError as exc:
        raise BrokerViolation("preview verdict was already submitted") from exc
    except OSError as exc:
        raise BrokerViolation("preview verdict could not be recorded") from exc
    os.close(fd)
    state["preview_submission"] = {
        "verdict": verdict,
        "artifact_sha256": digest,
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        _write_state(session_path / "state.json", state)
    except OSError as exc:
        raise BrokerViolation("preview verdict could not be recorded") from exc
    return {"verdict": verdict, "artifact_sha256": digest}


def _implausible_observation_time(observed_at: Any, created_at: Any) -> bool:
    """A stored observation must fall between session creation and now."""
    try:
        moment = datetime.fromisoformat(observed_at)
        created = float(created_at)
    except (TypeError, ValueError):
        return True
    if moment.tzinfo is None:
        return True
    return moment.timestamp() < created or moment > datetime.now(timezone.utc) + OBSERVATION_CLOCK_SKEW


def close_session(*, capability: str) -> dict[str, Any]:
    state = _resolve_capability(capability)
    session_path = _safe_session_path(_state_root(), state["session_id"])
    observation = state.get("preview_submission") if state["kind"] == "preview" else None
    artifact_changed = False
    implausible_time = False
    if observation is not None:
        root = Path(state["repo_root"])
        artifact = root / state["artifact_path"]
        if not isinstance(observation, dict) or set(observation) != {"verdict", "artifact_sha256", "observed_at"} or validate_target_path(state["artifact_path"], root) is not None:
            artifact_changed = True
        else:
            try:
                artifact_changed = _hash_file(artifact) != observation["artifact_sha256"] or observation["artifact_sha256"] != state["expected_sha256"]
            except OSError:
                artifact_changed = True
            implausible_time = _implausible_observation_time(observation["observed_at"], state.get("created_at"))
    try:
        (session_path / "state.json").unlink()
        if state["kind"] == "preview":
            (session_path / "preview-submitted").unlink(missing_ok=True)
        session_path.rmdir()
    except OSError as exc:
        raise BrokerViolation("author broker session could not close safely") from exc
    if artifact_changed:
        raise BrokerViolation("preview artifact changed after verdict submission")
    if implausible_time:
        raise BrokerViolation("preview observation time is implausible")
    result = {"session_id": state["session_id"], "status": "closed"}
    if observation is not None:
        result["observation"] = observation
    return result


def _tool_schema(properties: dict[str, Any] | None = None, required: list[str] | None = None) -> dict[str, Any]:
    return {"type": "object", "properties": properties or {}, "required": required or [], "additionalProperties": False}


TOOLS = (
    {
        "name": "create_formal_session",
        "description": "Create one parent-only capability bound to the exact canonical permitted-output list for a formal model. Returns only a session id, opaque capability, and canonical permitted paths.",
        "inputSchema": _tool_schema(
            {
                "repo_root": {"type": "string", "minLength": 1},
                "workflow_file": {"type": "string", "minLength": 1},
                "model_id": {"type": "string", "minLength": 1},
                "permitted_paths": {"type": "array", "minItems": 1, "maxItems": MAX_PERMITTED_PATHS, "items": {"type": "string", "minLength": 1}},
            },
            ["repo_root", "workflow_file", "model_id", "permitted_paths"],
        ),
    },
    {
        "name": "write_formal_file",
        "description": "Write one canonical target from the capability's permitted-output list atomically. Returns only the canonical target and SHA-256 digest; never page or model prose.",
        "inputSchema": _tool_schema(
            {"capability": {"type": "string", "minLength": 1}, "target": {"type": "string", "minLength": 1}, "content": {"type": "string", "minLength": 1}},
            ["capability", "target", "content"],
        ),
    },
    {
        "name": "create_preview_session",
        "description": "Create one parent-only preview capability bound to the canonical artifact path and its expected SHA-256. Returns only a session id, opaque capability, and digest.",
        "inputSchema": _tool_schema(
            {"repo_root": {"type": "string", "minLength": 1}, "artifact_path": {"type": "string", "minLength": 1}, "expected_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"}},
            ["repo_root", "artifact_path", "expected_sha256"],
        ),
    },
    {
        "name": "submit_preview_verdict",
        "description": "Submit one closed rendered-preview verdict. The broker rehashes the artifact and returns only the verdict and artifact SHA-256; no page title, body text, prose, or route crosses the boundary.",
        "inputSchema": _tool_schema(
            {"capability": {"type": "string", "minLength": 1}, "verdict": {"type": "string", "enum": list(PREVIEW_VERDICTS)}},
            ["capability", "verdict"],
        ),
    },
    {
        "name": "close_session",
        "description": "Close one author-broker session and remove its private state. Intended for the trusted parent after the bounded agent call completes. Returns the session id and status; after a preview verdict it also returns `observation` with the verdict, artifact_sha256, and the broker-stamped observed_at time.",
        "inputSchema": _tool_schema({"capability": {"type": "string", "minLength": 1}}, ["capability"]),
    },
)

TOOL_NAMES = tuple(tool["name"] for tool in TOOLS)


def call_tool(name: str, arguments: Any) -> Any:
    if name not in TOOL_NAMES or not isinstance(arguments, dict):
        raise BrokerViolation("unknown author broker tool or malformed arguments")
    if name == "create_formal_session":
        return create_formal_session(**arguments)
    if name == "write_formal_file":
        return write_formal_file(**arguments)
    if name == "create_preview_session":
        return create_preview_session(**arguments)
    if name == "submit_preview_verdict":
        return submit_preview_verdict(**arguments)
    return close_session(**arguments)


def _error_code(exc: Exception) -> str:
    message = str(exc).casefold()
    if "permitted" in message or "target" in message or "artifact path" in message:
        return "path_violation"
    if "capability" in message or "session" in message:
        return "receipt_violation"
    if "content exceeds" in message:
        return "content_too_large"
    if "artifact bytes" in message or "preview artifact" in message:
        return "preview_mismatch"
    if "kind" in message:
        return "unsupported_kind"
    return "schema_validation"


def _response(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def handle_message(message: Any) -> dict[str, Any] | None:
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        return _error(None, -32600, "invalid request")
    request_id = message.get("id")
    method = message.get("method")
    if method == "notifications/initialized":
        return None
    if method == "initialize":
        requested = message.get("params", {}).get("protocolVersion", "2024-11-05")
        return _response(request_id, {"protocolVersion": requested, "capabilities": {"tools": {"listChanged": False}}, "serverInfo": SERVER_INFO})
    if method == "ping":
        return _response(request_id, {})
    if method == "tools/list":
        return _response(request_id, {"tools": list(TOOLS)})
    if method == "tools/call":
        params = message.get("params")
        if not isinstance(params, dict):
            return _error(request_id, -32602, "invalid tool parameters")
        try:
            result = call_tool(params.get("name"), params.get("arguments", {}))
        except Exception as exc:
            code = _error_code(exc)
            return _response(request_id, {"isError": True, "content": [{"type": "text", "text": f"broker_error:{code}"}], "structuredContent": {"error_code": code}})
        text = result if isinstance(result, str) else json.dumps(result, sort_keys=True, separators=(",", ":"))
        return _response(request_id, {"content": [{"type": "text", "text": text}]})
    return _error(request_id, -32601, "method not found")


def main() -> int:
    if sys.version_info < (3, 11):
        print("author broker requires Python 3.11 or newer", file=sys.stderr)
        return 2
    for raw_line in sys.stdin.buffer:
        try:
            message = json.loads(raw_line)
            reply = handle_message(message)
        except (UnicodeDecodeError, json.JSONDecodeError):
            reply = _error(None, -32700, "parse error")
        if reply is not None:
            sys.stdout.write(json.dumps(reply, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
