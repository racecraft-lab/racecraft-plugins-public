#!/usr/bin/env python3
"""Resolve PR-event metadata or authenticate manual dispatch against the live PR.

This repository CI policy is shared by the title and release-note jobs. Dispatch
inputs identify a PR; they never supply metadata for either validator.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from gh_json import run_gh_json


class MetadataError(ValueError):
    """The event or API response cannot authenticate the metadata being checked."""


def metadata_fields(pull: Any) -> dict[str, Any]:
    """Validate the complete metadata shape before emitting any job output."""
    if not isinstance(pull, dict):
        raise MetadataError("pull request metadata is not an object")
    title, body, labels, draft = (pull.get(key) for key in ("title", "body", "labels", "draft"))
    if not isinstance(title, str) or "body" not in pull or (body is not None and not isinstance(body, str)):
        raise MetadataError("pull request title or body is missing or malformed")
    if type(draft) is not bool or not isinstance(labels, list):
        raise MetadataError("pull request labels or draft state is missing or malformed")
    names = []
    for label in labels:
        if not isinstance(label, dict) or not isinstance(label.get("name"), str):
            raise MetadataError("pull request label is malformed")
        names.append(label["name"])
    return {"title": title, "body": body or "", "labels": names, "draft": draft}


def bind_dispatch(pull: Any, number: str, repository: str, ref: str, sha: str) -> None:
    """Reject a dispatch unless the response identifies its exact open PR head."""
    try:
        identity = (
            pull["number"], pull["state"], pull["base"]["repo"]["full_name"],
            pull["head"]["repo"]["full_name"], f"refs/heads/{pull['head']['ref']}", pull["head"]["sha"],
        )
    except (KeyError, TypeError) as error:
        raise MetadataError("pull request head identity is missing or malformed") from error
    if type(identity[0]) is not int or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise MetadataError("pull request number or workflow SHA is malformed")
    if identity != (int(number), "open", repository, repository, ref, sha):
        raise MetadataError("dispatch does not match the referenced open pull request's repository, branch and head SHA")


def resolve_metadata(
    event_name: str,
    event: Any,
    repository: str,
    ref: str,
    sha: str,
    *,
    api: Callable[[Sequence[str], type[Exception]], Any] = run_gh_json,
) -> dict[str, Any]:
    """Use signed event text for PR runs and a fresh API response for dispatch."""
    if not isinstance(event, dict):
        raise MetadataError("event is not an object")
    if event_name == "pull_request":
        return metadata_fields(event.get("pull_request"))
    if event_name != "workflow_dispatch":
        raise MetadataError("unsupported metadata event")
    inputs = event.get("inputs")
    number = inputs.get("pr_number") if isinstance(inputs, dict) else None
    if not isinstance(number, str) or not re.fullmatch(r"[1-9][0-9]*", number):
        raise MetadataError("dispatch requires a positive pull request number")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise MetadataError("workflow repository is malformed")
    pull = api(["api", f"repos/{repository}/pulls/{number}"], MetadataError)
    bind_dispatch(pull, number, repository, ref, sha)
    return metadata_fields(pull)


def main(environment: Mapping[str, str] | None = None) -> int:
    env = os.environ if environment is None else environment
    try:
        event = json.loads(Path(env["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8"))
        metadata = resolve_metadata(env["GITHUB_EVENT_NAME"], event, env["GITHUB_REPOSITORY"], env["GITHUB_REF"], env["GITHUB_SHA"])
        # JSON escapes newlines/control characters, so event text cannot inject
        # additional output keys or delimiters into the runner's output file.
        with Path(env["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
            output.write(f"metadata={json.dumps(metadata, separators=(',', ':'))}\n")
            output.write(f"draft={str(metadata['draft']).lower()}\n")
        if env["GITHUB_EVENT_NAME"] == "workflow_dispatch":
            with Path(env["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as summary:
                summary.write("Manual PR metadata validation: these job checks do not satisfy required pull request checks.\n")
    except (MetadataError, KeyError, OSError, json.JSONDecodeError) as error:
        print(f"PR metadata resolution failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
