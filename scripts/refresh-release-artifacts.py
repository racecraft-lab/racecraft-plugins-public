#!/usr/bin/env python3
"""Refresh generated release artifacts so a release PR passes its own gates.

release-please bumps the source plugin versions and the marketplace registry
version fields but does not rebuild the generated payloads, hash-pinned
installed-cache proofs, or gate evidence. This refreshes all of them from the
current source tree so a release PR is self-consistent before merge. The
proof-snapshot heuristic below assumes this script is the ONLY normal mutator
of dist/** and the installed-cache fixtures — release-please extra-files must
never pre-bump those trees. A canonical-proof fallback also lets the refresh
repair legacy release branches that were partially bumped before that invariant
was enforced, without healing deliberate negative-test sentinels:

1. Recompute the runner trust metadata (manifest sha256 entries + ``.sha256``).
2. Rebuild the Claude and Codex install payloads.
3. Sync the marketplace registries to the source plugin versions.
4. Content-sync the installed-cache fixtures to the rebuilt payloads.
5. Refresh the installed-cache proof tree hashes.
6. Regenerate the payload-completeness, zero-Bash guard, and release-readiness
   evidence.

The refresh is idempotent: a second run on the same source makes no further
changes. It does NOT regenerate the docs reference — the release workflow runs
``pnpm --dir docs-site reference:generate`` separately.
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
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

INSTALLED_CACHE_ROOT = "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache"

PROOF_GLOB_DIR = "tests/speckit-pro/unit/fixtures/plugin-bash-confinement"
EVIDENCE_PROOF = "docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json"
PARTIAL_ROOT_PROOF = f"{PROOF_GLOB_DIR}/installed-cache-proof-partial-root.json"

PAYLOAD_COMPLETENESS_REQUEST = (
    "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/requests/payload-completeness-apply.json"
)
PAYLOAD_COMPLETENESS_RESULT = "docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json"
ZERO_BASH_FINAL_REQUEST = (
    "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/requests/zero-bash-guard-final.json"
)
ZERO_BASH_RESULT = "docs/ai/specs/.process/XPLAT-009-zero-bash-guard-result.json"
RELEASE_READINESS_REQUEST = "tests/speckit-pro/unit/fixtures/installed-plugin-release/requests/release-readiness.json"
RELEASE_READINESS_RESULT = "docs/ai/specs/.process/XPLAT-009-release-readiness-result.json"
RELEASE_READINESS_REQUEST_ID = "xplat-008-release-readiness-ready"

CHECK_WORKTREE_PATHS = (
    "dist",
    ".claude-plugin/marketplace.json",
    ".agents/plugins/marketplace.json",
    "docs-site/src/content/docs/reference",
    RUNNER_MANIFEST_FILE,
    RUNNER_CHECKSUM_FILE,
    INSTALLED_CACHE_ROOT,
    PROOF_GLOB_DIR,
    EVIDENCE_PROOF,
    PAYLOAD_COMPLETENESS_RESULT,
    ZERO_BASH_RESULT,
    RELEASE_READINESS_RESULT,
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

    from speckit_pro_runner.gates import active_path_guard, payloads

    changed: list[str] = []

    # 1. Runner trust metadata (manifest sha256 entries + .sha256 companion).
    changed += refresh_runner_trust_metadata(repo_root)

    # Snapshot each proof row's pre-rebuild recompute so step 5 only refreshes
    # rows whose hash was correct for the old payload; deliberate sentinels
    # (all-zeros, cross-surface mismatches, missing roots) are left untouched.
    proof_files = discover_proof_files(repo_root)
    pre_rebuild = snapshot_proof_recomputes(repo_root, proof_files, active_path_guard)

    # 2. Rebuild Claude and Codex payloads.
    payloads.build_xplat008_payloads(repo_root, repo_root / "dist")

    # 3. Sync marketplace versions to the source plugin versions.
    changed += sync_marketplace_versions(repo_root)

    # 4. Content-sync the installed-cache fixtures to the rebuilt payloads.
    changed += sync_installed_cache_fixtures(repo_root)

    # 5. Refresh installed-cache proof tree hashes. The canonical evidence
    # mapping recovers legacy release branches whose payload was partially
    # bumped before the pre-rebuild snapshot, while the row-level snapshot
    # continues to preserve deliberate negative-test sentinels.
    canonical_replacements = canonical_proof_hash_replacements(repo_root, active_path_guard)
    changed += refresh_proof_tree_hashes(
        repo_root,
        proof_files,
        pre_rebuild,
        active_path_guard,
        canonical_replacements=canonical_replacements,
    )

    # 6. Regenerate gate evidence in gate order.
    changed += regenerate_evidence(repo_root, runner_root)

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
# Step 4: installed-cache fixtures
# --------------------------------------------------------------------------- #


def sync_installed_cache_fixtures(repo_root: Path) -> list[str]:
    changed: list[str] = []
    for product in ("claude", "codex"):
        source_root = repo_root / "dist" / product / "speckit-pro"
        target_root = repo_root / INSTALLED_CACHE_ROOT / product / "speckit-pro"
        changed += mirror_tree_by_content(source_root, target_root, repo_root)
    return changed


def mirror_tree_by_content(source_root: Path, target_root: Path, repo_root: Path) -> list[str]:
    changed: list[str] = []
    source_files = {
        path.relative_to(source_root).as_posix(): path
        for path in source_root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
    target_files = {
        path.relative_to(target_root).as_posix(): path
        for path in target_root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }

    for rel in sorted(set(target_files) - set(source_files)):
        target_files[rel].unlink()
        changed.append(rel_to_repo(target_files[rel], repo_root))

    for rel, source_path in sorted(source_files.items()):
        target_path = target_root / rel
        if (
            rel in target_files
            and sha256_file(target_path) == sha256_file(source_path)
            and normalized_file_mode(target_path) == normalized_file_mode(source_path)
        ):
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        changed.append(rel_to_repo(target_path, repo_root))

    remove_empty_dirs(target_root)
    return changed


def normalized_file_mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def remove_empty_dirs(root: Path) -> None:
    if not root.is_dir():
        return
    for directory in sorted(
        (path for path in root.rglob("*") if path.is_dir()),
        key=lambda item: len(item.parts),
        reverse=True,
    ):
        try:
            directory.rmdir()
        except OSError as exc:
            # Expected during cleanup when a directory is still non-empty or
            # disappears between discovery and removal; re-raise anything else.
            if exc.errno not in (errno.ENOTEMPTY, errno.ENOENT):
                raise


# --------------------------------------------------------------------------- #
# Step 5: installed-cache proof tree hashes
# --------------------------------------------------------------------------- #


def discover_proof_files(repo_root: Path) -> list[Path]:
    fixtures = sorted((repo_root / PROOF_GLOB_DIR).glob("installed-cache-proof*.json"))
    return fixtures + [repo_root / EVIDENCE_PROOF]


def snapshot_proof_recomputes(repo_root: Path, proof_files: list[Path], guard: Any) -> dict[Path, list[str | None]]:
    snapshot: dict[Path, list[str | None]] = {}
    for proof_file in proof_files:
        document = json.loads(proof_file.read_text(encoding="utf-8"))
        rows = document.get("proofs") if isinstance(document.get("proofs"), list) else []
        snapshot[proof_file] = [recompute_tree_hash(repo_root, guard, row) for row in rows]
    return snapshot


def canonical_proof_hash_replacements(repo_root: Path, guard: Any) -> dict[str, str]:
    """Map trusted recorded hashes to rebuilt hashes for legacy partial bumps.

    The committed evidence proof is the canonical full-root positive case. The
    partial-root fixture is also trusted when present because its negative case
    must isolate root-boundary findings without adding a stale-hash finding.
    Replacing those exact hashes across the fixture family preserves intentional
    cross-product mismatches and all-zero stale sentinels while updating every
    positive hash consistently.
    """

    replacements: dict[str, str] = {}
    proof_paths = [EVIDENCE_PROOF]
    if (repo_root / PARTIAL_ROOT_PROOF).is_file():
        proof_paths.append(PARTIAL_ROOT_PROOF)
    for proof_rel in proof_paths:
        proof_file = repo_root / proof_rel
        try:
            proof_text = proof_file.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            fail(f"unable to read canonical installed-cache proof at {proof_rel}: {exc}")
            raise  # unreachable; fail() exits
        try:
            document = json.loads(proof_text)
        except json.JSONDecodeError as exc:
            fail(
                f"canonical installed-cache proof at {proof_rel} is malformed JSON: "
                f"{exc.msg} (line {exc.lineno}, column {exc.colno})"
            )
            raise  # unreachable; fail() exits
        rows = document.get("proofs") if isinstance(document.get("proofs"), list) else []
        for row in rows:
            if not isinstance(row, dict):
                continue
            current = row.get("source_payload_tree_hash")
            rebuilt = recompute_tree_hash(repo_root, guard, row)
            if not isinstance(current, str) or rebuilt is None or current == rebuilt:
                continue
            existing = replacements.get(current)
            if existing is not None and existing != rebuilt:
                fail("canonical installed-cache proof maps one recorded hash to multiple rebuilt hashes")
            replacements[current] = rebuilt
    return replacements


def refresh_proof_tree_hashes(
    repo_root: Path,
    proof_files: list[Path],
    pre_rebuild: dict[Path, list[str | None]],
    guard: Any,
    *,
    canonical_replacements: dict[str, str] | None = None,
) -> list[str]:
    changed: list[str] = []
    for proof_file in proof_files:
        text = proof_file.read_text(encoding="utf-8")
        document = json.loads(text)
        rows = document.get("proofs") if isinstance(document.get("proofs"), list) else []
        replacements = dict(canonical_replacements or {})
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            current = row.get("source_payload_tree_hash")
            old = pre_rebuild.get(proof_file, [])[index] if index < len(pre_rebuild.get(proof_file, [])) else None
            # Only refresh a row whose hash matched the pre-rebuild payload
            # (a genuine, up-to-date proof); leave deliberate sentinels.
            if not isinstance(current, str) or old is None or current != old:
                continue
            new = recompute_tree_hash(repo_root, guard, row)
            if new is not None and new != current:
                existing = replacements.get(current)
                if existing is not None and existing != new:
                    fail("installed-cache proof hash replacement is ambiguous")
                replacements[current] = new
        for current, new in replacements.items():
            text = text.replace(
                f'"source_payload_tree_hash": "{current}"',
                f'"source_payload_tree_hash": "{new}"',
            )
        changed += write_text_if_changed(proof_file, text, repo_root)
    return changed


def recompute_tree_hash(repo_root: Path, guard: Any, row: Any) -> str | None:
    if not isinstance(row, dict):
        return None
    source_root = row.get("source_payload_root")
    if not isinstance(source_root, str) or not source_root:
        return None
    try:
        inventory = guard.payload_tree_inventory(repo_root, source_root, row)
    except (OSError, ValueError):
        return None
    if not inventory or not inventory.get("files"):
        return None
    return inventory["tree_hash"]


# --------------------------------------------------------------------------- #
# Step 6: gate evidence
# --------------------------------------------------------------------------- #


def regenerate_evidence(repo_root: Path, runner_root: Path) -> list[str]:
    changed: list[str] = []

    completeness = run_runner_request(repo_root, runner_root, PAYLOAD_COMPLETENESS_REQUEST)
    if completeness.get("status") != "ok":
        fail(f"payload-completeness gate did not pass (status={completeness.get('status')})")
    changed += write_text_if_changed(
        repo_root / PAYLOAD_COMPLETENESS_RESULT, json.dumps(completeness, indent=2) + "\n", repo_root
    )

    zero_bash = run_runner_request(repo_root, runner_root, ZERO_BASH_FINAL_REQUEST)
    if zero_bash.get("status") != "ok":
        fail(f"zero-bash-guard-final gate did not pass (status={zero_bash.get('status')})")
    changed += write_text_if_changed(
        repo_root / ZERO_BASH_RESULT, json.dumps(zero_bash, indent=2) + "\n", repo_root
    )

    readiness = run_runner_request(
        repo_root, runner_root, RELEASE_READINESS_REQUEST, request_id=RELEASE_READINESS_REQUEST_ID
    )
    if readiness.get("status") != "ok":
        fail(f"release-readiness gate did not pass (status={readiness.get('status')})")
    readiness = normalize_live_host_evidence(readiness)
    readiness_text = (json.dumps(readiness, indent=2) + "\n").replace(str(Path.home()), "<home>")
    changed += write_text_if_changed(repo_root / RELEASE_READINESS_RESULT, readiness_text, repo_root)

    return changed


LIVE_HOST_PYTHON = "<python3>"
LIVE_HOST_SPECIFY = "<specify>"
LIVE_HOST_VERSION = "<version>"
LIVE_HOST_PLATFORM = "<host>"
LIVE_HOST_ARCHITECTURE = "<arch>"


def normalize_live_host_evidence(readiness: dict[str, Any]) -> dict[str, Any]:
    """Canonicalize live host probe fields before committing the evidence.

    The release-readiness payload embeds whichever machine ran the refresh
    last (interpreter path and version, platform, architecture, specify-on-
    PATH), so regenerating on a different OS rewrites the file and the
    artifact-consistency gate reports phantom drift. The release workflow
    re-runs the live gates directly; the committed evidence only needs the
    gate verdicts, not the refreshing host's identity.
    """
    release_readiness = readiness.get("data", {}).get("release_readiness")
    if not isinstance(release_readiness, dict):
        return readiness
    for record in release_readiness.get("runner_invocations") or []:
        if not isinstance(record, dict):
            continue
        if isinstance(record.get("platform"), str):
            record["platform"] = LIVE_HOST_PLATFORM
        inputs = record.get("runner_request", {}).get("inputs", {})
        if isinstance(inputs, dict) and isinstance(inputs.get("platform"), str):
            inputs["platform"] = LIVE_HOST_PLATFORM
        resolution = record.get("interpreter_resolution")
        if isinstance(resolution, dict):
            if isinstance(resolution.get("resolved_executable"), str):
                resolution["resolved_executable"] = LIVE_HOST_PYTHON
            if isinstance(resolution.get("invocation_argv_prefix"), list):
                resolution["invocation_argv_prefix"] = [LIVE_HOST_PYTHON]
            if isinstance(resolution.get("version"), str):
                resolution["version"] = LIVE_HOST_VERSION
            if isinstance(resolution.get("diagnostic"), str):
                resolution["diagnostic"] = re.sub(
                    r"Python \d+(?:\.\d+)*", f"Python {LIVE_HOST_VERSION}", resolution["diagnostic"]
                )
        invocation = record.get("invocation")
        if isinstance(invocation, dict) and isinstance(invocation.get("argv"), list) and invocation["argv"]:
            invocation["argv"][0] = LIVE_HOST_PYTHON
        report = record.get("runner_response", {}).get("data", {}).get("report")
        if isinstance(report, dict):
            if isinstance(report.get("platform"), str):
                report["platform"] = LIVE_HOST_PLATFORM
            if isinstance(report.get("architecture"), str):
                report["architecture"] = LIVE_HOST_ARCHITECTURE
            if isinstance(report.get("python_version"), str):
                report["python_version"] = LIVE_HOST_VERSION
            prerequisites = report.get("prerequisites")
            if isinstance(prerequisites, dict):
                for probe_name, placeholder in (("python", LIVE_HOST_PYTHON), ("specify", LIVE_HOST_SPECIFY)):
                    probe = prerequisites.get(probe_name)
                    if isinstance(probe, dict):
                        if "path" in probe:
                            probe["path"] = placeholder
                        if "version" in probe:
                            probe["version"] = LIVE_HOST_VERSION
                        if "diagnostic_code" in probe:
                            probe["diagnostic_code"] = None
                        if "status" in probe:
                            probe["status"] = "<probe>"
    return readiness


def run_runner_request(
    repo_root: Path, runner_root: Path, request_rel: str, *, request_id: str | None = None
) -> dict[str, Any]:
    request = json.loads((repo_root / request_rel).read_text(encoding="utf-8"))
    if request_id is not None:
        request["request_id"] = request_id
    env = dict(os.environ)
    env["PYTHONPATH"] = str(runner_root)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, "-m", "speckit_pro_runner"],
        input=json.dumps(request).encode("utf-8"),
        capture_output=True,
        cwd=str(repo_root),
        env=env,
        check=False,
    )
    try:
        return json.loads(completed.stdout.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        fail(
            f"runner request {request_rel} did not return a JSON envelope "
            f"(exit={completed.returncode}): {completed.stderr.decode('utf-8', 'replace')[:500]}"
        )
        raise  # unreachable; fail() exits


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
