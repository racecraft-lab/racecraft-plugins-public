"""Shared readiness item values and privacy validation; independent of record and host observers."""

from __future__ import annotations

import re
from typing import Any

from ..strict_input import SelectionError, require_text
from ..sweep_isolation import secret_matches

MAX_TEXT = 400
NOT_OBSERVED_ACTION = "Run the preparation check for this item, then rerun scaffold."
# Keep the supported scaffold slash commands; refuse absolute paths, including roots and UNC paths.
LOCAL_PATH_RE = re.compile(
    r"(?<![\w./\\-])(?:/(?!speckit-pro:[a-z][a-z0-9-]*(?=[^\w/\\-]|$)|"
    r"(?:plugin|reload-plugins|hooks|mcp)(?=[^\w/\\-]|$))[^\s]*|~[/\\]|[A-Za-z]:[\\/]|\\|file://)")


def clean_text(value: Any, label: str) -> str:
    """Text that may be written to the record: one short line, no credential, no absolute path."""
    text = require_text(value, label).strip()
    if len(text) > MAX_TEXT or "\n" in text or "\r" in text:
        raise SelectionError(f"{label} must be one line of at most {MAX_TEXT} characters")
    if secret_matches(text):
        raise SelectionError(f"{label} looks like a credential; the record never stores one")
    if LOCAL_PATH_RE.search(text):
        raise SelectionError(f"{label} holds an absolute local path; use a repository-relative path")
    return text


def make_item(status: str, evidence_source: str, observed_at: str, fingerprints: dict[str, str],
              action: str | None = None) -> dict[str, Any]:
    required = {"action": action} if action is not None else {}
    return {"status": status, "evidence_source": evidence_source, "observed_at": observed_at,
            "fingerprints": fingerprints, **required}


