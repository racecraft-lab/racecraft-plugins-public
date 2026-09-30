"""List the files a pull request changes against its base branch."""

from __future__ import annotations

import subprocess
from pathlib import Path


def changed_files_for_base(
    base_ref: str,
    *,
    repo_root: Path,
    error: type[Exception],
) -> tuple[str, ...]:
    """Files changed between ``origin/<base_ref>`` and HEAD; failures raise ``error``."""
    if not base_ref:
        raise error("BASE_REF is not set")
    try:
        completed = subprocess.run(
            ["git", "diff", "--name-only", f"origin/{base_ref}...HEAD"],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=True,
            shell=False,
        )
    except subprocess.CalledProcessError as failure:
        detail = (failure.stderr or "").strip()
        suffix = f": {detail}" if detail else ""
        raise error(
            f"git changed-file detection failed with exit code {failure.returncode}{suffix}"
        ) from failure
    except OSError as failure:
        raise error(f"unable to run git changed-file detection: {failure}") from failure
    return tuple(completed.stdout.splitlines())
