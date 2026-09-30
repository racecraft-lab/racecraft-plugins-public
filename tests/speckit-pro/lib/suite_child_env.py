"""The environment both suite dispatchers give each test child process."""

from __future__ import annotations

import os
from pathlib import Path

# Scripts run in parallel, and git's detached auto-maintenance can create and
# delete .git/objects/maintenance.lock while a fixture walks .git.
GIT_CONFIG = (("commit.gpgsign", "false"), ("maintenance.auto", "false"), ("gc.auto", "0"))


def child_environment(repo_root: Path, *, verbose: bool = False) -> dict[str, str]:
    env = os.environ.copy()
    plugin_root = (repo_root / "speckit-pro").as_posix()
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = plugin_root if not existing else f"{plugin_root}{os.pathsep}{existing}"
    env["GIT_CONFIG_COUNT"] = str(len(GIT_CONFIG))
    for index, (key, value) in enumerate(GIT_CONFIG):
        env[f"GIT_CONFIG_KEY_{index}"] = key
        env[f"GIT_CONFIG_VALUE_{index}"] = value
    if verbose:
        env["VERBOSE"] = "true"
    return env
