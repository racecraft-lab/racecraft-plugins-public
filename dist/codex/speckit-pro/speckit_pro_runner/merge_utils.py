"""Shared merge helpers for runner fixture overlays."""

from __future__ import annotations

import copy
from typing import Any

__all__ = ("deep_merge",)


def deep_merge(target: dict[str, Any], overrides: dict[str, Any]) -> None:
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            deep_merge(target[key], value)
        else:
            target[key] = copy.deepcopy(value)
