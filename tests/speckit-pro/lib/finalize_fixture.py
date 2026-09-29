"""Run the finalize-run helper over a frozen fixture, the way a native eval case stages it."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3] / "speckit-pro"


def run_finalize_fixture(directory: Path) -> tuple[dict, dict]:
    """The fixture's `finalize-request.json` and the result the runner derives from it and its `ledger.json`."""
    if str(PLUGIN_ROOT) not in sys.path:
        sys.path.insert(0, str(PLUGIN_ROOT))
    from speckit_pro_runner.helpers.run_finalization import finalize_run

    request = json.loads((directory / "finalize-request.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as temp:
        ledger = Path(temp) / ".process/execution-control/ledger.json"
        ledger.parent.mkdir(parents=True)
        ledger.write_text((directory / "ledger.json").read_text(encoding="utf-8"), encoding="utf-8")
        return request, finalize_run(Path(temp), request["inputs"])
