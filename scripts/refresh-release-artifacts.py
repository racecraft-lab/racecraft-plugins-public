#!/usr/bin/env python3
"""Refresh generated release artifacts so a release PR passes its own gates.

release-please bumps the source plugin versions and the marketplace registry
version fields but does not rebuild the generated payloads. This refreshes
them from the current source tree so a release PR is self-consistent before
merge:

1. Recompute the runner trust metadata (manifest sha256 entries + ``.sha256``).
2. Rebuild the Claude and Codex install payloads.
3. Sync the marketplace registries to the source plugin versions.

The refresh is idempotent: a second run on the same source makes no further
changes. It does NOT regenerate the docs reference — the release workflow runs
``pnpm --dir docs-site reference:generate`` separately.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, TextIO

sys.dont_write_bytecode = True

RUNNER_MANIFEST_FILE = "speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json"
RUNNER_CHECKSUM_FILE = "speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256"

# marketplace registry -> within-plugin manifest read from each entry's source dir
MARKETPLACES = (
    (".claude-plugin/marketplace.json", ".claude-plugin/plugin.json"),
    (".agents/plugins/marketplace.json", ".codex-plugin/plugin.json"),
)

CHECK_WORKTREE_PATHS = (
    "dist",
    ".claude-plugin/marketplace.json",
    ".agents/plugins/marketplace.json",
    "docs-site/src/content/docs/reference",
    RUNNER_MANIFEST_FILE,
    RUNNER_CHECKSUM_FILE,
)
CHECK_COPY_IGNORES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".worktrees",
    "__pycache__",
    "node_modules",
}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify generated artifacts in an isolated copy without mutating the worktree",
    )
    args = parser.parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    if args.check:
        return check_release_artifacts(repo_root)
    return refresh_release_artifacts(repo_root)


def refresh_release_artifacts(repo_root: Path) -> int:
    runner_root = repo_root / "speckit-pro"
    sys.path.insert(0, str(runner_root))

    from speckit_pro_runner.gates import payloads

    changed: list[str] = []

    # 1. Runner trust metadata (manifest sha256 entries + .sha256 companion).
    changed += refresh_runner_trust_metadata(repo_root)

    # 2. Rebuild Claude and Codex payloads.
    payloads.build_installed_plugin_payloads(repo_root, repo_root / "dist")

    # 3. Sync marketplace versions to the source plugin versions.
    changed += sync_marketplace_versions(repo_root)

    if changed:
        print("Refreshed release artifacts:")
        for path in sorted(dict.fromkeys(changed)):
            print(f"  {path}")
    else:
        print("Release artifacts already consistent; no changes.")
    return 0


def check_release_artifacts(
    repo_root: Path,
    *,
    run: Callable[..., subprocess.CompletedProcess[Any]] = subprocess.run,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Regenerate in an isolated copy and report content or file-mode drift."""
    stdout = sys.stdout if stdout is None else stdout
    stderr = sys.stderr if stderr is None else stderr
    repo_root = repo_root.resolve()

    try:
        status = run(
            [
                "git",
                "status",
                "--porcelain",
                "--untracked-files=all",
                "--",
                *CHECK_WORKTREE_PATHS,
            ],
            cwd=str(repo_root),
            text=True,
            capture_output=True,
            check=False,
            shell=False,
        )
    except OSError as exc:
        print(f"::error::Unable to inspect generated release artifacts: {exc}", file=stderr)
        return 1
    if status.returncode != 0:
        if status.stderr:
            stderr.write(status.stderr)
        print(
            f"::error::Unable to inspect generated release artifacts "
            f"(git status exited {status.returncode}).",
            file=stderr,
        )
        return status.returncode or 1
    worktree_drift = [line for line in status.stdout.splitlines() if line.strip()]
    if worktree_drift:
        report_check_drift(worktree_drift, stderr)
        return 1

    try:
        source_before = snapshot_tree(repo_root)
        with tempfile.TemporaryDirectory(prefix="release-artifact-check-") as tmp:
            isolated_root = Path(tmp) / "repository"
            shutil.copytree(
                repo_root,
                isolated_root,
                ignore=ignored_copy_names,
                symlinks=True,
            )
            for setup_argv in (
                ["git", "init", "--quiet"],
                ["git", "add", "--all"],
            ):
                setup = run(
                    setup_argv,
                    cwd=str(isolated_root),
                    text=True,
                    capture_output=True,
                    check=False,
                    shell=False,
                )
                if setup.returncode != 0:
                    if setup.stderr:
                        stderr.write(setup.stderr)
                    print(
                        f"::error::Unable to prepare the isolated release artifact check "
                        f"({setup_argv[0]} {setup_argv[1]} exited {setup.returncode}).",
                        file=stderr,
                    )
                    return setup.returncode or 1
            child_environment = os.environ.copy()
            child_environment["PYTHONDONTWRITEBYTECODE"] = "1"
            completed = run(
                [sys.executable, "scripts/refresh-release-artifacts.py"],
                cwd=str(isolated_root),
                env=child_environment,
                text=True,
                capture_output=True,
                check=False,
                shell=False,
            )
            if completed.returncode != 0:
                if completed.stdout:
                    stdout.write(completed.stdout)
                if completed.stderr:
                    stderr.write(completed.stderr)
                print(
                    f"::error::Generated release artifact verification failed "
                    f"(refresh exited {completed.returncode}).",
                    file=stderr,
                )
                return completed.returncode or 1
            isolated_after = snapshot_tree(isolated_root)
        source_after = snapshot_tree(repo_root)
    except OSError as exc:
        print(f"::error::Unable to verify generated release artifacts: {exc}", file=stderr)
        return 1

    if source_after != source_before:
        print(
            "::error::The source worktree changed while generated release artifacts were checked.",
            file=stderr,
        )
        return 1

    drift = compare_snapshots(source_before, isolated_after)
    if drift:
        report_check_drift(drift, stderr)
        return 1

    print("Generated release artifacts match the source tree.", file=stdout)
    return 0


def ignored_copy_names(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in CHECK_COPY_IGNORES}


def snapshot_tree(root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for directory, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current = Path(directory)
        dirnames[:] = sorted(name for name in dirnames if name not in CHECK_COPY_IGNORES)
        for name in tuple(dirnames):
            path = current / name
            if path.is_symlink():
                key = path.relative_to(root).as_posix()
                snapshot[key] = f"link:{os.readlink(path)}"
                dirnames.remove(name)
        for name in sorted(filenames):
            if name in CHECK_COPY_IGNORES:
                continue
            path = current / name
            key = path.relative_to(root).as_posix()
            if path.is_symlink():
                snapshot[key] = f"link:{os.readlink(path)}"
            elif path.is_file():
                mode = stat.S_IMODE(path.stat().st_mode)
                snapshot[key] = f"file:{mode:04o}:{sha256_file(path)}"
    return snapshot


def compare_snapshots(before: dict[str, str], after: dict[str, str]) -> list[str]:
    changes: list[str] = []
    for path in sorted(before.keys() | after.keys()):
        if path not in before:
            changes.append(f"A {path}")
        elif path not in after:
            changes.append(f"D {path}")
        elif before[path] != after[path]:
            changes.append(f"M {path}")
    return changes


def report_check_drift(drift: Sequence[str], stderr: TextIO) -> None:
    print(
        "::error::Generated release artifacts drift from the source tree. "
        "Run scripts/refresh-release-artifacts.py and commit the result. "
        "After publishing, re-run the Release workflow to re-sync the release PR "
        "(Recovery Scenario 1).",
        file=stderr,
    )
    print("Generated artifact drift:", file=stderr)
    for line in dict.fromkeys(drift):
        print(f"  {line}", file=stderr)


# --------------------------------------------------------------------------- #
# Step 1: runner trust metadata
# --------------------------------------------------------------------------- #


def refresh_runner_trust_metadata(repo_root: Path) -> list[str]:
    plugin_root = repo_root / "speckit-pro"
    package_dir = plugin_root / "speckit_pro_runner"
    source_files = sorted(
        path for path in package_dir.rglob("*.py") if "__pycache__" not in path.parts
    )
    digests = {path.relative_to(plugin_root).as_posix(): sha256_file(path) for path in source_files}

    changed: list[str] = []

    manifest_path = repo_root / RUNNER_MANIFEST_FILE
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["runner_files"] = [
        {
            "path": {"kind": "plugin_relative", "value": rel, "display": rel},
            "sha256": digest,
        }
        for rel, digest in sorted(digests.items())
    ]
    changed += write_text_if_changed(manifest_path, json.dumps(manifest, indent=2) + "\n", repo_root)

    checksum_text = "".join(f"{digest}  {rel}\n" for rel, digest in sorted(digests.items()))
    changed += write_text_if_changed(repo_root / RUNNER_CHECKSUM_FILE, checksum_text, repo_root)

    return changed


# --------------------------------------------------------------------------- #
# Step 3: marketplace versions
# --------------------------------------------------------------------------- #


def sync_marketplace_versions(repo_root: Path) -> list[str]:
    changed: list[str] = []
    for marketplace_rel, manifest_rel in MARKETPLACES:
        marketplace_path = repo_root / marketplace_rel
        if not marketplace_path.is_file():
            continue
        document = json.loads(marketplace_path.read_text(encoding="utf-8"))
        plugins = document.get("plugins")
        if not isinstance(plugins, list):
            continue
        mutated = False
        for entry in plugins:
            if not isinstance(entry, dict):
                continue
            source = entry.get("source")
            source_path = source if isinstance(source, str) else source.get("path") if isinstance(source, dict) else None
            if not isinstance(source_path, str) or not source_path.startswith("./") or ".." in source_path:
                continue
            plugin_manifest = repo_root / source_path[2:] / manifest_rel
            if not plugin_manifest.is_file():
                continue
            version = json.loads(plugin_manifest.read_text(encoding="utf-8")).get("version")
            if isinstance(version, str) and version and entry.get("version") != version:
                entry["version"] = version
                mutated = True
        if mutated:
            changed += write_text_if_changed(
                marketplace_path, json.dumps(document, indent=2) + "\n", repo_root
            )
    return changed


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def write_text_if_changed(path: Path, text: str, repo_root: Path) -> list[str]:
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return []
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return [rel_to_repo(path, repo_root)]


def rel_to_repo(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fail(message: str) -> None:
    print(f"refresh-release-artifacts: {message}", file=sys.stderr)
    raise SystemExit(1)


if __name__ == "__main__":
    raise SystemExit(main())
