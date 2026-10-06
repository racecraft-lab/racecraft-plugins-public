#!/usr/bin/env python3
"""Live probe: each curated install command runs in a fresh project at the pinned Spec Kit.

This is an operator-run, networked check and is not part of any suite layer. It needs the pinned
`specify` CLI first on PATH and reaches github.com. It fails, never skips, when the CLI
is missing or is not the pinned version.

For every entry in `speckit-pro/scripts/curated-set.json` it runs the argv the install and upgrade
skills give the operator, `<kind> add <id> --from <archive_url>`, in a fresh `specify init` project:

- A preset installs without a prompt. The probe requires exit 0 and its directory, but reports
  completion unproven: those observations do not establish registration or manifest identity.
- An extension URL install stops at Spec Kit's own trust prompt, which only the operator answers.
  The check closes stdin, so the default is deny. It requires a normal nonzero exit after the
  prompt (the discovery-only refusal is gone), a verifiably empty registry, and an archive whose
  `extension.yml` declares the entry's id. That proves the refusal is gone, not that an install
  succeeds, so each extension is reported "unproven: needs operator confirmation" and the run exits 2.
- The legacy `--trust-pinned-archives` option fails closed: this check cannot certify a completed
  extension install and never bypasses the trust prompt. Live acceptance belongs to the operator.

Exit codes: 1 a failure, 2 no failure but every entry is unproven. No entry can pass, so the check
never exits 0: completed installs need owner-run acceptance.

`--owner-acceptance` is that owner-run acceptance. The owner runs it in their own terminal:
`python3 tests/speckit-pro/run-curated-install-check.py --owner-acceptance`. It refuses to start
without an interactive terminal. Each `<kind> add <id> --from <archive_url>` inherits the terminal,
so the owner reads and answers Spec Kit's own trust prompt; nothing here pipes, scripts or bypasses
it. After each command it reads Spec Kit v1.1.0's on-disk evidence and reports the entry
`installed`, `failed` or `not-run`:

- manifest identity: `.specify/<kind>s/<id>/<manifest>` is a regular file byte-identical to the
  manifest in the pinned archive, declares the id, and hashes to the registry's `manifest_hash`;
- registration: `.specify/<kind>s/.registry` lists the id with that hash, a version the manifest
  declares, and `source: local` (what a `--from` install records);
- active configuration: the registry entry is `enabled: true`, and an extension is listed under
  `installed:` in `.specify/extensions.yml`.

It exits 0 only when every curated entry is `installed`, and 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from contextlib import ExitStack
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "speckit-pro"))
from isolated_child import minimal_env  # noqa: E402
from speckit_pro_runner import spec_kit_pin  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
CURATED_SET = REPO_ROOT / "speckit-pro" / "scripts" / "curated-set.json"
COMMAND_TIMEOUT_SECONDS = 180
DISCOVERY_ONLY = "discovery-only"
TRUST_PROMPT = "Continue with installation?"
MANIFEST_NAMES = {"extension": "extension.yml", "preset": "preset.yml"}
REGISTRY_DIRS = {"extension": ".specify/extensions", "preset": ".specify/presets"}
REGISTRY_KEYS = {"extension": "extensions", "preset": "presets"}
EXTENSION_CONFIG = ".specify/extensions.yml"
# The operator's terminal settings, so Spec Kit can draw its prompt; none of them answers it.
TERMINAL_KEYS = ("TERM", "COLUMNS", "LINES")
# Only what pinned Spec Kit v1.1.0 reads to reach github.com: GITHUB_TOKEN/GH_TOKEN
# (authentication/github_http.py), and, through its urllib.request.build_opener openers
# (authentication/http.py), urllib's <scheme>_proxy/no_proxy variables and OpenSSL's default CA paths.
NETWORK_KEYS = ("GH_TOKEN", "GITHUB_TOKEN", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy", "https_proxy",
                "no_proxy", "SSL_CERT_FILE", "SSL_CERT_DIR")


def install_args(entry: dict[str, str]) -> list[str]:
    """The arguments after `specify` that the install and upgrade skills hand the operator."""
    return [entry["kind"], "add", entry["id"], "--from", entry["archive_url"]]


def specify(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run the `specify` found on PATH, with stdin closed so a trust prompt defaults to deny."""
    return subprocess.run(
        ["specify", *args], cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True,
        env=minimal_env({"NO_COLOR": "1"}, keys=NETWORK_KEYS), timeout=COMMAND_TIMEOUT_SECONDS,
        shell=False, check=False,
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


def archive_manifest(url: str, kind: str) -> bytes | None:
    """The manifest at the top of the pinned archive, the bytes Spec Kit copies on install."""
    with urllib.request.urlopen(url, timeout=COMMAND_TIMEOUT_SECONDS) as response:  # noqa: S310 (https URL from the curated set)
        archive = zipfile.ZipFile(io.BytesIO(response.read()))
    for name in archive.namelist():
        parts = name.split("/")
        if len(parts) == 2 and parts[1] == MANIFEST_NAMES[kind]:
            return archive.read(name)
    return None


def declares_id(manifest: bytes, entry_id: str) -> bool:
    pattern = re.compile(rf"^\s*id:\s*[\"']?{re.escape(entry_id)}[\"']?\s*$", re.MULTILINE)
    return bool(pattern.search(manifest.decode("utf-8", errors="replace")))


def archive_declares_id(url: str, kind: str, entry_id: str) -> bool:
    manifest = archive_manifest(url, kind)
    return manifest is not None and declares_id(manifest, entry_id)


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
        directory_observed = registry_entries(project, "preset", entry["id"]) is not None
        if result.returncode != 0 or not directory_observed:
            failures.append(f"{label}: exit {result.returncode}, directory_observed={directory_observed}")
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


def init_project(project: Path) -> list[str]:
    """Initialize a Spec Kit project in `project`, or say why that failed."""
    if subprocess.run(["git", "init", "-q", "."], cwd=project, env=minimal_env(), capture_output=True,
                      shell=False, check=False).returncode:
        return ["setup failed: git init"]
    created = specify(["init", "--here", "--integration", "claude", "--force", "--script", "py"], project)
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
    """Fail with its failures, or unproven: this check never certifies a completed install."""
    failures = check_entry(entry, project)
    if not failures and entry["kind"] == "extension" and trust_archives:
        failures = check_completed_install(entry)
    if failures:
        return "fail", failures
    return "unproven", []


def regular_file(path: Path) -> bytes | None:
    """The bytes of `path` when it is a regular file reached through no link; otherwise None."""
    if os.path.realpath(path) != str(path):
        return None
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError:
        return None
    with os.fdopen(descriptor, "rb") as handle:
        return handle.read() if stat.S_ISREG(os.fstat(handle.fileno()).st_mode) else None


def installed_ids(config: bytes) -> list[str]:
    """The block `installed:` list Spec Kit's yaml.dump writes to .specify/extensions.yml."""
    lines = config.decode("utf-8", errors="replace").splitlines()
    if "installed:" not in lines:
        return []
    items = []
    for line in lines[lines.index("installed:") + 1:]:
        match = re.fullmatch(r"(?:  )?- ['\"]?([^'\"\s]+)['\"]?", line)
        if not match:
            break
        items.append(match.group(1))
    return items


def registry_record(project: Path, kind: str, entry_id: str) -> dict | None:
    raw = regular_file(project / REGISTRY_DIRS[kind] / ".registry")
    try:
        registry = json.loads(raw) if raw is not None else None
    except ValueError:
        return None
    records = registry.get(REGISTRY_KEYS[kind]) if isinstance(registry, dict) else None
    record = records.get(entry_id) if isinstance(records, dict) else None
    return record if isinstance(record, dict) else None


def completion_evidence(project: Path, entry: dict[str, str], pinned: bytes) -> tuple[str, list[str]]:
    """`installed` with its evidence, or `failed` with every missing piece of it."""
    kind, entry_id = entry["kind"], entry["id"]
    label = f"{kind} {entry_id}"
    record = registry_record(project, kind, entry_id)
    if record is None:
        return "failed", [f"{label}: not registered in {REGISTRY_DIRS[kind]}/.registry"]
    manifest = regular_file(project / REGISTRY_DIRS[kind] / entry_id / MANIFEST_NAMES[kind])
    if manifest is None:
        return "failed", [f"{label}: no regular installed {MANIFEST_NAMES[kind]}"]
    digest = "sha256:" + hashlib.sha256(manifest).hexdigest()
    version = record.get("version")
    checks = [
        (manifest == pinned, "installed manifest differs from the pinned archive's"),
        (declares_id(manifest, entry_id), "installed manifest does not declare this id"),
        (record.get("manifest_hash") == digest, "registry manifest_hash does not match the installed manifest"),
        (isinstance(version, str) and re.search(rf"^\s+version:\s*[\"']?{re.escape(str(version))}[\"']?\s*$",
                                                 manifest.decode("utf-8", errors="replace"), re.MULTILINE) is not None,
         "registry version is not the manifest's"),
        (record.get("source") == "local", "registry source is not the local archive a --from install records"),
        (record.get("enabled") is True, "registry entry is not enabled"),
    ]
    if kind == "extension":
        config = regular_file(project / EXTENSION_CONFIG)
        checks.append((config is not None and entry_id in installed_ids(config),
                       f"not listed under installed: in {EXTENSION_CONFIG}"))
    failures = [f"{label}: {reason}" for ok, reason in checks if not ok]
    if failures:
        return "failed", failures
    active = f", listed in {EXTENSION_CONFIG}" if kind == "extension" else ""
    return "installed", [f"{label}: version {version}, manifest {digest} matches the pinned archive and the "
                         f"registry, registered from source local, enabled{active}"]


def operator_specify(args: list[str], cwd: Path) -> int:
    """Run `specify` on the operator's terminal: stdin, stdout and stderr are inherited, so only
    the operator answers any prompt. No flag or variable that skips a prompt is added."""
    env = minimal_env(keys=(*NETWORK_KEYS, *TERMINAL_KEYS))
    return subprocess.run(["specify", *args], cwd=cwd, env=env, shell=False, check=False).returncode


def accept_entry(entry: dict[str, str], project: Path) -> tuple[str, list[str]]:
    label = f"{entry['kind']} {entry['id']}"
    if "archive_url" not in entry:
        return "not-run", [f"{label}: no archive_url"]
    try:
        pinned = archive_manifest(entry["archive_url"], entry["kind"])
    except (OSError, zipfile.BadZipFile) as error:
        return "not-run", [f"{label}: pinned archive unavailable ({type(error).__name__})"]
    if pinned is None:
        return "not-run", [f"{label}: pinned archive has no {MANIFEST_NAMES[entry['kind']]}"]
    args = install_args(entry)
    print(f"\n== {label}: specify {' '.join(args)}", flush=True)
    print("   Review the prompt and answer it yourself.", flush=True)
    try:
        operator_specify(args, project)
    except OSError as error:
        return "not-run", [f"{label}: specify did not start ({type(error).__name__})"]
    return completion_evidence(project, entry, pinned)


def interactive() -> bool:
    """Whether a person is at this terminal to read and answer Spec Kit's prompts."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def owner_acceptance(entries: list[dict[str, str]]) -> int:
    """Install every curated entry with the operator at the terminal; 0 only when all are installed."""
    if not interactive():
        results = [("not-run", ["owner acceptance needs an interactive terminal; run it yourself"])] * len(entries)
    else:
        with tempfile.TemporaryDirectory(prefix="curated-acceptance-") as raw:
            project = Path(raw).resolve()
            setup_failures = fresh_project(project)
            if setup_failures:
                results = [("not-run", setup_failures)] * len(entries)
            else:
                results = [accept_entry(entry, project) for entry in entries]
    for entry, (status, details) in zip(entries, results, strict=True):
        print(f"{status.upper()} {entry['kind']} {entry['id']}: " + "; ".join(details))
    installed = [status for status, _details in results].count("installed")
    print(f"run-curated-install-check --owner-acceptance: {installed}/{len(entries)} installed")
    return 0 if installed == len(entries) else 1


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--curated-set", type=Path, default=CURATED_SET)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--trust-pinned-archives", action="store_true",
        help="legacy option: fails closed; completed installs need owner-run acceptance",
    )
    mode.add_argument(
        "--owner-acceptance", action="store_true",
        help="owner-run: install each entry on your terminal, answer Spec Kit's prompts yourself, verify",
    )
    args = parser.parse_args(argv)
    entries = json.loads(args.curated_set.read_text(encoding="utf-8"))["entries"]
    if not entries:
        print("FAIL curated set: no entries to verify", file=sys.stderr)
        return 1
    if args.owner_acceptance:
        return owner_acceptance(entries)
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
            reason = "needs operator confirmation" if entry["kind"] == "extension" else "needs owner-run acceptance"
            print(f"UNPROVEN {entry['kind']} {entry['id']}: {reason}", file=sys.stderr)
    for failure in dict.fromkeys(failure for status, failures in results if status == "fail" for failure in failures):
        print(f"FAIL {failure}", file=sys.stderr)
    counts = {status: [result[0] for result in results].count(status) for status in ("pass", "fail", "unproven")}
    unproven_note = f", {counts['unproven']} unproven (needs owner-run acceptance)" if counts["unproven"] else ""
    print(f"run-curated-install-check: {counts['pass']}/{len(entries)} passed{unproven_note}")
    return 1 if counts["fail"] else 2 if counts["unproven"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
