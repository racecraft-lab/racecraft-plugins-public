"""Own the changed-path selection policy for PR Checks."""

from __future__ import annotations

from collections.abc import Iterable

MODULE_DIR = "typesafe-jev"
# A change to the module, to this wrapper, or to the workflow that runs it can
# change the Go result, so each one runs the Go job.
TRIGGER_PATHS = frozenset(
    {"scripts/check-go-module.py", "scripts/changed_files.py", ".github/workflows/pr-checks.yml"}
)


def go_module_changed(changed_files: Iterable[str]) -> bool:
    for file_path in changed_files:
        if file_path.startswith(f"{MODULE_DIR}/") or file_path in TRIGGER_PATHS:
            return True
    return False

