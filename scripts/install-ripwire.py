#!/usr/bin/env python3
"""Install the checksum-pinned ripwire release and write its advisory PR report.

The Ripwire Advisory workflow runs this. ``install`` downloads the pinned
release for the runner's Linux architecture, verifies the SHA-256 recorded
here before opening the archive, and fails closed on any mismatch. ``report``
runs the layering, quality-delta, and doc-drift checks and writes the job
summary. The report is advisory: findings never fail it, and no required check
may depend on ripwire.

To bump the pin, download each Linux asset from the upstream release, compute
its SHA-256 locally, compare it with the release's published digest, and
update RIPWIRE_VERSION and RIPWIRE_SHA256 together.
"""

from __future__ import annotations

import argparse
import html
import os
import platform
import re
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import BinaryIO, TextIO

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pinned_archive as _pinned  # noqa: E402


RIPWIRE_VERSION = "0.6.5"
# SHA-256 of ripwire-<version>-linux-<arch>.tar.gz from the upstream release.
RIPWIRE_SHA256 = {
    "x64": "5c5794612f5f06632ada7c27a0f5c8f400748a70f707b64ec4d238c4fba2f7ea",
    "arm64": "25e5f37e2985830bbff189879797988b862e36521413a6e3654630a0e1f0b108",
}
RELEASE_BASE_URL = "https://github.com/redhat-et/ripwire/releases/download"
RIPWIRE_BINARY = "ripwire"
CHECK_TIMEOUT_SECONDS = 600
MAX_OUTPUT_CHARS = 20_000
_MACHINES = {"x86_64": "x64", "amd64": "x64", "aarch64": "arm64", "arm64": "arm64"}

# Raised when ripwire cannot be installed safely.
RipwireError = _pinned.PinnedArchiveError
DOWNLOAD_TIMEOUT_SECONDS = _pinned.DOWNLOAD_TIMEOUT_SECONDS


def linux_architecture(system: str | None = None, machine: str | None = None) -> str:
    system = platform.system() if system is None else system
    machine = platform.machine() if machine is None else machine
    arch = _MACHINES.get(machine.lower()) if system == "Linux" else None
    if arch is None:
        raise RipwireError(f"no pinned ripwire release for {system} {machine}")
    return arch


def install_ripwire(
    install_directory: Path,
    arch: str,
    *,
    sha256_by_arch: Mapping[str, str] = RIPWIRE_SHA256,
    opener: Callable[..., BinaryIO] | None = None,
) -> Path:
    if arch not in sha256_by_arch:
        raise RipwireError(f"no pinned ripwire release for Linux {arch}")
    stem = f"ripwire-{RIPWIRE_VERSION}-linux-{arch}"
    release = _pinned.PinnedArchive(
        "ripwire",
        f"{RELEASE_BASE_URL}/v{RIPWIRE_VERSION}/{stem}.tar.gz",
        sha256_by_arch[arch],
        f"{stem}/{RIPWIRE_BINARY}",
    )
    return _pinned.install_binary(release, install_directory / RIPWIRE_BINARY, opener=opener)


# (kind, title, root element, attributes shown in the summary)
CHECKS = (
    ("arch", "Layering", "arch", ("violations", "baselined", "new_violations")),
    ("quality-delta", "Quality delta", "quality-delta", ("regressions", "gating", "preexisting-worse", "new-symbol")),
    ("doc-drift", "Doc drift", "doc-drift", ("docs", "checked", "drift")),
)
# Attribute whose non-zero value is a finding, per check kind.
_FINDING_ATTRIBUTE = {"arch": "new_violations", "quality-delta": "regressions", "doc-drift": "drift"}
# Exit codes each check documents: --arch exits 2 on a new violation,
# --quality-delta exits 2 when pre-existing code got materially worse, and
# --doc-drift always exits 0.
_FINDING_EXIT_CODES = {"arch": {2}, "quality-delta": {2}, "doc-drift": set()}


def root_attributes(output: str, element: str) -> dict[str, str]:
    match = re.search(rf'<{re.escape(element)}((?:\s+[\w:-]+="[^"]*")*)\s*/?>', output)
    if match is None:
        return {}
    return dict(re.findall(r'([\w:-]+)="([^"]*)"', match.group(1)))


def check_status(kind: str, returncode: int, attributes: Mapping[str, str]) -> str:
    if returncode in _FINDING_EXIT_CODES[kind]:
        return "findings"
    finding = attributes.get(_FINDING_ATTRIBUTE[kind])
    if returncode != 0 or finding is None:
        return "error"
    return "clean" if finding == "0" else "findings"


def output_excerpt(output: str) -> str:
    if len(output) <= MAX_OUTPUT_CHARS:
        return output
    return output[:MAX_OUTPUT_CHARS] + f"\n... truncated ({len(output) - MAX_OUTPUT_CHARS} more characters)"


def _ripwire_environment(binary: Path) -> dict[str, str]:
    """Put the installed binary first on PATH so the argv names it literally."""
    environment = os.environ.copy()
    existing_path = environment.get("PATH", "")
    environment["PATH"] = str(binary.parent) + (os.pathsep + existing_path if existing_path else "")
    return environment


def merge_base(base_sha: str) -> str | None:
    if not base_sha:
        return None
    try:
        result = subprocess.run(
            ["git", "merge-base", base_sha, "HEAD"],
            capture_output=True,
            text=True,
            timeout=CHECK_TIMEOUT_SECONDS,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    sha = result.stdout.strip()
    return sha if result.returncode == 0 and sha else None


def _check_flag(kind: str, base: str | None) -> str | None:
    if kind == "arch":
        return "--arch=.ripwire_arch_rules"
    if kind == "quality-delta":
        return f"--quality-delta={base}..HEAD" if base else None
    return "--doc-drift"


def _run_check(binary: Path, kind: str, flag: str) -> tuple[str, str, str, str]:
    """Return (exit code, counts, status, output) for one ripwire check."""
    element, shown = next((c[2], c[3]) for c in CHECKS if c[0] == kind)
    try:
        result = subprocess.run(
            ["ripwire", ".", flag],
            capture_output=True,
            text=True,
            timeout=CHECK_TIMEOUT_SECONDS,
            check=False,
            shell=False,
            env=_ripwire_environment(binary),
        )
    except (OSError, subprocess.SubprocessError) as error:
        return "-", "", "error", f"unable to run ripwire: {error}"
    output = result.stdout + (f"\n[stderr]\n{result.stderr}" if result.stderr.strip() else "")
    attributes = root_attributes(result.stdout, element)
    counts = ", ".join(f"{name}={attributes[name]}" for name in shown if name in attributes)
    return str(result.returncode), counts, check_status(kind, result.returncode, attributes), output


def build_report(binary: Path, base_sha: str, *, stdout: TextIO = sys.stdout) -> tuple[int, str]:
    lines = [
        f"## Ripwire advisory report (ripwire {RIPWIRE_VERSION})",
        "",
        "Advisory only: findings never fail this job, and no required check depends on ripwire.",
        "",
    ]
    if not (binary.is_file() and os.access(binary, os.X_OK)):
        lines.append("ripwire is not installed, so no checks ran. See the install step log.")
        print("::warning title=ripwire advisory::ripwire is not installed; no checks ran", file=stdout)
        return 0, "\n".join(lines) + "\n"

    base = merge_base(base_sha)
    rows = ["| Check | Command | Exit | Counts | Status |", "| --- | --- | --- | --- | --- |"]
    details: list[str] = []
    for kind, title, _element, _shown in CHECKS:
        flag = _check_flag(kind, base)
        if flag is None:
            rows.append(f"| {title} | `--quality-delta` | - | merge-base with the PR base unavailable | error |")
            print(f"::warning title=ripwire advisory::{title}: merge-base unavailable", file=stdout)
            continue
        code, counts, status, output = _run_check(binary, kind, flag)
        rows.append(f"| {title} | `ripwire . {flag}` | {code} | {counts or '-'} | {status} |")
        if status != "clean":
            print(f"::warning title=ripwire advisory::{title}: {status} ({counts or 'exit ' + code})", file=stdout)
        details.extend(
            [
                f"<details><summary>{html.escape(title)} output</summary>",
                "",
                f"<pre>{html.escape(output_excerpt(output))}</pre>",
                "",
                "</details>",
                "",
            ]
        )
    lines.extend(rows)
    lines.append("")
    lines.extend(details)
    return 0, "\n".join(lines) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("install", help="download, verify, and install the pinned ripwire binary")
    subparsers.add_parser("report", help="run the advisory ripwire checks and write the job summary")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    runner_temp = os.environ.get("RUNNER_TEMP", "")
    if not runner_temp:
        print("::error::RUNNER_TEMP is not set", file=sys.stderr)
        return 1
    install_directory = Path(runner_temp) / "ripwire-bin"
    if args.command == "install":
        try:
            installed = install_ripwire(install_directory, linux_architecture())
        except RipwireError as error:
            print(f"::error::ripwire install failed: {error}", file=sys.stderr)
            return 1
        print(f"Installed ripwire {RIPWIRE_VERSION} at {installed}")
        return 0

    code, summary = build_report(install_directory / RIPWIRE_BINARY, os.environ.get("BASE_SHA", ""))
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write(summary)
    else:
        print(summary)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
