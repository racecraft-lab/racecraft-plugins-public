"""Exit-status policy shared by repository runner entry points."""

from __future__ import annotations


def shell_compatible_status(returncode: int) -> int:
    """Convert subprocess signal return codes to conventional shell statuses."""
    return 128 + abs(returncode) if returncode < 0 else returncode or 1
