#!/usr/bin/env python3
"""Plan or execute bounded native evaluations with retained local evidence."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any
import uuid


TEST_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TEST_ROOT.parents[1]
if str(TEST_ROOT / "lib") not in sys.path:
    sys.path.insert(0, str(TEST_ROOT / "lib"))

from native_eval_catalog import LAYERS, load_catalog, plan_trials, select_cases  # noqa: E402
from native_eval_pool import _validate_limits  # noqa: E402
from native_eval_execution import run_evaluations  # noqa: E402
from native_eval_adapters import prepare_judge, execute_prepared, judge_runtime_compatibility_identity  # noqa: E402
from native_eval_capture import normalize_trace  # noqa: E402
from native_eval_judge import build_judge_request  # noqa: E402


DEFAULT_CATALOG = TEST_ROOT / "evals" / "catalog.json"
SUITE_MANIFEST = TEST_ROOT / "suite-manifest.json"
_HOSTS = ("claude", "codex")


class NativeJudge:
    """One pinned native judge callback, scheduled by the shared Codex pool."""

    def __init__(self, model: str):
        self.model = model
        probe_case = {"requirements": [{"id": "probe"}], "checks": [
            {"id": "probe", "requirement": "probe", "type": "semantic", "rubric": "Check the supplied evidence."}
        ]}
        probe_observation = {"completed": True, "error": None, "final_text": "probe",
                             "activations": [], "tool_calls": [], "artifacts": {}, "usage": {}}
        request = build_judge_request(probe_case, probe_observation)
        with tempfile.TemporaryDirectory(prefix="native-judge-preflight-") as root:
            prepared = prepare_judge(request, attempt_dir=Path(root) / "probe", model=model)
            self._compatibility = judge_runtime_compatibility_identity(prepared)
        self.runtime_identity = {
            "native": self._compatibility,
            "executor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        }

    def __call__(self, request: dict[str, object], grade_dir: Path, model: str) -> str:
        if model != self.model:
            raise ValueError("semantic judge model changed after admission")
        prepared = prepare_judge(request, attempt_dir=grade_dir / "native", model=model)
        if judge_runtime_compatibility_identity(prepared) != self._compatibility:
            raise ValueError("semantic judge runtime changed after admission")
        raw = execute_prepared(prepared, timeout=120)
        process = raw.process_evidence
        if raw.exit_code != 0 or raw.timed_out or process.get("cleanup_verified") is not True \
                or process.get("cleanup_error") is not None or process.get("unexpected_descendants") is True:
            raise ValueError("semantic judge native process failed or cleanup is unverified")
        observation = normalize_trace("codex", raw.raw_trace)
        if observation["tool_calls"]:
            raise ValueError("semantic judge performed a prohibited tool call")
        result_path = prepared.result_path
        if result_path is None or not result_path.is_file() or result_path.is_symlink() \
                or result_path.stat().st_size > 1024 * 1024:
            raise ValueError("semantic judge structured result is unavailable or unsafe")
        result = result_path.read_text(encoding="utf-8")
        if result.strip() != observation["final_text"].strip():
            raise ValueError("semantic judge result differs from native terminal evidence")
        return result


@dataclass(frozen=True)
class Config:
    catalog: Path
    layers: tuple[str, ...]
    case_ids: tuple[str, ...]
    hosts: tuple[str, ...]
    runs: int
    claude_concurrency: int
    codex_concurrency: int
    nested_concurrency: int
    preview: bool
    execute: bool
    output: Path | None
    resume: bool
    retry_cases: tuple[str, ...]
    retry_status: str | None
    claude_model: str
    codex_model: str
    judge_model: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--layers", nargs="+", required=True)
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--hosts", choices=("claude", "codex", "both"), default="both")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--claude-concurrency", type=int, default=4)
    parser.add_argument("--codex-concurrency", type=int, default=4)
    parser.add_argument("--nested-concurrency", type=int, default=1)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preview", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--retry-case", action="append", default=[])
    parser.add_argument("--retry-status", choices=("fail", "invalid", "incomplete"))
    parser.add_argument("--claude-model", default="claude-sonnet-5")
    parser.add_argument("--codex-model", default="gpt-6-sol")
    parser.add_argument("--judge-model", default="gpt-6-sol")
    return parser


def _resolve_layers(values: list[str]) -> tuple[str, ...]:
    try:
        manifest = json.loads(SUITE_MANIFEST.read_text(encoding="utf-8"))
        layers = manifest["layers"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(f"could not load suite manifest: {exc}") from exc
    if not isinstance(layers, list):
        raise ValueError("suite manifest layers are malformed")
    by_selector: dict[str, str] = {}
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        layer_id, key = layer.get("id"), layer.get("key")
        if isinstance(layer_id, str) and isinstance(key, str) and key in LAYERS:
            by_selector[layer_id] = key
            by_selector[key] = key
    if not values:
        raise ValueError("at least one layer is required")
    resolved: list[str] = []
    for value in values:
        if value not in by_selector:
            raise ValueError(f"layer is not available for native evaluation: {value}")
        resolved.append(by_selector[value])
    if len(resolved) != len(set(resolved)):
        raise ValueError("layers contain duplicate selections")
    return tuple(resolved)


def _nonempty_unique(values: list[str], label: str) -> tuple[str, ...]:
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise ValueError(f"{label} values must be nonempty")
    if len(values) != len(set(values)):
        raise ValueError(f"{label} contains duplicates")
    return tuple(values)


def parse_config(argv: list[str]) -> Config:
    args = build_parser().parse_args(argv)
    if not 1 <= args.runs <= 50:
        raise ValueError("runs must be an integer from 1 through 50")
    selected_hosts = _HOSTS if args.hosts == "both" else (args.hosts,)
    capacities = _validate_limits(
        "provider concurrency", {"claude": args.claude_concurrency, "codex": args.codex_concurrency},
        {"claude": 8, "codex": 8},
    )
    _validate_limits(
        "nested concurrency", {host: args.nested_concurrency for host in _HOSTS},
        {host: min(2, capacities[host]) if host in selected_hosts else 2 for host in _HOSTS},
    )
    if args.execute and args.output is None:
        raise ValueError("--output is required with --execute")
    if args.preview and (args.output is not None or args.resume or args.retry_case or args.retry_status is not None):
        raise ValueError("output, resume, and retry options require --execute")
    retry_cases = _nonempty_unique(args.retry_case, "retry cases")
    if bool(retry_cases) != (args.retry_status is not None):
        raise ValueError("--retry-case and --retry-status must be supplied together")
    if retry_cases and not args.resume:
        raise ValueError("explicit retries require --resume")
    return Config(
        args.catalog, _resolve_layers(args.layers), _nonempty_unique(args.case_id, "case ids"), selected_hosts,
        args.runs, args.claude_concurrency, args.codex_concurrency, args.nested_concurrency,
        args.preview, args.execute, args.output, args.resume, retry_cases, args.retry_status,
        args.claude_model, args.codex_model, args.judge_model,
    )


def preview_payload(config: Config, cases: list[dict[str, Any]], rows: list[dict[str, object]]) -> dict[str, object]:
    semantic_cases = {case["id"] for case in cases if any(check["type"] == "semantic" for check in case["checks"])}
    native_modes = {(row["case_id"], row["host"], row["mode"]) for row in rows}
    return {
        "mode": "preview",
        "layers": list(config.layers),
        "case_ids": [case["id"] for case in cases],
        "hosts": list(config.hosts),
        "runs": config.runs,
        "unique_cases": len(cases),
        "native_modes": len(native_modes),
        "subject_trials": len(rows),
        "potential_judge_calls": sum(row["case_id"] in semantic_cases for row in rows),
    }


def run_execution(
    config: Config, catalog: dict[str, Any], cases: list[dict[str, Any]], rows: list[dict[str, object]],
) -> int:
    """Dispatch the shared executor and retain a distinct report per invocation."""
    output = config.output
    if output is None:
        raise ValueError("execution requires an output directory")
    if output.is_symlink() or output.exists() and not output.is_dir():
        raise ValueError("output must be a regular directory, not a symlink")
    if config.resume and not output.is_dir():
        raise ValueError("--resume requires an existing output directory")
    if not config.resume and output.is_dir() and any(output.iterdir()):
        raise ValueError("existing output contains evidence; use --resume")
    judge = NativeJudge(config.judge_model) if any(
        check["type"] == "semantic" for case in cases for check in case["checks"]
    ) else None
    report = run_evaluations(config, catalog, cases, rows, repo_root=REPO_ROOT, judge_execute=judge)
    reports = output.resolve(strict=True) / "reports"
    if reports.is_symlink():
        raise ValueError("report directory must not be a symlink")
    reports.mkdir(exist_ok=True)
    report_path = reports / (uuid.uuid4().hex + ".json")
    with report_path.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps({"report": str(report_path), "counts": report["counts"],
                      "pair_counts": report["pair_counts"],
                      "providers": report["providers"], "limitations": report["limitations"]}, sort_keys=True))
    return report["exit_status"]


def main(argv: list[str] | None = None) -> int:
    try:
        config = parse_config(sys.argv[1:] if argv is None else argv)
        catalog = load_catalog(config.catalog, REPO_ROOT)
        cases = select_cases(catalog, layers=config.layers, case_ids=config.case_ids or None)
        rows = plan_trials(cases, hosts=config.hosts, runs=config.runs)
        if config.preview:
            print(json.dumps(preview_payload(config, cases, rows), sort_keys=True))
            return 0
        return run_execution(config, catalog, cases, rows)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
