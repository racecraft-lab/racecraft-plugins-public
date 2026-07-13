#!/usr/bin/env python3
"""Keep Release Please pull requests draft until generated artifacts are synchronized."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from typing import Any

from resolve_release_prs import (
    ResolutionError,
    fetch_open_prs,
    parse_json_array,
    resolve_release_prs,
)


class LifecycleError(RuntimeError):
    """Raised when a release pull request cannot transition safely."""


class CommandRunner:
    def output(self, argv: Sequence[str]) -> str:
        if not argv or argv[0] != "gh":
            raise LifecycleError("release PR lifecycle only supports gh commands")
        completed = subprocess.run(
            ["gh", *argv[1:]],
            text=True,
            capture_output=True,
            shell=False,
            check=False,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            raise LifecycleError(detail or f"command failed ({completed.returncode}): {' '.join(argv)}")
        return completed.stdout.strip()

    def run(self, argv: Sequence[str]) -> None:
        if not argv or argv[0] != "gh":
            raise LifecycleError("release PR lifecycle only supports gh commands")
        completed = subprocess.run(
            ["gh", *argv[1:]],
            text=True,
            capture_output=True,
            shell=False,
            check=False,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            raise LifecycleError(detail or f"command failed ({completed.returncode}): {' '.join(argv)}")


def lifecycle_targets(
    release_prs_raw: str,
    base_ref: str,
    *,
    fetch_open=fetch_open_prs,
) -> list[dict[str, Any]]:
    release_prs = parse_json_array(release_prs_raw, "release PR lifecycle metadata")
    open_prs = [] if release_prs else fetch_open(base_ref)
    return resolve_release_prs(release_prs, open_prs, base_ref)


def set_draft_state(
    release_prs: list[dict[str, Any]],
    *,
    draft: bool,
    runner: CommandRunner,
) -> None:
    for release_pr in release_prs:
        number = release_pr["number"]
        try:
            state = json.loads(
                runner.output(["gh", "pr", "view", str(number), "--json", "isDraft"])
            )
        except json.JSONDecodeError as exc:
            raise LifecycleError(f"PR #{number} returned malformed draft state") from exc
        current = state.get("isDraft") if isinstance(state, dict) else None
        if not isinstance(current, bool):
            raise LifecycleError(f"PR #{number} returned an invalid draft state")
        if current == draft:
            print(f"PR #{number}: already {'draft' if draft else 'ready'}")
            continue

        command = ["gh", "pr", "ready", str(number)]
        if draft:
            command.append("--undo")
        runner.run(command)
        print(f"PR #{number}: marked {'draft' if draft else 'ready'}")


def main(
    argv: Sequence[str] | None = None,
    environment: Mapping[str, str] | None = None,
    *,
    runner: CommandRunner | None = None,
    fetch_open=fetch_open_prs,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", choices=("hold", "ready"))
    args = parser.parse_args(argv)
    environment = os.environ if environment is None else environment
    base_ref = environment.get("BASE_REF", "main")
    try:
        targets = lifecycle_targets(
            environment.get("RELEASE_PRS", "[]"),
            base_ref,
            fetch_open=fetch_open,
        )
        if args.state == "ready" and not targets:
            raise LifecycleError("release PR resolver returned no metadata")
        set_draft_state(
            targets,
            draft=args.state == "hold",
            runner=runner or CommandRunner(),
        )
    except (LifecycleError, ResolutionError, json.JSONDecodeError) as exc:
        print(f"release-pr-lifecycle: {exc}", file=sys.stderr)
        return 1
    if not targets:
        print("No open Release Please PR requires a draft hold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
