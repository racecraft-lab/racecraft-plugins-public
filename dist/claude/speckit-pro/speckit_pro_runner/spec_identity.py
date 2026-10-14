"""Shared namespace and number identity for spec IDs and directories."""

from __future__ import annotations

import re


def normalize_spec_identity(value: str) -> str:
    parts = value.lower().split("-")
    first = parts[0] if parts else ""
    if re.fullmatch(r"[a-z]+", first):
        namespace = first
        number_suffix = parts[1] if len(parts) > 1 else ""
    else:
        namespace = "spec"
        number_suffix = first
    return f"{namespace} {number_suffix}"
