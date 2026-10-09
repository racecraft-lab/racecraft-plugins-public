#!/usr/bin/env python3
"""Authenticate manual PR metadata against the selected workflow ref and SHA."""

from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from superseded_run import COMMIT_SHA_PATTERN, REPOSITORY_PATTERN, Fetch, github_fetch


def validate_dispatch_context(environment: Mapping[str, str]) -> None:
    if environment["GITHUB_EVENT_NAME"] != "workflow_dispatch":
        raise ValueError("metadata authentication requires a manual dispatch")
    patterns: dict[str, str | re.Pattern[str]] = {
        "GITHUB_REPOSITORY": REPOSITORY_PATTERN,
        "PR_NUMBER": r"[1-9][0-9]*",
        "GITHUB_REF": r"refs/heads/.+",
        "GITHUB_SHA": COMMIT_SHA_PATTERN,
    }
    for field, pattern in patterns.items():
        if not re.fullmatch(pattern, environment[field]):
            raise ValueError(f"missing or invalid {field}")


def manual_pr_metadata(environment: Mapping[str, str], *, fetch: Fetch) -> dict[str, Any]:
    validate_dispatch_context(environment)
    repository = environment["GITHUB_REPOSITORY"]
    number = environment["PR_NUMBER"]
    pr = fetch(f"/repos/{repository}/pulls/{number}")
    if type(pr["number"]) is not int:
        raise ValueError("PR number must be an integer")
    bindings = (
        (pr["number"], int(number), "PR number"),
        (pr["base"]["repo"]["full_name"], repository, "base repository"),
        (pr["head"]["repo"]["full_name"], repository, "head repository"),
        (pr["head"]["ref"], environment["GITHUB_REF"].removeprefix("refs/heads/"), "head branch"),
        (pr["head"]["sha"], environment["GITHUB_SHA"], "head SHA"),
        (pr["state"], "open", "PR state"),
    )
    for actual, expected, field in bindings:
        if actual != expected:
            raise ValueError(f"live {field} does not match the manual dispatch")
    return validated_metadata(pr)


def validated_metadata(pr: Mapping[str, Any]) -> dict[str, Any]:
    field_types: dict[str, type | tuple[type, ...]] = {
        "title": str, "body": (str, type(None)), "labels": list, "draft": bool,
    }
    for field, expected_type in field_types.items():
        if not isinstance(pr[field], expected_type):
            raise ValueError(f"invalid live PR {field}")
    if not pr["title"]:
        raise ValueError("live PR title is empty")
    labels = [label["name"] for label in pr["labels"]]
    if any(not isinstance(label, str) or not label for label in labels):
        raise ValueError("invalid live PR label name")
    return {
        "title": pr["title"],
        "body": pr["body"] or "",
        "labels": labels,
        "draft": pr["draft"],
    }


def main(environment: Mapping[str, str] | None = None, *, fetch: Fetch | None = None) -> int:
    env = os.environ if environment is None else environment
    try:
        api = fetch or github_fetch(env["GH_TOKEN"], env["GITHUB_API_URL"])
        metadata = manual_pr_metadata(env, fetch=api)
        with Path(env["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
            output.write(f"metadata={json.dumps(metadata, ensure_ascii=True)}\n")
    except (KeyError, TypeError, ValueError, OSError) as exc:
        print(f"error: could not authenticate manual PR metadata: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
