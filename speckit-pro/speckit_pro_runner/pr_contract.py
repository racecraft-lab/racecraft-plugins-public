"""The pull-request title, packet-path, and deferred-item shapes that every runner surface shares.

The PR packet schema, the packet normalizer, the live PR-title gate, and
`finalize-run` all read these values, so a title or a deferred item that one of
them accepts is one the others accept too. The packet schema is JSON and cannot
import them; a unit test proves its patterns equal the ones built here.
Packet normalization, validation, and mutation guards share the canonical
packet paths here without importing one another.
"""

from __future__ import annotations

import re
from typing import Any

TITLE_TYPES = ("feat", "fix", "chore", "docs", "refactor", "test")
# Lowercase only: the release gate and the repository agent contract both reject an uppercase scope.
TITLE_SCOPE_PATTERN = r"[a-z0-9-]+"
TITLE_DESCRIPTION_PATTERN = r"[A-Za-z][A-Za-z0-9 ,.'()/-]+"
# The packet schema's generated_title.value and generated_title.scope patterns.
PACKET_TITLE_SCOPE_PATTERN = f"^{TITLE_SCOPE_PATTERN}$"
PACKET_TITLE_VALUE_PATTERN = rf"^[a-z]+\({TITLE_SCOPE_PATTERN}\): {TITLE_DESCRIPTION_PATTERN}$"
# The live PR-title gate: any description after the scope.
GATE_TITLE_PATTERN = rf"^({'|'.join(TITLE_TYPES)})\({TITLE_SCOPE_PATTERN}\): .+"

# One deferred item in a PR body's "Deferred / not verified" section, and the human-UAT record behind it.
DEFERRED_ITEM_FIELDS = ("item", "reason", "finish")


def is_one_line(text: str) -> bool:
    """True when `text` is non-blank and holds no line break."""
    return bool(text.strip()) and re.search(r"[\r\n]", text) is None


def require_one_line(text: str, field: str) -> str:
    """`text` itself, or a ValueError naming `field` when it breaks across lines."""
    if is_one_line(text):
        return text
    raise ValueError(f"{field} must be one line; the PR body renders each deferred field on one line")


PACKET_SLUG = r"[a-z0-9][a-z0-9._-]*"


SOURCE_FEATURE_PATTERN = re.compile(rf"^specs/(?P<feature>{PACKET_SLUG})$")


PACKET_PATH_PATTERN = re.compile(
    rf"^(?P<source_feature_dir>specs/{PACKET_SLUG})/\.process/pr-packets/(?P<packet_id>{PACKET_SLUG})\.json$"
)


def packet_path_parts(packet_path: Any) -> dict[str, str] | None:
    if not isinstance(packet_path, str):
        return None
    match = PACKET_PATH_PATTERN.fullmatch(packet_path)
    if match is None:
        return None
    return {"source_feature_dir": match.group("source_feature_dir"), "packet_id": match.group("packet_id")}


def canonical_packet_paths(source_feature_dir: str, packet_id: str) -> dict[str, str]:
    return {
        "packet_path": f"{source_feature_dir}/.process/pr-packets/{packet_id}.json",
        "body_file": f"{source_feature_dir}/.process/pr-packets/{packet_id}/body.md",
        "validation_result_path": f"{source_feature_dir}/.process/pr-packets/{packet_id}/validation.json",
    }
