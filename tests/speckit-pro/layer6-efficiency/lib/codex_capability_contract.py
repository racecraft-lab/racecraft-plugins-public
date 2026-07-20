#!/usr/bin/env python3
"""Capability evidence constants, canonicalization, and input contract helpers."""

from __future__ import annotations

import argparse
import base64
import binascii
import copy
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
from html.parser import HTMLParser
import json
import os
import re
import secrets
import stat
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

SCHEMA_VERSION = "1.0.0"
PENDING_TELEMETRY_PROFILE_ID = "sha256:f39d0acd9403d193b07861c5cba5dac0e7ba901936ad542c18dd4eb008ec898b"
EXTRACT_NORMALIZATION = "unicode_text_whitespace_collapsed_utf8"
SURFACES = ("app_server", "cli", "interactive_picker")
APPROVED_CANARY_EXECUTORS = ()
APPROVED_LIVE_COLLECTION_METHODS = ()
CANONICAL_MANIFEST_SCHEMA_VERSION = "2.0.0"
CANONICAL_MANIFEST_SNAPSHOT_ID = "G56R-001-SNAPSHOT-2026-07-16-V3"
CANONICAL_MANIFEST_DIGEST = "sha256:3dc5c6c7a117ac8d01728ffeff1a35cf38fb0d6e982bb029cf192a790d30cd64"
PRIVATE_REFRESH_MAX_BYTES = 32 * 1024 * 1024
RAW_EVIDENCE_RETENTION_DAYS = 30
RAW_EVIDENCE_PENDING_DAYS = 30
RETENTION_RECORDS_DIR = "retention-records"
DELETION_RECORDS_DIR = "deletion-records"
PUBLICATION_RECEIPTS_DIR = "publication-receipts"
DELETION_INTENTS_DIR = "deletion-intents"
RETENTION_LOCK_FILE = ".retention-lock"
HAS_DESCRIPTOR_RELATIVE_IO = os.open in os.supports_dir_fd and os.stat in os.supports_dir_fd
ERROR_TERMINALS = ("timeout", "output_cap_exceeded", "launch_error", "transport_error", "authentication_error", "rate_limited", "malformed_response", "explicit_rejection", "service_reroute", "ambiguous_error")
_UNSET = object()


class _BlockingHardLinkRace(ValueError):
    """Deletion cannot complete while the original evidence inode remains linked."""


_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
_HEX_SHA256 = re.compile(r"[0-9a-f]{64}")
_RAW_REF = re.compile(r"raw://sha256:[0-9a-f]{64}")
_TOKEN = re.compile(r"[a-z0-9][a-z0-9._-]*")
_CLAIM_ID = re.compile(r"[A-Z0-9][A-Z0-9_-]*")
_LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._-]{0,127}")
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,127}")
_GIT_OBJECT = re.compile(r"[0-9a-f]{40,64}")
_WORK_ITEM_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
_RFC3339_UTC = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z")
_SOURCE_ID = re.compile(r"OPENAI-DOC-[0-9]{3}")
_OPENAI_AUTHORITY_PREFIXES = {
    "learn.chatgpt.com": ("/docs",),
    "developers.openai.com": ("/codex", "/api/docs"),
    "platform.openai.com": ("/docs",),
}
_MULTI_CLAIM_EXTRACT_DEPENDENCIES = {
    "OPENAI-DOC-022": {
        "b8177497966d4cee4b9ca46d971800df3ac074c70d05420d96ab2dd979ab1542": {"G56R-V3-PROMPT_ABLATION"},
        "6c3191ea0ea940545c49d495a06e9ff910ff0a41885ca509af06648dd59c6c3c": {"G56R-V3-PROMPT_GUIDANCE"},
        "77d357a58637de23803a1f4c01271e3eee4525e177d9bc42fbb2cda6d0167123": {"G56R-V3-PROMPT_GUIDANCE"},
    },
}
_ENTRY_KEYS = {"model", "effort", "available", "hidden", "machine_id", "raw_label", "capabilities"}
_OBSERVATION_KEYS = {
    "surface_observation_id", "client_identity_id", "surface", "collection_method_id",
    "method_inputs_digest", "started_at", "completed_at", "completeness_state",
    "visibility_policy", "entries", "raw_evidence_digest", "raw_evidence_ref",
    "sanitized_evidence_digest", "repository_binding", "work_item",
}
_SANITIZER_PROFILES = {
    "surface_entry": (_ENTRY_KEYS, frozenset(), True),
    "surface_status": (frozenset({"surface", "status"}), frozenset(), False),
    "fixture_identity": (frozenset({"account"}), frozenset({"account"}), False),
}
_FORBIDDEN_KEY_PARTS = ("authorization", "credential", "secret", "token", "cookie", "header", "prompt", "content", "account", "hostname", "host_name", "path", "remote")


class _AuthorityTupleSet(list):
    pass


class _BoundDecisionSet(list):
    pass


class _VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts, self.hidden_stack, self.invalid_hidden_markup = [], [], False

    def handle_starttag(self, tag, attrs):
        if tag in {"head", "script", "style", "noscript", "template", "svg"}:
            self.hidden_stack.append(tag)

    def handle_endtag(self, tag):
        if tag in {"head", "script", "style", "noscript", "template", "svg"}:
            if not self.hidden_stack or self.hidden_stack[-1] != tag:
                self.invalid_hidden_markup = True
            else:
                self.hidden_stack.pop()

    def handle_data(self, data):
        if not self.hidden_stack and not self.invalid_hidden_markup:
            self.parts.append(data)


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def digest(value):
    raw = value if isinstance(value, bytes) else canonical_bytes(value)
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


def _visible_text(value):
    parser = _VisibleText(); parser.feed(value)
    if parser.rawdata:
        raise ValueError("retrieved body contains malformed hidden markup")
    parser.close()
    if parser.invalid_hidden_markup or parser.hidden_stack:
        raise ValueError("retrieved body contains malformed hidden markup")
    return " ".join(" ".join(parser.parts).split())


def _validated_body(body_b64, extracts, source_id):
    if body_b64 is None:
        if extracts:
            raise ValueError(f"{source_id} bounded extracts require a retrieved body")
        return None
    try:
        body_bytes = base64.b64decode(body_b64, validate=True)
        body_text = body_bytes.decode()
    except (binascii.Error, UnicodeDecodeError, TypeError):
        raise ValueError("retrieved body must be canonical UTF-8 base64")
    if base64.b64encode(body_bytes).decode() != body_b64:
        raise ValueError("retrieved body must be canonical UTF-8 base64")
    collapsed = _visible_text(body_text)
    valid_extracts = isinstance(extracts, list) and extracts and all(
        set(extract) == {"text", "extract_sha256", "normalization"}
        and isinstance(extract["text"], str) and extract["text"]
        and extract["normalization"] == EXTRACT_NORMALIZATION
        and _HEX_SHA256.fullmatch(str(extract["extract_sha256"]))
        and hashlib.sha256(extract["text"].encode()).hexdigest() == extract["extract_sha256"]
        and extract["text"] in collapsed
        for extract in extracts
    )
    if not valid_extracts:
        raise ValueError(f"{source_id} retrieved body does not contain every bounded extract")
    return body_bytes


def _need_digest(value, field):
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise ValueError(f"{field} must be a sha256 digest")


def _token(value):
    return isinstance(value, str) and bool(_TOKEN.fullmatch(value))


def _openai_url(value):
    if not isinstance(value, str) or not value or any(character.isspace() or ord(character) < 0x20 or ord(character) == 0x7f for character in value):
        return False
    parsed = urlparse(value); host = (parsed.hostname or "").lower()
    try:
        port = parsed.port
    except ValueError:
        return False
    path_parts = parsed.path.split("/")
    canonical_path = (
        parsed.path.startswith("/")
        and "%" not in parsed.path
        and "\\" not in parsed.path
        and "" not in path_parts[1:]
        and not {".", ".."} & set(path_parts)
    )
    allowed_path = any(
        parsed.path == prefix or parsed.path.startswith(f"{prefix}/")
        for prefix in _OPENAI_AUTHORITY_PREFIXES.get(host, ())
    )
    return (
        parsed.scheme == "https"
        and parsed.geturl() == value
        and parsed.username is None
        and parsed.password is None
        and port is None
        and parsed.netloc.lower() == host
        and parsed.query in {"", "surface=cli"}
        and parsed.fragment in {"", "configure-footer-items-with-statusline"}
        and canonical_path
        and allowed_path
    )


def _utc_timestamp(value):
    if not isinstance(value, str) or not _RFC3339_UTC.fullmatch(value): return False
    try: parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError: return False
    return parsed.tzinfo is not None and parsed.utcoffset().total_seconds() == 0


def _parsed_timestamp(value, field):
    if not _utc_timestamp(value):
        raise ValueError(f"{field} must be RFC3339 UTC")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value):
    raise ValueError(f"non-JSON numeric constant: {value}")


def _parse_json_bytes(raw):
    try:
        return json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("JSON input must be strict UTF-8 JSON") from error

__all__ = [name for name in globals() if not name.startswith("__")]
