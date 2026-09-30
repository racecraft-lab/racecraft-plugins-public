"""Claude scaffold script that populates the workspace and stages the upstream integration.

The adapter copies this file with ``native_eval_fixture_setup.py``,
``native_eval_strict_json.py``, ``native_eval_upstream.py`` and
``native_eval_toolchain.py`` beside the case inputs, and ``fixture.sh`` runs it
with the workspace as the working directory.
"""

from __future__ import annotations

from pathlib import Path

import native_eval_fixture_setup as setup
import native_eval_upstream as upstream


def main() -> int:
    root = Path(__file__).resolve(strict=True).parent
    workspace = setup.workspace_directory(Path.cwd())
    setup.populate_workspace(setup.load_plan(root / "fixture-plan.json"), workspace)
    upstream.stage_serialized(
        root / "upstream-controller" / "specify-claude",
        workspace,
        root / "upstream-identity.json",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
