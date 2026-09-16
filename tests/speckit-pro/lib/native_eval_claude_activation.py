"""Fail-closed evidence for explicit Claude skill-loader activation.

The public plugin-eval stream omits the initial slash command.  This module
binds a controller-prepared static skill to Claude's retained root-session
JSONL, where the native loader records both the command envelope and its
directly parented rendered-skill injection.  Availability, final prose, and
correct output are deliberately not activation evidence.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any, Mapping


WITNESS_SCHEMA = "native-claude-explicit-skill-witness/v1"
RECEIPT_SCHEMA = "native-claude-explicit-skill-activation/v1"
AUTHORITY = "claude-session-loader"
MAX_TRACE_BYTES = 32 * 1024 * 1024
MAX_SESSION_BYTES = 16 * 1024 * 1024
MAX_SKILL_BYTES = 2 * 1024 * 1024
MAX_PROMPT_BYTES = 2 * 1024 * 1024
MAX_TRACE_RECORDS = 20_000
MAX_SESSION_RECORDS = 20_000
MAX_PROJECT_DIRECTORIES = 256
MAX_PROJECT_ENTRIES = 20_000

_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_SKILL = re.compile(r"[a-z0-9][a-z0-9._-]*:[a-z0-9][a-z0-9._-]*")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_VERSION = re.compile(r"[0-9A-Za-z][0-9A-Za-z._+-]{0,127}")
_DYNAMIC_SKILL_MARKERS = (
    re.compile(rb"\$(?:ARGUMENTS|\{ARGUMENTS\}|[0-9]+|\{CLAUDE_SESSION_ID\})"),
    re.compile(rb"(?m)^!`"),
)


class ClaudeActivationError(ValueError):
    """Base error for explicit Claude activation evidence."""


class ClaudeActivationUnavailable(ClaudeActivationError):
    """The expected native session artifact was not durably available."""


class ClaudeActivationInvalid(ClaudeActivationError):
    """The supplied or collected evidence violated the native contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ClaudeActivationInvalid(message)


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _text_bytes(value: object, label: str, maximum: int) -> bytes:
    _require(isinstance(value, str), f"{label} must be text")
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ClaudeActivationInvalid(f"{label} is not valid UTF-8 text") from exc
    _require(0 < len(encoded) <= maximum, f"{label} has invalid size")
    return encoded


def _canonical_uuid(value: object, label: str) -> str:
    _require(isinstance(value, str) and _UUID.fullmatch(value) is not None,
             f"{label} is not a canonical UUID")
    return value


def _canonical_skill(value: object) -> str:
    _require(isinstance(value, str) and _SKILL.fullmatch(value) is not None,
             "skill name must be a canonical namespaced skill")
    return value


def _absolute_posix_path(value: object, label: str) -> str:
    _require(isinstance(value, str) and "\x00" not in value and "\n" not in value
             and "\r" not in value and "\\" not in value,
             f"{label} is not a canonical absolute path")
    path = PurePosixPath(value)
    _require(path.is_absolute() and value == path.as_posix()
             and all(part not in {"", ".", ".."} for part in path.parts[1:]),
             f"{label} is not a canonical absolute path")
    return value


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    if len(pairs) != len({key for key, _value in pairs}):
        raise ValueError("duplicate JSON key")
    return dict(pairs)


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-JSON constant: {value}")


def _valid_json(value: Any) -> bool:
    if value is None or isinstance(value, (bool, int)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, str):
        return not any(0xD800 <= ord(char) <= 0xDFFF for char in value)
    if isinstance(value, list):
        return all(_valid_json(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _valid_json(key) and _valid_json(item)
                   for key, item in value.items())
    return False


def _json_line(value: str, label: str) -> dict[str, Any]:
    try:
        result = json.loads(
            value, object_pairs_hook=_unique_object, parse_constant=_reject_constant,
        )
    except (TypeError, ValueError) as exc:
        raise ClaudeActivationInvalid(f"malformed {label}: {exc}") from exc
    _require(isinstance(result, dict) and _valid_json(result), f"malformed {label}")
    return result


def _jsonl(raw: bytes, *, label: str, maximum_bytes: int,
           maximum_records: int, require_final_newline: bool = True) -> list[dict[str, Any]]:
    _require(isinstance(raw, bytes) and 0 < len(raw) <= maximum_bytes,
             f"{label} has invalid size")
    if require_final_newline:
        _require(raw.endswith(b"\n"), f"{label} may be truncated")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ClaudeActivationInvalid(f"{label} is not UTF-8") from exc
    lines = text.splitlines()
    _require(0 < len(lines) <= maximum_records, f"{label} exceeds record bounds")
    _require(all(line.strip() for line in lines), f"{label} contains a blank record")
    return [_json_line(line, f"{label} record {index}")
            for index, line in enumerate(lines, 1)]


def _frontmatter_body(staged_skill: bytes, expected_skill: str) -> bytes:
    _require(isinstance(staged_skill, bytes) and 0 < len(staged_skill) <= MAX_SKILL_BYTES,
             "staged skill has invalid size")
    try:
        staged_skill.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ClaudeActivationInvalid("staged skill is not UTF-8") from exc
    _require(staged_skill.startswith(b"---\n"), "staged skill has no strict frontmatter")
    end = staged_skill.find(b"\n---\n", 4)
    _require(end >= 4 and end <= 64 * 1024, "staged skill frontmatter is malformed")
    header = staged_skill[4:end].decode("utf-8")
    _require(len(header.splitlines()) <= 256, "staged skill frontmatter exceeds line bounds")
    fields: dict[str, str] = {}
    for line in header.splitlines():
        match = re.fullmatch(r"([A-Za-z][A-Za-z0-9-]*):[ \t]*(.*)", line)
        if match is None:
            continue
        key, value = match.groups()
        _require(key not in fields, f"staged skill has duplicate {key} frontmatter")
        fields[key] = value.strip()
    _require(fields.get("name") == expected_skill.rsplit(":", 1)[1],
             "staged skill name does not match the expected command")
    _require(fields.get("user-invocable") == "true",
             "staged skill is not explicitly user-invocable")
    _require(fields.get("disable-model-invocation") == "true",
             "staged skill does not preserve manual-only invocation")
    body = staged_skill[end + len(b"\n---\n"):]
    _require(bool(body), "staged skill body is empty")
    _require(not any(marker.search(body) for marker in _DYNAMIC_SKILL_MARKERS),
             "dynamic skill rendering is unsupported")
    return body


def _trace_identity(raw_trace: bytes, expected_skill: str) -> dict[str, Any]:
    records = _jsonl(
        raw_trace, label="Claude public trace", maximum_bytes=MAX_TRACE_BYTES,
        maximum_records=MAX_TRACE_RECORDS, require_final_newline=False,
    )
    init = [record for record in records
            if record.get("type") == "system" and record.get("subtype") == "init"]
    _require(len(init) == 1, "Claude public trace must contain one init record")
    record = init[0]
    session_id = _canonical_uuid(record.get("session_id"), "Claude init session id")
    cwd = _absolute_posix_path(record.get("cwd"), "Claude init cwd")
    version = record.get("claude_code_version")
    _require(isinstance(version, str) and _VERSION.fullmatch(version) is not None,
             "Claude init version is invalid")
    skills = record.get("skills")
    _require(isinstance(skills, list) and len(skills) <= 512
             and all(isinstance(item, str) for item in skills)
             and len(skills) == len(set(skills)), "Claude init skill inventory is invalid")
    _require(expected_skill in skills, "expected skill is absent from the Claude init inventory")
    return {
        "session_id": session_id,
        "cwd": cwd,
        "cli_version": version,
        "bytes": len(raw_trace),
        "sha256": _sha(raw_trace),
    }


def build_activation_witness(
    *, skill_name: str, prompt: str, staged_skill: bytes,
    staged_skill_directory: str, raw_trace: bytes,
) -> dict[str, Any]:
    """Build a controller-owned static rendering witness before replay grading."""
    skill = _canonical_skill(skill_name)
    prompt_bytes = _text_bytes(prompt, "explicit skill prompt", MAX_PROMPT_BYTES)
    command_prefix = f"/{skill}"
    _require(prompt == command_prefix or prompt.startswith(command_prefix + " "),
             "prompt is not an explicit invocation of the expected skill")
    arguments = prompt[len(command_prefix):]
    if arguments.startswith(" "):
        arguments = arguments[1:]
    arguments_bytes = arguments.encode("utf-8")
    directory = _absolute_posix_path(staged_skill_directory, "staged skill directory")
    _require(PurePosixPath(directory).name == skill.rsplit(":", 1)[1],
             "staged skill directory does not match the expected skill")
    body = _frontmatter_body(staged_skill, skill)
    command_content = (
        f"<command-message>{skill}</command-message>\n"
        f"<command-name>/{skill}</command-name>\n"
        f"<command-args>{arguments}</command-args>"
    ).encode("utf-8")
    rendered = (
        f"Base directory for this skill: {directory}\n".encode("utf-8")
        + body + b"\n\nARGUMENTS: " + arguments_bytes
    )
    trace = _trace_identity(raw_trace, skill)
    return {
        "schema_version": WITNESS_SCHEMA,
        "authority": "controller-prepared-static-skill",
        "skill": skill,
        "prompt": {"bytes": len(prompt_bytes), "sha256": _sha(prompt_bytes)},
        "arguments": {"bytes": len(arguments_bytes), "sha256": _sha(arguments_bytes)},
        "command_content": {"bytes": len(command_content), "sha256": _sha(command_content)},
        "rendered_injection": {"bytes": len(rendered), "sha256": _sha(rendered)},
        "skill_source": {
            "path": f"skills/{skill.rsplit(':', 1)[1]}/SKILL.md",
            "file_bytes": len(staged_skill),
            "file_sha256": _sha(staged_skill),
            "body_bytes": len(body),
            "body_sha256": _sha(body),
            "base_directory_bytes": len(directory.encode("utf-8")),
            "base_directory_sha256": _sha(directory.encode("utf-8")),
        },
        "trace": trace,
    }


def _digest_record(value: object, label: str) -> dict[str, Any]:
    _require(isinstance(value, dict) and set(value) == {"bytes", "sha256"},
             f"{label} witness is malformed")
    count = value.get("bytes")
    digest = value.get("sha256")
    _require(isinstance(count, int) and not isinstance(count, bool) and count >= 0
             and isinstance(digest, str) and _SHA256.fullmatch(digest) is not None,
             f"{label} witness is malformed")
    return {"bytes": count, "sha256": digest}


def _validated_witness(value: Mapping[str, Any]) -> dict[str, Any]:
    _require(isinstance(value, Mapping), "activation witness must be an object")
    witness = dict(value)
    _require(set(witness) == {
        "schema_version", "authority", "skill", "prompt", "arguments",
        "command_content", "rendered_injection", "skill_source", "trace",
    }, "activation witness fields are malformed")
    _require(witness.get("schema_version") == WITNESS_SCHEMA
             and witness.get("authority") == "controller-prepared-static-skill",
             "activation witness authority is invalid")
    skill = _canonical_skill(witness.get("skill"))
    for key in ("prompt", "arguments", "command_content", "rendered_injection"):
        witness[key] = _digest_record(witness.get(key), key.replace("_", " "))
    source = witness.get("skill_source")
    _require(isinstance(source, dict) and set(source) == {
        "path", "file_bytes", "file_sha256", "body_bytes", "body_sha256",
        "base_directory_bytes", "base_directory_sha256",
    }, "skill source witness is malformed")
    expected_path = f"skills/{skill.rsplit(':', 1)[1]}/SKILL.md"
    _require(source.get("path") == expected_path, "skill source path is invalid")
    for field in ("file_bytes", "body_bytes", "base_directory_bytes"):
        _require(isinstance(source.get(field), int) and not isinstance(source.get(field), bool)
                 and source[field] > 0, f"skill source {field} is invalid")
    for field in ("file_sha256", "body_sha256", "base_directory_sha256"):
        _require(isinstance(source.get(field), str)
                 and _SHA256.fullmatch(source[field]) is not None,
                 f"skill source {field} is invalid")
    trace = witness.get("trace")
    _require(isinstance(trace, dict) and set(trace) == {
        "session_id", "cwd", "cli_version", "bytes", "sha256",
    }, "trace witness is malformed")
    _canonical_uuid(trace.get("session_id"), "witness session id")
    _absolute_posix_path(trace.get("cwd"), "witness cwd")
    _require(isinstance(trace.get("cli_version"), str)
             and _VERSION.fullmatch(trace["cli_version"]) is not None,
             "witness Claude version is invalid")
    _digest_record({"bytes": trace.get("bytes"), "sha256": trace.get("sha256")},
                   "trace")
    return witness


def _record_identity(record: Mapping[str, Any], witness: Mapping[str, Any],
                     label: str) -> None:
    trace = witness["trace"]
    _require(record.get("type") == "user", f"{label} is not a user record")
    _require(record.get("sessionId") == trace["session_id"], f"{label} session mismatch")
    _require(record.get("cwd") == trace["cwd"], f"{label} cwd mismatch")
    _require(record.get("version") == trace["cli_version"], f"{label} version mismatch")
    _require(record.get("entrypoint") == "sdk-cli" and record.get("userType") == "external"
             and record.get("isSidechain") is False, f"{label} is not a root SDK user record")
    _canonical_uuid(record.get("uuid"), f"{label} uuid")
    _canonical_uuid(record.get("promptId"), f"{label} prompt id")
    _require(isinstance(record.get("timestamp"), str) and bool(record["timestamp"]),
             f"{label} timestamp is invalid")
    message = record.get("message")
    _require(isinstance(message, dict) and message.get("role") == "user",
             f"{label} message is invalid")


def parse_explicit_activation(
    raw_session: bytes, witness: Mapping[str, Any],
) -> dict[str, Any]:
    """Parse a retained raw root session against a saved controller witness."""
    expected = _validated_witness(witness)
    records = _jsonl(
        raw_session, label="Claude root session", maximum_bytes=MAX_SESSION_BYTES,
        maximum_records=MAX_SESSION_RECORDS,
    )
    record_uuids = [record["uuid"] for record in records
                    if isinstance(record.get("uuid"), str)]
    _require(len(record_uuids) == len(set(record_uuids)),
             "Claude root session contains duplicate record UUIDs")
    skill = expected["skill"]
    prefix = f"<command-message>{skill}</command-message>\n".encode("utf-8")
    command_candidates: list[tuple[int, dict[str, Any], bytes]] = []
    for index, record in enumerate(records):
        message = record.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, str):
            encoded = content.encode("utf-8", errors="strict")
            if encoded.startswith(prefix):
                command_candidates.append((index, record, encoded))
    _require(len(command_candidates) == 1,
             "Claude root session must contain one expected loader command")
    command_index, command, command_content = command_candidates[0]
    _record_identity(command, expected, "Claude loader command")
    _require(command.get("parentUuid") is None and command.get("isMeta") in (None, False),
             "Claude loader command is not the root explicit prompt")
    command_digest = expected["command_content"]
    _require(len(command_content) == command_digest["bytes"]
             and _sha(command_content) == command_digest["sha256"],
             "Claude loader command does not match the controller prompt")
    _require(command_index == min(
        index for index, record in enumerate(records)
        if isinstance(record.get("message"), dict)
        and record["message"].get("role") == "user"
    ), "Claude loader command is not the first root user message")

    child_candidates = [
        (index, record) for index, record in enumerate(records)
        if record.get("type") == "user" and record.get("isMeta") is True
        and record.get("parentUuid") == command.get("uuid")
    ]
    _require(len(child_candidates) == 1,
             "Claude root session must contain one direct loader injection")
    injection_index, injection = child_candidates[0]
    _require(injection_index == command_index + 1,
             "Claude loader injection is not adjacent to its command")
    _record_identity(injection, expected, "Claude loader injection")
    for field in ("sessionId", "promptId", "cwd", "version", "entrypoint",
                  "userType", "isSidechain", "timestamp"):
        _require(injection.get(field) == command.get(field),
                 f"Claude loader injection {field} does not match its command")
    message = injection["message"]
    content = message.get("content")
    _require(isinstance(content, list) and len(content) == 1
             and isinstance(content[0], dict)
             and set(content[0]) == {"type", "text"}
             and content[0].get("type") == "text"
             and isinstance(content[0].get("text"), str),
             "Claude loader injection content is malformed")
    rendered = content[0]["text"].encode("utf-8", errors="strict")
    rendering = expected["rendered_injection"]
    _require(len(rendered) == rendering["bytes"]
             and _sha(rendered) == rendering["sha256"],
             "Claude loader injection does not match the staged static skill")
    witness_bytes = json.dumps(expected, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=False).encode("utf-8")
    return {
        "schema_version": RECEIPT_SCHEMA,
        "authority": AUTHORITY,
        "skill": skill,
        "session_id": expected["trace"]["session_id"],
        "prompt_id": command["promptId"],
        "command_record": {
            "index": command_index,
            "uuid": command["uuid"],
            "content_bytes": len(command_content),
            "content_sha256": _sha(command_content),
        },
        "injection_record": {
            "index": injection_index,
            "uuid": injection["uuid"],
            "parent_uuid": injection["parentUuid"],
            "rendered_bytes": len(rendered),
            "rendered_sha256": _sha(rendered),
        },
        "skill_source": dict(expected["skill_source"]),
        "arguments": dict(expected["arguments"]),
        "session_artifact": {
            "bytes": len(raw_session),
            "sha256": _sha(raw_session),
        },
        "trace_binding": dict(expected["trace"]),
        "witness_sha256": _sha(witness_bytes),
    }


def _descriptor_collection_supported() -> bool:
    return (
        os.name == "posix" and hasattr(os, "O_DIRECTORY") and hasattr(os, "O_NOFOLLOW")
        and hasattr(os, "geteuid") and os.open in os.supports_dir_fd
        and os.stat in os.supports_dir_fd and os.stat in os.supports_follow_symlinks
    )


def _owned_directory(name: str | Path, *, directory_fd: int | None = None) -> int:
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(name, flags, dir_fd=directory_fd)
    metadata = os.fstat(descriptor)
    if not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.geteuid():
        os.close(descriptor)
        raise ClaudeActivationInvalid("Claude retained path is not an owned real directory")
    return descriptor


def _read_session_file(project_fd: int, filename: str) -> bytes:
    flags = (os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0)
             | getattr(os, "O_CLOEXEC", 0))
    descriptor = os.open(filename, flags, dir_fd=project_fd)
    try:
        before = os.fstat(descriptor)
        _require(stat.S_ISREG(before.st_mode), "Claude session artifact is not a regular file")
        _require(before.st_uid == os.geteuid(), "Claude session artifact has wrong ownership")
        _require(before.st_nlink == 1, "Claude session artifact is hard-linked")
        _require(0 < before.st_size <= MAX_SESSION_BYTES,
                 "Claude session artifact has invalid size")
        payload = bytearray()
        while len(payload) <= MAX_SESSION_BYTES:
            chunk = os.read(descriptor, min(65536, MAX_SESSION_BYTES + 1 - len(payload)))
            if not chunk:
                break
            payload.extend(chunk)
        _require(len(payload) <= MAX_SESSION_BYTES,
                 "Claude session artifact exceeds byte bounds")
        after = os.fstat(descriptor)
        _require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
                 == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
                 and len(payload) == before.st_size,
                 "Claude session artifact changed during collection")
        return bytes(payload)
    finally:
        os.close(descriptor)


def collect_retained_session(
    retained_root: Path, witness: Mapping[str, Any],
) -> bytes:
    """Collect only the exact root-session JSONL from a retained eval tree.

    The caller must persist the returned bytes with its existing write-once raw
    evidence mechanism before grading.  This function never writes a receipt.
    """
    expected = _validated_witness(witness)
    if not _descriptor_collection_supported():
        raise ClaudeActivationUnavailable(
            "platform lacks descriptor primitives for safe Claude session collection"
        )
    target = f"{expected['trace']['session_id']}.jsonl"
    root_fd: int | None = None
    config_fd: int | None = None
    projects_fd: int | None = None
    try:
        root_fd = _owned_directory(Path(retained_root))
        config_fd = _owned_directory("config", directory_fd=root_fd)
        projects_fd = _owned_directory("projects", directory_fd=config_fd)
        project_names = sorted(os.listdir(projects_fd))
        _require(len(project_names) <= MAX_PROJECT_DIRECTORIES,
                 "Claude retained projects exceed directory bounds")
        matches: list[bytes] = []
        total_entries = 0
        for project_name in project_names:
            metadata = os.stat(project_name, dir_fd=projects_fd, follow_symlinks=False)
            _require(not stat.S_ISLNK(metadata.st_mode),
                     "Claude retained projects contain a symlink")
            _require(stat.S_ISDIR(metadata.st_mode),
                     "Claude retained projects contain an unexpected entry")
            project_fd = _owned_directory(project_name, directory_fd=projects_fd)
            try:
                entries = sorted(os.listdir(project_fd))
                total_entries += len(entries)
                _require(total_entries <= MAX_PROJECT_ENTRIES,
                         "Claude retained projects exceed entry bounds")
                for entry in entries:
                    entry_metadata = os.stat(entry, dir_fd=project_fd, follow_symlinks=False)
                    _require(not stat.S_ISLNK(entry_metadata.st_mode),
                             "Claude retained project contains a symlink")
                    _require(stat.S_ISDIR(entry_metadata.st_mode)
                             or stat.S_ISREG(entry_metadata.st_mode),
                             "Claude retained project contains a special entry")
                    if entry == target:
                        matches.append(_read_session_file(project_fd, entry))
            finally:
                os.close(project_fd)
        _require(len(matches) <= 1, "multiple Claude root-session artifacts matched")
        if not matches:
            raise ClaudeActivationUnavailable("Claude root-session artifact is unavailable")
        return matches[0]
    except FileNotFoundError as exc:
        raise ClaudeActivationUnavailable("Claude retained session tree is unavailable") from exc
    except ClaudeActivationError:
        raise
    except OSError as exc:
        raise ClaudeActivationInvalid(f"Claude retained session collection failed: {exc}") from exc
    finally:
        for descriptor in (projects_fd, config_fd, root_fd):
            if descriptor is not None:
                os.close(descriptor)


__all__ = [
    "AUTHORITY",
    "RECEIPT_SCHEMA",
    "WITNESS_SCHEMA",
    "ClaudeActivationError",
    "ClaudeActivationInvalid",
    "ClaudeActivationUnavailable",
    "build_activation_witness",
    "collect_retained_session",
    "parse_explicit_activation",
]
