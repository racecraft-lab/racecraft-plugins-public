"""Inspect pinned tools and execute selected models from isolated input snapshots."""

from __future__ import annotations

import math
import re
import shutil
import subprocess
import time
import uuid
import zipfile
from pathlib import Path
from typing import Any

from . import apalache, tlc
from .catalog import RUNS_PATH, FormalError, confined, digest
from .process import run_process

ADAPTERS = {"apalache": apalache, "tlc": tlc}
CHECKER_SHA256 = {"apalache": "079b6c2320252469dcf79afec6886b8255d3dd1b34a9484433c88986752efaa8",
                  "tlc": "936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88"}


def manifest_attributes(manifest: str) -> dict[str, str]:
    """Unfold headers in the main section according to the JAR specification."""
    main = manifest.replace("\r\n", "\n").replace("\r", "\n").split("\n\n", 1)[0]
    unfolded = main.replace("\n ", "")
    return {key.lower(): value for line in unfolded.split("\n") if ": " in line for key, value in [line.split(": ", 1)]}


def inspect_tool(root: Path, tool: dict[str, Any], checker: str) -> dict[str, Any]:
    jar = Path(tool["jar"])
    jar = jar.resolve() if jar.is_absolute() else confined(root, tool["jar"])
    java = shutil.which("java")
    requested_java = shutil.which(tool["java"])
    if java is None or requested_java is None or Path(java).resolve() != Path(requested_java).resolve():
        raise FormalError("missing_tool", "Select the configured Java runtime on PATH before running formal-doctor")
    if java is None or not jar.is_file():
        raise FormalError("missing_tool", f"Install the pinned {checker} distribution and Java explicitly; expected jar: {tool['jar']}")
    actual = digest(jar)
    if actual != tool["sha256"] or actual != CHECKER_SHA256.get(checker):
        raise FormalError("version_mismatch", f"{checker} jar checksum differs from the plugin-pinned distribution or catalog")
    with zipfile.ZipFile(jar) as archive:
        manifest = archive.read("META-INF/MANIFEST.MF").decode("utf-8")
    metadata = manifest_attributes(manifest)
    version = metadata.get("x-git-tag", "").removeprefix("v") if checker == "tlc" else metadata.get("implementation-version")
    if version != tool["version"]:
        raise FormalError("version_mismatch", f"{checker} jar manifest does not report {tool['version']}")
    if any((jar.parent / name).exists() for name in metadata.get("class-path", "").split()):
        raise FormalError("unsupported", "untracked JAR sidecars can change model semantics; use an isolated official distribution")
    completed = subprocess.run([java, "-version"], capture_output=True, text=True, timeout=10, check=False, shell=False)
    version = (completed.stdout + completed.stderr).strip()
    match = re.search(r'version "(\d+)', version)
    minimum = 11 if checker == "tlc" else 21
    if completed.returncode or match is None or int(match.group(1)) < minimum:
        raise FormalError("missing_tool", f"{checker} requires Java {minimum} or newer")
    return {"checker": checker, "version": tool["version"], "sha256": actual, "java_version": version, "java_sha256": digest(Path(java).resolve())}


def checker_command(root: Path, tool: dict[str, Any], temporary: str) -> list[str]:
    jar = Path(tool["jar"])
    jar = jar.resolve() if jar.is_absolute() else confined(root, tool["jar"])
    java = shutil.which(tool["java"])
    if java is None:
        raise FormalError("missing_tool", "Select the configured Java runtime on PATH before running the checker")
    return [java, f"-Xmx{tool['heap_mb']}m", "-XX:+UseParallelGC", f"-Djava.io.tmpdir={temporary}", "-jar", str(jar)]


def obligations(model: dict[str, Any]) -> list[dict[str, Any]]:
    return ADAPTERS[model["checker"]].obligations(model)


def preview_model(root: Path, item: dict[str, Any]) -> list[dict[str, Any]]:
    adapter = ADAPTERS[item["model"]["checker"]]
    return [{"id": obligation["id"], "argv": checker_command(root, item["tool"], "<run>/tmp") + adapter.arguments(item["model"], obligation, "<run>/output", "<run>/settings.json")} for obligation in obligations(item["model"])]


def execute_model(root: Path, model_id: str, item: dict[str, Any]) -> dict[str, Any]:
    model = item["model"]
    adapter = ADAPTERS[model["checker"]]
    inspect_tool(root, item["tool"], model["checker"])
    run = confined(root, f"{RUNS_PATH}/{model_id}/{uuid.uuid4().hex}")
    snapshot = run / "inputs"
    snapshot.mkdir(parents=True)
    (run / "tmp").mkdir()
    confined(root, f"{RUNS_PATH}/.gitignore").write_text("*\n", encoding="utf-8")
    for value in model["inputs"]:
        destination = snapshot / value
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(confined(root, value, durable=True), destination)
        if digest(destination) != item["input_hashes"][value]:
            raise FormalError("stale", f"model input changed while snapshotting: {value}")
    settings = run / "settings.json"
    settings.write_text("{}\n", encoding="utf-8")
    deadline = time.monotonic() + model["budget"]["timeout_seconds"]
    results = []
    for obligation in obligations(model):
        remaining = math.ceil(deadline - time.monotonic())
        if remaining <= 0:
            results.append({"id": obligation["id"], "verdict": "timeout"})
            break
        log = run / f"{obligation['id']}.log"
        argv = checker_command(root, item["tool"], str(run / "tmp")) + adapter.arguments(model, obligation, str(run / obligation["id"]), str(settings))
        result = run_process(argv, snapshot, log, remaining, model["budget"]["output_bytes"])
        status = adapter.verdict(result)
        configured = dict(re.findall(r"(?m)^\s*> Set the (initialization|transition) predicate to (\w+)\s+I@\S+\s*$", result["output"]))
        if model["checker"] == "apalache" and status == "pass" and configured != {"initialization": obligation["init"], "transition": model["next"]}:
            status = "inconclusive"
        results.append({"id": obligation["id"], "verdict": status, "exit_code": result["exit_code"], "duration_ms": result["duration_ms"], "excerpt": result["output"][-4096:], "log": log.relative_to(root).as_posix()})
        if status != "pass":
            break
    passed = len(results) == len(obligations(model)) and all(r["verdict"] == "pass" for r in results)
    return {"model": model_id, "verdict": "pass" if passed else results[-1]["verdict"], "mode": model["mode"], "bounds": model["bounds"], "assumptions": model["assumptions"], "obligations": results}
