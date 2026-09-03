#!/usr/bin/env python3
"""Claude hook attestation and receipt-only enforcement for sweep agents."""

from __future__ import annotations

import enum
import hashlib
import json
import os
import re
import secrets
import stat
import sys
import time
from pathlib import Path
from typing import Any


HOOK_VERSION = "sweep-isolation-v1"
FAILURE_MESSAGE = "feedback sweep security hook failed closed"
RECEIPT_RE = re.compile(r"^sweep-result:v1:[0-9a-f]{64}$")
CAPABILITY_RE = re.compile(r"^sweep-cap:v1:[0-9a-f]{32}:[0-9a-f]{64}$")
SWEEP_ROLES = {
    "sweep-classifier",
    "sweep-analyst",
    "speckit-pro:sweep-classifier",
    "speckit-pro:sweep-analyst",
}
PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class HookReason(enum.Enum):
    """Closed vocabulary naming which check refused the run.

    The hook prints exactly one of these names after ``FAILURE_MESSAGE`` so the
    model can correct the specific violation instead of guessing. Every value is
    a literal defined here. Reviewer comments, snapshot bytes, payload fields,
    environment values, and exception text never reach the message.
    """

    ATTESTATION = "attestation"
    BROKER_SCOPE = "broker_scope"
    HOOK_INPUT = "hook_input"
    HOOK_MODE = "hook_mode"
    LAUNCHER_CAPABILITY = "launcher_capability"
    RECEIPT_MISSING = "receipt_missing"
    RECEIPT_SHAPE = "receipt_shape"
    UNCLASSIFIED = "unclassified"


class HookRefusal(Exception):
    """A fail-closed refusal that carries one reason class and nothing else."""

    def __init__(self, reason: HookReason) -> None:
        super().__init__(reason.value)
        self.reason = reason


def _refuse(reason: HookReason) -> int:
    print(f"{FAILURE_MESSAGE}: {reason.value}", file=sys.stderr)
    return 2


def _payload() -> dict[str, Any]:
    raw = sys.stdin.buffer.read(64 * 1024 + 1)
    if len(raw) > 64 * 1024:
        raise ValueError("hook input exceeds the bound")
    value = json.loads(raw or b"{}")
    if not isinstance(value, dict):
        raise ValueError("hook input must be an object")
    return value


def _repo_root(payload: dict[str, Any]) -> Path:
    value = payload.get("cwd")
    if not isinstance(value, str) or not value:
        value = os.getcwd()
    return Path(value).resolve(strict=False)


def _attestation_path(repo_root: Path) -> Path:
    uid = getattr(os, "getuid", lambda: 0)()
    root = Path(os.environ.get("TMPDIR") or "/tmp") / f"speckit-pro-sweep-hooks-{uid}"
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = root.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise OSError("unsafe hook attestation directory")
    uid = getattr(os, "getuid", lambda: info.st_uid)()
    if info.st_uid != uid:
        raise OSError("hook attestation directory has the wrong owner")
    if stat.S_IMODE(info.st_mode) & 0o077:
        os.chmod(root, 0o700)
    digest = hashlib.sha256(str(repo_root).encode("utf-8")).hexdigest()
    return root / f"{digest}.json"


def _hooks_sha256() -> str:
    return hashlib.sha256((PLUGIN_ROOT / "hooks" / "hooks.json").read_bytes()).hexdigest()


def _hook_script_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _write_attestation(repo_root: Path) -> None:
    target = _attestation_path(repo_root)
    temporary = target.with_name(f".{target.name}.{secrets.token_hex(8)}.tmp")
    record = {
        "version": HOOK_VERSION,
        "repo_root": str(repo_root),
        "hooks_sha256": _hooks_sha256(),
        "hook_script_sha256": _hook_script_sha256(),
        "created_at": time.time(),
    }
    fd = os.open(
        temporary,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            fd = -1
            json.dump(record, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if fd >= 0:
            os.close(fd)
        try:
            temporary.unlink()
        except FileNotFoundError:
            # The atomic replace may already have removed the temporary path.
            pass


def _verify_attestation(repo_root: Path) -> None:
    path = _attestation_path(repo_root)
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        info = os.fstat(fd)
        uid = getattr(os, "getuid", lambda: info.st_uid)()
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != uid
            or stat.S_IMODE(info.st_mode) & 0o077
            or info.st_size > 16 * 1024
        ):
            raise OSError("unsafe hook attestation record")
        with os.fdopen(fd, "r", encoding="utf-8") as handle:
            fd = -1
            record = json.load(handle)
    finally:
        if fd >= 0:
            os.close(fd)
    if (
        not isinstance(record, dict)
        or record.get("version") != HOOK_VERSION
        or record.get("repo_root") != str(repo_root)
        or record.get("hooks_sha256") != _hooks_sha256()
        or record.get("hook_script_sha256") != _hook_script_sha256()
        or time.time() - float(record.get("created_at", 0)) > 24 * 60 * 60
    ):
        raise ValueError("hook attestation is stale or mismatched")


def _reason_checked(reason: HookReason, fn, *args: Any) -> Any:
    """Run ``fn(*args)``, turning its checked errors into one ``HookRefusal``.

    Every call site that needs a specific reason class instead of the generic
    ``UNCLASSIFIED`` fallback goes through here, so the checked-exception tuple
    stays in one place.
    """
    try:
        return fn(*args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise HookRefusal(reason) from exc


def _require_attestation(repo_root: Path) -> None:
    _reason_checked(HookReason.ATTESTATION, _verify_attestation, repo_root)


def _agent_type(payload: dict[str, Any]) -> str | None:
    direct = payload.get("agent_type") or payload.get("subagent_type")
    if isinstance(direct, str):
        return direct
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        nested = tool_input.get("subagent_type") or tool_input.get("agent_type")
        if isinstance(nested, str):
            return nested
    return None


def _final_message(payload: dict[str, Any]) -> str | None:
    for key in ("last_assistant_message", "agent_output", "output"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    return None


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] != HOOK_VERSION:
        print("feedback sweep hook version mismatch", file=sys.stderr)
        return 2
    if sys.version_info < (3, 11):
        print("feedback sweep hooks require Python 3.11 or newer", file=sys.stderr)
        return 2
    try:
        payload = _reason_checked(HookReason.HOOK_INPUT, _payload)
        repo_root = _reason_checked(HookReason.HOOK_INPUT, _repo_root, payload)
        mode = argv[0]
        if mode == "attest":
            _reason_checked(HookReason.ATTESTATION, _write_attestation, repo_root)
            return 0
        role = _agent_type(payload)
        if mode == "authorize-broker":
            _require_attestation(repo_root)
            capability = os.environ.get("SPECKIT_SWEEP_CAPABILITY", "")
            agent_id = payload.get("agent_id")
            if (
                role not in SWEEP_ROLES
                or not isinstance(agent_id, str)
                or not agent_id
                or CAPABILITY_RE.fullmatch(capability) is None
            ):
                # Broker calls are restricted to the isolated sweep subagent.
                raise HookRefusal(HookReason.BROKER_SCOPE)
            return 0
        if role not in SWEEP_ROLES:
            return 0
        _require_attestation(repo_root)
        if mode == "pre-dispatch":
            capability = os.environ.get("SPECKIT_SWEEP_CAPABILITY", "")
            if CAPABILITY_RE.fullmatch(capability) is None:
                # Sweep agents require an isolated launcher capability.
                raise HookRefusal(HookReason.LAUNCHER_CAPABILITY)
            return 0
        if mode == "validate-stop":
            final = _final_message(payload)
            if final is None:
                raise HookRefusal(HookReason.RECEIPT_MISSING)
            if RECEIPT_RE.fullmatch(final.strip()) is None:
                # The final output is not exactly one valid receipt.
                raise HookRefusal(HookReason.RECEIPT_SHAPE)
            return 0
        raise HookRefusal(HookReason.HOOK_MODE)
    except HookRefusal as refusal:
        return _refuse(refusal.reason)
    except Exception:
        # Every other failure, named or not, still fails closed with one reason
        # class. A traceback would exit 1, which the hook contract treats as
        # allow, and would print exception text the model must never read.
        return _refuse(HookReason.UNCLASSIFIED)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
