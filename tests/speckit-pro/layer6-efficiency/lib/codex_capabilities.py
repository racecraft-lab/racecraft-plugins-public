#!/usr/bin/env python3
"""Fail-closed Codex capability evidence adapter for G56R-002."""

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
RETENTION_LOCK_DIR = ".retention-lock"
ERROR_TERMINALS = ("timeout", "output_cap_exceeded", "launch_error", "transport_error", "authentication_error", "rate_limited", "malformed_response", "explicit_rejection", "service_reroute", "ambiguous_error")
_UNSET = object()
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


def _stable_file_identity(metadata):
    return (
        metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns,
        metadata.st_ctime_ns, stat.S_IMODE(metadata.st_mode),
    )


def _read_bounded_regular_file(path, *, required_mode=None):
    source = Path(os.path.abspath(path))
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        pathname_before = os.stat(source, follow_symlinks=False)
        if not stat.S_ISREG(pathname_before.st_mode):
            raise ValueError("bounded input must be a regular non-symlink file")
        descriptor = os.open(source, flags)
    except OSError as error:
        raise ValueError("bounded input must be a readable regular non-symlink file") from error
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("bounded input must be a regular file")
        if _stable_file_identity(pathname_before) != _stable_file_identity(before):
            raise ValueError("bounded input pathname changed before it was read")
        if required_mode is not None and os.name != "nt" and stat.S_IMODE(before.st_mode) != required_mode:
            raise ValueError(f"private input must use mode {required_mode:04o}")
        if before.st_size > PRIVATE_REFRESH_MAX_BYTES:
            raise ValueError("bounded input exceeds the maximum size")
        chunks, total = [], 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, PRIVATE_REFRESH_MAX_BYTES + 1 - total))
            if not chunk:
                break
            chunks.append(chunk); total += len(chunk)
            if total > PRIVATE_REFRESH_MAX_BYTES:
                raise ValueError("bounded input exceeds the maximum size")
        after = os.fstat(descriptor)
        if _stable_file_identity(after) != _stable_file_identity(before) or total != after.st_size:
            raise ValueError("bounded input changed while it was being read")
        try:
            current = os.stat(source, follow_symlinks=False)
        except OSError as error:
            raise ValueError("bounded input pathname changed while it was being read") from error
        if not stat.S_ISREG(current.st_mode) or _stable_file_identity(current) != _stable_file_identity(after):
            raise ValueError("bounded input pathname changed while it was being read")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def digest_regular_file(path):
    source = Path(os.path.abspath(path)); flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        pathname_before = os.stat(source, follow_symlinks=False)
        if not stat.S_ISREG(pathname_before.st_mode): raise ValueError("client executable must be a regular file that is not a symlink")
        descriptor = os.open(source, flags)
    except OSError as error:
        raise ValueError("client executable must be a readable regular file that is not a symlink") from error
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or _stable_file_identity(pathname_before) != _stable_file_identity(before):
            raise ValueError("client executable pathname changed before hashing")
        hasher, remaining = hashlib.sha256(), before.st_size
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                raise ValueError("client executable changed while hashing")
            hasher.update(chunk); remaining -= len(chunk)
        after = os.fstat(descriptor)
        if _stable_file_identity(before) != _stable_file_identity(after):
            raise ValueError("client executable changed while hashing")
        try:
            current = os.stat(source, follow_symlinks=False)
        except OSError as error:
            raise ValueError("client executable pathname changed while hashing") from error
        if not stat.S_ISREG(current.st_mode) or _stable_file_identity(current) != _stable_file_identity(after):
            raise ValueError("client executable pathname changed while hashing")
        return f"sha256:{hasher.hexdigest()}"
    finally:
        os.close(descriptor)


def _extract_claim_dependencies(source):
    bindings = set(source["claim_bindings"])
    if len(bindings) == 1:
        return {item["extract_sha256"]: set(bindings) for item in source["bounded_extracts"]}
    raw = source.get("extract_claim_dependencies", _MULTI_CLAIM_EXTRACT_DEPENDENCIES.get(source["official_source_ledger_id"], {}))
    return {key: set(value) for key, value in raw.items()}


def _route_claim_dependencies(route, sources_by_id):
    source_ids = route.get("official_source_ledger_ids", [])
    raw = route.get("official_source_claim_dependencies")
    if raw is None:
        dependencies = {}
        for source_id in source_ids:
            bindings = set(sources_by_id[source_id]["claim_bindings"])
            if len(bindings) != 1:
                raise ValueError("multi-claim route source requires explicit route-to-claim dependencies")
            dependencies[source_id] = bindings
        return dependencies
    if not isinstance(raw, dict) or set(raw) != set(source_ids):
        raise ValueError("route-to-claim dependencies must cover every bound source exactly")
    dependencies = {}
    for source_id, claims in raw.items():
        bindings = set(sources_by_id[source_id]["claim_bindings"])
        if not isinstance(claims, list) or not claims or len(claims) != len(set(claims)) or not set(claims) <= bindings:
            raise ValueError("route-to-claim dependency is not bound to its source")
        dependencies[source_id] = set(claims)
    return dependencies


def validate_manifest(manifest, *, allow_synthetic_manifest=False):
    snapshot = manifest.get("snapshot", {})
    if manifest.get("schema_version") != CANONICAL_MANIFEST_SCHEMA_VERSION or snapshot.get("snapshot_id") != CANONICAL_MANIFEST_SNAPSHOT_ID:
        raise ValueError("manifest schema or snapshot identity is not the canonical G56R-001 v3 authority")
    if not allow_synthetic_manifest and digest(manifest) != CANONICAL_MANIFEST_DIGEST:
        raise ValueError("manifest content does not match the canonical G56R-001 v3 authority")
    sources = manifest.get("official_source_ledger", [])
    ids = [row.get("official_source_ledger_id") for row in sources]
    if len(sources) != 22 or len(set(ids)) != 22 or any(not _SOURCE_ID.fullmatch(str(item)) for item in ids):
        raise ValueError("manifest must contain exactly 22 unique current OPENAI-DOC records")
    if any(not isinstance(row.get("claim_bindings"), list) or not row["claim_bindings"] or len(row["claim_bindings"]) != len(set(row["claim_bindings"])) or not all(isinstance(item, str) and _CLAIM_ID.fullmatch(item) for item in row["claim_bindings"]) or not _openai_url(row.get("requested_url")) or not _openai_url(row.get("canonical_url")) for row in sources):
        raise ValueError("every current source requires claim bindings and approved URLs")
    for row in sources:
        extracts = row.get("bounded_extracts", [])
        if not extracts or any(set(item) != {"text", "extract_sha256", "normalization"} or not item["text"] or item["normalization"] != EXTRACT_NORMALIZATION or not _HEX_SHA256.fullmatch(str(item["extract_sha256"])) or hashlib.sha256(item["text"].encode()).hexdigest() != item["extract_sha256"] for item in extracts):
            raise ValueError("every current source requires valid bounded extracts")
        bindings = set(row["claim_bindings"])
        if len(bindings) > 1:
            dependencies = _extract_claim_dependencies(row)
            if set(dependencies) != {item["extract_sha256"] for item in extracts} or set().union(*dependencies.values()) != bindings or any(not claims or not claims <= bindings for claims in dependencies.values()):
                raise ValueError("multi-claim source requires complete extract-to-claim dependencies")
    contracts = manifest.get("agent_contracts", []); contract_ids = [row.get("agent_contract_id") for row in contracts]
    routes = manifest.get("candidate_routes", []); route_ids = [row.get("candidate_route_id") for row in routes]
    invalid_contract_hash = any(not _HEX_SHA256.fullmatch(str(row.get("source_sha256"))) or not _HEX_SHA256.fullmatch(str(row.get("instruction_sha256"))) for row in contracts)
    if len(contracts) != 12 or len(routes) != 23 or len(contract_ids) != len(set(contract_ids)) or len(route_ids) != len(set(route_ids)) or invalid_contract_hash or any(row.get("agent_contract_id") not in set(contract_ids) for row in routes):
        raise ValueError("candidate routes require unique agent-contract owners")
    efforts = manifest.get("effort_surface_records", [])
    effort_ids = [row.get("effort_surface_record_id") for row in efforts]
    if len(efforts) != 5 or len(effort_ids) != len(set(effort_ids)) or any(row.get("official_source_ledger_id") not in set(ids) for row in efforts):
        raise ValueError("manifest must contain exactly five effort-surface records")
    contracts_by_id = {row["agent_contract_id"]: row for row in contracts}; effort_id_set = set(effort_ids); source_id_set = set(ids)
    invalid_route_binding = any(
        not _HEX_SHA256.fullmatch(str(row.get("role_instruction_sha256")))
        or row.get("role_instruction_sha256") != contracts_by_id[row["agent_contract_id"]]["instruction_sha256"]
        or not set(row.get("official_source_ledger_ids", [])) <= source_id_set
        or not set(row.get("effort_surface_record_ids", [])) <= effort_id_set
        or len(row.get("official_source_ledger_ids", [])) != len(set(row.get("official_source_ledger_ids", [])))
        or len(row.get("effort_surface_record_ids", [])) != len(set(row.get("effort_surface_record_ids", [])))
        for row in routes
    )
    if invalid_route_binding: raise ValueError("candidate route authority binding is invalid")
    sources_by_id = {row["official_source_ledger_id"]: row for row in sources}
    for route in routes:
        _route_claim_dependencies(route, sources_by_id)
    quarantined, authoritative, by_record = [], set(), {}
    for row in efforts:
        values = row.get("documented_values", [])
        field = str(row.get("field", "")); codex_selector = str(row.get("surface", "")).startswith("Codex ") and any(name in field for name in ("model_reasoning_effort", "supportedReasoningEfforts", "defaultReasoningEffort"))
        if row.get("support_status") != "documented" or not codex_selector or any(not _token(value) for value in values):
            quarantined.append(str(row.get("effort_surface_record_id")))
        else:
            by_record[row["effort_surface_record_id"]] = set(values); authoritative.update(values)
    return {"current_source_count": 22, "historical_active_count": 0, "effort_surface_count": 5, "quarantined_effort_record_ids": sorted(quarantined), "authoritative_effort_tokens": sorted(authoritative), "authoritative_effort_tokens_by_record": {key: sorted(value) for key, value in by_record.items()}}


def _changed_extract_claims(source, extracts):
    original = source["bounded_extracts"]
    if extracts == original:
        return set()
    bindings = set(source["claim_bindings"])
    if len(bindings) == 1:
        return bindings
    dependencies = _extract_claim_dependencies(source)
    changed = [item for item in original if item not in extracts]
    claims = set().union(*(dependencies[item["extract_sha256"]] for item in changed)) if changed else set()
    return claims or bindings


def normalize_source_refreshes(manifest, captured, *, source_capture_digest=None, allow_synthetic_manifest=False):
    validate_manifest(manifest, allow_synthetic_manifest=allow_synthetic_manifest)
    if source_capture_digest is None:
        source_capture_digest = digest(canonical_bytes(captured) + b"\n")
    _need_digest(source_capture_digest, "source_capture_digest")
    sources = {row["official_source_ledger_id"]: row for row in manifest["official_source_ledger"]}
    actual = [row.get("official_source_ledger_id") for row in captured]
    if len(captured) != 22 or set(actual) != set(sources) or len(set(actual)) != 22:
        raise ValueError("source refresh must cover the 22 unique current records")
    statuses = {"confirmed_current", "changed", "redirected", "inaccessible", "withdrawn", "conflicting"}
    measured = {"official_source_ledger_id", "requested_url", "canonical_url", "retrieved_at", "status", "invalidated_claim_ids", "retrieved_body_b64", "bounded_extracts"}
    normalized = []
    for item in captured:
        source, status = sources[item["official_source_ledger_id"]], item.get("status")
        if set(item) != measured or item.get("requested_url") != source.get("requested_url") or not _openai_url(item.get("canonical_url")):
            raise ValueError("captured refresh identity or URL does not match current authority")
        if status not in statuses or not _utc_timestamp(item.get("retrieved_at")):
            raise ValueError("source refresh status or timestamp is invalid")
        bindings = list(source.get("claim_bindings", [])); invalid = list(item.get("invalidated_claim_ids", []))
        if len(invalid) != len(set(invalid)) or not set(invalid) <= set(bindings):
            raise ValueError("claim-scoped invalidation is invalid")
        canonical_changed = item["canonical_url"] != source["canonical_url"]
        if canonical_changed and set(invalid) != set(bindings):
            raise ValueError("canonical URL change must invalidate every bound claim")
        if status in {"inaccessible", "withdrawn", "conflicting"} and set(invalid) != set(bindings):
            raise ValueError("adverse source outcome must invalidate every bound claim")
        body_bytes = _validated_body(item["retrieved_body_b64"], item["bounded_extracts"], item["official_source_ledger_id"])
        body, extracts = (digest(body_bytes), list(item["bounded_extracts"])) if body_bytes is not None else (None, [])
        if body is not None:
            redirect_with_change = status == "redirected" and source["requested_url"] != item["canonical_url"]
            changed_claims = _changed_extract_claims(source, extracts)
            if changed_claims and (status != "changed" and not redirect_with_change or not changed_claims <= set(invalid)):
                raise ValueError("changed bounded extracts must invalidate dependent claims")
        if body is None and status not in {"inaccessible", "withdrawn", "conflicting"}:
            raise ValueError("a retrieved body is required for this source outcome")
        if body is not None and status in {"confirmed_current", "changed", "redirected"}:
            prior_body = f"sha256:{source['body_sha256']}"
            expected_status = "redirected" if source["requested_url"] != item["canonical_url"] else "changed" if canonical_changed else "confirmed_current" if body == prior_body else "changed"
            if status != expected_status: raise ValueError("source refresh status or timestamp is invalid")
        evidence = {"canonical_url": item["canonical_url"], "retrieved_at": item["retrieved_at"], "body_digest": body, "bounded_extracts": extracts}
        normalized.append({
            "official_source_ledger_id": item["official_source_ledger_id"],
            "requested_url": source["requested_url"], "canonical_url": item["canonical_url"],
            "retrieved_at": item["retrieved_at"], "body_digest": body, "status": status,
            "retrieved_body_b64": item["retrieved_body_b64"],
            "source_capture_digest": source_capture_digest,
            "bounded_extracts": extracts, "retrieval_evidence_digest": digest(evidence),
            "documented_facts": list(source.get("exact_documented_facts", [])),
            "claim_bindings": bindings, "invalidated_claim_ids": invalid,
            "prior_record_digest": digest(source),
        })
    return sorted(normalized, key=lambda row: row["official_source_ledger_id"])


def validate_published_source_refreshes(manifest, refreshes, *, allow_synthetic_manifest=False):
    validate_manifest(manifest, allow_synthetic_manifest=allow_synthetic_manifest); sources = {row["official_source_ledger_id"]: row for row in manifest["official_source_ledger"]}
    if len(refreshes) != 22 or [row.get("official_source_ledger_id") for row in refreshes] != sorted(sources):
        raise ValueError("source refresh must cover the 22 unique current records")
    keys = {"official_source_ledger_id", "requested_url", "canonical_url", "retrieved_at", "body_digest", "status", "source_capture_digest", "bounded_extracts", "retrieval_evidence_digest", "documented_facts", "claim_bindings", "invalidated_claim_ids", "prior_record_digest"}
    statuses = {"confirmed_current", "changed", "redirected", "inaccessible", "withdrawn", "conflicting"}
    for item in refreshes:
        source = sources[item["official_source_ledger_id"]]; bindings = source["claim_bindings"]
        if set(item) != keys or item["requested_url"] != source["requested_url"] or not _openai_url(item["canonical_url"]) or not _utc_timestamp(item["retrieved_at"]):
            raise ValueError("source refresh authority fields must be canonical manifest values")
        if item["documented_facts"] != source["exact_documented_facts"] or item["claim_bindings"] != bindings or item["prior_record_digest"] != digest(source):
            raise ValueError("source refresh authority fields must be canonical manifest values")
        _need_digest(item["source_capture_digest"], "source_capture_digest")
        invalid = item["invalidated_claim_ids"]
        if item["status"] not in statuses or len(invalid) != len(set(invalid)) or not set(invalid) <= set(bindings): raise ValueError("source refresh status or invalidation is invalid")
        canonical_changed = item["canonical_url"] != source["canonical_url"]
        if canonical_changed and set(invalid) != set(bindings):
            raise ValueError("canonical URL change must invalidate every bound claim")
        if item["body_digest"] is not None: _need_digest(item["body_digest"], "body_digest")
        elif item["bounded_extracts"]: raise ValueError("bounded extracts require a published body digest")
        for extract in item["bounded_extracts"]:
            if set(extract) != {"text", "extract_sha256", "normalization"} or not isinstance(extract["text"], str) or not extract["text"] or extract["normalization"] != EXTRACT_NORMALIZATION or not _HEX_SHA256.fullmatch(str(extract["extract_sha256"])) or hashlib.sha256(extract["text"].encode()).hexdigest() != extract["extract_sha256"]:
                raise ValueError("published bounded extract identity is invalid")
        if item["status"] in {"confirmed_current", "changed", "redirected"} and (item["body_digest"] is None or not item["bounded_extracts"]):
            raise ValueError("source refresh lacks bounded extract evidence")
        redirect_with_change = item["status"] == "redirected" and source["requested_url"] != item["canonical_url"]
        changed_claims = _changed_extract_claims(source, item["bounded_extracts"])
        if item["status"] in {"confirmed_current", "changed", "redirected"} and changed_claims and (item["status"] != "changed" and not redirect_with_change or not changed_claims <= set(item["invalidated_claim_ids"])):
            raise ValueError("changed bounded extracts must invalidate dependent claims")
        if item["status"] in {"inaccessible", "withdrawn", "conflicting"} and set(item["invalidated_claim_ids"]) != set(bindings):
            raise ValueError("adverse source outcome must invalidate every bound claim")
        if item["status"] in {"confirmed_current", "changed", "redirected"}:
            prior_body = f"sha256:{source['body_sha256']}"; expected_status = "redirected" if source["requested_url"] != item["canonical_url"] else "changed" if canonical_changed else "confirmed_current" if item["body_digest"] == prior_body else "changed"
            if item["status"] != expected_status: raise ValueError("source refresh status is inconsistent with captured evidence")
        evidence = {"canonical_url": item["canonical_url"], "retrieved_at": item["retrieved_at"], "body_digest": item["body_digest"], "bounded_extracts": item["bounded_extracts"]}
        if item["retrieval_evidence_digest"] != digest(evidence): raise ValueError("source retrieval evidence digest is invalid")
    capture_digests = {row["source_capture_digest"] for row in refreshes}
    if len(capture_digests) != 1:
        raise ValueError("source refreshes must bind one complete raw source capture")
    invalidated = sorted({claim for row in refreshes for claim in row["invalidated_claim_ids"]})
    return {"count": 22, "invalidated_claim_ids": invalidated, "digest": digest(refreshes), "sanitized_refreshes": refreshes}


def validate_source_refreshes(manifest, refreshes, *, allow_synthetic_manifest=False):
    raw_keys = {"official_source_ledger_id", "requested_url", "canonical_url", "retrieved_at", "body_digest", "status", "retrieved_body_b64", "source_capture_digest", "bounded_extracts", "retrieval_evidence_digest", "documented_facts", "claim_bindings", "invalidated_claim_ids", "prior_record_digest"}
    for item in refreshes:
        if set(item) != raw_keys: raise ValueError("source refresh must retain the closed raw evidence binding")
        body_bytes = _validated_body(item["retrieved_body_b64"], item["bounded_extracts"], item.get("official_source_ledger_id"))
        if item["body_digest"] is None and body_bytes is not None or item["body_digest"] is not None and (body_bytes is None or item["body_digest"] != digest(body_bytes)):
            raise ValueError("source body digest does not match captured evidence")
    sanitized = [{key: item[key] for key in item if key != "retrieved_body_b64"} for item in refreshes]
    return validate_published_source_refreshes(manifest, sanitized, allow_synthetic_manifest=allow_synthetic_manifest)


def build_client_identity(payload):
    keys = ("reported_version", "build_identifier_kind", "build_identifier", "distribution")
    if not isinstance(payload, dict) or set(payload) not in (set(keys), {*keys, "client_identity_id"}):
        raise ValueError("client identity must use the closed v1 shape")
    clean = {key: payload.get(key) for key in keys}
    if any(not value for value in clean.values()) or clean["build_identifier_kind"] not in {"vendor_build_id", "executable_sha256", "package_sha256"}:
        raise ValueError("client identity is incomplete or unsupported")
    _safe_sanitized_value(clean)
    identity = {"client_identity_id": digest(clean), **clean}
    if not _token(clean["distribution"]) or not _LABEL.fullmatch(str(clean["reported_version"])):
        raise ValueError("client version or distribution is invalid")
    if clean["build_identifier_kind"] == "vendor_build_id" and not _IDENTIFIER.fullmatch(str(clean["build_identifier"])):
        raise ValueError("vendor build identifier is invalid")
    if clean["build_identifier_kind"] != "vendor_build_id" and not _DIGEST.fullmatch(str(clean["build_identifier"])):
        raise ValueError("client distribution or immutable build identifier is invalid")
    if payload.get("client_identity_id", identity["client_identity_id"]) != identity["client_identity_id"]:
        raise ValueError("client_identity_id does not match its canonical payload")
    return identity


def build_repository_binding(revision, tree_object):
    if not _GIT_OBJECT.fullmatch(str(revision)) or not _GIT_OBJECT.fullmatch(str(tree_object)):
        raise ValueError("repository revision and tree object must be immutable Git object IDs")
    payload = {
        "revision": revision,
        "tree_object": tree_object,
        "tree_digest": digest({"git_tree_object": tree_object}),
        "evidence_ref": f"git-object://{revision}/{tree_object}",
    }
    return {"repository_binding_id": digest(payload), **payload}


def validate_repository_binding(binding):
    keys = {"repository_binding_id", "revision", "tree_object", "tree_digest", "evidence_ref"}
    if not isinstance(binding, dict) or set(binding) != keys:
        raise ValueError("repository binding must use the closed v1 shape")
    expected = build_repository_binding(binding["revision"], binding["tree_object"])
    if binding != expected:
        raise ValueError("repository binding does not match its revision and tree evidence")
    return binding


def repository_binding_from_checkout(repository_root):
    def status():
        completed = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=repository_root, capture_output=True, text=True, timeout=5,
            check=False,
        )
        if completed.returncode:
            raise ValueError("active checkout cleanliness is unavailable")
        return completed.stdout

    if status():
        raise ValueError("active checkout must be clean before collection")
    values = []
    for revision in ("HEAD",):
        completed = subprocess.run(
            ["git", "rev-parse", revision], cwd=repository_root, capture_output=True,
            text=True, timeout=5, check=False,
        )
        value = completed.stdout.strip()
        if completed.returncode or not _GIT_OBJECT.fullmatch(value):
            raise ValueError("active checkout revision/tree binding is unavailable")
        values.append(value)
    resolved_revision = values[0]
    completed = subprocess.run(
        ["git", "rev-parse", f"{resolved_revision}^{{tree}}"], cwd=repository_root,
        capture_output=True, text=True, timeout=5, check=False,
    )
    tree_object = completed.stdout.strip()
    if completed.returncode or not _GIT_OBJECT.fullmatch(tree_object):
        raise ValueError("active checkout revision/tree binding is unavailable")
    values.append(tree_object)
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repository_root, capture_output=True,
        text=True, timeout=5, check=False,
    )
    if completed.returncode or completed.stdout.strip() != resolved_revision:
        raise ValueError("active checkout changed during collection binding")
    if status():
        raise ValueError("active checkout changed during collection binding")
    return build_repository_binding(*values)


def validate_work_item(work_item):
    if not isinstance(work_item, dict) or set(work_item) != {"kind", "id"} or work_item.get("kind") not in {"task", "fixture", "objective"} or not _WORK_ITEM_ID.fullmatch(str(work_item.get("id"))):
        raise ValueError("work item must use the closed task/fixture/objective shape")
    return work_item


def _safe_sanitized_value(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower()
            sensitive = any(part in lowered for part in _FORBIDDEN_KEY_PARTS)
            if sensitive and not (isinstance(nested, str) and nested.startswith("fixture-")):
                raise ValueError("sanitized output contains a forbidden sensitive field")
            _safe_sanitized_value(nested)
    elif isinstance(value, list):
        for nested in value: _safe_sanitized_value(nested)
    elif isinstance(value, str) and (value.startswith(("/", "\\")) or "://" in value or re.match(r"^[A-Za-z]:[\\/]", value)):
        raise ValueError("sanitized output contains a path or remote locator")


def sanitize(record, profile):
    if profile not in _SANITIZER_PROFILES or not isinstance(record, dict):
        raise ValueError("sanitizer profile is unknown")
    allowlist, pseudonym_fields, strict = _SANITIZER_PROFILES[profile]
    if strict and set(record) - set(allowlist): raise ValueError("surface entry contains undeclared fields")
    result = {}
    for key in sorted(set(record) & set(allowlist)):
        value = record[key]
        result[key] = f"fixture-{key}" if key in pseudonym_fields else value
    _safe_sanitized_value(result)
    return result


def _clean_entry(raw):
    raw = sanitize(raw, "surface_entry")
    if not {"model", "effort", "available", "hidden"} <= set(raw):
        raise ValueError("surface entry contains undeclared or missing fields")
    if not isinstance(raw["model"], str) or not _LABEL.fullmatch(raw["model"]) or not _token(raw["effort"]):
        raise ValueError("surface entry model or effort is invalid")
    if not isinstance(raw["available"], bool) or not isinstance(raw["hidden"], bool):
        raise ValueError("surface entry availability fields must be boolean")
    if "machine_id" in raw and not _token(raw["machine_id"]): raise ValueError("surface entry machine identifier is invalid")
    if "raw_label" in raw and (not isinstance(raw["raw_label"], str) or not _LABEL.fullmatch(raw["raw_label"])): raise ValueError("surface entry raw label is invalid")
    if "capabilities" in raw and (not isinstance(raw["capabilities"], list) or not all(_token(value) for value in raw["capabilities"])):
        raise ValueError("surface entry capabilities are invalid")
    return {key: raw[key] for key in sorted(raw)}


def _observation_payload(observation):
    return {key: observation[key] for key in sorted(_OBSERVATION_KEYS - {"surface_observation_id"})}


def _unknown_capture_record(surface, client_identity_id, repository_binding, work_item, captured_at):
    repository = validate_repository_binding(repository_binding); work_item = validate_work_item(work_item)
    if surface not in SURFACES or not _DIGEST.fullmatch(str(client_identity_id)) or not _utc_timestamp(captured_at):
        raise ValueError("unknown capture binding is invalid")
    return {
        "schema_version": SCHEMA_VERSION, "surface": surface, "client_identity_id": client_identity_id,
        "repository_binding_id": repository["repository_binding_id"], "work_item": work_item,
        "collection_method_id": "unknown-observation-v1", "outcome": "no_approved_live_collector",
        "captured_at": captured_at,
    }


def _collection_authority(observation):
    repository = validate_repository_binding(observation["repository_binding"])
    work_item = validate_work_item(observation["work_item"])
    shared = {"repository_binding_id": repository["repository_binding_id"], "work_item": work_item}
    method = observation["collection_method_id"]
    if method == "fixture-enumeration-v1":
        expected = digest({"include_hidden": observation["surface"] == "app_server", **shared})
        authority = "synthetic"
    elif method == "unknown-observation-v1":
        expected = digest({"reason": "no_approved_live_collector", "surface": observation["surface"], **shared})
        authority = "non_authoritative"
        if observation["completeness_state"] != "unknown" or observation["entries"]:
            raise ValueError("unknown observation method cannot carry discovered entries")
    else:
        raise ValueError("collection method is not in the closed registry")
    if observation["method_inputs_digest"] != expected:
        raise ValueError("collection method inputs do not match the closed registry")
    return authority


def validate_observation(observation):
    if not isinstance(observation, dict) or set(observation) != _OBSERVATION_KEYS:
        raise ValueError("surface observation must use the closed v1 shape")
    if observation["surface"] not in SURFACES or observation["completeness_state"] not in {"complete", "partial", "unavailable", "unknown"}:
        raise ValueError("unsupported surface observation")
    expected_visibility = {"complete_enumeration": observation["completeness_state"] == "complete"} if observation["surface"] == "interactive_picker" else None
    if observation["visibility_policy"] != expected_visibility:
        raise ValueError("surface collection or visibility policy is invalid")
    if not _utc_timestamp(observation["started_at"]) or not _utc_timestamp(observation["completed_at"]):
        raise ValueError("collection timestamp must be RFC3339 UTC")
    if datetime.fromisoformat(observation["started_at"].replace("Z", "+00:00")) > datetime.fromisoformat(observation["completed_at"].replace("Z", "+00:00")):
        raise ValueError("collection window is reversed")
    for field in ("client_identity_id", "method_inputs_digest", "raw_evidence_digest"):
        _need_digest(observation[field], field)
    if observation["sanitized_evidence_digest"] is not None:
        _need_digest(observation["sanitized_evidence_digest"], "sanitized_evidence_digest")
    if not _RAW_REF.fullmatch(str(observation["raw_evidence_ref"])):
        raise ValueError("raw evidence reference must be content addressed")
    if observation["raw_evidence_ref"] != f"raw://{observation['raw_evidence_digest']}":
        raise ValueError("raw_evidence_ref must match raw_evidence_digest")
    observation["entries"] = [_clean_entry(item) for item in observation["entries"]]
    _collection_authority(observation)
    if observation["collection_method_id"] == "unknown-observation-v1":
        if observation["started_at"] != observation["completed_at"]:
            raise ValueError("unknown observation must use one capture timestamp")
        record = _unknown_capture_record(
            observation["surface"], observation["client_identity_id"], observation["repository_binding"],
            observation["work_item"], observation["started_at"],
        )
        expected_evidence = digest(canonical_bytes(record) + b"\n")
        if observation["raw_evidence_digest"] != expected_evidence or observation["sanitized_evidence_digest"] != expected_evidence:
            raise ValueError("unknown observation evidence does not match its deterministic attempt record")
    if observation["surface_observation_id"] != digest(_observation_payload(observation)):
        raise ValueError("surface observation identity does not match its canonical payload")
    return observation


def fixture_observation(surface, payload, client_identity_id):
    state, entries = payload.get("state", "unknown"), [_clean_entry(item) for item in payload.get("entries", [])]
    if surface not in SURFACES or state not in {"complete", "partial", "unavailable", "unknown"}:
        raise ValueError("unsupported surface observation")
    repository = validate_repository_binding(payload.get("repository_binding", build_repository_binding("0" * 40, "0" * 40)))
    work_item = validate_work_item(payload.get("work_item", {"kind": "fixture", "id": "G56R-002-SYNTHETIC"}))
    evidence = digest({"surface": surface, "state": state, "entries": entries})
    result = {
        "client_identity_id": client_identity_id, "surface": surface,
        "collection_method_id": "fixture-enumeration-v1", "method_inputs_digest": digest({"include_hidden": surface == "app_server", "repository_binding_id": repository["repository_binding_id"], "work_item": work_item}),
        "started_at": "2026-07-16T00:00:00Z", "completed_at": "2026-07-16T00:00:00Z", "completeness_state": state,
        "visibility_policy": {"complete_enumeration": state == "complete"} if surface == "interactive_picker" else None,
        "entries": entries, "raw_evidence_digest": evidence, "raw_evidence_ref": f"raw://{evidence}", "sanitized_evidence_digest": evidence,
        "repository_binding": repository, "work_item": work_item,
    }
    result["surface_observation_id"] = digest(result)
    return validate_observation(result)


def unknown_observation(surface, client_identity_id, repository_binding, work_item, *, raw_evidence_digest=None, captured_at="2026-07-16T00:00:00Z"):
    repository = validate_repository_binding(repository_binding); work_item = validate_work_item(work_item)
    if not _utc_timestamp(captured_at): raise ValueError("unknown observation timestamp must be RFC3339 UTC")
    evidence = digest(canonical_bytes(_unknown_capture_record(surface, client_identity_id, repository, work_item, captured_at)) + b"\n")
    if raw_evidence_digest is not None and raw_evidence_digest != evidence:
        raise ValueError("unknown observation raw evidence does not match its attempt record")
    _need_digest(evidence, "raw_evidence_digest")
    result = {
        "client_identity_id": client_identity_id, "surface": surface,
        "collection_method_id": "unknown-observation-v1",
        "method_inputs_digest": digest({"reason": "no_approved_live_collector", "surface": surface, "repository_binding_id": repository["repository_binding_id"], "work_item": work_item}),
        "started_at": captured_at, "completed_at": captured_at,
        "completeness_state": "unknown", "visibility_policy": {"complete_enumeration": False} if surface == "interactive_picker" else None,
        "entries": [], "raw_evidence_digest": evidence, "raw_evidence_ref": f"raw://{evidence}", "sanitized_evidence_digest": evidence,
        "repository_binding": repository, "work_item": work_item,
    }
    result["surface_observation_id"] = digest(result)
    return validate_observation(result)


def _candidate_tuples(manifest, validation, *, allow_synthetic_manifest=False):
    authority = validate_manifest(manifest, allow_synthetic_manifest=allow_synthetic_manifest)
    refreshes = validation["sanitized_refreshes"]
    sources = {row["official_source_ledger_id"]: row for row in manifest["official_source_ledger"]}; current_ids = set(sources)
    contracts = {row["agent_contract_id"]: row for row in manifest.get("agent_contracts", [])}; effort_records = {row["effort_surface_record_id"]: row for row in manifest["effort_surface_records"]}
    refresh_by_source = {row["official_source_ledger_id"]: row for row in validation["sanitized_refreshes"]}
    efforts_by_record = authority["authoritative_effort_tokens_by_record"]
    route_dependencies = {route["candidate_route_id"]: _route_claim_dependencies(route, sources) for route in manifest.get("candidate_routes", [])}
    def source_adverse_for_route(row, route):
        invalid = set(row["invalidated_claim_ids"])
        dependencies = route_dependencies[route["candidate_route_id"]][row["official_source_ledger_id"]]
        return row["status"] in {"inaccessible", "withdrawn", "conflicting"} or bool(invalid & dependencies)

    tuples = []
    for route in manifest.get("candidate_routes", []):
        model = route.get("model_selector", {}).get("requested_value"); effort = route.get("effort_selector", {}).get("requested_value")
        source_ids = route.get("official_source_ledger_ids", []); reasons = []
        adverse_source_ids = {
            source_id for source_id in source_ids
            if source_adverse_for_route(refresh_by_source[source_id], route)
        }
        if not _token(model) or not source_ids or not set(source_ids) <= current_ids or adverse_source_ids:
            reasons.append("source_not_admitted")
        bound_records = [effort_records[record_id] for record_id in route.get("effort_surface_record_ids", [])]
        supporting = [row for row in bound_records if effort in efforts_by_record.get(row["effort_surface_record_id"], [])]
        valid_supporting = [row for row in supporting if row["official_source_ledger_id"] in set(source_ids) and not source_adverse_for_route(refresh_by_source[row["official_source_ledger_id"]], route)]
        if not _token(effort) or not supporting:
            reasons.append("effort_not_source_admitted")
        elif not valid_supporting: reasons.append("effort_source_not_admitted")
        contract = contracts[route["agent_contract_id"]]
        tuples.append({"candidate_route_id": route["candidate_route_id"], "agent_contract_id": route["agent_contract_id"],
                       "named_agent": contract["agent_name"], "model": model, "effort": effort,
                       "candidate_route_digest": digest(route), "source_ref": contract["source_ref"],
                       "source_sha256": f"sha256:{contract['source_sha256']}", "instruction_sha256": f"sha256:{contract['instruction_sha256']}",
                       "role_instruction_sha256": f"sha256:{route['role_instruction_sha256']}", "agent_contract_digest": digest(contract),
                       "official_source_bindings": [{"official_source_ledger_id": source_id, "source_refresh_digest": digest(refresh_by_source[source_id])} for source_id in sorted(source_ids)],
                       "effort_surface_bindings": sorted(({"effort_surface_record_id": row["effort_surface_record_id"], "effort_surface_record_digest": digest(row), "official_source_ledger_id": row["official_source_ledger_id"], "source_refresh_digest": digest(refresh_by_source[row["official_source_ledger_id"]])} for row in bound_records), key=lambda row: row["effort_surface_record_id"]),
                       "source_admitted": not reasons, "authority_reasons": reasons})
    return _AuthorityTupleSet(tuples)


def candidate_tuples_from_manifest(manifest, refreshes, *, allow_synthetic_manifest=False):
    validation = validate_source_refreshes(manifest, refreshes, allow_synthetic_manifest=allow_synthetic_manifest)
    return _candidate_tuples(manifest, validation, allow_synthetic_manifest=allow_synthetic_manifest)


def candidate_tuples_from_published(manifest, refreshes):
    return _candidate_tuples(manifest, validate_published_source_refreshes(manifest, refreshes))


def _surface_disagreements(indexed, observations_by_surface):
    disagreements = {}
    for key in sorted({key for entries in indexed.values() for key in entries}):
        values = {surface: indexed[surface].get(key) for surface in SURFACES}
        observed = [value for value in values.values() if value is not None]
        availability = {value["available"] for value in observed}
        hidden = {value["hidden"] for value in observed}
        disagreement_class = "hidden_state" if len(hidden) > 1 else "availability" if len(availability) > 1 else None
        if disagreement_class is None:
            continue
        tuple_value = {"model": key[0], "effort": key[1]}
        disagreements[key] = {
            "canonical_tuple": tuple_value,
            "surface_values": values,
            "evidence_refs": {surface: observations_by_surface[surface]["raw_evidence_ref"] for surface in SURFACES},
            "proposed_normalized_key": tuple_value,
            "disagreement_class": disagreement_class,
            "tuple_disposition": "excluded",
        }
    return disagreements


def _surface_index_and_invalidity(observations, normalization_map, normalization_map_id, aggregate_integrity_digest):
    reasons = []
    if len({item["client_identity_id"] for item in observations}) != 1:
        reasons.append("unprovable_shared_client_identity")
    canonical_aliases = [item["canonical_model_id"] for item in normalization_map.values()]
    if len(canonical_aliases) != len(set(canonical_aliases)):
        reasons.append("ambiguous_or_duplicate_normalization_key")
    indexed = {}
    for observation in observations:
        entries = {}
        for raw in observation["entries"]:
            alias = normalization_map.get(raw["model"])
            if alias is not None and "machine_id" in raw and raw["machine_id"] != alias["canonical_model_id"]:
                reasons.append("ambiguous_or_duplicate_normalization_key")
                continue
            key = (alias["canonical_model_id"] if alias is not None else raw["model"], raw["effort"])
            if not all(_token(value) for value in key) or key in entries:
                reasons.append("ambiguous_or_duplicate_normalization_key")
            entries[key] = raw
        indexed[observation["surface"]] = entries
    actual_integrity = digest({"observations": observations, "normalization_map_id": normalization_map_id})
    if aggregate_integrity_digest != actual_integrity:
        reasons.append("aggregate_hash_mismatch")
    return indexed, list(dict.fromkeys(reasons)), actual_integrity


def evaluate_surface_matrix(observations, source_tuples, *, aliases=None, expected_integrity_digest=_UNSET):
    if any(row.get("source_admitted") for row in source_tuples) and not isinstance(source_tuples, _AuthorityTupleSet):
        raise ValueError("source admission requires a manifest-bound tuple set")
    aliases = aliases or {}; observations = [validate_observation(dict(item)) for item in observations]
    surfaces = [item["surface"] for item in observations]
    if len(observations) != 3 or set(surfaces) != set(SURFACES) or len(set(surfaces)) != 3:
        raise ValueError("matrix requires exactly one observation per surface")
    observations_by_surface = {item["surface"]: item for item in observations}
    observations = [observations_by_surface[surface] for surface in SURFACES]
    clients = {item["client_identity_id"] for item in observations}
    repository_ids = {item["repository_binding"]["repository_binding_id"] for item in observations}; work_items = {canonical_bytes(item["work_item"]) for item in observations}
    if len(repository_ids) != 1 or len(work_items) != 1: raise ValueError("surface observations must share repository and work-item bindings")
    collection_authorities = [_collection_authority(item) for item in observations]
    normalized_aliases = {}; observations_by_surface = {item["surface"]: item for item in observations}
    for raw_label, alias in aliases.items():
        required = {"canonical_model_id", "authority_kind", "authority_surface"}; enriched = required | {"client_identity_id", "authority_evidence_ref"}
        if not isinstance(raw_label, str) or not _LABEL.fullmatch(raw_label) or not isinstance(alias, dict) or set(alias) != required and set(alias) != enriched:
            raise ValueError("alias authority must use the closed pinned-build shape")
        canonical, surface = alias["canonical_model_id"], alias["authority_surface"]
        if not _token(canonical) or alias["authority_kind"] != "machine_readable_identifier" or surface not in SURFACES:
            raise ValueError("alias authority is unsupported")
        observation = observations_by_surface[surface]
        evidence = [entry for entry in observation["entries"] if entry["model"] == raw_label and entry.get("raw_label") == raw_label and entry.get("machine_id") == canonical]
        if len(evidence) != 1: raise ValueError("alias authority evidence is absent")
        expected_alias = {"canonical_model_id": canonical, "authority_kind": "machine_readable_identifier", "authority_surface": surface,
                          "client_identity_id": observation["client_identity_id"], "authority_evidence_ref": observation["raw_evidence_ref"]}
        if set(alias) == enriched and alias != expected_alias: raise ValueError("alias authority does not match the pinned-build evidence")
        normalized_aliases[raw_label] = expected_alias
    authority_keys = {"candidate_route_digest", "source_ref", "source_sha256", "instruction_sha256", "role_instruction_sha256", "agent_contract_digest", "official_source_bindings", "effort_surface_bindings"}
    if any(row.get("source_admitted") and (not authority_keys <= set(row) or not row["official_source_bindings"] or not row["effort_surface_bindings"]) for row in source_tuples):
        raise ValueError("source admission requires complete tuple authority")
    normalization = digest(normalized_aliases)
    actual_integrity = digest({"observations": observations, "normalization_map_id": normalization})
    if expected_integrity_digest is _UNSET:
        integrity = actual_integrity
    else:
        _need_digest(expected_integrity_digest, "expected_integrity_digest")
        integrity = expected_integrity_digest
    indexed, reasons, _ = _surface_index_and_invalidity(observations, normalized_aliases, normalization, integrity)
    decisions = []
    disagreements_by_key = _surface_disagreements(indexed, observations_by_surface)
    disagreements = [disagreements_by_key[key] for key in sorted(disagreements_by_key)]
    sources = list(source_tuples); source_keys = {(row.get("model"), row.get("effort")) for row in sources}
    observed_keys = {key for entries in indexed.values() for key in entries}
    for key in sorted(observed_keys - source_keys):
        suffix = digest({"model": key[0], "effort": key[1]})[7:23]
        sources.append({"candidate_route_id": f"runtime-only:{suffix}", "agent_contract_id": "unbound-runtime-observation",
                        "named_agent": "unbound-runtime-observation", "model": key[0], "effort": key[1],
                        "candidate_route_digest": digest({"runtime_only": key}), "source_ref": "runtime-only-observation",
                        "source_sha256": digest({"runtime_only": "source"}), "instruction_sha256": digest({"runtime_only": "instruction"}),
                        "role_instruction_sha256": digest({"runtime_only": "instruction"}), "agent_contract_digest": digest({"runtime_only": "contract"}),
                        "official_source_bindings": [], "effort_surface_bindings": [],
                        "source_admitted": False, "authority_reasons": ["source_not_admitted"]})
    complete = all(item["completeness_state"] == "complete" for item in observations); collection_authoritative = all(item == "approved_live" for item in collection_authorities)
    for source in sources:
        key = (source.get("model"), source.get("effort")); values = {surface: indexed[surface].get(key) for surface in SURFACES}
        observed = [value for value in values.values() if value is not None]; availability = {value["available"] for value in observed}; hidden = {value["hidden"] for value in observed}
        picker_omission = values["interactive_picker"] is None and values["app_server"] is not None and values["cli"] is not None and values["app_server"]["hidden"] and values["cli"]["hidden"] and next(item for item in observations if item["surface"] == "interactive_picker")["visibility_policy"] == {"complete_enumeration": True}
        why = list(source.get("authority_reasons", [])) if not source.get("source_admitted") else []
        if reasons: disposition, surface_why = "unknown", ["matrix_invalid"]
        elif key[1] is None: disposition, surface_why = "unknown", ["canonical_effort_unknown"]
        elif key in disagreements_by_key:
            disposition = "disagreed"
            surface_why = ["hidden_state_disagreement" if disagreements_by_key[key]["disagreement_class"] == "hidden_state" else "surface_disagreement"]
        elif not complete or len(observed) != 3 and not picker_omission: disposition, surface_why = "unknown", ["surface_evidence_incomplete"]
        elif availability == {True}: disposition, surface_why = "agreed", []
        else: disposition, surface_why = "agreed", ["availability_not_proven"]
        why.extend(item for item in surface_why if item not in why)
        if not collection_authoritative and "collection_evidence_non_authoritative" not in why: why.append("collection_evidence_non_authoritative")
        included = source.get("source_admitted") and disposition == "agreed" and availability == {True} and collection_authoritative
        disagreement = disagreements_by_key.get(key)
        decisions.append({"candidate_route_id": source["candidate_route_id"], "agent_contract_id": source["agent_contract_id"], "named_agent": source["named_agent"],
                          "canonical_model_id": key[0], "canonical_effort": key[1], "source_admitted": bool(source.get("source_admitted")),
                          "candidate_route_digest": source["candidate_route_digest"], "source_ref": source["source_ref"],
                          "source_sha256": source["source_sha256"], "instruction_sha256": source["instruction_sha256"], "role_instruction_sha256": source["role_instruction_sha256"],
                          "agent_contract_digest": source["agent_contract_digest"], "official_source_bindings": list(source["official_source_bindings"]), "effort_surface_bindings": list(source["effort_surface_bindings"]),
                          "runtime_capability_snapshot_id": None,
                          "surface_evidence": {item["surface"]: {"surface_observation_id": item["surface_observation_id"], "completeness_state": item["completeness_state"], "visibility_policy": item["visibility_policy"], "raw_evidence_digest": item["raw_evidence_digest"], "raw_evidence_ref": item["raw_evidence_ref"], "matching_entry": values[item["surface"]]} for item in observations},
                          "hidden_state": {surface: values[surface]["hidden"] if values[surface] is not None else None for surface in SURFACES},
                          "normalization_map_id": normalization, "disagreement_digest": digest(disagreement) if disagreement else None,
                          "exact_treatment_readiness": "pending" if included else "not_ready_excluded",
                          "source_admission_reasons": list(source.get("authority_reasons", [])),
                          "availability_disposition": "supported" if included else "unknown", "surface_disposition": disposition,
                          "decision": "included" if included else "excluded", "reasons": why})
    payload = {"schema_version": SCHEMA_VERSION, "client_identity_id": next(iter(clients)) if len(clients) == 1 else digest({"invalid": "client_identity"}),
               "repository_binding_id": next(iter(repository_ids)), "work_item": observations[0]["work_item"],
               "observations": observations, "normalization_map": normalized_aliases, "normalization_map_id": normalization, "disagreements": disagreements,
               "aggregate_integrity_digest": integrity, "validity": "invalid" if reasons else "valid", "invalidity_reasons": reasons}
    matrix_id = digest(payload)
    for decision in decisions: decision["surface_matrix_id"] = matrix_id
    return {"surface_matrix_id": matrix_id, **payload}, _BoundDecisionSet(decisions)


def validate_surface_matrix(matrix):
    required = {"surface_matrix_id", "schema_version", "client_identity_id", "repository_binding_id", "work_item", "observations", "normalization_map", "normalization_map_id", "disagreements", "aggregate_integrity_digest", "validity", "invalidity_reasons"}
    if set(matrix) != required or matrix.get("schema_version") != SCHEMA_VERSION: raise ValueError("surface matrix must use the closed v1 shape")
    observations = [validate_observation(dict(item)) for item in matrix["observations"]]
    surfaces = [item["surface"] for item in observations]
    if len(observations) != 3 or set(surfaces) != set(SURFACES) or len(set(surfaces)) != 3: raise ValueError("matrix requires exactly one observation per surface")
    by_surface = {item["surface"]: item for item in observations}; observations = [by_surface[surface] for surface in SURFACES]
    matrix = {**matrix, "observations": observations}
    clients = {item["client_identity_id"] for item in observations}
    expected_client_identity = next(iter(clients)) if len(clients) == 1 else digest({"invalid": "client_identity"})
    if matrix["client_identity_id"] != expected_client_identity: raise ValueError("matrix client identity mismatch")
    validate_work_item(matrix["work_item"])
    if any(item["repository_binding"]["repository_binding_id"] != matrix["repository_binding_id"] or item["work_item"] != matrix["work_item"] for item in observations): raise ValueError("matrix repository or work-item binding mismatch")
    observations_by_surface = {item["surface"]: item for item in observations}
    alias_keys = {"canonical_model_id", "authority_kind", "authority_surface", "client_identity_id", "authority_evidence_ref"}
    for raw_label, alias in matrix["normalization_map"].items():
        if not _LABEL.fullmatch(str(raw_label)) or not isinstance(alias, dict) or set(alias) != alias_keys or not _token(alias["canonical_model_id"]) or alias["authority_kind"] != "machine_readable_identifier" or alias["authority_surface"] not in SURFACES:
            raise ValueError("normalization map alias authority is invalid")
        observation = observations_by_surface[alias["authority_surface"]]
        evidence = [item for item in observation["entries"] if item["model"] == raw_label and item.get("raw_label") == raw_label and item.get("machine_id") == alias["canonical_model_id"]]
        if alias["client_identity_id"] != observation["client_identity_id"] or alias["authority_evidence_ref"] != observation["raw_evidence_ref"] or len(evidence) != 1:
            raise ValueError("normalization map alias authority is not bound to the pinned build")
    if matrix["normalization_map_id"] != digest(matrix["normalization_map"]): raise ValueError("normalization map identity mismatch")
    _need_digest(matrix["aggregate_integrity_digest"], "aggregate_integrity_digest")
    indexed, expected_invalidity_reasons, _ = _surface_index_and_invalidity(
        observations, matrix["normalization_map"], matrix["normalization_map_id"], matrix["aggregate_integrity_digest"],
    )
    if matrix["validity"] not in {"valid", "invalid"} or matrix["invalidity_reasons"] != expected_invalidity_reasons or (matrix["validity"] == "invalid") != bool(expected_invalidity_reasons):
        raise ValueError("surface matrix validity is inconsistent")
    expected_disagreements = _surface_disagreements(indexed, observations_by_surface)
    actual_disagreements = {}
    for item in matrix["disagreements"]:
        keys = {"canonical_tuple", "surface_values", "evidence_refs", "proposed_normalized_key", "disagreement_class", "tuple_disposition"}
        tuple_value = item.get("canonical_tuple", {}) if isinstance(item, dict) else {}
        tuple_key = (tuple_value.get("model"), tuple_value.get("effort"))
        if set(item) != keys or set(tuple_value) != {"model", "effort"} or not all(_token(value) for value in tuple_key) or tuple_key in actual_disagreements:
            raise ValueError("surface disagreement must use unique canonical tuple keys")
        if item != expected_disagreements.get(tuple_key):
            raise ValueError("surface disagreement is inconsistent with observed values")
        actual_disagreements[tuple_key] = item
    if set(actual_disagreements) != set(expected_disagreements):
        raise ValueError("surface disagreement inventory is incomplete")
    if matrix["surface_matrix_id"] != digest({key: matrix[key] for key in matrix if key != "surface_matrix_id"}):
        raise ValueError("surface matrix identity does not match its canonical payload")
    return matrix


def _validated_canary_approvals(approvals):
    keys = {"executor_contract_id", "contract_version", "implementation_digest", "platform", "approval_evidence_digest"}; identities = []
    for item in approvals:
        if not isinstance(item, dict) or set(item) != keys or item["contract_version"] != SCHEMA_VERSION or item["platform"] not in {"macos", "linux", "windows"}:
            raise ValueError("canary approval must use the closed repository-owned shape")
        for field in ("executor_contract_id", "implementation_digest", "approval_evidence_digest"): _need_digest(item[field], field)
        identities.append((item["executor_contract_id"], item["implementation_digest"]))
    if len(identities) != len(set(identities)): raise ValueError("canary approvals must be unique")
    return approvals


def _canary_evidence_payload(result):
    return {
        "schema_version": SCHEMA_VERSION,
        "snapshot_id": result["snapshot_id"],
        "canonical_model_id": result["canonical_model_id"],
        "canonical_effort": result["canonical_effort"],
        "terminal_class": result["terminal_class"],
        "exit_code": result["exit_code"],
        "sentinel_observed": result["sentinel_observed"],
    }


def _validate_canary_result_envelope(result, approvals=APPROVED_CANARY_EXECUTORS, *, evidence_bytes=None):
    required = {"snapshot_id", "canonical_model_id", "canonical_effort", "attempt_index", "timeout_seconds", "combined_output_cap_bytes", "executor_contract_id", "implementation_digest", "executor_result_digest", "contract_version", "platform", "timeout_enforced", "output_cap_enforced", "process_tree_termination_state", "retry_count", "exit_code", "sentinel_observed", "terminal_class", "availability_disposition", "evidence_digest"}
    if set(result) != required:
        raise ValueError("canary result must use the closed v1 envelope")
    for field in ("snapshot_id", "executor_contract_id", "implementation_digest", "executor_result_digest", "evidence_digest"):
        _need_digest(result[field], field)
    if not _token(result["canonical_model_id"]) or not _token(result["canonical_effort"]) or result["platform"] not in {"macos", "linux", "windows"}:
        raise ValueError("canary tuple or platform identity is invalid")
    bound_result = {key: result[key] for key in result if key not in {"executor_result_digest", "availability_disposition"}}
    if result["executor_result_digest"] != digest(bound_result): raise ValueError("canary result digest does not bind the closed result envelope")
    integer_fields = ("attempt_index", "timeout_seconds", "combined_output_cap_bytes", "retry_count")
    if any(type(result[field]) is not int for field in integer_fields) or type(result["timeout_enforced"]) is not bool or type(result["output_cap_enforced"]) is not bool or type(result["sentinel_observed"]) is not bool or result["exit_code"] is not None and type(result["exit_code"]) is not int:
        raise ValueError("canary result uses invalid primitive types")
    fixed = result["attempt_index"], result["timeout_seconds"], result["combined_output_cap_bytes"], result["contract_version"], result["retry_count"]
    if fixed != (1, 30, 65536, SCHEMA_VERSION, 0) or not result["timeout_enforced"] or not result["output_cap_enforced"]:
        raise ValueError("canary bounds or retry contract violated")
    if result["terminal_class"] not in ("success", *ERROR_TERMINALS) or result["process_tree_termination_state"] not in {"not_needed", "completed", "failed"}:
        raise ValueError("unknown canary state")
    if result["terminal_class"] in {"timeout", "output_cap_exceeded"} and result["process_tree_termination_state"] == "not_needed":
        raise ValueError("bounded canary termination requires process-tree cleanup")
    if evidence_bytes is not None:
        if not isinstance(evidence_bytes, bytes) or digest(evidence_bytes) != result["evidence_digest"]:
            raise ValueError("canary evidence bytes do not match evidence_digest")
        evidence = _parse_json_bytes(evidence_bytes)
        if evidence_bytes != canonical_bytes(evidence) + b"\n" or evidence != _canary_evidence_payload(result):
            raise ValueError("canary evidence must use the canonical closed redacted schema")
    approvals = _validated_canary_approvals(approvals); approval = next((item for item in approvals if item["executor_contract_id"] == result["executor_contract_id"] and item["implementation_digest"] == result["implementation_digest"]), None)
    if approval is not None and approval["platform"] != result["platform"]:
        raise ValueError("canary executor platform does not match its repository approval")
    success = approval and approval.get("implementation_digest") == result["implementation_digest"] and result["terminal_class"] == "success" and result["exit_code"] == 0 and result["sentinel_observed"] and result["process_tree_termination_state"] != "failed"
    return {**result, "availability_disposition": "available_for_pinned_environment" if success else "unknown"}


def validate_canary_result(result, approvals=APPROVED_CANARY_EXECUTORS, *, evidence_bytes):
    if evidence_bytes is None:
        raise ValueError("canary result requires its content-addressed redacted evidence")
    return _validate_canary_result_envelope(result, approvals, evidence_bytes=evidence_bytes)


def validate_canary_results(results, approvals=APPROVED_CANARY_EXECUTORS):
    keys = [(item.get("snapshot_id"), item.get("canonical_model_id"), item.get("canonical_effort")) for item in results]
    if len(keys) != len(set(keys)):
        raise ValueError("only one canary is permitted per snapshot/model/effort")
    result_digests = [item.get("executor_result_digest") for item in results]
    if len(result_digests) != len(set(result_digests)): raise ValueError("canary result digests cannot be replayed across tuple keys")
    return [_validate_canary_result_envelope(item, approvals) for item in results]


def validate_raw_evidence_root(raw_root, repository_root):
    if os.name == "nt":
        raise ValueError("operator-only raw evidence permissions are not supported on Windows")
    lexical, repo = Path(os.path.abspath(raw_root)), Path(repository_root).resolve()
    if lexical.is_symlink(): raise ValueError("raw_evidence_root cannot be a symlink")
    raw = lexical.resolve(strict=True)
    if raw == repo or repo in raw.parents or _git_worktree_ancestor(raw):
        raise ValueError("raw_evidence_root must resolve outside every Git worktree")
    if not raw.is_dir(): raise ValueError("raw_evidence_root must be a directory")
    for path in (raw, *raw.rglob("*")):
        if path.is_symlink(): raise ValueError("raw_evidence_root cannot contain symlinks")
        if os.name != "nt":
            mode = stat.S_IMODE(path.stat().st_mode)
            if path.is_dir() and mode != 0o700 or path.is_file() and mode != 0o600:
                raise ValueError("raw evidence directories require 0700 and files require 0600")
            if path.is_file() and path.stat().st_nlink != 1:
                raise ValueError("raw evidence files cannot have alternate hard links")
        if not path.is_dir() and not path.is_file(): raise ValueError("raw_evidence_root may contain only regular files and directories")
    return raw


def _git_worktree_ancestor(path):
    current = path if path.is_dir() else path.parent
    return any((ancestor / ".git").exists() for ancestor in (current, *current.parents))


def validate_private_external_file(path, repository_root, label, *, output=False):
    if os.name == "nt":
        raise ValueError("operator-only private-file permissions are not supported on Windows")
    lexical = Path(os.path.abspath(path)); repo = Path(repository_root).resolve()
    if lexical.is_symlink(): raise ValueError(f"{label} cannot be a symlink")
    parent = lexical.parent.resolve(strict=True); resolved = parent / lexical.name
    if resolved == repo or repo in resolved.parents or _git_worktree_ancestor(resolved): raise ValueError(f"{label} must remain outside every Git worktree")
    if os.name != "nt" and stat.S_IMODE(parent.stat().st_mode) != 0o700: raise ValueError(f"{label} parent directory must use mode 0700")
    if output and not resolved.exists(): return resolved
    if not resolved.is_file() or resolved.is_symlink(): raise ValueError(f"{label} must be a regular non-symlink file")
    if os.name != "nt" and stat.S_IMODE(resolved.stat().st_mode) != 0o600: raise ValueError(f"{label} must use mode 0600")
    if resolved.stat().st_size > PRIVATE_REFRESH_MAX_BYTES: raise ValueError(f"{label} exceeds the bounded private-file size")
    return resolved


def read_private_external_file(path, repository_root, label):
    resolved = validate_private_external_file(path, repository_root, label)
    return resolved, _read_bounded_regular_file(resolved, required_mode=0o600)


def validate_content_addressed_private_file(path, repository_root, label):
    resolved, raw = read_content_addressed_private_file(path, repository_root, label)
    return resolved


def read_content_addressed_private_file(path, repository_root, label):
    resolved, raw = read_private_external_file(path, repository_root, label)
    expected_name = f"{digest(raw).removeprefix('sha256:')}.json"
    if resolved.name != expected_name:
        raise ValueError(f"{label} must use its exact content digest as the filename")
    return resolved, raw


def materialize_source_capture(raw_root, repository_root, capture_bytes):
    captured = _parse_json_bytes(capture_bytes)
    if not isinstance(captured, list):
        raise ValueError("captured refresh must be a JSON list")
    raw = validate_raw_evidence_root(raw_root, repository_root)
    capture_digest = digest(capture_bytes)
    target = raw / f"{capture_digest.removeprefix('sha256:')}.json"
    if target.exists():
        _, retained = read_content_addressed_private_file(target, repository_root, "source capture")
        if retained != capture_bytes: raise ValueError("content-addressed source capture bytes disagree")
    else:
        _write_private_bytes(target, capture_bytes, append_only=True)
    validate_raw_evidence_root(raw, repository_root)
    _, retained = read_content_addressed_private_file(target, repository_root, "source capture")
    if retained != capture_bytes:
        raise ValueError("source capture was not retained under its content identity")
    return capture_digest, target


def validate_source_capture_evidence(manifest, refreshes, raw_root, repository_root):
    capture_digests = {item.get("source_capture_digest") for item in refreshes}
    if len(capture_digests) != 1:
        raise ValueError("source refreshes must bind one complete raw source capture")
    capture_digest = capture_digests.pop(); _need_digest(capture_digest, "source_capture_digest")
    raw = validate_raw_evidence_root(raw_root, repository_root)
    target = raw / f"{capture_digest.removeprefix('sha256:')}.json"
    _, capture_bytes = read_content_addressed_private_file(target, repository_root, "source capture")
    expected = normalize_source_refreshes(
        manifest, _parse_json_bytes(capture_bytes), source_capture_digest=capture_digest,
    )
    if refreshes and "retrieved_body_b64" not in refreshes[0]:
        expected = validate_source_refreshes(manifest, expected)["sanitized_refreshes"]
    if canonical_bytes(expected) != canonical_bytes(refreshes):
        raise ValueError("normalized source refresh does not match its retained raw capture")
    return capture_digest


def validate_canary_evidence(raw_root, repository_root, result):
    _need_digest(result.get("evidence_digest"), "evidence_digest")
    raw = validate_raw_evidence_root(raw_root, repository_root)
    target = raw / f"{result['evidence_digest'].removeprefix('sha256:')}.json"
    _, evidence_bytes = read_content_addressed_private_file(target, repository_root, "canary evidence")
    validate_canary_result(result, evidence_bytes=evidence_bytes)
    return evidence_bytes


def materialize_unknown_capture(raw_root, repository_root, surface, client_identity_id, repository_binding, work_item, captured_at):
    raw = validate_raw_evidence_root(raw_root, repository_root)
    record = _unknown_capture_record(surface, client_identity_id, repository_binding, work_item, captured_at)
    stored = canonical_bytes(record) + b"\n"; evidence = digest(stored)
    target = raw / f"{evidence.removeprefix('sha256:')}.json"
    if target.exists():
        _, retained = read_content_addressed_private_file(target, repository_root, "unknown capture")
        if retained != stored: raise ValueError("content-addressed unknown capture bytes disagree")
    else:
        _write(target, record, private=True)
    validate_raw_evidence_root(raw, repository_root)
    _, retained = read_content_addressed_private_file(target, repository_root, "unknown capture")
    if retained != stored or digest(retained) != evidence:
        raise ValueError("unknown capture was not retained under its content identity")
    return evidence, target


def validate_unknown_observation_evidence(observation, raw_root, repository_root):
    observation = validate_observation(dict(observation))
    if observation["collection_method_id"] != "unknown-observation-v1":
        return
    raw = validate_raw_evidence_root(raw_root, repository_root)
    target = raw / f"{observation['raw_evidence_digest'].removeprefix('sha256:')}.json"
    _, retained = read_content_addressed_private_file(target, repository_root, "unknown observation evidence")
    expected = canonical_bytes(_unknown_capture_record(
        observation["surface"], observation["client_identity_id"], observation["repository_binding"],
        observation["work_item"], observation["started_at"],
    )) + b"\n"
    if retained != expected:
        raise ValueError("unknown observation evidence bytes do not match the deterministic attempt record")


def _format_timestamp(value):
    return value.isoformat().replace("+00:00", "Z")


def _private_record_directory(raw, name):
    target = raw / name
    if target.exists():
        if target.is_symlink() or not target.is_dir():
            raise ValueError("raw evidence record path must be a private directory")
    else:
        try:
            target.mkdir(mode=0o700)
        except FileExistsError:
            if target.is_symlink() or not target.is_dir():
                raise ValueError("raw evidence record path must be a private directory")
    if os.name != "nt":
        target.chmod(0o700)
    return target


def _store_private_record(directory, value, repository_root):
    payload = canonical_bytes(value) + b"\n"; record_digest = digest(payload)
    target = directory / f"{record_digest.removeprefix('sha256:')}.json"
    if target.exists():
        _, retained = read_content_addressed_private_file(target, repository_root, "raw evidence record")
        if retained != payload: raise ValueError("content-addressed raw evidence record bytes disagree")
        return record_digest
    try:
        _write(target, value, private=True, append_only=True)
    except FileExistsError:
        _, retained = read_content_addressed_private_file(target, repository_root, "raw evidence record")
        if retained != payload: raise ValueError("content-addressed raw evidence record bytes disagree")
    return record_digest


def _load_private_records(directory, repository_root, label):
    if not directory.exists(): return []
    if directory.is_symlink() or not directory.is_dir(): raise ValueError(f"{label} path must be a private directory")
    entries = sorted(directory.iterdir(), key=lambda path: path.name)
    if any(path.is_symlink() or not path.is_file() or path.suffix != ".json" for path in entries):
        raise ValueError(f"{label} directory contains an undeclared entry")
    records = []
    for path in entries:
        _, raw = read_content_addressed_private_file(path, repository_root, label)
        record = _parse_json_bytes(raw)
        if raw != canonical_bytes(record) + b"\n": raise ValueError(f"{label} must use canonical JSON bytes")
        records.append((digest(raw), record))
    return records


def _validate_retention_record(record_digest, record):
    keys = {"schema_version", "candidate_freeze_id", "raw_evidence_digest", "published_at", "registered_at", "delete_after"}
    if not isinstance(record, dict) or set(record) != keys or record["schema_version"] != "raw-evidence-retention.v1":
        raise ValueError("raw evidence retention record must use the closed v1 shape")
    _need_digest(record_digest, "retention record digest"); _need_digest(record["candidate_freeze_id"], "candidate_freeze_id"); _need_digest(record["raw_evidence_digest"], "raw_evidence_digest")
    published = _parsed_timestamp(record["published_at"], "retention publication timestamp")
    _parsed_timestamp(record["registered_at"], "retention registration timestamp")
    delete_after = _parsed_timestamp(record["delete_after"], "retention deletion deadline")
    if delete_after != published + timedelta(days=RAW_EVIDENCE_RETENTION_DAYS):
        raise ValueError("raw evidence retention deadline must be exactly 30 days after publication")
    return record


def _validate_deletion_record(record_digest, record):
    keys = {"schema_version", "raw_evidence_digest", "retention_record_digests", "delete_after", "deleted_at"}
    if not isinstance(record, dict) or set(record) != keys or record["schema_version"] != "raw-evidence-deletion.v1":
        raise ValueError("raw evidence deletion record must use the closed v1 shape")
    _need_digest(record_digest, "deletion record digest"); _need_digest(record["raw_evidence_digest"], "raw_evidence_digest")
    refs = record["retention_record_digests"]
    if not isinstance(refs, list) or not refs or refs != sorted(set(refs)):
        raise ValueError("raw evidence deletion record requires unique retention records")
    for value in refs: _need_digest(value, "retention_record_digest")
    deadline = _parsed_timestamp(record["delete_after"], "deletion deadline")
    if _parsed_timestamp(record["deleted_at"], "deletion timestamp") < deadline:
        raise ValueError("raw evidence deletion precedes its retention deadline")
    return record


def _validate_publication_receipt(record_digest, record):
    keys = {"schema_version", "candidate_freeze_id", "published_artifact_digest", "published_at", "retention_record_digests"}
    if not isinstance(record, dict) or set(record) != keys or record["schema_version"] != "raw-evidence-publication.v1":
        raise ValueError("raw evidence publication receipt must use the closed v1 shape")
    _need_digest(record_digest, "publication receipt digest")
    _need_digest(record["candidate_freeze_id"], "candidate_freeze_id")
    _need_digest(record["published_artifact_digest"], "published_artifact_digest")
    _parsed_timestamp(record["published_at"], "publication receipt timestamp")
    refs = record["retention_record_digests"]
    if not isinstance(refs, list) or not refs or refs != sorted(set(refs)):
        raise ValueError("publication receipt requires unique retention records")
    for value in refs: _need_digest(value, "retention_record_digest")
    return record


def _freeze_raw_evidence_digests(freeze):
    observations = freeze["surface_matrix"]["observations"]
    digests = {
        item["raw_evidence_digest"] for item in observations
        if item["collection_method_id"] != "fixture-enumeration-v1"
    }
    digests.update(item["source_capture_digest"] for item in freeze["official_source_refreshes"])
    digests.update(item["evidence_digest"] for item in freeze["canary_results"])
    for value in digests: _need_digest(value, "raw_evidence_digest")
    return sorted(digests)


@contextmanager
def _retention_lock(raw):
    target = raw / RETENTION_LOCK_DIR
    try:
        target.mkdir(mode=0o700)
    except FileExistsError as error:
        raise ValueError("raw evidence retention operation is already in progress") from error
    if target.is_symlink() or not target.is_dir():
        raise ValueError("raw evidence retention lock is invalid")
    if os.name != "nt": target.chmod(0o700)
    try:
        yield
    finally:
        target.rmdir()


def _register_raw_evidence_retention_locked(freeze, raw, repository_root):
    published = _parsed_timestamp(freeze.get("published_at"), "freeze publication timestamp")
    evidence_digests = _freeze_raw_evidence_digests(freeze)
    if not evidence_digests: return []
    deleted_digests = {
        _validate_deletion_record(record_digest, record)["raw_evidence_digest"]
        for record_digest, record in _load_private_records(raw / DELETION_RECORDS_DIR, repository_root, "deletion record")
    }
    if set(evidence_digests) & deleted_digests:
        raise ValueError("raw evidence cannot be registered after deletion has begun")
    records = _private_record_directory(raw, RETENTION_RECORDS_DIR)
    existing = {}
    for record_digest, raw_record in _load_private_records(records, repository_root, "retention record"):
        record = _validate_retention_record(record_digest, raw_record)
        key = (record["candidate_freeze_id"], record["raw_evidence_digest"], record["published_at"])
        if key in existing:
            raise ValueError("freeze evidence has multiple retention registration records")
        existing[key] = record_digest
    registered_at = None
    record_digests = []
    for evidence_digest in evidence_digests:
        evidence_path = raw / f"{evidence_digest.removeprefix('sha256:')}.json"
        read_content_addressed_private_file(evidence_path, repository_root, "retained raw evidence")
        key = (freeze["candidate_freeze_id"], evidence_digest, freeze["published_at"])
        if key in existing:
            record_digests.append(existing[key]); continue
        if registered_at is None:
            registered = _retention_now()
            if registered.tzinfo is None or registered.utcoffset() != timedelta(0):
                raise ValueError("retention registration clock must be UTC")
            registered_at = _format_timestamp(registered)
        record = {
            "schema_version": "raw-evidence-retention.v1",
            "candidate_freeze_id": freeze["candidate_freeze_id"],
            "raw_evidence_digest": evidence_digest,
            "published_at": freeze["published_at"],
            "registered_at": registered_at,
            "delete_after": _format_timestamp(published + timedelta(days=RAW_EVIDENCE_RETENTION_DAYS)),
        }
        record_digests.append(_store_private_record(records, record, repository_root))
    validate_raw_evidence_root(raw, repository_root)
    return sorted(record_digests)


def _publication_target_matches(path, payload):
    target = Path(path)
    if not target.exists():
        return False
    if _read_bounded_regular_file(target) != payload:
        raise ValueError("publication output already exists with different bytes")
    return True


def _store_publication_receipt_locked(freeze, retention_record_digests, raw, repository_root):
    receipt = {
        "schema_version": "raw-evidence-publication.v1",
        "candidate_freeze_id": freeze["candidate_freeze_id"],
        "published_artifact_digest": digest(canonical_bytes(freeze) + b"\n"),
        "published_at": freeze["published_at"],
        "retention_record_digests": sorted(retention_record_digests),
    }
    directory = _private_record_directory(raw, PUBLICATION_RECEIPTS_DIR)
    receipt_digest = _store_private_record(directory, receipt, repository_root)
    _validate_publication_receipt(receipt_digest, receipt)
    return receipt_digest


def publish_with_raw_evidence_retention(
    freeze, output, raw_evidence_root, repository_root, *, manifest,
    predecessor=None, expected_telemetry_profile_id=None, expected_treatment_contract_digest=None,
    expected_predecessor_telemetry_profile_id=None, expected_predecessor_treatment_contract_digest=None,
):
    raw = validate_raw_evidence_root(raw_evidence_root, repository_root)
    freeze = validate_freeze(
        freeze, manifest, predecessor=predecessor,
        expected_telemetry_profile_id=expected_telemetry_profile_id,
        expected_treatment_contract_digest=expected_treatment_contract_digest,
        expected_predecessor_telemetry_profile_id=expected_predecessor_telemetry_profile_id,
        expected_predecessor_treatment_contract_digest=expected_predecessor_treatment_contract_digest,
    )
    payload = canonical_bytes(freeze) + b"\n"
    with _retention_lock(raw):
        validate_raw_evidence_root(raw, repository_root)
        deleted_digests = {
            _validate_deletion_record(record_digest, record)["raw_evidence_digest"]
            for record_digest, record in _load_private_records(raw / DELETION_RECORDS_DIR, repository_root, "deletion record")
        }
        if set(_freeze_raw_evidence_digests(freeze)) & deleted_digests:
            raise ValueError("raw evidence cannot be registered after deletion has begun")
        validate_source_capture_evidence(manifest, freeze["official_source_refreshes"], raw, repository_root)
        already_published = _publication_target_matches(output, payload)
        retention_record_digests = _register_raw_evidence_retention_locked(freeze, raw, repository_root)
        if not already_published:
            _write(output, freeze, append_only=True)
        receipt_digest = _store_publication_receipt_locked(freeze, retention_record_digests, raw, repository_root)
        validate_raw_evidence_root(raw, repository_root)
        return {"retention_record_digests": retention_record_digests, "publication_receipt_digest": receipt_digest}


def _retention_now():
    return datetime.now(timezone.utc)


def reconcile_raw_evidence_retention(raw_evidence_root, repository_root, as_of=None, *, apply=False):
    raw = validate_raw_evidence_root(raw_evidence_root, repository_root)
    if apply:
        if as_of is not None: raise ValueError("cleanup derives its deletion time from current UTC")
        current = _retention_now()
        if current.tzinfo is None or current.utcoffset() != timedelta(0): raise ValueError("cleanup clock must be UTC")
        effective_as_of = _format_timestamp(current)
    else:
        current = _parsed_timestamp(as_of, "retention as-of timestamp"); effective_as_of = as_of
    with _retention_lock(raw):
        validate_raw_evidence_root(raw, repository_root)
        return _reconcile_raw_evidence_retention_locked(raw, repository_root, effective_as_of, current, apply=apply)


def _reconcile_raw_evidence_retention_locked(raw, repository_root, as_of, current, *, apply):
    all_retention_records = [(_validate_retention_record(record_digest, record), record_digest) for record_digest, record in _load_private_records(raw / RETENTION_RECORDS_DIR, repository_root, "retention record")]
    retention_by_digest = {record_digest: record for record, record_digest in all_retention_records}
    publication_receipts = [(_validate_publication_receipt(record_digest, record), record_digest) for record_digest, record in _load_private_records(raw / PUBLICATION_RECEIPTS_DIR, repository_root, "publication receipt")]
    receipt_freeze_ids, governing_record_digests = set(), set()
    for receipt, _ in publication_receipts:
        if receipt["candidate_freeze_id"] in receipt_freeze_ids:
            raise ValueError("candidate freeze has multiple publication receipts")
        receipt_freeze_ids.add(receipt["candidate_freeze_id"])
        refs = set(receipt["retention_record_digests"])
        if not refs <= set(retention_by_digest):
            raise ValueError("publication receipt references a missing retention record")
        for ref in refs:
            retained = retention_by_digest[ref]
            if retained["candidate_freeze_id"] != receipt["candidate_freeze_id"] or retained["published_at"] != receipt["published_at"]:
                raise ValueError("publication receipt does not bind its freeze retention records")
        governing_record_digests.update(refs)
    pending_record_digests = sorted(set(retention_by_digest) - governing_record_digests)
    retention_records = all_retention_records
    deletion_records = [(_validate_deletion_record(record_digest, record), record_digest) for record_digest, record in _load_private_records(raw / DELETION_RECORDS_DIR, repository_root, "deletion record")]
    retention_by_evidence = {}
    for record, record_digest in retention_records:
        retention_by_evidence.setdefault(record["raw_evidence_digest"], []).append((record, record_digest))
    deletion_by_evidence = {}
    for record, record_digest in deletion_records:
        if record["raw_evidence_digest"] in deletion_by_evidence:
            raise ValueError("raw evidence digest has multiple deletion records")
        deletion_by_evidence[record["raw_evidence_digest"]] = (record, record_digest)
    if not set(deletion_by_evidence) <= set(retention_by_evidence):
        raise ValueError("deletion record lacks retained evidence authority")
    retained, deleted, deletion_digests = [], [], []
    for evidence_digest in sorted(retention_by_evidence):
        grouped = retention_by_evidence[evidence_digest]
        record_digests = sorted(record_digest for _, record_digest in grouped)
        deadlines = []
        for record, record_digest in grouped:
            registered = _parsed_timestamp(record["registered_at"], "retention registration timestamp")
            if current < registered:
                raise ValueError("retention as-of timestamp precedes the registration record")
            deadline = _parsed_timestamp(record["delete_after"], "retention deletion deadline")
            if record_digest not in governing_record_digests:
                deadline = min(deadline, registered + timedelta(days=RAW_EVIDENCE_PENDING_DAYS))
            deadlines.append(deadline)
        deadline = max(deadlines)
        deadline_text = _format_timestamp(deadline); target = raw / f"{evidence_digest.removeprefix('sha256:')}.json"
        deletion = deletion_by_evidence.get(evidence_digest)
        if deletion is not None:
            record, record_digest = deletion
            if record["retention_record_digests"] != record_digests or record["delete_after"] != deadline_text:
                raise ValueError("raw evidence deletion record does not bind the complete retention history")
            if current < _parsed_timestamp(record["deleted_at"], "deletion timestamp"):
                raise ValueError("retention as-of timestamp precedes the deletion record")
            if target.exists():
                if not apply: raise ValueError("deletion record still has retained raw evidence bytes")
                read_content_addressed_private_file(target, repository_root, "expired raw evidence"); target.unlink(); _fsync_directory(raw)
            deleted.append(evidence_digest); deletion_digests.append(record_digest); continue
        if current < deadline:
            read_content_addressed_private_file(target, repository_root, "retained raw evidence")
            retained.append(evidence_digest); continue
        if not target.exists(): raise ValueError("expired raw evidence is missing without a deletion record")
        if not apply: raise ValueError("expired raw evidence requires cleanup")
        read_content_addressed_private_file(target, repository_root, "expired raw evidence")
        deletion_record = {
            "schema_version": "raw-evidence-deletion.v1",
            "raw_evidence_digest": evidence_digest,
            "retention_record_digests": record_digests,
            "delete_after": deadline_text,
            "deleted_at": as_of,
        }
        directory = _private_record_directory(raw, DELETION_RECORDS_DIR)
        record_digest = _store_private_record(directory, deletion_record, repository_root)
        target.unlink(); _fsync_directory(raw); deleted.append(evidence_digest); deletion_digests.append(record_digest)
    validate_raw_evidence_root(raw, repository_root)
    return {
        "schema_version": "raw-evidence-retention-report.v1", "mode": "cleanup" if apply else "verify", "as_of": as_of,
        "retained_evidence_digests": retained, "deleted_evidence_digests": deleted,
        "retention_record_digests": sorted(record_digest for _, record_digest in retention_records),
        "pending_retention_record_digests": pending_record_digests,
        "publication_receipt_digests": sorted(record_digest for _, record_digest in publication_receipts),
        "deletion_record_digests": sorted(deletion_digests),
    }


def validate_tuple_decisions(decisions, *, require_snapshot=False):
    if any(item.get("decision") == "included" for item in decisions) and not isinstance(decisions, _BoundDecisionSet):
        raise ValueError("included decisions require manifest-bound authority")
    keys = {"candidate_route_id", "candidate_route_digest", "agent_contract_id", "named_agent", "agent_contract_digest", "source_ref", "source_sha256", "instruction_sha256", "role_instruction_sha256", "canonical_model_id", "canonical_effort", "official_source_bindings", "effort_surface_bindings", "runtime_capability_snapshot_id", "surface_matrix_id", "surface_evidence", "hidden_state", "normalization_map_id", "disagreement_digest", "source_admitted", "source_admission_reasons", "availability_disposition", "surface_disposition", "exact_treatment_readiness", "decision", "reasons"}
    for item in decisions:
        strings = (item.get("candidate_route_id"), item.get("agent_contract_id"), item.get("named_agent"), item.get("canonical_model_id"))
        if set(item) != keys or not all(isinstance(value, str) and value and not any(mark in value for mark in ("/", "\\", "://", "@")) for value in strings):
            raise ValueError("tuple decision must use the sanitized closed v1 shape")
        if not isinstance(item["source_ref"], str) or not item["source_ref"] or item["source_ref"].startswith(("/", "\\")) or ".." in Path(item["source_ref"]).parts: raise ValueError("tuple source_ref must be repository relative")
        for field in ("candidate_route_digest", "agent_contract_digest", "source_sha256", "instruction_sha256", "role_instruction_sha256", "surface_matrix_id", "normalization_map_id"):
            _need_digest(item[field], field)
        if item["instruction_sha256"] != item["role_instruction_sha256"]: raise ValueError("tuple instruction hashes disagree")
        snapshot = item["runtime_capability_snapshot_id"]
        if snapshot is not None: _need_digest(snapshot, "runtime_capability_snapshot_id")
        if require_snapshot and snapshot is None: raise ValueError("tuple runtime snapshot binding is required")
        if item["disagreement_digest"] is not None: _need_digest(item["disagreement_digest"], "disagreement_digest")
        source_binding_keys = {"official_source_ledger_id", "source_refresh_digest"}
        if any(set(row) != source_binding_keys or not _SOURCE_ID.fullmatch(str(row["official_source_ledger_id"])) or not _DIGEST.fullmatch(str(row["source_refresh_digest"])) for row in item["official_source_bindings"]): raise ValueError("tuple official-source binding is invalid")
        effort_binding_keys = {"effort_surface_record_id", "effort_surface_record_digest", "official_source_ledger_id", "source_refresh_digest"}
        if any(set(row) != effort_binding_keys or not isinstance(row["effort_surface_record_id"], str) or not row["effort_surface_record_id"] or not _SOURCE_ID.fullmatch(str(row["official_source_ledger_id"])) or not _DIGEST.fullmatch(str(row["effort_surface_record_digest"])) or not _DIGEST.fullmatch(str(row["source_refresh_digest"])) for row in item["effort_surface_bindings"]): raise ValueError("tuple effort-surface binding is invalid")
        if set(item["surface_evidence"]) != set(SURFACES) or set(item["hidden_state"]) != set(SURFACES): raise ValueError("tuple surface evidence is incomplete")
        evidence_keys = {"surface_observation_id", "completeness_state", "visibility_policy", "raw_evidence_digest", "raw_evidence_ref", "matching_entry"}
        for surface, evidence in item["surface_evidence"].items():
            if set(evidence) != evidence_keys or evidence["completeness_state"] not in {"complete", "partial", "unavailable", "unknown"}: raise ValueError("tuple surface evidence is invalid")
            _need_digest(evidence["surface_observation_id"], "surface_observation_id"); _need_digest(evidence["raw_evidence_digest"], "raw_evidence_digest")
            if evidence["raw_evidence_ref"] != f"raw://{evidence['raw_evidence_digest']}": raise ValueError("tuple surface evidence reference is invalid")
            if evidence["matching_entry"] is not None: _clean_entry(evidence["matching_entry"])
            expected_hidden = evidence["matching_entry"]["hidden"] if evidence["matching_entry"] is not None else None
            if item["hidden_state"][surface] != expected_hidden: raise ValueError("tuple hidden state does not match surface evidence")
        if item["canonical_effort"] is not None and not _token(item["canonical_effort"]): raise ValueError("tuple effort is invalid")
        if not isinstance(item["source_admitted"], bool) or item["availability_disposition"] not in {"supported", "available_for_pinned_environment", "unknown"} or item["surface_disposition"] not in {"agreed", "disagreed", "unknown"} or item["exact_treatment_readiness"] not in {"pending", "not_ready_excluded"} or item["decision"] not in {"included", "excluded"} or not all(_token(value) for value in item["source_admission_reasons"] + item["reasons"]):
            raise ValueError("tuple decision disposition is invalid")
        if item["decision"] == "excluded" and not item["reasons"]:
            raise ValueError("excluded tuple decision requires a reason")
        if item["decision"] == "included" and (not item["source_admitted"] or item["surface_disposition"] != "agreed"): raise ValueError("included tuple lacks source and surface admission")
    if len({item["candidate_route_id"] for item in decisions}) != len(decisions): raise ValueError("tuple decision candidate identities must be unique")
    return decisions


def build_runtime_snapshot(identity, refreshes, matrix, *, supersedes=None):
    if supersedes is not None: _need_digest(supersedes, "supersedes_snapshot_id")
    matrix = validate_surface_matrix(matrix)
    if matrix["client_identity_id"] != identity["client_identity_id"]: raise ValueError("freeze client identity does not match the matrix")
    repository = validate_repository_binding(matrix["observations"][0]["repository_binding"]); work_item = validate_work_item(matrix["work_item"])
    entries = [entry for observation in matrix["observations"] for entry in observation["entries"]]
    raw_digest = digest([item["raw_evidence_digest"] for item in matrix["observations"]])
    payload = {"schema_version": SCHEMA_VERSION, "surface_matrix_id": matrix["surface_matrix_id"], "client_identity_id": identity["client_identity_id"],
               "controlled_repository_snapshot": repository, "work_item": work_item,
               "models": sorted({item["model"] for item in entries}), "efforts": sorted({item["effort"] for item in entries}),
               "capabilities": sorted({value for item in entries for value in item.get("capabilities", [])}),
               "collection_window": {"started_at": min(item["started_at"] for item in matrix["observations"]), "completed_at": max(item["completed_at"] for item in matrix["observations"])},
               "raw_evidence_digest": raw_digest, "raw_evidence_ref": f"aggregate://{raw_digest}",
               "source_refresh_set_digest": digest(refreshes), "supersedes_snapshot_id": supersedes}
    return {"runtime_capability_snapshot_id": digest(payload), **payload}


def _freeze_identity_payload(freeze):
    return {key: freeze[key] for key in freeze if key != "candidate_freeze_id"}


def _validate_publication_time(published_at, refreshes, matrix, predecessor=None):
    published = _parsed_timestamp(published_at, "publication timestamp")
    evidence_times = [
        *(_parsed_timestamp(item["retrieved_at"], "source retrieval timestamp") for item in refreshes),
        *(_parsed_timestamp(item["completed_at"], "surface collection timestamp") for item in matrix["observations"]),
    ]
    if evidence_times and published < max(evidence_times):
        raise ValueError("publication timestamp precedes captured evidence")
    if predecessor is not None and published <= _parsed_timestamp(predecessor["published_at"], "predecessor publication timestamp"):
        raise ValueError("successor publication timestamp must be later than its predecessor")


def _successor_canary_results(predecessor, same_runtime_inputs):
    return copy.deepcopy(predecessor["canary_results"]) if predecessor is not None and same_runtime_inputs else []


def _validate_same_snapshot_canary_history(predecessor, results, unchanged_snapshot):
    if not unchanged_snapshot:
        return
    prior_results = predecessor["canary_results"]
    if len(results) < len(prior_results) or canonical_bytes(results[:len(prior_results)]) != canonical_bytes(prior_results):
        raise ValueError("same-snapshot successor cannot drop or rewrite canary history")


def build_freeze(
    identity, refreshes, matrix, decisions, published_at, *, manifest, predecessor=None,
    raw_evidence_root=None, repository_root=None,
    expected_predecessor_telemetry_profile_id=None,
    expected_predecessor_treatment_contract_digest=None,
):
    identity = build_client_identity(identity); matrix = validate_surface_matrix(matrix); decisions = validate_tuple_decisions(decisions)
    if (raw_evidence_root is None) != (repository_root is None):
        raise ValueError("freeze raw evidence root and repository root must be provided together")
    if any(item["collection_method_id"] == "unknown-observation-v1" for item in matrix["observations"]):
        if raw_evidence_root is None or repository_root is None:
            raise ValueError("initial unknown-observation publication requires its raw evidence root")
        for observation in matrix["observations"]:
            validate_unknown_observation_evidence(observation, raw_evidence_root, repository_root)
    if predecessor is not None:
        predecessor = validate_freeze(
            predecessor, manifest,
            expected_telemetry_profile_id=expected_predecessor_telemetry_profile_id,
            expected_treatment_contract_digest=expected_predecessor_treatment_contract_digest,
            _enforce_lineage=False,
        )
    if len(refreshes) != 22 or len({item.get("official_source_ledger_id") for item in refreshes}) != 22:
        raise ValueError("freeze requires all 22 source refreshes")
    refresh_validation = validate_source_refreshes(manifest, refreshes); sanitized_refreshes = refresh_validation["sanitized_refreshes"]
    if raw_evidence_root is not None:
        validate_source_capture_evidence(manifest, refreshes, raw_evidence_root, repository_root)
    _validate_publication_time(published_at, sanitized_refreshes, matrix, predecessor)
    rebuilt, expected = evaluate_surface_matrix(matrix["observations"], candidate_tuples_from_manifest(manifest, refreshes), aliases=matrix["normalization_map"], expected_integrity_digest=matrix["aggregate_integrity_digest"])
    if rebuilt["surface_matrix_id"] != matrix["surface_matrix_id"] or canonical_bytes(expected) != canonical_bytes(decisions):
        raise ValueError("tuple decisions do not match manifest-backed matrix evaluation")
    source_digest, telemetry = refresh_validation["digest"], PENDING_TELEMETRY_PROFILE_ID
    same_runtime_inputs = predecessor is not None and (
        predecessor["client_identity"] == identity
        and predecessor["official_source_refreshes"] == sanitized_refreshes
        and predecessor["surface_matrix"] == matrix
    )
    supersedes_snapshot = None
    if predecessor is not None:
        supersedes_snapshot = predecessor["runtime_capability_snapshot"].get("supersedes_snapshot_id") if same_runtime_inputs else predecessor["runtime_capability_snapshot_id"]
    snapshot = build_runtime_snapshot(identity, sanitized_refreshes, matrix, supersedes=supersedes_snapshot)
    decisions = _BoundDecisionSet([{**item, "runtime_capability_snapshot_id": snapshot["runtime_capability_snapshot_id"]} for item in expected]); validate_tuple_decisions(decisions, require_snapshot=True)
    tuple_digest = digest(decisions); manifest_binding = {"schema_version": manifest["schema_version"], "snapshot_id": manifest["snapshot"]["snapshot_id"], "manifest_digest": digest(manifest)}
    included = [item["candidate_route_id"] for item in decisions if item["decision"] == "included"]
    excluded = [{"candidate_route_id": item["candidate_route_id"], "reasons": item["reasons"]} for item in decisions if item["decision"] == "excluded"]
    result = {"schema_version": SCHEMA_VERSION, "source_manifest_binding": manifest_binding, "client_identity": identity, "client_identity_id": identity["client_identity_id"],
            "official_source_refreshes": sanitized_refreshes, "surface_matrix": matrix, "runtime_capability_snapshot": snapshot,
            "runtime_capability_snapshot_id": snapshot["runtime_capability_snapshot_id"], "telemetry_profile_id": telemetry,
            "source_refresh_set_digest": source_digest, "current_ledger_digest": source_digest, "surface_matrix_id": matrix["surface_matrix_id"],
            "surface_matrix_digest": matrix["surface_matrix_id"], "tuple_decision_digest": tuple_digest,
            "included_candidate_route_ids": included, "excluded_candidates": excluded,
            "tuple_decisions": decisions, "approved_canary_executors": list(APPROVED_CANARY_EXECUTORS),
            "canary_results": _successor_canary_results(predecessor, same_runtime_inputs), "published_at": published_at,
            "supersedes_candidate_freeze_id": predecessor["candidate_freeze_id"] if predecessor is not None else None}
    result["candidate_freeze_id"] = digest(_freeze_identity_payload(result))
    return validate_freeze(
        result, manifest, predecessor=predecessor,
        expected_predecessor_telemetry_profile_id=expected_predecessor_telemetry_profile_id,
        expected_predecessor_treatment_contract_digest=expected_predecessor_treatment_contract_digest,
    )


def _documented_discovery_unavailable(observations):
    return any(item.get("collection_method_id") == "unknown-observation-v1" for item in observations)


def _validate_canary_tuple_binding(decisions, result, snapshot_id, observations):
    matches = [
        item for item in decisions
        if item["canonical_model_id"] == result["canonical_model_id"]
        and item["canonical_effort"] == result["canonical_effort"]
    ]
    admitted = [item for item in matches if item["source_admitted"]]
    if result["snapshot_id"] != snapshot_id or not admitted:
        raise ValueError("canary requires a source-admitted snapshot model/effort key")
    if not _documented_discovery_unavailable(observations):
        raise ValueError("canary requires documented discovery to be unavailable")
    return admitted


def validate_freeze(
    freeze, manifest, *, predecessor=None, expected_telemetry_profile_id=None,
    expected_treatment_contract_digest=None, expected_predecessor_telemetry_profile_id=None,
    expected_predecessor_treatment_contract_digest=None, _enforce_lineage=True,
):
    keys = {"schema_version", "candidate_freeze_id", "source_manifest_binding", "client_identity", "client_identity_id", "official_source_refreshes", "source_refresh_set_digest", "surface_matrix", "surface_matrix_id", "runtime_capability_snapshot", "runtime_capability_snapshot_id", "telemetry_profile_id", "current_ledger_digest", "surface_matrix_digest", "tuple_decision_digest", "included_candidate_route_ids", "excluded_candidates", "tuple_decisions", "approved_canary_executors", "canary_results", "published_at", "supersedes_candidate_freeze_id"}
    actual_keys = set(freeze) if isinstance(freeze, dict) else set()
    treatment_bound = "treatment_contract_digest" in actual_keys
    expected_keys = keys | ({"treatment_contract_digest"} if treatment_bound else set())
    if not isinstance(freeze, dict) or actual_keys != expected_keys or freeze.get("schema_version") != SCHEMA_VERSION: raise ValueError("freeze must use the closed v1 shape")
    validate_manifest(manifest); identity = build_client_identity(freeze["client_identity"])
    if predecessor is not None:
        predecessor = validate_freeze(
            predecessor, manifest,
            expected_telemetry_profile_id=expected_predecessor_telemetry_profile_id,
            expected_treatment_contract_digest=expected_predecessor_treatment_contract_digest,
            _enforce_lineage=False,
        )
    supersedes = freeze["supersedes_candidate_freeze_id"]
    if supersedes is None and predecessor is not None:
        raise ValueError("initial freeze cannot declare a predecessor")
    if supersedes is not None:
        _need_digest(supersedes, "supersedes_candidate_freeze_id")
        if _enforce_lineage and predecessor is None:
            raise ValueError("successor freeze requires its validated predecessor")
        if predecessor is not None and supersedes != predecessor["candidate_freeze_id"]:
            raise ValueError("successor freeze predecessor identity is invalid")
    if freeze["client_identity_id"] != identity["client_identity_id"]: raise ValueError("freeze client identity fields disagree")
    if freeze["client_identity"] != identity: raise ValueError("freeze client identity must use the canonical closed shape")
    expected_manifest = {"schema_version": manifest["schema_version"], "snapshot_id": manifest["snapshot"]["snapshot_id"], "manifest_digest": digest(manifest)}
    if freeze["source_manifest_binding"] != expected_manifest: raise ValueError("freeze manifest binding is not canonical")
    refresh_validation = validate_published_source_refreshes(manifest, freeze["official_source_refreshes"]); matrix = validate_surface_matrix(freeze["surface_matrix"])
    _validate_publication_time(freeze["published_at"], freeze["official_source_refreshes"], matrix, predecessor)
    if freeze["source_refresh_set_digest"] != refresh_validation["digest"] or freeze["current_ledger_digest"] != refresh_validation["digest"]: raise ValueError("freeze source ledger digests disagree")
    if freeze["surface_matrix_id"] != matrix["surface_matrix_id"] or freeze["surface_matrix_digest"] != matrix["surface_matrix_id"]: raise ValueError("freeze surface matrix fields disagree")
    snapshot = freeze["runtime_capability_snapshot"]; expected_snapshot = build_runtime_snapshot(identity, freeze["official_source_refreshes"], matrix, supersedes=snapshot.get("supersedes_snapshot_id"))
    if snapshot != expected_snapshot or freeze["runtime_capability_snapshot_id"] != expected_snapshot["runtime_capability_snapshot_id"]: raise ValueError("freeze runtime snapshot fields disagree")
    unchanged_snapshot = predecessor is not None and expected_snapshot["runtime_capability_snapshot_id"] == predecessor["runtime_capability_snapshot_id"]
    if predecessor is not None:
        required_snapshot_predecessor = predecessor["runtime_capability_snapshot"].get("supersedes_snapshot_id") if unchanged_snapshot else predecessor["runtime_capability_snapshot_id"]
        if expected_snapshot["supersedes_snapshot_id"] != required_snapshot_predecessor:
            raise ValueError("successor runtime snapshot lineage is invalid")
    rebuilt_matrix, expected_decisions = evaluate_surface_matrix(matrix["observations"], candidate_tuples_from_published(manifest, freeze["official_source_refreshes"]), aliases=matrix["normalization_map"], expected_integrity_digest=matrix["aggregate_integrity_digest"])
    if rebuilt_matrix["surface_matrix_id"] != matrix["surface_matrix_id"]: raise ValueError("published surface matrix cannot be rebuilt")
    expected_decisions = _BoundDecisionSet([{**item, "runtime_capability_snapshot_id": expected_snapshot["runtime_capability_snapshot_id"]} for item in expected_decisions])
    validate_tuple_decisions(expected_decisions, require_snapshot=True)
    if canonical_bytes(freeze["tuple_decisions"]) != canonical_bytes(expected_decisions): raise ValueError("published tuple decisions cannot be rebuilt")
    route_ids = {item["candidate_route_id"] for item in expected_decisions}; manifest_route_ids = {item["candidate_route_id"] for item in manifest["candidate_routes"]}
    if not manifest_route_ids <= route_ids or freeze["tuple_decision_digest"] != digest(expected_decisions): raise ValueError("freeze tuple authority is incomplete")
    included = [item["candidate_route_id"] for item in expected_decisions if item["decision"] == "included"]
    excluded = [{"candidate_route_id": item["candidate_route_id"], "reasons": item["reasons"]} for item in expected_decisions if item["decision"] == "excluded"]
    if freeze["included_candidate_route_ids"] != included or freeze["excluded_candidates"] != excluded: raise ValueError("freeze derived candidate lists disagree")
    _need_digest(freeze["candidate_freeze_id"], "candidate_freeze_id")
    if freeze["telemetry_profile_id"] == PENDING_TELEMETRY_PROFILE_ID:
        if treatment_bound or expected_telemetry_profile_id is not None or expected_treatment_contract_digest is not None:
            raise ValueError("pending-treatment freeze cannot claim a treatment contract binding")
    else:
        if expected_telemetry_profile_id is None or expected_treatment_contract_digest is None:
            raise ValueError("treatment-aware freeze validation requires the expected profile and contract binding")
        _need_digest(expected_telemetry_profile_id, "expected telemetry profile ID")
        _need_digest(expected_treatment_contract_digest, "expected treatment contract digest")
        if not treatment_bound:
            raise ValueError("treatment-aware freeze must retain its treatment contract digest")
        _need_digest(freeze["treatment_contract_digest"], "treatment contract digest")
        if freeze["telemetry_profile_id"] != expected_telemetry_profile_id or freeze["treatment_contract_digest"] != expected_treatment_contract_digest:
            raise ValueError("freeze treatment profile and contract binding disagree")
    canonical_approvals = list(_validated_canary_approvals(APPROVED_CANARY_EXECUTORS))
    if freeze["approved_canary_executors"] != canonical_approvals:
        raise ValueError("published canary approvals do not match the repository-owned allowlist")
    if not canonical_approvals and freeze["canary_results"]:
        raise ValueError("published canary results require a repository-approved executor")
    validated_canaries = validate_canary_results(freeze["canary_results"], APPROVED_CANARY_EXECUTORS)
    if validated_canaries != freeze["canary_results"]: raise ValueError("published canary dispositions are not validated")
    _validate_same_snapshot_canary_history(predecessor, validated_canaries, unchanged_snapshot)
    for result in validated_canaries:
        _validate_canary_tuple_binding(expected_decisions, result, expected_snapshot["runtime_capability_snapshot_id"], matrix["observations"])
    if freeze["candidate_freeze_id"] != digest(_freeze_identity_payload(freeze)): raise ValueError("candidate freeze identity does not bind its authoritative payload")
    return freeze


def build_canary_successor(
    predecessor, result, manifest, published_at, *, raw_evidence_root, repository_root,
    expected_telemetry_profile_id=None, expected_treatment_contract_digest=None,
):
    predecessor = validate_freeze(
        predecessor, manifest,
        expected_telemetry_profile_id=expected_telemetry_profile_id,
        expected_treatment_contract_digest=expected_treatment_contract_digest,
        _enforce_lineage=False,
    )
    evidence_bytes = validate_canary_evidence(raw_evidence_root, repository_root, result)
    validated = validate_canary_result(result, APPROVED_CANARY_EXECUTORS, evidence_bytes=evidence_bytes)
    _validate_canary_tuple_binding(predecessor["tuple_decisions"], validated, predecessor["runtime_capability_snapshot_id"], predecessor["surface_matrix"]["observations"])
    results = validate_canary_results([*predecessor["canary_results"], validated], APPROVED_CANARY_EXECUTORS)
    successor = copy.deepcopy(predecessor)
    successor.update({
        "canary_results": results,
        "published_at": published_at,
        "supersedes_candidate_freeze_id": predecessor["candidate_freeze_id"],
    })
    successor["candidate_freeze_id"] = digest(_freeze_identity_payload(successor))
    return validate_freeze(
        successor, manifest, predecessor=predecessor,
        expected_telemetry_profile_id=expected_telemetry_profile_id,
        expected_treatment_contract_digest=expected_treatment_contract_digest,
        expected_predecessor_telemetry_profile_id=expected_telemetry_profile_id,
        expected_predecessor_treatment_contract_digest=expected_treatment_contract_digest,
    )


def _read(path, *, require_canonical=False):
    raw = _read_bounded_regular_file(path)
    value = _parse_json_bytes(raw)
    if require_canonical and raw != canonical_bytes(value) + b"\n":
        raise ValueError("stored JSON artifact is not canonical")
    return value


def _fsync_directory(path):
    if os.name == "nt":
        return
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_private_bytes(path, payload, *, append_only=False):
    if os.name == "nt":
        raise ValueError("operator-only private-file permissions are not supported on Windows")
    if len(payload) > PRIVATE_REFRESH_MAX_BYTES: raise ValueError("private output exceeds the bounded size")
    parent = Path(path).parent
    descriptor, temporary = tempfile.mkstemp(prefix=".g56r-002-", dir=parent)
    try:
        if os.name != "nt":
            os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload); stream.flush(); os.fsync(stream.fileno())
        if append_only:
            os.link(temporary, path)
        else:
            os.replace(temporary, path)
        _fsync_directory(parent)
        if append_only:
            os.unlink(temporary)
            _fsync_directory(parent)
    except Exception:
        try: os.close(descriptor)
        except OSError: pass  # Best-effort cleanup must not mask the original failure.
        try: os.unlink(temporary)
        except OSError: pass  # Best-effort cleanup must not mask the original failure.
        raise


def _write(path, value, *, private=False, append_only=False):
    payload = canonical_bytes(value) + b"\n"
    if private:
        _write_private_bytes(path, payload, append_only=append_only)
        return
    if append_only:
        descriptor, temporary = tempfile.mkstemp(prefix=".g56r-002-publish-", dir=Path(path).parent)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload); stream.flush(); os.fsync(stream.fileno())
            os.link(temporary, path)
            _fsync_directory(Path(path).parent)
        except Exception:
            try: os.close(descriptor)
            except OSError: pass  # Best-effort cleanup must not mask the original failure.
            raise
        finally:
            try: os.unlink(temporary)
            except OSError: pass  # Best-effort cleanup must not mask the original failure.
        return
    Path(path).write_bytes(payload)


def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    refresh = sub.add_parser("refresh-sources"); refresh.add_argument("--manifest", required=True); refresh.add_argument("--captured-refresh", required=True); refresh.add_argument("--raw-evidence-root", required=True); refresh.add_argument("--output", required=True)
    identify = sub.add_parser("identify-client"); identify.add_argument("--reported-version", required=True); group = identify.add_mutually_exclusive_group(required=True); group.add_argument("--build-id"); group.add_argument("--executable"); identify.add_argument("--distribution", required=True); identify.add_argument("--output", required=True)
    collect = sub.add_parser("collect"); collect.add_argument("--surface", choices=SURFACES, required=True); collect.add_argument("--client-identity", required=True); collect.add_argument("--raw-evidence-root", required=True); collect.add_argument("--work-item-kind", choices=("task", "fixture", "objective"), required=True); collect.add_argument("--work-item-id", required=True); collect.add_argument("--output", required=True)
    canary = sub.add_parser("canary"); canary.add_argument("--manifest", required=True); canary.add_argument("--freeze", required=True); canary.add_argument("--model", required=True); canary.add_argument("--effort", required=True); canary.add_argument("--executor-result", required=True); canary.add_argument("--raw-evidence-root", required=True); canary.add_argument("--published-at"); canary.add_argument("--expected-telemetry-profile-id"); canary.add_argument("--expected-treatment-contract-digest"); canary.add_argument("--output", required=True)
    freeze = sub.add_parser("freeze"); freeze.add_argument("--manifest", required=True); freeze.add_argument("--source-refresh", required=True); freeze.add_argument("--client-identity", required=True); freeze.add_argument("--app-server", required=True); freeze.add_argument("--cli", required=True); freeze.add_argument("--interactive-picker", required=True); freeze.add_argument("--raw-evidence-root", required=True); freeze.add_argument("--aliases"); freeze.add_argument("--predecessor-freeze"); freeze.add_argument("--expected-predecessor-telemetry-profile-id"); freeze.add_argument("--expected-predecessor-treatment-contract-digest"); freeze.add_argument("--published-at"); freeze.add_argument("--output", required=True)
    published = sub.add_parser("validate-freeze"); published.add_argument("--manifest", required=True); published.add_argument("--freeze", required=True); published.add_argument("--predecessor-freeze"); published.add_argument("--expected-telemetry-profile-id"); published.add_argument("--expected-treatment-contract-digest"); published.add_argument("--expected-predecessor-telemetry-profile-id"); published.add_argument("--expected-predecessor-treatment-contract-digest")
    retention = sub.add_parser("retention"); retention.add_argument("--raw-evidence-root", required=True); retention.add_argument("--as-of"); retention.add_argument("--mode", choices=("verify", "cleanup"), default="verify"); retention.add_argument("--output", required=True)
    args, repo = parser.parse_args(argv), Path(__file__).resolve().parents[4]
    now = lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if args.command == "refresh-sources":
        _, capture_bytes = read_content_addressed_private_file(args.captured_refresh, repo, "captured refresh")
        capture_digest, _ = materialize_source_capture(args.raw_evidence_root, repo, capture_bytes)
        output = validate_private_external_file(args.output, repo, "normalized refresh output", output=True)
        _write(output, normalize_source_refreshes(_read(args.manifest), _parse_json_bytes(capture_bytes), source_capture_digest=capture_digest), private=True); return 0
    if args.command == "identify-client":
        kind, identifier = ("vendor_build_id", args.build_id) if args.build_id else ("executable_sha256", digest_regular_file(args.executable))
        _write(args.output, build_client_identity({"reported_version": args.reported_version, "build_identifier_kind": kind, "build_identifier": identifier, "distribution": args.distribution})); return 0
    if args.command == "collect":
        validate_raw_evidence_root(args.raw_evidence_root, repo); identity = build_client_identity(_read(args.client_identity))
        binding = repository_binding_from_checkout(repo); work_item = validate_work_item({"kind": args.work_item_kind, "id": args.work_item_id})
        captured_at = now(); raw_digest, _ = materialize_unknown_capture(args.raw_evidence_root, repo, args.surface, identity["client_identity_id"], binding, work_item, captured_at)
        _write(args.output, unknown_observation(args.surface, identity["client_identity_id"], binding, work_item, raw_evidence_digest=raw_digest, captured_at=captured_at)); return 0
    if args.command == "canary":
        if not APPROVED_CANARY_EXECUTORS:
            raise ValueError("no repository-approved canary executor is available in this slice")
        if (args.expected_telemetry_profile_id is None) != (args.expected_treatment_contract_digest is None):
            raise ValueError("treatment-aware canary requires both expected binding arguments")
        validate_raw_evidence_root(args.raw_evidence_root, repo); _, result_bytes = read_private_external_file(args.executor_result, repo, "canary executor result"); result = _parse_json_bytes(result_bytes)
        manifest = _read(args.manifest); predecessor = _read(args.freeze, require_canonical=True)
        if (result.get("snapshot_id"), result.get("canonical_model_id"), result.get("canonical_effort")) != (predecessor.get("runtime_capability_snapshot_id"), args.model, args.effort):
            raise ValueError("canary result does not match the requested tuple")
        successor = build_canary_successor(
            predecessor, result, manifest, args.published_at or now(),
            raw_evidence_root=args.raw_evidence_root, repository_root=repo,
            expected_telemetry_profile_id=args.expected_telemetry_profile_id,
            expected_treatment_contract_digest=args.expected_treatment_contract_digest,
        )
        publish_with_raw_evidence_retention(
            successor, args.output, args.raw_evidence_root, repo, manifest=manifest,
            predecessor=predecessor,
            expected_telemetry_profile_id=args.expected_telemetry_profile_id,
            expected_treatment_contract_digest=args.expected_treatment_contract_digest,
            expected_predecessor_telemetry_profile_id=args.expected_telemetry_profile_id,
            expected_predecessor_treatment_contract_digest=args.expected_treatment_contract_digest,
        )
        return int(successor["canary_results"][-1]["availability_disposition"] == "unknown")
    if args.command == "validate-freeze":
        predecessor = _read(args.predecessor_freeze, require_canonical=True) if args.predecessor_freeze else None
        if (args.expected_telemetry_profile_id is None) != (args.expected_treatment_contract_digest is None):
            raise ValueError("treatment-aware freeze validation requires both expected binding arguments")
        if (args.expected_predecessor_telemetry_profile_id is None) != (args.expected_predecessor_treatment_contract_digest is None):
            raise ValueError("treatment-aware predecessor validation requires both expected binding arguments")
        validate_freeze(
            _read(args.freeze, require_canonical=True), _read(args.manifest), predecessor=predecessor,
            expected_telemetry_profile_id=args.expected_telemetry_profile_id,
            expected_treatment_contract_digest=args.expected_treatment_contract_digest,
            expected_predecessor_telemetry_profile_id=args.expected_predecessor_telemetry_profile_id,
            expected_predecessor_treatment_contract_digest=args.expected_predecessor_treatment_contract_digest,
        ); return 0
    if args.command == "retention":
        if args.mode == "verify" and args.as_of is None: raise ValueError("retention verification requires --as-of")
        if args.mode == "cleanup" and args.as_of is not None: raise ValueError("retention cleanup uses current UTC and does not accept --as-of")
        output = validate_private_external_file(args.output, repo, "retention report output", output=True)
        report = reconcile_raw_evidence_retention(args.raw_evidence_root, repo, args.as_of, apply=args.mode == "cleanup")
        _write(output, report, private=True); return 0
    _, source_refresh_bytes = read_private_external_file(args.source_refresh, repo, "normalized source refresh")
    manifest, refreshes, identity = _read(args.manifest), _parse_json_bytes(source_refresh_bytes), build_client_identity(_read(args.client_identity)); validate_source_refreshes(manifest, refreshes)
    tuples = candidate_tuples_from_manifest(manifest, refreshes)
    aliases = _read(args.aliases) if args.aliases else {}
    matrix, decisions = evaluate_surface_matrix([_read(args.app_server), _read(args.cli), _read(args.interactive_picker)], tuples, aliases=aliases)
    predecessor = _read(args.predecessor_freeze, require_canonical=True) if args.predecessor_freeze else None
    if (args.expected_predecessor_telemetry_profile_id is None) != (args.expected_predecessor_treatment_contract_digest is None):
        raise ValueError("treatment-aware predecessor validation requires both expected binding arguments")
    result = build_freeze(
        identity, refreshes, matrix, decisions, args.published_at or now(), manifest=manifest, predecessor=predecessor,
        raw_evidence_root=args.raw_evidence_root, repository_root=repo,
        expected_predecessor_telemetry_profile_id=args.expected_predecessor_telemetry_profile_id,
        expected_predecessor_treatment_contract_digest=args.expected_predecessor_treatment_contract_digest,
    )
    publish_with_raw_evidence_retention(
        result, args.output, args.raw_evidence_root, repo, manifest=manifest, predecessor=predecessor,
        expected_predecessor_telemetry_profile_id=args.expected_predecessor_telemetry_profile_id,
        expected_predecessor_treatment_contract_digest=args.expected_predecessor_treatment_contract_digest,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
