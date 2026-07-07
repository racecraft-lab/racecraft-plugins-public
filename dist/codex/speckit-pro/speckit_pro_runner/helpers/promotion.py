"""Promotion metadata helpers for mutation-capable runner entries."""

from __future__ import annotations

from typing import Any

SUPPORTED_PROMOTION_STATES = {"golden_only", "bash_compared", "deferred", "out_of_scope"}


def promotion_record(
    helper_id: str,
    *,
    promotion_status: str,
    fixture_ids: list[str] | None = None,
    bash_reference_ids: list[str] | None = None,
    rollback: str | None = None,
) -> dict[str, Any]:
    status = promotion_status if promotion_status in SUPPORTED_PROMOTION_STATES else "deferred"
    return {
        "helper_id": helper_id,
        "promotion_status": status,
        "fixture_ids": sorted(fixture_ids or []),
        "bash_reference_ids": sorted(bash_reference_ids or []),
        "rollback": rollback or "Disable the helper registry entry before active cutover.",
    }
