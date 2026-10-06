#!/usr/bin/env python3
"""Live check: each curated install command works in a fresh project at the pinned Spec Kit.

This is an operator-run, networked check and is not part of any suite layer. It needs the pinned
`specify` CLI first on PATH and reaches github.com. It fails, never skips, when the CLI
is missing or is not the pinned version.

For every entry in `speckit-pro/scripts/curated-set.json` it runs the argv the install and upgrade
skills give the operator, `<kind> add <id> --from <archive_url>`, in a fresh `specify init` project:

- A preset installs without a prompt, so the check requires exit 0 and the preset directory.
- An extension URL install stops at Spec Kit's own trust prompt, which only the operator answers.
  The check closes stdin, so the default is deny. It requires a normal nonzero exit after the
  prompt (the discovery-only refusal is gone) and a verifiably empty registry, then downloads the archive and
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
from contextlib import ExitStack
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


def install_args(entry: dict[str, str]) -> list[str]:
    """The arguments after `specify` that the install and upgrade skills hand the operator."""
    return [entry["kind"], "add", entry["id"], "--from", entry["archive_url"]]


def specify(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run the `specify` found on PATH, with stdin closed so a trust prompt defaults to deny."""
    return subprocess.run(
        ["specify", *args], cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True,
        env={**os.environ, "NO_COLOR": "1"}, timeout=COMMAND_TIMEOUT_SECONDS, shell=False, check=False,
    )


def check_cli_version(cwd: Path) -> list[str]:
    result = specify(["version"], cwd)
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


def registry_entries(project: Path, kind: str) -> list[str] | None:
    """List the whole registry without following links; unknown evidence is not absence."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        with ExitStack() as descriptors:
            parent = os.open(project / ".specify", flags)
            descriptors.callback(os.close, parent)
            try:
                registry = os.open(Path(REGISTRY_DIRS[kind]).name, flags, dir_fd=parent)
            except FileNotFoundError:
                return []
            descriptors.callback(os.close, registry)
            return os.listdir(registry)
    except OSError:
        return None


def check_entry(entry: dict[str, str], project: Path) -> list[str]:
    label = f"{entry['kind']} {entry['id']}"
    if "archive_url" not in entry:
        return [f"{label}: no archive_url, and Spec Kit refuses a bare add on its default catalogs"]
    result = specify(install_args(entry), project)
    output = result.stdout + result.stderr
    failures = []
    if DISCOVERY_ONLY in output:
        failures.append(f"{label}: refused as discovery-only")
    if entry["kind"] == "preset":
        target = project / REGISTRY_DIRS[entry["kind"]] / entry["id"]
        installed = target.is_dir() and not target.is_symlink() and registry_entries(project, "preset") is not None
        if result.returncode != 0 or not installed:
            failures.append(f"{label}: exit {result.returncode}, installed={installed}")
        return failures
    if TRUST_PROMPT not in output:
        failures.append(f"{label}: did not reach the trust prompt")
    if result.returncode <= 0:
        failures.append(f"{label}: expected a normal nonzero abort, got exit {result.returncode}")
    if registry_entries(project, entry["kind"]) != []:
        failures.append(f"{label}: registry is not verifiably empty after the unanswered trust prompt")
    if not archive_declares_id(entry["archive_url"], entry["kind"], entry["id"]):
        failures.append(f"{label}: archive has no {MANIFEST_NAMES[entry['kind']]} declaring this id")
    return failures


def fresh_project(project: Path) -> list[str]:
    """Initialize a Spec Kit project at the pinned version, or say why that is not possible."""
    failures = check_cli_version(project)
    if failures:
        return failures
    if subprocess.run(["git", "init", "-q", "."], cwd=project, capture_output=True, shell=False, check=False).returncode:
        return ["setup failed: git init"]
    created = specify(["init", "--here", "--integration", "claude", "--force", "--script", "py"], project)
    return [f"setup failed: specify init exit {created.returncode}"] if created.returncode else []


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--curated-set", type=Path, default=CURATED_SET)
    args = parser.parse_args(argv)
    entries = json.loads(args.curated_set.read_text(encoding="utf-8"))["entries"]
    failed_entries = 0
    with tempfile.TemporaryDirectory(prefix="curated-install-") as raw:
        project = Path(raw)
        setup_failures = fresh_project(project)
        if setup_failures:
            failed_entries = len(entries)
        failures = setup_failures + [
            failure for entry in ([] if setup_failures else entries) for failure in check_entry(entry, project)
        ]
    failed_entries = failed_entries or len({failure.split(":")[0] for failure in failures})
    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    print(f"run-curated-install-check: {len(entries) - failed_entries}/{len(entries)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
