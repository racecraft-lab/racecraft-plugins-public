#!/usr/bin/env python3
"""run-all.py — Python stdlib orchestrator for the speckit-pro test suite.

Reproduces the ``run-all.sh`` developer UX 1:1 (XPLAT-010 US1, FR-006, research
§D5) with no Bash or ``jq`` dependency of its own:

  run-all.py               # Layers 1, 4, 5 + toolchain preflight (default)
  run-all.py --live        # default layers, passing --live to the child tests
  run-all.py --layer 4     # a single layer
  run-all.py --integration # Layer 7 (integration fixtures)
  run-all.py --all         # every layer that has a runner block + live
  run-all.py --verbose     # per-test VERBOSE output in the children

The layer roster, per-layer scripts, execution mode (execute vs print-commands),
and counting flags all come from ``tests/speckit-pro/suite-manifest.json`` — the
single source of truth the shipped suite gate also reads. Layer 8 is a gate-only
parity layer with no run-all block, matching ``run-all.sh``.

Headline: ``speckit-pro test suite: X/Y passed`` (``X/Y passed (Z failed)`` on
failure), where X/Y sums each child's ``<label>: X/Y passed`` line. Exit 0 iff
no failures, 1 on any failure, 2 on an unknown flag.

Transitional dispatch (until the ports land): ``.sh`` children run via ``bash``
when it is available; on a Bash-absent platform each is skipped with an explicit
diagnostic (never a silent green) per FR-006. ``.py`` children always run.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SUITE_MANIFEST = "tests/speckit-pro/suite-manifest.json"
SUMMARY_RE = re.compile(r"[0-9]+/[0-9]+ passed")
COUNT_RE = re.compile(r"([0-9]+)/([0-9]+)")
RULE = "────────────────────────────────────────"
HEADER_RULE = "════════════════════════════════════════"
# Child layers that honour the --live flag in run-all.sh (Layer 4 unit tests and
# Layer 7 integration fixtures); Layers 1/5 ignore it.
LIVE_AWARE_LAYERS = {"4", "7"}
TOOLCHAIN_TRIGGER_LAYERS = ("1", "4", "5", "7")


class UsageError(Exception):
    """Raised on an unknown/malformed flag (maps to exit code 2)."""


@dataclass
class Config:
    live: bool = False
    run_all: bool = False
    run_layer: str | None = None
    verbose: bool = False


def parse_args(argv: list[str]) -> Config:
    config = Config()
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--live":
            config.live = True
            index += 1
        elif arg == "--layer":
            if index + 1 >= len(argv):
                raise UsageError("--layer requires a value")
            config.run_layer = argv[index + 1]
            index += 2
        elif arg == "--integration":
            config.run_layer = "7"
            index += 1
        elif arg == "--all":
            config.run_all = True
            config.live = True
            index += 1
        elif arg == "--verbose":
            config.verbose = True
            index += 1
        else:
            raise UsageError(arg)
    return config


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_manifest(root: Path) -> dict:
    return json.loads((root / SUITE_MANIFEST).read_text(encoding="utf-8"))


def layer_should_run(layer: dict, config: Config) -> bool:
    layer_id = layer["id"]
    if layer_id == "toolchain":
        return False
    # Layer 8 is gate-only: no default, not live, not integration -> no run-all block.
    has_block = layer["default"] or layer["live_only"] or layer["integration"]
    if not has_block:
        return False
    if config.run_layer is not None:
        return config.run_layer == layer_id
    if config.run_all:
        return True
    return bool(layer["default"])


def toolchain_should_run(manifest: dict, config: Config) -> bool:
    by_id = {layer["id"]: layer for layer in manifest["layers"]}
    return any(
        layer_id in by_id and layer_should_run(by_id[layer_id], config)
        for layer_id in TOOLCHAIN_TRIGGER_LAYERS
    )


def parse_summary(output: str) -> tuple[int, int] | None:
    last = None
    for line in output.splitlines():
        if SUMMARY_RE.search(line):
            last = line
    if last is None:
        return None
    match = COUNT_RE.search(last)
    return (int(match.group(1)), int(match.group(2)))


def sum_all_summaries(output: str) -> tuple[int, int] | None:
    lines = [line for line in output.splitlines() if SUMMARY_RE.search(line)]
    if not lines:
        return None
    passed = total = 0
    for line in lines:
        match = COUNT_RE.search(line)
        passed += int(match.group(1))
        total += int(match.group(2))
    return (passed, total)


def classify_child(exit_code: int, summary: tuple[int, int] | None) -> tuple[str, int, int]:
    """Return (disposition, passed_delta, failed_delta) per the FR-006 taxonomy."""
    if summary is not None:
        passed, total = summary
        failed = total - passed
        if exit_code != 0 and failed == 0:
            return ("failed-exit", passed, 1)
        return ("counted", passed, failed)
    if exit_code == 0:
        # A zero-exit module with no summary line is a no-summary pass.
        return ("no-summary-pass", 0, 0)
    # A nonzero exit with no summary is a crash -> exactly one failed unit.
    return ("crash", 0, 1)


def format_headline(passed: int, failed: int) -> str:
    total = passed + failed
    if failed == 0 and total > 0:
        return f"speckit-pro test suite: {passed}/{total} passed"
    return f"speckit-pro test suite: {passed}/{total} passed ({failed} failed)"


def exit_code_for(total_fail: int) -> int:
    return 0 if total_fail == 0 else 1


def child_env(root: Path, config: Config) -> dict[str, str]:
    env = os.environ.copy()
    env["TESTS_DIR"] = str(root / "tests" / "speckit-pro")
    env["PLUGIN_ROOT"] = str(root / "speckit-pro")
    env.setdefault("PROJECT_ROOT", env["PLUGIN_ROOT"])
    if config.verbose:
        env["VERBOSE"] = "true"
    return env


def dispatch_script(
    path: Path,
    layer: dict,
    config: Config,
    root: Path,
    bash_path: str | None,
) -> tuple[str, int, bool]:
    """Run one child test. Returns (merged_output, exit_code, bash_absent_skip)."""
    pass_live = config.live and layer["id"] in LIVE_AWARE_LAYERS
    if path.suffix == ".py":
        argv = [sys.executable, str(path)]
    else:
        if bash_path is None:
            return ("", 0, True)
        argv = [bash_path, str(path)]
    if pass_live:
        argv.append("--live")
    completed = subprocess.run(
        argv,
        cwd=root,
        text=True,
        capture_output=True,
        env=child_env(root, config),
        shell=False,
        check=False,
    )
    return (completed.stdout + completed.stderr, completed.returncode, False)


def run_execute_layer(layer: dict, config: Config, root: Path, bash_path: str | None) -> tuple[int, int]:
    print(f"\nLayer {layer['id']}: {layer['label']}")
    print(RULE)
    layer_pass = layer_fail = 0
    for script in layer["scripts"]:
        path = root / script["path"]
        label = Path(script["path"]).stem
        if not path.is_file():
            print(f"  SKIP: {label} (not found)")
            continue
        output, exit_code, bash_absent = dispatch_script(path, layer, config, root, bash_path)
        if bash_absent:
            # FR-006: a transitional .sh child on a Bash-absent platform is
            # skipped with an explicit diagnostic, never a silent green.
            print(f"  SKIP: {label} (bash unavailable — transitional .sh dispatch pending port)")
            continue
        summary = sum_all_summaries(output) if layer["integration"] else parse_summary(output)
        disposition, passed, failed = classify_child(exit_code, summary)
        layer_pass += passed
        layer_fail += failed
        if disposition == "crash":
            print(f"  FAIL {label} (exit {exit_code}, no summary — child may have crashed)")
        elif disposition == "no-summary-pass":
            print(f"  PASS {label} (no summary)")
        elif failed == 0:
            print(f"  PASS {label} ({passed}/{passed + failed})")
        else:
            print(f"  FAIL {label} ({passed}/{passed + failed}, {failed} failed)")
    return layer_pass, layer_fail


def print_layer_commands(layer: dict, root: Path) -> None:
    print(f"\nLayer {layer['id']}: {layer['label']}")
    print(RULE)
    print("  Run manually (requires claude -p / codex):")
    for script in layer["scripts"]:
        print(f"    bash {script['path']}")


def run_toolchain_preflight(root: Path, config: Config, manifest: dict) -> bool:
    by_id = {layer["id"]: layer for layer in manifest["layers"]}
    mode = "tests" if ("1" in by_id and layer_should_run(by_id["1"], config)) else "shell"
    request = {
        "schema_version": "1.0",
        "request_id": "run-all-py-toolchain",
        "helper_id": "suite-gate",
        "operation": "run-toolchain-preflight",
        "mode": "read_only",
        "inputs": {"mode": mode, "repo_root": "."},
    }
    env = os.environ.copy()
    plugin_root = str(root / "speckit-pro")
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = plugin_root if not existing else f"{plugin_root}{os.pathsep}{existing}"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, "-m", "speckit_pro_runner"],
        input=json.dumps(request),
        text=True,
        capture_output=True,
        cwd=root,
        env=env,
        shell=False,
        check=False,
    )
    try:
        response = json.loads(completed.stdout) if completed.stdout.strip() else {}
    except json.JSONDecodeError:
        return False
    return response.get("status") == "ok"


def print_summary(total_pass: int, total_fail: int, layer_results: list[str]) -> None:
    print()
    print(HEADER_RULE)
    print(format_headline(total_pass, total_fail))
    for line in layer_results:
        print(f"  {line}")
    print()


def main(argv: list[str]) -> int:
    try:
        config = parse_args(argv)
    except UsageError as exc:
        print(f"Unknown flag: {exc}", file=sys.stderr)
        return 2

    root = repo_root()
    manifest = load_manifest(root)
    bash_path = shutil.which("bash")

    total_pass = total_fail = 0
    layer_results: list[str] = []

    if os.environ.get("SPECKIT_SKIP_TOOLCHAIN_CHECK") != "1" and toolchain_should_run(manifest, config):
        print("\nToolchain Preflight")
        print(RULE)
        if not run_toolchain_preflight(root, config, manifest):
            print("  FAIL check-toolchain (gate)")
            print("\nToolchain preflight failed — aborting before running any layer.", file=sys.stderr)
            print("Fix the tools listed above, or set SPECKIT_SKIP_TOOLCHAIN_CHECK=1 to bypass the gate.", file=sys.stderr)
            return 1
        print("  PASS check-toolchain (gate; not counted in suite total)")
        layer_results.append("toolchain preflight: ok (gate, not counted)")

    for layer in manifest["layers"]:
        if not layer_should_run(layer, config):
            continue
        if layer["execution"] == "print-commands":
            print_layer_commands(layer, root)
            continue
        layer_pass, layer_fail = run_execute_layer(layer, config, root, bash_path)
        total_pass += layer_pass
        total_fail += layer_fail
        layer_results.append(f"L{layer['id']}: {layer_pass}/{layer_pass + layer_fail}")

    print_summary(total_pass, total_fail, layer_results)
    return exit_code_for(total_fail)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
