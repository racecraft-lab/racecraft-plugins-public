#!/usr/bin/env python3
"""Canonical public and private publication I/O."""

from __future__ import annotations

if __package__:
    from .codex_capability_freeze import *
else:
    from codex_capability_freeze import *

def _read(path, *, require_canonical=False):
    raw = _read_bounded_regular_file(path)
    value = _parse_json_bytes(raw)
    if require_canonical and raw != canonical_bytes(value) + b"\n":
        raise ValueError("stored JSON artifact is not canonical")
    return value

__all__ = [name for name in globals() if not name.startswith("__")]
