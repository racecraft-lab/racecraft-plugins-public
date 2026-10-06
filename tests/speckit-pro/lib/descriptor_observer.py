"""Observe descriptor ownership without closing anything on the caller's behalf."""

from collections.abc import Iterator
from contextlib import contextmanager
import os
from typing import Any
from unittest.mock import patch


@contextmanager
def record_open_descriptors() -> Iterator[list[int]]:
    """Record successful OS opens during a call, including reused descriptor numbers."""
    descriptors: list[int] = []
    real_open = os.open

    def record(*args: Any, **kwargs: Any) -> int:
        descriptors.append(real_open(*args, **kwargs))
        return descriptors[-1]

    with patch.object(os, "open", record):
        yield descriptors
