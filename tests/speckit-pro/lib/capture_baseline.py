#!/usr/bin/env python3
"""Capture a bash test's VERBOSE PASS/FAIL inventory into a frozen parity baseline.

Each ``.sh``->``.py`` port in XPLAT-010 commits one count-parity baseline per
``(script, invocation-mode)`` pair. This tool produces it: it runs the bash
predecessor under ``VERBOSE=true`` in the pinned **non-root** capture
environment, keeps only the lines matching
``^\\s*(.+?)\\s\\.\\.\\.\\s(PASS|FAIL)$`` (discarding all other, possibly
interleaved, subprocess stdout), and writes the frozen format to
``tests/speckit-pro/parity/xplat-010/<script>-baseline.txt``:

    NNN <verbatim runtime name>   (one per executed _pass/_fail, in order)
    TOTAL: <N>

Names are captured **verbatim** from runtime output — never grepped from
``assert_*`` source text. Capture fails loud on any PASS/FAIL line with an empty
name rather than inventing a positional ``check-NNN`` placeholder (count-parity
contract §1/§2, research §D6). PR 2 ships this tooling; the ports (PRs 3a-9)
consume it.

CLI: ``python3 tests/speckit-pro/lib/capture_baseline.py <script.sh> [-- args...]``
"""

from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

# The single frozen parse filter (Clarifications Session 1, S1-Q4).
VERBOSE_LINE = re.compile(r"^\s*(.+?)\s\.\.\.\s(PASS|FAIL)$")

BASELINE_DIR = "tests/speckit-pro/parity/xplat-010"


class BaselineError(Exception):
    """Raised on a malformed capture (empty/stale name, missing script, root env)."""


def parse_verbose_lines(text: str) -> list[tuple[str, str]]:
    """Return ``[(name, outcome)]`` for every VERBOSE PASS/FAIL line, in order.

    Non-matching lines (progress text, summaries, interleaved detail) are
    discarded. A matched line whose name is empty/whitespace fails loud.
    """
    results: list[tuple[str, str]] = []
    for line in text.splitlines():
        match = VERBOSE_LINE.match(line)
        if match is None:
            continue
        name = match.group(1).strip()
        outcome = match.group(2)
        if not name:
            raise BaselineError(f"empty check name on PASS/FAIL line: {line!r}")
        results.append((name, outcome))
    return results


def render_baseline(results: list[tuple[str, str]]) -> str:
    """Render the frozen ``NNN <name>`` + ``TOTAL: <N>`` baseline text."""
    lines = [f"{index:03d} {name}" for index, (name, _outcome) in enumerate(results, start=1)]
    lines.append(f"TOTAL: {len(results)}")
    return "\n".join(lines) + "\n"


def capture_environment() -> dict[str, object]:
    """Record the pinned capture environment (must be non-root, matching CI).

    A root-vs-non-root capture can diverge (e.g. 31 vs 36 assertions for
    ``test-moc-lint-exit-codes.sh``), so the environment is recorded and the
    capture refuses to run as root.
    """
    is_root = hasattr(os, "geteuid") and os.geteuid() == 0
    return {
        "is_root": bool(is_root),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }


def capture(
    script: Path,
    out_path: Path,
    *,
    extra_args: tuple[str, ...] = (),
    env_overrides: dict[str, str] | None = None,
) -> dict[str, object]:
    """Run ``script`` under ``VERBOSE=true``, write the baseline, return metadata.

    Fails loud when: the capture environment is root; ``bash`` is unavailable;
    the script is missing; or any PASS/FAIL line has an empty name.
    """
    environment = capture_environment()
    if environment["is_root"]:
        raise BaselineError(
            "refusing to capture a parity baseline as root — capture in the pinned "
            "non-root, CI-matching environment (root-vs-non-root assertion drift)"
        )
    if not script.is_file():
        raise BaselineError(f"script not found: {script}")
    bash_executable = shutil.which("bash")
    if bash_executable is None:
        raise BaselineError("bash not found — baseline capture requires bash for the .sh predecessor")

    env = os.environ.copy()
    env["VERBOSE"] = "true"
    if env_overrides:
        env.update(env_overrides)

    completed = subprocess.run(
        [bash_executable, str(script), *extra_args],
        text=True,
        capture_output=True,
        env=env,
        shell=False,
        check=False,
    )
    results = parse_verbose_lines(completed.stdout + "\n" + completed.stderr)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_baseline(results), encoding="utf-8")
    return {
        "baseline_path": out_path.as_posix(),
        "total": len(results),
        "exit_code": completed.returncode,
        "environment": environment,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Capture a VERBOSE count-parity baseline for a .sh test.")
    parser.add_argument("script", help="Path to the .sh predecessor to capture.")
    parser.add_argument("--out", help="Output baseline path (default: parity/xplat-010/<script>-baseline.txt).")
    parser.add_argument("script_args", nargs="*", help="Extra args passed to the script (invocation mode).")
    args = parser.parse_args(argv)

    script = Path(args.script)
    repo_root = Path(__file__).resolve().parents[3]
    if args.out:
        out_path = Path(args.out)
    else:
        out_path = repo_root / BASELINE_DIR / f"{script.stem}-baseline.txt"

    try:
        summary = capture(script, out_path, extra_args=tuple(args.script_args))
    except BaselineError as exc:
        print(f"capture-baseline: {exc}", file=sys.stderr)
        return 1
    print(f"capture-baseline: wrote {summary['baseline_path']} (TOTAL: {summary['total']})")
    print(f"capture-baseline: environment={summary['environment']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
