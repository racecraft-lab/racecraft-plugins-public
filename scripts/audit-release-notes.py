#!/usr/bin/env python3
"""Verify published release notes and emit immutable audit metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, TextIO

FAILURE_OUTCOME = "release_note_composition_failed"


class AuditFailure(RuntimeError):
    def __init__(self, message: str, returncode: int = 1) -> None:
        super().__init__(message)
        self.returncode = returncode or 1


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def append_summary(environment: Mapping[str, str], lines: Sequence[str]) -> None:
    summary_path = environment.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with Path(summary_path).open("a", encoding="utf-8") as summary:
        summary.write("\n".join(lines).rstrip() + "\n")


def audit_release_notes(
    repo_root: Path,
    environment: Mapping[str, str],
    *,
    run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    urlopen: Callable[..., Any] = urllib.request.urlopen,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    stdout = sys.stdout if stdout is None else stdout
    stderr = sys.stderr if stderr is None else stderr
    snapshot_path = repo_root / "release-note-input" / "release-note-snapshot.json"
    audit_path = repo_root / "release-note-audit.json"
    composer_path = repo_root / "scripts" / "compose-release-notes.py"
    capture_result = environment["CAPTURE_RESULT"]
    download_outcome = environment["SNAPSHOT_DOWNLOAD_OUTCOME"]
    audit: dict[str, Any] = {
        "capture_result": capture_result,
        "composer_run_attempt": int(environment["WORKFLOW_RUN_ATTEMPT"]),
        "outcome": FAILURE_OUTCOME,
        "schema_version": 1,
        "snapshot_download_outcome": download_outcome,
        "workflow_run_id": int(environment["WORKFLOW_RUN_ID"]),
    }

    def write_audit() -> str:
        encoded = (json.dumps(audit, sort_keys=True, separators=(",", ":")) + "\n").encode()
        audit_path.write_bytes(encoded)
        digest = sha256(encoded)
        with Path(environment["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
            output.write(f"audit_sha256={digest}\n")
            if "release_body_sha256" in audit:
                output.write(f"release_body_sha256={audit['release_body_sha256']}\n")
        return digest

    def fail(message: str, returncode: int = 1) -> None:
        audit["error"] = message
        audit_digest = write_audit()
        append_summary(
            environment,
            [
                "### Release note composition failed",
                "",
                f"- Audit SHA-256: `{audit_digest}`",
                f"- Reason: `{message}`",
            ],
        )
        print(
            json.dumps(
                {"error": message, "outcome": FAILURE_OUTCOME},
                sort_keys=True,
                separators=(",", ":"),
            ),
            file=stderr,
        )
        raise AuditFailure(message, returncode)

    try:
        if capture_result != "success":
            fail(f"release input capture did not succeed: {capture_result or 'missing'}")
        if download_outcome != "success":
            fail(f"release snapshot download did not succeed: {download_outcome or 'missing'}")

        snapshot_bytes = snapshot_path.read_bytes()
        snapshot_sha256 = sha256(snapshot_bytes)
        expected_sha256 = environment["EXPECTED_SNAPSHOT_SHA256"]
        if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
            fail("release snapshot has no valid expected SHA-256")
        if snapshot_sha256 != expected_sha256:
            fail("release snapshot SHA-256 mismatch")

        artifact_id = environment["SNAPSHOT_ARTIFACT_ID"]
        artifact_digest = environment["SNAPSHOT_ARTIFACT_DIGEST"]
        if not artifact_id.isdigit() or not re.fullmatch(r"[0-9a-f]{64}", artifact_digest):
            fail("release snapshot artifact metadata is invalid")

        snapshot = json.loads(snapshot_bytes)
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
        if not isinstance(snapshot, dict) or set(snapshot) != expected_keys:
            fail("release snapshot schema is invalid")
        if (
            snapshot["schema_version"] != 1
            or snapshot["repository"] != environment["GITHUB_REPOSITORY"]
            or not isinstance(snapshot["release_body"], str)
            or not isinstance(snapshot["tag"], str)
            or not snapshot["tag"].strip()
            or not isinstance(snapshot["compare"], dict)
            or not isinstance(snapshot["pulls"], dict)
        ):
            fail("release snapshot provenance is invalid")

        audit["composer_sha256"] = sha256(composer_path.read_bytes())
        audit["raw_release_body_sha256"] = sha256(snapshot["release_body"].encode())
        audit["snapshot"] = {
            "artifact_digest": artifact_digest,
            "artifact_id": int(artifact_id),
            "artifact_url": environment["SNAPSHOT_ARTIFACT_URL"],
            "byte_count": len(snapshot_bytes),
            "content_sha256": snapshot_sha256,
        }
        audit["tag"] = snapshot["tag"]

        composer_environment = os.environ.copy()
        composer_environment.update(environment)
        composer_environment["RELEASE_TAG"] = snapshot["tag"]
        completed = run(
            [sys.executable, str(composer_path), "--snapshot", str(snapshot_path)],
            env=composer_environment,
            text=True,
            capture_output=True,
            check=False,
            shell=False,
        )
        stdout.write(completed.stdout)
        audit["composer_returncode"] = completed.returncode
        if completed.returncode != 0:
            audit["composer_diagnostic_sha256"] = sha256(completed.stderr.encode())
            message = "release-note composer failed"
            try:
                diagnostic = json.loads(completed.stderr)
                if (
                    isinstance(diagnostic, dict)
                    and diagnostic.get("outcome") == FAILURE_OUTCOME
                    and isinstance(diagnostic.get("error"), str)
                ):
                    message = f"{message}: {diagnostic['error']}"
            except json.JSONDecodeError:
                # Composer stderr is not guaranteed to be JSON; keep the generic failure message.
                pass
            fail(message, completed.returncode)
        stderr.write(completed.stderr)

        composer_result = json.loads(completed.stdout)
        expected_result_keys = {
            "body_byte_count",
            "body_sha256",
            "commit_count",
            "outcome",
            "previous_tag",
            "pull_request_count",
            "release_id",
            "snapshot_byte_count",
            "snapshot_payload_sha256",
            "snapshot_reused",
            "snapshot_source_sha256",
            "tag",
        }
        if (
            not isinstance(composer_result, dict)
            or set(composer_result) != expected_result_keys
            or composer_result.get("outcome") != "release_note_composed"
            or composer_result.get("tag") != snapshot["tag"]
        ):
            fail("release-note composer returned an invalid result envelope")
        release_id = composer_result.get("release_id")
        if isinstance(release_id, bool) or not isinstance(release_id, int) or release_id <= 0:
            fail("release-note composer returned an invalid release id")
        composer_digests = (
            composer_result.get("body_sha256"),
            composer_result.get("snapshot_payload_sha256"),
            composer_result.get("snapshot_source_sha256"),
        )
        if not all(
            isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest)
            for digest in composer_digests
        ):
            fail("release-note composer returned invalid digest metadata")
        if not isinstance(composer_result.get("snapshot_reused"), bool):
            fail("release-note composer returned an invalid snapshot reuse verdict")
        commit_count = composer_result.get("commit_count")
        pull_request_count = composer_result.get("pull_request_count")
        body_byte_count = composer_result.get("body_byte_count")
        snapshot_byte_count = composer_result.get("snapshot_byte_count")
        if (
            isinstance(commit_count, bool)
            or not isinstance(commit_count, int)
            or not 0 <= commit_count <= 250
            or isinstance(pull_request_count, bool)
            or not isinstance(pull_request_count, int)
            or not 0 <= pull_request_count <= commit_count
            or isinstance(body_byte_count, bool)
            or not isinstance(body_byte_count, int)
            or body_byte_count <= 0
            or snapshot_byte_count != len(snapshot_bytes)
        ):
            fail("release-note composer returned invalid count metadata")

        repository = urllib.parse.quote(environment["GITHUB_REPOSITORY"], safe="/")
        release_url = (
            f"{environment['GITHUB_API_URL'].rstrip('/')}/repos/{repository}/releases/{release_id}"
        )
        request = urllib.request.Request(
            release_url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {environment['GITHUB_TOKEN']}",
                "User-Agent": "racecraft-release-note-audit",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            method="GET",
        )
        with urlopen(request, timeout=30.0) as response:
            release = json.loads(response.read().decode("utf-8"))
        published_body = release.get("body") if isinstance(release, dict) else None
        expected_suffix = f"## Commit appendix\n\n{snapshot['release_body']}"
        if (
            release.get("id") != release_id
            or release.get("tag_name") != snapshot["tag"]
            or not isinstance(published_body, str)
            or not published_body.startswith("## Highlights\n\n")
        ):
            fail("published release body does not match the composed release contract")
        marker = "\n\n<!-- release-note-composer-snapshot:v1 "
        if published_body.count(marker) != 1:
            fail("published release body has no unique immutable snapshot marker")
        payload, _marker_metadata = published_body.rsplit(marker, 1)
        published_body_sha256 = sha256(published_body.encode())
        if (
            not payload.endswith(expected_suffix)
            or composer_result["body_sha256"] != published_body_sha256
            or composer_result["body_byte_count"] != len(published_body.encode())
            or composer_result["snapshot_payload_sha256"] != sha256(payload.encode())
            or composer_result["snapshot_source_sha256"] != snapshot_sha256
        ):
            fail("published release body does not match composer digest metadata")

        audit.update(
            {
                "outcome": "release_note_composed_and_verified",
                "body_byte_count": composer_result["body_byte_count"],
                "commit_count": composer_result["commit_count"],
                "previous_tag": composer_result["previous_tag"],
                "pull_request_count": composer_result["pull_request_count"],
                "release_body_sha256": published_body_sha256,
                "release_id": release_id,
                "snapshot_payload_sha256": composer_result["snapshot_payload_sha256"],
                "snapshot_reused": composer_result["snapshot_reused"],
                "snapshot_source_sha256": composer_result["snapshot_source_sha256"],
                "snapshot_byte_count": composer_result["snapshot_byte_count"],
            }
        )
        audit_digest = write_audit()
        append_summary(
            environment,
            [
                "### Release note audit",
                "",
                f"- Snapshot SHA-256: `{snapshot_sha256}`",
                f"- Published body SHA-256: `{audit['release_body_sha256']}`",
                f"- Audit SHA-256: `{audit_digest}`",
                f"- Snapshot artifact: {environment['SNAPSHOT_ARTIFACT_URL']}",
            ],
        )
    except AuditFailure as error:
        return error.returncode
    except Exception as error:
        try:
            fail(f"release note audit raised {type(error).__name__}: {error}")
        except AuditFailure as failure:
            return failure.returncode
    return 0


def record_audit_artifact(
    environment: Mapping[str, str],
    *,
    stdout: TextIO | None = None,
) -> int:
    stdout = sys.stdout if stdout is None else stdout
    record = {
        "artifact_digest": environment["AUDIT_ARTIFACT_DIGEST"],
        "artifact_id": int(environment["AUDIT_ARTIFACT_ID"]),
        "artifact_url": environment["AUDIT_ARTIFACT_URL"],
        "outcome": "release_note_audit_published",
    }
    print(json.dumps(record, sort_keys=True, separators=(",", ":")), file=stdout)
    append_summary(
        environment,
        [
            "### Immutable audit artifact",
            "",
            f"- Artifact id: `{record['artifact_id']}`",
            f"- Artifact SHA-256: `{record['artifact_digest']}`",
            f"- Artifact: {record['artifact_url']}",
        ],
    )
    return 0


def main(
    argv: Sequence[str] | None = None,
    environment: Mapping[str, str] | None = None,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--record-artifact",
        action="store_true",
        help="record the uploaded audit artifact in the step summary",
    )
    args = parser.parse_args(argv)
    environment = os.environ if environment is None else environment
    try:
        if args.record_artifact:
            return record_audit_artifact(environment)
        return audit_release_notes(Path.cwd(), environment)
    except (KeyError, OSError, TypeError, ValueError) as exc:
        print(f"audit-release-notes: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
