"""Own the changed-path selection policy for PR Checks."""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from pathlib import PurePosixPath

MODULE_DIR = "typesafe-jev"
# A change to the module, to this wrapper, or to the workflow that runs it can
# change the Go result, so each one runs the Go job.
TRIGGER_PATHS = frozenset(
    {"scripts/check-go-module.py", "scripts/changed_files.py", ".github/workflows/pr-checks.yml",
     "scripts/ci_selection.py", "scripts/emit-plugin-matrix.py"}
)


def go_module_changed(changed_files: Iterable[str]) -> bool:
    for file_path in changed_files:
        if file_path.startswith(f"{MODULE_DIR}/") or file_path in TRIGGER_PATHS:
            return True
    return False


# Only this exact external page is dedicated to the plugin. Shared docs and
# generated references can affect speckit-pro and deliberately run the full suite.
TYPESAFE_DOCS = frozenset({"docs-site/src/content/docs/install/typesafe-jev.md"})
REPOSITORY_CHECKS = (
    "tests/speckit-pro/unit/test-privacy-scan.py",
    "tests/speckit-pro/layer1-structural/validate-typesafe-jev-metadata.py",
    "tests/speckit-pro/layer1-structural/validate-plugin-metadata.py",
    "tests/speckit-pro/layer1-structural/validate-instruction-files.py",
    "tests/speckit-pro/layer1-structural/validate-docs-layout.py",
    "tests/speckit-pro/layer1-structural/validate-doc-test-layer-paths.py",
    "tests/speckit-pro/unit/test-typesafe-jev-release-build.py",
)
REPOSITORY_GATE_REQUEST = (
    "tests/speckit-pro/unit/fixtures/repository-bash-confinement/requests/repo-bash-confinement.json"
)


def typesafe_only_path(path: str) -> bool:
    """Accept canonical relative file paths in the explicit reduced-suite set."""
    if not path or path != PurePosixPath(path).as_posix() or ".." in path.split("/"):
        return False
    return path.startswith("typesafe-jev/") or path in TYPESAFE_DOCS


def select_checks(changed_files: Sequence[str] | None) -> dict[str, str]:
    """Unknown/empty evidence runs the full suite and Go; unknown paths run full."""
    if not changed_files or any(not path.strip() for path in changed_files):
        return {"plugins": '["speckit-pro"]', "repository_checks": "false", "run_go": "true"}
    reduced = all(typesafe_only_path(path) for path in changed_files)
    return {
        "plugins": json.dumps([] if reduced else ["speckit-pro"], separators=(",", ":")),
        "repository_checks": str(reduced).lower(),
        "run_go": str(reduced or go_module_changed(changed_files)).lower(),
    }
