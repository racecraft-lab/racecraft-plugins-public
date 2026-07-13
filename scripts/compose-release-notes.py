#!/usr/bin/env python3
"""Capture immutable release inputs and compose public GitHub Release highlights.

Capture and release mutation use GitHub's REST API through ``urllib``. Live
composition reads only a canonical snapshot for Compare and pull-request data;
the dry-run path performs no network or release mutations.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))
import release_note_policy as _release_note_policy  # noqa: E402

CompositionError = _release_note_policy.CompositionError
CONVENTIONAL_PREFIX_RE = _release_note_policy.CONVENTIONAL_PREFIX_RE
DiscoveredCommit = _release_note_policy.DiscoveredCommit
SKIP_LABEL = _release_note_policy.SKIP_LABEL
TRAILING_PR_RE = _release_note_policy.TRAILING_PR_RE
_label_names = _release_note_policy._label_names
_validation_inputs_from_environment = _release_note_policy._validation_inputs_from_environment
extract_release_note = _release_note_policy.extract_release_note
sanitize_fallback_subject = _release_note_policy.sanitize_fallback_subject
sanitize_release_note = _release_note_policy.sanitize_release_note
validate_release_note = _release_note_policy.validate_release_note
MAX_COMPARE_COMMITS = 250
SNAPSHOT_SCHEMA_VERSION = 1
APPENDIX_HEADING = "## Commit appendix"
HIGHLIGHTS_HEADING = "## Highlights"
FAILURE_OUTCOME = "release_note_composition_failed"
VALIDATION_FAILURE_OUTCOME = "release_note_validation_failed"
VALIDATION_PASS_OUTCOME = "release_note_validation_passed"
SNAPSHOT_MARKER_PREFIX = "<!-- release-note-composer-snapshot:v1 "

COMPARE_HEADING_RE = re.compile(
    r"(?m)^#{1,6}[ \t]+.*?\]\([^\n)]*/compare/"
    r"(?P<previous>[^\s)]+?)\.\.\.(?P<current>[^\s)]+)\)"
)
MERGE_COMMIT_SUBJECT_RE = re.compile(r"^Merge pull request #(?P<number>[1-9][0-9]*) from \S+$")
SNAPSHOT_MARKER_RE = re.compile(
    r"\n\n<!-- release-note-composer-snapshot:v1 "
    r"source_sha256=(?P<source_sha256>[0-9a-f]{64}) "
    r"payload_sha256=(?P<payload_sha256>[0-9a-f]{64}) "
    r"compare_commit_count=(?P<compare_commit_count>0|[1-9][0-9]{0,2}) -->\Z"
)
@dataclass(frozen=True)
class PersistedSnapshot:
    """Digest-verified composed body persisted in the GitHub Release itself."""
    payload: str
    source_sha256: str
    payload_sha256: str
    body_sha256: str
    compare_commit_count: int


@dataclass(frozen=True)
class ReleaseInputSnapshot:
    """Canonical immutable inputs captured before release-body composition."""
    raw_body: str
    repository: str
    tag: str
    previous_tag: str
    commits: tuple[DiscoveredCommit, ...]
    pulls: Mapping[int, Mapping[str, object]]
    sha256: str
    byte_count: int
    commit_count: int


class GitHubClient:
    """Minimal no-retry GitHub REST client."""

    def __init__(
        self,
        repository: str,
        token: str,
        *,
        api_url: str = "https://api.github.com",
        timeout: float = 30.0,
    ) -> None:
        if not re.fullmatch(r"[^/\s]+/[^/\s]+", repository):
            raise CompositionError("GITHUB_REPOSITORY must be owner/repository")
        if not token:
            raise CompositionError("GITHUB_TOKEN is required")
        self.repository = repository
        self.token = token
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout

    def request_json(
        self,
        method: str,
        path: str,
        payload: Mapping[str, object] | None = None,
    ) -> tuple[dict, dict[str, str]]:
        """Make exactly one JSON request; callers recover by re-running the job."""
        data = None
        if payload is not None:
            data = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(
            f"{self.api_url}{path}",
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "racecraft-release-note-composer",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
                headers = {key: value for key, value in response.headers.items()}
        except urllib.error.HTTPError as error:
            raise CompositionError(f"GitHub API HTTP {error.code} for {method} {path}") from error
        except (urllib.error.URLError, http.client.IncompleteRead, TimeoutError, OSError) as error:
            raise CompositionError(f"GitHub API transport error for {method} {path}: {error}") from error

        try:
            decoded = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CompositionError(f"GitHub API returned invalid JSON for {method} {path}") from error
        if not isinstance(decoded, dict):
            raise CompositionError(f"GitHub API returned a non-object for {method} {path}")
        return decoded, headers


def parse_previous_tag(release_body: str, new_tag: str) -> str:
    """Read the previous tag from release-please's raw compare-link heading."""
    for match in COMPARE_HEADING_RE.finditer(release_body):
        previous = urllib.parse.unquote(match.group("previous"))
        current = urllib.parse.unquote(match.group("current"))
        if current == new_tag:
            return previous
    raise CompositionError(f"raw release body has no compare heading ending at tag {new_tag!r}")


def _header_value(headers: Mapping[str, str], name: str) -> str:
    for key, value in headers.items():
        if key.lower() == name.lower():
            return value
    return ""


def discover_commits(
    compare: Mapping[str, object],
    headers: Mapping[str, str],
) -> list[DiscoveredCommit]:
    """Validate one complete Compare response and discover every trailing PR."""
    if _header_value(headers, "Link").strip():
        raise CompositionError("Compare API response is paginated")

    commits_value = compare.get("commits")
    total_value = compare.get("total_commits")
    if not isinstance(commits_value, list) or isinstance(total_value, bool) or not isinstance(total_value, int):
        raise CompositionError("Compare API response is missing commits or total_commits")
    if total_value != len(commits_value):
        raise CompositionError(
            f"Compare API response is truncated: total_commits={total_value}, returned={len(commits_value)}"
        )
    if total_value > MAX_COMPARE_COMMITS:
        raise CompositionError(
            f"Compare API range exceeds the non-paginated {MAX_COMPARE_COMMITS}-commit limit: "
            f"total_commits={total_value}"
        )

    discovered: list[DiscoveredCommit] = []
    seen: set[int] = set()
    for index, item in enumerate(commits_value):
        if not isinstance(item, dict):
            raise CompositionError(f"Compare API commit {index} is not an object")
        commit = item.get("commit")
        message = commit.get("message") if isinstance(commit, dict) else None
        if not isinstance(message, str) or not message.splitlines():
            raise CompositionError(f"Compare API commit {index} has no subject")
        subject = message.splitlines()[0].strip()
        pr_match = TRAILING_PR_RE.search(subject) or MERGE_COMMIT_SUBJECT_RE.match(subject)
        if pr_match is None:
            # A merge-commit range lists inner branch commits that carry no PR
            # reference of their own; the merge commit resolves their PR.
            continue
        number = int(pr_match.group("number"))
        prefix_match = CONVENTIONAL_PREFIX_RE.match(subject)
        kind = prefix_match.group("kind").lower() if prefix_match else ""
        if number not in seen:
            seen.add(number)
            discovered.append(DiscoveredCommit(number, subject, kind))
    if commits_value and not discovered:
        raise CompositionError("Compare range commit subjects resolved no pull requests")
    return discovered


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_persisted_snapshot(
    release_body: str,
    raw_release_body: str,
    *,
    expected_source_sha256: str | None = None,
) -> PersistedSnapshot | None:
    """Load an existing composed body only when all immutable digests verify."""
    if not release_body.startswith(f"{HIGHLIGHTS_HEADING}\n"):
        return None
    marker = f"\n\n{SNAPSHOT_MARKER_PREFIX}"
    if release_body.count(marker) != 1:
        raise CompositionError("existing composed release has no unique snapshot audit marker")

    match = SNAPSHOT_MARKER_RE.search(release_body)
    if match is None:
        raise CompositionError("existing composed release has no valid snapshot audit metadata")

    payload = release_body[: match.start()]
    source_sha256 = match.group("source_sha256")
    if expected_source_sha256 is not None:
        if not re.fullmatch(r"[0-9a-f]{64}", expected_source_sha256):
            raise CompositionError("expected persisted snapshot source digest is invalid")
        if source_sha256 != expected_source_sha256:
            raise CompositionError("persisted release-note snapshot source digest does not match input snapshot")

    payload_sha256 = _sha256_text(payload)
    if match.group("payload_sha256") != payload_sha256:
        raise CompositionError("persisted release-note snapshot payload digest verification failed")
    if not payload.endswith(raw_release_body):
        raise CompositionError("persisted release-note snapshot appendix does not match RELEASE_BODY")

    compare_commit_count = int(match.group("compare_commit_count"))
    if compare_commit_count > MAX_COMPARE_COMMITS:
        raise CompositionError("persisted release-note snapshot Compare commit count exceeds 250")
    return PersistedSnapshot(
        payload=payload,
        source_sha256=source_sha256,
        payload_sha256=payload_sha256,
        body_sha256=_sha256_text(release_body),
        compare_commit_count=compare_commit_count,
    )


def _format_highlight(note: str) -> str:
    lines = note.splitlines() or [note]
    return "- " + lines[0] + "".join(f"\n  {line}" for line in lines[1:])


def compose_release_body(
    raw_release_body: str,
    commits: Sequence[DiscoveredCommit],
    pulls: Mapping[int, Mapping[str, object]],
    *,
    compare_commit_count: int,
    source_sha256: str | None = None,
) -> str:
    """Compose Highlights while embedding only the raw action body as appendix."""
    if isinstance(compare_commit_count, bool) or not isinstance(compare_commit_count, int):
        raise CompositionError("release input snapshot Compare commit count is invalid")
    if compare_commit_count < len(commits):
        raise CompositionError(
            "release input snapshot Compare commit count is smaller than the resolved pull set"
        )
    if compare_commit_count > MAX_COMPARE_COMMITS:
        raise CompositionError("release input snapshot Compare commit count exceeds 250")
    if source_sha256 is None:
        source_sha256 = _sha256_text(raw_release_body)
    if not re.fullmatch(r"[0-9a-f]{64}", source_sha256):
        raise CompositionError("release input snapshot source digest is invalid")

    entries: list[tuple[DiscoveredCommit, str | None, bool]] = []
    block_count = 0
    for commit in commits:
        pr = pulls.get(commit.pr_number)
        if not isinstance(pr, Mapping):
            raise CompositionError(f"unable to resolve pull request #{commit.pr_number}")
        skipped = SKIP_LABEL in _label_names(pr)
        body_value = pr.get("body")
        if body_value is None:
            body_value = ""
        if not isinstance(body_value, str):
            raise CompositionError(f"pull request #{commit.pr_number} body is not text")
        extracted = extract_release_note(body_value)
        note = sanitize_release_note(extracted) if extracted is not None else None
        if extracted is not None and not note:
            raise CompositionError(
                f"pull request #{commit.pr_number} release-note block is empty after sanitization"
            )
        if note is not None and not skipped:
            block_count += 1
        entries.append((commit, note, skipped))

    highlights: list[str] = []
    for commit, note, skipped in entries:
        if skipped:
            continue
        if note is not None:
            highlights.append(note)
            continue
        if block_count != 0 and commit.kind not in {"feat", "fix"}:
            continue
        fallback = sanitize_fallback_subject(commit.subject)
        highlights.append(fallback)

    rendered = "\n".join(_format_highlight(highlight) for highlight in highlights)
    if not rendered:
        rendered = "No consumer-visible changes."

    # Guard rail: raw_release_body is the release action's body output and is
    # the only appendix source. Discovery is Compare-API-only; never substitute
    # the live release body or rendered changelog links here.
    payload = f"{HIGHLIGHTS_HEADING}\n\n{rendered}\n\n{APPENDIX_HEADING}\n\n{raw_release_body}"
    marker = (
        f"{SNAPSHOT_MARKER_PREFIX}"
        f"source_sha256={source_sha256} "
        f"payload_sha256={_sha256_text(payload)} "
        f"compare_commit_count={compare_commit_count} -->"
    )
    return f"{payload}\n\n{marker}"


def canonical_snapshot_bytes(snapshot: Mapping[str, object]) -> bytes:
    """Encode the immutable input snapshot in its sole accepted byte form."""
    try:
        encoded = json.dumps(
            snapshot,
            allow_nan=False,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as error:
        raise CompositionError(f"release input snapshot is not JSON-serializable: {error}") from error
    return f"{encoded}\n".encode("utf-8")


def capture_release_input_snapshot(
    client: GitHubClient,
    tag: str,
    raw_body: str,
    explicit_previous_tag: str | None = None,
) -> dict[str, object]:
    """Capture Compare plus normalized PR body/labels for immutable replay."""
    previous_tag = explicit_previous_tag or parse_previous_tag(raw_body, tag)
    base = urllib.parse.quote(previous_tag, safe="")
    head = urllib.parse.quote(tag, safe="")
    compare, headers = client.request_json(
        "GET",
        f"/repos/{client.repository}/compare/{base}...{head}",
    )
    commits = discover_commits(compare, headers)
    pulls: dict[str, dict[str, object]] = {}
    for commit in commits:
        try:
            pr, _headers = client.request_json(
                "GET",
                f"/repos/{client.repository}/pulls/{commit.pr_number}",
            )
        except CompositionError as error:
            raise CompositionError(f"unable to resolve pull request #{commit.pr_number}: {error}") from error
        body = pr.get("body")
        if body is None:
            body = ""
        if not isinstance(body, str):
            raise CompositionError(f"pull request #{commit.pr_number} body is not text")
        pulls[str(commit.pr_number)] = {
            "body": body,
            "labels": sorted(_label_names(pr)),
        }

    link = _header_value(headers, "Link").strip()
    compare_headers = {"Link": link} if link else {}
    return {
        "compare": compare,
        "compare_headers": compare_headers,
        "previous_tag": previous_tag,
        "pulls": pulls,
        "release_body": raw_body,
        "repository": client.repository,
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "tag": tag,
    }


def load_release_input_snapshot(
    path: str,
    *,
    expected_sha256: str | None = None,
    expected_repository: str | None = None,
    expected_tag: str | None = None,
) -> ReleaseInputSnapshot:
    """Load and fully validate canonical immutable composition inputs."""
    try:
        raw = sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()
    except OSError as error:
        raise CompositionError(f"unable to load release input snapshot: {error}") from error
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CompositionError(f"release input snapshot is not valid UTF-8 JSON: {error}") from error
    if not isinstance(value, dict):
        raise CompositionError("release input snapshot must be a JSON object")
    if raw != canonical_snapshot_bytes(value):
        raise CompositionError("release input snapshot bytes are not canonical JSON")

    digest = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None:
        if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
            raise CompositionError("expected release input snapshot digest is not lowercase SHA-256")
        if digest != expected_sha256:
            raise CompositionError("release input snapshot digest verification failed")

    expected_keys = {
        "compare",
        "compare_headers",
        "previous_tag",
        "pulls",
        "release_body",
        "repository",
        "schema_version",
        "tag",
    }
    if set(value) != expected_keys or value.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        raise CompositionError("release input snapshot schema is invalid")

    repository = value.get("repository")
    tag = value.get("tag")
    previous_tag = value.get("previous_tag")
    raw_body = value.get("release_body")
    compare = value.get("compare")
    headers = value.get("compare_headers")
    pulls_value = value.get("pulls")
    if not isinstance(repository, str) or not re.fullmatch(r"[^/\s]+/[^/\s]+", repository):
        raise CompositionError("release input snapshot repository is invalid")
    if not isinstance(tag, str) or not tag.strip():
        raise CompositionError("release input snapshot tag is invalid")
    if not isinstance(previous_tag, str) or not previous_tag.strip():
        raise CompositionError("release input snapshot previous_tag is invalid")
    if not isinstance(raw_body, str):
        raise CompositionError("release input snapshot release_body is not text")
    if not isinstance(compare, dict) or not isinstance(headers, dict):
        raise CompositionError("release input snapshot compare data is invalid")
    if not all(isinstance(key, str) and isinstance(item, str) for key, item in headers.items()):
        raise CompositionError("release input snapshot compare headers are invalid")
    if not isinstance(pulls_value, dict):
        raise CompositionError("release input snapshot pulls must be an object")
    if expected_repository is not None and repository != expected_repository:
        raise CompositionError("release input snapshot repository does not match GITHUB_REPOSITORY")
    if expected_tag is not None and tag != expected_tag:
        raise CompositionError("release input snapshot tag does not match release tag")
    if parse_previous_tag(raw_body, tag) != previous_tag:
        raise CompositionError("release input snapshot tag range does not match release body")

    commits = discover_commits(compare, headers)
    expected_pull_keys = {str(commit.pr_number) for commit in commits}
    if set(pulls_value) != expected_pull_keys:
        missing = sorted(expected_pull_keys - set(pulls_value))
        extra = sorted(set(pulls_value) - expected_pull_keys)
        raise CompositionError(
            f"release input snapshot pull set mismatch: missing={missing}, extra={extra}"
        )

    pulls: dict[int, Mapping[str, object]] = {}
    for commit in commits:
        metadata = pulls_value[str(commit.pr_number)]
        if not isinstance(metadata, dict) or set(metadata) != {"body", "labels"}:
            raise CompositionError(f"release input snapshot pull #{commit.pr_number} schema is invalid")
        body = metadata.get("body")
        labels = metadata.get("labels")
        if not isinstance(body, str):
            raise CompositionError(f"release input snapshot pull #{commit.pr_number} body is not text")
        if (
            not isinstance(labels, list)
            or not all(isinstance(label, str) for label in labels)
            or labels != sorted(set(labels))
        ):
            raise CompositionError(f"release input snapshot pull #{commit.pr_number} labels are invalid")
        pulls[commit.pr_number] = {"body": body, "labels": labels}

    total_commits = compare.get("total_commits")
    if isinstance(total_commits, bool) or not isinstance(total_commits, int):
        raise CompositionError("release input snapshot Compare total_commits is invalid")
    return ReleaseInputSnapshot(
        raw_body=raw_body,
        repository=repository,
        tag=tag,
        previous_tag=previous_tag,
        commits=tuple(commits),
        pulls=pulls,
        sha256=digest,
        byte_count=len(raw),
        commit_count=total_commits,
    )

def _resolve_release(client: GitHubClient, tag: str) -> tuple[int, str]:
    quoted_tag = urllib.parse.quote(tag, safe="")
    release, _headers = client.request_json("GET", f"/repos/{client.repository}/releases/tags/{quoted_tag}")
    release_id = release.get("id")
    if isinstance(release_id, bool) or not isinstance(release_id, int) or release_id <= 0:
        raise CompositionError(f"release lookup for tag {tag!r} returned no numeric id")
    release_body = release.get("body")
    if not isinstance(release_body, str):
        raise CompositionError(f"release lookup for tag {tag!r} returned no text body")
    return release_id, release_body


def _write_step_summary(message: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if not summary_path:
        return
    try:
        with Path(summary_path).open("a", encoding="utf-8") as summary:
            summary.write(message.rstrip() + "\n")
    except OSError:
        pass


def _write_github_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT", "")
    if not output_path:
        return
    try:
        with Path(output_path).open("a", encoding="utf-8") as output:
            output.write(f"{name}={value}\n")
    except OSError as error:
        raise CompositionError(f"unable to write GITHUB_OUTPUT: {error}") from error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", default=os.environ.get("RELEASE_TAG"), help="new release tag")
    parser.add_argument("--prev-tag", help="override previous tag (normally parsed from release body)")
    parser.add_argument("--dry-run", action="store_true", help="compose from an offline fixture without API calls")
    parser.add_argument(
        "--capture-snapshot", action="store_true",
        help="capture immutable Compare and PR inputs without mutating a release",
    )
    parser.add_argument("--validate-pr", action="store_true", help="validate one PR from env-only inputs")
    environment_options = {
        "--fixture": ("RELEASE_NOTES_FIXTURE", "offline JSON fixture path for --dry-run, or - for stdin"),
        "--snapshot": ("RELEASE_NOTES_SNAPSHOT", "canonical immutable input snapshot for live composition"),
        "--expected-snapshot-sha256": ("EXPECTED_SNAPSHOT_SHA256", "expected lowercase SHA-256 of the canonical input snapshot"),
    }
    for option, (environment, help_text) in environment_options.items():
        parser.add_argument(option, default=os.environ.get(environment), help=help_text)
    parser.add_argument(
        "--snapshot-output",
        default=os.environ.get("RELEASE_NOTES_SNAPSHOT_OUTPUT", "release-note-snapshot.json"),
        help="canonical snapshot output path for --capture-snapshot",
    )
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.validate_pr:
            if (
                args.capture_snapshot
                or args.dry_run
                or args.expected_snapshot_sha256
                or args.fixture
                or args.prev_tag
                or args.snapshot
                or args.tag
            ):
                raise CompositionError("--validate-pr cannot be combined with composition arguments")
            title, body, labels, draft = _validation_inputs_from_environment()
            valid, reason = validate_release_note(title, body, labels, draft=draft)
            result = {"outcome": VALIDATION_PASS_OUTCOME if valid else VALIDATION_FAILURE_OUTCOME, "reason": reason}
            stream = sys.stdout if valid else sys.stderr
            print(json.dumps(result, sort_keys=True, separators=(",", ":")), file=stream)
            return 0 if valid else 1

        if not args.tag:
            raise CompositionError("release tag is required via --tag or RELEASE_TAG")

        if args.capture_snapshot:
            if args.dry_run or args.fixture or args.snapshot or args.expected_snapshot_sha256:
                raise CompositionError("--capture-snapshot cannot be combined with composition inputs")
            raw_body = os.environ.get("RELEASE_BODY")
            if raw_body is None:
                raise CompositionError("RELEASE_BODY is required for --capture-snapshot")
            repository = os.environ.get("GITHUB_REPOSITORY", "")
            token = os.environ.get("GITHUB_TOKEN", "")
            api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")
            client = GitHubClient(repository, token, api_url=api_url)
            snapshot_value = capture_release_input_snapshot(client, args.tag, raw_body, args.prev_tag)
            snapshot_bytes = canonical_snapshot_bytes(snapshot_value)
            try:
                Path(args.snapshot_output).write_bytes(snapshot_bytes)
            except OSError as error:
                raise CompositionError(f"unable to write release input snapshot: {error}") from error
            snapshot_sha256 = hashlib.sha256(snapshot_bytes).hexdigest()
            commits_value = snapshot_value["compare"].get("total_commits")
            pull_count = len(snapshot_value["pulls"])
            result = {
                "commit_count": commits_value,
                "outcome": "release_note_snapshot_captured",
                "pull_request_count": pull_count,
                "snapshot_byte_count": len(snapshot_bytes),
                "snapshot_sha256": snapshot_sha256,
                "tag": args.tag,
            }
            print(json.dumps(result, sort_keys=True, separators=(",", ":")))
            _write_github_output("snapshot_sha256", snapshot_sha256)
            _write_step_summary(
                f"### Release note input captured\n\n- Tag: `{args.tag}`\n"
                f"- Commits: {commits_value}\n- Pull requests: {pull_count}\n"
                f"- Snapshot bytes: {len(snapshot_bytes)}\n"
                f"- Snapshot SHA-256: `{snapshot_sha256}`"
            )
            return 0

        if args.dry_run:
            if not args.fixture:
                raise CompositionError("--dry-run requires an offline --fixture")
            snapshot_input = load_release_input_snapshot(
                args.fixture,
                expected_sha256=args.expected_snapshot_sha256,
                expected_tag=args.tag,
            )
            if args.prev_tag is not None and args.prev_tag != snapshot_input.previous_tag:
                raise CompositionError("--prev-tag does not match release input snapshot")
            composed = compose_release_body(
                snapshot_input.raw_body,
                snapshot_input.commits,
                snapshot_input.pulls,
                compare_commit_count=snapshot_input.commit_count,
                source_sha256=snapshot_input.sha256,
            )
            snapshot = load_persisted_snapshot(
                composed,
                snapshot_input.raw_body,
                expected_source_sha256=snapshot_input.sha256,
            )
            if snapshot is None:  # Defensive: composed bodies always carry the marker.
                raise CompositionError("dry-run composition produced no persisted snapshot metadata")
            sys.stdout.write(composed)
            _write_step_summary(
                f"### Release note composer dry run\n\n"
                f"- Range: `{snapshot_input.previous_tag}...{args.tag}`\n"
                f"- Commits: {snapshot_input.commit_count}\n"
                f"- Pull requests: {len(snapshot_input.commits)}\n"
                f"- Input snapshot SHA-256: `{snapshot_input.sha256}`\n"
                f"- Body SHA-256: `{snapshot.body_sha256}`\n"
                f"- Snapshot payload SHA-256: `{snapshot.payload_sha256}`"
            )
            return 0

        if not args.snapshot:
            raise CompositionError("live composition requires --snapshot or RELEASE_NOTES_SNAPSHOT")
        if not args.expected_snapshot_sha256:
            raise CompositionError("live composition requires EXPECTED_SNAPSHOT_SHA256")
        repository = os.environ.get("GITHUB_REPOSITORY", "")
        token = os.environ.get("GITHUB_TOKEN", "")
        api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")
        snapshot_input = load_release_input_snapshot(
            args.snapshot,
            expected_sha256=args.expected_snapshot_sha256,
            expected_repository=repository,
            expected_tag=args.tag,
        )
        raw_body = snapshot_input.raw_body
        client = GitHubClient(repository, token, api_url=api_url)
        previous_tag = snapshot_input.previous_tag
        if args.prev_tag is not None and args.prev_tag != previous_tag:
            raise CompositionError("--prev-tag does not match release input snapshot")
        release_id, persisted_body = _resolve_release(client, args.tag)
        canonical_body = compose_release_body(
            raw_body,
            snapshot_input.commits,
            snapshot_input.pulls,
            compare_commit_count=snapshot_input.commit_count,
            source_sha256=snapshot_input.sha256,
        )
        snapshot = load_persisted_snapshot(
            persisted_body,
            raw_body,
            expected_source_sha256=snapshot_input.sha256,
        )
        snapshot_reused = snapshot is not None
        if snapshot is None:
            if persisted_body != raw_body:
                raise CompositionError(
                    "live release body does not match the immutable release-action body snapshot"
                )
            composed = canonical_body
            snapshot = load_persisted_snapshot(
                composed,
                raw_body,
                expected_source_sha256=snapshot_input.sha256,
            )
            if snapshot is None:  # Defensive: composed bodies always carry the marker.
                raise CompositionError("composition produced no persisted snapshot metadata")
        else:
            if persisted_body.encode("utf-8") != canonical_body.encode("utf-8"):
                raise CompositionError(
                    "persisted release-note body does not match canonical composition "
                    "from the immutable input snapshot"
                )
            composed = persisted_body

        client.request_json("PATCH", f"/repos/{client.repository}/releases/{release_id}", {"body": composed})
        result = {
            "outcome": "release_note_composed",
            "tag": args.tag,
            "previous_tag": previous_tag,
            "commit_count": snapshot_input.commit_count,
            "pull_request_count": len(snapshot_input.commits),
            "release_id": release_id,
            "body_sha256": snapshot.body_sha256,
            "body_byte_count": len(composed.encode("utf-8")),
            "snapshot_byte_count": snapshot_input.byte_count,
            "snapshot_payload_sha256": snapshot.payload_sha256,
            "snapshot_source_sha256": snapshot.source_sha256,
            "snapshot_reused": snapshot_reused,
        }
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        _write_step_summary(
            f"### Release notes composed\n\n- Range: `{previous_tag}...{args.tag}`\n"
            f"- Commits: {snapshot_input.commit_count}\n"
            f"- Pull requests: {len(snapshot_input.commits)}\n- Release id: `{release_id}`\n"
            f"- Input snapshot SHA-256: `{snapshot_input.sha256}`\n"
            f"- Snapshot reused: `{str(snapshot_reused).lower()}`\n"
            f"- Body bytes: {len(composed.encode('utf-8'))}\n"
            f"- Body SHA-256: `{snapshot.body_sha256}`\n"
            f"- Snapshot payload SHA-256: `{snapshot.payload_sha256}`"
        )
        return 0
    except CompositionError as error:
        diagnostic = {"outcome": FAILURE_OUTCOME, "error": str(error)}
        print(json.dumps(diagnostic, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        _write_step_summary(f"### Release note composition failed\n\n`{FAILURE_OUTCOME}`: {error}")
        return 1


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
