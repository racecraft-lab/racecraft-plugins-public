#!/usr/bin/env python3
"""Refresh repository proof data after reviewing Codex instruction changes."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "speckit-pro"))

from codex_instruction_review import REVIEW_INVENTORY, instruction_inventory, review_inventory_document
from speckit_pro_runner.atomic_write import AtomicWriteOptions, WriteBinding, write_bytes_atomic_with_options  # noqa: E402
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
        content = (json.dumps(inventory, indent=2, sort_keys=True) + "\n").encode("utf-8")
        write_bytes_atomic_with_options(
            REVIEW_INVENTORY, content,
            AtomicWriteOptions(trust_root=REPO_ROOT, binding=WriteBinding(parent_fd)),
        )
    finally:
        os.close(parent_fd)


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    with tempfile.TemporaryDirectory() as temporary:
        skills = Path(temporary) / "skills"
        render_host_skills(REPO_ROOT / "speckit-pro", "codex", skills)
        inventory = review_inventory_document(
            instruction_inventory(REPO_ROOT / "speckit-pro/codex-agents"),
            instruction_inventory(skills),
        )
    write_inventory(inventory)
    print("Wrote instruction inventory. Review source changes and the inventory diff together.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
