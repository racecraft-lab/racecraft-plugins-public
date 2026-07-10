#!/usr/bin/env python3
"""Layer-4 privacy regression guard for the current repository tree."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import unittest
from collections.abc import Callable, Iterable
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "tests" / "speckit-pro"
SHARED_LIB = TESTS_ROOT / "lib"
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))

from test_result import run_counted  # noqa: E402


BASELINE = TESTS_ROOT / "parity" / "xplat-010" / "test-privacy-scan-baseline.txt"
SCHEMA_PATH = REPO_ROOT / "docs-site" / "src" / "lib" / "schema.ts"
TOOLING_SOURCE_PATHS = (
    Path("tests/speckit-pro/layer4-scripts/test-privacy-scan.py"),
    Path("tests/speckit-pro/layer7-integration/scrub-transcript.py"),
)
DOC014_PUBLIC_IDENTITY_PATHS = {
    Path("docs-site/src/lib/schema.ts"),
    Path("docs-site/tests/seo-schema-org.spec.mjs"),
    Path("docs/ai/specs/.process/DOC-014-workflow.md"),
}

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9_.%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", re.IGNORECASE)
HOME_PATH_PATTERN = re.compile(
    r"(?:/(?:Users|home)/|[A-Za-z]:[\\/]+Users[\\/]+)[A-Za-z0-9_.\-]+",
    re.IGNORECASE,
)
HYPHENATED_HOME_PATH_PATTERN = re.compile(r"-Users-[A-Za-z0-9_.\-]+", re.IGNORECASE)
PRIVATE_VAR_PATTERN = re.compile(r"/private/var/folders/[A-Za-z0-9_/\.\-]+", re.IGNORECASE)
TMP_TRANSCRIPT_PATTERN = re.compile(r"/private/tmp/claude-[0-9]+", re.IGNORECASE)
UUID_PATTERN = re.compile(
    r"[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}",
    re.IGNORECASE,
)
ALLOWED_EMAILS = {"support@openai.com", "git@github.com"}

CURRENT_INVENTORY = [
    "all-alpha identities still emit sliding-window fragments",
    "non-allowlisted email addresses absent",
    "absolute local home paths absent",
    "hyphenated local home path dumps absent",
    "specific temp transcript path absent",
    "specific macOS temp folder path absent",
    "raw UUIDs absent",
    "dynamic local identity and workspace terms absent",
    "privacy tooling does not encode local identity fragments",
    "Layer 7 replay fixtures do not commit captured raw transcript files",
]

GENERIC_LOCAL_TERMS = {
    "actions",
    "admin",
    "build",
    "cache",
    "claude",
    "codex",
    "documents",
    "downloads",
    "github",
    "home",
    "integration",
    "layer4",
    "layer7",
    "local",
    "main",
    "openai",
    "plugins",
    "private",
    "project",
    "projects",
    "public",
    "racecraft",
    "repo",
    "root",
    "runner",
    "speckit",
    "staff",
    "support",
    "tests",
    "users",
    "work",
    "worktrees",
}


def baseline_inventory(path: Path) -> list[str]:
    names: list[str] = []
    total: int | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("TOTAL: "):
            total = int(line.removeprefix("TOTAL: "))
            continue
        _ordinal, name = line.split(" ", 1)
        names.append(name)
    if total != len(names):
        raise AssertionError(f"baseline TOTAL {total} does not match {len(names)} names")
    return names


def git_output(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        check=False,
        shell=False,
    )


def current_tree_files() -> list[Path]:
    result = git_output("ls-files", "--cached", "--others", "--exclude-standard", "-z")
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git ls-files failed: {message}")

    paths: list[Path] = []
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        relative = Path(raw_path.decode("utf-8", errors="surrogateescape"))
        absolute = REPO_ROOT / relative
        if absolute.is_file() and not absolute.is_symlink():
            paths.append(relative)
    return paths


def read_lines(relative_path: Path) -> Iterable[tuple[int, str]]:
    path = REPO_ROOT / relative_path
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ()
    return enumerate(text.splitlines(), start=1)


def scan_for(pattern: re.Pattern[str], paths: Iterable[Path]) -> list[str]:
    hits: list[str] = []
    for relative_path in paths:
        for line_number, line in read_lines(relative_path):
            if pattern.search(line):
                hits.append(f"./{relative_path.as_posix()}:{line_number}:{line}")
    return hits


def scan_for_non_allowlisted_email(paths: Iterable[Path]) -> list[str]:
    hits: list[str] = []
    for relative_path in paths:
        for line_number, line in read_lines(relative_path):
            emails = EMAIL_PATTERN.findall(line)
            if any(email.lower() not in ALLOWED_EMAILS for email in emails):
                hits.append(f"./{relative_path.as_posix()}:{line_number}:{line}")
    return hits


def is_sensitive_local_term(term: str) -> bool:
    normalized = term.lower()
    if len(normalized) < 5 or normalized in GENERIC_LOCAL_TERMS:
        return False
    if normalized.startswith(("racecraft-", "speckit-", "test-")):
        return False
    if normalized.startswith("layer") and "-" in normalized[5:]:
        return False
    return True


def emit_sensitive_terms_from_value(value: str) -> list[str]:
    terms: list[str] = []
    parts = re.findall(r"[A-Za-z0-9_.-]+", value)
    # The predecessor's ``while read`` receives ``tr`` output without a final
    # newline, so a final token is intentionally not consumed.
    if value and re.fullmatch(r"[A-Za-z0-9_.-]", value[-1]):
        parts = parts[:-1]
    for part in parts:
        lowered = part.lower().removeprefix(".")
        if is_sensitive_local_term(lowered):
            terms.append(lowered)

        compact = re.sub(r"[^a-z0-9]", "", lowered)
        if is_sensitive_local_term(compact):
            terms.append(compact)

        if any(marker in compact for marker in ("document", "project", "racecraft", "speckit", "plugin")):
            continue

        window = 12 if compact.isalpha() else 8
        if len(compact) >= window:
            terms.extend(compact[index : index + window] for index in range(len(compact) - window + 1))
    return terms


def git_config(key: str) -> str:
    result = git_output("config", "--get", key)
    if result.returncode != 0:
        return ""
    return result.stdout.decode("utf-8", errors="replace").strip()


def dynamic_local_pattern() -> re.Pattern[str] | None:
    git_email = git_config("user.email")
    email_local = git_email.rsplit("@", maxsplit=1)[0]
    values = (
        os.environ.get("HOME", ""),
        os.environ.get("USER", ""),
        os.environ.get("LOGNAME", ""),
        os.environ.get("USERPROFILE", ""),
        os.environ.get("USERNAME", ""),
        git_config("user.name"),
        email_local,
        str(REPO_ROOT),
    )
    terms = sorted(
        {
            term
            for value in values
            for term in emit_sensitive_terms_from_value(value)
            if is_sensitive_local_term(term)
        }
    )
    if not terms:
        return None
    return re.compile("|".join(re.escape(term) for term in terms), re.IGNORECASE)


def doc014_public_identity_literals() -> tuple[str, ...]:
    try:
        source = SCHEMA_PATH.read_text(encoding="utf-8")
    except OSError:
        return ()
    start = source.find("buildPersonSchema")
    if start < 0:
        return ()
    block = source[start:]
    end = block.find("};")
    if end >= 0:
        block = block[: end + 2]

    literals = set(re.findall(r"\bname:\s*'([^']+)'", block))
    for url in re.findall(r"https://github\.com/[A-Za-z0-9_.-]+", block):
        literals.add(url)
        literals.add(url.removeprefix("https://"))
    return tuple(sorted(literals, key=len, reverse=True))


def dynamic_local_hits(pattern: re.Pattern[str], paths: Iterable[Path]) -> list[str]:
    allowed_literals = doc014_public_identity_literals()
    hits: list[str] = []
    for relative_path in paths:
        for line_number, line in read_lines(relative_path):
            if pattern.search(line) is None:
                continue
            sanitized = line
            if relative_path in DOC014_PUBLIC_IDENTITY_PATHS:
                for literal in allowed_literals:
                    sanitized = sanitized.replace(literal, "<DOC014_PUBLIC_IDENTITY>")
                if pattern.search(sanitized) is None:
                    continue
            hits.append(f"./{relative_path.as_posix()}:{line_number}:{line}")
    return hits


def committed_transcript_fixtures() -> list[str]:
    result = git_output("ls-files", "tests/speckit-pro/layer7-integration/**/transcript.jsonl")
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git ls-files failed: {message}")
    return result.stdout.decode("utf-8", errors="replace").splitlines()


def assert_no_hits(test: unittest.TestCase, hits: list[str], label: str) -> None:
    preview = "; ".join(hits[:3])
    test.assertFalse(hits, f"{label} leaked into current tree: {preview}")


class PrivacyScanTests(unittest.TestCase):
    def test_privacy_scan_contract(self) -> None:
        self.assertEqual(baseline_inventory(BASELINE), CURRENT_INVENTORY)
        paths = current_tree_files()
        local_pattern = dynamic_local_pattern()

        def alpha_fragments() -> None:
            fragments = emit_sensitive_terms_from_value("/qwertyuiopasdfgh/")
            self.assertIn("qwertyuiopas", fragments)

        def non_allowlisted_emails() -> None:
            assert_no_hits(self, scan_for_non_allowlisted_email(paths), CURRENT_INVENTORY[1])

        def no_pattern(pattern: re.Pattern[str], label: str) -> Callable[[], None]:
            return lambda: assert_no_hits(self, scan_for(pattern, paths), label)

        def no_dynamic_local_hits() -> None:
            if local_pattern is not None:
                assert_no_hits(self, dynamic_local_hits(local_pattern, paths), CURRENT_INVENTORY[7])

        def no_tooling_source_hits() -> None:
            if local_pattern is not None:
                hits = scan_for(local_pattern, TOOLING_SOURCE_PATHS)
                preview = "; ".join(hits[:3])
                self.assertFalse(hits, f"{CURRENT_INVENTORY[8]} leaked into privacy tooling: {preview}")

        def no_committed_transcripts() -> None:
            self.assertFalse(committed_transcript_fixtures(), "committed transcript.jsonl fixture found")

        checks: list[tuple[str, Callable[[], None]]] = [
            (CURRENT_INVENTORY[0], alpha_fragments),
            (CURRENT_INVENTORY[1], non_allowlisted_emails),
            (CURRENT_INVENTORY[2], no_pattern(HOME_PATH_PATTERN, CURRENT_INVENTORY[2])),
            (CURRENT_INVENTORY[3], no_pattern(HYPHENATED_HOME_PATH_PATTERN, CURRENT_INVENTORY[3])),
            (CURRENT_INVENTORY[4], no_pattern(TMP_TRANSCRIPT_PATTERN, CURRENT_INVENTORY[4])),
            (CURRENT_INVENTORY[5], no_pattern(PRIVATE_VAR_PATTERN, CURRENT_INVENTORY[5])),
            (CURRENT_INVENTORY[6], no_pattern(UUID_PATTERN, CURRENT_INVENTORY[6])),
            (CURRENT_INVENTORY[7], no_dynamic_local_hits),
            (CURRENT_INVENTORY[8], no_tooling_source_hits),
            (CURRENT_INVENTORY[9], no_committed_transcripts),
        ]
        for name, check in checks:
            with self.subTest(msg=name):
                check()


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PrivacyScanTests)
    return run_counted(suite, label="test-privacy-scan")


if __name__ == "__main__":
    raise SystemExit(main())
