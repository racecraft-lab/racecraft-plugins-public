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
  prompt (the discovery-only refusal is gone), a verifiably empty registry, and an archive whose
  `extension.yml` declares the entry's id. That proves the refusal is gone, not that an install
  succeeds, so each extension is reported "unproven: needs operator confirmation" and the run exits 2.
- The legacy `--trust-pinned-archives` option fails closed: this check cannot certify a completed
  extension install and never bypasses the trust prompt. Live acceptance belongs to the operator.

Exit codes: 0 every entry passed, 1 a failure, 2 no failure but some extension is unproven.
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
    try:
        result = specify(["version"], cwd)
    except FileNotFoundError:
        installed_version, cli_found = None, False
    else:
        installed_version = spec_kit_pin.parse_cli_version(result.stdout) if result.returncode == 0 else None
        cli_found = True
    status = spec_kit_pin.version_status(installed_version, cli_found=cli_found)
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


def directory_state(info: os.stat_result) -> tuple[int, ...]:
    """Bind an inspection to both directory identity and its content-change timestamps."""
    return info.st_dev, info.st_ino, info.st_mode, info.st_mtime_ns, info.st_ctime_ns


def registry_entries(project: Path, kind: str, entry_id: str | None = None) -> list[str] | None:
    """List the whole registry without following links; unknown evidence is not absence."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        with ExitStack() as descriptors:
            parent = os.open(project / ".specify", flags)
            descriptors.callback(os.close, parent)
            bindings = [(project / ".specify", None, directory_state(os.fstat(parent)))]
            name = Path(REGISTRY_DIRS[kind]).name
            try:
                registry = os.open(name, flags, dir_fd=parent)
            except FileNotFoundError:
                registry = None
            entries = []
            if registry is not None:
                descriptors.callback(os.close, registry)
                bindings.append((Path(name), parent, directory_state(os.fstat(registry))))
                if entry_id is not None:
                    target = os.open(entry_id, flags, dir_fd=registry)
                    descriptors.callback(os.close, target)
                    bindings.append((Path(entry_id), registry, directory_state(os.fstat(target))))
                entries = os.listdir(registry)
            if not all(directory_state(os.stat(path, dir_fd=base, follow_symlinks=False)) == before
                       for path, base, before in reversed(bindings)):
                return None
            if registry is None:
                try:
                    os.stat(name, dir_fd=parent, follow_symlinks=False)
                except FileNotFoundError:
                    return [] if entry_id is None else None
                return None
            return entries
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
        installed = registry_entries(project, "preset", entry["id"]) is not None
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


def init_project(project: Path, extra: list[str] | tuple[str, ...] = ()) -> list[str]:
    """Initialize a Spec Kit project in `project`, or say why that failed."""
    if subprocess.run(["git", "init", "-q", "."], cwd=project, capture_output=True, shell=False, check=False).returncode:
        return ["setup failed: git init"]
    created = specify(["init", "--here", "--integration", "claude", "--force", "--script", "py", *extra], project)
    return [f"setup failed: specify init exit {created.returncode}"] if created.returncode else []


def fresh_project(project: Path) -> list[str]:
    """Initialize a Spec Kit project at the pinned version, or say why that is not possible."""
    return check_cli_version(project) or init_project(project)


def check_completed_install(entry: dict[str, str]) -> list[str]:
    """Fail closed until the operator supplies completed-install acceptance outside this check."""
    label = f"{entry['kind']} {entry['id']}"
    # Directory presence and init's exit status are not registration or manifest evidence.
    # Do not manufacture that evidence by pre-authorizing third-party extension execution.
    return [f"{label}: completed install is unproven; owner-run acceptance is required"]


def entry_result(entry: dict[str, str], project: Path, trust_archives: bool) -> tuple[str, list[str]]:
    """One of pass, fail or unproven, with the failures behind a fail."""
    failures = check_entry(entry, project)
    if not failures and entry["kind"] == "extension" and trust_archives:
        failures = check_completed_install(entry)
    if failures:
        return "fail", failures
    return ("unproven" if entry["kind"] == "extension" and not trust_archives else "pass"), []


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--curated-set", type=Path, default=CURATED_SET)
    parser.add_argument(
        "--trust-pinned-archives", action="store_true",
        help="legacy option: fails closed; completed installs need owner-run acceptance",
    )
    args = parser.parse_args(argv)
    entries = json.loads(args.curated_set.read_text(encoding="utf-8"))["entries"]
    if not entries:
        print("FAIL curated set: no entries to verify", file=sys.stderr)
        return 1
    results: list[tuple[str, list[str]]] = []
    with tempfile.TemporaryDirectory(prefix="curated-install-") as raw:
        project = Path(raw)
        setup_failures = fresh_project(project)
        if setup_failures:
            results = [("fail", setup_failures)] * len(entries)
        else:
            results = [entry_result(entry, project, args.trust_pinned_archives) for entry in entries]
    for entry, (status, _failures) in zip(entries, results, strict=True):
        if status == "unproven":
            print(f"UNPROVEN {entry['kind']} {entry['id']}: needs operator confirmation", file=sys.stderr)
    for failure in dict.fromkeys(failure for status, failures in results if status == "fail" for failure in failures):
        print(f"FAIL {failure}", file=sys.stderr)
    counts = {status: [result[0] for result in results].count(status) for status in ("pass", "fail", "unproven")}
    unproven_note = f", {counts['unproven']} unproven (needs operator confirmation)" if counts["unproven"] else ""
    print(f"run-curated-install-check: {counts['pass']}/{len(entries)} passed{unproven_note}")
    return 1 if counts["fail"] else 2 if counts["unproven"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
