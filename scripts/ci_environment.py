"""Own the clean child environment shared by repository CI dispatchers."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1] / "speckit-pro"


def build_environment(base: Mapping[str, str]) -> dict[str, str]:
    environment = dict(base)
    environment.update(
        {
            "SPECKIT_SKIP_TOOLCHAIN_CHECK": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_SYSTEM": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
            "PYTHONPATH": str(PLUGIN_ROOT),
        }
    )
    return environment

