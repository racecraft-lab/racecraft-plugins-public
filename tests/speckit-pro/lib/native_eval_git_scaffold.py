"""Claude scaffold script that materializes a v2 Git fixture in the eval workspace.

The adapter copies this file, ``native_eval_fixture_setup.py`` and
``native_eval_strict_json.py`` beside the case inputs, and ``fixture.sh`` runs
it with the workspace as the working directory. Optional inputs decide the
variant:

- one absolute argument names the controller-owned receipt path; without it the
  receipt is written to ``fixture-receipt.json`` beside this file;
- ``git-controller-exclude.bin`` holds the controller entries for the Git
  exclude file; without it the entries are empty;
- ``upstream-identity.json`` makes the script stage the serialized upstream
  integration (``native_eval_upstream.py`` is staged with it) after the receipt.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import sys

import native_eval_fixture_setup as setup


def write_exclude(workspace: Path, controller_exclude: bytes, include_worktrees: bool) -> None:
    git_directory = workspace / ".git"
    status = git_directory.lstat()
    if not stat.S_ISDIR(status.st_mode) or stat.S_ISLNK(status.st_mode):
        raise ValueError("git fixture control directory is unsafe")
    info_directory = git_directory / "info"
    try:
        info_directory.mkdir(mode=0o700)
    except FileExistsError:
        pass
    status = info_directory.lstat()
    if not stat.S_ISDIR(status.st_mode) or stat.S_ISLNK(status.st_mode):
        raise ValueError("git fixture info directory is unsafe")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(info_directory / "exclude", flags, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(controller_exclude + (b"/.worktrees/\n" if include_worktrees else b""))
        stream.flush()
        os.fsync(stream.fileno())


def receipt_path(root: Path, arguments: list[str]) -> Path:
    if not arguments:
        return root / "fixture-receipt.json"
    if len(arguments) != 1:
        raise ValueError("controller receipt path is required")
    path = Path(arguments[0])
    if not path.is_absolute():
        raise ValueError("controller receipt path must be absolute")
    return path


def main(arguments: list[str] | None = None) -> int:
    root = Path(__file__).resolve(strict=True).parent
    receipt = receipt_path(root, list(sys.argv[1:] if arguments is None else arguments))
    exclude_file = root / "git-controller-exclude.bin"
    controller_exclude = exclude_file.read_bytes() if exclude_file.exists() else b""
    workspace = setup.workspace_directory(Path.cwd())
    result = {
        "schema_version": setup.GIT_SCHEMA_VERSION,
        **setup.materialize_workspace(setup.load_plan(root / "fixture-plan.json"), workspace),
    }
    write_exclude(workspace, controller_exclude, "worktrees" in result)
    setup.snapshot_git_repository_controls(workspace)
    setup.write_receipt(receipt, result)
    if (root / "upstream-identity.json").exists():
        import native_eval_upstream as upstream
        upstream.stage_serialized(
            root / "upstream-controller" / "specify-claude", workspace,
            root / "upstream-identity.json",
        )
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
