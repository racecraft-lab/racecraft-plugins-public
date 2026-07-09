#!/usr/bin/env python3
"""Resolve release PR metadata for both new and unchanged Release Please runs.

Release Please only populates its ``prs`` output when it creates or updates a
release pull request. An already-open PR can remain unchanged even though main
contains release-infrastructure fixes that still need to be reconciled onto its
branch. In that case, discover the open Release Please branch directly.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from typing import Any


class ResolutionError(ValueError):
    """Raised when trusted release PR metadata is malformed."""


def parse_json_array(raw: str, label: str) -> list[Any]:
    try:
        value = json.loads(raw or "[]")
    except json.JSONDecodeError as exc:
        raise ResolutionError(f"{label} is not valid JSON: {exc.msg}") from exc
    if not isinstance(value, list):
        raise ResolutionError(f"{label} must be a JSON array")
    return value


def release_branch_prefix(base_ref: str) -> str:
    encoded_base = base_ref.replace("/", "--")
    return f"release-please--branches--{encoded_base}--components--"


def normalize_release_pr(candidate: Any, base_ref: str, *, strict: bool) -> dict[str, Any] | None:
    if not isinstance(candidate, dict):
        if strict:
            raise ResolutionError("release PR entry must be an object")
        return None

    branch = candidate.get("headBranchName") or candidate.get("headRefName") or ""
    candidate_base = candidate.get("baseRefName") or base_ref
    prefix = release_branch_prefix(base_ref)
    cross_repository = candidate.get("isCrossRepository") is True
    if cross_repository or candidate_base != base_ref or not isinstance(branch, str) or not branch.startswith(prefix):
        if strict:
            raise ResolutionError(f"release PR entry does not target {base_ref!r} with prefix {prefix!r}")
        return None
    component = branch.removeprefix(prefix)
    if not component or re.fullmatch(r"[A-Za-z0-9._-]+", component) is None:
        raise ResolutionError(f"unsafe release PR branch: {branch!r}")

    number = candidate.get("number")
    if isinstance(number, str) and number.isdigit():
        number = int(number)
    if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
        raise ResolutionError(f"release PR entry has invalid number: {number!r}")

    title = candidate.get("title") or "chore(release): release speckit-pro"
    if not isinstance(title, str) or not title.strip():
        raise ResolutionError("release PR entry has an invalid title")

    return {
        "number": number,
        "title": title,
        "headBranchName": branch,
    }


def resolve_release_prs(
    release_prs: list[Any], open_prs: list[Any], base_ref: str
) -> list[dict[str, Any]]:
    source = release_prs if release_prs else open_prs
    strict = bool(release_prs)
    resolved: list[dict[str, Any]] = []
    seen: set[tuple[int, str]] = set()
    for candidate in source:
        normalized = normalize_release_pr(candidate, base_ref, strict=strict)
        if normalized is None:
            continue
        identity = (normalized["number"], normalized["headBranchName"])
        if identity in seen:
            continue
        seen.add(identity)
        resolved.append(normalized)
    return sorted(resolved, key=lambda item: (item["number"], item["headBranchName"]))


def fetch_open_prs(base_ref: str) -> list[Any]:
    completed = subprocess.run(
        [
            "gh",
            "pr",
            "list",
            "--state",
            "open",
            "--base",
            base_ref,
            "--limit",
            "100",
            "--json",
            "number,title,headRefName,baseRefName,isCrossRepository",
        ],
        text=True,
        capture_output=True,
        shell=False,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "gh pr list failed").strip()
        raise ResolutionError(detail)
    return parse_json_array(completed.stdout, "open PR inventory")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref", default=os.environ.get("BASE_REF", "main"))
    parser.add_argument(
        "--release-prs-json",
        default=os.environ.get("RELEASE_PRS", "[]"),
        help="Release Please prs output as JSON",
    )
    parser.add_argument(
        "--open-prs-json",
        default=None,
        help="Optional open PR inventory for deterministic tests; otherwise query gh",
    )
    parser.add_argument(
        "--github-output",
        default=None,
        help="Append compact prs/found outputs to this GitHub Actions output file",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        release_prs = parse_json_array(args.release_prs_json, "release-please prs output")
        if release_prs:
            open_prs: list[Any] = []
        elif args.open_prs_json is not None:
            open_prs = parse_json_array(args.open_prs_json, "open PR inventory")
        else:
            open_prs = fetch_open_prs(args.base_ref)
        resolved = resolve_release_prs(release_prs, open_prs, args.base_ref)
    except ResolutionError as exc:
        print(f"resolve-release-prs: {exc}", file=sys.stderr)
        return 2
    compact = json.dumps(resolved, separators=(",", ":"), sort_keys=True)
    if args.github_output:
        output_path = os.path.abspath(args.github_output)
        with open(output_path, "a", encoding="utf-8") as output:
            output.write(f"prs={compact}\n")
            output.write(f"found={'true' if resolved else 'false'}\n")
        if resolved:
            print(f"Release PR reconciliation target: {compact}")
        else:
            print("No open Release Please PR requires reconciliation.")
    else:
        print(compact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
