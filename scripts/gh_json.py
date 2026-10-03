"""Run one `gh` CLI call and return its parsed JSON output.

The one owner for repository scripts that read GitHub through `gh`. Each caller
passes its own error type, so a failure surfaces in the caller's terms.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from typing import Any


def run_gh_json(argv: Sequence[str], error: type[Exception]) -> Any:
    completed = subprocess.run(
        ["gh", *argv],
        text=True,
        capture_output=True,
        check=False,
        shell=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown gh error"
        raise error(f"gh {' '.join(argv[:2])} failed: {detail}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise error("gh returned malformed JSON") from exc
