#!/usr/bin/env python3
"""run-all.py — Python stdlib orchestrator for the speckit-pro test suite.

Reproduces the ``run-all.sh`` developer UX with no Bash or ``jq`` dependency of
its own:

  run-all.py               # Layers 1, 4, 5 + toolchain preflight (default)
  run-all.py --live        # default deterministic layers; no live Layer 7 selected
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

Every executable manifest entry is Python-authoritative. A non-``.py`` entry
fails closed instead of falling back to a platform shell.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

TEST_LIB = Path(__file__).resolve().parent / "lib"
if str(TEST_LIB) not in sys.path:
    sys.path.insert(0, str(TEST_LIB))

from test_result import classify_counted_child  # noqa: E402

SUITE_MANIFEST = "tests/speckit-pro/suite-manifest.json"
RULE = "────────────────────────────────────────"
HEADER_RULE = "════════════════════════════════════════"
# Layer 7 owns the executable live mode. Layer 4 is deterministic unit coverage;
# forwarding --live to unittest modules would corrupt their argument parsing.
LIVE_AWARE_LAYERS = {"7"}
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


def execution_layers(manifest: dict) -> list[dict]:
    """Return numeric layers in the predecessor's 1..8 presentation order."""
    layers = [layer for layer in manifest["layers"] if layer["id"] != "toolchain"]
    return sorted(layers, key=lambda layer: int(layer["id"]))


def toolchain_should_run(manifest: dict, config: Config) -> bool:
    by_id = {layer["id"]: layer for layer in manifest["layers"]}
    return any(
        layer_id in by_id and layer_should_run(by_id[layer_id], config)
        for layer_id in TOOLCHAIN_TRIGGER_LAYERS
    )


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
) -> tuple[str, int]:
    """Run one Python child test and fail closed on a non-Python manifest entry."""
    pass_live = config.live and layer["id"] in LIVE_AWARE_LAYERS
    if path.suffix != ".py":
        return (
            f"{path.stem}: 0/1 passed\n"
            f"unsupported non-Python manifest entry: {path}\n",
            1,
        )
    argv = [sys.executable, str(path)]
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
    return (completed.stdout + completed.stderr, completed.returncode)


def run_execute_layer(layer: dict, config: Config, root: Path) -> tuple[int, int]:
    print(f"\nLayer {layer['id']}: {layer['label']}")
    print(RULE)
    layer_pass = layer_fail = 0
    if not layer["scripts"]:
        print("  FAIL: no test scripts discovered")
        return 0, 1
    for script in layer["scripts"]:
        path = root / script["path"]
        label = Path(script["path"]).stem
        if not path.is_file():
            print(f"  FAIL: {label} (not found)")
            layer_fail += 1
            continue
        output, exit_code = dispatch_script(path, layer, config, root)
        disposition, passed, failed, _detail = classify_counted_child(
            exit_code,
            output,
            label,
        )
        layer_pass += passed
        layer_fail += failed
        if disposition == "crash":
            print(f"  FAIL {label} (exit {exit_code}, no summary — child may have crashed)")
        elif disposition == "missing-summary":
            print(f"  FAIL {label} (exit 0, no summary)")
        elif disposition == "invalid-summary":
            print(f"  FAIL {label} (invalid or empty summary)")
        elif disposition == "duplicate-summary":
            print(f"  FAIL {label} (multiple owned summaries)")
        elif disposition == "failed-exit":
            print(f"  FAIL {label} ({passed}/{passed} reported, exit {exit_code})")
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
        argument_hint = " <skill>" if layer["id"] in {"2", "3"} else ""
        print(f"    python3 {script['path']}{argument_hint}")


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
    total_pass = total_fail = 0
    layer_results: list[str] = []
    selected_layers = 0

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

    for layer in execution_layers(manifest):
        if not layer_should_run(layer, config):
            continue
        selected_layers += 1
        if layer["execution"] == "print-commands":
            print_layer_commands(layer, root)
            continue
        layer_pass, layer_fail = run_execute_layer(layer, config, root)
        total_pass += layer_pass
        total_fail += layer_fail
        layer_results.append(f"L{layer['id']}: {layer_pass}/{layer_pass + layer_fail}")

    if selected_layers == 0:
        print("\n  FAIL: no executable layer selected")
        total_fail += 1

    print_summary(total_pass, total_fail, layer_results)
    return exit_code_for(total_fail)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
