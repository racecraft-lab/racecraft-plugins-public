#!/usr/bin/env python3
"""Preview or explicitly install pinned, project-local formal tools."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT))

from speckit_pro_runner.formal.catalog import confined, digest, read_json
from speckit_pro_runner.formal.evidence import atomic_record
from speckit_pro_runner.formal.process import runtime_environment
from speckit_pro_runner.formal.quint import ENTRY, inspect, tree_digest, validate_tool

MAX_BYTES = 268435456
TOOLS = {
    "apalache": {
        "version": "0.62.2", "asset": "apalache-0.62.2.tgz",
        "url": "https://github.com/apalache-mc/apalache/releases/download/v0.62.2/apalache-0.62.2.tgz",
        "download_sha256": "765f610537281a0f25b8c30f2554f19523e2859c824e80e62276653ee23c10e2",
        "sha256": "079b6c2320252469dcf79afec6886b8255d3dd1b34a9484433c88986752efaa8",
        "member": "apalache-0.62.2/lib/apalache.jar", "jar": "apalache.jar",
    },
    "tlc": {
        "version": "1.7.4", "asset": "tla2tools-1.7.4.jar",
        "url": "https://github.com/tlaplus/tlaplus/releases/download/v1.7.4/tla2tools.jar",
        "download_sha256": "936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88",
        "sha256": "936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88", "jar": "tla2tools.jar",
    },
}


def download(url: str, target: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "speckit-formal-tool-setup"})
    total = 0
    with urllib.request.urlopen(request, timeout=60) as response, target.open("wb") as stream:
        while chunk := response.read(1048576):
            total += len(chunk)
            if total > MAX_BYTES:
                raise ValueError("Formal tool download exceeds 256 MiB")
            stream.write(chunk)
    if total == 0:
        raise ValueError("Formal tool download was empty")


def materialize_jar(asset: Path, target: Path, tool: dict) -> None:
    if digest(asset) != tool["download_sha256"]:
        raise ValueError("Downloaded tool checksum differs from the pinned release")
    if "member" in tool:
        with tarfile.open(asset) as archive:
            members = [m for m in archive if m.name == tool["member"]]
            if len(members) != 1 or not members[0].isfile() or not 0 < members[0].size <= MAX_BYTES:
                raise ValueError("Pinned distribution must contain exactly one regular checker JAR")
            source = archive.extractfile(members[0])
            if source is None:
                raise ValueError("Pinned distribution JAR could not be read")
            with source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
    else:
        shutil.copyfile(asset, target)
    if digest(target) != tool["sha256"]:
        raise ValueError("Extracted checker JAR checksum differs from the pinned release")


def install_jar(root: Path, base: Path, name: str, cache: Path | None) -> dict:
    tool = TOOLS[name]
    destination = confined(root, (base / (name + "-" + tool["version"])).relative_to(root).as_posix())
    jar = confined(root, (destination / tool["jar"]).relative_to(root).as_posix())
    if not destination.exists():
        with tempfile.TemporaryDirectory(prefix=".setup-", dir=base) as temporary:
            staging = Path(temporary)
            asset = cache / tool["asset"] if cache else staging / tool["asset"]
            if cache is None:
                download(tool["url"], asset)
            materialize_jar(asset, staging / "verified.jar", tool)
            ready = staging / "ready"
            ready.mkdir()
            (staging / "verified.jar").rename(ready / tool["jar"])
            ready.rename(destination)
    if not jar.is_file() or digest(jar) != tool["sha256"]:
        raise ValueError("Existing formal tool differs from the pinned release; inspect it before repairing or replacing it")
    return {"version": tool["version"], "jar": jar.relative_to(root).as_posix(), "sha256": tool["sha256"], "java": "java", "heap_mb": 4096}


def install_quint(root: Path, base: Path) -> dict:
    destination = confined(root, (base / "quint-0.32.0").relative_to(root).as_posix())
    receipt = confined(root, (base / "quint-0.32.0-install.json").relative_to(root).as_posix())
    source = PLUGIN_ROOT / "skills/speckit-coach/examples/formal/tooling/quint"
    if not destination.exists():
        with tempfile.TemporaryDirectory(prefix=".quint-setup-", dir=base) as temporary:
            staging = Path(temporary)
            ready = staging / "ready"
            ready.mkdir()
            for name in ("package.json", "package-lock.json"):
                shutil.copyfile(source / name, ready / name)
            user_config, global_config = staging / "user.npmrc", staging / "global.npmrc"
            user_config.touch()
            global_config.touch()
            env = {k: v for k, v in runtime_environment().items() if not k.lower().startswith("npm_config_") and k not in {"NPM_TOKEN", "NODE_AUTH_TOKEN"}}
            subprocess.run(["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund", "--registry=https://registry.npmjs.org",
                            "--userconfig=" + str(user_config), "--globalconfig=" + str(global_config), "--cache=" + str(staging / "cache")],
                           cwd=ready, env=env, stdin=subprocess.DEVNULL, stdout=sys.stderr, stderr=sys.stderr, check=True, timeout=300)
            if not (ready / ENTRY).is_file() or digest(ready / "package-lock.json") != digest(source / "package-lock.json"):
                raise ValueError("Quint installation did not preserve the approved compiler and lockfile")
            tool = {"version": "0.32.0", "root": str(ready), "tree_sha256": tree_digest(ready), "node": "node"}
            inspect(root, tool)
            ready.rename(destination)
            tool["root"] = destination.relative_to(root).as_posix()
            atomic_record(receipt, tool)
    if not receipt.is_file():
        raise ValueError("Quint installation is interrupted; inspect the directory and restore its recorded identity before retrying")
    tool = read_json(receipt)
    validate_tool(tool)
    if tool["root"] != destination.relative_to(root).as_posix() or digest(destination / "package-lock.json") != digest(source / "package-lock.json"):
        raise ValueError("Quint receipt must identify this project-local installation and the shipped lockfile")
    inspect(root, tool)
    return tool


def setup(root: Path, selected: list[str], apply: bool, cache: Path | None = None) -> dict:
    root = root.resolve(strict=True)
    base = confined(root, ".specify/tools/formal")
    if not apply:
        return {"verdict": "preview", "writes_state": False, "destination": str(base), "selected": selected,
                "downloads": {name: TOOLS[name] for name in selected if name in TOOLS},
                "quint": "npm ci from the shipped lockfile; lifecycle scripts disabled" if "quint" in selected else None,
                "requirements": "Existing Java for checker execution; Node.js 24 and npm for selected Quint only. No runtimes are installed."}
    base.mkdir(parents=True, exist_ok=True)
    ignored = confined(root, (base / ".gitignore").relative_to(root).as_posix())
    ignored.write_text("*\n", encoding="utf-8")
    installed = {name: install_quint(root, base) if name == "quint" else install_jar(root, base, name, cache) for name in selected}
    return {"verdict": "installed", "writes_state": True, "tools": installed,
            "next": "Review these entries in the model catalog, then run formal-doctor. Selection is unchanged."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--tool", choices=("apalache", "tlc", "quint"), action="append", required=True)
    parser.add_argument("--apply", action="store_true", help="Explicitly authorize the displayed downloads and project-local installation")
    parser.add_argument("--download-cache", type=Path, help="Use already downloaded JAR/distribution assets; do not download missing assets")
    args = parser.parse_args()
    try:
        result = setup(args.repo_root, list(dict.fromkeys(args.tool)), args.apply, args.download_cache)
    except (ValueError, OSError, subprocess.SubprocessError, tarfile.TarError) as exc:
        result = {"verdict": "setup_failed", "reason": str(exc), "writes_state": args.apply}
    print(json.dumps(result, sort_keys=True, indent=2))
    return 1 if result["verdict"] == "setup_failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
