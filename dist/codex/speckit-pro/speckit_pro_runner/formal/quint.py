"""Pinned Quint compilation to JSON; the existing Apalache process owns checking."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any

from .catalog import FormalError, confined, digest, read_json
from .process import run_process, runtime_environment
from .selection import require_fields, require_text, unique_object

VERSION = "0.32.0"
PACKAGE = "node_modules/@informalsystems/quint"
ENTRY = PACKAGE + "/dist/src/cli.js"


def installation(root: Path, tool: dict[str, Any]) -> Path:
    path = Path(tool["root"])
    return path.resolve() if path.is_absolute() else confined(root, tool["root"])


def tree_digest(directory: Path) -> str:
    """Pin the compiler and all installed dependencies without following symlinks."""
    directory = directory.resolve(strict=True)
    result = hashlib.sha256()
    for path in sorted(directory.rglob("*")):
        name = path.relative_to(directory).as_posix()
        if path.is_symlink():
            if not path.resolve().is_relative_to(directory):
                raise FormalError("unsupported", "Quint installation links outside its pinned directory")
            result.update(name.encode() + b"\0link:" + str(path.readlink()).encode() + b"\n")
            continue  # only the fixed CLI entry is executed; npm's .bin links are unused
        if path.is_file():
            result.update(name.encode() + b"\0" + digest(path).encode() + b"\n")
    return result.hexdigest()


def validate_tool(value: Any) -> dict[str, Any]:
    if value is None:
        raise FormalError("missing_tool", "Configure the approved pinned Quint installation in catalog.tools.quint")
    require_fields(value, {"version", "root", "tree_sha256", "node"}, "Quint tool")
    if value["version"] != VERSION:
        raise FormalError("version_mismatch", f"Quint requires qualified version {VERSION}")
    for key in ("root", "node"):
        require_text(value[key], f"quint.{key}")
    if not isinstance(value["tree_sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", value["tree_sha256"]):
        raise ValueError("quint.tree_sha256 must pin the full installed compiler/dependency tree")
    return value


def inspect(root: Path, tool: dict[str, Any]) -> dict[str, Any]:
    directory = installation(root, tool)
    if not (directory / ENTRY).is_file() or not (directory / "package-lock.json").is_file():
        raise FormalError("missing_tool", "Install the pinned Quint package and lockfile explicitly before checking")
    metadata = read_json(directory / PACKAGE / "package.json")
    if metadata.get("version") != VERSION or tree_digest(directory) != tool["tree_sha256"]:
        raise FormalError("version_mismatch", "Quint package version or full installation checksum differs from the catalog")
    node = shutil.which("node")
    requested = shutil.which(tool["node"])
    if node is None or requested is None or Path(node).resolve() != Path(requested).resolve():
        raise FormalError("missing_tool", "Select the configured Node.js runtime on PATH")
    result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=10, stdin=subprocess.DEVNULL,
                            shell=False, env=runtime_environment())
    version = result.stdout.strip()
    if result.returncode or not re.fullmatch(r"v24\.\d+\.\d+", version):
        raise FormalError("version_mismatch", "The qualified Quint profile uses Node.js 24")
    return {"version": VERSION, "tree_sha256": tool["tree_sha256"], "node_version": version, "node_sha256": digest(Path(node).resolve())}


def command(root: Path, tool: dict[str, Any], model: dict[str, Any], snapshot: str) -> list[str]:
    directory = installation(root, tool)
    return [str(shutil.which(tool["node"])), "--permission", f"--allow-fs-read={directory}", f"--allow-fs-read={snapshot}",
            str(directory / ENTRY), "compile", "--target=json", "--flatten=true", "--main=" + model["main"],
            "--init=" + model["init"], "--step=" + model["next"], model["module"]]


def compile_model(root: Path, item: dict[str, Any], snapshot: Path, timeout: int) -> tuple[dict[str, Any], dict[str, Any]]:
    model = item["model"]
    path = snapshot / (model["module"] + ".json")
    result = run_process(command(root, item["compiler"], model, str(snapshot)), snapshot, path, timeout, model["budget"]["output_bytes"])
    verdict = "inconclusive"
    if result["timed_out"]:
        verdict = "timeout"
    elif not result["output_limited"] and result["exit_code"] == 0:
        try:
            compiled = json.loads(result["output"], object_pairs_hook=unique_object)
            if compiled.get("main") == model["main"] and isinstance(compiled.get("modules"), list) and compiled["modules"]:
                verdict = "compiled"
        except (ValueError, AttributeError):
            verdict = "inconclusive"
    elif result["exit_code"] == 1 and ("QNT" in result["output"] or "error:" in result["output"]):
        verdict = "invalid_model"
    receipt = {"verdict": verdict, "exit_code": result["exit_code"], "duration_ms": result["duration_ms"],
               "output": path.relative_to(root).as_posix(), "excerpt": "" if verdict == "compiled" else result["output"][-2048:]}
    return {**model, "module": path.relative_to(snapshot).as_posix()}, receipt
