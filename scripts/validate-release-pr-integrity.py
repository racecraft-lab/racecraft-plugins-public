#!/usr/bin/env python3
"""Fail closed when a generated release PR drops a cited fix commit."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections.abc import Callable, Sequence
from typing import Any


RELEASE_BRANCH_PREFIX = "release-please--branches--"
TRUSTED_ASSOCIATIONS = frozenset({"OWNER", "MEMBER", "COLLABORATOR"})
RESOLUTION_CLAIM_RE = re.compile(
    r"\b(?:addressed|fixed|implemented|landed|resolved|retained)\b", re.IGNORECASE
)
COMMIT_CITATION_RE = re.compile(
    r"(?<![0-9A-Fa-f])`?([0-9A-Fa-f]{7,40})`?(?![0-9A-Fa-f])"
)
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

THREAD_COMMENTS_QUERY = """
query($thread:ID!,$after:String){
  node(id:$thread){
    ... on PullRequestReviewThread{
      comments(first:100,after:$after){
        nodes{body authorAssociation url}
        pageInfo{hasNextPage endCursor}
      }
    }
  }
}
""".strip()


class IntegrityError(RuntimeError):
    """Raised when release-PR integrity cannot be established."""


def run_gh(argv: Sequence[str]) -> dict[str, Any]:
    completed = subprocess.run(
        ["gh", *argv],
        text=True,
        capture_output=True,
        check=False,
        shell=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown gh error"
        raise IntegrityError(f"gh {' '.join(argv[:2])} failed: {detail}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise IntegrityError("gh returned malformed JSON") from exc
    if not isinstance(payload, dict):
        raise IntegrityError("gh returned a non-object JSON response")
    return payload


def _connection_page(
    connection: Any,
    *,
    label: str,
) -> tuple[list[dict[str, Any]], bool, str | None]:
    if not isinstance(connection, dict):
        raise IntegrityError(f"{label} is missing")
    nodes = connection.get("nodes")
    if not isinstance(nodes, list) or not all(isinstance(item, dict) for item in nodes):
        raise IntegrityError(f"{label} is malformed")
    page_info = connection.get("pageInfo")
    if not isinstance(page_info, dict):
        raise IntegrityError(f"{label} pagination metadata is missing")
    has_next_page = page_info.get("hasNextPage")
    if not isinstance(has_next_page, bool):
        raise IntegrityError(f"{label} pagination metadata is malformed")
    if "endCursor" not in page_info:
        raise IntegrityError(f"{label} pagination cursor metadata is missing")
    end_cursor = page_info.get("endCursor")
    if has_next_page and (not isinstance(end_cursor, str) or not end_cursor):
        raise IntegrityError(f"{label} pagination cursor is missing")
    if end_cursor is not None and not isinstance(end_cursor, str):
        raise IntegrityError(f"{label} pagination cursor is malformed")
    return nodes, has_next_page, end_cursor


def _load_thread_comments(
    thread: dict[str, Any],
    *,
    api: Callable[[Sequence[str]], dict[str, Any]],
) -> dict[str, Any]:
    comments = thread.get("comments")
    nodes, has_next_page, end_cursor = _connection_page(
        comments,
        label="review thread comments",
    )
    all_nodes = list(nodes)
    seen_cursors: set[str] = set()
    while has_next_page:
        thread_id = thread.get("id")
        if not isinstance(thread_id, str) or not thread_id:
            raise IntegrityError("review thread ID is missing for comment pagination")
        assert isinstance(end_cursor, str)
        if end_cursor in seen_cursors:
            raise IntegrityError("review thread comment pagination cursor did not advance")
        seen_cursors.add(end_cursor)
        payload = api(
            [
                "api",
                "graphql",
                "-f",
                f"query={THREAD_COMMENTS_QUERY}",
                "-F",
                f"thread={thread_id}",
                "-f",
                f"after={end_cursor}",
            ]
        )
        if payload.get("errors"):
            raise IntegrityError("GitHub GraphQL returned errors while paginating comments")
        data = payload.get("data")
        node = data.get("node") if isinstance(data, dict) else None
        if not isinstance(node, dict):
            raise IntegrityError("review thread comment pagination response is malformed")
        page_nodes, has_next_page, end_cursor = _connection_page(
            node.get("comments"),
            label="review thread comments",
        )
        all_nodes.extend(page_nodes)

    assert isinstance(comments, dict)
    return {
        **thread,
        "comments": {
            **comments,
            "nodes": all_nodes,
            "pageInfo": {"hasNextPage": False, "endCursor": end_cursor},
        },
    }


def load_release_pr(
    repository: str,
    pr_number: int,
    *,
    api: Callable[[Sequence[str]], dict[str, Any]] = run_gh,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    owner, name = repository.split("/", 1)
    query = """
query($owner:String!,$name:String!,$number:Int!,$after:String){
  repository(owner:$owner,name:$name){
    pullRequest(number:$number){
      headRefName
      headRefOid
      reviewThreads(first:100,after:$after){
        nodes{
          id
          isResolved
          comments(first:100){
            nodes{body authorAssociation url}
            pageInfo{hasNextPage endCursor}
          }
        }
        pageInfo{hasNextPage endCursor}
      }
    }
  }
}
""".strip()
    threads: list[dict[str, Any]] = []
    after: str | None = None
    pr: dict[str, Any] | None = None
    while True:
        argv = [
            "api",
            "graphql",
            "-f",
            f"query={query}",
            "-f",
            f"owner={owner}",
            "-f",
            f"name={name}",
            "-F",
            f"number={pr_number}",
        ]
        if after is not None:
            argv.extend(("-f", f"after={after}"))
        payload = api(argv)
        if payload.get("errors"):
            raise IntegrityError("GitHub GraphQL returned errors")
        repository_data = (payload.get("data") or {}).get("repository")
        current = repository_data.get("pullRequest") if isinstance(repository_data, dict) else None
        if not isinstance(current, dict):
            raise IntegrityError(f"pull request #{pr_number} was not found")
        if pr is None:
            pr = current
        connection = current.get("reviewThreads")
        if not isinstance(connection, dict):
            raise IntegrityError("review thread inventory is missing")
        nodes, has_next_page, end_cursor = _connection_page(
            connection,
            label="review thread inventory",
        )
        threads.extend(_load_thread_comments(thread, api=api) for thread in nodes)
        if not has_next_page:
            break
        after = end_cursor
    assert pr is not None
    return pr, threads


def cited_resolution_commits(threads: Sequence[dict[str, Any]]) -> dict[str, set[str]]:
    citations: dict[str, set[str]] = {}
    for thread in threads:
        if thread.get("isResolved") is not True:
            continue
        comments = thread.get("comments")
        nodes = comments.get("nodes") if isinstance(comments, dict) else None
        if not isinstance(nodes, list):
            raise IntegrityError("review thread comments are malformed")
        for comment in nodes:
            if not isinstance(comment, dict):
                raise IntegrityError("review thread comment is malformed")
            body = comment.get("body")
            association = comment.get("authorAssociation")
            if (
                not isinstance(body, str)
                or association not in TRUSTED_ASSOCIATIONS
                or RESOLUTION_CLAIM_RE.search(body) is None
            ):
                continue
            url = comment.get("url")
            source = url if isinstance(url, str) and url else "resolved review comment"
            for match in COMMIT_CITATION_RE.finditer(body):
                citations.setdefault(match.group(1).lower(), set()).add(source)
    return citations


def validate_citations(
    repository: str,
    head_sha: str,
    citations: dict[str, set[str]],
    *,
    api: Callable[[Sequence[str]], dict[str, Any]] = run_gh,
) -> None:
    dropped: list[str] = []
    for cited_sha, sources in sorted(citations.items()):
        commit = api(["api", f"repos/{repository}/commits/{cited_sha}"])
        full_sha = commit.get("sha")
        if not isinstance(full_sha, str) or re.fullmatch(r"[0-9A-Fa-f]{40}", full_sha) is None:
            raise IntegrityError(f"cited commit {cited_sha} could not be resolved")
        comparison = api(["api", f"repos/{repository}/compare/{full_sha}...{head_sha}"])
        if comparison.get("status") not in {"ahead", "identical"}:
            dropped.append(f"{cited_sha} ({', '.join(sorted(sources))})")
    if dropped:
        raise IntegrityError(
            "resolved review thread cites commit(s) not reachable from the release PR head: "
            + "; ".join(dropped)
        )


def validate_release_pr(
    repository: str,
    pr_number: int,
    *,
    api: Callable[[Sequence[str]], dict[str, Any]] = run_gh,
) -> int:
    pr, threads = load_release_pr(repository, pr_number, api=api)
    branch = pr.get("headRefName")
    if not isinstance(branch, str):
        raise IntegrityError("pull request head branch is missing")
    if not branch.startswith(RELEASE_BRANCH_PREFIX):
        print(f"PR #{pr_number} is not a generated release PR; integrity check skipped")
        return 0
    head_sha = pr.get("headRefOid")
    if not isinstance(head_sha, str) or re.fullmatch(r"[0-9A-Fa-f]{40}", head_sha) is None:
        raise IntegrityError("release PR head SHA is invalid")
    citations = cited_resolution_commits(threads)
    validate_citations(repository, head_sha, citations, api=api)
    print(
        f"release PR #{pr_number} retains {len(citations)} commit citation(s) "
        "from resolved maintainer review threads"
    )
    return 0


def main() -> int:
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    raw_number = os.environ.get("PR_NUMBER", "")
    if REPOSITORY_RE.fullmatch(repository) is None:
        print("release-pr-integrity: GITHUB_REPOSITORY is invalid", file=sys.stderr)
        return 2
    try:
        pr_number = int(raw_number)
    except ValueError:
        print("release-pr-integrity: PR_NUMBER is invalid", file=sys.stderr)
        return 2
    if pr_number <= 0:
        print("release-pr-integrity: PR_NUMBER is invalid", file=sys.stderr)
        return 2
    try:
        return validate_release_pr(repository, pr_number)
    except IntegrityError as exc:
        print(f"release-pr-integrity: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
