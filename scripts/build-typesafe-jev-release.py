#!/usr/bin/env python3
"""Build, upload, verify, and publish the typesafe-jev release assets.

Go is the plugin-owned toolchain for typesafe-jev/. This script is the
repository side of its release: it calls the Go and GitHub CLIs with argv
lists and no shell.

Every mode reads the release tag from --tag or RELEASE_TAG, which must be
typesafe-jev-vX.Y.Z. The binary is stamped with the bare version, because
`evaluate update` compares versions and cannot parse a tag.

Modes, in release order:

  build          Cross-compile every release target into
                 evaluate-<os>-<arch>.tar.gz (the binary plus LICENSE) and
                 write SHA256SUMS.txt beside them.
  upload         Attach the archives and SHA256SUMS.txt to the draft release.
  verify         Download the draft's own assets, check every archive against
                 SHA256SUMS.txt, and run this machine's binary: `version` must
                 print the tag's version, and `call --check` in an empty home
                 must exit 3 (no credential configured).
  publish        Publish the verified draft without marking it the
                 repository's latest release.
  smoke-install  Install the published release with the plugin's own
                 installer, as a user would, and run the installed binary.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = REPO_ROOT / "typesafe-jev"
LICENSE_FILE = MODULE_DIR / "LICENSE"
INSTALLER = MODULE_DIR / "plugin" / "scripts" / "install_evaluate.py"
TAG_RE = re.compile(r"^typesafe-jev-v(?P<version>[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?)$")
SUMS_NAME = "SHA256SUMS.txt"
DEFAULT_OUT_DIR = "typesafe-jev-release"
# The same targets check-go-module.py cross-compiles on every pull request.
RELEASE_TARGETS = (
    ("darwin", "amd64"),
    ("darwin", "arm64"),
    ("linux", "amd64"),
    ("linux", "arm64"),
)
# The binaries this script runs live at fixed relative paths, so every
# subprocess argv here names its executable literally.
VERIFY_BINARY = "typesafe-jev-release-verify/evaluate"
SMOKE_BINARY = "typesafe-jev-release-smoke/evaluate"
CHECK_UNCONFIGURED = 3
ARCH_NAMES = {"x86_64": "amd64", "amd64": "amd64", "arm64": "arm64", "aarch64": "arm64"}


class ReleaseBuildError(RuntimeError):
    """Raised when a release step cannot run or does not pass."""


def version_from_tag(tag: str) -> str:
    match = TAG_RE.fullmatch(tag or "")
    if match is None:
        raise ReleaseBuildError(f"release tag {tag!r} is not typesafe-jev-vX.Y.Z")
    return match.group("version")


def asset_name(goos: str, goarch: str) -> str:
    return f"evaluate-{goos}-{goarch}.tar.gz"


def _tar_member(name: str, data: bytes, mode: int) -> tuple[tarfile.TarInfo, io.BytesIO]:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mode = mode
    info.mtime = 0
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    info.type = tarfile.REGTYPE
    return info, io.BytesIO(data)


def archive_bytes(binary: bytes, license_text: bytes) -> bytes:
    """Return a reproducible .tar.gz holding `evaluate` and `LICENSE`."""
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for name, data, mode in (("evaluate", binary, 0o755), ("LICENSE", license_text, 0o644)):
            tar.addfile(*_tar_member(name, data, mode))
    compressed = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=compressed, mtime=0) as gz:
        gz.write(raw.getvalue())
    return compressed.getvalue()


def sums_text(archives: Mapping[str, bytes]) -> str:
    """Return SHA256SUMS.txt in `<hex>  <name>` form, one line per archive."""
    return "".join(f"{hashlib.sha256(archives[name]).hexdigest()}  {name}\n" for name in sorted(archives))


def parse_sums(text: str) -> dict[str, str]:
    sums: dict[str, str] = {}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) == 2 and re.fullmatch(r"[0-9a-f]{64}", fields[0]):
            sums[fields[1].lstrip("*")] = fields[0]
    return sums


def _run_options(cwd: Path, env: Mapping[str, str] | None) -> dict[str, object]:
    return {
        "cwd": cwd,
        "env": dict(env) if env is not None else None,
        "text": True,
        "capture_output": True,
        "check": False,
        "shell": False,
    }


# One runner per executable, each naming it literally, so the repository's
# Bash-confinement guard can resolve every command this script starts.
def run_go(*args: str, env: Mapping[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    argv = ["go"]
    argv.extend(args)
    try:
        return subprocess.run(argv, **_run_options(MODULE_DIR, env))
    except OSError as error:
        raise ReleaseBuildError(f"unable to run go: {error}") from error


def run_gh(*args: str) -> subprocess.CompletedProcess[str]:
    argv = ["gh"]
    argv.extend(args)
    try:
        return subprocess.run(argv, **_run_options(REPO_ROOT, None))
    except OSError as error:
        raise ReleaseBuildError(f"unable to run gh: {error}") from error


def run_installer(*args: str) -> subprocess.CompletedProcess[str]:
    argv = [sys.executable, str(INSTALLER)]
    argv.extend(args)
    try:
        return subprocess.run(argv, **_run_options(REPO_ROOT, None))
    except OSError as error:
        raise ReleaseBuildError(f"unable to run the installer: {error}") from error


def run_verify_binary(*args: str, env: Mapping[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    argv = ["typesafe-jev-release-verify/evaluate"]  # VERIFY_BINARY, spelled out for the guard
    argv.extend(args)
    try:
        return subprocess.run(argv, **_run_options(REPO_ROOT, env))
    except OSError as error:
        raise ReleaseBuildError(f"unable to run {VERIFY_BINARY}: {error}") from error


def run_smoke_binary(*args: str, env: Mapping[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    argv = ["typesafe-jev-release-smoke/evaluate"]  # SMOKE_BINARY, spelled out for the guard
    argv.extend(args)
    try:
        return subprocess.run(argv, **_run_options(REPO_ROOT, env))
    except OSError as error:
        raise ReleaseBuildError(f"unable to run {SMOKE_BINARY}: {error}") from error


def _require_success(completed: subprocess.CompletedProcess[str], what: str) -> None:
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise ReleaseBuildError(f"{what} failed with exit code {completed.returncode}: {detail}")


def go_build(goos: str, goarch: str, version: str, output: Path) -> bytes:
    env = {**os.environ, "GOOS": goos, "GOARCH": goarch, "CGO_ENABLED": "0"}
    completed = run_go(
        "build", "-trimpath", "-ldflags", f"-s -w -X main.version={version}", "-o", str(output), "./cmd/evaluate",
        env=env,
    )
    _require_success(completed, f"go build for {goos}/{goarch}")
    return output.read_bytes()


def build(version: str, out_dir: Path) -> dict[str, bytes]:
    out_dir.mkdir(parents=True, exist_ok=True)
    license_text = LICENSE_FILE.read_bytes()
    archives: dict[str, bytes] = {}
    with tempfile.TemporaryDirectory(prefix="typesafe-jev-build-") as scratch:
        for goos, goarch in RELEASE_TARGETS:
            binary = go_build(goos, goarch, version, Path(scratch) / f"evaluate-{goos}-{goarch}")
            name = asset_name(goos, goarch)
            archives[name] = archive_bytes(binary, license_text)
            (out_dir / name).write_bytes(archives[name])
            print(f"built {name}")
    (out_dir / SUMS_NAME).write_text(sums_text(archives), encoding="utf-8")
    print(f"wrote {SUMS_NAME}")
    return archives


def release_files(out_dir: Path) -> list[str]:
    names = [asset_name(goos, goarch) for goos, goarch in RELEASE_TARGETS] + [SUMS_NAME]
    missing = [name for name in names if not (out_dir / name).is_file()]
    if missing:
        raise ReleaseBuildError(f"missing release files in {out_dir}: {', '.join(missing)}")
    return [str(out_dir / name) for name in names]


def upload(tag: str, out_dir: Path) -> None:
    completed = run_gh("release", "upload", tag, *release_files(out_dir), "--clobber")
    _require_success(completed, "gh release upload")
    print(f"uploaded {len(RELEASE_TARGETS)} archives and {SUMS_NAME} to {tag}")


def host_target() -> tuple[str, str]:
    goos = platform.system().lower()
    goarch = ARCH_NAMES.get(platform.machine().lower(), "")
    if (goos, goarch) not in RELEASE_TARGETS:
        raise ReleaseBuildError(f"no release target for {platform.system()} {platform.machine()}")
    return goos, goarch


def extract_binary(archive: bytes) -> bytes:
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        member = tar.getmember("evaluate")
        if not member.isreg():
            raise ReleaseBuildError("archive member evaluate is not a regular file")
        handle = tar.extractfile(member)
        if handle is None:
            raise ReleaseBuildError("archive member evaluate cannot be read")
        return handle.read()


def check_assets(download_dir: Path) -> dict[str, bytes]:
    """Check every archive against SHA256SUMS.txt and return them by name."""
    sums_path = download_dir / SUMS_NAME
    if not sums_path.is_file():
        raise ReleaseBuildError(f"the release has no {SUMS_NAME}")
    sums = parse_sums(sums_path.read_text(encoding="utf-8"))
    archives: dict[str, bytes] = {}
    for goos, goarch in RELEASE_TARGETS:
        name = asset_name(goos, goarch)
        path = download_dir / name
        if not path.is_file():
            raise ReleaseBuildError(f"the release has no {name}")
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if sums.get(name) != digest:
            raise ReleaseBuildError(f"{name} does not match {SUMS_NAME}")
        archives[name] = data
    return archives


def require_version(completed: subprocess.CompletedProcess[str], version: str) -> None:
    """`evaluate version` must print exactly the tag's version."""
    _require_success(completed, "evaluate version")
    if completed.stdout.strip() != version:
        raise ReleaseBuildError(f"evaluate version printed {completed.stdout.strip()!r}, want {version!r}")


def require_unconfigured(completed: subprocess.CompletedProcess[str]) -> None:
    """With no credential anywhere, `call --check` must report exit 3."""
    if completed.returncode != CHECK_UNCONFIGURED:
        raise ReleaseBuildError(
            f"evaluate call --check with no credential exited {completed.returncode}, want {CHECK_UNCONFIGURED}"
        )


def empty_home_env(home: str) -> dict[str, str]:
    return {"PATH": os.environ.get("PATH", ""), "HOME": home}


def install_verify_binary(archive: bytes) -> None:
    target = REPO_ROOT / VERIFY_BINARY
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(extract_binary(archive))
    target.chmod(0o755)


def verify(tag: str, version: str) -> None:
    with tempfile.TemporaryDirectory(prefix="typesafe-jev-verify-") as scratch:
        completed = run_gh("release", "download", tag, "--dir", scratch)
        _require_success(completed, "gh release download")
        archives = check_assets(Path(scratch))
    install_verify_binary(archives[asset_name(*host_target())])
    try:
        require_version(run_verify_binary("version"), version)
        with tempfile.TemporaryDirectory(prefix="typesafe-jev-home-") as home:
            require_unconfigured(run_verify_binary("call", "--check", "--plugin-defaults", env=empty_home_env(home)))
    finally:
        shutil.rmtree(REPO_ROOT / Path(VERIFY_BINARY).parent, ignore_errors=True)
    print(f"verified {tag}: {len(archives)} archives match {SUMS_NAME}; the binary reports {version}")


def publish(tag: str) -> None:
    completed = run_gh("release", "edit", tag, "--draft=false", "--latest=false")
    _require_success(completed, "gh release edit")
    print(f"published {tag}")


def smoke_install(version: str) -> None:
    completed = run_installer("--version", version, "--dest", str(REPO_ROOT / SMOKE_BINARY), "--force")
    _require_success(completed, "install_evaluate.py")
    try:
        require_version(run_smoke_binary("version"), version)
        with tempfile.TemporaryDirectory(prefix="typesafe-jev-home-") as home:
            require_unconfigured(run_smoke_binary("call", "--check", "--plugin-defaults", env=empty_home_env(home)))
    finally:
        shutil.rmtree(REPO_ROOT / Path(SMOKE_BINARY).parent, ignore_errors=True)
    print(f"installed and ran evaluate {version} from the published release")


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", choices=("build", "upload", "verify", "publish", "smoke-install"))
    parser.add_argument("--tag", default=os.environ.get("RELEASE_TAG", ""), help="typesafe-jev-vX.Y.Z (default: $RELEASE_TAG)")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help="where build writes and upload reads the assets")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        version = version_from_tag(args.tag)
        out_dir = Path(args.out_dir)
        if not out_dir.is_absolute():
            out_dir = REPO_ROOT / out_dir
        if args.mode == "build":
            build(version, out_dir)
        elif args.mode == "upload":
            upload(args.tag, out_dir)
        elif args.mode == "verify":
            verify(args.tag, version)
        elif args.mode == "publish":
            publish(args.tag)
        else:
            smoke_install(version)
    except (ReleaseBuildError, OSError, tarfile.TarError, KeyError) as error:
        print(f"build-typesafe-jev-release: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
