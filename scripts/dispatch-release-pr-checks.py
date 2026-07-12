#!/usr/bin/env python3
"""Dispatch PR Checks for normalized release-please pull requests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Callable, Mapping
from typing import Any

DEFAULT_TITLE = "chore(release): release speckit-pro"


class DispatchError(ValueError):
    """Release PR metadata or workflow dispatch failed."""


def parse_release_prs(raw: str | None) -> list[dict[str, str]]:
    try:
        value = json.loads(raw or "[]")
    except json.JSONDecodeError as exc:
        raise DispatchError(
            f"RELEASE_PRS is not valid JSON: {exc.msg} "
            f"(line {exc.lineno}, column {exc.colno})"
        ) from exc
    if not isinstance(value, list):
        raise DispatchError("RELEASE_PRS must be a JSON array")
    if not value:
        raise DispatchError("release PR resolver returned no metadata")

    release_prs: list[dict[str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise DispatchError(f"release PR metadata at index {index} must be an object")
        branch_value = item.get("headBranchName") or item.get("headRefName")
        branch = _validated_branch(branch_value, index)
        number = _validated_number(item.get("number"), index)
        title = _validated_title(item.get("title"), index)
        release_prs.append({"branch": branch, "number": number, "title": title})
    return release_prs


def _validated_branch(value: Any, index: int) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DispatchError(f"release PR metadata at index {index} has an invalid branch")
    if len(value) > 255 or value in {"@", "."} or value.startswith(("/", "-")):
        raise DispatchError(f"release PR metadata at index {index} has an invalid branch")
    if value.endswith(("/", ".")) or "//" in value or ".." in value or "@{" in value:
        raise DispatchError(f"release PR metadata at index {index} has an invalid branch")
    if any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in value):
        raise DispatchError(f"release PR metadata at index {index} has an invalid branch")
    if any(character in "~^:?*[\\" for character in value):
        raise DispatchError(f"release PR metadata at index {index} has an invalid branch")
    if any(part.startswith(".") or part.endswith(".lock") for part in value.split("/")):
        raise DispatchError(f"release PR metadata at index {index} has an invalid branch")
    return value


def _validated_number(value: Any, index: int) -> str:
    if isinstance(value, bool):
        raise DispatchError(f"release PR metadata at index {index} has an invalid number")
    if isinstance(value, int):
        number = value
    elif isinstance(value, str) and value.isascii() and value.isdigit():
        number = int(value)
    else:
        raise DispatchError(f"release PR metadata at index {index} has an invalid number")
    if number <= 0:
        raise DispatchError(f"release PR metadata at index {index} has an invalid number")
    return str(number)


def _validated_title(value: Any, index: int) -> str:
    if value is None or value == "":
        return DEFAULT_TITLE
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise DispatchError(f"release PR metadata at index {index} has an invalid title")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise DispatchError(f"release PR metadata at index {index} has an invalid title")
    return value


def dispatch_release_pr_checks(
    release_prs: list[dict[str, str]],
    *,
    run: Callable[..., subprocess.CompletedProcess[Any]] = subprocess.run,
) -> None:
    for release_pr in release_prs:
        argv = [
            "gh",
            "workflow",
            "run",
            "pr-checks.yml",
            "--ref",
            release_pr["branch"],
            "-f",
            f"pr_number={release_pr['number']}",
            "-f",
            f"pr_title={release_pr['title']}",
            "-f",
            "base_ref=main",
        ]
        try:
            run(argv, check=True, shell=False)
        except subprocess.CalledProcessError as exc:
            raise DispatchError(
                f"PR Checks dispatch failed for PR #{release_pr['number']} "
                f"(child exit {exc.returncode})",
            ) from exc
        except OSError as exc:
            raise DispatchError(
                f"PR Checks dispatch failed for PR #{release_pr['number']}: {exc}"
            ) from exc


def main(
    environment: Mapping[str, str] | None = None,
    *,
    run: Callable[..., subprocess.CompletedProcess[Any]] = subprocess.run,
) -> int:
    environment = os.environ if environment is None else environment
    try:
        release_prs = parse_release_prs(environment.get("RELEASE_PRS"))
        dispatch_release_pr_checks(release_prs, run=run)
    except DispatchError as exc:
        print(f"dispatch-release-pr-checks: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
