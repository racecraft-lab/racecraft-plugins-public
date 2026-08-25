"""Fail-closed isolation primitives for the pull-request feedback sweep.

The model-facing boundary in this module is an immutable Git object snapshot.
Reviewer text and model records live in a private, mode-0700 session store and
cross back to the trusted runner only as opaque, one-use receipts.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterator


MAX_BLOB_BYTES = 256 * 1024
MAX_SNAPSHOT_BYTES = 16 * 1024 * 1024
MAX_SNAPSHOT_FILES = 8_192
MAX_READ_BYTES = 32 * 1024
MAX_READ_LINES = 240
MAX_SEARCH_LITERAL_BYTES = 512
MAX_SEARCH_RESULTS = 50
MAX_SEARCH_LINE_BYTES = 1_024
MAX_COMMENT_BYTES = 8_192
MAX_SESSION_COMMENTS = 1_024
MAX_SESSION_COMMENT_BYTES = 8 * 1024 * 1024
MAX_REASON_BYTES = 512
MAX_FINDING_BYTES = 6_144
MAX_ANCHOR_BYTES = 512
MAX_REPLACEMENT_BYTES = 8_192
MAX_PRIVATE_STATE_BYTES = 64 * 1024 * 1024
DEFAULT_SESSION_TTL_SECONDS = 15 * 60
SESSION_VERSION = 1
HOOK_VERSION = "sweep-isolation-v1"
RECEIPT_PREFIX = "sweep-result:v1:"
RECEIPT_RE = re.compile(r"^sweep-result:v1:([0-9a-f]{64})$")
CAPABILITY_PREFIX = "sweep-cap:v1:"
CAPABILITY_RE = re.compile(r"^sweep-cap:v1:([0-9a-f]{32}):([0-9a-f]{64})$")
SESSION_ID_RE = re.compile(r"^[0-9a-f]{32}$")
HEX_OBJECT_RE = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
ARTIFACT_ALLOWLIST = ("spec.md", "plan.md", "tasks.md")
CLASS_VALUES = ("amended", "answered", "deferred", "no action")
PERSPECTIVES = ("codebase", "spec-context", "domain")
BROKER_TOOL_NAMES = (
    "snapshot_list",
    "snapshot_read",
    "snapshot_search",
    "review_comment",
    "consensus_inputs",
    "submit_result",
)
BROKER_ERROR_CODES = (
    "comment_mismatch",
    "submit_shape",
    "classifier_class",
    "classifier_target",
    "classifier_reason",
    "schema_fields",
    "evidence_path",
    "perspective_mismatch",
    "synthesis_consistency",
    "receipt_violation",
    "isolation_violation",
    "schema_validation",
)


class IsolationViolation(ValueError):
    """The requested read is outside the immutable snapshot boundary."""


class SchemaViolation(ValueError):
    """A model record does not match its exact closed schema."""


class ReceiptViolation(ValueError):
    """A receipt is invalid, stale, expired, replayed, or cross-session."""


class MutationViolation(ValueError):
    """A receipt-gated artifact mutation failed a precondition."""


class CaptureViolation(RuntimeError):
    """The private GitHub observation could not be captured completely."""


@dataclass(frozen=True)
class SnapshotEntry:
    path: str
    oid: str
    mode: str
    content: bytes
    sha256: str


def _git_env() -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", ""),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_OPTIONAL_LOCKS": "0",
        "LC_ALL": "C",
    }


def _run_git(repo_root: Path, *args: str, text: bool = False) -> str | bytes:
    git_executable = shutil.which("git")
    if git_executable is None:
        raise IsolationViolation("git is unavailable")
    try:
        completed = subprocess.run(
            [git_executable, *args],
            cwd=repo_root,
            env=_git_env(),
            text=text,
            capture_output=True,
            check=False,
            timeout=30,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise IsolationViolation("git snapshot operation failed") from exc
    if completed.returncode != 0:
        raise IsolationViolation("git snapshot operation failed")
    return completed.stdout


def current_head(repo_root: Path) -> str:
    head = str(_run_git(repo_root, "rev-parse", "--verify", "HEAD^{commit}", text=True)).strip()
    if HEX_OBJECT_RE.fullmatch(head) is None:
        raise IsolationViolation("repository HEAD is not a commit object")
    return head


def _normalize_snapshot_path(raw: str, *, allow_prefix: bool = False) -> str:
    if not isinstance(raw, str) or "\x00" in raw or "\\" in raw:
        raise IsolationViolation("snapshot path is malformed")
    if not raw:
        if allow_prefix:
            return ""
        raise IsolationViolation("snapshot path is required")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise IsolationViolation("snapshot path escapes the repository")
    normalized = path.as_posix()
    if normalized.startswith(".git/") or normalized == ".git":
        raise IsolationViolation("Git metadata is outside the snapshot")
    return normalized


SENSITIVE_FILENAMES = frozenset(
    {
        ".env",
        ".git-credentials",
        ".netrc",
        ".npmrc",
        ".pypirc",
        "credentials",
        "credentials.json",
        "id_dsa",
        "id_ecdsa",
        "id_ed25519",
        "id_rsa",
        "secrets.json",
    }
)
SENSITIVE_COMPONENTS = frozenset({".aws", ".gnupg", ".ssh", "private", "secrets"})
SENSITIVE_SUFFIXES = (".key", ".p12", ".pfx", ".pem")


def _sensitive_path(path: str) -> bool:
    parts = [part.casefold() for part in PurePosixPath(path).parts]
    name = parts[-1]
    return (
        name in SENSITIVE_FILENAMES
        or name.startswith(".env.")
        or name.endswith(SENSITIVE_SUFFIXES)
        or any(part in SENSITIVE_COMPONENTS for part in parts)
    )


PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN (?:[A-Z0-9 ]* )?PRIVATE KEY(?: BLOCK)?-----", re.IGNORECASE
)
PREFIX_SECRET_RULES = (
    (
        "github_token",
        re.compile(r"\b((?:ghp|gho|ghu|ghs|ghr)_(?=[A-Za-z0-9]*[0-9])[A-Za-z0-9]{36,255})"),
    ),
    (
        "github_fine_grained_pat",
        re.compile(r"\b(github_pat_(?=[A-Za-z0-9_]*[0-9])[A-Za-z0-9_]{82,255})"),
    ),
    (
        "slack_token",
        re.compile(r"\b(xox[abceprs]-(?=[A-Za-z0-9-]*[0-9])[A-Za-z0-9-]{17,250})"),
    ),
    (
        "anthropic_api_key",
        re.compile(r"\b(sk-ant-(?=[A-Za-z0-9_-]*[0-9])[A-Za-z0-9_-]{24,120})"),
    ),
    (
        "openai_api_key",
        re.compile(r"\b(sk-(?:proj-|svcacct-|admin-)?[A-Za-z0-9_-]{20,}?T3BlbkFJ[A-Za-z0-9_-]{20,})"),
    ),
    (
        "google_api_key",
        re.compile(r"\b(AIza(?=[0-9A-Za-z_-]*[0-9])[0-9A-Za-z_-]{35})\b"),
    ),
    (
        "aws_access_key_id",
        re.compile(r"\b((?:AKIA|ASIA|ABIA|ACCA|A3T[A-Z0-9])[A-Z2-7]{16})\b"),
    ),
    (
        "url_credentials",
        re.compile(
            r"(?i)\b[a-z][a-z0-9+.-]{1,30}://[^\s:/@'\"<>`]{1,64}"
            r":((?=[^\s/@]*[0-9])[^\s/@'\"<>${}`]{8,256})@"
        ),
    ),
)
PREFIX_SECRET_RES = tuple(pattern for _rule, pattern in PREFIX_SECRET_RULES)
ASSIGNED_SECRET_RE = re.compile(
    r"(?i:(?:api[_ -]?key|access[_ -]?key|auth[_ -]?token|password|secret|token))"
    r"[A-Za-z0-9_ -]*[ \t]*[=:][ \t]*[\"']?"
    r"([A-Za-z0-9._~+/=-]{20,})"
)
BEARER_SECRET_RE = re.compile(r"(?i:bearer)[ \t]+([A-Za-z0-9._~+/=-]{20,})")
OUTBOUND_SECRET_RULES = tuple((pattern, rule) for rule, pattern in PREFIX_SECRET_RULES) + (
    (ASSIGNED_SECRET_RE, "assigned_secret"),
    (BEARER_SECRET_RE, "bearer_token"),
)


def secret_matches(text: str) -> bool:
    return bool(
        PRIVATE_KEY_RE.search(text)
        or any(pattern.search(text) for pattern in PREFIX_SECRET_RES)
        or ASSIGNED_SECRET_RE.search(text)
        or BEARER_SECRET_RE.search(text)
    )


def _decode_snapshot_blob(content: bytes) -> str | None:
    if b"\x00" in content:
        return None
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None
    if secret_matches(text):
        return None
    return text


class GitSnapshot:
    """An immutable, filtered view of regular UTF-8 blobs at one Git commit."""

    def __init__(self, repo_root: Path, head: str, entries: dict[str, SnapshotEntry]) -> None:
        self.repo_root = repo_root
        self.head = head
        self._entries = entries

    @classmethod
    def capture(cls, repo_root: Path, *, head: str | None = None) -> "GitSnapshot":
        root = repo_root.resolve(strict=True)
        if not root.is_dir():
            raise IsolationViolation("repository root is not a directory")
        frozen_head = current_head(root) if head is None else head
        if HEX_OBJECT_RE.fullmatch(frozen_head) is None:
            raise IsolationViolation("snapshot head is malformed")
        verified = str(
            _run_git(root, "rev-parse", "--verify", f"{frozen_head}^{{commit}}", text=True)
        ).strip()
        if verified != frozen_head:
            raise IsolationViolation("snapshot head is not the requested commit")
        tree = bytes(_run_git(root, "ls-tree", "-rz", "--full-tree", frozen_head))
        entries: dict[str, SnapshotEntry] = {}
        total_bytes = 0
        for raw_record in tree.split(b"\x00"):
            if not raw_record:
                continue
            try:
                metadata, raw_path = raw_record.split(b"\t", 1)
                mode, object_type, raw_oid = metadata.split(b" ", 2)
                path = raw_path.decode("utf-8", errors="strict")
                oid = raw_oid.decode("ascii", errors="strict")
                mode_text = mode.decode("ascii", errors="strict")
            except (ValueError, UnicodeDecodeError):
                continue
            if mode_text not in {"100644", "100755"} or object_type != b"blob":
                continue
            try:
                normalized = _normalize_snapshot_path(path)
            except IsolationViolation:
                continue
            if _sensitive_path(normalized) or len(entries) >= MAX_SNAPSHOT_FILES:
                continue
            size_text = str(_run_git(root, "cat-file", "-s", oid, text=True)).strip()
            if not size_text.isdecimal():
                continue
            size = int(size_text)
            if size > MAX_BLOB_BYTES or total_bytes + size > MAX_SNAPSHOT_BYTES:
                continue
            content = bytes(_run_git(root, "cat-file", "blob", oid))
            if len(content) != size or _decode_snapshot_blob(content) is None:
                continue
            entries[normalized] = SnapshotEntry(
                path=normalized,
                oid=oid,
                mode=mode_text,
                content=content,
                sha256=hashlib.sha256(content).hexdigest(),
            )
            total_bytes += size
        return cls(root, frozen_head, entries)

    def list(self, prefix: str = "") -> list[dict[str, Any]]:
        normalized_prefix = _normalize_snapshot_path(prefix, allow_prefix=True)
        return [
            {"path": entry.path, "sha256": entry.sha256, "bytes": len(entry.content)}
            for entry in sorted(self._entries.values(), key=lambda value: value.path)
            if not normalized_prefix
            or entry.path == normalized_prefix
            or entry.path.startswith(normalized_prefix.rstrip("/") + "/")
        ]

    def entry(self, path: str) -> SnapshotEntry:
        normalized = _normalize_snapshot_path(path)
        entry = self._entries.get(normalized)
        if entry is None:
            raise IsolationViolation("path is not exposed by the snapshot")
        return entry

    def read(
        self,
        path: str,
        *,
        start_line: int | None = None,
        end_line: int | None = None,
    ) -> dict[str, Any]:
        entry = self.entry(path)
        text = entry.content.decode("utf-8")
        if start_line is None and end_line is None:
            selected = text
            first = 1
            last = max(1, len(text.splitlines()))
        else:
            first = 1 if start_line is None else start_line
            lines = text.splitlines(keepends=True)
            last = len(lines) if end_line is None else end_line
            if (
                isinstance(first, bool)
                or isinstance(last, bool)
                or not isinstance(first, int)
                or not isinstance(last, int)
                or first < 1
                or last < first
                or last - first + 1 > MAX_READ_LINES
            ):
                raise IsolationViolation("snapshot line range is invalid or over bound")
            selected = "".join(lines[first - 1 : last])
        if len(selected.encode("utf-8")) > MAX_READ_BYTES:
            raise IsolationViolation("snapshot read exceeds the output bound; request fewer lines")
        return {
            "path": entry.path,
            "sha256": entry.sha256,
            "start_line": first,
            "end_line": last,
            "text": selected,
        }

    def search(
        self,
        literal: str,
        *,
        prefix: str = "",
        max_results: int = MAX_SEARCH_RESULTS,
    ) -> list[dict[str, Any]]:
        if not isinstance(literal, str) or not literal or "\x00" in literal:
            raise IsolationViolation("a non-empty literal search value is required")
        if len(literal.encode("utf-8")) > MAX_SEARCH_LITERAL_BYTES:
            raise IsolationViolation("literal search value exceeds the bound")
        if (
            isinstance(max_results, bool)
            or not isinstance(max_results, int)
            or max_results < 1
            or max_results > MAX_SEARCH_RESULTS
        ):
            raise IsolationViolation("search result limit is invalid")
        normalized_prefix = _normalize_snapshot_path(prefix, allow_prefix=True)
        hits: list[dict[str, Any]] = []
        for entry in sorted(self._entries.values(), key=lambda value: value.path):
            if normalized_prefix and not (
                entry.path == normalized_prefix
                or entry.path.startswith(normalized_prefix.rstrip("/") + "/")
            ):
                continue
            for line_number, line in enumerate(entry.content.decode("utf-8").splitlines(), start=1):
                if literal not in line:
                    continue
                line_bytes = line.encode("utf-8")
                if len(line_bytes) > MAX_SEARCH_LINE_BYTES:
                    line = line_bytes[:MAX_SEARCH_LINE_BYTES].decode("utf-8", errors="ignore")
                hits.append({"path": entry.path, "line": line_number, "text": line})
                if len(hits) >= max_results:
                    return hits
        return hits


def default_state_root() -> Path:
    uid = getattr(os, "getuid", lambda: 0)()
    return Path(tempfile.gettempdir()) / f"speckit-pro-feedback-sweep-{uid}"


def _bounded_comment_body(body: str) -> tuple[str, bool]:
    raw = body.encode("utf-8")
    if len(raw) <= MAX_COMMENT_BYTES:
        return body, False
    end = MAX_COMMENT_BYTES
    while end > 0 and (raw[end] & 0xC0) == 0x80:
        end -= 1
    return raw[:end].decode("utf-8"), True


def _run_gh(args: list[str], repo_root: Path) -> str:
    executable = shutil.which("gh")
    if executable is None:
        raise CaptureViolation("GitHub CLI is unavailable")
    try:
        completed = subprocess.run(
            [executable, "api", *args],
            cwd=repo_root,
            env=os.environ.copy(),
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CaptureViolation("GitHub observation failed") from exc
    if completed.returncode != 0 or len(completed.stdout.encode("utf-8")) > 16 * 1024 * 1024:
        raise CaptureViolation("GitHub observation failed")
    return completed.stdout


def _run_gh_json(args: list[str], repo_root: Path) -> Any:
    try:
        return json.loads(_run_gh(args, repo_root))
    except json.JSONDecodeError as exc:
        raise CaptureViolation("GitHub observation returned malformed JSON") from exc


THREADS_QUERY = """
query($owner:String!,$name:String!,$number:Int!,$cursor:String){
  repository(owner:$owner,name:$name){
    pullRequest(number:$number){
      reviewThreads(first:50,after:$cursor){
        nodes{
          id isResolved
          comments(first:100){
            nodes{id body authorAssociation author{login}}
            pageInfo{hasNextPage endCursor}
          }
        }
        pageInfo{hasNextPage endCursor}
      }
    }
  }
}
""".strip()

THREAD_COMMENTS_QUERY = """
query($thread:ID!,$cursor:String){
  node(id:$thread){
    ... on PullRequestReviewThread{
      comments(first:100,after:$cursor){
        nodes{id body authorAssociation author{login}}
        pageInfo{hasNextPage endCursor}
      }
    }
  }
}
""".strip()


def _review_comment_record(node: Any) -> dict[str, Any]:
    if not isinstance(node, dict):
        raise CaptureViolation("review thread returned a malformed comment")
    author = node.get("author")
    login = author.get("login") if isinstance(author, dict) else None
    body = node.get("body")
    if not isinstance(body, str):
        raise CaptureViolation("review thread comment has no body")
    bounded, truncated = _bounded_comment_body(body)
    return {
        "id": node.get("id"),
        "surface": "review_thread",
        "author": login,
        "author_association": node.get("authorAssociation"),
        "body": bounded,
        "thread_resolved": False,
        "truncated": truncated,
    }


def _thread_comment_pages(repo_root: Path, thread: dict[str, Any]) -> list[dict[str, Any]]:
    comments = thread.get("comments")
    if not isinstance(comments, dict) or not isinstance(comments.get("nodes"), list):
        raise CaptureViolation("review thread comment connection is malformed")
    records = [_review_comment_record(node) for node in comments["nodes"]]
    page_info = comments.get("pageInfo")
    if not isinstance(page_info, dict):
        raise CaptureViolation("review thread pagination is malformed")
    cursor = page_info.get("endCursor")
    while page_info.get("hasNextPage") is True:
        if not isinstance(cursor, str) or not cursor:
            raise CaptureViolation("review thread pagination cursor is missing")
        page = _run_gh_json(
            [
                "graphql",
                "-f",
                f"query={THREAD_COMMENTS_QUERY}",
                "-F",
                f"thread={thread.get('id')}",
                "-F",
                f"cursor={cursor}",
            ],
            repo_root,
        )
        try:
            comments = page["data"]["node"]["comments"]
        except (KeyError, TypeError) as exc:
            raise CaptureViolation("review thread pagination response is malformed") from exc
        if not isinstance(comments.get("nodes"), list) or not isinstance(comments.get("pageInfo"), dict):
            raise CaptureViolation("review thread pagination response is malformed")
        records.extend(_review_comment_record(node) for node in comments["nodes"])
        page_info = comments["pageInfo"]
        cursor = page_info.get("endCursor")
    return records


def read_github_comments(
    repo_root: Path,
    *,
    repository: str,
    pr_number: int,
) -> tuple[str, list[dict[str, Any]]]:
    """Capture both GitHub comment surfaces privately and completely."""
    if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is None:
        raise CaptureViolation("repository must be an owner/name identifier")
    if isinstance(pr_number, bool) or not isinstance(pr_number, int) or pr_number < 1:
        raise CaptureViolation("pull request number must be a positive integer")
    owner, name = repository.split("/", 1)
    viewer = _run_gh_json(["user"], repo_root)
    self_login = viewer.get("login") if isinstance(viewer, dict) else None
    if not isinstance(self_login, str) or not self_login or "\n" in self_login:
        raise CaptureViolation("authenticated GitHub login is unavailable")

    review_comments: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        args = [
            "graphql",
            "-f",
            f"query={THREADS_QUERY}",
            "-F",
            f"owner={owner}",
            "-F",
            f"name={name}",
            "-F",
            f"number={pr_number}",
        ]
        if cursor is not None:
            args.extend(("-F", f"cursor={cursor}"))
        page = _run_gh_json(args, repo_root)
        try:
            threads = page["data"]["repository"]["pullRequest"]["reviewThreads"]
        except (KeyError, TypeError) as exc:
            raise CaptureViolation("review thread response is malformed") from exc
        if not isinstance(threads.get("nodes"), list) or not isinstance(threads.get("pageInfo"), dict):
            raise CaptureViolation("review thread response is malformed")
        for thread in threads["nodes"]:
            if not isinstance(thread, dict):
                raise CaptureViolation("review thread response is malformed")
            if thread.get("isResolved") is False:
                review_comments.extend(_thread_comment_pages(repo_root, thread))
        page_info = threads["pageInfo"]
        if page_info.get("hasNextPage") is not True:
            break
        cursor = page_info.get("endCursor")
        if not isinstance(cursor, str) or not cursor:
            raise CaptureViolation("review thread pagination cursor is missing")

    conversation_pages = _run_gh_json(
        ["--paginate", "--slurp", f"repos/{repository}/issues/{pr_number}/comments?per_page=100"],
        repo_root,
    )
    if not isinstance(conversation_pages, list):
        raise CaptureViolation("pull-request conversation response is malformed")
    conversation_comments: list[dict[str, Any]] = []
    for page in conversation_pages:
        if not isinstance(page, list):
            raise CaptureViolation("pull-request conversation page is malformed")
        for node in page:
            if not isinstance(node, dict) or not isinstance(node.get("body"), str):
                raise CaptureViolation("pull-request conversation comment is malformed")
            user = node.get("user")
            bounded, truncated = _bounded_comment_body(node["body"])
            conversation_comments.append(
                {
                    "id": node.get("node_id"),
                    "surface": "pr_conversation",
                    "author": user.get("login") if isinstance(user, dict) else None,
                    "author_association": node.get("author_association"),
                    "body": bounded,
                    "thread_resolved": False,
                    "truncated": truncated,
                }
            )
    comments = [*review_comments, *conversation_comments]
    _validate_comment_set(comments)
    return self_login, comments


def _workflow_text(snapshot: GitSnapshot, workflow_file: str) -> str:
    normalized = _normalize_snapshot_path(workflow_file)
    try:
        return snapshot.entry(normalized).content.decode("utf-8", errors="strict")
    except (IsolationViolation, UnicodeDecodeError) as exc:
        raise CaptureViolation("workflow file is not exposed by the exact-HEAD snapshot") from exc


def capture_session_from_comments(
    repo_root: Path,
    *,
    workflow_file: str,
    self_login: str,
    comments: list[dict[str, Any]],
    state_root: Path | None = None,
    now: float | None = None,
    ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
) -> dict[str, Any]:
    """Filter one complete private observation before creating a model session."""
    if not isinstance(self_login, str) or not self_login.strip():
        raise CaptureViolation("authenticated GitHub login is required")
    from .helpers.read_only import (
        SWEEP_SELF_REPLY_PREFIX,
        SWEEP_TRUSTED_ASSOCIATIONS,
        sweep_export_record,
        sweep_logged_comment_ids,
    )

    snapshot = GitSnapshot.capture(repo_root)
    logged, unreadable_row = sweep_logged_comment_ids(_workflow_text(snapshot, workflow_file))
    if unreadable_row is not None:
        raise CaptureViolation("feedback sweep log has an unreadable comment id")
    selected: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []
    routes: dict[str, str] = {}
    for raw_comment in comments:
        comment = _validate_comment(raw_comment)
        safe = {"id": comment["id"], "surface": comment["surface"]}
        if comment["author_association"] not in SWEEP_TRUSTED_ASSOCIATIONS:
            excluded.append({**safe, "reason": "untrusted_author"})
            continue
        body = comment["body"].replace("\r\n", "\n").replace("\r", "\n")
        if body.startswith(SWEEP_SELF_REPLY_PREFIX) and comment["author"] == self_login:
            excluded.append({**safe, "reason": "self_reply"})
            continue
        if comment["id"] in logged:
            excluded.append({**safe, "reason": "already_logged"})
            continue
        if comment["thread_resolved"] is True:
            excluded.append({**safe, "reason": "thread_resolved"})
            continue
        export = sweep_export_record(body)
        routes[comment["id"]] = "no_action" if export is not None and export["kind"] == "empty" else "dispatch"
        selected.append(comment)
    metadata = SweepSession.create(
        repo_root,
        comments=selected,
        snapshot=snapshot,
        state_root=state_root,
        now=now,
        ttl_seconds=ttl_seconds,
    )
    for comment in metadata["comments"]:
        comment["route"] = routes[comment["id"]]
    metadata["excluded"] = excluded
    metadata["counts"] = {
        "observed": len(comments),
        "candidates": len(selected),
        "excluded": len(excluded),
    }
    return metadata


def capture_github_session(
    repo_root: Path,
    *,
    repository: str,
    pr_number: int,
    workflow_file: str,
    state_root: Path | None = None,
) -> dict[str, Any]:
    self_login, comments = read_github_comments(
        repo_root,
        repository=repository,
        pr_number=pr_number,
    )
    return capture_session_from_comments(
        repo_root,
        workflow_file=workflow_file,
        self_login=self_login,
        comments=comments,
        state_root=state_root,
    )


def _ensure_private_directory(path: Path) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise ReceiptViolation("private session root is unsafe")
    uid = getattr(os, "getuid", lambda: info.st_uid)()
    if info.st_uid != uid:
        raise ReceiptViolation("private session root has the wrong owner")
    if stat.S_IMODE(info.st_mode) & 0o077:
        os.chmod(path, 0o700)


def _write_private_json(path: Path, payload: dict[str, Any]) -> None:
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            fd = -1
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if fd >= 0:
            os.close(fd)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _safe_session_path(state_root: Path, session_id: str) -> Path:
    if SESSION_ID_RE.fullmatch(session_id) is None:
        raise ReceiptViolation("session id is malformed")
    root = state_root.resolve(strict=True)
    session_path = root / session_id
    if session_path.parent != root:
        raise ReceiptViolation("session path escapes the private store")
    return session_path


def _validate_comment(comment: Any) -> dict[str, Any]:
    if not isinstance(comment, dict):
        raise SchemaViolation("comment must be an object")
    required = {
        "id",
        "surface",
        "author",
        "author_association",
        "body",
        "thread_resolved",
        "truncated",
    }
    if set(comment) != required:
        raise SchemaViolation("comment fields do not match the private capture schema")
    if (
        not isinstance(comment["id"], str)
        or not comment["id"].strip()
        or len(comment["id"].encode("utf-8")) > 256
    ):
        raise SchemaViolation("comment id is required")
    if comment["surface"] not in {"review_thread", "pr_conversation"}:
        raise SchemaViolation("comment surface is unknown")
    if comment["author"] is not None and (
        not isinstance(comment["author"], str)
        or len(comment["author"].encode("utf-8")) > 256
    ):
        raise SchemaViolation("comment author is malformed")
    if comment["author_association"] not in {
        "OWNER",
        "MEMBER",
        "COLLABORATOR",
        "CONTRIBUTOR",
        "FIRST_TIMER",
        "FIRST_TIME_CONTRIBUTOR",
        "MANNEQUIN",
        "NONE",
    }:
        raise SchemaViolation("comment association is unknown")
    if not isinstance(comment["body"], str):
        raise SchemaViolation("comment body must be text")
    if len(comment["body"].encode("utf-8")) > MAX_COMMENT_BYTES:
        raise SchemaViolation("comment body exceeds the private capture bound")
    if not isinstance(comment["thread_resolved"], bool) or not isinstance(comment["truncated"], bool):
        raise SchemaViolation("comment flags must be booleans")
    return dict(comment)


def _validate_comment_set(comments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(comments) > MAX_SESSION_COMMENTS:
        raise SchemaViolation("comment observation exceeds the session count bound")
    validated = [_validate_comment(comment) for comment in comments]
    if sum(len(comment["body"].encode("utf-8")) for comment in validated) > MAX_SESSION_COMMENT_BYTES:
        raise SchemaViolation("comment observation exceeds the session byte bound")
    return validated


class SweepSession:
    """Private persistent state shared by isolated one-model invocations."""

    def __init__(self, session_id: str, state_root: Path, *, now: float | None = None) -> None:
        self.session_id = session_id
        self.state_root = state_root
        self._now = now
        self.session_path = _safe_session_path(state_root, session_id)
        if not self.session_path.is_dir() or self.session_path.is_symlink():
            raise ReceiptViolation("private sweep session does not exist")
        self.state_path = self.session_path / "state.json"
        self.lock_path = self.session_path / "state.lock"

    @classmethod
    def create(
        cls,
        repo_root: Path,
        *,
        comments: list[dict[str, Any]],
        snapshot: GitSnapshot | None = None,
        state_root: Path | None = None,
        now: float | None = None,
        ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
    ) -> dict[str, Any]:
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int) or ttl_seconds < 1:
            raise ReceiptViolation("session TTL must be a positive integer")
        timestamp = time.time() if now is None else float(now)
        frozen_snapshot = GitSnapshot.capture(repo_root) if snapshot is None else snapshot
        if frozen_snapshot.repo_root != repo_root.resolve(strict=True):
            raise IsolationViolation("provided snapshot belongs to another repository")
        if current_head(frozen_snapshot.repo_root) != frozen_snapshot.head:
            raise IsolationViolation("provided snapshot is stale")
        private_comments = _validate_comment_set(comments)
        if len({comment["id"] for comment in private_comments}) != len(private_comments):
            raise SchemaViolation("comment ids must be unique within a sweep session")
        root = default_state_root() if state_root is None else state_root
        _ensure_private_directory(root)
        session_id = secrets.token_hex(16)
        session_path = root / session_id
        session_path.mkdir(mode=0o700)
        state = {
            "version": SESSION_VERSION,
            "session_id": session_id,
            "repo_root": str(frozen_snapshot.repo_root),
            "head": frozen_snapshot.head,
            "created_at": timestamp,
            "expires_at": timestamp + ttl_seconds,
            "receipt_key": secrets.token_hex(32),
            "comments": private_comments,
            "results": {},
            "capabilities": {},
            "broker_errors": {},
            "accepted": {"classifier": {}, "perspective": {}, "synthesis": {}},
        }
        try:
            _write_private_json(session_path / "state.json", state)
            lock_fd = os.open(session_path / "state.lock", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(lock_fd)
        except OSError:
            shutil.rmtree(session_path, ignore_errors=True)
            raise
        return {
            "session_id": session_id,
            "head": frozen_snapshot.head,
            "expires_at": timestamp + ttl_seconds,
            "comments": [
                {
                    "id": comment["id"],
                    "surface": comment["surface"],
                    "body_sha256": hashlib.sha256(comment["body"].encode("utf-8")).hexdigest(),
                    "author_association": comment["author_association"],
                }
                for comment in private_comments
            ],
        }

    @classmethod
    def open(
        cls,
        session_id: str,
        *,
        state_root: Path | None = None,
        now: float | None = None,
    ) -> "SweepSession":
        root = default_state_root() if state_root is None else state_root
        _ensure_private_directory(root)
        return cls(session_id, root, now=now)

    def _clock(self) -> float:
        return time.time() if self._now is None else float(self._now)

    @contextmanager
    def _locked_state(self) -> Iterator[dict[str, Any]]:
        import fcntl

        fd = os.open(self.lock_path, os.O_RDWR | getattr(os, "O_NOFOLLOW", 0))
        try:
            lock_info = os.fstat(fd)
            uid = getattr(os, "getuid", lambda: lock_info.st_uid)()
            if (
                not stat.S_ISREG(lock_info.st_mode)
                or lock_info.st_uid != uid
                or stat.S_IMODE(lock_info.st_mode) & 0o077
            ):
                raise ReceiptViolation("private sweep session lock is unsafe")
            fcntl.flock(fd, fcntl.LOCK_EX)
            state_fd = -1
            try:
                state_fd = os.open(
                    self.state_path,
                    os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                )
                state_info = os.fstat(state_fd)
                if (
                    not stat.S_ISREG(state_info.st_mode)
                    or state_info.st_uid != uid
                    or stat.S_IMODE(state_info.st_mode) & 0o077
                    or state_info.st_size > MAX_PRIVATE_STATE_BYTES
                ):
                    raise ReceiptViolation("private sweep session state is unsafe")
                with os.fdopen(state_fd, "r", encoding="utf-8") as handle:
                    state_fd = -1
                    state = json.load(handle)
            except (OSError, json.JSONDecodeError) as exc:
                raise ReceiptViolation("private sweep session state is unreadable") from exc
            finally:
                if state_fd >= 0:
                    os.close(state_fd)
            self._validate_state(state)
            yield state
            _write_private_json(self.state_path, state)
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    def _validate_state(self, state: dict[str, Any]) -> None:
        if state.get("version") != SESSION_VERSION or state.get("session_id") != self.session_id:
            raise ReceiptViolation("private sweep session version or identity is invalid")
        if self._clock() > float(state.get("expires_at", 0)):
            raise ReceiptViolation("sweep session has expired")
        if not isinstance(state.get("receipt_key"), str) or len(state["receipt_key"]) != 64:
            raise ReceiptViolation("sweep receipt key is invalid")

    def _assert_live_head(self, state: dict[str, Any]) -> None:
        repo_root = Path(state["repo_root"])
        if current_head(repo_root) != state["head"]:
            raise ReceiptViolation("repository HEAD changed after the sweep snapshot")

    def snapshot(self) -> GitSnapshot:
        with self._locked_state() as state:
            self._assert_live_head(state)
            return GitSnapshot.capture(Path(state["repo_root"]), head=state["head"])

    def repo_root(self) -> Path:
        with self._locked_state() as state:
            return Path(state["repo_root"])

    def head(self) -> str:
        with self._locked_state() as state:
            self._assert_live_head(state)
            return str(state["head"])

    def record_broker_error(self, code: str) -> None:
        """Persist one closed diagnostic enum without model-controlled fields."""
        if code not in BROKER_ERROR_CODES:
            raise ReceiptViolation("broker error code is outside the closed vocabulary")
        with self._locked_state() as state:
            errors = state.setdefault("broker_errors", {})
            if not isinstance(errors, dict) or any(
                key not in BROKER_ERROR_CODES
                or isinstance(value, bool)
                or not isinstance(value, int)
                or value < 0
                for key, value in errors.items()
            ):
                raise ReceiptViolation("private broker diagnostics are invalid")
            errors[code] = min(errors.get(code, 0) + 1, 1_000_000)

    def broker_error_counts(self) -> dict[str, int]:
        """Return only closed diagnostic enums and bounded counts."""
        with self._locked_state() as state:
            errors = state.get("broker_errors", {})
            if not isinstance(errors, dict) or any(
                key not in BROKER_ERROR_CODES
                or isinstance(value, bool)
                or not isinstance(value, int)
                or value < 0
                for key, value in errors.items()
            ):
                raise ReceiptViolation("private broker diagnostics are invalid")
            return {key: min(value, 1_000_000) for key, value in errors.items()}

    def invalidate(self) -> None:
        """Remove exactly this private session without following filesystem links."""
        import fcntl

        directory_fd = os.open(
            self.session_path,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        lock_fd = -1
        try:
            directory_info = os.fstat(directory_fd)
            uid = getattr(os, "getuid", lambda: directory_info.st_uid)()
            if (
                not stat.S_ISDIR(directory_info.st_mode)
                or directory_info.st_uid != uid
                or stat.S_IMODE(directory_info.st_mode) & 0o077
            ):
                raise ReceiptViolation("private sweep session directory is unsafe")
            if set(os.listdir(directory_fd)) != {"state.json", "state.lock"}:
                raise ReceiptViolation("private sweep session contains unexpected files")
            for name in ("state.json", "state.lock"):
                info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_uid != uid
                    or stat.S_IMODE(info.st_mode) & 0o077
                ):
                    raise ReceiptViolation("private sweep session file is unsafe")
            lock_fd = os.open(
                "state.lock",
                os.O_RDWR | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=directory_fd,
            )
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            os.unlink("state.json", dir_fd=directory_fd)
            os.unlink("state.lock", dir_fd=directory_fd)
        except OSError as exc:
            raise ReceiptViolation("private sweep session could not be invalidated safely") from exc
        finally:
            if lock_fd >= 0:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                finally:
                    os.close(lock_fd)
            os.close(directory_fd)
        try:
            self.session_path.rmdir()
        except OSError as exc:
            raise ReceiptViolation("private sweep session directory could not be removed") from exc

    def _comment(self, state: dict[str, Any], comment_id: str) -> dict[str, Any]:
        for comment in state["comments"]:
            if comment["id"] == comment_id:
                return comment
        raise SchemaViolation("comment id is not part of this sweep session")

    def _accepted_amended_classifier(
        self, state: dict[str, Any], comment_id: str
    ) -> dict[str, Any]:
        digest = state["accepted"]["classifier"].get(comment_id)
        result = state["results"].get(digest) if isinstance(digest, str) else None
        payload = result.get("payload") if isinstance(result, dict) else None
        if not isinstance(payload, dict) or payload.get("class") != "amended":
            raise ReceiptViolation("an accepted amended classifier result is required")
        return payload

    def issue_capability(
        self,
        comment_id: str,
        *,
        stage: str,
        perspective: str | None = None,
    ) -> str:
        """Mint one opaque model-call capability bound to closed private context."""
        if stage not in {"classifier", "perspective", "synthesis"}:
            raise SchemaViolation("capability stage is unknown")
        if stage == "perspective":
            if perspective not in PERSPECTIVES:
                raise SchemaViolation("perspective capability requires a closed perspective")
        elif perspective is not None:
            raise SchemaViolation("perspective is only valid for a perspective capability")
        with self._locked_state() as state:
            self._assert_live_head(state)
            self._comment(state, comment_id)
            if stage in {"perspective", "synthesis"}:
                self._accepted_amended_classifier(state, comment_id)
            if stage == "synthesis":
                accepted = state["accepted"]["perspective"].get(comment_id, {})
                if not isinstance(accepted, dict) or set(accepted) != set(PERSPECTIVES):
                    raise ReceiptViolation("three accepted perspectives are required")
            binding = {
                "session_id": self.session_id,
                "head": state["head"],
                "comment_id": comment_id,
                "stage": stage,
                "perspective": perspective,
                "nonce": secrets.token_hex(16),
            }
            digest = hmac.new(
                bytes.fromhex(state["receipt_key"]),
                ("capability:" + json.dumps(binding, sort_keys=True, separators=(",", ":"))).encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            capabilities = state.get("capabilities")
            if not isinstance(capabilities, dict):
                raise ReceiptViolation("private capability store is invalid")
            if digest in capabilities:
                raise ReceiptViolation("capability collision")
            capabilities[digest] = binding
            return f"{CAPABILITY_PREFIX}{self.session_id}:{digest}"

    @classmethod
    def from_capability(
        cls,
        capability: str,
        *,
        state_root: Path | None = None,
    ) -> tuple["SweepSession", dict[str, Any]]:
        match = CAPABILITY_RE.fullmatch(capability) if isinstance(capability, str) else None
        if match is None:
            raise ReceiptViolation("model-call capability is malformed")
        session = cls.open(match.group(1), state_root=state_root)
        binding = session.resolve_capability(capability)
        return session, binding

    def resolve_capability(self, capability: str) -> dict[str, Any]:
        match = CAPABILITY_RE.fullmatch(capability) if isinstance(capability, str) else None
        if match is None or match.group(1) != self.session_id:
            raise ReceiptViolation("model-call capability is malformed or cross-session")
        digest = match.group(2)
        with self._locked_state() as state:
            self._assert_live_head(state)
            capabilities = state.get("capabilities")
            binding = capabilities.get(digest) if isinstance(capabilities, dict) else None
            if not isinstance(binding, dict):
                raise ReceiptViolation("model-call capability does not belong to this session")
            expected = hmac.new(
                bytes.fromhex(state["receipt_key"]),
                ("capability:" + json.dumps(binding, sort_keys=True, separators=(",", ":"))).encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(expected, digest):
                raise ReceiptViolation("model-call capability signature is invalid")
            if binding.get("session_id") != self.session_id or binding.get("head") != state["head"]:
                raise ReceiptViolation("model-call capability is stale")
            self._comment(state, binding.get("comment_id"))
            return json.loads(json.dumps(binding))

    def review_comment(self, comment_id: str) -> dict[str, Any]:
        with self._locked_state() as state:
            self._assert_live_head(state)
            comment = self._comment(state, comment_id)
            from .helpers.read_only import sweep_analyst_payload, sweep_export_record

            normalized = comment["body"].replace("\r\n", "\n").replace("\r", "\n")
            export = sweep_export_record(normalized)
            matched_lines = [] if export is None else export["matched_lines"]
            shaped = sweep_analyst_payload(
                {
                    "text": normalized,
                    "truncated": comment["truncated"],
                    "matched_lines": matched_lines,
                },
                comment_id,
            )
            if shaped.get("exit_code") != 0:
                raise IsolationViolation("review comment could not be shaped")
            try:
                block = json.loads(shaped["stdout"])["text"]
            except (KeyError, TypeError, json.JSONDecodeError) as exc:
                raise IsolationViolation("review comment shaping returned no bounded block") from exc
            return {
                "comment_id": comment_id,
                "surface": comment["surface"],
                "block": block,
                "export": export,
                "classes": list(CLASS_VALUES),
                "targets": list(ARTIFACT_ALLOWLIST),
            }

    def submit_result(
        self,
        stage: str,
        payload: Any,
        *,
        perspective: str | None = None,
    ) -> str:
        with self._locked_state() as state:
            self._assert_live_head(state)
            normalized = validate_result(
                stage,
                payload,
                perspective=perspective,
                snapshot=GitSnapshot.capture(Path(state["repo_root"]), head=state["head"]),
            )
            comment_id = normalized["comment_id"]
            self._comment(state, comment_id)
            if stage == "synthesis":
                accepted_classifier = state["accepted"]["classifier"].get(comment_id)
                if isinstance(accepted_classifier, str):
                    classifier = self._accepted_amended_classifier(state, comment_id)
                    edit = normalized.get("edit")
                    if isinstance(edit, dict) and edit.get("file") != classifier.get("target"):
                        raise SchemaViolation("synthesis target differs from the accepted classifier target")
                accepted_perspectives = state["accepted"]["perspective"].get(comment_id, {})
                if isinstance(accepted_perspectives, dict) and set(accepted_perspectives) == set(
                    PERSPECTIVES
                ):
                    perspective_records = [
                        state["results"][accepted_perspectives[name]]["payload"]
                        for name in PERSPECTIVES
                    ]
                    has_escape = any(record["escape_hatch"] for record in perspective_records)
                    is_escape_review = (
                        normalized["outcome"] == "human_review"
                        and normalized["basis"] == "escape_unresolved"
                    )
                    if has_escape != is_escape_review:
                        raise SchemaViolation(
                            "synthesis outcome does not preserve the accepted escape hatch"
                        )
                    if normalized["basis"] == "analyst_failed":
                        raise SchemaViolation(
                            "analyst_failed cannot follow three accepted perspectives"
                        )
            nonce = secrets.token_hex(16)
            binding = {
                "session_id": self.session_id,
                "head": state["head"],
                "stage": stage,
                "comment_id": comment_id,
                "perspective": perspective,
                "nonce": nonce,
                "payload_sha256": hashlib.sha256(
                    json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("utf-8")
                ).hexdigest(),
            }
            digest = hmac.new(
                bytes.fromhex(state["receipt_key"]),
                json.dumps(binding, sort_keys=True, separators=(",", ":")).encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            if digest in state["results"]:
                raise ReceiptViolation("receipt collision")
            state["results"][digest] = {
                **binding,
                "payload": normalized,
                "used": False,
                "created_at": self._clock(),
            }
            return RECEIPT_PREFIX + digest

    def _consume_result(self, receipt: str, *, expected_stage: str) -> dict[str, Any]:
        match = RECEIPT_RE.fullmatch(receipt) if isinstance(receipt, str) else None
        if match is None:
            raise ReceiptViolation("result is not an exact sweep receipt")
        digest = match.group(1)
        with self._locked_state() as state:
            self._assert_live_head(state)
            result = state["results"].get(digest)
            if not isinstance(result, dict):
                raise ReceiptViolation("receipt does not belong to this sweep session")
            if result.get("stage") != expected_stage:
                raise ReceiptViolation("receipt stage does not match this transition")
            if result.get("head") != state["head"] or result.get("session_id") != self.session_id:
                raise ReceiptViolation("receipt binding is stale or cross-session")
            if result.get("used") is not False:
                raise ReceiptViolation("receipt has already been used")
            result["used"] = True
            comment_id = result["comment_id"]
            if expected_stage == "perspective":
                state["accepted"]["perspective"].setdefault(comment_id, {})[
                    result["payload"]["perspective"]
                ] = digest
            else:
                state["accepted"][expected_stage][comment_id] = digest
            return json.loads(json.dumps(result))

    def accept_receipt(self, receipt: str, *, expected_stage: str) -> dict[str, Any]:
        result = self._consume_result(receipt, expected_stage=expected_stage)
        payload = result["payload"]
        if expected_stage == "classifier":
            return {
                "comment_id": payload["comment_id"],
                "class": payload["class"],
                "target": payload["target"],
            }
        if expected_stage == "perspective":
            return {
                "comment_id": payload["comment_id"],
                "perspective": payload["perspective"],
                "status": "accepted",
            }
        if expected_stage == "synthesis":
            return {
                "comment_id": payload["comment_id"],
                "outcome": payload["outcome"],
                "agreement": payload["agreement"],
                "basis": payload["basis"],
                "status": "accepted",
            }
        raise ReceiptViolation("receipt stage is unknown")

    def consensus_inputs(self, comment_id: str, *, stage: str) -> dict[str, Any]:
        with self._locked_state() as state:
            self._assert_live_head(state)
            self._comment(state, comment_id)
            accepted = state["accepted"]
            if stage == "classifier":
                return {"comment_id": comment_id}
            classifier_digest = accepted["classifier"].get(comment_id)
            if classifier_digest is None:
                raise ReceiptViolation("classifier receipt has not been accepted")
            classifier = state["results"][classifier_digest]["payload"]
            if stage == "perspective":
                return {
                    "comment_id": comment_id,
                    "target": classifier["target"],
                    "classifier": classifier,
                }
            if stage == "synthesis":
                found = accepted["perspective"].get(comment_id, {})
                if set(found) != set(PERSPECTIVES):
                    raise ReceiptViolation("three accepted perspectives are required")
                return {
                    "comment_id": comment_id,
                    "target": classifier["target"],
                    "perspectives": [state["results"][found[name]]["payload"] for name in PERSPECTIVES],
                }
            raise ReceiptViolation("consensus stage is unknown")


def _require_exact_keys(payload: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != keys:
        raise SchemaViolation(f"{label} fields do not match the exact schema")
    return dict(payload)


def _bounded_nonempty(value: Any, limit: int, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.encode("utf-8")) > limit:
        raise SchemaViolation(f"{label} is empty or over bound")
    return value


def _safe_evidence_path(value: str, snapshot: GitSnapshot) -> None:
    match = re.fullmatch(r"(.+?)(?::([1-9][0-9]*))?", value)
    if match is None:
        raise SchemaViolation("evidence citation is malformed")
    try:
        snapshot.entry(match.group(1))
    except IsolationViolation as exc:
        raise SchemaViolation("evidence citation is outside the snapshot") from exc


def validate_result(
    stage: str,
    payload: Any,
    *,
    perspective: str | None,
    snapshot: GitSnapshot,
) -> dict[str, Any]:
    if stage == "classifier":
        record = _require_exact_keys(payload, {"comment_id", "class", "target", "reason"}, stage)
        _bounded_nonempty(record["comment_id"], 256, "comment_id")
        if record["class"] not in CLASS_VALUES:
            raise SchemaViolation("classifier class is outside the closed vocabulary")
        amended = record["class"] == "amended"
        if (amended and record["target"] not in ARTIFACT_ALLOWLIST) or (
            not amended and record["target"] is not None
        ):
            raise SchemaViolation("classifier target does not match the class")
        reason = _bounded_nonempty(record["reason"], MAX_REASON_BYTES, "reason")
        if any(character in reason for character in "|\r\n"):
            raise SchemaViolation("classifier reason is not one physical table-safe line")
        return record
    if stage == "perspective":
        record = _require_exact_keys(
            payload,
            {"comment_id", "perspective", "finding", "evidence", "escape_hatch"},
            stage,
        )
        _bounded_nonempty(record["comment_id"], 256, "comment_id")
        if record["perspective"] not in PERSPECTIVES or record["perspective"] != perspective:
            raise SchemaViolation("perspective does not match the dispatched perspective")
        _bounded_nonempty(record["finding"], MAX_FINDING_BYTES, "finding")
        evidence = record["evidence"]
        if not isinstance(evidence, list) or len(evidence) > 32 or any(
            not isinstance(item, str) for item in evidence
        ):
            raise SchemaViolation("perspective evidence must be a bounded string array")
        for citation in evidence:
            _safe_evidence_path(citation, snapshot)
        if not isinstance(record["escape_hatch"], bool):
            raise SchemaViolation("escape_hatch must be a boolean")
        if len(json.dumps(record, ensure_ascii=False).encode("utf-8")) > MAX_COMMENT_BYTES:
            raise SchemaViolation("perspective record exceeds its total bound")
        return record
    if stage == "synthesis":
        record = _require_exact_keys(
            payload,
            {"comment_id", "outcome", "agreement", "basis", "edit"},
            stage,
        )
        _bounded_nonempty(record["comment_id"], 256, "comment_id")
        if record["outcome"] not in {"resolved", "human_review"}:
            raise SchemaViolation("synthesis outcome is unknown")
        if record["outcome"] == "human_review":
            if (
                record["agreement"] is not None
                or record["basis"] not in {"all_disagree", "escape_unresolved", "analyst_failed"}
                or record["edit"] is not None
            ):
                raise SchemaViolation("human-review synthesis fields are inconsistent")
            return record
        if record["agreement"] not in {"3/3", "2/3"} or record["basis"] is not None:
            raise SchemaViolation("resolved synthesis fields are inconsistent")
        edit = _require_exact_keys(record["edit"], {"file", "anchor", "replacement"}, "edit")
        if edit["file"] not in ARTIFACT_ALLOWLIST:
            raise SchemaViolation("synthesis edit targets a non-artifact path")
        _bounded_nonempty(edit["anchor"], MAX_ANCHOR_BYTES, "anchor")
        if not isinstance(edit["replacement"], str) or len(edit["replacement"].encode("utf-8")) > MAX_REPLACEMENT_BYTES:
            raise SchemaViolation("replacement is not text or exceeds its bound")
        record["edit"] = edit
        return record
    raise SchemaViolation("result stage is unknown")


def redact_model_text(text: str) -> tuple[str, int]:
    lines = text.splitlines(keepends=True)
    output: list[str] = []
    redactions = 0
    inside_key = False
    for line in lines:
        stripped = line.strip()
        if PRIVATE_KEY_RE.fullmatch(stripped):
            inside_key = True
            output.append("[redacted: private_key]\n" if line.endswith(("\n", "\r")) else "[redacted: private_key]")
            redactions += 1
            continue
        if inside_key:
            output.append("[redacted: private_key]\n" if line.endswith(("\n", "\r")) else "[redacted: private_key]")
            redactions += 1
            if stripped.startswith("-----END ") and stripped.endswith("PRIVATE KEY-----"):
                inside_key = False
            continue
        shaped = line
        for pattern, rule in OUTBOUND_SECRET_RULES:
            while True:
                found = pattern.search(shaped)
                if found is None:
                    break
                start, end = found.span(1)
                shaped = shaped[:start] + f"[redacted: {rule}]" + shaped[end:]
                redactions += 1
        output.append(shaped)
    if not lines and text:
        return text, 0
    return "".join(output), redactions


def _safe_feature_dir(repo_root: Path, feature_dir: str) -> Path:
    normalized = _normalize_snapshot_path(feature_dir)
    target = repo_root / normalized
    current = repo_root
    for component in PurePosixPath(normalized).parts:
        current = current / component
        try:
            info = current.lstat()
        except OSError as exc:
            raise MutationViolation("feature directory cannot be inspected safely") from exc
        if stat.S_ISLNK(info.st_mode):
            raise MutationViolation("feature directory crosses a symlink")
    if not target.is_dir():
        raise MutationViolation("feature directory is not a directory")
    return target


def apply_synthesis_receipt(
    repo_root: Path,
    feature_dir: str,
    session: SweepSession,
    receipt: str,
    *,
    mode: str,
) -> dict[str, Any]:
    if mode not in {"dry_run", "apply"}:
        raise MutationViolation("mutation mode must be dry_run or apply")
    root = repo_root.resolve(strict=True)
    if root != session.repo_root().resolve(strict=True):
        raise MutationViolation("mutation repository does not match the sweep session")
    session_head = session.head()
    if current_head(root) != session_head:
        raise MutationViolation("repository HEAD changed before mutation")
    result = session._consume_result(receipt, expected_stage="synthesis")
    payload = result["payload"]
    if result["head"] != session_head:
        raise MutationViolation("receipt head does not match the sweep session")
    if payload["outcome"] == "human_review":
        return {
            "status": "human_review",
            "comment_id": payload["comment_id"],
            "head": result["head"],
        }
    feature_path = _safe_feature_dir(root, feature_dir)
    edit = payload["edit"]
    if edit["file"] not in ARTIFACT_ALLOWLIST:
        raise MutationViolation("artifact target is outside the allowlist")
    target = feature_path / edit["file"]
    relative = target.relative_to(root).as_posix()
    snapshot = GitSnapshot.capture(root, head=result["head"])
    try:
        snapshot_entry = snapshot.entry(relative)
    except IsolationViolation as exc:
        raise MutationViolation("artifact is not present in the frozen snapshot") from exc
    try:
        info = target.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise MutationViolation("artifact target is not a regular file")
        live_bytes = target.read_bytes()
        live_text = live_bytes.decode("utf-8", errors="strict")
    except (OSError, UnicodeDecodeError) as exc:
        raise MutationViolation("artifact target cannot be read safely") from exc
    live_digest = hashlib.sha256(live_bytes).hexdigest()
    if live_digest != snapshot_entry.sha256:
        raise MutationViolation("artifact bytes changed after the frozen snapshot")
    anchor = edit["anchor"]
    if live_text.count(anchor) != 1:
        raise MutationViolation("edit anchor must match exactly once")
    replacement, redaction_count = redact_model_text(edit["replacement"])
    updated = live_text.replace(anchor, replacement, 1)
    updated_bytes = updated.encode("utf-8")
    after_digest = hashlib.sha256(updated_bytes).hexdigest()
    status = "planned_redacted" if redaction_count else "planned"
    if mode == "apply":
        if current_head(root) != result["head"]:
            raise MutationViolation("repository HEAD changed during mutation validation")
        try:
            from .helpers.mutation import snapshot_write_target, write_bytes_atomic

            expected = snapshot_write_target(target, root)
            if expected.get("digest") != live_digest:
                raise MutationViolation("artifact changed during mutation validation")
            write_bytes_atomic(target, updated_bytes, trust_root=root, expected_snapshot=expected)
        except MutationViolation:
            raise
        except OSError as exc:
            raise MutationViolation("atomic artifact write failed") from exc
        status = "applied_redacted" if redaction_count else "applied"
    return {
        "status": status,
        "comment_id": payload["comment_id"],
        "path": relative,
        "head": result["head"],
        "before_sha256": live_digest,
        "after_sha256": after_digest,
        "redaction_count": redaction_count,
    }
