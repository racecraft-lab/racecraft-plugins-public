#!/usr/bin/env python3
"""Local-identity patterns the repository privacy scan rejects, and their redaction.

``tests/speckit-pro/unit/test-privacy-scan.py`` fails the tree on any match of
these patterns. ``redact_private_text`` replaces the same matches with
placeholders, so text kept in a committed fixture (such as a Layer 6 dispatch
prompt) passes that scan by construction.
"""

from __future__ import annotations

import re

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9_.%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", re.IGNORECASE)
HOME_PATH_PATTERN = re.compile(
    r"(?:/(?:Users|home)/|[A-Za-z]:[\\/]+Users[\\/]+)[A-Za-z0-9_.\-]+",
    re.IGNORECASE,
)
HYPHENATED_HOME_PATH_PATTERN = re.compile(r"-Users-[A-Za-z0-9_.\-]+", re.IGNORECASE)
PRIVATE_VAR_PATTERN = re.compile(r"/private/var/folders/[A-Za-z0-9_/\.\-]+", re.IGNORECASE)
TMP_TRANSCRIPT_PATTERN = re.compile(r"/private/tmp/claude-[0-9]+", re.IGNORECASE)
UUID_PATTERN = re.compile(
    r"[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}",
    re.IGNORECASE,
)
# Controller-owned, no-network Git identity used only by native-eval fixtures.
ALLOWED_EMAILS = {"support@openai.com", "git@github.com", "native-eval@example.invalid"}

# Temp paths first: a temp transcript path embeds a hyphenated home path.
_REDACTIONS: tuple[tuple[re.Pattern[str], str], ...] = (
    (TMP_TRANSCRIPT_PATTERN, "<TMP>"),
    (PRIVATE_VAR_PATTERN, "<TMP>"),
    (HOME_PATH_PATTERN, "<HOME>"),
    (HYPHENATED_HOME_PATH_PATTERN, "<HOME>"),
    (UUID_PATTERN, "<scrubbed-uuid>"),
)


def _redact_email(match: re.Match[str]) -> str:
    return match.group(0) if match.group(0).lower() in ALLOWED_EMAILS else "<EMAIL>"


def redact_private_text(text: str) -> str:
    """Replace every privacy-scan match in ``text`` with a placeholder."""
    for pattern, placeholder in _REDACTIONS:
        text = pattern.sub(placeholder, text)
    return EMAIL_PATTERN.sub(_redact_email, text)
