#!/usr/bin/env python3
"""Descriptor-relative retention recovery helpers."""

from __future__ import annotations

if __package__:
    from .codex_capability_publication_records import *
else:
    from codex_capability_publication_records import *


def _unlink_descriptor_relative(filename, parent_descriptor):
    os.unlink(filename, dir_fd=parent_descriptor)


def _descriptor_entry_exists(parent_descriptor, filename):
    try:
        os.stat(filename, dir_fd=parent_descriptor, follow_symlinks=False)
        return True
    except FileNotFoundError:
        return False


__all__ = [name for name in globals() if not name.startswith("__")]
