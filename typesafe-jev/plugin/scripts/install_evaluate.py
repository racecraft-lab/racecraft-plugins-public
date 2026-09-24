#!/usr/bin/env python3
"""Install the evaluate binary from a typesafe-jev release.

The plugin carries a launcher, not the server: the server is a compiled Go
binary, released per platform. This downloads the archive for this machine
from an explicit release tag, checks it against the release's SHA256SUMS.txt,
and installs it where the launcher looks for it.

It always names a tag. This repository releases more than one component, so
its "latest" release can belong to another one.

    python3 install_evaluate.py              # the plugin's own version
    python3 install_evaluate.py --version 0.9.0
    python3 install_evaluate.py --force      # replace an existing binary

Nothing here reads a key. The key file is a separate, manual step.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import platform
import re
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

REPOSITORY = "racecraft-lab/racecraft-plugins-public"
RELEASES = f"https://github.com/{REPOSITORY}/releases/download"
TAG_PREFIX = "typesafe-jev-v"
SUMS_NAME = "SHA256SUMS.txt"
# One compressed binary and a few lines of checksums. Both caps are generous by
# orders of magnitude; they exist so a wrong URL cannot fill the disk.
MAX_ARCHIVE_BYTES = 100 << 20
MAX_SUMS_BYTES = 1 << 20
TIMEOUT_SECONDS = 60
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?$")
PLUGIN_MANIFEST = Path(__file__).resolve().parents[1] / ".claude-plugin" / "plugin.json"

# Release builds exist for these only. Windows has none yet: the plugin's
# launcher cannot run the server there, so Jev stays off on Windows.
OS_NAMES = {"darwin": "darwin", "linux": "linux"}
ARCH_NAMES = {
    "x86_64": "amd64",
    "amd64": "amd64",
    "arm64": "arm64",
    "aarch64": "arm64",
}


class InstallError(RuntimeError):
    """A failure the operator can act on. The message says what and why."""


def plugin_version() -> str:
    try:
        data = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise InstallError(f"cannot read the plugin version from {PLUGIN_MANIFEST}: {error}") from error
    version = data.get("version") if isinstance(data, dict) else None
    if not isinstance(version, str) or not VERSION_RE.match(version):
        raise InstallError(f"{PLUGIN_MANIFEST} has no release version; pass --version")
    return version


def target() -> tuple[str, str]:
    """Return this machine's (os, arch) in Go's spelling."""
    system = OS_NAMES.get(platform.system().lower())
    arch = ARCH_NAMES.get(platform.machine().lower())
    if system is None or arch is None:
        raise InstallError(
            f"no release build for {platform.system()} {platform.machine()}; "
            "build from source instead (see the typesafe-jev README)"
        )
    return system, arch


def default_destination() -> Path:
    """Where the plugin's launcher looks: EVALUATE_BIN, else the default path.

    A leading ~ in EVALUATE_BIN is expanded, as the launcher does, so both
    resolve the same file.
    """
    explicit = os.environ.get("EVALUATE_BIN")
    if explicit:
        return Path(os.path.expanduser(explicit))
    return Path.home() / ".local" / "libexec" / "racecraft-jev" / "evaluate"


def fetch(url: str, limit: int) -> bytes:
    """Download url into memory, refusing anything over limit bytes."""
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            body = response.read(limit + 1)
    except urllib.error.HTTPError as error:
        raise InstallError(f"{url} returned HTTP {error.code}") from error
    except (urllib.error.URLError, OSError) as error:
        raise InstallError(f"cannot download {url}: {error}") from error
    if len(body) > limit:
        raise InstallError(f"{url} is over the {limit} byte limit")
    return body


def expected_checksum(sums: bytes, asset: str) -> str:
    for line in sums.decode("utf-8", "replace").splitlines():
        fields = line.split()
        if len(fields) == 2 and fields[1].lstrip("*") == asset:
            digest = fields[0].lower()
            if re.fullmatch(r"[0-9a-f]{64}", digest):
                return digest
    raise InstallError(f"{SUMS_NAME} lists no checksum for {asset}")


def extract_binary(archive: bytes, member_name: str) -> bytes:
    """Return the one regular file named member_name from a .tar.gz archive."""
    try:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
            for member in tar:
                if member.name != member_name:
                    continue
                if not member.isreg():
                    raise InstallError(f"archive member {member_name} is not a regular file")
                if member.size > MAX_ARCHIVE_BYTES:
                    raise InstallError(f"archive member {member_name} is over the size limit")
                handle = tar.extractfile(member)
                if handle is None:
                    raise InstallError(f"archive member {member_name} cannot be read")
                return handle.read()
    except (tarfile.TarError, OSError, EOFError) as error:
        raise InstallError(f"the archive cannot be read: {error}") from error
    raise InstallError(f"the archive has no {member_name}")


def install(binary: bytes, destination: Path, force: bool) -> None:
    """Write binary to destination atomically: stage beside it, then rename."""
    if destination.exists() and not force:
        raise InstallError(f"{destination} already exists; pass --force to replace it")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, staged = tempfile.mkstemp(prefix=".evaluate-install-", dir=destination.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(binary)
        os.chmod(staged, 0o755)
        os.replace(staged, destination)
    except OSError as error:
        raise InstallError(f"cannot install to {destination}: {error}") from error
    finally:
        if os.path.exists(staged):
            os.unlink(staged)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install the evaluate binary from a typesafe-jev release.")
    parser.add_argument("--version", help="release to install, such as 0.9.0 (default: this plugin's version)")
    parser.add_argument("--dest", type=Path, help="install path (default: $EVALUATE_BIN, else ~/.local/libexec/racecraft-jev/evaluate)")
    parser.add_argument("--force", action="store_true", help="replace an existing binary")
    parser.add_argument("--base-url", default=RELEASES, help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        version = (args.version or plugin_version()).removeprefix("v")
        if not VERSION_RE.match(version):
            raise InstallError(f"{version!r} is not a release version such as 0.9.0")
        system, arch = target()
        destination = args.dest or default_destination()
        if destination.exists() and not args.force:
            raise InstallError(f"{destination} already exists; pass --force to replace it")

        tag = f"{TAG_PREFIX}{version}"
        asset = f"evaluate-{system}-{arch}.tar.gz"
        base = f"{args.base_url.rstrip('/')}/{tag}"
        print(f"Installing evaluate {version} ({system}/{arch}) from {tag}")
        digest = expected_checksum(fetch(f"{base}/{SUMS_NAME}", MAX_SUMS_BYTES), asset)
        archive = fetch(f"{base}/{asset}", MAX_ARCHIVE_BYTES)
        got = hashlib.sha256(archive).hexdigest()
        if got != digest:
            raise InstallError(f"checksum mismatch for {asset}: got {got}, want {digest}")
        install(extract_binary(archive, "evaluate"), destination, args.force)
    except InstallError as error:
        print(f"install_evaluate: {error}", file=sys.stderr)
        return 1
    print(f"Installed {destination}")
    print(
        "Next: put a TypeSafe or OpenRouter key in ~/.config/racecraft-jev/typesafe.key "
        "or openrouter.key (chmod 600), then reconnect the jev MCP server."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
