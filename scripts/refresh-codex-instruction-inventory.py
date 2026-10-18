#!/usr/bin/env python3
"""Refresh repository proof data after reviewing Codex instruction changes."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import stat
import sys
import tempfile
from contextlib import suppress
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "speckit-pro"))

from codex_instruction_review import REVIEW_INVENTORY, instruction_inventory
from speckit_pro_runner.host_skills import render_host_skills  # noqa: E402
from speckit_pro_runner.trusted_io import trusted_open_directory  # noqa: E402


def write_inventory(inventory: dict[str, dict[str, str]]) -> None:
    """Replace only the inventory entry, relative to a held, unlinked parent.

    Never truncate an existing inode: even a hard link must leave its other
    names untouched. Directory descriptors keep parent swaps from redirecting
    either temporary-file creation or publication.
    """
    parent_fd = trusted_open_directory(REVIEW_INVENTORY.parent, REPO_ROOT)
    if parent_fd is None:
        raise OSError("inventory parent is missing, linked, or unsupported")
    try:
        with suppress(FileNotFoundError):
            info = os.stat(REVIEW_INVENTORY.name, dir_fd=parent_fd, follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode):
                raise OSError("inventory output must be a regular file, not a link")
        temporary = f".{REVIEW_INVENTORY.name}.{secrets.token_hex(8)}.tmp"
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644, dir_fd=parent_fd)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(json.dumps(inventory, indent=2, sort_keys=True) + "\n")
            os.replace(temporary, REVIEW_INVENTORY.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
        finally:
            with suppress(FileNotFoundError):
                os.unlink(temporary, dir_fd=parent_fd)
    finally:
        os.close(parent_fd)


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    with tempfile.TemporaryDirectory() as temporary:
        skills = Path(temporary) / "skills"
        render_host_skills(REPO_ROOT / "speckit-pro", "codex", skills)
        inventory = {
            "skills": instruction_inventory(skills),
            "agents": instruction_inventory(REPO_ROOT / "speckit-pro/codex-agents"),
        }
    write_inventory(inventory)
    print("Wrote instruction inventory. Review source changes and the inventory diff together.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
