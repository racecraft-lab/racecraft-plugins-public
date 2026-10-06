#!/usr/bin/env python3
"""Live check: each curated install command works in a fresh project at the pinned Spec Kit.

This is an operator-run, networked check and is not part of any suite layer. It needs the pinned
`specify` CLI on PATH (or `--specify`) and reaches github.com. It fails, never skips, when the CLI
is missing or is not the pinned version.

For every entry in `speckit-pro/scripts/curated-set.json` it runs the argv the install and upgrade
skills give the operator, `<kind> add <id> --from <archive_url>`, in a fresh `specify init` project:

- A preset installs without a prompt, so the check requires exit 0 and the preset directory.
- An extension URL install stops at Spec Kit's own trust prompt, which only the operator answers.
  The check closes stdin, so the default is deny. It requires that the prompt is reached (the
  discovery-only refusal is gone) and that nothing was installed, then downloads the archive and
  requires an `extension.yml` that declares the entry's id.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "speckit-pro"))
from speckit_pro_runner import spec_kit_pin  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
CURATED_SET = REPO_ROOT / "speckit-pro" / "scripts" / "curated-set.json"
COMMAND_TIMEOUT_SECONDS = 180
DISCOVERY_ONLY = "discovery-only"
TRUST_PROMPT = "Continue with installation?"
MANIFEST_NAMES = {"extension": "extension.yml", "preset": "preset.yml"}
REGISTRY_DIRS = {"extension": ".specify/extensions", "preset": ".specify/presets"}


def install_argv(specify: str, entry: dict[str, str]) -> list[str]:
    """The argv the install and upgrade skills hand the operator for one curated entry."""
    return [specify, entry["kind"], "add", entry["id"], "--from", entry["archive_url"]]


def run(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True,
        env={**os.environ, "NO_COLOR": "1"}, timeout=COMMAND_TIMEOUT_SECONDS, shell=False, check=False,
    )


def check_cli_version(specify: str, cwd: Path) -> list[str]:
    result = run([specify, "version"], cwd)
    status = spec_kit_pin.version_status(
        spec_kit_pin.parse_cli_version(result.stdout) if result.returncode == 0 else None,
        cli_found=True,
    )
    if status != "match":
        return [f"specify is {status} against the pinned {spec_kit_pin.PINNED_VERSION}"]
    return []


def archive_declares_id(url: str, kind: str, entry_id: str) -> bool:
    with urllib.request.urlopen(url, timeout=COMMAND_TIMEOUT_SECONDS) as response:  # noqa: S310 (https URL from the curated set)
        archive = zipfile.ZipFile(io.BytesIO(response.read()))
    pattern = re.compile(rf"^\s*id:\s*[\"']?{re.escape(entry_id)}[\"']?\s*$", re.MULTILINE)
    for name in archive.namelist():
        parts = name.split("/")
        if len(parts) == 2 and parts[1] == MANIFEST_NAMES[kind]:
            return bool(pattern.search(archive.read(name).decode("utf-8")))
    return False


def check_entry(specify: str, entry: dict[str, str], project: Path) -> list[str]:
    label = f"{entry['kind']} {entry['id']}"
    if "archive_url" not in entry:
        return [f"{label}: no archive_url, and Spec Kit refuses a bare add on its default catalogs"]
    result = run(install_argv(specify, entry), project)
    output = result.stdout + result.stderr
    installed = (project / REGISTRY_DIRS[entry["kind"]] / entry["id"]).exists()
    failures = []
    if DISCOVERY_ONLY in output:
        failures.append(f"{label}: refused as discovery-only")
    if entry["kind"] == "preset":
        if result.returncode != 0 or not installed:
            failures.append(f"{label}: exit {result.returncode}, installed={installed}")
        return failures
    if TRUST_PROMPT not in output:
        failures.append(f"{label}: did not reach the trust prompt")
    if installed:
        failures.append(f"{label}: installed without the operator answering the trust prompt")
    if not archive_declares_id(entry["archive_url"], entry["kind"], entry["id"]):
        failures.append(f"{label}: archive has no {MANIFEST_NAMES[entry['kind']]} declaring this id")
    return failures


def fresh_project(specify: str, project: Path) -> list[str]:
    """Initialize a Spec Kit project at the pinned version, or say why that is not possible."""
    failures = check_cli_version(specify, project)
    for setup in (["git", "init", "-q", "."],
                  [specify, "init", "--here", "--integration", "claude", "--force", "--script", "sh"]):
        if failures:
            break
        completed = run(setup, project)
        if completed.returncode != 0:
            failures.append(f"setup failed: {' '.join(setup[:2])} exit {completed.returncode}")
    return failures


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--specify", default="specify", help="path to the pinned specify CLI")
    parser.add_argument("--curated-set", type=Path, default=CURATED_SET)
    args = parser.parse_args(argv)
    entries = json.loads(args.curated_set.read_text(encoding="utf-8"))["entries"]
    failed_entries = 0
    with tempfile.TemporaryDirectory(prefix="curated-install-") as raw:
        project = Path(raw)
        setup_failures = fresh_project(args.specify, project)
        for failure in setup_failures:
            print(f"FAIL {failure}", file=sys.stderr)
        if setup_failures:
            failed_entries = len(entries)
        else:
            for entry in entries:
                failures = check_entry(args.specify, entry, project)
                failed_entries += bool(failures)
                for failure in failures:
                    print(f"FAIL {failure}", file=sys.stderr)
    print(f"run-curated-install-check: {len(entries) - failed_entries}/{len(entries)} passed")
    return 1 if failed_entries else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
